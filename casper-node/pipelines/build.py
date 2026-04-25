from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from core.shell import run_command



def run_build(target_name: str, target_config: Dict[str, Any]) -> Dict[str, Any]:
    target_type = str(target_config.get("type", "python")).lower()
    path = str(target_config.get("path", "."))
    project_path = Path(path)

    if not project_path.exists():
        return {"status": "error", "message": f"Target path does not exist: {path}"}

    steps: list[dict] = []

    if target_type == "node":
        steps.append(run_command(["npm", "install"], cwd=path))
        steps.append(run_command(["npm", "run", "build"], cwd=path))
    elif target_type == "docker":
        steps.append(run_command(["docker", "build", "-t", f"{target_name}:latest", "."], cwd=path))
    else:
        steps.append(run_command(["python", "-m", "pip", "install", "-r", "requirements.txt"], cwd=path))
        steps.append(run_command(["python", "-m", "pytest", "-q"], cwd=path))

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
