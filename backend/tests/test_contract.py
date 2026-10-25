from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_contract():
    init_db()
    client.post("/api/_reset")
    yield


def test_contract_all_get_endpoints():
    app_id = "APP-0001"
    token = "21c5519ddbbced3d"
    doc_id = "D-04"
    finding_id = "F-014"

    # 1. /api/applications/{id}/events
    res_events = client.get(f"/api/applications/{app_id}/events")
    assert res_events.status_code == 200
    events_data = res_events.json()
    assert "stages" in events_data
    assert "completed" in events_data
    assert "done" in events_data
    assert len(events_data["stages"]) == 8

    # 2. /api/applications/{id}/summary
    res_sum = client.get(f"/api/applications/{app_id}/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert "id" in sum_data
    assert "institution" in sum_data
    assert "name" in sum_data["institution"]
    assert "state" in sum_data["institution"]
    assert "cycle" in sum_data
    assert "category" in sum_data
    assert "version" in sum_data
    assert "claims" in sum_data
    assert "open_checks" in sum_data
    assert "overall" in sum_data
    assert "findings_open" in sum_data
    assert sum_data["overall"] in ("READY_FOR_DECISION", "REVIEW_INCOMPLETE")

    # 3. /api/applications/{id}/coverage
    res_cov = client.get(f"/api/applications/{app_id}/coverage")
    assert res_cov.status_code == 200
    cov_data = res_cov.json()
    assert "requirements" in cov_data
    assert "checks" in cov_data
    assert "overall" in cov_data
    assert "open_checks" in cov_data
    assert "waivers" in cov_data
    assert len(cov_data["requirements"]) == 14
    for r in cov_data["requirements"]:
        assert "id" in r
        assert "title" in r
        assert "state" in r
        assert "rung" in r
        assert "required_rung" in r
        assert "conflict" in r
        assert "waived" in r

    # 4. /api/applications/{id}/claims
    res_claims = client.get(f"/api/applications/{app_id}/claims")
    assert res_claims.status_code == 200
    claims_data = res_claims.json()
    assert "claims" in claims_data
    assert "counts" in claims_data
    assert "sample" in claims_data

    # 5. /api/applications/{id}/diff
    res_diff = client.get(f"/api/applications/{app_id}/diff")
    assert res_diff.status_code == 200
    diff_data = res_diff.json()
    assert "changed" in diff_data
    assert "ribbon" in diff_data

    # 6. /api/applications/{id}/timeline
    res_time = client.get(f"/api/applications/{app_id}/timeline")
    assert res_time.status_code == 200
    time_data = res_time.json()
    assert "today" in time_data
    assert "semesters" in time_data
    assert "pins" in time_data

    # 7. /api/applications/{id}/photos
    res_ph = client.get(f"/api/applications/{app_id}/photos")
    assert res_ph.status_code == 200
    ph_data = res_ph.json()
    assert "campus_polygon" in ph_data
    assert "photos" in ph_data

    # 8. /api/findings
    res_fins = client.get("/api/findings")
    assert res_fins.status_code == 200
    fins_data = res_fins.json()
    assert "findings" in fins_data
    assert "bundles" in fins_data
    for f in fins_data["findings"]:
        assert "id" in f
        assert "rule_id" in f
        assert "rule_version" in f
        assert "severity" in f
        assert "state" in f
        assert "req" in f
        assert "explanation" in f
        assert "next_step" in f
        assert "kind" in f["next_step"]
        assert "cost" in f["next_step"]
        assert "why" in f["next_step"]
        assert "ai_read" in f
        assert "decision" in f
        assert "resolved" in f

    # 9. /api/findings/{id}/graph
    res_graph = client.get(f"/api/findings/{finding_id}/graph")
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    assert "trace" in graph_data

    # 10. /api/documents/{id}/boxes
    res_boxes = client.get(f"/api/documents/{doc_id}/boxes")
    assert res_boxes.status_code == 200
    boxes_data = res_boxes.json()
    assert doc_id in boxes_data

    # 11. /api/documents/{id}/file
    res_file = client.get(f"/api/documents/{doc_id}/file")
    assert res_file.status_code == 200
    assert "application/pdf" in res_file.headers.get("content-type", "")

    # 12. /api/network/faculty/{token}
    res_net = client.get(f"/api/network/faculty/{token}")
    assert res_net.status_code == 200
    net_data = res_net.json()
    assert "label" in net_data
    assert "token" in net_data
    assert "nodes" in net_data
    assert "edges" in net_data
    assert "overlaps" in net_data

    # 13. /api/alerts
    res_alerts = client.get("/api/alerts")
    assert res_alerts.status_code == 200
    assert "alerts" in res_alerts.json()

    # 14. /api/rules
    res_rules = client.get("/api/rules")
    assert res_rules.status_code == 200
    rules_data = res_rules.json()
    assert "version" in rules_data
    assert "rules" in rules_data

    # 15. /api/audit
    res_audit = client.get("/api/audit")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert isinstance(audit_data, list)
    assert len(audit_data) >= 3
    for entry in audit_data:
        assert "seq" in entry
        assert "event" in entry
        assert "prev_hash" in entry
        assert "hash" in entry

    # 16. /api/audit/verify
    res_verify = client.get("/api/audit/verify")
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert "intact" in verify_data
    assert "entries" in verify_data
    assert "first_broken_seq" in verify_data
    assert "head" in verify_data

    # 17. /api/eval/summary
    res_eval = client.get("/api/eval/summary")
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert "rows" in eval_data
    assert "planted" in eval_data
    assert "found" in eval_data
    assert "false_positives" in eval_data

    # 18. /api/applications/{id}/scrutiny
    res_scrut = client.get(f"/api/applications/{app_id}/scrutiny")
    assert res_scrut.status_code == 200
    scrut_data = res_scrut.json()
    assert "document" in scrut_data
    assert "fields" in scrut_data
    assert "checks" in scrut_data
    assert "groups" in scrut_data
    assert "simulated" in scrut_data
    assert "workflow" in scrut_data
