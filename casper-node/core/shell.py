from __future__ import annotations

import subprocess
from typing import List, Mapping


ALLOWED = {
    "python",
    "python3",
    "pip",
    "npm",
    "yarn",
    "pnpm",
    "docker",
    "git",
    "pytest",
}


def run_command(command: List[str], cwd: str | None = None, env: Mapping[str, str] | None = None) -> dict:
    if not command:
        return {"status": "error", "code": -1, "stdout": "", "stderr": "Empty command"}

    executable = command[0].split("/")[-1]
    if executable not in ALLOWED:
        return {
            "status": "error",
            "code": -1,
            "stdout": "",
            "stderr": f"Blocked command: {executable}",
        }

    proc = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=False)
    return {
        "status": "ok" if proc.returncode == 0 else "error",
        "code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
