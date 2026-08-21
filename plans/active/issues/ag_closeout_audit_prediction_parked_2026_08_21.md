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
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/prediction_consolidated_closeout_2026_07_18.md, /plans/active/prediction_satellite_ao_dispatch_batch16_2026_08_21.md]
created: 2026-08-21
last_updated: 2026-08-21 # ag-closeout-audit Phase 2/3 sweep — orphan table re-verified, 1 item extracted to batch16
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
| `data_completion_prediction_2026_07_15.md` | **re-verified 2026-08-21 (Phase 3), still true — carried finding, now 6+ re-confirmations 2026-07-25→08-21, crosses escalation threshold** — Phase-B CQG-bundle object-layer migration needs a dedicated scoping plan, never authored. Operator-gated / too-large-for-a-batch-todo; NOT extracted. Needs an actual operator ruling or a dedicated scoping plan authored directly (not another re-triage). |
| `prediction_batch4_deferred_residuals_2026_08_16.md` | **re-verified 2026-08-21, still true** — 38,020-row manifest `--apply` reclassification — permanent `[OPERATOR]` hard-stop per delete-safety protocol. Correctly excluded, no action. |
| `prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md` | **re-verified 2026-08-21, still true** — blocked on external Betfair `ACCOUNT_PENDING_PASSWORD_CHANGE` (last live-checked 2026-08-12, no update since); already tracked/retagged `[BLOCKED-CREDENTIALS][INFRA]` in `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`. Genuinely credential-gated, correctly excluded. |
| `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md` | **➡️ EXTRACTED 2026-08-21** → `plans/active/prediction_satellite_ao_dispatch_batch16_2026_08_21.md`. Re-verified the "3 items redirect to `cross_ag_live_capture_parity_2026_08_14.md`" framing was a stalemate, not real coverage — that redirect target is itself `assigned_vm: NA`/`execution_scope: local-only`, so nobody was actually dispatched. All 3 open todos (cache-refresh wiring, Polymarket catalog-writer root-cause, zero-ever-captured diagnosis) are bounded with clear DoDs; extracted verbatim into a new draft satellite batch. |
| `prediction_cross_venue_arb_and_coverage_2026_07_24.md` | **re-verified 2026-08-21**: tarball-overwrite-race item is already drafted (not re-extracted, avoiding a duplicate) in `prediction_satellite_ao_dispatch_batch14_2026_08_19.md` (still `status: draft`, awaiting operator promotion) + the fixture-pairing item remains a genuine `[DESIGN]` gate. Still orphaned in the strict "no ACTIVE coverage" sense purely because batch14 hasn't been promoted yet — not a fresh finding, no new action taken here. |
| `predictions_ml_walk_forward_and_arb_2026_06_20.md` | **re-verified 2026-08-21, still true** — chained on still-open cross-AG `sports_master:Group E` gate (`plans/epics/sports_master.md` line 649, confirmed still `[ ]` unchecked live today). Genuinely blocked, correctly excluded. |
| `sports_prediction_mvp_writetime_precompute_2026_07_24.md` | **re-verified 2026-08-21, still true** — deliberately-unshipped schema-bump (`MANIFEST_SCHEMA_VERSION` 9→10 on UTL's shared `AvailabilityRecord`, fleet-wide-redeploy scope-risk STOP). Genuinely design-needed, correctly excluded. |

## Mechanical hygiene flags

- `batch14`/`batch15` (both `status: draft`) draft concrete extraction todos citing several candidates above
  (tarball race, phase_ab/phase_c/phase_e items) — none of it counts as coverage until promoted to active.
  **Re-verified 2026-08-21 (Phase 2 sweep): still accurate, both remain `status: draft`, nothing to mechanically fix
  here** — this flag is informational (no stale tag/citation/checkbox-format issue to apply a direct fix to). Same
  status now also applies to `batch16` (new, `status: draft`, see the Orphaned table row above).

## Big findings

`manifest_hygiene_red_all_2026_08_17.md` (correctly `exclude_cross_cutting`, real owner cross-cutting): carried a
genuine, actively-diagnosed prediction data-correctness bug — POLYMARKET's `prediction_canonical_question_group`
manifest cell DIVERGENT_EMPTY on 43% of days across the entire capture history — root-caused + fixed 2026-08-20
(`instruments-service@a586f34102`, Gamma API pagination-offset ceiling silently dropping already-fetched pages on a
422). Now resolved; flagging only because no `predictions_master`-owned doc ever independently tracked or fixed it.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit prediction Phase-1 sweep (1 batch).
- **ag-closeout-audit 2026-08-21 (prediction tranche, Phase 2/3 sweep)**: Phase 2 — re-verified the single Mechanical
  hygiene flag; still accurate, nothing to mechanically fix (informational, not a stale-tag/citation/checkbox
  issue). Phase 3 — re-classified all 7 orphan-table rows against the current live docs (not just this doc's own
  one-line summaries): 6 re-confirmed correctly excluded (operator-gated ×2, credential-gated ×1, already-drafted-
  elsewhere ×1, cross-AG-gated ×1, design-needed ×1); 1 (`prediction_live_instrument_cache_never_refreshed_and_
  polymarket_catalog_gap_2026_08_14.md`) was a mutual-redirect stalemate between two NA docs with no actual
  dispatched owner — extracted its 3 bounded todos into
  `/plans/active/prediction_satellite_ao_dispatch_batch16_2026_08_21.md` (`status: draft`). Source doc annotated with
  an `➡️ EXTRACTED` banner, not deleted. `data_completion_prediction_2026_07_15.md`'s CQG-migration finding is now a
  6th consecutive re-confirmation across 2026-07-25→08-21 — flagging prominently per the carried-finding escalation
  rule: this needs an operator ruling or a dedicated scoping plan authored directly, not another audit re-triage.
