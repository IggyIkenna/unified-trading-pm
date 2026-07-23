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
last_updated: "2026-07-23"
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

## Pipeline bugs found (page-first: parked in an issue doc, do NOT fix here)

Operator decision 2026-07-17/21: the page reads the clouds directly so it works regardless of these; fixing them touches
CI files in Ikenna's active area → **parked, not fixed.** **RE-VERIFIED 2026-07-21 (the CI area was actively fixed
2026-07-20) and filed:** `plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`.
Most of the 2026-07-17 list resolved itself — see the issue doc for the full verified status. Summary:

1. `version` never sent → image tags SHA-only ~late June. **STILL OPEN but root-cause UNCONFIRMED** (could be
   intentional SHA-only tagging) — issue doc #1.
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
- [x] [OPERATOR] P0. **Tab 2 — Deploy timeline** — ✅ signed off 2026-07-21 (iterated: correctness + usefulness pass).
      `ui@e01e5fc`. Was one-service (uts-shared-deployment-api) + 4 static AWS rows; now **estate-wide** across 5 real
      sections: Cloud Run for that service (15 revs, each with a computed **held-for** interval so "what ran on date X"
      is a lookup) + other Cloud Run services + **GCE VM launches (a launch IS the tarball-lane deploy)** + the real AWS
      App Runner storm + ECS. New surfaces: **● live-now** badges, **human-vs-CI deployer** column (hand-deploys lit
      red), **config-only / new-code / live-now / failed** filter chips, per-row **console↗ / VM↗** links, and
      `resolve ↗` where a digest→SHA join exists but the value needs a fresh gcloud auth. **Real-page requirement (fold
      into the build):** a **date cursor** so "what ran on date X" is an actual selection — the held-for intervals
      already support the lookup; the real page's date-range picker provides the control.
- [x] [OPERATOR] P0. **Tab 3 — Pipeline** — ✅ signed off 2026-07-21 (iterated). `ui@e01e5fc`. Added **All / Failed /
      Image / Tarball / GCP / AWS** filter chips, surfaced the previously-dead `xlane` flag as a **⇄ both-lanes** badge
      (one commit built as image AND tarball), and a **shipped ↗** through-line hint on successful image builds. Drawer
      (step timeline + failure + log excerpt) unchanged. **Stale-fact fix `ui@57785a3`:** the note claiming the
      failure-watcher "only posts free text to Slack / stamps `unified-trading-pm`" was corrected — that watcher was
      **fixed 2026-07-20** (right repo + notify-slack dedup).
- [x] [OPERATOR] P0. **Tab 4 — Artifacts** — ✅ signed off 2026-07-21 (iterated). `ui@e01e5fc`. Was 8 image rows for 2
      repos; now **one row per repo** showing the real sprawl (**ECR inventory probed live 2026-07-21**): 20 repos,
      image counts, latest tags, last-push, **running? + state** (running / App-Runner-PAUSED / ECS-desired=0 /
      orphaned-GC / empty / still-pushing), with **running / orphaned-GC / empty / cloud** filters. GCP AR kept as the
      2026-07-17 sample + an honest aggregate row (full AR walk needs gcloud auth). **Real-page requirement (fold into
      the build):** a per-repo **size** column + a **GC-candidate** flag (no matching build AND not running) so the 1.5
      TB AR sprawl is actionable at row level (ties to the cost page). GCP side needs live auth → real-page, not mock.
      (Overlaps the Phase-6 P3 "orphaned-image GC candidates" stretch — promote into the v1 Artifacts columns.)
- [x] [OPERATOR] P0. **Tab 5 — Health** — ✅ signed off 2026-07-21 (iterated). `ui@e01e5fc`. Folded in 3 new
      **measured** deploy-lane findings (App Runner storm, orphaned ECR estate, ~40% config churn → 13 conditions),
      added severity **tiles + filter**, an **Area** column, and a **"see in <tab> ↗"** cross-link from every condition
      to the view that proves it. Note now states none of these fires an alert today. **Stale-fact fix `ui@57785a3`:**
      corrected the failure-watcher note (fixed 2026-07-20) and the AWS-tarball "`code/` has 0 objects" claim (now
      **populated**; real defect = the launcher's 404 bucket). The AWS-lane **bugs** (tarball mismatch, freeze-replay)
      are kept as **real defects tagged `AWS-deferred`**, distinct from the blue "parked · not a defect" tier (App
      Runner/ECR) — **operator CONFIRMED this framing 2026-07-21** ("what's broken is broken").
- [x] [OPERATOR] P0. ✅ **AWS-deferred reframe applied across the mock** (operator 2026-07-21) — the AWS state is
      **intentional parking (no credits)**, not breakage. Added a top **GCP-active / AWS-parked banner**; Deploy
      timeline tiles + section headers reframed to "intentionally parked · last active 2026-05-22"; Artifacts states
      `orphaned · GC` → **`parked · AWS deferred`** (kept, not GC) with the GCP legacy AR aggregate as the only true GC
      row; Health demoted the 2 AWS conditions to a blue **`deferred` (not a defect)** tier (now high 5 / med 3 / low 3
      / deferred 2). ✅ Confirmed 2026-07-21 ("what's broken is broken; fix AWS when we need AWS").
- [x] [OPERATOR] P0. ✅ **Final sign-off on the whole mock — 2026-07-21** → Phases 1–6 UNBLOCKED, build started.

### Phase 1 — backend read + snapshot layer (deployment-api)

- [x] [BACKEND] P1. ✅ New `services/artifact_pipeline/` service on the cost-observability shape: providers for Cloud
      Build, Artifact Registry, Cloud Run revisions — `deployment-api@8eda1f8`/`72a0108`/`a13c667`. CodeBuild, ECR, App
      Runner/ECS, tarball manifests stay deferred (AWS parked; VM tarball lane honestly unknown pending Phase 3c).
- [ ] [BACKEND] P2. Snapshot worker (`scripts/artifact_snapshot_worker.py`, Cloud Scheduler / `POST …/snapshot-run`):
      periodically read the live APIs, append normalized parquet to `gs://{state}/artifact-snapshots/…`; DuckDB-over-
      parquet read path with `BoundedCache`. Honour the OOM constraints; no per-request cloud scans. Downgraded from P1
      — the live-scan 300s TTL cache covers today's load; this is for long-history + concurrent-load headroom.
- [x] [BACKEND] P1. ✅ The runtime join — `deployment-api@a13c667` (2026-07-23): live workload digest → matched AR image
      (one `list_docker_images` call over the canonical `unified-trading-system` repo, ~3365 images/20 repos, ~4s cold)
      → a SHA-shaped tag on that image → the `BuildFact` carrying that (repo, sha) → drift verdict. **Collapsed
      `DRIFT_PINNED` into `DRIFT_OK`** — Cloud Run's API exposes only the resolved digest, never the tag the operator
      originally deployed with, so "deployed via an immutable `@sha256` pin" and "deployed via a `:<sha>` tag that
      happens to still resolve to this digest" are OBSERVATIONALLY IDENTICAL from this join; claiming the stronger
      `pinned` would be unprovable, so both read as the one honest `ok` ("traceable to a commit"). `DRIFT_HAND` reuses
      the deployer-identity signal already computed for Deploy timeline (`deployer != "Cloud     Build"`), not a
      separate provenance check. Deployer identity already lands from `revision.creator` (shipped with Deploy timeline,
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
- [ ] [UI] P2. **NEW (2026-07-23) — revisit "default view = What's running."** The plan locked this shape 2026-07-17
      (line 127); it was never implemented because Pipeline shipped first and nothing since has flipped
      `useState<TabId>` back. Now that What's running is live, either flip the default or explicitly re-decide with the
      operator — don't let a stale shape decision silently persist.
- [x] [UI] P1. ✅ **NEW (operator ask 2026-07-23) — per-column sort + filter on every live table, multi-select on each
      view's identity column.** `deployment-ui@3126b1b` (Pipeline + Deploy timeline) + `@3210bb5` (Artifacts, What's
      running, Health). Shared `ColumnHeader`/`MultiSelectFilter`/`TextFilterInput` primitives, client-side over the
      already-loaded data (no new fetch) — not originally in this plan's scope, captured + closed same-turn.

### Phase 3b — cross-links (deployment-ui + deployment-api) — operator requirement 2026-07-17

> **🟢 UNBLOCKED 2026-07-23** — this phase was gated on the What's running view landing (the version row that would
> deep-link); it shipped as `deployment-ui@3210bb5`/`deployment-api@a13c667` this session. Recommended next phase.

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
- **2026-07-21 — Tabs 2–5 correctness+usefulness pass, AWS-deferred reframe, issue doc filed (3 ships).** (1)
  `ui@e01e5fc` — Deploy timeline made estate-wide (Cloud Run + GCE VM launches as tarball-lane deploys + real AWS
  storm), live-now badges, held-for intervals, human-vs-CI deployer, filter chips, console links; Pipeline gained filter
  chips + the ⇄-both-lanes xlane badge; Artifacts rebuilt to one-row-per-repo from a **live ECR inventory** (20 repos,
  real counts); Health folded in deploy-lane findings + severity filter + cross-links. All verified in jsdom (0 script
  errors). AWS data probed live 2026-07-21; GCP stayed the 2026-07-17 sample (auth still expired). (2) `ui@fa38eaa` +
  `pm@f25f10911` — reframed AWS from red/defect to **intentionally parked** (operator: no AWS credits, GCP is sole
  active path): top banner, Deploy/Artifacts/Health states → parked/deferred, Health `deferred` tier. (3) `pm@6f52496a4`
  — filed `issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` after re-verifying every audit
  finding against current code (see the new lesson below). **Still mock-only; no page code started.**
- **2026-07-21 (later) — build-kickoff prep + mock stale-fact corrections (`ui@57785a3`).** Operator signalled readiness
  to build the image tab and to include the tarball SHA stamp **now** ("do it now" — Phase 3c Option A folds into the
  first build). Before starting, re-read Tabs 2–5 against current verified facts and shipped `ui@57785a3` fixing 3 stale
  spots: the Tab-3 + Tab-5 failure-watcher note (that watcher was **fixed 2026-07-20** — right repo + notify-slack
  dedup) and the Tab-5 AWS-tarball "`code/` 0 objects" claim (now **populated**; real defect = the launcher's 404
  bucket). Kept the AWS-lane bugs as real defects tagged `AWS-deferred`, distinct from the blue "parked · not a defect"
  tier — flagged for operator confirmation. Mapped the full build blueprint from the two reference services
  (`cost_observability` backend service + `CostObservability.tsx` page — providers/`_safe` isolation, snapshot worker,
  DuckDB-over-parquet, `_resolve_range`, reqId ordering guard, mock-handler ordering, NAV_GROUPS/route seams). Captured
  two real-page requirements as gate-item notes (Tab-4 per-repo size + GC-candidate flag; Tab-2 date cursor). Verified
  in jsdom (all 5 tabs render, 0 errors); content-verified on origin (ahead=0). **Still mock-only; awaiting operator
  sign-off on Tabs 2–5 before any page code.**
- **2026-07-21 (later) — build STARTED (operator signed off all 5 tabs); backend Phase 1/2 first vertical shipped.**
  Operator: "good to start … on all the tabs 1 to 5" + AWS-lane framing confirmed ("what's broken is broken"). Flipped
  the DO-NOT-START banner → 🟢 BUILD STARTED and ticked all 5 tab gates + the final sign-off (`pm@161200196`). Built
  `deployment_api/services/artifact_pipeline/` on the cost-observability shape and shipped the first end-to-end vertical
  — the **Pipeline (builds) view** — as **`deployment-api@8eda1f8`**: the normalized contract for ALL 5 views
  (`models.py` — internal `BuildFact`/`DeployFact`/`ImageFact` + Pydantic response models), the TTL cache, the `safe[T]`
  per-source isolation wrapper, the `gcp_cloud_builds` provider (Cloud Build → `BuildFact`, adding the structured
  `failure_info` + `steps` the old build-history route dropped), `service.builds()` (window resolution, dup + cross-lane
  detection, data-derived stats), `GET /api/artifacts/builds` + the loud `_resolve_range` 400 gate, main.py
  registration, and 13 `--block-network` unit tests. Full deployment-api gate green (basedpyright 0, ruff clean, 4783
  tests). **Remaining backend:** 4 views (images / deploys / running-join+drift / health) + their providers (AR
  versions, Cloud Run revisions, ECR, App Runner/ECS, CodeBuild, tarball manifests) + the snapshot worker + the runtime
  digest→SHA join; then the UI page + Phase 3c tarball stamp.
- **2026-07-21 (later still) — UI vertical slice 1 shipped: the `/ops/artifacts` page with a LIVE Pipeline tab
  (`deployment-ui@47e6379`).** Operator asked for "at least one tab … in the actual UI". Ran the API (:8004, real GCP
  data via ADC/`GCP_PROJECT_ID=central-element-323112`, `DISABLE_AUTH=true`) + the UI (:5183) locally for the operator
  first — verified 400 live builds / 98.2% success / 7 failures / 26 wasted-dups flowing end-to-end. Then built
  `src/pages/ArtifactPipeline.tsx` (self-contained, mirroring `CostObservability`: plain fetch + `useRef` reqId guard +
  inline token-styled primitives): a 5-tab shell (running / deploy / **pipeline** / artifacts / health) where the
  **Pipeline (builds) tab is wired live to `GET /api/artifacts/builds`** — data-derived stat band (total / success-rate
  / failed / median / wasted-dup), client-side lane/cloud/status filters, and a per-build failure + step-timeline
  drawer; the other four tabs render an honest "backend in progress" placeholder. Wired the route (`App.tsx`) + a
  Fleet&Cost `NAV_GROUPS` entry (`NavMenu.tsx` — auto-lights `TopNavBar` + satisfies the orphan-audit),
  `getArtifactBuilds`
  - `BuildsResponse`/`BuildRow`/`BuildStep`/`BuildsStats` types on `deploymentApi.ts`, a `mockArtifactBuilds` handler on
    `mock-api.ts`, **5 Vitest** unit tests + a **2-case `pw:L2`** smoke spec (`tests/smoke/artifact-pipeline.spec.ts`;
    cites this plan). Bumped the two nav-count tests (15→16 canonical entries). Full deployment-ui gate green (tsc +
    eslint
  - orphan-audit + 1047 tests + build + codex checks incl. no-hardcoded-colours). Shipped through two peer-rebase
    sentinel-stale cycles (busy branch) — pull-rebase kept the merged tree, content-verified ahead=0. **Remaining UI:**
    the 4 placeholder tabs' real views + their `pw:L2` coverage + `__mock` race hooks, each gated on its per-view
    backend (deploys next).
- **2026-07-23 — Deploy timeline vertical (2nd view) shipped end-to-end, plus a live production bugfix caught building
  it.** Operator: "continue with the remaining pages … work in worktrees tabs 2" (confirmed the per-slot clone model IS
  the workspace's "worktree" isolation — no separate mechanism). Synced all 3 repos first; discovered a DIFFERENT
  operator (`harshkantariya`, host `harsh_pc`) is independently working this same plan on their own slot-2 clone —
  `deployment-api@0a920c2` (a 30s RPC-deadline fix for the exact "keeps loading" hang the operator had just reported)
  and `deployment-ui@038038e` (the frontend counterpart: a 45s `AbortController` timeout on `getArtifactBuilds`) both
  landed mid-session. Neither touched the Deploys view — confirmed via full history grep before starting, no collision.
  - **Backend — `deployment-api@72a0108`.** `gcp_cloud_run_revisions()` provider: reuses `list_cloud_run_services()` (no
    extra RPC) to enumerate workloads + resolve the live revision, lists each service's revisions (`RevisionsClient`,
    same `_gcp_sdk` boundary), classifies each into new/config/rollback/failed by walking the digest sequence
    chronologically, and computes "held for" via ONE-STEP-LOOKAHEAD to the revision that replaced it.
    `service.deploys()` mirrors `builds()`'s window/stats shape, with one deliberate exception: `live_now` is a
    POINT-IN-TIME count over ALL facts, never the windowed subset — a narrow date range must not undercount what's
    actually serving. `GET /api/artifacts/deploys` + 12 new `--block-network` tests (21 total). MEASURED live: 690
    revisions / 16 services, ~9-11s cold scan (comparable to builds' ~5s, same 300s cache).
  - **Live bug found + fixed in the SAME file (findings-triage: same-file → same commit).** Google-cloud repeated fields
    (`Build.steps`, `Build.images`, `Revision.containers`, `Revision.conditions`) are runtime instances of
    `proto.marshal.collections.repeated.Repeated`/`RepeatedComposite` — NOT `list`/`tuple` — so the
    `isinstance(x, (list, tuple))` gate used throughout `providers.py` silently dropped every real field. The
    ALREADY-SHIPPED Pipeline view's step-timeline drawer and "Produced" column have been silently empty for every real
    build since `8eda1f8`. Root-caused via static introspection (no live RPC needed — built a synthetic proto message,
    no network flakiness in the way) before confirming live. Fixed with one shared `_as_item_list()` helper (any
    iterable, not just list/tuple); verified against live Cloud Build + Cloud Run data both before and after. Also
    found + fixed a `held_for` sign-error (subtraction direction backwards, always computed negative → always empty) via
    the SAME live-verification pass — caught because the numbers looked wrong, not because a test failed.
  - **A genuine finding, not a bug: `deployment-service` has ZERO working Cloud Run revisions, ever.** Its one-ever
    revision's `Ready` condition is `CONDITION_FAILED` ("container failed to start and listen on PORT=8080"); since it
    never went ready, `list_cloud_run_services()`'s `latest_created_revision` fallback still reports it as the service's
    newest state — so the page correctly shows `live=true, change_type=failed` for it. Left as-is (verified via the real
    condition message, not assumed) — exactly the kind of defect this page exists to surface.
  - **UI — `deployment-ui@797180c`.** `DeployTimelineView` mirrors `PipelineView`'s shape (data-derived stat band,
    filter chips, flat table — no drawer, `DeployRow` has no nested detail to expand); `DEPLOY_FILTERS` (all / code /
    live / fail) match the frozen mock's semantics exactly, filtered CLIENT-SIDE like Pipeline (one full-window fetch,
    no round-trip per filter click). Both live views now fetch eagerly + concurrently on mount/window-change, each with
    its own request-id guard (mirrors `CostObservability`'s `loadCore` pattern). **Operator ask, same turn:** default
    window 7d (was 14d) + a real date-range picker on BOTH live views — ported `CostObservability`'s `DateRangePicker`
    verbatim (native `<input type="date">`, `min`/`max` wired to the API's 366-day cap, a hand-picked range deselects
    the day-preset pills and vice versa). Factored the peer's ad hoc 45s abort-timeout into a shared
    `fetchArtifactApi()` helper reused by the new `getArtifactDeploys` (same hang protection, one implementation, not
    two copies to drift). 9 Vitest + 4 `pw:L2` tests; full deployment-ui gate green (101 tests). **Remaining UI:** the 3
    placeholder tabs' real views (running / artifacts / health), each gated on its per-view backend.
- **2026-07-23 (later) — a help/tooltip dialog shipped for the page** (operator ask, out-of-plan-scope but small):
  `deployment-ui@cdcd3df` — a `HelpCircle` button opening a `CostHelpDialog`-style dialog explaining the page's controls
  and, at the time, the two live tabs' columns. Superseded by the later help-dialog update below once all five tabs
  shipped.
- **2026-07-23 (later still) — the remaining three views (Artifacts, What's running, Health) all shipped in one session,
  plus per-column sort/filter/multi-select across all five tables** (operator: "continue with the remaining 3 pages"
  then "make sure they also have these sort and filter and select capabilities").
  - **Backend — `deployment-api@a13c667`.** Added `RegistryImageFact` (a new per-image internal fact type, distinct from
    the existing per-repo `ImageFact` roll-up) and `gcp_artifact_registry_images()`: one `list_docker_images` RPC over
    the single canonical `unified-trading-system` AR repository returns every service's every pushed image in one shot
    (MEASURED live: 3365 images across 20 repos, ~4s cold with `page_size=1000`) — no per-service repo enumeration
    needed, and no scan cap was actually load-bearing (5000 is a generous runaway-safety net). `service.images()`
    aggregates that list per `(cloud, registry, repo)` into the `ImageRow` roll-up (tags of the newest image, summed
    size, a `running_on` cross-ref against live Deploy-timeline digests, and a `state` derived from
    running/age-since-last-push — `STATE_LEGACY` at >30 days idle with nothing running it). `service.running()` is the
    plan's headline runtime join: joins each live `DeployFact`'s digest against the AR image list (digest→image), picks
    a SHA-shaped tag off the matched image (→ the git commit), and joins that `(repo, sha)` to the already-cached
    `BuildFact` list for the trigger/branch. `service.health()` makes ZERO new cloud calls — every condition is derived
    from the builds/deploys/images/running facts the other three view-methods already fetched (AWS-deferred is always
    emitted; live-but-never-ready deploys → high; recent build failures / dup builds → med/low; floating-tag or
    hand-deployed live workloads → med; the VM-tarball-lane gap → med, always; AR registry sprawl ≥500 images/repo →
    low). 12 new `--block-network` unit tests (33 total); full deployment-api gate green.
  - **A real design choice, not a bug: `DRIFT_PINNED` never fires — everything traceable reads `DRIFT_OK`.** Cloud Run's
    API exposes only the RESOLVED digest on a revision, never the tag the operator originally deployed with — so a
    genuine `@sha256`-pin deploy and a `:<sha>`-tag deploy that happens to still resolve to the same digest are
    OBSERVATIONALLY IDENTICAL from this join. Claiming the stronger `pinned` verdict would be a fabricated precision
    this data can't support, so both collapse to the one honest `ok` ("traceable to a commit, however it got there").
    Recorded here so a future session doesn't "fix" `DRIFT_PINNED` into firing without re-deriving why it doesn't.
  - **A ruff gotcha, workspace-relevant beyond this file: `# noqa: <fake-code>` is a soft warning,
    `# noqa: <real-but- disabled-code>` is a hard RUF100 error.** The existing `# noqa: cloud-sdk-direct` convention
    (`routes/builds.py`) uses a made-up string as the noqa "code" — ruff can't parse it as a real code, so it degrades
    to a non-blocking "invalid noqa directive" WARNING and the diagnostic underneath (the `TID251` banned-import) stays
    genuinely unsuppressed. That's fine for the LINT step (which doesn't select TID251) but means the STEP-5.95 ratchet
    script (which runs an ISOLATED `ruff --select TID251` pass) counts it as a real, uncounted-by-noqa violation — so a
    new `from google.cloud import ...` site with only that fake-code comment silently pushes the ratchet's ONE global
    ceiling past baseline, even though it "looked" suppressed. The fix already exists in this codebase
    (`_ci_status_firestore_store.py`): use the REAL code, `# noqa: TID251`, which the ratchet's isolated pass properly
    honors — but that then makes the PLAIN `ruff check` (LINT step, which never selects TID251) flag the noqa itself as
    unused (`RUF100`, since TID251 isn't in the selected set there), which IS a hard blocking error under this repo's
    default `select = [...]` (RUF is in it). Resolved via `pyproject.toml`'s existing escape hatch: a
    `[tool.ruff.lint.per-file-ignores]` entry silencing `RUF100` for the one file — added
    `"deployment_api/services/artifact_pipeline/providers.py" = ["RUF100"]` alongside the pre-existing
    `_ci_status_firestore_store.py` entry. Two separate ruff invocations, two different rule sets, same line — always
    check both when adding a new `# noqa: TID251` site.
  - **UI — `deployment-ui@3210bb5`.** `ArtifactsView`/`RunningView`/`HealthView` replace the three `ComingSoon`
    placeholders, matching Pipeline/Deploy timeline's established shape (data-derived stat tiles, filter-pill bar,
    client-side table). `RunningView` flattens `RunningGroup.versions` to one row per live version (today always length
    1 per service — Cloud Run traffic-split isn't detected by this join, so `fragmented` reads 0 fleet-wide; the shape
    supports a future multi-version row without a contract change) and reuses the Pipeline drawer pattern (click a row
    to expand the full `why` + host list). `images`/`running`/`health` are NOT windowed by date — they load once on
    mount and only refetch on an explicit Refresh, unlike Pipeline/Deploy timeline's window-driven fetch.
  - **The same-turn operator ask — per-column sort + filter + multi-select — landed in two ships, not duplicated
    logic.** `@3126b1b` built the shared primitives (`ColumnHeader`, `MultiSelectFilter`, `TextFilterInput`,
    `toggleColumnSort`/`compareSortValues`) for Pipeline + Deploy timeline; `@3210bb5` reused them verbatim for the
    three new views, adding only each view's own column-key `switch` (`imageSortValue`/`runningSortValue`/
    `healthSortValue`) and column-filter shape. Every table's identity column (Repo / Workload / Service / Area) is
    explicitly multi-select per the operator's ask; other bounded columns (Cloud, State, Change, Drift, Severity) got
    the same multi-select for consistency rather than a narrower text box.
  - Coverage: 19 Vitest (page total) + 10 `pw:L2` (spec total); full deployment-ui gate green (1097 tests workspace-
    wide). Both live dev servers (tmux-hosted, `:5183` UI / `:8004` API) picked up every change via Vite HMR — verified
    healthy post-ship, no restart needed.

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
- **An audit finding decays — re-verify against CURRENT code before filing or acting, especially in a hot area
  (2026-07-21).** The 2026-07-17 pipeline-bug list was ~4 days old and the CI area is the workspace's hottest (Ikenna
  pushed to PM 9 min before I checked; `setup-data-pipeline-vm.sh` 7h, `freeze-deferred-build-replay.yml` 24h). On
  re-check: **#5 was already FIXED 2026-07-20**, **#2 was not-a-bug** (never reproduced), **#6 had partially landed**
  (SHA now measured at boot). Had I filed the list as-was, ~half would have been stale/duplicate. The discipline that
  caught it: grep the 444 issue docs for existing coverage → **READ** the candidates (not grep-then-conclude) → verify
  each bug against the live file + a live probe (the AWS bucket 404, the `deferred-aws-build-` vs `deferred-build-`
  filter) → file only what survives, and record the "verified NOT open" set so nobody re-investigates.
- **"Parked" ≠ "broken" — do not frame an intentional-off state as a defect (operator 2026-07-21).** I first rendered
  the AWS App Runner PAUSED / ECR-idle states as high-severity red defects ("orphaned · GC"). They are **deliberate**:
  AWS is deferred (no credits), GCP is the sole active production path. Fixing code is free; only creating/deploying AWS
  images costs credits — so AWS-side code bugs are _deferred-with-AWS_, not urgent, and the parked estate is _kept_, not
  a GC candidate. When a resource is off, establish WHY (intentional vs failure) before labelling it.
- **Editing a teammate's actively-hot files is a collision risk, not just a cost question.** When the operator green-lit
  fixing the bugs, the real blocker surfaced as collision (Ikenna is live in every file these bugs live in), not cost.
  Surfaced it and parked the fixes in the issue doc with "loop Ikenna in first" rather than barging into fleet-critical
  CI/boot files. Recurring: the multi-agent-safety "never edit recently-pushed files" rule is about blast radius.
- **A new `deployment_api.services.*` submodule is INVISIBLE to the unit suite until registered in
  `tests/unit/conftest.py` (2026-07-21).** That conftest replaces `deployment_api.services` with a stub package whose
  `__path__ = []`, then hand-injects a curated list of real submodules into `sys.modules` (`cost_observability` is one).
  A new service dotted-imports fine under plain `python` and passes basedpyright, but pytest collection dies with
  `ModuleNotFoundError: No module named 'deployment_api.services.<new>'` — and because `main.py` imports the new route,
  it CASCADES to break every test that imports the app. Fix: register the new service exactly like `cost_observability`
  (pre-import + `sys.modules["deployment_api.services.<new>"] = real_<svc>`). Plain-import / basedpyright / ruff all
  hide it because only pytest loads that conftest — only the FULL gate catches it. Cost one gate cycle; now fixed once
  for the whole `artifact_pipeline` package (the remaining 4 views won't re-hit it).
- **`isinstance(x, (list, tuple))` is the WRONG check for any google-cloud protobuf repeated field — workspace-wide, not
  just here (2026-07-23).** Repeated fields (`Build.steps`, `Build.images`, `Revision.containers`,
  `Revision.conditions`, and presumably more across the codebase) are `proto.marshal.collections.repeated.Repeated` /
  `RepeatedComposite` at runtime — neither is a `list` or `tuple` subclass, so that isinstance gate silently returns
  "empty" for real data while a hand-built test double using a plain list sails through every unit test. This shipped
  silently in `8eda1f8` and was only caught because a NEW call site (`Revision.containers`) hit the identical pattern
  and produced an empty digest that looked wrong on inspection — the ORIGINAL bug (`Build.steps`/`images`) would still
  be unnoticed today without that coincidence. Grep `isinstance(.*\(list, tuple\))` against any file that reads a
  `google.cloud.*` proto response before trusting its "empty" case. Fix pattern: normalize via
  `list(cast("Iterable[object]", value))` in a try/except TypeError, not an isinstance gate.
- **Static introspection beats a live RPC for a data-shape question, and sidesteps live-service flakiness.** Diagnosing
  the `RepeatedComposite` bug needed to know a proto field's RUNTIME type, not its live VALUE — a synthetic
  `cb.Build()` + `.steps.append(...)` answered it with zero network calls, in the same window where live Cloud Build
  RPCs were intermittently hanging (a transient, unexplained blip — ADC/network were independently confirmed healthy).
  When the question is "what type is this," construct the object; don't fight a flaky network for it.
- **A collision check is grep-before-build, not grep-after-symptom.** Before starting the Deploys vertical, checked
  `git log --oneline --all --grep=deploy -- <the exact files about to be touched>` and the plan's `locked_by:` — both
  clear — BEFORE writing a line of provider/service/route code, not after noticing a conflict. Caught mid-session that a
  different operator (`harshkantariya`, host `harsh_pc`) is independently active on this exact plan, on their own slot-2
  clone; their one real-code commit that turn was a narrow, reactive fix to the SAME symptom this session had just
  diagnosed for the operator (the builds hang) — not a race on unclaimed scope. Multi-agent plans need this check before
  every new vertical, not just before a risky one.
- **A registry's byte-size sprawl and its image COUNT are independent signals — the plan's own "~1.5 TB" figure primed
  an assumption that didn't hold.** Before probing live, ~1.5 TB suggested a registry too large to fully list. MEASURED:
  the whole `unified-trading-system` AR repo is only 3365 images (20 repos), listed cold in ~4s — the byte figure is
  dominated by average image SIZE (ML/data-heavy services), not image COUNT. A scan cap sized for "1.5 TB of data" would
  have been massively over-provisioned for what's actually a cheap, fully-listable metadata call. Measure the actual
  axis you're worried about (count vs. bytes) before sizing a safety cap around the wrong one.
- **Two ruff invocations, two different rule sets, on the same file — check both, not just the one CI step you're
  staring at.** The plain `ruff check` (LINT step) and the STEP-5.95 ratchet's isolated `--select TID251` pass read the
  SAME `# noqa` comment under DIFFERENT enabled-rule sets, so a fix for one broke the other twice in sequence during
  this session (fake-code noqa → ratchet counts it as unsuppressed; real-code `TID251` noqa → plain lint flags it as
  `RUF100` unused). The existing `_ci_status_firestore_store.py` precedent (a `per-file-ignores: RUF100` entry) was the
  answer, but only visible by reading `pyproject.toml` directly — the two CI step names alone didn't point at it. When a
  `# noqa: TID251` (or any two-differently-configured-invocation rule) won't go green, grep `pyproject.toml` for how the
  ONE prior site that already worked solved it, rather than iterating noqa text blind.

## Deferred work after 2026-07-23

> Superseded 2026-07-23 (again, same day) — the table below described the state after Pipeline + Deploy timeline
> shipped, running/artifacts/health "not started". All five views are now live (`deployment-api@a13c667`,
> `deployment-ui@3210bb5`), plus per-column sort/filter/multi-select workspace-wide on the page. This is the current
> state.

**Recommended NEXT: Phase 3b cross-links** (the Deployments URL-param filter + console deep-links) — it was explicitly
gated on the Running view landing (the version row that deep-links out), which just shipped; the backend half is audited
cheap (~2-line additive `DeploymentItem` field + reuse an existing `consoleUrl()` helper). The snapshot worker and the
tarball commit stamp (Phase 3c) are the other two real remaining Phase-1/3 items but are lower-urgency (the live-scan
cache already covers today's load; the tarball stamp needs a scheduled live VM launch to verify, not more code).

| Item                                                                       | State / why deferred                                                                                                                                                         | Blocked on                             |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| Whole-mock sign-off, all 5 tabs, tarball stamp scope                       | ✅ **DONE 2026-07-21** — operator: "good to start … on all the tabs 1 to 5"; DO-NOT-START banner lifted (`pm@161200196`)                                                     | —                                      |
| Pipeline (builds) view — backend + live UI tab                             | ✅ **DONE** — `deployment-api@8eda1f8`/`0a920c2`, `deployment-ui@47e6379`/`038038e`                                                                                          | —                                      |
| Deploy timeline view — backend + live UI tab                               | ✅ **DONE 2026-07-23** — `deployment-api@72a0108`, `deployment-ui@797180c`                                                                                                   | —                                      |
| Date-range picker + 7d default (both windowed live views)                  | ✅ **DONE 2026-07-23** — operator ask, same turn as the Deploy timeline ship (`deployment-ui@797180c`)                                                                       | —                                      |
| **What's running** view (the headline runtime join + drift classifier)     | ✅ **DONE 2026-07-23** — `deployment-api@a13c667`, `deployment-ui@3210bb5`. Scoped to the Cloud Run (image) lane; `fragmented` always 0 for now (no traffic-split detection) | —                                      |
| Artifacts (registry inventory) view                                        | ✅ **DONE 2026-07-23** — `deployment-api@a13c667`, `deployment-ui@3210bb5`. GCP AR only; AWS ECR stays parked/unread                                                         | —                                      |
| Health (measured conditions) view                                          | ✅ **DONE 2026-07-23** — `deployment-api@a13c667`, `deployment-ui@3210bb5`. Derives every condition from the other four views' own facts, zero new cloud calls               | —                                      |
| Per-column sort + filter + multi-select on every live table                | ✅ **DONE 2026-07-23** — operator ask, same day as the last 3 views; `deployment-ui@3126b1b` + `@3210bb5`                                                                    | —                                      |
| Snapshot worker (GCS parquet + DuckDB, the OOM-safe long-window read path) | **Not started** — the live-scan cache (300s TTL) covers today's needs; the worker is for long-history + concurrent-load headroom                                             | —                                      |
| (A) tarball commit stamp (Phase 3c Option A)                               | **Cannot be done yet** — audit-cleared YES-WITH-CONDITIONS; verify via a live EPHEMERAL_BATCH launch (no CI covers the shell file)                                           | a deliberate operator-scheduled launch |
| Phase 3b cross-links (Deployments URL-param filter, console deep-links)    | 🟢 **UNBLOCKED, next recommended** — audited cheap (2-line + reuse `consoleUrl()`); its one gate (Running view landing) is now clear                                         | —                                      |
| "Default view = What's running" (locked 2026-07-17, never implemented)     | **Not started** — page still defaults to Pipeline; re-decide with the operator or just flip it now that Running is live                                                      | operator confirmation (or just do it)  |
| Issue doc for the pipeline bugs                                            | ✅ **DONE 2026-07-21** — `issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`; only #4/#7 (AWS-deferred) + #1/#3 (GCP) open                         | Ikenna (his active CI files)           |
| AWS resume (App Runner + ECS + ECR)                                        | **Cannot be done yet — operator-owned** — AWS intentionally parked; deferred until AWS credits are available                                                                 | AWS credits                            |
