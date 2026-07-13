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
related: [gcs_bucket_estate_cleanup_2026_07_10.md, terraform_bucket_estate_drift_resurrection_2026_07_13.md]
created: "2026-07-13"
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
locked_since:
assigned_vm:
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

1. Decide the canonical home: add a `recon` kind to cloud-providers.yaml (env-tiered `recon-{env}-{pid}`?) OR fold recon
   outputs into an existing store bucket under a `recon/` prefix (estate-consolidation-friendlier). Operator call — it
   changes whether the estate grows by 1-2 buckets or by 0.
2. Provision the chosen target; point `config.py` at the resolver (not an f-string); fix the launcher header.
3. Confirm what should produce the upstream `t1-recon/{ml,strategy}/{date}/_SUCCESS` inputs stage0 polls — the producers
   presumably also never wrote (same missing bucket): the whole T1 chain needs an end-to-end run, not just the bucket
   creation.
4. Verify the next scheduled run goes green; check dev/staging siblings; add the recon job to whatever failure alerting
   watches Cloud Run (55 consecutive failures paged nobody — that's its own gap).
