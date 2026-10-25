# SATYAPAN (सत्यापन) Case Desk (frontend only)

*Satyapan* means "verification". Product name lives in one place: `src/ui/Shell.tsx` (masthead) and `index.html` (title).

React + Vite + TypeScript. No UI kit, no Tailwind: the look is hand-built in `src/styles.css`
(khadi paper, manila folders, docket slips with a torn-stub edge, rubber stamps with rough ink, evidence ladder, hard offsets, no gradients, no rounded SaaS cards).

## Coverage against the SIH PS3+PS5 deck
See `docs/FEATURE_COVERAGE.md` for what is built, what was added, how each is verified, and the honest to-do list.

## Run
```bash
npm install
npm run dev          # http://localhost:5173  (mock backend is ON)
npm test             # 27 tests: golden vectors, rule parity, every page rendered against the mock API, full officer flow, PS5 additions
npm run build        # type-check + production build
```

## Mock vs real backend
- Default: **Mock Service Worker** answers every `/api/...` call in the browser (`src/mocks/handlers.ts`) from `public/fixtures/*.json`.
  The audit hash chain, the No-Silent-Pass guard (HTTP 409), waivers, accept/dismiss, resubmission diff, RuleDial and the results page run for real in the browser.
- Real backend: create `.env.local` with `VITE_API_BASE=http://localhost:8000` and restart. The worker never starts; the same routes go to FastAPI.
  Contract your friend must meet: `docs/API_CONTRACT.md`.

## Where things are
| Path | What |
|---|---|
| `src/ui/*` | Stamp, Ladder (EvidenceStrip), FoldStack, CalendarRail, SealSlot, Spine, FindingSlip, PdfViewer (pdf.js + evidence boxes), NetworkMap, PlausibilityMap (offline SVG, no map tiles), Trace/Graph, Modals (waiver, clause drawer), ChainFooter, DiffRibbon/BundleCard |
| `src/pages/*` | Inbox (docket), Case (case desk), Institution (pre-check, fixes), Others (rule lab, alerts, audit, results) |
| `src/lib/*` | Pure engines, golden-tested against the Python ones: norm, rung, guard, chain, delta, sampler, rules, format |
| `src/mocks/handlers.ts` | The fake backend |
| `public/fixtures/` | JSON + 8 synthetic PDFs from the offline generator (PyMuPDF boxes included) |

## Keyboard (case desk)
`J` `K` next/previous finding · `Y` accept · `N` dismiss · `R` request info · `W` waive (written reason) · `C` clause · `G` evidence graph · `Ctrl/Cmd+K` palette · `Esc` close.

## Demo path (about 3 minutes)
1. Docket: unfold the fold stack (honest bound: at most 23 of 62), see the red and amber queues.
2. Case desk: seal withheld, 7 open checks; Fire NOC pin pulses inside the odd semester.
3. F-014: PDF jumps to page 8 with the evidence box; `C` for the clause; Network and Infra tabs.
4. Press Approve: genuine 409. Accept review items (`Y`), upload the corrected area statement on Fixes (diff ribbon), waive R05 and R06 with reasons, then Approve.
5. Footer: Verify, then Tamper (demo), Verify again, Reset. Results page: computed from ground truth.

## Notes
- Fonts load from Google Fonts (Libre Caslon Text, Public Sans, Courier Prime, Noto Sans Devanagari) and fall back to Georgia / Courier New offline.
- All data is synthetic and fictional. Norms and clauses are illustrative until copied from AICTE APH 2024-27. Do not add the State Emblem or official logos.
- Case data is the Pune "SVIET" case, AY 2027-28. If your slides say "DIT-Pune / AY 2026-27", edit the strings in `public/fixtures/*.json` (names, dates) and re-run the generator in the backend kit; the UI reads everything from fixtures.
