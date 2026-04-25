from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class MemoryStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.logs_dir = self.base_dir / "logs"
        self.sessions_dir = self.base_dir / "sessions"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "payload": payload,
        }
        file_path = self.logs_dir / f"{ts}.log"
        with file_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
        return file_path
