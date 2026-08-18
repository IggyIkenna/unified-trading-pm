---
doc_type: issue
title: blrs-daily-determinism Cloud Run Job pages daily — wired to the wrong BLRS CLI operation
summary: >-
  DP-WATCHER-006 CRITICAL page for uts-prod-blrs-daily-determinism (Cloud Run Job, exit 1 daily since scheduler
  activation). Root cause -- the Terraform Stage B wiring invokes --operation reconcile (the LIVE-trading T+1
  recon op, which requires execution-store config snapshots + ML/strategy t1-recon GCS outputs that this
  paper-week soak pipeline never produces) instead of --operation daily-determinism (the op actually built for
  this job -- P7.1-B, DailyDeterminismHandler -- which reads paper_ledger_root/batch_ledger_root and honest-no-ops
  when they're unset). Fixed by switching the CLI operation; a separate, larger gap remains (paper_ledger_root/
  batch_ledger_root are never populated and no batch-rerun trigger stage exists), tracked as a follow-up todo.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, batch-live-reconciliation-service]
scope: [engineer, admin]
tags: [dp-alerts, dp-watcher-006, cloud-run-job, blrs, determinism, terraform]
related: [/plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md]
created: 2026-08-18
parent_epic: observability_master
priority: P1
source: [DP-WATCHER-006, agt-86b806]
assigned_vm: NA
resolved_by:
locked_by:
---

## What I found

`uts-prod-blrs-daily-determinism` (Cloud Run Job, `asia-northeast1`, project `central-element-323112`) has been
failing every scheduled T+1 execution (02:30 UTC daily) since the `paper_determinism_enabled` gate flipped to
`true` by default. Confirmed via `gcloud run jobs executions list` + `gcloud logging read` for the 2026-08-18
and 2026-08-17 executions — both fail identically:

```
[Stage 0] FAILED — Missing upstream data for <date>: execution config snapshot:
gs://execution-store-prd-central-element-323112/configs/snapshots/<date>/config.json; ML t1-recon outputs:
gs://recon-prd-central-element-323112/t1-recon/ml/<date>/_SUCCESS; strategy t1-recon outputs:
gs://recon-prd-central-element-323112/t1-recon/strategy/<date>/_SUCCESS
Reconciliation FAILED -- 0 deviations, failed stages: ['config_pull']
Container called exit(1).
```

Root cause: `deployment-service/terraform/gcp/paper_week_determinism_scheduler.tf`'s `blrs_daily_determinism_job`
module invokes `python -m batch_live_reconciliation_service --operation reconcile --mode batch`. `--operation
reconcile` (`ReconcileHandler` → `stage0_config_pull.run_stage0`) is the **live-trading** T+1 reconciliation
path — it unconditionally requires an execution-store config snapshot + ML/strategy `t1-recon` `_SUCCESS`
markers, none of which any producer writes in this paper-week-soak context. Nothing in the codebase writes to
`t1-recon/ml/`, `t1-recon/strategy/`, or `execution-store-*/configs/snapshots/` for this pipeline — those are a
different (not-yet-live) data source entirely.

The job that was actually meant for this cron — `--operation daily-determinism`
(`DailyDeterminismHandler`, P7.1-B, shipped after the terraform comment was written) — reads
`cfg.paper_ledger_root` / `cfg.batch_ledger_root` instead (the paper run's ledger + its batch-rerun's ledger,
exactly what `config.py`'s own doc-comment says "the cron sets ... from the prior day's paper run + its batch
rerun"), and returns an **honest no-op** (`status: ok, skipped: no_run_configured`, not an alert-worthy
failure) when those roots are unset — never a fabricated verdict. The terraform's header comment ("a dedicated
`--operation daily_determinism_stage` is NOT yet implemented ... tracked as P-todo") is stale: P7.1-B shipped
2026-06-20 (`plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 7 P2.7.1/P2.7.2). The
Terraform wiring was simply never updated to point at it.

## Why it matters

A false-failure CRITICAL page every single night (DP-WATCHER-006, generic Cloud Run Job execution-failure
sweep — "no per-job dependent action exists yet" per its own registry entry) trains the on-call rotation to
ignore blrs-daily-determinism pages, which will mask a REAL determinism-bug page once the pipeline is properly
wired (P6.2's whole purpose — CRITICAL on a determinism bug).

## Fix shipped

`deployment-service` — `paper_week_determinism_scheduler.tf`: `blrs_daily_determinism_job.args` switched
`--operation reconcile` → `--operation daily-determinism`; dropped the dead `RECONCILE_DATE` env var (read by
no code path — `DailyDeterminismHandler._resolve_day()` already defaults to yesterday-UTC when `--start-date`
is absent, which matches the T+1 cron's own cadence); updated the stale header comment. See commit for exact
diff.

## Remaining gap (NOT fixed here — out of scope for a one-shot DP escalation)

`paper_ledger_root` / `batch_ledger_root` are still never populated (both default `""`), and there is no
Cloud Run Job/cron stage anywhere that triggers strategy-service's existing `batch-rerun` CLI operation
(`cli/handlers/batch_rerun.py`, proven ε=0 — P2.7.2/P9.B, 2026-06-20) to produce the "run B" ledger this stage
needs. Until both are wired, `daily-determinism` will run as a permanent (correct, honest) no-op — it will
never actually reconcile. Tracked as a `- [ ]` follow-up todo in
`plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 7.

## Recommended decision

A: Land the CLI-operation fix now (stops the false page immediately, zero regression risk — the job goes from
"crashes daily" to "honestly no-ops daily") and track the ledger-root + batch-rerun-trigger wiring as a
separate, larger P2 infra todo. **[WORKER REC]**
B: Also attempt the full ledger-root wiring in this same session (requires designing how the cron discovers
"yesterday's paper run_id" dynamically — a real design decision, not a mechanical fix).

Going with A — see Progress Log / commit for the shipped fix.

## Progress Log

- **2026-08-18** — Diagnosed via `gcloud run jobs executions list` + `gcloud logging read` (2 consecutive failed
  executions, 2026-08-17 and 2026-08-18, identical `[Stage 0] FAILED — Missing upstream data` error). Fixed:
  `deployment-service@e3826a7f7c` (`--operation reconcile` → `--operation daily-determinism`, dead `RECONCILE_DATE`
  env var dropped, stale header comment corrected), verified on `origin/live-defi-rollout`. Follow-up gap
  (ledger-root wiring) tracked as `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` P2.7.5.
  Status kept `open` pending P2.7.5 — the immediate CRITICAL page is resolved, but this doc's title ("wired to the
  wrong CLI operation") is now historical; re-verify next scheduled run (02:30 UTC) exits 0 before closing.
