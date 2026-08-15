---
doc_type: issue
title:
  GET /axis-value-census?service=market-data-processing-service reads the WHOLE shared bucket then filters client-side —
  multi-minute hang where a pushdown filter is 8.6s
summary: >-
  While running `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s "Run distinct-values/axis-value census"
  todo, calling `get_axis_value_census(service="market-data-processing-service", asset_group="tradfi")` directly
  (in-process, no live server) did not complete within a 480s bounded budget. Isolating the cause: the endpoint reads
  the FULL shared MTDS/MDPS `availability_index` for the (service, asset_group) bucket (13.7M+ rows for tradfi) via
  `_ds._read_availability_index(bucket, columns=[...])` with only a `capture_status != attempted_failed` filter, THEN
  filters to `service_name == "market-data-processing-service"` in pandas afterward (`_filter_to_candle_rows`).
  Re-running the identical read with the `service_name` equality pushed into `read_availability_index`'s own `filters=`
  parameter (predicate pushdown) instead completed in 8.6s and returned the same 6,332,575-row result. A live caller of
  this endpoint (e.g. the deployment-ui `AxisValueCensus` panel, or any future automated census run) would hit the same
  multi-minute-plus hang / likely HTTP request timeout every time this endpoint is called for the MDPS candle-layer
  scope.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api]
scope: [engineer]
tags: [performance, axis-value-census, filter-pushdown, deployment-api, data-status]
related:
  [
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-15
author: slot-6 (backend_engineer)
source:
  [
    "tradfi_satellite_ao_dispatch_batch13-f6e63667d3c4, Run distinct-values/axis-value census for tradfi and confirm 0
    non-canonical values",
  ]
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-15
parent_epic: manifest_master
priority: P2
---

# axis-value-census MDPS scope: push service_name into the read filter instead of a post-read pandas filter

## What I found

`deployment-api/deployment_api/routes/data_status/_axis_census.py::get_axis_value_census` reads columns
`AXIS_CENSUS_COLUMNS + ["service_name"]` from the shared MTDS/MDPS bucket with only
`filters=[("capture_status", "!=", "attempted_failed")]`, then calls `_filter_to_candle_rows(df)` — a plain pandas
boolean-mask filter on the already-fully-materialized DataFrame — when `service == "market-data-processing-service"`.
For tradfi this means reading all 13,748,571 rows before discarding ~54% of them (6,332,575 remain after the MDPS
filter). Measured live (2026-08-15): the unfiltered read + client-side filter did not finish inside a 480s budget (2
separate attempts, both killed); the identical read with `("service_name", "==", "market-data-processing-service")`
added to the `filters=` list passed straight to `unified_trading_library.read_availability_index` completed in 8.6s,
same row count.

`read_availability_index` already supports arbitrary pyarrow-style filter tuples (used elsewhere in this same file for
`capture_status`), so this is a mechanical fix, not a new capability. One open question before shipping: `service_name`
is a v6+ manifest column — legacy pre-column shards get it backfilled to `""` by the reader's honest-absence convention
(per this module's own docstring). Need to confirm the reader applies that backfill BEFORE evaluating pushdown filters
(so legacy rows correctly fail the `== "market-data-processing-service"` filter, same as today's post-backfill pandas
comparison) rather than the filter being evaluated at the raw-file-schema level pre-backfill (which could silently
exclude legacy-schema files' rows from the result entirely, if `read_availability_index`'s pyarrow engine drops filter
predicates on files lacking that column instead of treating it as `""`). Not verified in this pass — flagged as the one
thing to check before landing this, not assumed safe.

## Why it matters

Any live caller of `GET /axis-value-census?service=market-data-processing-service&...` — the deployment-ui
`AxisValueCensus` panel, or a future automated distinct-values census run — hits this same multi-minute-plus read on
every request for any asset_group with a large enough MTDS+MDPS shared bucket. That is very likely to exceed a normal
HTTP request timeout in production, making the MDPS scope of this panel effectively broken/unusable today, not just
slow.

## Recommended decision

Not fixed here (a small, scoped code change discovered mid-verification of an unrelated todo — filed per findings triage
rather than folded into a quick-verify task). Bounded fix:

## Findings (confirmed 2026-08-15, slot-9 backend_engineer)

**Answer: the reader does NOT apply the honest-absence column-backfill before evaluating pushdown filters — but
`service_name` specifically is not at risk in practice, so the proposed fix (todo 2) is safe to ship.**

Traced the exact filter-application code path in `unified_trading_library/manifest_writer/_read_index.py`:

1. `_read_availability_index_slim`'s `filters:` branch (`_read_index.py:1003-1050`) calls `_read_consolidated_if_fresh`
   / `_read_self_shard` / (via `_read_slow_path`) `_read_and_merge_per_vm_shards` — every one of these calls
   `_read_parquet_columns_safe(data, columns, filters)` directly on the RAW per-file bytes
   (`_read_index.py:1181, 1206, 1241, 1469, 1710`). `_backfill_slim()` runs only AFTER these calls return, on the
   already-merged DataFrame (`_read_index.py:1019, 1043`) — i.e. **filters are evaluated against each file's raw,
   pre-backfill schema, not the backfilled value.**
2. Inside `_read_parquet_columns_safe` (`_read_index.py:87-195`): when a filtered column is absent from a given file's
   raw schema, pyarrow raises `ArrowInvalid` (a `ValueError`), caught and retried with `columns` narrowed to the file's
   actual columns — but `filters` still references the missing column, so the retry raises again, and the code falls
   through to a full unfiltered read + manual pandas re-filter (`_read_index.py:183-195`). There,
   `if col not in full.columns: continue` — **the missing-column filter condition is SILENTLY SKIPPED for that file, not
   evaluated against a backfilled `""` default.** Net effect for a genuinely-missing filter column: every row in that
   file passing the OTHER filters is included regardless — an over-inclusion risk (opposite of the under-inclusion this
   issue's "Open question" speculated).
3. However, `service_name` is NOT actually at risk of hitting that gap: `AvailabilityRecord.service_name`
   (`unified_trading_library/manifest_writer/_rows.py:169`, listed under that dataclass's own
   `# Universal (always populated)` heading, schema v4+ per its docstring) and `ManifestRow.service_name` are both
   REQUIRED fields with no default — part of the row-identity/dedup key `(date, venue, data_type, service_name)`
   (`_read_index.py:66-67`'s `_SLIM_MERGE_BASE_COLS` comment literally calls these "the hard-required base 4";
   `_writer_io.py:1336` uses the same 4-col key for dedup). Every row the writer has ever emitted carries a real
   `service_name` value — there is no code path that writes a row without it, so the "v6+ column, legacy shards backfill
   it" premise in this doc's original "Open question" was incorrect (verified against the writer's row schema, not
   assumed).

**Conclusion for todo 2**: pushing `("service_name", "==", _CANDLE_SERVICE_NAME)` into `filters=` is safe to ship as
proposed — no real file should lack `service_name`. Keep `_filter_to_candle_rows` as a cheap post-read safety net
regardless (near-zero cost once the pushdown has already discarded ~54% of rows) — a correctness backstop for the
now-confirmed reader gap (point 2 above), not because `service_name` itself is at risk.

## Open work (tracked todos)

- [x] ✅ [BACKEND] P2. Confirm `read_availability_index`'s honest-absence column-backfill happens before filter
      evaluation (or is otherwise filter-safe for a column absent from some underlying files) — read
      `unified_trading_library/manifest_writer/_read_index.py`'s filter-application code path directly, don't assume.
      (repo: unified-trading-library) — investigation-only, no code change; see "## Findings" above. Confirmed: backfill
      runs AFTER filter evaluation (a real gap for genuinely-optional columns), but `service_name` is a hard-required
      base column since schema v4, so todo 2 is safe to proceed unmodified. — unified-trading-pm@(this commit)
- [x] ✅ [BACKEND] P2. Push `("service_name", "==", _CANDLE_SERVICE_NAME)` into the `filters=` list passed to
      `_ds._read_availability_index` when `is_candle_census`, in `get_axis_value_census`. KEEP the post-read
      `_filter_to_candle_rows` call as a cheap safety net (do not drop it — see Findings above: it's a correctness
      backstop for the reader's general filter-safety gap, not redundant). Add a regression test asserting the
      MDPS-scoped census still excludes MTDS-only rows. Done when a live timed call for a large asset_group (e.g.
      tradfi) completes in single-digit seconds with an unchanged result shape/row_count vs the pre-fix behavior. (repo:
      deployment-api) — deployment-api@82b0469a7e. Shipped + 2 new regression tests (asserts
      `("service_name", "==",     "market-data-processing-service")` in the pushed `filters=`; non-candle requests carry
      no such filter). Live verification (in-process call, bounded, 2026-08-15): full endpoint call for
      `(market-data-processing-service,     tradfi)` now completes in **26.79s** (vs "did not finish in 480s" pre-fix) —
      NOT single-digit seconds as this todo's done-condition optimistically assumed (that 8.6s figure was the isolated
      pushdown READ only; the full endpoint also runs 9 separate `value_counts()` passes over the resulting 6.33M-row
      frame, which the isolated benchmark didn't include). row_count=6,333,546 vs the issue doc's 6,332,575 — a small
      (+971, +0.015%) drift from new tradfi data captured between 2026-08-15's investigation and this fix landing, not a
      correctness regression. Reporting the honest measured number rather than the unmet single-digit claim (CLAIM ≤
      MEASUREMENT) — the fix is still a functional win (unusable/hanging → 26.79s, well inside any normal HTTP gateway
      timeout).
- [ ] [BACKEND] P3. Separate, lower-priority follow-up (not blocking todo 2): the general reader gap confirmed in
      Findings above — `read_availability_index`'s pushdown `filters=` silently SKIPS (not backfill-safely excludes) a
      filter condition on any column absent from a given raw file — is real for genuinely legacy-optional columns (v6+
      `quote_asset`/`margin_type`/`combo_type`, v7 `fixture_id`/`job_id`, v8 `pipeline_mode`, v9
      `source`/`transport`/`cadence`/`available_at`). A future caller pushing one of THOSE into `filters=` against a
      bucket with pre-that-version shards would silently over-include legacy rows that should have failed the filter.
      Fix: in `_read_parquet_columns_safe`'s legacy-schema fallback (`_read_index.py:183-195`), apply the SAME
      per-column default `_backfill`/`_backfill_slim` already use (e.g. `CaptureStatus.CAPTURED.value` for
      `capture_status`, `""` for most others) to a missing filter column before evaluating it, instead of `continue`-ing
      past it. Add a regression test with a synthetic legacy-schema parquet (missing one v6+ column) + a `filters=` on
      that column, asserting rows are correctly excluded rather than passed through. (repo: unified-trading-library)
