---
scope: [engineer]
---

# Validation Patterns

See 06-coding-standards/README.md.

## §Timestamp-Alignment-Gate

Every raw-data `sink.write(...)` in `instruments-service` with a `day={D}` partition key
MUST run through `InstrumentsWriteGate.validate_and_write(...)` from
`unified_trading_library.instruments_write_gate`.

The gate enforces the §5 lookahead-bias rule
([`02-data/sports-scheduling-and-sharding.md` §5](../02-data/sports-scheduling-and-sharding.md#5-lookahead-bias--data-crimes)):
no row-level "as-of" / "valuation" / "data-available-at" timestamp may exceed the partition's
batch date.

**Why this exists.** On 2026-04-22 a Transfermarkt backfill VM
(`tm-backfill-20260421-231758`) ran 18 hours writing wall-clock-2026
`valuation_date=2026-04-22` rows onto `day=2023-03-16` partitions before being caught by visual
log inspection. Two bugs: (1) the orchestrator's TM short-circuit passed `season=None`
(adapter defaulted to `datetime.now(UTC).year=2026`); (2) the adapter stamped
`valuation_date=datetime.now(UTC)` on missing-field rows. §5 names both "data crimes."
Fixes in instruments-service commit `cdded95`; permanent fail-loud guard in UTL `c1987760`
+ instruments-service `454cca3` + `d049d8b`.

### The rule

For every DataFrame written to `by_date/day={D}/entity={E}/...`, every column in
`DEFAULT_AS_OF_COLUMNS` must satisfy `value.date() <= D`:

```python
DEFAULT_AS_OF_COLUMNS = (
    "as_of_date",
    "valuation_date",
    "data_available_at",
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

The helper is in `instruments_service.engine.orchestrator`. The module-level `_WRITE_GATE` is a
singleton `InstrumentsWriteGate(mode="warn")`.

### Modes

- **warn (default, current)**: log + emit `DATA_ALIGNMENT_VIOLATION` + proceed with the write.
  Used during rollout to baseline violation volume before flipping to strict.
- **strict**: log + emit + raise `TimestampAlignmentError` + skip the write. Per-shard
  `try/except` catches the error and calls
  `manifest.record_failed(error="ALIGNMENT_VIOLATION")`.

Flip the default via `_WRITE_GATE = InstrumentsWriteGate(mode="strict")` after warn-mode
prod baseline is clean.

### When the gate no-ops

- `partition` has no `day=` key (mapping / index / cache writes land here — `team_mapping.parquet`,
  `fixture_mapping.parquet`, TM team-mapping cache, SFI league-mapping cache). `sink.write(...)`
  may remain plain in those cases; the gate makes no assertion without a batch date.
- DataFrame is empty or None.
- None of `DEFAULT_AS_OF_COLUMNS` are present. Threading `_gated_sink_write` anyway for writes
  that MIGHT later grow one of those columns is cheap insurance (e.g. the instrument-universe
  writes at `orchestrator.py` L1396 / L1723 / L1775 / L2340).

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

### Related

- Plan: `plans/active/instruments_service_write_gate_validation_2026_04_22.plan.md`.
- Upstream rule: [`02-data/sports-scheduling-and-sharding.md` §5](../02-data/sports-scheduling-and-sharding.md#5-lookahead-bias--data-crimes).
- Feature-service parallel: `FeatureWriteGate` in
  `unified_trading_library.feature_service_base.write_gate` — composes NaN/inf/leakage checks +
  `validate_timestamp_date_alignment`. `InstrumentsWriteGate` is the narrower raw-data analogue.
