from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class HubBootstrapCredentials:
    service_id: str
    service_token: str
    hub_api_url: str | None = None
    hub_api_v1_prefix: str = "/api/v1"
    service_key: str | None = None


def load_hub_bootstrap_credentials(path: str | Path) -> HubBootstrapCredentials | None:
    payload = _read_json_payload(Path(path))
    if payload is None:
        return None

    service_id = _normalize_string(payload.get("service_id"))
    service_token = _normalize_string(payload.get("service_token"))
    if service_id is None or service_token is None:
        return None

    return HubBootstrapCredentials(
        service_id=service_id,
        service_token=service_token,
        hub_api_url=_normalize_string(payload.get("hub_api_url")),
        hub_api_v1_prefix=_normalize_prefix(payload.get("hub_api_v1_prefix")),
        service_key=_normalize_string(payload.get("service_key")),
    )


def write_hub_bootstrap_credentials(
    path: str | Path,
    payload: HubBootstrapCredentials,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "service_id": payload.service_id,
                "service_token": payload.service_token,
                "hub_api_url": payload.hub_api_url,
                "hub_api_v1_prefix": _normalize_prefix(payload.hub_api_v1_prefix),
                "service_key": payload.service_key,
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )


def _read_json_payload(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return raw if isinstance(raw, dict) else None


def _normalize_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_prefix(value: Any) -> str:
    normalized = _normalize_string(value)
    if normalized is None:
        return "/api/v1"
    return normalized if normalized.startswith("/") else f"/{normalized}"
