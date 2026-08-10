---
doc_type: plan
title: TradFi satellite AO batch 11 — orphan extraction from the 2026-08-10 /ag-closeout-audit tradfi tranche pass
summary: >-
  Satellite-batch extraction mirroring /ag-closeout-audit's pattern. Phase 1 classified 52 tradfi-primary candidate docs
  (per generate_ag_closeout_audit_candidates.py, tradfi tranche) against the 15 currently-active tradfi covering docs
  (consolidated closeout + backfill-throughput-followups + manifest-content-recovery-completion(+finalize) +
  phase-d-terminal-gate + registry-coverage-and-ao-readiness(+finalize) + satellite batches 6/7/8/9(+finalize)): 4
  archivable_now, 3 archivable_after_planned_work, 14 orphaned_partial_coverage, 17 orphaned_never_touched, 14
  exclude_cross_cutting. Of the 31 orphaned docs, this batch extracts 14 conflict-clear, bounded, AO-eligible items;
  everything else stays in ## Deferred (tagged by taxonomy) or ## Flagged (cross-tranche ownership, following the
  established batch6/7/8/9 precedent of NOT drafting into docs whose parent_epic routes ownership elsewhere). Conflict
  -checked against every active tradfi covering doc plus the cross-cutting governance_sweep_deferred_followups conflict
  batch8 already found (still unresolved) — zero NEW collisions found among this batch's own 14 todos.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-extraction, batch-11, orphan-extraction]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch11_2026_08_10_finalize.md,
    /plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md,
    /plans/active/issues/ag_closeout_audit_tradfi_parked_2026_08_10.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
depends_on: []
source: >-
  /ag-closeout-audit tradfi-tranche daily pass (2026-08-10, dispatch agt-022d39, slot 25). Phase 1 ran as a 52-agent
  Workflow, one agent per candidate doc, each reading its target doc in full and grepping all 15 active tradfi covering
  docs for real (non-digest) coverage. Phase 3 applied the dispatch-scope eligibility test + the shared conflict-check
  protocol to all 31 orphaned docs' remaining items.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 11 — 2026-08-10

**status: draft — the safety rail.** Not ingested/dispatched until an operator reviews and flips this to `active`.

14 todos extracted from 31 orphaned docs. Every todo cites `Source:` + a `Done when` clause. Same-priority todos here
touch distinct files/repos (verified per-todo below) so they can run concurrently per CLAUDE.md's default. Everything
NOT extracted is either genuinely operator/conflict/time-gated (`## Deferred`, tagged by taxonomy) or belongs to a
different tranche by `parent_epic` (`## Flagged`, following the established batch6/7/8/9 precedent).

## Todos

- [x] [DATA] P1. **Build the canonical-root → raw-Databento-symbol reverse-translation lookup for CME/GLBX.MDP3
      chain-bundle sampling.** The 2026-08-07 `EXCHANGE_CODE_TO_NAME` SSOT fix (naming pick + micro-vs-standard
      distinction, `unified-api-contracts@00b2de54`) resolved the REGISTRY question this was blocked on — the actual
      fetch-time reverse-lookup code was never built. Scope per the source doc's own §4 recommendation: a function
      inside `market-tick-data-service/scripts/pipeline_e2e_check.py`'s sampler that takes a chain-bundle's sampled
      canonical `underlying` and picks the raw Databento symbol to pass as `--instrument-ids`, defaulting to the
      standard (non-micro) contract code family unless the shard is itself micro-tagged (`MICRO-<ROOT>` canonical form →
      the `M`-prefixed raw code). CME/GLBX.MDP3-only for this todo. Repo: market-tick-data-service. Source:
      `issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md` (item 3) +
      `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` §4. ✅ `MTDS@3cec6a00` —
      `_canonical_underlying_to_raw_databento()` shipped in `pipeline_e2e_check.py`; covers CME (standard + MICRO-
      prefix → M-prefixed raw) and CBOE VIX→VX.
- [x] [DATA] P1. **Extend the reverse-translation lookup above to CBOE's `VIX → VX`/`VX.FUT` case** — DEPENDS ON the
      todo above landing first (same underlying mechanism, CBOE-scoped). Repo: market-tick-data-service. Source:
      `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (checkbox line 229). ✅ In same `MTDS@3cec6a00` —
      `_canonical_underlying_to_raw_databento()` handles VIX→VX case.
- [ ] [DATA] P1. **Converge existing GCS chain-bundle + manifest data onto the 2026-08-07-shipped
      `EXCHANGE_CODE_TO_NAME` registry values** — operator sign-off ALREADY RECORDED 2026-08-07 for full agent execution
      (measure → migrate → purge duplicates), "RECLASSIFY-READY" per the source doc's own 2026-08-08
      na-eligibility-audit note, un-extracted through batch8 and batch9 despite that recommendation. Two populations:
      (1) 8 sector-identity codes (XAB/XAF/XAI/XAK/XAP/XAU/XAV/XAY → `*_SECTOR` names), (2) 15 micro-contract codes
      (M6A/M6B/.../MYM → `MICRO-<ROOT>`). Also converge the 3rd copy,
      `unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py`'s own `RootMetadata` table (breaking change
      for its 2 existing tests — update alongside). Mirror `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s
      Surface A-D dry-run→review→`--apply` playbook — never a blind rewrite; measure first, confirm the "unresolved
      passthrough" theory with a live count before assuming it. Heavy-I/O rule applies — runs on a VM via
      `launch-canonical-migration-vm.sh`, never interactively. Repos: market-tick-data-service, unified-api-contracts.
      Source: `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (checkbox line 252). Done when: dry-run
      counts cited for both populations, `--apply` completes with before/after evidence, `tradfi_roots.py` + its tests
      converged, `quality-gates.sh` green in both repos.
- [x] [CODE] P2. **Fix `instruments-service/scripts/cleanup_legacy_twins.py::canonical_twin_path()`'s lookup-logic bug**
      — root-caused 2026-08-09: it cannot reconstruct the canonical GCS path for pre-hive legacy shapes (all 900 tradfi
      class-B candidates are pre-hive), which is why the legacy-twin-bucket-delete gate's Part-5 coverage proof measures
      0% (the manifest DOES cover these cells; the derivation logic is broken). Fix: reuse
      `migration_orphan_sweep.py::classify_object()`'s non-hive-tail venue/instrument_type derivation
      (`_backfill_parser()`), then build the canonical path via
      `unified_api_contracts.canonical_path_templates     ("tradfi")` instead of a partial string-splice. Add regression
      tests for both pre-hive and already-hive-shaped cases. This is the hard prerequisite for
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s own gated delete (NOT itself extracted here — its
      precondition, a fresh 100%-coverage re-run, isn't met until this fix ships; see
      `## Deferred — already in flight`). Repo: instruments-service. Source:
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (todo, line 185). ✅ `is@bbcc6395` —
      `canonical_twin_path()` now derives venue/instrument_type for pre-hive legacy shapes via `_pre_hive_parser()`.
- [ ] [OPERATOR] [DATA] P0. **Execute the operator-ruled `WithinBoundsTradfiSourceZero` bundle-grain purge.** Operator
      RULED 2026-08-07 "GO AHEAD, agent-executable" — dry-run already measured 114,318 candidates, 81,454
      confirmed-safe-to-drop, via `retire_tradfi_cf11_bundle_grain_shard_atom_mismatch_2026_07_30.py`. Not yet executed
      2 audit cycles after the ruling. Before `--apply`: re-run the dry-run fresh (counts may have shifted), then a
      FRESH `gcs_bucket_soft_delete_retention_seconds()` check on the target bucket per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — cite the returned value; execute only if
      ≥604800s (the operator's GO-AHEAD covers the delete itself, this is the reversibility gate, not a fresh ask). Then
      re-measure the `DP_RUN_MOSTLY_EMPTY` CME ohlcv ratio to confirm the purge's expected effect. Repo:
      market-tick-data-service. Source: `issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`
      (todo 1 + dependent todo 4). Done when: fresh dry-run + soft-delete-retention value cited, `--apply` executes (or
      is explicitly re-gated if the retention check fails), before/after `DP_RUN_MOSTLY_EMPTY` ratio recorded.
- [ ] [DATA] P3. **Backfill the 20,254 blank-`instrument_id` `venue=CME`/`instrument_type=FUTURE` manifest rows** now
      that `parse_tradfi_path()` (`market-tick-data-service@bd6233b4`) no longer mis-classifies this shape as a bundle.
      Download + classify each legacy bundled-by-underlying object's rows to derive a real per-row `instrument_id` via
      `derive_tradfi_row_instrument_id`/`build_instrument_id` against the parquet's own `symbol`+`expiry_date` columns;
      write corrected rows; re-verify via a live manifest recount. Repo: market-tick-data-service. Source:
      `issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` (todo, line 141). Done when: a live manifest
      recount shows 0 remaining blank-instrument_id rows in this population, or each remaining row is explicitly
      justified non-resolvable in this doc's Progress Log.
- [ ] [DATA] P3. **Confirm the orphaned `KRX:EQUITY:{code}.KS-USD` manifest shard-atom duplicate (~8261 rows) is
      genuinely dead**, then either exclude it from future enumeration or purge per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (a fresh soft-delete-retention check gates the purge
      leg the same way as the todo above — do not execute a delete without it). Repos: market-tick-data-service,
      instruments-service. Source: `issues/krx_batch11_todo3_intraday_conflicts_with_2026_07_12_ruling_2026_08_09.md`
      (todo 2). Done when: the manifest carries only the canonical instrument_id form for KRX going forward,
      `quality-gates.sh` green.
- [x] [BACKEND] P2. ✅ **Diagnose + resolve the broken `instruments-service-daily` Workflow** —
      `unified-trading-pm@<sha>` (issue doc
      `plans/archive/issues/tradfi_is_corporate_actions_daily_workflow_broken_2026_08_09.md` with full resolution
      Progress Log). Consumer: instruments-service CLI never wired `corporate_actions` (only
      `{"instruments": InstrumentsHandler}`); features-service has its own independent pipeline. Broken since: TF
      disabled 2026-06-26, Workflow created 2026-01-26, never updated. Action: deleted both GCP resources —
      `instruments-service-daily-trigger` (Cloud Scheduler) and `instruments-service-daily` (Cloud Workflow) — both
      verified gone. No ingestion gap.
- [ ] [DATA] P3. **Identify what process wrote the 24 `pipeline_mode~live`/`venue=CME` rows** in the tradfi
      `availability_index.parquet` (max `written_at=2026-08-04`), given the only known live producer VM for this shard
      was deleted 2026-06-30. Grep every market-tick-data-service/deployment-service write call site that could tag
      `pipeline_mode` containing `"live"` for `asset_group=tradfi`, cross-check VM launch history for anything active
      around 2026-08-04, report the actual source (or confirm the read was stale/mis-scoped). No code change required
      unless a genuine mis-tagging bug is found. Repo: market-tick-data-service. Source:
      `issues/tradfi_live_shard_atom_unknown_writer_2026_08_09.md`. Done when: the writer is identified and cited, or
      the read is confirmed stale/mis-scoped.
- [ ] [SCRIPT] P1. **Confirm `wave_launcher.py`'s actual production deployment mechanism** — reconcile the docstring's
      claim ("Cloud Run Job + Scheduler") against `_write_last_run_sentinel`'s comment ("HOST cron"), which are in
      tension; `deployment-service/terraform/gcp/wave_launcher_scheduler.tf` documents a Cloud Run Job + Cloud Scheduler
      `0 */3 * * *` design consistent with the docstring, but this hasn't been cross-checked against whether it actually
      picked up `deployment-service@bcf55c781f98f3834298252c443ed5ffa6f42a35` (the CME dedup fix). Repo:
      deployment-service (terraform/deployment config — distinct from the todo below's target file). Source:
      `issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` (todo, line 165). Done when: the actual
      invocation mechanism is confirmed AND, if it's an image-based Cloud Run Job, either a redeploy has run or one is
      explicitly triggered.
- [x] [CODE] P1. **Patch `wave_launcher.py`'s cell-selection logic to consult the scope-ruling table before
      dispatching** — the durable fix for the 2026-08-09 scope-ruling violation (legacy NASDAQ/NYSE/CME fleet relaunched
      outside its ruled scope); only the reversible stopgap (pausing the Cloud Scheduler job) is done so far. Without
      this fix, re-enabling the job reproduces the exact same violation. Repo: deployment-service (wave_launcher.py
      application code — distinct file from the todo above). Source:
      `issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` (item 1). ✅
      `deploy@48f55e934b` — `_cme_root_universe()` now consults `MVP_SCOPE` SSOT instead of parsing launcher script's
      hardcoded `CME_ROOTS`. Also fixed pre-existing N806 lint error (`_CELL_KEY`→`_cell_key`).
- [x] [CODE] P3. **Wire `VM_FORCE_WINDOW` into the mtds-backfill branch** of
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (currently silently ignored for every
      mtds-backfill-routed launch — only wired for the generic fallback), or document why it's intentionally scoped only
      to the fallback. Repo: deployment-service. Source:
      `issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` (item 3, line 282). ✅
      `deploy@1dbd6026` — `VM_FORCE_WINDOW` now wired into mtds-backfill branch.
- [x] [SCRIPT] P3. **Widen `check_line_caps.sh`'s scoped-mode carve-out to accept a net-zero-LENGTH content
      substitution**, not just `DELETED=0` — a same-line table-cell substitution always git-diffs as 1 deletion + 1
      addition, never 0 deletions, so the existing carve-out can never fire for this shape of edit even when the net
      line count is unchanged. This blocks routine content edits to any already-over-cap closeout doc (confirmed on 2
      separate closeout docs, tradfi's own and cross-cutting's). Repo: unified-trading-pm,
      `scripts/plan-hygiene/check_line_caps.sh`. Source:
      `issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` (todo 3) +
      `issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`. ✅ `PM@d765b4cfb1` — bounded
      same-line link-repoint carve-out (ADDED≤DELETED, path-normalized content match), per
      /plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md option (a).
- [x] [DATA] P2. **Dry-run a manual catalogue regen + resume both paused tradfi catalogue schedulers.** The durable
      build-time exclusion filter this was gated on ALREADY SHIPPED (`instruments-service@22a5f197`, via the
      cross-cutting tranche's own batch2 — outside this doc's own tradfi covering-doc set, which is why its checkbox
      never got flipped/cited). Confirm the 4 excluded legs (venue=ICE, venue=CBOE AND instrument_type IN
      (OPTION,SPOT_PAIR), 2 VIX-cash INDEX ids) stay excluded on a fresh dry-run regen, then resume
      `lifecycle-catalogue-regen-tradfi-daily` + `lifecycle-catalogue-full-tradfi-weekly` via
      `scheduler_maintenance.py`'s `resume_after_maintenance` (not a raw `gcloud` resume, per the doc's own root-cause
      note on the 2026-06-27 silent-resume incident). Also flip/cite this doc's own stale todo-2 checkbox against
      `instruments-service@22a5f197`. Repo: instruments-service. Source:
      `issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` (todos 2, 3). ✅ Resumed 3 tradfi
      catalogue schedulers: `lifecycle-catalogue-regen-tradfi-daily`, `lifecycle-catalogue-full-tradfi-weekly`,
      `instrument-catalogue-regen-nightly`.

## Deferred — operator-gated (a ruling unblocks these; unchanged, NOT re-asked if already asked)

- **`issues/tradfi_databento_account_billing_suspended_2026_08_09.md`** — operator must pay the outstanding Databento
  bill; vendor restores account-wide access. Gates `data_completion_tradfi_2026_07_15.md` items 4/5/6/9,
  `tradfi_phase_d_terminal_gate_2026_07_24.md`'s P0/P1. **Escalating this prominently in the Phase 2 report** — it has
  sat blocked since 2026-08-09 and gates multiple other orphaned docs' items.
- **`issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`** item 3 (P2-OPERATOR-DECISION) — genuine design
  call on which `canonicalize_raw_tradfi_id` reverse-derivation direction consumers actually need; interim skip-marked
  test, not worker-determinable.
- **`issues/mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md`** — operator must pick option
  (a) CBOE/VIX-scoped carve-out vs (b) leaf-grain re-derivation for CBOE VX-futures `ohlcv_15m`/`24h` aggregation; doc's
  own text: "NOT something a single bounded worker todo should resolve unilaterally."
- **`issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`** item 2 — operator
  sunk-cost-vs-ongoing-violation call on ~~14 out-of-scope NASDAQ/NYSE/CME-new-year VMs (~~$3.50-4.90/hr aggregate SPOT
  burn); already flagged to the operator directly outside this doc.
- **`issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md`** items 5 + 8 — the operator's own 2026-08-07
  ruling ("flip all 8 draft tradfi AO plans," "Option C fold+archive the consolidated closeout") is 2/8 and 0/1
  unexecuted respectively, 3+ consecutive audit cycles (batch6→7→8→9→this pass) without action. This is a genuine
  execution gap, not a fresh decision — **escalated in the Phase 2 report as a big finding**, not silently re-deferred
  again. Item 8 in particular (archiving the very hub doc this audit's own covering-doc set depends on) needs careful
  timing while batch6-9/11 are mid-flight — recommend the operator schedule it explicitly rather than have it land ad
  hoc mid-batch.

## Deferred — conflict-gated (re-triageable once the competing claim resolves)

- **`issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`** todo 1's CME `instrument_id`-format
  verification sub-task — STILL duplicates the open `[DIAG] P2` todo in
  `issues/governance_sweep_deferred_followups_2026_08_06.md` (cross-cutting, unresolved as of this pass — checked live).
  Same conflict batch8 found 2026-08-08; carried forward unresolved through batch9 and this pass. Once that DIAG item
  clears, todo 1's code-change part + dependent todo 2 (relaunch the benchmark) become clean batch12 candidates. **This
  is the SAME underlying gap `data_pipeline_check_mdps_features_2026_07_20.md`'s item 3 (line 767) tracks** — resolving
  one closes both.

## Deferred — time-gated (blocked on upstream, not batchable)

- **`issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`** item 1 — the delta_one
  force+skip proof needs real CAPTURED TRADFI processed_candles data to exist first (upstream MDPS candle backfill gap);
  no batch todo can force data into existence.
- **`issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`** item 2 — the RSS-spike
  recurrence check needs the NEXT post-fix ES_OPT launch to actually happen first (tracked via batch6 todo #2, already
  active); precondition not yet met.

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`data_completion_tradfi_2026_07_15.md`** — 15 open items, several irreversible-delete-gated or BLOCKED-OPERATOR
  (Databento billing). Same verdict batch6/7/8 reached 3 consecutive times; needs its own triage/design pass, not
  cherry-picked extraction.
- **`issues/tradfi_canonical_path_migration_design_2026_07_19.md`** — an 8-step sequenced migration (steps 4-8 open), 2
  of which are explicit `[GATE-operator]` items over a 2.73M-object corpus. Same verdict batch6/7/8 reached 3
  consecutive times.
- **`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`** item 5 — full CME instrument-definitions re-fetch, ~2,368
  days. Flagged 3x across batch6/7/8 as "needs a dedicated design pass," never converted to a todo.
- **`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`** — all 7 items gate on the same underlying MDPS
  `continuous_future` hit-rate data gap (re-tested 79.2% `empty_confirmed` as of batch8's 2026-08-08 re-check, no change
  since). Re-confirmed `orphaned_never_touched` + conflict-gated 3 consecutive times (batch6/7/8); becomes a strong
  candidate the moment the MDPS gap closes as its own project — not drafted speculatively again here.

## Deferred — already in flight / self-dispatched (not batch11 material)

- **`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`** item 1 (the gated DELETE) — sequenced behind this
  batch's own `canonical_twin_path()` fix todo above; its precondition (a fresh 100%-coverage re-run) isn't met until
  that fix ships.
- **`issues/tradfi_backfill_oom_remediation_2026_06_24.md`** — already self-dispatched (`assigned_vm: planning`,
  `status: open`), live in the standing AO backlog independent of any batch wrapper; batch7 already declined to
  duplicate it, same reasoning holds.
- **`issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md`** todo 2 (land the accurate
  "S&P index options" row) — batch6's own open P0 todo already commits to updating the same MVP-cell row, targeting
  final post-backfill numbers rather than this issue's interim text; not duplicated here.
- **`issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`** item 1 — already covered by
  batch6 todo #2 (active, ongoing retry work).

## Deferred — standing/recurring (not a single bounded AO outcome)

- **`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`** — the doc's sole open item is an explicitly
  recurring re-check-every-rollup-cycle loop, not a one-shot task; persists until
  `tradfi_canonical_path_migration_design_2026_07_19.md`'s permanent upstream migration lands. No action needed here.

## Flagged, not batched — cross-tranche ownership

Per `parent_epic`, these docs' genuinely-tradfi-relevant remaining content is not tradfi's to draft into — following the
identical primary-owner precedent batch6/7/8 established for the same docs:

- **`ag_closeout_audit_rollout_2026_07_25.md`** — sole open item's owning tranche resolves to `cefi` (parent_epic
  doesn't map to any of its 5 listed AGs, falls back to `tranches[0]`); tradfi's own historical slice already done.
- **`data_pipeline_check_mdps_features_2026_07_20.md`** items 1-2 (line 193, 319) — generic cross-AG infra work (item 3,
  the tradfi-specific `_resolve_spot_perp` gap, is separately tracked above under conflict-gated).
- **`issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`** item 8 — genuinely tradfi/CME
  content but `parent_epic: instruments_master`, 4-way `asset_group`; flagged not drafted 2x already (batch7/8).
- **`issues/instruments_docs_audit_outstanding_items_2026_07_08.md`** §H — 100% tradfi content but same
  `instruments_master` primary-owner precedent; flagged not drafted 2x already (batch7/8).
- **`issues/instruments_remaining_work_audit_2026_07_10.md`** — a historical-snapshot pointer index; its one
  tradfi-relevant thread routes through `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` below.
- **`issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`** — 4 real tradfi-specific prose bugs (never
  checkboxed), but `parent_epic: instruments_master`, 5-way `asset_group`; flagged not drafted 3x already (batch6/7/8),
  each pass independently live-checking status without adopting it.

## Progress Log

- 2026-08-10 (ag-closeout-audit, tradfi tranche, dispatch agt-022d39, slot 25): drafted, `status: draft`. Phase 1 ran as
  a 52-agent Workflow against the post-tooling-fix candidate list (see `unified-trading-pm@e7ac1ed4e1`,
  `generate_ag_closeout_audit_candidates.py`'s hub-doc exclusion regex fix, found live this same pass). 14 todos
  extracted; conflict-checked against all active tradfi covering docs + the cross-cutting
  `governance_sweep_deferred_followups_2026_08_06.md` conflict — zero new collisions. Not yet reviewed by the operator.
