---
doc_type: audit-instruction
title: trading_agent_master_audit_instructions
summary:
  Weekly audit checklist for trading-agent-service (closed-loop allocator strategy→execution) — 6 checks covering GH_PAT
  valid (no silent clone fail), workspace QG exits 0, allocator integration test, per-client multiprocessing.Process
  isolation, ServiceBootstrap (STEP 5.61), and make_health_router (STEP 5.62), plus batch→paper→live e2e goal posts.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [trading-agent-service]
scope: [engineer, admin]
tags: [audit, trading-agent, quality-gates, per-client-isolation, execution, reconciliation]
related: [/codex/04-architecture/per-client-isolation-architecture.md]
created: 2026-05-22
tier: L2
parent_epic: infrastructure_master
cadence: Weekly
verifier:
lifespan:
type: audit-instructions
epic: trading_agent_master
assigned_vm: vm-trading-core
last_updated: 2026-05-22
---

# Trading Agent Master — Audit Instructions

## Epic Scope

trading-agent-service: closed-loop allocator that connects strategy signals to execution, workspace QG integration,
per-client subprocess isolation. Key issues tracked: GH_PAT silent clone fail, workspace QG health.

Codex SSOTs: `/codex/04-architecture/per-client-isolation-architecture.md`

## Triggers

- Weekly (minimum cadence)
- Whenever workspace QG reports a silent clone fail for trading-agent-service
- After any GH_PAT rotation
- After per-client isolation architecture changes

## Checklist

- [ ] (a) **GH_PAT secret valid**: trading-agent-service GH_PAT is not the invalid key that caused silent clone fail.
      Check: `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md` — status RESOLVED or
      BLOCKED-CREDENTIALS Verify: workspace QG runs without silent failures for this repo

- [ ] (b) **Workspace QG exits cleanly**: `bash scripts/quality-gates.sh` exits 0 for trading-agent-service. Run:
      quality gates in trading-agent-service dir

- [ ] (c) **Closed-loop allocator integration test**: test exercises full pipeline (strategy signal → allocator → mock
      execution) with mock data. Find: `rg "allocator" trading-agent-service/tests/ --include="*.py" -l`

- [ ] (d) **Per-client subprocess isolation**: allocator uses `multiprocessing.Process` per client (not threads). Grep:
      `rg "multiprocessing.Process\|Process(" trading-agent-service/ --include="*.py"` — verify used in main loop

- [ ] (e) **ServiceBootstrap present — QG STEP 5.61**: `ServiceBootstrap(...)` in service source for
      STARTED/STOPPED/FAILED events. Grep: `rg "ServiceBootstrap" trading-agent-service/ --include="*.py"` — at least 1
      hit in main service file

- [ ] (f) **Health router present — QG STEP 5.62**: `api/main.py` imports `make_health_router` from UTL and registers
      it. Grep: `rg "make_health_router" trading-agent-service/ --include="*.py"`

### E2E Pipeline Verification (Batch → Paper → Live)

- (e2e-batch) **Batch e2e audit**: run `bash scripts/quality-gates.sh` with mock upstream features data → strategy
  produces signals → execution records manifest rows. Use `CLOUD_MOCK_MODE=true` and synthetic feature fixtures. Goal:
  confirm the entire batch code path executes without real upstream data.
- (e2e-paper) **Paper trading goal post**: paper trading for ≥1 DeFi archetype runs ≥7 days without silent failures.
  Manifest shows strategy_output + execution_record rows. PnL stream emits StrategyPnlStreamEvent. Dashboard shows paper
  positions. This is the gate before live.
- (e2e-live) **Live trading goal post**: live execution for ≥1 DeFi archetype with real wallet transactions confirmed
  on-chain. PnL calculator confirms realized + unrealized PnL matches expected from strategy signals.
- (post-trade) **Post-trade audit**: after live runs ≥7 days, verify execution records match strategy signals (no
  slippage model regression), PnL attribution is correct, and no cross-client fund movement occurred.
- (mock-upstream) **Mock upstream pattern**: strategy and execution audits MUST be runnable with mock MTDS + features
  data. Document the mock fixture location and how to substitute upstream parquets for independent downstream testing.

## Success Criteria

- All 6 checklist items GREEN
- workspace QG exits 0 for trading-agent-service (no silent clone fail)
- Closed-loop allocator test passes

- Batch e2e with mock upstream: full code path from features → strategy → execution runs without errors
- Paper trading ≥7 days: strategy_output + execution_record rows in manifest, PnL events flowing
- Live trading confirmed: ≥1 on-chain transaction verified for a real wallet

## Output Format

Result file at `plans/audit/results/trading_agent_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
