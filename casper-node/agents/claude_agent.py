from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from agents.base import BaseAgent


class ClaudeAgent(BaseAgent):
    endpoint = "https://api.anthropic.com/v1/messages"

    def __init__(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    def generate(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "status": "error",
                "provider": "claude",
                "message": "ANTHROPIC_API_KEY is not set",
            }

        selected_model = model or self.model
        payload = {
            "model": selected_model,
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        response = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)
        if response.status_code >= 400:
            return {
                "status": "error",
                "provider": "claude",
                "message": f"HTTP {response.status_code}",
                "details": response.text,
            }

        data = response.json()
        blocks = data.get("content", [])
        text = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        return {
            "status": "ok",
            "provider": "claude",
            "model": selected_model,
            "content": text,
            "raw": data,
        }
