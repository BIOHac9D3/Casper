from __future__ import annotations

import pytest

from core.config import load_targets


def test_load_targets_happy_path(tmp_path) -> None:
    cfg = tmp_path / "targets.yaml"
    cfg.write_text(
        "targets:\n"
        "  local:\n"
        "    path: .\n"
        "    type: python\n",
        encoding="utf-8",
    )

    targets = load_targets(cfg)

    assert targets == {"local": {"path": ".", "type": "python"}}


def test_load_targets_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_targets(tmp_path / "missing.yaml")


def test_load_targets_invalid_shape(tmp_path) -> None:
    cfg = tmp_path / "targets.yaml"
    cfg.write_text("targets:\n  - one\n  - two\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_targets(cfg)


def test_load_targets_empty_file_returns_empty_dict(tmp_path) -> None:
    cfg = tmp_path / "targets.yaml"
    cfg.write_text("", encoding="utf-8")

    assert load_targets(cfg) == {}
