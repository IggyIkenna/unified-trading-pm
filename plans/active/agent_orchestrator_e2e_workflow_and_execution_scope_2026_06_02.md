---
title: Agent-orchestrator end-to-end workflow + execution-scope plan-routing field
parent_epic: orchestrator_master
priority: P1
status: active
execution_scope: local-only
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
created: 2026-06-02
locked_by: live-defi-rollout
locked_since: 2026-06-02
related_plans:
  - plans/active/harsh_day_master_2026_06_02.md
  - plans/active/agent_context_and_memory_hygiene_2026_06_02.md
  - plans/active/quality_gates_resource_contention_speedup_2026_06_02.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/epics/orchestrator_master.md
  - plans/active/issues/orchestrator_autonomy_residual_findings_2026_06_02.md
---

# Agent-orchestrator e2e workflow + execution-scope field

## Why

The intended autonomous loop is: **audit instructions → results + agent-surfaced issue docs → new plans → push →
orchestrator backlog → worker assignment → quickmerge → staging → SIT → main → CICD**. Verified against the code
2026-06-02 (operator-stated flow vs reality below). Most of it is live; the gaps are a missing plan-routing field, a
discovery-latency question, and stale rules that contradict the live merge path.

## The canonical flow vs reality (verified 2026-06-02)

| Step                                                                         | Reality                                                                                                            | Evidence                                                                                             |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| audit instr (`plans/audit/instructions/`) → results (`plans/audit/results/`) | convention; produced by agents/slots                                                                               | —                                                                                                    |
| agents surface bugs/ambiguity → issue docs (`plans/active/issues/`)          | convention; manual                                                                                                 | —                                                                                                    |
| results + issues → **new plan**                                              | **MANUAL** — orchestrator does NOT scan `issues/` or `audit/results/`, and does NOT auto-author plans              | `regen_backlog_from_plan.py` globs `plans/active/*.md` non-recursively                               |
| new plan pushed → orchestrator acks                                          | ✅ but **polling**, not push-triggered                                                                             | `PlanRegenLoop` (interval env `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS`; +~60s after boot) — **G2** |
| backlog → worker assignment                                                  | ✅ fully automated, no human gate                                                                                  | `dispatch.pick_next_task()`                                                                          |
| which plans are picked up / by which VM                                      | only `assigned_vm` gates VM routing; **no orchestrator-vs-local gate** → absent `assigned_vm` ⇒ picked up globally | `regen_backlog_from_plan.py` per-VM filter — **G1**                                                  |
| workers finish → quickmerge → staging                                        | ✅ live — `quickmerge` default routes ALL commits → `staging`; `--to-staging` is a no-op                           | `scripts/quickmerge.sh` (PR base = staging)                                                          |
| SIT → staging merged to main                                                 | ✅ dispatch-driven — SIT emits `staging-validated` → `staging-to-main.yml` auto-merges                             | `.github/workflows/staging-to-main.yml`                                                              |
| main → CICD                                                                  | ✅ `main` push → `qg-passed` → `cloud-build-router` → `uts-prod` (frontend/firestore/backend)                      | `cloud-build-router.yml`                                                                             |

**Exception (codified):** `agent-orchestrator` repo targets `main` directly (skips LDR→staging→main) — it is operator
tooling, not production trading code. **LDR** is NOT phased out: agents commit `tab/<op>/<N>` → push LDR (continuous
integration + server-deploy axis); quickmerge→staging is the **promotion step when a unit is done**.

## Gaps to close

### G1 — execution-scope plan-routing field [P0] _(the field Harsh asked for)_

- [ ] [DESIGN] P0. Add `execution_scope: orchestrator-agent | local-only | hybrid` to PLAN_FORMAT.md frontmatter schema.
      Default when ABSENT = `orchestrator-agent` (backward-compatible — no backfill of the ~200 existing plans needed).
      `local-only` = orchestrator skips ingestion entirely (work done + verified locally by an operator). `hybrid` =
      ingested but flagged for operator review.
- [ ] [SCRIPT] P0. Wire the field into `agent-orchestrator/server/regen_backlog_from_plan.py` — at the per-VM filter,
      skip any plan with `execution_scope: local-only`. Add a unit test (`test_execution_scope_skip`).
- [ ] [DOC] P1. Stamp the local-only coordination/design plans (`harsh_day_master`, `agent_context_and_memory_hygiene`,
      this plan) with `execution_scope: local-only` (done at authoring — confirm the ingester honours it once G1 ships).
      Document the field in the orchestrator overview codex doc.

### G2 — discovery latency [P1] _(Harsh-owned — he will verify the live interval + decide)_

- [ ] [DESIGN] P1. Confirm the REAL `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` in the live env (the default in code is
      long; operator believes it is shorter). If a pushed plan should be acked promptly, either lower the interval or
      add a push/webhook-triggered `/api/backlog/regen`. **Owner: Harsh** (noted he will handle while working this
      plan).

### G3 — merge-flow doc drift [P0] _(fix lives in the context-hygiene plan)_

- [ ] [DOC] P0. The live staging-first quickmerge flow contradicts the rules fed to agents
      (`.claude/rules/workspace-workflow.md` "staging = breaking changes"; `cursor-configs/CLAUDE.md` "quickmerge for
      promotion-to-main" / "DO NOT quickmerge dirty deps → push LDR"). Reconcile to the live model + the LDR dual-path.
      Tracked as instance (e) in
      [agent_context_and_memory_hygiene_2026_06_02.md](agent_context_and_memory_hygiene_2026_06_02.md) Phase 3 — fix
      there, do not duplicate.

### G4 — prove the loop end-to-end [P1]

- [ ] [TEST] P1. Run `agent-orchestrator/scripts/e2e_demo.py` + `scripts/dev.sh --mock` locally; confirm the full
      spawn→work→report→snapshot→resume cycle passes and the dashboard renders. Capture pass/fail + any gap. (Ikenna:
      orchestrator is ready to test; real backlog only after CI + data plans land — mock proves the flow now.)

## Related open work (NOT absorbed here)

The archived `orchestrator_autonomy_audit_remediation_2026_06_01` left **F1/F2/FM3** open (running VM behind LDR HEAD;
vm-ml SSM-degraded/now-stopped; foreign-repo playwright-report still tracked). These are tracked in
[issues/orchestrator_autonomy_residual_findings_2026_06_02.md](issues/orchestrator_autonomy_residual_findings_2026_06_02.md)
— owned there, referenced here so the e2e picture is complete. Fleet is currently consolidated to **2 running VMs**
(vm-orchestrator + api-host); 9 epic VMs stopped.

## Full-execution criterion (PLAN_FORMAT §8)

- `execution_scope` is in PLAN_FORMAT.md, honoured by `regen_backlog_from_plan.py` (test proves a `local-only` plan is
  skipped), and the 3 local-only docs are stamped.
- G2 interval is confirmed in the live env with the operator's decision recorded.
- `e2e_demo.py` passes locally with the result captured.
- G3 reconciliation is closed in the context-hygiene plan (cross-checked, not duplicated).
