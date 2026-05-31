from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import threading
import logging

from core.schemas.monitoring import Metric, MetricType, MetricDefinition

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self) -> None:
        self.metrics: Dict[str, List[Metric]] = {}
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self._lock = threading.Lock()
    
    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str = "",
        labels: Optional[List[str]] = None,
        alert_threshold: Optional[float] = None,
        alert_severity: str = "warning"
    ) -> None:
        definition = MetricDefinition(
            name=name,
            type=metric_type,
            description=description,
            labels=labels or [],
            alert_threshold=alert_threshold,
            alert_severity=alert_severity
        )
        self.metric_definitions[name] = definition
    
    def unregister_metric(self, name: str) -> bool:
        if name in self.metric_definitions:
            del self.metric_definitions[name]
            return True
        return False
    
    def record(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        description: str = "",
        timestamp: Optional[datetime] = None
    ) -> Metric:
        metric = Metric(
            name=name,
            type=self.metric_definitions.get(name, {}).get("type", MetricType.GAUGE),
            value=value,
            labels=labels or {},
            timestamp=timestamp or datetime.utcnow(),
            description=description or self.metric_definitions.get(name, {}).get("description", "")
        )
        
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(metric)
            
            if len(self.metrics[name]) > 10000:
                self.metrics[name] = self.metrics[name][-5000:]
        
        self._check_threshold(name, value)
        return metric
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
        description: str = ""
    ) -> Metric:
        with self._lock:
            last_metric = None
            if name in self.metrics and self.metrics[name]:
                last_metric = self.metrics[name][-1]
            
            if last_metric:
                new_value = last_metric.value + value
            else:
                new_value = value
        
        return self.record(name, new_value, labels, description)
    
    def set(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        description: str = ""
    ) -> Metric:
        return self.record(name, value, labels, description)
    
    def observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        description: str = ""
    ) -> Metric:
        return self.record(name, value, labels, description)
    
    def _check_threshold(self, name: str, value: float) -> None:
        definition = self.metric_definitions.get(name)
        if not definition or definition.alert_threshold is None:
            return
        
        if value > definition.alert_threshold:
            from .alerts import AlertManager, AlertSeverity
            alert_manager = AlertManager()
            alert_manager.trigger(
                name=f"{name}_threshold_exceeded",
                component="metrics",
                description=f"Metric {name} exceeded threshold",
                severity=AlertSeverity(definition.alert_severity),
                metric=name,
                threshold=definition.alert_threshold,
                current_value=value
            )
    
    def get_metric(self, name: str, limit: Optional[int] = None) -> List[Metric]:
        with self._lock:
            metrics = self.metrics.get(name, [])
            if limit:
                return metrics[-limit:]
            return metrics.copy()
    
    def get_all_metrics(self) -> Dict[str, List[Metric]]:
        with self._lock:
            return {k: v.copy() for k, v in self.metrics.items()}
    
    def get_metric_stats(self, name: str) -> Dict[str, Any]:
        metrics = self.get_metric(name)
        if not metrics:
            return {
                "name": name,
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "sum": 0,
                "latest": None
            }
        
        values = [m.value for m in metrics]
        return {
            "name": name,
            "count": len(metrics),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "avg": sum(values) / len(values) if values else None,
            "sum": sum(values) if values else 0,
            "latest": metrics[-1].to_dict() if metrics else None
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        return {name: self.get_metric_stats(name) for name in self.metrics.keys()}
    
    def clear_metric(self, name: str) -> int:
        with self._lock:
            if name in self.metrics:
                count = len(self.metrics[name])
                self.metrics[name].clear()
                return count
        return 0
    
    def clear_all(self) -> int:
        with self._lock:
            total = sum(len(v) for v in self.metrics.values())
            self.metrics.clear()
            return total
    
    def query_metrics(
        self,
        name_pattern: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Metric]:
        results = []
        for name, metrics in self.metrics.items():
            if name_pattern and name_pattern not in name:
                continue
            for metric in metrics:
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                if labels:
                    match = all(metric.labels.get(k) == v for k, v in labels.items())
                    if not match:
                        continue
                results.append(metric)
        return results
