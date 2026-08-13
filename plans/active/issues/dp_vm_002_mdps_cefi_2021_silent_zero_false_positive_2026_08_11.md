---
doc_type: issue
title:
  DP-VM-002 FALSE POSITIVE — VM mdps-cefi-2021-20260810-052119 wrote 21,847 POLARS AGGREGATED lines but classified
  SILENT (pre-fix _PROGRESS_RE gap)
summary: >-
  Escalation agt-b947d5: VM mdps-cefi-2021-20260810-052119 (MDPS CeFi 2021 sharded backfill) drained with manifest
  captured 0→0 and was classified GONE_NO_CAPTURE/SILENT by the exit-code fleet monitor. Direct GCS read of the
  persisted run.log (4.9MB, 34,329 lines) proves the VM wrote 21,847 POLARS AGGREGATED log lines (~11M candles across
  multiple instruments/timeframes for 2021-01-01 through 2021-01-04). The pre-fix `_PROGRESS_RE` regex did not include
  the `POLARS AGGREGATED` marker — this VM ran (05:24–07:15 UTC 2026-08-10) BEFORE the fix (commit `2f077c97`, slot 18,
  18:11 UTC same day) was deployed. Confirmed FALSE POSITIVE: candles ARE in GCS, the manifest shard was stranded on the
  killed VM's atexit. Fix is already in main — no code to ship. VM should be re-launched (killed mid-run, no
  EXIT_STATUS, real progress).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-data-processing-service]
scope: [engineer]
tags: [dp-vm-002, false-positive, mdps, cefi, polars-aggregated, already-fixed, relaunch-needed]
related:
  [
    /plans/active/issues/dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
source: dp-fleet-monitor
resolved_by: ""
locked_by: ""
created: 2026-08-11
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: small
estimate_baseline: 0.05
calibrated_ai_days: 0.05
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

## What I found

**DP-VM-002 CRITICAL alert `agt-b947d5` for `mdps-cefi-2021-20260810-052119` is a FALSE POSITIVE.**

Direct GCS read of `gs://deployment-scripts-central-element-323112/vm-logs/mdps-cefi-2021-20260810-052119/run.log`:

| Signal                            | Value                                                              |
| --------------------------------- | ------------------------------------------------------------------ |
| Run.log size                      | 4,932,576 bytes (4.9 MB)                                           |
| Total lines                       | 34,329                                                             |
| **POLARS AGGREGATED count**       | **21,847**                                                         |
| First POLARS AGGREGATED at offset | 12,177 (within first ~100 lines)                                   |
| Last POLARS AGGREGATED at offset  | 4,925,302 (near end)                                               |
| EXIT_STATUS blob                  | Absent (VM killed, never wrote terminal marker)                    |
| PREEMPTED blob                    | Absent (not a SPOT preemption)                                     |
| Last heartbeat                    | 2026-08-10T07:14:33Z                                               |
| Processing window                 | 05:24 → ~07:15 UTC (~110 min), dates 2021-01-01 through 2021-01-04 |

The VM processed 1,234 instruments across `trades`, `liquidations`, `options_chain`, `futures_chain`,
`derivative_ticker`, `book_snapshot_5` data types, producing ~11M candles. The `📊` progress tracker line shows
"10,963,262 candles" for `options_chain` alone on 2021-01-04.

Run.log excerpt (typical POLARS AGGREGATED pattern — present from start to end):

```
2026-08-10 05:26:08,235 INFO POLARS AGGREGATED: 1440 1m candles (end-of-period timestamps preserved)
2026-08-10 05:26:08,278 INFO POLARS AGGREGATED: 288 5m candles (end-of-period timestamps preserved)
...
2026-08-10 07:14:33,868 INFO POLARS AGGREGATED: 1 24h candles (end-of-period timestamps preserved)
```

## Why it matters

The pre-fix `_PROGRESS_RE` in `deployment_service/data_pipeline_monitors/_gcs.py` did not include the
`POLARS AGGREGATED` marker — the run.log signal that MDPS candle-derivation writes real candle rows to GCS. Without it,
the classifier returned `SILENT` → `GONE_NO_CAPTURE` → CRITICAL page, even though the VM was actively producing data.

## Root cause confirmed

The VM ran at 05:24–07:15 UTC on 2026-08-10. The fix (commit `2f077c97`, "stop GONE_NO_CAPTURE false pages for
real-write MDPS + launcher-host VMs") was committed by slot 18 at 18:11 UTC the same day — **after** this VM's run
completed. The fix added `POLARS AGGREGATED` to `_PROGRESS_RE` specifically because of the `mdps-cefi-2019-*`
drained-with-candles storm. This `mdps-cefi-2021-*` VM is the same false-positive class on a different year shard.

**Fix status**: Code is already shipped (`2f077c97` → promoted to main at `40b5cf56`). No code changes needed from this
escalation.

## Recommended decision

1. **No code to ship** — the classifier fix is already in main. Future MDPS VM terminations will be correctly classified
   as PROGRESS / EXPECTED_NO_CAPTURE.
2. **Re-launch the VM** — it was killed mid-run (no terminal EXIT_STATUS, processing only reached 2021-01-04 of 365
   days). The VM had real progress and the data is in GCS candles. Re-launch with
   `launch-mdps-sharded-backfill.sh cefi --year 2021` to resume from checkpoint if available, or from genesis.
3. **Close this escalation** — confirmed false positive from a now-fixed detector gap.

## Todos

- [ ] [INFRA] P2. **ADDED 2026-08-12 (/plan-reconcile, Section 2 zero-checkbox conversion)** — Re-launch the
      `mdps-cefi-2021-*` sharded MDPS CeFi backfill (`launch-mdps-sharded-backfill.sh cefi --year 2021`), resuming from
      checkpoint if available (prior run `mdps-cefi-2021-20260810-052119` was killed mid-run at 2021-01-04, no terminal
      `EXIT_STATUS` — confirmed false-positive SILENT classification; real candle data already in GCS). Repo:
      deployment-service.

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- 2026-08-11: Read escalation context, domain SSOTs, and classifier code. Accessed VM run.log from GCS. Confirmed 21,847
  POLARS AGGREGATED lines. Root cause: pre-fix `_PROGRESS_RE` missing POLARS AGGREGATED — fix already shipped. Filed
  this issue doc.
