---
scope: [engineer, admin]
---

# Alerting Service: Batch/Live Alignment

## Principle

Same routing rules, same deduplication, same cooldown logic — only the event source and delivery behaviour differ
between batch and live modes.

## Live Mode

```
Pub/Sub subscriptions (risk-breach, circuit-breaker, fill-events, etc.)
  → AlertSubscriber.stream()
  → route_event() — rules + dedup + cooldown
  → PagerDuty / Telegram / Slack (actual delivery)
  → GCS audit log (alerting/history/date={date}/)
```

## Batch Mode

```
GCS event logs (events/{service}/{date}/events.jsonl)
  → BatchEventReader.stream() — sorted by timestamp
  → route_event() — SAME rules + dedup + cooldown
  → GCS batch-audit log (delivery SUPPRESSED)
  → Summary report (what would have fired)
```

## CLI

```bash
# Live (unchanged)
python -m alerting_service --mode live

# Batch — single day
python -m alerting_service --mode batch --date 2026-03-20

# Batch — date range
python -m alerting_service --mode batch --date 2026-03-15 --end-date 2026-03-20
```

## Topology Convention

Follows `get_messaging_protocol()` from UTL topology_reader:

- `batch → "gcs"` — BatchEventReader reads from GCS
- `live → "pubsub"` — AlertSubscriber reads from Pub/Sub

## Batch Audit Records

Written to `gs://alerting-service-{project}/alerting/history/` with `status: "batch_audit"`. Each record shows what
WOULD have been delivered:

```json
{
  "alert_id": "a1b2c3d4e5f6",
  "event_name": "CIRCUIT_BREAKER_OPEN",
  "channels": ["pagerduty", "telegram"],
  "severity": "critical",
  "status": "batch_audit",
  "response_detail": "delivery_suppressed_batch_mode",
  "source": "execution-service",
  "original_timestamp": "2026-03-20T14:23:01Z"
}
```

## Use Cases

1. **Validate rule changes**: Replay a week of events with new rules before deploying live
2. **Incident replay**: See exactly what alerts fired (or didn't) during an incident
3. **Tune cooldown/dedup**: Adjust parameters and replay to see effect on alert volume
4. **New category onboarding**: Verify prediction market alerts route correctly before going live

## Live Instruments Failure Rules

Two complementary signals cover live-instrument failure modes — downstream-detected staleness vs upstream-detected
connectivity gaps. Both fire HIGH-severity (PagerDuty + Telegram); recovery events round out the lifecycle so operators
see the close-loop signal rather than orphan fired-but-never-cleared alerts.

| AlertCode                     | Producer                                   | Severity | Channels             | Payload contract                                                                  |
| ----------------------------- | ------------------------------------------ | -------- | -------------------- | --------------------------------------------------------------------------------- |
| `TICK_STALENESS`              | MDPS write-gate (downstream-detected)      | HIGH     | PagerDuty + Telegram | `venue`, `instrument`, `baseline_seconds`, `actual_seconds`, `last_received_at`   |
| `CONNECTIVITY_GAP_DETECTED`   | MTDS `LiveConnectivityWatchdog` (upstream) | HIGH     | PagerDuty + Telegram | `venue`, `instrument`, `gap_window_start`, `last_received_at`                     |
| `CONNECTIVITY_RECOVERED`      | MTDS reconnect handler                     | INFO     | Telegram             | `venue`, `instrument`, `gap_window_start`, `recovered_at`                         |
| `CONNECTIVITY_GAP_BACKFILLED` | MTDS replay/backfill handler               | INFO     | Telegram             | `venue`, `instrument`, `gap_window_start`, `recovered_at`, `replayed_ticks_count` |

Threshold: `tick_staleness_seconds` (UAC `ALERT_THRESHOLDS`, default 300s = 5min, unit `ThresholdUnit.SECONDS`).
Per-venue overrides via `ALERT_THRESHOLDS["tick_staleness_seconds"].per_archetype_overrides` once Phase 7 quietness
baseline tunes against live MDPS emission.

**30-second coalesce window**: when both `TICK_STALENESS` (MDPS) and `CONNECTIVITY_GAP_DETECTED` (MTDS) fire on the same
`(venue, instrument)` within 30s, the alerting-service router (`alerting_service/notifiers/router.py`
`_check_coalesce_window`) merges them into ONE operator-visible alert. The first event in the window fires normally
(PagerDuty + Telegram + persistence); subsequent events within 30s log `ALERT_COALESCED` and short-circuit return.
Recovery events (`CONNECTIVITY_RECOVERED`, `CONNECTIVITY_GAP_BACKFILLED`) are NOT coalesced — they close the loop on
previously-fired gap alerts and must always reach the operator.

Distinct from existing `KILL_SWITCH_VENUE_DISCONNECT` (venue-wide CRITICAL kill-switch fire — halts adapters) vs
`TICK_STALENESS` / `CONNECTIVITY_GAP_DETECTED` (per-instrument observability — operator visibility, no automatic halt).

SSOTs:

- UAC `unified_api_contracts.alerting.AlertCode` (codes), `LIVE_ALERT_RULES` (routing rules),
  `ALERT_THRESHOLDS["tick_staleness_seconds"]` (threshold).
- Plan: `unified-trading-pm/plans/active/alerting_service_live_rules_2026_05_07.md` § "Tick-staleness + connectivity-gap
  event taxonomy".
- Coalesce impl: `alerting-service/alerting_service/notifiers/router.py` (`_COALESCE_WINDOW_SECONDS`,
  `_COALESCED_EVENT_NAMES`, `_check_coalesce_window`).
- Tests: `alerting-service/tests/unit/notifiers/test_router_coalesce.py` (22 unit tests covering all coalesce shapes).
