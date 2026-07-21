---
doc_type: plan
title: deployment-service-build-infrastructure-repair
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-22
overview:
  Repair deployment-service Dockerfile + cloudbuild.yaml so Cloud Build ships a fresh deployment-dashboard image for the
  first time since 2026-02-20, unblocking Plan 3 (sports-scheduler cron) and Plan 6 (features-sports-service
  deployment).
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-22
type: infra
epic: epic-deployment
completion_gates: { code: C5, deployment: D2, business: none }
repo_gates:
  - { repo: deployment-service, code: C0, deployment: D0, business: none }
depends_on: []
todos: []
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Verified 2026-07-21 (batch-5 archived-plan discipline triage): all 5 open items'
underlying goals were independently achieved via later, more comprehensive work — P5 (sports-scheduler Cloud Run
unblock) via `plans/active/issues/sports_trigger_scheduler_cloud_dispatch_broken_2026_07_08.md` (resolved, per-service
Cloud Run Jobs); P4 (deployment-service Cloud Build health) via
`plans/active/test_fleet_image_builds_from_current_code_2026_06_17.md` (active, GCP+AWS build parity established); P6
(features-sports-service build-rot) superseded by
`plans/active/features_sports_service_consolidation_deploy_2026_07_15.md`. P3/P7 are downstream gates of P4-P6, moot for
the same reasons.

## Context

**D1 report (2026-04-22):** Every deployment-service Cloud Build since ~2026-02-20 has FAILED. Six submissions in this
session failed at different layers. Last successful `deployment-dashboard` AR image: 2026-02-20. Two months of
production-blocking build rot.

**Immediate consumer:** Plan 3 (`sports_scheduler_cron_activation_2026_04_21.md`) Phase 6 is terraform-ready but cannot
apply — the terraform `google_cloud_run_v2_job` references a `sports-scheduler` image that would be co-pushed with
`deployment-dashboard` by the broken cloudbuild.yaml. Zero deployments possible until the pipeline is repaired.

**Six root-cause bugs** (confirmed in Phase-0-FINDINGS section below):

| #   | Bug                                                                                                 | File : Line           | Evidence                                                                                                                                    |
| --- | --------------------------------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `COPY ui/package*.json ./` fails — `ui/` never existed in this repo                                 | `Dockerfile:22`       | `git log --all --diff-filter=A -- 'ui/'` returns empty. Sibling repo `deployment-ui/` is the real UI.                                       |
| 2   | `uv sync --frozen --no-dev --system` — uv>=0.11 removed `--system` from `uv sync`                   | `Dockerfile:63, 101`  | Sibling features-sports-service (corrected 2026-04) uses `uv pip install --system --no-deps -e .`.                                          |
| 3   | `COPY api/ backends/ deployment/` — these exist as `deployment_service/api/` etc., not at repo root | `Dockerfile:68-70`    | `ls deployment-service/` shows no top-level `api/`, `backends/`, `deployment/`. `deployment_service/{api,backends,deployment}` all present. |
| 4   | `CMD gunicorn api.main:app -c /app/api/gunicorn.conf.py` — module path wrong + config file missing  | `Dockerfile:92`       | `deployment_service/api/main.py` exists; `api/` does not. `find . -name gunicorn*` finds only `.venv/` copies, no config file in source.    |
| 5   | `$IMAGE` in heredoc unescaped + placeholder `UNKNOWN/UNKNOWN`                                       | `cloudbuild.yaml:225` | Cloud Build substitution engine expands `$IMAGE` at yaml-parse time, fails. Also UNKNOWN/UNKNOWN is an unfinished edit.                     |
| 6   | Terraform drift: `terraform plan` = 56 adds + 78 changes outside Plan 3 scope                       | `terraform/gcp/`      | Two months of code ↔ live drift. **OUT OF SCOPE** for this plan — flagged for a separate drift-remediation plan if urgent.                  |

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

## Phases

### Phase 0 — Archaeology [SOLO]

- [x] [AGENT] P0. (`p0-archaeology`) Phase 0 archaeological audit — fact-find the blast radius BEFORE touching the
      Dockerfile. SEQUENTIAL — all later phases depend on this. **2026-04-25 sub-agent confirmation:** `ui/`, `api/`,
      `backends/`, `deployment/` directories DO NOT EXIST at deployment-service repo root (verified via `ls -d`).
      `deployment_service/{api,backends,deployment}/` subpackages all exist; `configs/` exists at repo root.
      `deployment_service/api/main.py` defines `app = create_app()` at line 43 (factory pattern — gunicorn imports the
      module and grabs the `app` attribute, which is fine). `deployment-api/gunicorn.conf.py` exists in sibling repo;
      `deployment_service/api/gunicorn.conf.py` was already vendored at commit `d19a969 chore: sync workspace changes`.

### Phase 1 — Dockerfile repair [PARALLEL with Phase 2]

- [x] [AGENT] P1. (`p1-dockerfile-repair`) Phase 1 — Repair the Dockerfile. Blocked on Phase 0. **2026-04-25 commit
      `3f09f52` on `live-defi-rollout` (deployment-service):** BUG-1a (drop `ui-builder` Stage 1) ✓; BUG-1b (drop
      `COPY --from=ui-builder`) ✓; BUG-2 (`uv sync --system` → `uv pip install --system --no-deps -e .` on both `api`
      and `api-dev` stages) ✓; BUG-3 (drop `COPY api/ backends/ deployment/`, keep `COPY configs/`) ✓; BUG-4 (CMD →
      `gunicorn deployment_service.api.main:app -c /app/deployment_service/api/gunicorn.conf.py`) ✓; BUG-5 (no
      keyrings.\* references survive — UTL base image carries UAC + UTL + transitive deps) ✓. 3 stages intact: `base` →
      `api` → `api-dev` → `sports-scheduler`. Dockerfile diffstat 49 lines changed (15 ins / 34 del).

### Phase 2 — cloudbuild.yaml repair [PARALLEL with Phase 1]

- [x] [AGENT] P2. (`p2-cloudbuild-repair`) Phase 2 — Repair cloudbuild.yaml. Blocked on Phase 0, PARALLEL with Phase 1.
      **2026-04-25 commit `3f09f52` on `live-defi-rollout` (deployment-service):** BUG-6 (heredoc
      `$IMAGE`/`$RESULT`/`$i` → `$$IMAGE`/`$$RESULT`/`$$i`; replaced `UNKNOWN/UNKNOWN` placeholder with
      `${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_ARTIFACT_REPO}/${_SERVICE_NAME}:${COMMIT_SHA}`) ✓. BUG-7
      (`configure-docker` already on `gcr.io/cloud-builders/gcloud` — correct, no change) ✓. BUG-8 (`deploy` step on
      `gcr.io/google.com/cloudsdktool/cloud-sdk` — correct, no change) ✓. `images:` list unchanged (4 tags). cloudbuild
      diffstat 20 lines changed (10 ins / 10 del). QG STEP 5.17 (cloudbuild.yaml structure validation) PASSED.

### Phase 3 — Local docker smoke [SEQUENTIAL after Phase 1+2]

- [ ] [AGENT] P3. (`p3-local-smoke`) Phase 3 — Local Docker build smoke. Blocked on Phase 1 + Phase 2. SEQUENTIAL.
      **2026-04-25 sub-agent: SKIPPED.** Local docker is available (Docker version 28.5.1), but a local build pulls the
      `unified-trading-library:latest` AR base image which still has the stale `client_factory` ImportError on this
      branch (Plan 13 Phase 2 cloudbuild rebuild not yet triggered by operator). Smoke would fail at runtime in a way
      that does not exercise the Dockerfile fix. Operator should re-run Phase 3 AFTER Plan 13 Phase 2 produces a fresh
      UTL base image.

### Phase 3b — deployment-service QG [PARALLEL with Phase 3]

- [x] [AGENT] P3b. (`p3b-qg`) Phase 3b — deployment-service Pass 1 quality gates. Blocked on Phase 1. **2026-04-25:**
      Ran `bash scripts/quality-gates.sh`. cloudbuild.yaml structure (STEP 5.17) PASSED. Pre-existing failures NOT
      caused by Phase 1+2 changes: STEP 5.10 (`gcp_instance_lister.py` direct cloud SDK import — pre-existing),
      pip-audit vulnerabilities (pre-existing), codex-compliance count exceeded (7 vs max 4 — pre-existing). Commit
      landed via `--no-verify` with `[QG-BYPASS: pre-existing-violations]` per the explicit instruction in `p3b-qg`.
      Surgical scope: 2 files (Dockerfile + cloudbuild.yaml).

### Phase 4 — Cloud Build smoke [OPERATOR-GATED]

- [ ] [AGENT] P4. (`p4-cloud-build-smoke`) Phase 4 — Cloud Build smoke. Blocked on Phase 3 AND Phase 3b passing.
      SEQUENTIAL. **OPERATOR-GATED.** Sub-agent does NOT submit Cloud Build. Operator command (after Plan 13 Phase 2
      ships a fresh UTL base image):
      `cd deployment-service && gcloud builds submit --config=cloudbuild.yaml --region=asia-northeast1 --project=central-element-323112 .`
      Expected: STATUS=SUCCESS; fresh `deployment-dashboard:${COMMIT_SHA}` + `sports-scheduler:${COMMIT_SHA}` tags in
      AR; Cloud Run revision Ready.

### Phase 5 — Plan 3 unblock (terraform + scheduler) [OPERATOR-GATED]

- [ ] [AGENT] P5. (`p5-plan3-unblock`) Phase 5 — Unblock Plan 3 (sports_scheduler_cron_activation). Blocked on Phase 4.
      **OPERATOR-GATED.** Scoped terraform apply against `terraform/gcp/` for the 2 sports-scheduler resources only;
      manual scheduler fire; verify `condition.state=Succeeded`. Flip Plan 3 Phase-6 checkboxes via PM doc-only
      fast-path quickmerge.

### Phase 6 — Plan 6 build-rot check [PARALLEL with Phase 5]

- [ ] [AGENT] P6. (`p6-plan6-check`) Phase 6 — Check whether Plan 6 (features-sports-service deployment) has the same
      build rot. Blocked on Phase 4. PARALLEL with Phase 5. Re-audit
      `features-sports-service/{Dockerfile,cloudbuild.yaml}` against the same 6 bug classes; if clean, flip and note "no
      repair required."

### Phase 7 — Workspace-wide success criteria [FINAL GATE]

- [ ] [AGENT] P7. (`p7-success-criteria`) Phase 7 — Validate workspace-wide success criteria. Blocked on Phase 5 AND
      Phase 6. SEQUENTIAL. Update plan frontmatter `repo_gates[deployment-service].code: C5, deployment: D2`. Final
      report-back to orchestrator: D1 6-Cloud-Build-failure regression closed + Plan 3 Phase 6 unblocked.

## Success criteria (per phase)

| Phase | Code gate                                                                          | Deployment gate                                                                                                                    | Business gate                                |
| ----- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| 0     | —                                                                                  | —                                                                                                                                  | PHASE-0-FINDINGS table embedded in plan body |
| 1     | `ruff check Dockerfile` (via QG) pass                                              | —                                                                                                                                  | —                                            |
| 2     | `ruff check cloudbuild.yaml` (QG yaml-lint) pass                                   | —                                                                                                                                  | —                                            |
| 3     | `docker build --target api` exit 0 + `import deployment_service.api.main` succeeds | —                                                                                                                                  | —                                            |
| 3b    | `bash scripts/quality-gates.sh` exit 0                                             | —                                                                                                                                  | —                                            |
| 4     | —                                                                                  | `gcloud builds submit` STATUS=SUCCESS + fresh AR tag today + Cloud Run Ready revision                                              | —                                            |
| 5     | —                                                                                  | `sports-scheduler` Cloud Run Job + `sports-scheduler-cron` Cloud Scheduler present + first manual fire `condition.state=Succeeded` | —                                            |
| 6     | `features-sports-service/Dockerfile` audit done + clean-or-dirty classification    | —                                                                                                                                  | —                                            |
| 7     | deployment-service `repo_gates` → `code: C5, deployment: D2`; Plan 3 → D3          | Plan 3 second cron fire (≤5 min window) writes state JSON to GCS                                                                   | Plan 3 unblocked                             |

The final phase MUST include:

- `cd deployment-service && bash scripts/quality-gates.sh` green.
- `gcloud builds list --region=asia-northeast1 --limit=1 --format='value(status)'` returns `SUCCESS`.
- `gcloud run services describe deployment-dashboard --format='value(status.conditions[0].status)'` returns `True`.
- `gcloud scheduler jobs describe sports-scheduler-cron --location=asia-northeast1` does not return NOT_FOUND.

## Out of scope

- **Terraform drift remediation (~134 resources)** — `terraform plan` shows 56 adds + 78 changes across features
  buckets, strategy buckets, IAM bindings, non-sports schedulers. Open a sibling plan
  `deployment_service_terraform_drift_remediation_2026_04_22` if the operator confirms urgency. Plan 12 only applies the
  2 sports-scheduler-scoped resources in Phase 5.
- **Consumer-repo Dockerfile hygiene for repos OTHER than deployment-service and features-sports-service** — out of
  scope. Plan 12 Phase 6 spot-checks features-sports-service ONLY because it's Plan 6's target.
- **UI co-serving from deployment-service** — dropping Stage 1 (`ui-builder`) is the decision. If the operator later
  wants the deployment dashboard to co-serve UI HTML from the API container (instead of fronting deployment-ui as a
  separate Cloud Run service), that requires a multi-repo Docker build context + separate plan.
- **Image version bumps for UTL base image** — the
  `asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest` tag floats. If
  the UTL base has itself regressed on deps since 2026-02-20, that's a separate UTL-side fix.
- **`deployment-api` sibling repo Dockerfile** — has the SAME `uv sync --frozen --no-dev --system` pattern that's broken
  by uv>=0.11. Flagged as follow-up `deployment_api_build_infrastructure_repair_2026_04_23` if deployment-api Cloud
  Build is also failing. Verify in Phase 6.

## Cross-references

- **Plan 3** (`sports_scheduler_cron_activation_2026_04_21.md`) depends on Phase 4 of this plan landing. Plan 3 Phase 6
  is the first plan to actually exercise a fresh deployment-service image in 2+ months.
- **Plan 6** (`features_sports_pipeline_deployment_2026_04_21.md`) may depend on Phase 6 of this plan —
  features-sports-service Cloud Build status confirms or refutes.
- **PLAN_FORMAT.md** § Citadel-Grade Planning Standards — this plan follows the pre-audit / phased-DAG /
  success-criteria structure.
- **Codex `02-data/sports-scheduling-and-sharding.md` §12.0** — register entry added for this plan (see commit wave).
- **D1 sub-agent report** (2026-04-22 session) — source of the 6-Cloud-Build-failure audit trail that motivated this
  plan.

## Phase-0-FINDINGS (populate during Phase 0 execution)

| Item                                                      | Finding                                                                                                                                                                                                                              | Action                                                                                                                                                                         |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ui/` / `api/` / `backends/` / `deployment/` at repo root | **CONFIRMED NEVER EXISTED.** `git log --all --diff-filter=A -- 'ui/' 'api/' 'backends/' 'deployment/'` returns empty. Actual layout: `deployment_service/{api,backends,deployment}/` subpackages; `configs/` at repo root (correct). | DROP `ui-builder` stage; delete `COPY api/ backends/ deployment/` lines; keep `COPY configs/`.                                                                                 |
| `uv sync --system` compatibility                          | **BROKEN with uv >= 0.11.** features-sports-service Dockerfile (2026-04 corrected) uses `uv pip install --system --no-deps -e .` — copy that pattern.                                                                                | Replace both `uv sync --frozen --no-dev --system` lines.                                                                                                                       |
| `gunicorn.conf.py` location                               | **MISSING from source.** Sibling `deployment-api/gunicorn.conf.py` exists at repo root; no equivalent in deployment-service. `deployment_service/api/main.py` exists.                                                                | Vendor into `deployment_service/api/gunicorn.conf.py` (copy sibling's shape); update CMD to `deployment_service.api.main:app -c /app/deployment_service/api/gunicorn.conf.py`. |
| Live `deployment-dashboard` image                         | To capture in Phase 0: `gcloud run services describe deployment-dashboard --format='value(spec.template.spec.containers[0].image)'`. Expected: SHA from 2026-02-20 build.                                                            | Confirm image age = gap evidence.                                                                                                                                              |
| `cloudbuild.yaml:225` heredoc                             | **BOTH** unescaped `$IMAGE`/`$RESULT` **AND** placeholder `UNKNOWN/UNKNOWN`.                                                                                                                                                         | Escape to `$$IMAGE` / `$$RESULT`; replace UNKNOWN with `${_ARTIFACT_REPO}/${_SERVICE_NAME}:${COMMIT_SHA}`.                                                                     |
| Terraform drift                                           | `terraform plan` in `deployment-service/terraform/gcp/` expected to show 56 adds + 78 changes.                                                                                                                                       | OUT OF SCOPE — Plan 12 only `-target`s the 2 sports-scheduler resources. Spawn drift-remediation plan if urgent.                                                               |

## Notes

- **Plan is locked** (`locked_by: live-defi-rollout`, `locked_since: 2026-04-22`) — archival requires `[unlock-plan]`
  per §9a of SUB_AGENT_MANDATORY_RULES.md.
- **Agent unlock protocol:** when all phases pass, ask the human to unlock. Do NOT unlock autonomously.
- **Rollback posture:** the Phase-4 Cloud Build is destructive only insofar as it pushes a new `:latest` tag. The
  previous 2026-02-20 tag remains in AR;
  `gcloud run services update-traffic deployment-dashboard --to-tags=<old-sha>=100` reverts the serving revision if the
  new image regresses at runtime. Terraform Phase 5 is additive (new resources only, no destructive changes).
- **Commit discipline:** Phase 1 + Phase 2 share a quickmerge wave (`fix(docker):` + `fix(cloudbuild):` combined). Phase
  5 terraform apply is manual / operator-gated — Phase 5 checkbox flip commits to PM only.
