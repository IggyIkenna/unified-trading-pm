---
title: VM image build caching gaps — deployment-service, execution-service, strategy-service
created: 2026-05-15
author: slot-2
source:
  - codex audit item 12 (VM image build caching audit)
locked_by: ""
---

## What I found

Three Cloud Build + Dockerfile caching gaps identified across deployment-service, execution-service, and strategy-service. All three repos build on every CI push without leveraging Docker layer cache, adding 3–8 minutes of unnecessary build time per commit.

### Gap 1 — Missing `--cache-from` in Cloud Build docker build steps (all 3 repos, P1)

**Impact**: Every Cloud Build run rebuilds all Docker layers from scratch even when nothing changed except a config comment. Cloud Build does NOT share Docker layer cache between runs by default.

**Fix**: Add `--cache-from` pointing to the `:latest` tag already in Artifact Registry before each `docker build` call.

```yaml
# Before (all 3 repos):
- name: "gcr.io/cloud-builders/docker"
  id: "build"
  args:
    - "build"
    - "--build-arg"
    - "PROJECT_ID=${PROJECT_ID}"
    ...

# After:
- name: "gcr.io/cloud-builders/docker"
  id: "build"
  args:
    - "build"
    - "--cache-from"
    - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REGISTRY_REPO}/${_SERVICE_NAME}:latest"
    - "--build-arg"
    - "PROJECT_ID=${PROJECT_ID}"
    ...
```

**Risk**: Zero — `--cache-from` is purely advisory. If no cache hit, build proceeds as today.

**Repos**: deployment-service `cloudbuild.yaml` (3 build steps: build, build-dev, build-sports-scheduler), execution-service `cloudbuild.yaml` (1 build step), strategy-service `cloudbuild.yaml` (1 build step).

---

### Gap 2 — `COPY . /app/service` before `uv sync` in execution-service + strategy-service Dockerfiles (P1)

**Impact**: Any source file change (even a docstring edit) invalidates the `uv sync --frozen --no-dev --system` Docker layer and forces a full dependency reinstall (~2–4 minutes). This affects every developer pushing a code change.

**Root cause**: both Dockerfiles copy the entire source tree before installing dependencies:

```dockerfile
# execution-service/Dockerfile (current — WRONG ORDER):
COPY . /app/execution-services      # invalidates dep cache on any source change
WORKDIR /app/execution-services
RUN uv sync --frozen --no-dev --system   # reinstalls ALL deps even if pyproject.toml unchanged

# strategy-service/Dockerfile (current — WRONG ORDER):
COPY . /app/strategy-service
WORKDIR /app/strategy-service
RUN uv sync --frozen --no-dev --system
```

**Fix** (canonical dep-layer-before-source pattern):

```dockerfile
# Both services — correct order:
WORKDIR /app/service-name
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --system    # only re-runs when deps change
COPY . .                                  # source changes stay in a later layer
```

**Note**: deployment-service Dockerfile already uses the correct pattern (`COPY pyproject.toml uv.lock README.md ./` before `RUN uv pip install`). Gap is only in execution-service and strategy-service.

**Risk**: Low — this is a pure layer reordering with identical end state. The installed dependencies are the same; only the cache invalidation boundary changes. Requires testing that the build completes correctly after reorder.

---

### Gap 3 — execution-service `pull-base-image` step pulls wrong image (P1)

**Impact**: Cloud Build's `pull-base-image` step pulls `unified-trading-library:latest` but the execution-service Dockerfile uses `unified-trading-services:latest` as the base image. The pre-pull step (intended to warm Docker auth + cache) has no effect on the actual build.

```yaml
# execution-service/cloudbuild.yaml (current — WRONG IMAGE):
- name: "gcr.io/cloud-builders/docker"
  id: "pull-base-image"
  args: ["pull", "asia-northeast1-docker.pkg.dev/$PROJECT_ID/unified-trading-library/unified-trading-library:latest"]

# execution-service/Dockerfile (actual base image used):
FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-services/unified-trading-services:latest AS base
```

**Fix**: Change `pull-base-image` in execution-service `cloudbuild.yaml` to pull `unified-trading-services:latest` instead of `unified-trading-library:latest`.

**Risk**: Zero — changing the pull step to pull the correct image has no build semantics difference. It either works (cache warm) or fails (image not found — would surface a real bug).

---

### Gap 4 — deployment-service uses `E2_HIGHCPU_32` (4× expensive, P2)

**Impact**: deployment-service Cloud Build uses `E2_HIGHCPU_32` while the standard for all other services is `E2_HIGHCPU_8`. At ~$0.22/min vs ~$0.06/min, a 10-minute build costs $2.20 vs $0.60. For ~5 deploys/day, this adds ~$8/day vs ~$2.25/day.

**Context**: The `E2_HIGHCPU_32` may be intentional because deployment-service runs 3 parallel docker build stages (build, build-dev, build-sports-scheduler) and the 32 vCPUs speed parallel layer construction. The QG step also runs docker inside docker. But the savings vs E2_HIGHCPU_8 have not been measured.

**Recommendation**: Measure one build on `E2_HIGHCPU_8` to see wall-clock impact before deciding to downgrade. Not urgent pre-May-23 but worth tracking.

---

## Why it matters

- Every source-code push to these 3 repos triggers a full Docker rebuild (3–8 min of wasted build time, ~$0.60–$2.20 per build depending on machine type).
- For the May-23 cutover window where CI becomes the production gate, this is ~50 extra builds/day × 5 min = ~4 extra GPU-hours of compute per day.
- Gaps 1–3 are safe to fix immediately (no semantic change, no test risk).

## Recommended decision

| Gap | Action | Owner | Urgency |
|-----|--------|-------|---------|
| Gap 1 (`--cache-from` all 3) | Fix: add `--cache-from` to all 3 `cloudbuild.yaml` | slot-2 or slot-8 | Pre-May-23 (P1) |
| Gap 2 (layer order exec+strategy) | Fix: reorder COPY in Dockerfiles + smoke build | slot owning exec/strategy CI | Pre-May-23 (P1) |
| Gap 3 (exec base image mismatch) | Fix: 1-line change in exec `cloudbuild.yaml` | slot-2 or slot-8 | Pre-May-23 (P1) |
| Gap 4 (deploy E2_HIGHCPU_32) | Investigate: measure wall-clock on E2_HIGHCPU_8 | slot-2 or slot-8 | P2 post-May-23 |

**deployment-service `--cache-from` fix**: safe to ship immediately — no semantic change to the build.
**execution-service + strategy-service Dockerfile reorder**: requires a test build to confirm the re-ordered image starts and passes QG before merging.
