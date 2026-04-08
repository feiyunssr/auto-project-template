from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from secrets import token_hex

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ServiceJob
from app.repositories.ai_profiles import AiProfileRepository
from app.schemas.tasks import (
    TaskArtifactResponse,
    TaskAttemptResponse,
    TaskDetailResponse,
    TaskResultResponse,
    TaskSummaryResponse,
)


def normalize_payload(payload: dict) -> tuple[dict, str]:
    normalized = json.loads(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    payload_hash = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode("utf-8")).hexdigest()
    return normalized, payload_hash


def make_idempotency_key(
    submitter_id: str,
    scenario_key: str,
    payload_hash: str,
    *,
    namespace: str,
) -> str:
    bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    raw = f"{namespace}:{submitter_id}:{scenario_key}:{payload_hash}:{bucket}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_job_no() -> str:
    return f"JOB{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{token_hex(3).upper()}"


def is_job_retryable(job: ServiceJob) -> bool:
    return bool((job.result_summary or {}).get("retryable")) or job.error_code in {
        "PROVIDER_TIMEOUT_FINAL",
        "PROVIDER_RATE_LIMIT_FINAL",
    }


async def build_task_detail(job: ServiceJob, session: AsyncSession) -> TaskDetailResponse:
    profile = None
    if job.ai_profile_id:
        profile = await AiProfileRepository(session).get_profile(job.ai_profile_id)
    max_retries = profile.max_retries if profile else None
    last_success = max(job.results, key=lambda item: item.version_no, default=None)
    return TaskDetailResponse(
        **TaskSummaryResponse.model_validate(job).model_dump(),
        input_payload=job.input_payload,
        normalized_payload=job.normalized_payload,
        submitted_by_hub_user_id=job.submitted_by_hub_user_id,
        submitted_by_name=job.submitted_by_name,
        source_channel=job.source_channel,
        retryable=is_job_retryable(job),
        max_retries=max_retries,
        last_success_result=TaskResultResponse.model_validate(last_success) if last_success else None,
        attempts=[
            TaskAttemptResponse.model_validate(item) for item in sorted(job.attempts, key=lambda row: row.attempt_no)
        ],
        results=[
            TaskResultResponse.model_validate(item)
            for item in sorted(job.results, key=lambda row: row.version_no, reverse=True)
        ],
        artifacts=[
            TaskArtifactResponse.model_validate(item)
            for item in sorted(job.artifacts, key=lambda row: row.created_at, reverse=True)
        ],
    )
