---
doc_type: issue
title: Fleet git-health `not_clean_since` reads a pinned constant across churning repos/slots
summary: >-
  Across 4+ consecutive review-agent poll ticks (2026-07-27 15:41-16:29Z), every dirty repo reported by `GET
  /api/fleet/git-health` carried the SAME `not_clean_since` value (`2026-07-27T06:12:04Z`) even as the actual set of
  dirty (host, slot, repo) triples churned — different slots (0, 1, 3), different repos (agent-orchestrator,
  deployment-api, deployment-ui, unified-trading-pm, features-service), different file counts each tick.
  `dirty_oldest_mtime` on the same repos was either null or showed genuinely fresh mtimes (minutes old), confirming
  these were live/active edits, not long-abandoned WIP. This breaks the review agent's long-dirty-worktree diagnostic
  (`unified-trading-pm/agents/review.md` § 3d), which relies on `not_clean_since` age to distinguish a stuck/orphaned
  worktree from normal interactive editing — as observed, EVERY dirty repo reads as ~9h+ stale regardless of when it
  actually went dirty.
status: open
nature: issue
asset_group:
  [ao, meta] # corrected 2026-08-02 (/ag-closeout-audit cross-cutting, operator-ruled) -- `infrastructure` -> `ao`; the
  # defect is in agent-orchestrator's own `server/routes/git_health.py` fleet reporter (repos: [agent-orchestrator],
  # parent_epic: orchestrator_master), i.e. ao-tranche, not generic infrastructure. Left multi-value (`meta` kept as
  # ruled: substitution only), so it stays exempt from check_ag_closeout_linkage.py by construction.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [git-health, fleet-monitoring, worktree-health, reporter-bug, review-agent]
related: []
created: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
source: >-
  Discovered by the persistent review agent (agent_id agt-160e62, slot 2) during its standing poll loop while
  spot-checking `/api/fleet/git-health` for long-dirty worktrees per review.md § 3d. Root-caused in chat by main (agent
  agt-c7dd49, 2026-07-27T16:31Z): `_propagate_not_clean_since` in `server/routes/git_health.py` (near L74-118) stamps
  `not_clean_since = snapshot_time` only the first time a repo is observed non-clean for a given (host, slot) key
  (looked up via `ss.get_slot_git_status_row(session, host, slot_id)` at L237-238), and otherwise carries the prior
  stamp forward — this looks CORRECT in isolation. Main's triage: the shared-constant behavior across different
  slots/repos points upstream of this function, to either (a) the reporter cron (`slot-git-status-report.sh`) posting a
  fixed/non-refreshing `reported_at` instead of the real post-time, or (b) the fleet-aggregation view collapsing to one
  global snapshot's `reported_at` rather than surfacing the correct per-(host,slot) value. A third possibility not yet
  ruled out: the hysteresis gate in the same function (`_DIRTY_CONSECUTIVE_TICKS_CONFIRM_THRESHOLD`, requires a
  CONFIRMED clean streak before clearing `not_clean_since`) may be legitimately never clearing for repos that are being
  edited on-and-off all day since 06:12 — in which case the field is doing what its docstring says, just in a way that
  makes it useless for one-shot "did this go dirty just now vs hours ago" checks on actively-touched repos, and the fix
  may be exposing a separate per-observation "last dirty transition" alongside the confirmed-clean-gated
  `not_clean_since`, rather than a bug fix to the existing field.
resolved_by:
locked_by:
context_scope: [agent-orchestrator/server/routes/git_health.py, scripts/dev/slot-git-status-report.sh, agents/review.md]
drift_direction: advance-code
depends_on: []
---

# Fleet git-health `not_clean_since` reads a pinned constant across churning repos/slots

## What I found

Fleet-wide `not_clean_since` on `GET /api/fleet/git-health` read the identical timestamp (`2026-07-27T06:12:04Z`) for
every dirty repo across 4 consecutive review-loop ticks spanning ~50 minutes (15:41Z, 15:58Z, 16:14Z, 16:29Z), even
though:

- The set of dirty (slot, repo) pairs changed every tick (slot 0: agent-orchestrator/deployment-ui/deployment-api; slot
  1: unified-trading-pm; slot 3: deployment-ui/deployment-api).
- `dirty_files` counts on the same repo changed tick-to-tick (e.g. slot 0 `deployment-ui` went 5→3 files).
- `dirty_oldest_mtime`, when non-null, showed mtimes only minutes old (e.g. `2026-07-27T15:52:29Z` at the 15:58Z tick) —
  i.e. real, fresh edits.
- The fleet git-health reporter itself was NOT stale during this window (`reporter_stale: false`, `ff_pull_last_run`
  advancing each tick, `ff_pull_last_result: skip:dirty`/`dirty:unconfirmed`).

## Why it matters

The review agent's worktree-health watch (`unified-trading-pm/agents/review.md` § 3d) is specced to use
`not_clean_since` age (">~30 min") to flag a genuinely stuck/orphaned worktree vs normal in-progress editing. As
observed, this field cannot currently distinguish the two cases — every dirty repo reads as ~9h+ old regardless of
actual dirty-since time, which would either mass-false-positive (if taken at face value) or force every consumer to fall
back to `dirty_oldest_mtime` + manual file-churn cross-checking (the mitigation the review agent used this session).

## Recommended decision

Someone with access to the live AO backend (planning VM) and the reporter cron should:

1. Confirm whether `slot-git-status-report.sh` computes `reported_at`/dirty-transition freshly per post, or reuses a
   fixed/boot-time value.
2. Confirm the fleet-aggregation view (`GET /api/fleet/git-health`) surfaces the correct per-(host, slot, repo)
   `not_clean_since` rather than a single collapsed/global snapshot value.
3. Decide whether the existing hysteresis-gated `not_clean_since` should stay as-is (last confirmed-non-clean streak
   start) with a NEW separate "most recent dirty transition" field added for the stuck-vs-active diagnostic, or whether
   the hysteresis logic itself needs a bugfix so `not_clean_since` resets correctly across distinct editing sessions.

## Todos

- [ ] [BACKEND] P3. Instrument or trace `slot-git-status-report.sh`'s `reported_at`/dirty-transition posting to confirm
      whether it sends a fresh timestamp per run or a fixed value (repo: agent-orchestrator).
- [ ] [BACKEND] P3. Audit `GET /api/fleet/git-health`'s aggregation path to confirm it surfaces
      `SlotGitStatusRow`-scoped `not_clean_since` per (host, slot, repo) rather than any global/shared snapshot value
      (repo: agent-orchestrator).
- [ ] [BACKEND] P3. Based on the above, either fix the upstream timestamp source, or add a distinct "last observed dirty
      transition" field alongside the existing hysteresis-gated `not_clean_since` so worktree-health consumers
      (review.md § 3d) can reliably distinguish a fresh edit from a genuinely long-stuck worktree (repo:
      agent-orchestrator).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Doc's own 'Recommended
  decision' section frames the remaining step as a field-design choice (new field vs. hysteresis bugfix) — genuine
  judgment call, diagnostic todos feed directly into it.
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — 2026-07-30 verdict re-affirmed. In
  scope this run only because of the 2026-08-02 `asset_group` retag `infrastructure` → `ao` (`6ef14a71e`); body content
  unchanged. All 3 `[BACKEND] P3` todos are diagnostics feeding the doc's own unresolved field-design choice (keep the
  hysteresis-gated `not_clean_since` and ADD a separate "last observed dirty transition" field, vs. bugfix the existing
  field's reset semantics) — a genuine judgment call.
