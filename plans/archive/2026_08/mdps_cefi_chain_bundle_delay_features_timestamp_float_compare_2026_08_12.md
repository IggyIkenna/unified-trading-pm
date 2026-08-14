---
doc_type: issue
title: >-
  MDPS chain-bundle candle derivation crashed on native-datetime64 timestamp columns ("'>' not supported between
  instances of 'Timestamp' and 'float'") — fixed; blast-radius audit CONTAINED to the already-fixed shard, resolved
summary: >-
  DP-VM-001 (`DP_VM_EXIT_NONZERO`, exit_code=1) fired for `mdps-cefi-2019-20260810-023141` (the CeFi 2019 year-shard of
  `launch-mdps-sharded-backfill.sh`). Diagnosed via the archived `run.log`:
  `CefiTradesAdapter._calculate_delay_features`
  (`market_data_processing_service/app/adapters/cefi/trades_adapter.py:529`, pre-fix) compared
  `tick_data[exchange_ts_col].max() > 1e15` to auto-detect µs-vs-ns epoch scale, assuming the
  `timestamp`/`local_timestamp` columns always hold a raw numeric epoch. For the DERIBIT chain-bundle read path
  (`ticks.parquet` futures/options bundle, read via `pl.scan_parquet(...).to_pandas()`), those columns arrive as native
  pandas `datetime64` instead, so the comparison raised `TypeError: '>' not supported between instances of 'Timestamp'
  and 'float'` for every timeframe (15s/1m/5m/15m/1h/4h/24h), causing `cefi/trades/FUTURE: ALL FAILED` +
  `cefi/liquidations/PERPETUAL: ALL FAILED` and 241 "Handler returned non-zero exit code: 1" lines, which exited the VM
  1. Fixed by normalizing any datetime64-dtype column to int64 nanoseconds before the scale heuristic runs
  (`market-data-processing-service@cc65f076ae`), with regression coverage for both the all-datetime64 and mixed-dtype
  cases. The 2019 CeFi shard was relaunched with the fix live (root-cause-diagnosed carve-out — see
  `/codex/15-runbooks/incidents/rb_infra_relaunch.md` § Bounds). Open: this helper is shared, not chain-bundle-specific
  — it plausibly affects any venue/asset_group whose `trades` chain-bundle carries a native-datetime `timestamp` column
  and lacks `ts_event` (one `BITFINEX-FUTURES` line also appeared in this VM's error log), so prior CeFi backfill runs
  across other venues/years may have silently hit the same crash without anyone having traced it to this exact line
  before.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [cefi, mdps, dp-vm-001, timestamp, chain-bundle, candle-derivation, data-pipeline]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /plans/epics/mtds_mdps_master.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /plans/epics/mtds_mdps_master.md,
    market-data-processing-service/market_data_processing_service/app/adapters/cefi/trades_adapter.py,
  ]
created: "2026-08-12"
author: slot-3
priority: P2
parent_epic: mtds_mdps_master
source: >-
  DP-VM-001 escalation agt-68d94a (data_pipeline_failure worker, wall_type=data_pipeline_failure, repository_dispatch
  escalate-to-orchestrator) for VM mdps-cefi-2019-20260810-023141, exit_code=1. Diagnosed by reading the VM's archived
  run.log via UTL StorageClient
  (`gs://deployment-scripts-central-element-323112/vm-logs/mdps-cefi-2019-20260810-023141/run.log`) and tracing the
  exact comparison via a dedicated sub-agent read of market-data-processing-service source.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: fix
estimate_class: bug
estimate_baseline: 0.3
calibrated_ai_days: 0.3
assigned_role: data
resolved_by: slot-30
locked_by:
depends_on: []
---

# MDPS chain-bundle candle derivation: Timestamp-vs-float compare crash (fixed) + blast-radius audit (open)

> **🟢 ARCHIVED 2026-08-14 — RESOLVED** (status: resolved, all todos `[x]`, unlocked). Archived by slot-30 (data). Both
> the fix (`market-data-processing-service@cc65f076ae`) and the blast-radius audit
> (`market-data-processing-service@4cd46c17ba`) are shipped — see Progress Log for the full grep/manifest-cross-check
> evidence, plus `agt-87339b`'s independent 2026-08-14 second-instance relaunch. No successor doc; this issue is fully
> closed, not superseded.

## Evidence

**run.log** (`gs://deployment-scripts-central-element-323112/vm-logs/mdps-cefi-2019-20260810-023141/run.log`,
`EXIT_STATUS`="1"):

```
ERROR    [trades] DERIBIT:PERPETUAL:ETH-USD@INV: 15s: '>' not supported between instances of 'Timestamp' and 'float'; 1m: ...; 5m: ...; 15m: ...; 1h: ...; 4h: ...; 24h: ...
ERROR    [trades] DERIBIT:PERPETUAL:BTC-USD@INV: 15s: '>' not supported ... (same, all 7 timeframes)
ERROR    [trades] DERIBIT:FUTURE:BTC-USD@INV-20191227: 15s: '>' not supported ... (same, all 7 timeframes)
ERROR    cefi/liquidations/PERPETUAL: ALL FAILED (2/2)
ERROR    cefi/trades/FUTURE: ALL FAILED (4/4)
ERROR Handler returned non-zero exit code: 1   [x241 across the run]
```

## Root cause

`CefiTradesAdapter._calculate_delay_features` (`trades_adapter.py:513`, pre-fix) resolved
`exchange_ts_col`/`local_ts_col` via `_detect_delay_columns` (priority: `ts_event`/`timestamp`,
`ts_init`/`local_timestamp`), then ran a µs-vs-ns scale heuristic:

```python
divisor = 1_000_000 if tick_data[exchange_ts_col].max() > 1e15 else 1_000
```

This assumes the resolved column is always a raw numeric epoch. For the per-symbol trades files that holds — `timestamp`
is a plain int64 epoch column matching Tardis' CSV convention. For the chain-bundle read path (`ticks.parquet` DERIBIT
futures/options bundle, streamed via `pl.scan_parquet(...).to_pandas()` in `live_workers_streaming.py`), the source
`timestamp` column is a native Polars `Datetime`, which `.to_pandas()` turns into pandas `datetime64[ns]` — so `.max()`
returns a `pandas.Timestamp`, and `Timestamp > 1e15` raises `TypeError`. This fired for every timeframe because
`_streaming_process_slice_timeframes` re-enters the `seed + process_to_candles` branch per timeframe when `base_candles`
stays `None` after the base (15s) timeframe's exception.

## Fix (shipped)

`market-data-processing-service@cc65f076ae` — normalize any `datetime64`-dtype column to int64 nanoseconds before the
scale heuristic runs (both `exchange_ts_col` and `local_ts_col` checked independently, since one side can be numeric
while the other is native-datetime). Regression coverage added in
`tests/unit/test_hft_features.py::TestDelayFeaturesDatetimeColumns` for the all-datetime64 and mixed-dtype cases.
`quality-gates.sh` green (sentinel `a959bd0192dea464e43ed0117f87f9c301f5bd08`).

## Relaunch (root-cause-diagnosed carve-out)

Per `/codex/15-runbooks/incidents/rb_infra_relaunch.md` § Bounds, the ≤2/(vm-prefix,day) relaunch cap resets when a
relaunch is root-cause-diagnosed with a shipped fix live for the first time — this is that case (`mdps-cefi-` had 0
relaunches on 2026-08-12, the original failure was 2026-08-10). Relaunched `cefi --year 2019` via
`deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh` with the fix live; see the worker's `/done` evidence for
the new VM name + STARTED verification.

## Recommended decision — blast-radius audit (open, not yet done)

`_calculate_delay_features` is a shared helper, not chain-bundle-specific — the same crash plausibly hit **any**
venue/asset_group whose `trades` chain-bundle read carries a native- datetime `timestamp` column and lacks `ts_event`
(this VM's error log also had one `BITFINEX-FUTURES` line, not just DERIBIT). Prior CeFi backfill runs across other
venues/years may have silently hit this same crash and been miscounted as generic failures rather than traced to this
line.

- [x] ✅ [SCRIPT] P2. Grep prior `mdps-cefi-*`/`mdps-tradfi-*`/`mdps-defi-*` run.log archives (or the manifest's
      `attempted_failed` reason strings) for the exact `"not supported between instances of 'Timestamp' and 'float'"`
      signature to size the historical blast radius, and re-trigger `record_failed`→retry (never a blind mass relaunch)
      for any shard whose failure resolves to this exact root cause. — market-data-processing-service@4cd46c17ba +
      evidence below. Blast radius CONTAINED to the already-fixed shard; no further retry action needed (see Progress
      Log).

## Progress Log

- **data_pipeline_failure agt-87339b 2026-08-14**: a SECOND, separate 2019 CeFi year-shard —
  `mdps-cefi-2019-20260810-035109` (launched 2026-08-10 03:51, ~80min after this issue's original `...-023141` VM, so
  pre-dates the fix) — hit the identical `TypeError: '>' not supported between instances of 'Timestamp' and 'float'` on
  its LAST processed date (2019-12-31, the final date in its 365-day range), for `[trades] BITFINEX-FUTURES/DERIBIT`
  (7/7 timeframes each) and `[liquidations] BINANCE-FUTURES:PERPETUAL` (candle-write failures) — 12 errors, 21/33
  succeeded, `exit_code=1`, DP-VM-001 escalation. Confirmed via `run.log`
  (`gs://deployment-scripts-central-element-323112/log-archive/final/mdps-cefi-2019-20260810-035109/run.log`) this is
  the SAME root cause as above (`_calculate_delay_features`'s µs-vs-ns scale heuristic on a native-`datetime64` column)
  — the fix (`market-data-processing-service@cc65f076ae`) was already live in this repo, this VM simply pre-dated it.
  Per RB-INFRA-RELAUNCH's root-cause-diagnosed carve-out (root cause already diagnosed + fix already shipped + this is
  the first relaunch of `mdps-cefi-` TODAY with the fix live), relaunched `cefi --year 2019` as
  `mdps-cefi-2019-20260814-193801` (`launch-mdps-sharded-backfill.sh`, presence-skip will fast-skip the already-captured
  days and only reprocess 2019-12-31). Verified STARTED@T+60s (`gcloud compute instances describe` = RUNNING) and
  PROGRESS@T+10min (serial console showed live tarball-deploy sequence advancing, not stalled) — did not wait for the
  full multi-hour run to complete; the standing DP-VM fleet monitor will catch and re-escalate if this relaunch also
  fails. This is now the SECOND confirmed instance of the blast-radius concern below (a pre-fix VM hitting the same
  crash) — reinforces that the P2 blast-radius audit todo is worth doing, not just theoretical.

- **slot-30 2026-08-14** (this todo — blast-radius grep + retry check):
  - **Manifest leg** (`attempted_failed` reason strings): ran
    `instruments-service --operation reprocess-shards --asset-group {cefi,tradfi,defi} --capture-status attempted_failed --error-reason-contains "not supported between instances of 'Timestamp' and 'float'"`
    (dry-run) — **0 of 85,064 / 27,516 / 138,327 rows matched**, in all three asset groups. Root cause: the crashing VMs
    exited non-zero (`Handler returned non-zero exit code: 1`) before any per-shard `record_failed` call ever wrote this
    exact exception text into `error_reason` — the manifest genuinely has nothing to flip.
  - **run.log leg**: wrote + ran a one-off script
    (`market-data-processing-service/scripts/blast_radius_cefi_chain_bundle_timestamp_float_2026_08_14.py`,
    `market-data-processing-service@4cd46c17ba`) that streams every archived
    `log-archive/final/mdps-{cefi,tradfi,defi}-*/run.log` durable snapshot (294 total: 22 cefi / 161 tradfi / 111 defi)
    via bounded ranged reads (files measured 700MB+ each — a plain full-object download+decode+splitlines would have
    materialized ~700MB+ per file in RAM on this shared host, so this streams in 8MB chunks with early-stop per file
    instead) and greps for the exact signature. **Result: 19 of 294 matched, and every single match is an
    `mdps-cefi-2019-*` VM** (0 tradfi, 0 defi, 0 cefi outside the 2019 shard). All 19 are dated 2026-08-10/2026-08-11 —
    pre-fix relaunch attempts of the SAME `mdps-cefi-2019` singleton shard, all
    `DERIBIT:FUTURE:*-2019*`/`DERIBIT:PERPETUAL:*` chain-bundle instruments, matching the root cause exactly (2019 is
    the only CeFi year whose futures/perpetual data ships as a DERIBIT chain-bundle rather than per-symbol).
  - **Conclusion**: blast radius is CONTAINED to the single `mdps-cefi-2019` singleton shard — every one of the 19
    matched archives (including `...-035109`, the VM `agt-87339b`'s entry above independently escalated + relaunched as
    `mdps-cefi-2019-20260814-193801`) is a pre-fix relaunch attempt of that SAME shard; no other venue/year/asset_group
    ever hit this signature, live or in the manifest. **No further retry action beyond what's already landed above is
    warranted**: the shard already has two independent post-fix relaunches (`...-20260812` from the original incident,
    `...-20260814-193801` from `agt-87339b` today), and there is no OTHER shard anywhere in the fleet whose failure
    resolves to this root cause — a third relaunch of the same already-covered shard would be pure duplicate work. This
    satisfies the todo's "never a blind mass relaunch" instruction: the correct action here is confirming zero
    additional scope, not manufacturing a relaunch.

- **context-scout 2026-08-14**: populated context_scope (3 entries).

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- 2026-08-12 (slot-3, agt-68d94a): diagnosed root cause from run.log, shipped the fix (`cc65f076ae`), relaunched the
  2019 CeFi shard with the fix live, filed this doc for the blast-radius follow-up.
