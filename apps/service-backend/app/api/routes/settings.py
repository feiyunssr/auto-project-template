import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_auth_context, get_db_session, get_runtime
from app.core.config import get_settings
from app.models import ServiceAiProfile
from app.repositories.ai_profiles import AiProfileRepository
from app.schemas.common import AuthContext
from app.schemas.settings import (
    AiProfileListResponse,
    AiProfileResponse,
    AiProfileUpsertRequest,
    AiRuntimeSettingsResponse,
    AiScenarioRuntimeResponse,
    HubRuntimeStatusResponse,
    ProviderOptionResponse,
)
from app.services.provider_registry import list_supported_provider_names

router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger(__name__)


def _derive_hub_mode(
    hub_enabled: bool,
    registration_snapshot: dict[str, object],
    telemetry_snapshot: dict[str, object],
) -> str:
    if not hub_enabled:
        return "local_fallback"

    registration_status = str(registration_snapshot.get("status", "degraded"))
    telemetry_status = str(telemetry_snapshot.get("status", "degraded"))
    if registration_status == "healthy" and telemetry_status == "healthy":
        return "connected"
    if registration_status in {"pending", "healthy"} and telemetry_status == "pending":
        return "bootstrap_pending"
    if registration_status == "pending":
        return "bootstrap_pending"
    return "degraded"


@router.get("/runtime", response_model=AiRuntimeSettingsResponse)
async def get_ai_runtime_settings(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    runtime=Depends(get_runtime),
) -> AiRuntimeSettingsResponse:
    settings = get_settings()
    repo = AiProfileRepository(session)
    registration_snapshot = runtime.registration.snapshot()
    telemetry_snapshot = runtime.hub_telemetry.snapshot()
    hub_api_url = runtime.hub_telemetry.hub_api_url
    hub_api_v1_prefix = runtime.hub_telemetry.hub_api_v1_prefix
    profiles = list(await repo.list_profiles(include_inactive=True))
    scenario_keys = list(dict.fromkeys(profile.scenario_key for profile in profiles)) or ["general"]
    scenarios: list[AiScenarioRuntimeResponse] = []

    for scenario_key in scenario_keys:
        scenario_profiles = [profile for profile in profiles if profile.scenario_key == scenario_key]
        active_profiles = [profile for profile in scenario_profiles if profile.is_active]
        default_profile = next((profile for profile in active_profiles if profile.is_default), None)
        effective_profile = default_profile or (active_profiles[0] if active_profiles else None)
        resolution_source = None
        if default_profile is not None:
            resolution_source = "scenario_default"
        elif effective_profile is not None:
            resolution_source = "first_active_profile"

        scenarios.append(
            AiScenarioRuntimeResponse(
                scenario_key=scenario_key,
                scenario_label=scenario_key.replace("_", " ").title(),
                configured_profile_key=default_profile.profile_key if default_profile else None,
                effective_profile_key=effective_profile.profile_key if effective_profile else None,
                effective_profile_name=effective_profile.profile_name if effective_profile else None,
                effective_provider_name=effective_profile.provider_name if effective_profile else None,
                resolution_source=resolution_source,
                active_profile_count=len(active_profiles),
                total_profile_count=len(scenario_profiles),
            )
        )

    return AiRuntimeSettingsResponse(
        provider_mode=settings.provider_mode,
        default_provider_name=settings.default_provider_name,
        supported_providers=[
            ProviderOptionResponse(
                provider_name=provider_name,
                provider_label=provider_name.upper(),
                supported_scenarios=scenario_keys,
            )
            for provider_name in list_supported_provider_names()
        ],
        require_hub_auth=settings.require_hub_auth,
        hub_enabled=runtime.hub_telemetry.hub_enabled,
        hub_mode=_derive_hub_mode(runtime.hub_telemetry.hub_enabled, registration_snapshot, telemetry_snapshot),
        hub_api_url=hub_api_url,
        hub_api_v1_prefix=hub_api_v1_prefix,
        service_public_base_url=settings.service_public_base_url,
        hub_registration=HubRuntimeStatusResponse(
            status=str(registration_snapshot.get("status", "degraded")),
            registration_id=registration_snapshot.get("registration_id"),
            lease_ttl_sec=registration_snapshot.get("lease_ttl_sec"),
            last_error=registration_snapshot.get("last_error"),
            last_heartbeat_at=registration_snapshot.get("last_heartbeat_at"),
        ),
        hub_telemetry=HubRuntimeStatusResponse(
            status=str(telemetry_snapshot.get("status", "degraded")),
            service_id=telemetry_snapshot.get("service_id"),
            last_error=telemetry_snapshot.get("last_error"),
            last_heartbeat_at=telemetry_snapshot.get("last_heartbeat_at"),
            last_event_at=telemetry_snapshot.get("last_event_at"),
        ),
        scenarios=scenarios,
    )


@router.get("/ai-profiles", response_model=AiProfileListResponse)
async def list_ai_profiles(
    scenario_key: str | None = None,
    include_inactive: bool = False,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> AiProfileListResponse:
    profiles = await AiProfileRepository(session).list_profiles(
        scenario_key=scenario_key,
        include_inactive=include_inactive,
    )
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
