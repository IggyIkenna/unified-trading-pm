---
doc_type: codex-ssot
title: Signal Broadcast Architecture — Outbound Signal Leasing
summary:
  Implementation map for Signal Leasing (fourth commercial path) — outbound-only strategy-signal emission from
  strategy-service to counterparty endpoints, no capital/execution observation. Per-repo role map + D1-D10 decisions
  (strategy-service sub-package, webhook+REST-pull, per-counterparty HMAC, at-least-once idempotency, shard isolation).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, strategy-service, unified-api-contracts, unified-trading-library, unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [strategy, execution, uac, observability, ui, escalation]
related:
  [
    ../_ssot-rules/04-dart-commercial-axes.md,
    ../commercial-model/signal-leasing.md,
    ../../04-architecture/shard-level-failure-isolation.md,
    ../../06-coding-standards/config-reloader-pattern.md,
    /codex/14-customer-journeys/shared-core/instruction-schema-fit-and-package-boundaries.md,
  ]
created: 2026-04-20
authoritative_for: [signal leasing/broadcast outbound emission architecture (D1-D10)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md,
    /codex/09-strategy/strategy-summary.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Signal Broadcast Architecture — Outbound Signal Leasing

> Implementation map for outbound signal emission from `strategy-service` to external counterparties. Signal Leasing is
> the fourth commercial path (alongside DART, IM, Reg Umbrella); it is output-only — Odum emits signals, the
> counterparty executes on their own infrastructure, no capital flows, no execution observation.

**Rule sources:** [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md) (Signal Leasing is outside
the 2×3 matrix), [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) (signals are
Odum-enriched output),
[rule 10 — strategy instruction schema principles](../_ssot-rules/10-strategy-instruction-schema-principles.md)
(schema-depth dimension reused for payload projection).

**Plan SSOT:**
[`signal_leasing_broadcast_architecture_2026_04_20.plan.md`](../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md)
— decisions D1–D10 locked, 8-repo scope, Phase 6 of 8.

**Commercial framing:** [`../commercial-model/signal-leasing.md`](../commercial-model/signal-leasing.md) — pricing
options, Sept 2026 go-live, $5k/mo two-counterparty anchor.

## Why this doc exists

Signal Leasing emits Odum strategy signals to institutional counterparty endpoints. This is **not** DART
`Instructions integration` (block 5) — DART instructions are _inbound_ (client → Odum execution). Signal Leasing is
_outbound_ (Odum → counterparty execution). Different direction, different data model, different failure semantics,
different auth. The architecture reuses every workspace-standard pattern (shard-level isolation, `classify_venue_error`,
`ApiKeyReloader`, `ServiceBootstrap`, `make_health_router`) but composes them into a net-new emission pathway.

This doc is the implementation map: which repo owns what, how the pieces compose at runtime, and which SSOT rule each
invariant enforces.

## Direction and scope

```
┌────────────────────────┐       ┌───────────────────────┐
│  Odum strategy-service │ ───▶  │  Counterparty         │
│  (signal generation)   │       │  (executes on own     │
│                        │ ◀───  │   infra — Odum does   │
│  emits signal payload  │  ack  │   NOT see fills)      │
└────────────────────────┘       └───────────────────────┘

        outbound (this doc)          NOT DART inbound
```

Signal Leasing does **not**: manage capital, observe counterparty execution, report back counterparty P&L by default, or
reuse the DART instruction schema. It **does**: emit strategy-level signals on a negotiated schedule, optionally receive
acknowledgements, and log every delivery for billing/audit.

## Implementation map

| Repo                        | Path                                                                                                             | Role                                                                                                                                                                                                                                                                   |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`     | `unified_api_contracts/signal_broadcast.py` (facade) + `unified_api_contracts/internal/domain/signal_broadcast/` | Entity + event schemas: `Counterparty`, `CounterpartyEntitlement`, `SchemaDepth`, `SignalEmission`, `SignalAcknowledgement`, `SignalPayloadMinimal` / `Standard` / `Rich`. Consumer repos import via the `signal_broadcast` facade only.                               |
| `unified-api-contracts`     | `unified_api_contracts/registry/capability_declarations/_signal_broadcast.py`                                    | Capability registry for the signal-broadcast surface per UAC Citadel architecture convention.                                                                                                                                                                          |
| `unified-trading-library`   | `unified_trading_library/events/__init__.py` (`STANDARD_LIFECYCLE_EVENTS`)                                       | Two lifecycle events: `STRATEGY_SIGNAL_EMITTED_EXTERNAL` (every successful or retrying delivery), `STRATEGY_SIGNAL_ACKNOWLEDGED` (counterparty ack). Registered alongside the existing 11 batch / 12 live events.                                                      |
| `strategy-service`          | `strategy_service/signal_broadcast/emitter.py`                                                                   | **Orchestrator.** Wires router, transport, credentials, audit, failure-isolation. Computes `emission_id` (uuid5) for D5 idempotency; enforces D7 token-bucket rate limit per (counterparty, strategy); wraps every per-counterparty call in D10 shard-level isolation. |
| `strategy-service`          | `strategy_service/signal_broadcast/router.py`                                                                    | Resolves (slot_label, counterparty_id) → entitled emission + per-counterparty schema-depth projection (D4 allowlist + D8 negotiated depth).                                                                                                                            |
| `strategy-service`          | `strategy_service/signal_broadcast/transport.py`                                                                 | D2 hybrid: webhook HTTP POST primary + REST-pull endpoint for counterparty-initiated reconciliation/backfill. At-least-once retry on 5xx + network errors; idempotency key in `X-Odum-Emission-Id` header.                                                             |
| `strategy-service`          | `strategy_service/signal_broadcast/credentials.py`                                                               | D3 per-counterparty HMAC secret fetched via UTL `ApiKeyReloader` pattern (hot-reload on Secret Manager rotation). Signs every payload with the counterparty-specific key.                                                                                              |
| `strategy-service`          | `strategy_service/signal_broadcast/audit.py`                                                                     | Emits `STRATEGY_SIGNAL_EMITTED_EXTERNAL` and `STRATEGY_SIGNAL_ACKNOWLEDGED`; writes BQ billing log (D6 per-signal granularity — billing contract picks emit or ack column).                                                                                            |
| `strategy-service`          | `strategy_service/signal_broadcast/failure_isolation.py`                                                         | Per-counterparty try/except with `classify_venue_error()` + `ADAPTER_FETCH_FAILED` emit. **Never raises to the signal generator.** D10 anchor.                                                                                                                         |
| `strategy-service`          | `strategy_service/signal_broadcast/config.py` + `config_reloaders.py`                                            | Typed `SignalBroadcastConfig` (STEP 5.34) + `start_signal_broadcast_reloaders(service_config: SignalBroadcastConfig, ...)`. No `object` type, no `getattr`.                                                                                                            |
| `strategy-service`          | `strategy_service/signal_broadcast/broadcaster.py`                                                               | Singleton facade (`SignalBroadcaster.build()`) consumed by the CLI entry point and the `make_health_router` `data_freshness` callback.                                                                                                                                 |
| `strategy-service`          | `strategy_service/cli/service_entry.py` + `api/main.py`                                                          | `ServiceBootstrap` invocation + `make_health_router` `data_freshness` callback returns a nested `signal_broadcast` block sourced from `broadcaster.data_freshness()`. REST-pull router mounted when the broadcaster singleton is active.                               |
| `deployment-service`        | `scripts/provision-signal-broadcast-secrets.sh`                                                                  | Creates / rotates per-counterparty HMAC secrets under the naming convention `signal-broadcast-counterparty-{cp_id}-hmac`.                                                                                                                                              |
| `deployment-service`        | `configs/signal-broadcast/counterparties.yaml`                                                                   | Deploy-time mirror of the two staging counterparty fixtures (counterparty_id / webhook_url / schema_depth / allowed_slots / active_from/to / rate_limit / secret_manager_ref). Runtime source of truth remains UAC `Counterparty`.                                     |
| `deployment-service`        | `terraform/services/strategy-service/gcp/`                                                                       | Cloud Run Job extension (D1 recommendation (a) — no 67th service). Adds `secret_environment_variables` (HMAC secrets) + 8 `SIGNAL_BROADCAST_*` env vars to the existing strategy-service deployment.                                                                   |
| `deployment-service`        | `scripts/smoke-signal-broadcast.sh`                                                                              | Local-emulator smoke — drives the strategy-service Phase-3 integration suite (uses `responses`, zero live HTTP). Live-staging smoke with real GCP creds deferred to human operator.                                                                                    |
| `unified-trading-system-ui` | `app/(platform)/services/signals/dashboard/page.tsx`                                                             | Counterparty observability UI — 4 panels: `<SignalHistoryTable>`, `<BacktestComparisonPanel>`, `<DeliveryHealthPanel>`, `<PnlAttributionPanel>` (renders null until `Counterparty.pnl_reporting_enabled`).                                                             |
| `unified-trading-system-ui` | `app/(platform)/services/signals/counterparties/page.tsx`                                                        | Admin surface — counterparty table, detail panel, entitlement toggle, active flip, delivery-health rollup, audit event list. Admin-only gate.                                                                                                                          |
| `unified-trading-system-ui` | `lib/auth/counterparty.ts`                                                                                       | Counterparty persona stub (D9) — `COUNTERPARTY_USER_TYPE = "counterparty"`, `COUNTERPARTY_POST_AUTH_REDIRECT = "/services/signals/dashboard"`, `isCounterpartyUser()` discriminator, `postAuthRedirectFor()` helper.                                                   |

## Failure isolation (D10)

Signal emission to external counterparties follows the
[shard-level failure isolation](../../04-architecture/shard-level-failure-isolation.md) rule verbatim. Each counterparty
delivery is a "shard" at the granularity of (slot_label, counterparty_id). The invariant:

- **Per-counterparty try/except.** `failure_isolation.py` wraps every webhook POST. A failed counterparty delivery must
  never impact strategy-service operation or any other counterparty's delivery.
- **Classify through UAC.** Every exception flows through `classify_venue_error()` (UAC) to produce a structured
  `VenueError` with `error_code`, `action`, `retry_safe`.
- **Emit `ADAPTER_FETCH_FAILED`.** Every failure logs `ADAPTER_FETCH_FAILED` via
  `log_event("ADAPTER_FETCH_FAILED", details={...})` with the classified error.
- **Never raises to the signal generator.** The strategy that generated the signal does not see counterparty delivery
  failures — it continues with the next tick.

This matches how every adapter handles venue-API failures. Signal broadcast is an adapter; the counterparty endpoint is
the "venue" from the isolation rule's perspective.

## Authentication model (D3)

- **Per-counterparty HMAC secret.** Each counterparty has its own HMAC secret stored in Secret Manager under
  `signal-broadcast-counterparty-{cp_id}-hmac`. Provisioned by
  `deployment-service/scripts/provision-signal-broadcast-secrets.sh`.
- **Hot-reload via `ApiKeyReloader`.** `credentials.py` reuses the UTL `ApiKeyReloader` pattern — when a secret rotates,
  the next emission picks up the new key without a service restart. SSOT:
  [`../../06-coding-standards/config-reloader-pattern.md`](../../06-coding-standards/config-reloader-pattern.md).
- **Payload signing.** Every emitted payload is HMAC-signed with the counterparty-specific key and sent in the
  `X-Odum-Signature` header. Counterparties verify server-side.
- **No OAuth, no mTLS.** D3 resolution — HMAC is the institutional-signal-feed standard; OAuth / mTLS add operational
  overhead without meaningful security uplift for this threat model.

The credential convention matches
[interface-credential-convention](../../04-architecture/interface-credential-convention.md): credentials fetched from
Secret Manager, injected into the transport layer at runtime. Counterparty credentials are never passed as constructor
params to strategy code — isolation stays at the broadcast layer.

## Delivery transport (D2)

Hybrid: webhook primary + REST-pull fallback.

- **Webhook (primary).** HTTP POST to the counterparty-supplied URL. At-least-once retry on network errors, 5xx
  responses, or classified-retryable venue errors. `emission_id` (uuid5 over strategy_id + slot_label +
  emission_timestamp) in the `X-Odum-Emission-Id` header for counterparty-side dedup.
- **REST-pull (fallback).** Counterparty can reconcile by calling `GET /signal-broadcast/emissions?since=...` on
  strategy-service. Mounted by `api/main.py` when the broadcaster singleton is active. Used for counterparty-initiated
  backfill after outages.
- **Delivery guarantees (D5).** At-least-once with idempotency key. Exactly-once is over-engineered for signal delivery;
  at-most-once drops signals on transient failures.

## Rate limiting (D7)

Per-counterparty-per-strategy token bucket.

- **Config source.** Per-counterparty rate limit lives in UAC `Counterparty.rate_limit_per_strategy_per_sec` (runtime
  source of truth). Service-wide transport knobs (max retries, backoff base, timeout) exposed via terraform variables
  - `SIGNAL_BROADCAST_WEBHOOK_*` env vars.
- **Granularity.** (counterparty_id, strategy_id) — a noisy strategy on one counterparty does not starve other
  strategies on the same counterparty, and one counterparty's burst does not affect others.
- **Enforcement.** `emitter.py` checks the token bucket before calling transport. Rate-limited emissions are logged (not
  dropped silently) via `ADAPTER_FETCH_FAILED` with `error_code=RATE_LIMITED`.

## Schema depth (D8)

Per-counterparty negotiated depth — mirrors
[rule 10 schema-depth dimension](../_ssot-rules/10-strategy-instruction-schema-principles.md):

| Depth      | Contents                                                                                                        |
| ---------- | --------------------------------------------------------------------------------------------------------------- |
| `minimal`  | Instrument, direction, target size, timestamp — the eight-ish minimum required for counterparty to act.         |
| `standard` | Minimal + confidence, strategy-family tag, parent-child grouping, cadence hint.                                 |
| `rich`     | Standard + bespoke fields negotiated per counterparty (proprietary risk overlays, custom execution directives). |

Depth is declared on `Counterparty.schema_depth` and applied by `router.py` before payload construction. Payload shape
types: `SignalPayloadMinimal`, `SignalPayloadStandard`, `SignalPayloadRich` (UAC).

## Observability

Two surfaces, both backed by the UTL event stream and the BQ billing log.

- **Counterparty dashboard** (`/services/signals/dashboard`). Four panels:
  - `<SignalHistoryTable>` — last N emissions scoped to entitled slots; filter by slot / date / status.
  - `<BacktestComparisonPanel>` — Odum-held backtest numbers vs live signal aggregate (read-only). Per-archetype
    paper-readiness gate (paper-runnable / paper-shippable / backtest-only / stub) determines which strategies surface
    their backtest comparisons here — see
    [`archetype-paper-readiness.md`](../../09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md) for
    the 4-state taxonomy SSOT (ST-20 cross-ref, added 2026-05-13).
  - `<DeliveryHealthPanel>` — webhook success rate, retry counts, avg latency, last-delivery timestamp.
  - `<PnlAttributionPanel>` — renders null until `Counterparty.pnl_reporting_enabled` (post-Sept-2026 follow-up).
- **Admin surface** (`/services/signals/counterparties`). Counterparty table, detail panel, entitlement toggle, active
  flip, delivery-health rollup, audit event list. Admin-only gate.

The event timeline feeding both surfaces:

```
STRATEGY_SIGNAL_EMITTED_EXTERNAL  ──▶  (counterparty endpoint)  ──▶  STRATEGY_SIGNAL_ACKNOWLEDGED
                                 │
                                 └─ (on failure) ADAPTER_FETCH_FAILED + classify_venue_error()
```

BQ billing log records one row per emission with: emission_id, strategy_id, slot_label, counterparty_id, schema_depth,
attempts, final_status, latency_ms, acked_at.

## Service-infrastructure invariants

Every service in the workspace is enforced to meet five invariants (QG-enforced as errors). Signal-broadcast slots into
the existing strategy-service deployment, so these are inherited:

- **`ServiceBootstrap`** — `strategy_service/cli/service_entry.py` calls
  `ServiceBootstrap(service_name="strategy-service", ...)`; signal-broadcast config reloaders wired in via
  `_get_config()`.
- **Health API** — `strategy_service/api/main.py` uses `make_health_router` (UTL); `data_freshness` callback extended to
  include a nested `signal_broadcast` block from `broadcaster.data_freshness()`.
- **Typed config reloaders** — `signal_broadcast/config_reloaders.py` exposes
  `start_signal_broadcast_reloaders(service_config: SignalBroadcastConfig, ...)`. No `object`, no `getattr`.
- **Schema provenance** — all domain types (`Counterparty`, `SignalEmission`, etc.) live in UAC
  `internal.domain.signal_broadcast/`, re-exported via the `signal_broadcast` facade. Zero local definitions in
  strategy-service source.
- **API key hot-reload** — `credentials.py` uses UTL `ApiKeyReloader`, not a one-shot key fetch.

## Decision map (D1–D10)

| #   | Decision                      | Resolution                                                                     |
| --- | ----------------------------- | ------------------------------------------------------------------------------ |
| D1  | Emission service ownership    | Sub-package in `strategy-service`; Cloud Run Job extended; no 67th service.    |
| D2  | Delivery transport            | Hybrid — webhook primary, REST-pull fallback.                                  |
| D3  | Authentication model          | Per-counterparty HMAC secret via `ApiKeyReloader`; payload signed server-side. |
| D4  | Which strategies are leasable | Per-counterparty slot_label allowlist (`CounterpartyEntitlement`).             |
| D5  | Delivery guarantees           | At-least-once with uuid5 idempotency key.                                      |
| D6  | Metering + audit granularity  | Emit + ack events, both logged; billing picks emit or ack per contract.        |
| D7  | Rate limiting                 | Per-counterparty-per-strategy token bucket.                                    |
| D8  | Payload schema                | Negotiated schema depth — `minimal` / `standard` / `rich`.                     |
| D9  | Counterparty persona          | Domain entity distinct from "client" (no capital, no DART reporting surface).  |
| D10 | Failure isolation             | Shard-level — `classify_venue_error` + `ADAPTER_FETCH_FAILED`; never raises.   |

## Cross-references

- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md) — Signal Leasing as fourth path
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — enriched output, not raw data
- [rule 10 — strategy instruction schema principles](../_ssot-rules/10-strategy-instruction-schema-principles.md) —
  schema-depth dimension reused for payload projection
- [../commercial-model/signal-leasing.md](../commercial-model/signal-leasing.md) — commercial framing, pricing, Sept
  2026 anchor
- [dart-pricing-axes.md](dart-pricing-axes.md) — related pricing model (DART side)
- [../../04-architecture/shard-level-failure-isolation.md](../../04-architecture/shard-level-failure-isolation.md) — D10
  rule anchor
- [../../04-architecture/interface-credential-convention.md](../../04-architecture/interface-credential-convention.md) —
  D3 credential pattern
- [../../06-coding-standards/config-reloader-pattern.md](../../06-coding-standards/config-reloader-pattern.md) —
  `ApiKeyReloader` hot-reload pattern
- [`instruction-schema-fit-and-package-boundaries.md`](instruction-schema-fit-and-package-boundaries.md) — inbound DART
  instruction schema (direction contrast — not this doc)
- [`../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md`](../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md)
  — plan SSOT, D1–D10 locked, 8-repo scope
