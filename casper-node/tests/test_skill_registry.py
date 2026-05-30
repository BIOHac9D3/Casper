import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry.skills import SkillRegistry
from core.schemas.skill import Skill, SkillDomain, SkillInput, SkillTrigger


def test_registry_initialization():
    registry = SkillRegistry()
    assert registry.skills == {}
    assert registry.sources == {}


def test_register_and_get_skill():
    registry = SkillRegistry()
    skill = Skill(id="test_skill", name="Test Skill", domain=SkillDomain.WEB)
    registry.register(skill, "test_source")
    assert registry.get("test_skill") == skill
    assert registry.sources["test_skill"] == "test_source"


def test_list_all():
    registry = SkillRegistry()
    skill1 = Skill(id="skill1", name="Skill 1", domain=SkillDomain.WEB)
    skill2 = Skill(id="skill2", name="Skill 2", domain=SkillDomain.DATA)
    registry.register(skill1)
    registry.register(skill2)
    all_skills = registry.list_all()
    assert len(all_skills) == 2


def test_list_by_domain():
    registry = SkillRegistry()
    skill1 = Skill(id="skill1", name="Skill 1", domain=SkillDomain.WEB)
    skill2 = Skill(id="skill2", name="Skill 2", domain=SkillDomain.WEB)
    skill3 = Skill(id="skill3", name="Skill 3", domain=SkillDomain.DATA)
    registry.register(skill1)
    registry.register(skill2)
    registry.register(skill3)
    web_skills = registry.list_by_domain(SkillDomain.WEB)
    assert len(web_skills) == 2


def test_search_by_trigger():
    registry = SkillRegistry()
    skill1 = Skill(id="skill1", name="Skill 1", domain=SkillDomain.WEB,
                   triggers=[SkillTrigger(phrase="create web app")])
    skill2 = Skill(id="skill2", name="Skill 2", domain=SkillDomain.DATA,
                   triggers=[SkillTrigger(phrase="analyze data")])
    registry.register(skill1)
    registry.register(skill2)
    results = registry.search_by_trigger("create web app")
    assert len(results) == 1
    assert results[0] == skill1


def test_unregister_skill():
    registry = SkillRegistry()
    skill = Skill(id="test_skill", name="Test Skill", domain=SkillDomain.WEB)
    registry.register(skill)
    assert registry.unregister("test_skill") is True
    assert registry.get("test_skill") is None


def test_clear():
    registry = SkillRegistry()
    skill = Skill(id="test_skill", name="Test Skill", domain=SkillDomain.WEB)
    registry.register(skill)
    registry.clear()
    assert registry.skills == {}


def test_get_stats():
    registry = SkillRegistry()
    skill1 = Skill(id="skill1", name="Skill 1", domain=SkillDomain.WEB, enabled=True)
    skill2 = Skill(id="skill2", name="Skill 2", domain=SkillDomain.DATA, enabled=False)
    registry.register(skill1)
    registry.register(skill2)
    stats = registry.get_stats()
    assert stats["total_skills"] == 2
    assert stats["enabled_skills"] == 1
    assert stats["disabled_skills"] == 1