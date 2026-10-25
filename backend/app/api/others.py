from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException

from app.db import get_db, reset_all_state
from app.fixtures_layer import get_fixture_copy, load_fixture

router = APIRouter(tags=["others"])


@router.get("/alerts")
async def get_alerts():
    return get_fixture_copy("alerts")


@router.get("/network/faculty/{token}")
async def get_faculty_network(token: str):
    from app.engines.crossinst import build_faculty_network
    with get_db() as conn:
        return build_faculty_network(conn, token)


@router.get("/eval/summary")
async def get_eval_summary():
    truth = load_fixture("ground_truth")
    found = load_fixture("findings_ids")
    flagged_ids = set(found.get("flagged_ids", []))
    planted = truth.get("planted", [])
    rows = [{**p, "found": p["id"] in flagged_ids} for p in planted]
    found_count = len([r for r in rows if r["found"]])
    return {
        "rows": rows,
        "planted": len(rows),
        "found": found_count,
        "false_positives": found.get("false_positives_on_valid_but_unusual", 0),
    }


@router.post("/_reset")
async def post_reset():
    if os.getenv("ENV") == "production":
        raise HTTPException(status_code=403, detail="Reset is disabled in production")
    with get_db() as conn:
        reset_all_state(conn)
    return {"ok": True}
