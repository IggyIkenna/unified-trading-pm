---
doc_type: issue
title:
  "`read_availability_index(bucket, columns=[...])` (no `filters=`) silently returned an empty DataFrame against a live,
  fresh, 8.7M-row cefi manifest — the raw parquet read of the SAME blob returned all rows correctly"
summary: >-
  While investigating the HYPERLIQUID backfill-gap todo (coverage_floor_registries_no_cross_propagation_2026_07_17.md),
  called `read_availability_index("market-data-tick-cefi-prd-central-element-323112", columns=["date","venue",
  "data_type","capture_status","instrument_count"])` (the documented slim-read fast path, no `filters=` kwarg) and got
  `total rows: 0`. A direct `google.cloud.storage` download + `pd.read_parquet` of the exact same blob
  (`_index/availability_index.parquet`, 142 MB, `updated=2026-07-27T08:30:25Z` — fresh, not stale) returned 8,742,430
  rows including thousands of HYPERLIQUID rows. The manifest was NOT stale and the bucket credentials/access were
  confirmed working (a `google.cloud.storage.Client()` listed the bucket fine in the same session) — so this was not a
  simple auth/staleness non-issue, yet the slim path returned empty with NO error, warning, or log visible to the
  caller. Not root-caused in this session (out of scope for the HYPERLIQUID todo this was found under) — filed as its
  own trackable finding per the workspace's "every deferral becomes a todo" rule rather than left as a passing mention.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [manifest, read-availability-index, data-correctness, silent-placeholder, honest-absence, slim-read]
related:
  [
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /plans/active/issues/read_availability_index_bare_defi_callers_2026_07_27.md,
    /plans/archive/issues/read_availability_index_unfiltered_callsite_audit_2026_07_26.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P2
source:
  "data_engineering worker (slot-11, planning VM), 2026-07-27, AO task
  coverage_floor_registries_no_cross_propagation-006 — hit while probing the live cefi manifest for the HYPERLIQUID
  backfill-gap investigation; not the task's own scope, so root-cause deferred and filed here instead."
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
context_scope: [unified-trading-library/unified_trading_library/manifest_writer/_read_index.py, /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md, /plans/active/issues/read_availability_index_bare_defi_callers_2026_07_27.md, /plans/archive/issues/read_availability_index_unfiltered_callsite_audit_2026_07_26.md, /codex/02-data/availability-manifest-and-data-status.md]
---

# `read_availability_index` slim path returns empty against a fresh, valid manifest — no error surfaced

## What I found

Repro (this session, live prod):

```python
from unified_trading_library.manifest_writer._read_index import read_availability_index
df = read_availability_index(
    "market-data-tick-cefi-prd-central-element-323112",
    columns=["date", "venue", "data_type", "capture_status", "instrument_count"],
)
len(df)  # -> 0
```

vs. a direct read of the identical blob, same session, same credentials:

```python
from google.cloud import storage
import pandas as pd, io
client = storage.Client()
blob = client.bucket("market-data-tick-cefi-prd-central-element-323112").blob("_index/availability_index.parquet")
df = pd.read_parquet(io.BytesIO(blob.download_as_bytes()))
len(df)  # -> 8,742,430
```

The blob's `updated` timestamp was `2026-07-27T08:30:25Z` — same day, hours-fresh, not remotely stale by any reasonable
staleness threshold. Bucket access itself was confirmed working independently (listed bucket contents fine via the same
`google.cloud.storage.Client()` in the same process).

**Not root-caused** — this was found incidental to a different task (the HYPERLIQUID coverage-floor investigation) and
chasing it fully was out of that task's scope. The call routes through
`unified_trading_library/manifest_writer/_read_index.py::_read_availability_index_slim` (the `columns=` fast path
without `filters=`, lines ~712-764 as of this session) — it tries `_read_consolidated_if_fresh`, falls back to
`_read_slow_path` (per-VM shard merge) on `None`, and returns an empty `pd.DataFrame(columns=columns)` **silently** (no
raised exception, no logged warning visible to the caller) if BOTH paths come back empty/`None`. Whether the actual
failure is in the staleness check, the per-VM shard fallback, or something else in that chain was not verified live —
that verification is this todo's job.

## Why it matters

- **Silent-placeholder-adjacent**: a caller trusting this function's return value (empty DataFrame = "no data") would
  wrongly conclude a well-populated manifest is empty — the exact honest-absence-vs-genuine-failure conflation this
  workspace's data-correctness rules exist to prevent, except here it's a READ-side bug, not a write-side one.
  Downstream: any `/data-freshness` skill invocation, coverage audit, or backfill orchestrator pre-skip check that uses
  the `columns=` fast path (rather than the full unprojected read) could be silently making decisions against a
  phantom-empty view of a manifest that is actually full.
- **Two adjacent, already-filed issue docs** (`read_availability_index_bare_defi_callers_2026_07_27.md`,
  `read_availability_index_unfiltered_callsite_audit_2026_07_26.md`) cover a DIFFERENT defect class in the same module
  family (OOM from repeated full/unprojected reads) — this is a distinct correctness bug (silent empty return on the
  PROJECTED/slim path), not a duplicate of either.

## Todos

- [ ] [DATA] P2. **unified-trading-library** — root-cause why `read_availability_index(bucket, columns=[...])` (no
      `filters=`) returned an empty DataFrame against the fresh, valid cefi manifest blob described above. Reproduce
      live against the SAME bucket first (the manifest changes daily — re-verify the repro still holds before
      diagnosing). Trace `_read_availability_index_slim`'s no-filters branch (`_read_consolidated_if_fresh` →
      `_read_self_shard` → `_merge_shard_frames`, falling back to `_read_slow_path`) to find which step returned
      `None`/empty and why. (repo: unified-trading-library)
- [ ] [DATA] P2. **unified-trading-library** — once root-caused, either fix the silent-empty path to loud-fail (mirror
      `_raise_shards_exist_but_unreadable`'s pattern elsewhere in this same file — shards/data known to exist but a read
      path returns nothing IS a genuine failure, not honest absence) or fix the underlying read defect directly; add a
      regression test pinning "columns= fast path returns the same row count as the unprojected full path against a
      real/fixture manifest" so this can't silently regress again. (repo: unified-trading-library)

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
