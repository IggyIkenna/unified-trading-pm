---
doc_type: audit-result
title: Run-Lifecycle Events Audit — 2026-05-05
summary:
  Point-in-time (2026-05-05) audit classifying every long-running Python entry-point on UTL-events + run-lifecycle
  adoption — 49 call setup_events, 17 C-class rollout targets emit no run-level events, and the Phase-3 rollout order
  for the run_lifecycle helper refactor.
status: partial
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    client-reporting-api,
    deployment-service,
    e2e-testing,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer]
tags: [audit, run-lifecycle, observability, mtds, mdps, scripts]
related: [/plans/audit/results/vm_event_emission_audit_2026_05_15.md, /codex/04-architecture/service-emission-policy.md]
created: 2026-05-05
authoritative_for: [run_lifecycle entry-point rollout classification (2026-05-05 audit)]
referenced_by: [plans/audit/results/vm_event_emission_audit_2026_05_15.md]
owner:
last_reviewed: 2026-05-17
code_refs:
auditor: ikenna
severity: P2
date: 2026-05-05
audited_scope: run-lifecycle / UTL-events adoption across every long-running Python entry-point
parent_epic: observability_master
resulting_plan:
lib_version:
doc_versions_checked: []
---

# Run-Lifecycle Events Audit — 2026-05-05

Phase 2 of `plans/archive/run_lifecycle_events_ssot_2026_05_05.plan.md`. Identifies every long-running Python
entry-point in the workspace and classifies it on:

- **Has UTL events?** (calls `setup_events` from `unified_trading_library.events`)
- **Has run-lifecycle?** (uses `run_lifecycle(...)` helper or hand-rolls `*_RUN_STARTED` + `*_RUN_COMPLETED|FAILED`)

Phase 3 of the plan refactors the **C-classified** entry-points below to use the helper.

## Summary

- **49** Python files in the workspace call `setup_events` (already on UTL events lib).
- **17** of those are long-running entry-points (scripts/ or cli/) that emit no run-level events — the rollout target.
- **0** long-running entry-points use the new `run_lifecycle` helper yet (it's brand new in `unified_trading_library`
  `af7319f1`).
- **1** entry-point (`migrate_sports_canonical.py` MTDS `ce9b069`) hand-rolls the events ad-hoc — refactor to helper as
  part of Phase 3.

## Classification key

- **A** — uses UTL events AND has run-lifecycle (helper or hand-rolled). ✅ done.
- **B** — uses UTL events but missing one half (e.g. STARTED only, no terminal event).
- **C** — uses UTL events but no run-lifecycle at all. **Rollout target.**
- **D** — does not use UTL events. Out of scope here; covered by separate "every service on UTL" sweep.

## Rollout-target (C) entry-points — 17 files

Ordered by criticality for predictions e2e first, then operations.

### MTDS migrate scripts (4) — **HIGH PRIORITY** — peers of migrate_sports_canonical

These are the same shape as `migrate_sports_canonical.py` (which was hand-rolled in MTDS `ce9b069`). Direct copy-paste
of the helper-refactor pattern.

| File                                                                                        | Notes                                                                                                    |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `market-tick-data-service/market_tick_data_service/scripts/migrate_defi_canonical.py`       | Same shape as sports migrate; service_name = `migrate-defi-canonical`                                    |
| `market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_canonical.py`     | service_name = `migrate-tradfi-canonical`                                                                |
| `market-tick-data-service/market_tick_data_service/scripts/migrate_polymarket_canonical.py` | service_name = `migrate-polymarket-canonical`                                                            |
| `market-tick-data-service/scripts/migrate_cefi_v2.py`                                       | Note: under `scripts/` (root), not `market_tick_data_service/scripts/`. service_name = `migrate-cefi-v2` |

### MDPS handlers + scripts

| File                                                                                              | Notes                                     |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `market-data-processing-service/market_data_processing_service/cli/handlers/live_mode_handler.py` | Long-running live worker; needs lifecycle |

### deployment-service

| File                                                    | Notes                                                                           |
| ------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `deployment-service/deployment_service/cli/main.py`     | CLI dispatcher; lifecycle around the dispatched command                         |
| `deployment-service/scripts/vm/deployment_heartbeat.py` | VM heartbeat daemon — long-running, needs lifecycle for VM-watchdog correlation |

### instruments-service scripts

| File                                                            | Notes                                                    |
| --------------------------------------------------------------- | -------------------------------------------------------- |
| `instruments-service/scripts/aggregate_legacy_es_opt_trades.py` | One-off aggregation script                               |
| `instruments-service/scripts/full_polymarket_dump.py`           | Heavy dump operation; needs lifecycle for ETA visibility |

### features-\* + ml-training

| File                                                                                               | Notes                                                              |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `features-service (commodity family)/features_commodity_service/cli/main.py`                       | Service CLI                                                        |
| `features-service (sports family)/features_sports_service/scripts/compute_sfi_progressive_only.py` | One-off compute                                                    |
| `ml-training-service/ml_training_service/cli/handlers/__init__.py`                                 | Handlers package; lifecycle on the dispatch shape, not per-handler |

### MTDS handlers

| File                                                                               | Notes                 |
| ---------------------------------------------------------------------------------- | --------------------- |
| `market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py` | Handler dispatch site |

### e2e + utility scripts

| File                                                               | Notes                                                                          |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| `e2e-testing/scripts/prediction/validate-single-day.py`            | Validation script; lifecycle gives ETA + terminal status to monitors           |
| `unified-trading-library/scripts/check_utl_adoption.py`            | Adoption-check utility; sub-second runs but lifecycle gives clean event stream |
| `unified-trading-pm/scripts/dev/smoke-test-dev.py`                 | Smoke wrapper                                                                  |
| `unified-trading-pm/scripts/validation/audit-library-imports.py`   | Audit script                                                                   |
| `unified-trading-pm/scripts/validation/check_data_completeness.py` | Validation script; data-pipeline-relevant                                      |

## Hand-rolled (B) — refactor to helper

| File                                                                                    | Notes                                                                                                                                                                                                                                                                                                                                                                                                           |
| --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `market-tick-data-service/market_tick_data_service/scripts/migrate_sports_canonical.py` | MTDS `ce9b069` added ad-hoc `MIGRATE_SPORTS_RUN_STARTED` / `_COMPLETED` / `_FAILED`. Phase 3 swap to `run_lifecycle("migrate-sports-canonical", details=...)`. **Defer until the currently-running PID 88903 migrate (started 19:48:48Z) finishes** — refactoring the on-disk script while the running process has it loaded into memory is fine, but easier to verify the next run uses the helper end-to-end. |

## Already-A (UTL events + lifecycle present elsewhere) — sample

These call `setup_events` and either don't need run-lifecycle (long-running services with their own `ServiceBootstrap`
lifecycle managing STARTED/STOPPED) or already emit it via different mechanisms. **Out of rollout scope:**

- `unified-trading-library/unified_trading_library/feature_service_base/base_service.py` — `ServiceBootstrap` covers it
- `unified-trading-library/unified_trading_library/lifecycle/daemon.py` — daemon lifecycle module
- `unified-trading-library/unified_trading_library/manifest_consolidator.py` — has its own consolidate-cycle events
- `client-reporting-api/*` — service mains use `ServiceBootstrap`
- `strategy-service/strategy_service/signal_broadcast/observability_ingest.py` — service module
- `system-integration-tests/system_integration_tests/audit/checks/check_observability.py` — test/audit module

## D-classified (no UTL events) — separate sweep

Running this audit again with a wider grep would catch:

- ad-hoc shell scripts with `gcloud compute instances create` that don't bootstrap UTL events at all
- Cloud Functions / Cloud Run jobs configured via terraform without an `setup_events()` call site

That's a follow-up plan — get every long-running thing onto UTL events FIRST, then onto `run_lifecycle`.

## Phase 3 rollout order

1. **migrate_sports_canonical** — refactor from hand-rolled to helper (Phase 3 §1). Defer until the running migrate
   finishes.
2. **MTDS peer migrates (4 files)** — copy-paste the helper integration. Single MTDS commit.
3. **MDPS, instruments-service, features-\*, ml-training** — per-repo focused commits.
4. **deployment-service** — `cli/main.py` + `scripts/vm/deployment_heartbeat.py`. Heartbeat is a daemon — lifecycle
   wraps the daemon's outer loop.
5. **PM + e2e + UTL utility scripts** — minor.
