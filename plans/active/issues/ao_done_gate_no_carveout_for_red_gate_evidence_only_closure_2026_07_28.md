---
doc_type: issue
title:
  agent-orchestrator /done cross-repo checkbox-flip verification has no accepted disposition for a genuinely-still-open,
  do-not-flip-on-RED-gate todo whose evidence commit is older than the 30-minute Mode-2 window
summary: >-
  `server/verify.py`'s `check_plan_flip` (Mode 2, cross-repo PM-flip check) hard-409s `/done` for a task whose
  `done_definition` legitimately forbids flipping the checkbox (a data-pipeline-correctness RED-gate todo per CLAUDE.md
  "Data pipeline correctness is the heartbeat" -- flipping on RED would violate that HARD RULE). Two compounding gaps:
  (1) `_pm_log_commits_touching_plan_ref` only looks back 30 minutes, so evidence committed earlier in a session that
  was later resumed/re-booted (this exact case: commits from 11:08-11:09Z, `/done` retried at 13:33Z) returns an empty
  `pm_shas` regardless of content; (2) even inside the window, `_mode2_disposition` only recognizes THREE dispositions
  (a real `[x]` flip, a CANCELLED/SUPERSEDED marker, or a DEFERRED-BY-DESIGN marker) -- none fits "still genuinely open,
  real work, temporarily blocked on ANOTHER slot's active in-flight fix, not permanent/non-fix, not superseded", which
  is exactly what a RED-gate-blocked todo is. Net effect: this class of task has NO self-service path to `/done` at all,
  confirmed live via two rejected calls (`reason: "cross_repo_pm_file_touched_no_checkbox_flip"` then `reason:
  "cross_repo_pm_log_clean"` on the same task, `data_completion_cefi-011`) even on a fully clean tree with
  already-pushed evidence commits.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, done-gate, plan-flip-verification, red-gate, data-correctness, bug]
related:
  [
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/issues/ao_done_gate_checkbox_flip_blind_to_self_archived_plan_ref_2026_07_26.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: 2026-07-28
priority: P2
parent_epic: orchestrator_master
source: "worker, slot 12, hit live while closing out data_completion_cefi-011 per main's BLOCKED-Q ruling"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# /done checkbox-flip verification has no carve-out for RED-gate evidence-only closure

## What I found

Task `data_completion_cefi-011`
(`[DATA] P1. C-source RIDER (folded into C0 (b)): the source column ... lands in THIS walk`,
`plans/active/data_completion_cefi_2026_07_15.md`) is a genuine RED-gated todo: main already ruled (BLOCKED-Q answer,
this same task, earlier in this session) that the checkbox must stay `- [ ]` because the audit backing this whole
C0/C-source chain is RED (v9=97.4%, source-blank=24%, pipeline_mode-blank=1.4%, Era-B chain=490,332 rows) and the real
predecessor/owner is `plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md` (owned by
slots 2+15, not this task). Main's exact words: "flipping it would violate the data-pipeline-correctness HARD RULE" and
"evidence-only closure is correct."

Two evidence commits were already made + pushed earlier in this session documenting the finding and avoiding a redundant
3rd full-corpus scan:

- `unified-trading-pm@b87980d15` (11:08:07Z) -- flagged triple-dispatch on the cefi rebuild dry-run, killed the
  redundant 3rd copy.
- `unified-trading-pm@ce4af5f15` (11:09:34Z) -- re-check note: predecessor still blocked, duplicate dispatch avoided.

Both touch `plans/active/data_completion_cefi_2026_07_15.md` (confirmed via `git show --stat`), both are on
`origin/live-defi-rollout` (worktree fully clean, `git rev-list --count HEAD..origin/live-defi-rollout` = 0 and vice
versa). Per main's guidance, I retried `/done` at 13:33:26Z citing `sha: "ce4af5f15"`:

```
{"detail":{"msg":"commit 'ce4af5f15' does not touch the plan checkbox at
'plans/active/data_completion_cefi_2026_07_15.md' -- flip the checkbox ...",
"reason":"cross_repo_pm_log_clean","sha":"ce4af5f15"}}
```

Reading `server/verify.py::check_plan_flip` directly (not guessing):

1. Mode 2 (cross-repo) calls `_pm_log_commits_touching_plan_ref(pm_worktree, candidate, within_minutes=30)` --
   `git log --since="30 minutes ago" ... -- <plan_ref>`. My evidence commits are from 11:08-11:09Z; the retry was at
   13:33Z -- **over 2 hours later**, well outside the 30-minute window. `pm_shas` comes back empty.
2. With `pm_shas` empty, the function falls through to `checkbox_currently_checked` (reads the CURRENT on-disk plan text
   for a `- [x] <brief>` line matching this todo's exact brief). The checkbox is genuinely, correctly still `- [ ]` (per
   the do-not-flip-on-RED ruling) -- so this is `False` too.
3. Both checks fail -> `reason: "cross_repo_pm_log_clean"`, `/done` rejected -- **identical code path to a worker who
   genuinely forgot to flip**, even though this worker was explicitly told NOT to flip.

Even hypothetically retrying within the 30-minute window would not have helped: `_mode2_disposition` (L776-793) only
tries three dispositions in order -- `_diff_flips_checkbox` (real `[x]`), `_diff_cancels_checkbox` (CANCELLED/
SUPERSEDED marker), `_diff_defers_checkbox` (DEFERRED-BY-DESIGN marker). None of these fits this case:

- Not a real flip (correctly forbidden).
- Not CANCELLED/SUPERSEDED -- the todo is NOT re-scoped or dead; it's real, still-open work.
- Not DEFERRED-BY-DESIGN either -- that marker's own docstring (`_diff_defers_checkbox`, L716-725) is for "a todo the
  operator has ruled a closed, **permanent non-fix** (no timeline, nothing to schedule)". This todo is the opposite:
  it's actively being worked, just by a DIFFERENT slot's already-assigned fix chain (slots 2+15 on the false-phantom
  predecessor), with a real timeline (once that fix lands, this rider becomes doable).

So there is currently **no accepted disposition at all** for "genuinely still open, real, temporarily blocked on ANOTHER
owner's in-flight fix, not superseded, not a permanent non-fix" -- which is exactly what every RED-gated
data-correctness todo looks like while the gate is red.

## Why it matters

This is not a one-off: the data-pipeline-correctness HARD RULE (`codex/02-data/data-pipeline-correctness-hard-rule.md`)
explicitly says a RED data audit FREEZES layer-N+1 work and gates checkbox-flipping until green -- so RED-gated todos
recur by design across every asset-group's consolidated-closeout plan, not just this cefi one. Any worker that hits this
gate has no self-service resolution: it cannot flip (forbidden by the data-correctness rule), cannot CANCEL (the work is
real and still expected), cannot DEFER-BY-DESIGN (not a permanent non-fix, and semantically dishonest to claim it is),
and the 30-minute Mode-2 window means even a same-session retry a bit later (a compact/resume, a `/blocked` round-trip
waiting on main's answer, or just a slow QG run elsewhere) ages the evidence commit out of consideration. The task is
stuck permanently `in-progress` on this slot with no way to `/done` it, which either strands the slot indefinitely or
forces an operator/main manual DB patch outside the normal flow.

## Recommended decision

- [ ] [BACKEND] P2. Add a fourth accepted Mode-2/Mode-1 disposition in `server/verify.py` for "genuinely still open,
      temporarily blocked on another owner's in-flight fix, evidence documented" -- e.g. a `BLOCKED-ON:<ref>` or similar
      non-checkbox marker convention (this exact plan already uses an ad-hoc "🔴 BLOCKED ... confirmed by main" bold
      prefix on a sibling todo at `data_completion_cefi_2026_07_15.md` for the same purpose, but verify.py has no regex
      recognizing it -- only `_ADDED_CANCELLED_LINE_RE` and `_ADDED_DEFERRED_LINE_RE` exist). Mirror
      `_diff_cancels_checkbox`/`_diff_defers_checkbox`'s structure: a `_diff_blocks_checkbox` matching a
      `- [ ]     <brief>` line replaced by one still carrying `- [ ]` plus a recognizable `BLOCKED` marker, accepted
      with `reason="todo_blocked_pending_other_owner"`. Repo: agent-orchestrator.
- [ ] [BACKEND] P2. Separately: widen (or remove) the Mode-2 30-minute window specifically for the fallback
      `checkbox_currently_checked`-style checks -- i.e. even when `pm_shas` is empty because the evidence commit is old,
      still fall through to reading the CURRENT on-disk plan text for a recognized disposition marker (mirrors how Mode
      1's fallback at L920-932 already does this for the `[x]`-flip case; Mode 2's empty-`pm_shas` branch at L1006-1025
      currently only checks `checkbox_currently_checked` for a real `[x]`, not for the CANCELLED/DEFERRED/ (future
      BLOCKED) marker text). This closes the "evidence aged out of the log window" half of the gap independently of the
      marker-convention fix above. Repo: agent-orchestrator.
- [ ] [DOC] P3. Once either fix above ships, add the accepted BLOCKED-marker convention to `task_template.md`'s
      "remove/re-state a todo" section (alongside the existing CANCELLED/SUPERSEDED and DEFERRED-BY-DESIGN conventions)
      so future RED-gate todos use a consistent, machine-recognized marker from the start.

## Progress Log

- 2026-07-28 (worker, slot 12): Filed after a `/done` retry (per main's own BLOCKED-Q ruling on this exact task) still
  409'd on a fully clean tree with already-pushed evidence commits, confirming main's predicted "server gap" diagnosis.
  Root-caused by reading `server/verify.py::check_plan_flip` directly (not guessing) -- two independent causes
  identified (30-min window + missing 4th disposition). Per main's instruction: task LEFT in-progress, NOT
  skipped/redispatched, checkbox NOT flipped.
