---
doc_type: codex-ssot
title: Allocator Pipeline Contract
summary:
  "WIP contract (DELTA 2026-05-22) for the strategy-service allocator pipeline sitting between archetype signal
  generation and StrategyInstruction emission: risk-gate application order (leverage cap → drawdown gate → exposure cap
  → per-instrument limit), sizing formula (signal_size_pct × portfolio_nav × leverage_multiplier via guard_rails), and
  ArchetypeAllocationDirective.weight override semantics. Full contract to be specified per strategy_master."
status: draft
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, trading-agent-service]
scope: [engineer]
tags: [strategy, allocator, execution, risk, reconciliation]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/instrument-type-leverage-matrix.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-param-schema-inventory.md,
    ../../../04-architecture/trading-agent-service-directive-pipeline.md,
  ]
created: 2026-05-22
authoritative_for: [archetype-signal-to-allocator-to-execution instruction pipeline contract]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-param-schema-inventory.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-strategy-params.md,
    /codex/09-strategy/architecture-v2/cross-cutting/instrument-type-leverage-matrix.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md,
    /codex/09-strategy/architecture-v2/cross-cutting/universe-enumeration-contract.md,
  ]
owner:
last_reviewed: 2026-05-22
code_refs:
---

# Allocator Pipeline Contract

> **[DELTA 2026-05-22]** **Current state:** Allocator pipeline exists in strategy-service but contract is undocumented
> at codex level. Discovery via `strategy_archetype_logic_audit_2026_05_20.md`. **Planned delta:** Full contract to be
> specified per `strategy_master.md`. **Target architecture:** Canonical allocator→execution instruction contract
> (sizing, risk limits, instruction format).

## Context

The allocator pipeline sits between archetype signal generation and execution instruction emission. It applies risk-gate
filters, position-size constraints, and leverage limits before emitting `StrategyInstruction` objects to
execution-service.

Key components (as of 2026-05-22, strategy-service):

- `strategy_service/portfolio_allocator/service.py` — main allocator loop
- `strategy_service/portfolio_allocator/guard_rails.py` — risk-limit enforcement
- `strategy_service/portfolio_allocator/emitter.py` — instruction emission boundary
- `BaseArchetypeEngineV2.weight_with_directive()` — directive-weighted allocation (wired May-23; no-op stub)

## Current State

Pipeline is implemented but the contract between archetype signal outputs and allocator inputs (field shapes, sizing
semantics, risk-limit application order, directive override semantics) is undocumented at codex level.

The trading-agent-service `ArchetypeAllocationDirective` composes with this pipeline:
`/codex/04-architecture/trading-agent-service-directive-pipeline.md`.

## Target

Full contract spec including:

1. Input shape: archetype signal → allocator (position target, confidence score, timestamp)
2. Risk-gate application order (leverage cap → drawdown gate → exposure cap → per-instrument limit)
3. Sizing formula: `position_size = signal_size_pct × portfolio_nav × leverage_multiplier` (subject to guard_rails)
4. Output shape: allocator → `StrategyInstruction` (UAC schema, execution routing, instrument_id)
5. Directive override semantics: `ArchetypeAllocationDirective.weight` multiplies the signal_size_pct before sizing

## See also

- `plans/epics/strategy_master.md`
- `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`
- `/codex/09-strategy/architecture-v2/cross-cutting/instrument-type-leverage-matrix.md`
- `/codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md`
- `/codex/04-architecture/trading-agent-service-directive-pipeline.md`
