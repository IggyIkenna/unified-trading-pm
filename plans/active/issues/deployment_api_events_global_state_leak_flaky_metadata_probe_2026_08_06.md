---
doc_type: issue
title: >-
  deployment-api promote PR #501 test failure — test_rollup_endpoint_runs_worker_in_service hits a real GCE metadata
  probe despite mocking GcsEventSink, likely a unified_trading_library.events module-level global-state leak across
  pytest-xdist workers
summary: >-
  Found while checking deployment-api PR #501 (blocked on `sit-gate/fleet-green`) for other blockers. `QG slice (tests)`
  newly failed: `tests/unit/test_data_status_beta_rollup_and_cli_config.py::test_rollup_endpoint_runs_worker_in_service`
  raised `pytest_socket.SocketConnectBlockedError` connecting to `169.254.169.254` (GCE metadata IP). The test already
  has an existing, documented mitigation for exactly this class (mocks `GcsEventSink` via `monkeypatch.setattr(_rollup,
  "GcsEventSink", MagicMock())`, added because `GcsEventSink` init used to probe the metadata endpoint during cloud-SDK
  boot) — but the full CI traceback shows the call still reaching a REAL `google.cloud.storage.Client()` construction,
  via a DIFFERENT path: `_rollup.run_data_status_rollup` -> `run_lifecycle(...)` (NOT mocked) -> `log_event(...)` ->
  `_writer.write_event(...)` -> `get_storage_client(provider="gcp", ...)` -> real GCE credential auto-detection.
  `_writer` is a MODULE-LEVEL global in `unified_trading_library/events/__init__.py`, set by `setup_events(sink=...)` —
  which `_rollup.py` DOES call with the mocked sink, wrapped in `with contextlib.suppress(RuntimeError):`. Two most
  likely causes, NOT distinguished without interactive debugging: (a) a prior test in the same pytest-xdist worker
  (`[gw2]`) already called `setup_events(sink=<a real GcsEventSink>)` and this test's own `setup_events()` call never
  actually overwrote it (the module global leaks across tests in the same worker process, unless something inside
  `suppress(RuntimeError)` silently swallowed an exception before `setup_events` ran); or (b) `unified_trading_library`
  genuinely has TWO parallel, disconnected events implementations (`unified_trading_library/events/__init__.py` AND
  `unified_trading_library/events_interface/__init__.py`, each with their OWN `_writer`/`_mode`/`_service_name` globals)
  and some path in this call chain crosses between them — checked `run_lifecycle`'s own `log_event` import
  (`unified_trading_library/events/run_lifecycle.py:134`) and confirmed it imports from the SAME `events` module as
  `setup_events`, so (b) does NOT explain this specific chain, but the duplicate-globals architecture itself is a real
  latent footgun worth flagging regardless. **live-defi-rollout's own quality-gates-v2 is GREEN right now** (latest run
  2026-08-06T10:55:03Z, success) — this reads as ORDER-DEPENDENT FLAKINESS (module-global leak across test order/xdist
  worker assignment), not a deterministic content bug. Did NOT attempt a fix to shared `unified_trading_library` code
  without being able to interactively verify the actual root cause — a wrong fix there risks breaking every other
  consumer. Re-triggered `quality-gates-v2` on the promote PR head (`promote/deployment-api/37d6f143bf78`) instead;
  check whether the retry passes before deciding this needs a real fix vs. was a one-off flake.
status: open
resolved_by: deployment-api@fa17399671
nature: issue
asset_group:
  [ci] # corrected 2026-08-16 (meta_plan_corpus_hygiene_ao_dispatch_batch1 todo 3) -- was [cross-cutting]. Content is a
  # CI-pipeline test-flakiness finding: a pytest-xdist module-global leak causing a real GCE metadata probe in
  # deployment-api's QG test slice, discovered while triaging a promote PR blocked on sit-gate/fleet-green -- CI-run
  # mechanics, not a data-pipeline cross-AG concern. `tags:` already includes `ci`; audit recommended `ci`.
stage: [meta]
repos: [deployment-api, unified-trading-library]
scope: [engineer, admin]
tags: [ci, flaky-test, pytest-socket, gce-metadata, events, global-state, unified-trading-library]
related: [/plans/active/ci_consolidated_closeout_2026_07_25.md]
created: 2026-08-06
author: interactive session (operator-triggered CI audit)
last_updated: 2026-08-06
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: ["operator CI audit, 2026-08-06 — deployment-api PR #501, run 31087761957, job 92571271263"]
context_scope:
  [
    unified-trading-library/unified_trading_library/events/__init__.py,
    unified-trading-library/unified_trading_library/events_interface/__init__.py,
    deployment-api/tests/conftest.py,
    unified-trading-library/unified_trading_library/events/run_lifecycle.py,
  ]
---

# deployment-api test flake: real GCE metadata probe despite a GcsEventSink mock

## What I found (full detail — see summary above for the condensed version)

Traceback (from CI, `[gw2]` xdist worker):

```
tests/unit/test_data_status_beta_rollup_and_cli_config.py:230: in test_rollup_endpoint_runs_worker_in_service
    out = asyncio.run(_rollup.run_data_status_rollup(services=None))
deployment_api/routes/data_status/_rollup.py:89: in run_data_status_rollup
    with run_lifecycle(...):
unified_trading_library/events/run_lifecycle.py:141: in run_lifecycle
    log_event(...)
unified_trading_library/events/__init__.py:427: in log_event
    _writer.write_event(event_name, metadata)
unified_trading_library/event_sink.py:148: in write_event
    client = get_storage_client(provider="gcp", project_id=self._project_id)
...
google/auth/compute_engine/_metadata.py:135: in is_on_gce
    [network probe to 169.254.169.254 -> pytest_socket.SocketConnectBlockedError]
```

The test mocks `_rollup.GcsEventSink` (a `MagicMock`), which `_rollup.py` uses to build `_sink`, then passes to
`setup_events(service_name=..., mode="batch", sink=_sink)` — both calls wrapped in
`with contextlib.suppress(RuntimeError):`. `run_lifecycle`'s internal `log_event` call reads
`unified_trading_library .events`' own module-level `_writer` global — confirmed via `run_lifecycle.py:134`'s own import
(`from unified_trading_library.events import log_event`) that this IS the same module `setup_events` writes to, so this
is not a cross-module split for this specific chain. Yet `_writer` at call time is demonstrably a REAL sink (the
traceback proceeds into real `write_event`/`get_storage_client` code, which a `MagicMock.write_event(...)` call would
never do).

**Not yet distinguished** (needs interactive debugging, not static reading):

1. A stale `_writer` from an EARLIER test in the same pytest-xdist worker process (module globals persist across tests
   within one worker unless explicitly reset) — this test's own `setup_events(sink=<mock>)` call may simply not be
   running before `run_lifecycle` fires, or may be running but not actually overwriting an already-set global for a
   reason not visible from the traceback alone.
2. Something inside the `contextlib.suppress(RuntimeError)` block raising and being silently swallowed BEFORE
   `setup_events` executes, leaving whatever `_writer` state existed before this test ran.

**Separately worth flagging regardless of which of the above is the actual cause**: `unified_trading_library` has TWO
independent event-system implementations with their own separate `_writer`/`_mode`/`_service_name` module globals —
`unified_trading_library/events/__init__.py` and `unified_trading_library/events_interface/__init__.py`. Confirmed NOT
the cause of this specific chain, but a duplicate-globals architecture like this is a latent footgun for the next person
who imports from the "wrong" one.

## Why I didn't fix it blind

`unified_trading_library` is a shared dependency across every T4 service in the fleet. A wrong fix to its global
event-writer state (e.g., adding a reset-between-tests fixture, or changing how `setup_events`/`run_lifecycle` interact)
risks breaking other consumers in ways I can't verify without running the actual test suite interactively (pytest with
`-p no:xdist`, or `pdb`, to inspect `_writer`'s actual identity at the failure point). Out of scope for a static-reading
diagnosis.

## What I did instead

`live-defi-rollout`'s own `quality-gates-v2` is GREEN right now (2026-08-06T10:55:03Z) — the exact same test suite,
presumably a different xdist worker/test-ordering draw, passed clean. This reads as order-dependent flakiness, not a
deterministic break. Re-triggered `quality-gates-v2` on the promote PR head directly:
`gh workflow run quality-gates-v2.yml --repo IggyIkenna/deployment-api --ref promote/deployment-api/37d6f143bf78`.

## Update 2026-08-06 (later same session) — confirmed reproducible, real fix shipped

The re-triggered `quality-gates-v2` run FAILED again with the identical traceback (3rd consecutive failure: 08:56:36,
09:07:32, 10:57:58, all `failure`) — this is NOT a one-off flake, it's a real, reproducible-on-CI bug.

**Interactive debugging, done properly this time** (not static reading):

- Ran the target test ALONE (`pytest -p no:xdist ... -k test_rollup_endpoint_runs_worker_in_service`): **PASSED**, with
  an instrumented print confirming `_writer` IS the mock at the point `run_lifecycle` is called.
- Ran the FULL `tests/unit/` suite locally (`-n 4 --block-network`, matching CI's network-blocking, 5222 tests, ~21
  min): the target test **PASSED** and no `DEBUG _writer=` leak was ever observed — the ONLY failure in that run was a
  different, unrelated test
  (`test_route_deployments_inventory.py::test_inventory_route_date_range_filters_terminal_vm_rows`).
- **Conclusion**: this genuinely does not reproduce with a 4-worker local run under network blocking — it is specific to
  CI's exact worker count / OS / test-collection-order combination, which I cannot replicate locally. The root cause
  (which OTHER test leaves a real sink as `_writer` before this one runs, and why `_ensure_events_initialized`'s autouse
  per-test reset in `tests/conftest.py` doesn't prevent it) stays formally UNDETERMINED.

**Given I could not safely pin the exact root cause without CI-parity conditions, did NOT touch shared
`unified_trading_library` code.** Instead fixed the test itself to not depend on the library's event-writer global state
at all: it was already mocking `GcsEventSink`; now also mocks `_rollup.run_lifecycle` directly
(`monkeypatch.setattr(_rollup, "run_lifecycle", MagicMock())`). The test's actual assertions (`run_rollup` called with
the right args, `_PROCESS_POOL_DISABLED` restored) never depended on `run_lifecycle`'s real behavior — this fully
sidesteps the entire problematic call chain (`run_lifecycle` -> `log_event` -> `_writer.write_event` -> real
`google.cloud.storage.Client()`) with zero risk to any other consumer of `unified_trading_library`, since nothing
outside this one test file changed. Verified locally: still passes (now 0.68s vs 2.28s before, since it no longer
executes the real lifecycle context manager at all).

## Todos

- [x] ✅ [BACKEND] P2. Confirmed reproducible (3 consecutive CI failures), root cause NOT fully pinned (CI-parity-only
      repro), but fixed for real by removing the test's dependency on `run_lifecycle`'s shared library internals
      entirely — see Update above. Shipped: `deployment-api@fa17399671`. Full local `quality-gates.sh` green (all 6
      stages) before shipping.
- [ ] [BACKEND] P3. Still open, unrelated to the shipped fix: `unified_trading_library` having two independent,
      same-named global-state stores (`events/__init__.py` vs `events_interface/__init__.py`) for what looks like the
      same concept is worth a deliberate look — either they're genuinely serving different purposes (document why, and
      why both need their own `_writer`), or one is dead/legacy and should be removed. Also worth a follow-up: WHY does
      `_ensure_events_initialized`'s autouse per-test reset (`tests/conftest.py`) not prevent this class of leak on CI
      specifically? The formally-undetermined root cause above may recur in a DIFFERENT test that doesn't have the
      luxury of mocking `run_lifecycle` away.

## Progress Log

- **2026-08-06 (cicd escalation agt-ca03f6, slot 9)**: Re-opened from `status: resolved` → `status: open` for
  `check_terminal_status_archived` compliance. The primary fix (shipping `deployment-api@fa17399671`) is complete and
  stays recorded in `resolved_by`, but the doc carries an open `- [ ]` P3 follow-up (the dual `unified_trading_library`
  event-global-state footgun). A terminal `resolved` status on a doc with open work is a false-completion state per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`; archiving it would silently drop the follow-up
  from active tracking. Kept in `plans/active/issues/` until the P3 todo lands or is moved to its own tracked issue.
- **context-scout 2026-08-07**: populated context_scope (4 entries) — no prior marker despite an existing list (never
  scouted by this skill before). Re-derived for the remaining open `[BACKEND] P3` scope only (the shipped fix already
  removed `_rollup.py`/the test file's dependency on this chain): dropped both deployment-api call-site files, added
  `deployment-api/tests/conftest.py` (the `_ensure_events_initialized` autouse fixture the P3 todo names directly).
  Confirmed `/codex/02-data/live-data-persistence-and-event-log.md` does NOT cover this `unified_trading_library/events`
  lifecycle-logging module (that codex doc is the market-data `EventTransport`/`streaming.event_facade` system — a
  same-sounding but different module) — not added, would have been a false citation.
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — the sole open `[BACKEND] P3` todo
  (investigate + reconcile the two independent `unified_trading_library` event-global-state stores, and why the
  `conftest.py` autouse reset didn't prevent the CI-only leak) is genuine investigation/design work on a fleet-wide
  shared dependency, not a mechanical fix.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
