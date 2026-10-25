# SATYAPAN / ISHAN Scrutiny Backend (SIH26261 / PS5)

A real FastAPI + SQLite scrutiny backend for the SATYAPAN AICTE application integrity desk. It performs real document scrutiny on the **Fire NOC** (extracting fields, evaluating AST rules, searching bounding boxes, checking forensics), detects cross-institution faculty overlaps ("Sakshya"), identifies cross-institution document reuse, enforces cryptographic audit logging, and coordinates officer actions under strict guard conditions.

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.9+ (Python 3.11+ recommended)
- Node.js 18+ (for running the React frontend)

### 2. Backend Setup
From the repository root:

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server on port 8000
uvicorn app.main:app --port 8000 --reload
```

The server starts at `http://localhost:8000`, with all API routes mounted under `/api`.

### 3. Running the React Frontend
In a separate terminal from the repository root:

```bash
# Point frontend to the real FastAPI backend
VITE_API_BASE=http://localhost:8000/api npm run dev
```

Open `http://localhost:5173/` in your browser. The frontend interacts directly with the live FastAPI backend.

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` or set these environment variables:

| Variable | Default | Description |
|---|---|---|
| `ENV` | `development` | Environment mode (`development` or `production`). In `production`, `POST /api/_reset` is disabled. |
| `DEMO_TODAY` | `2027-01-12` | Review reference clock date in ISO format (`YYYY-MM-DD`). |
| `STAGE_DELAY_MS` | `500` | Display delay (in ms) per pipeline stage for UI animation. Set to `0` for instant test runs. |
| `SCENARIO` | `full` | `full`: 13 non-Fire-NOC requirements retain fixture rows as submitted profile. `fresh`: all non-uploaded requirements fail `missing_document`. |
| `HMAC_SECRET` | `satyapan_demo_hmac_secret_2027` | Secret key used for anonymizing faculty IDs into 16-character HMAC tokens. |

---

## 📊 System Architecture & Component Mapping

| Component | Status | Implementation Details |
|---|---|---|
| **Fire NOC Extraction** | **Computed** | PyMuPDF text & word search in `extract/regex_fire_noc.py`. Returns coordinates in PDF points (top-left origin). |
| **Fire NOC 8-Point Scrutiny** | **Computed** | Real rule evaluation in `checks/fire_noc.py`: number format regex, date order, expiry vs `DEMO_TODAY`, AST rule `FIRE_NOC_COVERS_SEMESTER`, AST rule `FLOORS_WITHIN_NOC`, address match, and metadata tampering analysis. |
| **8-Stage Pipeline** | **Computed** | Sequential background execution in `pipeline/runner.py` (`intake, read, change, check, verify, coverage, resolve, review`). Persisted in SQLite `application_run`. |
| **Cryptographic Audit Chain** | **Computed** | Ported in `audit/chain.py`. SHA-256 hash chain with canonical JSON (sorted keys, no spaces, UTF-8 unicode). Verified against golden vectors. |
| **Audit Tamper & Repair** | **Computed** | `POST /api/audit/_tamper` modifies row 3 payload; `GET /api/audit/verify` flags broken hash at seq 3; `POST /api/audit/_repair` restores integrity. |
| **Faculty Overlap ("Sakshya")** | **Computed** | Table `faculty_appointment`. `HMAC-SHA256` tokenization; detects concurrent full-time appointments across institutions. Serves computed `GET /api/network/faculty/{token}`. |
| **Document Reuse** | **Computed** | Table `other_institution_document`. Compares document SHA-256 against filings from other institutions. Flags `F-023` `DOC_REUSE` without accusation. |
| **Guard & Waivers** | **Computed** | `engines/guard.py`. Blocks `approve` with HTTP 409 if open checks remain. Enforces senior officer role and 15+ character mandatory written waiver reasons. |
| **Pre-Check Dry-Run** | **Computed** | `POST /api/institution/precheck`. Runs document analysis against the 14-requirement checklist. Creates no official application state; logs one `precheck.run` audit entry. |
| **Rule AST Evaluator** | **Computed** | `engines/bengine.py`. Pure AST evaluation of syntax trees from `rules.json` (version `eoa_v1`). `POST /api/rules/simulate` simulates parameter sensitivity. |
| **Issuer Registry** | **Simulated** | `adapters/simulated_registry.py`. Simulates State Fire Service registry response (`agrees`, `mismatch`, `not_found`, `source_down`). |
| **Photo Geofencing & Haversine** | **Computed** | `engines/geo.py`. Haversine geodesic distance, polygon centroid, and ray-casting point-in-polygon checks for campus photo validation. |
| **LLM Fire NOC Extractor** | **Computed / Optional** | `extract/llm_fire_noc.py`. Pluggable LLM extractor with JSON-schema output, `temperature=0`, SQLite response caching (`llm_cache`), regex fallback, and `ai_read` provenance. |
| **Non-Fire-NOC Requirements** | **Fixture-backed** | Requirements R01..R04, R06..R14 read from `public/fixtures/coverage.json` in `SCENARIO=full` mode. |
| **Evaluation Benchmarks** | **Fixture-backed** | `GET /api/eval/summary` computes recall against `ground_truth.json` and `findings_ids.json`. |

---

## 🧪 Testing

To run the complete automated test suite (31 test cases):

```bash
cd backend
./.venv/bin/pytest -v
```

### Test Coverage Summary:
- `test_health.py`: Verifies server health check endpoint.
- `test_vectors.py`: Parity testing against `tests/vectors.json` (chain, norm, rung, check_state, guard, bucket, sampler, AST rules).
- `test_phase2.py`: SQLite persistence, audit tamper/repair, guard 409, waiver 403/200, finding 422, fixture endpoints.
- `test_phase3.py`: Fire NOC generator, extractor, 8-point checks (default, expired, tampered, garbage), pipeline runner, and scrutiny groups.
- `test_phase4.py`: Faculty appointment overlap variants, document reuse detection, precheck isolation, `fresh` scenario 409, role security.
- `test_contract.py`: Verifies every GET endpoint in `docs/API_CONTRACT.md` and UI field expectations.
- `test_phase6.py`: Campus polygon geofencing, photo distance calculations, and LLM extractor fallback/caching.

---

## 🛠️ Synthetic Document Generator

Generate synthetic Fire NOC PDFs for testing:

```bash
# Generate default demo PDF (ends 79 days before odd semester)
python synth/make_fire_noc.py --out data/samples/fire_noc_demo.pdf

# Generate expired Fire NOC (valid till before 12-01-2027)
python synth/make_fire_noc.py --out data/samples/fire_noc_expired.pdf --expired

# Generate tampered Fire NOC (unregistered number, mod date >> creation date, Photoshop editor tag)
python synth/make_fire_noc.py --out data/samples/fire_noc_tampered.pdf --tampered
```
