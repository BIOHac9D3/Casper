from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import typer
from rich import print
from rich.table import Table
from rich.progress import Progress

from core.monitoring.health import HealthChecker
from core.monitoring.alerts import AlertManager, Alert, AlertStatus, AlertSeverity
from core.monitoring.metrics import MetricsCollector
from core.monitoring.analytics import AnalyticsTracker
from core.schemas.monitoring import HealthStatus

app = typer.Typer(help="Casper Node Monitoring and Alerting")

health_checker = HealthChecker()
alert_manager = AlertManager()
metrics_collector = MetricsCollector()
analytics_tracker = AnalyticsTracker()


@app.callback()
def init() -> None:
    global health_checker, alert_manager, metrics_collector, analytics_tracker
    health_checker = HealthChecker()
    alert_manager = AlertManager()
    metrics_collector = MetricsCollector()
    analytics_tracker = AnalyticsTracker()


@app.command()
def health(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed health information"),
    check: Optional[str] = typer.Option(None, "--check", "-c", help="Check specific component")
) -> None:
    if check:
        component_health = health_checker.check_component(check)
        if component_health:
            print(f"[bold]{check}[/bold]")
            print(f"  Status: [{_status_color(component_health.status)}{component_health.status.value}[/{_status_color(component_health.status)}]")
            print(f"  Message: {component_health.message}")
            print(f"  Timestamp: {component_health.timestamp}")
            if component_health.details:
                print(f"  Details: {component_health.details}")
        else:
            print(f"[red]Component '{check}' not found[/red]")
            available = list(health_checker.checks.keys())
            print(f"[dim]Available checks: {', '.join(available)}[/dim]")
        return
    
    system_health = health_checker.check_health()
    
    if detailed:
        print(f"[bold]System Health Report[/bold]
")
        print(f"  Overall Status: [{_status_color(system_health.status)}{system_health.status.value}[/{_status_color(system_health.status)}]")
        print(f"  Version: {system_health.version}")
        print(f"  Uptime: {_format_uptime(system_health.uptime_seconds)}")
        print(f"  Timestamp: {system_health.timestamp}")
        print()
        
        print("[bold]Component Health:[/bold]")
        for component in system_health.components:
            color = _status_color(component.status)
            print(f"  [{color}]{component.component}[/{color}] {component.status.value}: {component.message}")
            if component.details:
                for key, value in component.details.items():
                    print(f"    {key}: {value}")
    else:
        table = Table(title="System Health")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="")
        table.add_column("Message", style="white")
        
        for component in system_health.components:
            color = _status_color(component.status)
            table.add_row(
                component.component,
                f"[{color}]{component.status.value}[/{color}]",
                component.message
            )
        
        print(table)
        print(f"
[bold]Overall Status:[/bold] [{_status_color(system_health.status)}{system_health.status.value}[/{_status_color(system_health.status)}]")
        print(f"[dim]Uptime: {_format_uptime(system_health.uptime_seconds)}[/dim]")


@app.command()
def alerts(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (open, acknowledged, resolved, closed)"),
    severity: Optional[str] = typer.Option(None, "--severity", help="Filter by severity (info, warning, error, critical)"),
    component: Optional[str] = typer.Option(None, "--component", "-c", help="Filter by component"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of alerts to show"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all alerts")
) -> None:
    status_filter = None
    if status:
        try:
            status_filter = AlertStatus(status.lower())
        except ValueError:
            print(f"[red]Invalid status: {status}[/red]")
            print(f"[dim]Valid statuses: {[s.value for s in AlertStatus]}[/dim]")
            raise typer.Exit(1)
    
    severity_filter = None
    if severity:
        try:
            severity_filter = AlertSeverity(severity.lower())
        except ValueError:
            print(f"[red]Invalid severity: {severity}[/red]")
            print(f"[dim]Valid severities: {[s.value for s in AlertSeverity]}[/dim]")
            raise typer.Exit(1)
    
    alerts = alert_manager.list_alerts(
        status=status_filter,
        severity=severity_filter,
        component=component,
        limit=limit if not all else None
    )
    
    if not alerts:
        print("[yellow]No alerts found matching the criteria[/yellow]")
        return
    
    table = Table(title="Alerts")
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Name", style="green")
    table.add_column("Severity", style="")
    table.add_column("Status", style="")
    table.add_column("Component", style="blue")
    table.add_column("Triggered", style="dim")
    
    for alert in alerts:
        severity_color = _severity_color(alert.severity)
        status_color = _status_color_alert(alert.status)
        table.add_row(
            alert.id[:8],
            alert.name,
            f"[{severity_color}]{alert.severity.value}[/{severity_color}]",
            f"[{status_color}]{alert.status.value}[/{status_color}]",
            alert.component,
            alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    print(table)
    print(f"[dim]Found {len(alerts)} alert(s)[/dim]")


@app.command()
def alerts_acknowledge(alert_id: str, user: Optional[str] = None) -> None:
    alert = alert_manager.acknowledge(alert_id, user)
    if alert:
        print(f"[green]Alert '{alert_id}' acknowledged[/green]")
    else:
        print(f"[red]Alert '{alert_id}' not found[/red]")
        raise typer.Exit(1)


@app.command()
def alerts_resolve(alert_id: str, message: str = "", user: Optional[str] = None) -> None:
    alert = alert_manager.resolve(alert_id, user, message)
    if alert:
        print(f"[green]Alert '{alert_id}' resolved[/green]")
        if message:
            print(f"  Resolution: {message}")
    else:
        print(f"[red]Alert '{alert_id}' not found[/red]")
        raise typer.Exit(1)


@app.command()
def metrics(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter by metric name"),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of metrics to show"),
    stats: bool = typer.Option(False, "--stats", "-s", help="Show statistics instead of raw metrics")
) -> None:
    if stats:
        all_stats = metrics_collector.get_all_stats()
        if name:
            if name in all_stats:
                stat = all_stats[name]
                print(f"[bold]{name}[/bold]")
                print(f"  Count: {stat['count']}")
                print(f"  Min: {stat['min']}")
                print(f"  Max: {stat['max']}")
                print(f"  Avg: {stat['avg']:.4f}")
                print(f"  Sum: {stat['sum']}")
                if stat['latest']:
                    print(f"  Latest: {stat['latest']}")
            else:
                print(f"[red]Metric '{name}' not found[/red]")
            return
        
        table = Table(title="Metric Statistics")
        table.add_column("Name", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Min", style="")
        table.add_column("Max", style="")
        table.add_column("Avg", style="")
        
        for metric_name, stat in sorted(all_stats.items()):
            table.add_row(
                metric_name,
                str(stat['count']),
                str(stat['min']) if stat['min'] is not None else "N/A",
                str(stat['max']) if stat['max'] is not None else "N/A",
                f"{stat['avg']:.4f}" if stat['avg'] is not None else "N/A"
            )
        
        print(table)
        return
    
    if name:
        metrics = metrics_collector.get_metric(name, limit)
        if not metrics:
            print(f"[yellow]No metrics found for '{name}'[/yellow]")
            return
        
        table = Table(title=f"Metrics: {name}")
        table.add_column("Timestamp", style="dim")
        table.add_column("Value", style="green")
        table.add_column("Labels", style="blue")
        
        for metric in metrics:
            labels_str = ", ".join(f"{k}={v}" for k, v in metric.labels.items()) if metric.labels else "-"
            table.add_row(
                metric.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                str(metric.value),
                labels_str
            )
        
        print(table)
    else:
        all_metrics = metrics_collector.get_all_metrics()
        table = Table(title="All Metrics")
        table.add_column("Name", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Latest Value", style="")
        table.add_column("Latest Timestamp", style="dim")
        
        for name, metrics in sorted(all_metrics.items()):
            latest = metrics[-1] if metrics else None
            table.add_row(
                name,
                str(len(metrics)),
                str(latest.value) if latest else "N/A",
                latest.timestamp.strftime("%Y-%m-%d %H:%M:%S") if latest else "N/A"
            )
        
        print(table)


@app.command()
def analytics(
    summary: bool = typer.Option(False, "--summary", "-s", help="Show analytics summary"),
    skill: Optional[str] = typer.Option(None, "--skill", help="Show stats for specific skill"),
    errors: bool = typer.Option(False, "--errors", "-e", help="Show error analysis")
) -> None:
    if errors:
        error_analysis = analytics_tracker.get_error_analysis()
        print("[bold]Error Analysis[/bold]
")
        print(f"  Total Errors: {error_analysis['total_errors']}")
        print()
        
        print("[bold]Error Counts by Type:[/bold]")
        for error_type, count in sorted(error_analysis['error_counts'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count}")
        print()
        
        print("[bold]Errors by Skill:[/bold]")
        for skill_id, skill_errors in error_analysis['error_by_skill'].items():
            print(f"  {skill_id}:")
            for error_type, count in sorted(skill_errors.items(), key=lambda x: x[1], reverse=True):
                print(f"    {error_type}: {count}")
        return
    
    if summary:
        summary = analytics_tracker.get_summary()
        print("[bold]Analytics Summary[/bold]
")
        print(f"  Total Skills: {summary.total_skills}")
        print(f"  Total Executions: {summary.total_executions}")
        print(f"  Success Rate: {summary.success_rate:.2f}%")
        print(f"  Average Execution Time: {summary.avg_execution_time:.4f}s")
        print()
        
        print("[bold]Execution Trends:[/bold]")
        for period, count in summary.execution_trends.items():
            print(f"  {period}: {count}")
        print()
        
        print("[bold]Most Used Skills:[/bold]")
        for skill in summary.most_used_skills[:5]:
            print(f"  {skill['skill_id']}: {skill['total_executions']} executions")
        print()
        
        print("[bold]Recent Errors:[/bold]")
        for error in summary.recent_errors[:5]:
            print(f"  {error['timestamp']}: {error['skill_id']} - {error['error_type']}")
        return
    
    if skill:
        stats = analytics_tracker.get_skill_stats(skill)
        if stats:
            print(f"[bold]{skill}[/bold]")
            print(f"  Total Executions: {stats.total_executions}")
            print(f"  Successful: {stats.successful_executions}")
            print(f"  Failed: {stats.failed_executions}")
            print(f"  Total Execution Time: {stats.total_execution_time:.4f}s")
            print(f"  Average Execution Time: {stats.avg_execution_time:.4f}s")
            print(f"  Last Execution: {stats.last_execution}")
            print(f"  Last Success: {stats.last_success}")
            print(f"  Last Failure: {stats.last_failure}")
            print()
            
            if stats.error_rates:
                print("[bold]Error Rates:[/bold]")
                for error_type, count in stats.error_rates.items():
                    print(f"  {error_type}: {count}")
        else:
            print(f"[yellow]No stats found for skill '{skill}'[/yellow]")
        return
    
    all_stats = analytics_tracker.get_all_skill_stats()
    if not all_stats:
        print("[yellow]No skill statistics available[/yellow]")
        return
    
    table = Table(title="Skill Statistics")
    table.add_column("Skill ID", style="cyan")
    table.add_column("Total", style="green")
    table.add_column("Success", style="green")
    table.add_column("Failed", style="red")
    table.add_column("Avg Time", style="")
    table.add_column("Last Exec", style="dim")
    
    for skill_id, stats in sorted(all_stats.items(), key=lambda x: x[1].total_executions, reverse=True):
        success_rate = (stats.successful_executions / stats.total_executions * 100) if stats.total_executions > 0 else 0
        table.add_row(
            skill_id,
            str(stats.total_executions),
            f"[green]{stats.successful_executions}[/green]",
            f"[red]{stats.failed_executions}[/red]",
            f"{stats.avg_execution_time:.4f}s",
            stats.last_execution.strftime("%Y-%m-%d %H:%M:%S") if stats.last_execution else "N/A"
        )
    
    print(table)


@app.command()
def stats() -> None:
    print("[bold]Monitoring Statistics[/bold]
")
    
    system_health = health_checker.check_health()
    print("[bold]System Health:[/bold]")
    print(f"  Status: [{_status_color(system_health.status)}{system_health.status.value}[/{_status_color(system_health.status)}]")
    print(f"  Components: {len(system_health.components)}")
    print(f"  Uptime: {_format_uptime(system_health.uptime_seconds)}")
    print()
    
    alert_counts = alert_manager.get_alert_count_by_status()
    print("[bold]Alerts:[/bold]")
    for status, count in alert_counts.items():
        print(f"  {status}: {count}")
    print()
    
    all_metrics = metrics_collector.get_all_metrics()
    print("[bold]Metrics:[/bold]")
    for name, metrics in all_metrics.items():
        print(f"  {name}: {len(metrics)} data points")
    print()
    
    summary = analytics_tracker.get_summary()
    print("[bold]Analytics:[/bold]")
    print(f"  Total Skills: {summary.total_skills}")
    print(f"  Total Executions: {summary.total_executions}")
    print(f"  Success Rate: {summary.success_rate:.2f}%")


def _status_color(status: HealthStatus) -> str:
    color_map = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.DEGRADED: "yellow",
        HealthStatus.UNHEALTHY: "red",
        HealthStatus.UNKNOWN: "white"
    }
    return color_map.get(status, "white")


def _status_color_alert(status: AlertStatus) -> str:
    color_map = {
        AlertStatus.OPEN: "red",
        AlertStatus.ACKNOWLEDGED: "yellow",
        AlertStatus.RESOLVED: "green",
        AlertStatus.CLOSED: "white"
    }
    return color_map.get(status, "white")


def _severity_color(severity: AlertSeverity) -> str:
    color_map = {
        AlertSeverity.INFO: "blue",
        AlertSeverity.WARNING: "yellow",
        AlertSeverity.ERROR: "red",
        AlertSeverity.CRITICAL: "red"
    }
    return color_map.get(severity, "white")


def _format_uptime(seconds: float) -> str:
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
