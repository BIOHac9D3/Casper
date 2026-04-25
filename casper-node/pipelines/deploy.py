from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from core.shell import run_command


class PipelineResult(TypedDict, total=False):
    status: str
    message: str
    target: str
    steps: List[Dict[str, Any]]


def _planned(command: List[str]) -> Dict[str, Any]:
    return {
        "status": "dry-run",
        "code": 0,
        "stdout": f"$ {' '.join(command)}",
        "stderr": "",
        "command": command,
    }


def run_deploy(
    target_name: str,
    target_config: Dict[str, Any],
    commit_message: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    branch = str(target_config.get("branch", "main"))
    message = commit_message or f"deploy({target_name}): {datetime.now(timezone.utc).isoformat()}"

    commands: List[List[str]] = [
        ["git", "add", "."],
        ["git", "commit", "-m", message],
        ["git", "push", "origin", branch],
    ]

    if dry_run:
        return {
            "status": "ok",
            "message": "Deployment dry-run",
            "target": target_name,
            "steps": [_planned(cmd) for cmd in commands],
        }

    steps = [run_command(cmd) for cmd in commands]
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
