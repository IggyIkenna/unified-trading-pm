---
doc_type: codex-ssot
title: "Deployment Clusters: Live vs Batch (SSOT)"
summary:
  Canonical taxonomy of deployment clusters — a live cluster (many different services co-running) vs a batch cluster
  (the same service ×N shards in parallel); per-tier shard atoms (data / decision / ML / execution), daily shards as the
  universal replay axis, tarball vs Cloud Build mechanisms, and the per-VM shard-isolation + write-gate concurrency
  invariants.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [deployment, backfill, manifest, mtds, live-trading]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/05-infrastructure/deployment-ui-architecture.md,
  ]
created: 2026-05-06
authoritative_for:
  [live vs batch deployment cluster taxonomy, per-cluster-type sizing + deployment mechanism (tarball vs Cloud Build)]
referenced_by:
  [
    /codex/02-data/prediction-schema-paths.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/04-architecture/features-service-architecture.md,
    /codex/04-architecture/instruments-live-architecture.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/deployment-ui-architecture.md,
    /codex/06-coding-standards/feature-service-pattern.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Deployment Clusters: Live vs Batch (SSOT)

<!-- MULTI_AXIS_CORRECTION_2026_05_06 -->

> **Multi-axis correction (2026-05-06)** — per
> [`data_status_multi_axis_shard_propagation_2026_05_06.plan.md`](../../plans/archive/data_status_multi_axis_shard_propagation_2026_05_06.plan.md):
> a column belongs in the **shard atom** ONLY IF it earns it via failure isolation OR memory ceiling OR concurrency
> orthogonality. Otherwise it's a **display axis** (row-level column for filter/group, NOT a manifest row per value).
> This refines the per-asset-group shard atoms below:
>
> - **Sports**: shard atom = `(asset_group=sports, venue/source, data_type, league_id, day)`. **`fixture_id` is a
>   row-level column in the parquet, NOT a shard axis** — `(league_id, day)` already bounds the per-day fixture set;
>   per-fixture detail at drill-down comes from reading the parquet, not from a separate manifest row. Avoids 10×
>   manifest inflation.
> - **Prediction**: shard atom =
>   `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`.
>   **`market_id` is a row-level column in the parquet, NOT a shard axis** — same rationale. HOURLY (24/day) + DAILY +
>   ELECTION groups all roll up to one manifest row per `(canonical_question_group, day)`; per-market detail at
>   drill-down from parquet.
> - **CeFi options/futures bundles**: bundle root IS a shard axis (memory + concurrency); per-symbol within bundle is
>   parquet row (cluster validation enforces all expected per-bundle clusters covered).
> - **DeFi `chain`** IS a shard axis (independent RPC/subgraph endpoints + failure isolation).
> - **ML / strategy / execution**: new `job_id` v7 manifest column for experiment-keyed services. Same
>   `(model_family, training_period, job_id)` shard atom for ML training; `(strategy_id, job_id)` for strategy;
>   `(strategy_id, instruction_type, job_id)` for execution. Re-running same configs = new `job_id` (audit trail of
>   every experiment version).
> - **instrument_type for instruments-service**: NOT a shard axis (Databento + TARDIS bulk-fetch all instrument_types
>   per venue in one call). Display axis only — row column for filter/group.

**Purpose**: define the canonical taxonomy of how the unified trading system gets deployed — what a "deployment cluster"
is, the live vs batch split, the per-tier shard semantics that drive cluster sizing, and the deployment mechanisms
(tarball + Cloud Build) supported via the deployment-UI.

**Per workspace CLAUDE.md `§ Batch = Live: Unified Pipeline Architecture`**: live and batch use the same code path +
same component interactions + same data contracts. Only the SOURCE serving a given `(asset_group, data_type)` may
differ + only the EXECUTION FILL source differs (matching engine vs real venue). Cluster topology is the operational
difference; data and timing semantics are identical.

---

## Two cluster types

### Live deployment cluster

**Definition**: multiple different services co-located + co-running. The cluster is the production trading pipeline
serving real-time decisions.

Services in a live cluster:

- **Data tier**: instruments-service (reference data refresh), market-tick-data-service (live tick capture),
  market-data-processing-service (live candle aggregation), features-\* (live feature compute).
- **Decision tier**: strategy-service (live signal generation), risk-and-exposure-service (live exposure tracking),
  position-balance-monitor-service (live position state).
- **Execution tier**: execution-service (live order routing + fill matching).
- **ML tier**: ml-inference-service (live prediction).

All running concurrently. Each service handles its own work-stream independently; failures in one service don't kill
others (per `04-architecture/shard-level-failure-isolation.md`).

**Cluster sizing**: ONE replica per service (or N replicas for horizontal scale). Each replica handles the live request
stream.

**Shards in a live cluster**: the natural unit of work the service processes per request — one fixture, one
instrument-day, one strategy-decision. Daily shards are the universal axis for replay.

### Batch deployment cluster

**Definition**: the SAME service running N times concurrently for N different shards in parallel. The cluster is a
horizontal-scale backfill or backtest job.

A batch cluster is single-service:

- **Data backfill cluster** (e.g. MTDS): N VMs each processing a different (venue, date-range) shard.
- **MDPS reprocess cluster**: N VMs each processing a different (venue, data_type, date-range) shard.
- **Backtest cluster** (strategy / ML / execution): N VMs each running a different (config_id, day-range) shard.

All running concurrently. Per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`) prevents the workers
from clobbering each other's manifest writes.

**Cluster sizing**: N is set per the parallelism the source supports (Databento rate limit, Tardis venue throughput,
Polymarket REST quota, etc.) and the total work-units to backfill.

**Shards in a batch cluster**: the work-unit assigned to each VM. Daily shards are the universal axis: every backfill
picks start_date + end_date + shard_dimensions. Per-tier shard semantics defined below.

---

## Per-tier shard semantics

The shard atom = the manifest row key for the service tier. Data-pipeline tier and decision tier have different shard
shapes; daily granularity is the common axis so any backtest or backfill can pick start/end ranges.

### Data-pipeline tier (instruments-service, MTDS, MDPS, features-\*)

Shard atom = full v6 row key per asset_group:

| Asset group              | Shard atom                                                                                                                                                                                                                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CeFi spot/perp**       | `(asset_group, venue, data_type, instrument_type, instrument_id, day)`                                                                                                                                                                                                                      |
| **CeFi options/futures** | `(asset_group, venue, data_type, options_chain\|futures_chain, root, day)` + `quote_asset` + `margin_type` for DERIBIT inverse vs linear                                                                                                                                                    |
| **TradFi futures**       | `(asset_group=tradfi, venue, data_type, instrument_type, root, day)`                                                                                                                                                                                                                        |
| **TradFi ETFs**          | `(asset_group=tradfi, venue, data_type, instrument_type, instrument_id, day)`                                                                                                                                                                                                               |
| **TradFi options**       | `(asset_group=tradfi, venue, data_type, options_chain, root, day)` — ES.OPT 11-cluster + `combo_type` + `leg_weights`                                                                                                                                                                       |
| **DeFi**                 | `(asset_group=defi, chain, venue/protocol, data_type, instrument_id_or_protocol_id, day)`                                                                                                                                                                                                   |
| **Sports**               | `(asset_group=sports, source, data_type, league_id, day)` for ALL sports data_types (ODDS*\*, FIXTURE*\*, INJURIES, STANDINGS, LEAGUES, TEAMS, etc.) — `fixture_id` is row-level column NOT shard axis (per Q1 resolution; cluster validation enforces per-fixture coverage within parquet) |
| **Prediction**           | `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` — `market_id` is row-level column NOT shard axis (per Q1 resolution; cluster_extractor=market_id validates per-canonical-question coverage)                                 |

**What "a shard" means in the data-pipeline tier**: one day's worth of one (instrument OR root OR fixture OR
canonical_question_group) for one (data_type / timeframe / feature_group) for one venue/chain. Daily granularity is
universal — backfills pick `start_date` + `end_date` + filter by `(asset_group, venue, data_type, ...)`.

### Decision tier (strategy-service, position-balance-monitor, risk-and-exposure-service)

Shard atom: `(asset_group, strategy_id\|client_id, day, [config_id])`.

**What "a shard" means in the decision tier**: one day's worth of one strategy or client running with one config. For
backtest clusters, `config_id` distinguishes parameter sweeps — each VM runs one (strategy, config) combo over a date
range.

### ML tier (ml-training-service, ml-inference-service)

Shard atom:

- **Training**: `(asset_group, model_family, training_period, [config_id])` — walk-forward window per model family.
- **Inference**: `(asset_group, model_family, day, [config_id])` — daily inference shard.

**What "a shard" means in the ML tier**: training shards are walk-forward windows (e.g. "2024-01" or "2024" depending on
cadence); inference shards are daily, one per model family. Daily inference shards let backtest-mode replay pick
start/end ranges.

### Execution tier (execution-service)

Shard atom: `(asset_group, strategy_id, venue, instruction_type, day, [config_id])`.

**What "a shard" means in the execution tier**: one day's worth of execution decisions for one (strategy, venue,
instruction_type). Live cluster + matching-engine cluster shard identically; only the fill source differs (real venue vs
matching engine).

---

## Daily shards as the universal axis

Every tier shards by date, so any backtest or backfill can pick `start_date` + `end_date`. This is non-negotiable per
workspace CLAUDE.md `§ Batch = Live` — backtest mode must replay a date range exactly the way live mode would have
processed it.

Cross-tier consequence:

- A backtest cluster spanning all tiers (instruments → MTDS → MDPS → features → strategy → ML → execution) is N
  data-tier batch clusters (one per service) sequenced in topological order, then M decision/ML/execution batch clusters
  (one per `(strategy, config)`) running over the same date range.
- A live cluster spanning all tiers is ONE replica per service (or N for horizontal scale), processing the live stream
  concurrently.

The data + timing semantics are identical between the two; only the deployment topology and execution-fill source
differ.

---

## Deployment mechanisms

Both mechanisms below are equally valid; both will be selectable via the deployment-UI eventually. **All
deployment-related scripts live in `deployment-service`, NOT in the individual services they deploy.** This is
non-negotiable — services must not own their own VM launchers, tarball builders, or Cloud Build configs.

### Mechanism 1: Tarball-based VM deployment (current)

**Flow**:

1. `bash deployment-service/scripts/vm/create-code-tarballs.sh <flag>` builds tarballs for the affected repos (flags:
   `--all` for any multi-repo feature; `--asset-group SPORTS|CEFI|TRADFI|DEFI|PREDICTION` for an asset_group's pipeline;
   `--include <repo>` for one-off addition; bare invocation = CORE only — UAC/UTL/MTDS/deployment-service).
2. Tarballs land at `gs://deployment-scripts-{pid}/code/{repo}-code.tar.gz`.
3. VM launcher (`bash deployment-service/scripts/vm/launch-{...}.sh`) creates a GCE VM with `setup-data-pipeline-vm.sh`
   as boot script.
4. Boot script pulls tarballs from `gs://deployment-scripts-{pid}/code/`, sets up `.venv`, runs the service entrypoint
   with shard-specific env vars.

**Shard parameterisation**: launcher passes `VM_ASSET_GROUP` / `VM_NAME` / `MTDS_ASSET_GROUP` / etc. + the date range /
venue list / shard filters as env vars to the boot script. Service reads them and processes the assigned shard.

**SSOT for tarball deployment**: [`05-infrastructure/vm-tarball-deployment.md`](./vm-tarball-deployment.md) (canonical
recipe + flags + post-edit refresh discipline).

**Pros**: fast iteration (push code, refresh tarball, launch VM in seconds — no Docker build); low cloud-bill overhead.

**Cons**: tarballs are mutable (post-launch refresh changes future VM behaviour); no immutable deployment audit trail.

### Mechanism 2: Cloud Build (immutable container deployment)

**Flow**:

1. `git push` to `live-defi-rollout` triggers Cloud Build per repo.
2. Cloud Build runs the repo's `Dockerfile` (using
   `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/{pid}/unified-trading-library/unified-trading-library:latest`),
   pushes to Artifact Registry.
3. deployment-service (via deployment-UI) launches GCE VM (or Cloud Run job for non-stateful services) referencing the
   AR image digest.

**Shard parameterisation**: same env-var mechanism as tarball, but the service code is baked into the immutable image at
Cloud Build time — no post-launch tarball-refresh drift.

**Pros**: immutable deployments + audit trail (every run references a specific image digest); Cloud Run alternative for
some services; built-in rollback (deploy older digest).

**Cons**: slower iteration (Cloud Build takes minutes); higher container-storage cost (every commit produces a new
image).

**SSOT for Cloud Build deployment**: under construction. References:

- [`05-infrastructure/cicd-setup.md`](./cicd-setup.md) (Cloud Build trigger configuration per repo).
- [`05-infrastructure/artifact-registry-setup.md`](./artifact-registry-setup.md) (per-repo AR layout).

### Both mechanisms eventually surface in deployment-UI

The deployment-UI's deployment-flow tab will offer both mechanisms as options for any deployment cluster:

- **Tarball mechanism**: useful for active development + iterative debugging — push + refresh tarball + relaunch.
- **Cloud Build mechanism**: useful for production deployments + audit-trail requirements — immutable image references +
  rollback.

Both mechanisms produce identical runtime behaviour at the service level (same code, same env vars, same shard
parameterisation). The deployment-UI's deployment-flow surfaces the cluster type (live vs batch), the shard
parameterisation, the source mechanism (tarball / Cloud Build), and the per-service health + event stream.

---

## Concurrency invariants (apply to both cluster types + both mechanisms)

These are non-negotiable across live and batch clusters and across tarball and Cloud Build deployments:

1. **Per-VM shard isolation** for batch clusters with N > 1 VMs writing the same manifest: `VM_NAME=<unique>` +
   `MANIFEST_PER_VM_SHARDS=true`. UTL guard `MultiWorkerWithoutShardIsolationError`. QG STEP 5.66 enforces.
2. **Manifest aggregation** via the `manifest_consolidator` daemon (Cloud Scheduler `*/1 * * * *`): merges per-VM shards
   under `_index/per_vm/{vm_name}.parquet` into the canonical `_index/availability_index.parquet` with last-writer-wins
   on identical row_key. Reader fallback merges per-VM shards when canonical blob is older than
   `MANIFEST_CONSOLIDATED_STALENESS_SEC` (default 120s).
3. **Structured event publication**: every service emits structured events to
   `gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl`. Required: `STARTED` within 60s
   of launch, per-shard progress events, `STOPPED` or `FAILED` at exit. Per workspace CLAUDE.md
   `§ No fire-and-forget VM launches`.
4. **Shard-level failure isolation**: a failed shard MUST NOT kill other shards in the same batch (or other services in
   the same live cluster). Per `04-architecture/shard-level-failure-isolation.md`.
5. **Write-gate quartet at `record_captured`**: row count + NaN ratio + schema + cluster coverage. Failure of any pillar
   → `record_failed(<typed_reason>)` instead of writing the parquet. Per `06-coding-standards/validation-and-errors.md`
   §2.
6. **Four-category empty-output decision** (A/B/C/D): at every per-shard adapter. Per
   `06-coding-standards/validation-and-errors.md` §1.
7. **`available_at` per-row write-time** equal to live-pipeline-arrival: every row in every shard's parquet carries
   `available_at`. Per workspace CLAUDE.md `§ available_at`.

The data-status panel in the deployment-UI reads the canonical manifest + per-VM shard fallback, so it reflects honest
cluster state regardless of which mechanism deployed the cluster or which type the cluster is (live vs batch).

---

## Active migrations relevant to deployment clusters

- **Sports per-fixture row-level migration** (writegate Phase 2.B; Q1 resolution): sports per-fixture data_types stay
  sharded at `(league_id, day)` granularity but expose `fixture_id` as a row-level column with cluster validation
  enforcing per-fixture coverage. Reader paths in MDPS sports adapter, features-sports input pipeline, deployment-UI
  drill-down all migrating in lockstep.
- **Polymarket canonical_question_group migration** (predictions Plan A): MTDS prediction adapter migrating shard atom
  from `data_type=<base_asset>` to `data_type=prediction_canonical_question_group`. GCS reconciler in batch cluster
  splits per-base_asset parquets into per-canonical-group parquets.
- **`category=` → `asset_group=` GCS migration** (writegate Phase 3.A + Plan C): per-asset_group migration scripts;
  batch clusters run the rebuild scripts; legacy `category=` fallback reader deleted only after 100% migration verified.
- **Cluster-validation rollout** (writegate Phase 1A + 2.B): `record_captured` mandatory `expected_root_clusters` +
  `cluster_extractor` for bundled data_types; QG STEP 5.64 enforces statically; both live and batch clusters get the
  runtime guard.

---

## Cross-references

- **Manifest semantics + per-service shard dimension matrix**:
  [`02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
- **deployment-service shard alignment + GCS path templates**:
  [`deployment-service/docs/SHARDING_AND_DATA_ALIGNMENT.md`](../../../deployment-service/docs/SHARDING_AND_DATA_ALIGNMENT.md)
- **Shard-level failure isolation**:
  [`04-architecture/shard-level-failure-isolation.md`](/codex/04-architecture/shard-level-failure-isolation.md)
- **4-category empty-output + cluster validation + 4-pillar write-gate (single SSOT)**:
  [`06-coding-standards/validation-and-errors.md`](/codex/06-coding-standards/validation-and-errors.md)
- **Tarball deployment recipe**: [`05-infrastructure/vm-tarball-deployment.md`](./vm-tarball-deployment.md)
- **Cloud Build CI/CD setup**: [`05-infrastructure/cicd-setup.md`](./cicd-setup.md)
- **Runtime tiers + deployment**:
  [`05-infrastructure/runtime-tiers-and-deployment.md`](./runtime-tiers-and-deployment.md)
- **Active plans**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md),
  [`plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](../../plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md)
