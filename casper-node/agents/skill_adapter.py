from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.schemas.skill import Skill, SkillInput
from core.registry.skills import SkillRegistry
from agents.base_agent import BaseAgent


class InputCollector:
    def __init__(self, interactive: bool = True):
        self.interactive = interactive

    def collect(self, inputs: List[SkillInput], prompt: str, **kwargs) -> Dict[str, Any]:
        collected = {}
        for input_spec in inputs:
            if input_spec.name in kwargs:
                collected[input_spec.name] = kwargs[input_spec.name]
                continue
            if input_spec.default is not None:
                collected[input_spec.name] = input_spec.default
                continue
            if input_spec.required and self.interactive:
                value = self._prompt_user(input_spec)
                collected[input_spec.name] = value
        return collected

    def _prompt_user(self, input_spec: SkillInput) -> Any:
        print(f"
{input_spec.prompt}")
        if input_spec.options:
            print(f"Options: {', '.join(input_spec.options)}")
            for i, option in enumerate(input_spec.options, 1):
                print(f"{i}. {option}")
            choice = input("Select option number: ")
            try:
                index = int(choice) - 1
                return input_spec.options[index]
            except (ValueError, IndexError):
                print("Invalid selection. Using first option.")
                return input_spec.options[0]
        else:
            if input_spec.type.value == "boolean":
                choice = input("Enter yes/no: ").lower()
                return choice in ("yes", "y", "true", "1")
            elif input_spec.type.value == "file":
                return input("Enter file path: ")
            elif input_spec.type.value == "number":
                try:
                    return float(input("Enter value: "))
                except ValueError:
                    return 0
            else:
                return input("Enter value: ")


class SkillAgent(BaseAgent):
    def __init__(self, registry: SkillRegistry, interactive: bool = True):
        super().__init__()
        self.registry = registry
        self.input_collector = InputCollector(interactive=interactive)

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        matched_skills = self.registry.search_by_trigger(prompt)
        if not matched_skills:
            return super().generate(prompt, model, **kwargs)
        best_skill = self._select_best_skill(matched_skills, prompt)
        inputs = self.input_collector.collect(best_skill.inputs, prompt, **kwargs)
        if not self._validate_inputs(inputs, best_skill.disallowed):
            return {"status": "error", "message": "Input validation failed", "skill_id": best_skill.id}
        return self._execute_skill(best_skill, inputs, model)

    def _select_best_skill(self, skills: List[Skill], prompt: str) -> Skill:
        scored_skills = []
        for skill in skills:
            score = skill.priority * 10
            for trigger in skill.triggers:
                if trigger.phrase.lower() in prompt.lower():
                    score += trigger.weight * 100
            scored_skills.append((score, skill))
        scored_skills.sort(key=lambda x: x[0], reverse=True)
        return scored_skills[0][1]

    def _validate_inputs(self, inputs: Dict[str, Any], disallowed: List[str]) -> bool:
        for key, value in inputs.items():
            value_str = str(value).lower()
            for disallowed_phrase in disallowed:
                if disallowed_phrase.lower() in value_str:
                    return False
        return True

    def _execute_skill(self, skill: Skill, inputs: Dict[str, Any], model: Optional[str]) -> Dict[str, Any]:
        prompt_template = self._get_skill_prompt_template(skill)
        try:
            formatted_prompt = prompt_template.format(**inputs)
        except KeyError:
            formatted_prompt = prompt_template
        result = super().generate(formatted_prompt, model)
        return self._post_process_result(result, skill, inputs)

    def _get_skill_prompt_template(self, skill: Skill) -> str:
        input_descriptions = "
".join(f"- {i.name}: {i.prompt}" for i in skill.inputs)
        return f"You are an expert assistant specialized in {skill.domain.value}.
Your task: {skill.name}

{skill.description}

Input parameters:
{input_descriptions}

Please provide a comprehensive response based on the inputs provided.
"

    def _post_process_result(self, result: Dict[str, Any], skill: Skill, inputs: Dict[str, Any]) -> Dict[str, Any]:
        result["skill"] = {"id": skill.id, "name": skill.name, "domain": skill.domain.value}
        result["inputs"] = inputs
        return result

    def list_skills(self) -> List[Dict[str, Any]]:
        skills = self.registry.list_all()
        return [skill.to_dict() for skill in skills]

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        skill = self.registry.get(skill_id)
        if skill:
            return skill.to_dict()
        return None

    def enable_skill(self, skill_id: str) -> bool:
        skill = self.registry.get(skill_id)
        if skill:
            skill.enabled = True
            return True
        return False

    def disable_skill(self, skill_id: str) -> bool:
        skill = self.registry.get(skill_id)
        if skill:
            skill.enabled = False
            return True
        return False