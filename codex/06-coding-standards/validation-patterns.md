---
scope: [engineer]
---

# Validation Patterns

## §Write-Gate-Quartet (the 4 pillars at `record_captured`)

Every `record_captured` call is gated by 4 pillars. Failure of any pillar → `record_failed(<typed_reason>)` instead of
writing the parquet. NO partial passes. Per workspace CLAUDE.md `§ Validation gates per record_captured` + writegate
plan Phase 1A.

| Pillar                                            | Gate                                                                                                                                                                                         | Failure mode                                                              | Lifted from                                                                                                                                             |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Row count > 0**                              | Mandatory unless source response was legitimately empty (then `record_empty`, not `record_captured`).                                                                                        | `record_failed(EmptyAfterFilterError)`                                    | Built-in to `record_captured`                                                                                                                           |
| **2. NaN ratio per column < threshold**           | Per-feature-group thresholds in UAC `nan_thresholds.NAN_RATIO_THRESHOLDS`.                                                                                                                   | `record_failed(NanRatioExceededError(column, observed_ratio, threshold))` | Plan B lifts from `instruments-service _validate_predictions_null_rates` (FootyStats-only) to UTL `write_gate_helpers.check_nan_ratio` with single SSOT |
| **3. Schema matches contract**                    | Required columns + types match UAC schema declaration (existing `ParquetSchemaEnforcer`). Includes `available_at` column required per row.                                                   | `record_failed(SchemaMismatchError)`                                      | Existing `ParquetSchemaEnforcer`                                                                                                                        |
| **4. Cluster coverage ≥ expected** (BUNDLED only) | For `data_type ∈ BUNDLED_DATA_TYPES`, `expected_root_clusters` + `cluster_extractor` MANDATORY (UTL guard raises `MissingClusterValidationError` if absent; QG STEP 5.64 statically checks). | `record_failed(ClusterCoverageError(missing, observed))`                  | Writegate Phase 1A — new                                                                                                                                |

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

## §Available-At-Per-Row (write-time stamping)

Every shard's parquet contains an `available_at` column. Each row's value = when the live pipeline would have actually
had that row's information per
`unified_api_contracts.canonical.crosscutting.availability_semantics.AVAILABILITY_AT_SEMANTICS`. NEVER derived at
read-time. Per workspace CLAUDE.md `§ available_at is per-row, write-time, equal to live-pipeline-arrival`.

`record_captured` calls `assert_available_at_present(df)` internally — missing or null `available_at` →
`LookaheadBiasError`.

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

---

## §Timestamp-Alignment-Gate (raw-data sink writes)

Every raw-data `sink.write(...)` in `instruments-service` with a `day={D}` partition key MUST run through
`InstrumentsWriteGate.validate_and_write(...)` from `unified_trading_library.instruments_write_gate`.

The gate enforces the §5 lookahead-bias rule
([`02-data/sports-scheduling-and-sharding.md` §5](../02-data/sports-scheduling-and-sharding.md#5-lookahead-bias--data-crimes)):
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
    "data_available_at",
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

## §LookaheadBias-Enforcement (features-\* + MDPS compute)

`LookaheadBiasError` raised loud at every features-\* + MDPS compute, NOT warn-mode. Every input row consumed must
satisfy `input.available_at <= target_ts - horizon`. Strict-mode raise, not log-and-continue. Per workspace CLAUDE.md
`§ LookaheadBiasError`.

Currently fires for `lst_yields`; writegate Phase 2 + Plan B extend to every features-\* calculator. The UAC
`feature_group → required_inputs[]` DAG (Plan B lift to UAC `feature_dag.FEATURE_DAG`) drives the check.

**For prediction markets** (predictions Plan A): per-market lifecycle gating extends the check — feature compute at time
T can only consume ticks where `tick.timestamp <= T` AND `tick.market_id`'s `market_created_at <= T` AND
`tick.market_id`'s `settlement_time > T`. UTL helper `assert_lifecycle_respected(feature_t, market_lifecycles)` in
`unified_trading_library.lifecycle_gate`.

---

## §Available-At Reader Enforcement (post-2026-05-06)

Reading services (features-_ / strategy-service / ml-_ / execution-service backtest / pnl-attribution) MUST consume the
`available_at` column when filtering rows for a feature compute or backtest decision at time `T`:

```python
# Required filter at every cross-service read boundary:
df_safe = df[df["available_at"] <= target_ts - horizon]

# Banned anti-patterns:
# - Filtering by `day` partition key alone (allows late-day rows whose available_at > target_ts)
# - Deriving `available_at` at read-time (impossible — see workspace CLAUDE.md `§ available_at`)
# - Using `timestamp` instead of `available_at` (timestamp is the event time; available_at is when we'd KNOW about the event live)
```

---

## Anti-Patterns (DO NOT)

- `record_captured` for a bundled `data_type` without `expected_root_clusters` + `cluster_extractor` — UTL guard raises
  `MissingClusterValidationError` and QG STEP 5.64 fails CI.
- Standalone `check_cluster_coverage(df, ...)` callsite outside `record_captured` — deprecated; helper is private to
  UTL.
- Writing parquets without an `available_at` column — `assert_available_at_present` raises `LookaheadBiasError`.
- Deriving `available_at` at read-time — impossible to do honestly (read-time can't tell "available now" from "available
  when the fixture happened").
- Mode-dependent code paths for live vs batch — banned per `§ Live = batch`.

---

## Related

- **Active write-gate plan**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md)
- **Active predictions migration plan**:
  [`plans/active/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](../../plans/active/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md)
- **InstrumentsWriteGate plan**: `plans/active/instruments_service_write_gate_validation_2026_04_22.plan.md`
- **Upstream lookahead-bias rule**:
  [`02-data/sports-scheduling-and-sharding.md` §5](../02-data/sports-scheduling-and-sharding.md#5-lookahead-bias--data-crimes)
- **Manifest semantics + write-gate quartet**:
  [`02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- **Three-category empty-output decision tree**: [`06-coding-standards/error-handling.md`](./error-handling.md)
- **Shard-level failure isolation pattern**:
  [`04-architecture/shard-level-failure-isolation.md`](../04-architecture/shard-level-failure-isolation.md)
- **FeatureWriteGate parallel**: `unified_trading_library.feature_service_base.write_gate` — composes NaN/inf/leakage
  checks + `validate_timestamp_date_alignment`. `InstrumentsWriteGate` is the narrower raw-data analogue.
