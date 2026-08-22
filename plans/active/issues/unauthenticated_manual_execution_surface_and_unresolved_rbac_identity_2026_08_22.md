---
doc_type: issue
title: execution-service /manual/* order surface is mounted with no auth dependency, and deployment-api RBAC never resolves a caller identity
summary: >-
  Two independently verified authentication defects found while establishing a ground-truth fact base for the
  client-facing commercial documents on 2026-08-22. First, execution-service mounts its manual order surface
  directly on the app with no auth dependency, while its two sibling instruction routers on the same app both
  carry one. Second, deployment-api's RBAC reads a request-state identity that no production code path ever
  writes, so every permission check falls through to the unauthenticated default. Both surfaces reach real
  order placement or real deployment actions.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, deployment-api]
scope: [engineer]
tags: [security, authentication, rbac, execution, deployment-api]
related:
  [
    /plans/active/commercial_model_doc_reconciliation_2026_08_22.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: ground-truth codebase pass for the commercial-model document reconciliation, 2026-08-22
context_scope:
  [
    /codex/11-project-management/doc-frontmatter-schema.md,
    /plans/active/commercial_model_doc_reconciliation_2026_08_22.md,
  ]
---

# Unauthenticated manual execution surface, and RBAC that never resolves an identity

Both findings surfaced during a read-only ground-truth pass over the codebase on 2026-08-22, run to establish what
the client-facing commercial documents may honestly claim. Neither was the object of the search. Both were then
verified directly rather than taken from the reporting agent.

## Finding 1 — `/manual/*` is mounted with no auth dependency

`execution-service/execution_service/api/manual_instruction_api.py:21` declares:

```python
router = APIRouter(prefix="/manual", tags=["manual-trading"])
```

No `dependencies=[...]`, and a grep for `create_api_auth` or `Depends(` across that module returns nothing.

`execution_service/api/main.py:230-233` mounts it directly on the application:

```python
app.include_router(health_router)
app.include_router(external_instruction_router)
app.include_router(manual_router)
app.include_router(account_instruction_router)
```

There is no authenticated parent router in `main.py`: a grep for `APIRouter(` and `dependencies=[` in that file
returns nothing. This matters because the comparable pattern elsewhere in the estate does exist and does work.
`client-reporting-api` defines `_authenticated_router = APIRouter(dependencies=[Depends(_api_auth)])` and mounts
its routers inside it, which is why an apparently bare router there is in fact authenticated. Nothing equivalent
guards `/manual/*`.

The two sibling routers mounted on the same lines DO carry authentication. `account_instruction_api.py:66-67`
sits behind `create_api_auth("execution-service")`, as does the external instruction router. So this is not a
service-wide posture, it is one router that is missing what its neighbours have.

`main.py`'s own module docstring records that `/manual/*` was registered here on 2026-08-20 specifically because
`POST /manual/instruction` was returning 404 on the deployed service. The surface is therefore deployed and
reachable, not dormant.

**Not yet verified, and it changes the severity:** whether Cloud Run ingress restrictions put a network boundary
in front of this service. The reporting agent found no `ingress`, `allow-unauthenticated` or `allUsers` setting in
any of the three `cloudbuild.yaml` files in these repos, which means the control, if it exists, is configured
outside this codebase. Confirm this against the live Cloud Run service configuration before deciding how urgent
the fix is. A network boundary would downgrade this from critical to a defence-in-depth gap; its absence would
make an unauthenticated order-placement surface publicly reachable.

## Finding 2 — deployment-api RBAC resolves no identity in production

`deployment-api/deployment_api/rbac.py` reads `request.state.user_email` to resolve the caller's role. A
workspace-wide grep for an assignment to `state.user_email` returns hits in exactly one file:
`deployment-api/tests/unit/test_rbac.py`, where the tests set it by hand. No middleware, no dependency and no
route handler in any repo writes it in a production path.

The consequence is that every `require_permission` check resolves against a missing identity and falls through to
the unauthenticated default role. The endpoints behind those checks include `strategy/wizard/deploy` and
`execution/backtest/launch`.

The tests pass because they inject the very state the application never populates, which is why this survived.

## Why this is filed rather than fixed in place

Both are outside the scope of the document reconciliation that found them, both touch deployed services, and
Finding 1's severity depends on infrastructure configuration that has to be read from Cloud Run rather than from
the repositories. Fixing authentication on a live order surface is also not a change to make quietly in the middle
of a documentation pass.

## Todos

- [ ] [OPERATOR] P0. **Determine whether Cloud Run ingress restricts execution-service.** Read the live service
      configuration for ingress settings and IAM invoker bindings. This decides whether Finding 1 is a publicly
      reachable unauthenticated order surface or a defence-in-depth gap behind a network boundary. Everything else
      about Finding 1 follows from the answer.
- [ ] [BACKEND] P0. **Put `/manual/*` behind the same auth dependency its sibling routers use.**
      `create_api_auth("execution-service")`, matching `account_instruction_api` and the external instruction
      router. Enumerate the routes on that router first and confirm each one's caller, since at least one internal
      caller reaches it at `{live_service_execution_url}/manual/instruction` in non-mock mode and will need a
      credential.
- [ ] [BACKEND] P0. **Make deployment-api RBAC resolve a real identity, or fail closed.** Either write
      `request.state.user_email` from the authenticated principal in middleware, or have `rbac.py` raise rather
      than default to a role when no identity is present. Failing closed is the safer default and turns any missed
      wiring into a visible 403 rather than a silent privilege grant.
- [ ] [BACKEND] P1. **Add a regression test that exercises RBAC through the real application stack**, not by
      setting `request.state` by hand. The current unit tests pass precisely because they inject state the
      application never sets, so they cannot catch this class of defect.
- [ ] [BACKEND] P1. **Audit the strategy-service endpoint auth posture.** The same ground-truth pass reported 49
      of 74 strategy-service endpoints as unauthenticated. That figure has not been independently verified and
      should be, since it may include internal-only routers where it is correct.
