---
name: per-client-isolation-preaudit-2026-05-20
title: Pre-audit — per-client subprocess isolation (Group H, Phase 0)
created: 2026-05-20
author: slot-4 (ikenna)
status: complete
parent_plan: per_client_isolation_and_venue_fanout_topology_2026_05_20.md
---

# Per-Client Isolation Pre-Audit — 2026-05-20

Phase 0 read-only audit for
[`per_client_isolation_and_venue_fanout_topology_2026_05_20.md`](../per_client_isolation_and_venue_fanout_topology_2026_05_20.md).
Produces the enumeration required to drive Phase 1 (UAC contracts) and Phase 3 (StrategySupervisor concrete impl).

---

## (a) Single-tenant assumptions in strategy-service

Every location that assumes one client per process — must be refactored for per-ClientWorker subprocess isolation.

### A.1 — DomainEventLogger singleton (CRITICAL)

**File**: `strategy_service/engine/infrastructure/logging/domain_event_logger.py`

- Lines 53–58: Class-level `_instance` implementing `__new__` singleton pattern
- Line 82: stores `client_name` at construction time
- Lines 89–91: `_global_order`, `_order_lock`, `_sync_order_lock` are shared across the singleton — if two ClientWorkers
  ran in the same process, order numbering and log routing would collide.

**Disposition**: Each ClientWorker subprocess gets its own Python interpreter → singleton is per-subprocess by default.
No code change required for Phase 3. Document invariant in codex.

### A.2 — `_get_service_auth_token()` @lru_cache (HIGH)

**File**: `strategy_service/risk/auth_s2s.py`

- Lines 30–31: `@lru_cache(maxsize=1)` caches a single auth token for the entire process.
- Token is keyed on `UnifiedCloudConfig().service_auth_token` — per-service, not per-client.

**Disposition**: Per-subprocess isolation resolves this (each subprocess has its own cache). No change for Phase 3.
Verify in Phase 7 tests.

### A.3 — `_get_expected_api_key()` @lru_cache (HIGH)

**File**: `strategy_service/risk/api/main.py`

- Lines 64–65: `@lru_cache(maxsize=1)` on `_get_expected_api_key()`
- Line 67–68: loads `get_service_config()` → secret name `"risk-api-key-{environment}"` with no per-client variant.

**Disposition**: Risk API key is service-level (not client-level) so shared caching is correct. No change needed.

### A.4 — `_gas_fee_df_cache` module-level global (HIGH)

**File**: `strategy_service/pnl/engine/pnl_input_builder.py`

- Line 23: `_gas_fee_df_cache: dict[str, pd.DataFrame] = {}` — keyed by `chain_id`, no `client_id` dimension.
- Lines 41–42: cache written at module import time.

**Disposition**: Gas fee data is chain-level, not client-level. Cache key (`chain_id`) does not leak client state.
Per-subprocess isolation means each ClientWorker has its own module-level dict — no cross-client collision. No change
required.

### A.5 — `StrategyServiceConfig` module-level singleton (HIGH)

**File**: `strategy_service/config.py`

- Line 505: `_config: StrategyServiceConfig | None = None`
- Lines 508–513: `get_config()` returns the process-wide singleton.

**Disposition**: StrategySupervisor reads config once at boot and passes archetype/shard config to each ClientWorker via
subprocess startup args. Each ClientWorker subprocess has its own `_config` module global. No cross-client collision in
subprocess model. No change required for Phase 3.

### A.6 — `config_reloaders.py` module-level singletons (HIGH)

**File**: `strategy_service/config_reloaders.py`

- Lines 30–31: `_strategy_reloader`, `_instrument_reloader` — module-level
- Lines 34–35: `_active_strategy_config`, `_active_instruments` — atomic swap globals shared across all callers
  in-process.

**Disposition**: These live in the StrategySupervisor parent process and feed the `MarkPriceAggregator`. ClientWorkers
receive config snapshots via shared memory at startup; hot-reloads are pushed via `CREDENTIAL_ROTATED` events per
Phase 5. **Phase 3 action**: StrategySupervisor owns the reloader; ClientWorker reads from shared memory snapshot, NOT
from `config_reloaders.py` directly. Ensure Phase 4 ClientWorker does NOT import `config_reloaders.py`.

### A.7 — `ArchetypeKillSwitchSubscriber` per-client halt state (MEDIUM)

**File**: `strategy_service/archetype_kill_switch_subscriber.py`

- Lines 133–180: `_halted_archetypes` dict + `_global_behaviour` flag held in instance. If instance is shared across
  clients, a halt for client A would affect client B.

**Disposition**: StrategySupervisor in Phase 3 subscribes at supervisor level; each ClientWorker subscribes
independently in its subprocess. No shared instance across ClientWorkers. No change required at code level — isolation
is structural.

### A.8 — `KillSwitchBusSubscriber` module-level singleton (MEDIUM)

**File**: `strategy_service/kill_switch_bus_subscriber.py`

- Line 22: `_subscriber = KillSwitchBusSubscriberBase(service_log_prefix="STRATEGY")` — module-level instantiation.
- Lines 25–27: `on_bus_event()` delegates to shared `_subscriber`.
- Line 30–49: `is_blocked_by_bus()` accepts optional `client_id` parameter.

**Disposition**: Module-level instantiation runs once per subprocess. In the subprocess model, each ClientWorker imports
this module fresh → its own `_subscriber` instance. No cross-client collision. **Phase 3 action**: Document this pattern
in the ClientWorker startup doc so future engineers don't try to share the module-level instance.

---

## (b) UAC event types: current client_id coverage

### B.1 — EventMetadata has optional client_id (ALREADY PRESENT)

**File**: `unified_api_contracts/internal/events.py`

- Line 661: `client_id: str | None = Field(default=None, json_schema_extra={"pii": True})`
- All typed event wrappers inheriting `EventMetadata` already carry `client_id` as an optional field.

**Disposition**: Field exists. Phase 1 new event types (`ClientLifecycleEvent`, `ClientReadyEvent`,
`ClientQuarantinedEvent`, `ShardCapacityEvent`, `TransferIntent`, `TransferResult`) must set `client_id` as **required**
(not optional) — these are inherently per-client events.

### B.2 — Emissions lacking explicit client_id routing (TARGET)

These strategy-service emission sites emit without setting `client_id` explicitly:

- `strategy_service/engine/core/signal_publisher.py:214,225,252` — SIGNAL_GENERATED, STALE_DATA, RISK_RULE_BLOCKED
- `strategy_service/engine/core/components/pnl_residual_emitter.py:69` — UNEXPLAINED_PNL_RESIDUAL

**Phase 3 action**: StrategySupervisor spawns each ClientWorker with its `client_id` as an env arg. ClientWorker injects
`client_id` into every event emission at the UAC `EventMetadata` layer. Phase 4 (ClientWorker concrete impl) wires this
injection.

### B.3 — New UAC types required (Phase 1)

Per plan spec — all must be added to `unified_api_contracts/canonical/crosscutting/`:

| Type                     | client_id required? | Notes                                                                |
| ------------------------ | ------------------- | -------------------------------------------------------------------- |
| `ClientLifecycleEvent`   | YES                 | kind: REGISTER/DEREGISTER/QUARANTINE/UNQUARANTINE/CREDENTIAL_ROTATED |
| `ClientReadyEvent`       | YES                 | emitted by ClientWorker after preflight green                        |
| `ClientQuarantinedEvent` | YES                 | emitted on preflight failure                                         |
| `ShardCapacityEvent`     | NO                  | archetype + shard level, not per-client                              |
| `TransferIntent`         | YES                 | source_account + dest_account MUST share client_id                   |
| `TransferResult`         | YES                 | matches TransferIntent.idempotency_key                               |

---

## (c) Kill-switch event subscribers requiring ClientLifecycleEvent equivalent

### C.1 — `ArchetypeKillSwitchSubscriber`

**File**: `strategy_service/archetype_kill_switch_subscriber.py:133–180`

- Subscribes to `KillSwitchArmedEvent` / `KillSwitchDisarmEvent`
- Currently no per-client kill-switch — halting archetype halts ALL clients on that archetype VM.

**Phase 3 action**: `ClientLifecycleEvent.kind=QUARANTINE` is the per-client equivalent. StrategySupervisor translates
`QUARANTINE` events into targeted ClientWorker termination without affecting other ClientWorkers on the same archetype
VM.

### C.2 — `KillSwitchBusSubscriber` module

**File**: `strategy_service/kill_switch_bus_subscriber.py:22–49`

- Module-level `_subscriber` wraps `KillSwitchBusSubscriberBase`
- `is_blocked_by_bus(client_id=...)` already has per-client parameter path

**Phase 3 action**: Verify `KillSwitchBusSubscriberBase.is_blocked(client_id)` in UTL handles per-client routing
correctly. If not, Phase 2 (UTL bases) `ClientLifecycleBusSubscriberBase` resolves this via its own subscription
surface.

---

## (d) `colocated_engine.py` cross-process boundaries

**File**: `e2e-testing/scripts/defi/colocated_engine.py`

**Finding**: No `subprocess.Popen`, `multiprocessing`, `Queue`, `Pipe`, or `shared_memory` in colocated_engine.py.
Architecture is explicitly single-process co-location:

- All ring services (strategy → execution → position → pnl → risk) imported directly into one Python process (sys.path
  injection at lines 65–80)
- `SharedState` class (lines 187–246): in-memory state, all services share heap
- `GcsEventSink` (lines 51–56): async background publishing (not multiprocess)

**Phase 3/4 implication**: colocated_engine.py is a test/e2e harness, not the production code path. For May-23 live
launch, each ClientWorker subprocess IS the colocated engine for its client. The e2e-testing harness needs a separate
test that spins up 2 ClientWorker subprocesses (via StrategySupervisor) and validates crash isolation — that is Phase 7
scope.

**Phase 7 action**: Add `e2e-testing/tests/integration/test_two_client_subprocess_isolation.py` that spawns 2
ClientWorkers via StrategySupervisor and validates:

1. Crash in one ClientWorker (deliberate SIGKILL) does not terminate the other.
2. MarkPriceAggregator shared memory reads remain consistent for surviving client.
3. Supervisor restarts crashed client within exponential backoff window.

---

## (e) Execution-service `isolation_policy.py` — assert_client_allowed coverage

**File**: `execution_service/isolation_policy.py:79–94`

- `assert_client_allowed(client_id: str | None)` correctly raises `CrossClientEventError` when
  `client_id != _cached_client_id` for ISOLATED policy.
- `load_client_venue_credentials(venue)` correctly scopes to per-client Secret Manager path
  `clients/<client_id>/<venue>/api_key`.

**Coverage gap**: `assert_client_allowed` is called from only ONE location:

- `execution_service/engine/modes/live/trigger.py:34`

**Missing coverage** (not yet calling `assert_client_allowed`):

- `execution_service/trade_execution/ws_feeds.py` — event bus subscriber
- `execution_service/engine/connectivity_gap_bridge.py` — event consumer
- All `venue` classes in `execution_service/venues/` — may consume events

**Disposition**: This is a **Phase 6 scope item** (execution-service docs + wiring). Slot 7 owns Phase 6. Flag here for
slot 7: add `assert_client_allowed()` to ALL event-bus subscriber entry points in execution-service, not just the live
trigger.

**Verdict**: Execution-service isolation is structurally correct (one process per client_id via deployment-api fan-out),
but `assert_client_allowed` call coverage is incomplete. Defense-in-depth gap, not an architectural flaw.

---

## (f) MTM compute paths — confirmed (2026-05-20)

All 4 paths from the architecture decision table are confirmed present:

| #   | File                                                      | Line    | Compute                                              |
| --- | --------------------------------------------------------- | ------- | ---------------------------------------------------- |
| 1   | `strategy_service/pnl/engine/pnl_input_builder.py`        | 197–198 | `unrealized_pnl = net_qty × last_price - buy_val`    |
| 2   | `strategy_service/position/core/mark_price_subscriber.py` | 52      | `unrealized_pnl = (mark_price - entry_price) × qty`  |
| 3   | `strategy_service/position/core/leg_snapshot_builder.py`  | 106     | `notional = abs(position_units × mark_price)`        |
| 4   | `strategy_service/risk/core/risk_calculator.py`           | 127–129 | aggregates `position_value` (pre-MTM'd) for leverage |

**Implication confirmed**: MarkPriceAggregator must live in StrategySupervisor and broadcast via
`multiprocessing.shared_memory` to all ClientWorker subprocesses. Without shared-memory broadcast, N clients × M symbols
= N×M MTM computes per tick vs. M computes + N reads (the target).

---

## (g) Per-venue credential refresh cadence

| Venue type                         | Current cadence                                          | Source                                                                | Phase 5 KMS poll target                                                             |
| ---------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Service auth token (risk API)      | Cached at startup, no refresh                            | `risk/auth_s2s.py:30`                                                 | Not per-venue, no change                                                            |
| Strategy config / instruments      | 300s (5 min)                                             | `config_reloaders.py:225`                                             | N/A (not creds)                                                                     |
| Signal broadcast HMAC secrets      | `observability_refresh_interval_seconds` (config-driven) | `signal_broadcast/config_reloaders.py:125`                            | → `ClientCredentialKmsPoller` CEX path                                              |
| Venue API keys (execution-service) | Loaded at process start, no refresh                      | `execution_service/isolation_policy.py:load_client_venue_credentials` | Execution-service is separate per-client process; Phase 5 is strategy-service scope |

**Phase 5 KMS poll defaults** (matching plan spec):

- CEX venues (Binance, OKX, Bybit, Coinbase, Upbit): **60s** poll — frequent rotation expected
- DEX venues (Uniswap, Curve, Balancer, Hyperliquid): **300s** poll — private keys rotated less often
- Lending protocols (Aave, Morpho, Idle, Karak, Yearn, Puffer): **600s** poll — protocol auth is typically wallet-based,
  slow rotation

**Config parameter** for Phase 5: `clients.yaml` → `credential_poll_interval_seconds` per (client_id, venue). Defaults
above apply when not specified.

**`account_query_client.py` on_reload_credentials** hook:

- `strategy_service/position/core/account_query_client.py:76`: `on_reload_credentials()` hot-reload hook exists.
- Phase 5 `ClientCredentialKmsPoller` should call this hook on rotation.

---

## Summary for Phase 1 (UAC) and Phase 3 (StrategySupervisor)

### Phase 1 (slot 5) — critical inputs from this audit

1. All 6 new UAC types confirmed needed (B.3 table).
2. `TransferIntent.source_account.client_id` MUST equal `TransferIntent.dest_account.client_id` — HARD RULE per plan +
   `client-funds-isolation.md`.
3. `ShardCapacityEvent` should NOT carry `client_id` — it's archetype+shard level.
4. `ClientLifecycleEvent.kind=QUARANTINE` is the per-client kill-switch equivalent (C.1).

### Phase 3 (slot 4) — ready to implement once Phase 2 lands

Key implementation invariants from this audit:

- StrategySupervisor parent process OWNS `config_reloaders.py` singletons (A.6).
- ClientWorkers MUST NOT import `config_reloaders.py` — receive config via shared memory.
- `DomainEventLogger` singleton is safe per-subprocess — no change needed (A.1).
- `assert_client_allowed` gap in execution-service is Phase 6 scope, not Phase 3 (e).
- MarkPriceAggregator shared-memory broadcast is mandatory due to 4 confirmed MTM paths (f).
- `on_reload_credentials()` hook in `account_query_client.py:76` is the Phase 5 injection point (g).
