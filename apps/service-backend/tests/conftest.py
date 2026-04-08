from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


def _build_client(tmp_path, monkeypatch, require_hub_auth: bool) -> Iterator[TestClient]:
    database_path = tmp_path / "service-test.db"
    heartbeat_path = tmp_path / "service-worker.json"
    monkeypatch.setenv("SERVICE_BACKEND_DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.setenv("SERVICE_BACKEND_WORKER_HEARTBEAT_PATH", str(heartbeat_path))
    monkeypatch.setenv("SERVICE_BACKEND_RUN_EMBEDDED_WORKER", "true")
    monkeypatch.setenv("SERVICE_BACKEND_ENABLE_SERVICE_API", "true")
    monkeypatch.setenv("SERVICE_BACKEND_SERVICE_API_BEARER_TOKEN", "test-service-token")
    monkeypatch.delenv("SERVICE_BACKEND_HUB_API_URL", raising=False)
    monkeypatch.delenv("SERVICE_BACKEND_HUB_SERVICE_KEY", raising=False)
    monkeypatch.setenv("SERVICE_BACKEND_REQUIRE_HUB_AUTH", "true" if require_hub_auth else "false")

    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, monkeypatch, require_hub_auth=False)


@pytest.fixture
def auth_required_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, monkeypatch, require_hub_auth=True)
