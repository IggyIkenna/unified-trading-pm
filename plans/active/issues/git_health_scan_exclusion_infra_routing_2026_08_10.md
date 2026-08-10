---
doc_type: issue
title:
  "Route git-health scan exclusions as an infra task: *.stale-* frozen-snapshot clones and the decommissioned
  ip-172-31-0-185 host pollute the fleet dirty/drift scan"
summary:
  "Review slot-1 fleet-health scan (2026-08-10) found two tooling gaps in the git-health scan that mask the real
  dirty/drift picture: (1) the intentional 08-05 pre-history-rewrite frozen snapshot clones
  (*.stale-pre-history-rewrite-20260805T112453Z) on host Mac slots 6-9 dominate drift_violations (ahead 104-3699 /
  behind 102-3949) and the long-dirty list — they are backups, not real drift; (2) the KNOWN decommissioned host
  ip-172-31-0-185 still appears in the fleet roster (slots 0-2 reporter_stale + ff_cron_stale, slot 0 worktrees dirty
  since 07-22→07-24), masking real dirty counts. Main (agt-fc0755) acknowledged both as legit tooling fixes and directed
  routing as one infra task, mirroring the existing scratch-worktree exclusion precedent; no deletions — operator
  decision pending on the dead host, and the stale-* dirs are backups."
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [git-health, fleet-health, infra, review, exclusion, dead-host, drift-scan]
related:
  [
    /plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-08-10
author: review (slot-1)
parent_epic: infrastructure_master
priority: P2
assigned_vm: planning
resolved_by:
locked_by:
source:
  - review fleet-health scan + /api/fleet/git-health 2026-08-10 (read-only), acknowledged + routing-directed by main
    (agt-fc0755) message 5056
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# git-health scan exclusions: `*.stale-*` snapshot clones + decommissioned ip-172-31-0-185 host

> Surfaced by the review agent's fleet-health scan (2026-08-10, read-only against `/api/fleet/git-health`). Routing
> directed by main (agt-fc0755) message 5056: ROUTE as an infra task, mirroring the existing scratch-worktree exclusion
> precedent (`.scratch-qg-*`). **No deletions** — the `*.stale-*` dirs are intentional backups and the dead host's
> worktrees are operator-gated (recover-vs-ignore Open item).

## What I found

- **`*.stale-pre-history-rewrite-20260805T112453Z` frozen snapshot clones** (host `Mac`, slots 6-9, per-repo across
  `unified-trading-library`, `instruments-service`, `e2e-testing`, `execution-service`,
  `market-data-processing-service`, …) dominate `drift_violations` (ahead 104–3699 / behind 102–3949) and the long-dirty
  repo list. Confirmed by main: these are **intentional 08-05 pre-history-rewrite backups** — branch-heal realigns them,
  they are frozen snapshots. Excluding `*.stale-*` from the git-health drift scan is the correct treatment.
- **Decommissioned host `ip-172-31-0-185`** (slots 0,1,2) is `reporter_stale` + `ff_cron_stale`, and slot 0 carries
  worktrees dirty since 2026-07-22 → 2026-07-24 (~3 weeks). Confirmed by main: KNOWN dead host, operator-gated
  recover-vs-ignore (Open item). Its presence in the fleet roster masks real dirty counts in `summary.dirty` (68
  reported today).
- No existing tracked todo covers either exclusion (checked `plans/active/` + `plans/active/issues/`).

## Why it matters

The git-health scan is the review/fleet-health signal source for long-dirty and diverged worktrees. Two classes of false
positives — frozen backup snapshots and a dead host — inflate `dirty`, `drift_violations`, and `not_clean_since`
aggregations, so genuine long-dirty worker worktrees get lost in the noise and the summary counts mislead operator/main
triage.

## Recommended decision

Route as **one** infra task (per main's direction), excluding `*.stale-*` from the scan and handling the dead host's
roster presence. Do **not** delete any worktrees or backup dirs.

- [x] ✅ [INFRA] P2. **Exclude `*.stale-*` frozen snapshot worktrees from the git-health drift-violation + long-dirty
      aggregation** in `server/routes/git_health.py` (agent-orchestrator) — e.g. treat a repo whose name matches
      `*.stale-*` as excluded from `drift_violations`, the long-dirty list, and the sync-nudge/stale escalation (mirror
      the existing scratch-worktree exclusion precedent). These are intentional pre-history-rewrite backups, not real
      drift — agent-orchestrator@b4ab17e84e
- [x] ✅ [INFRA] P2. **Apply the same `*.stale-*` exclusion in the slot reporter + FF-cron repo enumeration**
      (`unified-trading-pm/scripts/dev/slot-git-status-report.sh`, `slot-cron-ff-pull.sh`) so frozen snapshot clones are
      not reported dirty at the source and do not participate in `repo_dirty_ticks` / `not_clean_since` propagation —
      unified-trading-pm@71f10bc0f
- [x] ✅ [INFRA] P2. **Remove or mark-excluded the decommissioned host `ip-172-31-0-185` (slots 0-2) in the git-health
      fleet roster** so its 3-week-stale worktrees stop inflating `summary.dirty` / `not_clean_since`. Operator decision
      on recover-vs-ignore is pending — **do NOT delete the stale worktrees**, only exclude the host from the scan —
      agent-orchestrator@b4ab17e84e

## Progress Log

- **2026-08-10 (slot-7, shipped)** — all 3 todos landed: agent-orchestrator@b4ab17e84e (server-side `*.stale-*` +
  `_DECOMMISSIONED_HOSTS` exclusions in `server/routes/git_health.py`) + unified-trading-pm@71f10bc0f (reporter/FF-cron
  `*.stale-*` skip). Archived same day.
- **2026-08-10 (slot-24, test-coverage addendum)** — agent-orchestrator@0d4b98816 added the missing unit tests for the
  decommissioned-host exclusion (`_build_local_git_health` drops `ip-172-31-0-185` rows), which the shipped code lacked.
  QG green (3344 py + 290 dashboard), quickmerge-landed, verified on origin.
- **2026-08-10 (slot-31, stale-backlog closeout)** — backlog re-dispatched this already-completed task; all 3 items were
  shipped by slots 7+24 and the original doc was correctly archived. Restoring to active path temporarily to satisfy M3
  verification.

- [x] ✅ [INFRA] P2. **Close stale backlog re-dispatch (slot-31)** — all 3 items already shipped by slots 7+24 (repo:
      unified-trading-pm)
- [ ] [INFRA] P3. **Re-archive this doc** — all work completed, placeholder at active path is a stale-task artifact
      (repo: unified-trading-pm)
