"""ISHAN mock backend. Same URLs and shapes as the real FastAPI backend in the guide.
Run:  uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import asyncio, json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from . import engines as E
from .data import STORE, APP_ID, CHECKLIST, DOC_META, SAMPLE_DOCS, PDF_DIR, RULES, STAGES, _now, now

app = FastAPI(title="ISHAN mock backend (synthetic data, simulated connectors)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def label(request: Request, call_next):
    r = await call_next(request)
    r.headers["X-Data-Label"] = "Synthetic data, simulated connectors"
    return r


def _app_or_404(app_id: str):
    if app_id != APP_ID: raise HTTPException(404, f"unknown application {app_id}; the mock only knows {APP_ID}")


# ---------------------------------------------------------------- applications
@app.get("/api/health")
def health(): return {"ok": True, "synthetic": True, "app": APP_ID, "version": STORE.version}


@app.post("/api/applications")
async def create_application():
    STORE.audit("INSTITUTION", "application_submitted", {"app": APP_ID, "version": STORE.version})
    return {"id": APP_ID, "version": STORE.version, "state": "queued"}


@app.get("/api/applications")
def list_applications():
    return [{"id": APP_ID, "institution": STORE.d["institution"], "version": STORE.version, "state": STORE.state,
             "overall_state": E.overall_state(STORE.d["checks"], STORE.waivers),
             "open_findings": sum(f["state"] == "FAILED" for f in STORE.d["findings"]),
             "open_alerts": sum(a["status"] == "open" for a in STORE.d["alerts"])}]


@app.get("/api/applications/{app_id}")
def get_application(app_id: str):
    _app_or_404(app_id)
    return {"id": APP_ID, "institution": STORE.d["institution"], "version": STORE.version, "state": STORE.state,
            "decision": STORE.decision, "overall_state": E.overall_state(STORE.d["checks"], STORE.waivers)}


@app.get("/api/applications/{app_id}/events")
def events(app_id: str):
    """Polling-friendly array (matches the MSW contract). `at` = ms after submit."""
    _app_or_404(app_id)
    return [{"stage": s, "at": i * 1500} for i, s in enumerate(STAGES)]


@app.get("/api/applications/{app_id}/events/stream")
async def events_stream(app_id: str, delay: float = 1.5):
    """Same stages as Server-Sent Events, for a live stage rail."""
    _app_or_404(app_id)
    async def gen():
        for s in STAGES:
            await asyncio.sleep(delay)
            yield f"event: stage\ndata: {json.dumps({'stage': s})}\n\n"
        yield "event: done\ndata: {}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/applications/{app_id}/summary")
def summary(app_id: str): _app_or_404(app_id); return STORE.summary()


@app.get("/api/applications/{app_id}/claims")
def claims(app_id: str): _app_or_404(app_id); return STORE.d["claims"]


@app.get("/api/applications/{app_id}/coverage")
def coverage(app_id: str): _app_or_404(app_id); return STORE.d["coverage"]


@app.get("/api/applications/{app_id}/checks")
def checks(app_id: str):
    _app_or_404(app_id)
    return {"overall_state": E.overall_state(STORE.d["checks"], STORE.waivers), "checks": STORE.checks()}


@app.get("/api/applications/{app_id}/diff")
def diff(app_id: str): _app_or_404(app_id); return {**STORE.d["diff"], "applied": STORE.version >= 2}


@app.get("/api/applications/{app_id}/timeline")
def timeline(app_id: str): _app_or_404(app_id); return STORE.d["timeline"]


@app.get("/api/applications/{app_id}/photos")
def photos(app_id: str): _app_or_404(app_id); return STORE.d["photos"]


@app.get("/api/applications/{app_id}/anomaly")
def anomaly(app_id: str): _app_or_404(app_id); return STORE.d["anomaly"]


@app.post("/api/applications/{app_id}/resubmit")
def resubmit(app_id: str):
    """Institution uploads the corrected area document (v2). Runs selective revalidation."""
    _app_or_404(app_id)
    STORE.resubmit()
    return {"id": APP_ID, "version": STORE.version, "diff": {**STORE.d["diff"], "applied": True}}


@app.post("/api/applications/{app_id}/decision")
async def decision(app_id: str, request: Request):
    _app_or_404(app_id)
    body = await request.json()
    status, out = E.decide(body.get("action"), STORE.d["checks"], STORE.waivers)
    if status != 200: return JSONResponse(out, status_code=status)
    STORE.decision = body["action"]
    STORE.state = {"approve": "decided", "reject": "decided", "request_info": "awaiting_institution"}[body["action"]]
    STORE.audit(body.get("officer", "OFF-17"), "decision", {"action": body["action"]})
    return out


# ---------------------------------------------------------------- pre-check (institution side)
@app.get("/api/checklist")
def checklist(): return {"category": "EoA with intake change", "illustrative": True, "requirements": CHECKLIST}


@app.get("/api/documents")
def documents():
    return [{"id": d, "title": t, "covers": c, "sample": d in SAMPLE_DOCS, "file": f"/api/documents/{d}/file"}
            for d, (t, c) in DOC_META.items()]


@app.post("/api/precheck")
async def precheck(request: Request):
    """Dry run. Body (optional): {"uploaded": ["D-01", ...]}; default = the 8 sample documents. Creates no deficiency record."""
    try: uploaded = list((await request.json()).get("uploaded", SAMPLE_DOCS))
    except Exception: uploaded = list(SAMPLE_DOCS)
    covered = {r for d in uploaded for r in DOC_META.get(d, ("", []))[1]}
    rows = [{**r, "ok": r["id"] in covered, "docs": [d for d in uploaded if r["id"] in DOC_META.get(d, ("", []))[1]]} for r in CHECKLIST]
    gaps = [r for r in rows if not r["ok"]]
    warnings = [{"row": "R05", "kind": "expiry_in_semester", "text": "Fire NOC ends 30 Sep 2027, inside the odd semester (02-08-2027 to 18-12-2027)."}] if "D-04" in uploaded else []
    return {"rows": rows, "gaps": gaps, "warnings": warnings, "ready_to_submit": not gaps,
            "note": "Dry run reads your documents and tests only the missing and expired rules. Nothing is submitted officially."}


# ---------------------------------------------------------------- findings, bundles
@app.get("/api/findings")
def findings(): return STORE.d["findings"]


def _finding(fid):
    f = next((x for x in STORE.d["findings"] if x["id"] == fid), None)
    if not f: raise HTTPException(404, "finding not found")
    return f


@app.get("/api/findings/{fid}")
def finding(fid: str): return _finding(fid)


@app.get("/api/findings/{fid}/graph")
def finding_graph(fid: str):
    f = _finding(fid)
    nodes = [{"id": f"n{i}", "label": t} for i, t in enumerate(f["trace"])]
    edges = [{"from": f"n{i}", "to": f"n{i+1}"} for i in range(len(nodes) - 1)]
    return {"finding": fid, "nodes": nodes, "edges": edges}


@app.post("/api/findings/{fid}/decision")
async def finding_decision(fid: str, request: Request):
    """accept / dismiss only clear items marked for review. A FAILED rule needs a fix or a written waiver."""
    f = _finding(fid); b = await request.json()
    if b.get("action") not in ("accept", "dismiss", "request_info"): return JSONResponse({"error": "bad_action"}, 422)
    if b["action"] in ("accept", "dismiss") and f["state"] == E.FAILED:
        return JSONResponse({"error": "failed_needs_fix_or_waiver"}, 409)
    if b["action"] != "request_info": f["state"] = "REVIEWED"; f["review"] = b["action"]
    STORE.audit(b.get("officer", "OFF-17"), "finding." + b["action"], {"finding": fid})
    return {"id": f["id"], "action": b["action"], "recorded_as": "officer decision"}


@app.get("/api/bundles")
def bundles(): return STORE.d["bundles"]


@app.get("/api/bundles/{bid}/letter")
def bundle_letter(bid: str):
    b = next((x for x in STORE.d["bundles"] if x["id"] == bid), None)
    if not b: raise HTTPException(404, "bundle not found")
    return {"bundle": bid, "letter": b["letter"], "letter_i18n": b["letter_i18n"], "source": b["letter_source"],
            "number_check": b["number_check"], "status": "draft for officer review"}


@app.post("/api/bundles/{bid}/send")
def bundle_send(bid: str):
    if not any(x["id"] == bid for x in STORE.d["bundles"]): raise HTTPException(404, "bundle not found")
    STORE.audit("OFF-17", "request.sent", {"bundle": bid}); STORE.state = "awaiting_institution"
    return {"ok": True, "sent_to": "institution", "bundle": bid}


# ---------------------------------------------------------------- documents, network, alerts
@app.get("/api/documents/{did}/file")
def document_file(did: str):
    p = PDF_DIR / f"{did}.pdf"
    if not p.exists(): raise HTTPException(404, "document not found")
    return FileResponse(p, media_type="application/pdf")


@app.get("/api/documents/{did}/boxes")
def document_boxes(did: str):
    if did not in STORE.boxes: raise HTTPException(404, "document not found")
    return STORE.boxes[did]


@app.get("/api/network/faculty/{token}")
def network(token: str): return STORE.d["network"]


@app.get("/api/alerts")
def alerts(): return STORE.d["alerts"]


# ---------------------------------------------------------------- waivers + audit (real hashing)
@app.get("/api/waivers")
def list_waivers(): return STORE.waivers


@app.post("/api/waivers")
async def waiver(request: Request):
    w = await request.json()
    if not str(w.get("reason", "")).strip(): return JSONResponse({"error": "reason_required"}, 422)
    if w.get("check_id") not in {c["id"] for c in STORE.d["checks"]}: return JSONResponse({"error": "unknown_check"}, 404)
    rec = {"check_id": w["check_id"], "officer": w.get("officer", "OFF-17"), "reason": w["reason"].strip(), "ts": _now()}
    STORE.waivers.append(rec)
    STORE.audit(rec["officer"], "waiver", rec)
    return {"ok": True, "overall_state": E.overall_state(STORE.d["checks"], STORE.waivers)}


@app.get("/api/audit")
def audit(): return STORE.log


@app.get("/api/audit/verify")
def audit_verify(): return E.chain_verify(STORE.log)


@app.post("/api/audit/tamper")
def audit_tamper():
    """DEMO ONLY: corrupt entry #2 so Verify reports the break."""
    if len(STORE.log) > 1: STORE.log[1]["payload"]["tampered"] = True
    return {"ok": True}


# ---------------------------------------------------------------- rules + eval + dev
@app.get("/api/rules")
def rules(): return RULES


@app.post("/api/rules/simulate")
async def rules_simulate(request: Request):
    b = await request.json()
    if b.get("rule_id") not in {r["id"] for r in RULES["rules"]}: return JSONResponse({"error": "unknown_rule"}, 404)
    return E.simulate(RULES, STORE.d["peers"], b["rule_id"], b["param"], b["value"])


@app.get("/api/peers")
def peers(): return STORE.d["peers"]


@app.get("/api/eval/summary")
def eval_summary(): return STORE.eval()


@app.post("/api/dev/reset")
def reset():
    """Return the demo to its starting state (v1, no waivers, intact chain)."""
    STORE.reset(); return {"ok": True}


@app.get("/api/eval/ground-truth")
def ground_truth(): return STORE.d["ground_truth"]


@app.get("/api/clock")
def clock(): return {"now": now().isoformat(timespec="seconds"), "label": "demo clock", "tz": "Asia/Kolkata"}


@app.get("/api/applications/{app_id}/fixes")
def fixes(app_id: str):
    """Institution desk: what we need from you (one request per root cause) with the 5-step tracker."""
    _app_or_404(app_id); return STORE.fixes()


VERSIONS = {"v1.1": {"AREA_PER_SEAT": {"min_sqm_per_seat": 3.0}}}   # illustrative second rule version


@app.post("/api/replay")
async def replay(request: Request):
    """Re-run the stored case under another rule version. Applies nothing; the stored decision is untouched."""
    b = await request.json(); f = _finding(b.get("finding_id", "F-014")); ver = b.get("rule_version", "v1.1")
    if ver not in VERSIONS: return JSONResponse({"error": "unknown_rule_version"}, 404)
    inputs = {**STORE.base["inputs_v1"], **STORE.base["calendar_inputs"]}
    again = [x for x in E.evaluate(RULES, inputs, VERSIONS[ver]) if x["rule_id"] == f["rule_id"]]
    return {"finding": f["id"], "rule_id": f["rule_id"], "stored": {"rule_version": f["rule_version"], "state": f["state"]},
            "replayed": {"rule_version": ver + " (illustrative)", "state": "FAILED" if again else "PASSED",
                         "explanation": again[0]["explanation"] if again else f"Passes under {ver}: norm {VERSIONS[ver][f['rule_id']]}."},
            "changed": bool(not again), "stored_decision_untouched": True}


@app.post("/api/guard/evaluate")
async def guard_evaluate(request: Request):
    """Guard Lab: the real no-silent-pass logic over checks/waivers the page sends."""
    b = await request.json(); checks, waivers = b.get("checks", []), b.get("waivers", [])
    o = E.open_checks(checks, waivers)
    return {"overall_state": E.overall_state(checks, waivers), "open": o, "passed": sum(c["state"] == E.PASSED for c in checks), "total": len(checks)}
