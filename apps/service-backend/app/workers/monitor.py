from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


class WorkerMonitor:
    def __init__(self, heartbeat_path: str, timeout_sec: int) -> None:
        self.heartbeat_path = Path(heartbeat_path)
        self.timeout_sec = timeout_sec

    def snapshot(self) -> dict[str, int | str]:
        if not self.heartbeat_path.exists():
            return {
                "status": "stopped",
                "active_jobs": 0,
                "processed_jobs": 0,
                "last_heartbeat_at": "",
            }

        try:
            payload = json.loads(self.heartbeat_path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "status": "stopped",
                "active_jobs": 0,
                "processed_jobs": 0,
                "last_heartbeat_at": "",
            }

        heartbeat_raw = payload.get("last_heartbeat_at") or ""
        if not heartbeat_raw:
            payload["status"] = "stopped"
            return payload

        heartbeat_at = datetime.fromisoformat(heartbeat_raw)
        if datetime.now(timezone.utc) - heartbeat_at > timedelta(seconds=self.timeout_sec):
            payload["status"] = "stopped"
        else:
            payload["status"] = "running"
        return payload
