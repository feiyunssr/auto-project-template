import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProviderMode = Literal["mock"]
HubMode = Literal["local_fallback", "bootstrap_pending", "connected", "degraded"]


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


class ProviderOptionResponse(BaseModel):
    provider_name: str
    provider_label: str
    supported_scenarios: list[str]


class AiScenarioRuntimeResponse(BaseModel):
    scenario_key: str
    scenario_label: str
    configured_profile_key: str | None = None
    effective_profile_key: str | None = None
    effective_profile_name: str | None = None
    effective_provider_name: str | None = None
    resolution_source: str | None = None
    active_profile_count: int = 0
    total_profile_count: int = 0


class HubRuntimeStatusResponse(BaseModel):
    status: str
    registration_id: str | None = None
    service_id: str | None = None
    lease_ttl_sec: int | None = None
    last_error: str | None = None
    last_heartbeat_at: str | None = None
    last_event_at: str | None = None


class AiRuntimeSettingsResponse(BaseModel):
    provider_mode: ProviderMode
    default_provider_name: str
    supported_providers: list[ProviderOptionResponse]
    require_hub_auth: bool
    hub_enabled: bool
    hub_mode: HubMode
    hub_api_url: str | None = None
    hub_api_v1_prefix: str
    service_public_base_url: str
    hub_registration: HubRuntimeStatusResponse
    hub_telemetry: HubRuntimeStatusResponse
    scenarios: list[AiScenarioRuntimeResponse]
