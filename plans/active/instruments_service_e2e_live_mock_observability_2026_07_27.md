---
doc_type: plan
title: instruments-service E2E — live mode, mock scenarios, observability (Phases 5-7)
summary:
  Re-scoped from the never-completed Phases 5-7 of the archived 2026-03 instruments-service E2E audit
  (plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md) — live-mode 15-min clock alignment,
  mock-mode failure scenarios, and observability/logging checks, none of which were ever run.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [e2e-testing, instruments-service, live-mode, mock-mode, observability]
related: []
created: 2026-07-27
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1
last_updated: 2026-07-27
supersedes: []
superseded_by:
locked_by:
locked_since:
depends_on:
source: [plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md]
assigned_role: backend_engineer
drift_direction: none
---

# instruments-service E2E — live mode, mock scenarios, observability

## Context

The original instruments-service E2E audit (2026-03-21, archived 2026-07-27) completed Phases 1-4 plus a real 2026-03-23
DEFI-category audit that found 6 real bugs, but never ran Phases 5-7. Re-verify against current instruments-service
before assuming any of the below is still accurate — 4+ months have passed.

## Todos

- [x] ✅ [SCRIPT] P1. **Phase 5 — Live mode clock alignment. DONE 2026-07-30 (slot-15) — premise corrected + real bug
      found + fixed.** The literal command (`--operation live --mode batch --interval 15`) does not exist: `--operation`
      only accepts `instruments` (`--mode` is the batch/live selector), and `--interval` is not a flag anywhere in
      instruments-service or unified-trading-library (confirmed via `--help` + full-repo grep). Read the actual
      `--mode live` code path (`unified-trading-library/unified_trading_library/service_framework/_adapter.py:219-237`):
      it is a **one-shot, externally-triggered** run that defaults `start_date=end_date=today` and force-refreshes —
      there is no internal 15-minute wall-clock-aligned boundary-wait loop for this service (that primitive,
      `UTCAlignedScheduler`, lives in UTL's `streaming/utc_aligned_scheduler.py` and is consumed only by
      market-tick-data-service's `websocket_runner.py`). The CLI docstring's claim of "UTL ScheduledIO (wall-clock
      aligned)" is stale/aspirational — `class ScheduledIO` does not exist anywhere in the codebase. No Cloud
      Scheduler/terraform cron wires instruments-service `--mode live` to a 15-min external cadence either (only daily
      06:00/02:00 UTC crons exist) — confirmed via terraform grep. **5.1/5.2 (boundary-wait/`:00/:15/:30/:45`
      alignment): N/A, architecture doesn't implement it** — not a regression, this was never built for this service.

      **5.3/5.4 — actually run + verified** via `main_service_cli()` with `--operation instruments --mode live
          --asset-group cefi` under `CLOUD_MOCK_MODE=true`: confirmed `ServiceRuntime` STARTED log line, per-venue fetch
          logging (URDI[...] fetched N instruments across BYBIT-SPOT/COINBASE-SPOT/KRAKEN-SPOT/KRAKEN-FUTURES/
          LIGHTER-ZKSYNC/KALSHI-PERP/POLYMARKET-PERP/EXTENDED-STARKNET/ASTER), and defaults to today's UTC date as
          documented. **Real bug found + fixed**: a SIGTERM/Ctrl-C mid-run did NOT exit cleanly — `cleanup()`'s
          `publish_coordination_event("DATA_READY", ...)` call (instruments_handler.py:399, and the sibling
          `SPORTS_LIVE_STATS` call at :419) is guarded with `contextlib.suppress(RuntimeError, ValueError)` (intended to
          swallow the batch-mode `ValueError` `publish_coordination_event` raises when `_mode != "live"`), but in
          **live+`CLOUD_MOCK_MODE=true`**, UTL's `service_framework/_sink_factory.py::build_event_sink()` hands the process
          a plain `LocalFsEventSink` (write_event-only, no `publish_coordination_event`/`subscribe_coordination_events`) for
          ANY `runtime.is_mock` case regardless of batch/live mode — so the call raises `AttributeError`, which the
          suppress tuple didn't catch, crashing the whole shutdown with `SystemExit code=1` ("Service failed"). **Fixed**:
          broadened both suppress tuples to `(RuntimeError, ValueError, AttributeError)` — instruments-service@`<pending>`.
          Re-verified: same repro now exits `SystemExit code=0` on SIGTERM mid-run, no traceback. **Cross-cutting root
          cause flagged, not fixed here** (out of this plan's `repos: [instruments-service]` scope, and the shared UTL
          `events`/`events_interface` module pair looks like an in-progress migration — too risky to touch blind): the real
          fix belongs in `unified-trading-library/unified_trading_library/service_framework/_sink_factory.py` (or
          `event_sink.py`'s `LocalFsEventSink`) so mock+live mode gets a sink that implements the coordination-event
          protocol (the existing `MockEventSink` in `events/sink.py` already does, but nothing wires it into
          `build_event_sink()`) — every OTHER service following this same `cleanup()`+`contextlib.suppress` pattern is
          exposed to the identical crash. Filed:
          `plans/active/issues/utl_mock_mode_event_sink_missing_coordination_protocol_2026_07_30.md`.

          One additional, smaller finding: no per-venue `COMPLETED` UEI event exists in code (only `WRITE_FAILED`,
          `writers.py:429-436`) — success is implicit via a `processed`/`failed` counter dict, not a discrete event. 5.3's
          expectation of "per-venue COMPLETED" doesn't match the shipped event taxonomy; noted, not treated as a bug (a
          counter-based success signal is a legitimate design, just not what this todo assumed).

- [ ] [SCRIPT] P2. **Phase 6 — Mock-mode failure scenarios.** Run and verify: (6.1) `--scenario default` normal mock
      generation; (6.2) `--scenario stress` (10x cardinality) — memory + writes succeed; (6.3) `--scenario missing_data`
      (instruments disappear mid-day) — downstream handles empty gracefully; (6.4) injected fake symbol
      (`FAKE-EXCHANGE:SPOT:NOSYMBOL`) — clean skip/error, no crash; (6.5) missing entire DEFI category —
      market-tick-data-service gets nothing for DEFI and skips cleanly; (6.6) corrupt expiry date
      (`expiry="not-a-date"`) — parser warns, doesn't crash; (6.7) `CLOUD_MOCK_MODE=true` → `config_source=local`, no
      GCS reads.
- [ ] [SCRIPT] P2. **Phase 7 — Observability.** Verify: (7.1) ServiceRuntime log line has all dimensions; (7.2) UEI
      STARTED/COMPLETED/per-venue events fire; (7.3) shard-level isolation (one venue failure doesn't crash others);
      (7.4) dry-run warning logged ("DRY RUN" + "UCI dry-run mode ACTIVE"); (7.5) `ADAPTER_FETCH_FAILED` events classify
      failed venues correctly; (7.6) "Memory watchdog started" logged.
- [ ] [VALIDATE] P3. **Re-verify the 6 bugs from the 2026-03-23 DEFI E2E audit are still real** (Balancer 400, Aster
      lowercase-category bug, Hyperliquid 0-instruments, missing data-catalogue entries, a Pydantic warning,
      CFE-not-in-UAC) before re-filing any of them — 4 months have passed and some may already be fixed incidentally.

## Progress Log

- 2026-07-27: Plan created, re-scoping the never-run Phases 5-7 out of the archived 2026-03 instruments-service E2E
  audit doc per operator decision (pre-June-1 stale-plans audit).

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — all 4 todos are bounded verification RUNS with
  explicit per-item done-when checklists (Phase 5 clock-alignment 5.1-5.4, Phase 6 mock scenarios 6.1-6.7, Phase 7
  observability 7.1-7.6, the 6-bug re-verify) — determinable by a worker alone.
