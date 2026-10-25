from __future__ import annotations

from typing import Any, Optional, Protocol, TypedDict
from pathlib import Path


class Field(TypedDict):
    key: str
    value: Any
    confidence: float
    page: int
    box: list[float]  # [x0, y0, x1, y1] PDF points, top-left origin
    ai_read: bool


class Extractor(Protocol):
    def extract(self, pdf_path: Path) -> list[Field]:
        ...
