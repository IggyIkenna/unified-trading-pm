---
doc_type: issue
title: >-
  Stuck escalation agt-ed7277 (market-tick-data-service, data_pipeline_failure) — CONFIRMED: all
  3 CI-escalation-reserved slots (32, 33, 9001) are themselves paused, not an account-exhaustion
  or escalation-mechanism bug
summary: >-
  /escalation-queue-reconcile Step 1-2 (2026-08-18, this session) found escalation `agt-ed7277`
  (market-tick-data-service, data_pipeline_failure) stuck `status=queued`, `dispatched_at=null`,
  attempts climbing (61 -> 103 across the session), `last_error="no free configured slot to
  dispatch escalation onto"`. escalation.py's tuning constants are confirmed NOT drifted, and the
  dedicated 3-slot CI-escalation reserve (`DEFAULT_CI_ESCALATION_SLOT_RESERVE=3`, config.py:436)
  is correctly sized. **Root cause CONFIRMED (not just hypothesized)**: the actual 3 reserved slot
  ids are 32, 33, and 9001 (the top-3 non-review slot ids at the time) — `GET /api/state` shows
  ALL THREE currently `status=paused`, `worker_alive=false`. That alone fully explains "no free
  configured slot" regardless of account health: the reserve is structurally paused, not just
  capacity-constrained. A secondary, real risk: slots 32 and 33 are BOTH bound to the SAME account
  (`sub-b-iggy2london`, `status=high_usage`, 88% of its weekly message limit used, `overage_status:
  rejected`/`overage_disabled_reason: out_of_credits` — so it cannot burst past quota via overage)
  — even once unpaused, 2 of the 3 reserved slots draw from one shrinking budget. Slot 9001 has no
  account bound at all (`account_id: null`). This is NOT the same root-cause class as the
  2026-08-05 incident (`ao_scheduled_job_reserve_and_staggering_2026_08_04.md`, pure account-pool
  exhaustion) — that was this doc's initial hypothesis before the slot-level data came in; corrected
  here rather than left standing, per the workspace's own "fix a misleading doc in the same turn"
  rule.
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
depends_on: []
---

# Stuck escalation agt-ed7277 — CONFIRMED: the 3 reserved slots are themselves paused

## The row (last pulled 2026-08-18 ~09:27 UTC)

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
  "attempts": 103,
  "reescalations": 0,
  "last_error": "no free configured slot to dispatch escalation onto"
}
```

`reescalations=0` and `resolved_at=null` rule out the re-escalation-aware exception in the
`/escalation-queue-reconcile` skill's own Step 1 — this row never reached that cycle. Attempts
climbed 61 -> 103 over roughly 40 minutes of this session with zero successful dispatches: the
mechanism is retrying correctly, it just has nowhere to land.

## What's confirmed NOT the cause

- `escalation.py` tuning constants match expected values exactly — no reverted/drifted constant.
- `DEFAULT_CI_ESCALATION_SLOT_RESERVE = 3` (`config.py:436`) is live and correctly sized.

## CONFIRMED root cause

`GET /api/state` slot data:

```json
[
  {"slot_id": 32, "status": "paused", "account_id": "sub-b-iggy2london", "worker_alive": false},
  {"slot_id": 33, "status": "paused", "account_id": "sub-b-iggy2london", "worker_alive": false},
  {"slot_id": 9001, "status": "paused", "account_id": null, "worker_alive": false}
]
```

Slots 32/33/9001 ARE the current CI-escalation reserve (top-3 non-review slot ids). **All three are
individually paused with `worker_alive: false`** — the reserve mechanism and account pool are both
fine in the abstract; the concrete, physical slots reserved for escalation dispatch simply cannot
spawn anything right now because they're paused. This fully explains "no free configured slot"
without needing an account-exhaustion story at all.

**Secondary risk, worth fixing even after unpausing**: slots 32 and 33 are both bound to the SAME
account, `sub-b-iggy2london` (operator-identified live in chat) — `status: high_usage`,
`weekly_pct: 88` (1056/1200 weekly messages used, resets 2026-08-23), `five_hour_pct: 17` (healthier
short-term), `overage_status: rejected`, `overage_disabled_reason: out_of_credits` (cannot burst
past its plan quota). Two of the three reserved slots drawing from one account nearing its weekly
cap is a single point of failure for the whole reserve. Slot 9001 has no account bound at all
(`account_id: null`) — it can't dispatch anything regardless of pause state until one is assigned.

## Follow-up

- [x] [SCRIPT] P1. Confirm which accounts the current CI-escalation-reserved slots are bound to —
      DONE, see above. Root cause is the pause state, not account exhaustion. (repo:
      agent-orchestrator)
- [ ] [OPERATOR] P1. Decide whether to resume slots 32/33/9001 now — asked live in chat
      2026-08-18, awaiting the operator's answer at time of filing. (repo: agent-orchestrator)
- [ ] [SCRIPT] P2. Assign a real account to slot 9001 (`account_id: null` today) and consider
      spreading 32/33 across two different accounts instead of double-booking sub-b, so the
      reserve doesn't share a single quota ceiling. (repo: agent-orchestrator)
- [ ] [SCRIPT] P2. Pull `overage_disabled_reason` for the other 21 disabled accounts (the field
      name this session's first pass got wrong) to understand whether that's a temporary overage
      window or something needing operator action — separate from this specific stuck row, but
      surfaced by the same investigation. (repo: agent-orchestrator)
