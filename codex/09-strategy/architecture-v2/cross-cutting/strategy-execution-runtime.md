---
doc_type: codex-ssot
title: Strategy Execution Runtime
summary:
  "Strategy execution runtime tick-loop lifecycle on a strategy VM: `ServiceBootstrap` STARTED → per-client preflight
  (KMS auth → venue ping → balance → CLIENT_READY) → per tick (features → archetype signal → allocator pipeline → emit
  `StrategyInstruction` or `record_empty` → manifest row → PnL stream) → STOPPED/FAILED. Entry via
  `colocated_engine.py`."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [trading-agent-service]
scope: [engineer]
tags: [strategy, execution, orchestrator, manifest, self-healing]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md,
    ../../../04-architecture/promote-workflow-architecture.md,
    /codex/09-strategy/architecture-v2/cross-cutting/treasury-trading-wallet-invariant.md,
    /codex/09-strategy/architecture-v2/cross-cutting/universe-enumeration-contract.md,
  ]
created: 2026-05-22
authoritative_for:
  [
    strategy execution-runtime tick-loop lifecycle (colocated_engine STARTED/tick/STOPPED + instruction-emission
    contract),
  ]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-config-drift-detection.md,
    /codex/09-strategy/architecture-v2/cross-cutting/universe-enumeration-contract.md,
  ]
owner:
last_reviewed: 2026-05-22
code_refs:
---

# Strategy Execution Runtime

> **[DELTA 2026-05-22]** **Current state:** Runtime lifecycle (startup, heartbeat, shutdown) is implemented but not
> documented at codex level. Discovery via `strategy_archetype_logic_audit_2026_05_20.md`. **Planned delta:** Full
> runtime spec per `strategy_master.md`. **Target architecture:** Canonical lifecycle contract for strategy → execution
> instruction emission.

## Context

The strategy execution runtime is the loop that runs continuously on a strategy VM, consuming market data and emitting
`StrategyInstruction` objects per tick. It is the "inner loop" of the deployed strategy system.

## Current State

Runtime is implemented via `colocated_engine.py` (CLI entrypoint for paper/live mode) wiring into per-archetype engine
classes (`BaseArchetypeEngineV2` subclasses). `ServiceBootstrap` handles STARTED/STOPPED/FAILED events.

Key components:

- `strategy_service/engine/core/base_engine_v2.py` — base tick loop + signal generation
- `strategy_service/engine/core/gcs_storage_service.py` — instruction write path (with `StrategyManifestRecorder`)
- `strategy_service/engine/co_located/colocated_engine.py` — CLI entrypoint bridging paper/live modes
- `strategy_service/portfolio_allocator/service.py` — allocator step within the tick loop

## Runtime Lifecycle

```
VM boots → ServiceBootstrap STARTED
    → load strategy config (hot-reload via StrategyDirectiveReloader)
    → per-client preflight (KMS auth → venue ping → balance fetch → CLIENT_READY)
    → tick loop starts:
        per tick:
            1. fetch features / market data
            2. archetype signal generation
            3. allocator pipeline (sizing + guard_rails)
            4. emit StrategyInstruction (or record_empty if no signal)
            5. write manifest row (record_captured / record_empty / record_failed)
            6. emit StrategyPnlStreamEvent to trading-agent-service
    → on shutdown: SERVICE_STOPPED + manifest flush
    → on unhandled exception: SERVICE_FAILED + alert
```

## Instruction Emission Contract

- Each tick where a signal fires: one `StrategyInstruction` per (client_id, strategy_id, leg_id)
- No signal: `StrategyManifestRecorder.record_empty(reason=EXPECTED_NO_SIGNAL)` — no parquet row written
- GCS error: `StrategyManifestRecorder.record_failed()` — `DependencyError(fail_fast=False)` per shard-isolation rule

## See also

- `plans/epics/strategy_master.md`
- `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`
- `plans/active/strategy_execution_contract_remediation_2026_05_20.md`
- `/codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md`
- `/codex/04-architecture/promote-workflow-architecture.md`
