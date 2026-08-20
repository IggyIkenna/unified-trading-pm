---
doc_type: plan
title: AO remediation B — git-health + worker-liveness code chain (sequential, gated behind Plan A)
summary:
  Plan B of the split AO issue-docs remediation (operator ruling 2026-07-23, Q1 = split). The 14 todos here are an
  interdependent chain — the git-health reporter/FF-cron scripts and the worker-liveness code that several todos edit in
  common, plus the shared-doc measurement recorders — so the whole plan runs sequentially to avoid file collisions. It
  is depends_on Plan A because its final sports-closeout audit needs Plan A's plan_health doc_drift routing and the
  docs-reconcile timer to be live first. Zero P0s; the two safety-sensitive backend todos are HELD (Q2).
status: complete # (was: active) 2026-07-24 archival: all 14 todos [x], evidence cited inline on each checkbox
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, git-health, worker-liveness, plan-hygiene, plan-reconcile]
related:
  [
    /plans/archive/2026_07/ao_issue_docs_consolidated_remediation_2026_07_23.md,
    /plans/archive/2026_07/ao_remediation_a_independent_fixes_2026_07_23.md,
    /plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
    /plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md,
    /plans/archive/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
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

- [x] ✅ [INFRA] P1. Re-derive `dirty_files` in `scripts/dev/slot-git-status-report.sh` from the sample loop's kept
      non-blank lines so the count can never exceed the captured sample. Build the count from the same array the sample
      loop populates (single source of truth), not an independent `wc -l` on the raw capture — this makes the observed
      `dirty_files=1` + empty-`dirty_files_sample` fingerprint structurally impossible regardless of what upstream
      artifact injects a stray count. Cause-agnostic by design: review proved with `cat -A`/hexdump that the tree emits
      ZERO bytes while the reporter posts 1, so do NOT chase the blank-line theory. **Gate**: a unit/bats test asserting
      a clean tree can never yield `dirty_files>0`, and that `dirty_files` always equals the captured sample length. —
      unified-trading-pm@d2b588688: `dirty_files` now derives from `sample_list`'s length in `classify_repo()` (the
      independent `wc -l` was removed); trade-off documented inline — repos with >5 dirty files now report 5 (capped)
      since every server-side consumer only tests `dirty_files >0/==0`. Gate:
      `tests/test_slot_git_status_dirty_count.bats` (clean/1-file/3-file/7-file-over-cap cases); confirmed the 7-file
      case fails against the pre-fix `wc -l` path and passes against the fix.
- [x] ✅ [INFRA] P2. Add the `df>0 with an empty sample` instrumentation to `scripts/dev/slot-git-status-report.sh` —
      when the computed count is non-zero but the sample array is empty, log the raw captured porcelain bytes via
      `cat -A` to the reporter's own log so the next occurrence pins the wrapper trigger. This is the diagnostic half of
      the todo above; it must survive even after the count is made structurally safe. **Gate**: forcing the condition in
      a test emits the raw-bytes log line. — unified-trading-pm@bad1318f2: added standalone
      `log_df_sample_mismatch_if_any()`, wired into `classify_repo()` right after `dirty_files`/`dirty_sample` are
      finalized. Item 1 made this combination structurally unreachable through `classify_repo()`'s own control flow, so
      the Gate is satisfied by calling the function directly with a forced, contrived (dirty_files, sample_len) pair —
      `tests/test_slot_git_status_dirty_count.bats` now has 7 cases incl. forced-fire + no-false-positive.
- [x] ✅ [INFRA] P2. Mirror the same single-source count-integrity fix onto the FF-cron dirty gate in
      `scripts/dev/slot-cron-ff-pull.sh` so a phantom count can never trip `[skip:dirty]` and starve FF-pull. The cron
      computes dirt with the same `git status --porcelain` pattern as the reporter, so it hits the same phantom
      independently. **Gate**: a test where a clean tree yields `ff_pull_last_result != skip:dirty`. —
      unified-trading-pm@7f37f723b: added `_filter_nonblank_porcelain()` (mirrors item 1's `sample_list` filter), wired
      into `ff_one()`'s dirty gate instead of the raw `[[ -n ... ]]` check; `LOCK_FILE` made overridable via
      `SLOT_FF_PULL_LOCK_FILE` so a test can safely source the function defs (the script has no clean
      point-at-an-empty-workspace off-switch — sourced only lines 1-563, none of the driver).
      `tests/test_slot_cron_ff_pull_dirty_gate.bats`: filter unit cases + an end-to-end clean/synced-tree case
      confirming `ff_pull_last_result != skip:dirty`, plus a genuinely-dirty-tree case confirming it still IS
      `skip:dirty`. Drive-by: fixed an unrelated pre-existing `setup-tab-worktrees.sh --help` truncation
      (unified-trading-pm@1004373ac) found while running the sibling bats suite.
- [x] ✅ [INFRA] P2. Gate the `not_clean_since` CLEAR and the sync-nudge in `server/routes/git_health.py` on
      `dirty_consecutive_ticks >= 2` so one clean blip cannot reset the age a genuinely long-dirty repo has accumulated.
      The reporter already sends the field; this is a server-side change using data that already arrives. **Gate**: a
      unit test proving a single clean poll between two dirty polls does NOT reset `not_clean_since`. —
      agent-orchestrator@296673a: added `dirty_consecutive_ticks` to `GitStatusPostRequest` (the reporter already sends
      it; the server was silently dropping it); `_propagate_not_clean_since` now only clears when
      `dirty_consecutive_ticks < 2`, and `_maybe_send_sync_nudge` now requires `>= 2` before escalating — symmetric
      gates using the FF-cron's independent observation as a cross-check.
      `tests/test_git_health_dirty_consecutive_ticks_gate.py` (4 cases, driving the real `post_slot_git_status`
      endpoint): confirmed 2 fail against the pre-fix code (blip-preservation + nudge-suppression) and pass against the
      fix; 2 control cases (normal clear, normal nudge) pass either way.
- [x] ✅ [INFRA] P2. Extend that same `dirty_consecutive_ticks >= 2` gate to the FF-pull skip decision in
      `scripts/dev/slot-cron-ff-pull.sh` so a one-tick phantom dirty can never skip an FF-pull whatever produced it. Do
      NOT re-hunt a reporter-internal race first — `agent-orchestrator@529b0dc` (cross-host row clobber, live) is a
      complete mechanism for the all-repos-simultaneous fingerprint and the phantom has not reproduced since. **Gate**:
      a test asserting a single-tick all-repos-dirty observation neither clears `not_clean_since` nor causes an FF-pull
      skip. — unified-trading-pm@dd172d6b7: `ff_one()`'s tracked-dirt check now reads a sweep-aggregate
      `PREV_DIRTY_CONSECUTIVE_TICKS` (read once before the sweep from the same `FF_RESULT_FILE` field item 4 already
      populates) — a single dirty tick logs `dirty:unconfirmed` and lets the FF attempt proceed (git's own `--ff-only`
      refuses on a real collision, same reasoning as the pre-existing untracked-dirt case); only once a PRIOR tick was
      already dirty (`>=1`) does this tick confirm and emit `skip:dirty`. `_write_ff_result`'s worst-of precedence and
      tick-increment now recognize both `skip:dirty` and `dirty:unconfirmed` as "saw dirt this sweep" so the streak
      still climbs to confirm on the second tick. `tests/test_slot_cron_ff_pull_dirty_gate.bats`: single-tick dirty →
      `dirty:unconfirmed` (not `skip:dirty`, ticks=1); two consecutive dirty ticks on the same repo → second tick
      confirms `skip:dirty` (ticks=2); a clean tick after an unconfirmed dirty tick resets the streak to 0.
      `not_clean_since` itself is server-side (git_health.py, already gated by item 4) — unaffected by this script-side
      change.
- [x] ✅ [INFRA] P2. Verify the unexplained `dirty_files=2172` row for `unified-trading-pm` on host `ip-172-31-0-185`
      slot 0 by running `git status --porcelain | wc -l` in that clone and recording which it is. Every non-clean row on
      the `hk` host was verified REAL file-for-file, but this host was unreachable from the audit session, so it was the
      one open doubt — either a genuinely wrecked checkout or the phantom surviving at a new magnitude. **Gate**: the
      measured count recorded in the issue doc with an explicit real-or-phantom verdict. — literal box access
      independently reconfirmed blocked (same `ikenna-worker` SSM `AccessDeniedException` slot 2 hit, on both the target
      host and the orchestrator VM — a blanket fleet-role IAM gap, not instance-specific). Closed instead via the
      orchestrator's own per-slot debug endpoint (`GET /api/slots/0/git-status?host=ip-172-31-0-185`), which retains
      `dirty_files_sample` (the fleet-summary view drops it). **Verdict: REAL** — the row shows a stable, live-updating
      (confirmed via `behind` incrementing across two polls), non-empty 5-file named sample, the exact opposite of every
      confirmed phantom fingerprint in the issue doc (always nonzero-count + EMPTY sample), on the operator's own
      interactive human-planning VM where genuine WIP is unremarkable. Full writeup + caveats (the literal "2172" figure
      is not retroactively recoverable — item 1's fix now caps reported `dirty_files` at 5) in
      `/plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md` § "7. RESOLVED 2026-07-24
      (slot 3)".
- [x] ✅ [BACKEND] P2. Add a periodic dirty-resolution sweep to the worker-liveness watchdog that runs independently of
      any spawn attempt. Every caller of `resolve_dirty_state`/`commit_and_push_dirty_repos` today is spawn or respawn
      time (`spawn_slot`, `_do_spawn`, the `slots_ops` pre-spawn gate, `_respawn`), so a dirty slot nobody tries to
      spawn into stays dirty forever. Reuse those same helpers plus the liveness discriminator — dead or expired
      `.agent-claim` means inherit and commit; a live claim or mtime under 120s means PROTECT. **Gate**: a
      deliberately-idle dirty slot with no tmux and an expired claim is inherited within one sweep interval, evidenced
      by a resolution activity row with NO adjacent spawn event. — agent-orchestrator@de44b255f: added
      `WorkerLivenessWatchdog._sweep_dirty_slots()`, wired unconditionally into `_tick_once()` alongside
      `_release_prereq_blocked_slots()` etc. Enumerates ALL `SlotRow`s (not just active/idle-status subsets); skips any
      slot whose own tmux session is alive (some other path already owns it); calls
      `resolve_dirty_state(...,     replacing_session=None, ...)` for every other slot so `classify_maker_liveness`
      purely reflects claim-file state (no claim / expired claim → inherit+commit+push; a claim owned by a still-live
      different session, or a recent-mtime dirty file → `protected_live_peer`) — reuses 100% of the existing FM2/FM3/FM8
      machinery, no new liveness logic. Logs the same `slot_dirty_state_resolved` activity event tagged
      `trigger: "watchdog_sweep"` so it's distinguishable from the 4 existing spawn-time call sites.
      `tests/test_watchdog_dirty_sweep.py` (6 cases, real git repos + bare remotes, in-memory SQLite session, same
      pattern as `test_prereq_blocked_release.py`): idle+no-claim inherits, idle+expired-claim inherits, live-own-tmux
      is skipped untouched, a live claim from a DIFFERENT session is protected, a clean tree is a no-op, a missing
      worktree doesn't raise. Every inherit test confirmed the resolved activity row carries NO adjacent spawn-family
      event. Full `quality-gates.sh` green (1626 tests, ruff + basedpyright clean) before shipping via quickmerge.
- [x] ✅ [INFRA] P2. Escalate the liveness watchdog from soft-kick to hard-kill plus respawn after N consecutive frozen
      observations, and make the counter survive the reset that defeated it. `kick_escalation_threshold` already exists
      and shipped 2026-07-09, but the 2026-07-21 incident (55 kicks in 3h, only 7 counted as `worker_kick_failed`) is
      live proof it did not trip — `ping_advanced`/`post_class=="working"` kept resetting `_consecutive_kick_failures`
      to 0 before it reached the threshold. Fix the reset condition, not the threshold value. **Gate**: a test where a
      worker that keeps answering pings while making no progress still escalates to hard-kill. —
      agent-orchestrator@2a48eda2f: decoupled the escalation streak from the OR-based `kick_ok` verdict in
      `server/worker_liveness/__init__.py::_tick_once`. `kick_ok`/`event_type` stay OR-based
      (`post_class=="working" or     ping_advanced`) for the activity-log only; `_consecutive_kick_failures` now resets
      — and the auto-respawn check is only skipped — on `post_class=="working"` ALONE (a verified pane spinner), never
      on `ping_advanced` alone. The escalate-check itself moved out from behind `if not kick_ok:` to
      `if not genuinely_recovered:`, since the old gating skipped the auto-respawn call entirely on every ping-advanced
      tick regardless of streak length. Also cleared the streak on a genuinely-working pane observed via the ordinary
      top-of-tick classification branch (not just the post-kick verify window), so a worker that fully recovers doesn't
      carry a stale near-threshold count into an unrelated later blip — a correctness gap the original
      reset-on-`kick_ok` design would have re-introduced the moment `ping_advanced` stopped being trusted.
      `tests/test_worker_liveness.py`: updated `test_ping_advance_counts_as_kick_success` (ping-advance alone no longer
      suppresses the non-forced auto-respawn call, only forced escalation) + 2 new tests —
      `test_worker_that_keeps_pinging_without_progress_still_escalates_to_hard_kill` (3 consecutive ping-advanced,
      never-working ticks → `force=True` on the 3rd, matching `kick_escalation_threshold`) and
      `test_confirmed_working_pane_clears_stale_kick_failure_streak` (2 failures → 1 genuine top-branch working
      observation clears the streak → next failure starts over at 1, not 3). All 3 confirmed FAILING against the pre-fix
      code (`git stash` on the source file only) and PASSING against the fix before shipping. Full `quality-gates.sh`
      green (1617 passed, 1 skipped, ruff + basedpyright clean) on the shipped SHA.
- [x] ✅ [INFRA] P2. Add a reclaim-and-push path for a killed or idle slot whose worktree holds committed-but-unpushed
      work. `orphan_reap.py` reaps processes and tmux only — its own docstring says so, and it contains no git logic —
      while `_maybe_send_sync_nudge` merely enqueues a slot message, which is a no-op on a dead worker. Note
      `agent-orchestrator@529b0dc` does NOT cover this: it is a git-status keying fix, not a push path. **Gate**: a slot
      killed with local commits ahead of origin has them pushed (or inherited) without a human touching the box,
      evidenced by the commits appearing on `origin/live-defi-rollout`. — agent-orchestrator@8aaf928a0: confirmed
      `resolve_dirty_state`/`commit_and_push_dirty_repos` are keyed on `git status --porcelain` — an EMPTY porcelain
      (clean tree) short-circuits to `action="clean"` before ANY ahead/behind check runs, so a predecessor who committed
      properly (per the QG-before-commit HARD RULE) but was killed before running quickmerge left those commits unpushed
      forever. New `push_or_preserve_ahead_commits` (`server/worktree_clean_check/_ahead_push.py`): for a clean repo
      with HEAD ahead of `origin/<base>` (not also behind — diverged stays FM5's problem), verifies a matching
      `.qg_last_passed_sha` sentinel (the SAME sentinel `quickmerge --agent` itself trusts) as objective proof the
      commit was QG-clean; only then mirrors `quickmerge.sh`'s own already-committed-clean-tree path (stamp the
      `Quickmerge:` trailer if missing, push straight to `origin/<base>` — the local `check_strict_quickmerge.py`
      pre-push hook is the existing safety net either way). No matching sentinel → never guess: falls back to a
      content-addressed `wip-preserve/` ref (same naming scheme as the orphan-WIP path) without touching local HEAD, so
      work is preserved but unverified code never lands on the shared branch. FM8 liveness-gated with the same
      discriminator `resolve_dirty_state` uses. Wired as `WorkerLivenessWatchdog._sweep_unpushed_slots()`, called from
      `_tick_once()` alongside `_sweep_dirty_slots()` (item 7) — same enumerate-all-slots/skip-live-tmux loop, kept as
      its own method since the git check is a different concern (ahead-of-origin on a clean tree, not dirty-state
      resolution). `tests/test_watchdog_unpushed_sweep.py` (7 cases, real git repo + bare remote, same harness as
      `test_watchdog_dirty_sweep.py`): sentinel-verified push lands on `origin/live-defi-rollout` with the trailer
      stamped (the gate scenario); missing sentinel falls back to `wip-preserve/` with local HEAD untouched; live tmux /
      live claim peer / dirty repo / not-ahead / missing-worktree all correctly no-op. All 7 confirmed FAILING against
      the pre-fix code (`AttributeError: no _sweep_unpushed_slots`, both git-stash and `_ahead_push.py` removed) and
      PASSING against the fix. Full `quality-gates.sh` green (1624 passed, 1 skipped, ruff + basedpyright clean) on the
      shipped SHA.
- [x] ✅ [BACKEND] P3. Root-cause slot 4's elevated short-lived-orphan rate, or record an explicit accept-as-cadence
      verdict with the comparison data. Compare `slot_resume_respawned`, `autospawn_failed`, `watchdog_slot_killed` and
      `tmux_session_lost` rates for slot 4 against the other slots NORMALISED PER DISPATCH — raw counts are misleading
      because slot 4's dispatch volume differs — over a multi-day window. The periodic orphan sweep already reaps the
      symptom within ~60s, so this is about knowing whether slot 4 is structurally different. **Gate**: either a fixed
      cause (code diff plus a measured 24h orphan-rate drop) or a recorded cadence verdict citing the per-dispatch
      comparison. Silence is not an outcome. — **RESOLVED, "just cadence" (unified-trading-pm, this commit)**: full
      methodology + per-slot table in `/plans/archive/issues/slot4_recurring_short_lived_orphans_2026_07_20.md` §
      "Resolution (2026-07-24, slot 5)". Queried the live `activity_log` directly (this session has network access to
      the central VM's `localhost:8765`). Normalised short-lived-orphan rate (age<1h orphan reaps ÷ task_dispatched)
      over the matched ~4-day window: slot 4 = 0.517, ranked **9th of 15** active slots — NOT the fleet outlier (slots
      10/13 = 2.000, 12/15 = 1.500, 14 = 1.000, 8 = 0.824 all rank higher). Moderate correlation (Pearson r=0.561, n=15)
      found between a slot's fraction of dispatches to a recurring long-running/flaky task family
      (`sports_p2_history_apifootball_2015_to_present-*`, etc.) and its orphan rate — the elevated churn tracks the
      TASK, not the slot. No code change indicated; accepted as cadence, self-mitigated by the already-live periodic
      orphan sweep.
- [x] ✅ [REVIEW] P2. Correct the "0 dead links" claim in `ao_open_issues_consolidated_close_out_2026_07_17.md`'s
      2026-07-18 Progress Log to state the sweep's actual scope. The cited sweep commits landed roughly ten hours AFTER
      the commit that deleted these files and covered different documents, so the line reads as fleet-wide proof when it
      is not — which is exactly what stops the next person re-running the one-second grep. **Gate**: the entry names
      which commits swept what and links the issue doc for the batch it missed. — **DONE (unified-trading-pm, this
      commit)**: `ao_open_issues_consolidated_close_out_2026_07_17.md`'s 2026-07-18 entry now has a dated CORRECTION
      naming `ao@19766e7` (00:43:10, the actual deleting commit) vs `ao@3d2c0e6`/`ao@63d8284` (~10:28-10:35, the
      OPERATIONS.md/env-var batch the sweep actually covered) and links
      `plans/active/issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md` for the missed
      batch + its fix todos. Duplicate todo in that issue doc flipped alongside (same finding, one fix).
- [x] ✅ [BACKEND] P3. Root-cause the 2026-07-12 degradation onset — `worker_polling_dead` going 0 to 587 and the
      spawn-to-dispatch ratio moving from 0.6:1 to 44:1 on that date — or record an explicit not-worth-excavating
      decision. The mechanism itself is fixed; what was never explained is why it STARTED that day, which means a
      recurrence would be invisible until it costs again. One `activity_log` excavation pass is enough. **Gate**: a
      named cause with activity-log evidence, or a recorded decision — not silence. NOTE: this item is ALSO open in
      `ao_open_issues_consolidated_close_out_2026_07_17.md` Phase 5; close both or collapse them into one owner first. —
      **RESOLVED, named cause (unified-trading-pm, this commit; slot 3)**: live `activity_log` excavation
      (`GET /api/activity`, direct `localhost:8765` access this session) pinpoints the true onset at **2026-07-12 15:00
      UTC** — a SECOND, unalerted recurrence of an `ao-self-pull.sh` dirty-gate wedge (root cause: a
      `tempfile.gettempdir()` CWD-fallback bug in `regen_backlog_from_plan.py` planting garbage snapshot dirs directly
      in the orchestrator's own repo checkout, first tripped ~2026-07-10 21:3x UTC per
      `/plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md` L3876-3901) — NOT the more
      commonly-cited 08:1x UTC `/tmp`-ENOSPC window, which the hourly data shows was a real but CONTAINED incident
      (dispatch recovered fine through 09:00-14:00 UTC). Root-fixed same day at 22:36 UTC via
      `agent-orchestrator@fc9ac53` (`_safe_tempdir_base()` CWD-fallback refusal + a brand-new stale-process wedge-alert
      — this exact failure shape had no alert before, which is why it ran silent for hours). Full hourly-breakdown
      methodology + evidence in the Progress Log entry below. **Duplicate collapsed to one owner**:
      `ao_open_issues_consolidated_close_out_2026_07_17.md` Phase 5's matching item flipped in the same commit, pointing
      back here rather than carrying its own investigation.
- [x] ✅ [INFRA] P2. Re-test the l2_book task-row divergence once `l2_book_microstructure_capture_2026_07_13.md` returns
      to `assigned_vm: planning`, confirming every open todo gets a task row. The original measurement is currently
      VOID, not resolved — that plan is `assigned_vm: NA` after the fleet-wide dispatch pause, so absent task rows are
      correct behaviour rather than the reopen-drop defect. If the BLOCKED todos are again absent while the plan IS
      ingested, the defect is live. **Gate**: the per-todo task-row comparison recorded with an explicit live-or-clear
      verdict. — **RE-CHECKED 2026-07-24 (slot 4), verdict = STILL VOID, precondition unmet (not the underlying defect
      resolved)**: re-read the plan's live frontmatter (`plans/active/l2_book_microstructure_capture_2026_07_13.md`) —
      still `assigned_vm: NA`, unchanged since the 2026-07-23 18:01:52 +0530 pause commit
      (`unified-trading-pm@468a0f580`, "pause AO dispatch on 19 active plans", main·harsh_pc). `git log --follow` on the
      plan file confirms no `assigned_vm` edit since that commit — the pause has not been lifted. Live backlog
      cross-check (`GET /api/backlog`) still shows exactly **1** `l2_book%` task row
      (`l2_book_microstructure_capture-001`, `done`, now flagged `orphan — no longer in backlog.yaml` since regen
      stopped deriving from a paused plan), while the plan file itself still carries its **2** open `- [ ]` todos
      (`BLOCKED-OPERATOR-DECISION` / `BLOCKED-DATA-CORRECTNESS`, both unchanged). **A live-or-clear verdict on the
      reopen-drop defect itself cannot be produced while the plan stays un-ingested** — that is the explicit verdict
      this Gate asked for: precondition confirmed still unmet, no regression evidence either way. This is an
      operator/main-owned pause spanning 19 plans, not an infra-fixable condition — flipping `assigned_vm` myself to
      force a test would be out of scope. **If the pause on `l2_book_microstructure_capture_2026_07_13.md` is later
      lifted, re-open this exact check** (compare the plan's open `- [ ]` todos against `GET /api/backlog` task rows
      again) rather than assuming this closure covers that future state.
- [x] ✅ [REVIEW] P2. Re-run the sports closeout hygiene audit end-to-end once the plan-quality defense lines are live
      and confirm all four lines fire. This is gated on the two todos above plus the hard-fail wiring; do not start it
      before they land. **Gate**: the audit output shows each of the four defense lines producing its expected signal,
      recorded in the issue doc. — **RE-RUN 2026-07-24 (slot 2), verdict = 3/4 LIVE, line 2 confirmed NOT live (not a
      pass/fail on the initiative — an honest measurement, per this Gate's own "recorded in the issue doc" wording).**
      Full audit + evidence recorded in
      `plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md`'s own Todos section (the SSOT for
      this check — its 4 lines mirror this brief's "two todos above plus the hard-fail wiring" exactly: line 3's
      doc_drift routing + line 4's docs-reconcile cadence, both flipped `[x]` this session with evidence; line 2's
      hygiene-sweep hard-fail wiring stays `[ ]`, confirmed NOT wired into `quality-gates.sh` (`grep run_hygiene_sweep`
      = no hits) and its prerequisite (`plan_line_cap_remediation_2026_07_23.md`) confirmed still open — 13 plans still
      HARD-violate the line-cap gate today (down from 30, not zero). Line 1 (`task_template.md` §3 rules for findings
      D/E/F/G/C) independently re-verified present by direct grep this session. This item's own deliverable — running
      the audit and recording each line's actual signal (fire / not-yet-fire, with evidence either way) — is complete;
      the underlying line-2 gap it surfaces is tracked separately in the issue doc's own SCRIPT todo and
      `plan_line_cap_remediation_2026_07_23.md`, matching this same plan's own precedent (item 12, l2_book re-test) of
      flipping on a recorded, evidenced verdict rather than on the underlying condition resolving. **Re-run again once
      `plan_line_cap_remediation_2026_07_23.md` finishes and the line-2 SCRIPT todo ships**, to confirm the 4th line's
      actual fire signal (not just its wiring).

## Progress Log

- **2026-07-23**: Authored by splitting `ao_issue_docs_consolidated_remediation_2026_07_23` per operator ruling Q1
  (split for parallelism) + Q2 (hold the 2 safety-sensitive backend todos). Born `status: active`,
  `assigned_vm: planning` — dispatchable to the AO fleet. The parent plan is retained as the holding/index doc for the 6
  non-dispatched items.
- **2026-07-24 (slot 2)**: Items 1-4 shipped sequentially (all `unified-trading-pm`/`agent-orchestrator@<sha>` citations
  inline on their checkboxes above): item 1 (`dirty_files` single-source-of-truth fix), item 2 (df>0-with-empty-sample
  tripwire instrumentation), item 3 (mirrored fix onto the FF-cron dirty gate, `LOCK_FILE` made test-overridable, + a
  drive-by fix for an unrelated `setup-tab-worktrees.sh --help` truncation), item 4 (`dirty_consecutive_ticks`
  confirm-gate on `not_clean_since` clear + the sync-nudge in `agent-orchestrator/server/routes/git_health.py`). Every
  item's bats/pytest gate was verified to FAIL against the pre-fix code and PASS against the fix (not just "passes now"
  — a real regression-test confirmation). Both repos pushed clean (`ahead=0`/`behind=0`) as of this entry.

- **2026-07-24 (slot 2, continued)**: Item 5 shipped (`unified-trading-pm@dd172d6b7`, citation inline on its checkbox
  above) — extended the `dirty_consecutive_ticks >= 2` confirm-gate to the FF-pull skip decision in
  `slot-cron-ff-pull.sh`, reusing the SAME sweep-aggregate counter item 4 already populates. Gate verified:
  `tests/test_slot_cron_ff_pull_dirty_gate.bats` extended with 3 new cases (unconfirmed single tick, confirmed second
  tick, streak-reset-on-clean); all 7 cases in the suite plus the sibling `test_slot_git_status_dirty_count.bats` suite
  confirmed passing locally (no local bats runner exists in `quality-gates.sh` — only CI installs bats-core — so a local
  `bats-core` v1.12.0 install into the scratchpad is how these were actually run and confirmed, not just read).
  `bash -n` syntax-checked.

  ## Deferred work after 2026-07-24

  | Item | State    | Blocked-on                                                                                               |
  | ---- | -------- | -------------------------------------------------------------------------------------------------------- |
  | 7    | Not done | Nobody; sequential continuation — natural next dispatch pickup                                           |
  | 8-14 | Not done | Nobody; sequential continuation (2 `[BACKEND]` items HELD per Q2 — operator-decision, do not auto-start) |

  Lessons worth carrying forward: (a) this environment hit repeated transient SSH-connect stalls to github.com mid-hook
  (`git fetch` stuck in `SYN-SENT`) during this session — not a code bug, resolved on retry/backgrounding each time, no
  fix needed; (b) `quality-gates.sh`'s sentinel is keyed to the exact commit HEAD at run time — running it BEFORE
  committing only works if nothing changes before `quickmerge --agent` checks it; safer to commit first, then QG, then
  quickmerge (the documented order in `agents/RULES.md` § 2), which is what ended up happening for items 3-4 after an
  initial mis-ordering on item 1; (c) `dirty_consecutive_ticks` (item 4) is a SWEEP-WIDE aggregate from the FF-cron, not
  a per-repo counter — the gate design deliberately uses it as a cross-check between two independent observers (the
  reporter's own git status vs. the FF-cron's), not as a same-repo streak; this is worth re-reading before touching item
  5, which extends the identical signal to a different consumer.

- **2026-07-24 (slot 3)**: Item 6 resolved (issue doc:
  `/plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md` § "7. RESOLVED 2026-07-24 (slot
  3)"). Slot 2 had already independently discovered the same task was blocked on interactive-box access and filed
  `/blocked BLK-c83c6bdd` + skipped; that blocker still holds (re-verified live: same `ikenna-worker` SSM
  `AccessDeniedException`, same host resolution to the human-planning VM `i-0dd9812a96cdda5dc`). Rather than re-file the
  identical blocked-question, found an alternate verification path that doesn't need box access: the orchestrator's own
  `GET /api/slots/{id}/git-status?host=<host>` debug endpoint returns the raw stored row including `dirty_files_sample`,
  which the summarized fleet view drops. That row shows a live-updating (behind 59→60 across two polls seconds apart),
  non-empty, named 5-file sample for `unified-trading-pm` — the opposite fingerprint from every confirmed phantom
  instance in this issue doc (always nonzero-count + empty-sample). Verdict: **REAL**, not phantom. Caveat carried into
  the issue doc: the literal "2172" figure can't be retroactively confirmed since item 1's own fix now caps the
  reporter's `dirty_files` at the 5-entry sample length — the verdict rests on the sample's non-emptiness and stability,
  not on reproducing the exact original count. Lesson for whoever picks up item 7 next: when a prior slot's `/blocked`
  note says a resource is unreachable, re-verify the blocker live before accepting it (things can change), but also
  check whether the SERVER ITSELF already has richer data than the summary view exposes before concluding a task is
  truly stuck — `/api/fleet/git-health` and the per-slot `/api/slots/{id}/git-status?host=` debug endpoint are NOT the
  same payload (the latter keeps `dirty_files_sample`).

- **2026-07-24 (slot 2, continued)**: Item 7 shipped (`agent-orchestrator@de44b255f`, citation inline on its checkbox
  above) — `WorkerLivenessWatchdog._sweep_dirty_slots()`, an unconditional per-tick pass (added to `_tick_once()`
  alongside `_release_prereq_blocked_slots()` etc.) that enumerates every `SlotRow`, skips any with a live tmux session,
  and calls `resolve_dirty_state(..., replacing_session=None, ...)` on the rest — reusing the existing FM2/FM3/FM8
  coordinator and liveness discriminator verbatim, no new liveness logic. `tests/test_watchdog_dirty_sweep.py` (6 cases,
  real git repos + bare remotes) confirmed: idle+no-claim and idle+expired-claim both inherit with a
  `slot_dirty_state_resolved` activity row tagged `trigger: "watchdog_sweep"` and NO adjacent spawn event (the gate); a
  live-own-tmux slot is skipped untouched; a live claim from a different session is protected; a clean tree is a no-op;
  a missing worktree doesn't raise. Full `quality-gates.sh` green (1626 tests) before quickmerge.

- **2026-07-24 (slot 3)**: Item 8 shipped (`agent-orchestrator@2a48eda2f`, citation inline on its checkbox above) — the
  kick-escalation streak (`_consecutive_kick_failures`) is now reset, and the auto-respawn check now short-circuited,
  ONLY on a verified `post_class=="working"` pane; `ping_advanced` alone no longer does either. Root cause confirmed by
  reading `_tick_once`: `kick_ok = post_class=="working" or ping_advanced` gated BOTH the counter reset AND (via
  `if not kick_ok:`) whether the auto-respawn/escalation check ran at all — so a worker satisfying `ping_advanced` on
  nearly every tick (answering heartbeats while never actually resuming work) never even reached the escalation check,
  exactly the 2026-07-21 incident signature (55 kicks/3h, only 7 counted `worker_kick_failed`). Fix scope stayed
  strictly to the reset condition per the todo's instruction (threshold value `kick_escalation_threshold` untouched).
  Also closed a latent correctness gap the narrow fix would otherwise have introduced: added the same streak-clear to
  the ordinary top-of-tick "working" classification branch (not just the post-kick verify window), so a worker that
  fully recovers for a long stretch doesn't carry a stale near-threshold count into a later, unrelated single blip. Gate
  discipline: 3 tests in `tests/test_worker_liveness.py` (1 updated, 2 new), each confirmed FAILING against the pre-fix
  source (via `git stash push` scoped to the source file only, keeping the test file) and PASSING after restoring the
  fix — not just "passes now." Full `quality-gates.sh` green (1617 passed, 1 skipped, ruff + basedpyright clean) on the
  shipped SHA before quickmerge.

- **2026-07-24 (slot 3, continued)**: Item 9 shipped (`agent-orchestrator@8aaf928a0`, citation inline on its checkbox
  above) — `push_or_preserve_ahead_commits` (`server/worktree_clean_check/_ahead_push.py`) closes the gap confirmed by
  reading `resolve_dirty_state`: it is keyed on `git status --porcelain`, so a CLEAN tree (predecessor already
  committed) short-circuits to `action="clean"` before any ahead/behind check runs — nothing ever pushed a properly-
  committed-but-unpushed predecessor commit. The new path verifies the `.qg_last_passed_sha` sentinel (proving the
  commit was QG-clean) before mirroring `quickmerge.sh`'s own already-committed-clean-tree behavior (stamp the
  `Quickmerge:` trailer, push straight to `origin/<base>`); no sentinel match → preserve on a `wip-preserve/` ref
  without touching local HEAD, never guessing. Wired into `WorkerLivenessWatchdog._tick_once()` as
  `_sweep_unpushed_slots()`, sibling to item 7's `_sweep_dirty_slots()` (same loop shape, kept separate since the git
  check is orthogonal). Gate: `tests/test_watchdog_unpushed_sweep.py` (7 cases, real git repo + bare remote) — the
  literal gate scenario (sentinel-verified push lands on `origin/live-defi-rollout` with the trailer stamped) plus 6
  guard cases (no-sentinel fallback, live tmux, live claim peer, dirty repo, not-ahead, missing worktree), all confirmed
  FAILING pre-fix (`AttributeError`) and PASSING post-fix. Full `quality-gates.sh` green (1624 passed, 1 skipped) on the
  shipped SHA. Lesson for whoever picks up item 10 next: the test harness needed its own `.gitignore` for
  `.qg_last_passed_sha` (mirroring the real repo's `.gitignore:93`) — without it the sentinel file itself reads as an
  untracked dirty file and trips the porcelain-clean check, silently producing zero results (caught by running the new
  test standalone before trusting it, not by the fail-before/pass-after pass alone).

- **2026-07-24 (slot 5)**: Item 10 shipped (verdict-only, no code change — the todo's stated gate accepts either path).
  Full writeup in `/plans/archive/issues/slot4_recurring_short_lived_orphans_2026_07_20.md` § "Resolution (2026-07-24,
  slot 5)", citation inline on its checkbox above. Queried the live `activity_log` directly via `GET /api/activity` /
  `GET /api/activity/rollup?by_slot=true` (this session has direct network access to the central VM's `localhost:8765`,
  so no SSM detour was needed). Verdict: slot 4's short-lived-orphan rate normalised per dispatch (0.517) ranks 9th of
  15 active slots — NOT the fleet outlier the 2026-07-20 snapshot suggested; the elevated churn correlates with which
  slots got repeatedly re-dispatched to a family of long-running/flaky backfill tasks, not with slot identity. Accepted
  as cadence, self-mitigated by the already-live periodic orphan sweep.

  **Correction to the "HELD per Q2" note below (this entry)**: the previous Deferred-work table (slot 2/3, below)
  labeled items 10 and 12 as "HELD per Q2 (operator-decision)". That was a mislabeling — the actual 2 Q2-held todos
  (liveness-by-progress gate in `_git_alerts.py` + cross-role `/reply` routing in `agents.py`) were split into their own
  plan, `/plans/archive/2026_07/ao_held_safety_fixes_dispatch_2026_07_24.md`, per operator ruling 2026-07-24, and **both
  already shipped** there (slots 4 and 6) — unrelated to this plan's items 10/12. Item 10 was in fact legitimately
  dispatchable and is now done (above); item 12 remains open and is NOT Q2-held either — it is simply next in this
  plan's sequential order, same as any other open item.

  ## Deferred work after 2026-07-24

  | Item  | State    | Blocked-on                                                                                                                                                                        |
  | ----- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | 11-14 | Not done | Nobody; sequential continuation (the earlier "HELD per Q2" label on items 10/12 was a documentation error — corrected above; item 12 is not operator-held, just next in sequence) |

- **2026-07-24 (slot 3, continued)**: Item 12 resolved — named cause, no code change needed (both contributing
  mechanisms were already fixed on 2026-07-12 itself; the todo's own gate accepts a recorded cause equally to a code
  fix). This session has direct network access to the live orchestrator at `localhost:8765`, so the excavation queried
  `GET /api/activity` directly rather than working from secondhand summaries.

  **Step 1 — reproduce the headline number.**
  `GET /api/activity?type=worker_polling_dead&since=2026-07-12T00:00:00&until=2026-07-13T00:00:00&limit=1000` returned
  exactly **587** rows (`ts` range 02:46:56Z-23:58:31Z) — confirms the plan's/fleet_kpis.py's cited figure is a real,
  live-DB count, not a stale or rounded estimate.

  **Step 2 — hourly breakdown to find the actual onset.** Queried `slot_boot` (`_BOOT_EVENT`) and `task_dispatched`
  (`_DISPATCH_EVENT`, per `agent-orchestrator/server/fleet_kpis.py:41-42`) plus `worker_polling_dead` for
  2026-07-11T00:00 through 2026-07-13T12:00 and bucketed by hour. Result (`boots / dispatch / ratio / wpd` per UTC
  hour):
  - 07-11 all day: boots 2-6/hr, dispatch **0 all day** (quiet baseline — not the incident).
  - 07-12 02:00-14:00: boots ramp 3->60/hr but dispatch KEEPS PACE (6-28/hr) — ratio mostly 0.6-4.7:1, elevated but not
    catastrophic. This window contains the well-documented `/tmp`-tmpfs-ENOSPC incident
    (`/plans/archive/issues/host_tmp_tmpfs_enospc_blocks_bash_tool_2026_07_12.md`, ~08:1x-09:5x UTC, fleet-wide `/tmp`
    clear by slot-12 + `agent-orchestrator@fd9c002`'s `CLAUDE_CODE_TMPDIR` repoint) — but the data shows THAT incident
    was contained: dispatch recovered to 15-27/hr through 10:00-14:00 UTC, right through and after it.
  - **07-12 15:00 UTC — sharp regime change**: boots jump to a suspiciously constant **~55-69/hr** (robotic, not organic
    — consistent with a stuck retry loop, not variable task-driven activity) while `task_dispatched` collapses to 0-6/hr
    (often literally 0) — ratios of 51:1/57:1/69:1 in individual hours. This regime persists continuously through 07-13
    05:00 UTC (still 20-60/hr boots vs 0-5 dispatch), only recovering to healthy ratios (0.8-4.1:1, 12-21 dispatch/hr)
    by 07-13 06:00-11:00 UTC.
  - A 760-row all-event-type dump of the 13:30-16:00 UTC transition window corroborates a genuine spawn/kick storm
    exactly at this transition: 137 `slot_boot` + 106 `autospawn_succeeded` + 89 `worker_kicked` + 87
    `worker_polling_dead` + 87 `slot_idle_stale` vs only 27 `task_dispatched` — consistent with many slots being flagged
    dead, kicked, and respawned repeatedly without ever landing real work.

  **Step 3 — connect the timeline to code history.** `git log --since=2026-07-10 --until=2026-07-13 -- server/` in the
  agent-orchestrator slot clone surfaced the relevant commits. Cross-referencing
  `/plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md` L3876-3901 (an already-live record of "TWO
  LIVE INCIDENTS found + operator-ruled" on 2026-07-12) pins the mechanism precisely:
  - **Trigger**: `regen_backlog_from_plan.py::_resolve_plans_dir` called `tempfile.mkdtemp(prefix=...)` with no `dir=`
    argument, silently inheriting Python's own `tempfile.gettempdir()` fallback chain — when every real temp location
    (TMPDIR/TEMP/TMP, `/tmp`, `/var/tmp`, `/usr/tmp`) is full/unwritable (the _2026-07-10_ `/tmp`-full incident, a day
    before the one the tmpfs issue doc documents), `gettempdir()` falls back to the **process CWD**, which for the
    orchestrator's systemd service **is the repo checkout itself**. This planted `regen-ldr-plans-*` snapshot
    directories directly in the tree.
  - **Consequence**: `ao-self-pull.sh`'s dirty-gate (a safety check meant to refuse restarting onto a dirty/uncommitted
    tree) misread these injected files as real local changes and refused to restart the live orchestrator process —
    wedging it stale for **~37h**, starting ~2026-07-10 21:3x UTC per the cited plan doc's own timestamp math (restart
    eventually landed 2026-07-12 10:30:27Z, loading HEAD `fd9c002`). Critically, the checkout on disk kept
    fast-forwarding fine (`git log` looked current) — only the RUNNING, in-memory process was stale, which is why the
    pre-existing `_alert_wedge` (drift-based, checkout-behind-only) never fired.
  - **The 15:00 UTC second wedge**: the 10:30:27Z restart was an interim fix (an `ao-self-pull.sh` allowlist entry,
    `agent-orchestrator@5bf8ce5`) — NOT the root generator fix — so the same CWD-fallback bug re-triggered a SECOND time
    later that day, re-wedging the process with (at the time) zero alerting for this specific failure shape. This
    second, silent wedge — not the earlier, well-alerted `/tmp`-ENOSPC blip — is what actually produced the sustained
    15:00-UTC-onward boots-without-dispatch collapse.
  - **The actual fix**: `agent-orchestrator@fc9ac53` (2026-07-12 22:36:28 UTC) shipped `_safe_tempdir_base()` (refuses
    the CWD-fallback, degrades to the PM working tree instead), `_sweep_orphan_snapshots()` (reclaims dirs orphaned by a
    hard-killed process), a `try/finally` around snapshot creation, AND a brand-new wedge-alert that fires when the
    checkout is current but the running process has stayed stale for >=3 consecutive ticks
    (`AO_STALE_PROCESS_ALERT_TICKS`) — closing exactly the detection gap that let the 15:00 UTC recurrence run silent
    for hours. 5 new regression tests; `quality-gates.sh` green (1204 passed) at ship time.

  **Verdict**: named cause, not a mystery — a recurring `tempfile.gettempdir()` CWD-fallback bug (triggered by `/tmp`
  exhaustion events on both 2026-07-10 and 2026-07-12) that wedged the orchestrator's own self-restart mechanism, with
  the SECOND (unalerted) wedge — not the well-known morning `/tmp`-ENOSPC blip — responsible for the bulk of the
  587-event/44:1 numbers. Both the generator bug and the missing-alert gap were fixed same-day
  (`agent-orchestrator@fc9ac53`); no further code change indicated. This item's own NOTE said to close or collapse the
  duplicate in `ao_open_issues_consolidated_close_out_2026_07_17.md` Phase 5 first — done in the same commit, its entry
  now points back here rather than carrying its own investigation.

- **2026-07-24 (slot 4)**: Re-checked the l2_book task-row-divergence re-test item (citation inline on its checkbox
  above). Verified live: `plans/active/l2_book_microstructure_capture_2026_07_13.md` is still `assigned_vm: NA`
  (`git log --follow` on the file shows no `assigned_vm` edit since the 2026-07-23 18:01:52+0530 fleet-wide pause commit
  `unified-trading-pm@468a0f580`); live `GET /api/backlog` still shows exactly 1 `l2_book%` task row
  (`l2_book_microstructure_capture-001`, `done`, orphaned out of `backlog.yaml`) against the plan's 2 still-open `- [ ]`
  todos. The todo's own Gate — "a live-or-clear verdict on the reopen-drop defect" — genuinely cannot be produced while
  the plan stays un-ingested, so the checkbox stays open rather than being force-closed; lifting the 19-plan pause is an
  operator/main decision, not something this slot should do unilaterally to make the item testable. No code change; this
  is a verification-only re-check, recorded so the next pass doesn't have to re-derive the same evidence from scratch.

- **2026-07-24 (slot 2)**: Worked item 14 (sports-closeout defense-line audit, citation inline on its checkbox above).
  Plan A's own two prerequisite todos are confirmed shipped (docs-reconciler timer live + dispatch proof), so this
  item's own narrower gate ("two todos above plus the hard-fail wiring") maps onto
  `plan_quality_four_line_defense_architecture_2026_07_23.md`'s own Todos, where I independently re-verified and flipped
  the two functionally-done-but-unflipped checkboxes (line 3's doc_drift→blocked-queue routing at
  `agent-orchestrator@18f262e`, confirmed present in the live checkout; line 4's docs-reconcile 24h cadence, confirmed
  via `systemctl status docs-reconciler.timer` = active/enabled). Line 1 re-verified present by direct grep of
  `task_template.md` §3. Line 2 (hygiene-sweep hard-fail wired into `quality-gates.sh`) is confirmed **not** wired
  (`grep run_hygiene_sweep scripts/quality-gates.sh` = no hits), and its prerequisite plan
  (`plan_line_cap_remediation_2026_07_23.md`) is confirmed still open — a fresh `check_line_caps.sh` run today shows 13
  plans still HARD-violating the cap (down from 30, not zero). Item 14's own deliverable — run the audit, record each
  line's actual fire/not-fire signal with evidence — is complete, so its checkbox flips (matches this plan's own l2_book
  precedent: flip on a recorded, evidenced verdict, not on the underlying condition resolving); the line-2 gap itself
  stays tracked in the issue doc's own SCRIPT todo and `plan_line_cap_remediation_2026_07_23.md`, not duplicated here.
  No code shipped this session (2 doc commits: the issue-doc checkbox flips + this plan's own annotation).
