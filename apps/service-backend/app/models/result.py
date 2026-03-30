import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ServiceResult(TimestampMixin, Base):
    __tablename__ = "service_result"
    __table_args__ = (Index("ix_service_result_job_version", "job_id", "version_no", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("service_job.id"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    result_type: Mapped[str] = mapped_column(String(64), nullable=False)
    structured_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    preview_text: Mapped[str | None] = mapped_column(Text)
    quality_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    review_comment: Mapped[str | None] = mapped_column(Text)

    job = relationship("ServiceJob", back_populates="results")
