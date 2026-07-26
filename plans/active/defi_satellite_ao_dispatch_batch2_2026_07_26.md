---
doc_type: plan
title: DeFi satellite AO batch 2 — fresh Phase-1/Phase-3 triage of the defi closeout-orphan corpus
summary: >-
  Second AO-dispatch batch for defi, produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) +
  Phase-3 (conflict-check + draft) triage over all 56 defi AG-primary docs not already covered by the consolidated
  closeout, aggregated-sources index, batch1 (+finalize), and the forked children (track01-per-instrument-and-canon-id,
  lending-writer-retire-prerequisite, gmx-venue-removal+finalize, dex-pool-symbol-fix-backfill-purge+finalize,
  track5-coverage-mvp-backfill, native-ao-extract+finalize) (2026-07-26). 44 docs came back orphaned (25 partial
  coverage, 19 never touched); 1 was a mistag whose real content is fleet-wide CI/QG infra, not defi-specific
  (excluded); 1 was fully closed already (`mtds_perp_funding_backfill_hang_2026_07_14.md`, archive candidate, not
  actioned by this batch). Phase 3's conflict check cleared 24 candidates from the 44 orphaned docs into fresh
  AO-dispatch todos, then found 1 genuine duplicate pair (both docs independently drafted the identical "90-day
  lst-rates backfill for 6 venues" ask) and merged them into a single combined todo citing both sources — 23 todos ship
  here. Left 3 conflict-gated, 11 operator-gated, 3 time-gated, 1 too-large-or-risky, and 2 human-only items in the
  Deferred sections below for the next iteration or an explicit operator ruling, per the skill's non-batchable taxonomy.
  Also flags a separate mistag found during Phase-0 discovery
  (`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`, tagged bare `[cross-cutting]` despite its
  defi-prefixed title — `locked_by: live-defi-rollout` so not retagged here, flagged for the finalize plan).
status: draft
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    execution-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-2, satellite-docs, fresh-triage]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.8
estimate_calibrated_ai_days: 2.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (interactive, operator-approved scope) — Phase 1 classified all 56 defi
  AG-primary docs not already in the covering-plan set via a Workflow fan-out (56 agents), Phase 3 ran a conflict-check
  + candidate-todo draft over the 44 orphaned docs via a second Workflow fan-out (44 agents, resumed once after a
  session interruption via cached-agent replay), per the skill's documented methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 2 — fresh triage extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 23 todos below are same-priority-independent and touch distinct files/docs (verified — the one
> confirmed duplicate pair was merged into a single todo before this doc was authored, not left as two colliding
> entries).

## Todos

- [ ] [DATA] P1. Fill DeFi manifest venue-key under-enumeration (C8): UAC's `defi_venue_capabilities.py` declares 90
      defi venue-keys, but the `_index/availability_index.parquet` manifest currently enumerates only a partial subset
      per instrument_type family — lst 14/22, lending 6/21, perp 5/8 — leaving genuine absentee venues with NO manifest
      row at all (not even `expected_unattempted`): DRIFT-SOLANA (Solana MVP), FRAX, MORPHO, FLUID. Audit the
      enumeration path that seeds `expected_unattempted` rows for defi (the same enumerator touched by the 2026-06-22
      blank-`asset_group`/blank-`chain` fixes referenced in this plan's Progress Log) and confirm it is being driven off
      the full UAC venue-capability registry rather than a stale/partial venue list; re-run (or extend) the seeding pass
      so every one of the 90 UAC-declared venue-keys gets a manifest row (captured or honest `expected_unattempted`) for
      its declared instrument_type family, with DRIFT-SOLANA/FRAX/MORPHO/FLUID confirmed present. Source:
      /plans/active/data_completion_defi_2026_07_15.md (item C8). Done when: a manifest census (deployment-api
      `_axis_census.py` or equivalent) shows lst/lending/perp venue-key counts matching UAC's 90-key registry (100%
      enumerated, not just 14/22, 6/21, 5/8), with DRIFT-SOLANA, FRAX, MORPHO, and FLUID each carrying at least one
      manifest row; quality-gates.sh green.
- [ ] [CHORE] P3. Finish the two housekeeping-cluster sub-items NOT already covered by
      `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (which only covers the OPERATIONS dict fix and the
      paper_run_handler stale comments): (1) delete
      `market-tick-data-service/scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` — its own documented
      `Delete-when: dex-pools-prd/lst-rates-prd/perp-funding-prd are deleted` condition is now satisfied (all 3 buckets
      confirmed deleted per the source doc's Progress Log); (2) audit the ~8
      `market-tick-data-service/scripts/defi_*_2026_06_01.py` / `gate3_solana_manifest_reconcile.py` /
      `backfill_hl_*_2026_06_17.py` scripts (all tagged `Lifecycle: campaign`) for hardcoded dead bucket-name templates
      tied to earlier, already-completed migrations — repoint or mark for deletion per each script's own Lifecycle
      marker; not urgent but currently orphaned. Source:
      plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md. Done when:
      `migrate_lst_perp_shared_bucket_gap_2026_07_13.py` is deleted (or its deletion is confirmed already done with a
      cited commit), and each of the ~8 campaign scripts has been checked for dead bucket-name templates with either a
      repoint applied or a documented reason no fix is needed.
- [ ] [DATA] P1. **Fix the doubled `day={D}/day={D}/` prefix bug in the DeFi instruments-store `by_date` tree (both the
      writer regression AND the v9 migrator's malformed projection).** Two defects, both must be fixed before the gated
      defi §H instruments-store object `--apply`: (1) an instruments-service `by_date` WRITER regression nests a second
      `day=` segment for recent snapshots (`≥2026-05-05` onward -- confirmed doubled at `day=2026-05-05` and
      `day=2026-05-07`; `day=2026-05-03` and all earlier days are single, canonical
      `day={D}/venue={V}/instruments.parquet`) -- locate and fix the writer so it never emits
      `day={D}/day={D}/venue=.../instruments.parquet`; (2) `migrate_instruments_store_v9.py`'s `canonical_object_rel`
      inserts `pipeline_mode=/asset_group=` after the FIRST `day=` but does not normalize a pre-existing doubled `day=`
      segment, producing a malformed projected path
      (`day=2026-05-07/pipeline_mode=batch_instruments_service/asset_group=defi/day=2026-05-07/venue=...`) -- add a
      `day=.../day=...` collapse (or a pre-flight reject that surfaces the malformed rows instead of silently migrating
      them) to `canonical_object_rel`. Repo: instruments-service. Note: the catalogue/enumerate read path
      (`build_instrument_catalogue`, via `_DAY_RE.search`/`_VENUE_RE.search`) already resolves the correct day+venue
      regardless, so this is a G4 object-migration correctness gate, not a CF-14/catalogue blocker. **Done when**: (a) a
      fresh `by_date` snapshot write for any day after the fix contains a single `day={D}/` segment (verified on a live
      or dry-run write); (b) `migrate_instruments_store_v9.py --asset-group defi --dry-run` over the previously-doubled
      date range (`2026-05-05`..`2026-05-07`+) projects single-`day=` canonical paths with no `day=.../day=...`
      malformation; (c) `quality-gates.sh` green for instruments-service. Source:
      `defi_migration_audit_log_2026_07_24.md` (P1 "DeFi instruments-store `by_date` has a DOUBLED `day={D}/day={D}/`
      prefix" finding, slot-2 2026-06-07 G2 verify dry-run).
- [ ] [DATA] P3. **Fold `lst-rates` into DeFi data-status + exclude orphan `VAULT` venue.** (1) Wire the `lst-rates`
      availability_index (bucket `lst-rates-central-element-323112`) into the defi data-status aggregation / rollup
      `manifest_source` read path (deployment-api `data_status` aggregation + the defi projection rebuild) so the 5 LST
      venues (ANKR/STADER/STAKEWISE/SWELL/MANTLE + LIDO/ROCKETPOOL/ETHENA/...) stop reading as zero — this corpus
      already reads only `market-data-tick-defi`, not the dedicated lst-rates bucket, even though the data is genuinely
      captured (not a data gap). (2) Exclude/remap the orphan generic `VAULT` venue (1113 captured rows, not a real
      protocol) out of `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES`. Do NOT touch the bare-`SUSHISWAP` classic-vs-V3
      alias question in the same registries — that is explicitly out of scope here (conflict-gated, see note). Source:
      `plans/active/defi_venue_lst_rates_residual_2026_07_24.md`. Done when: (a) the 5 LST venues' rows are visibly
      credited (non-zero) in the DeFi could-exist / data-status view, verified via the deployment-api `data_status`
      endpoint or UI; and (b) `VAULT` no longer appears as a live/uncategorized registered venue in
      `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES` (excluded or mapped to its real protocol), with its
      previously-orphaned rows now attributable to a real protocol or explicitly documented as excluded. (repos:
      deployment-api, unified-api-contracts)
- [ ] [BACKEND] P1. **Migrate `AaveRateImpactCalculator` off the structurally-zero DefiLlama Yields borrow field onto
      MTDS `lending_indices`, then re-point strategy-service's P&L reader to the writer's actual feature_group name.**
      (1) In features-service, change `AaveRateImpactCalculator.fetch_data()`
      (`features_service/onchain/app/calculators/aave_rate_impact_calculator.py`) to source
      `total_borrow_usd`/borrow-APY-equivalent fields from the MTDS `lending_indices` parquet (per-block Aave subgraph
      capture, `market-tick-data-service/.../aave_lending.py`) instead of DefiLlama Yields' `/pools` endpoint — that
      endpoint returns `totalBorrowUsd=None` for all 16,092 pools it serves (confirmed, not sampled), which
      `pool_float()` defaults to `0.0`, making utilization (`total_borrow/total_supply`) and therefore every rate-model
      output column (`projected_supply_apy`, `projected_borrow_apy`, `rate_impact_supply_bps`, `rate_impact_borrow_bps`)
      a deterministic zero for every symbol, every day, structurally, regardless of when it runs. This is the
      previously-identified but never-executed tail item from
      `plans/archive/issues/aave_irm_slope_capture_dropped_2026_05_12.md` Step 4 ("~1 cal AI-day; the override path is
      dormant until then") — do not re-litigate the data-source choice, MTDS `lending_indices` is the already-identified
      internal SSOT replacement, no new vendor search needed. (2) Once the calculator produces real, non-degenerate
      utilization/borrow-side values, update `strategy-service/pnl/engine/orchestrator.py:144` (currently reads
      `feature_group="aave_rate_impact"`) to read `feature_group="rate_impact"` — the writer's actual, UAC-ratified name
      since the 2026-07-21 vocabulary rename (`unified-api-contracts@e9faf32e`) — so the P&L engine stops silently
      swallowing the feature lookup (`→ {}` → unadjusted P&L presented as adjusted). Repos: features-service,
      strategy-service. **Done when**: re-running the onchain `rate_impact` backfill for a recent date
      (`--feature-group rate_impact --mode batch`) produces non-zero `total_borrow_usd`, non-zero utilization, and
      non-zero `rate_impact_supply_bps`/`rate_impact_borrow_bps` for Aave-v3-Ethereum pools with known nonzero
      real-world borrow activity (spot-check against the MTDS `lending_indices` source rows for the same pools/date);
      `strategy-service/pnl/engine/orchestrator.py` reads `feature_group="rate_impact"` (not `aave_rate_impact`); both
      repos' `quality-gates.sh` green. Source:
      `issues/aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26.md`.
- [ ] [ENGINEER] P1. Triage the 9 `unified-api-contracts/unified_api_contracts/internal/architecture_v2/` files flagged
      by the original `rg -l -i 'drift|pacifica'` sweep but never individually confirmed fixed by the 2026-07-16
      follow-up dispatch — `perp_hedge_sizer.py`, `capability_manifest.py`, `archetype_config.py`,
      `backtest_scenarios.py`, `flash_loan_receiver.py`, `algo_compatibility.py`, `liquidation_bonus_schedule.py`,
      `benchmark_fill_pricing.py`, `archetype_capability.py`. For each: re-run `rg -n -i 'drift|pacifica'` scoped to
      that file, classify every hit as genuine live Solana-perp-DEX venue residue (Drift/Pacifica venue id, leg spec,
      capability entry) vs a false positive (e.g. "schema/numeric drift", unrelated prose). For genuine hits, apply the
      SAME fix pattern already used on the resolved files in this issue (`archetype_capability_manifest.json`,
      `archetype_leg_spec_seeds.py`, `collateral_registry.py`, `simulation_assumptions.py`, `jurisdiction_overlay.py`,
      `order_semantics.py`, `venue_tokens.py`, `archetype_leg_spec.py`): remove/repoint the dead venue entry and leave a
      `# DRIFT/PACIFICA (Solana) removed 2026-07-16 (operator ruling: ...)` comment marker, matching the marker
      convention already applied workspace-wide. Do NOT touch `unified-trading-system-ui`'s
      `venue_set_variants`/`archetype_capability_registry`/`strategy_instance_catalogue` or
      `tests/e2e/_shared/strategy-registry.ts` in this todo — those are separately gated on an undecided strategy-domain
      call (delete vs re-leg `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` onto Jupiter) and on the stale UI/UAC
      registry-sync generator (see this doc's Secondary finding) being fixed first; out of scope here. Source:
      `plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`. Done when: all 9 files
      have either a documented false-positive verdict (no code change) or a genuine-hit fix with the standard removal
      comment marker, `unified-api-contracts` full `quality-gates.sh` is green, and the change ships via scoped
      `quickmerge.sh --agent --files`.
- [ ] [DOCS] P3. Document the three MEV archetypes (`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, `ARBITRAGE_MEV_JIT_LIQUIDITY`,
      `ARBITRAGE_MEV_BACKRUN`) as explicitly OUT of the paper-replay tick-builder-wiring scope. Add a short note (in the
      relevant strategy-service archetype/catalog doc or module-level docstring near `_ENGINE_DRIVABLE_ARCHETYPES` in
      `paper_universe.py`, plus a one-line cross-reference from
      `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`'s own DOCS todo) stating: these three are
      architecturally opportunistic/runtime-mempool-driven with no catalog-declared currency universe, so no
      day-partition tick loader can be built against them; a currency constraint for them would require new logic inside
      the engines themselves — a materially different, separately-scoped piece of work, not attempted here. Source:
      `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` (DOCS P3 todo, line ~606). Done when: the
      out-of-scope rationale for these 3 archetypes is written down in a discoverable, permanent location (codex or
      in-repo docstring/comment) rather than living only in this issue doc, and the issue doc's own DOCS todo is checked
      off with a citation to where it now lives.
- [ ] [CODE] P3. Fix wrong catalog-builder import alias in `tests/integration/test_recursive_borrow_scenarios.py`:
      `FAMILY_2_CELL_IDS` is built by importing `_build_carry_recursive_staked` (the **plain** `CARRY_RECURSIVE_STAKED`
      archetype's catalog builder) aliased as `_build_carry_recursive_borrow_perp_hedged`, instead of importing the real
      `build_carry_basis_perp_inv` (the `CARRY_BASIS_PERP_INV` archetype's actual catalog builder). Today this is
      harmless (both builders happen to satisfy the same `len(...) >= 5` row-count assertion) but the Family-2 test cell
      IDs are silently sourced from the wrong archetype's catalog rows. Fix: import and alias
      `build_carry_basis_perp_inv` correctly, re-run the file's tests, confirm `FAMILY_2_CELL_IDS` now reflects
      `CARRY_BASIS_PERP_INV`'s real 10-row catalog and the existing assertions still pass (adjust the row-count
      assertion only if the real count differs from 5+). Ship via quickmerge scoped to this one test file. Source:
      plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md ("Minor incidental finding" under
      the `CARRY_RECURSIVE_BORROW_LENDING_ONLY` / `CARRY_BASIS_PERP_INV` orchestrator-stub section, 2026-07-24). Done
      when: `tests/integration/test_recursive_borrow_scenarios.py` imports `build_carry_basis_perp_inv` (not the
      plain-archetype builder) for its Family-2 registry, `bash scripts/quality-gates.sh --no-fix` is green, and the fix
      is shipped + the plan checkbox flipped.
- [ ] [DESIGN] P3. Evaluate wiring the existing `curve_adapter.py`/`api.curve.fi` REST path
      (`market_tick_data_service/market_interface/adapters/defi/curve_adapter.py`) into the batch `dex_pool_swaps`
      collection cascade for CURVE/OPTIMISM (mirroring the "ARB/POLY only on hosted service (deprecated) — use
      api.curve.fi instead" precedent already documented in UAC `_defi.py`), as an alternative to leaving this cell as a
      permanent honest `EXPECTED_SUBGRAPH_DEINDEXED` absence. Repo: market-tick-data-service. Not urgent — every other
      `dex_pool_swaps` (venue, chain) cell is unaffected and the ~144-952 CURVE/OPTIMISM rows are a small fraction of
      the asset_group's total gap; do NOT implement the wiring itself in this todo — only produce the evaluation. **Done
      when**: a written, evidence-cited verdict is appended to the source issue doc stating whether `curve_adapter.py`'s
      REST integration can realistically be wired into the `dex_swaps_handler.py` batch cascade for this (venue, chain)
      pair (covering: does the REST response shape map onto the existing `dex_pool_swaps` schema/writer contract; what
      integration point would the call live at; rough effort), with an explicit go/no-go recommendation for a follow-up
      implementation todo. Source: `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`.
- [ ] [DATA] P2. **Re-run the DeFi `instrument_availability` shape-B ("hive") vs flat reconciliation with a null-aware
      comparator, full population.** The 2026-07-14 corrected-comparison pass found the original 45.2% (1,315/2,911)
      byte-mismatch figure is very likely inflated/entirely explained by a `None`-vs-`NaN` serialization artifact
      (Python `object`-dtype `None` on the flat writer vs `float64`-dtype `NaN` on the hive writer, only in columns
      `pool_fee_tier`/`quote_asset_decimals`) — a null-aware re-comparison on a 70-pair stratified spot-check (10 venues
      × 7 dates) found **0 real field-level diffs**, but that was only 70 pairs, not the original 2,911. Re-run the full
      reconciliation (all 2,353 real day-partitions, or at minimum the original 2,911 venue-day pairs where both shapes
      have a comparable file) with a null-aware field comparator (treat `None`==`NaN` as equal). Reuse/adapt the
      read-only investigation approach cited in Source (scratchpad `defi_shape_b_reconcile.py` pattern,
      `run5.json`/`run100.json`) — this is READ-ONLY, nothing is written to or deleted from GCS. Record the corrected
      mismatch percentage and a final verdict (real divergence confirmed at scale vs artifact-only, effectively 0% real
      divergence) as a new dated section in Source. Do NOT run any delete, backup, or migration step, and do NOT make
      the "finish v9 hive migration vs delete the stale frozen hive snapshot" call — that remains an explicit operator
      decision that folds into `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (cross-cutting
      instruments-service scope, out of bounds for this todo).

  Source: `defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`

  Done when: the null-aware reconciliation has run across the full 2,911-pair (or full 2,353-day-partition) population
  and a corrected mismatch percentage + closing verdict is recorded in Source as a new dated section, definitively
  resolving whether the original 45.2% figure was a comparison-methodology artifact or real divergence at scale.

- [ ] [DATA] P2. Once `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s P1 [BACKEND]
      `_perp_funding_kalshi_polymarket.py` cefi-routing fix (sourced from
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s 2026-07-24 root-cause resolution) has landed AND its P1
      [DATA] corpus-wide KALSHI_PERP scope audit has produced its per-day/per-symbol GCS-present/manifest-absent count,
      re-run manifest rebuilds for every affected historical day/symbol identified by the scope audit so the
      previously-silently-dropped KALSHI_PERP/POLYMARKET_PERP perp_funding rows (originally rejected because
      `source='kalshi_perp'`/`'polymarket_perp'` was not a registered `SOURCE_PRIORITY[("defi","perp_funding")]` source)
      get correctly re-emitted under the now-fixed cefi-classified write path. Repo: market-tick-data-service. **Done
      when**: every day/symbol the scope audit flagged as GCS-present/manifest-absent for KALSHI_PERP/POLYMARKET_PERP
      perp_funding now has a manifest row under the correct classification, `quality-gates.sh` green, and
      `issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`'s status flips to resolved. Source:
      `issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`.
- [ ] [SCRIPT] P1. **Implement the MTDS DeFi perf bundle (knobs + async fan-out + executor-offload) as ONE combined
      commit** — code-only, no VM launch, no canary. (a) Add `defi_max_concurrent_fetches` (32),
      `defi_max_inflight_tasks` (128), `defi_max_concurrent_uploads` (64) to
      `market_tick_data_service/config/service_config.py`, mirroring the existing Tardis 3-knob block (verified: none of
      the 3 currently exist — grep-confirmed). (b) Replace the sequential `for protocol in protocols` loop(s) in
      `market_tick_data_service/cli/handlers/solana_defi_handler.py` and the sequential shard loop in
      `dex_pools_handler.py` with a bounded fan-out reusing UTL's `ParallelPerSymbolRunner` (call with
      `manifest_writer=None` during fan-out; apply `record_captured`/`record_zero_rows`/`record_failed` + the heartbeat
      SEQUENTIALLY afterward, in original iteration order, to preserve today's manifest-write/heartbeat semantics
      exactly). (c) Route the blocking `_upload_parquet`/`storage.upload_bytes` calls through `loop.run_in_executor` on
      a DEDICATED `ThreadPoolExecutor` (never the default pool — the cefi DNS-starvation wedge). Ship as ONE commit —
      the 3 knobs are proven inert alone (0% gain) unless bundled with the fan-out; do not split. Add/extend unit tests
      proving: shard-level failure isolation preserved (no `raise` in per-shard loops), `record_captured` grain
      unchanged, no upload reorder/drop. Explicitly do NOT launch the 2-VM TheGraph canary or any wide SPOT wave — that
      validation step is operator-owned ("ship code + I run the canary", per
      `defi_track5_coverage_mvp_backfill_2026_07_24.md`'s own deferral to this doc) and is separately gated on the
      auth-blocked `gcloud compute` access noted in this doc's § Auth block; this todo covers the code + unit-test
      portion only, which the source doc states is safe to implement without live infra. Source:
      `plans/active/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md` § "Optimization — the perf bundle" (P1
      item). Done when: the 3 new knobs exist in `service_config.py`; `solana_defi_handler.py` and
      `dex_pools_handler.py` fan out fetch+upload via `ParallelPerSymbolRunner` with sequential post-loop
      manifest-write/heartbeat application; blocking upload calls run on a dedicated `ThreadPoolExecutor`; new/updated
      unit tests pass proving shard isolation, unchanged `record_captured` grain, and no upload reorder/drop;
      `bash scripts/quality-gates.sh` is green on `market-tick-data-service`; change is committed via
      `quickmerge.sh --agent` (no VM launch, no canary run) and this doc's perf-bundle checkbox is flipped with the
      commit SHA as evidence.
- [ ] [BACKEND] P1. **Add a per-instrument residual emitter to the capturable non-POOL DeFi handlers**
      (`lending_indices_handler`, `risk_params_handler`, `lst_rates_handler`, `evm_defi_collectors` in
      market-tick-data-service) so their IS-seeded per-instrument `expected_unattempted` cells can reconcile — mirror
      the existing DEX pattern (`record_catalogue_residual_empty` / `EmptyConfirmedReason.EXPECTED_NOT_ENOUGH_TVL`,
      `_dex_swaps_queries.py:157`, `residual = catalogue_pool_ids - captured_pool_ids`) but reusing the now-generalised
      `catalogue_pool_ids_for_shard` (`_catalogue_filter.py:77`, tracked as its own prerequisite todo in
      `defi_satellite_ao_dispatch_batch1_2026_07_25.md`) so each handler diffs its OWN captured-instrument set against
      the IS catalogue subset for its `instrument_type`(s) and emits a per-instrument empty-confirmed row for the
      residual, instead of today's VENUE/CHAIN-grain blank-`instrument_id` `record_zero_rows`/`record_empty`.
      `lst_rates_handler` additionally needs the per-instrument `instrument_id` grain added to its residual/empty path
      specifically — NOTE: `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s combined `lst_rates_handler.py` todo
      already fixed the CAPTURED-path per-instrument `record_captured` grain but explicitly excludes the empty/residual
      path ("do not touch the empty/residual path") — this todo is the remaining, un-duplicated residual-side half for
      `lst_rates_handler` plus the wholly-untouched residual emitters for
      `lending_indices_handler`/`risk_params_handler`/`evm_defi_collectors`. Do NOT reuse `EXPECTED_NOT_ENOUGH_TVL` (it
      sits in `OUT_OF_COVERAGE_WINDOW_REASONS` and would re-create the denominator-exclusion bug this doc exists to
      avoid) — use the doc's already-shipped `EmptyConfirmedReason.EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH`-adjacent
      terminal-reason machinery only for the genuinely-unsatisfiable reference-only class (already resolved separately);
      for these 4 genuinely-capturable handlers, emit ordinary per-instrument empty-confirmed rows so cells can flip to
      `captured` on a real re-capture. Repo: market-tick-data-service. **Done when**: all 4 handlers call a
      per-instrument residual emitter (new shared helper or per-handler call mirroring the DEX pattern) after their
      capture pass, one new/extended unit test per handler asserts a per-instrument empty-confirmed row is written for
      an uncaptured-but-in-catalogue instrument (with a real `instrument_id`, not blank), the existing
      `lst_rates_handler` CAPTURED-path grain fix from batch1 is left untouched/still green, and
      `bash scripts/quality-gates.sh --no-fix` is green in market-tick-data-service. Source:
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`.
- [ ] [DATA] P3. Append F10 (YEARN_V3/ETHEREUM/yield_bearing/vault_share_price pipeline_mode<->source desync, MEDIUM,
      delete_elig=NO) to the DeFi reconciliation register as a defi-scoped row, per the audit's own Section 9
      maintenance-contract note ("F10 ... not in the register as defi-scoped rows ... flagged as follow-up") -- add the
      row under whichever register doc F10 belongs (/codex/02-data/non-canonical-path-inventory.md or the
      canonical-cutover-register, matching the format of existing register entries) citing
      data_pipeline_reconciliation_defi_2026_07_20.md Section 4/Section 9 as the source finding. Source:
      defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md (todo 5). Done when: F10 has a row in the register doc
      with the same fields (finding id, severity, description, delete_elig) as other register entries, and the register
      doc's F10 row links back to data_pipeline_reconciliation_defi_2026_07_20.md.
- [ ] [CODE] P2. Wire EULER_V2 lending-indices capture and resolve the UAC "Plasma" chain ambiguity — per
      `plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`'s two remaining unblocked open todos
      (items EULER_V2-capture-wiring and Plasma-chain-resolution; the doc's HYPERLIQUID/ASTER UAC-registry todo is
      intentionally excluded — see note): (1) Re-verify the EULER_V2 Goldsky subgraph's current sync lag (measured ~38
      days / ~271K blocks behind Ethereum mainnet as of 2026-07-10, `defi_venue_capabilities.py:150-153`) — do NOT wire
      capture if it is still stalled; if stalled, stop here and record the measured lag. (2) If caught up: fix the
      `mtds_operations` mismatch on the `euler_v2` `_ProtocolCapability` (`capability_declarations/_defi.py:476`,
      currently `["collect-lending-indices","collect-liquidations"]`) by repointing it to `collect-evm-defi` (the CLI
      operation that actually implements the EULER_V2 collector,
      `market_tick_data_service/cli/handlers/evm_defi_handler.py`/`evm_defi_collectors.py`), OR add real EULER_V2
      handling to MTDS's `LendingIndicesHandler`/`LiquidationsHandler` defaults — pick whichever matches how
      `collect-evm-defi` is actually meant to be invoked; the existing `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entries for
      EULER_V2-ETHEREUM/ARBITRUM (`defi_venue_capabilities.py:155-156`) already exist but have zero real captured rows —
      trigger/verify a real capture run afterward. (3) Separately, resolve which "Plasma" chain UAC's
      `FLUID-PLASMA`/`AAVE-PLASMA` placeholder chain entries are meant to refer to (the 2025 Tether-backed Plasma L1,
      vs. the unrelated pre-2020 Polygon Plasma bridge) by investigating chain-config provenance/commit history/any
      on-chain references before touching those entries — if genuinely unresolvable from evidence alone, close this
      sub-item as `BLOCKED-OPERATOR-DECISION` with the ambiguity documented rather than guessing. Source:
      `plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`. Done when: the subgraph lag is
      re-verified and documented either way; if caught up, `mtds_operations` is repointed (or handler wired)
      consistently with the collector actually used and a capture run demonstrably produces >0 real `lending_indices`
      rows for EULER_V2-ETHEREUM and/or EULER_V2-ARBITRUM in the manifest (if still stalled, this sub-item closes as
      `BLOCKED-UPSTREAM` with the measured lag cited instead); and the Plasma chain identity is either
      confirmed/documented in UAC or explicitly filed `BLOCKED-OPERATOR-DECISION`.
- [ ] [DEPLOY] P1. Redeploy the DeFi backfill VM tarball/image carrying `market-tick-data-service@420221b4` (or later
      HEAD), then — AFTER confirming the redeploy — execute the production re-collect for the 2,958 affected historical
      shards (`dex_pool_state` 2,107 rows + `lst_rates` 851 rows, 434 unique dates 2020-01-01..2026-06-29, 13 venues / 9
      chains) using the exact commands in the source doc's "Exact commands for the follow-up" section:
      `python -m market_tick_data_service --operation collect-dex-pools --mode batch --asset-group DEFI --start-date 2020-01-19 --end-date 2026-06-25`
      and `--operation collect-lst-rates --mode batch --asset-group DEFI --start-date 2020-01-01 --end-date 2026-06-29`,
      launched via the registered `launch-mtds-dex-pools-backfill-vm.sh` (and the lst-rates equivalent) so the run
      carries the redeployed fixed image. **[OPERATOR] VM-launch note**: this is a production launch against live
      subgraph/RPC endpoints consuming real API quota; justified safe-idempotent per the source doc's own scoping —
      `ManifestFreshnessCache`'s skip-if-fresh means the ~99.99% already-good shards near-instant-skip and only the
      2,958 actually-stale ones do real work. The deploy step is a HARD PREREQUISITE to the re-collect step (sequential,
      not parallel) — launching the re-collect on the still-pre-fix image would reproduce the exact
      `UPSTREAM_INSTRUMENTS_CATALOG_STALE` mislabeling this issue's `420221b4` fix already corrected once (the
      2026-07-15 ~12:16-12:22Z recurrence). Repo: market-tick-data-service / deployment-service (VM tarball build).
      Source: `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`. **Done when**: the backfill image build is
      verified to carry `420221b4`+; the re-collect VM(s) launch successfully (STARTED <60s, ≥1 progress/hr per the
      VM-launcher runbook) and run to completion or a documented monitored handoff; a before/after live-count query
      against `market-data-tick-defi-prd-central-element-323112`'s canonical `availability_index.parquet` shows
      `UPSTREAM_INSTRUMENTS_CATALOG_STALE`/`attempted_failed` for `dex_pool_state`+`lst_rates` dropping toward 0,
      replaced by a mix of `captured` and `empty_confirmed[EXPECTED_PRE_VENUE_LAUNCH]`; this issue doc's `[DATA] P1`
      (full re-collect) and `[DEPLOY] P1` (redeploy) checkboxes are flipped `[x]` with the evidence (build/deploy
      confirmation + before/after counts) cited inline.
- [ ] [ENGINEER] P2. Close the second and third instances of stale DRIFT residue in
      `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` by applying the SAME playbook already
      validated + shipped for the first instance (`deployment-ui@83ec561`, Progress Log 2026-07-21: a formula-verified,
      referential-integrity-checked SURGICAL PRUNE — not a blind regen, since no recoverable generator exists for any of
      these files):
  - `unified-trading-system-ui/lib/registry/ui-reference-data.json` — remove the ~40 lines of lowercase `"drift"`
    residue in generated archetype/capability data: `venue_ids` array entries (`"drift"` inside e.g.
    `["drift","gmx_v2","hyperliquid"]` / `["drift","gmx_v2","hyperliquid","lido","uniswap_v3"]`), the archetype id
    `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod`, and the free-text `notes` describing the Jito/Marinade +
    Kamino + Drift hedge leg. Recompute/verify any dependent summary counts the file carries; confirm zero NEW dangling
    references.
  - `unified-api-contracts/openapi/capability-manifest.json` (`venue:drift` + `collateral:drift` nodes, 22 edges),
    `unified-api-contracts/openapi/capability-verdict-matrix.json` (~70 `"venue": "drift"` rows, recompute
    per-archetype + top-level `available_count`/`blocked_count`/`cell_count` summaries exactly as done for
    deployment-ui's verdict-matrix), `unified-api-contracts/openapi/capability-unlock-report.json` (3
    `"to_node_id": "venue:drift"` refs in `impossible`/`roadmap` sections). For every file: reverse-engineer + preserve
    its existing pretty-printing/formatting before editing (as instance 1 required), leave
    `generated_from_commit`/`manifest_commit` provenance fields UNCHANGED (this is a documented delta on a stale base,
    not a freshness claim — matches instance 1's precedent), run each repo's existing consumer/loader test suites to
    confirm no breakage, and quickmerge scoped to only the touched files. OUT OF SCOPE for this todo (do not touch): the
    fourth instance, `unified-api-contracts/openapi/prospectus/*.md` (57 files) — its generator
    (`unified-trading-pm/scripts/openapi/generate_strategy_prospectus.py`) has drifted from the committed copies on many
    axes UNRELATED to drift removal (venue-category classification, execution-algorithm lists, diagnostic strings,
    formatting, 2 archetypes missing from the committed set), so blind regeneration risks a large unrelated diff — that
    needs a human design decision on how to reconcile the generator drift before anyone dispatches a fix there. Done
    when:
    `rg -in '"venue:drift"|"collateral:drift"|"venue":\s*"drift"' unified-trading-system-ui/lib/registry/ui-reference-data.json unified-api-contracts/openapi/capability-manifest.json unified-api-contracts/openapi/capability-verdict-matrix.json unified-api-contracts/openapi/capability-unlock-report.json`
    returns zero matches (plus a manual check that no other lowercase `"drift"` venue-id residue remains per the
    case-insensitive-sweep lesson already recorded in this doc); each repo's existing test suite is green; changes
    shipped via quickmerge with real commit shas; and this issue doc's Progress Log is updated to record instances 2+3
    closed while instance 4 (prospectus) stays explicitly open. Source:
    `plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`
- [ ] [REGISTRY] P2. Close 4 leftover DeFi wizard/taxonomy gaps from
      `e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`: (1) **D3** — `backtest_solana_basis.py` exercises a
      drift-perp / Orca(Raydium) SOL-DEX-spot basis that has NO cell in `CARRY_BASIS_PERP` (spot venues are
      CEX/`uniswap_v3` only, `orca`/`raydium`/`whirlpool` absent) — add the Solana-DEX spot venues to the
      `CARRY_BASIS_PERP` leg-spec + verdict-matrix (unified-api-contracts) + wizard `leg:CARRY_BASIS_PERP:spot` option
      tree (unified-trading-system-ui), OR (if Solana-DEX-spot basis is determined to be data-only / not a deployable
      cell) document that explicitly in the leg-spec instead of the current silent omission; (2) delete or wire the dead
      `per_venue_margin_buffer_pct: 0.20` key in `strategy-service/.../configs/arbitrage_price_dispersion.yaml`
      (currently zero Python references) into the collateral-aware down-size branch already shipped in
      `staked_basis.py::_derive_structure`; (3) make `spot_venue` a first-class selectable axis for staked-basis —
      currently hardcoded per-LST (ETH-LST→UNISWAP_V3, SOL-LST→JUPITER, `catalog_staked_basis.py:30-35`) with no
      Binance-spot/orca/raydium alternative, even though the engine already accepts a `spot_venue` param and APD already
      exposes an equivalent via `venue_universe` — in unified-api-contracts (leg-spec/manifest) + strategy-service
      (catalog); (4) audit the e2e DeFi catalog's 5 behavioural params left at engine defaults
      (`entry_bps`/`exit_bps`/`min_health_factor`/`hedge_deadline_ms`/`peg_drift_threshold_bps`) against the
      production/paper-run intended values for functional (not just nominal) alignment, per the doc's "NEW findings" P2
      ask. Source: e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md. Done when: (1) CARRY_BASIS_PERP either has
      orca/raydium spot cells wired end-to-end (leg-spec + verdict-matrix + wizard option tree) with a wizard-buildable
      drift-perp/orca-spot config, OR the leg-spec explicitly documents Solana-DEX-spot basis as non-deployable; (2)
      `per_venue_margin_buffer_pct` is either removed from the YAML or has a live code path consuming it; (3)
      `spot_venue` is a selectable axis for staked-basis in both the leg-spec/manifest and the wizard, mirroring APD's
      `venue_universe` pattern; (4) a written comparison of the 5 behavioural e2e defaults vs production/paper intent is
      committed, with any mismatch either fixed in-repo or filed as a new `plans/active/issues/` doc.
- [ ] [DOCS] P2. **Close out `features_service_defi_data_loading_blockers_2026_05_29.md` (status still `open`, no
      `resolved_by`) — verify + flip, do not re-implement.** Direct code inspection (this audit pass) already confirms
      every substantive item in the doc is SHIPPED: (1)
      `DEFI_DATA_TYPE_OVERRIDES`/`volume_analysis`/`vwap`/`microstructure` now route through UAC
      `resolve_data_type_for_feature_group()` → `dex_pool_swaps`, proven by
      `tests/delta_one/integration/test_delta_one_integration.py::test_defi_{volume_analysis,vwap,microstructure}_resolves_dex_pool_swaps`
      (features-service); (2) the OHLC-semantics investigation (Issue 5 / decision #3) is answered and documented in
      `unified-api-contracts/unified_api_contracts/internal/schemas/_candle_contracts.py` lines ~400-408, which
      explicitly cites this issue doc by name ("features_service_defi_data_loading_blockers_2026_05_29 #3") and explains
      the USD-normalized-spot-price semantics; (3) the duplicate-column UAC cleanup (decision #4,
      `swap_count`/`volume_quote_usd`) is done — `_candle_contracts.py` drops `volume_quote_usd` as a duplicate and
      keeps `swap_count` only on the state candle, verified by
      `unified-api-contracts/tests/internal/unit/test_mdps_candle_contracts.py`; (4) the EOD-handoff's three CeFi-pivot
      cross-repo bugs are ALSO fixed — tz-naive/aware join fixed in
      `market-data-processing-service/market_data_processing_service/app/core/canonical_writer_streaming.py`
      (`.dt.replace_time_zone("UTC")`, comment quotes the exact original error), MDPS column-order drift fixed via
      `pl.concat(..., how="diagonal_relaxed")` in
      `features-service/features_service/delta_one/app/core/data_loader.py::_concat_and_sort` (comment dated "Surfaced
      2026-06-01 by the CeFi features smoke"), and the filter-pushdown queue-time fix is live in
      `market-data-processing-service/.../orchestration_scanner.py::_collect_matching_parquet_blobs` (filters on
      `venues`/`instrument_ids` before adding to `files`). Worker action: re-verify these five citations still hold on
      current `main` (re-run the cited tests / re-grep the cited lines), then flip this doc's frontmatter `status: open`
      → `status: resolved`, fill `resolved_by:` with the confirming commit SHAs/citations, and remove
      `locked_by: live-defi-rollout` if no longer needed. **Done when**: frontmatter shows `status: resolved` +
      populated `resolved_by:` with evidence citations for all 4 original decisions + the 3 CeFi-pivot bugs, committed
      via `docs(plans):`. Source: plans/active/issues/features_service_defi_data_loading_blockers_2026_05_29.md
- [ ] [SCRIPT] P3. Regenerate the stale `adapter_contract_baseline.yaml` entries for the 2026-07-14 Solana-Drift/Helius
      split: in `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`, first confirm the split
      (commit 7a8bc43c, moving Helius batch-resolve retry/rate-limit mechanics from
      `market_tick_data_service/cli/handlers/solana_defi_drift.py` into the new sibling `solana_defi_drift_helius.py`)
      did not actually DROP any tracked contract calls
      (`classify_venue_error`/`ADAPTER_FETCH_FAILED`/`record_captured`/`record_empty`/`record_zero_rows`/`record_failed`)
      — verify via `git log -p` / `git show` around 7a8bc43c that the calls now counted in `solana_defi_drift_helius.py`
      (9 today) are the same calls formerly counted under `solana_defi_drift.py` (was baselined at 12, now 10), i.e. the
      split moved calls rather than silently losing them. If confirmed intentional (no real regression), run
      `check_adapter_contract_regression --regenerate-baseline` (or the equivalent quality-gates.sh 5.70/6
      baseline-regen flow) scoped to `market-tick-data-service` to update the `solana_defi_drift.py` baseline count to
      10 and add a fresh baseline entry for `solana_defi_drift_helius.py` at 9. If instead calls were actually lost (a
      real regression), do NOT regenerate — file a new P1/P2 issue doc describing the lost contract calls and leave the
      WARN in place. Source: `plans/active/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md`.
      Done when: `quality-gates.sh --no-fix` on `market-tick-data-service` no longer prints the "Adapter contract-call
      regression" ⚠️ for `solana_defi_drift.py`, the updated `adapter_contract_baseline.yaml` diff is committed, and the
      source issue doc's status is flipped to resolved (or a new regression issue doc is filed instead, per the above
      branch).
- [ ] [SCRIPT] P2. Confirm defi OHLCV/DEX writers no longer reproduce the 2026-06-28 phantom-capture pattern (manifest
      `capture_status=captured` rows with no backing GCS parquet — 219,529 rows, dominant in
      `swaps_ohlcv_*`/`dex_pool_swaps`/`gas_fees`). The original capture-BATCH OHLCV writer implicated in the 2026-06-28
      finding was RETIRED 2026-07-18/19 for the per-instrument writer re-architecture (SHIPPED
      `market-tick-data-service@4ca2640d`, R1 in `defi_track01_per_instrument_and_canon_id_2026_07_24.md`), so this is a
      fresh verification against the CURRENT writer path, not a re-check of retired code. Read `write_defi_rows`
      (`market_interface/adapters/defi/canonical_write.py`) + `_write_and_upload`
      (`cli/handlers/evm_defi_collectors.py`) and every active defi OHLCV/dex_pool_swaps/gas_fees handler, and verify
      `record_captured` is invoked only AFTER a confirmed-successful parquet upload for that instrument
      (write-then-record ordering) — never before or independent of the flush, which is the exact ordering bug the
      2026-06-28 batch writer is suspected of. Repo: market-tick-data-service (read-only code review; no live backfill
      run required — do not attempt a code fix in this todo). Source: `issues/phantom_captures_defi_2026_06_28.md`.
      **Done when**: a finding is appended to the issue doc's Progress Log stating, per active defi
      OHLCV/dex_pool_swaps/gas_fees writer handler, whether `record_captured` happens strictly after a verified
      successful parquet write (with exact code-line citations), and either confirms the phantom-recreation risk is
      closed across all of them or files a new dated issue doc under `plans/active/issues/` for any handler found still
      vulnerable.
- [ ] [SCRIPT] P2. **Confirm/close Phase 5 #2 `dex_pool_swaps` DEX-fill 3-VM fleet** (`mtds-dex-swaps-backfill-1/2/3`,
      date-sharded on-demand, covering the measured gap `2024-10-07→2026-07-21`) — verify via
      `gcloud compute instances list --filter="name~mtds-dex-swaps-backfill"` (confirmed still all 3 `RUNNING` as of
      2026-07-26, well past the doc's original ~20-30h estimate). For each VM: read `run.log` + per-VM manifest shard
      count (`time_created`, not log activity) to confirm genuine climbing progress, not a silent stall. If any VM has
      vanished/terminated without reaching its assigned date-range end, relaunch that exact chunk's command again
      (idempotent by design per the doc's own Deferred-work table) rather than restarting from the original start date.
      Once all 3 VMs report `process_final=True`/`exit_code=0` for their assigned ranges, flip
      `lst_rate_honest_coverage_2026_07_21.md`'s Phase 5 `#2 DEX fill` todo with the manifest-count evidence and append
      a Progress Log entry. Source: `lst_rate_honest_coverage_2026_07_21.md` (Phase 5, "#2 DEX fill" todo + RESUME POINT
      deferred-work table row "Phase 5 #2 dex_pool_swaps backfill"). Done when: all 3 VMs are confirmed terminated with
      a completed date-range (or successfully relaunched to reach that state), the doc's Phase 5 #2 todo is checked off
      with cited manifest evidence, and the RESUME POINT table row is updated to reflect the closed state.
- [ ] [SCRIPT] P2. **Run the designed 90-day lst-rates backfill for the 6 already-shipped, accuracy-verified DeFi venues
      (ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER) — first re-verify the shared LST-rates cron is no longer
      crash-looping.** `defi_five_never_captured_venues_fix_2026_07_22.md` asserts the blocking gas-fees crash-loop bug
      is already fixed (mtds@522185a6); `defi_venue_phase_live_definition_contradiction_2026_07_22.md` (same underlying
      ask, filed independently) requires a live re-check before trusting that — do the re-check first since it is cheap
      and the two docs disagree on whether it is still needed. Verify `uts-prod-mtds-collect-lst-rates` (Cloud Scheduler
      job `uts-prod-mtds-collect-lst-rates-cron`, `asia-northeast1`, project `central-element-323112`) is healthy on its
      most recent run(s) —
      `gcloud scheduler jobs describe uts-prod-mtds-collect-lst-rates-cron --location=asia-northeast1` +
      `gcloud run jobs executions list --job=<the corresponding Cloud Run Job> --region=asia-northeast1` (or equivalent
      log check) confirming no OOM/timeout crash-loop in the last several scheduled runs. **If healthy**: run the local,
      no-VM, ~2,340-call 90-day RPC backfill for the 6 venues via the current canonical `lst_rates_handler.py` RPC-based
      path (queries historical block numbers directly), then manifest-verify new rows landed across the full 90-day
      window for each of the 6 venues (`instruments-service/scripts/measure_honest_coverage.py` or a direct manifest
      read against the prod `lst-rates-central-element-323112` bucket / `market-data-tick-defi` corpus, whichever the
      handler writes to) — `record_captured` (not `attempted_failed`) for all 6 venues, any gap either backfilled or
      explicitly logged as a real per-day upstream absence, never silently skipped. **If still crash-looping**: do NOT
      run the backfill — instead file a new tracked issue doc
      (`plans/active/issues/defi_lst_rates_cron_crash_loop_<date>.md`) documenting the health-check evidence and the
      specific crash-loop symptom, and explicitly leave the backfill deferred pending that fix. Source:
      `issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md`,
      `issues/defi_five_never_captured_venues_fix_2026_07_22.md`. **Done when**: either (a) the 90-day backfill is
      complete and manifest-verified for all 6 venues with cited cron-health evidence, or (b) a new issue doc exists
      citing the crash-loop evidence and explicitly defers the backfill.

## Deferred — conflict-gated (genuinely unresolved, do not draft competing todos)

- **`plans/active/issues/defi_code_codex_drift_2026_05_27.md`**: D15 ("HYPERLIQUID + ASTER are DEFI_VENUE_PHASE=pipeline
  but perp_funding_handler actively collects them; reconcile the phase label (→ live, or confirm cefi-axis
  classification)") is a DUPLICATE of already-tracked-but-undispatched ground, not genuinely orphaned. Live-code check
  confirms D15's own premise is stale: HYPERLIQUID/ASTER are not even present in UAC's defi_venues.py DEFI_VENUE_PHASE
  registry today (grep on unified-api-contracts/unified_api_contracts/registry/defi_venues.py returns zero hits for
  either venue) — they only appear in the CEFI-side registries (market_data_categories.py CEFI venue lists,
  _mvp_scope_rules.py). The real current gap is exactly what
  plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md tracks as its own open [CODE] P1 item
  ("HYPERLIQUID/ASTER durable fix — declare them in UAC's own `ALL_DEFI_VENUES` + `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (a
  deployment-api-local stopgap already unblocks the dashboard)"), which IS cited inside the covering set at
  plans/active/defi_consolidated_closeout_aggregated_sources_2026_07_24.md line 478. D15's own alternate framing ("...or
  confirm cefi-axis classification") is the same blocking question that doc records as needing "the CEFI/DEFI
  dual-counting axis decision" — and that decision is now ALREADY RESOLVED (operator-confirmed 2026-07-07 in
  plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md lines 157-168:
  HYPERLIQUID/ASTER are intentional hybrid on-chain-CLOB venues, CEFI holds instrument definitions / DEFI holds
  chain-level settlement context; re-confirmed not-a-double-counting-risk in the 2026-07-21 update inside the turbo-api
  doc itself, lines 265-275). So D15 and the turbo-api doc's P1 prescribe the identical fix (UAC registry declaration)
  against the identical now-unblocked decision — a clear duplicate, not a genuine two-sided conflict. Per the
  conflict-check rule, do not draft a competing D15 todo from this orphan-doc's audit; the correct dispatch vehicle for
  the actual remaining work is the turbo-api doc's own P1 item (already enumerated in the aggregated_sources index, just
  not yet folded into an active AO-dispatch batch plan). Recommended resolution: when the aggregated_sources index's own
  backlog is next turned into a dispatch batch, fold that P1 item (now unblocked — no operator decision needed) into it;
  this orphan doc's D15 line should be closed with a cross-reference note to the turbo-api doc rather than spawning a
  second, redundant todo.
- **`plans/active/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`**: The one remaining open item in
  this doc — the unchecked `- [ ] [FEATURE] P2 delta_one funding_oi venue-aware annualisation` todo (features-service,
  thread venue through the delta_one calculator interface so non-8h venues like Hyperliquid annualise correctly) — is
  explicitly annotated in the doc itself as "DEFERRED — successor: perp_funding_data_semantics_and_cadence_2026_06_16.md
  (parent_epic mtds_mdps_master); migrated 2026-06-21 — not the carry path; cross-cutting delta_one refactor." I
  verified that successor doc exists, is status:open, asset_group:[cross-cutting], parent_epic:mtds_mdps_master,
  priority P1, locked_by:live-defi-rollout, last_updated 2026-06-27 — i.e. it is a live, actively-owned issue doc that
  already claims this exact ground (same file, `features_service/delta_one/app/calculators/funding_oi.py`, same
  mechanism: venue-aware annualisation). Grepping the entire defi covering set (consolidated closeout, batch1, track01,
  track5, and all other listed docs) for `funding_oi`/`delta_one`/venue-aware annualisation returns zero hits — nothing
  in the defi tranche re-claims or duplicates this work, which is correct because it was deliberately migrated OUT of
  defi scope into a cross-cutting/mtds_mdps_master doc on 2026-06-21. This is therefore not a genuine defi-AG orphan:
  the work exists, is tracked, and is owned by a different, already-live doc outside this tranche's scope. Drafting a
  defi-AO todo for it here would create a competing/duplicate claim on the same file against the successor doc's
  existing ownership (locked_by:live-defi-rollout). Recommended resolution: no action needed in the defi tranche — this
  item should surface (if at all) only in a cross-cutting or mtds/mdps tranche audit of
  `perp_funding_data_semantics_and_cadence_2026_06_16.md` itself, not as a new defi satellite-batch todo. The target doc
  `e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md` can be treated as fully closed-out from the defi AG's
  perspective — its sole open thread is correctly parked in its designated successor.
- **`plans/active/issues/lst_exchange_rate_data_availability_2026_07_21.md`**: Phase-1's "orphaned_never_touched"
  verdict is a false positive produced by the narrow covering-set grep — the target doc is NOT actually orphaned.
  Grepping the covering set for the mechanism names (lst_yields, lst_rates, aave_oracle/AaveOracle, dex_pool_swaps,
  Curve, Orca/Raydium/Meteora) surfaced defi_consolidated_closeout_aggregated_sources_2026_07_24.md lines 160-180, which
  itself points to a fully active, non-draft plan NOT in the given 13-doc covering-set list:
  plans/active/lst_rate_honest_coverage_2026_07_21.md (status: active, created 2026-07-21, `related:` cites this exact
  target doc plus pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md). That plan's summary is a verbatim
  restatement of the target doc's four gaps ("#1 CEX spot = a Tardis backfill... #3 Aave oracle = the real code build...
  #2 DEX pool = a collector/endpoint fix... #4 protocol redemption = a features backfill + a Solana/LRT join fix") and
  its todo list (grepped directly) carries open, still-unchecked items covering every one of the target's 5 close
  actions: line 232 open [MTDS] P2 "#1 CEX-spot contiguity backfill — full-history Tardis backfill over *-SPOT LST
  venues" (= close action 2), line 264 open [FEATURES] P2 "#4 lst_yields backfill — run over the full lst_rates source
  history" (= close action 1), line 364 open [MTDS] P3 "#2 DEX fill — deep-backfill dex_pool_swaps once the endpoint
  lands" (= close action 3), line 371/375 open [STRATEGY] "A2 staking leg" / "Recursive-staking borrow leg — unblocks
  once #3 Aave oracle lands" (downstream of close action 4), and most of the Aave-oracle wiring itself (close action 4)
  is already [x]-checked done (lines 65-172: adapter built, venue registered, Chainlink feeds added, backfill run) —
  only the residual force/skip proof (line 158) is open. Close action 5 (Solana Orca/Raydium/Meteora zero-object gap) is
  separately tracked inside the given covering set itself: defi_satellite_ao_dispatch_batch1_2026_07_25.md line 120
  "[CODE] P1. Implement Orca Whirlpool tick-array binary decode", plus aggregated_sources' "+6 more" list names G7 Orca
  tick-array decode / G8 Raydium second pool as open P2 items. This is not a two-different-fixes conflict (no competing
  approach exists) — it is a clean duplicate: an already-active plan is executing precisely the close actions Phase 1
  flagged as uncovered, just outside the covering-set list this audit was scoped to check. Recommend: (a) correct the
  doc's Phase-1 classification from orphaned_never_touched to covered-by-active-plan-outside-given-set, (b) fold
  lst_rate_honest_coverage_2026_07_21.md into the defi covering-set inventory (defi_consolidated_closeout_2026_07_18.md
  or aggregated_sources' plan list) so future audits don't re-flag this doc, and (c) do NOT draft a new satellite-batch
  todo — it would race/duplicate lst_rate_honest_coverage's already-open todos on the same files/mechanisms.

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md`**: Conflict check (clean, no overlap): grepped all
  13 covering-plan-set docs for every file/mechanism name in the 4 uncovered §6 items (`jupiter.py`,
  `governance_params_event_poller`, `onchain_event_poller`, `alchemy_adapter`, `thegraph_ws_adapter`, `helius_solana`,
  `native_staking_handler`). Only one hit: `native_staking_handler.py` appears in
  `defi_satellite_ao_dispatch_batch1_2026_07_25.md` line 357, but that todo is about threading `mode=` into
  `assert_defi_catalog_fresh()` across 9 handlers — an unrelated mechanism, not the Helius-consolidation fix. No genuine
  overlap found; nothing else claims this ground. Confirmed exact uncovered items via re-read of §6 (lines 341-357): of
  the 6 listed follow-ups, only #5 (onchain/**init**.py docstring, P3) and #6 (curve_adapter._download_liquidity trace,
  P3) are cited by `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (lines ~182-195) and confirmed by
  `defi_consolidated_native_ao_extract_2026_07_25.md`'s own conflict-check (lines 136-146). The 4 remaining uncovered
  items are: 1. `jupiter.py::JupiterReferenceDataAdapter` (P2) — register as a live DeFi venue in
  `factory.py::_ADAPTERS["jupiter"]` OR delete the class + its 2 test files. 2. Governance-params-refresh
  re-verification (P1, doc's own 🔴 OPERATOR-NOTIFY banner, big/cross-repo/data-correctness-adjacent) — re-verify
  features-service `aave_risk_calculator.py` / strategy-service sizing against the measured fact
  `GovernanceParamsEventPoller` never runs in prod, then either wire it into a live entrypoint or update the plan/codex
  record to state the feature has never been live. 3. `adapters/defi/live/onchain_event_poller.py` +
  `adapters/defi_live/{alchemy_adapter.py,thegraph_ws_adapter.py}` (P2) — wire in or delete. 4.
  `onchain/helius_solana.py::HeliusSolanaAdapter` vs `native_staking_handler.py` (P2) — decide which implementation is
  authoritative and consolidate. Applying dispatch-scope eligibility: all 4 are explicitly framed by the source doc's
  own authors (who deliberately declined to make these calls in-pass) as binary product/design decisions, not safe
  unilateral code fixes — jupiter.py's disposition has stated downstream effects on UAC venue lists /
  `VENUE_TO_ADAPTER_KEY` / manifest schema / backfill scope / billing (a new live venue is a product decision); item 3
  is the same "wire in a whole new live-data feature vs delete tested code" shape with no existing successor to default
  to; item 4 requires choosing which of two working implementations becomes canonical (deleting the other) with no
  stated tie-breaker; item 2 already carries the doc's own 🔴 OPERATOR-NOTIFY banner (cross-repo,
  data-correctness-adjacent — features-service/strategy-service APR/sizing risk) and even its "re-verify" half depends
  on the wire-in-vs-document-as-never-live fork being resolved first. None of the four reduces to a worker-determinable
  bounded outcome without an operator ruling on the underlying product/scope question first. Recommended resolution:
  raise all 4 to the operator as a single batched decision request (jupiter venue: register or delete; governance
  poller: wire in now or document as never-live pending features/strategy re-verification;
  onchain_event_poller/alchemy/thegraph: wire in or delete; Helius: consolidate onto adapter or delete adapter) — once
  ruled, each becomes a trivially bounded, batchable AO todo executing the chosen branch.
- **`plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`**: Confirmed the Phase-1 finding: lines
  325-332 carry an unchecked
  `- [ ] [DATA] P2. Reconcile _INSTRUMENT_TYPE_ALIASES ... against the legacy venue_mapping.DataTypeConfig table` item,
  and grepping the exact mechanism name `_INSTRUMENT_TYPE_ALIASES` across the full covering-plan set (consolidated
  closeout, aggregated-sources, native-ao-extract+finalize, track01, track5, lending-writer-retire-prerequisite,
  gmx-removal+finalize, dex-pool-symbol-fix+finalize, satellite batch1+finalize) returns zero hits anywhere. Conflict
  check: 4 docs in the covering set (defi_consolidated_native_ao_extract_2026_07_25.md,
  defi_track01_per_instrument_and_canon_id_2026_07_24.md, defi_lending_writer_retire_prerequisite_2026_07_20.md,
  defi_consolidated_closeout_2026_07_18.md) DO mention A_TOKEN/DEBT_TOKEN, but on inspection all of them concern the
  separate LENDING→A_TOKEN/DEBT_TOKEN instrument_type RETIRE (write-side instrument_type value + GCS-path/manifest-row
  shard-atom desync across 8 MTDS writers, in instruments-service/MTDS/UTL repos, gated by the operator's D2 ruling).
  That is a different SSOT and a different mechanism from this doc's uncovered item, which is about UAC's
  `unified_api_contracts.registry.market_data_categories._INSTRUMENT_TYPE_ALIASES` table (used by
  `valid_data_types_for_instrument_type`, which feeds `enumerate_expected_universe`'s data_types resolution and
  `possible_manifest.is_valid_shard_key`) disagreeing with the legacy
  `venue_mapping.DataTypeConfig.instrument_data_types` table over which data_types (specifically `oracle_prices`) are
  valid for A_TOKEN/DEBT_TOKEN/LST/YIELD_BEARING tokens. No file/mechanism overlap — genuinely uncovered, not a
  duplicate of the retire work. However the doc's own text explicitly frames the fix as requiring a decision, not
  mechanical execution: "decide which table is the SSOT for these tokens' valid data_types (they currently disagree on
  oracle_prices)... That reconciliation is a genuine SSOT-contradiction call (cross-repo, orphan-sweep-adjacent) needing
  an explicit decision, not a fix bundled into a P1.3 materialization task." This mirrors the exact escalation pattern
  the sibling defi_lending_writer_retire_prerequisite_2026_07_20.md plan used for its own analogous A_TOKEN/DEBT_TOKEN
  SSOT-contradiction questions (todo 6: "Escalate as an option-set if it is not decidable from the naming SSOT"). The
  decision needed: which registry (UAC's `_INSTRUMENT_TYPE_ALIASES` vs the legacy `venue_mapping.DataTypeConfig`) is
  authoritative for A_TOKEN/DEBT_TOKEN/LST/YIELD_BEARING valid data_types — specifically whether `oracle_prices` is a
  legitimate data_type for these instrument types — because picking wrong silently misclassifies real captured
  `oracle_prices` cells as orphan candidates downstream in the phantom-reconciler/orphan-sweep. This is a bounded
  engineering task ONLY after that call is made; before that it is an undecided cross-repo semantic-SSOT ruling, so it
  does not meet dispatch-scope eligibility as-is. Recommend: operator rules on the SSOT question (likely
  alongside/adjacent to the existing D2 lending-retire ruling track since it touches the same token set), then a
  follow-up AO todo implements the chosen mapping into `_INSTRUMENT_TYPE_ALIASES`.
- **`plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`**: Confirmed via direct read:
  the doc's Todos list has 4 items. Todos 1 ([DATA] P1 scale measurement) and 2 ([DIAG] P1 content-sample/distribution)
  are cited and dispatched in defi_satellite_ao_dispatch_batch1_2026_07_25.md (matching Phase-1's "(2 todos)" tally).
  Todos 3 and 4 are NOT dispatched anywhere. Conflict check: grepped plans/active/ for "composite-venue",
  "legacy_precanonical", "fold-vs-migrate", "ETHENA-ETHEREUM". Only hit besides the target doc itself and the
  batch1/aggregated-sources citations is defi_track01_per_instrument_and_canon_id_2026_07_24.md (lines 203-216), which
  is an already-checked-off ✅ item describing the SAME finding and explicitly deferring: "Remaining: scale
  measurement + a targeted migration script — tracked in that issue doc, not re-duplicated here." No competing fix
  approach is proposed anywhere else — no genuine conflict, just the same single source of truth (the target issue doc)
  referenced from two places. Todo 3 is explicitly framed by the doc itself as a genuine, non-mechanical judgment call:
  "[OPERATOR] P1. Decision needed: fold ... vs. some other disposition — gated on the scale + sample-distribution facts
  from the two todos above ... This is a genuine judgment call, not a mechanical fix (per task_template.md's
  bounded-outcome rule) — do not execute a fold/migrate without this decision." That is a direct
  dispatch-scope-eligibility disqualifier (task_template.md finding + operator ruling 2026-07-23: an open-ended
  judgment/design call is a human decision, not an AO-eligible todo). Todo 4 ([PM] P2 file a migration plan) is
  sequentially gated on todo 3's outcome ("once scale + the fold-vs-migrate decision are both in hand") and therefore
  also not currently draftable as a standalone AO todo — its content (what the migration plan should even propose)
  cannot be determined until the operator rules on fold-vs-migrate. Both todo 3 and todo 4 must wait: (1) for batch1's
  todos 1&2 to complete and surface scale + distribution facts, then (2) for the operator to make the fold-vs-migrate
  call, at which point todo 4 becomes a bounded, batchable "file the migration plan reflecting decision X" todo.
  Recommended resolution: leave todo 3 as the doc's own gate; once batch1 finalizes, surface the fold-vs-migrate
  question directly to the operator (not through another AO dispatch draft) and re-run this extraction for todo 4 once
  that answer exists.
- **`plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`**: Read the target doc and
  confirmed Phase-1's evidence exactly. Of the 3 open todos, the VERIFY (P2) is dispatched by
  defi_satellite_ao_dispatch_batch1_2026_07_25.md (line ~546-549); the other two are explicitly excluded there (lines
  ~578-592) with detailed reasoning I independently re-verified against the source doc's own text. Conflict check:
  grepped defi_consolidated_closeout_2026_07_18.md, defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
  defi_consolidated_native_ao_extract_2026_07_25(+finalize),
  defi_dex_pool_symbol_fix_backfill_purge_2026_07_25(+finalize), defi_gmx_venue_removal_2026_07_25(+finalize),
  defi_lending_writer_retire_prerequisite_2026_07_20.md, defi_track01_per_instrument_and_canon_id_2026_07_24.md,
  defi_track5_coverage_mvp_backfill_2026_07_24.md, and batch1_finalize for "perp_daily_ctx". All hits are pure
  citations/status-tracking references (the aggregated-sources index restates the same 3 open todos verbatim;
  batch1_finalize lists it among docs to re-check for closure; track01 only mentions the data_type as part of an
  unrelated manifest-row filter). No other doc proposes a competing fix or claims this exact registration work — no
  genuine conflict. Remaining uncovered item: **[CODE] P2** — "Register `perp_daily_ctx` as its own canonical
  data_type + SchemaContract; add manifest writes to both ad-hoc writers (schema unchanged); backfill manifest rows for
  existing historical shard tuples" — gated on the VERIFY todo's finding. Applying the dispatch-scope eligibility test:
  this is NOT a bounded worker-executable outcome even after the VERIFY lands. The source doc itself explicitly flags
  this step as "needing operator awareness before autonomous execution," citing the SAME parent plan's own established
  precedent that a canonical-set addition to `DATA_TYPES_BY_ASSET_GROUP` is "NOT safe-code" (RESULT 4, venue-axis case)
  — it can silently expand the historical `expected_unattempted` universe and drop fleet-wide `completeness_pct`, and it
  registers a new type in the schema surface read live by `CanonicalPerpFundingProvider` (the live paper-trading
  reader). This is a genuine blast-radius/judgment call requiring an operator ruling on whether the risk is acceptable,
  not a determinable-by-worker-alone outcome — batch1's own exclusion reasoning reaches the identical conclusion
  independently. The 3rd item ([OPERATOR-DECISION] P3, whether to fold perp_daily_ctx into the perp_funding-demotion
  decision) is separately already queued as entry 4 in issues/autonomous_session_operator_decisions_2026_07_25.md
  awaiting the operator — no further action needed there. Recommended resolution: once the VERIFY finding lands (from
  batch1) AND the operator explicitly rules that a `perp_daily_ctx` data_type addition is safe (mirroring whatever
  ruling comes on the venue-axis precedent, or a fresh sign-off), the CODE todo becomes batchable as a follow-up in a
  future batch. Until then it stays parked — do not draft a competing/premature candidate_todo.
- **`plans/active/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`**: Confirmed uncovered: todo-2
  (reconcile the 2026-07-08 Balancer `@CHAIN` instrument_id patch against the 2026-07-18 Option-A ruling — revert vs
  ratify) and todo-3 (fix CURVE's still-bare colliding instrument_id) are not cited by any doc in the covering set. Only
  todo-1 (read-only audit/verify, explicitly told to flag not resolve) and todo-4 (codex port) are covered, both via
  `defi_satellite_ao_dispatch_batch1_2026_07_25.md` lines 305-325. Conflict check: grepped all 12 covering-set docs for
  curve/balancer/@CHAIN/cross-chain mentions. Hits exist in defi_consolidated_closeout_2026_07_18.md,
  defi_track01_per_instrument_and_canon_id_2026_07_24.md, defi_consolidated_native_ao_extract_2026_07_25.md,
  defi_dex_pool_symbol_fix_backfill_purge(_finalize)_2026_07_25.md, defi_gmx_venue_removal_finalize_2026_07_25.md — but
  every one of these is a DIFFERENT mechanism/bug: CURVE/OPTIMISM subgraph-deindex reclassification of
  `dex_pool_state`/`dex_pool_swaps` capture_status (unrelated to instrument_id collision), and Balancer subgraph
  `symbol` malformation (a different field entirely, not the `@CHAIN`-suffixed `instrument_id` patch). None touch
  `unified_api_contracts/canonical/crosscutting/defi.py`, `defi_catalog_reader.py:192`, or
  `balancer_cross_chain_pool_address_collision_backfill_2026_07_08.py`. No genuine overlap — this is not a duplicate.
  Dispatch-scope eligibility: the doc's own "Recommended fix" section is headed "not yet actioned — operator/plan-owner
  decision". Todo-2 is explicitly a two-option fork with no stated default ("either revert the patch ... or explicitly
  ratify Balancer as an intentional carve-out and document why") — an undecided design/policy call, not a checkable fact
  a worker can resolve alone. Todo-3 (the actual CURVE fix) is causally downstream of that fork: which mechanism to
  apply to CURVE (bare + rely on canonical_instrument_id, vs an @CHAIN-style suffix matching Balancer) depends entirely
  on which branch of todo-2 the operator picks. Additionally, the batch1 audit todo (in-flight, not yet run) is meant to
  produce end-to-end PASS/FAIL evidence per row that would inform this decision — drafting a CURVE-fix todo now, before
  that audit's findings land and before the operator rules on revert-vs-ratify, would prescribe a fix mechanism blind.
  Recommended resolution: operator should rule on todo-2 (revert Balancer's `@CHAIN` patch to bare, or ratify it as a
  carve-out) — ideally after batch1's audit todo produces its per-row PASS/FAIL findings — and only then should a
  combined "reconcile Balancer + fix CURVE consistently" AO todo be drafted against that ruling.
- **`plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`**: Confirmed via full read: the
  target doc's 4 open todos split as (1) VERIFY completeness_pct impact and (4) VERIFY the swaps_ohlcv_4h timeframe
  discrepancy — both explicitly covered by defi_satellite_ao_dispatch_batch1_2026_07_25.md lines 341-355
  (verbatim-matching "Source:" citations, confirmed by batch1_finalize.md line 85's "(2 todos)" count) — vs (2) execute
  Path A (build a `_DEFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`-style guard in enumerate_expected_universe.py, THEN add
  the 7 swaps_ohlcv_* keys to DATA_TYPES_BY_ASSET_GROUP['defi']) and (3) execute Path B (accepted-exception stopgap,
  `_ACCEPTED_EXCEPTIONS` in deployment-api/_distinct_values.py) — neither cited anywhere in the defi covering set.
  CONFLICT CHECK: grepped defi_consolidated_closeout_2026_07_18.md (only an index restatement, line 84),
  defi_satellite_ao_dispatch_batch1_2026_07_25.md/finalize,
  defi_track01/track5/lending-writer-retire/gmx-venue-removal/dex-pool-symbol-fix (+finalizes), and
  defi_consolidated_native_ao_extract docs for "swaps_ohlcv", "DEFI_MTDS_TICK_MANIFEST_EXCLUDED", and
  "enumerate_expected_universe" overlap. No other doc touches the swaps_ohlcv_* registry-addition or accepted-exception
  mechanism — gmx-venue-removal touches enumerate_expected_universe.py but for a wholly different venue-exclusion
  concern (GMX venue removal), not the defi data_types axis/guard. No duplicate or superseding claim found on todos
  #2/#3 specifically. Why NOT batchable: todo #2 is explicitly "(Gated on the verify above.)" in the source doc's own
  text — its correct execution depends on the completeness_pct simulation's measured output (safe-direct vs.
  needs-guard-first), which is produced by batch1's VERIFY todo. But batch1 is itself `status: draft` (not yet
  dispatched/executed) — its VERIFY hasn't run, so no measured answer exists yet to determine whether Path A can proceed
  directly or must build the guard first. On top of that time/sequencing gate, the doc frames Path A vs Path B as an
  explicit fork requiring judgment: Path A is "recommended if the exclusion-list work is done first," Path B is the
  fallback "if Path A's exclusion-list work is not prioritized soon" — the doc's own "Path B" section explicitly
  instructs whoever picks this up to "flag this semantic tradeoff explicitly to whoever approves it" (Path B trades
  correctness/precedent-consistency for lower risk/cost). This is a genuine two-option fork needing a prioritization
  ruling (is the guard-first work worth doing now, or take the interim stopgap?) compounded by a real dependency on an
  unexecuted prerequisite (batch1's VERIFY). Drafting an AO todo for either path now would either (a) presuppose an
  unmeasured simulation result, risking exactly the tradfi-precedent denominator-corruption failure mode this same doc
  documents in detail, or (b) silently pick Path B's lower-accuracy stopgap without the flagged tradeoff being
  operator-approved. Recommended resolution: once batch1's VERIFY todo lands (status flips off draft and the simulation
  report is produced), re-run this closeout-audit extraction for this doc — at that point either draft a
  Path-A-execution todo (if the report shows the guard is unnecessary or scopes exactly what guard to build) or ask the
  operator explicitly whether to take Path B as an interim stopgap. Do not draft a competing todo now.
- **`plans/active/issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`**:
  Conflict check: grepped the consolidated closeout plan's own todos plus every
  batch1/track01/lending-writer-retire/gmx-venue-removal/dex-pool-symbol-fix/track5(+finalize) doc for overlap on this
  doc's remaining ground. The 4 todos in defi_satellite_ao_dispatch_batch1_2026_07_25.md (lines ~386-419: [DATA] P1
  measure-scale, [BACKEND] P1 fix write_defi_rows leaf, [DOC] P1 correct canonical-cutover-register.md §5, [DOC] P1
  correct four-surface-reconciliation-procedure.md/reconciliation-finding-taxonomy.md) exactly and non-redundantly cover
  the doc's [DIAG], [CODE], and both [PM] todos — no other doc in the set independently claims the same ground with a
  different approach (defi_consolidated_closeout_2026_07_18.md:359-366 cites the same CODE fix redundantly via the same
  source doc, not a competing fix). No genuine conflict found. The ONE uncovered item is the P0 [OPERATOR] todo ("Decide
  the sequencing implication of Fact 1: stop active batch/backfill crons until the leaf-naming fix ships, accept the
  growing backlog, or expedite the fix") — nothing in the covering set contains this decision point, and the source doc
  itself frames it as "Options, not a recommendation from this doc — needs the plan owner's call." This is a genuine
  two/three-way operational fork (stop crons vs. accept backlog vs. expedite fix) with real tradeoffs (halting crons vs.
  data quality vs. schedule risk) that only the plan owner/operator can rule on — it is not a checkable fact or bounded
  worker-executable outcome, so it fails the dispatch-scope eligibility test and cannot be drafted as an AO-dispatch
  todo. Recommended resolution: surface this fork to the operator directly (e.g. via the next defi status update or
  Slack) referencing this issue doc's P0 todo; once ruled, the ruling itself (e.g. "stop crons X/Y/Z" or "expedite CODE
  fix to P0") could become a follow-on batchable todo.
- **`plans/active/issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md`**: No conflict with any
  covering-set doc (grep for test_collateral_validation.py, funding_ensemble_engine.py, CollateralValidationMixin,
  defi_enhancements across the full defi covering set returned zero hits — nothing else claims this ground). The blocker
  is a genuine three-way operator decision baked into the source doc itself: A) rewrite test_collateral_validation.py
  against the live v2 mechanism (catalog_staked_basis.py's build_carry_staked_basis() + staked_basis.py's
  _BANNED_LST_PERP_COMBOS) — doc's recommended option, restores real coverage; B) delete the dead-import file outright,
  leaving coverage to the (unverified-adequate) catalog/engine unit tests; or C) leave the file as dead code but flip
  the e2e-testing/scripts/defi/ QG lint block (strategy-service/scripts/quality-gates.sh lines ~137-148) from log_warn
  (non-blocking) to blocking, so a future dead import fails loudly without fixing this one. These are materially
  different outcomes (content fix vs deletion vs gate-hardening with no content fix) — not resolvable from the evidence
  alone, needs an explicit operator ruling on approach before a bounded AO todo can be drafted. Once the operator picks
  A, B, or C, a follow-up single-outcome todo (e.g., "rewrite test_collateral_validation.py per option A") becomes
  batchable. Separately, the doc's noted-not-filed follow-up (funding_ensemble_engine.py's hardcoded LST_VENUES =
  {"ETH": ("stETH","Bybit")} drift risk vs VENUE_COLLATERAL_MATRIX, zero strategy_service/UAC imports) remains genuinely
  unfiled and uncovered anywhere in the set, but the doc itself calls it lower-severity/exploratory-script — worth
  folding into whichever follow-up todo eventually gets drafted once the operator rules on the primary A/B/C decision,
  rather than spinning it out alone.
- **`plans/active/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`**: Confirmed via read: the doc's
  "Tracked follow-ups" section (lines 334-365) has 5 items. Item (1) HYPERLIQUID trades backfill re-run and item (3)
  delete retired perp_funding DeFi-routing residue ARE covered — item (3) verbatim in
  defi_satellite_ao_dispatch_batch1_2026_07_25.md lines 462-471 (cites this doc as Source, targets
  perp_funding_handler.py `_PROTOCOL_PIPELINE_SOURCE`/`_chain_map` hyperliquid/aster/lighter entries + the one-off
  script delete). Grepped item (1)'s HL-trades-backfill mechanism too and it is separately covered (not re-verified here
  since Phase 1 already confirmed it; focus was the 3 uncovered items). Conflict check (grep across the full covering
  set: consolidated closeout, both dispatch batches, track01, lending-writer-retire-prerequisite,
  gmx-venue-removal(+finalize), dex-pool-symbol-fix-backfill-purge(+finalize), track5, native-ao-extract(+finalize)) for
  the 3 remaining uncovered items' target files/mechanisms (`k-prefix`/`kPEPE`/`kBONK`/`kSHIB`,
  `_EXTRA_LIVE_PROBE_SOURCES_BY_AG`, `RULE 11`, `916 HL`/`642 ASTER`, `defi/perp_funding` reconciliation) returned ZERO
  hits anywhere except the batch1 residue-delete (item 3, already accounted for). The only proximate touch is
  defi_gmx_venue_removal_2026_07_25.md editing the SAME file (perp_funding_handler.py) but a DIFFERENT entry (gmx
  dispatch removal, not hyperliquid/aster/lighter routing or the 916/642 row reconciliation) — complementary, not
  overlapping, and not one of my 3 uncovered items anyway. No conflict found. All 3 remaining uncovered items are
  decision-gated, not worker-executable as bounded todos: - Item (2) HYPERLIQUID k-prefix case-sensitivity fix (FIX P3):
  the doc's own text says the fix "needs the canonical-vs-native HL coin-case convention resolved (risk of a shard-key
  mismatch)" — two plausible resolutions (normalize the catalogue side to native case vs. make the trade-row match
  case-insensitive) with a real risk of picking wrong and corrupting a shard key; this is a design call a worker cannot
  make alone, even though it lacks the literal "BLOCKED-OPERATOR-DECISION" tag the other two carry. - Item (4) reconcile
  916 HL + 642 ASTER defi/perp_funding legacy rows (INFRA P3): explicitly tagged BLOCKED-OPERATOR-DECISION in the doc —
  operator must pick delete-vs-re-home before any GCS mutation/index rebuild can run. - Item (5) extend live-probe
  mechanism to cefi CEX venues (FIX P3): explicitly tagged BLOCKED-OPERATOR-DECISION in the doc — requires an operator
  ruling to relax the RULE 11 `test_prediction_live_union_is_prediction_scoped_only` invariant before the UAC
  `possible_manifest.py` change can be made. Recommended resolution: raise all 3 to the operator as one batched decision
  ask (HL coin-case convention choice; delete-vs-re-home for the 916+642 legacy rows; RULE-11 relax-or-not for cefi
  live-probing). Once ruled, each resolves into its own bounded, worker-executable todo citing this same source doc —
  none is currently draftable as a safe AO-dispatch todo.
- **`plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`**: Confirmed via Read of
  the target doc's final section ("Needs an explicit operator ruling", lines 720-733) plus the 2026-07-23 reconciliation
  note (lines 738-749): the sole genuinely-open remaining item is a two-part semantic fork requiring an OPERATOR
  decision, not worker-executable bounded work -- (1) whether "ETH-underlying units" client-reporting means (A) a
  currency-preference view of already-computed USD PnL at today's rate, or (B) a genuinely different FX-noise-isolated
  "true native staking return" metric -- these visibly disagree over any multi-day window where the underlying asset's
  USD price moves, and (2) whether the two structurally-incompatible ShareClass enums
  (canonical.crosscutting.share_class.ShareClass {USDT,ETH,BTC} vs internal.architecture_v2.enums.ShareClass, 9 values)
  should converge to one canonical enum or stay intentionally scoped with a documented split. The doc itself explicitly
  frames this as "flagging, not picking." The already-shipped STAKING leg engine wiring (strategy-service@e93902d8) is
  NOT open against E2 -- that part is settled per the reconciliation note; only the reporting-layer dual-unit VIEWING
  work (wiring ShareClassFxMatrix to a real rate feed, un-orphaning convert_settlement_to_share_class, and the
  (A)-vs-(B) semantics ruling) remains, gated behind the operator's fork decision. Conflict check: grepped
  ShareClass/share_class/convert_settlement_to_share_class across the full defi covering-plan set (consolidated
  closeout, aggregated-sources index, satellite batch1+finalize, native-ao-extract+finalize,
  dex-pool-symbol-fix+finalize, gmx-venue-removal+finalize, lending-writer-retire-prerequisite,
  track01-per-instrument-and-canon-id, track5-coverage-mvp-backfill). Only one hit: defi_gmx_venue_removal_2026_07_25.md
  line 143, an already-checked-off (shipped) todo removing a GMX ShareClass.USDC catalogue entry -- unrelated to the
  enum-convergence ruling or the (A)-vs-(B) semantics fork, and already complete, so no genuine overlap. No other
  covering-plan doc touches this ground at all. Since the outcome hinges on an undecided design/judgment call the
  operator must make first (two mutually-exclusive client-facing PnL semantics + an enum-convergence-vs-scope-split
  decision), this cannot be turned into a bounded AO-dispatch todo now. Per the operating rules, this should be resolved
  via a LOCAL/interactive session posing the ruling to the operator; only after that ruling lands would a
  properly-scoped implementation todo (wiring ShareClassFxMatrix, un-orphaning convert_settlement_to_share_class per
  whichever semantics is chosen) become AO-eligible.
- **`plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`**: Read the target
  doc and confirmed the Phase-1 evidence exactly: todos 1-3 (measure scope, build the restamp script with dry-run/tests,
  ship via quickmerge — explicitly "Do NOT run --apply") are covered verbatim by
  defi_satellite_ao_dispatch_batch1_2026_07_25.md lines 172-181, which cites this doc by name as Source. Todo 4 is the
  target doc's own [OPERATOR]-tagged step: "Obtain operator authorization for a paused-writer apply window... identify +
  pause the relevant MTDS manifest-consolidator cron, run restamp_lending_instrument_type_2026_07_24.py --apply, confirm
  the post-write verification output, then resume the cron." The doc itself states "This is the human-only /
  operator-gated step — do not execute the pause or the --apply write without explicit operator authorization." Todo 5
  (post-apply verification against the distinct-values panel + cross-link back to the parent audit + close out this
  plan) is strictly sequentially dependent on todo 4's --apply having actually run (it re-pulls the honest-coverage
  rollup post-apply and diffs against the pre-apply baseline) — it cannot execute until todo 4 completes, so it inherits
  the same gate. CONFLICT CHECK: grepped defi_consolidated_closeout_2026_07_18.md and every
  batch1/track01/lending-writer-retire/gmx-venue-removal/dex-pool-symbol-fix/track5(+finalize) doc for
  restamp_lending_instrument_type / lending_instrument_type / paused-writer / manifest-consolidator-cron mentions. Found
  two adjacent-but-distinct hits, neither a real conflict: (1) defi_satellite_ao_dispatch_batch1_2026_07_25.md line ~553
  has an UNRELATED Kamino/Solend `lending_indices` instrument_type shape-conflict todo
  (`lending_indices_handler.py::resolve_lending_instrument_type()` vs a Track-2 GCS probe) — different handler file
  (lending_indices_handler.py, not liquidations_handler.py), different instrument_type values
  (solana_lending/solana_amm_pool, not liquidation/lending), different mechanism (read-only probe, not a manifest
  restamp). (2) defi_lending_writer_retire_prerequisite_2026_07_20.md documents a hardcoded-literal-vs-resolver desync
  also in lending_indices_handler.py — again a different writer/file than liquidations_handler.py (the target doc's
  writer, already fixed at mtds@fec20de2). Neither doc touches the liquidations_handler.py historical-restamp ground or
  the specific paused-cron/--apply mechanism. No genuine overlap. Recommended resolution: this doc's remaining ground
  (todos 4-5) stays un-batched as-is until an operator explicitly authorizes the paused-writer apply window — no
  candidate AO-dispatch todo should be drafted for it, since the doc's own authoring already correctly scoped items 1-3
  as AO-eligible (already batched) and items 4-5 as the human-only tail. No new todo/plan needed; this is expected,
  already-correct gating, not a coverage gap to fix.

## Deferred — time-gated (re-check on the next batch iteration)

- **`plans/active/issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`**: Not batchable now: this doc's own
  scope (Morpho adapter wiring + calendar-window backfill) is fully complete per the 2026-07-17 re-check #14 — the sole
  remaining item (re-run the G2 gate) is blocked purely on an external condition,
  `defi_onchain_v10_universe_v2_seed_or_backfill_progressed`, owned by `plans/active/data_completion_defi_2026_07_15.md`
  (not in this covering set) and shared with the sibling task `mvp_backfill_defi_onchain_v10-001`, which the
  consolidated closeout (`defi_consolidated_closeout_2026_07_18.md` line ~620) already tracks as parked on the identical
  condition. This doc's own backlog entry was hand-edited 2026-07-17 to `priority: 999` + the same prerequisite, so it
  will self-unblock and re-enter dispatch automatically once that condition flips — no covering-plan todo is needed or
  useful before then, and drafting one would just recreate the proven-dead 13-dispatch bounce cycle documented in
  re-checks #1-#13. Recommend: (1) no AO todo drafted for this doc at this time; (2) flag for the operator/covering-set
  author that `defi_consolidated_closeout_2026_07_18.md`'s existing gated todo could be broadened to also name
  `defi_morpho_lending_indices_never_wired-001` explicitly (both entries share the one condition) so a future closeout
  pass doesn't re-flag this doc as "uncovered" every cycle; (3) separately, the 2026-07-25 reconciliation-note flagging
  the worker's direct `backlog.yaml` hand-edit as a HARD-RULE violation is itself unresolved and belongs to whoever owns
  backlog.yaml governance, not to this doc's data-fix scope.
- **`plans/active/issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`**: Confirmed via direct read of § 6:
  the doc has 4 open items. Items (1) [terraform/scheduler wiring for staking-yields, doc's own "§ 6.1"] and (4) [codex
  defi-data-types-catalog.md § 7 Production-label fix] ARE covered — verbatim-matching todos exist in
  defi_satellite_ao_dispatch_batch1_2026_07_25.md lines 326-333 ([INFRA] P1, Source cites this doc) and lines 334-340
  ([DATA] P1, Source cites this doc, wording matches § 6's bullet almost exactly). Items (2) and (3) are NOT cited
  anywhere in the covering set (grepped defi_consolidated_closeout_2026_07_18.md,
  defi_consolidated_closeout_aggregated_sources_2026_07_24.md, defi_track01_per_instrument_and_canon_id_2026_07_24.md,
  defi_lending_writer_retire_prerequisite_2026_07_20.md, defi_gmx_venue_removal_2026_07_25(+finalize).md,
  defi_dex_pool_symbol_fix_backfill_purge_2026_07_25(+finalize).md, defi_track5_coverage_mvp_backfill_2026_07_24.md,
  defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md — zero hits on "shard leaf", "ticks.parquet",
  "StakingYieldsHandler", "capability-completion" tied to staking_yields). No genuine conflict either: track01's R2d
  item registers `lst_rates`-only capability coverage for venues like YEARN_V3/CONVEX/SYMBIOTIC/etc. and explicitly
  states the reverse ("`lst_rates`-only, not `staking_yields` — the staking_yields handler only covers
  LIDO/ETHERFI/EIGENLAYER, so registering it would manufacture a false MISSING") — different data_type, deliberately
  distinguished, no overlap with item (3)'s staking_yields capability-completion work. So this is genuinely
  orphaned-partial, not a duplicate. However, BOTH remaining items are explicitly, textually self-gated in the source
  doc on § 6.1 (the terraform/scheduler wiring todo) actually landing AND the handler actually running in production:
  item (2) reads "Once § 6.1 lands and the handler actually runs, verify the real per-venue shard leaf names match
  expectation..." and item (3) reads "Scope a capability-completion pass once § 6.1 confirms the 3 existing venues
  actually produce good data in production." As of this audit, § 6.1's terraform entry is only queued in batch1, not yet
  executed/verified — zero `instrument_type=staking` rows exist per the doc's own § 1.2 measurement across 6 sampled
  days. Dispatching (2) or (3) now would have a worker verifying shard names / scoping capability-completion against
  data that does not yet exist. This is a real external-event gate (first successful scheduled run producing live rows),
  not a design/judgment call and not a plan conflict — hence time_gated rather than operator_gated or batchable.
  Recommended resolution: re-run this Phase-3 extraction (or add a follow-up satellite-batch todo, gated via
  `depends_on` on the batch1 plan / its staking-yields terraform todo) once § 6.1 has shipped and at least one manifest
  row exists for `instrument_type=staking`.
- **`plans/active/issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`**: Confirmed the two uncovered items
  are Todo3 (P2 spot-check dex_pool_state/dex_pool_swaps coverage for all 4 protocols — UNISWAP_V2, UNISWAP_V4,
  TRADER_JOE_V2, VELODROME_V2 — across 2026-03→today, gated on "once the relaunched mtds-dex-pools-backfill VM (this
  session) + the running mtds-dex-swaps-backfill-1/2/3 fleet finish") and Todo5 (P3 manifest-level capture_status
  cross-check, explicitly gated on "once GCS network conditions in an agent sandbox are no longer measured at ~100 KB/s"
  — an environment-condition gate, not a deterministic worker-executable outcome today). CONFLICT CHECK: grepped the
  full defi covering set for dex_pool_state/dex_pool_swaps/mtds-dex-pools-backfill/mtds-dex-swaps-backfill overlap. No
  doc disputes or duplicates the SPOT-CHECK action itself. However there is a genuine entanglement, not a clean "no
  overlap": plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md (status: active, sequential: true) is an
  in-flight plan that will DELETE-and-full-historical-re-backfill dex_pool_state for exactly 2 of Todo3's 4 target
  protocols (TRADER_JOE_V2, VELODROME_V2 — via a different bug fix, the missing inputTokens/symbol-resolution query
  change) across their "full historical range," which necessarily spans the same 2026-03→today window Todo3 wants
  spot-checked. That plan's own todos are themselves gated ("Live-test whether 2022-era pool metadata is still
  indexed... before committing to a full historical backfill", "scoped only to the ranges confirmed recoverable") and
  not yet reported complete anywhere in the corpus. Dispatching Todo3 now risks either (a) spot-checking data that the
  symbol-fix plan is about to purge+rewrite out from under it (wasted/stale verification), or (b) racing the symbol-fix
  plan's own backfill+purge todos on the same underlying parquet leaves. This isn't a "two todos prescribe conflicting
  fixes" case (different bugs, compatible end-states) so it doesn't meet the bar for conflict_gated, but it does mean
  Todo3's precondition ("once the relaunched VMs finish") is BOTH externally time-gated (no evidence any of the three
  referenced VMs — mtds-dex-pools-backfill relaunch, the 3-way dex-swaps shard fleet — have reported completion anywhere
  in the corpus) and now additionally entangled with the symbol-fix plan's in-flight churn on the same cells for 2/4
  protocols. Recommended resolution: do not draft a standalone spot-check todo yet; either (1) fold the spot-check into
  defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md's own post-backfill verification step once that plan's
  sequential chain reaches its re-backfill todo (natural ordering point), or (2) re-surface this issue doc for
  AO-dispatch batch2 once BOTH the three original VMs AND the symbol-fix plan's re-backfill todo report done. Todo5 is
  independently time-gated on transient sandbox network conditions and not itself blocking anything — no action needed
  until that condition changes; a future audit pass can re-check.

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`plans/active/issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`**: Confirmed via Read: Item 2
  (4 zero-capture protocols) is closed per the doc's own 2026-07-25 update (wired 2026-07-14, verified 2026-07-24,
  residual TRADER_JOE_V2/VELODROME_V2 gaps already dispatched in defi_satellite_ao_dispatch_batch1_2026_07_25.md). Item
  1 (batch_onchain_subgraph bare-0x-address.parquet second writer path, live for CURVE, needing a
  pool-address→symbol/venue/chain resolver plus a VM-eligible historical migration over genuinely-live production data)
  remains open. Conflict check: grepped the full covering set for
  `batch_onchain_subgraph`/pool-address-resolver/bare-0x-address language. Two files match the string
  `batch_onchain_subgraph` but neither addresses this doc's Item 1: (1) defi_satellite_ao_dispatch_batch1_2026_07_25.md
  uses the term only to fix a source-label ambiguity (Tier-4 defillama_historical_ratio rows mislabeled with the same
  pipeline_mode as genuine on-chain rows) and separately to correct a stale "no new defi writes" claim in the cutover
  register — neither touches the CURVE address-only-file shape or a resolver. (2)
  defi_track01_per_instrument_and_canon_id_2026_07_24.md uses the term in an unrelated finding (Solana ORCA/RAYDIUM
  dex_pool_state collector producing zero canonical-shape shards since before a 2026-06-08 pause). No doc in the set
  proposes or claims the resolver/migration Item 1 describes — this is not a duplicate and not stale on the other side;
  it is genuinely uncovered. Dispatch-scope eligibility: this fails the bounded/single-worker-checkable test. It
  requires (a) confirming/locating or building a pool-address→symbol/venue/chain resolver against the reference-data
  catalog (an open design question — "likely already exists," unverified), then (b) scoping and running a VM-eligible
  historical backfill/transform over a currently-live production data shape with backup-first safety requirements. The
  doc's own 2026-07-25 re-check (written under the same ag-closeout-audit batchN methodology this task follows) already
  explicitly self-classifies this as "too-large/risky... not a bounded, single-worker-checkable batchN todo... needs its
  own dedicated triage/design pass as a standalone plan when picked up." Agreeing with that self-assessment: this is not
  a batchable todo. It should be picked up as its own dedicated LOCAL/human-planning triage-and-design session first (to
  resolve the resolver-source question and scope the migration), only after which a properly-bounded AO todo could be
  drafted against that decision's outcome. No new candidate_todo drafted; the doc's own recommendation (re-check again
  only if the resolver/scope question is independently investigated elsewhere first) stands.

## Deferred — human-only (needs a dedicated engineering/design session, not an AO todo)

- **`plans/active/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`**: Confirmed via full read: the
  doc's 4-step fix chain is only partially covered. defi_satellite_ao_dispatch_batch1_2026_07_25.md's 2 cited todos
  cover (a) a DIAGNOSTIC-only pass on the frozen onchain consolidator (fixes only if trivial; otherwise "remediation
  stays open pending a human design decision" — so step 1 does not definitively close, and step 2 "re-derive the index
  from producer-honest shards" is explicitly not attempted at all, since it depends on step 1's outcome) and (b) the
  count-provenance anomaly investigation (fully covers the "not chased here" aside — no further action needed on that
  thread). Neither that todo nor anything else in the covering set (grepped defi_consolidated_closeout_2026_07_18.md,
  aggregated_sources, native_ao_extract±finalize, dex_pool_symbol_fix±finalize, gmx_venue_removal±finalize,
  lending_writer_retire_prerequisite, track01, track5 for
  `ltv|liquidation_threshold|reward_rate|flash_loan_liquidity|health.factor|feature-less|onchain_manifest_dishonest`)
  touches step 3 (build missing MTDS chain-field collectors: ltv, liquidation_threshold, reward_rate,
  flash_loan_liquidity, health-factor inputs) or step 4 (recompute the 5 feature-less groups).
  defi_consolidated_closeout_aggregated_sources_2026_07_24.md's "0 open todos" claim for this doc is contradicted —
  steps 2-4 have zero citation anywhere. CONFLICT CHECK: no doc prescribes a competing/different fix for the same file
  or mechanism — this is pure absence of coverage, not a duplicate or contradiction. One soft, non-blocking overlap
  worth flagging: defi_gmx_venue_removal_2026_07_25.md independently touched (and currently keeps PAUSED, pending
  a >=4-cycle durability watch before resume) the shared `uts-prod-manifest-consolidator-market-data-defi-cron` used for
  its own surgical row-removal work — this is the same physical consolidator process Track 8 claims is "ENABLED, running
  every 1 minute" per batch1's diagnostic todo. This is a live-state dependency (any onchain-consolidator diagnosis
  should account for the cron's current paused/resuming status) but not a competing prescribed fix, so it does not gate
  this into conflict_gated. DISPATCH-SCOPE VERDICT: steps 2-4 are not AO-batchable as a single bounded todo. Step 2 is
  contingent on step 1's still-undecided outcome (the covering todo explicitly defers to "a human design decision" if
  non-trivial) — its scope literally cannot be fixed today. Steps 3-4 are, in the source doc's own words, "genuinely new
  scope (upstream collection)... size them as their own work, not as part of mark→recompute" — building missing MTDS
  chain-field collectors (ltv/liquidation_threshold/reward_rate/flash_loan_liquidity/health-factor inputs) across the
  onchain lending protocols requires deciding which chain APIs/protocols to source each field from, schema design, and
  which of the 5 feature groups to prioritize — an open judgment/design call, not a checkable worker-alone outcome. This
  is directly analogous to the sibling ORCA/RAYDIUM Solana indexer finding in
  defi_consolidated_native_ao_extract_2026_07_25.md, independently ruled `[DESIGN] P3`/human-only under the same
  dispatch-scope rule ("genuinely new capability... file a dedicated implementation plan when this becomes a priority").
  Recommend: once step 1's consolidator diagnosis lands (from the already-dispatched batch1 todo) and the operator rules
  on the design question it surfaces, THEN author a dedicated scoping/design plan for steps 2-4 (likely as its own defi
  satellite doc) — that scoping plan, not this audit, is where a properly-bounded AO todo for the MTDS collector build
  would first become extractable.
- **`plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md`**: Conflict check found no genuine conflict:
  defi_consolidated_native_ao_extract_2026_07_25.md (line 170) already independently classified this exact doc as
  human-only for the same reasons. No plan in the covering set attempts to build the indexer, generalize the sig-index
  script, or author the implementation plan. The item stays uncovered by design — it is gated on an operator priority
  decision ("when this becomes a priority") plus genuine design/architecture judgment (protocol-specific Solana
  instruction decoding), not a worker-executable, bounded todo. Recommend: leave as-is until the operator explicitly
  prioritizes this capability, then a human authors plans/active/<new>_solana_dex_pool_swaps_indexer_<date>.md directly
  from the doc's existing 5-step breakdown rather than routing it through AO dispatch.

## Note — 1 mistag found, not actioned here (flag for a follow-up retag)

- `plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` — tagged
  `asset_group: [defi]` only because it was discovered while shipping a DeFi Fluid-adapter fix, but the doc's actual
  content is a fleet-wide QG STEP 5.101 (empty-string-fallback ratchet) infra/CI issue spanning multiple repos, not
  defi-specific. Should be retagged (likely `cross-cutting` or `infra`), not archived or folded into a defi batch.

## Note — a second mistag found during Phase-0 discovery (locked, not retagged here)

- `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` is tagged bare `[cross-cutting]`
  despite its `defi_`-prefixed title (the skill's "fork inherits parent's cross-cutting tag" pattern) — its content
  (collateral-aware sizing, USDC down-size branch, stables-only opportunity-checker scoring) reads as
  defi/staked-basis-specific, but the doc also describes "full wizard parameterization for all supported archetypes,"
  which could be genuinely cross-cutting wizard tooling. This is ambiguous enough to need a real read, and the doc is
  `locked_by: live-defi-rollout` (someone else has it locked) — flagged for the finalize plan's follow-up rather than
  retagged unilaterally here.

## Note — 1 doc found archivable_now (not actioned here — a separate archival todo, not a batch candidate)

- `plans/active/issues/mtds_perp_funding_backfill_hang_2026_07_14.md` — all 5 todos are checked with detailed completion
  evidence (root-cause confirmed, defensive guard shipped market-tick-data-service@5a163d02, endpoint fix shipped
  @56efdd7d, VM relaunch verified end-to-end on live infra). Ready for the standard 6-step archival ritual; not drafted
  as an AO todo here since archival itself needs no AO worker judgment call.
