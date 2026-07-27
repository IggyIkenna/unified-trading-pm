---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05 (merged across multiple driver invocations — see
  merge_pipeline_e2e_report.py): total=16 passed=0 failed=4 ambiguous=0 skipped=7"
status: fail
nature: record
asset_group: [cross-cutting, defi, prediction, sports, tradfi]
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

**Summary:** total=16 passed=0 failed=4 ambiguous=0 skipped=7

## Results

| Shard                | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| -------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DEFI:delta_one       | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| DEFI:delta_one       | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| DEFI:onchain         | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| DEFI:onchain         | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| GLOBAL:calendar      | force | failed  | not_applicable | 0    | 0       | -        | PROD-WRITE BUG: wrote to gs://features-calendar-prd-... despite IS_TEST_RUN=true (is_test_run field declared but never consumed in calendar/config.py). See issues/features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md. 0 rows written this run (no real damage), exit_code=0 at the VM level but this is a P0 SAFETY bug, not a pass.                                                                                                                                        |
| GLOBAL:calendar      | skip  | not_run | not_applicable | None | 0       | -        | force violated test-bucket isolation — do not proceed to skip-proof until fixed                                                                                                                                                                                                                                                                                                                                                                                                           |
| PREDICTION:delta_one | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| PREDICTION:delta_one | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| SPORTS:sports        | force | failed  | not_applicable | 0    | 51      | -        | PROD-WRITE BUG: wrote REAL data (51 fixtures, per-league fixture_features/derived_features) to gs://features-sports-prd-... despite IS_TEST_RUN=true (is_test_run field declared but never consumed in sports/config.py or batch_handler.py's bucket_name resolution). See issues/features_sports_is_test_run_ignored_writes_real_data_to_prod_2026_07_27.md. Worse than the calendar P0 (real content, not 0 rows). exit_code=0 at the VM level but this is a P0 SAFETY bug, not a pass. |
| SPORTS:sports        | skip  | not_run | not_applicable | None | 0       | -        | force violated test-bucket isolation -- do not proceed to skip-proof until fixed                                                                                                                                                                                                                                                                                                                                                                                                          |
| TRADFI:commodity     | force | failed  | not_applicable | 1    | 0       | -        | All 3 external data sources (eia_weekly_storage, cftc_cot_report, baker_hughes_rig_count) returned 403/timeout/404 from the GCP VM. NOT a credentials gap (all 3 documented as public/no-auth). See issues/features_commodity_public_api_403_from_gcp_vm_2026_07_27.md. Batch completed: 0/4 succeeded.                                                                                                                                                                                   |
| TRADFI:commodity     | skip  | not_run | not_applicable | None | 0       | -        | force failed on all external sources — skip-if-fresh is moot without a successful write                                                                                                                                                                                                                                                                                                                                                                                                   |
| TRADFI:delta_one     | force | failed  | not_applicable | 1    | 0       | -        | dependency_check_failed: Missing market-data-processing-service, Path gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-04/, Date 2026-07-04, No data for 2026-07-04/TRADFI                                                                                                                                                                                                                                                                   |
| TRADFI:delta_one     | skip  | not_run | not_applicable | None | 0       | -        | force already failed on missing input — skip-if-fresh is moot without a successful write                                                                                                                                                                                                                                                                                                                                                                                                  |
| TRADFI:volatility    | force | skipped | not_applicable | 0    | 0       | -        | no_captured_input_for_window (window slid to 2026-01-29..2026-01-30 via --auto-day; 872x 'No captured perp' honest-absence warnings, 0 ERROR/CRITICAL, Completed 0/4 groups, exit_code=0 DEPLOYMENT_COMPLETED). Manually recorded — driver process was not actively watched to completion (stopped live-watching per session note), reconstructed from direct gcloud storage cat of the VM's own run.log.                                                                                 |
| TRADFI:volatility    | skip  | not_run | not_applicable | None | 0       | -        | force produced zero captured rows — skip-if-fresh is moot without a successful write                                                                                                                                                                                                                                                                                                                                                                                                      |

## Bucket paths (where each write/read actually landed)

| Shard                | Leg   | Parquet bucket                               | Manifest bucket                              | Same bucket? |
| -------------------- | ----- | -------------------------------------------- | -------------------------------------------- | ------------ |
| DEFI:delta_one       | force | `-`                                          | `-`                                          | -            |
| DEFI:delta_one       | skip  | `-`                                          | `-`                                          | -            |
| DEFI:onchain         | force | `-`                                          | `-`                                          | -            |
| DEFI:onchain         | skip  | `-`                                          | `-`                                          | -            |
| GLOBAL:calendar      | force | `-`                                          | `-`                                          | -            |
| GLOBAL:calendar      | skip  | `-`                                          | `-`                                          | -            |
| PREDICTION:delta_one | force | `-`                                          | `-`                                          | -            |
| PREDICTION:delta_one | skip  | `-`                                          | `-`                                          | -            |
| SPORTS:sports        | force | `features-sports-prd-central-element-323112` | `features-sports-prd-central-element-323112` | yes          |
| SPORTS:sports        | skip  | `-`                                          | `-`                                          | -            |
| TRADFI:commodity     | force | `-`                                          | `-`                                          | -            |
| TRADFI:commodity     | skip  | `-`                                          | `-`                                          | -            |
| TRADFI:delta_one     | force | `-`                                          | `-`                                          | -            |
| TRADFI:delta_one     | skip  | `-`                                          | `-`                                          | -            |
| TRADFI:volatility    | force | `-`                                          | `-`                                          | -            |
| TRADFI:volatility    | skip  | `-`                                          | `-`                                          | -            |

## Note — GLOBAL:calendar — P0 DATA-CORRECTNESS BUG, not a clean pass

VM `features-e2e-global-20260727-074139-a9e7df` (`DEPLOYMENT_COMPLETED exit_code=0`) wrote to
`gs://features-calendar-prd-central-element-323112/...` — **PROD**, despite `IS_TEST_RUN=true` /
`PROTOCOL_DATA_SINK_BUCKET=features-calendar-test-...` both set in the VM env. Root cause (direct code read):
`features_service/calendar/config.py`'s `is_test_run` field is declared but consumed NOWHERE in the package —
`get_source_bucket()` never branches on it or checks `get_data_sink(routing_key=...)` (the correct pattern
`delta_one/config.py`'s `get_output_bucket()` already uses). 0 rows written this run (no real damage), but a real-data
day would silently pollute PROD from a smoke-test invocation. Full writeup + fix:
`issues/features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md` (P0, operator-notified). **Do not re-run this
cell until the fix lands.**

## Note — SPORTS:sports — P0 DATA-CORRECTNESS BUG, worse than calendar's — wrote REAL data to PROD

VM `features-e2e-sports-20260727-085523-281e78` (`DEPLOYMENT_COMPLETED exit_code=0`) wrote REAL, non-empty feature data
— 51 fixtures across dozens of leagues, `fixture_features`/`derived_features`/`standings`/`teams`/`venues` for
`day=2026-07-05` — to `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-07-05/...`,
despite `IS_TEST_RUN=true` / `PROTOCOL_DATA_SINK_BUCKET_SPORTS=features-sports-test-...` both set in the VM env; the
`-test-` bucket was confirmed completely empty. Same root-cause CLASS as the calendar P0 (`is_test_run` declared but
never consumed), different call site: `features_service/sports/cli/handlers/batch_handler.py:872`'s
`bucket_name = bucket or resolve_bucket(kind="features-sports", asset_group="sports")` never checks `get_data_sink`.
**Worse than calendar**: object `generation`/`metageneration` confirm these were first-writes (no existing prod data
destroyed), but real, valid content was created via an unintended test-invocation path — the exact mechanism that could
corrupt PROD with WRONG values if a future smoke test runs against a broken build. Full writeup + fix:
`issues/features_sports_is_test_run_ignored_writes_real_data_to_prod_2026_07_27.md` (P0, operator-notified). **Do not
re-run this cell until the fix lands.**

## Note — TRADFI:commodity — external data sources unreachable from this GCP VM (not a credentials gap)

VM `features-e2e-tradfi-20260727-083257-974efe` (`DEPLOYMENT_FAILED exit_code=1`, `Batch completed: 0/4 succeeded`) —
all 3 data sources (`eia_weekly_storage`, `cftc_cot_report`, `baker_hughes_rig_count`) returned 403/timeout/404. Each
adapter's own docstring states "Authentication: None required (public)" — this is NOT `BLOCKED-CREDENTIALS` (no
credential exists to provision); most likely GCP-VM outbound-IP blocking or a missing/generic `User-Agent` header these
public sites now reject. The manifest's own honest-absence guard correctly REFUSED to record this as `empty_confirmed`
(no clean-200-empty `FetchEvidence`) — a good defensive catch, not a bug. Full writeup:
`issues/features_commodity_public_api_403_from_gcp_vm_2026_07_27.md` (P2).

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
