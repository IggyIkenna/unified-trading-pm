---
doc_type: plan
title: Artifact pipeline observability — build → artifact → deploy lineage across both clouds
summary:
  A new /ops/artifacts page that shows the deployment estate's FINAL stage end-to-end — every Docker image and VM
  tarball built, where it landed, what git SHA it carries, why a build failed, and (the view that does not exist today)
  what each workload is ACTUALLY running right now, with drift flags. Reads live cloud APIs behind a periodic
  GCS-snapshot worker (the cost-observability pattern) so it is cheap and OOM-safe. Absorbs the scattered prior art
  (CloudBuildsTab + cloud_builds/builds/builds_history + RepoCi ImageCell) into one coherent surface and retires the
  narrow per-service tab. Mock-first is done (real probed data); this plan wires the real API + UI.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    deployment-observability,
    artifact-pipeline,
    image-builds,
    tarballs,
    cloud-build,
    codebuild,
    cloud-run-revisions,
    mock-first,
    ci-cd,
  ]
related:
  [
    deployment_observability_expansion_2026_07_08.md,
    cost_observability_ui_2026_07_08.md,
    deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md,
    deployment_registry_firestore_migration_2026_07_14.md,
  ]
created: "2026-07-17"
last_updated: "2026-07-17"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 13
estimate_calibrated_ai_days: 10
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: operator request 2026-07-17 (interactive, tab-2)
assigned_role: infra
drift_direction: advance-code
---

# Artifact pipeline observability — build → artifact → deploy lineage

> **Human / local plan** (`assigned_vm: NA`, never AO-ingested). Operator-driven in an interactive session. Mock-first:
> the standalone HTML mock is agreed before any code. This plan REFERENCES the codex SSOTs below; it does not duplicate
> them.

## Why

The build pipeline is dual-cloud and busy (GCP Cloud Build → Artifact Registry, AWS CodeBuild → ECR; a separate VM
code-tarball lane). It **emits** rich per-build/per-deploy metadata but **persists almost none of it durably**, and
nothing today answers the question that matters most — _"what is each workload actually running right now, and where did
it come from?"_ The existing `_image_signal` (RepoCi) answers the **image-level** question ("is main's code built into
the latest image?") and was explicitly scoped "v1 image-level, not runtime-level". This page is the runtime layer + a
real cross-cloud build/deploy feed, so the deployment estate's final stage becomes legible.

## Codex SSOTs (read + keep this plan aligned — plan↔codex drift is review-blocking)

- `codex/05-infrastructure/dual-cloud-image-builds.md` — the image build flow (routers, registries, promote gate,
  provenance). **NOTE: this doc has measured drift — see "Codex fixes" below. Correcting it is in-scope.**
- `codex/05-infrastructure/vm-tarball-deployment.md` — the tarball lane (Lane B).
- `codex/05-infrastructure/cloud-agnostic-build-lineage.md` — STUB; the aspirational SHA→dual-cloud-parity model. This
  page is the pragmatic first cut of the "trace an artifact to a SHA" goal.
- `codex/06-coding-standards/ui-testing-layers.md` — the pw:L2 gate (no UI tick without `[UI]` + `pw:L2 ✓` + a cited
  regression spec).
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — for the snapshot worker.
- Constraint doc (active plan, not codex): `deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md` — the
  hard memory rules the backend must obey (see "Constraints").

## Data feasibility — MEASURED 2026-07-17 (the load-bearing part)

Every field the target shape needs can be produced, it is cheap, and ~60–72 days of history already exists free. Numbers
below are measured against GCP `central-element-323112` + AWS `427895769566`, not assumed.

| Source                      | Depth (measured)                      | Carries                                                 | Read cost |
| --------------------------- | ------------------------------------- | ------------------------------------------------------- | --------- |
| **Cloud Run revisions**     | back to **2026-05-06** (72d; 192/svc) | image, **resolved digest**, deploy time, deployer       | free      |
| **Cloud Build history**     | back to **2026-05-19** (60d; 2000+)   | SHA, trigger, branch, **structured failureInfo**, steps | free      |
| **AWS CodeBuild**           | 400+ builds/project                   | SHA, phases[].contexts[] failure, initiator             | free      |
| **Artifact Registry / ECR** | all live images                       | digest, tags, pushed-at, size                           | free      |
| **App Runner / ECS**        | operation history incl. **FAILED**    | image (by tag), deploy status + time                    | free      |
| **Tarball manifests (GCS)** | 3645 manifests (outlive 158 tarballs) | commit_sha (full), pyproject_version, created_at, clean | free      |

- **The existing `unified-trading-cicd-events` ledger is a red herring for builds** — no TTL, but today-only partitions
  and rows are QG-state transitions (`MAIN_GREEN`, `SIT_VALIDATED`), not build records (only ~1 `cloud-build-router` row
  seen). Do NOT depend on it; read the cloud APIs directly.
- **Cost to keep history forever**: a build record ≈ 1.5 KB, a revision ≈ 0.6 KB → **< 0.5 GB/year** → GCS storage **<
  $0.01/mo**; reads are metadata API calls (no charge, no egress); query is in-process DuckDB (free); worker is a ~1-min
  job every 30–60 min. **Cents per year — the "no huge money" constraint is met.**

## The runtime join (how "what's running" resolves)

- **GCP images**: Cloud Run revision `status.imageDigest` resolves even a `:latest` pin to a real digest → match against
  the AR image's tags → short-SHA → Cloud Build record → git SHA + trigger + failure. **Verified end-to-end.**
- **AWS images**: App Runner/ECS resolve image by **tag** at config level (thinner) → join to CodeBuild
  `resolvedSourceVersion` for the SHA. ECR carries **no git SHA** on the image itself.
- **Tarball VMs (Lane B)**: the SHA exists in the sidecar manifest + boot log but is **never stamped on the VM registry
  entry** (`git_commit`/`image_digest` are `""` on every live VM; `dep_versions` shows the fake `0.99.0`
  `SETUPTOOLS_SCM_PRETEND_VERSION` constant). This column is honestly _unknown_ until a small pipeline fix lands (see
  "Honest gaps").

## Target shape — /ops/artifacts, 5 views

Reuses the shipped cost-page date-range picker + segmented control; all unknowns render as explicit "unknown + why",
never a fabricated green (the `_image_signal` principle).

1. **What's running** ⭐ (default) — every workload → resolved artifact → digest → matched build → git SHA, with drift
   flags: 🟢 digest/SHA-pinned · 🔴 floating `:latest` · 🔴 hand-deployed · 🟡 stale/behind-green · 🔴 fake-populated
   (the `0.99.0` tarball case) · ⚪ honestly-unknown.
2. **Deploy timeline** — Cloud Run revisions + App Runner/ECS operations: every deploy, its digest, when, by whom;
   change-type = new-code / **config-only** (same digest) / **rollback** (digest reverted) / **failed** (deploy broke
   though the build was green). **Also answers "what was running on date X"** — revision N was live [t_N, t_{N+1}).
3. **Pipeline** — both clouds, both lanes; status, trigger, SHA, branch, started, duration, produced artifact,
   structured failure. Row → detail drawer (step/phase timeline + failure message + log excerpt + cloud-console link).
4. **Artifacts** — AR + ECR + tarball bucket: tags, digest, pushed, size, "running?" badge; surfaces the 1.5 TB sprawl
   and the GCP-SHA-tag vs ECR-version-tag mismatch.
5. **Health** — measured pipeline defects, severity-ranked (the ones in "Codex fixes" + "Pipeline bugs" below).

## Honest gaps (target ≠ producible without extra work — do NOT fake these)

- **Tarball VM runtime SHA** — needs a ~1-line pipeline fix (`_launch_with_tee` exports `GIT_COMMIT` from the parsed
  `_tarball_actual_sha` before `deployment_heartbeat.py register`, OR add a `tarball_sha` field to the registry entry).
  Cheap, but it is CODE in `deployment-service`, not a read. **Belongs to the issue doc / Ikenna's CI area, not this
  page.** Until it lands, the tarball "built from" column is _unknown_.
- **AWS tarball lane** — structurally broken: uploader defaults to `uts-prod-deployment-state` (0 objects in `code/`);
  the EC2 launcher expects `unified-trading-deployment-scripts-427895769566` which does not exist. Separate infra bug.
- **AWS runtime is thinner than GCP** — image resolved by tag not digest; e.g. `uts-deployment-api-prod` (App Runner)
  runs `:latest` and is **PAUSED** today after 2 failed deploys; `uts-defi-prod` (ECS) has 3 services but **0 running
  tasks**. Show honestly.
- **Pre-window history** (older than the API's ~60–72d) is gone unless snapshotted from today. Operator accepts starting
  from today; the snapshot worker makes it forever-durable going forward.

## Prior art to ABSORB then delete (operator decision: absorb + retire)

- `deployment-ui/src/components/CloudBuildsTab.tsx` (per-service, GCP-trigger-centric card list) + its per-service
  `builds` tab mount (`App.tsx`) and `DeployConsole` embed.
- `deployment-api/routes/{cloud_builds,_cloud_builds_*,_code_builds_aws,builds,builds_history}.py` — narrow, duplicated
  (raw Artifact Registry client copy-pasted across `builds.py` + `builds_history.py`). Consolidate into one
  builds/artifacts service; keep the manual-trigger action; port the keyless GCP→AWS WIF pattern.
- `deployment-ui/src/pages/RepoCi.tsx` `ImageCell` + `RepoCiImageSignal` (`client.ts`) — the fleet-wide image signal;
  promote its honest fields (last-success fallback, `deploy_model` source/bundled) into the new page's columns.
- `deployment-api/routes/vm_deployments.py` `VmDeploymentEntryModel` — already carries `image_digest`/`git_commit`
  (empty for tarballs today); reuse for Lane B once the stamp lands.

## Constraints (from the OOM remediation plan — binding)

- 4 GiB ceiling, `WORKERS=2` → any process-local cache exists 2×. Use `deployment_api/utils/bounded_cache.py`
  `BoundedCache(maxsize, ttl)`, never an unbounded dict.
- No Redis / cross-instance tier. The ONE sanctioned shape for an expensive multi-cloud source is **expensive-source →
  periodic GCS snapshot (parquet/JSONL) → cheap local DuckDB/TTL read** (the cost-observability worker). A builds page
  polling the clouds per-request is banned.
- Aggregations use DuckDB-over-Arrow/parquet; never materialize raw fact rows in Python.
- The SWR bounded-key cache (`deployments_inventory.py`, 45s TTL, single-flight, per-provider census timeout) is the
  reference for the live "what's running" census layer.

## Codex fixes (measured drift — correcting is in-scope, post-build)

- `dual-cloud-image-builds.md` says registry `unified-trading` — real is **`unified-trading-system`** (~1.5 TB);
  `unified-trading` returns NOT_FOUND.
- Says images tagged `:<version>` — reality is `:$SHORT_SHA` / `:latest`; version tags stopped ~late June (the
  `version`-never-sent bug below).
- Says triggers `<repo>-<env>` / AWS projects `<repo>-<env>` — reality is `<repo>-build`, `<repo>-feature-build`,
  `<repo>-main-deploy`, `<repo>-live-defi-rollout`, `<repo>-prod`; AWS projects are bare `<repo>`.
- Says "router is the canonical AWS trigger" — a real build showed `initiator: GitHub-Hookshot` (a webhook fired it).
- Says the manifest is the provenance audit trail — `deployed_versions` is empty and `deployed_versions_aws` is absent.

## Pipeline bugs found (page-first: file an issue doc + notify Ikenna, do NOT fix here)

Operator decision 2026-07-17: the page reads the clouds directly so it works regardless of these; fixing them touches
v2-gated CI workflows in Ikenna's current area. Capture in `plans/active/issues/` and notify.

1. `version` never sent in any live `qg-passed` payload → router reads `client_payload.version` with no fallback →
   `IMAGE_TAG=""` → image tags lost their version fleet-wide (corroborated by the AR tag history flip in late June).
2. `deployment-api` per-service Cloud Build history filters on `REPO_NAME` (auto substitution) but the router passes
   `_REPO_NAME` (custom), no fallback → router-triggered builds may be invisible. **UNVERIFIED — I could not reproduce
   it on 5 sampled builds (all had `REPO_NAME` set); needs a confirmed router-triggered build before designing around
   it.**
3. GCP build events never carry `build_id` into the GCS ledger; AWS does.
4. `freeze-deferred-build-replay.yml` filters `startswith("deferred-build-")` → never matches the AWS
   `deferred-aws-build-…` artifact → AWS freeze-deferred builds never replay.
5. Cloud-build-failure-watcher persists the failure reason only as free text in a Slack message and stamps
   `repo: unified-trading-pm` (its own repo), not the repo that failed.
6. Tarball VM BoM never stamped (see Honest gaps) — the runtime-provenance gap.

## Todos

### Phase 0 — shape (done / in flight)

- [x] [OPERATOR] P0. Audit both clouds + 4 codebase audits (pipeline / deployment-api / deployment-ui / tarball lane) —
      all complete; findings captured above.
- [x] [OPERATOR] P0. Mock-first standalone HTML with REAL probed data (5 views: running / deploy-timeline / pipeline /
      artifacts / health) — `scratchpad/artifact-pipeline-mock.html`. Iterating with operator.
- [ ] [OPERATOR] P0. Lock the shape with the operator (default tab, which views ship v1 vs later, any cuts).

### Phase 1 — backend read + snapshot layer (deployment-api)

- [ ] [BACKEND] P1. New `services/artifact_pipeline/` service on the cost-observability shape: providers for Cloud Build
      list/describe, CodeBuild, Artifact Registry, ECR, Cloud Run revisions, App Runner/ECS ops, tarball manifests —
      each wrapped so one cloud's failure never blanks the others. Consolidate the duplicated AR/ECR client code.
- [ ] [BACKEND] P1. Snapshot worker (`scripts/artifact_snapshot_worker.py`, Cloud Scheduler / `POST …/snapshot-run`):
      periodically read the live APIs, append normalized parquet to `gs://{state}/artifact-snapshots/…`; DuckDB-over-
      parquet read path with `BoundedCache`. Honour the OOM constraints; no per-request cloud scans.
- [ ] [BACKEND] P1. The runtime join: workload → resolved digest/tag → matched build → git SHA; drift classifier (pinned
      / floating / hand / stale / fake-populated / unknown). Deployer identity from `serving.knative.dev/creator`.

### Phase 2 — API contract (deployment-api)

- [ ] [BACKEND] P1. Endpoints + Pydantic models (local `# CORRECT-LOCAL` like cost_observability):
      `/api/artifacts/running`, `/deploys`, `/builds`, `/images`, `/health`; date-range params reusing the costs
      `_resolve_range` validation (loud 400 on half/inverted/over-long). Every response echoes the resolved window.
- [ ] [BACKEND] P1. Backend unit tests (route + provider), mocking at the helper/factory level per the repo convention;
      `--block-network` safe.

### Phase 3 — UI page (deployment-ui)

- [ ] [UI] P1. `/ops/artifacts` page (top-level route + NAV_GROUPS entry, or a cockpit tab — decide at shape-lock); 5
      views; reuse the cost-page date-range picker, `Segmented`, `Card`, `Badge`, status pills, the `useRef` reqId
      ordering guard, and the visibility-paused refresh. Unknowns render explicitly.
- [ ] [UI] P1. API client (`deploymentApi.ts` flat-function style) + mock-api handlers (route before any broad wildcard)
      with `__mock*` test hooks mirroring the cost page.
- [ ] [UI] P1. Vitest for the page + `pw:L2` smoke spec (mock-mode) covering each view, the running-drift flags, the
      deploy change-type, and the failure drawer. No UI tick without `pw:L2 ✓` + a cited regression spec.

### Phase 4 — absorb + retire

- [ ] [UI] P2. Port the manual-trigger action into the new page; remove `CloudBuildsTab` from the per-service tab bar +
      `DeployConsole`; delete `CloudBuildsTab.tsx` (no shim). Fold `RepoCi` ImageCell fields into the new columns.
- [ ] [BACKEND] P2. Retire the superseded narrow routes once the new service covers them; delete dead code.

### Phase 5 — codex + issue doc + notify

- [ ] [REVIEW] P2. File `plans/active/issues/artifact_pipeline_metadata_gaps_<date>.md` with the 6 pipeline bugs above;
      **notify the operator / Ikenna** (cross-repo, touches v2-gated CI in Ikenna's area). Verify bug #2 first.
- [ ] [REVIEW] P2. Fix the 5 `dual-cloud-image-builds.md` drifts (registry name, tag convention, trigger/project naming,
      canonical-trigger claim, empty-manifest provenance). Post-phase codex audit.

### Phase 6 — later / optional (stretch)

- [ ] [BACKEND] P3. _(stretch, optional)_ "Built but never deployed" + build→deploy latency (join build digest to the
      first revision that ran it).
- [ ] [INFRA] P3. _(stretch, optional)_ Image vulnerability-scan status (AR + ECR native scanning) + orphaned-image GC
      candidates (no matching build AND not running) — ties to the 1.5 TB and the cost page.
- [ ] [INFRA] P3. _(stretch, optional)_ Deploy-churn / crash-loop signal (e.g. uts-shared-deployment-api redeployed ~14×
      in hours; ~40% config-only) surfaced as a health condition.

## Progress log

- **2026-07-17** — Audit + mock complete. Both clouds probed live; 4 code audits done. Operator decisions captured:
  scope = images + tarballs (artifact pipeline); absorb+retire CloudBuildsTab; page-first (bugs → issue doc); human
  plan. Mock at `scratchpad/artifact-pipeline-mock.html` (real probed data; 2 fabricated attributions caught + fixed;
  bug #2 demoted to UNVERIFIED). Deploy-timeline view + churn/rollback/failed-deploy signals added after the feasibility
  grill confirmed Cloud Run revisions are a free 72-day per-deploy history. Feasibility verdict: producible + cheap
  (cents/yr) + ~60–72d already retained. **Shape not yet locked; no page code started.**
