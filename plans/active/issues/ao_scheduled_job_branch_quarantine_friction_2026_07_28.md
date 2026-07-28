---
doc_type: issue
title:
  Closed a scheduled-job observability follow-up — ag-closeout-auditor/na-eligibility-auditor's ao/ci tranches could
  silently skip a day on the shared 900s branch-quarantine recency guard, and a quarantine failure never retried onto a
  different slot
summary: >-
  Follow-up from ao_scheduled_job_observability_and_slack_alerting_2026_07_28.md: that doc left the branch-state
  quarantine (FM5/FM7) friction on ag-closeout-auditor/na-eligibility-auditor's `ao`/`ci` tranches as an open,
  operator-gated observation ("not something to loosen without separate operator direction"). Operator reviewed the
  tradeoff and approved BOTH proposed mitigations (2026-07-28 interactive session): (1) retry a quarantine failure on a
  different slot, same as the pre-existing "benign:" TOCTOU-race retry, and (2) narrow the auto-heal's ahead-commit-age
  recency guard specifically for this one-shot scheduled-dispatch family (900s → 300s), trading some of that margin for
  fewer missed daily tranches. Investigation while implementing found the retry mechanism as first designed would NOT
  have worked: a branch-quarantine failure never creates a tmux session on the target slot (the gate runs BEFORE
  tmux_spawn.spawn), so unlike the benign-race case — where the racing session naturally makes the slot look busy on
  retry — `_pick_free_slot` would have kept re-picking the SAME quarantined slot every attempt. Fixed by adding an
  explicit exclude-set threaded through the retry loop.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, scheduled-jobs, branch-quarantine, autospawn, plan_health, bug, hardening]
related:
  [ao_scheduled_job_observability_and_slack_alerting_2026_07_28, ao_agentkind_literal_gap_dashboard_outage_2026_07_28]
created: 2026-07-28
priority: P2
parent_epic: orchestrator_master
source:
  "operator interactive session, slot 3 — reviewed the two open follow-ups from the scheduled-job observability build
  and approved loosening the branch-quarantine gate + adding a retry, scoped to the scheduled-job dispatch family only"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by: slot-3 (interactive), agent-orchestrator@e69f528
locked_by:
---

# Scheduled-job dispatch: retry + narrow the branch-quarantine recency guard (operator-approved)

## What I found

`ao_scheduled_job_observability_and_slack_alerting_2026_07_28.md`'s Follow-ups section left the branch-state quarantine
(FM5/FM7) friction on `ag-closeout-auditor`/`na-eligibility-auditor`'s `ao`/`ci` tranches open, explicitly gated on
operator direction: the shared `MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN` (900s,
`worktree_clean_check/_realign_guard.py`) exists to stop a slot's auto-heal from silently discarding a live worker's
just-made commit — tied to two real prior data-loss incidents (`slot11_silent_branch_reset_data_loss_2026_07_13`,
`slot_double_reset_dataloss_race_2026_07_25`). Loosening it isn't a decision to make unilaterally.

Presented the operator two concrete options (retry-on-different-slot; narrow the window scoped to this dispatch family)
plus the tradeoff each one costs against that margin. Operator approved doing **both**.

**A design gap found while implementing the retry**: `plan_health.dispatch()`'s existing retry-on-`"benign:"` works
today because the RACING dispatcher's session lands on the contested slot, so `_pick_free_slot`'s live `has_session()`
check naturally skips it on the next attempt. A branch-quarantine failure is different — the quarantine gate
(`autospawn._do_spawn`'s `elif slot_path.exists():` branch) runs and refuses BEFORE `tmux_spawn.spawn()` is ever called,
so the slot never gets a tmux session at all. Without an explicit fix, `_pick_free_slot` would have kept re-picking the
exact same quarantined slot on every one of the 5 retry attempts — burning the whole retry budget on one bad slot
instead of trying the fleet's other free ones. Caught this via a test that initially failed the way production would
have (`test_dispatch_retries_on_a_different_slot_after_branch_quarantine` looped 5x on slot 1 instead of reaching slot
2).

## Fix

**`agent-orchestrator@e69f528`**:

- `autospawn._do_spawn` gains an optional `min_ahead_age_seconds: int | None = None` parameter, resolved to a concrete
  `int` (either the override or `worktree_clean_check.MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN`) before threading it
  into `heal_dead_slot_branch_quarantine` — every OTHER caller (worker/escalation/resume/main/review spawns) passes no
  override and gets the exact same shared 900s guard as before, unchanged.
- `plan_health.py` gains `_SCHEDULED_JOB_MIN_AHEAD_AGE_SECONDS = 300` (5 minutes) — passed on every `do_spawn` call from
  `dispatch()`, the only caller in this module, covering all 5 plan_health-family modes (`report` / `reconcile` /
  `docs_reconcile` / `ag_closeout` / `na_eligibility`) uniformly, since they share one dispatch codepath and gate. This
  resolves the observed case outright (460s-old commit was already older than the new 300s threshold).
- `_RETRYABLE_ERR_PREFIXES = ("benign:", "branch-state quarantine")` — the retry-continue condition now covers both
  failure classes.
- `_pick_free_slot` gained `exclude_slot_ids: frozenset[int] = frozenset()`; `dispatch()`'s retry loop accumulates a
  `quarantined_slot_ids` set across attempts and passes it in, so a retry after a quarantine failure genuinely lands on
  a different slot.
- Kept a basedpyright-clean call site: a first draft conditionally splatted a `dict[str, object]` into the heal call to
  avoid passing the kwarg at all when no override was given — basedpyright correctly refused this (it can't narrow which
  keys a `dict[str, object]` carries at a given call, so it type-checked EVERY keyword parameter of the call, including
  unrelated ones like `now`, against `object`). Fixed by always resolving a concrete `int` before the call instead.

**Why this is bounded, not a blank loosening**: the 900s guard stays the untouched default for every dispatch path
except this one scheduled-job family. If the narrower 300s window is ever wrong (discards a genuinely-live worker's
commit), the independent `HeadBackwardCanary` (`head_backward_canary.py`, detection half of the same 2026-07-13 fix)
still detects and pages on the resulting reflog signature — that safety net doesn't care which guard let the realign
through.

## Verification

- 6 new tests: `test_autospawn.py` (`test_do_spawn_threads_min_ahead_age_seconds_override_into_heal_call`,
  `test_do_spawn_resolves_default_min_ahead_age_seconds_when_no_override_given`); `test_plan_health.py`
  (`test_dispatch_passes_scheduled_job_min_ahead_age_seconds_override`,
  `test_dispatch_retries_on_a_different_slot_after_branch_quarantine`,
  `test_dispatch_exhausted_retries_on_quarantine_keeps_the_quarantine_message`,
  `test_dispatch_quarantine_on_a_single_slot_fleet_reports_no_free_slot`).
- Full repo `bash scripts/quality-gates.sh`: 1849 server tests + 154 dashboard tests, `ruff`/`basedpyright`/`tsc` clean.
- Not yet observed live in production (no quarantine has fired since deploy) — the next real signal is whichever of
  `ag-closeout-auditor`'s or `na-eligibility-auditor`'s `ao`/`ci` tranches next hits a genuinely-recent ahead commit;
  `ScheduledJobRunRow` (from the observability build this fix follows up on) will show whether it retried/succeeded or
  was one of the now-rarer genuine quarantine failures.

## Follow-ups

None open. The other follow-up from the parent doc (`na_eligibility_auditor`'s per-tranche timeout re-measurement)
remains separately open there, unaffected by this fix.
