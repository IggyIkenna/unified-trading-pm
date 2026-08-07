---
doc_type: plan
title: Relaunch the vm-zombie-watchdog daemon to pick up the canonical-migration threshold fix (routing-gap fix)
summary: >-
  A single-todo dispatch plan created to close a dispatch-routing gap discovered across three consecutive
  `data_engineering` AO dispatches (slot 12 2026-08-07, slot 7 2026-08-07 x2) of
  `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s [DIAG] P1 todo (gas_fees legacy-purge manifest step). That
  investigation root-caused + confirmed-fixed a VM-boot reap of the `canonical-migration-defi-gas-fees-legacy-purge-*`
  VM (`deployment-service@0e94ceee1` added a `canonical-migration-` entry to `vm_zombie_watchdog.py`'s
  `PREFIX_IDLE_THRESHOLDS` + raised `STALL_TIMEOUT_SEC` in `launch-canonical-migration-vm.sh`), but the fix is DORMANT:
  the live watchdog daemon VM (`vm-zombie-watchdog-20260805-125558`, booted 2026-08-05T07:26:02Z) only loads
  `vm_zombie_watchdog.py` once at its own boot time — over a day before the fix commit — and re-verified STILL running
  the stale code as of this plan's creation. Relaunching that daemon is explicitly out of `data_engineering` craft scope
  (`agents/data_engineering.md` STEP 0.5: `does_not: infra/VM launches`) and the daemon's own history carries two
  confirmed live-VM-kill incidents from careless real-mode relaunches (2026-06-23, 2026-07-18) — the source issue doc's
  own todo already required operator authorization before executing, which the two prior `data_engineering` dispatches
  correctly declined to bypass. The gap this plan fixes is narrower: the underlying `[INFRA] P0` todo lived only inside
  an issue doc with doc-level `assigned_vm: NA`, so the backlog regen never surfaced it for `infra`-craft dispatch in
  the first place — this plan gives it a proper `assigned_role: infra` / `assigned_vm: planning` home so it can reach an
  infra-craft worker (or an operator directly) for the authorization + relaunch itself.
status: active
nature: process
asset_group: [infrastructure, defi]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, vm-launcher, zombie-watchdog, dispatch-routing-gap, gas_fees, canonical-migration]
related:
  [
    /plans/active/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md,
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/archive/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-07"
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
    deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
    /plans/active/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md,
    /plans/archive/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md,
  ]
source: >-
  Discovered as a recurring dispatch-routing gap across three `data_engineering` AO dispatches of
  `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s [DIAG] P1 todo (2026-08-07: slot 12, slot 7 x2 — see that plan's
  own Progress Log). All three independently confirmed the same root cause + the same "fix shipped, daemon dormant" gap
  and declined to relaunch the daemon themselves (out of craft scope; live-VM-kill precedent); the second and third
  slot-7 dispatches each recommended via `/blocked` that the operator create exactly this kind of `infra`-scoped
  dispatch plan. Drafted `status: draft` per CLAUDE.md § "Plan destination — ASK BEFORE CREATING" — flipping to `active`
  is the operator's call, mirroring `infra_satellite_ao_dispatch_batch8_2026_08_07.md`'s same-day precedent for an
  autonomously-drafted single-todo infra plan.
---

# Relaunch vm-zombie-watchdog — routing-gap fix

> **Operator authorized the relaunch to main at 2026-08-07T07:30Z; flipped `status: draft` → `active` in the same edit
> as the todo flip below** (the plan was never dispatched before the work completed — activated retroactively so the
> record is consistent). This plan's one todo is DONE; it is eligible for archival per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

## Why this plan exists — a dispatch-routing gap, not new investigation

The underlying problem is fully root-caused and the code fix is already shipped and confirmed present on
`live-defi-rollout` (`deployment-service@0e94ceee1`). What is NOT done is the daemon relaunch itself, and that action
has sat un-dispatchable because the todo describing it lives inside
`plans/active/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`, whose doc-level
frontmatter is `assigned_vm: NA` — so `regen_backlog_from_plan.py` never surfaces that todo to any worker, `infra`-craft
or otherwise. Three consecutive `data_engineering` dispatches (which cannot execute the relaunch themselves — out of
craft scope, and the action itself carries two prior confirmed live-VM-kill incidents making it
operator-authorization-gated regardless of craft) rediscovered the identical state on 2026-08-07 without anything
changing, because nothing was actually acting on their `/blocked` recommendation. This plan is that action.

## Todos

- [x] ✅ [OPERATOR] [INFRA] P0. **Relaunch the `vm-zombie-watchdog` daemon VM** — `deployment-service@0e94ceee1`
      relaunched as `vm-zombie-watchdog-20260807-075242` (created 2026-08-07T07:52:45Z, asia-northeast1-c), boot-clean;
      first real-mode poll at 08:02:58Z logged "Watchdog summary: 26 alive / 0 zombie / 3 too_young" → "watchdog
      complete: killed 0/0 zombies" + "terminated-reaper: reaped 0/0" — live fleet intact. Dry-run validated safe (2
      clean cycles, zero reaps) BEFORE cutover; stale daemon `vm-zombie-watchdog-20260805-125558` deleted. Operator
      authorized the relaunch to main at 2026-08-07T07:30Z; executed by main. Source issue doc's mirrored todo flipped
      with the same evidence (see
      `issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`). **Done when** (met):
      a fresh `vm-zombie-watchdog-*` instance (created after this todo executed) is RUNNING with a confirmed-clean
      serial-console boot and at least one real-mode "watchdog complete" poll cycle logged, and the source issue doc's
      todo is flipped with that evidence cited. Repo: deployment-service (relaunch), unified-trading-pm (source-doc
      reconciliation + this plan's own archival once its one todo is done). Source:
      `issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md` (the `[INFRA] P0` todo,
      verbatim intent).

## Codex SSOTs (read before executing this todo)

- `/codex/05-infrastructure/vm-launcher-runbook.md` — VM launch + zombie-watchdog conventions
- `/plans/archive/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md` — the two prior live-VM-kill
  incidents from careless real-mode relaunches of this exact daemon; read in full before executing
- `plans/active/task_template.md` §4 — the single-todo finalize-plan-coverage carve-out this plan uses (one todo, no
  separate finalize twin — archival folded into the todo's own "Done when")

## Progress Log

- **2026-08-07 (data_engineering, slot 7)**: drafted after a THIRD consecutive `data_engineering` dispatch of
  `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s [DIAG] P1 todo re-confirmed the identical dormant-daemon state
  (`vm-zombie-watchdog-20260805-125558` still RUNNING, unchanged) with no new information to add — the prior two
  `/blocked` postings from this same slot had already recommended exactly this fix (an `assigned_role: infra` dispatch
  plan) without anyone acting on it. Created `status: draft` (not `active`) per CLAUDE.md's plan-creation hard rule; no
  VM/GCS/cron mutation performed by this session. Read-only investigation only.
- **2026-08-07 (main, operator-authorized relaunch)**: operator authorized the real-mode relaunch at 07:30Z; main drove
  it via an infra sub-agent. Dry-run validated safe first (2 clean cycles, zero reaps), then cutover: stale
  `vm-zombie-watchdog-20260805-125558` deleted, new instance `vm-zombie-watchdog-20260807-075242` created
  2026-08-07T07:52:45Z (asia-northeast1-c), serial-console confirmed boot-clean, first real-mode poll at 08:02:58Z
  logged "Watchdog summary: 26 alive / 0 zombie / 3 too_young" → "watchdog complete: killed 0/0 zombies" +
  "terminated-reaper: reaped 0/0" — live fleet intact, `deployment-service@0e94ceee1`'s `canonical-migration-`
  `PREFIX_IDLE_THRESHOLDS` fix now live. Flipped this plan's one todo `[x]` and `status: draft` → `active` in this edit;
  mirrored the flip in `issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`. This
  plan is now complete and eligible for archival (done as a separate follow-up commit).
