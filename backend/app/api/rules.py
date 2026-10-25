from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.fixtures_layer import get_fixture_copy, load_fixture
from app.engines.bengine import simulate

router = APIRouter(tags=["rules"])


class SimulateRequest(BaseModel):
    rule_id: str
    param: str
    value: float


@router.get("/rules")
async def get_rules():
    # Contract: GET /api/rules must return rules.json exactly as is
    return load_fixture("rules")


@router.post("/rules/simulate")
async def post_simulate_rule(body: SimulateRequest):
    rules_data = load_fixture("rules")
    peers = load_fixture("peers")

    target_rule = next((r for r in rules_data.get("rules", []) if r["id"] == body.rule_id), None)
    if not target_rule:
        raise HTTPException(status_code=404, detail=f"Rule {body.rule_id} not found")

    res = simulate(target_rule, peers, body.param, body.value)
    return {
        **res,
        "total": len(peers),
        "first10": res["first10"],
    }


@router.post("/replay")
async def post_replay():
    return get_fixture_copy("replay")
