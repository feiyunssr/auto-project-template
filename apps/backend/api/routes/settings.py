import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.dependencies import get_auth_context, get_db_session
from apps.backend.models import ServiceAiProfile
from apps.backend.repositories.ai_profiles import AiProfileRepository
from apps.backend.schemas.common import AuthContext
from apps.backend.schemas.settings import AiProfileListResponse, AiProfileResponse, AiProfileUpsertRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])
logger = logging.getLogger(__name__)


@router.get("/ai-profiles", response_model=AiProfileListResponse)
async def list_ai_profiles(
    scenario_key: str | None = None,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> AiProfileListResponse:
    profiles = await AiProfileRepository(session).list_profiles(scenario_key=scenario_key)
    return AiProfileListResponse(items=[AiProfileResponse.model_validate(profile) for profile in profiles])


@router.post("/ai-profiles", response_model=AiProfileResponse)
async def upsert_ai_profile(
    payload: AiProfileUpsertRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> AiProfileResponse:
    repo = AiProfileRepository(session)
    profile = await repo.get_by_key(payload.profile_key)
    if profile is None:
        profile = ServiceAiProfile(
            profile_key=payload.profile_key,
            created_by_hub_user_id=auth.hub_user_id,
            updated_by_hub_user_id=auth.hub_user_id,
        )

    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    profile.updated_by_hub_user_id = auth.hub_user_id
    await repo.save_profile(profile)
    await session.commit()
    logger.info(
        "ai_profile_saved profile_id=%s profile_key=%s scenario=%s hub_user_id=%s",
        profile.id,
        profile.profile_key,
        profile.scenario_key,
        auth.hub_user_id,
    )
    return AiProfileResponse.model_validate(profile)
