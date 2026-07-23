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
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer]
tags: [mock-parity, deployment-api, validation, ui, dx]
related:
  [
    /plans/active/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineering
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

- [ ] [SERVICE] P2. **Fix `/api/data-status/coverage-summary` mock to match the live contract** — populate
      `asset_groups` and rename `totals.dates_across_asset_groups` → `dates_across_categories`, plus
      `capture_status_counts` / `completion_pct` / `unique_instruments`. Highest-value: this is the endpoint the Data
      Status UI work of 2026-07-16 sits on.
- [ ] [SERVICE] P2. **Diagnose `ImportError: artifactregistry_v1`** driving the `/api/builds/history` +
      `/api/fixtures/upcoming` 500s — venv-only, or a real missing dependency that reaches Cloud Run?
- [ ] [SERVICE] P3. **Bring `/api/repo-ci/overview` mock up to the staging-dormant contract** (`promotion_model`,
      `staging_dormant_mode`, `image_gcp`/`image_aws`, `image.deploy_host`/`deploy_model`).
- [ ] [SERVICE] P3. **Reconcile the `/api/deployments` pagination contract** — live `has_more`+`total_count` vs mock
      `total`. Pick one; the UI reads whichever it was written against.
- [ ] [SERVICE] P3. **Refresh the frozen mock fixtures** (cloud-builds 2026-03-29 · fleet-git-health/gh-rate-limit
      2026-06-10 · inventory 2026-06-22 · escalations 2026-06-27) — a fixture that never moves silently trains the UI on
      stale shapes.
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
