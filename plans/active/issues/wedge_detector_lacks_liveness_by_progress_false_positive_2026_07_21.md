---
doc_type: issue
title:
  Fleet wedge-detector (review heuristic + sync_nudge + git_staleness_alert) lacks a liveness-by-progress check —
  false-positive "recycle worker" on long burst-committing autonomous runs
summary: >-
  On 2026-07-21 a review-role agent escalated slot 8 (unified-trading-pm, task
  `pm_qg_plan_discipline_and_frontmatter_regression-005`) THREE consecutive times (msgs 1577/1579/1581) as "genuinely
  wedged" and twice recommended a forced `/compact` or recycle. The signals it keyed on — `context_used_pct=100`,
  `last_msg` frozen at the boot-time "booted — resuming …" text, and worktree dirty ~75min — plus the system's own
  automated `sync_nudge_sent` (16:02, 16:32) and `git_staleness_alert_sent` (16:44) all fired with no worker response,
  which the review read as confirmation of a wedge. All of it was a FALSE POSITIVE: main verified at the process/git
  level that slot 8 was actively working the whole time — tool-use count climbed monotonically (101→117 across ~18min),
  a live `bash scripts/quality-gates.sh --no-fix` PID ran, fresh `scripts/plan-*` procs kept spawning, and the worktree
  committed in bursts (HEAD `1b3303be0` committed 25s before the 3rd escalation — i.e. AFTER the 16:44 staleness alert).
  A forced recycle would have destroyed an actively-committing 1h25m run plus a general-purpose sub-agent at ↓223k
  tokens. Root cause: every wedge/staleness detector in the fleet keys on heartbeat-freshness (`last_msg`/`context_pct`)
  and git-dirty-DURATION, both of which a long, bypass-permissions, burst-committing run defeats by construction — the
  worker neither posts heartbeats nor drains its inbox mid-run, and stays continuously dirty across a multi-commit span.
  None of the detectors consult an actual PROGRESS signal (recent-commit recency, live child-proc, or tool-use delta),
  so "not responding to nudges" is indistinguishable from "wedged."
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags:
  [
    agent-orchestrator,
    wedge-detection,
    worker-liveness,
    false-positive,
    sync-nudge,
    git-staleness-alert,
    liveness-by-progress,
    automation-calibration,
  ]
related: [plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [main-orchestrator-observation]
resolved_by:
locked_by:
depends_on: []
---

# What I found

Three consecutive review-role escalations (agent messages 1577 → 1579 → 1581, 2026-07-21 16:21–16:52) flagged slot 8 as
"genuinely wedged" and twice recommended a forced `/compact` or recycle to "unstick" it. The escalation confidence
climbed because the system's own remediation automation had already fired and been ignored:

- `sync_nudge_sent` at 16:02 and 16:32
- `git_staleness_alert_sent` at 16:44

The review reasonably concluded "automated remediation already tried and failed → genuinely wedged, needs a manual
recycle."

**It was a false positive.** Main (this orchestrator) verified at the OS/git level on each escalation that slot 8 was
continuously making forward progress:

- **tool-use count climbed monotonically**: 101 → 105 → 108 → 110 → 111 → 112 → 114 → 116 → 117 over ~18 min.
- **live processes** under `.tabs/8/`: a `bash scripts/quality-gates.sh --no-fix` PID mid-run (QG legitimately takes
  minutes), plus fresh `scripts/plan-*` python procs spawning every tick.
- **git commits in bursts**: HEAD was
  `1b3303be0 docs(plans): file instruments-service DERIBIT-COMBO test/golden drift finding`, committed **25 seconds
  before the 3rd escalation** — i.e. AFTER the 16:44 `git_staleness_alert`. The log showed a steady stream of recent
  `docs(plans):` commits from the batch archived-plan triage run.

A forced recycle/compact would have killed an actively-committing 1h25m run plus a general-purpose sub-agent at ↓223k
tokens.

# Root cause

Every wedge/staleness detector in the fleet — the review-role heuristic AND the automated `sync_nudge` /
`git_staleness_alert` — keys on **heartbeat freshness** (`last_msg`, `context_used_pct`) and **git-dirty duration**.
Both signals are defeated by construction by a long, bypass-permissions, burst-committing autonomous run:

- it does **not post a fresh `last_msg` heartbeat** mid-run (so `last_msg` stays frozen at boot text and `context_pct`
  pins at 100),
- it does **not drain its inbox** mid-run (so nudges land but get no response — which is NOT evidence of a wedge), and
- it stays **continuously dirty** across a multi-commit span (so git-dirty-duration crosses the staleness threshold even
  while committing).

None of the detectors consult a genuine PROGRESS signal, so "unresponsive to nudges" is indistinguishable from "wedged."

# The fix (proposed)

Add a **liveness-by-progress** gate that must be FALSE before any wedge escalation or auto-recycle fires. A worker is
NOT wedged if ANY of these advanced within the last ~5–10 min:

1. **commit recency** — `git -C <worktree> log -1 --format=%ct` newer than the alert window;
2. **live child proc** — any process whose cwd/argv is under the worker's worktree (`pgrep -f <worktree>`), especially a
   running `quality-gates.sh` / `pytest` / `basedpyright`;
3. **tool-use delta** — the pane's tool-use counter (or an equivalent server-side per-worker action counter) increased.

Wire this into (a) the `git_staleness_alert` / `sync_nudge` emitters so they suppress on live progress, and (b) the
review-role wedge heuristic. This mirrors the existing async-wait/poll discipline rule ("poll on a PROGRESS metric, flat
= stall") and the per-tab-worktrees liveness-gating (`kill -0`, mtime) — the wedge-detector just never got the
progress-signal half.

# Notes

- No work was lost — main intercepted all three escalations and declined the recycle each time (replies 1578, 1580,
  1582), backing the decision with process/git evidence.
- This is filed `assigned_vm: NA` / `execution_scope: local-only` because it modifies the orchestrator's own
  worker-safety automation, where a careless fix could SUPPRESS genuine wedge detection — operator should review the
  suppression predicate before it dispatches.
- Cross-cut: this is the same failure shape as the "heartbeat-alive-but-stalled" projection blind spot — the API
  projection (`last_msg`/`context_pct`) is not a liveness oracle; the OS/git layer is.
