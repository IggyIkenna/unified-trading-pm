---
title: Mock-data pipeline benchmarking — synthetic-data harness for per-stage bottleneck profile
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (Group F item 18 2-yr batch backtest sized for cutover archetypes)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/mock_data_pipeline_benchmarking_2026_05_08.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  - plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md
  - plans/active/features_repo_consolidation_2026_05_08.md
related_codex:
  - codex/02-data/contracts-scope-and-layout.md
  - codex/05-infrastructure/runtime-tiers-and-deployment.md
  - codex/05-infrastructure/vm-tarball-deployment.md
  - codex/06-coding-standards/performance-targets.md
estimate_class: design
estimate_baseline_ai_days: 11.8
estimate_calibrated_ai_days: 7.0
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~0.5, ~1.5, ~2, ~2, + 5 more). Class inferred from filename (design, multiplier 0.6×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
---

# Mock-data pipeline benchmarking

## Why this plan exists

May-23 cutover gates on Group F item 18 ("2-yr batch backtest run completes inside an operationally-acceptable window")

- item 17 paper-trade smoke. Today nobody has measured per-stage CPU / memory / IO / wall-clock for the
  cutover-archetype pipeline (MTDS read → MDPS compute → features → ML inference → strategy → matching engine).
  Real-data benchmarks are gated on full backfill completion which is mid-flight. Synthetic-data benchmarks let us
  pre-empt VM-shape sizing surprises 2 weeks early. This plan ships per-asset_group synthetic generators for cutover
  archetypes only, a benchmark harness that drives the full pipeline on a VM, and per-stage profile reports + VM-shape
  recommendations. Full breadth across non-cutover archetypes / asset_groups deferred post-cutover.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. UAC synthetic-data generator contracts: `SyntheticGeneratorId`, `SyntheticParams`, per-asset_group generator factory.
2. Per-cutover-archetype generators: CeFi tick + funding + OI + liquidation; DeFi gas + LST + lending + DEX + oracle.
   Realism axis 1-3 (cardinality / parquet size / shard count) sufficient for bottleneck measurement.
3. Benchmark harness: drives full pipeline (MTDS → MDPS → features → ML → strategy → matching engine) on a VM with
   synthetic input.
4. Per-stage profile: wall-clock, CPU%, RSS, IO read/write bytes, GCS / S3 listing depth.
5. VM-shape recommendation matrix: per-stage `(min_cpu, min_ram, min_disk, min_iops)` justified by profile data.
6. Codex SSOTs: 1 NEW + 2 UPDATE.
7. Real-VM benchmark runs for both cutover archetypes; full per-stage profile report.

### Non-goals (post-cutover)

- Full per-asset_group generator coverage beyond cutover archetypes — post-cutover sub-plan.
- Realism axis 4 (calibrated GBM / SDEs) for correctness benchmarking — post-cutover; current cutover pipelines are
  data-shape-driven, not value-driven.
- Sports / prediction generators — post-cutover; cutover archetypes don't consume those.
- Continuous benchmark cron (nightly perf trend) — post-cutover; one cycle of benchmarks is the cutover MVP.

## Pre-audit / blast radius

| Repo                       | Surface                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------ |
| `unified-api-contracts`    | NEW: `canonical/crosscutting/synthetic_generator.py`; `registry/generators/{cefi,defi}.py`             |
| `unified-trading-library`  | NEW: `synthetic/generator.py`, `synthetic/harness.py`, `synthetic/profile.py`                          |
| `market-tick-data-service` | UPDATE: synthetic-data pipeline-mode hook (writes generator output to GCS/S3 with proper shard layout) |
| `mdps` + `features-*`      | UPDATE: read synthetic input via existing reader paths (no code change if shard layout matches)        |
| `unified-trading-pm`       | NEW + UPDATE codex docs                                                                                |

## Phased execution DAG

```text
0 (pre-audit) → 1 (UAC contracts) → 2 (UTL primitives) → 3 (per-archetype generators, parallel) → 4 (benchmark harness)
→ 5 (real-VM benchmark runs) → 6 (per-stage profile + VM-shape matrix) → 7 (codex SSOTs) → 8 (cutover gate)
```

## Phase 0 — Pre-audit (Day 1, ~0.5 AI-day, 2 parallel sub-agents)

- [x] [AGENT] P0. **0.A Existing generator inventory.** Walk MTDS / mdps / features-\* test fixtures + scripts/ for any
      synthetic generators. Output: per-data_type coverage matrix. (slot 7 2026-05-12 — § Audit findings 0.A; no
      reusable cross-pipeline generator exists, only per-service test mock providers.)
- [x] [AGENT] P0. **0.B Per-cutover-archetype data shape requirements.** Enumerate every (asset_group, data_type) the 2
      cutover archetypes consume + per-day expected row counts + per-shard parquet sizes (from real backfill samples
      where available, or estimated otherwise). (slot 7 2026-05-12 — § Audit findings 0.B data-shape table; row counts
      are realism-axis-1 estimates pending real-backfill calibration before Phase 5.)

**Full-execution criterion**: § Audit findings populated; per-archetype data-shape table. ✅

## Phase 1 — UAC synthetic-data contracts (Days 2-3, ~1.5 AI-days)

- [x] [AGENT] P0. **1.A `SyntheticGeneratorId` + `SyntheticParams` Pydantic.** Closed-enum generator IDs; params include
      row_count_per_day, schema_version, realism_axis, shard_layout, output_uri. (uac@`d47b232` —
      `canonical/crosscutting/synthetic_generator.py`: `SyntheticGeneratorId` (13) + `SyntheticDataDomain` (8) +
      `SyntheticRealismAxis` (4) + `SyntheticShardLayout` (closed shard-atom set validator) + `SyntheticParams`
      (date-range + fanout-matches-layout validators + `params_hash()`); surfaced on top-level UAC facade.)
- [x] [AGENT] P0. **1.B Per-asset_group registry seed.** `registry/generators/{cefi,defi}.py` per data_type generators
      for cutover archetypes only. (uac@`d47b232` — `registry/generators/{cefi,defi,tradfi}.py` (added tradfi for the
      cross-asset hedge overlay per work-split scope "DeFi + CeFi + TradFi"); `SyntheticGeneratorSpec` self-registers
      in `SYNTHETIC_GENERATOR_REGISTRY`; `generators_for_archetype()` helper.)
- [x] [AGENT] P0. **1.C `SyntheticOutputManifest` Pydantic.** Tracks generator_id × output_uri × row_count for the
      harness to verify before pipeline run. (uac@`d47b232` — `SyntheticShardManifest` + `SyntheticOutputManifest`
      (per-generator) + `SyntheticRunManifest` (aggregates a whole run's generator manifests) with `total_rows` /
      `total_bytes` aggregate properties.)
- [x] [AGENT] P0. **1.D Tests.** ≥15 unit tests; registry completeness; per-archetype coverage. (uac@`d47b232` —
      `tests/internal/unit/test_synthetic_generator.py`: 70 tests pass; covers enum counts, shard-axis validator,
      params validators + hash determinism, spec cardinality, manifest round-trips, registry completeness (13 = 6+5+2),
      per-archetype coverage, `register_generator` idempotency + conflict-detection.)

**Full-execution criterion**: UAC PR pushed (uac@`d47b232`); QG green — basedpyright/ruff to be confirmed by CI (slot
worktree has no per-repo `.venv`; 70 unit tests verified green via `.venv-workspace`).

## Phase 2 — UTL synthetic primitives (Days 3-5, ~2 AI-days)

- [ ] [AGENT] P0. **2.A `synthetic/generator.py`.** Per-data_type generator class; produces parquets with correct
      schema + cardinality + `available_at` discipline (per CLAUDE.md "available_at is write-time"). Realism axis 1-3.
- [ ] [AGENT] P0. **2.B `synthetic/harness.py`.** Drives full pipeline end-to-end: generator → MTDS write → MDPS compute
      → features → ML → strategy → matching engine. Reuses prod entry points; no parallel pipeline.
- [ ] [AGENT] P0. **2.C `synthetic/profile.py`.** Wraps each pipeline stage with per-stage profiler (psutil + GCS / S3
      listing instrumentation). Output: `StageProfile` parquet (stage_name, wall_clock, cpu_max, rss_max, io_read_bytes,
      io_write_bytes).
- [ ] [AGENT] P0. **2.D Tests.** ≥30 unit tests.

**Full-execution criterion**: UTL PR pushed; QG green; harness end-to-end on stub data emits non-empty
`StageProfile.parquet`.

## Phase 3 — Per-archetype generators (Days 5-7, ~2 AI-days, 2 parallel sub-agents)

- [ ] [AGENT] P0. **3.A `carry_staked_basis` generators.** DeFi gas, LST rates (jitoSOL/mSOL/bSOL Solana +
      wstETH/rETH/cbETH EVM), Aave + Morpho lending indices, Uniswap + Curve pool states, Pyth + Chainlink oracle feeds.
      Per-day row counts calibrated to real-backfill samples.
- [ ] [AGENT] P0. **3.B `ARBITRAGE_PRICE_DISPERSION` generators.** CeFi tick + ohlcv_1m + ohlcv_15m + funding_rate +
      OI + liquidations across cutover venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster) for the relevant
      instrument set.
- [ ] [AGENT] P1. **3.C Real-backfill calibration.** **DEFERRED-from-Phase-0.B** (slot 7 2026-05-12). For each of the
      13 specs in `registry/generators/{cefi,defi,tradfi}.py`: where the real backfill has reached the cutover universe,
      populate `real_backfill_sample_uri` + tune `default_row_count_per_day` + the axis-2 byte-size model from
      `gs://central-element-323112-*-{raw,processed}/...` samples; where it hasn't, keep the estimate + a `# ESTIMATE`
      marker. The `defi_gas` non-uniform per-chain block-rate distribution (ETH 7.2k / ARB 350k / OP+BASE 43.2k / SOL
      216k blocks per day) is the trickiest — the UTL generator (Phase 2.A) carries the per-chain weighting table; do
      NOT distribute `row_count_per_day` uniformly across the 5 chain shards. Provenance: § Audit findings 0.B.

**Full-execution criterion**: harness reads synthetic data through prod readers without schema-drift errors; row counts
match per-archetype data-shape table.

## Phase 4 — Benchmark harness wire-in (Days 7-9, ~2 AI-days)

- [ ] [AGENT] P0. **4.A CLI flags.** Backtest CLI gains `--synthetic-generator <id>` + `--synthetic-params <yaml>`.
      Mutually exclusive with real-data flags.
- [ ] [AGENT] P0. **4.B Per-stage profiler integration.** Pipeline orchestrator wraps each named stage with
      `synthetic.profile.profile_stage(name)`.
- [ ] [AGENT] P0. **4.C Profile parquet emit.** Per-run
      `gs://{pid}-benchmark-reports/{archetype}/{run_id}/stage_profile.parquet`.

**Full-execution criterion**: single archetype × single VM run emits non-empty profile.

## Phase 5 — Real-VM benchmark runs (Days 9-11, ~2 AI-days)

- [ ] [SCRIPT] P0. **5.A Per-archetype × per-VM-shape matrix.** Launch VMs across `c2-standard-{4,8,16,32}` +
      `c3-highcpu-44`; run cutover-archetype synthetic harness; emit profile parquet per (archetype, vm_shape).
- [ ] [SCRIPT] P0. **5.B No fire-and-forget.** Per "No fire-and-forget VM launches" HARD RULE — STARTED + per-stage
      progress + STOPPED events per VM.
- [ ] [AGENT] P0. **5.C Evidence capture.**

**Full-execution criterion**: ≥10 (archetype × shape) profile parquets in GCS; per-stage wall-clock + CPU max captured.

## Phase 6 — Per-stage profile + VM-shape matrix (Days 11-12, ~1 AI-day)

- [ ] [AGENT] P0. **6.A Aggregate report.** Per-stage P50/P95/P99 wall-clock + CPU + RSS + IO. Output:
      `benchmark_report.parquet` + markdown summary in plan body.
- [ ] [AGENT] P0. **6.B VM-shape recommendation matrix.** Per-archetype × per-stage recommended
      `(min_cpu, min_ram, min_disk, min_iops)`. Justified per profile.
- [ ] [AGENT] P0. **6.C Bottleneck callouts.** Stages where wall-clock × scale-factor exceeds Group F item 18 budget
      ("operationally-acceptable window") flagged as P0 follow-ups for `live_pipeline_mtds_mdps_features_2026_05_08`
      consumers.

**Full-execution criterion**: report committed to plan body; ≥1 recommendation per stage; bottleneck callouts filed if
any.

## Phase 7 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [ ] [AGENT] P0. **7.A NEW `codex/05-infrastructure/synthetic-data-benchmarking.md`.** Generator contract, harness
      shape, per-stage profile, VM-shape matrix.
- [ ] [AGENT] P0. **7.B UPDATE `runtime-tiers-and-deployment.md`** — VM-shape recommendations cross-link.
- [ ] [AGENT] P0. **7.C UPDATE `performance-targets.md`** — per-stage targets backed by profile data.

**Full-execution criterion**: 1 NEW + 2 UPDATE; cross-references resolve.

## Phase 8 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **8.A Master plan extension.** Group F item 18 row gains "VM-shape sized per benchmark report;
      cutover-archetype profile green within Group F operationally-acceptable budget."
- [ ] [AGENT] P0. **8.B Banners removed.**

**Full-execution criterion**: master plan row green; banners gone.

## Cross-plan coordination

- `live_pipeline_mtds_mdps_features_2026_05_08` — bottleneck callouts in Phase 6.C feed back as P0 todos there.
- `simulation_scenarios_topology_price_shocks_2026_05_09` — synthetic-scenario harness shares the generator primitives;
  scenarios extend generators with mutation overlays.
- `features_repo_consolidation_2026_05_08` — features-repo consolidation lands first; benchmark runs against the
  consolidated repo.

## Deferred work after 2026-05-10 plan-creation session

| Item                                                   | Status            | Successor / blocker                        |
| ------------------------------------------------------ | ----------------- | ------------------------------------------ |
| Full per-asset_group generator coverage beyond cutover | DEFERRED-PER-USER | Post-cutover sub-plan                      |
| Realism axis 4 (calibrated GBM / SDEs)                 | DEFERRED-PER-USER | Post-cutover; cutover is data-shape-driven |
| Sports / prediction generators                         | DEFERRED-PER-USER | Post-cutover                               |
| Continuous benchmark cron (perf trend)                 | DEFERRED-PER-USER | Post-cutover; one-cycle MVP                |

## Done definition

1. ✅ Phases 0-8 every checkbox flipped with evidence.
2. ✅ UAC + UTL + MTDS + PM green.
3. ✅ Per-archetype × per-VM-shape profile matrix; recommendations justified.
4. ✅ Bottleneck callouts (if any) filed in `live_pipeline_mtds_mdps_features_2026_05_08`.
5. ✅ Master plan Group F item 18 row gains the budget assertion.

## Audit findings

### 0.A — Existing generator inventory (slot 7, 2026-05-12)

**Verdict: no reusable cross-pipeline synthetic generator exists.** Workspace grep
(`SyntheticGenerator|synthetic_generator|SyntheticParams|synthetic/` + `find -type d -name synthetic`) returns nothing
under any service or library. What DOES exist is a scatter of per-service unit-test mock providers, none of which
produce on-disk parquet through prod readers — they hand in-memory dataframes/objects directly to engine code:

| Where | What it does | Reusable for the harness? |
|---|---|---|
| `market-tick-data-service/tests/market_interface/fixtures/mock_ws_server.py` (`MockWebSocketFeed`) | WS feed mock for live-mode tests | No — WS only, no batch parquet path |
| `ml-training-service/ml_training_service/engine/mock_data_provider.py` + `app/core/mock_feature_generator.py` | feature dataframes for ML-training unit tests | No — in-memory dataframes, ML-stage only |
| `ml-inference-service/scripts/seed_mock_data.py` + `ml-training-service/scripts/seed_mock_data.py` | seed firestore/GCS for local-dev demo | Partial — seeding pattern only; not pipeline-shaped |
| `features-service/tests/{volatility,multi_timeframe,sports}/unit/test_mock_data_provider.py`, `position-balance-monitor-service`, `pnl-attribution-service`, `risk-and-exposure-service` `tests/unit/test_mock_data_provider.py` | per-feature-family in-memory provider for unit tests | No — unit-test scoped, in-memory |
| `unified-trading-api/unified_trading_api/mock_data/seed_{strategies,timeseries}.py` | UI demo seed | No — UI-layer fixtures |

⇒ The benchmark harness has to ship its own generator primitive (Phase 2 UTL `synthetic/generator.py`) that writes
real parquet with the prod schema + shard layout under a GCS/S3 prefix. No prior art to extend; this is `brand-new`.
**(Note: the plan frontmatter says `estimate_class: design` — the UAC contract layer (Phase 1) and codex (Phase 7)
are design, but the UTL generator + harness + per-archetype writers (Phases 2-4) are closer to `brand-new`. Net
effect is roughly a wash with the design multiplier; leaving frontmatter as-is per "do NOT mass-sweep" rule, flagging
here.)**

### 0.B — Per-cutover-archetype data-shape table (slot 7, 2026-05-12)

The two cutover archetypes (`carry_staked_basis` DeFi lead + `leveraged_funding_arb` / `ARBITRAGE_PRICE_DISPERSION`
CeFi hedge+arb) consume the following `(asset_group, data_type)` set. Row counts below are **realism-axis-1 estimates**
keyed to a representative cutover universe — they MUST be calibrated against real backfill samples before the Phase 5
VM runs (the registry `SyntheticGeneratorSpec.real_backfill_sample_uri` field is the carrier; currently empty for all
13 specs). Per-shard parquet byte-size (axis-2) targets are TBD pending the same samples.

Representative cutover universe (encoded in `registry/generators/{cefi,defi,tradfi}.py`):
- CeFi venues: `bybit`, `deribit`, `binance`, `okx`, `hyperliquid`, `aster` (6) × instruments `BTCUSDT`/`ETHUSDT`/`SOLUSDT` (3) → 18 cells.
- DeFi chains: `ethereum`, `arbitrum`, `optimism`, `base`, `solana` (5). LST protocols: marinade/jito/blazestake/lido/rocket_pool/coinbase_cbeth (6). Lending: aave_v3/morpho. DEX pools: 4. Oracle feeds: 5.
- TradFi: 5 instruments (ES/NQ/ZN/GC/DXY) × `databento` source.

| Generator id | asset_group / data_type | Shard atom | Cells | ≈ rows/day (sum) | Pipeline stages touched | Archetype(s) |
|---|---|---|---|---|---|---|
| `cefi_trades` | cefi / trades | (venue, instrument) | 18 | 1.8M | mtds_read→mdps_compute→features→strategy→matching_engine | ARB / leveraged_funding_arb |
| `cefi_ohlcv_1m` | cefi / ohlcv_1m | (venue, instrument) | 18 | 25.9k (1440/cell) | mtds_read→mdps_compute→features→ml_inference→strategy | ARB / leveraged_funding_arb |
| `cefi_ohlcv_15m` | cefi / ohlcv_15m | (venue, instrument) | 18 | 1.7k (96/cell) | mtds_read→mdps_compute→features→ml_inference→strategy | ARB / leveraged_funding_arb |
| `cefi_funding_rate` | cefi / funding_rate | (venue, instrument) | 18 | 432 (≤24/cell) | mtds_read→features→strategy | ARB / leveraged_funding_arb (THE carry signal) |
| `cefi_open_interest` | cefi / open_interest | (venue, instrument) | 18 | 25.9k (1440/cell) | mtds_read→features→strategy | ARB / leveraged_funding_arb |
| `cefi_liquidations` | cefi / liquidations | (venue, instrument) | 18 | 90k (bursty, ~5k/cell) | mtds_read→features→strategy | ARB / leveraged_funding_arb |
| `defi_gas` | defi / gas | (chain,) | 5 | ~660k (non-uniform: ETH 7.2k, ARB 350k, OP/BASE 43.2k, SOL 216k) | mtds_read→features→strategy→matching_engine | carry_staked_basis / leveraged_funding_arb |
| `defi_lst_rates` | defi / lst_rates | (chain, protocol) | 6 | 576 (96/cell) | mtds_read→features→strategy | carry_staked_basis (THE staking signal) |
| `defi_lending_indices` | defi / lending_indices | (chain, protocol) | ~50 | 1.2k | mtds_read→features→strategy | carry_staked_basis |
| `defi_dex_pool_state` | defi / dex_pool_state | (chain, pool) | 4 | 5.76k (1440/cell) | mtds_read→features→strategy→matching_engine | carry_staked_basis (hedge-swap slippage) |
| `defi_oracle_feeds` | defi / oracle_feeds | (chain, oracle_feed) | 5 | 7.2k (1440/cell) | mtds_read→features→strategy | carry_staked_basis (mark oracle) |
| `tradfi_ohlcv_1m` | tradfi / ohlcv_1m | (venue, instrument) | 5 | 6.9k (≤1380/cell) | mtds_read→mdps_compute→features→strategy | both (cross-asset hedge overlay) |
| `tradfi_ohlcv_1d` | tradfi / ohlcv_1d | (venue, instrument) | 5 | 5 (1/cell) | mtds_read→features→strategy | both (cross-asset hedge overlay) |

**Open calibration item (P1, DEFERRED to Phase 3 sub-agents):** populate `real_backfill_sample_uri` on each spec + tune
`default_row_count_per_day` + the axis-2 byte-size model from `gs://central-element-323112-*-{raw,processed}/...` samples
where the backfill has reached the cutover universe; for `(asset_group, data_type)` cells the backfill hasn't reached yet,
keep the estimate + a `# ESTIMATE` marker. `defi_gas` non-uniform per-chain block-rate distribution is the trickiest —
the UTL generator (Phase 2.A) carries a per-chain block-rate weighting table; do NOT distribute `row_count_per_day`
uniformly across the 5 chain shards.

## DONE block

(Filled at completion.)
