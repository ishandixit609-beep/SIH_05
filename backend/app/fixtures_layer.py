# FIXTURE-BACKED, NOT COMPUTED
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "public" / "fixtures"

_CACHE: dict[str, Any] = {}


def load_fixture(name: str) -> Any:
    """Load a fixture JSON from public/fixtures/<name>.json."""
    if name in _CACHE:
        return _CACHE[name]
    path = FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        _CACHE[name] = data
        return data


def get_fixture_copy(name: str) -> Any:
    data = load_fixture(name)
    return json.loads(json.dumps(data))
