---
doc_type: issue
title:
  "features-service pipeline_e2e_check.py's --require-captured let a TRADFI:delta_one shard through with genuinely
  missing MDPS processed_candles input, wasting a VM launch on a predictable dependency failure"
summary:
  "Running /data-pipeline-check-features for delta_one:TRADFI (day=2026-07-19, auto-day-slid to 2026-07-18..2026-07-19)
  with --require-captured --auto-day, the driver proceeded to launch a real force-leg VM. The VM's own internal
  dependency check immediately failed: market-data-processing-service output missing at
  gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-18/ (No data for
  2026-07-18/TRADFI). Both force and skip legs recorded vm_not_success (exit=1) — an honest failure signal, not a false
  pass, but --require-captured's whole purpose is to skip cells like this BEFORE spending VM time, and it didn't."
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, require-captured, mdps-dependency, honest-absence, vm-spend]
related: [data_pipeline_check_mdps_features_2026_07_20]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source: "todo 9b full-matrix run (/data-pipeline-check-features), slot-3, 2026-07-27"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# require-captured missed a TRADFI candle gap that the VM's own dependency check caught (2026-07-27)

## What happened

`cd features-service && python3 scripts/pipeline_e2e_check.py --day 2026-07-19 --family delta_one --asset-group TRADFI --legs force,skip --require-captured --auto-day`
launched a real VM (`features-e2e-tradfi-20260727-103425-2b064d`) rather than skipping with
`no_captured_input_for_window` (which is exactly what happened for DEFI and PREDICTION in the same run). The VM's
`run.log`:

```
ERROR DEPENDENCY CHECK FAILED
ERROR Missing: market-data-processing-service
ERROR   Path: gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-18/
ERROR   Reason: No data for 2026-07-18/TRADFI
```

The skip-leg VM (`features-e2e-tradfi-20260727-103823-2b064d`) hit the identical failure a few minutes later, since the
input gap didn't change.

## Why this matters

- `--require-captured`'s entire purpose (per the skill's own docs) is "skip unprovable ones instead of launching a VM
  that can only produce a false no-output failure" — it worked correctly for DEFI/PREDICTION but not TRADFI. Two
  possible root causes, not yet distinguished:
  1. **Phantom-capture on TRADFI candles**: the availability-index/manifest row(s) `--require-captured` reads say
     `captured` for the window, but the physical `processed_candles/by_date/day=2026-07-18/` object doesn't exist — the
     same "manifest says captured, GCS object missing" failure class documented elsewhere this session for other shards.
  2. **Coverage-check granularity gap**: `--require-captured`'s window check may pass on _some_ canonically-shaped
     TRADFI candle rows existing somewhere in the lookback window without verifying the _exact_ date/path the runtime
     dependency check requires. Not investigated further here — flagging as a real finding, not chasing root cause under
     time pressure mid a 29-cell matrix run.
- Real (small) VM spend wasted on a call that was always going to fail. On a full production-scale sweep, an uncaught
  version of this class of gap multiplied across many shards is real cost, not just an annoyance.

## Todos

- [ ] [SCRIPT] P2. Compare `--require-captured`'s coverage-check query against the exact
      `market-data-processing-service` dependency-check path/date the runtime check enforces for TRADFI candles —
      confirm whether this is phantom-capture (manifest row without object) or a coverage-check granularity gap, then
      fix at the root (either the manifest/GCS divergence, or require-captured's query).
- [ ] [DATA] P3. Re-run `/data-pipeline-check-features --family delta_one --asset-group TRADFI` once MDPS TRADFI candle
      backfill covers 2026-07-18 (or once the require-captured gap is fixed) to get a genuine force+skip proof for this
      shard.

## Progress Log

- 2026-07-27 (slot-7): **Independently corroborated on a THIRD occurrence.** The same full-matrix run (day=2026-07-05)
  hit the identical `DEPENDENCY CHECK FAILED — Missing market-data-processing-service` for `TRADFI:delta_one` at
  `gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-04/` — a THIRD distinct
  day (07-04 here, 07-18 in this doc's own finding) hitting the same TRADFI-candle coverage-check/dependency-check
  disagreement. Raises confidence this is a persistent gap, not a one-off manifest glitch for a single day. Folded into
  the broader multi-root-cause writeup (this is "Root cause A" there, alongside 5 sibling findings from the same run):
  `issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`. Not fixed by either session — this
  doc's own todo above remains the tracked fix; not duplicating a second fix-todo in the broader doc.
