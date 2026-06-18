---
title:
  "Cloud Build operational findings (2026-06-18 smoke test) — mdps Docker break + deployment-ui Cloud Build visibility
  gaps"
created: 2026-06-18
source:
  - "2026-06-18 operator-directed Cloud Build smoke test: verify permissions, run base + service builds, check
    deployment-ui visibility, retry a failing service (at most 4 builds)"
  - "GCP central-element-323112, region asia-northeast1 — builds 590050dc (UTL base), 4a7de34e (mtds), 40c74eab (mdps);
    prior mdps failure baf77da9"
locked_by: live-defi-rollout
parent_epic: infrastructure_master
priority: P2
status: active
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
- Three builds triggered successfully and ran to terminal: `590050dc` (UTL base, `-live-defi-rollout`) → **SUCCESS**,
  `4a7de34e` (mtds, `-live-defi-rollout`) → **SUCCESS**, `40c74eab` (mdps, `-build`@main) → **FAILURE** (Finding 1).

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

### Finding 3 — deployment-api build history returns EMPTY for all builds (P2, deeper than a mapping bug)

`GET /api/cloud-builds/history/market-tick-data-service` → `{"builds":[],"total":0}` AND
`GET /api/cloud-builds/history/market-data-processing-service` → `{"builds":[],"total":0}` — **both empty**, even though
mtds builds green continuously and mdps's `market-data-processing-service-build` trigger (the exact one the endpoint
maps to) has builds today (incl. my failure `40c74eab` + `baf77da9`). So the empty result is NOT merely the trigger
mapping. **Primary root cause** (`cloud_builds.py:386-391`): `get_build_history` queries
`ListBuildsRequest(project_id=...)` — **GLOBAL scope** (a code comment notes the regional parent "fails with 400 on REST
transport") — but every build runs **regionally in `asia-northeast1`** (the triggers are regional), and a global
`list_builds` does not return regional builds → always empty. **Secondary**: even with the scope fixed, the
`service → <service>-build` hard-map (`cloud_builds.py:346`) still misses repos whose live builds run on the
`-live-defi-rollout` trigger (UTL, mtds, UAC, UCI, internal-contracts). Route: `cloud_builds.py:313 get_build_history`.

## Why it matters

- **Finding 1** blocks every mdps image (the CeFi/TradFi candle-processing service — a data-pipeline component); `main`
  can't produce a deployable image. Data-pipeline correctness is the heartbeat.
- **Findings 2 + 3** make the deployment-ui Cloud Build pane non-functional: the triggers list 500s, and build history
  returns empty for EVERY repo (regional builds are invisible to the global query). Operators can't see any build status
  — confirmed empty for both an LDR-built repo (mtds) and a main-built repo (mdps).

## Recommended decision

- **F1**: change `market-data-processing-service/Dockerfile:57` from `uv sync --frozen --no-dev` to the proven mtds
  pattern `uv pip install --system -e . --no-deps`, **plus** explicit installs of any mdps-specific external deps not in
  the UTL base (numba etc.) — OR add a `stage-siblings` step to the cloudbuild and `COPY` the siblings to `/app/`.
  Validate via a `market-data-processing-service-feature-build` run AND a
  `docker run … python -c "import market_data_processing_service"` (a green build alone will NOT catch a `--no-deps`
  runtime break such as missing numba).
- **F2**: diagnose the 500 in `list_triggers` (cloud_builds.py:99) — likely the GCP triggers API call or the
  AWS-triggers merge raising; the deployment-ui triggers pane depends on it.
- **F3**: query `list_builds` with the REGIONAL parent `projects/{p}/locations/asia-northeast1` (use the gRPC transport,
  which doesn't hit the REST 400 the code comment cites) instead of global `project_id` scope — that is the primary fix
  for the always-empty history. Secondarily, map each service to its ACTUAL live trigger (`-live-defi-rollout` where
  present, else `-build`) so LDR-built repos appear too (cloud_builds.py:313/346/386).

## Todos

- [ ] [DOCKER] P1. Fix market-data-processing-service Docker build sibling-resolution break — switch `Dockerfile:57`
      `uv sync --frozen --no-dev` → mtds pattern `uv pip install --system -e . --no-deps` (+ explicit mdps-only external
      deps), or stage siblings into the build context. Validate via `market-data-processing-service-feature-build` +
      `docker run` import check before promoting to main. Repo: market-data-processing-service.
- [ ] [SCRIPT] P2. Fix deployment-api `GET /api/cloud-builds/triggers` 500 (cloud_builds.py:99 `list_triggers`). Repo:
      deployment-api.
- [ ] [SCRIPT] P2. Fix deployment-api build-history always-empty — query `list_builds` with the regional parent
      `projects/{p}/locations/asia-northeast1` (gRPC transport) not global `project_id` scope (cloud_builds.py:386), AND
      map each service to its real live trigger so `-live-defi-rollout` repos appear (cloud_builds.py:346). Empirically
      both mtds (`-live-defi-rollout`) and mdps (`-build`) return empty today. Repo: deployment-api.

## Composes with

- Service Dockerfile pattern: `market-tick-data-service` is the green GCP reference (base-image +
  `uv pip install -e . --no-deps`); the `uv sync --frozen` Docker pattern needs siblings staged in-context.
- `codex/08-workflows/ci-cd-flow.md` (build/promotion pipeline) · deployment-ui Cloud Build pane.
