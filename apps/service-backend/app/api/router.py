from fastapi import APIRouter

from app.api.routes.settings import router as settings_router
from app.api.routes.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(tasks_router)
api_router.include_router(settings_router)
