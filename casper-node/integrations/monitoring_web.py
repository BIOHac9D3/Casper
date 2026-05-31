from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

from core.monitoring.health import HealthChecker
from core.monitoring.alerts import AlertManager, Alert, AlertStatus, AlertSeverity
from core.monitoring.metrics import MetricsCollector
from core.monitoring.analytics import AnalyticsTracker
from core.schemas.monitoring import (
    SystemHealth, 
    ComponentHealth, 
    HealthStatus,
    Metric,
    MetricType,
    MetricDefinition,
    SkillUsageStats,
    AnalyticsSummary
)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

health_checker = HealthChecker()
alert_manager = AlertManager()
metrics_collector = MetricsCollector()
analytics_tracker = AnalyticsTracker()


class AlertTriggerRequest(BaseModel):
    name: str
    component: str
    description: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    metric: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None
    tags: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class AlertAcknowledgeRequest(BaseModel):
    user: Optional[str] = None


class AlertResolveRequest(BaseModel):
    message: str = ""
    user: Optional[str] = None


class MetricRecordRequest(BaseModel):
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None
    description: str = ""


class MetricDefinitionRequest(BaseModel):
    name: str
    metric_type: MetricType
    description: str = ""
    labels: Optional[List[str]] = None
    alert_threshold: Optional[float] = None
    alert_severity: str = "warning"


@router.get("/health", response_model=SystemHealth)
async def get_health() -> SystemHealth:
    return health_checker.check_health()


@router.get("/health/{component}", response_model=ComponentHealth)
async def get_component_health(component: str) -> ComponentHealth:
    component_health = health_checker.check_component(component)
    if not component_health:
        raise HTTPException(status_code=404, detail=f"Component '{component}' not found")
    return component_health


@router.get("/alerts", response_model=List[Alert])
async def list_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    component: Optional[str] = Query(None, description="Filter by component"),
    limit: Optional[int] = Query(100, description="Maximum number of alerts to return")
) -> List[Alert]:
    return alert_manager.list_alerts(
        status=status,
        severity=severity,
        component=component,
        limit=limit
    )


@router.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str) -> Alert:
    alert = alert_manager.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert


@router.post("/alerts/trigger", response_model=Alert)
async def trigger_alert(request: AlertTriggerRequest) -> Alert:
    return alert_manager.trigger(
        name=request.name,
        component=request.component,
        description=request.description,
        severity=request.severity,
        metric=request.metric,
        threshold=request.threshold,
        current_value=request.current_value,
        tags=request.tags,
        context=request.context
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(alert_id: str, request: AlertAcknowledgeRequest) -> Alert:
    alert = alert_manager.acknowledge(alert_id, request.user)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert


@router.post("/alerts/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(alert_id: str, request: AlertResolveRequest) -> Alert:
    alert = alert_manager.resolve(alert_id, request.user, request.message)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert


@router.post("/alerts/{alert_id}/close", response_model=Alert)
async def close_alert(alert_id: str, request: AlertAcknowledgeRequest) -> Alert:
    alert = alert_manager.close(alert_id, request.user)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert


@router.get("/alerts/stats")
async def get_alert_stats() -> Dict[str, Any]:
    return {
        "by_status": alert_manager.get_alert_count_by_status(),
        "by_severity": alert_manager.get_alert_count_by_severity(),
        "total": len(alert_manager.alerts)
    }


@router.get("/metrics", response_model=Dict[str, List[Metric]])
async def get_all_metrics() -> Dict[str, List[Metric]]:
    return metrics_collector.get_all_metrics()


@router.get("/metrics/{name}", response_model=List[Metric])
async def get_metric(name: str, limit: Optional[int] = Query(100)) -> List[Metric]:
    return metrics_collector.get_metric(name, limit)


@router.post("/metrics/{name}", response_model=Metric)
async def record_metric(name: str, request: MetricRecordRequest) -> Metric:
    return metrics_collector.record(
        name=name,
        value=request.value,
        labels=request.labels,
        description=request.description
    )


@router.post("/metrics/{name}/increment")
async def increment_metric(
    name: str,
    value: float = 1.0,
    labels: Optional[Dict[str, str]] = None,
    description: str = ""
) -> Metric:
    return metrics_collector.increment(name, value, labels, description)


@router.post("/metrics/define", response_model=Dict[str, Any])
async def define_metric(request: MetricDefinitionRequest) -> Dict[str, Any]:
    metrics_collector.register_metric(
        name=request.name,
        metric_type=request.metric_type,
        description=request.description,
        labels=request.labels,
        alert_threshold=request.alert_threshold,
        alert_severity=request.alert_severity
    )
    return {"status": "ok", "message": f"Metric '{request.name}' defined"}


@router.get("/metrics/{name}/stats")
async def get_metric_stats(name: str) -> Dict[str, Any]:
    return metrics_collector.get_metric_stats(name)


@router.get("/metrics/stats")
async def get_all_metric_stats() -> Dict[str, Dict[str, Any]]:
    return metrics_collector.get_all_stats()


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary() -> AnalyticsSummary:
    return analytics_tracker.get_summary()


@router.get("/analytics/skills")
async def get_all_skill_stats() -> Dict[str, SkillUsageStats]:
    return analytics_tracker.get_all_skill_stats()


@router.get("/analytics/skills/{skill_id}")
async def get_skill_stats(skill_id: str) -> Optional[SkillUsageStats]:
    return analytics_tracker.get_skill_stats(skill_id)


@router.get("/analytics/errors")
async def get_error_analysis() -> Dict[str, Any]:
    return analytics_tracker.get_error_analysis()


@router.get("/analytics/trends")
async def get_execution_trends() -> Dict[str, Any]:
    summary = analytics_tracker.get_summary()
    return {"trends": summary.execution_trends}


@router.get("/stats")
async def get_monitoring_stats() -> Dict[str, Any]:
    system_health = health_checker.check_health()
    return {
        "health": {
            "status": system_health.status.value,
            "components": len(system_health.components),
            "uptime_seconds": system_health.uptime_seconds
        },
        "alerts": alert_manager.get_alert_count_by_status(),
        "metrics": {
            "total_metrics": len(metrics_collector.metrics),
            "total_data_points": sum(len(v) for v in metrics_collector.metrics.values())
        },
        "analytics": {
            "total_skills": len(analytics_tracker.skill_stats),
            "total_executions": sum(
                s.total_executions for s in analytics_tracker.skill_stats.values()
            )
        }
    }
