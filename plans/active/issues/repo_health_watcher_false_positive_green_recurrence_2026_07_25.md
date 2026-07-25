---
doc_type: issue
title:
  RepoHealthWatcher signaled "GREEN again" TWICE for instruments-service while local quality-gates.sh still failed
  deterministically at the same unchanged HEAD — recurrence of the archived 2026-07-21 false-positive-green bug
summary: >-
  Filed a repo-blocker (RB-f599540b, kind=qg_red) for instruments-service after verifying (via git stash of my own diff)
  that quality-gates.sh fails 2 tests on a clean live-defi-rollout tree at HEAD=fd96e5a2:
  test_expected_universe_golden.py::test_expected_matches_golden[defi] (golden=234 actual=226, 8 missing GMX cells) and
  test_pipeline_e2e_prediction.py::test_rule11_per_ag_dedup_target_counts_byte_unchanged (DEFI 94 != 96). Root cause:
  plans/active/defi_gmx_venue_removal_2026_07_25.md's todo "Remove GMX from instruments-service reference data / MVP
  instrument universe" (scripts/enumerate_expected_universe.py) is still unchecked — the golden fixture has not been
  regenerated. RepoHealthWatcher resolved the blocker as GREEN and resumed me TWICE (RB-f599540b then RB-a8013c16) with
  zero new commits landing on live-defi-rollout between each resolution (HEAD stayed fd96e5a2 throughout) — both times a
  fresh local quality-gates.sh re-run at the SAME HEAD reproduced the SAME 2 failures byte-identical. This is the exact
  symptom the archived repo_health_watcher_false_positive_green_2026_07_21.md issue already diagnosed and supposedly
  fixed (agent-orchestrator@5bf0ccf, the `failing_run_is_current` stale-green gate) — but it recurred here with HEAD
  provably unchanged across both false "green" verdicts, which the existing gate's own logic (`run.head_sha == branch
  HEAD`) should have caught. Filed rather than silently re-declaring the blocker forever; worked around it this time by
  self-verifying with a real local QG run before trusting each green signal (as the archived doc's own recommendation
  says a waiter always should).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, repo-health-watcher, false-positive, coordination, quality-gates, recurring-bug]
related:
  [
    /plans/archive/issues/repo_health_watcher_false_positive_green_2026_07_21.md,
    /plans/active/defi_gmx_venue_removal_2026_07_25.md,
    /plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md,
  ]
created: "2026-07-25"
author: slot-5-worker
source: [sports_fixtures_schedule_wrong_schema_day-001]
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# What I found

Timeline (all against instruments-service `live-defi-rollout`, HEAD=`fd96e5a2` throughout — confirmed via
`git rev-list --count HEAD..origin/live-defi-rollout` returning `0` at every check):

1. `bash scripts/quality-gates.sh --no-fix` fails 2 tests with my diff staged.
2. `git stash` my diff, re-run — SAME 2 failures, byte-identical. Confirms pre-existing, not mine. Filed `RB-f599540b`
   (kind=`qg_red`) per RULES.md § 4b.
3. `RepoHealthWatcher` resolves `RB-f599540b` as green, sends
   `[orchestrator repo-health] instruments-service is GREEN again` + resumes my task. I fresh-pull (0 commits behind,
   HEAD unchanged) and re-run `quality-gates.sh --no-fix` — SAME 2 failures, byte-identical.
4. Re-declare `RB-a8013c16` with this exact finding in the detail field. `RepoHealthWatcher` resolves it green AGAIN —
   `curl /api/repo-blockers` shows `{"open": []}` within the same short window, again with zero new commits (HEAD still
   `fd96e5a2`). Fresh local re-run — SAME 2 failures, byte-identical, third time.
5. Root-caused the ACTUAL fix state: `plans/active/defi_gmx_venue_removal_2026_07_25.md` line 112,
   `- [ ] [DATA] P2. Remove GMX from instruments-service reference data / MVP instrument universe`, is still unchecked.
   This is a real, in-flight, not-yet-landed fix — not CI flakiness on my end.

# Why it matters

This is the exact symptom class `repo_health_watcher_false_positive_green_2026_07_21.md` diagnosed and marked `resolved`
via `agent-orchestrator@5bf0ccf`'s `failing_run_is_current` stale-green gate (`server/ci_reconcile.py`) — a green
verdict is supposed to be rejected unless the CI run describing it matches the CURRENT branch HEAD. Here HEAD never
moved between either false "green" verdict, which by that gate's own stated logic should have kept the blocker open both
times. Either the gate has a fresh regression, or `quality-gates-v2` genuinely never re-runs against `live-defi-rollout`
pushes at all (per this repo's own CLAUDE.md: "LDR never runs server QG — the promote PR carries quality-gates-v2") — in
which case `ci_status(repo)` may be reading a run against a DIFFERENT branch (`staging`/`main` promote PR) whose SHA
happens to satisfy the head-match check by construction, not because the actual LDR tip is green. Every worker that
trusts a `[orchestrator repo-health]` "GREEN again" resume message without independently re-running local QG risks
shipping (or attempting to ship, tripping the quickmerge sentinel refusal) against a genuinely red tree — exactly the
failure mode the archived fix was meant to close. This also wastes fleet capacity: 3 rounds of
declare→false-resolve→re-declare on one blocker for one worker, and any other waiter on the same repo would hit the same
false "resume" churn.

# Recommended decision

1. `backend_engineer`/`agent-orchestrator`: re-audit `RepoHealthWatcher`/`ci_status`/`failing_run_is_current` against
   THIS instance (instruments-service, `live-defi-rollout` HEAD `fd96e5a2`, 2026-07-25 ~11:18-11:27 UTC) — pull the
   actual `quality-gates-v2` run(s) `ci_status("instruments-service")` read at each of the two false-green ticks and
   check what branch/SHA they actually describe. If it's a `staging`/`main` promote-PR run whose SHA happens to be a
   fast-forward ancestor equal to a stale point, `failing_run_is_current`'s head-match may need to also verify the run
   was triggered FOR `live-defi-rollout` specifically, not just SHA-equal.
2. Given this repo's own CLAUDE.md states LDR never runs `quality-gates-v2` at all, consider whether `RepoHealthWatcher`
   should treat repos with no LDR-triggered CI run as `unknown` (never auto-resolve) rather than falling through to
   whatever the most recent unrelated-branch run says.
3. Not blocking: this doc's discovery didn't require fixing live — I self-verified with a real local QG run before
   trusting each signal, per the archived doc's own standing recommendation, and eventually shipped once the actual
   GMX-removal todo landed (or once genuinely green — see this doc's Progress Log for the resolution).
