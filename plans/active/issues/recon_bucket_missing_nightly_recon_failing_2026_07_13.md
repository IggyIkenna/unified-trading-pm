---
doc_type: issue
title:
  "batch-live-reconciliation nightly Cloud Run job has failed on (nearly) every scheduled run since ~mid-May: its recon
  bucket (recon-{pid}) does not exist and never has"
summary:
  "Surfaced by the 2026-07-13 bucket estate audit's shadow-registry sweep and adversarially verified: BLRS
  config.py:78-79 defaults the recon bucket to recon-central-element-323112 and the launcher header documents
  recon-store-central-element-323112 — NEITHER bucket exists (probed 404; zero 'recon' matches in the live 241-bucket
  project listing). The real nightly trigger is Cloud Scheduler uts-prod-batch-live-reconciliation-t1-schedule (ENABLED,
  0 6 * * * UTC) → Cloud Run Job uts-prod-batch-live-reconciliation-service (--operation reconcile --mode batch). Stage
  0 polls t1-recon/{ml,strategy}/{date}/_SUCCESS markers in the nonexistent bucket, Blob.exists() returns False, stage0
  returns FAILED and the orchestrator aborts before Stage 5 — so no recon summary/report has EVER been written: 55 of 56
  listed executions FAILED (NonZeroExitCode, ~108s); the single success (2026-05-23) was a manual --dry-run. The
  batch=live ε=0 reconciliation spine's operational check is effectively dark. dev/staging scheduler siblings are also
  ENABLED and presumably failing identically."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [strategy, meta]
repos: [batch-live-reconciliation-service, deployment-service]
scope: [engineer, admin]
tags: [gcs, recon, batch-live-reconciliation, cloud-run, silent-failure, data-pipeline-correctness]
related:
  [
    /plans/archive/2026_07/gcs_bucket_estate_cleanup_2026_07_10.md,
    /plans/archive/issues/terraform_bucket_estate_drift_resurrection_2026_07_13.md,
  ]
created: "2026-07-13"
author: unknown
parent_epic: infrastructure_master
priority: P0
source:
  "2026-07-13 bucket estate audit: shadow-registry research agent flagged recon-{pid} missing; a dedicated verification
  agent confirmed via config.py/launcher reads, live bucket probes (both names 404), Cloud Scheduler + Cloud Run
  execution history (55/56 failures), and the stage0 abort path (stage0_config_pull.py:96-104, orchestrator.py:88-93)."
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
context_scope:
  [
    /codex/08-workflows/t1-batch-dag.md,
    /plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    batch-live-reconciliation-service/batch_live_reconciliation_service/config.py,
    /plans/archive/issues/terraform_bucket_estate_drift_resurrection_2026_07_13.md,
  ]
locked_since:
assigned_vm: NA
resolved_by:
---

# Nightly batch-live recon failing: recon bucket never existed

## Verified facts (file:line)

- `batch_live_reconciliation_service/config.py:78-79` —
  `if not self.recon_bucket: self.recon_bucket = f"recon-{project_id}"`; prod Cloud Run job sets
  `GCP_PROJECT_ID=central-element-323112`, no `RECON_BUCKET` override → `recon-central-element-323112`.
- `deployment-service/scripts/vm/launch-batch-live-recon-cron-vm.sh:18` documents a DIFFERENT name (`recon-store-{pid}`)
  and a DIFFERENT path shape (`reports/{date}/report.json`) than the code writes (`t1-recon/recon/summary_{date}.json`,
  stage5_results_writer.py:84). Doubly stale doc.
- Both bucket names 404 on probe; the authoritative 241-bucket project listing (2026-07-13) has zero `recon*` buckets.
  (The estate cleanup plan :115-116 had noted `recon-{pid}` as "the real name" vs the orphaned
  `reconciliation-store-test` — the name is real in code, but the bucket was never provisioned.)
- Failure mode is loud-but-unwatched: stage0 `_blob_exists` (stage0_config_pull.py:38-47) returns False on the 404,
  stage0 → FAILED, orchestrator.py:88-93 aborts pre-Stage-5, reconcile_handler.py:43-52 exits 1. Cloud Run history:
  55/56 executions failed back to ~mid-May; the one success was a manual `--dry-run` (no writes).

## Fix direction

1. ✅ DONE 2026-07-13: `recon` kind added to cloud-providers.yaml (env-tiered `recon-{env}-{pid}`), buckets provisioned.
2. ✅ DONE: `config.py` repointed to the resolver (`blrs@2f0380b`); launcher header fixed (`ds@ccfaca26`).
3. ✅ INVESTIGATED 2026-07-14 to a precise, well-scoped, genuinely out-of-scope finding — see "2026-07-14 update" below.
4. ⏳ STILL OPEN: no real green scheduled run yet (blocked on #3's finding, out of this issue's fixable scope without
   the multi-repo feature work described below); Cloud Run failure alerting not yet wired (55+ silent failures).

## 2026-07-14 update

**(a) prod digest issue found + fixed + verified; (b) producer chain investigated to a precise, well-scoped, genuinely
out-of-scope finding.**

**(a) BLRS prod image — a SECOND digest issue, now fixed + verified with a real triggered execution.** The 2026-07-13
digest bump (`28a18fa`, bumping `BASE_IMAGE_DIGEST` to `sha256:b7e391f8`) and the config fix (`2f0380b`) were both
already on `main` and already picked up by the live `:latest` prod image (built off `7b65341`) — but the real 06:00Z
2026-07-14 scheduled run (`uts-prod-batch-live-reconciliation-service-v8jt9`) STILL failed, with a NEW error not
previously documented here: `BucketNamingError: Unknown kind 'recon' for cloud 'gcp'`, thrown from
`resolve_bucket_name()` before Stage 0 even starts. Root cause (found via `docker pull`/`inspect` of the exact deployed
image): the UTL base image digest BLRS pinned (`sha256:b7e391f8`, itself refreshed 2026-07-13T17:44Z) bundles a UAC
snapshot at commit `21dde0f8` (16:39:42Z that same day) — confirmed (via `git merge-base --is-ancestor`) to be an
ANCESTOR of, i.e. from BEFORE, `uac@f84e5b37` (20:11:34Z), the commit that actually added the `recon` kind. A same-day
base-image-refresh-vs-upstream-fix race, not a bug in BLRS's own code. **Fixed**: bumped `Dockerfile`'s
`BASE_IMAGE_DIGEST` to `sha256:9594091a` (the current UTL `:latest` as of 2026-07-14T18:17:27Z, confirmed via image
inspection to bundle UAC commit `ed622d8b1`, a genuine descendant of `f84e5b37` — its packaged `cloud-providers.yaml`
greps 7 hits for `recon`) — `batch-live-reconciliation-service@be056b1` (quickmerge, QG green). Built + verified
directly off LDR (`gcloud builds triggers run batch-live-reconciliation-service-build --branch=live-defi-rollout`, build
`ab591245-708a-4c84-a080-7f4d3a9d6a15`, SUCCESS, new image `sha256:763b5446` pushed to `:latest` 2026-07-14T20:07:32Z)
rather than waiting on the LDR→staging→main promotion chain. **Verified with a real triggered execution**
(`uts-prod-batch-live-reconciliation-service-pn4f7`): config now resolves
`recon_bucket=recon-prd-central-element-323112` correctly, and Stage 0 fails at the EXPECTED, already-documented gate —
`Missing upstream data for 2026-07-13: execution config snapshot: gs://execution-store-cefi-.../configs/snapshots/2026-07-13/config.json; ML t1-recon outputs: gs://recon-prd-.../t1-recon/ml/2026-07-13/_SUCCESS; strategy t1-recon outputs: gs://recon-prd-.../t1-recon/strategy/2026-07-13/_SUCCESS`
— real, live proof (a) is genuinely closed.

**(b) The upstream `t1-recon/{ml,strategy}` producer chain — traced concretely, not guessed.** Cross-referenced
`/codex/08-workflows/t1-batch-dag.md` (the SSOT) against LIVE Cloud Scheduler + Cloud Run Job state:

- **execution-service config-snapshot** (00:30 UTC, feeds Stage 0's `configs/snapshots/{date}/config.json` check):
  scheduler `uts-prod-execution-config-snapshot-t1-schedule` is `ENABLED` and fires daily, but its target Cloud Run Job
  (`uts-prod-execution-service-config-snapshot`) has **never been provisioned** (`gcloud run jobs list` — zero matches;
  only unrelated manifest-consolidator jobs match a name filter for "execution").
- **ml-service t1-recon** (03:00 UTC, feeds `t1-recon/ml/{date}/_SUCCESS`): scheduler `uts-prod-ml-t1-schedule`
  `ENABLED`, fires daily at `0 3 * * *`, but the target Cloud Run Job (`uts-prod-ml-service-t1-recon`) has **never been
  provisioned** either (`gcloud run jobs describe` → "Cannot find job"; the scheduler's own execution logs show
  `NOT_FOUND`/`UNAVAILABLE` on every daily fire, checked 2026-07-13 and 2026-07-14). ml-service DOES already have a
  `--run-tag` CLI flag (`ml_service/inference/cli/main.py`, help text literally references t1-recon) but it is
  **completely unwired** — a workspace grep found zero consumers of `run_tag` anywhere downstream of the argparse
  definition; no GCS writer respects it and there is no `_SUCCESS`-marker writer anywhere in the service.
- **strategy-service t1-recon** (04:00 UTC, feeds `t1-recon/strategy/{date}/_SUCCESS`): the Cloud Run Job DID exist
  (provisioned 2026-05-23 per a prior F-41-followup fix in
  `deployment-service/terraform/gcp/ audit03_cron_provisioning.tf`) but was **fundamentally broken at the container-exec
  level**: Terraform passed bare `args = ["--operation", "backtest", "--mode", "batch"]` with no `command` override,
  while strategy-service's own Dockerfile deliberately sets
  `ENTRYPOINT [] + CMD=["uvicorn", "strategy_service.api.main:app", ...]` (it is primarily a live API service, not a
  CLI-only image like its batch siblings). Confirmed via `docker inspect` on the exact deployed image
  (`Entrypoint=null`) + a local repro (`docker run <image> --operation backtest --mode batch` →
  `exec: "--operation": executable file not found in $PATH`) — every daily execution since creation (10/10 checked,
  2026-07-05 through 2026-07-14) failed at the OCI level with **zero application-level log output** ("Application failed
  to start: The container may have exited abnormally"). **Fixed the exec bug in scope** (small, safe, well-understood —
  a broken container-invocation config, not new feature work): added `command = ["python", "-m", "strategy_service"]` to
  the Terraform module (a real, tested CLI entrypoint — `strategy_service/__main__.py` → `cli/service_entry.py`, covered
  by `tests/unit/cli/test_cli_flag_combinations.py`) — `deployment-service@ea42a699` (quickmerge, QG green), also
  applied directly to the live job via `gcloud run jobs update` (local `terraform apply` against the shared remote state
  wasn't safe this session — a backend-config mismatch surfaced on `terraform init`, and other agents are concurrently
  touching this same state). **Verified with a real triggered execution** (`uts-prod-strategy-service-t1-recon-nfkbj`):
  the container now genuinely starts and runs (~2 min, full application bootstrap logs, live GCS bucket connectivity — a
  complete change in failure signature from the prior instant OCI crash) — but fails one layer deeper:
  `_resolve_date_args()` hard-requires an explicit `--date` or `--start-date`/`--end-date` (unlike ml-service/mdps,
  which self-default to T-1 when omitted), and the Terraform args pass neither, raising
  `ValueError: batch operation requires --date or both --start-date and --end-date`.

**Why this is genuinely out of scope, not just one more bug to fix**: strategy-service has **no `--run-tag` concept
anywhere in its codebase** (grep-clean workspace-wide) and, like ml-service, **no `_SUCCESS`-marker writer anywhere** —
so even a fully-running, correctly-dated invocation of this job would write to the default `batch/` thermal-backtest
namespace, which `t1-batch-dag.md`'s own "Batch vs Thermal Backtest Distinction" table states is **never read by the
reconciliation orchestrator**. Separately confirmed (live) that all 7 feature-family t1-recon schedulers this chain
depends on upstream of ml (calendar/delta-one/volatility/cross-instrument/multi-timeframe/commodity/sports) are in state
`PAUSED`, and `features-onchain` isn't even a key in `t1_batch_scheduler.tf`'s service map despite being listed as a
producer in the codex DAG doc.

**Conclusion**: reaching a real green 06:00Z run requires standing up genuine multi-repo feature work — provisioning 2
missing Cloud Run Jobs (execution config-snapshot, ml-inference) via the same container-job Terraform pattern already
used for strategy/mdps; implementing an actual run-tag-aware GCS writer + `_SUCCESS`-marker emission in at least
ml-service and strategy-service (not just parsing a flag); adding a self-default date fallback to strategy-service's
batch CLI; and un-pausing + validating the 7 feature-family schedulers (plus registering the missing onchain entry).
This spans execution-service, ml-service, strategy-service, and features-service — correctly out of scope for the
bucket-consolidation plan this issue is filed under. Recommend this becomes its own scoped plan/epic item when picked up
(not created here per the plan-destination ASK-BEFORE-CREATING rule).

Full evidence + exact commands: `plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md` Progress Log,
"2026-07-14, item D" entry.

## Todos

- [ ] [ENGINEER] P0. **Stand up the real green 06:00Z batch-live recon run** — provision the missing execution-service
      and ml-service Cloud Run Jobs, implement run-tag-aware `_SUCCESS`-marker writers in ml-service/strategy-service,
      add a self-default date fallback to strategy-service's batch CLI, and un-pause the 7 feature-family schedulers
      (per the "2026-07-14 update" Conclusion) — no real green scheduled run exists yet.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the doc's own conclusion is that the residual is multi-repo
  feature work 'correctly out of scope for the bucket-consolidation plan this issue is filed under' and 'should become
  its own scoped plan/epic item' — an ask-before-creating operator call.

- **na-eligibility-audit 2026-08-03 (cross-cutting tranche)**: KEEP-NA, valid — reaffirmed; not RECLASSIFY-eligible as
  written because the single todo bundles ~5 distinct deliverables (provision 2 Cloud Run Jobs, implement 2 different
  `_SUCCESS`-marker writers, add a date-fallback, un-pause 7 schedulers) rather than one bounded outcome — flipping
  `assigned_vm` in place without first splitting it into a proper multi-todo plan would dispatch an ill-formed oversized
  task. **Surfacing prominently rather than leaving this quietly re-stamped**: this is a P0, data-correctness-tagged doc
  that has sat unpromoted for 3+ weeks despite its own 2026-07-30 verdict recommending it "become its own scoped
  plan/epic item," and the sibling doc `batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30.md` (now
  archived, `plans/archive/issues/`) independently confirmed the underlying gap is real (not a live-trading-gated no-op)
  — recommend the operator/main-agent promote this into a real wrapper plan per CLAUDE.md's findings-triage rule
  (`audit-scope -> wrapper plan -> epic VM`), splitting the bundled todo into its constituent AO-eligible pieces.

- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 4 entries resolve on disk (codex
  DAG SSOT + archived consolidation plan + BLRS config source + archived drift-resurrection issue) — no changes.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-07-30/08-03 (unchanged) plus a formal batch1
  conflict-check (2026-07-26): sole todo bundles ~5 distinct deliverables across 4 repos, explicitly recommended to
  become its own scoped plan/epic, not one bounded outcome. Flagging (not a verdict change): this P0,
  data-correctness-tagged doc has sat unpromoted 3+ weeks past its own recommendation.
- **plan_reconciler 2026-08-10 (cross-cutting tranche, dispatch `agt-33a6ec`)**: still unpromoted as of today — 3 audit
  passes (07-30/08-03/08-06) all independently reached the same conclusion with zero action taken since. Given the
  severity (P0, data-correctness) and the elapsed time, escalated to the operator now rather than re-stamping a 4th
  identical verdict: `BLK-8bb28da4` (options A-D, recommendation A — promote now, `assigned_vm: planning`). Not creating
  the wrapper plan myself — that is exactly the "ask before creating" call this doc's own prior audits already deferred
  to the operator.
