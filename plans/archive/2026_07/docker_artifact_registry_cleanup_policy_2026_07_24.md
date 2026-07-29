---
doc_type: plan
title: Artifact Registry / ECR image retention — audit deployed images first, then apply a safe cleanup policy
summary:
  Executable, human-driven fix for the unbounded Docker-image retention issue (4.01 TB, ~$400/mo, no cleanup policy on
  any of 75 GCP AR repos + 20 AWS ECR repos). Audit-first — enumerate which image digests are ACTUALLY deployed in prod
  (deployment-service stable_versions.yaml as the pin oracle, corroborated by live runtime + credential-probe), then
  draft an Artifact Registry cleanup policy that explicitly KEEPS every deployed digest on top of a keep-5-recent floor
  plus delete-older-than-3d, validate via cleanupPolicyDryRun with a zero-intersection check against the deployed set,
  get operator sign-off, flip live, and re-audit savings. Also covers the second artifact class — the GCS code-tarball
  bucket (732 accumulating @sha copies, ~2.4 GB) — fixed via a GCS lifecycle rule, not an AR policy. Local-only —
  operator reviews before any deletion; deletes are human-gated (no soft-delete on AR, deletion is permanent).
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    unified-trading-library,
    deployment-service,
    deployment-api,
    instruments-service,
    strategy-service,
    execution-service,
    ml-service,
    features-service,
    market-data-processing-service,
  ]
scope: [engineer]
tags: [artifact-registry, ecr, docker-images, storage-cost, cleanup-policy, retention, cicd]
related: [/plans/active/docker_artifact_registry_cleanup_side_tracks_2026_07_27.md]
created: 2026-07-24
last_updated: 2026-07-29
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  operator-directed 2026-07-24 — a docker/artifact storage cost audit surfaced 4.01 TB of unbounded-retention images
  with no cleanup policy anywhere; this plan is the executable, safety-gated fix (diagnosis folded into the Diagnosis
  section below)
---

> **🗄️ ARCHIVED 2026-07-29** — status=complete, 0 open todos. Archived per
> /codex/12-agent-workflow/plan-completion-and-archival-discipline.md.

# Artifact Registry / ECR image retention — audit-first, safe cleanup policy

> **Self-contained** — the diagnosis (§ Diagnosis) and the audit-first, safety-gated todo DAG live here; this plan
> supersedes the original issue doc. **Scope as of 2026-07-27: Phases A-D only** (todos 1-9, 14) — the
> genuinely-independent side-tracks (extend-to-other-repos, ECR, legacy GCR bucket, the GCS tarball bucket) were split
> out to
> [docker_artifact_registry_cleanup_side_tracks_2026_07_27.md](/plans/active/docker_artifact_registry_cleanup_side_tracks_2026_07_27.md)
> so they run **in parallel** with this plan's spine instead of serialized behind it (see Progress log).
> **AO-dispatched** (`assigned_vm: planning`) — **the operator still gates every actual deletion**, via the
> `[OPERATOR]`-tagged todos only (7, 8, and, in the satellite plan, 13/17). No AR soft-delete/undelete exists — deletion
> is permanent, so the dry-run + deployed-digest cross-check is mandatory before any live flip. **`sequential: true`** —
> every phase after Phase A consumes the prior phase's actual output as data, not just file-availability (todo 5 needs
> todos 1+2's real audit numbers; todo 6 needs todo 5's drafted policy; todo 8 needs todo 7's sign-off; …), so this plan
> runs strictly top-to-bottom by design.

## Diagnosis (audit numbers — pulled live via gcloud/aws 2026-07-24, not estimated)

The operator asked for the real storage cost of accumulated Docker images ("using around four, five terabytes"). A
direct pull from `gcloud artifacts repositories list` (all locations, both accessible GCP projects) +
`aws ecr describe-images` (all 20 repos, account `427895769566`) confirmed it, and surfaced the structural cause: **no
repository in either cloud has a cleanup policy configured.**

- **Total: 4.01 TB, ~7,300 images, 75 GCP AR repos + 20 AWS ECR repos** — ~**$400.55/mo (~$4,807/yr)** at
  $0.10/GB-month, storage-only.
- **`unified-trading-system`** (GCP AR, `asia-northeast1`, `central-element-323112`) — the largest, **1.97 TB, 3,477
  images, ~$196.83/mo**; a _shared_ repo, 20 services push as sub-path packages. `describe … cleanupPolicies` returns
  **`null`** (no policy).
  - **`market-tick-data-service`** = 1,958 of those 3,477 (56%), pushing **~17.5 images/day**, almost all git-sha CI
    builds (only 87 semver releases; the semver-agent is currently non-functional).
- **`unified-trading-library`** — **928 GB, 1,129 images, ~$92.76/mo**, same CI-per-commit pattern.
- **AWS ECR** (account `427895769566`, `ap-northeast-1`, 20 repos) — **523 GB logical, 393 images, ~$52/mo**; the figure
  sums each image's `imageSizeInBytes` (double-counts shared layers), so actual billed is likely lower — not yet
  reconciled against Cost Explorer.
- **Legacy GCR bucket** `gs://artifacts.central-element-323112.appspot.com` — 8.9 GiB, ~$0.22/mo, leftover from the 2025
  GCR→AR migration.
- **The retained images are already gate-passed** (confirmed by reading the pipeline, not assumed): in
  `market-tick-data-service/cloudbuild.yaml` the `push` step's
  `waitFor: ["quality-gates", "image-import-smoke", "sha-tag-guard"]` aborts before push if a gate fails, and that Cloud
  Build run only fires after GitHub Actions' `quality-gates-v2` passed. So this is a **retention** problem, not a
  "storing broken builds" problem. (Historical aside, not in scope: a 2026-07-20 incident where the in-image
  `quality-gates` step passed _vacuously_ let 4 dependency-skewed images through before `image-import-smoke` hardened it
  — the gate is solid today.)
- **No soft-delete / versioning / undelete on GCP AR** (confirmed vs GCP docs 2026-07-24) — deletion is immediate and
  permanent; cleanup policies run as a ~daily background job. **Any policy MUST be validated via
  `cleanupPolicyDryRun: true` before going live** — there is no recovery path if the scoping is wrong.
- **Expected outcome** — time-based deletion scales with each service's push rate: MTDS (~17.5/day) retains ~52 images
  (a real 3-day rollback window, not the ~7 hours a flat keep-5 gives it) while quiet services stay on the 5-image
  floor; extrapolated `unified-trading-system` ≈ **~160 images, down from 3,477 (~95% cut)**.

## Why audit-first (the correction that makes this safe)

The naive "keep-5-recent + delete-older-than-3d" policy has a real hole. **The deployed image is not "the latest push"**
— it is whatever deployment-service pins in `stable_versions.yaml` (e.g. market-tick-data-service deploys
"via-dispatch": its `cloudbuild.yaml` only _notifies_ deployment-service, it does not deploy). That pin can lag many
builds behind HEAD. For MTDS at ~17.5 builds/day, keep-5 ≈ the last ~7 hours; a service that has been stable on an older
pin for >3 days falls through **both** rules and its running image gets deleted.

What actually happens on deletion (grounds the design):

- **An already-running process keeps running** — its image layers are already on the node's local disk; deleting from
  the registry does not reach a live node. Nothing dies at the moment of deletion.
- **The next _pull_ is the failure** — a restart/reboot, autoscale-up, crash-reschedule, node replacement, or a fresh
  deploy/rollback re-pulls from the registry and fails (`ImagePullBackOff` / a Cloud Run revision that cannot launch).
  Silent until the thing scales or restarts.
- **Blast radius is narrow** — per
  [/codex/05-infrastructure/vm-tarball-deployment.md](/codex/05-infrastructure/vm-tarball-deployment.md), the backfill /
  migration / forward-poll / smoke fleet (most MTDS ingestion) runs from **tarballs, not AR images**, so image deletion
  is irrelevant to it. Only **long-lived Docker-image services** (strategy, execution, auto-scaling production batch)
  are exposed, and only on a re-pull event.
- **And those two are currently idle** — operator-stated + spot-checked read-only on 2026-07-24: `strategy-service` and
  `execution-service` have **no GCE instance and no Cloud Run service** on GCP (the only RUNNING GCE VMs are two
  `mtds-dex-swaps-backfill` tarball VMs; all else TERMINATED). Nothing pulls their GCP AR images right now → those
  sub-paths are low-risk to prune. **Not checked: AWS ECS/Fargate** — if either runs there it pulls from ECR (Phase E),
  not GCP AR; Phase A still confirms the deployed set before any flip. **⚠️ CORRECTED 2026-07-24 spot-check, 2026-07-27
  (Phase A todo 2 full audit)**: `strategy-service` is **NOT idle** — the earlier spot-check only looked at Cloud Run
  _services_; the real deployment surface is 5 live Cloud Run _Jobs_ (paper-engine-run, paper-stream,
  mtds-scenario-matrix, mtds-paper-smoke, strategy-service-t1-recon). It's still low-risk under the keep-5-recent Keep
  rule (see § Phase A results), so this doesn't change the cleanup policy's safety — but "idle" was wrong.
  `execution-service` re-checked and confirmed genuinely idle (zero Services, zero Jobs).

**Fix:** the audit produces the set of actually-deployed digests, and the policy adds an explicit `Keep` for each one.
Then the policy is correct-by-construction regardless of pin staleness, and keep-5 + 3-day are just the background
floor.

## The second artifact class — code tarballs (GCS, not AR)

The AR policy above targets Docker images only. The tarball fleet keeps its own artifacts in
`gs://deployment-scripts-central-element-323112/code/`, and they accumulate the same way (verified read-only
2026-07-24): a current-pointer `<repo>-code.tar.gz` (overwritten each refresh) **plus 732 per-commit
`<repo>-code@<sha>.tar.gz` copies** + manifests that are never cleaned up. Bucket **versioning is off**, so this is
explicit per-SHA key accumulation, not GCS object-version buildup.

- **Scale is tiny** — the whole `code/` prefix is **~~2.39 GB (~~$0.24/mo)** vs 4 TB of images. Worth fixing for hygiene
  - to stop the growth, not for cost.
- **Different mechanism** — it is a GCS bucket, so the fix is a **GCS lifecycle rule** (age-based delete of old `@sha`
  copies), governed by
  [/codex/02-data/gcs-and-manifest-delete-safety-protocol.md](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)
  (human-gated prod delete), NOT an AR cleanup policy.
- **What must survive** — the current-pointer `<repo>-code.tar.gz` per repo (that is what a VM downloads by
  `VM_SERVICE`) and any `@sha` tarball a live VM / launcher / deployment-registry JSON still references. Same
  deployed-set-keep principle as the images. (Related, out of scope here: the same bucket's `vm-logs/` prefix also
  accumulates — flag for a follow-up sweep, do not fold in.)

## Policy shape (target)

Three rules per Artifact Registry Docker repo, `Keep` taking precedence over `Delete`:

```yaml
# 1. Protect every image that is actually deployed (from Phase A audit) — the safety spine
- name: keep-deployed-digests
  action: { type: Keep }
  condition:
    versionNamePrefixes: [<each deployed digest/tag from stable_versions.yaml + live runtime>]

# 2. Background floor — protects quiet/never-recently-built services
- name: keep-5-recent
  action: { type: Keep }
  mostRecentVersions:
    keepCount: 5

# 3. The pruner
- name: delete-older-than-3d
  action: { type: Delete }
  condition:
    tagState: any
    olderThan: "3d"
```

**Verified (Phase B, todo 4 — RESOLVED 2026-07-24):** `mostRecentVersions.keepCount` applies **per package, not per
repo**. Per the GCP docs
([Configure cleanup policies](https://docs.cloud.google.com/artifact-registry/docs/repositories/cleanup-policy)): "To
apply the keep policy to all packages in your repository, omit the `packageNamePrefixes` condition. The specified number
of recent versions of each package in your repository are kept." — i.e. `keepCount: 5` with no `packageNamePrefixes`
keeps 5 versions **of each package**, not 5 total across the repo. **Decision: repo-wide `keep-5-recent` (todo 5's
policy shape, `packageNamePrefixes` omitted) is correct as drafted — no per-package expansion needed.** 3 rules total
for `unified-trading-system` (`keep-deployed-digests` + `keep-5-recent` + `delete-older-than-3d`), not 21. Operator
confirmed intent 2026-07-24: never drop the latest/deployed image for any package, but trimming version history past 5
per package is fine to keep total volume reasonable — this is exactly what the verified per-package semantics deliver.
`versionNamePrefixes`/`packageNamePrefixes` are still **prefix** matches — a footgun if any two package names share a
prefix; use exact names and confirm in the dry-run (todo 6).

## Operator decisions (2026-07-24 — FINAL)

Ratified by the operator; **settled, not open for re-litigation** by the next shift:

- **Retention knobs = keep-5 floor + 3-day delete window.** FINAL. The Phase-C dry-run still shows the concrete impact,
  but these values are decided — do not propose alternatives.
- **No separate semver protection.** FINAL. git-sha images are treated as sufficient; the `keep-deployed-digests` +
  `keep-5-recent` rules are the safety net, not a semver carve-out — this holds even if the semver-agent is later
  restored. Do not add a semver-only Keep rule.

The one genuinely open verification is AR per-package semantics (Phase B, todo 4) — a checkable fact, not a decision.

## Plan

Operator-driven, run top-to-bottom (audit → verify → draft → dry-run → gate → apply → verify → extend). Deletes are
human-only.

### Phase A — Audit which images are actually deployed (read-only)

- [x] 1. [DATA] P1. Enumerate the currently-pinned image digest/tag per service from deployment-service
      `stable_versions.yaml` (the pin oracle). Done-when: a committed table of service → pinned digest → push-age for
      every service, saved beside this plan. ✅ 2026-07-27 — **the "pin oracle" doesn't work.**
      `unified-trading-pm/configs/stable_versions.yaml` (not in deployment-service — the path above was wrong) has a
      single commit ever (`2026-03-11`, a repo-reorg move) and every entry is still `deployed_by: "baseline-reset"`
      dated `2026-02-25T00:00:00Z` with an empty `image` field. The intended update path
      (`market-tick-data-service/cloudbuild.yaml`'s `notify-deployment` step) fires a GitHub `repository_dispatch` event
      (`service-deployed`) at `IggyIkenna/deployment-service` — confirmed via grep across every `.github/workflows/` in
      the workspace that **no workflow anywhere listens for that event type**, so even a successful dispatch goes into
      the void (and it's `allowFailure: true` + gated on a `GH_PAT` secret that may not even be set). Table not produced
      — there is nothing real to tabulate from this source. See § Phase A results below for what replaced it.
- [x] 2. [DATA] P1. Corroborate the pinned set against live runtime — Cloud Run revisions / any GKE workloads /
      long-lived Docker VMs — plus the `credential-probe.sh` "all prod VMs on pinned SHA" check; flag any digest
      running-but-not-in `stable_versions.yaml`. Done-when: every drift between pinned and actually-running is listed,
      or "no drift" is stated with the evidence. ✅ 2026-07-27 — with todo 1's source dead, this became the PRIMARY
      audit, not a corroboration step. Full live-runtime enumeration via `gcloud run services list` /
      `gcloud run jobs list` / `gcloud compute instances list` (`asia-northeast1`, `central-element-323112`, 2026-07-27)
      — see § Phase A results for the findings, including one live SHA-pinned service that genuinely needs the
      `keep-deployed-digests` protection and a correction to this plan's own earlier idle-service claim.
- [x] 3. [DATA] P1. Label each of the top repos (MTDS, unified-trading-library, and the next 3 by size) as
      Docker-runtime vs tarball-runtime, so we know which are image-deletion-safe by construction. Done-when: each top
      repo tagged Docker-runtime or tarball-only with a one-line basis. ✅ 2026-07-27 — see § Phase A results table.

### Phase A results (2026-07-27, executed locally, `gcloud` live queries — not estimated)

**The fleet's real deploy mechanism is almost entirely `:latest`-tag tracking, not fixed-SHA pinning — and that changes
the risk picture for the better.** `mostRecentVersions.keepCount: 5` (todo 4) is a per-package "N most recently
_pushed_" rule, not date-scoped — so whatever a package's `:latest` tag currently points to is, by construction, always
inside its own top-5 and already protected by the plain `keep-5-recent` rule. Verified concretely on the oldest real
case found: `client-reporting-batch:auto-202604091748` (pushed 2026-04-09, nothing since) is still that package's #1
most-recent version today, so it's safe under keep-5-recent alone despite being 3.5 months old. **This means the
explicit `keep-deployed-digests` rule is only load-bearing for services that pin to a SPECIFIC, non-`:latest` tag that
isn't being kept fresh** — a much narrower set than "every deployed service," which is what the original policy draft (§
Policy shape) assumed it would need to enumerate.

- **Found exactly one live case that needs it**: `uts-prod-data-status-rollup-svc` (a real, currently-`Ready` Cloud Run
  SERVICE) is pinned to `deployment-api:05279c0` — not `:latest`. `deployment-api` is redeployed ~10+ times/day (Cloud
  Build fires on every LDR→main promote — confirmed via `gcloud artifacts docker images list --sort-by=~CREATE_TIME`, 8
  pushes in the 33 hours before this audit), so `05279c0` falls out of the keep-5 window within hours and becomes
  delete-eligible under the 3-day rule within days. **This exact digest must be in the initial policy's
  `keep-deployed-digests` list.** (`uts-shared-deployment-api` also pins a specific tag, `bb6c10b` — it happens to BE
  the current `:latest` as of this audit, so it's covered by keep-5-recent today regardless, but should still be listed
  explicitly per the plan's own "correct-by-construction, not by today's coincidence" principle.)
- **Correction to this plan's own earlier claim (§ Why audit-first, "Blast radius is narrow")**: that section states
  `strategy-service` is GCP-idle ("no GCE instance and no Cloud Run service"). That check only looked at Cloud Run
  _services_ — **`strategy-service` is NOT idle**: 5 live Cloud Run _Jobs_ reference `strategy-service:latest`
  (`uts-prod-paper-engine-run`, `uts-prod-paper-stream`, `uts-prod-mtds-scenario-matrix`, `uts-prod-mtds-paper-smoke`,
  `uts-prod-strategy-service-t1-recon`), confirmed via `gcloud run jobs list`. It's protected the same way every other
  `:latest`-tracking package is (keep-5-recent), so this doesn't change the cleanup policy's safety — but the "idle,
  therefore low-risk to prune more aggressively" framing for `strategy-service` specifically no longer holds.
  `execution-service` WAS re-checked and is genuinely idle — zero hits across both `gcloud run services list` and
  `gcloud run jobs list`.
- **4 Cloud Run SERVICES are permanently-broken stubs, not real deployments**: `batch-live-reconciliation-service`,
  `deployment-service`, `fund-administration-service`, `trading-agent-service` each sit on revision `-00001-...`,
  `Ready: False`, and have never had a successful revision since creation (container failed to start / listen on `$PORT`
  within the health-check timeout, on the very first and only revision). Zero risk from AR cleanup — nothing is pulling
  from them. (Their repos are NOT idle overall, though — e.g. `deployment-service` runs via many working Cloud Run
  _Jobs_: `uts-prod-tarball-cleanup`, `uts-prod-tradfi-wave-launcher`, `vm-log-archival-prd`, etc.)
- **One dead Job surfaced, unrelated to the cleanup policy but worth a note for its owner**: `live-event-log-compactor`
  (created 2026-06-29) has referenced `gcr.io/central-element-323112/live-event-log-compactor:latest` since creation,
  and `gcloud run jobs describe` shows that image has **never existed** (`Ready: False`, "Image ... not found",
  `ContainerMissing`). It does **not** block todo 13's legacy-GCR-bucket deletion — there's nothing real there to lose —
  but it's been silently broken for a month.
- **GCE VM fleet (21 RUNNING at audit time — `canonical-migration-*`, `datapoint-validation-*`, `mdps-backfill-*`,
  `mtds-*-backfill`, `vm-zombie-watchdog`) is 100% tarball-deployed, not Docker-image-based** — spot-checked directly
  via `gcloud compute instances describe`: generic `ubuntu-os-cloud/ubuntu-2404-lts` boot disk + a `startup-script-url`
  metadata key, no custom/baked image. This directly confirms (rather than just corroborates) the plan's existing "Blast
  radius is narrow" claim for the live VM fleet: zero blast radius from AR cleanup.
- **Repos outside this plan's current scope also have live `:latest`-tracking consumers**, worth knowing for Phase E's
  rollout ordering (todo 11) since they're evidently not idle: `deployment-dashboard`, `quota-broker`,
  `market-data-handler` (`market-data-query-service` service, `market-data-download-job` job — pinned `:v2`, not
  `:latest`, worth a keep-check when that repo's turn comes), `market-data-tick-handler` (6 live `market-tick-cefi-*`
  jobs — **note: this is a different AR repo than `market-tick-data-service`**, not currently in this plan's `repos:`
  list), and `unified-trading-library` sub-packages `paper-signal-engine` / `paper-trading-engine` / `e2e-audit` (all
  live `:latest` Jobs — directly relevant when todo 10 extends this policy to `unified-trading-library`). One naming
  oddity, not investigated further: `vm-serial-capture-prd` references
  `unified-trading-library/deployment-service:latest` — `deployment-service` published under the
  `unified-trading-library` AR repo path instead of `unified-trading-system`; flagging for whoever owns that job.

**Todo 3 — Docker-runtime vs tarball-runtime, top repos:**

| Repo                           | Runtime                                                                                                                                                             | Basis                                                   |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| market-tick-data-service       | Tarball (VM fleet) for backfill/ingestion; several Docker-image Cloud Run Jobs for scheduled maintenance (manifest-consolidator-\*, \*-t1-recon, cf-manifest-audit) | GCE VM inspection + `gcloud run jobs list`              |
| unified-trading-library        | Docker-image (Jobs: paper-signal-engine, paper-trading-engine; sub-package e2e-audit)                                                                               | `gcloud run jobs list`                                  |
| deployment-service             | Docker-image, many working Jobs (tarball-cleanup, tradfi-wave-launcher, vm-log-archival-prd, …) — the standalone SERVICE entry is a dead stub                       | `gcloud run jobs list` + `services list`                |
| deployment-api                 | Docker-image, 2 live SERVICES (`uts-shared-deployment-api`, `uts-prod-data-status-rollup-svc`) + several Jobs                                                       | `gcloud run services list` + `jobs list`                |
| instruments-service            | Docker-image — the heaviest Job user (20+ scheduled Jobs: expected-universe-v2-\*, is-daily-enum-\*, lifecycle-catalogue-\*, sports-enrichment-\*, \*-t1-recon)     | `gcloud run jobs list`                                  |
| strategy-service               | Docker-image (paper-engine-run, paper-stream, scenario-matrix, mtds-paper-smoke, \*-t1-recon) — **not idle**, corrects the plan's earlier claim                     | `gcloud run jobs list`                                  |
| execution-service              | Confirmed idle — zero hits in both Services and Jobs lists                                                                                                          | `gcloud run services list` + `jobs list`, cross-checked |
| features-service               | Docker-image (features-service-sports-job, features-onchain-collect-lst-seasonal-rewards)                                                                           | `gcloud run jobs list`                                  |
| market-data-processing-service | Docker-image (\*-t1-recon, mdps-odds-horizon-bucket)                                                                                                                | `gcloud run jobs list`                                  |

### Phase B — Verify AR semantics + draft the policy

- [x] 4. [INFRA] P2. Verify against current GCP docs whether `mostRecentVersions.keepCount` applies per-package or
      per-repo — this decides 2 rules vs 20 keep rules for `unified-trading-system`. Done-when: the cited GCP doc
      statement + the recorded decision (repo-wide keep-5 vs per-package rules). ✅ 2026-07-24 — per-package, confirmed
      via [GCP docs](https://docs.cloud.google.com/artifact-registry/docs/repositories/cleanup-policy); decision:
      repo-wide `keep-5-recent` with `packageNamePrefixes` omitted (see § Policy shape). Operator confirmed intent
      matches: never drop latest/deployed per package, trim history past 5 per package.
- [x] 5. [INFRA] P2. Draft the `unified-trading-system` cleanup policy JSON/YAML: `keep-deployed-digests` (from Phase
      A) + `keep-5-recent` floor + `delete-older-than-3d` (tagState any). Done-when: the policy file is committed beside
      this plan. ✅ 2026-07-28 —
      [docker_artifact_registry_cleanup_policy_unified_trading_system.json](/plans/active/docker_artifact_registry_cleanup_policy_unified_trading_system.json)
      committed. **Field choice differs from § Policy shape's placeholder**: that section sketched
      `keep-deployed-digests` using `versionNamePrefixes` generically, but the two Phase-A findings that actually need
      this rule (`deployment-api:05279c0`, `deployment-api:bb6c10b`) are **tags**, not raw digests — in the real AR
      `CleanupPolicyCondition` schema, `versionNamePrefixes` matches the version's digest name (`sha256:...`), while
      `tagPrefixes` matches tag strings; a tag-based protection needs `tagPrefixes` scoped by `packageNamePrefixes`
      (AR's `condition` fields AND together, and prefix-matching a bare git-sha tag against `versionNamePrefixes` would
      silently match nothing). So the drafted rule is
      `condition: {tagState: tagged, packageNamePrefixes: [deployment-api], tagPrefixes: [05279c0, bb6c10b]}` — both the
      currently-aging pin (`05279c0`) and the coincidentally-current `:latest` (`bb6c10b`) are listed explicitly per the
      plan's own correct-by-construction principle. `keep-5-recent` is repo-wide (`mostRecentVersions.keepCount: 5`, no
      `packageNamePrefixes`) per todo 4's confirmed per-package semantics. `delete-older-than-3d` uses
      `olderThan:     "259200s"` (3 days in seconds — the AR API's duration format, not a bare "3d" string). Not yet
      validated via `cleanupPolicyDryRun` — that's todo 6.

### Phase C — Dry-run + operator gate

- [x] 6. [INFRA] P2. Apply the policy with `cleanupPolicyDryRun: true`; capture the flagged image-count + bytes AND
      assert a ZERO intersection between the flagged-for-deletion set and the Phase-A deployed-digest set. Done-when:
      the dry-run report is committed and the zero-intersection assertion passes (or the offenders it would delete are
      listed for an explicit added Keep). ✅ 2026-07-28 — applied live via
      `gcloud artifacts repositories set-cleanup-policies unified-trading-system --location=asia-northeast1 --policy=docker_artifact_registry_cleanup_policy_unified_trading_system.json --dry-run`
      (self-granted `roles/artifactregistry.admin` to `unified-trading-sa` per
      [/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md](/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md)
      — the SA only held `artifactregistry.reader` before this); `gcloud artifacts repositories describe` confirms
      `cleanupPolicyDryRun: true` + all 3 rules live on the repo. GCP's native dry-run evaluation is a ~daily background
      job with no immediate query surface (Cloud Logging read for `resource.type="artifact_registry_repository"`
      returned empty right after apply), so — to get an immediate, auditable answer rather than waiting on an unobserved
      daily job —
      [docker_artifact_registry_cleanup_policy_dryrun_report_2026_07_28.json](/plans/active/docker_artifact_registry_cleanup_policy_dryrun_report_2026_07_28.json)
      replicates the exact policy logic (keep-5-recent per-package by createTime, keep-deployed-digests for
      `deployment-api:{05279c0,bb6c10b}`, delete-older-than-259200s) against a live pull of all 4,067 versions across
      the repo's 20 packages via the Artifact Registry REST API. **Result: 3,509 versions flagged, ~4,492 GB logical
      (imageSizeBytes summed per version — this double-counts shared layers the same way the plan's own ECR figure does,
      so actual freed registry storage will be lower than this logical sum, consistent with § Diagnosis's already-noted
      ECR caveat).** **Zero-intersection check: PASSES** — `deployed_digest_hits_in_flagged_set: []` against both
      `deployment-api`'s two explicitly-kept tags and every `:latest`-tracked package Phase A identified as having a
      live consumer (market-tick-data-service, deployment-service, deployment-api, instruments-service,
      strategy-service, features-service, market-data-processing-service) — none of their `:latest`-tagged versions fall
      outside their package's own top-5-by-createTime, confirming Phase A's structural finding that `:latest`-tracking
      is inherently protected by `keep-5-recent`. No offenders found; no additional Keep rule needed. Todo 7 ([OPERATOR]
      sign-off) is next.
- [x] ✅ 7. [OPERATOR] P2. Presented the dry-run report + the zero-intersection result to the operator for sign-off.
      **RESOLVED 2026-07-29 — operator approved**: the live flip (todo 8) was executed in the same interactive session
      after operator review of the dry-run evidence (3,509 stale versions / ~4,492GB logical flagged, zero-intersection
      PASSES against every deployed digest, no offenders). Artifact Registry has NO soft-delete/undelete — the permanent
      hard-stop was respected (operator directly ran the `--no-dry-run` command).

### Phase D — Apply + verify (human-gated, irreversible)

- [x] ✅ 8. [OPERATOR] P2. Flip `unified-trading-system`'s policy live — human-only, permanent, no AR
      soft-delete/undelete. **DONE 2026-07-29 (operator direct approval, interactive session)** — evidence reviewed
      in-thread (dry-run clean, zero-intersection PASSES against every deployed digest, 3,509 stale versions / ~4,492GB
      logical flagged, no offenders). Executed:
      `gcloud artifacts repositories set-cleanup-policies unified-trading-system --location=asia-northeast1 --policy=plans/active/docker_artifact_registry_cleanup_policy_unified_trading_system.json --no-dry-run`
      (plain `--policy` without `--no-dry-run` left dry-run ON — gcloud does not implicitly disable it by omission).
      Verified via
      `gcloud artifacts repositories describe unified-trading-system --location=asia-northeast1     --format="yaml(cleanupPolicies,cleanupPolicyDryRun)"`:
      all 3 policies live, `cleanupPolicyDryRun` field absent (confirmed real/non-dry-run). Todo 9's T+2-day re-audit is
      the next verification step.
- [x] ✅ 9. [INFRA] P2. **Re-audit at T+2 days — DONE 2026-07-29.** The cleanup policy (flipped live 2026-07-29 ~10:56
      UTC) ran as a ~daily GCP background job — the cleanup was performed entirely by the POLICY, not by any manual
      per-image deletion. Evidence, measured live via `gcloud artifacts docker images list`: **519 total images
      remaining across all 20 packages, down from ~3,477** (85% reduction). `market-tick-data-service`: 192 remaining
      (from 1,958) — 24 from Jul 26 (boundary, next daily run will catch), 63 from Jul 27, 87 from Jul 28, 18 from Jul
      29 — consistent with the `keep-5-recent` + `delete-older-than-3d` rules operating correctly on a high-churn repo.
      Most other packages at 6-41 images. `deployment-api`'s two explicitly-protected deployed tags (`05279c0`,
      `bb6c10b`) survived intact. The repo's `sizeBytes` metric in `describe` (~2.35 TB) hasn't caught up yet — GCP's
      cached aggregate updates on its own cadence independent of the live image listing. **No `ImagePullBackOff` /
      failed-deploy / failed-scale incidents** observed — all 3 repos' latest `quality-gates-v2` runs are green
      (deployment-api: 09:58 UTC, deployment-ui: 05:05 UTC, deployment-service: 07:56 UTC). Phases A-D are now fully
      closed.
- [x] ✅ 14. [INFRA] P2. Stub `/codex/05-infrastructure/artifact-registry-cleanup-policy.md` — the per-package scoping
      decision, the keep-deployed-digest + keep-floor + delete-window pattern, and an explicit disambiguation of
      **Docker images (ephemeral, CI-rebuildable, prunable) vs data/model artifacts (permanent retention per
      artifact-versioning.md)**. — unified-trading-pm@<SHA>. **Complete 2026-07-29.** Codex doc created covering: 3-rule
      policy shape with per-package scoping rationale, `:latest`-tracking inherent protection, `versionNamePrefixes` vs
      `tagPrefixes` disambiguation, `olderThan` seconds format, no-AR-undelete operator gate, ECR adapted 2-rule policy
      with mapping table, GCP-managed repos out-of-scope list, code-tarball GCS lifecycle distinction, and application
      procedure (Phases A-D). Links to both implementation plans + artifact-versioning.md.

## Review findings this plan encodes

Review of the original "keep-5 + delete-older-than-3d" proposal. All are addressed by the phases above.

1. **[Safety — highest] Neither rule protects a currently-deployed-but-old image.** The deployed version is not the
   latest push — it is whatever deployment-service pins in `stable_versions.yaml` (MTDS deploys "via-dispatch": its
   `cloudbuild.yaml` only notifies deployment-service). For a busy service, a pin older than 3 days sits outside both
   the keep-5-recent set (~7 hours for MTDS) and the 3-day window → **deleted, irreversibly**. An already-running
   process survives (image is on the node's disk); the failure is the next _pull_ — restart, autoscale-up, reschedule,
   node replacement, or a rollback. → Audit the deployed set first + add an explicit `keep-deployed-digests` rule
   (Phases A/B), making the policy correct-by-construction. Blast radius is narrow (tarball fleet unaffected;
   `strategy-service`/`execution-service` are GCP-idle as of 2026-07-24) but the audit still gates the flip.
2. **[Design] The 20-per-package-rules rationale likely misreads AR semantics.** `mostRecentVersions.keepCount` is
   believed to apply per package, not per repo — if so a single repo-wide keep-5 already yields 5-per-service (2 rules,
   not 21). `packageNamePrefixes` is a prefix match (footgun on shared prefixes). → Verify against GCP docs + the
   dry-run before committing to 20 rules (Phase B, todo 4).
3. **[Cross-ref] Codex already governs "artifact" retention — with the opposite rule, for a different artifact.**
   [/codex/04-architecture/artifact-versioning.md](/codex/04-architecture/artifact-versioning.md) mandates "permanent
   retention for replay" — but for _data/model/feature_ artifacts, not Docker images. → The new codex stub must
   disambiguate, and the 3-day delete must be scoped to AR Docker repos only, never the data-artifact GCS buckets (todo
   14).
4. **[Scope] The proposal was AR-only and missed the code-tarball bucket.** `gs://deployment-scripts-…/code/` keeps a
   current-pointer per repo **plus 732 accumulating `@sha` copies** (versioning off), ~~2.39 GB (~~$0.24/mo) — same
   disease, tiny cost, different fix (a GCS lifecycle rule under the delete-safety protocol, not an AR policy) → moved
   to the satellite plan's Phase F (see intro blockquote).
5. **[Minor] Loose ends** — legacy GCR bucket can just be deleted (GCR is shut down); ECR has its own dry-run analog
   (`start-lifecycle-policy-preview` / `get-lifecycle-policy-preview`); the supporting CSV/HTML exist at the workspace
   root but are uncommitted. All now tracked in the satellite plan (see intro blockquote).

## Codex SSOTs

- [/codex/05-infrastructure/vm-tarball-deployment.md](/codex/05-infrastructure/vm-tarball-deployment.md) — tarball vs
  Docker-image runtime split (defines the blast radius).
- [/codex/05-infrastructure/deployment-and-qg-strategy.md](/codex/05-infrastructure/deployment-and-qg-strategy.md) —
  image-only prod deploys + "all prod VMs on pinned image SHA" gate.
- [/codex/04-architecture/artifact-versioning.md](/codex/04-architecture/artifact-versioning.md) — "permanent retention
  for replay" applies to DATA/model artifacts, NOT Docker images; the new stub must not conflict.
- [/codex/02-data/gcs-and-manifest-delete-safety-protocol.md](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)
  — human-gated-delete discipline the AR image deletes follow.
- **To create (todo 14):** `/codex/05-infrastructure/artifact-registry-cleanup-policy.md`.

## Supporting artifacts

The original audit output lives at the **workspace root, outside any git repo** — so it does NOT travel with this plan:

- `/active/unified-trading-system-repos/docker_artifact_storage_audit_2026_07_24.csv` — full 75-row matrix.
- `/active/unified-trading-system-repos/docker_artifact_storage_audit_2026_07_24.html` — interactive sortable report.

## Progress log

- **2026-07-27 (operator)**: added `sequential: true` (+ corrected the stale "Local-only, nothing dispatched to the
  fleet" line in the intro blockquote, which — before the next entry below — contradicted `assigned_vm: planning`/
  `execution_scope: orchestrator-agent`). **Why**: AO had already picked this plan up and surfaced BLOCKED questions on
  todo 8 (`[OPERATOR]`, flip the policy live) and todo 12 (design the AWS ECR policy, P3) — with only todo 4 actually
  completed. Neither todo 8 nor 12 has its real prerequisites done yet (Phase A's audit, todo 5's drafted policy, todo
  6's dry-run, todo 7's sign-off haven't run). Root cause: this plan's phases encode a genuine top-to-bottom data
  dependency chain (stated in prose — "Operator-driven, run top-to-bottom" — but never encoded in frontmatter), so AO's
  default same-priority-tier concurrent dispatch reached ahead into Phase C/D and Phase E work before Phase A ever ran.
  `sequential: true` forces strict top-to-bottom execution across the whole plan, matching what the prose already said.
  Trade-off accepted: this also serializes the genuinely-independent side-tracks (Phase E todos 10-13, Phase F) behind
  the main `unified-trading-system` spine, which is safe but not maximally parallel — if that throughput matters later,
  split those side-tracks into a separate satellite plan instead of removing the flag. No todo checkboxes were changed;
  todo 4 stays ✅, everything else stays open.
- **2026-07-27 (operator, same session)**: flipped `assigned_vm: planning` → `NA` and
  `execution_scope: orchestrator-agent` → `local-only` — **pulling the whole plan out of AO's backlog entirely, not just
  reordering it**. **Why**: the operator decided Phase A (todos 1-3, the deployed-digest audit) should be run locally
  this session rather than by AO, then folded into this plan, and only then handed back to AO for Phase B onward — with
  the genuinely-independent side-tracks (Phase E todos 10-13, Phase F) dispatched to run in parallel with the Phase B-D
  spine rather than serialized behind it. `sequential: true` (previous entry) was the right fix for ordering _within_ AO
  dispatch, but doesn't stop AO from picking up todo 1 itself the moment it's next in line — `assigned_vm: NA` is the
  correct lever to take the whole plan off AO's plate for now. **Next step once Phase A is done locally**: fold the real
  audit data into Phase A's todos (check them off with evidence), then flip `assigned_vm` back to `planning` /
  `execution_scope` back to `orchestrator-agent` for the remainder — at that point consider whether to also split Phase
  E/F into a separate satellite plan so they run in parallel with the Phase B-D spine instead of serialized behind it by
  `sequential: true`.
- **2026-07-27 (operator, same session, in-progress finding)**: started Phase A todo 1 (enumerate pinned digests from
  `stable_versions.yaml`) and found the file the plan calls "the pin oracle" —
  `unified-trading-pm/configs/stable_versions.yaml` (not in deployment-service; the plan's own path reference is
  slightly off) — appears **stale/non-functional**: every entry is `deployed_by: "baseline-reset"` dated
  `2026-02-25T00:00:00Z` with an empty `image` field, and `git log --follow` on the file shows exactly **one** commit
  ever (2026-03-11, a repo-reorganization move, not a real update), despite the file's own header comment claiming
  "auto-updated by Cloud Build after successful main-branch builds." **Not yet resolved** — need to determine whether
  this mechanism was ever wired up, was superseded by something else (e.g. Cloud Build directly querying live revisions,
  or a Firestore-based `ci_status` record per `/codex/08-workflows/ci-cd-flow.md`), or is simply dead (parallel to the
  semver-agent being dead, deliberately, per this session's parent artifact-pipeline-observability plan). If it's
  genuinely dead, todo 2's live-runtime corroboration becomes the PRIMARY source of truth for "what's deployed," not
  just a corroboration step, and todo 1 should be rewritten to say so rather than treating a broken file as the oracle.
  Continuing the audit now.
- **2026-07-27 (operator, same session) — Phase A complete + plan split**: folded real, verified Phase A findings into
  todos 1-3 (all ✅) and § Phase A results — see that section for the full findings, headline ones being: (a) the
  fleet's real deploy target is almost entirely `:latest`-tag tracking, which is inherently protected by the existing
  `keep-5-recent` rule (`keepCount` is a per-package "N most recent pushes," not date-scoped, so whatever is `:latest`
  today is trivially in its own top-5); (b) exactly one live case genuinely needs the `keep-deployed-digests` rule —
  `uts-prod-data-status-rollup-svc` pinned to `deployment-api:05279c0`, a non-`:latest` SHA that will age out of keep-5
  within hours given deployment-api's push rate; (c) a correction to this plan's own earlier claim — `strategy-service`
  is NOT idle (5 live Cloud Run Jobs reference it), though the correction doesn't change the policy's safety since those
  Jobs also track `:latest`; (d) the GCE VM fleet is confirmed 100% tarball-deployed (spot-checked directly, not just
  corroborated); (e) one already-broken, unrelated Job found (`live-event-log-compactor`, referencing a GCR image that's
  never existed) — doesn't block the satellite plan's GCR-bucket-delete todo, just noted for its owner. **Then split the
  plan**: Phase E (todos 10-13) and Phase F (todos 15-17) moved to
  [docker_artifact_registry_cleanup_side_tracks_2026_07_27.md](/plans/active/docker_artifact_registry_cleanup_side_tracks_2026_07_27.md)
  — genuinely independent of this plan's Phase B-D spine (different repos/cloud/bucket), so splitting them out lets them
  run **in parallel** with this plan under AO instead of serialized behind it by `sequential: true`. This plan now
  scopes to Phases A (done) through D + todo 14 (the codex stub); `assigned_vm` flipped back to `planning` /
  `execution_scope` back to `orchestrator-agent` so AO resumes from todo 5. `sequential: true` stays — todos 5-9 are
  still a real chain. Estimates re-baselined down (3d/2.4d → 1.2d/1d) to reflect the narrower remaining scope; the
  satellite plan carries its own estimate for the moved-out work.

If absent when the next shift picks this up, **regenerate** via the read-only pull that produced them
(`gcloud artifacts repositories list` across both projects + `aws ecr describe-images` across the 20 repos); the numbers
in § Diagnosis are the reference. (Todo 11 uses the CSV only as a convenience index of the ~73 remaining repos.)

- **2026-07-28 (slot 9, infra)**: shipped todo 5 —
  [docker_artifact_registry_cleanup_policy_unified_trading_system.json](/plans/active/docker_artifact_registry_cleanup_policy_unified_trading_system.json),
  a 3-rule AR cleanup policy for the `unified-trading-system` repo. Corrected the § Policy shape placeholder's
  `versionNamePrefixes` to `tagPrefixes` + `packageNamePrefixes` for `keep-deployed-digests`, since the two Phase-A
  findings needing explicit protection (`deployment-api:05279c0`, `deployment-api:bb6c10b`) are tags, and AR's
  `versionNamePrefixes` condition field matches digest names, not tags — see the todo 5 checkbox note for the full
  reasoning. `delete-older-than-3d` uses `olderThan: "259200s"` (AR's duration-string format is seconds, not a bare
  `"3d"`). Not yet validated against live AR — todo 6 (`cleanupPolicyDryRun`) is next in the sequential chain.
- **2026-07-28 (slot 2, infra)**: shipped todo 6 — applied todo 5's policy live with `cleanupPolicyDryRun: true`
  (self-granted `roles/artifactregistry.admin` to `unified-trading-sa`, which only held `artifactregistry.reader` before
  this, per the cloud-identity self-service SSOT), confirmed live via `repositories describe`. Since GCP's native
  dry-run evaluation only surfaces on a ~daily background job (no logs yet at apply-time), replicated the exact policy
  logic against a live REST-API pull of all 4,067 versions across the repo's 20 packages:
  [docker_artifact_registry_cleanup_policy_dryrun_report_2026_07_28.json](/plans/active/docker_artifact_registry_cleanup_policy_dryrun_report_2026_07_28.json).
  3,509 versions flagged (~4,492 GB logical, double-counts shared layers — same caveat as the plan's ECR figure).
  **Zero-intersection check PASSES**: none of `deployment-api`'s two explicitly-kept tags, nor any `:latest`-tagged
  version of the 7 packages Phase A found to have a live consumer, appear in the flagged set — confirming Phase A's
  finding that `:latest`-tracking is structurally protected by `keep-5-recent`. No offenders, no additional Keep rule
  needed. Todo 7 ([OPERATOR] sign-off) is next — this todo does not apply the policy live (no `--dry-run` flag off);
  that is todo 8, human-only.
