from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.core.config import Settings
from app.services.hub_bootstrap import load_hub_bootstrap_credentials
from app.services.hub_telemetry import HubTelemetryService

logger = logging.getLogger(__name__)


@dataclass
class RegistrationSnapshot:
    status: str = "degraded"
    registration_id: str | None = None
    lease_ttl_sec: int = 60
    last_error: str | None = None
    last_heartbeat_at: str | None = None


class HubRegistrationService:
    def __init__(
        self,
        settings: Settings,
        instance_id: str,
        *,
        hub_telemetry: HubTelemetryService | None = None,
    ) -> None:
        self.settings = settings
        self.instance_id = instance_id
        self.hub_telemetry = hub_telemetry
        self.snapshot_state = RegistrationSnapshot(
            status=self._initial_status(),
        )
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task is None:
            self._stop.clear()
            if self._can_use_internal_registration():
                try:
                    await self._sync_once()
                except Exception as exc:  # noqa: BLE001
                    self.snapshot_state.status = "degraded"
                    self.snapshot_state.last_error = str(exc)
                    logger.warning("hub_registration_initial_sync_failed error=%s", exc)
            else:
                self.refresh_bootstrap_state()
            self._task = asyncio.create_task(self._run_loop(), name="hub-registration-loop")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    def snapshot(self) -> dict[str, str | int | None]:
        return asdict(self.snapshot_state)

    def refresh_bootstrap_state(self) -> None:
        if self._has_bootstrap_credentials():
            self.snapshot_state.status = "healthy"
            self.snapshot_state.last_error = None
            return
        if self._effective_hub_api_url():
            self.snapshot_state.status = "pending"
            self.snapshot_state.last_error = "Waiting for Hub auto-onboarding bootstrap credentials."
            return
        self.snapshot_state.status = "degraded"
        self.snapshot_state.last_error = "HUB_API_URL or bootstrap credentials are not configured."

    async def _run_loop(self) -> None:
        if not self._can_use_internal_registration():
            while not self._stop.is_set():
                self.refresh_bootstrap_state()
                await asyncio.sleep(max(self.settings.heartbeat_interval_sec, 5))
            return

        async with httpx.AsyncClient(base_url=self.settings.hub_api_url, timeout=5.0) as client:
            backoff = self.settings.registration_backoff_sec
            while not self._stop.is_set():
                try:
                    await self._sync_once(client)
                    backoff = self.settings.registration_backoff_sec
                    await asyncio.sleep(max(5, self.snapshot_state.lease_ttl_sec // 2))
                except Exception as exc:  # noqa: BLE001
                    self.snapshot_state.status = "degraded"
                    self.snapshot_state.last_error = str(exc)
                    logger.warning("hub_registration_failed backoff_sec=%s error=%s", backoff, exc)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 60)

    async def _sync_once(self, client: httpx.AsyncClient | None = None) -> None:
        if client is None:
            async with httpx.AsyncClient(
                base_url=self.settings.hub_api_url,
                timeout=5.0,
            ) as owned_client:
                await self._sync_once(owned_client)
                return
        if self.snapshot_state.registration_id is None:
            await self._register(client)
        else:
            await self._heartbeat(client)

    async def _register(self, client: httpx.AsyncClient) -> None:
        response = await client.post(
            "/internal/services/register",
            headers={"Authorization": f"Bearer {self.settings.hub_service_key}"},
            json={
                "service_key": self.settings.service_key,
                "display_name": self.settings.service_display_name,
                "description": self.settings.service_description,
                "version": self.settings.app_version,
                "base_url": self.settings.service_public_base_url,
                "healthz_url": f"{self.settings.service_public_base_url}/healthz",
                "team": self.settings.service_team,
                "environment": self.settings.environment,
                "capabilities": self.settings.service_capabilities.split(","),
                "instance_id": self.instance_id,
            },
        )
        response.raise_for_status()
        payload = response.json()
        self.snapshot_state.registration_id = payload.get("registration_id", f"local-{uuid4()}")
        self.snapshot_state.lease_ttl_sec = int(payload.get("lease_ttl_sec", 60))
        if self.hub_telemetry is not None:
            service_id = payload.get("service_id")
            service_token = payload.get("service_token")
            if service_id and service_token:
                self.hub_telemetry.configure_credentials(
                    str(service_id),
                    str(service_token),
                )
        self.snapshot_state.status = "healthy"
        self.snapshot_state.last_error = None
        logger.info(
            "hub_registered registration_id=%s lease_ttl_sec=%s instance_id=%s",
            self.snapshot_state.registration_id,
            self.snapshot_state.lease_ttl_sec,
            self.instance_id,
        )

    async def _heartbeat(self, client: httpx.AsyncClient) -> None:
        response = await client.post(
            "/internal/services/heartbeat",
            headers={"Authorization": f"Bearer {self.settings.hub_service_key}"},
            json={
                "registration_id": self.snapshot_state.registration_id,
                "instance_id": self.instance_id,
                "version": self.settings.app_version,
            },
        )
        response.raise_for_status()
        self.snapshot_state.status = "healthy"
        self.snapshot_state.last_heartbeat_at = datetime.now(timezone.utc).isoformat()
        self.snapshot_state.last_error = None
        logger.info(
            "hub_heartbeat_ok registration_id=%s heartbeat_at=%s",
            self.snapshot_state.registration_id,
            self.snapshot_state.last_heartbeat_at,
        )

    def _effective_hub_api_url(self) -> str | None:
        if self.settings.hub_api_url:
            return self.settings.hub_api_url
        if self.hub_telemetry is not None and self.hub_telemetry.hub_enabled:
            return self.hub_telemetry.hub_api_url
        credentials = load_hub_bootstrap_credentials(self.settings.hub_service_credentials_path)
        if credentials is None:
            return None
        return credentials.hub_api_url

    def _has_bootstrap_credentials(self) -> bool:
        if self.hub_telemetry is not None and self.hub_telemetry.is_configured:
            return True
        return load_hub_bootstrap_credentials(self.settings.hub_service_credentials_path) is not None

    def _can_use_internal_registration(self) -> bool:
        return bool(self.settings.hub_api_url and self.settings.hub_service_key)

    def _initial_status(self) -> str:
        if self._can_use_internal_registration():
            return "pending"
        if self._has_bootstrap_credentials():
            return "healthy"
        if self._effective_hub_api_url():
            return "pending"
        return "degraded"
