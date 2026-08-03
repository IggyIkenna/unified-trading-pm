---
doc_type: issue
title:
  "CEFI:cross_instrument's delta-one loading step hung twice in a row (44min, then 14min) on the same VM shape —
  suspected GCS-listing reliability issue, not a code regression"
summary: >-
  Re-verifying features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md's P2 re-verify todo, two
  independent CEFI:cross_instrument re-check VMs (`features-e2e-cefi-20260803-144527-526e13`,
  `features-e2e-cefi-20260803-154630-526e13`) both hung at the identical log line (`"Loading delta-one features from
  gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-07-05/ timeframe=15s"`,
  `batch_handler.py::_ingest_delta_one`, which calls `storage_client.list_blobs(bucket, prefix=day_prefix)` then filters
  client-side) — the run.log AND the GCS heartbeat blob both froze mid-run (44+ min and 14+ min respectively, well past
  the 60s heartbeat cadence), Cloud Monitoring CPU utilization flatlined at a suspiciously constant ~19-20% (real work
  fluctuates; a flat plateau reads as a stuck/spinning thread), and neither VM produced any further output before being
  deleted. This is UNRELATED to either of this session's two shipped multi_timeframe fixes (`cross_instrument`'s loader
  code was never touched) and unrelated to root cause C's earlier OOM fix (verified separately — this hang happens
  BEFORE the compute stage even starts, during the initial data load). Both VMs were confirmed genuinely stalled (not
  just slow) per the infra/data_engineering craft's VM-delete guardrail (heartbeat blob age + run.log tail + zero output
  progress, all three independently confirmed) and deleted; a third relaunch is in flight as part of the parent todo,
  not part of this doc's own scope.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [infra, features-service, pipeline-e2e-check, cross-instrument, gcs-listing, hang, vm-reliability]
related:
  [
    /plans/active/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
    /plans/active/issues/features_cross_instrument_smoke_verify_unbounded_memory_second_ao_outage_2026_08_01.md,
  ]
created: 2026-08-03
priority: P2
parent_epic: infrastructure_master
source:
  "slot-6, data_engineering, discovered while re-running
  features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md's P2 re-verify todo for CEFI:cross_instrument,
  2026-08-03"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    features-service/features_service/cross_instrument/cli/handlers/batch_handler.py,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/active/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
  ]
resolved_by:
---

# CEFI:cross_instrument's delta-one loading step hung twice in a row — suspected GCS-listing reliability issue

## What I found

While re-verifying the affected 6 shards from `features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`'s
P2 todo, CEFI:cross_instrument's re-check VM hung on **two independent attempts in a row**, both at the exact same point
in the code:

```
INFO Loading delta-one features from gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-07-05/ timeframe=15s
```

(`batch_handler.py::_ingest_delta_one`, line ~223 — calls `storage_client.list_blobs(bucket, prefix=day_prefix)` then
filters the returned paths client-side for `f"/timeframe={timeframe}/" in p`.)

**Attempt 1** — VM `features-e2e-cefi-20260803-144527-526e13`: run.log and the GCS heartbeat blob
(`vm-heartbeat/<vm>.txt`) both froze at `2026-08-03T14:51:03Z`/`14:51:05Z` (heartbeat content stuck on `"starting"`) and
never advanced again — checked repeatedly over 44+ minutes. Cloud Monitoring CPU utilization for the VM rose normally
through boot/setup (~2-19% through 14:52Z) then flatlined at a suspiciously constant ~19-20% from 14:53Z onward for the
entire remaining window — real compute work fluctuates; a dead-flat plateau for 30+ minutes reads as a stuck/spinning
thread, not genuine ongoing work. `gcloud compute ssh` (via the `unified-trading-sa` ambient identity) timed out rather
than connecting, consistent with (but not conclusive proof of) a genuinely wedged VM. Deleted after confirming all three
of the craft's VM-delete-guardrail signals (heartbeat age, run.log tail, zero manifest/output progress).

**Attempt 2** — VM `features-e2e-cefi-20260803-154630-526e13` (a clean relaunch, ~1h later): the IDENTICAL symptom
reproduced — run.log and heartbeat blob both froze at `15:52:48Z`/on `"starting"`, CPU flatlined at the same ~19-20%
plateau from ~15:55Z onward, checked again 14+ minutes later with zero progress. Deleted the same way.

**Not yet root-caused** — this doc exists to TRACK the finding, not diagnose the underlying mechanism (out of scope for
the verification-only todo that surfaced it). Candidate hypotheses, none confirmed:

- `list_blobs()` on a large/growing prefix (CEFI's `day=2026-07-05/` delta-one tree has grown substantially across this
  session's multiple re-check runs — many feature_groups × timeframes × ~900 instruments) hitting a pagination bug, a
  client-library retry loop with no visible logging, or GCS-side throttling that manifests as a silent stall rather than
  a clean error.
- A network path issue specific to this VM shape/zone that happens to reproduce at the same code point twice by
  coincidence (less likely given the identical CPU signature both times, but not ruled out).
- Something in the `-test-` bucket's growing object count specifically (as opposed to the equivalent PROD-scale listing,
  which this exact code path has presumably handled without incident elsewhere) crossing a threshold that triggers
  pathological behavior.

## Why it matters

- This is the SAME `_ingest_delta_one` code path flagged in
  `features_cross_instrument_smoke_verify_unbounded_memory_second_ao_outage_2026_08_01.md` as a prior OOM risk (fixed by
  scoping the listing to one `timeframe=` rather than the whole day) — worth checking whether that fix's own
  `list_blobs()` call is now hitting a DIFFERENT failure mode (hang instead of OOM) as the corpus it lists keeps
  growing.
- Two-for-two reproduction on the exact same log line, with the exact same CPU signature, on unrelated VM instances ~1
  hour apart, is a real pattern — not a one-off flake. If this recurs on a genuine PROD backfill (not just the `-test-`
  bucket this session used), it would silently stall a real cross_instrument compute run indefinitely (no crash, no
  error, just an unresponsive VM that only a heartbeat-staleness check would ever catch).
- Per the workspace's no-fire-and-forget / VM-preemption-and-billing-waste rules, a VM that hangs indefinitely without
  erroring is a real billing-waste + reliability risk if it isn't caught by monitoring.

## Todos

- [ ] [DIAG] P2. **Root-cause the hang.** Reproduce deliberately (relaunch CEFI:cross_instrument against a day with a
      similarly large delta-one tree) with closer monitoring — SSH in early (before it can wedge) and capture a stack
      trace / `py-spy dump` of the stuck process, or add verbose logging around `list_blobs()`'s pagination to see
      whether it's making progress internally that just never logs. Repo: features-service
      (`features_service/cross_instrument/cli/handlers/batch_handler.py::_ingest_delta_one`). Done when: the actual
      stuck call is identified (not just re-confirmed to hang) and a fix or a bounded-timeout/retry wrapper is proposed.
- [ ] [DIAG] P3. Check whether this is `-test-`-bucket-specific (a smaller bucket that's grown unusually dense from
      repeated same-day re-check runs across a short interval) or would also reproduce against a PROD-scale bucket with
      a naturally large `day=` tree. If `-test-`-specific, consider whether cross_instrument's e2e check driver should
      periodically prune old `-test-` runs' partial trees, or the finding is a false alarm.

## Progress Log

- 2026-08-03 (slot-6, data_engineering): filed after two independent hangs on the same shard/step while re-verifying
  `features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`'s P2 todo. Not investigated further this
  session (verification-only todo scope) — a third relaunch attempt for the parent todo's own purposes is tracked there,
  not here.
