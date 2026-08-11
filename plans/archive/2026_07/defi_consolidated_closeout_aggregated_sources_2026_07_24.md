---
doc_type: plan
title: DeFi consolidated close-out — aggregated source docs (discoverability index)
summary: >-
  The "Aggregated source docs" discoverability index extracted verbatim from defi_consolidated_closeout_2026_07_18.md's
  2026-07-24 line-cap trim (2nd pass — the umbrella:true exemption was removed same-day, so the plan needed a second,
  deeper trim beyond the earlier same-day Strategy/PnL + history + Track-1 forks). Lists every other defi-relevant
  plan/issue with a repo-root-relative path and a condensed digest of its currently-open todos (bold, non-checkbox
  markers -- see task_template.md finding H -- so this stays structurally un-ingestable by AO's regen_backlog parser
  even though this doc itself is LOCAL/not dispatched). Read this alongside the parent for full context on what's open
  across the defi asset group; the parent's own native Tracks 1-8 are NOT duplicated here.
status:
  complete # (was: active) 2026-07-28 archival sweep: this doc's own single [DOC] P3 todo (verify the digest is
  # accurate) is done; verified zero open todos of its own
nature: process
asset_group: [defi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [defi, discoverability, index, aggregated-source-docs, plan-hygiene]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Plan line-cap hygiene remediation, 2nd pass, /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md -- operator
  ruling 2026-07-24 removed the umbrella:true exemption entirely (flat 1000L hard cap, no exceptions), requiring a
  second trim of defi_consolidated_closeout_2026_07_18.md beyond its earlier same-day pass.
assigned_role: data_engineering
drift_direction: none
---

## Deferred work — migrated to:

**N/A — this doc is a pure discoverability index, not a work-owning plan.** Its own single todo (verify the digest stays
accurate) is done. The real open work it catalogs lives in the ~dozens of cited sibling docs (several still carrying
real double-digit open-todo counts, e.g. `data_completion_defi_2026_07_15.md` (25 open) and
`candle_canonical_path_migration_execution_2026_07_24.md` (16 open, all P0/P1) as of 2026-07-28) — archiving this index
does not close any of that work; see the parent `/plans/active/defi_consolidated_closeout_2026_07_18.md` for the live
picture.

> **🗄️ ARCHIVED 2026-07-28 (plan-hygiene sweep)** — this doc's own scope (a verified-accurate discoverability digest) is
> complete; it does not represent the defi asset group being done. Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

# DeFi consolidated close-out — aggregated source docs (discoverability index)

> Extracted verbatim from `/plans/active/defi_consolidated_closeout_2026_07_18.md`'s 2026-07-24 line-cap trim (2nd
> pass). Nothing summarized or dropped.

## Aggregated source docs (referenced, not duplicated — every other active defi + defi-touching plan/issue)

> **Format**: each bullet is a real repo-root-relative link followed by a condensed digest of its currently-OPEN
> top-level todos (unchecked `- [ ]` only — `[x]` and `[~]` excluded). `+N more` means P2/P3 items exist beyond the ones
> listed — open the file for the rest. Digests condensed 2026-07-24 so an AO worker can triage from this doc alone.

- **Strategy/PnL/backtest axis**:
  - [`plans/active/defi_strategy_pnl_axis_index_2026_07_24.md`](/plans/active/defi_strategy_pnl_axis_index_2026_07_24.md)
    — 0 own top-level todos (active entry-point index, not closed/archived — it references other plans instead of
    carrying its own checkboxes). Most of what it points to is already indexed elsewhere in this section
    (`lst_rate_honest_coverage_2026_07_21.md`,
    `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`,
    `issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`,
    `issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`,
    `issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md`); two of its links are NOT tracked elsewhere
    here: `plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md` (`asset_group: [cross-cutting]`, 4
    open todos, out of this plan's defi-primary scope) and
    `plans/active/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md` (`asset_group: [infrastructure]`,
    explicitly "not defi-scoped itself" per its own doc).

- **Bucket / storage / migration**:
  - [`plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md`](/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md)
    - **[SCRIPT] P2.** 3 diagnostic/migration scripts (MTDS + strategy-service) still hardcode dead flat bucket-name
      templates for dex-pools/lst-rates/perp-funding — need the same
      `resolve_bucket_name(kind="tick-data", asset_group="defi")` repoint already shipped elsewhere.
    - **[CHORE] P3.** Housekeeping cluster (low-risk): delete a script past its own `Delete-when`, fix a stale
      `OPERATIONS` bucket_type dict, audit ~8 `Lifecycle: campaign` scripts with dead bucket names, fix stale comments.
  - [`plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`](/plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md)
    - **[SCRIPT] P0.** Final defi MVP verification — all 6 data_types `attempted_failed=0` AND `expected_unattempted=0`
      post-genesis; subgraph-zero-on-alive-day cells typed honest, never silent.
  - [`plans/archive/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md`](/plans/archive/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/candle_canonical_path_migration_execution_2026_07_24.md`](/plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md)
    (16 open, all P0/P1 — this is the cefi-authored candle-namespace migration epic; defi is sequenced FIRST in its
    per-AG apply order)
    - **[DATA] P0.** Rebuild code tarballs for the 4 already-shipped repos so canonical-shape changes are live on VM
      images.
    - **[DATA] P0.** VERIFY on `-test-` via `/data-pipeline-check-mdps` that the writer emits the canonical shape — GATE
      before any prod-data executor.
    - **[DATA] P0.** VERIFY readers dual-read correctly against both canonical and legacy-flat prefixes.
    - **[SCRIPT] P0.** Run the sanctioned Tier-2 spot-VM single-walk census for a precise per-AG object count before
      sizing the migration fleet.
    - **[SCRIPT] P0.** Build the migration executor — idempotent, sharded, `--apply`-gated, PROGRESS.json checkpointed.
    - **[SCRIPT] P0.** Implement the path transform (backward-add `instrument_type=`, keep SOURCE `data_type`).
    - **[SCRIPT] P0.** Implement DEDUP for the split-brain candle layout (~2x inflation on cefi/tradfi/prediction).
    - **[SCRIPT] P0.** Implement PURGE of empty-stem objects (~0.6-0.8% defect rate).
    - **[SCRIPT] P0.** Implement QUARANTINE for unresolvable legacy TradFi leaf ids — never guess.
    - **[SCRIPT] P0.** Wire manifest re-record to the SOURCE-keyed row into the executor for correct post-migration
      skip-if-fresh.
    - **[SCRIPT] P0.** Upgrade the executor's pre-delete verification from SIZE-only to crc32c checksum.
    - **[DATA] P0.** Extend `launch-canonical-migration-vm.sh` for this migration's per-AG SPOT fleet launch.
    - **[DATA] P1.** P6 drain+snapshot: coordinate with the running cefi raw_tick VMs before the candle migration
      writes.
    - **[DATA] P0.** P7 per-AG SPOT migration apply, order defi→prediction→cefi→tradfi.
    - **[DATA] P0.** P8 verify/reconcile: 4-surface reconciliation + extend the UAC canonical-path-violations oracle to
      `processed_candles/`.
    - **[DATA] P1.** Root-cause + close the candle object↔manifest disconnect so skip-if-fresh can be trusted at scale.

- **Coverage / honest-coverage / manifest**:
  - [`plans/active/data_completion_defi_2026_07_15.md`](/plans/active/data_completion_defi_2026_07_15.md) (25 open: 10
    P0, 9 P1, 6 P2 — P0/P1 listed in full, P2 capped)
    - **[DATA] P0.** B0 — RUN the existing `expected_unattempted` chain for DeFi (wire the MTDS batch orchestrator
      through IS pre-flight → `record_expected_unattempted`, run a prod batch, validate the denominator). GATED on
      C-GREEN.
    - **[DATA] P0.** C0 — path + bucket canonicalisation (the foundational migration), RUN ON A VM. C0a-C0e DONE; C0f
      (delete legacy originals) remains: 2 of 14 legacy buckets (`lending-indices`) still deferred pending a live VM
      finishing.
    - **[DATA] P0.** C11 — deeper phantom audit: are the POST-launch dex `captured` rows actually object-backed? Re-run
      the captured-vs-objects walk after C12 lands, without read-path normalisation.
    - **[DATA] P0.** D1 — features-onchain-defi is near-empty (3 rows); features-delta-one-defi +
      features-volatility-defi have no index. Run the features backfill. GATED on C-GREEN.
    - **[DATA] P0.** E1 — CeFi `derivative_ticker` funding-carrier fetch failures: ASTER partially resolved, OKX-FUTURES
      still unverified — re-check independently.
    - **[DATA] P0.** G1 — Launch the full 2024-06-01→2026-06-01 backfill VM (Drift V2 historical + Solana spot DEX
      state). Operator-launched.
    - **[DATA] P0.** G2 — Launch live-mode snapshotters via `--live --continuous` (Drift funding hourly + Solana DEX
      pool state 1-min). GATED on G1+C-GREEN.
    - **[PLAY] P0.** G3 — Run 24h paper trade via `run-paper.sh --strategy SOL_BASIS`. GATED on G2.
    - **[HUMAN] P0.** G4 — Promote to live wallet — HUMAN-ONLY hard-stop. GATED on G3.
    - **[DATA] P0.** `instruments-store-defi` reference-surface canonical-form walk — same
      v9/`asset_group=`/`pipeline_mode=`/`source` target as the MTDS C0 walk; re-run CF-1…CF-12 before any DeFi
      instruments writer relaunch.
    - **[DATA] P1.** C2 — data_type alias dedup across buckets (hyphen→underscore; pool/swap collapse to
      `dex_pool_state`/`dex_pool_swaps`). Rides the C0 walk.
    - **[DATA] P1.** C3 — VENUE-CHAIN→flat: legacy `UNISWAPV3-ETHEREUM` venue strings → flat `venue` + populated
      `chain`. Same walk.
    - **[DATA] P1.** C4 — schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same walk.
    - **[DATA] P1.** C5 — phantom-grid delete: remove the cartesian `data_type × venue` empty grid in
      `market-data-tick-defi`.
    - **[DATA] P1.** C8 — fill manifest under-enumeration: UAC declares 90 defi venue-keys but manifest enumerated only
      a fraction (lst 14/22, lending 6/21, perp 5/8). **CORRECTED 2026-07-26**: the "genuine absentees
      DRIFT-SOLANA/FRAX/MORPHO/FLUID" framing is stale — DRIFT-SOLANA's absence is correct-by-design (removed
      2026-07-16) and FRAX-ETHEREUM was never in scope (its UAC capability is `vault_share_price`, not lst/lending).
      Deeper finding: DeFi has no `expected_unattempted` seeder at all, gated on an operator/architecture decision — see
      `plans/archive/issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`.
    - **[DATA] P1.** C9 — legacy DeFi bucket object paths are pre-canonical (`category=` not `asset_group=`, no
      `pipeline_mode=`); normalise in the same single-walk as C2-C4.
    - **[DATA] P1.** D2 — MDPS swaps_ohlcv reprocess for the stale chain-column `attempted_failed` rows (28,634
      UNISWAP_V3-ETHEREUM + companion venues). GATED on C-GREEN.
    - **[CODE] P1.** G5 — Phoenix radix-slab decode (top-of-book bid+ask+size); not gated on G1-G4.
    - **[DATA] P1.** BLOCKED-CREDENTIALS — gas-fees MANTLE paid RPC (free public RPC 429-throttles `eth_feeHistory`);
      unblock = a paid MANTLE RPC key in Secret Manager.
    - +6 more (P2: C6 Pyth backfill, G6 Jupiter historical reconstruction, G7 Orca tick-array decode, G8 Raydium second
      pool, FLAG2 `_BUCKET_CATEGORY_OVERRIDES` DeFi scope, sub-bucket blank-chain phantom audit) — see file for the
      rest.
  - [`plans/active/lst_rate_honest_coverage_2026_07_21.md`](/plans/active/lst_rate_honest_coverage_2026_07_21.md) (7
    open)
    - **[MTDS] P2.** #1 CEX-spot contiguity backfill — full-history Tardis backfill over `*-SPOT` LST venues (9 real
      (venue,symbol) cells across 3 venues; BYBIT structurally absent). Blocked twice on VM OOM; filed as its own P0
      bug, not relaunching blind.
    - **[FEATURES] P2.** #4 `lst_yields` backfill — Solana-LST sub-fix (DefiLlama historical-ratio fallback) SHIPPED;
      genesis dates validated + corrected for 7 tokens (Sanctum INF was 2.3 years too late); ezETH/rsETH historical MTDS
      collector backfill still held pending real-infra caution.
    - **[MTDS] P3.** #2 DEX fill — deep-backfill `dex_pool_swaps`; endpoint + price column now live, LAUNCHED
      (operator-acked) — verify completion.
    - **[STRATEGY] P2.** A2 staking leg — wire `carry_staked_basis` STAKING_REWARD/CARRY to the `lst_yields` index
      ratio; explicit-zero the Aave-lending mismodel; ship to LDR.
    - **[STRATEGY] P3.** Recursive-staking borrow leg — wire the `aave_borrow_index` cost leg once the Aave oracle
      (collateral) lands.
    - **[MTDS] P3.** Solana `lst_rates` `pipeline_mode` mislabels which tier supplied each row (Tier-4 DefiLlama
      market-proxy rows stamped as if on-chain/subgraph) — fix `pipeline_mode_for_source` to key off the real per-row
      `method`.
    - **[MTDS] P3.** Prove force + skip per surface on `-test-` — BLOCKED-CREDENTIALS (the `-test-` bucket doesn't exist
      / SA lacks `storage.buckets.get`+`create`).
  - [`plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md`](/plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md)
    — ARCHIVED 2026-07-27, 0 open todos (all 9 mini-plans confirmed archived/complete).
  - [`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`](/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md)
    (9 open: 1 P0, 6 P1, 1 P2, 1 P3 — P0/P1 listed in full, P2/P3 capped)
    - **[OPERATOR] P0.** BLOCKED-OPERATOR-DECISION — coordinate a maintenance window with the operator for the
      prediction + tradfi consolidator crons before pausing either.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — snapshot the prediction canonical manifest index + pause its
      consolidator cron. Snapshot half DONE 2026-07-14; cron-pause half not done (no operator go-ahead).
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — apply `rebuild_prediction_manifest.py` (full date range),
      force-consolidate, re-run the fill-rate audit.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — resume the prediction consolidator cron; record before/after fill-rate
      evidence.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — snapshot the tradfi canonical manifest index + pause its consolidator
      cron. Snapshot half DONE 2026-07-14; cron-pause half not done.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — apply `rebuild_tradfi_manifest.py` (full date range),
      force-consolidate, verify fill rate + guardrail + row count.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — resume the tradfi consolidator cron; record evidence.
    - +2 more (P2 present-the-defi-audit-for-go/no-go decision, P3 stretch implement-if-GO) — see file for the rest.
  - [`plans/active/data_pipeline_check_mdps_features_2026_07_20.md`](/plans/active/data_pipeline_check_mdps_features_2026_07_20.md)
    (≈27 open: 14 P0, 8 P1, 5 P2 — P0/P1 listed in full, P2 capped)
    - **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-mdps` e2e across all AGs × venues × data_types × timeframes.
    - **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-features` e2e across all families × valid AGs.
    - **[DATA] P0.** Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + migrate existing data to zero
      orphans.
    - **[DATA] P0.** Produce a concrete ETA to backfill all remaining DeFi MVP (benchmark × remaining-shard count ×
      throughput × fleet width × $ cost).
    - **[DATA] P0.** Verify whether MDPS `max_workers` actually overlaps GCS writes — measured evidence implies SERIAL;
      up to ~8x ETA impact if fixed.
    - **[DATA] P0.** Enumerate the candle-coverage GAP per (asset_group, venue, data_type, timeframe) — drives which AGs
      to run + the ETA denominator.
    - **[DATA] P0.** Run `/data-pipeline-check-mdps` across all relevant AGs not already in candles.
    - **[DATA] P0.** Run `/data-pipeline-check-features` across all shards (8 families × valid AGs).
    - **[DATA] P0.** VERIFY the prod projection on a real prod-bucket MDPS run before sizing the win — the biggest
      unknown in the ETA.
    - **[SCRIPT] P0.** Implement F1+F2 (UTL `manifest_completeness.py`) + F3 (MDPS `_publish_emission_check`), with the
      1.4M-row perf guard.
    - **[DATA] P0.** Audit every `read_availability_index` caller on defi for a missing column/filter projection (1.58
      GB index, OOM risk).
    - **[SCRIPT] P0.** Fix the shared seed context (per-call immutable value object + collision-proof cache key) + a
      regression test — prerequisite for raising in-process concurrency.
    - **[SCRIPT] P0.** Implement R1 (concurrent date-subprocesses) — the months→weeks throughput lever, safe today.
    - **[DATA] P0.** Real-VM re-measure of end-to-end per-instrument-day rate against a PROD-sized index after the
      read-path fix lands.
    - **[DATA] P1.** Steady-state benchmark VMs (250GB disk) per representative shard-type; project full-history time +
      SPOT cost + parallelization headroom.
    - **[SCRIPT] P1.** Backfill-processing path optimized learning from cefi (within-VM multiproc, faster libs,
      fleet-wide).
    - **[DATA] P1.** Full DeFi-MVP candle backfill on real infra — GATED on
      `candle_canonical_path_migration_execution_2026_07_24.md` reaching P8.
    - **[SCRIPT] P1.** Add the all-NaN-parquet-vs-`captured` assertion to `/data-pipeline-check-mdps` (+ features twin)
      as a distinct `content_check=` verdict.
    - **[DOC] P1.** Correct `/codex/05-infrastructure/spot-vms-for-backfill.md` — preemption signal is now installed by
      `setup-data-pipeline-vm.sh` as a systemd unit, not via `launcher_common.sh`.
    - **[SCRIPT] P1.** Close residual risk 1 — make arg-required launchers relaunchable (features especially).
    - **[DATA] P1.** Blast radius: did any past prod MDPS run use `max_workers>1` over a heterogeneous list? Affected
      shards may need seed re-derivation.
    - **[SCRIPT] P1.** Implement R1 bounded-concurrent `_run_date_as_subprocess` dispatch. Gated on the seed-context
      fix.
    - +5 more (P2: ship/quickmerge housekeeping, codex promotion of the two-signal table, correct performance-targets.md
      compute-vs-IO classification, vectorize `_calculate_volume_clock_features`, write-batching for per-timeframe
      parquet writes) — see file for the rest.
  - [`plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`](/plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md)
    (14 open: 8 P1, 4 P2, 2 P3 — P1 listed in full, P2/P3 capped)
    - **[DESIGN] P1.** Fix the mockup's leaf model everywhere it still needs it — re-verify SPORTS/PREDICTION don't have
      an analogous mistake once the operator's review reaches those tabs.
    - **[DESIGN] P1.** Design the CEFI instrument-definition parquet resharding to (date, venue, instrument_type), one
      file per shard — design only, operator-gated before actual resharding.
    - **[CODE] P1.** Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM — same blank-`instrument_type` bug hits
      DRIFT/KAMINO/MARGINFI/MARINADE/ORCA/RAYDIUM/SOLEND-SOLANA + CURVE-OPTIMISM.
    - **[CODE] P1.** Pull the real per-instrument_type breakdown for DERIBIT live and confirm OPTION coverage is
      actually healthy.
    - **[CODE] P1.** Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
      entries (deployment-api + deployment-ui).
    - **[CODE] P1.** Move `market_metadata` off the MTDS `per_venue_per_data_type_daily` axis onto the
      `reference_scope`-based model.
    - **[VERIFY] P1.** Raw-parquet spot-check 5 additional CeFi venues (OKX-FUTURES, bare BYBIT, BINANCE-FUTURES,
      KRAKEN-FUTURES, BINANCE-DELIVERY) for the same multi-type blank-collapse.
    - **[CODE] P1.** Backfill historical CeFi/TradFi manifest rows with the corrected per-instrument_type split (pre-fix
      rows still blended+blank).
    - +6 more (P2: remove phantom OPTION on bare OKX, retire DERIBIT-COMBO as its own venue key, extend CLOB-on-chain
      classification to HYPERLIQUID/ASTER, audit MTDS/reference-data conflation elsewhere; P3: update a UI tooltip,
      clarify the venue-detail link naming) — see file for the rest.
  - [`plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`](/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md)
    (5 open — recounted live 2026-07-26 by `/plan-reconcile defi`, was "6 open"; the CME item below flipped `[x]`)
    - **[CODE] P1.** Add a falsifier test that fails CI when a venue/source key present in both coverage registries
      disagrees on its date — the permanent backstop against re-divergence.
    - **[DATA] P1.** Resolve the 8 confirmed multi-year/multi-month CeFi mismatches (BITFINEX, KRAKEN, COINBASE-SPOT,
      DERIBIT, OKX, BINANCE, BYBIT, HYPERLIQUID) against measured manifest reality.
    - ~~**[DATA] P2.** Resolve the CME mismatch~~ — ✅ DONE, flipped `[x]` at
      `coverage_floor_registries_no_cross_propagation_2026_07_17.md:163`.
    - **[DATA] P2.** Resolve the POLYMARKET mismatch (CLOB-launch vs first-actual-instrument, ~2.3-year gap).
    - **[DATA] P3.** Resolve the small 1-21 day DeFi protocol drifts (CURVE, UNISWAP_V2/V4, BALANCER, LIDO) + the
      AAVE_V3 chain-axis question.
    - **[DATA] P3.** Publish an explicit key-mapping table between the two registries' key schemes — prerequisite for
      the P1 falsifier todo.
  - [`plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`](/plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md)
    (3 open)
    - **[DATA] P0.** VERIFY the prod projection before sizing the win — is `_publish_emission_check` actually firing on
      prod MDPS backfills?
    - **[DATA] P0.** The 1.58 GB defi-prd index is its own P0 — audit every `read_availability_index` caller for a
      missing column/filter projection (OOM risk).
    - **[DOC] P2.** Record in codex that the per-VM manifest flush is already debounced, so the "flush is O(n²)"
      hypothesis isn't re-derived.
  - [`plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](/plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
    (2 open)
    - **[DATA] P1.** Prove the fixed writers green on one real day, then migrate the historical flat
      `instrument_availability`/`market_lifecycle`/`futures_contracts` objects up into full hive. Deferred to Round 2
      (likely VM-scale).
    - **[REVIEW] P1.** On writer ship, record the full-hive cutover date in
      `/codex/02-data/canonical-cutover-register.md` + flip the non-canonical-path-inventory row #16 to EXECUTED.
  - [`plans/active/issues/estate_orphan_assessment_2026_07_21.md`](/plans/active/issues/estate_orphan_assessment_2026_07_21.md)
    (7 open — corrected 2026-07-25 plan-reconcile, was undercounted at 4; 3 items below were missing, including the
    doc's single highest-priority defi item)
    - **[INFRA] P1.** Run the orphan sweep for defi/cefi/tradfi/prediction on a VM — cefi + prediction COMPLETE (real
      measured `E_orphan_real` counts); defi IN PROGRESS (3rd attempt, now resume-capable after 2 SPOT preemptions).
    - **[DATA] P1.** (todo 3c, previously missing from this digest) **Scope + run the defi orphan_class_E (15,865,384
      rows) backfill** — mirrors todo 3b's proven cefi/prediction pattern, but must first separate genuine production
      silent-write gaps from test-artifact contamination before `--apply`; also resolve 8 flagged `unknown_prefixes`.
    - **[CODE] P2.** Make the manifest load resumable/streamed in `migration_orphan_sweep.py` — folded into
      `migration_orphan_sweep_performance_decay_2026_07_22.md`, don't duplicate investigation here.
    - **[CODE] P3.** `GcsEventSink` never `.shutdown()`s its background `ThreadPoolExecutor` — costs ~11.5 real SPOT-VM
      minutes per batch script using this pattern.
    - **[CODE] P2.** Give `backfill_orphan_class_e.py --apply` a batched-incremental `record_cells()` call
      (cell-boundary-safe) so a SPOT preemption doesn't lose 100% of progress.
    - **[DATA] P3.** (todo 7, previously missing from this digest) **14 cefi objects mis-bucketed into the DEFI bucket,
      ESCALATED not backfilled** — found via defi's backfill dry-run 2026-07-24.
    - **[DATA] P2.** (todo 8, previously missing from this digest) **Measure prediction's `B_legacy_duplicate`
      population** — never reported anywhere in this doc's corpus; read the already-durable sweep report from todo 3's
      completed run, no re-walk needed.
  - [`plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md`](/plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/phantom_captures_defi_2026_06_28.md`](/plans/archive/issues/phantom_captures_defi_2026_06_28.md)
    (3 open)
    - **[SCRIPT] P1.** Diagnose defi phantom root cause: uniform ~25,400 counts across 7 `swaps_ohlcv_*` granularities
      suggest a single batch writer failure.
    - **[SCRIPT] P1.** Apply defi phantom reconciliation (219,529 rows → `attempted_failed`) BEFORE defi backfill G0.
    - **[SCRIPT] P2.** After reconcile + backfill: confirm defi OHLCV writers are fixed so new writes don't re-create
      the phantom pattern.

- **DeFi-specific canonicalisation residuals**:
  - [`plans/active/defi_venue_lst_rates_residual_2026_07_24.md`](/plans/active/defi_venue_lst_rates_residual_2026_07_24.md)
    (2 open — linked here 2026-07-25 ag-closeout-linkage fix, forked verbatim off the archived
    migration-verification/orphan-safety harness):
    - **[DATA] P3.** Fold the `lst-rates` corpus into the DeFi could-exist / data-status view (5 LST venues read as zero
      today despite captured rows).
    - **[DATA] P3.** Orphan/junk defi venues — `VAULT` + `SUSHISWAP` classic-vs-V3 ambiguity reconciliation in
      `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES`.
  - [`features_service_defi_data_loading_blockers_2026_05_29.md`](/plans/archive/2026_07/features_service_defi_data_loading_blockers_2026_05_29.md)
    — ✅ RESOLVED 2026-07-26 (worker, slot 6), archived: all 4 original decisions + the 3 CeFi-pivot cross-repo bugs
    (tz-aware-vs-naive datetime join, canonical_writer column-order drift, filter-pushdown memory overhead) re-verified
    live against current code, all confirmed shipped.
  - [`defi_onchain_derivable_values_and_date_drift_2026_06_20.md`](/plans/archive/2026_07/defi_onchain_derivable_values_and_date_drift_2026_06_20.md)
    — ✅ ARCHIVED 2026-07-27, all 14 todos done: Pyth Hermes/jitoSOL resolved as **clip**
    (`unified-api-contracts@4a29261e`), Latent Bug-class-3 local-fallback sweep shipped (`instruments-service@8b02b647`;
    broader sweep beyond that concrete precedent filed separately at
    `/plans/archive/issues/defi_broader_local_fallback_vs_uac_sweep_2026_07_27.md`).
  - [`plans/archive/2026_07/defi_lending_writer_retire_prerequisite_2026_07_20.md`](/plans/archive/2026_07/defi_lending_writer_retire_prerequisite_2026_07_20.md)
    (5 open — ⛔ GATES Track 1's LENDING retire)
    - **[CODE] P0.** Ship the retire atomically across UAC+MTDS+UTL in ONE wave — a partial wave IS the outage (the
      documented meta-lesson of the earlier reversal).
    - **[DATA] P0.** Runtime green proof — run it, don't read it: real one-day run for each of the 8 writers,
      manifest-verified `captured` + zero `attempted_failed`.
    - **[DATA] P0.** Three-surface agreement check on the shards from the runtime proof — GCS path · parquet column ·
      manifest row. Any disagreement is a hard fail.
    - **[DATA] P1.** Grain regression check — confirm the type change didn't disturb the per-market `record_captured`
      grain that converts `expected_unattempted`.
    - **[PM] P1.** Flip the gate + hand off — record evidence, flip the migration plan's banner from BLOCKED to CLEARED,
      notify the operator the ~16.7M-row migration may begin.
  - [`plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md`](/plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md)
    (3 open)
    - **[VERIFY] P0.** Phase-D gate — full Stage-4 historical carry tracer over 2022-01-01..today across all 7
      archetypes. REOPENED 2026-07-12 (prior ✅ covered gate LOGIC only; the 2022→today data outcome was 10/10
      SKIP_NO_DATA).
    - **[SCRIPT] P1.** Re-run `phase_d_gate.py` against real 2022→today data once the DeFi backfill reaches full
      coverage.
    - **[AGENT] P2.** `SolidlyCLForkPool` historical golden-swap validation — ≥20 Velodrome + ≥20 Aerodrome real
      on-chain fixtures within 5 bps.
  - [`plans/archive/issues/defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md`](/plans/archive/issues/defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md)
    — 0 open todos (closed/archived/record-only) — corrected 2026-07-25 (plan-reconcile): `status: resolved`, both
    bullets `[x]`.
  - [`plans/archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`](/plans/archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md)
    (4 open — recounted live 2026-07-26 by `/plan-reconcile defi`; the previous "0 open todos
    (closed/archived/record-only)" entry was wrong, this doc is `status: open` with 4 live `- [ ]` todos at
    `:82`/`:84`/`:87`/`:89`)
    - **[DATA] P1.** Verify each of the 6 known cross-chain pool-address collisions (1 CURVE + 5 BALANCER) resolves
      correctly under Option A end-to-end (catalogue → MTDS → MDPS → features → manifest/data-status).
    - **[DATA] P1.** Reconcile the 2026-07-08 Balancer `@CHAIN` `instrument_id` patch against the 2026-07-18 Option-A
      ruling — revert the patch, or explicitly ratify Balancer as an intentional carve-out and document why.
    - **[DATA] P1.** Fix CURVE's still-bare, still-colliding `instrument_id` (the only one of the 6 with zero
      mitigation).
    - **[DOC] P2.** Update `/codex/02-data/defi-canonical-naming-ssot.md` with the two-id/dual-key POOL model
      (post-phase codex audit).
  - [`plans/active/issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`](/plans/archive/issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md)
    (3 open)
    - **[BACKEND] P1.** Generalise `catalogue_pool_ids_for_shard` beyond `instrument_type=='pool'` — the prerequisite
      for any non-pool residual reconciliation.
    - **[BACKEND] P1.** Add a per-instrument residual emitter to the capturable non-POOL handlers
      (`lending_indices_handler`, `risk_params_handler`, `lst_rates_handler`, `evm_defi_collectors`).
    - **[DATA] P2.** Check whether affected (venue, chain) pairs are in UAC `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` or
      `PROTOCOL_PAUSE_WINDOWS` — superseded by the enumerator's priority ordering, may no longer be decision-relevant.
  - [`plans/archive/issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`](/plans/archive/issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`](/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md)
    (1 open — recounted live 2026-07-26 by `/plan-reconcile defi`; the previous "0 open todos" entry only accounted for
    the relabel-forward verification tracked under
    [`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)
    below, and missed this separate item at `:254`)
    - **[DATA] P2.** Item 6 — resolve item 4's "inconclusive, not a clean bill" gap for Kamino/Solend `lending_indices`;
      probe BOTH `instrument_type=solana_lending` AND `instrument_type=solana_amm_pool` path shapes before filing a
      verdict (operator ruling 2026-07-25).
  - [`plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md`](/plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md)
    (1 open)
    - **[DESIGN] P3.** Author the dedicated implementation plan when this becomes a priority — not urgent, a 2-venue gap
      on a data_type with non-zero coverage elsewhere.
  - [`plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`](/plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/lst_exchange_rate_data_availability_2026_07_21.md`](/plans/archive/issues/lst_exchange_rate_data_availability_2026_07_21.md)
    — 0 open todos (closed/archived/record-only; archived 2026-07-30).
  - [`plans/archive/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`](/plans/archive/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/mtds_lst_extended_rates_uncited_addresses_2026_07_19.md`](/plans/archive/issues/mtds_lst_extended_rates_uncited_addresses_2026_07_19.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`](/plans/active/issues/defi_morpho_lending_indices_never_wired_2026_07_12.md)
    (1 open)
    - **[SCRIPT] P2.** Re-run `mvp_backfill_defi_onchain_v10_2026_06_27.md`'s G2 gate for `lending_indices` after the
      backfill completes.
  - [`plans/active/issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`](/plans/active/issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md)
    — 0 open todos (closed/archived/record-only) — its follow-up capture work is tracked under
    [`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)
    below.
  - [`plans/active/issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`](/plans/archive/issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md)
    (4 open — recounted live 2026-07-26 by `/plan-reconcile defi`; the previous "0 open todos
    (closed/archived/record-only)" entry was wrong, this doc is `status: open` with 4 live `- [ ]` todos at
    `:144`/`:150`/`:160`/`:165`)
    - **[DATA] P1.** Run `--apply` on a VM + verify the manifest rows actually flipped — NOT YET RUN (2 VM-launch
      attempts 2026-07-24 both failed differently); blocked by the heavy-I/O hard rule.
    - **[SCRIPT] P2.** In `dex_swaps_handler.py`, detect the terminal "subgraph not found: no allocations" GraphQL
      response at FETCH time so the writer calls `record_empty(reason=EXPECTED_SUBGRAPH_DEINDEXED)`, not
      `record_failed`.
    - **[DESIGN] P3.** Evaluate wiring `curve_adapter.py`/`api.curve.fi` REST into batch `dex_pool_swaps` for
      CURVE/OPTIMISM.
    - **[SCRIPT] P3.** Repeat the live-subgraph-health spot-check for the remaining un-investigated long-tail
      `attempted_failed` buckets.
  - [`plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`](/plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md)
    (1 open)
    - **[DESIGN] P1.** GATED on parity results — decide whether to demote `perp_funding` from a captured raw type to a
      DERIVED interval view now that `derivative_ticker` is the canonical raw funding home for all perps.
  - [`plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`](/plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`](/plans/archive/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md)
    (3 open)
    - **[VERIFY] P2.** Confirm whether adding a data_type to `DATA_TYPES_BY_ASSET_GROUP["defi"]` actually changes
      `expected_unattempted`/`completeness_pct`, or is scoped independently.
    - **[CODE] P2.** Gated on the verify above — if inert, register `perp_daily_ctx` as its own canonical data_type +
      SchemaContract; backfill manifest rows for existing shards.
    - **[OPERATOR-DECISION] P3.** Whether/when to execute the perp_funding-demotion todo, and whether
      `perp_daily_ctx`/mark-price should fold into that same decision.
  - [`plans/active/issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`](/plans/active/issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md)
    (5 open)
    - **1. [DATA] P2.** Confirm the stale-row hypothesis — compare the desynced row's `attempted_at`/`available_at`
      against the handler's git-blame introduction date.
    - **2. [DATA] P2.** Measure blast radius beyond the single sampled row — scan for any row where `pipeline_mode`
      implies a different vendor than the `source` column names.
    - **3. [CODE] P2.** Fix `vault_share_price_handler.py` to pass an explicit `source=` on every
      `record_captured`/`record_failed`/`record_zero_rows` call.
    - **4. [DECISION] P2.** If todo 1 confirms stale legacy rows, rule on remediation — accepted historical artifact vs
      targeted manifest correction.
    - **5. [DATA] P3.** Append F10 to the reconciliation register per the audit's own maintenance-contract note.
  - [`plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`](/plans/archive/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md)
    (4 open)
    - **[VERIFY] P2.** Confirm the exact `completeness_pct` before/after impact of adding an exclusion guard vs adding
      the 7 keys without one — answers whether Path A is safe directly.
    - **[CODE] P2.** Gated on the verify above — execute Path A: add the defi-scoped exclusion guard + the 7
      `swaps_ohlcv_*` keys to `DATA_TYPES_BY_ASSET_GROUP['defi']`.
    - **[CODE] P3.** Alternatively execute Path B (accepted-exception stopgap) if Path A isn't prioritized soon.
    - **[VERIFY] P3.** Reconcile the `swaps_ohlcv_4h` timeframe discrepancy before either path ships.
  - [`plans/active/issues/defi_five_never_captured_venues_fix_2026_07_22.md`](/plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md`](/plans/archive/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md)
    (3 open)
    - **[SCRIPT] P0.** Both DeFi launchers MISS the SPOT preemption contract (zero
      `lc_write_preemption_signal_file`/`lc_write_launch_params` calls) — must land before any wide SPOT wave.
    - **[DATA] P0.** `available_at` clobbered by wall-clock `now()` — BIG FINDING, breaks batch==live ε=0; needs an
      operator ruling on intended semantics.
    - **[SCRIPT] P1.** Knobs + async fan-out + executor-offload, together — the 3 concurrency knobs are inert alone;
      bundle with `ParallelPerSymbolRunner` fan-out + dedicated ThreadPoolExecutor. CANARY at 2 VMs before any wide
      wave.
  - [`plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md`](/plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`](/plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md)
    (3 open)
    - **[BACKEND] P2.** `RecursiveLoopOrchestrator` exists + is substantially complete in execution-service, but
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY`/`CARRY_BASIS_PERP_INV` need NEW strategy-side decision logic (not plumbing)
      — correctly NOT AO-dispatchable, parked pending an operator design session.
    - **[BACKEND] P2.** Phase 5 — LIQUIDATION_CAPTURE: new on-chain liquidation-cascade feed + `health_factor_trigger`.
    - **[DOCS] P3.** Explicitly document
      `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`/`ARBITRAGE_MEV_JIT_LIQUIDITY`/`ARBITRAGE_MEV_BACKRUN` as OUT of the
      tick-builder-wiring scope (opportunistic/mempool-driven, no catalog-declared universe).
  - [`plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`](/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md)
    — 0 open todos (closed/archived/record-only) — its P0 finding (6 of 9 archetypes checked can't execute a real trade
    in ANY environment) blocks further orphaned-archetype work; read before touching that thread.
  - [`plans/active/issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`](/plans/active/issues/defi_upstream_instruments_catalog_stale_2026_07_15.md)
    (4 open)
    - **[DATA] P1.** Execute the re-collect commands (or launch as a monitored backfill) once scoped; verify
      before/after counts — clears the `DP_RUN_MOSTLY_EMPTY` alert.
    - **[DEPLOY] P1.** Redeploy the DeFi backfill VM tarball/image with `420221b4` so the next re-walk records honest
      `empty_confirmed` instead of recurring `attempted_failed`.
    - **[SCRIPT] P3.** Thread `mode=` into `assert_defi_catalog_fresh(...)` for the 9 handlers that still omit it —
      orthogonal to the pre-genesis classification fix.
    - **[DESIGN] P3.** IS-DeFi-catalogue-completion-signal retry-sweep — re-scoped, valid only for the genuine
      post-genesis catalogue-behind class now.
  - [`plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`](/plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md)
    (5 open)
    - **[CODE] P1.** `EULER_V2-ARBITRUM`'s `defi_venues.py` phase-dict comment is still factually wrong — correct it to
      state the real reason (adapter is Ethereum-only), not a stale no-subgraph-id claim.
    - **[CODE] P2.** Three concrete gaps to actually wire EULER_V2 capture: `mtds_operations` capability mismatch,
      capability-gate entries with zero rows ever captured, and a ~38-day-stalled upstream subgraph to re-verify before
      wiring.
    - **[VERIFY] P3.** Resolve which "Plasma" chain UAC's `FLUID-PLASMA`/`AAVE-PLASMA` placeholders refer to before
      touching those entries.
    - **[CODE] P1.** HYPERLIQUID/ASTER durable fix — declare them in UAC's own `ALL_DEFI_VENUES` +
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (a deployment-api-local stopgap already unblocks the dashboard).
    - **[OPS] P1.** Restart/fix the `uts-prod-data-status-rollup` Cloud Run Job — Cloud Scheduler has been firing into
      `UNAVAILABLE` since at least 2026-07-05.
  - [`plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`](/plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`](/plans/archive/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`](/plans/archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`](/plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`](/plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`](/plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md)
    (1 open)
    - **[DATA] P2.** `lst_yields` sparse coverage (~15 days) — file the coverage extension with features-onchain/MTDS;
      STAKING_REWARD honestly books zero (visible log) outside that window until then.
  - [`plans/archive/issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md`](/plans/archive/issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md)
    — 0 open todos (closed/archived/record-only) — operator ruling needed (rewrite vs delete vs gate-hardening) before
    this becomes a real todo.
  - [`plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`](/plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md)
    — 0 open todos (closed/archived/record-only).
  - **[`plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`](/plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md)**
    — 4 open (3 P1, 1 P2) — scale-measurement + content-sample todos gating an OPERATOR fold-vs-migrate decision on
    whether this legacy glued-venue composite population should be folded onto its correct canonical path or given some
    other disposition.
  - **[`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)**
    — 13 open (5 P0, 3 P1, 5 P2 — 11 plain-open + 2 `[~]` partial; re-verified LIVE 2026-07-25, corrects the stale "18
    open" count above); top P0s: R3-run full-corpus migration VM still applying, catalogue-venue-gap re-enum/re-rollup
    deploy-gated, ~16.7M-row LENDING→A_TOKEN/DEBT_TOKEN Wave-D migration, residual canon walk C2-C12, address/UUID
    fallback elimination in `canonical_instrument_id`.

- **Cross-AG / infra / process**:
  - [`plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md`](/plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md)
    (9 open: 3 P1, 3 P2, 3 P3 — P1 listed in full, P2/P3 capped)
    - **[DATA] P1.** Retrofit the ~48 DeFi adapters that build `instrument_key` as an ad hoc f-string to
      `build_canonical_instrument_id(...)`. Do NOT start until the TYPE-token question below is resolved.
    - **[DATA] P1.** Resolve the non-canonical TYPE-token question before retrofitting —
      `VAULT`/`SUPPLY`/`BORROW`/`LENDING_MARKET`/`GOVERNANCE_TOKEN`/`SPOT`/`PERP` aren't real `InstrumentType` enum
      values.
    - **[DATA] P1.** Fix the real "no VENUE:TYPE: wrap at all" gap in both Prediction adapters (Kalshi + Polymarket
      store the bare raw provider id).
    - +6 more (P2: VERIFY morpho.py's current code against finding 6, ship each retrofit batch via quickmerge, resolve
      the FI_-vs-FF_ Kraken-Futures collision; P3: cross-reference the TradFi combo-leg fix, refactor `ccxt_adapter.py`,
      upgrade MTDS's already-correct callers) — see file for the rest.
  - [`plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md`](/plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md)
    (2 open)
    - **[SCRIPT] P2.** DEX-pool catalog regeneration (finding 2, all 13 protocols) — code is already correct, only the
      catalog rows predate it; re-run instrument discovery and rewrite in place.
    - **[DECISION] P2.** Confirm exact target quote-currency per on-chain-perp venue (ASTER/PACIFICA/LIGHTER-ZKSYNC)
      before the illustrative targets become real implementation targets.
  - [`plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`](/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md)
    (3 open)
    - **[VERIFY] P1.** Check whether manifest regeneration is automatic or requires an explicit re-enumeration trigger
      when an IS adapter's stamped `instrument_type` changes.
    - **[VERIFY] P2.** Spot-check 2-3 more findings from the smoke-test doc across all 3 layers (DERIBIT live-vs-batch,
      HUOBI-SPOT venue-universe gap).
    - **[DECISION] P2.** Once the pilot trace (AAVE_V3) lands, decide the reconciliation cadence for the remaining 58
      findings.
  - [`plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`](/plans/archive/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md)
    (1 open — recounted live 2026-07-26 by `/plan-reconcile defi`, was "2 open"; the P1 re-fetch/backfill item flipped
    `[x]` at `:98`)
    - **[DATA] P2.** Remove/relabel the 1 defi/UNISWAP_V3-BASE row mis-filed in the sports manifest under
      `source=api_football` (date=2026-06-26), plus the second mislabeled `source=instruments_service asset_group=cefi`
      row found in the same probe — same wrong-non-blank-value bug class.
  - [`plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`](/plans/archive/2026_08/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md)
    (6 open)
    - **1. [DATA] P1.** instruments-service: canonicalise the `instrument_availability` write using the sink PREFIX
      mechanism, not the partition dict (the UTL sink sorts keys alphabetically).
    - **2. [DATA] P1.** market-tick-data-service: rule on + fix the cefi chain tail — W1 emits a bare `underlying=` path
      while W2 emits the canonical v6 tail.
    - **3. [DOCS] P2.** Correct 3 in-repo comments asserting the IS live writer emits the hive layout.
    - **4. [SCRIPT] P2.** Add a Phase-0 `-test-` assertion on the resolved WRITE bucket to
      `data-pipeline-check-mdps`/`-features`.
    - **5. [DOCS] P2.** Add an explicit "never pass `--allow-live-prod-writes`" prohibition to the MTDS check skill doc.
    - **6. [DATA] P3.** Decide whether `market_lifecycle`/`futures_contracts` are in the canonical shard grammar's
      scope.
  - [`plans/active/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`](/plans/archive/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md)
    (4 open)
    - **[SERVICE] P1.** Add a write-time canonical-path guard to the Tardis cefi lane (currently has none) — DEFAULT
      all-class `canonical_path_violations`.
    - **[SERVICE] P1.** Fix `tardis_shared.py:671` to escape `/` in the stem; migrate the 48+ KRAKEN-SPOT corrupt
      objects.
    - **[SERVICE] P1.** Turn `validate=True` on the two `tardis_cefi_shards.py` write sites and make violations FATAL,
      not advisory.
    - **[DATA] P1.** Migrate/restate the 1,697 historical non-canonical live colon_wire cefi objects as part of the
      surface-A re-run.
  - [`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
    (8 open — cefi/cross-AG-primary, defi has none of the empty-stem class)
    - **2. [DATA] P1.** Corpus-wide count of zero-length-stem candle objects; purge or repair — census done, repair
      pending P7 `--apply`.
    - **3. [DATA] P1.** Canonicalise TradFi candle leaf ids (`E1AF0_*_migrated_*` → `VENUE:TYPE:SYMBOL`) — 93% of the
      TradFi corpus is quarantined, unresolved as of P8; needs a real leaf-id resolution pass or an operator won't-fix
      ruling.
    - **7. [DATA] P0.** Root-cause the candle object↔manifest disconnect — confirmed cross-AG (defi 0 rows despite 1.1M
      live candle objects; cefi/tradfi/prediction all similarly degenerate); skip-if-fresh is moot fleet-wide until
      fixed.
    - **9. [DATA] P1.** Split-brain candle layout — quantify the corpus-wide split and fold into the A/B/C migration;
      pending P5 executor.
    - **13. [DATA] P3.** `ProvisionalTargetIndex` keys lack a bucket component — the split-brain COUNT can be inflated
      by cross-AG path coincidences.
    - **15. [DOC] P3.** Update `build_canonical_candle_path()`'s docstring example to match the 2026-07-21 correction.
    - **16. [SCRIPT] P3.** Investigate a DERIBIT trades:24h force-leg `off_template` classification mismatch —
      non-blocking.
    - **19. [SCRIPT] P2.** Fix `_copy_verify_delete()`'s retry-idempotency gap — a verification-FAILED destination is
      never re-copied on a subsequent run; source data was never at risk.
  - [`plans/archive/issues/canonical_closeout_open_questions_2026_07_18.md`](/plans/archive/issues/canonical_closeout_open_questions_2026_07_18.md)
    — 0 open todos (closed/archived/record-only).
  - [`/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`](/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md)
    (2 open)
    - **2. [DATA] P0.** Make a run whose every write failed EXIT NON-ZERO (fix the "N success / 0 failed" summary to
      count written, not processed).
    - **3. [DATA] P1.** Sweep the other candle data_types (trades, book_snapshot_5, liquidations, options_chain,
      futures_chain, the DeFi set) for the same contract-drift class before the backfill.
  - [`plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`](/plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md)
    (8 open)
    - **1. [SCRIPT] P2.** S1-a — `launch-prediction-features-vm.sh` is BROKEN; superseded by
      `launch-features-vm.sh --feature-family cross_instrument`. DELETE + repoint registry (pending operator).
    - **2. [SCRIPT] P2.** S1-b — `launch-mdps-features-live.sh` is non-runnable but still registered (5 rows) — DELETE
      or finish the dispatcher branch (pending operator).
    - **3. [SCRIPT] P1.** S1-c — `mdps-sports-<year>-<ts>` emitted but registered in NEITHER registry → invisible to the
      zombie watchdog; add it or drop sports from the sharded launcher default set.
    - **4. [SCRIPT] P3.** S2-a — trim `launch-features-backfill-vm.sh` to the redirect stub (unreachable dead body).
    - **5. [SCRIPT] P3.** S2-b — delete 8 stale `features_*_service`/`ml_*_service` SERVICE_TARBALLS keys.
    - **6. [SCRIPT] P3.** S3-a — delete MDPS one-offs past their `Delete-when` after verifying each condition.
    - **7. [SCRIPT] P3.** S3-c — repoint `smoke_matrix.py` SSOT citations to `launch-features-vm.sh` + the codex
      smoke-matrix doc.
    - **8. [SCRIPT] P3.** S3-b — sports dual entrypoint needs an operator/design adjudication; do NOT silently delete
      (breaks live sports backfills).
  - [`/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`](/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md)
    (1 open)
    - **3. [DATA] P1.** Assess blast radius on existing candle data — any past MDPS run with `max_workers>1` over a
      heterogeneous file list may carry wrong leading-bin seeds.
  - [`plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`](/plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`](/plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md)
    (4 open)
    - **[DECISION] P1.** Decide the fix mechanism for 338 empty-string-fallback call sites — bulk-annotate safe ones,
      rewrite unsafe ones fail-fast, or add a baseline-ratchet file.
    - **[SCRIPT] P1.** Once decided, execute it and get `quality-gates.sh` exiting 0 on MTDS's `live-defi-rollout` tip.
    - **[SCRIPT] P3.** Ratchet 5 baselines DOWN (`--update-baseline` per repo) — pure hygiene, unbanked headroom is how
      `agent-orchestrator` reached 26.
    - **[SCRIPT] P2.** Stamp a `commit:` anchor into the `agent-orchestrator` baseline row so an over-baseline failure
      can git-diff against a known-good point instead of a positional tail-slice guess.
  - [`plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`](/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md)
    (3 open)
    - **[VERIFY] P1.** FLUID `lending_indices` silently returns 0 rows for ~18 months (2024-06-01→2025-11-26) — the
      resolver contract wasn't deployed until 2025-11-26; needs an alternate historical read path.
    - **[VERIFY] P1.** Root-cause the 273 mistagged DERIBIT/COMBO rows — not attempted this session.
    - **[CODE] P2.** Update both drilldown mockups — not attempted this session; ~12 remaining P2/P3 items
      low-value/deferred.
  - [`plans/active/issues/mtds_perp_funding_backfill_hang_2026_07_14.md`](/plans/archive/issues/mtds_perp_funding_backfill_hang_2026_07_14.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md`](/plans/archive/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`](/plans/active/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md)
    (5 open)
    - **[INFRA] P2.** HYPERLIQUID trades backfill re-run — parser fix is code-correct but no re-run has happened since;
      ~12,179 stale rows persist. Force/overwrite, monitored (not fire-and-forget).
    - **[FIX] P3.** HYPERLIQUID k-prefix coin case-sensitivity — `kPEPE`/`kBONK`/`kSHIB` requests drop real fills due to
      a case mismatch between catalogue and fill-matching.
    - **[CODE] P3.** Delete the retired perp_funding DeFi-routing residue (stale HL/ASTER/LIGHTER entries) so a re-run
      can never re-stamp DeFi HL/ASTER perp_funding.
    - **[INFRA] P3.** **Synced 2026-07-28 (was stale here) — Auto-resolved, retagged from BLOCKED-OPERATOR-DECISION**:
      reconcile the 916 HL + 642 ASTER `defi/perp_funding` legacy rows (redundant with cefi
      `derivative_ticker.funding_rate`) by DELETE (option a — the redundant/simpler default), reversibility-cleared per
      finding T. Ready for AO dispatch, not yet executed — see the source issue doc for the full mandate (re-verify
      soft-delete retention fresh in the same run before the actual delete).
    - **[FIX] P3.** **Synced 2026-07-28 (was stale here) — RULED, retagged from BLOCKED-OPERATOR-DECISION**: RELAX RULE
      11 to cover cefi CEX venues (operator's live-probing-scope theme: broaden, don't narrow) — add cefi CEX venues to
      `_EXTRA_LIVE_PROBE_SOURCES_BY_AG`, relax/rename the RULE-11 test, re-verify the ~35 mis-flagged shards flip to
      captured. See the source issue doc for the full mandate.
  - [`plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`](/plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md)
    — 0 open todos (recounted live 2026-07-26 by `/plan-reconcile defi`, was "1 open"): the
    default-to-yesterday-date-bridge item flipped `[x] ✅ … FIXED 2026-07-16` at `:271`. Archival candidate — see this
    doc's own `## Archival + consolidation candidates` note.
  - [`plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`](/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md)
    (2 open — sports/prediction-primary, tracked here for cross-AG catalogue overlap)
    - **[OPS] P2.** Verify the next scheduled `lifecycle-catalogue-regen-sports` run promotes successfully and
      `prod/catalog.parquet` row count is `>= 27,216`.
    - **[INFRA] P3.** Grant the catalogue-regen SA `storage.objects.create` on the events-sink bucket so structured
      events stop silently 403ing.
  - [`plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md`](/plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`](/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`](/plans/archive/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md)
    (1 open — recounted live 2026-07-26 by `/plan-reconcile defi`; the previous "0 open todos
    (closed/archived/record-only)" entry was wrong, the doc's single `- [ ]` sits at `:118`)
    - **[CODE] P2.** Add a collision-resistant component (8-hex slug of `hash(venue, data_type)`) to
      `pipeline_e2e_check.py::_vm_name()`, under GCE's 63-char limit, + a regression test asserting two same-second
      same-asset_group shard launches produce distinct VM names.
  - [`plans/archive/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md`](/plans/archive/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md`](/plans/archive/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md)
    (5 open)
    - **1. [REVIEW] P1.** Confirm whether MTDS call-site updates for the UAC colon-strictness change were intended to
      land in the same wave — cross-link if already in flight.
    - **2. [DATA] P1.** Fix `canonical_write.py::write_defi_rows` (the `WETH:USDC` POOL case) — resolve the symbol
      before calling `build_instrument_id`, or route through UAC quarantine.
    - **3. [DATA] P1.** Fix `tardis_shared.py::derive_row_instrument_id`'s disabled-by-default fallback (the
      `ADAF0:USTF0` case) the same way.
    - **4. [REVIEW] P2.** Re-check `test_slash_id_never_forges_a_path_segment` — confirm whether it's the same fix as
      todo 2 or a separate defi-oracle-price naming gap.
    - **5. [REVIEW] P2.** Once 2-4 ship, re-run MTDS's full `quality-gates.sh` to confirm no other UAC-contract-change
      fallout.
  - [`plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`](/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md)
    (4 open)
    - **[CODE] P2.** `_L5_VENUES` cefi part RESOLVED-BY-DELETION; still open — audit
      `_SOURCE_COVERAGE_START`/`_PROTOCOL_TO_DATA_TYPE` (onchain) for the same read-from-UAC fix.
    - **[CODE] P2.** Add missing `book_snapshot`/`market_metadata`/`fills` declarations to
      `VENUE_DATA_TYPE_CAPABILITIES["POLYMARKET"/"KALSHI"]`; retire deployment-api's parallel registry.
    - **[SCRIPT] P3.** Delete confirmed-dead code (`MVP_VENUE_DATA_TYPES`, DeFi's emptied `DEFI_VENUE_AXIS_OVERRIDES`,
      Prediction's inert matrix row) — not touched this pass, `defi_venues.py` was live-being-edited concurrently.
    - **[DESIGN] P2.** 31 DeFi (venue, data_type) pairs declare a genesis start-date with zero real captured rows (100%
      `empty_confirmed`) — needs an operator/data-owner decision per (protocol, data_type).
  - [`plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`](/plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md`](/plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md)
    — 0 open todos (closed/archived/record-only).
  - [`/plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md`](/plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md)
    (3 open)
    - **6. [DATA] P1.** PROVE the fixed delta_one + volatility writers green on one real day, then migrate historical
      objects up into the `by_date/day=` tree.
    - **7. [DATA] P1.** Re-sync the availability manifest + data-status render for the migrated features cells so all
      four canonical surfaces agree.
    - **8. [REVIEW] P1.** On writer ship, record the cutover date in the canonical-cutover-register + flip the
      non-canonical-path-inventory row #17 to EXECUTED.
  - [`plans/archive/issues/migration_orphan_sweep_performance_decay_2026_07_22.md`](/plans/archive/issues/migration_orphan_sweep_performance_decay_2026_07_22.md)
    (1 open)
    - **7. [CODE] P3.** Genuinely stream `_load_manifested_cells()`'s parquet read instead of relying on a bigger
      machine type — today's fix works but doesn't scale as cefi's index keeps growing.

- **Cross-AG-touching cefi plans referenced here for their defi overlap** (primary tracking:
  [`plans/active/cefi_consolidated_closeout_2026_07_18.md`](/plans/active/cefi_consolidated_closeout_2026_07_18.md)):
  - [`plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md`](/plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md)
    (2 open) — [ ] [SCRIPT] P2. Spot-check 3 random days of DERIBIT options greeks/IVs. [ ] [SCRIPT] P2. Spot-check 1
    day of BINANCE-FUTURES funding + open_interest.
  - [`plans/active/cefi_ml_directional_continuous_live_2026_06_20.md`](/plans/active/cefi_ml_directional_continuous_live_2026_06_20.md)
    (3 open) — [ ] [AGENT] P0. Continuous ML signal live ≥7 days across OKX+Binance+Bybit — GATED on
    wallet-key/kill-switch operator hard-stops. [ ] [VERIFY] P0. 2-year config-grid backtest fidelity run — architecture
    verified, grid run pending operator VM scheduling. [ ] [RESEARCH] P2. Not currently scheduled (2026-07-24: reworded
    off the bare DEFERRED-then-dash marker, which is reserved for whole-plan migrations per the plan-discipline gate —
    this is a single low-priority research idea, not a plan-level deferral, and has no successor plan to banner): volume
    as a first-class feature for the cs/ext ML models.
  - [`plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`](/plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md)
    (22 open — a genuinely large tradfi/cefi crypto-venue-equity-perp build; top items only) — [ ] [SCRIPT] P0.
    Propagation ops (B1/B3/B4) — run the IS→catalogue→enumerator→MTDS chain on real infra to completion; IN PROGRESS. [
    ] [UAC] P0. Map index perps (SPXUSDT/NAS100/SPYUSDT/XAUUSDT) to their CME/Databento canonical + contract multiplier.
    [ ] [DESIGN] P0. execution-service — IBKR equities execution adapter is the gating unlock for the winning
    single-stock basis archetype. [ ] [DESIGN] P0. strategy-service+UAC — replace the fixed net-profitable-12 with a
    broad dynamic live-net-carry universe. — see file for the remaining 18 (mostly P1/P2 strategy-design + data-sourcing
    items).

- **Newly discovered (completeness-check addition, 2026-07-24)**:
  - [`plans/active/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`](/plans/active/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md)
    (`asset_group: [defi, cefi]`, `status: open` — the DRIFT + all-other-Solana-perp-DEX kill ruling's DATA/STATE half;
    not previously named in this section) (1 open)
    - **[DATA] P2.** Once the sibling's UAC venue removal + IS adapter removal are fully on `origin`, re-run
      `build_instrument_catalogue.py --asset-group defi` (and `cefi`) as a confirmation pass — pre-conditions now
      satisfied, `instruments-service@ee19f6f3` already hardens the catalogue script to structurally exclude the killed
      venues.

- **Retagged into defi scope 2026-07-25** (both were orthogonality mistags found scoping the new cross-cutting AG layer
  — see `cursor-configs/skills/ag-closeout-audit/SKILL.md`'s Orthogonality HARD CHECK):
  - [`defi_venue_lst_rates_residual_2026_07_24.md`](/plans/active/defi_venue_lst_rates_residual_2026_07_24.md) —
    lst-rates aggregation + venue-spelling residual, forked from `migration_verification_orphan_safety_2026_06_10`.
  - [`features_service_defi_data_loading_blockers_2026_05_29.md`](/plans/archive/2026_07/features_service_defi_data_loading_blockers_2026_05_29.md)
    — ✅ RESOLVED + archived 2026-07-26; `master:` field named `defi_manifest_canonicalisation_2026_06_01.md` as owner.
  - [`e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`](/plans/archive/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md)
    — ✅ ARCHIVED 2026-07-27, all 6 BUGs fixed + shipped (UTL@b587b91b/ed622af8, UAC@fd5bcfa/7fade10,
    execution-service@38c7e06f, strategy-service@b91d3e1f, features-service@16be6c0f).
  - [`e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`](/plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md)
    — e2e DeFi strategy configs taxonomy/wizard round-trip fidelity gaps; repos/paths all `e2e-testing/scripts/defi/*`.

- **Newly discovered (ag_closeout_auditor sweep, 2026-07-27)**:
  - [`issues/read_availability_index_bare_defi_callers_2026_07_27.md`](/plans/archive/issues/read_availability_index_bare_defi_callers_2026_07_27.md)
    (`asset_group: [defi]`, `status: open`, `assigned_vm: planning` — already checkbox-formatted, 17 real todos, not
    previously named in this section) — full-corpus audit of ~35-40 bare `read_availability_index()` call sites across 8
    repos reachable on the 1.58 GB defi availability index with no `columns=`/`filters=` projection (OOM risk, matching
    the `mtds_backfill_vm_startup_oom_rc137_2026_07_14` incident class). **[SCRIPT] P0.** deployment-api
    `services/manifest_source.py:164` fallback — single highest-blast-radius fix (feeds ~10 dashboard endpoints).
    **[SCRIPT] P0.** market-tick-data-service `reader.py:839` + `engine/orchestrator/__init__.py:509`. **[SCRIPT] P0.**
    ml-service live-inference `manifest_inference_guard.py:46`. — see file for the remaining 13 P1-P3 items across
    unified-trading-library/features-service/instruments-service/strategy-service/deployment-service/e2e-testing, plus a
    proposed new QG gate to prevent regressions.

## Todos

- [x] ✅ [DOC] P3. **This index is not "0 open work" — it aggregates dozens of sibling docs carrying real open todos**
      (by design, non-checkbox digest bullets — e.g. 25 open in `data_completion_defi_2026_07_15.md`, 16 open P0/P1 in
      `candle_canonical_path_migration_execution_2026_07_24.md`); do not treat this doc's own checkbox-free format as
      evidence the defi asset group is done. **Verified accurate 2026-07-28** — re-read the doc in full: the caveat is
      present and correctly describes the doc's own content (dozens of `- **[TAG] Pn.**` non-checkbox digest bullets
      across the "Aggregated source docs" section, several still carrying real double-digit open-todo counts, e.g. the
      cited `data_completion_defi_2026_07_15.md` (25 open) and `candle_canonical_path_migration_execution_2026_07_24.md`
      (16 open, all P0/P1)). No correction needed; checkbox flipped to record the verification.
