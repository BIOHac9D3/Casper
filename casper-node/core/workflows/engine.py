from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
import time

from core.registry.skills import SkillRegistry
from core.registry.workflows import WorkflowRegistry
from core.schemas.workflow import Workflow, WorkflowStep, StepStatus, WorkflowStatus
from agents.skill_adapter import SkillAgent


class WorkflowExecutionError(Exception):
    def __init__(self, message: str, step_id: str, workflow_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.step_id = step_id
        self.workflow_id = workflow_id
        self.details = details or {}


class WorkflowEngine:
    def __init__(self, skill_registry: SkillRegistry, workflow_registry: Optional[WorkflowRegistry] = None):
        self.skill_registry = skill_registry
        self.workflow_registry = workflow_registry or WorkflowRegistry()
        self.skill_agent = SkillAgent(skill_registry, interactive=False)
        self._execution_context: Dict[str, Any] = {}
    
    def execute_workflow(
        self,
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        workflow = self.workflow_registry.get(workflow_id)
        if not workflow:
            return {
                "status": "error",
                "message": f"Workflow '{workflow_id}' not found",
                "workflow_id": workflow_id
            }
        if not workflow.enabled:
            return {
                "status": "error",
                "message": f"Workflow '{workflow_id}' is disabled",
                "workflow_id": workflow_id
            }
        start_time = time.time()
        execution_id = f"{workflow_id}-{int(start_time * 1000)}"
        
        self._execution_context[execution_id] = {
            "workflow_id": workflow_id,
            "start_time": start_time,
            "inputs": inputs or {},
            "step_results": {},
            "step_statuses": {},
            "current_step": None,
            "completed_steps": [],
            "failed_steps": [],
            "skipped_steps": []
        }
        
        try:
            step_results = self._execute_steps(workflow, inputs or {}, execution_id, timeout)
            execution_time = time.time() - start_time
            
            return {
                "status": "completed",
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "execution_time": execution_time,
                "steps_completed": len(step_results),
                "step_results": step_results,
                "inputs": inputs,
                "timestamp": start_time
            }
        except WorkflowExecutionError as e:
            return {
                "status": "failed",
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "error": str(e),
                "failed_step": e.step_id,
                "details": e.details,
                "step_results": self._execution_context[execution_id].get("step_results", {}),
                "completed_steps": self._execution_context[execution_id].get("completed_steps", []),
                "failed_steps": self._execution_context[execution_id].get("failed_steps", [e.step_id])
            }
        except Exception as e:
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "error": str(e),
                "step_results": self._execution_context[execution_id].get("step_results", {})
            }
        finally:
            if execution_id in self._execution_context:
                del self._execution_context[execution_id]
    
    def _execute_steps(
        self,
        workflow: Workflow,
        inputs: Dict[str, Any],
        execution_id: str,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        ctx = self._execution_context[execution_id]
        sorted_steps = sorted(workflow.steps, key=lambda s: s.position)
        results = []
        
        for step in sorted_steps:
            if timeout and (time.time() - ctx["start_time"]) > timeout:
                raise WorkflowExecutionError(
                    "Workflow execution timed out",
                    step_id=step.id,
                    workflow_id=workflow.id,
                    details={"elapsed_time": time.time() - ctx["start_time"]}
                )
            
            if not self._should_execute_step(step, ctx):
                ctx["skipped_steps"].append(step.id)
                ctx["step_statuses"][step.id] = StepStatus.SKIPPED.value
                continue
            
            ctx["current_step"] = step.id
            try:
                result = self._execute_step(step, inputs, ctx, execution_id)
                results.append(result)
                ctx["step_results"][step.id] = result
                ctx["completed_steps"].append(step.id)
                ctx["step_statuses"][step.id] = StepStatus.COMPLETED.value
                
                if workflow.retry_policy == "continue" and result.get("status") == "error":
                    ctx["failed_steps"].append(step.id)
                    ctx["step_statuses"][step.id] = StepStatus.FAILED.value
                    if workflow.retry_policy == "fail_on_error":
                        raise WorkflowExecutionError(
                            f"Step '{step.id}' failed and retry policy is fail_on_error",
                            step_id=step.id,
                            workflow_id=workflow.id,
                            details=result
                        )
            except Exception as e:
                ctx["failed_steps"].append(step.id)
                ctx["step_statuses"][step.id] = StepStatus.FAILED.value
                if workflow.retry_policy == "fail_on_error":
                    raise WorkflowExecutionError(
                        f"Step '{step.id}' failed: {str(e)}",
                        step_id=step.id,
                        workflow_id=workflow.id,
                        details={"error": str(e)}
                    )
        
        return results
    
    def _should_execute_step(self, step: WorkflowStep, ctx: Dict[str, Any]) -> bool:
        if not step.required:
            return True
        for dep in step.depends_on:
            if dep not in ctx["completed_steps"] and dep not in ctx["skipped_steps"]:
                return False
        return True
    
    def _execute_step(
        self,
        step: WorkflowStep,
        workflow_inputs: Dict[str, Any],
        ctx: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        skill = self.skill_registry.get(step.skill_id)
        if not skill:
            return {
                "status": "error",
                "step_id": step.id,
                "skill_id": step.skill_id,
                "message": f"Skill '{step.skill_id}' not found"
            }
        if not skill.enabled:
            return {
                "status": "error",
                "step_id": step.id,
                "skill_id": step.skill_id,
                "message": f"Skill '{step.skill_id}' is disabled"
            }
        
        merged_inputs = {**workflow_inputs, **step.inputs}
        for mapping in ctx.get("workflow").output_mappings:
            if mapping.target_step == step.id:
                source_result = ctx["step_results"].get(mapping.source_step, {})
                if source_result.get("status") == "ok":
                    if mapping.source_output in source_result:
                        merged_inputs[mapping.target_input] = source_result[mapping.source_output]
        
        try:
            result = self.skill_agent.generate(
                prompt=step.description or f"Execute {step.name}",
                model=None,
                use_skills=True,
                **merged_inputs
            )
            return {
                **result,
                "step_id": step.id,
                "skill_id": step.skill_id,
                "status": result.get("status", "ok"),
                "execution_time": result.get("execution_time", 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "step_id": step.id,
                "skill_id": step.skill_id,
                "message": str(e)
            }
    
    def execute_single_skill(
        self,
        skill_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.skill_agent.generate(
            prompt=f"Execute skill {skill_id}",
            model=model,
            use_skills=True,
            **{"skill_id": skill_id, **(inputs or {})}
        )
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        if execution_id not in self._execution_context:
            return None
        ctx = self._execution_context[execution_id]
        workflow = self.workflow_registry.get(ctx["workflow_id"])
        if not workflow:
            return None
        
        return {
            "execution_id": execution_id,
            "workflow_id": ctx["workflow_id"],
            "workflow_name": workflow.name,
            "start_time": ctx["start_time"],
            "elapsed_time": time.time() - ctx["start_time"],
            "current_step": ctx["current_step"],
            "completed_steps": ctx["completed_steps"],
            "failed_steps": ctx["failed_steps"],
            "skipped_steps": ctx["skipped_steps"],
            "step_statuses": ctx["step_statuses"],
            "total_steps": len(workflow.steps)
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        workflows = self.workflow_registry.list_all()
        return [
            {"id": wf.id, "name": wf.name, "description": wf.description, "enabled": wf.enabled, "status": wf.status.value}
            for wf in workflows
        ]
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        workflow = self.workflow_registry.get(workflow_id)
        if not workflow:
            return None
        return workflow.to_dict()
    
    @contextmanager
    def workflow_context(self, workflow_id: str):
        workflow = self.workflow_registry.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found")
        original_status = workflow.status
        try:
            workflow.status = WorkflowStatus.RUNNING
            yield workflow
        finally:
            workflow.status = original_status
