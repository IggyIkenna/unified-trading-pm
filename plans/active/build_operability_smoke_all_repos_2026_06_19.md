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

- [ ] [INFRA] P0. **Triage the trigger-less repos with the operator** — for each of {alerting-service,
      batch-live-reconciliation-service, client-reporting-api, fund-administration-service, greeks-service,
      trading-agent-service}: is it intentionally not built as a Cloud Build image (WIP / different deploy path), or is a
      missing trigger a gap to fill? "Build all repos" can't include a repo with no trigger until this is answered.
      Also confirm `deployment-ui`↔`deployment-dashboard-build` and the UTL base-image build path. Repo: PM/deployment-
      service (trigger inventory) + operator decision.
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
- [ ] [DOCKER] P1. Diagnose the **2 highest-risk repos first** (deployment-api, trading-agent-service — both on the old
      `e939b4ee` base mdps's floors had outgrown): confirm they fail the same way, apply digest+guard+frozen fixes,
      build green. These are the canaries for the batch fix. Repos: deployment-api, trading-agent-service.

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

## Phase 5 — Root-cause the stale-digest fan-out (so this doesn't recur)

- [ ] [INFRA] P1. **Why is every service repo's `BASE_IMAGE_DIGEST` stale?** The fan-out
      (`update-dependency-version.yml` digest-refresh PR on base republish) evidently has not landed fleet-wide (mdps
      was 2 generations behind; the fleet is 1 behind). Diagnose: does the workflow run? does it open PRs? do they
      merge? Fix the mechanism — hand-refreshing digests (Phase 2) is whack-a-mole without this. Composes with the
      stale-pin audit todo in `deployment_ui_monitoring_pane_2026_06_19.md`. Repos: PM (fan-out workflow) + per-repo
      `update-dependency-version.yml`.

## Success criteria

- Every Python service repo image: `docker build` green AND import-green AND entrypoint/health-green (operable).
- unified-trading-library import-green; deployment-ui + unified-trading-system-ui Node-build-green.
- The operability probe runs inside each cloudbuild (Phase 4) so a future runtime break fails the build, not prod.
- The base-digest fan-out is fixed (Phase 5) so pins stay fresh automatically.

## Codex SSOT updates

- `codex/06-coding-standards/quality-gates.md` — in-image operability smoke step (the real "test the artifact you
  deploy") + the credential-free probe env.
- `codex/08-workflows/ci-cd-flow.md` — build-operability gate in the cloudbuild pipeline; base-digest fan-out mechanism.
