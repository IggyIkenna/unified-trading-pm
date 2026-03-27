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
