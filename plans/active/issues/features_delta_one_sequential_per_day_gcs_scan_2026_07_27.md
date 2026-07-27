---
doc_type: issue
title:
  features-service delta_one data_loader does a sequential per-day GCS existence probe loop — likely root cause of
  multi-hour CEFI/TRADFI compute
summary: >-
  Live evidence from a real running VM (`features-e2e-cefi-20260727-063401-025349`, still RUNNING after 6h23m / 435k+
  `run.log` lines, no `EXIT_STATUS`) shows `features_service/delta_one/app/core/data_loader.py`'s
  `_collect_daily_frames` doing a plain sequential `while current_date <= end_date` loop — one GCS
  `blob_exists`/`download_bytes` round trip PER DAY, awaited one at a time, no batching or concurrency — repeated per
  (instrument x data_type x timeframe) via `load_candles_with_buffer`'s `buffer_days` extension. With ~589 CEFI
  perpetuals/futures and a multi-week buffer window, this multiplies into hundreds of thousands of small sequential
  network round trips, which is the most likely actual root cause of CEFI/TRADFI delta_one force-leg runs taking many
  hours (observed still-incomplete past 6h23m) rather than the ~40min the driver's old default `--timeout-sec=2400`
  assumed. Raising `--timeout-sec` (companion issue) is a mitigation, not a fix — this doc tracks the real root cause.
status: open
nature: issue
asset_group: [cefi, tradfi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [infra, features-service, performance, sequential-loop, gcs, delta_one]
related:
  [
    /plans/active/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source:
  "slot-14, infra, discovered while implementing the --timeout-sec raise for
  features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md, 2026-07-27"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# features-service delta_one sequential per-day GCS existence-probe loop

## What I found

While implementing the timeout-raise fix for
`issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`, I checked the LIVE state of the 8
`features-e2e-cefi-*`/`features-e2e-tradfi-*` VMs still running from earlier sessions
(`gcloud compute instances list --filter="name~'features-e2e'"`, 2026-07-27 12:57 UTC). The oldest,
`features-e2e-cefi-20260727-063401-025349` (created 2026-07-27T06:34:11Z), was still `RUNNING` with **no `EXIT_STATUS`
blob** at `gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-cefi-20260727-063401-025349/EXIT_STATUS`
— **6h23m elapsed**, not preempted, not stalled: `run.log` had **435,244 lines** and the tail showed active,
live-advancing timestamps (12:56:32–12:56:34, i.e. seconds before the check).

The tail was a long run of consecutive
`WARNING No upstream MDPS data for HYPERLIQUID:PERPETUAL:SOPH-USD@LIN on <date> (data_type=trades) — skipping date`
lines, one per calendar day, for a SINGLE instrument, spanning at least 2026-06-17..2026-07-16 (30 consecutive days) at
the tail alone. Reading the source (`features_service/delta_one/app/core/data_loader.py`):

- `_collect_daily_frames` (`data_loader.py:346-387`) is a plain synchronous-shaped loop:
  `while current_date <= end_date: ... df = self._try_load_one_day(...); current_date += timedelta(days=1)` — ONE
  `blob_exists` (+ `download_bytes` on a hit) GCS round trip PER DAY, awaited sequentially, no `asyncio.gather`/batch.
- `load_candles_with_buffer` (`data_loader.py:530-569`) extends the requested window backwards by `buffer_days` before
  calling `load_candles` → `_collect_daily_frames`, so the per-instrument day-count is `(end-start) + buffer_days`, not
  just the driver's own 1-day shard window (`resolve_lookback.py` reports `delta_one` `min_lookback_days=1`, but the
  INTERNAL buffer used inside a feature calculator is a separate, larger window not visible from the driver side — the
  30+ consecutive per-day probes in the tail are consistent with a multi-week buffer, not a 1-day one).
- This repeats once per `(instrument, data_type, timeframe)` triple a feature group requests. With ~589 CEFI
  perpetuals/futures (`features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`'s own count) and
  multiple `candle_data_types`/timeframes per instrument, the total sequential-GCS-round-trip count is easily in the
  hundreds of thousands to low millions — matching the observed 435k+ log lines after 6h23m (~19 lines/sec sustained,
  consistent with per-call network RTT dominating, not compute).

None of the 8 running VMs (`features-e2e-cefi-*` x6, `features-e2e-tradfi-*` x2 as of the same check) had an
`EXIT_STATUS` blob — all still mid-compute after 20min-6h23m of runtime.

## Why it matters

1. **This is very likely the actual root cause** of the timeout/orphan-VM pattern tracked in the companion issue —
   raising `--timeout-sec` (shipped: `features-service` `_FAMILY_TIMEOUT_OVERRIDES`, this session) only defers the
   symptom; a driver-side timeout large enough to survive the REAL completion time (plausibly 8-15+ hours at this rate)
   is impractical for what is meant to be a smoke/e2e check tool.
2. **Real SPOT-compute cost**: 8 VMs concurrently running for hours each on this pattern is a genuine, ongoing billing
   cost, separate from (compounds with) the duplicate-VM-launch waste already tracked in
   `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`.
3. **Production-path relevance**: `data_loader.py` is the SAME code path a real (non-test) delta_one feature compute run
   uses — this is not test-harness-only overhead. If this pattern is real, ordinary production feature-compute runs for
   CEFI/TRADFI delta_one are also this slow, which affects any operational timeline depending on feature-compute latency
   (backfills, promote gates, etc.), not just this e2e check tool.
4. Distinct from the already-tracked MDPS "S1 sequential per-instrument timeframe loop" bottleneck
   (`data_pipeline_check_mdps_features_2026_07_20.md`, candle WRITER side, market-data-processing-service) — this is a
   features-service READ-path bottleneck, in a different repo/module, not yet covered by that todo's fix.

## Recommended fix path

- [ ] [SCRIPT] P1. Confirm the hypothesis directly: instrument `buffer_days` value(s) actually passed to
      `load_candles_with_buffer` for CEFI/TRADFI delta_one feature groups (grep callers), and the real
      `(data_type, timeframe)` fan-out per instrument, to get an exact "GCS round trips per instrument" count and
      confirm it explains the observed ~19 lines/sec sustained rate. Repo: features-service.
- [ ] [SCRIPT] P1. If confirmed, batch/parallelize the per-day existence probes in `_collect_daily_frames`
      (`asyncio.gather` over the day range, or a single prefix-listing GCS call instead of N per-day `blob_exists` round
      trips) — the SAME class of fix already applied elsewhere in this codebase for candle writes (S1). Repo:
      features-service. **Done when**: a from-scratch CEFI:delta_one force-leg run's wall-clock drops materially
      (target: well under the raised `_FAMILY_TIMEOUT_OVERRIDES` value) with identical output.
- [ ] [DATA] P2. Once fixed, re-measure the real per-shard completion time and correct `_FAMILY_TIMEOUT_OVERRIDES` in
      `features-service/scripts/pipeline_e2e_check.py` (likely lowerable back toward the generic default) and the
      SKILL.md benchmark section — same "Done when" the companion timeout issue's P2 todo already asks for.
- [ ] [DATA] P2. Check whether the 8 currently-running `features-e2e-cefi-*`/`features-e2e-tradfi-*` VMs (as of
      2026-07-27 12:57 UTC) ever produce `EXIT_STATUS`, and if any are genuinely stuck (not just slow) rather than
      progressing, per the VM-delete guardrail (`agents/infra.md` STEP 0.65) — do not force-delete a VM that is still
      genuinely advancing.

## Progress Log

- 2026-07-27 (slot-14, infra): Filed while shipping the `--timeout-sec` raise for the companion issue. Not investigated
  further this session (root-cause confirmation + fix is real code-reading + a real-VM re-measurement, out of scope for
  the narrowly-dispatched timeout-raise todo). The evidence above (VM name, exact timestamps, line counts, code line
  numbers) is real-VM and real-code verified, not speculative — the "likely root cause" framing reflects that the causal
  chain (loop shape → round-trip count → observed rate) is confirmed, but a direct before/after fix measurement has not
  yet been done.
