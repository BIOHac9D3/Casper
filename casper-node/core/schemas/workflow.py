from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from .skill import Skill, SkillDomain


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class OutputMapping(BaseModel):
    source_step: str = Field(..., description="ID of the step that produces the output")
    source_output: str = Field(..., description="Name of the output field from the source step")
    target_step: str = Field(..., description="ID of the step that consumes the output")
    target_input: str = Field(..., description="Name of the input parameter in the target step")


class WorkflowStep(BaseModel):
    id: str = Field(..., description="Unique identifier for this step")
    skill_id: str = Field(..., description="ID of the skill to execute")
    name: str = Field(default="", description="Human-readable name for this step")
    description: str = Field(default="", description="Description of what this step does")
    position: int = Field(default=0, description="Execution order position")
    required: bool = Field(default=True, description="Whether this step is required")
    timeout: Optional[int] = Field(default=None, description="Timeout in seconds for this step")
    retry_count: int = Field(default=0, ge=0, description="Number of retries on failure")
    condition: Optional[str] = Field(default=None, description="Condition for executing this step (Python expression)")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Static inputs for this step")
    depends_on: List[str] = Field(default_factory=list, description="List of step IDs this step depends on")


class Workflow(BaseModel):
    id: str = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Human-readable name of the workflow")
    description: str = Field(default="", description="Detailed description of the workflow")
    domain: SkillDomain = Field(default=SkillDomain.AUTOMATION, description="Domain of the workflow")
    version: str = Field(default="1.0.0", description="Version of the workflow")
    author: Optional[str] = Field(default=None, description="Author of the workflow")
    enabled: bool = Field(default=True, description="Whether the workflow is enabled")
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT, description="Current status of the workflow")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization and filtering")
    steps: List[WorkflowStep] = Field(default_factory=list, description="List of steps in the workflow")
    output_mappings: List[OutputMapping] = Field(default_factory=list, description="Mappings between step outputs and inputs")
    timeout: Optional[int] = Field(default=None, description="Total workflow timeout in seconds")
    retry_policy: str = Field(default="fail_on_error", description="Retry policy: fail_on_error, continue, skip")

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "id": "data_analysis_pipeline",
                    "name": "Data Analysis Pipeline",
                    "description": "A workflow that loads data, cleans it, analyzes it, and generates a report",
                    "domain": "data",
                    "steps": [
                        {"id": "load_data", "skill_id": "load_csv", "position": 0},
                        {"id": "clean_data", "skill_id": "clean_dataset", "position": 1, "depends_on": ["load_data"]},
                        {"id": "analyze_data", "skill_id": "statistical_analysis", "position": 2, "depends_on": ["clean_data"]},
                        {"id": "generate_report", "skill_id": "generate_markdown_report", "position": 3, "depends_on": ["analyze_data"]}
                    ],
                    "output_mappings": [
                        {"source_step": "load_data", "source_output": "data", "target_step": "clean_data", "target_input": "dataset"},
                        {"source_step": "clean_data", "source_output": "cleaned_data", "target_step": "analyze_data", "target_input": "data"},
                        {"source_step": "analyze_data", "source_output": "results", "target_step": "generate_report", "target_input": "analysis"}
                    ]
                }
            ]
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain.value,
            "version": self.version,
            "author": self.author,
            "enabled": self.enabled,
            "status": self.status.value,
            "tags": self.tags,
            "steps": [s.dict() for s in self.steps],
            "output_mappings": [m.dict() for m in self.output_mappings],
            "timeout": self.timeout,
            "retry_policy": self.retry_policy
        }

    def get_step_order(self) -> List[str]:
        sorted_steps = sorted(self.steps, key=lambda s: s.position)
        return [s.id for s in sorted_steps]

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def validate(self) -> List[str]:
        errors = []
        step_ids = [s.id for s in self.steps]
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(f"Step {step.id} depends on non-existent step {dep}")
        for mapping in self.output_mappings:
            if mapping.source_step not in step_ids:
                errors.append(f"Output mapping references non-existent source step {mapping.source_step}")
            if mapping.target_step not in step_ids:
                errors.append(f"Output mapping references non-existent target step {mapping.target_step}")
        return errors
