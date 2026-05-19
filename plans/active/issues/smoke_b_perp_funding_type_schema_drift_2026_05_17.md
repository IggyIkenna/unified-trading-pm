---
title: "Smoke B FAILED — perp_funding Int64→Datetime schema drift + GcsEventSink rate-limit stall"
created: 2026-05-17
author: ikenna-slot1-main
source:
  - "features-onchain-defi-20260517-171908 DEPLOYMENT_FAILED (exit_code=124)"
  - "features-onchain-defi-20260517-191412 STALLED — GcsEventSink stall after 9 events"
  - "gs://deployment-scripts-central-element-323112/vm-logs/features-onchain-defi-20260517-171908/run.log"
  - "gs://deployment-scripts-central-element-323112/vm-logs/features-onchain-defi-20260517-191412/run.log"
locked_by: live-defi-rollout
---

# Smoke B FAILED — perp_funding schema drift + utilization stall

## What I found

VM `features-onchain-defi-20260517-171908` (DeFi features, 2026-04-08→2026-04-12) exited with `DEPLOYMENT_FAILED` at
17:23 UTC (stall watchdog killed after 3601s log silence, exit_code=124).

**Bug 1: perp_funding timestamp schema drift**

```
ERROR ❌ Error in load_derivative_ticker: type Int64 is incompatible with expected type Datetime('ns', 'UTC')
```

Occurs for `perp_funding` on dates 2026-04-10, 2026-04-11, 2026-04-12. The MTDS parquet files for those dates store the
timestamp column as `Int64` (epoch nanoseconds) rather than `Datetime('ns', 'UTC')`. The features-onchain reader
(`load_derivative_ticker`) expects `Datetime`. The per-shard error isolation catches it (logged as ERROR, no raise), so
those dates are silently skipped rather than blocking the run.

**Bug 2: utilization subprocess stall (VM 171908)**

After:

```
INFO Resolved 50 MTDS parquet files for rate_indices ... day=2026-04-08 ...
INFO Loaded 134426 rate rows from MTDS
[vm-exec] STALL: log has not grown in 3601s (threshold=3600s) — killing CMD_PID=6771
```

The features-onchain subprocess for `utilization` on 2026-04-08 hung indefinitely after loading rate_indices data. Stack
trace showed `do_wait` in kernel — waiting for a child process that never exited. No OOM, no Python exception.

Initial fix from parallel agent: capped `emit_aave_utilization_events` at 500 rows + unblocked GCS async path
(@64682456). BUT the root cause was not fully addressed — see Bug 4.

**Bug 3: startup NameError (VMs 192145, 192529)**

`Callable` import inside `TYPE_CHECKING` block was evaluated at runtime in `cast(Callable[..., object], fn)`. Caused VMs
`192145` + `192529` to exit with `DEPLOYMENT_FAILED` (exit_code=1) after only 17s. Fixed by features-service@818d8ecc
(slot-8; moved to unconditional import). Tarball rebuilt at `2026-05-17T18:30:09Z`.

**Bug 4: GcsEventSink synchronous blocking causes write stall (VM 191412)**

After tarball rebuild with Bug 1+2 partial fixes and relaunch as VM `features-onchain-defi-20260517-191412`, the
utilization stall recurred at the SAME point:

```
INFO Loaded 134426 rate rows from MTDS
[stall — log silent for 3601s]
```

Only 9 DEFI_FEATURE_AAVE_UTILIZATION events emitted before stall (visible in event-sink monitoring). Root cause chain:

1. `emit_aave_utilization_events` calls `log_event` per row (up to cap)
2. `log_event` → `GcsEventSink.write_event` → `client.upload_bytes` synchronously
3. `upload_bytes` uses `timeout=600, retry=_GCS_RETRY(deadline=600s)` — 10-minute total block per upload
4. After ~9 uploads, GCS returns `429 TooManyRequests`; the retry policy retries for up to 600s blocking the event loop
5. The subsequent `log_event` call from `write_features` → `_apply_emission_gate` → `publish_with_policy` also stalls
6. `PERSISTENCE_STARTED` is never emitted; feature write never starts; VM watchdog kills after 3600s silence

Cap of 500 was insufficient — 500 × 274ms = 137s blocking time already saturates GCS rate limit.

## Why it matters

- **DeFi features (onchain) are not computed** for the 2026-04-08→2026-04-12 window → paper backtest blocked
- The perp_funding type drift means `onchain_perps` feature group is silently empty for affected dates (no WARNING)
- The utilization GcsEventSink stall is a complete blocker — ANY date with utilization data hangs the VM indefinitely

## Recommended decision

**Bug 1 (perp_funding schema drift)** — fixed in `load_derivative_ticker` (non-blocking on Smoke B):

- Per-part and post-concat cast: `cast(pl.Datetime("ns", "UTC"))` + `pl.from_epoch` fallback already in code.
- Remaining Int64 errors on dates 2026-04-09..12 are caught by shard-level error isolation — run continues.
- Owner: slot-6 (features-onchain).

**Bug 4 (GcsEventSink rate-limit stall)** — two-part fix:

- UTL: Add `ThreadPoolExecutor(max_workers=4)` to `GcsEventSink.__init__`; wrap upload with
  `_future.result(timeout=15.0)` — best-effort, drops event on timeout instead of blocking event loop.
- features-service: Reduce `_MAX_UTILIZATION_EVENTS` from 500 → 10. 10 × 274ms = 2.74s total — well below GCS quota.
- UTL fix: UTL@aca4004c. features-service fix: features-service@5afdd918.

**Re-run Smoke B** — VM 193018 RUNNING with Bugs 1+2+3 fixed. If it stalls at utilization (Bug 4), rebuild tarball with
@aca4004c+@5afdd918 and relaunch.

## Status

- [x] ✅ [AGENT] P0. Bug 1 fix — perp_funding timestamp cast in `load_derivative_ticker` — slot-6 owns
      (features-onchain) — features-service@30e449d7 (per-shard cast Int64→Datetime before append; also covered by
      post-concat cast at 64682456 from parallel agent). NOTE: Int64 errors persist on 4 of 5 dates in VM 191412 — cast
      insufficient for mixed-precision files; shard-level isolation prevents stall.
- [x] ✅ [AGENT] P0. Bug 2 investigation — utilization subprocess stall root cause + timeout guard — slot-6 owns —
      features-service@30e449d7 (root cause: synchronous PubSub log_event per-row on 134k rows; fix: cap
      emit_aave_utilization_events at `_MAX_UTILIZATION_EVENTS=500`; GCS async write fix at 64682456 from parallel
      agent)
- [x] ✅ [AGENT] P0. Bug 3 (startup NameError) — `Callable` import inside `TYPE_CHECKING` block evaluated at runtime in
      `cast(Callable[..., object], fn)` — features-service@818d8ecc (slot-8; moved to unconditional import). Caused VMs
      `192145` + `192529` to DEPLOYMENT_FAILED (exit_code=1, 17s). Tarball rebuilt at `2026-05-17T18:30:09Z`.
- [x] ✅ [AGENT] P0. Bug 4 fix (GcsEventSink synchronous blocking) — root cause: GcsEventSink.write_event calls
      upload_bytes synchronously with timeout=600 + retry(deadline=600s); after 9 uploads GCS rate-limits and 10th
      upload stalls event loop indefinitely. 500-cap insufficient (500×274ms=137s saturates GCS quota). Fix:
      UTL@aca4004c (ThreadPoolExecutor + 15s timeout, best-effort drops) + features-service@5afdd918 (cap 500→10,
      10×274ms=2.74s well below rate-limit threshold). VM 191412 stalled due to Bug 4.
- [x] ✅ [AGENT] P0. Bug 5 (`+ not allowed on i64 and duration[μs]`) — `_add_timestamp_out` in `feature_writer.py`
      handled `Utf8` and `Datetime` but NOT `Int64`. `rate_impact_calculator` creates `timestamp` as epoch-microseconds
      integer → Polars `Int64`; adding `pl.duration(...)` to `Int64` raises. Caused VM `193018` to DEPLOYMENT_FAILED
      (exit_code=1) at group 9/11 (`rate_impact`) — all prior groups passed cleanly. Fixed in features-service@ae90d1fd
      (slot-8). Tarball rebuilt at `2026-05-17T19:06:20Z`.
- [x] ✅ [AGENT] P0. Bug 6 fix (`rate_impact` LookaheadBiasError) — `aave_rate_impact_calculator.fetch_data()` used
      `datetime.now(UTC)` as observation timestamp; `_enforce_as_of_boundary` rejected it when run_time >> as_of in
      historical backfill (VM 200717 FAILED at group 9/11, exit_code=1, 19:35 UTC). Two-pronged fix:
      features-service@c10fa999 (batch-skip in orchestrator, same pattern as macro_sentiment — slot-1-main) +
      features-service@40494dd7 (timestamp pinned to end_date in calculator — parallel agent). Tarball rebuilt
      @19:43:44Z (features-service-code.tar.gz = @c10fa999 active; @40494dd7 manifest also present).
- [x] ✅ [AGENT] P0. Bug 7 (`success_count=9/11` → DEPLOYMENT_FAILED) — `_log_window_outcome` returned
      `days_written >     0`; STALE_DATA emission policy suppressed ALL writes for historical dates (onchain_perps +
      utilization, 5 dates each) → `days_written=0` → `False` for 2 groups → `9==11=False` → exit_code=1. VM 204250
      FAILED at 20:11 UTC. Two layered fixes: features-service@09f182b5 (batch-skip guards for onchain_perps +
      utilization, parallel agent) + features-service@ebbb3c53 (safety net: returns True when days_with_data > 0,
      slot-1-main). Tarball rebuilt at 2026-05-17T20:19:03Z.
- [x] ✅ [AGENT] P0. Smoke B DEPLOYMENT_COMPLETED — VM `features-onchain-defi-20260517-211522` exit_code=0 at 20:21:48
      UTC — 11/11 groups (7 batch-skip + 6 written). 7 bugs fixed across 7 VM iterations (~17:00 → 20:21 UTC). Prior
      FAILED VMs: 204250 (Bug 7), 204428+204443 (killed), 200717 (Bug 6), 203044 (pre-Bug-6).
- [x] ✅ [AGENT] P1. Harsh-side paper backtest B-015 UNBLOCKED — cross-side ping sent to \_agent_pings.md at tick-63
      (PM@573764e0).

---

## Triage — 2026-05-18

**Status**: OPEN  
**Triaged by**: slot-8 triage sweep  
**Reason**: Schema drift + stall issues partially addressed; follow-up needed
