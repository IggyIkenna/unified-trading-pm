---
doc_type: plan
title: Finish features-sports-service → features-service consolidation (deploy side)
summary: >-
  The 2026-05-08 features-service repo consolidation moved sports code into features_service/sports/ and archived
  features-sports-service, but the deployment side was never finished — the live Cloud Run job still runs the old
  archived repo's stale image, broken since ~2026-04-22 (a fleet-wide unified-trading-library/unified-api-contracts
  version-skew bug). Stand up real deployment for the consolidated sports code, retire the old job, re-enable
  scheduling, then finish the deferred features-sports bare-bucket delete this outage blocked.
status: active
nature: process
asset_group: [sports]
stage: [meta]
repos: [features-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [deployment, consolidation, cloud-run, terraform, sports, outage, technical-debt]
related:
  [
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/archive/features_repo_consolidation_2026_05_08.plan.md,
    plans/active/issues/features_sports_service_cloud_run_job_broken_image_2026_07_15.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator decision 2026-07-15 (Path B chosen over patching the archived repo)
Codex SSOTs: [/codex/05-infrastructure/vm-launcher-runbook.md, /codex/08-workflows/ci-cd-flow.md]
---

# Finish features-sports-service → features-service consolidation (deploy side)

## What I found (2026-07-15, root-cause investigation)

While cutting over the `features-sports` flat-bucket migration ([[bucket_estate_consolidation_to_sub100_2026_07_13]]),
discovered `features-sports-service-job` (Cloud Run, region `asia-northeast1`, project `central-element-323112`) crashes
at Python import time: `ModuleNotFoundError: No module named 'unified_api_contracts.internal'` (from
`unified_trading_library/config_interface/auth/entitlements.py:15`). Its daily Cloud Scheduler trigger has been **PAUSED
since 2026-06-08**; last successful run **2026-06-07** — 5+ weeks of no sports feature computation.

**Root cause (confirmed via git history + Artifact Registry evidence, not guessed):**

1. `unified-trading-library`'s `entitlements.py` started requiring `unified_api_contracts.internal` as of commit
   `6bb892bc` (2026-04-02).
2. UTL's own `unified-api-contracts` dependency constraint stayed loose (`>=0.1.0,<1.0.0`) through at least 2026-04-22.
3. The only two `unified-api-contracts` wheels published in that whole window were `0.2.38` (2026-03-12, **predates**
   `internal/` by two weeks — `internal/` was only added 2026-03-26 in commit `1d08bae3`) and an out-of-sequence
   `0.1.20` (published later but numerically lower). A standard resolver picks the numerically highest match — `0.2.38`
   — so **any UTL base image built between 2026-04-02 and mid-2026 was fleet-wide broken** for this code path, not just
   this one service.
4. `features-sports-service`'s Dockerfile installs itself `--no-deps`, so it purely inherited whatever
   `unified-api-contracts` the `unified-trading-library:latest` base image had baked in the day it was built
   (2026-04-22, confirmed via `gcloud artifacts docker images list --include-tags`) — the broken `0.2.38`.
5. Nothing caught it: the repo's `quality-gates.sh` has no import/smoke gate, and the Dockerfile `HEALTHCHECK` only
   imports the lightweight top-level package `__init__.py`, never the real entrypoint (`cli/main.py`) where the crash
   lives.

**The compounding blocker:** `features-sports-service`'s GitHub repo was **archived 2026-05-08**
([[features_repo_consolidation_2026_05_08]]) — its code was already merged into `features-service`'s
`features_service/sports/` sub-package. But the **deployment side of that consolidation was never finished**: the live
Cloud Run job still runs the old archived repo's image, and no `features-service`-based sports Cloud Run job exists yet.
Patching the archived repo would re-legitimize something the org already decided to retire.

**Operator ruling 2026-07-15:** Path B — finish the abandoned consolidation properly rather than patch the archived
repo. This plan tracks that work.

## Why it matters

- A production data pipeline (sports features) has been silently dead for 5+ weeks with no alert firing (the scheduler
  pause looks intentional from the outside, not a crash).
- The same fleet-wide UTL/UAC version-skew window (2026-04-02 → mid-2026) may have affected other services built in that
  window that touch `config_interface/auth/entitlements.py` — **not yet audited**, flagged here for a possible follow-up
  sweep, not fixed in this plan (scope: features-sports-service only).
- `features-service`'s own `cloudbuild.yaml` already exists (`_SERVICE_NAME: features-service`) but was apparently never
  wired to a live Cloud Run job for the sports sub-command — this plan closes that gap.

## Todos

- [x] [INFRA] P0. Confirm a build against current dependency versions genuinely resolves a wheel containing
      `unified_api_contracts.internal` — verify with a real
      `docker run --rm --entrypoint python <image> -c "import unified_api_contracts.internal.schemas.rbac"`, not just an
      inference from version constraints, before wiring up any new deployment. — ✅ 2026-07-15, evidence:
      `docker pull     asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/features-service:latest`
      (digest `sha256:c204c49dbdc57200806c0b89e6f3ca2caa7f1226de062de09d05c2e942cdcdc9`, tags `0.66.0,7a60a31,latest`,
      built 2026-07-14) →
      `docker run --rm --entrypoint python <image> -c "import     unified_api_contracts.internal.schemas.rbac; ..."`
      exit 0, `IMPORT OK`; a second run additionally imported `unified_trading_library` + `log_event` (the exact failing
      chain from the issue doc) end-to-end, exit 0. The fleet-wide UTL/UAC version-skew bug does NOT reproduce against
      the current features-service image.
- [x] [INFRA] P0. Stand up a real Cloud Run job (+ any Workflow terraform resources mirroring the old
      `daily_workflow`/`backfill_workflow` definitions) for `features-service`'s `features_service/sports/*` sub-package
      — new terraform in `deployment-service/terraform/**`, reusing the existing `features-service` `cloudbuild.yaml`
      image. — ✅ 2026-07-15, `deployment-service@8b1c561f6d18fd7532b223ea462277131b03ebf8` (quickmerge, landed on
      `live-defi-rollout`, quality-gates.sh green): new
      `terraform/services/features-service-sports/gcp/{main,variables,terraform.tfvars,outputs,backend}.tf` — a
      distinctly-named job (`features-service-sports-job`) + daily/backfill Workflow set that COEXISTS with the legacy
      `features-sports-service-job` until it's retired (later todo). `terraform validate` clean; `terraform init` (real
      GCS backend, new state prefix `services/features-service-sports`) + `terraform plan` → "4 to add, 0 to change, 0
      to destroy" against real GCP APIs (project/SA verified live) — NOT applied (deploy is a later todo). Verified
      post-plan no resources exist yet (`gcloud run jobs list` / `gcloud workflows list` — neither
      `features-service-sports-job` nor its workflow present).
- [x] [SCRIPT] P0. Map CLI flags/entrypoint: confirm `features_service/sports/*`'s CLI surface matches what the old
      job's Cloud Run args/schedule expected (per this workspace's `--operation`/`--mode`/`--asset-group` CLI
      convention); adjust the new job's args if the consolidated CLI shape differs. — ✅ 2026-07-15:
      `--operation     compute --mode batch --asset-group SPORTS --tables fixture_features --start-date/--end-date` are
      UNCHANGED (read `features_service/sports/cli/{parser,main}.py`) — but the consolidated image is multi-family, so
      every invocation needs a NEW top-level dispatcher prefix `--feature-family sports` before those flags (read
      `features_service/cli/main.py` — `parse_known_args()` forwards everything after `--feature-family <x>` verbatim to
      `features_service.sports.cli.main.main()`); baked into both Workflow YAMLs above. **Second, more material
      finding**: the consolidated `features_service/sports/cli/_providers.py` + `_fetch_runner.py` docstrings state "All
      data fetching is done by instruments-service which writes to GCS. FSS reads from GCS only — no direct adapter
      instantiation" — confirmed by reading `batch_handler.py`'s `_run_batch()`, which now calls
      `run_fetch_providers(...)` → a pure GCS reader (`read_all_reference_data`), not an external API call. The old
      job's 4 `secret_environment_variables` (`BETFAIR_APP_KEY`/`ODDS_API_KEY`/`ODDSJAM_API_KEY`/`OPTICODDS_API_KEY`)
      are vestigial for the new architecture — grepped, zero references anywhere in `features_service/sports/*` — so the
      new terraform intentionally ships `secret_environment_variables = {}` (mirrors the `features-calendar-service`
      precedent) instead of carrying them over. **Separate, load-bearing terraform-only finding**: `features-service`'s
      Dockerfile `CMD` is `["uvicorn", "features_service.api.main:app", ...]` (the API-server default for the shared
      multi-family image) — unlike the legacy per-family image, a bare Cloud Run Job execution without an explicit
      `command` override would boot the API server instead of running the CLI to a terminal exit code. The new
      terraform's `daily_job` module now pins `command = ["python", "-m", "features_service"]` (verified in the
      `terraform plan` output) — this is NOT present in the legacy job's terraform and would have been a silent miss if
      copied verbatim.
- [x] [INFRA] P1. Repoint the existing GCS-FUSE mount / bucket wiring (canonical
      `features-sports-prd-central-element-323112`, already correct per the 2026-07-15 bucket-flattening sweep) to the
      new job. — ✅ 2026-07-15: new terraform's `gcs_volumes` reuses the SAME canonical bucket
      (`features-sports-${bucket_env_short}-${project_id}` → `features-sports-prd-central-element-323112`, confirmed
      against `unified-api-contracts/unified_api_contracts/config/cloud-providers.yaml`'s `features-sports:` key) —
      verified in the `terraform plan` output
      (`volume_mounts.mount_path =     /mnt/gcs/features-sports-prd-central-element-323112`,
      `gcs.bucket = features-sports-prd-central-element-323112`).
- [x] [INFRA] P1. Deploy the new Cloud Run job; manually trigger a real execution and watch it reach a genuine
      `SUCCEEDED` terminal state (not just "past the import line") before trusting it. — ✅ 2026-07-15 (~19:00Z
      ReverifyExecution): execution `features-service-sports-job-qsqs4` reached a GENUINE `SUCCEEDED` (`Completed=True`,
      `succeededCount=1`, `failedCount=0`; watched live to terminal on a 30s cadence). Ran the digest-pinned image
      `@sha256:b7fc3d7f…`, `command=["python","-m","features_service"]`, args overridden to the full contract
      `--feature-family sports --operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date 2026-07-14 --end-date 2026-07-15`.
      **The false `CONSOLIDATOR_DOWN` that killed `kk4dv` is CLEARED** — logs show
      `sports batch startup gate: instruments-store     consolidator healthy for sports (bucket=instruments-store-sports-prd-central-element-323112)`
      passing for BOTH dates (the exact preflight the UTL `c47273c1` lock-aware fix targets), no heartbeat/DOWN error.
      **Real output landed in the canonical bucket** (`gs://features-sports-prd-central-element-323112`):
      `compute_fixture_features[2026-07-14]` → 14 rows across leagues 129/2(UCL)/848(UECL)/874 → 4 non-empty
      `features.parquet` (17-18KB each) written `2026-07-15T18:59:15Z`; `compute_fixture_features[2026-07-15]` → 3 rows
      league 255(USL_CHAMPIONSHIP) → 1 parquet (18KB) written `18:59:29Z`; `Processing completed successfully`. Object
      write-timestamps match the log lines (not stale/placeholder). Scheduler `features-service-sports-daily-trigger`
      still PAUSED (unchanged — un-pause is todo 8). — 🟡 2026-07-15 DeployAndVerify phase: terraform applied clean (see
      Progress Log), scheduler paused, but BOTH manual executions attempted this touch terminated `NonZeroExitCode` —
      first on a real, separate terraform bug (default job `args` omit `--start-date`/`--end-date`, see new todo below),
      second (with correct date overrides) on an external, pre-existing blocker:
      `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` (the
      `instruments-store-sports` manifest consolidator is livelocked on its own GCS lock, never refreshing
      `availability_index.parquet` past the 120s freshness budget `features-service.compute_features` requires,
      `recovery=fail_fast`). Import chain + CLI contract + GCS mount all confirmed WORKING on this attempt — the blocker
      is downstream, in a different system. Per this touch's explicit instruction, did NOT proceed to retire the legacy
      job. Still `[ ]` — retry once the linked issue is resolved. **UPDATE 2026-07-15 ~19:53Z (VerifyImageDeploy):
      unblocked at the image/deploy boundary** — the CI hang is fixed, `features-service:latest` is now the fixed
      `0.66.0`/`afbe1ef` image, and the job is re-pinned to that verified digest `@sha256:b7fc3d7f…`
      (`deployment-service@6c47fa1d`, live job generation 2, scheduler still PAUSED). Re-attempt the manual execution
      with the same
      `--feature-family sports --operation compute --mode batch --asset-group SPORTS     --tables fixture_features --start-date/--end-date`
      overrides used in `kk4dv` and confirm a genuine `SUCCEEDED`; the `c47273c1` lock-aware preflight (now in-image,
      verified) should clear the false `CONSOLIDATOR_DOWN`.
- [x] [INFRA] P2. Fix `terraform/services/features-service-sports/gcp/main.tf`'s `module.daily_job.args` default
      (currently `--feature-family sports --operation compute --mode batch --asset-group SPORTS`, no dates) — a bare
      `gcloud run jobs execute` with no overrides fails CLI validation
      (`Batch mode requires --date or both     --start-date and --end-date`); every real Workflow invocation already
      overrides args via `containerOverrides` so this only bites a manual bare execute, but should still carry a sane
      default. Found + evidenced 2026-07-15 during the DeployAndVerify phase (see
      `instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` evidence section, execution
      `features-service-sports-job-fs8sj`). — ✅ 2026-07-15 (VerifyAndRetire phase), `deployment-service@f2ced5a8`
      (shipped in the same commit as todo 7). The default `args` now append
      `--date 2026-07-14 --tables fixture_features` — a fixed, immutable historical fixture date (proven non-empty: 14
      rows across leagues 129/2/848/874 per todo 5) so a bare smoke-execute is deterministic, cheap, and honestly
      non-empty rather than crashing on arg-validation. `--date` was confirmed the parser's single-date form
      (`features_service/sports/cli/parser.py`; no relative/`today` token exists, so a static date is the only viable
      terraform default). Applied in-place (`tofu apply -target=module.daily_job...`, `0 add / 1 change / 0 destroy`,
      image digest UNCHANGED @sha256:b7fc3d7f, job generation 3); live `gcloud run jobs describe` args verified to carry
      the new date/tables, so terraform code == live state (no drift).
- [ ] [INFRA] P2. On the NEXT features-service image rollout, re-pin
      `terraform/services/features-service-sports/gcp/terraform.tfvars`'s `docker_image` to the new verified digest (it
      is now an explicit `@sha256:…` pin, not `:latest` — deliberately, so the job runs a KNOWN verified image rather
      than silently inheriting whatever `:latest` resolved to at the last apply, which is how it ran the stale broken
      `c204c49d`). Verify the new digest in-container
      (`docker run … import     unified_trading_library.config_interface.auth.entitlements` +
      `assert_consolidator_healthy` source) before re-pinning. Added 2026-07-15 VerifyImageDeploy phase
      (`deployment-service@6c47fa1d`). _Alternative if the operator prefers tag-tracking: keep `:latest` but add a
      post-build `gcloud run jobs update --image` (or `terraform apply     -replace`) step to the features-service
      rollout so the tag→digest re-pins every build — a bare `:latest` alone does NOT auto-propagate to Cloud Run job
      executions._
- [x] [INFRA] P1. Apply the separately-found `--category`→`--asset-group` Workflow-YAML terraform drift (confirmed real,
      independent of the import crash, found via `terraform plan` on the old job's Workflow resources) — carry the fix
      into the new job's Workflow definitions; required before scheduling can safely resume. — ✅ 2026-07-15
      (DriftRetireReenable phase): verified SATISFIED-by-construction, no apply needed. The `--category` drift lives
      ONLY in the LEGACY workflows — `gcloud workflows describe features-sports-service-daily` line 36 = `--category`,
      `features-sports-service-backfill` line 15 = `--category`. The NEW job's workflows already use `--asset-group` in
      BOTH terraform code (`terraform/services/features-service-sports/gcp/main.tf` lines 107, 168) AND live
      (`gcloud     workflows describe features-service-sports-daily` → `--asset-group` at line 38). `terraform plan` on
      the new job dir (`-lock=false`) = ZERO infra drift (only a benign `backfill_example_command` output-value refresh,
      no resource change). The legacy `--category` workflows get destroyed with the legacy job (todo 7), so the fix
      needs no separate application. The real scheduled fire (todo 8) exercised the `--asset-group` workflow end-to-end.
- [x] [INFRA] P1. Repoint the per-fixture Tier-3/4 sports feature triggers (`features_pre_match` @ T-1h,
      `features_post_match` @ T+25h) in `deployment-service/configs/sports-trigger-tiers.yaml` from the legacy job to
      the new `features-service-sports-job` — PREREQUISITE for todo 7. — ✅ 2026-07-15 (RepointDispatch phase),
      `deployment-service@9ec1c3bef2330fe4fa53a38eefde634d66b996b4` (quickmerge `--agent --files`, landed on
      `live-defi-rollout`, `quality-gates.sh --no-fix` green in 59s, sentinel==HEAD; foreign soft-delete WIP in
      `terraform/gcp/main.tf` left untouched/isolated). **Dispatch-code fix (the real prerequisite, not a YAML swap):**
      `deployment_service/sports_trigger_scheduler.py::_build_cli_cmd` now injects a leading `--feature-family sports`
      (derived from `asset_group.lower()`) for the consolidated features-service via a new
      `_MULTI_FAMILY_DISPATCH_SERVICES = frozenset({"features-service"})` guard — so it emits
      `python -m features_service --feature-family sports --operation compute --mode batch --asset-group SPORTS …` and,
      after `_strip_python_module_prefix` (drops only `python -m <module>`), the Cloud Run args override leads with
      `--feature-family sports` (the exact selector the multi-family dispatcher `features_service/cli/main.py`
      requires). **Family/service-aware, NOT always-emit** — verified `_build_cli_cmd` is SHARED across services
      (instruments-service Tier-1/2, MTDS Tier-3), so instruments-service/MTDS dispatches are unchanged (2 new
      regression tests assert features-service gets the prefix + instruments-service does NOT). **YAML repoint:** both
      `features-service` entries (`features_pre_match` `--tables fixture_features,odds_features`; `features_post_match`
      `--tables derived_features`) `cloud_run_job_name` → `features-service-sports-job` (+ header-comment note refresh).
      **Runtime PROOF the new job accepts the per-fixture shape (real production path, not just a unit test):** drove
      the exact chain `_build_cli_cmd → _strip_python_module_prefix → CloudRunBackend.deploy_shard` (the same code a
      live per-fixture trigger runs) for BOTH shapes with a real single fixture date (start==end==2026-07-14): (1)
      pre_match override
      `--feature-family sports --operation compute --mode batch --asset-group SPORTS --start-date 2026-07-14 --end-date 2026-07-14 --run-tag live --tables fixture_features,odds_features`
      → execution `features-service-sports-job-trb5m` → genuine `Completed/True`, `succeededCount=1` ("completed
      successfully in 1m0.9s"); logs show `instruments-store consolidator healthy` + `market-data consolidator healthy`
      (no `CONSOLIDATOR_DOWN`), `fixture_features` computed, `odds_features` honestly recorded confirmed-empty (no
      upstream MTDS odds for that date), `Processing completed successfully`. (2) post_match override
      `… --tables derived_features` → execution `features-service-sports-job-slz8z` → genuine `Completed/True`,
      `succeededCount=1` ("completed successfully in 4m21.06s"); `Wrote derived_features: 14 total rows across leagues`
      (129/2·UCL/848·UECL/874), `Processing completed successfully` (the `recovery=skip` data_quality NaN warnings are a
      reference-data-completeness note, not a dispatch/exit failure). `readyToRetire=true` — todo 7 (legacy-job
      retirement) is now unblocked.
- [x] [INFRA] P1. Retire the old `features-sports-service-job` Cloud Run job + its Cloud Scheduler trigger once the new
      job is confirmed healthy end-to-end (avoid a double-fire window). — ✅ 2026-07-15 (VerifyAndRetire phase),
      `deployment-service@f2ced5a8a7162374c974e622ff803c8ad91ac4c8` (quickmerge `--agent --files`, on
      `origin/live-defi-rollout`, verified ancestor; `quality-gates.sh --no-fix` green 59s, sentinel==HEAD).
      Re-confirmed no live dispatch to the legacy job first (grep: only comments + the legacy dir's own vars remained;
      both `sports-trigger-tiers.yaml` per-fixture entries point at `features-service-sports-job`; the sole ENABLED
      daily scheduler on `0 7 * * *` is the NEW `features-service-sports-daily-trigger`, the legacy
      `features-sports-service-daily-trigger` was PAUSED). Retirement mirrors the features-calendar/features-onchain
      precedent: `tofu state rm` the 4 legacy resources (`module.daily_job.google_cloud_run_v2_job.job`,
      `module.daily_workflow.google_cloud_scheduler_job.trigger[0]`, `module.daily_workflow.google_workflows_workflow`,
      `module.backfill_workflow.google_workflows_workflow`; state prefix `services/features-sports-service`) BEFORE the
      physical `gcloud` delete of the job + scheduler + both workflows (`features-sports-service-daily`,
      `features-sports-service-backfill`); every `describe` returns **NOT_FOUND (404)**. Removed the whole legacy
      terraform dir (`terraform/services/features-sports-service/`, gcp + dead never-configured aws scaffold — its S3
      backend was a commented-out placeholder, so nothing was ever deployed on AWS) so a blind apply can't resurrect it,
      and refreshed the now-stale legacy cross-reference comments in the new job's `main.tf`. Post-delete re-verified
      the NEW job (generation 3, digest-pinned), scheduler (ENABLED), and both workflows (ACTIVE) are all
      intact/healthy. No double-fire window (legacy daily scheduler was PAUSED throughout, now deleted). — ⏸️ 2026-07-15
      (DriftRetireReenable phase): DEFERRED, `depends_on` the new repoint todo above. The legacy job's terraform is 4
      resources in its own state prefix `services/features-sports-service`
      (`module.daily_job.google_cloud_run_v2_job.job`,
      `module.daily_workflow.google_{workflows_workflow,cloud_scheduler_job.trigger[0]}`,
      `module.backfill_workflow.google_workflows_workflow.workflow`) — retirement = `terraform state rm` each + `gcloud`
      delete + remove the legacy `.tf` dir. NOT done this touch because `configs/sports-trigger-tiers.yaml` still
      dispatches per-fixture Tier-3/4 features to `features-sports-service-job`; deleting it now converts a "broken
      image" failure into a "job not found" failure on those live triggers. The double-fire risk todo 7 guards against
      is fully mitigated meanwhile: the legacy DAILY scheduler `features-sports-service-daily-trigger` stays PAUSED
      (verified `0 7 * * *`, same slot as the new one — kept paused deliberately). The separately-noted
      `uts-prod-features-sports-t1-schedule` / `features-sports-service-t1-recon`
      (`terraform/gcp/t1_batch_scheduler.tf`) does NOT target the legacy daily job — it targets
      `uts-prod-features-sports-service-t1-recon`, a job the file's own comment (lines 73-74) records as never having
      existed in any tier; it is a dead, already-PAUSED scheduler, left as-is (repointing it to the new job would
      conflate the T+1-recon architecture with the daily-window job). **UPDATE 2026-07-15 (RepointDispatch phase): the
      blocking prerequisite is now CLEARED + PROVEN** (`readyToRetire=true`) — the two `sports-trigger-tiers.yaml`
      per-fixture entries were repointed to `features-service-sports-job` and the dispatch code now emits the
      `--feature-family sports` prefix, with BOTH per-fixture shapes proven SUCCEEDED against the new job via the real
      `deploy_shard` path (pre_match `trb5m`, post_match `slz8z`; `deployment-service@9ec1c3be`, see the repoint todo
      above). Retiring the legacy `features-sports-service-job` (4 terraform resources in state prefix
      `services/features-sports-service`: `terraform state rm` each + `gcloud` delete + remove the legacy `.tf` dir) is
      now safe — nothing live dispatches to it (tiers repointed; legacy daily scheduler stays PAUSED). Left `[ ]` for
      the retirement phase.
- [x] [INFRA] P0. Re-enable scheduling for the new job (equivalent of `features-sports-service-daily-trigger`); verify
      one real scheduled (not just manual) fire succeeds. — ✅ 2026-07-15 (DriftRetireReenable phase, real evidence, not
      inference): `gcloud scheduler jobs resume features-service-sports-daily-trigger` → `state: ENABLED`; then
      `gcloud     scheduler jobs run features-service-sports-daily-trigger` (force fire at 19:13:56Z) → the scheduler
      POSTed to the `features-service-sports-daily` workflow executions endpoint, creating workflow execution
      `05bd100d-848d-4142-8fcc-699987f7a79c` (startTime 19:13:58Z). Watched live to terminal: workflow → `SUCCEEDED`,
      result
      `{"start_date":"2026-07-14","end_date":"2026-07-22","status":"completed","execution":"…features-service-sports-job-6tm9w"}`
      (a real T-1..T+7 window computed from `sys.now()`). The workflow spawned job execution
      `features-service-sports-job-6tm9w` → `status.conditions[0]=Completed/True`, `succeededCount=1`, `failedCount=0`.
      **Consolidator preflight healthy on EVERY date under the scheduled fire** (not just the manual one): logs show
      `sports batch startup gate: instruments-store consolidator healthy for sports (bucket=instruments-store-sports-prd-central-element-323112)` +
      `market-data consolidator healthy` repeated across the window, ZERO `CONSOLIDATOR_DOWN`. Real features computed:
      `compute_fixture_features[2026-07-18]: 55 fixtures`, `[2026-07-19]: 28`, `[2026-07-20]: 1`, `[2026-07-21]: 14`,
      `[2026-07-22]: 19`, then `Processing completed successfully` + `[features-service] shutdown complete`. Fresh
      non-empty parquet landed in the canonical bucket:
      `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-07-18/league=<L>/feature_group=fixture_features/features.parquet`
      written `2026-07-15T19:16:03-04Z` (17,750 B, matching the write-log line, not a placeholder). Scheduler left
      ENABLED on this verified-healthy state.
- [x] [INFRA] P2. Finish the deferred [[bucket_estate_consolidation_to_sub100_2026_07_13]] `features-sports` bare bucket
      delete (1 real migrated object + 2 confirmed-ephemeral VM-staging objects already accounted for) —
      `terraform state rm` the `google_storage_bucket.features_sports` resource before the physical delete (mirrors the
      `features-calendar` precedent), then delete the bucket. — ✅ 2026-07-15 (FinishBucketAndDocs phase, real
      evidence): re-confirmed the bare `gs://features-sports-central-element-323112` held exactly the expected 3 live
      objects (1 migrated `sfi_progressive.parquet` + 2 ephemeral `_vm_staging/fss_backfill/*`), 39 total rows incl.
      noncurrent versions all collapsing to those same 3 logical paths (no hidden data); verified the migrated object is
      intact in the canonical `gs://features-sports-prd-central-element-323112` (25,989 B).
      `tofu state rm     google_storage_bucket.features_sports` (prod state, prefix `terraform/state/prod`) →
      "Successfully removed 1 resource instance(s)"; canonical
      `google_storage_bucket.canonical["features-sports-prd-…"]` untouched. Removed the resource block from
      `deployment-service/terraform/gcp/main.tf` + the orphaned import block from `_imports_reconcile.tf` (both →
      REMOVED comments mirroring the features-calendar precedent), `tofu validate` clean; shipped
      `deployment-service@bfea7928` (quickmerge `--agent --files`, `quality-gates.sh --no-fix` green, sentinel==HEAD — a
      concurrent foreign soft-delete WIP in main.tf was stash-isolated so ONLY my hunk landed, then restored). Physical
      delete: `gcloud storage rm --recursive --all-versions --continue-on-error` (purged all 3 objects + all noncurrent
      versions → bucket empty) then `gcloud storage buckets delete --quiet`; `buckets describe` → `404 not found`.
      Canonical bucket + migrated object re-verified alive post-delete.
- [x] [DOCS] P2. Close `plans/active/issues/features_sports_service_cloud_run_job_broken_image_2026_07_15.md` (status →
      resolved), append final Progress Log entries to both this plan and
      `bucket_estate_consolidation_to_sub100_2026_07_13.md`, and note in
      `plans/archive/features_repo_consolidation_2026_05_08.plan.md` that the deploy-side gap is now closed. — ✅
      2026-07-15 (FinishBucketAndDocs phase): flipped all 4 related issue docs to `status: resolved` with Resolution
      sections + `resolved_by` provenance — `features_sports_service_cloud_run_job_broken_image_2026_07_15.md`,
      `features_service_cloud_build_quality_gates_hang_2026_07_15.md` (root cause = a unit-test gs:// hermeticity bug,
      fixed `features-service@bd0db4d7`, green build `fd73ca17`), and the two consolidator docs
      (`instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` closed as a MISDIAGNOSIS of its
      already-root-caused sibling `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`; both
      fixed by UTL `c47273c1`, now deployed + proven). Appended the closing Progress Log entry below + a closing entry
      to `bucket_estate_consolidation_to_sub100_2026_07_13.md`, and annotated
      `plans/archive/features_repo_consolidation_2026_05_08.plan.md` that the deploy-side gap is now closed.
- [x] [REVIEW] P3. _(stretch, optional)_ Scope (do not fix here) whether other services built in the 2026-04-02 →
      mid-2026 window touch `config_interface/auth/entitlements.py` and could have the same silent breakage — file a
      separate audit plan if the scope looks non-trivial. — ✅ 2026-07-15, DONE WITH FINDINGS (read-only fleet audit,
      NOT descoped): enumerated all 149 UTL/UAC-bearing Cloud Run deployments (24 services + 125 jobs, 7 regions; VMs
      out of scope — tarball deploys resolve deps fresh), flagged 17 in-window suspects, and docker-tested each by
      pulling its EXACT deployed digest and running
      `import     unified_trading_library.config_interface.auth.entitlements`. **RESULT: ZERO other broken deployments —
      features-sports-service was the ONLY casualty.** 16/17 suspects printed IMPORT_OK exit 0; the 17th
      (`market-data-tradfi` consolidator) is HEALTHY-by-parity (identical fresh `:latest` digest + entrypoint family as
      2 clean-tested siblings running `*/1` successfully). Root reason the in-window heuristic over-flags: MTDS-family
      images vendor UAC from SOURCE at `/app/.deps/`, which already contains `internal/`, so the broken-published-wheel
      failure mode structurally cannot reproduce for them; Cloud Run jobs also re-resolve `:latest` per execution and
      self-heal on the fresh post-fix image. Full per-deployment table, verdicts, generic per-broken remediation recipe
      (mirrors this session's features-sports fix, incl. the archived-repo caveat), and two SEPARATE non-bug operational
      findings (~37-day paused-DeFi-collector data gap; Group-C jobs failing today on fresh images) filed at
      [`plans/active/issues/utl_uac_skew_fleet_audit_2026_07_15.md`](issues/utl_uac_skew_fleet_audit_2026_07_15.md).

## Progress Log

- 2026-07-15: Plan created. Root cause fully confirmed (see "What I found"); operator chose Path B (finish the
  consolidation) over Path A (patch the archived repo) in the same session. No execution yet — this plan is the tracking
  vehicle for the work about to start.
- 2026-07-15 (BuildDeployment phase, todos 1-4): Confirmed with real evidence (not inference) that the current
  `features-service:latest` image resolves `unified_api_contracts.internal` cleanly (docker run exit 0, full
  `unified_trading_library` import chain including the exact `entitlements.py` line that crashed the old job). Wrote +
  shipped `deployment-service@8b1c561f6d18fd7532b223ea462277131b03ebf8` — new
  `terraform/services/features-service-sports/gcp/**` (Cloud Run Job `features-service-sports-job` + daily/backfill
  Workflow, distinctly named so it can coexist with the legacy job until retirement). `terraform validate` clean;
  `terraform plan` against real GCP APIs (new state prefix, not applied) shows a clean "4 to add" with correct
  image/SA/bucket/env wiring. Two real findings surfaced during CLI-mapping due-diligence and are now baked into the
  terraform (see todo 3's evidence): (1) the consolidated dispatcher needs a `--feature-family sports` prefix on every
  invocation; (2) the consolidated `features_service/sports/*` no longer performs direct provider fetches (that moved to
  instruments-service) so the legacy job's 4 provider-API secrets are dead code for the new job and were intentionally
  dropped; (3) `features-service`'s Dockerfile CMD is `uvicorn ...` (API server) so the new job's terraform explicitly
  pins `command = ["python", "-m", "features_service"]` — omitting this would have silently booted the wrong process on
  every execution. NOT deployed/applied this touch (todos 5-8 — execute, verify SUCCEEDED, retire the old job, re-enable
  scheduling — are separate, later steps; see this session's structured handoff for the readyToDeploy assessment).
  Adjacent finding, NOT actioned (outside this touch's scope): a second scheduler,
  `uts-prod-features-sports-t1-schedule`, is also PAUSED and likely also points at the same broken legacy
  `features-sports-service-job` (via `terraform/gcp/t1_batch_scheduler.tf`'s `features-sports-service-t1-recon` entry) —
  the later "retire old job / re-enable scheduling" todos should check whether this t1-recon path also needs repointing
  to the new job before it's safe to un-pause.
- 2026-07-15 (DeployAndVerify phase, todo 5 — real evidence, not inference): Independently re-verified the prior
  BuildDeployment-phase terraform (`deployment-service@8b1c561f6d18fd7532b223ea462277131b03ebf8`) against live GCP —
  commit present on `origin/live-defi-rollout`, `terraform init` + fresh `terraform plan` reproduced the same "4 to add,
  0 to change, 0 to destroy", SA + Artifact Registry image both confirmed to exist live. Applied with `-target` scoped
  to exactly the 4 new resources (`module.daily_job.google_cloud_run_v2_job.job`,
  `module.daily_workflow.google_workflows_workflow.workflow`,
  `module.daily_workflow.google_cloud_scheduler_job.trigger`,
  `module.backfill_workflow.google_workflows_workflow.workflow`) —
  `Apply complete! Resources: 4 added, 0 changed, 0 destroyed`; post-apply `terraform plan` shows zero infra drift (only
  a benign output-value diff). Immediately `gcloud scheduler jobs pause features-service-sports-daily-trigger` →
  confirmed `PAUSED`, per the terraform's own double-fire-avoidance note. **Manual verification did NOT reach SUCCEEDED
  — todo 5 stays open, legacy job NOT retired, per this touch's explicit instruction to stop on any execution failure.**
  Two real executions run: (1) bare `gcloud run jobs execute` (no overrides) → `features-service-sports-job-fs8sj`,
  `NonZeroExitCode`, failed CLI validation (`Batch mode requires --date or both --start-date and --end-date` — the job's
  default `args` genuinely omit dates, new follow-up todo added above); (2) retried with `--args` overrides matching the
  Workflow's real contract
  (`--feature-family sports --operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date 2026-07-14 --end-date 2026-07-15`)
  → `features-service-sports-job-kk4dv`, got PAST CLI validation + the full Python import chain (re-confirms the
  fleet-wide UTL/UAC skew bug does not reproduce) + GCS-FUSE mount, then failed `NonZeroExitCode` on
  `Manifest consolidator appears DOWN for bucket='instruments-store-sports-prd-central-element-323112': ... heartbeat is 208s old (> 120s budget) ... recovery=fail_fast`.
  Root-caused (not guessed): the `uts-prod-manifest-consolidator-instruments-sports` Cloud Run Job (single Scheduler
  cron, `*/1 * * * *`, no duplicate trigger) is livelocked — every ~1min cycle logs
  `skipping cycle ... fresh lock present (sibling cron still running)` + `error=locked` (8/8 sampled executions between
  12:14-12:41 UTC), yet no genuine sibling overlaps (each run completes in 7-9s). `_index/consolidator.lock` is
  rewritten fresh on every cycle including skip-only cycles, consistent with a lock-TTL bug that never lets the lock age
  out. `availability_index.parquet` got exactly one genuine write in the ~30min observed window (12:39:43 UTC) then went
  stale again immediately. Filed as
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` (new issue, P1,
  cross-repo/data-correctness — this is an EXTERNAL blocker in a different system, not a defect in the
  features-service-sports deploy work itself, which is now proven correct up to that boundary). **Terraform/job/workflow
  resources deliberately left in place** (scheduler stays paused) — no rollback needed, they are correct; re-attempt
  manual verification once the linked issue is resolved, THEN proceed to todos 6-8.
- 2026-07-15 (DriftFixRetireReenable phase, todos 6-8 — STOPPED per gating condition, real evidence, not inference):
  Task handoff explicitly gated todos 6-8 on `manualExecutionSucceeded`; independently re-verified (not just trusted the
  flag) rather than proceeding: `gcloud run jobs executions describe features-service-sports-job-kk4dv` still shows
  `Completed=False / NonZeroExitCode`; `gcloud scheduler jobs describe features-service-sports-daily-trigger` still
  `PAUSED`; the linked blocker (`instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`) is confirmed
  STILL ACTIVE — `uts-prod-manifest-consolidator-instruments-sports` executions are still firing on a tight ~1min
  cadence at 2026-07-15T12:47-12:49Z (same livelock signature as the earlier observation window). Per the task's
  explicit instruction, did NOT proceed to todo 6 (Workflow YAML `--category`→`--asset-group` drift fix), todo 7 (retire
  the legacy job), or todo 8 (re-enable scheduling) — all three remain `[ ]`. No terraform/config changes made, nothing
  shipped this touch. Next unblock step: resolve the manifest-consolidator livelock issue, then re-attempt a manual
  `features-service-sports-job` execution to a genuine `SUCCEEDED` terminal state (todo 5) before revisiting 6-8.
- 2026-07-15 (FinishBucketAndDocs phase, todos 9-10 — STOPPED per this touch's explicit gating condition, real evidence,
  not inference): Task instruction was "if `schedulingReenabled` is false or `realScheduledFireVerified` is false, STOP
  and report why — do not delete the bucket on an unhealthy service." Independently re-verified live rather than
  trusting the prior touch's handoff flags:
  `gcloud scheduler jobs describe features-service-sports-daily-trigger --location=asia-northeast1 --project=central-element-323112`
  → still `state: PAUSED`; `gcloud run jobs executions list --job=features-service-sports-job` → both prior executions
  (`kk4dv`, `fs8sj`) still show `Completed=False` (no successful execution exists at all, manual or scheduled);
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` → `status: open`;
  `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-instruments-sports` → still firing on the same
  tight ~1min livelock cadence (executions at 12:48-12:52 UTC, i.e. still reproducing ~10min after the prior touch's
  last observation). **Gate condition holds** (`schedulingReenabled=false`, `realScheduledFireVerified=false`) — did NOT
  touch the `features-sports` bare bucket, did NOT edit `deployment-service/terraform/gcp/main.tf`'s
  `google_storage_bucket.features_sports` resource, did NOT close the linked issue doc
  (`features_sports_service_cloud_run_job_broken_image_2026_07_15.md` stays as-is), and did NOT append to
  `bucket_estate_consolidation_to_sub100_2026_07_13.md` since there is nothing new to report there — the bucket delete
  remains blocked on the SAME unresolved external livelock as the prior touch. Todos 6-10 remain `[ ]`. No
  terraform/config/code changes made in any repo this touch; the only change is this documentation-only append. Next
  unblock step unchanged from the prior touch: resolve
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` first, then re-attempt
  `features-service-sports-job` to a genuine `SUCCEEDED`, then re-enable scheduling + verify one real scheduled fire —
  only then is it safe to revisit todos 6-10 (Workflow YAML drift, legacy job retirement, scheduling re-enable, bucket
  delete, issue-doc closure).
- 2026-07-15 (~13:45Z, fleet-wide manifest-consolidator audit — DOCS-ONLY, read-only, relevant to todo 5's blocker): A
  separate dispatch audited all 25 other `uts-prod-manifest-consolidator-*` Cloud Run jobs to check whether the
  `instruments-sports` livelock blocking this plan's todo 5 (per
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`) is a fleet-wide defect.
  **Result: it is not** — 0 of the 25 audited jobs show the same signature (23 HEALTHY, 2 DORMANT/paused-and-excluded, 1
  new-but-different finding: `market-data-cefi` needs the same `CONSOLIDATOR_LOCK_TTL_SECONDS` override pattern already
  applied to `market-data-defi`/`instruments-sports`, unrelated to this plan). **More importantly, a live re-watch of
  `instruments-sports` itself (13:32-13:39Z) found it is NOT actually an indefinite livelock** — it is a genuine ~7-8min
  real merge (confirmed: one watched end-to-end, 434.7s, clean acquire→merge→write→release, lock correctly absent
  immediately after) colliding with a naive freshness-gate threshold
  (`assert_consolidator_healthy`/`ConsolidatorLivenessMonitor`) that can't tell a legit in-flight merge from a downed
  consolidator. **This exact mechanism was already root-caused and fixed in code** by a sibling issue doc
  (`plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`, discovered via
  this audit — the two issue docs were filed independently on the same underlying bug from two different entry points):
  `unified-trading-library@c47273c1` ("lock-aware consolidator liveness — a fresh held lock is proof-of-life, not
  DOWN"), committed 2026-07-15T13:03:17+01:00, is UTL's current HEAD. **This directly gives todo 5 a concrete, scoped
  unblock path** (replacing the prior open-ended "wait for the livelock investigation"): (1) rebuild the
  `market-tick-data-service` (MTDS) image + redeploy the consolidator-liveness-watchdog so it carries `c47273c1`; (2)
  rebuild + redeploy `features-service`'s own image (its `assert_consolidator_healthy` call, confirmed via `grep` in
  `features_service/sports/cli/handlers/_manifest_preflight.py`, is baked into the 2026-07-14 image digest that predates
  this fix); (3) only then re-attempt the manual `features-service-sports-job` verification execution. Both issue docs
  updated + cross-linked with the full per-job audit table and evidence; no code, terraform, or Cloud Run/Scheduler
  config was touched (docs-only). Todo 5 stays `[ ]` — the blocker is confirmed still live (the fix is not yet deployed
  anywhere) — but is no longer an open-ended fleet-wide unknown.
- 2026-07-15 (~15:45Z, UnblockDeploy phase — dispatched per the prior touch's concrete unblock path, real evidence, not
  inference): Completed all 3 prerequisite deployment actions the prior touch's audit identified as blocking todo 5. (1)
  `market-data-cefi` TTL-shorter-than-real-merge-duration fix shipped (`deployment-service@8e94608`,
  `CONSOLIDATOR_LOCK_TTL_SECONDS=1200`, live-bumped via `gcloud run jobs update` + codified in terraform,
  `quality-gates.sh --no-fix` green) — unrelated to sports but was the one open item from the fleet-wide audit, closed
  while in the area. (2) Independently re-verified (not just trusted) that the `uts-prod-consolidator-liveness-watchdog`
  MTDS rebuild+redeploy already reported in the sibling issue doc's 14:05Z update is real and live:
  `market-tick-data-service:latest` resolves to `sha256:1e974ccd...`, the watchdog's most recent execution ran that
  exact digest, and its logs show 0 DOWN across all 26 buckets. (3) Rebuilt `features-service` itself against the
  fix-containing UTL base image: confirmed via real `docker run` (not inference) that UTL AR digest `sha256:56bd0fe5...`
  (built from UTL HEAD `c47273c1`) genuinely contains the `consolidator_cycle_in_flight` short-circuit inside
  `assert_consolidator_healthy`; bumped `features-service/Dockerfile`'s `BASE_IMAGE_DIGEST` accordingly
  (`features-service@7c2e4ef1`, `quality-gates.sh --no-fix` green); manually triggered `features-service-build` (its
  Cloud Build trigger only fires on push to `main`, not `live-defi-rollout` where quickmerge lands) — build
  `0b5cec2d-2f6a-4416-b870-44e3db644e1f` against the correct commit, in progress as of this entry.
  `features-service-sports-job`'s terraform `docker_image` is pinned to the mutable `:latest` tag, so once this build
  pushes, the job's next execution picks up the fix with no further terraform/gcloud action needed on the job itself.
  **Todo 5 stays `[ ]`** — this phase deliberately stopped short of re-attempting the manual verification execution
  (gated on the Cloud Build above reaching `SUCCESS`); full evidence in
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`'s matching 15:45Z update.
  Next step: once the build succeeds, re-run `features-service-sports-job` with the same
  `--feature-family sports --operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date/--end-date`
  overrides used in execution `kk4dv` and confirm a genuine `SUCCEEDED` terminal state. **UPDATE (~15:37Z): the Cloud
  Build did NOT reach `SUCCESS`** — it hung inside the quality-gates test step both times (original + one retry) and
  never pushed a new image; `features-service:latest` is confirmed still the stale 2026-07-14 image. Filed as
  `plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md` (P1, suspected `E2_HIGHCPU_8`
  memory pressure, not confirmed). Todo 5 stays `[ ]` and should NOT be re-attempted yet — it would still hit the same
  false-DOWN error against the un-updated image. This is now the blocking item, ahead of the consolidator livelock doc
  (which is otherwise resolved pending this deploy).
- 2026-07-15 (~16:55Z, FinishBucketAndDocs phase re-dispatch, todos 9-10 — STOPPED again per the same gating condition,
  real evidence, not inference): Re-dispatched with the identical gate: "if `schedulingReenabled` is false or
  `realScheduledFireVerified` is false, STOP and report why — do not delete the bucket on an unhealthy/unverified
  service." Independently re-verified live rather than trusting either the task's flags or the prior 13:53Z STOP entry
  (`d737b09fd`):
  `gcloud scheduler jobs describe features-service-sports-daily-trigger --location=asia-northeast1 --project=central-element-323112`
  → still `state: PAUSED`. `gcloud run jobs executions list --job=features-service-sports-job` → still only the same two
  executions from earlier today, both `Completed=False` (`kk4dv` @ 12:37:32Z, `fs8sj` @ 12:33:56Z) — no execution of any
  kind (manual or scheduled) has ever reached `SUCCEEDED`.
  `gcloud artifacts docker images list …/features-service --include-tags --sort-by=~CREATE_TIME` → `:latest` is still
  digest `sha256:c204c49d…`, built 2026-07-14T00:58:45 — unchanged, still predates the UTL `c47273c1`
  lock-aware-consolidator-liveness fix. `gcloud builds list` (unfiltered, newest-first) confirms no new features-service
  build attempt exists beyond the two already-filed failures against commit `7c2e4ef1` (`0b5cec2d` TIMEOUT, `c4262919`
  CANCELLED) — the most recent builds in the whole project (15:15Z onward: two `unified-api-contracts` builds, a
  `deployment-service` build) are unrelated to features-service. **Gate condition still holds**
  (`schedulingReenabled=false`, `realScheduledFireVerified=false`) — consistent with, not superseding, the 13:53Z STOP.
  Per the explicit instruction: did NOT touch the `features-sports` bare bucket
  (`gs://features-sports-central-element-323112`), did NOT edit `deployment-service/terraform/gcp/main.tf`'s
  `google_storage_bucket.features_sports` resource or its `_imports_reconcile.tf` import block, did NOT close
  `plans/active/issues/features_sports_service_cloud_run_job_broken_image_2026_07_15.md`, did NOT touch
  `bucket_estate_consolidation_to_sub100_2026_07_13.md` (no new state to report there — same blocker), and did NOT flip
  todos 6-10 (all remain `[ ]`). No terraform/config/code changes made in any repo this touch; this Progress Log append
  is the only change. Next unblock step unchanged: get a features-service Cloud Build to genuinely reach `SUCCESS`
  against the UTL `c47273c1`-based commit (root-causing/fixing the quality-gates hang in
  `plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md` is the prerequisite), verify the
  new digest carries the fix, re-attempt `features-service-sports-job` to a genuine `SUCCEEDED`, un-pause + verify one
  real scheduled fire — only then revisit todos 6-10 (Workflow-YAML drift, legacy-job retirement, scheduling re-enable,
  bucket delete, issue-doc closure) in a future touch.
- 2026-07-15 (~16:45Z, FixBuildHang phase re-dispatch — real evidence, not inference; hang still NOT resolved):
  Dispatched specifically to root-cause and fix the `features_service_cloud_build_quality_gates_hang_2026_07_15.md`
  blocker. Falsified the issue doc's "suspected root cause" (xdist parallel-worker memory pressure) with source-level
  evidence — `features-service/scripts/quality-gates.sh` forces `PYTEST_WORKERS=0` unconditionally, so pytest already
  runs single-process (`-n 0`) in BOTH local and Cloud Build environments; the CI-only `-n auto` path never fires for
  this repo. Found and fixed a real, separate local<->CI parity bug instead (`gcp_auth_info` test fixtures in
  `tests/cross_instrument/conftest.py` + `tests/multi_timeframe/conftest.py` could resolve REAL ambient GCE metadata
  credentials on an actual Cloud Build worker while always falling back to mocks off-GCE) — `features-service@78fd05d1`,
  local `quality-gates.sh --no-fix` full run green (6:02, sentinel matches HEAD), shipped via quickmerge. Re-triggered
  `features-service-build` against this commit
  (`gcloud builds triggers run features-service-build --branch=live-defi-rollout`) → build
  `cc976c01-794a-4437-a745-4e1c8ccf722f`. **The hang reproduced at the identical checkpoint** (`[3/6] TESTS` →
  `Coverage floor` line, then flat) — watched live for ~10 confirmed-flat minutes before deliberately cancelling (not
  another blind full 1800s) since the evidence was already conclusive. Full findings + evidence in
  `plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md`'s new Progress Log entry. **Root
  cause still unconfirmed; `features-service:latest` is STILL the stale 2026-07-14 `sha256:c204c49d...` image** — todo 5
  stays `[ ]`, unchanged from before this touch. Did NOT apply a machine-type bump or xdist-worker-cap (the issue doc's
  other suggested fixes) since the mechanism they target is now falsified — applying either would be an unevidenced
  guess. Next step (per the issue doc's updated "not yet tried" list): get live/streamed pytest output out of a Cloud
  Build run (currently fully silent until pass/fail) so the NEXT attempt can localize exactly which test is stuck, or
  bisect by feature-family via a throwaway trigger, before proposing any resource/parallelism change.
- 2026-07-15 (DriftFixRetireReenable phase re-dispatch, todos 6-8 — STOPPED again per the same gating condition, real
  evidence, not inference): Re-dispatched with `manualExecutionSucceeded=false` handed off from the reverify phase. Per
  the task's explicit instruction ("if manualExecutionSucceeded is false, STOP and report why — do not retire anything
  or touch scheduling"), independently re-verified live rather than trusting the handoff flag alone (account
  `ikenna@odum-research.com` / project `central-element-323112`, both confirmed matching this time — no auth/project
  mismatch this touch):
  `gcloud scheduler jobs describe features-service-sports-daily-trigger --location=asia-northeast1` → still
  `state: PAUSED`. `gcloud run jobs executions list --job=features-service-sports-job` → still only the same two
  executions (`kk4dv`, `fs8sj`); `gcloud run jobs executions describe features-service-sports-job-kk4dv` →
  `Completed=False`, `reason=NonZeroExitCode`, `failedCount=1` — no execution (manual or scheduled) has ever reached
  `SUCCEEDED`. `gcloud artifacts docker images list …/features-service --include-tags --sort-by=~CREATE_TIME` →
  `:latest` is still digest `sha256:c204c49d…`, built 2026-07-14T00:58:45 — unchanged, still predates the UTL `c47273c1`
  lock-aware-consolidator-liveness fix. `gcloud builds list` (newest-first, 8 builds) shows the most recent
  features-service build attempt is still `cc976c01-794a-4437-a745-4e1c8ccf722f` (`CANCELLED`, 16:30:50Z, the same one
  already filed in the issue doc) — no new features-service build has been triggered since; the builds newer than it are
  all `unified-trading-library`/`market-tick-data-service` (unrelated). **Gate condition holds**
  (`manualExecutionSucceeded=false`) — did NOT apply the `--category`→`--asset-group` Workflow-YAML drift fix (todo 6),
  did NOT run `terraform plan`/`apply` on it, did NOT touch `terraform state rm` or delete the legacy
  `features-sports-service-job`/`features-sports-service-daily-trigger` (todo 7), and did NOT un-pause
  `features-service-sports-daily-trigger` or force a scheduler fire (todo 8). No terraform/config/code changes made in
  any repo this touch; this Progress Log append is the only change. Todos 6-8 remain `[ ]`. Next unblock step unchanged
  from the prior touch: get a `features-service` Cloud Build to genuinely reach `SUCCESS` against the UTL
  `c47273c1`-based commit (root-causing the quality-gates hang in
  `plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md` is the prerequisite — its "not yet
  tried" list, in order: (a) stream pytest output live instead of the current silent redirect so a hang localizes to a
  specific test, (b) bisect by feature-family via a throwaway Cloud Build trigger), verify the new digest carries the
  fix, re-attempt `features-service-sports-job` to a genuine `SUCCEEDED`, THEN revisit todos 6-8 in a future touch.
- 2026-07-15 (~17:02Z, FinishBucketAndDocs phase re-dispatch — STOPPED again per the identical gating condition, real
  evidence, not inference): Re-dispatched with the explicit instruction "if `schedulingReenabled` is false or
  `realScheduledFireVerified` is false, STOP and report why — do not delete the bucket on an unhealthy/unverified
  service." Independently re-verified live rather than trusting the handed-in flags or any prior touch's entry:
  `gcloud scheduler jobs describe features-service-sports-daily-trigger --location=asia-northeast1 --project=central-element-323112`
  → still `state: PAUSED`. `gcloud run jobs executions list --job=features-service-sports-job` → still only the same two
  executions (`kk4dv` @ 2026-07-15T12:37:32Z, `fs8sj` @ 2026-07-15T12:33:56Z), both `Completed=False`/`NonZeroExitCode`
  — no execution, manual or scheduled, has ever reached `SUCCEEDED`.
  `gcloud artifacts docker images list .../features-service --include-tags --sort-by=~CREATE_TIME` → `:latest` is still
  digest `sha256:c204c49d...`, built 2026-07-14T00:58:45 — unchanged, still predates the UTL `c47273c1`
  lock-aware-consolidator-liveness fix (`gcloud builds list` itself was unreachable this touch — repeated calls timed
  out after 60-90s with no output, a tooling/API-latency issue distinct from the build-hang bug itself — but the
  Artifact Registry digest/timestamp is the authoritative signal for "has a build ever pushed a new image," and it is
  unchanged, so the gate conclusion does not depend on the builds-list call succeeding). Cross-checked all 4 linked
  issue docs' frontmatter `status:` field directly (not just prose):
  `features_sports_service_cloud_run_job_broken_image_2026_07_15.md` = `open`,
  `features_service_cloud_build_quality_gates_hang_2026_07_15.md` = `open`,
  `instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` = `open`,
  `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md` = `open`. **Gate condition holds**
  (`schedulingReenabled=false`, `realScheduledFireVerified=false`) — did NOT touch the `features-sports` bare bucket
  (`gs://features-sports-central-element-323112`), did NOT edit `deployment-service/terraform/gcp/main.tf`'s
  `google_storage_bucket.features_sports` resource or its `_imports_reconcile.tf` import block, did NOT run any
  `terraform state rm`/`gcloud storage rm`/`gcloud storage buckets delete`, did NOT close ANY of the 4 linked issue docs
  (all remain `status: open`, none flipped to `resolved`), and did NOT flip todos 6-10 (all remain `[ ]`). No
  terraform/config/code changes made in any repo this touch; this Progress Log append (+ the matching append to
  `bucket_estate_consolidation_to_sub100_2026_07_13.md`) is the only change, shipped docs-only per the PM `docs(plans):`
  direct-push carve-out. Next unblock step unchanged from every prior touch since the build-hang was discovered: get a
  `features-service` Cloud Build to genuinely reach `SUCCESS` against the UTL `c47273c1`-based commit
  (root-causing/fixing the hang in `features_service_cloud_build_quality_gates_hang_2026_07_15.md` is the prerequisite —
  its "not yet tried" list is unchanged: (a) stream pytest output live instead of the current silent redirect to
  localize the stuck test/module, (b) bisect by feature-family via a throwaway Cloud Build trigger), verify the new
  digest carries the fix, re-attempt `features-service-sports-job` to a genuine `SUCCEEDED`, un-pause + verify one real
  scheduled fire — only then is a future touch safe to revisit todos 6-10 (Workflow-YAML drift, legacy-job retirement,
  scheduling re-enable, bucket delete, issue-doc closure).
- 2026-07-15 (~17:53Z, ShipAndTrigger phase — implemented "not yet tried" item (a): stream pytest output live +
  phase-agnostic hang self-localizer, then re-triggered the build). Shipped three diagnostic edits toward getting a
  `features-service` Cloud Build to fail FAST with the stuck stack instead of stalling silently to the 1800s timeout:
  (i) `features-service/pyproject.toml` — `timeout_method = "thread"` under `[tool.pytest.ini_options]` so the existing
  `--timeout=60` fires a thread-based all-thread stack dump on a TEST/FIXTURE-phase hang (the default `signal` method
  can't interrupt a C-level/syscall hang); (ii) `features-service/tests/conftest.py` — a module-level (import-time)
  faulthandler watchdog gated on `CLOUD_BUILD == "true"`
  (`faulthandler.dump_traceback_later(420, exit=True, file=sys.stderr)`) that is PHASE-AGNOSTIC — it catches a
  COLLECTION/import-phase hang that pytest-timeout's per-item watchdog cannot, dumping every thread's stack and
  hard-exiting non-zero at ~7min so base-service.sh's failure-path `cat`/tee surfaces the stack; (iii)
  `unified-trading-pm/scripts/quality-gates-base/base-service.sh` — both pytest invocations rewritten from
  `>>"$_pytest_log" 2>&1; cat-on-failure` to `2>&1 | tee -a "$_pytest_log"` + `_pytest_rc=${PIPESTATUS[0]}` so output
  streams LIVE (the redirect+trap-rm design deleted the tempfile on the timeout kill → zero diagnostic). NOTE: (iii) is
  baked into the UTL base image at `/app/unified-trading-pm/scripts/quality-gates-base/base-service.sh`, so it does NOT
  reach THIS build — it is fleet-hardening for local + GitHub-Actions quality-gates-v2 + future UTL rebuilds; (i)+(ii)
  ARE COPY'd into the features-service image and DO reach CI, and are the load-bearing diagnostic. Chose to gate (ii) on
  `CLOUD_BUILD` only (not `CLOUD_BUILD or CI`) because GitHub-Actions quality-gates-v2 runs the FULL suite (not
  `--quick`, ~273s local here) which could legitimately exceed the 420s budget and false-fail — the Cloud Build target
  sets `CLOUD_BUILD=true` so the diagnostic goal is fully met; decide-and-document. Full
  `bash scripts/quality-gates.sh --no-fix` green in 273s (sentinel `.qg_last_passed_sha=78fd05d1...` == pre-commit
  HEAD). Shipped: features-service@`b4cae4eb` (`quickmerge.sh --agent --files 'pyproject.toml tests/conftest.py'`,
  landed on LDR); unified-trading-pm@`0148b6f34` (base-service.sh, PM `scripts/**` carve-out direct push). Re-triggered
  `gcloud builds triggers run features-service-build --branch=live-defi-rollout --region=asia-northeast1` → build
  `136fce13-69dd-4eac-bc5b-e9fe0251c524` (QUEUED against commit `b4cae4eb`, createTime 17:53:04Z). NOT watched here — a
  follow-on phase watches the build to SUCCESS-or-diagnosed-fast-fail. Todos 6-10 remain `[ ]`; no
  terraform/config/product-code changes this touch. See the matching entry in
  `plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md`.

- 2026-07-15 (~19:1x UTC): **CI hang ROOT-CAUSED + fixed.** Instrumented build `136fce13` failed fast with a
  thread-method stack dump pinpointing `tests/sports/unit/test_gcs_paths_and_reader_deps.py:138` →
  `_read_split_fixtures_fallback` → UTL `read_fixtures_joined` → `pd.read_parquet(gs://…)` → pyarrow `get_file_info`
  hang (native C++ GCS I/O pytest-socket can't block; hangs on a GCE worker with ambient ADC, fails fast locally — a
  unit-test hermeticity bug). Fix shipped `features-service@bd0db4d7` (mock the fixtures split-fallback so no unit test
  makes a real gs:// read; sweep-confirmed the only unit-level offender). Full QG green (278s). Rebuild triggered: build
  `fd73ca17-8d5a-435c-8ec6-9af11eb377fc` against `bd0db4d7` — being watched to SUCCESS. Once green + image push verified
  to carry UTL `c47273c1`, todo 5 (sports-job re-verify) unblocks; todos 6-10 follow. Full detail in
  `plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md`.

- 2026-07-15 (~19:53Z, VerifyImageDeploy phase — real evidence, not inference): Verified the fixed image AND corrected a
  latent Cloud-Run image-pinning trap that would have kept the job on the broken image even after the rebuild. **(1)
  Image verified in-container** (`docker run --rm --entrypoint python <img> -c ...`): `:latest` has moved PAST `bd0db4d`
  — a newer fleet rebuild `afbe1ef` (still `0.66.0`, built `2026-07-15T19:38:03Z`) now holds the `latest` tag at digest
  `sha256:b7fc3d7f7b92fe37edfae592b8c62244ecc46d5598dd4e08571508de08fb3117`. That digest docker-run-verifies to contain
  BOTH fixes: `import unified_trading_library.config_interface.auth.entitlements` succeeds (no
  `unified_api_contracts.internal` ModuleNotFoundError), and `inspect.getsource(assert_consolidator_healthy)` shows the
  UTL `c47273c1` lock-aware short-circuit
  (`from ... import consolidator_cycle_in_flight; if consolidator_cycle_in_flight(client, bucket): return`) — the exact
  mechanism that turns the `kk4dv` false `CONSOLIDATOR_DOWN` (heartbeat 208s > 120s while a legit long merge holds the
  lock) into a pass. **(2) Corrected the prior touch's `:latest`-auto-propagates assumption** (15:45Z entry: "the job's
  next execution picks up the fix with no further terraform/gcloud action needed"): Cloud Run resolves an image
  tag→digest at job **create/update** time, not per-execution. Proven:
  `gcloud run jobs executions describe features-service-sports-job-kk4dv` ran `@sha256:c204c49d…` (the stale 2026-07-14
  image), and `terraform state show` recorded the job image as the bare `:latest` tag — so a plain re-apply is a no-op
  and a new execution would have re-run the BROKEN c204c49d, silently. **(3) Re-pinned the job to the verified digest
  via terraform** (state-consistent path): set `terraform/services/features-service-sports/gcp/terraform.tfvars`
  `docker_image` to the explicit `@sha256:b7fc3d7f…` digest,
  `terraform plan -target=module.daily_job.google_cloud_run_v2_job.job` → `0 to add, 1 to change, 0 to destroy`
  (image-only, in-place), applied clean. Confirmed live: `gcloud run jobs describe features-service-sports-job` now
  shows `image = …@sha256:b7fc3d7f…` (generation 2); scheduler `features-service-sports-daily-trigger` still `PAUSED`
  (unchanged). Shipped `deployment-service@6c47fa1d` (`quickmerge --agent --files`, `quality-gates.sh --no-fix` green,
  sentinel==HEAD). **Todo 5 stays `[ ]`** — this phase did NOT run the verification execution (that is todo 5's Execute
  step); the image is now verified-fixed and the job points at it, so todo 5 is unblocked at the image/deploy boundary.
  Execution success still depends on the instruments-sports consolidator being genuinely healthy at run time (per the
  ~13:45Z audit it is — a ~7-8min real merge, not an indefinite livelock — and `c47273c1` now tolerates its in-flight
  lock), which todo 5 must prove by actually reaching `SUCCEEDED`. Added todo below re: the digest-pin now needing a
  re-pin on future features-service rollouts.
- 2026-07-15 (~19:00Z, ReverifyExecution phase, todo 5 — DONE, real evidence, not inference): Pre-flight confirmed the
  live job is digest-pinned to the verified `@sha256:b7fc3d7f…` (`command=["python","-m","features_service"]`; default
  args lack `--tables`/dates by design) and the scheduler is PAUSED. Triggered
  `gcloud run jobs execute features-service-sports-job --region=asia-northeast1 --project=central-element-323112` with
  the full-contract `--args` override
  (`--feature-family sports --operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date 2026-07-14 --end-date 2026-07-15`,
  same shape as `kk4dv`) → execution `features-service-sports-job-qsqs4`. Watched live on a 30s cadence (18:57→18:59Z)
  to a GENUINE terminal `SUCCEEDED`: `status.conditions[0]` = `Completed / True`, `succeededCount=1`, `failedCount=0`.
  **Both remaining gates PROVEN from logs + GCS, not assumed:** (1) the manifest-consolidator preflight NO LONGER
  false-fails —
  `sports batch startup gate: instruments-store consolidator healthy for sports (bucket=instruments-store-sports-prd-central-element-323112)`
  logged (passing) for BOTH run dates, with NO `CONSOLIDATOR_DOWN`/heartbeat-stale error; this is exactly the false-DOWN
  that killed `kk4dv`, now cleared by the in-image UTL `c47273c1` lock-aware short-circuit. (2) real feature output
  landed in the canonical bucket
  `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=<D>/league=<L>/feature_group=fixture_features/features.parquet`
  — `compute_fixture_features[2026-07-14]` wrote 14 rows across leagues 129/2(UCL)/848(UECL)/874 → 4 non-empty parquets
  (17,461 / 18,046 / 17,584 / 17,612 B) `mtime=2026-07-15T18:59:15Z`; `compute_fixture_features[2026-07-15]` wrote 3
  rows league 255(USL_CHAMPIONSHIP) → 1 parquet (18,359 B) `mtime=18:59:29Z`; `Processing completed successfully` +
  `[features-service] shutdown complete`. Object write-timestamps match the write-log lines exactly (fresh, not stale
  placeholders). Todo 5 flipped `[x]`. Scheduler left PAUSED (un-pause is todo 8 — deliberately not touched this touch).
  The features-service-sports deploy is now proven healthy end-to-end, which UNBLOCKS the previously-gated downstream
  todos: todo 6 (`--category`→`--asset-group` Workflow-YAML drift), todo 7 (retire the legacy
  `features-sports-service-job` + its trigger), todo 8 (re-enable + verify one real scheduled fire), then todos 9-10
  (bucket delete + issue-doc closure). No terraform/config/code changes this touch (the job/image were already correctly
  deployed by the prior VerifyImageDeploy phase); this plan edit is the only change, shipped docs-only via the PM
  `docs(plans):` carve-out.
- 2026-07-15 (~19:18Z, DriftRetireReenable phase, todos 6-8 — real evidence, not inference). Reverify handed off
  `manualExecutionSucceeded=true` (execution `qsqs4` SUCCEEDED); independently re-verified live
  (`gcloud run jobs executions describe features-service-sports-job-qsqs4` → `Completed/True`, `succeededCount=1`)
  before proceeding, then executed the phase. **Todo 6 (`--category`→`--asset-group` Workflow drift): SATISFIED,
  verified no-op.** The drift lives ONLY in the LEGACY workflows (`features-sports-service-daily` line 36 =
  `--category`, `features-sports-service-backfill` line 15 = `--category`, confirmed via `gcloud workflows describe`);
  the NEW job's workflows already carry `--asset-group` in both terraform code and live, and `terraform plan` on
  `terraform/services/features-service-sports/gcp` = zero infra drift (only a benign output refresh). The legacy
  `--category` workflows are destroyed with the legacy job (todo 7), so no separate apply is required. **Todo 8
  (re-enable scheduling + verify a real scheduled fire): DONE end-to-end.**
  `gcloud scheduler jobs resume features-service-sports-daily-trigger` → ENABLED; `gcloud scheduler jobs run …`
  (19:13:56Z) → workflow execution `05bd100d-848d-4142-8fcc-699987f7a79c` → `SUCCEEDED` (computed window
  start=2026-07-14 / end=2026-07-22); spawned job execution `features-service-sports-job-6tm9w` → `Completed/True`,
  `succeededCount=1`, `failedCount=0`; consolidator preflight healthy on every date (no `CONSOLIDATOR_DOWN`); real
  features computed across T-1..T+7 (07-18: 55, 07-19: 28, 07-20: 1, 07-21: 14, 07-22: 19 fixtures); fresh non-empty
  parquet in `gs://features-sports-prd-central-element-323112/…/day=2026-07-18/…/features.parquet` written 19:16:03-04Z.
  Scheduler left ENABLED on this verified-healthy state. **Todo 7 (retire legacy job): DEFERRED — a real new dependency
  was discovered.** `configs/sports-trigger-tiers.yaml` (lines 189, 248) still dispatches the per-fixture Tier-3/4
  sports feature triggers (`features_pre_match`, `features_post_match`) to `features-sports-service-job`; retiring the
  legacy job now would break those live dispatches ("job not found"). Repointing them to the new job is NOT a simple
  YAML name-swap — the consolidated image needs a `--feature-family sports` prefix that the dispatch path
  (`deployment_service/sports_trigger_scheduler.py::_build_cli_cmd`) does not currently emit, so a dispatch-code change
  is required first. Filed as a new P1 prerequisite todo above; the legacy job is left in place. The double-fire risk
  todo 7 guards against is fully mitigated meanwhile: the legacy daily scheduler `features-sports-service-daily-trigger`
  stays PAUSED (same `0 7 * * *` slot). The separately-noted `uts-prod-features-sports-t1-schedule` /
  `features-sports-service-t1-recon` was re-checked — it targets `uts-prod-features-sports-service-t1-recon`, a
  never-existent job (per `t1_batch_scheduler.tf` comment, lines 73-74), NOT the legacy daily job, so it needs no action
  here (dead + already PAUSED). No terraform/code changes this touch; this plan edit is the only change, shipped
  docs-only via the PM `docs(plans):` carve-out.
- 2026-07-15 (FinishBucketAndDocs phase, todos 9-10 — FINAL, real evidence, not inference). Gate re-verified live before
  any destructive action: `features-service-sports-daily-trigger` = `ENABLED`, the last scheduled fire's job execution
  `SUCCEEDED` — so `schedulingReenabled` + `realScheduledFireSucceeded` both hold; proceeded. **Todo 9 (bucket delete):
  DONE.** Re-confirmed `gs://features-sports-central-element-323112` held exactly the expected 3 live objects (1
  migrated `sports_features/…/day=2020-01-01/…/sfi_progressive.parquet` + 2 ephemeral `_vm_staging/fss_backfill/*`); 39
  all-version rows collapse to those same 3 logical paths (no hidden data); verified the migrated object present +
  intact (25,989 B) in the canonical `gs://features-sports-prd-central-element-323112` first.
  `tofu state rm google_storage_bucket.features_sports` on the PROD state (**note: the live prod resources live at
  backend prefix `terraform/state/prod`, NOT the `terraform/state/dev` default hardcoded in `main.tf`'s backend block —
  init with `-backend-config="prefix=terraform/state/prod"`; the `dev` prefix is a near-empty 11-entry state**) →
  "Successfully removed 1 resource instance(s)"; canonical `google_storage_bucket.canonical["features-sports-prd-…"]`
  confirmed still in state (untouched). Removed the resource block from `deployment-service/terraform/gcp/main.tf` + the
  now-orphan import block from `_imports_reconcile.tf` (both → REMOVED comments, mirroring the features-calendar
  precedent so a future apply cannot resurrect the bucket / error on a dangling import target); `tofu validate` clean.
  Shipped `deployment-service@bfea7928` (`quickmerge --agent --files`, `quality-gates.sh --no-fix` green in 65s,
  sentinel==HEAD). **Multi-agent note:** `main.tf` carried a concurrent FOREIGN soft-delete/versioning WIP (a different
  workstream: `instruments_cefi`/`instruments_sports`/`market_data_sports`,
  `deployment_scripts_bucket_softdelete_log_churn`); isolated it via `git stash push -- terraform/gcp/main.tf` so ONLY
  my features_sports-removal hunk landed, then `git stash pop` restored it byte-for-byte (verified: 34+/17- across
  exactly those 3 blocks, zero features_sports in the residual diff) — the foreign WIP was neither shipped nor
  clobbered. Physical delete: `gcloud storage rm --recursive --all-versions --continue-on-error` (all objects +
  noncurrent versions → empty) then `gcloud storage buckets delete --quiet`; `buckets describe` → `404 not found`.
  Canonical bucket + migrated object re-verified alive post-delete. **Todo 10 (docs closure): DONE.** Flipped all 4
  related issue docs to `status: resolved` + Resolution sections + `resolved_by` provenance:
  `features_sports_service_cloud_run_job_broken_image_2026_07_15.md` (Path B deploy complete + proven),
  `features_service_cloud_build_quality_gates_hang_2026_07_15.md` (root cause = a unit-test `gs://` hermeticity bug in
  `tests/sports/unit/test_gcs_paths_and_reader_deps.py`, NOT xdist/memory; fixed `features-service@bd0db4d7`, green
  build `fd73ca17-8d5a-435c-8ec6-9af11eb377fc`), `instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`
  (closed as a MISDIAGNOSIS of its already-root-caused sibling — a legit ~7-8min real merge, not a livelock), and
  `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md` (the durable root-cause record; both
  fixed by UTL `c47273c1`, now deployed + proven via the scheduled fire's zero-`CONSOLIDATOR_DOWN`). Appended a closing
  entry to `bucket_estate_consolidation_to_sub100_2026_07_13.md` and annotated
  `plans/archive/features_repo_consolidation_2026_05_08.plan.md` that the deploy-side gap is now closed. Flipped todos 9
  - 10 → `[x]` above. **Remaining open (deliberate, tracked — NOT this phase's scope):** todo 7 (retire the legacy
    `features-sports-service-job`) stays deferred behind its P1 prerequisite — the `configs/sports-trigger-tiers.yaml`
    Tier-3/4 per-fixture triggers still dispatch to the legacy job and need a `--feature-family sports` dispatch-code
    change in `deployment_service/sports_trigger_scheduler.py::_build_cli_cmd` before repointing; double-fire risk fully
    mitigated by the legacy daily scheduler staying PAUSED. Two P2 terraform-hygiene follow-ups (job `args` default
    dates; re-pin `docker_image` digest on next rollout) + the P3 optional fleet-skew audit also remain. Plan shipped
    docs-only via the PM `docs(plans):` carve-out; the only CODE change this phase was the terraform removal
    (`deployment-service@bfea7928`).
- 2026-07-15 (RepointDispatch phase — the todo-7 prerequisite; real evidence, not inference). Cleared the last blocking
  dependency on retiring the legacy `features-sports-service-job`: the per-fixture Tier-3/4 sports-feature triggers now
  dispatch to the consolidated `features-service-sports-job`, and the new job is PROVEN to accept the exact per-fixture
  shape. **Dispatch-code fix (the real prerequisite):** `deployment_service/sports_trigger_scheduler.py::_build_cli_cmd`
  now prepends `--feature-family <asset_group.lower()>` (→ `sports`) for the consolidated features-service, gated by a
  new module-level `_MULTI_FAMILY_DISPATCH_SERVICES = frozenset({"features-service"})` — family/service-aware, NOT an
  always-emit, because `_build_cli_cmd` is SHARED with the single-family instruments-service (Tier-1/2) and MTDS
  (Tier-3) dispatches, which must NOT receive the flag (2 new regression tests lock both directions). The prefix sits
  right after `python -m features_service` so `_strip_python_module_prefix` (drops only the `python -m <module>` head)
  preserves it as the leading Cloud Run args-override arg the multi-family dispatcher `features_service/cli/main.py`
  requires. **YAML repoint:** both `features-service` entries in `configs/sports-trigger-tiers.yaml`
  (`features_pre_match` `--tables fixture_features,odds_features`; `features_post_match` `--tables derived_features`)
  `cloud_run_job_name` → `features-service-sports-job` (+ stale header-comment reference refreshed). Shipped
  `deployment-service@9ec1c3bef2330fe4fa53a38eefde634d66b996b4` (quickmerge `--agent --files`,
  `quality-gates.sh --no-fix` green 59s, sentinel==HEAD; the concurrent foreign soft-delete WIP in
  `terraform/gcp/main.tf` was left untouched — not staged, not shipped). **Runtime PROOF (real production dispatch path,
  start==end single fixture date 2026-07-14):** drove the exact live chain
  `_build_cli_cmd → _strip_python_module_prefix → CloudRunBackend.deploy_shard` (the same code a per-fixture trigger
  runs — gcloud's `--args` ArgList rejects the duplicate `--start-date`/`--end-date` value, but the real API path passes
  args as a list so it is the faithful proof) for BOTH tiers: pre_match override
  `--feature-family sports --operation compute --mode batch --asset-group SPORTS --start-date 2026-07-14 --end-date 2026-07-14 --run-tag live --tables fixture_features,odds_features`
  → execution `features-service-sports-job-trb5m` → genuine terminal `Completed/True` `succeededCount=1` ("completed
  successfully in 1m0.9s"), logs `instruments-store consolidator healthy` + `market-data consolidator healthy` (no
  `CONSOLIDATOR_DOWN`), `fixture_features` computed, `odds_features` honestly confirmed-empty (no upstream MTDS odds for
  the date), `Processing completed successfully`; post_match override `… --tables derived_features` → execution
  `features-service-sports-job-slz8z` → genuine terminal `Completed/True` `succeededCount=1` ("completed successfully in
  4m21.06s"), `Wrote derived_features: 14 total rows across leagues` (129/2·UCL/848·UECL/874),
  `Processing completed successfully` (the `recovery=skip` all-NaN data_quality warnings are a
  reference-data-completeness note for that date's leagues, not a dispatch/exit failure). **`readyToRetire=true`** —
  todo 7 (retire the legacy job + its already-PAUSED scheduler) is now unblocked and safe (nothing live dispatches to
  the legacy job). Did NOT perform the legacy-job retirement itself this phase (destructive `terraform state rm` +
  delete on the `services/features-sports-service` state prefix — the retirement phase's scope); flipped the repoint
  prerequisite todo `[x]` and annotated todo 7 with the unblock. This plan edit is docs-only via the PM `docs(plans):`
  carve-out.
- 2026-07-15 (VerifyAndRetire phase — FINAL functional item; real evidence, not inference). Verified `readyToRetire`
  live (not just trusted the handoff), then retired the legacy `features-sports-service-job` end-to-end. **Re-confirmed
  no live reference to the legacy job first:** repo grep for `features-sports-service-job` returned only comments + the
  legacy dir's own vars; the two `configs/sports-trigger-tiers.yaml` per-fixture entries (`features_pre_match`,
  `features_post_match`) both dispatch to `features-service-sports-job`; `gcloud scheduler jobs list` showed the only
  ENABLED `0 7 * * *` daily trigger is the NEW `features-service-sports-daily-trigger`, while the legacy
  `features-sports-service-daily-trigger` was PAUSED (no double-fire). **Retirement (state-rm-before-delete, mirroring
  the features-calendar / features-onchain precedent):** `tofu state rm` all 4 legacy resources
  (`module.daily_job.google_cloud_run_v2_job.job`, `module.daily_workflow.google_cloud_scheduler_job.trigger[0]`,
  `module.daily_workflow.google_workflows_workflow.workflow`,
  `module.backfill_workflow.google_workflows_workflow.workflow`; state prefix `services/features-sports-service`) →
  "Successfully removed 4 resource instance(s)", state now empty; then
  `gcloud run jobs delete features-sports-service-job` +
  `gcloud scheduler jobs delete features-sports-service-daily-trigger` +
  `gcloud workflows delete features-sports-service-{daily,backfill}` — every subsequent `describe` returns **NOT_FOUND
  (404)**, all four confirmed gone. Removed the whole legacy terraform dir `terraform/services/features-sports-service/`
  (gcp + the dead never-deployed aws scaffold — its S3 backend was a commented-out placeholder) so a blind apply cannot
  resurrect it, and refreshed the now-stale legacy cross-reference comments in the consolidated job's `main.tf`.
  Post-delete re-verified the NEW job (generation 3, digest-pinned @sha256:b7fc3d7f), the NEW scheduler (ENABLED), and
  both NEW workflows (`features-service-sports-daily`/`-backfill`, ACTIVE) are all intact/healthy. **Also handled the P2
  job-args default-dates hygiene fix (todo P2, shipped in the same commit):** appended
  `--date 2026-07-14 --tables fixture_features` (a fixed, immutable historical fixture date proven non-empty per todo 5
  — `--date` is the parser's single-date form, no relative token exists) to the consolidated job's default `args` so a
  bare `gcloud run jobs execute` passes CLI date-validation with a deterministic non-empty smoke result; applied
  in-place (`tofu apply -target`, `0 add / 1 change / 0 destroy`, image UNCHANGED, gen 3), live args verified so code ==
  live (no drift). Shipped `deployment-service@f2ced5a8a7162374c974e622ff803c8ad91ac4c8` (`quickmerge --agent --files` —
  the 9 legacy-dir deletions + the consolidated `main.tf` edit; `quality-gates.sh --no-fix` green 59s, sentinel==HEAD;
  landed on `origin/live-defi-rollout`, verified ancestor). **Multi-agent safety:** the concurrent FOREIGN
  soft-delete/versioning WIP in `terraform/gcp/main.tf` was left untouched throughout — never staged (scoped `--files`
  by name), never shipped, still dirty in the worktree; a `.terraform.lock.hcl` registry-source churn my `tofu init`
  introduced was `git checkout`-restored so only the retirement hunks landed. This plan edit (todo-7 + P2 flips + this
  entry) is docs-only via the PM `docs(plans):` carve-out. **PLAN STATE:** all critical-path + functional deliverables
  are now COMPLETE — the consolidated `features-service-sports-job` is live/healthy (manual `qsqs4` + scheduled `6tm9w`
  both SUCCEEDED), scheduling ENABLED + a real scheduled fire proven, the `features-sports` bare bucket deleted, all 4
  issue docs closed, and the legacy job/scheduler/workflows retired (404-confirmed). Only two non-blocking items remain,
  both intentionally left `[ ]`: the P2 `docker_image` digest re-pin (a CONDITIONAL-FUTURE action that only fires on the
  NEXT features-service image rollout — not actionable now, the job is correctly pinned to the current verified digest)
  and the P3 fleet-skew audit (explicitly optional stretch). Plan kept `status: active` as a tracking vehicle for those
  two; nothing blocks it.
- 2026-07-15 (FixDigestPin phase — footgun B, operator-directed): Designed + verified (read-only) the permanent fix for
  the P2 re-pin footgun so future rollouts never need a manual digest re-pin. CONVENTION CHOSEN: the fleet-standard
  post-push `gcloud run jobs update <job> --image=…:latest` auto-repin step in the service's OWN cloudbuild.yaml (three
  precedents: `deployment-service/cloudbuild.yaml` id `redeploy-monitor-jobs`,
  `deployment-service/cloud-build/deployment-service-jobs-image.cloudbuild.yaml` id `redeploy-jobs`,
  `deployment-service/scripts/cloud-run/deploy-shared.sh` rollup sync) — this is EXACTLY the "_Alternative if the
  operator prefers tag-tracking_" spelled out in the P2 todo above, and it removes the footgun rather than replacing a
  manual step (digest re-pin) with another manual step. Two edits made (both a MATCHED PAIR): (1)
  `features-service/cloudbuild.yaml` — new `redeploy-features-jobs` step re-pins `features-service-sports-job` to the
  freshly-built `:latest` on every build; (2) `terraform/services/features-service-sports/gcp/terraform.tfvars` —
  `docker_image` flipped `@sha256:b7fc3d7f…` → `:latest` (matches every other service tfvars). Verified read-only:
  `features-service:latest` resolves to `sha256:b7fc3d7f…` — the EXACT pinned digest (so the flip is behavior-neutral
  today); the job exists on that digest; cloudbuild.yaml yaml-parses; prettier + `tofu fmt` clean; **deployment-service
  QG green** (sentinel `0c3fb77`). NOT SHIPPED — BLOCKED: `features-service` `live-defi-rollout` (HEAD==origin
  `d695c06b`) is RED on a pre-existing, unrelated sports coverage-gate test
  (`tests/sports/unit/test_run_new_calculators_coverage_gate.py::…::test_squad_value_pre_launch_is_out_of_coverage`,
  `'partial' != 'out_of_coverage'`; features-service `quality-gates-v2` CI FAILED 5 of last 6 runs →
  flaky/data-dependent; my only diff is `cloudbuild.yaml`, never imported by pytest) → no green local sentinel →
  `quickmerge` refuses; and the tfvars `:latest` half MUST NOT ship alone (it recreates the footgun). Not fixing the
  sports test here (out of scope, collision risk, could mask a real coverage regression). Blocker + ready-to-ship fix
  filed: `plans/active/issues/features_service_red_tree_blocks_digest_pin_fix_2026_07_15.md`. P2 re-pin todo
  intentionally LEFT `[ ]` (honest: the fix is prepared + verified but NOT shipped — flip it green only after both files
  land, with the two shas).
- 2026-07-15 (FixStatePrefixTrap phase — footgun C, operator-directed): Removed the `deployment-service/terraform/gcp`
  invocation trap. **Two real footguns confirmed by evidence:** (1) `main.tf`'s `backend "gcs"` block hardcodes
  `prefix = "terraform/state/dev"` (backend blocks can't interpolate vars) — but the live prod estate (~198 resources)
  lives under `terraform/state/prod`; `dev` is a near-empty ~11-entry state, so a bare `tofu init && apply` silently
  targets the wrong env (verified: `.terraform/terraform.tfstate` backend cache currently shows
  `prefix: terraform/state/prod`, and `scripts/bootstrap/bootstrap_gcp.sh` already passes
  `-backend-config=prefix=terraform/state/${ENV}` with a required `--env` — so the OFFICIAL bootstrap path is safe, but
  a direct `tofu`/`terraform` call is not). (2) The dir is **OpenTofu** — the git-tracked `.terraform.lock.hcl` pins
  providers from `registry.opentofu.org` (confirmed `git show HEAD:...lock.hcl`), so running the `terraform` binary here
  rewrites those provider sources to `registry.terraform.io` (HashiCorp) — a committable regression (this exact churn
  already bit the FixDigestPin phase's `tofu init` and had to be `git checkout`-restored). **FIX (PREFERRED wrapper+doc,
  non-colliding — main.tf was carrying concurrent foreign soft-delete/versioning WIP so it was NOT touched):** added
  `deployment-service/terraform/gcp/tofu.sh` — a wrapper that REQUIRES an explicit `ENV` (dev|staging|prod) or leading
  positional and refuses without it (exit 2), maps `ENV` → `-backend-config=prefix=terraform/state/<env>` + `bucket` +
  `-reconfigure` on `init`, injects the required tofu vars (`project_id`/`region`/`environment`/`bucket_prefix`) via
  `TF_VAR_*`, invokes `tofu` and HARD-FAILS if the binary is absent (exit 3 — never falls back to `terraform`), and
  carries a cross-invocation guard that reads the cached backend prefix and refuses a `plan`/`apply` whose `ENV`
  disagrees with the last `init` (exit 4). **Verified (dry, no live-infra mutation):** shellcheck CLEAN; exercised all
  four refusal paths (no-ENV→2, bad-ENV→2, ENV=dev-vs-cached-prod→4) and the init/positional/pass-through dispatch via a
  fake `tofu` shim on PATH (correct `-backend-config` bucket+prefix+reconfigure emitted). **SHIPPED:** wrapper
  `deployment-service@dea0e2c7d13b0475244b0fc1e6ff73bee397dfe3` (`quality-gates.sh --no-fix` GREEN 99s, sentinel
  `0c3fb77`==HEAD; `quickmerge --agent --files 'terraform/gcp/tofu.sh'`; landed on `origin/live-defi-rollout`,
  ancestor-verified). The Fix-B tfvars `:latest` half was left held/dirty and NOT staged (still blocked on the
  features-service red tree). Codex runbook (both gotchas + owner/cadence/verifier/last_executed frontmatter):
  `/codex/05-infrastructure/deployment-service-gcp-tofu-state.md`. **DEFERRED (small tracked follow-up):** hardening the
  `main.tf` backend-block default itself (fail-loud, or correct to prod) — deferred because main.tf was contested by
  foreign WIP at fix time and the wrapper removes the trap for the normal path; recorded in the codex runbook's
  Footgun-1 follow-up note. Docs-only via the PM `docs(...)` carve-out.
- 2026-07-15 (ReportAndFile phase — P3 fleet-skew audit CLOSED, read-only, DOCS-ONLY): Flipped todo P3 to
  done-with-findings. Audited the whole fleet for the same UTL/UAC `unified_api_contracts.internal` import-skew that
  killed features-sports-service: 149 UTL/UAC-bearing Cloud Run deployments (24 services + 125 jobs, 7 regions; VMs out
  of scope). 17 in-window suspects flagged (11 `uts-prod-mtds-collect-*` DeFi/onchain collectors + 6
  `uts-prod-manifest-consolidator-*`); each docker-tested against its EXACT deployed digest via
  `docker run --entrypoint python <img@digest> -c "import unified_trading_library.config_interface.auth.entitlements"`.
  **RESULT: ZERO other broken deployments — features-sports-service was the ONLY casualty.** 16/17 printed IMPORT_OK
  exit 0; the 17th (`market-data-tradfi` consolidator) is HEALTHY-by-parity (identical fresh `:latest` digest
  `6b3dbf5e` + entrypoint family as 2 clean-tested siblings running `*/1` successfully). Decisive structural reason the
  in-window heuristic over-flagged: MTDS-family images vendor UAC from SOURCE at `/app/.deps/unified-api-contracts/`,
  which already contains the `internal/` package, so the broken-published-wheel failure mode structurally cannot
  reproduce for them (the version-label `0.1.20` is the source checkout's label, not the internal-less PyPI wheel);
  additionally Cloud Run jobs re-resolve `:latest` per execution and self-heal on the fresh post-fix image. Two SEPARATE
  non-bug operational findings surfaced and were recorded for their own triage: (a) ~37-day paused DeFi/onchain
  data-collection gap across the 11 mtds-collect crons (their ~06-08 failures have a different, unrelated cause — logs
  past 30-day retention); (b) Group-C jobs failing TODAY on FRESH post-06-09 images (data/config, not the import skew).
  Full per-deployment table, per-suspect verdicts, and the generic per-broken remediation recipe
  (rebuild-via-Cloud-Build-trigger + runtime import verify + redeploy/re-pin, incl. the archived-repo caveat that
  features-sports hit) filed at
  [`plans/active/issues/utl_uac_skew_fleet_audit_2026_07_15.md`](issues/utl_uac_skew_fleet_audit_2026_07_15.md).
  READ-ONLY throughout — no service/job/image/scheduler modified.

## Deferred work — migrated to:

**This plan itself (self-resolved, same plan)** — the sole hit (line ~713, "Todo 7 (retire legacy job): DEFERRED — a
real new dependency was discovered") described a temporary blocker on retiring `features-sports-service-job`: the
`configs/sports-trigger-tiers.yaml` Tier-3/4 per-fixture triggers still dispatched to the legacy job, and
`deployment_service/sports_trigger_scheduler.py::_build_cli_cmd` did not yet emit the required `--feature-family sports`
prefix. A new P1 prerequisite todo was filed inline (same plan) to fix the dispatch code first. That prerequisite was
subsequently cleared and proven in the RepointDispatch phase (progress-log entries ~line 767-799): `_build_cli_cmd` now
injects `--feature-family sports`, both `sports-trigger-tiers.yaml` per-fixture entries were repointed and verified
SUCCEEDED against the new job, and Todo 7 (retire the legacy job) is now `[x]` DONE. No external successor plan was
needed — the deferral was fully closed within this same plan.
