---
doc_type: codex-ssot
title: Validation and Errors
summary: >-
  SSOT for write-side validation + per-shard error handling: the 4-category empty-output decision (A honest-absence / B
  upstream-timestamp-bias / C malformed-fields / D zero-activity-bar), the write-gate quartet at `record_captured`,
  per-row Pydantic validation, `available_at`/LookaheadBias, InstrumentsWriteGate, and InstrumentRecord hard-required
  fields.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, features-service, instruments-service, strategy-service, unified-trading-library]
scope: [engineer]
tags: [data-correctness, validation, manifest, honest-coverage, data-pipeline]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-05-08
authoritative_for:
  [write-gate quartet at record_captured, four-category empty-output decision, InstrumentsWriteGate raw-data alignment]
referenced_by:
  [
    /codex/02-data/partitioning.md,
    /codex/02-data/prediction-schema-paths.md,
    /codex/02-data/shard-granularity-cefi.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/05-infrastructure/deployment-clusters-live-vs-batch.md,
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/retry-pattern.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Validation and Errors

> **SSOT for write-side validation + per-shard error handling.** Merges the legacy `error-handling.md` (3-/4-category
> empty-output decision tree) + `validation-patterns.md` (write-gate quartet, available_at, InstrumentsWriteGate,
> LookaheadBias) + `schema-validation.md` (per-row Pydantic validation) into a single chapter. One error-class hierarchy
> per concern; no duplicated write-gate-quartet table.

## TL;DR

Every per-shard adapter / calculator / writer follows the same discipline at the write boundary:

1. **Resolve every empty-output condition** to one of 4 categories (§1) — A honest absence, B upstream timestamp bias, C
   mid-process malformed fields, D zero-activity-bar (catalog-aware).
2. **Pass 4 write-gate pillars** at `record_captured` (§2) — row count, NaN ratio, schema, cluster coverage. Failure of
   ANY pillar → `record_failed(<typed_reason>)` instead of writing the parquet.
3. **Validate per-row, not per-batch** (§3) — Pydantic `model_validate` per row; bad rows route to `record_failed` with
   the exact row's `row_key` and Pydantic error path.
4. **Stamp `available_at` per row at write-time** (§4) — UTL `availability_stamping.stamp_available_at_*` per UAC
   semantics; `LookaheadBiasError` raised loud at every read boundary that violates
   `input.available_at <= target_ts - horizon`.
5. **Gate raw-data sink writes through `InstrumentsWriteGate`** (§5) — `valuation_date`, `as_of_date`, `available_at`,
   etc. must satisfy `value.date() <= partition_day`; `TimestampAlignmentError` in strict mode.
6. **Wrap every shard in try/except** (§6) — never `raise` inside per-shard / per-venue / per-instrument loops; classify
   - record_failed + continue.

---

## §1 Four-category empty-output decision (every per-shard adapter)

Per workspace CLAUDE.md `§ Four-category empty-output decision`, every condition that could produce an empty result
resolves to ONE of four categories. **NO fifth category. NO silent NaN placeholder rows.** The
`_create_empty_output()`-style placeholder method is BANNED from `base_adapter` and equivalent base classes (writegate
Phase 2.A deletes it across MDPS' 37 callsites).

| Path                                | Condition                                                                                                                                                           | Manifest verb                                                                           | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **A. Honest absence**               | Source returned 0 ticks for the requested window AND catalog/venue says the shard was structurally empty.                                                           | `record_empty(row_key, reason=<typed>, attempted_at)`                                   | Counts in denominator only. Pre-genesis dates, paused leagues, market not yet listed, instrument delisted, non-trading days — all path A. Reason MUST be from `EMPTY_CONFIRMED_REASONS` (blank rejected via `LegacyBlankErrorReasonError`).                                                                                                                                                                                                      |
| **B. Upstream timestamp bias**      | Source returned ticks; ALL fall outside the requested day after `interval_idx` filter.                                                                              | `record_failed(UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks))`      | UPSTREAM bug — partition mislabeled at MTDS write-time, OR source replay covered wrong window, OR clock-skew. **Paired upstream MTDS partitioner-validation fix at `raw_tick_hive.py`** (writegate Phase 2.B): `assert tick.timestamp.date() == day_partition_key` before each write; reject mismatched ticks + emit `RAW_TICK_PARTITION_MISMATCH`.                                                                                              |
| **C. Mid-process malformed fields** | Rows in window but downstream calc dropped due to NaN/malformed source fields.                                                                                      | `record_failed(MalformedTickFieldError(field, n_dropped, sample_values))`               | Data-quality bug worth diagnosing — adapter author surfaces sample values for triage. Different from "all NaN" output (which fails the NaN-ratio write-gate pillar).                                                                                                                                                                                                                                                                             |
| **D. Zero-activity bar** (NEW)      | Source returned 0 BUT instruments-service catalog says the instrument was ALIVE on the day AND day falls within venue market hours (operator directive 2026-05-07). | `record_captured` with zero-activity bars (O=H=L=C=prior_LTP, volume=0, trade_count=0). | Captures the "tradeable but illiquid" semantic distinct from "missing." Critical for cross-instrument analyses like volatility smiles where every strike must be visible. The catalog-aware write-gate (writer-side guard, writegate Wave 2 of Phase 3.D.5) drives the (A) vs (D) split. For sports / prediction the (D) bar shape uses prior bookmaker odds / prior market mid as carry-forward; for cefi / defi / tradfi it's prior trade LTP. |

The 4 typed errors land in `unified-trading-library/unified_trading_library/errors.py` per writegate plan Phase 1A.

### Why path B is `record_failed`, not `record_empty`

Path B is upstream corruption, NOT honest absence. Treating it as honest empty would silently accept a real bug and
inflate `empty_confirmed` denominators. The fix lives at MTDS partitioner-validation; MDPS just needs to detect path B +
route to `record_failed(UpstreamTimestampBiasError)` so operators see the typed reason in the data-status panel and can
investigate the upstream.

Reference incident **2026-05-05**: MDPS produced 1440-row NaN OHLC parquets per (venue, data_type, day) for years;
manifest said `captured`; downstream features computed garbage on garbage. The post-plan contract makes this bug class
structurally impossible by deleting `_create_empty_output()` and forcing the 4-category decision at every callsite.

### Reason taxonomy (closed set)

`record_empty` accepts only typed reasons from UAC `EMPTY_CONFIRMED_REASONS`: `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` /
`EXPECTED_PAUSED_LEAGUE` / `EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_PRE_GENESIS_CHAIN` /
`EXPECTED_INSTRUMENT_NOT_LISTED` / `EXPECTED_INSTRUMENT_DELISTED` / `EXPECTED_PARTIAL_HALF_DAY` /
`SOURCE_RETURNED_ZERO`. Blank reasons are rejected loudly via `LegacyBlankErrorReasonError`. **Asset-group-specific
empty_confirmed legitimacy rule (operator directive 2026-05-07)**: sports / prediction CAN have empty_confirmed at
instrument-day grain; cefi / defi / tradfi CANNOT — only venue-level rules (HOLIDAY / WEEKEND / PRE_VENUE_LAUNCH /
PRE_GENESIS_CHAIN / PARTIAL_HALF_DAY) make empty_confirmed legit.

---

## §2 Write-gate quartet at `record_captured`

Every `record_captured` call is gated by 4 pillars. Failure of any pillar → `record_failed(<typed_reason>)` instead of
writing the parquet. NO partial passes. Per workspace CLAUDE.md `§ Validation gates per record_captured` + writegate
plan Phase 1A.

| Pillar                                            | Gate                                                                                                                                                                                          | Failure mode                                                              | Lifted from                                                                                                                                             |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Row count > 0**                              | Mandatory unless source response was legitimately empty (then `record_empty`, not `record_captured`).                                                                                         | `record_failed(EmptyAfterFilterError)`                                    | Built-in to `record_captured`                                                                                                                           |
| **2. NaN ratio per column < threshold**           | Per-feature-group thresholds in UAC `nan_thresholds.NAN_RATIO_THRESHOLDS`.                                                                                                                    | `record_failed(NanRatioExceededError(column, observed_ratio, threshold))` | Plan B lifts from `instruments-service _validate_predictions_null_rates` (FootyStats-only) to UTL `write_gate_helpers.check_nan_ratio` with single SSOT |
| **3. Schema matches contract**                    | Required columns + types match UAC schema declaration (existing `ParquetSchemaEnforcer`). Includes `available_at` column required per row. See §3 for per-row Pydantic validation discipline. | `record_failed(SchemaMismatchError(column, expected, observed))`          | Existing `ParquetSchemaEnforcer`                                                                                                                        |
| **4. Cluster coverage ≥ expected** (BUNDLED only) | For `data_type ∈ BUNDLED_DATA_TYPES`, `expected_root_clusters` + `cluster_extractor` MANDATORY (UTL guard raises `MissingClusterValidationError` if absent; QG STEP 5.64 statically checks).  | `record_failed(ClusterCoverageError(missing, observed))`                  | Writegate Phase 1A — new                                                                                                                                |

### Cluster validation pillar (mandatory for bundled shards)

`ManifestWriter.record_captured` REQUIRES `expected_root_clusters: Mapping[str, int]` +
`cluster_extractor: Callable[[str], str]` kwargs when
`data_type ∈ unified_api_contracts.canonical.crosscutting.honest_coverage.BUNDLED_DATA_TYPES`. UTL guard raises
`MissingClusterValidationError` if absent. **QG STEP 5.64 statically walks every `record_captured(` callsite and asserts
the kwargs are passed when the literal data_type is bundled — fails CI if missing.**

**Bundled data_types** (cluster validation mandatory):

| Data type                                                                   | Cluster registry                | Cluster extractor                                                              | Notes                                                                                                                                                                          |
| --------------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `options_chain`                                                             | `OPTIONS_CLUSTERS` (UAC)        | regex on symbol prefix → `(E[1-5]A\|EW[1-4]\|EOM\|ES)` for ES.OPT 11-cluster   | Lifted from instruments-service to UAC per writegate Phase 1B                                                                                                                  |
| `futures_chain`                                                             | `FUTURES_CLUSTERS` (UAC)        | derived from `raw_symbol` via `derive_expiry_bucket(symbol, today)` UTL helper | ES + MES seeds; per-root spreads + butterflies; greenfield                                                                                                                     |
| `prediction_canonical_question_group`                                       | `PREDICTION_GROUPS` (UAC)       | `lambda row: row["market_id"]`                                                 | Per-canonical-group expected market_ids per day by cadence (HOURLY=24/day, DAILY=1/day, ELECTION=1 over months); populated by predictions Plan A; empty placeholder until then |
| `ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` (sports per-fixture-bundle) | `SPORTS_FIXTURE_CLUSTERS` (UAC) | `lambda row: row["bookmaker"]`                                                 | Per-league-tier expected bookmaker sets; tier-1 EU football seed                                                                                                               |

Adding a new bundled data_type means adding it to UAC `BUNDLED_DATA_TYPES` AND seeding its registry — no half-measures,
no helper-call-pattern. The standalone `check_cluster_coverage` helper is private to UTL after the contract change;
callers that try to use it directly outside `record_captured` get a deprecation error.

**On under-coverage**: `record_captured` calls `_check_cluster_coverage` internally; on under-coverage
`record_failed(ClusterCoverageError(missing, observed))` fires INSTEAD of writing the parquet. Reference incident
**2026-05-06**: TradFi MVP ES.OPT 18 dates with single-parent fills passed manifest as `captured` because no cluster
validation existed. Post-plan contract makes this bug class structurally impossible.

---

## §3 Per-row schema validation (write-time)

Every adapter / calculator / writer that writes parquet to GCS MUST validate **per-row** against the canonical schema
before calling `record_captured`. Schema drift detected at read-time is too late — by then a downstream service has
already consumed garbage.

### SSOT — UAC schema declarations

The canonical schema for each `data_type` lives in UAC under `unified_api_contracts/canonical/domain/<asset_group>/`.
Adapters import the schema and validate before writing:

```python
from unified_api_contracts.canonical.domain.cefi.ohlcv_1m import OHLCV1mRow
from unified_trading_library.errors import SchemaMismatchError

def _write_row(row: dict, manifest: ManifestWriter, row_key: ShardKey) -> None:
    try:
        validated = OHLCV1mRow.model_validate(row)        # Pydantic per-row
    except ValidationError as exc:
        manifest.record_failed(
            row_key=row_key,
            error=SchemaMismatchError(
                data_type=row_key.data_type,
                row_index=...,
                pydantic_errors=exc.errors(),
            ),
            attempted_at=now(),
        )
        return  # Do not append the row to the parquet writer.

    parquet_writer.append(validated.model_dump())
```

### Why per-row, not per-batch

Per-batch validation (validate the dataframe at the end) catches a schema drift bug, but loses the bad row's identity —
you get one error for "100 rows failed" with no clue which 100. Per-row validation:

- Records `record_failed` with the exact row's `row_key` and the per-row error reason.
- Lets the rest of the batch ship cleanly (the bad row doesn't poison the parquet).
- Surfaces partial failures in the manifest as `attempted_failed` with `error_reason=SCHEMA_VALIDATION_FAILED`.

### `SCHEMA_VALIDATION_FAILED` reason

`SCHEMA_VALIDATION_FAILED` is a typed `error_reason` in the manifest taxonomy (closed set; canonical list in UAC
`EMPTY_CONFIRMED_REASONS` + `ATTEMPTED_FAILED_REASONS`). The reason carries the Pydantic error path so operators can
debug from manifest reads alone. The error class is `SchemaMismatchError` (single canonical name; the legacy alias
`SchemaValidationFailedError` was removed at the D.5 merge).

### What MUST validate

Every write-time adapter:

- MTDS adapters (per-instrument tick fetchers, per-bar OHLCV builders).
- MDPS calculators (per-bar OHLC reshape, per-bar features).
- features-service calculators (every BaseCalculator subclass).
- instruments-service catalog refresh adapters.
- ml-training-service feature loaders (validate inputs before training; bad inputs corrupt the model).

### What does NOT validate at write-time

- Pure passthrough services that read a parquet and re-write a derived parquet — they trust the read-time schema (which
  was already validated at write).
- Backfill scripts that operate on already-validated parquets.

---

## §4 `available_at` + LookaheadBias

### §4.1 `available_at` per-row write-time stamping

Every shard's parquet contains an `available_at` column. Each row's value = when the live pipeline would have actually
had that row's information per
`unified_api_contracts.canonical.crosscutting.availability_semantics.AVAILABILITY_AT_SEMANTICS`. NEVER derived at
read-time. Per workspace CLAUDE.md `§ available_at is per-row, write-time, equal to live-pipeline-arrival`.

`record_captured` calls `assert_available_at_present(df)` internally — missing or null `available_at` →
`LookaheadBiasError`. (Note: missing `available_at` is a lookahead-bias risk, hence raised via `LookaheadBiasError`, not
`SchemaMismatchError`. The schema pillar in §2 catches structural column-shape drift; the available_at presence check
catches the timing-semantics violation.)

UTL stamping helpers (`unified_trading_library.availability_stamping`):

| Helper                                                                             | Used for                                                                                                                                                |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `stamp_available_at_kickoff_offset(df, kickoff_col, minutes=60)`                   | Sports fixture_lineups (kickoff − 60min, conservative — actual is at LEAST 60min before)                                                                |
| `stamp_available_at_post_match(df, kickoff_col, duration_min, scrape_latency_min)` | Sports fixture_stats / fixture_player_stats (match_end_time + scrape latency)                                                                           |
| `stamp_available_at_event_time(df, event_time_col)`                                | Per-row event_time pass-through (fixture_events, injuries when in-fixture)                                                                              |
| `stamp_available_at_announcement(df, announced_col)`                               | Sports fixtures (low-confidence default until forward-poll source lands per `sports_forward_poll_timestamps_2026_<TBD>.plan.md`)                        |
| `stamp_available_at_explicit(df, fetch_completed_at)`                              | Sports reference tables (8 entries: players / venues / leagues / teams / referees / coaches / standings / rounds); prediction MARKET_LIFECYCLE metadata |
| `stamp_available_at_tick_plus_latency(df, ts_col, source_key)`                     | CeFi / DeFi / TradFi / prediction tick-level data; latency from `UAC.SOURCE_PRIORITY[(asset_group, data_type)]` top entry                               |

**Live = batch principle**: live and batch produce identical schemas, identical fields, identical timing semantics. Only
the SOURCE differs. Historical writes stamp `available_at` with the live-pipeline-equivalent arrival time, NOT the
historical archive's slower archive time. Banned: separate live-only data_types like `LINEUPS_PRE_MATCH` vs
`LINEUPS_POST_MATCH`; field sets that diverge between live + batch parquets.

### §4.2 LookaheadBias enforcement (features-\* + MDPS compute)

`LookaheadBiasError` raised loud at every features-\* + MDPS compute, NOT warn-mode. Every input row consumed must
satisfy `input.available_at <= target_ts - horizon`. Strict-mode raise, not log-and-continue. Per workspace CLAUDE.md
`§ LookaheadBiasError`.

Currently fires for `lst_yields`; writegate Phase 2 + Plan B extend to every features-\* calculator. The UAC
`feature_group → required_inputs[]` DAG (Plan B lift to UAC `feature_dag.FEATURE_DAG`) drives the check.

**For prediction markets** (predictions Plan A): per-market lifecycle gating extends the check — feature compute at time
T can only consume ticks where `tick.timestamp <= T` AND `tick.market_id`'s `market_created_at <= T` AND
`tick.market_id`'s `settlement_time > T`. UTL helper `assert_lifecycle_respected(feature_t, market_lifecycles)` in
`unified_trading_library.lifecycle_gate`.

### §4.3 Available-at reader enforcement (post-2026-05-06)

Reading services (features-\* / strategy-service / ml-\* / execution-service backtest / pnl-attribution) MUST consume
the `available_at` column when filtering rows for a feature compute or backtest decision at time `T`:

```python
# Required filter at every cross-service read boundary:
df_safe = df[df["available_at"] <= target_ts - horizon]

# Banned anti-patterns:
# - Filtering by `day` partition key alone (allows late-day rows whose available_at > target_ts)
# - Deriving `available_at` at read-time (impossible — see workspace CLAUDE.md `§ available_at`)
# - Using `timestamp` instead of `available_at` (timestamp is the event time; available_at is when we'd KNOW about the event live)
```

---

## §5 InstrumentsWriteGate (raw-data sink writes)

Every raw-data `sink.write(...)` in `instruments-service` with a `day={D}` partition key MUST run through
`InstrumentsWriteGate.validate_and_write(...)` from `unified_trading_library.instruments_write_gate`.

The gate enforces the §5 lookahead-bias rule
([`02-data/sports-scheduling-and-sharding.md` §5](/codex/02-data/sports-scheduling-and-sharding.md#5-lookahead-bias--data-crimes)):
no row-level "as-of" / "valuation" / "data-available-at" timestamp may exceed the partition's batch date.

**Why this exists.** On 2026-04-22 a Transfermarkt backfill VM (`tm-backfill-20260421-231758`) ran 18 hours writing
wall-clock-2026 `valuation_date=2026-04-22` rows onto `day=2023-03-16` partitions before being caught by visual log
inspection. Two bugs: (1) the orchestrator's TM short-circuit passed `season=None` (adapter defaulted to
`datetime.now(UTC).year=2026`); (2) the adapter stamped `valuation_date=datetime.now(UTC)` on missing-field rows. §5
names both "data crimes." Fixes in instruments-service commit `cdded95`; permanent fail-loud guard in UTL `c1987760` +
instruments-service `454cca3` + `d049d8b`.

### The rule

For every DataFrame written to `by_date/day={D}/entity={E}/...`, every column in `DEFAULT_AS_OF_COLUMNS` must satisfy
`value.date() <= D`:

```python
DEFAULT_AS_OF_COLUMNS = (
    "as_of_date",
    "valuation_date",
    "available_at",          # canonical column required per row (post-2026-05-06)
    "kickoff_utc",
    "event_time",
    "computed_at",
)
```

Override per call via `check_columns=` if a venue uses a different column family.

### Usage

Call `_gated_sink_write(sink, ...)` instead of `sink.write(...)`:

```python
_gated_sink_write(
    sink,
    data=df,
    partition={"day": date, "entity": "player_values"},
    filename="player_values.parquet",
    venue="transfermarkt",
    entity="player_values",
)
```

The helper is in `instruments_service.engine.orchestrator`. The module-level `_WRITE_GATE` is a singleton
`InstrumentsWriteGate(mode="warn")`.

### Modes

- **warn (default, current)**: log + emit `DATA_ALIGNMENT_VIOLATION` + proceed with the write. Used during rollout to
  baseline violation volume before flipping to strict.
- **strict**: log + emit + raise `TimestampAlignmentError` + skip the write. Per-shard `try/except` catches the error
  and calls `manifest.record_failed(error="ALIGNMENT_VIOLATION")`.

Flip the default via `_WRITE_GATE = InstrumentsWriteGate(mode="strict")` after warn-mode prod baseline is clean.

### When the gate no-ops

- `partition` has no `day=` key (mapping / index / cache writes land here — `team_mapping.parquet`,
  `fixture_mapping.parquet`, TM team-mapping cache, SFI league-mapping cache). `sink.write(...)` may remain plain in
  those cases; the gate makes no assertion without a batch date.
- DataFrame is empty or None.
- None of `DEFAULT_AS_OF_COLUMNS` are present. Threading `_gated_sink_write` anyway for writes that MIGHT later grow one
  of those columns is cheap insurance (e.g. the instrument-universe writes at `orchestrator.py` L1396 / L1723 / L1775 /
  L2340).

### Emitted event

`DATA_ALIGNMENT_VIOLATION` (see `unified_trading_library.events`). Payload:

```python
{
    "partition": {"day": "2023-03-16", "entity": "player_values"},
    "batch_date": "2023-03-16",
    "mode": "warn" | "strict",
    "venue": "transfermarkt",
    "entity": "player_values",
    "violations": [
        {
            "column": "valuation_date",
            "offending_row_count": 3,
            "sample_offending_value": "2026-04-22",
            "total_non_null": 3,
        },
    ],
}
```

Severity is `WARNING` in warn mode, `CRITICAL` in strict.

---

## §6 Per-shard try/except pattern (data-pipeline tier)

```python
from unified_trading_library.errors import (
    UpstreamTimestampBiasError,
    MalformedTickFieldError,
    ClusterCoverageError,
    NanRatioExceededError,
    SchemaMismatchError,
    MissingClusterValidationError,
    LookaheadBiasError,
)
from unified_api_contracts import classify_venue_error
from unified_api_contracts.canonical.crosscutting.honest_coverage import (
    BUNDLED_DATA_TYPES,
    DATA_TYPE_TO_CLUSTER_REGISTRY,
)

for shard in shards_to_process:
    try:
        df = await fetch_and_normalise(shard)
        # `available_at` column populated per row by the adapter via
        # `unified_trading_library.availability_stamping.stamp_available_at_*`
        # per UAC.AVAILABILITY_AT_SEMANTICS for the (asset_group, data_type) pair.

        if shard.data_type in BUNDLED_DATA_TYPES:
            manifest_writer.record_captured(
                row_key=shard.to_row_key(),
                df=df,
                data_type=shard.data_type,
                expected_root_clusters=DATA_TYPE_TO_CLUSTER_REGISTRY[shard.data_type],
                cluster_extractor=shard.cluster_extractor,
            )
        else:
            manifest_writer.record_captured(
                row_key=shard.to_row_key(),
                df=df,
                data_type=shard.data_type,
            )

    # ── 4-category empty-output decision ────────────────────────────────────
    except SourceReturnedNoTicks as e:                # path A — honest absence
        manifest_writer.record_empty(
            row_key=shard.to_row_key(),
            reason=e.typed_reason,                    # from EMPTY_CONFIRMED_REASONS
            attempted_at=now,
        )

    except UpstreamTimestampBiasError as e:           # path B — upstream bug
        manifest_writer.record_failed(row_key=shard.to_row_key(), error=e, attempted_at=now)
        log_event("UPSTREAM_TIMESTAMP_BIAS", severity="WARNING", details={
            "shard": shard.to_dict(),
            "observed_dates": e.observed_dates,
            "expected_day": e.expected_day.isoformat(),
            "n_ticks": e.n_ticks,
        })

    except MalformedTickFieldError as e:              # path C — data-quality bug
        manifest_writer.record_failed(row_key=shard.to_row_key(), error=e, attempted_at=now)

    # path D (zero-activity bar) — shaped at fetch-time, lands in the try block
    # via record_captured with carry-forward bars; no separate except clause.

    # ── 4-pillar write-gate failures ────────────────────────────────────────
    except (ClusterCoverageError, NanRatioExceededError, SchemaMismatchError, LookaheadBiasError) as e:
        # `record_captured` already routed to `record_failed` internally before raising.
        log_event("WRITE_GATE_FAILED", severity="WARNING", details={
            "shard": shard.to_dict(),
            "pillar": type(e).__name__,
            "details": e.diagnostic_payload(),
        })

    # ── Anything else: classify + record_failed + continue ─────────────────
    except Exception as e:
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
        # Do NOT raise — continue with remaining shards (per shard-level failure isolation).
```

### Live cluster vs batch cluster — same handling, different concurrency

Per
[`05-infrastructure/deployment-clusters-live-vs-batch.md`](/codex/05-infrastructure/deployment-clusters-live-vs-batch.md):

- **Live cluster**: multiple different services co-located + co-running. A failed shard in MTDS (e.g. one venue's tick
  stream errors) doesn't kill MDPS, features-\*, strategy, or execution running concurrently in the same cluster — each
  service handles its own per-shard isolation per the pattern above.
- **Batch cluster**: the SAME service running N times for N different shards in parallel. A failed shard in worker VM #3
  doesn't kill workers #1-2 or #4-N — each VM runs its own per-shard loop independently. Per-VM shard isolation
  (`MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`) prevents the workers from clobbering each other's manifest writes.

Live and batch produce identical outputs at the manifest row-key level (per workspace CLAUDE.md `§ Live = batch`). The
error-handling pattern is identical.

---

## Anti-Patterns (DO NOT)

- `raise RuntimeError(...)` inside a per-shard / per-venue / per-instrument loop — kills all remaining shards.
- `except: pass` or `except Exception: continue` without `record_failed` — silently drops the failure. Reference:
  2026-05-05 Databento `download_batch_df` per-schema swallow incident; fixed in writegate plan parent.
- `_create_empty_output()` returning n_candles-row NaN DataFrames — BANNED from `base_adapter` (writegate Phase 2.A
  deletion).
- Empty parquet that passes existence-check + manifest `captured` — banned. Use `record_empty(row_key, reason)` for
  honest absence OR `record_failed(<typed_reason>)` for failures.
- Lookup-by-mode (`if live_mode: ... else: ...`) for empty-handling — same data, same fields, same timing semantics in
  both modes per `§ Live = batch`. Mode-dependent code paths for empties are double-SSOT and banned.
- `record_captured` for a bundled `data_type` without `expected_root_clusters` + `cluster_extractor` — UTL guard raises
  `MissingClusterValidationError` and QG STEP 5.64 fails CI.
- Standalone `check_cluster_coverage(df, ...)` callsite outside `record_captured` — deprecated; helper is private to
  UTL.
- Writing parquets without an `available_at` column — `assert_available_at_present` raises `LookaheadBiasError`.
- Deriving `available_at` at read-time — impossible to do honestly (read-time can't tell "available now" from "available
  when the fixture happened").
- Per-batch (vs per-row) Pydantic validation — loses bad-row identity; fail-fast on the dataframe means 1 error for N
  bad rows. Use per-row `model_validate` and route bad rows to `record_failed(SchemaMismatchError)`.
- Using a custom `SchemaValidationFailedError` class — the canonical name is `SchemaMismatchError`; the legacy alias was
  removed at the D.5 merge.

---

## §7 InstrumentRecord hard-required field enforcement

`InstrumentRecord._enforce_per_asset_group_required_fields` (Pydantic `model_validator(mode="after")`) enforces
per-asset-group field requirements at write-time. Rules shipped as of 2026-05-20:

| Rule | Condition                                          | Requirement                                                                               | Shipped                  |
| ---- | -------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------ |
| 1    | `instrument_type in {SPOT_PAIR, PERPETUAL}`        | `base_asset` non-empty AND `quote_asset` non-empty                                        | `uac@hard-schema-phase1` |
| 2    | DeFi ONCHAIN                                       | `pool_address` OR `base_asset_contract_address` non-null (disjunctive — one or the other) | `uac@hard-schema-phase1` |
| 3    | `instrument_type == FUTURE`                        | `expiry` non-null                                                                         | `uac@80aef10`            |
| 4    | `instrument_type == OPTION`                        | `expiry` non-null                                                                         | `uac@80aef10`            |
| 5    | `instrument_type == EVENT_CONTRACT`                | `expiry` non-null                                                                         | `uac@80aef10`            |
| 6    | `instrument_type in DEFI_ONCHAIN_INSTRUMENT_TYPES` | `base_asset_decimals` non-null                                                            | `uac@956bec1`            |
| 7    | `instrument_type == POOL`                          | `quote_asset_decimals` non-null (two-asset pool)                                          | `uac@956bec1`            |

**`DEFI_ONCHAIN_INSTRUMENT_TYPES`** (UAC `internal/reference/instrument.py`):
`{POOL, LENDING, LST, YIELD_BEARING, A_TOKEN, DEBT_TOKEN, STAKING, SPOT_ASSET}`

**Declaration status**: all fields above stay `Optional` at declaration level (cannot express disjunctive or
per-instrument-type constraints in the type system alone). The `model_validator` is the runtime SSOT. Subclass approach
(declaration-level enforcement for `expiry` on FUTURE/OPTION) is Phase E — deferred post-cutover per
`hard_schema_phase1_field_flip_migration_2026_05_19.md`.

**Audit scripts** (instruments-service/scripts/):

- `audit_defi_null_decimals_2026_05_19.py` — audits Rules 6+7 against GCS historical rows
- `audit_cefi_empty_base_quote_2026_05_19.py` — audits Rule 1 against GCS historical rows

**SSOT**: `plans/active/hard_schema_phase1_field_flip_migration_2026_05_19.md`

- `plans/active/hard_schema_enforcement_2026_05_08.md`

---

## Cross-references

- **Manifest semantics + write-gate quartet (read-side detail)**:
  [`02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
  `§ Integrity Principles 4`
- **Honest absence (read-side downstream)**:
  [`02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md) — how
  downstream consumers handle `attempted_failed` rows + reason taxonomy detail.
- **Shard-level failure isolation pattern**:
  [`04-architecture/shard-level-failure-isolation.md`](/codex/04-architecture/shard-level-failure-isolation.md)
- **Deployment cluster taxonomy**:
  [`05-infrastructure/deployment-clusters-live-vs-batch.md`](/codex/05-infrastructure/deployment-clusters-live-vs-batch.md)
- **BaseCalculator (where the validation hook lives)**: [`feature-service-pattern.md`](feature-service-pattern.md)
- **FeatureWriteGate parallel**: `unified_trading_library.feature_service_base.write_gate` — composes NaN/inf/leakage
  checks + `validate_timestamp_date_alignment`. `InstrumentsWriteGate` is the narrower raw-data analogue.
- **Upstream lookahead-bias rule (sports)**:
  [`02-data/sports-scheduling-and-sharding.md` §5](/codex/02-data/sports-scheduling-and-sharding.md#5-lookahead-bias--data-crimes)
- **Active write-gate plan**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
- **Active hard-schema enforcement plan**:
  [`plans/active/hard_schema_enforcement_2026_05_08.md`](../../plans/active/hard_schema_enforcement_2026_05_08.md)
- **Archived predictions migration plan**:
  [`plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](../../plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md)
- **InstrumentsWriteGate plan**:
  [`plans/ai/instruments_service_write_gate_validation_2026_04_22.plan.md`](../../plans/ai/instruments_service_write_gate_validation_2026_04_22.plan.md)
