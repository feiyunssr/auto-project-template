from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


def _build_client(tmp_path, monkeypatch, require_hub_auth: bool) -> Iterator[TestClient]:
    database_path = tmp_path / "service-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.delenv("HUB_API_URL", raising=False)
    monkeypatch.delenv("HUB_SERVICE_KEY", raising=False)
    monkeypatch.setenv("REQUIRE_HUB_AUTH", "true" if require_hub_auth else "false")

    from apps.backend.core.config import get_settings

    get_settings.cache_clear()
    from apps.backend.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, monkeypatch, require_hub_auth=False)


@pytest.fixture
def auth_required_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, monkeypatch, require_hub_auth=True)
