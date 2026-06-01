from __future__ import annotations

import subprocess
from pathlib import PurePath
from typing import List, Mapping, Optional, Set


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


def _executable_name(arg: str) -> str:
    """Extract a bare executable name from a path-like argument.

    Accepts forms like 'git', '/usr/bin/git', './bin/git', or
    'C:\\\\tools\\\\git.exe'. Returns the trailing component without
    directories, ignoring trailing slashes.
    """
    return PurePath(arg).name or arg


def run_command(
    command: List[str],
    cwd: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    extra_allowed: Optional[Set[str]] = None,
) -> dict:
    if not command:
        return {"status": "error", "code": -1, "stdout": "", "stderr": "Empty command"}

    executable = _executable_name(command[0])
    allowed = ALLOWED if extra_allowed is None else ALLOWED | set(extra_allowed)
    if executable not in allowed:
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
