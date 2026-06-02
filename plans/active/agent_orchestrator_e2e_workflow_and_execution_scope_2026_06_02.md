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

**Branch model — agent-orchestrator now follows the SAME flow as every other repo (operator decision 2026-06-02,
supersedes the prior `main`-direct exception).** Today the repo has `origin/live-defi-rollout` and `main` but **no
`staging` branch** (verified 2026-06-02 — see G5). It must adopt the full `tab/<op>/<N>` → LDR (continuous integration +
server-deploy axis) → quickmerge→`staging` → SIT → `main` path. **LDR** is the continuous-integration axis; quickmerge→
staging is the **promotion step when a unit is done**; merge-to-`main` is the CICD trigger (see G6).

## Gaps to close

### G1 — execution-scope plan-routing field [P0] _(the field Harsh asked for)_

- [ ] [DESIGN] P0. Add `execution_scope: orchestrator-agent | local-only` to PLAN_FORMAT.md frontmatter schema (two
      values only — `hybrid` dropped per operator 2026-06-02). Default when ABSENT = `orchestrator-agent`
      (backward-compatible — no backfill of the ~200 existing plans needed). `local-only` = orchestrator skips ingestion
      entirely (work done + verified locally by an operator).
- [ ] [SCRIPT] P0. Wire the field into `agent-orchestrator/server/regen_backlog_from_plan.py` — at the per-VM filter,
      skip any plan with `execution_scope: local-only`. Add a unit test (`test_execution_scope_skip`).
- [ ] [DOC] P1. Stamp the local-only coordination/design plans (`harsh_day_master`, `agent_context_and_memory_hygiene`,
      this plan) with `execution_scope: local-only` (done at authoring — confirm the ingester honours it once G1 ships).
      Document the field in the orchestrator overview codex doc.

### G2 — discovery latency [P0] _(Harsh-owned)_

**Verified 2026-06-02:** `DEFAULT_PLAN_REGEN_INTERVAL_SECONDS = 21600` (**6h**) at
`server/regen_backlog_from_plan.py:602` — the long default IS what runs unless the env overrides it (no prod override
confirmed). 6h is far too much latency: plans are authored continuously, so backlog discovery lags up to 6h.

- [ ] [SCRIPT] P0. Lower `DEFAULT_PLAN_REGEN_INTERVAL_SECONDS` to **≤ 1800 (30 min)** in
      `server/regen_backlog_from_plan.py` (operator cap: 30 min max). Update the docstring at line 29 + the comment at
      line 602 (currently "same cadence as SQLite backup" — decouple from the snapshot cadence). Add/adjust the unit
      test asserting the new default.
- [ ] [DESIGN] P1. _(stretch)_ For near-instant ack, add a push-triggered `POST /api/backlog/regen` callable from a
      post-push GHA hook — polling at 30 min is the floor, push is the ceiling. Not required for the 30-min fix.

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

### G5 — backend statelessness for CICD-restart-via-GHA [P0] _(operator-raised 2026-06-02)_

The target deploy model: merge→`main` → CICD rebuilds frontend, updates Firestore, and GHA restarts every backend with
new code. That requires the backend + frontend to be **stateless** (restart-safe). Verified 2026-06-02:

| Surface                   | Stateless?           | Evidence                                                                                                                                |
| ------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Frontend** `dashboard/` | ✅ yes               | Vite/React static build; reads all state from the API at runtime. Rebuild + redeploy is safe.                                           |
| **Backend** `server/`     | ❌ **NOT stateless** | Authoritative state = local SQLite `data/state/state.db` **inside the repo dir** (`config.db_path()`, override `ORCHESTRATOR_DB_PATH`). |

Backend lifecycle (verified): `lifespan` startup calls `initialise()` reading the **local** DB + starts `SnapshotLoop`
(periodic GCS/S3 push); graceful shutdown takes a final `snapshot_session(reason="shutdown")`. **There is NO
auto-restore from GCS/S3 on boot** — `scripts/restore_from_gcs.sh` is manual-only. So a GHA "fresh checkout + restart"
loses state unless the state dir survives the restart. Hard-kill/OOM also skips the shutdown snapshot (the
api_host_chronic_impairment note shows OOM restarts happen) → you fall back to the last periodic snapshot.

- [ ] [DESIGN] P0. Pick the durability model and document it: **(a)** persistent volume — point `ORCHESTRATOR_DB_PATH`
      at a mounted disk that survives GHA restarts (durable, not "stateless" but restart-safe); **or (b)** auto-restore
      on boot — `lifespan` pulls the latest GCS/S3 snapshot when the local DB is absent/older (true stateless compute,
      externalized state). (b) is the genuine "stateless backend".
- [ ] [SCRIPT] P0. Implement the chosen model. If (b): add boot-restore to `lifespan` before `initialise()` + tighten
      the periodic snapshot interval so the RPO on a hard-kill is bounded; add a test that a fresh DB dir boots from a
      seeded snapshot.
- [ ] [DESIGN] P1. Audit remaining in-process state (`_state` dict, the loop threads) for anything not reconstructable
      from the DB on restart — confirm all server-lifetime state rehydrates from SQLite.

### G6 — staging branch + main-triggered CICD for agent-orchestrator [P0] _(operator decision 2026-06-02)_

- [ ] [INFRA] P0. Create the `staging` branch for agent-orchestrator and wire `quickmerge.sh` (PR base = staging) + a
      `staging-to-main` SIT gate, mirroring the trading-repo flow. Removes the old `main`-direct exception.
- [ ] [INFRA] P0. Add the merge-to-`main` CICD trigger: rebuild dashboard, update Firestore (if used by the deploy),
      GHA-restart the backends. **Depends on G5** — do not flip on the auto-restart until the backend is restart-safe.

## Related open work (NOT absorbed here)

The archived `orchestrator_autonomy_audit_remediation_2026_06_01` left **F1/F2/FM3** open (running VM behind LDR HEAD;
vm-ml SSM-degraded/now-stopped; foreign-repo playwright-report still tracked). These are tracked in
[issues/orchestrator_autonomy_residual_findings_2026_06_02.md](issues/orchestrator_autonomy_residual_findings_2026_06_02.md)
— owned there, referenced here so the e2e picture is complete. Fleet is currently consolidated to **2 running VMs**
(vm-orchestrator + api-host); 9 epic VMs stopped.

## Full-execution criterion (PLAN_FORMAT §8)

- `execution_scope` (two values: `orchestrator-agent | local-only`) is in PLAN_FORMAT.md, honoured by
  `regen_backlog_from_plan.py` (test proves a `local-only` plan is skipped), and the 3 local-only docs are stamped.
- G2: `DEFAULT_PLAN_REGEN_INTERVAL_SECONDS` lowered to ≤ 1800 (30 min) with the test updated.
- G5: backend durability model chosen + implemented; a fresh state dir restart preserves state (test proves it).
- G6: `staging` branch exists, quickmerge→staging→SIT→main wired, and the main→CICD trigger is live (gated on G5).
- `e2e_demo.py` passes locally with the result captured.
- G3 reconciliation is closed in the context-hygiene plan (cross-checked, not duplicated).
