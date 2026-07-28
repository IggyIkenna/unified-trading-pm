---
doc_type: issue
title:
  "read_availability_index(columns=..., filters=...) silently returns an empty DataFrame on ANY ValueError/OSError/
  FileNotFoundError from its GCS-read path — including a caller misconfiguration (missing GCP_PROJECT_ID) — instead of
  surfacing the real error, indistinguishable from a genuinely-empty index"
summary: >-
  `_read_availability_index_slim` in `unified_trading_library/manifest_writer/_read_index.py` (both the filters= branch,
  lines ~704-705, and the non-filters branch, lines ~758-759) wraps its GCS-client-acquisition +ead call in `except
  (FileNotFoundError, OSError, ValueError, pd.errors.ParserError): return pd.DataFrame(columns=columns)`. Reproduced
  live: calling `get_storage_client()` with no `GCP_PROJECT_ID`/`AWS_ACCOUNT_ID` in the environment raises `ValueError:
  GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in environment` — this is caught by the broad except and silently
  converted to an empty-index result, indistinguishable from "the bucket genuinely has zero rows for this filter." The
  underlying parquet in this repro had 27,811 real rows (358 matching the caller's date filter) — a config error
  masqueraded as "no data."
status: resolved
nature: issue
asset_group: [meta]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [data-correctness, silent-placeholder, manifest, read-path, error-handling]
related: [plans/active/is_daily_enum_capture_heal_2026_07_07.md]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source:
  [
    "Surfaced while verifying a real backfill's manifest rows (slot-2, 2026-07-27) — a standalone verification script
    forgot to export GCP_PROJECT_ID, and read_availability_index reported 0 rows for a bucket that had 27,811.",
  ]
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by: unified-trading-library@0db19a72
---

> **🟢 RESOLVED 2026-07-28** — `_read_availability_index_slim`'s both branches (filters= and columns-only) now resolve
> `get_storage_client()` OUTSIDE the broad `except (FileNotFoundError, OSError, ValueError, pd.errors.ParserError)`, so
> a config `ValueError` from `get_project_id()` (missing `GCP_PROJECT_ID`/`AWS_ACCOUNT_ID`) propagates instead of being
> folded into "index empty". Genuine GCS-404/corrupt-parquet-returns-empty behavior is unchanged (locked by new
> regression tests). Shipped together with the sibling
> `manifest_reader_silent_empty_on_missing_project_id_2026_07_24.md` fix (same code path) —
> `unified-trading-library@0db19a72`, `quality-gates.sh` green.

# `read_availability_index` silently swallows config/read errors as "empty index"

## 1. What I found

`_read_availability_index_slim`'s `filters=` branch:

```python
except (FileNotFoundError, OSError, ValueError, pd.errors.ParserError):
    return pd.DataFrame(columns=columns)
```

(and the equivalent non-filters branch a few dozen lines below). This `try` wraps `get_storage_client()` +
`_read_consolidated_if_fresh` + `_read_self_shard` + `_merge_shard_frames`. A live repro: running a standalone script
against `instruments-store-pred-prd-central-element-323112` with `columns=`/`filters=` set but NO `GCP_PROJECT_ID`
exported raised, inside `get_storage_client()`:

```
ValueError: GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in environment
```

`_read_availability_index_slim` caught this (it's a `ValueError`) and returned an empty `DataFrame` — no exception, no
log line, no signal that anything was wrong. Downloading and parsing the SAME underlying parquet directly (bypassing
this function) confirmed 27,811 real rows, 358 matching the filter. The config error was completely invisible to the
caller.

## 2. Why it matters

This directly contradicts the workspace's own stated design intent elsewhere in the SAME file —
`_raise_shards_exist_but_unreadable`'s docstring explicitly calls out "Silently returning an empty DataFrame here is the
exact silent-placeholder anti-pattern the stale-consolidator raise above otherwise guards against" — but the
`filters=`/`columns=` slim-read path's own broad except does exactly that for a WIDER class of errors (any `ValueError`,
not just a stale-consolidator condition). A production caller with a missing/misconfigured `GCP_PROJECT_ID` (a deploy
regression, a bad env-var rollout, a misconfigured local repro script like the one that found this) would get a silent
"no data" result instead of a loud, actionable error — masking exactly the kind of regression
`/codex/02-data/honest-absence-downstream-handling.md` exists to prevent.

## 3. Recommended fix (not yet implemented — needs a maintainer familiar with this module's full call-site surface)

Narrow the except to genuinely GCS-404-shaped conditions only (mirroring the pattern already used a few lines up in
`_read_and_merge_per_vm_shards` / `_read_self_shard`, which check
`exc_name in ("NotFound", "Forbidden") or "404" in str(exc)` before treating an exception as "absent"), and let a bare
`ValueError` from `get_storage_client()` (or any other non-GCS-404 cause) propagate. This is NOT a one-line fix to apply
blind: `_read_parquet_columns_safe` itself raises `ValueError` internally as an EXPECTED legacy-schema-fallback signal
in one caller path — narrowing the outer except without checking every call site that currently relies on this catch-all
could introduce a regression. Scope this as its own small task with the existing UTL manifest-writer test suite as the
safety net.

## 4. Open work

- [x] ✅ [CODE] P2. Narrow `_read_availability_index_slim`'s broad `except (..., ValueError, ...)` (both branches) to
      genuine GCS-not-found conditions only, matching the `exc_name in ("NotFound", "Forbidden") or "404" in str(exc)`
      pattern already used elsewhere in this file; verify no existing caller relies on the current catch-all behaviour
      for a legitimate non-404 case (repo: unified-trading-library). — **DONE 2026-07-28**:
      `unified-trading-library@0db19a72`. Actual fix shape differs slightly from the letter of this todo (safer, same
      intent): rather than rewriting the except tuple itself (which still legitimately needs to catch a genuine
      corrupt-parquet `ValueError` from the fallback read in `_read_parquet_columns_safe`), `get_storage_client()` is
      now resolved OUTSIDE the try in both branches, so the config `ValueError` never reaches the except at all —
      narrower in effect without touching the genuine-404/corrupt-parquet path. Verified no existing caller relies on
      the old catch-all-swallows-config-errors behavior: full `quality-gates.sh` green (all pre-existing tests pass
      unchanged) plus new regression tests locking BOTH contracts (config ValueError raises; genuinely-missing-bucket
      still returns empty) in `tests/unit/test_manifest_read_index_slim.py`.

## 5. Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` — why a silent-empty read masking a real error is a
  data-correctness regression, not a cosmetic bug.
