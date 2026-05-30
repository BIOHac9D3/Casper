from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from core.schemas.skill import Skill, SkillDomain
from core.parsers.codex_parser import CodexParser


class SkillRegistry:
    """Central registry for managing skills."""
    
    def __init__(self) -> None:
        """Initialize an empty skill registry."""
        self.skills: Dict[str, Skill] = {}
        self.sources: Dict[str, str] = {}
        self.index: Dict[str, Dict[str, List[str]]] = {
            "domain": {},
            "trigger": {},
            "tag": {},
            "author": {}
        }
    
    def register(self, skill: Skill, source: Optional[str] = None) -> None:
        """
        Register a skill in the registry.
        
        Args:
            skill: The skill to register
            source: Optional source identifier for the skill
        """
        if skill.id in self.skills:
            # Skill already exists, update it
            existing = self.skills[skill.id]
            if source and existing.source != source:
                # Different source, keep both or merge? For now, just update
                pass
            self.skills[skill.id] = skill
        else:
            self.skills[skill.id] = skill
        
        if source:
            self.sources[skill.id] = source
        
        # Update indexes
        self._update_indexes(skill)
    
    def _update_indexes(self, skill: Skill) -> None:
        """Update all search indexes for a skill."""
        # Domain index
        domain_key = skill.domain.value
        if domain_key not in self.index["domain"]:
            self.index["domain"][domain_key] = []
        if skill.id not in self.index["domain"][domain_key]:
            self.index["domain"][domain_key].append(skill.id)
        
        # Trigger index
        for trigger in skill.triggers:
            phrase = trigger.phrase.lower()
            if phrase not in self.index["trigger"]:
                self.index["trigger"][phrase] = []
            if skill.id not in self.index["trigger"][phrase]:
                self.index["trigger"][phrase].append(skill.id)
        
        # Tag index
        for tag in skill.tags:
            tag_key = tag.lower()
            if tag_key not in self.index["tag"]:
                self.index["tag"][tag_key] = []
            if skill.id not in self.index["tag"][tag_key]:
                self.index["tag"][tag_key].append(skill.id)
        
        # Author index
        if skill.author:
            author_key = skill.author.lower()
            if author_key not in self.index["author"]:
                self.index["author"][author_key] = []
            if skill.id not in self.index["author"][author_key]:
                self.index["author"][author_key].append(skill.id)

    def get(self, skill_id: str) -> Optional[Skill]:
        """
        Get a skill by its ID.
        
        Args:
            skill_id: The ID of the skill to retrieve
            
        Returns:
            Optional[Skill]: The skill if found, None otherwise
        """
        return self.skills.get(skill_id)
    
    def list_all(self) -> List[Skill]:
        """
        List all registered skills.
        
        Returns:
            List[Skill]: All registered skills
        """
        return list(self.skills.values())
    
    def list_by_domain(self, domain: SkillDomain) -> List[Skill]:
        """
        List skills by domain.
        
        Args:
            domain: The domain to filter by
            
        Returns:
            List[Skill]: Skills in the specified domain
        """
        domain_key = domain.value
        skill_ids = self.index["domain"].get(domain_key, [])
        return [self.skills[skill_id] for skill_id in skill_ids]
    
    def search_by_trigger(self, phrase: str, partial_match: bool = True) -> List[Skill]:
        """
        Search skills by trigger phrase.
        
        Args:
            phrase: The phrase to search for
            partial_match: Whether to match partial phrases (default: True)
            
        Returns:
            List[Skill]: Skills matching the trigger phrase
        """
        phrase_lower = phrase.lower()
        skill_ids: List[str] = []
        
        # Exact match
        if phrase_lower in self.index["trigger"]:
            skill_ids.extend(self.index["trigger"][phrase_lower])
        
        # Partial matches
        if partial_match:
            for trigger, ids in self.index["trigger"].items():
                if phrase_lower in trigger:
                    skill_ids.extend(ids)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skill_ids = []
        for skill_id in skill_ids:
            if skill_id not in seen:
                seen.add(skill_id)
                unique_skill_ids.append(skill_id)
        
        return [self.skills[skill_id] for skill_id in unique_skill_ids]
    
    def list_by_tag(self, tag: str) -> List[Skill]:
        """
        List skills by tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List[Skill]: Skills with the specified tag
        """
        tag_key = tag.lower()
        skill_ids = self.index["tag"].get(tag_key, [])
        return [self.skills[skill_id] for skill_id in skill_ids]
    
    def list_by_author(self, author: str) -> List[Skill]:
        """
        List skills by author.
        
        Args:
            author: The author to filter by
            
        Returns:
            List[Skill]: Skills by the specified author
        """
        author_key = author.lower()
        skill_ids = self.index["author"].get(author_key, [])
        return [self.skills[skill_id] for skill_id in skill_ids]

    def unregister(self, skill_id: str) -> bool:
        """
        Remove a skill from the registry.
        
        Args:
            skill_id: The ID of the skill to remove
            
        Returns:
            bool: True if the skill was removed, False if it didn't exist
        """
        if skill_id not in self.skills:
            return False
        
        skill = self.skills[skill_id]
        del self.skills[skill_id]
        
        if skill_id in self.sources:
            del self.sources[skill_id]
        
        # Remove from indexes
        self._remove_from_indexes(skill)
        
        return True
    
    def _remove_from_indexes(self, skill: Skill) -> None:
        """Remove a skill from all indexes."""
        # Domain index
        domain_key = skill.domain.value
        if domain_key in self.index["domain"]:
            if skill.id in self.index["domain"][domain_key]:
                self.index["domain"][domain_key].remove(skill.id)
        
        # Trigger index
        for trigger in skill.triggers:
            phrase = trigger.phrase.lower()
            if phrase in self.index["trigger"]:
                if skill.id in self.index["trigger"][phrase]:
                    self.index["trigger"][phrase].remove(skill.id)
        
        # Tag index
        for tag in skill.tags:
            tag_key = tag.lower()
            if tag_key in self.index["tag"]:
                if skill.id in self.index["tag"][tag_key]:
                    self.index["tag"][tag_key].remove(skill.id)
        
        # Author index
        if skill.author:
            author_key = skill.author.lower()
            if author_key in self.index["author"]:
                if skill.id in self.index["author"][author_key]:
                    self.index["author"][author_key].remove(skill.id)
    
    def clear(self) -> None:
        """Clear all skills from the registry."""
        self.skills.clear()
        self.sources.clear()
        self.index = {
            "domain": {},
            "trigger": {},
            "tag": {},
            "author": {}
        }

    def load_from_yaml(self, config_path: str | Path) -> None:
        """
        Load skills configuration from a YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        path = Path(config_path) if isinstance(config_path, str) else config_path
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        
        # Load source configurations
        for source_config in config.get("sources", []):
            self._load_source(source_config)
        
        # Apply overrides
        for skill_id, override in config.get("overrides", {}).items():
            if skill_id in self.skills:
                skill = self.skills[skill_id]
                for key, value in override.items():
                    if hasattr(skill, key):
                        setattr(skill, key, value)
    
    def _load_source(self, source_config: Dict[str, Any]) -> None:
        """
        Load skills from a source configuration.
        
        Args:
            source_config: Source configuration dictionary
        """
        source_name = source_config.get("name", "unknown")
        source_path = Path(source_config.get("path", ""))
        
        if not source_path.exists():
            print(f"Warning: Source path {source_path} does not exist")
            return
        
        if source_name == "codex":
            parser = CodexParser(source_path)
            skills = parser.parse()
            
            for skill in skills:
                skill.enabled = source_config.get("enabled", True)
                skill.priority = source_config.get("priority", 0)
                self.register(skill, source_name)
        else:
            print(f"Warning: Unknown source type: {source_name}")
    
    def load_from_codex_repo(self, repo_path: str | Path) -> None:
        """
        Load skills directly from the Codex repository.
        
        Args:
            repo_path: Path to the Codex repository
        """
        parser = CodexParser(repo_path)
        skills = parser.parse_from_codex_repo(repo_path)
        
        for skill in skills:
            self.register(skill, "codex")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the registry.
        
        Returns:
            Dict[str, Any]: Registry statistics
        """
        return {
            "total_skills": len(self.skills),
            "enabled_skills": sum(1 for s in self.skills.values() if s.enabled),
            "disabled_skills": sum(1 for s in self.skills.values() if not s.enabled),
            "domains": {d: len(ids) for d, ids in self.index["domain"].items()},
            "tags": {t: len(ids) for t, ids in self.index["tag"].items()},
            "sources": {s: sum(1 for sid, src in self.sources.items() if src == s) 
                       for s in set(self.sources.values())}
        }
