---
doc_type: issue
title: >-
  TmuxSessionLossRateCanary firing 20+ breach/resolve cycles/day — dedup logic is correct, the
  threshold is likely too tight for this fleet's normal churn rate
summary: >-
  ao-watchdog (2026-08-18, this session) found `"tmux session loss rate RECOVERED"` firing 23x in
  24h and 18x the day before in `agent-orchestrator-alerts`, initially suspected as a dedup bug.
  Read `server/tmux_session_loss_rate_canary.py` directly: `_maybe_alert`'s state-transition dedup
  (`was_breached` sentinel, one page per breach episode, one RESOLVED per recovery) is correctly
  implemented, matching the DiskSpaceCanary pattern — NOT a dedup bug. The real likely cause:
  `tmux_session_loss_rate_min_count=3` within a `tmux_session_loss_rate_window_seconds=600` (10min)
  rolling window, checked every `tmux_session_loss_rate_interval_seconds=120` (2min)
  (`config.py:1049-1051`), was tuned for the 2026-08-10 incident's SPIKE signature (4 correlated
  losses at once) — but 3-in-10-min may be well within this fleet's normal respawn/rotation churn
  at 30+ concurrent slots, causing the threshold to be crossed and un-crossed repeatedly rather
  than only during genuine incidents. Not yet measured precisely — this doc records the hypothesis
  + the concrete next step, not a proven root cause.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao-watchdog, alerting, tmux-session-loss, tuning]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  Interactive /ao-watchdog run, 2026-08-18 (this session) — Slack channel pull
  (slack-read-channel.py agent-orchestrator-alerts 48) showed the repeat count; code read
  (server/tmux_session_loss_rate_canary.py, server/config.py) to rule out a dedup bug.
resolved_by:
locked_by:
---

# TmuxSessionLossRateCanary likely over-tuned, not under-deduped

## What was observed

`agent-orchestrator-alerts` Slack channel, bucketed by day (this session's 48h pull):
- Yesterday (0-24h ago): `"tmux session loss rate RECOVERED"` x23
- Day before (24-48h ago): x18

## What's confirmed NOT the cause

`server/tmux_session_loss_rate_canary.py`'s `_maybe_alert` (lines 137-163) implements the same
state-transition dedup every other canary in this family uses (mirrors `DiskSpaceCanary`): a
`dedup_state.load_bool_sentinel`/`save_bool_sentinel` breach flag, one page on breach (only if not
already breached), one RESOLVED page on recovery (only if previously breached), silent on every
still-breached or still-healthy tick in between. This is correct dedup — the repeat count is NOT a
missing-dedup bug.

## Leading hypothesis (not yet measured)

`config.py:1049-1051`:
```python
tmux_session_loss_rate_interval_seconds: int = 120   # check every 2 min
tmux_session_loss_rate_min_count: int = 3            # >=3 losses...
tmux_session_loss_rate_window_seconds: int = 600      # ...within any 10-min window
```

Per the module's own docstring, this was tuned for the 2026-08-10 incident's signature: "4
sessions across different agent kinds lost their tmux sessions simultaneously" — a correlated-kill
SPIKE. A threshold of 3-within-10-minutes may simply be within this fleet's normal variance at
30+ concurrent slots (boots alone ran ~133 in a recent 24h window per the same watchdog run,
~5.5/hour average, with real bursts around dispatch waves) — meaning the rolling count crosses 3
and drops back below it repeatedly through ordinary respawn/rotation/task-boundary churn, not
because 20+ genuine incidents happened. `_count_excluded_losses` already excludes
one_shot/scheduled-lifecycle agents and idle slots, which helps, but may not be enough at this
fleet size.

**Not yet measured**: the actual `tmux_session_lost` rate distribution over a representative
period (e.g. a full week), which would show whether 3-in-10-min is genuinely rare (supporting "the
canary is fine, these were real transient incidents") or routinely brushed (supporting "raise the
threshold and/or require N consecutive over-threshold ticks before paging, not a single rolling
snapshot").

## Follow-up

- [ ] [SCRIPT] P2. Query `ActivityRow` for `tmux_session_lost` events over the last 7 days,
      bucket into rolling 10-min windows the same way `_count_excluded_losses` does, and plot/
      count how often the count crosses 3. If it crosses routinely (say, >5x/day) outside any
      known incident window, that's direct evidence for raising the threshold. (repo:
      agent-orchestrator)
- [ ] [SCRIPT] P2. If confirmed over-tuned, raise `tmux_session_loss_rate_min_count` and/or
      `tmux_session_loss_rate_window_seconds`, OR add a "sustained N consecutive ticks over
      threshold" requirement (the interval is 120s — even 2 consecutive over-threshold ticks
      would filter out a single-tick blip while still catching a real multi-minute spike).
      Cite the measured baseline from the todo above in the commit, not a guessed number. (repo:
      agent-orchestrator)
