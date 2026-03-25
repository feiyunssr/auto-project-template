import uuid
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.backend.db.base import Base
from apps.backend.models.mixins import TimestampMixin


class ServiceArtifact(TimestampMixin, Base):
    __tablename__ = "service_artifact"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("service_job.id"), nullable=False)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("service_job_attempt.id"))
    artifact_role: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_type: Mapped[str] = mapped_column(String(32), nullable=False, default="inline")
    uri: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    checksum: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)

    job = relationship("ServiceJob", back_populates="artifacts")
