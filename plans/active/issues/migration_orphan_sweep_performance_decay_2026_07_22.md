---
doc_type: issue
title:
  migration_orphan_sweep.py object-walk exhibits a severe, reproducible throughput decay (~11,000/s → 51/s) that makes
  it unusable on defi/prediction/cefi-scale buckets — 3 of 4 relaunched orphan-sweep VMs never completed
summary: >-
  The 2026-07-22 orphan-sweep VM relaunch (estate_orphan_assessment_2026_07_21.md todo 3) initially looked healthy — a
  30-min watchdog window showed defi/tradfi/prediction climbing steadily. A later check (after a ~10hr real-world gap)
  showed the true outcome — only tradfi actually finished. defi and prediction both hit an identical, severe throughput
  cliff at ~1.15-1.2M objects (11,000/s → 582/s in one 50K-object step, then continuous smooth decay down to ~51/s ten
  hours later, never recovering) and were still running-but-crawling when SPOT-preempted. cefi failed even earlier — two
  separate launch attempts both produced ZERO log/heartbeat output for 30-40+ minutes before being killed as stalled.
  This is a genuine, reproducible performance bug in the tool, not an infra flake — it needs a real fix before this
  sweep can be re-attempted on any large asset_group.
status: open
nature: issue
asset_group: [defi, cefi, prediction]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [orphan-sweep, performance, algorithmic-complexity, gcs, vm, migration-orphan-sweep, stall]
related:
  [
    estate_orphan_assessment_2026_07_21.md,
    ../../codex/02-data/orphan-object-detection.md,
    ../../codex/02-data/reconciliation-census-and-compute-tiers.md,
  ]
created: 2026-07-22
last_updated: 2026-07-22
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  found while monitoring the 2026-07-22 orphan-sweep VM relaunch (estate_orphan_assessment_2026_07_21.md todo 3),
  confirmed after a ~10hr real-world gap exposed the VMs' true (non-)completion state
depends_on: []
---

# migration_orphan_sweep.py performance decay (2026-07-22)

## Measured evidence — defi and prediction hit an IDENTICAL cliff

Both VMs were launched within the same minute (`orphan-sweep-defi-20260722-050426`,
`orphan-sweep-prediction-20260722-050511`) and both logged this exact shape (raw `run.log` excerpts, GCS bucket
`deployment-scripts-central-element-323112/vm-logs/{vm}/run.log`):

**defi:**

```
2026-07-22 05:08:46,221 INFO   1200000 objects swept (11046/s)
2026-07-22 05:42:45,641 INFO   1250000 objects swept (582/s)
2026-07-22 06:27:41,767 INFO   1300000 objects swept (268/s)
2026-07-22 07:15:27,369 INFO   1350000 objects swept (175/s)
2026-07-22 08:01:53,413 INFO   1400000 objects swept (133/s)
2026-07-22 08:50:10,712 INFO   1450000 objects swept (108/s)
2026-07-22 09:37:16,543 INFO   1500000 objects swept (92/s)
2026-07-22 10:24:06,765 INFO   1550000 objects swept (81/s)
2026-07-22 11:10:38,914 INFO   1600000 objects swept (73/s)
2026-07-22 11:57:32,840 INFO   1650000 objects swept (67/s)
2026-07-22 12:44:38,583 INFO   1700000 objects swept (62/s)
2026-07-22 13:31:44,209 INFO   1750000 objects swept (58/s)
2026-07-22 14:18:59,846 INFO   1800000 objects swept (54/s)
2026-07-22 15:06:31,309 INFO   1850000 objects swept (51/s)
```

**prediction (independent bucket, same shape, same ~1.15-1.2M cliff point):**

```
2026-07-22 05:10:24,662 INFO   1150000 objects swept (10427/s)
2026-07-22 05:43:37,423 INFO   1200000 objects swept (571/s)
2026-07-22 06:33:12,404 INFO   1250000 objects swept (246/s)
2026-07-22 07:22:14,092 INFO   1300000 objects swept (162/s)
2026-07-22 08:11:12,505 INFO   1350000 objects swept (123/s)
2026-07-22 08:59:49,853 INFO   1400000 objects swept (101/s)
2026-07-22 09:47:56,204 INFO   1450000 objects swept (87/s)
2026-07-22 10:35:40,267 INFO   1500000 objects swept (76/s)
2026-07-22 11:24:13,345 INFO   1550000 objects swept (69/s)
2026-07-22 12:12:53,077 INFO   1600000 objects swept (63/s)
2026-07-22 13:01:56,229 INFO   1650000 objects swept (58/s)
2026-07-22 13:51:14,454 INFO   1700000 objects swept (54/s)
2026-07-22 14:40:24,910 INFO   1750000 objects swept (51/s)
```

Note the logged rate is `seen / (time.time() - t0)` — a **cumulative average since start**, not an instantaneous rate
(`run_sweep()` in `instruments-service/scripts/migration_orphan_sweep.py:597`). A cumulative average can only decay this
smoothly and continuously (never leveling off, ~46 minutes per 50K-object step by the last checkpoint) if the
**per-object cost keeps growing** — a one-time slow patch of the bucket would drag the average down once and then it
would stabilize or recover; it does not here, in either bucket, at nearly the identical absolute object count. Two
independent buckets hitting the same wall at the same count is a strong signal this is a process-internal/algorithmic
threshold, not a data-region characteristic of either bucket specifically.

Both VMs were still alive and technically progressing (not crashed) when GCP preempted them (SPOT) roughly ten hours
after launch, per `gcloud compute operations list` showing `compute.instances.preempted` events. **Neither wrote a final
report** (`_index/audit/orphan_sweep_{ag}.parquet` for both buckets is still the stale 2026-06-11 file) — they would not
have finished for a very long time at the observed decay trajectory even without the preemption.

## cefi — worse, and different: zero output at all, twice

Two separate cefi launch attempts (`orphan-sweep-cefi-20260722-050405`, then `-055006` after killing the first as
stalled) both produced:

- **Zero bytes ever written to `run.log`** (confirmed via `gcloud storage cat` returning "matched no objects" for the
  second attempt; the first attempt's `run.log` existed but never advanced past the startup-script trace).
- **Zero updates to the independent GCS-blob heartbeat sidecar** (`vm-heartbeat/{vm}.txt`) past its initial `"starting"`
  write at launch+~2min — this sidecar is a totally independent `while true; do ...; sleep 60; done &` bash loop
  backgrounded BEFORE the Python process starts, so its silence too (not just the tee'd Python output) is a strong
  signal of genuine system-wide unresponsiveness, not merely "the sweep is slow."
- Serial console confirmed **completely silent** (no kernel/systemd/process messages at all) for 34+ minutes on the
  first attempt.
- The process DID launch correctly (confirmed via serial console: `Task launched PID: 7144`, correct command line) —
  this is not the VM_TASK dispatch-branch bug (that was found and fixed separately, see
  `estate_orphan_assessment_2026_07_21.md` todo 3's Progress Log).

Working hypothesis (unverified — no SSH/profiling access from this environment): `run_sweep()` calls
`_load_manifested_cells()` (`migration_orphan_sweep.py:615`) **before the walk loop and before any log line**, which
does a single unchunked `client.download_bytes(bucket, "_index/availability_index.parquet")` followed by
`pd.read_parquet(io.BytesIO(raw))`. cefi's consolidated availability index is very likely the largest of any
asset_group's (most venues, longest history, highest tick-data volume) — a multi-GB `BytesIO`-buffered full-file
download + in-memory parquet decode on an `e2-standard-4` (16GB RAM) could plausibly consume enough memory to cause
severe system-wide swap thrashing, which would freeze the Python process AND the independent heartbeat bash loop AND
starve the tee-wrapper's upload cadence simultaneously — matching every symptom observed. This is the same class of
scale problem that already broke an in-session (non-VM) attempt at this same load step for `defi`'s ~1.8GB index
(`requests.exceptions.ChunkedEncodingError`, see `estate_orphan_assessment_2026_07_21.md`'s "NOT COMPLETED" section) —
if cefi's index is bigger still, a VM with more resilient networking would not save it if the failure mode is memory
exhaustion rather than a flaky connection.

## Working hypothesis for the defi/prediction decay (unverified — needs profiling)

`run_sweep()`'s per-object loop (`migration_orphan_sweep.py:556-599`) does bounded, O(1)-ish work per object (`Counter`
increments, `SizingRollup.add` — a `dict.setdefault` + list-mutation, `actionable.append`) — nothing there obviously
scales with total objects seen. The one genuinely expensive per-object operation is `_footer_row_count()` (a real
network `download_bytes` call), gated to objects classified `ORPHAN_REAL` under 256KB. Two candidate explanations, not
distinguished without live profiling:

1. **GCS client-side rate-limit backoff compounding.** If the footer-read rate crosses a GCS per-second quota once the
   walk reaches a region of the bucket dominated by small orphan-candidate objects, and the client library's
   retry/backoff grows with consecutive throttled requests, the AVERAGE cost per object would keep climbing exactly like
   this — worse as more requests queue up.
2. **Growing in-process memory / GC pressure.** `actionable: list[SweptObject]` and `SizingRollup.by_cell` are unbounded
   accumulators for the lifetime of the walk. If a large fraction of objects in this bucket region classify as class-B/E
   (both go into `actionable`), the growing live-object count could increase Python GC pause overhead per iteration,
   though this is a much weaker effect than (1) for dataclasses without reference cycles.

Neither is confirmed. This section should be read as "where to look first," not a diagnosis.

## Impact

- **The orphan-sweep tool cannot currently complete a single walk on defi, prediction, or cefi** — the three largest
  measured asset_groups by this proxy. Only tradfi and sports (already measured 2026-06-11/2026-07-21) have ever
  produced a report with this tool.
- `estate_orphan_assessment_2026_07_21.md` todo 3 was marked **"CONFIRMED HOLDING"** based on a 30-minute watchdog
  window that ended before the cliff manifested in the log — that assessment is corrected here and in that doc's
  Progress Log. The dispatch-branch fix (`deployment-service@74eca154`) IS real and necessary (it fixed a hard crash
  within 3 minutes) but was insufficient — it just unblocked the walk far enough to reach this SEPARATE, deeper bug.
- Relaunching defi/prediction/cefi orphan-sweep again with no code change will very likely reproduce the same failure
  and burn another ~10+ hours of SPOT VM time for no report.

## Todos

- [ ] 1. [CODE] P1. **Profile a real run** (e.g. `py-spy dump`/`cProfile` on a VM, or a bounded local repro against a
      copy of defi's or prediction's bucket listing) to find the actual per-object cost that grows over time — confirm
      or rule out the GCS-backoff vs. GC-pressure hypotheses above.
- [ ] 2. [CODE] P1. **Bound or stream `_load_manifested_cells()`'s index download** for large asset_groups (chunked
      read, or process the availability index in row-group batches rather than one `BytesIO` — same class of fix already
      needed for the in-session ChunkedEncodingError case) — this is the more likely cefi-specific root cause and should
      be fixed regardless of what the defi/prediction profiling finds.
- [ ] 3. [CODE] P2. Once root-caused, fix the defi/prediction decay (likely: cap/throttle the footer-read
      ThreadPoolExecutor-equivalent concurrency explicitly, or move the footer-read entirely into the SEPARATE,
      already-controlled `backfill_orphan_class_e_sports.py`-style footer-verify pass rather than doing it inline during
      classification).
- [ ] 4. [REVIEW] P2. Add a checkpoint/resume mechanism to `migration_orphan_sweep.py` itself (it currently has NONE — a
      preemption mid-walk is a full restart-from-scratch, per the tool's own docstring) OR accept that as a known
      limitation and ensure `ON_DEMAND=true` is used for any future large-AG attempt until this doc's fixes land, since
      SPOT preemption of an unresumable multi-hour walk is pure wasted compute.
- [ ] 5. [DATA] P1. Once fixed, re-run orphan-sweep for defi/prediction/cefi to actual completion — this is a
      prerequisite for `estate_orphan_assessment_2026_07_21.md`'s cefi/defi/tradfi orphan assessment, which remains
      genuinely unmeasured for these 3 asset_groups (tradfi is now measured, sports was measured 2026-07-21).

## Lesson (do not re-learn)

**A 30-minute watchdog window is not sufficient evidence of "holding" for a tool with no historical completion-time
baseline.** The earlier assessment ("dispatch fix CONFIRMED HOLDING... no crash") was true as far as it went — the
crash-on-launch bug really was fixed — but a healthy-looking climbing counter over 30 minutes said nothing about whether
the SAME counter would still be climbing at a useful rate an hour later. Measure against a known per-asset_group
historical baseline (tradfi's own first successful run, or sports's) before calling a long-running tool healthy, not
just "still running, still climbing."
