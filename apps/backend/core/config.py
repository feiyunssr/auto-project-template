from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ai-auto-hub-service"
    app_version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./service.db"

    hub_api_url: str | None = None
    hub_service_key: str | None = None
    require_hub_auth: bool = False
    dev_hub_user_id: str = "local-dev-user"
    dev_hub_user_name: str = "Local Operator"
    dev_hub_role: str = "operator"
    service_public_base_url: str = "http://localhost:8000"
    cors_allowed_origins: str = (
        "http://127.0.0.1:4173,http://localhost:4173,http://127.0.0.1:5173,http://localhost:5173"
    )
    cors_allowed_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1|\[::1\]|\d{1,3}(?:\.\d{1,3}){3}|\[[0-9a-fA-F:]+\])(?::\d+)?$"
    )
    service_key: str = "auto-project-template"
    service_display_name: str = "AI Auto Hub Service Template"
    service_description: str = "Standard AI Auto Hub child service backend."
    service_team: str = "growth-ai"
    service_capabilities: str = "task_orchestration,healthz,ai_profiles"

    worker_poll_interval_ms: int = 250
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
