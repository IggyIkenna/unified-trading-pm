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
  see `/plans/active/defi_venue_pipeline_to_live_ao_build_2026_07_30.md`), but the follow-through gap is real and today
  depends on a human/agent remembering rather than a mechanism. Not urgent: `auto_park` is a genuine backstop once a
  task actually starts getting DECLINED as GATED (as it did for `cefi_track2_backfill_vm_preempted_no_recovery-003`),
  but a task that keeps getting ACCEPTED-and-worked (not declined) never trips it.
status: open
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
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# AO: partial-disposition "park it" blocked-answers have no automatic follow-through

## Todos

- [ ] [BACKEND] P3. Close the disposition→action follow-through gap for blocked-answers that recommend a mechanical
      backlog action. Today a main-agent "park the task" answer records disposition only and nothing applies it (main
      cannot hand-edit `backlog.yaml`; there is no main park API; `auto_park` fires only on ≥3 GATED/BLOCKED/PARKED
      _declines_, not on an accepted-and-worked task). Pick one: (a) an authenticated `POST /api/backlog/{id}/park`
      endpoint that applies the RULES.md §4 recipe programmatically (priority=999 + `priority_override` + a named
      initially-false prereq) + reload — the same mutation `server/auto_park.py` already performs, just operator/main-
      triggerable instead of decline-triggered; and/or (b) when a blocked-answer carries an explicit park disposition,
      have the backend either apply (a) or surface an unmistakable operator action-item (not just recorded text).
      Whatever the choice, a park disposition must not depend on someone remembering to hand-apply it. Done-when: a main
      "park it" blocked-answer deterministically results in the task being parked (or an explicit operator step being
      raised), verified end-to-end on one real task.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch / blocked-queue /
  backlog-derivation model this gap sits inside.
- `/codex/04-architecture/agent-orchestrator-overview.md` — AO runtime overview.
