---
doc_type: issue
title: >-
  unified-trading-library's get_captured_instruments() calls read_availability_index() with no date filters=, decoding
  the WHOLE availability manifest on every call -- confirmed real (~14.67GB anon-rss OOM-kill) sibling anti-pattern to
  the just-fixed features-service delta_one _build_captured_index() bug, on the same real DEFI index
summary: >-
  Found while root-causing delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md (fixed in
  features-service@f8e21361 -- _build_captured_index() now passes a [date - buffer_days, date] filters= pushdown). The
  SAME anti-pattern (a column-projected but otherwise unfiltered read_availability_index() call, filtered only AFTER the
  full decode via pandas boolean masking) exists in unified_trading_library/feature_service_base/
  manifest_discovery.py::get_captured_instruments() -- confirmed by direct read, not inference. This function accepts an
  optional date= parameter specifically to narrow the result, but never threads it into filters= (the row-group
  predicate-pushdown mechanism read_availability_index() actually supports, per its own docstring which cites the EXACT
  same OOM incident: mtds_backfill_vm_startup_oom_rc137_2026_07_14, measured ~14.86GB -> ~5MB for an equivalent
  single-day filter on the real 27.4M-row DEFI index). get_captured_instruments() is called from features-service's
  DataLoader.get_available_instruments() (delta_one/app/core/data_loader.py) on every batch run where the caller does
  not pass an explicit --instruments list -- i.e. every normal production backfill/live call, not just the
  --skip-dependency-check edge case that surfaced the sibling bug.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [utl, manifest, availability-index, oom, memory, filters-pushdown, delta-one]
related:
  - /plans/active/issues/delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md
  - /plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md
created: "2026-07-31"
source:
  - Discovered via a dedicated research pass root-causing
    delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md (prediction... no --
    defi_satellite_ao_dispatch_batch3_2026_07_26.md's D1 follow-up chain), slot 14
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: unified-trading-library@6c0ca59b
---

> **🟢 ARCHIVED 2026-08-02** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` (unified-trading-library@6c0ca59b). Moved by
> the `/plan-reconcile` whole-corpus run of 2026-08-02, which found this doc sitting in `plans/active/issues/` at a
> terminal status — `check_terminal_status_archived` was RED at 13 violations against a baseline of 1. No content was
> rewritten.

# What I found

`unified_trading_library/feature_service_base/manifest_discovery.py::get_captured_instruments()`:

```python
def get_captured_instruments(
    bucket: str, date: str | None = None, data_type: str | None = None,
    service_name: str = "features-service", asset_group: str | None = None,
) -> list[str]:
    index: DataFrame = read_availability_index(
        bucket,
        columns=["capture_status", "date", "data_type", "venue", "instrument_type", "instrument_id"],
        # NO filters= -- date is applied via a post-decode pandas mask instead:
    )
    mask: Series[bool] = index["capture_status"].astype(str) == "captured"
    if date is not None:
        mask = mask & (index["date"].astype(str) == date)
```

`read_availability_index()`'s own docstring (`unified_trading_library/manifest_writer/_read_index.py:353-364`) documents
the exact fix pattern and cites the exact real-world incident this repeats: `filters=` is pyarrow-style row-group
predicate pushdown -- row groups that provably don't match are skipped BEFORE decode, bounding peak memory to roughly
the matching subset, "measured ~14.86 GiB -> ~5 MB for a single-day filter on the real 27.4M-row DeFi index"
(`mtds_backfill_vm_startup_oom_rc137_2026_07_14`). `get_captured_instruments()` receives a `date` parameter specifically
to narrow its result but never passes it through as `filters=` -- it decodes the WHOLE manifest every call regardless.

This is a genuine sibling of the bug just fixed in `features-service@f8e21361`
(`delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`): that fix bounded
`dependency_checker.py::_build_captured_index()`'s equivalent unfiltered call. `get_captured_instruments()` is a
DIFFERENT call site (this repo, not features-service) reached via `DataLoader.get_available_instruments()`
(`features-service/features_service/delta_one/app/core/data_loader.py:263-295`) -- called on EVERY delta_one batch run
where the caller does not pass an explicit `--instruments` list, not just the `--skip-dependency-check` edge case. Given
the confirmed real cost of an unfiltered read on this exact DEFI index (~14.67GB anon-rss, a live kernel OOM-kill per
the sibling incident doc), this is a live, standing risk for any DEFI delta_one run relying on instrument auto-discovery
-- not a hypothetical.

# Why this matters

`get_captured_instruments()` is a shared UTL function -- likely called by more than just features-service's delta_one
path (grep before fixing to confirm the full caller set). A fix here benefits every caller, not just the one that
surfaced it. Given the confirmed OOM cost on the real DEFI index, this is a live billing-waste / reliability risk (a
SPOT VM OOM-killed mid-backfill wastes the compute + delays real coverage), matching the severity class CLAUDE.md's
data-pipeline-correctness rule treats as a heartbeat issue, not a nice-to-have.

# What I did NOT do

Did not fix this myself -- `unified-trading-library` is a different repo from the one
`delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md` scoped this session to
(`repos: [features-service]`), and UTL is a shared, cross-cutting foundational library many services depend on --
changing it needs its own scoped todo + full caller-impact check (does every existing caller pass `date=` when it
legitimately could, or does some caller rely on the current "all dates" behavior on purpose?), not a same-session
scope-creep fix bundled into the features-service todo.

# Recommended decision

- [x] ✅ [BACKEND] P2. Thread `date` (and, where meaningfully narrowing, `data_type`) into a `filters=` row-group
      pushdown in `get_captured_instruments()`
      (`unified_trading_library/feature_service_base/manifest_discovery.py:79-138`), mirroring the exact pattern just
      shipped in `features-service@f8e21361` (`dependency_checker.py::_build_captured_index`) and the already-correct
      pattern in `_discover_instruments_from_manifest`. First grep every caller of `get_captured_instruments()` across
      the workspace to confirm none of them rely on the current "read ALL dates" behavior when `date=None` isn't
      actually intended as "give me everything" (the function's own docstring says `None` = all dates, which is a
      legitimate use case that must keep working unfiltered -- only the `date is not None` branch should route through
      `filters=`). Add a regression test pinning the call signature (mirroring
      `TestBuildCapturedIndexColumnProjection::test_read_availability_index_is_column_projected_and_date_filtered` in
      `features-service/tests/delta_one/unit/test_lookback_validation.py`) and, if feasible, a tracemalloc/memray
      before-after measurement on a realistic-sized synthetic index. Repo: unified-trading-library. Done when:
      `get_captured_instruments(date=<x>)` calls `read_availability_index(...,     filters=[("date", "=", x)])`, every
      existing caller's behavior is confirmed unchanged (or intentionally improved, with the caller's own tests still
      green), `bash scripts/quality-gates.sh` is green, and the fix ships via `quickmerge.sh --agent --files`.

# Progress Log

- 2026-07-31 (slot 14, backend_engineer, dispatch `delta_one_skip_dependency_check_oom_pre_2023_05_dates-001`): filed
  while root-causing the sibling features-service bug -- fixed that one directly (in scope), verified this UTL-side
  sibling by direct code read (not inference), filed as its own cross-repo follow-up rather than scope-creeping into the
  features-service fix.
- 2026-07-31 (slot 14, backend_engineer, dispatch `utl_get_captured_instruments_unfiltered_manifest_read-001`): fixed.
  Grepped every caller of `get_captured_instruments()` across the workspace first (`features-service`'s
  `volatility/core/data_loader.py` and `delta_one/app/core/data_loader.py`, both of which already pass explicit
  `date=`/`data_type=` on every real call, plus this repo's own unit tests) -- confirmed none rely on the unfiltered
  "read ALL dates" behavior when `date=None` isn't intentional; that legitimate `None` = all-dates case is preserved
  unfiltered. Threaded `date` and (independently) `data_type` into `filters=` with `==` ops, mirroring the
  already-correct in-file precedent `check_dependency_via_manifest()` (not the "=" op used by the two features-service
  call sites cited in the recommendation -- `==` is what the fallback legacy-schema pandas re-filter path in
  `_read_index.py::_read_parquet_columns_safe`/`_read_availability_index_slim` actually matches on op string, so `==` is
  the safer, already-proven-correct choice in this exact file; not a functional difference on the primary pyarrow path,
  which accepts both). Added 3 new regression tests pinning the exact call signature for date-only/data_type-only/
  neither (mirroring `TestBuildCapturedIndexColumnProjection` in features-service) plus updated the existing column-
  projection test to also assert the filters= it now passes. Skipped the optional tracemalloc/memray before-after
  measurement (not feasible without live GCS access to the real 27.4M-row DEFI index in this sandboxed session; the
  identical `filters=` mechanism's memory-reduction is already measured and cited in `read_availability_index`'s own
  docstring and the sibling features-service fix's regression test). `bash scripts/quality-gates.sh` green. Shipped:
  `unified-trading-library@6c0ca59b`.
