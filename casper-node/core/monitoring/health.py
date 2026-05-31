from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import time
import psutil

from core.schemas.monitoring import HealthStatus, SystemHealth, ComponentHealth


class HealthCheckError(Exception):
    def __init__(self, message: str, component: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.component = component
        self.details = details or {}


class HealthChecker:
    def __init__(self, start_time: Optional[float] = None) -> None:
        self.start_time = start_time or time.time()
        self.checks: Dict[str, Callable[[], ComponentHealth]] = {}
        self._register_default_checks()
    
    def _register_default_checks(self) -> None:
        self.register_check("system", self._check_system_health)
        self.register_check("memory", self._check_memory_health)
        self.register_check("cpu", self._check_cpu_health)
        self.register_check("disk", self._check_disk_health)
    
    def register_check(self, name: str, check_func: Callable[[], ComponentHealth]) -> None:
        self.checks[name] = check_func
    
    def unregister_check(self, name: str) -> None:
        if name in self.checks:
            del self.checks[name]
    
    def _check_system_health(self) -> ComponentHealth:
        try:
            uptime = time.time() - self.start_time
            return ComponentHealth(
                component="system",
                status=HealthStatus.HEALTHY,
                message="System operational",
                timestamp=datetime.utcnow(),
                latency_ms=None,
                details={"uptime_seconds": uptime}
            )
        except Exception as e:
            return ComponentHealth(
                component="system",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                timestamp=datetime.utcnow(),
                latency_ms=None
            )
    
    def _check_memory_health(self) -> ComponentHealth:
        try:
            mem = psutil.virtual_memory()
            usage_percent = mem.percent
            available_mb = mem.available / (1024 * 1024)
            
            if usage_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High memory usage: {usage_percent}%"
            elif usage_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"Elevated memory usage: {usage_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage: {usage_percent}%"
            
            return ComponentHealth(
                component="memory",
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                latency_ms=None,
                details={"usage_percent": usage_percent, "available_mb": available_mb}
            )
        except Exception as e:
            return ComponentHealth(
                component="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {e}",
                timestamp=datetime.utcnow(),
                latency_ms=None
            )
    
    def _check_cpu_health(self) -> ComponentHealth:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High CPU usage: {cpu_percent}%"
            elif cpu_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"Elevated CPU usage: {cpu_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage: {cpu_percent}%"
            
            return ComponentHealth(
                component="cpu",
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                latency_ms=None,
                details={"usage_percent": cpu_percent, "cpu_count": cpu_count}
            )
        except Exception as e:
            return ComponentHealth(
                component="cpu",
                status=HealthStatus.UNHEALTHY,
                message=f"CPU check failed: {e}",
                timestamp=datetime.utcnow(),
                latency_ms=None
            )
    
    def _check_disk_health(self) -> ComponentHealth:
        try:
            disk = psutil.disk_usage('/')
            usage_percent = disk.percent
            free_mb = disk.free / (1024 * 1024)
            
            if usage_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Low disk space: {usage_percent}% used"
            elif usage_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"Disk space getting low: {usage_percent}% used"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage: {usage_percent}%"
            
            return ComponentHealth(
                component="disk",
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                latency_ms=None,
                details={"usage_percent": usage_percent, "free_mb": free_mb}
            )
        except Exception as e:
            return ComponentHealth(
                component="disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {e}",
                timestamp=datetime.utcnow(),
                latency_ms=None
            )
    
    def check_health(self) -> SystemHealth:
        components = []
        worst_status = HealthStatus.HEALTHY
        
        for name, check_func in self.checks.items():
            try:
                component_health = check_func()
                components.append(component_health)
                if component_health.status.value > worst_status.value:
                    worst_status = component_health.status
            except Exception as e:
                components.append(ComponentHealth(
                    component=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    timestamp=datetime.utcnow()
                ))
                worst_status = HealthStatus.UNHEALTHY
        
        uptime = time.time() - self.start_time
        
        return SystemHealth(
            status=worst_status,
            timestamp=datetime.utcnow(),
            components=components,
            version="1.0.0",
            uptime_seconds=uptime
        )
    
    def check_component(self, component: str) -> Optional[ComponentHealth]:
        if component not in self.checks:
            return None
        return self.checks[component]()
    
    def get_uptime(self) -> float:
        return time.time() - self.start_time
