from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict
import threading
import logging

from core.schemas.monitoring import SkillUsageStats, AnalyticsSummary
from core.registry.skills import SkillRegistry

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    def __init__(self, skill_registry: Optional[SkillRegistry] = None) -> None:
        self.skill_registry = skill_registry
        self.skill_stats: Dict[str, SkillUsageStats] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._max_history = 10000
    
    def record_execution(
        self,
        skill_id: str,
        execution_time: float,
        success: bool,
        error_type: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> None:
        with self._lock:
            if skill_id not in self.skill_stats:
                self.skill_stats[skill_id] = SkillUsageStats(skill_id=skill_id)
            
            stats = self.skill_stats[skill_id]
            stats.total_executions += 1
            stats.total_execution_time += execution_time
            
            if success:
                stats.successful_executions += 1
                stats.last_success = datetime.utcnow()
            else:
                stats.failed_executions += 1
                stats.last_failure = datetime.utcnow()
                if error_type:
                    stats.error_rates[error_type] = stats.error_rates.get(error_type, 0) + 1
            
            stats.last_execution = datetime.utcnow()
            stats.avg_execution_time = (
                stats.total_execution_time / stats.total_executions
                if stats.total_executions > 0
                else 0.0
            )
            
            execution_record = {
                "skill_id": skill_id,
                "timestamp": datetime.utcnow(),
                "execution_time": execution_time,
                "success": success,
                "error_type": error_type,
                "model": model,
                "provider": provider
            }
            self.execution_history.append(execution_record)
            
            if len(self.execution_history) > self._max_history:
                self.execution_history = self.execution_history[-self._max_history // 2:]
    
    def get_skill_stats(self, skill_id: str) -> Optional[SkillUsageStats]:
        with self._lock:
            return self.skill_stats.get(skill_id)
    
    def get_all_skill_stats(self) -> Dict[str, SkillUsageStats]:
        with self._lock:
            return self.skill_stats.copy()
    
    def get_summary(self) -> AnalyticsSummary:
        with self._lock:
            total_skills = len(self.skill_stats)
            total_executions = sum(s.total_executions for s in self.skill_stats.values())
            successful_executions = sum(s.successful_executions for s in self.skill_stats.values())
            
            success_rate = (
                (successful_executions / total_executions * 100)
                if total_executions > 0
                else 0.0
            )
            
            total_time = sum(s.total_execution_time for s in self.skill_stats.values())
            avg_execution_time = (
                (total_time / total_executions)
                if total_executions > 0
                else 0.0
            )
            
            most_used = sorted(
                self.skill_stats.values(),
                key=lambda s: s.total_executions,
                reverse=True
            )[:10]
            
            most_used_list = [
                {
                    "skill_id": s.skill_id,
                    "total_executions": s.total_executions,
                    "success_rate": (
                        (s.successful_executions / s.total_executions * 100)
                        if s.total_executions > 0
                        else 0.0
                    ),
                    "avg_execution_time": s.avg_execution_time
                }
                for s in most_used
            ]
            
            recent_errors = []
            for record in reversed(self.execution_history[-100:]):
                if not record["success"]:
                    recent_errors.append({
                        "skill_id": record["skill_id"],
                        "timestamp": record["timestamp"].isoformat(),
                        "error_type": record["error_type"],
                        "execution_time": record["execution_time"]
                    })
                    if len(recent_errors) >= 10:
                        break
            
            execution_trends = self._calculate_trends()
            
            return AnalyticsSummary(
                total_skills=total_skills,
                total_executions=total_executions,
                success_rate=success_rate,
                avg_execution_time=avg_execution_time,
                most_used_skills=most_used_list,
                recent_errors=recent_errors,
                execution_trends=execution_trends
            )
    
    def _calculate_trends(self) -> Dict[str, int]:
        trends: Dict[str, int] = {}
        now = datetime.utcnow()
        
        for period_name, delta in [
            ("last_hour", timedelta(hours=1)),
            ("last_24h", timedelta(hours=24)),
            ("last_7d", timedelta(days=7)),
            ("last_30d", timedelta(days=30))
        ]:
            start_time = now - delta
            count = sum(
                1 for r in self.execution_history
                if r["timestamp"] >= start_time
            )
            trends[period_name] = count
        
        return trends
    
    def get_skill_execution_trend(self, skill_id: str, days: int = 7) -> List[Dict[str, Any]]:
        with self._lock:
            stats = self.skill_stats.get(skill_id)
            if not stats:
                return []
            
            trend = []
            now = datetime.utcnow()
            for i in range(days):
                day_start = now - timedelta(days=days - i)
                day_end = day_start + timedelta(days=1)
                
                count = sum(
                    1 for r in self.execution_history
                    if (r["skill_id"] == skill_id and 
                        day_start <= r["timestamp"] < day_end)
                )
                
                trend.append({
                    "date": day_start.strftime("%Y-%m-%d"),
                    "count": count
                })
            
            return trend
    
    def get_error_analysis(self) -> Dict[str, Any]:
        with self._lock:
            error_counts: Dict[str, int] = defaultdict(int)
            error_by_skill: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            
            for record in self.execution_history:
                if not record["success"] and record["error_type"]:
                    error_counts[record["error_type"]] += 1
                    error_by_skill[record["skill_id"]][record["error_type"]] += 1
            
            return {
                "total_errors": len([r for r in self.execution_history if not r["success"]]),
                "error_counts": dict(error_counts),
                "error_by_skill": {k: dict(v) for k, v in error_by_skill.items()}
            }
    
    def clear_skill_stats(self, skill_id: str) -> bool:
        with self._lock:
            if skill_id in self.skill_stats:
                del self.skill_stats[skill_id]
                return True
        return False
    
    def clear_all(self) -> int:
        with self._lock:
            total = len(self.skill_stats) + len(self.execution_history)
            self.skill_stats.clear()
            self.execution_history.clear()
            return total
    
    def set_skill_registry(self, skill_registry: SkillRegistry) -> None:
        self.skill_registry = skill_registry
