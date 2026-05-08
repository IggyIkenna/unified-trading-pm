---
title:
  "MDPS liquidity-baseline 3rd state (illiquidity vs data-bug) + live tick-staleness watchdog — both reuse same
  per-(venue, instrument, period) baseline"
created: 2026-05-08
author: ikenna
source:
  - market-data-processing-service/market_data_processing_service/output_writer_service.py:194 (1440 NaN OHLC writeback
    — deprecated path)
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md:2351-2430 (Wave 3.M zero-volume-bar adapter audit
    pending)
  - plans/active/alerting_service_live_rules_2026_05_07.md:52-203 (alert taxonomy — DEFI_FEATURE_STALE present but
    no TICK_STALENESS)
  - CLAUDE.md "Four-category empty-output decision" (categories A/B/C/D — D added 2026-05-07 evening)
  - CLAUDE.md "Live = batch" workspace principle
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# MDPS liquidity-baseline 3rd state + live tick-staleness watchdog

> **Severity**: P1 — live-only readiness item (Group F+G in master plan); doesn't strictly block May 23 paper-trade
> smoke but blocks honest-coverage promise + production live observability. **Blast radius**:
> market-data-processing-service (write-gate) + UAC (per-(venue, instrument, period) baseline SSOT) + alerting-service
> (live tick-staleness consumer) + features-\* + execution-service (downstream freshness gates). **Suggested owner**:
> writegate Phase 3.D.5 Wave 3.M+1 OR fold into `alerting_service_live_rules_2026_05_07.md` Phase 1+ (cross-cuts
> both).

## What I found

Two related architectural gaps, both reusing the same baseline data structure.

### Gap 1 — MDPS can't distinguish illiquidity from data-quality-bug

Current Phase 3.D.5 design (CLAUDE.md "Four-category empty-output decision") routes ALL
`(alive instrument, market open, zero ticks in period)` to category D — write zero-volume bar with prior-LTP
carry-forward + `record_captured`. This assumes the zero-tick reason is illiquidity (which is the right default for
trading correctness — every strike must be visible for cross-instrument analyses like volatility smiles).

**But not all zero-tick periods are illiquidity.** A period that gets zero ticks when the prior 30-day rolling baseline
says ~1000 ticks is data-quality-suspected, not illiquidity. Currently:

- No `liquidity_baseline` / `expected_tick_rate` / `rolling_tick_count` / `tick_rate_baseline` in MDPS code.
- No `DATA_QUALITY_SUSPECTED_GAP` typed reason in `EMPTY_CONFIRMED_REASONS` closed set.
- Search across MDPS, UAC, all active plans returned ZERO matches for these terms.
- Wave 3.M ([writegate plan:2351-2430](../writegate_honest_coverage_endtoend_2026_05_06.md#L2351-L2430)) defines
  category D zero-volume-bar mechanism but doesn't define a 3rd state for "alive + zero ticks +
  baseline-says-shouldnt-be-zero."

[output_writer_service.py:194](../../../market-data-processing-service/market_data_processing_service/output_writer_service.py#L194)
still writes 1440 NaN OHLC rows when upstream MTDS has zero rows — the 2026-05-05 deprecated path that hasn't been
migrated yet.

### Gap 2 — Live tick-staleness watchdog doesn't exist

The mirror-image of MDPS's batch validation: in live mode, watch for "instrument X hasn't produced a tick in 2× expected
interval → STALE alert."

- [alerting_service_live_rules_2026_05_07.md:52-203](../alerting_service_live_rules_2026_05_07.md#L52-L203)
  covers `DEFI_FEATURE_STALE` (feature compute delays) and circuit-breaker codes, but NO per-(venue, instrument)
  tick-arrival freshness alert.
- [unified-trading-library tests/unit/test_freshness_monitor.py](../../../unified-trading-library/tests/unit/test_freshness_monitor.py)
  has DATA_STALE event but tied to feature compute delays, not tick arrival.
- [data_status_extended.py:29-423](../../../deployment-service/deployment_service/cli/utils/data_status_extended.py#L29-L423)
  has staleness thresholds at BATCH layer (manifest age checks for backfill VM monitoring) — not live-tick-grain.
- No `TICK_STALENESS` / `TICK_FRESHNESS` / `LAST_TICK_AT` event types or alert codes.

This violates the workspace `Live = batch` principle: if batch has manifest empty_confirmed + attempted_failed +
expected_unattempted (4-state taxonomy), live needs the equivalent — a real-time monitor that says "instrument X should
have produced a tick within Y seconds based on baseline; hasn't → STALE."

## Why it matters

- **Silent bad data flows downstream**: a venue WS feed disconnects but our infra reconnects without surfacing the gap →
  MDPS sees zero ticks for the gap period → category D zero-volume-bars → features compute on zero-volume bars →
  strategies trade on stale prior-LTP → execution bleeds.
- **Volatility smile / correlation features wrong**: cross-instrument analyses that depend on simultaneous price
  discovery silently include "tradeable but illiquid" zero-volume bars when actually the instrument was just
  disconnected.
- **No live recourse**: in batch we can re-run the backfill if data quality is suspected. In live, we need real-time
  staleness signal to (a) trigger reconnect, (b) flag downstream consumers, (c) alert operator before strategy starts
  trading on stale data.
- **Group F+G live-only readiness**: per master plan, this IS one of the "live observability" + "circuit breaker +
  auto-recovery" prerequisites; without it, the May 23 cutover ships without a key safety net.

## Recommended decision

Build one architectural primitive — per-(venue, instrument, period) `expected_tick_rate_baseline` — that solves both
gaps:

### Phase 1 — UAC SSOT for liquidity baseline

New module: `unified_api_contracts.canonical.crosscutting.liquidity_baseline`

```python
@dataclass(frozen=True)
class TickRateBaseline:
    venue: VenueName
    instrument_id: str
    period: PeriodLength  # 15s / 1m / 5m / 15m / 1h / 1d
    rolling_window_days: int  # default 30
    p10_tick_count: float
    p50_tick_count: float
    p90_tick_count: float
    last_refreshed_at: datetime
    sample_count: int  # how many periods aggregated (sanity gate: ≥ 100)

def get_baseline(venue, instrument_id, period) -> TickRateBaseline | None:
    """Returns rolling 30-day baseline; None if instrument too new (sample_count < 100)."""
```

Storage: `gs://{pid}-baselines/liquidity_baseline_v1/{venue}/{period}/{date}/baselines.parquet` — daily snapshots,
refreshed via a daily VM that walks MDPS captured parquets and computes the per-instrument distributions. Read-side:
cached in memory at MDPS write-gate + at live-staleness-watchdog startup.

### Phase 2 — MDPS write-gate consults baseline

Extend `EMPTY_CONFIRMED_REASONS` closed set with `DATA_QUALITY_SUSPECTED_GAP`. At MDPS bar-write boundary:

```python
baseline = get_baseline(venue, instrument_id, period)
observed_ticks = len(mtds_ticks_in_period)

if observed_ticks > 0:
    write_normal_bar()
    record_captured(...)
elif baseline is None:
    # too new instrument — fall through to category D zero-volume-bar (current behaviour)
    write_zero_volume_bar()
    record_captured(...)
elif observed_ticks == 0 and baseline.p10_tick_count > LIQUIDITY_BASELINE_GAP_THRESHOLD:
    # alive + market-open + zero-ticks + baseline says shouldn't be zero → suspected data bug
    record_failed(reason=DATA_QUALITY_SUSPECTED_GAP, baseline_p10=baseline.p10_tick_count, observed=0)
    # DO NOT write a zero-volume bar — explicit gap is more honest than masking
else:
    # alive + market-open + zero-ticks + baseline says zero is plausible → illiquidity
    write_zero_volume_bar()
    record_captured(...)
```

`LIQUIDITY_BASELINE_GAP_THRESHOLD` defaults to 10 (if even the p10 of the rolling-30-day baseline expects ≥10 ticks per
period and we got zero, that's suspicious). Tunable per asset_group.

### Phase 3 — Live tick-staleness watchdog

New service or sub-module of alerting-service:

```python
class LiveTickStalenessWatchdog:
    def __init__(self):
        self.baselines = load_all_baselines()
        self.last_tick_at: dict[(venue, instrument_id), datetime] = {}

    async def on_tick(self, venue, instrument_id, ts):
        self.last_tick_at[(venue, instrument_id)] = ts

    async def check_staleness_loop(self):
        while True:
            now = utcnow()
            for (venue, instrument_id), last_ts in self.last_tick_at.items():
                baseline = self.baselines.get((venue, instrument_id, "1m"))  # use 1m period as default check grain
                if baseline is None:
                    continue
                expected_interval_seconds = 60.0 / max(baseline.p50_tick_count, 1)
                threshold_seconds = expected_interval_seconds * STALENESS_MULTIPLIER  # default 5x
                if (now - last_ts).total_seconds() > threshold_seconds:
                    emit_event(
                        TICK_STALENESS,
                        severity=WARNING,
                        details={
                            "venue": venue,
                            "instrument_id": instrument_id,
                            "last_tick_at": last_ts,
                            "expected_interval_s": expected_interval_seconds,
                            "observed_gap_s": (now - last_ts).total_seconds(),
                            "baseline_p50": baseline.p50_tick_count,
                        },
                    )
            await asyncio.sleep(STALENESS_CHECK_INTERVAL)
```

Downstream consumers (execution-service, strategy-service, position-balance-monitor) subscribe to `TICK_STALENESS`
events + adjust trading behaviour (block new orders for stale instruments; flag features as low-confidence).

### Phase 4 — Backfill for historical baseline (one-time)

Walk all captured MDPS parquets for last 60 days, compute baselines per (venue, instrument, period), upload to
`liquidity_baseline_v1/` bucket. Daily refresh VM thereafter.

## Acceptance criteria

- [ ] `TickRateBaseline` dataclass + storage layout shipped in UAC.
- [ ] Daily baseline-refresh VM running, populating `liquidity_baseline_v1/` bucket.
- [ ] MDPS write-gate consults baseline; `DATA_QUALITY_SUSPECTED_GAP` typed reason added to `EMPTY_CONFIRMED_REASONS`
      closed set.
- [ ] `TICK_STALENESS` event type added to UAC alerting taxonomy.
- [ ] LiveTickStalenessWatchdog service (or alerting-service sub-module) consuming live ticks + emitting staleness
      events.
- [ ] execution-service / strategy-service handle TICK_STALENESS by blocking new orders for the affected (venue,
      instrument).
- [ ] Smoke test: in batch backfill, deliberately drop ticks for an EPL fixture-day where baseline says ~1k ticks/min —
      verify `record_failed(DATA_QUALITY_SUSPECTED_GAP)` instead of zero-volume-bar.
- [ ] Smoke test: in live, simulate WS disconnect for 5 minutes on a high-liquidity instrument — verify TICK_STALENESS
      fires within `STALENESS_MULTIPLIER × p50_interval` after disconnect.

## Open questions

- Should the baseline be per-period-of-day (e.g. EPL fixtures cluster Sat 12:30-17:00 UTC) rather than a single rolling
  30-day average? More accurate but more storage. Default: single rolling, revisit if false-positive rate is high.
- For DeFi (block-rate-based, not tick-rate-based): the baseline shape is `expected_blocks_per_period`. Same
  architecture, different unit.
- For sports (event-driven goals/cards/lineups): does this even apply, or is sports orthogonal? Probably orthogonal —
  sports doesn't have continuous tick streams; staleness signal is "FIXTURES forward-poll didn't run for date X" which
  is a different layer.
- What's the right `STALENESS_MULTIPLIER`? 5x is a guess — empirical tuning post-launch.
- Coordination with `mtds_live_data_recovery_self_detect_2026_05_08.md`: when MTDS detects WS disconnect, it ALSO fires
  events. Do TICK_STALENESS (downstream-detected) and CONNECTIVITY_GAP (upstream-detected) duplicate each other?
  Probably TICK_STALENESS is the cross-cutting safety net; CONNECTIVITY_GAP is the upstream root-cause signal. Both
  useful, fire independently.
