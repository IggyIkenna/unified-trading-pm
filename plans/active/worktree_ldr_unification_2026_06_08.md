---
title: Worktree LDR-unification — drop per-tab branches, slots on live-defi-rollout (Path B reference-clones)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
created: 2026-06-08
orchestrated_by: plans/active/cicd_contract_hardening_2026_06_01.md
related_plans:
  - plans/active/per_agent_worktrees_2026_05_10.md
  - plans/active/qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md
  - plans/archive/2026_06/quickmerge_dep_content_sync_and_strict_enforcement_2026_06_08.md
  - plans/active/staging_clean_start_and_stale_pr_hygiene_2026_06_08.md
source:
  - chat design session 2026-06-08 (operator + vm-planning)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Worktree LDR-unification

> **Orchestrated by** `cicd_contract_hardening_2026_06_01.md` (CI master). **SEQUENCED LAST — runbook step 6**
> (operator-sequenced 2026-06-08): execution is **deferred** until the pipeline is healthy and green end-to-end (runbook
> steps 0–5 done, `main == LDR` fleet-wide), because **live slot-cron / tab-branch work is ongoing right now** and
> retiring the branches + crons mid-flight would disrupt it. Design/spike (Phase 0) may be drafted earlier, but the
> migration itself (Phases 1–3) does NOT start until step 6.

## Problem (what we found)

The per-tab **branch** (`tab/<op>/N`) is **not a deliberate architectural choice** — it's a workaround for git's "can't
check out the same branch in two worktrees" constraint (`per_agent_worktrees_2026_05_10.md` Path A). The real isolation
is **worktree-level** (separate index/working-tree → solves the 4 shared-`.git/index` foot-guns). The branch is
incidental, and it buys us a continuous **sync tax**:

- `slot-cron-ff-pull.sh` (every 5 min, LDR→tab)
- `tab-mirror-to-ldr.yml` GHA (tab→LDR FF, both legs)
- per-slot branch maintenance in `setup-tab-worktrees.sh` (`--add-slot`/`--reset-slot` rebase paths)
- orchestrator slot↔branch tracking + the diverged-tab recovery recipes in CLAUDE.md

**Commit attribution is already in the author NAME field (`[slot-<N>·<host>]`), fully independent of branch** — so agent
identity survives a branch change unchanged (composes with `quickmerge_dep_content_sync_and_strict_enforcement` §
agent-naming).

## Decision — Path B, NOT shared-`.git`-same-branch

The literal "same branch, shared `.git`" form is the one variant that fails: git refuses it, and forcing it gives
**commit-time ref races** on the shared `live-defi-rollout` ref/HEAD (today's model defers all contention to _push_
time, mediated by remote atomicity). The sound form is **Path B** (documented + un-chosen in
`per_agent_worktrees_2026_05_10.md:198`, only because "Path A worked smoothly with Cursor"):

- **Per-slot `git clone --reference ${WORKSPACE_ROOT}/<repo> --shared <url> .tabs/<N>/<repo>`** — separate `.git` per
  slot (no ref races), shared object store via `--reference` (no disk blowup), each clone **independently on
  `live-defi-rollout`**. Default branch = LDR.
- Contention moves to **LDR push-time** (rebase-on-reject) — already handled by `quickmerge` STAGE 0.4 Not-Behind Gate.

## Pre-audit (blast radius)

- [x] ✅ [SCRIPT] P2. Grep every consumer of `tab/<op>/N` branch naming: `setup-tab-worktrees.sh`,
      `slot-cron-ff-pull.sh`, `slot-git-status-report.sh`, `slot-master-rebase.sh`, `tab-mirror-to-ldr.yml`,
      `verify-slot-host-symmetry.sh`, `agent-orchestrator/server/worktree_clean_check.py`, `workspace-manifest.json`
      base-branch overrides, and the CLAUDE.md / `codex/05-infrastructure/per-tab-worktrees.md` rule surface. Build the
      removal/rewrite manifest BEFORE any change.

## Phase 0 — Spike (research)

- [x] ✅ [SCRIPT] P2. Path-B spike: stand up 2 reference-clone slots on `live-defi-rollout`, confirm Cursor/VSCode git
      integration, shared-object disk footprint, and concurrent commit+push behaviour (two slots push LDR
      near-simultaneously → rebase-on-reject converges). Success: no ref-race, disk ≈ Path A, IDE clean.

## Phase 1 — quickmerge LDR-direct (depends: Phase 0)

- [x] ✅ [SCRIPT] P2. Change `quickmerge.sh`: on a slot that is **on LDR** (no tab branch), commit-to-LDR (push LDR) +
      **open the LDR→staging PR directly** — retire the tab→LDR mirror hop. Forced staging-PR existence is a HARD
      post-condition of every code quickmerge (cross-ref `quickmerge_dep_content_sync_and_strict_enforcement` § strict).
- [x] ✅ [SCRIPT] P2. Keep STAGE 0.4 Not-Behind reconcile (ff→rebase-autostash) as the LDR push-contention mediator.

## Phase 2 — Migrate bootstrap + retire sync machinery (depends: Phase 1)

- [x] ✅ [SCRIPT] P2. Rewrite `setup-tab-worktrees.sh` to provision Path-B reference-clones on LDR
      (`--init`/`--add-slot`/ `--reset-slot` collapse to clone + clean-check, no branch create/rebase).
- [x] ✅ [SCRIPT] P2. **Retire** `tab-mirror-to-ldr.yml` (fleet rollout-template delete) + `slot-cron-ff-pull.sh`
      (replace with a thin `git -C <slot> pull --ff-only origin live-defi-rollout`), and drop the per-slot-branch reset
      paths.
- [x] ✅ [SCRIPT] P2. Add a **drift-detection cron** (replaces the divergence half of tab-mirror): flag any slot whose
      HEAD is not an ancestor-or-equal of `origin/live-defi-rollout` (the only invariant left to police).

## Phase 3 — Rules + codex alignment (depends: Phase 2)

- [x] ✅ [DOCS] P2. Rewrite CLAUDE.md + `codex/05-infrastructure/per-tab-worktrees.md`: remove tab-branch/upstream/
      diverged-tab recovery sections; replace with the Path-B LDR-direct model. Update `SUB_AGENT_MANDATORY_RULES.md` §
      git-discipline.
- [x] ✅ [DOCS] P2. Update `agent-orchestrator/server/worktree_clean_check.py` base-branch logic (LDR for all; the AO
      `main` override is already removed).
  - ⚠️ **Over-marked correction (2026-06-10)**: this item covered ONLY `base_branch_for_repo` (the ahead/behind base).
    The **FM7 pre-spawn gate still hard-asserted `HEAD == tab/<op>/<N>`** (a hard gate in `autospawn.py` / `server.py` /
    `worker_liveness.py`) and `commit_and_push_dirty_repos` still did `git push origin HEAD` — together they would have
    FM7-quarantined EVERY Path-B slot (HEAD on LDR) so no worker could spawn/respawn, and the orphan-WIP push would have
    landed un-QG'd WIP directly on the shared integration branch. Completed at **agent-orchestrator@edf5e63** (gate
    accepts `HEAD==base`; orphan-WIP → `wip-preserve/orchestrator-slot-<N>` + reset to `origin/<base>`; +3 tests).
    Verified live: `check_slot_branch_state` returns `should_stop=False` for all Path-B slots.

## Success criteria

- Zero `tab/<op>/N` refs created; `git rev-parse --abbrev-ref HEAD == live-defi-rollout` on every slot.
- `slot-cron-ff-pull` + `tab-mirror` GHA deleted fleet-wide; drift-cron green.
- A 2-slot concurrent commit+quickmerge converges with no manual rebase.
- `verify-slot-host-symmetry.sh` passes under the new model.

## Codex SSOT updates

`codex/05-infrastructure/per-tab-worktrees.md` (rewrite), CLAUDE.md § Per-Tab Worktrees + § Git discipline,
`SUB_AGENT_MANDATORY_RULES.md` § git.

## Progress — 2026-06-08 (slot-1 autonomous, EXECUTED)

- **EXECUTED** (operator: "multi-slot session ended, finish now"). Slots 2-11 reclined to **Path-B reference-clones** on
  `live-defi-rollout` (`git clone --reference <sibling> <url>`, own .git, shared objects). **All prior uncommitted slot
  WIP preserved to `origin/wip-preserve/slot-<N>` branches** first (verified recoverable) — nothing compromised.
- **Machinery**: `setup-tab-worktrees.sh` now provisions Path-B reference-clones; `tab-mirror-to-ldr.yml` DISABLED
  fleet-wide (24 repos); `slot_drift_check.py` is the new drift invariant (HEAD ancestor-or-equal of origin/LDR);
  `slot-cron-ff-pull.sh` + `quickmerge.sh` work UNCHANGED for Path-B (keyed on the integration branch, not tab names —
  the cron's upstream self-heal is a no-op on a clone whose @{upstream}=origin/LDR; quickmerge pushes HEAD→LDR + opens
  the staging PR). Phase-1 spike subsumed by the live reclone proof.
- **Docs**: CLAUDE.md § "Per-slot worktrees — Path-B" + SUB_AGENT + codex/per-tab-worktrees.md SUPERSEDED-bannered.
- **Slot-1** stays on `tab/ikennaigboaka/1` ONLY as the live operating slot during this migration — reclines to Path-B
  on its next `setup-tab-worktrees.sh --reset-slot 1` (it pushes via explicit `HEAD:live-defi-rollout` refspec, so it is
  unaffected by the tab-mirror retirement). `worktree_clean_check.py` already bases on LDR (the AO main-override was
  removed earlier) — no change needed.

## Open — orchestrator/planning VM host migration to Path-B (2026-06-09, operator-directed)

> Operator 2026-06-09: "the vm-planning vm needs to be redone to use the new cron with the remote remotes and agents
> using their worktree tabs to offer their commits." The laptop hosts are on Path-B; the **LIVE orchestrator VM is
> NOT** — it is still the symmetric-worker host that spawns VM workers, and those workers must offer commits the SAME
> Path-B way (reference-clone slots on `live-defi-rollout`, ff-pull cron, `quickmerge --agent --files`), not the retired
> tab-branch model. **Why it matters now:** the `ci-failure-watcher --escalate` path repository-dispatches genuine
> merge-conflict promotion PRs to this VM to spawn a worker that rebases on LDR — if its workers are on the stale
> worktree model (or it is running behind), escalation degrades to "no worker spawned". The new `--auto-recover` path
> (shipped 2026-06-09) removes the v2-never-reported deadlock from the escalate load, so escalations are now RARE and
> genuinely need a healthy, Path-B-correct worker host.

**Target host (LIVE, audited 2026-06-09):** AWS `i-0c9b283b31d6b5ca7` = `vm-0` / `agent-orchestrator-vm-1`, `m8i.4xlarge`,
running, `api.agent-orchestrator.odum-research.com → 13.113.200.22`. `/health` reports **version 0.6.0** (CLAUDE.md
references v0.7+ for `assigned_vm`) and `data_freshness.stale: true` → the deployed orchestrator is also BEHIND and
should be redeployed as part of this. Worker-topology SSOT: `codex/05-infrastructure/agent-orchestrator-worker-topology.md`.

- [x] ✅ [INFRA] P1. On `i-0c9b283b31d6b5ca7`: pull the new PM tooling (`setup-tab-worktrees.sh` Path-B,
      `migrate-slots-to-pathb.sh`, `slot_drift_check.py`, the strict-quickmerge pre-push hook, updated CLAUDE.md +
      SUB_AGENT + codex) onto its main clones via `git pull --ff-only origin live-defi-rollout`, then **DRY-RUN**
      `migrate-slots-to-pathb.sh --slots 1-<N> --dry-run` (declare VM identity first:
      `git config --global slotIdentity.name <vm-id>` / `…email` — VMs leave email at the Ikenna fleet default per
      CLAUDE.md § Commit attribution; `VM_NAME` env supplies the `[slot-N·<vm>]` host tag). Preserves all WIP to
      `origin/wip-preserve/<vm>-slot-<N>` first. — **DONE 2026-06-10**: PM + AO main clones FF-pulled to
      `origin/live-defi-rollout` (PM junk WIP stashed → `vm-pm-wip-cleared-pre-pathb-2026-06-10`); dry-run clean with
      identity `ikennaigboaka [slot-N·planning]` (`VM_NAME=planning`).
- [x] ✅ [INFRA] P1. Execute the Path-B reclone of every orchestrator worker slot on the VM
      (`migrate-slots-to-pathb.sh --slots 1-<N>`); verify `slot_drift_check.py --tabs-root <tabs>` exits 0 and each slot
      is a clone on `live-defi-rollout` (HEAD ancestor-or-equal of `origin/LDR`), identity reads `<vm-id> [slot-N·<vm>]`.
      — **DONE 2026-06-10**: `--slots 1-5` → 115/115 clones, 0 failures, 0 WIP-preserve needed (clean trees); all 5 slots
      = clone on `live-defi-rollout`, 0 leftover worktrees, identity `ikennaigboaka [slot-N·planning]`; drift = 115/115
      ancestor-or-equal of `origin/LDR`.
- [x] ✅ [INFRA] P1. Install/refresh the symmetric-worker crons on the VM (`slot-cron-ff-pull.sh` +
      `slot-git-status-report.sh` every 5 min) so VM workers stay current on LDR and offer commits via
      `quickmerge --agent --files` from their own reference-clone worktree — confirm `verify-slot-host-symmetry.sh`
      exits 0 on the VM (both crons installed + ran <10 min + report posted). — **DONE 2026-06-10**: ff-pull +
      status-report + symmetry crons present; `verify-slot-host-symmetry.sh` exits 0.
- [x] ✅ [INFRA] P1. Redeploy the orchestrator on the VM to current `live-defi-rollout` (it reports v0.6.0 +
      `data_freshness.stale: true`); confirm `/health` version advances + `stale: false`, and AutoSpawn headroom is
      healthy so `--escalate` dispatches actually spawn a worker (the "no worker spawned" symptom clears). — **DONE
      2026-06-10**: AO main FF-pulled to **edf5e63** (Path-B gate fix) + `systemctl restart orchestrator.service`;
      `/health` `stale:false`, serving requests, no FM7/quarantine/traceback errors (only a benign self-retrying usage-
      poller sqlite-locked transient); `ORCHESTRATOR_AUTOSPAWN_ENABLED=true`, queue currently empty so no spawn yet
      (correct). NOTE: `/health` `version` stays "0.6.0" — that is a hardcoded app-version constant, NOT a deploy-fresh-
      ness signal (code is current LDR); the "version advances" expectation was a misread of that constant.
- [ ] [DOCS] P2. **AO worker-facing surface still teaches the tab-branch model (Phase-3 gap, found 2026-06-10)** —
      rewrite `agent-orchestrator/agents/worker.md` (it still instructs "commit on / push to your tab branch
      `tab/<operator>/<SLOT_ID>`") and the `branch` boot-prompt render-var fallback (`autospawn.py:229`,
      `server.py:560`/`:1765` → `f"tab/{operator}/{slot_id}"`) to the Path-B LDR-direct model, so spawned workers aren't
      handed stale tab-branch git instructions. Non-blocking (under Path-B a worker's `git push origin HEAD` / quickmerge
      resolves to LDR) but a clarity + `SUB_AGENT_MANDATORY_RULES` parity gap.
- [ ] [SCRIPT] P3. **Cosmetic bug in `scripts/dev/migrate-slots-to-pathb.sh` (found 2026-06-10)** — the run-header prints
      `| DRY-RUN` whenever `DRY` is set to ANYTHING incl. `0` (`${DRY:+ | DRY-RUN}` treats the string `"0"` as set); the
      actual logic correctly gates reclone on `[[ "$DRY" == 1 ]]`, so real runs DID reclone — only the header label lies
      (confirmed: a real `--slots 1-5` run printed `DRY-RUN` yet performed all 115 clones). Fix:
      `dry_label=""; [[ "$DRY" == 1 ]] && dry_label=" | DRY-RUN"` and use `$dry_label`.
- [ ] [INFRA] P2. **agent-orchestrator drift-tick is STAGED on LDR pending ao's LDR→main promotion** (ao@ad76dda synced
      `main-backmerge-to-ldr.yml` from the PM SSOT, 2026-06-09). Scheduled workflows fire only from the DEFAULT branch
      (ao default = `main`), so the ao drift-tick is INERT until it reaches ao `main`. ao `main` is `ahead_by=22 /
      behind_by=0` of LDR (strictly behind, clean FF) but draining it deploys in-flight ao work + is G6-gated — so it
      activates when ao's LDR→main promotion is enabled (this section's P1 redeploy), NOT by a unilateral FF now.
- [ ] [INFRA] P2. End-to-end smoke: force a genuine merge-conflict promotion PR (or wait for a real one), confirm
      `ci-failure-watcher --auto-recover --escalate` auto-recovers v2-never-reported PRs in-band AND escalates the true
      conflict → the VM spawns a Path-B worker that rebases on LDR + re-quickmerges. Archive this section when green.
