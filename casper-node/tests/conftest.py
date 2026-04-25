from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.memory import MemoryStore  # noqa: E402  (import after sys.path injection)


ENV_VARS = (
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "LOCAL_MODEL",
    "OLLAMA_HOST",
    "CASPER_HTTP_TIMEOUT",
)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def tmp_memory(tmp_path: Path) -> MemoryStore:
    return MemoryStore(tmp_path / "memory")


@pytest.fixture
def mock_post(monkeypatch: pytest.MonkeyPatch) -> Callable[..., MagicMock]:
    """Patches `requests.post` in every agent module and returns a builder.

    Call the returned builder with `status_code`, `json_data`, and `text`
    to install a fake response. The builder returns the recorded `MagicMock`
    so tests can assert on calls.
    """
    holder: dict[str, MagicMock] = {}

    def install(*, status_code: int = 200, json_data: Any = None, text: str = "") -> MagicMock:
        response = MagicMock()
        response.status_code = status_code
        response.text = text
        response.json.return_value = json_data if json_data is not None else {}

        post = MagicMock(return_value=response)
        monkeypatch.setattr("agents.base.requests.post", post)
        holder["post"] = post
        return post

    return install
