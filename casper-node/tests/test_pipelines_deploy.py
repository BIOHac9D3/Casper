from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipelines import deploy as deploy_module
from pipelines.deploy import run_deploy


@pytest.fixture
def fake_run(monkeypatch):
    calls: list[list[str]] = []

    def _ok(command, cwd=None, env=None):
        calls.append(list(command))
        return {"status": "ok", "code": 0, "stdout": "", "stderr": ""}

    runner = MagicMock(side_effect=_ok)
    monkeypatch.setattr(deploy_module, "run_command", runner)
    runner.calls = calls
    return runner


def test_runs_three_git_steps(fake_run) -> None:
    result = run_deploy("staging", {}, commit_message="hello")

    assert result["status"] == "ok"
    assert fake_run.calls[0] == ["git", "add", "."]
    assert fake_run.calls[1] == ["git", "commit", "-m", "hello"]
    assert fake_run.calls[2] == ["git", "push", "origin", "main"]


def test_default_commit_message_includes_target(fake_run) -> None:
    run_deploy("production", {})
    commit_step = fake_run.calls[1]
    assert commit_step[0:3] == ["git", "commit", "-m"]
    assert commit_step[3].startswith("deploy(production):")


def test_short_circuits_on_failure(monkeypatch) -> None:
    sequence = [
        {"status": "ok", "code": 0, "stdout": "", "stderr": ""},
        {"status": "error", "code": 1, "stdout": "", "stderr": "nothing to commit"},
        {"status": "ok", "code": 0, "stdout": "", "stderr": ""},
    ]
    runner = MagicMock(side_effect=sequence)
    monkeypatch.setattr(deploy_module, "run_command", runner)

    result = run_deploy("staging", {}, commit_message="msg")

    assert result["status"] == "error"
    assert result["message"] == "Deployment pipeline failed"


def test_branch_override_used_in_push(fake_run) -> None:
    run_deploy("prod", {"branch": "release"}, commit_message="m")
    push_step = fake_run.calls[2]
    assert push_step == ["git", "push", "origin", "release"]


def test_default_branch_is_main_when_unset(fake_run) -> None:
    run_deploy("prod", {}, commit_message="m")
    assert fake_run.calls[2] == ["git", "push", "origin", "main"]


def test_dry_run_does_not_invoke_runner(monkeypatch) -> None:
    runner = MagicMock()
    monkeypatch.setattr(deploy_module, "run_command", runner)

    result = run_deploy("staging", {"branch": "develop"}, commit_message="m", dry_run=True)

    runner.assert_not_called()
    assert result["status"] == "ok"
    assert result["message"] == "Deployment dry-run"
    assert all(step["status"] == "dry-run" for step in result["steps"])
    assert result["steps"][2]["command"] == ["git", "push", "origin", "develop"]
