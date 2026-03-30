from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)


class HubTelemetrySettings(Protocol):
    app_name: str
    app_version: str
    environment: str
    service_key: str
    heartbeat_interval_sec: int
    hub_api_url: str | None
    hub_api_v1_prefix: str
    hub_service_id: str | None
    hub_service_token: str | None
    hub_service_credentials_path: str
    hub_request_timeout_seconds: float


@dataclass(slots=True)
class TelemetrySnapshot:
    status: str = "degraded"
    service_id: str | None = None
    last_error: str | None = None
    last_heartbeat_at: str | None = None
    last_event_at: str | None = None


class HubTelemetryService:
    def __init__(
        self,
        settings: HubTelemetrySettings,
        *,
        instance_id: str,
        client_factory: Callable[..., httpx.AsyncClient] | None = None,
    ) -> None:
        self.settings = settings
        self.instance_id = instance_id
        self.client_factory = client_factory or httpx.AsyncClient
        self.credentials_path = Path(settings.hub_service_credentials_path)
        self.service_id = settings.hub_service_id
        self.service_token = settings.hub_service_token
        self._load_credentials_from_file(update_snapshot=False)
        self.snapshot_state = TelemetrySnapshot(
            status="pending" if self.is_configured else "degraded",
            service_id=self.service_id,
        )
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    @property
    def is_configured(self) -> bool:
        self._load_credentials_from_file()
        return bool(self.settings.hub_api_url and self.service_id and self.service_token)

    def configure_credentials(self, service_id: str, service_token: str) -> None:
        self.service_id = service_id
        self.service_token = service_token
        self.snapshot_state.service_id = service_id
        self.snapshot_state.status = "pending"
        self.snapshot_state.last_error = None
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        self.credentials_path.write_text(
            json.dumps(
                {
                    "service_id": service_id,
                    "service_token": service_token,
                }
            ),
            encoding="utf-8",
        )

    async def start(self) -> None:
        if self._task is None:
            self._stop.clear()
            self._task = asyncio.create_task(self._run_loop(), name="hub-telemetry-loop")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    def snapshot(self) -> dict[str, str | None]:
        return asdict(self.snapshot_state)

    async def emit_heartbeat(self) -> bool:
        sent_at = self._now().isoformat()
        ok = await self._post_json(
            self._telemetry_path("/heartbeat"),
            {
                "sent_at": sent_at,
                "service_version": self.settings.app_version,
                "metadata": {
                    "component": "service-backend",
                    "environment": self.settings.environment,
                    "instance_id": self.instance_id,
                    "service_key": self.settings.service_key,
                },
            },
        )
        if ok:
            self.snapshot_state.last_heartbeat_at = sent_at
        return ok

    async def emit_job_succeeded(
        self,
        *,
        job_id: str,
        attempt_no: int,
        occurred_at: datetime,
        status: str,
        duration_ms: int | None,
        metadata: dict[str, Any],
    ) -> bool:
        return await self._emit_event(
            source_event_id=(
                f"job_succeeded:{job_id}:{attempt_no}:{self._event_suffix(occurred_at)}"
            ),
            event_type="job_succeeded",
            job_id=job_id,
            occurred_at=occurred_at,
            status=status,
            duration_ms=duration_ms,
            error_code=None,
            error_summary=None,
            metadata=metadata,
        )

    async def emit_job_failed(
        self,
        *,
        job_id: str,
        attempt_no: int,
        occurred_at: datetime,
        status: str,
        duration_ms: int | None,
        error_code: str | None,
        error_summary: str | None,
        metadata: dict[str, Any],
    ) -> bool:
        return await self._emit_event(
            source_event_id=(
                f"job_failed:{job_id}:{attempt_no}:{self._event_suffix(occurred_at)}"
            ),
            event_type="job_failed",
            job_id=job_id,
            occurred_at=occurred_at,
            status=status,
            duration_ms=duration_ms,
            error_code=error_code,
            error_summary=error_summary,
            metadata=metadata,
        )

    async def _run_loop(self) -> None:
        while not self._stop.is_set():
            if not self.is_configured:
                self.snapshot_state.status = "degraded"
                self.snapshot_state.last_error = (
                    "Waiting for HUB_SERVICE_ID and HUB_SERVICE_TOKEN bootstrap credentials."
                )
                await asyncio.sleep(max(self.settings.heartbeat_interval_sec, 5))
                continue
            await self.emit_heartbeat()
            await asyncio.sleep(max(self.settings.heartbeat_interval_sec, 5))

    async def _emit_event(
        self,
        *,
        source_event_id: str,
        event_type: str,
        job_id: str,
        occurred_at: datetime,
        status: str,
        duration_ms: int | None,
        error_code: str | None,
        error_summary: str | None,
        metadata: dict[str, Any],
    ) -> bool:
        ok = await self._post_json(
            self._telemetry_path("/events"),
            {
                "events": [
                    {
                        "source_event_id": source_event_id,
                        "event_type": event_type,
                        "job_id": job_id,
                        "occurred_at": occurred_at.isoformat(),
                        "status": status,
                        "duration_ms": duration_ms,
                        "error_code": error_code,
                        "error_summary": error_summary,
                        "metadata": metadata,
                    }
                ]
            },
        )
        if ok:
            self.snapshot_state.last_event_at = occurred_at.isoformat()
        return ok

    async def _post_json(self, path: str, payload: dict[str, Any]) -> bool:
        self._load_credentials_from_file()
        if not self.is_configured:
            return False

        try:
            async with self.client_factory(
                base_url=self.settings.hub_api_url,
                timeout=self.settings.hub_request_timeout_seconds,
            ) as client:
                response = await client.post(
                    path,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.service_token}"},
                )
                response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            self.snapshot_state.status = "degraded"
            self.snapshot_state.last_error = str(exc)
            logger.warning("hub_telemetry_post_failed path=%s error=%s", path, exc)
            return False

        self.snapshot_state.status = "healthy"
        self.snapshot_state.last_error = None
        return True

    def _telemetry_path(self, suffix: str) -> str:
        prefix = self.settings.hub_api_v1_prefix.rstrip("/")
        return f"{prefix}/services/{self.service_id}{suffix}"

    def _load_credentials_from_file(self, *, update_snapshot: bool = True) -> None:
        if not self.credentials_path.exists():
            return
        try:
            payload = json.loads(self.credentials_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("hub_telemetry_credentials_load_failed error=%s", exc)
            return

        service_id = payload.get("service_id")
        service_token = payload.get("service_token")
        if not service_id or not service_token:
            return

        self.service_id = str(service_id)
        self.service_token = str(service_token)
        if update_snapshot and hasattr(self, "snapshot_state"):
            self.snapshot_state.service_id = self.service_id

    @staticmethod
    def _event_suffix(occurred_at: datetime) -> int:
        return int(occurred_at.timestamp() * 1000)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)
