from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from core.schemas.workflow import Workflow, WorkflowStep, WorkflowStatus, StepStatus


class WorkflowRegistry:
    def __init__(self) -> None:
        self.workflows: Dict[str, Workflow] = {}
        self.index: Dict[str, Dict[str, List[str]]] = {
            "domain": {},
            "tag": {},
            "author": {},
            "status": {}
        }
    
    def register(self, workflow: Workflow, source: Optional[str] = None) -> None:
        if workflow.id in self.workflows:
            self.workflows[workflow.id] = workflow
        else:
            self.workflows[workflow.id] = workflow
        self._update_indexes(workflow)
    
    def _update_indexes(self, workflow: Workflow) -> None:
        domain_key = workflow.domain.value
        if domain_key not in self.index["domain"]:
            self.index["domain"][domain_key] = []
        if workflow.id not in self.index["domain"][domain_key]:
            self.index["domain"][domain_key].append(workflow.id)
        for tag in workflow.tags:
            tag_key = tag.lower()
            if tag_key not in self.index["tag"]:
                self.index["tag"][tag_key] = []
            if workflow.id not in self.index["tag"][tag_key]:
                self.index["tag"][tag_key].append(workflow.id)
        if workflow.author:
            author_key = workflow.author.lower()
            if author_key not in self.index["author"]:
                self.index["author"][author_key] = []
            if workflow.id not in self.index["author"][author_key]:
                self.index["author"][author_key].append(workflow.id)
        status_key = workflow.status.value
        if status_key not in self.index["status"]:
            self.index["status"][status_key] = []
        if workflow.id not in self.index["status"][status_key]:
            self.index["status"][status_key].append(workflow.id)
    
    def get(self, workflow_id: str) -> Optional[Workflow]:
        return self.workflows.get(workflow_id)
    
    def list_all(self) -> List[Workflow]:
        return list(self.workflows.values())
    
    def list_by_domain(self, domain: str) -> List[Workflow]:
        workflow_ids = self.index["domain"].get(domain, [])
        return [self.workflows[wf_id] for wf_id in workflow_ids]
    
    def list_by_tag(self, tag: str) -> List[Workflow]:
        tag_key = tag.lower()
        workflow_ids = self.index["tag"].get(tag_key, [])
        return [self.workflows[wf_id] for wf_id in workflow_ids]
    
    def list_by_status(self, status: WorkflowStatus) -> List[Workflow]:
        status_key = status.value
        workflow_ids = self.index["status"].get(status_key, [])
        return [self.workflows[wf_id] for wf_id in workflow_ids]
    
    def unregister(self, workflow_id: str) -> bool:
        if workflow_id not in self.workflows:
            return False
        workflow = self.workflows[workflow_id]
        del self.workflows[workflow_id]
        self._remove_from_indexes(workflow)
        return True
    
    def _remove_from_indexes(self, workflow: Workflow) -> None:
        domain_key = workflow.domain.value
        if domain_key in self.index["domain"]:
            if workflow.id in self.index["domain"][domain_key]:
                self.index["domain"][domain_key].remove(workflow.id)
        for tag in workflow.tags:
            tag_key = tag.lower()
            if tag_key in self.index["tag"]:
                if workflow.id in self.index["tag"][tag_key]:
                    self.index["tag"][tag_key].remove(workflow.id)
        if workflow.author:
            author_key = workflow.author.lower()
            if author_key in self.index["author"]:
                if workflow.id in self.index["author"][author_key]:
                    self.index["author"][author_key].remove(workflow.id)
        status_key = workflow.status.value
        if status_key in self.index["status"]:
            if workflow.id in self.index["status"][status_key]:
                self.index["status"][status_key].remove(workflow.id)
    
    def clear(self) -> None:
        self.workflows.clear()
        self.index = {
            "domain": {},
            "tag": {},
            "author": {},
            "status": {}
        }
    
    def load_from_yaml(self, config_path: str | Path) -> None:
        path = Path(config_path) if isinstance(config_path, str) else config_path
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        for workflow_config in config.get("workflows", []):
            workflow = Workflow(**workflow_config)
            self.register(workflow, "yaml")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_workflows": len(self.workflows),
            "enabled_workflows": sum(1 for w in self.workflows.values() if w.enabled),
            "disabled_workflows": sum(1 for w in self.workflows.values() if not w.enabled),
            "domains": {d: len(ids) for d, ids in self.index["domain"].items()},
            "tags": {t: len(ids) for t, ids in self.index["tag"].items()},
            "statuses": {s: len(ids) for s, ids in self.index["status"].items()}
        }
