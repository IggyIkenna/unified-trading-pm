---
doc_type: issue
title:
  "push_or_preserve_ahead_commits: rejected push permanently strands a QG-verified commit with no retry (post-hoc audit
  finding)"
summary:
  "A post-hoc implementation audit of the already-shipped, already-archived AO remediation plans re-verified
  server/worktree_clean_check/_ahead_push.py::push_or_preserve_ahead_commits (the watchdog sweep that auto-pushes a
  clean, QG-verified, ahead-of-origin commit on a worker's behalf). The audit's primary concern -- a stale sentinel SHA
  being trusted to authorize pushing a LATER, unverified commit -- is confirmed NOT possible (verified independently as
  content-diff-gated, not SHA-alone). The stale-SHA-in-the-activity-log symptom found alongside it was fixed same
  session (agent-orchestrator@06c5f8e9a2). What remains unfixed is a secondary, lower-probability but real gap: if the
  auto-push is REJECTED (e.g. a concurrent peer push to the same shared branch), the function safely falls back to
  preserving the work on a wip-preserve/ ref (no data loss), but the on-disk .qg_last_passed_sha sentinel now points at
  a pre-amend commit that is a SIBLING, not an ancestor, of the post-amend local HEAD -- so the sentinel can never
  re-verify on a later tick, and (since origin has since diverged) the repo also now reads behind > 0, permanently
  excluding it from this sweep. A genuinely QG-verified commit silently degrades from auto-landing eventually to needing
  a human, with zero retry logic and no test coverage for this branch."
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, worker-liveness, git, quickmerge, post-hoc-audit]
related:
  [
    /plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md,
    /plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md,
  ]
created: 2026-07-24
author: unknown
last_updated: 2026-07-24
priority: P3
parent_epic: orchestrator_master
source:
  "Post-archival implementation audit (2026-07-24) of ao_remediation_a/b/held-safety — 9 parallel verification agents
  re-checked all 24 shipped todos against live code; this is the one finding deliberately left unfixed rather than
  rushed into the single riskiest auto-push code path in the codebase."
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/worktree_clean_check/_ahead_push.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/tests/test_watchdog_unpushed_sweep.py,
    /plans/archive/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
---

# `_ahead_push.py` — rejected-push leaves a verified commit permanently stranded

## What was found

`server/worktree_clean_check/_ahead_push.py::push_or_preserve_ahead_commits` (wired into
`WorkerLivenessWatchdog._sweep_unpushed_slots()`), read in full during the post-hoc audit:

1. `sha`/`full_sha` capture, sentinel verification, and the `Quickmerge:` trailer stamp were all confirmed correct. The
   one bug found here — the activity-log evidence citing the stale pre-amend SHA instead of the actually-pushed
   post-amend SHA — was fixed same session: **`agent-orchestrator@06c5f8e9a2`**, `sha`/`full_sha` now re-captured AFTER
   the stamp attempt.
2. **Not fixed**: if `git push origin HEAD:{base}` (the line right after the trailer stamp) is REJECTED — a concurrent
   peer push to the same shared `live-defi-rollout` branch is a documented, recurring contention pattern elsewhere in
   this codebase — the function correctly falls back to `_preserve` (a `wip-preserve/` ref, no data loss). But:
   - Local HEAD is left at the now-amended commit.
   - The on-disk `.qg_last_passed_sha` sentinel still names the PRE-amend SHA.
   - `git commit --amend` produces a same-tree SIBLING, not a descendant, of the pre-amend commit (confirmed via a live
     repro this session: `git merge-base --is-ancestor` returns false between them).
   - So `_sentinel_verified`'s next check (exact-match OR ancestor-of-HEAD) fails BOTH ways — the sentinel can never
     re-link to this HEAD again.
   - Because origin has since diverged, the repo also now reads `behind > 0` on every future tick, which
     `push_or_preserve_ahead_commits` explicitly excludes (`if ahead == 0 or behind > 0: continue`) — so it drops out of
     this sweep entirely, forever.
   - Net effect: a commit that WAS genuinely QG-verified silently degrades from "the watchdog will land this
     automatically" to "a human has to notice the `wip-preserve/` ref and land it manually," with no alert, no retry,
     and no test covering this exact branch (`tests/test_watchdog_unpushed_sweep.py`'s 7 cases don't include a
     rejected-push scenario).

## Why this wasn't fixed immediately

This is the single riskiest automated code path in the system (it pushes to the shared branch on a worker's behalf with
no human in the loop). The audit's fix-agents were instructed to stay conservative and fix only the precisely scoped,
low-risk items; a proper fix here needs a real design decision — should it retry (how many times, what backoff), should
it re-verify+re-stamp against the new HEAD after a rejected push, should it alert instead of silently falling further
behind — rather than a guessed one-line patch to the riskiest file in the codebase.

## Open todos

- [ ] [BACKEND] P3. Design + implement a recovery path for the rejected-push case in `push_or_preserve_ahead_commits`:
      at minimum, either (a) re-run `_stamp_quickmerge_trailer_if_missing` + re-capture the sentinel against the NEW
      HEAD after a rejected push so a later tick can re-verify and retry, or (b) explicitly detect this state
      (verified-but-diverged-since-rejected-push) and surface it as a distinct, actionable signal (blocked-queue entry
      or Slack alert) rather than silently falling out of the sweep. **Gate**: a test reproducing a rejected push (bare
      remote already has a conflicting commit) proving the work is either automatically retried and lands, or surfaced
      as a visible blocked condition — not silently stranded.

## Progress Log

- **2026-07-24**: Filed after a 9-agent parallel post-hoc audit of the (now-archived) `ao_remediation_a/b` +
  `ao_held_safety_fixes_dispatch` plans found this as the one gap not worth rushing a fix for. 7 of 8 total gaps found
  in that audit were fixed same session (`agent-orchestrator@06c5f8e9a2`, `agent-orchestrator@0cc12fdbb2`,
  `unified-trading-pm@5cc0ea829`); this is the sole deliberate deferral.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the doc's own `Why this wasn't fixed immediately` section states
  the fix needs a real design decision (retry count/backoff vs re-stamp vs alert) on what it calls 'the single riskiest
  automated code path in the system'. Independently held in `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s
  conflict-gated Deferred list, which adds a file-collision reason (its characterisation test lands in
  `tests/test_watchdog_unpushed_sweep.py`, the same module the gate-aware sweep fix needs).
- **2026-07-31 (re-triage)**: The file-collision reason has CLEARED —
  `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`'s gate-aware sweep shipped
  `agent-orchestrator@49c919d`, adding 3 new tests to `tests/test_watchdog_unpushed_sweep.py` (12/12 passing, no
  conflict). This doc's own design-decision gap is UNCHANGED and still open — this todo still needs its own
  retry/backoff-vs-alert design call — but it is no longer blocked on anything else landing first; it's ready to be
  worked directly whenever picked up.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified (6 entries, unchanged) — all still resolve and remain the right minimal set
  for the doc's sole open todo (rejected-push recovery design in `_ahead_push.py`).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries) -- still the right minimal set for the
  sole open todo (rejected-push recovery design in `_ahead_push.py`).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. Sole open todo remains a real design decision on "the single riskiest automated code path in the
  system" (doc's own words).
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — checked against the full round7-10 precedent set (IAM
  self-service, D16, S5.1, plan-destination default, escalation-N, reversibility-qualified deletes, Option B retirement,
  DeepSeek/Slack-webhook credentials, sibling-script self-service) — none apply; the retry-vs-alert design call on the
  fleet's riskiest auto-push path is unchanged and genuinely undecided. Corroborated by the same-day
  `/ag-closeout-audit ao` batch12 run, which independently lists this doc under operator-gated (22), declined
  zero-extraction.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Sole open todo remains a real, undecided retry-vs-alert design call on "the single riskiest
  automated code path in the system" (doc's own words, unchanged framing since filing) — checked against the full
  round7-10 precedent set, none apply.
