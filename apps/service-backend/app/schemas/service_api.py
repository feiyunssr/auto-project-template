import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.tasks import TaskAttemptResponse, TaskResultResponse


class ServiceApiTaskCreateRequest(BaseModel):
    scenario_key: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=2, max_length=160)
    ai_profile_id: uuid.UUID | None = None
    input_payload: dict[str, Any]


class ServiceApiTaskSummaryResponse(BaseModel):
    id: uuid.UUID
    job_no: str
    scenario_key: str
    title: str
    status: str
    current_attempt_no: int
    retryable: bool = False
    error_code: str | None = None
    error_message: str | None = None
    result_summary: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class ServiceApiTaskDetailResponse(ServiceApiTaskSummaryResponse):
    input_payload: dict[str, Any]
    normalized_payload: dict[str, Any]
    max_retries: int | None = None
    last_success_result: TaskResultResponse | None = None
    attempts: list[TaskAttemptResponse]


class ServiceApiTaskResultResponse(BaseModel):
    task_id: uuid.UUID
    job_no: str
    status: str
    retryable: bool = False
    error_code: str | None = None
    error_message: str | None = None
    result_summary: dict[str, Any] | None = None
    result: TaskResultResponse | None = None
    finished_at: datetime | None = None


class ServiceApiAuthContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submitter_id: str
    submitter_name: str
    source_channel: str
