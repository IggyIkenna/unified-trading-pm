---
doc_type: issue
title: >-
  VIX futures backfill launch FAILED — 5/7 SPOT-preempted within minutes, 2/7 deleted mid-run with no completion marker;
  plus 2 code bugs (ts_event schema, chain-empty manifest write)
summary: >-
  Monitoring of the 7 VIX backfill VMs launched 2026-08-10 (this session) shows the launch did NOT complete: 5/7
  (`tradfi-bf-vix-light-{2021,2023,2024,2025,2026}-*`) were SPOT-preempted 2-6 minutes after insert (no log dirs at
  all); the other 2 (`2020`, `2022`) were deleted ~22-24 min after insert, mid-run, with NO completion marker (PROGRESS
  last_completed 2020-06-16 / 2022-01-14 — mid-year, not done). Only 25 raw VIX parquet files were written today total.
  The availability manifest shows 2020 VIX/CBOE with ZERO real captured rows (300 phantom captured, row_count=0); the
  real 2021-2026 captured rows in the manifest are from PRIOR backfills (07-21/27, 08-03/07/08), not this run. Two
  genuine code bugs confirmed on today's written files: (1) the VIX/CBOE ohlcv_1m parquet carries `ts_event` instead of
  canonical `timestamp` — "Schema validation FAILED" on every chunk, whereas prior-07-27 VIX and CME ES files carry
  `timestamp`; (2) every manifest write fails non-blocking with `MalformedRowKeyError: shard-atom field 'chain' was
  explicitly passed as empty` — so even successfully-downloaded VIX rows were never recorded in the manifest. The plan's
  done-when ("all 7 VMs confirmed completed + manifest shows real captured VIX/CBOE rows spanning 2020-01-01 through
  today") is NOT met. Fixing requires: correct the DatabentoAdapter schema mapping for CBOE/XCBF.PITCH ohlcv_1m
  (ts_event→timestamp), fix the futures_chain row_key to omit empty `chain`, and RELAUNCH the 7 years (on-demand or with
  a preemption-resilient strategy — SPOT lost 5/7 in minutes). Repo: market-tick-data-service (schema + manifest
  row_key), deployment-service (launcher).
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, vix, cboe, backfill, data-correctness, spot-preemption, schema, manifest]
related:
  - /plans/active/issues/tradfi_vix_full_history_backfill_2026_08_10.md
  - /plans/archive/issues/databento_concurrency_gating_audit_2026_08_09.md
  - /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md
  - /codex/02-data/tradfi-databento-sourcing-ssot.md
parent_epic: tradfi_master
source:
  "Monitoring of tradfi-bf-vix-light-{2020..2026}-20260810-13{1032,1055,1116,1136,1155,1218,1254} VMs (worker slot 12,
  dispatched from /plans/active/issues/tradfi_vix_full_history_backfill_2026_08_10.md, 2026-08-10)"
assigned_vm: planning
resolved_by:
locked_by:
created: 2026-08-10
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/tradfi_vix_full_history_backfill_2026_08_10.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py,
    deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh,
  ]
---

# VIX futures backfill launch FAILED

## What I found

Monitored the 7 VIX backfill VMs launched 2026-08-10 (per `tradfi_vix_full_history_backfill_2026_08_10.md`). GCP
operations log (all times UTC):

| VM (year) | insert   | outcome                                                                          |
| --------- | -------- | -------------------------------------------------------------------------------- |
| 2020      | 12:10:37 | delete op DONE 12:34:28 — run.log stops 12:34:39Z, mid-run, NO completion marker |
| 2021      | 12:10:59 | `compute.instances.preempted` 12:13:32 (SPOT, ~2.5 min) — no log dir             |
| 2022      | 12:11:19 | delete op DONE 12:35:31 — run.log stops 12:34:29Z, mid-run, NO completion marker |
| 2023      | 12:11:41 | `compute.instances.preempted` 12:13:40 (~2 min) — no log dir                     |
| 2024      | 12:12:00 | `compute.instances.preempted` 12:13:28 (~1.5 min) — no log dir                   |
| 2025      | 12:12:30 | `compute.instances.preempted` 12:13:39 (~1 min) — no log dir                     |
| 2026      | 12:12:57 | `compute.instances.preempted` 12:15:59 (~3 min) — no log dir                     |

- **5 of 7 were SPOT-preempted within 1-3 minutes of insert** (2021, 2023, 2024, 2025, 2026). No `vm-logs` dir exists
  for any of them. The launcher defaults to SPOT (`--provisioning-model=SPOT --instance-termination-action=DELETE`); the
  databento concurrency audit cleared the _Databento per-IP_ constraint but GCP SPOT preemption is a separate, uncounted
  risk — 5/7 reaped immediately.
- **The other 2 (2020, 2022) were deleted ~22-24 min after insert, mid-run, with NO completion marker.** Their `run.log`
  files end abruptly at 12:34-12:35Z at a `RESOURCE_SAMPLE`/`PIPELINE_HEARTBEAT` boundary (no `ALL_DONE`/shutdown line).
  `PROGRESS.json` shows `last_completed_date` = **2020-06-16** and **2022-01-14** — i.e. partway through the year, not
  complete. The delete ops are `delete` (not a self-delete-on-completion which only fires after the chunk loop exits 0).
- **Only 25 raw VIX parquet files were written today** (15 for 2020, 10 for 2022), spanning a handful of dates (e.g.
  2020-06-17, 2022-01-13). The other 5 years wrote nothing today.
- **Manifest (availability_index.parquet)**: 2020 VIX/CBOE has **ZERO real captured rows** — 300 rows marked `captured`
  but ALL with `row_count=0` (phantom captured). Real captured rows (row_count>0) exist for 2021-2026 but their
  `written_at`/file mtimes trace to PRIOR backfills (07-21/27, 08-03/07/08), not this run. Min manifest date is
  2020-06-01 (UAC CBOE floor), max 2026-08-06.

## Why it matters

- The operator's scope decision ("VIX futures in scope until November, full 2020→today window") is **not served** — 2020
  has no real VIX data, and this launch contributed ~nothing.
- Two **code bugs** (confirmed on today's written files) would corrupt ANY successful relaunch, so fixing them is a
  prerequisite, not optional:
  1. **Schema regression — `ts_event` vs `timestamp`.** Today's VIX/CBOE ohlcv_1m parquet columns are
     `['ts_event', ..., 'available_at']` and
     `"Schema validation FAILED: venue=CBOE data_type=ohlcv_1m missing columns=['timestamp']"` fires on every chunk.
     Prior VIX files (2026-07-27) and CME ES files both carry `timestamp`. Repo: market-tick-data-service
     (DatabentoAdapter CBOE/XCBF.PITCH mapping).
  2. **Manifest write fails — `chain` empty.** Every `record_captured` for this futures_chain/VIX shard fails
     non-blocking with `MalformedRowKeyError: shard-atom field 'chain' was explicitly passed as empty`. So even
     successfully-downloaded rows are never recorded → the manifest stays phantom/absent. Repo: market-tick-data-service
     (futures_chain row_key must omit `chain` when empty, matching `OnchainPerpBatchHandler._row_key`).

## Recommended decision

1. **Fix the schema bug** — make the VIX/CBOE (XCBF.PITCH) ohlcv_1m writer emit canonical `timestamp` (same as ES /
   prior VIX). Verify with a single-day force run.
2. **Fix the manifest row_key** — omit `chain` when empty for the non-per-chain futures_chain shard (there is already a
   passing test pattern for this: `test_row_key_omits_chain_when_empty`).
3. **RELAUNCH the 7 years** with a preemption-resilient strategy — `--on-demand` (cash cost, but this is a one-time
   6.5-year history load and the account is time-sensitive) or at least NOT a bare SPOT default that lost 5/7 in
   minutes. Reuse `launch-tradfi-backfill-vm.sh` with `--root-symbol VIX --tier light --year <y>`.
4. After completion, re-verify the manifest: `venue=='CBOE' AND underlying=='VIX'` with `capture_status=='captured'` and
   `row_count>0` for 2020-01-01..today.

## Todos

- [x] ✅ [DATA] P1. Fix DatabentoAdapter VIX/CBOE (XCBF.PITCH) ohlcv_1m schema mapping to emit canonical `timestamp`
      instead of `ts_event` (repo: market-tick-data-service) — today's files fail
      `Schema validation FAILED:     missing columns=['timestamp']`; prior-07-27 VIX + CME ES files carry `timestamp`. —
      market-tick-data-service@dcd3b7c401 (restore ts_event→timestamp dual-write copy in `_COLUMN_ALIASES`; source
      `ts_event` preserved for MDPS priority-3 readers, `timestamp` copy satisfies
      `_TICK_REQUIRED_COLUMNS["ohlcv_1m"]` + pre-Phase-4 on-disk corpus; QG green)
- [x] [DATA] P1. Fix futures_chain manifest `record_captured` row_key to omit `chain` when empty (repo:
      market-tick-data-service) — currently every VIX shard write fails `MalformedRowKeyError: chain explicitly empty`,
      so captured rows never reach the manifest. — market-tick-data-service@f0345e7df4 (omit empty chain from the
      nontrade-sentinel row_key + 3 regression tests locking in the bundle-path omit-when-empty fix)
- [x] ✅ [SCRIPT] P1. RELAUNCH the 7-year VIX futures backfill (2020-2026, CBOE/ohlcv_1m) on-demand or with a
      preemption-resilient strategy after the two code fixes land (repo: deployment-service) — the 2026-08-10 SPOT
      launch lost 5/7 VMs to preemption within minutes and the other 2 were deleted mid-run with no completion. — All 7
      VMs relaunched on-demand (`tradfi-bf-vix-light-{2020..2026}-20260810-172*`, deployment-service, zone
      asia-northeast1-c) and verified RUNNING past the prior 3.5-min kill window (10 min, 0 deletes). Two ADDITIONAL
      root causes beyond the issue's 2 bugs were found + fixed during this relaunch: (a) deployment-service@98ec8ddb —
      the deployed vm-zombie-watchdog killed every tradfi-bf-vix-light VM as `tardis_cap_violation` (the name matches
      the legacy Tardis name-pattern fallback, but these are Databento VMs) — fixed by honoring an explicit
      `VM_TARDIS_CONSUMER=0` opt-out in both guards + stamping it in launch-tradfi-backfill-vm.sh, watchdog VM
      relaunched; (b) market-tick-data-service@e14f358b — `_write_bundle_shard_row` passed no `source=` to
      `record_captured_from_counts`, so the multi-source (tradfi, ohlcv_1m) manifest write failed non-blocking and
      captured rows were never recorded — now passes `source=latency_source` (=databento). Verified live:
      `2026-01-02 VIX ohlcv_1m captured row_count=4183 source=databento` in the per-VM manifest shard, 0 schema
      validation failures, parquet carries canonical `timestamp` + `ts_event`. Both fixes QG-green + quickmerged; mtds
      tarball rebuilt at e14f358b.
- [x] ✅ [DATA] P2. **DONE 2026-08-10 (slot-27, data_engineering).** After relaunch, verified the manifest shows real
      captured VIX/CBOE rows (row_count>0). **Evidence**: all 7 VMs RUNNING (created 17:21-17:23 UTC, actively
      processing); 2020 per-VM manifest has 28 unique dates (2020-06-01→2020-07-09 and counting) with 170K row_count,
      source=databento — 2020 was the primary gap (previously 0 real rows, 300 phantom). Schema fix verified: parquet
      files carry both canonical `timestamp` AND `ts_event` (not ts_event-only). Consolidated manifest
      (`_index/availability_index.parquet`) shows 7,595 real captured rows (24.7M row_count) spanning 2020-06-01 (UAC
      CBOE floor) to 2026-08-06; 2024 gap (only Jan-Feb in prior data) being filled by the currently-running 2024 VM.
      Backfill is IN PROGRESS, not terminal — the 7 on-demand VMs are ~1h into a multi-hour full-history run. No code
      shipped (verification-only task).

- [ ] [DATA] P3. After all 7 VIX backfill VMs reach terminal completion (STOPPED/TERMINATED with EXIT_STATUS=0 or
      self-deleted), re-verify the consolidated manifest covers the full 2020-06-01→today window with real captured rows
      (row_count>0) across all years. Per-VM manifests already show data flowing; this is the terminal gate. (repo:
      market-tick-data-service)
- [x] ✅ [DATA] P0. **DONE 2026-08-10 (main, Claude Code session) — the `market-tick-data-service@e14f358b` source=
      kwarg bug (todo above) is NOT VIX-specific: it hit 6 CME futures roots too, one of them still actively failing
      live when found.** Checked every `tradfi-bf-cme-ohlcv-1m-*` VM launched today (19 total, all pre-fix, 12:07-15:07
      UTC — the 20-min fix landed at 16:56 UTC) for the same
      `Manifest write failed... Multi-source manifest write     missing required source= kwarg` warning: **6 affected**
      — `BTC-2021` (18 occurrences), `GC-2020` (119, still RUNNING and actively re-hitting it when found), `HG-2020`
      (12), `MET-2025` (47), `NG-2020` (10), `SI-2020` (28). 13 others clean (the bug is per-underlying nondeterministic
      within the same shared code path, not universal). **Action taken**: killed the still-running `GC-2020` VM
      (`gcloud compute instances delete`, stopping the waste immediately); relaunched all 6 via
      `launch-tradfi-bf-cme-ohlcv-1m.sh --only-root <ROOT> --year <YEAR>` (dry-run verified identical VM-name/date-range
      targeting first). All 6 confirmed RUNNING with the fixed code — 0 manifest- write-failure occurrences on the
      relaunches (checked `GC-2020`'s new run.log directly), real manifest rows landing
      (`Manifest updated: date=2020-01-06 ... complete=True`). No separate "manifest rebuild" tool was needed —
      relaunching with the fixed code IS the rebuild mechanism: the buggy writes left the affected dates' manifest rows
      genuinely absent (not just stale), so the launcher's existing skip-if-captured pre-flight check correctly treats
      them as real gaps needing a fetch, while dates that were never affected stay untouched. **Blast-radius check
      across other asset groups (operator ask)**: sports and defi adapters have ZERO chain-bundle
      (`futures_chain`/`options_chain`) manifest-write code path at all — architecturally cannot hit this bug, no
      further action. CEFI's Tardis adapter (`tardis_cefi_shards.py`) DOES route through the same shared
      `manifest_finalize._write_bundle_shard_row` function — checked all 4 `cefi-queue-heavy-binancefutu-*` backfill VMs
      from the last 2 weeks (2026-07-27 through 2026-08-09): **0 occurrences** — CEFI's chain-bundle cells are
      registered single-source in UAC SOURCE_PRIORITY, so they never hit the "must pass source=" requirement this bug is
      gated on. No CEFI/sports/defi manifest rebuild needed. Repo: deployment-service (relaunch),
      market-tick-data-service (bug already fixed by slot-16, this todo is the blast-radius sweep + CME remediation).

## Progress Log

- 2026-08-10 (slot-27, data_engineering): todo 4 (verify manifest after relaunch). Verified all 7 VMs RUNNING
  (tradfi-bf-vix-light-{2020..2026}, created 17:21-17:23 UTC, ~1h in). 2020 per-VM manifest (28 chunks so far) shows 28
  unique dates (2020-06-01→2020-07-09, 170K row_count, source=databento) — the primary gap (0 real 2020 rows
  pre-relaunch) is closed. Schema fix confirmed: parquet carries both `timestamp` AND `ts_event`. Consolidated manifest
  (`_index/availability_index.parquet`) has 7,595 real captured VIX/CBOE rows (24.7M row_count) from 2020-06-01 (UAC
  CBOE floor) to 2026-08-06. 2024 was sparse in prior data (Jan-Feb only) — the 2024 VM is now running and filling it.
  All data source=databento, pipeline_mode=batch_databento. No code changes needed (verification-only). Backfill is IN
  PROGRESS — VMs will need several more hours to complete the full 7-year window.

- **context-scout 2026-08-14**: populated context_scope (4 entries).
