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
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /plans/active/issues/plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md,
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
depends_on: []
context_scope:
  [
    agent-orchestrator/server/tmux_session_loss_rate_canary.py,
    agent-orchestrator/server/config.py,
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /plans/active/issues/plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md,
    /plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md,
  ]
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

## Convergence note (2026-08-18, cross-doc audit)

This is NOT the same mechanism as `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` (that doc's confirmed root
cause — a shared ambient tmux socket killable by any process's bare `kill-server`/`rm -rf` — explains why a session
DIES; this doc is about whether the ALERT correctly counts deaths that already happened, a distinct statistics
question) — not merging into it. It IS the direct follow-on to the canary
`plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md` recommended and shipped
(`agent-orchestrator@cc3b5b4`), and it shares a specific, previously-unlinked insight with the root-cause doc: that
doc's own still-open P3 todo notes `check-ao-recent-deaths.sh`'s `burst_size` conflates ordinary `reason="manual"`
`one_task_per_session` recycle-teardowns with genuine losses — proven for its 2026-08-14 23:33 cluster, where 3 of 5
counted "losses" were confirmed benign recycles, not crashes. `_count_excluded_losses` already excludes
`one_shot`/`scheduled` agents and `idle`-status slots, but per that same finding may NOT exclude a benign recycle on
an otherwise-active slot — the exact gap this doc's own hypothesis needs measured. The follow-up below is revised to
check for this directly rather than only counting raw crossings.

## Follow-up

- [x] N. ✅ [SCRIPT] P2. Query `ActivityRow` for `tmux_session_lost` events over the last 7 days,
      bucket into rolling 10-min windows the same way `_count_excluded_losses` does, and plot/
      count how often the count crosses 3. If it crosses routinely (say, >5x/day) outside any
      known incident window, that's direct evidence for raising the threshold below. **For each
      crossing, also cross-reference every member against a preceding `reason="manual"`
      `SESSION-TEARDOWN` log line within ~60s** (the method
      `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` already proved out for its
      2026-08-14 23:33 cluster) — if crossings are dominated by benign recycles rather than genuine
      losses, that's a DIFFERENT fix (exclude `reason="manual"` from the count) than raising the
      raw threshold. (repo: agent-orchestrator) Extracted to `/plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 3 (na-eligibility-audit 2026-08-19, ao tranche, RECLASSIFY per-todo split).
- [ ] [SCRIPT] P2. If confirmed over-tuned, raise `tmux_session_loss_rate_min_count` and/or
      `tmux_session_loss_rate_window_seconds`, OR add a "sustained N consecutive ticks over
      threshold" requirement (the interval is 120s — even 2 consecutive over-threshold ticks
      would filter out a single-tick blip while still catching a real multi-minute spike).
      Cite the measured baseline from the todo above in the commit, not a guessed number. (repo:
      agent-orchestrator) **Ordering NOT machine-enforced**: this todo is conditioned on the
      confirming measurement extracted to `/plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md`
      item 3 — no `depends_on`/`gate_on_depends` links the two, the ordering rests on this prose note only.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:96033122b406632d]: RECLASSIFY (per-todo split) — todo 1 (7-day ActivityRow rate measurement) extracted to `/plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 3. Doc stays NA for todo 2 (the raise-threshold action, correctly conditional on todo 1's own result).
- **context-scout 2026-08-19**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — sole remaining item (raise the threshold once confirmed over-tuned) stays explicitly conditioned on the measurement extracted to `/plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 3, not yet landed; not a standalone bounded action.
- **/plan-reconcile ao 2026-08-22 — CORRECTION to the entry immediately above**: that measurement HAD already landed
  when the note was written. `ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 3 is `[x]` ("**DONE — see Progress
  Log 2026-08-20**"), and that doc's 2026-08-20 entry carries the full result: 1,760 qualifying losses (10.46/hour),
  **194 threshold-crossing episodes in seven days (27.71/day)** simulating the canary's 120s tick over a 600s window
  at threshold 3, of which only **8 of 1,048 crossing-member rows (0.8%)** had a preceding
  `SESSION-TEARDOWN ... reason=manual` line within 60s. The gating condition for this doc's remaining
  raise-the-threshold todo is therefore **satisfied**, and that todo is now actionable rather than blocked.
