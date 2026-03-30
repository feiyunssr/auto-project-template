from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from secrets import token_hex

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_auth_context, get_db_session
from app.core.errors import ServiceError, ValidationFailedError
from app.models import ServiceJob
from app.models.enums import JobStatus
from app.models.mixins import utcnow
from app.repositories.ai_profiles import AiProfileRepository
from app.repositories.tasks import TaskRepository
from app.schemas.common import AuthContext
from app.schemas.tasks import (
    TaskArtifactResponse,
    TaskAttemptResponse,
    TaskCreateRequest,
    TaskDetailResponse,
    TaskListResponse,
    TaskResultResponse,
    TaskSummaryResponse,
)
from app.services.state_machine import ensure_transition

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)


def _normalize_payload(payload: dict) -> tuple[dict, str]:
    normalized = json.loads(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    payload_hash = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode("utf-8")).hexdigest()
    return normalized, payload_hash


def _make_idempotency_key(auth: AuthContext, scenario_key: str, payload_hash: str) -> str:
    bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    raw = f"{auth.hub_user_id}:{scenario_key}:{payload_hash}:{bucket}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _job_no() -> str:
    return f"JOB{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{token_hex(3).upper()}"


async def _build_task_detail(job: ServiceJob, session: AsyncSession) -> TaskDetailResponse:
    profile = None
    if job.ai_profile_id:
        profile = await AiProfileRepository(session).get_profile(job.ai_profile_id)
    max_retries = profile.max_retries if profile else None
    last_success = max(job.results, key=lambda item: item.version_no, default=None)
    retryable = bool((job.result_summary or {}).get("retryable")) or job.error_code in {
        "PROVIDER_TIMEOUT_FINAL",
        "PROVIDER_RATE_LIMIT_FINAL",
    }
    return TaskDetailResponse(
        **TaskSummaryResponse.model_validate(job).model_dump(),
        input_payload=job.input_payload,
        normalized_payload=job.normalized_payload,
        submitted_by_hub_user_id=job.submitted_by_hub_user_id,
        submitted_by_name=job.submitted_by_name,
        source_channel=job.source_channel,
        retryable=retryable,
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


@router.post("", response_model=TaskSummaryResponse)
async def create_task(
    payload: TaskCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> TaskSummaryResponse:
    if not payload.input_payload:
        raise ValidationFailedError("Task payload validation failed.", {"input_payload": "请输入业务输入"})
    normalized_payload, payload_hash = _normalize_payload(payload.input_payload)
    idempotency_key = _make_idempotency_key(auth, payload.scenario_key, payload_hash)
    repo = TaskRepository(session)
    existing = await repo.get_job_by_idempotency_key(idempotency_key)
    if existing:
        logger.info(
            "task_idempotency_hit job_id=%s job_no=%s hub_user_id=%s",
            existing.id,
            existing.job_no,
            auth.hub_user_id,
        )
        return TaskSummaryResponse.model_validate(existing)

    if payload.ai_profile_id:
        profile = await AiProfileRepository(session).get_profile(payload.ai_profile_id)
        if profile is None:
            raise ValidationFailedError("Task payload validation failed.", {"ai_profile_id": "请选择有效的 AI 配置"})

    job = ServiceJob(
        job_no=_job_no(),
        submitted_by_hub_user_id=auth.hub_user_id,
        submitted_by_name=auth.hub_user_name,
        source_channel=payload.source_channel,
        scenario_key=payload.scenario_key,
        title=payload.title,
        ai_profile_id=payload.ai_profile_id,
        input_payload=payload.input_payload,
        normalized_payload=normalized_payload,
        normalized_payload_hash=payload_hash,
        idempotency_key=idempotency_key,
        status=JobStatus.QUEUED.value,
        priority=5,
        result_summary={"message": "任务已提交，正在调用 AI 处理"},
    )
    await repo.create_job(job)
    await session.commit()
    logger.info(
        "task_created job_id=%s job_no=%s scenario=%s hub_user_id=%s source_channel=%s",
        job.id,
        job.job_no,
        job.scenario_key,
        auth.hub_user_id,
        job.source_channel,
    )
    return TaskSummaryResponse.model_validate(job)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: str | None = Query(default=None),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> TaskListResponse:
    items = await TaskRepository(session).list_jobs(hub_user_id=auth.hub_user_id, status=status)
    return TaskListResponse(items=[TaskSummaryResponse.model_validate(item) for item in items])


@router.get("/{job_id}", response_model=TaskDetailResponse)
async def get_task_detail(
    job_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> TaskDetailResponse:
    job = await TaskRepository(session).get_job_by_id(job_id)
    if job is None or job.submitted_by_hub_user_id != auth.hub_user_id:
        raise ServiceError(code="TASK_NOT_FOUND", message="Task not found.", status_code=404)
    return await _build_task_detail(job, session)


@router.post("/{job_id}/retry", response_model=TaskSummaryResponse)
async def retry_task(
    job_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> TaskSummaryResponse:
    job = await TaskRepository(session).get_job_by_id(job_id)
    if job is None or job.submitted_by_hub_user_id != auth.hub_user_id:
        raise ServiceError(code="TASK_NOT_FOUND", message="Task not found.", status_code=404)
    ensure_transition(job.status, JobStatus.QUEUED.value)
    job.status = JobStatus.QUEUED.value
    job.error_code = None
    job.error_message = None
    job.finished_at = None
    job.updated_at = utcnow()
    await session.commit()
    logger.info("task_requeued job_id=%s job_no=%s hub_user_id=%s", job.id, job.job_no, auth.hub_user_id)
    return TaskSummaryResponse.model_validate(job)
