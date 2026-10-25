from __future__ import annotations

from typing import Any, Optional, TypedDict
from app.engines.norm import same

CONF_THRESHOLD = 0.85


class Grade(TypedDict):
    rung: int
    conflict: bool


class Check(TypedDict):
    state: str
    reason: str


def grade(
    evidence: dict[str, Any],
    rel_tol: float = 0.0,
    threshold: float = CONF_THRESHOLD,
) -> Grade:
    doc_val = evidence.get("docValue", evidence.get("doc"))
    doc_conf = evidence.get("docConfidence", evidence.get("conf"))
    rec_val = evidence.get("recordValue", evidence.get("rec"))
    adapter = evidence.get("adapterStatus", evidence.get("adapter"))

    has_doc = doc_val is not None
    doc_ok = has_doc and (doc_conf is not None and doc_conf >= threshold)
    has_rec = rec_val is not None

    conflict = adapter == "mismatch" or (
        has_doc and has_rec and not same(doc_val, rec_val, rel_tol)
    )

    if conflict:
        return {"rung": 1 if doc_ok else 0, "conflict": True}
    if adapter == "verified":
        return {"rung": 3, "conflict": False}
    if doc_ok and has_rec:
        return {"rung": 2, "conflict": False}
    if doc_ok:
        return {"rung": 1, "conflict": False}
    return {"rung": 0, "conflict": False}


def check_state(i: dict[str, Any]) -> Check:
    if not i.get("configured", True):
        return {"state": "NOT_CONFIGURED", "reason": "no_rule_or_checklist"}

    has_doc = i.get("has_document", i.get("hasDocument", True))
    if not has_doc:
        return {"state": "FAILED", "reason": "missing_document"}

    adapter_status = i.get("adapter_status", i.get("adapterStatus"))
    expiry = i.get("expiry")
    must_cover_until = i.get("must_cover_until", i.get("mustCoverUntil"))
    if adapter_status == "expired" or (expiry and must_cover_until and expiry < must_cover_until):
        return {"state": "FAILED", "reason": "expired_or_expires_too_soon"}

    rules = i.get("rules", [])
    if any(r is False for r in rules):
        return {"state": "FAILED", "reason": "rule_failed"}

    g = i.get("g")
    if g is None:
        g = {"rung": 3, "conflict": False}

    if g.get("conflict"):
        return {"state": "MANUAL_REVIEW", "reason": "sources_disagree"}

    low_conf = i.get("low_confidence", i.get("lowConfidence", False))
    if adapter_status == "manual_review" or low_conf:
        return {"state": "MANUAL_REVIEW", "reason": "needs_human_read"}

    required_rung = i.get("required_rung", i.get("requiredRung", 2))
    max_rung = i.get("max_rung", i.get("maxRung", 3))
    need = min(required_rung, max_rung)

    if g.get("rung", 0) < need:
        why = (
            "source_unavailable"
            if adapter_status in ("source_unavailable", "pending")
            else "no_record_to_match"
        )
        return {"state": "UNABLE_TO_VERIFY", "reason": why}

    return {"state": "PASSED", "reason": "ok"}


def coverage_state(c: dict[str, Any]) -> str:
    st = c.get("state")
    if st == "FAILED":
        return "missing" if c.get("reason") == "missing_document" else "partial"
    mapping = {
        "PASSED": "complete",
        "MANUAL_REVIEW": "needs_review",
        "UNABLE_TO_VERIFY": "unable_to_verify",
        "NOT_CONFIGURED": "not_configured",
    }
    return mapping.get(st, "needs_review")
