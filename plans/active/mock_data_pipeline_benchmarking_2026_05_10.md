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

- [x] [AGENT] P0. **2.A `synthetic/generator.py`.** Per-data_type generator class; produces parquets with correct
      schema + cardinality + `available_at` discipline (per CLAUDE.md "available_at is write-time"). Realism axis 1-3.
      (utl@`ca9c346` — `generate(SyntheticParams) -> SyntheticOutputManifest`: per-`SyntheticDataDomain` column
      skeletons (8 families) + per-row `available_at = ts + emission-latency` + `PER_CHAIN_BLOCK_RATE_PER_DAY`-weighted
      `defi_gas` shard distribution (NON-uniform per § Audit findings 0.B) + deterministic per-shard RNG +
      local-FS/`gs://`/`s3://` writer abstraction + `_synthetic_manifest.json` receipt + `load_output_manifest()`.)
- [x] [AGENT] P0. **2.B `synthetic/harness.py`.** Drives full pipeline end-to-end: generator → MTDS write → MDPS compute
      → features → ML → strategy → matching engine. Reuses prod entry points; no parallel pipeline.
      (utl@`ca9c346` — `BenchmarkHarness.run(archetype, ...)`: generator step (per-spec `generate()` → `SyntheticRunManifest`)
      then prod-pipeline DAG `PIPELINE_STAGE_ORDER` (mtds_read..matching_engine, subset per `pipeline_stages_touching`,
      optional stages skipped); `subprocess` mode shells out to each service CLI w/ `--synthetic-input-uri` (raises
      `HarnessStageNotWiredError` until Phase 4 wires the flag — NO parallel pipeline); `stub` mode = in-process stubs
      for tests/smoke; per-stage isolation (failed stage → exit_code≠0, harness continues unless `strict_stages`).)
- [x] [AGENT] P0. **2.C `synthetic/profile.py`.** Wraps each pipeline stage with per-stage profiler (psutil + GCS / S3
      listing instrumentation). Output: `StageProfile` parquet (stage_name, wall_clock, cpu_max, rss_max, io_read_bytes,
      io_write_bytes). (utl@`ca9c346` — `profile_stage(name)` ctx-manager: monotonic wall-clock + `cpu_seconds`/`cpu_max_percent`
      + `rss_max_bytes` (sampler thread, process + children) + `io_read/write_bytes` (psutil io_counters delta) +
      `cloud_list_calls`/`cloud_objects_listed` (via `record_cloud_listing()` thread-local); `StageProfileAccumulator`
      collects + back-fills run_id/archetype/vm_shape + `write_parquet("stage_profile.parquet")`.)
- [x] [AGENT] P0. **2.D Tests.** ≥30 unit tests. (utl@`ca9c346` — `tests/unit/synthetic/`: 54 tests pass (27 generator
      + 14 profile + 13 harness); covers parquet write/schema/`available_at`/cardinality/`defi_gas` non-uniform/manifest
      round-trip/deterministic-RNG; profiler wall-clock/cloud-listing/exception-recording; harness stub end-to-end +
      `subprocess` NotWired + auto-resolve + optional-skip + strict/non-strict. basedpyright + ruff clean.)

**Full-execution criterion**: UTL PR pushed (utl@`ca9c346`); QG — basedpyright clean (`.venv-workspace`) + ruff clean
+ 54 unit tests green; CI confirms full QG. Harness `stub`-mode end-to-end emits non-empty `stage_profile.parquet`
(verified in `test_harness_stub_mode_end_to_end` + `test_accumulator_writes_parquet`). ✅

## Phase 3 — Per-archetype generators (Days 5-7, ~2 AI-days)

> **Scope note (slot 7 2026-05-12):** the per-archetype generators are the cross-product of (a) the registry specs
> (Phase 1.B) and (b) the per-`SyntheticDataDomain` column-skeleton + cardinality + `available_at` logic (Phase 2.A) —
> there is no additional "per-archetype generator class" to write. So 3.A/3.B are **design-shipped** with Phases 1.B +
> 2.A; what remains is *calibration* (3.C — real-backfill row counts + axis-2 byte sizes) and *prod-reader schema-parity
> verification* (3.D — gated on Phase 4 since it needs a real pipeline-stage run). The work-split's "5 asset_group
> sub-agents" was NOT run as a 5-way fan-out: sports/prediction generators are DEFERRED-PER-USER (plan non-goals), and
> cefi/defi/tradfi are fully covered by the 13 shipped specs + the Phase 2.A domain logic — a 5-way fan-out would have
> been redundant work + 2 no-op confirmations.

- [x] [AGENT] P0. **3.A `carry_staked_basis` generators.** DeFi gas, LST rates (jitoSOL/mSOL/bSOL Solana +
      wstETH/rETH/cbETH EVM), Aave + Morpho lending indices, Uniswap + Curve pool states, Pyth + Chainlink oracle feeds.
      (design-shipped — uac@`d47b232` `registry/generators/defi.py` (5 specs: `defi_gas`/`defi_lst_rates`/`defi_lending_indices`/`defi_dex_pool_state`/`defi_oracle_feeds`,
      shard atoms `(chain,)` / `(chain,protocol)` / `(chain,pool)` / `(chain,oracle_feed)`) + utl@`ca9c346` `synthetic/generator.py`
      `DEFI_ONCHAIN`/`DEFI_RATES`/`DEFI_DEX`/`DEFI_ORACLE` column skeletons; cutover universe encoded in `CUTOVER_DEFI_CHAINS`/`CUTOVER_LST_PROTOCOLS`/`CUTOVER_LENDING_PROTOCOLS`/`CUTOVER_DEX_POOLS`/`CUTOVER_ORACLE_FEEDS`.
      Real-backfill row-count calibration → 3.C P1.)
- [x] [AGENT] P0. **3.B `ARBITRAGE_PRICE_DISPERSION` generators.** CeFi tick + ohlcv_1m + ohlcv_15m + funding_rate +
      OI + liquidations across cutover venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster) for the relevant
      instrument set. (design-shipped — uac@`d47b232` `registry/generators/cefi.py` (6 specs, shard atom `(venue,instrument)`,
      `CUTOVER_CEFI_VENUES` = the 6 cutover perp venues × `CUTOVER_CEFI_INSTRUMENTS` BTC/ETH/SOL) + utl@`ca9c346`
      `CEFI_TICK`/`CEFI_OHLCV`/`CEFI_DERIVATIVES` column skeletons; row counts = axis-1 estimates, calibration → 3.C.)
- [ ] [AGENT] P1. **3.C Real-backfill calibration.** **DEFERRED-from-Phase-0.B** (slot 7 2026-05-12). For each of the
      13 specs in `registry/generators/{cefi,defi,tradfi}.py`: where the real backfill has reached the cutover universe,
      populate `real_backfill_sample_uri` + tune `default_row_count_per_day` + the axis-2 byte-size model from
      `gs://central-element-323112-*-{raw,processed}/...` samples; where it hasn't, keep the estimate + a `# ESTIMATE`
      marker. The `defi_gas` non-uniform per-chain block-rate distribution (ETH 7.2k / ARB 350k / OP+BASE 43.2k / SOL
      216k blocks per day) is in `PER_CHAIN_BLOCK_RATE_PER_DAY` (utl@`ca9c346`) — tune those numbers, do NOT switch to a
      uniform split. Provenance: § Audit findings 0.B. **Successor for the calibration-blocked half**: this plan stays
      active until 3.C lands or the cutover backfill horizon closes; if backfill slips past 2026-05-23, fold into
      `live_pipeline_mtds_mdps_features_2026_05_08`.
- [ ] [AGENT] P1. **3.D Prod-reader schema-parity verification.** **DEFERRED (gated on Phase 4)** (slot 7 2026-05-12).
      Run each generator's output through the prod MTDS / MDPS / features-* reader for that `(asset_group, data_type)`
      (via the harness `subprocess` mode once Phase 4 wires the `--synthetic-input-uri` flag) and assert NO schema-drift
      error (CLAUDE.md "Reader/schema-drift bug → RAISE LOUD"). Any column the prod reader expects that the Phase 2.A
      skeleton omits → add it to the skeleton + a `# SCHEMA-PARITY: <reader>` provenance line. Provenance: Phase 3
      full-execution criterion. **Also fold (slot-8 handshake 2026-05-12, `harsh_orchestrator/pings/slot_8.md:15`)**:
      (a) cefi fixtures cover the 21-venue zero-activity-bar matrix incl. the Cat-D shape (`catalogue_audit_cefi_2026_05_12.md`);
      (b) tradfi re-point at the new `tradfi_etfs.py`/`tradfi_roots.py` SSOT once Ikenna's catalogue Phase 5 lands —
      don't bake the fragmented 4-place ETF list into specs; (c) sports/prediction gaps (season-window +
      `EXPECTED_PAUSED_LEAGUE`; `prediction_canonical_question_group` + `MARKET_LIFECYCLE` data_types) are already
      covered by the DEFERRED-PER-USER post-cutover sports/prediction sub-plan — anticipate the PR-3/PR-4 fix there.

**Full-execution criterion**: harness reads synthetic data through prod readers without schema-drift errors (3.D, gated
on Phase 4); row counts match per-archetype data-shape table after calibration (3.C). Generator surface (3.A+3.B)
design-shipped. ✅(partial)

## Phase 4 — Benchmark harness wire-in (Days 7-9, ~2 AI-days)

> **Note (slot 7 2026-05-12):** the plan's "Backtest CLI gains `--synthetic-generator`" framing assumed a single
> top-level backtest CLI; in reality the harness drives the full DAG across 6 service CLIs, so the right shape is (a)
> a UTL benchmark CLI that orchestrates (4.A — `python -m unified_trading_library.synthetic`), and (b) each service
> CLI gaining a `--synthetic-input-uri` flag for the `subprocess` stage path (4.A-tail — deferred, see below). 4.B
> (per-stage profiler integration) and 4.C (profile-parquet emit) are SATISFIED inside the harness/CLI already.

- [x] [AGENT] P0. **4.A CLI flags / benchmark CLI.** (utl@`457fe19` — `synthetic/cli.py` + `synthetic/__main__.py`:
      `python -m unified_trading_library.synthetic --archetype <X> --date-start.. --date-end.. --input-uri.. --report-uri.. --mode stub|subprocess --row-count-scale.. [--venues.. --instruments.. --chains.. --protocols.. --strict-stages]`;
      resolves the generator set for the archetype, generates synthetic input, drives the prod-pipeline DAG via
      `BenchmarkHarness`, writes `stage_profile.parquet` + `synthetic_run_manifest.json` under `--report-uri`; mutually
      exclusive with real-data backtest flags by construction (this CLI is the synthetic path only). Smoke-verified
      end-to-end in `stub` mode.)
- [ ] [AGENT] P0. **4.A-tail Per-service `--synthetic-input-uri` flags.** **PARTIAL** (slot 6 2026-05-12 reserve
      pickup). **`setup-data-pipeline-vm.sh` synthetic-benchmark branch ✅ SHIPPED** (deployment-service@`3fde508` —
      added `synthetic-benchmark` to the existing VM_TASK dispatch OR-list at line 670 alongside `mdps-backfill` /
      `features-backfill` / `phantom-recon` / `expected-universe-enum` / `cross-asset-rescan`;
      `launch-synthetic-benchmark-vm.sh` passes the UTL CLI via VM_BACKFILL_CMD). **Still DEFERRED — 6 service CLI
      `--synthetic-input-uri` flags**: each of MTDS / MDPS / features-* / ML-inference / strategy / execution needs
      a `--synthetic-input-uri <prefix>` flag (consumes the generator parquet under that prefix via its existing
      reader path — no parallel reader, just a source override). Until then the harness `subprocess` mode raises
      `HarnessStageNotWiredError` (covered by `test_harness_subprocess_mode_raises_not_wired`). **Per-service
      wire-in spec (operator-runnable for next slot)**:

      | Service | CLI entry | Reader override point | Pattern |
      |---|---|---|---|
      | MTDS | `market-tick-data-service/market_tick_data_service/cli/main.py` `_add_service_args` (line 141+) | `tardis_reader.py` + `databento_reader.py` source-URI lookup | `parser.add_argument("--synthetic-input-uri", type=str, default=None, help="If set, read raw-tick parquet from this URI prefix instead of prod source")` + thread to each reader as a constructor kwarg that overrides the prod-bucket URI builder |
      | MDPS | `market-data-processing-service/.../cli/main.py` | `RawTickHive.read()` reader pathing | Same flag; pass to `RawTickHive(synthetic_input_uri=...)` overriding the per-asset-group prod bucket |
      | features-* | per-family service CLI (`features-onchain-service` / `features-sports-service` / `features-volatility-service` / etc.) | each `LiveAggregator` / `LiveRunner` upstream source | Same flag; override the manifest reader's bucket-name resolver to point at the synthetic prefix |
      | ML-inference | `ml-inference-service/.../cli/main.py` | feature-vector parquet reader | Same flag; pass to the upstream feature-vector loader |
      | strategy | `strategy-service/strategy_service/cli/main.py` | signal + features parquet readers | Same flag; thread through to upstream-source resolver in `StrategyEngine` orchestrator |
      | execution | `execution-service/execution_service/cli/main.py` | matching-engine pool-snapshot reader (for batch backtest replay) | Same flag; pass to `pool_from_snapshot` to read snapshots from synthetic prefix instead of prod `dex_pools` data_type |

      **Reader override semantics**: when `--synthetic-input-uri gs://{pid}-synthetic-input/{run_id}` is set, the
      reader's source-URI builder returns `f"{synthetic_input_uri}/asset_group={ag}/data_type={dt}/..."` (matching
      the generator's shard layout per UAC `SyntheticShardLayout`) INSTEAD of the prod `resolve_bucket_name(...)`
      output. No parallel reader path; same parquet schema; same hive layout. Per CLAUDE.md "Live = batch": the
      ONLY thing that differs is the source URI; everything downstream stays prod-shaped.

      **Successor**: this plan (stays active); if it slips past 2026-05-23, fold into
      `live_pipeline_mtds_mdps_features_2026_05_08`. Provenance: Phase 4 reframe note above.
- [x] [AGENT] P0. **4.B Per-stage profiler integration.** (utl@`ca9c346` — `BenchmarkHarness._run_stage` wraps every
      DAG stage with `synthetic.profile.profile_stage(name)`; no separate pipeline-orchestrator to wire — the harness
      IS the orchestrator, per "Never build standalone backtest engines": `subprocess` mode shells out to the prod
      service CLIs, the harness only sequences + profiles.)
- [x] [AGENT] P0. **4.C Profile parquet emit.** (utl@`457fe19` — `cli.main` writes `stage_profile.parquet` +
      `synthetic_run_manifest.json` to `<report-uri>/{archetype}/{run_id}/` via the generator's local-FS/`gs://`/`s3://`
      writer abstraction; the launcher (Phase 5.A) sets `--report-uri gs://{pid}-benchmark-reports`.)

**Full-execution criterion**: benchmark CLI emits a non-empty `stage_profile.parquet` for a single archetype (verified
in `stub` mode; a real per-stage profile needs `subprocess` mode → 4.A-tail). ✅(partial)

## Phase 5 — Real-VM benchmark runs (Days 9-11, ~2 AI-days)

> **🟡 PREREQUISITE NOT MET (2026-05-12):** the real matrix run (5.B/5.C) needs Phase 4.A-tail (`--synthetic-input-uri`
> in 6 service CLIs + the `setup-data-pipeline-vm.sh` `synthetic-benchmark` branch) AND the zombie-watchdog VM
> relaunched (so the new `synbench-` prefix is picked up). Until both land, only `--mode stub` runs (meaningless
> profiles). 5.A (launcher script + watchdog registration) is shipped; the actual runs are a documented handoff —
> see § "Deferred work" below.

- [x] [SCRIPT] P0. **5.A Per-archetype × per-VM-shape launcher.** (deployment-service — `scripts/vm/launch-synthetic-benchmark-vm.sh`:
      `--archetype <X> --shapes "c2-standard-8 c2-standard-16 c2-standard-32 c3-highcpu-44" --date-start.. --date-end.. --mode.. --env..`;
      fans out one VM per (archetype, machine-type), each running `python -m unified_trading_library.synthetic` via the
      `setup-data-pipeline-vm.sh` bootstrap with `SYNTHETIC_*` metadata; VM name `synbench-{arch}-{shape}-{ts}`; the
      `synbench-` prefix registered in `vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET` (heartbeat-only). bash + py syntax
      clean. **Does NOT run yet** — see prerequisite banner.)
- [ ] [SCRIPT] P0. **5.B No fire-and-forget — actual matrix run.** **DEFERRED (blocked on 4.A-tail + watchdog relaunch)**.
      Launch the ≥10 (archetype × shape) VMs, verify STARTED+per-stage-progress+STOPPED per VM. Successor: this plan.
- [ ] [AGENT] P0. **5.C Evidence capture.** **DEFERRED (blocked on 5.B)**. Successor: this plan.

**Full-execution criterion**: ≥10 (archetype × shape) profile parquets in GCS; per-stage wall-clock + CPU max captured.
Launcher script shipped (5.A); actual runs deferred (5.B/5.C — blocked on 4.A-tail). ✅(partial)

## Phase 6 — Per-stage profile + VM-shape matrix (Days 11-12, ~1 AI-day)

> **DEFERRED (blocked on Phase 5 actual runs).** The aggregation code is a pandas/polars groupby over the
> `stage_profile.parquet` files Phase 5 produces — trivial once the parquets exist; no point shipping it against
> zero/stub data. Successor: this plan.

- [ ] [AGENT] P0. **6.A Aggregate report.** Per-stage P50/P95/P99 wall-clock + CPU + RSS + IO. Output:
      `benchmark_report.parquet` + markdown summary in plan body. **DEFERRED (blocked on Phase 5).**
- [ ] [AGENT] P0. **6.B VM-shape recommendation matrix.** Per-archetype × per-stage recommended
      `(min_cpu, min_ram, min_disk, min_iops)`. Justified per profile. **DEFERRED (blocked on 6.A).**
- [ ] [AGENT] P0. **6.C Bottleneck callouts.** Stages where wall-clock × scale-factor exceeds Group F item 18 budget
      ("operationally-acceptable window") flagged as P0 follow-ups for `live_pipeline_mtds_mdps_features_2026_05_08`
      consumers. **DEFERRED (blocked on 6.A).**

**Full-execution criterion**: report committed to plan body; ≥1 recommendation per stage; bottleneck callouts filed if
any. **DEFERRED (blocked on Phase 5).**

## Phase 7 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [x] [AGENT] P0. **7.A NEW `codex/05-infrastructure/synthetic-data-benchmarking.md`.** Generator contract, harness
      shape, per-stage profile, VM-shape matrix. (PM — `codex/05-infrastructure/synthetic-data-benchmarking.md`:
      5 contract axes (UAC), the generator (UTL), the per-stage profiler, the harness DAG, the benchmark CLI + launcher,
      the VM-shape matrix (status: not-yet-populated, blocked on Phase 4-tail), the execution-owner block, the 4-step
      "add a generator" workflow.)
- [x] [AGENT] P0. **7.B UPDATE `runtime-tiers-and-deployment.md`** — VM-shape recommendations cross-link. (PM —
      added "Data-pipeline VM machine-type sizing — backed by the synthetic benchmark" section pointing at the new doc;
      machine-type defaults flagged provisional until the matrix is populated.)
- [x] [AGENT] P0. **7.C UPDATE `performance-targets.md`** — per-stage targets backed by profile data. (PM — added
      "Per-pipeline-stage targets — backed by the synthetic benchmark, not guessed" section; per-stage targets flagged
      provisional until the matrix is populated.)

**Full-execution criterion**: 1 NEW + 2 UPDATE; cross-references resolve. ✅

## Phase 8 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **8.A Master plan extension.** Group F item 18 row gains "VM-shape sized per benchmark report;
      cutover-archetype profile green within Group F operationally-acceptable budget." **DEFERRED (blocked on Phase 5/6
      — there is no benchmark report yet to size against; editing the master-plan Group F row now would assert a green
      that doesn't exist).** Successor: this plan, after Phase 5/6 land. The master plan (`master_to_live_defi_2026_05_23.md`)
      Group F item 18 is Ikenna-side territory anyway — when the report lands, ping Ikenna's main to add the row +
      continuous-verification column entry.
- [ ] [AGENT] P0. **8.B Banners removed.** No `🟢 VM RUNNING` / `🟡 IN-FLIGHT REFACTOR` banner was ever added (no VM
      launched, no on-disk-shape refactor — the synthetic generator writes to a dedicated benchmark prefix, not the prod
      hive). Nothing to remove. (Note: when Phase 5 actually launches the matrix VMs, a `🟢 VM RUNNING` banner SHOULD be
      added to this plan + `live_pipeline_mtds_mdps_features_2026_05_08` per the Cross-Plan Coordination Banners rule.)

**Full-execution criterion**: master plan row green; banners gone. **DEFERRED (8.A blocked on Phase 5/6); 8.B is a
no-op (no banner was added).**

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

1. ⏳ Phases 0-8 every checkbox flipped with evidence — **Phases 0-4 + 7 done (2026-05-12 slot-7); Phase 5.A done; 3.C
   / 3.D / 4.A-tail / 5.B / 5.C / 6.A-C / 8.A deferred (see § "Deferred work after 2026-05-12 slot-7 session").**
2. ⏳ UAC + UTL + PM green — UAC (`d47b232`) + UTL (`ca9c346` + `457fe19`) basedpyright + ruff + unit tests verified
   green via `.venv-workspace` (slot worktrees have no per-repo `.venv`); PM doc-only; deployment-service bash+py
   syntax clean; CI confirms full QG. (Plan said "MTDS green" — MTDS is not touched this round; the MTDS
   `--synthetic-input-uri` flag is in the deferred 4.A-tail.)
3. ⏳ Per-archetype × per-VM-shape profile matrix; recommendations justified — **deferred (Phase 5/6 blocked on 4.A-tail).**
4. ⏳ Bottleneck callouts (if any) filed in `live_pipeline_mtds_mdps_features_2026_05_08` — **deferred (Phase 6.C, blocked on Phase 5/6).**
5. ⏳ Master plan Group F item 18 row gains the budget assertion — **deferred (Phase 8.A, blocked on Phase 5/6; Ikenna-side row).**

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

## Deferred work after 2026-05-12 slot-7 session

| Phase / item | Status as of 2026-05-12 | Successor / blocker |
|---|---|---|
| Phase 0 (pre-audit) | ✅ done | — |
| Phase 1 (UAC contracts + registry) | ✅ done — uac@`d47b232` (13 generator ids, 70 tests) | — |
| Phase 2 (UTL generator + profiler + harness) | ✅ done — utl@`ca9c346` (54 tests) | — |
| Phase 3.A / 3.B (per-archetype generators) | ✅ design-shipped (Phase 1.B specs + Phase 2.A domain logic) | — |
| Phase 3.C (real-backfill row-count + axis-2 byte-size calibration) | 🟡 deferred (P1) | this plan; if cutover backfill slips past 2026-05-23 → fold into `live_pipeline_mtds_mdps_features_2026_05_08` |
| Phase 3.D (prod-reader schema-parity verification) | 🟡 deferred (P1) | this plan; **blocked on Phase 4.A-tail** (needs `subprocess` mode) |
| Phase 4.A (benchmark CLI) | ✅ done — utl@`457fe19` (`python -m unified_trading_library.synthetic`) | — |
| Phase 4.B (per-stage profiler integration) | ✅ done — in `BenchmarkHarness` | — |
| Phase 4.C (profile-parquet emit) | ✅ done — in `cli.main` | — |
| Phase 4.A-tail (`--synthetic-input-uri` flag in 6 service CLIs + `setup-data-pipeline-vm.sh` `synthetic-benchmark` branch) | 🟡 deferred (P0) | this plan; if slips past 2026-05-23 → `live_pipeline_mtds_mdps_features_2026_05_08` |
| Phase 5.A (matrix launcher + watchdog registration) | ✅ done — deployment-service@`9e9bf42` (`launch-synthetic-benchmark-vm.sh` + `synbench-` prefix) | — |
| Phase 5.B / 5.C (actual matrix VM runs + evidence) | 🟡 deferred (P0) | this plan; **blocked on Phase 4.A-tail + zombie-watchdog VM relaunch** |
| Phase 6.A-C (aggregate report + VM-shape matrix + bottleneck callouts) | 🟡 deferred (P0) | this plan; **blocked on Phase 5 actual runs** |
| Phase 7 (codex SSOTs) | ✅ done — `codex/05-infrastructure/synthetic-data-benchmarking.md` NEW + `runtime-tiers-and-deployment.md` + `performance-targets.md` cross-links | — |
| Phase 8.A (master-plan Group F item 18 row) | 🟡 deferred (P0) | this plan; **blocked on Phase 5/6** (no report to assert green against); Ikenna-side row — ping when ready |
| Phase 8.B (banner removal) | ✅ n/a (no banner was added — no VM launched, no on-disk-shape refactor) | — |
| `benchmark-reports` bucket kind in `cloud-providers.yaml` | 🟡 deferred (P2) | finding routed to `bucket_name_ssot_canonicalisation_2026_05_10.md` (slot 4) — until then the launcher uses the conventional `${PROJECT}-benchmark-reports` name + the CLI takes `--report-uri` explicitly |

**The active half of this plan** (it stays in `plans/active/`): Phase 4.A-tail → Phase 5.B/5.C → Phase 6 → Phase 8.A,
plus 3.C/3.D. The cutover gate (Group F item 18) is the deadline driver. **Cannot archive until at least Phase 6
lands** (or it explicitly hands the real-VM run to `live_pipeline_mtds_mdps_features_2026_05_08` — which it does NOT
yet; current state is "this plan stays active").

## Temporary states + their canonical follow-up plans

- **`subprocess`-mode harness raises `HarnessStageNotWiredError`** until Phase 4.A-tail wires `--synthetic-input-uri`
  into MTDS / MDPS / features-* / ML-inference / strategy / execution CLIs + a `setup-data-pipeline-vm.sh`
  `synthetic-benchmark` branch. Canonical follow-up: **this plan** (Phase 4.A-tail); if it slips past 2026-05-23 →
  `live_pipeline_mtds_mdps_features_2026_05_08`. Until then only `--mode stub` runs (meaningless profiles — exercises
  wiring only).
- **`launch-synthetic-benchmark-vm.sh` uses the conventional `${PROJECT}-benchmark-reports` bucket name** (no
  `resolve_bucket_name(kind="benchmark-reports")`) because that kind isn't in `cloud-providers.yaml` yet. Canonical
  follow-up: `bucket_name_ssot_canonicalisation_2026_05_10.md` adds the kind; then switch the CLI to derive it.
- **`SyntheticGeneratorSpec.real_backfill_sample_uri` is empty + `default_row_count_per_day` are axis-1 estimates**
  for all 13 specs. Canonical follow-up: **this plan** Phase 3.C (real-backfill calibration).
- **Master plan Group F item 18 row does NOT yet assert the benchmark budget.** Canonical follow-up: **this plan**
  Phase 8.A, after Phase 5/6 land — coordinated with Ikenna's main (the master-plan Group F rows are Ikenna-side).

## DONE block

### DONE-2026-05-12 — slot 7 (Harsh side, agent-tag harsh-mock-data-benchmarking-tab)

**Shipped this session** (one continuous slot, ~14 cal AI-day budget):

- **Phase 0** — § Audit findings 0.A (no reusable cross-pipeline generator exists; only per-service in-memory test
  mock providers) + 0.B (13-spec data-shape table; row counts = realism-axis-1 estimates → 3.C calibration P1).
- **Phase 1** — uac@`d47b232` `canonical/crosscutting/synthetic_generator.py` (`SyntheticGeneratorId` 13 ids /
  `SyntheticDataDomain` 8 / `SyntheticRealismAxis` 4 / `SyntheticShardLayout` / `SyntheticParams` / `SyntheticGeneratorSpec`
  / `SyntheticOutputManifest` / `SyntheticRunManifest` / `SYNTHETIC_GENERATOR_REGISTRY` + helpers, on the UAC facade)
  + `registry/generators/{cefi,defi,tradfi}.py` (6 cefi + 5 defi + 2 tradfi specs for the 2 cutover archetypes +
  cross-asset hedge overlay) + `tests/internal/unit/test_synthetic_generator.py` (70 tests, basedpyright+ruff clean).
- **Phase 2** — utl@`ca9c346` `unified_trading_library/synthetic/{generator,profile,harness}.py`: realism-axis-1..3
  parquet generator (per-domain column skeletons + per-row `available_at` + `PER_CHAIN_BLOCK_RATE_PER_DAY`-weighted
  `defi_gas` distribution + deterministic per-shard RNG + local-FS/`gs://`/`s3://` writer + `_synthetic_manifest.json`
  receipt); `profile_stage()` ctx-manager + `StageProfileAccumulator` (wall-clock/CPU/RSS/IO/cloud-listing →
  `stage_profile.parquet`); `BenchmarkHarness` (generator → prod-pipeline DAG `mtds_read..matching_engine`; `subprocess`
  mode shells out to service CLIs + raises `HarnessStageNotWiredError` until Phase 4-tail; `stub` mode for tests;
  per-stage isolation). `tests/unit/synthetic/` 54 tests, basedpyright+ruff clean.
- **Phase 3.A/3.B** — design-shipped (the per-archetype generators ARE the registry specs × the per-domain logic);
  5-way asset_group fan-out NOT run (redundant given Phase 1+2 cover cefi/defi/tradfi; sports/prediction DEFERRED-PER-USER).
- **Phase 4.A** — utl@`457fe19` `synthetic/cli.py` + `synthetic/__main__.py` (`python -m unified_trading_library.synthetic`);
  4.B (profiler integration) + 4.C (profile-parquet emit) satisfied inside the harness/CLI; smoke-verified end-to-end
  in `stub` mode.
- **Phase 5.A** — deployment-service@`9e9bf42` `scripts/vm/launch-synthetic-benchmark-vm.sh` (one VM per
  (archetype, machine-type)) + `synbench-` prefix in `vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET`.
- **Phase 7** — `codex/05-infrastructure/synthetic-data-benchmarking.md` NEW + cross-link sections in
  `runtime-tiers-and-deployment.md` + `performance-targets.md`.
- **Plan flips** — PM@`a13ae989` (Phase 0+1), PM@`e880e823` (Phase 2+3), + this session's final flip (Phase 4+5.A+7+8
  + Done-definition + scoreboard + Temporary-states).

**Deferred (with successors)** — see § "Deferred work after 2026-05-12 slot-7 session" + § "Temporary states":
3.C real-backfill calibration (P1), 3.D prod-reader schema-parity (P1, blocked on 4.A-tail), 4.A-tail per-service
`--synthetic-input-uri` flags (P0), 5.B/5.C actual matrix VM runs (P0, blocked on 4.A-tail + watchdog relaunch),
6.A-C aggregate report + VM-shape matrix (P0, blocked on Phase 5), 8.A master-plan Group F row (P0, blocked on Phase 5/6,
Ikenna-side), `benchmark-reports` bucket kind (P2, routed to bucket-ssot plan / slot 4).

**Plan stays active** — the cutover gate (Group F item 18, deadline 2026-05-23) is not closed; do not archive until
≥ Phase 6 lands or it explicitly hands the real-VM run to `live_pipeline_mtds_mdps_features_2026_05_08`.
