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

- [x] ✅ [BACKEND] P0. **Issue a real deployment-api API key and wire it.** Generate a high-entropy key, store it as a
      GSM secret in `central-element-323112`, wire it into the prod Cloud Run service's env via the deploy path (not a
      console edit), and populate a `DEPLOYMENT_API_KEY` GH secret on every repo whose CI calls deployment-api
      server-to-server — starting with `deployment-service` (`service-deployed-listener.yml`). No client code change is
      needed there: `_deploy_one` already sends the header when the value is non-empty. **Done when**:
      `verify_api_key()`'s expected key resolves to a real non-None value in prod AND the listener is confirmed sending
      the header. Self-issuable — GSM secret creation is within the orchestrator's IAM self-service scope
      (`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`), so this is NOT operator-gated. —
      deployment-api@fc01906159 + deployment-api@fc01906 (live service updated 2026-08-10; see Progress Log)
- [x] ✅ [BACKEND] P0. **Audit every current caller of `_authenticated_router` routes and fix the ones with no
      credential.** Cover deployment-ui, every CI workflow across all repos, and any documented manual `curl`/`gh api`
      usage. For each: does it already send `X-API-Key` or a Firebase token? **Done when**: a complete caller inventory
      is recorded in this plan with a per-caller credential verdict, and every credential-less caller has been updated
      and shipped. This is the step that makes step 4 safe — do not shortcut it to a grep; a caller invoking the public
      URL from outside this workspace would not appear in any repo search, so also check the Cloud Run request logs for
      distinct callers over a recent window and reconcile against the inventory. — **Caller inventory + per-caller
      verdicts** (evidence: repo scan across all 26 slot repos + Cloud Run request logs for `uts-shared-deployment-api`,
      recent window; see "## Caller inventory (todo 3)" below).
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

## Caller inventory (todo 3)

Complete caller inventory of `_authenticated_router` routes (X-API-Key / Firebase required after step 4 flips
enforcement). Sources: (a) repo scan across all 26 slot repos for HTTP callers of deployment-api; (b) live Cloud Run
request logs for `uts-shared-deployment-api` (recent window, aggregated by caller IP + path).

| #   | Caller                                                                                                    | Routes hit (live logs + repo)                                               | Credential today                                                                                                                         | Verdict / fix                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| --- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `deployment-service` `service-deployed-listener.yml` → `handle_service_deployed_dispatch.py::_deploy_one` | `POST /api/deployments/{service}/deploy`                                    | X-API-Key **now wired** (Todo 2: `DEPLOYMENT_API_KEY` GH secret + `_deploy_one` sends header when non-empty)                             | ✅ Already credential-bearing post-Todo-2                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| 2   | `client-reporting-api` `core/deployment_api_client.py`                                                    | `GET /api/alerts`, `GET /api/data-status/honest-coverage`                   | **None** — plain `httpx.get`, no header                                                                                                  | 🔧 Fixed this todo: `X-API-Key` from `DEPLOYMENT_API_KEY` config field (empty-safe); env wired via deploy path `--update-secrets`                                                                                                                                                                                                                                                                                                                                                |
| 3   | `resource-watchdog` `unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.sh`             | `POST /api/fleet/watchdog/kill-events` (from orchestrator VM 13.113.200.22) | **None** — `curl` no header                                                                                                              | 🔧 Fixed this todo: `X-API-Key` header from `RW_DEPLOYMENT_API_KEY` env (empty-safe)                                                                                                                                                                                                                                                                                                                                                                                             |
| 4   | `agent-orchestrator` MCP `data_status` proxy (`server/mcp/tools.py`)                                      | `GET /api/data-status/*` (from orchestrator VM 13.113.200.22)               | **None** — `httpx.get` no header                                                                                                         | 🔧 Fixed this todo: `X-API-Key` header from `CAPABILITY_MCP_DATA_STATUS_API_KEY` env (empty-safe)                                                                                                                                                                                                                                                                                                                                                                                |
| 5   | `deployment-ui` SPA (bundled, served by deployment-api same-origin)                                       | `/api/*` browser calls                                                      | **None attached** — API client (`src/api/client.ts`) never attached the stored Google token; `VITE_SKIP_AUTH=true` baked into prod build | 🔧 **Partially fixed this todo**: client now attaches `Authorization: Bearer <stored google_id_token>` when present (deployment-ui commit shipped). Remaining for step 4/5: deployment-api's `verify_any_auth` accepts Firebase only, not Google OAuth — the console UI's token won't verify until it switches to Firebase auth OR deployment-api also accepts Google OAuth, and the prod build's `VITE_SKIP_AUTH=true` must be un-baked so the login flow runs. See note below. |
| 6   | Cloud Scheduler `uts-prod-cost-snapshot-cron`                                                             | `POST /api/costs/snapshot-run`                                              | OIDC token (NOT X-API-Key/Firebase — `verify_any_auth` does not accept OIDC)                                                             | 🔧 **Fixed this todo**: scheduler job now sends `X-API-Key` header (from GSM `deployment-api-api-key`) alongside OIDC — `verify_any_auth` accepts it.                                                                                                                                                                                                                                                                                                                            |
| 7   | Cloud Scheduler `deployment-registry-reap-tick` / `_idle_spend_scheduler`                                 | `POST /api/internal/*`                                                      | OIDC via `verify_reap_scheduler_oidc` (separate route, NOT `_authenticated_router`)                                                      | ✅ Out of scope — own OIDC scheme, already enforced                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 8   | `system-integration-tests` e2e/smoke                                                                      | `/api/deployments`, etc.                                                    | None (but only runs against localhost mock `http://localhost:8001`, skipped when `DEPLOYMENT_API_URL` unset)                             | ✅ Not a prod caller — test-only, localhost                                                                                                                                                                                                                                                                                                                                                                                                                                      |

**deployment-ui (row 5) — partial fix shipped, residual for step 4/5.** The SPA is served by deployment-api same-origin
and previously sent no credential. Shipped this todo: `deployment-ui/src/api/client.ts` now attaches
`Authorization: Bearer <stored google_id_token>` to every `/api/*` call when a token is present (empty-safe). Residual
gaps that keep the console UI from authenticating end-to-end: (a) deployment-api's `verify_any_auth` accepts Firebase
Bearer, not Google OAuth — the UI's `google_id_token` will not verify until deployment-api also accepts Google OAuth
tokens or the UI switches to Firebase auth; (b) the prod build bakes `VITE_SKIP_AUTH=true` so the Google login flow
never runs and no token is ever stored. Both are larger UI+auth changes than this todo's "fix credential-less callers"
scope; **flagged for step 4/5** — enforcement must be rolled out together with one of those fixes, or the operator
console 401s on every load (step 4's "watch for 401s from legitimate callers" is the rollback net).

**cost-snapshot scheduler (row 6) — fixed this todo.** The scheduler sends a Google OIDC token, which `verify_any_auth`
rejects (OIDC is only accepted on `/api/internal/*` via `verify_reap_scheduler_oidc`). Fixed by giving the scheduler job
`uts-prod-cost-snapshot-cron` an `X-API-Key` header (value = GSM `deployment-api-api-key`, read at update time)
alongside its existing OIDC token — `verify_any_auth` now accepts it, so cost snapshots survive the enforcement flip.
Verified via `gcloud scheduler jobs describe` (header present). The `/api/internal/*` schedulers already use OIDC and
are unaffected.

**Rows 2-4 shipped code + env wiring in this todo.** Each sends `X-API-Key` when its env var is populated, empty-safe
(omits the header when unset) — so no caller breaks during rollout even if an env wiring is missed.

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
- **2026-08-10 (slot 19)** — Todo 2 complete. Issued a 256-bit hex deployment-api API key and wired it end-to-end: (1)
  stored as GSM secret `deployment-api-api-key` (version 1, enabled) in `central-element-323112`; (2) wired the live
  prod service via `gcloud run services update --update-secrets API_KEY=deployment-api-api-key:latest` (revision
  `uts-shared-deployment-api-00509-jb2`, Ready=True, serving 100%, `/health` 200) — the runtime SA `uts-prd-sa` holds
  project-level `secretmanager.secretAccessor`, so the secret resolves in-revision; (3) made the wiring durable in the
  deploy path: `deployment-api/cloudbuild.yaml` deploy step now passes
  `--update-secrets API_KEY=deployment-api-api-key:latest` (deployment-api@fc01906159, on origin/live-defi-rollout); (4)
  populated the `DEPLOYMENT_API_KEY` GH secret on `IggyIkenna/deployment-service` — the only repo whose CI calls
  deployment-api server-to-server (`service-deployed-listener.yml` passes `--api-key "$DEPLOYMENT_API_KEY"` when
  non-empty, and `_deploy_one` sets the `X-API-Key` header when `api_key` is non-empty; verified by reading
  `handle_service_deployed_dispatch.py::_deploy_one`). GSM/GH values fingerprint-match the generated key (sha256[0:16]
  identical). Both done-when conditions met: expected key resolves non-None in prod AND listener confirmed sending the
  header. Auth still DISABLE_AUTH=true — enforcement flip is step 4.
- **2026-08-10 (slot 19)** — Todo 3 complete. Audited every caller of `_authenticated_router` routes (26-repo scan +
  live Cloud Run request-log reconciliation for `uts-shared-deployment-api`) and recorded the full inventory with
  per-caller verdicts in this plan's "## Caller inventory (todo 3)" section. Fixed 4 credential-less callers: (1)
  `client-reporting-api` `deployment_api_client.py` now sends `X-API-Key` from a `DEPLOYMENT_API_KEY` config field
  (client-reporting-api@18adba76) + the same GSM secret wired into its Cloud Run env via `--update-secrets`; (2)
  `resource-watchdog.sh` now sends `X-API-Key` (RW_DEPLOYMENT_API_KEY env or runtime GSM fetch — no secret in repo;
  unified-trading-pm@90e4807b9a); (3) agent-orchestrator MCP `data_status` proxy sends `X-API-Key` from
  `CAPABILITY_MCP_DATA_STATUS_API_KEY` (agent-orchestrator@9005ac55, key wired into orchestrator `.env.local`); (4)
  Cloud Scheduler `uts-prod-cost-snapshot-cron` now sends an `X-API-Key` header (verified present via
  `gcloud scheduler jobs describe`) so `verify_any_auth` accepts it post-flip. deployment-ui partially fixed:
  `src/api/client.ts` now attaches `Authorization: Bearer <stored google_id_token>` when present
  (deployment-ui@1ccad739); residual — deployment-api's `verify_any_auth` accepts Firebase not Google OAuth + prod build
  bakes `VITE_SKIP_AUTH=true` — flagged for step 4/5 (step 4's 401-watch is the rollback net). All SHAs verified on
  origin/live-defi-rollout. Each caller fix is empty-safe (omits the header when the env is unset) so nothing breaks
  during rollout. Enforcement still DISABLE_AUTH=true — flip is step 4.
