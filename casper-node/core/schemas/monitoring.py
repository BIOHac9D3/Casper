from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class ComponentHealth(BaseModel):
    component: str = Field(..., description="Name of the component")
    status: HealthStatus = Field(default=HealthStatus.UNKNOWN, description="Current health status")
    message: str = Field(default="", description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Last check timestamp")
    latency_ms: Optional[float] = Field(default=None, description="Response latency in milliseconds")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")


class SystemHealth(BaseModel):
    status: HealthStatus = Field(default=HealthStatus.UNKNOWN, description="Overall system health")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    components: List[ComponentHealth] = Field(default_factory=list, description="Health of individual components")
    version: str = Field(default="1.0.0", description="System version")
    uptime_seconds: float = Field(default=0.0, description="System uptime in seconds")


class Alert(BaseModel):
    id: str = Field(..., description="Unique alert identifier")
    name: str = Field(..., description="Alert name")
    description: str = Field(default="", description="Detailed alert description")
    severity: AlertSeverity = Field(default=AlertSeverity.INFO, description="Alert severity level")
    status: AlertStatus = Field(default=AlertStatus.OPEN, description="Current alert status")
    component: str = Field(..., description="Affected component")
    metric: Optional[str] = Field(default=None, description="Related metric name")
    threshold: Optional[float] = Field(default=None, description="Threshold value that was exceeded")
    current_value: Optional[float] = Field(default=None, description="Current value when alert triggered")
    triggered_at: datetime = Field(default_factory=datetime.utcnow, description="When alert was triggered")
    acknowledged_at: Optional[datetime] = Field(default=None, description="When alert was acknowledged")
    resolved_at: Optional[datetime] = Field(default=None, description="When alert was resolved")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context data")


class Metric(BaseModel):
    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Type of metric")
    value: float = Field(..., description="Current metric value")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels for filtering")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When metric was recorded")
    description: str = Field(default="", description="Metric description")


class MetricDefinition(BaseModel):
    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Type of metric")
    description: str = Field(default="", description="Metric description")
    labels: List[str] = Field(default_factory=list, description="Default labels")
    alert_threshold: Optional[float] = Field(default=None, description="Threshold for alerts")
    alert_severity: str = Field(default="warning", description="Severity for threshold alerts")


class SkillUsageStats(BaseModel):
    skill_id: str = Field(..., description="ID of the skill")
    total_executions: int = Field(default=0, description="Total number of executions")
    successful_executions: int = Field(default=0, description="Number of successful executions")
    failed_executions: int = Field(default=0, description="Number of failed executions")
    total_execution_time: float = Field(default=0.0, description="Total execution time in seconds")
    avg_execution_time: float = Field(default=0.0, description="Average execution time in seconds")
    last_execution: Optional[datetime] = Field(default=None, description="Last execution timestamp")
    last_success: Optional[datetime] = Field(default=None, description="Last successful execution timestamp")
    last_failure: Optional[datetime] = Field(default=None, description="Last failure timestamp")
    error_rates: Dict[str, int] = Field(default_factory=dict, description="Error counts by error type")


class AnalyticsSummary(BaseModel):
    total_skills: int = Field(default=0, description="Total number of skills")
    total_executions: int = Field(default=0, description="Total skill executions")
    success_rate: float = Field(default=0.0, description="Overall success rate")
    avg_execution_time: float = Field(default=0.0, description="Average execution time")
    most_used_skills: List[Dict[str, Any]] = Field(default_factory=list, description="Top used skills")
    recent_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Recent errors")
    execution_trends: Dict[str, int] = Field(default_factory=dict, description="Execution counts by time period")
