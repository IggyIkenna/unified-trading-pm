---
doc_type: issue
title: >-
  Second same-day agent-orchestrator outage — features_service.cross_instrument's smoke-verify run grew to 38.8GB RSS
  over 4.5h, ignored its own `timeout 150` wrapper entirely; killed via SIGTERM-then-SIGKILL, AO recovered
summary: >-
  Slot 12, verifying the smoke_matrix.py PROTOCOL_DATA_SINK_BUCKET fix
  (features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md), ran `features_service.cross_instrument --operation
  compute --mode batch --asset-group CEFI --start-date 2026-05-03 --end-date 2026-05-03` (PID 892676) wrapped in its
  harness's `timeout 150 ... | tail -40`. The process grew to 38.8GB RSS (60% of host RAM), ran 4.5 hours — over 100x
  its stated 150s bound, with `timeout` doing nothing to stop it — and pinned host memory (639MB free, swap 27G/47G
  used) and the orchestrator.service cgroup (MemoryAvailable: 0B, swap 15.9/16G maxed), producing the same
  `sqlite3.OperationalError: database is locked` on `BEGIN IMMEDIATE` signature as this morning's outage
  (orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md) and the DB-lock-storm class
  before it. Operator SIGTERM'd PID 892676; it ignored the signal for 12+ seconds while still in a schedulable `Rl`
  (running) state, not blocked I/O — escalated to SIGKILL, which worked immediately. Host memory recovered fully
  (55Gi->19Gi used, cgroup 0B->38GB available) within seconds, but the API stayed degraded (one 22.3s response, CPU
  pegged 106% sustained) for roughly another 3-4 minutes before response times returned to normal (sub-20ms) — a
  processing backlog draining, not a second wedge. Total outage window (last confirmed DB-lock error to first fast
  response): ~07:00Z-07:40Z, at least 40 minutes.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, features-service, e2e-testing]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    incident,
    memory-leak,
    manifest-read,
    outage,
    shared-host,
    timeout-not-enforced,
    features-service,
    smoke-test,
    cross-cutting-pattern,
  ]
related:
  [
    /plans/active/issues/features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md,
    /plans/active/issues/expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md,
    /plans/archive/issues/orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md,
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
  ]
created: 2026-08-01
last_updated: 2026-08-01
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: >-
  Discovered live on the orchestrator VM (ip-172-31-5-118) via an interactive Claude Code session with direct host
  access, in response to a second same-day operator report ("AO is down again").
resolved_by:
locked_by:
locked_since:
---

# features_service.cross_instrument smoke-verify run — unbounded memory, `timeout` ignored, second AO outage today

## What's confirmed

1. **Trigger**: slot 12, mid-way through verifying its own fix for
   `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md` (all 8 `smoke_matrix.py` harnesses were silently
   writing to PROD buckets under `IS_TEST_RUN=true`), ran a real (non-dry-run) verification leg for the
   `cross_instrument` family:
   `IS_TEST_RUN=true GCP_PROJECT_ID=central-element-323112 PROTOCOL_DATA_SINK_BACKEND=gcp PROTOCOL_DATA_SINK_BUCKET_CEFI=features-cefi-test-central-element-323112 PROTOCOL_DATA_SINK_BUCKET=features-cefi-test-central-element-323112 timeout 150 .venv/bin/python -m features_service.cross_instrument --operation compute --mode batch --asset-group CEFI --start-date 2026-05-03 --end-date 2026-05-03`
   in `.tabs/12/features-service` (PID 892674 = `timeout` wrapper, PID 892676 = the actual python process).
2. **Grew to 38.8GB RSS (60% of a 61GB host) over 4.5 hours**, confirmed still slowly climbing at check time (38849520
   -> 38849628 bytes over 5s). Ran **over 100x past its own `timeout 150` bound** — `timeout` sends `SIGTERM` at the
   deadline by default and gives up if the child doesn't exit (no `--kill-after` was passed), so the wrapper provided
   zero actual protection here.
3. **Same downstream failure signature as prior incidents**: host memory pinned (`free -h`: 639MB free, 6.3GB available,
   swap 27G/47G used), `orchestrator.service` cgroup at its ceiling (`MemoryAvailable: 0B`, swap 15.9G/16G), and a live
   `sqlite3.OperationalError: database is locked` on `BEGIN IMMEDIATE` in the journal (last observed `Aug 01 07:36:39`)
   — the identical write-lock-under-memory-pressure class as `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`
   and this morning's `orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md`. `/api/mode`
   returned `HTTP:000` at repeated 10-20s timeouts.
4. **The process ignored `SIGTERM` too, not just its parent's `timeout`.** Operator sent `SIGTERM` directly to PID
   892676; `ps` showed it still alive and RSS still growing 12+ seconds later, in state `Rl` (running/schedulable, NOT
   blocked on I/O — ruling out an uninterruptible-syscall explanation). Escalated to `SIGKILL`, which reaped it
   immediately (`<defunct>` within 2s).
5. **Recovery had two phases.** Memory recovered instantly and fully after the `SIGKILL` (host used 55Gi->19Gi,
   available 6.3Gi->42Gi; orchestrator cgroup 0B->38GB available) — but the API stayed degraded for another ~3-4
   minutes: one request took 22.3s (vs. normal sub-20ms), and the orchestrator process showed sustained 106% CPU during
   that window (journal showed real background work draining — `autospawn`/`plan_health` retry-loop lines and a
   `Plan regen complete: scanned=658...` — not a second wedge, but a genuine backlog of delayed work catching up). Three
   consecutive follow-up requests then returned in 2ms/5.5ms/18ms, confirming full recovery.
6. **Not yet root-caused at the code level** (unlike the sibling `expand_defi_pool_catalogue_from_manifest` incident,
   which WAS read directly and fixed) — this doc records the operational incident + kill only. Whether
   `features_service.cross_instrument`'s compute path shares the "unfiltered wide manifest read" anti-pattern already
   confirmed today in 4 other call sites (delta_one's `LookbackValidator`, UTL's `get_captured_instruments`,
   instruments-service's `expand_defi_pool_catalogue_from_manifest`, MTDS's `gas_fees` migration — see
   `expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md`'s cross-cutting note) is unconfirmed; the symptom
   (large RSS reading a manifest-backed compute over a bounded 1-day window) is consistent with it but nobody has read
   `cross_instrument`'s actual read path yet.

## Why it matters

- **Second full/severe AO outage in one calendar day** (this doc +
  `orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md` this morning), both the
  identical downstream mechanism (host memory exhaustion -> cgroup ceiling -> SQLite write-lock wedge) from a DIFFERENT
  triggering script each time. The mechanism-level fixes shipped this morning (unit-file self-heal, `/tmp` headroom) are
  unrelated to this trigger class and don't prevent a repeat — every fix so far has been reactive (kill the specific
  offending PID after the fact), not preventive.
- **`timeout <n>` is not a safety net for this failure class, and every smoke/verification script that relies on it
  alone should be treated as unprotected.** This is a new, distinct finding vs. the prior incidents (which didn't
  involve a `timeout` wrapper failing) — worth flagging broadly since `_invoke_cli()`'s `timeout 150` pattern is shared
  verbatim across all 8 `smoke_matrix.py` files per `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`,
  meaning the other unverified legs (multi_timeframe, onchain, sports, volatility) carry the same false sense of
  boundedness if any of them hit the same anti-pattern.
- **Fifth-ish same-day/same-week occurrence of a memory-runaway subprocess threatening this shared host** — reinforces
  the cross-cutting todo already open in `expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md` (a shared
  safe-by-default manifest-read helper) is worth prioritizing rather than continuing to patch one script at a time.

## Todos

- [ ] [DATA] P2. Read `features_service.cross_instrument`'s compute path (the code actually exercised by
      `--operation compute --mode batch --asset-group CEFI --start-date 2026-05-03 --end-date 2026-05-03`) and determine
      whether it shares the unfiltered-wide-manifest-read anti-pattern already fixed in the 4 sibling incidents this
      week. If confirmed, apply the same fix shape (column-pruned/filtered read, `os._exit()` after the real work
      completes to avoid a lingering-thread hang). (repo: features-service)
- [ ] [INFRA] P2. Fix or replace the `timeout 150` protection in all 8 `e2e-testing/scripts/<family>/smoke_matrix.py`'s
      `_invoke_cli()` — either add `timeout --kill-after=<n> 150 ...` (forces `SIGKILL` if `SIGTERM` is ignored, closing
      the exact gap this incident exposed) or wrap with a real memory cap (`ulimit -v`, or
      `scripts/dev/run-bounded-analysis.sh`) since a process that ignores `SIGTERM` for over 100x its wall-clock budget
      cannot be trusted to respect a bare `timeout`. Done when: a repro (a script that traps/ignores SIGTERM) is killed
      within a few seconds of the deadline, not left running indefinitely. (repo: e2e-testing)
- [ ] [DATA] P3. Once `[DATA] P2` above lands (or rules out the anti-pattern), resume the remaining unverified
      `smoke_matrix.py` legs (multi_timeframe, onchain, sports, volatility) for
      `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`'s original verification goal, this time with the
      fixed/hardened timeout wrapper from the todo above. (repo: features-service, e2e-testing)

## Codex SSOTs

- None directly own subprocess-timeout hardening or the cross-cutting manifest-read-safety gap; if the `[INFRA] P2` fix
  lands, consider whether `/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-compute-on-shared-host should gain a
  short note that `timeout <n>` alone is not a sufficient memory/hang guard for ad-hoc scripts on this VM.

## Progress Log

- **2026-08-01 (interactive operator session)**: live-diagnosed + killed (SIGTERM ignored, SIGKILL succeeded), AO
  confirmed fully recovered (response times back to sub-20ms after a ~3-4min backlog-drain window). Notified slot 12
  live (`POST /api/slots/12/message`) before it resumed its remaining verification legs. Did not root-cause
  `cross_instrument`'s own read path this session (out of scope for a live-incident response) — filed as `[DATA] P2`
  above.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): RECLASSIFY
  `NA -> planning`. Fresh (same-day) doc, `assigned_vm: NA` was the unassessed default, not a deliberate call — no
  operator ruling, `depends_on` gate, or "do not dispatch" banner anywhere in the doc. All 3 todos are
  bounded/deterministic (checkable- fact confirmation + a concrete kill-within-seconds repro criterion),
  `assigned_role: data_engineering` already correctly set. Phase 2 conflict-check:
  `plans/active/issues/features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md` (active `assigned_vm: planning`)
  explicitly parks its own P2 re-verification todo on THIS doc's `[INFRA] P2` fix landing ("Do NOT flip this checkbox or
  unpark before then") — not a duplicate claim, but a genuine blocking prerequisite for already-dispatched AO work,
  which argues FOR reclassifying promptly rather than against it. No competing claim found on the
  `[DATA] P2`/`[INFRA] P2`/`[DATA] P3` todos themselves.
