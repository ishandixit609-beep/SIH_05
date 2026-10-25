# SATYAPAN mock backend (PS5 / SIH26261)

FastAPI server whose data matches the SATYAPAN frontend screens exactly: Shri Vidya Institute of Engineering & Technology, Pune,
APP-0001, AY 2027-28, demo clock 12 Jan 2027 10:30 IST, findings F-011..F-025, 10 spine checks (7 open), 4 alerts, 14-row pre-check.
Real code: guard + waivers (409), rung/delta bucketing, rules evaluator + rule dial + replay, resubmission diff, overlap join,
cheapest-next-step, bundler, letter number check, SHA-256 audit chain (tamper). Faked and labelled: OCR/LLM, issuer lookups, anomaly.

## Run (PowerShell)
    python -m venv .venv; .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m pytest -q
    uvicorn app.main:app --reload --port 8000        # docs at /docs
Vite: add `server: { proxy: { "/api": "http://localhost:8000" } }` and remove the MSW start lines.
`POST /api/dev/reset` restores the demo.

## Screen -> endpoint
Docket: GET /api/applications/APP-0001/summary (counts, sample_statement, queues, anomaly, required_checks_open), /bundles
Case Desk: .../coverage (spine), .../timeline, .../checks, /findings, /findings/{id}, /findings/{id}/graph, /documents/{id}/file + /boxes,
  POST .../decision, POST /waivers, POST /findings/{id}/decision, /bundles/{id}/letter, POST /bundles/{id}/send
Tabs: .../claims (Delta), /network/faculty/{token}, .../photos (Infra), /audit, /audit/verify, POST /audit/tamper
Pre-check: GET /checklist, /documents, POST /precheck   Fixes: GET .../fixes, POST .../resubmit, GET .../diff
Rule Lab: GET /rules, POST /rules/simulate, POST /replay, POST /guard/evaluate   Alerts: GET /alerts
Results: GET /eval/summary (computed from live data), /eval/ground-truth   Misc: GET /clock, /applications

## Field names to map if your components differ
Check states: PASSED | CONFLICT | FAILED | UNABLE TO VERIFY | MANUAL REVIEW (coverage has both `state` and `check_state`).
next_step.kind = request_one_document. Findings carry title, explanation, evidence[{doc,page,text}], trace, fix, queue (red|amber), ai_read.

## Honest limits
Norms are illustrative until copied from APH 2024-27. Anomaly result is fixed (mock). One application. State is in memory.
