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

> **Human / local plan** (`assigned_vm: NA`, never AO-ingested). Operator-driven in an interactive session. This plan
> REFERENCES the codex SSOTs below; it does not duplicate them.

> 🔴 **WORKING MODE — DO NOT START IMPLEMENTATION** (operator, 2026-07-20). We are **far** from building this. The
> agreed process is: **review each tab in the mock, one at a time; a tab is only finalised when the operator signs it
> off; real work starts only after ALL tabs are finalised.** Until then the mock is the only UI artifact, and every
> decision/finding goes into THIS plan so nothing is forgotten. **Phases 1–6 below are BLOCKED on the Phase 0 tab review
> completing** — they are written up in advance deliberately (so the design is captured while it is fresh), NOT because
> they are ready to pick up. Do not begin backend or page code, and do not treat an unchecked Phase-1 todo as available
> work.

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

| Source                      | Depth (measured)                                                                                                                | Carries                                                            | Read cost |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | --------- |
| **Cloud Run revisions**     | back to **2026-05-06** (72d; 192/svc)                                                                                           | image, **resolved digest**, deploy time, deployer                  | free      |
| **Cloud Build history**     | back to **2026-05-19** (60d; 2000+)                                                                                             | SHA, trigger, branch, **structured failureInfo**, steps            | free      |
| **AWS CodeBuild**           | 400+ builds/project                                                                                                             | SHA, phases[].contexts[] failure, initiator                        | free      |
| **Artifact Registry / ECR** | all live images                                                                                                                 | digest, tags, pushed-at, size                                      | free      |
| **App Runner / ECS**        | operation history incl. **FAILED**                                                                                              | image (by tag), deploy status + time                               | free      |
| **Tarball manifests (GCS)** | **4064 manifests / 163 tarballs**, from 2026-05-17, **no lifecycle rule on `code/`** (unlimited retention; cleanup cron PAUSED) | commit_sha (full), pyproject_version, created_at, git_status_clean | free      |

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

1. **What's running** ⭐ (default) — **the row unit is `service × artifact version`, NOT one row per host** (operator
   2026-07-17). The estate is an ephemeral VM fleet, so a per-host table is both noisy and a duplicate of the
   Deployments page, which owns the host census. Each row = one code version actually live, its resolved digest, the
   matched build → git SHA, the **host count**, and the age of the oldest host on it. **Expandable to the host list.**
   - Drift flags: 🟢 digest/SHA-pinned · 🔴 floating `:latest` · 🔴 hand-deployed · 🟡 stale/behind-green · 🔴
     fake-populated (the `0.99.0` tarball case) · ⚪ honestly-unknown · 🟠 **fragmented** (N versions of ONE service
     live at once) — plus a tab-level "N services running >1 version right now".
   - **Why fragmentation is the headline signal, not a nicety**: a Cloud Run service rolls forward, but **a VM never
     updates itself** — a VM launched 3 days ago runs 3-day-old code for its whole life. So a fix shipped today does NOT
     reach VMs launched before it, and they keep writing pre-fix data. That is a data-correctness concern
     (`codex/02-data/data-pipeline-correctness-hard-rule.md`), not a tidiness one, and nothing surfaces it today.
     MEASURED live 2026-07-17: 13 running VMs, with 4 `features-sports` VMs in two cohorts launched ~7h apart.
   - **Cross-links (operator requirement)**: a version row deep-links into the **Deployments view with a pre-loaded
     filter** showing only the hosts on that image/tarball, and out to the **GCP/AWS console** where that build ran (+
     its logs) so the operator can verify it is the right artifact. Both require work on the Deployments side — see
     Phase 3b.
2. **Deploy timeline** — Cloud Run revisions + App Runner/ECS operations: every deploy, its digest, when, by whom;
   change-type = new-code / **config-only** (same digest) / **rollback** (digest reverted) / **failed** (deploy broke
   though the build was green). **Also answers "what was running on date X"** — revision N was live [t*N, t*{N+1}).
3. **Pipeline** — both clouds, both lanes; status, trigger, SHA, branch, started, duration, produced artifact,
   structured failure. Row → detail drawer (step/phase timeline + failure message + log excerpt + cloud-console link).
4. **Artifacts** — AR + ECR + tarball bucket: tags, digest, pushed, size, "running?" badge; surfaces the 1.5 TB sprawl
   and the GCP-SHA-tag vs ECR-version-tag mismatch.
5. **Health** — measured pipeline defects, severity-ranked (the ones in "Codex fixes" + "Pipeline bugs" below).

## Honest gaps (target ≠ producible without extra work — do NOT fake these)

- **Tarball VM runtime SHA — NOW IN SCOPE** (operator 2026-07-17, supersedes the earlier "issue-doc only" call). Today
  `git_commit`/`image_digest` are `""` on every live VM, so the fragmentation view — the single most valuable thing for
  the VM fleet — is unresolvable. Operator approved **both** paths, with a clear split:
  - **(A) MEASURED, going forward — THE ONLY PATH** (audit-cleared, Phase 3c). Stamp the real commit on the registry
    entry at launch. Anything launched after it lands shows a measured value.
  - ❌ **(B) INFERRED — EVALUATED AND DROPPED (operator decision 2026-07-17).** The proposal was to reconstruct a commit
    by joining a VM's launch time against the tarball manifest timeline. The audit put the honest ceiling at _"probably
    this commit, ±one 30-minute refresh window, per repo, for VMs launched in the last 30 days"_, and found a
    disqualifying flaw: `started_at` is recorded **after** the tarball download, so the join runs against the wrong
    timestamp and is biased toward the wrong answer. Compounding limits: the floating manifest is overwritten each
    rebuild, a VM installs several tarballs (a per-repo vector, each independently ambiguous), `deployments/archive/`
    expires at 30 days, and `--allow-dirty-tarball` builds carry a `commit_sha` that does not describe the shipped
    bytes. **Decision: do not build it.** A number that looks precise and isn't is worse than an honest blank — so
    pre-(A) VMs render as ⚪ **unknown**, with the reason, and simply age out as the fleet recycles.
  - 🔴 **HARD CONSTRAINT (operator), SATISFIED**: (A) must NOT break the CD flow that works today — VMs boot and pull
    the _current latest_ tarball, and that must keep working unchanged. "Making changes for this feature is okay, but
    not at the cost of breaking something that is working right now." The Phase 3c audit returned
    **YES-WITH-CONDITIONS** and confirmed structurally that **no tarball naming or path change is required** — the
    change only reads a value the boot already downloads, parses, and currently discards.
- **AWS tarball lane — broken at TWO independent points** (re-verified 2026-07-17; an earlier draft of this plan framed
  this wrongly as an uploader/launcher bucket disagreement — the uploader and the AWS setup script actually **agree** on
  `uts-prod-deployment-state`). The real findings: (1) `s3://uts-prod-deployment-state/code/` is **EMPTY** (0 objects;
  only a `scratch/` prefix exists) — the AWS uploader lane appears never to have run, or its output was deleted; and (2)
  `launch-ec2-vm.sh:272` resolves via `lc_aws_code_bucket` → `unified-trading-deployment-scripts-427895769566`, which
  **does not exist** (head-bucket 404), and 9 AWS launchers use that path. **The GCP lane is entirely unaffected.** Out
  of scope here — do NOT conflate it with the GCP stamp change.
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

- **CORRECTED 2026-07-17 (measured from `deployment-api/cloudbuild.yaml:427-429`)**: the deployed ceiling is **16 GiB /
  `--cpu 4` / `WORKERS=2`**, raised from 8 GiB on 2026-07-17 after an OOM (8585 MiB vs an 8192 limit) driven by the
  **data-status** page, not the deployments inventory. An earlier draft of this plan said "4 GiB", quoting decision D2
  of the OOM remediation plan — **that plan is now stale against the deployed config**; trust `cloudbuild.yaml`. (Drift
  worth raising separately against that plan.) The discipline below still stands — the budget is just not the binding
  constraint it was assumed to be.
- `WORKERS=2` → any process-local cache exists 2×. Use `deployment_api/utils/bounded_cache.py`
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
7. **AWS App Runner: both prod services PAUSED after a 13-failure deploy storm on 2026-05-22** (NEW, measured live
   2026-07-21). `uts-deployment-api-prod` = 7 of 9 ops FAILED; `uts-alerting-service-prod` = 6 of 8 FAILED incl. a
   failed `CREATE_SERVICE`. Both ended `PAUSE_SERVICE` at 14:38Z. The builds were green — the **deploys** broke, a class
   the build feed can't see. Evidence: `aws apprunner list-operations`. (deployment-api-prod was already a known gap;
   the second paused service + the true failure count are the new facts.)
8. **AWS ECR estate is orphaned — 0 of 20 repos have a running task** (NEW, measured live 2026-07-21). 2 App-Runner
   PAUSED, 3 ECS `uts-defi-prod` at `desired=0`, the other 15 have no AWS runtime; 4 repos are **empty** (0 images:
   risk-and-exposure-service, unified-trading-system, position-balance-monitor-service, deployment-ui); **18 of 20 last
   pushed 2026-06-27** — AWS image builds went quiet that day; only `market-tick-data-service` still pushes and it is
   `latest`-only (no version tag → corroborates bug #1). ~393 images retained, nothing serves them. Evidence:
   `aws ecr describe-images` + App Runner/ECS state.
9. **~40% of Cloud Run deploys ship nothing** (config-only redeploys, same digest) — churn that reads as activity; cheap
   to flag, noise unlabelled. Evidence: Cloud Run revision digests for `uts-shared-deployment-api` (192 revs).

## Todos

### Phase 0 — shape (done / in flight)

- [x] [OPERATOR] P0. Audit both clouds + 4 codebase audits (pipeline / deployment-api / deployment-ui / tarball lane) —
      all complete; findings captured above.
- [x] [OPERATOR] P0. Mock-first standalone HTML with REAL probed data (5 views: running / deploy-timeline / pipeline /
      artifacts / health) — shipped at `deployment-ui/public/design-mocks/artifact-pipeline.html`
      (deployment-ui@479f8c2), viewable at `/design-mocks/artifact-pipeline.html`. **Temporary — delete the folder when
      the real page ships.** Iterating with operator.
- [x] [OPERATOR] P0. Shape locked with the operator 2026-07-17 — **top-level `/ops/artifacts`** (not a cockpit tab),
      **all 5 views in v1**, **default view = What's running**.
- [x] [OPERATOR] P0. ✅ Rebuilt "What's running" on the service × version model — `deployment-ui@3fcc112` +
      collapsible-groups follow-up. Row unit is now service × artifact version with an expandable host list, a
      `fragmented` flag, cross-links, collapsible service groups and an expand/collapse-all control. Stat tiles are
      computed from the data (a check caught hand-written numbers disagreeing with the table). Interactions verified in
      a real DOM (jsdom), not just eyeballed.

**Per-tab review gate — real work starts only when ALL of these are signed off:**

- [x] [OPERATOR] P0. **Tab 1 — What's running** — reviewed 2026-07-20; rebuilt to service × version + collapsible +
      **build-datetime column**. _Awaiting final sign-off._ Review findings folded in (drive the real page from these):
  - **Row unit** = service × artifact version, expandable host list, collapsible service groups + expand/collapse-all.
  - **"Built from · when" column** (operator ask): each row shows the artifact's creation time, because a SHA points to
    a commit but not a date. Images → Artifact Registry `createTime`; tarballs → **"frozen at launch"** (a VM never
    self-updates, so its code is frozen at boot; the exact tarball `created_at` is unresolvable until the stamp — this
    is a THIRD concrete argument for the stamp, alongside the missing commit and the fragmentation risk). Once (A)
    lands, tarball rows get a real build time from the manifest `created_at`.
  - **Artifact-type + pin-strength must be legible in the real page** (operator asked what the raw strings meant — the
    mock made them decode it). Teach the two ladders explicitly:
    `image: :latest (floating) → :sha (tag, traceable) → @sha256 (digest, provable)` and
    `tarball: x.tar.gz (floating) → x@sha.tar.gz (pinned)`. The SHA-tag is legible-but-mutable; the digest is
    immutable-but-opaque-to-the-commit (so a digest-pinned row shows `Built from = unknown` even though its build time
    is known). Consider a per-row type/pin chip + a one-line legend of the ladders.
  - **Stat tiles computed from data**, not hand-written (a check caught them disagreeing). Do the same in the real page
    — derive counts server-side, never hardcode.
  - Data source for build-time is confirmed available (image `createTime`, manifest `created_at`); a couple of GCP
    createTimes in the MOCK are deploy-derived only because gcloud auth expired mid-session — a non-issue for the real
    backend (it holds live creds).
- [ ] [OPERATOR] P0. **Tab 2 — Deploy timeline** — iterated (correctness + usefulness pass), awaiting operator review.
      `ui@e01e5fc`. Was one-service (uts-shared-deployment-api) + 4 static AWS rows; now **estate-wide** across 5 real
      sections: Cloud Run for that service (15 revs, each with a computed **held-for** interval so "what ran on date X"
      is a lookup) + other Cloud Run services + **GCE VM launches (a launch IS the tarball-lane deploy)** + the real AWS
      App Runner storm + ECS. New surfaces: **● live-now** badges, **human-vs-CI deployer** column (hand-deploys lit
      red), **config-only / new-code / live-now / failed** filter chips, per-row **console↗ / VM↗** links, and
      `resolve ↗` where a digest→SHA join exists but the value needs a fresh gcloud auth.
- [ ] [OPERATOR] P0. **Tab 3 — Pipeline** — iterated, awaiting review. `ui@e01e5fc`. Added **All / Failed / Image /
      Tarball / GCP / AWS** filter chips, surfaced the previously-dead `xlane` flag as a **⇄ both-lanes** badge (one
      commit built as image AND tarball), and a **shipped ↗** through-line hint on successful image builds. Drawer (step
      timeline + failure + log excerpt) unchanged.
- [ ] [OPERATOR] P0. **Tab 4 — Artifacts** — iterated, awaiting review. `ui@e01e5fc`. Was 8 image rows for 2 repos; now
      **one row per repo** showing the real sprawl (**ECR inventory probed live 2026-07-21**): 20 repos, image counts,
      latest tags, last-push, **running? + state** (running / App-Runner-PAUSED / ECS-desired=0 / orphaned-GC / empty /
      still-pushing), with **running / orphaned-GC / empty / cloud** filters. GCP AR kept as the 2026-07-17 sample + an
      honest aggregate row (full AR walk needs gcloud auth).
- [ ] [OPERATOR] P0. **Tab 5 — Health** — iterated, awaiting review. `ui@e01e5fc`. Folded in 3 new **measured**
      deploy-lane findings (App Runner storm, orphaned ECR estate, ~40% config churn → 13 conditions), added severity
      **tiles + filter**, an **Area** column, and a **"see in <tab> ↗"** cross-link from every condition to the view
      that proves it. Note now states none of these fires an alert today.
- [ ] [OPERATOR] P0. **Final sign-off on the whole mock** → unblocks Phases 1–6.

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

- [ ] [UI] P1. `/ops/artifacts` **top-level route + NAV_GROUPS entry** (shape locked by operator 2026-07-17: top-level,
      all 5 views in v1, default view = What's running); reuse the cost-page date-range picker, `Segmented`, `Card`,
      `Badge`, status pills, the `useRef` reqId ordering guard, and the visibility-paused refresh. Unknowns render
      explicitly.
- [ ] [UI] P1. "What's running" as **service × version rows with an expandable host list** (not one row per host) + the
      `fragmented` flag and the tab-level ">1 version live" counter.
- [ ] [UI] P1. API client (`deploymentApi.ts` flat-function style) + mock-api handlers (route before any broad wildcard)
      with `__mock*` test hooks mirroring the cost page.
- [ ] [UI] P1. Vitest for the page + `pw:L2` smoke spec (mock-mode) covering each view, the running-drift flags, the
      deploy change-type, and the failure drawer. No UI tick without `pw:L2 ✓` + a cited regression spec.

### Phase 3b — cross-links (deployment-ui + deployment-api) — operator requirement 2026-07-17

- [ ] [BACKEND] P1. Carry the image/tarball version on the Deployments inventory row so it can be filtered on.
      **Additive only** — `DeploymentItem` today carries no image URI / digest / commit; adding fields must not break
      any existing consumer or field-set assertion. Respect the 45s SWR cache + the 4 GiB / WORKERS=2 budget (report the
      payload delta before shipping). **AUDITED 2026-07-17 — cheaper than assumed: the data is already in hand.**
      `DeploymentRegistryEntry` already declares `image_digest`/`git_commit`
      (`unified_trading_library/deployment_registry.py:205-206`) and `_vm_item()` (`deployments_inventory.py:689-721`)
      **already receives that entry object** — it simply never copies the fields onto the row. So this is a ~2-line
      addition with **zero new I/O / census cost**; no join to write. Payload delta measured at **<20 KB** across ~200
      targets. `_unmanaged_vm_item` (live-GCE-but-unregistered) correctly stays `None`. **No test anywhere asserts a
      closed field set**, so additive fields are safe.
- [ ] [UI] P1. Deployments view accepts a **pre-loaded filter via URL param** (e.g. `?git_commit=<sha>`), so an
      /ops/artifacts version row deep-links to exactly the hosts running that artifact. **AUDITED — the page was built
      for this**: every filter already reads `useSearchParams()` via one `setParam` helper, and the module docstring
      states the intent ("ALL filters are URL-backed … so alert deep-links and shareable filtered views work"). Taken
      params: `umbrella / cloud / status / asset_group / kind / launched_by / region / detail` — pick a fresh name and
      follow the `kind` filter pattern (`Deployments.tsx:1202-1226`). Note **no page currently deep-links into the
      Deployments LIST with a preset filter** — this would be the first consumer of an existing-but-unused capability.
      Also surface `git_commit`/`dep_versions` in `VmDeploymentDetails.tsx`, which today renders neither despite the
      wire model carrying them (dead fields).
- [ ] [UI] P2. **Console deep-links** out to where the build ran + its logs — GCP Cloud Build (`logUrl` is on the build
      record), Artifact Registry, AWS CodeBuild (CloudWatch `deepLink`), ECR, and the GCE instance — so the operator can
      verify an artifact is the right one. **AUDITED — reuse `consoleUrl(item)` at `DeploymentDetail.tsx:216-262`**: an
      existing pure-URL-construction helper with a `switch (item.kind)` already covering VM (GCE + EC2), Cloud Run
      job+service, Cloud Function, ECS, Lambda across both clouds. Build log URLs come straight off the build API
      (`log_url`), not hand-built. **Gap: no Artifact Registry / ECR link builder exists** — write that one fresh,
      following `consoleUrl`'s pattern.

### Phase 3c — tarball commit tracking (AUDIT-GATED — must not break CD)

- [x] [REVIEW] P0. ✅ Blast-radius audit DONE 2026-07-17 — **VERDICT: YES, WITH CONDITIONS.** Blast radius measured as
      **zero**: `git_commit` is a write-mostly string with no validating, alerting, reconciling, deduplicating, or QG
      consumer anywhere in the workspace (all 56 candidate files grep-then-READ); `deployment-ui` has **zero** reads of
      it. The populated round-trip is already covered by a passing test
      (`deployment-api/tests/unit/test_vm_deployment_bom.py:73-87`); nothing relies on emptiness except two
      defaults-tests and one cosmetic `"unknown"` on an unrelated registry (`monitor.short_commit`). **Key finding — the
      commit is already measured and then thrown away**: `setup-data-pipeline-vm.sh:613-615` parses and logs
      `_tarball_actual_sha` at boot, but `/var/log/vm-setup.log` only reaches GCS via the failure EXIT trap
      (early-returns on `rc == 0`), so on a SUCCESSFUL boot it is discarded (probe: recent `vm-logs/<vm>/` hold only
      `run.log`). **No naming/path change is required** — SHA-pinned immutable tarballs (`<name>@<sha>.tar.gz`, selected
      by `*_TARBALL_SHA` VM metadata, fail-closed) ALREADY exist and 5 launchers already use them.
- [ ] [INFRA] P1. **(A) measured stamp** — 2 additive shell edits in `setup-data-pipeline-vm.sh`, **zero Python
      changes**: accumulate `_tarball_actual_sha` in the download loop (`:604-648`), then `export GIT_COMMIT` inside
      `_launch_with_tee()` (`:876-948`) next to the existing `VM_NAME`/`VM_TASK` exports. `GIT_COMMIT` is already the
      first `AliasChoices` entry on `DeploymentConfig.git_commit`, so `resolve_deployment_bom()` picks it up unchanged.
      **CONDITIONS (all binding):** (1) 🔴 the file runs under `set -euo pipefail` — write
      `if [[ -n … ]]; then export     …; fi`, **never** a trailing `[[ … ]] && export` as a function's last statement
      (returns non-zero → propagates → would break EVERY VM boot at once); place it mid-block. (2) Set `GIT_COMMIT`
      only; leave `IMAGE_DIGEST` unset — there is no image on this path and `bom.py:58-69` deliberately refuses to
      invent a digest. (3) Never abort a boot on a missing/garbage SHA — degrade to today's `""`. (4) Do NOT use
      `extras` as the carrier — `vm_deployments.py:114` pops it, making it invisible to the API and both UIs. (5)
      Document the semantics precisely: on the floating path the value means "the manifest `commit_sha` this VM read at
      boot", **not an attestation of the running bytes** (the `*/30` refresh cron can land between the tarball and
      manifest `gsutil cp` calls). (6) Keep inferred values out of this field. (7) Do NOT touch the AWS lane in the same
      change. **VERIFICATION GATE — no existing CI covers this file** (bash uploaded straight to GCS, never executed in
      CI; `deployment-service/quality-gates.sh` will NOT catch a `set -e` regression). Must verify with a **live
      launch**: fire one cheap `EPHEMERAL_BATCH` VM, run the codex T+10min check, and assert a registry row appears in
      `deployments/active/` with a **non-empty `git_commit`**. Add a unit test that `resolve_deployment_bom` reads
      `GIT_COMMIT` from env (covers the Python half; the real risk is the shell half).

> ❌ **Option (B) — inferred-from-manifest-timeline — is DROPPED** (operator decision 2026-07-17). Rationale recorded
> under "Honest gaps" above. Pre-(A) VMs render as ⚪ **unknown with the reason**, and age out as the fleet recycles. Do
> not reintroduce an inferred commit into `git_commit`.

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

- [ ] [INFRA] P3. _(stretch, optional)_ **Fleet-wide SHA-pinning — upgrades the tarball answer from _plausible_ to
      _proven_.** The pin lane already exists and is fail-closed (`<name>@<sha>.tar.gz` + self-verifying manifest check,
      `setup-data-pipeline-vm.sh:620-644`), with 5 launchers using it. Extending it fleet-wide makes the recorded commit
      an attestation of the running bytes rather than "what the manifest said at boot". **Hazard**: the codex documents
      a 2026-06-01 incident where pinned fan-out tarballs were pruned seconds after upload, killing 20 VMs (exit 2).
      Currently dormant — `uts-prod-tarball-cleanup-cron` is PAUSED and there is no lifecycle rule on `code/` — but any
      revival of pruning must be reconciled with this first. Separate, larger change; do NOT bundle with (A).
- [ ] [REVIEW] P3. _(stretch, optional)_ Issue doc — **the whole VM tarball path bypasses `resolve_bucket_name()`** and
      hardcodes `deployment-scripts-central-element-323112` (`setup-data-pipeline-vm.sh:47`,
      `create-code-tarballs.sh:45`, ~48 launchers), contradicting both the workspace storage rule and the codex SSOT's
      own description of this path. Combine with the two-point AWS-lane breakage into one deployment-bucket-resolution
      issue doc.
- [ ] [BACKEND] P3. _(stretch, optional)_ "Built but never deployed" + build→deploy latency (join build digest to the
      first revision that ran it).
- [ ] [INFRA] P3. _(stretch, optional)_ Image vulnerability-scan status (AR + ECR native scanning) + orphaned-image GC
      candidates (no matching build AND not running) — ties to the 1.5 TB and the cost page.
- [ ] [INFRA] P3. _(stretch, optional)_ Deploy-churn / crash-loop signal (e.g. uts-shared-deployment-api redeployed ~14×
      in hours; ~40% config-only) surfaced as a health condition.

## Progress log

- **2026-07-17** — Audit + mock complete. Both clouds probed live; 4 code audits done. Operator decisions captured:
  scope = images + tarballs (artifact pipeline); absorb+retire CloudBuildsTab; page-first (bugs → issue doc); human
  plan. Mock shipped to `deployment-ui/public/design-mocks/artifact-pipeline.html` (deployment-ui@479f8c2, viewable at
  `/design-mocks/artifact-pipeline.html`; temporary, delete-when the real page ships) — real probed data; 2 fabricated
  attributions caught + fixed; bug #2 demoted to UNVERIFIED. Deploy-timeline view + churn/rollback/failed-deploy signals
  added after the feasibility grill confirmed Cloud Run revisions are a free 72-day per-deploy history. Feasibility
  verdict: producible + cheap (cents/yr) + ~60–72d already retained.
- **2026-07-17 (later)** — **Shape LOCKED**: top-level `/ops/artifacts`, all 5 views in v1, default = What's running.
  Operator review of the running tab surfaced a **real design defect**: the row unit was per-workload, collapsing the
  whole VM fleet into one row — misleading at fleet scale (measured: 13 live VMs, incl. 4 `features-sports` in two
  cohorts ~7h apart, i.e. two code versions live in one service). Row unit changed to **service × artifact version with
  an expandable host list**, plus a `fragmented` flag; rationale is data-correctness (a VM never self-updates, so a fix
  shipped today never reaches VMs launched before it). Operator added: deep-link a version row into **Deployments with a
  pre-loaded filter** (needs additive Deployments-side work — Phase 3b) and out to the **GCP/AWS console + build logs**
  for verification. Tarball commit tracking moved **into scope**: (A) measured stamp going forward + (B) inferred from
  the manifest timeline for historic only — **gated on a blast-radius audit** (Phase 3c) under the operator's hard
  constraint that the working latest-tarball CD flow must not break. Two read-only audits dispatched (tarball
  blast-radius; Deployments filter support).
- **2026-07-17 — BOTH AUDITS LANDED.** Tarball verdict **YES-WITH-CONDITIONS**: blast radius measured zero, the change
  is 2 shell lines + 0 Python, no naming/path change, and the commit is _already_ parsed at boot and thrown away. The
  single real risk is a `set -e` regression in `setup-data-pipeline-vm.sh` — which **no CI gate covers** (bash uploaded
  straight to GCS, never executed in CI), so the verification gate is a live `EPHEMERAL_BATCH` launch, not a test run.
  Option (B) came back **weaker than assumed** (±30-min window, wrong-side timestamp, per-repo vector, 30-day archive
  expiry) and may not be worth building now that (A) is cheap. Deployments audit: the cross-link is **cheaper than
  assumed** — provenance is already in hand in `_vm_item()` (~2 lines, zero new I/O), the page is already fully
  URL-param-backed by design, and `consoleUrl()` already exists to reuse.
- **2026-07-17 — three corrections to earlier claims in this plan** (all fixed above): (1) the memory ceiling is **16
  GiB**, not 4 — I had quoted a stale decision from the OOM plan instead of the deployed `cloudbuild.yaml`; (2) the AWS
  tarball lane's uploader and setup script **agree** on the bucket — the real breakage is an empty `code/` prefix plus a
  _different_ nonexistent bucket in the EC2 launcher; (3) manifest/tarball counts corrected to **4064 / 163**. Also: the
  `0.99.0` `dep_versions` value is an **honest** report of a deliberately-pinned `SETUPTOOLS_SCM_PRETEND_VERSION`
  constant (`setup-data-pipeline-vm.sh:703`, because tarballs ship without `.git`) — it carries zero provenance, but the
  BoM is not lying; the mock's wording must reflect that distinction.
- **2026-07-17 — operator DROPPED option (B) entirely.** Only (A), the measured stamp, gets built. Pre-(A) VMs render as
  ⚪ unknown-with-reason rather than carrying a falsely-precise inferred commit, and age out as the fleet recycles.
- **2026-07-20/21 — Tab 1 iterated + signed-off-pending.** Rebuilt to service × version with expandable hosts, made
  service groups collapsible + an expand/collapse-all control (verified in jsdom), and added the "Built from · when"
  build-datetime column (operator ask). Interactions and stat tiles verified against the data, not eyeballed. All tab-1
  review findings folded into the per-tab gate item above. **No page code started — still mock-only, per the working
  mode banner.**

## Lessons this session (so they are not re-learned the hard way)

- **Verify a push landed by CONTENT on origin, not by a push exit code or an is-ancestor check.** A retry loop reported
  "landed" falsely: `git pull --rebase --autostash` popped a _staged_ edit back as _unstaged_, the loop's conditional
  `git commit` then had nothing staged, and the `merge-base --is-ancestor HEAD origin` check passed anyway (HEAD was the
  pulled tip). Fix: after an autostash pop, **re-stage by name before committing**, and gate success on
  `git show origin/<branch>:<file> | grep <expected-content>`. Every ship in this session's later half uses that
  content-gated loop.
- **Compute UI stat tiles from the data; never hand-write them.** A consistency check caught the running-tab tiles
  (claimed 3 fragmented / 11 floating / 3 hand) disagreeing with the rendered rows (real: 4 / 19 / 2), and caught a row
  silently dropped in a rebuild. The real page must derive these server-side.
- **Do not fabricate data to fill a cell.** GCP `gcloud` auth expired mid-session (measured: "Reauthentication failed …
  cannot prompt"); AWS still worked. Two image build-dates I could not re-pull render `n/a — re-auth` rather than a
  made-up date. A `gcloud auth login` on the operator side refills them; the real backend holds live creds so this is a
  mock-only gap.
- **Three earlier claims I made were wrong and are corrected above** — do not let the stale versions survive: memory
  ceiling is **16 GiB** not 4 (I quoted a stale plan decision over the deployed `cloudbuild.yaml`); the AWS tarball
  uploader/setup-script **agree** on the bucket (the breakage is an empty prefix + a different nonexistent bucket); and
  the `0.99.0` `dep_versions` value is an **honest** constant (`SETUPTOOLS_SCM_PRETEND_VERSION`), not the BoM lying.
- **The tarball-audit agent's completion record was lost across a compaction** — its findings had already been folded
  into the plan, but I re-verified every load-bearing Lane-B claim with a fresh live probe rather than trusting them.
  Treat any pre-compaction agent finding as unverified until re-probed.

## Deferred work after 2026-07-21

**Recommended NEXT: operator reviews the iterated Tabs 2–5 in the mock** (`ui@e01e5fc`) — all four had the correctness +
usefulness pass applied this turn and now await scrutiny; that review is the only unblocked forward step. Everything
below whole-mock sign-off is deliberately not started.

| Item                                                    | State / why deferred                                                                                                                                     | Blocked on                            |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Tab 1 final sign-off                                    | **Operator-owned** — reviewed + iterated, awaiting the green tick                                                                                        | operator                              |
| Tabs 2–5 mock review (Deploy/Pipeline/Artifacts/Health) | **Operator-owned** — iterated this turn (correctness + usefulness), awaiting operator scrutiny                                                           | operator                              |
| Whole-mock final sign-off                               | **Operator-owned** — the gate that unblocks all implementation                                                                                           | tabs 1–5 signed off                   |
| Phase 1–6 implementation (backend, page, absorb, codex) | **Cannot be done yet** — gated by the mock sign-off above                                                                                                | whole-mock sign-off                   |
| (A) tarball commit stamp                                | **Cannot be done yet** — audit-cleared YES-WITH-CONDITIONS, but part of Phase 3c; verify via a live EPHEMERAL_BATCH launch (no CI covers the shell file) | mock sign-off + Phase 3c start        |
| Fill the mock's 2 `n/a — re-auth` build dates           | **Cannot be done yet** — needs a fresh GCP `gcloud auth login`                                                                                           | operator re-auth (optional, cosmetic) |
| Issue doc: 9 pipeline bugs + bucket-resolution bypass   | **Not done** — Phase 5 todo; now 9 (added AWS App Runner storm, orphaned ECR estate, config churn — all measured 2026-07-21); notify Ikenna (CI-area)    | nobody — but coordinate w/ Ikenna     |
