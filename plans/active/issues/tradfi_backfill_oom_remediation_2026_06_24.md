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
related: [/plans/archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md]
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
last_updated: 2026-08-01
context_scope:
  [
    /plans/epics/tradfi_master.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
  ]
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
- [x] ✅ [TRADFI] P2. **DONE 2026-07-27 (slot-14, data_engineering)** — memray'd the real per-date fetch/decode/write
      path (`market-tick-data-service@live-defi-rollout`, no code change — diagnostic only). **Top allocator is the
      "un-released pyarrow frame" half of the hypothesis, NOT the DBN decode half**: DBN/databento decode functions do
      not appear anywhere in the top-5 allocating call sites by size or by count.

      **Repro**: real live Databento credentials (Secret Manager `databento-api-key` via `unified-trading-sa`, no
                                                                                                                                                                                                                                                                                                                                                                      mocking) against `--asset-group tradfi --venues NYSE --data-types ohlcv_1m --source databento --force
                                                                                                                                                                                                                                                                                                                                                                      --start-date 2025-06-25 --end-date 2025-06-25`, writes routed to the `-test-` bucket
                                                                                                                                                                                                                                                                                                                                                                      (`IS_TEST_RUN=true`, `test_aware=True` bucket resolution — no prod writes). `memray run --native` wrapped the
                                                                                                                                                                                                                                                                                                                                                                      real CLI process (`python -m market_tick_data_service`, memray 1.19.3 installed ad hoc into `.venv` via `uv pip
                                                                                                                                                                                                                                                                                                                                                                      install` for this session only — not a pyproject dependency, not committed). Real fetch: 523 requested NYSE
                                                                                                                                                                                                                                                                                                                                                                      tickers (S&P500 + ETF universe minus the NASDAQ-classified subset) → 516 instruments actually traded that day →
                                                                                                                                                                                                                                                                                                                                                                      **208,627 total rows written across 516 per-symbol parquet partitions, 18.1 MB total output** (confirms the
                                                                                                                                                                                                                                                                                                                                                                      same "tiny output" shape as the documented ~1.3 MB/date case, just a different day/venue — most symbols wrote
                                                                                                                                                                                                                                                                                                                                                                      only tens-to-hundreds of 1-minute bars, e.g. `BNY`: 1 row, `EZET`: 5 rows).

                                                                                                                                                                                                                                                                                                                                                                      **Measured (memray's own allocator-level peak, not a `ps` sample)**: **peak RSS 2.899 GB**, 17,127,136 total
                                                                                                                                                                                                                                                                                                                                                                      allocations, 13.390 GB cumulative allocated — i.e. a **~164× memory-to-output amplification** on an ordinary
                                                                                                                                                                                                                                                                                                                                                                      (non-worst-case) trading day, the same phenomenon as the fleet's documented ~15 GB-vs-1.3 MB gap (~11,500×) at
                                                                                                                                                                                                                                                                                                                                                                      smaller absolute scale (this repro didn't hunt for the single worst historical day/product — see Follow-up
                                                                                                                                                                                                                                                                                                                                                                      below).

                                                                                                                                                                                                                                                                                                                                                                      **Top allocating call sites (`memray stats`)**:

                                                                                                                                                                                                                                                                                                                                                                      | Rank | Site                                                                 | Bytes   | Allocations |
                                                                                                                                                                                                                                                                                                                                                                      | ---- | -------------------------------------------------------------------- | ------- | ------------ |
                                                                                                                                                                                                                                                                                                                                                                      | 1    | `pyarrow/parquet/core.py:1180 write_table`                          | 2.518GB | 6,157,517    |
                                                                                                                                                                                                                                                                                                                                                                      | 2    | `pyarrow/pandas_compat.py:633 convert_column`                        | 1.128GB | 821,284      |
                                                                                                                                                                                                                                                                                                                                                                      | 3    | (native/opaque stack, unresolved)                                    | 835MB   | —            |
                                                                                                                                                                                                                                                                                                                                                                      | 4    | `pandas/core/internals/blocks.py:2661 get_values`                    | 622MB   | —            |
                                                                                                                                                                                                                                                                                                                                                                      | 5    | `typing.py:1028 __init__` (stdlib — generic/typing object churn)     | 566MB   | —            |

                                                                                                                                                                                                                                                                                                                                                                      By allocation **count** (not size), the same two sites dominate even harder — `write_table` (6.16M allocations,
                                                                                                                                                                                                                                                                                                                                                                      the single largest site both ways) and `write_chunk` itself (`unified_trading_library/io/streaming_writer.py:252`,
                                                                                                                                                                                                                                                                                                                                                                      1.85M allocations) — plus `numpy/_core/numeric.py:386 full()` (848,772) and
                                                                                                                                                                                                                                                                                                                                                                      `pandas/core/dtypes/cast.py:1207 maybe_infer_to_datetimelike` (846,112), both dtype-casting churn inside the
                                                                                                                                                                                                                                                                                                                                                                      pandas→arrow conversion.

                                                                                                                                                                                                                                                                                                                                                                      **Root cause, mapped to source**: `StreamingParquetWriter.write_chunk()`
                                                                                                                                                                                                                                                                                                                                                                      (`unified_trading_library/io/streaming_writer.py:206-253`) does `pa.Table.from_pandas(df, ...)` (line 221 →
                                                                                                                                                                                                                                                                                                                                                                      allocator site #2) then `self._writer.write_table(table)` (line 244 → allocator site #1, the single largest) on
                                                                                                                                                                                                                                                                                                                                                                      **every chunk of every per-symbol writer**. `PartitionedTickWriter` (`market-tick-data-service`
                                                                                                                                                                                                                                                                                                                                                                      `engine/orchestrator/partitioned_writer.py`) opens one such writer **per (instrument_type, data_type, symbol)**
                                                                                                                                                                                                                                                                                                                                                                      for non-derivative instrument types — i.e. up to 516 concurrently-tracked `StreamingParquetWriter` +
                                                                                                                                                                                                                                                                                                                                                                      `pq.ParquetWriter` instances for this one NYSE day alone. Each pyarrow `write_table()` call carries **fixed
                                                                                                                                                                                                                                                                                                                                                                      per-call C++ overhead** (schema resolution, dictionary-encoding buffers, zstd compressor context, column
                                                                                                                                                                                                                                                                                                                                                                      statistics collectors) that does **not scale down** for a symbol that only ever writes 1-5 rows that day — so
                                                                                                                                                                                                                                                                                                                                                                      the fixed per-writer/per-chunk cost, multiplied across hundreds of mostly-tiny per-symbol writers, dominates
                                                                                                                                                                                                                                                                                                                                                                      total transient RSS far more than the actual row/byte volume does. This is a genuinely different mechanism than
                                                                                                                                                                                                                                                                                                                                                                      "eager DBN decode buffering" (ruled out — decode functions don't show up in the top allocators at all); it is
                                                                                                                                                                                                                                                                                                                                                                      the **pyarrow write-path fan-out** exactly as the plan's own "un-released pyarrow frame" phrasing anticipated.

                                                                                                                                                                                                                                                                                                                                                                      **Follow-up not done here** (diagnostic-only scope, no code fix required per this todo's done-when): this
                                                                                                                                                                                                                                                                                                                                                                      repro used an ordinary NYSE day, not the fleet's actual worst-case (`gc-2025`, 60 OOM-kills at `e2-standard-4`).
                                                                                                                                                                                                                                                                                                                                                                      The worst-case's ~15GB peak is plausibly the SAME mechanism at a much larger scale (a genuinely liquid
                                                                                                                                                                                                                                                                                                                                                                      options-chain day, or a multi-day chunk accumulating across dates within one long-lived process — the existing
                                                                                                                                                                                                                                                                                                                                                                      `gc.collect()`+`malloc_trim(0)` per-date call in `tick_data_handler.py` was already added as a suspected
                                                                                                                                                                                                                                                                                                                                                                      cross-date mitigation) rather than a different bug; a fix (batching multiple symbols per `ParquetWriter`
                                                                                                                                                                                                                                                                                                                                                                      instance, or capping concurrently-open per-symbol writers) is future scoped work, not this todo's remit.
                                                                                                                                                                                                                                                                                                                                                                      Artifact: memray capture + flamegraph generated this session (`memray run --native` → `.bin`, `memray flamegraph`
                                                                                                                                                                                                                                                                                                                                                                      → `.html`); regenerate via the exact repro command above — the capture file itself is a session-scratch
                                                                                                                                                                                                                                                                                                                                                                      artifact, not committed (the measured numbers above are the durable record). Target repo:
                                                                                                                                                                                                                                                                                                                                                                      `market-tick-data-service`.

## 2026-07-31 finding — CBOE/VX calendar-spread per-row log-flood OOM (DP-VM-001, DIFFERENT mechanism, FIXED)

**DP_VM_EXIT_NONZERO escalation agt-1907b4** (slot-10, data_pipeline_failure): `tradfi-bf-cboe-ohlcv-1m-vx-2026-*` (the
CBOE/XCBF VX.FUT year-2026 shard) crash-looped **7 times in ~31h** (2026-07-30 00:10 → 2026-07-31 04:21), alternating
`exit_code=137` (OOM, 5x) and `125` (2x), **zero net progress** — `PROGRESS.json`'s `last_completed_date` bounced
non-monotonically across separate VM launches (2026-01-28 → 2026-07-15 → 2026-05-06 → 2026-02-25), i.e. each fresh VM
was NOT converging toward completion.

**Root cause — a DIFFERENT mechanism than the pyarrow-writer-fan-out documented above**: the target failure's `run.log`
tail was a dense flood of `DatabentoAdapter: cannot classify raw_symbol=... — row will be dropped` WARNING lines (30+
within an 8ms window at time of death) for CFE calendar-spread legs, e.g. `VX/H6:1:S - VX/J6:1:B`. Dropping these spread
legs IS the **intended** OHLCV-capture behaviour — confirmed by the pre-existing docstring on `VX_FUTURE_RE`
(`unified-api-contracts/.../databento_classifier_patterns.py`): "Calendar spreads (`VX/N6:1:S - VX/Q6:1:B`)... are then
dropped as non-classifiable legs, which is the intended behaviour for OHLCV capture." The BUG was operational, not a
classification gap: `_safe_classify` (`market-tick-data-service/.../databento_adapter.py`) logged a full WARNING **per
ROW**, and Databento streams a fresh row for every (spread-symbol, date, minute-bar) tuple across the whole ~200-day
backfill window — a bounded handful of distinct spread symbols, each hit up to millions of times. host_metrics_window on
the target VM showed LOW cpu (4-8%) and LOW mem (max 16% of the e2-highmem-16's 128GB) right up to the kill, consistent
with log-handler + GCS-tee buffering overhead (not the workload's actual data footprint) driving the OOM.

**Fix shipped 2026-07-31**: `market-tick-data-service@92037f45` — `_safe_classify` now warns once per distinct
unclassifiable `raw_symbol` per process, silently counting repeats (`_UNCLASSIFIABLE_SYMBOL_COUNTS`). No change to
classification/output semantics — rows are still dropped exactly as before, only the log volume is bounded.
`bash scripts/quality-gates.sh --no-fix` green; 2 new regression tests (`TestSafeClassifyUnclassifiableSymbolLogDedup`
in `test_databento_adapter_logic.py`).

**Relaunch NOT performed this session** — the runbook's bound (`/codex/15-runbooks/incidents/rb_infra_relaunch.md`: "if
it re-fails the SAME way twice... STOP relaunching, file an issue") was already exceeded (7 failures, far past
≤2/(vm-prefix,day)); blindly relaunching an 8th time before the fix landed would have just repeated the same OOM. Now
that the fix is shipped, the NEXT `tradfi-bf-cboe-ohlcv-1m-vx-*` relaunch (fresh registry-driven relaunch per the
runbook, or the standing `uts-prod-tradfi-wave-launcher` Cloud Run job's normal cadence) should be watched for a CLEAN
completion (no repeat OOM) to confirm — see todo below.

- [x] ✅ [INFRA] P1. **VERIFIED 2026-07-31 (slot-8, infra)** — the CBOE/VX log-flood OOM fix holds on a real relaunch.
      **Pre-flight**: confirmed `gs://deployment-scripts-central-element-323112/code/mtds-code.tar.gz` (rebuilt
      2026-07-31T05:06:01Z, manifest `commit_sha=55d051bd6e2a281d2d6d19cb890309bd7278eb9e`) has
      `market-tick-data-service@92037f45` as an ancestor (`git merge-base --is-ancestor` confirmed) — i.e. the fix is
      baked into the tarball every fresh VM boots from. The `tradfi-bf-cboe-ohlcv-1m-vx-2026-20260731-031156` run
      (launched 03:11:56Z, BEFORE the 04:48:58Z fix commit) still OOM'd (`exit 137`) — expected, it ran pre-fix code;
      not evidence against the fix. Relaunched via
      `bash deployment-service/scripts/vm/launch-tradfi-bf-cboe-ohlcv-1m.sh --year 2026`: - Attempt 1
      (`-20260731-053419`): SPOT-preempted at ~64s (`compute.instances.preempted`, unrelated infra churn, never reached
      the point of writing `run.log`) — not a genuine test, discounted. - Attempt 2 (`-20260731-053703`): STARTED
      confirmed <60s, ran clean through chunk 1/31 and into chunk 2/31 (`PROGRESS.json`:
      `last_completed_date=2026-01-07, monotonic=true`), processing REAL data (e.g. 2026-01-05: 16,229 records;
      2026-01-06: 15,865 records — not just idempotent skips). **Log-flood dedup directly confirmed on live data**: 23
      distinct unclassifiable VX calendar-spread `raw_symbol`s (`VX/F6:1:S - VX/G6:1:B` etc., spanning contract months
      F6→U6) each logged **exactly once**, every line carrying the fix's own suffix "further rows for this exact symbol
      are counted, not logged" — the pre-fix run's signature (same symbols repeating thousands of times within an 8ms
      window) did NOT recur. `RESOURCE_SAMPLE` RSS oscillated 4-16 GiB throughout (vs. the `e2-highmem-16`'s 128 GB
      ceiling) — no OOM, no `EXIT_STATUS` written, VM stayed `RUNNING`. **VERDICT: fix holds.** Full-corpus drain to
      100% (2026-01-01→2026-07-30) is a multi-hour campaign, same ownership pattern as the sibling P1 above — the
      standing `uts-prod-tradfi-wave-launcher` Cloud Run job continues it; no separate manual babysit-to-completion
      required. No code change needed this todo (92037f45 already shipped and verified). Target repo:
      `deployment-service` (relaunch, no diff) + `market-tick-data-service` (fix pre-shipped, verified live). Codex:
      `/codex/15-runbooks/incidents/rb_infra_relaunch.md`.

## 2026-08-01 finding — both offered pyarrow-writer-fan-out fixes carry unverified correctness risk; re-scoped into a research prerequisite + a gated implementation (NOT implemented this session)

**DP_VM_STALL/slot-10 pickup of the P3 above**: read `PartitionedTickWriter` (`partitioned_writer.py`) and
`StreamingParquetWriter` (`unified-trading-library/unified_trading_library/io/streaming_writer.py`) end-to-end plus the
real chunk-delivery path (`databento_fetch.py::_iterate_dbn_chunks` → `DBNStore.to_df(count=chunk_rows)` — Databento
streams rows in **time order across ALL requested symbols**, not grouped per-symbol, so a single symbol's rows CAN be
split across several separate `write_chunk()` calls over the life of one venue-date). Both options the P3 todo offered
turned out to carry real, unverified correctness risk that a single bounded pass should not decide unilaterally:

- **Option A (batch multiple symbols onto one shared `pq.ParquetWriter`)** breaks the documented **one-file-per-symbol**
  contract (`_resolve_writer_file_name`: `{SYMBOL}.parquet`, matching the live Databento/Yahoo-FX lane's canonical
  `instrument_id` filename stem). Nothing in this session's read confirmed whether every downstream reader
  (features-service, MDPS, BigQuery external tables, instruments-service) discovers tradfi/cefi single-instrument tick
  files by exact filename vs. directory glob — multi-symbol files would silently break an exact-filename reader.
- **Option B (cap concurrently-open writers, flush/close eagerly)** is unsafe as literally worded: `close()` uploads a
  FINAL parquet file to GCS (`_upload_to_gcs` is an idempotent **overwrite** of the fixed `gcs_path`). Since a symbol's
  rows can arrive in more than one `write_chunk()` call (confirmed above), evicting+closing a writer early and later
  reopening a fresh one for the SAME key would silently **overwrite and lose the earlier-flushed rows** — the opposite
  of "data pipeline correctness is the heartbeat". A safe version of "cap writers" needs either (a) proof that a
  symbol's rows are always time-contiguous within one venue-date (not verified — would need a live worst-case repro,
  which is exactly the "separately" ask below and is NOT safe to run inline on this shared host, see below), or (b) a
  multi-generation filename scheme (same downstream-reader blast-radius question as Option A).
- A third candidate (buffer/coalesce a key's chunks and flush once per key instead of once per `write_chunk()` call —
  same total row count, same file, same close-time, no layout change) is SAFE against data loss, but changes WHEN
  `StreamingParquetWriter.write_chunk()`'s pre-write validation (`_run_pre_write_checks`,
  `_assert_available_at_present`) fires — 6 existing unit test files (`test_partitioned_writer_cefi_available_at.py`,
  `test_partitioned_writer_cefi_chain_tail_v6.py`, `test_partitioned_writer_tradfi_filename_canonical.py`, others)
  assert the underlying writer's `write_chunk` is called **synchronously, once per top-level `write_chunk()` call** —
  deferring it would move validation-failure attribution away from the original chunk, a real observability regression
  for a data-pipeline that leans on "fail loud, attribute correctly" throughout.
- **Re-running the memray repro against the worst-case (`gc-2025`, 60 OOM-kills, ~15GB peak) was explicitly out of scope
  for this session** — `RULES.md` §1's memory-bounding HARD RULE (3 prior same-shape shared-host OOM incidents) bars
  running an unbounded subprocess that could plausibly reach double-digit-GB RSS directly on this shared planning host;
  it needs a dedicated VM or `run-bounded-analysis.sh`, not an inline session.

**Given `estimate_class: brand-new`/"deeper, durable fix" framing and NO live-correctness pressure (the doc's own words:
"Not required to unblock — the e2-highmem-4 bump already gives the practical margin")**, shipping either option
unverified in a single pass would trade a real (if modest) infra cost saving against a small but real chance of a silent
tick-data-loss regression in a live-trading pipeline. Re-scoped into two properly-bounded, individually AO-eligible
follow-ups below instead of one "either/or" design call. No code changed this session (diagnosis-only).

- [ ] [DATA] P3. **Determine whether any downstream reader of tradfi/cefi single-instrument tick parquet
      (`instrument_type=…/data_type=…/{SYMBOL}.parquet`) discovers files by exact filename vs. directory-glob** — grep
      `features-service`, `market-data-processing-service`, `instruments-service`, and any BigQuery external-table DDL
      for how they enumerate per-symbol tradfi/cefi tick objects. A checkable fact-finding task with a determinable
      yes/no outcome per reader; write the answer as a new dated finding in THIS issue doc. **Done-when (explicit oracle
      for the gated todo below, per operator 2026-08-01)**: a table enumerating EVERY downstream reader of these
      per-symbol tradfi/cefi tick files, one row per reader, columns
      `{reader (repo::module), discovery method (exact     filename / directory-glob / manifest-driven listing), verdict (safe for shared-writer batching Y/N)}`
      — no reader left unclassified. Target repos: `features-service`, `market-data-processing-service`,
      `instruments-service`.
- [ ] [TRADFI] P3. **Gated on the todo above.** If every reader glob-discovers files (safe for Option A) or if a
      multi-generation filename scheme is acceptable (safe for Option B), implement the corresponding fix in
      `PartitionedTickWriter`/`StreamingParquetWriter` per the analysis above, on a dedicated VM (never inline on the
      shared host) re-running the `gc-2025` worst-case memray repro to confirm peak RSS actually drops enough to revert
      the `e2-standard-4` machine-type bump. If no reader tolerates either layout change, keep the buffer/coalesce
      alternative instead (update the 6 unit tests listed above to assert on total accumulated rows / final file content
      rather than per-call `write_chunk` invocation count). Target repo: `market-tick-data-service`.

## 2026-07-31 finding — false-positive stall-kill on `tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-*` (DP-VM-001, THIRD distinct mechanism, NOT OOM, NOT the consolidator-lock-wait class — root cause not yet isolated)

**DP_VM_EXIT_NONZERO escalation agt-a10a13** (slot-14, data_pipeline_failure):
`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-120455` exited `137`, alert framed it as OOM. Durable GCS logs
(`vm-logs/<vm>/{EXIT_STATUS,LAUNCH_PARAMS.json,PROGRESS.json,run.log}` — survive self-delete) tell a DIFFERENT story
than either of the two mechanisms already documented above:

- **Not a real OOM.** `RESOURCE_SAMPLE` lines through the whole run show `rss` peaking at **~18.8 GiB out of the
  `e2-highmem-16`'s 128 GB** (mem% never exceeded ~17%) — nowhere near the machine ceiling. (Machine type is also
  confirmed further bumped since this doc's 2026-06-24/07-14 entries: `_tradfi-ohlcv-launcher-lib.sh:49` default is now
  `e2-highmem-16`, not `e2-highmem-4`.)
- **Not the 2026-07-30 consolidator-lock-wait class either** (`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md` UPDATE 2)
  — that class kills a VM that is genuinely IDLE waiting on a manifest-consolidator lock with zero output. This VM was
  NOT idle: chunks 16/17/18 (`2020-04-15..2020-05-05`) each completed in ~4-5 minutes with continuous real
  `StreamingParquetWriter: uploaded ...` / `DatabentoAdapter: streamed chunk ...` log lines throughout — genuine,
  ongoing forward progress right up to the kill.
- **The watchdog's own claim doesn't match the log**:
  `[vm-exec] WORKER_STALLED (no-progress-marker): no progress in 3927s (threshold=3900s)`. Directly measured (this
  session) the actual gap between consecutive lines matching `STALL_PROGRESS_REGEX="uploaded|streamed"`
  (`_tradfi-ohlcv-launcher-lib.sh:204`) across the ENTIRE 263k-line run.log: **max real gap = 232 seconds** — nowhere
  near 3900s. The watchdog (`vm-exec-with-gcs-tee.sh`'s `STALL_PROGRESS_REGEX` byte-offset tracking, lines 254-269)
  killed a VM that, by the log's own content, never actually stopped emitting matching progress lines for more than 4
  minutes at a stretch.
- **Root cause NOT isolated this session** — the per-tick trace that would show exactly where `made_progress`/
  `cur_size`/`last_progress_size` diverged from reality (`$WATCHDOG_HEARTBEAT="/tmp/vm-exec-$$.watchdog_alive"`) is
  **local-only, never uploaded to GCS**, and was lost when the VM self-deleted — so the exact defect in the byte-offset
  bookkeeping (line 254-269 of `vm-exec-with-gcs-tee.sh`) could not be pinned post-hoc. Ruled out as a candidate:
  `heartbeat_daemon.py` / UTL `unified_trading_library/lifecycle/uploader.py` reads+uploads `local_log` via
  `read_bytes()` on each cycle without truncating it, so local-log truncation-vs-stale-offset is NOT the mechanism
  either. This is a genuinely open question, not a guessed fix.
- **Why it matters**: this is the SAME VM family (`tradfi-bf-cme-ohlcv-1m-*`) as the already-fixed 2026-07-30
  consolidator-lock-wait class and shares the same symptom (`WORKER_STALLED (no-progress-marker)`, exit 137) but is a
  DIFFERENT, still-open bug that can false-positive-kill a VM that IS making real progress, mid-backfill, wasting the VM
  cost and delaying completion — a genuine (if smaller-scale) instance of the workspace's billing-waste concern
  (`/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`). A full-year CME backfill needs 4+ hours
  (53 chunks × ~5 min); this VM only reached chunk 18/53 (~87 min) before the false kill, so a relaunch has multiple
  more chances to hit the same false-positive before completing.

**Action taken**: relaunched per `/codex/15-runbooks/incidents/rb_infra_relaunch.md` (bound not exceeded — this was the
only escalation-driven relaunch of this exact VM-prefix found in `gcloud compute operations list` for today; other
same-prefix launches in the operations history are the standing `uts-prod-tradfi-wave-launcher` Cloud Run job's normal
~2-3h cadence, not escalation relaunches).
`bash deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh --only-root ES --year 2020` (`--dry-run` first
confirmed identical scope to the failed VM: `venue=CME 2020-01-01..2020-12-31 instruments=ES.FUT;ES.OPT`) →
`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-134654`, confirmed `RUNNING` immediately, `DEPLOYMENT_STARTED` in
`run.log` at T+44s (well within the runbook's T+60s bound), chunk 1/53 underway. `VM_FORCE=false` (unchanged from the
failed run's `LAUNCH_PARAMS.json`) means the per-VM manifest shard's skip-if-fresh logic will not redo already-captured
dates, so no wasted duplicate work from the relaunch.

- [ ] [CODE] P1. **Isolate the exact defect in `vm-exec-with-gcs-tee.sh`'s `STALL_PROGRESS_REGEX` byte-offset
      bookkeeping (lines 254-269)** that let a VM emitting real progress lines every ≤232s get killed for an alleged
      3927s of silence. Candidate next step: make `$WATCHDOG_HEARTBEAT` (currently local-only,
      `/tmp/vm-exec-$$.watchdog_alive`) durable (tee to GCS alongside `run.log`) so the next occurrence's per-tick
      `cur_size`/`last_progress_size`/`made_progress` trace survives VM self-delete for post-hoc diagnosis, since this
      session's attempt to root-cause it after the fact was blocked by exactly that gap. Target repo:
      `deployment-service`.
- [ ] [DATA] P2. **Watch the 2026-07-31T13:46Z relaunch (`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-134654`) to
      completion** — if it ALSO false-stall-kills before finishing the 2020 year-shard, that's a second data point
      strengthening the P1 above and would exceed this VM-prefix's `≤2/day` relaunch bound (STOP further blind
      relaunches at that point per the runbook, escalate instead). Target repo: deployment-service.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **slot-10 2026-08-01**: picked up the pyarrow-writer-fan-out P3 todo; diagnosed both offered fixes as carrying
  unverified data-loss/downstream-breakage risk (see finding above), re-scoped into a research-prerequisite todo + gated
  implementation todo instead of shipping either unverified. No code changed.
- **slot-10 2026-08-01**: `/blocked` BLK-1434c791 answered by main — DECISION A confirmed (re-scope was correct per the
  dispatch-scope-eligibility + data-pipeline-correctness-heartbeat + memory-bounding HARD RULES, not a discretionary
  call). Sharpened the research-prereq todo's done-when into an explicit per-reader table oracle (reader / discovery
  method / batching-safe verdict) per main's follow-up ask.
