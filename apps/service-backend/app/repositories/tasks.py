from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ServiceArtifact, ServiceJob, ServiceJobAttempt, ServiceResult
from app.models.enums import JobStatus


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(self, job: ServiceJob) -> ServiceJob:
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def get_job_by_id(self, job_id: uuid.UUID) -> ServiceJob | None:
        statement = (
            select(ServiceJob)
            .where(ServiceJob.id == job_id)
            .options(
                selectinload(ServiceJob.attempts),
                selectinload(ServiceJob.results),
                selectinload(ServiceJob.artifacts),
            )
        )
        return await self.session.scalar(statement)

    async def get_job_by_idempotency_key(self, idempotency_key: str) -> ServiceJob | None:
        statement = select(ServiceJob).where(ServiceJob.idempotency_key == idempotency_key)
        return await self.session.scalar(statement)

    async def list_queued_job_ids(self, limit: int = 10) -> list[uuid.UUID]:
        statement = (
            select(ServiceJob.id)
            .where(ServiceJob.status == JobStatus.QUEUED.value)
            .order_by(ServiceJob.priority.asc(), ServiceJob.created_at.asc())
            .limit(limit)
        )
        rows = await self.session.scalars(statement)
        return list(rows.all())

    async def list_jobs(
        self,
        hub_user_id: str,
        status: str | None = None,
        limit: int = 20,
    ) -> Sequence[ServiceJob]:
        statement = select(ServiceJob).where(ServiceJob.submitted_by_hub_user_id == hub_user_id)
        if status:
            statement = statement.where(ServiceJob.status == status)
        statement = statement.order_by(desc(ServiceJob.created_at)).limit(limit)
        result = await self.session.scalars(statement)
        return result.all()

    async def add_attempt(self, attempt: ServiceJobAttempt) -> ServiceJobAttempt:
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def add_result(self, result: ServiceResult) -> ServiceResult:
        self.session.add(result)
        await self.session.flush()
        return result

    async def add_artifact(self, artifact: ServiceArtifact) -> ServiceArtifact:
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def count_results_for_job(self, job_id: uuid.UUID) -> int:
        statement = select(func.count(ServiceResult.id)).where(ServiceResult.job_id == job_id)
        return int((await self.session.scalar(statement)) or 0)

    async def get_latest_success_result(self, job_id: uuid.UUID) -> ServiceResult | None:
        statement = (
            select(ServiceResult)
            .where(ServiceResult.job_id == job_id)
            .order_by(desc(ServiceResult.version_no))
            .limit(1)
        )
        return await self.session.scalar(statement)

    async def health_counts(self) -> dict[str, int]:
        ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
        queued = await self.session.scalar(
            select(func.count(ServiceJob.id)).where(ServiceJob.status == JobStatus.QUEUED.value)
        )
        running = await self.session.scalar(
            select(func.count(ServiceJob.id)).where(ServiceJob.status == JobStatus.RUNNING.value)
        )
        failed_recent = await self.session.scalar(
            select(func.count(ServiceJob.id)).where(
                ServiceJob.status == JobStatus.FAILED.value,
                ServiceJob.updated_at >= ten_minutes_ago,
            )
        )
        return {
            "queued_jobs": int(queued or 0),
            "running_jobs": int(running or 0),
            "failed_jobs_10m": int(failed_recent or 0),
        }
