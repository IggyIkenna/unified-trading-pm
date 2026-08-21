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

- [x] [DATA] P3. For each of the 12 above, determine WHY its `auto_unpark__<task_id>`
      prerequisite was never set — read the task's own plan doc / the code path that's
      supposed to set this prerequisite (grep `auto_unpark__` in `agent-orchestrator/server/`
      for the setter side, not just the checker) and classify each: (a) still genuinely
      waiting on its real condition (fine, leave parked), (b) the setter path has a bug and
      never fires, (c) the condition already resolved but nothing flipped the flag (a stuck
      park — needs a manual `PrerequisiteRow` set or the plan's own resolution path
      re-triggered). Report the split, not just "found N durable-park tasks." — **DONE
      2026-08-21, verdict: (b) does not apply to any of the 12 — there is no auto-clearing
      "setter" for any of them to be buggy.** Read `server/auto_park.py`'s own docstring in
      full: unparking is deliberately NOT "detect the original blocker resolved" — the ONLY
      trigger is an explicit `POST /api/prerequisites/{condition} {"value": true}` call by an
      operator or a purpose-built script; `AutoParkReconciler` (`auto_park_reconcile.py`) only
      notices a condition someone ELSE already flipped and does the mechanical backlog.yaml
      cleanup. So every one of the 12 is genuinely (a) "still waiting for someone/something to
      look and decide" — none had a broken auto-clear to fix, because none was ever supposed to
      auto-clear. Per-task detail, cross-checked live against `/api/backlog/parked` (48
      non-orphan rows fleet-wide) + `data/config/backlog.yaml`:
      - `sports_odds_api_scattered_multiyear_gaps-3b44a0a4ec31`: odds-capture is explicitly still
        gated on a pending API-key decision (chat-only context this session, no citable doc yet)
        — correctly still parked, no action.
      - `defi_orphan_bucket_delete_list_includes_canonical_bucket-1a7a039d65b6` and
        `tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16_finalize-ddc61604807d`: the API's
        own `likely_needs_human_action` field already flags BOTH `true` — bucket-delete tasks,
        correctly gated pending an operator per the delete-safety HARD RULE; no bug, no action
        beyond what's already tracked.
      - `pytest_timeout_60s_flaky_under_contention-472dc502ba82`: this task's OWN purpose is a
        "post-fix monitoring window" — i.e. it's designed to sit parked until an observation
        period elapses, then someone checks back and clears it. 10.1 days in, that window has
        almost certainly elapsed — this is the one candidate worth an operator actually looking
        at (not a bug, just overdue for the human step the design always required).
      - `sports_satellite_ao_dispatch_batch5_2026_07_26_finalize-62cffa9f8f25` (19.0d, oldest)
        and `data_pipeline_check_mdps_features-468d3dca150d` (15.5d): both are "finalize"/gated
        rollup tasks — genuinely still waiting on upstream chain items, consistent with their
        plan structure.
      - `sports_closeout_track_s2_foldin-8544f8ba3735`: carries a SECOND, ordinary blocker too
        (`prereq task sports_closeout_track_s2_foldin-0ff8aa2eb9ef not done`) — the durable-park
        layer is redundant with a real still-open dependency; not stuck, just double-gated.
      - Remaining 5 (`sports_af_completion_pass`, `tradfi_satellite_ao_dispatch_batch9`,
        `cefi_hl_aster_vm_resource_downsize`, `tradfi_satellite_ao_dispatch_batch13`,
        `safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content`): no evidence either
        way of resolution — genuinely open findings/plans, correctly left parked pending review.

      **Side-finding, confirmed not a new bug**: 10 of the 12 show `priority_override: false`
      live in `backlog.yaml` despite still being blocked by their (intact) SQLite
      `auto_unpark__` condition — `auto_park.py`'s own docstring documents this exact drift as
      an accepted LIMITATION ("priority_override is stored ONLY in backlog.yaml... a bug resets
      it... the prereq still blocks dispatch" — the "suspenders" holding even when the "belt"
      slips). Cosmetic only (affects queue-position display, not dispatch eligibility) — no
      todo raised for it, it's already the documented, accepted design.

      **Separate observation, not yet actioned**: 3 of the 12
      (`sports_satellite_ao_dispatch_batch5_2026_07_26_finalize`,
      `data_pipeline_check_mdps_features`, `sports_closeout_track_s2_foldin`) have NO row at
      all in `/api/backlog/parked` (no cooldown row, `ss_cooldown.parked_rows` never sees them)
      even though their SQLite `auto_unpark__` condition is set and blocking — meaning
      `AutoParkReconciler`'s scan set is incomplete for these 3 specifically (its scan is
      cooldown-row-keyed, not condition-keyed). Functionally harmless today (nothing has tried
      to clear their condition anyway), but if an operator ever DOES flip the condition true for
      one of these 3 via the API, the reconciler's periodic scan won't notice — the backlog.yaml
      cleanup (removing the stale prereq + restoring `priority_override`) would need a manual
      `unpark_task` call or an on-demand reconcile pass, not the automatic one. Not filing a
      separate issue for this — it's a narrow edge case with no live impact, noted here for
      whoever next touches `auto_park_reconcile.py`.
- [ ] [SCRIPT] P3. If (b) or (c) above turns out to be the common case rather than the
      exception, consider whether `claimable_queued_task_ids`/the dashboard's "blocked"
      annotation should visually separate "durable park" from ordinary gate/prereq blocking
      — right now a stuck park and a healthy gate_on_depends both just render as "blocked",
      and the dashboard tooltip's own "self-resolving for a capacity-wait" framing doesn't
      obviously cover this durable-park case (it isn't a capacity-wait at all). **Still open
      2026-08-21** — the per-task classification above found (b)/(c) do NOT apply (every park
      is a legitimate, by-design "waiting on a human/script to look" state, not a broken
      auto-clear), so the original trigger for this todo didn't materialize. Worth doing anyway
      though: `GET /api/backlog/parked` already computes a `likely_needs_human_action` boolean
      per row (confirmed live, correctly flagging both bucket-delete tasks above) — the
      dashboard's "blocked" sub-count could reuse that existing field to split "durable park,
      needs a human" from ordinary gate/prereq blocking with NO new backend logic, just a UI
      change consuming a field that already exists. Left open as a genuine but small UI todo,
      not mine to implement unasked.

## Progress Log

- **2026-08-21 (interactive session, slot 19)**: found as a side effect of tracing the
  BACKLOG panel's "443 blocked" figure end-to-end for an operator who'd conflated it with the
  unrelated `blocked_queue` (unanswered questions) count cleared earlier the same session.
  The 443/442 figure itself was verified correct — this doc is only for the 3% sub-finding
  (12 durable-park tasks) that wasn't investigated further before the session ended.
- **2026-08-21 (same session, continued post-`/compact`)**: closed todo 1 — read
  `auto_park.py`/`auto_park_reconcile.py` in full, then cross-checked all 12 tasks live against
  `GET /api/backlog/parked` (74 total cooldown rows fleet-wide, 26 orphaned/stale, 48 still
  tracking a real backlog task) and the actual `data/config/backlog.yaml` on the orchestrator's
  own cwd (`agent-orchestrator/` root checkout, NOT the `harsh_orchestrator/backlog.yaml` file
  found first — that one is a stale/unrelated 263-line file, a dead end worth remembering).
  Verdict: no bug causing the stuck state — durable park requires an explicit external clear by
  design, and nothing has done that for any of the 12 yet. One task
  (`pytest_timeout_60s_flaky_under_contention`) is genuinely overdue for that human look since
  its own monitoring-window purpose has likely elapsed; the rest are legitimately still open.
  Two side-findings recorded (priority_override drift — confirmed harmless/already-documented;
  3-of-12 missing cooldown rows — narrow edge case, not worth its own issue doc).
