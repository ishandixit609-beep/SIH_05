from __future__ import annotations

import json
import os
import sqlite3
from typing import Any
from fastapi import Request

from app.fixtures_layer import get_fixture_copy
from app.engines.guard import open_checks, overall_state
from app.engines.crossinst import detect_faculty_overlaps
from app.engines.cengine import check_document_reuse
from app.checks.fire_noc import run_fire_noc_checks
from app.db import ensure_demo_sample

REQ_OF: dict[str, str] = {
    "F-011": "R02",
    "F-012": "R02",
    "F-013": "R02",
    "F-023": "R02",
    "F-014": "R04",
    "F-015": "R04",
    "F-016": "R05",
    "F-017": "R08",
    "F-018": "R08",
    "F-019": "R08",
    "F-020": "R08",
    "F-025": "R08",
    "F-021": "R07",
    "F-022": "R06",
    "F-024": "R10",
}


def resolve_actor_and_role(request: Request) -> tuple[str, str]:
    raw_role = request.headers.get("X-Role", "Scrutiny officer")
    actor = request.headers.get("X-User", "officer-1")
    if raw_role in ("Scrutiny officer", "senior_officer"):
        norm_role = "senior_officer"
    elif raw_role == "Institution":
        norm_role = "institution"
    elif raw_role == "Auditor":
        norm_role = "auditor"
    else:
        norm_role = raw_role
    return actor, norm_role


def compute_live_state(conn: sqlite3.Connection) -> dict[str, Any]:
    cursor = conn.cursor()

    # Waivers
    cursor.execute("SELECT check_id, officer, reason, ts FROM waiver")
    waivers = {
        r["check_id"]: {"officer": r["officer"], "reason": r["reason"], "ts": r["ts"]}
        for r in cursor.fetchall()
    }

    # Finding decisions
    cursor.execute("SELECT finding_id, action, reason FROM finding_decision")
    decided_rows = cursor.fetchall()
    decided = {r["finding_id"]: r["action"] for r in decided_rows}
    decided_reasons = {r["finding_id"]: r["reason"] for r in decided_rows}

    # Resubmitted status
    cursor.execute("SELECT resubmitted FROM application_state WHERE app_id = 'APP-0001'")
    row = cursor.fetchone()
    resubmitted = bool(row["resubmitted"]) if row else False

    # Get scrutiny result for D-04
    cursor.execute("SELECT fields, checks FROM scrutiny_result WHERE app_id = 'APP-0001'")
    scrutiny_row = cursor.fetchone()
    if scrutiny_row:
        scrutiny_fields = json.loads(scrutiny_row["fields"])
        scrutiny_checks = json.loads(scrutiny_row["checks"])
    else:
        sample_path = ensure_demo_sample()
        scrut_res = run_fire_noc_checks(sample_path)
        scrutiny_fields = scrut_res["fields"]
        scrutiny_checks = scrut_res["checks"]

    cov = get_fixture_copy("coverage")
    fd = get_fixture_copy("findings")

    resolved_by_v2 = {"F-014", "F-015"} if resubmitted else set()

    # 1. Determine computed R05 state & rung from scrutiny checks
    failed_checks = [c for c in scrutiny_checks if c["outcome"] == "FAILED"]
    review_checks = [c for c in scrutiny_checks if c["outcome"] == "MANUAL_REVIEW"]
    unverif_checks = [c for c in scrutiny_checks if c["outcome"] == "UNABLE_TO_VERIFY"]

    if failed_checks:
        r05_state = "FAILED"
        r05_reason = "expired_or_expires_too_soon" if any("EXPIRED" in c["check_id"] for c in failed_checks) else "rule_failed"
    elif review_checks:
        r05_state = "MANUAL_REVIEW"
        r05_reason = "sources_disagree" if any("LOOKUP" in c["check_id"] for c in review_checks) else "needs_human_read"
    elif unverif_checks:
        r05_state = "UNABLE_TO_VERIFY"
        r05_reason = "source_unavailable"
    else:
        r05_state = "PASSED"
        r05_reason = "ok"

    if r05_state == "PASSED":
        resolved_by_v2.add("F-016")

    reg_chk = next((c for c in scrutiny_checks if c["check_id"] == "FN_ISSUER_LOOKUP"), None)
    if reg_chk and reg_chk["outcome"] == "PASSED":
        r05_rung = 3
    elif all(f.get("confidence", 0) >= 0.85 for f in scrutiny_fields):
        r05_rung = 1
    else:
        r05_rung = 0

    r05_conflict = any(c["outcome"] == "MANUAL_REVIEW" and "LOOKUP" in c["check_id"] for c in scrutiny_checks)

    # 2. Check cross-institution faculty overlap (Sakshya hero feature)
    faculty_overlaps = detect_faculty_overlaps(conn)
    hero_overlap = next((o for o in faculty_overlaps if o["token"] == "21c5519ddbbced3d"), None)

    # 3. Check document reuse
    cursor.execute("SELECT sha256 FROM document WHERE id = 'D-04'")
    d04_row = cursor.fetchone()
    d04_sha = d04_row["sha256"] if d04_row else ""
    doc_reuse_match = check_document_reuse(conn, d04_sha) if d04_sha else None

    # 4. Build findings list
    sem_check = next((c for c in scrutiny_checks if c["check_id"] == "FIRE_NOC_COVERS_SEMESTER"), None)
    fins: list[dict[str, Any]] = []

    for f in fd.get("findings", []):
        fid = f["id"]
        f_copy = {
            **f,
            "req": f.get("req") or REQ_OF.get(fid),
            "decision": decided.get(fid),
            "decision_reason": decided_reasons.get(fid),
            "resolved": fid in resolved_by_v2,
            "fixture_backed": True,
        }

        # Computed finding F-016: Fire NOC Covers Semester
        if fid == "F-016" and sem_check:
            f_copy["state"] = sem_check["outcome"]
            f_copy["explanation"] = sem_check["why"]
            if sem_check.get("evidence"):
                f_copy["evidence"] = [sem_check["evidence"]]
            f_copy["next_step"] = {
                "kind": "query_issuer",
                "cost": 3,
                "why": "Querying the state fire authority or requesting renewal receipt is the cheapest next step (cost 3).",
            }
            f_copy["fixture_backed"] = False

        # Computed finding F-017: Faculty Overlap
        if fid == "F-017" and hero_overlap:
            f_copy["state"] = "MANUAL_REVIEW"
            inst_a, inst_b = hero_overlap["institutions"]
            f_copy["explanation"] = (
                f"Possible overlap, needs human confirmation: Faculty token {hero_overlap['token']} "
                f"holds simultaneous full-time appointments at {inst_a} and {inst_b}. "
                f"Overlap from {hero_overlap['overlap_from']}."
            )
            f_copy["next_step"] = {
                "kind": "query_issuer",
                "cost": 3,
                "why": "Querying the universities to confirm relieving date is the cheapest next step (cost 3).",
            }
            f_copy["fixture_backed"] = False

        # Computed finding F-023: Document Reuse
        if fid == "F-023":
            if doc_reuse_match:
                f_copy["state"] = "MANUAL_REVIEW"
                f_copy["explanation"] = (
                    f"Possible reuse, needs human confirmation: Document SHA-256 matches an identical "
                    f"certificate filed by {doc_reuse_match['other_institution']} for {doc_reuse_match['doc_type']}. "
                    "Legitimate causes exist (shared premises, multi-institution trust campus). A human confirms."
                )
                f_copy["next_step"] = {
                    "kind": "request_document",
                    "cost": 2,
                    "why": "Requesting an institution-specific certificate or premises declaration is the cheapest next step (cost 2).",
                }
                f_copy["fixture_backed"] = False
            else:
                f_copy["fixture_backed"] = True

        fins.append(f_copy)

    # 5. Build requirements list with Scenario handling (full vs fresh)
    scenario = os.getenv("SCENARIO", "full").lower()
    reqs: list[dict[str, Any]] = []

    for r in cov.get("requirements", []):
        r_copy = dict(r)
        rid = r_copy["id"]

        if rid == "R05":
            r_copy["state"] = r05_state
            r_copy["reason"] = r05_reason
            r_copy["rung"] = r05_rung
            r_copy["conflict"] = r05_conflict
            r_copy["coverage"] = "complete" if r05_state == "PASSED" else "needs_review" if r05_state == "MANUAL_REVIEW" else "partial"
            r_copy["fixture_backed"] = False
        else:
            if scenario == "fresh":
                # In fresh scenario, all 13 non-uploaded requirements fail missing_document
                r_copy["state"] = "FAILED"
                r_copy["reason"] = "missing_document"
                r_copy["coverage"] = "missing"
                r_copy["rung"] = 0
                r_copy["conflict"] = False
                r_copy["fixture_backed"] = False
            else:
                r_copy["fixture_backed"] = True

        mine = [f for f in fins if REQ_OF.get(f["id"]) == rid]
        all_cleared = len(mine) > 0 and all(
            f["resolved"] or f["decision"] in ("accept", "dismiss") for f in mine
        )
        if r_copy.get("state") == "MANUAL_REVIEW" and all_cleared:
            r_copy.update(
                {
                    "state": "PASSED",
                    "reason": "cleared_by_officer",
                    "coverage": "complete",
                    "by": "human",
                    "conflict": False,
                }
            )
        elif rid == "R04" and resubmitted and scenario != "fresh":
            r_copy.update(
                {
                    "state": "PASSED",
                    "reason": "ok_after_resubmission",
                    "coverage": "complete",
                    "rung": 2,
                }
            )
        reqs.append(r_copy)

    checks = {r["id"]: r["state"] for r in reqs}
    overall = overall_state(checks, waivers)
    open_chks = open_checks(checks, waivers)

    return {
        "cov": cov,
        "fins": fins,
        "reqs": reqs,
        "checks": checks,
        "bundles": fd.get("bundles", []),
        "waivers": waivers,
        "overall": overall,
        "open_checks": open_chks,
        "resubmitted": resubmitted,
        "scrutiny_fields": scrutiny_fields,
        "scrutiny_checks": scrutiny_checks,
        "scenario": scenario,
    }
