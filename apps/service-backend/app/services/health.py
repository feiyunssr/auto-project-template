from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import Settings
from app.repositories.tasks import TaskRepository
from app.schemas.ops import HealthCheckItem, HealthResponse


async def build_health_response(
    settings: Settings,
    session_factory: async_sessionmaker,
    worker,
    registration_snapshot: dict,
    instance_id: str,
    started_at: datetime,
) -> tuple[int, HealthResponse]:
    checks: dict[str, HealthCheckItem] = {}
    metrics = worker.snapshot()
    overall_status = "healthy"

    try:
        async with session_factory() as session:
            await session.execute(text("select 1"))
            metrics.update(await TaskRepository(session).health_counts())
        checks["database"] = HealthCheckItem(status="healthy", detail="database connection ok")
    except Exception as exc:  # noqa: BLE001
        checks["database"] = HealthCheckItem(status="unhealthy", detail=str(exc))
        overall_status = "unhealthy"

    queue_status = "healthy" if metrics["status"] == "running" else "degraded"
    checks["queue"] = HealthCheckItem(
        status=queue_status,
        detail=f"worker status: {metrics['status']}; last heartbeat: {metrics.get('last_heartbeat_at') or 'n/a'}",
    )
    if queue_status == "degraded" and overall_status == "healthy":
        overall_status = "degraded"

    registration_status = registration_snapshot.get("status", "degraded")
    checks["hub_registration"] = HealthCheckItem(
        status=registration_status,
        detail=registration_snapshot.get("last_error") or "registration ok",
    )
    if registration_status != "healthy" and overall_status == "healthy":
        overall_status = "degraded"

    checks["provider_adapter"] = HealthCheckItem(status="healthy", detail=settings.provider_mode)
    uptime = int((datetime.now(timezone.utc) - started_at).total_seconds())
    response = HealthResponse(
        status=overall_status,
        service=settings.service_key,
        version=settings.app_version,
        instance_id=instance_id,
        uptime_sec=uptime,
        checks=checks,
        metrics={k: int(v) for k, v in metrics.items() if k not in {"status", "last_heartbeat_at"}},
        timestamp=datetime.now(timezone.utc),
        registration=registration_snapshot,
    )
    return (503 if overall_status == "unhealthy" else 200), response
