"""Small, real engines. Same logic as the ISHAN guide's Python/TS modules, kept in one file for the mock."""
import hashlib, hmac, json, re
from datetime import date
from math import comb, radians, sin, cos, asin, sqrt
import yaml
from dateutil import parser as dparse
from simpleeval import SimpleEval

# ---------------- rung + cell state ----------------
CONFLICT = "conflict"

def achieved_rung(c):
    if c.get("record_match") is False or c.get("adapter_status") == "mismatch": return CONFLICT
    if c.get("adapter_status") == "verified": return 3
    if c.get("record_match") is True: return 2
    if c.get("uploaded") and c.get("confidence", 0) >= c.get("threshold", 0.85): return 1
    return 0

def cell_state(achieved, required, rules_pass, adapter_status=None, expired=False, uploaded=False):
    if achieved == CONFLICT: return "needs_review"
    if adapter_status == "source_unavailable" and achieved < required: return "unable_to_verify"
    if expired: return "missing" if achieved == 0 and not uploaded else "needs_review"
    if achieved == 0: return "needs_review" if uploaded else "missing"
    if achieved >= required and rules_pass: return "complete"
    return "partial"

# ---------------- No-Silent-Pass guard ----------------
PASSED, FAILED, MANUAL, NOT_CONFIGURED, UNABLE = "PASSED", "FAILED", "MANUAL REVIEW", "NOT CONFIGURED", "UNABLE TO VERIFY"
CHK_CONFLICT = "CONFLICT"

def open_checks(checks, waivers):
    waived = {w["check_id"] for w in waivers if w.get("reason", "").strip()}
    return [c for c in checks if c["required"] and c["state"] != PASSED and c["id"] not in waived]

def overall_state(checks, waivers):
    return "REVIEW INCOMPLETE" if open_checks(checks, waivers) else "READY FOR DECISION"

def decide(action, checks, waivers):
    """Returns (http_status, body). approve is blocked while required checks are open and unwaived."""
    if action not in ("approve", "reject", "request_info"):
        return 422, {"error": "bad_action"}
    if action == "approve":
        o = open_checks(checks, waivers)
        if o: return 409, {"error": "open_checks", "open": o}
    return 200, {"action": action, "recorded_as": "officer decision"}

# ---------------- audit chain ----------------
GENESIS = "0" * 64
def canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def chain_append(log, ts, actor, event, payload):
    prev = log[-1]["hash"] if log else GENESIS
    body = {"seq": len(log) + 1, "ts": ts, "actor": actor, "event": event, "payload": payload}
    log.append({**body, "prev_hash": prev, "hash": hashlib.sha256((prev + canon(body)).encode()).hexdigest()})
    return log[-1]

def chain_verify(log):
    prev = GENESIS
    for e in log:
        body = {k: e[k] for k in ("seq", "ts", "actor", "event", "payload")}
        if e["prev_hash"] != prev or e["hash"] != hashlib.sha256((prev + canon(body)).encode()).hexdigest():
            return {"intact": False, "first_broken_seq": e["seq"]}
        prev = e["hash"]
    return {"intact": True, "entries": len(log), "head": prev}

# ---------------- delta / diff ----------------
def _norm(key, v):
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip()
    if key.endswith(("valid_till", "valid_from", "date")): return dparse.parse(s, dayfirst=True).date()
    return " ".join(s.lower().split())

def _same(key, a, b):
    a, b = _norm(key, a), _norm(key, b)
    if isinstance(a, float) and isinstance(b, float): return abs(a - b) <= 1e-6 * max(1, abs(a))
    return a == b

def bucket(claims, profile, declared, supported):
    out = {}
    for k, v in claims.items():
        if k not in profile: out[k] = "NEW"
        elif _same(k, v, profile[k]): out[k] = "UNCHANGED"
        elif k in declared and k in supported: out[k] = "CHANGED_WITH_EVIDENCE"
        else: out[k] = "CHANGED_NO_EXPLANATION"
    return out

def diff_claims(v1, v2): return sorted(k for k in set(v1) | set(v2) if v1.get(k) != v2.get(k))

def dependency_map(ruleset):
    dep = {}
    for r in ruleset["rules"]:
        for i in r["inputs"]: dep.setdefault(i, set()).add(r["id"])
    return dep

def rules_to_rerun(changed, dep): return sorted({r for k in changed for r in dep.get(k, ())})

def reconcile(old_findings, new_findings, reran):
    new_ids = {f["rule_id"] for f in new_findings}
    return {f["id"]: ("still_pending" if f["rule_id"] in new_ids else "resolved") if f["rule_id"] in reran else "still_pending"
            for f in old_findings}

# ---------------- sampling bound ----------------
def max_stale_consistent(N, n, alpha=0.05):
    last_ok = 0
    for K in range(N + 1):
        if comb(N - K, n) / comb(N, n) > alpha: last_ok = K
        else: break
    return last_ok

# ---------------- B-engine ----------------
def load_rules(path):
    txt = open(path, encoding="utf-8").read()
    d = yaml.safe_load(txt); d["sha256"] = hashlib.sha256(txt.encode()).hexdigest(); return d

def evaluate(ruleset, claims, overrides=None):
    out, flat = [], {k.replace(".", "_"): v for k, v in claims.items()}
    for r in ruleset["rules"]:
        if not all(i in claims for i in r["inputs"]): continue
        params = {**r.get("params", {}), **(overrides or {}).get(r["id"], {})}
        names = {**flat, **{f"params_{k}": v for k, v in params.items()}}
        ev = SimpleEval(names=names)
        if not bool(ev.eval(r["expr"])):
            ctx = {**names, "value": ev.eval(r["value_expr"]) if r.get("value_expr") else None}
            out.append({"rule_id": r["id"], "rule_version": ruleset["version"], "severity": r["severity"],
                        "state": "FAILED", "claims": r["inputs"], "clause": r.get("clause"),
                        "explanation": r["message"].format(**ctx)})
    return out

def simulate(ruleset, peers, rule_id, param, value):
    changed = []
    for p in peers:
        before = any(f["rule_id"] == rule_id for f in evaluate(ruleset, p["claims"]))
        after = any(f["rule_id"] == rule_id for f in evaluate(ruleset, p["claims"], {rule_id: {param: value}}))
        if before != after: changed.append(p["id"])
    return {"count": len(changed), "first10": changed[:10]}   # applies nothing

# ---------------- cross-institution + hints ----------------
def token(secret: bytes, raw_id: str):
    return "T-" + hmac.new(secret, raw_id.strip().upper().encode(), hashlib.sha256).hexdigest()[:12]

def _overlap(a_s, a_e, b_s, b_e):
    return max(a_s, b_s) <= min(a_e or date.max, b_e or date.max)

def overlaps(appts):
    ft = [a for a in appts if a["kind"] == "full_time"]; out = []
    for i, a in enumerate(ft):
        for b in ft[i + 1:]:
            if a["token"] == b["token"] and a["institution_id"] != b["institution_id"] and _overlap(a["start"], a["end"], b["start"], b["end"]):
                out.append({"token": a["token"], "a": a, "b": b, "label": "Possible overlap, needs human confirmation"})
    return out

def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = radians(lat1), radians(lat2)
    a = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * asin(sqrt(a))

def photo_hint(gps, campus, limit_km=5):
    if gps is None: return {"status": "no_location_data", "tone": "neutral"}
    d = haversine_km(*gps, *campus)
    return {"status": "within_campus" if d <= limit_km else "far_from_campus", "distance_km": round(d, 1),
            "tone": "review" if d > limit_km else "ok"}

# ---------------- C-engine, bundler, copilot ----------------
SEV_W = {"high": 10, "medium": 5, "low": 2}
ACTIONS = [{"kind": "read_qr", "label": "read QR", "cost": 1, "impact": 3, "needs": ["qr_present"]},
           {"kind": "request_one_document", "label": "request one document", "cost": 2, "impact": 3, "needs": []},
           {"kind": "query_issuer", "label": "query issuer", "cost": 3, "impact": 5, "needs": ["issuer_source"]},
           {"kind": "physical_inspection", "label": "physical inspection", "cost": 10, "impact": 8, "needs": []}]

def rank(finding, ctx, actions=ACTIONS):
    ok = [dict(a) for a in actions if set(a.get("needs", [])) <= ctx]
    sw = SEV_W[finding["severity"]]
    scored = sorted(ok, key=lambda a: (a["cost"], -a["impact"]))
    for a in scored:
        a["reason"] = ("No QR or issuer source exists" if not ({"qr_present", "issuer_source"} & ctx)
                       else f"cost {a['cost']} (cheapest available), impact {a['impact']}, finding severity weight {sw}")
    return scored

LABELS = {"identity": "Identity details differ", "area": "Area and intake inconsistent",
          "expired": "Certificate set expired", "missing": "Document set missing"}

def bundle(findings):
    parent = {f["id"]: f["id"] for f in findings}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i, a in enumerate(findings):
        for b in findings[i + 1:]:
            if set(a["claims"]) & set(b["claims"]) or (a.get("signature") and a.get("signature") == b.get("signature")):
                parent[find(a["id"])] = find(b["id"])
    groups = {}
    for f in findings: groups.setdefault(find(f["id"]), []).append(f)
    out = []
    for fs in groups.values():
        if len(fs) < 2: continue
        out.append({"id": f"B-{len(out)+1:02d}", "label": LABELS.get(fs[0].get("tag", "identity"), "Related findings"),
                    "finding_ids": [f["id"] for f in fs]})
    return out

NUM = re.compile(r"\d[\d,]*\.?\d*")
def numbers_ok(output, allowed_text):
    allowed = {n.strip(",.") for n in NUM.findall(allowed_text)}
    return all(n.strip(",.") in allowed for n in NUM.findall(output))

def template_letter(bundle_, top_action, findings):
    lines = [f"Regarding: {bundle_['label']}", "Please provide the following:"]
    lines += [f"- {f['explanation']} (ref {f['id']}, rule {f['rule_id']})" for f in findings]
    lines.append(f"Suggested next step: {top_action['kind'].replace('_', ' ')}.")
    lines.append("This is a request for clarification, not a decision.")
    return "\n".join(lines)

def figure_check(text, allowed_text):
    """Stamp data: how many figures the letter contains and whether all come from the cited findings."""
    figs = NUM.findall(text)
    return {"figures": len(figs), "passed": numbers_ok(text, allowed_text)}

def letter(llm_text, allowed_text, bundle_, top_action, findings):
    if llm_text and numbers_ok(llm_text, allowed_text): return llm_text, "llm"
    return template_letter(bundle_, top_action, findings), "template_fallback"
