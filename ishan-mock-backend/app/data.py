"""All fixtures for the SATYAPAN demo case (Shri Vidya Institute of Engineering & Technology, Pune),
built with the real engines, plus the mutable demo state. Matches the frontend screenshots exactly.
Call STORE.reset() to return to a clean demo."""
import copy, random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import engines as E, pdfs

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "pdfs"
APP_ID = "APP-0001"
IST = timezone(timedelta(hours=5, minutes=30))
DEMO_START = datetime(2027, 1, 12, 10, 30, tzinfo=IST)       # the frontend's "demo clock"
_BOOT = datetime.now(IST)
CAMPUS = (18.5204, 73.8567)
RULES = E.load_rules(ROOT / "rules" / "eoa_v1.yaml")
STAGES = ["intake", "read", "change", "check", "verify", "grade", "resolve", "awaiting_officer"]
ODD = (date(2027, 8, 2), date(2027, 12, 18)); EVEN = (date(2028, 1, 10), date(2028, 5, 13))
fmt = lambda d: d.strftime("%d-%m-%Y")

INSTITUTION = {"id": "SVIET", "name": "Shri Vidya Institute of Engineering & Technology", "city": "Pune", "state": "Maharashtra",
               "cycle": "AY 2027-28", "category": "EoA with intake change", "synthetic": True}

CHECKLIST = [  # ILLUSTRATIVE: confirm every row against APH 2024-27
    ("R01", "Trust / society registration"), ("R02", "Land ownership / lease"), ("R03", "Building completion certificate"),
    ("R04", "Built-up area vs intake"), ("R05", "Fire NOC valid through odd semester"), ("R06", "University affiliation"),
    ("R07", "Accreditation certificate"), ("R08", "Faculty list and full-time status"), ("R09", "Financial soundness (FDR)"),
    ("R10", "Infrastructure photographs"), ("R11", "Anti-ragging undertaking"), ("R12", "Internal Complaints Committee (POSH)"),
    ("R13", "Library and learning resources"), ("R14", "Accessibility (ramp / lift)")]
CHECKLIST = [{"id": i, "title": t} for i, t in CHECKLIST]

DOC_META = {  # which checklist rows each document satisfies in the pre-check dry run
    "D-01": ("Trust affidavit and undertakings", ["R01", "R11", "R12"]), "D-02": ("Land record (7/12 extract)", ["R02"]),
    "D-03": ("Architect-certified area statement", ["R03", "R04"]), "D-04": ("Fire NOC", ["R05"]),
    "D-05": ("University affiliation letter", ["R06"]), "D-06": ("Accreditation certificate (old format)", ["R07"]),
    "D-07": ("Faculty and library list", ["R08", "R13"]), "D-08": ("Financial soundness (FDR)", ["R09"]),
    "D-09": ("Building completion certificate", ["R03"]), "D-10": ("Infrastructure photographs", ["R10"]),
    "D-11": ("Accessibility certificate (ramp / lift)", ["R14"])}
SAMPLE_DOCS = [f"D-0{i}" for i in range(1, 9)]


def now(): return DEMO_START + (datetime.now(IST) - _BOOT)
def _now(): return now().isoformat(timespec="seconds")


def build_base():
    B = {}
    # ---- 80 claims bucketed by the REAL delta function: 62 unchanged / 9 with evidence / 3 unexplained / 6 new
    profile, claims, declared, supported, label, prev = {}, {}, set(), set(), {}, {}
    for i in range(62):
        k = f"misc.item_{i:02d}"; profile[k] = claims[k] = 100 + i; label[k] = f"Carried-forward item {i+1:02d}"
    evid = {"intake.total": (540, 600), "area.built_up_sqm": (1650, 1800), "area.carpet_sqm": (1500, 1720),
            "area.sanctioned_plan_sqm": (2200, 2400), "floors.built": (4, 5), "labs.count": (10, 12), "labs.area_sqm": (720, 900),
            "programme.CSE.intake": (180, 240), "programme.AIML.intake": (60, 120)}
    for k, (o, n) in evid.items(): profile[k], claims[k] = o, n; declared.add(k); supported.add(k)
    unexpl = {"faculty.count": (58, 83), "hostel.capacity": (240, 360), "library.titles": (18500, 26000)}
    for k, (o, n) in unexpl.items(): profile[k], claims[k] = o, n
    for i in range(6): claims[f"new.item_{i}"] = i; label[f"new.item_{i}"] = f"New item {i+1}"
    assert len(claims) == 80
    buckets = E.bucket(claims, profile, declared, supported)
    counts = {b: sum(v == b for v in buckets.values()) for b in set(buckets.values())}
    unch = sorted(k for k, b in buckets.items() if b == "UNCHANGED")
    sample = [{"claim": k, "seed": 2027, "reason": "random"} for k in random.Random(2027).sample(unch, 6)]
    N, n = len(unch), len(sample); bound = E.max_stale_consistent(N, n); pct = round(100 * bound / N)
    B["claims"] = {"claims": [{"key": k, "label": label.get(k, k), "value": claims[k], "previous": profile.get(k), "bucket": buckets[k],
                               "declared": k in declared} for k in claims],
                   "counts": counts, "sample": sample,
                   "sample_statement": {"N": N, "n": n, "stale_found": 0, "max_stale_plausible": bound, "upper_bound_pct": pct,
                       "text": f"{n} of {N} re-verified, 0 stale. 95% confidence: at most {bound} of {N} ({pct}%) are stale. "
                               "A sample is a tripwire, not a clearance."}}
    B["buckets"] = buckets

    # ---- rule inputs (v1 submission) + derived calendar values
    v1 = {"intake.total": 600, "area.built_up_sqm": 1800, "area.carpet_sqm": 1720, "area.sanctioned_plan_sqm": 2400,
          "faculty.count": 83, "floors.built": 5, "floors.noc_limit": 6, "labs.count": 12, "labs.area_sqm": 900}
    fire_till = date(2027, 9, 30)
    cal = {"fire.valid_till": fmt(fire_till), "fire.valid_till_ord": fire_till.toordinal(),
           "sem.odd_start": fmt(ODD[0]), "sem.odd_end": fmt(ODD[1]), "sem.odd_end_ord": ODD[1].toordinal()}
    B["inputs_v1"], B["calendar_inputs"] = v1, cal
    failed = {f["rule_id"]: f for f in E.evaluate(RULES, {**v1, **cal})}
    assert set(failed) == {"AREA_PER_SEAT", "CARPET_TO_BUILTUP", "FIRE_NOC_COVERS_SEMESTER"}, set(failed)

    # ---- findings F-011 .. F-025
    R = RULES["version"]
    def F(fid, rule, sev, state, title, expl, claimkeys, evidence=(), fix=None, ai=False, tag=None, trace_claim=None, queue="amber"):
        ev = [dict(e) for e in evidence]
        trace = [R, rule] + ([f"{ev[0]['doc']} p.{ev[0]['page']}", trace_claim, fid] if ev and trace_claim else [fid])
        return {"id": fid, "rule_id": rule, "rule_version": R, "severity": sev, "state": state, "title": title, "explanation": expl,
                "claims": claimkeys, "tag": tag, "bundle_id": None, "evidence": ev, "ai_read": ai, "fix": fix, "queue": queue, "trace": trace}
    name_expl = "Trust name differs between {a} and {b}. Spelling variants (Shri/Shree) are already normalised, so this is a different name."
    ev_name = lambda d, p: {"doc": d, "page": p, "text": pdfs.TRUST_A if d == "D-01" else pdfs.TRUST_B}
    trust_fix = "Upload one certified trust registration certificate that matches your AICTE record."
    fl = [
        F("F-011", "TRUST_NAME_CONSISTENT", "medium", E.MANUAL, "trust name consistent", name_expl.format(a="affidavit D-01", b="land record D-02"),
          ["trust.name"], [ev_name("D-01", 1), ev_name("D-02", 3)], trust_fix, True, "identity", "trust.name"),
        F("F-012", "TRUST_NAME_CONSISTENT", "medium", E.MANUAL, "trust name consistent", name_expl.format(a="affidavit D-01", b="AICTE record"),
          ["trust.name"], [ev_name("D-01", 1)], trust_fix, True, "identity", "trust.name"),
        F("F-013", "TRUST_NAME_CONSISTENT", "medium", E.MANUAL, "trust name consistent", name_expl.format(a="land record D-02", b="AICTE record"),
          ["trust.name"], [ev_name("D-02", 3)], trust_fix, True, "identity", "trust.name"),
        F("F-014", "AREA_PER_SEAT", "high", E.FAILED, "built-up area per seat", failed["AREA_PER_SEAT"]["explanation"], ["intake.total", "area.built_up_sqm"],
          [{"doc": "D-03", "page": 8, "text": "Built-up area: 1,800 sq m"}], "Upload the corrected architect-certified area statement.", True, "area", "intake.total", "red"),
        F("F-015", "CARPET_TO_BUILTUP", "medium", E.FAILED, "carpet to built-up", failed["CARPET_TO_BUILTUP"]["explanation"], ["area.carpet_sqm", "area.built_up_sqm"],
          [{"doc": "D-03", "page": 8, "text": "Carpet area: 1,720 sq m"}], "Upload the corrected architect-certified area statement.", False, "area", "area.carpet_sqm", "red"),
        F("F-016", "FIRE_NOC_COVERS_SEMESTER", "high", E.FAILED, "fire NOC covers semester", failed["FIRE_NOC_COVERS_SEMESTER"]["explanation"], ["fire.valid_till"],
          [{"doc": "D-04", "page": 1, "text": "Valid till 30-09-2027"}], "Upload the renewed Fire NOC (current one ends 30 Sep 2027).", False, "expired", "fire.valid_till", "red"),
        F("F-017", "CROSS_INSTITUTION_FACULTY_OVERLAP", "medium", E.MANUAL, "faculty overlap",
          "Possible full-time overlap F-7731: full-time at this institution from 01-04-2026 and at Sample College of Engineering, Ahilyanagar from 01-01-2027. Needs human confirmation.", ["faculty.token"]),
        F("F-018", "DELTA_UNEXPLAINED", "medium", E.MANUAL, "delta unexplained", "faculty.count changed 58 to 83 with no declared change.", ["faculty.count"],
          [{"doc": "D-07", "page": 4, "text": "Full-time faculty: 83"}], "Upload the approval or declaration that explains the faculty increase from 58 to 83.", False, "delta", "faculty.count"),
        F("F-019", "DELTA_UNEXPLAINED", "medium", E.MANUAL, "delta unexplained", "hostel.capacity changed 240 to 360 with no declared change.", ["hostel.capacity"],
          fix="Upload the approval that explains hostel capacity rising from 240 to 360.", tag="delta"),
        F("F-020", "DELTA_UNEXPLAINED", "medium", E.MANUAL, "delta unexplained", "library.titles changed 18,500 to 26,000 with no declared change.", ["library.titles"],
          fix="Upload the purchase record that explains library titles rising from 18,500 to 26,000.", tag="delta"),
        F("F-021", "CERT_FORMAT_UNUSUAL", "low", E.MANUAL, "unusual certificate format",
          "Accreditation certificate is in an older format and was read with low confidence. Valid but unusual: a human reads it; it is not failed.", ["accreditation.certificate"]),
        F("F-022", "ISSUER_SOURCE_UNAVAILABLE", "medium", E.UNABLE, "issuer source unavailable",
          "University affiliation could not be checked: the issuer source (simulated) did not respond. Unable to verify is not a failure.", ["university.affiliation"]),
        F("F-023", "DOCUMENT_REUSED", "medium", E.MANUAL, "scan reused",
          "A scan in this file has the same hash as a document in another institution's file. A hint for review, not proof.", ["documents.hash"]),
        F("F-024", "PHOTO_LOCATION", "medium", E.MANUAL, "photo location",
          "Two of six photos carry GPS about 38 km from the campus; two carry no location data (neutral).", ["infra.photos"]),
        F("F-025", "PEER_ANOMALY", "low", E.MANUAL, "unusual compared with peers",
          "Unusual compared with peers (same state and size band). Largest deviation: faculty growth. A prompt for review, not a conclusion.", ["faculty.growth"]),
    ]
    idf = [f for f in fl if f["rule_id"] == "TRUST_NAME_CONSISTENT"]
    bs = E.bundle(idf)
    for f in idf: f["bundle_id"] = bs[0]["id"]
    for f in fl:
        ladder = E.rank(f, set())
        top = ladder[0]
        f["next_step"] = {**top, "ladder": [{"kind": a["kind"], "label": a["label"], "cost": a["cost"]} for a in E.ACTIONS]}
    B["findings"] = fl
    top = E.rank(idf[0], set())[0]
    allowed = " ".join([f["id"] for f in idf] + [f["explanation"] for f in idf] + [R])
    llm_en = ("Your documents give the trust\u2019s name in three different ways (affidavit, land record and AICTE record). "
              "Please upload one certified trust registration certificate that matches your AICTE record, or tell us which "
              "document is out of date. Refs: F-011, F-012, F-013 (TRUST_NAME_CONSISTENT, eoa_v1).")
    text, source = E.letter(llm_en, allowed, bs[0], top, idf)
    B["bundles"] = [{**bs[0], "request_count": 1, "top_action": top,
                     "cheapest_next_step": "request one document (cost 2). One corrected trust registration certificate resolves all three.",
                     "letter": text, "letter_source": "llm_simulated" if source == "llm" else source,
                     "number_check": E.figure_check(text, allowed),
                     "letter_i18n": {
                         "hi": "आपके दस्तावेज़ों में ट्रस्ट का नाम तीन अलग-अलग तरीकों से लिखा है (शपथपत्र, भूमि अभिलेख और AICTE रिकॉर्ड)। कृपया एक प्रमाणित ट्रस्ट पंजीकरण प्रमाणपत्र अपलोड करें जो आपके AICTE रिकॉर्ड से मेल खाता हो, या बताएं कि कौन-सा दस्तावेज़ पुराना है। संदर्भ: F-011, F-012, F-013 (TRUST_NAME_CONSISTENT, eoa_v1)।",
                         "mr": "तुमच्या कागदपत्रांमध्ये ट्रस्टचे नाव तीन वेगवेगळ्या प्रकारे लिहिले आहे (प्रतिज्ञापत्र, जमीन अभिलेख आणि AICTE नोंद). कृपया तुमच्या AICTE नोंदीशी जुळणारे एक प्रमाणित ट्रस्ट नोंदणी प्रमाणपत्र अपलोड करा, किंवा कोणते कागदपत्र जुने आहे ते कळवा. संदर्भ: F-011, F-012, F-013 (TRUST_NAME_CONSISTENT, eoa_v1)."},
                     "note": "Canned for the demo. Real build: LLM call, numbers post-checked, template fallback."}]

    # ---- faculty overlap (hashed token)
    tk = E.token(b"demo-hmac-secret-not-for-production", "FAC-7731")
    ov = E.overlaps([
        {"token": tk, "institution_id": "SVIET", "kind": "full_time", "start": date(2026, 4, 1), "end": None},
        {"token": tk, "institution_id": "SCE-Ahilyanagar", "kind": "full_time", "start": date(2027, 1, 1), "end": None},
        {"token": "T-x", "institution_id": "SVIET", "kind": "visiting", "start": date(2027, 1, 1), "end": None}])
    B["network"] = [{**o, "display_ref": "F-7731", "finding": "F-017",
                     "institution_names": {"SVIET": INSTITUTION["name"], "SCE-Ahilyanagar": "Sample College of Engineering, Ahilyanagar"}} for o in ov]
    B["token"] = tk

    # ---- 40 peers + anomaly (mock; the real build uses a precomputed IsolationForest)
    rnd = random.Random(26261)
    firsts = ["Sahyadri", "Godavari", "Kaveri", "Narmada", "Deccan", "Malabar", "Vindhya", "Aravalli", "Nilgiri", "Konkan"]
    peers = []
    for i in range(40):
        intake = rnd.choice([300, 420, 540, 600, 720]); area = int(intake * rnd.uniform(3.4, 6.5))
        fac = max(8, int(intake / rnd.uniform(10, 24)))
        peers.append({"id": f"P-{i+1:02d}", "name": f"{rnd.choice(firsts)} Institute of Technology",
                      "state": rnd.choice(["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Uttar Pradesh"]),
                      "claims": {"intake.total": intake, "area.built_up_sqm": area, "faculty.count": fac}})
    B["peers"] = peers
    B["anomaly"] = {"institution": INSTITUTION["id"], "top_feature": "faculty_growth", "faculty_growth_pct": round(100 * (83 - 58) / 58),
                    "wording": "unusual compared with peers (same state and size band); a prompt for review, not a conclusion",
                    "text": "Anomaly model (precomputed, offline): unusual compared with peers (same state and size band); a prompt for "
                            "review, not a conclusion. Largest deviation: faculty growth.",
                    "precomputed_by": "MOCK: fixed result. Real build: IsolationForest trained offline on a synthetic cohort."}

    # ---- photos, timeline, alerts
    gps = [(18.5206, 73.8560), (18.5199, 73.8571), (18.862, 73.857), (18.862, 73.860), None, None]
    B["photos"] = {"campus": CAMPUS, "photos": [{"id": f"PH-{i+1}", "gps": g, "hint": E.photo_hint(g, CAMPUS)} for i, g in enumerate(gps)]}
    B["timeline"] = {"today": "2027-01-12",
                     "semesters": [{"name": "Odd semester AY 2027-28", "start": ODD[0].isoformat(), "end": ODD[1].isoformat()},
                                   {"name": "Even semester AY 2027-28", "start": EVEN[0].isoformat(), "end": EVEN[1].isoformat()}],
                     "pins": [{"doc": "Fire NOC", "label": "Fire NOC ends 30 Sep 2027 (inside semester)", "expires": fire_till.isoformat(),
                               "inside_semester": True, "finding": "F-016"}]}
    B["alerts"] = [
        {"id": "A-01", "kind": "expiry_in_semester", "title": "Document expires inside the semester", "owner_role": "reviewer", "due": "2027-01-19", "ref": "F-016", "status": "open"},
        {"id": "A-02", "kind": "source_unavailable", "title": "Issuer source unavailable", "owner_role": "reviewer", "due": "2027-01-15", "ref": "F-022", "status": "open"},
        {"id": "A-03", "kind": "anomaly", "title": "Unusual compared with peers", "owner_role": "reviewer", "due": "2027-01-19", "ref": "F-025", "status": "open"},
        {"id": "A-04", "kind": "bundle_awaiting_institution", "title": "Bundle awaiting institution response", "owner_role": "reviewer", "due": "2027-01-22", "ref": "B-01", "status": "open"}]

    # ---- requirement spine / checks (10 required)
    rows = [  # id, title, rung, required, stamp, doc, page, note, conflict
        ("R01", "Trust / society registration", 3, 3, E.PASSED, "D-01", 1, None, False),
        ("R02", "Land ownership / lease", 1, 2, E.CHK_CONFLICT, "D-02", 3, None, True),
        ("R03", "Building completion certificate", 2, 2, E.PASSED, "D-09", 1, None, False),
        ("R04", "Built-up area vs intake", 2, 2, E.FAILED, "D-03", 8, "3.0 sq m per seat vs 4.0 (illustrative)", False),
        ("R05", "Fire NOC valid through odd semester", 1, 1, E.FAILED, "D-04", 1, "ends 30 Sep 2027, semester ends 18 Dec 2027", False),
        ("R06", "University affiliation", 1, 3, E.UNABLE, "D-05", 1, None, False),
        ("R07", "Accreditation certificate", 0, 2, E.MANUAL, "D-06", 1, None, False),
        ("R08", "Faculty list and full-time status", 2, 2, E.MANUAL, "D-07", 4, "58 to 83, no declared change", False),
        ("R09", "Financial soundness (FDR)", 1, 1, E.PASSED, "D-08", 1, None, False),
        ("R10", "Infrastructure photographs", 1, 1, E.MANUAL, None, None, "2 of 6 photos far from campus, 2 without location", False)]
    cellmap = {E.PASSED: "complete", E.CHK_CONFLICT: "conflict", E.FAILED: "failed", E.UNABLE: "unable_to_verify", E.MANUAL: "needs_review"}
    findings_for = {"R02": ["F-011", "F-013"], "R04": ["F-014", "F-015"], "R05": ["F-016"], "R06": ["F-022"], "R07": ["F-021"],
                    "R08": ["F-017", "F-018"], "R10": ["F-024"]}
    B["coverage"] = [{"id": i, "requirement": t, "rung": r, "required_rung": q, "state": cellmap[st], "check_state": st, "doc": d, "page": p,
                      "note": n, "conflict": c, "findings": findings_for.get(i, []),
                      "source": "SIMULATED registry" if i in ("R01", "R06") else None, "expires": "2027-09-30" if i == "R05" else None}
                     for i, t, r, q, st, d, p, n, c in rows]
    B["checks"] = [{"id": i, "title": t, "required": True, "state": st} for i, t, r, q, st, d, p, n, c in rows]

    # ---- resubmission diff (v1 -> v2: corrected area statement)
    v2 = {**v1, "area.built_up_sqm": 2500, "area.carpet_sqm": 2100, "area.sanctioned_plan_sqm": 3000}
    chg = E.diff_claims(v1, v2); rr = E.rules_to_rerun(chg, E.dependency_map(RULES))
    old = [{"id": "F-014", "rule_id": "AREA_PER_SEAT"}, {"id": "F-015", "rule_id": "CARPET_TO_BUILTUP"}, {"id": "F-011", "rule_id": "TRUST_NAME_CONSISTENT"}]
    rec = E.reconcile(old, E.evaluate(RULES, {**v2, **cal}), rr)
    B["diff"] = {"from_version": 1, "to_version": 2, "changed": chg, "rules_rerun": rr, "findings": rec,
                 "values": {k: {"from": v1[k], "to": v2[k]} for k in chg},
                 "summary": {"values_changed": len(chg), "findings_resolved": sum(v == "resolved" for v in rec.values()),
                             "findings_pending": sum(v == "still_pending" for v in rec.values()), "dependent_checks_rerun": len(rr)}}

    # ---- ground truth (P01-P10) -> finding refs; eval is computed against live data by STORE.eval()
    B["ground_truth"] = [
        {"id": "P01", "problem": "Fire NOC expires inside the semester", "finding": "F-016"},
        {"id": "P02", "problem": "Area per seat 3.0 vs illustrative 4.0", "finding": "F-014"},
        {"id": "P03", "problem": "Trust name differs in three places", "finding": "F-011"},
        {"id": "P04", "problem": "Possible full-time overlap F-7731", "finding": "F-017"},
        {"id": "P05", "problem": "Faculty count 58 to 83 with no explanation", "finding": "F-018"},
        {"id": "P06", "problem": "Valid but unusual old-format certificate goes to manual review, not FAILED", "finding": "F-021"},
        {"id": "P07", "problem": "One QR-verified (rung 3) and one issuer source unavailable", "finding": "F-022"},
        {"id": "P08", "problem": "Scan reused in another institution's file", "finding": "F-023"},
        {"id": "P09", "problem": "Two photos far from campus, two without location", "finding": "F-024"},
        {"id": "P10", "problem": "Resubmission: 3 values changed, 2 findings resolved, 1 pending", "finding": "F-014"}]
    B["institution"] = INSTITUTION
    return B


class Store:
    def __init__(self): self.reset()

    def reset(self):
        self.base = build_base()
        self.boxes = pdfs.build(PDF_DIR)
        self.d = copy.deepcopy(self.base)
        self.waivers, self.log = [], []
        self.version, self.state, self.decision = 1, "awaiting_officer", None
        for ev, pl in (("application.submitted", {"app": APP_ID, "version": 1}),
                       ("stage.read", {"documents": 9, "rule_version": RULES["version"]}),
                       ("stage.check", {"findings": 15, "rules_sha256": RULES["sha256"][:12]})):
            self.audit("system", ev, pl)

    def audit(self, actor, event, payload): return E.chain_append(self.log, _now(), actor, event, payload)

    def open_findings(self): return [f for f in self.d["findings"] if f["state"] not in ("RESOLVED",)]

    def summary(self):
        fs = self.open_findings()
        red = [f["id"] for f in fs if f["queue"] == "red"] + [f["id"] for f in fs if f["rule_id"] == "DELTA_UNEXPLAINED"]
        amber = [f["id"] for f in fs if f["queue"] == "amber"]
        oc = E.open_checks(self.d["checks"], self.waivers)
        return {**self.d["claims"], "application_id": APP_ID, "institution": INSTITUTION, "version": self.version, "state": self.state,
                "overall_state": E.overall_state(self.d["checks"], self.waivers), "case_stamp": "MANUAL REVIEW" if oc else "READY FOR DECISION",
                "open_checks": oc, "required_checks_open": len(oc), "findings_open": len(fs),
                "alerts_open": sum(a["status"] == "open" for a in self.d["alerts"]),
                "queues": {"red": {"rules_failed": [f["id"] for f in fs if f["queue"] == "red"],
                                   "deltas": [f["id"] for f in fs if f["rule_id"] == "DELTA_UNEXPLAINED"], "count": len(red)},
                           "amber": {"findings": amber, "count": len(amber)}},
                "anomaly": self.d["anomaly"], "synthetic": True, "label": "Synthetic data, simulated connectors"}

    def checks(self):
        waived = {w["check_id"] for w in self.waivers if w["reason"].strip()}
        return [{**c, "waived": c["id"] in waived} for c in self.d["checks"]]

    def fixes(self):
        b = self.d["bundles"][0]; items = []
        for f in self.d["findings"]:
            if not f["fix"] or f["id"] in ("F-012", "F-013"): continue
            ids = b["finding_ids"] if f["id"] == "F-011" else [f["id"]]
            resolved = f["state"] == "RESOLVED"
            items.append({"finding": f["id"], "covers": ids, "action": f["fix"], "why": f["explanation"], "rule_id": f["rule_id"],
                          "rule_version": f["rule_version"], "bundle_id": f["bundle_id"], "upload_wired": f["id"] == "F-014",
                          "steps": [{"n": 1, "label": "Finding raised", "done": True}, {"n": 2, "label": "Explained", "done": True},
                                    {"n": 3, "label": "Fix listed", "done": True},
                                    {"n": 4, "label": "Resubmitted", "done": resolved},
                                    {"n": 5, "label": "Re-check", "done": resolved, "status": "resolved" if resolved else "pending"}]})
        return {"message": {"bundle": b["id"], "letter": b["letter"], "letter_i18n": b["letter_i18n"], "source": b["letter_source"],
                            "number_check": b["number_check"]}, "items": items}

    def eval(self):
        fs = {f["id"]: f for f in self.d["findings"]}; cov = {c["id"]: c for c in self.d["coverage"]}
        ph = [p["hint"]["status"] for p in self.d["photos"]["photos"]]
        d = self.d["diff"]["summary"]
        ok = {"P01": "F-016" in fs and self.d["timeline"]["pins"][0]["inside_semester"],
              "P02": "F-014" in fs and fs["F-014"]["rule_id"] == "AREA_PER_SEAT",
              "P03": len([f for f in fs.values() if f["rule_id"] == "TRUST_NAME_CONSISTENT"]) == 3 and len(self.d["bundles"]) == 1,
              "P04": len(self.d["network"]) == 1, "P05": self.d["buckets"]["faculty.count"] == "CHANGED_NO_EXPLANATION",
              "P06": cov["R07"]["state"] == "needs_review" and fs["F-021"]["state"] != E.FAILED,
              "P07": cov["R01"]["rung"] == 3 and cov["R06"]["state"] == "unable_to_verify",
              "P08": "F-023" in fs, "P09": ph.count("far_from_campus") == 2 and ph.count("no_location_data") == 2,
              "P10": (d["values_changed"], d["findings_resolved"], d["findings_pending"]) == (3, 2, 1)}
        table = [{**g, "result": "PASSED" if ok[g["id"]] else "FAILED"} for g in self.d["ground_truth"]]
        found = sum(r["result"] == "PASSED" for r in table)
        with_box = [f["id"] for f in fs.values() if f["evidence"] and all("page" in e for e in f["evidence"]) and f["trace"] and f["rule_version"]]
        without = [i for i in fs if i not in with_box]
        wrongly_failed = int(cov["R07"]["state"] == "failed" or fs["F-021"]["state"] == E.FAILED)
        return {"planted": table, "found": found, "total": len(table), "recall_pct": round(100 * found / len(table)),
                "valid_but_unusual_wrongly_failed": wrongly_failed,
                "findings_with_evidence": {"n": len(with_box), "of": len(fs), "ids": with_box},
                "findings_without_box": without,
                "note": "Synthetic results show that the workflow is correct. They are not a claim about accuracy on real institutions."}

    def resubmit(self):
        if self.version >= 2: return False
        self.version = 2
        for c in self.d["coverage"]:
            if c["id"] == "R04": c.update(state="complete", check_state=E.PASSED, note=None)
        for c in self.d["checks"]:
            if c["id"] == "R04": c["state"] = E.PASSED
        for f in self.d["findings"]:
            if self.d["diff"]["findings"].get(f["id"]) == "resolved": f["state"] = "RESOLVED"
        self.audit("institution", "application.resubmitted", {"version": 2, **self.d["diff"]["summary"]})
        return True


STORE = Store()
