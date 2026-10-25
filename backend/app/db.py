from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Optional

from app.audit.chain import append, GENESIS

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "satyapan.db"

DEMO_NOW = "2027-01-12T10:30:00+05:30"
OFFICER_DEFAULT = "officer-1"

STAGES = ["intake", "read", "change", "check", "verify", "coverage", "resolve", "review"]


def ensure_demo_sample() -> Path:
    sample_path = DB_DIR / "samples" / "fire_noc_demo.pdf"
    if not sample_path.exists():
        from synth.make_fire_noc import generate_fire_noc
        generate_fire_noc(sample_path)
    return sample_path


def get_db_path() -> Path:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return DB_PATH


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    get_db_path()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                seq INTEGER PRIMARY KEY,
                ts TEXT NOT NULL,
                actor TEXT NOT NULL,
                event TEXT NOT NULL,
                payload TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                hash TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS application_run (
                app_id TEXT PRIMARY KEY,
                version INTEGER NOT NULL DEFAULT 1,
                stages TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                done INTEGER NOT NULL DEFAULT 0,
                started_at REAL NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document (
                id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                path TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                doc_type TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS waiver (
                check_id TEXT PRIMARY KEY,
                officer TEXT NOT NULL,
                reason TEXT NOT NULL,
                ts TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS finding_decision (
                finding_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                reason TEXT,
                ts TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS application_state (
                app_id TEXT PRIMARY KEY,
                resubmitted INTEGER NOT NULL DEFAULT 0,
                version INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scrutiny_result (
                app_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                version INTEGER NOT NULL,
                fields TEXT NOT NULL,
                checks TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )
        conn.commit()

        # Seed initial state if audit_log is empty
        cursor.execute("SELECT COUNT(*) as cnt FROM audit_log")
        if cursor.fetchone()["cnt"] == 0:
            seed_boot_events(conn)

        # Seed application_state if empty
        cursor.execute("SELECT COUNT(*) as cnt FROM application_state WHERE app_id = 'APP-0001'")
        if cursor.fetchone()["cnt"] == 0:
            cursor.execute(
                "INSERT INTO application_state (app_id, resubmitted, version) VALUES ('APP-0001', 0, 1)"
            )
            conn.commit()

        # Seed application_run if empty
        cursor.execute("SELECT COUNT(*) as cnt FROM application_run WHERE app_id = 'APP-0001'")
        if cursor.fetchone()["cnt"] == 0:
            cursor.execute(
                """
                INSERT INTO application_run (app_id, version, stages, completed, done, started_at)
                VALUES ('APP-0001', 1, ?, 8, 1, ?)
                """,
                (json.dumps(STAGES), time.time() - 100),
            )
            conn.commit()

        # Ensure sample fire_noc_demo.pdf and D-04 document entry
        sample_path = ensure_demo_sample()
        cursor.execute("SELECT COUNT(*) as cnt FROM document WHERE id = 'D-04'")
        if cursor.fetchone()["cnt"] == 0:
            import hashlib
            doc_sha = hashlib.sha256(sample_path.read_bytes()).hexdigest()
            cursor.execute(
                """
                INSERT INTO document (id, sha256, path, version, doc_type)
                VALUES ('D-04', ?, ?, 1, 'fire_noc')
                """,
                (doc_sha, str(sample_path)),
            )
            conn.commit()

        # Initialize cross-institution faculty appointments and document reuse tables
        from app.engines.crossinst import init_faculty_table
        from app.engines.cengine import init_reuse_table
        from synth.make_fire_noc import generate_fire_noc
        init_faculty_table(conn)

        # Generate sample for reuse seeding if needed
        reuse_sample = DB_DIR / "samples" / "reused_noc_sample.pdf"
        if not reuse_sample.exists():
            generate_fire_noc(reuse_sample, number="SYN/FIRE/PUN/2026/8888")
        import hashlib
        reuse_sha = hashlib.sha256(reuse_sample.read_bytes()).hexdigest()
        init_reuse_table(conn, seed_sha256=reuse_sha)


def seed_boot_events(conn: sqlite3.Connection) -> None:
    chain: list[dict[str, Any]] = []
    boot_events = [
        ("application.submitted", {"app": "APP-0001", "version": "1"}),
        ("stage.read", {"docs": "8", "fields": "412"}),
        ("stage.check", {"rules": "7", "findings": "15"}),
    ]
    cursor = conn.cursor()
    cursor.execute("DELETE FROM audit_log")
    for event_name, payload in boot_events:
        row = append(chain, {"ts": DEMO_NOW, "actor": "system", "event": event_name, "payload": payload})
        cursor.execute(
            """
            INSERT INTO audit_log (seq, ts, actor, event, payload, prev_hash, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["seq"],
                row["event"]["ts"],
                row["event"]["actor"],
                row["event"]["event"],
                json.dumps(row["event"]["payload"], ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                row["prev_hash"],
                row["hash"],
            ),
        )
    conn.commit()


def get_audit_chain(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT seq, ts, actor, event, payload, prev_hash, hash FROM audit_log ORDER BY seq ASC")
    rows = cursor.fetchall()
    chain: list[dict[str, Any]] = []
    for r in rows:
        chain.append(
            {
                "seq": r["seq"],
                "event": {
                    "ts": r["ts"],
                    "actor": r["actor"],
                    "event": r["event"],
                    "payload": json.loads(r["payload"]),
                },
                "prev_hash": r["prev_hash"],
                "hash": r["hash"],
            }
        )
    return chain


def append_audit_event(
    conn: sqlite3.Connection,
    event_name: str,
    payload: dict[str, Any],
    actor: str = OFFICER_DEFAULT,
    ts: str = DEMO_NOW,
) -> dict[str, Any]:
    chain = get_audit_chain(conn)
    event_obj = {"ts": ts, "actor": actor, "event": event_name, "payload": payload}
    row = append(chain, event_obj)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO audit_log (seq, ts, actor, event, payload, prev_hash, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["seq"],
            ts,
            actor,
            event_name,
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
            row["prev_hash"],
            row["hash"],
        ),
    )
    conn.commit()
    return row


def tamper_audit_log(conn: sqlite3.Connection) -> None:
    """Tamper row 3's payload without updating its hash."""
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE audit_log
        SET payload = '{"findings":"3","rules":"7"}'
        WHERE seq = 3
        """
    )
    conn.commit()


def repair_audit_log(conn: sqlite3.Connection) -> None:
    seed_boot_events(conn)


def reset_all_state(conn: sqlite3.Connection) -> None:
    if os.getenv("ENV") == "production":
        raise PermissionError("Reset is disabled in production")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM waiver")
    cursor.execute("DELETE FROM finding_decision")
    cursor.execute("UPDATE application_state SET resubmitted = 0, version = 1 WHERE app_id = 'APP-0001'")
    cursor.execute(
        """
        UPDATE application_run
        SET version = 1, completed = 8, done = 1, started_at = ?
        WHERE app_id = 'APP-0001'
        """,
        (time.time() - 100,),
    )
    conn.commit()
    seed_boot_events(conn)
