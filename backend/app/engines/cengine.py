from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
from typing import Any, Optional


def init_reuse_table(conn: sqlite3.Connection, seed_sha256: Optional[str] = None) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS other_institution_document (
            institution_id TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            doc_type TEXT NOT NULL
        )
        """
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) as cnt FROM other_institution_document")
    if cursor.fetchone()["cnt"] == 0:
        # Default seed: use provided hash, or a known sample hash
        target_hash = seed_sha256 or "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        cursor.execute(
            """
            INSERT INTO other_institution_document (institution_id, sha256, doc_type)
            VALUES ('SYN-SANGLI-0017', ?, 'fire_noc')
            """,
            (target_hash,),
        )
        conn.commit()


def check_document_reuse(conn: sqlite3.Connection, doc_sha256: str) -> Optional[dict[str, Any]]:
    init_reuse_table(conn)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT institution_id, doc_type, sha256 FROM other_institution_document WHERE sha256 = ?",
        (doc_sha256,),
    )
    row = cursor.fetchone()
    if row:
        return {
            "matched": True,
            "other_institution": row["institution_id"],
            "doc_type": row["doc_type"],
            "sha256": row["sha256"],
        }
    return None
