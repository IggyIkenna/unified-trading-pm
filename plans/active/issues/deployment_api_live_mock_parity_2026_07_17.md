---
doc_type: issue
title:
  deployment-api mock mode has drifted from live (12 endpoints incl. an EMPTY coverage-summary) + two live-only 5xx from
  a missing artifactregistry dep
summary: |
  Operator asked (2026-07-16) whether deployment-ui could be developed against mock mode — i.e. "are live and mock the
  same shape and equally current?". Measured by diffing all 111 parameterless GET endpoints between a live and a mock
  deployment-api: **NO**. 54 endpoints match; **12 have a drifted contract** — worst is
  `/api/data-status/coverage-summary`, where mock returns an EMPTY `asset_groups` and the pre-rename field
  `dates_across_asset_groups`, so any UI built against it is built against a contract live does not have. Six more are
  frozen-in-time fixtures (cloud-builds stuck at 2026-03-29). Separately, live mode itself has two 5xx
  (`/api/builds/history`, `/api/fixtures/upcoming`) from `ImportError: artifactregistry_v1`, and `/api/vm-deployments`
  exceeds 90s. The comparison tool is promoted to `deployment-api/scripts/compare_live_mock_parity.py` — **re-run it;
  parity decays every time an endpoint is added to one side only**.
status: open
nature: issue
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; deployment-api/deployment-ui
  # mock-vs-live contract parity, core ui-tranche scope
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer]
tags: [mock-parity, deployment-api, validation, ui, dx]
related:
  [
    /plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
resolved_by:
locked_by:
drift_direction: advance-code
source:
  [
    deployment-api/scripts/compare_live_mock_parity.py,
    deployment-api/deployment_api/services/data_status/rollup_cache.py,
    deployment-api/deployment_api/routes/health_overview.py#L131,
  ]
depends_on: []
context_scope:
  [
    deployment-api/scripts/compare_live_mock_parity.py,
    deployment-api/deployment_api/services/data_status/rollup_cache.py,
    /plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md,
    /codex/05-infrastructure/deployment-observability.md,
    deployment-api/Dockerfile,
    deployment-api/deployment_api/routes/_gcp_cloud_functions.py,
  ]
---

# deployment-api mock mode has drifted from live

## How this was measured

`deployment-api/scripts/compare_live_mock_parity.py` (promoted from this session's scratchpad — **it must survive
because its answer has a date on it**). It diffs the KEY SHAPE (not values — mock values are meant to differ) and the
newest date in each payload, across every parameterless GET in the OpenAPI spec.

```bash
# live on 8005, mock on 8006 — mock mode is per-process, so it is two servers
GCP_PROJECT_ID=<proj> DISABLE_AUTH=true ENVIRONMENT=development .venv/bin/python -m uvicorn deployment_api.main:app --port 8005
CLOUD_MOCK_MODE=true GCP_PROJECT_ID=<proj> DISABLE_AUTH=true ENVIRONMENT=development .venv/bin/python -m uvicorn deployment_api.main:app --port 8006
.venv/bin/python scripts/compare_live_mock_parity.py --serial
```

**Result 2026-07-16: 111 endpoints compared — 54 same shape, 12 drifted, 7 status-mismatch, 38 needed params / both
non-200.** The tool's header documents the traps (rate-limiting fakes gaps; `python -m deployment_api` ignores `$PORT`;
422-on-both is not a finding; `{param}` paths are unmeasured).

## The drift that actually matters

| Endpoint                                                                                                                                                                                | Drift                                                                                                                                                                                                                                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/api/data-status/coverage-summary`                                                                                                                                                     | **Worst.** Mock returns `asset_groups: {}` (EMPTY) + the old field `totals.dates_across_asset_groups`; live returns populated CEFI/DEFI/PREDICTION/SPORTS/TRADFI + `dates_across_categories`, `capture_status_counts`, `completion_pct`, `unique_instruments`. A UI built on the mock is built on a contract live does not have. |
| `/api/repo-ci/overview`                                                                                                                                                                 | Mock lacks `promotion_model`, `staging_dormant_mode`, `image_gcp`/`image_aws`, `image.deploy_host`/`deploy_model` — exactly the fields added by the 2026-07-16 staging-dormant work.                                                                                                                                             |
| `/api/deployments`                                                                                                                                                                      | Pagination contract differs: live `has_more` + `total_count`; mock `total`.                                                                                                                                                                                                                                                      |
| `/api/alerts`, `/api/repo-ci/alerts`                                                                                                                                                    | Mock lacks `deployment_target`.                                                                                                                                                                                                                                                                                                  |
| `/api/services`, `/api/cloud-builds/triggers`, `/api/deployments/inventory`, `/api/repos/deploy-ready`, `/sports/venues`, `/api/instruments/*`, `/api/data-status/prediction-catalogue` | Smaller key gaps (several are only a harmless `"mock": true` marker — check before "fixing").                                                                                                                                                                                                                                    |

**Frozen fixtures (mock behind live):** cloud-builds `2026-03-29` · fleet-git-health + gh-rate-limit `2026-06-10` ·
deployments/inventory `2026-06-22` · repo-ci/escalations `2026-06-27`.

**Good news:** the endpoints shipped 2026-07-16 (`new-listings`, `upcoming-expiries`, `prediction-catalogue`) have full
mock parity — the drift is historical, not systemic.

## Live-only defects (mock cannot show you these)

- `/api/builds/history` + `/api/fixtures/upcoming` → **500**. Root cause in the slot-2 venv:
  `ImportError: cannot import name 'artifactregistry_v1' from 'google.cloud'`. Confirm whether it is a missing dep in
  the venv only, or a genuine unpinned/absent dependency that also hits Cloud Run.
- `/api/vm-deployments` → **>90s / timeout**. The route's own docstring admits "measured avg 93.75s / max 99.27s in
  prod"; it is SWR-cached, so only the cold path bites — but the cold path exceeds a 90s client timeout.

## Todos

- [x] ✅ [SERVICE] P2. **Fix `/api/data-status/coverage-summary` mock to match the live contract** — populate
      `asset_groups` and rename `totals.dates_across_asset_groups` → `dates_across_categories`, plus
      `capture_status_counts` / `completion_pct` / `unique_instruments`. Highest-value: this is the endpoint the Data
      Status UI work of 2026-07-16 sits on. — **DONE 2026-07-30 (slot 5), `deployment-api@d7546e6`.** An earlier
      "Cherry-pick D" commit (2026-07-20, `349946a`) had already populated `asset_groups` + renamed the field to
      `dates_across_categories` for CEFI/DEFI/SPORTS/TRADFI, and `capture_status_counts`/`completion_pct` were already
      present per-venue in `_mock_venue_entry` — but the default (instruments-service, unrestricted) live path iterates
      all 5 `MarketCategory` values while `_MOCK_COVERAGE_SEED` only carried 4, leaving a live-only key gap on
      `asset_groups.PREDICTION`. Added the missing PREDICTION seed entry (mirrors `build_mock_turbo_response`'s existing
      PREDICTION seed shape: event-driven, high-attempt/low-capture). `unique_instruments` already present at the
      per-response level. Regression test updated; full `quality-gates.sh` green, `quickmerge --agent` landed clean.
- [x] ✅ [SERVICE] P2. **Diagnose `ImportError: artifactregistry_v1`** driving the `/api/builds/history` +
      `/api/fixtures/upcoming` 500s — venv-only, or a real missing dependency that reaches Cloud Run? — **DONE
      2026-07-30 (slot 8), `deployment-api@c064574`.** Genuine, reaches Cloud Run — NOT venv-only.
      `google-cloud-artifact-registry` is a correctly-declared dependency of `deployment-service`
      (`deployment-service/pyproject.toml`), and `deployment-api`'s own routes (`routes/builds.py`,
      `routes/builds_history.py`) import `artifactregistry_v1` directly at call time. But `deployment-api`'s
      `Dockerfile` installs the vendored `deployment-service` sibling with `uv pip install --system --no-deps` (comment:
      avoids resolving `[tool.uv.sources]` sibling-repo paths that don't exist in the Cloud Build context) and its own
      hand-maintained explicit dependency list (the `uv pip install --system` block) already carries
      `google-cloud-run`/`google-cloud-compute` for exactly this reason but was missing `google-cloud-artifact-registry`
      — so the production/Cloud Run image never installs it, while a normal dev `.venv` (`uv sync`, full dependency
      resolution) has it and never reproduces the bug locally. Verified by reproducing the exact install sequence in an
      isolated Python 3.13 venv: `uv pip install --no-deps <deployment-service checkout>` alone →
      `ModuleNotFoundError: No module named     'google'`; adding `google-cloud-artifact-registry>=1.13.0,<2.0.0` (the
      pin added below) → import succeeds. Fix: added `'google-cloud-artifact-registry>=1.13.0,<2.0.0'` to the
      Dockerfile's explicit `uv pip install` list (next to `google-cloud-run`/`google-cloud-compute`). **Adjacent
      finding, not folded into this fix** (different failure mode — degrades honestly, doesn't 500):
      `deployment_api/routes/_gcp_cloud_functions.py` (wired into the live `/api/deployments/inventory` route) has the
      identical gap for `google-cloud-functions` (also a `deployment-service` dep, missing from the same Dockerfile
      list) — its `functions_v2.FunctionServiceClient()` call is `try/except`-wrapped so it silently returns `{}`
      instead of 500ing, meaning the Cloud Functions census has likely been silently empty in production rather than
      crashing. Tracked as a new P3 todo below. `google-cloud-scheduler` (deployment-service's third GCP dep missing
      from the list) was checked and is NOT actually imported anywhere in `deployment_api` — no fix needed there.
- [x] ✅ [SERVICE] P3. **Add `google-cloud-functions>=1.16.0,<2.0.0` to the `deployment-api` Dockerfile's explicit
      `uv pip install` list** (same list `google-cloud-artifact-registry` was just added to) — closes the silent
      `{}`-degradation gap in `deployment_api/routes/_gcp_cloud_functions.py`'s `list_cloud_functions()` (wired into
      `/api/deployments/inventory`), which has been silently returning an empty Cloud Functions census in the Cloud Run
      image since deployment-service is vendored `--no-deps` there too. (repo: deployment-api) — **DONE 2026-08-02
      (slot-13, backend_engineer), `deployment-api@d1d2a21`.** Added the pin next to `google-cloud-artifact-registry` in
      the Dockerfile's explicit `uv pip install` block; version constraint matches `deployment-service/pyproject.toml`'s
      own declared `google-cloud-functions>=1.16.0,<2.0.0`. `quality-gates.sh` green, shipped via `quickmerge --agent`,
      verified on origin.
- [x] ✅ [SERVICE] P3. **Bring `/api/repo-ci/overview` mock up to the staging-dormant contract** (`promotion_model`,
      `staging_dormant_mode`, `image_gcp`/`image_aws`, `image.deploy_host`/`deploy_model`). — **DONE 2026-08-03 (slot-7,
      backend_engineer), `deployment-api@dc7eece`.** `_mock_row()` now sets `promotion_model="ldr_main"` +
      `staging_dormant_mode=True` on every row (matches the current fleet manifest — every repo but `unified-trading-pm`
      itself is already `ldr_main`, fleet toggle is on) and adds `image_gcp`/`image_aws` (mirroring `image`, since every
      fixture repo is a standalone deploy); `_mock_image()` now also sets `deploy_model=None`/`deploy_host=None`
      (correct for these 7 repos — none are in `_SOURCE_DEPLOYED`/ `_BUNDLED_IN`). Added
      `test_overview_staging_dormant_contract_fields` + extended `test_overview_shape`'s key-set assertion to pin the
      contract. Full `quality-gates.sh` green (sentinel `dc7eece`), shipped via `quickmerge --agent`, verified on
      origin.
- [x] ✅ [SERVICE] P3. **Reconcile the `/api/deployments` pagination contract** — live `has_more`+`total_count` vs mock
      `total`. Pick one; the UI reads whichever it was written against. — **DONE 2026-08-03 (slot-7, backend_engineer),
      `deployment-api@e1e100e`.** Investigated both the backend consumer surface and the frontend: no live code path
      anywhere in the workspace reads `has_more`/`total_count`/`total` off this endpoint — deployment-ui's only consumer
      (`DeploymentHistory.tsx` via `client.ts`'s `getDeployments()`) destructures only `.deployments`, so consumption
      was a wash. Standardized the mock branch (`deployment_api/routes/deployments/_crud.py`) on live's shape
      (`deployment_state.py:62-68`) since (a) every prior fix in this doc brought mock into line with live, never the
      reverse, and (b) `total_count`+`has_more` is the pagination convention already used by every other paginated
      endpoint in this service (`catalogue_lifecycle.py`, `_repo_ci_alerts.py`, `data_status/_catalogue.py`,
      `data_status_drilldown/_instruments.py`). Updated `tests/unit/test_route_deployments_mock.py`'s two pagination
      assertions to match. `quality-gates.sh` green (sentinel `e1e100e`), shipped via `quickmerge --agent`, verified on
      origin. Adjacent finding filed as a new todo below (deployment-ui's own frontend mock still returns `total`).
- [ ] [UI] P3. **Update deployment-ui's own dev-mode/Playwright mock** (`deployment-ui/src/lib/mock-api.ts:4528-4534`,
      the `VITE_MOCK_API`-gated frontend fixture, distinct from deployment-api's backend `CLOUD_MOCK_MODE`) to emit
      `total_count`+`has_more` for `/api/deployments`, matching the backend contract fixed by the todo above. No live
      consumer reads either field today, so this is stale-fixture hygiene, not a functional bug — but leaving it
      diverged means deployment-ui's dev/Playwright surface no longer matches deployment-api's real (both live and
      now-fixed-mock) response shape. (repo: deployment-ui)
- [x] ✅ [SERVICE] P3. **Refresh the frozen mock fixtures** (cloud-builds 2026-03-29 · fleet-git-health/gh-rate-limit
      2026-06-10 · inventory 2026-06-22 · escalations 2026-06-27) — a fixture that never moves silently trains the UI on
      stale shapes. — **DONE 2026-08-03 (slot-6, backend_engineer), `deployment-api@c0aabe0`.** Rather than a one-time
      date bump (which would just re-freeze on the next measurement), each fixture now COMPUTES its timestamps relative
      to `datetime.now(UTC)`: `cloud_builds.py`'s mock trigger `last_build`, `repo_gh_rate_limit.py`'s
      `_mock_rate_limit` (`fetched_at` + all three `reset` epochs), `_repo_ci_mocks.py`'s `_mock_alerts()` (the
      `git_health` alert powering `/api/alerts`'s fleet-git-health signal) and `_mock_escalations()`, and
      `deployments_inventory/_mock_data.py`'s `_mock_inventory()` (which already took a `now: datetime` PARAMETER from
      its caller but never used it — a latent dead-parameter bug; now wired through). Every fixture's original relative
      spacing between events is preserved, just re-anchored to the present. `quality-gates.sh` green (sentinel
      `c0aabe0`), shipped via `quickmerge --agent`, verified on origin.
- [ ] [SERVICE] P3. **Decide whether parity should be a gate, not a script** — if `compare_live_mock_parity.py` were
      wired into a QG/contract test, none of the above could have rotted for four months. That is the durable fix; the
      script is the stopgap. (Cross-ref: deployment-ui@0c817d2 fixed the same rot class on the FRONTEND mock the same
      week — two mocks, same disease.)

## Lessons

- **"Is mock safe to develop against?" is not answerable from the code — measure it.** The intuition was "mock is fine";
  the measurement found an empty `asset_groups` on the single most-used data endpoint.
- **The live rate-limiter fakes parity gaps.** First run reported 5 false "live=429 mock=200 status mismatch" findings.
  Any comparison tool hitting live concurrently MUST treat 429 as "not measured" and re-measure serially.
- **`python -m deployment_api` ignores `$PORT`** (hardcodes 8004; `PORT` is not wired into `UnifiedCloudConfig`). Use
  `uvicorn ... --port` or the second instance silently collides with the first.

## Progress Log

- **slot-8 2026-07-30**: Fixed the `artifactregistry_v1` ImportError — `deployment-api@c064574`. Root cause:
  `deployment-api`'s `Dockerfile` vendors `deployment-service` with `uv pip install --system --no-deps` and its own
  hand-maintained explicit `uv pip install` package list never carried `google-cloud-artifact-registry` (unlike
  `google-cloud-run`/`google-cloud-compute`, added there for the identical reason). Verified genuine (not venv-only) by
  reproducing the exact install sequence in an isolated Python 3.13 venv: `--no-deps` install of `deployment-service`
  alone → `ModuleNotFoundError: No module named 'google'` on `from google.cloud import artifactregistry_v1`; adding the
  pin fixes it. Filed a new P3 todo for the adjacent `google-cloud-functions` gap (same pattern, silently degrades
  instead of 500ing — not folded into this fix). Full `quality-gates.sh` green (sentinel `c064574`), shipped via
  `quickmerge --agent`.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **slot-13 2026-08-02**: Added `google-cloud-functions>=1.16.0,<2.0.0` to the Dockerfile's explicit `uv pip install`
  list — `deployment-api@d1d2a21`, `quality-gates.sh` green, shipped via `quickmerge --agent`, verified on origin.
- **slot-7 2026-08-03**: Closed the `/api/repo-ci/overview` mock's staging-dormant contract gap —
  `deployment-api@dc7eece`. `_mock_row()`/`_mock_image()` now unconditionally set `promotion_model`,
  `staging_dormant_mode`, `image_gcp`/`image_aws`, and `image.deploy_model`/`deploy_host` on every row, mirroring what
  `_overview_row()`/`_image_signal()` always set live. Values chosen to match the actual current fleet manifest
  (`promotion_model="ldr_main"` + `staging_dormant_mode=True` fleet-wide; `deploy_model`/`deploy_host=None` since none
  of the 7 fixture repos are source-deployed or bundled). Added a regression test pinning the new keys.
  `quality-gates.sh` green (sentinel `dc7eece`), shipped via `quickmerge --agent`, verified on origin.
- **slot-7 2026-08-03**: Reconciled the `/api/deployments` pagination contract — `deployment-api@e1e100e`. Explored both
  consumer surfaces (deployment-api's own callers + deployment-ui) before picking a side: nothing reads
  `has_more`/`total_count`/`total` off this endpoint anywhere in the workspace today (deployment-ui's sole consumer,
  `DeploymentHistory.tsx`, only destructures `.deployments`), so the choice came down to precedent + convention rather
  than a forced UI dependency. Standardized the mock branch on live's `total_count`+`has_more` shape (matches
  `deployment_state.py` and every other paginated endpoint in this service) rather than the reverse, consistent with
  every prior fix in this doc. Updated the two affected pagination assertions in
  `tests/unit/test_route_deployments_mock.py`. `quality-gates.sh` green (sentinel `e1e100e`), shipped via
  `quickmerge --agent`, verified on origin. Filed a new `[UI]` P3 todo for the adjacent finding: deployment-ui's own
  frontend dev-mode/Playwright mock (`src/lib/mock-api.ts:4528-4534`, gated by `VITE_MOCK_API` — a separate mechanism
  from deployment-api's `CLOUD_MOCK_MODE`) still returns `total`; out of scope for this backend_engineer task (UI/TS
  work), left for a `ui_developer` pickup.
- **slot-6 2026-08-03**: Refreshed the four frozen mock fixtures — `deployment-api@c0aabe0`. Checked first whether any
  unit test pinned the exact frozen date literals (`grep` across `tests/unit/`) — none did, so free to change values.
  Chose relative-to-now computation over a one-time date bump specifically because a bump just re-freezes at the next
  measurement, which is the exact rot this todo exists to stop. Found `_mock_inventory(now: datetime)` already had a
  `now` parameter threaded in from every real caller (`_load_inventory`) that the function body simply never used —
  fixed that latent gap rather than adding a parallel `datetime.now()` call. Verified all four fixtures produce current,
  non-frozen output via direct import + a full local `quality-gates.sh` pass (targeted tests +
  `test_repo_ci_routes.py`/`test_repo_ci_alerts.py`/`test_route_deployments_inventory*.py`/`test_route_builds.py`, 505
  passed). `quality-gates.sh` green (sentinel `c0aabe0`), shipped via `quickmerge --agent`, verified on origin.
