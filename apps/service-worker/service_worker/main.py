from __future__ import annotations

import asyncio
import uuid

import app.models  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.logging import configure_logging
from app.services.hub_telemetry import HubTelemetryService
from app.workers.job_worker import JobWorker
from service_worker.settings import settings


def create_session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(settings.database_url, future=True, echo=False)
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def run_worker() -> None:
    hub_telemetry = HubTelemetryService(settings, instance_id=str(uuid.uuid4()))
    worker = JobWorker(
        session_factory=create_session_factory(),
        poll_interval_ms=settings.poll_interval_ms,
        max_jobs_per_cycle=settings.max_jobs_per_cycle,
        heartbeat_path=settings.heartbeat_path,
        hub_telemetry=hub_telemetry,
    )
    await worker.start()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await worker.stop()


def main() -> None:
    configure_logging(settings.log_level)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
