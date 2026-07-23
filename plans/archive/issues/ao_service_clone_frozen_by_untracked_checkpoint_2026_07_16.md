---
doc_type: issue
title:
  The central orchestrator VM has been running 2-day-old code — one untracked file froze the SERVICE clone at 23 commits
  behind, and the FF-pull skipped it silently every 5 minutes
summary: |
  The clone `orchestrator.service` runs from (WorkingDirectory=/home/ubuntu/unified-trading-system-repos/agent-orchestrator)
  was stuck at HEAD 9599c91 / 2026-07-14 16:40, 23 commits behind live-defi-rollout. Cause: ONE untracked file,
  main-agent-checkpoint.md — which context_lifecycle.py instructs the main agent to write BY DESIGN on RECYCLE — made
  slot-cron-ff-pull.sh classify the clone [skip:dirty] and refuse to fast-forward, every 5 minutes, for two days. Zero
  tracked modifications. The freeze is self-sustaining: a clone that cannot FF never stops being dirty. Consequence:
  every agent-orchestrator fix shipped in that window (including the whole 2026-07-16 R1/R2/R5/R6 dispatch-hardening
  set) was on LDR and NOT RUNNING — the fleet was executing code we had already fixed. Root cause is FIXED (two ships,
  below). The VM itself is NOT yet recovered: operator ruling 2026-07-16 is that the deploy is theirs to run, because
  unfreezing pulls 23 commits, ~22 of them not written or verified by this session, onto the live orchestrator.
status: resolved # (was: open) 2026-07-23 plan-reconcile — both remaining todos closed (one DONE via the archived ao_fleet_infra_hardening 800-clone sweep, one operator-descoped to the deployment-ui Fleet tab)
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, deployment, ff-pull, stale-clone, fleet-capacity, infrastructure, operator-action]
related:
  [
    ../../archive/2026_07/ao_dispatch_hardening_2026_07_16.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    ../../epics/orchestrator_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: orchestrator_master
priority: P0
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
locked_since:
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
supersedes:
superseded_by:
depends_on:
assigned_role: infra
drift_direction: advance-code
source:
  - "Live SSM inspection of i-0c9b283b31d6b5ca7 2026-07-16 while attempting Phase 3 (runtime verification) of
    ao_dispatch_hardening_2026_07_16"
  - "scripts/dev/slot-cron-ff-pull.sh (the [skip:dirty] gate) + its own auto-clean carve-out comments recording the two
    prior incidents"
---

> **🟢 EXECUTION CONSOLIDATED 2026-07-17** — this doc's open items are now tracked and executed via
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md)
> (operator-session local plan; verified-live classification table there). Do NOT start work from this doc alone — flip
> items in the plan and mirror them here. This doc stays the detail/evidence record.

# The central AO VM has been running 2-day-old code

> **✅ RECOVERED 2026-07-16 — the operator deployed it.** VERIFIED live: clone HEAD `96d005f`, `behind = 0`, all four
> fixes present on the box (R1 `claimable_queued_task_ids` ×3, R2 `_spawn_param_plan` ×3, R5 `_target_slot_is_dead` ×3,
> R6 `review_slot` ×10) + the gitignore. And the code is genuinely **RUNNING**, not merely on disk:
> `--reload --reload-dir server` is in ExecStart, the journal shows
> `15:01:03 WatchFiles detected changes in 'server/dispatch.py', … Reloading…` and the reloader's worker was re-forked
> at `15:01:12` (PID 1921076, parent 1544329 — the supervisor survives reloads by design, which is why its Jul-15 start
> time is NOT evidence of stale code). The operator also fixed a **root-PM divergence** — the clone the AO backend reads
> plans FROM — separately. **Phase 3 of `ao_dispatch_hardening` is UNBLOCKED.** Original finding retained below.
>
> ~~**🔴 OPERATOR ACTION REQUIRED — the VM is still frozen.**~~ The root cause is fixed and shipped, but the fix cannot
> reach the clone it fixes: a frozen clone cannot pull the change that unfreezes it. Someone has to break the loop by
> hand — recovery commands below. **Operator ruling 2026-07-16: this deploy is the operator's**, because unfreezing
> pulls 23 commits (~22 written by other sessions and not verified here) onto the live orchestrator.

## What was measured (live, read-only SSM, 2026-07-16)

Host `agent-orchestrator-vm-1` / `i-0c9b283b31d6b5ca7` — the central orchestrator VM.

| Probe                                                  | Result                                                               |
| ------------------------------------------------------ | -------------------------------------------------------------------- |
| `systemctl is-active orchestrator.service`             | `active` — the service is UP and looks healthy                       |
| `WorkingDirectory` (systemd unit)                      | `/home/ubuntu/unified-trading-system-repos/agent-orchestrator`       |
| `git log -1` in that clone                             | `9599c91` — **2026-07-14 16:40**                                     |
| `git rev-list --count HEAD..origin/live-defi-rollout`  | **23**                                                               |
| `git status --short`                                   | `?? main-agent-checkpoint.md` — **one untracked file**               |
| `git diff --stat`                                      | **empty — zero tracked modifications**                               |
| `grep -c claimable_queued_task_ids server/dispatch.py` | **0** — R1 is not on the box                                         |
| FF-pull cron log                                       | `[skip:dirty] agent-orchestrator — uncommitted changes`, every 5 min |

The same cron log shows every OTHER clone pulling fine in the same sweep (`[ff] agent-orchestrator … FF +1 → f1638923`
into the SLOT clones, `[ff] unified-trading-pm … FF +3`). **The cron is healthy. Only the service clone is frozen.**

## Why one untracked file is fatal

1. `context_lifecycle.py:195` instructs main, on RECYCLE, to write its watchlist/open-items/unanswered-messages
   checkpoint to `main-agent-checkpoint.md` and EXIT; the fresh boot reads it back. So the file exists **by design** in
   the clone root of any host running a main agent. It was never gitignored.
2. `slot-cron-ff-pull.sh` treated ANY `git status --porcelain` output as `[skip:dirty]` and refused to fast-forward.
3. Therefore the clone could never FF — **and because it could never FF, the file never stopped being dirt.** The freeze
   is self-sustaining: a stray file costs FOREVER, not one tick.

**This is the THIRD instance**, and the first two are memorialised in that script's own auto-clean carve-outs:

| Date       | File                                       | Clone                  | Damage                                 |
| ---------- | ------------------------------------------ | ---------------------- | -------------------------------------- |
| 2026-06-10 | `plan_health_digest.md`/`plan_skeleton.md` | vm-planning PM clone   | **545 commits behind** → empty backlog |
| 2026-07-14 | cron self-pull artifacts                   | root-PM                | **1138 commits behind**                |
| 2026-07-16 | `main-agent-checkpoint.md`                 | **CENTRAL AO service** | **23 commits behind, 2 days**          |

Each was patched by allowlisting one more filename to `git clean`. An allowlist can only ever name files someone already
got burned by, so the next new scratch file does it again — which is exactly what happened.

## Why it went unnoticed for two days

The FF-pull already has a dirty-streak alert (`FF_DIRTY_STREAK_THRESHOLD=3`) — but it only fires when **EVERY repo in
the sweep** is `[skip:dirty]`. Here 24 repos pulled fine and one was frozen, so the streak never triggered. **A single
frozen clone among healthy ones is invisible to the alarm that exists to catch exactly this.** Same shape as
`needs_operator_count` being computed and rendered nowhere.

## Root cause — FIXED (2 ships)

- **`agent-orchestrator@96d005f`** — gitignore `main-agent-checkpoint.md`. Chosen over adding it to the `git clean`
  allowlist because clean would **delete** the checkpoint, which is live state the next main boot reads to recover its
  identity and watchlist; ignoring keeps the file AND removes it from `--porcelain`, so the FF proceeds. The ff-pull
  script's own comment already prescribed this ("Should also be gitignored; this is the per-tick safety net").
- **`unified-trading-pm@5a8d6bc4d`** — the general fix (operator ruling 2026-07-16: "fix it now").
  `slot-cron-ff-pull.sh` now blocks only on **TRACKED** dirt. Untracked-only dirt proceeds, because an FF moves only
  tracked content, and in the one case where an untracked file genuinely collides git refuses on its own ("untracked
  working tree files would be overwritten") into the existing `[skip:ff-failed]`/`conflict` branch. **Git is the
  authority; guessing "dirty ⇒ skip" is what turned a harmless stray file into a permanent outage.** Verified
  empirically on a purpose-built repo (A: untracked-only → FF succeeds, file preserved; B: tracked dirt → still skips;
  C: real collision → git refuses, nothing clobbered), plus a `--dry-run` across all 25 real workspace repos (clean).

## Todos

- [x] [INFRA] P0. ✅ **DONE 2026-07-16 — operator deployed; VERIFIED live (not assumed).** Clone HEAD `96d005f`,
      `behind = 0`, R1/R2/R5/R6 all present on the box, and the running worker re-forked at `15:01:12` after WatchFiles
      saw the change — so the fixes are executing, not just sitting on disk. The operator also repaired a **root-PM
      divergence** (the clone the AO backend reads plans from), which was a second, independent staleness.
      ~~**Unfreeze + deploy the central VM** (operator-owned per the 2026-07-16 ruling).~~ The tree is clean apart from
      the one untracked file, so this is a plain FF — no WIP at risk. Recovery, on `i-0c9b283b31d6b5ca7`:

      ```bash
                                      cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
                                      sudo -u ubuntu git status --short          # expect ONLY: ?? main-agent-checkpoint.md
                                      sudo -u ubuntu git diff --stat             # expect EMPTY (no tracked WIP)
                                      sudo -u ubuntu git fetch origin live-defi-rollout
                                      sudo -u ubuntu git merge --ff-only origin/live-defi-rollout   # brings the gitignore → never recurs
                                      sudo -u ubuntu git log -1 --format='%h %ci'                   # confirm it moved off 9599c91
                                      grep -c claimable_queued_task_ids server/dispatch.py          # expect ≥1 → R1 is now on the box
                                      sudo systemctl restart orchestrator.service                   # systemctl ONLY — never nohup uvicorn (main.md HARD RULE)
                                      systemctl is-active orchestrator.service
                                      ```

                                      **Gate**: `git rev-list --count HEAD..origin/live-defi-rollout` == 0 AND
                                      `grep -c claimable_queued_task_ids server/dispatch.py` ≥ 1 AND the service is `active`. Note this deploys 23
                                      commits, ~22 of them from other sessions — all LDR-landed and gated by the normal path, but not verified by the
                                      session that found this.

- [x] [INFRA] P1. ✅ **RAN 2026-07-16 17:35Z — and it FAILED, which is exactly why it was worth running.** Unblocked by
      this doc's fix (the code was finally live, so there was something real to measure). Result: **R1 did NOT reduce
      the churn** — `autospawn_succeeded` per hour was 29 · 27 ‖ _deploy_ ‖ 27 · 30, i.e. flat across the boundary; 24h
      totals 915 spawns vs **63** `task_dispatched`, with `task_dispatched` at **0 for 3h straight** post-deploy.
      Root-caused to a phantom candidate slot (slot 0, unconfigured+paused since 2026-07-06, therefore holding no
      slot_skips, kept a fleet-skipped task permanently "claimable") and fixed in `agent-orchestrator@6c778e6`. The
      remaining pass-gate is tracked as the new P0 in `ao_dispatch_hardening_2026_07_16` Phase 3 — **not duplicated
      here**. That plan stays code-shipped-not-proven until that P0's runtime verdict lands.

- [x] [INFRA] P2. 🚫 **CLOSED-SUPERSEDED 2026-07-23 — operator-descoped, delivered in another repo.** The operator
      descoped the per-repo freeze-streak signal + surface on 2026-07-21 and handed it to the agent working the
      deployment-ui Fleet tab (breadcrumb in `../ao_open_issues_consolidated_close_out_2026_07_17.md`). Verified the
      deliverable actually landed: `deployment-ui/src/pages/FleetGit.tsx` renders per-repo `dirty_files` / `ahead` /
      `behind` / `DRIFT` badges plus `ff_pull_last_result` and reporter/ff-cron staleness, so a single frozen repo among
      clean siblings IS individually visible. **Do NOT reopen this in agent-orchestrator** — any follow-up belongs to
      FleetGit.tsx's owner. Original item: **HANDED OFF 2026-07-16 — operator is routing the UI-surface + alerting work
      to a separate agent** ("this needs a proper UI surface and alerting system so it doesn't occur again"). Kept here
      as the requirement of record; do NOT start it from this doc without checking with that owner first. **Make a
      single frozen clone visible.** The dirty-streak WARN only fires when EVERY repo in a sweep is dirty, so this
      outage was silent for two days. Alert on a per-repo streak (repo X `[skip:dirty]`/`[skip:ff-failed]` for N
      consecutive ticks), not on an all-repos-dirty sweep. The signal already exists — `_ff_record` tokens and
      `ff_pull_last_result` are per-sweep; make them per-repo. **Gate**: a single deliberately-frozen clone raises a
      WARN within N ticks.

- [x] [INFRA] P2. ✅ **DONE 2026-07-23 (scope-qualified — read the qualification before quoting this).** Executed via
      `ao_fleet_infra_hardening_2026_07_20.md` (archived 2026_07) todo 4: a measured sweep of **375 clones on the hk
      host + 425 on the orchestrator VM (800 total)** — worst clone 7 behind, **no 249-behind cases**, 42 clean clones
      FF'd, dirty clones protected rather than force-updated. **The qualification, kept deliberately**: "every host" was
      not literal (Ikenna's laptop was not swept) and the result is POINT-IN-TIME, not a standing guarantee — the child
      plan carries its own correction banner saying exactly that, because an earlier version of this claim was
      overclaimed as "zero frozen clones remain". Original item: **Audit every host for the same freeze.** The
      gitignore + ff-pull fixes stop it recurring, but any clone already frozen by an untracked file stays frozen until
      someone FFs it (self-sustaining). Sweep every host's root + slot clones for `HEAD..origin/live-defi-rollout > 0`
      with untracked-only dirt. The main agent's own checkpoint (read 2026-07-16) already reports a related, unresolved
      staleness on host `hk`: "hk utm behind 12→20→49 (growing steadily); FOUR hk repos now behind (deployment-ui=2,
      features-service=4, instruments-service=3, market-tick-data-service=6)" — it correctly concluded "host-side cron
      restart = operator/host-owned (outside my API surface)" and could not act. Check whether that shares this root
      cause.

## Progress Log

- **2026-07-16** — Found while attempting Phase 3 (runtime verification) of `ao_dispatch_hardening_2026_07_16`: the
  first check was "is the fixed code even running on the VM?" and the answer was no —
  `grep -c claimable_queued_task_ids server/dispatch.py` → **0**. That single check is the reason this surfaced at all;
  the plan would otherwise have been declared done on the strength of a green QG. Root cause fixed in two ships
  (`agent-orchestrator@96d005f` gitignore, `unified-trading-pm@5a8d6bc4d` general ff-pull fix). VM recovery left to the
  operator per their ruling — unfreezing deploys 23 commits, ~22 unverified by this session, onto the live orchestrator,
  and rule-11 blast-radius discipline says do not ship what you have not verified.
- **2026-07-16** — Worth recording as its own lesson: the general fix could not be committed on the first two attempts
  because **the crontab overwrites `slot-cron-ff-pull.sh` in the working tree from `origin` every 5 minutes** (the
  managed-cron-file self-pull; "local edits to them are overwritten every tick BY DESIGN"). The edit was silently
  clobbered mid-session. Editing that file requires landing edit→commit→push inside one 5-minute window. Not a bug — but
  an undocumented foot-gun that costs a confusing debug cycle, and precisely the kind of self-healing mechanism that
  fights the person trying to heal it.

- **2026-07-16 (RECOVERED)** — Operator deployed the VM and separately repaired a root-PM divergence (the clone the AO
  backend reads plans from — a second staleness with the same blast radius: a stale plan clone means the backlog the
  fleet works from is stale). Verified rather than trusted: `behind = 0`, all four fixes greppable on the box, and the
  journal + re-forked worker PID prove the running process picked them up at 15:01:12. **The 2026-07-16 dispatch fixes
  executed on the fleet for the first time at that moment** — everything before it was code-shipped-not-running.
  Operator is routing the durable UI-surface + alerting work (todo 3) to a dedicated agent.
