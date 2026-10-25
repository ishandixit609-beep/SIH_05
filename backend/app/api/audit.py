from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from app.db import (
    get_db,
    get_audit_chain,
    tamper_audit_log,
    repair_audit_log,
)
from app.audit.chain import verify

router = APIRouter(tags=["audit"])


@router.get("/audit")
async def get_audit():
    with get_db() as conn:
        return get_audit_chain(conn)


@router.get("/audit/verify")
async def verify_audit():
    with get_db() as conn:
        chain = get_audit_chain(conn)
        broken_seq = verify(chain)
        head = chain[-1]["hash"] if chain else ""
        return {
            "intact": broken_seq is None,
            "entries": len(chain),
            "first_broken_seq": broken_seq,
            "head": head,
        }


@router.post("/audit/_tamper")
async def tamper_audit():
    with get_db() as conn:
        tamper_audit_log(conn)
    return {"ok": True}


@router.post("/audit/_repair")
async def repair_audit():
    with get_db() as conn:
        repair_audit_log(conn)
    return {"ok": True}
