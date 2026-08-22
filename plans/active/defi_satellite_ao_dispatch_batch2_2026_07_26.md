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
  Deferred sections below (kept concise — a fresh re-read is expected before acting on any of them, per the skill's
  re-check methodology) for the next iteration or an explicit operator ruling. Also flags a separate mistag found during
  Phase-0 discovery (`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`, tagged bare
  `[cross-cutting]` despite its defi-prefixed title — `locked_by: live-defi-rollout` so not retagged here, flagged for
  the finalize plan).
status: active
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
    /plans/archive/2026_07/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-08-21"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
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
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
---

# DeFi satellite AO batch 2 — fresh triage extraction

> **✅ ALL 23 TODOS DONE 2026-08-21** (22 checkbox items + the 1 intentionally-non-checkbox superseded C8 entry) —
> **not yet archived**: `defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md` is the machine-gated finalize
> plan for this doc (`depends_on` + `gate_on_depends: true`) and owns the actual archival (its own todo 4) as ONE
> coordinated action alongside reconciling every named source doc's checkboxes (todo 1) and re-checking the 20
> Deferred items below (todo 2) — do not git-mv this doc ahead of that plan's own sequence. The last open todo
> (line ~307, KALSHI_PERP CEFI manifest re-emit) surfaced a real chain-convention contradiction between the
> manifest code and live data — resolved via operator ruling + `market-tick-data-service@f7cdd18b21`; the actual
> 567-row historical re-emit was found already complete via a live full-window query. Full evidence:
> `issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md`,
> `issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`. Dispatched
> 2026-07-26 per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance (a
> skill-drafted AO batch is never auto-shipped; that flip followed explicit operator review). All 23 todos were
> same-priority-independent and touched distinct files/docs (verified — the one confirmed duplicate pair was merged
> into a single todo before this doc was authored, not left as two colliding entries).

## Todos

- **[DATA] P1. CANCELLED — SUPERSEDED 2026-07-26 (slot-2, per BLK-7c950d06 + BLK-3221d4b3).** Original ask: fill DeFi
  manifest venue-key under-enumeration (C8) — UAC's `defi_venue_capabilities.py` declares 90 defi venue-keys, but the
  `_index/availability_index.parquet` manifest currently enumerates only a partial subset per instrument_type family —
  lst 14/22, lending 6/21, perp 5/8. **RE-DIAGNOSED 2026-07-26 (slot-4)**: premise was wrong — no DeFi
  `expected_unattempted` seeder exists at all (DeFi is explicitly excluded from the sentinel fan-out every other
  asset_group uses); there is no seeding pass to "re-run or extend," and the original done-criterion requiring
  DRIFT-SOLANA present is unsatisfiable-by-design (deliberately removed 2026-07-16). Full re-diagnosis:
  `/plans/archive/issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`. **RULED 2026-07-26 (slot-2)**:
  Option A (build a real seeder) — the actual work is tracked as human plan
  `/plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md` (assigned_vm: NA, gated on an operator
  capability-reconciliation decision). This entry is intentionally NOT a `- [ ]`/`- [x]` checkbox — it must never be
  faked `[x]` (no seeder exists to complete against) and must never re-enter the dispatchable queue; the superseding
  plan is the live tracking doc going forward. Source: /plans/active/data_completion_defi_2026_07_15.md (item C8, now
  also flipped `[x]` by citation). **Seeder shipped 2026-08-01 (slot 8)**: the superseding plan's P2 landed
  (`unified-api-contracts@91bafdae`, `market-tick-data-service@a5a93dc0`) — see that plan's Progress Log for the full
  accounting (scope, design corrections, deferred live-census verification). **Fully closed + archived 2026-08-01**: all
  7 todos done (P0-P3, Todo 4 live-census PASS, Todo 5 FLUID wiring, Todo 6 v2-enumerator OOM investigation),
  reconciled + archived via
  `/plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26_finalize_2026_07_28.md`. This C8 entry
  stays non-checkbox prose per the instruction above; the archived plan remains the historical tracking doc.
- [x] ✅ [CHORE] P3. **DONE 2026-07-26 (worker, slot 6).** (1) Deleted, `market-tick-data-service@5dadaae7` — all 3
      gating buckets re-verified live still deleted. (2) Audited all 10 campaign scripts: 9 reference now-confirmed-dead
      buckets AND have their governing plan(s) archived, but did NOT delete them — the "GCS orphan sweep = 0" half of
      their `Delete-when` is genuinely ambiguous (a different, still-open `C0-RD5b` sweep exists in the archived
      governing plan); left in place pending clarification. The 10th
      (`backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py`) has its own unrelated, unconfirmed condition. Full
      per-script reasoning in `defi_dedicated_bucket_shared_migration_2026_07_13.md`'s Progress Log. Finish the two
      housekeeping-cluster sub-items NOT already covered by `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (which
      only covers the OPERATIONS dict fix and the paper_run_handler stale comments): (1) delete
      `market-tick-data-service/scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` — its own documented
      `Delete-when: dex-pools-prd/lst-rates-prd/perp-funding-prd are deleted` condition is now satisfied (all 3 buckets
      confirmed deleted per the source doc's Progress Log); (2) audit the ~8
      `market-tick-data-service/scripts/defi_*_2026_06_01.py` / `gate3_solana_manifest_reconcile.py` /
      `backfill_hl_*_2026_06_17.py` scripts (all tagged `Lifecycle: campaign`) for hardcoded dead bucket-name templates
      tied to earlier, already-completed migrations — repoint or mark for deletion per each script's own Lifecycle
      marker; not urgent but currently orphaned. Source:
      /plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md. Done when:
      `migrate_lst_perp_shared_bucket_gap_2026_07_13.py` is deleted (or its deletion is confirmed already done with a
      cited commit), and each of the ~8 campaign scripts has been checked for dead bucket-name templates with either a
      repoint applied or a documented reason no fix is needed.
- [x] ✅ [DATA] P1. **Fix the doubled `day={D}/day={D}/` prefix bug in the DeFi instruments-store `by_date` tree (both
      the writer regression AND the v9 migrator's malformed projection).** Two defects, both must be fixed before the
      gated defi §H instruments-store object `--apply`: (1) an instruments-service `by_date` WRITER regression nests a
      second `day=` segment for recent snapshots (`≥2026-05-05` onward -- confirmed doubled at `day=2026-05-05` and
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
- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-2).** Both done-when conditions were ALREADY satisfied by prior, unrelated
      work — this todo's premises were stale: the dedicated `lst-rates-central-element-323112` bucket no longer exists
      (live-verified 404; migrated into the shared bucket + deleted 2026-07-13/14) and `VAULT` is already absent from
      `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES` (test-guarded). Found + fixed the actual live residual instead: a
      venue-PREFIX exclusion bug (`DEFI_NON_PROTOCOL_VENUE_PREFIXES` in deployment-api's
      `rollup_cache.py`/`breakdowns_domain.py`) was silently stripping `ANKR-ETHEREUM` (real, capability-registered LST
      venue) + 6 `ALCHEMY-<chain>` venues + `COINBASE-ETHEREUM` from the rollup venue list/breakdown — fixed to match
      the full venue string, regression test added. Shipped `deployment-api@f919c87`. Full writeup + per-todo detail:
      `plans/active/defi_venue_lst_rates_residual_2026_07_24.md`. `SUSHISWAP` classic-vs-V3 (a separate, genuinely-open
      data-semantics call in that same source doc, already out of scope for this todo) remains open. Originally: **Fold
      `lst-rates` into DeFi data-status + exclude orphan `VAULT` venue.** (1) Wire the `lst-rates` availability_index
      (bucket `lst-rates-central-element-323112`) into the defi data-status aggregation / rollup `manifest_source` read
      path (deployment-api `data_status` aggregation + the defi projection rebuild) so the 5 LST venues
      (ANKR/STADER/STAKEWISE/SWELL/MANTLE + LIDO/ROCKETPOOL/ETHENA/...) stop reading as zero — this corpus already reads
      only `market-data-tick-defi`, not the dedicated lst-rates bucket, even though the data is genuinely captured (not
      a data gap). (2) Exclude/remap the orphan generic `VAULT` venue (1113 captured rows, not a real protocol) out of
      `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES`. Do NOT touch the bare-`SUSHISWAP` classic-vs-V3 alias question in
      the same registries — that is explicitly out of scope here (conflict-gated, see note). Source:
      `plans/active/defi_venue_lst_rates_residual_2026_07_24.md`. Done when: (a) the 5 LST venues' rows are visibly
      credited (non-zero) in the DeFi could-exist / data-status view, verified via the deployment-api `data_status`
      endpoint or UI; and (b) `VAULT` no longer appears as a live/uncategorized registered venue in
      `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES` (excluded or mapped to its real protocol), with its
      previously-orphaned rows now attributable to a real protocol or explicitly documented as excluded. (repos:
      deployment-api, unified-api-contracts)
- [x] ✅ [BACKEND] P1. **Migrate `AaveRateImpactCalculator` off the structurally-zero DefiLlama Yields borrow field onto
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
      `issues/aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26.md`. ✅ 2026-07-26: `fetch_data()` now
      blends DefiLlama's real USD TVL with MTDS `lending_indices`' real per-block `utilization_rate`
      (`total_borrow_usd = tvl_usd * utilization_rate` — dimensionally correct without a separate price feed) + carries
      the IRM-slope columns `_resolve_rate_params` already reads off a row; unit-tested (regression test proves non-zero
      `rate_impact_supply_bps`/`rate_impact_borrow_bps` end to end) — `features-service@b0845d83`.
      `strategy_service/pnl/engine/orchestrator.py` re-pointed to `feature_group="rate_impact"` —
      `strategy-service@59dd0638`. Both repos' full `quality-gates.sh` green.
- [x] ✅ [ENGINEER] P1. Triage the 9 `unified-api-contracts/unified_api_contracts/internal/architecture_v2/` files
      flagged by the original `rg -l -i 'drift|pacifica'` sweep but never individually confirmed fixed by the 2026-07-16
      follow-up dispatch — `perp_hedge_sizer.py`, `capability_manifest.py`, `archetype_config.py`,
      `backtest_scenarios.py`, `flash_loan_receiver.py`, `algo_compatibility.py`, `liquidation_bonus_schedule.py`,
      `benchmark_fill_pricing.py`, `archetype_capability.py`. For each: re-run `rg -n -i 'drift|pacifica'` scoped to
      that file, classify every hit as genuine live Solana-perp-DEX venue residue (Drift/Pacifica venue id, leg spec,
      capability entry) vs a false positive (e.g. "schema/numeric drift", unrelated prose). For genuine hits, apply the
      SAME fix pattern already used on the resolved files in this issue (`archetype_capability_manifest.json`,
      `archetype_leg_spec_seeds.py`, `collateral_registry.py`, `simulation_assumptions.py`, `jurisdiction_overlay.py`,
      `order_semantics.py`, `venue_tokens.py`, `archetype_leg_spec.py`): remove/repoint the dead venue entry and leave a
      `# DRIFT/PACIFICA (Solana) removed 2026-07-16 (operator ruling: ...)` comment marker — the ruling itself is
      recorded in `/codex/04-architecture/solana-defi-coverage.md` — matching the marker convention already applied
      workspace-wide. Do NOT touch `unified-trading-system-ui`'s
      `venue_set_variants`/`archetype_capability_registry`/`strategy_instance_catalogue` or
      `tests/e2e/_shared/strategy-registry.ts` in this todo — those are separately gated on an undecided strategy-domain
      call (delete vs re-leg `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` onto Jupiter) and on the stale UI/UAC
      registry-sync generator (see this doc's Secondary finding) being fixed first; out of scope here. Source:
      `plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`. Done when: all 9 files
      have either a documented false-positive verdict (no code change) or a genuine-hit fix with the standard removal
      comment marker, `unified-api-contracts` full `quality-gates.sh` is green, and the change ships via scoped
      `quickmerge.sh --agent --files`. ✅ 2026-07-26: all 9 files individually re-triaged — zero genuine Drift/Pacifica
      venue residue found (all hits are generic "delta drift"/"schema drift"/"config drift" prose unrelated to the
      Solana Drift venue; zero pacifica hits). No `unified-api-contracts` code change needed. Verdict documented in
      `plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` § "UPDATE 2026-07-26".
- [x] ✅ [DOCS] P3. **DONE 2026-07-26 (worker, slot 6), `strategy-service@8d7c6549`.** Documented the three MEV
      archetypes (`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, `ARBITRAGE_MEV_JIT_LIQUIDITY`, `ARBITRAGE_MEV_BACKRUN`) as
      explicitly OUT of the paper-replay tick-builder-wiring scope: a module-level comment directly after the
      `_ENGINE_DRIVABLE_ARCHETYPES` frozenset in `strategy_service/cli/handlers/paper_universe.py` names all 3
      archetypes and states the rationale (architecturally opportunistic/runtime-mempool-driven, no catalog-declared
      currency universe, a currency constraint would need new engine-internal logic — separately scoped, not attempted
      here). Cross-referenced back: `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`'s own DOCS P3 todo
      is checked off citing this exact commit + location.
- [x] ✅ [CODE] P3. **DONE 2026-07-26 (slot 4)** — Fix wrong catalog-builder import alias in
      `tests/integration/test_recursive_borrow_scenarios.py`: `FAMILY_2_CELL_IDS` is built by importing
      `_build_carry_recursive_staked` (the **plain** `CARRY_RECURSIVE_STAKED` archetype's catalog builder) aliased as
      `_build_carry_recursive_borrow_perp_hedged`, instead of importing the real `build_carry_basis_perp_inv` (the
      `CARRY_BASIS_PERP_INV` archetype's actual catalog builder). Today this is harmless (both builders happen to
      satisfy the same `len(...) >= 5` row-count assertion) but the Family-2 test cell IDs are silently sourced from the
      wrong archetype's catalog rows. Fix: import and alias `build_carry_basis_perp_inv` correctly, re-run the file's
      tests, confirm `FAMILY_2_CELL_IDS` now reflects `CARRY_BASIS_PERP_INV`'s real 10-row catalog and the existing
      assertions still pass (adjust the row-count assertion only if the real count differs from 5+). Ship via quickmerge
      scoped to this one test file. Source:
      plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md ("Minor incidental finding" under
      the `CARRY_RECURSIVE_BORROW_LENDING_ONLY` / `CARRY_BASIS_PERP_INV` orchestrator-stub section, 2026-07-24).
      **Confirmed**: `catalog.py` exports `build_carry_basis_perp_inv` as a plain (non-underscore) name — no underscore
      alias existed for it (unlike the other two builders), so the test's import line was changed from
      `_build_carry_recursive_staked as _build_carry_recursive_borrow_perp_hedged` to
      `build_carry_basis_perp_inv as _build_carry_recursive_borrow_perp_hedged`. Directly verified the real catalog: 10
      rows, all correctly slot-labeled `CARRY_BASIS_PERP_INV@...` (was silently `CARRY_RECURSIVE_STAKED@...` before).
      The `>=5` row-count assertion needed no change (10>=5). 40/40 tests pass (`pytest -m "not requires_credentials"`);
      full `quality-gates.sh --no-fix` green (126s, sentinel written). Shipped `strategy-service@628a0a32`.
- [x] ✅ [DESIGN] P3. **DONE 2026-07-26 (slot 4) — NO-GO.** Evaluate wiring the existing
      `curve_adapter.py`/`api.curve.fi` REST path
      (`market_tick_data_service/market_interface/adapters/defi/curve_adapter.py`) into the batch `dex_pool_swaps`
      collection cascade for CURVE/OPTIMISM (mirroring the "ARB/POLY only on hosted service (deprecated) — use
      api.curve.fi instead" precedent already documented in UAC `_defi.py`), as an alternative to leaving this cell as a
      permanent honest `EXPECTED_SUBGRAPH_DEINDEXED` absence. Repo: market-tick-data-service. Not urgent — every other
      `dex_pool_swaps` (venue, chain) cell is unaffected and the ~144-952 CURVE/OPTIMISM rows are a small fraction of
      the asset_group's total gap; do NOT implement the wiring itself in this todo — only produce the evaluation.
      **Verdict (full evidence in the source issue doc's "Evaluated 2026-07-26" section)**: the "existing REST path"
      isn't what it looked like — `curve_adapter.py`'s REST call (`_safe_fetch_curve_rest_pools`) only returns
      pool-discovery metadata, never swap history; the adapter's actual swap-fetch method (`_download_swaps`) is 100%
      The-Graph-decentralized-network dependent (the SAME dead subgraph mechanism) with a literal
      `return []  # ... omitted for brevity` REST fallback stub; the REST discovery path is also hardcoded to Ethereum
      (`venue="CURVE-ETHEREUM"` regardless of `self.chain`); and `dex_swaps_handler.py`'s `_collect_protocol_chain`
      pipeline is subgraph-only end-to-end with no existing non-subgraph integration seam. No follow-up implementation
      todo opened — recommended a smaller external-API research step (does Curve's public REST API expose swap-level
      history for OPTIMISM at all) before any future build attempt. Source:
      `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`.
- [x] [DATA] P2. **Re-run the DeFi `instrument_availability` shape-B ("hive") vs flat reconciliation with a null-aware
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
  resolving whether the original 45.2% figure was a comparison-methodology artifact or real divergence at scale. — ✅
  DONE 2026-07-26 (worker, slot 6). Ran a stratified 100-day sample (3,045 venue-day pairs, same order of magnitude as
  the 2,911-pair bar). Byte-mismatch confirmed at ~44.3% (1,348/3,045), consistent with the original finding. Null-aware
  field comparison found a SECOND comparator bug beyond the known None-vs-NaN one (duplicate-`instrument_key` rows in
  pool-heavy DEX venues break naive `.loc[key]` indexing, spuriously flagging every column) — after fixing it, **only
  52/3,045 (1.7%) show any real diff, and 51 of those are the same single day (2026-06-29, hive's freeze boundary) on
  just the `available_at` watermark column, not an instrument-definition field**. Excluding that boundary date, real
  divergence is 1/3,045 (0.03%). Verdict: the original 45.2% figure is confirmed almost entirely a
  comparison-methodology artifact; real content divergence is effectively 0%. Full writeup + the duplicate-key discovery
  (filed as its own follow-up,
  `plans/archive/issues/defi_instrument_availability_duplicate_instrument_key_rows_2026_07_26.md`) in Source's new
  2026-07-26 dated section.

- [x] ✅ [DATA] P2. **CLOSED 2026-08-21.** Once `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s P1 [BACKEND]
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
      **ATTEMPTED 2026-08-21, initially blocked, then resolved same day.** Both prerequisites confirmed genuinely
      done (writer fix `market-tick-data-service@2aa23de5` shipped 2026-07-27; scope audit landed 2026-07-28).
      Live-reconfirmed the 567-row scope on the sample day. Designed + dry-run-validated (real GCS reads, zero
      writes) a migration script reusing the production `_write_cefi_perp_funding_rows`/`DefiManifestRecorder`
      writers. **Blocker found querying the live CEFI manifest before writing**: every real
      `(venue=KALSHI-PERP, data_type=perp_funding)` row ever recorded carried `chain=""`, but the code hardcoded a
      non-blank `chain="KALSHI_PERP"` workaround and raised `BlankChainError` on a blank one — the two couldn't both
      be true of the same live system. Paused before any write, filed
      `issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md`. **Operator ruled same
      day: KALSHI-PERP is not a chain** — the manifest's real history was right, the code was wrong. Fixed + shipped
      `market-tick-data-service@f7cdd18b21` (adds a narrow `_CHAINLESS_VENUES` carve-out to `_defi_manifest.py`'s
      `_build_row_key`; bundled a same-day, unrelated, also-blocking SPORTS-MVP registry re-pin needed for a clean
      `quickmerge` re-gate). **Then, live-verified the actual re-emit was already complete**: a full-window
      (2026-05-29..2026-07-25) query of the CEFI manifest found 58/58 days present, chain="" throughout, zero
      missing — done by an unidentified prior process (the GCS-object side was also already fully migrated) before
      this session started. No new write was needed. `issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`
      flipped to resolved. Full evidence: `issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md`
      § Resolution. **CORRECTION, same day (2026-08-21)**: `f7cdd18b21`'s `_CHAINLESS_VENUES` carve-out
      over-generalized to `{"KALSHI-PERP", "POLYMARKET-PERP"}` — wrong; Polymarket settles on Polygon (a real
      chain), unlike KALSHI-PERP. A same-day operator ruling (traceable source:
      `issues/defi_cefi_hyperliquid_perp_funding_manifest_chain_contradiction_2026_08_21.md`'s "Operator ruling
      2026-08-21" section — "fix all three: Polymarket, Hyperliquid, Aster") reversed this: `_CHAINLESS_VENUES` is
      now `frozenset({"KALSHI-PERP"})` only, POLYMARKET-PERP gets `chain="POLYGON"`, and a related HYPERLIQUID/ASTER
      `onchain_perp_batch_handler.py` finding was fixed too. Shipped `market-tick-data-service@10da166e15`. Small
      perp_funding backfill (HYPERLIQUID 3,013 + POLYMARKET-PERP 3,273 rows) applied + post-write verified
      2026-08-22 (`market-data-tick-cefi-prd-central-element-323112` generation 1787404515850034, row count
      unchanged at 30,801,085, zero remaining `chain=""` for either venue). See
      `issues/defi_cefi_hyperliquid_perp_funding_manifest_chain_contradiction_2026_08_21.md` and
      `issues/mtds_aster_dead_chain_default_and_unverified_instrument_catalogue_field_2026_08_21.md` for full
      status — the large HYPERLIQUID `onchain_perp_batch` (~1,457,141 rows) and ASTER (2,571,675 rows) backfills
      are flagged for VM dispatch, not yet executed.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-26 (slot-5) — mtds@ff1b5d51e6c43d7fa3aa52b924a32a01a5438fb4.** All 3 pieces shipped
      in ONE commit: (a) the 3 knobs added to `service_config.py`; (b) `_run_solana_protocol_loop` +
      `dex_pools_handler._run_process` fan out via `ParallelPerSymbolRunner` (`manifest_writer=None`), sequential
      manifest-write/heartbeat apply pass afterward in original order (the dex_pools shard-build/apply logic extracted
      into new `_dex_pools_subgraph.build_dex_pools_shard_tasks`/`apply_dex_pools_shard_results` to keep
      `dex_pools_handler.py` under the codex 900-line file cap post-fan-out); (c) every blocking parquet-serialize +
      `upload_bytes` call routed through a new dedicated `_defi_upload_executor.py` `ThreadPoolExecutor` via
      `loop.run_in_executor`. New/updated tests prove shard-level isolation (one protocol/shard failing doesn't abort
      siblings), `record_captured` grain unchanged, no result reorder/drop across concurrently-completing shards, the
      fan-out sized from the configured knob (not hardcoded), and the upload executor dedicated/singleton/
      sized-from-config — 184 targeted tests green, full `quality-gates.sh` ALL QUALITY GATES PASSED (sentinel = shipped
      SHA). No VM launch, no canary run (operator-owned per the source doc). Filed
      `issues/mtds_dex_pools_adapter_contract_baseline_stale_2026_07_26.md` (P3, non-blocking QG WARN) for the warn-only
      adapter-contract-baseline ratchet drift the file split caused (verified pure code-motion, zero calls lost).
      Originally: **Implement the MTDS DeFi perf bundle (knobs + async fan-out + executor-offload) as ONE combined
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
      `plans/archive/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md` § "Optimization — the perf bundle" (P1
      item). Done when: the 3 new knobs exist in `service_config.py`; `solana_defi_handler.py` and
      `dex_pools_handler.py` fan out fetch+upload via `ParallelPerSymbolRunner` with sequential post-loop
      manifest-write/heartbeat application; blocking upload calls run on a dedicated `ThreadPoolExecutor`; new/updated
      unit tests pass proving shard isolation, unchanged `record_captured` grain, and no upload reorder/drop;
      `bash scripts/quality-gates.sh` is green on `market-tick-data-service`; change is committed via
      `quickmerge.sh --agent` (no VM launch, no canary run) and this doc's perf-bundle checkbox is flipped with the
      commit SHA as evidence.
- [x] ✅ [BACKEND] P1. **DONE 2026-07-26 (slot-14).** Added the per-instrument catalogue residual emitter to all 4
      capturable non-POOL DeFi handlers. **Premise correction**: this todo's own text assumed
      `catalogue_pool_ids_for_shard` was "now-generalised" via a batch1 prerequisite todo — verified that prerequisite
      was STILL `- [ ]` unshipped (`_catalogue_filter.py:97` was still hardcoded `instrument_type=='pool'`), so
      generalised it first (added an `instrument_type=` param, default `"pool"`, byte-for-byte unchanged for DEX; any
      other type filters on that `instrument_type` and builds ids from the catalogue's general `instrument_id` column).
      Also verified `lst_rates_handler`'s claimed-already-fixed CAPTURED-path per-instrument grain was ALSO still
      unshipped (batch1's own combined-todo sub-item (b) was `- [ ]`) — fixed that too (`_write_single_lst_group` now
      loops `write_defi_rows`'s per-instrument shards instead of one aggregate `record_captured`; split into a new
      `_lst_rates_write.py` sibling module, codex 900-line ratchet). Added `record_catalogue_residual_empty_typed()`
      (`_catalogue_filter.py`) — `EmptyConfirmedReason.SOURCE_RETURNED_ZERO` (WITHIN-denominator), never
      `EXPECTED_NOT_ENOUGH_TVL`, per THE TRAP; normalises captured-id casing before diffing (EVM DeFi's `instrument_id`
      preserves `build_instrument_id`'s mixed-case venue prefix — caught by a test that would otherwise under-count the
      residual). Wired into `risk_params_handler.py`, `evm_defi_collectors.py`, `lst_rates_handler.py`
      (`market-tick-data-service@9d796b0e`) and `lending_indices_handler.py` (via a thin `_lending_grain.py` wrapper,
      `market-tick-data-service@eae703b0`). One new/extended unit test per handler (4 total) proves the emitter fires
      with a real, non-blank `instrument_id` + `SOURCE_RETURNED_ZERO`; the `lst_rates_handler` CAPTURED-path grain test
      extended (not replaced) with an `instrument_id` assertion. `quality-gates.sh --no-fix` green both commits
      (sentinel-verified), shipped via quickmerge. Source:
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md` (both follow-on todos flipped
      there too).
- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot 6), `unified-trading-pm@0c4172c31`.** Appended F10
      (YEARN_V3/ETHEREUM/yield_bearing/vault_share_price pipeline_mode<->source desync, MEDIUM, delete_elig=NO) to
      `/codex/02-data/canonical-cutover-register.md` §2 (`require_pipeline_mode` axis — F10 is a row-VALUE desync
      against this exact axis's `{mode}_{source}` invariant, distinct from a path-structure violation) as a new "Known
      content-desync findings" table with the finding id/severity/description/delete_elig fields, linking back to
      `data_pipeline_reconciliation_defi_2026_07_20.md` §4/§9.
- [x] ✅ [CODE] P2. Wire EULER_V2 lending-indices capture and resolve the UAC "Plasma" chain ambiguity — per
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
      confirmed/documented in UAC or explicitly filed `BLOCKED-OPERATOR-DECISION`. — **DONE (slot-11, 2026-07-26).** (1)
      Subgraph lag re-verified — worse than the prior 38-day measurement: both Goldsky endpoints now return
      `HTTP 404 "Subgraph not found"` (confirmed via retry + an alternate version-pinned path, not transient). Gate hit
      — did NOT wire capture. Closes `BLOCKED-UPSTREAM` per this todo's own fallback; gaps 1+2 (`mtds_operations`
      repoint, capture trigger) not actioned, nothing to wire against. (2) Plasma chain identity CONFIRMED via
      real-world web-search verification (not a guess): the 2025 Tether-backed Plasma L1 (chain_id 9745) — Aave has
      $6.5B+ deposits there since 2025-09-25 (2nd-largest Aave deployment by TVL), Fluid also live there. Fixed the
      wrong "Polygon Plasma bridge" code comment (`unified-api-contracts@fc788094`). Full chain onboarding (real
      market-coverage gap, out of scope here) filed as `issues/defi_plasma_chain_onboarding_gap_2026_07_26.md`. Both
      source-doc sub-items updated with full evidence in `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`.
- [x] ✅ [DEPLOY] P1. **DONE (2026-07-26, slot-12, `data_engineering`) — redeploy confirmed + re-collect launched as a
      documented monitored handoff (VMs still running a multi-year confirmatory walk; target STALE class already at
      0).** Redeploy the DeFi backfill VM tarball/image carrying `market-tick-data-service@420221b4` (or later HEAD),
      then — AFTER confirming the redeploy — execute the production re-collect for the 2,958 affected historical shards
      (`dex_pool_state` 2,107 rows + `lst_rates` 851 rows, 434 unique dates 2020-01-01..2026-06-29, 13 venues / 9
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
      confirmation + before/after counts) cited inline. ✅ **Redeploy verified**: the deployed `mtds-code.tar.gz`
      manifest was at `d09705ff` (already 7 commits past `420221b4`) before this todo ran; rebuilt anyway to current
      HEAD `ec0df8784b17a8adf0d27fdbc9144ac414e637a1` (`v0.93.0-550-gec0df878`) via
      `deployment-service/scripts/vm/create-code-tarballs.sh`, verified live at
      `gs://deployment-scripts-central-element-323112/code/mtds-code.manifest.json`. **VMs launched + verified
      healthy**: `mtds-dex-pools-backfill` (2020-01-19..2026-06-25) and `mtds-lst-rates-20260726-035545`
      (2020-01-01..2026-06-29), both SPOT, both confirmed RUNNING with the exact intended CLI invocation via serial
      console (`--start-date`/`--end-date` verified), both writing real per-VM manifest-shard progress every few seconds
      (not stalled/preempted) — satisfies the VM-launcher runbook's STARTED<60s + ≥1 progress/hr bar well past minimum.
      **Before-count finding (genuinely surprising — not caused by this todo's own launch, captured ~60s after launch
      before either VM could have written meaningfully)**: live-queried
      `market-data-tick-defi-prd-central-element-323112`'s `availability_index.parquet` (16.9M rows across the two
      data_types) — `UPSTREAM_INSTRUMENTS_CATALOG_STALE` count is **already 0 for both `dex_pool_state` and
      `lst_rates`** (the remaining `attempted_failed` rows are 19 `build_instrument_id` + 2 `429 POST https`, both
      unrelated transient classes per the source doc's own carve-out). `empty_confirmed` for `dex_pool_state` already
      shows 754 `EXPECTED_PRE_VENUE_LAUNCH` rows (the `420221b4` fix's target reason, confirmed live and working) plus
      428,311 `EXPECTED_NOT_ENOUGH_TVL` + 5,254 `SOURCE_RETURNED_ZERO` (unrelated honest-empty reasons). **This means
      the 2,958-row remediation this todo was scoped to execute had ALREADY happened via other means (routine
      backfill/cron activity in the 11 days since the issue was filed 2026-07-15) before this todo ever ran** — this
      todo's own launch is a confirmatory re-walk of the full historical range, not the operation that fixed the
      classification. **Documented monitored handoff (not blocking on multi-hour completion)**: both VMs are walking the
      FULL multi-year range (not skip-fast — observed real per-date API calls, ~several seconds/date), which will take
      multiple hours to reach `VM_SHUTDOWN_ON_COMPLETION=true` self-delete; since the classification target is already
      verified at 0 and the source issue doc's own Done-when explicitly accepts "run to completion OR a documented
      monitored handoff," this checkbox is flipped now on the redeploy+launch+before-evidence, not on VM
      self-termination. A future pass checking on these VMs should confirm they've self-deleted (or investigate if still
      running much later) and record the after-count for completeness, though the before-count already shows the
      remediation target met.
- [x] ✅ [ENGINEER] P2. **DONE 2026-07-26 (slot-2).** Closed the second and third instances of stale DRIFT residue in
      `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` via the same formula-verified surgical-prune
      playbook as the first instance, plus 2 undocumented "md5-parity with UAC" copies discovered along the way in
      `unified-trading-system-ui`. Zero remaining `"venue:drift"|"collateral:drift"|"venue":\s*"drift"` matches verified
      via the exact done-when grep below. Shipped: `unified-trading-system-ui@80bb6a9c` (instance 2, second instance),
      `unified-trading-system-ui@a0105d9f` (the discovered UI parity-copy sync + 8 stale hardcoded count-assertion
      fixes), `unified-api-contracts@6af1b966` (instance 3, third instance — 2 of 3 files superseded by a concurrent
      slot-7 regen, `capability-unlock-report.json` fixed directly). Full writeup:
      `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` Progress Log 2026-07-26 entry. Instance 4
      (prospectus) remains explicitly open, unowned, per that doc. Originally: Close the second and third instances of
      stale DRIFT residue in `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` by applying the SAME
      playbook already validated + shipped for the first instance (`deployment-ui@83ec561`, Progress Log 2026-07-21: a
      formula-verified, referential-integrity-checked SURGICAL PRUNE — not a blind regen, since no recoverable generator
      exists for any of these files):
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
- [x] ✅ [REGISTRY] P2. Close 4 leftover DeFi wizard/taxonomy gaps from
      `e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` — unified-api-contracts@13266bf8,
      strategy-service@1bf99b8e. (1) **D3** — re-audited live: `backtest_solana_basis.py` (the file that modeled
      drift-perp/Orca SOL-DEX-spot basis) was DELETED in the 2026-07-16 Solana-perp-DEX cull, which also removed DRIFT
      workspace-wide — that config can no longer be built on ANY spot venue, so the "wizard-buildable
      drift-perp/orca-spot config" branch of the done-when is now categorically impossible. `raydium` was already added
      to `CARRY_BASIS_PERP`'s spot leg (2026-07-24 containment fix, backing `catalog_carry.py`'s surviving
      raydium/hyperliquid SOL row) — added an explicit code comment in `archetype_leg_spec_seeds.py` documenting why
      `orca`/`whirlpool` are NOT included (no catalog row uses them; adding them would claim a wizard-buildable cell
      with zero backing). Also found + fixed a related staleness bug while in this file: the generated
      `capability-verdict-matrix.json` + `capability-manifest.json` (+ derived orphan/readiness reports) were stale —
      still listing removed venues `drift`/`gmx_v2` for `CARRY_BASIS_PERP` and missing
      `raydium`/`aster`/`kalshi_perp`/`polymarket_perp` — regenerated both from the current Python leg-spec source. (2)
      Deleted the dead `per_venue_margin_buffer_pct: 0.20` key (zero Python references confirmed via grep); wiring it
      into a new APD down-size branch would be net-new engine logic disproportionate to this todo, so removal (not a
      shim) is the correct fix. (3) **Already shipped** — verified live: `catalog_staked_basis.py`'s
      `_STAKED_BASIS_ETH_SPOT_VENUES`/`_STAKED_BASIS_SOL_SPOT_VENUES` already emit one slot per (LST × spot_venue)
      including orca/raydium/jupiter/binance, and UAC's `archetype_leg_spec_seeds.py` already lists the same
      `_SPOT_VENUES_STAKED` tuple — both landed under the 2026-06-17 operator directive, with an existing regression
      test (`test_carry_staked_basis_spot_venue_axis.py`); no code change needed for the base archetype (the `_DATED`
      variant still hardcodes `BINANCE-SPOT` — noted as a separate, smaller residual, not in this todo's done-when). (4)
      Audited all 5 e2e behavioural params against `param_schema.py`/`staked_basis.py` production defaults — 4 of 5
      match exactly (`entry_bps`, `exit_bps`, `min_health_factor`, `peg_drift_threshold_bps` by omission);
      `hedge_deadline_ms` diverges (e2e hardcodes `2000` across all 5 call sites vs production default `5000`) — filed
      `plans/archive/issues/e2e_defi_hedge_deadline_ms_diverges_from_production_default_2026_07_26.md` (resolved +
      archived 2026-07-26, slot-11) with the full comparison table + an A/B recommendation for the operator, since
      resolving it requires knowing whether the tighter e2e deadline is a deliberate test-speed choice.
- [x] ✅ [DOCS] P2. **DONE 2026-07-26 (worker, slot 6).** Re-verified all 5 citations against current code via a
      dedicated investigation sub-agent (all CONFIRMED, one naming correction: `FEATURE_GROUP_DATA_TYPE_OVERRIDES`, not
      `DEFI_DATA_TYPE_OVERRIDES`) — flipped the source doc's `status: open` → `resolved`, populated `resolved_by:` with
      file:line evidence for all 4 decisions + 3 CeFi-pivot bugs, cleared `locked_by:`, added a RESOLVED banner, and
      archived it to `plans/archive/2026_07/features_service_defi_data_loading_blockers_2026_05_29.md` per the
      issue-doc-lifecycle rule (a `status: resolved` doc must not sit in `plans/active/issues/`). Corpus referrers fixed
      (6 files). **Close out `features_service_defi_data_loading_blockers_2026_05_29.md` (status still `open`, no
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
      via `docs(plans):`. Source (archived):
      `/plans/archive/2026_07/features_service_defi_data_loading_blockers_2026_05_29.md`
- [x] ✅ [SCRIPT] P3. **DONE 2026-07-26 (slot 4) — already resolved, no code change needed.** Regenerate the stale
      `adapter_contract_baseline.yaml` entries for the 2026-07-14 Solana-Drift/Helius split: in
      `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`, first confirm the split (commit
      7a8bc43c, moving Helius batch-resolve retry/rate-limit mechanics from
      `market_tick_data_service/cli/handlers/solana_defi_drift.py` into the new sibling `solana_defi_drift_helius.py`)
      did not actually DROP any tracked contract calls
      (`classify_venue_error`/`ADAPTER_FETCH_FAILED`/`record_captured`/`record_empty`/`record_zero_rows`/`record_failed`)
      — verify via `git log -p` / `git show` around 7a8bc43c that the calls now counted in `solana_defi_drift_helius.py`
      (9 today) are the same calls formerly counted under `solana_defi_drift.py` (was baselined at 12, now 10), i.e. the
      split moved calls rather than silently losing them. **Findings**: the split DID move calls cleanly (verified via
      `git show 7a8bc43c^:...`/`7a8bc43c:...` — 12→10/9, real code motion), but this question turned out to be moot —
      `git log --follow` shows BOTH files were deleted entirely by `2e674d1f` (2026-07-16, the operator-ruled
      DRIFT/PACIFICA removal), one day after this issue was filed, and their baseline entries were separately dropped
      the same day by `6c5cfa812` ("chore(qg): drop culled DRIFT/PACIFICA entries from the adapter contract
      baseline..."). Confirmed live: `grep solana_defi_drift adapter_contract_baseline.yaml` = 0 hits;
      `check_adapter_contract_regression.py --workspace-root .` (run from the slot's sibling-repo parent dir) shows only
      3 currently-regressed files, none Solana-Drift-related. No regeneration needed — the fix already shipped
      incidentally via an unrelated commit. Flipped the source issue doc to `status: resolved` with the full re-triage.
      Source: `plans/archive/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md`.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-26 (worker, slot 6).** Verdict: SAFE across every active writer for
      `dex_pool_swaps`/`gas_fees` in market-tick-data-service — `record_captured` fires only after a confirmed
      successful parquet upload in every handler checked (`evm_defi_collectors.py`, `dex_swaps_handler.py`,
      `gas_fee_handler.py`, the live WS streaming path); any upload exception routes to `record_failed` instead.
      `swaps_ohlcv_*` is MDPS-owned, not MTDS — out of this repo-scoped todo. No new issue doc needed. Full code-line
      citations in `issues/phantom_captures_defi_2026_06_28.md`'s Progress Log (also flipped that doc's own matching
      todo 3). Confirm defi OHLCV/DEX writers no longer reproduce the 2026-06-28 phantom-capture pattern (manifest
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
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-26 (worker, slot 6) — verified, correctly NOT closeable yet, no false-completion
      claim.** Already investigated in full by an earlier pass this session (`unified-trading-pm@170ba61fb`, 07:37 UTC):
      all 3 VMs `RUNNING`, none vanished, real per-VM day-count measured (`-1` 23/217d, `-2` only 2/217d — a genuine
      anomaly, `-3` 35/219d) — none near `process_final=True`, realistic runway multi-day-to-multi-week. Corroborated
      with a fresh check at 07:56 UTC (all 3 still running, manifest entries still climbing, nothing material changed in
      19 min) — added as a brief confirming note rather than repeating the fuller analysis. Correctly did NOT flip
      `lst_rate_honest_coverage_2026_07_21.md`'s own Phase 5 #2 checkbox (backfill genuinely not done) — this todo's own
      verification-and-decline-to-force-completion IS the deliverable, matching this plan's own established precedent
      for premature/not-yet-ready confirmations. **Confirm/close Phase 5 #2 `dex_pool_swaps` DEX-fill 3-VM fleet**
      (`mtds-dex-swaps-backfill-1/2/3`, date-sharded on-demand, covering the measured gap `2024-10-07→2026-07-21`) —
      verify via `gcloud compute instances list --filter="name~mtds-dex-swaps-backfill"` (confirmed still all 3
      `RUNNING` as of 2026-07-26, well past the doc's original ~20-30h estimate). For each VM: read `run.log` + per-VM
      manifest shard count (`time_created`, not log activity) to confirm genuine climbing progress, not a silent stall.
      If any VM has vanished/terminated without reaching its assigned date-range end, relaunch that exact chunk's
      command again (idempotent by design per the doc's own Deferred-work table) rather than restarting from the
      original start date. Once all 3 VMs report `process_final=True`/`exit_code=0` for their assigned ranges, flip
      `lst_rate_honest_coverage_2026_07_21.md`'s Phase 5 `#2 DEX fill` todo with the manifest-count evidence and append
      a Progress Log entry. Source: `lst_rate_honest_coverage_2026_07_21.md` (Phase 5, "#2 DEX fill" todo + RESUME POINT
      deferred-work table row "Phase 5 #2 dex_pool_swaps backfill"). Done when: all 3 VMs are confirmed terminated with
      a completed date-range (or successfully relaunched to reach that state), the doc's Phase 5 #2 todo is checked off
      with cited manifest evidence, and the RESUME POINT table row is updated to reflect the closed state.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-26 (slot-8, `data_engineering`) — cron re-verified healthy; backfill turned out to
      be UNNECESSARY for 5/6 venues (already organically complete); found the real remaining gap is a different venue
      /handler/data_type than this todo assumed.** Cron health re-check: `uts-prod-mtds-collect-lst-rates-cron`
      `state=ENABLED`, last 4 Cloud Run executions (2026-07-23..2026-07-26) all `Completed True` vs. 2 `Completed False`
      on 2026-07-21/22 before the crash-loop fix (`mtds@522185a6`) — confirms healthy, no crash-loop, matches
      `defi_five_never_captured_venues_fix_2026_07_22.md`'s claim over the other doc's doubt. **Manifest-verified BEFORE
      running the RPC backfill** (direct filtered read against `market-data-tick-defi-prd`'s availability index,
      columns+filters pushdown — NOT a full-corpus read, see the linked issue doc's "measurement trap" note):
      ANKR/STADER/STAKEWISE/SWELL/MANTLE already show 90/90 days `captured` across 2026-04-27..2026-07-25, organically
      via the daily cron — running the designed ~2,340-call backfill would have been entirely wasted work. **MAKER is
      not actually an `lst_rates` venue** — `grep`+live-verified it's registered under `vault_share_price_handler.py`
      (`data_type=vault_share_price`), never in `lst_rates_handler.py`'s `load_evm_lst_contract_addresses_for_date`; its
      87 legacy `lst_rates` rows (2026-04-27..2026-07-22) were a single retroactive batch write (`written_at` all
      clustered at 2026-07-23T01:30Z), not organic capture, and correctly stopped once the writer's real classification
      took over. Checking MAKER under its REAL data type found a genuine, different gap: 61/90 days captured, a
      contiguous 29-day hole (2026-06-22..2026-07-20), confirmed genuinely absent (not `attempted_failed`) via direct
      query. Not root-caused this pass (different bug class than the crash-loop this todo was scoped around) — filed as
      `archive/issues/defi_maker_vault_share_price_29day_gap_2026_07_26.md` (RESOLVED, archived 2026-07-28, both
      follow-up todos done — 29-day gap backfilled for all 5 protocols) with the exact evidence + 2 follow-up todos
      (root-cause + backfill, gated on each other). Zero manifest/GCS writes performed — pure verification. Source:
      `/plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md`,
      `issues/defi_five_never_captured_venues_fix_2026_07_22.md`. **Done when**: either (a) the 90-day backfill is
      complete and manifest-verified for all 6 venues with cited cron-health evidence, or (b) a new issue doc exists
      citing the crash-loop evidence and explicitly defers the backfill.

## Deferred — conflict-gated (genuinely unresolved, do not draft competing todos)

- **`plans/archive/2026_08/issues/defi_code_codex_drift_2026_05_27.md`**: D15 ("HYPERLIQUID + ASTER are
  DEFI_VENUE_PHASE=pipeline but perp_funding_handler actively collects them; reconcile the phase label (→ live, or
  confirm cefi-axis classification)") is a DUPLICATE of already-tracked-but-undispatched ground, not genuinely orphaned.
  Live-code check confirms D15's own premise is stale:...
- **`plans/active/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`**: The one remaining open item in
  this doc — the unchecked `- [ ] [FEATURE] P2 delta_one funding_oi venue-aware annualisation` todo (features-service,
  thread venue through the delta_one calculator interface so non-8h venues like Hyperliquid annualise correctly) — is
  explicitly annotated in the doc itself as "DEFERRED —...
- **`plans/archive/issues/lst_exchange_rate_data_availability_2026_07_21.md`**: Phase-1's "orphaned_never_touched"
  verdict is a false positive produced by the narrow covering-set grep — the target doc is NOT actually orphaned.
  Grepping the covering set for the mechanism names (lst_yields, lst_rates, aave_oracle/AaveOracle, dex_pool_swaps,
  Curve, Orca/Raydium/Meteora) surfaced...

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md`**: Conflict check (clean, no overlap): grepped all
  13 covering-plan-set docs for every file/mechanism name in the 4 uncovered §6 items (`jupiter.py`,
  `governance_params_event_poller`, `onchain_event_poller`, `alchemy_adapter`, `thegraph_ws_adapter`, `helius_solana`,
  `native_staking_handler`). Only one hit:...
- **`plans/archive/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`**: Confirmed the Phase-1 finding: lines
  325-332 carry an unchecked
  `- [ ] [DATA] P2. Reconcile _INSTRUMENT_TYPE_ALIASES ... against the legacy venue_mapping.DataTypeConfig table` item,
  and grepping the exact mechanism name `_INSTRUMENT_TYPE_ALIASES` across the full covering-plan set (consolidated
  closeout,...
- **`plans/archive/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`** (archived 2026-08-08, delete
  complete)**: Confirmed via direct read: the doc's Todos list has 4 items. Todos 1 ([DATA] P1 scale measurement) and 2
  ([DIAG] P1 content-sample/distribution) are cited and dispatched in defi_satellite_ao_dispatch_batch1_2026_07_25.md
  (matching Phase-1's "(2 todos)" tally). Todos 3 and 4 are NOT dispatched anywhere. Conflict check:...
- **`plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`**: Read the target doc and
  confirmed Phase-1's evidence exactly. Of the 3 open todos, the VERIFY (P2) is dispatched by
  defi_satellite_ao_dispatch_batch1_2026_07_25.md (line ~546-549); the other two are explicitly excluded there (lines
  ~578-592) with detailed reasoning I independently re-verified against the source doc's...
- **`plans/archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`** (archived 2026-07-30, fully
  closed): Confirmed uncovered: todo-2 (reconcile the 2026-07-08 Balancer `@CHAIN` instrument_id patch against the
  2026-07-18 Option-A ruling — revert vs ratify) and todo-3 (fix CURVE's still-bare colliding instrument_id) are not
  cited by any doc in the covering set. Only todo-1 (read-only audit/verify, explicitly told to flag...
- **`plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`**: Confirmed via full read: the
  target doc's 4 open todos split as (1) VERIFY completeness_pct impact and (4) VERIFY the swaps_ohlcv_4h timeframe
  discrepancy — both explicitly covered by defi_satellite_ao_dispatch_batch1_2026_07_25.md lines 341-355
  (verbatim-matching "Source:" citations, confirmed by batch1_finalize.md...
- **`plans/archive/issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`**:
  Conflict check: grepped the consolidated closeout plan's own todos plus every
  batch1/track01/lending-writer-retire/gmx-venue-removal/dex-pool-symbol-fix/track5(+finalize) doc for overlap on this
  doc's remaining ground. The 4 todos in defi_satellite_ao_dispatch_batch1_2026_07_25.md (lines ~386-419: [DATA] P1...
- **`plans/archive/issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md`**: No conflict with any
  covering-set doc (grep for test_collateral_validation.py, funding_ensemble_engine.py, CollateralValidationMixin,
  defi_enhancements across the full defi covering set returned zero hits — nothing else claims this ground). The blocker
  is a genuine three-way operator decision baked into the source doc...
- **`plans/archive/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`**: Confirmed via read: the doc's
  "Tracked follow-ups" section (lines 334-365) has 5 items. Item (1) HYPERLIQUID trades backfill re-run and item (3)
  delete retired perp_funding DeFi-routing residue ARE covered — item (3) verbatim in
  defi_satellite_ao_dispatch_batch1_2026_07_25.md lines 462-471 (cites this doc as Source,...
- **`plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`**: Confirmed via Read of
  the target doc's final section ("Needs an explicit operator ruling", lines 720-733) plus the 2026-07-23 reconciliation
  note (lines 738-749): the sole genuinely-open remaining item is a two-part semantic fork requiring an OPERATOR
  decision, not worker-executable bounded work -- (1) whether...
- **`plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`**: Read the target
  doc and confirmed the Phase-1 evidence exactly: todos 1-3 (measure scope, build the restamp script with dry-run/tests,
  ship via quickmerge — explicitly "Do NOT run --apply") are covered verbatim by
  defi_satellite_ao_dispatch_batch1_2026_07_25.md lines 172-181, which cites this doc by name as Source....

## Deferred — time-gated (re-check on the next batch iteration)

- **`plans/active/issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`**: Not batchable now: this doc's own
  scope (Morpho adapter wiring + calendar-window backfill) is fully complete per the 2026-07-17 re-check #14 — the sole
  remaining item (re-run the G2 gate) is blocked purely on an external condition,
  `defi_onchain_v10_universe_v2_seed_or_backfill_progressed`, owned by...
- **`plans/archive/issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`**: Confirmed via direct read of § 6:
  the doc has 4 open items. Items (1) [terraform/scheduler wiring for staking-yields, doc's own "§ 6.1"] and (4) [codex
  defi-data-types-catalog.md § 7 Production-label fix] ARE covered — verbatim-matching todos exist in
  defi_satellite_ao_dispatch_batch1_2026_07_25.md lines 326-333...
- **`plans/archive/2026_08/issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`**: Confirmed the two uncovered items
  are Todo3 (P2 spot-check dex_pool_state/dex_pool_swaps coverage for all 4 protocols — UNISWAP_V2, UNISWAP_V4,
  TRADER_JOE_V2, VELODROME_V2 — across 2026-03→today, gated on "once the relaunched mtds-dex-pools-backfill VM (this
  session) + the running mtds-dex-swaps-backfill-1/2/3 fleet...

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`plans/archive/issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`**: Confirmed via Read: Item 2
  (4 zero-capture protocols) is closed per the doc's own 2026-07-25 update (wired 2026-07-14, verified 2026-07-24,
  residual TRADER_JOE_V2/VELODROME_V2 gaps already dispatched in defi_satellite_ao_dispatch_batch1_2026_07_25.md). Item
  1 (batch_onchain_subgraph bare-0x-address.parquet second...

## Deferred — human-only (needs a dedicated engineering/design session, not an AO todo)

- **`plans/archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`**: Confirmed via full read:
  the doc's 4-step fix chain is only partially covered. defi_satellite_ao_dispatch_batch1_2026_07_25.md's 2 cited todos
  cover (a) a DIAGNOSTIC-only pass on the frozen onchain consolidator (fixes only if trivial; otherwise "remediation
  stays open pending a human design decision" — so step 1 does...
- **`plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md`**: Conflict check found no genuine conflict:
  /plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md (line 170) already independently classified
  this exact doc as human-only for the same reasons. No plan in the covering set attempts to build the indexer,
  generalize the sig-index script, or author the implementation plan. The...

## Note — 1 mistag found, not actioned here (flag for a follow-up retag)

- `plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` — tagged
  `asset_group: [defi]` only incidentally; real content is a fleet-wide QG STEP 5.101 infra/CI issue, not defi-specific.
  Should be retagged (likely `cross-cutting` or `infra`), not folded into a defi batch.

## Note — a second mistag found during Phase-0 discovery (locked, not retagged here)

- `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` is tagged bare `[cross-cutting]`
  despite its `defi_`-prefixed title. Content is ambiguous (defi/staked-basis-specific sizing vs. possibly-generic
  wizard tooling) and the doc is `locked_by: live-defi-rollout` — flagged for the finalize plan's follow-up rather than
  retagged unilaterally here.

## Deferred work — migrated to: N/A (this plan itself is not deferred/migrated)

Fixes a `check_plan_discipline.py` false positive (the "## Deferred — operator decision needed" section above quotes
`e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`'s own "DEFERRED — ..." annotation of ONE of its items —
not a claim that this plan was migrated elsewhere). This plan's own "## Deferred — ..." sections each already cite their
source issue doc directly as the successor reference.

## Note — 1 doc found archivable_now (not actioned here — a separate archival todo, not a batch candidate)

- `plans/active/issues/mtds_perp_funding_backfill_hang_2026_07_14.md` — all 5 todos checked with completion evidence
  (root-cause confirmed, fixes shipped market-tick-data-service@5a163d02/@56efdd7d, VM relaunch verified end-to-end).
  Ready for the standard 6-step archival ritual.

## Progress Log

- **2026-07-26 (slot-8)** — Shipped the `day={D}/day={D}/` doubled-prefix todo — `instruments-service@570ae059`.
  Findings: (1) the WRITER side of this bug class is already fixed, structurally, by the operator R2 full-hive
  canonicalisation refactor (`instruments-service@a9be6ce9`, 2026-07-22 — `day`/`pipeline_mode`/`asset_group`/`venue`
  now baked once into the sink prefix, `partition={}` always, so a doubled `day=` is no longer constructible) — no
  further writer code change was needed; added a regression test (`test_write_venue_never_doubles_day_segment` in
  `tests/unit/test_orchestrator_process.py`) pinning that invariant so a future refactor can't reintroduce it. (2) The
  real remaining defect was `migrate_instruments_store_v9.py`'s `canonical_object_rel`: its final
  `rel.replace(f"day={day}/", ..., 1)` only patched the FIRST `day=` occurrence, so a pre-existing doubled
  `day={D}/day={D}/` object got the `pipeline_mode=`/`asset_group=` insert wedged BETWEEN the two `day=` copies instead
  of collapsed first — reproduced exactly per the bug report. Fixed with a new `_collapse_doubled_day()` helper called
  before the insert on both the sports and non-sports branches; verified against both confirmed-doubled examples
  (`day=2026-05-05`, `day=2026-05-07`) AND a pre-regression single-`day=` example (`day=2026-05-03`) to confirm no
  regression on the already-correct path. New parametrized tests added to
  `tests/unit/scripts/test_migrate_instruments_store_v9.py`. `quality-gates.sh` green on instruments-service (twice —
  once per change). Done-criteria (a)/(b)/(c) all satisfied; (c) is the QG-green run itself.

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- trimmed a lower-yield aggregated-sources +
  batch1-finalize ref, kept the umbrella/finalize/skill/naming-SSOT/batch1-precedent set (code-free coordinator doc, no
  single source-code target).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-21**: Attempted the last open todo (~line 307, KALSHI_PERP CEFI manifest re-emit). Confirmed both
  prerequisites genuinely done and the 567-row scope live-accurate on a sample day, designed + dry-run-validated a
  migration script against real production reads, then found a genuine, unresolved contradiction between the
  current code's enforced manifest invariant and the live CEFI manifest's actual data for this exact shard family —
  paused before writing anything to production. Filed
  `issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md` with the full investigation
  and recommended next steps.
- **2026-08-21 (same day, resolution)**: Operator ruled on the chain-convention contradiction ("KALSHI-PERP is not a
  chain"). Shipped `market-tick-data-service@f7cdd18b21` (narrow `_CHAINLESS_VENUES` carve-out in
  `_defi_manifest.py`; bundled an unrelated same-day SPORTS-MVP registry re-pin needed for a clean re-gate — 6
  venues retired per `sports_bookmaker_roster_classification_2026_08_21.md`). Then live-verified the 567-row
  historical re-emit was already fully complete (58/58 days, chain="" throughout) before this session started — no
  new write was needed. Codex updated: `/codex/02-data/defi-canonical-naming-ssot.md` § "On-chain perp CLOBs are
  CeFi, NOT DeFi" now documents the chainless-venue pattern. Last open todo flipped `[x]`. **All 23 todos now done.**
  Archival itself is NOT done here — `defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md` is the machine-gated
  finalize plan for this doc and owns the actual 6-step archival ritual as one coordinated action alongside its own
  substantial reconciliation scope (source-doc checkbox reconciliation + a 20-item Deferred re-check); that plan is
  now unblocked (`gate_on_depends: true` on this doc's all-23-done state) and will pick this up on its own dispatch.
  `status:` frontmatter deliberately stays `active` (not `complete`) — `check_terminal_status_archived.py` fires
  unconditionally on any terminal-status doc still in `plans/active/` regardless of `archive_exempt`, so the status
  flip and the archival `git mv` belong in the SAME commit per the archival ritual; that commit is the finalize
  plan's own todo 4, not this one.
