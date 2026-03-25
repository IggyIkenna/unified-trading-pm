---
name: alerting-batch-replay
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  Wire batch mode for alerting-service so it replays historical events from GCS at batch speed
  through the same routing rules as live mode. Same alert decisions, same routing pipeline —
  only the event source and delivery behaviour differ.

  ## Problem
  alerting-service accepts `--mode batch` but both batch and live modes read from Pub/Sub
  (AlertSubscriber). Batch mode should read from GCS event logs (`events/{service}/{date}/events.jsonl`)
  and replay them through route_event() at batch speed, with delivery suppressed (audit-only)
  or redirected to a batch-audit channel.

  This violates the system's core batch/live alignment philosophy:
  - `get_messaging_protocol("batch") → "gcs"` (topology_reader.py:121)
  - `get_messaging_protocol("live") → "pubsub"`
  - The alerting service ignores this and always uses Pub/Sub

  ## Solution
  Phase 1: Create BatchEventReader in alerting-service that reads JSONL event logs from GCS
  Phase 2: Wire batch mode in main.py to use BatchEventReader instead of AlertSubscriber
  Phase 3: Add delivery suppression — batch routes events through rules but writes audit
           records to GCS instead of firing PagerDuty/Telegram
  Phase 4: Add `--date` CLI arg for batch replay date range

  ## Scope: 2 repos
  - alerting-service — BatchEventReader, main.py batch wiring, delivery suppression
  - unified-trading-codex — document batch/live alerting convention

type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C4
  deployment: D1
  business: B4

repo_gates:
  - repo: alerting-service
    code: C0
    notes: "BatchEventReader + main.py batch wiring + delivery suppression"
  - repo: unified-trading-codex
    code: C0
    notes: "Document batch alerting convention"

isProject: false

todos:
  # ============================================================================
  # PHASE 1 — BatchEventReader  [PARALLEL]
  # ============================================================================
  - id: p1a-batch-event-reader
    content: |
      - [ ] [AGENT] P0. Create BatchEventReader class in alerting-service.
        File: alerting_service/subscribers/batch_event_reader.py

        Purpose: Read historical events from GCS event logs and yield them in
        chronological order, exactly as AlertSubscriber yields live events.

        Event log locations (written by GcsEventSink in UEI event_sink.py):
          gs://{service-events-bucket}/events/{service_name}/{date}/events.jsonl

        Each service writes its own events bucket. The alerting batch reader needs
        to aggregate events from ALL services for a given date range:
          - execution-service-events
          - risk-and-exposure-service-events
          - strategy-service-events
          - position-balance-monitor-service-events
          - instruments-service-events
          - market-tick-data-service-events
          etc.

        Implementation:
        ```python
        class BatchEventReader:
            def __init__(self, project_id: str, date_range: list[str]):
                self._project_id = project_id
                self._dates = date_range  # ["2026-03-20", "2026-03-21", ...]

            async def stream(self) -> AsyncIterator[tuple[str, dict[str, object]]]:
                \"\"\"Yield (event_name, details) pairs from GCS event logs.

                Reads all services' event logs for each date in the range,
                sorts by timestamp, and yields chronologically.
                Same interface as AlertSubscriber.stream().
                \"\"\"
                for date in self._dates:
                    events = self._read_all_services_for_date(date)
                    events.sort(key=lambda e: e.get("timestamp", ""))
                    for event in events:
                        event_name = event.get("event", "UNKNOWN_EVENT")
                        yield event_name, event
        ```

        Key design decisions:
        - Same yield signature as AlertSubscriber.stream(): tuple[str, dict[str, object]]
        - Reads from GCS via UCI get_storage_client (not direct SDK)
        - Sorts by timestamp within each date partition for deterministic replay
        - Shard-level failure isolation: if one service's log is missing, skip with warning
        - No rate limiting: replay at batch speed (as fast as GCS reads allow)

        The list of service event buckets should be derived from dependencies.yaml
        or hardcoded as a constant (all services emit events via GcsEventSink).
    status: pending

  - id: p1b-event-source-registry
    content: |
      - [ ] [AGENT] P1. Define EVENT_SOURCE_BUCKETS constant.
        File: alerting_service/subscribers/batch_event_reader.py

        All services write events to: events/{service_name}/{date}/events.jsonl
        in their respective event buckets.

        The bucket name convention is: {service-name}-events-{project_id}
        OR events may be in the shared alerting bucket or a central events bucket.

        Need to check: where does each service's GcsEventSink write?
        The bucket comes from PubSubEventSink init in main.py of each service.

        Alternative approach: Read from a CENTRAL events topic/bucket if one exists,
        rather than scanning per-service buckets. Check if there's a consolidated
        event log that all services write to.

        Decision: Use the alerting service's own event log GCS paths where
        route_event() already persists delivery records. For batch replay of
        SOURCE events (before they reach alerting), scan per-service event buckets.
    status: pending

  # ============================================================================
  # PHASE 1 gate: ruff + basedpyright pass on new file
  # ============================================================================

  # ============================================================================
  # PHASE 2 — Wire Batch Mode in main.py  [SEQUENTIAL after P1]
  # ============================================================================
  - id: p2a-main-batch-wiring
    content: |
      - [ ] [AGENT] P0. Wire batch mode in main.py to use BatchEventReader.
        File: alerting_service/main.py

        Current: Both batch and live modes create AlertSubscriber (Pub/Sub).
        Target:
          if args.mode == "live":
              # Current path: AlertSubscriber pulls from Pub/Sub
              subscriber = AlertSubscriber(project_id=config.gcp_project_id)
              await _run_subscriber_until_shutdown(subscriber, _shutdown_handler)
          elif args.mode == "batch":
              # New path: BatchEventReader reads from GCS event logs
              reader = BatchEventReader(
                  project_id=config.gcp_project_id,
                  date_range=get_date_range(args.date, args.end_date),
              )
              await _run_batch_replay(reader, _shutdown_handler)

        The _run_batch_replay function:
        - Iterates through reader.stream()
        - Calls the same _dispatch_event(event_name, enriched) as AlertSubscriber
        - Uses batch delivery mode (see Phase 3)
        - Logs summary at end: total events replayed, alerts that would have fired,
          alerts suppressed by cooldown, alerts deduplicated

        Must follow topology convention:
          messaging = get_messaging_protocol(mode=args.mode, service="alerting-service")
          # batch → "gcs", live → "pubsub"
    status: pending
    blocked_by: p1a-batch-event-reader

  - id: p2b-cli-date-args
    content: |
      - [ ] [AGENT] P1. Add --date and --end-date CLI args for batch mode.
        File: alerting_service/main.py

        Add to _build_parser():
          parser.add_argument("--date", help="Batch replay start date (YYYY-MM-DD)")
          parser.add_argument("--end-date", help="Batch replay end date (YYYY-MM-DD), default=--date")

        Validation:
          - --date required when --mode batch
          - --end-date defaults to --date (single day replay)
          - Both must be valid YYYY-MM-DD strings
          - --date/--end-date ignored in live mode

        Usage:
          python -m alerting_service --mode batch --date 2026-03-20
          python -m alerting_service --mode batch --date 2026-03-15 --end-date 2026-03-20
    status: pending

  # ============================================================================
  # PHASE 2 gate: cd alerting-service && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 3 — Delivery Suppression  [PARALLEL with P2]
  # ============================================================================
  - id: p3a-batch-delivery-mode
    content: |
      - [ ] [AGENT] P0. Add batch delivery suppression to route_event().
        File: alerting_service/notifiers/router.py

        In batch mode, route_event() must:
        1. Run the SAME routing rules (pattern matching, severity filter)
        2. Run the SAME deduplication and cooldown logic
        3. NOT actually deliver to PagerDuty/Telegram/Slack
        4. Instead: write an audit record to GCS with what WOULD have been delivered

        Implementation approach:
        - Add a module-level flag: _BATCH_MODE = False
        - Set it from main.py before replay starts
        - In route_event(), after rule matching but before delivery:
            if _BATCH_MODE:
                _persist_batch_audit_record(event_name, matched_rule, channels, details)
                return  # skip actual delivery
            # ... existing delivery code

        Audit record schema (written to alerting-service GCS bucket):
          alerting/batch-audit/date={date}/audit.jsonl
          {
            "event_name": "CIRCUIT_BREAKER_OPEN",
            "matched_rule": "CIRCUIT_BREAKER_*",
            "would_deliver_to": ["pagerduty", "telegram"],
            "severity": "critical",
            "deduplicated": false,
            "cooldown_active": false,
            "original_timestamp": "2026-03-20T14:23:01Z",
            "replay_timestamp": "2026-03-25T09:15:00Z",
            "source_service": "execution-service",
            "details": { ... }
          }

        This gives full visibility into "what alerts would have fired" for any
        historical date range, without actually paging anyone.
    status: pending

  - id: p3b-batch-summary-report
    content: |
      - [ ] [AGENT] P1. Add batch replay summary report.
        File: alerting_service/subscribers/batch_event_reader.py (or main.py)

        After batch replay completes, log a summary:
          ═══════════════════════════════════════════
          Alerting Batch Replay Summary
          ═══════════════════════════════════════════
          Date range:        2026-03-15 → 2026-03-20
          Total events:      12,847
          Events matched:    423 (routing rule hit)
          Would-deliver:     312 (after dedup + cooldown)
            PagerDuty:       28
            Telegram:        284
            Slack:           0
          Deduplicated:      87
          Cooldown blocked:  24
          Errors:            0
          ═══════════════════════════════════════════

        This lets you validate alert rules against historical data and tune
        thresholds/cooldowns before deploying rule changes to live.
    status: pending

  # ============================================================================
  # PHASE 3 gate: cd alerting-service && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 4 — Tests + Codex  [PARALLEL after P3]
  # ============================================================================
  - id: p4a-unit-tests
    content: |
      - [ ] [AGENT] P0. Add unit tests for BatchEventReader + batch delivery mode.
        File: alerting_service/tests/unit/test_batch_replay.py

        Tests:
        1. BatchEventReader.stream() yields events sorted by timestamp
        2. BatchEventReader handles missing service logs gracefully
        3. Batch delivery mode writes audit records instead of delivering
        4. Batch summary report counts are correct
        5. Deduplication and cooldown behave identically in batch vs live
        6. Empty date range produces zero events (not an error)

        Use CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true for all tests.
    status: pending
    blocked_by: p3a-batch-delivery-mode

  - id: p4b-codex-doc
    content: |
      - [ ] [AGENT] P2. Document batch/live alerting convention in codex.
        File: unified-trading-codex/04-architecture/alerting-batch-live.md

        Document:
        1. Live mode: Pub/Sub → route_event() → PagerDuty/Telegram/Slack → GCS audit
        2. Batch mode: GCS event logs → route_event() → GCS batch-audit (no delivery)
        3. Same routing rules, same deduplication, same cooldown
        4. Batch replay CLI usage
        5. How to use batch replay to validate alert rule changes
        6. Event log GCS path convention
        7. Batch audit record schema
    status: pending

  # ============================================================================
  # PHASE 4 gate: cd alerting-service && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 5 — QG Sweep  [SEQUENTIAL]
  # ============================================================================
  - id: p5a-qg-sweep
    content: |
      - [ ] [AGENT] P0. Run quality gates on all touched repos.
        cd alerting-service && bash scripts/quality-gates.sh
        cd unified-trading-codex && bash scripts/quality-gates.sh
        All must pass.
    status: pending
    blocked_by: p4a-unit-tests
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

| File                                                           | Purpose              |
| -------------------------------------------------------------- | -------------------- |
| `alerting_service/subscribers/batch_event_reader.py`           | GCS event log reader |
| `tests/unit/test_batch_replay.py`                              | Unit tests           |
| `unified-trading-codex/04-architecture/alerting-batch-live.md` | Convention doc       |

### Files to MODIFY

| File                                   | Change                                                       |
| -------------------------------------- | ------------------------------------------------------------ |
| `alerting_service/main.py`             | Branch on mode: batch→BatchEventReader, live→AlertSubscriber |
| `alerting_service/notifiers/router.py` | Add \_BATCH_MODE flag + audit record writer                  |
