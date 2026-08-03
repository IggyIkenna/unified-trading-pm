---
doc_type: issue
title: >-
  delta_one's preflight DependencyChecker unconditionally requires MDPS `processed_candles` for EVERY feature_group,
  even pass-through ones (returns/funding_oi) that never read processed_candles at all -- blocks legitimate backfills
  whenever the target date predates MDPS's candle-derivation coverage, regardless of whether the real raw pass-through
  data (oracle_prices/perp_funding) genuinely exists
summary: >-
  Found while resuming `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo (returns leg full-window production
  launch, 2022-11-01 start). The launch failed preflight with "Missing: market-data-processing-service ...
  processed_candles/by_date/day=2022-11-01/ ... No data for 2022-11-01/DEFI" even though `returns` is a pass-through
  feature_group (`NEEDS_CANDLE_PROCESSING=False` data_types oracle_prices/perp_funding) that never reads
  `processed_candles` -- it reads raw MTDS data directly via `_passthrough_loader.py`. Root cause: `_check_dependencies`
  (`features_service/delta_one/cli/handlers/batch_handler.py:130`) calls the shared UTL
  `BaseDependencyChecker.check_dependencies(date, asset_group)` with NO `feature_group` parameter at all, so the
  MDPS-candle `UPSTREAM_DEPS` entry (`dependency_checker.py:74-79`, `required: True`, unconditional) is checked
  regardless of which feature_group was actually requested. This file ALREADY has the correct exemption pattern one
  layer down -- `_discover_instruments` (`dependency_checker.py:664-684`) routes to
  `_discover_instruments_from_manifest` instead of walking `processed_candles` whenever `all(not
  needs_candle_processing(dt) for dt in candle_data_types)` -- but the earlier PREFLIGHT dependency check (which runs
  BEFORE instrument discovery even starts) has no equivalent exemption, so a pass-through backfill whose target date
  predates MDPS's DEFI candle-derivation coverage is blocked before it ever reaches the code that would have handled it
  correctly.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [defi, features-service, delta-one, dependency-checker, preflight, passthrough, data-correctness]
related:
  - /plans/archive/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md
  - /plans/archive/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md
  - /plans/archive/issues/delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
created: "2026-07-31"
source: [features-delta-one-defi-20260731-104738, preflight failure on 2022-11-01/DEFI/returns]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: features-service@f57d11ae
---

> **🟢 ARCHIVED 2026-08-02** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` (features-service@f57d11ae). Moved by the
> `/plan-reconcile` whole-corpus run of 2026-08-02, which found this doc sitting in `plans/active/issues/` at a terminal
> status — `check_terminal_status_archived` was RED at 13 violations against a baseline of 1. No content was rewritten.

# What I found

Launching `features-delta-one-defi-*` for `--feature-group returns --asset-group DEFI --start-date 2022-11-01` (the real
manifest-verified start of CHAINLINK `oracle_prices` coverage) failed at preflight:

```
ERROR Missing: market-data-processing-service
  Path: gs://market-data-tick-defi-prd-central-element-323112/processed_candles/by_date/day=2022-11-01/
  Reason: No data for 2022-11-01/DEFI
ERROR [HIGH] dependency error ... cannot run for 2022-11-01/DEFI: missing 1 required upstream dependencies
```

`returns` (like `funding_oi`) is a pass-through feature_group — its underlying data_types (`oracle_prices` /
`perp_funding`) have `NEEDS_CANDLE_PROCESSING=False` (confirmed via `unified_api_contracts.needs_candle_processing`) and
are read directly from raw MTDS data by `_passthrough_loader.py`, never from MDPS `processed_candles`. The real data
these feature groups need (confirmed via manifest + direct GCS reads earlier in this investigation chain) exists across
the full 2022-11-01..2026-07-22 window. MDPS's DEFI `processed_candles` bucket, by contrast, genuinely does not have
data that far back (its real coverage boundary sits somewhere between 2022-11-01 and 2023-05-12 — the narrower
verification window starting 2023-05-12 hit no such preflight failure).

## Root cause

`_check_dependencies` (`features_service/delta_one/cli/handlers/batch_handler.py:130-156`) calls:

```python
report = DependencyChecker().check_dependencies(date=start_date, asset_group=asset_group)
```

`check_dependencies` is the SHARED `unified_trading_library.core.dependency_checker.BaseDependencyChecker` method — its
signature is `(self, date, asset_group)`, no `feature_group` parameter — so it always walks the FULL `UPSTREAM_DEPS`
dict (`dependency_checker.py:74-79`), which declares `market-data-processing-service` / `processed_candles` as
`required: True` unconditionally, for every delta_one call regardless of which feature_group triggered it.

This exact file already has the CORRECT exemption pattern one layer downstream, at instrument-discovery time:
`_discover_instruments` (`dependency_checker.py:664-684`):

```python
if candle_data_types and all(not needs_candle_processing(dt) for dt in candle_data_types):
    return self._discover_instruments_from_manifest(bucket_name, date, candle_data_types)
return self._discover_instruments_from_processed_candles(bucket_name, date, timeframe, asset_group)
```

But the PREFLIGHT dependency check (which runs earlier, in `_run_preflight` → `_check_dependencies`, BEFORE
`_discover_instruments` is ever reached) has no equivalent — so a pass-through backfill whose start date predates MDPS's
real candle-derivation coverage is blocked before it ever reaches the code that already knows how to handle it
correctly.

# Why this matters

Blocks any DEFI `returns`/`funding_oi` backfill whose window starts before MDPS's real DEFI `processed_candles` coverage
boundary, even though the actual data these feature groups need is present and correctly computable — this is a FALSE
NEGATIVE, not a genuine missing-dependency case. The only current workaround is
`--skip-dependency-check`/`SKIP_DEPENDENCY_CHECK=1`, which also disables the (unrelated, useful)
`_validate_lookback_candles` sufficiency check for the SAME run (`fail_on_insufficient=not skip_dependency_check` at
`batch_handler.py:539`) — a coarser bypass than necessary, and one a future operator/worker has to re-discover and
re-justify every time this exact situation recurs (this is at least the 2nd time in this investigation chain a DIFFERENT
delta_one preflight/discovery layer needed the same pass-through exemption — see the related docs above).

# What I did NOT do

Used `SKIP_DEPENDENCY_CHECK=1` to unblock THIS session's backfill (justified: independently verified via manifest +
direct GCS reads that the real pass-through data exists across the full window — see the D1 todo's own Progress Log).
Did NOT patch `_check_dependencies`/`DependencyChecker` myself — this todo's actual job was completing the D1 backfill
launch, not auditing every delta_one preflight layer; flagging this as a scoped follow-up rather than absorbing
unplanned scope mid-backfill.

# Recommended decision

- [x] ✅ [BACKEND] P2. Thread `feature_group` (or a resolved `candle_data_types: frozenset[str]`) into
      `_check_dependencies`/`_run_preflight` (`features_service/delta_one/cli/handlers/batch_handler.py`) and skip (or
      down-weight to non-required) the `market-data-processing-service`/`processed_candles` `UPSTREAM_DEPS` entry when
      every requested feature_group's data_types are pass-through (`not needs_candle_processing(dt)` for all), mirroring
      the exact exemption already shipped in `_discover_instruments` (`dependency_checker.py:664-684`). Do NOT touch the
      shared UTL `BaseDependencyChecker.check_dependencies` signature (cross-cutting, used by every service that
      inherits it) — implement the exemption locally in features-service's `DependencyChecker`/`batch_handler.py` (e.g.
      an overridden `check_dependencies` or a pre-filter on `UPSTREAM_DEPS` before delegating to the base). Add a
      regression test covering a pass-through feature_group + a pre-MDPS-coverage date (e.g. `returns`/`funding_oi` +
      2022-11-01/DEFI) passing preflight without `--skip-dependency-check`, and confirm CEFI/TRADFI's existing (correct)
      candle-required behavior is unchanged. Repo: features-service. Done when: the described scenario passes preflight
      without `--skip-dependency-check`, `bash scripts/quality-gates.sh` is green, and the fix ships via
      `quickmerge.sh --agent --files`. — features-service@f57d11ae (dependency_checker.py 86c0628f + line-cap split
      f57d11ae), quality-gates.sh green (18055 passed), 5-case regression test added.

# Progress Log

- 2026-07-31 (slot-11, data_engineering craft, resuming `defi_satellite_ao_dispatch_batch3-014`): filed after the D1
  todo's `returns` full-window production launch hit this exact false-negative preflight block on its real
  manifest-verified start date; worked around via `SKIP_DEPENDENCY_CHECK=1` for this session's launch (independently
  verified safe), filing the proper fix as scoped follow-up work rather than absorbing it mid-backfill.
- 2026-07-31 (slot-7, backend_engineer craft): implemented the fix — added
  `DependencyChecker.check_dependencies_for_feature_groups` (delegates to a new
  `_passthrough_dependency_exemption.build_report_for_feature_groups` helper, split out to keep `dependency_checker.py`
  under the 900-line file-size gate), threaded `feature_groups` through `batch_handler.py`'s
  `_check_dependencies`/`_run_preflight`, and added
  `tests/delta_one/unit/test_dependency_checker_passthrough_exemption.py` (DEFI returns/funding_oi skip MDPS, DEFI mixed
  set + CEFI/TRADFI still require it). `quality-gates.sh` green (18055 passed, 209 skipped). Shipped
  features-service@f57d11ae, verified ancestor of `origin/live-defi-rollout`.
