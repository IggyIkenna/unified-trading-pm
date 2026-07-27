---
doc_type: issue
title:
  Two CI escalation dispatchers emit wall_types outside the closed WALL_TYPES set — they silently degrade to a Slack
  page with no worker ever spawned
summary:
  ldr-to-main-promote.yml emits wall_type "ldr_main_qg_failure" and sit-debounce-trigger.yml emits "sit_retry_cap" —
  neither is in agent-orchestrator's server/escalation.py WALL_TYPES set, so both fail the escalate-to-orchestrator.yml
  listener's case-statement validation before ever reaching /api/escalate. The notify job still pages Slack as a generic
  hard failure, masking that no AO worker was ever dispatched for these two standing conditions.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [ci, escalation, agent-orchestrator, wall_type, ldr-to-main, sit-debounce]
related: [/codex/04-architecture/ci-alerting.md]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: NA
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
supersedes:
superseded_by:
source:
  Dispatched as one of five parallel audit agents this session investigating "CI failure escalation to AO for all CI
  failures that need agents" (an operator-raised open question, not yet triaged before this session).
---

# CI escalation wall_type mismatch — 2026-07-27

## What I found

Audited whether every CI failure that needs an agent to fix actually escalates into AO's backlog. The core signal
(`quality-gates-v2` failing on a promotion PR or on LDR/main with no PR open) IS uniformly wired fleet-wide: every
repo's `quality-gates-v2.yml` fires an instant `escalate-ldr-qg-failure` job on failure (`wall_type: ldr_qg_failure`),
and `agent-orchestrator/server/ci_reconcile.py` (a 15-minute poll loop) catches the "no promotion PR open" gap.

But `server/escalation.py` validates every incoming escalation against a CLOSED set
(`WALL_TYPES = {merge_conflict, label_mismatch, sit_failure, stuck_promotion_pr, ldr_qg_failure, main_ci_red, plan_health, data_pipeline_failure}`
— `escalation.py:50-62`). Two dispatchers emit values outside this set:

- `unified-trading-pm/.github/workflows/ldr-to-main-promote.yml:331` — `wall_type: "ldr_main_qg_failure"`
- `unified-trading-pm/.github/workflows/sit-debounce-trigger.yml:321` — `wall_type: "sit_retry_cap"`

Both fail the listener's own case-statement validation
(`unified-trading-pm/.github/workflows/escalate-to-orchestrator.yml:138-144`, `exit 1`) before the request ever reaches
`POST /api/escalate`. The workflow's `notify` job still pages `#ci-failures` on this as a generic "hard failure
(auth/DNS/TLS or a bad request)" (lines 287-299) — so a human gets paged, but no AO worker is ever dispatched for either
standing condition. This reads as "wired up" from the Slack side while silently degrading to human-only underneath.

## Why it matters

Both conditions this masks are exactly the kind of thing AO exists to auto-fix: an LDR→main promotion stuck on a QG
failure, and a SIT retry cap being hit. A human seeing a generic "escalation failed (bad request?)" page has no easy way
to tell it's actually "this wall_type was never taught to the listener," so the gap can persist indefinitely without
looking like a gap.

## Todos

- [ ] [BACKEND] P2. **Add `ldr_main_qg_failure` and `sit_retry_cap` to `agent-orchestrator/server/escalation.py`'s
      `WALL_TYPES` set** (with whatever handling/role-routing the other wall_types get — read how `ldr_qg_failure` is
      handled as the closest analog for `ldr_main_qg_failure`, and how `sit_failure` is handled as the closest analog
      for `sit_retry_cap`) AND to `unified-trading-pm/.github/workflows/escalate-to-orchestrator.yml`'s case-statement
      validation (lines ~138-144) in the SAME change — the two must stay in lockstep or this exact bug recurs. Add a
      regression test confirming both wall_types now validate and reach the escalation dispatch path (not just a
      lint-level check that the strings match).
- [ ] [BACKEND] P3. **Audit for a THIRD class of this bug**: grep every `.github/workflows/*.yml` across the fleet for
      `wall_type:` literals, diff against `escalation.py`'s `WALL_TYPES` set, and confirm no other dispatcher emits an
      unrecognized value. If found, fold into the same fix above rather than filing a new doc.

## Codex SSOTs

- `/codex/04-architecture/ci-alerting.md` — escalation wall_type contract, `notify-slack.yml` carrier, dedup/cooldown
  semantics.
