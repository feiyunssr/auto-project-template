from fastapi import APIRouter, Depends, Response

from apps.backend.api.dependencies import get_runtime
from apps.backend.schemas.ops import HealthResponse
from apps.backend.services.health import build_health_response

router = APIRouter(tags=["ops"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz(response: Response, runtime=Depends(get_runtime)) -> HealthResponse:
    status_code, payload = await build_health_response(
        settings=runtime.settings,
        session_factory=runtime.session_factory,
        worker=runtime.worker,
        registration_snapshot=runtime.registration.snapshot(),
        instance_id=runtime.instance_id,
        started_at=runtime.started_at,
    )
    response.status_code = status_code
    return payload
