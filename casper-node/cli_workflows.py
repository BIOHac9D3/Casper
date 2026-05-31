from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.table import Table

from core.registry.skills import SkillRegistry
from core.registry.workflows import WorkflowRegistry
from core.workflows.engine import WorkflowEngine
from core.schemas.workflow import Workflow, WorkflowStatus

app = typer.Typer(help="Casper Node Workflow Management")

skill_registry = SkillRegistry()
workflow_registry = WorkflowRegistry()
workflow_engine = WorkflowEngine(skill_registry, workflow_registry)


@app.callback()
def init() -> None:
    global skill_registry, workflow_registry, workflow_engine
    codex_path = Path(__file__).parent.parent / "Codex" / "agent_system.py"
    if codex_path.exists():
        try:
            from core.parsers.codex_parser import CodexParser
            parser = CodexParser(codex_path)
            skills = parser.parse()
            for skill in skills:
                skill_registry.register(skill, "codex")
            print(f"[green]Loaded {len(skills)} skills from Codex[/green]")
        except Exception as e:
            print(f"[yellow]Warning: Could not load Codex skills: {e}[/yellow]")
    workflow_engine = WorkflowEngine(skill_registry, workflow_registry)


@app.command()
def list(
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Filter by domain"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all details")
) -> None:
    workflows = workflow_registry.list_all()
    if domain:
        workflows = [w for w in workflows if w.domain.value == domain]
    if tag:
        workflows = [w for w in workflows if tag in w.tags]
    if status:
        try:
            status_enum = WorkflowStatus(status.lower())
            workflows = [w for w in workflows if w.status == status_enum]
        except ValueError:
            print(f"[red]Unknown status: {status}[/red]")
            print(f"[dim]Available statuses: {[s.value for s in WorkflowStatus]}[/dim]")
            raise typer.Exit(1)
    
    if not workflows:
        print("[yellow]No workflows found matching the criteria[/yellow]")
        return
    
    if all:
        for workflow in workflows:
            print(f"[bold]{workflow.id}[/bold] ({workflow.name})")
            print(f"  Description: {workflow.description}")
            print(f"  Domain: {workflow.domain.value}")
            print(f"  Status: {workflow.status.value}")
            print(f"  Enabled: {workflow.enabled}")
            print(f"  Version: {workflow.version}")
            print(f"  Steps: {len(workflow.steps)}")
            print(f"  Tags: {', '.join(workflow.tags) if workflow.tags else 'none'}")
            print()
    else:
        table = Table(title="Available Workflows")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Domain", style="blue")
        table.add_column("Steps", style="magenta")
        table.add_column("Status", style="")
        table.add_column("Enabled", style="")
        
        for workflow in workflows:
            status_color = "green" if workflow.status == WorkflowStatus.ACTIVE else "yellow" if workflow.status == WorkflowStatus.DRAFT else "red"
            enabled_str = "[green]yes[/green]" if workflow.enabled else "[red]no[/red]"
            table.add_row(
                workflow.id,
                workflow.name,
                workflow.domain.value,
                str(len(workflow.steps)),
                f"[{status_color}]{workflow.status.value}[/{status_color}]",
                enabled_str
            )
        
        print(table)
        print(f"[dim]Found {len(workflows)} workflow(s)[/dim]")


@app.command()
def show(workflow_id: str) -> None:
    workflow = workflow_registry.get(workflow_id)
    
    if not workflow:
        print(f"[red]Workflow '{workflow_id}' not found[/red]")
        raise typer.Exit(1)
    
    print(f"[bold]{workflow.id}[/bold]")
    print(f"  Name: {workflow.name}")
    print(f"  Description: {workflow.description}")
    print(f"  Domain: {workflow.domain.value}")
    print(f"  Version: {workflow.version}")
    print(f"  Author: {workflow.author or 'unknown'}")
    print(f"  Status: {workflow.status.value}")
    print(f"  Enabled: {'[green]yes[/green]' if workflow.enabled else '[red]no[/red]'}")
    print(f"  Tags: {', '.join(workflow.tags) if workflow.tags else 'none'}")
    print(f"  Retry Policy: {workflow.retry_policy}")
    print(f"  Timeout: {workflow.timeout or 'none'}")
    print()
    
    print(f"[bold]Steps ({len(workflow.steps)}):[/bold]")
    for step in sorted(workflow.steps, key=lambda s: s.position):
        print(f"  {step.position + 1}. {step.id} ({step.name or step.skill_id})")
        print(f"     Skill: {step.skill_id}")
        print(f"     Required: {'[green]yes[/green]' if step.required else '[red]no[/red]'}")
        if step.depends_on:
            print(f"     Depends on: {', '.join(step.depends_on)}")
        if step.timeout:
            print(f"     Timeout: {step.timeout}s")
        if step.retry_count:
            print(f"     Retries: {step.retry_count}")
        print()
    
    print(f"[bold]Output Mappings ({len(workflow.output_mappings)}):[/bold]")
    if workflow.output_mappings:
        for mapping in workflow.output_mappings:
            print(f"  {mapping.source_step}.{mapping.source_output} -> {mapping.target_step}.{mapping.target_input}")
    else:
        print(f"  [dim](none)[/dim]")
    print()


@app.command()
def run(
    workflow_id: str = typer.Argument(..., help="ID of the workflow to execute"),
    input_file: Optional[str] = typer.Option(None, "--inputs", "-i", help="Path to JSON file with workflow inputs"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Timeout in seconds")
) -> None:
    import json
    
    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        print(f"[red]Workflow '{workflow_id}' not found[/red]")
        raise typer.Exit(1)
    
    if not workflow.enabled:
        print(f"[red]Workflow '{workflow_id}' is disabled[/red]")
        raise typer.Exit(1)
    
    inputs = {}
    if input_file:
        try:
            with open(input_file, 'r') as f:
                inputs = json.load(f)
            print(f"[green]Loaded inputs from {input_file}[/green]")
        except Exception as e:
            print(f"[red]Failed to load inputs: {e}[/red]")
            raise typer.Exit(1)
    
    print(f"[bold]Executing workflow: {workflow.name}[/bold]")
    print(f"  ID: {workflow.id}")
    print(f"  Steps: {len(workflow.steps)}")
    print()
    
    result = workflow_engine.execute_workflow(workflow_id, inputs, timeout)
    
    if result.get("status") == "completed":
        print(f"[green]Workflow completed successfully![/green]")
        print(f"  Execution ID: {result.get('execution_id')}")
        print(f"  Execution Time: {result.get('execution_time'):.2f}s")
        print(f"  Steps Completed: {result.get('steps_completed')}")
    elif result.get("status") == "failed":
        print(f"[red]Workflow failed![/red]")
        print(f"  Failed Step: {result.get('failed_step')}")
        print(f"  Error: {result.get('error')}")
        print(f"  Completed Steps: {result.get('completed_steps')}")
    else:
        print(f"[yellow]Workflow status: {result.get('status')}[/yellow]")
    
    print()
    print(f"[bold]Step Results:[/bold]")
    for step_result in result.get("step_results", []):
        status = step_result.get("status", "unknown")
        status_color = "green" if status == "ok" else "red" if status == "error" else "yellow"
        print(f"  [{status_color}]{step_result.get('step_id', 'unknown')}[/{status_color}] {status}")


@app.command()
def enable(workflow_id: str) -> None:
    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        print(f"[red]Workflow '{workflow_id}' not found[/red]")
        raise typer.Exit(1)
    workflow.enabled = True
    print(f"[green]Workflow '{workflow_id}' enabled[/green]")


@app.command()
def disable(workflow_id: str) -> None:
    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        print(f"[red]Workflow '{workflow_id}' not found[/red]")
        raise typer.Exit(1)
    workflow.enabled = False
    print(f"[green]Workflow '{workflow_id}' disabled[/green]")


@app.command()
def stats() -> None:
    stats = workflow_registry.get_stats()
    
    print("[bold]Workflow Registry Statistics[/bold]\n")
    print(f"  Total Workflows: {stats['total_workflows']}")
    print(f"  Enabled: {stats['enabled_workflows']}")
    print(f"  Disabled: {stats['disabled_workflows']}")
    print()
    
    print("[bold]By Domain:[/bold]")
    for domain, count in sorted(stats['domains'].items()):
        print(f"  {domain}: {count}")
    print()
    
    print("[bold]By Status:[/bold]")
    for status, count in sorted(stats['statuses'].items()):
        print(f"  {status}: {count}")
    print()
    
    print("[bold]By Tag:[/bold]")
    for tag, count in sorted(stats['tags'].items()):
        print(f"  {tag}: {count}")


@app.command()
def validate(workflow_id: str) -> None:
    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        print(f"[red]Workflow '{workflow_id}' not found[/red]")
        raise typer.Exit(1)
    
    errors = workflow.validate()
    
    if errors:
        print(f"[red]Workflow '{workflow_id}' has validation errors:[/red]")
        for error in errors:
            print(f"  - {error}")
        raise typer.Exit(1)
    else:
        print(f"[green]Workflow '{workflow_id}' is valid[/green]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
