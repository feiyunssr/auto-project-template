from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ServiceError(Exception):
    code: str
    message: str
    status_code: int = 400
    field_errors: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


class AuthRequiredError(ServiceError):
    def __init__(self, message: str = "Hub session is required.") -> None:
        super().__init__(code="AUTH_REQUIRED", message=message, status_code=401)


class ValidationFailedError(ServiceError):
    def __init__(self, message: str, field_errors: dict[str, str]) -> None:
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            field_errors=field_errors,
        )


class ProviderTimeoutError(ServiceError):
    def __init__(self, message: str, retryable: bool = True) -> None:
        super().__init__(
            code="PROVIDER_TIMEOUT",
            message=message,
            status_code=504,
            extra={"retryable": retryable},
        )


class ProviderRateLimitError(ServiceError):
    def __init__(self, message: str = "Provider rate limited the request.") -> None:
        super().__init__(code="PROVIDER_RATE_LIMIT", message=message, status_code=429)
