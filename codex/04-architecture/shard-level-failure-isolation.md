---
doc_type: codex-ssot
title: Shard-Level Failure Isolation (SSOT)
summary:
  A failed shard must not kill the batch — log + record_failed + continue (no raise in per-shard loops); covers the
  per-tier shard-atom matrix, the 4-pillar write-gate, and references the 4-category (honest-absence /
  upstream-timestamp-bias / malformed-field / zero-activity-bar) empty-output decision tree — corrected 2026-07-12 (was
  3-category, finding 346); taxonomy SSOT is 06-coding-standards/validation-and-errors.md.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    deployment-ui,
    execution-service,
    instruments-service,
    strategy-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [manifest, data-correctness, backfill, data-status, ssot, retry, error-classification, venue-error-map, qg-lint]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/deployment-clusters-live-vs-batch.md,
    /codex/06-coding-standards/validation-and-errors.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-03-27
authoritative_for:
  [
    shard-level failure isolation rule (no-raise per-shard loop + record_failed continuation),
    classify_venue_error unclassified-default retry_safe convention,
  ]
referenced_by:
  [
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/prediction-schema-paths.md,
    /codex/02-data/shard-granularity-cefi.md,
    /codex/02-data/sports-adapter-dependency-order.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/04-architecture/service-contract-audit-template.md,
    /codex/04-architecture/service-framework.md,
    /codex/05-infrastructure/deployment-clusters-live-vs-batch.md,
  ]
owner:
last_reviewed: 2026-07-25
code_refs:
  [
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/__init__.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain/glassnode.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain/helius_solana.py,
    unified-trading-pm/scripts/quality-gates-base/base-service.sh,
  ]
---

# Shard-Level Failure Isolation (SSOT)

<!-- EMPTY_OUTPUT_CATEGORY_CORRECTION_2026_07_12 -->

> **Category-count correction (2026-07-12, finding 346)** — this doc previously claimed a **3-category** empty-output
> decision tree (was: honest-absence / upstream-timestamp-bias / malformed-field only, matching
> `authoritative_for: [... three-category empty-output decision tree]`). The taxonomy SSOT is
> [`06-coding-standards/validation-and-errors.md`](/codex/06-coding-standards/validation-and-errors.md) §1, which
> documents **4 categories** (adds **D. zero-activity-bar**, catalog-aware, operator directive 2026-05-07). Corrected
> below; this doc's `authoritative_for` no longer claims the decision-tree count — that authority lives solely in
> `validation-and-errors.md`.

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

## Rule

**A failed shard MUST NOT kill other shards in the same batch (or other services in the same live cluster).**

Shards are the isolation boundary. When processing fails for one shard, the service:

1. Logs the error with full details (shard atom + correlation ID + typed error reason) to the structured event stream.
2. Records the failure to the manifest via
   `ManifestWriter.record_failed(row_key, error=<typed_error>, attempted_at=<now>)` so the data-status panel surfaces it
   (NOT silently dropped).
3. Continues processing remaining shards in the batch (batch cluster) or remaining requests in the service (live
   cluster).
4. Reports partial success at the end with per-shard pass/fail breakdown.

A **partially complete shard** is killed at the write boundary — `ManifestWriter.record_captured` runs the 4-pillar
write-gate (see below); any pillar failure → `record_failed` instead of writing the parquet. NO partial parquets land on
disk. NO silent NaN placeholder rows.

**The 4-pillar write-gate** (per workspace CLAUDE.md `§ Validation gates per record_captured`):

| Pillar                                            | Gate                                                                                                                                                                                         | Failure mode                                                         |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **1. Row count > 0**                              | Mandatory unless source response was legitimately empty (then `record_empty`, not `record_captured`).                                                                                        | `record_failed(EmptyAfterFilterError)`.                              |
| **2. NaN ratio per column < threshold**           | Per-feature-group thresholds in UAC `nan_thresholds.NAN_RATIO_THRESHOLDS`; lifted from per-service inline in Plan B.                                                                         | `record_failed(NanRatioExceededError(column, observed, threshold))`. |
| **3. Schema matches contract**                    | Required columns + types match UAC schema declaration. Existing `ParquetSchemaEnforcer`.                                                                                                     | `record_failed(SchemaMismatchError)`.                                |
| **4. Cluster coverage ≥ expected** (BUNDLED only) | For `data_type ∈ BUNDLED_DATA_TYPES`, `expected_root_clusters` + `cluster_extractor` MANDATORY (UTL guard raises `MissingClusterValidationError` if absent; QG STEP 5.64 statically checks). | `record_failed(ClusterCoverageError(missing, observed))`.            |

**Empty result decision tree (4 categories — was 3 prior to 2026-07-12 finding 346, NO silent NaN placeholders; taxonomy
SSOT is [`06-coding-standards/validation-and-errors.md`](/codex/06-coding-standards/validation-and-errors.md) §1, NOT
this doc)**: every empty-result condition resolves to one of:

- **A. Honest absence** — source returned 0 ticks for the requested window → `record_empty(row_key, attempted_at)`.
- **B. Upstream timestamp bias** — source returned ticks; ALL fall outside the requested day after `interval_idx` filter
  → `record_failed(UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks))`. UPSTREAM bug — partition
  mislabeled at MTDS write-time, source replay covered wrong window, OR clock-skew. Paired upstream MTDS
  partitioner-validation fix at `raw_tick_hive.py`.
- **C. Mid-process malformed fields** — rows in window but downstream calc dropped due to NaN/malformed source fields →
  `record_failed(MalformedTickFieldError(field, n_dropped, sample_values))`. Data-quality bug; sample values surface for
  triage.
- **D. Zero-activity bar** (was missing from this doc; per validation-and-errors.md §1) — source returned 0 BUT
  instruments-service catalog says the instrument was ALIVE on the day AND day falls within venue market hours →
  `record_captured` with carry-forward zero-activity bars (O=H=L=C=prior_LTP, volume=0, trade_count=0). Distinct from
  path A: captures "tradeable but illiquid," not "missing." See `validation-and-errors.md` §1 for the full reason
  taxonomy + catalog-aware write-gate detail.

The `_create_empty_output()` placeholder method is BANNED from `base_adapter` and equivalents (writegate Phase 2.A
deletes it across MDPS' 37 callsites).

---

## Shard atom — depends on the deployment cluster type

The shard atom = the v7 manifest row key for the service. The shard atom MUST be identical across writer atomicity
boundary, manifest row key, data-status display rollup, downstream service pre-flight gate, and deployment-ui
drill-down. Drift between any two = silent correctness bug.

**Two cluster types** (see
[`05-infrastructure/deployment-clusters-live-vs-batch.md`](/codex/05-infrastructure/deployment-clusters-live-vs-batch.md)
for full taxonomy):

- **Live deployment cluster** = multiple different services co-located + co-running (instruments-service + MTDS + MDPS +
  features-\* + strategy + execution all online concurrently). Shards = the natural unit of work the service processes
  per request (e.g. one fixture, one instrument-day, one strategy-decision).
- **Batch deployment cluster** = the SAME service running N times concurrently for N different shards (parallel
  processing of historical data). Shards = the work-units we partition the backfill into.

Live and batch are operationally different (one cluster type co-locates services; the other parallelises a single
service) but they produce IDENTICAL outputs at the shard atom level. Per workspace CLAUDE.md `§ Live = batch`, the data,
fields, and timing semantics are identical between live and batch — only the source serving a given
`(asset_group, data_type)` may differ. Daily shards are the common axis: every tier shards by date, so we can pick
start/end ranges for any backtest or backfill.

### Shard semantics by service tier

The shard atom shape depends on which tier of the pipeline the service belongs to:

| Tier                   | Services                                                              | Shard atom                                                                                                                                                                                                                                                                              | What "a shard" means                                                                                                                                                                    |
| ---------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data-pipeline tier** | instruments-service, MTDS, MDPS, features-\*                          | `(asset_group, [chain], venue, data_type, [instrument_type], [instrument_id\|root\|fixture_id\|canonical_question_group], [timeframe], [feature_group], [league_id], day)` — full v7 row key per asset_group, see `02-data/availability-manifest-and-data-status.md` per-service matrix | One day's worth of one (instrument OR root OR fixture OR canonical-question-group) for one (data_type / timeframe / feature_group) for one venue/chain. Daily granularity is universal. |
| **Decision tier**      | strategy-service, position-balance-monitor, risk-and-exposure-service | `(asset_group, strategy_id\|client_id, day, [config_id])`                                                                                                                                                                                                                               | One day's worth of one strategy or client running with one config. For backtests, `config_id` distinguishes parameter sweeps; daily shards let backtests pick start/end ranges.         |
| **ML tier**            | ml-training-service, ml-inference-service                             | `(asset_group, model_family, training_period\|day, [config_id])`                                                                                                                                                                                                                        | Training: one walk-forward window for one model family. Inference: one day's worth of inference for one model family. Daily inference shards for backtest-mode replay.                  |
| **Execution tier**     | execution-service                                                     | `(asset_group, strategy_id, venue, instruction_type, day, [config_id])`                                                                                                                                                                                                                 | One day's worth of execution decisions for one (strategy, venue, instruction_type). Live cluster + matching-engine cluster both shard identically; only the fill source differs.        |

Per the workspace CLAUDE.md `Per-asset-group shard-key matrix`, the data-pipeline tier expands to:

| Asset group              | Shard atom (data-pipeline tier)                                                                                                                                           | Bundling notes                                                                                                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CeFi spot/perp**       | `(asset_group, venue, data_type, instrument_type, instrument_id, day)`                                                                                                    | per-instrument                                                                                                                                                                   |
| **CeFi options/futures** | `(asset_group, venue, data_type, options_chain\|futures_chain, root, day)` + `quote_asset` + `margin_type` for DERIBIT inverse vs linear                                  | bundled by root with cluster validation MANDATORY                                                                                                                                |
| **TradFi futures**       | `(asset_group=tradfi, venue, data_type, instrument_type, root, day)`                                                                                                      | bundled, non-trading days pre-skipped → `empty_confirmed`                                                                                                                        |
| **TradFi ETFs**          | `(asset_group=tradfi, venue, data_type, instrument_type, instrument_id, day)`                                                                                             | per-instrument (IBIT, ETHA on NASDAQ)                                                                                                                                            |
| **TradFi options**       | `(asset_group=tradfi, venue, data_type, options_chain, root, day)` — ES.OPT 11-cluster taxonomy + `combo_type` + `leg_weights`                                            | bundled with cluster validation MANDATORY                                                                                                                                        |
| **DeFi**                 | `(asset_group=defi, chain, venue/protocol, data_type, instrument_id_or_protocol_id, day)`                                                                                 | `chain` is a first-class v5 axis                                                                                                                                                 |
| **Sports**               | `(asset_group=sports, source, data_type, league_id, day)` for ALL sports data_types (ODDS*\*, FIXTURE*\*, INJURIES, STANDINGS, LEAGUES, TEAMS, REFEREES, COACHES, ROUNDS) | `fixture_id` is row-level column NOT shard axis (per Q1 resolution / top-of-file banner); cluster_extractor=bookmaker for ODDS\*\* validates per-fixture coverage within parquet |
| **Prediction**           | `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`                                                           | `market_id` is row-level column NOT shard axis (per Q1 resolution); cluster_extractor=market_id validates per-canonical-question coverage; lifecycle bounds enforced             |

For the complete per-service shard dimension matrix, see
[`02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md).

---

## Per-VM shard isolation for concurrent backfills

Every batch-cluster deployment (multiple GCE VMs running the same service for different shards in parallel) MUST set
`VM_NAME=<unique>` + `MANIFEST_PER_VM_SHARDS=true` per worker. UTL runtime guard: `ManifestWriter.__init__` raises
`MultiWorkerWithoutShardIsolationError` when multi-process detection fires AND per-VM shard isolation isn't set. New
base-service.sh QG STEP 5.66 AST-walks launcher scripts that fork multi-process; asserts envvar setting.

Manifest consolidator merges per-VM shards under `_index/per_vm/{vm_name}.parquet` into the canonical
`_index/availability_index.parquet` with last-writer-wins on identical row_key. Reader fallback merges per-VM shards
when canonical blob is older than `MANIFEST_CONSOLIDATED_STALENESS_SEC` (default 120s).

**Why this matters for shard-level failure isolation**: in a batch cluster with 10 VMs writing the same manifest, OCC
contention on the canonical CAS causes retry exhaustion + last-writer-wins mid-merge that drops most of a rebuild's
output. Per-VM shard isolation eliminates the contention entirely — each VM writes its own shard, the consolidator
merges. Reference incident **2026-05-04**: instruments-service chunk workers without isolation clobbered each other's
manifest entries; fixed in `00f6352` + `619a32e`.

---

## Error Handling Pattern (data-pipeline tier)

```python
for shard in shards_to_process:
    try:
        df = await fetch_and_normalise(shard)
        manifest_writer.record_captured(
            row_key=shard.to_row_key(),
            df=df,
            data_type=shard.data_type,
            # Bundled data_types REQUIRE these kwargs (UTL MissingClusterValidationError if absent):
            expected_root_clusters=UAC.DATA_TYPE_TO_CLUSTER_REGISTRY[shard.data_type] if shard.data_type in UAC.BUNDLED_DATA_TYPES else None,
            cluster_extractor=shard.cluster_extractor if shard.data_type in UAC.BUNDLED_DATA_TYPES else None,
        )
    except SourceReturnedNoTicks:
        manifest_writer.record_empty(row_key=shard.to_row_key(), attempted_at=now)
    except UpstreamTimestampBiasError as e:
        manifest_writer.record_failed(row_key=shard.to_row_key(), error=e, attempted_at=now)
        log_event("UPSTREAM_TIMESTAMP_BIAS", severity="WARNING", details={
            "shard": shard.to_dict(),
            "observed_dates": e.observed_dates,
            "expected_day": e.expected_day.isoformat(),
            "n_ticks": e.n_ticks,
        })
    except MalformedTickFieldError as e:
        manifest_writer.record_failed(row_key=shard.to_row_key(), error=e, attempted_at=now)
    except (ClusterCoverageError, NanRatioExceededError, SchemaMismatchError) as e:
        # Write-gate pillar failures — `record_captured` already routed to record_failed internally
        # before raising; this catch is just for orchestrator-level continue
        log_event("WRITE_GATE_FAILED", severity="WARNING", details={"shard": shard.to_dict(), "pillar": type(e).__name__})
    except Exception as e:
        # Anything else: classify via UAC + record_failed
        manifest_writer.record_failed(
            row_key=shard.to_row_key(),
            error=classify_venue_error(e),
            attempted_at=now,
        )
        log_event("ADAPTER_FETCH_FAILED", severity="WARNING", details={
            "shard": shard.to_dict(),
            "error": str(e),
            "error_type": type(e).__name__,
            "correlation_id": correlation_id,
        })
        # Do NOT raise — continue with remaining shards
```

---

## `classify_venue_error()` unclassified-default convention (retry_safe)

> Pinned by `mtds_retry_safe_default_audit_2026_07_14` (audit + fixes: mtds@b8218f8a, mtds@f82f29c1; annotated residual:
> mtds@0041a8a6; QG lint STEP 5.104 in this commit). Fixes the bug class behind the kalshi_perp
> `mtds_perp_funding_backfill_hang_2026_07_14` incident.

UAC's `classify_venue_error(venue, error_code)` returns `None` whenever the `(venue, error_code)` pair is absent from
`VENUE_ERROR_MAP` — either the venue is entirely unregistered, or the venue is registered but that specific error code
isn't. Three rules govern what an adapter does with that `None`:

1. **Unclassified venue error → `retry_safe = False` — never default-retry an unknown.** The historical MTDS idiom
   `classification.retry_safe if classification (is not None)? else True` silently treated "I don't recognize this
   error" as "safe to retry," which for an unregistered venue retried PERMANENT HTTP statuses (404/400/403) up to
   `_MAX_RETRIES` for no benefit — the exact hang-adjacent bug class this audit fixed. The convention (and the
   fleet-wide QG lint enforcing it, see below) is the safe form:
   `classification.retry_safe if classification is not None else False` /
   `classification.retry_safe if classification else False` (both forms in use — see `defi/utils.py`,
   `prediction/kalshi_adapter.py`, `prediction/polymarket_adapter.py`, `cli/handlers/_defi_manifest.py`).
2. **Unregistered-venue HTTP errors → branch on the HTTP status directly, BEFORE ever consulting the classifier.** A
   venue can be structurally unregistered in `VENUE_ERROR_MAP` while its adapter still needs the standard
   permanent-vs-transient split (retry only `{429, 500, 502, 503, 504}`, fail fast on everything else). Don't route that
   split through `classify_venue_error` (which will always return `None` for an unregistered venue) — branch on
   `aiohttp.ClientResponseError.status` (or equivalent) directly in a small per-module `_handle_response_error` helper,
   and only fall through to the classifier for the non-status exception types it can actually help with. See
   `market_tick_data_service/market_interface/adapters/onchain/{glassnode,helius_solana}.py::_handle_response_error`.
3. **A narrow, deliberate exception to rule 1 is allowed for exception TYPES that are transient by construction** — e.g.
   `aiohttp.ClientError` / `asyncio.TimeoutError` (connection failures, timeouts), as opposed to a permanent HTTP
   status. If a status-branch per rule 2 already intercepts the permanent-status class before this code is ever reached,
   keeping `retry_safe = ... else True` for the remaining non-status transient-exception branch is defensible — retrying
   a bounded number of attempts is the standard resilience posture for a genuinely transient error, unlike retrying a
   permanent error to exhaustion. Any such exception MUST be annotated inline with `# QG-allow: retry-safe` + a comment
   explaining why (see the two GLASSNODE/HELIUS-SOLANA sites in `onchain/glassnode.py` / `onchain/helius_solana.py`) and
   is capped by a **global ratchet baseline** enforced by QG STEP 5.104 in
   `unified-trading-pm/scripts/quality-gates-base/base-service.sh` (fleet-wide — fires for every repo consuming
   `classify_venue_error`, not just MTDS). Baseline = 2 as of 2026-07-25; a new whitelisted site requires an explicit
   decision recorded in the introducing plan/commit AND a baseline bump in that QG step's comment — never a silent add.

**QG enforcement**: `unified-trading-pm/scripts/quality-gates-base/base-service.sh` STEP 5.104 greps every repo's
`${SOURCE_DIR}` for the unsafe `classification.retry_safe if classification (is not None)? else True` idiom. A hit
without a `# QG-allow: retry-safe` marker fails immediately (new unclassified-default site); a hit count above the
baseline fails even when annotated (whitelist growth needs an explicit bump, not a silent add).

---

## Anti-Patterns (DO NOT)

- `raise RuntimeError(...)` inside a per-shard loop — kills all remaining shards in the batch.
- Swallowing errors silently (`except: pass` or `except: continue` without `record_failed`) — errors must be logged AND
  surfaced in the manifest. Per `2026-05-05` Databento incident: `except Exception: continue` inside `download_batch_df`
  silently dropped per-schema results when ohlcv_1m + trades were bundled and ohlcv hit 429; orchestrator marked the
  shard `complete` with no record of the failure. Workspace rule: every per-schema / per-instrument loop must emit
  `record_failed` for failures.
- Storing partial shard data — if a shard fails ANY write-gate pillar mid-processing, discard its partial output
  (`record_failed` only writes the manifest row, NOT the parquet).
- `_create_empty_output()` returning n-row NaN DataFrames — banned method (writegate Phase 2.A deletes from
  `base_adapter`). Reference incident **2026-05-05**: MDPS produced 1440-row NaN OHLC parquets per (venue, data_type,
  day) for years; manifest said `captured`; downstream features computed garbage on garbage.
- Empty parquet that passes `existence_check` but has 0 rows + manifest claims `captured` — banned. Either
  `record_empty(row_key)` (honest absence) OR `record_failed(<typed_reason>)` (something went wrong).
- `classification.retry_safe if classification (is not None)? else True` — defaults an UNCLASSIFIED venue error to "safe
  to retry," which retries permanent 4xx statuses to exhaustion for an unregistered venue (see `classify_venue_error()`
  unclassified-default convention above). QG-blocked fleet-wide (STEP 5.104).

---

## Event Stream Requirements

Failed shard events MUST include:

- **Shard atom fields**: `asset_group`, `venue`, `chain` (DeFi), `data_type`, `instrument_type`, `instrument_id` /
  `root` / `fixture_id` / `canonical_question_group`, `league_id` (sports), `timeframe`, `feature_group`, `day` —
  whichever apply to this service's tier.
- **Typed error reason**: `error_type` = exception class name (`UpstreamTimestampBiasError` / `MalformedTickFieldError`
  / `ClusterCoverageError` / `NanRatioExceededError` / `SchemaMismatchError` / `MissingClusterValidationError` / etc.).
- **Diagnostic payload**: error-specific fields (e.g. `observed_dates` + `expected_day` + `n_ticks` for
  UpstreamTimestampBiasError; `missing_clusters` + `observed_clusters` for ClusterCoverageError; `column` +
  `observed_ratio` + `threshold` for NanRatioExceededError).
- **`correlation_id`**: For tracing across the live cluster (multi-service) or batch cluster (multi-VM).

This enables diagnosis from the event stream (GCS in batch, PubSub in live) without re-running the service. Per
workspace CLAUDE.md `§ No fire-and-forget VM launches`, every VM launch MUST emit STARTED within 60s + per-shard
progress + STOPPED/FAILED at exit; events stream to
`gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl`.

**Event types** (per writegate plan + plan C):

- `STARTED` / `STOPPED` / `FAILED` (lifecycle)
- `INSTRUMENT_PROCESSED` (per-instrument progress with row count) — required for adapter-level visibility per CLAUDE.md
- `RAW_TICK_PARTITION_MISMATCH` (MTDS partitioner validation)
- `CLUSTER_COVERAGE_INSUFFICIENT` (bundle adapter under-coverage)
- `LIFECYCLE_BOUNDS_VIOLATED` (prediction adapter pre-created or post-settled tick)
- `LOOKAHEAD_BIAS_DETECTED` (features-\* compute consumed row with `available_at > target_ts`)
- `MANIFEST_PER_VM_SHARD_WRITE` (per-VM shard parquet landed)
- `MULTI_WORKER_WITHOUT_SHARD_ISOLATION` (UTL guard fired)
- `ADAPTER_FETCH_FAILED` (canonical per-shard failure event with classified error)
- `DATA_ALIGNMENT_VIOLATION` (timestamp-alignment-gate fired — per `06-coding-standards/validation-and-errors.md` §5)
- `UPSTREAM_TIMESTAMP_BIAS` (path B in the four-category empty-output decision — was "three-category" prior to
  2026-07-12 finding 346; taxonomy SSOT `validation-and-errors.md` §1)
- `WRITE_GATE_FAILED` (any of the 4 pillars failed)

---

## Cross-references

- **Manifest semantics + per-service shard dimension matrix**:
  [`02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
- **Deployment cluster taxonomy (live vs batch)**:
  [`05-infrastructure/deployment-clusters-live-vs-batch.md`](/codex/05-infrastructure/deployment-clusters-live-vs-batch.md)
- **deployment-service shard alignment + GCS path templates**:
  [`deployment-service/docs/SHARDING_AND_DATA_ALIGNMENT.md`](../../../deployment-service/docs/SHARDING_AND_DATA_ALIGNMENT.md)
- **Four-category empty-output decision (taxonomy SSOT — was documented as three-category in this doc until 2026-07-12
  finding 346; corrected above)**:
  [`06-coding-standards/validation-and-errors.md`](/codex/06-coding-standards/validation-and-errors.md)
- **Cluster validation + 4-pillar write-gate**:
  [`06-coding-standards/validation-and-errors.md`](/codex/06-coding-standards/validation-and-errors.md)
- **Active plan**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
- **`classify_venue_error()` unclassified-default retry_safe convention + QG lint (STEP 5.104) — plan + parent
  incident**:
  [`plans/active/mtds_retry_safe_default_audit_2026_07_14.md`](../../plans/active/mtds_retry_safe_default_audit_2026_07_14.md),
  [`plans/active/issues/mtds_perp_funding_backfill_hang_2026_07_14.md`](../../plans/active/issues/mtds_perp_funding_backfill_hang_2026_07_14.md)
