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
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [infrastructure]; the deployment-ui
  # /artifacts page itself (repos: deployment-ui, deployment-api only) -- still cited from
  # infra_consolidated_closeout_2026_07_25.md as a cross-tranche mention, which is fine (same pattern as any
  # other tranche's Sources list citing a doc it doesn't primarily own)
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
    /plans/active/deployment_registry_firestore_migration_2026_07_14.md,
    /plans/active/ui_satellite_ao_dispatch_batch5_2026_08_21.md,
    /plans/archive/artifact_pipeline_observability_history_2026_08_21.md,
  ]
created: "2026-07-17"
last_updated: "2026-08-17" # corrected 2026-08-19 plan-reconcile, was stale vs own Progress Log
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
context_scope: [/codex/05-infrastructure/dual-cloud-image-builds.md, /codex/05-infrastructure/vm-tarball-deployment.md, /codex/06-coding-standards/ui-testing-layers.md, deployment-api/deployment_api/services/artifact_pipeline, deployment-ui/src/pages/ArtifactPipeline.tsx]
---

# Artifact pipeline observability — build → artifact → deploy lineage

> **Human / local plan** (`assigned_vm: NA`, never AO-ingested). Operator-driven in an interactive session. This plan
> REFERENCES the codex SSOTs below; it does not duplicate them.

> 🟢 **WORKING MODE — BUILD STARTED** (operator sign-off 2026-07-21). The whole-mock review is COMPLETE: **all 5 tabs
> signed off** ("good to start … on all the tabs 1 to 5"; remaining refinements land when live API data flows), and the
> AWS-lane framing CONFIRMED ("what's broken is broken; we'll fix AWS when we need AWS"). **Phases 1–6 are now UNBLOCKED
> and in build** — the full `/ops/artifacts` page, all 5 views, on the cost-observability architecture. The tarball SHA
> stamp (Phase 3c Option A) is **IN scope** for this build (operator: "do it now"). The mock
> (`deployment-ui/public/design-mocks/artifact-pipeline.html`) is the frozen design reference until the real page ships
> — then the whole `design-mocks/` folder is deleted (its Delete-when).

## Why

The build pipeline is dual-cloud and busy (GCP Cloud Build → Artifact Registry, AWS CodeBuild → ECR; a separate VM
code-tarball lane). It **emits** rich per-build/per-deploy metadata but **persists almost none of it durably**, and
nothing today answers the question that matters most — _"what is each workload actually running right now, and where did
it come from?"_ The existing `_image_signal` (RepoCi) answers the **image-level** question ("is main's code built into
the latest image?") and was explicitly scoped "v1 image-level, not runtime-level". This page is the runtime layer + a
real cross-cloud build/deploy feed, so the deployment estate's final stage becomes legible.

## Codex SSOTs (read + keep this plan aligned — plan↔codex drift is review-blocking)

- `/codex/05-infrastructure/dual-cloud-image-builds.md` — the image build flow (routers, registries, promote gate,
  provenance). **NOTE: this doc has measured drift — see "Codex fixes" below. Correcting it is in-scope.**
- `/codex/05-infrastructure/vm-tarball-deployment.md` — the tarball lane (Lane B).
- `/codex/05-infrastructure/cloud-agnostic-build-lineage.md` — STUB; the aspirational SHA→dual-cloud-parity model. This
  page is the pragmatic first cut of the "trace an artifact to a SHA" goal.
- `/codex/06-coding-standards/ui-testing-layers.md` — the pw:L2 gate (no UI tick without `[UI]` + `pw:L2 ✓` + a cited
  regression spec).
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — for the snapshot worker.
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
     (`/codex/02-data/data-pipeline-correctness-hard-rule.md`), not a tidiness one, and nothing surfaces it today.
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

## Pipeline bugs found (page-first: parked in an issue doc, do NOT fix here)

Operator decision 2026-07-17/21: the page reads the clouds directly so it works regardless of these; fixing them touches
CI files in Ikenna's active area → **parked, not fixed.** **RE-VERIFIED 2026-07-21 (the CI area was actively fixed
2026-07-20) and filed:** `plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`.
Most of the 2026-07-17 list resolved itself — see the issue doc for the full verified status. Summary:

1. `version` never sent → image tags SHA-only ~late June. **RESOLVED — root cause CONFIRMED 2026-07-24 (operator)**: the
   semver-agent that would compute + send `version` in the build dispatch payload is **dead, deliberately** — "we have
   kept it dead deliberately." SHA-only tagging is the expected, intentional consequence, not a defect. **Not a bug** —
   the issue doc's #1 (`build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`) has since been corrected
   to match: its `### #1` heading now reads "RESOLVED 2026-07-24, NOT A BUG" (verified by plan_reconciler, 2026-08-10) —
   the cross-doc follow-up this line used to flag as outstanding has already landed.
2. `REPO_NAME` vs `_REPO_NAME` build-history blind spot. **NOT A BUG** — never reproduced; code asserts `REPO_NAME`
   universal, manual path gained a `_SERVICE_NAME` fallback. Dropped.
3. GCP build events never carry `build_id` into the GCS ledger. **LOW-confidence / minor** — issue doc #3.
4. `freeze-deferred-build-replay.yml` filters `startswith("deferred-build-")` → never matches AWS `deferred-aws-build-*`
   (`cloud-build-router-aws.yml:83`). **CONFIRMED 2026-07-21 · AWS-deferred** — issue doc #4.
5. Cloud-build-failure-watcher wrong-repo stamp / free-text only. **FIXED 2026-07-20** — now `REPO_KEYS` fallback +
   notify-slack dedup ledger (`cloud-build-failure-watcher.yml:137,183`). Dropped.
6. Tarball VM BoM never stamped (see Honest gaps). **Plan-tracked here (Phase 3c)** — SHA now measured at boot
   (`setup-data-pipeline-vm.sh:706`); stamp-to-registry remains. Not in the issue doc. 7 (bucket). AWS tarball
   uploader/launcher bucket mismatch — launcher expects `unified-trading-deployment-scripts-<account>` (live: **404**),
   uploader writes `uts-prod-deployment-state/code/` (populated). **CONFIRMED 2026-07-21 · AWS-deferred** — issue doc
   #7.
7. **~40% of Cloud Run deploys ship nothing** (config-only redeploys, same digest) — churn that reads as activity; cheap
   to flag, noise unlabelled. GCP, the active cloud. Not in the issue doc (informational, not a defect). Evidence: Cloud
   Run revision digests for `uts-shared-deployment-api` (192 revs).

### AWS is intentionally parked — NOT bugs to fix (operator 2026-07-21)

**Load-bearing operator fact:** all deployments run on **GCP** and are healthy; **GCP is the sole active production
path**. **AWS is intentionally deferred — no AWS credits.** The App Runner services, ECS services, and ECR estate are
**deliberately stopped** and kept intact; they resume when credits return. The two AWS states below are NOT defects and
must NOT be framed as breakage in the page or the issue doc, nor "fixed":

- **AWS App Runner — both prod services PARKED (PAUSED)** (measured live 2026-07-21). `uts-deployment-api-prod` +
  `uts-alerting-service-prod` deliberately paused; the 2026-05-22 op-failure history (7/9 and 6/8) is _historical_, from
  before parking. Not actionable. Evidence: `aws apprunner list-operations`.
- **AWS ECR — entire estate PARKED** (measured live 2026-07-21). 0 of 20 repos run a task (2 App-Runner paused, 3 ECS
  `desired=0`, rest idle); 4 empty; 18/20 last pushed 2026-06-27 = when AWS was parked. ~393 images kept for resume —
  **not GC candidates.** Evidence: `aws ecr describe-images` + App Runner/ECS state.

The **AWS-side code bugs** #3 (build*id) / #4 (freeze-deferred replay) and the AWS half of the tarball-lane breakage are
\_genuine latent bugs* but are **deferred with AWS** — fix them only when AWS resumes, not now. The mock reflects all of
this: a top banner (GCP active / AWS parked), a Health `deferred` tier (blue, "not a defect"), and Artifacts states
`parked`/`legacy` instead of `orphaned · GC`.

## Todos

### Phase 0 — shape (done / in flight)

> **2026-07-28 retag** — all 11 P0 todos below are already ✅-checked with dated 2026-07-17→2026-07-21 operator
> sign-offs; per the operator's 2026-07-28 stale-gate audit ruling (CLAUDE.md Findings-triage: retag the moment a gate
> resolves, same edit), retagged the original OPERATOR tag to `[REVIEW]` (this file's convention for
> sign-off/review-type work) to reflect the completed nature of the work, not a live pending gate.

- [x] [REVIEW] P0. Audit both clouds + 4 codebase audits (pipeline / deployment-api / deployment-ui / tarball lane) —
      all complete; findings captured above.
- [x] [REVIEW] P0. Mock-first standalone HTML with REAL probed data (5 views: running / deploy-timeline / pipeline /
      artifacts / health) — shipped at `deployment-ui/public/design-mocks/artifact-pipeline.html`
      (deployment-ui@479f8c2), viewable at `/design-mocks/artifact-pipeline.html`. **Temporary — delete the folder when
      the real page ships.** Iterating with operator.
- [x] [REVIEW] P0. Shape locked with the operator 2026-07-17 — **top-level `/ops/artifacts`** (not a cockpit tab), **all
      5 views in v1**, **default view = What's running**.
- [x] [REVIEW] P0. ✅ Rebuilt "What's running" on the service × version model — `deployment-ui@3fcc112` +
      collapsible-groups follow-up. Row unit is now service × artifact version with an expandable host list, a
      `fragmented` flag, cross-links, collapsible service groups and an expand/collapse-all control. Stat tiles are
      computed from the data (a check caught hand-written numbers disagreeing with the table). Interactions verified in
      a real DOM (jsdom), not just eyeballed.

**Per-tab review gate — real work starts only when ALL of these are signed off:**

- [x] [REVIEW] P0. **Tab 1 — What's running** — reviewed 2026-07-20; rebuilt to service × version + collapsible +
      **build-datetime column**. ✅ **Signed off 2026-07-21.** Review findings folded in (drive the real page from
      these):
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
- [x] [REVIEW] P0. **Tab 2 — Deploy timeline** — ✅ signed off 2026-07-21 (iterated: correctness + usefulness pass).
      `ui@e01e5fc`. Was one-service (uts-shared-deployment-api) + 4 static AWS rows; now **estate-wide** across 5 real
      sections: Cloud Run for that service (15 revs, each with a computed **held-for** interval so "what ran on date X"
      is a lookup) + other Cloud Run services + **GCE VM launches (a launch IS the tarball-lane deploy)** + the real AWS
      App Runner storm + ECS. New surfaces: **● live-now** badges, **human-vs-CI deployer** column (hand-deploys lit
      red), **config-only / new-code / live-now / failed** filter chips, per-row **console↗ / VM↗** links, and
      `resolve ↗` where a digest→SHA join exists but the value needs a fresh gcloud auth. **Real-page requirement (fold
      into the build):** a **date cursor** so "what ran on date X" is an actual selection — the held-for intervals
      already support the lookup; the real page's date-range picker provides the control.
- [x] [REVIEW] P0. **Tab 3 — Pipeline** — ✅ signed off 2026-07-21 (iterated). `ui@e01e5fc`. Added **All / Failed /
      Image / Tarball / GCP / AWS** filter chips, surfaced the previously-dead `xlane` flag as a **⇄ both-lanes** badge
      (one commit built as image AND tarball), and a **shipped ↗** through-line hint on successful image builds. Drawer
      (step timeline + failure + log excerpt) unchanged. **Stale-fact fix `ui@57785a3`:** the note claiming the
      failure-watcher "only posts free text to Slack / stamps `unified-trading-pm`" was corrected — that watcher was
      **fixed 2026-07-20** (right repo + notify-slack dedup).
- [x] [REVIEW] P0. **Tab 4 — Artifacts** — ✅ signed off 2026-07-21 (iterated). `ui@e01e5fc`. Was 8 image rows for 2
      repos; now **one row per repo** showing the real sprawl (**ECR inventory probed live 2026-07-21**): 20 repos,
      image counts, latest tags, last-push, **running? + state** (running / App-Runner-PAUSED / ECS-desired=0 /
      orphaned-GC / empty / still-pushing), with **running / orphaned-GC / empty / cloud** filters. GCP AR kept as the
      2026-07-17 sample + an honest aggregate row (full AR walk needs gcloud auth). **Real-page requirement (fold into
      the build):** a per-repo **size** column + a **GC-candidate** flag (no matching build AND not running) so the 1.5
      TB AR sprawl is actionable at row level (ties to the cost page). GCP side needs live auth → real-page, not mock.
      (Overlaps the Phase-6 P3 "orphaned-image GC candidates" stretch — promote into the v1 Artifacts columns.)
- [x] [REVIEW] P0. **Tab 5 — Health** — ✅ signed off 2026-07-21 (iterated). `ui@e01e5fc`. Folded in 3 new **measured**
      deploy-lane findings (App Runner storm, orphaned ECR estate, ~40% config churn → 13 conditions), added severity
      **tiles + filter**, an **Area** column, and a **"see in <tab> ↗"** cross-link from every condition to the view
      that proves it. Note now states none of these fires an alert today. **Stale-fact fix `ui@57785a3`:** corrected the
      failure-watcher note (fixed 2026-07-20) and the AWS-tarball "`code/` has 0 objects" claim (now **populated**; real
      defect = the launcher's 404 bucket). The AWS-lane **bugs** (tarball mismatch, freeze-replay) are kept as **real
      defects tagged `AWS-deferred`**, distinct from the blue "parked · not a defect" tier (App Runner/ECR) — **operator
      CONFIRMED this framing 2026-07-21** ("what's broken is broken").
- [x] [REVIEW] P0. ✅ **AWS-deferred reframe applied across the mock** (operator 2026-07-21) — the AWS state is
      **intentional parking (no credits)**, not breakage. Added a top **GCP-active / AWS-parked banner**; Deploy
      timeline tiles + section headers reframed to "intentionally parked · last active 2026-05-22"; Artifacts states
      `orphaned · GC` → **`parked · AWS deferred`** (kept, not GC) with the GCP legacy AR aggregate as the only true GC
      row; Health demoted the 2 AWS conditions to a blue **`deferred` (not a defect)** tier (now high 5 / med 3 / low 3
      / deferred 2). ✅ Confirmed 2026-07-21 ("what's broken is broken; fix AWS when we need AWS").
- [x] [REVIEW] P0. ✅ **Final sign-off on the whole mock — 2026-07-21** → Phases 1–6 UNBLOCKED, build started.

### Phase 1 — backend read + snapshot layer (deployment-api)

- [x] [BACKEND] P1. ✅ New `services/artifact_pipeline/` service on the cost-observability shape: providers for Cloud
      Build, Artifact Registry, Cloud Run revisions — `deployment-api@8eda1f8`/`72a0108`/`a13c667`. CodeBuild, ECR, App
      Runner/ECS, tarball manifests stay deferred (AWS parked; VM tarball lane honestly unknown pending Phase 3c).
- [x] [BACKEND] P2. ✅ **EXTRACTED 2026-08-21 (na-eligibility-audit, RECLASSIFY per-todo split)** to
      `ui_satellite_ao_dispatch_batch5_2026_08_21.md` item 1 — Snapshot worker (`scripts/artifact_snapshot_worker.py`,
      Cloud Scheduler / `POST …/snapshot-run`): periodically read the live APIs, append normalized parquet to
      `gs://{state}/artifact-snapshots/…`; DuckDB-over-parquet read path with `BoundedCache`. Honour the OOM
      constraints; no per-request cloud scans. Still P2/deferred priority — the live-scan 300s TTL cache covers
      today's load; this is for long-history + concurrent-load headroom, not urgent. This checkbox tracks the
      extraction, not completion; the batch doc's own checkbox is the real dispatch surface.
- [x] [BACKEND] P1. ✅ The runtime join — `deployment-api@a13c667` (2026-07-23): live workload digest → matched AR image
      (one `list_docker_images` call over the canonical `unified-trading-system` repo, ~3365 images/20 repos, ~4s cold)
      → a SHA-shaped tag on that image → the `BuildFact` carrying that (repo, sha) → drift verdict. **Collapsed
      `DRIFT_PINNED` into `DRIFT_OK`** — Cloud Run's API exposes only the resolved digest, never the tag the operator
      originally deployed with, so "deployed via an immutable `@sha256` pin" and "deployed via a `:<sha>` tag that
      happens to still resolve to this digest" are OBSERVATIONALLY IDENTICAL from this join; claiming the stronger
      `pinned` would be unprovable, so both read as the one honest `ok` ("traceable to a commit"). `DRIFT_HAND` reuses
      the deployer-identity signal already computed for Deploy timeline (`deployer != "Cloud Build"`), not a separate
      provenance check. Deployer identity already lands from `revision.creator` (shipped with Deploy timeline,
      `72a0108`).

### Phase 2 — API contract (deployment-api)

- [x] [BACKEND] P1. ✅ Endpoints + Pydantic models (local `# CORRECT-LOCAL` like cost_observability): `/builds`,
      `/deploys` (`8eda1f8`/`72a0108`), `/running`, `/images`, `/health` (`a13c667`, 2026-07-23) — all five live.
      `running`/`images`/`health` are NOT windowed (no `days`/`start_date`/`end_date`) — they show current state, not
      history, so `_resolve_range`'s 400 gate only applies to `builds`/`deploys`.
- [x] [BACKEND] P1. ✅ Backend unit tests — 33 total (`test_artifact_pipeline.py`), `--block-network` safe (providers
      mocked at the module seam); full deployment-api quality-gates green.

### Phase 3 — UI page (deployment-ui)

> **🟢 ALL 5 VERTICAL SLICES LANDED — `deployment-ui@3210bb5` (2026-07-23).** The `/ops/artifacts` route + Fleet&Cost
> nav entry + 5-tab shell are live, and **every tab reads real cloud data** — Pipeline (builds), Deploy timeline (Cloud
> Run revisions), Artifacts (AR registry inventory), What's running (the digest→tag→SHA→build runtime join + drift
> classifier), and Health (conditions derived from the other four tabs' own facts). Pipeline + Deploy timeline share the
> **date-range picker** (operator ask 2026-07-23); the other three aren't windowed (they show current state, not
> history). **Every table's columns are sortable + filterable** (click-to-sort headers, a funnel icon per column —
> multi-select checklist for bounded columns, substring search for free text — operator ask 2026-07-23), with an
> explicit multi-select on each view's primary identity column: Repo (Pipeline, Artifacts), Workload/Service (Deploy
> timeline, What's running), Area (Health). Default view is still **Pipeline**, not What's running — the plan's "default
> = What's running" shape (line 127) was never revisited after the running view landed; a follow-up todo below tracks
> it. See the Progress log.

- [x] [UI] P1. ✅ `/ops/artifacts` **top-level route + NAV_GROUPS entry** — `deployment-ui@47e6379`; reuses the
      cost-page date-range picker + the `useRef` reqId ordering guard. Unknowns render explicitly (honest blanks, never
      a fabricated value). **Default view is still Pipeline, not What's running** — see the new follow-up todo below;
      the "default = What's running" shape (line 127) was never revisited once the running view actually landed.
- [x] [UI] P1. ✅ "What's running" — `deployment-ui@3210bb5` (2026-07-23). Scoped narrower than originally specced:
      **one row per live workload's CURRENT version** (Cloud Run's `list_cloud_run_services` reports exactly one live
      revision per service today), not a host-expandable multi-version group — Cloud Run traffic-split (>1 revision
      serving at once) isn't detected by this join, so `fragmented` always reads 0 for now. The `RunningGroup.versions`
      shape supports a future multi-version row without a contract change; a row still expands (click) to show the full
      drift explanation + its (single) host. VM-fleet fragmentation (the original "13 VMs, 2 code versions" case from
      2026-07-17) is out of scope until Phase 3c's tarball stamp lands — flagged as a Health condition instead of
      silently absent.
- [x] [UI] P1. ✅ API client (`deploymentApi.ts` flat-function style) + mock-api handlers (route before any broad
      wildcard) with realistic fixtures mirroring live shapes — `deployment-ui@3210bb5`.
- [x] [UI] P1. ✅ Vitest (19 for the page, 1097 total) + `pw:L2` smoke spec (10 cases) covering all five views, the
      running-drift flags, the deploy change-type, the failure drawer, and per-column sort/filter/multi-select on every
      table. No UI tick without `pw:L2 ✓` + a cited regression spec — both satisfied.
- [x] [UI] P2. ✅ **DECIDED 2026-07-24 (operator): default view = What's running — implemented 2026-07-27.**
      `deployment-ui@fb1da34` — flipped `useState<TabId>("pipe")` → `useState<TabId>("run")`
      (`ArtifactPipeline.tsx:2749`). Updated the 10 Vitest cases + the 6 `pw:L2` cases that implicitly relied on
      Pipeline being the default-rendered tab (added an explicit `artifact-tab-pipe` click before their
      Pipeline-specific assertions), rewrote the "defaults to…" test to assert the new default, and added a dedicated
      `pw:L2` case asserting the page opens on What's running. Full deployment-ui gate green (101 Vitest + `pw:L2`);
      both suites re-run clean post-edit.
- [x] [UI] P1. ✅ **NEW (operator ask 2026-07-23) — per-column sort + filter on every live table, multi-select on each
      view's identity column.** `deployment-ui@3126b1b` (Pipeline + Deploy timeline) + `@3210bb5` (Artifacts, What's
      running, Health). Shared `ColumnHeader`/`MultiSelectFilter`/`TextFilterInput` primitives, client-side over the
      already-loaded data (no new fetch) — not originally in this plan's scope, captured + closed same-turn.

### Phase 3b — cross-links (deployment-ui + deployment-api) — operator requirement 2026-07-17

> **🟢 UNBLOCKED 2026-07-23** — this phase was gated on the What's running view landing (the version row that would
> deep-link); it shipped as `deployment-ui@3210bb5`/`deployment-api@a13c667` this session. Recommended next phase.

- [x] [BACKEND] P1. ✅ **Carried the image/tarball version onto the Deployments inventory row — `deployment-api@24070d9`
      (2026-07-27).** Added `image_digest`/`git_commit` (both `str | None`) to `DeploymentItem`, populated in
      `_vm_item()` from `entry.image_digest or None` / `entry.git_commit or None` (honest `None` on a pre-BoM `""`,
      never a fabricated empty string). Two pre-existing test fake-entry stand-ins
      (`test_route_deployments_inventory.py`'s module-level `_FakeEntry` dataclass,
      `test_route_deployments_inventory_aws.py`'s inline per-test `_FakeEntry`) needed the two new attributes added
      since `_vm_item()` now reads them unconditionally — caught by a full-gate run, not assumed; one new unit test
      (`test_build_inventory_surfaces_image_digest_and_git_commit`) pins both the stamped and the honest-`None`
      legacy-row cases. Full deployment-api gate green (4985 tests). **Additive only** — `DeploymentItem` today carries
      no image URI / digest / commit; adding fields must not break any existing consumer or field-set assertion. Respect
      the 45s SWR cache + the 4 GiB / WORKERS=2 budget (report the payload delta before shipping). **AUDITED 2026-07-17
      — cheaper than assumed: the data is already in hand.** `DeploymentRegistryEntry` already declares
      `image_digest`/`git_commit` (`unified_trading_library/deployment_registry.py:205-206`) and `_vm_item()`
      (`deployments_inventory.py:689-721`) **already receives that entry object** — it simply never copies the fields
      onto the row. So this is a ~2-line addition with **zero new I/O / census cost**; no join to write. Payload delta
      measured at **<20 KB** across ~200 targets. `_unmanaged_vm_item` (live-GCE-but-unregistered) correctly stays
      `None`. **No test anywhere asserts a closed field set**, so additive fields are safe.
- [x] [UI] P1. ✅ **Pre-loaded `?git_commit=<sha>` filter on the Deployments view — `deployment-ui@74c0a7d`
      (2026-07-27).** Added a client-side `gitCommitFilter` read via `searchParams.get("git_commit")`, following the
      existing `serviceFilter`/`launchedByFilter` pattern exactly (`setParam`/exact-match, no dropdown of its own since
      it's a deep-link target, not an operator-picked value); an honest `null` on a row's `git_commit` never matches, so
      unstamped rows correctly stay excluded rather than false-positive-included. Since this is the first param with no
      owning dropdown, added a visible active-filter chip + a "clear" link (`deployments-git-commit-filter` / `-clear`
      testids) so the filter is never silently invisible. Also surfaced the previously-dead `git_commit`/ `image_digest`
      fields in `VmDeploymentDetails.tsx` (backend `VmDeploymentEntryModel` already sent them; the frontend type +
      component simply never read them). New coverage: 1 Vitest (`Deployments.test.tsx`) + 1 `pw:L2`
      (`deployments-wsd.spec.ts`), both asserting the filter narrows correctly and clears cleanly. Full deployment-ui
      gate green (1099 tests). Original audit for reference: every filter already reads `useSearchParams()` via one
      `setParam` helper, and the module docstring states the intent ("ALL filters are URL-backed … so alert deep-links
      and shareable filtered views work"). Taken params:
      `umbrella / cloud / status / asset_group / kind / launched_by / region / detail` — this was the first consumer of
      an existing-but-unused capability.
- [x] [UI] P2. ✅ **Console deep-links — `deployment-ui@74c0a7d` (2026-07-27).** Wrote the missing Artifact Registry /
      ECR link builder (`artifactConsoleUrl(cloud, registry, repo)` in `ArtifactPipeline.tsx`, following
      `consoleUrl()`'s pure-URL-construction pattern from `DeploymentDetail.tsx`) and wired it into two places: the
      Artifacts tab's per-repo row (a `↗` next to the repo name) and the What's running tab's expanded row detail
      (parses the joined `artifact` ref, e.g. `"unified-trading-system/deployment-api"`, since that view carries no
      separate registry/repo fields — `runningArtifactConsoleUrl()`). The AR location (`asia-northeast1`) and AWS
      account (`427895769566`) were confirmed against the LIVE `unified-trading-system` AR repo via
      `gcloud artifacts repositories list`, not assumed. The What's running row's expanded detail also gained the second
      half of the operator's original cross-link ask — a "View hosts on this commit in Deployments ↗" link using the new
      `?git_commit=` filter above, so a version row now deep-links BOTH to its registry console and to exactly the hosts
      running it. New coverage: 2 Vitest + 2 `pw:L2` cases (console-link href assertions for both GCP/AR and AWS/ECR
      rows, plus the Deployments deep-link href). GCP Cloud Build / AWS CodeBuild build-log links were already live
      (`row.log_url`, Pipeline tab drawer) — no new work needed there, confirmed by grep before starting. Gap that
      remains open, out of this todo's scope: AWS CodeBuild's CloudWatch `deepLink` and the GCE-instance console link
      are both already covered by the pre-existing `consoleUrl()` (Deployments/DeploymentDetail pages), not this page.

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
- [x] [INFRA] P1. ✅ **(A) measured stamp — `deployment-service@d8b1411c` (2026-07-27).** Found the accumulation half
      already free: `_tarball_actual_sha` is a plain (non-`local`) shell variable set inside the download loop, so it
      already survives as a global until `_launch_with_tee()` runs later in the same script execution — no code change
      was needed there, only the read. The actual edit is ONE additive block inside `_launch_with_tee()`, next to the
      existing `VM_NAME`/`VM_TASK` exports. All 7 binding conditions verified satisfied: (1)
      `if [[ -n … ]]; then export …; fi` form, placed mid-block (not the function's last statement) — safe under
      `set -euo pipefail`. (2) `IMAGE_DIGEST` left untouched — only `GIT_COMMIT` is set. (3) A missing/`"unknown"` SHA
      degrades silently to no export (same absence as today) — never aborts a boot. (4) Plain `export GIT_COMMIT=`, not
      `extras`. (5) The semantics are documented inline (manifest `commit_sha` at boot, not a running-bytes
      attestation). (6) No inferred value — only the measured `_tarball_actual_sha` from the manifest this VM actually
      downloaded. (7) The AWS lane was not touched. Python half:
      `test_resolve_bom_reads_git_commit_from_env_via_deployment_config` in `test_bom.py` — uses the REAL
      `DeploymentConfig` (not the existing tests' `_StubConfig` double) with `GIT_COMMIT` set via
      `patch.dict(os.environ, …)`, confirming the `AliasChoices` resolution itself works end-to-end through
      `resolve_deployment_bom()`, not just the passthrough logic the existing tests already covered. Full
      deployment-service gate green (bash syntax + shellcheck clean, `test_bom.py` 8 tests). **Verification gate not yet
      satisfied by this alone** — see the live-launch todo below; no CI executes this shell file, so a green unit test
      is necessary but not sufficient.
- [x] [INFRA] P1. ✅ **Live-launch verification COMPLETE — 2026-07-27.** Real VM
      `measure-honest-coverage-20260727-234251` (`launch-measure-honest-coverage-vm.sh prediction`,
      `VM_SERVICE=instruments_service`, both registered — see the dated Progress Log entry above for why the first two
      attempts via `launch-qg-snapshot-vm.sh` were abandoned: one had a stale setup script, the other hit an unrelated
      pre-existing "unregistered VM_SERVICE → install all 28 repos" launcher bug, unconnected to this fix). Ran to
      completion (`exit_code=0`, self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true` — confirmed gone via
      `gcloud compute instances describe` 404 post-run, no manual cleanup needed). **All 4 verification steps passed:**
      (1) codex T+10min check — `run.log` present + growing, `DEPLOYMENT_STARTED`/`DEPLOYMENT_COMPLETED` events fired.
      (2) Registry row confirmed at
      `gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-27/9dc3e0c9-6634-4f6c-a2cb-54d1d8786a46.json`
      (a completed run archives immediately — no separate `deployments/active/` check needed). (3)
      **`"git_commit": "f06eba12989dddff58831d26bf6977f92b57994e"` — non-empty, real 40-char SHA.** (4) **Spot-checked
      against the VM's own serial console** (`vm-setup.log` isn't uploaded on a SUCCESSFUL boot — confirmed the audit's
      own finding about the failure-only EXIT trap still holds — so the serial console, which captures unconditionally,
      was the right source): the LAST of the 4 tarballs this task needed (unified-api-contracts →
      unified-trading-library → deployment-service → **instruments-service**, in that order) logged
      `manifest: sha=f06eba12989d version=v0.91.0-563-gf06eba12` — the 12-char prefix matches the registry's stored
      40-char SHA EXACTLY. This confirms end-to-end: the download loop's `_tarball_actual_sha` correctly held the
      last-processed tarball's manifest commit → `_launch_with_tee()`'s new `export GIT_COMMIT=` correctly read it →
      `resolve_deployment_bom()`'s pre-existing `AliasChoices("GIT_COMMIT", …)` correctly resolved it with zero Python
      changes → the registry entry correctly persisted it. **Phase 3c is fully DONE.**

> ❌ **Option (B) — inferred-from-manifest-timeline — is DROPPED** (operator decision 2026-07-17). Rationale recorded
> under "Honest gaps" above. Pre-(A) VMs render as ⚪ **unknown with the reason**, and age out as the fleet recycles. Do
> not reintroduce an inferred commit into `git_commit`.

### Phase 3d — tarball-bucket provider (wire the GCS tarball lane into the views) — NEW 2026-07-24

> Distinct from Phase 3c above: 3c stamps a commit SHA onto tarball VMs for provenance; this phase is the more basic gap
> underneath it — **no provider anywhere reads the tarball-manifest GCS bucket at all**, so the tarball half of every
> view that is supposed to show it (target shape, line 148: "Artifacts — AR + ECR **+ tarball bucket**") is silently
> absent, not filtered/empty-on-purpose. CONFIRMED 2026-07-24 (operator: "in local version as well i cannot see anything
> in tarball lane"): `_all_build_facts()`/`_all_image_facts()` in `service.py` only ever call the
> Artifact-Registry/Cloud-Build (image-lane) providers; `LANE_TARBALL` is a real constant in `models.py` and the UI's
> lane filter chips already offer "Tarball" (Pipeline tab), but zero rows can ever carry it.
>
> **CORRECTED 2026-07-27 — the line below was WRONG, re-verify-against-the-cited-commit caught it**: this banner
> originally claimed "Deploy timeline ALREADY treats a GCE VM launch as the tarball-lane deploy event
> (`deployment-ui@797180c`/`deployment-api@72a0108`) — that half of the tarball story is live." The CITED commit's own
> message says the opposite: "AWS App Runner/ECS + GCE VM launches (the tarball-lane deploy) are later increments." No
> VM-launch-as-`DeployFact` provider exists anywhere in this codebase — `running()`'s tarball-lane coverage is zero, not
> partially built. This phase's actual scope is (and always was) just the BUILD/ARTIFACT half: the tarball's own
> creation/upload event (Pipeline tab) and its registry-style inventory (Artifacts tab) — both now shipped, see the
> Todos below. The VM-launch-deploy gap remains open, tracked as the blocker note on the "What's running tab" P3 todo.
>
> **⚠️ Bucket path needs live confirmation before implementation (operator, 2026-07-24)**: the bucket path cited below
> comes from `code_tarball_refresh_scheduler.tf`'s comment, cross-checked against the Data-feasibility table's
> 2026-07-17 measurement — the operator flagged uncertainty whether this is actually the same bucket tarballs get
> uploaded to today ("there is a bucket where tarballs are uploaded, not sure if you are referring to that one"). **Do
> NOT start Phase 3d's backend todo below from this citation alone** — first `gsutil ls`/`gcloud storage ls` the live
> bucket and diff its actual contents against the cited path before writing the provider.

- [x] [BACKEND] P1. ✅ **`gcp_tarball_manifest_builds()` provider — `deployment-api@3525bce` (2026-07-27).** Bucket path
      LIVE-VERIFIED via `gcloud storage ls` before writing any code (measured ~4966 manifests / ~1046 tarballs, up from
      the 2026-07-17 figure — confirms the bucket only grows, no lifecycle rule). **Design deviation from the original
      spec, deliberate**: reads ZERO manifest bodies — `commit_sha`/`branch`/`size`/timestamp are all derivable from the
      object's own name + `list_blobs` metadata (the SHA is IN the filename: `<repo>-code@<sha>.tar.gz`), so this stays
      one cheap metadata scan even at ~5000 objects rather than thousands of small downloads
      `pyproject_version`/`git_status_clean` are NOT read — `BuildFact` has no fields for them, so reading them would be
      pure waste). The floating (no-`@sha`) pointer is skipped for build-history purposes — it's always a byte-identical
      `cp` of the newest pin (`create-code-tarballs.sh:373`), so counting it would double the build event, not add
      information. Every row is `status="SUCCESS"` — this bucket structurally cannot record a failed refresh (no
      manifest gets written), so a fabricated failure rate is never at risk. Bucket name is config-derived
      (`deployment-scripts-{project_id}`, matching `_project_id(cfg)`'s existing pattern), NOT a hardcoded literal — the
      QG's "no hardcoded project ID in production" gate caught my first draft doing exactly that, and a `# noqa: gs-uri`
      covers the one display-string URI construction this doesn't route through `resolve_bucket_name()` for (documented
      as a separate, already-tracked gap, not a new one).
- [x] [BACKEND] P1. ✅ **Folded into `_all_image_facts()` / `service.images()` — `deployment-api@3525bce`.** One
      `RegistryImageFact` per manifest (floating AND pinned both count here, unlike the build-history reading — the
      Artifacts roll-up shows every currently-fetchable artifact); `registry="gcs-tarball-bucket"`
      (`REGISTRY_TARBALL_BUCKET` in `models.py`, shared by both `providers.py` and `service.py` rather than duplicated)
      so it never collides with the AR per-repo grouping key even when a tarball repo shares its name with an AR repo.
      `digest=""` always (honest absence — a tarball has no Docker digest), so the existing `running_on` cross-ref
      (keyed on digest) correctly never fires for these rows without any special-casing in `_image_row()` — reused
      verbatim, zero new logic needed there. `size_bytes` comes from the SIBLING `.tar.gz` object, never the tiny
      manifest JSON's own size — **a real bug a test caught before shipping**: the first draft fell back to the
      manifest's own byte count when no matching tarball existed, silently fabricating a plausible-looking but wrong
      size for an orphaned manifest; fixed to honest `None` in that case.
- [x] [BACKEND] P2. ✅ **Health's tarball-lane condition made data-driven — `deployment-api@3525bce`.** The existing "VM
      tarball-lane workloads carry no measured git commit yet" condition now gates on `images_resp` actually containing
      `REGISTRY_TARBALL_BUCKET` rows (count = the real number of tarball repos observed, not the fixed word "fleet") —
      it no longer fires as a blanket placeholder when the lane is simply unbuilt. Added a NEW condition, "The
      tarball-bucket provider returned zero rows" (MED, `tab=art`), that fires only when AR rows are present in the SAME
      response (proving `images()` itself works) but zero tarball rows exist — the same silent-empty symptom Phase 7
      diagnosed for AR before its IAM fix (a caught exception degrading to `[]`), isolated to the tarball provider
      specifically. **A stale claim caught + corrected while doing this**: this exact Phase 3d banner previously said
      "Deploy timeline ALREADY treats a GCE VM launch as the tarball-lane deploy event... that half of the tarball story
      is live" — re-verified against the CITED commit (`deployment-api@72a0108`)'s own message, which says the opposite
      ("GCE VM launches (the tarball-lane deploy) are later increments"). No VM-launch deploy provider exists yet, so
      `running()`'s tarball coverage remains exactly zero — the git-commit-gap condition's wording was correct
      regardless (it was never claiming VM launches were covered), but the banner's contrast claim was wrong and is
      corrected here so a future session doesn't build on it. New coverage: 10 new unit tests total across the 3 backend
      todos (parsing, size-backfill, both health-condition branches); full deployment-api gate green (4996 tests).
- [x] [UI] P2. ✅ **Pipeline tab — verified, `deployment-ui@05a087d` (2026-07-27).** No production code change was
      needed (confirmed, matching the original prediction) — `PipelineView`'s `Tarball` filter chip already worked
      against real data the moment the backend started returning `lane=tarball` rows. The mock fixture (`mock-api.ts`)
      already carried one tarball row (pre-existing, apparently added speculatively and never exercised) — added 1
      Vitest + 1 `pw:L2` case asserting the filter actually narrows to it and back, closing the "assumed-working,
      never-tested" gap the plan flagged.
- [x] [UI] P2. ✅ **Artifacts tab — verified, `deployment-ui@05a087d`.** Also no production code change needed:
      `registryOptions`/`cloudOptions` in `ArtifactsView` are already computed dynamically from `data.rows` (not a
      hardcoded option list), so a `registry="gcs-tarball-bucket"` row automatically appears as a selectable filter
      value the moment real data exists — same generic per-repo table, no special-casing. Added a tarball row to the
      mock fixture (there wasn't one) + 1 Vitest + 1 `pw:L2` case confirming the row renders and the Registry funnel
      isolates it correctly, including the same-repo-name-as-an-AR-row collision case.
- [ ] [UI] P3. **What's running tab** — a tarball-lane version row can only ever show a real commit once Phase 3c's
      stamp lands (today `git_commit` is `""` on every live VM); until then, tarball rows in Running should render
      explicitly ⚪ **unknown, reason: "stamp not yet live (Phase 3c)"** rather than silently absent — this is the
      "honest blank, never a fabricated value" principle the plan already commits to elsewhere (line 124). **Re-scoped
      2026-07-27**: genuinely blocked on more than Phase 3c alone — `running()` has ZERO tarball-lane rows today because
      no provider builds VM-launch `DeployFact`s at all (the Phase 3d banner's contrast claim that this already existed
      was stale, corrected above), so there is no tarball version row to even attach an "unknown" label to yet.
      Sequencing: a VM-launch-as-deploy provider (net-new, not currently a todo anywhere in this plan) → Phase 3c's
      commit stamp → this display fix. Left as P3/deferred rather than expanded into that larger scope without an
      explicit decision to do so.

### Phase 4 — absorb + retire

- [x] ✅ [UI] P2. **DONE 2026-08-15** — ported, `CloudBuildsTab.tsx` deleted (confirmed absent).
      deployment-ui@b3300a71a7.
- [x] ✅ [BACKEND] P2. **DONE 2026-08-15** — superseded narrow routes retired, dead code deleted.
      deployment-api@3f13e4435e.

### Phase 5 — codex + issue doc + notify

- [x] [REVIEW] P2. ✅ **STALE — already done under a different name, closing 2026-08-07 (na-eligibility-audit).** File
      `plans/active/issues/artifact_pipeline_metadata_gaps_<date>.md` with the 6 pipeline bugs above; notify the
      operator/Ikenna; verify bug #2 first. This plan's own "Pipeline bugs found" section (above) already states the
      filing happened 2026-07-21 under
      `plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` (RE-VERIFIED
      2026-07-21, most of the list resolved itself), and bug #2 (`REPO_NAME` vs `_REPO_NAME`) is already verified "NOT A
      BUG — never reproduced" in that same section. Independently corroborated by
      `issues/ag_closeout_audit_ui_parked_2026_08_07.md` Finding 3, which found this exact stale-read on the same day.
      This checkbox itself was pre-flipped 2026-08-07 by the na-eligibility-audit pass (unified-trading-pm@2b8073083);
      `ui_satellite_ao_dispatch_batch1`'s own todo 2 independently confirmed the same closure and additionally fixed the
      cross-referenced issue doc's stale `#1` item (confirmed-dead-semver-agent finding) — unified-trading-pm@d2094b791.
- [x] ✅ [REVIEW] P2. Fix the 5 `dual-cloud-image-builds.md` drifts (registry name, tag convention, trigger/project
      naming, canonical-trigger claim, empty-manifest provenance). Post-phase codex audit. **DONE 2026-08-08**
      (`ui_satellite_ao_dispatch_batch1-003`): all 5 fixed with fresh live evidence (GCP `gcloud artifacts`/
      `gcloud builds triggers`/`workspace-manifest.json` re-verified 2026-08-08; AWS project-naming claim retained
      unverified-this-pass — identity gap, see follow-up). Post-phase audit found + fixed 2 more stale sections
      (live-defi-rollout trigger claim, reusable-workflow repo location). 5 smaller code/infra findings filed as
      follow-up todos: `issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md`. —
      unified-trading-pm@dab5f0273

### Phase 6 — later / optional (stretch)

- [ ] [INFRA] P3. _(stretch, optional)_ **Fleet-wide SHA-pinning — upgrades the tarball answer from _plausible_ to
      _proven_.** The pin lane already exists and is fail-closed (`<name>@<sha>.tar.gz` + self-verifying manifest check,
      `setup-data-pipeline-vm.sh:620-644`), with 5 launchers using it. Extending it fleet-wide makes the recorded commit
      an attestation of the running bytes rather than "what the manifest said at boot". **Hazard**: the codex documents
      a 2026-06-01 incident where pinned fan-out tarballs were pruned seconds after upload, killing 20 VMs (exit 2).
      Currently dormant — `uts-prod-tarball-cleanup-cron` is PAUSED and there is no lifecycle rule on `code/` — but any
      revival of pruning must be reconciled with this first. Separate, larger change; do NOT bundle with (A).
- [x] ✅ [REVIEW] P3. _(stretch, optional)_ Issue doc — **the whole VM tarball path bypasses `resolve_bucket_name()`**
      and hardcodes `deployment-scripts-central-element-323112` (`setup-data-pipeline-vm.sh:47`,
      `create-code-tarballs.sh:45`, ~48 launchers), contradicting both the workspace storage rule and the codex SSOT's
      own description of this path. Combine with the two-point AWS-lane breakage into one deployment-bucket-resolution
      issue doc. — DONE via `ui_satellite_ao_dispatch_batch3_2026_08_09.md`'s own todo 1 (unified-trading-pm@commit
      cited there): filed `plans/archive/2026_08/issues/deployment_bucket_resolution_gaps_2026_08_09.md` (confirmed on disk) —
      verified by plan_reconciler 2026-08-10, checkbox was never flipped in this source doc.
- [x] ✅ [BACKEND] P3. **DONE 2026-08-15** — "built but never deployed" + build→deploy latency join shipped.
      deployment-api@764db37c33.
- [x] [INFRA] P3. _(stretch, optional)_ ~~orphaned-image GC candidates (no matching build AND not running)~~ —
      **RESOLVED 2026-07-29** by `docker_artifact_registry_cleanup_policy_2026_07_24.md` Phases A-D: the 3-rule cleanup
      policy (`keep-5-recent` + `keep-deployed-digests` + `delete-older-than-3d`) was applied live (no dry-run) on
      2026-07-29; the ~daily GCP background job removed ~2,958 images (85% reduction, 519 remaining from ~3,477)
      entirely via the policy — no manual per-image deletion. All 20 package counts are now consistent with the policy
      window.
- [x] ✅ [INFRA] P3. _(stretch, optional)_ **Image vulnerability-scan status** — **DONE 2026-08-16**, live-checked
      read-only (see Progress Log). Split out 2026-08-08 from the orphaned-image-GC todo above (was an unchecked
      trailing sentence, missed by 3 prior passes).
- [x] ✅ [INFRA] P3. **DONE 2026-08-15** — deploy-churn/crash-loop signal surfaced as a health condition.
      deployment-api@ec80509550 (ancestor of `origin/live-defi-rollout`).

### Phase 7 — production-vs-local parity audit: why prod showed empty when local showed real data — NEW 2026-07-24

> Triggered by the operator noticing the Artifacts tab showed real data locally "yesterday" but nothing at all on the
> deployed page. Framed as an audit, not a single fix — TWO independent root causes were found and fixed today, and a
> THIRD symptom remains genuinely open after both fixes deployed. Full evidence trail in the Progress log below; this
> section is the actionable todo list distilled from it.

- [x] [BACKEND] P0. ✅ **Root cause #1 — missing IAM grant.** `unified-trading-sa` (deployment-api's prod Cloud Run
      identity) never had `roles/artifactregistry.reader`; every `gcp_artifact_registry_images()` call in prod threw
      `PermissionDenied`, caught by `providers.safe()`, degrading to `[]` — while local dev used the operator's own
      broad personal ADC credentials, which already had access, so the gap was invisible locally. Fixed:
      `deployment-service@74306a1` (added `google_project_iam_member.unified_trading_artifactregistry_reader` to
      `terraform/gcp/main.tf`, mirroring the pre-existing grant on the dashboard's compute SA for the same need) +
      applied directly against the prod GCS-backed state (`1 added, 0 changed, 0 destroyed`). Verified independently of
      the app: impersonating `unified-trading-sa` and calling the exact same `ListDockerImagesRequest` returned real
      data (20 repos) — the grant is unambiguously correct and live.
- [x] [BACKEND] P0. ✅ **Root cause #2 — total logging silence, service-wide.** `deployment_api/main.py` never called
      `logging.basicConfig()` (or any handler setup) anywhere — confirmed via `gcloud logging read` showing **zero**
      application-level log lines had EVER reached Cloud Logging for this service, for any logger, at any severity (only
      Cloud Run's own auto-generated HTTP access + system lifecycle logs existed). This meant root cause #1's
      `providers.safe()` warning (`logger.warning("artifact-pipeline provider %s failed: %s", ...)`) was firing but
      going nowhere — the exact evidence that would have made root cause #1 a 30-second diagnosis instead of a
      multi-hour one. Fixed: `deployment-api@f27a8f1` — `logging.basicConfig(level=logging.INFO)`, mirroring
      `unified_trading_library.service_framework.bootstrap.ServiceBootstrap._setup_logging()`'s existing pattern.
- [x] [BACKEND] P0. ✅ **Root cause #3 — stdout buffering, compounding #2.** Even after #2 shipped, the images endpoint
      was STILL empty and STILL silent. `PYTHONUNBUFFERED` was never set anywhere (Dockerfile / `gunicorn.conf.py` / app
      code) — Python block-buffers stdout whenever it isn't a TTY (always true in a container), so log output could sit
      in an unflushed ~8KB buffer. Combined with this service's independently-observed crash-looping
      (`Uncaught signal: 6` recurring through the day, one real OOM kill at 05:35 UTC — found while investigating, not
      the original question), a hard kill would discard whatever hadn't flushed yet. Fixed: `deployment-api@6518e82` —
      `ENV PYTHONUNBUFFERED=1` in the `Dockerfile`. Verified BOTH fixes are genuinely baked into the live image (not a
      stale-deploy illusion): pulled the exact running digest (`sha256:1df38dd2…`) via `docker pull` + inspected it
      directly (`docker inspect` for the env var, `docker create`+`cat` for the `main.py` source) — both present.
- [x] ✅ [BACKEND] P0. **RESOLVED 2026-08-07 — CONFIRMED FIXED, hypothesis was correct.** Operator ruled 2026-08-07 (via
      consolidated NA-blocker-digest audit) to resume this paused (2026-07-24) investigation. Checked the live prod
      Cloud Run service (`uts-shared-deployment-api`, asia-northeast1) directly:
      `run.googleapis.com/cpu-throttling: 'false'` is ALREADY set (the override the leading hypothesis called for).
      Live-verified `GET /api/artifacts/images` against the real prod endpoint 2026-08-07 08:25 UTC — returns full,
      correctly-populated data: 39 repos, 2 running, 8 legacy, **0 empty**, real `last_pushed` timestamps and byte sizes
      throughout (e.g. `deployment-api` itself: 31 images, `running_on: uts-shared-deployment-api`, `state: running`).
      The silent-empty symptom described below is **no longer reproducible** — the fix is live and confirmed working
      end-to-end. (Original hypothesis, preserved for the record: prod showed empty even with all 3 root-cause fixes —
      IAM grant, logging config, stdout buffering — live on a fresh revision; local `docker run` against the exact same
      image+digest worked fine, ruling out the image/code; leading theory was GCP's default throttled-CPU mode starving
      background log-flush I/O between requests, fixed by disabling CPU throttling.)
- [x] [REVIEW] P2. ✅ **Separate finding, surfaced while investigating — issue doc FILED 2026-07-24.** This project's
      Cloud Logging ingestion is dominated by GCS Data Access audit logs — MEASURED 151 GB over one 7-day sample
      (project-wide, all resources), spiking to 76.5 GB on 2026-07-19 and 37.6 GB on 2026-07-22, both days correlating
      with a large `canonical-migration-{cefi,defi,tradfi,prediction}-*` VM campaign (200+ VMs in a single day) doing
      bulk per-object GCS operations against the `market-data-tick-{defi,cefi}-prd` buckets. This is legitimate,
      expected migration work — the cost is a side effect of GCS Data Access audit logging being enabled project-wide,
      not a bug in the migration itself. Filed at the operator's request:
      `plans/archive/2026_07/gcs_data_access_audit_log_cost_2026_07_24.md` — the exclusion-filter decision (touches
      logging/audit posture, not just cost) lives there now, routed to Ikenna (or the operator, Monday).

## Progress log

> **History extracted 2026-07-24** (line-cap remediation) → `artifact_pipeline_observability_history_2026_07_24.md`: the
> earliest dated Progress Log entries (2026-07-17 — Audit + mock complete, through 2026-07-21 (later still) — UI
> vertical slice 1 shipped) — the mock-first design phase, the shape lock, the tarball blast-radius + Deployments-
> filter audits, the AWS-deferred reframe, build kickoff, and the backend Phase 1/2 first vertical (Pipeline view) plus
> its first live UI tab. All shipped/narrative, zero open todos. See that file for the full early-build narrative.
>
> **History extracted 2026-07-27** (line-cap remediation, again) →
> `artifact_pipeline_observability_history_2026_07_27.md`: the 2026-07-23 dated entries (Deploy timeline vertical, the
> help dialog, the remaining three views + per-column sort/filter, the two layout passes) plus the entire "Lessons this
> session" section. All shipped/narrative, zero open todos. See that file for the full mid-build narrative + lessons.
>
> **History extracted 2026-08-21** (line-cap remediation, again — a RECLASSIFY-per-todo-split edit pushed the doc to
> 1012L, over the 1000L hard cap) → `artifact_pipeline_observability_history_2026_08_21.md`: the 2026-07-24 through
> 2026-07-27 dated Progress Log entries (production-vs-local parity investigation — IAM/logging/stdout-buffering root
> causes, the tarball-lane structural gap, the GCS Data Access audit-log cost finding; the same-day operator
> open-decisions review; the 2026-07-27 session where Phase 3b/3c/3d all shipped, incl. the live-launch verification's
> 3 attempts). All shipped/narrative, zero open todos. See that file for the full narrative.

- [ ] [SCRIPT] P3. **Correct the misattributed VM origin in
      `issues/deployment_service_qg_red_qg_snapshot_launcher_live_vm_flake_2026_07_27.md`** — that issue doc (filed by a
      different agent/slot-4, independently) states `qg-snapshot-20260727-232717` was "the actual daily qg-snapshot cron
      VM (terraform schedule '0 6 \* \* \*')"; it was actually this session's ad-hoc Phase 3c verification launch
      (confirmed: this session ran `bash launch-qg-snapshot-vm.sh` directly at that exact timestamp). The doc's actual
      finding (the launcher's singleton-lock preflight breaking `--dry-run-scheduler-body`'s statelessness) is still
      correct and still worth fixing — only the "which VM was this" attribution is wrong. Low-priority since it doesn't
      change the recommended fix, but leaving a wrong provenance claim in a filed issue doc could mislead whoever picks
      it up next about how often this collision actually happens in production.

## Deferred work after 2026-07-23

> Superseded 2026-07-23 (again, same day) — the table below described the state after Pipeline + Deploy timeline
> shipped, running/artifacts/health "not started". All five views are now live (`deployment-api@a13c667`,
> `deployment-ui@3210bb5`), plus per-column sort/filter/multi-select workspace-wide on the page. This is the current
> state.

**Updated 2026-07-27 (later): Phase 3b, 3c, and 3d are now ALL DONE** — the Phase 3c live-launch verification (the last
open piece below Phase 7) completed successfully via `measure-honest-coverage-20260727-234251` (`git_commit` confirmed
correctly stamped + spot-checked against the serial console). **Recommended NEXT**: Phase 7's CPU-throttling test (still
**operator-paused** since 2026-07-24 — "let's check the locally running one first") is now the only non-stretch,
non-AWS-gated item left in the whole plan. Beyond that: the Phase 6 stretch items (all P3, optional), the new P3
issue-doc-correction todo (Phase 3c section), and AWS resume (operator/credits-gated).

| Item                                                                                      | State / why deferred                                                                                                                                                                                                                                                                              | Blocked on                            |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Tarball-bucket provider (Phase 3d) — Pipeline/Artifacts rows                              | ✅ **DONE 2026-07-27** — `deployment-api@3525bce`, `deployment-ui@05a087d`. Running-tab tarball rows remain out of scope — no VM-launch deploy provider exists (see Phase 3d's P3 todo)                                                                                                           | a VM-launch deploy provider (net-new) |
| Phase 7 — prod-vs-local parity: root causes #1/#2/#3 (IAM/logging/buffering)              | ✅ **FIXED 2026-07-24** — `deployment-service@74306a1`, `deployment-api@f27a8f1`/`@6518e82` — but prod endpoint STILL empty on a fresh revision after all 3                                                                                                                                       | —                                     |
| Phase 7 — CPU-throttling test (leading untested hypothesis for the still-open symptom)    | **Paused 2026-07-24 — operator ask** ("let's check the locally running one first")                                                                                                                                                                                                                | operator resume                       |
| GCS Data Access audit-log cost finding (Cloud Logging, ~151 GB/7d, MTDS buckets)          | ✅ **Issue doc FILED 2026-07-24** — `plans/archive/2026_07/gcs_data_access_audit_log_cost_2026_07_24.md`; operator to route to Ikenna (or pick up Monday)                                                                                                                                         | Ikenna / operator                     |
| Whole-mock sign-off, all 5 tabs, tarball stamp scope                                      | ✅ **DONE 2026-07-21** — operator: "good to start … on all the tabs 1 to 5"; DO-NOT-START banner lifted (`pm@161200196`)                                                                                                                                                                          | —                                     |
| Pipeline (builds) view — backend + live UI tab                                            | ✅ **DONE** — `deployment-api@8eda1f8`/`0a920c2`, `deployment-ui@47e6379`/`038038e`                                                                                                                                                                                                               | —                                     |
| Deploy timeline view — backend + live UI tab                                              | ✅ **DONE 2026-07-23** — `deployment-api@72a0108`, `deployment-ui@797180c`                                                                                                                                                                                                                        | —                                     |
| Date-range picker + 7d default (both windowed live views)                                 | ✅ **DONE 2026-07-23** — operator ask, same turn as the Deploy timeline ship (`deployment-ui@797180c`)                                                                                                                                                                                            | —                                     |
| **What's running** view (the headline runtime join + drift classifier)                    | ✅ **DONE 2026-07-23** — `deployment-api@a13c667`, `deployment-ui@3210bb5`. Scoped to the Cloud Run (image) lane; `fragmented` always 0 for now (no traffic-split detection)                                                                                                                      | —                                     |
| Artifacts (registry inventory) view                                                       | ✅ **DONE 2026-07-23** — `deployment-api@a13c667`, `deployment-ui@3210bb5`. GCP AR only; AWS ECR stays parked/unread                                                                                                                                                                              | —                                     |
| Health (measured conditions) view                                                         | ✅ **DONE 2026-07-23** — `deployment-api@a13c667`, `deployment-ui@3210bb5`. Derives every condition from the other four views' own facts, zero new cloud calls                                                                                                                                    | —                                     |
| Per-column sort + filter + multi-select on every live table                               | ✅ **DONE 2026-07-23** — operator ask, same day as the last 3 views; `deployment-ui@3126b1b` + `@3210bb5`                                                                                                                                                                                         | —                                     |
| Snapshot worker (GCS parquet + DuckDB, the OOM-safe long-window read path)                | **Not started** — the live-scan cache (300s TTL) covers today's needs; the worker is for long-history + concurrent-load headroom                                                                                                                                                                  | —                                     |
| (A) tarball commit stamp (Phase 3c Option A) — the shell edit itself                      | ✅ **DONE 2026-07-27** — `deployment-service@d8b1411c` + `test_bom.py` Python-half test. All 7 audit conditions re-verified                                                                                                                                                                       | —                                     |
| Phase 3b cross-links (Deployments URL-param filter, console deep-links)                   | ✅ **DONE 2026-07-27** — `deployment-ui@74c0a7d`                                                                                                                                                                                                                                                  | —                                     |
| "Default view = What's running" (locked 2026-07-17, DECIDED 2026-07-24)                   | ✅ **DONE 2026-07-27** — `deployment-ui@fb1da34`                                                                                                                                                                                                                                                  | —                                     |
| Phase 3d (all 5 todos) — tarball provider, health condition, Pipeline/Artifacts verify    | ✅ **DONE 2026-07-27** — `deployment-api@3525bce`, `deployment-ui@05a087d`                                                                                                                                                                                                                        | —                                     |
| **Phase 3c live-launch verification (the shell edit's own verification gate)**            | ✅ **DONE 2026-07-27** — `measure-honest-coverage-20260727-234251` completed rc=0, `git_commit=f06eba12989d…` confirmed non-empty + matched against the serial console's manifest log. Phase 3c is now fully closed                                                                               | —                                     |
| Misattributed VM origin in the qg-snapshot-launcher-flake issue doc (another agent's doc) | **Not started** — low-priority correction, doesn't change that doc's recommended fix, see the new P3 todo above                                                                                                                                                                                   | —                                     |
| Issue doc for the pipeline bugs                                                           | ✅ **DONE 2026-07-21** — `issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`; only #4/#7 (AWS-deferred) + #3 (GCP, minor) open — **#1 RESOLVED 2026-07-24** (semver-agent confirmed deliberately dead; issue doc itself still needs the same correction as a follow-up) | Ikenna (his active CI files)          |
| Stale "Staging-first" quickmerge.sh messaging                                             | ✅ **RESOLVED — no action needed (operator 2026-07-24)**: cosmetic only, left as-is unless it starts causing real problems                                                                                                                                                                        | —                                     |
| AWS resume (App Runner + ECS + ECR)                                                       | **Cannot be done yet — operator-owned** — AWS intentionally parked; deferred until AWS credits are available                                                                                                                                                                                      | AWS credits                           |

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Explicit human/local-plan
  banner, dense ongoing operator sign-off history; remaining 12 items are either operator-paused, explicitly-optional
  stretch items, or follow-on cleanup tied to the same operator-reviewed design track.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added the real backend service module + frontend
  page as source targets (all 5 tabs already shipped there), dropped 2 codex refs tied to now-closed phases.
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-a6d668)**: KEEP-NA, valid — same as 2026-07-30; remaining
  12 items are operator-paused (CPU-throttling test), explicitly-optional stretch items (Phase 6 P3s), or follow-on
  cleanup tied to the same operator-reviewed design track.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: RESUMED the paused
  Phase 7 CPU-throttling investigation — operator confirmed ready. **RESOLVED same session**: live-checked
  `uts-shared-deployment-api`'s Cloud Run config, `cpu-throttling: false` already set; live-verified
  `/api/artifacts/images` returns full real data (39 repos, 0 empty) — symptom no longer reproducible, hypothesis
  confirmed correct, Phase 7's last open todo closed.
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, stale item closed — Phase 5's "file issue doc" todo was
  stale (the filing + bug #2 verification already happened 2026-07-21 under a different-named doc, see the closed todo
  above for the citation). Doc otherwise stays NA — human/local plan, dense operator sign-off history, remaining 10 open
  items are real follow-on/stretch work (1 sequencing-blocked on a net-new VM-launch deploy provider, 9 unblocked).
- **na-eligibility-audit 2026-08-08 (ui tranche)**: KEEP-NA, valid — checkbox-representation fix applied: split the
  prose-only "still open: image vulnerability-scan status" sentence (line ~683, trailing an `[x]`-checked parent) into
  its own `- [ ]` item, per `issues/ag_closeout_audit_ui_parked_2026_08_08.md` Finding 2 (3 prior passes had missed it,
  including this skill's own 2026-08-07 count). Open-item count is now 11 (was 10). Doc otherwise unchanged — same
  human/local plan, dense operator sign-off history; all 11 remaining items are real follow-on/stretch/P3 work (1 still
  sequencing-blocked, the rest unblocked but genuinely optional/low-priority), not defaulted/unassessed. No whole-doc
  RECLASSIFY candidate — this doc's satellite-batch extraction is already handled incrementally by
  `/ag-closeout-audit ui`'s batch1/batch2 mechanism (see `ui_consolidated_closeout_2026_07_30.md`), not this skill's
  remit.
- **round11 sweep 2026-08-09**: extracted 3 meta/doc items (tarball-bucket-resolution issue doc, AR/ECR scan-status
  check, misattributed-VM-origin correction) to `ui_satellite_ao_dispatch_batch3_2026_08_09.md` (+ finalize twin) — same
  class batch1 already validated safe here. 7 implementation-shaped items stay deferred per batch1's precedent. Doc
  stays NA; source checkboxes stay open until batch 3's finalize twin reconciles them.
- **context-scout 2026-08-15**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **2026-08-16**: vuln-scan todo DONE. GCP AR `SCANNING_DISABLED` (API off, not flipped — billing call). AWS ECR
  `scanOnPush` true on 9/20 repos, 0 actual scans (parked since 2026-06-27). No findings either side. Open-items: 10.
- **na-eligibility-audit 2026-08-17 (ui tranche)** [body-hash:fb83087f6d31c0d6]: KEEP-NA, valid — doc stays NA (dense,
  operator-reviewed in-flight build). Of 4 open items: 2 genuine deferred build/design work, 1 dependency-blocked
  (needs a net-new VM-launch-as-deploy provider), 1 confirmed stale duplicate (misattributed-VM-origin correction,
  already extracted to `ui_satellite_ao_dispatch_batch3_2026_08_09.md` item 3 — that batch's own copy hasn't shipped
  yet either, so not pre-flipped here; its gated finalize twin owns reconciling this checkbox once it does).
- **context-scout 2026-08-19**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-21 (ui tranche)**: RECLASSIFY (per-todo split) — of the 4 open items (Snapshot
  worker P2; What's running tab P3; Fleet-wide SHA-pinning P3 `_(stretch, optional)_`; misattributed-VM-origin
  correction P3), 1 (Snapshot worker) cleared the bounded-outcome bar — it names the exact script, the exact
  established pattern to mirror (the cost-observability snapshot-worker shape this plan already cites as "the ONE
  sanctioned shape"), and the exact output path — and was extracted to
  `ui_satellite_ao_dispatch_batch5_2026_08_21.md` item 1 (conflict-checked clean: no other active
  `assigned_vm: planning` doc under `parent_epic: observability_master`/`deployment_and_user_management_master`
  claims a snapshot-worker/artifact-snapshots build). The other 3 stay NA: "What's running tab" is genuinely
  sequencing-blocked on a net-new VM-launch-as-deploy provider that isn't scoped anywhere yet (a design call, not a
  todo); the SHA-pinning item is already structurally non-dispatchable via its own `_(stretch, optional)_` marker;
  the misattributed-VM-origin correction is confirmed ALREADY duplicated in
  `ui_satellite_ao_dispatch_batch3_2026_08_09.md` item 3 (still `status: active`, unlocked, per this doc's own
  2026-08-17 Progress Log note) — KEEP-NA-STALE (already-duplicated), citation already correct, no edit needed. Doc
  stays `assigned_vm: NA` overall (3 open items remain, all correctly gated).
