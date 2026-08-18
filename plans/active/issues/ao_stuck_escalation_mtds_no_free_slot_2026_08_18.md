---
doc_type: issue
title: >-
  Stuck escalation agt-ed7277 (market-tick-data-service, data_pipeline_failure) — 61 dispatch
  attempts, never once dispatched, "no free configured slot" — likely account-pool exhaustion,
  not an escalation-mechanism bug
summary: >-
  /escalation-queue-reconcile Step 1 (2026-08-18, this session) found escalation `agt-ed7277`
  (market-tick-data-service, data_pipeline_failure) stuck `status=queued`, `dispatched_at=null`,
  `attempts=61`, `reescalations=0`, `created_at` ~90+ min past the 45-min deadline,
  `last_error="no free configured slot to dispatch escalation onto"`. Step 2 confirmed
  escalation.py's tuning constants have NOT drifted (RESOLUTION_DEADLINE_MINUTES=45,
  MAX_REESCALATIONS=10, PAGE_AFTER_REESCALATIONS=2, RECONCILE_UNRESOLVED_WINDOW_HOURS=24 — all
  match expected) and the dedicated 3-slot CI-escalation reserve (`DEFAULT_CI_ESCALATION_SLOT_RESERVE`,
  config.py:436) is a real, correctly-sized mechanism, not itself misconfigured. The same watchdog
  run separately found the account pool heavily constrained right now (22 disabled + 5 rate_limited
  + 2 high_usage, no accounts reporting cleanly available) — this matches the EXACT root-cause class
  already diagnosed for the 2026-08-05 incident in
  `plans/archive/2026_08/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md` (there,
  "no free configured slot" traced to Claude account-pool exhaustion, not fleet/reserve saturation).
  Not yet confirmed with the same rigor that incident used (didn't trace which specific accounts the
  3 reserved slots are currently bound to) — flagging as the leading hypothesis, not a proven root
  cause.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao-watchdog, escalation-queue-reconcile, stuck-escalation, account-pool]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_08/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
    /cursor-configs/skills/escalation-queue-reconcile/SKILL.md,
  ]
created: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  Interactive /ao-watchdog + /escalation-queue-reconcile run, 2026-08-18 (this session) — GET
  /api/escalations/active surfaced the stuck row; escalation.py + config.py read directly to rule
  out mechanism drift.
resolved_by:
locked_by:
---

# Stuck escalation agt-ed7277 — likely account-pool exhaustion, not an escalation-mechanism bug

## The row (as pulled 2026-08-18 ~08:xx UTC)

```json
{
  "escalation_id": "agt-ed7277",
  "status": "queued",
  "repo": "market-tick-data-service",
  "wall_type": "data_pipeline_failure",
  "created_at": "2026-08-18T07:36:19.571735+00:00",
  "dispatched_at": null,
  "resolved_at": null,
  "resolution": null,
  "attempts": 61,
  "reescalations": 0,
  "last_error": "no free configured slot to dispatch escalation onto"
}
```

`reescalations=0` and `resolved_at=null` rule out the re-escalation-aware exception in the
`/escalation-queue-reconcile` skill's own Step 1 (that exception is for a row judged by
`resolved_at` after a `still_red_reescalated` flip — this row never got that far). Judged on its
real `created_at`, it is genuinely stuck: 61 attempts, zero successful dispatches, ~90+ minutes
past the 45-minute deadline.

## What's confirmed NOT the cause

- `escalation.py` tuning constants match expected values exactly — no reverted/drifted constant.
- `DEFAULT_CI_ESCALATION_SLOT_RESERVE = 3` (`config.py:436`) is live and the reserved-slot-id
  derivation (`ci_escalation_reserved_slot_ids`, top-3 non-review slot ids) is intact — this
  mechanism was built for exactly this wall_type (`data_pipeline_failure` is one of the three
  covered types per its own docstring).
- The 3 highest-numbered non-review slots showed live tmux sessions at investigation time — the
  reserve isn't structurally *absent*, so this doesn't look like a config/reserve-sizing bug on
  its face.

## Leading hypothesis (not yet fully proven)

The same watchdog run's account-pool check found `accounts_summary: {disabled: 22, rate_limited:
5, high_usage: 2}` — no account reporting cleanly available. If the 3 CI-escalation-reserved slots
are themselves bound to disabled/rate-limited accounts, "no free configured slot" would read
literally true even though the slot *processes* exist — this is the exact shape the 2026-08-05
incident (`ao_scheduled_job_reserve_and_staggering_2026_08_04.md`) already diagnosed: 94% of that
day's `no free configured slot`-flavored failures traced to Claude account exhaustion, not fleet
saturation, not a reserve-sizing bug.

**Not yet confirmed**: which accounts the 3 reserved slots (highest-numbered non-review slot ids at
the time) are currently bound to, and whether those specific accounts are among the
disabled/rate-limited set. That's the next concrete step to fully close this out.

## Follow-up

- [ ] [SCRIPT] P1. Confirm which accounts the current CI-escalation-reserved slots are bound to
      and cross-check against the disabled/rate_limited list — if confirmed, this closes as
      "account exhaustion, self-resolving as accounts reset" (same disposition as the 2026-08-05
      incident); if NOT confirmed, this is a live escalation-mechanism bug needing a fresh Step-2
      diagnosis. (repo: agent-orchestrator)
- [ ] [SCRIPT] P2. Pull `overage_disabled_reason` (the real field — this session's first pass
      queried the wrong field name and got nulls) for the 22 disabled accounts to understand
      whether this is a temporary overage window or something needing operator action. (repo:
      agent-orchestrator)
