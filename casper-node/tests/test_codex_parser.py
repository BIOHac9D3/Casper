import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.parsers.codex_parser import CodexParser
from core.schemas.skill import Skill, SkillDomain, InputType


def test_parser_initialization():
    parser = CodexParser("test.py")
    assert parser.file_path == Path("test.py")
    assert parser.skills_config == {}


def test_convert_single_skill():
    parser = CodexParser("test.py")
    config = {
        "name": "Test Skill",
        "domain": "web",
        "description": "Test description",
        "triggers": ["trigger1", "trigger2"],
        "inputs": [
            {"name": "input1", "type": "string", "prompt": "Prompt 1"},
            {"name": "input2", "type": "list", "prompt": "Prompt 2", "options": ["a", "b"]}
        ],
        "disallowed": ["bad1", "bad2"],
        "tags": ["tag1", "tag2"]
    }
    skill = parser._convert_single_skill("test_skill", config)
    assert skill.id == "test_skill"
    assert skill.name == "Test Skill"
    assert skill.domain == SkillDomain.WEB
    assert len(skill.triggers) == 2
    assert len(skill.inputs) == 2


def test_convert_inputs():
    parser = CodexParser("test.py")
    inputs_config = [
        {"name": "input1", "type": "string", "prompt": "Prompt 1"},
        {"name": "input2", "type": "number", "prompt": "Prompt 2"}
    ]
    inputs = parser._convert_inputs(inputs_config)
    assert len(inputs) == 2
    assert inputs[0].name == "input1"
    assert inputs[0].type == InputType.STRING


def test_convert_triggers():
    parser = CodexParser("test.py")
    triggers_config = ["trigger1", "trigger2"]
    triggers = parser._convert_triggers(triggers_config)
    assert len(triggers) == 2
    assert triggers[0].phrase == "trigger1"
    assert triggers[0].weight == 1.0