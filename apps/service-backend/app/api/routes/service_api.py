from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_service_api_auth_context
from app.core.errors import ServiceError, ValidationFailedError
from app.models import ServiceJob
from app.models.enums import JobStatus
from app.repositories.ai_profiles import AiProfileRepository
from app.repositories.tasks import TaskRepository
from app.schemas.service_api import (
    ServiceApiAuthContext,
    ServiceApiTaskCreateRequest,
    ServiceApiTaskDetailResponse,
    ServiceApiTaskResultResponse,
    ServiceApiTaskSummaryResponse,
)
from app.schemas.tasks import TaskSummaryResponse
from app.services.task_requests import build_task_detail, is_job_retryable, make_idempotency_key, new_job_no, normalize_payload

router = APIRouter(prefix="/service-api", tags=["service-api"])
logger = logging.getLogger(__name__)


def _service_summary(job: ServiceJob) -> ServiceApiTaskSummaryResponse:
    return ServiceApiTaskSummaryResponse(
        **TaskSummaryResponse.model_validate(job).model_dump(),
        retryable=is_job_retryable(job),
    )


def _service_result(job: ServiceJob, result) -> ServiceApiTaskResultResponse:
    return ServiceApiTaskResultResponse(
        task_id=job.id,
        job_no=job.job_no,
        status=job.status,
        retryable=is_job_retryable(job),
        error_code=job.error_code,
        error_message=job.error_message,
        result_summary=job.result_summary,
        result=result,
        finished_at=job.finished_at,
    )


@router.post("/tasks", response_model=ServiceApiTaskSummaryResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_service_api_task(
    payload: ServiceApiTaskCreateRequest,
    auth: ServiceApiAuthContext = Depends(get_service_api_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ServiceApiTaskSummaryResponse:
    if not payload.input_payload:
        raise ValidationFailedError("Task payload validation failed.", {"input_payload": "请输入业务输入"})
    normalized_payload, payload_hash = normalize_payload(payload.input_payload)
    repo = TaskRepository(session)
    profile_repo = AiProfileRepository(session)
    idempotency_key = make_idempotency_key(auth.submitter_id, payload.scenario_key, payload_hash, namespace="service_api")
    existing = await repo.get_job_by_idempotency_key(idempotency_key)
    if existing:
        logger.info("service_api_task_idempotency_hit job_id=%s job_no=%s", existing.id, existing.job_no)
        return _service_summary(existing)

    if payload.ai_profile_id:
        profile = await profile_repo.get_profile(payload.ai_profile_id)
        if profile is None:
            raise ValidationFailedError("Task payload validation failed.", {"ai_profile_id": "请选择有效的 AI 配置"})

    job = ServiceJob(
        job_no=new_job_no(),
        submitted_by_hub_user_id=auth.submitter_id,
        submitted_by_name=auth.submitter_name,
        source_channel=auth.source_channel,
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
    logger.info("service_api_task_created job_id=%s job_no=%s scenario=%s", job.id, job.job_no, job.scenario_key)
    return _service_summary(job)


@router.get("/tasks/{job_id}", response_model=ServiceApiTaskDetailResponse)
async def get_service_api_task_detail(
    job_id: uuid.UUID,
    auth: ServiceApiAuthContext = Depends(get_service_api_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ServiceApiTaskDetailResponse:
    job = await TaskRepository(session).get_job_by_id(job_id)
    if job is None or job.submitted_by_hub_user_id != auth.submitter_id:
        raise ServiceError(code="TASK_NOT_FOUND", message="Task not found.", status_code=404)
    detail = await build_task_detail(job, session)
    return ServiceApiTaskDetailResponse(
        **_service_summary(job).model_dump(),
        input_payload=detail.input_payload,
        normalized_payload=detail.normalized_payload,
        max_retries=detail.max_retries,
        last_success_result=detail.last_success_result,
        attempts=detail.attempts,
    )


@router.get("/tasks/{job_id}/result", response_model=ServiceApiTaskResultResponse)
async def get_service_api_task_result(
    job_id: uuid.UUID,
    auth: ServiceApiAuthContext = Depends(get_service_api_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ServiceApiTaskResultResponse:
    job = await TaskRepository(session).get_job_by_id(job_id)
    if job is None or job.submitted_by_hub_user_id != auth.submitter_id:
        raise ServiceError(code="TASK_NOT_FOUND", message="Task not found.", status_code=404)
    detail = await build_task_detail(job, session)
    return _service_result(job, detail.last_success_result)
