---
doc_type: codex-ssot
title: Unified Service Framework
summary:
  Unified service framework (unified-trading-library/service_framework) — ServiceBootstrap one-call entry,
  UnifiedServiceHandler process() sharing batch/live logic, build_event_sink, create_service_app FastAPI factory.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [infrastructure, ssot, service-framework, batch-live]
related:
  [
    /codex/04-architecture/service-control-surface.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-03-27
authoritative_for:
  [unified service framework (ServiceBootstrap/UnifiedServiceHandler/build_event_sink boilerplate elimination)]
referenced_by: [/codex/04-architecture/service-control-surface.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Unified Service Framework

## Overview

The service framework in `unified-trading-library/service_framework/` eliminates repeated infrastructure boilerplate
across all 23 services. Services implement domain logic only — the framework handles CLI setup, config loading, event
sink wiring, observability, lifecycle events, graceful shutdown, and exit code handling.

## Core Principle: One Handler, Framework Swaps I/O

Batch and live modes share the same business logic. The framework provides different I/O ports based on `--mode`:

| Seam    | Batch                   | Live                    |
| ------- | ----------------------- | ----------------------- |
| Input   | Date-range loop (GCS)   | PubSub subscription     |
| Output  | GCS write               | PubSub publish          |
| Trigger | Run once, exit          | Loop forever on events  |
| Handler | Same `process()` method | Same `process()` method |

## Quick Start: New Service in 15 Lines

```python
# my_service/cli/main.py — ENTIRE FILE
from unified_trading_library import ServiceBootstrap, BaseModeHandler

class ComputeHandler(BaseModeHandler):
    async def run(self) -> dict[str, object]:
        # Your domain logic here
        return {"status": "ok"}

def main() -> None:
    """Main entry point.

    SERVICE_EVENT: STARTED
    SERVICE_EVENT: STOPPED
    SERVICE_EVENT: FAILED
    """
    ServiceBootstrap(
        service_name="my-service",
        operations={"compute": ComputeHandler},
    ).run()
```

## Framework Components

### ServiceBootstrap (`bootstrap.py`)

One-call entry point replacing all `main()` boilerplate. Handles:

1. `.env` loading (dotenv, `override=False`)
2. `LOG_LEVEL` validation against `LogLevel` enum
3. Mock mode check → redirect to `mock_pipeline_fn()` if provided
4. Config resolution via `config_fn()` or static `config`
5. Event sink construction via `build_event_sink()` (topology-driven)
6. `setup_service_observability()` (events + tracing + memory watchdog)
7. `GracefulShutdownHandler` creation
8. Correlation ID generation + `STARTED` lifecycle event
9. Delegation to `ServiceCLI.run()` (existing dispatcher — not replaced)
10. `STOPPED` or `FAILED` event + `sys.exit()`

```python
ServiceBootstrap(
    service_name="my-service",
    operations={"compute": ComputeHandler, "live": LiveHandler},
    config_fn=get_config,
    extra_args_fn=add_custom_args,
    mock_pipeline_fn=run_mock_pipeline,
    categories=["CEFI", "TRADFI", "DEFI"],
    description="My Service — does useful things",
).run()
```

### build_event_sink (`_sink_factory.py`)

Topology-driven event sink selection. Replaces the 15-line if/elif/else block duplicated in every service:

```python
from unified_trading_library import build_event_sink

sink = build_event_sink("my-service", runtime)
# Returns LocalFsEventSink (mock), PubSubEventSink (live), or GcsEventSink (batch)
```

### UnifiedServiceHandler (`handler.py`)

For services where batch and live share the same business logic. Implement `process()` once:

```python
from unified_trading_library import UnifiedServiceHandler, ServiceRuntime

class ComputeHandler(UnifiedServiceHandler):
    def __init__(self, runtime: ServiceRuntime) -> None:
        super().__init__(runtime)
        self._engine = MyOrchestrationService()

    async def process(self, payload: object) -> object:
        return await self._engine.compute(payload)

    async def preflight(self) -> None:
        # Optional: dependency checks before processing starts
        pass
```

The framework automatically:

- Provides `BatchIO` (date-range iteration) or `LiveIO` (PubSub subscription) based on `--mode`
- Calls `process()` for each payload with shard-level failure isolation
- Handles `preflight()` and `cleanup()` lifecycle

### I/O Ports (`io_ports.py`, `io_batch.py`, `io_live.py`)

- `ServiceInput[PayloadT]` — async iterator yielding work items
- `ServiceOutput[ResultT]` — writes results
- `ServiceIO[PayloadT, ResultT]` — combines input + output with setup/teardown
- `BatchIO` — `DateRangeInput` + `StorageOutput`
- `LiveIO` — `PubSubInput` + `PubSubOutput`

### create_service_app (`fastapi_factory.py`)

FastAPI factory for API services:

```python
from unified_trading_library import create_service_app
from my_api.routes import router

app = create_service_app("my-api", routers=[router], auth_dependency=verify_api_key)
```

Includes: lifespan (startup/shutdown), health routes, correlation ID middleware, global error handler.

## Migration Guide

### Step 1: Adopt ServiceBootstrap (no handler changes)

Replace the 50-100 line `main()` with a `ServiceBootstrap` call, keeping existing `BaseModeHandler` subclasses. This
alone eliminates LOG_LEVEL validation, shutdown handler, event sink wiring, STARTED/STOPPED events, and exit codes.

### Step 2 (optional): Merge handlers into UnifiedServiceHandler

For services where batch and live call the same `OrchestrationService`, merge into one `UnifiedServiceHandler`.

### Step 3 (optional): Extract custom I/O

Services with unusual I/O (WebSocket, custom PubSub topics) override `build_io()` on the handler.

## Compatibility

- `ServiceBootstrap` accepts both `BaseModeHandler` (legacy) and `UnifiedServiceHandler` (new)
- `ServiceCLI` is reused internally — not replaced
- `ServiceRuntime` is unchanged — still the single source of truth for runtime config
- Existing `BaseFeatureService` continues to work for feature services that use it

## File Layout

```
unified_trading_library/service_framework/
    __init__.py          # Exports all public symbols
    bootstrap.py         # ServiceBootstrap
    handler.py           # UnifiedServiceHandler
    _adapter.py          # Bridges UnifiedServiceHandler → BaseModeHandler
    _sink_factory.py     # build_event_sink()
    io_ports.py          # ServiceInput, ServiceOutput, ServiceIO protocols
    io_batch.py          # DateRangeInput, StorageOutput, BatchIO
    io_live.py           # PubSubInput, PubSubOutput, LiveIO
    fastapi_factory.py   # create_service_app()
```
