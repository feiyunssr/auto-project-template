from pydantic import BaseModel, Field


class AutoOnboardingManifestResponse(BaseModel):
    service_key: str
    display_name: str
    description: str
    category: str
    owner_name: str
    service_type: str
    entry_url: str
    base_url: str
    healthcheck_url: str
    bootstrap_url: str
    capability_tags: list[str]
    permission_tags: list[str]


class AutoOnboardingBootstrapRequest(BaseModel):
    service_id: str = Field(min_length=1)
    service_token: str = Field(min_length=1)
    hub_api_url: str = Field(min_length=1)
    hub_api_v1_prefix: str = Field(default="/api/v1", min_length=1)
    service_key: str | None = None


class AutoOnboardingBootstrapResponse(BaseModel):
    status: str
    service_id: str
    hub_api_url: str
    hub_api_v1_prefix: str
