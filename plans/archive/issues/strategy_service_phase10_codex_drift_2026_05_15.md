---
doc_type: issue
title: Phase 10 Codex Audit — strategy-service backtest/family/venue-admission drift (2026-05-15)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-15
author: slot-3
resolved: 2026-05-17
resolution:
  SHIPPED — both drifts. Drift 1 (eligible_venues silent fallthrough) diagnosed + WARN-fix at
  `execution-service@7957371d` + 3 unit tests. Drift 2 (defi_lp/mev subdir family-map alignment) test at
  `strategy-service@f01d12d` + 4 unit tests.
source:
  [
    /codex/04-architecture/backtest-groups.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    strategy-service/strategy_service/engine/backtest/runner.py,
    strategy-service/strategy_service/engine/strategies/v2/orchestrator.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py,
  ]
locked_by: live-defi-rollout
---

# Phase 10 Codex Audit — Backtest / Family / Venue-Admission Drift

Audit performed 2026-05-15 per item 11 of slot 3 queue extension. Phase 10 = Group B backtest runner (strategy alpha).
Compared codex `backtest-groups.md` + `venue-eligibility.md` against shipped code.

---

## What I found

### ✅ CONFIRMED ALIGNED (7 items)

| Codex requirement                                    | Code location                                                                                                                                                    | Status     |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Group B uses same code path as live (batch=live)     | `GroupBRunner._process_tick` calls `V2EngineOrchestrator.on_tick`                                                                                                | ✅ ALIGNED |
| Only fill source differs from live                   | `BenchmarkFillEngine` replaces real venue path; orchestrator unchanged                                                                                           | ✅ ALIGNED |
| `DeployableConfigCandidate` output with content hash | `config_candidate.py` — `DeployableConfigCandidate` with `content_hash` field                                                                                    | ✅ ALIGNED |
| Sharpe/Sortino/Calmar/MaxDD metrics                  | `GroupBMetrics` in `config_candidate.py` has all 4                                                                                                               | ✅ ALIGNED |
| `BacktestGroup.B_STRATEGY` enum used                 | `GroupBRunner.backtest_group` returns `BacktestGroup.B_STRATEGY`                                                                                                 | ✅ ALIGNED |
| 9 canonical `StrategyFamily` values                  | UAC `StrategyFamily` enum: ML_DIRECTIONAL/RULES_DIRECTIONAL/CARRY_AND_YIELD/ARBITRAGE_STRUCTURAL/MARKET_MAKING/EVENT_DRIVEN/VOL_TRADING/STAT_ARB_PAIRS/PORTFOLIO | ✅ ALIGNED |
| Code dirs map to canonical families                  | `defi_lp → MARKET_MAKING` (documented), `mev → ARBITRAGE_STRUCTURAL` (documented)                                                                                | ✅ ALIGNED |

### ⚠️ DRIFTS FOUND

#### Drift 1 (Medium): `eligible_venues` never populated on emitted instructions

- **Codex** (`venue-eligibility.md`):
  > "Strategy emits intent with `eligible_venues: [...]`. Execution-service's SOR picks the one that will actually
  > receive the order right now."
- **Code**: `StrategyInstructionEnvelope.eligible_venues: list[str] = Field(default_factory=list)` in UAC schemas.py
  (line 225). Zero instances of `eligible_venues` being set anywhere in strategy-service
  (`grep -rn "eligible_venues" strategy_service/` → 0 hits).
- **Impact**: Every instruction emitted has `eligible_venues=[]`. Execution-service SOR has no venue guidance from
  strategy for SOR-routed instructions; must use own defaults.
- **Scope**: All archetype engines (CSB, APD, and 10+ others).
- **Ambiguity**: SOR applies to `venue_routing_mode: SOR_AT_EXECUTION` instructions. CSB emits `AtomicInstruction` with
  venue-specific legs (LEADER_HEDGE); APD may be `STRATEGY_PICKED`. If all instructions are `STRATEGY_PICKED`
  (target_venue already set), empty `eligible_venues` is fine by design. If any instruction uses `SOR_AT_EXECUTION`,
  this is a bug.
- **Recommended decision**: Diagnose in execution-service — does it treat empty `eligible_venues` as "all venues OK" or
  as "no venues admitted"? If the former, this is fine. If the latter, strategy engines must populate the field.
  Cross-repo scope → escalate to slot 1 for triage.

#### Drift 2 (Low): `defi_lp/` and `mev/` subdirectory → family mapping only in docstrings

- **Codex**: Expects `ARCHETYPE_TO_FAMILY` in UAC as the canonical mapping.
- **Code**: `defi_lp/__init__.py` says "DeFi LP archetypes share the MARKET_MAKING family"; `mev/__init__.py` says "MEV
  strategies are tagged `StrategyFamily.ARBITRAGE_STRUCTURAL`". No runtime assertion checks that archetypes in these
  subdirs actually map to the expected family in `ARCHETYPE_TO_FAMILY`.
- **Impact**: Organizational — a developer could add a wrong archetype to the wrong subdir without a test catching it.
- **Fix**: Low priority. Add a test that for each module in `defi_lp/` and `mev/`, the archetype's `StrategyFamily` from
  `ARCHETYPE_TO_FAMILY` matches the claimed family in `__init__.py`. **NICE-TO-HAVE P3.**

---

## Why it matters

Drift 1: If SOR-mode instructions hit execution-service with `eligible_venues=[]`, the execution-service may fail
silently or route to an unintended venue. This is a data correctness risk for live trading and Group B backtest
validity.

Drift 2: Low risk. Organizational confusion only.

---

## Recommended decision

- **Drift 1**: ✅ DIAGNOSED + WARN-FIX SHIPPED 2026-05-17 by slot-3. Reading `execution_service/v2/handlers.py:81`
  confirmed the behaviour: empty `eligible_venues` + empty `target_venue` → silent route to `"UNKNOWN_VENUE"` sentinel
  (NOT "all OK"). Strategy-side bug. Fix shipped at `execution-service@7957371d` emits a WARNING log so the silent
  fall-through becomes visible in the event stream; behaviour otherwise unchanged (backwards-compatible). Strategy
  engines still need to populate at least one of the two — the warning lets ops catch it.
- **Drift 2**: ✅ SHIPPED 2026-05-17 by slot-3 — `strategy-service@f01d12d` family-map test (above).

---

## Deferred work

| Item                                                          | Status                                                                                                                                                                                                                                                                                                                | Owner  |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| Diagnose execution-service SOR empty-eligible_venues behavior | ✅ DIAGNOSED + WARN-FIX SHIPPED 2026-05-17 (slot-3) — `execution-service@7957371d` `_resolve_venue` now emits WARNING when both target_venue + eligible_venues are empty (falls through to UNKNOWN_VENUE sentinel — strategy-side bug, no longer silent). 3 new tests in `tests/unit/v2/test_router_and_handlers.py`. | Slot 3 |
| Add family-map assertion test for defi_lp / mev subdirs       | ✅ SHIPPED 2026-05-17 (slot-3) — `strategy-service@f01d12d` `tests/unit/engine/strategies/v2/test_subdir_family_alignment.py` (4 tests green)                                                                                                                                                                         | Slot 3 |
