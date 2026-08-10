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

- [ ] [DATA] P1. Fix DatabentoAdapter VIX/CBOE (XCBF.PITCH) ohlcv_1m schema mapping to emit canonical `timestamp`
      instead of `ts_event` (repo: market-tick-data-service) — today's files fail
      `Schema validation FAILED:     missing columns=['timestamp']`; prior-07-27 VIX + CME ES files carry `timestamp`.
- [ ] [DATA] P1. Fix futures_chain manifest `record_captured` row_key to omit `chain` when empty (repo:
      market-tick-data-service) — currently every VIX shard write fails `MalformedRowKeyError: chain explicitly empty`,
      so captured rows never reach the manifest.
- [ ] [SCRIPT] P1. RELAUNCH the 7-year VIX futures backfill (2020-2026, CBOE/ohlcv_1m) on-demand or with a
      preemption-resilient strategy after the two code fixes land (repo: deployment-service) — the 2026-08-10 SPOT
      launch lost 5/7 VMs to preemption within minutes and the other 2 were deleted mid-run with no completion.
- [ ] [DATA] P2. After relaunch, verify the manifest shows real captured VIX/CBOE rows (row_count>0) spanning 2020-01-01
      through today — currently 2020 has zero real captured rows (300 phantom captured row_count=0).
