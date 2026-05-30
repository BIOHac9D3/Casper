"""
Casper Node - Skill Management CLI Commands

This module adds skill management commands to the Casper CLI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print

from core.registry.skills import SkillRegistry
from core.parsers.codex_parser import CodexParser

app = typer.Typer(help="Casper Node Skill Management")

# Global registry instance
registry = SkillRegistry()


@app.callback()
def init() -> None:
    """Initialize the skill management CLI."""
    # Load skills from Codex if available
    codex_path = Path(__file__).parent.parent / "Codex" / "agent_system.py"
    if codex_path.exists():
        try:
            parser = CodexParser(codex_path)
            skills = parser.parse()
            for skill in skills:
                registry.register(skill, "codex")
            print(f"[green]Loaded {len(skills)} skills from Codex[/green]")
        except Exception as e:
            print(f"[yellow]Warning: Could not load Codex skills: {e}[/yellow]")


@app.command()
def list(
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Filter by domain"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    enabled: Optional[bool] = typer.Option(None, "--enabled", "-e", help="Filter by enabled status"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all details")
) -> None:
    """List available skills."""
    skills = registry.list_all()
    
    # Apply filters
    if domain:
        skills = [s for s in skills if s.domain.value == domain]
    if tag:
        skills = [s for s in skills if tag in s.tags]
    if enabled is not None:
        skills = [s for s in skills if s.enabled == enabled]
    
    if not skills:
        print("[yellow]No skills found matching the criteria[/yellow]")
        return
    
    print(f"[bold]Found {len(skills)} skill(s):[/bold]\n")
    
    for skill in skills:
        status = "[green]enabled[/green]" if skill.enabled else "[red]disabled[/red]"
        if all:
            print(f"[bold]{skill.id}[/bold] ({skill.name})")
            print(f"  Domain: {skill.domain.value}")
            print(f"  Description: {skill.description}")
            print(f"  Status: {status}")
            print(f"  Triggers: {', '.join(t.phrase for t in skill.triggers)}")
            print(f"  Tags: {', '.join(skill.tags) if skill.tags else 'none'}")
            print()
        else:
            print(f"  {skill.id:20} {skill.name:30} {skill.domain.value:15} {status}")
    
    if not all:
        print()
        print("[dim]Use --all to show full details[/dim]")


@app.command()
def show(skill_id: str) -> None:
    """Show details of a specific skill."""
    skill = registry.get(skill_id)
    
    if not skill:
        print(f"[red]Skill '{skill_id}' not found[/red]")
        raise typer.Exit(1)
    
    print(f"[bold]{skill.id}[/bold]")
    print(f"  Name: {skill.name}")
    print(f"  Domain: {skill.domain.value}")
    print(f"  Description: {skill.description}")
    print(f"  Status: {'[green]enabled[/green]' if skill.enabled else '[red]disabled[/red]'}")
    print(f"  Version: {skill.version}")
    print(f"  Author: {skill.author or 'unknown'}")
    print(f"  Priority: {skill.priority}")
    print()
    print(f"  [bold]Triggers:[/bold]")
    for trigger in skill.triggers:
        print(f"    - {trigger.phrase} (weight: {trigger.weight})")
    print()
    print(f"  [bold]Inputs:[/bold]")
    if skill.inputs:
        for input_spec in skill.inputs:
            required = "[red]required[/red]" if input_spec.required else "[dim]optional[/dim]"
            print(f"    - {input_spec.name}: {input_spec.type.value} {required}")
            print(f"      Prompt: {input_spec.prompt}")
            if input_spec.default:
                print(f"      Default: {input_spec.default}")
            if input_spec.options:
                print(f"      Options: {', '.join(input_spec.options)}")
    else:
        print("    (none)")
    print()
    print(f"  [bold]Disallowed:[/bold]")
    if skill.disallowed:
        for item in skill.disallowed:
            print(f"    - {item}")
    else:
        print("    (none)")
    print()
    print(f"  [bold]Tags:[/bold]")
    if skill.tags:
        for tag in skill.tags:
            print(f"    - {tag}")
    else:
        print("    (none)")


@app.command()
def enable(skill_id: str) -> None:
    """Enable a skill."""
    success = registry.enable_skill(skill_id)
    
    if success:
        print(f"[green]Skill '{skill_id}' enabled[/green]")
    else:
        print(f"[red]Skill '{skill_id}' not found[/red]")
        raise typer.Exit(1)


@app.command()
def disable(skill_id: str) -> None:
    """Disable a skill."""
    success = registry.disable_skill(skill_id)
    
    if success:
        print(f"[green]Skill '{skill_id}' disabled[/green]")
    else:
        print(f"[red]Skill '{skill_id}' not found[/red]")
        raise typer.Exit(1)


@app.command()
def import_codex(repo_path: Optional[str] = None) -> None:
    """Import skills from Codex repository."""
    if repo_path is None:
        # Try to find Codex in parent directory
        codex_path = Path(__file__).parent.parent.parent / "Codex"
        if codex_path.exists():
            repo_path = str(codex_path)
        else:
            print("[red]Codex repository path required[/red]")
            print("Usage: casper skills import-codex /path/to/Codex")
            raise typer.Exit(1)
    
    try:
        parser = CodexParser(repo_path)
        skills = parser.parse_from_codex_repo(repo_path)
        
        count = 0
        for skill in skills:
            registry.register(skill, "codex")
            count += 1
        
        print(f"[green]Imported {count} skills from Codex[/green]")
    except Exception as e:
        print(f"[red]Failed to import from Codex: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stats() -> None:
    """Show skill registry statistics."""
    stats = registry.get_stats()
    
    print("[bold]Skill Registry Statistics[/bold]\n")
    print(f"  Total Skills: {stats['total_skills']}")
    print(f"  Enabled: {stats['enabled_skills']}")
    print(f"  Disabled: {stats['disabled_skills']}")
    print()
    
    print("[bold]By Domain:[/bold]")
    for domain, count in sorted(stats['domains'].items()):
        print(f"  {domain}: {count}")
    print()
    
    print("[bold]By Source:[/bold]")
    for source, count in sorted(stats['sources'].items()):
        print(f"  {source}: {count}")
    print()
    
    print("[bold]By Tag:[/bold]")
    for tag, count in sorted(stats['tags'].items()):
        print(f"  {tag}: {count}")


@app.command()
def test(skill_id: str, prompt: str) -> None:
    """Test a skill with a prompt."""
    from agents.skill_adapter import SkillAgent
    
    skill = registry.get(skill_id)
    if not skill:
        print(f"[red]Skill '{skill_id}' not found[/red]")
        raise typer.Exit(1)
    
    agent = SkillAgent(registry, interactive=False)
    
    try:
        result = agent.generate(prompt)
        print(f"[bold]Skill: {result.get('skill', {}).get('name', 'unknown')}[/bold]")
        print(f"[bold]Result:[/bold]")
        print(result.get('message', result))
    except Exception as e:
        print(f"[red]Error executing skill: {e}[/red]")
        raise typer.Exit(1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()