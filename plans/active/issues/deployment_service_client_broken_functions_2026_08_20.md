---
doc_type: issue
title: >-
  deployment-api deployment_service_client: nine live callers still use the unreachable deployment-service HTTP API
summary: >-
  The audit of every function other than create_deployment() found nine functions with concrete deployment-api call
  chains. They still POST/GET through DEPLOYMENT_SERVICE_URL, whose production default is http://localhost:9000 and
  has no Cloud Run Service deployment, so each live path is broken for the same root cause fixed in create_deployment().
  The two quota helpers have no callers in deployment-api or deployment-ui and are dead candidates, not live incidents.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui]
scope: [engineer]
tags: [deployment, deployment-service, http-client, production-bug, dead-code-audit]
related:
  [
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
  ]
created: 2026-08-20
author: slot-15
parent_epic: security_and_cross_cutting_master
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  2026-08-20 slot-15 audit of deployment-api/deployment_api/clients/deployment_service_client.py, tracing all exact
  call sites under deployment-api/deployment_api/ and the corresponding deployment-ui API/component surface.
context_scope:
  [
    deployment-api/deployment_api/clients/deployment_service_client.py,
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    deployment-api/deployment_api/services/deployment_manager.py,
    deployment-api/deployment_api/routes/deployments/_lifecycle.py,
    deployment-api/deployment_api/routes/deployment_state.py,
    deployment-api/deployment_api/routes/data_status_helpers.py,
  ]
---

# Nine live-broken deployment-service client functions

## Finding

`deployment_service_client.py:6-13` records the verified production root cause: the remaining functions use
`DEPLOYMENT_SERVICE_URL` (default `http://localhost:9000`), while deployment-service is not deployed as a reachable
Cloud Run Service and deployment-api has no URL override. `create_deployment()` is already the reference fix: it
invokes the bundled deployment-service CLI in a subprocess (`deployment_service_client.py:18-27, 197-264`).

## Required follow-up

Apply the same operator-approved CLI/library transport direction to the nine live functions, preserving each function's
existing response contract and caller error handling. Remove or explicitly retire the two uncalled quota helpers only
after confirming no external consumer exists; do not stand up a long-lived deployment-service HTTP service as a fix.

## Audit evidence

| Function | Live caller | Evidence | Recommendation |
| --- | --- | --- | --- |
| `calculate_shards` | Yes | `deployment_manager.py:200` and `:320` | Fix like `create_deployment()` |
| `get_data_status` | Yes | `routes/data_status_helpers.py:43`; UI `DataStatusTab.tsx:832`, `:855`, `:943` via `api/client.ts:628-680` | Fix like `create_deployment()` |
| `cancel_vm_jobs` | Yes | `_deployment_processor_helpers.py:36-65` | Fix like `create_deployment()` |
| `get_vm_status_batch` | Yes | `routes/deployment_state.py:287` | Fix like `create_deployment()` |
| `quota_acquire_batch` | No | Only definition and self-contained implementation at `deployment_service_client.py:453-488`; no other exact call site under deployment-api or deployment-ui | Remove after external-consumer check, or leave until confirmed dead |
| `get_cloud_run_status_batch` | Yes | `_deployment_processor_cloud_run.py:33`; `services/event_processor.py:332`; `routes/deployment_state.py:223` | Fix like `create_deployment()` |
| `quota_release_batch` | No | Only definition and self-contained implementation at `deployment_service_client.py:535-563`; no other exact call site under deployment-api or deployment-ui | Remove after external-consumer check, or leave until confirmed dead |
| `get_deployment_events` | Yes | `routes/deployments/_lifecycle.py:272-303`; UI `DeploymentDetails.tsx:411` via `api/client.ts:3804-3809` | Fix like `create_deployment()` |
| `get_vm_events` | Yes | `routes/deployments/_lifecycle.py:303-338` | Fix like `create_deployment()` |
| `live_rollback` | Yes | `routes/deployments/_lifecycle.py:341-373`; UI `DeploymentDetails.tsx:441` via `api/client.ts:3826-3834` | Fix like `create_deployment()` |
| `get_live_health` | Yes | `routes/deployments/_lifecycle.py:376-415`; UI `DeploymentDetails.tsx:423` via `api/client.ts:3840-3847` | Fix like `create_deployment()` |

The nine `Yes` rows are live-broken because their implementations still construct HTTP requests through
`_base_url()` (`deployment_service_client.py:55-57`) and the module documents that all remaining functions retain the
same unreachable-HTTP defect (`deployment_service_client.py:29-31`).

## Progress Log

- **2026-08-20 (slot-15):** Audit completed and all nine live call chains plus both uncalled quota helpers were
  independently traced. No code was changed. Follow-up issue filed from the parent plan's required findings triage.
- **context-scout 2026-08-20**: trimmed context_scope to 6 entries (from 9, all source-only) — added the parent
  cleanup plan as the pattern-precedent citation.
