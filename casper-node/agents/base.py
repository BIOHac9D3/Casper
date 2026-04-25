from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Abstract AI adapter interface."""

    @abstractmethod
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Generate a structured response."""
        raise NotImplementedError
