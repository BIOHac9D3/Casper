from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def _fallback_help() -> None:
    print("Casper Node CLI")
    print("\nDependencies are not installed. Install them with:")
    print("  python -m pip install -r requirements.txt")
    print("\nCommands:")
    print("  generate <prompt> [--provider openai|claude|local] [--model <model_id>]")
    print("  pull-model [--model <model_id>]")
    print("  build <target>")
    print("  deploy <target> [-m|--message <msg>]")


try:
    import typer
    from dotenv import load_dotenv
    from rich import print
    from rich.console import Console
    from rich.table import Table
except ModuleNotFoundError:
    if __name__ == "__main__":
        wants_help = any(arg in {"--help", "-h", "help"} for arg in sys.argv[1:])
        if wants_help:
            _fallback_help()
            raise SystemExit(0)
        print("Missing CLI dependencies. Run: python -m pip install -r requirements.txt")
        raise SystemExit(1)
    raise

from agents.base import BaseAgent
from agents.claude_agent import ClaudeAgent
from agents.local_agent import LocalAgent
from agents.openai_agent import OpenAIAgent
from core.config import load_targets
from core.memory import MemoryStore
from pipelines.build import run_build
from pipelines.deploy import run_deploy

__version__ = "0.1.0"

app = typer.Typer(help="Casper Node: mobile-first AI + CI/CD orchestrator")


def _version_callback(value: bool) -> None:
    if value:
        print(f"casper-node {__version__}")
        raise typer.Exit()

OPENAI_MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"]
CLAUDE_MODELS = ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022", "claude-3-7-sonnet-latest"]
LOCAL_MODELS = ["llama3.2:1b", "llama3.2:3b", "qwen2.5:3b", "mistral:7b"]

_PROVIDERS: dict[str, tuple[type[BaseAgent], list[str], str, int]] = {
    "openai": (OpenAIAgent, OPENAI_MODELS, "OPENAI_MODEL", 0),
    "claude": (ClaudeAgent, CLAUDE_MODELS, "ANTHROPIC_MODEL", 1),
    "local":  (LocalAgent,  LOCAL_MODELS,  "LOCAL_MODEL",   1),
}


def _bad_provider() -> typer.BadParameter:
    return typer.BadParameter("Provider must be one of: openai, claude, local")


def _raise_if_error(result: dict, *, context: str) -> None:
    if result.get("status") != "ok":
        raise RuntimeError(f"{context}: {result.get('message', 'unknown error')}")


@app.callback()
def init(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the casper-node version and exit.",
    ),
) -> None:
    load_dotenv()


def select_model(provider: str, requested_model: Optional[str]) -> str:
    entry = _PROVIDERS.get(provider)
    if entry is None:
        raise _bad_provider()
    _, choices, env_var, default_idx = entry
    default_model = os.getenv(env_var, choices[default_idx])

    if requested_model:
        return requested_model

    if sys.stdin.isatty():
        choice_text = ", ".join(choices)
        return typer.prompt(f"Choose {provider} model ({choice_text})", default=default_model)

    return default_model


@app.command()
def pull_model(
    model: Optional[str] = typer.Option(None, "--model", "-M", help="Local model to pull (Ollama)"),
) -> None:
    """Download/pull a local model from Ollama."""
    store = MemoryStore(Path("memory"))
    agent = LocalAgent()
    selected_model = select_model("local", model)
    result = agent.ensure_model(selected_model)
    store.log_event("pull_model", {"provider": "local", "model": selected_model, "status": result.get("status")})
    print(result)
    _raise_if_error(result, context=f"pull-model (local, {selected_model})")


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Prompt to send to an AI agent"),
    provider: str = typer.Option("openai", "--provider", "-p", help="openai, claude, or local"),
    model: Optional[str] = typer.Option(None, "--model", "-M", help="Explicit model id (skips prompt)"),
    auto_pull: bool = typer.Option(
        False,
        "--auto-pull",
        help="For local provider, auto-download model before generation",
    ),
) -> None:
    """Generate content from configured AI provider."""
    store = MemoryStore(Path("memory"))
    provider_name = provider.lower()

    entry = _PROVIDERS.get(provider_name)
    if entry is None:
        raise _bad_provider()
    agent_cls, *_ = entry
    agent = agent_cls()

    selected_model = select_model(provider_name, model)

    if provider_name == "local" and auto_pull and isinstance(agent, LocalAgent):
        pull_result = agent.ensure_model(selected_model)
        store.log_event(
            "pull_model",
            {"provider": provider_name, "model": selected_model, "status": pull_result.get("status")},
        )
        if pull_result["status"] != "ok":
            print(pull_result)
            _raise_if_error(pull_result, context=f"auto-pull (local, {selected_model})")

    result = agent.generate(prompt, model=selected_model)
    store.log_event(
        "generate",
        {
            "provider": provider_name,
            "model": selected_model,
            "status": result.get("status"),
        },
    )
    print(result)


@app.command()
def build(
    target: str = typer.Argument(..., help="Target name from configs/targets.yaml"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the steps that would run without executing them."),
) -> None:
    """Run build pipeline for a target."""
    targets = load_targets(Path("configs/targets.yaml"))
    if target not in targets:
        raise typer.BadParameter(f"Unknown target: {target}")

    result = run_build(target, targets[target], dry_run=dry_run)
    print(result)
    _raise_if_error(result, context=f"build ({target})")


@app.command()
def deploy(
    target: str = typer.Argument(..., help="Target name from configs/targets.yaml"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Git commit message"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the steps that would run without executing them."),
) -> None:
    """Commit and push local changes for CI/CD deployment."""
    targets = load_targets(Path("configs/targets.yaml"))
    if target not in targets:
        raise typer.BadParameter(f"Unknown target: {target}")

    result = run_deploy(target, targets[target], commit_message=message, dry_run=dry_run)
    print(result)
    _raise_if_error(result, context=f"deploy ({target})")


@app.command("list-targets")
def list_targets() -> None:
    """Show deploy targets configured in configs/targets.yaml."""
    targets = load_targets(Path("configs/targets.yaml"))
    table = Table(title="Casper Node targets")
    table.add_column("name", style="bold")
    table.add_column("path")
    table.add_column("type")
    table.add_column("branch")
    for name, cfg in targets.items():
        table.add_row(
            name,
            str(cfg.get("path", "")),
            str(cfg.get("type", "")),
            str(cfg.get("branch", "main")),
        )
    Console().print(table)


if __name__ == "__main__":
    app()
