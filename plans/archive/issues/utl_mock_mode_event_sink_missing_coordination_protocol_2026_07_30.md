---
doc_type: issue
title:
  UTL mock-mode event sink lacks the coordination-event protocol — crashes any service's cleanup() in live+mock mode
summary:
  unified-trading-library's `service_framework/_sink_factory.py::build_event_sink()` returns a plain `LocalFsEventSink`
  (write_event-only) for ANY `CLOUD_MOCK_MODE=true` run regardless of batch/live mode, but
  `publish_coordination_event()` only guards against the batch-mode `ValueError` — a live-mode + mock-mode service that
  calls it during cleanup gets an uncaught `AttributeError` and crashes on shutdown instead of exiting cleanly. Found +
  locally worked around in instruments-service (see the plan below); the shared library still needs the real fix.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer]
tags: [event-sink, mock-mode, live-mode, coordination-event, cleanup, shutdown, data-correctness]
related:
  [
    /plans/archive/2026_08/instruments_service_e2e_live_mock_observability_2026_07_27.md,
    /unified-trading-library/unified_trading_library/service_framework/_sink_factory.py,
    /unified-trading-library/unified_trading_library/event_sink.py,
    /unified-trading-library/unified_trading_library/events/__init__.py,
    /unified-trading-library/unified_trading_library/events/sink.py,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: agent_operating_framework_master
assigned_vm: planning
priority: P2
locked_by:
resolved_by: "unified-trading-library@d62a9c64 — plans-corpus-reduction-marathon wave 4"
source: >-
  Found while verifying instruments_service_e2e_live_mock_observability_2026_07_27.md Phase 5 (live-mode clock alignment
  / Ctrl-C clean-exit check) — reproduced live via `main_service_cli()` with `--mode live` under `CLOUD_MOCK_MODE=true`,
  then SIGTERM mid-run.
execution_scope: orchestrator-agent
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
---

# UTL mock-mode event sink lacks the coordination-event protocol

> **ARCHIVED (2026-07-30) — complete.** `LocalFsEventSink` now implements the coordination-event protocol as no-ops
> (`unified-trading-library@d62a9c64`); confirmed `events/` (package) is the live SSOT over `events_interface/` (legacy,
> zero live consumers).

## What I found

`unified_trading_library/service_framework/_sink_factory.py::build_event_sink()`:

```python
if runtime.is_mock:
    mock_path = Path(".local-dev-cache") / "events" / f"{service_name}.jsonl"
    return LocalFsEventSink(path=mock_path, service_name=service_name)
```

This branch fires for `CLOUD_MOCK_MODE=true` **regardless of `runtime.mode` (batch vs live)**. `LocalFsEventSink`
(`unified_trading_library/event_sink.py`) implements only `write_event()` — it does NOT implement
`publish_coordination_event()`/`subscribe_coordination_events()` (the `LiveEventSink` protocol extension defined in
`unified_trading_library/events/__init__.py:356-365`).

`unified_trading_library/events/__init__.py::publish_coordination_event()` guards:

```python
if _mode != "live":
    raise ValueError(f"Coordination events only supported in live mode (current mode: {_mode})")
cast(LiveEventSink, _writer).publish_coordination_event(event)
```

So the guard correctly raises `ValueError` in BATCH mode (callers suppress it), but in **LIVE mode**, `_mode == "live"`
passes the guard and the code proceeds straight to `_writer.publish_coordination_event(event)` — which is an
`AttributeError` when `_writer` is a `LocalFsEventSink` (the mock-mode sink). Any caller pattern like
instruments-service's `cleanup()` (`instruments_service/cli/instruments_handler.py:399,419` —
`contextlib.suppress(RuntimeError, ValueError)` around `publish_coordination_event(...)`) only anticipated the
batch-mode `ValueError`, not this live+mock-mode `AttributeError`, so the exception propagates uncaught.

**Reproduced live (2026-07-30)**:
`CLOUD_MOCK_MODE=true python -m instruments_service ... --mode live --asset-group cefi`, SIGTERM mid-run →
`WARNING Received SIGTERM - initiating graceful shutdown` (signal handling itself is fine) →
`ERROR Service failed: 'LocalFsEventSink' object has no attribute 'publish_coordination_event'` → `SystemExit code=1`.

A ready-made fix already exists in the same library and is unused for this path:
`unified_trading_library/events/sink.py::MockEventSink` implements both `publish_coordination_event()` (appends to an
in-memory list) and `subscribe_coordination_events()` (no-op) — but nothing wires it into `build_event_sink()`.

**Not fixed here**: `unified-trading-library` carries (at least) three parallel event-related modules — `event_sink.py`
(top-level, what `_sink_factory.py` actually imports), `events/` (package, what `instruments_handler.py` imports
`publish_coordination_event`/`setup_events` from), and `events_interface/` (a third, apparently newer package with its
own `MockEventSink`/`CoordinationEvent`). This pattern looks like an in-progress migration between modules — touching
the class hierarchy or import graph without understanding which module is the live SSOT risks breaking other consumers.
This issue is scoped to flag the gap with full evidence, not to guess at the migration's target shape.

## Why it matters

Every service using the shared `ServiceBootstrap`/`_sink_factory.py`/`publish_coordination_event()` pattern (the
standard STEP 5.61-5.62 wiring per `/codex/06-coding-standards/config-reloader-pattern.md`) that (a) runs `--mode live`
AND (b) runs under `CLOUD_MOCK_MODE=true` (local dev, CI smoke tests, any E2E/mock-scenario check) is exposed to this
exact crash on any interrupt/shutdown during cleanup — not just instruments-service. instruments-service worked around
it locally (broadened its own `contextlib.suppress` tuple to include `AttributeError`, instruments-service@`<pending>`),
but that's a local patch on the symptom, not the shared-library root cause; every other service's cleanup() still
crashes the same way until the sink factory itself is fixed.

## Recommended decision

Two options, either closes the gap; a worker can pick the less invasive one without operator input (this is a
same-blast-radius bugfix, not a design decision):

- (a) In `_sink_factory.py::build_event_sink()`, when `runtime.is_mock` AND `runtime.mode == "live"`, construct a
  mock-mode sink that DOES implement the coordination-event protocol (either give `LocalFsEventSink` no-op
  `publish_coordination_event`/`subscribe_coordination_events` methods — matching `MockEventSink`'s own no-op pattern,
  since a local mock has no real downstream consumer to coordinate with anyway — or swap in a purpose-built
  `LocalFsCoordinationEventSink` that logs+no-ops, preserving `LocalFsEventSink`'s "writes to a local jsonl" behavior
  for regular events).
- (b) Confirm which of `event_sink.py` / `events/sink.py` / `events_interface/sink.py` is the intended long-term SSOT
  (grep recent commits/PRs touching these three files for a migration plan) before choosing where the fix lands, to
  avoid fixing the module that's about to be retired.

## Todos

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 — `unified-trading-library@d62a9c64`.** Added no-op
      `publish_coordination_event`/`subscribe_coordination_events` methods to `LocalFsEventSink` in
      `unified_trading_library/event_sink.py` (mirrors `events/sink.py::MockEventSink`'s no-op pattern — a local mock
      sink has no real downstream consumer to coordinate with). `CoordinationEvent` imported under `TYPE_CHECKING` from
      `unified_trading_library.events` (not the deep `.events.schemas` path — the workspace import-pattern check
      requires the package-level import; verified 0 violations). Regression test added:
      `test_mock_mode_live_run_coordination_event_does_not_raise` in `tests/unit/test_sink_factory.py` — builds a mock
      sink via `build_event_sink()`, calls `setup_events(mode="live", ...)` then `publish_coordination_event(...)`,
      asserts no `AttributeError`. Full `quality-gates.sh` green (285s).
- [x] ✅ [SCRIPT] P3. **DONE 2026-07-30 — confirmed `unified_trading_library/events/` (package) is the live SSOT, no
      further migration action needed.** `events/__init__.py`'s own docstring states outright: "Merged from the legacy
      unified-events-interface package; consumers should import from here exclusively." Confirmed via usage census:
      `events/` is imported by 25+ live modules across the library (manifest writer, config reloaders, instruments
      preflight, streaming, core observability, etc.); `events_interface/` has zero consumers outside its own package +
      its own test suite (`rg -l "events_interface"` → only `events_interface/*.py` and `tests/events_interface/*`) — it
      is legacy/orphaned, not an active migration target. The fix in todo 1 correctly lands in `event_sink.py` (imported
      by `_sink_factory.py`, which is what services actually call) with the `CoordinationEvent` type sourced from the
      `events/` package SSOT — no changes needed to `events_interface/`.

## Progress Log

- **2026-07-30 (plans-corpus-reduction-marathon wave 4)**: both todos shipped in one pass —
  `unified-trading-library@d62a9c64`. Full `quality-gates.sh` green. Both the code fix and the SSOT-confirmation
  research todo are resolved; no remaining work. Ready to archive.
