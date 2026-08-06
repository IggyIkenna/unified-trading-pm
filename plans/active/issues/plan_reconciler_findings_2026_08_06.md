---
doc_type: issue
title: plan_reconciler findings — defi tranche — 2026-08-06
summary:
  Run-findings doc for the sharded daily plan-reconciler run (tranche=defi). Candidate register, verification results,
  applied fixes, routed items, coverage ledger.
status: open
created: "2026-08-06"
author: plan_reconciler
source: agt-24f4b0
nature: issue
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
parent_epic: defi_master
priority: P3
assigned_vm: NA
resolved_by: >-
asset_group: [defi]
tags: [plan-reconciler, run-findings, defi]
related: [defi_consolidated_closeout_2026_07_18]
locked_by: agt-24f4b0
---

# plan_reconciler run findings — defi tranche — 2026-08-06

Dispatch: `agt-24f4b0` · slot 7 · tranche `defi` · review branch `plan_reconciler/agt-24f4b0`

## Scope + inventory

- defi-tranche corpus (asset_group matching defi): **96 docs** = 28 active plans + 67 issue docs + 1 epic
  (`defi_master`)
- 12h GRACE SET (read-only this run): **45 docs** — heavily in-flight corpus (batch9/batch10 dispatches,
  hyperliquid→cefi migration, LST-rate work)
- WORKING SET (fixable): **51 docs** = 41 with open todos + 9 fully-done/zero-open candidates + 1 epic (41 open todos)
- Zero-checkbox docs in working set: `candle_feature_canonical_path_divergence_2026_07_20.md`,
  `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md`,
  `mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`

## Flips verified (applied 2026-08-06, branch plan_reconciler/agt-24f4b0)

1. lst_rate A2 staking leg (`lst_rate_honest_coverage_2026_07_21.md:381`) — `strategy-service@e93902d8`, verified
   ANCESTOR-OF-LDR 2026-08-06; evidence: in-doc audit L983-988 + `lst_rate_honest_coverage_over_cap_findings_2026_08_03`
   todo 2 (doc 18h old, under cap — flip unblocked).
2. lst_rate recursive-staking borrow leg (`:385`) — `strategy-service@23bd8b76` ✓ same evidence.
3. lst_rate Phase-3 sample-download (`:166`) — SUPERSEDED: Phase 5 #3 (AAVE oracle) proved the force-write leg, Phase 5
   #2 (DEX) proved the skip leg — flipped with supersession note.
4. backfill_smoke todo 6 (`backfill_smoke_write_path_canonical_audit_2026_07_20.md:302`) — decision made + both fixes
   shipped (`futures_contracts` + `market_lifecycle` full-hive prefix, `instruments-service@a9be6ce9`, archived hive doc
   todos 4-5 `[x]`).
5. backfill_smoke todo 3 (`:284`) — all three in-repo comment targets verified corrected in-tree
   (`instrument_availability_paths.py:21`, `DEFI_INSTRUMENTS.md:642`,
   `repair_tradfi_instrument_type_counts_2026_07_17.py:21`).
6. cryptovenue Barchart (`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md:228`) — RETIRED 2026-06-24, no
   shim (`/codex/02-data/pipeline-mode-partition.md:156`, availability-manifest:599-601; code: UAC `BATCH_BARCHART`
   removed, "No live Barchart adapter is needed").
7. cryptovenue KRX backfill (`:206`) — SUPERSEDED by 2026-06-28 Option C ruling (`EXPECTED_SOURCE_NOT_AVAILABLE`
   honest-empty; gate 378→0; `krx_equity_twin_no_source_2026_06_28.md` archived).
8. perp_daily_ctx `[OPERATOR-DECISION] P3` (`defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md:274`) — RESOLVED
   by citation: the DESIGN gate closed 2026-07-28 as KEEP BOTH (archived doc RESOLVED banner + `[x] ✅ [DESIGN] P1`) —
   no demote, fold question moot.
9. batch2_finalize `[DOC] P2` (`defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md:81`) — all 3 sub-items resolved
   by citation (retag already applied 2026-08-02 + still locked → own defer condition; other two docs archived).

## Contradictions (fixed/annotated)

- yearn summary "most likely a STALE row" vs todo 1 REFUTED (07-28, live manifest) — summary updated with the structural
  root cause (`SOURCE_PRIORITY[('defi','vault_share_price')]` single-source auto-stamp).
- perp_daily_ctx :161-167 "still-open `[DESIGN] P1` todo" — CLOSED 2026-07-28 KEEP BOTH — annotated (premise stale).
- catalog:71 tick-loader "not-yet-attempted follow-on" — SHIPPED 2026-07-23 `strategy-service@795fa10c` (curtailment doc
  Phase 1 FULLY SHIPPED) — corrected.
- cryptovenue Phase 2 step 2 `EQUITY_PERP` override vs 2026-07-16 operator banner — annotated STALE (identity rides
  `is_equity_perp`/`tracks_equity` tags).
- honest_coverage :571-572 "BINANCE-DELIVERY live-captured (2,126 rows)" vs Finding 4 CORRECTED (ZERO MTDS rows ever) —
  annotated corrected.
- track5 "no canonical rows written / R3 RUNNING partial" vs v10 archived GATE MET 2026-07-28 (11,440 captured, 0
  residual, finalize "No residual work remains") — annotated both spots; the flag-flip question routed (see Filed).
- defi_master PACIFICA-SOLANA presented active vs operator 2026-07-18 decommission — annotated.
- defi_master "7 active plans" — 15 plans + 15 issue docs today — updated.
- defi_master `assigned_vm: vm-defi` (invalid since 2026-06-27) — corrected to NA.

## Doc-drift

(append as confirmed)

## Hygiene fixes (applied)

- Path conventions (leading-slash + archive repoints): defi_master (~24 refs incl. the auto-populated child table),
  backfill_smoke ×2, mdps_features_deadcode ×5, non_tardis ×5, turbo ×2, yearn ×2, morpho ×2, perp_daily_ctx ×5, candle
  ×1, defi_pipeline_e2e ×3, upstream ×1, mtds_pipeline_check ×1, defi_catalog ×1.
- Non-canonical todo prefixes stripped (10): yearn:158/166, candle:442/485, mdps_features_deadcode:73/78/82/112,
  data_pipeline_check_mdps_features:193/319 (numbers preserved after the tag for prose cross-refs).
- `- [~]` → `- [ ]` (3): mtds_is:409, data_completion:201/375.
- lst_rate stray `</content>` removed (992→991L); `last_updated` refreshed (defi_master, mtds_is).
- catalog "7 already-drivable beyond" → 6 (count fix); liquidation-feed build now a TRACKED `- [ ]` todo (was untracked
  prose); track5 BLK-d355f03a return-path now a TRACKED `[OPERATOR]` todo.
- M1: perp_daily_ctx:270 placeholder `<pending-quickmerge-sha>` → `unified-api-contracts@75245222` ("feat(defi):
  register perp_mark_price as canonical data_type + SchemaContract", 2026-08-04 window).
- upstream R5-fix-7 citation → ledger archive (`r5_smoke_ledger_history_2026_08_05.md`, R5-fix-7 DONE 2026-08-04).
- defi_turbo :300 dangling "Update §3 below" → fixed; cryptovenue `\*\*` escape + B1-leg annotation.
- data_completion live_websocket ×3 → RETIRED 2026-06-30 annotations (net-zero line edits — doc pinned at 1000L).
- codex SSOT: defi-canonical-naming-ssot:88 `perp_funding` reclassification caveat (3 rulings 07-06/07-25/07-26, GMX
  removed 07-25); availability-manifest:174-195 dead dedicated-bucket section bannered SUPERSEDED + DELETED 07-13/14.
- AG-closeout orphan linkage: `defi_consolidated_closeout_2026_07_18` added to related of balancer, bridge_events,
  features_clean, gas_fees, dex_pool_state (5 non-grace; 4 grace-skipped — dex_pool_swaps_733 7h, delta_one 2h, lighter
  2h, blazestake 2h).

## Filed / routed (operator)

- track5/v10: does v10's archived GATE MET 2026-07-28 (11,440 rows, 0 residual) satisfy
  `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (the unpark note requires per-instrument shard-key
  progress)? → POST /api/slots/7/blocked (can_continue: true).
- KALSHI batch2:306: (a)/(b)/(c) disposition of the 567 already-written KALSHI_PERP/POLYMARKET_PERP objects — todo's
  Done-when is operator-gated on the kalshi issue's open `[OPERATOR] P2` → routed.
- defi_lst_oracle archive: all `[x]` + scope resolved, but `locked_by: live-defi-rollout` (locked_since 2026-05-21
  predates created 2026-07-20 — lock-hygiene flag) → [unlock-plan] + archive requested.
- defi_cefi_venue_chain_axis_contamination: 1001L hard-cap breach (GRACE doc) → operator-gated split required before any
  further edits.
- dex_pool_state archival: DEFERRED this run — refs from in-flight grace docs (batch6:440, batch10:219) would dangle;
  linkage fix applied; re-evaluate next run.
- batch9_finalize duplicate `[DOC] P1` tags (L61/L77): GRACE doc (created today) — noted for next run.

## Archive candidates (operator review)

(append as confirmed)

## Refuted (dropped by verify)

- candle header counts (H4-F3): time-qualified "as of 2026-07-20" — not a contradiction.
- candle 20-vs-17 todos (H4-F1): different referents (execution doc vs its own 17).
- pnl_interest_accrual :538 `[x]` (H4-F9): the filed-extension todo is done; the backfill is tracked in the extension
  doc — honest state.
- mdps_features D2/D3 (H1): deliberate M3-gate flips with re-opened follow-ups below — documented, not findings.
- mdps_features 9b (H1-D1): timeline-consistent — the "remains genuinely open" entries predate slot-7's completion; the
  flip documents the finished run + report + re-opened issues.
- defi_master:846 inverse (H7-4): `[x]` + `[PARTIAL-DONE]` marker; remainder explicitly tracked ("see item below") —
  deliberate authoring pattern, no uncheck.
- candle zero-checkbox (H4/H9 premise correction): has 2 open todos — inventory corrected, not an archive candidate.
- expected_unattempted fully-done (H9): has 1 nested `* [ ]` todo + LOCKED — correctly kept active.
- H8-F3 (pipeline-mode table `batch_defillama`): self-weakened by the doc's own "illustrative, not exhaustive" note.
- H5-F5/F6 (expected_unattempted banner/numerics): LOCKED doc — noted, not edited.
- H4-F4 (autonomous_decisions trim claim): historical log entry describing a past state (doc regrew since) — noted.

## Coverage (hunters / batches / docs) — all 10 reported

- H1 epic+big plans ✓ (defi_master, lst_rate_honest_coverage, data_completion_defi, data_pipeline_check_mdps_features) —
  A1-A3, B1-B8, C1-C9, D1-D7
- H2 active plans B ✓ (batch2, cryptovenue, defi_collateral, cefi_ml, track5, defi_pipeline_e2e) — F1-F13
- H3 issues batch1 ✓ (catalog, estate_orphan, morpho, curtailment) — A1-A7
- H4 issues batch2 ✓ (autonomous_decisions, pnl_interest_accrual, mtds_is, honest_coverage, candle) — F1-F11 +
  dispatch-premise corrections
- H5 issues batch3 ✓ (non_tardis, upstream, perp_daily_ctx, turbo, expected_unattempted, lst_oracle) — F1-F6, M1-M3, R1,
  S1-S6
- H6 issues batch4 ✓ (mdps_deadcode, yearn, backfill_smoke, gas_fees, features_clean, dex_pool_state) — F1-F9
- H7 missed-flip sweep ✓ (all ~96 docs, 262 open todos scanned) — 3 HIGH flips + 4 LOW partials + rejections
- H8 codex-alignment ✓ (9 plans × 8 SSOTs; resumed after connection error) — F1-F6
- H9 mechanical ✓ (non-canonical ×10, AG-closeout orphans ×9, caps, zero-checkbox, fully-done verification)
- H10 AO-readiness + grace ✓ (batch2:306 line-1, mdps:193/319/767, finalize statuses, batch9_finalize tags) + Part B
  grace-set one-liners

**Plans not reached**: none — the full 51-doc working set was covered (96-doc corpus inventoried; 45 grace docs
context-checked by H10 Part B).

## Plans not reached

(append if any)

## Phase-5.9 ledger

- routed_to_operator: 3 (track5/v10 flag question · KALSHI (a)/(b)/(c) · lst_oracle unlock+archive) — POST
  /api/slots/7/blocked can_continue:true
- parked_in_issue_doc: this findings doc
- agent_skips: 0 (all items routed or applied; grace-skipped items explicitly recorded for next run)

## Run progress — pre-compact checkpoint 2026-08-06 20:31 UTC

**State**: STEP 3 in flight — 10 read-only hunters launched in parallel (all model=sonnet, full
SUB_AGENT_MANDATORY_RULES injected). Results arrive as notifications; each feeds STEP 4 (adversarial verify: refuter +
confirmer, tiebreaker on splits; HARD-evidence bar for flips = sha reachable on `origin/live-defi-rollout` via
`git merge-base --is-ancestor`, or artifact live via grep-then-READ). Then STEP 5 (apply on review branch only), STEP 6
(route via `/blocked` + file here), STEP 7 (PR plan_reconciler/agt-24f4b0 → live-defi-rollout), STEP 8 (/done when no
open questions).

**Hunter roster (10)**:

- H1/H2/H3 — epic-cluster: defi_master.md + lst_rate_honest_coverage, data_completion_defi,
  data_pipeline_check_mdps_features, defi_satellite_batch2, cryptovenue, defi_collateral_sizing, cefi_ml_directional,
  defi_track5, defi_pipeline_e2e, instruments_satellite_batch1
- H4/H5/H6 — issue-cluster: all 23 working-set issue docs (defi_catalog_engine_config_key_contract_drift,
  estate_orphan_assessment, defi_morpho, defi_archetype, autonomous_session_operator_decisions, pnl_interest_accrual,
  mtds_is_full_adapter_smoketest, honest_coverage_shard_dimension, candle_feature_canonical_path_divergence,
  non_tardis_dexperp, defi_upstream_instruments_catalog_stale, defi_perp_daily_ctx_manifest_gap, defi_turbo,
  defi_expected_unattempted_backlog, defi_lst_oracle, backfill_smoke, adapter_findings, defi_legacy_precanonical,
  mtds_gas_fees, features_service_clean_check, defi_pipeline_mode_yearn, mdps_features_deadcode, dex_pool_state_build)
- H7 — missed-flip sweep: all ~96 defi docs, open `- [ ]` with sha/PR/artifact evidence in own text
- H8 — codex-alignment: 9 working active plans vs cited codex SSOTs (defi-canonical-naming-ssot, honest-coverage-model,
  pipeline-mode-partition, availability-manifest, honest-absence, defi-execution-overview, live-data-persistence,
  feature-formula-versioning)
- H9 — mechanical adjudicator: non-canonical todos (candle_feature:485, defi_pipeline_mode_yearn:158/166,
  mdps_features_deadcode:112), AG-closeout orphans (defi), terminal-status, line-caps
  (defi_cefi_venue_chain_axis_contamination ~1001L over-cap — GRACE, flag only), 3 zero-checkbox docs, 6 fully-done docs
- H10 — AO-readiness (vm=planning plans) + grace-set status one-liners

**Phase-0 mechanical inputs (measured, re-derivable in seconds)**:

- defi corpus = `rg -l '^asset_group:.*defi' plans/active/*.md plans/active/issues/*.md plans/epics/*.md` → 96 docs
  (28+67+1)
- grace set (45 docs): newest `git log -1 --format=%ct` <12h — heavily in-flight (batch9/batch10 2026-08-06,
  hyperliquid→cefi migration, LST-rate work); read-only this run
- working set (51 docs): 41 with open todos + 9 fully-done/zero-open + epic (41 open)
- AG-closeout orphans in defi (real, per check_ag_closeout_linkage.py):
  defi_balancer_dex_pool_state_writer_schema_mismatch, defi_bridge_events_historical_backfill_gap,
  defi_dex_pool_swaps_733_row_indexer, defi_onchain_dep_check_blazestake, delta_one_get_available_instruments,
  dex_pool_state_build_instrument_id_colon, features_service_clean_check, lighter_tardis_writerless_route_hang,
  mtds_gas_fees_migration_script (+ my findings doc itself, now linked via
  `related: [defi_consolidated_closeout_2026_07_18]`)
- terminal-status-archived (3, ALL non-defi: sit_stamp_skipped, sports_mtds_backfill_vm_unscoped, omniroute) +
  archive-candidates (2, non-defi: archive_candidates_content_verification_backlog, cloudbuild_template_behind_repos) —
  sibling tranche shards' scope
- reference-path violations (83 format / 88 dangling): NONE in defi-tranche docs — all plans/ai, plans/audit,
  plans/prompts, scratch_scenarios_day1, codex/, sports/ci-owned
- fully-done working docs (archive candidates to verify): instruments_satellite_ao_dispatch_batch1,
  issues/defi_expected_unattempted_backlog_1m, issues/autonomous_session_operator_decisions,
  issues/dex_pool_state_build_instrument_id_colon_in_symbol, cefi_deribit_binance_futures_bundle_verification_finalize,
  issues/defi_lst_oracle_timestamp_glued_instrument_id (last two locked_by live-defi-rollout — LOCKED, operator-gated)
- zero-checkbox working docs: issues/candle_feature_canonical_path_divergence (0 open/0 done — read in full: finished
  record vs prose work), issues/defi_kamino_lending_venue_drift_live_data_verification_gap,
  issues/mtds_pipeline_check_process_killed_during_skip_leg_poll

**Scratch tools (deliberately NOT promoted — re-derivable in seconds)**:

- `/tmp/defi_inventory.py` (per-doc open/done/age/status inventory; the findings-doc sections above already carry the
  derived facts)
- `/tmp/defi_batches.py` (hunter batch file lists)
- `/tmp/defi_docs.txt` / `/tmp/defi_working.txt` (doc path lists)
- `/tmp/hygiene_sweep.txt` (sweep output; the numbers are recorded above)
- None are referenced by any committed doc; no secrets anywhere (checked).

## Deferred work after 2026-08-06

| Item                                                                              | State / why deferred                                                             | Blocked-on                       |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | -------------------------------- |
| STEP 4 — adversarial verification                                                 | DONE (10 hunters + mechanical checks; pair-check in flight)                      | —                                |
| STEP 5 — apply confirmed fixes                                                    | COMMITTED checkpoint #1 (30 docs)                                                | —                                |
| STEP 6 — route hard items via /blocked                                            | 3 questions POSTed (BLK-997409b9 / BLK-555a42f7 / BLK-68917b3e)                  | operator answers                 |
| STEP 7 — PR plan_reconciler/agt-24f4b0 → live-defi-rollout                        | DONE — PR #2397 open; plan-health result POSTed (7 contradictions + 4 doc-drift) | —                                |
| STEP 8 — POST /api/plan_health/result + /done                                     | /done pending                                                                    | pair verdicts + operator answers |
| GRACE-skipped orphan linkage (dex_pool_swaps_733, delta_one, lighter, blazestake) | deferred — docs <12h old today                                                   | next reconciler run              |
| dex_pool_state archival                                                           | deferred — refs in grace docs batch6:440/batch10:219                             | batch6/batch10 land + next run   |
| axis_contamination 1001L split                                                    | operator-gated (GRACE doc)                                                       | operator                         |
| batch9_finalize duplicate [DOC] P1 tags                                           | GRACE doc (created today)                                                        | next reconciler run              |

**Next item**: collect hunter results → dedup → STEP 4 refuter/confirmer pass.
