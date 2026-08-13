---
doc_type: issue
title:
  a partial-disposition blocked-answer that recommends a mechanical backlog action (e.g. "park the task") has no
  automatic follow-through — nothing applies the action, it silently relies on someone remembering
summary: >-
  When the main agent answers a blocked-queue question with a disposition that implies a mechanical backlog mutation
  (most commonly "park this task"), the answer records the DISPOSITION only — no component then applies it. Main cannot
  hand-edit `data/config/backlog.yaml` (HARD RULE — backlog is plan-derived), and there is no main-agent park API
  endpoint (only `/api/backlog/{id}/unpark`, `/park/redispatch`, and `/api/prerequisites/{name}`, none of which can
  create a park). So a genuine park has exactly two real paths: an explicit operator step (RULES.md §4 hand-edit +
  `/api/backlog/reload`) or the backend `auto_park` trigger (server/auto_park.py — fires only after ≥3 GATED/BLOCKED/
  PARKED *declines* in-window). Neither fires from a main "park it" answer alone. Observed live on BLK-05853f23
  (`defi_venue_pipeline_to_live_ao_build-006`): main's earlier "A — park it" lean was recorded but never applied, and
  the task kept being re-offered at normal priority (review msg 2978). It did no harm THIS time (the correct resolution
  turned out to be "don't park — the verify check was a squash-ancestry false-negative and the fix was already on main",
  see `/plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md`), but the follow-through gap is real
  and today depends on a human/agent remembering rather than a mechanism. Not urgent: `auto_park` is a genuine backstop
  once a task actually starts getting DECLINED as GATED (as it did for
  `cefi_track2_backfill_vm_preempted_no_recovery-003`), but a task that keeps getting ACCEPTED-and-worked (not declined)
  never trips it.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, blocked-queue, dispatch, auto-park, backlog, follow-through-gap]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
  ]
created: 2026-07-31
author: unknown
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
drift_direction: advance-code
depends_on: []
source:
  [
    "Flagged 2026-07-31 13:52Z by the review role (msg 2980) to main-agent (agt-9f21bc) after main investigated
    BLK-05853f23 and found its earlier partial 'park it' disposition had never been mechanically applied — every-
    follow-up-is-a-todo, tracked here rather than left as chat prose.",
  ]
resolved_by:
  "Option (a) shipped — agent-orchestrator@5bfde668: POST /api/backlog/{task_id}/park (server/auto_park.py::manual_park)
  applies the RULES.md §4 recipe on an explicit request. Not yet live-verified end-to-end on a real dispatched task
  (this session had no path to the live orchestrator VM — see the doc's own note below); verified via unit + endpoint
  tests instead."
locked_by: # CORRECTED 2026-08-12 (/plan-reconcile): cleared — locked_since predated created (2026-07-31) by ~2 months
locked_since: # (impossible), and locked_by held a branch name, not an owner; same corpus-wide placeholder-lock bug
# flagged elsewhere in this findings doc. Doc status is already `resolved`, so no live lock should remain anyway.
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    agent-orchestrator/server/auto_park.py,
  ]
---

> **🗄️ ARCHIVED 2026-08-12 (/plan-reconcile)** — `status: resolved`, all todos done, `locked_by` cleared (was a
> corpus-wide placeholder bug artifact — locked_since predated created by 2 months, impossible; cleared this run).

# AO: partial-disposition "park it" blocked-answers have no automatic follow-through

## Todos

- [x] ✅ [BACKEND] P3. Close the disposition→action follow-through gap for blocked-answers that recommend a mechanical
      backlog action. Today a main-agent "park the task" answer records disposition only and nothing applies it (main
      cannot hand-edit `backlog.yaml`; there is no main park API; `auto_park` fires only on ≥3 GATED/BLOCKED/PARKED
      _declines_, not on an accepted-and-worked task). Pick one: (a) an authenticated `POST /api/backlog/{id}/park`
      endpoint that applies the RULES.md §4 recipe programmatically (priority=999 + `priority_override` + a named
      initially-false prereq) + reload — the same mutation `server/auto_park.py` already performs, just operator/main-
      triggerable instead of decline-triggered; and/or (b) when a blocked-answer carries an explicit park disposition,
      have the backend either apply (a) or surface an unmistakable operator action-item (not just recorded text).
      Whatever the choice, a park disposition must not depend on someone remembering to hand-apply it. Done-when: a main
      "park it" blocked-answer deterministically results in the task being parked (or an explicit operator step being
      raised), verified end-to-end on one real task. — agent-orchestrator@5bfde668. Shipped option (a):
      `POST /api/backlog/{task_id}/park` (`server/auto_park.py::manual_park`) applies the identical condition-naming +
      priority=999/`priority_override`/false-prereq mutation `_park_task`'s auto-threshold escalation already performs,
      so `unpark_task`/`AutoParkReconciler`/the dashboard's existing "Dispatch now"/"Mark done" work unchanged
      regardless of a park's origin. 404 if the task isn't in `backlog.yaml`, 409 if already parked. Deliberately does
      not page Slack (a manual park is a deliberate response, not an anomaly signal — the "automatic lifecycle events
      never page" convention). Option (b) (auto-detect a park disposition from a blocked-answer's free text and invoke
      (a) automatically) is NOT built — no structured "this answer means park" field exists on `AnswerRequest` today,
      and inferring intent from prose was judged too fragile to add speculatively; (a) alone satisfies this todo's own
      "Pick one: (a) ... and/or (b)" framing. Tests: `tests/test_auto_park.py` (6 new `manual_park` unit tests — recipe
      application, idempotency, unknown-task, no-Slack-page, shared unpark path) + `tests/test_parked_tasks_routes.py`
      (`TestParkTask`, 5 new endpoint tests incl. 404/409). Full `quality-gates.sh` green (2248 backend + 168 vitest
      passed, ruff/basedpyright/tsc clean). **Not live-verified end-to-end**: this session had no path to the live
      orchestrator VM (SSM reaches it read-only by convention; see the sibling PM issue this session also filed,
      `ao_operator_gated_canned_options_bc_still_no_op_2026_08_03.md`, for why) — whoever next uses this endpoint for a
      real park should confirm it end-to-end against the live server per this todo's original done-when.

## Progress Log

- **2026-08-03**: shipped `POST /api/backlog/{task_id}/park` per the todo above (agent-orchestrator@5bfde668), prompted
  by the operator flagging confusing/non-working operator-gated answer options in a separate audit this same session.
  Endpoint + unit tests written and QG-verified; live end-to-end verification against the real orchestrator VM is left
  to whoever next exercises a real park, since this session couldn't reach it (see resolved_by above).

- 2026-07-31 (slot-9, data_engineering): second confirming occurrence, different task —
  `defi_satellite_ao_dispatch_batch3-015` (the `funding_oi`/`returns` D1 DeFi features todo in
  `plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md`). The plan's own text records main ruled
  (~2026-07-31 12:58Z, in response to slot-16's `/blocked`) to PARK this todo via the backlog.yaml recipe (priority:
  999 + a false prerequisite gated on both linked issue docs) — yet my dispatch at 15:11:08Z (`task_dispatched`
  activity, `dispatch_reason: "tier=1 priority=20 plan_order=0"`) shows the task still at its plan-derived
  `priority: 20`, not 999. This is the 11th+ consecutive dispatch of this exact todo today (slots
  2,3,4,5,6,8,10,11,14,16, now 9) since the ruling — same root cause this doc already describes (a main "park it"
  disposition records intent only, nothing mechanically applies it). No new action taken beyond this evidence note;
  skipped the task per the established precedent (don't re-ask the already-answered question, don't force the compute
  step past its real infra blocker).

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-08-01; only change since = a referrer repoint to
  /plans/archive/2026_08/; `locked_by: live-defi-rollout` unchanged, single todo is still a 2-way (a)/(b) backend design
  choice): KEEP-NA, valid -- Full audit rationale: The single open todo asks the worker to 'Pick one: (a) ... and/or (b)
  ...' between two design approaches for closing a disposition-to-action follow-through gap in agent-orchestrator's core
  dispatch/backlog mechanism (adding a POST /api/backlog/{id}/park endpoint, and/or a backend-surfaced operator a...
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch / blocked-queue /
  backlog-derivation model this gap sits inside.
- `/codex/04-architecture/agent-orchestrator-overview.md` — AO runtime overview.
