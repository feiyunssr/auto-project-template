from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiErrorResponse(BaseModel):
    code: str
    message: str
    field_errors: dict[str, str] = {}
    details: dict[str, Any] = {}


class AuthContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hub_user_id: str
    hub_user_name: str | None = None
    role: str | None = None
