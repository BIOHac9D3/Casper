from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import uuid
import logging

from core.schemas.monitoring import Alert, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)


class AlertHandler:
    def handle_alert(self, alert: Alert) -> None:
        raise NotImplementedError


class ConsoleAlertHandler(AlertHandler):
    def handle_alert(self, alert: Alert) -> None:
        color_map = {
            AlertSeverity.INFO: "blue",
            AlertSeverity.WARNING: "yellow",
            AlertSeverity.ERROR: "red",
            AlertSeverity.CRITICAL: "red"
        }
        color = color_map.get(alert.severity, "white")
        logger.log(
            self._severity_to_level(alert.severity),
            f"[{color}]{alert.name}[/{color}] {alert.description} (Component: {alert.component})"
        )
    
    def _severity_to_level(self, severity: AlertSeverity) -> int:
        level_map = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }
        return level_map.get(severity, logging.INFO)


class AlertManager:
    def __init__(self) -> None:
        self.alerts: Dict[str, Alert] = {}
        self.handlers: List[AlertHandler] = [ConsoleAlertHandler()]
        self.subscribers: List[Callable[[Alert], None]] = []
    
    def add_handler(self, handler: AlertHandler) -> None:
        self.handlers.append(handler)
    
    def remove_handler(self, handler: AlertHandler) -> None:
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def subscribe(self, callback: Callable[[Alert], None]) -> None:
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[Alert], None]) -> None:
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def trigger(
        self,
        name: str,
        component: str,
        description: str = "",
        severity: AlertSeverity = AlertSeverity.INFO,
        metric: Optional[str] = None,
        threshold: Optional[float] = None,
        current_value: Optional[float] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Alert:
        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            name=name,
            description=description,
            severity=severity,
            status=AlertStatus.OPEN,
            component=component,
            metric=metric,
            threshold=threshold,
            current_value=current_value,
            triggered_at=datetime.utcnow(),
            tags=tags or [],
            context=context or {}
        )
        self.alerts[alert_id] = alert
        
        for handler in self.handlers:
            try:
                handler.handle_alert(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        for callback in self.subscribers:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert subscriber error: {e}")
        
        return alert
    
    def acknowledge(self, alert_id: str, user: Optional[str] = None) -> Optional[Alert]:
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        if alert.context is None:
            alert.context = {}
        alert.context["acknowledged_by"] = user or "system"
        return alert
    
    def resolve(self, alert_id: str, user: Optional[str] = None, message: str = "") -> Optional[Alert]:
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.description = f"{alert.description} - Resolved: {message}" if message else alert.description
        if alert.context is None:
            alert.context = {}
        alert.context["resolved_by"] = user or "system"
        alert.context["resolution"] = message
        return alert
    
    def close(self, alert_id: str, user: Optional[str] = None) -> Optional[Alert]:
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.CLOSED
        alert.resolved_at = datetime.utcnow()
        if alert.context is None:
            alert.context = {}
        alert.context["closed_by"] = user or "system"
        return alert
    
    def list_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        component: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Alert]:
        alerts = list(self.alerts.values())
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if component:
            alerts = [a for a in alerts if a.component == component]
        
        alerts.sort(key=lambda a: a.triggered_at, reverse=True)
        
        if limit:
            alerts = alerts[:limit]
        
        return alerts
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        return self.alerts.get(alert_id)
    
    def delete_alert(self, alert_id: str) -> bool:
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            return True
        return False
    
    def clear_all(self) -> int:
        count = len(self.alerts)
        self.alerts.clear()
        return count
    
    def get_open_alerts(self) -> List[Alert]:
        return [a for a in self.alerts.values() if a.status == AlertStatus.OPEN]
    
    def get_alert_count_by_status(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for alert in self.alerts.values():
            status = alert.status.value
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    def get_alert_count_by_severity(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for alert in self.alerts.values():
            severity = alert.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts
