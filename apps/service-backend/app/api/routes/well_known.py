from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_runtime
from app.core.config import get_settings
from app.schemas.auto_onboarding import (
    AutoOnboardingBootstrapRequest,
    AutoOnboardingBootstrapResponse,
    AutoOnboardingManifestResponse,
)

router = APIRouter(tags=["well-known"])


@router.get(
    "/.well-known/ai-auto-manifest.json",
    response_model=AutoOnboardingManifestResponse,
)
async def get_auto_onboarding_manifest() -> AutoOnboardingManifestResponse:
    settings = get_settings()
    base_url = settings.service_public_base_url.rstrip("/")
    return AutoOnboardingManifestResponse(
        service_key=settings.service_key,
        display_name=settings.service_display_name,
        description=settings.service_description,
        category=settings.service_team,
        owner_name=settings.service_team,
        service_type="web_application",
        entry_url=base_url,
        base_url=base_url,
        healthcheck_url=f"{base_url}/healthz",
        bootstrap_url=f"{base_url}/.well-known/ai-auto-bootstrap",
        capability_tags=[
            item.strip() for item in settings.service_capabilities.split(",") if item.strip()
        ],
        permission_tags=["hub_session"],
    )


@router.post(
    "/.well-known/ai-auto-bootstrap",
    response_model=AutoOnboardingBootstrapResponse,
)
async def bootstrap_auto_onboarding(
    payload: AutoOnboardingBootstrapRequest,
    runtime=Depends(get_runtime),
) -> AutoOnboardingBootstrapResponse:
    runtime.hub_telemetry.configure_credentials(
        payload.service_id,
        payload.service_token,
        hub_api_url=payload.hub_api_url,
        hub_api_v1_prefix=payload.hub_api_v1_prefix,
        service_key=payload.service_key,
    )
    runtime.registration.refresh_bootstrap_state()
    return AutoOnboardingBootstrapResponse(
        status="ok",
        service_id=payload.service_id,
        hub_api_url=payload.hub_api_url,
        hub_api_v1_prefix=payload.hub_api_v1_prefix,
    )
