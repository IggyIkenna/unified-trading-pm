---
doc_type: issue
title:
  deployment-api has several call sites passing a GCP project_id POSITIONALLY into UTL's
  get_secret_client()/get_storage_client() — landing in the `provider` parameter instead, which
  raises ValueError("Unsupported cloud provider") on every real (non-mocked) invocation
summary: |
  Found while wiring `deployment-api/deployment_api/routes/sports_venues.py`'s live-mode sports
  venue-credentials endpoint to real Secret Manager probing (nick_ai_platform_readiness_remediation_2026_08_16.md
  W4 sports mock-config half). `unified_trading_library.core.client_factory.get_secret_client()` and
  `get_storage_client()` both declare `provider` as their FIRST positional parameter, `project_id`
  second (`unified-trading-library/unified_trading_library/core/client_factory.py:44,84` — same order
  in `unified_trading_library/cloud_interface/factory.py:125,172`). Both resolve provider via
  `p = (provider_override or provider or _detect_secrets_provider()).lower()` (secrets) /
  `p = provider or get_cloud_provider()` (storage) — when a caller passes a project_id string as the
  sole positional arg, `provider` becomes that project_id string, `_detect_*()`/`get_cloud_provider()`
  auto-detection is skipped entirely (the `or` short-circuits on a truthy value), and neither
  `"gcp"`/`"aws"`/`"local"` matches → `else: raise ValueError(f"Unsupported cloud provider: {p!r}")`.
  This is silent only until a real (non-empty) project_id reaches a live/non-mocked code path; every
  test found for the affected files fully mocks the factory function itself (`MagicMock`/lambda
  return-value patches), so the bug produces green tests while being live-broken.

  Fixed the one instance directly adjacent to this task's own file family
  (`deployment_api/routes/venue_credentials.py:87`, the sibling "venue-credentials" pattern the sports
  task was told to mirror — zero test file exists for that route, zero regression risk) and used the
  correct `project_id=` keyword form in the new sports code. Did NOT fix the remaining instances below —
  they are unrelated files/domains outside the sports task's scope, deserve their own review of blast
  radius (is `infra_health.py`'s check even the one actually used, given `health_routes.py` has a
  separately-tested `_check_secret_manager`?), and one of them (`infra_health.py`) is a Layer-2
  post-deploy/CI-CD gate — a broken health-gate is a "big finding" per CLAUDE.md's findings-triage rule,
  not a silent ad-hoc fix bundled into an unrelated PR.

  **Remaining call sites (unverified beyond static read — confirm live-broken behavior before fixing,
  per CLAIM≤MEASUREMENT):**
  - `deployment_api/routes/infra_health.py:68` — `get_storage_client(project_id)` (GCS state-bucket
    check, `GET /infra/health`)
  - `deployment_api/routes/infra_health.py:98` — `get_secret_client(project_id)` (Secret Manager
    check, same endpoint) — if both are live-broken, `GET /infra/health`'s real-mode branch ALWAYS
    reports `gcs_state_bucket` and `secret_manager` as `"error"`/overall `"degraded"`, defeating its
    stated purpose ("Run after Terraform apply, before Layer 3 smoke tests")
  - `deployment_api/routes/repo_coverage.py:76` — `get_storage_client(project_id)`
  - `deployment_api/routes/repo_readiness.py:118` — `get_storage_client(project_id)`

  **Confirmed NOT affected** (different function, correct signature): `deployment_api/utils/
  deployment_state_reader.py:92,135` call `deployment_api.utils.storage_client.get_storage_client`
  (a local wrapper with `project_id` as ITS OWN first positional param, which internally calls the UTL
  function with the correct `project_id=` keyword) — not the UTL function directly, not the bug.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [deployment-api]
scope: [engineer]
tags: [deployment-api, get_secret_client, get_storage_client, positional-argument-bug, infra-health, client-factory]
related:
  [
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-16
priority: P2
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Adjacent finding while executing the mock-config half of nick_ai_platform_readiness_remediation_2026_08_16.md's
  W4 Sports todo (wiring deployment-api/routes/sports_venues.py to real Secret Manager probing, which required
  calling unified_trading_library.get_secret_client correctly and revealed the sibling venue_credentials.py file
  already had this exact bug).
drift_direction: advance-code
context_scope:
  [
    unified-trading-library/unified_trading_library/core/client_factory.py,
    unified-trading-library/unified_trading_library/cloud_interface/factory.py,
    deployment-api/deployment_api/routes/infra_health.py,
    deployment-api/deployment_api/routes/repo_coverage.py,
    deployment-api/deployment_api/routes/repo_readiness.py,
  ]
---

# deployment-api: positional `project_id` misread as `provider` in `get_secret_client`/`get_storage_client`

## What to do

> **Converted from a numbered prose list to tracked checkboxes 2026-08-18 (plan_reconciler cross-cutting)** —
> `assigned_vm: planning` with zero real checkboxes was structurally undispatchable (backlog regen is
> checkbox-driven); content unchanged.

- [ ] [CODE] P2. For each of the 3 remaining call sites above, confirm live-broken behavior first (don't assume —
      e.g. instantiate the real UTL function with a real non-empty project_id string and observe the `ValueError`,
      or trace whether `infra_health.py`'s `GET /infra/health` is even reachable/used vs. `health_routes.py`'s
      separately-implemented, separately-tested `_check_secret_manager`/equivalent GCS check — if the latter is what's
      actually wired into production health checks, `infra_health.py` may be effectively dead code and this is lower
      priority than it looks).
- [ ] [CODE] P2. Fix confirmed-live instances with the `project_id=project_id` keyword form (one-line changes,
      mirroring the fix already applied to `venue_credentials.py:87`).
- [ ] [TEST] P3. Since none of the affected files currently have a test covering the real-mode Secret
      Manager/storage-client branch (only `infra_health.py` has any real-mode test coverage, and it fully mocks the
      factory calls — meaning it would NOT have caught this bug and will NOT catch a regression either), add one
      assertion per fixed call site that the factory is invoked with `project_id=` as a keyword (e.g.
      `mock.assert_called_with(project_id=...)`) rather than a bare positional, so this exact bug class can't
      silently reappear.
- [ ] [SCRIPT] P3. `quality-gates.sh --no-fix` green, quickmerge.

## Progress Log

**2026-08-16 — filed.** Discovered while wiring `sports_venues.py`'s live-mode endpoint to real Secret
Manager probing for `nick_ai_platform_readiness_remediation_2026_08_16.md` W4 (sports mock-config
half). Fixed the one instance directly in that task's own file family
(`venue_credentials.py:87`) since it was zero-risk (no test file existed for it) and directly
informed correct usage in the new sports code. Traced the remaining 3 call sites
(`infra_health.py:68,98`, `repo_coverage.py:76`, `repo_readiness.py:118`) via a repo-wide grep for
both `get_secret_client(` and `get_storage_client(` and reading each call site's surrounding import
(confirming which import UNIFIED_TRADING_LIBRARY vs. a local wrapper) but did not fix them — out of
scope for the sports task, and `infra_health.py` in particular is a CI/CD-adjacent health gate whose
blast radius deserves its own look rather than an ad-hoc bundled fix. Ruled out
`deployment_state_reader.py:92,135` as a false positive — it calls a local wrapper
(`deployment_api/utils/storage_client.py::get_storage_client`) with the correct signature, not the
buggy UTL function.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:db39fdd68dc008ad]: RECLASSIFY (whole-doc) -- assigned_vm flipped NA -> planning; execution_scope -> orchestrator-agent; assigned_role: backend_engineer (was unset). Both open items are bounded/mechanical (confirm-then-fix, one-line project_id= keyword changes mirroring an already-applied fix), conflict-check CLEAR. doc_type: issue, structurally exempt from a finalize-plan companion per task_template.md's finalize-plan-coverage rule. Cross-cutting tranche audit.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
