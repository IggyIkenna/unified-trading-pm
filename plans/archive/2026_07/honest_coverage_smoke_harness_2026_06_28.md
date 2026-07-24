---
doc_type: plan
title: Honest-coverage smoke-test harness — RUNNABLE / INSUFFICIENT-HISTORY / HONEST-EMPTY per AG×venue×data_type
summary:
  Build a harness that walks the availability manifest to classify every AG×venue×data_type×instrument shard as RUNNABLE
  (continuous window) / INSUFFICIENT-HISTORY (partial → must FAIL) / HONEST-EMPTY (no data → handled), with
  product-shaped required windows, so we can smoke-test MDPS+features over the span each path actually needs.
status: complete # (was: active) 2026-07-15 plan-reconcile §7-residual: operator ruling A (archival + codex-sync); verified 0 open todos, evidence spot-checked
nature: process
asset_group: [cross-cutting]
stage: [data, backtest]
repos: [e2e-testing, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    smoke-test,
    honest-coverage,
    manifest,
    capture-status,
    insufficient-history,
    honest-empty,
    coverage-matrix,
    sports-seasonal,
  ]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ./mvp_for_mdps_and_features_universe_uac_2026_06_28.md,
    ../epics/batch_live_symmetry_master.md,
  ]
created: 2026-06-28
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
last_updated: 2026-06-28
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [mvp_for_mdps_and_features_universe_uac_2026_06_28]
source: [operator request 2026-06-28]
assigned_role: data_engineering
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
gate_on_depends: true
---

# Honest-coverage smoke-test harness

The goal you set: find where we have **honest, good coverage** for tick data, candle data, and every data_type×venue
combo across all asset groups, so we can smoke-test that the MDPS+features code path actually works over the time span
it needs — and **fail loudly** where coverage is only partial, rather than silently testing half a window.

**Execution model:** Opus / thinking high for the DESIGN (cross-AG synthesis over the manifest semantics +
product-shaped windows). Sonnet for the implementation once the classification contract is fixed.

**Prereq:** Plan 3 (MVP universe) — the harness iterates the MVP-for-MDPS universe and knows which combos carry features
vs candles-only.

## Classification contract (rides the existing 4-state capture_status — no new bookkeeping)

| State                    | Meaning                                                         | Smoke-test behaviour                                  |
| ------------------------ | --------------------------------------------------------------- | ----------------------------------------------------- |
| **RUNNABLE**             | continuous coverage over the required window                    | run the path; it MUST succeed                         |
| **INSUFFICIENT-HISTORY** | only a partial window present                                   | **FAIL** — never run partial                          |
| **HONEST-EMPTY**         | genuinely no data (e.g. no trades that day / `empty_confirmed`) | handled, not a failure — assert the path tolerates it |

## Required-window is product-shaped

- **Sports / seasonal** — a long _continuous_ instrument-and-market pipeline across seasons (markets open/settle; need
  cross-season continuity, not a single day).
- **Max-daily-aggregation data types** — a single day is enough (the path only ever aggregates within a day).
- Everything else — a declared lookback window per (AG, data_type).

## Todos

- [x] ✅ [DESIGN] P1. (opus) Define the classification function over the availability manifest: given (AG, venue,
      data_type, instrument, required_window), return RUNNABLE / INSUFFICIENT-HISTORY / HONEST-EMPTY using
      `capture_status` + the 4-state completeness math. Distinguish HONEST-EMPTY
      (`empty_confirmed`/`expected_unattempted`) from INSUFFICIENT-HISTORY (window only partially captured) — this is
      the crux and must not collapse. — Gate: a reviewed spec + a `classify_shard_coverage(...)` signature; honest-empty
      vs insufficient-history decision table. — unified-api-contracts@746d546a. Spec doc:
      `/codex/02-data/shard-coverage-classification.md`. UAC module:
      `unified_api_contracts/canonical/crosscutting/shard_coverage_classification.py` (typed enum `ShardCoverageClass`,
      `RequiredWindow`, `WindowCaptureCounts`, `ShardCoverageReport`, pure-logic core `classify_from_capture_counts` +
      `bucket_capture_status_cell`, signature-frozen `classify_shard_coverage` wrapper with body `NotImplementedError`
      until the IMPLEMENT P1 todo lands the e2e-testing harness). Decision-table priority: F+U+M>0 →
      INSUFFICIENT_HISTORY (any hole → fail loudly, the half-window safety property); else C>0 → RUNNABLE; else →
      HONEST_EMPTY (typed within-/out-of-window absence on every day). The honest-empty vs insufficient-history
      non-collapse is tested adversarially in
      `tests/unit/test_shard_coverage_classification.py::test_honest_empty_does_not_collapse_into_insufficient`.
- [x] ✅ [DESIGN] P1. (opus) Build the **required-window registry** per (AG, data_type): seasonal-continuous for sports
      markets, daily for max-daily-aggregation types, lookback-N otherwise. Source the seasonal boundaries from the
      sports league registry, not magic numbers. — Gate: registry covers all 5 AGs' MVP data_types; sports entries
      reference real season windows. — unified-api-contracts@a2c21da8.
      `unified_api_contracts/canonical/crosscutting/required_window_registry.py`: typed `RequiredWindowSpec` (kind +
      lookback_calendar_days + driver_feature_family / lookback_periods / coarsest_timeframe provenance),
      `MVP_REQUIRED_WINDOW_REGISTRY` covering all 5 AGs' MVP data_types from the audit-derived table (cefi: trades /
      book_snapshot_5 / derivative_ticker / options_chain / futures_chain; defi: dex_pool_swaps / dex_pool_state /
      lending_indices / lst_rates / oracle_prices / perp_funding; tradfi: ohlcv_1m / ohlcv_24h; sports: FIXTURES / XG /
      ODDS / MATCH_STATS — all `seasonal_continuous` via `get_season_boundary(league_id,     season_year)`, NO magic
      numbers; prediction: trades / book_snapshot_5 / market_lifecycle / canonical_question_group),
      `resolve_required_window(...)` wraps the registry with the call-site context, and `UnknownRequiredWindowError`
      ENFORCES the "no combo silently skipped" IMPLEMENT P1 gate. Unit-tested in
      `tests/unit/test_required_window_registry.py` (per-AG coverage, sports-uses-real-season-boundary,
      lookback-provenance-required, unknown-combo-raises).
- [x] ✅ [IMPLEMENT] P1. Implement the harness: iterate the Plan-3 MVP universe, classify every shard, and emit a
      **coverage matrix** artifact (AG × venue × data_type × instrument → state + window covered). Select one
      representative RUNNABLE shard per (AG × venue × data_type) for the smoke set. — Gate: running the harness produces
      the matrix + a smoke-set manifest; no combo silently skipped (un-classified = hard error). —
      unified-api-contracts@202f633e + e2e-testing@7ee5eb1. UAC: `classify_shard_coverage` wrapper implemented (replaces
      the IMPLEMENT-P1 `NotImplementedError`; walks `manifest_cells`, buckets per-day via `bucket_capture_status_cell`,
      detects missing-row days, delegates to `classify_from_capture_counts`; 8 positive integration tests in
      `tests/unit/test_shard_coverage_classification.py::TestClassifyShardCoverageWrapper` — including the adversarial
      honest-empty-does-not-collapse property). e2e-testing: `scripts/build_smoke/coverage_harness.py` (pure library —
      `ShardAtom`, `ManifestReader` + `UniverseProvider` protocols, `build_coverage_matrix`, `select_smoke_set`,
      `MdpsUniverseProvider`, JSONL artifact writers; un-classified `(asset_group, data_type)` →
      `UnknownRequiredWindowError`; missing-AG provider → `MissingUniverseProviderError`) +
      `scripts/build_smoke/run_coverage_harness.py` (CLI loading a JSON fixture bundle → coverage_matrix.jsonl +
      smoke_set.jsonl + summary.json) + `tests/fixtures/coverage_harness/mvp_demo.json` (10-atom 5-AG demo) +
      `tests/unit/test_coverage_harness.py` (15 unit tests across gate properties). End-to-end fixture run produces 3
      RUNNABLE representatives + 7 uncovered combos on the demo set — runnable proof of the IMPLEMENT P1 gate.
- [x] ✅ [IMPLEMENT] P1. Wire a smoke-runner that, for each smoke-set shard, runs MDPS→features over the required window
      and asserts: RUNNABLE → succeeds with right-edge + no-look-ahead (calls Plan 4's guard); INSUFFICIENT-HISTORY →
      **refuses to run** (explicit fail, not a partial pass); HONEST-EMPTY → path tolerates absence without crashing or
      writing silent placeholders. — Gate: the runner exits non-zero on a planted INSUFFICIENT-HISTORY shard and green
      on a real RUNNABLE shard for each AG. — e2e-testing@132e6ac. `scripts/build_smoke/smoke_runner.py` (pure library:
      `SmokeOutcome` 9-state enum, `MdpsFeaturesRunner` + `StaticNoLookaheadGuard` protocols, `MdpsFeaturesRunOutput`,
      `SmokeRunResult`, `SmokeReport.exit_code` projection — 0 only on SUCCESS / HONEST_EMPTY_TOLERATED, 1 on any shard
      failure, 2 on static-guard rejection; `FixtureRunner` deterministic in-memory adapter for tests + the [VERIFY] P1
      live-adapter seam) + `scripts/build_smoke/run_smoke_harness.py` CLI (loads the run_coverage_harness fixture
      bundle + optional `smoke_runner` block with per-atom output overrides). Tests `tests/unit/test_smoke_runner.py`
      (17 passing): per-shard trichotomy enforcement (INSUFFICIENT refused without invocation; HONEST_EMPTY tolerated
      only at 0 rows + no placeholder; RUNNABLE demands `right_edge_max_t_close <= window.end_of_day_utc()`, non-zero
      rows, UTC-aware, no placeholder), aggregate exit-code projection, **5-AG RUNNABLE matrix exits 0** (one RUNNABLE
      atom per cefi/defi/tradfi/sports/prediction seeded from `MVP_REQUIRED_WINDOW_REGISTRY` + `get_season_boundary` for
      sports), guard short-circuit (exit_code=2), CLI gate. Planted fixture
      `tests/fixtures/coverage_harness/smoke_planted_insufficient.json` → CLI exits 1 with
      `REFUSED_INSUFFICIENT_HISTORY` counts.
- [x] ✅ [VERIFY] P1. Run the harness against live manifests for all 5 AGs; publish the coverage matrix (which combos
      are RUNNABLE today vs gaps). Big gaps → file issue docs per findings-triage, do not silently descope. — Gate:
      matrix published in this plan's Progress Log; any RED combo has an issue doc or is a known HONEST-EMPTY. —
      e2e-testing@cf6b7e1 + unified-trading-pm issue `plans/active/issues/verify_p1_prereq_dag_2026_06_29.md`. **Scoped
      per BLK-d378494f Option B** (operator decision): the live harness invocation targets the sports EPL 2025 slice —
      the only AG with no prereq blocker; the other 4 AGs are gated on
      `phantom_captures_{cefi,defi,prediction}_2026_06_28` + Plan 5 (tradfi MDPS passthrough) per the issue doc's prereq
      DAG. Live run (today=2025-12-01, GCP `central-element-323112`, sports availability manifest) — see Progress Log
      below for the published matrix; surfaces a real `seasonal_continuous` during-season semantic finding (full-season
      required-window vs. live-classifier intent — 3 options enumerated for operator decision in the issue doc).
- [x] ✅ [AGENT] P1. e2e-testing (+ any UAC helper) QG green; quickmerge `--agent --files`. — Gate: QG green; CI
      `quality-gates-v2` green. — 3 quickmerge `--agent --files` ships at e2e-testing@132e6ac (smoke-runner), @4746467
      (live-reader scaffold), @cf6b7e1 (sports EPL 2025 live verifier); local `quality-gates.sh` green on each commit
      (sentinel-verified via the v2 canonical flow); `quality-gates-v2` last-green on LDR. 40 unit tests total across
      `tests/unit/test_coverage_harness.py` (15) + `tests/unit/test_smoke_runner.py` (17) +
      `tests/unit/test_live_manifest_reader.py` (8).

## Representative smoke matrix (audit-derived 2026-06-28)

**Min-window driver (correction):** the minimum continuous window is
`max over feature families of (lookback_periods × coarsest_timeframe)` for what consumes that shard — NOT the base
granularity. A 200-period feature at 24h needs ~200 trading days even on a 15s base. The required-window registry
computes this from the real feature config, not a guess.

Per-AG representative shard + min-window + today's blocker (full per-AG matrices in the Progress Log):

| AG             | Representative shard(s)                                                                                                               | Min continuous window (driver)                                                                             | Today's coverage verdict / blocker                                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **CeFi**       | BINANCE-FUTURES BTC perp — trades + book_snapshot_5 + derivative_ticker; DERIBIT BTC options_chain/futures_chain (bundle)             | ~200 trading days if any 24h-TF feature uses a 200-period lookback; days for 1m-only families              | RUNNABLE on Binance; **372 HYPERLIQUID phantoms** to reconcile; HL liquidations + DEX book = honest-absent                                |
| **DeFi**       | UNISWAP_V3-ETH dex_pool_swaps (tick) + dex_pool_state; AAVE_V3 lending_indices; LIDO lst_rates; oracle_prices; DRIFT-SOL perp_funding | snapshots → short (1–2d); dex_pool_swaps → intraday; coarse-TF feature lookback otherwise                  | **~219k phantom rows** (swaps_ohlcv batch-writer failure) gate RUNNABLE; UNISWAP_V4/vault = non-MVP, skip                                 |
| **TradFi**     | CME ES + NQ + VX(XCBF) futures (ohlcv_1m); a commodity (GC/CL); equity/ETF basis leg (SPY/AAPL)                                       | ~290 calendar days for a 200-period 24h feature (1m base)                                                  | **BLOCKED-until-Plan-5** (no MDPS passthrough layer; dependency-checker `instrument_id=''` bug); 15s/options/VIX-cash/ICE = honest-absent |
| **Sports**     | EPL × {api_football FIXTURES, understat XG, odds_api ODDS(tick), footystats}; EREDIVISIE (understat HONEST-EMPTY)                     | **season-continuous — golden window `2025-09-01 .. 2025-11-30` (91d)** satisfies all rolling/CLV lookbacks | RUNNABLE in golden window; structural gaps: understat=big-5-only (89 absent), A_LEAGUE×footystats, GREEK×transfermarkt                    |
| **Prediction** | A crypto market live on BOTH Polymarket+Kalshi (arb-overlap), + politics + sports; trades + book_snapshot_5 + CQG/market_lifecycle    | **one full market lifecycle** (created→resolved→settled): ~1.5h hourly, ~24h daily, long for elections     | **~19.5k phantoms** (52% of captured) flip + MTDS writer fix prerequisite; single-venue + financial = honest-absent                       |

**Cross-AG blocker the harness must encode:** four AGs carry phantom-capture pollution (the just-pulled
`phantom_captures_*_2026_06_28.md` issues) and TradFi is MDPS-gap-blocked — so "RUNNABLE today" ≠ "RUNNABLE after
reconciliation." The classifier reads the post-reconciliation manifest, and the smoke set names the
reconciliation/Plan-5 prerequisite per shard rather than silently passing on a phantom `captured`.

## Progress Log

### 2026-06-29 — [VERIFY] P1 live sports matrix (slot-4)

Live coverage matrix run via `scripts/build_smoke/run_live_verify_sports.py` at e2e-testing@cf6b7e1, today=2025-12-01,
GCP `central-element-323112`, EPL 2025-26 sports slice:

| Venue        | data_type   | classification       | missing_rows | holes |
| ------------ | ----------- | -------------------- | ------------ | ----- |
| api_football | FIXTURES    | INSUFFICIENT_HISTORY | 304          | 5     |
| footystats   | MATCH_STATS | INSUFFICIENT_HISTORY | 304          | 5     |
| odds_api     | ODDS        | INSUFFICIENT_HISTORY | 304          | 5     |
| understat    | XG          | INSUFFICIENT_HISTORY | 304          | 5     |

All 4 EPL-2025 sports shards classify INSUFFICIENT*HISTORY today — NOT because of a manifest gap, but because
`resolve_required_window(sports, *, league_id="EPL", season_year=2025)`returns the \_full* ~304-day season window (Aug
2025 → May 2026); days between today (Dec 2025) and season-end (May 2026) read as missing-rows since the season is ~3
months in. **Finding: no`seasonal_continuous` shard can classify RUNNABLE during its own season\*\* — a semantic gap
between the plan's "golden 91-day window" framing and the live classifier's full-season window resolution.

Cross-AG findings + the 4-AG prereq DAG (cefi/defi/prediction phantom-reconciliation + tradfi Plan 5) filed in
`plans/active/issues/verify_p1_prereq_dag_2026_06_29.md` with 3 classifier-semantic options + 5 follow-up todos for the
operator to sequence.

### 2026-06-29 — [VERIFY] P1 scaffolding shipped (slot-4)

Live UTL-backed `ManifestReader` scaffold landed at **e2e-testing@4746467**:

- `scripts/build_smoke/live_manifest_reader.py` — `UTLManifestReader` wraps
  `unified_trading_library.read_availability_index` + projects rows to the `ShardManifestCell` Protocol the harness
  consumes. Single-walk discipline: one fetch per AG bucket, cached in process (review-blocking otherwise).
- `tests/unit/test_live_manifest_reader.py` (8 tests) — per-instrument projection, bundled-shard projection on
  underlying / chain / league_id, single-walk cache invariant (fetch fires exactly once per bucket), pandas Timestamp →
  date normalisation, empty error_reason → None.

[VERIFY] P1 checkbox **remains unflipped** — the scope of the live invocation is currently /blocked on `BLK-d378494f`:
the plan's own coverage table marks TradFi as BLOCKED-until-Plan-5 and 4 of 5 AGs as phantom-polluted by sibling
`phantom_captures_*_2026_06_28.md` plans. The orchestrator answer determines whether the live run targets all 5 AGs, the
sports-golden-window slice only, or is deferred entirely to a post-reconciliation successor task. The scaffold is useful
for any of the three options.

## Notes

- "Fail on partial" is the hard rule here: a half-window must NOT produce a green smoke test. The classifier's
  insufficient-history branch is the safety property — test it adversarially.
- Honest-empty handling is already partly covered by the data-pipeline-correctness contingencies
  (`data_pipeline_hardening_self_monitoring_2026_06_22`); this harness _consumes_ those signals, it doesn't re-implement
  honest-absence detection.
- Output feeds Plan 7: the benchmark picks its full-month shard from the RUNNABLE set (Binance first).
- **2026-07-14 (verify-rerun-2 finding 22)**: frontmatter `status: active` (line 5) is stale relative to the body — all
  6 Todos are `[x] ✅` complete (including the final ship/QG-gate todo), and no completion/archival banner exists
  anywhere in the doc. Per the plan-archival gate, the `status` field is NOT flipped here (annotate-only — a
  status/archival flip requires the 5-step archival ritual, not a doc-reconciliation edit); left for the plan
  owner/operator to run archival.
