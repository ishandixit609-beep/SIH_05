from __future__ import annotations

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import init_db, get_db, append_audit_event
from app.engines.crossinst import make_faculty_token, detect_faculty_overlaps, init_faculty_table
from app.engines.cengine import check_document_reuse, init_reuse_table

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_clean():
    os.environ["SCENARIO"] = "full"
    os.environ["STAGE_DELAY_MS"] = "0"
    init_db()
    client.post("/api/_reset")
    yield


def test_hmac_helper():
    secret = "test_hmac_secret_123"
    raw_id = " faculty-7731 "
    token = make_faculty_token(raw_id, secret=secret)
    # 1. First 16 hex chars
    assert len(token) == 16
    assert all(c in "0123456789abcdef" for c in token)
    # 2. Case and whitespace invariant
    token2 = make_faculty_token("FACULTY-7731", secret=secret)
    assert token == token2
    # 3. Different raw id produces different token
    token3 = make_faculty_token("FACULTY-8842", secret=secret)
    assert token != token3


def test_faculty_overlap_variations():
    with get_db() as conn:
        cursor = conn.cursor()
        # Clean table for isolated test
        cursor.execute("DELETE FROM faculty_appointment")

        # 1. Full-time overlapping across different institutions -> FLAGGED
        tok_overlap = "tok_overlap_1111"
        cursor.execute("INSERT INTO faculty_appointment (token, institution_id, kind, start, end) VALUES (?, 'INST-A', 'full_time', '2025-01-01', NULL)", (tok_overlap,))
        cursor.execute("INSERT INTO faculty_appointment (token, institution_id, kind, start, end) VALUES (?, 'INST-B', 'full_time', '2025-06-01', NULL)", (tok_overlap,))

        # 2. One part-time -> NOT FLAGGED
        tok_part = "tok_parttime_222"
        cursor.execute("INSERT INTO faculty_appointment (token, institution_id, kind, start, end) VALUES (?, 'INST-A', 'full_time', '2025-01-01', NULL)", (tok_part,))
        cursor.execute("INSERT INTO faculty_appointment (token, institution_id, kind, start, end) VALUES (?, 'INST-B', 'part_time', '2025-06-01', NULL)", (tok_part,))

        # 3. Non-overlapping dates -> NOT FLAGGED
        tok_non_overlap = "tok_nonov_333333"
        cursor.execute("INSERT INTO faculty_appointment (token, institution_id, kind, start, end) VALUES (?, 'INST-A', 'full_time', '2023-01-01', '2024-12-31')", (tok_non_overlap,))
        cursor.execute("INSERT INTO faculty_appointment (token, institution_id, kind, start, end) VALUES (?, 'INST-B', 'full_time', '2025-01-01', NULL)", (tok_non_overlap,))

        conn.commit()

        overlaps_all = detect_faculty_overlaps(conn)
        tokens_flagged = [o["token"] for o in overlaps_all]

        assert tok_overlap in tokens_flagged
        assert tok_part not in tokens_flagged
        assert tok_non_overlap not in tokens_flagged


def test_document_reuse_hit_and_miss():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM other_institution_document")
        cursor.execute(
            """
            INSERT INTO other_institution_document (institution_id, sha256, doc_type)
            VALUES ('SYN-NAGPUR-0042', 'known_hash_1234567890abcdef', 'fire_noc')
            """
        )
        conn.commit()

        # Hit
        hit = check_document_reuse(conn, "known_hash_1234567890abcdef")
        assert hit is not None
        assert hit["matched"] is True
        assert hit["other_institution"] == "SYN-NAGPUR-0042"

        # Miss
        miss = check_document_reuse(conn, "unknown_hash_ffffffffffffff")
        assert miss is None


def test_precheck_creates_no_application_state():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM audit_log")
        audit_count_before = cursor.fetchone()["cnt"]

        cursor.execute("SELECT version FROM application_run WHERE app_id = 'APP-0001'")
        run_version_before = cursor.fetchone()["version"]

    res = client.post("/api/institution/precheck")
    assert res.status_code == 200
    data = res.json()
    assert "fixable" in data
    assert "blocking" in data
    assert len(data["fixable"]) > 0 or len(data["blocking"]) > 0

    # Ensure checklist requirements are reported
    all_reqs_in_precheck = [item["requirement"] for item in data["fixable"] + data["blocking"]]
    assert "R05" in all_reqs_in_precheck
    assert "R01" in all_reqs_in_precheck
    assert "R04" in all_reqs_in_precheck

    with get_db() as conn:
        cursor = conn.cursor()
        # Exactly one audit entry: precheck.run
        cursor.execute("SELECT COUNT(*) as cnt FROM audit_log")
        audit_count_after = cursor.fetchone()["cnt"]
        assert audit_count_after == audit_count_before + 1

        cursor.execute("SELECT event, actor FROM audit_log ORDER BY seq DESC LIMIT 1")
        last_event = cursor.fetchone()
        assert last_event["event"] == "precheck.run"

        # No application state or run modified
        cursor.execute("SELECT version FROM application_run WHERE app_id = 'APP-0001'")
        run_version_after = cursor.fetchone()["version"]
        assert run_version_after == run_version_before


def test_fresh_scenario_13_missing_and_409():
    os.environ["SCENARIO"] = "fresh"

    cov_res = client.get("/api/applications/APP-0001/coverage")
    assert cov_res.status_code == 200
    reqs = cov_res.json()["requirements"]

    # In fresh scenario, all requirements except R05 are missing_document
    missing_reqs = [r["id"] for r in reqs if r["state"] == "FAILED" and r["reason"] == "missing_document"]
    assert len(missing_reqs) == 13
    assert "R01" in missing_reqs
    assert "R04" in missing_reqs
    assert "R08" in missing_reqs

    # Approve returns 409 listing all open checks
    appr_res = client.post("/api/applications/APP-0001/decision", json={"action": "approve"})
    assert appr_res.status_code == 409
    open_checks = appr_res.json()["open_checks"]
    for m in missing_reqs:
        assert m in open_checks


def test_role_authorization_403():
    headers_auditor = {"X-Role": "Auditor", "X-User": "auditor-1"}

    # Auditor cannot approve
    res_appr = client.post(
        "/api/applications/APP-0001/decision",
        json={"action": "approve"},
        headers=headers_auditor,
    )
    assert res_appr.status_code == 403

    # Auditor cannot record waiver
    res_waiver = client.post(
        "/api/applications/APP-0001/waivers",
        json={"check_id": "R05", "reason": "Valid reason of 15+ characters"},
        headers=headers_auditor,
    )
    assert res_waiver.status_code == 403

    # Auditor cannot make finding decision
    res_finding = client.post(
        "/api/findings/F-014/decision",
        json={"action": "request_info", "reason": "Need document"},
        headers=headers_auditor,
    )
    assert res_finding.status_code == 403

    # Auditor cannot resubmit
    res_resub = client.post(
        "/api/applications/APP-0001/resubmit",
        headers=headers_auditor,
    )
    assert res_resub.status_code == 403

    # But Scrutiny officer / senior_officer can
    headers_officer = {"X-Role": "Scrutiny officer", "X-User": "officer-1"}
    res_finding_ok = client.post(
        "/api/findings/F-014/decision",
        json={"action": "request_info", "reason": "Need document from officer"},
        headers=headers_officer,
    )
    assert res_finding_ok.status_code == 200


def test_audit_chain_remains_intact_after_all_phase4_actions():
    res = client.get("/api/audit/verify")
    assert res.status_code == 200
    assert res.json()["intact"] is True
    assert res.json()["first_broken_seq"] is None
