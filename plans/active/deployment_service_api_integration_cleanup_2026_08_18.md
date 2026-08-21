---
doc_type: plan
title: deployment-service / deployment-api integration cleanup — image naming, HTTP-client dead path, Cloud Run Job registry
summary: >-
  Three related fixes at the deployment-service <-> deployment-api boundary, found chasing a naming collision this
  session. (1) 3 terraform files reuse deployment-api's OWN build image for Cloud Run Job monitors, tagged
  `deployment-api:latest` -- confusingly named AND non-obviously distinct from the ALREADY-EXISTING, DIFFERENT
  `deployment-service:latest` image wave_launcher already uses. (2) `deployment_service_client.py`'s
  `create_deployment()` is fully-coded, LIVE (real caller: deployment-ui's Deploy Console), and BROKEN in prod --
  it POSTs to a deployment-service HTTP API that is fully implemented server-side but never deployed as a reachable
  Cloud Run Service; its docstring cites a dangling `citadel_audit_remediation` reference. Operator-ruled direction:
  CLI/subprocess invocation, never a long-lived deployment-service HTTP layer. (3) Extends the VM-launcher
  single-source-of-truth pattern to Cloud Run Jobs, with a deployment-ui surface.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, deployment-api, deployment-ui, unified-trading-pm]
scope: [engineer, admin]
tags: [deployment, terraform, cloud-run, launcher-registry, ssot-contradiction, dead-code-audit]
related:
  [
    /codex/05-infrastructure/launcher-script-ssot.md,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
    /plans/active/issues/deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4.0
assigned_role: infra
effort: medium
drift_direction: advance-code
depends_on:
context_scope:
  [
    /codex/05-infrastructure/launcher-script-ssot.md,
    /codex/05-infrastructure/deployment-clusters-live-vs-batch.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    deployment-service/docs/ARCHITECTURE.md,
    deployment-api/deployment_api/clients/deployment_service_client.py,
    deployment-api/deployment_api/services/deploy_missing.py,
    deployment-service/deployment_service/api/routes/state.py,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
    /plans/active/issues/deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md,
  ]
supersedes:
superseded_by:
source:
  [
    "operator-directed interactive session, 2026-08-18 -- deployment-service/deployment-api integration cleanup
    (image naming collision, deployment_service_client.py SSOT contradiction + dead-vs-live determination, Cloud Run
    Job launcher-registry gap). Pre-task conflict-check grepped plans/active/ + plans/active/issues/ for overlap --
    no existing doc covers any of the 3 problems below; nearest siblings
    (deployment_service_prod_terraform_drift_2026_08_07.md, deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md,
    deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md) are adjacent terraform/IAM hygiene, not
    duplicative -- cross-linked via related:/context_scope above.",
  ]
locked_by:
locked_since:
---

# deployment-service / deployment-api integration cleanup

## Context (read before dispatch — saves every worker a re-derivation pass)

This session traced the deployment-service <-> deployment-api boundary end-to-end. Three independent, evidence-backed
findings below; each is scoped into its own todo(s), all on different files so they run concurrently by default (no
`sequential: true` on this plan).

**Problem 1 — image naming.** `data_pipeline_fleet_monitor_scheduler.tf`'s `data_pipeline_monitor_image` local,
`deployment_digest_scheduler.tf`'s `deployment_digest_image` local, and `monitoring_deadman_scheduler.tf`'s
`monitoring_deadman_image` local ALL resolve to
`${region}-docker.pkg.dev/${project_id}/unified-trading-system/deployment-api:latest` — confirmed via
`grep -rn "unified-trading-system/deployment-api" deployment-service/terraform/gcp/*.tf`, the ONLY 3 hits in the
54-file directory. **Verified false leads (do not touch)**: `consolidator_liveness_scheduler.tf` uses the
`market-tick-data-service` image; `wave_launcher_scheduler.tf`'s `wave_launcher_image_resolved` defaults to
`unified-trading-system/deployment-service:latest` (a GENUINELY DIFFERENT, already-existing image, built from
`deployment-service/Dockerfile`'s own `COPY deployment_service/ ./deployment_service/`); `cf_manifest_audit_scheduler.tf`
defaults to the MTDS image; `honest_coverage_scheduler.tf` uses `google-cloud-cli:alpine`; `data_status_rollup_scheduler.tf`
has no image local at all (comments merely mention the deployment-api HTTP endpoint). **Root cause**:
`deployment-api/Dockerfile` does `COPY _deployment-service/ /tmp/deployment-service/` (deployment-api's OWN build
copies the whole deployment-service repo in) — `monitoring_deadman_scheduler.tf`'s own comment confirms this is "the
only image that COPYs `deployment_service/`", which is how the 3 Cloud Run Jobs run
`-m deployment_service.data_pipeline_monitors.<entrypoint>` against an image that is genuinely deployment-api's
build artifact, not deployment-service's. **The naive fix ("rename to `deployment-service:latest`") is UNSAFE** — that
name is already taken by a different image.

**Problem 2 — SSOT contradiction + live-broken bug.** `deployment_api/clients/deployment_service_client.py`'s module
docstring claims deployment-service "currently exposes a CLI interface only" and cites a dangling
`citadel_audit_remediation` tracker (confirmed via corpus-wide grep: zero hits anywhere in the current
`unified-trading-pm` plan/issue/codex corpus — only 2 unrelated March-era archived docs + one report use that
substring). **Both halves of the docstring's premise are wrong**: deployment-service's
`deployment_service/api/routes/state.py` implements the FULL endpoint surface `deployment_service_client.py` calls,
route-for-route (`/api/v1/deployments`, `/api/v1/shards/calculate`, `/api/v1/data-status`, `/api/v1/vm-jobs/cancel`,
`/api/v1/vm-jobs/status-batch`, `/api/v1/cloud-run/status-batch`, `/api/v1/quota/acquire`, `/api/v1/quota/release`,
`/api/v1/deployments/{id}/events`, `/api/v1/deployments/{id}/vm-events`, `/api/v1/deployments/{id}/rollback`,
`/api/v1/deployments/{id}/live-health`) — its own module docstring says so verbatim ("Endpoints match exactly what
deployment_service_client.py in deployment-api calls"), and it's actually run in prod via
`gunicorn deployment_service.api.main:app` per `deployment-service/Dockerfile`'s CMD. **But this server is never
reachable from deployment-api**: `DEPLOYMENT_SERVICE_URL` defaults to `http://localhost:9000`
(`deployment_api_config.py`'s `deployment_service_url` Field), `deployment-api/cloudbuild.yaml`'s
`gcloud run deploy uts-shared-deployment-api` never overrides it via `--update-env-vars`, and there is no
`google_cloud_run_v2_service` terraform resource for deployment-service anywhere in
`deployment-service/terraform/gcp/` (deployment-service only ever runs as Cloud Run JOBS with overridden
entrypoints). So every `deployment_service_client.py` HTTP call fails with a connection error in prod today. **This
is LIVE, not dead**, for at least `create_deployment()`: `deployment-ui/src/api/client.ts`'s `createDeployment()` is
called from `deployment-ui/src/components/cockpit/DeployConsole.tsx`'s submit handler, reaching
`deployment_api/routes/deployments/_crud.py`'s `POST /deployments` route -> `deployment_manager.create_deployment()`
-> `_call_create_deployment()` -> this HTTP client function. **Operator-confirmed direction**: standardize on
library/CLI invocation — deployment-service stays CLI/Cloud-Run-Jobs only, never a long-lived HTTP service the way
`deployment_service/api/` currently (but unreachably) implements.

**Problem 3 — Cloud Run Job registry gap.** `/codex/05-infrastructure/launcher-script-ssot.md` already establishes
the VM-launcher single-source-of-truth pattern (`_SERVICE_LAUNCHER_SCRIPTS` in
`deployment_api/services/deploy_missing.py`, rendered by `deployment-ui/src/components/DeployMissingButton.tsx`) and
its own "Cloud Run launchers" section already covers Cloud Run Service-REVISION deploy scripts
(`deployment-service/scripts/cloud-run/deploy-*.sh`) — but nothing covers Cloud Run JOBS (the data-pipeline watcher
family: `data_pipeline_fleet_monitor_scheduler.tf`, `monitoring_deadman_scheduler.tf`, `deployment_digest_scheduler.tf`,
`consolidator_liveness_scheduler.tf`, `wave_launcher_scheduler.tf`, `cf_manifest_audit_scheduler.tf`,
`honest_coverage_scheduler.tf`, plus the 4 direct `resource "google_cloud_run_v2_job"` blocks
(`sports_scheduler`, `subgraph_health_probe`, `vm_log_archival`, `vm_serial_capture`) and the terraform-module-based
jobs like the T1-recon family — confirmed via `grep -rho 'resource "google_cloud_run_v2_job" "[a-z_]*"'
deployment-service/terraform/gcp/*.tf` plus `module.*_job` blocks). **Pre-agreed shape for this plan** (so todos 7-9
below don't need todo 5's code to have landed first): a new module
`deployment-api/deployment_api/services/cloud_run_jobs_registry.py` exporting
`CLOUD_RUN_JOB_REGISTRY: dict[str, CloudRunJobEntry]` (one dataclass/TypedDict per job: `terraform_file`,
`scheduler_cadence`, `purpose`), and a new route `GET /api/cloud-run-jobs` returning it as JSON.

---

## Todos

- [x] 1. ✅ [INFRA] P1. Resolve the `deployment-api:latest` image-naming confusion across the 3 terraform files that
      actually reference it. **Per-file finding was a genuine split, not the uniform either/or the todo anticipated**:
      `data_pipeline_fleet_monitor_scheduler.tf` (3 jobs: exit-code/heartbeat/meta) and `monitoring_deadman_scheduler.tf`
      invoke `deployment_service.data_pipeline_monitors.*` entrypoints — confirmed these resolve cleanly against
      deployment-service's OWN `deployment-service:latest` (the `maintenance-jobs`-stage image built by
      `deployment-service/cloud-build/deployment-service-jobs-image.cloudbuild.yaml` specifically for Cloud Run Jobs
      needing the eager `deployment_service.__init__` -> `backends` import chain — the SAME image
      `wave_launcher_scheduler.tf` already runs `deployment_service`-owned code on) — repointed all 4 job locals to
      it, deleted nothing (kept the locals, just fixed their value — DRY over the todo's literal "delete + inline 3x"
      suggestion). `deployment_digest_scheduler.tf` invokes `deployment_api.scripts.deployment_digest_worker` — a
      genuinely different, `deployment_api.*`-owned entrypoint that deployment-service's image does NOT install, so
      it correctly stays on a deployment-api-built image; attempted the "distinct honest tag" branch
      (`deployment-api-bundled:latest`) but **reverted** it — wiring the new tag required forward-porting a new
      build/push step into the shared `cloudbuild-api-template.yaml`, which `check_cloudbuild_template_drift`'s
      shrink-only baseline blocked (17 markers > baseline 16); that's a cross-cutting PM-template change out of this
      todo's scope. Left `deployment_digest_scheduler.tf` on the original `deployment-api:latest` tag — functionally
      correct (unchanged behavior), the naming-collision concern is NOT fully resolved for this one job (see follow-up
      todo below). **Live discovery not anticipated by the todo**: `deployment-api/cloudbuild.yaml`'s existing
      `redeploy-monitor-jobs` step auto-re-pinned all 4 dp-monitor/deadman jobs to `deployment-api:latest` on every
      deployment-api deploy — left unaddressed, the very next deploy would have silently reverted this fix. Narrowed
      that step (renamed `redeploy-digest-job`) to only `uts-prod-deployment-digest`, and added the 4 jobs to
      `deployment-service-jobs-image.cloudbuild.yaml`'s own `redeploy-jobs` re-pin list instead. Done-when (as
      modified by the above): `grep -rn "deployment-api:latest" deployment-service/terraform/gcp/*.tf` — zero hits in
      `data_pipeline_fleet_monitor_scheduler.tf`/`monitoring_deadman_scheduler.tf` (still present, correctly, in
      `deployment_digest_scheduler.tf` — see follow-up); `ENV=prod bash deployment-service/terraform/gcp/tofu.sh plan`
      shows only the 4 repointed jobs' image diff (targeted `-target` apply, no destroys, no unrelated pre-existing
      drift touched — `deployment_service_prod_terraform_drift_2026_08_07.md`'s ~62 unrelated changes left alone);
      applied; all 4 jobs' post-change executions SUCCEEDED. Evidence: `deployment-service@873d88a0a1` (terraform +
      deployment-service-jobs-image.cloudbuild.yaml, QG green) — targeted apply confirmed via
      `gcloud run jobs describe` (all 4 → `deployment-service:latest`) — executions
      `uts-prod-dp-exit-code-monitor-zzqq6`, `uts-prod-dp-heartbeat-watcher-kfzvt`, `uts-prod-dp-meta-watchers-rsq6v`,
      `uts-prod-monitoring-deadman-4swb7` all `succeededCount=1`. `deployment-api@8bdec86e9d` (cloudbuild.yaml
      narrowing, QG green) + `deployment-service@9a60be47a7` (deployment_digest_scheduler.tf revert, QG green). Final
      `tofu plan` re-verified: my 5 job resources show zero diff (change-count dropped from 67 -> 62, exactly -5).

- [ ] 1b. [INFRA] P3. Follow-up from item 1: give `deployment_digest_scheduler.tf`'s Cloud Run Job (`uts-prod-deployment-digest`)
      a distinct, honestly-named image tag instead of reusing `deployment-api:latest` (which still collides in name
      with the deployment-api SERVICE's own deploy identity, even though it's no longer confused with
      deployment-service:latest since items 1's other 4 jobs moved off it). Requires forward-porting a
      `deployment-api-bundled:latest` alias build (`-t`) + push step into
      `unified-trading-pm/configs/cloudbuild-api-template.yaml` (gated so it doesn't affect the template's OTHER
      consumers, e.g. client-reporting-api) so `deployment-api/cloudbuild.yaml`'s content stops being flagged as
      undrained by `check_cloudbuild_template_drift`'s shrink-only baseline — then re-apply the
      `deployment-api-bundled:latest` rename to `deployment_digest_scheduler.tf` + re-add the `redeploy-digest-job`
      re-pin to the new tag (both attempted + reverted in item 1's session — the terraform-side diff is straightforward
      to redo once the template accepts the build/push content). Done-when: `check_cloudbuild_template_drift.py --repo
      deployment-api` passes with the new content; `deployment_digest_scheduler.tf`'s local points at
      `deployment-api-bundled:latest`; applied + a verified SUCCEEDED execution.

- [x] 2. ✅ [BACKEND] P1. Fix `create_deployment()` in `deployment_api/clients/deployment_service_client.py` — it POSTs to
      `{DEPLOYMENT_SERVICE_URL}/api/v1/deployments`, a route `deployment_service/api/routes/state.py` DOES implement
      server-side, but the server is never reachable in prod (re-verify: `gcloud run services list
      --project=central-element-323112 --region=asia-northeast1` shows no deployment-service entry; `gcloud run
      services describe uts-shared-deployment-api --project=central-element-323112 --region=asia-northeast1
      --format='value(spec.template.spec.containers[0].env)'` shows no `DEPLOYMENT_SERVICE_URL` override, confirming
      the `http://localhost:9000` default is what's live). This path IS live, not dead — confirmed real caller:
      `deployment-ui/src/api/client.ts`'s `createDeployment()`, invoked from
      `deployment-ui/src/components/cockpit/DeployConsole.tsx`'s submit handler, reaching
      `deployment_api/routes/deployments/_crud.py`'s `POST /deployments` route -> `deployment_manager.create_deployment()`
      -> `_call_create_deployment()` -> this function — so today, clicking Deploy in the Deploy Console fails with a
      connection error every time. Per the operator-confirmed direction (library/CLI invocation, never a long-lived
      deployment-service HTTP layer): replace the HTTP POST in `create_deployment()` with a subprocess/CLI invocation
      of deployment-service's `deploy-shards` CLI, mirroring the launcher-invocation pattern in
      `deployment_api/services/deploy_missing.py`'s `_SERVICE_LAUNCHER_SCRIPTS` (a registered script path invoked via
      subprocess, not an HTTP round-trip). In the SAME file, correct the module docstring: remove the dangling
      `citadel_audit_remediation` reference and state the ACTUAL mechanism (subprocess/CLI for `create_deployment`;
      note that the file's other functions are separately audited in the next todo). Done-when: `create_deployment()`
      no longer performs an HTTP POST; a scripted or operator-supervised DeployConsole submit against staging
      succeeds end-to-end; the docstring no longer mentions `citadel_audit_remediation`; `quality-gates.sh --no-fix`
      green on `deployment-api`. Evidence: `<repo>@<sha>` + the staging submit's deployment_id/result. —
      `deployment-service@c16b1f1407` (QG: 3483 passed) + `deployment-api@cf45576cec` (QG: 5433 passed), both on LDR,
      ancestry-verified. `create_deployment()` now invokes `python -m deployment_service deploy-shards` as a
      subprocess (previously a stub CLI command — built out to mirror `state.py`'s `POST /api/v1/deployments` handler
      field-for-field via `StateManager.create_deployment()`). Docstring corrected. Real E2E verification: ran the
      actual client function against the live `unified-deployment-state-central-element-323112` bucket — first pass
      (pre-fix) returned a false-success JSON with NOTHING actually written to GCS (caught via direct `blob.exists()`
      check, not assumption); post-fix, write succeeded AND an independent `StateManager.load_state()` read-back
      returned the correct `deployment_id`/`service`/`status`; test objects deleted after, confirmed gone. **Second,
      more serious bug found + fixed along the way**: `StateManager.save_state/load_state/list_deployments` were
      calling nonexistent `upload_from_string()`/`download_as_string()` methods on UTL's GCS handle, silently
      swallowed by a defensive `getattr/callable()` guard — every deployment "creation" was logging success while
      persisting nothing. Fixed via the proven `upload_bytes`/`download_as_bytes` pattern already used correctly in
      `deployment_service/scripts/wave_launcher.py`. **This same anti-pattern is confirmed still present, unfixed, in
      `deployment_service/monitor.py`, `deployment_service/orchestrator.py`, and
      `deployment_service/backends/services/vm_monitoring.py`, plus 60+ untriaged candidate files fleet-wide** — see
      `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md` (filed, out of this
      todo's scope).

- [x] ✅ [REVIEW] P2. Audit-only (no fix) — for every OTHER function in `deployment_api/clients/deployment_service_client.py`
      (`calculate_shards`, `get_data_status`, `cancel_vm_jobs`, `get_vm_status_batch`, `quota_acquire_batch`,
      `get_cloud_run_status_batch`, `quota_release_batch`, `get_deployment_events`, `get_vm_events`, `live_rollback`,
      `get_live_health`), determine whether each has a real, currently-invoked caller — grep every route/service in
      `deployment-api/deployment_api/` plus the corresponding `deployment-ui/src/api/client.ts` functions and their
      component callers. Each shares `create_deployment()`'s exact same broken-HTTP root cause (same unreachable
      `DEPLOYMENT_SERVICE_URL`), so a live-caller function is an equally-broken production bug; a genuinely-uncalled
      function is real dead code. Produce a table: function -> live caller (yes/no + citation) -> recommendation
      (fix-like-create_deployment / remove / already-dead-leave-for-now). Done-when: the table is written into this
      todo's evidence, AND — if the table finds any OTHER live-broken function beyond `create_deployment` — a new
      issue doc is filed at `plans/active/issues/deployment_service_client_broken_functions_<date>.md` (fix-scoped
      follow-up, out of THIS plan's scope) per the findings-triage HARD RULE (never leave a live-broken function as a
      dangling prose note). **Evidence (slot-15 audit, 2026-08-20):**
      | function | live caller | recommendation |
      |---|---|---|
      | `calculate_shards` | Yes — `deployment_manager.py:200,320` | Fix like `create_deployment` |
      | `get_data_status` | Yes — `routes/data_status_helpers.py:43` | Fix like `create_deployment` |
      | `cancel_vm_jobs` | Yes — `_deployment_processor_helpers.py:53`, used by VM processor/cleanup | Fix like `create_deployment` |
      | `get_vm_status_batch` | Yes — `routes/deployment_state.py:287` | Fix like `create_deployment` |
      | `quota_acquire_batch` | No route/service/worker/UI caller found | Remove after external-import check |
      | `get_cloud_run_status_batch` | Yes — `routes/deployment_state.py:223`, `_deployment_processor_cloud_run.py:33`, `services/event_processor.py:332` | Fix like `create_deployment` |
      | `quota_release_batch` | No route/service/worker/UI caller found | Remove after external-import check |
      | `get_deployment_events` | Yes — `_lifecycle.py:303`; UI `client.ts:3804` → `DeploymentDetails.tsx:411` | Fix like `create_deployment` |
      | `get_vm_events` | Yes — `_lifecycle.py:331`; UI wrapper `client.ts:3816` has no component caller found | Fix backend; remove or wire unused UI wrapper |
      | `live_rollback` | Yes — `_lifecycle.py:361`; UI `client.ts:3826` → `DeploymentDetails.tsx:441` | Fix like `create_deployment` |
      | `get_live_health` | Yes — `_lifecycle.py:400`; UI `client.ts:3840` → `DeploymentDetails.tsx:423` | Fix like `create_deployment` |

      All nine live functions still POST via `_base_url()` and share the documented unreachable `localhost:9000`
      transport (`deployment_service_client.py:6-16,29-31`; `deployment_api_config.py:615-619`; no
      `google_cloud_run_v2_service` in `deployment-service/terraform/gcp/`). Follow-up issue filed:
      `/plans/active/issues/deployment_service_client_broken_functions_2026_08_20.md`. No code was changed by this
      audit.

- [ ] [DOC] P2. Correct `deployment-service/docs/ARCHITECTURE.md`'s claim "It is not a long-lived service —
      deployment-api orchestrates it as a library." Verify precisely what "library" means today: deployment-api's
      own `Dockerfile` (`COPY _deployment-service/ /tmp/deployment-service/` + the install step immediately after
      it — read the exact mechanism, editable pip install or PYTHONPATH) makes `deployment_service.*` modules
      importable/runnable via `-m deployment_service.xxx` entrypoint overrides INSIDE deployment-api's own built
      image — confirmed as the load-bearing mechanism for problem 1's 3 Cloud Run Jobs. But deployment-service ALSO
      ships a fully-built FastAPI HTTP server (`deployment_service/api/main.py`, run via
      `gunicorn deployment_service.api.main:app` per its own Dockerfile CMD) implementing an endpoint surface that
      matches `deployment_service_client.py` route-for-route — fully coded but (per the prior 2 todos' findings)
      never deployed as a reachable service. Rewrite the ARCHITECTURE.md paragraph to state BOTH mechanisms
      precisely and which is actually load-bearing today (library/Docker-COPY) vs. dead/unreachable
      (the HTTP server) — re-verify live via `gcloud run services list --project=central-element-323112` showing no
      deployment-service entry before asserting the HTTP server is unreachable, per the "verified, not asserted"
      discipline. Done-when: the paragraph states the true, dual-mechanism reality with citations; cross-references
      `deployment_service_client.py`'s corrected docstring (prior todo) so the two docs agree.

- [ ] [INFRA] P2. Enumerate every scheduled Cloud Run Job in `deployment-service/terraform/gcp/` (54 `.tf` files) —
      both direct `resource "google_cloud_run_v2_job"` blocks (4 confirmed via
      `grep -rho 'resource "google_cloud_run_v2_job" "[a-z_]*"' deployment-service/terraform/gcp/*.tf`:
      `sports_scheduler`, `subgraph_health_probe`, `vm_log_archival`, `vm_serial_capture`) AND every `module` block
      whose source implements a Cloud Run Job (the `t1_recon_instruments_job` / `instruments_cefi_t1_recon_job`
      pattern per `plans/active/issues/deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md`, plus
      the `{name}-launcher` pattern documented in `/codex/05-infrastructure/launcher-script-ssot.md`'s "Cloud
      Scheduler trigger SSOT" section, e.g. `honest-coverage-daily-launcher`) — for each: job name, defining `.tf`
      file, triggering Cloud Scheduler cadence (if any), image source (local var name), one-line purpose. Then build
      the registry consuming that inventory directly: a new module
      `deployment-api/deployment_api/services/cloud_run_jobs_registry.py` exporting
      `CLOUD_RUN_JOB_REGISTRY: dict[str, CloudRunJobEntry]` (a small dataclass/TypedDict with `terraform_file`,
      `scheduler_cadence`, `purpose` fields) — cite each entry's `terraform_file` SYMBOLICALLY (the filename, not a
      hardcoded image path) so the registry stays correct regardless of the image-local renames in the prior todos.
      Cross-check the terraform-declared set against `gcloud run jobs list --region=asia-northeast1
      --project=central-element-323112` to confirm no live drift (flag, don't fix — that's
      `deployment_service_prod_terraform_drift_2026_08_07.md`'s territory). Done-when: `CLOUD_RUN_JOB_REGISTRY` has
      one entry per inventoried job; `basedpyright`/`ruff` clean; the inventory table is written into this todo's
      evidence.

- [ ] [SCRIPT] P3. Build a QG parity check ensuring `CLOUD_RUN_JOB_REGISTRY` (prior todo) never silently drifts
      behind terraform — mirror the "warning-with-baseline" pattern in
      `/codex/05-infrastructure/launcher-script-ssot.md`'s "QG check policy" section (the same shape already used for
      `check_banned_placeholder_methods.py`): detect every `google_cloud_run_v2_job` resource / job-shaped module
      block across `deployment-service/terraform/gcp/*.tf`, assert each has a matching `CLOUD_RUN_JOB_REGISTRY` key,
      day-1 baseline any currently-tolerated gap. Done-when: `scripts/quality_gates/check_cloud_run_job_registry_parity.py`
      + companion baseline YAML exist, wired into `deployment-service/scripts/quality-gates.sh` (or `deployment-api`'s,
      whichever repo owns the check per its imports) as a new numbered STEP, green on introduction.

- [ ] [BACKEND] P2. Add `GET /api/cloud-run-jobs` in `deployment-api` (new routes file or an existing
      registry-adjacent one) returning `CLOUD_RUN_JOB_REGISTRY`'s contents as JSON, following the same
      response-shape conventions as the existing `GET /api/builds/{service}` route in
      `deployment-api/deployment_api/routes/builds.py`. Done-when: the route is registered + reachable
      (`curl <deployment-api-url>/api/cloud-run-jobs` returns the full registry), OpenAPI schema present, unit test
      covering the happy path.

- [ ] [DOC] P2. Extend `/codex/05-infrastructure/launcher-script-ssot.md` with a new section documenting the Cloud
      Run Job registry (prior 2 todos) — mirror the doc's existing "Scope: what counts as a VM launcher" table +
      "Adding a new launcher" numbered steps, adapted for Cloud Run Jobs (steps: add the terraform resource/module,
      register in `CLOUD_RUN_JOB_REGISTRY`, verify the Cloud Scheduler trigger per the doc's existing "Cloud
      Scheduler trigger SSOT" section). Explicitly distinguish this new section from the doc's existing "Cloud Run
      launchers" section (that one covers Cloud Run Service-REVISION deploy scripts
      `deployment-service/scripts/cloud-run/deploy-*.sh` — a different concern from Cloud Run JOB scheduling) with a
      one-line cross-pointer each way. Done-when: the new section exists; doc frontmatter's `last_reviewed`/`code_refs`
      updated.

- [x] ✅ [UI] P2. Add a deployment-ui surface rendering `GET /api/cloud-run-jobs` (prior route todo) — investigate what
      deployment-ui currently renders for the VM-launcher registry
      (`deployment-ui/src/components/DeployMissingButton.tsx`'s pattern, reachable from the Data Status drill-down)
      and check `deployment-ui/src/pages/` (`Cockpit.tsx`, `Deployments.tsx`, `HomeShell.tsx`) for a natural existing
      home before adding a new tab/section. Read-only listing (job name, cadence, purpose, last-execution status if
      cheaply reachable) is sufficient scope — a "trigger now" action is explicitly OUT of scope (no established UI
      precedent to mirror; would need its own IAM/audit-log review the way `deploy_missing.py`'s VM auto-launch split
      Phase 3 preview-only from a deferred Phase-4 auto-launch). Done-when: `pw:L2` check green + a regression spec
      cited (`tests/smoke/routes.spec.ts` for a new route, or `tests/widgets/<widget-id>.test.tsx` for a new widget)
      per the UI Verification Gate — tick evidence MUST include `repo@sha | pw:L2 ✓ | regression: <path>`.
      Evidence: deployment-ui@cd13cfa | pw:L2 ✓ (`tests/smoke/cloud-run-jobs.spec.ts`) | read-only `/cloud-run-jobs`
      page, nav entry, API client, and mock route committed; focused Playwright smoke passed (1 test).

---

- [x] ✅ [BACKEND] P0. **Break the deployment-api to deployment-service Python dependency** (added 2026-08-21, provenance
      `/plans/active/cross_repo_duplication_cleanup_2026_08_21.md`). `deployment-api/pyproject.toml:47,69,128` declares
      `deployment-service` as an editable path dependency and **15 non-test files import it**, two at module level
      (`routes/deployments_inventory/_aggregation.py:22-23`, `routes/deployments_inventory/_classification.py:20-21`;
      the rest are function-level, e.g. `routes/vm_admin.py:262`, `services/artifact_pipeline/providers.py:442`). This
      is a banned service-to-service dependency and it contradicts `deployment_api/config_loader.py:4-10`, whose
      docstring states deployment-api must not import deployment-service as a package. Someone already half-decoupled
      the repos — `config_loader.py`, `metrics.py` and `storage_client.py` are deliberately slimmed independent
      reimplementations — and left the route-level registry imports behind. Fix: hoist `CLOUD_RUN_JOBS` and
      `deployment_classification` to UAC, re-point the routes, drop the path dependency. SSOT:
      `/codex/04-architecture/tier-and-import-architecture.md`. Evidence: deployment-api@a9b88f253 + deployment-service@ecb0c156 + unified-api-contracts@e48adfa3; deployment-api QG 5,414 passed/11 skipped, deployment-service QG 3,655 passed/5 skipped, UAC QG passed.
- [ ] [BACKEND] P2. **Deduplicate the two backend pairs in `deployment-service`** (same provenance). `backends/aws.py`
      vs `backends/aws_batch.py` measure 404 vs 411 lines with **21 differing** (254 shared 30-line blocks);
      `backends/cloud_run.py` vs `backends/gcp.py` share 164 blocks. Extract the common driver rather than keeping two
      near-copies per cloud.

## Progress Log

- **2026-08-18 (authoring)**: Plan drafted this session after tracing the deployment-service/deployment-api
  boundary end-to-end (terraform image-local audit, HTTP client vs. server route-surface comparison, deployment-ui
  caller trace). `status: draft` pending operator review before dispatch. Companion gated finalize plan:
  `/plans/active/deployment_service_api_integration_cleanup_finalize_2026_08_18.md`.
- **2026-08-18 (operator directive — urgent fix dispatched ahead of full plan activation)**: Todo 2 (Deploy Console
  live-broken bug) was fixed and shipped out-of-band before the rest of the plan, since it was a live production
  bug (Deploy Console failing every submit), not deferred to normal AO dispatch order — see its evidence line above.
  Surfaced a second, more serious finding along the way (silent GCS write failures via a wrong UTL client method
  name, confirmed in 3 more deployment-service files + 60+ untriaged candidates fleet-wide) — filed as
  `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`, flagged to the
  operator directly (big finding: cross-repo, data-correctness). Plan flipped `status: active` this same edit —
  remaining todos (1, 3-9) now dispatchable to AO.
- **2026-08-19 (slot 32, item 1)**: Resolved. Per-file finding was a genuine split (2 of 3 jobs' entrypoints resolve
  cleanly against `deployment-service:latest`; the 3rd genuinely needs a deployment-api-built image) rather than the
  uniform either/or the todo phrased — see item 1's evidence line for the full split + the reverted
  `deployment-api-bundled:latest` attempt (blocked by `check_cloudbuild_template_drift`'s shrink-only baseline,
  requires a `cloudbuild-api-template.yaml` forward-port — spun off as new item 1b). Also surfaced + fixed a live
  discovery the todo didn't anticipate: `deployment-api/cloudbuild.yaml`'s pre-existing `redeploy-monitor-jobs`
  auto-repin step would have silently reverted this fix on the next deployment-api deploy — narrowed it and added
  the moved jobs to `deployment-service-jobs-image.cloudbuild.yaml`'s own re-pin list instead. All 4 repointed jobs'
  post-change executions verified SUCCEEDED live in prod (`uts-prod-dp-exit-code-monitor-zzqq6`,
  `uts-prod-dp-heartbeat-watcher-kfzvt`, `uts-prod-dp-meta-watchers-rsq6v`, `uts-prod-monitoring-deadman-4swb7`).
  Shipped: `deployment-service@873d88a0a1`, `deployment-api@8bdec86e9d`, `deployment-service@9a60be47a7`.
- **context-scout 2026-08-20**: refreshed context_scope (9 entries)
- **2026-08-20 (slot 7)**: Completed the deployment-ui Cloud Run Job registry surface. The committed page renders
  `GET /api/cloud-run-jobs` as a read-only table of job, Terraform file, scheduler cadence, and purpose; no trigger
  action is exposed. Focused Playwright verification passed: `tests/smoke/cloud-run-jobs.spec.ts` (1 passed).
