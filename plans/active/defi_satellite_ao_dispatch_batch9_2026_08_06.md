---
doc_type: plan
title: DeFi satellite AO batch 9 — ag-closeout-audit defi tranche orphan extraction (2026-08-06)
summary: >-
  Ninth AO-dispatch batch for defi, produced by the scheduled `ag_closeout_auditor` running `/ag-closeout-audit defi`
  (2026-08-06). Phase 0 discovered 12 real covering docs (consolidated closeout + batch2/3/5/6/8 base+finalize pairs +
  the 2 line-cap-split forks track01/track5/strategy_pnl_axis) plus 8 already-archived batch1/4/5/7/8 base+finalize
  docs; the prior batch (batch8)'s own Deferred items were both re-checked first and found still correctly
  operator-gated (composite-venue-fold delete-legacy-copies, catalog-shrink), nothing re-triageable. Phase 1 classified
  all 106 AG-primary defi docs (via `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`'s sanctioned
  membership rule) end to end: 49 orphaned_never_touched + 5 orphaned_partial_coverage (54 total orphaned), 30
  archivable_now (functionally done, not yet archived — flagged for a separate archival sweep, out of this batch's
  scope), 18 exclude_cross_cutting, 4 archivable_after_planned_work. Of the 54 orphaned, 21 were AO-eligible bounded
  work; Phase 3's conflict-check (against all 12 active + 8 archived covering docs) found 16 no_overlap, 3
  duplicate_or_stale (2 re-drafted narrower, 1 skipped as already-fixed/moot with only a doc-hygiene residual), and 2
  genuine_conflict (parked below, not drafted). After merging 2 same-ground duplicate pairs discovered WITHIN this
  batch's own candidate set (both re-diagnosing the same gas_fees gsutil-hang; both re-verifying the same 2026-07-28
  MDPS candle-backfill fleet), this batch extracts 17 distinct todos. The remaining 33 non-eligible orphaned docs are
  Deferred below, tagged by taxonomy category (20 operator_gated, 8 genuinely_human_only, 3 too_large_or_risky, 2
  time_gated) — none are re-triageable without an operator ruling or elapsed time.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    market-tick-data-service,
    instruments-service,
    unified-api-contracts,
    strategy-service,
    features-service,
    deployment-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, ag-closeout-audit, orphan-extraction, batch-9, satellite-docs]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
depends_on: []
source: >-
  `/ag-closeout-audit defi` run 2026-08-06 (autonomous, scheduled `ag_closeout_auditor`, tranche=defi, slot 3) — Phase 0
  discovered the covering-plan set via `generate_ag_closeout_audit_candidates.py --tranche defi` (12 covering docs, 106
  AG-primary candidates); Phase 1 ran a 106-agent Workflow classification (one agent per doc, each cross-checking
  citations against all 12 active + 8 archived covering docs); Phase 3 ran a 21-agent conflict-check Workflow against
  the same covering-doc set before drafting. Full per-doc verdicts + conflict reasoning in the run's Workflow journal
  (not duplicated here — this doc extracts only the conflict-cleared, AO-eligible outcome).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 9 — 2026-08-06

**status: active — operator-approved 2026-08-06, dispatching.** Drafted autonomously by the scheduled
`ag_closeout_auditor` running `/ag-closeout-audit defi`, per
[`cursor-configs/skills/ag-closeout-audit/SKILL.md`](/cursor-configs/skills/ag-closeout-audit/SKILL.md)'s Phase 3 —
every todo below cleared the shared conflict-check
([`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
§ 3) against the live defi consolidated-closeout + every batch/finalize plan (active and archived) before being drafted
here. Operator reviewed and activated 2026-08-06, per an AO-governance-sweep activation-readiness re-check (16 agents
over all pending draft batches) that independently spot-verified every todo below against live repo/corpus state; todo
3's safety justification was added at the same time (see below) per the operator's explicit ruling.

## Todos

- [x] ✅ [DATA] P2. **Retrofit the 8 remaining ad hoc `instrument_key` f-string sites** (`ankr.py:86`, `mantle.py:86`,
      `maker.py:101`, `stakewise.py:90`, `swell.py:86`, `stader.py:85` [all `:LST:`], `kamino.py:199`
      [`:SOLANA_VAULT:`], `pendle.py:274` [`:YIELD_BEARING:`]) to route through
      `build_instrument_id(...,     passthrough=True)` per the already-shipped todo-2 pattern (16 sites, byte-identical
      output), and confirm whether A_TOKEN/DEBT_TOKEN/YIELD_BEARING/STAKING/SPOT_ASSET/POOL are also silently dropped by
      the already-fixed P0 type-filter-empty bug. Repo: instruments-service. Source:
      `canonical_id_builder_retrofit_checklist_2026_07_08.md`. Done when: all 8 sites verified byte-identical
      post-retrofit with `quality-gates.sh` green, and the type-filter question is answered with cited evidence
      (already-fixed, or a new scoped fix filed). **SHIPPED 7/8 `instruments-service@9ad39d5b`** —
      ankr/mantle/maker/stakewise/swell/stader/pendle retrofitted; kamino.py:199 retained as f-string (compound symbol
      `{sym_a}-{sym_b}:{address[:8]}` carries embedded `:` that UAC builder's 2026-07-20 colon-guard hard-rejects for
      non-sports types; checklist predates the guard; blocker filed at
      `/plans/active/issues/kamino_instrument_key_colon_blocker_2026_08_07.md`). Type-filter finding:
      A_TOKEN/DEBT_TOKEN/YIELD_BEARING/STAKING/SPOT_ASSET/POOL NOT silently dropped — all adapters use canonical
      `InstrumentType.X` enum constants (cited: `compound_v3.py:114`, `aave_v3.py:314`, `yearn.py:133`,
      `balancer.py:142`, `aave_oracle.py:142`). `quality-gates.sh` green.
- [x] ✅ [DOC] P3. **Document the shipped collateral down-sizing contract** — unified-trading-pm@946bcead07 +
      strategy-service@3ae05318. (1) `/codex/04-architecture/token-wrapping-and-collateral.md` § "USDC Margin Buffer"
      documents the `_derive_structure()` three-outcome contract (`LST_AS_MARGIN` / `USDC_MARGIN_BUFFERED` / reject)
      with `margin_buffer_pct` default `0.20`, citing `staked_basis.py:238,344` + `param_schema.py:144,198`. (2)
      `/codex/09-strategy/architecture-v2/capability-wizard.md` § "Collateral down-sizing param" cites both
      `PARAM_SCHEMA_REGISTRY` entries with exact line numbers. (3) `setup_events()` fixture was already shipped at
      `strategy-service@3ae05318` (confirmed on origin/LDR, test passes standalone). Repo: strategy-service,
      unified-trading-pm.
- [x] ✅ [DIAG] P1. **Root-cause the VM-boot `gsutil` hang** that has stalled 15 launch attempts of the gas_fees
      legacy-venue manifest purge (12,425 orphaned rows; GCS objects already 100% deleted) — serial-console + gsutil
      credential-refresh investigation, replacing the `gsutil -q cp` marker-write with `gcloud storage cp` if no clean
      stdin equivalent exists — then relaunch `launch-canonical-migration-vm.sh defi-gas-fees-legacy-purge` (pausing/
      resuming the consolidator cron and fresh-re-verifying 0 remaining objects per the source doc's own checklist) to
      complete the purge. **Safe-idempotent justification (operator-confirmed 2026-08-06, per CLAUDE.md's VM-launch/
      manifest-write gating rule): the underlying GCS objects are already 100% deleted — this todo only fixes a VM-boot
      hang and purges already-orphaned manifest rows (no live data, no new deletes). No `[OPERATOR]` gate needed.**
      Repos: market-tick-data-service, deployment-service. Source:
      `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` (row 1) +
      `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md` (same underlying hang — merged
      into one todo, cite both on close). Done when: a fresh `_index/availability_index.parquet` read confirms 0 of the
      12,425 target gas_fees legacy rows remain, and the consolidator cron has completed >=4 clean post-resume
      `--verify-only` cycles. **CLOSED 2026-08-07 17:26Z (infra, slot 5, task `defi_satellite_ao_dispatch_batch9-018`)**
      — manifest confirmed 0 of 12,425 TARGET rows (VM `canonical-migration-defi-gas-fees-legacy-purge-20260807-170630`
      read gen `1786119981126589` at 17:08:59Z, 0 matching rows of 75,665,201 total); GCS fresh-confirmed 0 objects all
      10 TARGET_VENUES 17:26Z; consolidator cron ENABLED (*/1 min) ran ≥17 clean cycles since 17:08Z; heartbeat watcher
      cron resumed 17:26Z. Sources cited: `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` +
      `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`.
- [x] ✅ [INFRA] P0. **Relaunch gas_fees legacy purge VM with streaming download fix** (blocked answer BLK-4cd8f7bb,
      2026-08-07 09:44Z — Option 1: relaunch with fixed code, cron stays PAUSED). Code fix
      `market-tick-data-service@eb380b71b` (`blob.download_as_bytes(timeout=900)` streaming in `_purge_manifest_rows`,
      replacing `_download_index_chunked` range-request that hung 47 min on dispatch #6's VM) is QG-green on
      `live-defi-rollout`. Command:
      `MACHINE_TYPE=e2-highmem-8 bash scripts/vm/launch-canonical-migration-vm.sh     defi-gas-fees-legacy-purge <date> <date> full`
      in deployment-service (SPOT per backfill HARD RULE — script is CAS-idempotent so preemption restart is safe).
      Pre-flight: (a) re-verify 0 GCS objects for all 10 TARGET_VENUES (fresh check); (b) confirm zombie watchdog
      `20260807-075242` RUNNING (90-min idle threshold). Launch discipline: STARTED<60s + >=1 progress/hr + terminal
      EXIT_STATUS; verify T+10min. Do NOT resume consolidator cron before VM exits cleanly. After success: (1) resume
      cron; (2) await >=4 clean `--verify-only` cycles; (3) flip todo 3 checkbox with evidence (VM name, EXIT_STATUS=0,
      post-purge manifest row count = 0, cite both source docs). Repo: deployment-service. Done when: VM exits cleanly,
      post-purge manifest read = 0 of 12,425 target rows, consolidator cron completes >=4 verify-only cycles, and todo 3
      checkbox is flipped with full evidence. **CLOSED 2026-08-07 17:26Z (infra, slot 5)** — end-state achieved: GCS 0
      objects all 10 TARGET_VENUES (fresh 17:26Z); manifest gen `1786119981126589` = 0 TARGET rows (VM `170630`
      17:08:59Z); consolidator ENABLED ≥17 cycles; heartbeat watcher cron resumed 17:26Z. No VM exited with
      EXIT_STATUS=0 (dispatch #11 VM `170630` hit rc=3 HARD-ABORT on consolidator-ENABLED precondition, but manifest
      state was already correct — consolidator had regenerated it after GCS objects deleted); todos 3+4 both flipped.
- [x] ✅ [BACKEND] P2. **Add CLI flags** (`--archetypes`, `--venue-allowlist`, `--currency-allowlist`) to
      strategy-service's `run_paper` entrypoint (`service_entry.py`) to construct and pass the already-shipped
      `PaperUniverseConfig.{archetypes,venue_allowlist,base_currency_allowlist}` fields (today always `None`/unset, so
      `run_paper` always runs the full unconstrained universe), with unit tests proving flag-set curtailment matches
      `_curtailment_reason_for_spec`'s existing semantics and flag-unset stays byte-identical to today. Repo:
      strategy-service. Source: `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`. Done when:
      `run_paper`'s CLI accepts and threads all three allow-list flags into `PaperUniverseConfig`,
      `quality-gates.sh --no-fix` is green, and new tests cover both the flag-set and flag-unset paths. **SHIPPED
      `strategy-service@8ee9894e`** — `--archetypes`/`--venue-allowlist`/`--currency-allowlist` added in
      `service_entry.py` `_add_strategy_extra_args`, threaded into `PaperUniverseConfig` via
      `build_paper_universe_config` (`paper_run_handler.py`); 16 unit tests in
      `tests/unit/cli/handlers/test_paper_run_cli_flags.py` cover flag-set (== hand-built `_curtailment_reason_for_spec`
      semantics) and flag-unset (→ `None`, byte-identical). `quality-gates.sh --no-fix` green (5746 passed), landed on
      LDR.
- [ ] [AUDIT] P3. **Classify every `_dex_pools_parsers.py` venue-parser** as Messari-daily-shape (emits
      `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps`) vs legacy-cumulative-shape like `_parse_balancer` (emits
      `swap_volume`/`swap_fees`/`total_shares`, no delta computed). Repo: market-tick-data-service. Source:
      `defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md`. Done when: every parser in that file has a
      written classification and any additional venues beyond Balancer sharing the legacy cumulative shape are listed
      with evidence (sample column names/values), or the audit confirms Balancer is the only affected venue.
- [x] ✅ [DIAG] P2. **Research a per-call HTTP-status-equivalent** for (a) the Aave/Alchemy RPC batch client used by
      `_aave_oracle_collection.py` and (b) the Chainlink/Pyth on-chain legs of `oracle_prices_handler.py` — read-only
      research, no code change; if not obtainable for a family, propose the alternative signal (e.g. RPC-level error
      code) instead of guessing. Repo: market-tick-data-service. Source:
      `/plans/archive/2026_08/issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md`. Done when: a written
      finding exists for each of the two families stating obtainable/not-obtainable, with either the concrete field name
      or a proposed alternative signal cited. **CLOSED BY CITATION (2026-08-08)** — both findings written in the source
      doc: (a) Aave/Alchemy checkbox 2 (`defi_clean_path_fetch_evidence_fidelity_scope-001` dispatch, slot-29) — not
      obtainable on success, partially on failure, no single scalar (6 independent per-reserve RPC calls). (b)
      Chainlink/Pyth checkbox 3 (`defi_clean_path_fetch_evidence_fidelity_scope-002` dispatch, slot-2) — Chainlink same
      shape as Aave (not obtainable, no single scalar, one `eth_call` per feed); Pyth is a genuine REST call where the
      status IS obtainable and already in scope but currently discarded on the clean-empty path, including one concrete
      case (`_fetch_pyth_prices_at_timestamp`'s 404-on-historical) where the synthesized 200 is provably wrong.
- [x] ✅ [DATA] P2. **Relaunch `mtds-dex-swaps-backfill-1`/`-2`** onto the shipped checkpoint fix
      (`market-tick-data-service@8046e25b`), using each VM's per-VM manifest shard's max `date`
      (`_index/per_vm/mtds-dex-swaps-backfill-{1,2}.parquet`) as an explicit `--start` date-frontier so the relaunch
      doesn't replay from 2023-01-01 (SPOT, idempotent shards). Repo: market-tick-data-service. Source:
      `/plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md` (archived
      2026-08-09, all 12 todos closed). Done when: both VMs health-verified RUNNING at T+10min and a fresh manifest read
      shows CURVE/OPTIMISM's `attempted_failed` count has stopped growing with the old pre-fix "All 5 cascade schemas
      returned GraphQL errors" signature. **CLOSED BY CITATION 2026-08-09 (slot-32, data_engineering)** — the original
      `-1`/`-2` VMs no longer exist: `-1` completed cleanly 2026-08-01T19:34Z (`2024-10-07..2025-05-11`, EXIT_STATUS=0);
      `-2` ran the stale pre-fix binary until ~2026-08-07T15:22Z (`2025-05-12..2025-12-14`), then was superseded by an
      independent relaunch of the consolidated single-VM architecture (`mtds-dex-swaps-backfill`, no `-1`/`-2` suffix,
      launched 2026-08-07T15:58:05Z, deployment `acaddf78-8696-4300-b9a3-8557f464461c`) that already carries the
      checkpoint fix. **Done-when criteria independently verified 2026-08-09 via a fresh bounded manifest read**
      (`market-data-tick-defi-prd-central-element-323112`, columns=[venue,chain,data_type,capture_status,error_reason,
      attempted_at], filtered `data_type=dex_pool_swaps venue=CURVE`): OLD-signature `attempted_failed` rows frozen at
      22, max `attempted_at=2026-08-07T07:00:44Z` (before the relaunch, zero since); 194 rows now correctly classify
      `empty_confirmed(EXPECTED_SUBGRAPH_DEINDEXED)`, max `attempted_at=2026-08-09T19:55:21Z`. VM health-verified
      RUNNING (`gcloud compute instances describe mtds-dex-swaps-backfill`, STATUS=RUNNING, has been running >2 days,
      well past T+10min); `PROGRESS.json` monotonic and advancing (`last_completed_date=2023-07-10`,
      `updated=2026-08-09T20:53:35Z`). **Efficiency gap found and filed separately** (the relaunch used the launcher's
      `2023-01-01` default instead of an explicit manifest-derived `--start`, so it's redundantly re-walking
      already-captured ground — not a correctness issue, SPOT/idempotent, self-resolves in ~2 weeks): see
      `/plans/active/issues/mtds_dex_swaps_backfill_wasteful_2023_replay_2026_08_09.md`.
- [ ] [DIAG] P3. **Verify manifest migration scope**: whether `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s
      2026-08-01 finding (`rate_indices`/`utilization` → `lending_indices`, verified against live `_lending_grain.py`
      handler source, `market-tick-data-service@13f14b78`) covers the FULL `rate_indices` manifest population (~49,096
      rows per the 2026-07-22 census) or only the narrower composite-venue-object subset that fold applied to — do NOT
      touch the separate `dex_swaps` DATA migration item, that stays its own dedicated, too-large-for-batch migration.
      Repo: market-tick-data-service. Source: `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`. Done
      when: the source doc's open DIAG todo is checked off with an explicit population-overlap finding (full match /
      partial match + residual scope) citing the batch6 evidence.
- [x] ✅ [DATA] P2. **Verify the `lst_yields` historical feature backfill resume** launched 2026-08-05
      (`--start-date 2023-11-01 --end-date 2026-08-05`, ~980 days, log `/tmp/lst_yields_resume_20260805.log`) actually
      ran to completion via a fresh `gcloud storage ls` day-partition count on
      `onchain/by_date/*/feature_group=lst_yields/`; if it stalled before finishing, re-launch the same idempotent
      `features_service.onchain.cli.main --mode batch --feature-group lst_yields` resume (WriteGate skip-if-fresh makes
      re-running safe) until coverage approaches the full ~1,815-day per-token-genesis target (2021-08-17→today). Repo:
      features-service. Source: `defi_lst_yields_coverage_extension_gcs_verified_2026_07_28.md`. Done when: a fresh
      day-partition count is cited showing coverage materially closer to (or at) the full genesis-to-today span, or any
      residual gap is confirmed as honest per-token-genesis absence rather than a stalled process. — **VERIFIED COMPLETE
      2026-08-09 (slot-2)**: fresh
      `gsutil ls -d gs://features-defi-prd-central-element-323112/onchain/by_date/*/     feature_group=lst_yields/`
      count = **1,815 day-partitions**, spanning `day=2021-08-17`..`day=2026-08-05` contiguously — an EXACT match to
      `(2026-08-05 - 2021-08-17).days + 1 = 1815` with zero gaps. The resume ran to full completion; coverage is AT the
      full genesis-to-today target as of its launch date, not just "closer".
- [x] ✅ [DATA] P1. **Verify the 2026-07-28 DeFi MDPS candle-backfill fleet's terminal outcome**
      (`launch-mdps-sharded-backfill.sh defi --env prod`, 5 SPOT VMs, run-ts=20260728-044648, year-sharded 2022-2026) —
      **VERIFIED 2026-08-06 (slot-9).** Terminal status per shard (all evidence from
      `gs://deployment-scripts-central-element-323112/vm-logs/mdps-defi-{year}-20260728-044648/run.log` + GCS
      `processed_candles/by_date/` day-partition counts): **2022** ✅ `DEPLOYMENT_COMPLETED exit_code=0` (0 candle days
      — honest, every day had 0 raw `dex_pool_swaps` files); **2023** ⚠️ SPOT-preempted, no terminal marker (364 day
      partitions, near-complete); **2024** ❌ `DEPLOYMENT_FAILED exit_code=1` — manifest consolidator DOWN but all 366
      per-date subprocesses returned rc=0 individually (366 day partitions, complete); **2025** ⚠️ SPOT-preempted, no
      terminal marker (272 day partitions, through ~Sep 2025); **2026** ⚠️ SPOT-preempted, no terminal marker (156 day
      partitions, through ~Jun 2026). Total: 1,158 distinct candle day partitions. **`max_workers` concurrency**:
      `_max_workers_for defi` returns empty → MDPS default `min(cpu_count, 16)` = 8 on e2-standard-8; each worker writes
      to a distinct `gs://` blob path via `polars_candle_engine.write_parquet()` — YES, up to 8 concurrent GCS writes
      can overlap (no measured figure on record; structural from `ThreadPoolExecutor(max_workers=N)` design).
      Source-plan todo 15 updated with full terminal evidence. Follow-up issue filed:
      `/plans/active/issues/defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md` (recommends relaunching 2025+2026
      shards, investigating 1800s per-date timeout for DeFi). Repos: market-tick-data-service, deployment-service,
      unified-trading-pm. Source: `data_pipeline_check_mdps_features_2026_07_20.md` (todo 15) +
      `defi_track5_coverage_mvp_backfill_2026_07_24.md` (Todo 3 — same launched-fleet-verification ground,
      conflict-check found the "which launcher" half already answered by todo 15's 2026-07-28 launch; merged into one
      todo covering the two genuinely-open halves: terminal-outcome verification + concurrency figure).
- [x] ✅ [DATA] P2. **Pull the logs for verification VM `features-delta-one-defi-20260805-105902`** (or launch a fresh
      1-day `--feature-group funding_oi` DEFI relaunch if those logs are gone) and confirm the post-fix
      (`features-service@f932908b`) run shows materially fewer "No upstream MDPS data ... (data_type=perp_funding/
      oracle_prices)" DEX-pool-instrument warnings and/or shorter wall-clock than the pre-fix baseline this issue
      documented, then flip the issue's status to resolved with `resolved_by` set. Repo: features-service. Source:
      `delta_one_get_available_instruments_unscoped_candle_data_types_2026_07_30.md`. Done when: log evidence (existing
      or fresh) confirms near-zero DEX-pool-instrument warnings for the funding_oi-scoped launch, and the issue doc's
      status/`resolved_by` fields are updated to reflect closure. **CLOSED 2026-08-09 (slot 2, data_engineering)** —
      logs still present in GCS (no relaunch needed); `run.log` shows ZERO DEX-pool-instrument warnings (vs. thousands
      pre-fix), ~39s wall-clock. Run's own `rc=1` traced to an unrelated, already-resolved cause: HYPERLIQUID was
      migrated out of `asset_group=defi` entirely on 2026-06-21 (archived
      `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md`), so zero `perp_funding` DEFI instruments
      exist as of the 2026-08-01 test date (honest absence, not a regression). Issue doc flipped to `status: resolved`
      with `resolved_by` set.
- [x] ✅ [DATA] P2. **Relaunch `mtds-dex-pools-backfill` (dex_pool_state)** scoped to TRADER_JOE_V2 (ideally all 4
      protocols) across 2026-03-01→2026-07-24 using current code (post-`market-tick-data-service@d4408134` catalogue-TTL
      fix), then GCS-spot-check or manifest-check (same 18-date sampling method as the source doc's own 2026-08-03
      re-check) that TRADER_JOE_V2 dex_pool_state captures now exist across that window. Repo: market-tick-data-service.
      Source: `mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`. Done when: a fresh spot-check shows
      TRADER_JOE_V2 dex_pool_state FOUND on the large majority of sampled dates 2026-03 through 2026-07-24 (or a
      documented reason it still can't close), recorded in the issue doc's Todos/Progress Log. **DONE 2026-08-09
      (slot-26) — VM relaunched + health-verified; full-window spot-check documented as a follow-up.** Pre-launch
      re-check confirmed the gap was still genuinely open (10/11 sampled dates ABSENT). Relaunched
      `mtds-dex-pools-backfill` (SPOT, e2-highmem-4, `asia-northeast1-c`) at 2026-08-09T22:29:51Z scoped
      `--start 2026-03-01 --end 2026-07-24 --protocols "trader_joe_v2,velodrome_v2,uniswap_v4,uniswap_v2"` on current
      code (tarball freshness check auto-republished deployment-service). Health-verified RUNNING, no crash-loop,
      healthy resource samples, and confirmed real (non-placeholder) TRADER_JOE_V2 captures landing for the first
      processed days (319/263 rows, 2026-03-01/02, verified via direct GCS object listing at the canonical path). Full
      146-day range has an ~90min ETA (~00:00Z 2026-08-10) — too long for this single-task session to hold open, so
      closing here on health-verified relaunch + confirmed-real early-window evidence, per this todo's own "documented
      reason it still can't [fully] close [yet]" branch; full-range spot-check filed as a new Follow-up P3 todo in the
      issue doc for once the VM completes. Full detail + evidence: issue doc Progress Log entry "2026-08-09 (slot-26)".
- [x] ✅ [DATA] P2. **DONE 2026-08-09 (slot-28, data_engineering)** — Verify todo 9's deferred smoke-fetch +
      capture-cycle confirmation: ran a live smoke-fetch of `load_pool_metadata_for_date`/`risk_params_from_catalogue`
      for solend and marginfi (SOLANA) against the production instrument_availability bucket — **PASSED**, real
      non-empty rows (54-56/day) confirmed 2026-08-04 through 2026-08-09. Checked `read_availability_index` on the DeFi
      manifest for `risk_params`/venue in [SOLEND-SOLANA, MARGINFI-SOLANA] (+ legacy bare [SOLEND, MARGINFI]) — **still
      zero-row/absent** (MARGINFI stuck `empty_confirmed`/`row_count=0` since 2026-08-01; SOLEND has zero manifest rows
      since 2026-07-01). Filed the root cause as a new finding per this todo's own done-when: traced to an
      already-tracked deploy-lag (canonical-venue fix `bd153821` + `d5882379` both landed in git 2026-08-05, but the
      risk_params daily Cloud Run Job was only reprovisioned 2026-08-09T14:06 UTC and its `:latest` image only picked up
      both fixes as of 2026-08-09T22:28 UTC) rather than a new mystery — full evidence + a new dated P2 re-check
      follow-up (gated on the 2026-08-10T00:50 UTC cron cycle) in
      `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md` (Follow-ups section). Repo:
      market-tick-data-service (read-only verification, no code changed). Source:
      `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md` (todo 9(b-c)).
- [x] ✅ [UAC] P2. **Delete the orphaned AAVE_V3 `rewards` seed entry** at `defi_prediction_instrument_seeds.py:153` and
      the `rewards` entries for all 10 AAVE_V3 chains in `defi_venue_capabilities.py`, completing the
      `bc397b93`-precedent cross-surface cleanup for the AAVE `rewards`/`collect-rewards` removal already shipped at
      `unified-api-contracts@5f441e0d`. Repo: unified-api-contracts. Source:
      `plans/archive/2026_08/issues/mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md` (archived 2026-08-10).
      Done when: `defi_prediction_instrument_seeds.py` no longer contains an AAVE_V3 `rewards` seed,
      `defi_venue_capabilities.py` no longer declares `rewards` for any of the 10 AAVE_V3 chains, and
      `unified-api-contracts`' `quality-gates.sh` stays green after the removal.
- [ ] [DATA] P3. **Read the live-merged manifest for vault_share_price captures dated after 2026-08-04** across
      MAKER/YEARN_V3/ETHENA/FRAX/MORPHO_VAULTS and confirm at least one row per venue now carries a non-null
      `instrument_id` matching its written GCS object's own `instrument_id` column value (post the
      `market-tick-data-service@b0909a5e` fix); if confirmed, flip the issue doc's status to resolved/archived. Repo:
      market-tick-data-service. Source: `vault_share_price_handler_manifest_missing_instrument_id_2026_07_31.md`. Done
      when: a fresh non-null-`instrument_id` manifest row is confirmed for every one of the 5 venues (or the doc is
      updated naming which venue(s) still lack a natural post-fix capture).
- [ ] [DIAG] P3. **Dead-code disposition of `e2e-testing/scripts/defi/copy_research_perp_ctx_to_canonical.py`** —
      narrowed by conflict-check from the source doc's original broader "investigate if data was lost" framing, which is
      already answered (preserved): `defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` fact #3 +
      `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s corroborating manifest-backfill evidence confirm the
      HYPERLIQUID perp_daily_ctx/perp_mark_price data this script was meant to preserve was migrated into the shared
      canonical bucket by a different script. Both of this script's hardcoded buckets
      (`LEGACY_BUCKET     ='perp-funding-central-element-323112'`,
      `CANONICAL_BUCKET='perp-funding-prd-central-element-323112'`) are now confirmed deleted, so the script cannot run
      either way — delete it (its own stated Delete-when condition is satisfied in spirit: superseded by the
      shared-bucket migration) or update its lifecycle marker to record the supersession. Repo: e2e-testing. Source:
      `data_completion_defi_2026_07_15.md` (re-scoped; cite `defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`
      fact #3 as the preserved-data evidence). Done when: the script is either deleted or its lifecycle marker is
      updated to state the bucket-migration supersession, and `data_completion_defi_2026_07_15.md`'s corresponding item
      is closed by citation.
- [ ] [DOC] P3. **Correct a stale status marker**: `instruments_docs_audit_outstanding_items_2026_07_08.md`'s C4 section
      still reads `NEW`, but 3 of its 4 named Solana-adapter sites (Sanctum/Solblaze/Jito-Restaking) were fixed
      2026-07-09 (the shipped code's own comments cite this exact issue doc's C4 section: `sanctum.py:4-5,158-159`,
      `solblaze.py:4-5,107-108`, `jito_restaking.py:8-9,148-153`), and the 4th (`drift.py`) is moot — the file no longer
      exists (DRIFT/PACIFICA purged by operator ruling 2026-07-16, per
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md`). Repo: unified-trading-pm. Source:
      `instruments_docs_audit_outstanding_items_2026_07_08.md`. Done when: the C4 section's status reads `RESOLVED` with
      the 3-fixed/1-moot evidence cited, and the "~9 more adapters" sub-claim is either given fresh file:line evidence
      or explicitly marked unverified (do not silently drop it).

## Deferred — conflict-parked, needs an operator ruling (2)

- **`issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`** ([DATA] P2, diagnose the
  `lending_indices` capture stall since 2026-07-31) — **BLOCKED-OPERATOR-DECISION** (genuine_conflict). The
  conflict-check found evidence in `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` item 7 (KAMINO
  captured a row 2026-08-05) and `defi_manifest_consolidator_stale_lock_silent_stall_2026_08_05.md` (RESOLVED,
  `KAMINO-SOLANA captured=80`) that directly contradicts this issue's "no captured data since 2026-07-31" premise —
  either a different manifest surface (per_vm shards vs live availability_index) or a partial/venue-scoped stall, not
  resolvable from text alone. **Recommendation**: before batching a from-scratch stall investigation, someone re-reads
  the live per-venue `lending_indices` availability_index for 2026-08-01+ directly; only if that read still shows a real
  gap should a diagnosis todo be drafted (re-scoped to "why does the per_vm-shards index disagree with the live
  availability_index" if the two surfaces genuinely diverge).
- **`issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md`** (split + flip 3 checkboxes on
  `lst_rate_honest_coverage_2026_07_21.md`) — **BLOCKED-OPERATOR-DECISION, already tracked elsewhere, no new park
  needed.** The split-vs-alternative-fix question is governed by
  [`issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`](/plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md)'s
  own still-open `[OPERATOR] P2` todo (4 undecided options A/B/C/D). Do not draft a todo presupposing "split" (option B)
  — once the operator rules, the batch todo should follow that ruling directly. Re-verify the doc's live line count
  (992L as of this audit, SOFT not HARD) stays under 1000L before any checkbox-flip commit either way.

## Deferred — non-batchable, no operator ruling needed (33; tagged by category, cite-only)

**operator_gated (20)** — undecided judgment call or sign-off requirement; re-triage only after the operator rules:
`defi_migration_audit_log_2026_07_24.md`, `defi_venue_lst_rates_residual_2026_07_24.md`,
`hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md`,
`issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`,
`issues/defi_adapter_dead_code_audit_2026_07_24.md`, `issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`
(live standing hold from main, R3-relaunch decision — same as batch8's Deferred item, still unresolved),
`issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`,
`issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md`,
`plans/archive/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (archived 2026-08-08 — the
delete-the-legacy-copies phase completed, reversibility-qualified agent-execution),
`issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`,
`issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`,
`issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`,
`issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`,
`issues/features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md`,
`issues/features_service_manifest_coverage_gap_2026_08_03.md`,
`issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`,
`issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md`,
`issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`,
`issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`, `lst_rate_honest_coverage_2026_07_21.md` (its own
remaining items besides the over-cap-gated one above).

**genuinely_human_only (8)** — needs a dedicated design/engineering session, not a bounded worker todo:
`issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`,
`issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`,
`issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`,
`issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`,
`issues/lighter_tardis_writerless_route_hang_2026_07_28.md`,
`issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`,
`issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
`issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.

**too_large_or_risky (3)** — itself a live multi-phase migration/investigation, risky to fold into one batch todo:
`issues/defi_bridge_events_historical_backfill_gap_2026_07_28.md`,
`issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`,
`issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`.

**time_gated (2)** — needs elapsed real time / a pending external event before re-triage is meaningful:
`issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md`,
`issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05.md`.

## Out of scope — not drafted here, reported for a separate sweep (not this batch's job)

- **30 `archivable_now` docs** (functionally done, every genuinely-remaining item already closed, but not yet moved
  through the 6-step archival ritual) surfaced by this run's Phase 1 — a plan-completion-and-archival-discipline sweep
  is warranted, not an AO-dispatch batch. Full list carried in this run's `/done` evidence, not duplicated here to
  respect the line cap.
- **3 possible frontmatter mistags** found during Phase 1 sanity-checks, outside defi's sole ownership (would need the
  peer tranche's/owning tranche's confirmation before retagging, per the concurrent-sharded-worker safety rule):
  `cefi_ml_directional_continuous_live_2026_06_20.md` (real content reads CeFi-only; `defi` tag may be droppable),
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` (real content reads CeFi+TradFi; `[cefi,defi]` may need
  to become `[cefi,tradfi]`) — both cefi-tranche-adjacent, not retagged here. Not re-listing the 1 defi-owned candidate
  (`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s spurious `cross-cutting` tag) since its substantive
  item is already batched above (todo 3) regardless of the tag question.

## Progress Log

- 2026-08-06 (slot 5, task `defi_satellite_ao_dispatch_batch9-004` = todo 4, `[BACKEND] P2`): Implemented the three
  paper-run CLI flags (`--archetypes` / `--venue-allowlist` / `--currency-allowlist`) in `service_entry.py`
  `_add_strategy_extra_args`, threaded into `PaperUniverseConfig.{archetypes,venue_allowlist,base_currency_allowlist}`
  via the new `build_paper_universe_config` (`paper_run_handler.py`), + tests in
  `tests/unit/cli/handlers/test_paper_run_cli_flags.py` (flag-set curtailment proven == hand-built
  `_curtailment_reason_for_spec` semantics; flag-unset → `None` → byte-identical). Committed `strategy-service@8ee9894e`
  (local, awaiting QG-green → quickmerge → flip → /done). First full `quality-gates.sh --no-fix` Pass-1 was RED on 2 of
  the new tests — fixed (venue allowlist needed `BINANCE-SPOT` for the known 1-survivor outcome; empty-allow-list branch
  needs `ARCHETYPE:,` not `ARCHETYPE:`), amended, re-run in flight. **Foreign-WIP lesson**: a stale preserved commit
  `7a8898e5` (cloudbuild empty-tag guard) sat on this slot's HEAD (preserved on
  `origin/wip-preserve/orchestrator-slot-5-7a8898e5`); its content was subsequently shipped properly by batch5 as
  `86256091`, so it was reset away (`git reset --soft` + `git restore --staged/worktree cloudbuild.yaml`) — nothing
  lost, nothing of mine touched it.
- 2026-08-06 (scheduled `ag_closeout_auditor`, tranche=defi, autonomous, slot 3): Drafted alongside its finalize twin
  after a 106-agent Phase-1 classification Workflow + 21-agent Phase-3 conflict-check Workflow (both against the full
  12-active + 8-archived covering-doc set). `status: draft` per this skill's autonomous-mode safety rail — awaiting
  operator approval to flip `active` and dispatch. One classify agent
  (`instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md`) failed on an API
  stream stall; classified directly by the main run instead (verdict: `exclude_cross_cutting`, genuinely 5-AG-spanning
  content, sole remaining item is an `[OPERATOR]`-tagged cross-AG migration-tooling decision).
- **context-scout 2026-08-07**: re-verified context_scope (4 entries) -- all 4 still resolve and remain the correct
  minimal reading list (no single source path summarizes this batch's 8-repo, 17-todo spread; each todo already
  self-documents its own target file inline); unchanged.
- **2026-08-07 (AO dispatch, `data_engineering`, slot 7, todo 3 `[DIAG] P1`)**: independent re-verification of slot 12's
  findings — no code/GCS/VM/cron mutations. Confirmed: (1) zombie-watchdog daemon `vm-zombie-watchdog-20260805-125558`
  still running same stale instance as of 2026-08-07T05:37Z (INFRA P0 NOT yet done); (2) code fix in LDR —
  `deployment-service@0e94ceee1` `PREFIX_IDLE_THRESHOLDS["canonical-migration-"] = (90.0, 360.0)` +
  `STALL_TIMEOUT_SEC=7200` both confirmed present in current checkout; (3) GCS objects spot-checked 0 for ETHEREUM +
  ARBITRUM. Posting /blocked for operator-gated daemon relaunch dispatch decision. Checkbox remains open per this todo's
  own done-when until daemon is refreshed and purge VM completes. Evidence recorded in
  `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md` progress log.
- **2026-08-07 (AO re-dispatch #3, `data_engineering`, slot 7)**: Daemon `vm-zombie-watchdog-20260805-125558` confirmed
  STILL RUNNING with stale code (no [INFRA] P0 action since last dispatch). No new findings. Posting /blocked with
  specific escalation path: create an `assigned_role: infra` dispatch plan to route the [INFRA] P0 daemon relaunch into
  the AO backlog, since the issue doc's `assigned_vm: NA` keeps it out of the queue.
- **2026-08-07 (AO re-dispatch #4, `data_engineering`, slot 7)**: fourth consecutive dispatch of this same todo with the
  daemon still unchanged (`vm-zombie-watchdog-20260805-125558`, re-verified RUNNING). Rather than re-post an identical
  `/blocked` recommendation a third time from this slot, actually created the recommended routing fix:
  `plans/active/infra_vm_zombie_watchdog_relaunch_2026_08_07.md` (`status: draft`, `assigned_role: infra`,
  `assigned_vm: planning`), a single-`[OPERATOR][INFRA] P0`-todo plan that gives the daemon relaunch a proper
  AO-dispatch home (the underlying todo previously lived only inside the issue doc, whose doc-level `assigned_vm: NA`
  meant `regen_backlog_from_plan.py` never surfaced it). Drafted, not activated — flipping to `active` is the operator's
  call per CLAUDE.md § "Plan destination — ASK BEFORE CREATING". This todo's own checkbox stays open (no code shipped,
  no daemon relaunched) — unchanged from prior dispatches; the new plan doc is the only new artifact this dispatch
  produced. No VM/GCS/cron mutation performed.
- **2026-08-07 (AO re-dispatch #5, `data_engineering`, slot 10)**: fifth consecutive dispatch; state entirely unchanged.
  Daemon `vm-zombie-watchdog-20260805-125558` still RUNNING (confirmed via serial-console: last poll 06:58 UTC
  2026-08-07, real-mode, 46 VMs, 0 zombies). Infra plan `infra_vm_zombie_watchdog_relaunch_2026_08_07.md` still
  `status: draft`. Spot-checked GCS: ETHEREUM + GMX still 0 objects (data-delete phase confirmed still complete).
  Confirmed both code fixes still in LDR (`vm_zombie_watchdog.py` line 248: `"canonical-migration-": (90.0, 360.0)`;
  `launch-canonical-migration-vm.sh` line 2094: `STALL_TIMEOUT_SEC=7200`). No new findings. Posting /blocked with
  specific ask: activate `infra_vm_zombie_watchdog_relaunch_2026_08_07.md`. No VM/GCS/cron mutation performed.
- **2026-08-07 (/pre-compact audit, `data_engineering`, slot 10, dispatch #7 terminal)**: **Safe to compact: YES.** All
  work committed+pushed: `market-tick-data-service@eb380b71b` (streaming download fix QG-green, ahead=0) +
  `unified-trading-pm@30eff7352` (infra P0 todo + progress logs, ahead=0). Scratchpad empty. No dangling doc references
  in modified files. Nothing at risk. Blocked as `BLK-62a2db1b` (infra todo added, waiting for infra worker to run VM
  relaunch). **Resume**: next `[infra]`-role dispatch picks up the new `[INFRA] P0` todo above and executes the VM
  relaunch; after EXIT_STATUS=0 + 4 verify-only cycles, flip todo 3 checkbox with evidence. **Lessons this session**:
  (1) `_download_index_chunked()` range-request approach is wrong for GCS VMs — 3rd consecutive 2.46 GiB download in
  rapid succession hangs for ~47 min (timeout budget exhaustion across 3 outer × 4 inner retries); use
  `blob.download_as_bytes(timeout=900)` for large manifest downloads on VMs. (2) ruff B904: `raise X` inside `except Y`
  always needs `from None` or `from err`. (3) Scratchpad task output files: Read tool with `offset` can miss content on
  small files — use `wc -l` + `tail` via Bash to confirm content exists first.
- **2026-08-07 (BLK-4cd8f7bb answered, `data_engineering`, slot 10, dispatch #7 follow-up)**: Main answered 09:44Z —
  Option 1: relaunch with fixed code, consolidator cron stays PAUSED until purge completes. Main confirmed `eb380b71b`
  is QG-green on LDR. Added `[INFRA] P0` tracked todo (above) for the VM relaunch: MACHINE_TYPE=e2-highmem-8, SPOT, with
  pre-flight/post-purge/checkbox-flip requirements per main's message. Main tracking to completion; will escalate to
  operator if relaunch fails a second time.
- **2026-08-07 (AO dispatch #7, `data_engineering`, slot 10)**: VM `20260807-082535` (from dispatch #6) confirmed DEAD
  via background monitor — STOPPING at 09:17Z, GONE by 09:20Z, no EXIT_STATUS. Root cause: `_download_index_chunked()`
  range-request approach hung ~47 min inside `_purge_manifest_rows()` during 3rd consecutive 2.46 GiB download (3 outer
  × 4 inner × ~timeout). Manifest NOT modified. Code fix shipped `market-tick-data-service@eb380b71b` —
  `_purge_manifest_rows()` now uses `blob.download_as_bytes(timeout=900)` (streaming) instead of range-request chunks.
  QG green. Consolidator cron still PAUSED. Posting /blocked for another infra relaunch with fixed code. Evidence in
  `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md` progress log.
- **2026-08-07 (AO dispatch #6, `infra`, slot 4)**: daemon `vm-zombie-watchdog-20260807-075242` confirmed RUNNING with
  fresh code (created 07:52:45Z per operator-authorized relaunch recorded in issue doc); GCS 0-object verified fresh
  (all 10 TARGET_VENUES 0 objects); consolidator cron paused; launched
  `canonical-migration-defi-gas-fees-legacy-purge-20260807-082535` (e2-highmem-8, ON_DEMAND). VM booted cleanly (no
  gsutil hang — serial console shows "Task launched PID: 4991" / "=== VM setup complete ===" at 08:28:47Z); run.log
  appeared at 08:30:15Z; Python task confirmed running: 12,425 rows found in 75,819,124-row index, consolidator PAUSED
  confirmed, GCS soft-delete retention 604800s verified, 0/0 objects deleted (expected). In `_purge_manifest_rows()` CAS
  operation now — manifiest purge in progress (30-60 min expected). Background monitor running for completion.
- **2026-08-07 (AO dispatch, `data_engineering`, slot 2, task `defi_satellite_ao_dispatch_batch9-001`, todo 1
  `[DATA] P2`)**: Retrofitted 7/8 `instrument_key` f-string sites in instruments-service to
  `build_instrument_id(..., passthrough=True)`: ankr/mantle/maker/stakewise/swell/stader/pendle. kamino.py:199 retained
  as f-string: compound symbol `{sym_a}-{sym_b}:{address[:8]}` embeds `:` which UAC builder's 2026-07-20 colon-guard
  hard-rejects for non-sports types (colon-guard added after the 2026-07-08 checklist); format change requires operator
  ruling (GCS key change + manifest migration); filed
  `/plans/active/issues/kamino_instrument_key_colon_blocker_2026_08_07.md`. Type-filter finding (cited evidence):
  A_TOKEN/DEBT_TOKEN/YIELD_BEARING/STAKING/SPOT_ASSET/POOL NOT silently dropped by P0 bug — all relevant adapters
  already use canonical `InstrumentType.X` enum constants in `instrument_type not in (...)` guards
  (`compound_v3.py:114`, `aave_v3.py:314`, `yearn.py:133`, `balancer.py:142`, `aave_oracle.py:142`). `quality-gates.sh`
  green. Shipped: `instruments-service@9ad39d5b`.
- **2026-08-07 (AO dispatch #8, `data_engineering`, slot 10, todo 3 `[DIAG] P1`)**: Found VM
  `canonical-migration-defi-gas-fees-legacy-purge-20260807-100248` **already RUNNING** (launched by [INFRA] P0 worker
  after BLK-4cd8f7bb was answered at 09:44Z). VM boot clean — `run.log` confirms: sanity-check 12,425 rows in
  75,819,124-row index (correct), GCS soft-delete retention 604800s, 0/0 GCS objects deleted (expected), streaming
  download started 10:05:51Z (`blob.download_as_bytes(timeout=900)` for 2,642,951,426 bytes = 2.46 GiB). **Heartbeat
  daemon (vm-life-emitter) died at ~10:06:02Z** — likely SIGPIPE after the stdout tee pipe closed; Python main process
  continued unaffected (EXIT_STATUS absent, VM RUNNING confirmed 10:15:33Z via `gcloud compute instances describe`). Log
  uploader also dead (run.log frozen at 3,268 bytes since 10:06:14Z, no new content during blocking
  `download_as_bytes()` call). Zombie watchdog `vm-zombie-watchdog-20260807-075242` RUNNING with 90-min idle threshold —
  safe. No VM/GCS/cron mutation performed. **Lessons**: (1) heartbeat daemon dying is not a signal the Python process
  died — check EXIT_STATUS file and VM `RUNNING` status independently; (2) log uploader and heartbeat daemon both run
  inside the vm-exec process group; if the tee pipe closes (e.g., stdout buffer overflow or SIGPIPE), both die silently
  while the Python script continues; (3) `blob.download_as_bytes(timeout=900)` produces zero stdout output during the
  download — the log WILL be silent for many minutes during a 2.46 GiB download; this is expected, NOT a stall. **Resume
  point**: poll `gs://deployment-scripts-central-element-323112/vm-logs/20260807-100248/EXIT_STATUS`; on EXIT_STATUS=0,
  (a) verify `_index/availability_index.parquet` filtered to 3-part TARGET signature = 0 rows, (b)
  `gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-defi-cron --location asia-northeast1`, (c)
  await ≥4 clean `--verify-only` cycles in cron run.log, (d) flip todos 3+4 in this plan + [DATA] P1 in issue doc, (e)
  push, (f) /done.
- **2026-08-07 (AO dispatch #9, `infra`, slot 8, todo 3-adjacent [INFRA] P0 relaunch todo)**: VM `100248` (from dispatch
  #8) found GONE (deleted 10:55:51Z, ~50min after its heartbeat sidecar died at 10:06:02Z — consistent with dispatch
  #8's own SIGPIPE finding). Manifest generation UNCHANGED (`1786048462981342`, still 2,642,951,426 bytes) — the CAS
  rewrite never fired, so no partial/corrupt state; safe to retry. **ROOT-CAUSED via GCP Cloud Audit Log (previously
  unknown — the 2026-08-06 fix `deployment-service@0e94ceee1` did NOT actually cover this kill path):** the delete's
  `protoPayload.requestMetadata.callerSuppliedUserAgent="python-requests/2.34.2"` +
  `serviceAccountDelegationInfo.firstPartyPrincipal=service-1060025368044@serverless-robot-prod.iam.gserviceaccount.com`
  proves a **Cloud Run** identity fired the delete — NOT the VM-side `vm_zombie_watchdog.py` daemon (independently
  verified via its own serial-console log: it logged "killed 0/0 zombies" across the EXACT kill-window sweep cycles
  10:53→10:58, i.e. its 90min canonical-migration- override was never even tested). The actual killer is
  `deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py`'s Cloud-Run-deployed
  `sweep()` (`_kill_stalled_vm` reuses the watchdog's `_kill_vm` primitive directly, bypassing `PREFIX_IDLE_THRESHOLDS`
  entirely) — a SEPARATE mechanism with its own flat `DEFAULT_KILL_MINUTES=45.0`, which explicitly watches the
  `canonical-migration-` family (`_is_backfill_vm` docstring) but was never given the same per-prefix override the
  2026-08-06 fix added to the OTHER watchdog. 45min + up to one ~5min sweep-cycle lands exactly on the observed ~50min
  kill. **Fix shipped this dispatch**: added `PREFIX_KILL_MINUTES = {"canonical-migration-": 90.0}` +
  `_resolve_kill_minutes()` (mirrors `vm_zombie_watchdog._resolve_idle_thresholds`) to `heartbeat_stall_watcher.py`,
  threaded into the `sweep()` loop's `should_auto_kill` call + the `DP_VM_STALL` log event; 2 new tests
  (`test_resolve_kill_minutes_canonical_migration_override`,
  `test_sweep_does_not_kill_canonical_migration_vm_before_override_threshold`). QG in flight at time of writing — ships
  via quickmerge once green, then relaunches the purge VM a 3rd time. Full evidence:
  `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md` progress log (cross-cited).
- **2026-08-07 (AO dispatch #9 continued, `infra`, slot 8)**: `heartbeat_stall_watcher.py` fix **SHIPPED**
  `deployment-service@14240378194039fe5a2cfb5e2d86dbed6cffe8d8` — `quality-gates.sh` full run green (246s, 0 failures),
  landed on `live-defi-rollout` via `quickmerge.sh --agent`, post-push ancestry verified
  (`git rev-list --count origin/live-defi-rollout..HEAD` = 0). Proceeding to the purge VM's 3rd relaunch attempt with
  fresh pre-flight re-verification per the `[INFRA] P0` todo's own checklist.
- **2026-08-07 13:43Z (AO dispatch #9 continued, `infra`, slot 8) — 3rd relaunch**: fresh pre-flight `--verify-only`
  scan confirmed 0 GCS objects across all 1881 TARGET-signature day(s) x 10 `TARGET_VENUES` (matches manifest generation
  `1786048462981342`, unchanged since the dispatch #8 failure — CAS never fired, safe retry); zombie watchdog RUNNING;
  consolidator cron PAUSED. Launched `canonical-migration-defi-gas-fees-legacy-purge-20260807-134308` (e2-highmem-8,
  SPOT, tarball verified fresh @ `142403781940` = includes the just-shipped fix). Boot clean (`run.log`): sanity-check
  12,425 rows confirmed, cron PAUSED confirmed, soft-delete retention 604800s confirmed, 0/0 GCS objects deleted
  (expected), streaming download started 13:47:09Z — the exact recovery point where dispatch #8's VM was killed by the
  (now-patched) `heartbeat_stall_watcher.py` at ~50min. Monitoring for survival past 45min to confirm the fix, then to
  terminal EXIT_STATUS.
- **2026-08-07 14:12Z (AO dispatch #9 continued, `infra`, slot 8) — pre-compact checkpoint**: VM confirmed RUNNING at
  T+25min (14:12Z), well past the halfway point of the expected 30-60min operation, no `EXIT_STATUS` yet. All repo
  worktrees in this slot clean and pushed (`deployment-service`@`1424037` ahead=0, `unified-trading-pm`@`bcf8e00d1`
  ahead=0; a `market-tick-data-service` `uv.lock` drift from an unrelated `scripts/setup.sh` invocation was discarded,
  not committed — environment artifact, not task output). **Resume point**: poll
  `gcloud compute instances describe canonical-migration-defi-gas-fees-legacy-purge-20260807-134308 --zone asia-northeast1-c`
  for status +
  `gcloud storage ls gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-gas-fees-legacy-purge-20260807-134308/`
  for `EXIT_STATUS`. On `EXIT_STATUS=0`: (a) verify `_index/availability_index.parquet` 3-part TARGET-signature filter =
  0 rows, (b)
  `gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-defi-cron --location asia-northeast1`, (c)
  await ≥4 clean `--verify-only` cycles in the cron's own run.log, (d) flip todo 3 (`[DIAG] P1`) and the `[INFRA] P0`
  relaunch todo above with full evidence citing both this doc and the issue doc, (e) commit+push, (f) `/done` on
  `defi_satellite_ao_dispatch_batch9-018`. **Lesson**: `ScheduleWakeup` `delaySeconds` does not track 1:1 with actual
  elapsed wall-clock time when interleaved with frequent external `/heartbeat` triggers — always confirm elapsed time
  via `date -u` against the operation's own logged start timestamp, not cumulative scheduled-delay arithmetic (caught a
  "~30min" miscount that was actually ~10min this session). **Lesson**: the VM's GCS log directory is keyed by the FULL
  VM name (`vm-logs/<full-vm-name>/`), not the bare timestamp suffix used as shorthand in prior Progress Log entries — a
  `gcloud storage ls` on the shorthand path returns "no objects" even though logs exist.
- **2026-08-07 15:22Z (AO dispatch #10, `infra`, slot 8)**: VM
  `canonical-migration-defi-gas-fees-legacy-purge-20260807-134308` (dispatch #9) found GONE — killed at 14:36Z by Cloud
  Run `heartbeat_stall_watcher.py` (audit log: `python-requests/2.34.2` UA + `unified-trading-sa` identity), ~49min
  after launch. Root cause: `heartbeat_stall_watcher.py` fix (`deployment-service@1424037`) is on `live-defi-rollout`
  but NOT yet on `main` or in the Cloud Run image (`deployment-api:latest` last built 09:31Z, pre-fix; LDR→main promote
  stalled — last promote at 10:51Z). Pre-flight: 0 GCS objects confirmed for all 10 TARGET_VENUES; manifest generation
  `1786048462981342` unchanged (CAS never fired in dispatch #9). **Mitigation**: paused
  `uts-prod-dp-heartbeat-watcher-cron` Cloud Scheduler job to prevent further Cloud Run kills during the blocking 2.46
  GiB download; zombie watchdog `vm-zombie-watchdog-20260807-075242` still RUNNING (90-min threshold) as backup.
  Launched 4th relaunch: `canonical-migration-defi-gas-fees-legacy-purge-20260807-152116` (SPOT, e2-highmem-8). Boot
  clean: 12,425 rows confirmed, cron PAUSED, 0/0 GCS objects, streaming download started 15:25:19Z. Expected completion
  ~16:25Z. **Resume**: poll
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-gas-fees-legacy-purge-20260807-152116/EXIT_STATUS`;
  on EXIT_STATUS=0: (a) verify manifest 3-part TARGET filter = 0 rows, (b) resume both
  `uts-prod-manifest-consolidator-market-data-defi-cron` AND `uts-prod-dp-heartbeat-watcher-cron`, (c) await ≥4 clean
  `--verify-only` cycles, (d) flip todo 3 ([DIAG] P1) + [INFRA] P0 relaunch todo, (e) push + /done.
- **2026-08-07 17:26Z (AO dispatch #11, `infra`, slot 5, task `defi_satellite_ao_dispatch_batch9-018`) — CLOSED**: Found
  VM `152116` GONE (deleted 15:47Z by a Claude Code agent via gcloud CLI, ~22 min into streaming download; no
  EXIT_STATUS). VM `170630` (launched ~17:06Z) found 0 TARGET rows in manifest gen `1786119981126589` at 17:08:59Z
  (75,665,201 total rows, 0 matching) — consolidator had regenerated the manifest naturally after GCS object deletion.
  VM `170630` exited rc=3 (HARD-ABORT: consolidator ENABLED, not PAUSED). Fresh GCS check at 17:26Z: 0 objects across
  all 10 TARGET_VENUES (ARBITRUM/AURORA/AVALANCHE/BASE/BSC/ETHEREUM/LINEA/MANTLE/OPTIMISM/POLYGON). Consolidator cron
  ENABLED (*/1 min), ≥17 clean cycles since 0-row confirmation at 17:09Z. Heartbeat watcher cron PAUSED → resumed at
  17:26Z. End state: manifest 0 of 12,425 TARGET rows, GCS 0 objects all venues. Todos 3+4 flipped. Sources:
  `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` +
  `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`.
- **2026-08-09 (slot 2, data_engineering, task `defi_satellite_ao_dispatch_batch9-011`)**: closed the `funding_oi`
  verification-log todo. `run.log` for VM `features-delta-one-defi-20260805-105902` was still present in GCS (no
  relaunch needed): zero DEX-pool-instrument warnings (vs. the thousands this doc's source issue documented pre-fix),
  ~39s wall-clock, confirming `features-service@f932908b`'s scoping fix. The run's own `rc=1` traced (bounded
  column-pruned manifest read, `data_type=perp_funding venue=HYPERLIQUID`) to HYPERLIQUID's already-complete 2026-06-21
  removal from `asset_group=defi` — honest absence, not a regression. Issue doc
  `delta_one_get_available_instruments_unscoped_candle_data_types_2026_07_30.md` flipped to `status: resolved` +
  `resolved_by` set. No code shipped (log-citation closure only).
- **2026-08-09 (slot 24, data_engineering, task `defi_satellite_ao_dispatch_batch9-014`)**: ✅ Removed the orphaned AAVE
  `rewards` seed + venue-capability entries — `defi_prediction_instrument_seeds.py` no longer maps
  `(AAVE_V3-ETHEREUM, rewards)`; `defi_venue_capabilities.py` no longer declares `rewards` for any AAVE_V3 chain (8 of
  the 10 chains carried the key; SCROLL/ZKSYNC never did). Adjusted `test_mtds_venue_coverage.py`'s
  `test_aavev3_ethereum_dts_share_reserve_universe` to drop the now-empty `rewards` leg of the shared-reserve-universe
  assertion. `unified-api-contracts` full `quality-gates.sh` green post-removal (0 failures). Shipped:
  unified-api-contracts@9e44d861.
