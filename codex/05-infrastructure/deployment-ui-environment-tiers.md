---
title: Deployment-UI environment tiers — dev / staging / prod
scope: [engineer]
owner: harsh
status: stable
codified: 2026-05-18
last_reviewed: 2026-05-18
sources:
  - plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md (Phase H)
  - codex/05-infrastructure/deployment-ui-architecture.md
  - codex/05-infrastructure/firebase-split-topology.md
  - codex/05-infrastructure/bucket-isolation-model.md
  - codex/05-infrastructure/runtime-tiers-and-deployment.md
---

# Deployment-UI environment tiers — dev / staging / prod

## Overview

The deployment-UI and its backing deployment-api run in three tiers that exactly mirror the trading-system-UI pattern
documented in [`firebase-split-topology.md`](firebase-split-topology.md). **There is no in-UI environment toggle.** The
env is resolved from the domain at boot and never changes at runtime.

## Tier topology

| Tier      | Hostname                               | deployment-api Cloud Run    | GCP project      | GCS event bucket scope   |
| --------- | -------------------------------------- | --------------------------- | ---------------- | ------------------------ |
| `dev`     | `localhost:5183`                       | local uvicorn               | dev / mock       | local (no GCS writes)    |
| `staging` | `staging.<research-domain>/deployment` | Cloud Run (staging project) | staging GCP proj | `<staging-pid>-events-*` |
| `prod`    | `<research-domain>/deployment`         | Cloud Run (prod project)    | prod GCP proj    | `<prod-pid>-events-*`    |

## Env resolution rules

### Backend: `CLOUD_DEPLOYMENT_ENV` env var

`deployment-api` reads env tier from `CLOUD_DEPLOYMENT_ENV` (via `DeploymentApiConfig.deployment_env`) at boot. All 4
Monitor endpoint responses carry an `env` field populated from `settings.DEPLOYMENT_ENV` so the UI can badge the tier.
Cloud Run injects the var; local dev sets it in `.env`.

```
CLOUD_DEPLOYMENT_ENV=dev      → dev tier
CLOUD_DEPLOYMENT_ENV=staging  → staging tier
CLOUD_DEPLOYMENT_ENV=prod     → prod tier (default when unset in Cloud Run prod project)
```

### Frontend: `window.location.hostname`

`deployment-ui` resolves the tier client-side from the hostname at page load (Phase h3, same helper as
trading-system-UI):

```
localhost                           → dev   (green badge)
staging.<research-domain>           → staging (amber badge)
<research-domain>                   → prod  (red badge)
```

The env badge is **read-only** — clicking shows a tooltip with `{env, API_BASE_URL, cloud_target}`, never a dropdown.

## Per-env isolation

Each tier has its own:

| Resource                | Dev            | Staging                            | Prod                            |
| ----------------------- | -------------- | ---------------------------------- | ------------------------------- |
| deployment-api instance | local process  | Cloud Run (staging proj)           | Cloud Run (prod proj)           |
| GCS deployment registry | in-memory mock | `deployment-scripts-<staging-pid>` | `deployment-scripts-<prod-pid>` |
| GCS event/log buckets   | none           | `<staging-pid>-events-*`           | `<prod-pid>-events-*`           |
| Cloud Scheduler entries | none           | staging project entries            | prod project entries            |
| Live strategy clusters  | none           | staging paper-trade VMs            | prod live/paper VMs             |
| Firebase Auth project   | local mock     | staging Firebase project           | prod Firebase project           |
| Service account         | ADC            | staging SA                         | prod SA (scoped to prod only)   |

**No cross-env data leakage**: prod deployment-api service account has IAM bindings only on the prod GCP project.

## Operator iteration loop

```
dev tweaks  →  QG (local)  →  ship to staging  →
    soak (staging schedules + staging live clusters + staging data-status views)  →
    promote to prod
```

This is the identical flow as trading-system-UI (`firebase-split-topology.md` § "Promotion flow").

## Naming conventions

GCS deployment registry bucket: `deployment-scripts-<gcp_project_id>` — env-scoped by project ID automatically.

GCS event/log bucket suffix examples per `bucket-isolation-model.md`:

- Staging: `central-element-323112-staging-events` (illustrative — canonical names in `cloud-providers.yaml`)
- Prod: `central-element-323112-events`

## Phase H shipping status

| Item | Description                             | Status                                    |
| ---- | --------------------------------------- | ----------------------------------------- |
| h1   | This codex doc                          | ✅ 2026-05-18                             |
| h2   | deployment-api env-aware Monitor routes | ✅ 2026-05-18 @78b68c4                    |
| h3   | deployment-ui env badge in Header       | ⏳ in-flight                              |
| h4   | Staging + prod Cloud Run provisioning   | BLOCKED-OPERATOR — DNS + IAM (human-only) |
