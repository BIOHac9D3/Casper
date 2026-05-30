from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.schemas.skill import Skill, SkillInput, SkillTrigger, SkillDomain, InputType


class CodexParser:
    """Parser for Codex agent_system.py skills configuration."""
    
    def __init__(self, file_path: str | Path) -> None:
        """
        Initialize the parser with the path to the Codex configuration file.
        
        Args:
            file_path: Path to the Python file containing SKILLS_CONFIG
        """
        self.file_path = Path(file_path) if isinstance(file_path, str) else file_path
        self.skills_config: Dict[str, Any] = {}

    def parse(self) -> List[Skill]:
        """
        Parse the Codex skills configuration and return a list of Skill objects.
        
        Returns:
            List[Skill]: Parsed skills from the configuration
        """
        self._load_config()
        return self._convert_to_skills()
    
    def _load_config(self) -> None:
        """Load the SKILLS_CONFIG dictionary from the Python file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.file_path}")
        
        spec = importlib.util.spec_from_file_location("codex_config", self.file_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load module from {self.file_path}")
        
        module = importlib.util.module_from_spec(spec)
        if module is None:
            raise ValueError(f"Cannot create module from spec for {self.file_path}")
        
        spec.loader.exec_module(module)
        
        if not hasattr(module, 'SKILLS_CONFIG'):
            raise ValueError(f"No SKILLS_CONFIG found in {self.file_path}")
        
        self.skills_config = module.SKILLS_CONFIG

    def _convert_to_skills(self) -> List[Skill]:
        """
        Convert the Codex skills dictionary to a list of Skill objects.
        
        Returns:
            List[Skill]: Converted skills
        """
        skills = []
        
        for skill_id, config in self.skills_config.items():
            try:
                skill = self._convert_single_skill(skill_id, config)
                skills.append(skill)
            except Exception as e:
                print(f"Warning: Failed to parse skill {skill_id}: {e}")
                continue
        
        return skills
    
    def _convert_single_skill(self, skill_id: str, config: Dict[str, Any]) -> Skill:
        """
        Convert a single Codex skill configuration to a Skill object.
        
        Args:
            skill_id: The skill identifier
            config: The skill configuration dictionary
            
        Returns:
            Skill: The converted skill
        """
        # Convert inputs
        inputs = self._convert_inputs(config.get("inputs", []))
        
        # Convert triggers
        triggers = self._convert_triggers(config.get("triggers", []))
        
        # Get domain
        domain_str = config.get("domain", "other")
        try:
            domain = SkillDomain(domain_str)
        except ValueError:
            domain = SkillDomain.OTHER
        
        return Skill(
            id=skill_id,
            name=config.get("name", skill_id),
            domain=domain,
            description=config.get("description", ""),
            triggers=triggers,
            inputs=inputs,
            disallowed=config.get("disallowed", []),
            enabled=True,
            priority=0,
            version="1.0.0",
            author=None,
            tags=config.get("tags", [])
        )

    def _convert_inputs(self, inputs_config: List[Dict[str, Any]]) -> List[SkillInput]:
        """
        Convert Codex input configurations to SkillInput objects.
        
        Args:
            inputs_config: List of input configuration dictionaries
            
        Returns:
            List[SkillInput]: Converted skill inputs
        """
        inputs = []
        
        for input_config in inputs_config:
            try:
                input_type_str = input_config.get("type", "string")
                try:
                    input_type = InputType(input_type_str)
                except ValueError:
                    input_type = InputType.STRING
                
                skill_input = SkillInput(
                    name=input_config.get("name", ""),
                    type=input_type,
                    prompt=input_config.get("prompt", ""),
                    required=input_config.get("required", True),
                    default=input_config.get("default"),
                    options=input_config.get("options")
                )
                inputs.append(skill_input)
            except Exception as e:
                print(f"Warning: Failed to parse input {input_config.get('name', 'unknown')}: {e}")
                continue
        
        return inputs
    
    def _convert_triggers(self, triggers_config: List[str]) -> List[SkillTrigger]:
        """
        Convert Codex trigger strings to SkillTrigger objects.
        
        Args:
            triggers_config: List of trigger phrase strings
            
        Returns:
            List[SkillTrigger]: Converted skill triggers
        """
        triggers = []
        
        for trigger_phrase in triggers_config:
            try:
                trigger = SkillTrigger(phrase=trigger_phrase, weight=1.0)
                triggers.append(trigger)
            except Exception as e:
                print(f"Warning: Failed to parse trigger {trigger_phrase}: {e}")
                continue
        
        return triggers

    def parse_from_codex_repo(self, repo_path: str | Path) -> List[Skill]:
        """
        Parse skills directly from the Codex repository.
        
        This is a convenience method that looks for agent_system.py in the Codex repo
        and parses it.
        
        Args:
            repo_path: Path to the Codex repository
            
        Returns:
            List[Skill]: Parsed skills
        """
        codex_path = Path(repo_path) / "agent_system.py"
        if not codex_path.exists():
            raise FileNotFoundError(f"agent_system.py not found in Codex repo: {repo_path}")
        
        self.file_path = codex_path
        return self.parse()
    
    @classmethod
    def parse_file(cls, file_path: str | Path) -> List[Skill]:
        """
        Convenience class method to parse a single file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            List[Skill]: Parsed skills
        """
        parser = cls(file_path)
        return parser.parse()
