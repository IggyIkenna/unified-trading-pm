---
doc_type: issue
title: >-
  12 backlog tasks stuck in "durable park" (auto_unpark prerequisite never set) for
  4.5-19 days — found via a live dashboard "443 blocked" investigation, not chased further
summary: >-
  An operator asked why the BACKLOG panel's "443 blocked" annotation (queued - claimable,
  server/dispatch.py::claimable_queued_task_ids, dashboard/src/layout.tsx BacklogSummary)
  barely moved after 96 unanswered blocked-QUESTIONS were cleared in the same session —
  confirmed live that the two numbers are unrelated mechanisms (blocked_queue = unanswered
  operator/worker escalation questions; the backlog panel's "blocked" = task-claim
  eligibility) and the 443/442 figure itself is correct: verified by pulling every queued
  task's explain_blocked_bulk() reason and splitting 375 "eligible on slot(s)... waiting for
  one to go idle" (soft/capacity-wait, matches claimable) vs 442 with a real block (matches
  the dashboard number). Breaking the 442 down: 292 gate_on_depends (66%, by-design plan
  sequencing), 83 prereq-task-not-done (19%, plan-internal chains), 54 other named
  prerequisites (12%), 1 fleet-cooldown (transient) — all expected. The remaining 12 (3%,
  listed below) carry `prerequisite auto_unpark__<task_id> not set (durable park, DB-only)`
  and are aged 4.5-19 days (median ~10) — never investigated further in that session (the
  operator ran /pre-compact before responding to the offer to look closer). This doc exists
  so that offer isn't lost.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao-watchdog, backlog-dispatch, durable-park]
related:
  [
    /cursor-configs/skills/ao-watchdog/SKILL.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-21"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: none
source: >-
  Interactive /ao-watchdog + live backlog-panel investigation, 2026-08-21 (slot 19, this
  session) — operator screenshot of the dashboard's "443 blocked" annotation prompted a
  full trace of the calculation (confirmed correct, no bug), which surfaced this smaller
  durable-park finding as a side effect.
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/dashboard/src/layout.tsx,
  ]
---

# 12 backlog tasks in durable park with no unpark condition set, 4.5-19 days old

## What "durable park" means

`prerequisite auto_unpark__<task_id> not set (durable park, DB-only)` is a `PrerequisiteRow`
keyed `auto_unpark__<task_id>`, checked as a normal FLEET-scope filter by
`explain_blocked_bulk`/`claimable_queued_task_ids` (`agent-orchestrator/server/dispatch.py`).
Something upstream (a worker, a watchdog, a specific park reason) is expected to eventually
flip that prerequisite to `true` — until then the task sits queued but permanently
non-claimable, indistinguishable in the dashboard's aggregate "blocked" count from a normal
`gate_on_depends`/`prereq task` gate. Whether each of these 12 has a legitimate reason still
pending, or the thing that was supposed to auto-unpark it never ran / already ran and forgot
to set the flag, was NOT checked in the session that found this — that's the open work here.

## The 12 tasks (live snapshot, 2026-08-21 ~17:30 UTC)

| task_id | age (days) |
|---|---|
| `sports_satellite_ao_dispatch_batch5_2026_07_26_finalize-62cffa9f8f25` | 19.0 |
| `data_pipeline_check_mdps_features-468d3dca150d` | 15.5 |
| `sports_closeout_track_s2_foldin-8544f8ba3735` | 11.3 |
| `sports_odds_api_scattered_multiyear_gaps-3b44a0a4ec31` | 10.0 |
| `sports_af_completion_pass-649179736927` | 10.0 |
| `tradfi_satellite_ao_dispatch_batch9-29d3d0bec9b3` | 10.0 |
| `pytest_timeout_60s_flaky_under_contention-472dc502ba82` | 10.1 |
| `cefi_hl_aster_vm_resource_downsize-b41d0f36eed5` | 10.0 |
| `tradfi_satellite_ao_dispatch_batch13-ef1f025878eb` | 6.2 |
| `safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content-fbf51073d065` | 5.8 |
| `defi_orphan_bucket_delete_list_includes_canonical_bucket-1a7a039d65b6` | 5.7 |
| `tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16_finalize-ddc61604807d` | 4.5 |

Re-pull live via `GET /api/backlog`, filter `status == "queued"` and
`"durable park" in blocked_reason` — this list will have moved by the time anyone reads it;
treat the table above as a starting point, not current truth.

## Todos

- [ ] [DATA] P3. For each of the 12 above, determine WHY its `auto_unpark__<task_id>`
      prerequisite was never set — read the task's own plan doc / the code path that's
      supposed to set this prerequisite (grep `auto_unpark__` in `agent-orchestrator/server/`
      for the setter side, not just the checker) and classify each: (a) still genuinely
      waiting on its real condition (fine, leave parked), (b) the setter path has a bug and
      never fires, (c) the condition already resolved but nothing flipped the flag (a stuck
      park — needs a manual `PrerequisiteRow` set or the plan's own resolution path
      re-triggered). Report the split, not just "found N durable-park tasks."
- [ ] [SCRIPT] P3. If (b) or (c) above turns out to be the common case rather than the
      exception, consider whether `claimable_queued_task_ids`/the dashboard's "blocked"
      annotation should visually separate "durable park" from ordinary gate/prereq blocking
      — right now a stuck park and a healthy gate_on_depends both just render as "blocked",
      and the dashboard tooltip's own "self-resolving for a capacity-wait" framing doesn't
      obviously cover this durable-park case (it isn't a capacity-wait at all).

## Progress Log

- **2026-08-21 (interactive session, slot 19)**: found as a side effect of tracing the
  BACKLOG panel's "443 blocked" figure end-to-end for an operator who'd conflated it with the
  unrelated `blocked_queue` (unanswered questions) count cleared earlier the same session.
  The 443/442 figure itself was verified correct — this doc is only for the 3% sub-finding
  (12 durable-park tasks) that wasn't investigated further before the session ended.
