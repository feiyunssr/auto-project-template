from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Auto Service Worker"
    app_version: str = "0.2.0"
    database_url: str = "sqlite+aiosqlite:///./service.db"
    log_level: str = "INFO"
    poll_interval_ms: int = 500
    max_jobs_per_cycle: int = 2
    heartbeat_path: str = ".runtime/service-worker.json"

    model_config = SettingsConfigDict(
        env_prefix="SERVICE_WORKER_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
