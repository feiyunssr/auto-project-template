from __future__ import annotations

import asyncio
import hashlib
from time import perf_counter
from uuid import uuid4

from apps.backend.core.errors import ProviderRateLimitError, ProviderTimeoutError
from apps.backend.models import ServiceAiProfile, ServiceJob
from apps.backend.models.enums import QualityStatus
from apps.backend.services.providers.base import (
    NormalizedResult,
    PreparedRequest,
    ProviderAdapter,
    ProviderInvokeResult,
)


class MockProviderAdapter(ProviderAdapter):
    name = "mock"

    async def prepare_request(
        self,
        job: ServiceJob,
        profile: ServiceAiProfile,
    ) -> PreparedRequest:
        payload = {
            "job_no": job.job_no,
            "scenario_key": job.scenario_key,
            "input_payload": job.normalized_payload,
            "system_prompt": profile.system_prompt,
            "prompt_template": profile.prompt_template,
            "model_name": profile.model_name,
        }
        masked = dict(payload)
        masked["system_prompt"] = "***"
        return PreparedRequest(payload=payload, masked_payload=masked)

    async def invoke(
        self,
        prepared: PreparedRequest,
        profile: ServiceAiProfile,
        attempt_no: int,
    ) -> ProviderInvokeResult:
        started = perf_counter()
        normalized_input = prepared.payload["input_payload"]
        simulate = normalized_input.get("simulate")
        delay_ms = int(normalized_input.get("delay_ms") or 0)
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)
        if simulate == "timeout_always":
            raise ProviderTimeoutError("Mock provider simulated a persistent timeout.")
        if simulate == "timeout_once" and attempt_no == 1:
            raise ProviderTimeoutError("Mock provider simulated a first-attempt timeout.")
        if simulate == "rate_limit":
            raise ProviderRateLimitError()

        content = (
            normalized_input.get("content")
            or normalized_input.get("prompt")
            or normalized_input.get("brief")
            or "generated result"
        )
        digest = hashlib.sha256(str(normalized_input).encode("utf-8")).hexdigest()[:16]
        payload = {
            "preview": f"{content} :: {digest}",
            "artifact_uri": f"memory://artifact/{prepared.payload['job_no']}",
            "needs_review": simulate == "review_required",
        }
        latency_ms = int((perf_counter() - started) * 1000) + 25
        return ProviderInvokeResult(
            external_request_id=f"mock-{uuid4()}",
            payload=payload,
            latency_ms=latency_ms,
            input_tokens=max(1, len(str(normalized_input)) // 4),
            output_tokens=max(1, len(payload["preview"]) // 4),
        )

    async def normalize_response(
        self,
        job: ServiceJob,
        invoke_result: ProviderInvokeResult,
        profile: ServiceAiProfile,
    ) -> NormalizedResult:
        quality_status = (
            QualityStatus.REVIEW_REQUIRED.value
            if invoke_result.payload.get("needs_review")
            else QualityStatus.APPROVED.value
        )
        return NormalizedResult(
            result_type="mock_result",
            preview_text=invoke_result.payload["preview"],
            structured_payload={
                "job_no": job.job_no,
                "scenario_key": job.scenario_key,
                "content": invoke_result.payload["preview"],
            },
            artifacts=[
                {
                    "artifact_role": "result",
                    "storage_type": "inline",
                    "uri": invoke_result.payload["artifact_uri"],
                    "mime_type": "application/json",
                    "metadata": {"provider": self.name},
                }
            ],
            quality_status=quality_status,
            review_comment="Mock provider marked this output for review."
            if quality_status == QualityStatus.REVIEW_REQUIRED.value
            else None,
        )
