from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from typing import Any, Optional


def make_faculty_token(raw_id: str, secret: Optional[str] = None) -> str:
    """HMAC-SHA256 of raw ID, hex-encoded, first 16 characters. Raw IDs are never stored."""
    if secret is None:
        secret = os.getenv("HMAC_SECRET", "satyapan_demo_hmac_secret_2027")
    normalized = raw_id.strip().upper().encode("utf-8")
    h = hmac.new(secret.encode("utf-8"), normalized, hashlib.sha256).hexdigest()
    return h[:16]


def init_faculty_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS faculty_appointment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL,
            institution_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            start TEXT NOT NULL,
            end TEXT
        )
        """
    )
    conn.commit()

    # Seed if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM faculty_appointment")
    if cursor.fetchone()["cnt"] == 0:
        # Hero token from network.json
        hero_token = "21c5519ddbbced3d"
        appointments = [
            (hero_token, "SYN-PUNE-0001", "full_time", "2025-04-01", None),
            (hero_token, "SYN-SANGLI-0017", "full_time", "2026-01-05", None),
            # Unrelated faculty appointments (some part-time, some non-overlapping)
            ("a1b2c3d4e5f67890", "SYN-PUNE-0001", "part_time", "2024-01-01", None),
            ("a1b2c3d4e5f67890", "SYN-MUMBAI-0004", "full_time", "2024-01-01", None),
            ("f0e1d2c3b4a59876", "SYN-PUNE-0001", "full_time", "2022-01-01", "2024-12-31"),
            ("f0e1d2c3b4a59876", "SYN-NAGPUR-0042", "full_time", "2025-01-01", None),
        ]
        cursor.executemany(
            """
            INSERT INTO faculty_appointment (token, institution_id, kind, start, end)
            VALUES (?, ?, ?, ?, ?)
            """,
            appointments,
        )
        conn.commit()


def detect_faculty_overlaps(
    conn: sqlite3.Connection,
    token_filter: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Detect overlapping full-time faculty appointments across different institutions."""
    init_faculty_table(conn)
    cursor = conn.cursor()

    if token_filter:
        cursor.execute(
            "SELECT token, institution_id, kind, start, end FROM faculty_appointment WHERE token = ? ORDER BY start ASC",
            (token_filter,),
        )
    else:
        cursor.execute(
            "SELECT token, institution_id, kind, start, end FROM faculty_appointment ORDER BY token, start ASC"
        )

    rows = cursor.fetchall()

    by_token: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        tok = r["token"]
        by_token.setdefault(tok, []).append(dict(r))

    overlaps: list[dict[str, Any]] = []

    for tok, appts in by_token.items():
        n = len(appts)
        for i in range(n):
            for j in range(i + 1, n):
                a = appts[i]
                b = appts[j]

                # Must be different institutions
                if a["institution_id"] == b["institution_id"]:
                    continue

                # Both must be full_time
                if a["kind"] != "full_time" or b["kind"] != "full_time":
                    continue

                start_a = a["start"]
                end_a = a["end"] or "9999-12-31"

                start_b = b["start"]
                end_b = b["end"] or "9999-12-31"

                # Check intersection
                overlap_start = max(start_a, start_b)
                overlap_end = min(end_a, end_b)

                if overlap_start <= overlap_end:
                    overlaps.append({
                        "token": tok,
                        "institutions": sorted([a["institution_id"], b["institution_id"]]),
                        "overlap_from": overlap_start,
                        "overlap_to": None if overlap_end == "9999-12-31" else overlap_end,
                        "label": "Possible overlap, needs human confirmation",
                        "appointment_a": a,
                        "appointment_b": b,
                    })

    return overlaps


INSTITUTION_NAMES: dict[str, str] = {
    "SYN-PUNE-0001": "Shri Vidya Institute of Engineering & Technology, Pune",
    "SYN-SANGLI-0017": "Krishna Valley College of Engineering, Sangli",
    "SYN-MUMBAI-0004": "Mumbai Institute of Technology",
    "SYN-NAGPUR-0042": "Nagpur Engineering College",
}


def build_faculty_network(conn: sqlite3.Connection, token: str) -> dict[str, Any]:
    init_faculty_table(conn)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT token, institution_id, kind, start, end FROM faculty_appointment WHERE token = ? ORDER BY start ASC",
        (token,),
    )
    rows = cursor.fetchall()

    nodes: list[dict[str, str]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes = set()

    for r in rows:
        inst_id = r["institution_id"]
        if inst_id not in seen_nodes:
            seen_nodes.add(inst_id)
            nodes.append({
                "id": inst_id,
                "name": INSTITUTION_NAMES.get(inst_id, f"Institution {inst_id}"),
            })
        edges.append({
            "institution": inst_id,
            "from": r["start"],
            "to": r["end"],
            "kind": r["kind"],
        })

    overlaps = detect_faculty_overlaps(conn, token_filter=token)
    clean_overlaps = [
        {
            "token": o["token"],
            "institutions": o["institutions"],
            "overlap_from": o["overlap_from"],
            "overlap_to": o["overlap_to"],
            "label": o["label"],
        }
        for o in overlaps
    ]

    return {
        "label": "F-7731",
        "token": token,
        "nodes": nodes,
        "edges": edges,
        "overlaps": clean_overlaps,
    }
