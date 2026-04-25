from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.shell import run_command



def run_deploy(target_name: str, target_config: Dict[str, Any], commit_message: Optional[str] = None) -> Dict[str, Any]:
    _ = target_config
    message = commit_message or f"deploy({target_name}): {datetime.now(timezone.utc).isoformat()}"

    steps = [
        run_command(["git", "add", "."]),
        run_command(["git", "commit", "-m", message]),
        run_command(["git", "push", "origin", "main"]),
    ]

    for step in steps:
        if step["status"] != "ok":
            return {
                "status": "error",
                "message": "Deployment pipeline failed",
                "target": target_name,
                "steps": steps,
            }

    return {
        "status": "ok",
        "message": "Deployment pipeline executed",
        "target": target_name,
        "steps": steps,
    }
