---
doc_type: issue
title:
  "unified-trading-library@f4987fb8 accidentally deleted the LIVE `calendar_features` PATH_REGISTRY row while cleaning
  up confirmed-dead rows — breaks features-service calendar batch handler + a QG test"
summary: >-
  While shipping features_service_pipeline_mode_required_kwarg_break_2026_07_29's two pipeline_mode todos, the full
  `bash scripts/quality-gates.sh` run on features-service surfaced one additional, unrelated failure:
  `tests/calendar/unit/test_library_deps_integration.py::TestUnifiedTradingLibrary::test_build_path_for_calendar_features`
  raises `KeyError: "Dataset 'calendar_features' not in PATH_REGISTRY."`. Root cause: commit `f4987fb8` ("chore: delete
  confirmed-dead PATH_REGISTRY rows + domain_client consumer classes") in `unified-trading-library` states it deletes
  `corporate_actions`, `l2_book_checkpoints`, `liquidation_clusters`, `liquidity_features_1m`, and 5 `sports_*` rows —
  but its diff ALSO deletes the `calendar_features` row, which is NOT named anywhere in the commit message and is NOT
  dead: it has real, live production consumers in features-service (`calendar/adapters/storage_adapter.py`'s
  `get_writer(...)`, `calendar/config.py`'s default bucket kind, `calendar/cli/handlers/batch_handler.py`'s
  `build_bucket`/`build_path` calls, and `scripts/pipeline_e2e_check.py`'s manifest-source citation). This reads as
  collateral damage from the dead-row cleanup sweep (adjacent-entry mis-scoping), not an intentional removal — the
  commit's own stated scope never mentions it.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, features-service]
scope: [engineer, admin]
tags: [path-registry, unified-trading-library, calendar, regression, accidental-deletion, qg-red]
related:
  [
    /plans/active/issues/features_service_pipeline_mode_required_kwarg_break_2026_07_29.md,
    /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md,
  ]
created: 2026-07-29
parent_epic: infrastructure_master
source:
  [
    backend_engineer slot-15,
    2026-07-29,
    discovered while shipping features_service_pipeline_mode_required_kwarg_break-002,
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.05
estimate_calibrated_ai_days: 0.05
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-29
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# `calendar_features` PATH_REGISTRY row accidentally deleted by an unrelated dead-code cleanup commit

## What I found

Full `bash scripts/quality-gates.sh` on features-service (`live-defi-rollout` HEAD `cbb3e690` + local pipeline_mode
fixes) fails one test unrelated to the pipeline_mode work in progress:

```
FAILED tests/calendar/unit/test_library_deps_integration.py::TestUnifiedTradingLibrary::test_build_path_for_calendar_features
KeyError: "Dataset 'calendar_features' not in PATH_REGISTRY. Known: ['backtest_results', 'delta_one_features',
'execution_fills', 'instruments', 'lst_seasonal_rewards', 'ml_model_metadata', 'ml_models', 'ml_predictions',
'ml_training_artifacts', 'nautilus_catalog', 'onchain_features', 'pnl_attribution', 'positions',
'processed_candles', 'raw_tick_data', 'risk_metrics', 'strategy_instructions', 'strategy_orders',
'volatility_features']"
```

**Root cause**: `unified-trading-library@f4987fb8` ("chore: delete confirmed-dead PATH_REGISTRY rows + domain_client
consumer classes", author slot-2, 2026-07-29 06:45:28) states its scope as deleting `corporate_actions` /
`l2_book_checkpoints` / `liquidation_clusters` / `liquidity_features_1m` and 5 `sports_*` rows (all "confirmed dead:
zero writer, zero live GCS objects, zero real consumers"). Its diff on
`unified_trading_library/config_interface/paths/registry.py` also removes the `calendar_features` row — NOT named
anywhere in the commit message or its stated closure targets (`gcs_path_resolution_centralization_audit_2026_07_28.md`'s
dead-code todo + the sports_prediction doc's 5-row todo, neither of which lists `calendar_features`).

**`calendar_features` is NOT dead** — confirmed live consumers in features-service:

- `features_service/calendar/adapters/storage_adapter.py:19,30` — `get_writer("calendar_features", ...)`.
- `features_service/calendar/config.py:53` — default bucket-kind config value.
- `features_service/calendar/cli/handlers/batch_handler.py:105-110` — `build_bucket("calendar_features", ...)`
  - `build_path("calendar_features", ...)` + `dataset_name="calendar_features"`.
- `scripts/pipeline_e2e_check.py:487` — cites `PATH_REGISTRY['calendar_features'].path_template` as a manifest source.
- Two tests reference it directly: `tests/calendar/unit/test_library_deps_integration.py` (unit) and
  `tests/calendar/integration/test_unified_domain_client_integration.py` (integration) — both exercise
  `build_path("calendar_features", ...)` with real partition kwargs, not stub/dead-code smoke tests.

This reads as **adjacent-entry collateral damage** from the cleanup sweep (the deleted `calendar_features` block sits
immediately after `delta_one_features` and immediately before the onchain FOLD-A block in the diff — a likely
scoping/regex mis-slice during the dead-row removal), not an intentional, evidenced deletion.

## Why it matters

- **Production impact, not just CI**: `calendar/adapters/storage_adapter.py` and
  `calendar/cli/handlers/batch_handler.py` are live write paths for calendar features (FRED yield-curve /
  economic-results derived features) — with the row gone, any live call to `get_writer("calendar_features", ...)` or
  `build_bucket/build_path("calendar_features", ...)` now raises `KeyError` at runtime, not just in tests.
- **Blocks quickmerge for EVERY features-service commit** touching the calendar-features test suite (the full-suite
  `quality-gates.sh` sentinel never writes green while this KeyError fires) — same "one repo, one shared gate" blocking
  pattern as the pipeline_mode issue this was discovered alongside.

## Fix

Restore the exact deleted `DataSetSpec` entry (recovered verbatim from `git show f4987fb8`'s diff) to
`unified_trading_library/config_interface/paths/registry.py`, in its original position (between `delta_one_features` and
the onchain FOLD-A comment block):

```python
"calendar_features": DataSetSpec(
    name="calendar_features",
    bucket_template="features-calendar-{project_id}",
    path_template="calendar/{feature_group}/by_date/day={date}/",
    partition_keys=["feature_group", "date"],
    file_template="features.parquet",
),
```

## Todos

- [ ] [BACKEND] P1. Restore the `calendar_features` `DataSetSpec` row to
      `unified_trading_library/config_interface/paths/registry.py` (unified-trading-library repo), verbatim as recovered
      above. **Done when**:
      `tests/calendar/unit/test_library_deps_integration.py::TestUnifiedTradingLibrary::test_build_path_for_calendar_features`
      and `tests/calendar/integration/test_unified_domain_client_integration.py` pass, and full
      `bash scripts/quality-gates.sh` is green on unified-trading-library.

## Evidence

- `bash scripts/quality-gates.sh` on features-service `live-defi-rollout` HEAD `cbb3e690` (+ local uncommitted
  pipeline_mode fixes for `features_service_pipeline_mode_required_kwarg_break_2026_07_29.md`):
  `1 failed, 17975 passed, 209 skipped` (2026-07-29), the sole failure being this `KeyError`.
- `git -C unified-trading-library show f4987fb8 -- unified_trading_library/config_interface/paths/registry.py` — full
  diff confirms the `calendar_features` block is deleted alongside the commit's stated targets, but is never named in
  the commit message or the two closure-target docs it cites.
- `grep -rn "calendar_features" features-service/` — 4 production call sites + 2 tests, zero indication of dead/unused
  status.
