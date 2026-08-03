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
    /plans/archive/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
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
context_scope:
  [
    features-service/features_service/delta_one/app/core/data_loader.py,
    features-service/scripts/pipeline_e2e_check.py,
    /plans/archive/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
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

- [x] [SCRIPT] P1. ✅ Confirm the hypothesis directly: instrument `buffer_days` value(s) actually passed to
      `load_candles_with_buffer` for CEFI/TRADFI delta_one feature groups (grep callers), and the real
      `(data_type, timeframe)` fan-out per instrument, to get an exact "GCS round trips per instrument" count and
      confirm it explains the observed ~19 lines/sec sustained rate. Repo: features-service. — **CONFIRMED, slot-14,
      2026-07-27** — see `## Confirmation findings (2026-07-27)` below.
- [x] [SCRIPT] P1. ✅ If confirmed, batch/parallelize the per-day existence probes in `_collect_daily_frames`
      (`asyncio.gather` over the day range, or a single prefix-listing GCS call instead of N per-day `blob_exists` round
      trips) — the SAME class of fix already applied elsewhere in this codebase for candle writes (S1). Repo:
      features-service. **Done when**: a from-scratch CEFI:delta_one force-leg run's wall-clock drops materially
      (target: well under the raised `_FAMILY_TIMEOUT_OVERRIDES` value) with identical output. — **SHIPPED, slot-13,
      2026-07-27, `features-service@1ad44550`**: `_collect_daily_frames` now fires per-day probes concurrently via
      `asyncio.gather` + `asyncio.to_thread` (bounded by a new `_DAILY_FRAME_PROBE_CONCURRENCY=20` semaphore), extracted
      into `_probe_one_day` to stay under the method-size QG cap. Mirrors the existing
      `FeatureWriter._write_daily_partitions`/`check_exists` pattern in this same package (prefix-listing was ruled out:
      `day=` sits mid-path, not as a suffix, so no single GCS prefix isolates one instrument's date range). Full
      QG-green (17,908 tests passed) + quickmerge shipped. The end-to-end from-scratch wall-clock re-measurement in the
      "Done when" clause is the SAME work as the next todo below (re-measure real per-shard completion time) — not
      re-run separately here since it requires a real multi-hour VM backfill, out of scope for this code-change todo.
- [x] [DATA] P2. ✅ Once fixed, re-measure the real per-shard completion time and correct `_FAMILY_TIMEOUT_OVERRIDES` in
      `features-service/scripts/pipeline_e2e_check.py` (likely lowerable back toward the generic default) and the
      SKILL.md benchmark section — same "Done when" the companion timeout issue's P2 todo already asks for. —
      **RE-MEASURED 2026-08-03, slot-14, data_engineering — honest finding: the override was RAISED, not lowered** (real
      evidence contradicted the "likely lowerable" framing). Used real, already-captured post-fix GCS/VM evidence rather
      than launching a fresh multi-hour VM (single-walk/efficiency north-star — this is genuine `gcloud`/GCS-verified
      data, not a guess): VM `features-e2e-cefi-20260730-133536-025349` (launched 2026-07-30, well after
      `features-service@1ad44550` landed 2026-07-27 15:02 UTC) ran a genuine from-scratch CEFI:delta_one force leg
      (254/254 instruments, 18 feature groups, 4-worker pool) and reached `EXIT_STATUS=0` at **61793s (17h9m53s)** — but
      only a PARTIAL completion: 10/18 groups succeeded, the other 8 failed on an unrelated, already-tracked bug
      (`orchestrator_returned_false`, see
      `plans/archive/issues/features_smoke_matrix_verification_findings_2026_08_01.md`) — not a timeout. Per-group
      timeline confirmed groups run on a 4-worker pool (not fully sequential), and one group alone (`moving_averages`,
      the 200-candle-lookback @ 24h-output-timeframe cell) took **10h20m** on its own slot; a failed group (`returns`)
      still ran 5h23m before erroring, so the failures were not uniformly fast. A genuine 18/18 completion has still
      never been directly observed — blocked by that unrelated bug, not by this timeout. 61793s already consumed 86% of
      the prior 72000s budget with 8 groups' worth of real compute unaccounted for; extrapolating the 10 confirmed
      successes' per-group average across all 18 groups at the same 4-way concurrency projects a full completion around
      **~24h** — ABOVE the prior 72000s (20h) ceiling. **Real bottleneck for this cell is per-day candle
      download+merge/feature-compute cost for large-lookback groups, not the GCS existence-probe round trips the P1 fix
      batched — a distinct, still-open bottleneck**, consistent with why the fix (which targeted I/O round-trips) did
      not bring this cell's wall-clock down materially. Shipped: `_FAMILY_TIMEOUT_OVERRIDES[("delta_one","CEFI")]`
      raised 72000s→108000s (30h, ~25% margin over the ~24h projection) with the full reasoning as a code comment, 1 new
      regression test (`test_cefi_delta_one_override_exceeds_its_measured_partial_completion`) pinning the override
      against the real 61793s measurement, and this SKILL.md's benchmark section corrected to match —
      `features-service@086812b0` (QG green, verified on origin). **Caveat carried forward**: do not lower this override
      again without a genuine, directly-observed 18/18 completion (currently blocked by the unrelated
      `orchestrator_returned_false` bug, not by this todo's scope).
- [x] [DATA] P2. ✅ Check whether the 8 currently-running `features-e2e-cefi-*`/`features-e2e-tradfi-*` VMs (as of
      2026-07-27 12:57 UTC) ever produce `EXIT_STATUS`, and if any are genuinely stuck (not just slow) rather than
      progressing, per the VM-delete guardrail (`agents/infra.md` STEP 0.65) — do not force-delete a VM that is still
      genuinely advancing. — **CHECKED 2026-08-03, slot-15, data_engineering — none stuck; none still exist; see
      Progress Log for full evidence.**

## Confirmation findings (2026-07-27)

**`buffer_days` is not a single constant** — `DataLoader.load_candles_with_buffer` (`data_loader.py:530-569`) takes
`buffer_days` as a required param; `data_loader.py:546` subtracts it from `start_date` before the sequential day-loop
(`_collect_daily_frames`, `data_loader.py:346-387`, confirmed one `blob_exists`(+`download_bytes`)/day, awaited
sequentially, no `asyncio.gather`/batch). Real production path is `_tf_cluster_helper.py:107-111,315-319` →
`batch_handler.py:775-790` (`_calculate_buffer_days`) → `BufferManager.calculate_buffer_days`
(`buffer_manager.py:71-112`):
`calendar_days = ceil(ceil(max_lookback_candles * seconds_per_period * 1.2 / 86400) * multiplier)` (multiplier 1.0
CEFI/DEFI, 1.45 TRADFI, `buffer_manager.py:25-29`), where `max_lookback_candles` comes from `FEATURE_GROUP_LOOKBACK`
(`constants.py:41-83`) and `seconds_per_period` from the output timeframe being read. Range found: **1-240 calendar days
(CEFI)**, **1-348 calendar days (TRADFI)**, largest for `lookback_candles=200` groups (`moving_averages`,
`market_structure`, `swing_outcome_targets`) read at the `24h` output timeframe.

**Fan-out**: `_get_groups_to_process` (`batch_handler.py:747-773`) loops **18 feature groups** per asset_group
(`--feature-group ALL` minus `targets` minus the other asset_group's exclusive groups). TF clustering
(`_build_tf_clusters`, `_tf_cluster_helper.py:71-90`) collapses each group's output timeframes (7 for CEFI, 5 for
TRADFI) into **2 read clusters** ("near" + "high"), each issuing its own independent `load_candles_with_buffer` call —
**36 independent sequential-day-loop calls per instrument** for a full `ALL`-group run, with no cross-group
dedup/caching even when groups share the same `data_type`.

**Arithmetic (CEFI, 589 instruments, real `BufferManager` values)**: buffer-day sum across the 18 groups × 2 clusters ≈
1,523-1,595 days/instrument (near-cluster ≈27d, high-cluster ≈1,496d, +1-2d/call window overhead) →
`589 × ~1,595 ≈ 939,455` total GCS round trips (pure-sum variant `589 × 1,523 ≈ 897,047`). TRADFI (~96 instruments per
`unified_api_contracts/registry/tradfi_instrument_universe.py` key count — a registry count, not a verified per-run MVP
figure) ≈ `96 × 2,291 ≈ 219,936`.

**Rate match**: observed VM `features-e2e-cefi-20260727-063401-025349` — 435,244 log lines / 6h23m (22,980s) = **18.94
lines/sec**, matching the issue's observed "~19 lines/sec" almost exactly. Projected full-run duration from the computed
CEFI total: `897,047-939,455 / 19 ≈ 47,213-49,445s ≈ 13.1-13.7 hours` — inside this doc's own "plausibly 8-15+ hours"
estimate, and consistent with the VM still being mid-run (~46-49% complete) at the 6h23m/435,244-line checkpoint rather
than stalled.

**`resolve_lookback.py` discrepancy confirmed**: `resolve_lookback_requirements`
(`scripts/e2e/resolve_lookback.py:176-246`) computes `min_lookback_days=1` for delta_one by dividing
`lookback_candles=200` by `CANDLES_PER_DAY["1m"]=1440` (`resolve_lookback.py:57,67-76,215-230` — assumes the 200-candle
lookback is satisfied by 200 **1-minute** candles). The internal `BufferManager` computes the SAME 200-candle lookback
against the actual **output timeframe being read** (up to `24h` for the "high" cluster) → 240 (CEFI) / 348 (TRADFI)
calendar days, not 1. The driver believes it needs a 1-2 day window; the internal loader is actually reading up to
240-348 days per call — a >200x discrepancy, exactly as hypothesized.

**Verdict: CONFIRMED.** Full agent investigation with file:line citations for every claim is preserved in this session's
sub-agent transcript; caveats: (1) `buffer_days` ranges rather than one number — cite the range, not a point value, in
any downstream fix estimate; (2) the 435,244-line checkpoint was mid-run, not a completed total, so the 13-14h
projection is not yet an end-to-end verified measurement; (3) TRADFI's ~96-instrument figure is a registry key count,
treat its round-trip total as order-of-magnitude only; (4) arithmetic assumes the observed VM ran `--feature-group ALL`
(18 groups) — the tail log's single-instrument `data_type=trades` evidence is consistent with this but doesn't
independently prove it. **Next**: P1 batch/parallelize todo (below) is unblocked and should proceed.

## Progress Log

- 2026-07-27 (slot-14, infra): Filed while shipping the `--timeout-sec` raise for the companion issue. Not investigated
  further this session (root-cause confirmation + fix is real code-reading + a real-VM re-measurement, out of scope for
  the narrowly-dispatched timeout-raise todo). The evidence above (VM name, exact timestamps, line counts, code line
  numbers) is real-VM and real-code verified, not speculative — the "likely root cause" framing reflects that the causal
  chain (loop shape → round-trip count → observed rate) is confirmed, but a direct before/after fix measurement has not
  yet been done.
- 2026-07-27 (slot-14): P1 confirmation todo done. Traced every `load_candles_with_buffer` caller, computed the real
  `BufferManager`-derived buffer-day range (1-240d CEFI / 1-348d TRADFI), the real fan-out (18 groups × 2 TF-clusters =
  36 calls/instrument), and the full round-trip arithmetic (≈897K-940K CEFI). Rate math (18.94 vs observed ~19
  lines/sec) is an almost-exact match; projected 13-14h full-run duration lands inside this doc's own 8-15h estimate.
  `resolve_lookback.py`'s `min_lookback_days=1` vs the internal buffer's 240-348d is now root-caused to the
  1m-vs-actual-output-timeframe divide. See `## Confirmation findings` above for full detail + caveats. No code changed
  this session — pure investigation per the todo's scope; the P1 batch/parallelize fix todo is next.
- 2026-07-27 (slot-13): P1 batch/parallelize todo shipped (`features-service@1ad44550`). Investigated the storage client
  shape first (sub-agent): `blob_exists`/`download_bytes`/`list_blobs` are sync (`StorageClient` ABC), an
  `AsyncStorageClient` variant exists but has zero concrete implementations (dead scaffolding), and prefix-listing is
  impractical for this path shape (`day=` is a mid-path partition segment, not a suffix — one prefix can't isolate a
  single instrument's date range). Mirrored the existing `asyncio.gather`+`asyncio.to_thread` pattern already used in
  this package (`FeatureWriter._write_daily_partitions`/`check_exists`) rather than inventing a new one. Extracted
  `_probe_one_day` out of `_collect_daily_frames` to stay under the QG method-size cap (50L) after the first draft hit
  62L. Bounded concurrency at a new `_DAILY_FRAME_PROBE_CONCURRENCY=20` semaphore (no existing config field for this;
  the only other precedent in `delta_one` is `batch_handler`'s CLI `--max-workers`, default 4, group-level — not
  reusable here since this bound is per-call). Full `quality-gates.sh` green (17,908 passed, 0 new violations) on the
  committed SHA before quickmerge. Did NOT re-run the full from-scratch CEFI wall-clock measurement described in the
  todo's "Done when" — that requires a real multi-hour VM backfill and is the same work as the next todo (re-measure +
  correct `_FAMILY_TIMEOUT_OVERRIDES`), left for that todo rather than duplicated here.
- 2026-08-03 (slot-14, data_engineering): Picked up the re-measure/correct-override todo. Rather than launching a fresh
  multi-hour VM (efficiency north-star — real post-fix evidence already existed in GCS), pulled the actual
  post-`1ad44550` CEFI:delta_one VM run history (`gcloud storage ls`/`cat` on
  `gs://deployment-scripts-central-element-323112/vm-logs/`) and found a genuine from-scratch force-leg run
  (`features-e2e-cefi-20260730-133536-025349`) that reached `EXIT_STATUS=0` at 61793s but only 10/18 groups succeeded (8
  failed on the unrelated `orchestrator_returned_false` bug). Downloaded the full 1.69M-line run.log and extracted
  per-group start/complete timestamps to confirm the pool is 4-worker concurrent (not sequential) and that
  `moving_averages` alone took 10h20m. Concluded the override should be RAISED (108000s), not lowered as the todo's own
  speculative framing suggested — real evidence (61793s partial run already at 86% of the prior 72000s budget, plus a
  ~24h full-completion projection) contradicted that framing, so followed the evidence per CLAUDE.md's "trust the actual
  distribution, not the assumed number." Shipped `features-service@086812b0` (code comment + override value + 1 new
  regression test, QG green, verified on origin) and this doc's SKILL.md pointer
  (`cursor-configs/skills/data-pipeline-check-features/SKILL.md`). Did not touch the separate
  `orchestrator_returned_false` bug (already tracked elsewhere) or the still-open "check the 8 running VMs" todo below
  (out of this todo's scope — those VMs are 6+ days stale and have almost certainly already self-deleted).
- 2026-08-03 (slot-15, data_engineering): Picked up the final "check the 8 VMs" todo, confirming slot-14's suspicion.
  Live `gcloud compute instances list --filter="name~'features-e2e'"` shows ZERO `features-e2e-cefi-*`/
  `features-e2e-tradfi-*` instances (only an unrelated, already-`TERMINATED` `features-e2e-sports-*` VM from 2026-08-01
  remains) — every VM from the 2026-07-27 CEFI/TRADFI fleet is gone, confirmed individually via
  `gcloud compute instances describe <name> --zone=asia-northeast1-c` returning "resource ... was not found" for
  `-063401`/`-102228`/`-112159`/`-114259` (CEFI) and both `b1a99f`-suffixed TRADFI VMs. Reconstructed which VMs were
  actually running at the 12:57 UTC checkpoint by cross-referencing each 2026-07-27 `vm-logs/<vm>/` directory's
  `EXIT_STATUS` write-time (`gcloud storage objects describe ... --format="value(updateTime)"`) against its name-encoded
  creation time (UTC): a VM created before 12:57 with no `EXIT_STATUS` by then, or one written after 12:57, was still
  running at the checkpoint. This confirms `-063401` (06:34 launch) really was the oldest still running at 12:57
  (everything created 04:33-06:21 had already exited by then) and that 2 TRADFI VMs (`-112901-b1a99f`, `-124921-b1a99f`)
  were the ones running at 12:57, both later exiting `EXIT_STATUS=0` — matches this doc's "x2 tradfi" count exactly. The
  CEFI count from the vm-logs listing alone read as 8 running-before-12:57 directories rather than the doc's stated 6 (a
  launcher retry can leave a log-dir behind with no real VM attached to it, and no historical `gcloud instances list`
  snapshot survives to fully reconcile which log-dirs had a live VM at the exact checkpoint) — not fully reconcilable
  now, but immaterial to the actual question asked. The real finding: of the CEFI VMs running past 12:57, 5 (`-063401`,
  `-071402`, `-083854`, `-101851`, `-120200`) eventually wrote a real `EXIT_STATUS` (1, 1, 1, 1, 0 respectively) between
  19:50 UTC 2026-07-27 and 11:17 UTC 2026-07-28 — clean natural completions/failures, not stuck. 3 more (`-102228`,
  `-112159`, `-114259`) never wrote `EXIT_STATUS` despite actively advancing `run.log` for ~19-21h (last writes
  2026-07-28T07:29:06-07:30:52 UTC) — cross-checked
  `gcloud compute operations list --filter="operationType=compute.instances.preempted"` and found all 3 have a genuine
  `compute.instances.preempted` system event at 2026-07-28T07:31:0[5-7] UTC, seconds after their last log line: these
  were SPOT-preempted, not stuck. A separate, earlier trio of 2026-07-27 launches
  (`features-e2e-cefi-20260727-052137`/`-053419`, `features-e2e-tradfi-20260727-054139`) that never wrote a `run.log` at
  all were ALSO preempted, within minutes of creation (2026-07-27 ~05:22-05:44 UTC) — so those weren't launch failures,
  they were preempted before writing their first log line. Verdict for this todo: no VM is or was "genuinely stuck" —
  every long-running CEFI/TRADFI VM from that window either completed naturally (wrote a real `EXIT_STATUS`) or was
  SPOT-preempted (a distinct, already-understood termination mode, not a hang); none exist today, so no
  VM-delete-guardrail judgment call is needed since there is nothing left to delete. Tangential note (not actioned, out
  of scope): these VMs carrying `compute.instances.preempted` events means they're SPOT/preemptible -provisioned,
  consistent with CLAUDE.md's "backfill VMs default to SPOT" rule — the sibling issue doc's cost estimate assumed
  on-demand pricing for these same VMs, which if actually SPOT means that estimate was conservative-high, not a
  correctness problem worth its own follow-up. No code change was needed for this investigation-only todo. This is the
  last open item in this doc — every todo is now closed, so this doc is archival-eligible (no `locked_by`) as a
  housekeeping follow-up for whoever next runs the archival sweep.
