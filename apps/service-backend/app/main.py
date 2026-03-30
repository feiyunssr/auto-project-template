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

import app.models  # noqa: F401
from app.api.router import api_router
from app.api.routes.ops import router as ops_router
from app.core.config import Settings, get_settings
from app.core.errors import ServiceError
from app.core.logging import configure_logging
from app.db import SessionFactory, init_database
from app.models import ServiceAiProfile
from app.repositories.ai_profiles import AiProfileRepository
from app.schemas.common import ApiErrorResponse
from app.services.hub_telemetry import HubTelemetryService
from app.services.registration import HubRegistrationService
from app.workers.job_worker import JobWorker
from app.workers.monitor import WorkerMonitor

configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)


@dataclass
class AppRuntime:
    settings: Settings
    started_at: datetime
    instance_id: str
    session_factory: type(SessionFactory)
    worker: object
    registration: HubRegistrationService
    hub_telemetry: HubTelemetryService


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
    hub_telemetry = HubTelemetryService(settings, instance_id=instance_id)
    worker = (
        JobWorker(
            SessionFactory,
            poll_interval_ms=settings.worker_poll_interval_ms,
            max_jobs_per_cycle=settings.worker_max_jobs_per_cycle,
            heartbeat_path=settings.worker_heartbeat_path,
            hub_telemetry=hub_telemetry,
        )
        if settings.run_embedded_worker
        else WorkerMonitor(
            heartbeat_path=settings.worker_heartbeat_path,
            timeout_sec=settings.worker_heartbeat_timeout_sec,
        )
    )
    runtime = AppRuntime(
        settings=settings,
        started_at=datetime.now(timezone.utc),
        instance_id=instance_id,
        session_factory=SessionFactory,
        worker=worker,
        registration=HubRegistrationService(
            settings,
            instance_id=instance_id,
            hub_telemetry=hub_telemetry,
        ),
        hub_telemetry=hub_telemetry,
    )
    app.state.runtime = runtime
    logger.info(
        "service_starting instance_id=%s version=%s environment=%s",
        instance_id,
        settings.app_version,
        settings.environment,
    )
    await runtime.registration.start()
    await runtime.hub_telemetry.start()
    if isinstance(runtime.worker, JobWorker):
        await runtime.worker.start()
    try:
        yield
    finally:
        await runtime.registration.stop()
        await runtime.hub_telemetry.stop()
        if isinstance(runtime.worker, JobWorker):
            await runtime.worker.stop()
        logger.info("service_stopped instance_id=%s", instance_id)

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origin_list,
        allow_origin_regex=settings.cors_allowed_origin_regex,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.include_router(ops_router)
    return app


app = create_app()


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
