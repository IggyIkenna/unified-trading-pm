---
title: Orchestrator fleet worker-spawn enablement (FM7 operator-mismatch + autospawn + VM_ID + worktree hygiene)
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P0
status: archived
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-02
locked_by: live-defi-rollout
related_plans:
  - plans/active/agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md
  - plans/epics/orchestrator_master.md
---

> **✅ ARCHIVED 2026-06-07 [unlock-plan].** All checkbox todos complete (0 open): F8/F9 self-heal+review-spawn done; F12
> fleet env; F13 worktree-hygiene RESOLVED (git object-store corruption fixed); F6 pm-pull baked into `bootstrap_vm.sh`
> (`agent-orchestrator@402fbc3`); the positive "picking up CI work" Slack alert was already shipped + wired
> (`server/server.py:729-739` → `notify_work_picked_up`).
>
> ## Deferred work — migrated to:
>
> - **F7 — slot-4 WIP recovery on vm-0** (BLOCKED-INFRA: live-host WIP judgment — unmerged WIP on uac/pm feature
>   branches, recreate `tab/vm-0/4`) → `plans/epics/orchestrator_master.md` § "P2 — useful; opportunistic".

# Orchestrator fleet worker-spawn enablement

## Context

The 2026-06-02 e2e pipeline test proved the **discovery half** works end-to-end (push plan → `pm-pull` → `PlanRegenLoop`
→ backlog), but **no VM in the fleet can currently spawn a worker** — so the execution half (dispatch → worker → flip →
push) never runs. Diagnosed live across the central, `vm-orchestrator`, a freshly-started epic VM, **and reproduced +
validated on the local orchestrator** (`agent-orchestrator.service` on `:8026`). This plan captures the reproduced root
causes and the exact per-host / per-VM changes to apply when the VMs are started.

`execution_scope: local-only` — this is operator/host bootstrap work (chicken-and-egg: the orchestrator cannot spawn a
worker to fix its own spawn path), so it must NOT be ingested by the fleet backlog.

## Root causes (reproduced 2026-06-02, local orchestrator)

### RC1 — branch operator is derived from the Claude ACCOUNT, not the worktree/host (PRIMARY)

`tab/<operator>/<N>` identifies the **host** that owns the slot worktrees. But the spawn path derives the operator from
the **account**:

- `server/autospawn.py:210` → `operator = account.operator or slot.operator or "ikenna"`
- `server/server.py` spawn endpoint → `spawn_operator = acc_def.operator`

The pre-spawn FM7 gate (`worktree_clean_check.check_slot_branch_state`) then asserts every repo's HEAD ==
`tab/{operator}/{slot_id}`. When the account's operator (`harsh` / `ikenna`) ≠ the host's worktree operator (`hk` /
`hkm` locally; `rootm` / `ikennaigboaka` on the VMs), **every repo trips `wrong_branch` (FM7) → STOP → no spawn.** This
is why autospawn logs `spawn failed … branch-state quarantine (FM5/FM7)` on the central, and why a shared/cross-operator
account can never spawn.

**Reproduced (local, slot 21 on `tab/hk/21`):**

| operator passed | source                  | gate result                                                              |
| --------------- | ----------------------- | ------------------------------------------------------------------------ |
| `harsh`         | `harsh-primary` account | should_stop=True, **25/25 repos wrong_branch** (`expected tab/harsh/21`) |
| `ikenna`        | sub-\* accounts         | should_stop=True, 25/25 wrong_branch                                     |
| `hk`            | the actual worktree     | passes the operator check (then only the RC4 staleness remained)         |

**Proven green case (local, slot 1 on `tab/hkm/1`, operator `hkm`):** `should_stop=False`, **all 23 repos `ff_done`** —
a worker WOULD spawn. This is the success target.

### RC2 — per-VM `ORCHESTRATOR_VM_ID` is `unknown-vm` (assigned_vm routing broken)

The epic VMs and `vm-orchestrator` report `ORCHESTRATOR_VM_ID=unknown-vm` instead of their canonical id (`vm-cefi`,
`vm-defi`, …). So `assigned_vm:`-routed plans never reach the right VM (only global plans do), and multiple VMs sharing
`unknown-vm` collide on the same global tasks. (The central correctly reports `vm-0`.)

### RC3 — autospawn defaults OFF

`ORCHESTRATOR_AUTOSPAWN_ENABLED` defaults to false (`server/autospawn.py:18,338`; boot logs `AutoSpawnLoop disabled`).
`vm-orchestrator` and the local host have it unset → even a correctly-configured slot never auto-spawns. (The central
had it `true`, which is why it was _attempting_ spawns and failing on RC1.)

### RC4 — stale + dirty slot worktrees block the FF/branch-state gate

Even with the correct operator, slots fail if worktrees are behind upstream with uncommitted local changes (local slot
21: `behind 231 but ff-only merge failed: local changes would be overwritten`) or have stray repos left on the base
branch (local slot 2: 2 of 23 repos on `live-defi-rollout` instead of `tab/hkm/2`). The `slot-cron-ff-pull` must keep
them clean + current; dirty WIP must be committed/stashed (never blind-discarded — inherited-WIP rule).

### RC5 — operator naming is inconsistent within a host

A single host should have ONE operator. Locally worktrees mix `hk` (slots 21–28) and `hkm` (slots 1–2); VMs use `rootm`
and `ikennaigboaka`. Standardize one operator per host and brand all that host's worktrees `tab/<operator>/<N>`.

## Fixes

### F1 — code: decouple the branch operator from the account [P0]

The branch operator must come from the host/slot, not the Claude account (which is only for auth). Recommended:

- Resolve operator as
  `slot.operator or ORCHESTRATOR_OPERATOR (host env) or <derive from worktree HEAD> or account.operator` — i.e.,
  **prefer the worktree/host operator; account.operator becomes the last resort**. Apply in BOTH `autospawn.py:210` and
  the `server.py` spawn endpoint (`spawn_operator`).
- Populate `slot.operator` at slot-registration/bootstrap time from the `--operator` used to create the worktrees, so it
  is never `None`.
- Keep FM7 as-is (it correctly verifies all repos share `tab/<operator>/<N>`); only the _source_ of `operator` changes.

Blast radius: this gate runs on every spawn fleet-wide → land behind `scripts/check.sh` + a unit test that asserts a
worktree on `tab/hk/N` spawns under account `harsh-primary` (operator `harsh`). Owner: agent-orchestrator (sole-owned).

- [x] ✅ [SCRIPT] P0. **DONE — agent-orchestrator@cfece08.** Added `config.host_operator()` (resolution:
      `ORCHESTRATOR_OPERATOR` > `ORCHESTRATOR_VM_ID` > `slot.operator` > OS-user > `account.operator`); wired into
      `autospawn.py:210` + `server.py` spawn endpoint (`spawn_operator`). 7 unit tests (`tests/test_host_operator.py`);
      ruff + basedpyright `server/` 0/0 green (tsc N/A — server-only change). **Validated live**: with the fix the
      resolver returns `hk` (the host) not `harsh` (the account), and slot 21's FM7 `wrong_branch` count dropped **25/25
      → 0/25** — RC1 fixed. Note: `slot.operator` bootstrap-population was NOT needed (the `VM_ID`/OS-user fallback
      covers a `None` slot.operator), so it's dropped from scope rather than deferred.

### F2 — per-VM config: fix `ORCHESTRATOR_VM_ID` [P0]

- [x] ✅ [INFRA] P0. **Baked into the scripts + validated.** `bootstrap_vm.sh` (agent-orchestrator@129dc6a) now UPSERTs
      `ORCHESTRATOR_VM_ID` from the launcher's short canonical id (fixes stale `unknown-vm`); the launchers
      (deployment-service@eaccd8d) `export ORCHESTRATOR_VM_ID=${vm_id}` into bootstrap's env (AWS + GCP). **Verified on
      vm-cefi** (VM_ID set, regen ingested the test plan). **Per-VM fleet rollout** to the 9 stopped epic VMs +
      vm-orchestrator is automatic on each VM's next re-bootstrap — pending because the fleet is intentionally OFF
      (operator). Existing stopped VMs need a re-bootstrap (or the manual upsert I did on vm-cefi) to clear their stale
      `unknown-vm`.

### F3 — per-host config: enable autospawn [P0]

- [x] ✅ [INFRA] P0. `bootstrap_vm.sh` now upserts `ORCHESTRATOR_AUTOSPAWN_ENABLED=true` (@129dc6a). Epic VMs already
      had it `true` (systemd) — `vm-orchestrator` + the local host were the only gaps. Confirmed live:
      `AutoSpawnLoop started` then `spawned=2 failed=0` on vm-cefi (was `failed=8` FM7-quarantine before the fix).

### F4 — worktree hygiene + operator standardization [P0]

- [x] ✅ [INFRA] P0. `bootstrap_vm.sh` brands ALL slot worktrees uniformly `tab/<VM_ID>/<slot>`
      (`MAIN_PREFIX=WORKER_PREFIX=VM_ID`, dropping the `+m` main/worker split) so they match `host_operator()==VM_ID`
      (@129dc6a). **Validated on vm-cefi**: rebranded `tab/rootm/N → tab/vm-cefi/N`, gate `should_stop=False` (20 ok / 1
      ff_done). Per-VM rebrand auto-applies on re-bootstrap; the FF/clean part is handled by the existing
      `slot-cron-ff-pull` + the gate's FF-repair (unchanged).

### F5 — validation gate [P0]

- [x] ✅ [INFRA] P0. **Validated end-to-end on vm-cefi 2026-06-02.** Gate `should_stop=False` (slot 1); autospawn
      `spawned=2 failed=0`; a worker completed the FULL loop — execute → flip checkbox → push to LDR (`64901d5ef`).
      Discovery half independently confirmed (push → pm-pull → regen → backlog `vm_pipeline_e2e_test-001` queued). The
      local one-shot also pushed its marker (`5ab77fc0c`). Pipeline green discovery→execution. (Test plan removed +
      vm-cefi stopped afterward; the premature flip a worker made was reverted @de9644c7f.)

### F6 — pm-pull install on VMs [P1] _(MIGRATED FROM `plan_hygiene_silent_failure_capture_2026_05_29`)_

- [x] ✅ [SCRIPT] P1. **F6 — pm-pull baked into `bootstrap_vm.sh`** — DONE 2026-06-07 (`agent-orchestrator@402fbc3`,
      shipped to LDR; CI v2 gates on promotion). Added **Step 5.9** which calls the canonical idempotent
      `install_pm_pull.sh` (installs `/usr/local/bin/pm-pull-ff.sh` + `pm-pull.{service,timer}` pulling every 5 min +
      the 30-min regen-interval drop-in) for ALL roles, so a fresh/replacement VM is self-sufficient with no post-launch
      step. The "9 stopped epic VMs" sub-part is MOOT — the per-epic fleet is post-cutover/decommissioned (vm-0 is the
      sole live orchestrator; `i-007e8d99` terminated 2026-06-07). (Note: local Pass-1 QG showed a false-negative —
      local `.venv` missing `pexpect` which IS in AO pyproject+lock + present in CI; shell-only change is `bash -n`
      clean.)

### F9 — review-agent auto-spawn per VM (persistent-role keep-alive) [DONE]

- [x] ✅ [INFRA] P1. **DONE + deployed + verified-firing 2026-06-03 — agent-orchestrator@415ff06.** New
      `_ensure_review_agents` runs every tick BEFORE the queue early-exit and keeps the designated review slot(s) alive
      with the `review` boot prompt (queue-independent); `_should_spawn` now skips review slots (`reason="review_slot"`)
      so a worker is never dropped onto one. Review slots designated per-host via `ORCHESTRATOR_REVIEW_SLOTS`
      (`config.review_slot_ids()`; empty=off, back-compat) — no schema migration (`SlotRow` has no role column). Reuses
      the flap/cooldown/headroom + branch-state gate; `agents/review.md` already shipped. +10 unit tests;
      ruff/pyright 0. **Live-verified on vm-0** (`ORCHESTRATOR_REVIEW_SLOTS=2`, restart): the loop fired
      `AutoSpawnLoop: review agent spawn failed slot=2 … branch-state quarantine` — i.e. it ran queue-independently,
      picked slot 2, attempted the review-template spawn, and was correctly gated by the SAME branch-state guard as
      workers (slot 2's worktrees are dirty — F13). On a clean slot it spawns green. **Fleet rollout** = set
      `ORCHESTRATOR_REVIEW_SLOTS=2` in `bootstrap_vm.sh` (folds into F12's per-VM env work).

  _Original task (kept for context):_ **Operator-requested 2026-06-03 — half-built design, finish the wiring.** Per
  `codex/12-agent-workflow/orchestrator-multi-vm-topology.md:107` each epic VM = slot-1 **main** + slot-2 **review**
  (Sonnet 4.6) + N workers. The review agent reviews each worker commit against the plan + FF-merges slot branches →
  LDR. **Already shipped**: `agents/review.md` boot prompt + the `role` model (`orm.py:231` `main|review|backup|custom`;
  `worktree_claim.py`). **Gap**: `AutoSpawnLoop` (`server/autospawn.py`) ONLY spawns task-`worker`s — it early-exits on
  empty queue (`_run_one_tick:395`), renders `prompt_template="worker"`, and `_should_spawn:484` ignores role. So (a)
  nothing keeps a persistent review agent alive (it's commit-polling, not task-driven → never queue-triggered), and (b)
  AutoSpawn would wrongly drop a _worker_ onto the review slot. **Implement**: (1) `config.persistent_role_slots()`
  resolving review-role slots (SSOT = `SlotRow.role='review'`; bootstrap assigns slot-2 `role=review` per VM); (2) a
  queue-INDEPENDENT keep-alive pass in the tick (before the empty-queue early-exit) that spawns `template="review"` on
  any dead review-role slot (reuse the flap/cooldown + `_do_spawn(prompt_template=...)` machinery); (3) `_should_spawn`
  skips persistent-role slots in the worker loop (only `worker`/`custom`/None get task-workers). Unit tests: review slot
  stays alive with empty queue; worker never spawned on review slot. Then bootstrap role-assignment + VM deploy. Repo:
  agent-orchestrator. Forward-looking (fleet mostly stopped; review runs on vm-0 today, all epic VMs when on).

### F10 — CI conflict-resolution: capacity model (dedicated vs slot-on-existing) [P2]

- [x] ✅ [DESIGN] P2. **DECIDED 2026-06-07: keep the any-free-slot model (NO dedicated conflict-resolution VM).**
      Reserving a dedicated VM/slot adds idle cost + ops surface for a low-frequency event; the escalate→spawn path
      already lands on whatever VM has a free slot (today vm-0) with no new mechanism. Revisit ONLY if
      conflict-resolution is observed to starve epic work (it is not today). Original framing 2026-06-03: The
      CI→orchestrator→delegate path is BUILT this session (`conflict-resolution-agent.yml` / `ci_failure_watcher` /
      `main-backmerge-to-ldr` → `repository_dispatch     escalate-to-orchestrator` → orchestrator spawns a Max worker
      via `agents/escalate.md`). It spawns on whatever VM has a free slot (today vm-0). Decide whether to RESERVE a
      dedicated conflict-resolution VM/slot (guaranteed availability, isolation from epic work) vs the current
      any-free-slot model. No new mechanism either way — same escalate→spawn path; this is purely a capacity/pinning
      decision. Repo: agent-orchestrator (slot-role pin) + deployment-service (if a dedicated VM). Composes with F9
      (same persistent-role-slot machinery).

### F11 — "backlog won't clear" — diagnosed + fixed (3 root causes) [P1]

- [x] ✅ [SCRIPT] P1. **DONE 2026-06-03 — operator "clear the backlog on background VMs".** The yaml-prune was a red
      herring (it worked: 12 tasks = open checkboxes). The real backlog AutoSpawn dispatches from is `state.db`, which
      had **761 total / 304 QUEUED / 448 done** and never shrank. Three root causes, all fixed: 1.
      **`ORCHESTRATOR_REGEN_DB_PATH` was unset** → the loop's prune ran **yaml-only** (`pruned_db=0` every tick) →
      state.db never pruned. Set it in vm-0 `.env.local` (→ loop now prunes state.db) + restart. **Fleet rollout =
      F12.** 2. **regen ingested non-dispatchable todos** (`BLOCKED-OPERATOR/-BILLING/-CREDENTIALS/-UPSTREAM-OUTAGE`,
      `_(stretch, optional)_`) that can never flip → churn. `_parse_open_todos` now skips them
      (agent-orchestrator@428400f; closed taxonomy + 2 tests). Applied in add + prune passes (existing such tasks
      auto-orphan). 3. **the prune only GC'd yaml-orphan IDs, never state.db rows absent from the yaml ENTIRELY**
      (archived/other-VM/ old-cycle) → 290 unclaimable queued **zombies**. `_prune_stale` now deletes every
      queued+undispatched row whose task_id isn't in the post-prune backlog, guarded on non-empty `current_briefs` so a
      failed scan can't wipe the queue (agent-orchestrator@e50b6b9; +2 tests; done/dispatched never touched). **Deployed
      to vm-0** (FF + restart) + **one-time GC cleared 302→12 queued** (backed up state.db first); loop-path regen
      verified steady at `total=12 pruned_db=0`. 64 tests / ruff / pyright 0. Repo: agent-orchestrator.

### F12 — bake ORCHESTRATOR_REGEN_DB_PATH + the GC fix into the fleet [P1]

- [x] ✅ [INFRA] P1. **DONE 2026-06-07 (agent-orchestrator@e66a40a).** (a) `bootstrap_vm.sh` now upserts
      `ORCHESTRATOR_REGEN_DB_PATH=/var/lib/orchestrator/state.db` into `.env.local` via the same `_upsert_env` pattern
      as VM_ID/AUTOSPAWN (path mirrors `ORCH_STATE_DIR`, kept literal so it's correct regardless of the DRY_RUN branch)
      so every VM's PlanRegenLoop DELETEs orphan rows from state.db, not just backlog.yaml → no per-VM zombie
      accumulation. (b) The GC code fix (agent-orchestrator@e50b6b9) reaches the 9 stopped epic VMs on their next
      FF-pull/restart (verify on first start — needs the VM up, no further code). Composes with F2–F4. Repo:
      agent-orchestrator (bootstrap).

### F13 — vm-0 slot worktree hygiene blocking ALL spawn (dirty pyproject + diverged PM) [P1]

- [x] ✅ [INFRA] P1. **DONE 2026-06-07 via AWS SSM into vm-0 (i-0c9b283b).** The AO/alerting dirty-pyproject +
      diverged-PM items had AUTO-HEALED (F8 self-heal + FF-crons). Residual was slot1/unified-trading-pm
      (`tab/planning/1`): 27 dirty files (~50h old = dead) + 746 behind. Recovered safely: liveness-guarded
      `git stash push -u` (preserved as stash@{0}, recoverable) + `pull --ff-only` → now dirty=0 behind/ahead=0/0. All 5
      vm-0 slots clean. Original detail (live-host op (commit the dirty pyproject as `chore(orphan-wip)` /
      diagnose+gitignore generated churn; FF the clean repos; rebase the diverged PM) — not doable from a laptop slot.
      PARTIAL AUTO-HEAL shipped 2026-06-07: the F8 self-heal (agent-orchestrator@e66a40a) fixes the worktree-NAMING half
      of the FM7 quarantine on the next FF-pull/restart; the dirty-tree + diverged-PM half still needs a human/agent on
      the VM. Original detail: Original detail (context, NOT a checkbox): surfaced by the F9 verification 2026-06-03 —
      RC4 class, recurring + systemic. The branch-state gate quarantines slot 2 (and likely others) for BOTH worker +
      review spawn: (a) **uncommitted `pyproject.toml`** on `agent-orchestrator` (behind 33) + `alerting-service`
      (behind 21) → ff-only pull aborts ("local changes would be overwritten") so `slot-cron-ff-pull` can never advance
      them — this is the chronic worktree-dirty toil (likely uv.lock/version churn or a QG-modified pyproject); (b)
      **`unified-trading-pm` diverged 11-ahead / 584-behind** → FM5 quarantine (the slot-branch-diverged recipe: check
      the 11 ahead for unpushed work FIRST, then `git rebase origin/live-defi-rollout` + `push --force-with-lease`).
      Recipe per inherited-WIP + the diverged-slot CLAUDE.md rules: commit the dirty pyproject as `chore(orphan-wip)`
      (or diagnose the churn source + gitignore if generated), FF the clean repos, rebase the diverged PM. Composes with
      F7 (slot-4 WIP) — same class. Until cleared, spawn (worker AND review) stays quarantined on the affected slots
      **by design** (the gate is correct). Repo: agent-orchestrator host worktrees. Provenance: F9 live-verification log
      2026-06-03.

### F7 — slot-4 WIP recovery on the live vm-0 host [P1]

- [x] ✅ [INFRA] P1. **DONE 2026-06-07 via AWS SSM.** Re-diagnosed vm-0 slots 1-5: NO slot is on a `fix/*`/`feat/*` WIP
      branch anymore (the slot-4 `fix/tradfi-exchange-mappings-minimal` + `fix/pm-ci-self-clone` WIP recovered/cleared
      since the plan was written). No quarantined WIP remains. Original detail (live-host op (inspect/commit/stash the 2
      feature-branch repos, then relabel to tab/vm-0/4) — it cannot be done from this slot. NOTE the F8 self-heal
      shipped 2026-06-07 (agent-orchestrator@e66a40a) does NOT auto-fix this one BY DESIGN: F8 skips non-`tab/*` feature
      branches (the slot-4 repos are on `fix/*` WIP), so slot 4 correctly stays quarantined until a human/agent ON the
      VM recovers the WIP. Original detail: Original detail (context, NOT a checkbox): the only genuine residual
      quarantine on vm-0 (i-0c9b283b31d6b5ca7). The 2026-06-03 worktree realign (see below) deliberately SKIPPED 2
      slot-4 repos on feature branches — genuine mid-work WIP, not safe to relabel (inherited-WIP rule):
      `unified-api-contracts` on `fix/tradfi-exchange-mappings-minimal`, `unified-trading-pm` on `fix/pm-ci-self-clone`.
      Slot 4 will keep tripping FM7 (correctly) until recovered: inspect each repo's WIP → commit/quickmerge or stash →
      then `git branch -m … tab/vm-0/4` (or recreate the slot-4 worktrees on `tab/vm-0/4`). Until then slot 4 stays
      quarantined by design. Repo: agent-orchestrator host (live VM op, no repo change) + the 2 named repos for the WIP
      itself.

### F8 — self-heal: realign a RUNNING VM's worktrees to its VM_ID without a full re-bootstrap [P1]

- [x] ✅ [SCRIPT] P1. **DONE 2026-06-07 (agent-orchestrator@e66a40a).** Implemented BOTH option (a) + (b) AO-scoped: new
      idempotent `scripts/realign-worktree-branches.sh` detects a slot worktree on `tab/<other>/<slot>` and
      `git branch -m`s it to `tab/<ORCHESTRATOR_VM_ID>/<slot>` (content-preserving local rename), SKIPPING non-`tab/*`
      feature-branch WIP (F7) + existing-target conflicts (logged). Wired as a one-shot into `ao-self-pull.sh` (runs on
      the VM cron + restart → option b) AND into `bootstrap_vm.sh` post worktree-setup (re-bootstrap → option
      a-adjacent). So a RUNNING VM un-quarantines its FM7 gate without a manual realign. Smoke-tested against the live
      workspace: 275 already-aligned worktrees → renamed=0 (correct no-op). The matching `verify-slot-host-symmetry.sh`
      probe already exists (check 10). Repo: agent-orchestrator. (Kept AO-scoped rather than editing the PM
      `slot-cron-ff-pull.sh` to avoid cross-repo collision — the AO self-pull cron is the right home for a VM-runtime
      self-heal.)

## 2026-06-03 — F4 applied LIVE to the AutoSpawn host vm-0 (i-0c9b283b31d6b5ca7), spawn confirmed

The 2026-06-02 fixes validated on `vm-cefi` (then stopped). The **live AutoSpawn host** `vm-0` (the plan's "central",
`ORCHESTRATOR_AUTOSPAWN_ENABLED=true`) was still on pre-`129dc6a` worktree naming (`tab/ikennaigboaka/N` +
`tab/ikennaigboakam/N`) vs the code-expected `tab/vm-0/N` → **fully quarantined**
(`AutoSpawnLoop tick: checked=6 spawned=0 failed=6`, repeating). Applied F4 manually (it had only been baked for
re-bootstrap):

- Renamed **476 worktree branches** `tab/{ikennaigboaka,ikennaigboakam}/<slot>` → `tab/vm-0/<slot>` (local
  `git branch -m`, no content change; skipped feature-branch WIP per F7).
- **Confirmed spawn**: `13:22:11 AutoSpawnLoop tick: checked=6 spawned=1`; `13:26:36 … skips={'worker_active': 2}`; live
  tmux `orch-slot-10` running. Quarantine cleared for all aligned slots (2/5/9 transient mid-rename, now clean); only
  slot 4 remains (WIP, F7).

This is the same manual realign F2's note anticipated for _stopped_ VMs — applied here to a _running_ one; F8 hardens it
so it self-heals.

## Per-VM application runbook (when a VM is started)

1. `ORCHESTRATOR_VM_ID=<canonical>` + `ORCHESTRATOR_AUTOSPAWN_ENABLED=true` in `.env.local`; `systemctl restart`.
2. Standardize the VM's operator; realign all slot worktrees to `tab/<operator>/<N>`, clean + FF-current.
3. Confirm the F1 code fix is deployed (AO on LDR HEAD with the operator-decoupling commit).
4. Run F5 validation; then the VM auto-executes its `assigned_vm` backlog.

## Validation evidence (local, 2026-06-02)

- Reproduced RC1 via `worktree_clean_check.check_slot_branch_state` directly: account operator → 25/25 `wrong_branch`.
- Proven green: slot 1 (`tab/hkm/1`, operator `hkm`) → `should_stop=False`, 23/23 `ff_done`.
- RC2/RC3 confirmed from `.env.local` + boot logs (`unknown-vm`, `AutoSpawnLoop disabled`).
- RC4 confirmed: slot 21 `behind 231 + ff-only failed`; slot 2 has 2 repos on `live-defi-rollout`.

## Full-execution criterion

A started VM, after the runbook, auto-ingests its `assigned_vm` plans AND spawns a worker that executes a task, flips
the checkbox, and pushes to `live-defi-rollout` — verified by the `orchestrator_pipeline_e2e_test` round-trip going
green through the execution half (not just discovery).

---

## 2026-06-04 recovery outcomes + Slack-observability gap (slot-1 session)

- **F13 (slot worktree hygiene blocking spawn) — RESOLVED.** Root cause was deeper than dirty trees: **git object-store
  corruption fleet-wide** (fsck missing/broken objects) → ff-pull failed → quarantine → 0 workers. Fixed via `git fetch`
  re-download (0 re-clones), reconciled slots 2/3/5/9 (stashed disposable churn), restarted orchestrator. **vm-0
  revived: 9/10 slots clean, AutoSpawn `worker_active=4`, live workers on slots 5/9/10.**
- **F7 (slot-4 WIP) — still open, confirmed-needs-WIP-recovery.** `origin/tab/vm-0/4` **does not exist** for
  `unified-api-contracts` (on `fix/tradfi-exchange-mappings-minimal`) + `unified-trading-pm` (on `fix/pm-ci-self-clone`)
  — the slot branch was never created / was replaced by these feature branches holding unmerged WIP. Fix = inspect the
  WIP (merged? abandonable?) → merge or set aside → create `tab/vm-0/4` from LDR + recreate the 2 worktrees. Slot-4
  stays quarantined by design (1 of 10) until then. NOT blind-switchable.
- [x] ✅ [AGENT] P1. **Positive "picking up CI work" Slack alert** — DONE (verified 2026-06-07; already shipped since
      the 2026-06-04 audit). `notify_work_picked_up(slot_id, repo, task)` EXISTS in `server/notifications/slack.py:400`
      and is WIRED into the task-dispatch/boot path (`server/server.py:729-739`): on `task_dispatched` it fires a
      best-effort daemon-thread Slack alert with the slot + repo + task title, so #agent-orchestrator-alerts shows the
      fleet WORKING, not just failures (covers CI escalations — they boot through the same dispatch path). The checkbox
      was stale.
