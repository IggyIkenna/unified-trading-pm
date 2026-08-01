---
doc_type: plan
title: Sports live availability + source-latency — finalize (na-eligibility-audit reclassification twin)
summary: >-
  Gated closeout for sports_live_availability_and_source_latency_2026_07_24.md, reclassified `assigned_vm: NA ->
  planning` by the na-eligibility-audit sports-tranche run 2026-07-30 (retroactive-reclassification shape, codex
  ao-dispatch-batch-naming-and-conflict-check.md §1(b) — name unchanged, bolt-on finalize twin). The source doc's single
  remaining todo (wire api_football `/odds` in-play as the second live sports-odds source + confirm the live connector
  has actually resumed production polling) became bounded once the operator RULED the quota/tier question 2026-07-28 and
  rotated `odds-api-key` to a 5,000,000-credit/month subscription 2026-07-29 — what remains is deterministic wiring plus
  a stated verification, not a business or design call. This twin verifies that todo against its own "Done when" text
  and checks whether the source doc is then an archival candidate.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/sports_live_availability_and_source_latency_2026_07_24.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.25
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
depends_on: [sports_live_availability_and_source_latency_2026_07_24]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit sports tranche, 2026-07-30 — retroactive reclassification of an already-owned `assigned_vm: NA`
  doc per the skill's Phase 2/3. Conflict-check cleared: no currently-active `assigned_vm: planning` doc in
  `parent_epic: manifest_master` (nor `sports_satellite_ao_dispatch_batch5_2026_07_26.md`, nor
  `sports_consolidated_closeout_2026_07_19.md`) carries an open todo claiming the api_football `/odds` in-play
  second-source wiring or the live-connector resume confirmation.
context_scope:
  [
    /plans/active/sports_live_availability_and_source_latency_2026_07_24.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports live availability + source-latency — finalize

> **Machine-gated on `sports_live_availability_and_source_latency_2026_07_24.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue this plan's todo until the parent's remaining todo is done.

## Why the parent was reclassified (read before acting)

The parent's sole open todo was `BLOCKED-OPERATOR-DECISION` until 2026-07-28, when the operator directly ruled "picked a
paid sports-odds API quota tier — proceed with the resume", and then (2026-07-29) provisioned a new `odds-api-key` on a
5,000,000-credit/month subscription, live-verified by direct curl (HTTP 200, `x-requests-remaining: 5000000`). Both the
decision and the credential are therefore settled facts, not open asks — what the todo still carries is bounded
engineering with an explicit stated "Done when", which is the `/na-eligibility-audit` rubric's RECLASSIFY signature
(bounded, deterministic-outcome work that was correctly NA when filed and is simply no longer gated).

## Todos

- [ ] [DATA] P2. **Verify the parent's remaining todo against its own stated "Done when", then check archival
      eligibility.** Once `sports_live_availability_and_source_latency_2026_07_24.md`'s `[DATA] P2` Live-ODDS
      quota/second-source todo is `[x]`: (1) confirm the api_football `/odds` in-play source is genuinely wired as a
      fallback/supplement (read the call site, do not trust the parent's own evidence line); (2) confirm the live
      sports-odds ingestion has actually resumed in PRODUCTION — a fresh poll cycle succeeding against the live key on
      the running `mtds-live-sports-odds-api-trades` VM, per the parent's own explicit "not just a direct-API-call
      verification" clause; (3) grep the parent doc's remaining `- [ ]` items — if zero remain, it is an archival
      candidate, so run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), not just a checkbox flip. **Done when**:
      both verification legs are recorded with real evidence in this doc's Progress Log, and the parent is either
      archived or its remaining open items are named here.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — §1(b) retroactive-reclassification
  naming/pairing convention this twin follows; §3 the conflict-check protocol that cleared the parent.
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual todo (3) invokes.
- `/codex/02-data/live-data-persistence-and-event-log.md` — live=batch event-log spine the resumed live odds path must
  keep using (same code path as batch; no live-only data_types).

## Progress Log

- **2026-07-30** — Authored by the `/na-eligibility-audit` sports-tranche run as the paired finalize twin for the
  parent's `NA -> planning` reclassification. No work done on the parent's own todo in this pass; this doc exists so the
  reclassified plan has the finalize coverage `plans/active/task_template.md` requires for a `doc_type: plan`.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
