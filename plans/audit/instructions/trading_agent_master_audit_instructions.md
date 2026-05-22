---
name: trading_agent_master_audit_instructions
type: audit-instructions
epic: trading_agent_master
assigned_vm: vm-trading-core
tier: L2
last_updated: 2026-05-22
---

# Trading Agent Master — Audit Instructions

## Epic Scope

trading-agent-service: closed-loop allocator that connects strategy signals to execution, workspace QG integration,
per-client subprocess isolation. Key issues tracked: GH_PAT silent clone fail, workspace QG health.

Codex SSOTs: `codex/04-architecture/per-client-isolation-architecture.md`

## Triggers

- Monthly (minimum cadence)
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

## Success Criteria

- All 6 checklist items GREEN
- workspace QG exits 0 for trading-agent-service (no silent clone fail)
- Closed-loop allocator test passes

## Output Format

Result file at `plans/audit/results/trading_agent_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
