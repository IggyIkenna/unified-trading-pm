---
name: mock-data-pipeline-benchmarking
overview: >-
  Can we benchmark feature-processing / ML / strategy-backtest / execution-backtest bottlenecks on a VM today using
  synthetic mock data — without first completing the full multi-year market-tick backfill? Audits whether schemas,
  generators, and harnesses already exist or what's missing. **Strict reuse principle**: use `e2e-testing` +
  `deployment-service` + service repos as-is; non-prod buckets but same bucket structure as prod; same code paths as
  much as possible. NO parallel mock-stack.
type: question
status: plan-spawned
created: 2026-05-10
plan_spawned: 2026-05-10
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_plan: plans/active/mock_data_pipeline_benchmarking_2026_05_10.md
related_codex:
  - /codex/02-data/contracts-scope-and-layout.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/honest-absence-downstream-handling.md
  - /codex/04-architecture/batch-live-architecture.md
  - /codex/04-architecture/shard-level-failure-isolation.md
  - /codex/05-infrastructure/runtime-tiers-and-deployment.md
  - /codex/05-infrastructure/vm-tarball-deployment.md
  - /codex/05-infrastructure/launcher-script-ssot.md
  - /codex/05-infrastructure/live-pipeline-architecture.md
  - /codex/06-coding-standards/quality-gates.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/ml_and_features_master_2026_05_07.md
  - plans/epics/strategy_and_dart_master_2026_05_07.md
  - plans/epics/infrastructure_master_2026_05_07.md
  - plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  - plans/active/features_repo_consolidation_2026_05_08.md
related_questions:
  - plans/questions/batch_live_design_symmetry_2026_05_08.md
  - plans/questions/topology_features_strategy_ml_execution_2026_05_08.md
  - plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
  - plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Mock-data pipeline benchmarking — feature / ML / strategy / execution-backtest bottleneck audit

## Intent

The May-23 cutover requires that **a 2-year batch backtest run completes inside an operationally-acceptable window**
(master plan Group F item 18) and that **paper-trade smoke runs end-to-end without bottlenecking** (Group F item 17).
Today we don't know what those run-times actually are. Each downstream consumer (features-\* / ml-training /
ml-inference / strategy-service co-located with position-balance + risk + execution-service in matching-engine mode) has
been built incrementally; nobody has measured "given a representative day's worth of input data, how long does this
stage take on a VM, what's the per-stage CPU / memory / IO profile, and where's the bottleneck."

The blocker for measuring this today is **input data**: the canonical answer would be "run the full pipeline on a real
backfilled day from disk." But the backfills are partial, mid-flight, or post-cutover-only across several asset_groups.
Waiting for backfill completion to start measuring downstream throughput is the wrong sequencing — by the time the data
lands, we discover (a) features-volatility takes 8 hours per day on the chosen VM shape, (b) ml-training OOMs at the
chosen instance size, (c) strategy-backtest is single-threaded for a known-fixable reason. Each of those is a 1-week
post-cutover surprise we can pre-empt by benchmarking on synthetic data NOW.

The question is whether the workspace can already drive every downstream consumer end-to-end with synthetic data — same
parquet schema, same `data_type`, same `available_at` semantics, same shard-key matrix per asset_group, same row counts
per day, same NaN ratios, same empty-confirmed reason distribution. If yes: spin up VMs and measure. If no: identify
what's missing and ship that as a pre-cutover prerequisite.

This is a different question from `master_to_live_defi_2026_05_23.md` Group F item 18 (which assumes real backfill
data); this is the **synthetic-data path** that lets us de-risk the same Group F gate weeks earlier.

## Guiding principle — reuse, don't fork

**The mock-data path is NOT a parallel stack.** It uses what's already in the workspace, with the absolute minimum new
code on top:

- **`e2e-testing` repo** — the existing harnesses (`scripts/defi/colocated_engine.py`, sports / prediction harnesses,
  any other end-to-end runners) are the entry-point. Extend, don't re-author.
- **`deployment-service` VM launchers** — per the workspace VM-launcher SSOT, every benchmark VM launches via
  `deployment-service/scripts/vm/launch-*-vm.sh`. Add a `launch-benchmark-vm.sh` if missing; do NOT spin VMs from
  outside the SSOT.
- **Service repos as-is** — every service (features-_ / ml-_ / strategy-service / execution-service / position-balance /
  risk / mtds / mdps / instruments) runs the exact same code path under benchmark as it does under prod. NO benchmark
  forks of service code, NO `if benchmark_mode:` branches, NO mock-mode shims inside service business logic. The seam is
  at data-source + bucket-name, not inside the service.
- **Non-prod buckets, same bucket structure** — benchmark runs read / write to a separate bucket suffix (e.g.
  `<prefix>-benchmark-` instead of `<prefix>-` for prod) but with **the exact same internal hive partitioning, parquet
  schema, manifest layout, and path templates**. Per CLAUDE.md "VM Naming Convention" + the `VM_PREFIX_TO_BUCKET`
  registry, this is a 1-line registry addition + a `--bucket-suffix benchmark` flag through `UnifiedCloudConfig`, not a
  reader-side fork.
- **Same code paths as much as possible** — a benchmark VM running features-volatility loads the same Python module,
  same UAC contracts, same UTL helpers, same `ManifestWriter`, same `ApiKeyReloader`, same shard-level-failure-isolation
  loop as prod. The data it consumes is synthetic + the bucket it writes to is benchmark-suffixed; everything else is
  byte-for-byte identical to prod.

**Why the reuse discipline matters.**

1. **Bottleneck attribution.** A benchmark that runs through a parallel stack measures the parallel stack's bottlenecks,
   not prod's. The whole exercise is wasted if the answer doesn't transfer.
2. **Drift.** Per CLAUDE.md "Two teammates × multiple parallel agents" — a parallel stack rots faster than the prod
   stack because nobody runs it as their day job. By cutover week, the mock stack is N commits behind prod and the
   benchmark numbers are stale before they're reported.
3. **Citadel-grade § 7 SSOT discipline.** "Types/schemas belong in ONE place." The same applies to harness logic, VM
   launchers, manifest writers, reader fallbacks. A second mock-stack-only path violates the SSOT discipline by
   construction.
4. **Compose with existing rules.** "Plans Run To Actual Completion, Not Smoke-Test Green" applies — a benchmark that
   runs through a parallel stack is smoke-test-green-but-not-real. The reuse discipline IS the realness gate.

**The narrow exception** — synthetic-data **generators** are net-new code by definition. They live in a single SSOT
module (`unified-trading-library/synthetic_data/` or under a designated package), produce parquets that satisfy the
exact UAC schema contract, and write to non-prod buckets with the same path templates as prod. The generator IS the
parallel-stack surface, scoped to data production only — every consumer downstream of the bucket runs prod code.

Three concrete reasons for raising this question now:

1. **De-risk the May-23 deadline.** If features-volatility or ml-training has a sub-linear bottleneck (e.g.
   single-threaded NumPy compute, GIL contention, IO-thrash on small parquet files), discovering it 1 week before
   cutover is a crisis; discovering it 4 weeks before is solvable. Mock-data benchmarking shifts the discovery curve
   left.
2. **Backfills are mid-flight + uneven.** TradFi has data; CeFi has data; DeFi backfills are incomplete (Solana LST
   yields, on-chain fees, funding rates partial); sports + prediction lifecycles are still being canonicalized. Waiting
   for symmetry is a multi-week stall on benchmarking that doesn't need real data.
3. **VM-shape sizing is a P0 cost decision.** Before we provision the production fleet, we need to know "is
   `c2-standard-16` enough for features-volatility, or do we need `c2-standard-32` / `c3-highcpu-44`?" Mock-data
   benchmarking is the cheapest way to answer.

The audit is not "grep for mock fixtures." It's **"can the operator launch a VM today using
`deployment-service/scripts/vm/launch-benchmark-vm.sh`, with the existing service code unmodified, reading synthetic
data from a `*-benchmark-*` bucket with the same hive structure as prod, drive features → ML → strategy →
execution-backtest end-to-end, measure per-stage wall-clock + CPU + memory + IO, and produce a per-stage bottleneck
report — without backfilling a single byte of real market data and without forking any service code path."** Every gap
is a pre-cutover prerequisite.

## Question

### Block A — Schema knowledge: do we know enough to generate the right shape?

A1. **Per-data_type input schema — feature consumers.** For every `(asset_group, data_type)` that any features-\*
service consumes, do we have a canonical schema declaration in UAC describing exactly the parquet columns + types +
cardinalities a mock generator must produce? Specifically:

- **CeFi tick data** — `ticks`, `ohlcv_1m`, `ohlcv_15m`, `ohlcv_1h`, `funding_rate`, `open_interest`, `liquidations`,
  `book_top`, `trades` per venue + instrument_type (spot / perpetual / option / future).
- **DeFi data** — `gas_fees`, `lst_rates`, `vault_metrics`, `lending_indices`, `dex_swaps`, `pool_state`,
  `oracle_prices` per chain + protocol.
- **TradFi data** — `ohlcv_1m`, `ohlcv_15m`, `options_chain` (per ES.OPT 11-cluster taxonomy), `futures_chain`, ETF tick
  / quote.
- **Sports data** — `fixtures`, `lineups`, `injuries`, `fixture_events`, `fixture_stats`, `player_stats`,
  `odds_snapshot`, `odds_movement`, `arbitrage`, `weather`, `understat_xg`, `sfi_progressive`.
- **Prediction data** — CLOB ticks per `canonical_question_group`, market lifecycle (`market_created_at` /
  `resolution_time` / `settlement_time`), per-market_id state.

A2. **Per-feature-group input contract.** For every feature_group declared in UAC's `feature_group → required_inputs`
DAG (referenced by CLAUDE.md "shard-granularity SSOT"), do we know the EXACT inputs (data_types + shard atoms + temporal
window) the feature compute reads? If the DAG exists in code but not in a parsable SSOT, mock-data generation can't be
fully automated.

A3. **Per-ML-pipeline input contract.** For every ML training pipeline + inference pipeline (model_family declared in
UAC), do we know which feature_groups feed it + which target / label columns exist + per-window cardinality?

A4. **Per-strategy / archetype input contract.** For every strategy archetype (`carry_staked_basis`,
`leveraged_funding_arb`, sports archetypes, prediction archetypes), do we know the exact features + market data the
signal generator reads?

A5. **Execution-service backtest input contract.** The execution-service matching engine consumes simulated orders +
tick history. For the matching engine in batch / paper mode:

- What's the exact tick history schema it reads (per venue + instrument_type)?
- What metadata about the venue (fee tier, liquidity profile, latency model) does it need?
- What order-stream shape does the strategy → execution boundary produce?

A6. **`available_at` write-time discipline in mock data.** Per CLAUDE.md "available*at is a write-time column, never
derived at read-time" + per-source stamping rules. Mock generators MUST stamp `available_at` correctly, or
`LookaheadBiasError` will fire on every features compute. Audit: do we have per-source stamping helpers
(`unified_trading_library.availability_stamping.stamp_available_at*\*`) wired into generators?

A7. **Honest-absence + 4-state taxonomy in mock data.** Per CLAUDE.md, every shard's manifest row is one of `captured` /
`empty_confirmed` / `attempted_failed` / `expected_unattempted`, and parquet rows reflect honest gaps. Mock generators
must produce a representative mix — not just 100%-captured days — or downstream NaN-handling code paths are never
exercised under benchmark.

A8. **Schema versioning + drift.** Has the schema for any data_type changed in the last 6 months (column added / dropped
/ renamed)? If yes, are mock generators version-aware?

### Block B — Reuse audit: existing e2e-testing + deployment-service + service-repo surface

B1. **`e2e-testing` repo inventory — what's already there?** Per CLAUDE.md "Peripheral Script Directories Under
Primary-Consumer QG" the `e2e-testing/scripts/` tree contains harnesses imported by primary consumers. Audit each
sub-directory for benchmark-relevant shape:

- `e2e-testing/scripts/defi/colocated_engine.py` — paper-trade harness for the colocated DeFi engine. Does it support
  synthetic-data injection? Does it emit per-stage timing? Per CLAUDE.md it had a `get_strategy_factories` import-rot
  incident — is it currently green?
- `e2e-testing/scripts/sports/` — sports end-to-end harnesses.
- `e2e-testing/scripts/prediction/` — prediction harnesses.
- Any per-asset_group harness, per-archetype harness, per-service smoke harness.

For each: (a) what it does today, (b) whether it can drive on synthetic input, (c) whether it emits structured event
timing per stage.

B2. **`deployment-service/scripts/vm/` launchers — what's already there?** Per CLAUDE.md "VM launcher script SSOT" every
launcher lives here. Audit:

- Existing launcher patterns (`launch-cefi-*-vm.sh`, `launch-tradfi-*-vm.sh`, `launch-mtds-*-backfill-vm.sh`,
  `launch-sfi-forward-poll.sh`, `launch-vm-zombie-watchdog.sh`, etc.).
- Tarball / tarball-from-local / sibling-clone modes — which is right for benchmark VMs (probably tarball-from-local
  during dev iteration, tarball for CI).
- Singleton-lock pattern — benchmark VMs probably want singleton-lock per benchmark-name to avoid two simultaneous runs
  clobbering shared mock buckets.
- `VM_PREFIX_TO_BUCKET` watchdog dict — needs `benchmark-` prefix entry pointing at non-prod bucket.
- Event-stream verification per `No fire-and-forget VM launches` HARD RULE — the benchmark launcher must emit STARTED +
  per-stage progress + STOPPED.

B3. **Service-repo benchmark / profile entrypoints.** Per service, audit for existing benchmark scripts:

- features-_ services — `scripts/benchmark/_.py`, `scripts/profile/\*.py`, perf tests under `tests/perf/`.
- ml-training-service — per-model-family training profile.
- ml-inference-service — per-batch inference latency / throughput.
- strategy-service — per-archetype signal-generation timing.
- execution-service matching-engine — fill-simulation throughput.
- position-balance-monitor — position-update latency under load.
- risk-and-exposure-service — pre-flight risk-check latency.
- mtds — adapter throughput per venue (the recent `ParallelPerSymbolRunner` work has implicit timing measurement).
- mdps — bar-aggregation throughput per (venue, data_type).

For each: (a) entrypoint exists / partial / missing, (b) whether it consumes the SSOT generator surface (Block C) or
ad-hoc fixtures.

B4. **Synthetic-data generator inventory — workspace-wide.** What synthetic-data generators exist today?

- **CeFi tick generators** — random walk + tick discretization + bid-ask spread + trade-flow.
- **OHLCV bar generators** — bars from ticks + corner cases (gaps, halts).
- **Funding / OI / liquidation generators** — periodic event streams.
- **DeFi data generators** — gas-price walks, LST rate walks, lending-index curves, pool-state evolutions, oracle-price
  feeds.
- **TradFi options-chain generators** — Black-Scholes-driven IV surfaces + 11-cluster ES.OPT shape.
- **Sports data generators** — fixture schedule + per-fixture event timeline + per-fixture odds curve.
- **Prediction CLOB generators** — order-book snapshots + canonical-question-group lifecycles.
- **Order / fill stream generators** — execution-service input.
- **Feature-output generators** — synthetic feature parquets to test ML / strategy independent of upstream feature
  compute.

For each: file location, current realism axis, parametric scaling support, schema-version awareness.

B5. **Coverage gaps — which data_types have NO generator today?** Per the inventory in B4, enumerate every
`(asset_group, data_type)` with no synthetic generator. These are pre-benchmark blockers.

B6. **Realism axis — how realistic do generators need to be?** Bottleneck benchmarking has different realism needs than
correctness testing:

- **CPU-bound bottleneck measurement** — needs realistic row counts + column types + cardinalities + per-day shard
  distribution. Doesn't need realistic price dynamics.
- **Memory-bound bottleneck measurement** — needs realistic per-shard parquet file sizes + group-by cardinalities.
- **IO-bound bottleneck measurement** — needs realistic shard-count-per-day + parquet-file-count + GCS / S3 listing
  depth.
- **Algorithmic-correctness benchmarking** — needs realistic dynamics (autocorrelation, vol clustering, fat tails).

Most bottleneck work is in the first three buckets. Audit: which axis does each existing generator target?

B7. **Per-shard-key parametric scaling.** For benchmarking VM shape, generators must dial up / down:

- Number of instruments per (venue, day) — small (5) / medium (50) / large (500).
- Tick density per instrument-day — sparse (1k/day) / medium (100k/day) / dense (10M/day).
- Number of feature_groups computed per day.
- Feature window-length (rolling-N-bars where N varies).

Audit: are existing generators parametric on these axes, or do they hard-code shapes?

B8. **Realistic NaN / missing-data ratios.** Per CLAUDE.md "honest absence" — DeFi has empty_confirmed days
(pre-genesis), sports has paused-league windows, prediction has pre-market-creation windows. Mock generators must
reproduce these distributions.

B9. **Cross-source merge behaviour for mock data.** Per CLAUDE.md `SOURCE_PRIORITY` + multi-source merge. Some
data_types have multiple sources. Do generators support multi-source mode (produce 2+ source streams that merge per
priority order)?

### Block C — Bucket + path SSOT for non-prod runs

C1. **Bucket-suffix discipline — `*-benchmark-*` namespace.** Per the reuse principle, benchmark runs use separate
buckets but the same internal structure. Audit:

- Current `UTL@bucket_naming.py` SSOT (per Tab 4 work `UTL@780a9575`) — does it already support a `--bucket-suffix` /
  `--env benchmark` knob?
- `UnifiedCloudConfig` mediation — is the bucket-prefix selection threaded through UCI such that a single env-var flips
  every consumer + writer atomically, or is bucket-naming spread across many call-sites?
- Per asset_group, per cloud (GCP + AWS) — list of benchmark buckets needed (one per prod bucket today, OR a single
  benchmark bucket covering all asset_groups for the duration of the experiment).

C2. **Path templates + hive partitioning — same as prod.** The on-disk shape inside the benchmark buckets MUST match
prod byte-for-byte:

- Hive partitioning vocab (`asset_group=` canonical, `category=` legacy preserved).
- `data_type=`, `venue=`, `chain=`, `instrument_type=`, `day=YYYY-MM-DD`, `instrument_id=` (or chain-bundle for bundled
  data_types).
- Manifest path templates (`_index/availability_index.parquet`, `_index/per_vm/{vm_name}.parquet`).
- Per-asset_group reader fallback paths — `category=` legacy first-then-canonical, etc.

If any consumer reads via hardcoded path (not the UTL helper), the benchmark-bucket variant won't be found.

C3. **Bucket provisioning + lifecycle.** Who provisions the benchmark buckets, on what cadence?

- One-time at benchmark-run start, torn down after the run completes (cheap, but loses regression-tracking history).
- Persistent benchmark buckets per asset_group, retained with lifecycle policies (1-week / 1-month TTL on parquets).
- Per-experiment buckets with a UUID suffix for parallel benchmark runs.

C4. **Reader-side bucket-suffix awareness.** Consumers (features-_ / ml-_ / strategy / execution / position-balance /
risk) must read from `*-benchmark-*` when in benchmark mode. Audit:

- Does every consumer read bucket via UCI (the right path) or via `os.environ` + hardcoded prefix?
- Per the rule "no `os.getenv()` for credentials" — does the same discipline extend to bucket-name resolution?
- Hot-reload / runtime-flip — can a single env-var on the benchmark VM redirect every read + write to the benchmark
  bucket without code changes?

C5. **Manifest-bucket parity.** The availability manifest IS the SSOT for "what data exists." Benchmark runs need a
benchmark-bucket manifest with the same schema as prod, populated by the synthetic-data generators (which call
`record_captured` / `record_empty` / `record_failed` / `record_expected_unattempted` exactly as prod adapters do). No
fork of `ManifestWriter`, no shortcut "just put the parquets there and fake the manifest."

### Block D — End-to-end harness reuse

D1. **`e2e-testing` harness extension over fork.** For each existing harness, the benchmark variant is a
`--mode benchmark` flag (or equivalent) that:

- Switches data source from real-bucket to benchmark-bucket (single env-var per C4).
- Wraps each stage in a timing span (per D3).
- Emits structured events on the same event-stream contract as prod harnesses.
- Auto-shutdowns the VM with results uploaded to a benchmark-results bucket.

NO new harness files unless absolutely necessary. NO copy-paste of `colocated_engine.py` to
`colocated_engine_benchmark.py`.

D2. **Single benchmark-runner entrypoint.** Define ONE script (location TBD —
`deployment-service/scripts/vm/run-pipeline-benchmark.sh` OR `e2e-testing/scripts/benchmark/run-pipeline-benchmark.sh`)
that:

- Takes `--asset-group` + `--archetype` + `--mode {paper,batch}` + `--scale {small,medium,large,custom-spec}` flags.
- Routes to the appropriate existing `e2e-testing` harness with the right env-vars set.
- Emits per-stage events with timing.
- Aggregates a bottleneck report.

D3. **Profiling instrumentation — additive, not invasive.** Per the reuse principle, profiling lives outside service
code:

- `cProfile` / `py-spy` / `austin` attached at process boundary by the launcher (no `import cProfile` inside
  features-volatility business logic).
- `memray` / `memory_profiler` attached at process boundary.
- IO counters from `/proc/<pid>/io` polled by a watchdog goroutine in the launcher script.
- OpenTelemetry spans via the existing event-stream contract — service emits `STAGE_STARTED` / `STAGE_COMPLETED` events
  with per-stage metadata; the bottleneck report aggregator parses these from the event stream.

If service code needs to be modified to emit per-stage events, that's a prod-relevant improvement (same event in prod
benefits observability) — ship it as a service-side change with the benchmark consumer, not as a benchmark fork.

D4. **VM-launch chain reuse.** The benchmark VM launches via `deployment-service/scripts/vm/launch-benchmark-vm.sh` (new
script, but pattern-matched to existing launchers). VM behaviour:

- Pulls tarball per CLAUDE.md "VM tarball deployment" — same tarball as prod.
- Sets `CLOUD_PROVIDER` + `BUCKET_SUFFIX=benchmark` (or equivalent) — single env-var diff vs prod.
- Sets `VM_NAME=benchmark-<asset_group>-<archetype>-<scale>-<RUN_TS>` per VM Naming Convention.
- Registers prefix `benchmark-` in `VM_PREFIX_TO_BUCKET` watchdog dict pointing at benchmark events bucket.
- Auto-shutdowns at benchmark completion + emits `STOPPED` event with full result link.

### Block E — Bottleneck taxonomy: what are we measuring?

E1. **Per-stage wall-clock breakdown.** For each downstream stage, the canonical bottleneck-classification axes:

- **CPU-bound** — single-threaded compute, GIL contention, NumPy / Pandas operation cost.
- **Memory-bound** — peak RSS, swap thrashing, GC pause time.
- **IO-bound** — parquet read latency, GCS / S3 listing depth, per-file open/close cost.
- **Network-bound** — cross-cloud reads (AWS ↔ GCP), Pub/Sub latency.
- **Algorithmic** — known O(N²) loops, redundant recomputation, no-vectorization Pandas anti-patterns.

E2. **Per-stage scaling characteristics.** How does each stage scale with: number of instruments, tick density per
instrument, number of feature_groups, number of strategies, number of clients (per the client-flow question doc)?

E3. **Per-stage VM-shape recommendation.** Output of the benchmark: per stage, the recommended (instance-shape,
parallelism degree, memory headroom) for the production fleet. Feeds deployment-service VM provisioning + cost
forecasting.

E4. **Bottleneck remediation backlog.** Findings from benchmark runs feed a backlog: "features-volatility is
single-threaded, fixable via Numba; ml-training is IO-bound, fixable via parquet pre-cache; strategy-backtest has GIL
contention, fixable via process-pool fan-out." Each becomes a P0 / P1 / P2 todo folded into the appropriate epic plan.

### Block F — End-to-end audit recipe — verifying the system today

F1. **One-stop benchmark entrypoint script.** Script that, run from a benchmark VM, executes the full per-stage
benchmark suite + emits a bottleneck report (covered in D2).

F2. **Owner declaration per `Runbook Execution-Owner SSOT` HARD RULE.** This script needs an `execution.owner`:

- Owner — which Tab / cron / service maintainer.
- Cadence — pre-cutover one-shot, plus weekly continuous-verification post-cutover.
- Verifier — explicit threshold per stage (e.g. "features-volatility per-day < 30min on c2-standard-16").
- `last_executed` — populated once the benchmark runs.

F3. **Per-mode benchmark variants.**

- **Paper mode** — exercises full live-pipeline shape with synthetic upstream data.
- **Batch mode** — exercises 2-year backtest shape on compressed synthetic data (e.g. 7 days of high-density mock data
  simulating 2 years of bottleneck pressure).
- **Live mode** — pre-cutover, can't truly benchmark without real venues; defer to `paper_vs_live_workflow_maturity` Q.

F4. **Per-archetype benchmark variants.** Per archetype, drives only the relevant feature_groups + ML pipelines +
strategy.

F5. **Continuous-verification path.** Per the `Master Plan Continuous-Verification Column` HARD RULE, the benchmark
output feeds a per-stage threshold gate. If features-volatility regression-detects at +30% wall-clock vs baseline, P0
alert.

F6. **Pre-cutover gate — May-23 sign-off.** Define the explicit benchmark-readiness gate:

- Per-stage benchmark green per F2 thresholds.
- VM-shape decisions ratified per stage.
- Bottleneck remediation backlog items P0-tagged for fix-before-May-23, P1+ deferred to post-cutover.

### Block G — Composability with adjacent question docs

G1. **Composes with `batch_live_design_symmetry_2026_05_08.md`.** The reuse principle in this doc is the operational
expression of batch=live design symmetry — benchmark runs through the same code paths as prod, only fill-source +
bucket-suffix differ.

G2. **Composes with `topology_features_strategy_ml_execution_2026_05_08.md`.** The runtime topology decisions there
constrain benchmark targets — we benchmark the colocated configurations in the topology doc, not arbitrary fan-outs.

G3. **Composes with `paper_vs_live_workflow_maturity_2026_05_08.md`.** Paper mode (G1 there) is a benchmark target; the
maturity gates inform what "ready to benchmark" means.

G4. **Composes with `api_keys_wallets_accounts_readiness_2026_05_08.md`.** Mock-data benchmarking requires NO live venue
/ wallet credentials — the credential-light path that lets us measure compute throughput before credentials block.

G5. **Composes with `disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md`.** Circuit-breaker latency under
load is itself a benchmark stage; reconciliation throughput on synthetic data is a benchmark target.

G6. **Composes with `defi_readiness_catalogue_2026_05_08.md`.** The DeFi data catalogue defines what data_types exist;
the benchmark suite needs mock generators per cataloged DeFi data_type.

G7. **Composes with `live_pipeline_mtds_mdps_features_2026_05_08.md` + `features_repo_consolidation_2026_05_08.md`.**
The live-pipeline architecture decisions become benchmark VM-shape targets; features-consolidation must land before the
unified features benchmark surface is well-defined.

## What "answered" looks like

- A canonical plan exists in `plans/active/mock_data_pipeline_benchmarking_<date>.md`. The plan has per-Block phases:
  Block B (reuse audit + generator gap-fill), Block C (bucket SSOT + non-prod path discipline), Block D (harness
  extension), Block E (bottleneck taxonomy SSOT), Block F (audit-recipe + entrypoint script).
- A codex SSOT in `/codex/05-infrastructure/synthetic-data-benchmarking.md` (NEW) describes the workspace approach:
  reuse-not-fork principle + per-asset_group generator inventory + bucket-suffix SSOT + parametric axes + bottleneck
  taxonomy + benchmark-runner architecture + per-stage thresholds.
- A workspace-wide benchmark-runner exists at the right SSOT location (TBD per D2 — likely
  `deployment-service/scripts/vm/launch-benchmark-vm.sh` + `e2e-testing/scripts/benchmark/run-pipeline-benchmark.sh`),
  runnable per `--asset-group` + `--archetype` + `--mode` + `--scale` flag.
- Per-asset*group + per-data_type mock generators exist in a single SSOT module
  (`unified-trading-library/synthetic_data/` candidate), parametric on B7 axes, schema-version-aware per A8, calling
  `ManifestWriter.record*\*` exactly as prod adapters do.
- Each downstream service (features / ml-training / ml-inference / strategy / execution-matching-engine /
  position-balance / risk) has a `scripts/benchmark/` entrypoint that consumes the SSOT generator surface + emits
  structured-event timing per stage (per D3 — additive instrumentation, no service-side forks).
- The benchmark-runner launches via `deployment-service/scripts/vm/launch-benchmark-vm.sh` per the workspace VM-launcher
  SSOT, with event-stream verification per `No fire-and-forget VM launches` HARD RULE.
- Benchmark buckets are provisioned per C1-C3, with the same internal structure as prod buckets (hive vocab + path
  templates + manifest layout). Reader/writer code paths are identical to prod modulo a single bucket-suffix env-var.
- Initial benchmark runs against representative mock data are complete; per-stage bottleneck report exists as a codex
  appendix or PM-archived artifact.
- Bottleneck remediation backlog exists as P0 / P1 / P2 items folded into appropriate epic plans
  (ml_and_features_master, strategy_and_dart_master, infrastructure_master).
- Per-stage thresholds + continuous-verification path are wired into the master plan's continuous-verification column
  for relevant Group F items (item 17 paper-trade smoke runtime, item 18 batch backtest runtime).
- Service-readiness checklist gates per the master plan's per-service matrix get a "benchmark-passed" sub-gate.
- **Reuse-not-fork audit passes**: zero benchmark-only forks of service business logic; zero `if benchmark_mode:`
  branches inside services; bucket-suffix is the only env-var diff between benchmark + prod runs of the same code path.

## Audit findings — 2026-05-10 audit pass

Three parallel `Explore` sub-agents fanned out across the workspace; consolidated findings below. Citations are
file:line references against the workspace as of 2026-05-10.

### Block A — Schema knowledge (ready ~80%, sufficient for cefi/defi; gaps in sports/prediction/macro)

**A1 — Per-data_type input schemas.** AVAILABILITY*AT_SEMANTICS dict at
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/availability_semantics.py:~20-30` covers cefi
(trades, ohlcv*\*, book_snapshot, liquidations, options_chain), defi (swap, fx_rate, liquidity, market_state, gas_fees,
lst_yields, vault_state), sports (FIXTURES, FIXTURE_LINEUPS, FIXTURE_EVENTS, FIXTURE_STATS, INJURIES, ODDS, WEATHER),
prediction (market_created_at). **No per-column Parquet schema declarations centralized** — generators must infer field
shapes from `InputReq.data_type` enums + availability_semantics tuples. **Gap**: tradfi tuple sparse in
availability_semantics; per-data_type Pydantic models would lift inference reliability from ~70% to 100%.

**A2 — Feature DAG SSOT.** **PRESENT and declarative** at
`unified-api-contracts/unified_api_contracts/canonical/domain/features/required_inputs.py:1-429`.
`FEATURE_REQUIRED_INPUTS` dict maps `feature_group → List[InputReq]` where `InputReq` is a dataclass with
`asset_group, data_type, available_at_rule, horizon, source`. Helpers:
`get_required_inputs / has_required_inputs / list_feature_groups / validate_required_inputs`. Coverage: features-onchain
(defi) ~20 groups full; features-delta-one (cefi/tradfi) ~25 groups full; features-sports ~5 groups partial;
features-prediction ~2 groups minimal; features-macro absent. Already consumed by
`LookaheadBiasError. assert_no_lookahead()` + deployment-api `data_status` denominator.

**A3 — ML model_family + strategy archetype contracts.** ML model_family registry **NOT FOUND** as a centralized SSOT.
Strategy archetypes live at `strategy-service/strategy_service/portfolio_allocator/archetypes.py` with input shapes
implied via feature_groups but no explicit per-archetype input dataclass. **Gap** — minor for benchmarking (we can drive
via feature_groups already in DAG) but explicit dataclasses would tighten contract.

**A4 — Execution-backtest contract.** **READY**. `execution-service/execution_service/matching_engine/engine.py:1-100+`
declares `MatchingEngine` abstraction with L0Matcher (sports TOB), L1Matcher (tradfi trades), L2Matcher (cefi
orderbook), AMMMatcher (defi swaps), BenchmarkMatcher (lend/stake/borrow). `MatchResult` fully typed (success, filled,
remaining, fill_price, ts, optional price_impact_bps, optional fee_amount). Deterministic backtest path.

**A5 — `available_at` stamping helpers.** **PRESENT** at
`unified-trading-library/unified_trading_library/availability_stamping.py:1-120+`: `stamp_available_at_lineups`
(kickoff-60min) / `stamp_available_at_event_time` (per-row source column) / `stamp_available_at_post_match`
(match_end_time fallback kickoff+120min) / `stamp_available_at_offset` (generic). Covers sports + cefi/defi/tradfi
tick + prediction.

**A6 — Honest-absence taxonomy.** **PRESENT** at
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py:166` — `EMPTY_CONFIRMED_REASONS`
closed set with 13+ typed reasons
(`EXPECTED_HOLIDAY / EXPECTED_WEEKEND / EXPECTED_PAUSED_LEAGUE / EXPECTED_PRE_SOURCE_COVERAGE_START / EXPECTED_PRE_GENESIS_CHAIN / EXPECTED_INSTRUMENT_NOT_LISTED / EXPECTED_DELISTED / EXPECTED_PARTIAL_HALF_DAY / EXPECTED_OUTSIDE_TRADING_HOURS / EXPECTED_OUTSIDE_TRANSFER_WINDOW / EXPECTED_PRE_SEASON / EXPECTED_POST_SEASON / EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE / EXPECTED_DEPRECATED_DATA_TYPE`).
4-state `capture_status` enum at lines 56-80 (`captured / empty_confirmed / attempted_failed / expected_unattempted`).

**A7 — Schema versioning.** **ABSENT**. No `schema_version` column / migration helpers / version-aware reader fallback.
Long-term gap; not a blocker for first benchmark run.

**A8 — Bottom line on schema knowledge.** Sufficient SSOT exists to automate **~80%** of synthetic-data generation today
for cefi/defi/tradfi via the FEATURE_REQUIRED_INPUTS DAG + AVAILABILITY_AT_SEMANTICS + EMPTY_CONFIRMED_REASONS +
MatchingEngine contract. Remaining 20% needs (a) per-data_type Parquet field shape codification for sports/prediction
and tradfi-tick, (b) ML model_family registry, (c) optional explicit strategy archetype input dataclasses.

### Block B — Reuse audit (existing harness + launcher + entrypoint surface)

**B1 — `e2e-testing/scripts/` harness inventory** — 3 harnesses identified:

| Harness                                                | Purpose                                                                               | Synth-input?                                                                     | Per-stage events?          | Currently green?                                                                                                                                                                            |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `e2e-testing/scripts/defi/colocated_engine.py`         | Co-located DeFi/CeFi/TradFi/Sports/Prediction engine; ring services in single process | Partial — `--mode batch` reads from GCS feature buckets; no synth-tick injection | No formal per-stage timing | **NO — import-rotted** since 2026-05-01 (`get_strategy_factories` removed from strategy-service.cli.handlers.batch_utils; uncaught due to QG gap; reference incident codified in CLAUDE.md) |
| `e2e-testing/scripts/sports/arb_rolling_backtest.py`   | Sports arbitrage signal + backtest over historical odds                               | Partial — fixture schedule synthesisable, odds read from sports bucket           | No                         | Unknown                                                                                                                                                                                     |
| `e2e-testing/scripts/sports/test_two_days_pipeline.py` | Sports 2-day pipeline smoke                                                           | Yes — constructs sample data in-memory                                           | No                         | Unknown                                                                                                                                                                                     |

Per CLAUDE.md "Peripheral Script Directories Under Primary-Consumer QG" (codified 2026-05-08), these directories are
**outside primary-service QG** — fix is wiring `e2e-testing/scripts/defi/` into
`strategy-service/scripts/quality-gates.sh`.

**B2 — `deployment-service/scripts/vm/` launcher inventory.** **73 launch-\*-vm.sh scripts**, mature pattern (tarball +
tarball-from-local + singleton-lock + watchdog-registered). Patterns covered: cefi-{mr,fwd,venue}-,
tradfi-{bf,fwd,recent,instr,phantom}-, sports-{ref-v3}, mtds-{asset-group}-, mdps-{asset-group}-, instr-backfill-,
features-sports-, manifest-consolidator-, vm-zombie-watchdog. Singleton-lock in `launch-sfi-forward-poll.sh` +
`launch-mtds-prediction-backfill-vm.sh`.

- **`VM_PREFIX_TO_BUCKET` dict** at `deployment-service/scripts/vm/vm_zombie_watchdog.py:113-224`. **NO `benchmark-`
  prefix**. Add-pattern is 1-line dict entry + new launcher + watchdog VM relaunch.
- **NO `launch-benchmark-vm.sh`** exists.

**B3 — Service benchmark entrypoints.**

| Service                          | `scripts/benchmark/` | `tests/perf/`                                                                                                 | Notes                                 |
| -------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| execution-service                | NO                   | YES (+ `execution_service/benchmark/` for matching-engine perf — comparison.py / metrics.py / html_report.py) | Matching-engine-specific, not generic |
| strategy-service                 | NO                   | YES                                                                                                           | Signal-gen throughput tests           |
| ml-training-service              | NO                   | YES                                                                                                           | Training latency tests                |
| ml-inference-service             | NO                   | YES                                                                                                           | Batch inference throughput            |
| market-data-processing-service   | NO                   | YES                                                                                                           | OHLC bar aggregation perf             |
| features-delta-one-service       | NO                   | YES                                                                                                           | Feature compute latency (test-only)   |
| features-sports-service          | NO                   | Embedded in launch scripts                                                                                    | No dedicated benchmark                |
| features-volatility-service      | NO                   | NO                                                                                                            | **GAP — zero perf coverage**          |
| features-onchain-service         | NO                   | Embedded in launch scripts                                                                                    | No dedicated benchmark                |
| features-tradfi-options-service  | NO                   | NO                                                                                                            | **GAP**                               |
| features-prediction-service      | NO                   | NO                                                                                                            | **GAP**                               |
| position-balance-monitor-service | NO                   | NO                                                                                                            | **GAP**                               |
| risk-and-exposure-service        | NO                   | YES                                                                                                           | Risk check latency (test-only)        |
| market-tick-data-service         | NO                   | YES                                                                                                           | Adapter throughput per venue          |
| instruments-service              | NO                   | NO                                                                                                            | Reference data only                   |

**Zero services have `scripts/benchmark/` entrypoint.** All perf testing confined to `tests/perf/` (pytest-based).
Volatility / onchain / tradfi-options / prediction features + position-balance + instruments have **zero perf
instrumentation**.

**B4-B9 — Synthetic-data generator inventory.** **ZERO generators across the workspace.** Workspace-wide grep returns no
UTL `synthetic_data/` package, no test-fixture generators producing tick / OHLCV / DeFi data / TradFi options-chain /
sports / prediction CLOB / order-fill streams. **This is the single biggest pre-benchmark blocker**: without
per-data*type generators that satisfy UAC schema contracts + call `ManifestWriter.record*\*` correctly, the whole
reuse-principle benchmark cannot run regardless of how good the harness reuse is.

### Block C — Bucket + path SSOT for non-prod runs

**C1 — Bucket-naming SSOT.** `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py:1-60` is
the single SSOT (per Tab 4 work `UTL@780a9575`). YAML SSOT at `deployment-service/configs/cloud-providers.yaml` mirrored
to PM. **`resolve_bucket_name(cloud, asset_group, kind)` does NOT accept `--bucket-suffix` today** (line 54). Fix is a
5-line function-signature extension + `${suffix}` template substitution in cloud-providers.yaml.

**C2 — UCI bucket flow.** **No `unified-cloud-interface` service exists** — bucket flow is direct UTL import. Sample:
`colocated_engine.py:47` imports `get_bucket_name` directly from UTL. Pattern: services pull bucket names via UTL
bucket_naming, not via UCI mediation. Implication: bucket-suffix flow needs only the UTL extension; no UCI work.

**C3 — Path templates / hive partitioning.** **NOT centralized for features readers**. Per `colocated_engine.py:771-788`
the `_FEATURE_BUCKETS` dict + path construction is per-service. Hive partition vocab **IS** centralized at MTDS
`raw_tick_hive.py` (write side), but **reader path templates are duplicated per features-\* service**. Implication: a
single bucket-suffix env-var won't redirect every reader without lifting reader paths to a shared module — this is a
Phase 0 prereq.

**C4 — `ManifestWriter` parity.** **SINGLE class** at
`unified-trading-library/unified_trading_library/manifest_writer.py`. **Zero forks** workspace-wide. Synthetic-data
generators MUST call `ManifestWriter.record_captured / record_empty / record_failed / record_expected_unattempted`
exactly as prod adapters do — same SSOT, no parallel writer.

**C5 — Manifest-bucket parity.** Inherits from C4 — single writer means generators producing parquets to benchmark
buckets will write manifest entries to the same bucket via the same code path; no separate "fake manifest" surface.

### Block D — End-to-end harness reuse + instrumentation

**D1 — Event registry.** **PRESENT** at `unified-trading-library/unified_trading_library/events/__init__.py:38-248` +
`events/event_types.py`. **150+ event types** declared. Per-stage events DEFINED for FEATURE_GROUP_PROCESSING_STARTED/
COMPLETED, MODEL_SAVING_STARTED/COMPLETED, FILL_COMPLETED, STRATEGY_SIGNAL_GENERATED, UPSTREAM_FETCH_STARTED/COMPLETED,
PERSISTENCE_STARTED/COMPLETED. **BUT** — workspace-wide grep shows these intermediate progress events are **NOT EMITTED
at scale** by service code today. Only STARTED + STOPPED are reliably emitted by `ServiceBootstrap`.

**D2 — Profiling tool wiring.** **ABSENT** in production code. No
`cProfile / py-spy / austin / scalene / pyinstrument / memray / memory_profiler / tracemalloc / OpenTelemetry / OTel / tracer / span`
imports. Test-only OTel skeleton at `unified-trading-library/tests/unit/test_tracing.py:1` (`_NoOpTracer`).

**D3 — VM event-stream contract.** **PRESENT** at `unified-trading-library/unified_trading_library/event_sink.py:53-126`
(`GcsEventSink`). Path: `events/{service}/{ts[:10]}/{instance_id}/hour={HH:02d}/{ts_us}_{seq}.jsonl`. One event per
file. STARTED/STOPPED required within 60s of launch / at exit; intermediate progress events **optional** by contract but
the only way to disambiguate "silently broken" from "no progress" per CLAUDE.md "No fire-and-forget VM launches".

**D4 — Existing benchmark / bottleneck work.**

- `execution-service/execution_service/benchmark/` (`comparison.py` 30KB, `enhanced_comparison.py` 14KB, `metrics.py`
  14KB, `html_report.py` 14KB) — matching-engine specific, not generic pipeline benchmark.
- `plans/archive/ml_training_feature_read_perf_2026_05_06.plan.md` — prior ml-training perf work (archive, status
  unverified).
- No codex doc on bottleneck analysis or per-stage profiling methodology.

**E1 — Parallelism patterns.** No multiprocessing / `concurrent.futures` / asyncio patterns workspace-wide in
features-\*. UTL `ParallelPerSymbolRunner` (per workspace memory 2026-05-07 — MTDS scope) is per-symbol fan-out for
Tardis adapter, not per-pipeline-stage profiling.

### Bottom line — readiness summary

| Block                            | Status                                        | Critical gap                                                                                          |
| -------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| A — Schema knowledge             | **~80% ready**                                | Per-data_type Parquet field shapes for sports/prediction/tradfi-tick + ML model_family registry       |
| B — Reuse harness inventory      | **Partial**                                   | colocated_engine.py rotted; zero `scripts/benchmark/` entrypoints across services                     |
| B — Synthetic generators         | **0% ready**                                  | **ZERO generators exist** — single biggest blocker                                                    |
| C — Bucket SSOT                  | **Strong foundation, needs 1-line extension** | `resolve_bucket_name()` lacks `--bucket-suffix`; reader path templates not centralized                |
| C — ManifestWriter parity        | **READY**                                     | None                                                                                                  |
| D — Event-stream instrumentation | **Defined but not emitted**                   | Per-stage progress events declared in registry but service code doesn't call them at shard boundaries |
| D — Profiling tools              | **0% ready**                                  | No cProfile / austin / memray / OTel anywhere in prod                                                 |

**Verdict.** The workspace is ~30-40% ready for "reuse harnesses + bucket-suffix" today. The four critical pre-cutover
prerequisites in priority order:

1. **P0 — Synthetic-data generator SSOT** (UTL `synthetic_data/` module; per-data*type generators driven by
   FEATURE_REQUIRED_INPUTS DAG + AVAILABILITY_AT_SEMANTICS; call `ManifestWriter.record*\*` for parity). ~2-3 AI-days.
2. **P0 — `colocated_engine.py` import-rot fix + e2e-testing-into-primary-service-QG wiring** (per CLAUDE.md "Peripheral
   Script Directories Under Primary-Consumer QG" rule, codified 2026-05-08, not yet implemented). ~0.5 AI-day.
3. **P1 — `resolve_bucket_name()` `--bucket-suffix` + cloud-providers.yaml `${suffix}` templating + `benchmark-` prefix
   in `VM_PREFIX_TO_BUCKET` + `launch-benchmark-vm.sh`**. ~1 AI-day.
4. **P1 — Per-stage progress event emission in MTDS / MDPS / features-\* / ml-\* / strategy / execution loops**
   (existing event types, just need `log_event()` calls at shard boundaries). ~1 AI-day.

After P0+P1: a benchmark VM launches via standard `deployment-service/scripts/vm/launch-benchmark-vm.sh`, mounts
synthetic data via the SSOT generators into a `*-benchmark-*` bucket, runs the existing colocated_engine end-to-end
harness against it, and emits per-stage progress events parseable into a bottleneck report. Total pre-cutover
prerequisite scope: ~4-5 AI-days; remainder of plan ~3 AI-days for run + report + codex SSOT.

## Operator notes / answers

- **2026-05-10 — operator direction (this doc's framing)**: "Use `e2e-testing`, `deployment-service`, and the service
  repos — use what's there when we can. Of course not the same buckets as prod, but same bucket structure. As much of
  the same code paths as possible." Codified in this doc's `## Guiding principle — reuse, don't fork` section as the
  primary constraint on benchmark architecture.

Operator clarifications likely needed during iteration:

- Realism-axis target — do we need axis-1/2/3 (cheap parametric for bottleneck-only), axis-4 (calibrated dynamics for
  algorithmic correctness), or both?
- Pre-cutover priority ordering — which stage's benchmark is most important (features vs ML vs strategy vs
  execution-backtest)?
- VM-shape budget — per-stage cost ceiling.
- Continuous-verification cadence post-cutover — daily / weekly / per-PR.
- Benchmark-bucket lifecycle — ephemeral per-run, persistent per-asset_group, or per-experiment UUID-suffixed.
- Synthetic-vs-real-data trade-off — when real backfills land per asset_group, do we switch the benchmark to real data,
  or keep synthetic for reproducibility?

## Iteration log

| Date       | Author                  | Change                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ---------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-05-08 | ikenna + main agent     | Initial draft created (later lost — uncommitted)                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-05-10 | ikenna + main agent     | Recreated with `## Guiding principle — reuse, don't fork` section per operator direction; reframed Block B as "Reuse audit"; added Block C (bucket+path SSOT for non-prod runs); added Block D (end-to-end harness reuse); reuse-not-fork audit added to "What 'answered' looks like"                                                                                                                                                                                                |
| 2026-05-10 | main agent (audit pass) | Audit pass complete — 3 parallel `Explore` sub-agents fanned out across schema knowledge / reuse surface / instrumentation. Findings folded into `## Audit findings` section with file:line citations. Headline: ~30-40% reuse-ready today; 4 prereqs identified (synthetic generators + colocated_engine rot fix + bucket-suffix + per-stage event emission); active plan spawned at `plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`; status flipped to `plan-spawned` |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TBD (likely `plans/active/mock_data_pipeline_benchmarking_<date>.md`, possibly with sub-plan
  fan-out per stage)
- **Plan type**: `code` (generators + harness extensions) + `infra` (benchmark VM launcher + non-prod bucket
  provisioning + result storage) + `business` (threshold-setting + bottleneck remediation prioritization)
- **Owner side**: likely both — Ikenna for threshold-setting + bottleneck remediation prioritization + VM-shape
  decisions, Harsh for generator implementation + harness extensions + benchmark-runner script + bucket SSOT wiring +
  result-aggregation pipeline
- **Codex SSOTs touched**:
  - `/codex/05-infrastructure/synthetic-data-benchmarking.md` — NEW — workspace SSOT (reuse principle + generator
    architecture + bucket-suffix SSOT + bottleneck taxonomy + benchmark-runner)
  - `/codex/02-data/contracts-scope-and-layout.md` — UPDATE — link to per-data_type generator inventory
  - `/codex/05-infrastructure/runtime-tiers-and-deployment.md` — UPDATE — benchmark-VM tier + per-stage shape
    recommendations
  - `/codex/05-infrastructure/vm-tarball-deployment.md` — UPDATE — benchmark-VM launcher pattern
  - `/codex/05-infrastructure/launcher-script-ssot.md` — UPDATE — `launch-benchmark-vm.sh` registration
  - `/codex/04-architecture/batch-live-architecture.md` — UPDATE — benchmark-mode-as-batch-mode-with-synthetic-input
    framing
  - `/codex/06-coding-standards/quality-gates.md` — UPDATE — per-service benchmark entrypoint as a soft-gate
- **Cross-plan dependencies**:
  - `plans/active/master_to_live_defi_2026_05_23.md` — Group F items 17 + 18 reference benchmark thresholds for sign-off
  - `plans/epics/ml_and_features_master_2026_05_07.md` — features + ML benchmarking sits under this epic
  - `plans/epics/strategy_and_dart_master_2026_05_07.md` — strategy + execution-backtest benchmarking sits under this
    epic
  - `plans/epics/infrastructure_master_2026_05_07.md` — VM launcher + benchmark-runner + non-prod bucket provisioning
    sits under this epic
  - `plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md` — live-pipeline shape constrains benchmark target
    topology
  - `plans/active/features_repo_consolidation_2026_05_08.md` — features consolidation is a prerequisite for unified
    features benchmark surface
  - `plans/questions/batch_live_design_symmetry_2026_05_08.md` — reuse principle is the operational expression of the
    symmetry SSOT
  - `plans/questions/topology_features_strategy_ml_execution_2026_05_08.md` — topology decisions become benchmark
    targets
  - `plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md` — paper-mode benchmark variant
  - `plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md` — credential-light path
  - `plans/questions/disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md` — circuit-breaker latency as
    benchmark stage
  - `plans/questions/defi_readiness_catalogue_2026_05_08.md` — DeFi data catalogue feeds generator gap-list
- **Estimated scope**: Medium — ~5-8 AI-days for generator gap-fill + harness extensions + bucket SSOT wiring +
  benchmark-runner script + initial run + bottleneck report + codex SSOT. Breakdown: Block B (reuse audit + generators)
  ~2-3d, Block C (bucket SSOT) ~1d, Block D (harness extensions + launcher) ~1-2d, Block E (taxonomy SSOT) ~0.5d, Block
  F (entrypoint + run) ~1d, Codex docs + cross-plan threading ~0.5-1d.

## Plan extraction record

- **Plan path**:
  [`plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`](../active/mock_data_pipeline_benchmarking_2026_05_10.md)
- **Spawned**: 2026-05-10 by main agent following audit pass
- **Plan shape**: 5 phases — Phase 0 prereq gap-fill (synthetic generators + colocated_engine rot + bucket-suffix +
  per-stage events), Phase 1 benchmark VM + buckets, Phase 2 benchmark runner, Phase 3 initial run + bottleneck report,
  Phase 4 codex SSOT alignment + master-plan continuous-verification wiring, Phase 5 bottleneck-remediation backlog
  dispatch into epics
- **Codex updates committed**: TBD (Phase 4 of plan — `/codex/05-infrastructure/synthetic-data-benchmarking.md` NEW + 6
  codex updates per plan-shape decisions block)
- **Question doc closes (status: `closed`) when**: Phase 4 of the active plan ships (codex SSOT lands + master-plan
  continuous-verification column wired) AND a real synthetic-data benchmark run has produced a per-stage bottleneck
  report against representative scale.
