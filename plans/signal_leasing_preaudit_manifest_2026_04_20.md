---
title: "Signal Leasing — Phase 1 pre-audit manifest"
status: active
companion_to: signal_leasing_broadcast_architecture_2026_04_20.md
locked_by: live-defi-rollout
locked_since: 2026-04-20
---

# Pre-audit manifest — signal leasing blast radius

Companion to
[active/signal_leasing_broadcast_architecture_2026_04_20.md](active/signal_leasing_broadcast_architecture_2026_04_20.md).
Built from a workspace-wide scan of 8 repos on 2026-04-20. Consume in Phases 2-10; do not re-scan.

All paths are absolute under `$WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos`.

## D1-D10 locked 2026-04-20

| #   | Decision           | Locked value                                                                                                                                                                                           |
| --- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| D1  | Emission ownership | **New sub-package in `strategy-service`** (`strategy_service/signal_broadcast/`). No new repo.                                                                                                         |
| D2  | Transport          | **Hybrid** — webhook HTTP POST primary, REST pull fallback for counterparty-initiated reconciliation.                                                                                                  |
| D3  | Auth               | **Per-counterparty API key in Secret Manager + HMAC signing** of payload. ApiKeyReloader for hot-reload.                                                                                               |
| D4  | Entitlement        | **Per-counterparty allowlist of slot labels stored in UAC registry** (no new lock-state enum value).                                                                                                   |
| D5  | Delivery           | **At-least-once with idempotency key** (counterparty-side dedup). Never exactly-once.                                                                                                                  |
| D6  | Audit              | **Emit + ack events, both logged** — `STRATEGY_SIGNAL_EMITTED_EXTERNAL` + `STRATEGY_SIGNAL_ACKNOWLEDGED`.                                                                                              |
| D7  | Rate limit         | **Per-counterparty-per-strategy** bucketing.                                                                                                                                                           |
| D8  | Payload schema     | **Negotiated schema depth** — `minimal` / `standard` / `rich` enum on the `Counterparty` entity.                                                                                                       |
| D9  | Persona            | **New domain entity "counterparty"** in UAC — distinct from `ClientDefinition`.                                                                                                                        |
| D10 | Failure isolation  | **At-least-once retries never block strategy-service** — per `shard-level-failure-isolation.md`, classify via `classify_venue_error()`, emit `ADAPTER_FETCH_FAILED`, swallow in per-counterparty loop. |

## Existing system hooks (reuse, do not reinvent)

- `STRATEGY_SIGNAL_GENERATED` UTL event already emitted in strategy-service — the new emitter subscribes to it, does NOT
  replace it. See
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-library/unified_trading_library/events/event_types.py:295`.
- `BroadcastSink`
  (`/Users/ikennaigboaka/Code/unified-trading-system-repos/strategy-service/strategy_service/adapters/broadcast_sink.py:15`)
  is the existing internal Pub/Sub + SSE fan-out; **signal-leasing emission runs in parallel to this**, not replacing it
  — internal consumers keep their channel.
- `ApiKeyReloader`
  (`/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-library/unified_trading_library/api_key_reloader.py:23`)
  is the canonical hot-reload pattern. D3 integration uses this verbatim.
- `classify_venue_error`
  (`/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/__init__.py`)
  already exported at UAC root. The "adapter error classification" discipline applies to counterparty webhooks
  identically — counterparty endpoint = external API from strategy-service's perspective.
- `make_health_router` + `make_sse_router` from UTL service-framework — already in use at
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/strategy-service/strategy_service/api/main.py:12`.
  Signal-broadcast adds a new sub-router to the SAME FastAPI app (no new service process).
- `ServiceBootstrap` at
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-library/unified_trading_library/service_framework/bootstrap.py`.
  Existing strategy-service bootstrap absorbs the new sub-package — no new ServiceBootstrap call.
- No pre-existing `hmac`/HMAC webhook utility in any service repo; only stdlib `hmac` +
  `cryptography.hazmat.primitives.hmac` available. D3 HMAC signing utility is net-new code (placement below).

## Per-repo manifest

### 1. unified-api-contracts (UAC)

**CREATE:**

- `unified-api-contracts/unified_api_contracts/internal/domain/signal_broadcast/__init__.py` — domain package init;
  re-export entities.
- `unified-api-contracts/unified_api_contracts/internal/domain/signal_broadcast/counterparty.py` — `Counterparty`
  Pydantic BaseModel (fields: `counterparty_id`, `name`, `endpoint_url`, `auth_method` Literal["HMAC_SHA256"],
  `hmac_secret_ref`, `allowed_slots: frozenset[str]`, `schema_depth: SchemaDepth`, `rate_limit_per_strategy_per_sec`,
  `active: bool`, `created_at`, `activated_at`). Enforce immutable via `model_config = ConfigDict(frozen=True)` per
  `strategy_availability.py:30` precedent.
- `unified-api-contracts/unified_api_contracts/internal/domain/signal_broadcast/entitlement.py` —
  `CounterpartyEntitlement(counterparty_id, slot_label, active_from, active_to | None)`. Allowlist helper
  `entitled_slots_for(counterparty_id: str) -> frozenset[str]`.
- `unified-api-contracts/unified_api_contracts/internal/domain/signal_broadcast/schema_depth.py` — `SchemaDepth` StrEnum
  (`MINIMAL | STANDARD | RICH`) + per-depth payload shape selector. Mirrors rule-10 schema-depth dimension.
- `unified-api-contracts/unified_api_contracts/internal/domain/signal_broadcast/events.py` — Pydantic payload schemas
  consumed by `log_event` detail dicts:
  `SignalEmissionPayload(emission_id: UUID, counterparty_id, strategy_id, slot_label, emission_timestamp, signal_payload: JSONDict, idempotency_key, delivery_attempt: int, schema_depth)`,
  `SignalAcknowledgementPayload(emission_id, counterparty_id, ack_timestamp, status: Literal["DELIVERED","FAILED","DUPLICATE"], http_status_code, latency_ms)`.
- `unified-api-contracts/unified_api_contracts/internal/domain/signal_broadcast/registry.py` —
  `COUNTERPARTY_REGISTRY: dict[str, Counterparty]`; helper `counterparty_for(id)`, `active_counterparties()`,
  `entitlements_for(counterparty_id)`. Pre-seeded with 2 stub counterparties (populated at Phase 4 via Secret Manager
  bindings).
- `unified-api-contracts/unified_api_contracts/signal_broadcast.py` — **new domain facade** at repo root (sibling to
  `strategy.py`, `execution.py`, etc.). Re-exports `Counterparty`, `CounterpartyEntitlement`, `SchemaDepth`,
  `SignalEmissionPayload`, `SignalAcknowledgementPayload`, `COUNTERPARTY_REGISTRY`. Consumer import path:
  `from unified_api_contracts.signal_broadcast import Counterparty, ...`.
- `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_signal_broadcast.py` — per
  `strategy-service v2` precedent; declares `SIGNAL_BROADCAST_CAPABILITIES` (supported schema depths, max
  counterparties, rate-limit bounds). Not a per-venue capability file but follows same declarative shape as `_cefi.py`,
  `_defi.py` siblings.
- `unified-api-contracts/tests/unit/test_signal_broadcast_schemas.py` — unit tests for frozen invariants +
  `entitled_slots_for` + schema-depth payload round-trips.
- `unified-api-contracts/tests/unit/test_counterparty_registry.py` — registry lookup + allowlist enforcement tests.

**EDIT:**

- `unified-api-contracts/unified_api_contracts/__init__.py:1-100` — add re-exports for `Counterparty`,
  `CounterpartyEntitlement`, `SchemaDepth`, `SignalEmissionPayload`, `SignalAcknowledgementPayload`,
  `COUNTERPARTY_REGISTRY` per Citadel Import Rule (root facade surface).
- `unified-api-contracts/unified_api_contracts/internal/__init__.py` — re-export the 6 symbols above from
  `internal.domain.signal_broadcast.*` so services can `from unified_api_contracts.internal import Counterparty`
  (matches the pattern used for `StrategySignalMessage` in `signal_publisher.py:56`).
- `unified-api-contracts/docs/UAC_ADOPTION_MATRIX.md` — add `signal_broadcast` domain row.

**REFERENCES (no change, depend on):**

- `unified_api_contracts/internal/architecture_v2/strategy_availability.py` — pattern precedent for StrEnum + BaseModel
  frozen invariants. Follow this shape for `SchemaDepth` + `Counterparty`.
- `unified_api_contracts/strategy.py:1-64` — pattern precedent for root domain facade. `signal_broadcast.py` follows
  this file byte-for-byte in structure.
- `unified_api_contracts/canonical/crosscutting/errors/__init__.py` — source of `classify_venue_error`.
- `unified_api_contracts/registry/capability_declarations/_cefi.py` + `_defi.py` — structural templates for
  `_signal_broadcast.py`.
- `unified_api_contracts/internal/domain/strategy_service/client_registry.py` — contrast pattern: `ClientDefinition` /
  `ClientRegistry` is the peer that `Counterparty` must be semantically DISTINCT from (D9).

### 2. unified-trading-library (UTL)

**CREATE:**

- `unified-trading-library/unified_trading_library/signal_broadcast/__init__.py` — NEW sub-package for shared emission
  helpers that any future service might reuse. Initially only exports
  `build_hmac_signature(payload: bytes, secret: str) -> str` +
  `verify_hmac_signature(payload: bytes, signature: str, secret: str) -> bool` utilities. Kept in UTL (not
  strategy-service) because they are pure crypto and reusable.
- `unified-trading-library/unified_trading_library/signal_broadcast/hmac_signing.py` — HMAC-SHA256 utilities above;
  `cryptography.hazmat.primitives.hmac` backed, constant-time compare.
- `unified-trading-library/tests/unit/test_signal_broadcast_hmac.py` — verify signing + tampered-payload rejection
  - constant-time behaviour.
- `unified-trading-library/tests/events/unit/test_signal_broadcast_events.py` — lock test: both new events live in
  `STANDARD_LIFECYCLE_EVENTS`.

**EDIT:**

- `unified-trading-library/unified_trading_library/events/event_types.py:289-305` — add below `BACKTEST_COMPLETED`:
  ```python
  STRATEGY_SIGNAL_EMITTED_EXTERNAL = "STRATEGY_SIGNAL_EMITTED_EXTERNAL"
  STRATEGY_SIGNAL_ACKNOWLEDGED = "STRATEGY_SIGNAL_ACKNOWLEDGED"
  ```
  and include both in `STRATEGY_EVENT_TYPES`. Then in the `STANDARD_LIFECYCLE_EVENTS.update(...)` block at
  `event_types.py:~640-690`, add both event names.
- `unified-trading-library/unified_trading_library/events/__init__.py:49-200` — add `STRATEGY_SIGNAL_EMITTED_EXTERNAL`
  and `STRATEGY_SIGNAL_ACKNOWLEDGED` imports from `event_types`, and to `__all__` block at line ~524.
- `unified-trading-library/unified_trading_library/__init__.py:293` (imports) and `:1686` (`__all__`) — add both symbol
  re-exports so consumers can `from unified_trading_library import STRATEGY_SIGNAL_EMITTED_EXTERNAL`.
- `unified-trading-library/tests/events/unit/test_canonicalized_events.py` — extend parametrized list + set assertion at
  `:66` and `:166` to include the 2 new events.
- `unified-trading-library/tests/events/unit/test_schemas.py` — lock-test update to cover the 2 new events.

**REFERENCES (no change):**

- `unified-trading-library/unified_trading_library/api_key_reloader.py:23` — `ApiKeyReloader` class. D3 uses it
  unchanged; strategy-service's `signal_broadcast/credentials.py` instantiates it per-counterparty.
- `unified-trading-library/unified_trading_library/events/schemas.py:1-80` — `LifecycleEvent` +
  `STANDARD_LIFECYCLE_EVENTS` mechanics. No changes; only augmented via `event_types.py` import side-effect.
- `unified-trading-library/unified_trading_library/service_framework/bootstrap.py` — `ServiceBootstrap`. No change;
  strategy-service's existing bootstrap covers the new sub-package.
- `unified-trading-library/unified_trading_library/config_reloader.py` — typed config reloader pattern. New
  signal-broadcast config reloader uses this verbatim.

### 3. strategy-service

**CREATE:**

- `strategy-service/strategy_service/signal_broadcast/__init__.py` — NEW sub-package init; exports `SignalBroadcaster`,
  `CounterpartyRouter`, `WebhookTransport`, `SignalBroadcastAuditLogger`.
- `strategy-service/strategy_service/signal_broadcast/emitter.py` — `SignalBroadcaster` class. Subscribes to the
  existing `STRATEGY_SIGNAL_GENERATED` event stream (or observes the same record the existing `BroadcastSink`
  publishes). For each counterparty × emitted slot tuple from the router, builds the schema-depth-shaped payload, calls
  `WebhookTransport.deliver`, emits `STRATEGY_SIGNAL_EMITTED_EXTERNAL`. Wraps each counterparty in a try/except that
  classifies via `classify_venue_error` and emits `ADAPTER_FETCH_FAILED` (D10 + shard-level-failure rule). Never raises
  to the strategy cycle.
- `strategy-service/strategy_service/signal_broadcast/router.py` — `CounterpartyRouter`. Given
  `(slot_label, signal_record)`, returns the list of `(Counterparty, SchemaDepth)` tuples entitled to receive. Reads
  from UAC `COUNTERPARTY_REGISTRY` + `entitled_slots_for()`. Pure function, no I/O.
- `strategy-service/strategy_service/signal_broadcast/transport.py` — `WebhookTransport` (primary) + `RestPullEndpoint`
  (fallback, FastAPI sub-router). `WebhookTransport.deliver(counterparty, payload) -> DeliveryResult` with at-least-once
  retry loop (exponential backoff, max 3 retries, idempotency key header). `RestPullEndpoint` exposes
  `/signal-broadcast/counterparties/{id}/pending` with HMAC-authenticated GET, returns queued unacked emissions from a
  per-counterparty ring buffer.
- `strategy-service/strategy_service/signal_broadcast/audit.py` — `SignalBroadcastAuditLogger`. Thin wrapper around
  `log_event("STRATEGY_SIGNAL_EMITTED_EXTERNAL", ...)` and `log_event("STRATEGY_SIGNAL_ACKNOWLEDGED", ...)` with the UAC
  payload Pydantic models from Phase 2. Also writes BQ billing table rows via UCI (topic: `signal_broadcast_emissions`).
- `strategy-service/strategy_service/signal_broadcast/credentials.py` — `CounterpartyCredentials`. Wraps
  `ApiKeyReloader` keyed on a fabricated "venue" list equal to counterparty-ids (reuses UTL's hot-reload loop verbatim).
  Exposes `hmac_secret_for(counterparty_id) -> str`.
- `strategy-service/strategy_service/signal_broadcast/failure_isolation.py` — `@isolated_per_counterparty` decorator.
  Catches all exceptions, calls `classify_venue_error`, emits `ADAPTER_FETCH_FAILED` with counterparty/slot context,
  returns a `FailedDelivery` sentinel. Used by `WebhookTransport.deliver`.
- `strategy-service/strategy_service/signal_broadcast/rate_limiting.py` — token-bucket rate limiter, keyed by
  `(counterparty_id, strategy_id)` per D7.
- `strategy-service/strategy_service/signal_broadcast/config.py` — typed `SignalBroadcastConfig` BaseModel (max retries,
  backoff base, bucket capacity, REST pull buffer size). Sourced via `UnifiedCloudConfig`.
- `strategy-service/tests/unit/signal_broadcast/test_emitter.py` — unit tests for the emit loop + allowlist gate.
- `strategy-service/tests/unit/signal_broadcast/test_router.py` — entitlement routing tests.
- `strategy-service/tests/unit/signal_broadcast/test_transport.py` — `responses`-library mocked webhook retry +
  idempotency; HMAC signature verification.
- `strategy-service/tests/unit/signal_broadcast/test_failure_isolation.py` — ensures raising counterparties do NOT
  propagate out of the emitter.
- `strategy-service/tests/integration/signal_broadcast/test_end_to_end.py` — full cycle: `STRATEGY_SIGNAL_GENERATED` →
  emit → mock counterparty → ack → BQ row.

**EDIT:**

- `strategy-service/strategy_service/__main__.py` — wire `SignalBroadcaster` into service startup alongside the existing
  `BroadcastSink`. Register `CounterpartyCredentials.start()` ApiKeyReloader loop.
- `strategy-service/strategy_service/api/main.py:30-54` — mount the `RestPullEndpoint` FastAPI sub-router alongside the
  existing health + SSE routers. No changes to existing routers.
- `strategy-service/strategy_service/config.py` — add `signal_broadcast: SignalBroadcastConfig` field to the service
  config (typed, per SERVICE_INFRA STEP 5.34).
- `strategy-service/strategy_service/config_reloaders.py` — register
  `start_signal_broadcast_config_reloader(service_config)` per typed-reloader pattern (`config-reloader-pattern.md`).
- `strategy-service/strategy_service/adapters/broadcast_sink.py:15-31` — ADD comment cross-reference to the new
  `signal_broadcast/` sub-package clarifying: `BroadcastSink` is internal Pub/Sub+SSE; external counterparty emission is
  a distinct pathway. No code change, just a docstring pointer.
- `strategy-service/strategy_service/engine/core/signal_publisher.py:192-193` — after the existing
  `log_event("SIGNAL_GENERATED", ...)`, hand off the `_signal_details` dict to `SignalBroadcaster.on_signal_generated()`
  via a thin bridge (constructor-injected). The broadcaster runs downstream in its own thread; this call is non-blocking
  per D10.
- `strategy-service/pyproject.toml` — ensure no new dependency groups added (flat deps). `cryptography` and `httpx` are
  already transitive via UTL — confirm, otherwise add to root `[project.dependencies]`.

**REFERENCES (no change):**

- `strategy-service/strategy_service/adapters/broadcast_sink.py` — internal BroadcastSink pattern; peer to new emitter.
- `strategy-service/strategy_service/adapters/signal_hub.py` — SSE fan-out peer; unaffected.
- `strategy-service/strategy_service/portfolio_allocator/service.py` — allocator pathway; unaffected (no capital flows
  in signal leasing).
- `strategy-service/strategy_service/engine/core/signal_publisher.py:111` — the class we bridge from.
- `strategy-service/tests/integration/test_strategy_cascade_events.py` — existing cascade test; should be extended later
  to assert new event NOT emitted for non-leased strategies.

### 4. execution-service

Per D10 + plan §"execution-service: minor — ensure execution events for Odum-operated strategies don't leak if the
strategy is also leased externally; emission happens BEFORE execution, not instead."

**CREATE:** (none)

**EDIT:**

- `execution-service/execution_service/README.md` (or equivalent top-of-package docstring) — add one-paragraph
  cross-reference clarifying: signal emission to counterparties happens upstream in strategy-service; execution
  observers of `STRATEGY_SIGNAL_GENERATED` must not also consume `STRATEGY_SIGNAL_EMITTED_EXTERNAL` (it is a
  broadcast-audit event, not a new trigger).

**REFERENCES (no change, validate invariants):**

- `execution-service/execution_service/engine/transfers/live_ccxt_adapter.py` — confirmed uses `ApiKeyReloader` (pattern
  we copy in strategy-service `signal_broadcast/credentials.py`).
- `execution-service/execution_service/compliance/compliance_reporter.py` — uses "counterparty" in the regulatory MiFID
  reporting sense (venue-side). Different meaning from D9 domain entity. No namespace collision because our new type is
  `Counterparty` under `unified_api_contracts.signal_broadcast`, whereas the MiFID usage is inline parameter naming.
  **Flag for Phase 6 docs**: cross-reference both usages to disambiguate.
- `execution-service/execution_service/compliance/mifid_reporter.py` — same as above.
- No Pub/Sub topic name collision check needed; signal_broadcast emits to the new `signal_broadcast_emissions` topic
  (phase 4 provisions). execution-service consumes `trade_alerts` which is distinct.

### 5. deployment-service

**CREATE:**

- `deployment-service/scripts/provision/provision-counterparty-secrets.sh` — helper that creates per-counterparty HMAC
  secret in GCP Secret Manager under `counterparty-hmac-secret-{counterparty_id}` (matches
  `/codex/07-security/secret-naming-convention.md`). Idempotent.
- `deployment-service/scripts/provision/provision-counterparty-secrets.py` — Python variant for CI/CD. Reads from
  `counterparty-bootstrap.yaml` config.
- `deployment-service/configs/counterparty-bootstrap.yaml` — seed data for the 2 Sept-2026 launch counterparties.
  Placeholder endpoints; real values injected by ops pre-go-live.
- `deployment-service/tests/unit/test_counterparty_secret_provisioning.py` — tests that the script creates the correct
  secret names + grants the strategy-service IAM role access.

**EDIT:**

- `deployment-service/deployment_service/services/` — **no new service file needed**. Signal-broadcast runs inside the
  existing strategy-service Cloud Run process (D1 decision). Confirm strategy-service service config in
  `deployment-service/configs/clusters/*.yaml` allocates enough memory for the extra goroutine-equivalent work (bump
  `memory_mb` by ~128).
- `deployment-service/configs/clusters/*.yaml` — for each cluster that runs strategy-service, ensure the new Pub/Sub
  topic `signal_broadcast_emissions` is declared in `pubsub_topics`.
- `deployment-service/terraform/gcp/main.tf` (or relevant module) — declare the new Pub/Sub topic + per-counterparty
  secret IAM bindings (read access for strategy-service service account only).
- `deployment-service/scripts/sync/sync-secrets.py` — add `counterparty-hmac-secret-*` glob to the list of secret name
  patterns the diff/sync script recognises. Reference line: `:1-80`.
- `deployment-service/scripts/vm/create-code-tarballs.sh` — confirm strategy-service tarball pulls the new
  `strategy_service/signal_broadcast/` sub-package (it will, because the tarball follows the whole `strategy_service/`
  tree).

**REFERENCES (no change):**

- `deployment-service/functions/rotate-exchange-keys/main.py` — secret rotation precedent. New counterparty secrets
  follow the same rotation policy (90-day rotation via Cloud Scheduler).
- `deployment-service/scripts/bootstrap/bootstrap_gcp.sh` — must be run with updated Terraform to provision the new
  secrets + topic before Phase 4 smoke test.
- `deployment-service/terraform/gcp/secret_rotation.tf` — existing rotation policy template.

### 6. unified-trading-system-ui

**CREATE:**

- `unified-trading-system-ui/app/(platform)/services/signals/counterparties/page.tsx` — admin surface listing
  counterparties, emission state toggles, entitlement matrix (slot × counterparty). Route under
  `/services/signals/ counterparties`.
- `unified-trading-system-ui/app/(platform)/services/signals/counterparties/[counterpartyId]/page.tsx` —
  per-counterparty detail page: delivery health panel, signal history table, entitlement editor.
- `unified-trading-system-ui/app/(platform)/services/signals/page.tsx` — landing index for the admin surface.
- `unified-trading-system-ui/app/(platform)/services/signals/dashboard/page.tsx` — counterparty observability UI (light
  dashboard per plan §Phase 5). Tenant-scoped via `audience-from-persona.ts`. Four panels: `<SignalHistoryTable>`,
  `<BacktestComparisonPanel>`, `<DeliveryHealthPanel>`, `<PnlAttributionPanel>` (optional).
- `unified-trading-system-ui/components/signals/signal-history-table.tsx` — table listing last N emissions scoped to
  entitled slots; filters by slot / date / status.
- `unified-trading-system-ui/components/signals/backtest-comparison-panel.tsx` — Odum-held backtest numbers vs live
  signal aggregate; read-only.
- `unified-trading-system-ui/components/signals/delivery-health-panel.tsx` — webhook success rate, retry counts, avg
  latency, last-delivery timestamp per slot.
- `unified-trading-system-ui/components/signals/pnl-attribution-panel.tsx` — optional P&L panel; renders only when
  counterparty has self-reported P&L in the mock fixture.
- `unified-trading-system-ui/components/signals/counterparty-admin-table.tsx` — admin list view.
- `unified-trading-system-ui/lib/signals/counterparty-types.ts` — TS mirror of UAC `Counterparty` +
  `CounterpartyEntitlement` + `SchemaDepth`. Mirror pattern matches `lib/architecture-v2/availability.ts` (Phase 10
  precedent).
- `unified-trading-system-ui/lib/mocks/fixtures/signal-broadcast.ts` — mock counterparties + mock emissions + mock ack
  history. Consumed when `VITE_MOCK_API=true`.
- `unified-trading-system-ui/tests/unit/signals/counterparty-types.test.ts` — type-mirror parity test.
- `unified-trading-system-ui/tests/e2e/signals-counterparty-admin.spec.ts` — Playwright spec for admin surface.

**EDIT:**

- `unified-trading-system-ui/components/shell/nav-copy.ts` — add `"Signals"` entry to platform nav (admin-role only). Do
  NOT duplicate the existing public `/signals` marketing entry.
- `unified-trading-system-ui/lib/auth/audience-from-persona.ts` — extend `audienceForPersonaId` to recognise a new
  `"signal-lease-counterparty"` persona id → maps to a new `"signal_lease_counterparty"` Audience value. Per D9
  (counterparty as new domain entity) this is distinct from `trading_platform_subscriber`.
- `unified-trading-system-ui/lib/auth/personas.ts:16` — add `signal-lease-counterparty-*` personas ONLY in demo mode
  (prod counterparties are API-key-authenticated domain entities, NOT user-logins). Per D9 clarification in plan §Phase
  5 ("Counterparty persona (new domain entity per D9) integration — tenant-scoped auth for the observability UI").
- `unified-trading-system-ui/lib/auth/types.ts` — add `"signal_lease_counterparty"` to the `Audience` union.
- `unified-trading-system-ui/app/(platform)/investor-relations/board-presentation/components/board-presentation-data.ts`
  — update slide 8 Signal Leasing entry to reflect Sept 2026 go-live + $5k/mo + 2 counterparties (Phase 7).
- `unified-trading-system-ui/app/(platform)/investor-relations/plan-presentation/data.ts` — update slide 9 signal
  leasing detail similarly (Phase 7).
- `unified-trading-system-ui/public/signals.html` — add a small "Admin & observability surfaces" teaser linking to
  `/services/signals` (admin) + `/services/signals/dashboard` (counterparty observability) — rendered only for
  authenticated Odum roles.
- `unified-trading-system-ui/lib/registry/ui-reference-data.json` — add `signal_broadcast` section with event names +
  mock counterparty ids (used by ops event-stream viewer).
- `unified-trading-system-ui/components/ops/event-stream-viewer.tsx` — extend known-events list to render the 2 new UTL
  events (`STRATEGY_SIGNAL_EMITTED_EXTERNAL`, `STRATEGY_SIGNAL_ACKNOWLEDGED`) with appropriate styling.
- `unified-trading-system-ui/lib/mocks/fixtures/ops-event-stream.ts` — seed mock events with the 2 new event names.

**REFERENCES (no change, depend on):**

- `app/(public)/signals/page.tsx` + `public/signals.html` — already shipped 2026-04-20; Phase 5 public work done.
- `components/marketing/marketing-static-from-file.tsx` — marketing renderer; unchanged.
- `lib/auth/audience-from-persona.ts:2-27` — audience gating doc; the new `signal_lease_counterparty` audience reuses
  this mechanism.
- `lib/architecture-v2/availability.ts` — TS mirror pattern; `lib/signals/counterparty-types.ts` copies its shape.

### 7. unified-trading-pm (codex docs + cursor rules)

**CREATE:**

- `unified-trading-pm/codex/14-playbooks/shared-core/signal-broadcast-architecture.md` — new SSOT doc: implementation
  map, D1-D10 resolutions, HMAC signing format, idempotency contract, failure-isolation pattern, auth model,
  per-counterparty rate-limit table, schema-depth payload shapes.
- `unified-trading-pm/codex/04-architecture/signal-broadcast-topology.md` — cross-link into 04-architecture for
  service-topology discovery: shows strategy-service → WebhookTransport → counterparty, SSOT for topic/secret naming.
- `unified-trading-pm/codex/07-security/signal-broadcast-credentials.md` — counterparty-credential lifecycle:
  provisioning, rotation, revocation, HMAC signature spec.
- `unified-trading-pm/scripts/propagation/rollout-counterparty-registry.sh` — optional helper (defer to follow-up) for
  propagating `COUNTERPARTY_REGISTRY` seed data.

**EDIT:**

- `unified-trading-pm/codex/00-SSOT-INDEX.md` — add rows for `signal_broadcast/` UAC sub-package,
  `signal-broadcast-architecture.md`, `signal-broadcast-topology.md`, `signal-broadcast-credentials.md`. Insert
  alphabetically near "Security + secrets patterns" row (line ~37-44).
- `unified-trading-pm/codex/14-playbooks/commercial-model/signal-leasing.md` — already references the plan (line
  148-150). Add cross-reference to the new `shared-core/signal-broadcast-architecture.md` doc (Phase 6).
- `unified-trading-pm/codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md` — brief note that Signal Leasing's
  backend is tracked in `signal-broadcast-architecture.md` (Phase 6 task).
- `unified-trading-pm/codex/14-playbooks/commercial-model/revenue-projection-2026-monthly.md` — Phase 7 number updates
  (Sept-Dec signal leasing $5k/mo).
- `unified-trading-pm/codex/14-playbooks/commercial-model/cash-deployment-plan.md` — Phase 7 minor year-end cash
  revision (£464k → £429k).
- `unified-trading-pm/codex/14-playbooks/commercial-model/pricing-building-blocks.md` — add signal-leasing rows with
  Sept 2026 anchor.
- `unified-trading-pm/cursor-configs/CLAUDE.md` — add Key Rule: "Strategy-service external signal emission MUST use
  shard-level failure isolation + classify_venue_error() pattern; counterparty credentials via ApiKeyReloader; never
  block strategy-service on counterparty endpoint failure (D10)."
- `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — same addition.
- Workspace root `/Users/ikennaigboaka/Code/unified-trading-system-repos/.claude/CLAUDE.md` (if editable) — same
  addition (note: this is a symlink / copy managed via the cursor-configs canonical path).
- `unified-trading-pm/cursor-rules/adapters/` — optional new cursor rule `signal-broadcast-failure-isolation.mdc` if
  plan §Phase 6 decides it's worth its own rule file. Recommendation per plan: likely skip (already covered by existing
  adapter-error-classification rule).
- `unified-trading-pm/plans/active/signal_leasing_broadcast_architecture_2026_04_20.md` — tick Phase 1 box
  - reference this manifest (done in Phase 1 wrap-up commit).
- `unified-trading-pm/plans/active/path_to_100m_finalization_2026_04_20.md` — tick linked phase if any references signal
  leasing backend enablement.
- `unified-trading-pm/codex/14-playbooks/roadmap/plan-references.md` — add this plan to the roadmap index.

**REFERENCES (no change):**

- `/codex/04-architecture/shard-level-failure-isolation.md` — D10 anchor.
- `/codex/04-architecture/interface-credential-convention.md` — D3 anchor.
- `/codex/06-coding-standards/config-reloader-pattern.md` — typed config reloader anchor.
- `/codex/07-security/secret-naming-convention.md` — counterparty secret naming authority.
- `/codex/07-security/secret-rotation.md` — 90-day rotation policy inherited.
- `/codex/07-security/service-to-service-auth.md` — auth design anchor for counterparty HMAC.

### 8. Memory

(`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/`)

**CREATE:**

- `project_signal_leasing_broadcast_architecture_2026_04_20.md` — project memory entry capturing D1-D10, per-repo
  ownership, go-live anchor, follow-ups, cross-repo commit SHAs (populated at Phase 8 handoff).

**EDIT:**

- `MEMORY.md` — add a one-line top-level index entry for the new memory file. Do NOT repeat details in MEMORY.md; all
  details live in the topic file.

**REFERENCES (no change):**

- Existing memory files: `audit-remediation-agents-2026-03-07.md`, `defi_backend_implementation_2026_03_30b.md`.
- Path-to-$100M memory entry (in MEMORY.md) — cross-reference, no update.

## Cross-repo invariants

- **D10 shard-level-failure-isolation** — anchor file
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/codex/04-architecture/shard-level-failure-isolation.md:40-56`.
  Phase 3's `failure_isolation.py` must literally mirror the
  `for … try/except … log_event("VENUE_PROCESSING_FAILED", …)` pattern, substituting `COUNTERPARTY_DELIVERY_FAILED`
  (mapped via `classify_venue_error` and emitted as `ADAPTER_FETCH_FAILED` per existing adapter rule).
- **D3 HMAC signing** — no pre-existing HMAC helper in any service repo. Place in UTL
  `unified_trading_library/signal_broadcast/hmac_signing.py` (shared library location per system-first rule). stdlib
  `hmac` + `cryptography.hazmat.primitives.hmac` are both in `.venv-workspace`; prefer `cryptography` for constant-time
  verification.
- **UAC Citadel Import Rules** — all 6 new symbols must be importable via
  `from unified_api_contracts.signal_broadcast import ...` (root facade) AND
  `from unified_api_contracts.internal import ...` (internal surface). No consumer repo may reach into
  `unified_api_contracts.internal.domain.signal_broadcast.*` directly.
- **Flat deps only** — none of the new sub-packages introduce `[project.optional-dependencies]`. `cryptography` and
  `httpx` are already top-level deps of UTL / strategy-service (verify during Phase 2).
- **Dockerfile convention** — no new Dockerfile needed (strategy-service's existing Dockerfile picks up the new
  sub-package). If any new Cloud Run service is introduced later (not in this plan), it MUST use `ARG PROJECT_ID` +
  `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`.
- **Schema provenance (QG-enforced)** — `Counterparty`, `CounterpartyEntitlement`, `SchemaDepth`,
  `SignalEmissionPayload`, `SignalAcknowledgementPayload` MUST live in UAC. strategy-service may only construct
  instances + pass them; no local BaseModel/dataclass re-declaration.
- **`ApiKeyReloader` reuse (D3)** — strategy-service `signal_broadcast/credentials.py` MUST use `ApiKeyReloader`
  directly. Do NOT write a one-shot secret fetch (QG-enforced since 2026-03-24).
- **ServiceBootstrap + Health API (QG-enforced)** — strategy-service already has both. New sub-package rides on them; no
  new `ServiceBootstrap(...)` call (would duplicate lifecycle emissions).
- **Typed config reloader (QG-enforced)** —
  `start_signal_broadcast_config_reloader(service_config: StrategyServiceConfig)` must use the typed-config variant,
  never `getattr(service_config, ...)` or `object` type.
- **No duplicate "counterparty" naming** — execution-service's `compliance_reporter.py` and `mifid_reporter.py` already
  use the word "counterparty" in the MiFID regulatory sense (venue-side). Our new `Counterparty` UAC entity is
  semantically distinct. The disambiguation note in `signal-broadcast-architecture.md` must spell this out explicitly to
  prevent confusion.
- **Format-string safety** — all `log_event` calls in new code pass `details=dict(...)`; never f-string/concatenate
  error messages into the event name.
- **No `os.getenv`** — all config via `UnifiedCloudConfig`; counterparty endpoints via `COUNTERPARTY_REGISTRY` (UAC),
  not env vars.
- **Batch = Live** — the signal-broadcast emitter MUST run in both modes (batch mode emits historical signals to a mock
  counterparty sink; live mode emits to the real counterparty endpoint). The code path is identical; only the
  `WebhookTransport` target URL differs.

## Parallelization strategy for Phases 2-10

```
Phase 1 (manifest) ─── DONE (this document)
                            │
                            ▼
               ┌──────────── Phase 2 (UAC + UTL contracts) ────────────┐
               │  2a: UAC signal_broadcast domain + facade              │  SEQUENTIAL gate
               │  2b: UTL events + HMAC utility      } PARALLEL to 2a   │  → QG both repos
               └────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌─────────── Phase 3 (strategy-service) ───────────┐
         │  emitter + router + transport + audit +          │  depends on Phase 2
         │  credentials + failure_isolation + rate_limit +  │
         │  config + tests                                  │
         └──────────────────────────────────────────────────┘
                            │
                            ▼
         ┌─────────── Phase 4 (deployment-service) ─────────┐  depends on Phase 3
         │  secrets + pubsub topic + terraform +            │  (same-repo QG)
         │  provisioning scripts                            │
         └──────────────────────────────────────────────────┘
                            │
                            ├──── Phase 5 (UI)       } PARALLELIZABLE after Phase 3
                            │     admin + dashboard + personas + nav + tests
                            │
                            ├──── Phase 6 (codex docs) } PARALLELIZABLE after Phase 3
                            │     shared-core + 04-arch + 07-security +
                            │     SSOT-INDEX + CLAUDE.md + cursor rules + memory
                            │
                            ├──── Phase 7 (presentations) } PARALLELIZABLE after Phase 5 starts
                            │     board-presentation-data.ts + plan data.ts +
                            │     revenue-projection + cash-deployment
                            │
                            ▼
               Phase 8 (QG + integration test + handoff) — SEQUENTIAL FINAL GATE
```

**Parallelizable groups:**

- **Group A (after Phase 1):** UAC work + UTL work can proceed concurrently because they share no files; UTL test lock
  file depends on UAC only for type imports, wait to add the lock test until after UAC facade is merged.
- **Group B (after Phase 3):** Phase 5 UI + Phase 6 docs + Phase 7 decks can all proceed in parallel — they touch
  different repos entirely.
- **Sequential bottleneck:** Phase 2 → Phase 3 → Phase 4 is strictly linear (UAC contracts must exist before
  strategy-service imports them; secrets must exist before smoke test).

**Commit order constraint:** When PR-ing, UAC commits first (downstream pulls), then UTL (strategy-service downstream),
then strategy-service, then deployment-service. This matches the workspace DAG.

## Blast-radius count

|                        | UAC | UTL | strategy-service | execution-service | deployment-service | UI  | PM  | Memory | **Total** |
| ---------------------- | --- | --- | ---------------- | ----------------- | ------------------ | --- | --- | ------ | --------- |
| Files to CREATE        | 10  | 4   | 13               | 0                 | 4                  | 14  | 4   | 1      | **50**    |
| Files to EDIT          | 3   | 5   | 7                | 1                 | 5                  | 11  | 13  | 1      | **46**    |
| References (no change) | 5   | 4   | 5                | 3                 | 3                  | 4   | 6   | 2      | **32**    |

- **Total files touched: ~96** across 8 repos (50 create + 46 edit).
- **Cross-repo symbol moves: 0** — all new symbols are net-new; no existing symbols are renamed or relocated.
- **New UTL events: 2** — `STRATEGY_SIGNAL_EMITTED_EXTERNAL`, `STRATEGY_SIGNAL_ACKNOWLEDGED`.
- **New UAC domain entities: 5** — `Counterparty`, `CounterpartyEntitlement`, `SchemaDepth`, `SignalEmissionPayload`,
  `SignalAcknowledgementPayload`.
- **New Pub/Sub topics: 1** — `signal_broadcast_emissions` (+ per-counterparty webhook endpoints as runtime config).
- **New Secret Manager entries: 2** (at launch) — `counterparty-hmac-secret-{cp1_id}`,
  `counterparty-hmac-secret-{cp2_id}` (grows with counterparty count).
- **New UI routes: 4** — `/services/signals`, `/services/signals/counterparties`,
  `/services/signals/counterparties/[id]`, `/services/signals/dashboard`.
- **Deleted files: 0** (no cleanup — signal broadcast is net-new capability).

## High-surprise findings

1. **`SignalPublisher` in strategy-service already emits `SIGNAL_GENERATED`** (not `STRATEGY_SIGNAL_GENERATED`) at
   `strategy-service/strategy_service/engine/core/signal_publisher.py:192`. The UTL constant `STRATEGY_SIGNAL_GENERATED`
   exists (`event_types.py:295`) and is used in tests. Phase 3 bridge should tap into the MiFID `SIGNAL_GENERATED` path
   (the richer one) — Phase 3 will need to confirm which event the emitter subscribes to; may need to standardise both
   into `STRATEGY_SIGNAL_GENERATED` as cleanup. **Minor follow-up hazard, not a blocker.**
2. **`BroadcastSink` at `strategy-service/strategy_service/adapters/broadcast_sink.py` already exists as an internal
   Pub/Sub + SSE fan-out.** The plan's `SignalBroadcaster` is NOT a replacement — it runs in parallel with a different
   target audience (external counterparties, not internal consumers). Plan and docs must make this explicit to avoid
   confusion.
3. **`counterparty` token collides semantically with execution-service MiFID reporting usage** — both
   `execution_service/compliance/compliance_reporter.py` and `mifid_reporter.py` use "counterparty" in the regulatory
   sense (venue-side). Our D9 domain entity is distinct. Codex doc must disambiguate; no code-level namespace collision
   (different packages).
4. **No pre-existing HMAC helper anywhere in the workspace** (only stdlib + `cryptography` library). D3 signing is
   net-new utility code placed in UTL.
5. **`archive/unified-events-interface/` references `counterparty` in an archived schemas.py** — excluded from scan
   (archived). Just noting for completeness.
6. **`api-football/normalize.py` uses `shard`-pattern unrelated to signal broadcast** — false positive during grep.
   Ignored.

## D1-D10 issues surfaced post-scan

None — all 10 decisions remain sound after seeing the code:

- **D1 confirmed** — `strategy-service/strategy_service/adapters/` already hosts analogous emission code; adding
  `signal_broadcast/` alongside is the clean pattern.
- **D2 confirmed** — strategy-service already exposes FastAPI (`api/main.py`); adding a REST-pull sub-router is trivial.
- **D3 confirmed** — `ApiKeyReloader` exists and is QG-enforced for secret fetching; this is the only compliant pattern.
- **D4 confirmed** — UAC registry has precedents (`STRATEGY_AVAILABILITY_REGISTRY`, `COUNTERPARTY_REGISTRY` follows
  verbatim).
- **D5 confirmed** — no transactional-outbox machinery exists in the workspace to support exactly-once; would require
  new infra. At-least-once + idempotency is correct.
- **D6 confirmed** — 2-event pattern matches existing `STRATEGY_SIGNAL_GENERATED` + downstream events' shape.
- **D7 confirmed** — no existing rate-limiter granularity to conflict with; token-bucket per `(counterparty, strategy)`
  is clean.
- **D8 confirmed** — `SchemaDepth` StrEnum follows `StrategyMaturity` / `LockState` precedents
  (`strategy_availability.py:46`).
- **D9 confirmed** — `ClientDefinition` / `ClientRegistry` already exist in UAC (`client_registry.py`); new
  `Counterparty` / `COUNTERPARTY_REGISTRY` in the signal_broadcast sub-package is a clean sibling.
- **D10 confirmed** — `shard-level-failure-isolation.md` pattern is well-established and applies identically to
  counterparty-endpoint failures.

## Success gate for Phase 1

- [x] Pre-audit manifest committed (this file).
- [x] No naming collisions found beyond the benign MiFID `counterparty` usage (documented above).
- [x] Reusable patterns identified: `ApiKeyReloader` (D3), `classify_venue_error` + shard-isolation (D10),
      `ServiceBootstrap` + `make_health_router` (service infra), `strategy.py` facade (UAC layout), `StrategyMaturity`
      StrEnum (D8), `BroadcastSink` (peer pattern for new emitter).
- [x] All D1-D10 decisions validated against the code — no revisions needed.

Phase 1 complete. Proceed to Phase 2 (UAC + UTL contracts) in parallel-group-A mode.
