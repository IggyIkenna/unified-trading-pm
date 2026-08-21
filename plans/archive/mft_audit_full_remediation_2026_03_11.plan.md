---
doc_type: plan
title: mft-audit-full-remediation
summary: Full remediation of all 15 FAILs and 20 WARNs from the 2026-03-11 Citadel-grade MFT infrastructure audit. Covers
  float price precision, CI/CD divergence, deployment-api tier boundary (HTTP), cloud abstraction compliance, schema governance,
  code quality, and governance/compliance gaps.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, execution-service, instruments-service, market-data-processing-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
todos:
- {id: float-fields-defi-api-contracts, content: §5.1a/b — Replace float price/qty fields with Decimal in unified-defi-execution-interface/connectors/cefi_base.py (17 fields) and unified-api-contracts/canonical_mappings.py (4 fields in ContractSpec), status: done}
- {id: import-error-fallbacks, content: '§8.3 — Remove try/except ImportError fallbacks in deployment-service/live_deployment.py:306-307,359-360 — fail loud at module import time', status: done}
- {id: deployment-service-http-server, content: '§4.3a — Add FastAPI HTTP server to deployment-service: create deployment_service/api/app.py + routes/state.py on port 9000, wiring StateManager methods to canonical endpoints matching deployment_service_client.py', status: done}
- {id: deployment-api-remove-direct-imports, content: §4.3b — Remove all 5 direct Python imports of deployment_service business logic from deployment-api routes/workers; replace with deployment_service_client HTTP calls; remove deployment-service from deployment-api deps, status: done}
- {id: ci-path-cloud-mock-rollout, content: '§15.2+§15.3 — Create unified-trading-pm/scripts/propagation/rollout-quality-gates-ci-workflows.py to add export PATH, CLOUD_MOCK_MODE=true, GCP_PROJECT_ID to all 34+ repos missing PATH and 37+ missing CLOUD_MOCK_MODE; run script', status: done}
- {id: qg-scripts-collapse-stubs, content: '§2.1/§17 — Collapse 6 oversized quality-gates.sh scripts (execution-service 194L, elysium-defi-system 122L, deployment-api 94L, deployment-service 73L, instruments-service 59L, market-tick-data-service 57L) into <50L stubs sourcing base-service.sh', status: done}
- {id: ci-no-fix-flag, content: '§15.4 — Ensure --no-fix flag present on all CI quality-gates.sh invocations (covered by rollout script, verify residual repos)', status: done}
- {id: ssot-index-register-plans, content: '§9.1 — Register 13 unregistered active plans in unified-trading-codex/00-SSOT-INDEX.md: batch_live_recon, cloud_infra_bucket_auth, cloud_infra_extended_bootstrap, contract_completeness_checker, data_availability_live_expectations, dev_environment_automated_onboarding, error_normalisation_unknown_exchanges, execution_service_logic_audit, linter_audit_all_repos, recon_rebalancing_order_recovery, semver_multi_project_env, ui_coverage_uplift, zero_baseline_typecheck (all _2026_03_10)', status: done}
- {id: ssot-index-remove-phantoms, content: '§9.2 — Remove 4 phantom entries from SSOT-INDEX that have no disk files: coverage_remediation_2026_03_10, quality_gates_dry_refactor_2026_03_09, ui_auth_oauth_pkce_2026_03_09, unit_tests_and_test_failure_action', status: done}
- {id: execution-service-fail-under, content: §11.5 — Fix execution-service/pyproject.toml fail_under=31 → fail_under=70 to match quality-gates.sh MIN_COVERAGE=70, status: done}
- {id: strategy-service-integration-markers, content: '§11.6 — Add pytestmark = pytest.mark.integration at module level to 3 strategy-service integration test files (test_signal_pipeline.py, test_strategy_pipeline.py, test_strategy_cascade_events.py)', status: done}
- {id: type-ignore-docs-sweep, content: '§8.2 — Add type:ignore documentation entries to QUALITY_GATE_BYPASS_AUDIT.md in unified-domain-client and unified-trading-library for known suppressions', status: done}
- {id: float-fields-internal-contracts, content: '§5.1c — Replace float price/quantity/spread/basis fields with Decimal in unified-internal-contracts/features.py (90+ fields, audit each: price fields → Decimal, pure ratios → float with comment). Also fix unified-api-contracts/execution.py:183,201.', status: done}
- {id: gs-uri-migration, content: '§12.1/§12.6 — Replace 6 hardcoded gs:// URI constructions in market-data-processing-service with UCI get_storage_client() calls (data_source.py, data_sink.py, orchestration_workers.py ×2, output_writer_service.py, orchestration_coordinator.py). Add gs:// rg lint gate to base-service.sh.', status: done}
- {id: orchestration-workers-mixin-split, content: §2.5 — Split orchestration_workers.py (889L) into BatchOrchestrationMixin (batch_workers.py) + LiveOrchestrationMixin (live_workers.py) + thin composer class. All existing imports preserved via composer., status: done}
- {id: type-ignore-audit-fix, content: '§2.6 — Audit all 136 type:ignore instances. Fix architectural violations (remove suppression + fix root cause). Add specific error codes to legitimate suppressions. Target: <20 documented-legitimate. Focus: market-data-processing-service (18+), unified-trading-library, unified-api-contracts.', status: done}
- {id: mifid-best-execution-event, content: '§6.6 — Add BestExecutionEvent schema to unified-events-interface/schemas.py with venue, instrument_id, execution_price (Decimal), reference_price, price_improvement, order_id, fill_id, fca_form_type (RTS28/RTS27), mifid_timestamp fields. Add to __all__ and test_event_logging.py.', status: done}
- {id: trading-critical-todos-tracked, content: '§13.2 — Add 7 trading-critical TODOs as tracked plan todos in stub_completion_interfaces_and_infra.md: risk batch compute, cash reserve check, BALANCER-ETH, live UMI gas estimator, roll calendar prices, mark price features', status: done}
- {id: npm-version-drift-fixes, content: '§16 — Fix npm version drift: settlement-ui @playwright/test ^1.41.0 → ^1.58.2; deployment-ui typescript/vite/eslint → canonical versions; unified-admin-ui npm install to regenerate stale package-lock.json', status: done}
- {id: baseline-json-docs, content: §8.1 — Document market-data-processing-service/.basedpyright-baseline.json (8722L) in QUALITY_GATE_BYPASS_AUDIT.md with status DOCUMENTED-WARN and link to zero_baseline_typecheck_2026_03_10.md, status: done}
isProject: false
---

# MFT Audit Full Remediation — 2026-03-11

**Grade at audit time:** FAIL (15 FAILs, 20 WARNs, 17 sections) **Sections with FAILs:** §1, §2, §4, §5, §8, §9, §12,
§15, §17 **Sections PASS:** §3 (Security), §10 (Integration Tests), §14 (Orphaned Code)

## Execution Model

Two waves of parallel agents (1 agent per 2 tasks). Wave 2 starts after Wave 1 commits land.

## Wave 1 Agent Assignments

| Agent | Tasks                                           | Repos                                                                                                                     |
| ----- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| A1    | §5.1a/b float fields + §8.3 ImportError         | unified-defi-execution-interface, unified-api-contracts, deployment-service                                               |
| A2    | §4.3a/b deployment HTTP server + remove imports | deployment-service, deployment-api                                                                                        |
| A3    | §15.2+§15.3 CI rollout script                   | unified-trading-pm                                                                                                        |
| A4    | §2.1/§17 QG stubs + §15.4 --no-fix              | execution-service, deployment-api, deployment-service, instruments-service, market-tick-data-service, elysium-defi-system |
| A5    | §9.1 register plans + §9.2 remove phantoms      | unified-trading-codex                                                                                                     |
| A6    | §11.5 fail_under + §11.6 markers + §8.2 docs    | execution-service, strategy-service, unified-domain-client, unified-trading-library                                       |

## Wave 2 Agent Assignments

| Agent | Tasks                                  | Repos                                                                          |
| ----- | -------------------------------------- | ------------------------------------------------------------------------------ |
| A7    | §5.1c float fields (features.py)       | unified-internal-contracts, unified-api-contracts                              |
| A8    | §12 gs:// migration + lint gate        | market-data-processing-service, unified-trading-pm                             |
| A9    | §2.5 mixin split + §2.6 type:ignore    | market-data-processing-service                                                 |
| A10   | §6.6 MiFID event + §13.2 TODO tracking | unified-events-interface, unified-trading-pm                                   |
| A11   | §16 npm drift + §8.1 baseline docs     | settlement-ui, deployment-ui, unified-admin-ui, market-data-processing-service |

## Key Technical Decisions

- **HTTP not gRPC** for deployment-api: `deployment_api/clients/deployment_service_client.py` already exists with all
  endpoint definitions — just needs the server side wired in deployment-service
- **Decimal not custom field**: use `from decimal import Decimal` (19+ files already use this pattern)
- **CI rollout via script**: new `rollout-quality-gates-ci-workflows.py` following `rollout-agent-workflows.sh` pattern
  (read manifest → patch each repo's workflow YAML → commit)
