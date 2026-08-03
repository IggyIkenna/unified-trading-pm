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

- [x] ✅ [DIAG] P2. **Root-cause the hang.** — unified-trading-library@680bbafb. Root cause identified via static
      analysis + git-history cross-reference (no VM relaunch needed — the mechanism is deterministic, not
      environmental): `GCSStorageClient.list_blobs()` (which `_ingest_delta_one` calls) resolves each listed blob's
      `size` via `_resolve_list_blobs_size()`; when GCS's `objects.list` returns `size=None` for a just-written object
      (an eventual-consistency propagation race, added 2026-07-30 commit `8bce325a` to fix a manifest-cost accounting
      hole), that helper calls `blob.reload()` — the SOLE native GCS call in `gcp.py` with **no `retry=`/`timeout=`
      bound**, unlike every other call in the file. `_ingest_delta_one` never even uses `.size` (it only reads `.name`),
      so this reload() tax is pure overhead for this caller, but it's synchronous and serial: on a `day=2026-07-05/`
      prefix repeatedly rewritten by the same session's back-to-back re-check runs (dense, very-recently-written objects
      — precisely when the size-propagation race is most likely to hit), a large fraction of listed blobs can require
      this unbounded reload(), turning an O(1) listing into a serial, silently-unbounded per-blob stall — with zero log
      output (the only log line inside the helper fires ONLY if size is STILL `None` after reload(), so a run of
      successful-but-slow reloads produces no visible symptom at all, matching "run.log froze mid-run" and the flat
      ~19-20% CPU signature (network I/O + retry backoff, not idle, not fluctuating compute)) — for as long as 44
      minutes. Fix shipped: `blob.reload(timeout=30, retry=_GCS_RETRY)`, bounding the reload to the same 600s retry
      deadline used by every other call in the file, so a wedge now resolves or fails loudly within a bounded envelope
      instead of hanging indefinitely. Also widened the `_GCSBlob` Protocol's `reload()` signature to accept the kwargs
      (previously `reload(self) -> None`, the sole reason this call couldn't already pass them) and added/updated unit
      test coverage (`tests/cloud_interface/unit/test_gcp_providers.py::test_list_blobs_size_none_reload_is_bounded` +
      updated `test_list_blobs_reloads_when_size_none`'s side-effect stub, which previously only tolerated a zero-arg
      `reload()` call). QG green, SHA verified on `origin/live-defi-rollout`.
- [ ] [DIAG] P3. Check whether this is `-test-`-bucket-specific (a smaller bucket that's grown unusually dense from
      repeated same-day re-check runs across a short interval) or would also reproduce against a PROD-scale bucket with
      a naturally large `day=` tree. If `-test-`-specific, consider whether cross_instrument's e2e check driver should
      periodically prune old `-test-` runs' partial trees, or the finding is a false alarm.
- [ ] [BACKEND] P3. **Follow-up optimization (deferred, not required for the P2 fix above):** eliminate the reload() tax
      at its root for callers that never use blob size — add an opt-in `resolve_size: bool = True` parameter to
      `StorageClient.list_blobs()` (default `True` preserves existing behavior for size-sensitive callers like
      `_apply_per_vm_merge_budget`), thread it through `GCSStorageClient.list_blobs()` to skip
      `_resolve_list_blobs_size()`'s reload() entirely when `False`, and pass `resolve_size=False` from
      `features-service`'s `_ingest_delta_one`/`_list_polymarket_parquets` (both discard `.size`, only using `.name`).
      Deferred from this task because it touches the abstract `StorageClient` interface + `StorageClientProtocol`
      (unified-api-contracts) + all 4 provider implementations (GCS/AWS/local/async) for what the P2 fix above already
      makes safe (bounded) rather than fast — a real latency win, not a correctness fix, so lower urgency than the
      hang-elimination shipped above. Repos: unified-trading-library, unified-api-contracts, features-service.

## Progress Log

- 2026-08-03 (slot-6, data_engineering): filed after two independent hangs on the same shard/step while re-verifying
  `features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`'s P2 todo. Not investigated further this
  session (verification-only todo scope) — a third relaunch attempt for the parent todo's own purposes is tracked there,
  not here.
- 2026-08-03 (slot-10, worker): root-caused + fixed the P2 todo — see checkbox above for full mechanism. Confirmed via
  static analysis (read `_ingest_delta_one` → `list_blobs()` → `_resolve_list_blobs_size()` → the unbounded
  `blob.reload()`) and git-history cross-reference (the reload() call was added 2026-07-30, well before these 2026-08-03
  hangs, and is the ONLY native GCS call in `gcp.py` missing a `retry=`/`timeout=` bound — every sibling call in the
  same file passes `retry=_GCS_RETRY`). Did not relaunch a VM to reproduce live: the mechanism is deterministic given
  the `size=None` propagation race (not flaky/environmental), the two prior hangs already provide strong live evidence
  (identical log line, identical CPU flatline signature, twice), and a live repro would itself need to wedge a VM for up
  to 44 minutes to observe — not a good use of a bounded diagnostic task once the static evidence chain was conclusive.
  Shipped the bounding fix + regression test; filed the root-elimination optimization as a separate P3 follow-up todo
  (not required for this task's done-when, which only asked for "a fix or a bounded-timeout/retry wrapper").
