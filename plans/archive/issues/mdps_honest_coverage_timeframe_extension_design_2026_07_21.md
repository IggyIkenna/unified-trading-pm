---
doc_type: issue
title: >-
  Design for extending MTDS honest-coverage to MDPS (timeframe-aware) -- verified sound on the MTDS-regression lens by 3
  independent reviewers, but a CRITICAL bug (the `service` parameter is never threaded to the one call site that needs
  it) was independently found by all 3, meaning the design's central MDPS-narrowing mechanism is currently dead code as
  specified. NOT implemented -- design + review only.
summary: >-
  A design was produced (this session, 2026-07-21, before a context-compaction boundary) for extending
  `deployment-api`'s MTDS honest-coverage formula (`mtds_honest_coverage_for_venue` / `per_instrument_coverage` /
  `_apply_mtds_honest_coverage`) to also cover MDPS (market-data-processing-service) candle derivation, adding a
  timeframe axis (MDPS derives multiple candle timeframes -- 15s/1m/5m/15m/1h/4h/1d -- per venue/data_type, which MTDS's
  raw-tick model has no equivalent of). Three independent adversarial reviews were then run against the design. All 3
  independently confirmed the design does NOT introduce any MTDS regression (every new parameter is additive with a
  `None`-preserving default, verified against every real call site). But 2 of the 3 reviews (and a 3rd on a related
  angle) ALSO independently found the SAME critical, ship-blocking defect: the design's central mechanism for narrowing
  MDPS's expected-data-type set never actually fires, because the `service` string needed by
  `get_expected_data_types_for_venue(venue, service=...)` is dropped at the eligibility gate
  (`is_mtds_honest_coverage_target`) and never threaded through the 4 intervening function signatures down to the one
  call site that needs it (`mtds.py:629`). Two additional real (non-blocking but real) implementation bugs were also
  found: a pandas index-misalignment in the Tier-3 timeframe branch's own code sample, and a legacy-row fallback branch
  that silently reverts to a non-timeframe-aware formula. Plus 5 open questions the design explicitly declined to
  resolve without operator input (most importantly: does historical MDPS coverage silently drop out of the new
  honest-coverage numerator for any window spanning the 2026-07-21 data_type-axis cutover?). NOTHING HAS BEEN
  IMPLEMENTED. This doc exists so the verified design + the corroborated critical finding are not lost and don't need to
  be re-derived from scratch by whoever picks this up next.
status: resolved
nature: design
asset_group: [cefi, defi, tradfi]
stage: [data]
repos: [deployment-api, unified-api-contracts, market-data-processing-service, unified-trading-library]
scope: [engineer]
tags:
  [
    mdps,
    honest-coverage,
    timeframe,
    deployment-api,
    design,
    adversarial-review,
    service-threading-bug,
    corroborated-finding,
    duplicate-finding,
  ]
related:
  - /plans/archive/issues/mdps_generic_classifier_processed_regression_2026_07_21.md
  - plans/active/data_pipeline_check_mdps_features_2026_07_20.md
  - plans/active/mtds_data_status_page_parity_2026_07_21.md
created: "2026-07-21"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by: >-
  ALREADY SHIPPED under `plans/active/mtds_data_status_page_parity_2026_07_21.md` (same design, same corroborated
  critical bug, same 2 minor bugs, same 2 open questions — all independently found + fixed + resolved there):
  unified-api-contracts@a7798b93 + deployment-api@60a23ae (Tier-3 + service-threading fix), deployment-api@43f067e
  (Tier-2 timeframe-awareness follow-up). See Resolution section below.
locked_by:
source: [self-investigation-2026-07-21, adversarial-review-x3-2026-07-21, promoted-from-scratchpad-2026-07-23]
---

# Provenance / promotion note

This design + its 3 reviews were produced in a prior pass of this same multi-day session (2026-07-21), before a
context-compaction boundary, and were never committed -- they existed only as 4 scratchpad text files
(`mdps_design.txt` + `mdps_review1/2/3.txt`) with zero repo footprint until a `/pre-compact` audit on 2026-07-23 caught
them (Step 1 of that skill: "chat-only findings... exist nowhere on disk"). This doc reproduces that work faithfully.
**Nothing below has been re-verified against the CURRENT (2026-07-23) working tree** -- roughly 2 days of unrelated
concurrent work have landed on `deployment-api`/`unified-api-contracts` since 2026-07-21; file:line citations should be
spot-checked before implementation, though the underlying mechanisms described are unlikely to have changed since none
of this session's other (DeFi/LST-focused) work touched these files.

# Grounding facts the design relies on (as verified 2026-07-21)

1. **Service isolation is already free.** `_build_manifest_category`
   (`deployment-api/deployment_api/services/data_status/manifest.py:798-801`) masks `filtered = index.loc[mask]` where
   `mask = (date range) & (index["service_name"] == service)` BEFORE
   `_build_venue_breakdown`/`_apply_mtds_honest_coverage`/`mtds_honest_coverage_for_venue` ever see the frame. When
   `service == "market-data-processing-service"`, every row the honest-coverage code touches is already MDPS-only.
2. **The manifest carries `timeframe` for every row deployment-api reads.** `_read_index.py:357-361` (`_V8_COLUMNS`)
   lists `timeframe`; `data_status_service.py:449` always reads the full schema. Confirmed by a reviewer to go further
   than claimed: `timeframe` is in `_ROW_KEY_COLUMNS`
   (`unified-trading-library/unified_trading_library/manifest_writer/_rows.py:63,97`) -- it's part of the row-KEY, so
   distinct timeframes produce distinct manifest rows, not overwrites.
3. **MDPS's writer normalizes `timeframe` before the manifest write.** `canonical_writer.py:241`
   (`_normalise_timeframe`, `canonical_writer_shaping.py:194-202`) maps `"24h"` -> `"1d"`. Manifest `timeframe` is
   always `"1d"`, never `"24h"`, for daily candles.
4. **Three DIFFERENT timeframe-token vocabularies exist in the codebase and none matches what the writer emits**:
   `deployment_api/utils/path_combinatorics.py:53` (`PROCESSING_TIMEFRAMES`, has `"24h"`),
   `unified_api_contracts/registry/processed_data_dependencies.py:55` (`_TIMEFRAMES`, has both `"1d"` and `"24h"`,
   missing `"15s"`), and the writer's actual normalized output (`"1d"`, no `"24h"`). A new design must not copy any of
   the three uncritically.
5. **Manifest `data_type` on MDPS rows is bimodal by write-time vintage.** As of commit `752eaff` (2026-07-21, comment
   "Manifest data_type AXIS = SOURCE data_type (operator ruling 2026-07-21)", `canonical_writer.py:513`), rows carry
   SOURCE-keyed `data_type` (`"trades"`, `"derivative_ticker"`) + a real `timeframe`. Rows written before that commit
   carry the legacy aggregated shape (`"ohlcv_1m"`, `"deriv_ohlcv_1h"`). See Open Question 1.
6. **`is_per_instrument_shard_data_type`** (UAC `market_data_categories.py:2196-2203`) already includes both current
   MDPS data_types (`trades`, `derivative_ticker`) -- both route to the Tier-3 per-instrument branch, never the
   venue-level branch, confirming where the design's changes must land.
7. **A SEPARATE, ALREADY-LIVE regression was found as a side effect of fact #5** -- filed as its own doc,
   `mdps_generic_classifier_processed_regression_2026_07_21.md` (do not conflate with this design; it is a live
   production bug, not a design gap).

# The design (condensed -- see the full file:line change list below for implementation)

**(a) `is_mtds_honest_coverage_target`** -- generalize in place (don't rename, don't fork):
`_HONEST_COVERAGE_SERVICES: frozenset[str] = {"market-tick-data-service", "market-data-processing-service"}`, same body
shape otherwise. MDPS reuses `MTDS_CATEGORY_META` as-is for venue-list resolution (both services resolve the same venue
universe per category, confirmed via `SERVICE_TO_KIND`).

**(b) `per_instrument_coverage` / `mtds_honest_coverage_for_venue`** -- add an optional
`timeframes: list[str] | None = None` param to both (and to `_apply_mtds_honest_coverage`), default `None` preserves
every existing MTDS call path byte-for-byte (verified against every real call site, including ~20 test call sites). When
set, the Tier-3 found-set computation becomes a `(instrument_id, timeframe, date)` triple instead of a pair, and the
response gains an optional `per_timeframe` breakdown key + a new `unit` literal `"shard_instrument_timeframe_days"`.

**(c) UAC registry additions** (all additive, new):
`MDPS_DERIVABLE_DATA_TYPES = frozenset({"trades", "derivative_ticker"})` (SSOT replacing deployment-api's local
`PROCESSING_DATA_TYPES`); `MDPS_CANONICAL_TIMEFRAMES = ("15s","1m","5m","15m","1h","4h","1d")` (verified against the
writer's actual output, not copied from any existing divergent list); a new
`service == "market-data-processing-service"` branch in `get_expected_data_types_for_venue` that narrows to
`MDPS_DERIVABLE_DATA_TYPES` (deliberately does NOT fall through to the "footgun fallback" full cross-product).

**(d) Denominator formula**:
`expected_shards(venue, dt) = Σ_instrument |clip(expected_dates, instrument.existence_window)| × |timeframes|` -- clip
once per instrument (unchanged from today), sum, THEN multiply by timeframe count. NOT a blanket
`|instruments| × |dates| × |timeframes|` cross-product (would double-count delisted-instrument days). Conditional on
Open Question 2 (no per-timeframe start-date divergence) -- if that's ever confirmed false, the formula needs
per-timeframe clipping instead of a flat multiply.

**(e) Full file:line change list** (15 items, all additive/new-optional-param -- not reproduced verbatim here to keep
this doc's length sane; the original had exact line ranges for every one of: UAC's 2 new registries + the new `service`
branch, deployment-api's 4 signature changes across
`mtds.py`/`instrument_coverage.py`/`venue_resolution.py`/`manifest.py`, and 2 pre-existing bug fixes in
`path_combinatorics.py`/`processed_data_dependencies.py` needed for the new timeframe vocabulary to be correct).
**Whoever implements this should re-derive the exact line list fresh against the current tree rather than trust
2-day-old citations** -- the STRUCTURE of the change (which functions, in what order, what each does) is the durable
part of this doc; exact line numbers are not.

**(f) Open questions, explicitly NOT resolved -- need operator input before implementation:**

1. **Does `timeframe` get populated on MDPS manifest rows written BEFORE the `752eaff` cutover?** If not resolved,
   historical MDPS coverage silently drops out of the new honest-coverage numerator for any window spanning the cutover,
   understating `completion_pct`. Three options were identified: (a) accept as a known transition artifact with a
   provenance flag, (b) one-time manifest migration relabeling historical rows, (c) a dual-read compat shim matching
   both the legacy and new `data_type` shapes for pre-cutover dates. **This directly affects a data-correctness number
   and should not be decided unilaterally.**
2. **Does any `(venue, data_type)` pair have a per-timeframe start-date divergence** (e.g. `"15s"` candles only enabled
   for a subset of venues, starting later than `"1m"`/`"5m"` for the same venue)? No evidence found either way in the
   code. If yes, the flat-multiply denominator overstates `expected_shards` until a per-`(venue,dt,timeframe)` override
   table is added.
3. **F4 seed-guard interaction** (`mtds.py:469-576`) -- not touched by this design's changes (dispatched before the
   per-instrument branch); whether MDPS's writer ever materializes `expected_unattempted` rows that would hit this
   branch was not verified.
4. Naming of new display strings (`"per_venue_per_data_type_per_timeframe_daily"` / `"shard_instrument_timeframe_days"`)
   not checked against any UI contract.
5. (Covered by the sibling regression doc, not re-listed here.)

# Adversarial review findings (3 independent passes)

All three reviews independently confirmed **no MTDS regression** — every new parameter is additive with a `None`-default
verified against real call sites (including test call sites), the shared LRU cache key is unchanged (timeframe-invariant
by construction, correctly not widened), and no formula change applies unconditionally rather than gated on
`service == MDPS`.

**CRITICAL, ship-blocking, found independently by reviews 1, 2, and 3 (full corroboration):** the design's central
mechanism -- narrowing MDPS's expected-data-type set via a new `service` branch in `get_expected_data_types_for_venue`
-- **never actually fires**. `service` is checked at the eligibility gate
(`is_mtds_honest_coverage_target(service, cat)`) and then dropped; it is not a parameter of
`_apply_mtds_honest_coverage`, `mtds_honest_coverage_for_venue`, or threaded into the
`get_expected_data_types_for_venue(venue)` call at `mtds.py:629` (which calls with no `service=`, defaulting to `""`).
**Concrete impact**: MDPS's `expected_dts` resolves to the FULL raw-tick data-type list for that venue (e.g.
`BINANCE-FUTURES` declares 5 types; the design's own `MDPS_DERIVABLE_DATA_TYPES` covers only 2) instead of the narrowed
MDPS-derivable set. Every extra raw dt shows `expected_shards > 0, found_shards == 0` for the entire window, tanking
`completion_pct` and populating `missing_data_types` with types MDPS was never meant to cover -- the EXACT conflation
bug this design set out to prevent, just relocated one layer down. One reviewer noted the correct pattern already exists
one file away (`breakdowns_core.py:608`, the sibling generic-breakdown builder, which DOES correctly thread `service=`).

**Fix** (small, mechanical, not yet applied): add `service: str = ""` to `_apply_mtds_honest_coverage` and
`mtds_honest_coverage_for_venue`'s signatures; thread `service=service` from `_build_manifest_category` (which already
has `service` in scope as its own first param) down through both calls to
`get_expected_data_types_for_venue(venue, service=service)` at `mtds.py:629`. Default `service=""` reproduces today's
exact MTDS behavior, so this fix is itself additive/safe.

**Real, non-blocking implementation bugs found (2 of 3 reviews, different specific manifestations of the same root cause
-- the design's timeframe branch wasn't checked against the function's existing legacy/non-legacy row split):**

- A pandas index-misalignment: the design's own Tier-3 code sample builds `tf_str` from the UNFILTERED `dt_rows` while
  `iid_str`/`rd_str` are built from an already-masked subset (`non_legacy_mask`) -- whenever a (venue, dt) slice has
  even one legacy row mixed with non-legacy rows (exactly the partial-migration state Open Question 1 flags as
  plausible), the differing-length/index series will misalign under pandas' index-aligning `&`, either raising or
  silently corrupting the mask. Fix: derive `tf_str` from the same masked slice.
- The legacy-row-fallback branch (`instrument_coverage.py:365-382`, fires when a whole (venue,dt) slice is
  legacy-shaped) is never touched by the timeframe parameter at all -- it returns a plain per-date count with no
  `len(timeframes)` multiplier, silently reverting to a non-timeframe-aware formula and creating a unit mismatch against
  the Tier-3 branch's output within the same accumulation loop.

**What the design got right, verified not just trusted:** the process-pool/subprocess concurrency boundary
(`build_category_in_subprocess`'s fixed pickle-crossing signature) is correctly handled -- the design computes
`timeframes` INSIDE `_build_manifest_category` using locals that already cross all 3 concurrency paths (process-pool,
thread-pool, serial) unchanged, so no new parameter needs to cross the pickle boundary. This also correctly covers the
offline rollup worker, which calls the same function via the serial path. Also confirmed:
`_SERVICE_CATEGORY_RESTRICTIONS["market-data-processing-service"] = {"CEFI","TRADFI","DEFI"}` (`defi.py:138`) means MDPS
never reaches SPORTS/PREDICTION, so reusing the shared category-meta table without forking it is safe.

**Minor/cosmetic findings, not blocking:** a citation-range imprecision (function actually spans further than cited);
the "prerequisite" framing on one item overstates an actual dependency (the new timeframe vocabulary is independently
hardcoded, not derived from the buggy old constant, so fixing the old constant first isn't strictly required, just good
hygiene); a second, entirely separate `completion_pct` surface
(`deployment-api/deployment_api/services/data_status/coverage.py:295-429`, the offline rollup worker's own tally) is
never mentioned in the design and would remain out of scope/not-timeframe-aware -- worth one sentence in any future spec
noting this explicitly so a reader doesn't assume full coverage.

# Status: NOT implemented

Zero code has been written for this design. It is blocked on: (1) the corroborated critical `service`-threading fix
(small, mechanical, described above), (2) the 2 non-blocking implementation bugs (also described above), and (3) an
operator decision on Open Question 1 (historical-coverage cutover handling) at minimum before this should ship, since it
directly affects a data-correctness number.

# Deferred work after 2026-07-21 (filed 2026-07-23)

| Item                                                                                        | State       | Blocked on                                                              |
| ------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------- |
| Re-verify all file:line citations against the current (2026-07-23+) tree                    | Not done    | Nobody -- 2 days of drift risk, do this before implementing             |
| Fix the corroborated critical `service`-threading bug                                       | Not done    | Nobody -- small, mechanical, described above in full                    |
| Fix the 2 non-blocking implementation bugs (index misalignment, legacy-fallback gap)        | Not done    | Nobody -- described above in full                                       |
| Operator decision: Open Question 1 (historical coverage cutover handling)                   | Not done    | Operator-owned -- data-correctness decision, do not decide unilaterally |
| Operator/factual answer: Open Question 2 (per-timeframe start-date divergence)              | Not done    | Operator-owned -- factual question about MDPS's real deployed config    |
| Implement the design once the above are resolved                                            | Not done    | All of the above                                                        |
| `mdps_generic_classifier_processed_regression_2026_07_21.md` (the separate live regression) | Filed, open | See that doc -- independent of this design's fate                       |

**Recommended next item**: re-verify citations against the current tree, then fix the critical `service`-threading bug
(cheapest, unblocks the rest), then bring Open Questions 1 and 2 to the operator before writing any new production code.

# Resolution (2026-07-23) — the whole design was already implemented, ship-blocking bug and all

While starting on the "recommended next item" above, reading `mtds.py`/`instrument_coverage.py`/
`processed_data_dependencies.py` against the current tree showed the design is not merely re-derivable — **it has
already been implemented, reviewed, and shipped**, under `plans/active/mtds_data_status_page_parity_2026_07_21.md`'s
"MDPS parity" todos (the same parent effort this design's own provenance note names as where it was produced alongside).
This doc's "rescue" from scratchpad on 2026-07-23 promoted a design that a different concurrent session had already
carried all the way to production in the intervening two days — a genuine parallel-discovery collision, not wasted
original work (the design + reviews were real and correct at the time they were written).

Point-by-point, everything this doc flagged as blocking is resolved in the shipped work:

- **The corroborated critical `service`-threading bug**: fixed exactly as this doc's own "Fix" section prescribed —
  `service` now threads `manifest.py` → `_apply_mtds_honest_coverage` → `mtds_honest_coverage_for_venue` →
  `get_expected_data_types_for_venue`. Shipped `unified-api-contracts@a7798b93` + `deployment-api@60a23ae`, verified by
  an independent second agent re-reading the diff and re-running both test suites from scratch (977 deployment-api
  - 44 UAC registry tests, zero regressions).
- **The 2 non-blocking implementation bugs** (pandas index-misalignment; legacy-row-fallback gap): both fixed in the
  same ship — `tf_str` now derived from the same masked slice, and the legacy fallback gained both a `len(timeframes)`
  multiplier and an explicit `denominator_timeframe_aware: false` provenance marker.
- **Open Question 1** (historical pre-cutover row visibility): resolved by direct production-data investigation, not a
  coin-flip default — the live manifest has exactly 6 total MDPS rows, all a single 2026-04-16 smoke-test write, so
  there is no real historical volume to backfill or reverse-map. Currently MOOT, with an explicit re-open trigger (real
  MDPS production volume appearing in the manifest) rather than closed as permanently settled.
- **Open Question 2** (per-timeframe start-date divergence): same investigation — sample size of 1 real row is too small
  to prove or disprove anything; the shipped flat-uniform `MDPS_CANONICAL_TIMEFRAMES` default stands, unconfirmed but
  unfalsified, with the same re-open trigger.
- **Tier-2 (venue-level) timeframe-awareness**, explicitly out of this design's original scope: also since shipped as a
  follow-up, `deployment-api@43f067e`.
- **The sibling classifier regression** (this doc's own fact #7): confirmed independently resolved too — see the
  `Resolution` section on `mdps_generic_classifier_processed_regression_2026_07_21.md`.

**What is NOT a duplicate and is genuinely new, separate work**: the same parent plan's final `[UI]` P1 todo found that
the backend `scope` param this work (and its sibling MVP-wiring todos) shipped had **zero UI-reachable consumer** —
neither `getDataStatusManifest` nor `getDataStatusTurbo` in `deployment-ui/src/api/client.ts` ever sent a `scope` param,
and there was no page-level toggle on the shared coverage grid. That gap has now been closed (2026-07-23): both client
functions thread an optional `scope: CoverageScope` param, and `DataStatusTab.tsx` renders a page-level "Coverage Scope"
toggle on all three services (instruments-service / market-tick-data-service / market-data-processing-service),
live-verified via dev server + Playwright MCP, regression-locked in
`deployment-ui/tests/smoke/mtds_mdps_data_status_parity_2026_07_22.spec.ts`. See
`mtds_data_status_page_parity_2026_07_21.md`'s Progress Log for the shipped SHA.

Nothing further to do on this design doc. Whoever next touches MDPS timeframe-aware honest coverage should start from
the shipped code + `mtds_data_status_page_parity_2026_07_21.md`'s Progress Log, not from this design.
