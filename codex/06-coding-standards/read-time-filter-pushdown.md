---
scope: [engineer, admin]
---

# Read-time filter pushdown — list before load

## Rule

Every batch service whose pipeline shape is **list raw → filter candidate set → load → process → write** MUST apply
scope filters (`instrument_ids` / `venues` / `data_types` / equivalent) **at the LIST stage** before any blob's bytes
are downloaded. Filtering only at the WRITE stage is review-blocking — the scanner queues N blobs, workers download all
N, memory grows linearly with N regardless of how many outputs actually get written.

## Anti-pattern (don't do this)

```python
# Scanner returns blobs whose `venue=` prefix matches `venues`
# but DOES NOT consult `instrument_ids` on the matching path.
if venues:
    blob_has_venue = any(f"venue={v}" in blob_name for v in venues)
    if not blob_has_venue and not filter_blob_by_criteria(blob_name, venues, instrument_ids):
        continue
files.append(blob_name)
# Later: worker downloads blob, write step filters by instrument_ids.
```

Even if the per-blob write is a no-op when `instrument_ids` doesn't match, the **download already happened** — memory is
gone for the duration of the worker. With N=200+ blobs and concurrent workers, RSS climbs into tens of GB before the
worker queue drains.

## Correct pattern

```python
# Scanner applies BOTH filters at list time. Workers only ever see the
# operator-requested file list.
if venues:
    blob_has_venue = (
        any(f"venue={v}" in blob_name for v in venues)
        or _blob_matches_chain_split_venue(blob_name, venues)
    )
    if not blob_has_venue and not filter_blob_by_criteria(blob_name, venues, instrument_ids=None):
        continue
if instrument_ids and not any(iid in blob_name for iid in instrument_ids):
    continue
files.append(blob_name)
```

The `instrument_ids` check is **its own gate**, applied unconditionally when set. Substring match against the blob path
is sufficient when filenames carry the instrument id (`.../BTCUSDT.parquet` matches `instrument_ids=["BTCUSDT"]`).

## Why "list, then write-time check" is not defence-in-depth

If the list stage is correctly scoped, the write-time filter is unreachable for non-matching rows. Keeping the
write-time filter is fine, but it cannot substitute for the list-time filter — every blob the scanner returns incurs
full download + Polars load before the write decision.

## How to verify the fix

**Unit test**: invoke the scanner with a multi-venue + narrow-instrument scope, mock the storage client to return a
realistic blob set (10+ instruments per venue), assert exact count of returned files. The pre-fix code returns
`N_venues × N_instruments_per_venue`; the post-fix code returns `N_venues × N_requested_instruments`. Reference:
[`market-data-processing-service/tests/unit/test_orchestration_scanner.py`](../../../market-data-processing-service/tests/unit/test_orchestration_scanner.py).

**Operational test**: re-run the same narrow-scope backfill on a modest VM (`e2-standard-8` / 32 GB is the realistic
floor — `e2-standard-4` / 16 GB OOMs on the 526 MB prod availability_index parquet load before the scanner runs). The
scanner log line `Listed N files from BUCKET/prefix for data_type=DT` MUST report `N` ≤
`N_venues × N_requested_instruments` on the inner `process_category` call. If `N` is closer to
`N_venues × all_instruments_in_those_venues`, the fix is incomplete.

**Note**: there is also a pre-count `list_instrument_files` call at the tracker setup (`process_handler.py:383` for
MDPS) that passes only `venues` and reports a wider N — this is a tracker-display imprecision, not the bug. The relevant
log is the one fired from inside `process_category` after `✅ Loaded N {asset_group} instruments from GCS`.

## Reference implementation

- `market-data-processing-service/market_data_processing_service/app/core/orchestration_scanner.py:441-457` (post-fix
  shape; landed at MDPS commit `e47205d`)
- `market-data-processing-service/market_data_processing_service/app/core/orchestration_scheduling.py:243`
  (sibling-correct shape — `filter_blob_by_criteria` called unconditionally; predates the scanner fix and includes an
  inline comment about the related 2026-05-05 incident)
- `market-data-processing-service/tests/unit/test_orchestration_scanner.py` (regression coverage; 6 tests pin the
  4-vs-18 + 2-vs-3 deltas as fail-on-regression)

## Incidents

- **2026-05-28 narrow-scope smoke** (operator laptop, 93 GB): 4 instruments × 1 data_type × 1 day reached 75.2% of 93 GB
  RAM (~70 GB) before operator-kill. Scanner returned ~200 blobs instead of 4 because `instrument_ids` was silently
  dropped on venue-prefix match.
- **2026-05-28 full-scope CeFi VM hang** (`mdps-backfill-cefi-20260528-112956`, e2-standard-8 / 32 GB): 2 of N
  instruments processed in 40 min, then hang. No `--venues` was set, so both filters were skipped entirely; scanner
  returned every parquet for the day.
- **2026-05-05 chain-bundle silent absorption** (related but different): an earlier listing path mis-routed non-chain
  blobs through the chain adapter when the data_type partition was empty. Fixed at `orchestration_scheduling.py:217+` by
  calling `filter_blob_by_criteria` unconditionally — same shape the scanner later landed.

## Cross-service generalization

Other batch services with the same `list → filter → load → process → write` pipeline shape that should be audited for
read-time filter discipline:

- `features-delta-one-service`, `features-cross-instrument-service`, `features-multi-timeframe-service` — consume
  processed candles, filter by archetype/instrument set
- `features-onchain-service` — consumes raw on-chain ticks, filters by chain/protocol/pool
- `instruments-service` reconciler scripts — list raw instrument-availability parquets, filter by asset_group
- `batch-live-reconciliation-service` — list manifest rows for comparison, filter by service/asset_group

For each, the audit recipe is: trace the listing call (typically a `storage_client.list_blobs(prefix=...)` followed by a
per-blob filter loop), then confirm the per-blob filter applies ALL operator-requested scope dimensions, not just the
partition-level ones.

## Composes with

- [`codex/04-architecture/shard-level-failure-isolation.md`](../04-architecture/shard-level-failure-isolation.md) —
  per-shard scoping (a different scope axis)
- [`codex/02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) —
  write-side honest-absence (unrelated; this rule is read-side)

## Reference plan

[`plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`](../../plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md).
