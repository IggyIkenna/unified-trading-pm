---
title: "UTL Base-Image Rebuild + Cross-Service Cloud Run Unblock"
priority: P0
status: active
owner: agent
created: 2026-04-22
locked_by: live-defi-rollout
locked_since: 2026-04-22
type: infra
epic: epic-infra
completion_gates:
  code: C5
  deployment: D2
  business: none
repo_gates:
  - repo: unified-trading-library
    code: C0
    deployment: D0
    business: none
depends_on: []
isProject: false
---

## Context

The shared Python base image
`asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library:latest` in
Artifact Registry is **stale relative to current UTL source on `origin/live-defi-rollout`**. Every downstream service
that uses this base image fails at container runtime with:

```
ImportError in unified_trading_library.core.__init__:11
→ from unified_trading_library.core.client_factory import (
        clear_client_caches,
        download_from_storage,
        get_secret,
        get_secret_client,
        get_storage_client,
        storage_exists,
        upload_to_storage,
    )
```

The `client_factory` module exists in current UTL source
(`unified-trading-library/unified_trading_library/core/client_factory.py` — confirmed present on
`origin/live-defi-rollout`) but is absent (or has a different shape) inside the baked AR image.

### Witnesses

1. **features-sports-service Cloud Run Job** (`features-sports-service-job`) — deployed by D2+D3 sub-agent
   2026-04-22T00:30Z. First execution via `gcloud workflows execute` reports `SUCCEEDED` at the workflow level, but
   that's because the workflow's `check_features` step uses `"completionTime" in body` which is always truthy — it does
   not gate on `failedCount == 0`. The underlying Cloud Run execution actually exited(1) with the ImportError above.
2. **features-onchain-service daily workflow** — has been failing daily for the same reason (incidental finding from
   D2+D3).
3. **sports-scheduler** — `deployment-service/Dockerfile` line 117 (`FROM api AS sports-scheduler`) inherits line 33
   (`FROM ... unified-trading-library:latest AS base`), so Plan 5 (`sports_scheduler_cron_activation`) Cloud Run
   activation is ALSO blocked on this rebuild once Plan 12 (`deployment_service_build_infrastructure_repair`) finishes.

### Phase-0 pre-audit findings (this shapes the scope)

Rather than a "simple rebuild", archaeology shows the Cloud Build pipeline IS auto-wired but has been FAILING for 2+
days. Plan 13 must actually diagnose the build breakage and fix it, not just click rebuild.

| Check                                                    | Finding                                                                                                                                                                                                                                                                                 |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UTL `Dockerfile` present                                 | Yes — `unified-trading-library/Dockerfile` (99 lines). `FROM python:3.13-slim` → installs gcsfuse, gcloud CLI, uv, keyrings-google-artifactregistry-auth, then `uv pip install --system --no-cache-dir --no-sources -e .`.                                                               |
| UTL `cloudbuild.yaml` present                            | Yes — publishes wheel + Docker base image on push to `live-defi-rollout`.                                                                                                                                                                                                               |
| Cloud Build trigger                                      | **Exists and fires.** `unified-trading-library-live-defi-rollout` (id `493290ef-2200-42e3-b9ba-c0d84894ed46`). Watches `^live-defi-rollout$`. `filename: cloudbuild.yaml`. Not disabled.                                                                                                 |
| Last successful `:latest` tag in AR                      | 2026-04-15T16:55:26Z. Image SHA `40fa7ab5...`.                                                                                                                                                                                                                                          |
| Commits on UTL `origin/live-defi-rollout` since then     | 20+ commits including `4da72fc0 feat: merge unified-events-interface into unified_trading_library.events`, `bf7ad8d1 feat(events): register ADAPTER_FETCH_FAILED + ADAPTER_FETCH_ANOMALY`, `b2ad7d0c feat(manifest-migrations): add UTL ManifestMigrator`, `78f96d94 feat(lifecycle)...`. |
| Recent Cloud Build runs (filter `tags:library-unified-trading-library`) | **Every build since 2026-04-20 18:08 has FAILED.** 2026-04-22T00:38 `bf7ad8d1` WORKING (not yet finished at Phase 0 time). 2026-04-21T20:56 `74757e88` FAILURE. 2026-04-21T12:16 `78f96d94` FAILURE. 2026-04-21T03:00 `6be6fc1a` FAILURE. 2026-04-21T02:43 `258c6e0b` FAILURE. 2026-04-20T22:46 `a7d8a489` FAILURE. 2026-04-20T19:31 `7b01f8b2` FAILURE. 2026-04-20T19:28 `613fe77d` FAILURE. 2026-04-20T19:27 `4ee91009` FAILURE. 2026-04-20T18:08 `cd96d9fb` FAILURE. |
| Root-cause error (from failed build `8244328b` log tail) | `Step #11 "build-base-image": RUN uv pip install --system --no-cache-dir --no-sources -e .` fails with: `× No solution found when resolving dependencies: Because unified-api-contracts was not found in the package registry and unified-trading-library==0.3.167 depends on unified-api-contracts>=0.1.0,<1.0.0, we can conclude that unified-trading-library==0.3.167 cannot be used.` |
| UAC wheel in AR                                          | Stale. `0.1.20` (2026-04-02T00:57:13) and `0.2.38` (2026-03-12). Nothing newer. Current `unified-api-contracts/pyproject.toml` still declares `version = "0.1.20"` — so semver-agent has NOT bumped UAC in 20+ days on this branch.                                                     |
| UTL wheel in AR                                          | Stale. `0.3.167` (2026-04-02T01:19:22) and `0.3.191` (2026-03-13). Current `unified-trading-library/pyproject.toml` declares `version = "0.3.167"` — same version, 20+ commits of new source → Cloud Build's `publish-python` step is idempotent (same version + same commit-SHA range), but the wheel content is incomplete for downstream. |
| UAC Cloud Build trigger                                  | `unified-api-contracts-live-defi-rollout` exists and fires. UAC builds may be failing for a similar reason — confirm in Phase 0.                                                                                                                                                        |
| Blast radius — services using UTL base image             | 25 active service Dockerfiles. Confirmed list in pre-audit manifest below.                                                                                                                                                                                                              |

### What actually needs fixing (narrowed scope)

The failing Dockerfile step is:

```dockerfile
# line 85
RUN uv pip install --system --no-cache-dir --no-sources -e .
```

`--no-sources` is correct (the adjacent-repo `tool.uv.sources` paths don't exist in a single-repo Docker build context),
but without sources uv MUST resolve `unified-api-contracts>=0.1.0,<1.0.0` from the configured `EXTRA_PYTHON_INDEX_URL`.
`cloudbuild.yaml` step `build-base-image` does pass `--build-arg EXTRA_PYTHON_INDEX_URL="<token-embedded-AR-URL>"`, but
the build FAILS at this step — meaning one of:

1. **AR OAuth2 token expiry**: `gcloud auth print-access-token` tokens live ~1 hour. If the cloudbuild step
   `auth-ar` runs early and `build-base-image` starts > 1h later after quality-gates, the token embedded in
   `EXTRA_PYTHON_INDEX_URL` expires inside the Docker build.
2. **uv + extra-index-url interaction with `--no-sources`**: When `--no-sources` is passed, uv does not re-read
   `[tool.uv.sources]` AT ALL, so it relies on the extra-index. If `EXTRA_PYTHON_INDEX_URL` is empty (or the
   `pip.conf` write at Dockerfile line 70-72 silently produces no-op because uv doesn't read pip.conf), uv sees no
   secondary index and fails the resolution.
3. **UAC wheel version mismatch**: even if auth works, AR only has UAC `0.1.20` and `0.2.38`. The UTL pyproject pin
   `>=0.1.0,<1.0.0` SHOULD accept `0.1.20`. So this is less likely the failure mode — but worth verifying by
   checking if the pin has moved to `>=0.2.0` on some recent commit.

**Most likely root cause: (1) token expiry or (2) uv not respecting `EXTRA_PYTHON_INDEX_URL` as pip would.** A clean
fix is to copy the repo's own UAC sibling into `.deps/unified-api-contracts/` BEFORE the `COPY . .` + install, the same
way the AWS CodeBuild path already does (Dockerfile line 79-80), so the build is self-sufficient and doesn't depend on
AR network calls at all.

### Related orthogonal issues (flagged here, owned by sibling plans — not in Plan 13 scope)

1. **Cloud Workflow polling bug**: `check_features` step uses `"completionTime" in body` which is always truthy even
   when the Cloud Run Job exited(1). Must switch to `int(succeededCount) > 0` or `int(failedCount) == 0`. Sibling plan:
   `cloud_workflow_completion_polling_fix_2026_04_22` (to be authored).
2. **`cloudbuild.yaml` template assumes sibling PM repo** (`clone-pm-scripts` step clones unified-trading-pm). Already
   handled cleanly; no fix needed here.
3. **`--force` cross-service duplicate argparse declarations** — UTL `ServiceBootstrap` owns `--force`; every service
   that re-declares it needs cleanup. Sibling plan: `service_cli_force_flag_consolidation_2026_04_22` (to be authored).
4. **Plan 12 `deployment_service_build_infrastructure_repair`** — 6 Dockerfile/cloudbuild.yaml bugs blocking all
   deployment-service Cloud Builds since 2026-02-20. Orthogonal blocker for sports-scheduler; tracked separately.

### Pre-audit manifest — downstream consumers (blast radius for the rebuild)

Every service whose Dockerfile `FROM`s the UTL base image. A rebuild of `:latest` fixes all 25 in one shot (next build
of each service pulls the new base).

| Repo                                | Dockerfile path                       | Notes                                                                                          |
| ----------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------- |
| features-sports-service             | `Dockerfile`                          | Cloud Run Job. Active witness — D2+D3 deployed 2026-04-22T00:30Z, ImportError on first run.    |
| features-onchain-service            | `Dockerfile`                          | Active witness — daily workflow failing.                                                        |
| features-calendar-service           | `Dockerfile`                          |                                                                                                |
| features-commodity-service          | `Dockerfile`                          |                                                                                                |
| features-cross-instrument-service   | `Dockerfile`                          |                                                                                                |
| features-delta-one-service          | `Dockerfile`                          |                                                                                                |
| features-volatility-service         | `Dockerfile`                          |                                                                                                |
| features-multi-timeframe-service    | `Dockerfile`                          |                                                                                                |
| instruments-service                 | `Dockerfile`                          |                                                                                                |
| market-tick-data-service            | `Dockerfile`                          |                                                                                                |
| market-data-processing-service      | `Dockerfile`                          |                                                                                                |
| execution-service                   | `Dockerfile`                          |                                                                                                |
| strategy-service                    | `Dockerfile`                          |                                                                                                |
| trading-agent-service               | `Dockerfile`                          |                                                                                                |
| ml-inference-service                | `Dockerfile`                          |                                                                                                |
| ml-training-service                 | `Dockerfile`                          |                                                                                                |
| position-balance-monitor-service    | `Dockerfile`                          |                                                                                                |
| risk-and-exposure-service           | `Dockerfile`                          |                                                                                                |
| pnl-attribution-service             | `Dockerfile`                          |                                                                                                |
| batch-live-reconciliation-service   | `Dockerfile`                          |                                                                                                |
| fund-administration-service         | `Dockerfile`                          |                                                                                                |
| client-reporting-api                | `Dockerfile`                          |                                                                                                |
| deployment-api                      | `Dockerfile`                          |                                                                                                |
| deployment-service                  | `Dockerfile` (line 33)                | Multi-stage. `sports-scheduler` stage (line 117) inherits UTL base. Also needs Plan 12 repair. |
| alerting-service                    | `cloudbuild.yaml` (Dockerfile absent in grep — verify in Phase 0) | Confirm Dockerfile path.                              |

## Phased Execution DAG

```
Phase 0 (archaeology)
  ├─ p0-archaeology (solo — confirm Phase-0 findings, check WORKING build outcome)
  │
  └─► Phase 1 (build-pipeline fix)
        ├─ p1-dockerfile-fix (SEQUENTIAL on Phase 0 — fix uv pip install failure)
        ├─ p1-cloudbuild-fix (SEQUENTIAL on Phase 0 — refresh AR token inside docker step OR add .deps copy)
        │
        └─► Phase 2 (rebuild + push)
              ├─ p2-trigger-rebuild (push a trivial chore commit OR manual trigger)
              ├─ p2-verify-new-image (gcloud artifacts docker images list)
              │
              └─► Phase 3 (downstream smoke)
                    ├─ p3-smoke-features-sports (gcloud run jobs execute) — PARALLEL
                    ├─ p3-smoke-features-onchain (daily workflow manual trigger) — PARALLEL
                    │
                    └─► Phase 4 (flip dependent plan checkboxes)
                          ├─ p4-plan-6-flip (features_sports_pipeline_deployment Phase 3/4 todos) — PARALLEL
                          ├─ p4-plan-3-confirm (sports-scheduler independence from UTL base) — PARALLEL
                          │
                          └─► Phase 5 (optional — prevent drift)
                                └─ p5-automate-autotrigger-health (monitor dashboard OR GHA badge)
```

## Phases

### Phase 0 — Archaeology [SOLO]

- [ ] [AGENT] P0. Verify the running Cloud Build for commit `bf7ad8d1` (build id
      `63a2611c-f9b7-4a89-9b36-86204d06d593`) succeeded or failed. Command:
      `gcloud builds describe 63a2611c-f9b7-4a89-9b36-86204d06d593 --project=central-element-323112
      --format='value(status,finishTime)'`. If it succeeded, Phase 1 becomes no-op and jump to Phase 2 verification.
      Otherwise tail the log: `gcloud builds log 63a2611c-f9b7-4a89-9b36-86204d06d593 --project=central-element-323112
      2>&1 | tail -100` to confirm the same root-cause.

- [ ] [AGENT] P0. Check UAC build history on `live-defi-rollout` the same way:
      `gcloud builds list --project=central-element-323112 --filter='tags:library-unified-api-contracts'
      --sort-by=~createTime --limit=8`. If UAC builds are ALSO failing, Plan 13 scope expands to fix UAC build first
      (required upstream of UTL). If UAC builds succeed but the wheel version has not been bumped past `0.1.20`, note
      that semver-agent is not firing on `live-defi-rollout` — which is actually expected (semver-agent bumps on merge
      to main, not on feature-branch pushes). This is NOT a bug; UTL + UAC wheels only get republished when the PR
      lands on main. Plan 13 can proceed regardless — the Docker base image does NOT depend on wheels being published,
      only on the Dockerfile self-install succeeding.

- [ ] [AGENT] P0. Confirm the blast-radius table above by grepping:
      `grep -l 'unified-trading-library:latest' */Dockerfile */cloudbuild.yaml 2>&1 | sort`.

### Phase 1 — Fix the Dockerfile / cloudbuild.yaml so `uv pip install -e .` resolves UAC inside the container [SEQUENTIAL on Phase 0]

Pick the cleanest fix from these candidates (in order of preference):

**Option A (preferred) — copy UAC source into Docker context via cloudbuild step**:

Mirror the AWS CodeBuild pattern (Dockerfile line 79-80 already supports `/app/.deps/unified-api-contracts`). Add a
Cloud Build step BEFORE `build-base-image` that clones or copies the UAC repo into `/workspace/.deps/`:

```yaml
- name: "gcr.io/google.com/cloudsdktool/cloud-sdk:alpine"
  id: "clone-uac-source"
  entrypoint: "bash"
  args:
    - "-c"
    - |
      set -e
      GH_PAT=$$(gcloud secrets versions access latest --secret=GH_PAT --project=$PROJECT_ID 2>/dev/null || echo "")
      mkdir -p /workspace/.deps
      git clone --depth=1 --branch live-defi-rollout \
        "https://$$GH_PAT@github.com/IggyIkenna/unified-api-contracts.git" \
        /workspace/.deps/unified-api-contracts
  waitFor: ["-"]
```

Then ensure `build-base-image` uses this: copy `.deps/` into the Docker build context (already done — it's part of
`.`, just confirm no `.dockerignore` excludes it).

- [ ] [AGENT] P0. Add the `clone-uac-source` step to `unified-trading-library/cloudbuild.yaml` BEFORE
      `build-base-image`. Add `.deps` to `build-base-image`'s `waitFor` list. Verify `.dockerignore` (if present) does
      NOT exclude `.deps/`.

- [ ] [AGENT] P0. Confirm Dockerfile line 79-80 will pick it up:
      `if [ -d /app/.deps/unified-api-contracts ]; then uv pip install --system --no-cache-dir -e /app/.deps/unified-api-contracts; fi`.
      This installs UAC FIRST (in editable mode from local path), so the subsequent `uv pip install -e . --no-sources`
      finds UAC already installed in the system Python.

**Option B (fallback) — refresh AR token inside the docker step**: If Option A is blocked by GH_PAT secret access,
move the `gcloud auth print-access-token` call INTO the `build-base-image` step so the token is fresh:

```yaml
- name: "gcr.io/cloud-builders/docker"
  id: "build-base-image"
  entrypoint: "bash"
  args:
    - "-c"
    - |
      set -e
      TOKEN=$$(gcloud auth print-access-token)
      AR_URL="https://oauth2accesstoken:$${TOKEN}@asia-northeast1-python.pkg.dev/$PROJECT_ID/unified-libraries/simple/"
      docker build -f Dockerfile \
        --build-arg EXTRA_PYTHON_INDEX_URL="$${AR_URL}" \
        -t asia-northeast1-docker.pkg.dev/$PROJECT_ID/unified-trading-library/unified-trading-library:latest \
        .
```

But this still relies on uv honouring `EXTRA_PYTHON_INDEX_URL` under `--no-sources` — which is the suspected latent
issue. Prefer Option A.

- [ ] [AGENT] P0. If Option A proves infeasible: refactor `build-base-image` step to mint a fresh token inline.
      Dockerfile remains unchanged.

### Phase 2 — Rebuild + push [SEQUENTIAL on Phase 1]

- [ ] [AGENT] P0. Commit the cloudbuild.yaml change via quickmerge (surgical
      `git add unified-trading-library/cloudbuild.yaml`). Autotrigger fires on push. Monitor:
      `gcloud builds list --project=central-element-323112 --ongoing --filter='tags:library-unified-trading-library'`.

- [ ] [AGENT] P0. On success, confirm new `:latest` tag in AR with current commit SHA:
      `gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library
      --include-tags --sort-by=~UPDATE_TIME --limit=3 --project=central-element-323112`. The `:latest` row's
      `CREATE_TIME` must be later than 2026-04-22 with today's commit SHA.

- [ ] [AGENT] P0. **Fail-loud verify** — run the old failing import inside a fresh container pull:
      `docker pull asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library:latest &&
       docker run --rm asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library:latest
       -c "from unified_trading_library.core.client_factory import get_storage_client; print('OK')"`. Must print `OK`.

### Phase 3 — Downstream smoke [PARALLEL after Phase 2]

- [ ] [AGENT] P0. Re-run features-sports-service Cloud Run Job:
      `gcloud run jobs execute features-sports-service-job --region=asia-northeast1 --project=central-element-323112
      --wait`. On completion inspect: `gcloud run jobs executions describe <execution-id> --region=asia-northeast1
      --format='value(status.conditions)'`. Exit-code must be 0. Also confirm at least one new `fixture_features`
      parquet was written to `gs://features-sports-<project>-...` (Plan 6 writer path).

- [ ] [AGENT] P0. Re-run features-onchain-service daily workflow:
      `gcloud workflows execute <onchain-workflow-name> --location=asia-northeast1 --project=central-element-323112`.
      Exit-code must be 0. Check the workflow's Cloud Run execution for zero ImportErrors.

- [ ] [AGENT] P1. Spot-check two more services that `FROM` the UTL base to confirm rebuild didn't accidentally break
      anything else. Suggested: `instruments-service` (heaviest user of UTL client_factory) and `execution-service`
      (heaviest user of UTL events). For each, `docker pull` the service's AR image if published post-rebuild and
      confirm it imports cleanly.

### Phase 4 — Unblock downstream plans [PARALLEL after Phase 3]

- [ ] [AGENT] P1. Flip
      `plans/active/features_sports_pipeline_deployment_2026_04_21.plan.md` Phase 3 T-1h smoke checkbox once Phase 3
      smoke above passes. (Plan 6 owns the UI verification + historical backfill VM todos — leave those to the Plan 6
      agent; Plan 13 only proves the base-image blocker is cleared.)

- [ ] [AGENT] P1. Confirm Plan 3 (`sports_scheduler_cron_activation`) does not depend on this rebuild. sports-scheduler
      is built from `deployment-service/Dockerfile` line 117 which does inherit the UTL base (line 33). **Therefore
      Plan 3 Phase 1 Cloud Run deploy IS gated on Plan 13 Phase 2 PLUS Plan 12 Dockerfile repair.** Update Plan 3
      context section to note both blockers have landed once Phase 2 succeeds.

- [ ] [AGENT] P2. Add Plan 13 cross-ref to
      `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` §12.4 noting Plans 3, 6, and any other
      Cloud Run activation plan are gated on this rebuild.

### Phase 5 — Prevent drift (optional but recommended) [SOLO after Phase 4]

- [ ] [AGENT] P2. Add a GHA badge or small monitoring cron that alerts on Telegram if the latest UTL `:latest` tag in
      AR is > 48h older than the latest `origin/live-defi-rollout` commit on UTL. Use the existing `send-telegram.sh`
      pattern from `unified-trading-pm/scripts/`. This prevents a silent 6-day drift from recurring. Place the monitor
      in `unified-trading-pm/scripts/monitors/ar-image-freshness-check.sh` + add a cron trigger.

- [ ] [AGENT] P2. Document the Cloud Build retry rhythm in
      `unified-trading-pm/codex/05-infrastructure/vm-tarball-deployment.md` as a sibling section: "Base-image freshness
      SLA — AR `:latest` MUST not drift > 48h from UTL `origin/live-defi-rollout` HEAD. Check via
      `gcloud artifacts docker images list ...`. Alert chain: Cloud Build trigger → on-fail Telegram via
      `post-build-notify.sh`." (If not yet present, add the notifier as part of this todo.)

## Success criteria (per phase gate)

- **Phase 0 gate**: Archaeology confirms or refutes the Phase-0 findings. If `bf7ad8d1` Cloud Build succeeded while we
  wrote this plan, jump to Phase 2 verify-only. If UAC builds are also failing, Plan 13 scope expands (document the
  expansion in a commit).
- **Phase 1 gate**: `unified-trading-library/cloudbuild.yaml` passes `yamllint` and Cloud Build's config validation
  (`gcloud builds submit --config=cloudbuild.yaml --no-source --dry-run` or equivalent).
- **Phase 2 gate**: New `:latest` AR image tagged with post-2026-04-22 commit SHA. `docker pull` + in-container
  `from unified_trading_library.core.client_factory import get_storage_client` works.
- **Phase 3 gate**: features-sports-service + features-onchain-service Cloud Run Jobs exit 0 with real data writes
  visible in their respective GCS output paths.
- **Phase 4 gate**: Plan 6 Phase 3 + Phase 4 checkboxes flipped (by Plan 6 agent). Plan 3 context updated.
- **Phase 5 gate**: AR freshness monitor live; alert fires if drift > 48h.

## Orthogonal follow-up plans (flagged for operator — not Plan 13's scope)

1. `cloud_workflow_completion_polling_fix_2026_04_22` — fix `"completionTime" in body` → `int(failedCount) == 0`.
   Blocks: future silent-success-masks-failure across every Cloud Workflow using the same polling pattern.
2. `service_cli_force_flag_consolidation_2026_04_22` — UTL `ServiceBootstrap` owns `--force`; services re-declaring it
   duplicate argparse. Blocks: confusing double-definition errors when a new service copies a launcher template.
3. `ar_image_freshness_monitor_2026_04_22` — if Phase 5 above is deferred, spin it into its own small plan so the
   monitor lands regardless of Plan 13's completion scope.

## Notes

- Do NOT bump `unified-trading-library/pyproject.toml` version manually. The semver-agent handles version bumps on
  merge to main. This plan's fix is a pure infrastructure repair; no feature semantics change.
- `cloudbuild.yaml` edits on UTL land via the standard quickmerge flow against `live-defi-rollout`. The trigger watches
  that branch, so the push itself re-kicks the pipeline.
- If the `clone-uac-source` step fails because GH_PAT secret is not available in the UTL Cloud Build service account,
  switch to a GCS-backed source bundle: operator uploads the UAC source tarball to
  `gs://deployment-scripts-<project>/code/unified-api-contracts.tar.gz` (same pattern as VM tarballs), and the
  cloudbuild step `gsutil cp` + untars. This is the same "tarball deployment" muscle the VM side already uses.
