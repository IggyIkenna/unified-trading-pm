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
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer]
tags: [event-sink, mock-mode, live-mode, coordination-event, cleanup, shutdown, data-correctness]
related:
  [
    /plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md,
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
resolved_by:
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

- [ ] [SCRIPT] P2. Add no-op `publish_coordination_event`/`subscribe_coordination_events` methods to `LocalFsEventSink`
      in `unified_trading_library/event_sink.py` (mirror `events/sink.py::MockEventSink`'s no-op pattern), so any
      service's live+mock-mode cleanup() no longer needs a defensive `AttributeError` suppress. Add a regression test
      exercising `build_event_sink()` with `is_mock=True, mode="live"` → `publish_coordination_event()` completes
      without raising. Repo: unified-trading-library.
- [ ] [SCRIPT] P3. Before landing the above, grep recent commit history on `event_sink.py` vs `events/` vs
      `events_interface/` to confirm which module is the live SSOT (this workspace's usual event/schema migrations leave
      a superseded-banner or a codex note) — if `events_interface/` is the intended eventual replacement, land the fix
      there instead (or in both, if both are still actively consumed). Repo: unified-trading-library.
