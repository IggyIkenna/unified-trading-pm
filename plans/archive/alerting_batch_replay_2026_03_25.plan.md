---
doc_type: plan
title: alerting-batch-replay
summary: "Wire batch mode for alerting-service so it replays historical events from GCS at batch speed\nthrough the same\
  \ routing rules as live mode. Same alert decisions, same routing pipeline —\nonly the event source and delivery behaviour\
  \ differ.\n\n## Problem\nalerting-service accepts `--mode batch` but both batch and live modes read from Pub/Sub\n(AlertSubscriber).\
  \ Batch mode should read from GCS event logs (`events/{service}/{date}/events.jsonl`)\nand replay them through route_event()\
  \ at batch speed, with delivery suppressed (audit-only)\nor redirected to a batch-audit channel.\n\nThis violates the\
  \ system's core batch/live alignment philosophy:\n- `get_messaging_protocol(\"batch\") → \"gcs\"` (topology_reader.py:121)\n\
  - `get_messaging_protocol(\"live\") → \"pubsub\"`\n- The alerting service ignores this and always uses Pub/Sub\n\n## Solution\n\
  Phase 1: Create BatchEventReader in alerting-service that reads JSONL event logs from GCS\nPhase 2: Wire batch mode in\
  \ main.py to use BatchEventReader instead of AlertSubscriber\nPhase 3: Add delivery suppression — batch routes events\
  \ through rules but writes audit\n         records to GCS instead of firing PagerDuty/Telegram\nPhase 4: Add `--date`\
  \ CLI arg for batch replay date range\n\n## Scope: 2 repos\n- alerting-service — BatchEventReader, main.py batch wiring,\
  \ delivery suppression\n- unified-trading-pm/codex — document batch/live alerting convention"
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-25'
locked_by: live-defi-rollout
locked_since: 2026-03-25
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: D1, business: B4}
repo_gates:
- {repo: alerting-service, code: C0, notes: BatchEventReader + main.py batch wiring + delivery suppression}
- {repo: unified-trading-pm/codex, code: C0, notes: Document batch alerting convention}
isProject: false
todos:
- {id: p1a-batch-event-reader, content: "- [x] [AGENT] P0. Create BatchEventReader class in alerting-service.\n  File: alerting_service/subscribers/batch_event_reader.py\n\n  Purpose: Read historical events from GCS event logs and yield them in\n  chronological order, exactly as AlertSubscriber yields live events.\n\n  Event log locations (written by GcsEventSink in UEI event_sink.py):\n    gs://{service-events-bucket}/events/{service_name}/{date}/events.jsonl\n\n  Each service writes its own events bucket. The alerting batch reader needs\n  to aggregate events from ALL services for a given date range:\n    - execution-service-events\n    - risk-and-exposure-service-events\n    - strategy-service-events\n    - position-balance-monitor-service-events\n    - instruments-service-events\n    - market-tick-data-service-events\n    etc.\n\n  Implementation:\n  ```python\n  class BatchEventReader:\n      def __init__(self, project_id: str, date_range: list[str]):\n          self._project_id = project_id\n\
    \          self._dates = date_range  # [\"2026-03-20\", \"2026-03-21\", ...]\n\n      async def stream(self) -> AsyncIterator[tuple[str, dict[str, object]]]:\n          \\\"\\\"\\\"Yield (event_name, details) pairs from GCS event logs.\n\n          Reads all services' event logs for each date in the range,\n          sorts by timestamp, and yields chronologically.\n          Same interface as AlertSubscriber.stream().\n          \\\"\\\"\\\"\n          for date in self._dates:\n              events = self._read_all_services_for_date(date)\n              events.sort(key=lambda e: e.get(\"timestamp\", \"\"))\n              for event in events:\n                  event_name = event.get(\"event\", \"UNKNOWN_EVENT\")\n                  yield event_name, event\n  ```\n\n  Key design decisions:\n  - Same yield signature as AlertSubscriber.stream(): tuple[str, dict[str, object]]\n  - Reads from GCS via UCI get_storage_client (not direct SDK)\n  - Sorts by timestamp within each date partition\
    \ for deterministic replay\n  - Shard-level failure isolation: if one service's log is missing, skip with warning\n  - No rate limiting: replay at batch speed (as fast as GCS reads allow)\n\n  The list of service event buckets should be derived from dependencies.yaml\n  or hardcoded as a constant (all services emit events via GcsEventSink).\n", status: pending}
- {id: p1b-event-source-registry, content: "- [x] [AGENT] P1. Define EVENT_SOURCE_BUCKETS constant.\n  File: alerting_service/subscribers/batch_event_reader.py\n\n  All services write events to: events/{service_name}/{date}/events.jsonl\n  in their respective event buckets.\n\n  The bucket name convention is: {service-name}-events-{project_id}\n  OR events may be in the shared alerting bucket or a central events bucket.\n\n  Need to check: where does each service's GcsEventSink write?\n  The bucket comes from PubSubEventSink init in main.py of each service.\n\n  Alternative approach: Read from a CENTRAL events topic/bucket if one exists,\n  rather than scanning per-service buckets. Check if there's a consolidated\n  event log that all services write to.\n\n  Decision: Use the alerting service's own event log GCS paths where\n  route_event() already persists delivery records. For batch replay of\n  SOURCE events (before they reach alerting), scan per-service event buckets.\n", status: pending}
- {id: p2a-main-batch-wiring, content: "- [x] [AGENT] P0. Wire batch mode in main.py to use BatchEventReader.\n  File: alerting_service/main.py\n\n  Current: Both batch and live modes create AlertSubscriber (Pub/Sub).\n  Target:\n    if args.mode == \"live\":\n        # Current path: AlertSubscriber pulls from Pub/Sub\n        subscriber = AlertSubscriber(project_id=config.gcp_project_id)\n        await _run_subscriber_until_shutdown(subscriber, _shutdown_handler)\n    elif args.mode == \"batch\":\n        # New path: BatchEventReader reads from GCS event logs\n        reader = BatchEventReader(\n            project_id=config.gcp_project_id,\n            date_range=get_date_range(args.date, args.end_date),\n        )\n        await _run_batch_replay(reader, _shutdown_handler)\n\n  The _run_batch_replay function:\n  - Iterates through reader.stream()\n  - Calls the same _dispatch_event(event_name, enriched) as AlertSubscriber\n  - Uses batch delivery mode (see Phase 3)\n  - Logs summary at\
    \ end: total events replayed, alerts that would have fired,\n    alerts suppressed by cooldown, alerts deduplicated\n\n  Must follow topology convention:\n    messaging = get_messaging_protocol(mode=args.mode, service=\"alerting-service\")\n    # batch → \"gcs\", live → \"pubsub\"\n", status: pending, blocked_by: p1a-batch-event-reader}
- {id: p2b-cli-date-args, content: "- [x] [AGENT] P1. Add --date and --end-date CLI args for batch mode.\n  File: alerting_service/main.py\n\n  Add to _build_parser():\n    parser.add_argument(\"--date\", help=\"Batch replay start date (YYYY-MM-DD)\")\n    parser.add_argument(\"--end-date\", help=\"Batch replay end date (YYYY-MM-DD), default=--date\")\n\n  Validation:\n    - --date required when --mode batch\n    - --end-date defaults to --date (single day replay)\n    - Both must be valid YYYY-MM-DD strings\n    - --date/--end-date ignored in live mode\n\n  Usage:\n    python -m alerting_service --mode batch --date 2026-03-20\n    python -m alerting_service --mode batch --date 2026-03-15 --end-date 2026-03-20\n", status: pending}
- {id: p3a-batch-delivery-mode, content: "- [x] [AGENT] P0. Add batch delivery suppression to route_event().\n  File: alerting_service/notifiers/router.py\n\n  In batch mode, route_event() must:\n  1. Run the SAME routing rules (pattern matching, severity filter)\n  2. Run the SAME deduplication and cooldown logic\n  3. NOT actually deliver to PagerDuty/Telegram/Slack\n  4. Instead: write an audit record to GCS with what WOULD have been delivered\n\n  Implementation approach:\n  - Add a module-level flag: _BATCH_MODE = False\n  - Set it from main.py before replay starts\n  - In route_event(), after rule matching but before delivery:\n      if _BATCH_MODE:\n          _persist_batch_audit_record(event_name, matched_rule, channels, details)\n          return  # skip actual delivery\n      # ... existing delivery code\n\n  Audit record schema (written to alerting-service GCS bucket):\n    alerting/batch-audit/date={date}/audit.jsonl\n    {\n      \"event_name\": \"CIRCUIT_BREAKER_OPEN\",\n \
    \     \"matched_rule\": \"CIRCUIT_BREAKER_*\",\n      \"would_deliver_to\": [\"pagerduty\", \"telegram\"],\n      \"severity\": \"critical\",\n      \"deduplicated\": false,\n      \"cooldown_active\": false,\n      \"original_timestamp\": \"2026-03-20T14:23:01Z\",\n      \"replay_timestamp\": \"2026-03-25T09:15:00Z\",\n      \"source_service\": \"execution-service\",\n      \"details\": { ... }\n    }\n\n  This gives full visibility into \"what alerts would have fired\" for any\n  historical date range, without actually paging anyone.\n", status: pending}
- {id: p3b-batch-summary-report, content: "- [x] [AGENT] P1. Add batch replay summary report.\n  File: alerting_service/subscribers/batch_event_reader.py (or main.py)\n\n  After batch replay completes, log a summary:\n    ═══════════════════════════════════════════\n    Alerting Batch Replay Summary\n    ═══════════════════════════════════════════\n    Date range:        2026-03-15 → 2026-03-20\n    Total events:      12,847\n    Events matched:    423 (routing rule hit)\n    Would-deliver:     312 (after dedup + cooldown)\n      PagerDuty:       28\n      Telegram:        284\n      Slack:           0\n    Deduplicated:      87\n    Cooldown blocked:  24\n    Errors:            0\n    ═══════════════════════════════════════════\n\n  This lets you validate alert rules against historical data and tune\n  thresholds/cooldowns before deploying rule changes to live.\n", status: pending}
- {id: p4a-unit-tests, content: "- [x] [AGENT] P0. Add unit tests for BatchEventReader + batch delivery mode.\n  File: alerting_service/tests/unit/test_batch_replay.py\n\n  Tests:\n  1. BatchEventReader.stream() yields events sorted by timestamp\n  2. BatchEventReader handles missing service logs gracefully\n  3. Batch delivery mode writes audit records instead of delivering\n  4. Batch summary report counts are correct\n  5. Deduplication and cooldown behave identically in batch vs live\n  6. Empty date range produces zero events (not an error)\n\n  Use CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true for all tests.\n", status: pending, blocked_by: p3a-batch-delivery-mode}
- {id: p4b-codex-doc, content: "- [x] [AGENT] P2. Document batch/live alerting convention in codex.\n  File: unified-trading-pm/codex/04-architecture/alerting-batch-live.md\n\n  Document:\n  1. Live mode: Pub/Sub → route_event() → PagerDuty/Telegram/Slack → GCS audit\n  2. Batch mode: GCS event logs → route_event() → GCS batch-audit (no delivery)\n  3. Same routing rules, same deduplication, same cooldown\n  4. Batch replay CLI usage\n  5. How to use batch replay to validate alert rule changes\n  6. Event log GCS path convention\n  7. Batch audit record schema\n", status: pending}
- {id: p5a-qg-sweep, content: "- [x] [AGENT] P0. Run quality gates on all touched repos.\n  cd alerting-service && bash scripts/quality-gates.sh\n  cd unified-trading-pm && bash scripts/quality-gates.sh\n  All must pass.\n", status: pending, blocked_by: p4a-unit-tests}
---

# Alerting Batch Replay

## Problem Statement

The alerting service accepts `--mode batch` but ignores the mode — both batch and live read from Pub/Sub via
AlertSubscriber. This violates the system's batch/live alignment philosophy where
`get_messaging_protocol("batch") → "gcs"` and `get_messaging_protocol("live") → "pubsub"`.

Batch replay should let you answer: "Given historical events from March 15-20, what alerts would have fired with the
current routing rules?" This is essential for:

- Validating alert rule changes before deploying to live
- Debugging false positives/negatives from production incidents
- Tuning cooldown and deduplication parameters
- Ensuring new prediction market alerts (Polymarket, Kalshi) route correctly

## Architecture

```
LIVE MODE (current — works)
─────────────────────────────────────────────────────
  Pub/Sub topics (fill-events-*, risk-breach-*, circuit-breaker-*, ...)
    │
    ▼
  AlertSubscriber.stream()          ← pulls from Pub/Sub subscriptions
    │
    ▼
  route_event(event_name, details)  ← routing rules + dedup + cooldown
    │
    ├──► PagerDuty (critical)
    ├──► Telegram  (all matched)
    └──► GCS audit log (alerting/history/date={date}/)


BATCH MODE (new)
─────────────────────────────────────────────────────
  GCS event logs (events/{service}/{date}/events.jsonl)
    │                   ▲
    │                   │ Written by GcsEventSink in every service
    │
    ▼
  BatchEventReader.stream()         ← reads from GCS, sorted by timestamp
    │
    ▼
  route_event(event_name, details)  ← SAME routing rules + dedup + cooldown
    │
    ├──► PagerDuty  ✗ SUPPRESSED
    ├──► Telegram   ✗ SUPPRESSED
    └──► GCS batch-audit log (alerting/batch-audit/date={date}/)
              │
              └── What WOULD have been delivered (channel, severity, rule matched)
```

## Key Design Decisions

1. **Same routing pipeline**: Batch mode calls `route_event()` with identical rules. The only difference is delivery
   suppression — no actual notifications sent.

2. **GCS as batch event source**: Events live at `events/{service}/{date}/events.jsonl` (written by `GcsEventSink` in
   UEI). BatchEventReader reads all services' logs for the requested date range and yields them chronologically.

3. **Audit-only output**: Batch writes to `alerting/batch-audit/date={date}/audit.jsonl` with full metadata about what
   would have been delivered. This is queryable for post-hoc analysis.

4. **Batch speed**: No rate limiting, no sleep between events. Process as fast as GCS reads allow. A week of events
   replays in seconds.

5. **Deterministic replay**: Events sorted by original timestamp within each date partition. Deduplication and cooldown
   state reset at start of each batch run (clean slate).

## Event Log Format (Input — written by all services)

```jsonl
{"event": "CIRCUIT_BREAKER_OPEN", "service": "execution-service", "timestamp": "2026-03-20T14:23:01Z", "metadata": {"venue": "BINANCE-FUTURES", "reason": "error_rate_exceeded"}}
{"event": "FILL_RECEIVED", "service": "execution-service", "timestamp": "2026-03-20T14:23:02Z", "metadata": {"venue": "POLYMARKET", "instrument": "POLYMARKET::UP_DOWN::BTC::5M::1774230900"}}
{"event": "RISK_BREACH", "service": "risk-and-exposure-service", "timestamp": "2026-03-20T14:23:05Z", "metadata": {"breach_type": "position_limit", "venue": "BINANCE-FUTURES"}}
```

## Batch Audit Record Format (Output)

```jsonl
{
  "event_name": "CIRCUIT_BREAKER_OPEN",
  "matched_rule": "CIRCUIT_BREAKER_*",
  "would_deliver_to": [
    "pagerduty",
    "telegram"
  ],
  "severity": "critical",
  "deduplicated": false,
  "cooldown_active": false,
  "original_timestamp": "2026-03-20T14:23:01Z",
  "source_service": "execution-service"
}
```

## CLI Usage

```bash
# Single day replay
python -m alerting_service --mode batch --date 2026-03-20

# Multi-day replay
python -m alerting_service --mode batch --date 2026-03-15 --end-date 2026-03-20

# Live mode (unchanged)
python -m alerting_service --mode live
```

## Dependency DAG

```
P1 (BatchEventReader) ──── P1a: Reader class + GCS read logic
  [PARALLEL]                P1b: Event source bucket registry
                                    │
                           Lint gate (ruff + basedpyright)
                                    │
P2 (main.py wiring) ────── P2a: Batch mode → BatchEventReader
  [SEQUENTIAL after P1]     P2b: --date / --end-date CLI args
                                    │
                           QG gate
                                    │
P3 (Delivery suppression) ─ P3a: Batch delivery mode flag + audit records
  [PARALLEL with P2]         P3b: Batch summary report
                                    │
                           QG gate
                                    │
P4 (Tests + Codex) ──────── P4a: Unit tests for batch replay
  [PARALLEL after P3]        P4b: Codex alerting-batch-live.md
                                    │
P5 (QG sweep) ────────────── P5a: All repos green
```

## Success Criteria

### Phase 1

- BatchEventReader.stream() yields events from GCS JSONL files
- Handles missing logs gracefully (skip with warning)

### Phase 2

- `--mode batch --date 2026-03-20` uses BatchEventReader, not AlertSubscriber
- `--mode live` still uses AlertSubscriber (no regression)
- Topology convention honoured: `get_messaging_protocol("batch") == "gcs"`

### Phase 3

- Batch mode runs same routing rules but writes audit records instead of delivering
- Audit records include: event_name, matched_rule, would_deliver_to, severity, deduplicated flag, cooldown_active flag
- Summary report printed at end of batch run

### Phase 4

- Unit tests pass with CLOUD_MOCK_MODE=true
- `cd alerting-service && bash scripts/quality-gates.sh` green

## Pre-Audit Manifest

### Files to CREATE

| File                                                              | Purpose              |
| ----------------------------------------------------------------- | -------------------- |
| `alerting_service/subscribers/batch_event_reader.py`              | GCS event log reader |
| `tests/unit/test_batch_replay.py`                                 | Unit tests           |
| `unified-trading-pm/codex/04-architecture/alerting-batch-live.md` | Convention doc       |

### Files to MODIFY

| File                                   | Change                                                       |
| -------------------------------------- | ------------------------------------------------------------ |
| `alerting_service/main.py`             | Branch on mode: batch→BatchEventReader, live→AlertSubscriber |
| `alerting_service/notifiers/router.py` | Add \_BATCH_MODE flag + audit record writer                  |
