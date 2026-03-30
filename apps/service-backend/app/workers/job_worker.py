from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services.orchestrator import JobOrchestrator
from app.repositories.tasks import TaskRepository

logger = logging.getLogger(__name__)


class JobWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        poll_interval_ms: int = 500,
        max_jobs_per_cycle: int = 2,
        heartbeat_path: str | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.poll_interval_ms = poll_interval_ms
        self.max_jobs_per_cycle = max_jobs_per_cycle
        self.heartbeat_path = Path(heartbeat_path) if heartbeat_path else None
        self._runner: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._active_jobs = 0
        self._processed_jobs = 0
        self._last_heartbeat_at: str | None = None

    async def start(self) -> None:
        if self._runner is None:
            self._stop.clear()
            self._runner = asyncio.create_task(self._run(), name="job-worker-runner")
            logger.info(
                "job_worker_started poll_interval_ms=%s max_jobs_per_cycle=%s",
                self.poll_interval_ms,
                self.max_jobs_per_cycle,
            )

    async def stop(self) -> None:
        self._stop.set()
        if self._runner:
            self._runner.cancel()
            await asyncio.gather(self._runner, return_exceptions=True)
            self._runner = None
        await self._write_heartbeat("stopped")
        logger.info("job_worker_stopped processed_jobs=%s", self._processed_jobs)

    def snapshot(self) -> dict[str, int | str]:
        return {
            "status": "running" if self._runner and not self._runner.done() else "stopped",
            "active_jobs": self._active_jobs,
            "processed_jobs": self._processed_jobs,
            "last_heartbeat_at": self._last_heartbeat_at or "",
        }

    async def _run(self) -> None:
        while not self._stop.is_set():
            async with self.session_factory() as session:
                queued_job_ids = await TaskRepository(session).list_queued_job_ids(limit=self.max_jobs_per_cycle)

            if not queued_job_ids:
                await self._write_heartbeat("idle")
                await asyncio.sleep(self.poll_interval_ms / 1000)
                continue

            for job_id in queued_job_ids:
                if self._stop.is_set():
                    break
                self._active_jobs += 1
                try:
                    async with self.session_factory() as session:
                        await JobOrchestrator(session).run_job(job_id)
                    self._processed_jobs += 1
                finally:
                    self._active_jobs -= 1
                    await self._write_heartbeat("running")

            await asyncio.sleep(0)

    async def _write_heartbeat(self, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._last_heartbeat_at = now
        if self.heartbeat_path is None:
            return

        payload = {
            "status": status,
            "active_jobs": self._active_jobs,
            "processed_jobs": self._processed_jobs,
            "last_heartbeat_at": now,
        }
        self.heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(self.heartbeat_path.write_text, json.dumps(payload), "utf-8")
