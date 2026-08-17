---
doc_type: plan
title:
  Prediction satellite AO batch 7 — the one genuinely new orphan since batch6 (trades/book_snapshot_5 available_at
  consumer check)
summary: >-
  Seventh AO-dispatch batch for prediction, produced by the `/ag-closeout-audit prediction` scheduled run 2026-08-04
  (ag_closeout_auditor, slot 11). Live re-run of `generate_ag_closeout_audit_candidates.py --tranche prediction --json`
  found `total_members=48` (down from 52 on 2026-07-31 — 5 previously-covered docs archived/resolved in the interim),
  `never_cited_count=12` (up from 11 — the 11 prior basenames are unchanged, all still genuinely cross-cutting
  multi-AG-tagged; +1 new). A fresh 12-agent Phase-1 Workflow classified all 12: 11 `exclude_cross_cutting` (matches
  prior rounds' verdict on the same 11 basenames) and exactly 1 `orphaned_never_touched` —
  `archive/2026_08/issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md` (created 2026-08-02, one day after the
  last full audit, so no prior round could have seen it). That doc's own remaining work is a single bounded, AO-eligible
  P3 todo (check whether any real downstream consumer reads `available_at` for `data_type in {trades, book_snapshot_5}`
  on prediction-venue data), conflict-checked clean against all 11 covering docs + the doc's own cross-cutting parent
  plan (which explicitly defers the question here rather than claiming it). `status: draft` — a skill-drafted AO batch
  is never auto-shipped; flipping to `active` to dispatch is an operator decision (CLAUDE.md "Plan destination — ASK
  BEFORE CREATING").
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-7, available_at, downstream-consumer-check]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md,
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_07_31.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-16"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.18
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit prediction scheduled run 2026-08-04 (ag_closeout_auditor, slot 11, dispatch agt-a7e099) — Phase 0
  re-ran `generate_ag_closeout_audit_candidates.py --tranche prediction --json` (48 members, 12 never_cited, +1 new vs
  the 2026-07-31 baseline); Phase 1 classified all 12 never-cited candidates via a Workflow fan-out (12 agents, 0
  errors); Phase 3 conflict-checked the one genuine orphan against all 11 covering docs plus its cross-cutting parent
  plan (mtds_available_at_cross_asset_backfill_2026_07_13.md, which explicitly defers the question to this doc rather
  than claiming it — "the trades/book_snapshot_5 question is tracked separately in the new issue doc, not blocking this
  plan further").
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_08/issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md,
    market-tick-data-service/market_tick_data_service/scripts/_rebuild_prediction_emit.py,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

# Prediction satellite AO batch 7 — trades/book_snapshot_5 `available_at` consumer check

> **Status: active — operator-approved 2026-08-06, dispatching.** This batch was drafted autonomously by the
> `/ag-closeout-audit prediction` scheduled run (2026-08-04). Per CLAUDE.md's "Plan destination — ASK BEFORE CREATING"
> HARD RULE and the ag-closeout-audit skill's autonomous-mode guidance, a skill-drafted AO batch is never auto-shipped:
> flipping `status: draft` → `active` to actually dispatch this todo is an operator decision.

## Why this batch exists

Every prior round (batch1-6, native_ao_extract, the 4 Phase A-E children) has already triaged and either dispatched or
correctly deferred the rest of prediction's corpus — this run's own re-audit confirms the same 11 `never_cited`
candidates from 2026-07-31 are still, unchanged, genuinely cross-cutting multi-AG docs (owned by no single tranche's
batch, correctly excluded — see this run's own `ag_closeout_audit_prediction_parked_2026_08_04.md` for the full per-doc
reasoning). The corpus is well-drained. The ONE new gap is a single doc created 2026-08-02 — one day after the last full
audit ran (2026-07-31) — so no prior round could plausibly have seen it.

## Todos

- [x] ✅ [DATA] P3. **DONE 2026-08-16 (slot-19, data_engineering) — unified-trading-pm@e3ca863b9d** — code-read across
      `market-tick-data-service`
      (write side) + `market-data-processing-service` (candle-compute read side; `features-service`/`strategy-service`/
      `execution-service`/`deployment-api`/UI checked via grep, no hits). **Verdict**: a real, non-test consumer
      exists for Kalshi `trades` only — `market-data-processing-service`'s `PredictionTradesAdapter.
      _get_local_timestamp_column` reads `available_at` as the candle-timestamp source for KALSHI-shaped rows — but it
      reads the RAW captured parquet's own write-time-stamped column (`market-tick-data-service`'s
      `kalshi_adapter.py`, unconditional per-row stamp), not the AVAILABILITY MANIFEST's shard-level
      `available_at`/`available_at_envelope` metadata field this doc's fill-rate audit measured — so the low manifest
      fill-rate does not affect this consumer. No consumer found for Polymarket `trades` or `book_snapshot_5` (either
      venue). **No separately-scoped manifest backfill is needed** for either data_type — practically resolves to
      option (b) of the done-when (no backfill scoped). Full evidence recorded in the source doc's own Progress Log
      (checkbox flipped there too, `status: open` → `resolved`, 0 open todos). Source:
      `archive/2026_08/issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`.

## Deferred

None — every other `never_cited` candidate this run classified `exclude_cross_cutting` (11 docs, all carrying 4-6
`asset_group` markers spanning multiple/all 5 AGs, none exclusively prediction-scoped in content). Full per-doc
reasoning: `ag_closeout_audit_prediction_parked_2026_08_04.md`.

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — Phase 3 dispatch-scope eligibility test + conflict-check
  protocol this batch applied.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 — the shared conflict-check
  protocol.

## Progress Log

- 2026-08-04 (slot 11, ag_closeout_auditor, dispatch agt-a7e099): drafted by the `/ag-closeout-audit prediction`
  scheduled run. Phase 1 = 12-agent Workflow (`wf_242a15b4-6b2`), 0 errors; verdicts: 11 `exclude_cross_cutting`, 1
  `orphaned_never_touched`. Phase 3 conflict-check: grepped all 11 covering docs + the candidate's cross-cutting parent
  plan (`mtds_available_at_cross_asset_backfill_2026_07_13.md`) for overlap on `available_at`/`trades`/`book_snapshot_5`
  — found only unrelated hits (a different downstream-consumer check, about trader-identity/PII fields, in
  `prediction_phase_ab_residuals_2026_07_24.md` and `prediction_consolidated_native_ao_extract_2026_07_25.md`) and the
  parent plan's own explicit hand-off language ("tracked separately... not blocking this plan further") confirming no
  double-claim. Extracted the 1 conflict-clear bounded todo. Left `status: draft` per the autonomous-mode safety rail —
  operator flips to `active` to dispatch.
- **context-scout 2026-08-07**: populated/refreshed context_scope (3 entries) — verified all 3 still resolve and still
  map to the sole open P3 `available_at` consumer-check todo; unchanged.
- **2026-08-17 (plan_reconciler)**: `last_updated` was stale (2026-08-06, 10 days after the sole todo's actual
  2026-08-16 completion) — corrected in frontmatter above. Completion evidence lives in the source doc's own Progress
  Log (`archive/2026_08/issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`, `status:
  resolved`, 0 open todos, banner "🟢 ARCHIVED 2026-08-16").
- **context-scout 2026-08-17**: re-verified context_scope (3 entries), unchanged — still the sole `available_at`
  consumer-check todo's source doc, code target, and manifest-status codex SSOT.
