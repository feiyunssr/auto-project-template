from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthCheckItem(BaseModel):
    status: str
    detail: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    instance_id: str
    uptime_sec: int
    checks: dict[str, HealthCheckItem]
    metrics: dict[str, int]
    timestamp: datetime
    registration: dict[str, Any]
