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
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, databento, massive, mtds, t1-batch, cron, data-correctness, sourcing]
related: [../sports_legacy_bucket_cutover_2026_07_16.md]
created: 2026-07-17
last_updated: 2026-07-17
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
source: cutover T6.10
---

# TradFi T+1 has no working MTDS collection job

## What was measured (2026-07-17, `[slot-3·laptop]`)

Fixing sports cutover **T6.10** (the broken `fast-t1-recon` job) surfaced this. The chain:

1. `uts-prod-market-tick-data-service-fast-t1-recon` had baked args `--operation download --mode batch` with **no
   `--asset-group`** → every execution died with `ValueError: asset_group is required for tick-data bucket resolution`,
   `failedCount=1`, 0 results. Daily at 00:30 since before the freeze. (This is the T6.10 symptom.)
2. The terraform scheduler describes the phase as _"MTDS T+1 FAST — Sports odds, DeFi on-chain, Prediction, TradFi"_ and
   the job module comment as _"Sports odds, Prediction, TradFi"_.
3. Baking `--asset-group SPORTS PREDICTION TRADFI` (execution `…-lx64t`) then failed with:
   `ValueError: --source databento|massive is REQUIRED for a TradFi OHLCV download (no SOURCE_PRIORITY[0] default — the stamp must reflect the ACTUAL fetcher's vendor)`.
   SSOT: `codex/02-data/tradfi-databento-sourcing-ssot.md`.
4. `--source` is a **single per-invocation vendor value**. Any value chosen for the TradFi leg would MIS-STAMP the
   sports/prediction legs sharing the invocation. ⇒ **TradFi cannot share this job.** T6.10 was fixed by dropping
   TradFi: `--asset-group SPORTS PREDICTION` (execution `…-vs2bd` succeededCount=1). `deployment-service@cf49de42`.
5. The full MTDS Cloud Run job inventory (2026-07-17) is: `…-cefi-t1-recon`, `…-fast-t1-recon`, and the 11
   `…-mtds-collect-*` DeFi per-operation jobs. **Nothing source-scoped for TradFi.** `fast-t1-recon` was the only job
   nominally covering TradFi and it has never succeeded.

## Impact

TradFi T+1 tick collection (Databento CFE / CME-1s, Massive equities / CME-1m) is **not running on the batch path**. If
a TradFi corpus exists it was backfilled some other way; the daily T+1 forward-fill is absent.

## Fix (not done here — needs its own workstream)

Add TradFi-source-scoped T+1 MTDS job(s) alongside `mtds_fast_t1_recon_job` / `mtds_cefi_t1_recon_job` in
`deployment-service/terraform/gcp/audit03_cron_provisioning.tf` + `t1_batch_scheduler.tf`:

- `…-tradfi-databento-t1-recon`: `--operation download --mode batch --asset-group TRADFI --source databento`
- `…-tradfi-massive-t1-recon`: `--operation download --mode batch --asset-group TRADFI --source massive`

(split by which datasets each vendor owns — see the sourcing SSOT). Verify each with a real execution that exits 0 and
writes rows, per the T6.10 "run it, don't read it" gate.
