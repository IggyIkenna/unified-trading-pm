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
- [x] [INFRA] P1. Local-build the cloned base libs — **DONE**: `unified-api-contracts` wheel PASS (`0.19.0`);
  `unified-trading-library` base image PASS (`.deps/UAC` recipe, `sha256:7b614fec…`, import OK). `unified-cloud-interface`
  + `unified-internal-contracts` NOT cloned → GCP-direct (below).
- [ ] [INFRA] P1. GCP build each via `gcloud builds triggers run <repo>-live-defi-rollout --branch live-defi-rollout
  --region asia-northeast1`; watch to SUCCESS; confirm image/digest lands in AR. One at a time.
- [ ] [INFRA] P1. After UTL rebuilds: record the NEW base digest → it becomes the `--build-arg BASE_IMAGE_DIGEST` for
  Phase 2 service builds (build services against the fresh base).

### Phase 2 — Service images (local → GCP), against fresh base
Candidate canaries first (the cloudbuild template names them): `execution-service`, `instruments-service`,
`alerting-service`. Then the rest: `strategy-service`, `market-tick-data-service`, `market-data-processing-service`,
`features-*`, `ml-*`, `client-reporting-api`, `fund-administration-service`, `batch-live-reconciliation-service`,
`greeks-service`, `trading-agent-service`, `deployment-service`.
- [x] [INFRA] P1. Local-build the services — **DONE: 9/15 build locally** (6 Pattern-A standalone +
  alerting/execution/greeks with a 2-sibling context). The other 6 (strategy, batch-live-reconciliation, fund-administration,
  market-data-processing, ml, trading-agent) are **Pattern-B-bespoke** → left GCP-authoritative; normalization filed in
  `plans/active/issues/service_dockerfile_pattern_normalization_2026_06_17.md`. See findings log for the full matrix.
- [ ] [INFRA] P2. **🔴 BLOCKED-CREDENTIALS (2026-06-18) — GCP build via `gcloud builds triggers run <repo>-build --branch
  main` / `<repo>-live-defi-rollout --branch live-defi-rollout` (region asia-northeast1), watched to SUCCESS, one at a
  time, STOP + diagnose on first systemic failure.** **Manual trigger-run is permission-blocked**: both `harshkantariya`
  and the `github-actions-deploy` SA hold only `roles/cloudbuild.builds.viewer` (read — can WATCH builds, cannot RUN
  them), and the deploy SA isn't impersonable. GSM reuse can't avoid it (the only stored SA key —
  `github-actions-sa-key`/`github-actions-deploy` — is `cloudbuild.builds.viewer`, not editor). **➡️ Full cross-cloud
  permission audit + grant commands (operator parity): `plans/active/issues/operator_iam_permission_parity_2026_06_18.md`**
  (GCP: `roles/editor` + `projectIamAdmin` + `serviceAccountTokenCreator`; AWS: `PowerUserAccess`). Until granted, the only
  no-perm path is the natural **main-push auto-fire** (services build on main push, base libs on LDR push) — but most
  service repos are already `main==LDR` (0-file delta → no build), so it only fires for the ~4 with pending content;
  `deployment-api`/`deployment-ui` GCP-build this way from the P1/P2 promotions.
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
- 2026-06-17: **Phase-1 structure clarified** — among the "base libs", **only `unified-trading-library` produces a Docker
  image**; `unified-api-contracts` / `unified-cloud-interface` / `unified-internal-contracts` are **wheel-only** (baked
  INTO the UTL base image as published wheels from the AR `unified-libraries` index). Phase-1 local = validate lib WHEELS
  + build the UTL IMAGE.
- 2026-06-17: **CLONE-SET ≠ BUILDABLE-SET** — this slot has **25** cloned repos; `unified-cloud-interface` +
  `unified-internal-contracts` are **NOT cloned** (exist on GitHub, default=main, not archived; cloud-interface is also
  vendored as a module inside UTL at `unified_trading_library/cloud_interface/`). Trigger-only libs are **GCP-direct** (or
  clone first) — can't be local-built here; the `unified-*-interface` build-trigger repos are likely the same.
- 2026-06-17: **`unified-api-contracts` wheel PASS** — `uv build --wheel` → `unified_api_contracts-0.19.0-py3-none-any.whl`, free/local.
- 2026-06-17: **UTL base-image local build — attempt #1 FAILED, root-caused, #2 PASS.**
  - **#1 (`EXTRA_PYTHON_INDEX_URL` token path) FAILED** at `Dockerfile:93` `uv pip install -e .`: *"unified-api-contracts
    not found in the package registry"* — **even though UAC 0.19.0 IS published in AR** (08:42). Root cause: **`uv` does
    NOT read the `pip.conf` the Dockerfile writes** (lines 78-82), so the AR index was never applied → UAC unresolved.
    **⚠ Phase-3 flag:** AWS-CodeBuild uses this same env→pip.conf hook for *external* private deps (CodeArtifact) — verify
    it actually feeds uv there (UAC itself is fine — AWS also `.deps`-clones it).
  - **Real model:** cloudbuild's `clone-uac-source` (and AWS buildspec) put UAC into **`.deps/unified-api-contracts`**;
    Dockerfile line 88 installs from there, so the base build never needs the index for UAC. UTL's **only** internal dep is
    UAC (other 59 deps are public PyPI → no AR auth needed for the base image).
  - **#2 (`.deps/UAC` source, no index) PASS** — UTL base image built clean (`sha256:7b614fec…`, 2.77GB); `import
    unified_trading_library, unified_api_contracts` OK inside the image. **Canonical local UTL-build recipe.** (Image
    entrypoint intercepts args → use `docker run --entrypoint python …` for in-image checks.)
- 2026-06-17: **FINDING (P3 fix) — `.deps/` is NOT in UTL `.gitignore`** but builds generate it → leaves the slot dirty
  (FF-pull `[skip:dirty]` risk). Per "generated artifacts are gitignored, never committed" it should be added to
  `unified-trading-library/.gitignore`. (Temp `.deps/` cleanup pending — sandbox blocks `rm -rf`/`git clean`; gitignoring
  is the durable fix.)
- 2026-06-17: **PHASE-2 LOCAL SWEEP (14 cloned Python services) — 6 PASS / 9 FAIL, single root cause = TWO Dockerfile patterns.**
  - **✅ Pattern A (base-image, self-contained: `FROM utl@digest` + `uv pip install --no-deps -e .`)** builds clean with a
    single-repo `docker build` context: **instruments, client-reporting-api, deployment-service, features, market-tick-data,
    agent-orchestrator** (+ UTL base + UAC wheel). 6 services.
  - **❌ Pattern B (vendored-sibling: `COPY unified-api-contracts/ unified-trading-library/` into context + `uv sync --frozen`
    against `file:///unified-api-contracts` path source)** FAILS a single-repo context — needs a **multi-repo build context**
    with UAC+UTL sources staged in (cloudbuild does this; local single-repo `docker build` doesn't). 9 services:
    - *B1 fails at the `COPY` step* ("`/unified-api-contracts`: not found"): **alerting, batch-live-reconciliation, execution,
      greeks, strategy**.
    - *B2 fails at `uv sync --frozen`* ("Distribution not found at `file:///unified-api-contracts`"): **fund-administration,
      market-data-processing, ml, trading-agent**.
  - **These are NOT broken code** — Pattern B builds fine on GCP (cloudbuild stages siblings). The failure is the local
    single-repo context. **Follow-up:** (a) build Pattern-B locally with a staged multi-repo context to validate current
    code; (b) **the A-vs-B inconsistency is itself a finding** → candidate fleet Dockerfile normalization (Pattern A is the
    clean base-image-leveraging form; Pattern B redundantly re-vendors + re-syncs sibling sources despite FROM-ing the base).
    File as a separate normalization item, do NOT fork mid-validation.
- 2026-06-17: **Pattern-B with multi-repo context (UAC+UTL staged) → 3 more PASS, 6 still FAIL — Pattern B is PER-SERVICE BESPOKE.**
  - **PASS with UAC+UTL siblings staged:** **alerting** (5.57GB), **execution** (6.92GB), **greeks** (5.78GB). So those 3
    vendor exactly UAC+UTL → local-buildable with a 2-sibling context. (Note Pattern-B images run ~5.5–7GB vs Pattern-A ~3GB
    — they re-vendor+re-sync, so fatter.)
  - **Still FAIL — each needs MORE, and differently:**
    - **strategy** vendors a THIRD sibling — `COPY market-tick-data-service/` → needs mtds staged too.
    - **batch-live-reconciliation** — `COPY configs/cloud-providers.yaml` (a file NOT in its repo; cloudbuild stages it
      from deployment-service/UAC).
    - **fund-administration / market-data-processing / ml / trading-agent (B2)** — `uv.lock` pins UAC at the **absolute path
      `file:///unified-api-contracts`** (filesystem ROOT), so `uv sync --frozen` fails unless the sibling sits at exactly
      `/unified-api-contracts` (not `/app/...`). Fragile build-machine-absolute lock paths.
  - **META-FINDING (the real deliverable):** the fleet's service Docker build contracts are **inconsistent + fragile** —
    Pattern A (6 services) is the clean self-contained base-image form; Pattern B (9 services) re-vendors a *per-service-varying*
    set of sibling sources/configs and `uv sync`s against absolute lock paths. Each Pattern-B service needs its own bespoke
    cloudbuild staging, which is why local repro is hard and why they're fatter. **Recommendation: a fleet Dockerfile
    NORMALIZATION to Pattern A** (FROM base + `uv pip install --no-deps -e .`) — separate task, file it; do NOT fork here.
  - **Local-validation status:** 9/15 Python services build locally (6 Pattern-A + alerting/execution/greeks). The other 6
    are GCP-authoritative (their cloudbuild stages correctly) — chasing bespoke local contexts per service has diminishing
    value vs the normalization fix.
- 2026-06-17: **NODE/UI images (3) — 1 PASS / 2 multi-repo-context.**
  - ✅ **unified-trading-system-ui** — clean standalone build (2.46GB).
  - ❌ **deployment-ui** — `COPY unified-admin-ui/packages/core` (a monorepo sibling NOT cloned here) → same vendored-sibling
    fragility in the UI layer → GCP-authoritative.
  - ❌ **deployment-api** — Dockerfile **bundles the dashboard** (`COPY /ui` — the deployment-ui SPA, the shared-image pattern
    behind the Cloud Run service we promoted earlier); needs the UI staged → GCP-authoritative (this one is **by-design**
    bundling, not the same "normalize away" case). Also note its base is pinned to a DIFFERENT digest (`e939b4ee…`) than the
    current `:latest` (`a1b0cf83…`) — another stale base-digest pin.
- 2026-06-17: **EOD STOP (local phase complete).** Local image-build validation done: **10/18 image repos build standalone
  locally** (UTL base + UAC wheel + 6 Pattern-A services + 3 Pattern-B-simple + unified-trading-system-ui); the **8 bespoke**
  (6 Pattern-B + deployment-ui + deployment-api) are GCP-authoritative. **GCP pass deferred to 2026-06-18 AM (operator).**
  Housekeeping done: temp `.deps`/orchestrator removed, UTL `.gitignore` shipped (`.deps/` ignored), normalization issue filed.

## Composes with / SSOTs
- IAM/unknown-image (separate): `plans/active/issues/deployment_dashboard_image_status_and_multicloud_toggle_2026_06_17.md`
- Build pipeline: service `cloudbuild.yaml` canonical template (STEP 5.22 canary services); UTL `cloudbuild.yaml`;
  FROM-digest ratchet (CLAUDE.md § Dependencies+builds); `quickmerge.sh` `--build` (Gap 5).
- Tarball path: `deployment-service/scripts/vm/create-code-tarballs.sh`; `codex/05-infrastructure/vm-tarball-deployment.md`.
- VM/image deploy topology: `codex/04-architecture/runtime-deployment-topology.md`.
