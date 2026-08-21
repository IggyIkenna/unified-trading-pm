---
doc_type: plan
title: Artifact pipeline observability — Shipped History part 3 (forked from the artifact pipeline observability plan)
summary:
  Archive-bound Progress Log history extracted verbatim from artifact_pipeline_observability_2026_07_17.md's
  2026-08-21 line-cap remediation (na-eligibility-audit push hit the 1000L hard cap at 1012L/50 todos). Covers the
  2026-07-24 production-vs-local parity investigation (3 root causes found, IAM grant / logging silence / stdout
  buffering, plus the tarball-lane structural gap and the GCS Data Access audit-log cost side-finding), the same-day
  operator review of open decisions, and the 2026-07-27 session where Phase 3b/3c/3d all shipped (deployment
  registry commit stamp, Deployments cross-links, the tarball-bucket provider, and the live-launch verification's
  3 attempts). Every item in this file is already pure narrative describing already-shipped work — zero open todos.
  Record-only; not intended for further action.
status: complete
nature: record
asset_group: [ui]
stage: [meta]
repos: [deployment-ui, deployment-api, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [deployment-observability, artifact-pipeline, image-builds, tarballs, cloud-build, history, plan-split, archive-bound]
related:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/archive/artifact_pipeline_observability_history_2026_07_24.md,
    /plans/archive/artifact_pipeline_observability_history_2026_07_27.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
supersedes:
superseded_by:
depends_on:
source: >-
  Extracted by na-eligibility-audit (ui tranche, 2026-08-21) — the live doc's RECLASSIFY-per-todo-split edit pushed
  it to 1012L, over the 1000L hard `check_line_caps.sh` gate; per `task_template.md` §3 finding J, extracting the
  oldest fully-closed dated Progress Log section is the correct incremental fix (this is the THIRD such extraction
  for this doc, following the 2026-07-24 and 2026-07-27 ones).
locked_by:
locked_since:
context_scope: [/plans/active/artifact_pipeline_observability_2026_07_17.md]
---

# Artifact pipeline observability — Shipped History part 3

> Verbatim extraction of `artifact_pipeline_observability_2026_07_17.md`'s "## Progress log" section, the two dated
> entries spanning 2026-07-24 through 2026-07-27 (the production-vs-local parity investigation through the Phase
> 3b/3c/3d shipping session). All shipped/narrative, zero open todos. The live plan's own "## Progress log" section
> now carries a one-line pointer here instead.

- **2026-07-24 — production-vs-local parity investigation: 2 root causes found + fixed, 1 remains open; tarball-lane gap
  confirmed structural (not today's bug); a real Cloud Logging cost finding surfaced as a side investigation.** Operator
  reported the Artifacts tab showed real data locally the day before but nothing on the deployed page.
  - **Root cause #1 (IAM) + #2 (logging silence) + #3 (stdout buffering)** — see Phase 7 above for the full todo-level
    detail; summarized here for the timeline: `unified-trading-sa` lacked `artifactregistry.reader`
    (`deployment-service@74306a1`, terraform-applied directly against prod state, verified via impersonated-credentials
    reproduction); `deployment-api/main.py` never configured logging at all, so the resulting `providers.safe()` warning
    was firing into the void (`deployment-api@f27a8f1`, `logging.basicConfig()`); and `PYTHONUNBUFFERED` was never set,
    compounding with this service's independently-discovered crash-looping (`Uncaught signal: 6` recurring, one real OOM
    at 05:35 UTC) to lose whatever log output hadn't flushed (`deployment-api@6518e82`, `ENV PYTHONUNBUFFERED=1`). Both
    deployment-api fixes promoted LDR→main via the fleet `*/5` auto-promote cron (NOT the "staging-first" path
    quickmerge's own messaging still claims — that messaging is stale: staging was retired since June end and its
    workflows were only actually stopped recently, per operator 2026-07-24; this repo is actually on the direct
    `ldr_main` model like every other repo) → Cloud Build (`_DEPLOY=true`) → fresh Cloud Run revisions (`00267-c2k` then
    `00268-d2l`). **RESOLVED — no action needed (operator 2026-07-24)**: "keep it in quickmerge if it's not creating any
    issues" — the stale console message is cosmetic only (the actual promotion path is unaffected), so it's
    intentionally left as-is unless it starts causing real confusion or problems later.
  - **Root cause #3's investigation is still open** — even with all three fixes verifiably baked into the live image
    (confirmed by pulling the exact deployed digest and inspecting it directly, not by trusting the build log), the prod
    endpoint stayed silent AND empty on a brand-new revision. Reproduced the EXACT deployed image locally via
    `docker run` — it logs perfectly there, ruling out the image/code as the remaining cause. Leading hypothesis
    (untested): Cloud Run's default CPU-throttling (no `cpu-throttling` override on this service) starving background
    log-flush work between requests. Operator paused this thread to focus on the local dev environment instead —
    resume-point recorded in Phase 7.
  - **Tarball lane confirmed empty for a structural, pre-existing reason, unrelated to today's bugs** — operator
    independently noticed the local instance also shows nothing in the Tarball lane. Traced to `service.py`/
    `providers.py`: `LANE_TARBALL` exists in the data model and the UI already has lane filter chips for it, but no
    provider was ever written to read the GCS tarball-manifest bucket — confirmed via direct code read, reproduced live
    locally (`/api/artifacts/builds` returns `lanes={'image'}` only, 33/33 rows). New Phase 3d above captures the
    concrete todos to close this.
  - **Local dev environment stood up from scratch in this clone** (`.tabs/2` had no `.env.local` at all — the summarized
    prior session's local setup didn't carry over into this clone). Started `deployment-api` (`:8004`,
    `DISABLE_AUTH=true` — the sanctioned local-dev auth bypass in `deployment_api/auth.py`, not a workaround) +
    `deployment-ui` (`:5183`, a fresh `.env.local` pointed at `localhost:8004` instead of the prod URL the repo's
    `.env.local.example` template does NOT default to). Confirmed working end-to-end with real data: 20 repos,
    `market-tick-data-service` at 1961 images / 2.87 TB (a fresh, slightly-higher measurement than this plan's existing
    "~1.5 TB" line — worth reconciling if that figure gets cited again).
  - **A genuine, currently-unfiled cost finding surfaced as a side investigation** (operator asked about Cloud Logging
    cost for an unrelated reason — checking whether the logging fix would be expensive). This project's Cloud Logging
    ingestion is dominated by GCS Data Access audit logs on the MTDS prod buckets, driven by the canonical-migration VM
    campaigns' bulk per-object operations — MEASURED 151 GB / 7 days, real recurring cost, not a defect in the migration
    itself. Filed as its own issue doc same day, see below.
- **2026-07-24 (later) — operator review of the open-decisions list; 6 items resolved/clarified, 1 issue doc filed, 1
  new todo split out.** Walked the operator through every open decision and unclear item from the earlier audit; folded
  each answer into the plan rather than leaving them in chat:
  - **GCS Data Access cost finding → issue doc filed**, at the operator's explicit request "so Ikenna can pick this up":
    `plans/archive/2026_07/gcs_data_access_audit_log_cost_2026_07_24.md`. Operator: will route it to Ikenna, or pick it
    up personally Monday.
  - **"Default view = What's running" — DECIDED, not re-opened.** Operator: "keep this one" — confirms the original
    2026-07-17 lock stands; the remaining work is a mechanical `useState<TabId>` flip in `ArtifactPipeline.tsx`, no
    further decision needed. Phase 3 todo + Deferred-work table updated to reflect DECIDED rather than "re-decide with
    the operator."
  - **Phase 3c's live-launch verification split into its own todo** (operator: "add a todo item to launch and do the
    steps necessary to verify this") — previously just a note inside the shell-edit todo; now a standalone `[INFRA] P1`
    item so it can't be silently skipped once the code change ships.
  - **Bug #1 (image tags SHA-only) — root cause CONFIRMED, not a bug.** Operator: "the semver-agent that was supposed to
    write the version is dead right now and we have kept it dead deliberately. audited that one." Updated the "Pipeline
    bugs found" summary from "root-cause UNCONFIRMED" to resolved; flagged that the sibling issue doc
    (`build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`) still needs the same correction as a
    follow-up (out of today's scope — not edited).
  - **Stale "Staging-first" quickmerge.sh messaging — resolved as no-action-needed.** Operator: staging has been retired
    since June end, its workflows were only actually stopped recently; "keep it in quickmerge if it's not creating any
    issues." Cosmetic-only, intentionally left as-is.
  - **Phase 3d's tarball bucket path flagged as unconfirmed, not fact.** Operator: "there is a bucket where tarballs are
    uploaded, not sure if you are referring to that one" — added an explicit warning ahead of the
    `gcp_tarball_manifests()` todo that the cited path (from a `.tf` comment + a 2026-07-17 measurement) must be
    live-verified against the actual bucket before implementation starts, not trusted as-is.
  - **Not addressed this round** (still open, no new instruction given): the CPU-throttling test itself (still paused)
    and the "no documented fallback if CPU-throttling isn't the answer" gap — both remain exactly as Phase 7 already
    states them.
- **2026-07-27 — Phase 3b, 3d, and 3c (including the live-launch verification) ALL shipped in one session.** Operator
  dispatch: complete the plan's remaining todos autonomously. Shipped, each verified landed on
  `origin/live-defi-rollout` by content (not just exit code — this repo was under heavy concurrent-agent contention all
  session; several pushes needed 2-4 pull-rebase-retry cycles, and one retry silently dropped a staged edit that a
  content-diff check caught before it would have shipped an incomplete commit):
  - **Default tab flip** — `deployment-ui@fb1da34`. `useState<TabId>("pipe")` → `"run"`; fixed 10 Vitest + 6 `pw:L2`
    cases that assumed Pipeline was the default-rendered tab.
  - **Phase 3b (all 3 todos)** — `deployment-api@24070d9`, `deployment-ui@74c0a7d`. `image_digest`/`git_commit` added to
    the Deployments `DeploymentItem` (a real bug caught here: two pre-existing test fake-entry doubles needed the new
    attributes since `_vm_item()` now reads them unconditionally). `?git_commit=<sha>` deep-link filter on the
    Deployments view (client-side, first param with no owning dropdown, so a visible chip + clear link was added).
    Artifact Registry/ECR console-link builder (`artifactConsoleUrl()`), wired into both the Artifacts tab and the
    What's running tab's expanded detail (which now cross-links to both the registry console AND the Deployments commit
    filter — the operator's original 2026-07-17 ask).
  - **Phase 3d (all 5 todos)** — `deployment-api@3525bce`, `deployment-ui@05a087d`. Live-verified the tarball bucket
    path first (`gcloud storage ls`, ~4966 manifests/~1046 tarballs, matches the cited `.tf` comment exactly). Built
    `gcp_tarball_manifest_builds()`/`gcp_tarball_manifest_images()` reading ZERO manifest bodies (SHA is in the
    filename; every other field is `list_blobs` metadata) — a deliberate deviation from the original spec's "read each
    manifest" framing, kept the ~5000-object scan genuinely cheap. **A real bug a test caught before shipping**: the
    first draft fell back to the manifest JSON's OWN byte size when no matching `.tar.gz` existed, fabricating a
    plausible-but-wrong size for an orphaned manifest — fixed to honest `None`. **A stale claim caught and corrected**:
    this exact Phase 3d banner said "Deploy timeline ALREADY treats a GCE VM launch as the tarball-lane deploy event" —
    re-verifying the CITED commit's own message showed the opposite; no VM-launch deploy provider exists anywhere, so
    `running()`'s tarball coverage is genuinely zero, not partially built. Corrected in-place rather than left to
    mislead a future session. Pipeline/Artifacts UI needed zero production code changes (both already generic over the
    data), confirmed with new regression coverage.
  - **Phase 3c shell edit + Python test** — `deployment-service@d8b1411c`. One additive block in `_launch_with_tee()`
    (`if [[ -n … ]]; then export GIT_COMMIT=…; fi` — never a trailing `&&`, which would abort every VM boot under
    `set -euo pipefail`); all 7 audit conditions re-verified satisfied. Discovered the "accumulate
    `_tarball_actual_sha`" half of the plan's "2 additive edits" framing needs no code change at all — it's a plain
    (non-`local`) shell variable that already survives as a global from the download loop to `_launch_with_tee()`; only
    the read-and-export was net-new. Added `test_resolve_bom_reads_git_commit_from_env_via_deployment_config` in
    `test_bom.py` using the REAL `DeploymentConfig` (not the file's existing `_StubConfig` double) so the
    `AliasChoices("GIT_COMMIT", …)` resolution itself is exercised, not just `resolve_deployment_bom`'s passthrough.
  - Every plan-checkbox flip landed as its own `docs(plans):` commit, each independently content-verified against
    `origin/live-defi-rollout` — see the individual commit SHAs on each todo above.
  - **The Phase 3c live-launch verification — RESOLVED, took 3 attempts** (todo below Phase 3c's shell-edit todo).
    **First attempt (`qg-snapshot-20260727-232216`) deleted pre-work** — GCS copy of `setup-data-pipeline-vm.sh` was
    stale (predated this session's fix); deleted before it did any work, then republished both the setup script and the
    stale `deployment-service`/`unified-api-contracts` tarballs
    (`gcloud storage cp … + create-code-tarballs.sh --include …`), confirmed via the launcher's own freshness check
    ("setup script fresh" + "all 3 tarball(s) current"). **Second attempt (`qg-snapshot-20260727-232717`) launched clean
    but FAILED for an unrelated, pre-existing reason, unconnected to this plan's fix** — `SETUP_EXIT_STATUS=1`,
    `vm-setup.log` shows `SETUP FAILED rc=1` during `uv pip install` of ALL 28 repos simultaneously. Root cause:
    `VM_SERVICE=qg_snapshot` (the qg-snapshot launcher's own hardcoded metadata) matches no entry in `SERVICE_TARBALLS`,
    so `setup-data-pipeline-vm.sh` falls back to "installing all available tarballs" — a dependency-resolution conflict
    across the full 28-repo install, not anything this plan's `GIT_COMMIT` change touches (the failure happens during
    `uv pip install`, BEFORE `_launch_with_tee()` — where the new export lives — is ever reached). **A DIFFERENT agent
    (slot-4) independently found this same running VM** and filed
    `issues/deployment_service_qg_red_qg_snapshot_launcher_live_vm_flake_2026_07_27.md`, but misattributed it as "the
    real daily qg-snapshot cron" — it was actually this session's ad-hoc verification launch; that doc needs a
    correction noting the true origin (not yet applied — a small, low-priority follow-up, tracked as a new P3 todo below
    rather than silently left wrong). **Third attempt — pivoted to a properly-registered `VM_SERVICE` instead of
    fighting the qg-snapshot launcher's fallback bug**: `deployment_service` (this exact repo) IS a registered
    `SERVICE_TARBALLS` entry, so any launcher using it takes the normal single-tarball path. Chose
    `launch-measure-honest-coverage-vm.sh prediction` (`VM_SERVICE=instruments_service`, also registered; `prediction`
    picked as the smallest asset group to keep the run short) — a legitimate, already-scheduled (00:30 UTC daily)
    production task, e2-highmem-4, launched as `measure-honest-coverage-20260727-234251` (~2026-07-27T23:42:51 JST /
    ~14:42 UTC). Confirmed no singleton-lock conflict before launching. **Tarball staleness warnings on THIS launch are
    expected noise, not a blocker**: the launcher warned `instruments-service`/`unified-api-contracts`/
    `deployment-service` tarballs are stale relative to the ABSOLUTE latest commit on each repo — irrelevant here, since
    (a) `deployment-service`'s tarball manifest (`dae295f916b5…`) is a confirmed DESCENDANT of this session's fix commit
    (`d8b1411c`) regardless of being behind the latest HEAD, and (b) this specific task doesn't even need the
    `deployment-service` tarball (`VM_SERVICE=instruments_service` only pulls `instruments-service-code` + its
    UTL/UAC/MTDS dependency chain) — what matters for THIS verification is only that the VM correctly stamps WHATEVER
    commit_sha its manifest says, not which specific commit that is. **RESOLVED — this VM completed successfully,
    `exit_code=0`, self-deleted cleanly.** Registry row at
    `deployments/archive/2026-07-27/9dc3e0c9-6634-4f6c-a2cb-54d1d8786a46.json` carries
    `"git_commit": "f06eba12989dddff58831d26bf6977f92b57994e"` — non-empty, and spot-checked correct: the serial console
    (used instead of `vm-setup.log`, which the audit already noted only uploads on failure) shows the LAST of the 4
    tarballs this task needed — `instruments-service-code` — logged
    `manifest: sha=f06eba12989d version=v0.91.0-563-gf06eba12` immediately before "Code deployed from GCS (4 repos)", a
    12-char prefix match against the registry's full 40-char SHA. **All 4 verification-gate steps pass; see the Phase 3c
    live-launch todo above, now flipped `[x]`, for the complete evidence trail.**
