import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskCreateRequest(BaseModel):
    scenario_key: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=2, max_length=160)
    ai_profile_id: uuid.UUID | None = None
    source_channel: str | None = Field(default="hub", max_length=64)
    input_payload: dict[str, Any]


class TaskSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_no: str
    scenario_key: str
    title: str
    status: str
    current_attempt_no: int
    error_code: str | None = None
    error_message: str | None = None
    result_summary: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class TaskAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attempt_no: int
    workflow_stage: str
    provider_name: str
    provider_model: str
    status: str
    retryable: bool
    error_code: str | None = None
    error_message: str | None = None
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    external_request_id: str | None = None
    started_at: datetime
    finished_at: datetime | None = None


class TaskResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_no: int
    result_type: str
    structured_payload: dict[str, Any]
    preview_text: str | None = None
    quality_status: str
    review_comment: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    artifact_role: str
    storage_type: str
    uri: str
    mime_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(TaskSummaryResponse):
    input_payload: dict[str, Any]
    normalized_payload: dict[str, Any]
    submitted_by_hub_user_id: str
    submitted_by_name: str | None = None
    source_channel: str | None = None
    retryable: bool = False
    max_retries: int | None = None
    last_success_result: TaskResultResponse | None = None
    attempts: list[TaskAttemptResponse]
    results: list[TaskResultResponse]
    artifacts: list[TaskArtifactResponse]


class TaskListResponse(BaseModel):
    items: list[TaskSummaryResponse]
