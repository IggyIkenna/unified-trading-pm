---
title: "TradFi OHLCV backfill VMs OOM-crash-loop (~15GB) — per-date full-catalogue reload, NOT a databento hang"
created: 2026-06-24
parent_epic: tradfi_master
source:
  - market-tick-data-service/market_tick_data_service/engine/sentinels.py::_load_sentinel_catalogs
  - market-tick-data-service/market_tick_data_service/engine/cefi_catalog_reader.py::_load_latest_catalog
  - "serial-console (gc/es/6j/nyse-2024): repeated `Out of memory: Killed process (python)` anon-rss ~15.3GB"
locked_by: live-defi-rollout
priority: P0
status: active
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

**Root cause:** the per-date sentinel fan-out `_load_sentinel_catalogs(date)` calls
`catalog_list_instruments("cefi"/"defi"/"tradfi", date, date)` **once per date**, and the cefi pre-listing read once
more — and each call re-downloaded + re-parsed the **full rolled-up `catalog.parquet`** (cefi = **227,576 rows**, logged
twice per date as `cefi_catalog_reader: loaded 227576 catalogue rows`) with **no caching**. The catalogue file is
**date-INDEPENDENT** (one `prod/catalog.parquet` roll-up), so re-reading it per date is pure churn: over a multi-date
chunk the repeated pyarrow→pandas materialisations (≈4 large loads × 7 dates) accumulate RSS that pyarrow's memory pool
never returns to the OS → ~15 GB → OOM on the 16 GB box.

## Why it matters

- TradFi OHLCV backfill makes **zero net progress** — reap→relaunch→re-OOM forever (the band-aid auto-reaper just spins
  the loop on the unfixed code). May-23 critical-path data, `tradfi_master`.
- Same class as the 2026-06-22 sports OOM (exit 137, self-delete → looked like clean completion).
- The fleet monitor mis-attributed it to the databento hang; the issue doc
  `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` "[TRADFI] P1" dispatch hypotheses (stale-tarball /
  different-unbounded-call) were both wrong — it is a memory blow-up.

## Fix (shipped)

`market-tick-data-service` — instance-level memoisation of the rolled-up catalogue on the cefi/defi/tradfi readers
(registered once at orchestrator init, reused for every date). Load the parquet once per process; filter per-date on the
cached frame; a `None` result (catalog absent) is cached too. Cuts per-chunk catalogue loads ~4×7→~4 (first date only) —
a >7× memory-churn cut. Sports reader is exempt (it reads genuinely per-(day,league) small blobs, not a monolith).

- `cefi_catalog_reader.py` / `defi_catalog_reader.py` / `tradfi_catalog_reader.py`: `_load_latest_catalog` → memoising
  wrapper over `_download_latest_catalog`.
- Regression: `tests/unit/engine/test_catalog_reader_cache.py` — asserts the catalogue is downloaded exactly ONCE across
  a 7-date range and across `list_instruments` + `list_not_yet_listed`.

## Recommended decision

- [ ] [TRADFI] P0. Ship the catalogue-cache fix (market-tick-data-service), rebuild the mtds GCS tarball from clean LDR,
      reap the OOM-looping `tradfi-bf-*` VMs and relaunch on the fixed tarball, and run the tradfi OHLCV backfill to
      manifest-verified completion (captured rows climb, no OOM in serial console). Target repo:
      `market-tick-data-service`.
- [ ] [MONITOR] P2. **DEFERRED / NICE-TO-HAVE** — if heavy `.OPT` `ohlcv_1s` days still spike past 16 GB after the cache
      fix, bump the `launch-tradfi-bf-*` machine type to `e2-highmem-4` (32 GB) as defence-in-depth. Verify with serial
      console before/after; do NOT bump pre-emptively (the cache fix is the root-cause cure — throwing RAM at a leak
      masks it). Target repo: `deployment-service`.
