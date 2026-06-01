from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, TypedDict

import requests


class AgentResult(TypedDict, total=False):
    """Shape of every dict returned by an agent.

    `status` is always present and is either "ok" or "error".
    Other keys are populated depending on the path; callers should not
    assume keys outside `status` are present in error results.
    """

    status: str
    provider: str
    model: str
    content: str
    message: str
    details: str
    raw: Any


class BaseAgent(ABC):
    """Abstract AI adapter interface."""

    @abstractmethod
    def generate(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Generate a structured response."""
        raise NotImplementedError

    def _post_json(
        self,
        url: str,
        *,
        provider: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: int,
        model: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[AgentResult]]:
        """POST JSON and split the result into (data, error_result).

        Exactly one of the returned values is non-None. The error dict
        preserves the historical key order: status, provider, [model],
        message, details. `model` is only included when the caller passes
        one — this matches how `LocalAgent` reports errors with the model
        attached, while cloud agents do not.
        """
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code >= 400:
            error: AgentResult = {"status": "error", "provider": provider}
            if model is not None:
                error["model"] = model
            error["message"] = f"HTTP {response.status_code}"
            error["details"] = response.text
            return None, error
        return response.json(), None
