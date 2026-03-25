from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    database_path = tmp_path / "service-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.delenv("HUB_API_URL", raising=False)
    monkeypatch.delenv("HUB_SERVICE_KEY", raising=False)

    from apps.backend.core.config import get_settings

    get_settings.cache_clear()
    from apps.backend.main import app

    with TestClient(app) as test_client:
        yield test_client
