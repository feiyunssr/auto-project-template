from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker

from apps.backend.services.orchestrator import JobOrchestrator

logger = logging.getLogger(__name__)


class JobWorker:
    def __init__(self, session_factory: async_sessionmaker, concurrency_limit: int = 2) -> None:
        self.session_factory = session_factory
        self.concurrency_limit = concurrency_limit
        self.queue: asyncio.Queue[uuid.UUID] = asyncio.Queue()
        self._runner: asyncio.Task | None = None
        self._active: set[asyncio.Task] = set()
        self._semaphore = asyncio.Semaphore(concurrency_limit)
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._runner is None:
            self._stop.clear()
            self._runner = asyncio.create_task(self._run(), name="job-worker-runner")
            logger.info("job_worker_started concurrency_limit=%s", self.concurrency_limit)

    async def stop(self) -> None:
        self._stop.set()
        if self._runner:
            self._runner.cancel()
            await asyncio.gather(self._runner, return_exceptions=True)
            self._runner = None
        if self._active:
            for task in list(self._active):
                task.cancel()
            await asyncio.gather(*self._active, return_exceptions=True)
        logger.info("job_worker_stopped active_jobs=%s queued_jobs=%s", len(self._active), self.queue.qsize())

    async def enqueue(self, job_id: uuid.UUID) -> None:
        await self.queue.put(job_id)
        logger.info("job_enqueued job_id=%s queued_jobs=%s", job_id, self.queue.qsize())

    def snapshot(self) -> dict[str, int | str]:
        return {
            "status": "running" if self._runner and not self._runner.done() else "stopped",
            "queued_jobs": self.queue.qsize(),
            "running_jobs": len(self._active),
        }

    async def _run(self) -> None:
        while not self._stop.is_set():
            job_id = await self.queue.get()
            logger.info("job_dequeued job_id=%s remaining_queue=%s", job_id, self.queue.qsize())
            task = asyncio.create_task(self._consume(job_id), name=f"job-{job_id}")
            self._active.add(task)
            task.add_done_callback(self._active.discard)

    async def _consume(self, job_id: uuid.UUID) -> None:
        async with self._semaphore:
            async with self.session_factory() as session:
                orchestrator = JobOrchestrator(session)
                await orchestrator.run_job(job_id)
