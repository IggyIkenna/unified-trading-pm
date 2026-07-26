---
doc_type: plan
title: DeFi satellite AO batch 1 — conflict-cleared extraction from the 2026-07-25 orphan audit
summary: >-
  First AO-dispatch batch for defi (the last of 5 asset groups getting the /ag-closeout-audit skill's Phase 3 treatment
  this session, after sports/tradfi/prediction/cefi). Extracted from a 40-doc AO-eligibility triage over every defi
  satellite doc not covered by defi_consolidated_closeout_2026_07_18.md /
  defi_consolidated_closeout_aggregated_sources_2026_07_24.md. The triage found 60 candidate AO-eligible todos across 29
  of those docs (1 doc flagged too-large-or-risky excluded entirely, itself having had 1 candidate deferred alongside
  it; 9 further docs had zero eligible candidates from the start — 10 excluded docs total), each cross-checked against
  every one of that doc's own flagged conflicts per the operator's 2026-07-25 conflict-check discipline. 59 of the 60
  survived — the 1 remaining is a genuine cross-doc contradiction routed to the operator decision queue, not silently
  decided. 4 groups of same-file collisions (10 sub-items total, spanning both within-doc and cross-doc overlaps) were
  combined into 4 todos to avoid an in-batch same-file collision, so the 59 surviving candidates ship here as 53 todo
  bullets, plus a 54th appended 2026-07-25 once operator-decision entry #3 (Kamino/Solend `lending_indices` shape)
  resolved and moved from the operator queue into Todos (see the Deferred section's "RESOLVED" note) — 54 todo bullets
  total.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    market-tick-data-service,
    strategy-service,
    instruments-service,
    unified-api-contracts,
    market-data-processing-service,
    deployment-service,
    unified-trading-library,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-1, satellite-docs, conflict-checked]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.6
estimate_calibrated_ai_days: 3.7
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /autonomous session 2026-07-25, driven by the /ag-closeout-audit skill Phase 3 (conflict-checked next-batch drafting)
  after a 40-doc defi satellite AO-eligibility triage (per-doc kept/excluded/needs_operator_ruling captured this
  session, mirroring the sports/tradfi/prediction/cefi batch1 methodology). This doc is the conflict-cleared subset only
  (59 of 60 candidates, shipped as 53 combined todo bullets).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 1 — conflict-cleared extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 53 todos below are same-priority-within-doc and touch distinct files (4 same-file collision
> groups — spanning both within-one-doc and cross-doc overlaps — were combined specifically to avoid an in-batch
> collision, see each combined todo's own note) so they are safe to dispatch concurrently once activated. Every included
> item's source doc already showed an empty `excluded`/`needs_operator_ruling` conflict list at extraction time except
> one doc (todo 53's source), whose 2 non-kept items are in the Deferred section below with their stated reasons, and
> one further doc whose sole candidate is a genuine cross-doc contradiction routed to the operator decision queue rather
> than shipped here.

## Todos

- [x] ✅ [SCRIPT] P1. Repoint `market-tick-data-service/scripts/migrate_legacy_solana_defi_to_canonical.py`'s
      `SubsetSpec.canonical_bucket_kind` off the invalid `"dex-pools"`/`"lst-rates"` values (falls through to a legacy
      fallback building now-404 flat bucket names) to `resolve_bucket_name(kind="tick-data",     asset_group="defi")`,
      mirroring the pattern already shipped in `canonical_dex_pool_provider.py` / `data_manifest_handler.py` in this
      same source plan. Repo: market-tick-data-service. **Done when**: neither kind resolves to the dead legacy
      fallback; the script's usage sites still import/parse cleanly; `quality-gates.sh` green. Source:
      `defi_dedicated_bucket_shared_migration_2026_07_13.md`. — market-tick-data-service@ebaae6f43f69. Both
      `get_write_bucket_name(spec.canonical_bucket_kind)` call sites now resolve via
      `resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="defi")`; removed the now-vestigial
      `canonical_bucket_kind` field from `SubsetSpec` and all 8 constructions (every subset writes to the same shared
      bucket now, so the field no longer carried information). `quality-gates.sh` green (286s, sentinel written).
- [x] ✅ [SCRIPT] P1. Repoint `strategy-service/scripts/trace_carry_staked_basis.py`'s `_LST_RATES_BUCKET_TEMPLATE` /
      `_PERP_FUNDING_BUCKET_TEMPLATE` off the dead flat-bucket-name templates to
      `resolve_bucket_name(kind="tick-data",     asset_group="defi")`, mirroring the pattern already shipped for
      `canonical_dex_pool_provider.py` / `canonical_perp_funding_provider.py`. Repo: strategy-service. **Done when**:
      both templates are removed/replaced; `main()`'s slot-processing loop still runs against real prod GCS data without
      error; `quality-gates.sh` green. Source: `defi_dedicated_bucket_shared_migration_2026_07_13.md`. — **Already
      resolved, no code change needed**: `strategy-service/scripts/trace_carry_staked_basis.py` (and both templates) no
      longer exist — the whole file was deleted `strategy-service@c09785a8` (2026-07-21, "fix: repoint funding/staking
      diagnostic scripts off deleted flat buckets to canonical resolve_bucket_name"), 4 days before this batch1 plan's
      2026-07-25 triage ran, superseded by `scripts/trace_all_carry_archetypes.py` (unified 7-archetype tracer,
      `strategy-service@24a40d5f`, reads `features-onchain`/`features-delta-one` via `resolve_bucket_name` already — no
      raw-tick-data bucket template of this shape survives anywhere in the repo, confirmed via corpus grep). Verified
      via `git log --diff-filter=D` + `git show c09785a8` on `live-defi-rollout`; nothing to ship.
- [x] ✅ [SCRIPT] P1. Repoint `strategy-service/scripts/probe_funding_rate_dispersion_coverage.py`'s
      `_DEFAULT_PERP_FUNDING_BUCKET_TEMPLATE` default to `resolve_bucket_name(kind="tick-data", asset_group="defi")`.
      Repo: strategy-service. **Done when**: the default no longer references a dead flat bucket name; running with no
      `--perp-funding-bucket` override resolves the shared bucket; `quality-gates.sh` green. Source:
      `defi_dedicated_bucket_shared_migration_2026_07_13.md`. — **Already resolved, no code change needed** (found while
      verifying the adjacent todo above, same source doc/same commit): `_resolve_buckets()` in
      `probe_funding_rate_dispersion_coverage.py` already calls
      `resolve_bucket_name(cloud=cloud, kind="tick-data", asset_group="defi")` for the funding bucket (and
      `asset_group="cefi"` for the tick bucket) — `_DEFAULT_PERP_FUNDING_BUCKET_TEMPLATE`/
      `_DEFAULT_TICK_DATA_BUCKET_TEMPLATE` were removed in the same `strategy-service@c09785a8` commit above. Verified
      by reading the current file; nothing to ship.
- [x] ✅ [CHORE] P1. Correct (or remove) the stale `"bucket_type": "dex-pools"`/`"perp-funding"` values in the
      module-level `OPERATIONS` constant in `market-tick-data-service/cli/handlers/data_manifest_handler.py` (confirmed
      unused elsewhere, contradicting the same file's own correct `_build_operations_dict()`, already
      `kind="tick-data"`). Repo: market-tick-data-service. **Done when**: `OPERATIONS`'s values no longer contradict
      `_build_operations_dict()`; a workspace grep confirms no other reader of the stale values; `quality-gates.sh`
      green. Source: `defi_dedicated_bucket_shared_migration_2026_07_13.md`. — market-tick-data-service@2bee1811. Both
      entries changed `"dex-pools"`/`"perp-funding"` → `"tick-data"`, matching the `kind="tick-data"` actually passed to
      `resolve_bucket_name()` by both real scanner call sites; workspace grep confirmed no reader of the old literals
      inside this constant (other repos' `"dex-pools"`/`"perp-funding"` hits are unrelated pre-2026-07-13 one-off
      migration scripts with their own local literals). Also fixed a pre-existing, unrelated QG blocker found along the
      way: `test_rule11_per_ag_shard_counts_byte_unchanged`'s CEFI pin (208) was stale against `uac@dfecc787`
      (registered `volatility_index` for cefi, +26 shards = 234) — root-caused via git-stash reproduction on a clean
      HEAD (fails identically without my change), bumped the pin with a dated comment. `quality-gates.sh` green (247s,
      sentinel written).
- [x] ✅ [CHORE] P1. Fix the 2 stale comments in `strategy-service/strategy_service/cli/handlers/paper_run_handler.py`
      that describe classes as "kind `perp-funding`"/"kind `dex-pools`" when the code already resolves
      `kind="tick-data"` — comment-only, no behavior change. Repo: strategy-service. **Done when**: both comments
      accurately describe the current resolution; no executable line changed; `quality-gates.sh` green. Source:
      `defi_dedicated_bucket_shared_migration_2026_07_13.md`. — strategy-service@4a7fbb17. Verified against the real
      `resolve_bucket_name()` calls in `canonical_perp_funding_provider.py`/`canonical_dex_pool_provider.py` (both
      `kind="tick-data"`); comment-only edit, no executable line changed; `quality-gates.sh` green (214s).
- [ ] [CODE] P1. Implement Phoenix DEX radix-slab top-of-book decode in
      `market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py` — parse the Phoenix market-account slab
      layout (RPC fetch already works) to populate `best_bid_price`/`best_ask_price`/sizes/`spread_bps`/`mid_price`;
      replace `record_failed(reason="SOURCE_HANDLER_TODO_PHOENIX_DECODE")` with `record_captured` once decoded; add 5+
      unit tests against known slab states. Repo: market-tick-data-service. **Done when**: a successful fetch calls
      `record_captured` (not `record_failed`) with all 5 fields populated; >=5 new unit tests pass; `quality-gates.sh`
      green. Source: `data_completion_defi_2026_07_15.md`.
- [ ] [CODE] P1. Implement Orca Whirlpool tick-array binary decode in
      `market_tick_data_service/cli/handlers/orca_whirlpool_state_handler.py` — decode the 3 nearest tick arrays around
      the already-extracted `tick_current_index` (~150-200 LOC), captured per-snapshot alongside the existing pool-state
      row, so downstream consumers can compute fill slippage at arbitrary sizes. Repo: market-tick-data-service. **Done
      when**: per-snapshot tick-array state is captured and persisted alongside pool state; new unit tests cover the
      decode; `quality-gates.sh` green. Source: `data_completion_defi_2026_07_15.md`.
- [ ] [DATA] P1. **Combined `instruments-service/scripts/enumerate_expected_universe.py` fix (2 sub-items merged into
      one todo — both would EDIT the same file):** (a) locate + fix the DeFi expected-universe seeder that emits
      blank-`chain` venue rows for the oracle-prices/perp-funding sub-buckets — canonicalize `chain` at write time in
      `instruments-service/instruments_service/engine/orchestrator/defi.py` instead of leaving it blank; (b) normalize
      the tz-naive vs tz-aware timestamp comparison in `_enumerate_v2_prediction` (~line 1852) — align
      `pd.Timestamp(created_str)`/`pd.Timestamp(settled_str)` and `window_start_ts`/`window_end_ts` to the same
      tz-awareness before comparing, so a scan-only v2-prediction enumerator run can complete without a `TypeError`.
      Repo: instruments-service. **Done when**: (a) a newly-seeded oracle/perp DeFi row carries a non-blank canonical
      chain value (verified via a targeted read of one recent day-shard, not a whole-corpus walk); (b) a scan-only
      `enumerate_expected_universe.py --asset-group prediction --enumerator-version v2` run completes end-to-end without
      the tz-comparison `TypeError` and reports a final candidate count; `quality-gates.sh` green in
      instruments-service. Source: `data_completion_defi_2026_07_15.md`,
      `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`.
- [ ] [BACKEND] P1. **Combined `market-tick-data-service/.../lst_rates_handler.py` fix — sub-item (b) DONE 2026-07-26
      (slot-14), sub-item (a) still OPEN.** (a) both `pipeline_mode_for_source("onchain_subgraph", ...)` call sites
      (~line 351 and ~447) hardcode the source string for EVERY Solana LST row regardless of which tier actually
      produced it — the per-row `method` field (written by `solana_lst_archival.py`) already tracks
      `alchemy_get_account_info` / `thegraph_subgraph` / `rest_api` / `defillama_historical_ratio`, so Tier-4
      `defillama_historical_ratio` rows (a market-price proxy, NOT genuine on-chain data) get the same
      `batch_onchain_subgraph` label as genuine Tier 1-3 rows — derive the source argument from each row's own
      `method`/tier instead (at minimum add a distinct source value for the Tier-4 path); the EVM LST path has no
      tier-fallback system and must stay byte-identical (do not touch it). **Still open — the remaining unit of work on
      this todo.** (b) ✅ **DONE 2026-07-26 (slot-14, done as a prerequisite of
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s residual-emitter todo, which discovered this was still
      unshipped despite that plan's premise that it was already fixed excluding the residual path).**
      `_write_single_lst_group()` now loops `write_defi_rows()`'s per-instrument `shards` and calls
      `record_captured(instrument_id=..., row_count=...)` once per shard instead of one (protocol, chain) aggregate with
      no `instrument_id` — mirrors `record_swap_pool_map()`/`record_market_captures()`/`_record_manifest_result()`. The
      residual/empty path (originally out of THIS todo's scope, per its "do not touch" framing — it belongs to
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s residual-emitter todo) was wired in the SAME session/commit
      since batch2's todo genuinely depends on this fix landing first. Split the write functions into a new
      `_lst_rates_write.py` sibling module (codex 900-line ratchet). Extended the existing captured-path test with an
      `instrument_id` assertion. `market-tick-data-service@9d796b0e`, `quality-gates.sh` green. **Repo:
      market-tick-data-service. Remaining done when (sub-item (a) only)**: a distinct pipeline_mode/source label is
      written for Tier-4-sourced rows vs Tier 1-3 rows (new/updated assertion in `tests/unit/test_lst_rates_handler.py`
      or `test_lst_rates_handler_coverage.py`), EVM LST pipeline_mode unchanged (pinned by a regression assertion);
      `quality-gates.sh` green. Source: `defi_strategy_pnl_axis_index_2026_07_24.md`,
      `lst_rate_honest_coverage_2026_07_21.md`,
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`.
- [ ] [BACKEND] P1. Fix `_perp_funding_kalshi_polymarket.py`'s KALSHI_PERP/POLYMARKET_PERP routing in
      market-tick-data-service: route both venues through a cefi-classified write path (mirroring
      `onchain_perp_batch_handler.py`'s explicit `asset_group='cefi'` `ManifestWriter` precedent) instead of DeFi-only
      `write_defi_rows`; fix the `source` field (currently hardcoded `"hyperliquid"` for both venues) to be
      venue-derived; then, only after the writer fix lands, run a targeted manifest cleanup of the small number of
      pre-existing stale KALSHI_PERP/POLYMARKET_PERP defi-classified rows. Repo: market-tick-data-service. **Done
      when**: rows route via a cefi-classified path (never `write_defi_rows`); `source` reflects the real venue;
      `quality-gates.sh` green; the pre-existing stale defi-classified rows are cleaned up in the same change. Source:
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`.
- [ ] [DATA] P1. Measure the exact scope of MTDS manifest rows stamped `instrument_type="liquidation"` by the pre-fix
      `liquidations_handler.py` code path (before `market-tick-data-service@fec20de2`), cross-checking each row's
      historical `protocol` column against `resolve_lending_instrument_type(protocol)` to confirm genuine lending
      mislabeling (never a real liquidation-event row). Then build
      `market-tick-data-service/scripts/restamp_lending_instrument_type_2026_07_24.py` mirroring the
      `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py`/`restamp_sports_odds_horizon_bucket_2026_07_22.py` safety
      pattern (dry-run default = the scope measurement, `--apply` CAS-guarded, pre-apply snapshot, post-write
      verification, unit tests). Ship via quickmerge, `quality-gates.sh` green first. Do NOT run `--apply` — operator
      gated. Repo: market-tick-data-service. **Done when**: the script exists; its dry-run mode prints the exact
      affected row count + shard/venue/date breakdown; unit tests cover classification/dry-run/apply and pass;
      `quality-gates.sh` green; commit verified as an ancestor of `origin/live-defi-rollout`; script remains un-applied
      at hand-off. Source: `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`.
- [ ] [CHORE] P1. Replace the stale `onchain/__init__.py` module docstring with the corrected text already drafted and
      verified in the source issue doc §2.2 (documents `GlassnodeAdapter` as `PLANNED_VENUES`-parked and
      `HeliusSolanaAdapter` as `BLOCKED-CREDENTIALS`-gated, replacing a stale 2026-04 "all adapters deleted" claim) —
      first confirm via `git status`/mtime that no other session has live uncommitted WIP in this file/package. Repo:
      market-tick-data-service. **Done when**: `market_interface/adapters/onchain/__init__.py`'s docstring matches the
      issue doc's §2.2 text verbatim, committed via quickmerge with `quality-gates.sh` green. Source:
      `issues/defi_adapter_dead_code_audit_2026_07_24.md`.
- [ ] [DIAG] P1. Trace whether `market_interface/adapters/defi/curve_adapter.py::_download_liquidity`'s broad
      `except Exception: ... return []` (~line 682) is distinguishable, in `base_defi_adapter.py`'s per-instrument
      loop's `if not result: continue` success/failure accounting, from a genuine zero-liquidity-snapshot day — write
      the finding (confirmed-masking or confirmed-legitimate) into an update appended to the issue doc, or a new issue
      doc if masking is confirmed. Repo: market-tick-data-service. **Done when**: a written, evidence-cited verdict
      states definitively whether the broad-except-return-`[]` path is/isn't distinguishable from a genuine empty-result
      day, quoting the caller code that proves it. Source: `issues/defi_adapter_dead_code_audit_2026_07_24.md`.
- [ ] [SCRIPT] P1. **Combined `market-tick-data-service/.../dex_swaps_handler.py` fix (2 sub-items merged into one todo
      — both would EDIT the same file, different venues/bugs):** (a) classify the CURVE/OPTIMISM "no allocations"
      GraphQL response as a distinct terminal condition at fetch time — detect a 200-status response whose `errors[]`
      message matches `subgraph not found: no allocations` (or any non-schema-drift GraphQL error repeating identically
      across all 5 cascade schema attempts) inside `_execute_subgraph_query`/`_run_cascade`, raise a typed terminal
      error (reuse `SubgraphNotFoundError` or add `_SubgraphDeindexedError`) instead of falling through to the generic
      RuntimeError, wire the manifest writer to `record_empty(reason=     EXPECTED_SUBGRAPH_DEINDEXED)` instead of
      `record_failed`; (b) fix the TRADER_JOE_V2 TheGraph query-schema-cascade failure (subgraph
      `H2VGe2tYavUEosSjomHwxbvCKy3LaNaW8Kjw2KhhHs1K`, confirmed 0% capture 2023-2026, all 5 cascade schemas fail with
      `bad indexers`) via a new/updated query schema variant or a deployment-ID swap per the live GraphQL error, then —
      once real TRADER_JOE_V2 rows confirmed flowing — launch a dedicated `dex_pool_swaps` backfill
      (`deployment-service/scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh`) for TRADER_JOE_V2 + VELODROME_V2 covering
      2023-01-01 through 2024-10-06. Repos: market-tick-data-service, deployment-service. **Done when**: (a) a live
      probe (or a simulating unit test) against CURVE/OPTIMISM's dex_pool_swaps cascade results in
      `record_empty(reason=EXPECTED_SUBGRAPH_DEINDEXED)`, not `record_failed`; a fresh backfill VM run produces no new
      `attempted_failed` rows for this cause; (b) TRADER_JOE_V2/AVALANCHE queries return real non-empty swap rows on 3+
      sample dates; the scoped SPOT backfill VM is launched and T+10min health-verified RUNNING; `quality-gates.sh`
      green. Source: `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`,
      `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`.
- [ ] [SCRIPT] P1. Spot-check live subgraph health for the remaining un-investigated `dex_pool_swaps` long-tail
      `attempted_failed` buckets (`UNISWAP_V3` TimeoutError×25, `UNISWAP_V3`/POLYGON schema-drift×24, 1-5-row long-tail
      buckets) — repeat the doc's live-probe methodology (direct POST to each subgraph's TheGraph gateway; fresh
      `_meta.block.timestamp` = healthy vs 200-with-`errors[]` "no allocations" = dead); re-measure each bucket's
      current row count against prod `_index/availability_index.parquet`. Read-only. Repo: market-tick-data-service.
      **Done when**: every distinct (venue, chain) subgraph ID backing the remaining long-tail buckets has a recorded
      live-probe verdict + current row count, written up as a follow-up issue doc. Source:
      `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`.
- [ ] [PM] P1. File a new tracked issue doc for the `collect-mev-events` pagination gap: `mev_events_handler.py` only
      pages the newest ~100 Flashbots relay rows/day (hard-exits after the first page), under-covering any day with >100
      MEV-Boost relay payloads — already fully root-caused in the source doc, no new investigation needed. Correct
      frontmatter (`doc_type: issue`, `asset_group: [defi]`, `repos:     [market-tick-data-service]`). Repo:
      unified-trading-pm. **Done when**: a new `plans/active/issues/defi_mev_events_pagination_gap_<date>.md` exists
      with the file:line citation + correct frontmatter, cross-referenced from the source doc's follow-up line. Source:
      `issues/defi_five_never_captured_venues_fix_2026_07_22.md`.
- [ ] [PM] P1. File a new tracked issue doc for the collect-* Terraform stagger's pre-existing T+1 freshness-deadline
      risk: `defi_collection_scheduler.tf`'s header requires the stagger finish by 02:25 UTC for `features-onchain` T+1
      freshness, but `solana-defi` alone (02:05 start, 1500s timeout) can already finish ~02:30 — appears
      pre-existing-violated. Name `t1_batch_scheduler.tf:124-128` as the owner to flag. Repo: unified-trading-pm. **Done
      when**: a new `plans/active/issues/defi_t1_freshness_deadline_stagger_<date>.md` exists citing both files and the
      deadline math. Source: `issues/defi_five_never_captured_venues_fix_2026_07_22.md`.
- [ ] [PM] P1. File a new tracked issue doc for the gas-fees historical `venue=<CHAINNAME>` path-migration question: the
      2026-07-22 rename (`market-tick-data-service@522185a6`, `_GAS_FEE_VENUE="ALCHEMY"`) fixed paths only forward —
      pre-existing historical `gas_fees` objects still sit under `venue=<CHAINNAME>` and won't retroactively move. Flag
      migrate-vs-leave as operator-gated — do not decide/execute here. Repo: unified-trading-pm. **Done when**: a new
      `plans/active/issues/defi_gas_fees_historical_venue_path_migration_<date>.md` exists documenting the pre-rename
      objects + rename commit, tagged `[OPERATOR]`/human-gated. Source:
      `issues/defi_five_never_captured_venues_fix_2026_07_22.md`.
- [ ] [PM] P1. File a new tracked issue doc for the ACROSS/STARGATE `bridge_events` historical-backfill capability gap:
      `bridge_events_handler.py` has no `--start-date`/`--end-date` CLI support (confirmed via grep, zero matches), so
      the daily cron can't be reused for a historical backfill to genesis (ACROSS 2021-11-11, STARGATE 2022-03-17)
      without that flag first. Do not build the flag or run a backfill here. Repo: unified-trading-pm. **Done when**: a
      new `plans/active/issues/defi_bridge_events_historical_backfill_gap_<date>.md` exists documenting the missing CLI
      support + genesis dates, correctly scoped as blocked-on-unbuilt-tooling. Source:
      `issues/defi_five_never_captured_venues_fix_2026_07_22.md`.
- [ ] [DATA] P1. Measure the true scale of the DeFi legacy pre-hive composite-venue object population (objects shaped
      like `.../venue=ETHENA-ETHEREUM/ticks_migrated_*.parquet` — no `chain=`/`instrument_type=`/`data_type=` hive
      segments — that `parse_hive_path()` returns `None` for, counted only toward `rebuild_defi_manifest.py`'s
      `unparseable` counter). Either extend that counter to persist the full unparseable-path set, or run a bounded
      manifest-driven cross-check (GCS presence vs zero manifest rows) — NOT a fresh whole-corpus walk. Repo:
      market-tick-data-service. **Done when**: a real count or tight bounded estimate (with method cited) of how many
      objects across the full 2020-2026 defi date range carry this legacy composite-venue shape is recorded as a dated
      update to the issue doc. Source: `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`.
- [ ] [DIAG] P1. Sample and directly read parquet content from a broader set of DeFi legacy composite-venue objects
      (beyond the single confirmed ETHENA-ETHEREUM example) — spanning the 9-venue population already identified on the
      2025-08-06 sample (AAVEV3/CURVE/ETHENA/ETHERFI/LIDO/MORPHO/UNISWAPV2/V3/V4-ETHEREUM) — and report per sampled
      object whether it's single-row-scale (like the confirmed ETHENA sample) or carries substantial historical data.
      Repo: market-tick-data-service. **Done when**: a stated distribution (e.g. "N of M sampled are single-row")
      covering a representative multi-venue/multi-day sample is recorded as a dated update to the issue doc, sufficient
      for the fold-vs-migrate decision to be answered against. Source:
      `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`.
- [ ] [DATA] P1. Corpus-wide scope audit for the KALSHI_PERP perp_funding manifest-emit failure: scan GCS under the
      scoped prefix (`pipeline_mode=batch_kalshi_perp/asset_group=defi/venue=KALSHI_PERP/...`) for all 5 observed
      KALSHI_PERP perp symbols across the full date range objects exist for (single-prefix listing, not a whole-corpus
      walk), cross-checking each day/symbol against the DeFi manifest index to confirm GCS-present / manifest-absent.
      Repo: market-tick-data-service (read-only). **Done when**: a per-day, per-symbol count of (GCS present / manifest
      absent) instances is produced across the full observed date range and recorded in the issue doc's "Not yet done"
      section, replacing the current single-day framing. Source:
      `issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`.
- [x] ✅ [BACKEND] P1. **DONE 2026-07-26 (slot-14, done as a prerequisite of
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s residual-emitter todo, which discovered this was still
      unshipped despite that plan's premise).** Generalised `catalogue_pool_ids_for_shard()` (`_catalogue_filter.py`)
      beyond the hardcoded `instrument_type=='pool'` filter — added an `instrument_type` parameter (default `"pool"`,
      byte-for-byte unchanged), any other type filters the cached catalogue on that `instrument_type` and builds the id
      set from the catalogue's general `instrument_id` column (lowercased). `instrument_type="pool"` path unchanged
      (existing pool tests green unmodified); 2 new unit tests prove `instrument_type="lending"` returns the correct
      in-window id set (+ respects the chain filter) from a synthetic non-pool catalogue fixture.
      `market-tick-data-service@9d796b0e`, `quality-gates.sh` green. Source:
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`.
- [ ] [DATA] P1. **Combined `vault_share_price_handler.py` investigation + fix (3 sub-items merged into one todo, all
      from the same doc, naturally sequenced confirm→measure→fix, 1 of the 3 EDITS the file):** (a) confirm the
      YEARN_V3/ETHEREUM/yield_bearing/vault_share_price pipeline_mode↔source desync stale-row hypothesis — read the live
      manifest rows' `attempted_at`/`available_at` and compare against the handler's git-blame introduction date (scoped
      manifest read, no new whole-corpus walk); (b) measure blast radius beyond the single sampled row — scan the defi
      manifest for any row where `pipeline_mode` implies one vendor via `pipeline_mode_for_source` reverse-mapping while
      `source` names a different vendor, scoped first to YEARN_V3 then all `vault_share_price`-data_type venues; (c) fix
      the handler to pass an explicit `source=` kwarg (e.g. `source="onchain_rpc"`, matching the value already passed to
      `pipeline_mode_for_source`) on every `record_captured`/`record_failed`/`record_zero_rows` call (currently
      blank-default). Repo: market-tick-data-service. **Done when**: (a) a written finding states whether the row(s)
      predate or postdate the handler's git-blame commit, both dates cited by sha/timestamp; (b) a written count/list of
      every row exhibiting the desync (beyond the one sampled row) is produced, scoped YEARN_V3 then all
      vault_share_price venues; (c) every call site in the file passes a non-blank explicit `source=` kwarg;
      `quality-gates.sh` green; shipped via quickmerge scoped to this file. Source:
      `issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`.
- [ ] [SCRIPT] P1. Write + run a read-only cross-source funding-parity check for every surviving DeFi perp venue
      declared for BOTH `perp_funding` and `derivative_ticker` in UAC's capability registry (excluding
      DRIFT-SOLANA/PACIFICA-SOLANA per the 2026-07-16 partial-supersede ruling; also exclude GMX — REMOVED 2026-07-25,
      see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md` — it is no longer a registered venue). Per
      (venue, market, funding interval) compare `perp_funding.funding_rate` against the matching `derivative_ticker`
      settlement row within a documented tolerance; emit an honest report (match %, divergence distribution, worst
      offenders). File any genuine divergence via standard findings-triage — do not resolve inline. No prod writes.
      Repo: market-tick-data-service (new lifecycle-marked script under `scripts/one_offs/`). **Done when**: the script
      exists with a lifecycle marker, runs clean read-only against prod GCS/manifest for every named venue, and a
      match%/divergence report is appended to the source issue doc's Progress log. Source:
      `issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-26 (slot-5, review) — real findings, not the expected Balancer-mismatch.** Audited
      all 6 known DeFi cross-chain pool-address collisions end-to-end. **Stage 1 (catalogue): PASS for all 6** — no
      `@CHAIN` suffixes anywhere in the live 12,219-row catalogue (the 2026-07-08 Balancer patch is gone/superseded,
      resolving the doc's finding #2 outright); `canonical_instrument_id` correctly disambiguates every row. **Stage 2
      (MTDS `defi_catalog_reader.py:192`): read-PASS, but a genuine pre-flight-skip FAIL/RISK finding** in
      `orchestrator/__init__.py::_run_preflight_availability_check` — its captured-atom skip-set keys on
      `(venue, data_type) → {bare instrument_id}` with `chain` never read anywhere in the function, so it cannot
      distinguish our exact collision shape. **Stage 3 (MDPS): the SAME bug class, second instance** in
      `orchestration_scanner.py`'s `existing_outputs` dedup (`(timeframe, instrument_id)`, bare). **Stages 4-5
      (features-service, manifest/data-status): NOT independently traced** (time-bounded; filed as follow-up scope, not
      guessed at). Filed a new P2 fix todo in the issue doc + flipped 3 stale/resolved checklist items there
      (verify-6-collisions, reconcile-Balancer-patch — now moot, fix-CURVE — premise was stale, CURVE was already
      correct). unified-trading-pm@00e073836. Repos: instruments-service, market-tick-data-service,
      market-data-processing-service, unified-trading-pm (read-only audit, no code changed). Source:
      `issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`.
- [ ] [DOC] P1. Port the already-decided two-id/dual-key POOL model into `/codex/02-data/defi-canonical-naming-ssot.md`
      — document that `instrument_id` stays bare `pool_address.lower()` while `chain` lives only in the symbolic
      `canonical_instrument_id`/`glued_pair_id` (Option A, operator ruling 2026-07-18), sourcing content already
      established in `unified_api_contracts/canonical/crosscutting/defi.py:313-331,409-435`,
      `instruments-service/docs/DEFI_INSTRUMENTS.md`, and the closeout plan's "The two-id model" section. Repo:
      unified-trading-pm. **Done when**: the codex doc contains a section documenting the two-id model consistent with
      those 3 sources. Source: `issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`.
- [ ] [INFRA] P1. Add a `staking-yields` entry to `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s
      `defi_collect_operations` map (cron `50 1 * * *`, the free slot between `eigenlayer-rewards` at 01:45 and
      `evm-defi` at 01:55; tier mirroring `eigenlayer-rewards`), apply via the same single-PR flow every other job in
      the file uses. Repo: deployment-service. **Done when**: `gcloud scheduler jobs list` shows a
      `staking-yields`-named job ENABLED and `gcloud run jobs list` shows the matching Cloud Run Job; after its first
      run, at least 1 manifest row exists for `instrument_type=staking` (verify STARTED + the manifest row per
      no-fire-and-forget — do not mark done on terraform-apply alone). Source:
      `issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`.
- [ ] [DATA] P1. Correct `/codex/02-data/defi-data-types-catalog.md` § 7's `staking_yields` row: remove the
      `Status:     Production (2026-04-24)` label — live-verified FALSE (zero scheduler jobs, zero Cloud Run Job, zero
      GCS objects across 6 sampled days, confirmed 2026-07-24) — and restate as `Status: Implemented, unscheduled`. Do
      NOT flip to Production — gated on the separate scheduler-wiring todo shipping. Repo: unified-trading-pm. **Done
      when**: the row no longer reads `Production (2026-04-24)`, instead reads an unscheduled/never-run status
      consistent with § 1's live-verification findings. Source:
      `issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`.
- [ ] [VERIFY] P1. Run a bounded, read-only simulation of instruments-service's `enumerate_expected_universe.py` defi
      resolution path (a scoped catalog subset, not a full prod re-run) to measure the `completeness_pct` denominator
      delta of adding the 7 `swaps_ohlcv_{15s,1m,5m,15m,1h,4h,1d}` keys to `DATA_TYPES_BY_ASSET_GROUP['defi']` WITH vs
      WITHOUT a `_DEFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`-style exclusion guard (mirroring the existing tradfi
      pattern in the same file). Ship no registry/code change — report only. Repo: instruments-service (read-only).
      **Done when**: a report citing the measured completeness_pct delta for both scenarios exists, answering whether
      the registry addition is safe directly or needs the guard first. Source:
      `issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`.
- [ ] [VERIFY] P1. Determine the root cause of the `swaps_ohlcv_4h` timeframe discrepancy — live manifest shows 51,985
      real captured rows despite `4h` being absent from `unified-api-contracts`'s `_candle_contracts.py`
      module-docstring declared DeFi timeframe set. Confirm intentional (correct the stale docstring to include `4h`) or
      a policy-violating bug (identify the producing code path in MDPS's `DefiSwapAdapter`/`swap_adapter.py` and file a
      follow-up). Repos: unified-api-contracts, market-data-processing-service. **Done when**: root cause is determined
      and cited with evidence; if intentional, the docstring is corrected; if a bug, the producing path is identified
      and a follow-up issue filed. Source: `issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`.
- [ ] [SCRIPT] P1. Thread `mode=` into `assert_defi_catalog_fresh()` for the 9 remaining DeFi handlers still omitting it
      (`liquidations_handler.py`, `native_staking_handler.py`, `liquidation_events_handler.py`,
      `token_transfers_handler.py`, `bridge_events_handler.py`, `flash_loan_events_handler.py`,
      `aggregator_route_handler.py`, `solana_defi_handler.py`, `lending_indices_handler.py`) — mirror the exact pattern
      already shipped for `dex_pools_handler.py`/`risk_params_handler.py`/`lst_rates_handler.py`
      (`market-tick-data-service@927acf01`): compute `_run_tag` from `args.run_tag` and pass
      `mode=('live' if     _run_tag == 'live' else 'batch')`. Add one regression test per handler asserting the actual
      `mode=` kwarg received across default/`--run-tag batch`/`--run-tag live`. Repo: market-tick-data-service. **Done
      when**: all 9 handlers explicitly thread `mode=`, one new regression test per handler passes verifying the
      received kwarg across all 3 run-tag states, `bash scripts/quality-gates.sh --no-fix` is green. Source:
      `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`.
- [ ] [CHORE] P1. Fix the stale EULER_V2-ARBITRUM phase-dict comment in
      `unified-api-contracts/unified_api_contracts/registry/defi_venues.py` (~line 508: claims "no UAC subgraph_id
      registered" — factually wrong since real Goldsky `SUBGRAPH_IDS` were registered and verified GREEN since
      2026-06-02). Replace with the real reason (mirroring the accurate EULER_V2-ETHEREUM sibling entry's wording:
      `euler_v2.py`'s reference-data adapter is Ethereum-only). Leave the FLUID-ARBITRUM half and the `"pipeline"` value
      untouched — comment-text-only fix. Repo: unified-api-contracts. **Done when**: the comment no longer claims "no
      UAC subgraph_id registered" and states the real Ethereum-only-adapter reason instead; `quality-gates.sh` green; no
      other lines changed. Source: `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`.
- [x] ✅ [INFRA] P1. **DONE 2026-07-26 (slot-7) — original symptom NOT recurring; job healthy in the sense that
      matters.** Diagnose and, if still broken, fix the `uts-prod-data-status-rollup` Cloud Run Job — as of 2026-07-10
      Cloud Scheduler had been firing into `UNAVAILABLE` (gRPC 14) since 2026-07-05T15:53Z. FIRST check current job
      health (`gcloud run jobs executions list`, blob `last_modified` on
      `gs://{pid}-data-status-rollups/market-tick-data-service/full.json.gz`) — a separate active plan
      (`infra_ops_residual_migration_verification_2026_07_24.md`) records the same job manually restarted around
      2026-07-24 for a DIFFERENT root cause (pinned image lag); if already healthy, record that and stop — do not
      duplicate the other plan's fix. If still erroring with the original symptom, diagnose + fix. Repo:
      deployment-service. **Done when**: either (a) the most recent execution succeeded and the rollup blob's
      `last_modified` is within ~10 min, confirming resolution, OR (b) the issue doc's Progress Log records the job was
      already healthy and only the separate image-staleness item remains open. Source:
      `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`. **Note (2026-07-26 correction)**: the job is
      actually the Cloud Run SERVICE `uts-prod-data-status-rollup-svc` + scheduler `uts-prod-data-status-rollup-cron`
      (there is no Cloud Run JOB by this name — `gcloud run jobs executions list` returns nothing because it's the wrong
      resource type; the todo's own command was mis-specified). Full diagnosis in the Progress Log below — original
      UNAVAILABLE/gRPC14 is gone; current DEADLINE_EXCEEDED/gRPC4 on the scheduler's own client-side wait is cosmetic
      (the backend keeps running past it and completes for ~12/14 services every cycle); the one real pre-existing gap
      (market-tick-data-service) is a KNOWN, already-tracked limitation, not new breakage.
- [ ] [DATA] P1. Measure the scale of bare-symbol-leaf DeFi batch writes since 2026-07-20 — run a bounded per-day GCS
      delimiter descent (not a corpus walk) over
      `raw_tick_data/by_date/day={YYYY-MM-DD}/pipeline_mode=batch_*/asset_group=defi/` for every day from 2026-07-20
      through the run date, and for each `pipeline_mode` count objects whose filename leaf does not equal the row's
      `instrument_id` (fails the UAC oracle's `canonical_path_violations()` id-form check,
      `_ID_FORM_CHECKED_ASSET_GROUPS={"cefi","defi"}`). Read-only; use the shipped oracle, do not reimplement it. Repos:
      unified-api-contracts (import only, read-only), market-tick-data-service (read-only). **Done when**: a
      per-pipeline_mode, per-day object count + id-form-violation count covering 2026-07-20 through the run date is
      written to a new results file and cross-linked from the source issue doc. Source:
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`.
- [ ] [BACKEND] P1. Fix `write_defi_rows()`'s filename-leaf construction to use the full `instrument_id`, not the bare
      `symbol` column — in `market-tick-data-service/.../canonical_write.py`, `write_defi_rows()` currently discards the
      `df.groupby("instrument_id")` key and rebuilds the leaf from only `group_symbol`. Change it to build the leaf from
      the sanitized `_inst_id` instead, so filename stem == the `instrument_id` column == the manifest key, per
      `cross-asset-canonical-target-ssot.md` §0/§1's hard rule. Scope is limited to the existing `instrument_id` column
      — do NOT wire the not-yet-populated `canonical_instrument_id` column (separate unbuilt-prerequisite item). Repo:
      market-tick-data-service. **Done when**: the leaf is built from the sanitized full `instrument_id`; a fresh sample
      of newly-written DeFi objects (all 6 handlers routing through `write_defi_rows`) passes the UAC oracle's id-form
      check with 0 violations; new/updated regression test passes; `quality-gates.sh` green. Source:
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`.
- [ ] [DOC] P1. Correct `canonical-cutover-register.md` §5's blanket "DeFi capture is STOPPED / no new defi writes"
      premise — measurably false for the batch lane (`pipeline_mode=batch_onchain_subgraph`/`batch_chainlink`/
      `batch_onchain_rpc`/`batch_aave` objects measured with `time_created=2026-07-24`). Narrow the claim to the
      live/websocket lane specifically, or substitute the measured fact that batch capture is actively writing. Repo:
      unified-trading-pm. **Done when**: §5 no longer makes an unqualified "no new defi writes" claim contradicting the
      measured batch-lane activity, with a cite to the source issue doc's Fact 1. Source:
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`.
- [ ] [DOC] P1. Correct the stale "oracle id-form check is tradfi-only" claim in
      `four-surface-reconciliation-procedure.md` §4/§4.3 and `reconciliation-finding-taxonomy.md` §2.2 — the check has
      covered cefi+defi by default since `unified-api-contracts@d40c5d7d` (refined `@1cd27478`). Update both docs' scope
      statements to `{tradfi, cefi, defi}`, and correct their shared worked example (`ADAF0:USTF0.parquet`, cited as "0
      violations == CANONICAL, false-clean") to note it now returns a real violation, or replace it. Repo:
      unified-trading-pm. **Done when**: both docs state the check covers
      `_ID_FORM_CHECKED_ASSET_GROUPS={tradfi,cefi,defi}`; the shared example is corrected or replaced. Source:
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`.
- [ ] [INFRA] P1. Apply the already-shipped `,`→`;` + `^;^`-delimiter metadata-parsing fix (live in
      `launch-mtds-dex-pools-backfill-vm.sh` and `launch-mtds-dex-swaps-backfill-vm.sh`) to
      `deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh`'s `VM_LENDING_PROTOCOLS` metadata
      construction — identical bug shape (comma-separated `--lending-protocols` collides with gcloud's default
      `,`-delimited `--metadata` parsing), latent because this launcher has only ever been exercised single-protocol.
      Repo: deployment-service. **Done when**: the launcher joins metadata pairs with `;` and passes
      `--metadata="^;^${METADATA}"`; invoking it with a comma-separated `--lending-protocols` value no longer throws
      gcloud's `Bad syntax for dict arg`; single-protocol behavior unchanged. Source:
      `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`.
- [ ] [BACKEND] P1. Rename the onchain feature_group keys in unified-api-contracts' two vocabularies not updated during
      the writer/CLI-name ratification (`unified-api-contracts@e9faf32e`) — `FEATURE_REQUIRED_INPUTS`
      (`required_inputs.py`) and the feature_group refs in `_feature_contracts.py` — from old registry names
      (`aave_lending_rates`, `aave_utilization`, `aave_risk_params`, `lst_staking_yields`, `eigen_rewards`,
      `aave_rate_impact`) to ratified names (`lending_rates`, `utilization`, `risk_params`, `lst_yields`, `rewards`,
      `rate_impact`), and drop `onchain_regime`/`defillama_tvl`/`protocol_rewards` (dropped from the main registry, no
      writer dispatch); update consuming tests. Repo: unified-api-contracts. **Done when**:
      `rg -i     'aave_lending_rates|aave_utilization|aave_risk_params|lst_staking_yields|eigen_rewards|aave_rate_impact|onchain_regime|defillama_tvl|protocol_rewards'`
      over both files returns zero hits; `quality-gates.sh` green. Source:
      `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`.
- [ ] [SCRIPT] P1. Add a machine check to e2e-testing that imports the onchain feature_group vocabulary from
      unified-api-contracts' `FEATURE_GROUP_TO_FAMILY`, features-service onchain CLI's `FEATURE_GROUPS`, and
      ml-service's `DEFI_FEATURE_GROUPS`, using the same cross-repo `sys.path` pattern e2e-testing already uses in
      `scripts/defi/colocated_engine.py`, computes pairwise set differences, and prints/asserts a diff report. Repo:
      e2e-testing. **Done when**: a new script/pytest exists that runs standalone, imports all three vocabularies, and
      reports pairwise set differences (verified by running it once); wired into e2e-testing's `quality-gates.sh` if a
      test, lifecycle-marked if a script. Source:
      `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`.
- [ ] [DIAG] P1. Verify the 2 unverified signals in the issue doc's §8: (a) sample onchain feature parquets under
      `gs://features-defi-prd-.../onchain/` (e.g. day=2026-03-05, day=2026-05-20) for exact duplicate rows (same
      timestamp+instrument_id repeated); (b) trace where `instrument_count` is computed in the onchain manifest-write
      path and determine why `onchain/_index/availability_index.parquet` shows the identical value 14,630,914 across six
      distinct feature_groups — confirm a true per-group count vs a shared/global count bug. Investigation only, no fix.
      Repos: features-service, unified-trading-library (read-only). **Done when**: a written finding is appended to the
      issue doc stating a definitive yes/no for (a) with sampled evidence, and the concrete code-level root cause for
      (b) (or that it could not be determined and why). Source:
      `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`.
- [ ] [DATA] P1. Re-run the HYPERLIQUID `trades` batch backfill with the current (fixed, `@c48096e7`) parser/routing
      code, force/overwrite over 2025-05-25..2025-07-27 (legacy `node_fills`) and 2025-07-28..today
      (`node_fills_by_block`) — do NOT expect 2025-03-22..2025-05-24 to populate (confirmed genuine upstream absence).
      Monitored SPOT backfill per the VM-launcher runbook (HYPERLIQUID exempt from the Tardis cap); no fire-and-forget.
      Repo: market-tick-data-service. **Done when**: the cefi `_index/availability_index.parquet` shows real captured
      HYPERLIQUID trades rows across both windows (post-force-rerun) with the pre-existing
      `empty_confirmed`/`SOURCE_RETURNED_ZERO` status cleared, and 2025-03-22..2025-05-24 correctly left empty. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.
- [ ] [BACKEND] P1. Delete the retired perp_funding DeFi-routing residue: remove the stale `hyperliquid`/`aster`/
      `lighter` entries from `_PROTOCOL_PIPELINE_SOURCE` (`perp_funding_handler.py:188-194`) and `_chain_map`
      (`:244-249`), delete the spent one-off script `scripts/backfill_hl_funding_from_s3_asset_ctxs_2026_06_17.py` (past
      its own `# Delete-when:` marker). Verify the `protocols` iterable no longer includes hyperliquid/aster/lighter
      before deleting the entries. Repo: market-tick-data-service. **Done when**: `perp_funding_handler.py` no longer
      routes those 3 venues through the defi bucket, the script file is deleted, `quality-gates.sh` green. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.
- [ ] [BACKEND] P1. Add the missing `Mode.REPLAY` case to `possible_manifest._canonical_pipeline_mode_prefixes` in
      unified-api-contracts so it also emits `replay_<source>/` prefixes alongside `Mode.BATCH`/`Mode.LIVE`, closing a
      latent gap in the phantom-shard auditor (additive, 1-line-class, no-risk future-proofing). Confirm
      `test_possible_manifest`'s prefix-count guard is quiescent before landing. Repo: unified-api-contracts. **Done
      when**: `_canonical_pipeline_mode_prefixes` iterates `(Mode.BATCH, Mode.LIVE, Mode.REPLAY)`; the prefix-count
      guard passes; `quality-gates.sh` green. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.
- [ ] [DIAG] P1. Run a real past-day EXTENDED-STARKNET `book_snapshot_5` backfill and a real current-day run against the
      shipped fix (`@55dac12a`, current-only-endpoint honest-skip) — confirm the past-day run produces 0 book rows with
      no fabricated HTTP/timestamp (honest absence) and the current-day run produces a real live current book row via
      the WS connector. Repo: market-tick-data-service. **Done when**: both runs are observed on real infra with the
      expected 0-past-row / real-current-row outcome, recorded in the doc's Progress Log. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.
- [ ] [DIAG] P1. Re-verify the LIGHTER-ZKSYNC Tardis exchange-slug + numeric market_id fix
      (`market-tick-data-service@0c4000a02`) against a real, free-tier-compatible first-of-month historical date to
      confirm real `trades`/`book_snapshot_5`/`derivative_ticker` rows still return. Repo: market-tick-data-service.
      **Done when**: a live Tardis probe on a first-of-month date for LIGHTER-ZKSYNC returns real, correctly-shaped rows
      for all 3 data types using current code, recorded in the doc's Progress Log. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.
- [ ] [DIAG] P1. Investigate (live API probe) whether EXTENDED-STARKNET's `/info/markets/{symbol}/trades` endpoint's
      descending cursor can actually walk back to historical (non-today) dates — the endpoint takes no
      `startTime`/`endTime` param and 0 trades rows of any capture_status exist at any date. Repo:
      market-tick-data-service. **Done when**: a live probe either confirms deep cursor-walking reaches a real
      historical date (record how far back) or confirms it structurally cannot, recorded in the doc's Progress Log.
      Source: `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.
- [ ] [DATA] P1. Diagnose (and ship a fix ONLY if a clear, undisputed one-line correction — otherwise document + stop)
      why the onchain `availability_index` manifest consolidator is a measured no-op: 13 index rows frozen at
      `date=2026-01-25` while GCS objects exist through 2026-05-22, a fresh scan measures `shards_scanned=1/rows_in=0`
      against 723 live onchain objects. Trace the onchain index-update/consolidator code path (repos:
      unified-trading-library, market-tick-data-service — grep-then-read, do not guess) and produce a written root
      cause. As part of the SAME investigation, explicitly reconcile against `defi_consolidated_closeout_2026_07_18.md`
      Track 8's 2026-07-22 correction claiming the manifest consolidator is "ENABLED, running every 1 minute,
      unaffected" — state whether this is the same consolidator process, and if so reconcile the apparent contradiction
      (or state it genuinely conflicts) — do NOT silently pick a side. Do NOT hand-edit `availability_index.parquet`
      directly. **Done when**: a dated Update section is added to the issue doc with the root cause + evidence (or
      "inconclusive, here is what was ruled out") and the Track 8 reconciliation explicitly stated; IF the root cause is
      a trivial undisputed fix, it may additionally be shipped + verified (re-scan shows `shards_scanned>1`/`rows_in>0`,
      index reflects dates beyond 2026-01-25); otherwise remediation stays open pending a human design decision and the
      todo completes on the documented diagnosis. Source:
      `issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`.
- [ ] [DATA] P1. Diagnose (and fix ONLY if a clear code bug) the implausible identical `instrument_count=14,630,914`
      reported across 5 different onchain feature_groups (health_factor, rewards, liquidation_events, risk_params,
      flash_loan_availability) plus lending_rates in the onchain availability_index — a per-group count shouldn't be
      identical across unrelated groups. Trace the count-aggregation/derivation code path and either fix the
      broadcast/join bug or document why the shared count is legitimate. Repos: unified-trading-library,
      market-tick-data-service. **Done when**: a written root cause is added to the issue doc as a dated Update, with
      either a shipped + verified fix (re-derived index shows distinct plausible counts) or a documented reason the
      shared count is legitimate. Source: `issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`.
- [ ] [DATA] P1. Investigate + file the `lst_yields` coverage-extension follow-up — confirm the real GCS date-coverage
      gap between features-onchain `lst_yields` (~15 days total as of 2026-07-23) and the underlying MTDS `lst_rates`
      raw corpus for the same EVM tokens (plausibly a features-layer compute lag, not raw-data absence — verify against
      real GCS, don't assume), then file a new dated issue doc proposing the concrete backfill scope (owning repo, date
      range, mechanism). Do NOT implement the backfill. Repo: unified-trading-pm (read-only GCS checks against
      features-service/market-tick-data-service, no production code changed). **Done when**: a new dated issue doc
      exists under `plans/active/issues/` citing exact GCS-verified coverage date ranges for both `lst_yields` and
      `lst_rates` per relevant EVM token, cross-linked from this doc's deferred-work row. Source:
      `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`.
- [ ] [SCRIPT] P1. Diagnose the root cause of the 2026-06-28 defi phantom-capture batch-writer failure (219,529 manifest
      rows recorded `captured` with no backing parquet — concentrated in the 7 `swaps_ohlcv_*` granularities at ~25,400
      each, plus 20,586 `dex_pool_swaps` and 12,249 `gas_fees`/ALCHEMY, UNISWAP_V4 largest venue at 69,573). Pull DeFi
      OHLCV batch-writer logs/git history for the affected window and determine whether the writer logged `captured`
      before crashing pre-flush. Note: the capture-BATCH model this writer belonged to was RETIRED 2026-07-18/19 for a
      per-instrument writer re-architecture — if the implicated code path no longer exists or logs expired, that is
      itself a valid, documentable finding (do not force a live fix on retired code). Repo: market-tick-data-service
      (read-only log/git investigation). **Done when**: either (a) a documented root-cause finding (citing log
      excerpts/commit) is recorded as an update in the issue doc, or (b) it is confirmed and documented that retroactive
      diagnosis is no longer possible because the writer was retired and/or logs expired — either outcome closes this
      todo; no live code fix required. Source: `issues/phantom_captures_defi_2026_06_28.md`.
- [ ] [VERIFY] P1. Confirm whether adding a data_type to `DATA_TYPES_BY_ASSET_GROUP["defi"]` (for an already-registered
      venue×instrument_type combination) actually changes expected_unattempted materialisation / completeness_pct, or
      whether that denominator is scoped independently — small, cheap, read-only check mirroring the equivalent
      venue-axis check already run in `distinct_values_noncanonical_audit_2026_07_20.md` RESULT 4. Repo:
      unified-api-contracts (read-only). **Done when**: a finding is written (appended to the issue doc's Progress Log)
      stating definitively — via a read-only code trace and/or a scoped enumerator test — whether registering
      `perp_daily_ctx` for the already-registered HYPERLIQUID/CeFi combinations would mint new expected_unattempted rows
      or move completeness_pct (NOTE: GMX dropped from this combination list — REMOVED 2026-07-25, see
      `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`). No code/schema/manifest changes made. Source:
      `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`.
- [ ] [DATA] P1. **Resolve the Kamino/Solend `lending_indices` `instrument_type` shape conflict — probe BOTH candidate
      paths.** `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` item 4 left this
      "inconclusive, not a clean bill": its own targeted shape (`instrument_type=solana_lending`, per
      `lending_indices_handler.py::resolve_lending_instrument_type()`) conflicts with
      `defi_consolidated_closeout_2026_07_18.md` Track 2's independent 2026-07-20 live GCS probe, which found 47 real
      KAMINO `lending_indices` objects under `instrument_type=solana_amm_pool` instead. Operator ruling 2026-07-25
      (queued entry #3 in `issues/autonomous_session_operator_decisions_2026_07_25.md`, answered): probe BOTH shapes and
      explicitly reconcile against the 47-object Track-2 finding before filing any verdict — do not conclude "clean
      bill" from checking only `solana_lending`. Repo: market-tick-data-service (read-only probe). Source:
      `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` item 6 (added 2026-07-25 per the
      operator's ruling). **Done when**: both `instrument_type=solana_lending` and `instrument_type=solana_amm_pool` are
      sampled for real KAMINO/SOLEND objects (uri + timestamp-vs-day= check, same method as items 4/5 in the source
      doc), the 47-object Track-2 population is accounted for, and a definitive verdict (clean / same fabrication bug as
      the dex_pools class / a different issue) is recorded in the source doc.

## Progress Log

- **2026-07-26 (slot-7)** — Diagnosed the `uts-prod-data-status-rollup` todo. **Resource-type correction**: it's a Cloud
  Run SERVICE (`uts-prod-data-status-rollup-svc`) fronted by Cloud Scheduler (`uts-prod-data-status-rollup-cron`,
  `*/20 * * * *`), not a Cloud Run JOB — `gcloud run jobs executions list` (the todo's own suggested command) returns
  nothing because it's the wrong API surface; `gcloud scheduler jobs describe` + `gcloud run services describe` are the
  right tools.
  - **Original symptom (UNAVAILABLE / gRPC 14, since 2026-07-05) is NOT recurring.** Current scheduler `status.code: 4`
    (DEADLINE_EXCEEDED) is a DIFFERENT code — the scheduler's own client-side HTTP wait (`attemptDeadline: 900s`,
    matching the Cloud Run `timeoutSeconds: 900`) times out, but Cloud Run does not kill the backend request just
    because the caller stopped waiting — confirmed by reading live `Creation Time` timestamps on
    `gs://central-element-323112-data-status-rollups/{service}/full.json.gz`: 12 of 14 `_DEFAULT_SERVICES` got a FRESH
    rollup within the same ~40min cycle (20:43–21:20 UTC), including `strategy-service` and `execution-service` (the
    LAST two in the worker's sequential processing list) — direct proof the backend keeps running to completion for the
    achievable set regardless of what the scheduler's own status field reports.
  - **market-tick-data-service is the one persistent gap — and it's a KNOWN, already-tracked limitation, not new
    breakage.** `plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md` already documents
    MTDS's full-2018-today manifest build as exceeding any sane per-child memory ceiling ("no RAM tier through 64GB
    survives it") — the per-service child-process isolation fix from that plan (`RLIMIT_AS` 24Gi) stops MTDS's failure
    from blocking OTHER services (confirmed here: MDPS, right after MTDS in the processing order, DOES succeed — direct
    evidence the isolation fix still holds), but MTDS's own rollup was never expected to succeed until the real fix
    (`/plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md`, still active) lands. This matches the todo's
    own "Done when (b)" branch: the job is healthy for what it can do; the remaining gap is a separately-owned,
    already-tracked item, not this todo's to fix.
  - **New finding along the way (filed, not fixed here)**: `ml-service`'s `full.json.gz` is ALSO missing (only
    `coverage.json.gz` exists), but unlike MTDS this is NOT explained by the known OOM class — both services processed
    AFTER ml-service in the sequential list (strategy-service, execution-service) succeeded in the same cycle, ruling
    out a simple "loop got cut off here" explanation. Filed
    `issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md` (P2, `assigned_vm: planning`, 2 scoped todos:
    re-confirm across more cycles, then root-cause the coverage-vs-full divergence) rather than open-ended debugging
    with only 16 log entries/2h to go on from this vantage point.

## Deferred

### Excluded — doc flagged `doc_too_large_or_risky_for_batch: true` (1 doc) — RE-CHECKED 2026-07-25, still excluded

- `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md` — flagged too-large/risky for a batch todo and
  excluded entirely (its sole AO-eligible candidate is deferred with it, per the batch-authoring rule that a flagged
  doc's candidates never ship regardless of how clean they individually look). Re-checked fresh 2026-07-25 (ahead of
  finalize-plan todo 2, since batch1 itself hasn't been dispatched yet): its item 2 (4 zero-capture protocols) is
  SUPERSEDED — already wired 2026-07-14, verified 2026-07-24, follow-up already covered by this same plan's
  `dex_swaps_handler.py` combined todo above. Its item 1 (second writer path historical migration) is STILL genuinely
  too-large/risky — unchanged since 2026-07-10, still needs its own dedicated design/scoping pass, not a batchN slot. No
  batch2 item drafted from this doc. Full re-check written into the source doc's own 2026-07-25 Update section.

### Excluded — same-doc gated/judgment items (2 items, from `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`)

- **[CODE] P2. Register `perp_daily_ctx` as its own canonical data_type + SchemaContract** (gated on the kept VERIFY
  todo above) — excluded because the doc's own text explicitly self-flags needing "operator awareness before autonomous
  execution," citing this same parent plan's established "UAC canonical-set additions are not safe-code" precedent (a
  canonical data_type addition can silently expand the historical expected_unattempted universe and drop fleet-wide
  completeness_pct, and registers a new type in the schema surface read live by `CanonicalPerpFundingProvider`). This is
  judgment-laden, blast-radius-uncertain work the dispatch-scope rule excludes even when nominally sequenced after a
  VERIFY step.
- **[OPERATOR-DECISION] P3. Whether/when to execute the demote-`perp_funding`-to-a-derived-view design todo** in
  `defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md` — explicitly self-tagged
  `[OPERATOR-DECISION]`; that sibling doc's own triage independently classifies the underlying `[DESIGN] P1` todo as
  human_only ("textbook decide-the-right-approach work, not a bounded worker outcome"). Never AO-eligible per the
  dispatch-scope rule. **Queued 2026-07-25** as entry 4 in `issues/autonomous_session_operator_decisions_2026_07_25.md`
  rather than left with no path forward — status open, awaiting the operator.

**Re-checked 2026-07-25 (ahead of finalize-plan todo 1, since batch1 hasn't been dispatched yet):** the kept
`[VERIFY] P2` todo above (Source: this same doc) has **not actually executed** — no Progress Log finding exists in the
source doc, and it is still an unchecked `[ ]` bullet sitting in this still-`status: draft`, undispatched plan. The
excluded `[CODE] P2` item therefore remains correctly gated on a sibling todo that hasn't landed yet (not a
stale/resolvable conflict) — it cannot move to batch2 until batch1 actually dispatches and the VERIFY finding lands.

### Excluded — zero eligible candidates from the start (9 docs, no action needed)

`defi_lending_writer_retire_prerequisite_2026_07_20.md`, `defi_track5_coverage_mvp_backfill_2026_07_24.md`,
`issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`,
`issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`,
`issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`,
`issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md`,
`issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`,
`issues/mtds_lst_extended_rates_uncited_addresses_2026_07_19.md`,
`archive/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md` — each had zero AO-eligible
candidates at extraction time; see each doc's own rationale. Reworded 2026-07-25 (plan-reconcile) for accuracy:
`defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md` is NOT a 10th zero-candidate doc — it had 1 AO-eligible
candidate, deferred alongside it under the too-large-or-risky flag above (see that section). The frontmatter's "10
excluded docs total" tally is these 9 zero-candidate docs plus that 1 too-large doc, not 10 docs that each had zero
candidates.

### Needs operator ruling — RESOLVED 2026-07-25, moved into Todos above

`issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`'s sole candidate ("Determine whether the
dex_pools-class fake-history-snapshot bug also affects Kamino/Solend Solana lending_indices in the `-prd-` bucket") was
a genuine cross-doc contradiction (`instrument_type=solana_lending` per the writer code vs. an independent
`instrument_type=solana_amm_pool` live-probe finding, 47 objects, in `defi_consolidated_closeout_2026_07_18.md` Track
2). Filed as entry 3 in `plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`; the operator answered
same-day: probe both shapes before concluding. Widened + dispatched as a Todos-section item above (source doc also
updated with a new item 6 carrying the same widened scope).

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` (`depends_on: [defi_satellite_ao_dispatch_batch1_2026_07_25]`
— `gate_on_depends: true`), mirroring the cefi/tradfi/prediction batch1 finalize-plan pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc.
