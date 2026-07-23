---
doc_type: codex-ssot
title: Execution-Service Per-Client Isolation
summary:
  Execution-service is always isolated (one process per client_id) — three enforcement layers (topology fan-out,
  isolation_policy binding, LiveTrigger assert_client_allowed) plus per-client Secret Manager credential loading.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, execution-service]
scope: [engineer, admin]
tags: [execution, cefi, defi, mvp, escalation]
related:
  [
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/transfer-coordinator.md,
  ]
created: 2026-05-20
authoritative_for: [execution-service per-client process isolation enforcement]
referenced_by:
  [
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/identity-model.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
  ]
owner:
last_reviewed: 2026-05-20
code_refs:
---

# Execution-Service Per-Client Isolation

## Overview

Execution-service is **always isolated** — one process per client, enforced at the platform level. Per-client venue API
keys, rate limits, entitlements, and order-flow confidentiality cannot be safely multiplexed in a single process.

SSOT: `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md` § Phase 6. Cross-reference:
`/codex/04-architecture/client-funds-isolation.md` HARD RULE — funds NEVER move between different clients.

**For May-23 2-client launch**: existing pattern is correct. No code change required. Deployment-api fans out one
execution-service process per client_id (Odum Research UK + defi-client-1).

---

## Enforcement layers

```
deployment-api
  └── runtime_profile fan-out: one execution-service process per CLIENT_ID
        └── isolation_policy.py
              ├── _load_policy(): reads runtime-topology.yaml isolation_policies.execution-service.default = "isolated"
              ├── get_bound_client_id(): returns CLIENT_ID env var (injected by deployment-api)
              ├── assert_client_allowed(client_id): raises CrossClientEventError if client_id ≠ bound
              └── load_client_venue_credentials(venue): fetches creds from Secret Manager at clients/<client_id>/<venue>/
        └── engine/modes/live/trigger.py
              └── LiveTrigger.on_instruction(): calls assert_client_allowed before queuing
```

### Layer 1 — topology (deployment-api)

`runtime-topology.yaml` sets `isolation_policies.execution-service.default = isolated` and `allowed = [isolated]`.
Deployment-api's runtime_profile fan-out creates one process per `client_id`, injecting `CLIENT_ID` as an env var. A
shared execution-service process is topology-impossible.

### Layer 2 — process binding (`isolation_policy.py:1-80`)

| Function                               | Behaviour                                                                                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `get_my_isolation_policy()`            | Reads `runtime-topology.yaml` via `get_isolation_policy("execution-service")`. Cached after first call.                                    |
| `get_bound_client_id()`                | Returns `CLIENT_ID` env var. `None` when unset (test / non-isolated mode).                                                                 |
| `assert_client_allowed(client_id)`     | In ISOLATED mode: raises `CrossClientEventError` if `client_id ≠ bound`. No-op in non-isolated mode.                                       |
| `load_client_venue_credentials(venue)` | Fetches `clients/<client_id>/<venue>/api_key` (+ `api_secret`) from Secret Manager. Raises `MissingClientBindingError` if CLIENT_ID unset. |

### Layer 3 — bus layer (`trigger.py:34`)

`LiveTrigger.on_instruction()` calls `assert_client_allowed(instruction["client_id"])` before queuing. A cross-client
instruction is silently dropped with a `CROSS_CLIENT_INSTRUCTION_REJECTED` warning log — it never reaches the handler.

---

## Credential loading

```
clients/<client_id>/<venue>/api_key        — always present
clients/<client_id>/<venue>/api_secret     — optional (venue-dependent)
```

Loaded via `load_client_venue_credentials(venue)`. Uses `get_secret_client()` from UTL — never `os.getenv` or a
hardcoded path. Logs `CLIENT_VENUE_CREDENTIALS_LOADED client_id=... venue=... has_secret=...` on each call.

---

## Cross-client transfer enforcement

`assert_client_allowed()` covers incoming event-bus instructions but does NOT cover fund-movement operations that
construct cross-client transfers via metadata (CEX withdrawal destination, DeFi protocol connector wallet, bridge
destination address). These gaps are documented in
`plans/active/issues/cross_client_funds_isolation_retroactive_audit_2026_05_20.md` and closed by the
`TransferCoordinator` facade (Phase 6 new component — see `/codex/04-architecture/transfer-coordinator.md`).

---

## Scaling beyond May-23

For 2 clients on May-23: 2 execution-service processes (one per client_id). Deployment-api fans out automatically when
`clients.yaml` lists 2 entries. Adding a 3rd client = adding an entry to `clients.yaml` + deployment-api promotion; no
code change to execution-service.

Per-venue rate limits: loaded from `RateLimitDomainConfig` via hot-reloadable domain config reloader
(`config_reloaders.py`). Rate limits are per-client per-venue and do not bleed across processes.
