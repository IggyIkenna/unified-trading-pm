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

Backend lifecycle (verified 2026-06-02 by code trace):

- **Source of truth = the local SQLite DB.** `lifespan` startup → `initialise()` (`server/bootstrap.py:177`) opens the
  **local** DB + syncs backlog/accounts YAML into it; starts `SnapshotLoop` (periodic GCS/S3 push). **No auto-restore
  from GCS/S3 on boot** — `scripts/restore_from_gcs.sh` is manual-only. GCS/S3 = disaster-recovery archive, not the live
  store.
- **In-flight writes are durable.** Every tx is `BEGIN IMMEDIATE` + WAL (`server/db.py:18,30`); `/done` commits inside
  `session_scope()` before responding → a crash mid-`/done` keeps the committed row. Only the in-memory `_state` dict +
  loop-thread state is lost on crash, and it all rehydrates from SQLite/YAML on boot.
- **Pre-restart flush exists but is not crash-proof.** Graceful shutdown calls `snapshot_session(reason="shutdown")`
  (`server/server.py:286`); systemd `orchestrator.service` sends SIGTERM with `TimeoutStopSec=30`. A slow GCS upload can
  exceed 30s → SIGKILL truncates it; an OOM (`MemoryMax=56G`) skips it entirely → fall back to the last periodic
  snapshot.

**VM-volume correction (the operator's question):** these are **long-running VMs**, so a normal `systemctl restart`
keeps `data/state/state.db` (the repo checkout persists — no data loss on restart). The real exposure is a
**code-redeploy that re-checks-out / cleans the repo dir**, or a fresh VM: `state.db` lives **inside the repo checkout**
(`STATE_DIR = REPO_ROOT/data/state`, `server/config.py:46`; `bootstrap_vm.sh` never sets `ORCHESTRATOR_DB_PATH`; the
systemd unit's `WorkingDirectory` + `ReadWritePaths` point inside the repo). The correction: **relocate the DB outside
the repo checkout** (`ORCHESTRATOR_DB_PATH=/var/lib/orchestrator/state.db` on a persistent path) so a GHA code redeploy
can never touch it — this is what makes the "update code → restart backend" CICD model (G6) safe on a long-running VM.

Operator steer 2026-06-02: keep **local SQLite as the live source of truth** (long-running VMs) + add a **pre-restart
flush** so no data is lost on deploy/restart, rather than going full GCS-restore-on-boot.

- [ ] [SCRIPT] P0. Move the live DB off the repo checkout: set `ORCHESTRATOR_DB_PATH` to a persistent path
      (`/var/lib/orchestrator/state.db`) in `bootstrap_vm.sh` + the systemd unit (`ReadWritePaths` + a one-time migrate
      of the existing DB). A code redeploy then cannot wipe state.
- [ ] [SCRIPT] P0. Harden the pre-restart flush: add an explicit `flush+snapshot` step the deploy/restart path calls
      BEFORE sending SIGTERM (e.g. `POST /api/admin/snapshot` or a systemd `ExecStop=` pre-hook), and raise
      `TimeoutStopSec` enough for the snapshot to finish. Goal: zero data loss on a planned restart even if the GCS
      upload is slow.
- [ ] [DESIGN] P1. OOM/hard-kill RPO: tighten the periodic `SnapshotLoop` interval (or WAL-checkpoint cadence) so an
      unplanned kill loses at most a bounded window. Confirm `_state` + loop state fully rehydrate from SQLite on boot
      (already true by trace — add a restart test that asserts it).

### G6 — staging branch + CICD for agent-orchestrator [P0] _(operator decision 2026-06-02)_

**Verified 2026-06-02:** agent-orchestrator already has `quality-gates-v2.yml` (canonical; triggers push/PR to
`[main, staging]`, calls PM's reusable `python-quality-gates-v2.yml`) **and** a `dispatch-cloud-build` job that fires
`qg-passed` → PM `cloud-build-router.yml` on **staging** push. So the CI + cloud-build trigger already exist — what's
missing is the **`staging` branch itself** + the v1-ghost cleanup. Its local gate is **`scripts/check.sh`** (no
`scripts/quickmerge.sh`/`quality-gates.sh` — it is not a uv service repo).

- [ ] [INFRA] P0. Create the `staging` branch for agent-orchestrator + a `staging-to-main` SIT/promotion gate mirroring
      the trading-repo flow. Removes the old `main`-direct exception. (Quickmerge in the trading repos is already
      staging-first — PR base = staging, `--to-staging` is a no-op — see G3/G7.)
- [ ] [INFRA] P0. Delete the stale v1 ghost workflows still present in agent-orchestrator (`quality-gates.yml`,
      `workspace-qg.yml`) — the v2 migration removed these from every other repo (deployment-ui done 2026-06-02). Pin
      branch protection to require `Quality Gates (agent-orchestrator) / quality-gates-v2`.
- [ ] [INFRA] P0. Confirm the merge→CICD restart path: dashboard rebuild + GHA-restart of the backend on deploy.
      **Depends on G5** — do not enable the auto-restart until the DB is off the repo checkout + the pre-restart flush
      is in place, or a deploy could wipe/lose state.

### G7 — reconcile agent boot prompts to the staging-first quickmerge + v2 flow [P0] _(operator-raised 2026-06-02)_

The boot prompts every spawned agent reads (`agent-orchestrator/agents/*.md`) already reference a "v2 quality-gate
flow" + `quickmerge --agent`, but they carry the **same staging-vs-LDR drift as G3** (verified against
`scripts/quickmerge.sh`, which is staging-first: all human commits → PR base `staging`; `--to-staging` is a no-op):

- [ ] [DOC] P0. `agents/worker.md:217` — "auto-merge to the target branch (live-defi-rollout; staging where the
      fast-path applies)" is wrong: quickmerge PR base is **`staging` for every human commit**. Fix to state the two
      axes clearly: raw `tab/<op>/<N>` → push **LDR** = continuous-integration (no PR, no remote CI);
      `quickmerge --agent` = the promotion step that opens a **PR to `staging`** → SIT → main.
- [ ] [DOC] P0. `agents/worker.md:218` — "Use `--to-staging` only if the task brief says so" is wrong: `--to-staging` is
      a **no-op** (everything already routes to staging). Remove the conditional.
- [ ] [DOC] P1. `agents/RULES.md:52-67` ship-cadence block — same reconciliation; keep the `.qg_last_passed_sha`
      sentinel two-pass (correct) but fix any "quickmerge → LDR" implication.
- [ ] [DOC] P1. Clarify the **operator-tooling exception** (`worker.md:228`): agent-orchestrator's own gate is
      `scripts/check.sh` (correct, verified) — but once G6 lands its `staging` flow, document whether agents working
      _inside_ agent-orchestrator ship via `check.sh` + reviewed direct push or via the new staging PR path.
- [ ] [DOC] P1. Note that "v2" = the CI required-check rename (`…/quality-gates-v2`, migration COMPLETE 2026-06-02,
      17/17 repos); the LOCAL two-pass commands (`scripts/quality-gates.sh` → `quickmerge.sh --agent`) are unchanged —
      so no command edits are needed, only the target-branch + `--to-staging` corrections. Cross-link G3 (do not
      duplicate the rules-file fix that lives in the context-hygiene plan).

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
- G5: DB relocated off the repo checkout (`ORCHESTRATOR_DB_PATH` persistent) + pre-restart flush hardened; a restart
  loses zero state (test proves it) and local SQLite stays the live source of truth.
- G6: `staging` branch exists, v1 ghost workflows deleted, branch protection requires `…/quality-gates-v2`, and the
  merge→CICD restart path is confirmed safe (gated on G5).
- G7: boot prompts corrected — quickmerge target is `staging` (not LDR), `--to-staging` documented as a no-op.
- `e2e_demo.py` passes locally with the result captured.
- G3 reconciliation is closed in the context-hygiene plan (cross-checked, not duplicated).
