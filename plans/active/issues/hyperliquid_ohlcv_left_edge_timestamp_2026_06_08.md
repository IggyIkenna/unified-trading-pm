---
title: instruments-service hyperliquid OHLCV reads LEFT (open) bar edge — violates canonical right-edge t_close
created: 2026-06-08
author: harsh
source:
  - plans/audit/results/tradfi_massive_migration_audit_2026_06_08.md (§ Cross-cutting bar-edge convention audit)
locked_by: live-defi-rollout
---

# hyperliquid OHLCV reads the LEFT/open bar edge (should be right-edge t_close)

> **FOLDED INTO `bar_edge_left_vs_right_systemic_2026_06_08.md`** — the deeper 2026-06-08 sweep found this is one
> instance of a SYSTEMIC class (~12 sites across instruments-service / MTDS / features-service). Track + remediate via
> the systemic issue doc; this file documents the original single instance.

## What I found

Surfaced by the cross-cutting bar-edge audit (operator-requested 2026-06-08) while auditing the Databento→Massive
migration. The workspace canonical OHLCV bar timestamp is the **RIGHT edge `t_close`** (UAC
`canonical/crosscutting/bar_boundary.py` `bar_window_for_close`; interval-aware via UTL
`compute_bar_close_boundary(ts, timeframe)`).

`instruments-service/instruments_service/reference_data/adapters/cefi/hyperliquid.py:255` `_parse_hl_candle` does:

```python
ts_raw = candle.get("t") or candle.get("T") or 0
```

Hyperliquid's `candleSnapshot` returns BOTH `t` = bar-OPEN ms (LEFT edge) and `T` = bar-CLOSE ms (RIGHT edge). This
prefers `t` (open) → the resulting `OHLCVRef.timestamp` is **one full interval early** for every timeframe (1m…1d).

## Why it matters

- Any consumer that treats `OHLCVRef.timestamp` as `t_close` gets a one-interval-early stamp (e.g. a 1m bar labelled
  10:00 actually closes 10:01; a 1d bar off by a day).
- **Scope-limiting fact**: this is in the **instruments-service reference-data** path (instrument listing / universe
  enumeration / `get_ohlcv`), NOT the MTDS→MDPS market-data candle pipeline that feeds features/strategy. The canonical
  candle store is right-edge-enforced by the MDPS write-gate (`assert_bar_boundary_contract`), so this bug does NOT
  pollute it. It is a genuine edge bug in the reference-data surface, not a heartbeat-data corruption.

## Recommended decision

Read `T` (close) instead of `t`, or convert `t + interval_seconds` to t_close (interval-aware via
`compute_bar_close_boundary` / `BAR_TIMEFRAME_SECONDS[tf]` — do not hardcode +60s). Add a unit test asserting
`OHLCVRef.timestamp == bar close`. Owner: DeFi/CeFi epic (`instruments-service`). Small + clear — ≤30 min fix.

Composes with: the cross-cutting bar-edge convention (UAC `bar_boundary.py`) + the MDPS bar-boundary QG checks
(`check_mdps_bar_boundary_compliance.py`). Consider whether the QG bar-boundary check should extend to
instruments-service reference-data adapters so this class of bug is caught at the gate, not only at MDPS.
