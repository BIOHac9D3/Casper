from __future__ import annotations

import os
from typing import Any, Dict

import requests

from agents.base import BaseAgent


class OpenAIAgent(BaseAgent):
    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "error", "provider": "openai", "message": "OPENAI_API_KEY is not set"}

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)
        if response.status_code >= 400:
            return {
                "status": "error",
                "provider": "openai",
                "message": f"HTTP {response.status_code}",
                "details": response.text,
            }

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "status": "ok",
            "provider": "openai",
            "model": self.model,
            "content": content,
            "raw": data,
        }
