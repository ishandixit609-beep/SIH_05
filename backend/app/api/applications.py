from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from typing import Any, Optional
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import (
    get_db,
    DEMO_NOW,
    STAGES,
    append_audit_event,
    ensure_demo_sample,
    DB_DIR,
)
from app.fixtures_layer import get_fixture_copy
from app.api.common import compute_live_state, resolve_actor_and_role
from app.engines.guard import make_waiver, decide, GuardBlocked
from app.pipeline.runner import execute_pipeline

router = APIRouter(prefix="/applications", tags=["applications"])

UPLOADS_DIR = DB_DIR / "uploads"


class WaiverRequest(BaseModel):
    check_id: str
    reason: str


class DecisionRequest(BaseModel):
    action: str


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def post_application(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
):
    actor, _ = resolve_actor_and_role(request)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    pdf_bytes: bytes
    if file is not None:
        content_type = file.content_type or ""
        pdf_bytes = await file.read()
    else:
        # Check if multipart form was sent without FastAPI File binding
        content_type_header = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type_header:
            form = await request.form()
            form_file = form.get("file")
            if form_file and hasattr(form_file, "read"):
                pdf_bytes = await form_file.read()
            else:
                sample_path = ensure_demo_sample()
                pdf_bytes = sample_path.read_bytes()
        else:
            # Empty body or JSON: use default demo sample
            sample_path = ensure_demo_sample()
            pdf_bytes = sample_path.read_bytes()

    # Verify magic bytes %PDF-
    if not pdf_bytes.startswith(b"%PDF-"):
        return JSONResponse(
            status_code=415,
            content={"detail": "File must be a valid PDF document starting with %PDF-"},
        )

    # Verify size <= 5 MB
    if len(pdf_bytes) > 5 * 1024 * 1024:
        return JSONResponse(
            status_code=413,
            content={"detail": "File size exceeds 5 MB limit"},
        )

    # Save to data/uploads/<uuid>.pdf (never trust client filename)
    target_filename = f"{uuid.uuid4().hex}.pdf"
    target_path = UPLOADS_DIR / target_filename
    target_path.write_bytes(pdf_bytes)

    doc_sha = hashlib.sha256(pdf_bytes).hexdigest()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM document WHERE id = 'D-04'")
        row = cursor.fetchone()
        current_version = row["version"] if row else 0
        new_version = current_version + 1

        cursor.execute(
            """
            INSERT OR REPLACE INTO document (id, sha256, path, version, doc_type)
            VALUES ('D-04', ?, ?, ?, 'fire_noc')
            """,
            (doc_sha, str(target_path), new_version),
        )
        cursor.execute(
            """
            UPDATE application_run
            SET version = ?, completed = 0, done = 0, started_at = ?
            WHERE app_id = 'APP-0001'
            """,
            (new_version, time.time()),
        )
        conn.commit()

    # Trigger background pipeline
    background_tasks.add_task(
        execute_pipeline,
        app_id="APP-0001",
        pdf_path=target_path,
        doc_sha256=doc_sha,
        doc_version=new_version,
    )

    return {"id": "APP-0001", "state": "queued"}


@router.get("/{app_id}/events")
async def get_application_events(app_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT stages, completed, done, started_at FROM application_run WHERE app_id = ?", (app_id,))
        row = cursor.fetchone()
        if row:
            stages = json.loads(row["stages"])
            completed = row["completed"]
            done = bool(row["done"])
            return {"stages": stages, "completed": completed, "done": done}
        return {"stages": STAGES, "completed": len(STAGES), "done": True}


@router.get("/{app_id}/scrutiny")
async def get_application_scrutiny(app_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version, sha256 FROM document WHERE id = 'D-04'")
        doc_row = cursor.fetchone()
        doc_version = doc_row["version"] if doc_row else 1
        doc_sha = doc_row["sha256"] if doc_row else ""

        live = compute_live_state(conn)
        fields = live["scrutiny_fields"]
        checks = live["scrutiny_checks"]

        verified_ok = [c["check_id"] for c in checks if c["outcome"] == "PASSED"]
        flagged = [c["check_id"] for c in checks if c["outcome"] in ("FAILED", "MANUAL_REVIEW")]
        could_not_verify = [c["check_id"] for c in checks if c["outcome"] == "UNABLE_TO_VERIFY"]

        return {
            "document": {
                "id": "D-04",
                "type": "Fire NOC",
                "sha256": doc_sha,
                "version": doc_version,
            },
            "fields": fields,
            "checks": checks,
            "groups": {
                "verified_ok": verified_ok,
                "flagged": flagged,
                "could_not_verify": could_not_verify,
            },
            "simulated": ["issuer_registry"],
            "workflow": {
                "computed": ["D-04", "R05", "F-016"],
                "fixture_backed": [
                    "R01", "R02", "R03", "R04", "R06", "R07",
                    "R08", "R09", "R10", "R11", "R12", "R13", "R14"
                ],
                "missing": [],
            },
        }


@router.get("/{app_id}/summary")
async def get_application_summary(app_id: str):
    with get_db() as conn:
        live = compute_live_state(conn)
        base_summary = get_fixture_copy("summary")
        open_findings = len([f for f in live["fins"] if not f.get("resolved") and not f.get("decision")])
        return {
            **base_summary,
            "overall": live["overall"],
            "open_checks": live["open_checks"],
            "findings_open": open_findings,
            "version": 2 if live["resubmitted"] else 1,
        }


@router.get("/{app_id}/coverage")
async def get_application_coverage(app_id: str):
    with get_db() as conn:
        live = compute_live_state(conn)
        reqs_with_waiver = [
            {**r, "waived": r["id"] in live["waivers"]} for r in live["reqs"]
        ]
        return {
            "requirements": reqs_with_waiver,
            "checks": live["checks"],
            "overall": live["overall"],
            "open_checks": live["open_checks"],
            "waivers": live["waivers"],
        }


@router.get("/{app_id}/claims")
async def get_application_claims(app_id: str):
    return get_fixture_copy("claims")


@router.get("/{app_id}/diff")
async def get_application_diff(app_id: str):
    return get_fixture_copy("diff")


@router.get("/{app_id}/timeline")
async def get_application_timeline(app_id: str):
    return get_fixture_copy("timeline")


@router.get("/{app_id}/photos")
async def get_application_photos(app_id: str):
    from app.engines.geo import compute_photo_statuses
    data = get_fixture_copy("photos")
    campus_polygon = data.get("campus_polygon", [])
    photos = data.get("photos", [])
    return {
        "campus_polygon": campus_polygon,
        "photos": compute_photo_statuses(campus_polygon, photos),
    }


@router.post("/{app_id}/waivers")
async def post_application_waiver(app_id: str, body: WaiverRequest, request: Request):
    actor, role = resolve_actor_and_role(request)
    try:
        w = make_waiver(body.check_id, actor, role, body.reason, DEMO_NOW)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO waiver (check_id, officer, reason, ts)
            VALUES (?, ?, ?, ?)
            """,
            (w["check_id"], w["officer"], w["reason"], w["ts"]),
        )
        conn.commit()
        append_audit_event(
            conn,
            "waiver.recorded",
            {"check": w["check_id"], "reason": w["reason"]},
            actor=actor,
            ts=DEMO_NOW,
        )
    return w


@router.post("/{app_id}/decision")
async def post_application_decision(app_id: str, body: DecisionRequest, request: Request):
    actor, role = resolve_actor_and_role(request)
    if role != "senior_officer":
        raise HTTPException(status_code=403, detail="Role not permitted to make application decision")

    with get_db() as conn:
        live = compute_live_state(conn)
        try:
            res = decide(body.action, live["checks"], live["waivers"])
        except GuardBlocked as e:
            return JSONResponse(
                status_code=409,
                content={"detail": "Seal withheld: required checks are open.", "open_checks": e.open_checks},
            )

        append_audit_event(
            conn,
            f"decision.{body.action}",
            {"app": app_id},
            actor=actor,
            ts=DEMO_NOW,
        )
    return res


@router.post("/{app_id}/resubmit")
async def post_application_resubmit(
    app_id: str,
    request: Request,
    file: Optional[UploadFile] = File(None),
):
    actor, role = resolve_actor_and_role(request)
    if role not in ("institution", "senior_officer"):
        raise HTTPException(status_code=403, detail="Role not permitted to resubmit application")

    with get_db() as conn:
        cursor = conn.cursor()

        # Handle optional PDF upload on resubmit
        pdf_bytes = None
        if file is not None:
            pdf_bytes = await file.read()
        elif "multipart/form-data" in request.headers.get("content-type", ""):
            form = await request.form()
            form_file = form.get("file")
            if form_file and hasattr(form_file, "read"):
                pdf_bytes = await form_file.read()

        if pdf_bytes and pdf_bytes.startswith(b"%PDF-"):
            UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
            target_filename = f"resubmit_{uuid.uuid4().hex}.pdf"
            target_path = UPLOADS_DIR / target_filename
            target_path.write_bytes(pdf_bytes)
            doc_sha = hashlib.sha256(pdf_bytes).hexdigest()

            cursor.execute(
                "INSERT OR REPLACE INTO document (id, sha256, path, version, doc_type) VALUES ('D-04', ?, ?, 2, 'fire_noc')",
                (doc_sha, str(target_path)),
            )
            from app.checks.fire_noc import run_fire_noc_checks
            scrut = run_fire_noc_checks(target_path)
            cursor.execute(
                """
                INSERT OR REPLACE INTO scrutiny_result (app_id, doc_id, sha256, version, fields, checks, updated_at)
                VALUES (?, 'D-04', ?, 2, ?, ?, ?)
                """,
                (app_id, doc_sha, json.dumps(scrut["fields"]), json.dumps(scrut["checks"]), time.time()),
            )

        cursor.execute("UPDATE application_state SET resubmitted = 1, version = 2 WHERE app_id = ?", (app_id,))
        conn.commit()
        append_audit_event(
            conn,
            "application.resubmitted",
            {"version": "2"},
            actor=actor if role == "institution" else "institution",
            ts=DEMO_NOW,
        )
    return get_fixture_copy("diff")
