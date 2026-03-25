from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.models import ServiceAiProfile


class AiProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_profiles(self, scenario_key: str | None = None) -> Sequence[ServiceAiProfile]:
        statement = select(ServiceAiProfile).where(ServiceAiProfile.is_active.is_(True))
        if scenario_key:
            statement = statement.where(ServiceAiProfile.scenario_key == scenario_key)
        statement = statement.order_by(ServiceAiProfile.is_default.desc(), ServiceAiProfile.updated_at.desc())
        result = await self.session.scalars(statement)
        return result.all()

    async def get_profile(self, profile_id: uuid.UUID) -> ServiceAiProfile | None:
        return await self.session.get(ServiceAiProfile, profile_id)

    async def get_by_key(self, profile_key: str) -> ServiceAiProfile | None:
        statement = select(ServiceAiProfile).where(ServiceAiProfile.profile_key == profile_key)
        return await self.session.scalar(statement)

    async def get_default_profile(self, scenario_key: str) -> ServiceAiProfile | None:
        statement = select(ServiceAiProfile).where(
            ServiceAiProfile.scenario_key == scenario_key,
            ServiceAiProfile.is_default.is_(True),
            ServiceAiProfile.is_active.is_(True),
        )
        return await self.session.scalar(statement)

    async def save_profile(self, profile: ServiceAiProfile) -> ServiceAiProfile:
        if profile.is_default:
            await self.session.execute(
                update(ServiceAiProfile)
                .where(ServiceAiProfile.scenario_key == profile.scenario_key)
                .values(is_default=False)
            )
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile
