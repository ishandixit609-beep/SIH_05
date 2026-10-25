from __future__ import annotations

from typing import Any, Iterable, Optional
from app.engines.norm import same

Bucket = str  # 'NEW' | 'UNCHANGED' | 'CHANGED_WITH_EVIDENCE' | 'CHANGED_NO_EXPLANATION'


def bucket(
    next_val: Any,
    prev_val: Any = None,
    declared: bool = False,
    supports: bool = False,
    tol: float = 0.0,
    missing: bool = False,
) -> Bucket:
    """Classify a claim's delta between current and previous cycle."""
    if missing or prev_val is None:
        return "NEW"
    if same(next_val, prev_val, tol):
        return "UNCHANGED"
    return "CHANGED_WITH_EVIDENCE" if (declared and supports) else "CHANGED_NO_EXPLANATION"


def counts(buckets: Iterable[Bucket]) -> dict[Bucket, int]:
    result: dict[Bucket, int] = {
        "NEW": 0,
        "UNCHANGED": 0,
        "CHANGED_WITH_EVIDENCE": 0,
        "CHANGED_NO_EXPLANATION": 0,
    }
    for b in buckets:
        result[b] = result.get(b, 0) + 1
    return result
