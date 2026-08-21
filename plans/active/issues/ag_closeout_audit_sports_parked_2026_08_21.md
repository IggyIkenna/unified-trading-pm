---
doc_type: issue
title: ag-closeout-audit sports 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit sports tranche Phase 1 audit (3 batches, 82 candidate docs). Compact orphan table.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, sports, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: sports_master
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
source: ["2026-08-21 — /ag-closeout-audit sports, 3 Phase-1 batches, 82 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit sports 2026-08-21

82 candidates, 3 batches. Counts: archivable_now 5 · archivable_after_planned_work 27 (dominant pattern — most
sports issue docs are self-dispatched with real self-tracked progress) · orphaned_partial_coverage 7 ·
orphaned_never_touched 24 · exclude_cross_cutting 17.

**Recurring gap**: `sports_satellite_ao_dispatch_batch14_2026_08_16.md` is `status: draft` and cited as "already
covers this" by 5+ candidates below — none of that citation counts as real coverage until promoted to active.

## Orphaned — compact table

| Doc | Taxonomy |
|---|---|
| `mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md` (15 items) | Track: LOCAL/human by design |
| `sports_live_arb_strategy_and_execution_routing_2026_08_14.md` (14 items) | Track: LOCAL/human by design |
| `sports_features_calculator_correctness_audit_2026_08_12.md` (~13 items, draft) | future human/local plan |
| `sportradar_credential_ask_2026_08_09.md` | scope + $499/mo credential decision |
| `sports_bookmaker_roster_classification_2026_08_21.md` | 2 OPERATOR rulings + 2 backend contradiction fixes (fresh, same-day) |
| `sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md` | claimed only by draft batch14 |
| `sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md` | deferred to a dedicated maintenance window |
| `sports_cf8_out_of_window_mechanism_reconciliation_2026_08_16.md` | sole item cannot auto-resolve |
| `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` | 2,436 T-0 shard reconciliation, parked 3+ passes, escalation-worthy per plan_reconciler 2026-08-19 |
| `sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md` | claimed only by draft batch14 |
| `sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md` | claimed only by draft batch14 |
| `sports_league_id_namespace_migration_2026_07_20.md` (P0) | human-gated STEP 9 delete + instruments-service per-fixture bug |
| `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` + `live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md` | **near-duplicate pair**, same VM/root-cause, never cross-referenced — consolidate |
| `sports_venue_smoke_checker_scope_and_canonical_gap_2026_08_20.md` | 2 P1 reconciliation items |
| `sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md` | new 606-object post-delete residual, bounded, batch candidate |
| `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` | Phase 3 OPERATOR GCS delete, correctly gated |
| `predictions_ml_walk_forward_and_arb_2026_06_20.md` | real owner is `prediction` tranche |

## Mechanical hygiene flags

- `sports_satellite_ao_dispatch_batch14_2026_08_16.md` — draft, cited as live coverage by 5+ na-eligibility-audit
  passes for docs it doesn't actually cover yet. Either activate it or revisit those "KEEP-NA-STALE" verdicts.
- `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` /
  `live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md`: both describe the identical incident
  (VM `mtds-live-sports-odds-api-odds-20260816-145019`, connector missing `upstream_failure_reason()`, exhausted
  odds-api-key, fabricated `SOURCE_RETURNED_ZERO`) — filed hours apart, no cross-reference either direction.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit sports Phase-1 sweep (3 batches).
