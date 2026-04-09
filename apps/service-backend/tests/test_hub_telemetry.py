from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from app.core.config import Settings
from app.services.hub_telemetry import HubTelemetryService


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None


class _FakeAsyncClient:
    def __init__(self, *, recorder: list[dict], **_: object) -> None:
        self.recorder = recorder

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, path: str, *, json: dict, headers: dict) -> _FakeResponse:
        self.recorder.append({"path": path, "json": json, "headers": headers})
        return _FakeResponse()


def _build_service(recorder: list[dict]) -> HubTelemetryService:
    settings = Settings(
        hub_api_url="https://hub.example.test",
        hub_service_id="00000000-0000-0000-0000-000000000123",
        hub_service_token="secret-token",
        hub_service_credentials_path="/tmp/auto-project-template-missing-hub-service-credentials.json",
    )
    return HubTelemetryService(
        settings,
        instance_id="instance-1",
        client_factory=lambda **kwargs: _FakeAsyncClient(recorder=recorder, **kwargs),
    )


@pytest.mark.asyncio
async def test_emit_heartbeat_posts_to_hub_telemetry_endpoint() -> None:
    recorder: list[dict] = []
    service = _build_service(recorder)

    ok = await service.emit_heartbeat()

    assert ok is True
    assert recorder[0]["path"] == "/api/v1/services/00000000-0000-0000-0000-000000000123/heartbeat"
    assert recorder[0]["headers"]["Authorization"] == "Bearer secret-token"
    assert recorder[0]["json"]["service_version"] == "0.2.0"
    assert recorder[0]["json"]["metadata"]["instance_id"] == "instance-1"
    assert recorder[0]["json"]["metadata"]["service_public_base_url"] == "http://192.168.1.242:11011"
    assert recorder[0]["json"]["metadata"]["healthcheck_url"] == "http://192.168.1.242:11011/healthz"
    assert service.snapshot()["status"] == "healthy"


@pytest.mark.asyncio
async def test_emit_job_failed_posts_error_details_to_hub() -> None:
    recorder: list[dict] = []
    service = _build_service(recorder)

    ok = await service.emit_job_failed(
        job_id="job-1",
        attempt_no=3,
        occurred_at=datetime(2026, 3, 30, 12, 0, tzinfo=UTC),
        status="failed",
        duration_ms=1250,
        error_code="PROVIDER_TIMEOUT_FINAL",
        error_summary="Provider timed out after 100 ms.",
        metadata={"scenario_key": "general", "retryable": True},
    )

    assert ok is True
    event = recorder[0]["json"]["events"][0]
    assert recorder[0]["path"] == "/api/v1/services/00000000-0000-0000-0000-000000000123/events"
    assert event["event_type"] == "job_failed"
    assert event["error_code"] == "PROVIDER_TIMEOUT_FINAL"
    assert event["error_summary"] == "Provider timed out after 100 ms."
    assert event["metadata"]["retryable"] is True


@pytest.mark.asyncio
async def test_emit_job_event_is_noop_when_hub_credentials_missing(tmp_path) -> None:
    service = HubTelemetryService(
        Settings(
            hub_service_credentials_path=str(tmp_path / "missing-hub-service-credentials.json"),
        ),
        instance_id="instance-1",
    )

    ok = await service.emit_job_succeeded(
        job_id="job-1",
        attempt_no=1,
        occurred_at=datetime(2026, 3, 30, 12, 0, tzinfo=UTC),
        status="succeeded",
        duration_ms=450,
        metadata={"scenario_key": "general"},
    )

    assert ok is False
    assert service.snapshot()["status"] == "degraded"


@pytest.mark.asyncio
async def test_emit_heartbeat_reads_credentials_from_runtime_file(tmp_path) -> None:
    recorder: list[dict] = []
    credentials_path = tmp_path / "hub-service-credentials.json"
    credentials_path.write_text(
        json.dumps(
            {
                "service_id": "00000000-0000-0000-0000-000000000999",
                "service_token": "runtime-secret",
                "hub_api_url": "https://hub.example.test",
                "hub_api_v1_prefix": "/api/runtime",
            }
        ),
        encoding="utf-8",
    )
    service = HubTelemetryService(
        Settings(
            hub_service_credentials_path=str(credentials_path),
        ),
        instance_id="instance-1",
        client_factory=lambda **kwargs: _FakeAsyncClient(recorder=recorder, **kwargs),
    )

    ok = await service.emit_heartbeat()

    assert ok is True
    assert recorder[0]["path"] == "/api/runtime/services/00000000-0000-0000-0000-000000000999/heartbeat"
    assert recorder[0]["headers"]["Authorization"] == "Bearer runtime-secret"
