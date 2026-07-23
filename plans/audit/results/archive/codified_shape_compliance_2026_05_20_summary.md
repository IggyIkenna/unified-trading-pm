---
doc_type: audit-result
title: A1 — Codified-shape compliance summary
summary:
  A1 codified-shape compliance scan across 8142 files / 25 repos — 2593 violations in 1274 files over 10 checks; biggest
  gaps are uac_import_surface (995, cursor-rule-only) and typed_empty_reason (81, runtime-only) with no CI enforcement;
  resolve_bucket_name (759) and classify_venue_error (302) already ratcheting.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [audit, quality-gates, ssot-audit, uac, canonicalisation, scripts]
related: [/plans/audit/results/archive/mega_audit_phase_a_issues_human_readable_2026_05_20.md]
created: 2026-05-20
audited_scope:
  8142 Python files across 25 service repos, 10 codified-shape checks (has_log_upload_trap, manifest_v8,
  record_emission, typed_empty_reason, classify_venue_error, resolve_bucket_name, lifecycle_class,
  no_hardcoded_venue_urls/universe, uac_import_surface); regex-heuristic, no AST
date: 2026-05-20
auditor: semver
parent_epic: infrastructure_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# A1 — Codified-shape compliance summary

_Generated: 2026-05-20T10:06:41.749278+00:00_

Files scanned: 8142

Files with at least one violation: 1274

Total violations: 2593

## Per-check totals (Phase A1)

| Check                         | Total violations | Existing QG ratchet                                                                                        | Status                       |
| ----------------------------- | ---------------: | ---------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `has_log_upload_trap`         |               28 | (deployment-service@6b4610c trap-fix bundled across 14 launchers)                                          | SHIPPED                      |
| `manifest_v8`                 |                6 | base-library.sh STEP 5.x manifest-schema-version                                                           | PARTIAL — verify version pin |
| `record_emission`             |              215 | scripts/qg/no_silent_absence_handlers.sh + scripts/quality_gates/check_emission_policy_paired_callsites.py | SHIPPED                      |
| `typed_empty_reason`          |               81 | (no current QG — relies on LegacyBlankErrorReasonError at runtime)                                         | GAP — needs QG step          |
| `classify_venue_error`        |              302 | scripts/qg/no_adapter_contract_regression.sh + scripts/quality_gates/check_adapter_contract_regression.py  | SHIPPED                      |
| `resolve_bucket_name`         |              759 | scripts/quality_gates/check_inline_bucket_uri.py + inline_bucket_uri_baseline.yaml                         | SHIPPED — ratcheting         |
| `lifecycle_class`             |                0 | (declared in vm_zombie_watchdog.py VM_PREFIX_TO_BUCKET — CLAUDE.md hard rule)                              | PARTIAL — needs CI check     |
| `no_hardcoded_venue_urls`     |              189 | scripts/qg/no_hardcoded_venue_urls.sh                                                                      | SHIPPED                      |
| `no_hardcoded_venue_universe` |               18 | scripts/qg/no_hardcoded_venue_universe.sh                                                                  | SHIPPED                      |
| `uac_import_surface`          |              995 | imports/uac-import-surface-enforcement.mdc + (no enforcement script)                                       | GAP — cursor rule only       |

## Per-repo totals

| Repo                              | Files scanned | Files violating | Total violations |
| --------------------------------- | ------------: | --------------: | ---------------: |
| execution-service                 |          1399 |             227 |              440 |
| market-tick-data-service          |           477 |             181 |              414 |
| unified-trading-library           |           752 |             161 |              385 |
| features-service                  |          1084 |             136 |              230 |
| deployment-api                    |           346 |              72 |              194 |
| deployment-service                |           249 |              55 |              156 |
| instruments-service               |           353 |              65 |              146 |
| strategy-service                  |           408 |              70 |              134 |
| ml-service                        |           314 |              53 |               72 |
| system-integration-tests          |           114 |              17 |               62 |
| position-balance-monitor-service  |           187 |              38 |               59 |
| market-data-processing-service    |           202 |              33 |               51 |
| ml-training-service               |           203 |              36 |               47 |
| e2e-testing                       |            55 |              20 |               40 |
| unified-api-contracts             |          1195 |              20 |               38 |
| ml-inference-service              |           105 |              16 |               24 |
| alerting-service                  |           114 |              13 |               18 |
| risk-and-exposure-service         |           119 |              15 |               18 |
| unified-trading-api               |           106 |              10 |               16 |
| pnl-attribution-service           |            65 |              12 |               14 |
| batch-live-reconciliation-service |            44 |               8 |               13 |
| trading-agent-service             |            53 |               6 |                9 |
| client-reporting-api              |           136 |               5 |                8 |
| fund-administration-service       |            36 |               3 |                3 |
| agent-orchestrator                |            26 |               2 |                2 |

## Top 25 violating files

| Rank | Repo                             | File                                                                  | Kind            | Total |
| ---: | -------------------------------- | --------------------------------------------------------------------- | --------------- | ----: |
|    1 | market-tick-data-service         | `tests/market_interface/integration/test_vcr_ac_schema_validation.py` | other           |    25 |
|    2 | unified-trading-library          | `tests/unit/test_domain_config_reloader.py`                           | gcs_user        |    25 |
|    3 | deployment-service               | `tests/unit/test_cloud_client.py`                                     | gcs_user        |    23 |
|    4 | unified-trading-library          | `tests/unit/test_reader_fallback_chain.py`                            | gcs_user        |    23 |
|    5 | instruments-service              | `instruments_service/engine/orchestrator.py`                          | manifest_writer |    17 |
|    6 | deployment-api                   | `deployment_api/services/data_status_drilldown.py`                    | gcs_user        |    16 |
|    7 | system-integration-tests         | `tests/smoke/test_mock_scenarios.py`                                  | other           |    16 |
|    8 | position-balance-monitor-service | `tests/position_interface/integration/test_vcr_position_schemas.py`   | other           |    15 |
|    9 | unified-trading-library          | `tests/cloud_interface/unit/test_bucket_naming.py`                    | gcs_user        |    15 |
|   10 | unified-trading-library          | `tests/unit/test_config_reloader.py`                                  | gcs_user        |    14 |
|   11 | deployment-api                   | `tests/unit/test_service_status_execution.py`                         | gcs_user        |    13 |
|   12 | deployment-service               | `tests/unit/test_cleanup_old_tarballs.py`                             | gcs_user        |    13 |
|   13 | strategy-service                 | `strategy_service/models/instruction.py`                              | other           |    13 |
|   14 | market-tick-data-service         | `market_tick_data_service/engine/orchestrator.py`                     | manifest_writer |    12 |
|   15 | execution-service                | `tests/trade_execution/integration/test_vcr_schema_validation.py`     | other           |    11 |
|   16 | unified-trading-library          | `tests/unit/lifecycle/test_uploader.py`                               | gcs_user        |    11 |
|   17 | deployment-api                   | `tests/unit/test_pool_breakdown.py`                                   | gcs_user        |    10 |
|   18 | deployment-api                   | `deployment_api/routes/services.py`                                   | gcs_user        |    10 |
|   19 | strategy-service                 | `strategy_service/engine/core/gcs_storage_service.py`                 | gcs_user        |    10 |
|   20 | unified-trading-library          | `tests/unit/test_domain_client_writers.py`                            | gcs_user        |    10 |
|   21 | deployment-api                   | `tests/unit/test_route_services.py`                                   | gcs_user        |     9 |
|   22 | deployment-api                   | `tests/unit/test_route_monitor_scheduled.py`                          | other           |     9 |
|   23 | deployment-api                   | `tests/unit/test_route_monitor_live.py`                               | other           |     9 |
|   24 | deployment-api                   | `tests/unit/test_config_management.py`                                | gcs_user        |     9 |
|   25 | deployment-service               | `tests/fixtures/cloud_fixtures.py`                                    | gcs_user        |     9 |

## Gap analysis — checks lacking workspace-wide QG enforcement

The mega-audit Phase A1 promised 10 checks; below are the ones where existing QG enforcement is partial or absent. These
slot into the **Cross-cutting QG ratchet plan** referenced from the mega-audit tracker (no new SSOT — extend existing
plan).

| Check                | Gap                                                                                   | Proposed remediation                                                                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `typed_empty_reason` | Runtime-only via `LegacyBlankErrorReasonError`; no static catch.                      | Add `scripts/quality_gates/check_typed_empty_reason.py` that scans for `record_empty(reason="...")` string literals and asserts `EmptyConfirmedReason.X` usage. |
| `uac_import_surface` | Cursor rule only (`imports/uac-import-surface-enforcement.mdc`) — not enforced in CI. | Promote to `scripts/quality_gates/check_uac_import_surface.py` + per-repo wiring.                                                                               |
| `lifecycle_class`    | Mandatory per CLAUDE.md but no CI checker.                                            | Add `scripts/quality_gates/check_vm_lifecycle_class.py` that parses `vm_zombie_watchdog.py` + asserts every entry has a typed `LifecycleClass`.                 |
| `manifest_v8`        | base-library.sh STEP enforces but A1 surfaces drift candidates.                       | Cross-check `MANIFEST_SCHEMA_VERSION` constants workspace-wide; raise to ERROR in QG.                                                                           |
