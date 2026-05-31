from fastapi import APIRouter
from typing import Any, Dict, List, Optional
from core.registry.skills import SkillRegistry

router = APIRouter()
skill_registry = SkillRegistry()

@router.get("/api/advanced-skills/discover")
async def discover(domain: Optional[str] = None):
    skills = skill_registry.list_all()
    return [s.to_dict() for s in skills]

@router.get("/api/advanced-skills/search")
async def search(query: str):
    all_skills = skill_registry.list_all()
    results = [s for s in all_skills if query.lower() in s.id.lower()]
    return [s.to_dict() for s in results]
