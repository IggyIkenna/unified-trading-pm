---
doc_type: issue
title: "MDPS manifest-consolidated staleness check appears inverted (age=6s flagged as >86400s)"
summary: >
  Intermittent `Error writing candles to GCS: Consolidated availability_index ... is stale (age=6s, older than
  MANIFEST_CONSOLIDATED_STALENESS_SEC=86400s)` during BITGET-FUTURES 1h backfill. The reported age (6s) is far below the
  threshold (86400s), suggesting the staleness comparison logic is inverted or comparing the wrong values. Intermittent
  — 6/250+ writes fail (2.4%).
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [data-correctness, mdps, manifest, bug]
related: [/plans/active/cefi_consolidated_closeout_2026_07_18.md]
parent_epic: infrastructure_master
source:
  "Observed in VM mdps-backfill-cefi-20260810-115835 run.log during BITGET-FUTURES 1h backfill monitoring (2026-08-10)"
assigned_vm: NA
resolved_by: unified-trading-library@26294ddf71
locked_by:
created: 2026-08-10
priority: P3
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

## Evidence

From VM `mdps-backfill-cefi-20260810-115835` run.log, BITGET-FUTURES 1h backfill for 2026-04-20..04-30:

```
Error writing candles to GCS: Consolidated availability_index for
bucket='market-data-tick-cefi-prd-central-element-323112' is stale
(age=6s, older than MANIFEST_CONSOLIDATED_STALENESS_SEC=86400s)
```

- **age=6s** — the manifest was refreshed 6 seconds ago (fresh)
- **threshold=86400s** — staleness threshold is 24 hours
- 6s < 86400s → should NOT trigger staleness rejection
- Intermittent: 6 failures out of 250+ writes (~2.4%); most writes to the same bucket succeed

## Impact

Low — most writes succeed. But the underlying comparison bug could cause more failures under different timing conditions
or manifest-consolidator refresh patterns.

## Root Cause (diagnosed 2026-08-10)

**The staleness comparison is NOT inverted.** The real issue is a misleading error message triggered by a transient
GCS/parquet read failure:

1. `_read_consolidated_if_fresh()` (UTL `manifest_writer/_read_index.py:1156`) correctly checks `age > staleness_sec` —
   age=6s, staleness=86400s → 6 > 86400 = False → blob IS fresh. But a **transient GCS download or parquet parse error**
   (`OSError`/`ValueError`/`ParserError` caught at line 1167) causes it to return `None`.
2. The slow path (`_read_slow_path` → `_resolve_stale_or_missing_consolidated_blob`) independently re-reads the blob
   metadata via `_consolidated_blob_age_sec()` → age=6s.
3. Per-VM shards exist → the check `age < staleness_budget * 5` passes → raises `ManifestConsolidatorStaleError` with
   the misleading message "age=6s, older than MANIFEST_CONSOLIDATED_STALENESS_SEC=86400s". The blob is NOT "older than"
   the threshold — the message conflates the severity-classification check (`age < staleness_budget * 5`, i.e. "stale"
   vs "DOWN") with the actual staleness gate (`age > staleness_sec`).
4. Intermittent at 2.4% (6/250+) because it depends on a transient GCS/parse error in the fast path.

## Fix (shipped)

- [x] ✅ [DATA] P3. Retry consolidated read in slow path when blob is actually fresh (`age < staleness_budget`) + fix
      misleading error message — `unified-trading-library@26294ddf71`. - When the consolidated blob is within the
      freshness window, retry `_read_consolidated_if_fresh` once before raising — the blob IS fresh and the initial
      failure is almost certainly transient. - Changed error message from "older than
      MANIFEST_CONSOLIDATED_STALENESS_SEC" to "staleness threshold MANIFEST_CONSOLIDATED_STALENESS_SEC" since the blob
      may not actually be older than the threshold. - File:
      `unified_trading_library/manifest_writer/_read_index.py:335-357`
