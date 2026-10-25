from __future__ import annotations

from datetime import datetime, date
import os
from pathlib import Path
import re
from typing import Any, Optional
import fitz
from dateutil.parser import parse as parse_date

from app.adapters.simulated_registry import lookup_fire_noc
from app.engines.bengine import eval_rule
from app.extract.base import Field
from app.extract.regex_fire_noc import RegexFireNocExtractor
from app.fixtures_layer import load_fixture

EDITORS = [
    "photoshop", "gimp", "illustrator", "canva", "inkscape", "corel",
    "foxit", "nitro", "sejda", "ilovepdf", "pdfescape", "acrobat"
]


def parse_pdf_date(d_str: Optional[str]) -> Optional[datetime]:
    if not d_str:
        return None
    s = d_str.strip()
    if s.startswith("D:"):
        s = s[2:]
    # Match YYYYMMDDHHmmss
    m = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", s)
    if m:
        try:
            return datetime(
                int(m.group(1)),
                int(m.group(2)),
                int(m.group(3)),
                int(m.group(4)),
                int(m.group(5)),
                int(m.group(6)),
            )
        except ValueError:
            pass
    try:
        return parse_date(s[:14])
    except Exception:
        return None


def run_fire_noc_checks(
    pdf_path: Path,
    extractor: Optional[Any] = None,
) -> dict[str, Any]:
    extractor = extractor or RegexFireNocExtractor()
    demo_today_str = os.getenv("DEMO_TODAY", "2027-01-12")
    demo_today = datetime.strptime(demo_today_str, "%Y-%m-%d").date()

    # Load claims & rules for scrutiny reason and AST evaluation
    claims_fixture = load_fixture("claims")
    claims_list = claims_fixture.get("claims", [])
    claims_map = {c["key"]: c["value"] for c in claims_list}
    claims_meta = {c["key"]: c for c in claims_list}
    rules_data = load_fixture("rules")
    rules_map = {r["id"]: r for r in rules_data.get("rules", [])}

    # Extract fields
    fields: list[Field] = extractor.extract(pdf_path)
    field_map = {f["key"]: f for f in fields}

    # Check key fields and confidence
    required_keys = ["fire_noc.number", "fire_noc.valid_till", "fire_noc.max_floors"]
    is_readable = (
        len(fields) > 0
        and all(k in field_map for k in required_keys)
        and all(field_map[k]["confidence"] >= 0.85 for k in required_keys)
    )

    if not is_readable:
        unread_check = {
            "check_id": "FN_READABLE",
            "title": "Document Legibility & Type Recognition",
            "outcome": "MANUAL_REVIEW",
            "why": "Could not read this document or unrecognized document format.",
            "evidence": None,
            "rule_id": "FN_READABLE",
            "rule_version": "eoa_v1",
            "clause": {"doc": "APH 2024-27", "ref": "Checklist", "page": None},
            "scrutiny_reason": "Automated extractor could not confidently extract mandatory Fire NOC fields.",
        }
        return {
            "fields": fields,
            "checks": [unread_check],
            "is_readable": False,
        }

    number_field = field_map["fire_noc.number"]
    valid_till_field = field_map["fire_noc.valid_till"]
    max_floors_field = field_map["fire_noc.max_floors"]
    issue_date_field = field_map.get("fire_noc.issue_date")
    premises_field = field_map.get("fire_noc.premises")
    agency_field = field_map.get("fire_noc.agency")

    number_val = str(number_field["value"])
    valid_till_str = str(valid_till_field["value"])
    valid_till_date = parse_date(valid_till_str, dayfirst=True).date()
    max_floors_val = int(max_floors_field["value"])

    issue_date_str = str(issue_date_field["value"]) if issue_date_field else "01-10-2026"
    issue_date = parse_date(issue_date_str, dayfirst=True).date()

    premises_text = str(premises_field["value"]) if premises_field else ""

    # Scrutiny reason template from claim bucket/prev
    claim_valid = claims_meta.get("fire_noc.valid_till", {})
    prev_valid = claim_valid.get("prev", "30-09-2026")
    scrutiny_reason_valid = (
        f"Fire NOC valid-till changed since the approved profile ({prev_valid} → {valid_till_str}), "
        "supported by this document; expiry check applies to documents with a validity date."
    )

    checks: list[dict[str, Any]] = []

    # 1. FN_NUMBER_FORMAT
    num_fmt_pass = bool(re.match(r"^SYN/FIRE/[A-Z]+/\d{4}/\d+$", number_val))
    checks.append({
        "check_id": "FN_NUMBER_FORMAT",
        "title": "Certificate Number Format",
        "outcome": "PASSED" if num_fmt_pass else "FAILED",
        "why": f"Certificate number {number_val} matches the issuer's format."
        if num_fmt_pass
        else f"Certificate number {number_val} does not match expected format ^SYN/FIRE/[A-Z]+/\\d{{4}}/\\d+$.",
        "evidence": {
            "doc": "D-04",
            "page": number_field["page"],
            "box": number_field["box"],
            "text": f"Certificate Number: {number_val}",
        },
        "rule_id": "FN_NUMBER_FORMAT",
        "rule_version": "eoa_v1",
        "clause": {"doc": "APH 2024-27", "ref": "Fire Safety Norms", "page": 1},
        "scrutiny_reason": scrutiny_reason_valid,
    })

    # 2. FN_ISSUER_LOOKUP (simulated source)
    reg = lookup_fire_noc(number_val, valid_till_str, max_floors_val)
    reg_status = reg["status"]
    if reg_status == "agrees":
        lookup_outcome = "PASSED"
        lookup_why = "Number found in the simulated State Fire Service registry; dates and floors agree. (simulated source)"
    elif reg_status == "not_found":
        lookup_outcome = "MANUAL_REVIEW"
        lookup_why = f"Certificate number {number_val} was not found in the simulated State Fire Service registry. Needs human confirmation. (simulated source)"
    elif reg_status == "mismatch":
        lookup_outcome = "MANUAL_REVIEW"
        lookup_why = f"Certificate number {number_val} found in simulated registry, but validity dates or floor limits disagree. (simulated source)"
    else:  # source_down
        lookup_outcome = "UNABLE_TO_VERIFY"
        lookup_why = "Simulated State Fire Service registry is unavailable. (simulated source)"

    checks.append({
        "check_id": "FN_ISSUER_LOOKUP",
        "title": "Issuer Registry Lookup (Simulated Source)",
        "outcome": lookup_outcome,
        "why": lookup_why,
        "evidence": {
            "doc": "D-04",
            "page": number_field["page"],
            "box": number_field["box"],
            "text": f"No: {number_val}",
        },
        "rule_id": "FN_ISSUER_LOOKUP",
        "rule_version": "eoa_v1",
        "clause": {"doc": "APH 2024-27", "ref": "Registry Cross-Verification", "page": 1},
        "scrutiny_reason": scrutiny_reason_valid,
    })

    # 3. FN_DATE_ORDER
    date_order_pass = issue_date < valid_till_date
    checks.append({
        "check_id": "FN_DATE_ORDER",
        "title": "Issue Date Precedes Expiry",
        "outcome": "PASSED" if date_order_pass else "FAILED",
        "why": f"Issued {issue_date.strftime('%d-%m-%Y')}, before valid-till {valid_till_date.strftime('%d-%m-%Y')}."
        if date_order_pass
        else f"Issue date {issue_date.strftime('%d-%m-%Y')} is not before valid-till {valid_till_date.strftime('%d-%m-%Y')}.",
        "evidence": {
            "doc": "D-04",
            "page": valid_till_field["page"],
            "box": valid_till_field["box"],
            "text": f"Valid till: {valid_till_str}",
        },
        "rule_id": "FN_DATE_ORDER",
        "rule_version": "eoa_v1",
        "clause": {"doc": "APH 2024-27", "ref": "Validity Sequencing", "page": 1},
        "scrutiny_reason": scrutiny_reason_valid,
    })

    # 4. FN_NOT_EXPIRED
    days_after_review = (valid_till_date - demo_today).days
    not_expired_pass = valid_till_date >= demo_today
    checks.append({
        "check_id": "FN_NOT_EXPIRED",
        "title": "Certificate Not Expired as of Review Date",
        "outcome": "PASSED" if not_expired_pass else "FAILED",
        "why": f"Valid till {valid_till_date.strftime('%d-%m-%Y')}, {days_after_review} days after the review date {demo_today.strftime('%d-%m-%Y')}."
        if not_expired_pass
        else f"Expired {abs(days_after_review)} days before the review date {demo_today.strftime('%d-%m-%Y')}.",
        "evidence": {
            "doc": "D-04",
            "page": valid_till_field["page"],
            "box": valid_till_field["box"],
            "text": f"Valid till: {valid_till_str}",
        },
        "rule_id": "FN_NOT_EXPIRED",
        "rule_version": "eoa_v1",
        "clause": {"doc": "APH 2024-27", "ref": "Mandatory Validity", "page": 1},
        "scrutiny_reason": scrutiny_reason_valid,
    })

    # 5. FIRE_NOC_COVERS_SEMESTER (from rules.json AST)
    odd_end_date = date(2027, 12, 18)  # 18-12-2027
    claims_env = {
        **claims_map,
        "fire_noc.valid_till_ord": valid_till_date.toordinal(),
        "semester.odd_end_ord": odd_end_date.toordinal(),
    }
    sem_rule = rules_map.get("FIRE_NOC_COVERS_SEMESTER", {})
    sem_res = eval_rule(sem_rule, claims_env)
    sem_pass = sem_res.get("state") == "PASSED"
    val_diff = int(sem_res.get("value", 0))

    checks.append({
        "check_id": "FIRE_NOC_COVERS_SEMESTER",
        "title": "Fire NOC Covers Academic Semester",
        "outcome": "PASSED" if sem_pass else "FAILED",
        "why": f"Covers the semester until 18-12-2027 ({val_diff} days after)."
        if sem_pass
        else f"Ends {abs(val_diff)} days before the odd semester ends on 18-12-2027.",
        "evidence": {
            "doc": "D-04",
            "page": valid_till_field["page"],
            "box": valid_till_field["box"],
            "text": f"Valid till: {valid_till_str}",
        },
        "rule_id": "FIRE_NOC_COVERS_SEMESTER",
        "rule_version": "eoa_v1",
        "clause": sem_rule.get("clause", {"doc": "APH 2024-27", "ref": "Clause 4.1.2", "page": 12}),
        "scrutiny_reason": scrutiny_reason_valid,
    })

    # 6. FLOORS_WITHIN_NOC (from rules.json AST)
    building_floors = int(claims_map.get("building.floors", 5))
    floors_env = {
        **claims_map,
        "fire_noc.max_floors": max_floors_val,
        "building.floors": building_floors,
    }
    floors_rule = rules_map.get("FLOORS_WITHIN_NOC", {})
    floors_res = eval_rule(floors_rule, floors_env)
    floors_pass = floors_res.get("state") == "PASSED"

    checks.append({
        "check_id": "FLOORS_WITHIN_NOC",
        "title": "Floors Within Sanctioned Fire NOC Limit",
        "outcome": "PASSED" if floors_pass else "FAILED",
        "why": f"Fire NOC allows {max_floors_val} floors; {building_floors} built.",
        "evidence": {
            "doc": "D-04",
            "page": max_floors_field["page"],
            "box": max_floors_field["box"],
            "text": f"Maximum floors: {max_floors_val}",
        },
        "rule_id": "FLOORS_WITHIN_NOC",
        "rule_version": "eoa_v1",
        "clause": floors_rule.get("clause", {"doc": "APH 2024-27", "ref": "Clause 2.3", "page": 6}),
        "scrutiny_reason": "Floor height safety limit check.",
    })

    # 7. FN_ADDRESS_MATCH
    pin_target = str(claims_map.get("campus.pincode", "411057"))
    dist_target = str(claims_map.get("campus.district", "Pune")).lower()
    address_pass = (pin_target in premises_text) and (dist_target in premises_text.lower())

    checks.append({
        "check_id": "FN_ADDRESS_MATCH",
        "title": "Premises Address Match with Application Profile",
        "outcome": "PASSED" if address_pass else "FAILED",
        "why": f"Premises address has pincode {pin_target} and district Pune, as in the application."
        if address_pass
        else f"Premises address does not contain applicant pincode {pin_target} or district Pune.",
        "evidence": {
            "doc": "D-04",
            "page": premises_field["page"] if premises_field else 1,
            "box": premises_field["box"] if premises_field else [0.0, 0.0, 0.0, 0.0],
            "text": f"Premises: {premises_text}",
        },
        "rule_id": "FN_ADDRESS_MATCH",
        "rule_version": "eoa_v1",
        "clause": {"doc": "APH 2024-27", "ref": "Campus Location Integrity", "page": 2},
        "scrutiny_reason": "Address verification against institution profile.",
    })

    # 8. FN_METADATA_HINT
    doc = fitz.open(str(pdf_path))
    meta = doc.metadata or {}
    producer = (meta.get("producer") or "").lower()
    creation_dt = parse_pdf_date(meta.get("creationDate"))
    mod_dt = parse_pdf_date(meta.get("modDate"))
    doc.close()

    suspicious_producer = any(ed in producer for ed in EDITORS)
    time_drift_hours = None
    if creation_dt and mod_dt:
        time_drift_hours = abs((mod_dt - creation_dt).total_seconds()) / 3600.0

    if suspicious_producer or (time_drift_hours is not None and time_drift_hours > 24.0):
        meta_outcome = "MANUAL_REVIEW"
        meta_why = "Possible tampering indicator, needs human confirmation. Hint, not proof."
    else:
        meta_outcome = "PASSED"
        meta_why = "no metadata to compare" if not (creation_dt and mod_dt) else "Creation and modification timestamps consistent; recognized generator."

    checks.append({
        "check_id": "FN_METADATA_HINT",
        "title": "PDF Metadata Integrity Analysis",
        "outcome": meta_outcome,
        "why": meta_why,
        "evidence": {
            "doc": "D-04",
            "page": 1,
            "box": [0.0, 0.0, 0.0, 0.0],
            "text": f"Producer: {meta.get('producer', 'N/A')}",
        },
        "rule_id": "FN_METADATA_HINT",
        "rule_version": "eoa_v1",
        "clause": {"doc": "APH 2024-27", "ref": "Metadata Forensic Screening", "page": 1},
        "scrutiny_reason": "Screening for graphic editor signatures or post-generation alterations.",
    })

    return {
        "fields": fields,
        "checks": checks,
        "is_readable": True,
    }
