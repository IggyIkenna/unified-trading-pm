---
doc_type: issue
title:
  Fleet-git RED Slack pages fired at 50 minutes when most episodes were slots mid-long-task, not wedged — raised to 90
  minutes
summary:
  Operator watched a live paging burst (slots 2, 3, 7, 9, 11, 12) where most RED episodes auto-recovered within about 20
  minutes of paging under extreme shared-repo commit velocity — a slot mid-long-task routinely sits AHEAD or behind for
  well over 50 minutes before it reaches a natural commit/push point. Raised GIT_RED_SUSTAIN_S from 50 to 90 minutes;
  also fixed the Slack/GCS alert text hardcoding a stale "30min" label disconnected from the real constant.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, alerting, slack, fleet-git, threshold, noise]
related:
  [
    /plans/archive/issues/ao_dispatch_health_idle_slot_thrash_2026_07_26.md,
    /plans/archive/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: NA
drift_direction: advance-code
depends_on: []
resolved_by:
  interactive session, 2026-07-27, agent-orchestrator (GIT_RED_SUSTAIN_S 50m->90m + stale-threshold-text fix, QG green,
  shipped via quickmerge)
locked_by:
supersedes:
superseded_by:
source:
  Operator pasted a live run of agent-orchestrator-alerts Slack pages (2026-07-26 22:39-23:01 UTC, slots 2/3/7/9/11/12)
  plus a dashboard screenshot, asking why slots showing clean in the UI had just paged RED, and directing the sustain
  threshold be raised — first to "maybe raise the threshold to 1 hour", then explicitly revised to "90 mins" after
  watching several episodes auto-recover (RECOVERED bookends for slots 4, 7, 12 all within ~20 minutes of their pages).
---

> **🟢 RESOLVED 2026-07-27** — `GIT_RED_SUSTAIN_S` raised 50m->90m, stale hardcoded threshold text fixed, QG green (48
> tests passing across both affected files), shipped via quickmerge.

# Fleet-git RED threshold too tight for long-task slots — 2026-07-27

> **🟢 RESOLVED 2026-07-27** — `GIT_RED_SUSTAIN_S` raised 50m->90m + stale-threshold-text fix shipped and verified same
> session; all 48 tests in the two affected files pass.

## What I found

`agent-orchestrator/server/worker_liveness/_git_alerts.py` pages the operator (`agent-orchestrator-alerts` Slack
channel) when any repo in a slot's git snapshot has been RED (dirty / ahead / diverged / clean-but-behind) sustained for
`GIT_RED_SUSTAIN_S` — already raised once from 30 to 50 minutes on 2026-07-24 for exactly this class of noise. The
operator's live paste showed the same pattern recurring at 50 minutes: six slots (2, 3, 7, 9, 11, 12) all paged RED
within a 20-minute window (22:39-22:58 UTC), and by 00:01 UTC three of them (4, 7, 12) had already posted the
`:white_check_mark: ... git RECOVERED` bookend — i.e. the episode was a slot legitimately mid-long-task (a long QG run,
then commit + push), not a genuinely wedged repo. Under this workspace's extreme shared-repo commit velocity (a peer
pushing every 1-2 minutes, confirmed repeatedly this session), a slot doing real work routinely doesn't reach a natural
commit point for well over 50 minutes.

Separately, while reading `server/notifications/slack.py::notify_git_staleness_red` to build the fix, found the paged
Slack header and the GCS-persisted alert message both hardcoded the literal string `"30min"` — completely disconnected
from the actual `GIT_RED_SUSTAIN_S` constant, which was already 50 minutes at the time (and is now 90). Every RED page
since the 2026-07-24 raise has been telling the operator the wrong threshold.

## The fix

- `GIT_RED_SUSTAIN_S`: `50 * 60` → `90 * 60`, with an inline comment recording the operator's live-observed rationale
  (mirrors the existing 30→50 comment's style).
- `notify_git_staleness_red` gained a `sustain_threshold_min: int = 90` parameter, threaded through from the caller's
  `GIT_RED_SUSTAIN_S // 60`, replacing both hardcoded `"30min"` occurrences (the Slack header and the GCS alert message)
  so the paged text always matches the real constant, including future re-tunings.
- Updated the module docstring's stale "≥30 min" reference and the stale `50 * 60` default on
  `FleetGitHealthSummary.git_red_sustain_secs` (`server/models/git_health.py`) for consistency (both routes that
  construct this model already pass the real constant explicitly, so this was a dead-but-misleading default, not a live
  bug).
- `tests/test_git_staleness_alerting.py`: every fixture using a fixed "sustained" age (`dirty_age_min=55` /
  `ncs_age_min=55`, previously just past the old 50-min threshold) bumped to 95 (just past the new 90-min threshold),
  including the matching assertion strings and one test's name/docstring. All 48 tests in the two affected files pass.

`GIT_RED_REALERT_S` (4h re-remind) and `GIT_CLEAN_CONFIRM_S` (15-min sustained-clean confirm before the RESOLVED bookend
fires) were left untouched — the operator's directive was specifically about the initial RED sustain threshold, and the
15-minute clean-confirm lag is exactly what made the very first screenshot in this session look like "no resolved ever
fires" (it hadn't been 15 minutes yet) before the operator's own follow-up paste confirmed the bookend does fire once
that window elapses.

## Why it matters

A pager that fires on normal, self-resolving activity trains the operator to ignore it — the opposite of what
`agent-orchestrator-alerts` is for (actionable-only channel, per
`/codex/04-architecture/agent-orchestrator-alerting.md`). Getting the sustain threshold closer to "actually wedged"
keeps the channel meaningful.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only channel contract, RESOLVED-bookend
  requirement (confirmed still correctly implemented by `_maybe_fire_staleness_resolved`, not touched by this fix).
