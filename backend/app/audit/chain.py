from __future__ import annotations

import hashlib
import json
from typing import Any, Optional, TypedDict

GENESIS = "0" * 64


class Event(TypedDict):
    ts: str
    actor: str
    event: str
    payload: dict[str, Any]


class Row(TypedDict):
    seq: int
    event: dict[str, Any]
    prev_hash: str
    hash: str


def canonical(v: Any) -> str:
    """Canonical JSON serialization: sorted keys, no spaces, UTF-8 encoded without ascii-escapes."""
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def entry_hash(prev: str, event: Any) -> str:
    return sha256_hex(prev + canonical(event))


def append(chain: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any]:
    prev = chain[-1]["hash"] if chain else GENESIS
    row: dict[str, Any] = {
        "seq": len(chain) + 1,
        "event": event,
        "prev_hash": prev,
        "hash": entry_hash(prev, event),
    }
    chain.append(row)
    return row


def verify(chain: list[dict[str, Any]]) -> Optional[int]:
    """Returns None when intact, else the first broken seq number."""
    prev = GENESIS
    for r in chain:
        expected = entry_hash(prev, r["event"])
        if r.get("prev_hash") != prev or r.get("hash") != expected:
            return r["seq"]
        prev = r["hash"]
    return None
