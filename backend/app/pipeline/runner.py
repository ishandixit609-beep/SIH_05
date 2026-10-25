from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, Optional

from app.checks.fire_noc import run_fire_noc_checks
from app.db import (
    get_db,
    append_audit_event,
    DEMO_NOW,
    STAGES,
)

STAGE_NAMES = ["intake", "read", "change", "check", "verify", "coverage", "resolve", "review"]


def execute_pipeline(
    app_id: str,
    pdf_path: Path,
    doc_sha256: str,
    doc_version: int,
    delay_ms: Optional[int] = None,
) -> dict[str, Any]:
    if delay_ms is None:
        delay_ms = int(os.getenv("STAGE_DELAY_MS", "500"))

    delay_sec = delay_ms / 1000.0

    # 1. Intake
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE application_run
            SET version = ?, completed = 1, done = 0, started_at = ?
            WHERE app_id = ?
            """,
            (doc_version, time.time(), app_id),
        )
        conn.commit()
        append_audit_event(
            conn,
            "stage.intake",
            {"app": app_id, "doc": "D-04", "version": str(doc_version)},
            actor="system",
            ts=DEMO_NOW,
        )

    if delay_sec > 0:
        time.sleep(delay_sec)

    # 2. Read (Extractor)
    scrutiny = run_fire_noc_checks(pdf_path)
    fields = scrutiny["fields"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE application_run SET completed = 2 WHERE app_id = ?",
            (app_id,),
        )
        conn.commit()
        append_audit_event(
            conn,
            "stage.read",
            {"docs": "1", "fields": str(len(fields))},
            actor="system",
            ts=DEMO_NOW,
        )

    if delay_sec > 0:
        time.sleep(delay_sec)

    # 3. Change (Delta)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE application_run SET completed = 3 WHERE app_id = ?",
            (app_id,),
        )
        conn.commit()
        append_audit_event(
            conn,
            "stage.change",
            {"claims_rechecked": str(len(fields)), "unchanged": "0"},
            actor="system",
            ts=DEMO_NOW,
        )

    if delay_sec > 0:
        time.sleep(delay_sec)

    # 4. Check (Rules & Scrutiny Checks)
    checks = scrutiny["checks"]
    failed_checks = [c for c in checks if c["outcome"] == "FAILED"]
    flagged_checks = [c for c in checks if c["outcome"] in ("FAILED", "MANUAL_REVIEW")]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE application_run SET completed = 4 WHERE app_id = ?",
            (app_id,),
        )
        conn.commit()
        append_audit_event(
            conn,
            "stage.check",
            {"rules": str(len(checks)), "failed": str(len(failed_checks))},
            actor="system",
            ts=DEMO_NOW,
        )

    if delay_sec > 0:
        time.sleep(delay_sec)

    # 5. Verify (Registry lookup)
    reg_check = next((c for c in checks if c["check_id"] == "FN_ISSUER_LOOKUP"), None)
    reg_outcome = reg_check["outcome"] if reg_check else "UNKNOWN"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE application_run SET completed = 5 WHERE app_id = ?",
            (app_id,),
        )
        conn.commit()
        append_audit_event(
            conn,
            "stage.verify",
            {"source": "issuer_registry", "status": reg_outcome},
            actor="system",
            ts=DEMO_NOW,
        )

    if delay_sec > 0:
        time.sleep(delay_sec)

    # 6. Coverage (R05 evaluation)
    if any(c["outcome"] == "FAILED" for c in checks):
        r05_state = "FAILED"
    elif any(c["outcome"] == "MANUAL_REVIEW" for c in checks):
        r05_state = "MANUAL_REVIEW"
    elif any(c["outcome"] == "UNABLE_TO_VERIFY" for c in checks):
        r05_state = "UNABLE_TO_VERIFY"
    else:
        r05_state = "PASSED"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE application_run SET completed = 6 WHERE app_id = ?",
            (app_id,),
        )
        conn.commit()
        append_audit_event(
            conn,
            "stage.coverage",
            {"requirement": "R05", "state": r05_state},
            actor="system",
            ts=DEMO_NOW,
        )

    if delay_sec > 0:
        time.sleep(delay_sec)

    # 7. Resolve
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE application_run SET completed = 7 WHERE app_id = ?",
            (app_id,),
        )
        conn.commit()
        append_audit_event(
            conn,
            "stage.resolve",
            {"finding": "F-016", "flagged": str(len(flagged_checks))},
            actor="system",
            ts=DEMO_NOW,
        )

    if delay_sec > 0:
        time.sleep(delay_sec)

    # 8. Review (Final)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE application_run
            SET completed = 8, done = 1
            WHERE app_id = ?
            """,
            (app_id,),
        )
        # Save scrutiny result
        cursor.execute(
            """
            INSERT OR REPLACE INTO scrutiny_result (app_id, doc_id, sha256, version, fields, checks, updated_at)
            VALUES (?, 'D-04', ?, ?, ?, ?, ?)
            """,
            (
                app_id,
                doc_sha256,
                doc_version,
                json.dumps(fields, ensure_ascii=False),
                json.dumps(checks, ensure_ascii=False),
                time.time(),
            ),
        )
        conn.commit()
        append_audit_event(
            conn,
            "stage.review",
            {"open_issues": str(len(flagged_checks))},
            actor="system",
            ts=DEMO_NOW,
        )

    return scrutiny
