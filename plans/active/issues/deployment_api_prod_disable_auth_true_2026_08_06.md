---
doc_type: issue
title: >-
  DISABLE_AUTH=true is live on prod uts-shared-deployment-api Cloud Run service — deployment-api's own production-guard
  is silently defeated because ENVIRONMENT is unset, not "production"
summary: >-
  Found while wiring the `service-deployed` dispatch listener (deployment-service + deployment-api's `deploy_build()`) —
  needed to confirm what auth deployment-api's `POST /api/deployments/{service}/deploy` requires from a machine caller.
  `deployment_api/auth.py` has an explicit startup guard: `if DISABLE_AUTH and ENVIRONMENT == "production": raise
  RuntimeError("DISABLE_AUTH=true is forbidden in production...")`. Live-checked the actual prod Cloud Run env (`gcloud
  run services describe uts-shared-deployment-api --project=<prod project> --region=asia-northeast1
  --format="json(spec.template.spec.containers[0].env)"`, 2026-08-06) and found `DISABLE_AUTH: "true"` set directly on
  the running revision, alongside `DEPLOYMENT_ENV: "prod"` — but there is NO `ENVIRONMENT` env var set at all.
  `UnifiedCloudConfig.environment` (what `auth.py`'s guard actually reads) is a DIFFERENT field from `DEPLOYMENT_ENV`,
  so it falls through to its own default (not `"production"`), the guard's `== "production"` check is False, and the
  service boots fine with auth fully disabled. Net effect: `verify_api_key()` / `verify_any_auth()` both short-circuit
  to a mock identity before checking any header — every route under `_authenticated_router` (`/api/deployments/*`,
  `/api/services/*`, `/api/builds/*`, and everything else registered there) is currently reachable from the public Cloud
  Run URL with ZERO authentication. This is the exact misconfiguration the guard exists to prevent, and it is defeated
  by an env-var-name mismatch rather than the guard being wrong — `DEPLOYMENT_ENV=prod` is the value someone clearly
  intended as "this is production", it just isn't the variable the guard reads. Did NOT fix this in the current task
  (out of scope — this repo's `service-deployed` listener work is scoped tightly to the dispatch/redeploy mechanism, and
  fixing prod auth is a separate, higher-blast-radius change: flipping DISABLE_AUTH off live could break any existing
  caller — deployment-ui, other automation — that currently sends no credential at all, so it needs its own audit of who
  calls this service and how, not a same-session fix bundled into an unrelated task). Practical implication for THIS
  task: the new `service-deployed-listener.yml` workflow currently omits the `X-API-Key` header when
  `DEPLOYMENT_API_KEY` (a not-yet-created GH secret) is unset — which works today only because of this gap, and will
  start requiring a real key the moment it's closed (no code change needed on the listener side when that happens).
status: open
resolved_by:
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, unified-trading-library]
scope: [engineer, admin]
tags: [security, auth, prod, deployment-api, cloud-run, disable-auth, misconfiguration]
related: [/plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md]
created: 2026-08-06
author: sub-agent (service-deployed dispatch listener task)
last_updated: 2026-08-06
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    "sub-agent session, 2026-08-06 — service-deployed dispatch listener task, `gcloud run services describe
    uts-shared-deployment-api`",
  ]
context_scope:
  [
    deployment-api/deployment_api/auth.py,
    deployment-api/deployment_api/firebase_auth.py,
    deployment-api/deployment_api/main.py,
    unified-trading-library/unified_trading_library/config_interface/cloud_config.py,
  ]
---

## What was found

Live, 2026-08-06,
`gcloud run services describe uts-shared-deployment-api --project <prod GCP project> --region asia-northeast1 --format="json(spec.template.spec.containers[0].env)"`:

```json
{
  "DISABLE_AUTH": "true",
  "DEPLOYMENT_ENV": "prod",
  "GCP_PROJECT_ID": "<prod GCP project>",
  "CLOUD_PROVIDER": "gcp",
  "CLOUD_MOCK_MODE": "false",
  "WORKERS": "2"
}
```

No `ENVIRONMENT` key is set anywhere in this env list.

`deployment_api/auth.py` (current code):

```python
_auth_cfg = UnifiedCloudConfig()
_disable_auth_raw: bool = _auth_cfg.disable_auth
_environment: str = _auth_cfg.environment
if _disable_auth_raw and _environment == "production":
    ...
    raise RuntimeError("DISABLE_AUTH=true is forbidden in production. ...")
DISABLE_AUTH: bool = _disable_auth_raw
```

`_auth_cfg.environment` is `UnifiedCloudConfig.environment` (a distinct field from `DEPLOYMENT_ENV`, which the Cloud Run
service DOES set to `"prod"` — someone clearly intended to mark this as production, just via the wrong variable name for
this specific guard). With `ENVIRONMENT` unset, `_auth_cfg.environment` resolves to whatever `UnifiedCloudConfig`'s own
default is (not `"production"`), so the guard's condition is `True and False` → `False` → the service boots normally
with `DISABLE_AUTH=true` live.

Runtime effect: `deployment_api/auth.py::verify_api_key()` and `deployment_api/firebase_auth.py::verify_any_auth()` both
start with `if DISABLE_AUTH: return "dev-mode"` / `return _MOCK_EMAIL` — before looking at any header at all. Every
route mounted on `_authenticated_router` in `deployment_api/main.py` (`/api/deployments/*` including the manual
`POST /api/deployments/{service}/deploy` used by both the deployment-ui Deploy console and the new `service-deployed`
listener, `/api/services/*`, `/api/builds/*`, and the rest of that router) is reachable from the service's public Cloud
Run URL with zero authentication today.

## Why this wasn't fixed in-session

Found as a side effect of confirming what auth header the new `service-deployed` listener
(`deployment-service/.github/workflows/service-deployed-listener.yml` +
`scripts/cicd/handle_service_deployed_dispatch.py`) needs to send. Flipping this live is a separate, higher-blast-radius
change than that task: it's not known which existing callers (deployment-ui, other CI automation, manual `curl`/`gh api`
usage) currently rely on the no-credential path, so turning auth on could break something without warning. This needs
its own scoped audit (who calls `_authenticated_router` routes today, do they already send `X-API-Key`/Firebase tokens,
what does closing the gap require) rather than a same-session fix bundled into an unrelated dispatch-listener task.

## Recommended fix shape (not yet actioned)

Either: (a) make the guard read `DEPLOYMENT_ENV` (or both `ENVIRONMENT` and `DEPLOYMENT_ENV`) so `DEPLOYMENT_ENV=prod`
actually trips it, or (b) set `ENVIRONMENT=production` explicitly on the prod Cloud Run service's env (terraform /
deploy script), whichever matches the intended long-term SSOT for "what counts as production" across the fleet — check
for other consumers of `UnifiedCloudConfig.environment` before picking one, since a rename could affect more than just
this guard.

Either fix needs a proper API key issued + wired into the Cloud Run service's env (currently there's no evidence one is
even configured — `verify_api_key()`'s `expected_key = _auth_cfg.api_key` would need a real, non-None value) and every
existing legitimate caller updated to send it, verified via a staged rollout (flip in a non-prod environment first, or
add the header everywhere and watch for 401s before enforcing) rather than a blind flip.

## Practical implication for the service-deployed listener (2026-08-06)

`service-deployed-listener.yml` currently sends no `X-API-Key` header when `DEPLOYMENT_API_KEY` (a GH secret
intentionally left unset) is empty — see `scripts/cicd/handle_service_deployed_dispatch.py::_deploy_one`'s docstring.
This works ONLY because of the gap documented here. No code change is needed on the listener side once this is fixed —
populate `DEPLOYMENT_API_KEY` with the real key and the listener will start sending it automatically
(`if api_key: headers["X-API-Key"] = api_key`).

## Resolution

- [ ] [BACKEND] P1. Decide fix shape (a) vs (b) above, confirm no other `UnifiedCloudConfig.environment` consumer would
      be broken by either choice.
- [ ] [BACKEND] P1. Issue a real deployment-api API key (GSM secret), wire it into the prod Cloud Run service's env, and
      populate a `DEPLOYMENT_API_KEY` GH secret on every repo whose CI calls deployment-api server-to-server (starting
      with `deployment-service`'s `service-deployed-listener.yml`).
- [ ] [BACKEND] P1. Audit every current caller of `_authenticated_router` routes (deployment-ui, other CI workflows,
      manual usage) for whether they already send a credential; fix any that don't before enforcing.
- [ ] [BACKEND] P1. Flip the guard/env so `DISABLE_AUTH=true` is actually rejected in prod, verify the service still
      boots with the real key wired in, and confirm a request with no credential now gets 401.

## Progress Log

- **context-scout 2026-08-07**: populated context_scope (4 entries) — the guard (`auth.py`), the sibling auth path
  (`firebase_auth.py`), the router mount point naming every affected route family (`main.py`), and the config field the
  guard actually reads vs. the one the Cloud Run env sets (`cloud_config.py`) — all four already named directly in the
  doc's own body.
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — all 4 open `[BACKEND] P1` todos gate on
  a real architecture/blast-radius decision (fix shape (a) vs (b), then issue+wire a real API key, audit every current
  caller, then flip the guard) that risks breaking any existing no-credential caller if done blind — genuine judgment +
  staged-rollout work, not a mechanical fix. **NOTIFY-OPERATOR flagged**: this doc documents a LIVE prod Cloud Run
  service (`uts-shared-deployment-api`) reachable with ZERO authentication right now (`DISABLE_AUTH=true` defeats the
  guard via an `ENVIRONMENT`/`DEPLOYMENT_ENV` name mismatch) — re-flagged here since no Progress Log entry since
  2026-08-06 shows this was fixed or operator-acknowledged.
- **plan_reconciler 2026-08-10 (cross-cutting tranche, dispatch `agt-33a6ec`)**: re-verified live — all 4 `[BACKEND] P1`
  todos still open, 4+ days since creation with no fix/ack in between (2026-08-08's `ag-closeout-audit` parked-findings
  runs re-flagged this same gap twice more, still unresolved). Given the severity (live unauthenticated prod endpoint)
  and staleness, escalated NOW rather than waiting for this run's end-of-pass routing: filed `BLK-46b42d75` asking the
  operator to pick fix shape (a) vs (b) vs (c) (see this doc's own "Recommended fix shape" section above for a/b).
  Before recommending, grepped the whole workspace for other consumers of `UnifiedCloudConfig.environment` (7 total,
  across `deployment-api`/`strategy-service`/`alerting-service`/`unified-trading-api`) — confirmed neither fix shape (a)
  nor (b) touches any of the other 6, since both are self-contained to `deployment-api`'s own guard/env (fix (a) adds a
  second string check inside `auth.py` without changing what `UnifiedCloudConfig.environment` resolves to anywhere else;
  fix (b) only sets an env var on `deployment-api`'s own Cloud Run revision). Recommended (A) on that basis — it fixes
  the actual root-cause name mismatch rather than papering over it with a value that happens to satisfy the current
  check. Did not attempt the live-traffic caller audit (todo 3) or the actual fix (out of scope for a
  plan-reconciliation pass — this is application code + live infra, not a plan doc). Not flipping any of the 4 todos;
  this remains genuinely operator-gated per the 2026-08-07 verdict above, now with a narrower, evidence-backed choice in
  front of the operator instead of an open-ended one.
