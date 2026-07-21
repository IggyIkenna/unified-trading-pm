---
doc_type: issue
title:
  "git-health phantom-dirty flicker: slot-git-status-report.sh races the 5-min FF-pull cron, emits a transient dirty
  that re-stamps not_clean_since to the poll time and can reset the sync-nudge age on a genuinely long-dirty repo"
summary:
  The per-slot git-health reporter (unified-trading-pm/scripts/dev/slot-git-status-report.sh) runs `git status
  --porcelain` on a ~5-min cadence and POSTs the result to /api/slots/{slot_id}/git-status. On repos the 5-min FF-pull
  cron (slot-cron-ff-pull.sh) actively touches, a status read caught mid-fetch/merge transiently reads dirty (mtime-
  churned but content-identical index entries) even though nothing is uncommitted. The server (git_health.py
  _propagate_not_clean_since) is CORRECT for a continuously-dirty repo — it preserves the prior not_clean_since and only
  stamps snapshot_time on a FIRST non-clean observation — so a not_clean_since pinned to the exact poll timestamp is the
  fingerprint of a reporter-side flicker (clean -> transient dirty -> clean). The only real harm — an intermittent CLEAN
  poll clears not_clean_since (git_health.py 88-90), resetting the age the ~30-min sync-nudge escalation depends on, so
  a genuinely long-dirty repo that happens to flicker could dodge the nudge. Non-blocking, digest-class. Confirmed on 3
  instances 2026-07-21 (slot3 unified-trading-pm, slot4 deployment-ui, slot16 unified-trading-pm), each re-verified
  genuinely clean via direct `git status --short` with no actual staleness >30min.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [git-health, monitoring, false-positive, race-condition, ff-cron, per-tab-worktrees, agent-orchestrator]
related:
  [
    plans/active/issues/slot5_deployment_api_dirty_false_positive_2026_07_13.md,
    codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-21
priority: P2
parent_epic: infrastructure_master
source: "review(slot1) msgs 1530/1532/1534 to main orchestrator, 2026-07-21"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## What I found

review(slot1) flagged, then re-confirmed across three ticks (05:47Z, 06:02Z), a repeating git-health flicker: certain
slots briefly report `state=dirty` with `not_clean_since` pinned to the exact poll timestamp, then revert to clean on
the next poll. Each time review re-verified the worktree directly (`git status --short` empty) — the repos are genuinely
clean; nothing is uncommitted.

Confirmed instances (all 2026-07-21):

| Slot | Repo               | First seen |
| ---- | ------------------ | ---------- |
| 3    | unified-trading-pm | earlier    |
| 4    | deployment-ui      | earlier    |
| 16   | unified-trading-pm | 06:02Z     |

The affected population is exactly **the repos the 5-min FF-pull cron actively touches** (unified-trading-pm,
deployment-ui) — the discriminating clue for root cause.

## Root cause

Two-part, and the split matters:

1. **Server propagation is CORRECT** — `_propagate_not_clean_since` in `agent-orchestrator/server/routes/git_health.py`
   (~lines 66-101) preserves the prior `not_clean_since` across contiguous non-clean observations and stamps
   `snapshot_time` only on a **first** non-clean observation (or an unparseable prior stamp). So a `not_clean_since`
   equal to the poll time is NOT a server persistence bug — it is the signature of a reporter that emitted a transient
   dirty at that tick after a preceding clean.

2. **Reporter-side race (the real defect)** — `unified-trading-pm/scripts/dev/slot-git-status-report.sh` runs
   `git status --porcelain` (~line 193) on its ~5-min cadence. When that read lands mid-fetch/merge of the concurrent
   5-min FF-pull cron (`slot-cron-ff-pull.sh`, which fetches/merges every worktree on a schedule — see
   `codex/05-infrastructure/per-tab-worktrees.md`), mtime-churned-but-content-identical index entries read **dirty** for
   that single poll, then clean again once the index settles. Same known class as
   `slot5_deployment_api_dirty_false_positive_2026_07_13.md` (which is why `dirty_sample` — up to 5 raw porcelain lines
   — was added to the reporter, precisely to expose the phantom paths).

## Why it (mildly) matters

Purely cosmetic for the fleet git-health view **except** for one real edge: an intermittent CLEAN poll clears
`not_clean_since` (git_health.py:88-90, the `is_clean_uptodate` gate), which resets the age that
`_maybe_send_sync_nudge` (~line 104) uses for its ~30-min escalation threshold. A repo that is **genuinely long-dirty
but happens to flicker** would therefore keep resetting its age and could dodge the sync-nudge indefinitely. No
occurrence of that failure mode has been observed (all 3 instances were truly clean), but it is the reason this is worth
fixing rather than ignoring.

## Fix lever (proposed, not yet implemented)

Gate on the reporter's **already-computed** `dirty_consecutive_ticks` (slot-git-status-report.sh ~line 160) so a single
clean/dirty blip can't move state:

- Require `dirty_consecutive_ticks >= 2` (N consecutive non-clean observations) before **clearing** `not_clean_since`,
  i.e. don't let one clean blip reset a real long-dirty age.
- Symmetrically, require the same before `_maybe_send_sync_nudge` treats a repo as dirty-for-escalation, so a one-tick
  phantom dirty never pages.

This is a small, isolated change to `git_health.py` (server) using a field the reporter already sends; no reporter
change strictly required, though optionally the reporter could suppress a dirty whose `dirty_consecutive_ticks == 1`
before POSTing.

## Open TODOs

- [ ] [INFRA] P2. Attach `dirty_sample` raw porcelain lines captured at a flicker tick for slot3/slot4/slot16 (review
      holds the direct-worktree evidence) — confirms the phantom paths are index-mtime churn, not real edits.
      Reproduction is well-characterized enough to fix without this if a clean capture proves hard to grab.
- [ ] [INFRA] P2. Implement the `dirty_consecutive_ticks >= 2` gate on the `not_clean_since` clear + sync-nudge in
      `agent-orchestrator/server/routes/git_health.py`; add a unit test that a single clean poll between two dirty polls
      does NOT reset `not_clean_since`.

## Triage

Non-blocking, digest-class, no page. Outside every active plan → parked here per findings-triage. Filed by the main
orchestrator on review(slot1)'s behalf after they consolidated the thread and stepped back from per-recurrence pings.
