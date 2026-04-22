---
name: deployment-service-build-infrastructure-repair
overview: Repair deployment-service Dockerfile + cloudbuild.yaml so Cloud Build ships a fresh deployment-dashboard image for the first time since 2026-02-20, unblocking Plan 3 (sports-scheduler cron) and Plan 6 (features-sports-service deployment).
priority: P0
status: active
owner: agent
created: 2026-04-22
locked_by: live-defi-rollout
locked_since: 2026-04-22
type: infra
epic: epic-deployment
completion_gates:
  code: C5
  deployment: D2
  business: none
repo_gates:
  - repo: deployment-service
    code: C0
    deployment: D0
    business: none
depends_on: []
todos:
  - id: p0-archaeology
    content: |
      - [ ] [AGENT] P0. Phase 0 archaeological audit — fact-find the blast radius BEFORE touching the Dockerfile. SEQUENTIAL — all later phases depend on this.
        - Confirm `ui/`, `api/`, `backends/`, `deployment/` dirs NEVER existed at deployment-service repo root:
          `cd deployment-service && git log --all --diff-filter=A --name-status -- 'api/' 'ui/' 'backends/' 'deployment/'`
          (Pre-audit already confirmed: returns empty. These COPY lines are aspirational — the Python package at `deployment_service/` has api/, backends/, deployment/ SUBDIRS; the Dockerfile is mis-pathed.)
        - Confirm `deployment_service/api/main.py` exists (it does) + locate the actual gunicorn `app` entrypoint. Dockerfile currently CMD's `gunicorn api.main:app -c /app/api/gunicorn.conf.py` — but `api/gunicorn.conf.py` does not exist anywhere in the repo (`find . -name gunicorn*` only finds the .venv copy). The sibling `deployment-api/gunicorn.conf.py` exists at deployment-api repo root — confirm whether deployment-service should vendor its own gunicorn conf or reuse deployment-api's image.
        - Resolve the LIVE image question: `gcloud run services describe deployment-dashboard --region=asia-northeast1 --format='value(spec.template.spec.containers[0].image)'` — which SHA is currently serving, and does its docker inspect match the current Dockerfile structure or the old one? (Expect 2026-02-20 SHA per D1 report.)
        - Inspect Artifact Registry tag history: `gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/${PROJECT_ID}/deployment-dashboard/deployment-dashboard --format='table(tags,updateTime)' --sort-by=~updateTime` — confirm the 2026-02-20 gap in fresh tags.
        - Read `deployment-service/pyproject.toml [project.scripts]` — entry point is `deploy-shards = "deployment_service.cli.main:main"`. NOT the FastAPI dashboard. Dashboard app lives at `deployment_service/api/main.py`. FastAPI app variable must be confirmed by `grep -n "^app = FastAPI" deployment_service/api/main.py`.
        - Check whether the live deployment-dashboard Cloud Run image was built from a PREVIOUS Dockerfile shape (pre-scaffold drift). If yes, the correct action is NOT "restore the old dirs" but "fix the Dockerfile to match reality."
        - Produce PHASE-0-FINDINGS table embedded in the plan body matching PRE-AUDIT pattern (see sports_scheduler_periodic_tier_dispatch plan for shape).
    status: todo
  - id: p1-dockerfile-repair
    content: |
      - [ ] [AGENT] P1. Phase 1 — Repair the Dockerfile. Blocked on Phase 0.
        - **BUG-1a**: Lines 22-27 — `COPY ui/package*.json` and `COPY ui/` assume a sibling `ui/` source tree at repo root. It doesn't exist and never existed. The deployment UI lives in the **sibling repo `deployment-ui/`** (confirmed present), NOT inside deployment-service. Decision: DROP Stage 1 (`ui-builder`). The dashboard's UI is served from deployment-ui's own Cloud Run service / Artifact Registry image; deployment-service serves only the orchestration API. If the UI must be co-served, the pattern is a multi-repo Docker build context (out of scope for Plan 12 — open a follow-up plan).
        - **BUG-1b**: Line 74 `COPY --from=ui-builder /app/ui/dist ./ui/dist` — delete along with Stage 1.
        - **BUG-2**: Line 63 `RUN uv sync --frozen --no-dev --system` — current uv (>=0.11) removed `--system` from `uv sync`. Mirror the shipped features-sports-service pattern: `RUN uv pip install --system --no-deps -e .` (UTL base image already has transitive deps pre-installed). Also applies to the api-dev stage line 101 — same fix.
        - **BUG-3**: Lines 68-71 — `COPY api/ backends/ deployment/ configs/` reference repo-ROOT paths that don't exist. Actual layout is `deployment_service/api/`, `deployment_service/backends/`, `deployment_service/deployment/`, plus `configs/` at repo root (that one IS correct). Replace with `COPY deployment_service/ ./deployment_service/` (already on line 67, so lines 68-70 become no-ops — delete them). Keep line 71 `COPY configs/ ./configs/` (configs/ exists at repo root).
        - **BUG-4**: Line 92 `CMD ["gunicorn", "api.main:app", "-c", "/app/api/gunicorn.conf.py"]` — two compounding errors: (a) module path `api.main:app` should be `deployment_service.api.main:app`, (b) config path `/app/api/gunicorn.conf.py` doesn't exist. Fix: create `deployment_service/api/gunicorn.conf.py` (mirror sibling `deployment-api/gunicorn.conf.py` — 2 workers, gevent class, timeout 300, port 8080), OR bundle it at repo root and COPY it explicitly. Preferred: vendor into `deployment_service/api/gunicorn.conf.py` so it's in the already-COPY'd package. Update CMD to `["gunicorn", "deployment_service.api.main:app", "-c", "/app/deployment_service/api/gunicorn.conf.py"]`.
        - **BUG-5**: Nested docker-in-docker UAC pull via `keyrings.google-artifactregistry-auth` — the UTL base image already carries `unified-api-contracts` + `unified-trading-library` pre-installed (per the `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest` contract). `--no-deps` on the `uv pip install -e .` respects this: no keyring needed, ADC stays in Cloud Build's outer context. Confirm no lingering `keyrings.*` references survive.
        - Post-edit, `cat Dockerfile` and eyeball: 4 stages intact (`base` → `api` → `api-dev` → `sports-scheduler`), no dead COPY lines, CMD resolvable from the Python package layout.
    status: todo
  - id: p2-cloudbuild-repair
    content: |
      - [ ] [AGENT] P2. Phase 2 — Repair cloudbuild.yaml. Blocked on Phase 0, PARALLEL with Phase 1.
        - **BUG-6**: Lines 225-235 heredoc uses `$IMAGE` and `$RESULT` inside `gcr.io/cloud-builders/gcloud` entrypoint bash — Cloud Build's substitution engine will try to expand `$IMAGE` as a substitution variable at yaml-parse time and fail (no such substitution defined). Escape as `$$IMAGE` / `$$RESULT` so the literal `$` reaches bash. Also the placeholder `asia-northeast1-docker.pkg.dev/$PROJECT_ID/UNKNOWN/UNKNOWN` on line 225 must be filled with the real image (`${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_ARTIFACT_REPO}/${_SERVICE_NAME}:${COMMIT_SHA}`) — this looks like an unfinished edit from whoever last touched the file.
        - **BUG-7**: Step 1 `configure-docker` uses `gcr.io/cloud-builders/gcloud` — this IS correct for `gcloud auth configure-docker` (the D1 report's finding that "docker builder doesn't ship gcloud" is correct but inverted — the current step already uses the gcloud builder, not docker. Verify. If actually on docker builder, migrate to gcloud builder.) Confirm by re-reading `configure-docker` step `name:` field.
        - **BUG-8**: Step 7 `deploy` uses `gcr.io/google.com/cloudsdktool/cloud-sdk` — correct for gcloud commands. No change.
        - Validate `timeout: "600s"` (10 min) vs `machineType: E2_HIGHCPU_32` — 10 min may be tight for a from-cold build with UI dropped (less work now). Post-fix, consider bumping to 1200s if first real build runs long.
        - Confirm `images:` list at bottom (lines 249-253) matches the two tags pushed: `${_SERVICE_NAME}:${COMMIT_SHA}`, `${_SERVICE_NAME}:latest`, `sports-scheduler:${COMMIT_SHA}`, `sports-scheduler:latest`.
        - Re-read top comment (lines 1-18): it claims "runs the EXACT same quality gates as Local/GHA" — quality-gates step 4 runs `scripts/quality-gates.sh --no-fix --quick` INSIDE the api-dev image. Post-repair, this must still work.
    status: todo
  - id: p3-local-smoke
    content: |
      - [ ] [AGENT] P3. Phase 3 — Local Docker build smoke. Blocked on Phase 1 + Phase 2. SEQUENTIAL.
        - Pre-flight: `docker --version` + `gcloud auth configure-docker asia-northeast1-docker.pkg.dev` so the UTL base image pulls.
        - `cd deployment-service && docker build --platform=linux/amd64 --build-arg PROJECT_ID=${GCP_PROJECT_ID:-central-element-323112} --target api -t deployment-dashboard-smoke:local .`
        - Success: exit 0, image present in `docker images | grep deployment-dashboard-smoke`.
        - Smoke-run the image ENTRY: `docker run --rm --entrypoint python deployment-dashboard-smoke:local -c "import deployment_service.api.main; print(deployment_service.api.main.app)"` — must print the FastAPI app object (not ImportError / ModuleNotFoundError).
        - Also smoke the sports-scheduler target: `docker build --target sports-scheduler -t sports-scheduler-smoke:local .` + `docker run --rm --entrypoint python sports-scheduler-smoke:local -c "import deployment_service.cli.commands.sports_trigger; print('ok')"`.
        - Tear down: `docker rmi deployment-dashboard-smoke:local sports-scheduler-smoke:local`.
        - If any step fails: diagnose root cause (module path? missing dep? broken UTL base pull?) and iterate; do NOT proceed to Phase 4 until local smoke passes.
    status: todo
  - id: p3b-qg
    content: |
      - [ ] [AGENT] P3b. Phase 3b — deployment-service Pass 1 quality gates. Blocked on Phase 1. PARALLEL with Phase 3.
        - `cd deployment-service && bash scripts/quality-gates.sh` — full run with no flags. Must exit 0.
        - Dockerfile / cloudbuild.yaml changes are plain YAML / Dockerfile edits — ruff + basedpyright don't lint them, but QG runs the Dockerfile-spec-syntax check + yaml validator if present in `scripts/quality-gates.sh`.
        - If QG fails on unrelated pre-existing codex violations (per 2026-04-21 pattern on deployment-service), apply the `git commit --no-verify` + `[QG-BYPASS: pre-existing-violation]` pattern ONLY for those lines; do not paper over Phase-1/2 bugs.
    status: todo
  - id: p4-cloud-build-smoke
    content: |
      - [ ] [AGENT] P4. Phase 4 — Cloud Build smoke. Blocked on Phase 3 AND Phase 3b passing. SEQUENTIAL.
        - Commit Phase 1 + Phase 2 changes to `live-defi-rollout` via `bash scripts/quickmerge.sh "fix(docker): repair Dockerfile + cloudbuild.yaml — drop non-existent ui/api/backends/deployment COPYs, fix uv sync --system, fix gunicorn module path + config" --agent`. Gets PR#/merge SHA.
        - Submit Cloud Build from a clean origin checkout so the build reflects the merged commit, not local working tree: `gcloud builds submit --config=cloudbuild.yaml --region=asia-northeast1 --project=${GCP_PROJECT_ID} .`
        - Expected outcome: `STATUS: SUCCESS`. All 8 steps pass: configure-docker → build → build-dev → build-sports-scheduler → quality-gates → push → push-sports-scheduler → gen-env → deploy → set-iam → scan-check.
        - Verify image landed: `gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/${GCP_PROJECT_ID}/deployment-dashboard/deployment-dashboard --sort-by=~updateTime --limit=3` — newest tag must be from TODAY, not 2026-02-20.
        - Verify sports-scheduler image: same command with `.../deployment-dashboard/sports-scheduler`. Must show two tags (`${COMMIT_SHA}`, `latest`) from today.
        - Verify Cloud Run rolled: `gcloud run services describe deployment-dashboard --region=asia-northeast1 --format='value(status.latestReadyRevisionName,spec.template.spec.containers[0].image)'` — image SHA matches today's commit; revision is Ready.
        - Log the SHA + buildId + Cloud Run revision in the plan as Phase 4 evidence.
    status: todo
  - id: p5-plan3-unblock
    content: |
      - [ ] [AGENT] P5. Phase 5 — Unblock Plan 3 (sports_scheduler_cron_activation). Blocked on Phase 4. SEQUENTIAL.
        - Read `plans/active/sports_scheduler_cron_activation_2026_04_21.plan.md` Phase 6 todos — they expect the sports-scheduler image to exist in AR.
        - Run scoped terraform apply: `cd deployment-service/terraform/gcp && terraform plan -target=google_cloud_run_v2_job.sports_scheduler -target=google_cloud_scheduler_job.sports_scheduler_cron -out=/tmp/sports-scheduler.tfplan` — must show 2 resources to add, 0 to change outside scope.
        - Apply: `terraform apply /tmp/sports-scheduler.tfplan`. Success: job + scheduler resources created.
        - Out of scope for this plan: the ~134-resource broader terraform drift (56 adds + 78 changes outside sports-scheduler scope — features buckets, strategy buckets, IAM bindings, non-sports schedulers). Flag in Phase-7 notes but DO NOT apply in Plan 12. Open a sibling plan `deployment_service_terraform_drift_remediation_2026_04_22` if the operator confirms the drift is urgent.
        - Force first scheduler fire: `gcloud scheduler jobs run sports-scheduler-cron --location=asia-northeast1`. Wait 30s.
        - Verify job success: `gcloud run jobs executions list --job=sports-scheduler --region=asia-northeast1 --limit=1 --format='value(name,completionTime,condition.state)'` — state must be `Succeeded`.
        - Flip Plan 3 Phase-6 checkboxes `[x] done` in the same quickmerge wave (PM doc-only fast-path).
    status: todo
  - id: p6-plan6-check
    content: |
      - [ ] [AGENT] P6. Phase 6 — Check whether Plan 6 (features-sports-service deployment) has the same build rot. Blocked on Phase 4. PARALLEL with Phase 5.
        - `cd features-sports-service && cat Dockerfile` — confirmed clean as of 2026-04-22 pre-audit: uses `uv pip install --system --no-deps -e .` (no `--system` on `uv sync`), no `ui/api/backends/deployment` COPYs, CMD is `python -m features_sports_service` (no gunicorn path trap). Should build fine.
        - `cd features-sports-service && cat cloudbuild.yaml` — re-audit for the same 4 bug classes (BUG-2 uv sync --system, BUG-4 gunicorn path, BUG-6 heredoc escape, BUG-1 non-existent COPYs).
        - If clean: flip this todo `[x] done` with note "features-sports-service Dockerfile + cloudbuild.yaml already follow the corrected pattern — no repair required. Plan 6 is NOT blocked on Plan 12."
        - If dirty: add specific bugs to Phase 1 + Phase 2 scope of a new plan `features_sports_service_build_infrastructure_repair_2026_04_23` (not scoped into Plan 12 — features-sports-service is a separate repo, separate `repo_gates`).
    status: todo
  - id: p7-success-criteria
    content: |
      - [ ] [AGENT] P7. Phase 7 — Validate workspace-wide success criteria. Blocked on Phase 5 AND Phase 6. SEQUENTIAL.
        - deployment-service: C5 reached (Phase 4 quickmerge landed on live-defi-rollout + merged to main via SIT).
        - deployment-service: D2 reached (Cloud Build `STATUS=SUCCESS`, fresh `deployment-dashboard:<today-SHA>` tag in AR, Cloud Run revision Ready).
        - Plan 3 reaches D3 (Cloud Run Job `sports-scheduler` exists, first Cloud Scheduler fire returns exit 0 with `condition.state=Succeeded`).
        - Confirm next scheduled Cloud Scheduler fire (≤ 5 min from Phase 5 manual fire) also succeeds — writes to `gs://deployment-scripts-${PROJECT_ID}/sports_scheduler_state/scheduler.json`.
        - Update plan frontmatter `repo_gates[deployment-service].code: C5, deployment: D2`.
        - Note terraform drift follow-up in plan body under "Out of scope" if not already captured.
        - Final report-back to orchestrator: D1's 6-Cloud-Build-failure regression closed + Plan 3 Phase 6 unblocked.
    status: todo
isProject: false
---

## Context

**D1 report (2026-04-22):** Every deployment-service Cloud Build since ~2026-02-20 has FAILED. Six submissions in
this session failed at different layers. Last successful `deployment-dashboard` AR image: 2026-02-20. Two months of
production-blocking build rot.

**Immediate consumer:** Plan 3 (`sports_scheduler_cron_activation_2026_04_21.plan.md`) Phase 6 is terraform-ready but
cannot apply — the terraform `google_cloud_run_v2_job` references a `sports-scheduler` image that would be co-pushed
with `deployment-dashboard` by the broken cloudbuild.yaml. Zero deployments possible until the pipeline is repaired.

**Six root-cause bugs** (confirmed in Phase-0-FINDINGS section below):

| # | Bug | File : Line | Evidence |
|---|-----|-------------|----------|
| 1 | `COPY ui/package*.json ./` fails — `ui/` never existed in this repo | `Dockerfile:22` | `git log --all --diff-filter=A -- 'ui/'` returns empty. Sibling repo `deployment-ui/` is the real UI. |
| 2 | `uv sync --frozen --no-dev --system` — uv>=0.11 removed `--system` from `uv sync` | `Dockerfile:63, 101` | Sibling features-sports-service (corrected 2026-04) uses `uv pip install --system --no-deps -e .`. |
| 3 | `COPY api/ backends/ deployment/` — these exist as `deployment_service/api/` etc., not at repo root | `Dockerfile:68-70` | `ls deployment-service/` shows no top-level `api/`, `backends/`, `deployment/`. `deployment_service/{api,backends,deployment}` all present. |
| 4 | `CMD gunicorn api.main:app -c /app/api/gunicorn.conf.py` — module path wrong + config file missing | `Dockerfile:92` | `deployment_service/api/main.py` exists; `api/` does not. `find . -name gunicorn*` finds only `.venv/` copies, no config file in source. |
| 5 | `$IMAGE` in heredoc unescaped + placeholder `UNKNOWN/UNKNOWN` | `cloudbuild.yaml:225` | Cloud Build substitution engine expands `$IMAGE` at yaml-parse time, fails. Also UNKNOWN/UNKNOWN is an unfinished edit. |
| 6 | Terraform drift: `terraform plan` = 56 adds + 78 changes outside Plan 3 scope | `terraform/gcp/` | Two months of code ↔ live drift. **OUT OF SCOPE** for this plan — flagged for a separate drift-remediation plan if urgent. |

**Scope fence:** Plan 12 repairs the build pipeline. Plan 12 does NOT repair the ~134-resource terraform drift — that's
a separate plan. Plan 12 does NOT repair consumer-repo Dockerfiles (features-sports-service et al.) unless Phase 6 finds
the same bugs — and even then, that work spawns a new plan scoped to those repos.

## Execution DAG

```
Phase 0 (archaeology, SEQUENTIAL — gate for everything)
    │
    ├─► Phase 1 (Dockerfile repair, PARALLEL with P2)     ─┐
    │                                                      │
    └─► Phase 2 (cloudbuild.yaml repair, PARALLEL with P1) │
                                                           │
                        ┌──────────────────────────────────┘
                        │
                        ├─► Phase 3  (local docker smoke, SEQUENTIAL)
                        │           │
                        └─► Phase 3b (deployment-service QG, PARALLEL with P3)
                                    │
                                    └──►  Phase 4 (Cloud Build SUCCESS, SEQUENTIAL)
                                                │
                                                ├─► Phase 5 (Plan 3 unblock — terraform + scheduler fire, SEQUENTIAL)
                                                │
                                                └─► Phase 6 (Plan 6 build-rot check, PARALLEL with P5)
                                                            │
                                                            └──►  Phase 7 (workspace-wide success criteria)
```

## Success criteria (per phase)

| Phase | Code gate | Deployment gate | Business gate |
|-------|-----------|-----------------|---------------|
| 0 | — | — | PHASE-0-FINDINGS table embedded in plan body |
| 1 | `ruff check Dockerfile` (via QG) pass | — | — |
| 2 | `ruff check cloudbuild.yaml` (QG yaml-lint) pass | — | — |
| 3 | `docker build --target api` exit 0 + `import deployment_service.api.main` succeeds | — | — |
| 3b | `bash scripts/quality-gates.sh` exit 0 | — | — |
| 4 | — | `gcloud builds submit` STATUS=SUCCESS + fresh AR tag today + Cloud Run Ready revision | — |
| 5 | — | `sports-scheduler` Cloud Run Job + `sports-scheduler-cron` Cloud Scheduler present + first manual fire `condition.state=Succeeded` | — |
| 6 | `features-sports-service/Dockerfile` audit done + clean-or-dirty classification | — | — |
| 7 | deployment-service `repo_gates` → `code: C5, deployment: D2`; Plan 3 → D3 | Plan 3 second cron fire (≤5 min window) writes state JSON to GCS | Plan 3 unblocked |

The final phase MUST include:

- `cd deployment-service && bash scripts/quality-gates.sh` green.
- `gcloud builds list --region=asia-northeast1 --limit=1 --format='value(status)'` returns `SUCCESS`.
- `gcloud run services describe deployment-dashboard --format='value(status.conditions[0].status)'` returns `True`.
- `gcloud scheduler jobs describe sports-scheduler-cron --location=asia-northeast1` does not return NOT_FOUND.

## Out of scope

- **Terraform drift remediation (~134 resources)** — `terraform plan` shows 56 adds + 78 changes across features
  buckets, strategy buckets, IAM bindings, non-sports schedulers. Open a sibling plan
  `deployment_service_terraform_drift_remediation_2026_04_22` if the operator confirms urgency. Plan 12 only applies
  the 2 sports-scheduler-scoped resources in Phase 5.
- **Consumer-repo Dockerfile hygiene for repos OTHER than deployment-service and features-sports-service** — out of
  scope. Plan 12 Phase 6 spot-checks features-sports-service ONLY because it's Plan 6's target.
- **UI co-serving from deployment-service** — dropping Stage 1 (`ui-builder`) is the decision. If the operator later
  wants the deployment dashboard to co-serve UI HTML from the API container (instead of fronting deployment-ui as a
  separate Cloud Run service), that requires a multi-repo Docker build context + separate plan.
- **Image version bumps for UTL base image** — the `asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`
  tag floats. If the UTL base has itself regressed on deps since 2026-02-20, that's a separate UTL-side fix.
- **`deployment-api` sibling repo Dockerfile** — has the SAME `uv sync --frozen --no-dev --system` pattern that's
  broken by uv>=0.11. Flagged as follow-up `deployment_api_build_infrastructure_repair_2026_04_23` if deployment-api
  Cloud Build is also failing. Verify in Phase 6.

## Cross-references

- **Plan 3** (`sports_scheduler_cron_activation_2026_04_21.plan.md`) depends on Phase 4 of this plan landing. Plan 3
  Phase 6 is the first plan to actually exercise a fresh deployment-service image in 2+ months.
- **Plan 6** (`features_sports_pipeline_deployment_2026_04_21.plan.md`) may depend on Phase 6 of this plan —
  features-sports-service Cloud Build status confirms or refutes.
- **PLAN_FORMAT.md** § Citadel-Grade Planning Standards — this plan follows the pre-audit / phased-DAG / success-criteria
  structure.
- **Codex `02-data/sports-scheduling-and-sharding.md` §12.0** — register entry added for this plan (see commit wave).
- **D1 sub-agent report** (2026-04-22 session) — source of the 6-Cloud-Build-failure audit trail that motivated this
  plan.

## Phase-0-FINDINGS (populate during Phase 0 execution)

| Item | Finding | Action |
| ---- | ------- | ------ |
| `ui/` / `api/` / `backends/` / `deployment/` at repo root | **CONFIRMED NEVER EXISTED.** `git log --all --diff-filter=A -- 'ui/' 'api/' 'backends/' 'deployment/'` returns empty. Actual layout: `deployment_service/{api,backends,deployment}/` subpackages; `configs/` at repo root (correct). | DROP `ui-builder` stage; delete `COPY api/ backends/ deployment/` lines; keep `COPY configs/`. |
| `uv sync --system` compatibility | **BROKEN with uv >= 0.11.** features-sports-service Dockerfile (2026-04 corrected) uses `uv pip install --system --no-deps -e .` — copy that pattern. | Replace both `uv sync --frozen --no-dev --system` lines. |
| `gunicorn.conf.py` location | **MISSING from source.** Sibling `deployment-api/gunicorn.conf.py` exists at repo root; no equivalent in deployment-service. `deployment_service/api/main.py` exists. | Vendor into `deployment_service/api/gunicorn.conf.py` (copy sibling's shape); update CMD to `deployment_service.api.main:app -c /app/deployment_service/api/gunicorn.conf.py`. |
| Live `deployment-dashboard` image | To capture in Phase 0: `gcloud run services describe deployment-dashboard --format='value(spec.template.spec.containers[0].image)'`. Expected: SHA from 2026-02-20 build. | Confirm image age = gap evidence. |
| `cloudbuild.yaml:225` heredoc | **BOTH** unescaped `$IMAGE`/`$RESULT` **AND** placeholder `UNKNOWN/UNKNOWN`. | Escape to `$$IMAGE` / `$$RESULT`; replace UNKNOWN with `${_ARTIFACT_REPO}/${_SERVICE_NAME}:${COMMIT_SHA}`. |
| Terraform drift | `terraform plan` in `deployment-service/terraform/gcp/` expected to show 56 adds + 78 changes. | OUT OF SCOPE — Plan 12 only `-target`s the 2 sports-scheduler resources. Spawn drift-remediation plan if urgent. |

## Notes

- **Plan is locked** (`locked_by: live-defi-rollout`, `locked_since: 2026-04-22`) — archival requires `[unlock-plan]`
  per §9a of SUB_AGENT_MANDATORY_RULES.md.
- **Agent unlock protocol:** when all phases pass, ask the human to unlock. Do NOT unlock autonomously.
- **Rollback posture:** the Phase-4 Cloud Build is destructive only insofar as it pushes a new `:latest` tag. The
  previous 2026-02-20 tag remains in AR; `gcloud run services update-traffic deployment-dashboard --to-tags=<old-sha>=100`
  reverts the serving revision if the new image regresses at runtime. Terraform Phase 5 is additive (new resources
  only, no destructive changes).
- **Commit discipline:** Phase 1 + Phase 2 share a quickmerge wave (`fix(docker):` + `fix(cloudbuild):` combined).
  Phase 5 terraform apply is manual / operator-gated — Phase 5 checkbox flip commits to PM only.
