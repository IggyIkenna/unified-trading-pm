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
priority: P1
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

## Addendum 2026-07-22 — a distinct data-quality facet: dirty row for a worktree that does not exist on the host

review(slot1, hk) reported (msg 1650, 2026-07-22 10:51Z) two more instances under a **fresh** `reported_at` (10:47Z):

| Slot | Repo(s) reported dirty        | Ground truth on hk host                                           |
| ---- | ----------------------------- | ----------------------------------------------------------------- |
| 0    | deployment-api, deployment-ui | **`.tabs/0` does not exist as a directory on this host at all**   |
| 4    | deployment-ui                 | `deployment-api`/`deployment-ui` both CLEAN via direct git status |

The **slot-4** instance is the same flicker class already characterised above (FF-cron mtime churn on a
present-and-clean repo → transient dirty). But the **slot-0** instance is a **different fingerprint** and is NOT
explained by the flicker/FF-cron race: the reporter cannot have `git status`-churned a worktree that isn't on the host —
so this row is a **stale/cached per-repo dirty state re-stamped with a fresh `reported_at`**, i.e. a git-health row
surviving (or bleeding in cross-host) for a slot/worktree that is absent on the reporting host, presented as live
because the timestamp is current. The masking risk is the same one already noted (a stale row can hide the true state of
a real repo), but the mechanism is stale-row-survival / host-attribution, not a one-tick flicker — worth a distinct
look. Not orphan-WIP (nothing to inherit; the directory isn't there). No page — digest-class, consistent with the rest
of this doc.

- [ ] [INFRA] P2. Determine why a git-health dirty row is emitted/retained for a worktree absent on the reporting host
      (`.tabs/0` on hk): is `slot-git-status-report.sh` reporting a stale cached prior result when the worktree dir is
      missing (should emit `absent`/skip, not a stale `dirty`), or is a row from another host being attributed to this
      one? Reporter should treat "worktree directory missing" as an explicit `absent` state, never carry forward a prior
      `dirty`. Add a guard + a test that a vanished worktree does not keep POSTing its last-known dirty.

### Follow-up 2026-07-22 (review msg 1654, 11:49Z) — the phantom `.tabs/0` row is unstable, and can now trip `drift_violation`

review(slot1, hk) added a data point that **hardens** the stale-row-survival read above: the same phantom
hk-slot0/deployment-ui entry (still on a `.tabs/0` that does not exist on this host) **mutated its reported state from
`dirty` (1 file) to `ahead` (2 commits)** across ticks — while `not_clean_since` stayed pinned at the same `08:12:03Z`
(unchanged) — and in the `ahead` form it now **trips `drift_violation=true`** where it previously did not. This is
diagnostic in two ways: (1) it confirms the row is **unstable/flaky, not a one-off blip** — a genuinely-absent worktree
cannot legitimately transition dirty→ahead, so the row is being fabricated/carried-forward from stale or cross-host
state; (2) it raises the stakes slightly beyond "cosmetic masking" — a phantom row that flips into `drift_violation`
could inject a **false drift signal** for a slot/worktree that isn't even on the host, which is a more actionable
false-positive than a phantom `dirty`. Same fix lever (reporter must emit `absent` for a missing worktree dir, never
carry forward a prior state) — this just adds urgency and a second failure mode (false `drift_violation`) to the open
INFRA todo above. Still digest-class, no page (review explicitly filed it as a record-only data point, no new
escalation). The slot3/6 diverged pair (same SHAs) and the `ip-172-31-0-185` slot0 out-of-scope session are unchanged
and already-known.

### Escalation 2026-07-22 (review msg 1658, 12:34Z) — ALL 24 repos false-dirty at once WITH real FF-pull starvation → bumped to P1

This is the data point that takes the issue from cosmetic/digest-class to **operationally impactful**, and is why the
frontmatter priority is now **P1** (was P2). review(slot1, hk) reported that its **own live slot** (hk slot 1, the
active review agent) had **all 24 repos report `dirty(1 file)` simultaneously**, with an **identical
`not_clean_since=2026-07-22T12:22:04Z` across every single one**. review directly checked 3 of them (agent-orchestrator,
unified-trading-library, unified-api-contracts) via `git status --short` in real time — **all genuinely CLEAN, zero
files**.

Two things make this materially worse than every prior instance in this doc:

1. **Real operational impact, not display-only.** `ff_pull_last_result` on that slot now reads **`skip:dirty`** — i.e.
   the 5-min FF-pull cron (`slot-cron-ff-pull.sh`) is **actively skipping the slot on this false dirty signal right
   now**. A slot that stops FF-pulling silently drifts behind `origin/live-defi-rollout`; that is the exact staleness
   the sync-nudge exists to catch, produced here by the reporter bug itself. The masking-risk hypothesized in the
   earlier sections is no longer hypothetical — a false-clean would clear the age, and a false-dirty is now demonstrably
   starving FF-pull. **Update (review msg 1662, 12:37Z): the event self-cleared within ~15 min** — review re-checked
   `git_status.repos[].dirty_files_sample` and all repos were back to clean, so the FF-pull skip was **transient (one
   cron window), not a stuck state**; this bounds the per-incident blast radius (a missed FF-pull tick, not indefinite
   starvation) but does not lower P1 — a fleet-wide all-repos false-dirty that trips even a single FF-pull skip is still
   a real reporter bug. review is now watching every tick to capture the `dirty_files_sample` on recurrence (churn-vs-
   fabrication proof), since the flicker window closed before a sample could be grabbed this time.
2. **Blast radius is fleet-wide and on LIVE slots, not a retired/absent worktree.** The `.tabs/0` addendum above was a
   phantom row for a worktree that doesn't exist on the host — annoying but inert. This is 24 present-and-clean repos on
   an active slot all flipped dirty at the **same instant**. The identical timestamp across all 24 strongly implicates a
   **race in the reporter itself** — scanning mid-write of some shared lock/temp artifact, or a bug that stamps every
   repo dirty when a single shared precondition trips — rather than 24 independent per-repo `git status` mtime-churn
   races coinciding by chance. This is a distinct (or at least strictly-stronger) fingerprint from the per-repo FF-cron
   mtime-churn flicker characterised at the top of this doc.

Not orphan-WIP (review's trees are actually clean; nothing to inherit). review filed it as a stronger repro signal for
the reporter bug, explicitly flagging the fleet-wide FF-pull-starvation risk on live slots. **Operator-surfacing item**
(added to the main orchestrator's next-operator-contact list): a monitoring reporter bug is now silently degrading a
real fleet operation (FF-pull currency) on live slots.

- [ ] [INFRA] P1. Root-cause the **all-repos-simultaneous** false-dirty (identical `not_clean_since` across 24 repos on
      one slot) in `slot-git-status-report.sh` — this points at a shared-precondition/shared-artifact race in the
      reporter, not per-repo `git status` churn. Because it drives `ff_pull_last_result=skip:dirty` and thus starves the
      FF-pull cron, the `dirty_consecutive_ticks >= 2` gate proposed above should also guard **the FF-pull skip
      decision** (`slot-cron-ff-pull.sh`), not just `not_clean_since` clearing + sync-nudge — a one-tick phantom dirty
      must not skip an FF-pull. Add a test that a single-tick all-repos-dirty observation neither clears/sets
      `not_clean_since` nor causes an FF-pull skip.

## Triage

Non-blocking, digest-class, no page. Outside every active plan → parked here per findings-triage. Filed by the main
orchestrator on review(slot1)'s behalf after they consolidated the thread and stepped back from per-recurrence pings.
2026-07-22 addendum appended by main from review msg 1650 (same subsystem — consolidated here rather than a duplicate
doc).
