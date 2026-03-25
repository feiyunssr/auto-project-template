import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.backend.db.base import Base
from apps.backend.models.enums import JobStatus
from apps.backend.models.mixins import TimestampMixin


class ServiceJob(TimestampMixin, Base):
    __tablename__ = "service_job"
    __table_args__ = (
        Index("ix_service_job_status_created_at", "status", "created_at"),
        Index("ix_service_job_submitter_created_at", "submitted_by_hub_user_id", "created_at"),
        Index("ix_service_job_idempotency_key", "idempotency_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    submitted_by_hub_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    submitted_by_name: Mapped[str | None] = mapped_column(String(128))
    source_channel: Mapped[str | None] = mapped_column(String(64))
    scenario_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    ai_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("service_ai_profile.id"),
        nullable=True,
    )
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    normalized_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    normalized_payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    result_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=JobStatus.DRAFT.value)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    current_attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    attempts = relationship("ServiceJobAttempt", back_populates="job", cascade="all, delete-orphan")
    results = relationship("ServiceResult", back_populates="job", cascade="all, delete-orphan")
    artifacts = relationship("ServiceArtifact", back_populates="job", cascade="all, delete-orphan")
