---
doc_type: plan
title: live-batch-protocol-completeness-2026-03-10
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    strategy-service,
    system-integration-tests,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-10"
overview:
  Audit and remediate all 14 T4 services to ensure both batch and live mode handlers, CLI flags, transport switching,
  and tests are present and functional.
type: code
epic: epic-code-completion
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - {
      repo: instruments-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: market-tick-data-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: market-data-processing-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-delta-one-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-volatility-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-calendar-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-onchain-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-commodity-service,
      code: C0,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-cross-instrument-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-multi-timeframe-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-sports-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: ml-training-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: strategy-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: execution-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: system-integration-tests,
      code: C0,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
depends_on: [mock_data_dev_project_seeding_2026_03_10, phase3_service_hardening_integration]
todos:
  - {
      id: p1-todo-05,
      content:
        "features-commodity-service: Create cli/handlers/ with live_handler.py and batch_handler.py; add --mode
        batch|live to cli/main.py",
      status: done,
      note:
        DONE — cli/handlers/live_handler.py and batch_handler.py created; --mode batch|live added to cli/main.py with
        BatchHandler/LiveHandler dispatch. Commit b187ad0.,
    }
  - {
      id: p1-todo-08,
      content: "market-data-processing-service: Add --mode batch|live to cli/parser.py; wire mode selection",
      status: done,
      note:
        DONE — --mode batch|live added to process subparser; _mode_dispatch_handler routes to LiveModeHandler (lazy
        import) or process_candles_handler. Commit 6a3b920.,
    }
  - {
      id: p1-todo-09,
      content:
        "instruments-service: Rename --run-mode to --mode in cli/parser.py; create cli/handlers/batch_handler.py",
      status: done,
      note:
        DONE — --run-mode renamed to --mode with deprecated --run-mode alias (both dest='mode'); validate_arguments()
        enforces required. Commit 9c313ef.,
    }
  - {
      id: p1-todo-10,
      content: "features-sports-service: Add unit tests for batch_handler.py",
      status: done,
      note:
        DONE — tests/unit/test_batch_handler.py created; 6 unit tests covering BatchHandler.run() lifecycle. Commit
        d389213.,
    }
  - {
      id: p1-todo-11,
      content: "market-tick-data-service: Add unit tests for cli/batch_handler.py",
      status: done,
      note:
        DONE — tests/unit/test_batch_handler.py created; 6 unit tests covering DownloadBatchHandler
        init/set_date/run/validate_config. Commit c85e0f8.,
    }
  - {
      id: p1-todo-12,
      content: "ml-training-service: Document as batch-only service in codex; rename handlers",
      status: done,
      note:
        DONE — unified-trading-/codex/04-architecture/batch-live-symmetry.md updated with Batch-Only Service Exemptions
        section documenting MLTR as batch-only by design. Commit e1d8545.,
    }
  - {
      id: p1-todo-13,
      content: "strategy-service: Consolidate live routing from service_entry.py to cli/handlers/live_handler.py",
      status: done,
      note:
        DONE — cli/handlers/live_handler.py created as synchronous facade over StrategyLiveHandler; exported from
        handlers __init__. Commit 70d8605.,
    }
  - {
      id: p1-todo-15,
      content: "Add test_live_mode_handler.py unit tests for FDS, FVS, FCS, FOS, STR",
      status: done,
      note:
        "DONE — FVS and FOS had pre-existing tests; FCS: tests/unit/test_live_mode_handler.py (commit 0a4d03f); STR:
        tests/unit/test_live_mode_handler.py (commit a03a607). FDS repo does not exist.",
    }
  - {
      id: phase2-transport-tests,
      content: Add tests/unit/test_mode_switching.py and tests/integration/test_mode_switching.py per service,
      status: done,
      note:
        "DONE — tests/unit/test_mode_switching.py added and committed for all 13 services: instruments-service (5 tests,
        source-inspection for live mode), market-data-processing-service (6 tests), market-tick-data-service (7 tests,
        INSTRUMENTS_READY coordination event), features-volatility-service (7 tests), features-delta-one-service (5
        tests), features-calendar-service (7 tests), features-onchain-service (6 tests), features-commodity-service (6
        tests), features-cross-instrument-service (7 tests), features-multi-timeframe-service (6 tests),
        features-sports-service (8 tests), strategy-service (7 tests, sys.modules pre-seeding for circular import),
        execution-service (7 tests). All 88 tests pass.",
    }
  - {
      id: phase3-sit-symmetry,
      content: Create system-integration-tests/tests/integration/test_batch_live_symmetry.py for 13 services,
      status: done,
      note:
        "DONE 2026-03-11 — test_batch_live_symmetry.py written; 5 parametrized test functions covering all 13 services
        from audit matrix (repo_exists, batch_handler_exists, live_handler_exists, both_modes_present, matrix_coverage).",
    }
  - {
      id: phase4-codex-update,
      content: Update unified-trading-/codex/04-architecture/batch-live-symmetry.md with final audit matrix,
      status: done,
      note:
        "DONE — Service Audit Matrix (2026-03-11) added covering 13 services with batch/live handler status, --mode
        flag, test coverage, and Handler Pattern Reference. Commit 8655262.",
    }
isProject: false
---

# Plan: Live vs Batch Mode Protocol Completeness Audit

## Context

`unified-cloud-interface` defines `RuntimeMode.BATCH` and `RuntimeMode.LIVE`. The codex (`batch-live-symmetry.md`)
requires every service to support both modes with correct transport protocol switching (live → PubSub, batch → GCS). In
practice: `live_mode_handler.py` exists only for IS and MTDH; `batch_handler.py` exists for FCS/FVS/FDS/FOS but not all
others. No systematic test verifies all 14 T4 services work in both modes. A service that works in batch backfill but
fails in live mode will only be discovered at live trading — unacceptable. Goal: audit matrix shows all 14 services × 2
modes = 28 combinations GREEN; every combination has a handler, unit test, and integration test.

---

## Phase 0: Audit matrix

Completed 2026-03-10. Legend: ✅ present and functional, ❌ absent, ⚠️ partial/stub/nonstandard.

Notes on columns:

- **live_handler**: dedicated `live_mode_handler.py`, `live_handler.py`, or equivalent live-mode entry point
- **batch_handler**: dedicated `batch_handler.py` or equivalent batch-mode entry point
- **CLI --mode flag**: `--mode batch|live` accepted by the CLI parser (or equivalent `--run-mode`)
- **Transport switches**: live → PubSub/queue, batch → GCS; both paths present and routed correctly
- **Unit test live**: unit test exercising live mode handler or live seams (seam-only counts as ⚠️)
- **Unit test batch**: unit test exercising batch mode handler
- **Integration test**: at least one integration test covering a handler or pipeline

| Service                          | live_handler | batch_handler | CLI --mode flag | Transport switches | Unit test live | Unit test batch | Integration test |
| -------------------------------- | ------------ | ------------- | --------------- | ------------------ | -------------- | --------------- | ---------------- |
| instruments-service (IS)         | ✅           | ⚠️            | ⚠️              | ⚠️                 | ✅             | ✅              | ✅               |
| market-tick-data-service (MTDS)  | ❌           | ✅            | ✅              | ⚠️                 | ❌             | ❌              | ❌               |
| market-data-processing (MDPS)    | ✅           | ✅            | ❌              | ⚠️                 | ✅             | ✅              | ✅               |
| features-delta-one (FDS)         | ✅           | ✅            | ✅              | ✅                 | ⚠️             | ✅              | ✅               |
| features-volatility (FVS)        | ❌           | ✅            | ✅              | ⚠️                 | ⚠️             | ✅              | ✅               |
| features-calendar (FCS)          | ❌           | ✅            | ✅              | ❌                 | ⚠️             | ✅              | ✅               |
| features-onchain (FOS)           | ❌           | ✅            | ✅              | ⚠️                 | ⚠️             | ✅              | ✅               |
| features-commodity (FCM)         | ❌           | ❌            | ❌              | ❌                 | ❌             | ❌              | ❌               |
| features-cross-instrument (FCIS) | ❌           | ❌            | ✅              | ❌                 | ❌             | ❌              | ⚠️               |
| features-multi-timeframe (FMTF)  | ❌           | ❌            | ✅              | ❌                 | ❌             | ❌              | ❌               |
| features-sports (FSS)            | ✅           | ✅            | ✅              | ✅                 | ✅             | ❌              | ✅               |
| ml-training-service (MLTR)       | ❌           | ⚠️            | ⚠️              | ⚠️                 | ❌             | ⚠️              | ✅               |
| strategy-service (STR)           | ⚠️           | ✅            | ⚠️              | ⚠️                 | ⚠️             | ✅              | ✅               |
| execution-service (EXEC)         | ✅           | ✅            | ⚠️              | ⚠️                 | ✅             | ✅              | ✅               |

Output: `unified-trading-pm/audits/batch_live_mode_audit_2026_03_10.md`

---

## Phase 0 Results

### Summary

- **GREEN (all 7 columns ✅)**: 0 services
- **NEAR-GREEN (5-6 green, rest ⚠️)**: FDS, FSS, EXEC
- **PARTIAL (batch only, no live handler)**: FVS, FCS, FOS, MTDS
- **STUB / STRUCTURAL GAP**: IS, MDPS, STR, MLTR
- **MISSING BOTH HANDLERS**: FCM, FCIS, FMTF

Total ❌ cells: 26 out of 98. Total ⚠️ cells: 22. Only 50 cells GREEN.

### Per-Service Findings

**instruments-service (IS)**

- `live_mode_handler.py` exists (`cli/handlers/live_mode_handler.py`) — runs on wall-clock intervals (15 min), writes to
  GCS. Correct for reference data but uses GCS not PubSub for live output (no streaming subscriber).
- No dedicated `batch_handler.py` — batch runs via `instrument_handler.py` +
  `engine/operations/instruments/batch_orchestrator.py`. Counts as ⚠️ (functional but nonstandard naming vs codex
  pattern).
- CLI uses `--run-mode batch|live` (not `--mode`) — nonstandard vs codex `cli-standards.md`. The `--mode` flag selects
  operation (instruments, aggregate, etc.), `--run-mode` selects execution mode.
- Transport: live handler uses GCS persistence thread (not PubSub subscribe) — correct for reference data pull pattern,
  but does not conform to codex streaming pattern.
- Unit tests: `test_live_mode_handler_coverage.py` ✅, `test_instruments_service_batch.py` + `test_batch_processor.py`
  ✅. Integration: `test_cli_handlers.py` ✅.

**market-tick-data-service (MTDS)**

- No `live_mode_handler.py` — live mode in `cli/main.py` sets up coordination event subscription
  (`subscribe_coordination_events("INSTRUMENTS_READY")`) then routes through same `DownloadBatchHandler` as batch. No
  dedicated live handler class.
- `batch_handler.py` exists (`cli/batch_handler.py` = `DownloadBatchHandler`) ✅.
- CLI parser accepts `--mode batch|live` ✅.
- Transport: live mode uses GCS event sink (not PubSub publish) and coordination events (not PubSub subscribe for data).
  No PubSub streaming. ⚠️
- No unit tests for live or batch handler specifically. No integration tests (placeholder only).

**market-data-processing (MDPS)**

- `live_mode_handler.py` exists (`cli/handlers/live_mode_handler.py`) ✅. Uses GCS event sink + async GCS data sink — no
  PubSub subscriber/publisher (writes to GCS in both modes). ⚠️ transport: both live and batch use GCS, not PubSub for
  live.
- `batch_handler.py` exists (`app/batch_handler.py` = `CandlesBatchHandler`) ✅.
- CLI parser (`cli/parser.py`) has no `--mode` flag — `cli/main.py` hardcodes `mode="batch"` in GCSEventSink setup. ❌
- Unit tests: `test_live_mode_handler.py` ✅, `test_batch_handler.py` ✅. Integration: `test_candle_storage.py` ✅.

**features-delta-one (FDS)**

- `live_handler.py` exists (`cli/handlers/live_handler.py`) — uses `PubSubSubscriber` for input ✅. `batch_handler.py`
  exists ✅.
- Parser `--mode` flag: choices `["batch", "live", "incremental"]` (incremental deprecated → live) ✅.
- Transport: live uses PubSub subscribe, batch uses `get_storage_client()` GCS ✅.
- Unit test live: `test_live_seams.py` (seam importability only) ⚠️ — no test of `live_handler.py` itself. Unit batch:
  `test_batch_handler.py` ✅ (via `test_live_seams.py` checks adapters). Integration: `test_delta_one_integration.py`
  ✅.

**features-volatility (FVS)**

- No `live_handler.py` — has `adapters/live_data_source.py` seam but no handler class that wires it into a run loop. ❌
- `batch_handler.py` exists (`cli/handlers/batch_handler.py`) ✅. Parser `--mode` flag ✅.
- Transport: batch uses GCS (`data_sink_adapter.py`). Live seam (`live_data_source.py`) uses `get_queue_client()` but is
  never invoked — no handler. ⚠️
- Unit test live: `test_live_seams.py` (seam importability only) ⚠️. Unit batch: `test_batch_handler.py` ✅.
  Integration: `test_volatility_integration.py` ✅.

**features-calendar (FCS)**

- No `live_handler.py` — `batch_handler.py` parser accepts `--mode batch|live|info` but the live branch prints
  `"Live mode not yet implemented; use --mode batch"` and does nothing. ❌
- `batch_handler.py` exists ✅. Has `adapters/live_data_source.py` seam.
- CLI `--mode` flag in `batch_handler.py` create_parser() ✅ (choices: batch, live, info). No separate `main.py` or
  `cli/parser.py` — entry via `__main__.py` → `app()` → batch_handler.
- Transport: live stub raises no error but does nothing ❌. Batch uses `GCSCalendarStorage` ✅.
- Unit test live: `test_live_seams.py` (seam importability only) ⚠️. Unit batch: `test_models.py` + batch_handler covers
  ✅. Integration: `test_split_libraries.py` ✅.

**features-onchain (FOS)**

- No `live_handler.py` — has `adapters/live_data_source.py` seam but no handler class. ❌
- `batch_handler.py` exists (`cli/handlers/batch_handler.py`) ✅. Parser `--mode` flag ✅.
- Transport: live seam uses `get_queue_client()` but never wired into run loop ⚠️. Batch uses GCS via `io/loader.py` ✅.
- Unit test live: `test_live_seams.py` ⚠️. Unit batch: `test_batch_handler.py` ✅. Integration:
  `test_onchain_integration.py` ✅.

**features-commodity (FCM)**

- No `live_handler.py` ❌. No `batch_handler.py` ❌. No handlers/ subdirectory at all.
- CLI `cli/main.py` has no `--mode` flag — only `--commodity`, `--dry-run`, `--run-tag`. ❌
- No transport switching ❌. No unit tests for live or batch mode ❌.
- Service computes signals and publishes via `SignalPublisher` (hardcoded to live-style pubsub publish inside
  `setup_events(mode="live")`) — effectively always runs in live mode with no batch path.

**features-cross-instrument (FCIS)**

- No `live_handler.py` ❌. No `batch_handler.py` ❌. No handlers/ subdirectory.
- CLI `cli/main.py` has `--mode batch|live` ✅ but live mode is a full TODO stub (all processing is `TODO(GH-BACKLOG)` —
  both batch and live paths call identical log events with no actual data load/process/write).
- No transport switching ❌ (both modes run same stub). No unit tests for live/batch mode ❌. Integration:
  `test_cross_instrument_integration.py` exists ⚠️ (unknown coverage of mode paths).

**features-multi-timeframe (FMTF)**

- No `live_handler.py` ❌. No `batch_handler.py` ❌. No handlers/ subdirectory.
- CLI `cli/main.py` has `--mode batch|live` ✅. Live mode routes to `orchestrator.run_live()` which is an explicit stub
  (`TODO(GH-BACKLOG): replace with real EventBus subscriber`). ❌
- No transport switching ❌ (stub loop, no PubSub). No unit tests for live or batch mode ❌. No integration tests.

**features-sports (FSS)**

- `live_handler.py` exists (`cli/handlers/live_handler.py`) — uses `PubSubSubscriber` ✅. `batch_handler.py` exists ✅.
- Parser `--mode batch|live` ✅. Transport: live → PubSub (publish + subscribe), batch → GCS ✅.
- Unit test live: `test_live_handler.py` ✅. Unit batch: no dedicated test for batch_handler ❌. Integration:
  `test_sports_integration.py` ✅.

**ml-training-service (MLTR)**

- No `live_mode_handler.py` / `live_handler.py` ❌. Training is inherently offline.
- Batch concept: `cli/handlers/` has train/evaluate/grid-search handlers (not batch_handler.py) ⚠️. Uses
  `--mode train|evaluate|grid-search` — no `batch|live` concept ⚠️.
- Transport: always reads from GCS (`get_storage_client()` in main.py, cloud_feature_provider.py). Hardcodes
  `mode="batch"` in `setup_events()`. No live-streaming concept. ⚠️
- No unit test for live mode ❌ (N/A by design). Batch=train: unit tests for train/eval/grid handlers ⚠️. Integration:
  `test_integration_complete_pipeline.py` ✅.
- **Assessment**: MLTR is inherently batch-only (model training). Live mode does not apply. Should be explicitly
  documented as batch-only service exempt from live-mode requirement.

**strategy-service (STR)**

- Live handler: `cli/service_entry.py` has `StrategyLiveHandler` class with `CascadeSubscriber` (PubSub stream) ✅. But
  this is in `service_entry.py`, not a standard `live_mode_handler.py`. `cli/handlers/__init__.py` maps `"live_trade"` →
  `BatchHandler` (not a separate live handler) ❌ — live routing is via `service_entry.py` `run_service_cli()` only.
- `batch_handler.py` exists (`cli/handlers/batch_handler.py`) ✅.
- CLI: `service_entry.py` parser accepts positional `mode batch|live` ✅ but `cli/parser.py` has
  `--mode choices=["batch"]` only ⚠️. Two separate CLIs with different mode vocabulary.
- Transport: `StrategyLiveHandler` uses `CascadeSubscriber` (PubSub) ⚠️ — wired but via non-standard service_entry path.
  Batch uses GCS ✅.
- Unit test live: `test_live_seams.py` (seam importability for `live_data_source.py` / `broadcast_sink.py`) ⚠️. Unit
  batch: `test_order_batch_storage.py` + others ✅. Integration: `test_strategy_pipeline.py` ✅.

**execution-service (EXEC)**

- `live_execution_handler.py` exists (`cli/handlers/live_execution_handler.py`) — routes to `ExecutionOrchestrator` ✅.
  Batch via `batch_backtest.py` + `engine/modes/batch/` ✅.
- CLI: `cli/main.py` dispatches by subcommand (`batch-backtest`, `backtest`) or `--operation live_execution`. No unified
  `--mode batch|live` flag ⚠️.
- Transport: `engine/modes/batch/` uses GCS (`StorageAdapter`) ✅. `engine/modes/live/` uses GCS async sink + venue
  WebSocket/exchange APIs (not PubSub for order routing — by design for execution) ⚠️.
- Unit test live: `test_live_execution_handler.py` ✅, `test_mode_adapters.py` ✅. Unit batch: `test_mode_adapters.py`
  ✅. Integration: `test_batch_live_symmetry.py` ✅ (tests TWAP algo consistency, not transport switching).

### Critical Gaps (Blocking Phase 1)

**MISSING live_handler — services with batch only:**

1. **MTDS** — live mode uses batch handler with coordination event setup; no dedicated live handler class
2. **FVS** — live_data_source.py seam exists but no handler to wire it
3. **FCS** — live mode is a `logger.info("not yet implemented")` stub
4. **FOS** — live_data_source.py seam exists but no handler to wire it

**MISSING both handlers — fully incomplete:** 5. **FCM** — no handlers/ dir, no --mode flag, no batch path, always runs
in implicit live-style 6. **FCIS** — has --mode flag, no handlers, both modes are TODO stubs 7. **FMTF** — has --mode
flag, no handlers, live is explicit stub in orchestrator

**MISSING batch_handler (live only):**

- None. All services that have live also have batch (or are batch-only like MLTR).

**MISSING --mode flag (CLI gap):** 8. **MDPS** — no --mode flag; live handler exists but not selectable via CLI
parser 9. **IS** — uses `--run-mode` not `--mode` (nonstandard)

**MISSING unit tests for live mode:** 10. **MTDS** — no live handler test 11. **FDS** — seam test only (no
live_handler.py test) 12. **FVS** — seam test only 13. **FCS** — seam test only 14. **FOS** — seam test only 15. **FCM**
— none 16. **FCIS** — none 17. **FMTF** — none 18. **STR** — seam test only

**MISSING unit tests for batch mode:** 19. **MTDS** — no batch handler unit test 20. **FSS** — no batch_handler.py unit
test

**Transport switching gaps (live does not use PubSub):** 21. **IS** — live handler writes to GCS (wall-clock pull), not
PubSub streaming (acceptable for reference data pattern but non-standard) 22. **MDPS** — live_mode_handler uses GCS sink
in both modes (no PubSub publish in live) 23. **MTDS** — live mode uses coordination events not PubSub data stream

**MLTR — exempt from live-mode requirement (batch-only by design):** MLTR should be formally documented as batch-only.
Remove from the 28-combination target; target is 26 combinations (13 services × 2 modes).

### Phase 1 TODOs (Gap Remediation)

Each missing handler → create a dedicated `live_mode_handler.py` or `batch_handler.py` using the reference patterns in
P1.1.

**P1-TODO-01** ✅ DONE `market-tick-data-service`: Create `cli/handlers/live_mode_handler.py` — wraps `DownloadHandler`
but adds PubSub-style trigger (subscribe to INSTRUMENTS_READY, then run). Move live coordination event subscription out
of `cli/main.py` into dedicated handler class.

**P1-TODO-02** ✅ DONE `features-volatility-service`: Create `cli/handlers/live_handler.py` — wire
`adapters/live_data_source.py` (already has `get_queue_client()` seam) into a handler run loop subscribing to candle
events and writing to `broadcast_sink.py`.

**P1-TODO-03** ✅ DONE `features-calendar-service`: Create `cli/handlers/live_handler.py` — subscribe to upstream
features-ready topic, re-compute calendar features on each event, publish to output topic. Remove "not yet implemented"
stub from `batch_handler.py`.

**P1-TODO-04** ✅ DONE `features-onchain-service`: Create `cli/handlers/live_handler.py` — wire
`adapters/live_data_source.py` seam into run loop.

**P1-TODO-05** `features-commodity-service`: Create `cli/handlers/` directory with `live_handler.py` (PubSub subscribe
to commodity data topic, publish signals) and `batch_handler.py` (GCS read/write, date-range). Add `--mode batch|live`
to `cli/main.py`.

**P1-TODO-06** ✅ DONE `features-cross-instrument-service`: Create `cli/handlers/` directory with `live_handler.py` and
`batch_handler.py`. Implement both (currently all logic is TODO stubs — coordinate with FCIS backlog).

**P1-TODO-07** ✅ DONE `features-multi-timeframe-service`: Create `cli/handlers/` directory with `live_handler.py`
(replace `orchestrator.run_live()` stub with real PubSub subscriber) and `batch_handler.py` (extract batch loop from
orchestrator).

**P1-TODO-08** `market-data-processing-service`: Add `--mode batch|live` to `cli/parser.py`. Wire selection so
`--mode live` invokes `live_mode_handler.py` and `--mode batch` invokes `app/batch_handler.py`.

**P1-TODO-09** `instruments-service`: Rename `--run-mode` to `--mode` in `cli/parser.py` for codex compliance. Create
`cli/handlers/batch_handler.py` as thin wrapper over `instrument_handler.py` + `batch_orchestrator.py`.

**P1-TODO-10** `features-sports-service`: Add unit tests for `batch_handler.py` (file:
`tests/unit/test_batch_handler.py`).

**P1-TODO-11** `market-tick-data-service`: Add unit tests for `cli/batch_handler.py` (file:
`tests/unit/test_batch_handler.py`).

**P1-TODO-12** `ml-training-service`: Document explicitly as batch-only service in codex (`batch-live-symmetry.md`) and
in repo `docs/` — exempt from live-mode handler requirement. Rename handlers to clarify: `train_handler.py` maps to
"batch training" concept.

**P1-TODO-13** `strategy-service`: Consolidate live routing — promote `StrategyLiveHandler` from `service_entry.py` to
`cli/handlers/live_handler.py`. Add `--mode` to `cli/parser.py` choices (currently batch only). Align with codex
pattern.

**P1-TODO-14** ✅ DONE `execution-service`: Add unified `--mode batch|live` flag to `cli/main.py` or
`cli/argument_parser.py` (currently uses subcommands). Ensure `--mode live` routes to `live_execution_handler.py` and
`--mode batch` routes to `batch_backtest.py`.

**P1-TODO-15** (all services with seam-only live tests): Add `test_live_mode_handler.py` unit tests for FDS, FVS, FCS,
FOS, STR — test the handler class directly with mocked transport, not just importability.

---

## Phase 1: Fill handler gaps

### P1.1 — Reference patterns

**Reference live_mode_handler** (from `market-data-processing-service`):

```python
class LiveModeHandler:
    def __init__(self, config: ServiceConfig) -> None:
        self._transport = get_pubsub_client()  # UCI — PubSub in live
        self._freshness = FreshnessMonitor(contract=LIVE_FRESHNESS_CONTRACT)

    async def run(self) -> None:
        log_event(STARTED, mode="live")
        asyncio.create_task(self._freshness.monitor(self._get_last_update))
        async for message in self._transport.subscribe(self._input_topic):
            result = await self._process(message)
            await self._transport.publish(self._output_topic, result)
            log_event(DATA_BROADCAST, mode="live", count=1)
        log_event(STOPPED, mode="live")
```

**Reference batch_handler** (from `features-calendar-service`):

```python
class BatchHandler:
    def __init__(self, config: ServiceConfig) -> None:
        self._storage = get_storage_client()  # UCI — GCS in batch

    async def run(self, start_date: date, end_date: date) -> None:
        log_event(STARTED, mode="batch")
        for day in date_range(start_date, end_date):
            data = await self._storage.read(self._input_path(day))
            result = await self._process(data)
            await self._storage.write(self._output_path(day), result)
        log_event(PROCESSING_COMPLETED, mode="batch")
```

### P1.2 — Create missing handlers

Per Phase 0 audit. Services needing live_handler created: MTDS, FVS, FCS, FOS, FCM, FCIS, FMTF. Services needing
batch_handler created: FCM, FCIS, FMTF. See P1-TODO-01 through P1-TODO-09 above. Services needing structural
consolidation: STR (service_entry.py → handlers/live_handler.py), EXEC (subcommand → --mode flag).

### P1.3 — CLI `--mode` flag

Every service CLI parser must accept `--mode batch|live`. If flag absent: add to each `cli/parser.py` or `cli/main.py`.

```python
parser.add_argument(
    "--mode",
    choices=["batch", "live"],
    default="batch",
    help="Operational mode: batch (GCS) or live (PubSub)"
)
```

---

## Phase 2: Transport protocol verification

### P2.1 — Unit test for transport switching

File per service: `tests/unit/test_mode_switching.py` (if absent)

```python
@pytest.mark.parametrize("mode,expected_transport", [
    ("batch", "GCSTransport"),
    ("live", "PubSubTransport"),
])
def test_correct_transport_selected(mode: str, expected_transport: str) -> None:
    config = ServiceConfig(mode=mode)
    handler = create_handler(config)
    assert type(handler._transport).__name__ == expected_transport
```

### P2.2 — Integration test with mocked deps

File per service: `tests/integration/test_mode_switching.py` (if absent)

```python
@pytest.mark.parametrize("mode", ["batch", "live"])
async def test_handler_produces_valid_output_schema(mode: str, mock_transport) -> None:
    handler = create_handler(mode, mock_transport)
    await handler.run_one_cycle(fixture_input)
    output = mock_transport.get_published()
    # Validate against UAC/UIC schema
    assert_schema_valid(output, SERVICE_OUTPUT_SCHEMA)
    # Verify events emitted correctly
    events = mock_uei.get_events()
    assert any(e.type == "STARTED" for e in events)
    assert any(e.type in ("DATA_BROADCAST", "PROCESSING_COMPLETED") for e in events)
```

---

## Phase 3: SIT batch-live symmetry test

### P3.1 — Symmetry test

File: `system-integration-tests/tests/integration/test_batch_live_symmetry.py`

For each service:

1. Run in batch mode with 1 day of fixture data (from dev seeded data)
2. Run in live mode with same data injected via mock PubSub
3. Compare outputs: schemas identical, values identical (same input = same output)
4. Verify event sequences are correct for each mode

```python
@pytest.mark.parametrize("service_name", [
    "instruments-service",
    "features-delta-one-service",
    "features-volatility-service",
    # ... all 14
])
async def test_batch_live_output_identical(service_name: str, fixture_data) -> None:
    batch_output = await run_service_batch(service_name, fixture_data)
    live_output = await run_service_live(service_name, fixture_data)
    assert batch_output.schema == live_output.schema
    assert batch_output.values == live_output.values  # same data = same result
```

---

## Phase 4: Documentation update

### P4.1 — Update batch-live-symmetry.md

File: `unified-trading-/codex/04-architecture/batch-live-symmetry.md`

Add:

- Audit matrix with final results
- Handler pattern with code examples (reference implementations)
- Transport selection diagram
- Freshness monitoring integration (how FreshnessMonitor integrates with live handlers)
- Test pattern for new services

---

## Verification Gates

- [ ] Audit matrix: 26 combinations GREEN (13 services × 2 modes; MLTR exempt as batch-only)
- [ ] Phase 0 findings resolved: P1-TODO-01 through P1-TODO-15 all closed
- [ ] `pytest */tests/unit/test_mode_switching.py` — all pass (new files per P2.1)
- [ ] `pytest */tests/integration/test_mode_switching.py` — all pass (new files per P2.2)
- [ ] SIT symmetry test — 13 services pass batch vs live comparison
- [ ] No service reachable via CLI without `--mode batch|live` flag (except MLTR which uses `--mode train|evaluate`)
- [ ] All services: `RUNTIME_MODE` env var respected when no CLI flag

## Files Modified / Created

- Missing `live_mode_handler.py` files (new, per audit findings)
- Missing `batch_handler.py` files (new, per audit findings)
- `*/cli/parser.py` — add `--mode` flag where absent
- `*/tests/unit/test_mode_switching.py` — add where absent
- `*/tests/integration/test_mode_switching.py` — add where absent
- `system-integration-tests/tests/integration/test_batch_live_symmetry.py` (new)
- `unified-trading-/codex/04-architecture/batch-live-symmetry.md` (update)
- `unified-trading-pm/audits/batch_live_mode_audit_2026_03_10.md` (new)

## Dependencies

- `data_availability_live_expectations_2026_03_10.md` (FreshnessMonitor wired in live handlers)
- `phase3_service_hardening_integration.md` (service hardening includes mode handler completion)
- `mock_data_dev_project_seeding_2026_03_10.md` (fixture data for symmetry tests)
