# SATYAPAN / ISHAN: Backend Accomplishments Report
**AICTE Application Scrutiny System (SIH26261 / PS5)**  
*Author: Antigravity AI Engineer | Branch: `backend`*

---

## 📌 1. Executive Summary

This document details the complete accomplishments achieved in building the **SATYAPAN / ISHAN Scrutiny Backend** inside the `backend/` directory of the `SIH_05` repository. 

The backend is a production-grade, asynchronous **FastAPI + SQLite** service that implements the full AICTE scrutiny workflow as specified in PS5. It delivers:
- **Genuinely computed document scrutiny** for the Fire NOC (including PyMuPDF text and coordinate extraction, 8-point deterministic rule checks, AST rule evaluation, and metadata forensics).
- **Strict adherence to the API contract** (`docs/API_CONTRACT.md`), enabling the existing React/Vite frontend (`src/`) to run out-of-the-box against `http://localhost:8000/api` without modifying a single line of frontend code.
- **Full PS5 compliance workflows**, including cryptographic audit chains, institution pre-checks, faculty overlap detection ("Sakshya"), document cross-institution reuse checks, officer guard logic, and cheapest next action recommendations.
- **100% automated test pass rate** across all 31 unit, parity, contract, and workflow test cases.

---

## 🛡️ 2. Golden Rules & Architectural Principles

1. **Strict Workspace Isolation**: All development was confined entirely to `backend/`. Not a single file in `src/`, `public/`, `tests/`, `docs/`, `package.json`, `dist/`, or `node_modules` was modified or deleted.
2. **Deterministic Judgments (No AI Pass/Fail)**: All approval, flag, and state decisions derive purely from deterministic rules, mathematical calculations, and AST syntax tree evaluations. AI/LLM models are restricted to assistive field extraction and always tagged with `ai_read: true`.
3. **Mandatory Neutral Vocabulary**: Non-accusatory language is enforced across all explanations and audit logs. The system uses *flagged, unusual, possible tampering indicators, possible overlap, needs human confirmation, ready for decision* rather than forbidden words like *fraud, forged, fake, approved-by-system*.
4. **Cryptographic Parity**: The SHA-256 hash chain implements canonical JSON formatting (sorted keys, compact separators, UTF-8 unicode preservation) ensuring bit-for-bit parity with TypeScript vectors, including Devanagari script.

---

## 🏗️ 3. Detailed Phase-by-Phase Deliverables

### Phase 0: Environment & Architecture Setup
- Built a standalone virtual environment layout (`backend/requirements.txt`, `.gitignore`, `.env.example`).
- Pinned and validated libraries compatible with **Python 3.9+** (including pinning ReportLab `<5.0.0` for Python 3.9 runtime compatibility).
- Created `app/main.py` with CORS middleware configured for Vite (`http://localhost:5173`) and a live health check endpoint (`GET /api/health`).

### Phase 1: Deterministic Engine Core & Golden Vector Parity
Ported and validated all core algorithmic engines against `tests/vectors.json`:
- **Cryptographic Audit Chain ([`backend/app/audit/chain.py`](file:///Users/DELL/SIH_05/backend/app/audit/chain.py))**: Generates deterministic SHA-256 hash chains over canonical JSON strings.
- **Text & Numeric Normalization ([`backend/app/engines/norm.py`](file:///Users/DELL/SIH_05/backend/app/engines/norm.py))**: Unicode category filtering for international scripts (e.g. Marathi/Hindi) and number extraction.
- **Evidence Ladder & State Machine ([`backend/app/engines/rung.py`](file:///Users/DELL/SIH_05/backend/app/engines/rung.py))**: Evaluates Rungs 0..3 evidence hierarchy and manages check state transitions (`PENDING`, `PASSED`, `FAILED`, `MANUAL_REVIEW`, `UNABLE_TO_VERIFY`).
- **Officer Guard Logic ([`backend/app/engines/guard.py`](file:///Users/DELL/SIH_05/backend/app/engines/guard.py))**: Blocks approvals when open checks exist, computes overall readiness (`READY_FOR_DECISION` vs `REVIEW_INCOMPLETE`), and enforces waiver validations.
- **Rule AST Evaluator & Dial ([`backend/app/engines/bengine.py`](file:///Users/DELL/SIH_05/backend/app/engines/bengine.py))**: Pure AST evaluator for JSON rule clauses (`FIRE_NOC_COVERS_SEMESTER`, `FLOORS_WITHIN_NOC`, `AREA_PER_SEAT`, etc.) and real-time sensitivity simulation.
- **Claims Diff Buckets ([`backend/app/engines/delta.py`](file:///Users/DELL/SIH_05/backend/app/engines/delta.py))**: Categorizes claims into `UNCHANGED`, `CHANGED_WITH_EVIDENCE`, `CHANGED_NO_EXPLANATION`, and `NEW`.
- **Stratified Auditor Sampler ([`backend/app/engines/sampler.py`](file:///Users/DELL/SIH_05/backend/app/engines/sampler.py))**: Calculates required sampling sizes and badge states based on risk scores.

### Phase 2: SQLite Persistence, Audit Verifier & Decision Guard
- **Relational Schema ([`backend/app/db.py`](file:///Users/DELL/SIH_05/backend/app/db.py))**: Initialized SQLite tables: `audit_log`, `application_run`, `document`, `waiver`, `finding_decision`, `application_state`, `scrutiny_result`, `other_institution_document`, `faculty_appointment`, and `llm_cache`.
- **Tamper-Evident Audit APIs**:
  - `GET /api/audit`: Returns the full sequence of cryptographic audit entries.
  - `GET /api/audit/verify`: Verifies the SHA-256 chain; returns `{intact: true/false, entries, first_broken_seq, head}`.
  - `POST /api/audit/_tamper`: Deliberately mutates row 3 payload for demonstration purposes.
  - `POST /api/audit/_repair`: Recalculates forward hashes to demonstrate audit recovery.
  - `POST /api/_reset`: Reinitializes SQLite state to boot clean state (disabled in production).
- **Officer Guard Enforcement ([`backend/app/api/applications.py`](file:///Users/DELL/SIH_05/backend/app/api/applications.py))**:
  - `POST /api/applications/APP-0001/decision`: Returns **HTTP 409 Conflict** with `{detail, open_checks: [...]}` if open unwaived checks remain.
  - `POST /api/applications/APP-0001/waivers`: Returns **HTTP 403 Forbidden** for non-senior officer roles or waiver explanations under 15 characters.
  - `POST /api/findings/{id}/decision`: Returns **HTTP 422 Unprocessable Entity** if an officer attempts to accept/dismiss a finding with state `FAILED`.
- **Fixture Layer ([`backend/app/fixtures_layer.py`](file:///Users/DELL/SIH_05/backend/app/fixtures_layer.py))**: Clearly demarcated fixture fallback for non-computed requirements.

### Phase 3: Real Fire NOC Scrutiny & 8-Stage Pipeline
- **Synthetic Document Generator ([`backend/synth/make_fire_noc.py`](file:///Users/DELL/SIH_05/backend/synth/make_fire_noc.py))**:
  - Built using ReportLab and PyMuPDF.
  - Produces authentic Indian fire safety certificates with issuer headers, seal stamps, reference numbers, and dates.
  - Supports flags: `--expired` (validity expiring before reference date) and `--tampered` (unregistered number, metadata modification timestamp anomaly, and editor tag indicators).
- **Deterministic Extractor ([`backend/app/extract/regex_fire_noc.py`](file:///Users/DELL/SIH_05/backend/app/extract/regex_fire_noc.py))**:
  - Performs regex parsing and word-level search in PyMuPDF.
  - Locates exact bounding boxes in PDF point coordinates (origin top-left) for visual document viewer highlighting.
- **Simulated Registry Adapter ([`backend/app/adapters/simulated_registry.py`](file:///Users/DELL/SIH_05/backend/app/adapters/simulated_registry.py))**:
  - Simulates Maharashtra State Fire Service registry lookups (`agrees`, `mismatch`, `not_found`, `source_down`).
- **8-Point Scrutiny Suite ([`backend/app/checks/fire_noc.py`](file:///Users/DELL/SIH_05/backend/app/checks/fire_noc.py))**:
  1. `FN_NUMBER_FORMAT`: Validates format regex `SYN/FIRE/<CITY>/<YEAR>/<SEQ>`.
  2. `FN_ISSUER_LOOKUP`: Queries simulated Fire Service registry.
  3. `FN_DATE_ORDER`: Verifies `issue_date < valid_till`.
  4. `FN_NOT_EXPIRED`: Verifies `valid_till >= DEMO_TODAY` (2027-01-12).
  5. `FIRE_NOC_COVERS_SEMESTER`: AST rule check ensuring validity covers odd semester (2027-08-02 to 2027-12-18).
  6. `FLOORS_WITHIN_NOC`: AST rule check ensuring campus floors <= NOC approved floors (5).
  7. `FN_ADDRESS_MATCH`: Normalizes and checks institution address match.
  8. `FN_METADATA_HINT`: Checks PDF creation/modification dates and editor software signatures.
- **Sequential 8-Stage Pipeline Runner ([`backend/app/pipeline/runner.py`](file:///Users/DELL/SIH_05/backend/app/pipeline/runner.py))**:
  - Executes stages asynchronously: `intake -> read -> change -> check -> verify -> coverage -> resolve -> review`.
  - Atomically appends an audit event to the cryptographic chain upon the completion of each stage.

### Phase 4: Full PS5 Workflows
- **Scenario Toggle (`SCENARIO=full|fresh`)**:
  - `SCENARIO=fresh`: Treats all 13 non-Fire-NOC requirements as `missing_document` (state: `FAILED`), simulating an incomplete submission and causing `POST /decision` to return 409.
  - `SCENARIO=full`: Uses submitted profile fixtures for demonstration.
- **Institution Pre-Check (`POST /api/institution/precheck`)**:
  - Self-service pre-check for institutions prior to final submission.
  - Performs complete dry-run validation across all 14 checklist requirements.
  - Creates **zero official application state** and logs exactly one `precheck.run` audit event.
- **Faculty Overlap Detection ("Sakshya", [`backend/app/engines/crossinst.py`](file:///Users/DELL/SIH_05/backend/app/engines/crossinst.py))**:
  - Evaluates concurrent full-time teaching appointments across multiple institutions.
  - Replaces raw faculty IDs with **16-character HMAC-SHA256 privacy tokens**.
  - Dynamically computes graph nodes, edges, and overlaps for `GET /api/network/faculty/{token}`.
- **Document Cross-Institution Reuse ([`backend/app/engines/cengine.py`](file:///Users/DELL/SIH_05/backend/app/engines/cengine.py))**:
  - Compares document SHA-256 against records filed by other institutions.
  - Generates finding `F-023` (`DOC_REUSE`) with neutral, non-accusatory phrasing.
- **Cheapest Next Action & Findings Engine**:
  - Recomputes findings `F-016`, `F-017`, `F-023` dynamically.
  - Suggests lowest cost resolution steps: `read_qr` (Cost 1), `request_one_document` (Cost 2), `query_issuer` (Cost 3), `physical_inspection` (Cost 10).
- **Role-Based Authorization ([`backend/app/auth.py`](file:///Users/DELL/SIH_05/backend/app/auth.py))**:
  - Enforces `X-Role` / `X-User` headers (e.g. `senior_officer`). Returns 403 on unauthorized waiver attempts.

### Phase 5: Complete API Contract Testing & Documentation
- **Contract Tests ([`backend/tests/test_contract.py`](file:///Users/DELL/SIH_05/backend/tests/test_contract.py))**:
  - Validates all 18 `GET` endpoints in `docs/API_CONTRACT.md` against live HTTP responses.
  - Verifies presence of all required UI fields, schemas, and datatypes.
- **Backend Documentation ([`backend/README.md`](file:///Users/DELL/SIH_05/backend/README.md))**:
  - Comprehensive guide covering installation, configuration, system architecture, test commands, and CLI options.

### Phase 6: Extras & Production Hardening
- **Campus Geofencing & Photo Distance ([`backend/app/engines/geo.py`](file:///Users/DELL/SIH_05/backend/app/engines/geo.py))**:
  - Implements the Haversine great-circle formula for spherical distance calculations.
  - Computes the campus polygon centroid and applies a ray-casting point-in-polygon algorithm.
  - Serves live evaluated photo statuses (`no_location_data`, `inside_campus`, `far_from_campus`) on `GET /api/applications/{id}/photos`.
- **LLM-Assisted Fire NOC Extractor ([`backend/app/extract/llm_fire_noc.py`](file:///Users/DELL/SIH_05/backend/app/extract/llm_fire_noc.py))**:
  - Pluggable LLM extractor conforming to the `Extractor` interface.
  - Uses OpenAI/Gemini JSON-schema formatting with `temperature=0`.
  - Features SQLite response caching in table `llm_cache` keyed by document SHA-256.
  - Automatically tags LLM fields with `ai_read: true`, while maintaining 100% deterministic regex fallback with `ai_read: false`.

---

## 📊 4. System Architecture Summary

| Component | Status | Implementation Details |
|---|---|---|
| **Fire NOC Extraction** | **Computed** | PyMuPDF text & word search in `extract/regex_fire_noc.py` (points, top-left origin). |
| **8-Point Fire NOC Checks** | **Computed** | Real rule evaluations in `checks/fire_noc.py` (regex, dates, AST rules, address, forensics). |
| **8-Stage Pipeline** | **Computed** | Sequential background execution in `pipeline/runner.py`. |
| **Cryptographic Audit Chain** | **Computed** | SHA-256 canonical JSON hash chain in `audit/chain.py`. |
| **Audit Tamper & Repair** | **Computed** | Endpoints `/api/audit/_tamper`, `/api/audit/verify`, and `/api/audit/_repair`. |
| **Faculty Overlap ("Sakshya")**| **Computed** | Table `faculty_appointment`, HMAC-SHA256 tokenization, `GET /api/network/faculty/{token}`. |
| **Document Reuse** | **Computed** | Table `other_institution_document`, SHA-256 hash matching, finding `F-023`. |
| **Decision Guard & Waivers** | **Computed** | `engines/guard.py`. HTTP 409 on open checks, HTTP 403 on invalid waivers. |
| **Institution Pre-Check** | **Computed** | `POST /api/institution/precheck`. Completely isolated dry-run checklist evaluation. |
| **Rule AST Evaluator** | **Computed** | `engines/bengine.py`. Pure syntax tree evaluation from `rules.json`. |
| **Photo Geofencing** | **Computed** | `engines/geo.py`. Haversine geodesic distance & ray-casting point-in-polygon checks. |
| **LLM Extractor & Cache** | **Computed / Optional** | `extract/llm_fire_noc.py`. JSON schema, SQLite caching (`llm_cache`), regex fallback. |
| **Issuer Registry** | **Simulated** | `adapters/simulated_registry.py`. Simulates State Fire Service registry responses. |
| **Non-Fire-NOC Requirements** | **Fixture-backed** | Requirements R01..R04, R06..R14 served from `public/fixtures/coverage.json` in `full` mode. |
| **Evaluation Benchmarks** | **Fixture-backed** | `GET /api/eval/summary` computes recall against `ground_truth.json`. |

---

## 🧪 5. Automated Test Suite Results

The automated test suite contains **32 comprehensive test cases** spanning unit tests, golden vector parity tests, API contract tests, and end-to-end integration workflows:

```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Users/DELL/SIH_05/backend/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/DELL/SIH_05/backend
plugins: anyio-4.12.1
collected 32 items

tests/test_contract.py::test_contract_all_get_endpoints PASSED           [  3%]
tests/test_full_cycle.py::test_full_cycle_upload_scrutiny_resubmit_and_decision PASSED [  6%]
tests/test_health.py::test_health PASSED                                 [  9%]
tests/test_phase2.py::test_audit_verify_tamper_repair PASSED             [ 12%]
tests/test_phase2.py::test_approve_with_open_checks_returns_409 PASSED   [ 15%]
tests/test_phase2.py::test_waiver_validation PASSED                      [ 18%]
tests/test_phase2.py::test_finding_decision_failed_returns_422 PASSED    [ 21%]
tests/test_phase2.py::test_fixture_endpoints PASSED                      [ 25%]
tests/test_phase3.py::test_generator_default_expired_tampered PASSED     [ 28%]
tests/test_phase3.py::test_garbage_pdf_handling PASSED                   [ 31%]
tests/test_phase3.py::test_upload_validations PASSED                     [ 34%]
tests/test_phase3.py::test_end_to_end_pipeline_and_scrutiny PASSED       [ 37%]
tests/test_phase4.py::test_hmac_helper PASSED                            [ 40%]
tests/test_phase4.py::test_faculty_overlap_variations PASSED             [ 43%]
tests/test_phase4.py::test_document_reuse_hit_and_miss PASSED            [ 46%]
tests/test_phase4.py::test_precheck_creates_no_application_state PASSED  [ 50%]
tests/test_phase4.py::test_fresh_scenario_13_missing_and_409 PASSED      [ 53%]
tests/test_phase4.py::test_role_authorization_403 PASSED                 [ 56%]
tests/test_phase4.py::test_audit_chain_remains_intact_after_all_phase4_actions PASSED [ 59%]
tests/test_phase6.py::test_geo_haversine_and_point_in_polygon PASSED     [ 62%]
tests/test_phase6.py::test_compute_photo_statuses_and_endpoint PASSED    [ 65%]
tests/test_phase6.py::test_llm_extractor_fallback_and_cache PASSED       [ 68%]
tests/test_vectors.py::test_chain_vectors PASSED                         [ 71%]
tests/test_vectors.py::test_same_text_vectors PASSED                     [ 75%]
tests/test_vectors.py::test_same_num_vectors PASSED                      [ 78%]
tests/test_vectors.py::test_grade_vectors PASSED                         [ 81%]
tests/test_vectors.py::test_check_state_vectors PASSED                   [ 84%]
tests/test_vectors.py::test_guard_vectors PASSED                         [ 87%]
tests/test_vectors.py::test_guard_decide_and_waiver PASSED               [ 90%]
tests/test_vectors.py::test_bucket_vectors PASSED                        [ 93%]
tests/test_vectors.py::test_sampler_vectors PASSED                       [ 96%]
tests/test_vectors.py::test_rules_ast_evaluator_demo PASSED              [100%]

======================== 32 passed, 5 warnings in 4.02s ========================
```

---

## 🚀 6. Verification & Quickstart Commands

### 1. Run the Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --port 8000 --reload
```

### 2. Connect the React Frontend
```bash
# From repository root
VITE_API_BASE=http://localhost:8000/api npm run dev
```

### 3. Run the Automated Tests
```bash
cd backend
./.venv/bin/pytest -v
```

### 4. Generate Synthetic Test Documents
```bash
cd backend
# Standard demo PDF (validity ends 79 days before odd semester)
python synth/make_fire_noc.py --out data/samples/fire_noc_demo.pdf

# Expired certificate
python synth/make_fire_noc.py --out data/samples/fire_noc_expired.pdf --expired

# Tampered certificate (unregistered number, mod date mismatch, Photoshop signature)
python synth/make_fire_noc.py --out data/samples/fire_noc_tampered.pdf --tampered
```
