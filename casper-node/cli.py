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
except ModuleNotFoundError:
    if __name__ == "__main__":
        wants_help = any(arg in {"--help", "-h", "help"} for arg in sys.argv[1:])
        if wants_help:
            _fallback_help()
            raise SystemExit(0)
        print("Missing CLI dependencies. Run: python -m pip install -r requirements.txt")
        raise SystemExit(1)
    raise

from agents.claude_agent import ClaudeAgent
from agents.local_agent import LocalAgent
from agents.openai_agent import OpenAIAgent
from core.config import load_targets
from core.memory import MemoryStore
from pipelines.build import run_build
from pipelines.deploy import run_deploy

app = typer.Typer(help="Casper Node: mobile-first AI + CI/CD orchestrator")

OPENAI_MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"]
CLAUDE_MODELS = ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022", "claude-3-7-sonnet-latest"]
LOCAL_MODELS = ["llama3.2:1b", "llama3.2:3b", "qwen2.5:3b", "mistral:7b"]


@app.callback()
def init() -> None:
    load_dotenv()


def select_model(provider: str, requested_model: Optional[str]) -> str:
    if provider == "openai":
        choices = OPENAI_MODELS
        default_model = os.getenv("OPENAI_MODEL", OPENAI_MODELS[0])
    elif provider == "claude":
        choices = CLAUDE_MODELS
        default_model = os.getenv("ANTHROPIC_MODEL", CLAUDE_MODELS[1])
    else:
        choices = LOCAL_MODELS
        default_model = os.getenv("LOCAL_MODEL", LOCAL_MODELS[1])

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
    if result["status"] != "ok":
        raise RuntimeError(result["message"])


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

    if provider_name == "openai":
        agent = OpenAIAgent()
    elif provider_name == "claude":
        agent = ClaudeAgent()
    elif provider_name == "local":
        agent = LocalAgent()
    else:
        raise typer.BadParameter("Provider must be one of: openai, claude, local")

    selected_model = select_model(provider_name, model)

    if provider_name == "local" and auto_pull:
        pull_result = agent.ensure_model(selected_model)
        store.log_event(
            "pull_model",
            {"provider": provider_name, "model": selected_model, "status": pull_result.get("status")},
        )
        if pull_result["status"] != "ok":
            print(pull_result)
            raise RuntimeError(pull_result["message"])

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
) -> None:
    """Run build pipeline for a target."""
    targets = load_targets(Path("configs/targets.yaml"))
    if target not in targets:
        raise typer.BadParameter(f"Unknown target: {target}")

    result = run_build(target, targets[target])
    print(result)
    if result["status"] != "ok":
        raise RuntimeError(result["message"])


@app.command()
def deploy(
    target: str = typer.Argument(..., help="Target name from configs/targets.yaml"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Git commit message"),
) -> None:
    """Commit and push local changes for CI/CD deployment."""
    targets = load_targets(Path("configs/targets.yaml"))
    if target not in targets:
        raise typer.BadParameter(f"Unknown target: {target}")

    result = run_deploy(target, targets[target], commit_message=message)
    print(result)
    if result["status"] != "ok":
        raise RuntimeError(result["message"])


if __name__ == "__main__":
    app()
