from __future__ import annotations

from fastapi import Header, Request

from apps.backend.core.config import get_settings
from apps.backend.core.errors import AuthRequiredError
from apps.backend.db import get_db_session
from apps.backend.schemas.common import AuthContext


async def get_auth_context(
    x_hub_user_id: str | None = Header(default=None),
    x_hub_user_name: str | None = Header(default=None),
    x_hub_role: str | None = Header(default=None),
) -> AuthContext:
    settings = get_settings()
    if not settings.require_hub_auth:
        return AuthContext(
            hub_user_id=x_hub_user_id or settings.dev_hub_user_id,
            hub_user_name=x_hub_user_name or settings.dev_hub_user_name,
            role=x_hub_role or settings.dev_hub_role,
        )
    if not x_hub_user_id:
        raise AuthRequiredError("Hub session missing or expired.")
    return AuthContext(
        hub_user_id=x_hub_user_id,
        hub_user_name=x_hub_user_name,
        role=x_hub_role,
    )


def get_runtime(request: Request):
    return request.app.state.runtime


__all__ = ["get_auth_context", "get_db_session", "get_runtime"]
