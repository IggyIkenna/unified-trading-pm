---
doc_type: issue
title: >-
  defi swaps_ohlcv_* MDPS-derived candle data_types missing from DATA_TYPES_BY_ASSET_GROUP['defi'] — real registry gap,
  but the fix is a UAC canonical-set addition whose denominator blast radius needs measuring first
summary: >-
  D6 sub-investigation of distinct_values_noncanonical_audit_2026_07_20.md's "D5/D6" todo. Confirmed
  swaps_ohlcv_{15s,1m,5m,15m,1h,4h,1d} are real, correctly-produced MDPS Phase-5b.1 processed-candle SchemaContracts
  (market_data_processing_service's DefiSwapAdapter, registered UAC internal/schemas/_candle_contracts.py), not a writer
  bug and not a "wrong coverage.json section read" — the distinct-values detector's defi.data_types axis is seeing
  genuine MDPS output. The gap is that DATA_TYPES_BY_ASSET_GROUP['defi'] never got these 7 keys added, while the
  analogous MDPS candle keys for cefi (ohlcv_1m) and tradfi (ohlcv_1s/1m/15m/24h) already ARE present. The
  conceptually-correct fix is adding them to DATA_TYPES_BY_ASSET_GROUP['defi'] (same class other asset_groups already
  did) — but traced the mechanism (instruments-service enumerate_expected_universe.py::enumerate_v2's generic branch
  cross-joins DATA_TYPES_BY_ASSET_GROUP[ag] against the full catalog x date_axis) and found tradfi ALREADY needed a
  dedicated exclusion list (_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES) to stop an analogous cross-service data type
  from seeding permanently-unsatisfiable expected_unattempted/attempted_failed cells into the wrong manifest. Adding 7
  defi keys without an equivalent guard would very likely repeat that exact failure mode. Declined to execute the
  registry addition this session (matches this same plan's own RESULT 4 "UAC canonical-set additions are NOT safe-code"
  caution, and the AUTONOMOUS_AGENT_RULES stop-short precedent already used by the sibling perp_daily_ctx task on this
  same plan) — documented the live row-count evidence + both remediation paths for the next session/operator to choose
  from.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-data-processing-service, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    honest-coverage,
    canonicalisation,
    data_types,
    candle-processing,
    mdps,
    manifest,
    distinct-values,
    denominator-blast-radius,
  ]
related:
  [
    plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
    plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
    plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
  ]
created: "2026-07-22"
last_updated: "2026-07-22"
parent_epic: manifest_master
priority: P2
source: >-
  distinct_values_noncanonical_audit_2026_07_20.md's D5/D6 todo (~line 328), dispatched to a sub-agent under /autonomous
  with an explicit precedent to stop short if the fix requires an unmeasured UAC canonical-set/denominator addition
  (mirrors the sibling perp_daily_ctx todo's own stop-short outcome on this same plan)
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    instruments-service/scripts/enumerate_expected_universe.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
---

# defi `swaps_ohlcv_*` MDPS candle data_types — real registry gap, fix needs a denominator blast-radius measurement

## Verdict

**Did NOT add `swaps_ohlcv_{15s,1m,5m,15m,1h,4h,1d}` to `DATA_TYPES_BY_ASSET_GROUP['defi']`.** Confirmed these are real,
legitimate, correctly-produced MDPS candle output (not junk, not a wrong-section-read detector bug) — the
conceptually-correct disposition genuinely is a UAC canonical-set addition. But traced the exact denominator mechanism
this would feed and found a directly analogous precedent (tradfi) where the SAME kind of addition, done without a
dedicated exclusion, created permanently-unsatisfiable manifest cells. Stopping short here, documenting both remediation
paths, per this plan's own RESULT 4 caution + the AUTONOMOUS_AGENT_RULES stop-short precedent already used by the
sibling `perp_daily_ctx` todo on this same plan. No code changed in unified-api-contracts, instruments-service, or
market-data-processing-service.

## What the source todo asked for (paraphrased)

`distinct_values_noncanonical_audit_2026_07_20.md`'s "D5/D6" todo (~line 328): "D5/D6 — bundle-grain
(`futures_chain`/`options_chain`/`combo`) recognition + scoping the `data_types` axis away from MDPS `processed_candles`
(`swaps_ohlcv_*`)." D5 (bundle-grain) is executed separately (see that plan's Progress Log,
`unified-api-contracts@<sha>` + `deployment-api@<sha>` this session) — this doc is D6 only.

Framing hypothesis in the source todo: the detector's `defi.data_types` axis enumeration might be reading from a
coverage.json section that MIXES MTDS raw-tick data_types with MDPS-derived candle data_types when it should only be
looking at one for this axis — i.e. possibly a "wrong section read" cross-contamination bug.

## Established facts (verified this session, file:line evidence)

1. **`_AXIS_SOURCES` in `deployment-api/deployment_api/routes/data_status/_distinct_values.py` is NOT
   asset-group-specific — it reads the SAME `by_venue_data_type` coverage.json section uniformly for every
   asset_group.** This rules out "wrong section read" as the mechanism — there is only one section, correctly used for
   all five asset_groups. The hypothesis in the source todo does not hold as stated.

2. **`swaps_ohlcv_{tf}` is a real, deliberately-registered MDPS Phase-5b.1 processed-candle output**, not a writer bug:
   - `unified-api-contracts/unified_api_contracts/internal/schemas/_candle_contracts.py` (module docstring): "MDPS
     processed-candle SchemaContracts — Phase 5b.1 ... co-located inside the MTDS tick buckets under
     `processed_candles/`" — lists the exact source→output mapping: `dex_pool_swaps → swaps_ohlcv_{tf}`, with DeFi
     timeframes `{15s, 1m, 5m, 15m, 1h, 1d}` (note: NOT `4h` — see finding 6 below).
   - `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py::NEEDS_CANDLE_PROCESSING`:
     `"dex_pool_swaps": True` — candle-derivable by design.
   - `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py::_DATA_TYPE_TO_MDPS_PREFIX`
     (referenced via
     `market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py`):
     `"dex_pool_swaps": "swaps_ohlcv"`, `"dex_swaps": "swaps_ohlcv"` —
     `mdps_data_type_key("dex_pool_swaps", tf) == f"swaps_ohlcv_{tf}"`.
   - `market-data-processing-service/market_data_processing_service/app/adapters/defi/swap_adapter.py::DefiSwapAdapter`
     — registered `@CandleAdapterRegistry.register(MarketAssetGroup.DEFI, "dex_pool_swaps")`, the real code that
     produces these candles from raw `dex_pool_swaps`/legacy `dex_swaps`/`swaps` tick data.

3. **Other asset_groups' analogous MDPS candle keys ARE already present in `DATA_TYPES_BY_ASSET_GROUP`** — this is NOT a
   defi-specific design decision to keep candle keys out of the axis; it is an inconsistency:
   - `DATA_TYPES_BY_ASSET_GROUP["cefi"]` includes `"ohlcv_1m"` (the `trades → ohlcv_{tf}` MDPS key, one timeframe only —
     the family's OTHER candle keys `book5_ohlcv_*`/`deriv_ohlcv_*`/`liq_agg_*` are NOT present, despite MDPS also
     producing those from `book_snapshot_5`/`derivative_ticker`/`liquidations`).
   - `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` includes `"ohlcv_1s"`, `"ohlcv_1m"`, `"ohlcv_15m"`, `"ohlcv_24h"` (4 of the 6
     declared TradFi timeframes `{1m, 5m, 15m, 1h, 4h, 1d}` per the same docstring — `5m`/`1h`/`4h` are missing, and
     `1s` is present despite not being in the declared TradFi timeframe list at all).
   - `DATA_TYPES_BY_ASSET_GROUP["sports"]` includes `"odds_horizon_bucket"` (bare, no per-timeframe suffix — a DIFFERENT
     registration convention, timeframe carried in a separate manifest column; this is the shape the
     `odds_horizon_bucket_{15m,1h,4h,1d}` re-stamp fix, already shipped this session, made the manifest match).
   - **Conclusion: `DATA_TYPES_BY_ASSET_GROUP` candle-key population is ad hoc and incomplete across every asset_group
     that has one — defi is simply the one where NONE of its family (`swaps_ohlcv_*`) was ever added, not a case of
     "defi's axis correctly excludes candle keys on principle."**

4. **Live row-count evidence** (2026-07-21 full honest-coverage rollup, `by_venue_data_type.defi`, aggregated across all
   defi venues):

   | data_type         | captured | attempted_failed | empty_confirmed |  total |
   | ----------------- | -------: | ---------------: | --------------: | -----: |
   | `swaps_ohlcv_15s` |   51,989 |           25,630 |             289 | 77,908 |
   | `swaps_ohlcv_1m`  |   51,989 |           25,629 |             270 | 77,888 |
   | `swaps_ohlcv_5m`  |   51,988 |           25,632 |             262 | 77,882 |
   | `swaps_ohlcv_15m` |   51,987 |           25,636 |             245 | 77,868 |
   | `swaps_ohlcv_1h`  |   51,987 |           25,635 |             204 | 77,826 |
   | `swaps_ohlcv_4h`  |   51,985 |           25,614 |             179 | 77,778 |
   | `swaps_ohlcv_1d`  |   51,985 |           25,603 |             163 | 77,751 |

   ~364K real captured candle rows total across the 7 timeframes — substantial, real, ongoing production MDPS output,
   not a fluke or a one-off backfill artifact.

5. **The correct disposition IS conceptually a `DATA_TYPES_BY_ASSET_GROUP['defi']` addition** (not an
   accepted-exception, unlike the tradfi `options_chain`/`futures_chain` data_types fix shipped earlier this session on
   the same plan) — those were excluded from the canonical set because they are conceptually
   INSTRUMENT_TYPES-at-the-wrong-axis; `swaps_ohlcv_*` has no such category mismatch, it genuinely IS a data_type, in
   the exact same sense `ohlcv_1m`/`odds_horizon_bucket` already are for their asset_groups.

6. **The mechanism this addition would feed, traced exactly**:
   `instruments-service/scripts/enumerate_expected_universe.py::enumerate_v2` resolves the per-asset_group data_types
   list to iterate as: sports → its own provider-scoped list; tradfi → `_tradfi_mtds_tick_manifest_data_types()` (==
   `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` MINUS `_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`); **every other
   asset_group (including defi) → the generic fallback
   `[str(dt) for dt in DATA_TYPES_BY_ASSET_GROUP.get(asset_group, [])]`, cross-joined against the FULL instrument
   catalog x date_axis** to materialise `expected_unattempted`/`empty_confirmed` rows for the `completeness_pct`
   denominator. Adding 7 new defi data_types here would multiply the defi denominator by those 7 keys across every defi
   instrument x every historical date — most of which never had (and structurally never will have) an MDPS candle row,
   since MDPS candle production only covers a bounded recent processing window, not the full historical catalog-x-date
   grid this enumerator assumes.

7. **A directly analogous failure already happened and was patched — for tradfi, not defi.**
   `_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` (`enumerate_expected_universe.py`, citing
   `plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` finding 3)
   exists SPECIFICALLY because two data_types in `DATA_TYPES_BY_ASSET_GROUP["tradfi"]`
   (`corporate_action_confirmed`/`earnings_result`) are captured by a DIFFERENT service into a DIFFERENT bucket
   (features-service's calendar module, not MTDS) — seeding them into this enumerator's MTDS-tick-manifest
   expected-universe creates "a permanently-unsatisfiable cell (100% `attempted_failed` by construction; no amount of
   retrying the MTDS backfill will ever close it)". **`swaps_ohlcv_*` is the identical shape of problem for defi**: MDPS
   (a different service, writing to `processed_candles/`, not MTDS's raw-tick manifest) is the real producer. Adding
   these 7 keys to `DATA_TYPES_BY_ASSET_GROUP['defi']` WITHOUT an equivalent defi-scoped exclusion in `enumerate_v2`'s
   generic branch (which, unlike tradfi's branch, has no such carve-out today) would very likely reproduce this exact
   failure mode fleet-wide for defi — permanently non-zero `attempted_failed`/`expected_unattempted` counts that no
   backfill can ever close, dragging down `completeness_pct` for every defi venue×instrument×date cell this enumerator
   iterates.

## Why the registry addition is declined this session (risk assessment)

Adding 7 new entries to `DATA_TYPES_BY_ASSET_GROUP['defi']` is exactly the class of change this same plan's own RESULT 4
already flagged as **NOT automatically safe-code**: it expands what `enumerate_expected_universe.py` treats as the
could-exist denominator, and (per finding 7 above) has a concrete, precedented failure mode when the real producer
writes to a different service/bucket than the enumerator assumes. Fully bounding the blast radius requires either (a)
building a defi-scoped exclusion list mirroring `_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` FIRST (so this
enumerator never tries to seed `swaps_ohlcv_*` expectations into the MTDS raw-tick manifest at all), or (b) running the
full `enumerate_expected_universe.py` + `measure_honest_coverage.py` pipeline with the hypothetical addition and diffing
`completeness_pct` across the entire defi fleet before/after — neither of which is a quick, low-risk, in-session check.
This mirrors the sibling `perp_daily_ctx` todo's own stop-short outcome on this exact plan
(`plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`), which the AUTONOMOUS_AGENT_RULES for
this dispatch explicitly cite as the model for when stopping short is the right call.

## Two remediation paths (proposed, NOT executed — operator/next-session choice)

**Path A — the conceptually-correct fix (recommended if the exclusion-list work is done first).**

1. Add a `_DEFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`-style guard (mirroring
   `_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` exactly) to `enumerate_expected_universe.py`'s defi resolution path
   FIRST, scoped to the 7 `swaps_ohlcv_*` keys (they are MDPS-produced, not MTDS-produced — same shape as the tradfi
   calendar exclusion).
2. THEN add `swaps_ohlcv_{15s,1m,5m,15m,1h,4h,1d}` to `DATA_TYPES_BY_ASSET_GROUP['defi']` (registry package,
   `unified-api-contracts`) — this makes them canonical for the distinct-values panel AND every other UAC consumer that
   reads this constant (validity matrices, UI reference-data generation, `mvp_scope`, etc — the same cross-cutting
   breadth the tradfi exclusion's own comment calls out as the reason its exclusion is scoped to the enumerator file
   only, not the registry constant itself).
3. Measure before/after `completeness_pct` for defi (expected: ZERO change, since step 1's exclusion should make the
   addition inert for the denominator) — cite the measurement, don't assume it.

**Path B — the lower-risk stopgap (mirrors the tradfi `options_chain`/`futures_chain` data_types fix shipped earlier
this session), if Path A's exclusion-list work is not prioritized soon.** Add an accepted-exception entry
`("data_types", "defi")` → a new
`DEFI_CANDLE_ACCEPTED_NONCANONICAL_DATA_TYPES = frozenset({"swaps_ohlcv_15s", "swaps_ohlcv_1m", "swaps_ohlcv_5m", "swaps_ohlcv_15m", "swaps_ohlcv_1h", "swaps_ohlcv_4h", "swaps_ohlcv_1d"})`
(mirroring `TRADFI_CHAIN_SNAPSHOT_ACCEPTED_NONCANONICAL_DATA_TYPES`'s exact mechanism in
`deployment-api/deployment_api/routes/data_status/_distinct_values.py::_ACCEPTED_EXCEPTIONS`). Zero denominator risk
(accepted-exceptions never touch `DATA_TYPES_BY_ASSET_GROUP`/`enumerate_expected_universe.py` at all — deployment-api
local only), silences the panel finding immediately, but is a less accurate label: these values are NOT a permanent
"never going to be fixed" case the way the tradfi bundle-grain values are — they arguably SHOULD eventually be
first-class canonical data_types, matching cefi/tradfi/sports's own (partial) precedent. Flag this semantic tradeoff
explicitly to whoever picks this up, rather than silently treating Path B as equivalent to Path A.

**Also worth noting, NOT part of either path**: `swaps_ohlcv_4h` has real captured data (51,985 rows) despite `4h` not
being in `_candle_contracts.py`'s own declared DeFi timeframe set `{15s, 1m, 5m, 15m, 1h, 1d}` — either the docstring is
stale or `4h` candles are being produced outside the documented timeframe policy. Whoever executes Path A/B should
reconcile this (add `4h` to the declared set, or investigate why it's being produced) rather than silently including it
in a registry/exception addition without addressing the discrepancy.

## What was deliberately NOT touched (collision avoidance / already-owned-elsewhere)

- **`dex_pools`/`dex_swaps`/`rate_indices`** (the other 3 of the original 10 `defi.data_types` non-canonical values from
  the 2026-07-20 ground truth) — confirmed these are STILL live, real, substantial raw manifest values today (2026-07-21
  rollup: `dex_pools` 454,077 captured / `dex_swaps` 3,458,668 captured / `rate_indices` 49,096 captured), but they are
  kebab/snake/legacy-name naming-drift ALREADY extensively tracked by
  `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (its own dedicated migration scripts:
  `instruments-service/scripts/canonicalize_defi_manifest_data_types_option_g_2026_05_16.py`,
  `market-tick-data-service/scripts/fold_legacy_solana_defi_to_consolidated_canonical_2026_07_21.py`, and ~15 other
  references across that catalogue doc). This is category-1 (owned by an in-flight plan), not part of D5/D6's scope —
  the "FOLDED + DELETED 2026-07-21" note in this plan's own Progress Log refers to a DIFFERENT thing (GCS legacy
  top-level object PREFIXES `dex_pools/`/`lending_indices/`, not the `data_type=dex_pools` manifest COLUMN VALUE, which
  is a separate, still-open naming migration on the catalogue plan). Not touched here.
- **`lending_indices`** — already canonical (present in `DATA_TYPES_BY_ASSET_GROUP['defi']` today), consistent with it
  being the CURRENT name the `rate_indices`→`lending_indices` migration is moving toward.
- **`perp_daily_ctx`/`perp_mark_price`** — already investigated + stopped-short by a sibling agent this session; see
  `plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`. Not re-touched.
- No code changed in `unified-api-contracts`, `instruments-service`, or `market-data-processing-service` for this D6
  item (the D5 bundle-grain fix shipped separately this session touched `unified-api-contracts` + `deployment-api` only
  — different files, different axis).

## Todos (for whoever picks this up next — NOT dispatched automatically)

- [x] [VERIFY] P2. Confirm the exact `completeness_pct` before/after impact of adding an
      `_DEFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`-style guard vs. adding the 7 keys WITHOUT one — a small, bounded,
      read-only simulation against `enumerate_expected_universe.py` (or a scoped subset of the defi catalog) rather than
      a full production re-run. Answers whether Path A is safe to execute directly or needs the guard built first. —
      **EXECUTED 2026-07-28 (slot-5), see "## Progress Log" below for the measurement.** Verdict: **the guard is
      REQUIRED** — without it, adding the 7 keys permanently drags `completeness_pct` down by ~20.6% (relative), zero
      recoverable via any amount of MTDS backfill; with the guard, the addition is provably (not just expected) inert —
      zero denominator delta.
- [ ] [CODE] P2. (Gated on the verify above.) Execute Path A: add the defi-scoped exclusion guard to
      `enumerate_expected_universe.py`, THEN add the 7 `swaps_ohlcv_*` keys to `DATA_TYPES_BY_ASSET_GROUP['defi']`,
      measuring + citing the before/after `completeness_pct` delta (expected: zero, if the guard is correctly scoped).
      Repos: instruments-service, unified-api-contracts.
- [ ] [CODE] P3. Alternatively/interim, execute Path B (accepted-exception stopgap) if Path A is not prioritized soon —
      lower engineering cost, zero denominator risk, but flag the semantic tradeoff (these are not a "permanent,
      never-fixed" case the way tradfi's bundle-grain values are) to whoever approves it.
- [x] [VERIFY] P3. Reconcile the `swaps_ohlcv_4h` timeframe discrepancy (real captured data exists at a timeframe not in
      `_candle_contracts.py`'s declared DeFi timeframe set) before either path ships. — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - the gating VERIFY was executed 2026-07-28 with a
  decisive measured verdict (guard REQUIRED, then provably inert) — Path A is now fully specified

### 2026-07-28 (slot-5) — completeness_pct denominator-delta simulation (bounded, read-only)

Executed the P2 VERIFY todo above via `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s dispatch of this exact item.
Ship no registry/code change (per that todo's own instruction) — report only.

**Method.** `instruments-service/scripts/enumerate_expected_universe.py` could not be imported directly in this venv
snapshot: `ImportError: cannot import name 'iter_route_contexts' from 'fastapi.routing'`, a **pre-existing, already-
tracked, fleet-wide environment issue** (`issues/fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md` —
unified-trading-library's fastapi/starlette floor bump vs. the canonical-dependency-manifest SSOT), unrelated to this
task and not fixed here. Worked around it by re-implementing `enumerate_v2`'s documented per-instrument-grain contract
exactly as specified in its own docstring ("yield one `ExpectedRow` per `(instrument_id, date, data_type)` triple where
the instrument is NOT alive on that date (`empty_confirmed`) OR is alive but has no manifest row
(`expected_unattempted`)"), while importing the ONE live registry input that actually changes between scenarios —
`unified_api_contracts.registry.market_data_categories.DATA_TYPES_BY_ASSET_GROUP['defi']` — for real, not hardcoded.
Bounded synthetic catalog (12 defi swap-pool instruments, all alive for the whole window) × a 30-day date axis (NOT a
full prod re-run, zero GCS/network reads) with an empty `present_set` (mirrors reality for `swaps_ohlcv_*` today: the
MTDS-tick manifest present_set never contains a row for these MDPS-produced keys — MDPS writes to `processed_candles/`,
a structurally different bucket/path — confirmed by this doc's own "Established facts" § finding 2).

**Live count today**: `DATA_TYPES_BY_ASSET_GROUP['defi']` = **27** data_types (not the ~25 estimated by eyeballing the
registry source — counted programmatically).

**Three scenarios, same bounded catalog/date_axis:**

| Scenario                            | data_types resolved | expected rows (12 instr × 30 days × N types) |
| ----------------------------------- | ------------------: | -------------------------------------------: |
| 1. Baseline (today, no addition)    |                  27 |                                        9,720 |
| 2. WITHOUT guard (+7, no exclusion) |                  34 |                                       12,240 |
| 3. WITH guard (+7, then excluded)   |                  27 |                                        9,720 |

**Decisive result — WITH guard is provably inert, not just "expected."** Scenario 3's `resolved_data_types` set is
`sorted(with_guard_data_types) == sorted(CURRENT_DEFI)` → **True**, i.e. byte-identical to today's list. Since
`enumerate_v2`'s entire output is a pure function of `(catalog, date_axis, resolved_data_types)`, an identical
`resolved_data_types` with the same catalog/date_axis structurally GUARANTEES identical output — this holds for ANY real
catalog/date_axis, not just the bounded 12×30 sample used here. **Scenario 3 row count == Scenario 1 row count: True,
delta = 0.** This mirrors `_tradfi_mtds_tick_manifest_data_types()`'s own proven pattern exactly.

**WITHOUT guard — measured, scale-invariant impact.** New rows added = 2,520 (= 12 × 30 × 7, sanity-checked). Framed as
a fraction of the new (bigger) denominator: 2,520 / 12,240 = **20.59%** — and because this is a ratio of `7 new keys` /
`34 total keys` it is **scale-invariant**: the same 20.6% figure holds regardless of catalog size or date-axis length
chosen, since every instrument-day contributes proportionally to both old and new keys equally. Since `present_set` has
zero matches for any of the 7 new keys in the real MTDS-tick manifest (confirmed structurally — MDPS's real output lives
in a different bucket/path this present_set never queries), **100% of that 20.6%-of-denominator share would land as
`expected_unattempted`/`empty_confirmed` with ZERO possible satisfaction via any amount of MTDS backfill** — i.e. for
any current defi `completeness_pct` baseline `C`, the post-addition value without the guard becomes
`C × (27/34) ≈ C × 0.7941` — a **permanent ~20.6% relative drop**, not a transient one, matching exactly the failure
mode `_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` was built to prevent for tradfi.

**Note on completeness_pct terminology** — this simulation targets the MTDS-tick-manifest `expected_unattempted`
denominator `enumerate_expected_universe.py::enumerate_v2` materialises (the mechanism this doc's finding 6 traced).
This is a **different** completeness_pct computation from `check_enumeration_completeness.py`'s Layer-1
venue/instrument_type metric (used elsewhere, e.g.
`/plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md`'s cited
`n_expected=109`/`completeness_pct=2.75` figure) — the two share a name but different denominators/producers; flagging
explicitly to avoid conflating them.

**Answer to the gating question** (for `defi_satellite_ao_dispatch_batch5_2026_07_27.md`'s gated `[CODE]` todo): **the
exclusion-guard IS required** — do not execute Path A's registry addition without first landing the
`_DEFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`-style guard in `enumerate_expected_universe.py`. The verification script
was ad-hoc/scratch-only (not committed, per this todo's "ship no registry/code change" instruction) — the method above
is fully reproducible from this description alone (live `DATA_TYPES_BY_ASSET_GROUP['defi']` import + the documented
`enumerate_v2` cross-join contract).

- **context-scout 2026-08-01**: populated context_scope (5 entries).

## Not fixed here, why

This is a stop-and-document outcome per this task's explicit AUTONOMOUS_AGENT_RULES precedent (mirroring the sibling
`perp_daily_ctx` todo), not a completed registry addition. See "Verdict" above.
