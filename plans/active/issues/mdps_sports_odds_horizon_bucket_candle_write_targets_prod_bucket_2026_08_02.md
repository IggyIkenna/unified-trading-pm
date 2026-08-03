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
    /plans/archive/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
    /plans/archive/issues/bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md,
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

- [x] ✅ [INFRA] P1. **DONE 2026-08-02 (slot-16, infra)** — Confirmed directly via the archived VM logs (no need to
      re-run — the original force-leg VM's `run.log` is still in GCS): `MDPS_OUTPUT_BUCKET_SPORTS` IS genuinely present
      in the launched process's environment. Repo: deployment-service (evidence only; no code change — the launcher's
      wiring is confirmed correct, see todo 3 below).
- [x] ✅ [CODE] P1. **DONE 2026-08-02 (slot-16, infra)** — The env var IS present (per todo 1) but still not honored.
      Traced the write path: confirmed it DOES call `config.get_output_bucket_for_asset_group()` — no sports-specific
      bypass exists. Root cause remains unidentified after this trace; see new todo 5 below. Repo:
      market-data-processing-service (investigation only; no code change).
- [x] ✅ [CODE] P1. **N/A — premise false, 2026-08-02 (slot-16, infra)**. Per todo 1, `MDPS_OUTPUT_BUCKET_SPORTS` is
      genuinely present in the launched command (confirmed via direct `run.log` evidence, not just the narrower
      `LAUNCH_PARAMS.json` artifact this todo's own text flagged as inconclusive) — `launch-mdps-backfill-vm.sh`'s
      `--output-bucket` wiring is CORRECT. This todo's contingent branch ("if the env var is genuinely missing") did not
      materialize; no launcher fix is needed. Repo: deployment-service (no code change — closing as not-applicable, not
      as done-with-a-fix).
- [ ] [DATA] P2. Once fixed, re-run a from-scratch force+skip
      `pipeline_e2e_check.py --asset-group SPORTS     --data-types odds_horizon_bucket` and confirm a genuine (non-403,
      non-timeout) verdict — either a real pass or a real data-derivation failure, not an infra/bucket-targeting
      artifact. Feeds back into `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track K (MDPS) checkpoint
      cadence. **UNBLOCKED 2026-08-02** — todo 5's fix (`market-data-processing-service@9642cbb`) landed; this re-run
      can proceed whenever next dispatched.
- [x] ✅ [CODE] P1. **DONE 2026-08-02 (slot-4, infra) — verified + checkbox-flipped by slot-16**.
      `market-data-processing-service@9642cbb` ("fix(mdps): streaming chain-bundle write path resolves output bucket,
      not source bucket"). Root cause: `_streaming_write_per_tf` in `live_workers_streaming.py`
      (`LiveChainStreamingMixin`) resolved its write bucket via `get_bucket_for_asset_group()` (the
      `PROTOCOL_DATA_SOURCE_BUCKET_{CAT}`/PROD getter) instead of `get_output_bucket_for_asset_group()` (the
      `MDPS_OUTPUT_BUCKET_{CAT}` override-aware getter) — a SEPARATE dispatch path from the already-correct eager
      `candle_write_mixin.py::_write_candles` that todos 1+2's static trace examined. Chain-bundle detection
      (`_chain_bundle_likely_from_path`) routes every SPORTS `ticks.parquet` through this streaming path BEFORE the
      eager path is ever reached, so the override was silently ignored regardless of how correct the eager path's own
      code was — explaining the "both launcher and write-dispatch check out correct, yet the write still 403s"
      contradiction todo 2 surfaced. Root-caused via runtime-path tracing, not further static reading (per the fix
      commit's own message). Verified: `git merge-base --is-ancestor 9642cbb origin/live-defi-rollout` = true.

## Progress Log

- 2026-08-02 (slot-2, infra): Filed while verifying the SPORTS:odds_horizon_bucket timeout override
  (`market-data-processing-service@dbcba44`). Confirmed the timeout mechanism itself works (both legs terminated
  genuinely within ~3.7min, well inside the new 3600s budget) — this doc tracks only the unrelated PROD-bucket-write
  defect discovered as a byproduct, not fixed in this session (outside this task's scope).

- 2026-08-02 (slot-16, infra, dispatched on todo 2 / `-002`): Picked up todo 2 ("if the env var IS present but still not
  honored, trace the code path"). Rather than wait on todo 1 (dispatched separately to slot 4, which was later `killed`
  and released the task back to `queued` without completing it — confirmed via `GET /api/state`/`GET /api/backlog`), did
  the underlying investigation myself since it's a direct prerequisite for my own todo and nothing else was actively
  working it.

  **Todo 1's answer (env var presence) — CONFIRMED PRESENT, with direct evidence**: the original force-leg VM
  (`mdps-backfill-sports-pipelinecheck-20260802-161417-d0c755`) was already deleted (`gcloud compute instances list`
  empty), but its `run.log` is still archived in GCS
  (`gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-sports-pipelinecheck-20260802-161417-d0c755/run.log`,
  fetched via `gcloud storage cat` — `gsutil` is broken on this host per the `pipeline_e2e_check.py` 2026-08-01 finding
  in a sibling issue, worked around the same way). Line 2 of `run.log` is the literal
  `[vm-exec] starting: bash -c (...)` line showing the FULL launched command, which contains
  `MDPS_OUTPUT_BUCKET_SPORTS=market-data-tick-sports-test-central-element-323112` as a genuine env-var prefix before the
  `python -m market_data_processing_service` invocation — this settles the doc's own open question (the narrower
  `LAUNCH_PARAMS.json` artifact not listing this key was correctly flagged as inconclusive by whoever filed the doc; the
  full launched command proves it IS present).

  **Todo 2's answer (code-path trace) — CONFIRMED CORRECT, no bypass found**: traced the actual write call chain for
  this run. The `run.log` shows `Streaming chain bundle: N instrument_id groups in raw_tick_data/.../ticks.parquet`
  lines (sports odds are chain-grouped), which routes to
  `market_data_processing_service/app/core/live_workers_chain.py`'s per-timeframe writer loop (`~line 527`), which calls
  `self._write_candles(...)` — the SAME `CandleWriteMixin._write_candles` (candle_write_mixin.py:186) used by every
  other MDPS write path (batch_workers.py, orchestration_service.py). That function resolves the bucket via
  `bucket_name: str = self.config.get_output_bucket_for_asset_group(category)` — no sports-specific override or bypass
  exists anywhere in this call chain. `get_output_bucket_for_asset_group` itself (`config.py:545`) is also correct on
  inspection: `get_config(f"MDPS_OUTPUT_BUCKET_{cat}", "")` where `cat = asset_group.value.upper()` — for SPORTS this is
  `MDPS_OUTPUT_BUCKET_SPORTS`, an exact match to the env var confirmed present above. Traced `get_config()` itself
  (`unified_trading_library/core/config.py:670`): it first checks the `UnifiedCloudServicesConfig` singleton for a
  declared field named `mdps_output_bucket_sports` (none exists — `model_config` uses `extra="ignore"`, confirmed via
  grep, so pydantic-settings does NOT auto-capture this as an extra attribute), then falls through to a plain, uncached
  `os.environ.get("MDPS_OUTPUT_BUCKET_SPORTS", "")` — which, given the var is genuinely in this process's environment
  from process start (part of the `bash -c` env-prefix, not a subprocess-inherited or later-set value), should return
  the override correctly. Also checked the one plausible env-stripping culprit
  (`process_handler.py::_run_date_as_subprocess`, which forks a per-date child and could in principle drop unlisted env
  vars) — ruled out for this specific run: the `run.log`'s own `MDPS legacy argv` line already shows
  `--no-subprocess-per-date`, i.e. `_build_legacy_argv` detected `start_date == end_date` and suppressed the subprocess
  fork entirely, so no child-process env-inheritance path is even in play here.

  **Net result**: both the launcher (todo 3's presumed track) and the write-dispatch code (todo 2's own ask) check out
  as CORRECT on static inspection, yet the write empirically still 403s against PROD with the override var confirmed
  present. This is a genuine, unresolved contradiction — I could not find the actual defect via code reading alone.
  Flipped todo 1 (my own direct evidence settles it), todo 2 (my own scoped ask — fully investigated, correctly
  concluding "no bypass" rather than forcing a fix that isn't there), and todo 3 (N/A — its contingent premise is
  false). Did NOT flip todo 4 (still blocked on the real fix) and filed a new todo 5 for the next actionable step
  (instrumented runtime debugging), per the "every follow-up is a tracked todo, never prose" HARD RULE — the specific
  next diagnostic moves are enumerated there rather than left as a vague "needs more investigation."

- 2026-08-02 (slot-16, infra, dispatched on todo 5 / `-005`): Picked up todo 5 ("root-cause and fix the actual defect").
  Followed the doc's own "cheaper first probe (a)" — checked `TARBALL_PINS.json` for the original force-leg VM
  (`gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-sports-pipelinecheck-20260802-161417-d0c755/TARBALL_PINS.json`):
  confirmed `MDPS_TARBALL_SHA` was genuinely `"floating"` (unpinned) for that run, so the exact deployed commit wasn't
  directly recoverable from the pin record. Before adding runtime instrumentation, re-read the current HEAD of the full
  write chain myself (`candle_write_mixin.py` → `canonical_writer.py` → `canonical_writer_manifest.py`) to independently
  verify todo 2's "no bypass" conclusion — confirmed correct for the EAGER path, but this is exactly where the
  contradiction lived: `git log --since` on the service repo surfaced `market-data-processing-service@9642cbb` (slot-4,
  landed 2026-08-02T17:19:06Z — after this doc's original 16:14-16:22Z reproduction run, and after my own session
  started on this same todo), which root-caused the REAL defect: a separate streaming chain-bundle write dispatcher
  (`live_workers_streaming.py::_streaming_write_per_tf`, reached via `_chain_bundle_likely_from_path` BEFORE the eager
  path for every SPORTS `ticks.parquet`) called the source-bucket getter instead of the output-bucket getter — a genuine
  second write path todos 1+2's trace never reached because it was static-reading the eager path only. Slot-4 shipped
  the fix but never flipped this issue doc's checkbox (a plan-flip gap on their end). Verified the fix is real and on
  origin (`git merge-base --is-ancestor 9642cbb origin/live-defi-rollout`), then flipped todo 5 to reflect the actual
  completion and corrected todo 4's now-stale "still blocked" note. No new code change from this session — the fix was
  already shipped; this session's contribution is verification + closing the plan-flip gap. Todo 4 (the from-scratch
  re-verification run) remains open for whoever picks it up next.
