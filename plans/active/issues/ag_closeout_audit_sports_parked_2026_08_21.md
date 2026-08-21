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

**Re-verified 2026-08-21 (sub-agent Phase 2/3 sweep)** — every row below re-read directly (not trusted from the
original one-line summary). Disposition column added; taxonomy column preserved verbatim for provenance.

| Doc | Taxonomy | 2026-08-21 disposition |
|---|---|---|
| `mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md` (15 items) | Track: LOCAL/human by design | Re-verified: `assigned_vm: NA`, `execution_scope: local-only`, `status: active`, confirmed correct — still orphaned, same reason. |
| `sports_live_arb_strategy_and_execution_routing_2026_08_14.md` (14 items) | Track: LOCAL/human by design | Re-verified: `assigned_vm: NA`, `execution_scope: local-only`, `status: active`, confirmed correct — still orphaned, same reason. |
| `sports_features_calculator_correctness_audit_2026_08_12.md` (~13 items, draft) | future human/local plan | Re-verified: `assigned_vm: NA`, `execution_scope: local-only`, `status: draft`, confirmed correct — still orphaned, same reason. |
| `sportradar_credential_ask_2026_08_09.md` | scope + $499/mo credential decision | Re-verified — genuine spend decision, operator-gated. Still orphaned, same reason. |
| `sports_bookmaker_roster_classification_2026_08_21.md` | 2 OPERATOR rulings + 2 backend contradiction fixes (fresh, same-day) | **BIG FINDING (transient, since resolved).** This file was found mid-session with an unresolved git stash-pop conflict marker triad embedded directly in its `## Todos` section, interleaving two divergent operator-ruling narratives (one citing `unified-api-contracts@710db834`, the other an unshipped `‹PENDING-SHA›` placeholder). Root-caused: the marked-`Updated upstream` side matched `origin/live-defi-rollout`'s real landed commit (`93e04da86f`) exactly; the other side was stale, never-committed local WIP. Restored to origin's verified content — the file is now clean. Flagging the class of hazard (yet another live git-stash-race collision on this checkout, joining the 6+ already tracked in the cross-tranche big-findings doc), not a currently-open corruption. |
| `sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md` | claimed only by draft batch14 | Re-verified: batch14 todo 2 still names this doc verbatim, still `status: draft`. No new work found. Still orphaned pending batch14's own operator activation decision (see Mechanical hygiene flags below). |
| `sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md` | deferred to a dedicated maintenance window | Re-verified: sole open item is a full-corpus prod backfill deliberately deferred given 3 documented production regressions on this exact surface (line ~290). Still orphaned, same reason — genuinely operator/time-gated, not bounded. |
| `sports_cf8_out_of_window_mechanism_reconciliation_2026_08_16.md` | sole item cannot auto-resolve | Re-verified: sole open item is `[OPERATOR] P2` remediation-policy decision, 6/7 todos done. Still orphaned, same reason. |
| `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` | 2,436 T-0 shard reconciliation, parked 3+ passes, escalation-worthy per plan_reconciler 2026-08-19 | Re-verified: now 3 consecutive na-eligibility-audit passes (2026-07-30, 2026-08-09, 2026-08-17) have parked this exact item asking for an explicit operator ruling between (A) scope+dispatch a bounded flip-script, or (B) rule it stays human-owned given the surface's regression history. Not bounded/AO-eligible as-is (the fork itself is the open question) — still orphaned, escalation-worthy, unchanged. Flagging again per the "must not sit flagged forever" rule the audits themselves already invoked. |
| `sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md` | claimed only by draft batch14 | Re-verified: batch14 todo 8 still names item 1 verbatim (item 2 is `[OPERATOR][DECISION]`, correctly excluded). Still orphaned pending batch14's activation decision. |
| `sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md` | claimed only by draft batch14 | Re-verified: batch14 todo 4 still names this doc's combined item verbatim. Still orphaned pending batch14's activation decision. |
| `sports_league_id_namespace_migration_2026_07_20.md` (P0) | human-gated STEP 9 delete + instruments-service per-fixture bug | Re-verified: doc itself is `assigned_vm: NA` / `execution_scope: local-only` by design (real cross-todo sequencing dependencies). The one standalone bug (per-fixture `league_id` resolution) was already extracted to batch14 todo 7; Track H is machine-gated on an unresolved operator design fork; STEP 9 delete stays human-gated. No new bounded residue found. Still orphaned, same reason. |
| `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` + `live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md` | **near-duplicate pair**, same VM/root-cause, never cross-referenced — consolidate | **✅ Mechanical fix applied 2026-08-21**: both docs now cite each other in `related:` + carry a Progress Log cross-reference note (not merged — each keeps its own independent evidence trail). **✅ 1 item extracted** → `plans/active/sports_satellite_ao_dispatch_batch17_2026_08_21.md` (dp_live_004's batch-historical-quota-stop CODE todo). The SCRIPT todo (sink-topic provision-check) was re-verified mostly superseded by `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md`'s already-shipped Phase-0 fix — annotated, not extracted (no scoped standing-guard target yet). The `[OPERATOR]` credential ask in both docs remains open, same real-world action either way. |
| `sports_venue_smoke_checker_scope_and_canonical_gap_2026_08_20.md` | 2 P1 reconciliation items | **Correction**: this doc is ALREADY `assigned_vm: planning` / `execution_scope: orchestrator-agent` in its own frontmatter — it is self-dispatched, not a true orphan. 3/4 todos are done (as of 2026-08-21); the sole remaining item ([BACKEND] P1, per-unit result-schema preservation) is already live in its own right-of-way. NOT extracted (would create a competing/duplicate dispatch of a doc that already carries its own `assigned_vm: planning`). Reclassifying from "orphaned" to "self-dispatched, active, not stalled." |
| `sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md` | new 606-object post-delete residual, bounded, batch candidate | **Correction**: this doc is ALSO ALREADY `assigned_vm: planning` / `execution_scope: orchestrator-agent` — self-dispatched, not a true orphan. Its sole open todo (characterize the 606-object post-delete residual) is already live in the backlog under this doc's own dispatch. NOT extracted for the same duplicate-dispatch reason as the row above. Reclassifying from "orphaned, batch candidate" to "self-dispatched, active." |
| `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` | Phase 3 OPERATOR GCS delete, correctly gated | Re-verified — Phase 3's GCS delete stays `[OPERATOR]`-gated by sequencing (depends on Phase 1/2 independent re-verification, out of this pass's scope). Still orphaned, same reason. |
| `predictions_ml_walk_forward_and_arb_2026_06_20.md` | real owner is `prediction` tranche | Re-verified: `assigned_vm: NA`, `execution_scope: local-only`, dual-tagged `[prediction, sports]`. Confirmed out of sports-tranche scope — not touched, per the `/prediction` tranche's own remit. |

## Mechanical hygiene flags

- `sports_satellite_ao_dispatch_batch14_2026_08_16.md` — draft, cited as live coverage by 5+ na-eligibility-audit
  passes for docs it doesn't actually cover yet. Either activate it or revisit those "KEEP-NA-STALE" verdicts.
  **Re-verified 2026-08-21**: still `status: draft` (5 days since 2026-08-16). Read all 8 citing docs directly —
  every one already correctly states "status: draft, not yet dispatched/active" and explicitly defers its own
  checkbox flip to batch14 landing (e.g. `sports_catalogue_reroll_...`: "Citation-only fix, not a reclassification.
  Doc stays `assigned_vm: NA`"). **The citations are NOT stale/misleading — nothing to fix there.** The real
  standing cost is that batch14 itself has sat undispatched for 5 days while blocking real backlog capacity:
  `idle_lingering_session_reclaim_not_firing_2026_08_19.md` records `gate-upstream-open:sports_satellite_ao_dispatch_batch14_2026_08_16`
  as the 2nd-largest blocker (11 blocked tasks) in a live idle-slot diagnostic. Activating batch14 is explicitly
  **not** a no-judgment mechanical fix — its own text says "flipping to `active` needs explicit operator approval
  before this batch dispatches" (9 real todos: 2 prod VM launches, a prod CF-8 backfill, several code fixes across
  6 repos). NOT activated this pass. **Flagging for explicit operator attention**: batch14 has been ready-to-review
  for 5 days with a measured 11-task backlog cost — recommend the operator either approve activation or explicitly
  decline so the 8 citing docs stop re-confirming the same "still draft" state on every audit pass.
- `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` /
  `live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md`: both describe the identical incident
  (VM `mtds-live-sports-odds-api-odds-20260816-145019`, connector missing `upstream_failure_reason()`, exhausted
  odds-api-key, fabricated `SOURCE_RETURNED_ZERO`) — filed hours apart, no cross-reference either direction.
  **✅ FIXED 2026-08-21**: both docs now cross-reference each other in `related:` + a Progress Log note; see the
  orphan table row above for the accompanying batch17 extraction.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit sports Phase-1 sweep (3 batches).
- **ag-closeout-audit 2026-08-21 (sports tranche, Phase 2/3 sub-agent sweep)**: Phase 2 — re-verified both
  Mechanical hygiene flags; applied the near-duplicate-pair cross-reference fix directly (2 files edited); the
  batch14 flag re-verified as not a stale-citation problem after all (all 8 citing docs are already accurate) —
  reframed as an operator-attention item instead of applying a unilateral activation. Phase 3 — re-read all 17
  orphan-table rows directly (not trusted from the original one-line summaries): found exactly 1 genuinely
  bounded/conflict-clear item, extracted to `sports_satellite_ao_dispatch_batch17_2026_08_21.md` (`status: draft`,
  `assigned_vm: NA` — needs operator review, per this session's explicit instructions). Found + corrected 2
  misclassifications (`sports_venue_smoke_checker_scope_and_canonical_gap_2026_08_20.md` and
  `sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md` are both already `assigned_vm: planning`
  in their own frontmatter — self-dispatched, not true orphans; extracting either would have created a duplicate
  dispatch). Found 1 file-corruption big finding (`sports_bookmaker_roster_classification_2026_08_21.md` — live git
  merge-conflict markers embedded in the working-tree file itself, not editable safely this session). All other 12
  rows re-confirmed correctly orphaned for their originally-stated reason. Did not re-open or re-litigate any
  archived/already-closed sports docs outside this parked doc's own 17-row table — out of this session's scope.
