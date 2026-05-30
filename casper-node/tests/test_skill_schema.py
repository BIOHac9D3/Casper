import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.schemas.skill import (
    Skill,
    SkillDomain,
    SkillInput,
    SkillTrigger,
    InputType
)


def test_skill_domain():
    assert SkillDomain.WEB.value == "web"
    assert SkillDomain.DATA.value == "data"
    assert SkillDomain("web") == SkillDomain.WEB


def test_input_type():
    assert InputType.STRING.value == "string"
    assert InputType.LIST.value == "list"
    assert InputType("string") == InputType.STRING


def test_skill_trigger():
    trigger = SkillTrigger(phrase="create web app", weight=1.5)
    assert trigger.phrase == "create web app"
    assert trigger.weight == 1.5


def test_skill_input():
    input_spec = SkillInput(
        name="app_name",
        type=InputType.STRING,
        prompt="Enter app name",
        required=True
    )
    assert input_spec.name == "app_name"
    assert input_spec.type == InputType.STRING


def test_skill_creation():
    skill = Skill(
        id="test_skill",
        name="Test Skill",
        domain=SkillDomain.WEB,
        description="A test skill",
        triggers=[SkillTrigger(phrase="test")],
        inputs=[SkillInput(name="input1", type=InputType.STRING, prompt="Input 1")],
        disallowed=["bad content"],
        enabled=True,
        priority=10
    )
    assert skill.id == "test_skill"
    assert skill.name == "Test Skill"
    assert skill.domain == SkillDomain.WEB


def test_skill_to_dict():
    skill = Skill(
        id="test_skill",
        name="Test Skill",
        domain=SkillDomain.WEB
    )
    result = skill.to_dict()
    assert result["id"] == "test_skill"
    assert result["domain"] == "web"


def test_skill_from_codex_config():
    config = {
        "name": "Codex Skill",
        "domain": "web",
        "description": "A skill from Codex",
        "triggers": ["create web app"],
        "inputs": [{"name": "app_name", "type": "string", "prompt": "Enter app name"}],
        "disallowed": ["illegal"]
    }
    skill = Skill.from_codex_config("codex_skill", config)
    assert skill.id == "codex_skill"
    assert skill.name == "Codex Skill"
    assert skill.domain == SkillDomain.WEB