---
doc_type: issue
title: MDPS's SOURCE-axis manifest switch (752eaff) silently breaks deployment-api's generic processed/raw classifier
summary: >-
  Found as a side-discovery while designing timeframe-aware MTDS-honest-coverage for MDPS (
  mtds_data_status_page_parity_2026_07_21.md), not caused by that work. `market-data-processing-service@752eaff` (today,
  2026-07-21, the operator-ruled fix for candle_feature_canonical_path_divergence_2026_07_20.md's "path≠manifest on
  data_type" finding) changed the manifest's `data_type` column for MDPS rows from the AGGREGATED key
  (`deriv_ohlcv_15m`) to the SOURCE key (`derivative_ticker`), so path and manifest now agree — but deployment-api's
  generic (non-honest-coverage) classifier, `_classify_data_type_for_venue`
  (deployment_api/services/data_status/breakdowns_core.py:680-756), calls `is_processed_data_type`/
  `get_raw_source_data_types` against `PROCESSED_REQUIRES_RAW` (unified-api-contracts
  registry/processed_data_dependencies.py:24-89), which is STILL keyed on the old aggregated tokens (`ohlcv_1h`,
  `deriv_ohlcv_5m`, ...). Post-cutover MDPS rows carry `data_type="trades"`/`"derivative_ticker"` — a raw SOURCE key,
  not a `PROCESSED_REQUIRES_RAW` key — so `is_processed_data_type("derivative_ticker")` now returns False for every
  post-cutover row. The 4-state "blocked_on_raw vs missing" classification this function drives silently degrades to
  always reporting "missing" (never "blocked_on_raw") for any MDPS venue/category that routes through the generic path
  (any category outside MTDS_CATEGORY_META, or any deploy before the honest-coverage parity work lands). This
  under-reports data availability without raising or logging — an honest-absence violation in spirit
  (codex/02-data/honest-absence-downstream-handling.md), even though no row is fabricated.
status: resolved
nature: issue
asset_group: [cefi, tradfi, defi]
stage: [data]
repos: [deployment-api, market-data-processing-service, unified-api-contracts]
scope: [engineer]
tags: [data-correctness, mdps, manifest, data_type, regression, classifier]
related: [candle_feature_canonical_path_divergence_2026_07_20.md, ../mtds_data_status_page_parity_2026_07_21.md]
created: "2026-07-21"
last_updated: "2026-07-22"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  side-discovery by a background research agent (mtds_data_status_page_parity_2026_07_21.md's MDPS-parity design
  workflow) while tracing deployment-api's generic manifest classification path, 2026-07-21; not caused by that work.
resolved_by: >-
  sub-agent, 2026-07-22 — unified-api-contracts@0900a4d98b1e5136ba28d343cbf6df7c58bfbd47 +
  deployment-api@ac2e61e606e41ba87515d54eb531648bafa304a3, both verified landed on origin/live-defi-rollout by SHA.
---

# MDPS data_type axis switch (752eaff) breaks deployment-api's generic processed/raw classifier

## How this was found

Not an audit — a side-discovery while a background research agent traced MTDS/MDPS honest-coverage code for
`mtds_data_status_page_parity_2026_07_21.md`'s MDPS-parity todo. The agent was reading `breakdowns_core.py` to
understand the (separate, non-honest-coverage) generic manifest classification path MDPS falls back to today, and
noticed it depends on a data_type vocabulary that a same-day commit had just moved out from under it.

## Root cause

1. **Before `752eaff`** (today): MDPS manifest rows carried the AGGREGATED `data_type` key (`ohlcv_1m`,
   `deriv_ohlcv_15m`, ...) — matching what `PROCESSED_REQUIRES_RAW`
   (`unified-api-contracts/unified_api_contracts/registry/processed_data_dependencies.py:24-89`) expects as keys.
2. **`752eaff`** (`market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py:513`,
   comment "Manifest data_type AXIS = SOURCE data_type (operator ruling 2026-07-21)") deliberately switched the manifest
   row's `data_type` to the SOURCE key (`trades`, `derivative_ticker`) so that path and manifest agree on this axis —
   the correct fix for `candle_feature_canonical_path_divergence_2026_07_20.md`'s "path≠manifest on data_type" finding.
3. **Consequence, not addressed by 752eaff**: `deployment-api/deployment_api/services/data_status/breakdowns_core.py`
   `_classify_data_type_for_venue` (lines 680-756) calls `is_processed_data_type(dt)`/`get_raw_source_data_types(dt)`
   (lines 742, 746) against `PROCESSED_REQUIRES_RAW`, which is still keyed on the pre-cutover AGGREGATED tokens.
   `is_processed_data_type("derivative_ticker")` → `False` (it's a source key, not an aggregated key) → the function can
   no longer detect that a "missing" MDPS row is actually "blocked on raw data" vs. genuinely absent — it now always
   falls through to reporting plain "missing" for every post-cutover MDPS row this path touches.

## Blast radius

- Only affects the **generic** (non-`is_mtds_honest_coverage_target`) manifest classification path — i.e. any MDPS
  venue/category not yet covered by the honest-coverage parity work in `mtds_data_status_page_parity_2026_07_21.md`, or
  any deploy before that work ships.
- No data is fabricated or lost — this is a classification-quality regression (wrong REASON code / 4-state bucket), not
  a missing-row or phantom-row problem.
- Does not affect MTDS (raw-tick) rows — `PROCESSED_REQUIRES_RAW`'s keys never applied to MTDS's own data_types.

## Recommended fix

Reconcile `PROCESSED_REQUIRES_RAW` (and the closely related `_TIMEFRAMES` vocabulary divergence noted below) against the
post-752eaff SOURCE-keyed convention — either:

- (a) re-key `PROCESSED_REQUIRES_RAW` to the SOURCE data_type keys `752eaff` now writes, or
- (b) teach `is_processed_data_type`/`get_raw_source_data_types` to accept both the legacy aggregated key AND the new
  source key during a transition window (mirroring the dual-read pattern the MDPS-parity design considered for its own
  Open Question 1), with a follow-up to drop the legacy key once no pre-cutover rows remain in the query window.

**Related, lower-severity finding surfaced by the same research pass** (not this issue's blocking finding, folded in
here rather than filing a third doc): three independent, mutually-inconsistent timeframe-token vocabularies exist in the
codebase — `deployment-api/deployment_api/utils/path_combinatorics.py:53` (`PROCESSING_TIMEFRAMES`, uses `"24h"`), the
MDPS writer's actual normalized output (`canonical_writer_shaping.py:194-202`, `_normalise_timeframe`, maps `"24h"` →
`"1d"`), and `unified-api-contracts/unified_api_contracts/registry/processed_data_dependencies.py:55` (`_TIMEFRAMES`,
includes both `"1d"` and `"24h"`, omits `"15s"`). None matches the writer's real output exactly. Should be reconciled to
one SSOT in the same pass as the fix above.

## Todos

- [x] [BACKEND] P1. ✅ Reconciled — option (b) (service-scoped dual-key), NOT option (a). Read the actual current
      callers first: the ONLY production consumer of `PROCESSED_REQUIRES_RAW`/`is_processed_data_type`/
      `get_raw_source_data_types` is `breakdowns_core.py::_classify_data_type_for_venue` (confirmed by grep — see B3
      below). A global re-key to SOURCE tokens (option a) was rejected: post-cutover, the SAME token (`"trades"`,
      `"derivative_ticker"`, ...) is genuinely RAW under MTDS's own manifest scope
      (`service=     "market-tick-data-service"`) but a PROCESSED candle row under MDPS's own scope
      (`service=     "market-data-processing-service"`) — a global re-key would misclassify every genuine raw MTDS row
      as processed. Instead, `is_processed_data_type`/`get_raw_source_data_types` gained an optional `service=` kwarg
      (default `""`, byte-for-byte unchanged for every existing caller): a SOURCE token in `MDPS_DERIVABLE_DATA_TYPES`
      is recognised as processed ONLY when `service == "market-data-processing-service"`. `breakdowns_core.py` threads
      its own `service` param (already available, already plumbed end-to-end) into both calls. Also fixed the
      closely-related B2 finding in the same pass (see below). Shipped:
      `unified-api-contracts@0900a4d98b1e5136ba28d343cbf6df7c58bfbd47` (+ new
      `tests/unit/test_processed_data_dependencies.py`, both `is_processed_data_type=True` restored under MDPS scope AND
      non-regression that the same token stays raw under MTDS scope),
      `deployment-api@ac2e61e606e41ba87515d54eb531648bafa304a3` (threads `service=service` through, +
      `TestMdpsSourceAxisClassification` in `test_data_status_service.py` covering both the MDPS-scoped fix and the
      MTDS-scoped non-regression). Both verified landed on `origin/live-defi-rollout` by SHA
      (`git merge-base --is-ancestor`), both repos' full `quality-gates.sh` green before shipping. Residual, explicitly
      documented in both code comments: this generic path still cannot recover full per-timeframe precision post-cutover
      (candle timeframe now lives outside the `data_type` axis this function keys on, so e.g. all of an MDPS venue's
      1m/5m/15m/1h/4h/1d candles derived from `"trades"` collapse into one `data_type="trades"` bucket here) — that
      precision is the `is_mtds_honest_coverage_target`-gated timeframe-aware path's job (already shipped this session),
      not this fallback's.
- [x] [DATA] P2. ✅ Verified `path_combinatorics.py:PROCESSING_TIMEFRAMES` already imports UAC's
      `MDPS_CANONICAL_TIMEFRAMES` (landed this session, confirmed by reading the file —
      `PROCESSING_TIMEFRAMES: list[str]     = list(MDPS_CANONICAL_TIMEFRAMES)`).
      `processed_data_dependencies.py:_TIMEFRAMES`'s `"1d"`+`"24h"` duplication IS the documented "kept for
      backward-compat resolution of already-written suffixes" case — confirmed correct, left as-is (not a bug, now
      documented as such in an expanded code comment). BUT found a real, distinct gap while checking "is this used
      anywhere that would actually break on a wrong token" per this todo's own instruction: `_TIMEFRAMES` omitted
      `"15s"`, which `MDPS_CANONICAL_TIMEFRAMES` (and the writer's real `mdps_data_type_key()`/`_normalise_timeframe()`
      output — verified by reading the actual writer, not copied from an existing constant) declares as a genuine
      derived candle grain — a legacy pre-cutover `book5_ohlcv_15s`/ `liq_agg_15s`/etc. row was invisible to
      `is_processed_data_type`. Fixed in the same `unified-api-contracts@0900a4d9` commit above (`_TIMEFRAMES` now
      `("15s", "1m", "5m", "15m", "1h", "4h", "1d",     "24h")`), with regression tests (`TestTimeframeVocabulary` in
      the new UAC test file).
- [x] [REVIEW] P2. ✅ Grepped both repos exhaustively for other consumers assuming the old aggregated data_type
      convention: (1) `PROCESSED_REQUIRES_RAW`/`is_processed_data_type`/`get_raw_source_data_types` — exactly one
      production consumer, `breakdowns_core.py` (fixed by B1 above); (2) grepped for literal aggregated-token strings
      (`"ohlcv_1h"`, `"deriv_ohlcv*"`, `"book5_ohlcv*"`, `"liq_agg*"`, `"swaps_ohlcv*"`, `"state_ohlcv*"`,
      `"lending_ohlcv*"`, `"oracle_ohlcv*"`, `"lst_ohlcv*"`, `"odds_ohlcv*"`, `"pred_ohlcv*"`) and for
      `data_type.startswith("ohlcv_"/"deriv_ohlcv_"/...)`-shaped pattern-matching across deployment-api — no other hits
      outside comments/docstrings and `path_combinatorics.py`/`mtds.py` (both already SOURCE-axis-aware, shipped this
      session). (3) Read `mtds.py::mtds_honest_coverage_for_venue`'s docstring in full: the
      `is_mtds_honest_coverage_target`-gated timeframe-aware path ALREADY handles the SOURCE-axis convention correctly
      and documents its own known, deliberate `historical_coverage_gap=True` limitation for pre-cutover rows — not a new
      finding, already shipped earlier this session (2026-07-22 follow-up), out of this issue's scope to re-touch. No
      other broken consumer found; nothing else to fix or file.
