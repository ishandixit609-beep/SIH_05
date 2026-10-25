from __future__ import annotations

import unicodedata
from typing import Any

VARIANTS: dict[str, str] = {
    "shree": "shri",
    "sri": "shri",
    "shrimati": "smt",
    "pvt": "private",
    "ltd": "limited",
    "coll": "college",
    "engg": "engineering",
}


def normalise_text(s: str) -> str:
    """Normalise text: NFC, lowercase, expand &, keep letters/marks/digits/_, map variants."""
    t = unicodedata.normalize("NFC", s or "").lower().replace("&", " and ")
    cleaned: list[str] = []
    for c in t:
        if c.isspace() or c == "_":
            cleaned.append(c)
        else:
            cat = unicodedata.category(c)
            if cat and cat[0] in ("L", "M", "N"):
                cleaned.append(c)
            else:
                cleaned.append(" ")
    tokens = "".join(cleaned).split()
    return " ".join(VARIANTS.get(w, w) for w in tokens)


# Alias to match TypeScript naming if imported
normaliseText = normalise_text


def same(a: Any, b: Any, rel_tol: float = 0.0) -> bool:
    """Compare two values for equivalence (boolean, numeric with relative tolerance, or normalized text)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b or abs(a - b) <= rel_tol * max(abs(a), abs(b))
    return normalise_text(str(a)) == normalise_text(str(b))
