from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import get_db, append_audit_event, DEMO_NOW
from app.fixtures_layer import get_fixture_copy
from app.api.common import compute_live_state, resolve_actor_and_role

router = APIRouter(prefix="/findings", tags=["findings"])


class FindingDecisionRequest(BaseModel):
    action: str
    reason: Optional[str] = None


@router.get("")
async def get_findings():
    with get_db() as conn:
        live = compute_live_state(conn)
        return {
            "findings": live["fins"],
            "bundles": live["bundles"],
        }


@router.get("/{finding_id}/graph")
async def get_finding_graph(finding_id: str):
    graphs = get_fixture_copy("graphs")
    graph = graphs.get(finding_id, {"trace": []})
    return graph


@router.post("/{finding_id}/decision")
async def post_finding_decision(
    finding_id: str,
    body: FindingDecisionRequest,
    request: Request,
):
    actor, role = resolve_actor_and_role(request)
    if role != "senior_officer":
        raise HTTPException(status_code=403, detail="Role not permitted to decide findings")

    with get_db() as conn:
        live = compute_live_state(conn)
        target = next((f for f in live["fins"] if f["id"] == finding_id), None)

        if target and target.get("state") == "FAILED" and body.action != "request_info":
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "A FAILED finding cannot be accepted or dismissed. Ask the institution to fix it, or record a documented waiver."
                },
            )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO finding_decision (finding_id, action, reason, ts)
            VALUES (?, ?, ?, ?)
            """,
            (finding_id, body.action, body.reason, DEMO_NOW),
        )
        conn.commit()

        payload: dict[str, Any] = {"finding": finding_id}
        if body.reason:
            payload["reason"] = body.reason.strip()

        append_audit_event(
            conn,
            f"finding.{body.action}",
            payload,
            actor=actor,
            ts=DEMO_NOW,
        )

    return {"ok": True}
