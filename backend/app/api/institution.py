from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.db import get_db, append_audit_event, DEMO_NOW, ensure_demo_sample
from app.api.common import resolve_actor_and_role
from app.checks.fire_noc import run_fire_noc_checks

router = APIRouter(prefix="/institution", tags=["institution"])

CHECKLIST_REQS = [
    ("R01", "Missing Society/Trust registration certificate", "Upload registered Trust/Society deed.", True),
    ("R02", "Missing Land Title/Ownership document", "Upload certified land ownership document or registered lease deed.", False),
    ("R03", "Missing Land Use Certificate", "Upload Land Use conversion certificate from competent revenue authority.", True),
    ("R04", "Missing Architect-certified area statement", "Upload architect statement of instructional and administrative carpet area.", False),
    ("R06", "Missing Structural Stability Certificate", "Upload structural stability certificate from certified structural engineer.", False),
    ("R07", "Missing Electrical Safety Certificate", "Upload electrical safety clearance certificate.", False),
    ("R08", "Missing Faculty cadre and qualification records", "Upload updated faculty appointment letters and joining reports.", False),
    ("R09", "Missing AICTE approval letters of previous years", "Upload previous year Extension of Approval (EoA) copy.", False),
    ("R10", "Missing geotagged campus infrastructure photographs", "Upload geotagged photographs with GPS coordinates matching campus polygon.", False),
    ("R11", "Missing Barrier-free environment / Divyangjan compliance", "Upload lift/ramp accessibility compliance certificate.", False),
    ("R12", "Missing Anti-ragging committee constitution", "Upload anti-ragging committee notification and student affidavits.", False),
    ("R13", "Missing Internal Complaint Committee (ICC)", "Upload committee notification and annual compliance report.", False),
    ("R14", "Missing Grievance Redressal Mechanism", "Upload grievance portal link and committee details.", False),
]


@router.post("/precheck")
async def post_precheck(
    request: Request,
    file: Optional[UploadFile] = File(None),
):
    actor, role = resolve_actor_and_role(request)
    if role not in ("institution", "senior_officer"):
        raise HTTPException(status_code=403, detail="Role not permitted to run precheck")

    pdf_bytes: Optional[bytes] = None
    if file is not None:
        pdf_bytes = await file.read()
    else:
        content_type_header = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type_header:
            form = await request.form()
            form_file = form.get("file")
            if form_file and hasattr(form_file, "read"):
                pdf_bytes = await form_file.read()

    # If file was uploaded, check PDF header
    temp_path: Optional[Path] = None
    if pdf_bytes is not None:
        if not pdf_bytes.startswith(b"%PDF-"):
            return JSONResponse(status_code=415, content={"detail": "File must be a valid PDF document with %PDF- header"})
        from app.db import DB_DIR
        temp_dir = DB_DIR / "uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / "precheck_temp.pdf"
        temp_path.write_bytes(pdf_bytes)
        target_path = temp_path
    else:
        target_path = ensure_demo_sample()

    # Run scrutiny on Fire NOC
    scrutiny = run_fire_noc_checks(target_path)
    checks = scrutiny.get("checks", [])

    fixable: list[dict[str, str]] = []
    blocking: list[dict[str, str]] = []

    # Map Fire NOC issues
    for c in checks:
        cid = c["check_id"]
        outcome = c["outcome"]
        if outcome == "FAILED":
            if cid == "FIRE_NOC_COVERS_SEMESTER":
                fixable.append({
                    "requirement": "R05",
                    "issue": "Fire NOC ends 30 Sep 2027, inside the odd semester (ends 18-12-2027).",
                    "suggested_fix": "Upload renewed Fire NOC covering until 18-12-2027, or the renewal receipt.",
                })
            elif cid == "FN_NOT_EXPIRED":
                blocking.append({
                    "requirement": "R05",
                    "issue": "Fire NOC has expired before the review date.",
                    "suggested_fix": "Upload a valid, unexpired Fire NOC.",
                })
            else:
                blocking.append({
                    "requirement": "R05",
                    "issue": f"{c['title']}: {c['why']}",
                    "suggested_fix": "Upload official certificate issued by State Fire Service.",
                })
        elif outcome == "MANUAL_REVIEW":
            fixable.append({
                "requirement": "R05",
                "issue": f"{c['title']}: {c['why']}",
                "suggested_fix": "Ensure registration number and issuer records agree.",
            })

    # Always report missing documents against the 14-requirement checklist
    for req_id, issue_text, fix_text, is_blocking in CHECKLIST_REQS:
        item = {
            "requirement": req_id,
            "issue": issue_text,
            "suggested_fix": fix_text,
        }
        if is_blocking:
            blocking.append(item)
        else:
            fixable.append(item)

    # Clean up temp file if created
    if temp_path and temp_path.exists():
        try:
            temp_path.unlink()
        except OSError:
            pass

    # Writes ONLY one audit entry: precheck.run. NO official submission state is created.
    with get_db() as conn:
        append_audit_event(
            conn,
            "precheck.run",
            {"file": "fire_noc", "fixable": str(len(fixable)), "blocking": str(len(blocking))},
            actor=actor,
            ts=DEMO_NOW,
        )

    return {"fixable": fixable, "blocking": blocking}
