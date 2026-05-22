---
scope: [engineer, admin]
created: 2026-05-16
last_reviewed: 2026-05-17
plan: plans/active/batch_live_symmetry_2026_05_10.md Tab 1 (P2 post-cutover placeholder)
status: placeholder
---

# TradFi Batch/Live Architecture

> Placeholder for the per-asset-group narrative for `asset_group=tradfi`. Cross-cutting batch=live invariant lives in
> [`batch-live-architecture.md`](batch-live-architecture.md). Full content shipped post-cutover; this placeholder exists
> so `tradfi-batch-live.md` is referenceable from the cross-asset-group meta section in `batch-live-architecture.md`
> without producing broken-link rot.

---

## §1 TradFi venues in scope (placeholder)

In-scope venues for the MVP cutover (May-23): **Databento** (live + historical equity + futures + ETF data), **Yahoo
Finance** (VIX 15m rolling 60d backfill), **Barchart** (VIX 15m preload). Post-cutover expansion targets: **IBKR** (live
IB gateway under `ibkr-gateway-infra/`), **Polygon.io** (corporate-actions + earnings), **FRED** (macro time series).

**Source of truth**: UAC `registry/capability_declarations/_tradfi.py`.

## §2 Matcher pattern (placeholder)

TradFi flows through the L2/L3 matchers documented in [`batch-live-architecture.md`](batch-live-architecture.md) § 5
with one TradFi-specific consideration: the NYSE/NASDAQ/CME calendar gates the live path's expected-cadence checks.
Live-mode emission policy MUST consume `unified_api_contracts.is_non_trading_day()` before flagging staleness (else half
the trading week shows as STALE).

The detailed matcher narrative (per-instrument-type behaviour, options chain shard atomicity, futures roll boundary
handling, VIX preload-vs-rolling priority) ships post-cutover.

## §3 Shard atom + empty rules (placeholder)

Shard atom = `(asset_group=tradfi, source, data_type, instrument_id, date)`. Empty rules + `expected_empty` reasons
documented post-cutover; until then, MTDS adapters route through the canonical
`unified_api_contracts.canonical.crosscutting.honest_coverage.EmptyConfirmedReason` enum (`EXPECTED_HOLIDAY` /
`EXPECTED_PRE_GENESIS_CHAIN` does NOT apply; use `EXPECTED_NON_TRADING_DAY` for weekend/holiday slots).

## §4 Integration with batch-vs-live equality (placeholder)

Same code-path principle as CeFi (see [`cefi-batch-live.md`](cefi-batch-live.md) § 5): there is ONE TradFi pipeline. The
cutover-week MVP runs in live + batch modes against the SAME `tick_data_handler` / `candle_compute` / `feature_*`
calculators. Mode-conditional logic is constrained to the CLI seam per
[`mode-axis-discipline.md`](../06-coding-standards/mode-axis-discipline.md) §4.

## §5 Cross-references

- [`batch-live-architecture.md`](batch-live-architecture.md) — cross-asset-group meta + L2/L3 matcher contract.
- [`cefi-batch-live.md`](cefi-batch-live.md) — sibling per-asset-group narrative.
- [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) — partition-key contract.
- [`../06-coding-standards/mode-axis-discipline.md`](../06-coding-standards/mode-axis-discipline.md) — 4-axis cartesian
  rules + anti-pattern list.
- `unified-trading-pm/plans/active/tradfi_master.md` — cutover-week TradFi delivery plan.

## §6 Successor

Post-cutover follow-up: replace this placeholder with the full per-instrument-type narrative once IBKR live + Polygon.io
backfill ship. Tracked in `tradfi_master.md` "post-cutover follow-ups" section.
