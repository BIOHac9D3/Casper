from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipelines import build as build_module
from pipelines.build import run_build


@pytest.fixture
def fake_run(monkeypatch):
    calls: list[list[str]] = []

    def _ok(command, cwd=None, env=None):
        calls.append(list(command))
        return {"status": "ok", "code": 0, "stdout": "", "stderr": ""}

    runner = MagicMock(side_effect=_ok)
    monkeypatch.setattr(build_module, "run_command", runner)
    runner.calls = calls
    return runner


def test_python_target(tmp_path, fake_run) -> None:
    result = run_build("local", {"type": "python", "path": str(tmp_path)})

    assert result["status"] == "ok"
    assert fake_run.calls[0][0:3] == ["python", "-m", "pip"]
    assert fake_run.calls[1][0:3] == ["python", "-m", "pytest"]


def test_node_target(tmp_path, fake_run) -> None:
    result = run_build("staging", {"type": "node", "path": str(tmp_path)})

    assert result["status"] == "ok"
    assert fake_run.calls[0] == ["npm", "install"]
    assert fake_run.calls[1] == ["npm", "run", "build"]


def test_docker_target(tmp_path, fake_run) -> None:
    result = run_build("production", {"type": "docker", "path": str(tmp_path)})

    assert result["status"] == "ok"
    assert fake_run.calls[0][:3] == ["docker", "build", "-t"]
    assert "production:latest" in fake_run.calls[0]


def test_missing_path_returns_error() -> None:
    result = run_build("ghost", {"type": "python", "path": "/nonexistent/path/xyz"})
    assert result["status"] == "error"
    assert "does not exist" in result["message"]


def test_short_circuits_on_first_failure(tmp_path, monkeypatch) -> None:
    sequence = [
        {"status": "ok", "code": 0, "stdout": "", "stderr": ""},
        {"status": "error", "code": 1, "stdout": "", "stderr": "fail"},
    ]
    runner = MagicMock(side_effect=sequence)
    monkeypatch.setattr(build_module, "run_command", runner)

    result = run_build("local", {"type": "python", "path": str(tmp_path)})

    assert result["status"] == "error"
    assert result["message"] == "Build failed"
    assert len(result["steps"]) == 2


def test_unknown_target_type_returns_error(tmp_path) -> None:
    result = run_build("oddball", {"type": "lua", "path": str(tmp_path)})
    assert result["status"] == "error"
    assert "Unknown target type" in result["message"]


def test_dry_run_does_not_invoke_runner(tmp_path, monkeypatch) -> None:
    runner = MagicMock()
    monkeypatch.setattr(build_module, "run_command", runner)

    result = run_build("local", {"type": "node", "path": str(tmp_path)}, dry_run=True)

    runner.assert_not_called()
    assert result["status"] == "ok"
    assert result["message"] == "Build dry-run"
    assert all(step["status"] == "dry-run" for step in result["steps"])
    assert result["steps"][0]["command"] == ["npm", "install"]
