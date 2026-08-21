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
  is correctly sized. **Root cause CONFIRMED (not just hypothesized)**: the REAL reserve is slots
  31/32/33 (an earlier pass wrongly included human slot 9001 — corrected below) — all three were
  `status=paused`, `worker_alive=false`, and all three bound to the SAME account (sub-b-iggy2london,
  88% weekly usage). Resumed via `POST /api/slots/{id}/resume`, operator-approved live in chat.
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
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
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
context_scope:
  [
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/config.py,
    /plans/active/ao_human_fleet_integration_2026_08_15.md,
    /plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md,
    cursor-configs/skills/escalation-queue-reconcile/SKILL.md,
  ]
---

> **🟢 ARCHIVED 2026-08-21** — all todos resolved and evidence-backed (account-spread self-corrected
> once [[ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21]]'s bugs 1-5 landed; see
> [[ci_escalation_reserve_slots_claimed_by_class_a_dispatch_2026_08_21]] for the live re-check).

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

## CONFIRMED root cause (corrected — see below)

**Correction (same session, minutes later): the first pass's `top-3 non-review slot ids` heuristic
did not exclude human-operator slots (`config.human_slot_ids()`, `DEFAULT_HUMAN_SLOTS = (9001,
9002)`, `ao_human_fleet_integration_2026_08_15.md`) and wrongly swept slot 9001 (Ikenna's own
human slot) into the guessed reserve. The operator caught this live. Re-derived excluding
`human_slot_ids()` — the REAL reserve is slots 31/32/33, not 32/33/9001.**

`GET /api/state` slot data (corrected):

```json
[
  {"slot_id": 31, "status": "paused", "account_id": "sub-b-iggy2london", "worker_alive": false, "kind": "worker"},
  {"slot_id": 32, "status": "paused", "account_id": "sub-b-iggy2london", "worker_alive": false, "kind": "worker"},
  {"slot_id": 33, "status": "paused", "account_id": "sub-b-iggy2london", "worker_alive": false, "kind": "worker"}
]
```

**All three real reserve slots — not just two — are bound to the SAME account** (`sub-b-iggy2london`,
`status: high_usage`, `weekly_pct: 88` — 1056/1200 weekly messages used, resets 2026-08-23,
`five_hour_pct: 17`, `overage_status: rejected`/`overage_disabled_reason: out_of_credits` so it
cannot burst past quota) **and all three are individually `paused`, `worker_alive: false`.** This
fully explains "no free configured slot" without any account-exhaustion story — the reserve is
100% single-account-concentrated AND fully paused, a more severe single-point-of-failure than the
"2 of 3" first draft stated.

Slot 9001 (human, Ikenna's) is unrelated to this escalation-reserve mechanism entirely — its own
`paused`/`worker_alive: false`/`account_id: null` state reflects no interactive human session
currently connected to it, not a bug in the escalation path. Investigating whether ITS state
correctly reflects reality (the operator separately flagged the human-fleet dashboard overview as
"not seeming to work") is tracked as its own, unrelated finding — not part of this doc.

## Remediation applied

**2026-08-18, operator-approved live in chat**: resumed slots 31/32/33 via
`POST /api/slots/{id}/resume`. All three flipped `status: paused -> idle` successfully.
`worker_alive` was still `false` immediately after (resume only changes eligibility for the
autospawn loop to claim the slot on its next tick — it doesn't force-spawn synchronously), and
`agt-ed7277` was still `queued`/`attempts=107` at the moment of the resume call. **Not yet
re-verified past that point** — the next `/escalation-queue-reconcile` Step 1 check (or a manual
`GET /api/escalations/active`) should confirm this row actually dispatches once the reserve slots
spawn workers.

## Follow-up

- [x] [SCRIPT] P1. Confirm which accounts the current CI-escalation-reserved slots are bound to —
      DONE (corrected to 31/32/33, all sub-b). (repo: agent-orchestrator)
- [x] [OPERATOR] P1. Decide whether to resume the reserve slots — operator approved live
      2026-08-18; applied (see Remediation above). (repo: agent-orchestrator)
- [x] [SCRIPT] P1. Re-verify `agt-ed7277` actually dispatched successfully after the resume +
      next autospawn tick — CONFIRMED: `status: dispatched` at attempts=108 (was still `queued` at
      107). `agt-8717c2` (deployment-service) also flipped to `dispatched`. One residual effect
      observed, not a new bug: `agt-63a017` (unified-trading-pm) hit the SAME "no free configured
      slot" error at 17 attempts once 2 of the 3 reserve slots were claimed by the two dispatches
      above — expected queue-draining contention with only a 3-slot reserve, not a regression; ties
      directly into the "spread across multiple accounts" follow-up below (a 3-slot single-account
      reserve saturates fast under simultaneous escalations). (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P2. **RESOLVED 2026-08-21.** Spread 31/32/33 across more than one account
      instead of triple-booking sub-b — today's incident is exactly what a single-account reserve
      produces the moment that one account gets paused/exhausted. **Operator decision 2026-08-21**:
      assigned to the agent already working
      [[ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21]], whose bugs 1-5 landed same
      day (`agent-orchestrator@e3a3ef4166` → `@ba855161ae`). Confirmed self-corrected per
      [[ci_escalation_reserve_slots_claimed_by_class_a_dispatch_2026_08_21]]'s own re-check: 31/32/33
      now occupied by 3 different accounts (zero `codex-luna`), and all escalation dispatches in the
      4.5h window since the fix spread across 6 distinct accounts with no single-account monopoly.
      (repo: agent-orchestrator)
- [x] N. ✅ [SCRIPT] P2. Pull `overage_disabled_reason` for the other 21 disabled accounts (the field
      name this session's first pass got wrong) to understand whether that's a temporary overage
      window or something needing operator action — separate from this specific stuck row, but
      surfaced by the same investigation. Cross-reference against the in-progress provider-
      onboarding plans (`deepseek_claude_blended_provider_routing_2026_07_28.md`,
      `grok_gemini_translation_proxy_2026_08_14.md`, `codex_luna_flex_bridge_2026_08_14.md`,
      `kimi_gemma_provider_onboarding_2026_08_16.md`) before treating any of them as anomalous —
      operator confirmed 2026-08-18 these disabled non-Anthropic accounts are largely expected,
      mid-onboarding/testing. (repo: agent-orchestrator) Extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 10 (na-eligibility-audit 2026-08-19, ao tranche, RECLASSIFY per-todo split).
- [x] N. ✅ [SCRIPT] P2. `/api/agents` returns ZERO rows for human slots (`human_agent_rows: []` when
      checked live 2026-08-18) — if the dashboard's human-fleet overview reads from this endpoint,
      that's why it "doesn't seem to work" per the operator. Needs its own investigation into which
      endpoint the human-fleet overview actually consumes and whether human-slot rows should be
      added to `/api/agents` or the overview should read `/api/state`'s `slots[]` instead. Filed
      here as a pointer, not a full diagnosis — deserves its own issue doc if it isn't already
      tracked under `ao_human_fleet_integration_2026_08_15.md`. (repo: agent-orchestrator) Extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 11 (na-eligibility-audit 2026-08-19, ao tranche, RECLASSIFY per-todo split).

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:4c459f34ca19cf91]: RECLASSIFY (per-todo split) — 2 of 3 remaining todos (pull overage_disabled_reason for the other 21 disabled accounts, investigate /api/agents zero human rows) extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` items 10-11. Doc stays NA for the sole remaining item ([OPERATOR] spread reserve slots 31/32/33 across more than one account instead of triple-booking sub-b).
- **context-scout 2026-08-19**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — sole remaining item ([OPERATOR] P2, spread reserve slots 31/32/33 across more than one account instead of triple-booking sub-b) is a genuine capacity/account-allocation decision, unchanged since the 2026-08-19 verdict.
