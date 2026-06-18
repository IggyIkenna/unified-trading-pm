---
title:
  "Cloud Build operational findings (2026-06-18 smoke test) — mdps Docker break + deployment-ui Cloud Build visibility
  gaps"
created: 2026-06-18
author: harshkantariya [slot-3·laptop]
source:
  - "2026-06-18 operator-directed Cloud Build smoke test: verify permissions, run base + service builds, check
    deployment-ui visibility, retry a failing service (at most 4 builds)"
  - "GCP central-element-323112, region asia-northeast1 — builds 590050dc (UTL base), 4a7de34e (mtds), 40c74eab (mdps);
    prior mdps failure baf77da9"
locked_by: live-defi-rollout
parent_epic: infrastructure_master
---

# Cloud Build operational findings (2026-06-18 smoke test)

> Operator (Harsh) 2026-06-18: ran an operational smoke test of GCP Cloud Build — confirmed `roles/editor` can trigger
> builds, manually ran the UTL base image + `market-tick-data-service` (both via their `-live-defi-rollout` triggers),
> and retried the failing `market-data-processing-service-build`. Three findings below.

## What I found

**Smoke-test result (capability):** ✅ Cloud Build is fully usable from this account.

- Permission: `harshkantariya@odum-research.com` has `roles/editor` on `central-element-323112` →
  `cloudbuild.builds.create`.
- Mechanism: builds run via **regional Cloud Build triggers in `asia-northeast1`** (NOT global —
  `gcloud builds triggers list` defaults to global and shows nothing). ~60 triggers exist: `<repo>-live-defi-rollout`
  (continuous on LDR), `<repo>-feature-build`, `<repo>-build` (main), `<repo>-main-deploy`. Run one with
  `gcloud builds triggers run <name> --region=asia-northeast1 --branch=<branch>` (builds from GitHub source — no local
  tarball; auto-populates `$SHORT_SHA`).
- Three builds triggered successfully and ran: `590050dc` (UTL base, `-live-defi-rollout`), `4a7de34e` (mtds,
  `-live-defi-rollout`), `40c74eab` (mdps, `-build`@main).

### Finding 1 — market-data-processing-service Docker build is broken on `main` (P1, build-blocking)

`market-data-processing-service-build` (branch `main`) has failed repeatedly (2026-06-18 04:01 + 07:22, build
`baf77da9`; reproduced 2026-06-18 as build `40c74eab`). Root cause at Docker `Step 10/18`:

```
RUN uv sync --frozen --no-dev
error: Failed to determine installation plan
  Caused by: Distribution not found at: file:///app/unified-api-contracts
```

- `market-data-processing-service/Dockerfile:57` runs `uv sync --frozen --no-dev`. `uv sync` reads `uv.lock`, which pins
  `unified-api-contracts` as `{ editable = "../unified-api-contracts" }` (resolves to `/app/unified-api-contracts` under
  `WORKDIR /app/market-data-processing-service`).
- That sibling is NOT in the build context: the Dockerfile only does `COPY . .` (the service repo), and
  `market-data-processing-service/cloudbuild.yaml` has **no `stage-siblings` step** (unlike the canonical service
  template, which clones UAC+UTL into the context).
- **Working reference = `market-tick-data-service`** (builds green continuously): its `Dockerfile:62` uses
  `RUN uv pip install --system -e . --no-deps` — installs only the service against the base image's already-installed
  UTL+UAC, never resolving the editable sibling path. (`uv pip install` ignores `[tool.uv.sources]`; `uv sync` honors it
  — that is the whole difference.)
- The mdps Dockerfile comment claims it "mirrors alerting-service working pattern" — but that pattern works on **AWS
  CodeBuild** because the AWS `buildspec` `pre_build` stages the siblings; the **GCP** cloudbuild does not replicate
  that staging.

### Finding 2 — deployment-api `/api/cloud-builds/triggers` returns 500 (P2)

`GET https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app/api/cloud-builds/triggers` → `Internal Server Error`.
This is the endpoint deployment-ui calls to list build triggers; a 500 means the deployment-ui triggers list is broken.
Route: `deployment-api/deployment_api/routes/cloud_builds.py:99 list_triggers` (merges GCP + AWS triggers).

### Finding 3 — deployment-api build history misses `-live-defi-rollout` builds (P2)

`GET /api/cloud-builds/history/market-tick-data-service` →
`{"trigger_name":"market-tick-data-service-build","builds":[],"total":0}` — but mtds is actively building (green) via
the **`market-tick-data-service-live-defi-rollout`** trigger, not `-build`. The history endpoint hard-maps `service` →
`<service>-build`, so for every repo whose live builds run on the `-live-defi-rollout` trigger (UTL, mtds, UAC, UCI,
internal-contracts) the deployment-ui shows "no builds" despite continuous green builds. Route:
`cloud_builds.py:313 get_build_history`.

## Why it matters

- **Finding 1** blocks every mdps image (the CeFi/TradFi candle-processing service — a data-pipeline component); `main`
  can't produce a deployable image. Data-pipeline correctness is the heartbeat.
- **Findings 2 + 3** make the deployment-ui Cloud Build pane misleading: the triggers list 500s, and the most active
  repos read as "no builds." Operators can't trust the build-status surface.

## Recommended decision

- **F1**: change `market-data-processing-service/Dockerfile:57` from `uv sync --frozen --no-dev` to the proven mtds
  pattern `uv pip install --system -e . --no-deps`, **plus** explicit installs of any mdps-specific external deps not in
  the UTL base (numba etc.) — OR add a `stage-siblings` step to the cloudbuild and `COPY` the siblings to `/app/`.
  Validate via a `market-data-processing-service-feature-build` run AND a
  `docker run … python -c "import market_data_processing_service"` (a green build alone will NOT catch a `--no-deps`
  runtime break such as missing numba).
- **F2**: diagnose the 500 in `list_triggers` (cloud_builds.py:99) — likely the GCP triggers API call or the
  AWS-triggers merge raising; the deployment-ui triggers pane depends on it.
- **F3**: map each service to its ACTUAL live trigger (`-live-defi-rollout` where present, else `-build`), or query
  builds by repo/branch rather than a fixed `<service>-build` trigger name (cloud_builds.py:313).

## Todos

- [ ] [DOCKER] P1. Fix market-data-processing-service Docker build sibling-resolution break — switch `Dockerfile:57`
      `uv sync --frozen --no-dev` → mtds pattern `uv pip install --system -e . --no-deps` (+ explicit mdps-only external
      deps), or stage siblings into the build context. Validate via `market-data-processing-service-feature-build` +
      `docker run` import check before promoting to main. Repo: market-data-processing-service.
- [ ] [SCRIPT] P2. Fix deployment-api `GET /api/cloud-builds/triggers` 500 (cloud_builds.py:99 `list_triggers`). Repo:
      deployment-api.
- [ ] [SCRIPT] P2. Fix deployment-api build-history trigger mapping so `-live-defi-rollout` builds appear
      (cloud_builds.py:313 `get_build_history` hard-maps `<service>-build`). Repo: deployment-api.

## Composes with

- Service Dockerfile pattern: `market-tick-data-service` is the green GCP reference (base-image +
  `uv pip install -e . --no-deps`); the `uv sync --frozen` Docker pattern needs siblings staged in-context.
- `codex/08-workflows/ci-cd-flow.md` (build/promotion pipeline) · deployment-ui Cloud Build pane.
