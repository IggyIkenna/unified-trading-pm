---name: d0-orchestrator-migration-2026-05-20
title: D0 — agent-orchestrator migration plan
created: 2026-05-20
author: ikenna (slot-8)
status: active
priority: P1
deadline: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
parent_plan: master_to_live_defi_2026_05_23.md
source_audits:
  - plans/audit/orchestrator_service_contract_audit_2026_05_20.md # C11
related_plans:
  - agent_orchestrator_cloud_run_deployment_2026_05_19.md
  - agent_orchestrator_dual_deployment_2026_05_19.md
parent_epic: orchestrator_master
---

# D0 — agent-orchestrator migration plan

> **Ordering step 0** in the Phase-E execution chain (runs in parallel with others — no D1+ dependency).
>
> C11 audit found **0 P0 findings** for the orchestrator. The agent-orchestrator is operator tooling, NOT a trading
> service — standard trading-service contract patterns (manifest emission, DependencyError) do not apply. Remaining gaps
> are P2/P3 correctness improvements.

## P2/P3 findings from C11

| Finding                                                                                        | Severity | File                     |
| ---------------------------------------------------------------------------------------------- | -------- | ------------------------ |
| Port mismatch: orchestrator uses 8765 internally but workspace port registry lists 8026        | P2       | orchestrator config      |
| CORS origin missing prod domain `agent-orchestrator.odum-research.com`                         | P2       | orchestrator CORS config |
| Dashboard work-split surface not yet fully replacing LEDGER.md as the authoritative split tool | P3       | process gap              |

## Remediation backlog

### Phase 1 — Port alignment

- [ ] [AGENT] P2. Align orchestrator port: update internal config to use 8026 (workspace standard per port registry
      `unified-trading-pm/scripts/dev/ui-api-mapping.json`); update any LEDGER.md or continuation-prompt references that
      mention 8765
- [ ] [AGENT] P2. Update CLAUDE.md orchestrator reference (already shows 8026) to confirm this is the deployed port; add
      a port-check assertion to the orchestrator startup log

### Phase 2 — CORS fix

- [ ] [AGENT] P2. Add `agent-orchestrator.odum-research.com` to CORS allowed origins in orchestrator FastAPI app config
  - Current: likely `localhost:*` only
  - Required: prod domain + localhost for local dev

### Phase 3 — Dashboard → LEDGER deprecation

- [ ] [AGENT] P3. Annotate `ikenna_orchestrator/LEDGER.md` and `harsh_orchestrator/LEDGER.md` with deprecation header
      pointing to dashboard at `agent-orchestrator.odum-research.com` as authoritative source
  - Dashboard is already authoritative per CLAUDE.md § "Daily Work-Split Process"
  - LEDGER.md stays as offline fallback but should not be primary read surface

## Success criteria

- [ ] Phase 1: orchestrator health endpoint responds on port 8026 in local dev; port registry is consistent
- [ ] Phase 2: `curl -H "Origin: https://agent-orchestrator.odum-research.com" -I http://localhost:8026/health` returns
      `Access-Control-Allow-Origin: https://agent-orchestrator.odum-research.com`
- [ ] Phase 3: LEDGER.md files carry deprecation header (offline fallback, not primary)

## Full-execution criterion

> Orchestrator boots on 8026 in local dev (`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh`) and prod
> CORS request from `agent-orchestrator.odum-research.com` succeeds. No service-contract P0 gaps identified in C11 —
> this plan is predominantly correctness cleanup.

## Temporary states

None — these are all direct fixes with no transitional state required.
