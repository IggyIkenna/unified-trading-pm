---
doc_type: issue
title: >-
  MDPS chain-bundle candle derivation crashed on native-datetime64 timestamp columns ("'>' not supported between
  instances of 'Timestamp' and 'float'") — fixed; blast-radius audit across venues/years still open
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
status: open
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
resolved_by:
locked_by:
depends_on: []
---

# MDPS chain-bundle candle derivation: Timestamp-vs-float compare crash (fixed) + blast-radius audit (open)

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

- [ ] [SCRIPT] P2. Grep prior `mdps-cefi-*`/`mdps-tradfi-*`/`mdps-defi-*` run.log archives (or the manifest's
      `attempted_failed` reason strings) for the exact `"not supported between instances of 'Timestamp' and 'float'"`
      signature to size the historical blast radius, and re-trigger `record_failed`→retry (never a blind mass relaunch)
      for any shard whose failure resolves to this exact root cause.

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- 2026-08-12 (slot-3, agt-68d94a): diagnosed root cause from run.log, shipped the fix (`cc65f076ae`), relaunched the
  2019 CeFi shard with the fix live, filed this doc for the blast-radius follow-up.
