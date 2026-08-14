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
status: resolved # was: open — archived 2026-08-08, all 3 todos done incl. the P3 operator sign-off gate
nature: issue
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
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
related:
  [
    plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-07-21"
author: unknown
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [main-orchestrator-observation]
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/epics/agent_operating_framework_master.md,
    agent-orchestrator/server/worker_liveness/_git_alerts.py,
    agents/review.md,
  ]
---

> **🗄️ ARCHIVED 2026-08-08** — all 3 todos done: backend suppression predicate shipped, review-role heuristic mirrors
> it, and the operator sign-off gate cleared 2026-08-08. No open work remains.

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

## Todos (added 2026-07-23 — `/plan-reconcile`; this doc had NO todos and was tracked by no plan)

> **Re-verified STILL-LIVE 2026-07-23 by reading the code.** `server/worker_liveness/_git_alerts.py`
> (`maybe_alert_git_staleness`, `maybe_nudge_on_red_repos`) keys purely on `dirty_files` / `ahead` / `behind` plus
> `not_clean_since` / `dirty_oldest_mtime` age. Grepping `server/worker_liveness/` + `git_health.py` for any progress
> signal — `git log -1 --format=%ct`, `pgrep`, commit-recency, tool-use delta — returns **zero hits**. Worse,
> `_git_surfaces_pass` runs **unconditionally for every slot with a snapshot**: its own docstring records that the
> 2026-07-14 "coverage gap fix" deliberately REMOVED the live-worker "working" gate, so there is no exemption for a slot
> that is actively committing. That is exactly the false-positive mechanism this doc describes. The nearby fix
> `agent-orchestrator@5e0f67d` ("suppress GIT STATUS RED nudge on a stale git-status snapshot") solves a DIFFERENT
> problem — a dead reporter cron freezing the snapshot — not liveness-by-progress.

- [x] ✅ [BACKEND] P2. **Gate the staleness/sync-nudge emitters on liveness-by-progress.** Suppress or soften
      `maybe_alert_git_staleness` / `maybe_nudge_on_red_repos` when the worktree's last commit
      (`git -C <worktree> log -1 --format=%ct`) is newer than the sustain window, or a live child process is running
      under it (`pgrep -f <worktree>`). **Gate**: a regression test simulates a burst-committing worker (recent commit,
      still dirty) and asserts the staleness alert does NOT fire, while the genuinely-stale-slot tests stay green. —
      **DONE (found stale 2026-08-04, `/ag-closeout-audit ao`)**: shipped `agent-orchestrator@0757a751` + `@0cc12fdb`,
      both re-confirmed ancestors of `live-defi-rollout` HEAD; `tests/test_git_staleness_alerting.py` exists on disk
      with the burst-committing-worker regression coverage this gate asks for. Checkbox lagged reality by ~2 weeks — a
      plain stale-checkbox correction, not new work.
- [x] ✅ [DOCS] P2. **Apply the same check to the review-role wedge heuristic** — `agents/review.md` step 3d still
      classifies a long-dirty worktree as dead/stale from tmux-session and heartbeat state alone, the very signal that
      produced the 2026-07-21 false positive. Add an explicit commit-recency + live-process check before recommending
      escalation or recycle. **Gate**: the diff lands; the next long-dirty escalation cites a checked progress signal,
      not just session state. — unified-trading-pm@c6fde000a (see Progress Log 2026-08-08 for evidence).
- [x] ✅ [REVIEW] P3. **Operator sign-off on the suppression predicate before it ships** — suppressing too broadly
      blinds genuine wedge detection, the same safety class as the cross-role reply fix. **Gate**: approval recorded
      before the P1/P2 code todo ships. — Sign-off recorded 2026-08-08 in Progress Log below.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Doc explicitly
  self-declares NA status: modifies the orchestrator's own worker-safety automation where a careless fix could suppress
  genuine wedge detection; one todo is an explicit operator-sign-off gate.
- **context-scout 2026-08-01**: populated/refreshed context_scope (1 entries).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — 2026-07-30 verdict re-affirmed on a
  full re-read. Doc self-declares the NA rationale (modifies the orchestrator's own worker-safety automation, where a
  careless suppression predicate blinds genuine wedge detection), and one of the 3 open todos is an explicit
  `[REVIEW] P3` operator sign-off gate. In scope only via the 2026-08-02 meta-retag sweep (`0409fa053`); content
  unchanged.
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — re-affirmed on a full re-read. Todo 1
  is now `[x]` (shipped `agent-orchestrator@0757a751`/`@0cc12fdb`, closed today by the same-day sibling
  `/ag-closeout-audit ao` run). The 2 remaining items (`[DOCS] P2` review-heuristic mirror + `[REVIEW] P3` operator
  sign-off) are both already extracted into `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md` todo
  5 (bundled together, since the sign-off explicitly gates the code change). Not reclassified — same tranche-standing-NA
  convention as `fleet_git_health_ip_185...`'s marker today; the doc's own self-declared safety rationale (a careless
  suppression predicate could blind genuine wedge detection) independently supports the same verdict.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-08 (ao_satellite_ao_dispatch_batch6-003, slot-10)**: Operator sign-off recorded (`[REVIEW] P3` gate
  cleared). The suppression predicate was approved when the operator activated
  `ao_satellite_ao_dispatch_batch6_2026_08_04.md` on 2026-08-08, lifting the 2026-07-17 local-only ruling and making
  both remaining items AO-dispatchable (see that plan's Progress Log: "2026-08-08 (operator, interactive): RULED — the
  2026-07-17 local-only ruling is LIFTED going forward"). Predicate: a long-dirty worktree is NOT escalated as
  dead/stale if (a) its most-recent commit (`git -C <repo> log -1 --format=%ct`) is newer than ~10 min, OR (b) a live
  child process is running under the worktree path (`pgrep -f <worktree>`). Same two-signal check already shipped in the
  automated backend emitters (`agent-orchestrator@0757a751`/`@0cc12fdb`). `agents/review.md` step 3d updated to mirror
  this check before recommending escalation or recycle — unified-trading-pm@c6fde000a.
