from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_clean_db():
    init_db()
    # Reset before each test
    client.post("/api/_reset")
    yield


def test_audit_verify_tamper_repair():
    # 1. Initially intact
    res = client.get("/api/audit/verify")
    assert res.status_code == 200
    data = res.json()
    assert data["intact"] is True
    assert data["entries"] == 3
    assert data["first_broken_seq"] is None
    assert len(data["head"]) == 64

    # 2. Tamper
    res_tamper = client.post("/api/audit/_tamper")
    assert res_tamper.status_code == 200

    # 3. Verify reveals broken seq 3
    res_broken = client.get("/api/audit/verify")
    assert res_broken.status_code == 200
    data_broken = res_broken.json()
    assert data_broken["intact"] is False
    assert data_broken["first_broken_seq"] == 3

    # 4. Repair
    res_repair = client.post("/api/audit/_repair")
    assert res_repair.status_code == 200

    # 5. Verify intact again
    res_restored = client.get("/api/audit/verify")
    assert res_restored.status_code == 200
    data_restored = res_restored.json()
    assert data_restored["intact"] is True
    assert data_restored["first_broken_seq"] is None


def test_approve_with_open_checks_returns_409():
    res = client.post("/api/applications/APP-0001/decision", json={"action": "approve"})
    assert res.status_code == 409
    body = res.json()
    assert "open_checks" in body
    assert len(body["open_checks"]) > 0
    assert "Seal withheld" in body["detail"]


def test_waiver_validation():
    # 14 chars trimmed -> 403
    short_reason = "12345678901234"  # length 14
    res_short = client.post(
        "/api/applications/APP-0001/waivers",
        json={"check_id": "R05", "reason": short_reason},
    )
    assert res_short.status_code == 403

    # 15 chars trimmed -> 200
    valid_reason = "123456789012345"  # length 15
    res_valid = client.post(
        "/api/applications/APP-0001/waivers",
        json={"check_id": "R05", "reason": valid_reason},
    )
    assert res_valid.status_code == 200
    w = res_valid.json()
    assert w["check_id"] == "R05"
    assert w["reason"] == valid_reason


def test_finding_decision_failed_returns_422():
    # Finding F-014 has state FAILED
    res_accept = client.post("/api/findings/F-014/decision", json={"action": "accept"})
    assert res_accept.status_code == 422
    assert "cannot be accepted or dismissed" in res_accept.json()["detail"]

    res_dismiss = client.post("/api/findings/F-014/decision", json={"action": "dismiss"})
    assert res_dismiss.status_code == 422

    # request_info is allowed on FAILED findings
    res_req = client.post("/api/findings/F-014/decision", json={"action": "request_info", "reason": "Need updated documents"})
    assert res_req.status_code == 200
    assert res_req.json()["ok"] is True


def test_fixture_endpoints():
    # Summary
    s_res = client.get("/api/applications/APP-0001/summary")
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert "institution" in s_data
    assert "overall" in s_data
    assert "open_checks" in s_data

    # Coverage
    c_res = client.get("/api/applications/APP-0001/coverage")
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert "requirements" in c_data
    assert "checks" in c_data

    # Findings
    f_res = client.get("/api/findings")
    assert f_res.status_code == 200
    f_data = f_res.json()
    assert "findings" in f_data
    assert "bundles" in f_data

    # Rules
    r_res = client.get("/api/rules")
    assert r_res.status_code == 200
    assert "rules" in r_res.json()

    # Rule simulate
    sim_res = client.post("/api/rules/simulate", json={"rule_id": "AREA_PER_SEAT", "param": "min_sqm_per_seat", "value": 3.5})
    assert sim_res.status_code == 200
    assert "count" in sim_res.json()

    # Eval summary
    eval_res = client.get("/api/eval/summary")
    assert eval_res.status_code == 200
    assert "rows" in eval_res.json()

    # Document boxes
    b_res = client.get("/api/documents/D-04/boxes")
    assert b_res.status_code == 200

    # Resubmit
    resub_res = client.post("/api/applications/APP-0001/resubmit")
    assert resub_res.status_code == 200
