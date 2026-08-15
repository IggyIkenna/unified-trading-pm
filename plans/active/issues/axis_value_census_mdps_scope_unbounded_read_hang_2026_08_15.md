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

## Open work (tracked todos)

- [ ] [BACKEND] P2. Confirm `read_availability_index`'s honest-absence column-backfill happens before filter evaluation
      (or is otherwise filter-safe for a column absent from some underlying files) — read
      `unified_trading_library/manifest_writer/_read_index.py`'s filter-application code path directly, don't assume.
      (repo: unified-trading-library)
- [ ] [BACKEND] P2. Once confirmed safe, change `get_axis_value_census` to push
      `("service_name", "==", _CANDLE_SERVICE_NAME)` into the `filters=` list passed to `_ds._read_availability_index`
      when `is_candle_census`, and drop the now-redundant post-read `_filter_to_candle_rows` call (or keep it as a cheap
      no-op safety net if the filter-safety check above finds any edge case it doesn't fully cover). Add a regression
      test asserting the MDPS-scoped census still excludes MTDS-only rows. Done when a live timed call for a large
      asset_group (e.g. tradfi) completes in single-digit seconds with an unchanged result shape/row_count vs the
      pre-fix behavior. (repo: deployment-api)
