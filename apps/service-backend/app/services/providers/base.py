from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.models import ServiceAiProfile, ServiceJob


@dataclass(slots=True)
class PreparedRequest:
    payload: dict[str, Any]
    masked_payload: dict[str, Any]


@dataclass(slots=True)
class ProviderInvokeResult:
    external_request_id: str
    payload: dict[str, Any]
    latency_ms: int
    input_tokens: int
    output_tokens: int


@dataclass(slots=True)
class NormalizedResult:
    result_type: str
    preview_text: str
    structured_payload: dict[str, Any]
    artifacts: list[dict[str, Any]]
    quality_status: str
    review_comment: str | None = None


class ProviderAdapter(Protocol):
    name: str

    async def prepare_request(
        self,
        job: ServiceJob,
        profile: ServiceAiProfile,
    ) -> PreparedRequest: ...

    async def invoke(
        self,
        prepared: PreparedRequest,
        profile: ServiceAiProfile,
        attempt_no: int,
    ) -> ProviderInvokeResult: ...

    async def normalize_response(
        self,
        job: ServiceJob,
        invoke_result: ProviderInvokeResult,
        profile: ServiceAiProfile,
    ) -> NormalizedResult: ...
