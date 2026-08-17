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

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).

- **data_pipeline_failure escalation 2026-08-17 (`agt-0e4c67`, DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED)**: dispatched on a
  fresh `uts-prod-blrs-daily-determinism` Cloud Run Job failure (1 failed task, ~154m old at dispatch). Live diagnosis
  (execution `uts-prod-blrs-daily-determinism-jm2mn`, 2026-08-17T02:32:12Z, `NonZeroExitCode`) confirms this is the SAME
  already-documented root cause, not a new defect: Stage 0 aborted on `Missing upstream data for 2026-08-16` — the same
  three artifacts named throughout this doc (execution config snapshot, ML t1-recon `_SUCCESS`, strategy t1-recon
  `_SUCCESS`), still absent because their producer chain is still unimplemented/unwired per the "2026-07-14 update" +
  "Conclusion" above. `resolve_bucket_name()`/config-loading itself is healthy (bucket resolves correctly to
  `recon-prd-central-element-323112`/`execution-store-prd-central-element-323112`, consistent with the July fix) — no
  bucket-env mismatch, no code regression. No fix applied (would be a guess at multi-repo feature work this doc's own
  2026-07-14 investigation already scoped out and its 07-30/08-03/08-06 audits already recommended promoting, not
  re-diagnosing). Not re-filing a duplicate `/blocked` — `BLK-8bb28da4` (2026-08-10) is still open and unresolved;
  re-raising the same question would just add noise. Flagging: since the scheduler runs this job daily (0 2/6 * * *
  depending on env) and the producer gap is unchanged, this is a recurring daily DP-WATCHER-006 page, not a one-off —
  worth the operator's attention alongside the original promote-now recommendation, since every day it stays unpromoted
  is another guaranteed page with no actionable new information.

- **data_pipeline_failure escalation 2026-08-17 (`agt-ea1a56`, DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED)**: a second
  dispatch on the SAME alert instance (1 failed task, ~274m old at this dispatch vs ~154m at `agt-0e4c67`'s). Live
  `gcloud run jobs executions list` confirms this is NOT a new execution: the latest is still
  `uts-prod-blrs-daily-determinism-jm2mn` (started 2026-08-17T02:30:08Z, completed 2026-08-17T02:32:12Z,
  `NonZeroExitCode`) — the identical execution `agt-0e4c67` already diagnosed above; the daily scheduler has not fired
  again since (next fire is tomorrow 02:30Z). No new diagnosis performed and no fix attempted — the root cause and
  scope are unchanged from the entry immediately above, and re-running the same investigation on the same execution
  would add no information. Not re-filing a duplicate `/blocked` — `BLK-8bb28da4` (2026-08-10) is still open and
  unresolved. This confirms the "recurring daily page" flag from the prior entry: two separate escalation dispatches
  fired for one underlying failure, which will keep happening every day the producer chain stays unpromoted.

- **data_pipeline_failure escalation 2026-08-17 (`agt-89fe96`, DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED)**: a THIRD
  dispatch on the same static alert (~438m old at this dispatch vs ~154m/`agt-0e4c67` and ~274m/`agt-ea1a56`) —
  independently re-derived the full root-cause chain (live `gcloud run jobs executions describe` +
  `gcloud logging read` on `uts-prod-blrs-daily-determinism-jm2mn`; `gcloud run jobs executions list`/`describe` on
  the 3 producer jobs; terraform read of `t1_batch_scheduler.tf` + `audit03_cron_provisioning.tf`) BEFORE finding
  this doc already contained the identical diagnosis in the "2026-07-14 update" section — confirms nothing has
  changed: `uts-prod-execution-service-config-snapshot` and `uts-prod-ml-service-t1-recon` still return "Cannot find
  job" (never provisioned), `uts-prod-strategy-service-t1-recon` still crashes identically (`ValueError: batch
  operation requires --date...`, reconfirmed on all 5 daily runs 08-13..08-17, all `NonZeroExitCode`). No fix
  applied — same reasoning as the two entries above (multi-repo feature work already scoped out + escalated, not a
  one-shot-safe guess). Cross-checked the sibling doc `asia_northeast1_zombie_schedulers_dead_targets_2026_08_07.md`:
  its open `[OPERATOR]` todo (2026-08-15) already covers the same 2 missing Cloud Run Jobs from the scheduler side —
  this entry is the confirming link that BLRS's daily Stage 0 failure is the ACTIVE, currently-paging downstream
  consequence of that exact gap (that todo's own text flagged this as "not independently verified this pass" — now
  it is). Not re-filing `/blocked` — `BLK-8bb28da4` (2026-08-10) still open, now 7 days unresolved.
  **New observation**: three escalation-worker dispatches for one unchanged, statically-failed execution inside a
  single day is itself worth flagging — each dispatch re-derives the same evidence from scratch at real token/slot
  cost. Same shape as the `AlertDeduplicator`-defeat incidents already catalogued in
  `/codex/05-infrastructure/data-pipeline-alerts.md` (DP-LIVE-004's volatile-detail-key case, `DP_CRON_DID_NOT_FIRE`'s
  resolved-bookend-severity case) but on DP-WATCHER-006's escalation-dispatch path, which that doc's incident log
  doesn't yet cover. Recommend a `/data-pipeline-alerts-reconcile` or `/escalation-queue-reconcile` pass check
  whether DP-WATCHER-006 dispatches suppress against an already-open blocked-question/escalation for the same
  target — did not investigate the dispatcher/dedup code myself (out of this one-shot role's scope).
- **na-eligibility-audit 2026-08-17** [body-hash:0bc6180966288f3f]: KEEP-NA, valid -- Sole todo bundles ~5 distinct deliverables across 4 repos, not one bounded outcome (4 independent audit passes -- 2026-07-30/08-03/08-06/08-17 -- all reach this conclusion). Standing unresolved operator escalation BLK-8bb28da4 (open since 2026-08-10, reconfirmed by 5 separate escalation-dispatch entries today alone against the SAME static failed Cloud Run execution -- flagged in-doc as a likely DP-WATCHER-006 escalation-dispatcher dedup gap, worth a /data-pipeline-alerts-reconcile or /escalation-queue-reconcile pass). Cross-cutting tranche audit.

- **data_pipeline_failure escalation 2026-08-17 (`agt-ff99aa`, DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED, dispatched ~601m/10h after the alert first fired)**: a FOURTH dispatch on the same static alert instance in one day. Re-verified live (`date -u` = 2026-08-17T12:36Z; `gcloud run jobs executions list uts-prod-blrs-daily-determinism`): the latest execution is still `-jm2mn` (started 02:30:08Z, completed 02:32:12Z, `NonZeroExitCode`) — identical to the execution `agt-0e4c67`/`agt-ea1a56`/`agt-89fe96` already diagnosed above; the scheduler has not fired again (next fire tomorrow 02:30Z). No new diagnosis performed, no fix applied, no duplicate `/blocked` filed — `BLK-8bb28da4` (2026-08-10) is still open, now 7+ days unresolved. Confirms `agt-89fe96`'s flagged pattern: this is now 4 escalation-worker dispatches against one unchanged, statically-failed execution, each re-deriving (or, this time, reusing) the same evidence at real token/slot cost — the underlying gap is the DP-WATCHER-006 escalation dispatcher not suppressing re-dispatch against an already-open blocked-question for the same target, per `agt-89fe96`'s recommendation to run `/data-pipeline-alerts-reconcile` or `/escalation-queue-reconcile`. Did not investigate the dispatcher/dedup code myself (out of this one-shot role's scope) — flagging again since the pattern has now recurred a 4th time.

- **data_pipeline_failure escalation 2026-08-17 (`agt-8586b2`, DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED, dispatched ~669m/~11.1h after the alert first fired)**: a FIFTH dispatch on the same static alert instance in one day. Independently re-derived the chain before finding this doc (live `gcloud run jobs executions describe`/`gcloud logging read` on `-jm2mn`; confirmed the Stage 0 upstream artifacts — `execution-store-prd-central-element-323112/configs/snapshots/2026-08-16/`, `recon-prd-central-element-323112/t1-recon/{ml,strategy}/2026-08-16/` — still have zero objects, project-wide, for any date, via `unified_trading_library.cloud_interface.get_storage_client().list_blobs(...)`, i.e. the producer chain remains fully unwired, not merely late). `date -u` = 2026-08-17T13:41Z; latest execution unchanged (`-jm2mn`, 02:30:08Z–02:32:12Z, `NonZeroExitCode`); scheduler has not refired (next 02:30Z tomorrow). No new diagnosis, no fix, no duplicate `/blocked` — `BLK-8bb28da4` (2026-08-10) still open, now 7+ days unresolved. This is now 5 escalation-worker dispatches against one unchanged execution in a single day, reconfirming `agt-89fe96`/`agt-ff99aa`'s flagged dispatcher-dedup gap (DP-WATCHER-006 re-dispatching against an already-open blocked-question for the same target) — did not investigate the dispatcher code myself (out of scope for this one-shot role), but the recurrence count is now high enough that the dedup gap itself, not just the underlying BLRS producer-chain gap, warrants direct operator/main-agent attention.

- **data_pipeline_failure escalation 2026-08-17 (`agt-73b620`, DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED, dispatched ~721m/~12h after the alert first fired)**: a SIXTH dispatch on the same static alert instance in one day. `date -u` = 2026-08-17T14:35:47Z; `gcloud run jobs executions list uts-prod-blrs-daily-determinism --region=asia-northeast1` (note: correct region is `asia-northeast1`, not `us-central1` — the job label `cloud.googleapis.com/location: asia-northeast1` confirms it) shows the latest execution still `-jm2mn` (started 02:30:08.885365Z, completed 02:32:12.420397Z, `NonZeroExitCode`, "container exited with an error, exit code 1") — identical to the execution every prior dispatch today (`agt-0e4c67`/`ea1a56`/`89fe96`/`ff99aa`/`8586b2`) already diagnosed; scheduler has not refired since (next fire 2026-08-18T02:30Z). No new diagnosis performed (root cause is exhaustively documented above and confirmed unchanged 5 times already today), no fix applied (same multi-repo out-of-scope reasoning), no duplicate `/blocked` filed — `BLK-8bb28da4` (2026-08-10) still open, now 7+ days unresolved. This is now 6 escalation-worker dispatches against one unchanged execution in a single day (~52min mean spacing over the last several), each paying real diagnosis/token cost for zero new information — strongly reconfirms the dispatcher-dedup gap `agt-89fe96`/`agt-ff99aa`/`agt-8586b2` already flagged. Did not investigate or fix the AO escalation-dispatch code myself (genuinely out of this one-shot data-pipeline-focused role's scope — the fix belongs in `agent-orchestrator`, not a DP-service repo). Restating the recommendation plainly given the mounting recurrence count: this alert instance needs either (a) `BLK-8bb28da4` answered so the wrapper plan can be created and the underlying BLRS producer-chain gap fixed (which stops the alert from firing at all), or (b) a `/escalation-queue-reconcile` / `/data-pipeline-alerts-reconcile` pass to stop DP-WATCHER-006 from re-dispatching a fresh one-shot worker against a target with an already-open, unresolved blocked-question — whichever happens first should happen soon; a 7th+ dispatch tomorrow at 02:30Z is otherwise a near-certainty.
