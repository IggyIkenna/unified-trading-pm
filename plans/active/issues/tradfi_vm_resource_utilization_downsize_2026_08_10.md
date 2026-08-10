---
doc_type: issue
title: >-
  TradFi OHLCV backfill fleet was massively CPU-over-provisioned — e2-highmem-16 -> e2-highmem-8, concurrency pinned
summary: >-
  Operator-requested cost audit (GCP costs high, "way too much resource for what they are doing"): a live utilization
  sweep across 245 `tradfi-bf-*` VMs from the last 24h (188 completed, 39 failed, 18 running), using the app's
  already-existing self-reported `cpu_pct`/`mem_pct` telemetry (no Ops Agent needed — see
  `/codex/05-infrastructure/deployment-observability.md`'s `host_metrics_window`/`deployment_operational_data` system,
  which already documents this correctly) found the OHLCV family (NASDAQ/NYSE/CME/CBOE-idx/ICE-idx, 97% of 24h fleet
  volume, 237/245 VMs) averaging only ~6-7% CPU (≈1 of 16 vCPUs) on `e2-highmem-16`, with memory peaking 22-31.5GB (NYSE
  worst-case) — well under 128GB. The small FRED/ES_OPT/VIX family (3%, `e2-highmem-4`) is memory-justified (up to 23GB
  of 32GB, no headroom to spare) and was NOT touched. Downsized the OHLCV family's default to `e2-highmem-8` (64GB —
  still ~2x headroom over the measured 31.5GB peak). The 16-vCPU choice was originally about matching the machine a
  measured 1.56x date-fanout throughput win (`--batch-date-concurrency`) was calibrated on, not a memory need at that
  size — the auto-derived concurrency formula would otherwise halve (20-way→10-way) on the smaller machine, so
  concurrency was PINNED at 20 (decoupled from vCPU-derived sizing) to test whether the workload is I/O-bound enough to
  sustain the same fanout on fewer cores, per operator direction ("why can't we just recalibrate by sizing down whilst
  keeping the concurrency the same... this is about VM doing the same work with less resource to avoid waste"). This is
  an explicit bet, not yet re-measured — flagged as an open follow-up below.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tradfi, cost-optimization, vm-sizing, gcp, resource-utilization, backfill]
related:
  - /codex/05-infrastructure/deployment-observability.md
  - /codex/05-infrastructure/vm-launcher-runbook.md
  - /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md
  - /plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md
  - /plans/active/tradfi_consolidated_closeout_2026_07_18.md
created: "2026-08-10"
author: main (Claude Code, interactive session)
parent_epic: tradfi_master
resolved_by:
locked_by:
locked_since:
source: >-
  Operator chat instruction, 2026-08-10: "so then did you raise concurrency cap" → led to auditing whether the cap=1
  singleton lock was justified (it wasn't — separate fix); "ok we need to seriously size down these machines then they
  are using wayyy to much resource for what they are doing"; "why cnat we just recalabrate by sizing down whilst keepin
  g te concurranyc the same... this si about vm doing the aame work with less rource to avoid waste."
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
---

# TradFi OHLCV backfill fleet resource-utilization audit + downsize

## What was measured (245 VMs, last 24h, via deployment-registry `host_metrics_window` self-reported telemetry)

| Family             | n   | Machine (before) | CPU avg / max | Memory peak | Verdict                                            |
| ------------------ | --- | ---------------- | ------------- | ----------- | -------------------------------------------------- |
| CBOE-idx-ohlcv-24h | 95  | e2-highmem-16    | 7.0% / 66.7%† | 27.1GB      | over-provisioned                                   |
| NASDAQ-ohlcv-1m    | 55  | e2-highmem-16    | 6.4% / 100%†  | 30.6GB      | over-provisioned                                   |
| NYSE-ohlcv-1m      | 51  | e2-highmem-16    | 5.6% / 8.3%   | 31.5GB      | over-provisioned (CPU); memory is the real ceiling |
| CME-ohlcv-1m       | 28  | e2-highmem-16    | 6.2% / 100%†  | 26.9GB      | over-provisioned                                   |
| ICE-idx-ohlcv-24h  | 8   | e2-highmem-16    | 7.0% / 7.9%   | 22.3GB      | over-provisioned                                   |
| fred-full          | 1   | e2-highmem-4     | 27.3% / 29.3% | 23.0GB      | memory-justified, NOT touched                      |
| es-opt-light       | 5   | e2-highmem-4     | 17.4% / 29.2% | 21.5GB      | memory-justified, NOT touched                      |
| vix-light          | 2   | e2-highmem-4     | 18.7% / 26.1% | 21.9GB      | memory-justified, NOT touched                      |

†Max-CPU spikes are isolated single-sample bursts at process startup, settling to steady-state 6-9% for the rest of the
run — real but brief, not sustained load.

Cross-checked running VMs' CPU against Cloud Monitoring's independent API — numbers agreed closely, confirming the
self-reported registry data is trustworthy. 7/245 VMs had no telemetry (failed/reaped before first heartbeat sample) —
genuinely no data, not a measurement gap.

## What changed

`deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh`:

1. `TRADFI_OHLCV_MACHINE` default: `e2-highmem-16` → `e2-highmem-8` (64GB, ~2x headroom over the 31.5GB NYSE peak; still
   `highmem` tier, not `standard`, since the OOM floor below `e2-standard-4`'s 16GB was already established in
   `tradfi_backfill_oom_remediation_2026_06_24.md`).
2. `TRADFI_OHLCV_BATCH_DATE_CONCURRENCY` default: was empty (auto-derived from vCPU, ~1.25 dates/vCPU) → pinned to `20`
   (the exact level the 1.56x throughput win was measured at on the old 16-vCPU machine). Without this pin, the downsize
   would have auto-derived concurrency down to 10, giving back some of that throughput win.

## Why NOT go smaller than 8 vCPU (the "just use 2 cores" question)

GCP's `e2-custom` machine types cap memory at 8GB per vCPU (verified live:
`gcloud compute machine-types describe e2-custom-4-49152` rejects 48GB on 4 vCPU — max is 32GB). Reaching the ~48GB+
headroom this fleet needs over its measured 31.5GB peak requires at least 6 vCPU under that ratio cap — so
`e2-highmem-8` (8 vCPU/64GB) is close to the ratio-constrained minimum, not an arbitrary conservative choice. Memory,
not CPU, is the real binding constraint on how small this can go.

## Open risk — the concurrency pin is unverified at this exact ratio

The prior throughput analysis found 20-way concurrency became CPU-bound and gave almost no win at 4 vCPU (~4%
improvement, `tradfi_backfill_throughput_followups_2026_07_24.md`). 8 vCPU/20-way (2.5 dates/vCPU) has NOT been
specifically measured — this session's low average-CPU finding (6-7% even at 16vCPU/20-way) suggests the workload is
I/O-bound enough to tolerate it, but that's an inference, not a direct measurement at this ratio.

## Todo

- [ ] [DATA] P2. **Re-measure throughput and CPU utilization on the downsized fleet** after this ships — confirm (a)
      per-VM completion time/rows-per-minute stays close to the historical 46.9k rows/min/VM CME rate (not regressed),
      and (b) CPU doesn't show sustained near-100% utilization (vs. the old brief-burst-only pattern), which would
      indicate the pinned concurrency=20 is CPU-bound on 8 vCPU. **Done when**: a fresh sample of completed VMs
      (post-downsize) shows throughput within ~10% of the historical rate AND CPU utilization pattern matches the old
      brief-burst profile, not sustained saturation. If either fails, revert the concurrency pin (delete the
      `TRADFI_OHLCV_BATCH_DATE_CONCURRENCY` override, let it re-derive to 10 for 8 vCPU) and re-measure before
      considering a further machine downsize. Repo: deployment-service.

## Progress Log

- 2026-08-10: doc created, code shipped same session (`deployment-service` — see commit citation on the
  `_tradfi-ohlcv-launcher-lib.sh` code comments once pushed). Re-measurement todo above intentionally left open, not
  attempted same-session (needs the downsized fleet to actually run for a representative sample first).
- **data_engineering (slot 18) 2026-08-10T17:30Z**: Re-measurement attempted. Only 1 OHLCV VM exists post-downsize:
  `tradfi-bf-cme-ohlcv-1m-gc-2020-20260810-150303` (asia-northeast1-c, e2-highmem-8 ✓, created 15:03Z, running ~2.4h).
  Zero completed OHLCV VMs fleet-wide — the other 7 running TradFi VMs are fred-full (e2-highmem-4, 1 VM) and vix-light
  (e2-highmem-4, 6 VMs), which are the memory-justified family NOT downsized. **Partial signal from the 1 running CME VM
  (109 dates processed, 2020-01→2020-06, 5.35M rows in ~143 min = 37.4k rows/min vs historical 46.9k rows/min/VM CME
  rate = 79.8%):** CPU p50=100% (~12.5% of 8 vCPU), max=186% (~23%), no sustained saturation — matches the old
  brief-burst profile. Memory peak ~28GB RSS (44% of 64GB). The 37.4k mid-run throughput is ~20% below the historical
  baseline, but this is a SINGLE incomplete VM mid-chunk (53 total chunks of ~7 days each) — not comparable to the
  completed-VM measurement the done_definition requires. **Todo remains gated**: needs a sample of COMPLETED VMs
  (post-downsize) for a valid throughput comparison. Releasing back to queue with `reason_code: GATED` per worker.md §
  4c.
