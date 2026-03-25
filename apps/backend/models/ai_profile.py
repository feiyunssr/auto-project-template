import uuid

from sqlalchemy import Boolean, Float, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from apps.backend.db.base import Base
from apps.backend.models.mixins import TimestampMixin


class ServiceAiProfile(TimestampMixin, Base):
    __tablename__ = "service_ai_profile"
    __table_args__ = (Index("ix_service_ai_profile_profile_key", "profile_key", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_key: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_name: Mapped[str] = mapped_column(String(128), nullable=False)
    scenario_key: Mapped[str] = mapped_column(String(64), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    prompt_template: Mapped[str | None] = mapped_column(Text)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=1024)
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=5_000)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    concurrency_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    created_by_hub_user_id: Mapped[str | None] = mapped_column(String(64))
    updated_by_hub_user_id: Mapped[str | None] = mapped_column(String(64))
