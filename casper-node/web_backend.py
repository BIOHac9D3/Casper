from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from core.environment import detect_environment, EnvironmentInfo
from core.registry.skills import SkillRegistry
from core.parsers.codex_parser import CodexParser
from agents.skill_adapter import SkillAgent
from integrations.skills_web import router as advanced_skills_router

# Initialize FastAPI app
app = FastAPI(
    title="Casper Node API",
    description="REST API for Casper Node AI orchestration",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include advanced skills router
app.include_router(advanced_skills_router)

# Initialize skill registry
skill_registry = SkillRegistry()

# Load Codex skills if available
try:
    from pathlib import Path
    codex_path = Path(__file__).parent / "Codex" / "agent_system.py"
    if codex_path.exists():
        parser = CodexParser(codex_path)
        skills = parser.parse()
        for skill in skills:
            skill_registry.register(skill, "codex")
except Exception:
    pass

# Initialize skill agent
skill_agent = SkillAgent(skill_registry, interactive=False)


# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    provider: str = "openai"
    model: Optional[str] = None
    use_skills: bool = True
    auto_pull: bool = False


class SkillRequest(BaseModel):
    skill_id: str


class EnableRequest(BaseModel):
    enabled: bool


# API Endpoints
@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "ok", "message": "Casper Node API is running", "version": "0.1.0"}


@app.get("/api/environment")
async def get_environment() -> Dict[str, Any]:
    env = detect_environment()
    return {"platform": env.platform.value, "is_termux": env.is_termux, "is_docker": env.is_docker, "supported": env.is_supported(), "python_version": env.python_version, "python_executable": env.python_executable, "node_version": env.node_version, "node_executable": env.node_executable, "architecture": env.architecture, "home_directory": str(env.home_directory), "temp_directory": str(env.temp_directory), "current_directory": str(env.current_directory)}


@app.post("/api/generate")
async def generate(request: GenerateRequest) -> Dict[str, Any]:
    try:
        result = skill_agent.generate(prompt=request.prompt, model=request.model, use_skills=request.use_skills)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/skills")
async def list_skills(domain: Optional[str] = None, tag: Optional[str] = None, enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
    skills = skill_registry.list_all()
    if domain:
        skills = [s for s in skills if s.domain.value == domain]
    if tag:
        skills = [s for s in skills if tag in s.tags]
    if enabled is not None:
        skills = [s for s in skills if s.enabled == enabled]
    return [skill.to_dict() for skill in skills]


@app.get("/api/skills/{skill_id}")
async def get_skill(skill_id: str) -> Dict[str, Any]:
    skill = skill_registry.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
    return skill.to_dict()


@app.post("/api/skills/{skill_id}/enable")
async def enable_skill(skill_id: str, request: EnableRequest) -> Dict[str, Any]:
    skill = skill_registry.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
    skill.enabled = request.enabled
    return {"status": "ok", "skill_id": skill_id, "enabled": request.enabled}


@app.get("/api/skills/stats")
async def get_skills_stats() -> Dict[str, Any]:
    return skill_registry.get_stats()


@app.post("/api/skills/import")
async def import_skills(repo_path: Optional[str] = None) -> Dict[str, Any]:
    try:
        if repo_path is None:
            from pathlib import Path
            codex_path = Path(__file__).parent.parent / "Codex"
            if codex_path.exists():
                repo_path = str(codex_path)
            else:
                return {"status": "error", "message": "Codex path required"}
        parser = CodexParser(repo_path)
        skills = parser.parse_from_codex_repo(repo_path)
        count = 0
        for skill in skills:
            skill_registry.register(skill, "codex")
            count += 1
        return {"status": "ok", "message": f"Imported {count} skills", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
