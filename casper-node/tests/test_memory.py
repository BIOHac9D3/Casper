from __future__ import annotations

import json
import re
from datetime import datetime


def test_log_event_writes_jsonl(tmp_memory) -> None:
    path1 = tmp_memory.log_event("test_event", {"k": "v"})
    path2 = tmp_memory.log_event("test_event", {"k": "v2"})

    assert path1 == path2
    lines = path1.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first["event"] == "test_event"
    assert first["payload"] == {"k": "v"}
    datetime.fromisoformat(first["timestamp"])


def test_log_filename_is_yyyymmdd(tmp_memory) -> None:
    path = tmp_memory.log_event("e", {})
    assert re.fullmatch(r"\d{8}\.log", path.name)


def test_directories_are_created(tmp_path) -> None:
    from core.memory import MemoryStore

    store = MemoryStore(tmp_path / "fresh")
    assert (tmp_path / "fresh" / "logs").is_dir()
    assert (tmp_path / "fresh" / "sessions").is_dir()
    assert store.logs_dir.exists()
