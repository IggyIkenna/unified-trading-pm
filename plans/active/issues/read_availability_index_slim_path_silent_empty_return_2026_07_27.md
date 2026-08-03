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
status: resolved
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
    /plans/archive/issues/read_availability_index_slim_silent_valueerror_swallow_2026_07_27.md,
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
resolved_by: unified-trading-library@0db19a72, unified-trading-library@3b72245a
locked_by:
context_scope:
  [
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /plans/active/issues/read_availability_index_bare_defi_callers_2026_07_27.md,
    /plans/archive/issues/read_availability_index_unfiltered_callsite_audit_2026_07_26.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

> **🟢 RESOLVED 2026-08-03** — root-caused as the SAME defect class as the sibling
> `read_availability_index_slim_silent_valueerror_swallow_2026_07_27.md` (filed the same day, different session, never
> cross-referenced until now): `_read_availability_index_slim`'s no-`filters=` branch resolved `get_storage_client()`
> **inside** its broad `except (FileNotFoundError, OSError, ValueError, pd.errors.ParserError)`. UTL's
> `get_storage_client()` → `get_project_id()` raises a plain `ValueError` when `GCP_PROJECT_ID`/`AWS_ACCOUNT_ID` is
> unset in the environment — unlike a raw `google.cloud.storage.Client()` (which needs no such env var and worked fine
> in the original repro session), so "bucket access confirmed working via the raw client" and "the UTL wrapper silently
> returned empty" are NOT a contradiction once you know the wrapper enforces a stricter precondition the raw client
> doesn't. That `ValueError` was silently swallowed by the broad except and returned as `pd.DataFrame(columns=columns)`
> — indistinguishable from a genuinely-empty manifest. Already fixed in `unified-trading-library@0db19a72` (2026-07-28,
> one day after this doc was filed) as part of closing the sibling issue, which explicitly resolved BOTH
> `_read_availability_index_slim` branches (filters= and columns-only) by moving `get_storage_client()` outside the try.
> Verified via a fresh live repro against the SAME cefi bucket (see Progress Log) —
> `read_availability_index(columns= [...])` now correctly returns 9,351,748 rows (manifest has grown from 8,742,430 rows
> on 2026-07-27). Added the explicit row-count-parity regression test this doc's Todo 2 asked for
> (`test_slim_read_row_count_matches_full_read`) to pin the CONTRACT itself, not just the one known cause —
> `unified-trading-library@3b72245a`.

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

- [x] ✅ [DATA] P2. **unified-trading-library** — root-cause why `read_availability_index(bucket, columns=[...])` (no
      `filters=`) returned an empty DataFrame against the fresh, valid cefi manifest blob described above. Reproduce
      live against the SAME bucket first (the manifest changes daily — re-verify the repro still holds before
      diagnosing). Trace `_read_availability_index_slim`'s no-filters branch (`_read_consolidated_if_fresh` →
      `_read_self_shard` → `_merge_shard_frames`, falling back to `_read_slow_path`) to find which step returned
      `None`/empty and why. (repo: unified-trading-library) — **DONE 2026-08-03** (slot-12, data_engineering): live
      re-repro no longer reproduces (see Progress Log); root-caused via code tracing + cross-reference to the sibling
      `read_availability_index_slim_silent_valueerror_swallow_2026_07_27.md` issue — `get_storage_client()` was resolved
      INSIDE the branch's broad `except (..., ValueError, ...)`, so a config `ValueError` from `get_project_id()`
      (missing `GCP_PROJECT_ID`/`AWS_ACCOUNT_ID`, which the raw `google.cloud.storage.Client()` used in the original
      repro's cross-check does NOT require) was silently folded into "empty index". Already fixed 2026-07-28 in
      `unified-trading-library@0db19a72` — one day after this doc was filed, by a different session closing the sibling
      issue, without cross-referencing this doc.
- [x] ✅ [DATA] P2. **unified-trading-library** — once root-caused, either fix the silent-empty path to loud-fail
      (mirror `_raise_shards_exist_but_unreadable`'s pattern elsewhere in this same file — shards/data known to exist
      but a read path returns nothing IS a genuine failure, not honest absence) or fix the underlying read defect
      directly; add a regression test pinning "columns= fast path returns the same row count as the unprojected full
      path against a real/fixture manifest" so this can't silently regress again. (repo: unified-trading-library) —
      **DONE 2026-08-03** (slot-12, data_engineering): underlying defect already fixed by
      `unified-trading-library@0db19a72` (client resolved outside the try — see Todo 1);
      `test_slim_read_raises_on_missing_gcp_project_id` already pins that exact cause for this branch. Added the
      explicit parity test this todo asked for — `test_slim_read_row_count_matches_full_read`
      (`tests/unit/test_manifest_read_index_slim.py`) — asserting `len(slim_result) == len(full_result)` on a shared
      fixture, so ANY future defect that makes the slim path drop rows (not just this specific historical cause) is
      caught, not only the one already-covered cause. Full `quality-gates.sh` green. Shipped:
      `unified-trading-library@3b72245a`.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries, unchanged — reviewed against current doc
  content and still accurate).
- **2026-08-03 (slot-12, data_engineering)**: Re-verified live against the SAME cefi bucket
  (`market-data-tick-cefi-prd-central-element-323112`) per Todo 1's own instruction to re-repro before diagnosing. The
  bug does **NOT** reproduce anymore:
  `read_availability_index(bucket, columns=["date","venue","data_type", "capture_status","instrument_count"])` now
  correctly returns 9,351,748 rows (manifest has grown from the 8,742,430 rows the original repro cited on 2026-07-27;
  blob `updated=2026-08-03T17:07:19Z`, 166 MB). Traced the no-filters branch step by step (`_read_self_shard` → `None`
  as expected, no self-shard on this VM; `_read_consolidated_if_fresh` → returns the full 9.35M-row frame directly, no
  fallback to `_read_slow_path` needed) — every step behaves correctly today. Also directly tested the OLD
  unconditional-widening behavior (the 19/20-column `_SLIM_MERGE_BASE_COLS | columns` set
  `_read_availability_index_slim` used before `unified-trading-library@65ae1e89`'s 2026-08-01 OOM fix) by calling
  `_read_consolidated_if_fresh` with the widened column list directly against the live bucket — it also succeeds cleanly
  (9,351,748 rows, ~7s, no memory issue at cefi's current scale) — ruling out the widening itself as the root cause of
  THIS bug (it was a genuine, separate defect, but not this one). Grepped `plans/active/` + `plans/archive/issues/` for
  anything already covering this code region and found
  `read_availability_index_slim_silent_valueerror_swallow_2026_07_27.md` (archived, RESOLVED via
  `unified-trading-library@0db19a72`, 2026-07-28) — filed the SAME day as this doc by a different session, hitting the
  identical code path (`_read_availability_index_slim`'s no-filters branch) via a different trigger (missing
  `GCP_PROJECT_ID` specifically, discovered via a standalone script that forgot to export it) but the exact SAME defect
  shape: `get_storage_client()` resolved inside the broad
  `except (FileNotFoundError, OSError, ValueError, pd.errors.ParserError)`, so its `ValueError` (from
  `get_project_id()`, `unified_trading_library/cloud_interface/ constants.py:69`) silently returned as empty. Confirmed
  via `git show 0db19a72 -- unified_trading_library/ manifest_writer/_read_index.py`: the fix moves
  `get_storage_client()` OUTSIDE the try in all three call sites (`read_availability_index`, both
  `_read_availability_index_slim` branches), and per that commit's own message it was shipped specifically to close the
  sibling issue's todo. This doc's own repro session almost certainly hit the identical cause: the raw
  `google.cloud.storage.Client()` cross-check in the original repro does NOT require `GCP_PROJECT_ID` (project resolves
  from ADC), while UTL's `get_storage_client()` → `get_project_id()` strictly requires the env var — exactly reconciling
  "bucket access confirmed working" with "the wrapper returned empty" that the original doc flagged as puzzling.
  Existing regression test `test_slim_read_raises_on_missing_gcp_project_id` (added by 0db19a72) already pins this exact
  cause for this exact branch. Added one more test this doc's Todo 2 explicitly asked for —
  `test_slim_read_row_count_matches_full_read` — a direct slim-vs-full row-count parity check on a shared 5-row fixture,
  so the CONTRACT (not just the one now-fixed cause) is locked. All 31 tests in
  `tests/unit/test_manifest_read_index_slim.py` pass.
