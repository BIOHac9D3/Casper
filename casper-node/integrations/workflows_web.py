from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from core.registry.workflows import WorkflowRegistry
from core.workflows.engine import WorkflowEngine
from core.schemas.workflow import Workflow

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

workflow_registry = WorkflowRegistry()
workflow_engine = WorkflowEngine(None, workflow_registry)


class WorkflowRequest(BaseModel):
    inputs: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None


@router.get("/")
async def list_workflows() -> List[Dict[str, Any]]:
    workflows = workflow_registry.list_all()
    return [
        {"id": w.id, "name": w.name, "enabled": w.enabled, "steps": len(w.steps)}
        for w in workflows
    ]


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    return workflow.to_dict()


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: WorkflowRequest) -> Dict[str, Any]:
    result = workflow_engine.execute_workflow(workflow_id, request.inputs, request.timeout)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Execution failed"))
    return result


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    return workflow_registry.get_stats()
