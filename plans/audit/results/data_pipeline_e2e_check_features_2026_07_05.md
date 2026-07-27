---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05 (merged across multiple driver invocations — see
  merge_pipeline_e2e_report.py): total=8 passed=0 failed=1 ambiguous=0 skipped=6"
status: pass
nature: record
asset_group: [defi, prediction, tradfi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-07-27
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-07-27
auditor: data_pipeline_e2e_check_features (real-VM automated run, merged)
parent_epic: infrastructure_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-05
generated_at: "2026-07-27T06:38:22.185403+00:00"
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)

**Legs:** force, skip

**Note — merged across multiple driver invocations** via `merge_pipeline_e2e_report.py` (the driver overwrites its
report per-invocation, does not append across separate `--asset-group`/`--family`-scoped processes).

**Summary:** total=8 passed=0 failed=1 ambiguous=0 skipped=6

## Results

| Shard                | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                                                  |
| -------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DEFI:delta_one       | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                               |
| DEFI:delta_one       | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                               |
| DEFI:onchain         | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                               |
| DEFI:onchain         | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                               |
| PREDICTION:delta_one | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                               |
| PREDICTION:delta_one | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                               |
| TRADFI:delta_one     | force | failed  | not_applicable | 1    | 0       | -        | dependency_check_failed: Missing market-data-processing-service, Path gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-04/, Date 2026-07-04, No data for 2026-07-04/TRADFI |
| TRADFI:delta_one     | skip  | not_run | not_applicable | None | 0       | -        | force already failed on missing input — skip-if-fresh is moot without a successful write                                                                                                                                |

## Bucket paths (where each write/read actually landed)

| Shard                | Leg   | Parquet bucket | Manifest bucket | Same bucket? |
| -------------------- | ----- | -------------- | --------------- | ------------ |
| DEFI:delta_one       | force | `-`            | `-`             | -            |
| DEFI:delta_one       | skip  | `-`            | `-`             | -            |
| DEFI:onchain         | force | `-`            | `-`             | -            |
| DEFI:onchain         | skip  | `-`            | `-`             | -            |
| PREDICTION:delta_one | force | `-`            | `-`             | -            |
| PREDICTION:delta_one | skip  | `-`            | `-`             | -            |
| TRADFI:delta_one     | force | `-`            | `-`             | -            |
| TRADFI:delta_one     | skip  | `-`            | `-`             | -            |

## Note — TRADFI:delta_one manually recorded (driver process crashed before writing its own report row)

The automated `pipeline_e2e_check.py` driver process (backgrounded, watched via Monitor) was silently killed twice
during this cell — once ~66s into `EXIT_STATUS`-polling with zero traceback/log output (matches the
`WorkerLivenessWatchdog`/shared-host-resource-pressure class documented in
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`), once when a foreground re-attempt hit
this session's own 300s tool timeout mid-poll. In BOTH cases the underlying GCP VM completed independently and correctly
— this row is reconstructed from DIRECT `gcloud storage cat` reads of the VM's own
`gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`, not from the driver's own (never-written) report
output. **Two independent VM runs** (`features-e2e-tradfi-20260727-054450-2b064d`,
`features-e2e-tradfi-20260727-060813-2b064d`) both hit the IDENTICAL terminal failure within ~15s of starting compute:

```
DEPENDENCY CHECK FAILED — Missing: market-data-processing-service
  Path: gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-04/
  Date: 2026-07-04  Asset group: TRADFI  Required: True  Reason: No data for 2026-07-04/TRADFI
```

exit_code=1, `DEPLOYMENT_FAILED`, self-deleted cleanly both times (`VM_SHUTDOWN_ON_COMPLETION=true`) — a genuine,
reproducible terminal state, not a crash or ambiguous hang.

**This is a real finding, not driver noise**: the driver's own `--require-captured` pre-launch check (via
`read_availability_index`) accepted the `2026-07-04..2026-07-05` window as covered for TRADFI (no `--auto-day` slide
triggered, unlike DEFI, where the same check correctly detected the gap and slid the window) — but the VM's OWN internal
dependency check, which reads the GCS path directly, found NO object there. **Caution on root-cause attribution**:
`issues/candle_feature_canonical_path_divergence_2026_07_20.md` todo 7 (an initially-plausible link, "candle
object↔manifest disconnect") turns out to be a DIFFERENT-direction bug that's now mostly root-caused + FIXED
(`mdps@caa995c`, 2026-07-27) — objects existing WITHOUT manifest rows, the opposite of what's observed here (driver's
coverage check reporting a row that doesn't correspond to a real object). Also plausibly just the mundane,
already-expected "TRADFI candle backfill hasn't reached this day yet" gap (`SKILL.md`'s own reality-check note) — except
the driver's `--auto-day`/`--require-captured` logic should have caught that and produced a clean `skipped` verdict
instead of launching a real VM. Filed as its own scoped follow-up todo in
`data_pipeline_check_mdps_features_2026_07_20.md` rather than force-linking to a doc whose own framing doesn't match —
do not assume causal identity with either candidate without direct investigation.
