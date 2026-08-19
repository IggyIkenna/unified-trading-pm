---
doc_type: issue
title: >-
  Proactive worker-slot account failover (agent-orchestrator@78a9a02) never fires for weekly/5-hour
  ceiling exhaustion — account_is_usable() doesn't check it
summary: >-
  Operator observed multiple sports_taxonomy_p4_backfill-related slots still pinned to account
  sub-b-iggy2london, which the operator believes is exhausted, despite a recently-shipped
  "proactive worker-slot account failover" fix. Investigation confirmed the fix IS deployed and
  live, but its usability check (account_is_usable()) only looks at rate_limited_until / auth-failed
  cooldown / account_status=="disabled" — never weekly_pct, five_hour_pct, or overage_status. Live
  query on the VM found sub-b-iggy2london at account_status=healthy, rate_limited_until=NULL,
  weekly_pct=95, five_hour_pct=4, overage_status=rejected — genuinely near its weekly ceiling by the
  richer signal, but invisible to the failover mechanism's narrower check. Confirmed zero
  worker_account_unusable_killed activity_log rows have ever fired.
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, account-failover, fleet-capacity]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/state_store/account_usage.py,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator, interactive session, 2026-08-19: dashboard screenshot showing several
  sports_taxonomy_p4_backfill tasks still associated with sub-b-iggy2london, asking why the
  recently-shipped proactive worker-slot account failover (agent-orchestrator@78a9a02) apparently
  didn't kick in. Investigated by a background agent this session (read-only, no code changes) —
  full findings below.
assigned_role: infra
drift_direction: none
---

# Proactive worker-slot account failover doesn't cover weekly/5-hour ceiling exhaustion

## What the shipped fix (`agent-orchestrator@78a9a02`) actually does

`AutoSpawnLoop._drain_worker_account_failover` (`server/autospawn.py`, called every AutoSpawn tick
from `_drain_escalations`) generalizes the main-agent's proactive failover to ordinary worker
slots. Each tick: queries `SlotRow` where `status IN ("working","blocked","idle")` and
`account_id IS NOT NULL`, excluding `review_slot_ids()`/`human_slot_ids()`. For each candidate,
calls `account_is_usable(session, account_id)`; if `False`, kills the tmux session (rate-limited
to one kill per cooldown per slot) and logs `worker_account_unusable_killed`. It deliberately does
nothing else — no resume, no requeue, no account re-pick; that's left to the existing
`tmux_pruner` (classifies the kill as an ordinary death) and `_resume_pass` (re-picks an account,
degrading through providers/models via `select_account_for_spawn`'s fallback chain).

Tests: `tests/test_autospawn.py:715-841`. No plan/issue doc exists for this specific 2026-08-19
change (only the 2026-06-17 archived plan for the *original* main-agent version) — this doc is the
first tracking artifact for it.

## Root cause: the usability signal doesn't cover this exhaustion mode

`account_is_usable()` (`server/state_store/account_usage.py:340-351`) checks only
`rate_limited_until`, an auth-failed cooldown, and `account_status == "disabled"`. It never
consults `weekly_pct`, `five_hour_pct`, or `overage_status` — those feed
`pick_next_account(require_headroom=True)` at NEW-dispatch time only, not this kill-check.

Live query on the VM's `account_usage` row for `sub-b-iggy2london`:
`account_status=healthy, rate_limited_until=NULL, weekly_pct=95, five_hour_pct=4,
overage_status=rejected`. Genuinely near its weekly ceiling by the richer signal — matching the
operator's belief — but `account_is_usable()` sees a perfectly healthy account and never triggers
a kill. Confirmed: zero `worker_account_unusable_killed` activity_log rows exist, ever, on this VM.

## Secondary factor observed

24 of 33 iggy2london-bound slots were already `status="paused"` (activity_log shows they were
paused 2026-08-18 ~07:14-07:24 UTC — ~21h *before* the failover fix even existed, via
`POST /api/slots/{id}/pause`). Paused slots are outside the failover candidate query's
`("working","blocked","idle")` filter regardless of account state, so they wouldn't be touched by
this mechanism even if the usability check were fixed.

## Genuine ambiguity, not yet resolved

At investigation time, no `SlotRow.current_task` matched `sports_taxonomy_p4_backfill`, and the
backlog API showed all 15 related tasks `status=queued, dispatched_to=None` — i.e. nothing was
actively running against `sub-b-iggy2london` at that instant. The operator's dashboard observation
may reflect a different moment than this snapshot; worth a fresh live check before/alongside a fix.

## Follow-up

- [ ] [BACKEND] P2. **Widen `account_is_usable()` (or add a second check
      `_drain_worker_account_failover` also consults) to treat a near-ceiling account
      (`weekly_pct`/`five_hour_pct` above some threshold, or `overage_status == "rejected"`) as
      unusable too** — not just `rate_limited_until`/disabled/auth-failed. Needs an operator
      decision on the right threshold (matching whatever `pick_next_account(require_headroom=True)`
      already uses, or a deliberately different one for the kill-vs-avoid distinction). Repo:
      agent-orchestrator.
- [ ] [OPERATOR] P3. **Decide whether paused slots should also be swept by the account-failover
      check**, or whether "paused" is correctly out of scope (an operator already took it out of
      rotation for a reason unrelated to account exhaustion). Not obviously a bug — needs a ruling,
      not just a code change.
- [ ] [SCRIPT] P3. **Re-check live whether any `sports_taxonomy_p4_backfill`-related slot is
      currently actively running (not just queued) against `sub-b-iggy2london`**, to confirm
      whether the operator's original observation still reproduces, before/alongside landing the
      fix above.
