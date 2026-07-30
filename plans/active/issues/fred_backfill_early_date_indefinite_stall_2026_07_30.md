---
doc_type: issue
title:
  "RETRACTED root cause: FRED backfill 'stall' on its first chunk is NOT a bug — it is the manifest reader's own bounded
  (1h default) wait for a genuinely live TRADFI consolidator lock; 3 VMs were killed prematurely misreading this as a
  hang"
summary: >-
  Originally filed as a suspected indefinite hang in FredAdapter's fetch path (3 VMs killed after 1-7 minutes of
  apparent zero progress on the very first backfill chunk). Live SSH + py-spy inspection of a 4th repro VM (2026-07-30,
  slot 6) shows the CORRECT root cause: the main thread is legitimately parked in
  `unified_trading_library.manifest_writer._read_index._wait_for_in_flight_cycle_then_reread` — a DELIBERATE, bounded
  wait (`consolidator_inflight_horizon_for_bucket`, 3600s default for tradfi since it has no per-asset_group override
  like defi=4200s/sports=2400s) for a currently-HELD, genuinely-fresh TRADFI manifest consolidator lock
  (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/consolidator.lock`, confirmed
  `started_at=2026-07-30T02:41:30Z`, a real live merge cycle, not orphaned). This is the manifest system's own
  documented "legitimate-in-flight-merge" protection working exactly as designed
  (`instruments_sports_manifest_consolidator_lock_livelock_2026_07_15` REOPENED-SCOPE) — NOT a FredAdapter defect, NOT
  date-specific, NOT related to the calendar-exemption fix (`unified-api-contracts@6d87d95e`, separately confirmed
  fixed/verified/unaffected by this). All prior "ruled out" analysis in the original version of this doc (retry logic,
  asyncio.gather concurrency, DNS/ThreadedResolver hypothesis) was diagnostically sound but chasing the wrong layer —
  the actual answer was one level up, in manifest-read pre-flight, not the FRED HTTP client at all.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [fred, tradfi, backfill, manifest-consolidator, false-positive, retraction, operator-education]
related:
  [
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
priority: P3
parent_epic: mtds_mdps_master
source: "macro_micro_econ_data_capture_audit-003, slot 6, escalation-continuation from agt-765e33"
execution_scope: orchestrator-agent
drift_direction: advance-code
assigned_role: data_engineering
assigned_vm: planning
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  "slot 6 retracted the original FredAdapter-hang hypothesis via SSH + py-spy live inspection (root cause: a legitimate
  consolidator-lock wait, not a bug) -- but this doc's status was set to resolved while 3 real follow-up todos remained
  open, a mismatch caught by check_archive_candidates.sh's 2026-07-29 hard-gate upgrade. Corrected back to status:open
  2026-07-30; todo 2 (logger.info visibility line) implemented same-day, unified-trading-library@a0546d68. Todos 1
  (measure real TRADFI cadence, do not guess) and 3 (relaunch the actual FRED backfill VM and let it run past the wait)
  remain genuinely open -- not something to close via a doc-hygiene pass."
---

# FRED backfill "stall" was a live TRADFI consolidator lock, not a bug

## What actually happened (corrected)

`gcloud compute ssh` into a 4th repro VM (`tradfi-bf-fred-full-20260730-023644`, `--start-floor 1970-01-01`) while it
showed the same CPU-flat symptom, then `py-spy dump --pid <mtds-pid>` for a live Python stack trace:

```
Thread 8237 (idle): "MainThread"
    _wait_for_in_flight_cycle_then_reread (unified_trading_library/manifest_writer/_read_index.py:190)
    _read_slow_path (unified_trading_library/manifest_writer/_read_index.py:248)
    _read_availability_index_slim (unified_trading_library/manifest_writer/_read_index.py:769)
    read_availability_index (unified_trading_library/manifest_writer/_read_index.py:362)
    _run_preflight_availability_check (orchestrator/preflight.py:752)
    ...
```

`_wait_for_in_flight_cycle_then_reread`'s own docstring: "Called only after the caller already confirmed
`consolidator_cycle_in_flight` (a fresh held lock — direct proof a real merge is running)... Polls until the lock clears
(the merge completed) or the wait deadline — `consolidator_inflight_horizon_for_bucket(bucket)` from the moment this
wait starts — passes, whichever comes first."

Confirmed the lock is real and fresh, not orphaned:

```
$ gsutil cat gs://market-data-tick-tradfi-prd-central-element-323112/_index/consolidator.lock
{"started_at": "2026-07-30T02:41:30.929879+00:00", "instance": "1-36327a2d"}
```

`consolidator_inflight_horizon_for_bucket("tradfi")` → `tradfi` is NOT in
`AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC = {"defi": 4200, "sports": 2400}`
(`unified_trading_library/manifest_writer/_staleness_budget.py:58`), so it falls through to
`_DEFAULT_CONSOLIDATOR_INFLIGHT_HORIZON_SEC = 3600` (1 hour). My 3 earlier kills (after 1, 3.7, and 7 minutes) were all
well inside this deliberately generous, documented bound — I mistook a correct, safe, by-design wait for a hang.

## Why this happened now, specifically

The TRADFI manifest bucket was under heavy write pressure this exact session: my own 2024 smoke tests +
`--force-recapture` correction + 3 killed full-backfill attempts, layered on whatever else the fleet's other concurrent
TRADFI-touching workers were doing — plausibly enough shard churn to trigger (or coincide with) a genuine consolidator
merge cycle right as I kept relaunching. This is very likely a normal, if unlucky-timed, operational event, not a new
consolidator bug.

## Corrected disposition of the original "ruled out" analysis

Everything in the original version of this doc (asyncio.gather concurrency confirmed, retry/backoff math, DNS
ThreadedResolver hypothesis) remains factually accurate as written — it correctly ruled out the FredAdapter layer. The
gap was scope: none of that analysis considered the manifest-READ pre-flight path itself could be the blocking call,
since `read_availability_index` looked like a fast local/GCS-index operation, not something with its own multi-minute
bounded-wait design. Live process inspection (the one tool this session's earlier attempts lacked) found it in under a
minute once actually applied.

## Why this still merits a (much smaller) followup, not a full close

- **TRADFI has no per-asset_group inflight-horizon tuning** (unlike defi=4200s/sports=2400s, both explicitly sized to
  their measured real consolidation cadence per `_staleness_budget.py`'s own comments). It silently inherits the generic
  3600s default. Worth a bounded follow-up to measure TRADFI's actual real merge cadence and add an explicit
  `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["tradfi"]` entry sized to it (same pattern as the other two), rather than
  relying on the generic default being "close enough."
- **No operator-visible signal distinguishes "waiting on a legitimate lock" from "actually stuck"** in the run.log tee'd
  output — a worker (or operator) watching logs sees the same CPU-flat, log-silent symptom either way, and the ONLY way
  to tell them apart is live process inspection (this session's method) or manually checking the lock blob's
  `started_at` age against the horizon. A single `logger.info` line when entering
  `_wait_for_in_flight_cycle_then_reread` (e.g. "waiting up to Ns for consolidator lock age=Xs to clear") would have
  saved this session ~20 minutes and 3 prematurely-killed SPOT VMs.

## Recommended next steps

- [ ] [DATA] P2. Add `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["tradfi"] = <measured-cadence>` to
      `unified_trading_library/manifest_writer/_staleness_budget.py`, sized the same way `defi`/`sports` were (measure
      TRADFI's real consolidation cadence from Cloud Logging/consolidator run history first, then set the horizon with
      margin — do NOT guess a number). Repo: unified-trading-library.
- [x] [BACKEND] P3. Add a `logger.info` (or `.warning`, given it can legitimately run for minutes) immediately on entry
      to `_wait_for_in_flight_cycle_then_reread` stating the lock age and horizon, so this state is visible in
      `run.log`/Cloud Logging without needing SSH+py-spy to distinguish "legitimate wait" from "actually stuck." Repo:
      unified-trading-library. — unified-trading-library@a0546d68: added a `logger.warning` on entry citing
      `bucket`/`lock_age_sec` (via the existing read-only `read_consolidator_lock_age_sec`)/`horizon_sec`, explicitly
      stating this is a legitimate by-design wait. `quality-gates.sh` green.
- [ ] [DATA] P1. Resume `macro_micro_econ_data_capture_audit-003`: relaunch the full `1962-01-02..today` FRED production
      backfill and this time let it run past this wait (up to the 1h horizon if needed, or until the consolidator lock
      clears, whichever comes first) rather than killing it prematurely. Verify real captured rows once it progresses
      past chunk 1, then flip that todo's checkbox with the VM name + evidence. See that plan doc for full context.

## Evidence log

- `gcloud compute ssh tradfi-bf-fred-full-20260730-023644 --tunnel-through-iap` + `py-spy dump --pid 8237` (installed
  via `pip install py-spy` in the VM's own venv), 2026-07-30T02:44Z — full stack trace captured above.
- `gsutil cat gs://market-data-tick-tradfi-prd-central-element-323112/_index/consolidator.lock` + `gsutil stat` on the
  same blob — confirms a genuinely fresh (`started_at` matching the GCS object's own creation time), non-orphaned lock.
- Code read: `unified_trading_library/manifest_writer/_read_index.py` (`_wait_for_in_flight_cycle_then_reread`,
  `_read_slow_path`'s full docstring explaining the "Legitimate-in-flight-merge case"),
  `unified_trading_library/manifest_consolidator.py` (`consolidator_cycle_in_flight`, `read_consolidator_lock_age_sec`),
  `unified_trading_library/manifest_writer/_staleness_budget.py` (`AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC`,
  `_DEFAULT_CONSOLIDATOR_INFLIGHT_HORIZON_SEC=3600`).
- `ss -tnp` on the stuck process (PID 8237) showed 8 established connections, all to Google IP ranges (GCS/telemetry),
  zero connections to FRED's API host — consistent with the process never having reached the FRED fetch step at all,
  corroborating the manifest-read-preflight-blocking explanation over any FRED-network-layer hypothesis.

## Progress Log

- **2026-07-30 (slot 6)**: original doc filed after 3 premature VM kills based on GCS-log-only observation (no SSH
  access attempted). Same session, same slot: tested SSH access (worked), relaunched a 4th repro VM, got a live `py-spy`
  stack trace within ~5 minutes of the VM starting, found and confirmed the true root cause (a live, legitimate
  consolidator lock), and rewrote this doc completely rather than leaving the original wrong diagnosis live. Downgraded
  from P1/open to P3/resolved (the remaining scope is a small observability + tuning improvement, not a live-blocking
  bug) and reassigned the actual next action back to `macro_micro_econ_data_capture_audit-003` itself (just let the
  backfill run without prematurely killing it).
