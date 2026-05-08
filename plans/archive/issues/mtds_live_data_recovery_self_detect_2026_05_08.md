---
title: "MTDS live data recovery — connectivity-loss self-detect + manifest gap signal + auto-backfill on reconnect"
created: 2026-05-08
author: ikenna
source:
  - market-tick-data-service/market_tick_data_service/ (live WS adapters — venue connections)
  - plans/active/mtds_streaming_and_backpressure_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md (Group F+G live-only readiness — backtest fidelity,
    batch-vs-live reconciliation, circuit breakers + auto-recovery)
  - CLAUDE.md "Live = batch" workspace principle
  - operator directive 2026-05-08: "live data recovery, which market tick data service needs to have embedded in it"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# MTDS live data recovery — connectivity-loss self-detect + auto-backfill

> **Severity**: P1 — Group F+G live-only readiness item; blocks May 23 paper-trade smoke if WS disconnects can silently
> lose ticks without downstream signal. **Blast radius**: market-tick-data-service (every live adapter) + UAC
> (CONNECTIVITY_GAP event taxonomy) + manifest schema (live-mode gap row) + downstream consumers (MDPS / features-\* /
> execution-service). **Suggested owner**: `mtds_streaming_and_backpressure_2026_05_07.md` extended scope OR new
> sibling plan.

## What I found

In live mode, MTDS connects to venue WS feeds and writes ticks to GCS in real-time. Connectivity loss can happen for
many reasons (network partition, venue maintenance, rate-limit cutoff, our pod OOMing) and our infra typically
auto-reconnects. But the **gap window** between disconnect and reconnect is silently lost unless we explicitly detect
and surface it.

Current state (verified by reading representative live adapters):

- WS reconnect logic exists but does NOT typically:
  - Emit a typed `CONNECTIVITY_GAP` event with `{venue, instruments_affected, gap_started_at, gap_ended_at, reason}` for
    downstream consumers.
  - Write a `record_failed(reason=LIVE_CONNECTIVITY_GAP)` manifest row for the affected (venue, day-or-period) shard so
    downstream MDPS / features-\* know the gap happened.
  - Trigger an automatic backfill from a historical source (Tardis / Databento / venue REST) on reconnect to fill the
    gap window with ground-truth ticks.
- Downstream consumers therefore can't distinguish "venue was genuinely quiet during this period" from "we lost the WS
  connection." Same data shape, different semantics.

The `Live = batch` workspace principle says live + batch produce identical schemas + timing semantics. But batch has
4-state capture taxonomy (captured / empty_confirmed / attempted_failed / expected_unattempted) — live mode currently
has no equivalent for "expected ticks but couldn't capture due to our own outage."

Per CLAUDE.md operator directive 2026-05-08:

> "Obviously, live, historically, if you get a parquet from TARDIS, for example, or you don't, then there's no data,
> because TARDIS doesn't have gaps like that. You lose connectivity for a whole day, you might genuinely just miss tick
> data. You might not; you don't know. You need to understand that that happened over that period so that downstream
> consumers know that there might be missing data and you might require backfills and shit like that. That's where live
> data recovery comes into play, which market tick data service needs to have embedded in it."

## Why it matters

- **Silent gap → category-D zero-volume-bar at MDPS → strategies trade on stale prior-LTP**: without an upstream signal,
  MDPS can't distinguish "venue quiet" from "MTDS disconnected." Routes both to category D zero-volume-bar; downstream
  features compute on stale carry-forward; strategies bleed.
- **No batch-vs-live reconciliation possible**: master plan Group F+G item (batch-vs-live reconciliation + P&L
  attribution) requires that live-mode gaps are durably recorded in the manifest so the reconciler can compare batch
  (historical truth) vs live (our capture) and surface discrepancies. Without `LIVE_CONNECTIVITY_GAP` rows, the
  reconciler reads "live captured ticks for period X" with no knowledge that period X had a 30-minute gap.
- **Operational opacity**: operators see "live data flowing" in the deployment-ui but can't tell the system is dropping
  ticks. First signal is downstream P&L drift hours later.
- **Auto-recovery is the right shape**: when the WS reconnects, MTDS already knows the gap window. Triggering a backfill
  from Tardis / Databento / venue-REST during the gap window is the natural fix — we have the source, we have the
  window, we just don't currently wire them.

## Recommended decision

### Phase 1 — Connectivity-loss detection + event emission

Every live adapter wraps the WS connection with a watchdog:

```python
class LiveConnectivityWatchdog:
    def __init__(self, venue, instruments, expected_heartbeat_interval_s):
        self.venue = venue
        self.instruments = instruments
        self.expected_heartbeat_interval_s = expected_heartbeat_interval_s
        self.last_message_at = utcnow()
        self.gap_state: GapState | None = None

    async def on_ws_message(self, msg):
        if self.gap_state is not None:
            # we were in a gap — emit recovery event
            emit_event(
                CONNECTIVITY_RECOVERED,
                details={
                    "venue": self.venue,
                    "instruments": self.instruments,
                    "gap_started_at": self.gap_state.started_at,
                    "gap_ended_at": utcnow(),
                    "gap_duration_s": (utcnow() - self.gap_state.started_at).total_seconds(),
                    "reason": self.gap_state.reason,
                },
            )
            self.gap_state = None
        self.last_message_at = utcnow()

    async def watchdog_loop(self):
        while True:
            now = utcnow()
            if (now - self.last_message_at).total_seconds() > 2 * self.expected_heartbeat_interval_s:
                if self.gap_state is None:
                    self.gap_state = GapState(started_at=self.last_message_at, reason="WS_HEARTBEAT_TIMEOUT")
                    emit_event(
                        CONNECTIVITY_GAP_DETECTED,
                        severity=ERROR,
                        details={
                            "venue": self.venue,
                            "instruments": self.instruments,
                            "gap_started_at": self.last_message_at,
                            "expected_heartbeat_interval_s": self.expected_heartbeat_interval_s,
                            "reason": "WS_HEARTBEAT_TIMEOUT",
                        },
                    )
            await asyncio.sleep(self.expected_heartbeat_interval_s / 2)
```

Two new event types in UAC:

- `CONNECTIVITY_GAP_DETECTED` — fires when watchdog detects gap.
- `CONNECTIVITY_RECOVERED` — fires when WS message arrives after a gap.

### Phase 2 — Manifest gap row at gap-window grain

When `CONNECTIVITY_RECOVERED` fires, MTDS writes a `record_failed` row to the manifest:

```python
manifest.record_failed(
    row_key={
        "asset_group": ...,
        "venue": venue,
        "data_type": ...,
        "instrument_id": ...,
        "date": gap_started_at.date(),  # or split across two dates if gap straddles midnight
    },
    error=LiveConnectivityGapError(
        gap_started_at=...,
        gap_ended_at=...,
        gap_duration_s=...,
        reason="WS_HEARTBEAT_TIMEOUT",
    ),
    error_reason="LIVE_CONNECTIVITY_GAP",
    attempted_at=gap_started_at,
)
```

Add `LIVE_CONNECTIVITY_GAP` to the typed `error_reason` taxonomy (closed set under UAC). The row signals to downstream:
"for this (venue, instrument, day), we have ticks before X and after Y but the window [X, Y] is unknown to us — backfill
or treat as missing."

### Phase 3 — Auto-backfill on reconnect

On `CONNECTIVITY_RECOVERED`, MTDS triggers a backfill task:

```python
async def auto_backfill_gap(venue, instruments, gap_started_at, gap_ended_at):
    # pick best historical source for venue per source_priority SSOT
    source = pick_backfill_source(venue, gap_started_at, gap_ended_at)
    backfilled_ticks = await source.fetch_ticks(venue, instruments, gap_started_at, gap_ended_at)
    if backfilled_ticks:
        write_to_gcs(backfilled_ticks, mark_with_provenance="LIVE_GAP_BACKFILL")
        manifest.record_captured(
            row_key={...},
            backfill_source=source.name,
            original_capture_failed_at=gap_started_at,
        )
        emit_event(CONNECTIVITY_GAP_BACKFILLED, details={...})
    else:
        # source also has no data — leave manifest as record_failed(LIVE_CONNECTIVITY_GAP)
        emit_event(CONNECTIVITY_GAP_BACKFILL_FAILED, details={...})
```

Backfill source selection per workspace `SOURCE_PRIORITY` SSOT — pick the next-priority source for that venue. For CeFi
spot/perp: Tardis usually has 5-min lag historical; for TradFi: Databento; for DeFi: chain-rpc replay.

### Phase 4 — Downstream consumer wiring

- **MDPS**: at write-gate, check manifest for `LIVE_CONNECTIVITY_GAP` rows in the period. If present, route to
  `record_failed(reason=UPSTREAM_LIVE_GAP)` instead of category-D zero-volume-bar. Downstream features see the explicit
  gap.
- **execution-service / strategy-service**: subscribe to `CONNECTIVITY_GAP_DETECTED` + `CONNECTIVITY_RECOVERED` events;
  pause new orders for affected (venue, instruments) until recovery. Reuses circuit-breaker infra.
- **alerting-service**: route gap events to operator alerts (Slack / Telegram per `alerting_service_live_rules` plan).

### Phase 5 — Heartbeat baseline calibration

Per-venue `expected_heartbeat_interval_s` baseline. Some venues send heartbeats every 1s, others every 30s, others
on-tick-only with no idle heartbeat. Empirical audit (run for 1 week, observe distribution) → seed UAC
`VENUE_HEARTBEAT_INTERVAL` SSOT. Default fallback: 60s with warning logged.

## Acceptance criteria

- [ ] `CONNECTIVITY_GAP_DETECTED` / `CONNECTIVITY_RECOVERED` / `CONNECTIVITY_GAP_BACKFILLED` /
      `CONNECTIVITY_GAP_BACKFILL_FAILED` event types in UAC.
- [ ] Every live adapter wraps WS with `LiveConnectivityWatchdog`.
- [ ] `LIVE_CONNECTIVITY_GAP` typed `error_reason` in EMPTY_CONFIRMED_REASONS / EXPECTED_FAILED_REASONS taxonomy.
- [ ] Auto-backfill fires on recovery; populates gap window from source-priority next source.
- [ ] MDPS write-gate consults manifest for gap rows; routes affected periods to `record_failed(UPSTREAM_LIVE_GAP)`.
- [ ] execution-service pauses new orders for affected (venue, instrument) on `CONNECTIVITY_GAP_DETECTED`.
- [ ] Operator alerts wire through alerting-service.
- [ ] Smoke test: deliberately kill WS connection for 5 min on a live adapter; verify event emission, manifest row,
      auto-backfill, downstream pause/resume.
- [ ] Batch-vs-live reconciliation report (Group F+G) handles `LIVE_CONNECTIVITY_GAP` + backfill provenance correctly.

## Open questions

- **Auto-backfill latency budget**: how fast must backfill complete to be useful? If a gap was 5 min and Tardis has 5
  min lag, backfill arrives 10+ min after gap start. For HFT/perp strategies that's already past horizon; for
  slower-cadence strategies (carry, basis) it's fine. Per-strategy decision on whether to consume backfill rows.
- **De-dup on backfill**: if the WS reconnects mid-gap and starts streaming again before backfill completes, we have
  overlap. Need de-dup at write-gate (timestamp + instrument_id primary key).
- **Source not having the gap window**: edge case where backfill source is also missing data. Manifest leaves
  `record_failed(LIVE_CONNECTIVITY_GAP)`; downstream knows it's a hard gap.
- **Coordination with `mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08.md`**: TICK_STALENESS
  (downstream-detected by watching last_tick_at) and CONNECTIVITY_GAP (upstream-detected at MTDS WS layer) overlap. Both
  useful — they fire from different vantage points. Normalize the alert taxonomy so duplicates don't spam operators.
- **Heartbeat interval auto-calibration vs hardcoded SSOT**: empirical seed value vs adaptive in-process calibration.
  Default: hardcoded SSOT, override per-venue if observed deviates significantly.
