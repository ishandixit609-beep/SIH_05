# Feature coverage: SIH PS3 + PS5 concept deck vs this site

Scope chosen: **PS5** (Proof-before-Decision Workbench). PS3 features are listed so the team can see what is deliberately not built.

## PS5: six proposed features

| # | Feature in the deck | Status | Where in the site | Verified by |
|---|---|---|---|---|
| 1 | Proof-Coverage Compiler | Built | Case desk, left Spine (requirement, document, page, rung, expiry) | `golden.test.ts`, `parity.test.ts`, smoke "Case desk" |
| 2 | Re-Submission Diff + Selective Revalidation | Built | Fixes page: upload corrected area statement, DiffRibbon (3 changed, 2 resolved, 1 pending, rules re-run) | smoke "full officer flow" |
| 3 | Root-Cause Clarification Bundler | Built | Inbox and case desk BundleCard B-01 (3 findings, 1 request) | smoke "Inbox", "Case desk" |
| 4 | No-Silent-Pass Guard | Built, **demo added** | SealSlot (real HTTP 409, waivers). **New:** Guard Lab on Rule lab page: flip any of 10 checks to manual-only / not configured and watch the overall state | `golden.test.ts`, `features.test.ts`, smoke "guard lab" |
| 5 | Evidence Graph | Built, **audit trail added** | TraceRibbon + graph modal (`G`). **New:** reviewer audit trail inside the modal (rule version, who acted, hash) | smoke "Case desk"; manual: press `Y` then `G` |
| 6 | Applicant Fix-It Copilot | Built, **made real** | Fixes page and BundleCard. **New:** the "numbers checked" claim now runs a live number check against the cited findings; each fix shows why it matters, the rule and a 5-step progress line | `features.test.ts` (accepts all three letters, rejects "pay 5,000") |

## Deck's measurement promises ("Measure quality")

| Promise | Status | Where |
|---|---|---|
| Recall on planted issues | Built (new headline stat) | Results page, counted from `ground_truth.json` |
| False positives on valid-but-unusual documents | Built | Results page |
| Findings with complete evidence | **New**, and honest: 7 of 15 | Results page lists the 8 without a page-level evidence box |
| Resolution time in a user test | **New** stopwatch (with vs without tool) | Results page, stored in the browser only |
| Precision | Not built: needs a labelled set of valid documents with no planted issue | Next step |

## Deck's boundary and honesty slides

Added the **Method** page (`/about`): what it builds on, MVP boundary, what we do not claim, official source links with the deck's caveats.

## Still to add (honest list)

1. Page-level evidence anchors for the 8 findings that have none (network, anomaly, source-status). Needs generated PDFs or record views for them.
2. A labelled "valid but unusual" document set to compute precision, not only a false-positive count.
3. Real backend behind `VITE_API_BASE` (contract in `API_CONTRACT.md`). Everything runs on the mock until then.
4. Interviews with real reviewers; the deck says the gaps are hypotheses.
5. PS3 features (mass-balance, blast-radius, transfer handshake, duplicate network, mismatch copilot, anomaly): not built, by choice of PS5.

## How to run the evaluation

```bash
npm install
npm test            # 27 tests: golden vectors, rule parity with Python, every page against the mock API, officer flow, PS5 additions
npm run build       # type-check + production build
npm run dev         # open http://localhost:5173
```

Manual run (about 5 minutes):

1. **Method** tab: read the scope and caveats.
2. **Docket** then **Case desk**: seal withheld (7 open checks). Press **Approve**: HTTP 409 with the open list.
3. Select F-014, press `G`: trace plus audit trail (empty). Close, press `Y` on a review item, press `G` again: the audit trail now shows your act.
4. **Fixes**: read the letter, see "number check passed"; upload the corrected area statement; DiffRibbon appears and the progress line for F-014 becomes "Re-check: resolved".
5. **Rule lab**: drag the dial; in Guard Lab press "make Accreditation manual-only": overall flips to Review incomplete.
6. **Results**: recall, false positives, evidence completeness; run the timer once with and once without the tool.
7. **Audit**: Verify, Tamper (demo), Verify again, Reset.
