# SATYAPAN / ISHAN: Full Coding Run Summary
**AICTE Application Scrutiny Case Desk (SIH26261 / PS5)**  
*Session Date: October 24–25, 2026 | Active Branch: `ishan` | Commit: `9e47918`*

---

## 🧭 1. Mission Overview

In this pair programming run, we built and delivered a **complete, production-grade Python (FastAPI + SQLite) backend** and seamlessly integrated it with the existing **React/Vite frontend** for the SATYAPAN AICTE application scrutiny system.

The core deliverable was to transition the project from static mocks into a **genuinely working scrutiny engine** for uploaded documents (specifically the Fire NOC), with automated PDF extraction, 8-point rule verification, tamper-evident cryptographic audit logging, cross-institution faculty overlap detection ("Sakshya"), document reuse detection, officer guard enforcement, and an end-to-end document upload-to-verification lifecycle.

---

## 🏆 2. Complete Summary of What Was Accomplished

### A. Core Algorithmic Engines (Golden Vector Parity)
- **Deterministic SHA-256 Audit Chain (`backend/app/audit/chain.py`)**: Canonical JSON encoding (sorted keys, compact separators, UTF-8 unicode preservation) matching TypeScript golden test vectors down to the exact hash, including Devanagari script.
- **Unicode Text & Numeric Normalizer (`backend/app/engines/norm.py`)**: Regex filters based on Unicode character categories (`\p{L}`, `\p{M}`, `\p{N}`) to support multilingual Indian scripts and normalize spelling variants (e.g., *Shri* vs *Shree*).
- **Evidence Ladder & State Engine (`backend/app/engines/rung.py`)**: Rungs 0..3 evidence hierarchy (0: text on page, 1: certified statement, 2: third-party corroboration, 3: direct issuer/registry lookup). State transitions: `PENDING`, `PASSED`, `FAILED`, `MANUAL_REVIEW`, `UNABLE_TO_VERIFY`.
- **Officer Guard & Decision Engine (`backend/app/engines/guard.py`)**: Blocks application approval with **HTTP 409 Conflict** if open checks remain. Validates senior officer roles and enforces mandatory 15+ character written waiver reasons.
- **Rule AST Evaluator & Dial (`backend/app/engines/bengine.py`)**: Evaluates JSON abstract syntax tree rule clauses (e.g. `FIRE_NOC_COVERS_SEMESTER`, `FLOORS_WITHIN_NOC`, `AREA_PER_SEAT`) and powers real-time sensitivity simulations on `POST /api/rules/simulate`.
- **Claims Diff Bucketer (`backend/app/engines/delta.py`)**: Classifies claims into `UNCHANGED`, `CHANGED_WITH_EVIDENCE`, `CHANGED_NO_EXPLANATION`, and `NEW`.
- **Stratified Auditor Sampler (`backend/app/engines/sampler.py`)**: Computes required audit sample counts and auditor badge states based on risk profiles.

### B. SQLite Relational Persistence & Audit Security
- **Relational Schema (`backend/app/db.py`)**: Initialized SQLite database (`backend/data/satyapan.db`) with tables: `audit_log`, `application_run`, `document`, `waiver`, `finding_decision`, `application_state`, `scrutiny_result`, `faculty_appointment`, `other_institution_document`, and `llm_cache`.
- **Audit Verification & Tamper Detection Endpoints**:
  - `GET /api/audit`: Returns complete cryptographic sequence.
  - `GET /api/audit/verify`: Verifies the SHA-256 chain; returns `{intact: true/false, entries, first_broken_seq, head}`.
  - `POST /api/audit/_tamper`: Mutates row 3 payload to demonstrate tamper detection in live presentations.
  - `POST /api/audit/_repair`: Re-hashes forward entries to demonstrate cryptographic recovery.
  - `POST /api/_reset`: Reinitializes SQLite state to boot clean state.

### C. Genuine Fire NOC Scrutiny & 8-Stage Pipeline
- **Synthetic PDF Generator (`backend/synth/make_fire_noc.py`)**:
  - ReportLab + PyMuPDF generator for authentic Maharashtra State Fire Service certificates.
  - Supports variants: standard demo (valid till 30-09-2027), `--expired` (valid till 10-01-2027), `--tampered` (unregistered number, mod date mismatch, Photoshop signature), and `--renewed` (valid till 31-12-2028).
- **PyMuPDF Document Extractor (`backend/app/extract/regex_fire_noc.py`)**:
  - Extracts certificate number, dates (`dayfirst=True`), floor limits, and premises address.
  - Locates exact bounding boxes in PDF points (origin top-left) for visual viewer highlighting.
- **Simulated Registry Adapter (`backend/app/adapters/simulated_registry.py`)**:
  - Simulates State Fire Service registry responses: `agrees`, `mismatch`, `not_found`, and `source_down`.
- **8-Point Scrutiny Suite (`backend/app/checks/fire_noc.py`)**:
  1. `FN_NUMBER_FORMAT`: Matches regex `^SYN/FIRE/[A-Z]+/\d{4}/\d+$`.
  2. `FN_ISSUER_LOOKUP`: Queries simulated Fire Service registry.
  3. `FN_DATE_ORDER`: Verifies `issue_date < valid_till`.
  4. `FN_NOT_EXPIRED`: Verifies `valid_till >= DEMO_TODAY` (2027-01-12).
  5. `FIRE_NOC_COVERS_SEMESTER`: AST rule ensuring validity covers odd semester (2027-08-02 to 2027-12-18).
  6. `FLOORS_WITHIN_NOC`: AST rule ensuring campus floors <= NOC approved floors (5).
  7. `FN_ADDRESS_MATCH`: Normalizes and checks institution address match.
  8. `FN_METADATA_HINT`: Checks PDF creation/modification dates and editor software signatures.
- **Sequential 8-Stage Pipeline Runner (`backend/app/pipeline/runner.py`)**:
  - Background asynchronous execution: `intake -> read -> change -> check -> verify -> coverage -> resolve -> review`.
  - Atomically appends an audit event to the cryptographic chain upon the completion of each stage.

### D. PS5 Core Workflows
- **Dual Scenario Support (`SCENARIO=full|fresh`)**:
  - `fresh`: Evaluates 13 non-Fire-NOC requirements as `missing_document` (`FAILED`), simulating an incomplete submission and causing `POST /decision` to return 409.
  - `full`: Retains submitted profile fixtures for demo evaluation.
- **Institution Pre-Check (`POST /api/institution/precheck`)**:
  - Completely isolated dry-run checklist evaluation against 14 requirements.
  - Creates **zero official application state** and logs exactly one `precheck.run` audit event.
- **Faculty Overlap Detection ("Sakshya", `backend/app/engines/crossinst.py`)**:
  - Detects concurrent full-time teaching appointments across multiple institutions.
  - Replaces raw faculty IDs with **16-character HMAC-SHA256 privacy tokens**.
  - Dynamically computes graph nodes, edges, and overlaps for `GET /api/network/faculty/{token}`.
- **Cross-Institution Document Reuse (`backend/app/engines/cengine.py`)**:
  - Detects duplicate document filings across institutions via SHA-256 matching.
  - Generates finding `F-023` (`DOC_REUSE`) with neutral, non-accusatory phrasing.
- **Cheapest Next Action Calculations**:
  - Findings calculate the lowest cost resolution path: `read_qr` (Cost 1), `request_one_document` (Cost 2), `query_issuer` (Cost 3), `physical_inspection` (Cost 10).
- **Role-Based Authorization (`backend/app/auth.py`)**:
  - Enforces `X-Role` / `X-User` headers. Returns 403 on unauthorized waiver attempts.

### E. Extras & Hardening
- **Campus Geofencing & Photo Distance (`backend/app/engines/geo.py`)**:
  - Haversine great-circle formula for spherical distance calculations.
  - Polygon centroid calculation and ray-casting point-in-polygon containment checks.
  - Live photo statuses (`inside_campus`, `far_from_campus`, `no_location_data`) served on `GET /api/applications/{id}/photos`.
- **LLM-Assisted Fire NOC Extractor (`backend/app/extract/llm_fire_noc.py`)**:
  - Pluggable LLM extractor with JSON-schema output and `temperature=0`.
  - SQLite response caching in table `llm_cache` keyed by document SHA-256.
  - Sets `ai_read: true` on LLM/cached results, while retaining deterministic regex fallback with `ai_read: false`.

### F. Frontend Integration & Lifecycle Mapping
- **Pulled Latest Commit**: Fast-forwarded local branch `ishan` to latest commit `9e47918` ("refurbish").
- **Live PDF Viewer Integration (`src/ui/PdfViewer.tsx`)**:
  - Fetches live uploaded files directly from `GET /api/documents/{doc}/file`.
  - Overlays real PyMuPDF bounding-box coordinates with fallback to offline fixtures.
- **Real File Upload on Pre-Check (`src/pages/Institution.tsx`)**:
  - Supports drag-and-drop and file picking of real PDFs.
  - Posts `multipart/form-data` to `POST /api/applications` and triggers the real 8-stage progress tracker.
- **Renewed Certificate Resubmission (`src/pages/Institution.tsx`)**:
  - Under `/institution/fixes`, finding `F-016` has an active **"Upload renewed Fire NOC"** button.
  - Resubmits the renewed PDF to `POST /api/applications/APP-0001/resubmit`, re-running scrutiny, transitioning requirement `R05` to `PASSED`, resolving `F-016`, and bumping the case to Version 2.
- **Download Accomplishments Report**:
  - Added one-click **`⬇ Report.md`** download button directly in the frontend navbar (`src/ui/Shell.tsx`).
  - Added backend download endpoint `GET /api/download/accomplishments`.

---

## 🔄 3. End-to-End Document Lifecycle Flow (`test_full_cycle.py`)

```text
[1. Pre-Check]        Institution runs dry-run -> R05 odd semester gap flagged.
       │
[2. Intake & Upload]  Institution uploads initial Fire NOC (valid till 30-09-2027).
       │
[3. Scrutiny Pipeline] 8-stage pipeline runs; AST evaluates semester gap -> F-016 FAILED.
       │
[4. Officer Docket]   Reviewer views PDF in viewer with live box; Approve is BLOCKED (409).
       │              Officer requests info on F-016 (audit logged).
       │
[5. Fix & Resubmit]   Institution uploads renewed Fire NOC (valid till 31-12-2028).
       │              Scrutiny re-runs: R05 PASSED, F-016 resolved, bumped to Version 2.
       │
[6. Final Decision]   Officer enters valid written waivers for open non-blockers.
       │              Officer approves application -> HTTP 200 APPROVED!
       │
[7. Audit Proof]      GET /api/audit/verify confirms all events cryptographically intact.
```

---

## 🧪 4. Test Suite Execution Results

### Backend (`pytest -v`): 32 of 32 Passed (100%)
```text
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
tests/test_bucket_vectors PASSED                                         [ 93%]
tests/test_sampler_vectors PASSED                                        [ 96%]
tests/test_rules_ast_evaluator_demo PASSED                               [100%]

======================== 32 passed, 5 warnings in 4.07s ========================
```

### Frontend (`npm test` / vitest): 20 of 20 Passed (100%)
```text
 ✓ tests/parity.test.ts (3)
 ✓ tests/golden.test.ts (11)
 ✓ tests/features.test.ts (6)

 Test Files  3 passed (3)
      Tests  20 passed (20)
```

---

## 🚀 5. How to Run & Verify

### 1. Launch Servers
```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --port 8000 --reload

# Terminal 2: Frontend
VITE_API_BASE=http://localhost:8000/api npm run dev
```

### 2. Live URLs
- **Web App:** [http://localhost:5173/](http://localhost:5173/)
- **Pre-Check Upload:** [http://localhost:5173/institution](http://localhost:5173/institution)
- **Case Review Docket:** [http://localhost:5173/case](http://localhost:5173/case)
- **Fixes & Renewed Resubmission:** [http://localhost:5173/institution/fixes](http://localhost:5173/institution/fixes)
- **Audit Chain Verifier:** [http://localhost:8000/api/audit/verify](http://localhost:8000/api/audit/verify)
- **Download Report:** [http://localhost:8000/api/download/accomplishments](http://localhost:8000/api/download/accomplishments)
