from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich import print

from agents.claude_agent import ClaudeAgent
from agents.openai_agent import OpenAIAgent
from core.config import load_targets
from core.memory import MemoryStore
from pipelines.build import run_build
from pipelines.deploy import run_deploy

app = typer.Typer(help="Casper Node: mobile-first AI + CI/CD orchestrator")


@app.callback()
def init() -> None:
    load_dotenv()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Prompt to send to an AI agent"),
    provider: str = typer.Option("openai", "--provider", "-p", help="openai or claude"),
) -> None:
    """Generate content from configured AI provider."""
    store = MemoryStore(Path("memory"))

    if provider.lower() == "openai":
        agent = OpenAIAgent()
    elif provider.lower() == "claude":
        agent = ClaudeAgent()
    else:
        raise typer.BadParameter("Provider must be one of: openai, claude")

    result = agent.generate(prompt)
    store.log_event("generate", {"provider": provider, "status": result.get("status")})
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
