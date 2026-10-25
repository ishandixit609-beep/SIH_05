from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Optional
import fitz
import httpx

from app.db import get_db
from app.extract.base import Extractor, Field
from app.extract.regex_fire_noc import RegexFireNocExtractor


def init_llm_cache_table(conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_cache (
            sha256 TEXT PRIMARY KEY,
            response TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    conn.commit()


class LLMFireNocExtractor:
    """LLM-assisted Fire NOC extractor with JSON-schema output, temperature 0, DB caching, and regex fallback."""

    def __init__(self, fallback_extractor: Optional[Extractor] = None):
        self.fallback = fallback_extractor or RegexFireNocExtractor()

    def extract(self, pdf_path: Path) -> list[Field]:
        if not pdf_path.exists():
            return []

        pdf_bytes = pdf_path.read_bytes()
        doc_sha = hashlib.sha256(pdf_bytes).hexdigest()

        # 1. Check SQLite Cache
        with get_db() as conn:
            init_llm_cache_table(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT response FROM llm_cache WHERE sha256 = ?", (doc_sha,))
            row = cursor.fetchone()
            if row:
                cached_data = json.loads(row["response"])
                return self._build_fields_from_dict(pdf_path, cached_data, ai_read=True)

        # 2. Check for LLM API Key (OpenAI / Gemini / custom)
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

        if not api_key:
            # Fall back to deterministic regex extractor (ai_read=False)
            return self.fallback.extract(pdf_path)

        # 3. Call LLM with JSON schema output (temperature 0)
        try:
            doc = fitz.open(str(pdf_path))
            raw_text = doc[0].get_text() if len(doc) > 0 else ""
            doc.close()

            prompt = (
                "Extract structured Fire NOC details from the text below as JSON.\n"
                "Return keys: number, valid_till, max_floors, issue_date, premises, agency, "
                "with confidence (0.0 to 1.0) for each field.\n\n"
                f"DOCUMENT TEXT:\n{raw_text}"
            )

            # Standard OpenAI-compatible endpoint call
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }

            resp = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=10.0)
            if resp.status_code == 200:
                result_json = resp.json()
                content_str = result_json["choices"][0]["message"]["content"]
                parsed_dict = json.loads(content_str)

                # Cache response
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT OR REPLACE INTO llm_cache (sha256, response, created_at) VALUES (?, ?, ?)",
                        (doc_sha, json.dumps(parsed_dict), time.time()),
                    )
                    conn.commit()

                return self._build_fields_from_dict(pdf_path, parsed_dict, ai_read=True)

        except Exception:
            # On any network or API error, fallback to regex
            pass

        return self.fallback.extract(pdf_path)

    def _build_fields_from_dict(self, pdf_path: Path, data: dict[str, Any], ai_read: bool = True) -> list[Field]:
        doc = fitz.open(str(pdf_path))
        page = doc[0] if len(doc) > 0 else None

        fields: list[Field] = []
        field_keys = [
            ("fire_noc.number", str(data.get("number", ""))),
            ("fire_noc.valid_till", str(data.get("valid_till", ""))),
            ("fire_noc.max_floors", int(data.get("max_floors", 5))),
            ("fire_noc.issue_date", str(data.get("issue_date", "01-10-2026"))),
            ("fire_noc.premises", str(data.get("premises", ""))),
            ("fire_noc.agency", str(data.get("agency", ""))),
        ]

        for k, v in field_keys:
            box = [0.0, 0.0, 0.0, 0.0]
            if page and str(v):
                rects = page.search_for(str(v))
                if rects:
                    box = [round(rects[0].x0, 1), round(rects[0].y0, 1), round(rects[0].x1, 1), round(rects[0].y1, 1)]

            fields.append({
                "key": k,
                "value": v,
                "confidence": float(data.get(f"{k}_confidence", 0.98)),
                "page": 1,
                "box": box,
                "ai_read": ai_read,
            })

        doc.close()
        return fields
