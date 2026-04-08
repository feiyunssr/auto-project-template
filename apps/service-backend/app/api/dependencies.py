from __future__ import annotations

import base64

from hmac import compare_digest

from fastapi import Header, Request

from app.core.config import get_settings
from app.core.errors import AuthRequiredError, ServiceApiAuthError, ServiceApiDisabledError
from app.db import get_db_session
from app.schemas.common import AuthContext
from app.schemas.service_api import ServiceApiAuthContext


async def get_auth_context(
    x_hub_user_id: str | None = Header(default=None),
    x_hub_user_name: str | None = Header(default=None),
    x_hub_user_name_b64: str | None = Header(default=None),
    x_hub_role: str | None = Header(default=None),
) -> AuthContext:
    settings = get_settings()
    decoded_hub_user_name = _decode_hub_user_name(x_hub_user_name_b64, fallback=x_hub_user_name)
    if not settings.require_hub_auth:
        return AuthContext(
            hub_user_id=x_hub_user_id or settings.dev_hub_user_id,
            hub_user_name=decoded_hub_user_name or settings.dev_hub_user_name,
            role=x_hub_role or settings.dev_hub_role,
        )
    if not x_hub_user_id:
        raise AuthRequiredError("Hub session missing or expired.")
    return AuthContext(
        hub_user_id=x_hub_user_id,
        hub_user_name=decoded_hub_user_name,
        role=x_hub_role,
    )


async def get_service_api_auth_context(
    authorization: str | None = Header(default=None),
) -> ServiceApiAuthContext:
    settings = get_settings()
    if not settings.enable_service_api or not settings.service_api_bearer_token:
        raise ServiceApiDisabledError()
    if authorization is None:
        raise ServiceApiAuthError("Service API bearer token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ServiceApiAuthError("Authorization header must use Bearer token.")
    if not compare_digest(token, settings.service_api_bearer_token):
        raise ServiceApiAuthError()
    return ServiceApiAuthContext(
        submitter_id=settings.service_api_submitter_id,
        submitter_name=settings.service_api_submitter_name,
        source_channel=settings.service_api_source_channel,
    )


def get_runtime(request: Request):
    return request.app.state.runtime


def _decode_hub_user_name(
    encoded_value: str | None,
    *,
    fallback: str | None,
) -> str | None:
    if not encoded_value:
        return fallback
    try:
        payload = base64.b64decode(encoded_value.encode("ascii"), validate=True)
        return payload.decode("utf-8")
    except Exception:
        return fallback


__all__ = ["get_auth_context", "get_db_session", "get_runtime", "get_service_api_auth_context"]
