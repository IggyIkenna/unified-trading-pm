---
title: "Test fleet image builds from current code — local (amd64) → GCP → AWS, base-first, no-deploy"
created: 2026-06-17
status: active
priority: P2
locked_by: live-defi-rollout
parent_epic: deployment_and_user_management_master
assigned_vm: vm-operator-ops
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
source:
  - 2026-06-17 operator (Harsh) — proactively validate that every repo's container image builds from current code BEFORE prod-readiness, so we surface + fix build breakage now instead of under prod pressure
  - 2026-06-17 Ikenna context — UI repos auto-build+deploy (rapid-dev, low harm); the rest are cost-gated behind quickmerge --build; the dashboard "unknown" image state is a SEPARATE (IAM) issue
  - 2026-06-17 diagnosis (harsh-slot-3) — full build-pipeline trace (base→service FROM-digest chain, test-in-image, GCP/AWS dual build paths, tarball-vs-image distinction)
---

# Test fleet image builds from current code (2026-06-17)

> **Goal:** prove that **every deployable repo's container image builds successfully from current code**, surface and
> fix whatever breaks (stale base-digest pins, missing deps, broken Dockerfiles, in-image AR auth, test-in-image
> failures), so that when we ARE ready to ship prod code we are not doing trial-and-error under pressure. **This is a
> build-validation exercise, NOT a deploy.** Deploy is the final, separate phase (1–2 images only, to confirm they run).

## Scope + non-goals

**In scope:** building container images for the deployable repos (base libraries + Cloud-Run service images) from their
**current working-tree code** — first **locally** on an amd64 machine (free, fast feedback), then on **GCP Cloud Build**
(authoritative, test-in-image), then validating the **AWS CodeBuild** path.

**Explicit non-goals (this exercise):**
- **No production deploy** of new images except a deliberate 1–2 image trial in the final phase.
- **We do NOT require `main == LDR`** — the point is to test the *build mechanism* on current code, not to ship current
  code. Build whatever branch the trigger/working-tree carries (libs→LDR, services→main or working tree locally).
- **Not** the tarball path — code tarballs (ephemeral VM backfill/orchestrator) are a separate, already-working artifact
  (see § "Build pipeline reference"); untouched here.
- **Not** the dashboard "unknown image" fix — that is a read-only IAM gap tracked separately in
  `plans/active/issues/deployment_dashboard_image_status_and_multicloud_toggle_2026_06_17.md` (Ikenna to grant
  `cloudbuild.builds.viewer` + `artifactregistry.reader` on `unified-trading-sa`). **Not a blocker for this plan** —
  building images uses the build SA (`github-actions-deploy`), which already has the perms.

## Key decisions (locked 2026-06-17)

1. **Order: local (amd64) → GCP → AWS.** Local `docker build` on an x86_64 Ubuntu desktop matches the `linux/amd64`
   target (no emulation), is free, and gives fast feedback → catches most "does it build" breakage before any GCP spend.
   GCP is the authoritative build (test-in-image, real substitutions, pushes to AR). AWS CodeBuild validated last.
   **Rationale (operator):** GCP builds cost money + slower feedback; fix locally first.
2. **Base-first, then dependents.** Service images are `FROM unified-trading-library@<digest>` with `--no-deps`, so a
   service built on a stale base bakes stale shared code. Rebuild base libs (UTL → UAC → interfaces) before services.
3. **Build directly via the trigger / `docker build` — NOT via `quickmerge --build`.** For this *test* we invoke builds
   on demand (`gcloud builds triggers run` on GCP; `docker build` locally) so there is no commit, no trailer, and full
   cost control (one repo at a time). `quickmerge --build` (the `Build-LDR: true` trailer → AWS CodeBuild webhook) is the
   normal cost-gated production path, not the test mechanism.
4. **Cost-aware, incremental.** A full fleet sweep is ~20 GCP Cloud Builds; run one repo at a time, watch, and STOP to
   diagnose if early repos surface a systemic issue rather than fanning out. Local builds are free → exhaust local first.
5. **No deploy until the final phase.** Building + pushing an image to Artifact Registry does NOT roll out a running
   service (`notify-deployment` only writes `stable_versions.yaml`). The trial deploy of 1–2 images is Phase 4.

## Build pipeline reference (grounded in source 2026-06-17)

**Two build paths (multi-cloud):**
- **GCP Cloud Build — auto-fires on push** (triggers all `live` except `deployment-api-build` = DISABLED):
  - base libs/interfaces on `^live-defi-rollout$`: `unified-trading-library`, `unified-api-contracts`,
    `unified-cloud-interface`, `unified-internal-contracts` (→ rebuild the base image + publish the wheel).
  - services + most interfaces on `^main$`: `instruments-service-build`, `execution-service-build`,
    `strategy-service-build`, `features-*-build`, `ml-*-build`, `market-*-build`, `unified-*-interface-build`, etc.
- **AWS CodeBuild — opt-in, cost-gated**: `quickmerge --build` stamps a `Build-LDR: true` commit trailer; the AWS
  CodeBuild webhook's COMMIT_MESSAGE filter fires the LDR image build only when present (`quickmerge.sh:1434`).
- **Auto-build-on-quickmerge** (manifest flag, default `--build` ON + auto-deploy): exactly **`deployment-api`,
  `deployment-ui`, `unified-trading-api`, `unified-trading-system-ui`** (the rapid-dev UI surfaces).

**Base image (UTL `cloudbuild.yaml`, on LDR):** AR auth → clone UAC (editable) → clone PM QG scripts → quality-gates
(tests) → build wheel + publish to AR python index → `docker build` base image tagged `:{VERSION}` + `:latest` → push
`--all-tags`. So UTL publishes **both** a wheel and the Docker base image; the base bakes UTL + UAC + all heavy shared
deps.

**Service image (`instruments-service/Dockerfile`):** `ARG BASE_IMAGE_DIGEST=sha256:…` →
`FROM …/unified-trading-library@${BASE_IMAGE_DIGEST}` → install uv + `keyrings.google-artifactregistry-auth` →
`COPY . .` → `uv pip install --system --no-deps -e .` (service layer only; relies on the base for all deps). The pinned
digest is the **FROM-digest ratchet**; cloudbuild can override `--build-arg BASE_IMAGE_DIGEST=`.

**Service cloudbuild (canonical template, on main):** auth-precheck → build → **quality-gates = test-in-image** (re-runs
`quality-gates.sh` INSIDE the built image) → push (only if QG passes) → notify-deployment (writes `stable_versions.yaml`;
does NOT roll out).

**Tarball vs image (why both exist):** `create-code-tarballs.sh` packages raw repo **source** (excludes `.git`/`.venv`/
caches) to `gs://{bucket}/code/{repo}-code.tar.gz` (+ SHA-pinned copy + manifest; AWS `s3://…` too). Ephemeral VMs
`gsutil cp` + `tar xzf` + build a venv + `uv pip install` **at boot**. Tarball = source only, deps resolved per-VM at
setup (fast to change, slower/less-reproducible boot) → used for **batch/backfill VMs + orchestrator**. Docker image =
fully-built + pinned + test-in-image (fast cached pull) → used for **Cloud Run services**. This plan touches only the
Docker-image path.

## Findings so far (2026-06-17)

- **Local readiness GREEN:** Docker 29.5.3 + buildx 0.34.1; arch x86_64 (amd64, matches target); Artifact Registry
  docker auth configured; the operator account can READ the base image (`describe` → digest).
- **Base-digest staleness is LIVE:** current base `:latest` = `sha256:a1b0cf83…`, but `instruments-service/Dockerfile`
  pins `BASE_IMAGE_DIGEST=sha256:c54f13d9…` (stale). Confirms the digest-pin gotcha — to build against current base,
  override `--build-arg BASE_IMAGE_DIGEST=<current>`. **Open question for the fleet:** how many service Dockerfiles carry
  stale pins (the dependency-update fan-out is supposed to refresh them).
- **First local build IN FLIGHT:** instruments-service (canary) against current base digest — result pending (task
  blrha5r7b). Will record exit + first breakage class below.

## Phases (DAG)

### Phase 0 — Local build harness + setup (this machine, free)
- [x] [INFRA] P0. Confirm local readiness (Docker/buildx, amd64, AR auth, base-image read) — DONE 2026-06-17.
- [x] [INFRA] P0. First canary local build: `instruments-service` against current base digest — **SUCCESS** (3.07GB
  image `sha256:f3b6c7f0…`, installed `instruments-service==0.10.0`, exit 0). `--no-deps` service install needs NO extra
  in-image AR auth (base carries deps). 2 cosmetic Dockerfile lint warnings only (empty default `BASE_IMAGE` arg;
  `--platform` constant). **Repo:** instruments-service.
- [ ] [SCRIPT] P1. Document the canonical local-build invocation (PROJECT_ID + BASE_IMAGE_DIGEST args, `--platform
  linux/amd64`) + the in-image AR-auth handling (does the `--no-deps` service install need ADC mounted? resolve once on
  the canary). Capture as a short runnable snippet IN THIS PLAN (no separate summary doc).
- [ ] [INFRA] P1. Decide base-image local strategy: services can pull the existing base from AR (no local base build
  needed); the base libs (UTL) build locally only if we want to test the base Dockerfile itself (heavier — needs UAC
  source + PM QG scripts). Record whether Phase 1 base libs are validated locally or GCP-only.

### Phase 1 — Base libraries (local → GCP), base-first
Order: `unified-cloud-interface` → `unified-api-contracts` → `unified-internal-contracts` → `unified-trading-library`.
- [ ] [INFRA] P1. Local build each base lib (where a Dockerfile/image exists); fix breakage; log findings. **Repos:** the 4 above.
- [ ] [INFRA] P1. GCP build each via `gcloud builds triggers run <repo>-live-defi-rollout --branch live-defi-rollout
  --region asia-northeast1`; watch to SUCCESS; confirm image/digest lands in AR. One at a time.
- [ ] [INFRA] P1. After UTL rebuilds: record the NEW base digest → it becomes the `--build-arg BASE_IMAGE_DIGEST` for
  Phase 2 service builds (build services against the fresh base).

### Phase 2 — Service images (local → GCP), against fresh base
Candidate canaries first (the cloudbuild template names them): `execution-service`, `instruments-service`,
`alerting-service`. Then the rest: `strategy-service`, `market-tick-data-service`, `market-data-processing-service`,
`features-*`, `ml-*`, `client-reporting-api`, `fund-administration-service`, `batch-live-reconciliation-service`,
`greeks-service`, `trading-agent-service`, `deployment-service`.
- [ ] [INFRA] P1. Local build each service against the fresh base digest; fix breakage; log findings. One at a time.
- [ ] [INFRA] P2. GCP build each via `gcloud builds triggers run <repo>-build --branch main --region asia-northeast1`
  (note: builds main HEAD — fine, we're testing the mechanism, not shipping). Watch to SUCCESS; confirm AR push. STOP +
  diagnose on the first systemic failure class before continuing.
- [ ] [BUG] P2. For every stale base-digest pin found, file the fix (refresh `BASE_IMAGE_DIGEST` ARG) in the owning
  repo — but only AFTER confirming the dependency-update fan-out isn't the intended owner; coordinate, don't fork it.

### Phase 3 — AWS CodeBuild path validation (after GCP green)
- [ ] [INFRA] P3. Validate the AWS CodeBuild build path for ≥1 base lib + ≥1 service (the `Build-LDR: true` trailer
  webhook, or the direct AWS CodeBuild project run). Confirm parity with GCP (same image builds). **Needs:** AWS
  CodeBuild read/run perms — `harsh-worker` currently lacks `codebuild:ListProjects` (file a `BLOCKED-CREDENTIALS` ask if
  it blocks).

### Phase 4 — Trial deploy (FINAL, separate gate)
- [ ] [INFRA] P3. Deploy 1–2 freshly-built images to confirm they actually run (low-risk repo first, e.g. a UI or a leaf
  service). Verify the running service is healthy. This is the ONLY deploy in this plan.

## Success criteria + continuous verification

| Phase | Cutover criterion | Continuous verification | Last verified |
| --- | --- | --- | --- |
| 0 | Local harness builds the canary green (or its failure is understood + logged) | re-run the canary local build | — |
| 1 | All base libs build (local + GCP); fresh base digest recorded | `gcloud builds list` SUCCESS per lib + AR digest | — |
| 2 | All service images build (local + GCP) against fresh base; stale pins triaged | `gcloud builds list` SUCCESS per service | — |
| 3 | ≥1 lib + ≥1 service build on AWS CodeBuild | AWS CodeBuild build SUCCESS | — |
| 4 | 1–2 trial images deploy + run healthy | service health endpoint 200 | — |

## Findings log
_(append each build failure + fix here as we go — this IS the plan's progress log; no separate summary doc.)_

- 2026-06-17: plan created.
- 2026-06-17: **canary local build PASS** — `instruments-service` built locally (amd64) against current base digest
  `a1b0cf83…` → 3.07GB image, exit 0. Confirms: (a) local amd64 build harness works; (b) `--no-deps` service layer needs
  no extra in-image AR auth; (c) building against an overridden (current) base digest works. Dockerfile has 2 cosmetic
  lint warnings (empty default `BASE_IMAGE` arg resolution; `FROM --platform` constant) — candidate P3 cleanup, not blocking.

## Composes with / SSOTs
- IAM/unknown-image (separate): `plans/active/issues/deployment_dashboard_image_status_and_multicloud_toggle_2026_06_17.md`
- Build pipeline: service `cloudbuild.yaml` canonical template (STEP 5.22 canary services); UTL `cloudbuild.yaml`;
  FROM-digest ratchet (CLAUDE.md § Dependencies+builds); `quickmerge.sh` `--build` (Gap 5).
- Tarball path: `deployment-service/scripts/vm/create-code-tarballs.sh`; `codex/05-infrastructure/vm-tarball-deployment.md`.
- VM/image deploy topology: `codex/04-architecture/runtime-deployment-topology.md`.
