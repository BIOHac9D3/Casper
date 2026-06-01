from __future__ import annotations

import os
from typing import Any, Dict, Optional

from agents.base import BaseAgent

REQUEST_TIMEOUT_SECONDS = int(os.getenv("CASPER_HTTP_TIMEOUT", "60"))
TEMPERATURE = 0.2


class OpenAIAgent(BaseAgent):
    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "error", "provider": "openai", "message": "OPENAI_API_KEY is not set"}

        selected_model = model or self.model
        payload = {
            "model": selected_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": TEMPERATURE,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data, error = self._post_json(
            self.endpoint,
            provider="openai",
            payload=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if error is not None:
            return dict(error)

        assert data is not None
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "status": "ok",
            "provider": "openai",
            "model": selected_model,
            "content": content,
            "raw": data,
        }
