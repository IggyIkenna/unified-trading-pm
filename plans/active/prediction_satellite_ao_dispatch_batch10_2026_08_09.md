---
doc_type: plan
title: Prediction satellite AO batch 10 — 2 unclaimed "batch5 candidate" deferrals from batch4 (operator-ruled fold-in)
summary: >-
  Tenth AO-dispatch batch for prediction. Origin: the `plan_reconciler` daily reconciliation run (agt-c3a27f, slot 13,
  2026-08-09, prediction tranche) found 2 fully-shipped, gate-cleared data items — both explicitly tagged "batch5
  candidate" in `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`'s 2026-08-07 Progress Log — that no
  batch 5-9 ever claimed (batch5 itself predates their 2026-08-07 promotion; batches 6-9 never reference either). Filed
  as a blocked-question (`BLK-0d9d2799`); operator ruled option A same day — "fold both into the next prediction
  satellite batch (batch10, not yet drafted)... avoids the passive risk of C (relying on a future audit to rediscover
  them, which per this doc history has already happened once with a batch that never claimed them)". Conflict-checked
  clean against the corpus (no other active doc claims either item's specific ground). The two items are NOT equally
  AO-dispatchable: Deferral (b) (POLYMARKET re-enum + `book_snapshot_5` backfill) is a genuine bounded `[DATA]` todo,
  gate cleared, re-tagged off `[OPERATOR]` 2026-07-28. Deferral (a) (the combined `_index` manifest canonicalisation
  single-walk) remains a PERMANENT `[OPERATOR]` hard-stop per workspace policy (manifest `--apply` is reserved for human
  execution) — folded in as an `[OPERATOR]` todo per the operator's ruling to include both, not reclassified to
  auto-dispatchable.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, ao-dispatch, close-out, batch-10, manifest-canonicalisation, book_snapshot_5, operator-gated]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/issues/plan_reconciler_findings_prediction_2026_08_09.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `plan_reconciler` daily reconciliation run, prediction tranche, 2026-08-09 (dispatch agt-c3a27f, slot 13). Both items
  trace to `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`'s 2026-08-07 (slot-11) Progress Log entry
  ("P2 re-check DONE"), which re-measured live counts and promoted both from gated `[OPERATOR]` deferrals to ready
  candidates ("filed as batch5 candidate" / "promoted to ready `[DATA]` candidate — batch5 or standalone plan,
  AO-dispatchable, no remaining gates"). Neither was ever picked up. Operator ruling on `BLK-0d9d2799` (2026-08-09, same
  session): fold both into a new batch10 rather than standalone plans (option B) or leaving them for a future audit to
  rediscover (option C).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator.py,
  ]
---

# Prediction satellite AO batch 10 — 2 unclaimed batch5-candidate deferrals

> **Status: active — operator-ruled 2026-08-09 (fold-in, not a fresh skill-drafted candidate).** This batch did not go
> through the usual `/ag-closeout-audit` draft→operator-approve cycle — it was authored directly per an explicit
> operator ruling on a `plan_reconciler` blocked-question (`BLK-0d9d2799`), so `status: active` from creation, same
> shape as any other operator-approved batch.

## Why this batch exists

`prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md` todo 2 (P2, done 2026-08-07) re-checked 2 items that
had been gated `[OPERATOR]` deferrals in batch4 itself, found both gates cleared, re-measured live counts, and
explicitly tagged both "batch5 candidate" in its Progress Log. `prediction_satellite_ao_dispatch_batch5_2026_07_26.md`
was archived before that 2026-08-07 promotion (it predates it), so it structurally could not have absorbed either item —
and no batch since (6, 7, 8, 9) ever cited either. `plan_reconciler`'s 2026-08-09 prediction-tranche pass found both
still unclaimed 2 days later and escalated rather than silently fixing the wrong thing (which one, if any, is truly
AO-eligible as-is is a judgment call — see Todo 1 below).

**Conflict-check** (per `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3): grepped the
corpus for both items' distinctive claims (`combined.*_index.*canonicalisation`, `POLYMARKET re-enum`,
`book_snapshot_5.*backfill`) — the only hits outside `batch4_finalize` itself are unrelated single-walk-discipline
mentions in other AGs' closeout docs and a different instrument_type-casing single-walk in
`prediction_phase_ab_residuals_2026_07_24.md` (a different topic entirely). Zero overlap. Clear to dispatch.

## Todos

- [ ] [OPERATOR] P2. **Deferral (a) — combined prediction `_index` manifest canonicalisation single-walk,
      out-of-lifecycle scope audit.** Legs (b)/(c) of the original 3-part item are ALREADY RESOLVED (0 rows each,
      flipped `[x]` in `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s P2/P3 — see `batch4_finalize`'s
      2026-08-07 entry). **Remaining leg (a) only**: as of 2026-08-07, 38,020 out-of-lifecycle POLYMARKET
      `empty_confirmed` rows + 1,953,482 `SOURCE_RETURNED_ZERO` rows (both growing — "pipeline running since") in
      `market-data-tick-pred-prd-central-element-323112`'s `_index/availability_index.parquet` need a scope audit +
      canonicalisation walk. **This remains a PERMANENT `[OPERATOR]` hard-stop**, per `batch4`'s own 2026-07-28 ruling
      (restated verbatim in `batch4_finalize`'s 2026-08-07 entry: "workspace policy unchanged — manifest `--apply`
      reserved for human execution forever") — this todo does NOT authorize an agent to run `--apply`; it authorizes
      RE-MEASURING the counts live (they are 2+ days stale as of this batch's authoring) and preparing the walk plan for
      human execution. **Done when**: counts are re-measured live via the same column-pruned batched-scan pattern
      batch4_finalize used, the walk plan (which rows, what the canonicalisation target shape is) is written up in this
      todo's Progress Log, and an `[OPERATOR]` handoff is posted for the actual `--apply` run. Repo:
      market-tick-data-service (read + plan only, no write).

- [ ] [DATA] P2. **Deferral (b) — POLYMARKET re-enum + `book_snapshot_5` re-backfill.** Gate cleared 2026-08-07
      (batch4's P0 lifecycle-bounds code, `instruments-service@3617261f`); re-tagged off `[OPERATOR]` 2026-07-28 per
      `batch4_finalize`'s own todo 2(b) — genuinely AO-dispatchable, no remaining gates as of the 2026-08-07 re-check.
      Re-enumerate POLYMARKET prediction markets against the current lifecycle-bounded universe and re-run the
      `book_snapshot_5` backfill for any gap the re-enum surfaces. **Re-verify the "no remaining gates" claim is still
      accurate before executing** — it is 2 days old as of this batch's authoring; re-check
      `prediction_live_clob_depth_capture_2026_07_24.md`'s depth-history retention section (its own related, more recent
      findings) for anything that changes this item's scope. **Done when**: the re-enum + backfill completes with a
      captured row count, `prediction_live_clob_depth_capture_2026_07_24.md`'s relevant open item (if any exists there)
      is cross-checked/updated, and this todo cites the resolving `<repo>@<sha>` + row-count evidence. Repo:
      market-tick-data-service.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the conflict-check protocol this
  batch applied before drafting.
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest schema + `record_captured`/`empty_confirmed`
  semantics both todos reference.
- `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` (2026-07-28 entry) — the originating ruling for Deferral (a)'s
  permanent-`[OPERATOR]` status; not itself a codex doc, cited here since no codex SSOT states this specific rule more
  precisely than the plan doc that established it.

## Progress Log

- 2026-08-09 (slot 13, plan_reconciler, dispatch agt-c3a27f): drafted per operator ruling on `BLK-0d9d2799` (see
  Source). Conflict-check clean (see "Why this batch exists"). `status: active` from creation per the operator's direct
  ruling (no separate draft→approve cycle needed — the ruling IS the approval). Paired finalize sibling:
  `prediction_satellite_ao_dispatch_batch10_2026_08_09_finalize.md`.
