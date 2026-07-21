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
status: open
nature: issue
asset_group: [cefi, tradfi, defi]
stage: [data]
repos: [deployment-api, market-data-processing-service, unified-api-contracts]
scope: [engineer]
tags: [data-correctness, mdps, manifest, data_type, regression, classifier]
related: [candle_feature_canonical_path_divergence_2026_07_20.md, ../mtds_data_status_page_parity_2026_07_21.md]
created: "2026-07-21"
last_updated: "2026-07-21"
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
resolved_by:
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

- [ ] [BACKEND] P1. Reconcile `PROCESSED_REQUIRES_RAW`'s data_type keys against `752eaff`'s SOURCE-axis manifest
      convention (option (a) or (b) above) so `_classify_data_type_for_venue` correctly detects "blocked_on_raw" for
      post-cutover MDPS rows again.
- [ ] [DATA] P2. Reconcile the three divergent timeframe-token vocabularies
      (`path_combinatorics.py:PROCESSING_TIMEFRAMES`, `canonical_writer_shaping.py:_normalise_timeframe`'s real output,
      `processed_data_dependencies.py:_TIMEFRAMES`) to one SSOT — verified against what the writer actually emits, not
      copied from any existing constant.
- [ ] [REVIEW] P2. Confirm whether this same SOURCE-axis switch affects any other deployment-api consumer keyed on the
      old aggregated data_type convention (this issue only traced `_classify_data_type_for_venue`; a broader grep for
      `PROCESSED_REQUIRES_RAW`/aggregated-token consumers was not exhaustive).
