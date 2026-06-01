from __future__ import annotations

import os
from typing import Any, Dict, Optional

from agents.base import BaseAgent

MAX_TOKENS = 800
REQUEST_TIMEOUT_SECONDS = int(os.getenv("CASPER_HTTP_TIMEOUT", "60"))
ANTHROPIC_VERSION = "2023-06-01"


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
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        data, error = self._post_json(
            self.endpoint,
            provider="claude",
            payload=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if error is not None:
            return dict(error)

        assert data is not None
        blocks = data.get("content", [])
        text = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        return {
            "status": "ok",
            "provider": "claude",
            "model": selected_model,
            "content": text,
            "raw": data,
        }
