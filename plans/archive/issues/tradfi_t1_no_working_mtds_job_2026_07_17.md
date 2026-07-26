---
doc_type: issue
title: TradFi T+1 tick collection has NO working MTDS Cloud Run job — fast-t1-recon can never cover it
summary:
  Found while fixing sports cutover T6.10 2026-07-17. The only MTDS job nominally scoped to TradFi T+1
  (`uts-prod-market-tick-data-service-fast-t1-recon`) structurally CANNOT collect TradFi — a TradFi OHLCV download
  requires an explicit `--source databento|massive` (no SOURCE_PRIORITY[0] default, by design, so the stamp reflects the
  real vendor), and `--source` is ONE per-invocation value, so it cannot be shared with the sports/prediction legs in
  the same job. The job has been firing daily at 00:30 into a guaranteed failure since before the sports freeze; the
  full Cloud Run job list carries no TradFi-source-scoped MTDS job at all. TradFi T+1 tick data (Databento CFE/CME-1s,
  Massive equities/CME-1m) is therefore NOT being collected on the T+1 batch path.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, databento, massive, mtds, t1-batch, cron, data-correctness, sourcing]
related: [../sports_legacy_bucket_cutover_2026_07_16.md]
created: 2026-07-17
last_updated: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
resolved_by:
  "deployment-service@11bed3c (tradfi_backfill_throughput_followups_2026_07_24.md — added source-scoped
  `uts-prod-market-tick-data-service-tradfi-databento-t1-recon` Cloud Run job + its scheduler, both ENABLED) plus its
  SIGKILL-hardening follow-up (2026-07-25, 46m28.5s run, no SIGKILL). LIVE re-verified 2026-07-26 (this todo,
  slot-5/review): `gcloud run jobs executions list --job=uts-prod-market-tick-data-service-tradfi-databento-t1-recon
  --region=asia-northeast1 --project=central-element-323112` shows 6 consecutive daily SCHEDULED (un-forced, ~00:35 UTC)
  executions 2026-07-21 through 2026-07-26, ALL succeededCount=1/failedCount=0, zero SIGKILLs. The 2026-07-26 run
  (processing 2026-07-25, a Saturday) correctly logged `No active venues ... known non-trading day` — honest-absence,
  not a failure. TradFi T+1 tick collection IS now running on the batch path."
source: cutover T6.10
---

# TradFi T+1 has no working MTDS collection job

> **🟢 RESOLVED 2026-07-26.** TradFi T+1 forward-fill job shipped (`deployment-service@11bed3c`) and live-reverified via
> 6 consecutive daily succeeded Cloud Run executions 2026-07-21 through 2026-07-26 — see `resolved_by` above and §
> "RESOLVED 2026-07-26" below. Archived here (plan_health hygiene-sweep hard-gate fix, escalation `agt-91b1f7`) per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule.

## What was measured (2026-07-17, `[slot-3·laptop]`)

Fixing sports cutover **T6.10** (the broken `fast-t1-recon` job) surfaced this. The chain:

1. `uts-prod-market-tick-data-service-fast-t1-recon` had baked args `--operation download --mode batch` with **no
   `--asset-group`** → every execution died with `ValueError: asset_group is required for tick-data bucket resolution`,
   `failedCount=1`, 0 results. Daily at 00:30 since before the freeze. (This is the T6.10 symptom.)
2. The terraform scheduler describes the phase as _"MTDS T+1 FAST — Sports odds, DeFi on-chain, Prediction, TradFi"_ and
   the job module comment as _"Sports odds, Prediction, TradFi"_.
3. Baking `--asset-group SPORTS PREDICTION TRADFI` (execution `…-lx64t`) then failed with:
   `ValueError: --source databento|massive is REQUIRED for a TradFi OHLCV download (no SOURCE_PRIORITY[0] default — the stamp must reflect the ACTUAL fetcher's vendor)`.
   SSOT: `/codex/02-data/tradfi-databento-sourcing-ssot.md`.
4. `--source` is a **single per-invocation vendor value**. Any value chosen for the TradFi leg would MIS-STAMP the
   sports/prediction legs sharing the invocation. ⇒ **TradFi cannot share this job.** T6.10 was fixed by dropping
   TradFi: `--asset-group SPORTS PREDICTION` (execution `…-vs2bd` succeededCount=1). `deployment-service@cf49de42`.
5. The full MTDS Cloud Run job inventory (2026-07-17) is: `…-cefi-t1-recon`, `…-fast-t1-recon`, and the 11
   `…-mtds-collect-*` DeFi per-operation jobs. **Nothing source-scoped for TradFi.** `fast-t1-recon` was the only job
   nominally covering TradFi and it has never succeeded.

## Impact

TradFi T+1 tick collection (Databento CFE / CME-1s, Massive equities / CME-1m) is **not running on the batch path**. If
a TradFi corpus exists it was backfilled some other way; the daily T+1 forward-fill is absent.

## RESOLVED 2026-07-26

Both blockers this doc's own frontmatter was waiting on are now closed on the other side
(`tradfi_backfill_throughput_followups_2026_07_24.md`): the T+1 forward-fill job shipped (`deployment-service@11bed3c`)
and its SIGKILL follow-up is fixed (46m28.5s clean run, no SIGKILL). Re-verified LIVE here (not by trusting either doc)
via `gcloud run jobs executions list` against the real Cloud Run job — 6 consecutive daily SCHEDULED executions
2026-07-21 through 2026-07-26 all succeeded (0 failures, 0 SIGKILLs); see `resolved_by` in the frontmatter for the full
citation. TradFi T+1 tick collection is no longer absent from the batch path — the original defect this doc reported is
fixed and confirmed live.

## Fix (historical — already delivered, kept for record)

Add TradFi-source-scoped T+1 MTDS job(s) alongside `mtds_fast_t1_recon_job` / `mtds_cefi_t1_recon_job` in
`deployment-service/terraform/gcp/audit03_cron_provisioning.tf` + `t1_batch_scheduler.tf`:

- `…-tradfi-databento-t1-recon`: `--operation download --mode batch --asset-group TRADFI --source databento`
- ~~`…-tradfi-massive-t1-recon`: `--operation download --mode batch --asset-group TRADFI --source massive`~~ —
  **OBSOLETE (2026-07-19 operator ruling, corrected 2026-07-25 plan-reconcile)**: Massive was REMOVED as a tradfi source
  entirely; `--source massive` routing is DELETED and now raises. No massive-scoped job is needed or possible. SSOT:
  `/codex/02-data/tradfi-databento-sourcing-ssot.md`.

(split by which datasets each vendor owns — see the sourcing SSOT). Verify each with a real execution that exits 0 and
writes rows, per the T6.10 "run it, don't read it" gate. **Status note (2026-07-25 plan-reconcile)**: the databento leg
above shipped — `uts-prod-market-tick-data-service-tradfi-databento-t1-recon` Cloud Run job +
`uts-prod-market-tick-data-tradfi-databento-t1-schedule` scheduler, both ENABLED — per
`/plans/active/tradfi_backfill_throughput_followups_2026_07_24.md` (which also tracks a live SIGKILL-at-2cpu/8Gi
follow-up on that same job, since fixed). **Reconciled 2026-07-26** — see § "RESOLVED 2026-07-26" above and the
frontmatter's `status`/`resolved_by`.
