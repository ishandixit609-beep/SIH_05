from __future__ import annotations

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import init_db, ensure_demo_sample
from app.checks.fire_noc import run_fire_noc_checks
from app.extract.regex_fire_noc import RegexFireNocExtractor
from synth.make_fire_noc import generate_fire_noc

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_env():
    os.environ["STAGE_DELAY_MS"] = "0"
    init_db()
    client.post("/api/_reset")
    yield


def test_generator_default_expired_tampered(tmp_path: Path):
    # 1. Default
    default_pdf = tmp_path / "default.pdf"
    generate_fire_noc(default_pdf)
    assert default_pdf.exists()

    res_default = run_fire_noc_checks(default_pdf)
    assert res_default["is_readable"] is True
    failed_default = [c["check_id"] for c in res_default["checks"] if c["outcome"] == "FAILED"]
    passed_default = [c["check_id"] for c in res_default["checks"] if c["outcome"] == "PASSED"]
    assert failed_default == ["FIRE_NOC_COVERS_SEMESTER"]
    assert len(passed_default) == 7

    # 2. Expired
    expired_pdf = tmp_path / "expired.pdf"
    generate_fire_noc(expired_pdf, expired=True)
    res_expired = run_fire_noc_checks(expired_pdf)
    failed_expired = [c["check_id"] for c in res_expired["checks"] if c["outcome"] == "FAILED"]
    assert "FN_NOT_EXPIRED" in failed_expired
    assert "FIRE_NOC_COVERS_SEMESTER" in failed_expired

    # 3. Tampered
    tampered_pdf = tmp_path / "tampered.pdf"
    generate_fire_noc(tampered_pdf, tampered=True)
    res_tampered = run_fire_noc_checks(tampered_pdf)
    review_tampered = [c["check_id"] for c in res_tampered["checks"] if c["outcome"] == "MANUAL_REVIEW"]
    assert "FN_ISSUER_LOOKUP" in review_tampered
    assert "FN_METADATA_HINT" in review_tampered
    # Tampered must be MANUAL_REVIEW, never FAILED for lookup/hint
    assert "FN_ISSUER_LOOKUP" not in [c["check_id"] for c in res_tampered["checks"] if c["outcome"] == "FAILED"]
    assert "FN_METADATA_HINT" not in [c["check_id"] for c in res_tampered["checks"] if c["outcome"] == "FAILED"]


def test_garbage_pdf_handling(tmp_path: Path):
    garbage_pdf = tmp_path / "garbage.pdf"
    garbage_pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    res = run_fire_noc_checks(garbage_pdf)
    assert res["is_readable"] is False
    assert len(res["checks"]) == 1
    assert res["checks"][0]["outcome"] == "MANUAL_REVIEW"
    assert "Could not read this document" in res["checks"][0]["why"]


def test_upload_validations(tmp_path: Path):
    # 1. Non-PDF magic bytes -> 415
    fake_txt = b"Hello world, not a PDF"
    res_415 = client.post(
        "/api/applications",
        files={"file": ("test.txt", fake_txt, "text/plain")},
    )
    assert res_415.status_code == 415

    # 2. Oversized file (> 5 MB) -> 413
    oversized = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 10)
    res_413 = client.post(
        "/api/applications",
        files={"file": ("large.pdf", oversized, "application/pdf")},
    )
    assert res_413.status_code == 413


def test_end_to_end_pipeline_and_scrutiny(tmp_path: Path):
    # 1. Generate a valid demo NOC and upload
    valid_pdf = tmp_path / "noc_upload.pdf"
    generate_fire_noc(valid_pdf)

    with open(valid_pdf, "rb") as f:
        res_post = client.post(
            "/api/applications",
            files={"file": ("noc_upload.pdf", f, "application/pdf")},
        )
    assert res_post.status_code == 202
    assert res_post.json()["id"] == "APP-0001"
    assert res_post.json()["state"] == "queued"

    # 2. Poll events until done
    events_res = client.get("/api/applications/APP-0001/events")
    assert events_res.status_code == 200
    events_data = events_res.json()
    assert events_data["done"] is True
    assert events_data["completed"] == 8

    # 3. Check scrutiny endpoint
    scrut_res = client.get("/api/applications/APP-0001/scrutiny")
    assert scrut_res.status_code == 200
    scrut = scrut_res.json()
    assert scrut["document"]["id"] == "D-04"
    assert len(scrut["fields"]) >= 3
    assert len(scrut["checks"]) == 8
    assert "FIRE_NOC_COVERS_SEMESTER" in scrut["groups"]["flagged"]
    assert "FN_NUMBER_FORMAT" in scrut["groups"]["verified_ok"]
    assert "FN_ISSUER_LOOKUP" in scrut["groups"]["verified_ok"]
    assert "FN_NOT_EXPIRED" in scrut["groups"]["verified_ok"]

    # 4. Check document boxes and file download
    boxes_res = client.get("/api/documents/D-04/boxes")
    assert boxes_res.status_code == 200
    assert "D-04" in boxes_res.json()
    assert len(boxes_res.json()["D-04"]["1"]) >= 3

    file_res = client.get("/api/documents/D-04/file")
    assert file_res.status_code == 200
    assert file_res.headers["content-type"] == "application/pdf"

    # 5. Check coverage R05 reflects the failed semester coverage check
    cov_res = client.get("/api/applications/APP-0001/coverage")
    assert cov_res.status_code == 200
    r05 = next(r for r in cov_res.json()["requirements"] if r["id"] == "R05")
    assert r05["state"] == "FAILED"
    assert r05["rung"] == 3  # Verified in simulated registry

    # 6. Approve returns 409
    appr_res = client.post("/api/applications/APP-0001/decision", json={"action": "approve"})
    assert appr_res.status_code == 409
    assert "R05" in appr_res.json()["open_checks"]

    # 7. Short waiver returns 403
    waiver_res = client.post(
        "/api/applications/APP-0001/waivers",
        json={"check_id": "R05", "reason": "Too short"},
    )
    assert waiver_res.status_code == 403

    # 8. Audit chain verify remains intact
    audit_res = client.get("/api/audit/verify")
    assert audit_res.status_code == 200
    assert audit_res.json()["intact"] is True
