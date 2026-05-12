---
title: "MDPS canonical_writer `available_at` off-by-one timeframe overshoot — fix shipped 2026-05-11"
created: 2026-05-11
author: ikenna-available-at-tab (slot 3)
source:
  - plans/active/available_at_lookahead_bias_completion_2026_05_08.md Phase 0.3 audit
  - market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py:336 (pre-fix)
  - market-data-processing-service/market_data_processing_service/app/calculators/fast_candle_aggregation.py:94 + :134
  - market-data-processing-service/market_data_processing_service/app/calculators/polars_candle_engine.py:242
locked_by: live-defi-rollout
locked_since: 2026-05-11
execution:
  owner: ikenna-available-at-tab (slot 3) — closed by the fix; no further runs
  cadence: one-shot
  verifier:
    "tests/unit/test_canonical_writer_record_helpers.py::test_stamp_candle_available_at_no_extra_timeframe_overshoot
    green on origin/live-defi-rollout"
  last_executed: 2026-05-11
---

> **Status 2026-05-11: ✅ FIXED + SHIPPED.** Two-commit close-out (MDPS code fix + UAC contract amendment + tests +
> regression-guard test). MDPS fix at `market-data-processing-service@f004e12`; UAC contract amendment at
> `unified-api-contracts@8672d49`. Both on `origin/live-defi-rollout`. This issue doc documents the bug for archive +
> maps the surface that was audited.

# MDPS canonical_writer `available_at` off-by-one timeframe overshoot

> **Severity**: P0 (data correctness, every MDPS-emitted candle since 2026-05-10 ohlcv_1h POC; over-conservative
> direction, NOT a leak, so no lookahead regression — but every batch parquet's `available_at` is one full timeframe
> further into the future than the live pipeline would actually deliver).
>
> **Blast radius**: MDPS (every candle write since the canonical_writer Phase 1.2A.1 latency-aware stamping shipped
> 2026-05-10) + downstream features-\* + strategy-service that consume `available_at` for lookahead-bias gates
> (consequences: features built on MDPS bars see them 1 timeframe later than reality; for 1d bars that's a full day late
> vs live-pipeline- arrival).
>
> **Suggested owner**: closed by slot 3 in-flight. Cross-side notification to Ikenna slot 1 (main) + the writegate Phase
> 2.A owner (P0-2 surgery shipped the surrounding code 2026-05-11 but inherited the off-by-one from the original
> 2026-05-10 Phase 1.2A.1 design).

## What I found

`canonical_writer._stamp_candle_available_at` computed:

```python
out["available_at"] = ts_dt + tf_delta + latency_delta
# = (timestamp) + timeframe + per-source emission latency
```

The module's mental model (lines 174-181 pre-fix) was:

> live-pipeline arrival of the bar at `[t_open, t_open + tf)` is the bar CLOSE plus the source-priority emission
> latency.

i.e. it assumed `timestamp = t_open`, computed `t_open + tf + latency = t_close + latency`. Mathematically correct under
that assumption.

But all three MDPS aggregator surfaces emit `timestamp = t_close`, not `t_open`:

| Aggregator | File:line                     | Code                                                          |
| ---------- | ----------------------------- | ------------------------------------------------------------- |
| 24h candle | `fast_candle_aggregation:94`  | `candle_timestamp = data_date + pd.Timedelta(days=1)`         |
| Interval   | `fast_candle_aggregation:134` | `candle_timestamp = boundaries[i + 1]`                        |
| Polars     | `polars_candle_engine:242`    | `timestamp = day_start_us + (interval_idx + 1) * interval_us` |

For `interval_idx = 0` and 1m bars, the first row's `timestamp = day_start + 60s` = `t_close` of the first bar
`[day_start, day_start + 60s)`.

So `canonical_writer` was reading `t_close`, treating it as `t_open`, and producing
`available_at = t_close + tf + latency` instead of the correct `t_close + latency`. The overshoot per candle is exactly
**one full timeframe**: 1 minute for 1m candles, 1 hour for 1h candles, **1 full day** for 1d candles.

## Why it matters

- **NOT a lookahead-bias leak.** Over-conservative is safe from a lookahead-bias standpoint — features see bars LATER
  than reality, never earlier. Strict `available_at <= target_ts - horizon` gates still pass on the over-stamped data.
- **IS a Live=batch consistency violation.** Per the workspace CLAUDE.md rule "Live = batch — same data, same fields,
  same timing semantics", historical batch writes MUST stamp `available_at` with the live-pipeline- arrival time we'd
  actually have in live mode. `t_close + tf + latency` is NOT what the live pipeline emits — live emits at
  `t_close + latency`. Backtest features computed against the over-stamped batch see bars later than the same features
  in live mode would see — silent batch/live divergence.
- **Compounds with 1d bars.** A 1d feature computed at time T = 2026-05-12 00:00:00 + 1h would see the 2026-05-11 daily
  bar (real availability ~50ms past close) ONE FULL DAY LATE under the bug (stamped 2026-05-12 00:00:00 + 1d + 50ms =
  2026-05-13 00:00:00.050). The feature compute would skip yesterday's bar entirely. Same horizon shift for hourly bars
  (1h late) etc.

## Fix

Two-commit close-out shipped 2026-05-11:

1. **`market-data-processing-service@f004e12`** — `canonical_writer.py:336`: drop `+ tf_delta` term. New formula:
   `out["available_at"] = ts_dt + latency_delta`. Module-level Phase 1.2A.1 comment block (lines 174-191) rewritten to
   explicitly document the `timestamp = t_close` aggregator convention with file:line references to all three aggregator
   paths. 4 existing `_stamp_candle_available_at` unit tests adjusted to use t_close inputs + expect
   `timestamp + latency` outputs (not `timestamp + tf + latency`). 1 new regression-guard test
   (`test_stamp_candle_available_at_no_extra_timeframe_overshoot`) asserting delta == latency only against a
   1h-timeframe input.

2. **`unified-api-contracts@8672d49`** — `bar_boundary.py` clause 4 amended from strict `available_at == t_close` to
   `available_at >= t_close` (lower bound — earlier = leak) with hard upper bound `available_at - t_close <= 25h`
   (catches any future stamping bug that adds an extra timeframe; real per-source latencies cap at 24h via
   transfermarkt). 4 new clause-4 tests covering the closed set of cases: (a) below-close raises; (b) equal-to-close
   passes (degenerate no-latency form); (c) every UAC `EMISSION_LATENCY_MS_BY_SOURCE` value passes (databento 10ms →
   transfermarkt 24h); (d) 25h+ past close raises the overshoot guard.

## Why the bug shipped

The original 2026-05-10 Phase 1.2A.1 `_stamp_candle_available_at` was written against the assumption that MDPS
aggregators emit `timestamp = t_open` (a common convention in some OHLCV systems — yfinance, Polygon, Databento bars all
use t_open). The actual MDPS convention is t_close (matches some crypto exchanges + real-time systems). The unit tests
encoded the bug — every test stamped a fixed timestamp and expected `timestamp + tf + latency`. Without a cross-check
against the actual aggregator-emitted convention, the inconsistency went unnoticed for 2026-05-10 → 2026-05-11 (~1 day).

The contract gap surfaced via Phase 0.3 audit (slot 3, `ikenna- available-at-tab`) on 2026-05-11 while reviewing MDPS
bar-boundary alignment for the UAC `assert_bar_boundary_contract` wiring (Phase 0.5). Slot 3 was about to wire the
validator into the canonical writer when the validator's strict clause 4 (`available_at == t_close`) rejected every MDPS
candle, exposing both the UAC contract gap AND the MDPS overshoot in one investigation.

## Recommended decision

Resolved. This issue doc is for the audit trail; no further action. Composes with
`available_at_lookahead_bias_completion_2026_05_08.md` Phase 0.5 (MDPS write-gate wiring) which now uses the corrected
contract

- correct MDPS stamping.
