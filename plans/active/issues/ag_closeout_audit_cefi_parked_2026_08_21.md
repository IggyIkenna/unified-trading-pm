---
doc_type: issue
title: ag-closeout-audit cefi 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit cefi tranche Phase 1 audit (4 batches, 103 candidate docs). Full read-only
  classification of every AG-primary doc against the tranche's real dispatched AO-batch coverage. Records every
  orphaned/partial-coverage doc + mechanical hygiene flags for Phase 2/3 follow-up.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, cefi, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/cefi_consolidated_closeout_2026_07_18.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: cefi_master
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
source: ["2026-08-21 — /ag-closeout-audit cefi, 4 Phase-1 batches, 103 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit cefi 2026-08-21

103 candidates, 4 batches. Counts: archivable_now 10 · archivable_after_planned_work ~18 (mostly self-dispatched
issue docs) · orphaned_partial_coverage 3 · orphaned_never_touched ~48 · exclude_cross_cutting ~24.

> **Phase 3 re-verification 2026-08-21 (ag-closeout-audit cefi tranche)**: every row below was re-checked against
> its own current frontmatter (`assigned_vm`/`execution_scope`) and, for the highest-signal rows, a full re-read —
> not just the one-line summary here. **Headline finding: zero rows qualified for a NEW satellite batch.** The
> "uncovered/bounded" rows turned out to be one of three things: (a) **false orphans** — already
> `assigned_vm: planning` + `execution_scope: orchestrator-agent`, i.e. genuinely self-dispatched and actively
> cycling through AO already (`cefi_track7_candle_bundle_regeneration_vm`, `manifest_consolidator_market_data_cefi_
> stuck_lock`, `cefi_live_venue_string_dispatch_broken`, `dp_vm_002_cefi_queue_heavy_binancefutu…`,
> `source_column_blank_on_external_cells`, `upbit_cefi_data_gap_may_2026` — 6 docs); (b) **mechanically un-orphaned
> this run** — `assigned_vm: vm-cross-cutting`, a stale legacy pre-2026-06-27 multi-VM value that the current
> single-VM `regen_backlog_from_plan.py` ingestion path silently drops (`assigned_vm` must equal the live `vm_id`
> "planning", or be absent — a value present-but-non-matching is excluded, not defaulted) — fixed to
> `assigned_vm: planning` directly on the 2 affected cefi docs (`dp_fetch_009_cefi_liquidations_raw_contract_
> overwritten`, `dp_fetch_009_cefi_liquidations_batch_aster`); **this same stale value was found on 9 more docs
> corpus-wide (sports/cross-cutting tranches) — flagged as a cross-tranche finding, not fixed here (out of cefi
> scope)**; (c) **mechanical hygiene** — the 4-doc `dp_live_004` near-duplicate cluster (same VM, same root cause,
> same fix, filed independently by 4 escalation dispatches with zero cross-referencing) was consolidated into its
> one already-correctly-dispatched member, with 2 real tracked `- [ ]` todos added (it had ZERO before despite
> `assigned_vm: planning`) and the 3 duplicates marked `status: superseded`. Every remaining row was re-verified via
> its own `assigned_vm: NA` + `execution_scope: local-only`/`human` frontmatter (deliberately not AO-dispatched by
> design) and its taxonomy confirmed still accurate — no new information changed any of those verdicts. Per-row
> disposition is now inline below.

## Orphaned (never_touched or partial_coverage) — need a future batch or operator ruling

- [ ] [DATA] P2. `aster_and_cefi_rolling_adv_feature_2026_07_21.md` — sole item (Phase-3 book_depth.py stretch),
      operator-gated judgment call. Taxonomy: operator-gated.
- [ ] [DATA] P2. `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` — Phase D (`_index` rebuild
      `--apply`) + Phase E verify; Phase B's 287,074-object delete already ran clean. Taxonomy: conflict-gated
      (re-assess AO-eligibility — Phase D/E may now qualify). **RE-VERIFIED 2026-08-21**: still
      `assigned_vm: NA` / `execution_scope: local-only` — a GCS `--apply` rebuild stays correctly human-gated per
      delete-safety convention; taxonomy unchanged.
- [ ] [DATA] P1. `cefi_ml_directional_continuous_live_2026_06_20.md` — backtest-fidelity gap partially covered by
      track2 batch; ≥7-day live-capital wallet-key hard-stop stays permanently human. Taxonomy: partial/human-hard-stop.
- [ ] [DATA] P2. `cefi_tardis_date_concurrency_2026_08_16.md` — concurrency step-to-6 + Phase-4 tail-latency, both
      dependency-blocked on Tardis N=1 slot. Taxonomy: time/resource-gated.
- [ ] [RESEARCH] P3. `crypto_alpha_research_2026_07_24.md` — large research backlog + §C permanently operator-gated
      trading-judgment groups. Taxonomy: operator-gated (standing).
- [ ] [DATA] P2. `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — equity-perp Tardis backfill launch,
      **duplicated** in `cefi_consolidated_closeout_2026_07_18.md` Track 0, neither dispatched. Taxonomy: duplicate
      tracking gap — needs reconciliation before dispatch.
- [ ] [DATA] P2. `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` — G1 sign-off missing, EXTENDED CF-11 design
      call, G4 eligible-but-unsigned, G5 orphaned DoD items. Taxonomy: operator-gated.
- [ ] [DATA] P3. `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md` — 2 design-judgment
      items, doc's own text: "needs a maintainer/operator call". Taxonomy: operator-gated.
- [ ] [INFRA] P3. `cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md` — opportunistic/non-blocking.
      Taxonomy: low-priority, uncovered.
- [ ] [DATA] P2. `cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md` — Tardis-tier spend decision + monitor-
      to-completion. Taxonomy: operator-gated.
- [x] [DATA] P2. `issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md` — 2 P3 dead-code/staleness items.
      Taxonomy: conflict-gated (re-triageable). **RE-VERIFIED 2026-08-21: FALSE ORPHAN.** Already
      `assigned_vm: planning` / `execution_scope: orchestrator-agent` — genuinely self-dispatched, not orphaned. No
      action needed.
- [ ] [DATA] P1. `issues/cefi_okx_spot_bybit_spot_backfill_never_relaunched_2026_08_16.md` — 3 relaunch todos,
      Tardis N=1-blocked. Taxonomy: resource-gated.
- [ ] [DATA] P2. `issues/cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md` — extracted to draft
      `batch22` (not real coverage — draft ≠ active). Taxonomy: false-orphan (draft-batch-limbo) — promote batch22.
- [ ] [DATA] P2. `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` — 586 marker-less rows
      `[OPERATOR]`-gated; Parquet CONTENT backfill P0 tracked in `cefi_content_migration_fleet_half_incomplete`
      (not in covering set — reconcile citation). Taxonomy: partial, citation gap.
- [ ] [DATA] P2. `issues/cefi_tardis_date_serial_barrier_still_open_2026_08_16.md` — items 1/2 held under a
      2026-08-16 operator ruling ("human plan, execute today"), redirects to `cefi_tardis_date_concurrency_2026_08_16.md`.
      Taxonomy: operator-gated, non-batchable.
- [x] [DATA] P2. `issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md` — per-day-scoped MDPS `--force`
      relaunch. Taxonomy: uncovered, bounded — batch candidate. **RE-VERIFIED 2026-08-21: FALSE ORPHAN.** Already
      `assigned_vm: planning` / `execution_scope: orchestrator-agent` — its Progress Log shows repeated AO workers
      (slot-15/13/24) actively re-dispatching against it, currently `reason_code: GATED` on a backfill VM's terminal
      state. Genuinely self-dispatched and cycling; no batch extraction needed (would be duplicate coverage).
- [ ] [DATA] P2. `issues/deribit_dated_option_trades_perpetual_misclassification_2026_07_27.md` — ~988GB DERIBIT
      dated-option data misclassified as perpetual, census/backfill/reclassify never dispatched
      (`execution_scope: human`, reaffirmed too-large-or-risky). Taxonomy: too-large-for-a-batch-todo.
- [ ] [DATA] P2. `issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md` — `[OPERATOR] P1` investigate 2
      live-capture stalls (BYBIT-FUTURES + CME). Taxonomy: operator-gated; near-duplicate of dp_live_004 cluster
      below.
- [x] [DATA] P2. `issues/dp_cron_did_not_fire_storm_recurred_on_stable_revision_2026_08_17.md` — 3 open todos
      (root-cause the ~2-3h-later regression). Taxonomy: uncovered, needs a batch. **RE-VERIFIED 2026-08-21: NOT a
      coverage gap.** `assigned_vm: NA` / `execution_scope: local-only` is deliberate — the doc's own Progress Log
      shows it re-confirmed `KEEP-NA` twice by na-eligibility-audit (2026-08-17, 2026-08-18): this doc's population
      is worked by the `data_pipeline_alerts_reconciler`'s own 6-hourly scheduled sweep, a DIFFERENT dispatch
      mechanism than the generic AO backlog. A satellite batch would create duplicate/conflicting coverage. No
      action.
- [ ] [DATA] P0. `issues/dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md` — 149,309-row
      batch-side population may share the same over-catch mistake as the already-fixed live rows; re-dispatched 3x,
      never resolved. Taxonomy: carried finding (3+ re-confirmations) — needs a dedicated scoped plan. **RE-VERIFIED
      2026-08-21**: still `assigned_vm: NA` / `execution_scope: local-only` / `execution_scope: human` (doc's own
      priority now reads P1, not P0 — minor drift from this parked doc, not chased). Taxonomy confirmed still
      accurate — a 149k-row corrective migration needs a dedicated scoped plan, not a batch todo.
- [ ] [DATA] P2. `issues/dp_fetch_009_cefi_liquidations_batch_aster_2026_08_20.md` — Tardis code-274 lockout slice.
      Taxonomy: uncovered.
- [ ] [DATA] P1. `issues/dp_fetch_009_cefi_liquidations_raw_contract_overwritten_2026_08_20.md` — UAC fix shipped but
      NOT reflected in prod MTDS writer (4,535 fresh failures post-fix). Taxonomy: uncovered, real correctness gap.
- [ ] [DATA] P2. `issues/dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md` — `[OPERATOR]`
      relaunch-vs-wait, pending 4th relaunch outcome. Taxonomy: operator-gated.
- [x] [DATA] P2. `issues/dp_vm_002_cefi_queue_heavy_binancefutu_streaming_writer_progress_gap_2026_08_14.md` —
      `[OPERATOR] P2` relaunch todo (only a cosmetic frontmatter fix was covered by batch20). Taxonomy: uncovered.
      **RE-VERIFIED 2026-08-21: FALSE ORPHAN.** Already `assigned_vm: planning` / `execution_scope:
      orchestrator-agent` — genuinely self-dispatched. No batch extraction needed.
- [ ] [DATA] P2. `issues/dp_vm_003_canonical_migration_cefi_deribit_sweep_wedged_relaunched_fresh_name_2026_08_16.md`
      — `[OPERATOR] P2` decide fate of old wedged VM. Taxonomy: operator-gated.
- [ ] [DATA] P2. `l2_book_microstructure_capture_2026_07_13.md` — features-extractor wiring + live event-log
      dispatcher wiring, correctly BLOCKED per 2026-07-14 operator ruling. Taxonomy: time/event-gated.
- [x] [DATA] P0. `manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` — CeFi manifest-consolidator fix
      shipped to source but NOT yet live in the deployed `market-tick-data-service:latest` Cloud Run cron image; same
      41.6h manifest-freeze incident (zero alerts) can recur until rebuilt+redeployed. Taxonomy: deploy-chain gap,
      P0 recurrence risk. **RE-VERIFIED 2026-08-21: FALSE ORPHAN.** Already `assigned_vm: planning` /
      `execution_scope: orchestrator-agent` / `sequential: true` — genuinely self-dispatched; its sole remaining
      todo (the MTDS image rebuild, `[INFRA] P2`) is already a normal AO todo. No batch extraction needed.
- [ ] [DATA] P2. `issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md` — newer 2026-08-18
      BTC/ETH/SOL/XAU disambiguation item, uncovered (older crypto-base item already closed via batch21).
      Taxonomy: uncovered.
- [ ] [DATA] P2. `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` — 2 live prod-GCS split-brain
      MERGE ops, delete/move-safety-gated. Taxonomy: delete-safety-gated.
- [ ] [DATA] P2. `issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md` — OKX/Hyperliquid scope-separation
      design + Upbit/Kraken/Bitfinex/Bitget provisioning (human). Taxonomy: mixed operator/human-gated.
- [x] [DATA] P2. `issues/source_column_blank_on_external_cells_2026_08_15.md` — provenance-enforcement flip gated on
      a deferred 1-row HYPERLIQUID/trades manual patch. Taxonomy: dependency-gated. **RE-VERIFIED 2026-08-21: FALSE
      ORPHAN.** Already `assigned_vm: planning` / `execution_scope: orchestrator-agent` — genuinely self-dispatched
      (the dependency-gate is on the doc's own completion, not on AO reachability). No batch extraction needed.
- [x] [DATA] P2. **Near-duplicate cluster (4 docs), needs consolidation before any dispatch**:
      `issues/dp_live_004_bybit_futures_book_snapshot_unproductive_2026_08_21.md`,
      `issues/dp_live_004_bybit_stale_vm_relaunch_required_2026_08_20.md`,
      `issues/dp_live_004_bybit_vm_stale_tarball_2026_08_20.md`,
      `issues/dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md` — all 4 describe the identical incident (same
      VM, same root cause: BYBIT-FUTURES book_snapshot_5 predates fix `market-tick-data-service@5f88715e4b`), filed
      independently by different escalation dispatches, none cross-referencing. Taxonomy: mechanical hygiene —
      consolidate into one doc with one tracked todo (cycle the VM) before dispatching. **CONSOLIDATED 2026-08-21**:
      `dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md` (already had the correct `assigned_vm: planning` /
      `execution_scope: orchestrator-agent` but ZERO `- [ ]` todos, so nothing was actually dispatchable) is now the
      canonical doc — added 2 real tracked todos (VM cycle + post-cycle verification) and `related:` links to the 3
      siblings. The 3 siblings marked `status: superseded` + `superseded_by:` pointing here, evidence kept intact.

## Mechanical hygiene flags (Phase 2 sweep applied 2026-08-21 — see per-item disposition below)

- `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`: Deferred-work table row contradicted an `[x]` checkbox
  a few lines above it (same commit, `deployment-service@0c38c00d`) — stale, never revised. **FIXED 2026-08-21
  (ag-closeout-audit cefi tranche, Phase 2 sweep)**: re-verified `0c38c00d` live (`git cat-file -t` + `merge-base
  --is-ancestor` against the real `deployment-service` checkout — resolves, is an ancestor of HEAD), then annotated
  the stale row with the same "CORRECTED … DONE" pattern the doc's own two sibling rows already use, and added a
  dated Progress Log entry + bumped `last_updated`.
- ~40% of cefi's raw candidate set turned out to be genuinely multi-AG/plan-hygiene docs padded into the tranche via
  array-containment (`parent_epic: instruments_master`/`security_and_cross_cutting_master`/etc.) — verdicted
  `exclude_cross_cutting`, not listed above. **No action** — this is a methodology note about the raw candidate set,
  not a specific doc to edit.
- `coverage_floor_registries_no_cross_propagation_2026_07_17.md` (5-AG doc) has its sole remaining item tracked
  exclusively via cefi's own `batch20` item 10 — should route through a cross-cutting batch instead. **Re-verified
  2026-08-21: no per-doc fix needed.** This is the exact "Cross-tranche routing / coverage-attribution gaps" pattern
  already documented in `/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md` ("A doc's
  real AO-dispatch coverage sometimes comes from a DIFFERENT tranche's batch than the one auditing it… not a gap,
  just means the per-tranche orphan counts slightly overstate true orphan totals until reconciled cross-tranche").
  The doc's sole open Follow-up (HYPERLIQUID re-verify, re-pointed to the 2026-08-16 fleet) is itself still genuinely
  in-flight — `batch20` item 10 (line ~227) is still `[ ]` open, not stale — so there is nothing broken to fix here;
  reclassifying which tranche's batch should own it is a cross-tranche routing decision, out of this tranche's scope.

## Big findings

See `/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md` items 6 (UPBIT-adjacent),
9. Also standalone this tranche: **UPBIT (an MVP CeFi venue) has had zero captured data for 72+ days** — fully
diagnosed, worker-determinable fix (relaunch once Tardis N=1 slot frees), 3 sessions have GATED-released it with no
extraction into a satellite batch to retry. `issues/upbit_cefi_data_gap_may_2026_2026_08_04.md`. **CORRECTED
2026-08-21 (ag-closeout-audit cefi Phase 3)**: the "no extraction into a satellite batch" framing is inaccurate —
the doc is already `assigned_vm: planning` / `execution_scope: orchestrator-agent`, i.e. genuinely self-dispatched;
a batch extraction would be duplicate coverage, not a fix. The real, still-open problem is the shared Tardis N=1
concurrency slot (same root blocker as `cefi_tardis_date_concurrency_2026_08_16.md` and
`cefi_okx_spot_bybit_spot_backfill_never_relaunched_2026_08_16.md`) — AO keeps re-dispatching and correctly
skipping with `reason_code: GATED` because the slot is occupied, not because the doc is unreachable. Still worth
operator attention as a genuine 72+-day live-data gap, just not for the reason originally stated.

## Progress Log

- **ag-closeout-audit 2026-08-21 (cefi tranche, Phase 2 + Phase 3 sweep)**: Phase 2 applied the one real mechanical
  fix (`data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`'s stale Deferred-work table row) and re-verified
  the other 2 flagged items needed no per-doc action. Phase 3 re-verified all ~31 orphan-list docs; found ZERO
  genuine bounded-but-uncovered candidates for a new satellite batch. Instead found and fixed 3 distinct bug
  classes: (1) 6 docs mis-classified "orphaned" that were actually already `assigned_vm: planning` /
  `execution_scope: orchestrator-agent` self-dispatched (false orphans, no action needed beyond the correction
  noted inline); (2) 2 cefi docs (`dp_fetch_009_cefi_liquidations_raw_contract_overwritten`,
  `…_batch_aster`) genuinely un-reachable by AO due to a stale legacy `assigned_vm: vm-cross-cutting` value —
  retagged to `planning` (9 more docs corpus-wide carry the same bug, flagged cross-tranche, not fixed here); (3)
  the 4-doc `dp_live_004` near-duplicate cluster consolidated into its one correctly-dispatched member, which had
  zero actual `- [ ]` todos despite correct dispatch frontmatter — added 2 real tracked todos, marked the 3
  duplicates `status: superseded`. No new `cefi_satellite_ao_dispatch_batch*` doc was created this run — none of
  the re-verified work qualified (everything real was either already self-dispatched, correctly gated by design, or
  fixed directly in place). Did not get to a full-content re-read of every `assigned_vm: NA` / `execution_scope:
  local-only` row (only frontmatter-consistency-checked) — those retain their original Phase-1 taxonomy, re-checked
  only for the specific "is this actually self-dispatched despite looking orphaned" bug class described above.
