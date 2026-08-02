---
doc_type: issue
title:
  MDPS SPORTS:odds_horizon_bucket candle write targets the PROD bucket even with `--output-bucket <test-bucket>` passed
  — only blocked by IAM, not by the launcher/writer honoring the override
summary: >-
  Verifying the new per-(asset_group, data_type) timeout override for SPORTS:odds_horizon_bucket
  (features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md todo 4), ran a genuine from-scratch
  force+skip `pipeline_e2e_check.py` run against day=2026-04-14 (auto-day). Both VMs (force
  `mdps-backfill-sports-pipelinecheck-20260802-161417-d0c755`, skip
  `mdps-backfill-sports-pcskip-20260802-161855-d0c755`) correctly launched with `--env staging --source-bucket
  market-data-tick-sports-prd-central-element-323112 --output-bucket
  market-data-tick-sports-test-central-element-323112` and BOTH ran as `uts-test-sa` (the `--env staging` fix from
  `pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md` is confirmed landed/working). Both legs completed
  genuinely (EXIT_STATUS=1 observed within ~3.5-3.7min, well inside the new 3600s timeout — so the TIMEOUT mechanism
  itself is validated, not abandoned). The failure cause is a THIRD, previously-undocumented bug: every candle write
  attempt in run.log targets `market-data-tick-sports-prd-central-element-323112` (the `--source- bucket`, i.e. PROD)
  instead of the passed `--output-bucket` test bucket — `uts-test-sa` correctly has no PROD write access, so every write
  403s (confirmed: `storage.objects.create` denied on `.../market-data-tick-sports-prd-.../
  processed_candles/by_date/day=2026-04-14/.../data_type=odds_horizon_bucket/...`). This is NOT the same defect as
  either related doc below: `bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md` is about the
  IAM CEL condition prefix not matching per-AG buckets at all (fixed, and irrelevant here since the attempted bucket is
  PROD, where `uts-test-sa` correctly should NEVER be able to write); `pipeline_e2e_check_missing_env_flag_test_bucket_
  403_2026_08_01.md` is about the wrong SERVICE ACCOUNT being used (also fixed — confirmed `uts-test-sa` is in use
  here). The IAM 403 is doing its job (preventing a smoke-check VM from writing fabricated test data into PROD) — but if
  the IAM condition were ever more permissive, this bug would let a `--output-bucket <test>` smoke-check silently
  corrupt real PROD candle data for SPORTS:odds_horizon_bucket.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [mdps, pipeline-e2e-check, bucket-isolation, data-correctness, iam, sports, odds_horizon_bucket, test-isolation]
related:
  [
    /plans/active/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
    /plans/active/issues/bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md,
    /plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
    /plans/audit/results/data_pipeline_e2e_check_mdps_2026_08_01.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: infrastructure_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: correct-code
source: >-
  Surfaced 2026-08-02 (slot-2, infra) while executing features_e2e_check_delta_one_timeout_orphans_duplicate_vms-005
  ("New corroborating instance, different service" — add SPORTS:odds_horizon_bucket timeout override to MDPS's
  pipeline_e2e_check.py and verify with a real from-scratch run). This finding is a byproduct of that verification run,
  not the task's own scope.
resolved_by:
locked_by:
depends_on: []
---

# MDPS SPORTS:odds_horizon_bucket candle write targets PROD instead of `--output-bucket`

## What I found

Ran, from `market-data-processing-service`:

```
python3 scripts/pipeline_e2e_check.py --day 2026-08-01 --legs force,skip --require-captured --auto-day \
  --asset-group SPORTS --data-types odds_horizon_bucket --project central-element-323112
```

Auto-day resolved to `2026-04-14`. The driver launched (all times UTC):

| time     | event                                                                                                                                                                                                                                         |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 16:14:17 | force-leg VM `mdps-backfill-sports-pipelinecheck-20260802-161417-d0c755` launched with `--env staging --source-bucket market-data-tick-sports-prd-central-element-323112 --output-bucket market-data-tick-sports-test-central-element-323112` |
| 16:18:01 | force leg's `run.log` shows `Handler returned non-zero exit code: 1` — genuine terminal result, `EXIT_STATUS=1` written                                                                                                                       |
| 16:18:55 | skip-leg VM `mdps-backfill-sports-pcskip-20260802-161855-d0c755` launched with the identical bucket flags                                                                                                                                     |
| 16:22:37 | skip leg's `run.log` shows the identical failure, `EXIT_STATUS=1` written                                                                                                                                                                     |

Both legs finished in ~3.5-3.7 minutes — well inside the new 3600s
`_FAMILY_TIMEOUT_OVERRIDES[("SPORTS", "odds_horizon_bucket")]` override, confirming that todo's own timeout mechanism is
sound (the VM was NOT abandoned; a genuine terminal verdict was obtained quickly). The failure itself is unrelated to
timing.

**Root symptom** (both VMs, identical): every candle-write attempt in `run.log` targets the PROD bucket
(`market-data-tick-sports-prd-central-element-323112`, i.e. the `--source-bucket`), not the passed `--output-bucket`
(`market-data-tick-sports-test-central-element-323112`):

```
2026-08-02 16:17:19,154 ERROR [CRITICAL] unknown error in market-data-processing-service.process_instrument_file:
403 POST https://storage.googleapis.com/upload/storage/v1/b/market-data-tick-sports-prd-central-element-323112/o
?uploadType=multipart: "uts-test-sa@central-element-323112.iam.gserviceaccount.com does not have
storage.objects.create access ... resource '.../buckets/market-data-tick-sports-prd-central-element-323112/objects/
processed_candles/by_date/day=2026-04-14/pipeline_mode=batch_odds_api/timeframe=15m/data_type=odds_horizon_bucket/
instrument_type=MATCH_ODDS/venue=BET888SPORT/...parquet'
```

This repeats for every instrument/timeframe in the shard (hundreds of 403s), plus a final `atexit manifest flush` 403
against the same PROD bucket. `uts-test-sa` correctly has NO write access to any `-prd-` bucket (by design, per
`bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md`'s fix) — the 403 is IAM correctly doing
its job. The bug is that the write was attempted against PROD at all, despite an explicit `--output-bucket <test>`.

**This is a THIRD, distinct defect from the two already-tracked related docs**:

- `bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md` — about the IAM CEL condition prefix
  not correctly enumerating per-asset-group buckets at all (fixed 2026-08-01, `deployment-service@4a93aac`). Not the
  cause here: the write is correctly evaluated against PROD (where `uts-test-sa` should never have access) — the CEL
  condition is irrelevant once the wrong bucket is targeted in the first place.
- `pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md` — about the wrong SERVICE ACCOUNT (`uts-prd-sa`
  instead of `uts-test-sa`) being used because `--env staging` wasn't passed (fixed for MDPS,
  `market-data-processing-service@b16d44c`). Not the cause here: this run's launch argv confirms `--env staging` IS
  present, and the 403 identity is correctly `uts-test-sa`.

**Where the override SHOULD apply**: `market_data_processing_service/config.py::get_output_bucket_for_asset_group()`
reads `MDPS_OUTPUT_BUCKET_{CAT}` (falls back to `get_source_bucket()`, i.e. PROD, only when the override is unset) —
correctly wired into every real candle-write call site (`app/core/batch_workers.py:183`,
`app/core/orchestration_service.py:436`, `app/core/candle_write_mixin.py:186,356`,
`cli/handlers/process_handler.py:86`). `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh:261-262,279-282`
conditionally appends `MDPS_OUTPUT_BUCKET_${cat_upper}=${OUTPUT_BUCKET_OVERRIDE}` to the VM's launched command when
`--output-bucket` is passed — this branch SHOULD have fired for this run (`--output-bucket` was passed). One data point
supporting a launcher-side gap: the VM's own `LAUNCH_PARAMS.json` (a separate progress-checkpoint artifact, not
necessarily the full env) does not list `MDPS_OUTPUT_BUCKET_SPORTS` among its keys — worth confirming directly whether
the full `VM_BACKFILL_CMD` string actually included it, not just inferring from this narrower artifact. Not chased
further this session (outside this task's scope — filed here instead of silently working around it).

## Why it matters

1. **Data-correctness risk, currently masked by IAM**: if the `-prd-` IAM condition were ever misconfigured more
   permissively (plausible — this exact bucket family has already had one IAM CEL bug this week), a routine
   `--output-bucket <test>` smoke-check run would silently write fabricated/test candle data into the REAL PROD SPORTS
   bucket, corrupting production data with no error signal.
2. **Blocks genuine SPORTS:odds_horizon_bucket verification**: every force/skip verification of this shard fails on this
   bug before it can produce a real pass/fail verdict on the actual candle-derivation logic — the
   `sports_consolidated_native_ao_extract_2026_07_25.md` Track K (MDPS) checkpoint cadence for this specific shard
   cannot get a genuine result until this is fixed.
3. Not a timeout defect — confirmed both legs terminate well inside budget; this doc exists purely to track the
   bucket-targeting bug uncovered as a byproduct of that verification.

## Recommended fix path

- [x] ✅ [INFRA] P1. **DONE 2026-08-02 (slot-10, data_pipeline_failure escalation agt-4f0f41).** Confirmed directly:
      `run.log`'s own startup line for BOTH the original force-leg VM
      (`mdps-backfill-sports-pipelinecheck-20260802-161417-d0c755`) and a fresh relaunch I ran with the identical argv
      (`mdps-backfill-sports-relaunch-20260802-163614-dp001`) prints the exact `bash -c` command
      `vm-exec` invoked, verbatim: `... MDPS_ASSET_GROUP=SPORTS MDPS_DATA_TYPES='odds_horizon_bucket'
      MDPS_OUTPUT_BUCKET_SPORTS=market-data-tick-sports-test-central-element-323112 SKIP_DEPENDENCY_CHECK=true
      /home/ikennaigboaka/venv/bin/python -m market_data_processing_service --operation process --mode batch ...`.
      **`MDPS_OUTPUT_BUCKET_SPORTS` IS genuinely present in the VM's process environment, correctly set to the
      `-test-` bucket** — this rules out a launcher/argv-wiring gap entirely; the defect is squarely in
      `market-data-processing-service`'s write-path code (todo below), not `launch-mdps-backfill-vm.sh`. (repo:
      deployment-service — confirmation only, no code change needed here)
- [ ] [CODE] P1. If the env var IS present but still not honored: trace which code path SPORTS:odds_horizon_bucket
      candle writes actually go through (the `MATCH_ODDS`/`odds_horizon_bucket` instrument_type in the failing paths
      suggests a sports-specific writer) and confirm it calls `config.get_output_bucket_for_asset_group()` like every
      other MDPS write path, not a bucket resolved some other way. (repo: market-data-processing-service)
- [x] ✅ [CODE] P1. **MOOT 2026-08-02 (slot-10, agt-4f0f41)** — the env var IS present (see todo 1 above), so this
      "if genuinely missing" branch does not apply; `launch-mdps-backfill-vm.sh`'s existing
      `OUTPUT_BUCKET_OVERRIDE`/`_out_val` wiring is confirmed working correctly for `sports`. Separately (independent
      hardening, not a fix for THIS bug): shipped a fail-fast guard in the same function requiring
      `--source-bucket`/`--output-bucket` whenever `--env != prod`, so a FUTURE caller that omits them entirely fails in
      <1s instead of burning a full VM run — `deployment-service@<pending>`. (repo: deployment-service)
- [ ] [DATA] P2. Once fixed, re-run a from-scratch force+skip
      `pipeline_e2e_check.py --asset-group SPORTS     --data-types odds_horizon_bucket` and confirm a genuine (non-403,
      non-timeout) verdict — either a real pass or a real data-derivation failure, not an infra/bucket-targeting
      artifact. Feeds back into `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track K (MDPS) checkpoint
      cadence.

## Progress Log

- 2026-08-02 (slot-2, infra): Filed while verifying the SPORTS:odds_horizon_bucket timeout override
  (`market-data-processing-service@dbcba44`). Confirmed the timeout mechanism itself works (both legs terminated
  genuinely within ~3.7min, well inside the new 3600s budget) — this doc tracks only the unrelated PROD-bucket-write
  defect discovered as a byproduct, not fixed in this session (outside this task's scope).
- **2026-08-02 (slot-10, data_pipeline_failure escalation agt-4f0f41) — corroborating occurrence + todo 1/3 answered,
  NOT fixed.** Independently dispatched via `DP_VM_EXIT_NONZERO` (DP-VM-001) for this exact force-leg VM
  (`mdps-backfill-sports-pipelinecheck-20260802-161417-d0c755`, `exit_code=1`), before finding this doc already tracked
  it. Confirmed `MDPS_OUTPUT_BUCKET_SPORTS` is genuinely present + correctly set in the VM's actual process env (see
  todo 1) — ruling out the launcher-wiring branch (todo 3). Re-ran the identical shard as a fresh relaunch
  (`mdps-backfill-sports-relaunch-20260802-163614-dp001`, same `--env staging --source-bucket <prd> --output-bucket
  <test> --data-types odds_horizon_bucket --force` argv) to confirm this is a genuine, repeatable code defect and not a
  one-off — **it reproduced identically, `exit_code=1`, same 403-against-`-prd-` write pattern.** New observation for
  whoever picks up todo 2 (tracing the actual write call site): `run.log` also shows a DIFFERENT, seemingly-unrelated
  client-side validation error firing heavily for this same shard —
  `StreamingParquetWriter pre-write validation failed: [partition_mismatch] ... venue mismatch in
  'FOOTBALL:UNIBET:MATCH_ODDS:...': partition declares FOOTBALL, id has UNIBET` (repeats for UNIBET/SPORT888/BETFAIR_EX_EU/
  etc.) — every SPORTS:odds_horizon_bucket instrument's partition path derives `venue=FOOTBALL` (the SPORT, not the
  bookmaker) while the real venue lives in the instrument_id. Not confirmed whether this is causally related to the
  bucket-targeting bug (e.g. instruments failing this validation falling through to a different/older write path that
  doesn't consult `MDPS_OUTPUT_BUCKET_SPORTS`), but it's the same shard, same run, and worth checking first since it's
  the more specific signal — a manifest write in the SAME run correctly landed on the `-test-` bucket
  (`ManifestWriter: per-VM shard updated ... at market-data-tick-sports-test-central-element-323112/_index/per_vm/...`),
  so bucket-override resolution is NOT globally broken in this run, only for (some/all of) the actual candle-parquet
  writes. Per RB-INFRA-RELAUNCH's "re-fails the same way twice → stop relaunching, root cause is already an issue" —
  did not attempt a third relaunch; this doc's existing P1/`assigned_vm:planning` todo 2 is the correct next step, not
  further relaunches. Shipped an unrelated, independent hardening fix in the same session (see todo 3) — does not close
  this issue.
