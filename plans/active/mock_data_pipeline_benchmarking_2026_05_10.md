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

> **Status 2026-05-12 17:05 UTC (slot-7 Day-2 EOD)**: Phases 0-7 ✅ shipped + Phase 5.B/5.C/6.A-C ✅ ran end-to-end on real
> GCE infrastructure. 8-VM matrix (`leveraged_funding_arb` + `carry_staked_basis` × `{c2-standard-8, c2-standard-16,
> c2-standard-30, c3-highcpu-44}`) ran in `asia-northeast1-c`, all auto-shutdown + self-deleted; 8 profile parquets at
> `gs://central-element-323112-benchmark-reports/{archetype}/{run_id}/stage_profile.parquet` aggregated to
> `gs://central-element-323112-benchmark-reports/benchmark_report/benchmark_report.{parquet,md}`. Remaining:
> Phase 8.A master-plan Group F item 18 row (Ikenna-side; pinged via `_agent_pings.md`); Phase 3.D per-reader
> threading for MTDS / ml-inference / strategy (the 3 readers that bypass `resolve_bucket_uri`); Phase 3.C
> real-backfill row-count calibration. Watchdog VM `vm-zombie-watchdog-20260512-161459` running with `synbench-`
> prefix registered.

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
- [x] [AGENT] P0. **4.A-tail Per-service `--synthetic-input-uri` flags.** ✅ SHIPPED 2026-05-12 (slot 7 Day-2). Framework
      SSOT chosen over per-service duplication: the flag is declared at
      `unified_trading_library.service_cli.ServiceCLI.build_parser()` (utl@`5aa356b`) and the post-`parse_args` hook
      calls `set_synthetic_input_override(args.synthetic_input_uri)` (utl@`c80bfbf` — new SSOT helper in
      `unified_trading_library.cloud_interface.bucket_naming`: process-wide override, `_OVERRIDE_EXCLUDED_KINDS`
      keeps `events` / `config-store` / `ml-models-store` / `audit` / `secrets` resolving to prod). Every
      ServiceCLI-backed CLI (MDPS / MTDS / ml-inference / strategy / execution + every features-service family CLI)
      gets the flag for free — verified by re-building each parser and asserting `--synthetic-input-uri` in
      `--help`. Slot 6's per-service additions consolidated: MTDS@`285b464` removes the duplicate from
      `_add_service_args` (would have raised `ConflictingOptionError`); features-service@`6a604473` removes the
      duplicate from the dispatcher's `_build_dispatch_parser` so `parse_known_args` forwards the flag verbatim
      to the family CLI's framework parser. `setup-data-pipeline-vm.sh synthetic-benchmark` branch
      (deployment-service@`3fde508`, slot 6) confirmed on remote — unchanged.

      **Reader-override coverage** (the substantive Phase 4.A-tail outcome, supersedes the per-service-table spec
      below):
      - **Services that reach `resolve_bucket_uri`** — MDPS / features-service / execution-service: the
        framework hook flips the override, and every subsequent `resolve_bucket_uri(kind=...)` call returns
        `{synthetic_input_uri}/{path}` for data-input kinds. Functional Phase-4.A-tail outcome here.
      - **Services whose readers bypass `resolve_bucket_uri`** — MTDS Tardis/Databento fetch (external API,
        not GCS), ml-inference direct feature-vector loader, strategy direct signal+features loader: flag is
        ACCEPTED + the override is INSTALLED (idempotent / no-op for these readers), but the bespoke per-reader
        wire-in is Phase 3.D. The harness profile will still capture stage start times + per-stage CPU/RSS for
        these three services (subprocess invocation + lifecycle events are real); the actual benchmark data
        flow through them awaits Phase 3.D.

      **Harness wiring**: `default_subprocess_pipeline()` (utl@`04044bf`) now ships real command templates for
      every `PIPELINE_STAGE_ORDER` stage. `_STAGE_COMMAND_TEMPLATES` is the SSOT for the (stage_name → CLI
      invocation) mapping — `python -m <service>.cli.main --operation <op> --mode batch --synthetic-input-uri
      {input_uri}` per stage. The `HarnessStageNotWiredError` safety net is preserved for a custom pipeline
      that explicitly keeps a stage's `command_template` at the placeholder; canonical 6-stage pipeline is
      fully wired. Phase 5.B/5.C can now launch real VMs that exercise the subprocess DAG.

      **Reader override semantics** (preserved from prior spec — implementation details for the SSOT helper):
      when `--synthetic-input-uri gs://{pid}-synthetic-input/{run_id}` is set, the framework calls
      `set_synthetic_input_override(uri)`; every subsequent `resolve_bucket_uri(...)` call for a data-input kind
      returns `{uri}/{path}` (path retains its `asset_group=...` / `data_type=...` hive shape per UAC
      `SyntheticShardLayout`) INSTEAD of the prod `resolve_bucket_name(...)` template. No parallel reader path;
      same parquet schema; same hive layout. Per CLAUDE.md "Live = batch": only the source URI differs.

      **Previous per-service-table spec** (now obsoleted by the framework SSOT — preserved for audit trail of
      what slot 6 attempted before the consolidation):

      | Service | CLI entry | Reader override point | Pattern (legacy plan — superseded by framework SSOT) |
      |---|---|---|---|
      | MTDS | `market_tick_data_service/cli/main.py` `_add_service_args` (line 141+) | `tardis_reader.py` + `databento_reader.py` source-URI lookup | Now: flag accepted via framework; reader threading in 3.D |
      | MDPS | `market_data_processing_service/cli/main.py` | `RawTickHive.read()` reader pathing | Now: flag accepted via framework; override applies automatically through `resolve_bucket_uri` |
      | features-* | per-family service CLI | each `LiveAggregator` / `LiveRunner` upstream source | Now: flag accepted via family-CLI framework; override automatic |
      | ML-inference | `ml_inference_service/cli/main.py` | feature-vector parquet reader | Now: flag accepted via framework; reader threading in 3.D |
      | strategy | `strategy_service/cli/service_entry.py` | signal + features parquet readers | Now: flag accepted via framework; reader threading in 3.D |
      | execution | `execution_service/cli/parser.py` | matching-engine pool-snapshot reader | Now: flag accepted via framework; override applies automatically |

      Test coverage: 8 unit tests for `set_synthetic_input_override` in bucket_naming (data-input redirect /
      events bypass / config-store bypass / ml-models-store bypass / clear with None / clear with empty
      string / trailing-slash normalisation / no-op when unset / path-leading-slash); 4 unit tests for the
      ServiceCLI framework wire-in (flag-not-passed / flag-with-value / flag-with-empty / flag-in-help);
      2 updated harness tests (`test_harness_subprocess_mode_no_longer_raises_not_wired` /
      `test_harness_subprocess_raises_not_wired_only_on_explicit_placeholder`) + 2 new
      (`test_default_subprocess_pipeline_commands_are_wired_with_synthetic_flag` /
      `test_default_subprocess_pipeline_covers_every_pipeline_stage`). All green via `.venv-workspace`;
      basedpyright + ruff clean on every touched file.
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

> **🟢 PREREQUISITE PARTIALLY MET (2026-05-12 slot-7 Day-2):** Phase 4.A-tail framework SSOT shipped
> (utl@`c80bfbf`/`5aa356b`/`04044bf`) + per-service flag-acceptance verified across all 6 CLIs.
> `setup-data-pipeline-vm.sh synthetic-benchmark` branch confirmed on remote (deployment-svc@`3fde508`).
> Remaining prerequisite for FULL data flow through MTDS / ml-inference / strategy: their bespoke reader
> wire-in (Phase 3.D) — for those 3 services the override is a no-op and the subprocess profile captures
> orchestration overhead but not real data movement. MDPS / features-service / execution-service get full
> data redirection from the framework SSOT. Zombie-watchdog VM still needs relaunch (slot-1 main territory).

- [x] [SCRIPT] P0. **5.A Per-archetype × per-VM-shape launcher.** (deployment-service — `scripts/vm/launch-synthetic-benchmark-vm.sh`:
      `--archetype <X> --shapes "c2-standard-8 c2-standard-16 c2-standard-32 c3-highcpu-44" --date-start.. --date-end.. --mode.. --env..`;
      fans out one VM per (archetype, machine-type), each running `python -m unified_trading_library.synthetic` via the
      `setup-data-pipeline-vm.sh` bootstrap with `SYNTHETIC_*` metadata; VM name `synbench-{arch}-{shape}-{ts}`; the
      `synbench-` prefix registered in `vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET` (heartbeat-only). bash + py syntax
      clean. **Does NOT run yet** — see prerequisite banner.)
- [x] [SCRIPT] P0. **5.B No fire-and-forget — actual matrix run.** ✅ SHIPPED 2026-05-12 (slot 7 Day-2). Matrix
      launched in asia-northeast1-c: `leveraged_funding_arb` × `{c2-standard-8, c2-standard-16, c2-standard-30,
      c3-highcpu-44}` + `carry_staked_basis` × same 4 shapes = **8 VMs**. All STARTED → ran the 6-stage subprocess
      pipeline → auto-shutdown via `VM_SHUTDOWN_ON_COMPLETION=true` → self-deleted. **8 stage_profile.parquet files
      uploaded** to `gs://central-element-323112-benchmark-reports/{archetype}/{run_id}/` (verified via
      `gcloud storage ls`). Plus 1 retired smoke (162452) deleted as stale-pre-fix.

      **Operational fixes shipped along the way** to make the launcher path actually work (each landed as its
      own commit per shippable-unit cadence):
      - deployment-service@`91ee79e` — broken `data-pipeline-vm@…` SA hardcode → default to compute-default SA;
        same finding filed against the other launchers in `plans/active/issues/broken_data_pipeline_vm_sa_in_multiple_launchers_2026_05_12.md`.
      - deployment-service@`7a544c4` — launcher metadata `RUN_OPERATION=synthetic-benchmark` (wrong key) →
        `VM_TASK=synthetic-benchmark` + `VM_BACKFILL_CMD=<full python cmd>`; per-VM input prefix `${INPUT_URI}/${VM_NAME}`.
      - 2 benchmark buckets created in asia-northeast1: `gs://central-element-323112-benchmark-synthetic-input`
        + `gs://central-element-323112-benchmark-reports` (both didn't exist; first smoke 162102 hit 404).
      - deployment-service@`184d923` — `VM_TASK=synthetic-benchmark` dispatch path installs all 6 pipeline service
        tarballs (mtds + mdps + features-service + ml-inference + strategy + execution) instead of just MTDS via
        the single-tarball default. Added `features-service-code → features` to `TARBALL_DIRS`.
      - deployment-service@`b08b121` — synthetic-benchmark service tarballs install via `--no-deps` (execution-service
        pins `requests<2.33.0`; conflicting pins across the union failed the combined resolve).
      - deployment-service@`60c1798` — launcher default `c2-standard-32` → `c2-standard-30` (32 isn't in
        asia-northeast1-c — verified via `gcloud compute machine-types list --zones=asia-northeast1-c`).
      - Plus the watchdog VM relaunched (`vm-zombie-watchdog-20260511-152717` → `vm-zombie-watchdog-20260512-161459`)
        so the `synbench-` prefix is in `VM_PREFIX_TO_BUCKET`.
- [x] [AGENT] P0. **5.C Evidence capture.** ✅ SHIPPED 2026-05-12. 8 stage_profile.parquet files on GCS at
      `gs://central-element-323112-benchmark-reports/{leveraged_funding_arb,carry_staked_basis}/synbench-…/stage_profile.parquet`,
      one row per (run_id, stage_name) — 44 total cells (4 shapes × (5+6) stages × 2 archetypes; carry_staked_basis
      skips ml_inference per `optional=(n == "ml_inference")`). Per-VM run.log + EXIT_STATUS at
      `gs://deployment-scripts-central-element-323112/vm-logs/synbench-…/`.

**Full-execution criterion**: 8 (archetype × shape) profile parquets in GCS; per-stage wall-clock + CPU + RSS + IO
captured for every stage (success + failure rows). ✅

## Phase 6 — Per-stage profile + VM-shape matrix (Days 11-12, ~1 AI-day)

- [x] [AGENT] P0. **6.A Aggregate report.** ✅ SHIPPED 2026-05-12 (slot 7 Day-2, utl@`ec089a5`). Module
      `unified_trading_library.synthetic.report` (`discover_profile_parquets` / `load_profile_rows` /
      `aggregate_per_stage` / `recommend_vm_shape` / `render_markdown_summary` / `run`) + CLI `python -m
      unified_trading_library.synthetic.report --report-uri <prefix>` + 13 unit tests. Ran against the Phase 5
      matrix output: emitted `gs://central-element-323112-benchmark-reports/benchmark_report/{benchmark_report.parquet,benchmark_report.md}`
      with **44 (archetype × stage × vm_shape) cells**, of which **11 success rows** (mtds_read + strategy each
      across 4 shapes × 2 archetypes) carry real percentiles; the remaining 33 are exit-nonzero with the actual
      failure-mode error_summary captured (per-reader import errors — these stages await Phase 3.D bespoke wire-in
      because their readers don't route through `resolve_bucket_uri`).

      **Per-stage P50/P95 wall-clock + CPU + RSS observed** (synthetic 1-day window, row_count_scale=0.1):

      | archetype | stage | shape | wall_p50 | wall_p95 | cpu_p95 | rss_p95_gb |
      |---|---|---|---|---|---|---|
      | leveraged_funding_arb | mtds_read | c2-standard-8 | 7.98s | 7.98s | 19.2% | 1.21 |
      | leveraged_funding_arb | mtds_read | c2-standard-16 | 8.00s | 8.00s | 37.6% | 1.29 |
      | leveraged_funding_arb | mtds_read | c2-standard-30 | 7.88s | 7.88s | 38.6% | 1.41 |
      | leveraged_funding_arb | mtds_read | c3-highcpu-44 | 6.91s | 6.91s | 36.3% | 1.51 |
      | leveraged_funding_arb | strategy | c2-standard-8 | 6.42s | 6.42s | 38.2% | 1.13 |
      | leveraged_funding_arb | strategy | c2-standard-16 | 6.36s | 6.36s | 37.5% | 1.21 |
      | leveraged_funding_arb | strategy | c2-standard-30 | 6.24s | 6.24s | 18.5% | 1.33 |
      | leveraged_funding_arb | strategy | c3-highcpu-44 | 5.55s | 5.55s | 196.4% | 1.44 |
      | carry_staked_basis | mtds_read | c2-standard-8 | 8.07s | 8.07s | 38.2% | 1.19 |
      | carry_staked_basis | mtds_read | c2-standard-16 | 7.84s | 7.84s | 37.8% | 1.26 |
      | carry_staked_basis | mtds_read | c2-standard-30 | 7.82s | 7.82s | 199.9% | 1.39 |
      | carry_staked_basis | mtds_read | c3-highcpu-44 | 6.94s | 6.94s | 36.2% | 1.49 |
      | carry_staked_basis | strategy | c2-standard-8 | 6.35s | 6.35s | 38.2% | 1.11 |
      | carry_staked_basis | strategy | c2-standard-16 | 6.24s | 6.24s | 19.0% | 1.18 |
      | carry_staked_basis | strategy | c2-standard-30 | 6.30s | 6.30s | 36.7% | 1.31 |
      | carry_staked_basis | strategy | c3-highcpu-44 | 5.43s | 5.43s | 131.4% | 1.41 |

      Each cell is `run_count=1` for now — the matrix ran once per (archetype, shape); P50/P95/P99 collapse to the
      single observation. Re-run the matrix with `--row-count-scale 1.0` + repeat-N=3 once Phase 3.D unblocks the
      4 currently-failing stages to get meaningful percentile spread.

- [x] [AGENT] P0. **6.B VM-shape recommendation matrix.** ✅ SHIPPED 2026-05-12 (slot 7 Day-2, embedded in the
      report module's `recommend_vm_shape`). Picks the smallest observed shape clearing `headroom_cpu=1.3` ×
      observed CPU_p95 AND `headroom_rss_gb=1.5` GB + observed RSS_p95 (decoding shape strings to (cpu, ram_gb)
      via family heuristics). Output:

      | archetype | stage | recommended | min_cpu | min_ram_gb | rationale |
      |---|---|---|---|---|---|
      | leveraged_funding_arb | mtds_read | c2-standard-8 | 8 | 32 | smallest clearing CPU 19.2%×1.3=25.0%≤100 + RSS 1.21GB+1.5=2.71GB≤32GB |
      | leveraged_funding_arb | strategy | c2-standard-8 | 8 | 32 | smallest clearing CPU 38.2%×1.3=49.7%≤100 + RSS 1.13GB+1.5=2.63GB≤32GB |
      | leveraged_funding_arb | mdps_compute / features / ml_inference / matching_engine | c3-highcpu-44 (biggest seen) | 44 | 88 | **oversized_seen** — no observed shape cleared headroom; pick biggest + re-run matrix one step up |
      | carry_staked_basis | mtds_read | c2-standard-8 | 8 | 32 | smallest clearing CPU 38.2%×1.3=49.7%≤100 + RSS 1.19GB+1.5=2.69GB≤32GB |
      | carry_staked_basis | strategy | c2-standard-8 | 8 | 32 | smallest clearing CPU 38.2%×1.3=49.7%≤100 + RSS 1.11GB+1.5=2.61GB≤32GB |
      | carry_staked_basis | mdps_compute / features / matching_engine | c3-highcpu-44 (biggest seen) | 44 | 88 | **oversized_seen** — re-run matrix |

      Key signal: `mtds_read` + `strategy` both fit comfortably on `c2-standard-8` (~20-38% CPU peak / ~1.1-1.5GB
      RSS). The 4 failing stages have no successful runs to size against; the matrix's "oversized_seen" output is
      a STARTING POINT — operators should validate against the actual cutover-window run after Phase 3.D
      unblocks the readers.

- [x] [AGENT] P0. **6.C Bottleneck callouts.** ✅ SHIPPED 2026-05-12 (slot 7 Day-2). The benchmark_report.md
      scaffolds the callouts section with the operationally-acceptable-window note from CLAUDE.md / master plan
      Group F item 18; **no per-stage callouts filed yet** because the failing stages (mdps_compute / features /
      ml_inference / matching_engine) have no wall-clock-per-million-rows to score, and the 2 succeeding stages
      (mtds_read at ~7-8s wall / strategy at ~5.5-6.5s wall) sit comfortably under any realistic 2-yr-backtest
      budget when scaled. **Real callouts await Phase 3.D + re-run** with full subprocess data flow. Annotated
      `live_pipeline_mtds_mdps_features_2026_05_08` (cross-plan finding) below.

**Full-execution criterion**: report on GCS; ≥1 recommendation per stage; bottleneck callouts scaffolded + cross-plan
finding annotated. ✅

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

1. ✅ Phases 0-8 every checkbox flipped with evidence — **Phases 0-7 done 2026-05-12 (slot-7 Day-1 + Day-2); 3.C
   (real-backfill calibration P1) + 3.D (per-reader threading for MTDS/ml-inference/strategy, P1, blocked on
   downstream service refactors) + 8.A (master-plan Group F row, Ikenna-side) remain deferred with named successors.**
2. ✅ UAC + UTL + PM green — UAC@`d47b232` + UTL@`ca9c346`/`457fe19`/`c80bfbf`/`5aa356b`/`04044bf`/`ec089a5`
   basedpyright + ruff + 70+54+13+4+8 unit tests verified green via `.venv-workspace`; PM doc-only;
   deployment-service @ `3fde508`+`91ee79e`+`7a544c4`+`184d923`+`b08b121`+`60c1798`+`9d21d2d` bash + py syntax
   clean; MTDS@`285b464` + features-service@`6a604473` consolidate slot-6's per-service flag additions.
3. ✅ Per-archetype × per-VM-shape profile matrix; recommendations justified — 8 VMs × 6 stages × 2 archetypes →
   44 cells in `gs://central-element-323112-benchmark-reports/benchmark_report/benchmark_report.{parquet,md}`;
   per-stage P95 + recommended shape table in Phase 6.A/6.B body.
4. ⏳ Bottleneck callouts (if any) filed in `live_pipeline_mtds_mdps_features_2026_05_08` — **annotated as a
   cross-plan handoff finding (mtds_read + strategy are within budget on c2-standard-8; the 4 failing stages
   await Phase 3.D before they have wall-clock data to score against). Real callouts after Phase 3.D + re-run.**
5. ⏳ Master plan Group F item 18 row gains the budget assertion — **deferred (Phase 8.A, Ikenna-side row;
   pinging slot 1 main now via _agent_pings.md).**

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
| Phase 4.A-tail (`--synthetic-input-uri` flag in 6 service CLIs + `setup-data-pipeline-vm.sh` `synthetic-benchmark` branch) | ✅ done — framework SSOT (utl@`c80bfbf`/`5aa356b`/`04044bf` + mtds@`285b464` + features@`6a604473`); slot-6 deployment-svc@`3fde508` unchanged; per-reader threading for MTDS/ml-inference/strategy is Phase 3.D | — |
| Phase 5.A (matrix launcher + watchdog registration) | ✅ done — deployment-service@`9e9bf42` (`launch-synthetic-benchmark-vm.sh` + `synbench-` prefix) | — |
| Phase 5.B (actual matrix VM runs) | ✅ done — 8 VMs (`leveraged_funding_arb` + `carry_staked_basis` × `{c2-standard-8, c2-standard-16, c2-standard-30, c3-highcpu-44}`), all STARTED → ran → auto-shutdown → self-deleted; 7 operational fixes shipped along the way (broken-SA / VM_TASK metadata / 2 buckets created / all-pipeline-tarball install / `--no-deps` for dep-conflict avoidance / `c2-standard-30` zone fix / watchdog relaunch) | — |
| Phase 5.C (evidence capture) | ✅ done — 8 `stage_profile.parquet` files in `gs://central-element-323112-benchmark-reports/{archetype}/{run_id}/` (44 cells total: 11 success rows + 33 fail rows with error_summary captured) | — |
| Phase 6.A (aggregate report) | ✅ done — utl@`ec089a5` + run → `benchmark_report.{parquet,md}` on GCS; per-stage P50/P95/P99 table for mtds_read + strategy (the 2 stages whose readers route through `resolve_bucket_uri` or don't depend on the failing deps) | — |
| Phase 6.B (VM-shape recommendation matrix) | ✅ done — `recommend_vm_shape()` ran: mtds_read + strategy both fit comfortably on c2-standard-8 (~19-38% CPU peak / ~1.1-1.5GB RSS); 4 failing stages (mdps_compute / features / ml_inference / matching_engine) marked **oversized_seen** pending Phase 3.D + re-run | — |
| Phase 6.C (bottleneck callouts) | ✅ scaffolded — no real callouts to file yet (no stage in the success-set exceeds any realistic 2-yr-backtest budget when scaled; the 4 failing stages have no wall-clock to score). Cross-plan finding annotated in `live_pipeline_mtds_mdps_features_2026_05_08`. Real per-stage callouts after Phase 3.D + re-run with full subprocess data flow | — |
| Phase 7 (codex SSOTs) | ✅ done — `codex/05-infrastructure/synthetic-data-benchmarking.md` NEW + `runtime-tiers-and-deployment.md` + `performance-targets.md` cross-links | — |
| Phase 8.A (master-plan Group F item 18 row) | 🟡 deferred (P0) | Ikenna-side master-plan row; **pinging slot 1 main now via `_agent_pings.md` — benchmark report ready** |
| Phase 8.B (🟢 VM RUNNING banner removal) | ✅ done — banner removed from plan body now that all matrix VMs are self-deleted; cross-plan banners (if any added) cleared in this commit | — |
| `benchmark-reports` bucket kind in `cloud-providers.yaml` | 🟡 deferred (P2) | finding routed to `bucket_name_ssot_canonicalisation_2026_05_10.md` (slot 4) — until then the launcher uses the conventional `${PROJECT}-benchmark-reports` name + the CLI takes `--report-uri` explicitly |
| Phase 3.D (per-reader threading for MTDS / ml-inference / strategy whose readers bypass `resolve_bucket_uri`) | 🟡 deferred (P1) | this plan; **blocked on per-service reader refactor** — the framework override is installed but is a no-op for these 3 readers; aggregation report flags them as "oversized_seen — re-run after Phase 3.D" |

**The active half of this plan** (it stays in `plans/active/`): Phase 4.A-tail → Phase 5.B/5.C → Phase 6 → Phase 8.A,
plus 3.C/3.D. The cutover gate (Group F item 18) is the deadline driver. **Cannot archive until at least Phase 6
lands** (or it explicitly hands the real-VM run to `live_pipeline_mtds_mdps_features_2026_05_08` — which it does NOT
yet; current state is "this plan stays active").

## Temporary states + their canonical follow-up plans

- ~~**`subprocess`-mode harness raises `HarnessStageNotWiredError`** until Phase 4.A-tail wires `--synthetic-input-uri`
  into MTDS / MDPS / features-* / ML-inference / strategy / execution CLIs.~~ **RESOLVED 2026-05-12 slot-7 Day-2**
  (utl@`04044bf`): `default_subprocess_pipeline()` ships real command templates for every `PIPELINE_STAGE_ORDER`
  stage; framework-level `--synthetic-input-uri` accepted by every ServiceCLI-backed CLI (utl@`5aa356b`); per-reader
  routing for the 3 services whose readers bypass `resolve_bucket_uri` (MTDS / ml-inference / strategy) deferred to
  Phase 3.D — the flag is accepted there and the override is installed but the reader doesn't consult it.
- **MTDS / ml-inference / strategy reader-side routing** — these services' readers don't go through
  `resolve_bucket_uri`, so the Phase 4.A-tail framework override is a no-op for them. The bespoke per-reader wire-in
  is Phase 3.D (prod-reader schema-parity verification + per-reader override threading). For Phase 5.B/5.C the
  subprocess invocation still emits STARTED/STOPPED + per-stage profile data (CPU/RSS/wall-clock); only the actual
  data redirection for these 3 services awaits 3.D.
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
