---
title: "Build-Operability Smoke — every repo image builds AND actually runs"
created: 2026-06-19
status: active
parent_epic: infrastructure_master
assigned_vm: planning
plan_of_record: plans/active/cicd_quality_gates_2026_06_18.md
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
source:
  - 2026-06-19 operator request — test that we can create images for ALL repos, and that the images are OPERABLE (open
    up + run), not just `docker build` exit 0 → needs a smoke test
  - 2026-06-19 mdps build fix (build_operability proven end-to-end on market-data-processing-service)
  - 2026-06-19 fleet Dockerfile/cloudbuild sweep (3 build-blocker classes catalogued below)
priority: P1
---

# Build-Operability Smoke — every repo image builds AND actually runs

## Why

Operator (2026-06-19): before the deploy phase (its own beast), prove that **every repo's image can be created AND is
operable** — the container opens up and runs, not merely that `docker build` exits 0. A green build hides runtime breaks
(a `--no-deps`/`--no-sources` install that drops a dep imports-but-crashes; a broken entrypoint). So we need a **smoke
test that probes operability**, run across the fleet.

**Approach (operator-confirmed 2026-06-19):** standalone smoke harness now + batch-fix the known build-blockers first,
then wire the proven probe into each cloudbuild as the durable follow-up.

## Validated operability probe (proven on mdps 2026-06-19)

A bare `docker run <img> --help` is a BAD probe: `ServiceBootstrap.run()` emits the `STARTED` event (→ cloud event sink
→ needs `GCP_PROJECT_ID`) BEFORE it handles `--help`. The correct probe is the **credential-free test env** (same as the
unit suite):

```bash
# 1. import probe — catches a --no-deps/--no-sources install that dropped a runtime dep
docker run --rm --entrypoint python <img> -c "import <pkg>; print('IMPORT OK')"
# 2. entrypoint probe (batch/CLI services) — catches a broken CLI/bootstrap
docker run --rm -e CLOUD_PROVIDER=local -e CLOUD_MOCK_MODE=true \
  -e GCP_PROJECT_ID=smoke -e ENVIRONMENT=dev <img> --help   # exit 0 = operable
```

mdps proof: IMPORT OK (exit 0) + `--help` full usage (exit 0), image `market-data-processing-service:8025264`.

**Probe differs by service TYPE** (one size does not fit):

- **Batch/CLI service** (mdps, mtds, instruments, features, batch-live-recon, …): import + `--help`.
- **API service** (deployment-api, client-reporting-api, ml-service, fund-administration, alerting): import + boot
  uvicorn + probe `/health` (or the service health route) + stop. `--help` may also work where a CLI exists.
- **Library** (unified-trading-library): import-only (no entrypoint).
- **UI / Node** (deployment-ui, unified-trading-system-ui): Node build + `next build` smoke — separate harness, not the
  Python probe.

## Build-blocker landscape (fleet sweep 2026-06-19)

Three independent classes, each a subset. **Stale base digest is fleet-wide** (the digest-refresh fan-out is broken —
see Phase 5). `:latest` base digest at sweep time = `sha256:2baa8551…` (UTL 0.13.0 / UAC 0.19.0).

| Repo                              | Install pattern        | In-image-QG guard | Base digest                     | Action needed                                                        |
| --------------------------------- | ---------------------- | ----------------- | ------------------------------- | -------------------------------------------------------------------- |
| market-data-processing-service    | ✅ fixed               | ✅ guard          | ✅ current                      | DONE (mdps@8025264d)                                                 |
| deployment-api                    | frozen, **no staging** | ⚠ no-guard       | **STALE e939b4ee** (UTL 0.11.0) | **HIGH**: digest + guard + frozen→`--no-sources`/staging (API probe) |
| trading-agent-service             | frozen, **no staging** | ⚠ no-guard       | **STALE e939b4ee** (UTL 0.11.0) | **HIGH**: digest + guard + frozen-fix                                |
| fund-administration-service       | frozen, **no staging** | ⚠ no-guard       | STALE c54f13d9                  | digest + guard + frozen-fix (API probe)                              |
| ml-service                        | frozen, **no staging** | ⚠ no-guard       | STALE 9db3ae4b                  | digest + guard + frozen-fix (API probe)                              |
| client-reporting-api              | pip (other)            | ⚠ no-guard       | STALE c54f13d9                  | digest + guard (API probe)                                           |
| deployment-service                | pip `--no-deps`        | ⚠ no-guard       | STALE c54f13d9                  | digest + guard                                                       |
| features-service                  | pip `--no-sources`     | ⚠ no-guard       | STALE a9026757                  | digest + guard                                                       |
| greeks-service                    | frozen + staging✓      | ⚠ no-guard       | STALE c54f13d9                  | digest + guard                                                       |
| instruments-service               | pip `--no-deps`        | ⚠ no-guard       | STALE c54f13d9                  | digest + guard                                                       |
| agent-orchestrator                | pip (other)            | ⚠ no-guard       | STALE 9db3ae4b                  | digest + guard (FastAPI; also has node dashboard)                    |
| alerting-service                  | frozen + staging✓      | ✅ guard          | STALE c54f13d9                  | digest refresh only (API probe)                                      |
| batch-live-reconciliation-service | pip `--no-deps`        | ✅ guard          | STALE c54f13d9                  | digest refresh only                                                  |
| execution-service                 | frozen + staging✓      | ✅ guard          | STALE c54f13d9                  | digest refresh only                                                  |
| market-tick-data-service          | pip `--no-deps`        | ✅ guard          | STALE c54f13d9                  | digest refresh only                                                  |
| strategy-service                  | frozen + staging✓      | ✅ guard          | STALE c54f13d9                  | digest refresh only                                                  |
| unified-trading-library           | pip `--no-sources`     | n/a               | n/a (IS the base)               | smoke = import-only; builds itself                                   |
| deployment-ui                     | n/a (Node)             | n/a               | n/a                             | Node build smoke (separate)                                          |
| unified-trading-system-ui         | n/a (Node)             | n/a               | n/a                             | Node build smoke (separate)                                          |

NOTE: "stale ≠ broken" — a stale digest only fails the build if the pinned base ships libs OLDER than that repo's
`pyproject.toml` floors (mdps's exact failure). The `e939b4ee` repos are highest risk (that base = UTL 0.11.0). The
`c54f13d9` repos may still satisfy — verify per-repo, don't assume. Adding the QG `CLOUD_BUILD` guard is harmless even
where in-image QG doesn't run (it only activates when the PM base script is absent), so batch-add it safely.

## Build-trigger reality — the map is NOT 1:1 with repo dirs (discovered 2026-06-19)

**BIG FINDING.** "Build all repos" is the wrong frame: the buildable units are the **~25 Cloud Build `-build` triggers**
(`asia-northeast1`), and they do NOT correspond 1:1 to the 19 workspace dirs. Three mismatch classes:

1. **A repo splits into MANY build triggers** (monorepo of buildable sub-services):
   - `features-service` → 5 triggers: `features-{calendar,delta-one,multi-timeframe,onchain,volatility}-service-build`.
   - `ml-service` → 3 triggers: `ml-inference-service-build`, `ml-training-service-build`, `ml-training-ui-build`.
   - So the repo-root `Dockerfile` I swept may not be the one each sub-service builds — each likely has its own.
2. **Triggers with no workspace dir** (sub-package / library builds): `execution-algo-library-build`,
   `unified-{cloud-services,config-interface,domain-services,events-interface,market-interface,order-interface,reference-data-interface}-build`,
   `api-contracts-build` (UAC). These build from sub-packages or separate library repos, not a top-level service dir.
3. **Repo dirs with a Dockerfile but NO `-build` trigger at all** — cannot be built via the standard mechanism:
   `agent-orchestrator` (VM-deployed, not a cloudbuild image), `alerting-service`, `batch-live-reconciliation-service`,
   `client-reporting-api`, `fund-administration-service`, `greeks-service`, **`trading-agent-service`**,
   `deployment-ui` (likely = `deployment-dashboard-build`), `unified-trading-system-ui` (separate UI pipeline),
   `unified-trading-library` (the BASE image — its own base-image build, not a `-build` trigger).

**Consequence for trading-agent canary:** the digest+install+guard fix was shipped (`trading-agent-service@388d5ac1`)
but it has **NO build trigger**, so it can't be validated via Cloud Build. Either it's intentionally not-yet-imaged
(WIP / deployed another way) or it's a pipeline gap. NEEDS OPERATOR TRIAGE (next todo).

- [x] ✅ [INFRA] P0. **Triage the trigger-less repos with the operator** — DONE 2026-06-19. All 6 were
      pipeline GAPS (new repos predating the trigger pipeline): triggers created + builds GREEN (see Phase 2.5 + progress
      log). `deployment-ui` → `deployment-ui-main-deploy` (Node UI bundled into deployment-api image; NOT a standalone
      Python `-build` trigger; old `deployment-dashboard` zombie deleted). UTL base-image →
      `unified-trading-library-live-defi-rollout` ("Build UTL base Docker image + publish wheel on live-defi-rollout
      push"). 28 live triggers now 1:1 with live repos. — PM@ef452ee05
- [ ] [SCRIPT] P0. **Re-map the harness to the REAL trigger list** (not `<repo>-build`): drive `--all` off the 25
      `-build` triggers, expand `features-service`→5 + `ml-service`→3, map `deployment-ui`→`deployment-dashboard`, and
      SKIP trigger-less repos with an explicit "no trigger" row (never a silent omission). Repo: e2e-testing.

## Phase 0 — Probe design + proof (DONE)

- [x] ✅ [INFRA] P0. DONE 2026-06-19 — design + validate the operability probe on a real image. mdps@8025264d: IMPORT
      OK + `--help` exit 0 under the credential-free env
      (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true     GCP_PROJECT_ID=smoke ENVIRONMENT=dev`). Established that a bare
      `docker run --help` is a BAD probe (bootstrap emits STARTED before --help) and that the existing cloudbuild Step
      #6 in-image QG is HOLLOW (exits 0 when PM base script absent → not actually testing operability).

## Phase 1 — Standalone build+smoke harness

- [x] ✅ [SCRIPT] P0. DONE 2026-06-19 — e2e-testing@d8a52254. Wrote `e2e-testing/scripts/build_smoke/build_smoke_all.sh`
      (path is `build_smoke/` not `build/` — the repo `.gitignore` `build/` pattern swallowed `scripts/build/`). Per
      repo: trigger the regional Cloud Build → pull → type-appropriate probe (python: import + `--help` under the
      credential-free env; library: import-only; ui: SKIP→Phase 4) → `BUILD / IMPORT / RUN` report row. `--all` /
      `--repo` / `--skip-build` (smoke an already-pushed image, no build spend) / `--tag`. **Disk-bounded**: `docker rmi`
      after every probe + an 8G pre-flight guard (a 2-image run hit `No space left on device` at 95% disk — caught by
      smoke-test-before-scale). Lifecycle marker present (campaign). The richer api `/health` + ui `next build` probes
      are deferred into Phase 4. Repo: e2e-testing.
- [x] ✅ [SCRIPT] P1. DONE 2026-06-19 — validated the harness on the 2 known-good repos: mdps `IMPORT ✅ RUN ✅` + mtds
      `IMPORT ✅ RUN ✅` (both `--skip-build`, exit 0, no images left behind). Harness end-to-end proven before fanning
      out. Repo: e2e-testing.

## Phase 2 — Batch-fix build blockers (so builds go green before smoking)

- [ ] [INFRA] P0. **Refresh every stale `BASE_IMAGE_DIGEST` → current `:latest`** across the 15 stale service repos
      (table above). Prefer a propagation pass (`scripts/propagation/`) over 15 hand-edits. Verify each refreshed pin
      satisfies that repo's `pyproject.toml` floors (the actual break condition). Repos: all stale-pinned (see table).
- [ ] [CI] P0. **Add the in-image QG `CLOUD_BUILD` guard** to the 10 no-guard `scripts/quality-gates.sh` (mirror the
      mtds/mdps pattern: `BASE_QG_SCRIPT` existence check → `exit 0` when `CLOUD_BUILD=true` and the PM base script is
      absent). Repos: agent-orchestrator, client-reporting-api, deployment-api, deployment-service, features-service,
      fund-administration-service, greeks-service, instruments-service, ml-service, trading-agent-service.
- [ ] [DOCKER] P0. **Fix the 4 frozen-without-sibling-staging repos** — `uv sync --frozen` with no `stage-siblings`
      cloudbuild step breaks like mdps did. Switch to `uv pip install --system -e . --no-sources` (keeps external deps)
      OR add a sibling-staging step. Verify each actually has editable sibling deps before changing. Repos:
      deployment-api, fund-administration-service, ml-service, trading-agent-service.
- [x] ✅ [DOCKER] P1. PARTIAL 2026-06-19 — canaries proved the recipe. **deployment-api@5d58dccd: digest+guard ONLY**
      (its install was already explicit-external-deps — the "frozen" sweep flag was a false positive matching a
      comment). Build `ca8aed2f` SUCCESS; smoke `IMPORT ✅` (RUN `❌` is a probe-limit, not a break: gunicorn entrypoint
      ≠ `--help`; API `/health` probe deferred to Phase 4). **trading-agent-service@388d5ac1: genuine mdps-clone**
      (digest + `uv sync --frozen`→`--no-sources` + guard) — fix shipped but **UNBUILDABLE: no Cloud Build trigger
      exists** (see Build-trigger reality + the P0 triage todo). So the recipe is proven on deployment-api; trading-agent
      awaits a trigger decision. Repos: deployment-api ✅, trading-agent-service (fix shipped, build blocked-no-trigger).

## Phase 3 — Run smoke across the fleet + report

- [ ] [SCRIPT] P0. Run `build_smoke_all.sh --all` across every repo; produce the `BUILD / IMPORT / RUN` matrix. Any RED
      → triage (build-blocker vs genuine operability break vs probe-env gap) and fix. Definition of done: every Python
      service repo is `BUILD ✅ IMPORT ✅ RUN ✅`; UTL import-green; the 2 Node UIs build-green. Repo: e2e-testing
      (driver) + per-repo fixes.
- [ ] [INFRA] P1. Capture per-repo build-minute cost + flag any repo whose image is unexpectedly large / slow (a
      side-signal of a bad install). Repo: e2e-testing.

## Phase 4 — Wire the probe into cloudbuild (durable, replaces the hollow Step #6)

- [ ] [CI] P1. Replace/augment the hollow in-image QG Step #6 with a **real operability smoke step** in each cloudbuild:
      run the validated import + entrypoint(`--help`/`/health`) probe inside the freshly-built image (credential-free
      env) BEFORE the push, so every future build is gated on "actually runs", not just "compiled". Roll out via the
      cloudbuild template if one exists, else per-repo. This is the durable successor that lets Phase 1's standalone
      harness retire. Repos: all service repos (+ template SSOT).

## Phase 3.5 — Remaining-repos build sweep results (2026-06-19) — the existing pipeline is broadly RED

Triggered all 11 remaining service-image `-build` units on `live-defi-rollout`. **2 GREEN** (instruments-service
`b2a975e4`, execution-service `f84a216f` — both build clean on their existing config). **9 FAILED**, root-caused into
4 classes:

- [ ] [INFRA] P0. **ZOMBIE TRIGGERS — 7 of the 9 failures build ARCHIVED repos.** `features-{calendar,delta-one,
      multi-timeframe,onchain,volatility}-service-build` + `ml-inference-service-build` + `ml-training-service-build`
      point at the SEPARATE GitHub repos `features-*-service` / `ml-*-service`, which were **archived read-only
      2026-05-08** when consolidated into `features-service` (8→sub-packages, `--feature-family` flag) and `ml-service`
      (per `workspace-manifest.json` notes + `features_repo_consolidation_2026_05_08.md`). Their builds fail on stale
      `uv sync --frozen --no-dev --system` (`--system` invalid on `uv sync`) — but the repos are DEAD; the fix is to
      **DELETE the 7 obsolete triggers** (consolidation cleanup that never happened), NOT fix their Dockerfiles. Repo:
      deployment-service (trigger inventory) — operator confirm before deleting.
- [ ] [INFRA] P0. **Create triggers for the LIVE consolidated repos** `features-service` + `ml-service` (same gap as the
      6 new repos — consolidation made the repos but no `-build` trigger). Their Dockerfiles are already correct
      (features-service `uv pip install --system -e . --no-sources`; ml-service `uv sync --frozen --no-dev`). Link +
      create trigger + build. NOTE: features-service builds ONE image parameterised by `--feature-family`; confirm the
      trigger/cloudbuild shape. Repos: features-service, ml-service.
- [ ] [DOCKER] P1. **strategy-service** build fails: `Dockerfile:47 COPY market-tick-data-service/` — a cross-repo
      sibling COPY not staged in the build context (and a service→service coupling that the no-service-deps rule frowns
      on). Diagnose why strategy needs the mtds tree (test fixtures? a vendored client?) → stage it in cloudbuild OR
      remove the COPY. Repo: strategy-service.
- [ ] [CI] P1. **deployment-service** build fails at Step #2 pulling the base image:
      `denied: Unauthenticated request ... downloadArtifacts` — its cloudbuild runs the docker build BEFORE configuring
      registry auth (the green repos have a `configure-docker` + `pull-base-image` step first). Add/reorder the auth
      step. Repo: deployment-service.

## Phase 5 — Root-cause the stale-digest fan-out (so this doesn't recur)

- [ ] [INFRA] P1. **Why is every service repo's `BASE_IMAGE_DIGEST` stale? — RCA DONE 2026-06-19, fix pending.**
      Mechanism (traced): a repo version-bump → `repository_dispatch[version-bump]` → PM `update-repo-version.yml`
      resolves the UTL base `:latest` digest (step ~line 408: `docker manifest`/registry read of
      `unified-trading-library:latest`) and attaches `base_image_digest` to the `dependency-update` consumer fan-out;
      each consumer's `update-dependency-version.yml` (trigger `repository_dispatch[dependency-update]`) rewrites the
      `ARG BASE_IMAGE_DIGEST` default. **Root cause (3 compounding gaps):** (1) the digest is attached **ONLY when
      resolved** — "missing GCP secrets or a registry miss → empty digest → consumers skip the digest step" (workflow
      comment ~line 375) — so any GHA run without GCP auth silently propagates NO digest; (2) it only rides a **UTL
      version-bump** event, not every base-image republish (a UAC/other-base-layer change republishes the base but
      doesn't re-resolve+dispatch the digest); (3) the consumer fan-out follows the **dependency graph**, so a repo not
      in that graph at dispatch time (e.g. the 6 NEW repos) never receives a digest dispatch → stuck at whatever digest
      it was created with (hence the fleet sits at `c54f13d9` = last successful resolve+dispatch, new repos at
      `e939b4ee`/varied). **Fix direction**: (a) ensure GCP auth (Workload-Identity/SA) is available in the
      digest-resolve step + fail-LOUD on empty digest instead of silently skipping; (b) re-resolve+dispatch the digest
      on **base-image republish** (a UTL/UAC `:latest` push), not only a UTL version-bump; (c) include ALL image-building
      repos in the fan-out target set (or add a periodic digest-drift sweep cron that opens refresh PRs for any repo
      whose pin lags `:latest`). Composes with the stale-pin audit in `deployment_ui_monitoring_pane_2026_06_19.md`.
      Repo: PM (`update-repo-version.yml`) + per-repo `update-dependency-version.yml`.

## Success criteria

- Every Python service repo image: `docker build` green AND import-green AND entrypoint/health-green (operable).
- unified-trading-library import-green; deployment-ui + unified-trading-system-ui Node-build-green.
- The operability probe runs inside each cloudbuild (Phase 4) so a future runtime break fails the build, not prod.
- The base-digest fan-out is fixed (Phase 5) so pins stay fresh automatically.

## Codex SSOT updates

- `codex/06-coding-standards/quality-gates.md` — in-image operability smoke step (the real "test the artifact you
  deploy") + the credential-free probe env.
- `codex/08-workflows/ci-cd-flow.md` — build-operability gate in the cloudbuild pipeline; base-digest fan-out mechanism.

## Phase 2.5 — wire the 6 new repos' build triggers (the GAP — operator-confirmed 2026-06-19)

The 6 trigger-less repos are NEW (pipeline designed ~3 months ago, predates them). Filling the gap:

- [x] ✅ [INFRA] DONE 2026-06-19 — **all 6 repos linked** to the `iggyikenna-github` Cloud Build connection
      (`gcloud builds repositories create`, autonomous — the GitHub App covers them, no operator grant needed).
- [x] ✅ [INFRA] DONE 2026-06-19 — **all 6 `-build` triggers created** imperatively against `iggyikenna-github`
      (`push ^main$`, `cloudbuild.yaml`), mirroring the working mdps trigger: `alerting-service-build`,
      `batch-live-reconciliation-service-build`, `client-reporting-api-build`, `fund-administration-service-build`,
      `greeks-service-build`, `trading-agent-service-build`. Created imperatively (NOT via the TF module) because the
      `modules/cloud-build/gcp` module defaults to connection `ln` which no longer exists (only `iggyikenna-github`) —
      same precedent as `deployment-service-jobs-image` (created imperatively, TF-imported later).
- [ ] [INFRA] P1. **Reconcile TF SSOT**: add the 4 missing repos (batch-live-recon, fund-admin, greeks, trading-agent —
      alerting + client-reporting are already in `locals.services`) to `deployment-service/terraform/cloud-build/gcp`
      `locals.services`, `terraform import` all 6 imperative triggers into state, AND **fix the module connection drift**
      (`ln` → `iggyikenna-github`) so a future apply doesn't try to recreate them against the dead connection. Do NOT
      blind `apply` the module before the import + connection fix (would disrupt the 15 live triggers). Repo:
      deployment-service.
- [ ] [DOCKER] P1. fund-administration-service has a **dead builder stage** (stage 1 builds but stage 2 never
      `COPY --from=builder` — it re-installs from scratch). Fixed both install lines to build-green for now; a follow-up
      should delete the redundant builder stage (faster build). Repo: fund-administration-service.

## Progress Log

- **2026-06-19** — Canaries proved the recipe (mdps operable; deployment-api `ca8aed2f` build+import green). Harness
  shipped (`e2e-testing@d8a52254`). **6 new repos**: linked + triggered (above). Build-blocker fixes:
  trading-agent@388d5ac1 (digest+install+guard); alerting/batch (digest), client-reporting/greeks (digest+guard),
  fund-admin (digest+2×install+guard) landing via QG+quickmerge sweep. NEXT: build all 6 on `live-defi-rollout` +
  smoke, then the remaining trigger units (re-map harness to the real ~25 triggers: features×5, ml×3, the interface
  libs). Stale base digest = fleet-wide (Phase 5 fan-out RCA). Disk on this host runs ~95% — smoke prunes per image.
- **2026-06-19 (cont.)** — ✅ **6/6 new repos build GREEN.** First pass: trading-agent `3f8c8f19`, alerting
  `3d01d550`, client-reporting `de41d7da`, greeks `827af2f7` SUCCESS. 2 surfaced **pre-existing bugs** (these repos had
  never been built): **batch** — Dockerfile `COPY configs/cloud-providers.yaml` referenced a context-absent file (stale;
  UAC-packaged since 2026-06-10) + its in-image QG guard was incomplete (only handled the `/workspace`-staged CI mode,
  not the no-PM-in-image case → fell to `git rev-parse` → empty WORKSPACE_ROOT); fixed both (`1215e6be`, then the guard
  `…`) → rebuild `e4287026` SUCCESS. **fund-admin** — Dockerfile didn't `COPY scripts/`, so the in-image QG ran the BASE
  IMAGE's leftover library QG (`base-library.sh`, unguarded); added `COPY scripts/` (`e9344230`) → rebuild `7f039a2d`
  SUCCESS. **Smoke**: all IMPORT ✅; RUN ✅ for CLI entrypoints (trading-agent, client-reporting); RUN n/a for the
  **uvicorn API services** (alerting, greeks — `--help` is not a valid probe; the boot+`/health` probe is Phase 4).
  **Lesson**: the install-pattern + guard greps had FALSE POSITIVES (matched comments / a different `CLOUD_BUILD`
  reference) — always read the actual `RUN`/source line, never trust the grep classification. NEXT: remaining ~19
  existing trigger units (build-first, fix-failures) + Phase 4 (uvicorn `/health` probe in the harness + cloudbuild) +
  Phase 5 (fan-out RCA) + TF reconcile (import the 6 imperative triggers, fix the `ln` drift).
- **2026-06-19 (STALE-REF CLEANUP — operator: "12→70→25 repos, find+remove all refs to archived/old repos")** — the
  remaining-sweep failures were mostly **debris from the repo-count churn**. Audited every trigger/link/config against
  the canonical live 25 (`workspace-manifest.json.repositories`) + the authoritative dead lists (`prune_removed_
  repositories.py` REMOVED frozenset + manifest `removedEntries`). **Removed**: (1) **37 ZOMBIE Cloud Build triggers**
  (of 65) targeting archived repos — features-{calendar,delta-one,multi-timeframe,onchain,volatility}-service +
  ml-{inference,training}-service (consolidated into features-service/ml-service), the 7 `unified-*-interface/services`
  removed libs, `execution-algo-library`, `ml-training-ui`, and `deployment-dashboard`→`unified-trading-deployment-v2`
  (the OLD deployment-ui name); **28 live triggers remain**. (2) **32 stale connection links** (incl. old names
  `market-tick-data-handler`, `live-health-monitor-ui`, `unified-trading-deployment-v2`); 19 live remain. (3) **8 dead
  `locals.services` entries** in `deployment-service/terraform/cloud-build/gcp/main.tf` (would have RECREATED the
  zombies on `terraform apply`). (4) **+9 orphans to the `REMOVED` frozenset** (`unified-{cloud,domain}-services`,
  `unified-{events,order}-interface`, `ml-training-ui`, `market-tick-data-handler`, `live-health-monitor-ui`,
  `execution-results-api`, `market-data-api`) — they were live triggers/links but in NEITHER authoritative dead list
  (the canonical list was incomplete). Trigger landscape is now 1:1 with live repos. NEXT (the actual "moving forward"):
  create features-service + ml-service triggers (consolidated live repos, currently trigger-less after the zombie
  purge) + fix strategy-service (cross-repo mtds COPY) + deployment-service (registry-auth ordering).
