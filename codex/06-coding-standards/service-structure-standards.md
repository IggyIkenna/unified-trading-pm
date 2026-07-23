---
doc_type: codex-ssot
title: Service Structure Standards
summary: >-
  Canonical engine/adapters/cli directory layout for every deployable T4 service — import direction (engine has zero
  adapter imports), singleton adapters <100L, ServiceBootstrap + make_health_router + typed config reloaders,
  shard-level failure isolation, and the file/complexity limit table; QG-enforced via base-service.sh.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer]
tags: [service-structure, quality-gates, uac, instruments, mtds, refactor]
related:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/06-coding-standards/service-orchestration-patterns.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/06-coding-standards/cli-convention.md,
  ]
created: 2026-03-27
authoritative_for: [service directory-structure standards (engine/adapters/cli layout + import-direction rule)]
referenced_by:
  [/codex/06-coding-standards/service-orchestration-patterns.md, /codex/06-coding-standards/thin-adapters-pattern.md]
owner: pm-orchestrator
last_reviewed: 2026-06-25
code_refs:
type: coding-standard
---

# Service Structure Standards

> Canonical SSOT for `engine/adapters/cli` layout. Every deployable service (T4) follows this structure. QG-enforced via
> `base-service.sh` STEP 5.x checks. See also: `/codex/04-architecture/tier-and-import-architecture.md` (5-tier
> dependency model) and `/codex/06-coding-standards/README.md` (full coding standards index).

---

## Directory layout

```
<service>/
  engine/           # Pure business logic — ZERO imports from adapters/
    operations/     # Top-level operation classes (one per --operation CLI arg)
    processors/     # Per-record / per-shard processing
    validation/     # Pre-flight, schema, cluster validation
  adapters/         # Thin I/O wrappers — delegate to UCI/UTL/UAC/UCS
  cli/              # Entry points only — parse args, call engine, exit
  config.py         # Typed config class via ConfigStore (hot-reload capable)
  api/
    main.py         # FastAPI app: make_health_router + data_freshness callback
```

---

## Hard rules (QG-enforced)

### Import direction

- `engine/` has **ZERO imports from `adapters/`** — business logic is adapter-free.
- `adapters/` may import from `engine/` (to call into logic, not to host it).
- `cli/` imports from `engine/` and `adapters/`; no business logic lives in `cli/`.
- **No service↔service imports** — services integrate by API contract / GCS / events (UAC as the shared schema). SSOT:
  `/codex/04-architecture/tier-and-import-architecture.md` § "No service ↔ service imports".

### Adapters

- Each adapter file `< 100 lines`; complex logic belongs in `engine/`.
- **Singleton adapter** pattern — `_ADAPTER_CACHE: dict[str, AdapterType]` (one instance per venue/source); never
  construct a new adapter per request.

### Service bootstrap

- Every service source must include `ServiceBootstrap(...)` (STEP 5.61) — handles `STARTED`/`STOPPED`/`FAILED` lifecycle
  events.
- `api/main.py` must wire `make_health_router` from UTL + a `data_freshness` callback (STEP 5.62).
- Config reloaders use a **typed config class** — never `object` or bare `getattr(service_config, ...)` (STEP 5.34).
- API key hot-reload via `ApiKeyReloader` from UTL, not one-shot `validate_api_keys_for_venues()`. SSOT:
  `/codex/06-coding-standards/config-reloader-pattern.md`.

### Concurrency

- I/O-bound operations: `MAX_WORKERS = 16`.
- CPU-bound operations: `MAX_WORKERS = 1–3`.
- RAM guardrail: at 85% → halve workers to 50%; at 90% → emergency shutdown.
- Use `aiohttp` (not `requests`) in async code.

### Shard-level failure isolation

- **No `raise` inside per-venue/per-shard loops** — errors are classified and logged; the loop continues.
- Every adapter classifies errors via UAC `classify_venue_error()` + emits `ADAPTER_FETCH_FAILED`. SSOT:
  `/codex/04-architecture/shard-level-failure-isolation.md`.

### CLI convention

- CLI uses `--operation` (what), `--mode` (batch/live), `--asset-group` (domain). SSOT:
  `/codex/06-coding-standards/cli-convention.md`.

---

## Schema provenance

- Domain types come from UAC (`unified_api_contracts.{domain}`) — no local type definitions that duplicate UAC types.
- Deep paths (`canonical.*`, `normalize_utils.*`) are UAC-internal — import only from the public surface.

---

## File/complexity limits

| Metric                | Warn | Hard cap |
| --------------------- | ---- | -------- |
| File lines            | 700  | 900      |
| Function lines        | —    | 200      |
| Method lines          | —    | 50       |
| Class lines           | —    | 900      |
| Cyclomatic complexity | —    | 10       |
| Imports per module    | —    | 30       |
| Function parameters   | —    | 5        |
| Test coverage         | —    | ≥ 70%    |

---

## Anti-patterns (banned)

- `app/core/` layout — use `engine/` instead.
- Business logic in `adapters/` — extract to `engine/`.
- Adapters importing from other adapters.
- One-shot API key validation instead of `ApiKeyReloader`.
- `object` or bare `getattr` in config reloaders.
- Local type definitions duplicating UAC types.
