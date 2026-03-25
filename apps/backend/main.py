from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import apps.backend.models  # noqa: F401
from apps.backend.api.routes.ops import router as ops_router
from apps.backend.api.routes.settings import router as settings_router
from apps.backend.api.routes.tasks import router as tasks_router
from apps.backend.core.config import Settings, get_settings
from apps.backend.core.errors import ServiceError
from apps.backend.core.logging import configure_logging
from apps.backend.db import SessionFactory, init_database
from apps.backend.models import ServiceAiProfile
from apps.backend.repositories.ai_profiles import AiProfileRepository
from apps.backend.schemas.common import ApiErrorResponse
from apps.backend.services.registration import HubRegistrationService
from apps.backend.workers.job_worker import JobWorker

configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)


@dataclass
class AppRuntime:
    settings: Settings
    started_at: datetime
    instance_id: str
    session_factory: type(SessionFactory)
    worker: JobWorker
    registration: HubRegistrationService


async def ensure_default_profile(settings: Settings) -> None:
    async with SessionFactory() as session:
        repo = AiProfileRepository(session)
        existing = await repo.get_by_key("default-general")
        if existing is None:
            profile = ServiceAiProfile(
                profile_key="default-general",
                profile_name="Default General Profile",
                scenario_key="general",
                is_default=True,
                provider_name=settings.default_provider_name,
                model_name="mock-001",
                system_prompt="You are the default provider profile.",
                prompt_template="{{ input_payload }}",
                temperature=0.2,
                max_tokens=1024,
                timeout_ms=settings.default_timeout_ms,
                max_retries=settings.default_max_retries,
                concurrency_limit=settings.default_concurrency_limit,
                created_by_hub_user_id="system",
                updated_by_hub_user_id="system",
            )
            await repo.save_profile(profile)
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_database()
    await ensure_default_profile(settings)
    instance_id = str(uuid.uuid4())
    runtime = AppRuntime(
        settings=settings,
        started_at=datetime.now(timezone.utc),
        instance_id=instance_id,
        session_factory=SessionFactory,
        worker=JobWorker(SessionFactory, concurrency_limit=settings.default_concurrency_limit),
        registration=HubRegistrationService(settings, instance_id=instance_id),
    )
    app.state.runtime = runtime
    logger.info(
        "service_starting instance_id=%s version=%s environment=%s",
        instance_id,
        settings.app_version,
        settings.environment,
    )
    await runtime.worker.start()
    await runtime.registration.start()
    try:
        yield
    finally:
        await runtime.registration.stop()
        await runtime.worker.stop()
        logger.info("service_stopped instance_id=%s", instance_id)


app = FastAPI(title="AI Auto Hub Service Template", version=get_settings().app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allowed_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(tasks_router)
app.include_router(settings_router)
app.include_router(ops_router)


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    log = logger.warning if exc.status_code >= 500 else logger.info
    log("service_error code=%s status=%s message=%s", exc.code, exc.status_code, exc.message)
    payload = ApiErrorResponse(
        code=exc.code,
        message=exc.message,
        field_errors=exc.field_errors,
        details=exc.extra,
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors = {}
    for error in exc.errors():
        loc = [str(item) for item in error["loc"] if item != "body"]
        field_errors[".".join(loc)] = error["msg"]
    logger.info("request_validation_failed field_errors=%s", field_errors)
    payload = ApiErrorResponse(
        code="VALIDATION_ERROR",
        message="Task payload validation failed.",
        field_errors=field_errors,
        details={},
    )
    return JSONResponse(status_code=422, content=payload.model_dump())
