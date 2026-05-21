---title: Wave 3.X Track D — zero-activity-bar implementation (post-cutover)
type: sub-plan
status: active
created: 2026-05-19
deadline: post-2026-05-23
parent_plan: wave3x_residual_ssots_2026_05_08.md
locked_by: live-defi-rollout
locked_since: 2026-05-19
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
estimate_calibration_note: |
  New implementation (brand-new class, 1.0× multiplier). Scope: UTL primitive +
  catalog threading + per-adapter wire-in across MTDS/MDPS/features-service.
  Audit docs from wave3x Track D are the spec.
parent_epic: mtds_mdps_master
---

**MIGRATED FROM:** `wave3x_residual_ssots_2026_05_08.md` § Track D items 1-4. Audit work completed 2026-05-11 (slot 3).
Implementation blocked pre-2026-05-23; this plan owns the post-cutover execution.

# Wave 3.X Track D — zero-activity-bar implementation

## Context

Track D audit completed 2026-05-11. Findings: `plans/archive/issues/wave3x_track_d_findings_2026_05_11.md`

Carry-forward semantics per data_type documented in: `codex/02-data/honest-absence-downstream-handling.md` §
"Zero-activity-bar shape"

Operator decision: case-D implementation (zero-activity-bars) requires a new UTL primitive + `instrument_catalog`
threaded at adapter construction. Post-cutover scope.

## Scope

**P0 — New UTL primitive**

- [ ] [UTL] P0. Implement `zero_activity_bars(last_snapshot, data_type, interval_close)` primitive in UTL
      `availability_stamping.py`. Per carry-forward table: `ohlcv_*` → O=H=L=C=prior_LTP, volume=0, trade_count=0;
      `trades` → empty parquet 0 rows; `book_snapshot_5` → carry-forward bid/ask 5 levels; `derivative_ticker` →
      carry-forward open_interest/mark_price/index_price. Unit tests. **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2:
      plan is explicitly post-2026-05-23 scope per operator decision ("Post-cutover scope" in plan context). UTL
      primitive is gate for all other items. 8 AI-day brand-new estimate.

**P0 — MTDS adapter wire-in**

- [ ] [MTDS] P0. Thread `instrument_catalog` into adapter construction in MTDS. Wire `zero_activity_bars()` at the
      adapter emission boundary for case-D (source-returns-zero AND catalog reports instrument alive). Per-adapter:
      `ohlcv_*`, `trades`, `book_snapshot_5`, `derivative_ticker`. Sports historical in instruments-service (NOT MTDS —
      per D3 audit finding). Per-adapter smoke tests. **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: gated on UTL
      primitive above.

**P0 — MDPS calculator wire-in**

- [ ] [MDPS] P0. Wire `zero_activity_bars()` at the candle-aggregation boundary in MDPS calculators. Per D4 audit: fix
      dead canonical-writer path + 1440-NaN TradFi passthrough + banned `_handle_empty_tick_data` /
      `_create_closed_market_candle` × 2 / `_maybe_write_vix_gap_placeholder`. Per-calculator smoke tests.
      **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: gated on UTL primitive above.

**P1 — features-service calculators**

- [ ] [features] P1. Wire `zero_activity_bars()` in features-service calculators for sports/prediction
      case-D-with-bookmaker-odds-carry-forward. Fix `np.zeros(n)` continuous-feature bug, commodity phantom manifest-row
      bug, sports `fillna(magic)` masking-absence, presence-only manifest (`ManifestWriter.add` → `record_captured`),
      onchain/delta_one honest-absence rows. Per D5/D6 audit findings. **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2:
      gated on UTL primitive above.

**P0 — Tests**

- [ ] [TEST] P0. Per-adapter smoke tests: synthetic instrument-alive-but-source-zero day → zero-activity-bar with
      correct shape per data_type; instrument-not-yet-listed day → `record_empty(EXPECTED_INSTRUMENT_NOT_LISTED)`;
      pre-genesis-chain day for DeFi → `record_empty(EXPECTED_PRE_GENESIS_CHAIN)`. **[DEFERRED-POST-CUTOVER]**
      2026-05-19 slot 2: gated on UTL primitive + adapter wire-ins above.

## Success criteria

- UTL `zero_activity_bars()` primitive with 100% unit test coverage.
- All MTDS/MDPS/features adapters emit zero-activity-bars for case-D instead of `record_empty()`.
- Per-adapter smoke tests pass with synthetic instrument-alive-but-source-zero inputs.
- QG green across UTL + MTDS + MDPS + features-service.

## Dependencies

- UTL primitive must land before adapter wire-ins (MTDS/MDPS/features).
- `instrument_catalog` threading: check `unified_api_contracts` for existing catalog interface before implementing.

## Audit findings SSOT

- `plans/archive/issues/wave3x_track_d_findings_2026_05_11.md` — full per-audit findings (D1-D6).
- `codex/02-data/honest-absence-downstream-handling.md` § "Zero-activity-bar shape" — carry-forward table.

## Temporary states + their canonical follow-up plans

| Temporary state                    | Successor                         |
| ---------------------------------- | --------------------------------- |
| DEFERRED items from wave3x Track D | This plan owns the implementation |
