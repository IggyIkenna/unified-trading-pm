---
doc_type: issue
title: >-
  GCSStorageClient's retry predicate drops connection-level errors (shard-13 SSL-EOF/connection-reset death) + a
  separate checkpoint-resume actuator bug (fixed)
summary: >-
  Split out of `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (that doc is near its 1000-line hard cap
  under heavy concurrent write load from the same fleet incident) to avoid growing it further. Two distinct findings
  from diagnosing `canonical-migration-cefi-content-13-relaunch20260731-032349`'s death (DP-VM-003, `agt-5a8706`,
  2026-07-31): (1) an OPEN root-cause finding — `GCSStorageClient`'s custom `_GCS_RETRY` predicate
  (`unified-trading-library/.../providers/gcp.py:66-75`) only retries HTTP 429/503 and REPLACES the GCS SDK's own
  broader default retry, which also covers `ConnectionError`/`SSLError`/`ProtocolError` — exactly the exception classes
  behind shard 13's death (`SSLEOFError`, `ConnectionResetError`). This is a fleet-wide reliability gap (every
  `GCSStorageClient` caller inherits the narrowed predicate), distinct from the memory-leak and `hard_deadline` scaling
  mechanisms already root-caused and fixed in the parent doc. (2) An ALREADY-FIXED, separate bug found while computing
  shard 13's checkpoint-resume date by hand: `RelaunchStalledVm`/`RelaunchPreemptedVm`
  (`deployment-service/scripts/recovery/{relaunch_stalled_vm,relaunch_backfill_vm}.py`) set their checkpoint override on
  a bare `START_DATE` env key, but 5 launchers (`launch-canonical-migration-vm.sh` among them) resolve their positional
  start-date arg as `"${2:-${RESUME_START_DATE:-}}"` and never read bare `START_DATE` — so the checkpoint-aware resume
  added 2026-07-27 was silently inert for this launcher family the whole time. Fixed (set both env keys) + regression
  tests reproducing this exact scenario, shipped `deployment-service@b34e85a`.
status: open
nature: issue
asset_group: [cefi, meta]
stage: [data, meta]
repos: [unified-trading-library, deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, gcs, retry, reliability, checkpoint-resume, vm-relaunch, data-pipeline]
related:
  [
    cefi_content_migration_fleet_half_incomplete_2026_07_26,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: cefi_master
source:
  "data_pipeline_failure escalation agt-5a8706, slot 4, 2026-07-31 -- DP-VM-003 relaunch of
  canonical-migration-cefi-content-13"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# GCSStorageClient retry predicate gap + a checkpoint-resume actuator bug (fixed)

## What I found

Dispatched via DP-VM-003 (`agt-5a8706`) for `canonical-migration-cefi-content-13-relaunch20260731-032349`, a shard in
the 21-shard `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` fleet. That VM's death didn't match either of
the two mechanisms already root-caused in the parent doc (pyarrow-pool memory leak; `hard_deadline` scaling bug) — its
`run.log` tail instead showed:

```
WARNING upload blocked >90.0s — abandoning attempt, will retry next tick
WARNING upload iteration failed: HTTPSConnectionPool(...): Max retries exceeded ...
  (Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol')))
WARNING heartbeat iteration failed: 404 GET .../deployments/active/d3638fd0-....json: No such object
ERROR migrate failed raw_tick_data/.../BYBIT:PERPETUAL:AXS-USDT@LIN.parquet: ConnectionResetError(104, 'Connection reset by peer')
```

Real progress (steady ~11 files/sec, 43,200→46,400/312,875 files) stopped cleanly at this point — not a hang, a cluster
of connection failures across several independent code paths (the migration's own GCS reads, its log-upload tee, and its
deployment-heartbeat registration) all around the same ~20-minute window.

**Root cause**: read `unified-trading-library/unified_trading_library/cloud_interface/providers/gcp.py:66-75`.
`GCSStorageClient.download_bytes`/`upload_bytes` (the calls this migration script's GCS reads/writes route through) pass
`retry=_GCS_RETRY`, a custom predicate:

```python
_GCS_RETRY = Retry(predicate=if_exception_type(TooManyRequests, ServiceUnavailable), deadline=600.0)
```

This REPLACES the GCS SDK's own `google.cloud.storage.retry.DEFAULT_RETRY`, which additionally retries
`ConnectionError`, `requests.exceptions.{ConnectionError,Timeout,ChunkedEncodingError}`, and
`urllib3.exceptions.{SSLError,ProtocolError,PoolError,TimeoutError}` — confirmed by reading the installed SDK package
directly. Shard 13's `SSLEOFError`/`ConnectionResetError` fall in exactly the classes the custom predicate drops, so
they failed immediately instead of retrying like the SDK default would. `GCSStorageClient.list_blobs()` (gcp.py:315-329)
also has no `timeout=` at all — not implicated in this specific death (it only runs once, before the migrate phase
begins), but a related gap in the same file worth closing at the same time.

This is a THIRD, distinct-from-memory contributor to this fleet's overall death rate — a fleet-wide reliability gap
(every `GCSStorageClient` caller inherits the narrowed predicate), not specific to the cefi content migration script.
Not fixed here: it touches shared retry logic used by every GCS caller across the codebase, a wider blast radius than a
one-shot escalation's remit (per `data_pipeline_failure.md`'s own `does_not: guess at an ambiguous fix`).

**Separately** (orthogonal — found while manually computing shard 13's own checkpoint-resume date, since the in-image
`RelaunchStalledVm` actuator can't actuate from the Cloud Run monitor image per the packaging gap in
`data-pipeline-alerts.md`): `RelaunchStalledVm.relaunch()`/`RelaunchPreemptedVm.relaunch()` both compute a
checkpoint-resumed date and write it to `env["START_DATE"]`. But `launch-canonical-migration-vm.sh` (and
`launch-api-football-backfill-vm.sh`, `launch-features-sports-backfill-vm.sh`, `launch-mdps-build-continuous-vm.sh`,
`launch-mdps-backfill-vm.sh`) resolve their positional start-date arg as `START_DATE="${2:-${RESUME_START_DATE:-}}"` and
never consult a bare `START_DATE` env var — so for these 5 launchers, the checkpoint override had zero effect;
`escalation.py::_recover_stalled_vm` passes the failed VM's own `launch_env` (which already carries the ORIGINAL
`RESUME_START_DATE`) straight through, silently replaying the original start date every time instead of the checkpoint
frontier. Confirmed this would have affected the PREEMPTION path too (`RelaunchPreemptedVm` targets the same 5 launchers
via `VM_NAME_OVERRIDE` self-relaunch, same bug shape). **Fixed**: set both `START_DATE` AND `RESUME_START_DATE` in the
checkpoint-override block of both actuators (harmless no-op for the ~23 launchers that read bare `START_DATE`), added
regression tests reproducing this exact scenario for both actuators, shipped `deployment-service@b34e85a` (QG green,
2988+ tests passing).

## Why it matters

The retry-predicate gap makes every GCS-heavy long-running VM in this fleet (and beyond — any `GCSStorageClient` caller)
more fragile to ordinary transient network blips than the SDK's own defaults would allow, needlessly inflating this
fleet's (and others') death/relaunch rate. The checkpoint-resume bug meant the "resume from where you left off" feature
shipped 2026-07-27 was never actually functional for 5 launcher families — every relaunch of this fleet done via the
automated actuator (once the packaging gap closes) would have silently replayed from the original start date, discarding
real progress, until this fix.

## Recommended decision

- [ ] [BACKEND] P2. Widen `_GCS_RETRY`
      (`unified-trading-library/unified_trading_library/cloud_interface/providers/     gcp.py:66-75`) to also retry
      connection-level transient errors — simplest: adopt `google.cloud.storage.retry.DEFAULT_RETRY` directly, or union
      it with the existing 429/503 predicate if the 429/503-specific `deadline=600.0` needs preserving. Add
      `timeout=600` to `list_blobs()` (gcp.py:315-329) for defense-in-depth. **Done when**: both changes ship + QG
      green; a quick regression test asserting `ConnectionError`/`SSLError` are retried (not just 429/503) would lock
      this in. Repo: unified-trading-library. This looks like a small, bounded, AO-eligible change (a checkable code fix
      with a stated done-when) — filed as `NA`/local per the default plan-destination posture since no operator
      confirmation was available at file-time; flip to `assigned_vm: planning` if a human agrees it's properly scoped.

## Progress Log

- 2026-07-31 (`data_pipeline_failure` escalation `agt-5a8706`, slot 4): filed after splitting out of the parent fleet
  doc to keep it under its line cap. Root-cause investigation for the retry-predicate finding was via a dedicated
  Explore sub-agent (read `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` + its GCS/retry/memory call chain
  in full); the checkpoint-resume actuator bug was found + fixed directly while manually relaunching shard 13.
  Unconfirmed: whether memory pressure also contributed to shard 13's socket failures (the sub-agent flagged this as
  worth checking `host_metrics_window.mem_pct` for, but out of this doc's filing scope) — the retry-predicate gap is
  real and worth fixing regardless of that outcome.
