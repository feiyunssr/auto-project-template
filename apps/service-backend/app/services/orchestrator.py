from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProviderRateLimitError, ProviderTimeoutError, ServiceError
from app.models import ServiceAiProfile, ServiceArtifact, ServiceJobAttempt, ServiceResult
from app.models.enums import AttemptStatus, JobStatus, QualityStatus
from app.models.mixins import utcnow
from app.repositories.ai_profiles import AiProfileRepository
from app.repositories.tasks import TaskRepository
from app.services.hub_telemetry import HubTelemetryService
from app.services.provider_registry import get_provider_adapter
from app.services.state_machine import ensure_transition

logger = logging.getLogger(__name__)


class JobOrchestrator:
    def __init__(
        self,
        session: AsyncSession,
        *,
        hub_telemetry: HubTelemetryService | None = None,
    ) -> None:
        self.session = session
        self.tasks = TaskRepository(session)
        self.ai_profiles = AiProfileRepository(session)
        self.provider = get_provider_adapter()
        self.hub_telemetry = hub_telemetry

    async def run_job(self, job_id) -> None:
        job = await self.tasks.get_job_by_id(job_id)
        if job is None:
            logger.warning("job_missing job_id=%s", job_id)
            return
        profile = await self._resolve_profile(job.ai_profile_id, job.scenario_key)
        logger.info(
            "job_started job_id=%s job_no=%s scenario=%s profile=%s max_retries=%s timeout_ms=%s",
            job.id,
            job.job_no,
            job.scenario_key,
            profile.profile_key,
            profile.max_retries,
            profile.timeout_ms,
        )
        ensure_transition(job.status, JobStatus.RUNNING.value)
        job.status = JobStatus.RUNNING.value
        job.started_at = job.started_at or utcnow()
        job.error_code = None
        job.error_message = None
        await self.session.commit()

        total_attempts = profile.max_retries + 1
        for attempt_no in range(1, total_attempts + 1):
            is_last_attempt = attempt_no == total_attempts
            try:
                await self._run_attempt(job, profile, attempt_no)
                return
            except ProviderTimeoutError as exc:
                await self._handle_retryable_error(job, profile, attempt_no, exc, is_last_attempt)
            except ProviderRateLimitError as exc:
                await self._handle_retryable_error(job, profile, attempt_no, exc, is_last_attempt)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "job_post_processing_failed job_id=%s attempt_no=%s",
                    job.id,
                    attempt_no,
                )
                await self._mark_failed(job, "POST_PROCESSING_FAILED", str(exc), retryable=False)
                return

    async def _resolve_profile(self, profile_id, scenario_key: str) -> ServiceAiProfile:
        profile = await self.ai_profiles.get_profile(profile_id) if profile_id else None
        profile = profile or await self.ai_profiles.get_default_profile(scenario_key)
        if profile is None:
            logger.warning("profile_missing scenario=%s profile_id=%s", scenario_key, profile_id)
            raise ServiceError(
                code="PROFILE_NOT_FOUND",
                message=f"No active AI profile for scenario `{scenario_key}`.",
                status_code=404,
            )
        return profile

    async def _run_attempt(self, job, profile: ServiceAiProfile, attempt_no: int) -> None:
        prepared = await self.provider.prepare_request(job, profile)
        attempt = ServiceJobAttempt(
            job_id=job.id,
            attempt_no=attempt_no,
            workflow_stage="invoke_provider",
            provider_name=profile.provider_name,
            provider_model=profile.model_name,
            request_payload_masked=prepared.masked_payload,
            status=AttemptStatus.RUNNING.value,
            retryable=False,
            started_at=utcnow(),
        )
        await self.tasks.add_attempt(attempt)
        await self.session.flush()
        job.current_attempt_no = attempt_no
        logger.info(
            "provider_attempt_started job_id=%s job_no=%s attempt_no=%s provider=%s model=%s",
            job.id,
            job.job_no,
            attempt_no,
            profile.provider_name,
            profile.model_name,
        )
        try:
            invoke_result = await asyncio.wait_for(
                self.provider.invoke(prepared, profile, attempt_no),
                timeout=profile.timeout_ms / 1000,
            )
            normalized = await self.provider.normalize_response(job, invoke_result, profile)
        except asyncio.TimeoutError as exc:
            attempt.status = AttemptStatus.TIMEOUT.value
            attempt.retryable = True
            attempt.error_code = "PROVIDER_TIMEOUT"
            attempt.error_message = f"Provider timed out after {profile.timeout_ms} ms."
            attempt.finished_at = utcnow()
            await self.session.flush()
            raise ProviderTimeoutError(attempt.error_message) from exc
        except ProviderTimeoutError as exc:
            attempt.status = AttemptStatus.TIMEOUT.value
            attempt.retryable = True
            attempt.error_code = "PROVIDER_TIMEOUT"
            attempt.error_message = str(exc)
            attempt.finished_at = utcnow()
            await self.session.flush()
            raise
        except ProviderRateLimitError as exc:
            attempt.status = AttemptStatus.FAILED.value
            attempt.retryable = True
            attempt.error_code = "PROVIDER_RATE_LIMIT"
            attempt.error_message = str(exc)
            attempt.finished_at = utcnow()
            await self.session.flush()
            raise

        attempt.status = AttemptStatus.SUCCEEDED.value
        attempt.external_request_id = invoke_result.external_request_id
        attempt.response_payload_trimmed = invoke_result.payload
        attempt.latency_ms = invoke_result.latency_ms
        attempt.input_tokens = invoke_result.input_tokens
        attempt.output_tokens = invoke_result.output_tokens
        attempt.finished_at = utcnow()

        version_no = (await self.tasks.count_results_for_job(job.id)) + 1
        result = ServiceResult(
            job_id=job.id,
            version_no=version_no,
            result_type=normalized.result_type,
            structured_payload=normalized.structured_payload,
            preview_text=normalized.preview_text,
            quality_status=normalized.quality_status,
            review_comment=normalized.review_comment,
        )
        await self.tasks.add_result(result)
        for artifact_payload in normalized.artifacts:
            await self.tasks.add_artifact(
                ServiceArtifact(
                    job_id=job.id,
                    attempt_id=attempt.id,
                    **artifact_payload,
                )
            )

        target_status = (
            JobStatus.REVIEW_REQUIRED.value
            if normalized.quality_status == QualityStatus.REVIEW_REQUIRED.value
            else JobStatus.SUCCEEDED.value
        )
        ensure_transition(job.status, target_status)
        job.status = target_status
        job.finished_at = utcnow()
        job.error_code = None
        job.error_message = None
        job.result_summary = {
            "preview_text": normalized.preview_text,
            "quality_status": normalized.quality_status,
            "result_type": normalized.result_type,
        }
        logger.info(
            (
                "job_succeeded job_id=%s job_no=%s attempt_no=%s "
                "final_status=%s external_request_id=%s"
            ),
            job.id,
            job.job_no,
            attempt_no,
            target_status,
            invoke_result.external_request_id,
        )
        await self.session.commit()
        await self._emit_success_event(job)

    async def _handle_retryable_error(
        self,
        job,
        profile,
        attempt_no: int,
        exc: Exception,
        is_last: bool,
    ) -> None:
        is_timeout = isinstance(exc, ProviderTimeoutError)
        error_code = (
            "PROVIDER_TIMEOUT_FINAL"
            if is_last and is_timeout
            else "PROVIDER_TIMEOUT_RETRYING"
            if is_timeout
            else "PROVIDER_RATE_LIMIT_FINAL"
            if is_last
            else "PROVIDER_RATE_LIMIT_RETRYING"
        )
        message = str(exc)
        job.current_attempt_no = attempt_no
        job.error_code = error_code
        job.error_message = message
        logger.warning(
            (
                "provider_attempt_retryable_error job_id=%s job_no=%s "
                "attempt_no=%s error_code=%s is_last=%s message=%s"
            ),
            job.id,
            job.job_no,
            attempt_no,
            error_code,
            is_last,
            message,
        )
        if is_last:
            await self._mark_failed(job, error_code, message, retryable=True)
            return
        await self.session.commit()
        await asyncio.sleep(min(2**attempt_no, 3))

    async def _mark_failed(self, job, error_code: str, error_message: str, retryable: bool) -> None:
        ensure_transition(job.status, JobStatus.FAILED.value)
        job.status = JobStatus.FAILED.value
        job.finished_at = utcnow()
        job.error_code = error_code
        job.error_message = error_message
        job.result_summary = {"retryable": retryable}
        logger.error(
            "job_failed job_id=%s job_no=%s error_code=%s retryable=%s message=%s",
            job.id,
            job.job_no,
            error_code,
            retryable,
            error_message,
        )
        await self.session.commit()
        await self._emit_failure_event(job, retryable=retryable)

    async def _emit_success_event(self, job) -> None:
        if self.hub_telemetry is None:
            return
        occurred_at = job.finished_at or utcnow()
        await self.hub_telemetry.emit_job_succeeded(
            job_id=str(job.id),
            attempt_no=job.current_attempt_no,
            occurred_at=occurred_at,
            status=job.status,
            duration_ms=self._duration_ms(job.started_at, occurred_at),
            metadata=self._build_event_metadata(job),
        )

    async def _emit_failure_event(self, job, *, retryable: bool) -> None:
        if self.hub_telemetry is None:
            return
        occurred_at = job.finished_at or utcnow()
        metadata = self._build_event_metadata(job)
        metadata["retryable"] = retryable
        await self.hub_telemetry.emit_job_failed(
            job_id=str(job.id),
            attempt_no=job.current_attempt_no,
            occurred_at=occurred_at,
            status=job.status,
            duration_ms=self._duration_ms(job.started_at, occurred_at),
            error_code=job.error_code,
            error_summary=job.error_message,
            metadata=metadata,
        )

    @staticmethod
    def _build_event_metadata(job) -> dict[str, str | int | bool | None]:
        return {
            "scenario_key": job.scenario_key,
            "source_channel": job.source_channel,
            "submitted_by_hub_user_id": job.submitted_by_hub_user_id,
            "submitted_by_name": job.submitted_by_name,
            "job_no": job.job_no,
        }

    @staticmethod
    def _duration_ms(started_at, occurred_at) -> int | None:
        if started_at is None or occurred_at is None:
            return None
        return max(int((occurred_at - started_at).total_seconds() * 1000), 0)
