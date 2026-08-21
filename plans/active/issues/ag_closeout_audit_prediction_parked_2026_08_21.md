---
doc_type: issue
title: ag-closeout-audit prediction 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit prediction tranche Phase 1 audit (1 batch, 30 candidate docs). Compact orphan table.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, prediction, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/prediction_consolidated_closeout_2026_07_18.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: predictions_master
assigned_vm: NA
execution_scope: human
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: ["2026-08-21 — /ag-closeout-audit prediction, 1 Phase-1 batch, 30 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit prediction 2026-08-21

30 candidates, 1 batch. Counts: archivable_now 3 · archivable_after_planned_work 1 · orphaned_partial_coverage 1 ·
orphaned_never_touched 6 · exclude_cross_cutting 19 (very high mistag rate — most candidates are genuinely
multi-AG instruments/plan-hygiene docs).

## Orphaned — compact table

| Doc | Taxonomy |
|---|---|
| `data_completion_prediction_2026_07_15.md` | **carried finding, 5+ re-confirmations 2026-07-25→08-19, crosses escalation threshold** — Phase-B CQG-bundle object-layer migration needs a dedicated scoping plan, never authored. Needs operator ruling. |
| `prediction_batch4_deferred_residuals_2026_08_16.md` | 38,020-row manifest `--apply` reclassification — permanent `[OPERATOR]` hard-stop per delete-safety protocol |
| `prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md` | blocked on external Betfair `ACCOUNT_PENDING_PASSWORD_CHANGE` |
| `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md` | 3 items redirect to `cross_ag_live_capture_parity_2026_08_14.md` (not in covering set) |
| `prediction_cross_venue_arb_and_coverage_2026_07_24.md` | tarball-overwrite-race (claimed only by draft batch14) + fixture-pairing design gate |
| `predictions_ml_walk_forward_and_arb_2026_06_20.md` | chained on still-open cross-AG `sports_master:Group E` gate |
| `sports_prediction_mvp_writetime_precompute_2026_07_24.md` | deliberately-unshipped schema-bump (scope-risk STOP) |

## Mechanical hygiene flags

- `batch14`/`batch15` (both `status: draft`) draft concrete extraction todos citing several candidates above
  (tarball race, phase_ab/phase_c/phase_e items) — none of it counts as coverage until promoted to active.

## Big findings

`manifest_hygiene_red_all_2026_08_17.md` (correctly `exclude_cross_cutting`, real owner cross-cutting): carried a
genuine, actively-diagnosed prediction data-correctness bug — POLYMARKET's `prediction_canonical_question_group`
manifest cell DIVERGENT_EMPTY on 43% of days across the entire capture history — root-caused + fixed 2026-08-20
(`instruments-service@a586f34102`, Gamma API pagination-offset ceiling silently dropping already-fetched pages on a
422). Now resolved; flagging only because no `predictions_master`-owned doc ever independently tracked or fixed it.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit prediction Phase-1 sweep (1 batch).
