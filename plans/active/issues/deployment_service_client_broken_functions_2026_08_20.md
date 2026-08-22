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

**CORRECTED 2026-08-22 — the original root cause below was wrong.** The remaining functions use
`DEPLOYMENT_SERVICE_URL` (default `http://localhost:9000`) and deployment-api has no URL override — that part holds.
But the claim that "deployment-service is not deployed as a reachable Cloud Run Service" is FALSE, verified against
live prod:

| Probe (2026-08-22) | Result |
| --- | --- |
| `gcloud run services list` | `deployment-dashboard` live, ready `True` |
| `GET /openapi.json` | all 13 `/api/v1/...` routes present |
| `GET /api/v1/data-coverage-summary?service=instruments-service` | **HTTP 200, real payload** |
| `POST /api/v1/cloud-run/status-batch` | **HTTP 422** (body validation) — route live, not 404/refused |
| `get-iam-policy deployment-dashboard` | `allUsers` -> `roles/run.invoker` — public, no ID token needed |
| `describe uts-shared-deployment-api` | 14 env vars; `DEPLOYMENT_SERVICE_URL` **not among them** |

`deployment-dashboard` IS deployment-service's own FastAPI app: its cloudbuild builds `--target api`, whose CMD is
`gunicorn deployment_service.api.main:app`, and `main.py` mounts `api/routes/state.py` at prefix `/api/v1`.

So the fix is ONE unset environment variable, not nine transport conversions. `create_deployment()`'s subprocess
mechanism (`deployment_service_client.py:197-264`) stays — it is the right shape for a heavy one-shot mutation — but
it is NOT the template for these nine read/query paths, and it was never necessitated by an absent server.

## Required follow-up

**SUPERSEDED 2026-08-22 by the corrected root cause above.** The original direction — convert all nine to
CLI/subprocess transport — was chosen on the false premise that no server existed. It does. Set
`DEPLOYMENT_SERVICE_URL` on deployment-api's Cloud Run deploy to the `deployment-dashboard` URL and all nine live
paths work as written, with their existing response contracts and caller error handling untouched. No long-lived
service needs standing up: it is already standing.

The two uncalled quota helpers are unaffected — remove or retire them only after confirming no external consumer.

**Converted to tracked todos 2026-08-20 (/plan-reconcile F-G12-1)** — this prose had zero checkboxes anywhere in the
corpus despite documenting nine live production-broken endpoints; per the HARD RULE "every follow-up is a `- [ ]`
todo, never prose."

**➡️ EXTRACTED 2026-08-21 (ag-closeout-audit, infra tranche Phase 3) — all 11 todos below →
`plans/active/infra_satellite_ao_dispatch_batch2_2026_08_21.md` todos 1-11.**

**RE-SCOPED 2026-08-22** — these were nine separate "convert the transport" todos written against a root cause
that turned out to be wrong (see Finding). One env var fixes all nine; what remains per-function is *verification*,
not conversion.

- [ ] [BACKEND] P0. **Root-cause fix, unblocks all nine below.** Set `DEPLOYMENT_SERVICE_URL` to the
      `deployment-dashboard` Cloud Run URL in deployment-api's `gcloud run deploy uts-shared-deployment-api`
      command (deployment-api/cloudbuild.yaml). Target is `allUsers`-invokable, so no ID-token plumbing is
      required — verified 2026-08-22. Also make an unset/localhost value loud at startup (assertion or health-check
      field) rather than silent, since that is exactly how this went unnoticed. Repo: deployment-api.
**Each of the nine below is gated on P0 and is now a VERIFICATION, not a conversion.** A green unit test does
NOT count — they mock the HTTP call, which is why this stayed invisible so long
(`/codex/12-agent-workflow/measurement-claims-discipline.md`: a proxy is not the property).

- [ ] [BACKEND] P1. Verify `calculate_shards` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live callers `deployment_manager.py:200,320`.
- [ ] [BACKEND] P1. Verify `get_data_status` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live callers `routes/data_status_helpers.py:43` and UI `DataStatusTab.tsx`
      (`:832`, `:855`, `:943` via `api/client.ts:628-680`).
- [ ] [BACKEND] P1. Verify `cancel_vm_jobs` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live caller `_deployment_processor_helpers.py:36-65`.
- [ ] [BACKEND] P1. Verify `get_vm_status_batch` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live caller `routes/deployment_state.py:287`.
- [ ] [BACKEND] P1. Verify `get_cloud_run_status_batch` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live callers `_deployment_processor_cloud_run.py:33`,
      `services/event_processor.py:332`, `routes/deployment_state.py:223`.
- [ ] [BACKEND] P1. Verify `get_deployment_events` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live callers `routes/deployments/_lifecycle.py:272-303` and UI
      `DeploymentDetails.tsx:411` via `api/client.ts:3804-3809`.
- [ ] [BACKEND] P1. Verify `get_vm_events` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live caller `routes/deployments/_lifecycle.py:303-338`.
- [ ] [BACKEND] P1. Verify `live_rollback` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live callers `routes/deployments/_lifecycle.py:341-373` and UI
      `DeploymentDetails.tsx:441` via `api/client.ts:3826-3834`.
- [ ] [BACKEND] P1. Verify `get_live_health` end-to-end against prod once `DEPLOYMENT_SERVICE_URL` is set — live callers `routes/deployments/_lifecycle.py:376-415` and UI
      `DeploymentDetails.tsx:423` via `api/client.ts:3840-3847`.
- [ ] [BACKEND] P3. Confirm `quota_acquire_batch` has no external consumer (only self-contained definition at
      `deployment_service_client.py:453-488`, no in-repo caller found), then remove it as dead code.
- [ ] [BACKEND] P3. Confirm `quota_release_batch` has no external consumer (only self-contained definition at
      `deployment_service_client.py:535-563`, no in-repo caller found), then remove it as dead code.

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
- **2026-08-22 (slot-30, interactive):** Root cause CORRECTED against live prod. The 2026-08-20 diagnosis
  ("deployment-service is not deployed as a reachable Cloud Run Service") is false — `deployment-dashboard` IS
  deployment-service's FastAPI app, live and publicly invokable, serving all 13 `/api/v1` routes;
  `GET /api/v1/data-coverage-summary` returned HTTP 200 with a real payload during this session. The defect is that
  `DEPLOYMENT_SERVICE_URL` is never set on `uts-shared-deployment-api` (14 env vars, absent from all of them), so
  every call dials the `http://localhost:9000` default. Nine transport-conversion todos re-scoped to one env-var fix
  plus nine verifications. The misleading claim was also corrected at its source in
  `deployment-api/deployment_api/clients/deployment_service_client.py`'s module docstring, which is where it
  originated and which had already misdirected at least one downstream session.
