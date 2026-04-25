from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import yaml



def load_targets(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    targets = data.get("targets", {})
    if not isinstance(targets, dict):
        raise ValueError("targets must be a dictionary")
    return targets
