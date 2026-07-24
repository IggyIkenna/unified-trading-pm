---
doc_type: issue
title:
  read_availability_index() silently returns empty DataFrame when GCP_PROJECT_ID is unset (masquerades as "manifest
  empty")
summary: >-
  read_availability_index()'s broad exception handler folds a config ValueError (GCP_PROJECT_ID unset) into the same
  "index empty" return as a genuine GCS 404/missing-bucket/corrupt-parquet — a silent-placeholder anti-pattern found
  while verifying the sfi_progressive_features backfill (sports_closeout_batch1_ao_ready_2026_07_24.md todo 4), where it
  produced a false "manifest write didn't land" alarm before a raw parquet read proved the data was fine.
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [manifest, silent-empty, honest-absence, read-path]
related: [/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md]
parent_epic: manifest_master
priority: P3
created: "2026-07-24"
assigned_vm: NA
source: [sports_closeout_batch1_ao_ready_2026_07_24.md todo 4]
locked_by:
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# read_availability_index() silent-empty on missing GCP_PROJECT_ID

## What I found

While verifying a manifest census for `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 4, calling
`unified_trading_library.read_availability_index(bucket)` from an ad-hoc diagnostic shell (env had
`GOOGLE_CLOUD_PROJECT` set but not `GCP_PROJECT_ID`) returned an empty DataFrame with the correct schema — no exception,
no log line. This read as "the manifest genuinely has zero rows for this feature_group", which is a false signal: the
underlying `_index/availability_index.parquet` object was 4.5MB / 242,030 rows the whole time.

Root cause: `get_storage_client()` (called internally by `_read_consolidated_if_fresh` / `_read_slow_path` inside
`read_availability_index`) raises `ValueError("GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in environment")` when that
specific env var is absent (`unified_trading_library/cloud_interface/constants.py::get_project_id`). That `ValueError`
is a plain `ValueError`, and `read_availability_index`'s outer exception handler
(`unified_trading_library/manifest_writer/_read_index.py` ~line 594) catches
`(FileNotFoundError, OSError, ValueError, pd.errors.ParserError)` and returns `_empty` for ALL of them — treating a
config error identically to "GCS 404 / missing bucket / corrupt parquet". Setting `GCP_PROJECT_ID` in the shell resolved
it immediately (confirmed the real row count via a raw `client.download_bytes()` + `pd.read_parquet()` read).

## Why it matters

This is the same silent-placeholder anti-pattern the workspace explicitly bans elsewhere (honest-absence rules,
`record_empty()`'s now-mandatory typed `reason=`) — a config/environment error and a genuine "nothing captured yet"
state are indistinguishable to every caller of `read_availability_index()`. A backfill script itself uses this same
function for its skip-cache (`_build_captured_set` pattern); if a VM ever launched with `GCP_PROJECT_ID` unset (e.g. a
bootstrap-script env regression), it would silently re-process every date instead of loud-failing, and any
diagnostic/verification session hitting the same gap would draw a false "manifest empty" conclusion — costing real
debugging time here (this exact false alarm was chased for several minutes before the actual cause was found).

## Recommended decision

Narrow the outer `except` in `read_availability_index` (and its slim-path sibling) so a `ValueError` raised by
`get_project_id()`/config resolution is NOT folded into "index empty" — either re-raise it distinctly, or catch it by
name/message before the broad tuple, so a misconfigured environment fails loud instead of reading as honest absence. Low
severity / P3 (never observed in a real VM launch, only in an ad-hoc diagnostic shell), but worth fixing
opportunistically by whoever next touches `unified_trading_library/manifest_writer/_read_index.py`.

## Todos

- [ ] [CODE] P3. In `unified_trading_library/manifest_writer/_read_index.py`'s `read_availability_index` (and its
      slim-path sibling), stop catching config/environment `ValueError`s (e.g. `get_project_id()`'s
      `"GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set"`) inside the broad
      `except (FileNotFoundError, OSError,     ValueError, pd.errors.ParserError): return _empty` — only GCS-shaped
      absence (404/missing bucket/corrupt parquet) should read as "index empty"; a config error should raise loudly.
      **Done when**: a unit test asserts that calling `read_availability_index` with `GCP_PROJECT_ID`/`AWS_ACCOUNT_ID`
      unset raises instead of returning an empty DataFrame, and existing 404/corrupt-parquet-return-empty tests still
      pass. (repo: unified-trading-library)
