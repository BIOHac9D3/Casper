from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from agents.base import BaseAgent


class LocalAgent(BaseAgent):
    """Local model adapter using Ollama-compatible HTTP endpoints."""

    def __init__(self) -> None:
        self.host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        self.model = os.getenv("LOCAL_MODEL", "llama3.2:3b")

    def ensure_model(self, model: Optional[str] = None) -> Dict[str, Any]:
        selected_model = model or self.model
        endpoint = f"{self.host}/api/pull"
        payload = {"name": selected_model, "stream": False}

        response = requests.post(endpoint, json=payload, timeout=600)
        if response.status_code >= 400:
            return {
                "status": "error",
                "provider": "local",
                "model": selected_model,
                "message": f"HTTP {response.status_code}",
                "details": response.text,
            }

        data = response.json()
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

        response = requests.post(endpoint, json=payload, timeout=180)
        if response.status_code >= 400:
            return {
                "status": "error",
                "provider": "local",
                "model": selected_model,
                "message": f"HTTP {response.status_code}",
                "details": response.text,
            }

        data = response.json()
        return {
            "status": "ok",
            "provider": "local",
            "model": selected_model,
            "content": data.get("response", ""),
            "raw": data,
        }
