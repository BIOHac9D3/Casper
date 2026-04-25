from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

import cli as cli_module
from cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def chdir_to_repo(monkeypatch) -> None:
    """Run CLI commands from the repo root so configs/targets.yaml resolves."""
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)


def test_version_option_prints_and_exits(runner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "casper-node" in result.stdout
    assert "0.1.0" in result.stdout


def test_list_targets_lists_configured_targets(runner, chdir_to_repo) -> None:
    result = runner.invoke(app, ["list-targets"])
    assert result.exit_code == 0
    assert "local" in result.stdout
    assert "staging" in result.stdout
    assert "production" in result.stdout


def test_deploy_dry_run_does_not_run_git(runner, chdir_to_repo, monkeypatch) -> None:
    runner_mock = MagicMock()
    monkeypatch.setattr("pipelines.deploy.run_command", runner_mock)

    result = runner.invoke(app, ["deploy", "local", "--dry-run", "-m", "preview"])

    assert result.exit_code == 0, result.stdout
    runner_mock.assert_not_called()
    assert "dry-run" in result.stdout.lower()


def test_build_dry_run_does_not_run_commands(runner, chdir_to_repo, monkeypatch) -> None:
    runner_mock = MagicMock()
    monkeypatch.setattr("pipelines.build.run_command", runner_mock)

    result = runner.invoke(app, ["build", "local", "--dry-run"])

    assert result.exit_code == 0, result.stdout
    runner_mock.assert_not_called()


def test_raise_if_error_includes_context() -> None:
    err = {"status": "error", "message": "boom"}
    with pytest.raises(RuntimeError) as exc:
        cli_module._raise_if_error(err, context="build (staging)")
    assert "build (staging)" in str(exc.value)
    assert "boom" in str(exc.value)


def test_raise_if_error_handles_missing_message() -> None:
    err = {"status": "error"}
    with pytest.raises(RuntimeError) as exc:
        cli_module._raise_if_error(err, context="ctx")
    assert "ctx" in str(exc.value)


def test_raise_if_error_passes_when_ok() -> None:
    cli_module._raise_if_error({"status": "ok"}, context="anything")


def test_unknown_provider_raises_bad_parameter(runner, chdir_to_repo) -> None:
    result = runner.invoke(app, ["generate", "--provider", "bogus", "x"])
    assert result.exit_code != 0
    combined = (result.stdout or "") + (getattr(result, "stderr", "") or "") + str(result.exception or "")
    assert "Provider must be one of" in combined
