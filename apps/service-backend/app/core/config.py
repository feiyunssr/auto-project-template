from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SERVICE_BACKEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Auto Service Backend"
    app_version: str = "0.2.0"
    api_v1_prefix: str = "/api/v1"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = Field(
        default="sqlite+aiosqlite:///./service.db",
        validation_alias=AliasChoices("SERVICE_BACKEND_DATABASE_URL", "DATABASE_URL"),
    )

    hub_api_url: str | None = Field(default=None, validation_alias=AliasChoices("SERVICE_BACKEND_HUB_API_URL", "HUB_API_URL"))
    hub_service_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SERVICE_BACKEND_HUB_SERVICE_KEY", "HUB_SERVICE_KEY"),
    )
    require_hub_auth: bool = Field(
        default=False,
        validation_alias=AliasChoices("SERVICE_BACKEND_REQUIRE_HUB_AUTH", "REQUIRE_HUB_AUTH"),
    )
    dev_hub_user_id: str = "local-dev-user"
    dev_hub_user_name: str = "Local Operator"
    dev_hub_role: str = "operator"
    service_public_base_url: str = "http://127.0.0.1:11010"
    cors_allowed_origins: str = (
        "http://127.0.0.1:11011,http://localhost:11011,http://127.0.0.1:4173,http://localhost:4173"
    )
    cors_allowed_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1|\[::1\]|\d{1,3}(?:\.\d{1,3}){3}|\[[0-9a-fA-F:]+\])(?::\d+)?$"
    )
    service_key: str = "auto-project-template"
    service_display_name: str = "AI Auto Child Service Template"
    service_description: str = "Standard AI Auto data-plane child service template."
    service_team: str = "growth-ai"
    service_capabilities: str = "task_orchestration,healthz,ai_profiles"

    run_embedded_worker: bool = False
    worker_poll_interval_ms: int = 500
    worker_max_jobs_per_cycle: int = 2
    worker_heartbeat_timeout_sec: int = 30
    worker_heartbeat_path: str = str(Path(".runtime") / "service-worker.json")
    heartbeat_interval_sec: int = 30
    registration_backoff_sec: int = 5
    default_provider_name: str = "mock"
    provider_mode: Literal["mock"] = "mock"

    default_timeout_ms: int = Field(default=5_000, ge=100, le=120_000)
    default_max_retries: int = Field(default=2, ge=0, le=5)
    default_concurrency_limit: int = Field(default=2, ge=1, le=10)

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
