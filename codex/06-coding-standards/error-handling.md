---
scope: [engineer]
---

# Error Handling

## Three-category empty-output decision tree (every per-shard adapter)

Per workspace CLAUDE.md `§ Three-category empty-output decision`, every condition that could produce an empty result
resolves to ONE of three categories. **NO fourth category. NO silent NaN placeholder rows.** The
`_create_empty_output()`-style placeholder method is BANNED from `base_adapter` and equivalent base classes (writegate
Phase 2.A deletes it across MDPS' 37 callsites).

| Path                                | Condition                                                                              | Manifest verb                                                                      | Notes                                                                                                                                                                                                                                                                                                                                               |
| ----------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. Honest absence**               | Source returned 0 ticks for the requested window.                                      | `record_empty(row_key, attempted_at)`                                              | Counts in denominator only. Pre-genesis dates, paused leagues, market not yet listed, instrument delisted, non-trading days — all path A.                                                                                                                                                                                                           |
| **B. Upstream timestamp bias**      | Source returned ticks; ALL fall outside the requested day after `interval_idx` filter. | `record_failed(UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks))` | UPSTREAM bug — partition mislabeled at MTDS write-time, OR source replay covered wrong window, OR clock-skew. **Paired upstream MTDS partitioner-validation fix at `raw_tick_hive.py`** (writegate Phase 2.B): `assert tick.timestamp.date() == day_partition_key` before each write; reject mismatched ticks + emit `RAW_TICK_PARTITION_MISMATCH`. |
| **C. Mid-process malformed fields** | Rows in window but downstream calc dropped due to NaN/malformed source fields.         | `record_failed(MalformedTickFieldError(field, n_dropped, sample_values))`          | Data-quality bug worth diagnosing — adapter author surfaces sample values for triage. Different from "all NaN" output (which fails the NaN-ratio write-gate pillar).                                                                                                                                                                                |

The 3 typed errors land in `unified-trading-library/unified_trading_library/errors.py` per writegate plan Phase 1A.

### Why path B is `record_failed`, not `record_empty`

Path B is upstream corruption, NOT honest absence. Treating it as honest empty would silently accept a real bug and
inflate `empty_confirmed` denominators. The fix lives at MTDS partitioner-validation; MDPS just needs to detect path B +
route to `record_failed(UpstreamTimestampBiasError)` so operators see the typed reason in the data-status panel and can
investigate the upstream.

Reference incident **2026-05-05**: MDPS produced 1440-row NaN OHLC parquets per (venue, data_type, day) for years;
manifest said `captured`; downstream features computed garbage on garbage. The post-plan contract makes this bug class
structurally impossible by deleting `_create_empty_output()` and forcing the 3-category decision at every callsite.

---

## Write-gate quartet at `record_captured`

Every `record_captured` call is gated by 4 pillars. Failure of any pillar → `record_failed(<typed_reason>)` instead of
writing the parquet. NO partial passes. See
[`02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
`§ Integrity Principles 4` for full detail.

| Pillar                                         | Typed error on failure                                     | Notes                                                                                                                                                                                        |
| ---------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Row count > 0**                              | `EmptyAfterFilterError`                                    | Mandatory unless source returned legitimately empty (then `record_empty`).                                                                                                                   |
| **NaN ratio per column < threshold**           | `NanRatioExceededError(column, observed_ratio, threshold)` | Per-feature-group thresholds in UAC `nan_thresholds.NAN_RATIO_THRESHOLDS`; lifted from per-service inline in Plan B.                                                                         |
| **Schema matches contract**                    | `SchemaMismatchError(column, expected, observed)`          | Required columns + types. Includes `available_at` column required per row.                                                                                                                   |
| **Cluster coverage ≥ expected** (BUNDLED only) | `ClusterCoverageError(missing, observed)`                  | For `data_type ∈ BUNDLED_DATA_TYPES`, `expected_root_clusters` + `cluster_extractor` MANDATORY (UTL guard raises `MissingClusterValidationError` if absent; QG STEP 5.64 statically checks). |

---

## Per-shard error handling pattern (data-pipeline tier)

```python
from unified_trading_library.errors import (
    UpstreamTimestampBiasError,
    MalformedTickFieldError,
    ClusterCoverageError,
    NanRatioExceededError,
    SchemaMismatchError,
    MissingClusterValidationError,
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

    # ── 3-category empty-output decision ────────────────────────────────────
    except SourceReturnedNoTicks:                     # path A — honest absence
        manifest_writer.record_empty(row_key=shard.to_row_key(), attempted_at=now)

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

    # ── 4-pillar write-gate failures ────────────────────────────────────────
    except (ClusterCoverageError, NanRatioExceededError, SchemaMismatchError) as e:
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

---

## Live cluster vs batch cluster — same handling, different concurrency

Per
[`05-infrastructure/deployment-clusters-live-vs-batch.md`](../05-infrastructure/deployment-clusters-live-vs-batch.md):

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
- Empty parquet that passes existence-check + manifest `captured` — banned. Use `record_empty(row_key)` for honest
  absence OR `record_failed(<typed_reason>)` for failures.
- Lookup-by-mode (`if live_mode: ... else: ...`) for empty-handling — same data, same fields, same timing semantics in
  both modes per `§ Live = batch`. Mode-dependent code paths for empties are double-SSOT and banned.

---

## Cross-references

- **Manifest semantics + write-gate quartet**:
  [`02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- **Cluster validation + InstrumentsWriteGate**:
  [`06-coding-standards/validation-patterns.md`](./validation-patterns.md)
- **Shard-level failure isolation pattern**:
  [`04-architecture/shard-level-failure-isolation.md`](../04-architecture/shard-level-failure-isolation.md)
- **Deployment cluster taxonomy**:
  [`05-infrastructure/deployment-clusters-live-vs-batch.md`](../05-infrastructure/deployment-clusters-live-vs-batch.md)
- **Active plan**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
