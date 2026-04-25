from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, TypedDict

from core.shell import run_command

KNOWN_TARGET_TYPES = {"python", "node", "docker"}


class PipelineResult(TypedDict, total=False):
    status: str
    message: str
    target: str
    steps: List[Dict[str, Any]]


def _planned(command: List[str], cwd: str) -> Dict[str, Any]:
    return {
        "status": "dry-run",
        "code": 0,
        "stdout": f"(cd {cwd} && {' '.join(command)})",
        "stderr": "",
        "command": command,
        "cwd": cwd,
    }


def _commands_for(target_type: str, target_name: str) -> List[List[str]]:
    if target_type == "node":
        return [["npm", "install"], ["npm", "run", "build"]]
    if target_type == "docker":
        return [["docker", "build", "-t", f"{target_name}:latest", "."]]
    return [
        ["python", "-m", "pip", "install", "-r", "requirements.txt"],
        ["python", "-m", "pytest", "-q"],
    ]


def run_build(
    target_name: str,
    target_config: Dict[str, Any],
    dry_run: bool = False,
) -> Dict[str, Any]:
    target_type = str(target_config.get("type", "python")).lower()
    path = str(target_config.get("path", "."))
    project_path = Path(path)

    if not project_path.exists():
        return {"status": "error", "message": f"Target path does not exist: {path}"}

    if target_type not in KNOWN_TARGET_TYPES:
        return {
            "status": "error",
            "message": f"Unknown target type: {target_type}",
            "target": target_name,
        }

    commands = _commands_for(target_type, target_name)

    if dry_run:
        return {
            "status": "ok",
            "message": "Build dry-run",
            "target": target_name,
            "steps": [_planned(cmd, path) for cmd in commands],
        }

    steps = [run_command(cmd, cwd=path) for cmd in commands]
    failed = next((s for s in steps if s["status"] != "ok"), None)
    if failed:
        return {
            "status": "error",
            "message": "Build failed",
            "target": target_name,
            "steps": steps,
        }

    return {
        "status": "ok",
        "message": "Build succeeded",
        "target": target_name,
        "steps": steps,
    }
