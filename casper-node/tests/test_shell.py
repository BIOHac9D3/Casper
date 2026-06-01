from __future__ import annotations

from unittest.mock import MagicMock


from core import shell
from core.shell import run_command


def test_empty_command_returns_error() -> None:
    result = run_command([])
    assert result["status"] == "error"
    assert result["code"] == -1
    assert "Empty command" in result["stderr"]


def test_blocked_executable() -> None:
    result = run_command(["evilbin", "--bad"])
    assert result["status"] == "error"
    assert result["stderr"] == "Blocked command: evilbin"


def test_allowed_executable_invokes_subprocess(monkeypatch) -> None:
    completed = MagicMock(returncode=0, stdout="hello", stderr="")
    fake_run = MagicMock(return_value=completed)
    monkeypatch.setattr(shell.subprocess, "run", fake_run)

    result = run_command(["git", "status"])

    assert result == {"status": "ok", "code": 0, "stdout": "hello", "stderr": ""}
    fake_run.assert_called_once()
    args, kwargs = fake_run.call_args
    assert args[0] == ["git", "status"]
    assert kwargs["capture_output"] is True


def test_executable_path_extraction(monkeypatch) -> None:
    completed = MagicMock(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(shell.subprocess, "run", MagicMock(return_value=completed))

    for command in (["/usr/bin/git", "log"], ["./bin/git", "log"], ["git"]):
        result = run_command(command)
        assert result["status"] == "ok", command


def test_extra_allowed_extends_allowlist(monkeypatch) -> None:
    completed = MagicMock(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(shell.subprocess, "run", MagicMock(return_value=completed))

    blocked = run_command(["customtool", "--go"])
    assert blocked["status"] == "error"

    allowed = run_command(["customtool", "--go"], extra_allowed={"customtool"})
    assert allowed["status"] == "ok"


def test_nonzero_returncode_marks_error(monkeypatch) -> None:
    completed = MagicMock(returncode=2, stdout="", stderr="bad")
    monkeypatch.setattr(shell.subprocess, "run", MagicMock(return_value=completed))

    result = run_command(["git", "status"])
    assert result["status"] == "error"
    assert result["code"] == 2
