"""Checks the mock against what the SATYAPAN frontend screenshots show."""
from fastapi.testclient import TestClient
from app.main import app, APP_ID

c = TestClient(app)
A = f"/api/applications/{APP_ID}"

def setup_function(_): c.post("/api/dev/reset")

def test_docket_numbers():
    s = c.get(f"{A}/summary").json()
    assert APP_ID == "APP-0001" and s["institution"]["name"].startswith("Shri Vidya Institute")
    assert s["counts"] == {"UNCHANGED": 62, "CHANGED_WITH_EVIDENCE": 9, "CHANGED_NO_EXPLANATION": 3, "NEW": 6}
    assert s["sample_statement"]["text"].startswith("6 of 62 re-verified, 0 stale. 95% confidence: at most 23 of 62 (37%)")
    assert (s["required_checks_open"], s["findings_open"], s["alerts_open"]) == (7, 15, 4)
    assert s["queues"]["red"]["count"] == 6 and s["queues"]["amber"]["count"] == 12
    assert [x["id"] for x in s["open_checks"]] == ["R02", "R04", "R05", "R06", "R07", "R08", "R10"]
    assert "faculty growth" in s["anomaly"]["text"]

def test_findings_text_matches_screens():
    f = {x["id"]: x for x in c.get("/api/findings").json()}; assert len(f) == 15
    assert f["F-014"]["explanation"] == "Built-up area per seat is 3.0 sq m; configured norm is 4.0 (illustrative)."
    assert f["F-015"]["explanation"] == "Carpet area is 0.96 of built-up area; configured ceiling is 0.85 (illustrative)."
    assert f["F-016"]["explanation"].startswith("Fire NOC is valid till 30-09-2027, which falls inside the odd semester (02-08-2027 to 18-12-2027)")
    assert f["F-014"]["trace"][:5] == ["eoa_v1", "AREA_PER_SEAT", "D-03 p.8", "intake.total", "F-014"]
    assert f["F-014"]["next_step"]["kind"] == "request_one_document" and f["F-014"]["next_step"]["reason"] == "No QR or issuer source exists"
    assert f["F-014"]["ai_read"] is True and f["F-015"]["ai_read"] is False

def test_bundle_letter_and_number_stamp():
    b = c.get("/api/bundles").json()[0]
    assert b["label"] == "Identity details differ" and b["finding_ids"] == ["F-011", "F-012", "F-013"]
    assert b["number_check"] == {"figures": 4, "passed": True}
    assert "Refs: F-011, F-012, F-013 (TRUST_NAME_CONSISTENT, eoa_v1)" in b["letter"] and set(b["letter_i18n"]) == {"hi", "mr"}
    fx = c.get(f"{A}/fixes").json(); assert [i["finding"] for i in fx["items"]][:3] == ["F-011", "F-014", "F-015"]

def test_spine_and_timeline_alerts():
    cov = {r["id"]: r for r in c.get(f"{A}/coverage").json()}; assert len(cov) == 10
    assert (cov["R01"]["check_state"], cov["R02"]["check_state"], cov["R06"]["check_state"]) == ("PASSED", "CONFLICT", "UNABLE TO VERIFY")
    assert cov["R04"]["doc"] == "D-03" and cov["R04"]["page"] == 8 and cov["R08"]["note"] == "58 to 83, no declared change"
    t = c.get(f"{A}/timeline").json(); assert t["pins"][0]["expires"] == "2027-09-30" and t["semesters"][0]["end"] == "2027-12-18"
    al = c.get("/api/alerts").json(); assert [a["id"] for a in al] == ["A-01", "A-02", "A-03", "A-04"] and al[3]["ref"] == "B-01"

def test_precheck_14_rows_two_gaps():
    assert len(c.get("/api/checklist").json()["requirements"]) == 14
    r = c.post("/api/precheck", json={}).json(); assert [g["id"] for g in r["gaps"]] == ["R10", "R14"]
    r2 = c.post("/api/precheck", json={"uploaded": ["D-01", "D-02", "D-03", "D-04", "D-05", "D-06", "D-07", "D-08", "D-10", "D-11"]}).json()
    assert r2["ready_to_submit"] is True

def test_pdfs_boxes():
    assert c.get("/api/documents/D-03/file").headers["content-type"] == "application/pdf"
    assert {b["text"] for b in c.get("/api/documents/D-03/boxes").json()} == {"Built-up area: 1,800 sq m", "Carpet area: 1,720 sq m"}
    assert c.get("/api/documents/D-09/file").status_code == 200

def test_resubmit_diff():
    r = c.post(f"{A}/resubmit").json()["diff"]["summary"]
    assert (r["values_changed"], r["findings_resolved"], r["findings_pending"]) == (3, 2, 1)
    s = c.get(f"{A}/summary").json(); assert s["required_checks_open"] == 6 and s["findings_open"] == 13

def test_guard_waivers_audit():
    r = c.post(f"{A}/decision", json={"action": "approve"}); assert r.status_code == 409
    ids = [x["id"] for x in r.json()["open"]]
    assert c.post("/api/waivers", json={"check_id": ids[0], "reason": " "}).status_code == 422
    for i in ids: assert c.post("/api/waivers", json={"check_id": i, "officer": "OFF-17", "reason": "Reviewed"}).status_code == 200
    assert c.post(f"{A}/decision", json={"action": "approve"}).status_code == 200
    log = c.get("/api/audit").json(); assert [e["event"] for e in log][:3] == ["application.submitted", "stage.read", "stage.check"]
    assert c.get("/api/audit/verify").json()["intact"] is True
    c.post("/api/audit/tamper"); assert c.get("/api/audit/verify").json()["intact"] is False

def test_accept_blocked_on_failed_rule():
    assert c.post("/api/findings/F-014/decision", json={"action": "accept"}).status_code == 409
    assert c.post("/api/findings/F-017/decision", json={"action": "accept"}).status_code == 200

def test_rule_lab_replay_eval():
    assert len(c.get("/api/rules").json()["rules"]) == 7
    sim = lambda v: c.post("/api/rules/simulate", json={"rule_id": "AREA_PER_SEAT", "param": "min_sqm_per_seat", "value": v}).json()["count"]
    assert sim(4.0) == 0 and sim(6.0) > 0
    r = c.post("/api/replay", json={"finding_id": "F-014", "rule_version": "v1.1"}).json()
    assert r["replayed"]["state"] == "PASSED" and r["stored_decision_untouched"]
    e = c.get("/api/eval/summary").json()
    assert (e["found"], e["total"], e["recall_pct"], e["valid_but_unusual_wrongly_failed"]) == (10, 10, 100, 0)
    assert (e["findings_with_evidence"]["n"], e["findings_with_evidence"]["of"]) == (7, 15)
    assert e["findings_without_box"] == ["F-017", "F-019", "F-020", "F-021", "F-022", "F-023", "F-024", "F-025"]

def test_clock_events_guard_lab():
    assert c.get("/api/clock").json()["now"].startswith("2027-01-12T10:3")
    assert c.get(f"{A}/events").json()[-1]["stage"] == "awaiting_officer"
    chk = [{"id": "x", "title": "Accreditation", "required": True, "state": "MANUAL REVIEW"}]
    assert c.post("/api/guard/evaluate", json={"checks": chk, "waivers": []}).json()["overall_state"] == "REVIEW INCOMPLETE"
