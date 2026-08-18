---
doc_type: plan
title: prediction venue e2e wiring batch 1 — finalize
summary: >-
  Gated closeout for prediction_venue_e2e_batch1_2026_08_16.md — machine-held via depends_on + gate_on_depends
  until every todo in that batch is done. Re-verifies evidence, runs the standard 6-step archival ritual on the
  batch plan, and checks whether all 5 AG batches are now closed so venue_e2e_wiring_2026_08_16.md's own
  Definition of done can be flipped.
status: complete
nature: process
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, prediction, ao-dispatch, satellite-batch, close-out, finalize]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/prediction_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-18"
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
    /plans/archive/2026_08/prediction_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored
  in the same turn as its batch, 2026-08-16 interactive session.
---

# prediction venue e2e wiring batch 1 — finalize

> **Was machine-gated on** [`/plans/archive/2026_08/prediction_venue_e2e_batch1_2026_08_16.md`](/plans/archive/2026_08/prediction_venue_e2e_batch1_2026_08_16.md)
> (`depends_on` + `gate_on_depends: true`) — both docs are now archived; the gate is historical.

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
- [x] ✅ [REVIEW] P1. **DONE 2026-08-18 (slot-3).** Ran the 6-step archival ritual on
      `prediction_venue_e2e_batch1_2026_08_16.md` (13/13 todos `[x]`, unlocked, no prose-only deferrals found).
      `status: complete`, `git mv` to `plans/archive/2026_08/prediction_venue_e2e_batch1_2026_08_16.md`. Referrer
      sweep: `venue_e2e_wiring_2026_08_16.md` (the one path-shaped markdown link) repointed to the archive path
      with an "archived — done" note, mirroring the defi/cefi/tradfi siblings' precedent; its
      `depends_on: [prediction_venue_e2e_batch1_2026_08_16]` bare-slug entry left unchanged (machine-parsed, out
      of scope per the archival SSOT). Remaining mentions in
      `plans/active/issues/plan_reconciler_findings_prediction_2026_08_{16,17}.md` and
      `plans/active/issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md` are bare backtick prose (not
      path-shaped links) — left as-is, same scope the defi/tradfi precedents used. `plans/active/INDEX.md` is
      auto-generated — regenerated via `scripts/plans/regenerate_active_plan_inventory.py` rather than
      hand-edited. No codex contract change — this batch's code fixes (KALSHI feature-ingest/book-collector/
      position-adapter/transfer-rail gaps, POLYMARKET archetype wiring) are already covered by their own tests;
      nothing new to establish as an SSOT rule. This finalize doc archives together with the batch plan in the
      same commit (single-repo/mode-1 combined flip+archival, sanctioned per
      `plan-completion-and-archival-discipline.md` § "No-double-gate" 2026-08-10 narrowing).
- [x] ✅ [REVIEW] P1. **DONE 2026-08-18 (slot-3).** Checked all 5 AG batches: `defi_venue_e2e_batch1_2026_08_16`,
      `cefi_venue_e2e_batch1_2026_08_16`, `tradfi_venue_e2e_batch1_2026_08_16` already archived (2026-08-17);
      `prediction_venue_e2e_batch1_2026_08_16` archiving now (this finalize);
      `sports_venue_e2e_batch1_2026_08_16` still has 1 open todo (confirmed live grep,
      `plans/active/sports_venue_e2e_batch1_2026_08_16.md`). **4/5 archived, 1 still open — not all 5 — no
      action** on `venue_e2e_wiring_2026_08_16.md`'s Definition of done section; its own gated sports finalize
      (`sports_venue_e2e_batch1_2026_08_16_finalize.md`) will find the all-5-done condition true once sports
      closes.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).

**2026-08-18 — all todos done, archiving now (slot 3, review).** Independently re-verified all 11 cited SHAs
across the batch (todo 1, done 2026-08-18 per the batch's own Progress Log). Ran the 6-step archival ritual:
no prose-only deferrals to migrate, 1 real referrer repointed (`venue_e2e_wiring_2026_08_16.md`), 3 bare-prose
mentions left as historical citations, `INDEX.md` regenerated via script not hand-edited, no codex contract
change needed. Confirmed 4/5 AG batches archived, sports still open — `venue_e2e_wiring_2026_08_16.md`'s
Definition of done stays untouched, its gated sports finalize will close that loop. This doc archives in the
same commit as the batch plan (single-repo mode-1, sanctioned combined flip+archival).
