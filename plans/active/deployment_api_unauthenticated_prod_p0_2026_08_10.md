---
doc_type: plan
title:
  "P0 — deployment-api prod is reachable unauthenticated from the public internet (DISABLE_AUTH=true + allUsers invoker
  + guard reading the wrong env var); close the gap without breaking existing callers"
summary: >-
  Escalation of `/plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md`, whose 4 `[BACKEND] P1`
  fix-steps sat unactioned for 4 days because the doc was mistagged `[cross-cutting]` and no tranche's closeout ever
  claimed it. Re-verified LIVE 2026-08-10 against the running Cloud Run service, and the real exposure is broader than
  the source doc recorded: the service has `ingress: all` AND `allUsers` bound to `roles/run.invoker`, so no GCP-level
  auth gates it either. Combined with `DISABLE_AUTH=true` and the application guard reading `ENVIRONMENT` (unset) rather
  than `DEPLOYMENT_ENV` (set to `prod`), every route on `_authenticated_router` — including `POST
  /api/deployments/{service}/deploy` — is invocable by anyone on the internet with zero credentials. The fix is NOT a
  blind flip: the source doc's own analysis, and the `service-deployed-listener.yml` note, both establish that live
  callers currently depend on the no-credential path, so enforcing auth before auditing and updating them would break
  prod deploys. Hence the strict order below (`sequential: true`) — decide the env SSOT, issue and wire the key, audit
  and fix every caller, and only then flip enforcement and verify a credential-less request gets 401.
status: active
nature: issue
asset_group: [ui]
stage: [meta]
repos: [deployment-api, unified-trading-library, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [security, p0, deployment-api, unauthenticated-prod, disable-auth, escalation, cloud-run-iam]
related:
  [
    /plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md,
    /plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md,
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_07.md,
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md,
    /plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
effort: high
drift_direction: none
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
  ]
source: >-
  Operator ruling 2026-08-10 (interactive session, slot 1): escalate the 4 open fix-steps in
  `deployment_api_prod_disable_auth_true_2026_08_06.md` to their own P0 rather than leaving them behind the P3 hygiene
  todos of `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`. Live re-verification performed in the same
  session (`gcloud run services describe` + `get-iam-policy`, asia-northeast1) confirmed the exposure is still present
  and added the two IAM/ingress facts the source doc did not record.
---

# P0 — deployment-api prod reachable unauthenticated from the public internet

## Live evidence (re-verified 2026-08-10, not inherited from the source doc)

`gcloud run services describe uts-shared-deployment-api --region asia-northeast1`:

| Fact                                                | Value                                                       |
| --------------------------------------------------- | ----------------------------------------------------------- |
| `spec.template.spec.containers[0].env DISABLE_AUTH` | `true`                                                      |
| `... DEPLOYMENT_ENV`                                | `prod`                                                      |
| `... ENVIRONMENT`                                   | **unset** — this is the var the guard actually reads        |
| `... API_KEY`                                       | **unset** — `verify_api_key()`'s expected key is None       |
| `metadata.annotations run.googleapis.com/ingress`   | `all` (public internet)                                     |
| `get-iam-policy`                                    | `allUsers` → `roles/run.invoker`                            |
| `status.url`                                        | `https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app` |

`deployment_api/auth.py` raises only when `_disable_auth_raw and _environment == "production"`. `_environment` is
`UnifiedCloudConfig.environment`, sourced from `ENVIRONMENT` — which is unset — so the condition is `True and False` →
the service boots with `DISABLE_AUTH=true`. `verify_api_key()` and `firebase_auth.verify_any_auth()` both return a mock
principal before reading any header. Net: every `_authenticated_router` route (`/api/deployments/*` including the manual
`POST /api/deployments/{service}/deploy`, `/api/services/*`, `/api/builds/*`) answers unauthenticated requests from the
open internet.

**The two IAM/ingress rows above are new** — the 2026-08-06 source doc recorded only the application-layer gap, so the
exposure was understated as "reachable from the service's public Cloud Run URL" without noting that nothing at the GCP
layer gates it either.

**Not probed.** The exposure is established from configuration alone; no unauthenticated request was issued against the
live endpoint. Do not "verify" this finding by calling a mutating route.

## Why this is NOT a blind flip (read before starting)

The source doc's own analysis and `scripts/cicd/handle_service_deployed_dispatch.py::_deploy_one` establish that live
callers depend on the credential-less path today — `service-deployed-listener.yml` deliberately sends no `X-API-Key`
because `DEPLOYMENT_API_KEY` is intentionally unset, and it works _only_ because of this gap. deployment-ui and other CI
automation may be in the same position. Enforcing auth before auditing and updating callers converts a confidentiality
problem into a prod-deploy outage. That is why this plan is `sequential: true`: the steps are a real dependency chain,
not independent work.

**Interim mitigation is an operator decision, not a worker one.** Dropping the `allUsers` invoker binding or setting
`ingress: internal-and-cloud-load-balancing` would shrink the blast radius in one command, but would break exactly the
callers step 3 exists to enumerate. Do not arm it unilaterally — raise it and let the operator choose, per
`/codex/04-architecture/autonomous-recovery-matrix.md` (protective arming is autonomous only where it cannot itself
cause an outage).

## Todos

- [x] ✅ [BACKEND] P0. **Decide the env SSOT and fix the guard.** — UTL@336f2b3b6c + deployment-api@d0eebac4e6.

      **Decision: Option (a)** — make the guard read both `ENVIRONMENT` and `DEPLOYMENT_ENV`.

          **Consumer enumeration of `UnifiedCloudConfig.environment`** (the `ENVIRONMENT` var):
          1. `deployment-api/auth.py:19` — the broken prod guard (FIXED)
          2. `unified-trading-api/middleware/auth.py:29` — identical guard pattern (same latent bug, out of scope for this plan)
          3. `unified-trading-api/routes/health.py:144` — diagnostic only (`"app_env"`), no behavioral impact
          4. `UTL core/config.py:573,578` — `is_production`/`is_development` properties (library code, shared by all services)
          5. `UTL cloud_config.py:795-805` — same `is_production`/`is_development`/`is_testing` on UnifiedCloudConfig
          6. `UTL secret_manager.py:164` — secret name resolution (env-normalized)
          7. `UTL sampling_service.py:59` — sampling env (env-normalized)
          8. `UTL cloud_auth_factory.py:131,158,184` — auth factory env resolution
          9. `UTL service_runtime.py:207` — runtime env value

          **Why Option (a) doesn't break any of the above**: the new `deployment_env` field is purely additive — it reads `DEPLOYMENT_ENV` alongside the existing `environment` field which still reads `ENVIRONMENT`. No existing consumer's behavior changes. Option (b) (`ENVIRONMENT=production`) would change behavior for ALL 9 consumers on the prod service, some of which (secret_manager, sampling_service) may have production-specific code paths that were never exercised because `ENVIRONMENT` was always unset.

          **Implementation**: Added `deployment_env: str` to `BaseConfig` (reads `DEPLOYMENT_ENV`, default `""`). Updated `deployment_api/auth.py` guard to: `if _disable_auth_raw and (_environment == "production" or _deployment_env in ("production", "prod"))`. Guard logic verified — condition evaluates True when `DEPLOYMENT_ENV=prod`. Do NOT deploy to prod — that is step 4.

- [ ] [BACKEND] P0. **Issue a real deployment-api API key and wire it.** Generate a high-entropy key, store it as a GSM
      secret in `central-element-323112`, wire it into the prod Cloud Run service's env via the deploy path (not a
      console edit), and populate a `DEPLOYMENT_API_KEY` GH secret on every repo whose CI calls deployment-api
      server-to-server — starting with `deployment-service` (`service-deployed-listener.yml`). No client code change is
      needed there: `_deploy_one` already sends the header when the value is non-empty. **Done when**:
      `verify_api_key()`'s expected key resolves to a real non-None value in prod AND the listener is confirmed sending
      the header. Self-issuable — GSM secret creation is within the orchestrator's IAM self-service scope
      (`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`), so this is NOT operator-gated.
- [ ] [BACKEND] P0. **Audit every current caller of `_authenticated_router` routes and fix the ones with no
      credential.** Cover deployment-ui, every CI workflow across all repos, and any documented manual `curl`/`gh api`
      usage. For each: does it already send `X-API-Key` or a Firebase token? **Done when**: a complete caller inventory
      is recorded in this plan with a per-caller credential verdict, and every credential-less caller has been updated
      and shipped. This is the step that makes step 4 safe — do not shortcut it to a grep; a caller invoking the public
      URL from outside this workspace would not appear in any repo search, so also check the Cloud Run request logs for
      distinct callers over a recent window and reconcile against the inventory.
- [ ] [BACKEND] P0. **Flip enforcement and prove the hole is closed.** Ship the step-1 guard/env change to prod so
      `DISABLE_AUTH=true` is genuinely rejected there, confirm the service still boots with the real key wired in, and
      confirm a request carrying no credential now receives 401. Watch for 401s from legitimate callers for a full
      deploy cycle afterward and roll back if any appear. **Done when**: a credential-less request returns 401, an
      authenticated request succeeds, and one real end-to-end deploy has completed through the listener post-flip.
- [ ] [BACKEND] P1. **Re-evaluate `ingress: all` + the `allUsers` invoker binding once app-layer auth is enforced.**
      With a real key required, public ingress may still be intentional (external CI callers) or may be removable
      defence-in-depth. **Done when**: an explicit keep-or-restrict verdict is recorded with the reasoning, and if
      restricting, the change is shipped and callers re-verified.

## Codex SSOTs

- `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` — why the GSM secret in step 2 is self-issuable
- `/codex/04-architecture/autonomous-recovery-matrix.md` — why interim ingress/IAM lockdown is not autonomous here
- `/codex/06-coding-standards/config-reloader-pattern.md` — `UnifiedCloudConfig` field semantics for step 1

## Progress Log

- **2026-08-10** — Escalated from `deployment_api_prod_disable_auth_true_2026_08_06.md` per operator ruling. Live
  re-verification confirmed the gap is still open on day 4 and surfaced two facts the source doc lacked (`ingress: all`,
  `allUsers` → `roles/run.invoker`), which broaden the exposure from "public Cloud Run URL" to "nothing gates it at the
  GCP layer either". Operator notified in-session at the moment of discovery; no mitigation armed, since every candidate
  mitigation risks breaking the very callers step 3 exists to enumerate, and the operator was mid-CI-fix.
- **2026-08-10 (slot 9)** — Todo 1 complete. Decision: Option (a). Added `deployment_env` field to `BaseConfig`
  (`unified-trading-library@336f2b3b6c`) reading `DEPLOYMENT_ENV`. Updated `deployment_api/auth.py` guard
  (`deployment-api@d0eebac4e6`) to check both `ENVIRONMENT` and `DEPLOYMENT_ENV`. Enumerated 9 consumers of
  `UnifiedCloudConfig.environment` — none broken by this additive change. Guard logic verified: condition
  `_deployment_env in ("production", "prod")` evaluates True when `DEPLOYMENT_ENV=prod`. Not deployed to prod (that's
  step 4).
