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
last_updated: 2026-08-03
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

- [x] ✅ [DATA] P2. Read `features_service.cross_instrument`'s compute path (the code actually exercised by
      `--operation compute --mode batch --asset-group CEFI --start-date 2026-05-03 --end-date 2026-05-03`) and determine
      whether it shares the unfiltered-wide-manifest-read anti-pattern already fixed in the 4 sibling incidents this
      week. If confirmed, apply the same fix shape (column-pruned/filtered read, `os._exit()` after the real work
      completes to avoid a lingering-thread hang). (repo: features-service) — features-service@2aea0e59. **Confirmed**:
      `BatchHandler._ingest_delta_one` listed `delta_one/by_date/day={D}/` UNSCOPED — that prefix spans ALL
      `feature_group=` dirs (18 for CEFI/DEFI) AND all 7 `DEFAULT_TIMEFRAMES`, even though every cross_instrument
      calculator computes at exactly ONE timeframe (`config.base_timeframe`, default "15s" — no CLI knob requests
      another, confirmed via `base_calculator.py`'s `timeframe` default + the batch handler's total absence of any
      per-timeframe branching downstream of `_input_data`). The unfiltered listing therefore pulled ~7x more
      per-instrument parquet files than the compute ever uses, downloaded+retained ONE AT A TIME in a plain Python loop
      (`_load_parquets_concat`'s `for p in paths: ... frames.append(df)`, one `pl.concat` at the end) — this explains
      BOTH observed symptoms: the 4.5h runtime (thousands of sequential GCS round-trips) and the continuously-climbing
      RSS (an ever-growing `frames` list before the single final concat). Same anti-pattern class as the 4 sibling
      incidents, manifested as an unscoped GCS-prefix listing rather than an unfiltered parquet-column read.
      Deliberately did NOT prune the `feature_group=` axis — `feature_builder_registry.py`'s per-group `sources`
      metadata plus a pre-existing regression test (`test_cross_asset_correlation_collision_safe_join`, whose own
      docstring already documents "`_ingest_delta_one` concatenates every delta_one feature group") both confirm the
      multi-feature_group concat is intentional (multiple indicator families feed the calculators) — narrowing that axis
      without deeper verification would risk a silent correctness regression, out of this todo's evidenced scope. **Fix
      applied** (mirrors the sibling fix shape): (1) `_ingest_delta_one` now takes a `timeframe` param and filters
      listed paths to `/timeframe={base_timeframe}/` before downloading (same cheap listing call; only the expensive
      download+concat step is scoped down) — mirrors the already-correct scoped-prefix pattern in this same module's
      `paired_dispatch.py` sibling. (2) `__main__.py` now catches the `SystemExit` that `ServiceBootstrap.run()` raises
      after all real work (compute+persist+manifest) has completed, and force-terminates via `os._exit()` on the
      resolved exit code — defensive parallel to the sibling `expand_defi_pool_catalogue` fix, since `sys.exit()` alone
      still waits on interpreter teardown (atexit + non-daemon-thread joins), the same hang class. Added
      `TestIngestDeltaOne` (3 cases: timeframe-filters, keeps every feature_group at that timeframe, raises
      `FileNotFoundError` when none match) + fixed 3 pre-existing tests whose `MagicMock` config never set
      `base_timeframe` (would've silently mismatched under the new filter). Also trimmed two pre-existing docstrings in
      `batch_handler.py` (900-line QG file-size cap — file was already at 898/900 before this change).
      `quality-gates.sh` full green (18097 passed, 0 failed; sentinel `2aea0e593872ad0d83409d62a0bb29db35b34cab`);
      quickmerge landed on `live-defi-rollout`, verified present on origin via `merge-base --is-ancestor`.
- [x] ✅ [INFRA] P2. Fix or replace the `timeout 150` protection in all 8
      `e2e-testing/scripts/<family>/smoke_matrix.py`'s `_invoke_cli()` — e2e-testing@404e4d8. **Correction to this
      todo's premise**: `_invoke_cli()` never actually contained a literal shell `timeout 150` wrapper (grepped full git
      history + working tree — 0 hits for a `150` timeout anywhere in this repo); all 8 families already used
      `subprocess.run(cmd, timeout=600, ...)`. The `timeout 150`-wrapped command in this incident's "What's confirmed"
      §1 was a hand-typed manual verification run by slot 12 directly in `.tabs/12/features-service` (not via
      `smoke_matrix.py`). That said, `subprocess.run`'s built-in `timeout=` kwarg DOES already SIGKILL (not bare
      SIGTERM) on expiry — verified live: a SIGTERM-trapping repro child was killed within its exact bound even before
      any change. The REAL residual gap (also verified live): `subprocess.run`'s `kill()` only signals the direct child
      PID — a repro parent that spawns its own grandchild subprocess left that grandchild running indefinitely as an
      orphan after the parent was killed, which is the actual "unbounded memory survives the timeout" failure mode this
      incident's symptom is consistent with. Fix applied: all 8 `_invoke_cli()`s (+ sports' inline equivalent) now use
      `subprocess.Popen(start_new_session=True)` + `communicate(timeout=600)`, and on `TimeoutExpired` SIGKILL the whole
      process GROUP via `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` — reaping the invoked CLI and any descendant
      it spawned. Re-verified the done-when repro with this exact fix: both a SIGTERM-trapping parent AND its
      SIGTERM-trapping grandchild are reaped within the deadline (previously the grandchild survived). QG green
      (`quality-gates.sh`, sentinel 404e4d8). (repo: e2e-testing)
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
- **2026-08-02 (slot 8, infra)**: `[INFRA] P2` shipped — e2e-testing@404e4d8, QG green. Corrected this todo's premise in
  place (the literal `timeout 150` never existed in `_invoke_cli()`; the real gap was `subprocess.run`'s `kill()` only
  reaping the direct child, not descendant processes — see the flipped todo above for the full finding). Flipping the
  `features_smoke_verify_timeout_hardening_landed` prerequisite green now so
  `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`'s parked `[DATA] P3`-adjacent re-verification work can
  unpark.
- **2026-08-03 (slot 12, data_engineering)**: `[DATA] P2` shipped — features-service@2aea0e59, QG green (18097 passed, 0
  failed; full no-skip-flags run). Root-caused `cross_instrument`'s compute path directly: `_ingest_delta_one`'s
  unscoped `delta_one/by_date/day={D}/` listing (spanning all 18 CEFI feature_group dirs x all 7 DEFAULT_TIMEFRAMES,
  though only 1 timeframe is ever consumed) is the same unfiltered-wide-read anti-pattern class as the 4 sibling
  incidents, applied via a client-side timeframe path-filter + a defensive `os._exit()` in `__main__.py` — see the
  flipped todo above for the full finding + fix detail. `[DATA] P3` (resume the remaining unverified smoke_matrix.py
  legs) is now unblocked but explicitly OUT of this todo's scope — left for the dispatcher to hand out as its own task
  per the /boot-per-shippable-unit discipline.
