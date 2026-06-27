---
doc_type: plan
title:
  "TradFi OHLCV backfill VMs OOM-crash-loop (~15GB transient/chunk) — peaks at the 16GB e2-standard-4 ceiling; NOT a
  hang"
created: 2026-06-24
parent_epic: tradfi_master
source:
  - market-tick-data-service/market_tick_data_service/engine/sentinels.py::_load_sentinel_catalogs
  - market-tick-data-service/market_tick_data_service/engine/cefi_catalog_reader.py::_load_latest_catalog
  - "serial-console (gc/es/6j/nyse-2024): repeated `Out of memory: Killed process (python)` anon-rss ~15.3GB"
locked_by: live-defi-rollout
priority: P0
status: active
summary: The 2026-06-24 `tradfi-bf-*` OHLCV backfill stalls flagged as `DP_VM_STALL` were **NOT** the databento chunk-decode hang (`afd5296` / `2410e712` are irrelevant to them) and a fresh tarball alone do...
nature: process
asset_group: tradfi
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
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
- [ ] [INFRA] P2. After the next `deployment-service` image rebuild (which bakes the committed e2-highmem-4 default),
      DROP the runtime `TRADFI_OHLCV_MACHINE` env override on the `uts-prod-tradfi-wave-launcher` Cloud Run job (the
      override is the stop-gap; the baked default is the durable state). Target repo: `deployment-service`.
- [ ] [TRADFI] P1. **Run the full tradfi OHLCV backfill to manifest-verified completion** on e2-highmem-4 (the
      wave-launcher drives shards one-at-a-time per its Databento-account guard — hours/days; `gc-2025` is already
      running on 32 GB). Verify captured rows climb + zero OOM in serial console per shard. Target repo:
      `market-tick-data-service` / `deployment-service`.
- [ ] [TRADFI] P2. **memray the ~15 GB per-date transient footprint** (tiny output, ~15 GB decoded) — the decode/enrich
      path of a heavy `GC.OPT ohlcv_1s` / many-symbol equity week holds far more than it emits. Reducing it lets the
      backfill run on the cheaper e2-standard-4 (revert the machine bump). Likely the eager DBN decode buffering or an
      un-released pyarrow frame. Target repo: `market-tick-data-service`.
