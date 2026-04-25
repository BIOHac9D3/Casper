from __future__ import annotations

import os
from typing import Any, Dict, Optional

from agents.base import BaseAgent

PULL_TIMEOUT_SECONDS = 600
GENERATE_TIMEOUT_SECONDS = 180


class LocalAgent(BaseAgent):
    """Local model adapter using Ollama-compatible HTTP endpoints."""

    def __init__(self) -> None:
        self.host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        self.model = os.getenv("LOCAL_MODEL", "llama3.2:3b")

    def ensure_model(self, model: Optional[str] = None) -> Dict[str, Any]:
        selected_model = model or self.model
        endpoint = f"{self.host}/api/pull"
        payload = {"name": selected_model, "stream": False}

        data, error = self._post_json(
            endpoint,
            provider="local",
            payload=payload,
            timeout=PULL_TIMEOUT_SECONDS,
            model=selected_model,
        )
        if error is not None:
            return dict(error)

        assert data is not None
        return {
            "status": "ok",
            "provider": "local",
            "model": selected_model,
            "message": data.get("status", "model ready"),
            "raw": data,
        }

    def generate(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        selected_model = model or self.model
        endpoint = f"{self.host}/api/generate"
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
        }

        data, error = self._post_json(
            endpoint,
            provider="local",
            payload=payload,
            timeout=GENERATE_TIMEOUT_SECONDS,
            model=selected_model,
        )
        if error is not None:
            return dict(error)

        assert data is not None
        return {
            "status": "ok",
            "provider": "local",
            "model": selected_model,
            "content": data.get("response", ""),
            "raw": data,
        }
