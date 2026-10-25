from __future__ import annotations

import json
from pathlib import Path
import pytest

from app.audit.chain import entry_hash, GENESIS
from app.engines.norm import same, normalise_text
from app.engines.rung import grade, check_state, coverage_state
from app.engines.guard import open_checks, overall_state, decide, make_waiver, GuardBlocked
from app.engines.bengine import eval_rule, simulate
from app.engines.delta import bucket
from app.engines.sampler import n_required, max_stale_if_zero_found

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VECTORS_PATH = REPO_ROOT / "tests" / "vectors.json"
FIXTURES_PATH = REPO_ROOT / "public" / "fixtures"


@pytest.fixture(scope="module")
def vectors():
    with open(VECTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_chain_vectors(vectors):
    chain_data = vectors["chain"]
    prev = GENESIS
    for i, event in enumerate(chain_data["events"]):
        computed_hash = entry_hash(prev, event)
        expected_row = chain_data["rows"][i]
        assert computed_hash == expected_row["hash"], f"Chain row {i+1} hash mismatch"
        assert prev == expected_row["prev_hash"], f"Chain row {i+1} prev_hash mismatch"
        prev = computed_hash


def test_same_text_vectors(vectors):
    for case in vectors["same_text"]:
        res = same(case["a"], case["b"])
        assert res is case["same"], f"same_text mismatch on a={case['a']!r}, b={case['b']!r}"


def test_same_num_vectors(vectors):
    for case in vectors["same_num"]:
        res = same(case["a"], case["b"], case["tol"])
        assert res is case["same"], f"same_num mismatch on a={case['a']}, b={case['b']}, tol={case['tol']}"


def test_grade_vectors(vectors):
    for idx, case in enumerate(vectors["grade"]):
        res = grade(case)
        assert res == case["expect"], f"grade mismatch on index {idx}: got {res}, expected {case['expect']}"


def test_check_state_vectors(vectors):
    for idx, case in enumerate(vectors["check_state"]):
        res = check_state(case["in"])
        assert res == case["expect"], f"check_state mismatch on index {idx}: got {res}, expected {case['expect']}"
        if "coverage" in case:
            cov = coverage_state(res)
            assert cov == case["coverage"], f"coverage_state mismatch on index {idx}: got {cov}, expected {case['coverage']}"


def test_guard_vectors(vectors):
    for idx, case in enumerate(vectors["guard"]):
        o = open_checks(case["checks"], case["waivers"])
        ov = overall_state(case["checks"], case["waivers"])
        assert o == case["open"], f"guard open_checks mismatch on index {idx}"
        assert ov == case["overall"], f"guard overall_state mismatch on index {idx}"


def test_guard_decide_and_waiver():
    checks = {"A": "PASSED", "B": "FAILED"}
    waivers = {}
    with pytest.raises(GuardBlocked) as exc_info:
        decide("approve", checks, waivers)
    assert exc_info.value.open_checks == ["B"]

    # Reject and request_info are allowed even with open checks
    assert decide("reject", checks, waivers) == {"action": "reject", "allowed": True}
    assert decide("request_info", checks, waivers) == {"action": "request_info", "allowed": True}

    # Waiver with invalid role
    with pytest.raises(PermissionError):
        make_waiver("B", "officer-1", "junior_officer", "Valid reason of 15+ characters", "2027-01-12T10:00:00+05:30")

    # Waiver with short reason (<15 characters)
    with pytest.raises(ValueError):
        make_waiver("B", "officer-1", "senior_officer", "Too short", "2027-01-12T10:00:00+05:30")

    # Valid waiver
    w = make_waiver("B", "officer-1", "senior_officer", "Valid reason of 15+ characters here", "2027-01-12T10:00:00+05:30")
    assert w["check_id"] == "B"
    waivers["B"] = w
    assert decide("approve", checks, waivers) == {"action": "approve", "allowed": True}


def test_bucket_vectors(vectors):
    for idx, case in enumerate(vectors["bucket"]):
        res = bucket(
            case["new"],
            case.get("old"),
            declared=case.get("declared", False),
            supports=case.get("supports", False),
            tol=case.get("tol", 0),
            missing=case.get("missing", False),
        )
        assert res == case["expect"], f"bucket mismatch on index {idx}: got {res}, expected {case['expect']}"


def test_sampler_vectors(vectors):
    sampler_data = vectors["sampler"]
    for case in sampler_data["n_required"]:
        res = n_required(case["p"])
        assert res == case["n"], f"n_required mismatch on p={case['p']}"

    for case in sampler_data["bound"]:
        res = max_stale_if_zero_found(case["N"], case["n"])
        assert res == case["k"], f"bound mismatch on N={case['N']}, n={case['n']}"


def test_rules_ast_evaluator_demo():
    rules_file = FIXTURES_PATH / "rules.json"
    claims_file = FIXTURES_PATH / "claims.json"

    with open(rules_file, "r", encoding="utf-8") as f:
        rules_by_id = {r["id"]: r for r in json.load(f)["rules"]}

    with open(claims_file, "r", encoding="utf-8") as f:
        claims = {c["key"]: c["value"] for c in json.load(f)["claims"]}

    # FIRE_NOC_COVERS_SEMESTER -> FAILED with value -79
    res_fire = eval_rule(rules_by_id["FIRE_NOC_COVERS_SEMESTER"], claims)
    assert res_fire["state"] == "FAILED"
    assert res_fire["value"] == -79

    # FLOORS_WITHIN_NOC -> PASSED with value 0
    res_floors = eval_rule(rules_by_id["FLOORS_WITHIN_NOC"], claims)
    assert res_floors["state"] == "PASSED"
    assert res_floors["value"] == 0
