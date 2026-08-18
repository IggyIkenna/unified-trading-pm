---
doc_type: plan
title: prediction venue e2e wiring batch 1 — finalize
summary: >-
  Gated closeout for prediction_venue_e2e_batch1_2026_08_16.md — machine-held via depends_on + gate_on_depends
  until every todo in that batch is done. Re-verifies evidence, runs the standard 6-step archival ritual on the
  batch plan, and checks whether all 5 AG batches are now closed so venue_e2e_wiring_2026_08_16.md's own
  Definition of done can be flipped.
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, prediction, ao-dispatch, satellite-batch, close-out, finalize]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: [prediction_venue_e2e_batch1_2026_08_16]
gate_on_depends: true
sequential: true
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/prediction_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored
  in the same turn as its batch, 2026-08-16 interactive session.
---

# prediction venue e2e wiring batch 1 — finalize

> **Machine-gated on** [`/plans/active/prediction_venue_e2e_batch1_2026_08_16.md`](/plans/active/prediction_venue_e2e_batch1_2026_08_16.md)
> (`depends_on` + `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`.

## Todos

- [x] ✅ [REVIEW] P1. For every completed todo in `prediction_venue_e2e_batch1_2026_08_16.md`, re-verify its cited
      evidence (commit sha resolves as an ancestor of `origin/live-defi-rollout`, cited report/run actually
      resolves). Done-when: all 5 of that batch's todos have independently re-confirmed evidence. — VERIFIED
      2026-08-18. All 11 cited commit SHAs across the batch's 13 todos independently re-confirmed as ancestors of
      `origin/live-defi-rollout`: `unified-trading-pm@da8caf5f5a`, `market-tick-data-service@6e428204f9`,
      `features-service@c5ad65df10`, `features-service@a14db662b9`, `unified-trading-pm@8bfa440ac1`,
      `strategy-service@890ca8a4ce`, `strategy-service@dc3c0219`, `unified-trading-pm@c20f242a85`,
      `unified-api-contracts@0ea4a852`, `unified-api-contracts@cc807336c1`, `strategy-service@daafe3e29b` (all
      `git merge-base --is-ancestor` OK). Spot-checked 2 of the underlying code claims directly: `PREDICTION_VENUES
      = ("POLYMARKET", "KALSHI")` confirmed live in `features-service/features_service/cross_instrument/engine/
      prediction_ingest.py:13`; `get_books_batch`/`_build_book_snapshot_5_rows` confirmed live in
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py`.
      The 3 non-code todos (stale-WIP triage, execution-adapter re-investigation, hard-rules confirmation) are
      pure-investigation with no SHA to verify — their cited reasoning was read and is internally consistent with
      the rest of the batch's evidence trail.
- [ ] [REVIEW] P1. Once `prediction_venue_e2e_batch1_2026_08_16.md` has zero open todos, run the standard 6-step
      archival ritual on it and this finalize plan. Done-when: both docs are under `plans/archive/`, and
      `regenerate_active_plan_inventory.py` reports zero orphan referrers to either.
- [ ] [REVIEW] P1. Check whether all 5 AG batches (cefi/defi/tradfi/sports/prediction) are now archived. If so,
      verify and flip `venue_e2e_wiring_2026_08_16.md`'s Definition of done section and follow its own stated
      closing action. If not, no action — a sibling finalize will find this true once the last batch closes.
      Done-when: either confirmed still-open siblings (no action) or the parent's Definition of done is verified
      with evidence.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
