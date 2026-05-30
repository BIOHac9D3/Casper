from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SkillDomain(str, Enum):
    """Domains/categories for skills."""
    WEB = "web"
    DATA = "data"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"
    DEVELOPMENT = "development"
    SECURITY = "security"
    OTHER = "other"


class InputType(str, Enum):
    """Types of skill inputs."""
    STRING = "string"
    LIST = "list"
    FILE = "file"
    NUMBER = "number"
    BOOLEAN = "boolean"


class SkillTrigger(BaseModel):
    """A trigger phrase that activates a skill."""
    phrase: str = Field(..., description="The trigger phrase to match against user prompts")
    weight: float = Field(default=1.0, ge=0.0, description="Matching weight for this trigger")


class SkillInput(BaseModel):
    """Definition of an input parameter for a skill."""
    name: str = Field(..., description="Unique name of the input parameter")
    type: InputType = Field(..., description="Type of the input")
    prompt: str = Field(..., description="User-friendly prompt for this input")
    required: bool = Field(default=True, description="Whether this input is required")
    default: Optional[Any] = Field(default=None, description="Default value if not provided")
    options: Optional[List[str]] = Field(default=None, description="Allowed values for list type inputs")


class Skill(BaseModel):
    """Definition of a skill."""
    id: str = Field(..., description="Unique identifier for the skill")
    name: str = Field(..., description="Human-readable name of the skill")
    domain: SkillDomain = Field(..., description="Category/domain of the skill")
    description: str = Field(default="", description="Detailed description of what the skill does")
    triggers: List[SkillTrigger] = Field(default_factory=list, description="Trigger phrases that activate this skill")
    inputs: List[SkillInput] = Field(default_factory=list, description="Input parameters for the skill")
    disallowed: List[str] = Field(default_factory=list, description="Content that is not allowed for this skill")
    enabled: bool = Field(default=True, description="Whether the skill is enabled")
    priority: int = Field(default=0, description="Priority for skill selection (higher = more priority)")
    version: str = Field(default="1.0.0", description="Version of the skill")
    author: Optional[str] = Field(default=None, description="Author of the skill")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization and filtering")
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "id": "example_skill",
                    "name": "Example Skill",
                    "domain": "web",
                    "description": "An example skill that demonstrates the schema",
                    "triggers": [{"phrase": "create web app", "weight": 1.0}],
                    "inputs": [{"name": "app_name", "type": "string", "prompt": "Enter app name", "required": True}],
                    "disallowed": ["illegal", "fraud"],
                    "enabled": True,
                    "priority": 10
                }
            ]
        }


    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary, handling enums properly."""
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain.value,
            "description": self.description,
            "triggers": [{"phrase": t.phrase, "weight": t.weight} for t in self.triggers],
            "inputs": [
                {
                    "name": i.name,
                    "type": i.type.value,
                    "prompt": i.prompt,
                    "required": i.required,
                    "default": i.default,
                    "options": i.options
                }
                for i in self.inputs
            ],
            "disallowed": self.disallowed,
            "enabled": self.enabled,
            "priority": self.priority,
            "version": self.version,
            "author": self.author,
            "tags": self.tags
        }
    
    @classmethod
    def from_codex_config(cls, skill_id: str, config: Dict[str, Any]) -> Skill:
        """
        Create a Skill from Codex-style configuration dictionary.
        
        Args:
            skill_id: The skill identifier
            config: Codex-style configuration dictionary
            
        Returns:
            Skill: A new Skill instance
        """
        inputs = []
        for input_config in config.get("inputs", []):
            input_type = input_config.get("type", "string")
            inputs.append(SkillInput(
                name=input_config.get("name", ""),
                type=InputType(input_type),
                prompt=input_config.get("prompt", ""),
                required=input_config.get("required", True),
                default=input_config.get("default"),
                options=input_config.get("options")
            ))
        
        triggers = []
        for trigger_phrase in config.get("triggers", []):
            triggers.append(SkillTrigger(phrase=trigger_phrase))
        
        domain = config.get("domain", "other")
        try:
            domain_enum = SkillDomain(domain)
        except ValueError:
            domain_enum = SkillDomain.OTHER
        
        return cls(
            id=skill_id,
            name=config.get("name", skill_id),
            domain=domain_enum,
            description=config.get("description", ""),
            triggers=triggers,
            inputs=inputs,
            disallowed=config.get("disallowed", []),
            enabled=True,
            priority=0,
            tags=config.get("tags", [])
        )
