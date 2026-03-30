from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Auto Service Worker"
    app_version: str = "0.2.0"
    database_url: str = "sqlite+aiosqlite:///./service.db"
    log_level: str = "INFO"
    environment: str = "local"
    service_key: str = "auto-project-template"
    poll_interval_ms: int = 500
    max_jobs_per_cycle: int = 2
    heartbeat_path: str = ".runtime/service-worker.json"
    hub_service_credentials_path: str = Field(
        default=".runtime/hub-service-credentials.json",
        validation_alias=AliasChoices(
            "SERVICE_WORKER_HUB_SERVICE_CREDENTIALS_PATH",
            "SERVICE_BACKEND_HUB_SERVICE_CREDENTIALS_PATH",
            "HUB_SERVICE_CREDENTIALS_PATH",
        ),
    )
    heartbeat_interval_sec: int = 30
    hub_api_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SERVICE_WORKER_HUB_API_URL",
            "SERVICE_BACKEND_HUB_API_URL",
            "HUB_API_URL",
        ),
    )
    hub_api_v1_prefix: str = Field(
        default="/api/v1",
        validation_alias=AliasChoices(
            "SERVICE_WORKER_HUB_API_V1_PREFIX",
            "SERVICE_BACKEND_HUB_API_V1_PREFIX",
            "HUB_API_V1_PREFIX",
        ),
    )
    hub_service_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SERVICE_WORKER_HUB_SERVICE_ID",
            "SERVICE_BACKEND_HUB_SERVICE_ID",
            "HUB_SERVICE_ID",
        ),
    )
    hub_service_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SERVICE_WORKER_HUB_SERVICE_TOKEN",
            "SERVICE_BACKEND_HUB_SERVICE_TOKEN",
            "HUB_SERVICE_TOKEN",
        ),
    )
    hub_request_timeout_seconds: float = Field(
        default=5.0,
        validation_alias=AliasChoices(
            "SERVICE_WORKER_HUB_REQUEST_TIMEOUT_SECONDS",
            "SERVICE_BACKEND_HUB_REQUEST_TIMEOUT_SECONDS",
            "HUB_REQUEST_TIMEOUT_SECONDS",
        ),
    )

    model_config = SettingsConfigDict(
        env_prefix="SERVICE_WORKER_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
