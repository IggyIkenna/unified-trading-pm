---
doc_type: plan
title:
  Data-status page UX & canonicalisation — extracted history (P2/P3 remaining-work session + Playwright mock-api fix)
summary: >-
  Archive-bound extraction of two fully-closed, dated Progress Log entries from
  /plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md, split out purely to bring that umbrella plan
  back under its 2000-line size cap. Content is verbatim and historical only -- (1) the 2026-07-17 P2/P3 remaining-work
  session journal (13 deprioritized follow-ups worked, session-end state, the "5 of 13 premises were wrong" lesson
  table), and (2) the 2026-07-17 Playwright re-verification session that found + fixed a month-old mock-api.ts catch-all
  routing bug shadowing every /api/data-status/* endpoint. Zero open todos here -- this file is a record, not a work
  queue.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, instruments-service]
scope: [engineer]
tags: [data-status, history, archive-bound, canonicalisation, mock-api, progress-log]
related: [/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-24
last_updated: 2026-07-24
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  extracted 2026-07-24 from /plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md to bring that plan
  under its 2000-line umbrella cap
---

# Data-status page UX & canonicalisation — extracted history

> **Archive-bound record, not a work queue.** This file holds two verbatim, fully-closed dated Progress Log entries
> extracted from the parent plan's history so the parent could get back under its line-count cap. No open todos exist in
> this file. See `/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md` for the live plan.

## Extracted Progress Log entries

### 2026-07-17 — P2/P3 remaining-work session (`/autonomous`) — working the 13 deprioritized follow-ups

Session working the 13 open P2/P3 todos in the Deferred table below. Journal per unit; each ships commit-push-flip.

**Operating context (READ THIS FIRST if you are a fresh/compressed context):** a **second agent is live in this same
checkout** right now — confirmed by mtime, not assumed (`deployment-api/deployment_api/services/fixtures_browser.py` +
`routes/fixtures_browse.py` + `tests/unit/test_fixtures_browser.py` were being edited seconds before this session's
first tool call; they are extending the fixtures browser with a `team=` filter + absolute `start_date`/`end_date`
window). Consequences, all of which bite:

1. **`deployment-api`'s full `quality-gates.sh` is RED and not mine to fix** — the LINT stage fails on that agent's live
   WIP (`fixtures_browse.py` E501, `fixtures_browser.py` RUF100). Every deployment-api unit this session therefore
   scope-verifies (`ruff check` + `ruff format --check` + `basedpyright` + targeted pytest on MY files only) and cites
   the carve-out, same precedent as `12c94be`/`e27ba4b`.
2. **basedpyright is A/B'd against HEAD per unit** rather than trusted absolutely — these files carry pre-existing
   `reportAny`/`dict[Hashable, Any]` errors, so "0 errors" is unachievable; "**0 NEW** errors vs the HEAD copy of the
   same file" is the real bar and is what each checkbox cites.
3. **quickmerge needs `--skip-preflight`** (the flag it documents "for multi-agent use") because deployment-service
   carries foreign-live `terraform.tfvars` → the dirty-deps pre-flight blocks. Verified safe per unit: that tfvars is a
   features-service-sports Cloud Run image pin, unrelated to anything shipped here. Same carve-out as `@62cc10f`.
4. **Post-ship `git show --name-only` is checked EVERY time** to prove quickmerge's whole-file `git add` didn't sweep
   the foreign hunks (the failure mode that produced `12c94be` + `57d913d`). Zero sweeps so far.

**Shipped this session** (see each checkbox for full evidence): A1 `resolved_date`/`requested_date` on
`get_honest_coverage` (deployment-api@4e996f8); A3 new-listings false-positive guard (deployment-api@a9b6207 +
deployment-ui@179c7ce).

**Method note worth keeping**: A3's todo said "quantify the rate (real-GCS query, not a guess)" — doing that FIRST
changed the outcome. The todo's premise ("legacy rows … inflate 'new'") implied a broad legacy problem; the measurement
showed the corpus-wide rate (0.87%) is nearly irrelevant to the actual card, which shows a 30-day window where the rate
is **0.02% and 100% attributable to one venue onboarded 7 days ago**. That reframed the fix from "exclude legacy rows"
(which would have hidden real listings for no measurable benefit) to "surface a fact about the one real cluster". The
guard was then re-verified by driving the _shipped service_ against real GCS, not just its fixtures.

#### SESSION-END STATE — 13 open P2/P3 todos at start → 6 open, of which 2 are NEW bugs found en route

**Shipped + flipped (10 of the 13):** A1 honest-coverage provenance (deployment-api@4e996f8) · A3 new-listings
false-positive guard (@a9b6207 + deployment-ui@179c7ce) · A5 **both** PERF items (@0e39a53) · B1 cefi split-row
canonicalisation **applied on real infra** (instruments-service@e6c31507) · B3 LENDING drain **applied on real infra**
(@e4fdd56c) · B4 `base_asset_contract_address` backend+UI (@13a8f0b + deployment-ui@a860937) · C1 mock-api IS fixtures
(deployment-ui@25262b8) · C2 tarball republish (verified — no code needed) · the "Sports TEAMS" row (a phantom; see the
row-10 correction above — no work existed).

**The recurring lesson: 5 of the 13 todos' premises were WRONG, and only measuring first caught it.** Worth
internalising before trusting this table's remaining rows:

| todo            | its premise                                             | what real data showed                                                                                        |
| --------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| A3              | "legacy rows inflate new-listings"                      | true corpus-wide (0.87%) but **0.02%** inside the window the card shows — one recently-onboarded venue       |
| A5 (prediction) | "~39s; add pagination"                                  | **~173s**, and pagination fixes nothing — the cache KEY was re-paying the whole corpus per page              |
| B3              | "finish the A_TOKEN split for MORPHO/FLUID/AAVE_PLASMA" | already split; re-splitting would write **1,766 duplicate ids**. AAVE_PLASMA doesn't exist; COMPOUND_V3 does |
| B2              | "root-cause remaining DeFi legacy values"               | **0** non-canonical values remain; the real residual is 78,489 **blank** captured rows in cefi/defi          |
| "Sports TEAMS"  | "data-correctness items 1-5"                            | no such work — a mislabelled row pointing at the P4-B UI todo                                                |

**Still open (6) — each reason is recorded on the todo itself; none are "ran out of time":**

1. **B2 cefi/defi captured-blank `instrument_type`** — root-caused in full (writer already fixed; only tradfi was ever
   backfilled) and journalled above; the generalised migration + tests are written and were dispatched to a sub-agent
   with the full rule set. **NOT applied at session end** — live GCS still reads cefi **13,046** / defi **65,443**
   captured-blank. That IS the acceptance metric to re-check: it must reach **0/0**, with non-captured blanks preserved.
2. **A2 `expiry` column** + 3. **A4 `question`/`title` column** — blocked on a live same-file agent **and** a regen race
   (both end in "then regen"; concurrent `prod/catalog.parquet` regens are last-writer-wins and silently drop one side's
   columns). Batch into ONE schema change + ONE regen once that agent's work lands — see the note on the A2 todo.
3. **C3 true-catalogue phase-2** — designed + de-risked, not implemented: the obvious shortcut was prototyped against
   real data and **reverted**, because `prod/catalog.parquet` is captured-derived, not "what exists". A concrete T4-safe
   design (publish an expected-universe projection) + a prerequisite bug (`/catalogue` prediction returns
   `total_count=79`) are written on the todo.
4. **Sports non-canonical `instrument_type`** (NEW) + 6. **DeFi POOL id collides across chains** (NEW) — two real
   correctness bugs found while doing the above, captured as todos per the discovery rule rather than absorbed silently.

**Ship discipline this session**: every unit commit→push→flip in the same turn; every real-infra migration dry-run →
apply → **independently re-read from GCS** (never trusting the script's own log) with a rollback snapshot recorded;
every deployment-api unit A/B'd against HEAD for basedpyright because a concurrent agent keeps that repo's full gate
red. Zero foreign-WIP sweeps — `git show --name-only` checked after every push, so the `12c94be`/`57d913d` failure class
did not recur.

### 2026-07-17 — Playwright re-verification found + fixed a month-old mock-api.ts bug shadowing every /api/data-status/* endpoint

Doing a fresh Playwright pass (mock mode, `VITE_MOCK_API=true`, port 5199) against everything shipped this plan found a
crash in `CatalogueExplorer` (`TypeError: Cannot read properties of undefined (reading 'length')`) on first render, and
found the Prediction Catalogue silently showing "No prediction markets match the current filters" despite the mock
having representative rows for every category. Root cause (traced via `page.evaluate` calling `fetch(...)` directly in
the live page, NOT assumption): `src/lib/mock-api.ts` has had a catch-all
`if (path.match(/^\/api\/data-status/)) { return json(MOCK_DATA_STATUS); }` sitting near the top of the ~2,700-line
`handleRoute` function since `deployment-ui@687d4ce` (2026-06-16) — **every** more-specific
`/api/data-status/<endpoint>` handler added to this file AFTER that date and BEFORE this catch-all's position in file
order (honest-coverage, turbo/manifest, venue-filters, list-files, instruments-for-shard, download-catalogue-csv,
catalogue, instruments, instrument-availability, prediction-catalogue — essentially every data-status mock endpoint
shipped over the past month, including this session's own P2/P3/P6 UI work) was silently shadowed, always receiving the
generic turbo coverage-summary payload instead of its own real response shape. This is exactly why so many earlier
verification passes this session (Phase A, the P3/P6 real-data checks) kept coming back INCONCLUSIVE/empty against mock
mode — the mock layer itself was broken the whole time, independent of whether the actual shipped code was correct.

**Fixed**: moved the catch-all to be the true last-resort fallback (immediately before the function's existing
`404 "Mock: no handler"` response), so every specific handler gets first crack at matching. Also added defensive
`?? []`/`?? 0` fallbacks in `CatalogueExplorer.tsx` for `data.instruments`/`data.total_count` so a future malformed
response degrades gracefully instead of crashing. Verified end-to-end via Playwright:
`fetch('/api/data-status/ catalogue?...')` now returns the correct
`{instruments: [...4 rows], total_count: 4, label: "captured instruments (availability-derived)"}` shape (previously
returned the turbo coverage payload with no `instruments` key at all); `/api/data-status/prediction-catalogue` now
returns 8 rows across all 7 categories. Full-page screenshot confirms both panels render real mock data with correct
capture_status/MVP badges. Full Vitest suite re-run clean (93 files, 990 tests, 0 regressions) — the routing reorder
didn't change behavior for any OTHER endpoint, confirming nothing else in the codebase was relying on the old (buggy)
shadowing behavior. — `deployment-ui@0c817d2`.

**Why this wasn't caught by any of this plan's own Vitest specs**: every affected component's own test file mocks
`fetchInstrumentCatalogue`/`fetchPredictionCatalogue` etc. directly (jest/vitest `vi.mock`), never actually routing
through the real `mock-api.ts` `handleRoute` dispatcher — so unit tests stayed green throughout the entire month this
bug existed. Only a REAL browser hitting the REAL mock server (i.e. what `pw:L2` is supposed to be, not just "Vitest
passed") would ever have caught it. Worth flagging as a broader lesson for this workspace's `[UI] + pw:L2` gate: a
Vitest pass proves the component logic is correct GIVEN its mocked inputs, not that the actual mock-server wiring
delivers those inputs in the browser.
