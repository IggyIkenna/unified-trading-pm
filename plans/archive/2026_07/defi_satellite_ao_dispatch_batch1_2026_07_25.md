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
status: complete
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
    /plans/archive/2026_07/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
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

> **🟢 ARCHIVED 2026-07-30.** All 54 todos done. Source-doc reconciliation (29 distinct source docs, incl. the Track 2
> cross-flip) + the too-large-doc re-check + the operator-ruling re-check were all completed by the companion finalize
> plan's own todos 1-3. The Deferred section below (the too-large-doc exclusion, the 2 same-doc gated/judgment items,
> the 9 zero-candidate docs, and the resolved operator-ruling item) was independently re-verified 2026-07-30: every item
> remains genuinely tracked in its own source doc or the operator-decisions issue doc — nothing orphaned, nothing needed
> a fresh batch2 item. No new durable contract from this batch — codex-alignment check: nothing to update (every todo
> executed an already-decided spec). Archived via
> `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` (archived alongside this doc, same
> commit).

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
- [x] ✅ [CODE] P1. Implement Phoenix DEX radix-slab top-of-book decode in
      `market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py` — parse the Phoenix market-account slab
      layout (RPC fetch already works) to populate `best_bid_price`/`best_ask_price`/sizes/`spread_bps`/`mid_price`;
      replace `record_failed(reason="SOURCE_HANDLER_TODO_PHOENIX_DECODE")` with `record_captured` once decoded; add 5+
      unit tests against known slab states. Repo: market-tick-data-service. **Done when**: a successful fetch calls
      `record_captured` (not `record_failed`) with all 5 fields populated; >=5 new unit tests pass; `quality-gates.sh`
      green. Source: `data_completion_defi_2026_07_15.md`. — market-tick-data-service@ee49a76d. Layout verified against
      the on-chain `Ellipsis-Labs/phoenix-v1` + `sokoban` program source (MarketHeader, sokoban RedBlackTree slab,
      free-list-aware node walk), cross-checked against the official `Ellipsis-Labs/phoenixpy` SDK's own decode. Decodes
      bids/asks, aggregates size at the best price tick, excludes freed/tombstoned nodes and expired
      (`last_valid_slot`/`last_valid_unix_timestamp_in_seconds`) orders, then populates `bid_price`/`bid_size`/
      `ask_price`/`ask_size`/`mid_price`/`spread_bps` and routes via `record_captured`/`record_zero_rows` instead of the
      stub's `record_failed`. Added per-sample-per-day looping (mirroring the Orca/Raydium ingesters) since the stub's
      `samples_per_day` param was previously accepted but unused. 20 new unit tests
      (`test_phoenix_orderbook_handler.py`) cover known slab states incl. a freed-node-exclusion case and an
      expired-order-exclusion case. `quality-gates.sh` green (7092 tests). Hit and resolved a repo-blocker (RB-ef115f4a,
      `pipelinemode_missing_batch_defillama_member_2026_07_26.md`, now archived) from an unrelated concurrent commit
      before shipping.
- [x] ✅ [CODE] P1. Implement Orca Whirlpool tick-array binary decode in
      `market_tick_data_service/cli/handlers/orca_whirlpool_state_handler.py` — decode the 3 nearest tick arrays around
      the already-extracted `tick_current_index` (~150-200 LOC), captured per-snapshot alongside the existing pool-state
      row, so downstream consumers can compute fill slippage at arbitrary sizes. Repo: market-tick-data-service. **Done
      when**: per-snapshot tick-array state is captured and persisted alongside pool state; new unit tests cover the
      decode; `quality-gates.sh` green. Source: `data_completion_defi_2026_07_15.md`. —
      market-tick-data-service@f771e841. The 3 TickArray accounts nearest `tick_current_index` (previous/current/next)
      are located via Program Derived Address (PDA — seeds `"tick_array"` + pool pubkey + `start_tick_index` string
      against the Whirlpool program, same scheme the Orca SDK uses), fetched concurrently via the existing
      `solana_get_account_info_at_slot` primitive (no new RPC primitive needed), decoded, and persisted as a
      `tick_array_state` JSON column on the existing `dex_pool_state` row (`write_defi_rows` already passes extra
      columns through — no new UAC schema/data_type needed). This service has no `solders`/`solana-py` dependency, so
      PDA derivation (base58 codec + Ed25519 curve-membership check) is a small pure-Python reimplementation local to
      the handler, rather than adding a new crypto dependency for one handler. An uninitialized tick array (no liquidity
      ever placed there) is honest absence — an empty `ticks` list, never fabricated. 13 new unit tests cover: tick
      decode (incl. negative `liquidity_net` two's-complement, uninitialized-slot skipping, short-buffer rejection), the
      nearest-3 start-index math (incl. negative-tick floor division), base58 round trip, the Ed25519 on-curve check
      (verified against the curve-independent identity-point (0,1) invariant), PDA determinism/off-curve invariant, and
      the new `tick_array_state` column end-to-end. `quality-gates.sh` green (7269 tests, full run).
- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-10) — both sub-items already resolved by prior commits predating this plan;
      no code change needed.** (a) The DeFi expected-universe seeder's blank-`chain` bug for glued `PROTOCOL-CHAIN`
      venues (incl. the oracle-prices/perp-funding sub-buckets — `CHAINLINK-ETHEREUM`, `AAVE-ETHEREUM`,
      `AAVE_V3-ARBITRUM` A_TOKEN rows) was fixed in `instruments-service@b34416ee` ("fix(enum): v2 defi enumerator emits
      canonical venue=PROTOCOL + chain=X (was combined PROTOCOL-CHAIN/blank-chain, phantom expected_unattempted)"),
      landed 2026-06-22 — **before** this plan (2026-07-25) and its source doc (`data_completion_defi_2026_07_15.md`,
      2026-07-15). The fix lives in `scripts/enumerate_expected_universe.py`'s `_enumerate_v2_defi` (not
      `engine/orchestrator/defi.py`, which only assembles the venue-fetch list — no EU-seeding logic lives there),
      splitting a blank-`chain` glued venue on its trailing `-` into `(canonical_venue, chain_upper)` before every
      `ExpectedRow` yield. Verified live via a synthetic reproduction against the current `_enumerate_v2_defi` (not a
      whole-corpus walk): a `CHAINLINK-ETHEREUM` SPOT_PAIR row and an `AAVE_V3-ARBITRUM` A_TOKEN row
      (oracle_prices/perp_funding data_types) both yield `chain='ETHEREUM'`/ `chain='ARBITRUM'` — never blank. (b) The
      tz-naive/tz-aware comparison crash in `_enumerate_v2_prediction` was fixed in `instruments-service@b90bc2d9`
      ("fix(scripts): fix tz-naive/tz-aware comparison crash in prediction v2 enumerator"), landed 2026-07-10 — also
      before this plan/source doc — via the identical `tz_localize(None)` normalization pattern the todo describes,
      already present at the current
      `af_ts = af_raw.tz_localize(None) if (af_raw is not None and af_raw.tzinfo is not None) else af_raw` (and the
      `at_ts` sibling). Verified live: `enumerate_v2(asset_group="prediction", ...)` against a synthetic catalogue entry
      with tz-aware `market_created_at`/`settlement_time` ISO strings completes with zero `TypeError` and reports a
      candidate count (2 rows for a 2-day window). No `quality-gates.sh` run needed (read-only verification, zero lines
      changed). Source: `data_completion_defi_2026_07_15.md`,
      `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`.
- [x] ✅ [BACKEND] P1. **Combined `market-tick-data-service/.../lst_rates_handler.py` fix — sub-item (b) DONE 2026-07-26
      (slot-14), sub-item (a) DONE 2026-07-26 (slot-2).** (a) both `pipeline_mode_for_source("onchain_subgraph", ...)`
      call sites (~line 351 and ~447) hardcoded the source string for EVERY Solana LST row regardless of which tier
      actually produced it — the per-row `method` field (written by `solana_lst_archival.py`) already tracks
      `alchemy_get_account_info` / `thegraph_subgraph` / `rest_api` / `defillama_historical_ratio`, so Tier-4
      `defillama_historical_ratio` rows (a market-price proxy, NOT genuine on-chain data) were getting the same
      `batch_onchain_subgraph` label as genuine Tier 1-3 rows. Fixed by deriving the pipeline_mode per WRITTEN SHARD
      from that shard's own `method` column instead of a single hardcoded call: added `PipelineMode.BATCH_DEFILLAMA` (+
      `SOURCE_PRIORITY[("defi","lst_rates")]` fallback entry, `SOURCE_MODE_CAPABILITY`, `EMISSION_LATENCY_MS_BY_SOURCE`)
      in `unified-api-contracts@f7019ffb`; `_write_single_lst_group()` in `market-tick-data-service@45a9fe69` picks
      `batch_defillama` when a shard's rows are ALL `defillama_historical_ratio`, else keeps the unchanged
      `batch_onchain_subgraph` label (covers the EVM path too, which never carries that `method` value — stayed
      byte-identical, no tier-fallback system touched). The `_check_preflight` (~line 447) call site was deliberately
      left untouched — it fires before any row/tier is resolved (catalog-unavailable gate for all 4 sentinels), so there
      is no per-row tier to derive from there; the "Remaining done when" criterion below is scoped to actually-WRITTEN
      rows only. `defillama` is BATCH-only (mirrors `aave`'s precedent) — `_finalize_lst_rows` defensively falls back to
      the unchanged label rather than raising if this handler ever runs in live mode (no `LIVE_DEFILLAMA` member
      exists). Regression test added: `test_tier4_solana_row_gets_distinct_pipeline_mode` in
      `test_lst_rates_handler_coverage.py` (asserts EVM + Tier1-3 Solana → `BATCH_ONCHAIN_SUBGRAPH`, Tier-4 Solana →
      `BATCH_DEFILLAMA` in the same `process()` run). Both repos' `quality-gates.sh` green. (b) ✅ **DONE 2026-07-26
      (slot-14, done as a prerequisite of `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s residual-emitter todo,
      which discovered this was still unshipped despite that plan's premise that it was already fixed excluding the
      residual path).** `_write_single_lst_group()` now loops `write_defi_rows()`'s per-instrument `shards` and calls
      `record_captured(instrument_id=..., row_count=...)` once per shard instead of one (protocol, chain) aggregate with
      no `instrument_id` — mirrors `record_swap_pool_map()`/`record_market_captures()`/`_record_manifest_result()`. The
      residual/empty path (originally out of THIS todo's scope, per its "do not touch" framing — it belongs to
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s residual-emitter todo) was wired in the SAME session/commit
      since batch2's todo genuinely depends on this fix landing first. Split the write functions into a new
      `_lst_rates_write.py` sibling module (codex 900-line ratchet). Extended the existing captured-path test with an
      `instrument_id` assertion. `market-tick-data-service@9d796b0e`, `quality-gates.sh` green. **Repo:
      market-tick-data-service + unified-api-contracts.** Source: `defi_strategy_pnl_axis_index_2026_07_24.md`,
      `lst_rate_honest_coverage_2026_07_21.md`,
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`.
- [x] ✅ [BACKEND] P1. **DONE 2026-07-27 (slot-14).** Fixed `_perp_funding_kalshi_polymarket.py`'s
      KALSHI_PERP/POLYMARKET_PERP routing in market-tick-data-service: both venues now route through a cefi-classified
      write path (`_write_cefi_perp_funding_rows()`, mirroring `onchain_perp_batch_handler.py`'s `asset_group='cefi'`
      `ManifestWriter` precedent — new UAC `build_cefi_partition_path`/`build_instrument_id`-based per-instrument
      sharder, no chain axis) instead of DeFi-only `write_defi_rows`; `DefiManifestRecorder` gained an `asset_group`
      param (default `"defi"`, ~25 other callers unchanged) and `perp_funding_handler.py` now constructs it with
      `asset_group="cefi"` + resolves the cefi bucket; `source` is now explicitly `_source_for_protocol(protocol)` on
      every `record_captured`/`record_zero_rows`/`record_failed`/`record_empty` call (was blank, silently auto-stamping
      the wrong single-source `"hyperliquid"` default). 71/71 targeted unit tests pass; `quality-gates.sh` green
      (265-497s across runs). **Manifest cleanup executed and verified against prod**:
      `scripts/remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py` removed the 8 pre-existing stale rows (4
      KALSHI_PERP `captured` + 4 POLYMARKET_PERP `attempted_failed`, all mis-stamped `source="hyperliquid"`) —
      26,540,325 → 26,540,317 rows, pre-apply backup snapshot taken, post-write verification confirmed zero remaining
      KALSHI_PERP/POLYMARKET_PERP rows. market-tick-data-service@2aa23de5 (writer fix),
      market-tick-data-service@6998ea4c (cleanup script's final streaming-rewrite, after the original pandas-based
      version proved unsafe on this contended host — see Progress Log entry below). Source:
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-2).** Measured the exact scope of MTDS manifest rows stamped
      `instrument_type="liquidation"` by the pre-fix `liquidations_handler.py` code path (before
      `market-tick-data-service@fec20de2`) via a live read-only probe of prod
      (`market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, 26,797,412 total rows): **0
      rows currently carry the buggy literal** — 7,106 rows carry `data_type=liquidations` (7,047 already
      `instrument_type=lending`, 59 `None` via the `record_zero_rows` fallback path, out of scope by construction). A
      genuine measured-zero, not a placeholder — the pre-fix window's captures (if any landed) have since fully cycled
      out. Built `market-tick-data-service/scripts/restamp_lending_instrument_type_2026_07_24.py` mirroring the
      `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py`/`restamp_sports_odds_horizon_bucket_2026_07_22.py` safety
      pattern (dry-run default, `--apply` CAS-guarded, pre-apply snapshot, post-write verification), cross-checking each
      affected row's `venue`-derived protocol against the REAL `_lending_grain.resolve_lending_instrument_type()`
      (imported, never re-implemented) to confirm genuine lending mislabeling. Adapted for memory safety per
      `remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py`'s documented OOM finding on this same 26.8M-row/~1GB
      index: `classify()`/`build_final()` operate only on the small `data_type=liquidations` candidate subset, the full
      corpus is only ever touched via `ParquetFile.iter_batches()` + a streaming `ParquetWriter`. 27 unit tests
      (classification/collision-detection, streaming dry-run/apply helpers, `try_once()` end-to-end against a fake
      CAS-aware storage client) all pass. `quality-gates.sh` green (sentinel verified). Shipped via quickmerge —
      market-tick-data-service@be064c27, verified ancestor of `origin/live-defi-rollout`
      (`rev-list --count HEAD     ^origin/live-defi-rollout` = 0). Script remains **un-applied** at hand-off — `--apply`
      stays operator-gated on a paused-consolidator-cron window (this plan's separate `[OPERATOR]` todo). Repo:
      market-tick-data-service. Source:
      `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`.
- [x] ✅ [CHORE] P1. **DONE 2026-07-30.** Replaced the stale `onchain/__init__.py` module docstring with the corrected
      text drafted and verified in the source issue doc §2.2 (documents `GlassnodeAdapter` as `PLANNED_VENUES`-parked
      and `HeliusSolanaAdapter` as `BLOCKED-CREDENTIALS`-gated, replacing the stale 2026-04 "all adapters deleted"
      claim), verbatim. Confirmed no concurrent WIP in the file/package before editing (clean `git status`). Shipped
      `market-tick-data-service@0cd76b93`, `quality-gates.sh` green (sentinel-verified). Source:
      `issues/defi_adapter_dead_code_audit_2026_07_24.md`.
- [x] ✅ [DIAG] P1. **DONE 2026-07-27 (slot-11) — no code shipped (diagnostic-only todo).** Traced whether
      `market_interface/adapters/defi/curve_adapter.py::_download_liquidity`'s broad `except Exception: ... return []`
      (~line 682) is distinguishable, in `base_defi_adapter.py`'s per-instrument loop's `if not result: continue`
      success/failure accounting, from a genuine zero-liquidity-snapshot day. **CONFIRMED MASKING** — quoted the full
      4-hop caller chain (curve_adapter.py → base_defi_adapter.py) proving a broad-except failure and a genuine empty
      day both produce `result = {"dex_pool_state": []}`, a non-empty (truthy) dict that never trips
      `if not result:     continue`, so the instrument is counted `succeeded` with zero rows either way. Finding
      appended to `issues/defi_adapter_dead_code_audit_2026_07_24.md` §2.3. Also surfaced + filed as its own issue doc a
      broader, cross-adapter version of the same gap (~12 adapters' `{"success": False, ...}` signal is never read by
      the same caller): `issues/defi_base_adapter_success_key_ignored_by_failure_accounting_2026_07_27.md`. Source:
      `issues/defi_adapter_dead_code_audit_2026_07_24.md`.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-11).** **Combined `market-tick-data-service/.../dex_swaps_handler.py` fix
      (2 sub-items merged into one todo — both would EDIT the same file, different venues/bugs):** (a) classify the
      CURVE/OPTIMISM "no allocations" GraphQL response as a distinct terminal condition at fetch time — SHIPPED
      `market-tick-data-service@dddd1b21`: `_execute_subgraph_query` now detects the `"no allocations"` fingerprint and
      raises `_SubgraphDeindexedError` (fails fast on the first cascade attempt instead of burning all 5 — the condition
      is subgraph-level, not query-shape), caught in `_collect_one_shard` and routed to
      `record_empty(reason=EmptyConfirmedReason.EXPECTED_SUBGRAPH_DEINDEXED)` instead of `record_failed`. Proven via 9
      new unit tests (fingerprint detector, `_execute_subgraph_query` raising, `_run_cascade` fail-fast propagation, the
      full outer-loop `process()` → `record_empty` path) — all green, plus the live-reproduced exact CURVE/OPTIMISM
      GraphQL error confirmed via direct `gateway-arbitrum.network.thegraph.com` probe. (b) TRADER_JOE_V2 —
      **live-verified NO code fix was actually needed**: the existing cascade's 2nd variant (`messari_from`) already
      matches the live subgraph schema exactly (introspection-confirmed) and returns real, non-empty swap rows on 3
      sample dates spanning the target range (2023-01-15, 2023-09-01, 2024-09-01, direct `gateway.thegraph.com` probe
      with a Secret-Manager TheGraph key). Launched the scoped SPOT backfill VM `mtds-dex-swaps-historical`
      (`--protocols trader_joe_v2,velodrome_v2 --start 2023-01-01 --end 2024-10-06`), T+10min health-verified RUNNING
      and actively writing manifest shards. `quality-gates.sh` green (market-tick-data-service, full run). Along the
      way, live-reproduced a SEPARATE, still-open "bad indexers" transient-indexer-health failure (not schema drift)
      affecting VELODROME_V2/OPTIMISM + others — folded as corroborating evidence into the existing 2026-07-27 (slot-2)
      scope-extension todo in the source issue doc rather than treated as blocking this todo's own "done when" bar
      (which names TRADER_JOE_V2/AVALANCHE specifically). Repos: market-tick-data-service, deployment-service. Source:
      `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`,
      `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-5) — no code shipped (read-only spot-check).** The 2026-07-15-era bucket
      labels named in this todo (`UNISWAP_V3` TimeoutError×25, `UNISWAP_V3`/POLYGON schema-drift×24) no longer match
      current reality — re-measured fresh against prod `_index/availability_index.parquet` (26,819,985 rows):
      `dex_pool_swaps` `attempted_failed` is now 866 rows across 11 (venue, chain, error_reason) buckets. Found this
      exact investigation had ALREADY been done comprehensively same-day by slot-2
      (`issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`, filed hours earlier) — rather than
      fork a duplicate doc, live-probed the same subgraph IDs again ~2h later (production `async_post_to_subgraph` path
      — aiohttp, not bare `urllib`, which Cloudflare-1010-blocks on this host) and appended the re-probe as new evidence
      to that doc: confirmed every distinct (venue, chain) subgraph backing the current long-tail now has a recorded
      live-probe verdict + current row count (table in the doc's new "Verified live (re-probe...)" section). Net new
      signal: PANCAKESWAP_V3/BSC's "bad indexers" condition self-healed within the day (transient, confirmed);
      UNISWAP_V3/OPTIMISM reproduced the IDENTICAL "bad indexers" error (same 3 indexer addresses) hours apart
      (stronger-but-not-yet-conclusive evidence toward structural, not blip — existing P2 todo left OPEN pending a
      genuine multi-day re-check); surfaced a NEW, previously-untracked finding (UNISWAP_V4/ETHEREUM 7 rows,
      error_reason `build_instrument_id` — a code-level id-construction bug, NOT a subgraph-health issue; the subgraph
      itself live-probed healthy) with its own new todo added to that doc. Also noted CURVE/OPTIMISM is still emitting
      fresh `attempted_failed` rows with the pre-fix error signature as of minutes before the probe (likely a
      not-yet-restarted backfill VM running pre-fix code — operational note, out of this todo's scope). Repo:
      unified-trading-pm (issue-doc update only; no production code touched this todo). Source:
      `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`,
      `issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`.
- [x] ✅ [PM] P1. **DONE 2026-07-28 (slot-11).** Filed, then RESOLVED + archived 2026-07-28 —
      `plans/archive/issues/defi_mev_events_pagination_gap_2026_07_28.md` (fix shipped
      market-tick-data-service@33fa3b58) — root cause is the pagination loop's exit branch (`mev_events_handler.py:235`,
      `cursor = from_slot`) hard-setting the cursor to the loop's own termination value on the "more data" branch, so
      any day with >100 Flashbots relay payloads only ever captures its newest page (~100 rows) with no
      `attempted_failed`/partial signal — silent under-coverage, not an outage. Correct frontmatter (`doc_type: issue`,
      `asset_group: [defi]`, `repos: [market-tick-data-service]`) + a concrete `[BACKEND] P2` fix todo (confirm cursor
      semantics, decrement correctly, add multi-page unit test, re-verify with a live sample-day backfill).
      Cross-referenced from the source doc's deferred-work row: updated
      `plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md` line 266 ("File the
      mev_events >100-payload/day pagination gap") from "Not filed" to point at the new doc. Repo: unified-trading-pm.
      Source: `issues/defi_five_never_captured_venues_fix_2026_07_22.md`.
- [x] ✅ [PM] P1. File a new tracked issue doc for the collect-* Terraform stagger's pre-existing T+1 freshness-deadline
      risk: `defi_collection_scheduler.tf`'s header requires the stagger finish by 02:25 UTC for `features-onchain` T+1
      freshness, but `solana-defi` alone (02:05 start, 1500s timeout) can already finish ~02:30 — appears
      pre-existing-violated. Name `t1_batch_scheduler.tf:124-128` as the owner to flag. Repo: unified-trading-pm. **Done
      when**: a new `plans/active/issues/defi_t1_freshness_deadline_stagger_<date>.md` exists citing both files and the
      deadline math. Source: `issues/defi_five_never_captured_venues_fix_2026_07_22.md`. — unified-trading-pm@2c4c1355f.
      Filed `/plans/archive/issues/defi_t1_freshness_deadline_stagger_2026_07_28.md` recomputing worst-case finish for
      every 02:xx collect-* job (solana-defi 02:30, bridge-events 02:35, lst-seasonal-rewards 03:05 — all confirmed
      violations) and flagging that the `t1_batch_scheduler.tf:124-128`/`:131-135` line-citations for the
      "features-onchain T+1 recon" consumer resolve to unrelated jobs — no such job exists in the file today, so the
      deadline itself is currently unverifiable against a real consumer.
- [x] ✅ [PM] P1. **DONE 2026-07-28 (slot-7).** Filed
      `plans/active/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md` — verified the rename commit
      (`market-tick-data-service@522185a6`, 2026-07-22 18:07:42+01:00) via `git show`, confirmed all 4 pre-fix `venue=`
      call sites (`"SOLANA"` x2, `"BITCOIN"`, `chain_name` for EVM) now write `_GAS_FEE_VENUE` ("ALCHEMY") with `chain=`
      untouched, and enumerated the 14 distinct legacy `venue=<CHAINNAME>` values the unmigrated historical population
      spans (12 EVM chains via `CHAIN_ID_TO_NAME` + `SOLANA` + `BITCOIN`). Filed with `assigned_vm: NA` /
      `execution_scope: local-only` and a single `[OPERATOR] P1` migrate-vs-leave todo — do not decide/execute here, per
      the task brief. Repo: unified-trading-pm. Source: `issues/defi_five_never_captured_venues_fix_2026_07_22.md`.
- [x] ✅ [PM] P1. File a new tracked issue doc for the ACROSS/STARGATE `bridge_events` historical-backfill capability
      gap — **investigation found the premise false**: `--start-date`/`--end-date` CLI support already exists
      generically (`ServiceBootstrap(add_date_args=True)` default → `BatchIO`/`DateRangeInput` → per-day `BatchPayload`,
      which `BridgeEventsHandler.process()` already consumes correctly); the grep-zero-matches was a grep-then-conclude
      trap, not a real gap. The actual blocker is `_catalog_preflight()` omitting `mode=` on its
      `assert_defi_catalog_fresh()` call (defaults to `"live"` freshness, fails-closed on historical dates) — already
      tracked by this plan's own "Thread mode= into assert_defi_catalog_fresh()" P1 todo below, which names
      `bridge_events_handler.py`. Filed the corrected finding + a small follow-up verification todo instead of a false
      blocked-on-unbuilt-tooling doc. Repo: unified-trading-pm —
      `plans/active/issues/defi_bridge_events_historical_backfill_gap_2026_07_28.md`. Source:
      `issues/defi_five_never_captured_venues_fix_2026_07_22.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-28 (slot-6, data_engineering)** — Measured the true scale of the DeFi legacy pre-hive
      composite-venue object population. Repo: market-tick-data-service (read-only measurement, no code change).

      **Method**: a bounded, prefix-scoped `gcloud storage ls` per each of the 9 already-known composite venue names
                                                                                                                                                                                                                                                                                                                                                                                                                                      (`.../day=*/asset_group=defi/venue={V}/**`), run in parallel — NOT a fresh whole-corpus walk (single-walk
                                                                                                                                                                                                                                                                                                                                                                                                                                      discipline preserved; the scan is pruned to exactly the 9 already-identified composite `venue=` directories).

                                                                                                                                                                                                                                                                                                                                                                                                                                      **Result: 5,332 objects total** — AAVEV3-ETHEREUM=632, CURVE-ETHEREUM=631, ETHENA-ETHEREUM=631,
                                                                                                                                                                                                                                                                                                                                                                                                                                      ETHERFI-ETHEREUM=631, LIDO-ETHEREUM=631, MORPHO-ETHEREUM=557, UNISWAPV2-ETHEREUM=632, UNISWAPV3-ETHEREUM=628,
                                                                                                                                                                                                                                                                                                                                                                                                                                      UNISWAPV4-ETHEREUM=359. **Corrects the issue doc's "full 2020-2026 defi date range" framing**: every venue's
                                                                                                                                                                                                                                                                                                                                                                                                                                      objects cluster in a ~20-month window (2024-05-02..2026-01-24, UNISWAPV4 narrower still from 2025-01-30) — not
                                                                                                                                                                                                                                                                                                                                                                                                                                      the full ~6.5-year corpus, consistent with the already-confirmed single one-time 2026-05-12 migration batch.
                                                                                                                                                                                                                                                                                                                                                                                                                                      Combined with the prior distribution finding, both prerequisite facts for the `[OPERATOR]` fold-vs-migrate
                                                                                                                                                                                                                                                                                                                                                                                                                                      decision are now in hand. Full writeup: `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`
                                                                                                                                                                                                                                                                                                                                                                                                                                      "2026-07-28 update — true corpus-wide scale measured" section. Source:
                                                                                                                                                                                                                                                                                                                                                                                                                                      `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`.

- [x] ✅ [DIAG] P1. Sample and directly read parquet content from a broader set of DeFi legacy composite-venue objects —
      downloaded + read all 9 venues x 5 sample days (43 objects, `2024-06-15`/`2025-01-15`/`2025-03-15`/`2025-06-01`/
      `2025-08-06`). **Result: only ETHENA-ETHEREUM is single-row (5/43); the other 8 venues carry substantial multi-row
      data (38/43), up to ~54k rows/day for UNISWAPV3-ETHEREUM** — refutes the doc's original single-row assumption.
      Also found UNISWAPV4-ETHEREUM uses a different filename shape (`ticks.parquet`, no `_migrated_<ts>` marker) from
      the same 2026-05-12 migration batch — not an active leak (zero recent-day objects in this shape), but a fold
      selector must match by PATH SHAPE, not filename pattern. Repo: market-tick-data-service —
      `plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` dated 2026-07-28 update.
      Source: `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-28 (slot-16).** Corpus-wide scope audit for the KALSHI_PERP perp_funding
      manifest-emit failure — scanned GCS under the scoped prefix
      (`pipeline_mode=batch_kalshi_perp/asset_group=defi/venue=KALSHI_PERP/...`) per-day (single-prefix listing per day,
      not a whole-corpus walk; a bucket-root delimiter-descent first confirmed 2,400 total `day=` partitions
      2020-01-01..2026-07-27, then the scoped per-day scan was live-verified empty on both edges of that window before
      trusting the result). **Found the affected window is 2026-05-29..2026-07-25 (55/58 days), 13 distinct real symbols
      (not the 5 seen on the single spot-checked day) — 567 (day,symbol) GCS-present instances total, ALL
      manifest-absent** (streamed the 26,978,131-row DEFI manifest, zero `venue=KALSHI_PERP` rows found). Confirmed zero
      new defi-labeled objects from 2026-07-26 onward, verifying the cefi-reroute fix
      (`market-tick-data-service@2aa23de5`, shipped earlier in this batch1 plan) took effect. Also surfaced + filed 2
      new follow-up findings not in scope to fix here: 3 zero-object gap days (2026-07-17/20/21) and a daily
      `_migrated_kalshi_perp_*` non-symbol marker artifact (2026-05-29..2026-07-16, then stops). Full breakdown + the 2
      new `[DIAG] P2` follow-up todos recorded in the issue doc's "Not yet done"/new "Follow-up" sections. No code
      shipped (read-only audit). Repo: market-tick-data-service (read-only). Source:
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
- [x] ✅ [DATA] P1. **DONE 2026-07-28 (slot-4, data_engineering).** All 3 sub-items resolved — full evidence in the
      source issue doc's todos 1+2 (updated same commit), summary here: **(a)** live manifest scan
      (`market-tick-data-service@50fb82cf`) REFUTES the stale-row hypothesis — desynced rows postdate the handler's
      git-blame intro (`9475e66b`, 2026-05-03), root-caused to UAC's single-source `SOURCE_PRIORITY` registry forcing
      the same stamp on every write, not staleness. **(b)** blast radius: 185/7,476 rows (2.5%) across 5 venues
      (ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARN_V3), not YEARN_V3-only. **(c)** already shipped
      (`market-tick-data-service@130847b6`, same slot, earlier pass). `quality-gates.sh` green both commits. Source:
      `issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-28 (slot-6, data_engineering).** Write + run a read-only cross-source
      funding-parity check for every surviving DeFi perp venue declared for BOTH `perp_funding` and `derivative_ticker`
      in UAC's capability registry (excluding DRIFT-SOLANA/PACIFICA-SOLANA per the 2026-07-16 partial-supersede ruling;
      also exclude GMX — REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md` — it is
      no longer a registered venue). Per (venue, market, funding interval) compare `perp_funding.funding_rate` against
      the matching `derivative_ticker` settlement row within a documented tolerance; emit an honest report (match %,
      divergence distribution, worst offenders). File any genuine divergence via standard findings-triage — do not
      resolve inline. No prod writes. Repo: market-tick-data-service (new lifecycle-marked script under
      `scripts/one_offs/`). — market-tick-data-service@4220f6eb. **Registry-declared-both set is empty** (perp_funding
      retired 2026-07-08 for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC in favor of derivative_ticker's embedded field;
      DRIFT/PACIFICA/GMX removed) — confirmed live via the actual `VENUE_DATA_TYPE_CAPABILITIES` registry, not assumed.
      Ran the historical-manifest comparison instead (what the DESIGN P1 todo below actually needs): of the 4 venues
      currently declaring `derivative_ticker` (HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC), only HYPERLIQUID has
      ANY historical `perp_funding` capture (209 dates, 2023-05..2026-06; the other 3 have zero, ever). Compared 2,640
      rows across 10 sampled days spanning HYPERLIQUID's 169-day overlap window: **match_pct=60.7%** at a 2e-5
      tolerance, p90 divergence 5.55e-5, worst-case 1.2e-3 — a genuine, non-trivial divergence, not float noise. Root
      cause: `derivative_ticker.funding_rate` is a per-minute LIVE snapshot (S3 asset_ctxs `funding` column);
      `perp_funding.funding_rate` is the REALIZED hourly-settlement value (dedicated `/fundingRates` endpoint) — related
      but not proven identical, contradicting the 2026-07-08 retirement's "byte-identical" justification. Filed as
      `issues/defi_hyperliquid_perp_funding_derivative_ticker_divergence_2026_07_28.md` (P1, not resolved inline) with
      `[OPERATOR]`/`[DESIGN]` follow-up todos; full match%/divergence report appended to the source issue doc's Progress
      log. `quality-gates.sh` green. Source:
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
      `archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`.
- [x] ✅ [DOC] P1. **DONE 2026-07-28 (slot-13, landed ahead of this todo's own dispatch) — verified 2026-07-28
      (slot-2).** Ported the two-id/dual-key POOL model into `/codex/02-data/defi-canonical-naming-ssot.md` — new "##
      POOL identity is a two-id / dual-key model (Option A, operator-ruled 2026-07-18)" section documents
      `instrument_id` staying bare `pool_address.lower()` (machine/join key) while `chain` disambiguates only inside the
      symbolic `canonical_instrument_id`/`glued_pair_id` (`<VENUE>-<CHAIN>:POOL:<BASE>-<QUOTE>[-<FEE_BPS>]`), plus the
      `DefiPoolIdentity` dataclass/`build_pool_identity()`/`parse_glued_pool_id()` provenance, the 6 known cross-chain
      collision rows being expected-not-buggy under Option A, the catalogue-internal
      `_aggregate_key`/`pool::{chain}::{pool_address}` key (explicitly distinguished from the two-id model), and the
      open P2 bare-`instrument_id`-only preflight/dedup gap. Re-verified consistent with all 3 cited sources:
      `unified_api_contracts/canonical/crosscutting/defi.py`'s
      `DefiPoolIdentity.canonical_instrument_id`/`glued_pair_id` properties,
      `instruments-service/docs/DEFI_INSTRUMENTS.md`'s "Instrument ID format" section, and the closeout plan's "The
      two-id model" section (`defi_consolidated_closeout_2026_07_18.md`). No further code change needed —
      unified-trading-pm@bf2594119. Repo: unified-trading-pm. Source:
      `archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`.
- [x] ✅ [INFRA] P1. Add a `staking-yields` entry to `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s
      `defi_collect_operations` map (cron `50 1 * * *`, the free slot between `eigenlayer-rewards` at 01:45 and
      `evm-defi` at 01:55; tier mirroring `eigenlayer-rewards`), apply via the same single-PR flow every other job in
      the file uses. Repo: deployment-service. **Done when**: `gcloud scheduler jobs list` shows a
      `staking-yields`-named job ENABLED and `gcloud run jobs list` shows the matching Cloud Run Job; after its first
      run, at least 1 manifest row exists for `instrument_type=staking` (verify STARTED + the manifest row per
      no-fire-and-forget — do not mark done on terraform-apply alone). Source:
      `issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`. — DONE 2026-07-26, deployment-service@bd46bf2.
      Added the map entry exactly as specified; `ENV=prod ./tofu.sh plan -target=...` showed
      `2 to add, 0 to change, 0 to destroy` (a new Cloud Run Job + Cloud Scheduler cron — purely additive, no
      `[OPERATOR]` gate applies); applied. Verified
      `gcloud scheduler jobs describe uts-prod-mtds-collect-staking-yields-cron` ENABLED and
      `gcloud run jobs describe uts-prod-mtds-collect-staking-yields` exists. **Did not wait for the 01:50 UTC cron**
      (many hours away) — manually triggered a real execution (`gcloud run jobs execute`), watched it to a genuine
      terminal status (`Completed True`, 47s), then read the per-VM manifest shard it wrote and confirmed **1 row:
      `instrument_type=staking`, `data_type=staking_yields`, `venue=EIGENLAYER`, `capture_status=captured`** — the
      done-when criterion is satisfied. **Bonus finding from the live run, fixed in the same pass**: the execution's
      logs showed LIDO and EtherFi both failing with DNS resolution errors
      (`Cannot connect to host api.lido.fi/api.etherfi.id: Name or service not known`), and the manifest shard had ZERO
      rows for either venue — not even `attempted_failed`. Root cause: each `_fetch_*_apy` helper caught its own
      exceptions internally and returned an empty list on failure, so the caller's `if rows:` branch treated a genuine
      fetch failure identically to "source legitimately returned nothing" and called `record_zero_rows` instead of
      `record_failed` — silently miscategorizing failures. Fixed by letting the fetch helpers' exceptions propagate to
      `_process_venue`'s existing (already-correct) classify-and-record `try/except`, which now correctly calls
      `record_failed`. Regression test updated (`test_client_error_propagates_for_correct_record_failed_classification`,
      the old test asserted the buggy swallow behavior) + full 23-test suite green. market-tick-data-service@2b6d9e6b.
      **Not yet re-verified against a rebuilt image** — the fix is source + test only; the next scheduled/manual
      execution (after the image rebuild lands) will exercise it for real, tracked as a follow-up below rather than
      blocking this todo (the terraform-wiring done-when criterion was about the manifest row existing, which it does).
- [x] ✅ [DATA] P1. **DONE 2026-07-28 (slot-5).** Corrected `/codex/02-data/defi-data-types-catalog.md` § 7's
      `staking_yields` row: replaced the `Status: Production (2026-04-24)` label (live-verified FALSE — zero scheduler
      jobs, zero Cloud Run Job, zero GCS objects across 6 sampled days, confirmed 2026-07-24) with
      `Status: Implemented, unscheduled`, consistent with § 1's live-verification findings in the source issue doc. Not
      flipped to Production — remains gated on the separate scheduler-wiring todo (already shipped above,
      deployment-service@bd46bf2, but this row change was scoped independently per the todo text). Repo:
      unified-trading-pm. Source: `issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`.
- [x] ✅ [VERIFY] P1. **DONE 2026-07-28 (slot-5).** Ran a bounded, read-only simulation (12 synthetic defi swap-pool
      instruments × 30-day date axis, zero GCS/network I/O — `enumerate_expected_universe.py` itself couldn't be
      imported in this venv due to the pre-existing, already-tracked fleet-wide `iter_route_contexts` fastapi
      ImportError, see `issues/fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md`; re-implemented
      `enumerate_v2`'s documented per-instrument-grain cross-join contract instead, using the real live-imported
      `DATA_TYPES_BY_ASSET_GROUP['defi']` = 27 keys today) measuring the `completeness_pct` denominator delta of adding
      the 7 `swaps_ohlcv_*` keys WITH vs WITHOUT a `_DEFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`-style exclusion guard.
      **Verdict: the guard IS required.** WITH the guard, `resolved_data_types` is byte-identical to today's list —
      structurally proven zero denominator delta (not just "expected"). WITHOUT the guard, the 7 new keys are a
      scale-invariant 20.59% (7/34) share of the new denominator, 100% of which is permanently unsatisfiable via MTDS
      backfill (MDPS writes to a different bucket/path) — i.e. `completeness_pct → completeness_pct × 0.7941`, a
      permanent ~20.6% relative drop. Full method + numbers in the source issue doc's new "## Progress Log" section.
      Ship no registry/code change (report only, per spec) — unified-trading-pm@1c722f1b3. Repo: unified-trading-pm (doc
      only; instruments-service read-only, no code changed). Source:
      `issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`.
- [x] ✅ [VERIFY] P1. Determine the root cause of the `swaps_ohlcv_4h` timeframe discrepancy — live manifest shows
      51,985 real captured rows despite `4h` being absent from `unified-api-contracts`'s `_candle_contracts.py`
      module-docstring declared DeFi timeframe set. Confirm intentional (correct the stale docstring to include `4h`) or
      a policy-violating bug (identify the producing code path in MDPS's `DefiSwapAdapter`/`swap_adapter.py` and file a
      follow-up). Repos: unified-api-contracts, market-data-processing-service. **Done when**: root cause is determined
      and cited with evidence; if intentional, the docstring is corrected; if a bug, the producing path is identified
      and a follow-up issue filed. Source: `issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`.
      **Evidence (2026-07-28, slot 8)**: INTENTIONAL, not a bug — `unified-api-contracts/.../_candle_contracts.py:161`
      already defines `_TIMEFRAMES_DEFI = ("15s", "1m", "5m", "15m", "1h", "4h", "1d")` (includes `4h`) and the
      registration loop at `:437` uses it directly; only the module docstring at `:43` was stale (omitted `4h`).
      Confirmed via `market-data-processing-service/market_data_processing_service/config.py:73-75`: "cefi"/"defi" are
      deliberately OMITTED from `_TIMEFRAME_CEILING_BY_ASSET_GROUP` because their UAC constants already equal the full
      7-timeframe default — i.e. MDPS intentionally uses the full ceiling (incl. `4h`) for defi, no scoping-down. Fixed
      the docstring: `unified-api-contracts@b3f3d382`.
- [x] ✅ [SCRIPT] P1. Thread `mode=` into `assert_defi_catalog_fresh()` for the 9 remaining DeFi handlers still omitting
      it (`liquidations_handler.py`, `native_staking_handler.py`, `liquidation_events_handler.py`,
      `token_transfers_handler.py`, `bridge_events_handler.py`, `flash_loan_events_handler.py`,
      `aggregator_route_handler.py`, `solana_defi_handler.py`, `lending_indices_handler.py`) — mirror the exact pattern
      already shipped for `dex_pools_handler.py`/`risk_params_handler.py`/`lst_rates_handler.py`
      (`market-tick-data-service@927acf01`): compute `_run_tag` from `args.run_tag` and pass
      `mode=('live' if     _run_tag == 'live' else 'batch')`. Add one regression test per handler asserting the actual
      `mode=` kwarg received across default/`--run-tag batch`/`--run-tag live`. Repo: market-tick-data-service. **Done
      when**: all 9 handlers explicitly thread `mode=`, one new regression test per handler passes verifying the
      received kwarg across all 3 run-tag states, `bash scripts/quality-gates.sh --no-fix` is green. Source:
      `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`. Shipped — `market-tick-data-service@c38e1b3f`
      (slot-8, 2026-07-28 06:52 UTC): all 9 handlers thread `mode=`, one regression test class per handler added,
      `quality-gates-v2` green on the push (run 30336409358). Verified 2026-07-28 by slot-10 (dispatched the same todo
      as `defi_satellite_ao_dispatch_batch1-030`, found the code already shipped — the code commit landed but the
      plan-flip half was missed) — grepped all 9 call sites confirm `mode=` present, confirmed 9 new/extended test files
      in the commit diff, confirmed CI green.
- [x] ✅ [CHORE] P1. Fix the stale EULER_V2-ARBITRUM phase-dict comment in
      `unified-api-contracts/unified_api_contracts/registry/defi_venues.py` (~line 508: claims "no UAC subgraph_id
      registered" — factually wrong since real Goldsky `SUBGRAPH_IDS` were registered and verified GREEN since
      2026-06-02). Replace with the real reason (mirroring the accurate EULER_V2-ETHEREUM sibling entry's wording:
      `euler_v2.py`'s reference-data adapter is Ethereum-only). Leave the FLUID-ARBITRUM half and the `"pipeline"` value
      untouched — comment-text-only fix. Repo: unified-api-contracts. **Done when**: the comment no longer claims "no
      UAC subgraph_id registered" and states the real Ethereum-only-adapter reason instead; `quality-gates.sh` green; no
      other lines changed. Source: `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`. — DONE 2026-07-28
      (slot-2): split the combined comment into two lines — EULER_V2-ARBITRUM now states the real Ethereum-only-adapter
      reason (mirroring the EULER_V2-ETHEREUM sibling), FLUID-ARBITRUM keeps its original "no UAC subgraph_id
      registered" reason untouched. `"pipeline"` values unchanged. unified-api-contracts@2bc678c8.
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
- [x] ✅ [DATA] P1. **DONE 2026-07-28 — market-tick-data-service@db830f3c (new one-off, read-only script; no change to
      service runtime code).** Measured the scale of bare-symbol-leaf DeFi batch writes since 2026-07-20 via a bounded
      per-day GCS delimiter descent (not a corpus walk) over
      `raw_tick_data/by_date/day={YYYY-MM-DD}/pipeline_mode=batch_*/asset_group=defi/` for every day from 2026-07-20
      through the run date (2026-07-28), counting per-`pipeline_mode` objects whose filename leaf fails the UAC oracle's
      `canonical_path_violations()` id-form check (read-only; used the shipped oracle, did not reimplement it).
      **Result: 6,932 total objects, 5,738 id-form violations (82.8%) across 28 day/pipeline_mode combinations**,
      2026-07-20 through 2026-07-27; the violation rate collapses to 0.0%/1.2% on 2026-07-27, the day
      `write_defi_rows()`'s leaf fix shipped (`market-tick-data-service@0fddb95e`), confirming the fix is effective.
      `day=2026-07-28` carried zero `pipeline_mode=batch_*` subdirectories at probe time (genuine zero, not a listing
      failure). Full per-pipeline_mode/per-day breakdown + raw JSON:
      `/plans/audit/results/defi_bare_symbol_leaf_census_2026_07_28.md`. Script (read-only, one-off):
      `market-tick-data-service/scripts/census_defi_bare_symbol_leaf_since_2026_07_20.py`. Cross-linked from the source
      issue doc. Repos: unified-api-contracts (import only, read-only), market-tick-data-service (read-only). Source:
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`.
- [x] [BACKEND] P1. ✅ **DONE 2026-07-27 — market-tick-data-service@0fddb95e.** Fix `write_defi_rows()`'s filename-leaf
      construction to use the full `instrument_id`, not the bare `symbol` column — in
      `market-tick-data-service/.../canonical_write.py`, `write_defi_rows()` currently discards the
      `df.groupby("instrument_id")` key and rebuilds the leaf from only `group_symbol`. Change it to build the leaf from
      the sanitized `_inst_id` instead, so filename stem == the `instrument_id` column == the manifest key, per
      `cross-asset-canonical-target-ssot.md` §0/§1's hard rule. Scope is limited to the existing `instrument_id` column
      — do NOT wire the not-yet-populated `canonical_instrument_id` column (separate unbuilt-prerequisite item). Repo:
      market-tick-data-service. **Done when**: the leaf is built from the sanitized full `instrument_id`; a fresh sample
      of newly-written DeFi objects (all 6 handlers routing through `write_defi_rows`) passes the UAC oracle's id-form
      check with 0 violations; new/updated regression test passes; `quality-gates.sh` green. Source:
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`. Fixed via a new
      colon-preserving sanitizer (`_sanitize_defi_instrument_id_leaf`) — the UAC oracle's DeFi id-form grammar
      (`_DEFI_INSTRUMENT_ID_RE`) requires literal `:` separators in the stem, unlike the existing bare-symbol sanitizer
      which folds `:` to `_`; verified directly against the oracle (`is_canonical_instrument_id()`) in a new regression
      test. Also fixed the coupled migration script's `leaf_for_instrument_id()` (documented byte-match-with-R1
      invariant) plus 6 affected unit test files (dex_pools/dex_swaps/lending_indices venue-glue guards narrowed to the
      partition directory, not the leaf, since the leaf legitimately now contains `VENUE-CHAIN`). Full
      `quality-gates.sh` green (sentinel-verified against `0fddb95e`'s parent commit).
- [x] [DOC] P1. ✅ **DONE 2026-07-28 (slot-6) — unified-trading-pm.** Correct `canonical-cutover-register.md` §5's
      blanket "DeFi capture is STOPPED / no new defi writes" premise — measurably false for the batch lane
      (`pipeline_mode=batch_onchain_subgraph`/`batch_chainlink`/`batch_onchain_rpc`/`batch_aave` objects measured with
      `time_created=2026-07-24`). Narrowed the claim to the live/websocket lane specifically (11 collect + 3 forward
      crons, PAUSED ~40 days) and substituted the measured fact that batch capture never stopped, with a cite to the
      source issue doc's Fact 1 (including the `COMP-WETH-30.0.parquet` / `time_created=2026-07-24T22:46:34Z` evidence).
      Also updated the "Writer emits the new leaf" milestone-table cell, which repeated the same stale premise as its
      Evidence text, to instead note the leaf-naming code fix shipped `mtds@0fddb95e` (2026-07-27, per this plan's own
      preceding todo) without claiming it's yet independently reconfirmed live in this register. Source:
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`.
- [x] ✅ [DOC] P1. **DONE 2026-07-28 (slot-11) — `unified-trading-pm@936c99588`.** Corrected the stale "oracle id-form
      check is tradfi-only" claim in `four-surface-reconciliation-procedure.md` §4/§4.3 and
      `reconciliation-finding-taxonomy.md` §2.2. Both docs now state the id-form check covers `{tradfi, cefi, defi}`
      (tradfi via its own pre-existing clause 8; cefi+defi via `_stem_id_form_violations()`'s
      `_ID_FORM_CHECKED_ASSET_GROUPS={"cefi","defi"}`, shipped `unified-api-contracts@d40c5d7d` 2026-07-20, refined
      `@1cd27478` 2026-07-23 — verified live against the actual constant, not assumed) and note `sports`/`prediction`
      remain filename-blind. The shared `ADAF0:USTF0.parquet` worked example is corrected in place — re-tested live
      2026-07-28 against `canonical_path_violations()`, confirmed it now returns a real violation, not "0 violations ==
      CANONICAL, false-clean". Repo: unified-trading-pm. Source:
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`.
- [x] ✅ [INFRA] P1. **DONE 2026-07-26 (slot-7) — deployment-service@e34060c, verified.** Apply the already-shipped
      `,`→`;` + `^;^`-delimiter metadata-parsing fix (live in `launch-mtds-dex-pools-backfill-vm.sh` and
      `launch-mtds-dex-swaps-backfill-vm.sh`) to
      `deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh`'s `VM_LENDING_PROTOCOLS` metadata
      construction — identical bug shape (comma-separated `--lending-protocols` collides with gcloud's default
      `,`-delimited `--metadata` parsing), latent because this launcher has only ever been exercised single-protocol.
      Repo: deployment-service. **Done when**: the launcher joins metadata pairs with `;` and passes
      `--metadata="^;^${METADATA}"`; invoking it with a comma-separated `--lending-protocols` value no longer throws
      gcloud's `Bad syntax for dict arg`; single-protocol behavior unchanged. Source:
      `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`. Metadata construction now matches the proven
      dex-pools/dex-swaps pattern exactly (`;`-joined, `startup-script-url=` folded into `$METADATA` itself,
      `--metadata="^;^${METADATA}"`). Verified for real (not just by analogy): ran the actual
      `gcloud compute instances create` local-parse step (against a deliberately nonexistent project, so nothing was
      ever created) with a synthetic 3-protocol value — the OLD comma-delimited format reproduces the exact reported
      error (`Bad syntax for dict arg: [compound_v3]`); the NEW `;`-delimited format parses cleanly past metadata and
      fails only on the (expected, harmless) project-not-found step. Single-protocol case verified clean too.
      `bash -n` + `shellcheck -S error` clean; full `quality-gates.sh` green (98s, sentinel `bd46bf2`).
- [x] ✅ [BACKEND] P1. Rename the onchain feature_group keys in unified-api-contracts' two vocabularies not updated
      during the writer/CLI-name ratification (`unified-api-contracts@e9faf32e`) — `FEATURE_REQUIRED_INPUTS`
      (`required_inputs.py`) and the feature_group refs in `_feature_contracts.py` — from old registry names
      (`aave_lending_rates`, `aave_utilization`, `aave_risk_params`, `lst_staking_yields`, `eigen_rewards`,
      `aave_rate_impact`) to ratified names (`lending_rates`, `utilization`, `risk_params`, `lst_yields`, `rewards`,
      `rate_impact`), and drop `onchain_regime`/`defillama_tvl`/`protocol_rewards` (dropped from the main registry, no
      writer dispatch); update consuming tests. Repo: unified-api-contracts. **Done when**:
      `rg -i     'aave_lending_rates|aave_utilization|aave_risk_params|lst_staking_yields|eigen_rewards|aave_rate_impact|onchain_regime|defillama_tvl|protocol_rewards'`
      over both files returns zero hits; `quality-gates.sh` green. Source:
      `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`. **✅ DONE 2026-07-27 (slot-12) —
      `unified-api-contracts@edf5122d`** ("refactor(features): ratify onchain feature_group vocab in
      required_inputs+contracts", shipped via quickmerge --agent). Renamed the 6 keys in `FEATURE_REQUIRED_INPUTS`
      (`required_inputs.py`) + `ONCHAIN_FEATURE_GROUPS`/routes (`_feature_contracts.py`) to the ratified names, dropped
      `onchain_regime`/`defillama_tvl`/`protocol_rewards`, updated consuming tests (`test_feature_contracts.py`,
      `test_feature_dag_ssot.py`). Verified: the done-when `rg -i` over both files returns **zero hits**; remaining
      corpus hits are out-of-scope (alerting code `defi_aave_utilization_spike`, the
      `normalize_defillama_tvl_history_point` DefiLlama normalizer, and docstrings documenting the rename), not the
      feature_group vocabulary.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-28 (slot-9, verified 2026-07-28 by slot-4).** Already shipped at
      `e2e-testing@bc6a7be` (`scripts/defi/onchain_feature_group_vocabulary_check.py`) — lifecycle-marked script
      (`# Epic/Lifecycle/Delete-when`), cross-repo `sys.path` pattern matching `colocated_engine.py`, imports all three
      vocabularies (UAC `FEATURE_GROUP_TO_FAMILY[onchain]`, features-service onchain CLI `FEATURE_GROUPS`, ml-service
      `DEFI_FEATURE_GROUPS`), computes + prints pairwise set differences. **Re-ran it live to verify**: features-service
      == UAC-onchain (13/13 identical — confirms the 2026-07-21 rename ruling holds); ml-service diverges from both (12
      groups, only `lending_rates` overlaps — pre-existing, separately-tracked drift per the source issue doc, correctly
      reported not asserted-away). `quality-gates.sh` green (sentinel matches HEAD). No test-wiring needed (script path,
      already lifecycle-marked). Source:
      `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`.
- [x] ✅ [DIAG] P1. Verify the 2 unverified signals in the issue doc's §8: (a) sample onchain feature parquets under
      `gs://features-defi-prd-.../onchain/` (e.g. day=2026-03-05, day=2026-05-20) for exact duplicate rows (same
      timestamp+instrument_id repeated); (b) trace where `instrument_count` is computed in the onchain manifest-write
      path and determine why `onchain/_index/availability_index.parquet` shows the identical value 14,630,914 across six
      distinct feature_groups — confirm a true per-group count vs a shared/global count bug. Investigation only, no fix.
      Repos: features-service, unified-trading-library (read-only). **Done when**: a written finding is appended to the
      issue doc stating a definitive yes/no for (a) with sampled evidence, and the concrete code-level root cause for
      (b) (or that it could not be determined and why). Source:
      `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`. — **DONE 2026-07-28**: both (a)
      and (b) CONFIRMED with root cause; not a live-orchestrator bug — see issue doc § "VERIFIED 2026-07-28 (slot-7)".
- [x] ✅ [DATA] P1. Re-run the HYPERLIQUID `trades` batch backfill with the current (fixed, `@c48096e7`) parser/routing
      code, force/overwrite over 2025-05-25..2025-07-27 (legacy `node_fills`) and 2025-07-28..today
      (`node_fills_by_block`) — do NOT expect 2025-03-22..2025-05-24 to populate (confirmed genuine upstream absence).
      Monitored SPOT backfill per the VM-launcher runbook (HYPERLIQUID exempt from the Tardis cap); no fire-and-forget.
      Repo: market-tick-data-service. **Done when**: the cefi `_index/availability_index.parquet` shows real captured
      HYPERLIQUID trades rows across both windows (post-force-rerun) with the pre-existing
      `empty_confirmed`/`SOURCE_RETURNED_ZERO` status cleared, and 2025-03-22..2025-05-24 correctly left empty. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`. — **DONE 2026-07-28 (slot-5)**: prior
      sweeps already fixed the bug (85-95% `captured` both windows, gap correctly unattempted); closed the remaining
      trailing-8-day gap — see Progress Log.
- [x] ✅ [BACKEND] P1. Delete the retired perp_funding DeFi-routing residue: remove the stale `hyperliquid`/`aster`/
      `lighter` entries from `_PROTOCOL_PIPELINE_SOURCE` (`perp_funding_handler.py:188-194`) and `_chain_map`
      (`:244-249`), delete the spent one-off script `scripts/backfill_hl_funding_from_s3_asset_ctxs_2026_06_17.py` (past
      its own `# Delete-when:` marker). Verify the `protocols` iterable no longer includes hyperliquid/aster/lighter
      before deleting the entries. Repo: market-tick-data-service. **Done when**: `perp_funding_handler.py` no longer
      routes those 3 venues through the defi bucket, the script file is deleted, `quality-gates.sh` green. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`. — **Already resolved, no code change
      needed**: `market-tick-data-service@2a760000` ("refactor(perp-funding): delete retired HYPERLIQUID/ASTER/LIGHTER
      DeFi-routing residue + spent backfill_hl_funding_from_s3_asset_ctxs one-off"), landed 2026-07-19, 6 days before
      this batch1 plan's 2026-07-25 triage ran. Verified live on current HEAD: `_PROTOCOL_PIPELINE_SOURCE` and the
      per-protocol `_chain_map` inside `_run_process` both contain only `kalshi_perp`/`polymarket_perp` (no
      hyperliquid/aster/lighter keys); `DEFAULT_PROTOCOLS` likewise lists only those two; the `protocols` iterable never
      includes the retired venues, so `perp_funding_handler.py` cannot route them through the defi bucket. The one-off
      script `scripts/backfill_hl_funding_from_s3_asset_ctxs_2026_06_17.py` is confirmed deleted
      (`git log     --diff-filter=D` shows it removed in the same commit; `find` on current tree returns nothing).
      Remaining `hyperliquid` mentions in the file are docstring/comment history + one unrelated
      `pipeline_mode_for_source` default in the generic "unknown protocol" error-path fallback, not a routing entry.
      Nothing to ship.
- [x] ✅ [BACKEND] P1. Add the missing `Mode.REPLAY` case to `possible_manifest._canonical_pipeline_mode_prefixes` in
      unified-api-contracts so it also emits `replay_<source>/` prefixes alongside `Mode.BATCH`/`Mode.LIVE`, closing a
      latent gap in the phantom-shard auditor (additive, 1-line-class, no-risk future-proofing). Confirm
      `test_possible_manifest`'s prefix-count guard is quiescent before landing. Repo: unified-api-contracts. **Done
      when**: `_canonical_pipeline_mode_prefixes` iterates `(Mode.BATCH, Mode.LIVE, Mode.REPLAY)`; the prefix-count
      guard passes; `quality-gates.sh` green. — unified-api-contracts@6456dd23. The prefix-count guard was NOT quiescent
      (6 sources per AG are REPLAY-capable per `SOURCE_MODE_CAPABILITY`), so
      `test_extra_live_probe_sources_do_not_leak_cross_ag`'s `expected_pipeline_mode_counts` was updated with the same
      explanatory-comment precedent used for prior additions: cefi 21→27 (+aster/databento/deribit/extended/
      hyperliquid/kalshi_perp), defi 17→24 (+chainlink/helius_rpc/hyperliquid/onchain_rpc/onchain_subgraph/
      pyth_hermes/solana_rpc), tradfi 6→9 (+databento/eia/massive); sports unaffected (no inline templates).
      `quality-gates.sh` green (275-322s across runs). Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.
- [x] ✅ [DIAG] P1. Run a real past-day EXTENDED-STARKNET `book_snapshot_5` backfill and a real current-day run against
      the shipped fix (`@55dac12a`, current-only-endpoint honest-skip) — confirm the past-day run produces 0 book rows
      with no fabricated HTTP/timestamp (honest absence) and the current-day run produces a real live current book row
      via the WS connector. Repo: market-tick-data-service. **Done when**: both runs are observed on real infra with the
      expected 0-past-row / real-current-row outcome, recorded in the doc's Progress Log. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`. — DONE 2026-07-28 (Progress Log).
- [x] ✅ [DIAG] P1. Re-verify the LIGHTER-ZKSYNC Tardis exchange-slug + numeric market_id fix
      (`market-tick-data-service@0c4000a02`) against a real, free-tier-compatible first-of-month historical date to
      confirm real `trades`/`book_snapshot_5`/`derivative_ticker` rows still return. Repo: market-tick-data-service.
      **Done when**: a live Tardis probe on a first-of-month date for LIGHTER-ZKSYNC returns real, correctly-shaped rows
      for all 3 data types using current code, recorded in the doc's Progress Log. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`. — RE-VERIFIED 2026-07-28, see Progress Log.
- [x] ✅ [DIAG] P1. Investigate (live API probe) whether EXTENDED-STARKNET's `/info/markets/{symbol}/trades` endpoint's
      descending cursor can actually walk back to historical (non-today) dates — the endpoint takes no
      `startTime`/`endTime` param and 0 trades rows of any capture_status exist at any date. Repo:
      market-tick-data-service. **Done when**: a live probe either confirms deep cursor-walking reaches a real
      historical date (record how far back) or confirms it structurally cannot, recorded in the doc's Progress Log.
      Source: `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`. — DONE: confirmed cannot.
- [x] ✅ [DATA] P1. Diagnose why the onchain `availability_index` manifest consolidator is a measured no-op — **DONE
      2026-07-28 (slot-12), diagnosis-only (no trivial fix exists).** Root cause: NOT a broken consolidator — the 13
      frozen rows live at a dead, orphaned `onchain/_index/` tree left behind by `bucket_fold_features_2026_07_17`'s
      2026-07-18 migration (no consolidator can ever target a sub-prefix). The bucket's real ROOT manifest is alive +
      current; Track 8's "ENABLED, running every 1 minute" is confirmed true and does not contradict this finding — the
      two measure different things. Needs an operator design decision (delete orphan + historical backfill-
      registration), so remediation stays open per this todo's contract. Full evidence:
      `archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md` (Update 2026-07-28, slot-12).
- [x] ✅ [DATA] P1. Diagnose (and fix ONLY if a clear code bug) the implausible identical `instrument_count=14,630,914`
      reported across 5 different onchain feature_groups (health_factor, rewards, liquidation_events, risk_params,
      flash_loan_availability) plus lending_rates in the onchain availability_index — a per-group count shouldn't be
      identical across unrelated groups. Trace the count-aggregation/derivation code path and either fix the
      broadcast/join bug or document why the shared count is legitimate. Repos: unified-trading-library,
      market-tick-data-service. **Done when**: a written root cause is added to the issue doc as a dated Update, with
      either a shipped + verified fix (re-derived index shows distinct plausible counts) or a documented reason the
      shared count is legitimate. Source:
      `archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`. — **DONE 2026-07-28 (slot-13)**:
      no live code bug; see dated Update in the issue doc.
- [x] ✅ [DATA] P1. **DONE 2026-07-28 (slot-12).** GCS-verified (bounded, prefix-scoped, no whole-corpus walk):
      features-onchain `lst_yields` is exactly 15 day-partitions (2026-04-03..2026-04-19, 2-day internal gap); MTDS raw
      `lst_rates` spans years both sides per EVM token (LIDO 2021-08-17..2026-07-27, ETHERFI ≥2024-01-01..2026-07-27,
      all 11 active EVM venues present in-window) — confirmed a features-layer backfill lag, not raw-data absence. Filed
      `issues/defi_lst_yields_coverage_extension_gcs_verified_2026_07_28.md` proposing backfill scope (features-service
      batch CLI, per-token genesis→today, no new tooling); backfill not executed (out of scope). Cross-linked from the
      source doc's deferred-work row + P2 todo. Repo: unified-trading-pm (read-only). Source:
      `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-28 (slot-15, data_engineering).** Diagnose the root cause of the 2026-06-28 defi
      phantom-capture batch-writer failure. Writer-ordering bug RULED OUT for both MDPS candle-write paths (repo-scope
      corrected: swaps_ohlcv is MDPS, not MTDS) at the incident-date commit — both already upload-before-record.
      Strongest evidence-based root cause: the pre-fix UTL manifest-consolidator column-misalignment bug
      (`unified-trading-library@6b0520a6`, 2026-06-27, ~18h pre-audit) — a positional `UNION ALL` merging
      differently-ordered shard columns into canonical explains both the spurious `captured` rows and their near-uniform
      per-granularity counts. No live fix needed (bug already fixed + rows already reconciled). Full evidence in
      `issues/phantom_captures_defi_2026_06_28.md` Progress Log. Source: same doc.
- [x] ✅ [VERIFY] P1. **DONE 2026-07-28 (slot-6, data_engineering).** Confirmed via read-only code trace: adding
      `perp_daily_ctx` to `DATA_TYPES_BY_ASSET_GROUP["defi"]` mints ZERO new `expected_unattempted` rows and moves NO
      `completeness_pct` for the already-registered HYPERLIQUID/CeFi combinations — HYPERLIQUID/CeFi venues enumerate
      under `DATA_TYPES_BY_ASSET_GROUP["cefi"]` (a separate dict key), not `["defi"]`
      (`instruments-service/scripts/enumerate_expected_universe.py:4145,1157`,
      `unified_api_contracts/registry/market_data_categories.py:360`). Mechanism note: the data_type axis is NOT
      independently scoped in general (unlike the venue axis) — it IS a direct enumerator input gated by
      `PROTOCOL_CAPABILITIES` (`market_data_categories.py:1443-1517`), so this specific inertness is due to
      HYPERLIQUID's asset_group placement, not the mechanism itself. No code/schema/manifest changes made. Full finding:
      `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` Progress Log (2026-07-28).
- [x] ✅ [DATA] P1. **Resolve the Kamino/Solend `lending_indices` `instrument_type` shape conflict** — probe BOTH
      candidate paths (`solana_lending` vs the Track-2-claimed `solana_amm_pool`) and reconcile against the 47-object
      Track-2 finding. **✅ 2026-07-28 (slot-2)**: `solana_amm_pool` never existed for KAMINO `lending_indices` — Track
      2's prose was a mislabeling; the real legacy shape is `instrument_type=lending`, clean on Track 2's own probe day.
      Probing OTHER days surfaced a NEW confirmed fabrication (a frozen 2026-05-04/05 snapshot duplicated across ~21
      months of `day=` partitions) — same bug class as the source issue, filed separately:
      `/plans/archive/issues/defi_kamino_solend_lending_indices_legacy_shape_fabricated_history_2026_07_28.md`. Source
      doc archived: `/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`.

## Progress Log

- **2026-07-28 (slot-5)** — Closed HYPERLIQUID `trades` batch-backfill re-run todo: `batch_hyperliquid` manifest check
  showed prior sweeps already fixed the bug (85-95% `captured` both windows, gap correctly unattempted); closed the one
  real remaining gap (trailing 8 days, 07-21..28) after 2 SPOT preemptions (confirmed via `compute.instances.preempted`)
  by finishing the remainder `ON_DEMAND=true` (justified to main, accepted) — final: all 8 days 173/173 files, no code
  change (parser fix `market-tick-data-service@c48096e7` shipped 2026-07-13).
- **2026-07-28 (slot-12)** — Re-verified LIGHTER-ZKSYNC Tardis fix (`@0c4000a02`) live, real rows confirmed. Finding:
  `issues/lighter_tardis_writerless_route_hang_2026_07_28.md`.
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
- **2026-07-26 (slot-14) — KALSHI_PERP/POLYMARKET_PERP cefi-routing todo IN PROGRESS, not yet shipped.** Working the
  todo "Fix `_perp_funding_kalshi_polymarket.py`'s KALSHI_PERP/POLYMARKET_PERP routing" (market-tick-data-service).
  **Code complete, targeted-tested, sitting uncommitted in the slot-14 worktree** (not yet quickmerged — blocked on a
  full `quality-gates.sh` pass, itself delayed by heavy same-host QG contention, see below):
  - `_perp_funding_kalshi_polymarket.py`: added `_write_cefi_perp_funding_rows()` (mirrors `write_defi_rows`'s
    per-instrument sharding but via UAC `build_cefi_partition_path`/`build_instrument_id`, no chain axis) and switched
    `_collect_kalshi_perp`'s write call to it instead of the DeFi-only `write_defi_rows`.
  - `_defi_manifest.py`: `DefiManifestRecorder` gained an `asset_group: str = "defi"` constructor param (default
    preserves all ~25 other DeFi-handler callers byte-identical), threaded through `_emit_captured_add`/`record_empty`/
    `record_zero_rows`/`_emit_failed_row`; `record_zero_rows` also gained a `source` passthrough (was silently dropped
    before, a latent gap on ANY caller, not just this todo).
  - `perp_funding_handler.py`: `_run_process` now resolves the CEFI bucket
    (`get_write_bucket_name("market_data", "cefi")`) and constructs `DefiManifestRecorder(..., asset_group="cefi")`;
    every `record_captured`/`record_zero_rows`/ `record_failed`/`record_empty` call in
    `_run_process`/`_dispatch_protocol` now passes an explicit `source=_source_for_protocol(protocol)` (was previously
    blank on the manifest write, auto-stamping to the wrong single-source `"hyperliquid"` default once routed through
    the multi-source `cefi/perp_funding` cell).
  - `tests/unit/test_perp_funding_kalshi_polymarket.py`: updated the one stale assertion
    (`test_writes_perp_funding_canonical_shard`) that expected the old defi hive path's `batch_kalshi_perp`
    pipeline_mode segment; cefi paths carry no pipeline_mode segment by design. **71/71 targeted tests pass** (
    `test_perp_funding_handler.py` + `test_perp_funding_kalshi_polymarket.py` + `test_defi_manifest_recorder.py`, 0.8s).
  - **Manifest cleanup (the todo's 3rd sub-requirement) — drafted, NOT YET RUN.**
    `scripts/remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py` (untracked, lifecycle-marked oneoff) is ready; a
    live read confirmed **8 stale rows** currently in the DEFI manifest (4 `KALSHI_PERP` `captured` + 4
    `POLYMARKET_PERP` `attempted_failed`, ALL stamped `source="hyperliquid"` — exactly the bug). Per the source issue
    doc's explicit sequencing, this MUST run only AFTER the writer fix ships (never before, or the still-live bug
    resurrects the rows) — do not run it until the 4 files above are committed+pushed.
  - **Root-caused, filed, and shipped a separate finding along the way**:
    `/plans/archive/issues/shared_host_tmp_tmpfs_full_2026_07_26.md` (unified-trading-pm@f7982c1a1, pushed) — the shared
    host's `/tmp` tmpfs was at 100% (accumulated since 2026-07-14 across many slots) AND
    `scripts/quality-gates-base/base-service.sh` has 25 `>/tmp/<name>_qg.log`-redirected QG steps sharing a FIXED
    (non-PID-unique) filename, so two slots' concurrent `quality-gates.sh` runs collide and produce spurious step
    failures — reproduced repeatedly (a step fails inline, the SAME checker invoked standalone with the same args passes
    clean). Did not attempt the 25-site fix itself (each has a paired write+read-back reference; too large for this
    todo's scope) — filed as a P2 todo in that issue doc instead.
  - **UPDATE 2026-07-27: code shipped, manifest cleanup EXECUTED AND VERIFIED.** QG passed (497s, sentinel written);
    code shipped `market-tick-data-service@2aa23de5`. The cleanup script's ORIGINAL pandas-based implementation then hit
    a severe, real production incident while running for real: the DEFI manifest is ~26.5M rows (~1GB on disk) and both
    `pandas.read_parquet` (~13GB RSS) and a naive single-shot `pyarrow.Table` load (~12GB RSS) + a `.filter()` call
    needing BOTH the original and filtered copies alive at once (~24GB peak) made the process a repeated target for a
    host memory-pressure killer (`earlyoom`) on this concurrently-oversubscribed shared VM (8 cores, load 15-44
    observed, active swapping) — **4 separate kills**, each silent (SIGTERM, no traceback), before the actual root cause
    was pinned down via in-process RSS instrumentation. Rewrote the script to stream row-groups
    (`ParquetFile.iter_batches()` + a streaming `ParquetWriter`, never materializing more than ~500K rows at a time) —
    peak RSS dropped from ~24GB to ~4.3GB, and the whole run (download, scan, snapshot, stream-write, CAS-write,
    stream-verify) completed in **72.4s**. Real prod run confirmed: **26,540,325 → 26,540,317 rows (exactly 8
    removed)**, pre-apply backup snapshot at
    `gs://market-data-tick-defi-prd-central-element-323112/_index/backups/availability_index.pre_kalshi_polymarket_removal_20260727T013308Z.parquet`,
    post-write verification asserted zero remaining KALSHI_PERP/POLYMARKET_PERP rows. **This todo's Done-when criteria
    are now ALL met** (cefi-classified write+manifest path shipped, source fixed, manifest cleanup executed) — the only
    remaining step is committing the corrected (streaming) version of
    `scripts/remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py` itself (the version that actually ran and
    succeeded, replacing the pandas-based version from the `2aa23de5` commit — QG was re-running against it as this note
    was written), then flipping this todo's checkbox with both shas + this evidence, then `/done`.
  - **Lesson for future large-manifest scripts on this fleet**: NEVER `pandas.read_parquet`/single-shot
    `pyarrow.read_table` a multi-million-row manifest index on this shared host without checking current `free -h` /
    `uptime` first — prefer `ParquetFile.iter_batches()` streaming by default for any manifest-index script (defi's is
    26.5M rows and growing; cefi's ~10.5M-row restamp from `2026-07-21` might be getting close to the same danger zone
    as it grows). A silent SIGTERM with zero output/traceback on this fleet is `earlyoom`, not a bug in your script —
    check `/proc/<pid>/stat` utime ticks over a real multi-second window (not just `ps %CPU`, which is a lifetime
    average and misleads once a process has done real work earlier in its life) to tell "genuinely still computing"
    apart from "hung/about to be killed" before waiting longer.
  - Also shipped (unified-trading-pm): a follow-up addendum to the tmpfs/QG-race issue doc adding a
    host-oversubscription root-cause section + a new `[INFRA] P1` todo — **still uncommitted as of this note** (hit
    branch drift 3x on a very active shared repo; deprioritized in favor of the actually-required manifest cleanup). Low
    risk — it's a working-tree-only diff, not at risk of loss, just not yet pushed.
- **2026-07-28 (slot-10)** — `mtds@55dac12a` confirm: batch CLI can't reach this gate so called `fetch_extended_rest`
  directly — past-day 0 book rows (honest absence), current-day 1 real book row. WS connector is BLOCKED-CREDENTIALS.

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

`/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`'s sole candidate
("Determine whether the dex_pools-class fake-history-snapshot bug also affects Kamino/Solend Solana lending_indices in
the `-prd-` bucket") was a genuine cross-doc contradiction (`instrument_type=solana_lending` per the writer code vs. an
independent `instrument_type=solana_amm_pool` live-probe finding, 47 objects, in
`defi_consolidated_closeout_2026_07_18.md` Track 2). Filed as entry 3 in
`plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`; the operator answered same-day: probe both
shapes before concluding. Widened + dispatched as a Todos-section item above (source doc also updated with a new item 6
carrying the same widened scope).

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` (`depends_on: [defi_satellite_ao_dispatch_batch1_2026_07_25]`
— `gate_on_depends: true`), mirroring the cefi/tradfi/prediction batch1 finalize-plan pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc.
