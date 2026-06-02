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

- [x] ✅ [DESIGN] P0. Added `execution_scope: orchestrator-agent | local-only` to PLAN_FORMAT.md frontmatter schema (two
      values only — no `hybrid`). Absent ⇒ `orchestrator-agent` (backward-compatible, no backfill). — unified-trading-pm
      (PLAN_FORMAT.md § YAML Frontmatter Schema)
- [x] ✅ [SCRIPT] P0. Wired into `agent-orchestrator/server/regen_backlog_from_plan.py`
      (`_parse_frontmatter_execution_scope` → unconditional skip on `local-only`, before the per-VM filter). 4 unit
      tests (parse default/local-only/no-frontmatter + `test_regen_skips_local_only_plans`); pytest 60 passed, check.sh
      green. — agent-orchestrator@e21bd41
- [x] ✅ [DOC] P1. The 3 local-only plans are stamped (verified); field documented in
      `codex/04-architecture/agent-orchestrator-overview.md` § "Backlog auto-generation". — unified-trading-pm

### G2 — discovery latency [P0] _(Harsh-owned)_

**Verified 2026-06-02:** `DEFAULT_PLAN_REGEN_INTERVAL_SECONDS = 21600` (**6h**) at
`server/regen_backlog_from_plan.py:602` — the long default IS what runs unless the env overrides it (no prod override
confirmed). 6h is far too much latency: plans are authored continuously, so backlog discovery lags up to 6h.

- [x] ✅ [SCRIPT] P0. Lowered `DEFAULT_PLAN_REGEN_INTERVAL_SECONDS` 21600(6h) → **1800 (30 min)** in
      `server/regen_backlog_from_plan.py`; docstrings updated + comment decoupled from the SQLite-backup cadence. This
      was a code-vs-doc drift — the codex overview already documented `default 1800`.
      `test_default_regen_interval_is_at_most_30min` added. — agent-orchestrator@e21bd41
- [ ] [DESIGN] P1. _(stretch, optional)_ Near-instant ack. The `POST /api/backlog/regen` endpoint **already exists**
      (`server/server.py:1581`, AUTHED) — what's missing is a post-push GHA hook in unified-trading-pm that calls it on
      `plans/active/*.md` changes. Deferred: it needs a GHA→central-orchestrator auth token (the operator JWT /
      internal-secret) wired as a repo secret — a small auth/secrets task, not required given the 30-min floor from the
      G2 default + the 5-min `pm-pull` (effective ≤30 min today).

### G3 — merge-flow doc drift [P0] _(fix lives in the context-hygiene plan)_

- [ ] [DOC] P0. The live staging-first quickmerge flow contradicts the rules fed to agents
      (`.claude/rules/workspace-workflow.md` "staging = breaking changes"; `cursor-configs/CLAUDE.md` "quickmerge for
      promotion-to-main" / "DO NOT quickmerge dirty deps → push LDR"). Reconcile to the live model + the LDR dual-path.
      Tracked as instance (e) in
      [agent_context_and_memory_hygiene_2026_06_02.md](agent_context_and_memory_hygiene_2026_06_02.md) Phase 3 — fix
      there, do not duplicate.

### G4 — prove the loop end-to-end [P1]

- [x] ✅ [TEST] P1. Ran both locally (slot-2, mock mode, 2026-06-02). **Both PASS** after fixing 3 harness/script bugs
      found in the process. — agent-orchestrator@ae798f7
  - **e2e_demo.py → EXIT 0, "ALL CHECKS PASSED"**: full lifecycle verified — boot→B-001 dispatch, gating (slot 3 idle),
    progress, blocked→escalate→answer→deliver, done+verify, condition-set unblocks B-002/B-003, auto-dispatch, and the
    critical **stop+resume** (both in-progress tasks preserved across SIGTERM+restart) + shutdown snapshot + activity
    log intact.
  - **dev.sh --mock → ready in 9s**, backend `/api/healthz` 200, dashboard 200 (`<title>Orchestrator</title>` +
    `<div id="root">`, vite entry compiles). Dashboard renders.
  - **Gaps found + fixed (the orchestrator itself was correct — these were stale script paths):**
    1. `e2e_demo.py` started the server in live mode → read the real 86-task `backlog.yaml` instead of the demo
       `backlog.mock.yaml` (B-001..B-003 absent) → first assertion failed. Fixed: force `ORCHESTRATOR_MODE=mock` in the
       server subprocess (self-contained).
    2. `e2e_demo.py` checked `REPO_ROOT/state.json` + cleaned `REPO_ROOT/state.db` — stale paths predating the
       `data/state/` + `.mock.` layout (the snapshot really lands at `data/state/state.mock.json`). Fixed to
       config-accurate paths.
    3. `dev.sh` readiness probe hit bare `/healthz` (404 — server registers `/api/healthz`, prefixed to dodge Knative's
       reservation) → dev.sh **always** timed out at 30s and tore down a healthy stack. Fixed the probe + the summary
       echo.

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

- [x] ✅ [SCRIPT] P0. DB + state.json moved off the repo checkout to **`/var/lib/orchestrator/`** via
      `ORCHESTRATOR_DB_PATH` + `ORCHESTRATOR_STATE_JSON` in the systemd unit (+ `ReadWritePaths=/var/lib/orchestrator`
      under `ProtectSystem=strict`); `bootstrap_vm.sh` creates+chowns the dir and does an **idempotent one-time move**
      of any existing in-repo `data/state/state.db` (+wal/shm/json). A redeploy can no longer wipe state. —
      agent-orchestrator@ff4fc23
- [x] ✅ [SCRIPT] P0. Pre-restart flush hardened: `TimeoutStopSec` **30 → 90** so the lifespan shutdown snapshot (which
      IS the pre-restart flush — `snapshot_session(reason="shutdown")`) completes even on a slow GCS/S3 upload. No
      `ExecStop` curl hook added — it would need the `/api/snapshot` auth token, and it's redundant now that the DB is
      persistent (a truncated snapshot only stales the DR archive, never live state). — agent-orchestrator@ff4fc23
- [x] ✅ [DESIGN] P1. OOM/hard-kill RPO: the periodic snapshot is already `ORCHESTRATOR_SNAPSHOT_INTERVAL_SECONDS=1800`
      (30 min) in the unit — that bounds the **DR-archive** staleness; the **live** RPO is now ~0 because the WAL DB
      sits on the persistent path and survives the kill. `_state` + loop-state rehydration from SQLite on boot is
      **proven by e2e_demo step 12** (stop+resume returns both in-progress tasks). No interval change needed.
- **Downstream-consumer fixes found during G5 (SSOT consistency for the moved path):**
  - `restore_from_gcs.sh` — defaulted to `${REPO_ROOT}/data/state.db` (wrong: missed the `/state/` subdir) and read a
    typo'd `ORCHESTRATOR_STATE_JSON_PATH` env var (never took effect). Now defaults to `/var/lib/orchestrator/` and
    reads the correct `ORCHESTRATOR_STATE_JSON`.
  - `gcs_sync.commit_state_to_git` — would have poisoned its `git add` with the out-of-repo state.json path; now skips
    any path outside `repo_root` (state.json is covered by the DB + GCS/S3 snapshot).

**Scope = code only (operator decision 2026-06-02).** Applies on the next bootstrap/deploy; the 2 live VMs migrate via
the idempotent one-time move in `bootstrap_vm.sh` when re-bootstrapped. e2e_demo regression green; check.sh green.

### G6 — staging branch + CICD for agent-orchestrator [P0] _(operator decision 2026-06-02)_

**Verified 2026-06-02:** agent-orchestrator already has `quality-gates-v2.yml` (canonical; triggers push/PR to
`[main, staging]`, calls PM's reusable `python-quality-gates-v2.yml`) **and** a `dispatch-cloud-build` job that fires
`qg-passed` → PM `cloud-build-router.yml` on **staging** push. So the CI + cloud-build trigger already exist — what's
missing is the **`staging` branch itself** + the v1-ghost cleanup. Its local gate is **`scripts/check.sh`** (no
`scripts/quickmerge.sh`/`quality-gates.sh` — it is not a uv service repo).

**Access + safety reality (verified 2026-06-02, corrected):** with `GH_PAT` the session IS repo **admin** (owner
`IggyIkenna`) — the earlier "push-only/not-admin" note was a wrong-token error (keyring `gho_` is push-only, `GH_PAT` is
admin). The real branch-protection blocker is a **GitHub billing/feature gate**, not access: branch-protection +
rulesets return `403 "Upgrade to GitHub Pro or make this repository public"` for **agent-orchestrator specifically**.
Every sibling repo (unified-trading-pm, execution-service, deployment-ui, alerting-service…) HAS active rulesets —
grandfathered from the v2-migration tooling during a paid-plan window that **deliberately skipped agent-orchestrator**
(the codified `main`-direct operator-tooling exception). It never got a ruleset and the feature is now gated for
creating one. The v2 **workflow already runs** on agent-orchestrator main/staging — only the _required-check
enforcement_ is missing. Also: creating `staging` or pushing to `main` fires the deploy path (`dispatch-cloud-build` on
staging; main→`cloud-build-router`) which **restarts the fleet backends** — out of bounds until the operator
green-lights a deploy (2026-06-02 directive: "don't restart the running backends").

- [x] ✅ [INFRA] P0. Deleted the stale v1 ghost workflows on LDR (`quality-gates.yml`, `workspace-qg.yml`).
      `workspace-     qg.yml` had still been triggering on every `live-defi-rollout` push (wasted runs); neither carries
      a cloud-build dispatch so removal triggers no deploy. — agent-orchestrator@0249a83
- [ ] [INFRA] P0. **BLOCKED-OPERATOR** — remove the v1 ghosts from `main` too + create the `staging` branch +
      `staging-to-main` SIT gate. Both actions trigger CICD → a fleet backend **restart**, so they wait for the operator
      to green-light a deploy. (LDR-side deletion above promotes to main on that same deploy.)
- [ ] [INFRA] P0. **BLOCKED-BILLING** — pin branch protection to require
      `Quality Gates (agent-orchestrator) /     quality-gates-v2`. Not an access problem (session is admin via
      `GH_PAT`); GitHub **feature-gates** rulesets + branch-protection for this repo (`403 upgrade-to-Pro`), the only
      repo of the set so gated. Resolve by ONE of: (a) upgrade the GitHub plan (Pro/Team) so a ruleset can be created
      here, (b) make the repo public (rulesets free for public), or (c) accept "v2 runs but isn't a hard-required gate"
      (operator tooling). Operator/billing decision.
- [x] ✅ [INFRA] P0. merge→CICD restart path confirmed wired: `quality-gates-v2.yml` `dispatch-cloud-build` (staging) +
      main→`cloud-build-router`→`uts-prod`. **Now safe w.r.t. state** since G5 moved the DB off the repo checkout — a
      deploy/restart no longer risks state. Actual enablement = the operator's deploy green-light (above).

### G7 — reconcile agent boot prompts to the staging-first quickmerge + v2 flow [P0] _(operator-raised 2026-06-02)_

The boot prompts every spawned agent reads (`agent-orchestrator/agents/*.md`) already reference a "v2 quality-gate
flow" + `quickmerge --agent`, but they carry the **same staging-vs-LDR drift as G3** (verified against
`scripts/quickmerge.sh`, which is staging-first: all human commits → PR base `staging`; `--to-staging` is a no-op):

- [x] ✅ [DOC] P0. `agents/worker.md:217` — fixed: quickmerge PR base is **`staging` for every human commit** (was
      "auto-merge to live-defi-rollout; staging where the fast-path applies"). Now states staging-first → SIT → main +
      names the `…/quality-gates-v2` check. — agent-orchestrator@33b1057
- [x] ✅ [DOC] P0. `agents/worker.md:218` — fixed: `--to-staging` documented as a **no-op** (was "use only if the task
      brief says so"). — agent-orchestrator@33b1057
- [x] ✅ [DOC] P1. `agents/RULES.md:52-67` ship-cadence block — fixed: Pass-2 comment now names the `staging` base +
      `--to-staging` no-op + v2 required check; sentinel two-pass kept. — agent-orchestrator@33b1057
- [ ] [DOC] P1. Clarify the **operator-tooling exception** (`worker.md:228`): agent-orchestrator's own gate is
      `scripts/check.sh` (correct, verified) — but once G6 lands its `staging` flow, document whether agents working
      _inside_ agent-orchestrator ship via `check.sh` + reviewed direct push or via the new staging PR path.
- [ ] [DOC] P1. Note that "v2" = the CI required-check rename (`…/quality-gates-v2`, migration COMPLETE 2026-06-02,
      17/17 repos); the LOCAL two-pass commands (`scripts/quality-gates.sh` → `quickmerge.sh --agent`) are unchanged —
      so no command edits are needed, only the target-branch + `--to-staging` corrections. Cross-link G3 (do not
      duplicate the rules-file fix that lives in the context-hygiene plan).

### G8 — worker boot-context de-bloat (executor-minimal context) [P0] _(Harsh 2026-06-02; verified)_

Distinct from G7 (which fixes the **merge-flow** wording in the prompts): this is the **context bloat / duplication**.
Verified worker boot context (orchestrator-spawned, before any work) ≈ **138 KB**: auto-loaded `CLAUDE.md` SSOT (84 KB,
via each repo's `.claude/CLAUDE.md → cursor-configs/CLAUDE.md`) + `.claude/rules/*.md` (14 KB) + the injected
`agents/worker.md` (24 KB) + `agents/RULES.md` it is told to read (16 KB). **Workers do NOT get `MEMORY.md`** — the
auto-memory folder is operator-local (our machine), not on the VMs; workers are **executors** and don't need our full
operator context (governance / planning / master-plan / model-tier rules).

- **Duplication:** `worker.md` + `RULES.md` **restate** workspace CLAUDE.md rules (quickmerge ×8, basedpyright ×4,
  conventional-commits ×3) — workers get them twice (auto-loaded CLAUDE.md + re-stated in the prompt). RULES.md calls
  itself "the slim replacement for AGENT_ONBOARDING.md + CLAUDE.md" but CLAUDE.md still auto-loads via the repo
  `.claude/CLAUDE.md` symlink → it doesn't replace, it doubles.
- **Competing rules SSOTs:** `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (180 L; CLAUDE.md says "paste via
  inject-mandatory-rules.sh") vs `agents/RULES.md` (355 L; what the spawn actually uses) — two drifting docs.
- **Stale paths:** `worker.md:114` `WORKSPACE_ROOT:-/home/ubuntu/...`; `RULES.md` `cat /home/hk/...SUB_AGENT...`.
- **CLAUDE.md double-load — RESOLVED (not a real bloat source):** Claude Code de-duplicates auto-loaded context by
  **resolved path**, so the same physical `cursor-configs/CLAUDE.md` reached via two symlinks (`<repo>/.claude/CLAUDE.md`
  + workspace `.claude/rules/CLAUDE.md`) loads ONCE. On the **VM** (where workers run) only the repo symlink path exists
  — there is no workspace `.claude/rules` there — so a single load regardless. The real duplication is **content**:
  `RULES.md`/`worker.md` restating CLAUDE.md's rules as different prose (a true second copy) → fixed by slimming, below.

- [x] ✅ [SCRIPT] P0. Added `.claude/CLAUDE.md` + `.claude/SUB_AGENT_MANDATORY_RULES.md` symlinks (→
      `../../unified-trading-pm/cursor-configs/...`) to the 2-of-3 repos that lacked them: **agent-orchestrator** (`.claude/`
      was gitignored wholesale → un-ignored the 2 SSOT symlinks) + **ml-service**. Now all 22 service repos match the
      pattern; AO agents auto-load CLAUDE.md instead of relying on RULES.md restating it. VMs get them via clone/worktree
      (PM is a sibling; `setup-tab-worktrees.sh` checks them out as tracked files — no bootstrap edit needed). —
      agent-orchestrator@bf85d21 + ml-service@f17f13e
- [x] ✅ [DESIGN] P0. **Slimmed `RULES.md` to worker-lifecycle-only** (option a): 357 → 233 L — stripped the
      generic-rule restatements (the 8 code rules / QG entrypoint / git discipline / findings-triage, all now auto-loaded
      via the `.claude/CLAUDE.md` symlink); kept worker-lifecycle-unique content (worktree scope, the server-verified
      ship→flip→`/done` loop incl. M3 cross-repo verification, sub-agent spawning, the backlog/HTTP API surface); §6 now
      points to the CLAUDE.md sections instead of duplicating. **RULES.md vs SUB_AGENT_MANDATORY_RULES.md stay separate**
      (justified: RULES.md = worker-lifecycle boot prompt; SUB_AGENT = the paste-into-`Task()` sub-agent ruleset — distinct
      audiences, not a dup). Also de-staled the CLAUDE.md AO branch-model exception (transitional, cross-links G6). —
      agent-orchestrator@41cb2a5 + unified-trading-pm@b811b4232
- [x] ✅ [SCRIPT] P1. Fixed stale paths: `worker.md:114` boot loop `WORKSPACE_ROOT` fallback `/home/ubuntu` → `$HOME`
      (workers run as the operator → correct base on any VM); `RULES.md` `cat /home/hk/…` → relative sibling path (prior
      session). Also exported `WORKSPACE_ROOT` in `bootstrap_vm.sh` (.env.local → systemd → tmux workers + operator
      .bashrc/.profile, mirroring GH_TOKEN) so the fallback is a safety net not the primary. — agent-orchestrator@41cb2a5
- [x] ✅ [SCRIPT] P1. CLAUDE.md double-load — **RESOLVED as not-a-real-issue** (see finding above): CC de-dups by resolved
      path, and the VM has only the single repo-symlink path. The real dup was content (RULES.md restating CLAUDE.md),
      fixed by the slim. — analysis, no code change needed.

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
