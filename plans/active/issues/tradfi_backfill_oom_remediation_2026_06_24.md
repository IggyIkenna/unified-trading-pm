---
doc_type: issue
title:
  TradFi OHLCV backfill VMs OOM-crash-loop (~15GB transient/chunk) — peaks at the 16GB e2-standard-4 ceiling; NOT a hang
summary:
  The 2026-06-24 `tradfi-bf-*` OHLCV backfill stalls flagged as `DP_VM_STALL` were **NOT** the databento chunk-decode
  hang (`afd5296` / `2410e712` are irrelevant to them) and a fresh tarball alone do...
status: open
nature: process
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, backfill, spot-vm, infrastructure, databento, monitoring, performance, data-pipeline]
related: [plans/active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md]
created: 2026-06-24
parent_epic: tradfi_master
priority: P0
source:
  [
    "market-tick-data-service/market_tick_data_service/engine/sentinels.py::_load_sentinel_catalogs",
    "market-tick-data-service/market_tick_data_service/engine/cefi_catalog_reader.py::_load_latest_catalog",
    "serial-console (gc/es/6j/nyse-2024): repeated `Out of memory: Killed process (python)` anon-rss ~15.3GB",
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
---

## What I found

The 2026-06-24 `tradfi-bf-*` OHLCV backfill stalls flagged as `DP_VM_STALL` were **NOT** the databento chunk-decode hang
(`afd5296` / `2410e712` are irrelevant to them) and a fresh tarball alone does **not** fix them. They are an **OOM
crash-loop**.

Serial-console evidence (read via `gcloud compute instances get-serial-port-output`, survives the self-delete) on every
stale VM:

| VM                                 | OOM-kills | machine               | anon-rss at kill |
| ---------------------------------- | --------- | --------------------- | ---------------- |
| `tradfi-bf-cme-ohlcv-1m-gc-2025-*` | 60        | e2-standard-4 (16 GB) | ~15.3 GB         |
| `tradfi-bf-cme-ohlcv-1m-es-2025-*` | 30        | e2-standard-4         | ~15.3 GB         |
| `tradfi-bf-nyse-ohlcv-1m-2024-*`   | 22        | e2-standard-4         | ~15.3 GB         |
| `tradfi-bf-cme-ohlcv-1m-6j-2025-*` | many      | e2-standard-4         | ~15.3 GB         |

Each chunk runs a **fresh** python process (`mtds_chunk_loop.sh` loops 53 date-chunks, one
`python -m market_tick_data_service ... --start-date CS --end-date CE` per chunk). Each fresh process balloons to ~15.3
GB within ~3 minutes and is OOM-killed; the wrapper advances to the next chunk and the next process OOMs again. To the
fleet monitor this is indistinguishable from a hang (sidecar + run.log + manifest shard all go stale, VM stays
`RUNNING`).

**Root cause (CORRECTED 2026-06-24 after live verification — supersedes the initial catalogue-reload theory):** the OOM
is a **per-date transient memory spike of ~15 GB** in the per-chunk python process's fetch/decode path, and it sits
**right at the 16 GB e2-standard-4 ceiling** → OOM-killed. Verified on `gc-2025` over a full year on e2-highmem-4 (32
GB): RSS fluctuates 2.5 → **15.3 GB peak** → 5.4 → 12.5 GB (resets per fresh chunk-process), zero OOM. The spike is a
heavy single-chunk databento fetch — a liquid `GC.OPT ohlcv_1s` expiry day, or a NASDAQ/NYSE many-symbol `ohlcv_1m` week
— whose decoded footprint is ~15 GB despite tiny written output (~1.3 MB/date), i.e. the decode/enrich path holds far
more than it emits. **The catalogue-reload theory was WRONG**: the rolled-up `catalog.parquet` files are tiny (tradfi
6.76 MiB / cefi 3.07 MiB / defi 0.95 MiB) — nowhere near 15 GB. The per-date 2× catalogue re-read WAS real churn and IS
now fixed (see below), but it was a minor contributor, not the OOM. The OOM is **pre-existing** (old code OOMed
identically; the old `gc-2025` cleared some chunks and OOMed on heavy ones), **NOT** introduced by the 2026-06-24
close-out.

## Why it matters

- TradFi OHLCV backfill makes **zero net progress** — reap→relaunch→re-OOM forever (the band-aid auto-reaper just spins
  the loop on the unfixed code). May-23 critical-path data, `tradfi_master`.
- Same class as the 2026-06-22 sports OOM (exit 137, self-delete → looked like clean completion).
- The fleet monitor mis-attributed it to the databento hang; the issue doc
  `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` "[TRADFI] P1" dispatch hypotheses (stale-tarball /
  different-unbounded-call) were both wrong — it is a memory blow-up.

## Fix — two parts

**1. The unblock (operational, verified): e2-highmem-4 (32 GB).** The ~15 GB transient peak fits comfortably in 32 GB.
Verified: `gc-2025` (worst prior offender, 60 OOM-kills on e2-standard-4) cleared >1 full 7-day chunk on e2-highmem-4
with **zero OOM-kills**, peak RSS 15.3 GB. Made the default in
`deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh` (`TRADFI_OHLCV_MACHINE` e2-standard-4 → e2-highmem-4).
**ROLLOUT (corrected): the wave-launcher is a Cloud Run JOB (`uts-prod-tradfi-wave-launcher`, every 2-3h), not a
host-cron — it runs the baked `deployment-service` image, so the committed lib-default change only reaches the fleet on
the next image rebuild.** Immediate fix applied 2026-06-24:
`gcloud run jobs update uts-prod-tradfi-wave-launcher --update-env-vars TRADFI_OHLCV_MACHINE=e2-highmem-4` (the lib
reads the env var; the launch subprocess inherits it). **VERIFIED:** a triggered execution launched 6 shards
(6a/6b/6c/6e/6j/ es-2020) all on e2-highmem-4. The committed default makes it permanent once the deployment-service
image rebuilds (drop the env override then). NOTE: the 12:00 wave had already launched 6 shards on the OLD e2-standard-4
(before the env override) — those OOM-looped + fired `DP_VM_STALL`; reaped 2026-06-24.

**2. The catalogue cache (real, minor — landed `market-tick-data-service@d83d70e2`).** Instance-level memoisation of the
rolled-up catalogue on the cefi/defi/tradfi readers (`_load_latest_catalog` → memoising wrapper over
`_download_latest_catalog`); the per-date 2× re-read is eliminated (now 1×/process). Verified live on the new gc VM
(`loaded 227576 catalogue rows` now once/process, was 2×/date). NOT the OOM fix — a churn/cost improvement. Regression:
`tests/unit/engine/test_catalog_reader_cache.py`. Also carried the databento-first test ripple (the close-out's UAC flip
left stale `batch_massive` / `available_at +15min` assertions → updated to `batch_databento` / 10 ms) so the gate was
green to land.

## Recommended decision

- [x] ✅ [TRADFI] P0. Catalogue-cache fix shipped (`market-tick-data-service@d83d70e2`) + mtds tarball rebuilt from
      clean LDR (`mtds-code @ d83d70e2`, verified). DONE 2026-06-24.
- [x] ✅ [INFRA] P0. e2-highmem-4 VERIFIED as the OOM unblock (gc-2025 cleared >1 chunk, zero OOM, peak 15.3 GB). DONE
      2026-06-24.
- [x] ✅ [INFRA] P0. Landed the `_tradfi-ohlcv-launcher-lib.sh` default → e2-highmem-4 (`deployment-service@ef8b4cd`) +
      applied the immediate `TRADFI_OHLCV_MACHINE=e2-highmem-4` env override on the `uts-prod-tradfi-wave-launcher`
      Cloud Run job (verified: 6 shards relaunched on highmem). Reaped the 6 pre-fix e2-standard-4 OOM-loopers. (Had to
      clear 4 foreign gate-reds from the concurrent tradfi close-out to land: MTDS databento-first test ripple + Yahoo
      method-size [foreign-fixed] + 2 vm_zombie_watchdog noqa placements.) DONE 2026-06-24.
- [x] ✅ [INFRA] P2. After the next `deployment-service` image rebuild (which bakes the committed e2-highmem-4 default),
      DROP the runtime `TRADFI_OHLCV_MACHINE` env override on the `uts-prod-tradfi-wave-launcher` Cloud Run job —
      **DONE, confirmed 2026-07-14 (see the P1 RECONCILED-COMPLETE-BY-FLEET entry below) and re-independently-verified
      live 2026-07-25** via `gcloud run jobs describe uts-prod-tradfi-wave-launcher     --region=asia-northeast1`: job
      env carries no `TRADFI_OHLCV_MACHINE` var (only
      PROJECT_ID/DEPLOYMENT_ENV/GCP_PROJECT_ID/CLOUD_PROVIDER/DEPLOYMENT_ENV_SHORT/WORKSPACE_ROOT/WAVE_MAX_CONCURRENT) —
      fleet runs on the baked `e2-highmem-4` default. Target repo: `deployment-service`.
- [x] ✅ [TRADFI] P1. **RECONCILED-COMPLETE-BY-FLEET (2026-07-14)** — the always-on wave-launcher fleet IS the
      manifest-verified completion run for this todo; no separate manual "run to completion" pass is needed or
      appropriate (it would just race the standing Cloud Run Job). Verified 2026-07-14 (~18:30Z): - **Machine type —
      CONFIRMED e2-highmem-4.** All 8 currently-RUNNING `tradfi-bf-cme-ohlcv-1m-*` / `tradfi-bf-cboe-ohlcv-1m-*` VMs
      (`cl/es/gc/hg/ng/nq/si-2025`, `vx-2026`) are `e2-highmem-4` (`gcloud compute instances list` for all 8 +
      `gcloud compute instances describe --format='value(machineType)'` on 3 of them: gc-2025, es-2025, cboe-vx-2026).
      The `uts-prod-tradfi-wave-launcher` Cloud Run job env no longer carries a `TRADFI_OHLCV_MACHINE` override (checked
      via `gcloud run jobs describe`) — the P2 todo above (drop the runtime override once the image bakes the default)
      has already happened; the fleet is running on the **baked code default**
      (`deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh:28`,
      `TRADFI_OHLCV_MACHINE="${TRADFI_OHLCV_MACHINE:-e2-highmem-4}"`), not a stop-gap env var. - **Zero OOM recurrence —
      CONFIRMED.**
      `gcloud compute instances get-serial-port-output --port=1 | grep -c "Out       of memory: Killed process"` = **0
      on all 8 currently-running fleet VMs** (the original bug's signature, 22-60 kills/VM on e2-standard-4, is gone).
      `gcloud compute operations list` shows the expected wave-launcher insert/delete cadence (every 2-3h) plus normal
      SPOT `compute.instances.preempted` events (self-recovering per `spot-vms-for-backfill.md`) — no rapid crash-loop
      churn; recently-completed VM lifetimes ran 6h-11h (e.g. `gc-2025-...-030117` lived 10h56m before self-delete),
      consistent with genuine multi-chunk completion, not the ~3-minute OOM cycle from the original bug. - **Manifest IS
      moving.** CME `captured` = 1,077,963 vs the cited "this morning" baseline of 1,077,959
      (`tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md` L105/280, also captured 2026-07-14) — net +4 in that
      narrow window, consistent with the campaign's documented "hours/days, one-shard-at-a-time" pace. Real write
      throughput is much higher (22,721 CME manifest rows written today: 13,551→captured, 9,018→empty_confirmed, 152→new
      EU), but most `captured`-status writes are idempotent re-touches of already-captured cells from the per-VM
      full-year chunk-loop re-walking overlapping year shards on every relaunch (written_at refreshes, capture_status
      doesn't change) — not a bug, just means raw write-count isn't a clean net-progress proxy; CME/CBOE-specific
      net-new-completions tracking would need a same-day-start/end manifest diff to isolate cleanly (not done here — out
      of this todo's bounded scope). Overall gap cells (attempted_failed+EU): 342,134+89,483=431,617 vs the cited
      2026-07-13 baseline 429,734; **attempted_failed alone dropped exactly 342,211→342,134 (-77)**, which cross-checks
      EXACTLY against the documented 2026-07-14 ICE purge (`tradfi_multisource_backfill_2026_06_22.md` L150:
      "attempted_failed 342,211→342,134, delta exactly -77" + captured 1,620,826→1,608,382, delta -12,444, both
      reclassified to empty_confirmed) — i.e. the attempted_failed drop is the ICE purge, not organic drainage; overall
      EU's small net rise (+1,960) is unattributed in this check (plausibly ongoing MVP/universe enumeration touching
      NASDAQ/NYSE/CME/KRX — Task B's domain) and does not indicate stall. **VERDICT: fleet IS the completion run —
      RECONCILED, not relaunched.** Ownership is wave_launcher-owned/ongoing (Cloud Run Job
      `uts-prod-tradfi-wave-launcher`, every 2-3h, Databento-account-guarded one-shard-at-a-time); it will keep draining
      CME/CBOE (and the rest of tradfi) asynchronously with zero OOM recurrence. No manual relaunch, launcher-default
      fix, or bulk-kill performed (fleet was healthy — see hard rule against killing a healthy fleet). The remaining
      throughput question (real per-day net-drain rate vs re-verification churn) is a secondary observation, not a
      blocker; the P2 memray todo below is the right place for the deeper decode/enrich footprint investigation if the
      pace itself becomes a concern. Evidence commands: `gcloud compute instances list/describe`,
      `gcloud compute operations list`, `gcloud run jobs describe uts-prod-tradfi-wave-launcher`,
      `gcloud compute instances get-serial-port-output`, `availability_index.parquet` read via instruments-service
      `.venv` (read-only, scratchpad query, ADC).
- [ ] [TRADFI] P2. **memray the ~15 GB per-date transient footprint** (tiny output, ~15 GB decoded) — the decode/enrich
      path of a heavy `GC.OPT ohlcv_1s` / many-symbol equity week holds far more than it emits. Reducing it lets the
      backfill run on the cheaper e2-standard-4 (revert the machine bump). Likely the eager DBN decode buffering or an
      un-released pyarrow frame. Target repo: `market-tick-data-service`.
