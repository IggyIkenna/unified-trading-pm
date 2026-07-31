---
doc_type: codex-ssot
title: Dockerfile Standards
summary:
  Docker image standards — Python services MUST FROM the shared Artifact Registry unified-trading-library base (uv/rg/
  gcloud/gcsfuse pre-installed; the heavier unified-trading-services base only when justified), UI repos use multi-stage
  node+nginx; plus layer-caching order, non-root appuser, HEALTHCHECK, approved-registry-only, and no-secrets-in-image
  rules.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [dockerfile, infrastructure, ci-cd, quality-gates, ui]
related: [/codex/06-coding-standards/dependency-management.md, /codex/06-coding-standards/quality-gates.md]
created: 2026-03-27
authoritative_for: [Dockerfile base-image and build standards]
referenced_by: [/codex/06-coding-standards/dependency-management.md]
owner:
last_reviewed:
code_refs:
---

# Dockerfile Standards

SSOT for all Docker image patterns in the unified trading system.

## Base Images

### Python Services (ALL service and API repos)

**ALWAYS use the shared Artifact Registry base image.** Never use `python:3.13-slim` or any public Python image directly
— the shared base has `uv`, `ripgrep`, `curl`, `ca-certificates`, `gcsfuse`, and the Google Cloud SDK pre-installed.

```dockerfile
ARG PROJECT_ID
FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest

WORKDIR /app

COPY pyproject.toml .
COPY <package_dir>/ ./<package_dir>/

RUN uv pip install --system --no-cache-dir -e .

ENTRYPOINT ["python", "-m", "<package_dir>"]
```

For services that need dev deps (test/lint in container):

```dockerfile
RUN uv pip install --system --no-cache-dir -e ".[dev]"
```

**Do NOT:**

- `RUN pip install uv` — uv is pre-installed in the base
- `RUN apt-get install ripgrep curl` — already in the base
- `COPY --from=deps /unified-*-interface ...` — shared libs are pre-installed in the base
- `FROM python:3.13-slim` — redundant, loses all shared layers
- `FROM ghcr.io/astral-sh/uv:...` — unofficial; use the approved Artifact Registry base

### UI Repos (React/TypeScript)

No shared Node.js base image exists. Use multi-stage builds with public Node + nginx:

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Runtime (no Node.js — just static assets)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Key points:**

- `npm ci` (not `npm install`) — deterministic from lock file
- Drop Node.js in runtime stage — lean nginx image only
- Quality gates (typecheck, lint, vitest) run in `cloudbuild.yaml` BEFORE docker build, not inside the image

### Heavy Trading Services

Some services (execution, instruments, market-tick-data,
market-tick-data-service/market_tick_data_service/market_interface) use the heavier `unified-trading-services:latest`
base which includes additional C extensions and trading-specific system deps:

```dockerfile
ARG PROJECT_ID
FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-services/unified-trading-services:latest
```

Use this base only if your service has a documented need for the additional deps. Default to
`unified-trading-library:latest` otherwise.

## Layer Caching Best Practices

1. **Copy `pyproject.toml` before source code** — dep layer only rebuilds when deps change, not on every code change
2. **`--no-cache-dir` on `uv pip install`** — avoids wasted space from pip wheel cache in the image
3. **`--platform=linux/amd64`** — explicit platform for reproducible multi-platform builds
4. **Shared base image** — all services share the base layers; Docker content-addressable storage deduplicates on disk
   and in memory

## CI/CD Caching

### Cloud Build (Google)

Cloud Build automatically caches Artifact Registry layers between builds. To get **explicit** layer cache reuse (faster
cold starts):

```yaml
steps:
  # Pull previous image to warm layer cache
  - name: "gcr.io/cloud-builders/docker"
    id: "pull-cache"
    entrypoint: "bash"
    args: ["-c", "docker pull asia-northeast1-docker.pkg.dev/$PROJECT_ID/<repo>/<service>:latest || true"]

  # Build with cache-from
  - name: "gcr.io/cloud-builders/docker"
    id: "build"
    args:
      - build
      - --cache-from
      - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/<repo>/<service>:latest"
      - -t
      - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/<repo>/<service>:latest"
      - .
    waitFor: ["pull-cache"]
```

### GitHub Actions

Use `docker/build-push-action@v5` with registry cache:

```yaml
- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: asia-northeast1-docker.pkg.dev/${{ env.PROJECT_ID }}/<repo>/<service>:latest
    cache-from: type=registry,ref=asia-northeast1-docker.pkg.dev/${{ env.PROJECT_ID }}/<repo>/<service>:cache
    cache-to: type=registry,ref=asia-northeast1-docker.pkg.dev/${{ env.PROJECT_ID }}/<repo>/<service>:cache,mode=max
    build-args: PROJECT_ID=${{ env.PROJECT_ID }}
```

For Python QG steps (not Docker), use uv lock-file keyed cache:

```yaml
- uses: actions/cache@v4
  with:
    path: |
      .venv
      ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
    restore-keys: uv-${{ runner.os }}-
```

## Private Library Support

The shared base image works seamlessly with private Artifact Registry Python packages because:

1. The base image has the `pip.conf` / `uv` Artifact Registry keyring pre-configured
2. `uv pip install -e .` resolves service-specific deps from `pyproject.toml`
3. Private packages (`unified-*`) are pre-installed in the base layer
4. Service-specific deps are installed in the service's own layer — no coupling

Each service owns its own `pyproject.toml` dependencies. The base image provides the shared foundation.

## uv pip install Retry Wrapper (BuildKit-secret GAR auth)

**Canonical convention (established 2026-07-30,
`plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`)** — every production
Dockerfile whose editable install resolves `unified-trading-library`/`unified-api-contracts` from the LIVE Artifact
Registry index (i.e. carries a `RUN --mount=type=secret,id=gar_token` layer, as opposed to a vendored-local-path
install) MUST wrap that `uv pip install ... --no-sources` call in a 3-attempt retry loop with exponential backoff, to
absorb the transient publish-ordering race between a downstream repo's floor-bump landing and the upstream wheel fully
propagating through the registry:

```dockerfile
RUN --mount=type=secret,id=gar_token \
    UV_EXTRA_INDEX_URL="https://oauth2accesstoken:$(cat /run/secrets/gar_token)@asia-northeast1-python.pkg.dev/central-element-323112/unified-libraries/simple/" \
    sh -c 'i=1; until uv pip install --system --no-sources -e .; do [ "$i" -ge 3 ] && { echo "uv pip install failed after 3 attempts" >&2; exit 1; }; w=$((15 * i)); echo "uv pip install failed (attempt $i/3) -- retrying in ${w}s"; sleep "$w"; i=$((i + 1)); done'
```

Applied identically (verbatim, modulo each service's own install flags/extras) across 8 repos as of 2026-07-30:
`strategy-service`, `ml-service`, `market-data-processing-service`, `instruments-service`, `trading-agent-service`,
`greeks-service`, `alerting-service`, `fund-administration-service`. **Not applicable** to `market-tick-data-service`
(installs UTL/UAC from vendored local `.deps/` paths, never resolves from the live GAR index at build time) or
`unified-trading-system-ui` (no Cloud Build trigger).

**Not yet automated** — unlike the `BASE_IMAGE_DIGEST` pin (§ Layer Caching,
`scripts/propagation/ add-dockerfile-digest-arg.py` + `scripts/quality_gates/check_base_image_digest_drift.py` + STEP
5.79), there is currently no propagation script or fleet drift-checker enforcing this pattern — it was hand-applied per
repo. A new repo, or a future edit to one of the 8 above, can silently drop the retry wrapper with nothing to catch it.
Building that automation (mirroring the digest-pin precedent) is tracked as its own follow-up todo rather than folded
into the doc-only pass that added this section — see the issue doc above.

## Security

- **Never bake secrets into images** — use `get_secret_client()` at runtime
- **Non-root user** — add `appuser` for production services:
  ```dockerfile
  RUN useradd --create-home --uid 1000 --shell /bin/bash appuser
  USER appuser
  ```
- **HEALTHCHECK** — all production services must include a health check:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
  ```
- Approved registry: `asia-northeast1-docker.pkg.dev` only (no Docker Hub in production)

## New Service Checklist

- [ ] `FROM ... unified-trading-library:latest` (or `unified-trading-services:latest` if justified)
- [ ] `ARG PROJECT_ID` before `FROM`
- [ ] `--platform=linux/amd64`
- [ ] `COPY pyproject.toml` before `COPY <source>/`
- [ ] `uv pip install --system --no-cache-dir -e .`
- [ ] Non-root `appuser`
- [ ] `HEALTHCHECK`
- [ ] No secrets in image
