import sys
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient


@contextmanager
def _build_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    database_path = tmp_path / "service-test.db"
    heartbeat_path = tmp_path / "service-worker.json"
    credentials_path = tmp_path / "hub-service-credentials.json"
    monkeypatch.setenv("SERVICE_BACKEND_DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.setenv("SERVICE_BACKEND_WORKER_HEARTBEAT_PATH", str(heartbeat_path))
    monkeypatch.setenv("SERVICE_BACKEND_HUB_SERVICE_CREDENTIALS_PATH", str(credentials_path))
    monkeypatch.setenv("SERVICE_BACKEND_RUN_EMBEDDED_WORKER", "true")
    monkeypatch.setenv("SERVICE_BACKEND_SERVICE_PUBLIC_BASE_URL", "http://127.0.0.1:11011")
    monkeypatch.delenv("SERVICE_BACKEND_HUB_API_URL", raising=False)
    monkeypatch.delenv("SERVICE_BACKEND_HUB_API_V1_PREFIX", raising=False)
    monkeypatch.delenv("SERVICE_BACKEND_HUB_SERVICE_KEY", raising=False)
    monkeypatch.delenv("SERVICE_BACKEND_HUB_SERVICE_ID", raising=False)
    monkeypatch.delenv("SERVICE_BACKEND_HUB_SERVICE_TOKEN", raising=False)
    monkeypatch.setenv("SERVICE_BACKEND_REQUIRE_HUB_AUTH", "false")

    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_well_known_manifest_exposes_auto_onboarding_contract(tmp_path, monkeypatch) -> None:
    with _build_client(tmp_path, monkeypatch) as client:
        response = client.get("/.well-known/ai-auto-manifest.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service_key"] == "auto-project-template"
    assert payload["entry_url"] == "http://127.0.0.1:11011"
    assert payload["healthcheck_url"] == "http://127.0.0.1:11011/healthz"
    assert payload["bootstrap_url"] == "http://127.0.0.1:11011/.well-known/ai-auto-bootstrap"
    assert "task_orchestration" in payload["capability_tags"]


def test_bootstrap_route_enables_hub_runtime_mode(tmp_path, monkeypatch) -> None:
    with _build_client(tmp_path, monkeypatch) as client:
        bootstrap_response = client.post(
            "/.well-known/ai-auto-bootstrap",
            json={
                "service_id": "00000000-0000-0000-0000-000000000555",
                "service_token": "runtime-secret",
                "hub_api_url": "https://hub.example.test",
                "hub_api_v1_prefix": "/api/runtime",
                "service_key": "auto-project-template",
            },
        )
        runtime_response = client.get("/api/v1/settings/runtime")

    assert bootstrap_response.status_code == 200
    assert runtime_response.status_code == 200
    runtime_payload = runtime_response.json()
    assert runtime_payload["hub_enabled"] is True
    assert runtime_payload["hub_mode"] == "bootstrap_pending"
    assert runtime_payload["hub_api_url"] == "https://hub.example.test"
    assert runtime_payload["hub_api_v1_prefix"] == "/api/runtime"
    assert runtime_payload["hub_registration"]["status"] == "healthy"
    assert runtime_payload["hub_telemetry"]["status"] == "pending"
    assert runtime_payload["hub_telemetry"]["service_id"] == "00000000-0000-0000-0000-000000000555"
