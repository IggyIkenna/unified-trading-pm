---
doc_type: plan
title: AO remediation B — git-health + worker-liveness code chain (sequential, gated behind Plan A)
summary:
  Plan B of the split AO issue-docs remediation (operator ruling 2026-07-23, Q1 = split). The 14 todos here are an
  interdependent chain — the git-health reporter/FF-cron scripts and the worker-liveness code that several todos edit in
  common, plus the shared-doc measurement recorders — so the whole plan runs sequentially to avoid file collisions. It
  is depends_on Plan A because its final sports-closeout audit needs Plan A's plan_health doc_drift routing and the
  docs-reconcile timer to be live first. Zero P0s; the two safety-sensitive backend todos are HELD (Q2).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, git-health, worker-liveness, plan-hygiene, plan-reconcile]
related:
  [
    /plans/active/ao_issue_docs_consolidated_remediation_2026_07_23.md,
    /plans/active/ao_remediation_a_independent_fixes_2026_07_23.md,
    /plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
    /plans/active/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md,
    /plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
  ]
created: 2026-07-23
last_updated: 2026-07-23
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on: ao_remediation_a_independent_fixes_2026_07_23
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "/plan-reconcile AO-scope run 2026-07-23, split per operator ruling Q1; parent
  ao_issue_docs_consolidated_remediation_2026_07_23"
---

# AO remediation B — git-health + worker-liveness code chain (sequential)

> **Split from `ao_issue_docs_consolidated_remediation_2026_07_23` per operator ruling 2026-07-23 (Q1 = split).**
> `sequential: true` because the todos genuinely overlap on files — `slot-git-status-report.sh` is touched by two,
> `slot-cron-ff-pull.sh` by two, `server/worker_liveness/*` by three, and the shared-doc recorders all append to the
> tracker / `ao_residuals`. Serialising the whole plan is the only intra-plan mechanism that prevents two workers
> colliding on one file, and it is also correct on the merits: this is one interdependent chain (the
> `dirty_consecutive_ticks` gate design in the `git_health.py` todo informs the FF-cron todo; the count fix informs the
> instrumentation todo). `depends_on` + `gate_on_depends` hold every todo here until Plan A is fully done, because the
> final sports-closeout audit needs Plan A's `plan_health` doc_drift routing and the `docs-reconcile` timer live.

> **CAVEAT the gate costs throughput** — the git-health/liveness fixes wait for Plan A's doc cleanups even though they
> do not depend on them. That is the accepted price of keeping this to two plans (operator ruling Q1). If more
> throughput is wanted later, the one genuinely-gated todo (the sports audit) can be split into its own tiny Plan C so
> this chain runs concurrently with Plan A.

## Codex SSOTs

- `/codex/05-infrastructure/per-tab-worktrees.md` — slot clones, FF-pull cron, the dirty/liveness discriminator
- `/codex/04-architecture/agent-orchestrator-worker-liveness.md` — watchdog, reaper, git-surfaces pass
- `/codex/12-agent-workflow/canonical-plan-flow.md` — corrected 2026-07-23; `assigned_vm` is `{planning, NA}`

## Todos (execute in this order — sequential)

- [ ] [INFRA] P1. Re-derive `dirty_files` in `scripts/dev/slot-git-status-report.sh` from the sample loop's kept
      non-blank lines so the count can never exceed the captured sample. Build the count from the same array the sample
      loop populates (single source of truth), not an independent `wc -l` on the raw capture — this makes the observed
      `dirty_files=1` + empty-`dirty_files_sample` fingerprint structurally impossible regardless of what upstream
      artifact injects a stray count. Cause-agnostic by design: review proved with `cat -A`/hexdump that the tree emits
      ZERO bytes while the reporter posts 1, so do NOT chase the blank-line theory. **Gate**: a unit/bats test asserting
      a clean tree can never yield `dirty_files>0`, and that `dirty_files` always equals the captured sample length.
- [ ] [INFRA] P2. Add the `df>0 with an empty sample` instrumentation to `scripts/dev/slot-git-status-report.sh` — when
      the computed count is non-zero but the sample array is empty, log the raw captured porcelain bytes via `cat -A` to
      the reporter's own log so the next occurrence pins the wrapper trigger. This is the diagnostic half of the todo
      above; it must survive even after the count is made structurally safe. **Gate**: forcing the condition in a test
      emits the raw-bytes log line.
- [ ] [INFRA] P2. Mirror the same single-source count-integrity fix onto the FF-cron dirty gate in
      `scripts/dev/slot-cron-ff-pull.sh` so a phantom count can never trip `[skip:dirty]` and starve FF-pull. The cron
      computes dirt with the same `git status --porcelain` pattern as the reporter, so it hits the same phantom
      independently. **Gate**: a test where a clean tree yields `ff_pull_last_result != skip:dirty`.
- [ ] [INFRA] P2. Gate the `not_clean_since` CLEAR and the sync-nudge in `server/routes/git_health.py` on
      `dirty_consecutive_ticks >= 2` so one clean blip cannot reset the age a genuinely long-dirty repo has accumulated.
      The reporter already sends the field; this is a server-side change using data that already arrives. **Gate**: a
      unit test proving a single clean poll between two dirty polls does NOT reset `not_clean_since`.
- [ ] [INFRA] P2. Extend that same `dirty_consecutive_ticks >= 2` gate to the FF-pull skip decision in
      `scripts/dev/slot-cron-ff-pull.sh` so a one-tick phantom dirty can never skip an FF-pull whatever produced it. Do
      NOT re-hunt a reporter-internal race first — `agent-orchestrator@529b0dc` (cross-host row clobber, live) is a
      complete mechanism for the all-repos-simultaneous fingerprint and the phantom has not reproduced since. **Gate**:
      a test asserting a single-tick all-repos-dirty observation neither clears `not_clean_since` nor causes an FF-pull
      skip.
- [ ] [INFRA] P2. Verify the unexplained `dirty_files=2172` row for `unified-trading-pm` on host `ip-172-31-0-185` slot
      0 by running `git status --porcelain | wc -l` in that clone and recording which it is. Every non-clean row on the
      `hk` host was verified REAL file-for-file, but this host was unreachable from the audit session, so it is the one
      open doubt — either a genuinely wrecked checkout (its own problem, since that clone can never FF while dirty) or
      the phantom surviving at a new magnitude. **Gate**: the measured count recorded in the issue doc with an explicit
      real-or-phantom verdict.
- [ ] [BACKEND] P2. Add a periodic dirty-resolution sweep to the worker-liveness watchdog that runs independently of any
      spawn attempt. Every caller of `resolve_dirty_state`/`commit_and_push_dirty_repos` today is spawn or respawn time
      (`spawn_slot`, `_do_spawn`, the `slots_ops` pre-spawn gate, `_respawn`), so a dirty slot nobody tries to spawn
      into stays dirty forever. Reuse those same helpers plus the liveness discriminator — dead or expired
      `.agent-claim` means inherit and commit; a live claim or mtime under 120s means PROTECT. **Gate**: a
      deliberately-idle dirty slot with no tmux and an expired claim is inherited within one sweep interval, evidenced
      by a resolution activity row with NO adjacent spawn event.
- [ ] [INFRA] P2. Escalate the liveness watchdog from soft-kick to hard-kill plus respawn after N consecutive frozen
      observations, and make the counter survive the reset that defeated it. `kick_escalation_threshold` already exists
      and shipped 2026-07-09, but the 2026-07-21 incident (55 kicks in 3h, only 7 counted as `worker_kick_failed`) is
      live proof it did not trip — `ping_advanced`/`post_class=="working"` kept resetting `_consecutive_kick_failures`
      to 0 before it reached the threshold. Fix the reset condition, not the threshold value. **Gate**: a test where a
      worker that keeps answering pings while making no progress still escalates to hard-kill.
- [ ] [INFRA] P2. Add a reclaim-and-push path for a killed or idle slot whose worktree holds committed-but-unpushed
      work. `orphan_reap.py` reaps processes and tmux only — its own docstring says so, and it contains no git logic —
      while `_maybe_send_sync_nudge` merely enqueues a slot message, which is a no-op on a dead worker. Note
      `agent-orchestrator@529b0dc` does NOT cover this: it is a git-status keying fix, not a push path. **Gate**: a slot
      killed with local commits ahead of origin has them pushed (or inherited) without a human touching the box,
      evidenced by the commits appearing on `origin/live-defi-rollout`.
- [ ] [BACKEND] P3. Root-cause slot 4's elevated short-lived-orphan rate, or record an explicit accept-as-cadence
      verdict with the comparison data. Compare `slot_resume_respawned`, `autospawn_failed`, `watchdog_slot_killed` and
      `tmux_session_lost` rates for slot 4 against the other slots NORMALISED PER DISPATCH — raw counts are misleading
      because slot 4's dispatch volume differs — over a multi-day window. The periodic orphan sweep already reaps the
      symptom within ~60s, so this is about knowing whether slot 4 is structurally different. **Gate**: either a fixed
      cause (code diff plus a measured 24h orphan-rate drop) or a recorded cadence verdict citing the per-dispatch
      comparison. Silence is not an outcome.
- [ ] [REVIEW] P2. Correct the "0 dead links" claim in `ao_open_issues_consolidated_close_out_2026_07_17.md`'s
      2026-07-18 Progress Log to state the sweep's actual scope. The cited sweep commits landed roughly ten hours AFTER
      the commit that deleted these files and covered different documents, so the line reads as fleet-wide proof when it
      is not — which is exactly what stops the next person re-running the one-second grep. **Gate**: the entry names
      which commits swept what and links the issue doc for the batch it missed.
- [ ] [BACKEND] P3. Root-cause the 2026-07-12 degradation onset — `worker_polling_dead` going 0 to 587 and the
      spawn-to-dispatch ratio moving from 0.6:1 to 44:1 on that date — or record an explicit not-worth-excavating
      decision. The mechanism itself is fixed; what was never explained is why it STARTED that day, which means a
      recurrence would be invisible until it costs again. One `activity_log` excavation pass is enough. **Gate**: a
      named cause with activity-log evidence, or a recorded decision — not silence. NOTE: this item is ALSO open in
      `ao_open_issues_consolidated_close_out_2026_07_17.md` Phase 5; close both or collapse them into one owner first.
- [ ] [INFRA] P2. Re-test the l2_book task-row divergence once `l2_book_microstructure_capture_2026_07_13.md` returns to
      `assigned_vm: planning`, confirming every open todo gets a task row. The original measurement is currently VOID,
      not resolved — that plan is `assigned_vm: NA` after the fleet-wide dispatch pause, so absent task rows are correct
      behaviour rather than the reopen-drop defect. If the BLOCKED todos are again absent while the plan IS ingested,
      the defect is live. **Gate**: the per-todo task-row comparison recorded with an explicit live-or-clear verdict.
- [ ] [REVIEW] P2. Re-run the sports closeout hygiene audit end-to-end once the plan-quality defense lines are live and
      confirm all four lines fire. This is gated on the two todos above plus the hard-fail wiring; do not start it
      before they land. **Gate**: the audit output shows each of the four defense lines producing its expected signal,
      recorded in the issue doc.

## Progress Log

- **2026-07-23**: Authored by splitting `ao_issue_docs_consolidated_remediation_2026_07_23` per operator ruling Q1
  (split for parallelism) + Q2 (hold the 2 safety-sensitive backend todos). Born `status: active`,
  `assigned_vm: planning` — dispatchable to the AO fleet. The parent plan is retained as the holding/index doc for the 6
  non-dispatched items.
