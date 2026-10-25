from __future__ import annotations

import io
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from synth.make_fire_noc import generate_fire_noc
from app.db import DB_DIR

client = TestClient(app)


def test_full_cycle_upload_scrutiny_resubmit_and_decision(tmp_path: Path):
    """
    Full end-to-end scrutiny lifecycle:
    1. Reset system to boot state
    2. Run institution precheck dry-run
    3. Upload standard Fire NOC (flags F-016 semester coverage gap)
    4. Run 8-stage scrutiny pipeline
    5. Verify evidence bounding boxes & scrutiny checks
    6. Officer decision blocked with HTTP 409
    7. Officer requests info on F-016
    8. Institution uploads renewed Fire NOC via resubmit
    9. Scrutiny re-runs: R05 passes, F-016 resolves
    10. Officer waives open items with valid 15+ char reasons
    11. Final approval succeeds with 200 OK
    12. Full SHA-256 audit chain verified intact
    """
    headers_officer = {"X-User": "officer-1", "X-Role": "senior_officer"}
    headers_inst = {"X-User": "inst-1", "X-Role": "institution"}

    # 1. Reset database
    res = client.post("/api/_reset")
    assert res.status_code == 200

    # Verify initial audit chain
    res = client.get("/api/audit/verify")
    assert res.status_code == 200
    assert res.json()["intact"] is True

    # 2. Institution precheck dry-run
    res = client.post("/api/institution/precheck", headers=headers_inst)
    assert res.status_code == 200
    precheck_data = res.json()
    assert "fixable" in precheck_data and "blocking" in precheck_data
    all_gaps = precheck_data["fixable"] + precheck_data["blocking"]
    assert any(g["requirement"] == "R05" for g in all_gaps)

    # 3. Generate initial Fire NOC (demo, expires 30-09-2027)
    demo_pdf = tmp_path / "fire_noc_initial.pdf"
    generate_fire_noc(demo_pdf, valid_till="30-09-2027")
    pdf_bytes = demo_pdf.read_bytes()

    # Upload document to start official application
    files = {"file": ("fire_noc_initial.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res = client.post("/api/applications", files=files, headers=headers_inst)
    assert res.status_code == 202
    app_run = res.json()
    assert app_run["id"] == "APP-0001"

    # 4. Wait for 8-stage pipeline completion
    for _ in range(50):
        res = client.get("/api/applications/APP-0001/events")
        assert res.status_code == 200
        events = res.json()
        if events["done"]:
            break
        time.sleep(0.05)
    assert events["done"] is True
    assert events["completed"] == 8

    # 5. Check Scrutiny Results
    # Coverage: R05 must be FAILED
    res = client.get("/api/applications/APP-0001/coverage")
    assert res.status_code == 200
    cov = res.json()
    r05 = next(r for r in cov["requirements"] if r["id"] == "R05")
    assert r05["state"] == "FAILED"
    assert "R05" in cov["open_checks"]

    # Findings: F-016 must be present and open
    res = client.get("/api/findings")
    assert res.status_code == 200
    findings_data = res.json()
    f016 = next(f for f in findings_data["findings"] if f["id"] == "F-016")
    assert f016["state"] == "FAILED"
    assert f016["resolved"] is False
    assert len(f016["evidence"]) > 0
    assert f016["evidence"][0]["box"][2] > f016["evidence"][0]["box"][0]  # valid bounding box

    # Boxes endpoint
    res = client.get("/api/documents/D-04/boxes")
    assert res.status_code == 200
    boxes_data = res.json()
    assert "D-04" in boxes_data

    # File endpoint
    res = client.get("/api/documents/D-04/file")
    assert res.status_code == 200
    assert res.content.startswith(b"%PDF-")

    # 6. Officer Guard: Approve MUST be blocked with 409
    res = client.post("/api/applications/APP-0001/decision", json={"action": "approve"}, headers=headers_officer)
    assert res.status_code == 409
    err_body = res.json()
    assert "R05" in err_body["open_checks"]

    # Officer cannot dismiss a FAILED finding (HTTP 422)
    res = client.post("/api/findings/F-016/decision", json={"action": "dismiss"}, headers=headers_officer)
    assert res.status_code == 422

    # 7. Officer requests info on F-016
    res = client.post("/api/findings/F-016/decision", json={"action": "request_info"}, headers=headers_officer)
    assert res.status_code == 200

    # 8. Institution Fix: Upload renewed Fire NOC (valid till 31-12-2028)
    renewed_pdf = tmp_path / "fire_noc_renewed.pdf"
    generate_fire_noc(renewed_pdf, renewed=True)
    renewed_bytes = renewed_pdf.read_bytes()

    resubmit_files = {"file": ("fire_noc_renewed.pdf", io.BytesIO(renewed_bytes), "application/pdf")}
    res = client.post("/api/applications/APP-0001/resubmit", files=resubmit_files, headers=headers_inst)
    assert res.status_code == 200

    # 9. Verify Scrutiny Re-evaluation after upload
    res = client.get("/api/applications/APP-0001/coverage")
    assert res.status_code == 200
    cov_v2 = res.json()
    r05_v2 = next(r for r in cov_v2["requirements"] if r["id"] == "R05")
    assert r05_v2["state"] == "PASSED"
    assert "R05" not in cov_v2["open_checks"]

    res = client.get("/api/findings")
    assert res.status_code == 200
    f016_v2 = next(f for f in res.json()["findings"] if f["id"] == "F-016")
    assert f016_v2["resolved"] is True

    # 10. Officer handles remaining open checks via valid written waivers (>= 15 chars)
    for chk in list(cov_v2["open_checks"]):
        res = client.post(
            "/api/applications/APP-0001/waivers",
            json={"check_id": chk, "reason": "Officer verified compliance via provisional authority certificate."},
            headers=headers_officer,
        )
        assert res.status_code == 200

    # Verify all checks now cleared
    res = client.get("/api/applications/APP-0001/coverage")
    assert res.status_code == 200
    assert len(res.json()["open_checks"]) == 0

    # 11. Final Officer Approval
    res = client.post("/api/applications/APP-0001/decision", json={"action": "approve"}, headers=headers_officer)
    assert res.status_code == 200
    decision_data = res.json()
    assert decision_data["action"] == "approve"
    assert decision_data["allowed"] is True

    # 12. Complete Audit Chain Verification
    res = client.get("/api/audit/verify")
    assert res.status_code == 200
    audit_verify = res.json()
    assert audit_verify["intact"] is True
    assert audit_verify["entries"] > 10  # boot + precheck + stages + decisions + waivers + approval
    assert audit_verify["first_broken_seq"] is None
