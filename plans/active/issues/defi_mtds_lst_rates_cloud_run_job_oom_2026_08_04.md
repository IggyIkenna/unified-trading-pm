---
doc_type: issue
title:
  Cloud Run job uts-prod-mtds-collect-lst-rates OOM-failing every scheduled run since 2026-08-02 — blocks ALL 11 EVM + 4
  Solana LST venues, not just BLAZESTAKE/SOLBLAZE
summary:
  While root-causing why market-tick-data-service's legacy BLAZESTAKE lst_rates writer stopped producing data
  2026-07-31→08-01 (defi_hyperliquid_residual_manifest_rows_2026_08_04.md's BLAZESTAKE finding), found the writer
  stoppage is NOT venue-specific — it is the daily `collect-lst-rates` Cloud Run JOB itself OOM-crashing on every
  scheduled 01:00 UTC run since 2026-08-02 (3 consecutive failures as of 2026-08-04, confirmed via `gcloud run jobs
  executions list` + Cloud Audit Logs quoting the exact message "The configured memory limit was reached" on all three).
  This blocks fresh `lst_rates` data for EVERY LST venue this handler covers (11 EVM LSTs + 4 Solana LSTs —
  Marinade/Jito/SolBlaze/Sanctum), not just the BLAZESTAKE/SOLBLAZE naming issue that triggered this investigation.
  Onset correlates with two 2026-08-01 deploys in the failure window (`market-tick-data-service@95d24521` "implement
  expected_unattempted seeder for venue/chain-grain DeFi handlers", wired into lst_rates_handler.py right before
  recorder.close(); and the same-day `read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md` fix, already
  archived) — a later attempted mitigation (`market-tick-data-service@d4408134`, 2026-08-03, "TTL the process-global
  catalogue cache") was live for the 2026-08-04 run and did NOT resolve the OOM (identical failure message on a newer
  image). Fix requires either a deployment-service Cloud Run job memory bump
  (`terraform/gcp/defi_collection_scheduler.tf`'s `lst-rates` entry, `memory = "2Gi"` -> a higher value) or a deeper
  memory-profiling pass in market-tick-data-service — both outside this dispatch's assigned repo scope
  (market-tick-data-service / unified-api-contracts / unified-trading-pm / unified-trading-library only;
  deployment-service was read-only for this investigation).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [defi, lst-rates, cloud-run, oom, memory, cron, data-pipeline-correctness]
related:
  [
    /plans/active/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
    /plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
  ]
created: 2026-08-04
author: slot-3
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: correct-code
resolved_by:
locked_by:
source:
  [
    "2026-08-04 (slot-3) — found while root-causing the BLAZESTAKE lst_rates writer stoppage dispatched via
    defi_hyperliquid_residual_manifest_rows_2026_08_04.md; evidence gathered via `gcloud run jobs executions list` /
    `gcloud run jobs executions describe` / `gcloud logging read` against project central-element-323112, region
    asia-northeast1 — read-only, no GCS corpus walk.",
  ]
depends_on: []
context_scope:
  [
    deployment-service/terraform/gcp/defi_collection_scheduler.tf,
    market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_catalogue_filter.py,
    /plans/active/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md,
  ]
---

# `uts-prod-mtds-collect-lst-rates` OOM-failing every run since 2026-08-02

## Why this is a separate issue from the BLAZESTAKE naming bug

`defi_hyperliquid_residual_manifest_rows_2026_08_04.md`'s BLAZESTAKE finding attributed the venue's writer stoppage to
the venue itself. Investigating the "why did it stop 2026-07-31→08-01" question (this dispatch's mandate) found a
DIFFERENT, handler-wide mechanism: the entire `collect-lst-rates` Cloud Run Job has been OOM-crashing on its daily
schedule since 2026-08-02, three days running as of 2026-08-04. This affects the SAME job that writes ALL 15 LST venues
this handler covers (11 EVM: Lido/RocketPool/EtherFi/Ethena/Ankr/Stader/Stakewise/Swell/Puffer/Mantle/ Eigenlayer + 4
Solana: Marinade/Jito/SolBlaze/Sanctum) — not a BLAZESTAKE-specific fault. Fixing the BLAZESTAKE/ SOLBLAZE naming bug
(shipped separately, same session) does NOT fix this — the job will keep failing to produce ANY fresh `lst_rates` data,
canonical venue name or not, until the OOM itself is addressed.

## Evidence

**Execution history**
(`gcloud run jobs executions list --job=uts-prod-mtds-collect-lst-rates --project= central-element-323112 --region=asia-northeast1`):

| Execution   | Start (UTC)               | Status              |
| ----------- | ------------------------- | ------------------- |
| `...-f2zwg` | 2026-08-01 01:00          | Completed True      |
| `...-gmhd2` | 2026-08-01 09:45 (ad-hoc) | Completed True      |
| `...-74rqc` | 2026-08-02 01:00          | Completed **False** |
| `...-lq977` | 2026-08-03 01:00          | Completed **False** |
| `...-c9qxr` | 2026-08-04 01:00          | Completed **False** |

**Failure message** (`gcloud logging read`,
`resource.type="cloud_run_job" AND resource.labels.job_name= "uts-prod-mtds-collect-lst-rates"`), identical across all
three failures:

```
Task uts-prod-mtds-collect-lst-rates-<exec>-task0 failed with exit code: 0 and message:
The configured memory limit was reached.
```

Cloud Run job config (`deployment-service/terraform/gcp/defi_collection_scheduler.tf`, `"lst-rates"` entry):
`cpu = "1"`, `memory = "2Gi"`, `timeout = 1200`. `maxRetries = 1` — each failing execution retries once immediately and
fails identically both times (`retriedCount: 1`, `failedCount: 1`).

**Image digests per execution**
(`gcloud run jobs executions describe <exec> --format="value(spec.template.spec. containers[0].image)"`) confirm a NEW
image deployed between each of these executions — i.e. this isn't one bad image stuck in place, the OOM has persisted
across at least 4 distinct image rebuilds (08-01 09:45 → 08-02 → 08-03 → 08-04, all different `@sha256:...` digests).

**Timing correlation** (not proven causal, but the tightest candidate): the last KNOWN-GOOD execution is 2026-08-01
09:45 UTC; the first failure is 2026-08-02 01:00 UTC. Two `market-tick-data-service` commits landed in that window that
touch this exact handler's memory profile:

- `95d24521` (2026-08-01T02:37:43Z) —
  `feat(defi): implement expected_unattempted seeder for venue/chain-grain DeFi handlers`, wires
  `recorder.emit_expected_unattempted_for_remaining(...)` into `lst_rates_handler.py` right before `recorder.close()`
  (both the early-return-on-zero-rows path and the normal-completion path). New code, new UAC-declared-venue enumeration
  loop per run — small in isolation (a handful of (venue, chain) pairs), but the nearest candidate to the exact failure
  boundary.
- The same day, `read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md` (already archived,
  `plans/archive/2026_08/`) shipped a UTL fix for a DIFFERENT unconditional-widening memory bug in
  `read_availability_index`'s slim-read path (`unified_trading_library/manifest_writer/_read_index.py`) — worth checking
  whether `lst_rates_handler.py`'s freshness-cache warmup (`_gas_fee_helpers.bounded_freshness_warmup`, reused here per
  that helper's own docstring) calls into a manifest-read path this fix does or doesn't cover.

A THIRD commit, `d4408134` (2026-08-03T17:48:54Z,
`fix(dex-pools): TTL the process-global catalogue cache (was read-once-forever)`,
`market_tick_data_service/cli/handlers/_catalogue_filter.py`), was live for the 2026-08-04 01:00 UTC execution
(confirmed via a newer image digest than 08-03's) and did **not** resolve the OOM — the 2026-08-04 failure message is
byte-identical to 08-02/08-03. This rules out the specific mechanism that fix targeted as the (or at least the ONLY)
driver, without identifying the real one.

**Not yet confirmed**: whether the OOM kills the process before or after any per-venue writes land for that day (the
`DefiManifestRecorder`'s `batch_size=1` drains each `record_captured` immediately, so an early-in-the-run OOM could
still leave SOME venues' data written for that day while later ones get nothing — order-of-processing dependent, not
checked in this pass). Not yet confirmed whether this is a genuine NEW memory-usage regression or the job sitting right
at the 2Gi edge for a while (the job's `gcloud run jobs executions list` history going back to May shows a long tail of
intermittent `Completed False` failures for a MIX of reasons — timeout, generic container error, and memory-limit — so
some baseline flakiness pre-dates 2026-08-02; what's new since 08-02 is the FAILURE BECOMING CONSISTENT, 3/3 days, all
with the identical memory-limit message).

## Why not fixed in this dispatch

This was found while executing a BLAZESTAKE-scoped naming-bug dispatch
(`defi_hyperliquid_residual_manifest_rows_2026_08_04.md`), whose assigned repo scope is `market-tick-data-service` /
`unified-api-contracts` / `unified-trading-pm` / `unified-trading-library` only. The most direct fix (bump
`memory = "2Gi"` in `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s `"lst-rates"` entry and
`terraform apply`) requires editing `deployment-service`, outside that scope. The alternative (root-cause and shrink the
handler's actual memory footprint in `market-tick-data-service`) needs a live redeploy-and-observe loop (this
environment cannot trigger a Cloud Build + Cloud Run Job execution round-trip and watch RSS climb) — reasoned candidates
are named above but none is confirmed as THE driver, so shipping a guessed code change here risked an unverified "fix"
that doesn't actually resolve the OOM (as `d4408134` already demonstrated can happen).

## Todos

- [ ] [INFRA] P1. **RULED 2026-08-06 (operator): approved, AO-dispatchable.** `[INFRA]` tag (was `[OPERATOR]`) — the
      doc's own text already says this is mechanical, not a judgment call; per the operator's standing policy on
      plan-scoped infra changes, dispatch it directly. Bump
      `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s `"lst-rates"` entry `memory = "2Gi"` to a higher
      value (e.g. `"4Gi"`) and `terraform apply` — the fast, low-risk mitigation while the real memory driver is
      investigated.
- [ ] [DIAG] P1. Root-cause the actual memory driver in `market-tick-data-service`'s `collect-lst-rates` path (11 EVM +
      4 Solana venues in one process) — candidates to check first: (a) whether
      `_gas_fee_helpers.bounded_freshness_warmup`'s manifest read is bounded the same way
      `read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md` fixed, (b) the DeFi instrument catalogue's
      actual decoded size in `_catalogue_filter.py::_load_catalogue` (currently reads ALL columns via
      `pd.read_parquet(io.BytesIO(raw))` with no `columns=` projection — a cheap, safe narrowing if the catalogue is
      wide), (c) whether 11 EVM adapters' concurrent RPC response buffering is the actual peak, independent of anything
      DeFi-catalogue-related. A local memory-profiled dry-run against the `-test-` buckets (not prod) would settle this
      without another live Cloud Run failure.
- [ ] [DIAG] P2. Once (a) is confirmed either way, check whether SOME venues in this job still got written on
      08-02/08-03/08-04 before the crash (per-venue processing order in `lst_rates_handler.py` vs. which venues show
      recent `written_at` in the manifest) — determines whether this is a total daily-data-loss event or a partial one.

## Progress Log

- **sub-agent dispatch 2026-08-04** (BLAZESTAKE naming-bug investigation,
  `defi_hyperliquid_residual_manifest_rows_2026_08_04.md`): filed this doc after confirming via
  `gcloud run jobs executions list` + `gcloud logging read` that the writer stoppage this dispatch was asked to diagnose
  is NOT BLAZESTAKE-specific — it's a handler-wide Cloud Run OOM affecting all 15 LST venues, first failing 2026-08-02
  and still failing as of 2026-08-04 (confirmed on the newest available image). BLAZESTAKE naming bug fixed + migrated
  separately in the same session (see the source doc's BLAZESTAKE section for that outcome) — this OOM is the reason the
  WRITER overall has produced zero fresh `lst_rates` data (any venue) since 2026-08-01, independent of the naming fix.

- **na-eligibility-audit 2026-08-06 (governance-sweep reclassification pass)**: RECLASSIFY,
  `assigned_vm: NA -> planning`. Todo 1 was resolved this same session ("RULED 2026-08-06 (operator): approved,
  AO-dispatchable", retagged `[OPERATOR] -> [INFRA]`) for a bounded one-line terraform memory bump
  (`deployment-service/terraform/gcp/defi_collection_scheduler.tf`) + terraform apply; todos 2-3 are bounded `[DIAG]`
  investigations with named candidates and a stated done-when. Conflict-check cleared (no overlapping claim in
  `parent_epic: infrastructure_master`). `assigned_role` was the placeholder value `NA`; filled `infra` (terraform +
  Cloud Run scope).
