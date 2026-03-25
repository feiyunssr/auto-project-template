import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AiProfileUpsertRequest(BaseModel):
    profile_key: str = Field(min_length=2, max_length=64)
    profile_name: str = Field(min_length=2, max_length=128)
    scenario_key: str = Field(min_length=2, max_length=64)
    is_default: bool = False
    is_active: bool = True
    provider_name: str = Field(min_length=2, max_length=64)
    model_name: str = Field(min_length=2, max_length=128)
    system_prompt: str | None = None
    prompt_template: str | None = None
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=64, le=16384)
    timeout_ms: int = Field(default=5000, ge=100, le=120000)
    max_retries: int = Field(default=2, ge=0, le=5)
    concurrency_limit: int = Field(default=2, ge=1, le=10)


class AiProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    profile_key: str
    profile_name: str
    scenario_key: str
    is_default: bool
    is_active: bool
    provider_name: str
    model_name: str
    system_prompt: str | None = None
    prompt_template: str | None = None
    temperature: float
    max_tokens: int
    timeout_ms: int
    max_retries: int
    concurrency_limit: int
    created_by_hub_user_id: str | None = None
    updated_by_hub_user_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AiProfileListResponse(BaseModel):
    items: list[AiProfileResponse]
