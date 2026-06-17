---
title: "Service Dockerfiles are inconsistent + fragile — normalize the 9 Pattern-B services to the clean base-image form (Pattern A)"
created: 2026-06-17
author: harshkantariya [slot-3·laptop]
status: active
priority: P2
locked_by: live-defi-rollout
parent_epic: deployment_and_user_management_master
source:
  - 2026-06-17 fleet image-build validation (plans/active/test_fleet_image_builds_from_current_code_2026_06_17.md) — local amd64 sweep of all 15 Python service images surfaced two divergent Dockerfile build contracts
---

# Service Dockerfiles inconsistent — normalize Pattern B → Pattern A

> **For Ikenna** — surfaced while test-building every service image locally from current code. Not blocking anything live
> (the bespoke builds DO work on GCP via per-service cloudbuild staging) — it's a reproducibility/maintainability +
> image-size cleanup. A fleet Dockerfile normalization decision.

## What I found

A local `docker build` of all 15 cloned Python service images (current code, amd64, against the current UTL base digest)
split cleanly into **two build contracts**:

- **Pattern A — clean base-image (6 services):** `FROM unified-trading-library@<digest>` + `COPY . .` +
  `uv pip install --system --no-deps -e .`. Self-contained; all shared deps come from the base image. **Builds from a
  single-repo context with zero extra staging.** Repos: `instruments-service`, `client-reporting-api`,
  `deployment-service`, `features-service`, `market-tick-data-service`, `agent-orchestrator`. Image size **~3 GB**.

- **Pattern B — vendored-sibling (9 services):** also `FROM` the base, but then **re-vendors sibling repo SOURCES into the
  build context** (`COPY unified-api-contracts/ unified-trading-library/ …`) and runs `uv sync --frozen` against local
  path sources. Requires a **multi-repo build context** that cloudbuild assembles via a per-service `stage-siblings` step.
  And the staging is **per-service-bespoke**:
  - `alerting`, `execution`, `greeks` — vendor exactly **UAC + UTL** (build locally once those 2 are staged). ✅ proved.
  - `strategy` — vendors a **third** sibling: `COPY market-tick-data-service/`.
  - `batch-live-reconciliation` — `COPY configs/cloud-providers.yaml` (a file **not in the repo** — cloudbuild stages it
    from deployment-service/UAC).
  - `fund-administration`, `market-data-processing`, `ml`, `trading-agent` — `uv.lock` pins UAC at the **absolute path
    `file:///unified-api-contracts`** (filesystem root), so `uv sync --frozen` fails unless the sibling is at exactly
    `/unified-api-contracts`. Build-machine-absolute lock paths.
  Image size **~5.5–7 GB** (≈2× Pattern A, because the sibling sources are re-vendored + re-synced on top of a base that
  already contains them).

**Local-build result:** 9/15 build cleanly here (6 Pattern-A + alerting/execution/greeks); the other 6 each need their own
bespoke context replicated and were left GCP-authoritative.

## Why it matters

- **Fragility / reproducibility:** every Pattern-B service has its own implicit context contract (which siblings, which
  configs, which absolute lock paths). It only builds where that exact staging is reproduced (cloudbuild + the AWS
  buildspec) — local builds and any new CI path break until each service's staging is hand-replicated.
- **Image bloat:** Pattern-B images are ~2× the size for no benefit (the base already contains UTL+UAC; re-vendoring +
  `uv sync` just duplicates them). Bigger images = slower pulls, more registry storage, larger attack surface.
- **Maintenance tax:** the `uv.lock` absolute path pins (`file:///unified-api-contracts`) are especially brittle — they
  encode a build-machine filesystem layout into the lock.
- **Not a live outage** — they build + deploy today via GCP. This is debt, hence **P2**, not P0/P1.

## Recommended decision

**Normalize all 9 Pattern-B services to Pattern A** — `FROM base@digest` + `COPY . .` + `uv pip install --no-deps -e .`,
dropping the sibling `COPY`s, the `uv sync --frozen` against path sources, and the per-service `stage-siblings` cloudbuild
steps. The base image already carries UTL+UAC, so the service only needs its own code installed `--no-deps`. Pattern A is
proven (6 services) and yields self-contained, single-context, ~3 GB builds that work identically local/GCP/AWS.

Open questions for the owner:
- Any Pattern-B service that genuinely needs a sibling NOT in the base (e.g. strategy ↔ market-tick-data-service)? If a
  service imports another *service's* code, that's a separate tier violation to resolve (services integrate by contract,
  not import) — flag, don't paper over with vendoring.
- Sequencing: normalize one canary (e.g. `alerting`) end-to-end (Dockerfile + cloudbuild `stage-siblings` removal + green
  GCP build), then fan out.

## Follow-up todos
- [ ] [DESIGN] P2. Decide + own the Pattern-A normalization (this doc). Owner: Ikenna.
- [ ] [INFRA] P2. Canary-normalize `alerting-service` Dockerfile + cloudbuild to Pattern A; confirm green GCP build + ~3GB image. **Repo:** alerting-service.
- [ ] [INFRA] P2. Fan out the normalization to the remaining 8 Pattern-B services. **Repos:** execution, greeks, strategy, batch-live-reconciliation, fund-administration, market-data-processing, ml, trading-agent.
- [ ] [BUG] P3. Investigate `strategy-service` vendoring `market-tick-data-service/` — confirm it's not a service↔service import (tier violation). **Repo:** strategy-service.

## Composes with
- Parent validation: `plans/active/test_fleet_image_builds_from_current_code_2026_06_17.md` (findings log).
- Tier/import architecture (no service↔service imports): `codex/04-architecture/tier-and-import-architecture.md`.
- Canonical service cloudbuild template + STEP 5.22: `unified-trading-pm/scripts/...` / service `cloudbuild.yaml`.
