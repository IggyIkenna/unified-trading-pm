---
name: per-client-isolation-and-venue-fanout-topology-2026-05-20
overview:
  Wire per-client subprocess isolation into strategy-service + confirm/document the existing per-client process isolation
  in execution-service + formalise multi-venue concurrent routing through the existing OMS, by 2026-05-23 live DeFi
  launch. Operator-directed: 2 clients live on May-23 (Odum Research UK + defi-client-1). Architecture must support
  hot add/remove of clients without VM restart, hard crash isolation between clients (subprocess boundary), centralised
  MarkPriceAggregator inside the strategy-service supervisor (MTM compute audit 2026-05-20 confirmed mark-to-market
  IS local — pricing-input is upstream MTDS/MDPS, but MTM compute is in-process), and auto-shard signal to
  deployment-service when a VM saturates. Composes with the un-deferred Phase 5 UTL lifts (ConfigReloaderBase +
  KillSwitchBusSubscriberBase → extended with ClientLifecycleBusSubscriberBase). May-23 ships E.0+E.1 hard isolation
  (subprocess per client, supervisor process, hybrid push/pull hot-reload); auto-shard supervisor signal (E.2) +
  intra-client multi-portfolio / multi-wallet rebalancer (E.3) deferred post-cutover with named successor anchors in
  this plan. **HARD RULE codified by this plan: funds NEVER move between different clients.** Rebalancing scope is
  always within a single client's portfolios (groups of strategy archetypes) or across that one client's wallets /
  accounts — never client-A-to-client-B. Custody + legal boundary (each client is a separately-managed account under
  its own custody / legal entity).
type: infra
epic: master_to_live_defi_2026_05_23
status: active

asset_group: cross-cutting
priority: P0
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-20
last_updated: 2026-05-20

estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5

completion_gates:
  code: C5
  deployment: D2
  business: B1

repo_gates:
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: e2e-testing
    code: C0
    deployment: none
    business: none

depends_on:
  - strategy_repo_consolidation_2026_05_19  # Phase 5 UTL lifts must land first (ConfigReloaderBase + KillSwitchBusSubscriberBase)
  - promote_workflow_may23_cli_path_2026_05_10  # VM launcher pattern this extends

---

## Context

**Operator-direction 2026-05-20**: DeFi May-23 launch needs 2 live clients (us + defi-client-1). Strategy + execution
architecture must support adding the 2nd client without restarting strategy VMs, with hard crash isolation between
clients (so client A's bug doesn't kill clients B-E running on the same archetype VM), and a documented path to scale to
5+ clients per archetype VM with auto-shard onto additional VMs.

**Pricing audit 2026-05-20 (verdict: HAS-LOCAL-PRICING)**: strategy-service consumes mark prices from upstream MTDS/MDPS
but **performs its own MTM compute** in 4 paths:

- `strategy_service/pnl/engine/pnl_input_builder.py:197-198` — `unrealized_pnl = net_qty × last_price - buy_val`
- `strategy_service/position/core/mark_price_subscriber.py:52` — `unrealized_pnl = (mark_price - entry_price) × qty`
- `strategy_service/position/core/leg_snapshot_builder.py:106` — `notional = abs(position_units × mark_price)`
- `strategy_service/risk/core/risk_calculator.py:127-129` — aggregates `position_value` (pre-MTM'd) for leverage

Implication: per-client ClientWorkers cannot be independently pricing-naive. **MarkPriceAggregator must live in the
strategy-service supervisor** (one compute per symbol per tick), broadcast results to ClientWorkers via shared memory.
Otherwise we duplicate MTM N times per tick.

**Execution-service audit 2026-05-20**: already single-tenant per process via
`execution-service/execution_service/isolation_policy.py:1-80` (`CLIENT_ID` env var binding, `assert_client_allowed()`
cross-client reject at bus layer). OMS exists: `execution_service/trade_execution/oms/persistent_oms.py:28`
(`PersistentOrderManager` with state machine PENDING→VALIDATED→SUBMITTED→FILLED|REJECTED|CANCELLED + idempotency cache).
Multi-venue concurrent routing exists: `execution_service/engine/concurrent.py:12` (asyncio.gather two-leg) +
`algorithms/sor.py:47` (SmartOrderRouter splits across Uniswap/Curve/Balancer). **Implication**: execution-service needs
no new isolation primitive — it needs documentation of the existing pattern + verification that 1-VM-per-client scales
to 2 clients on May-23 (it does; deployment-api fans out per-process per `CLIENT_ID`).

**Transfers (audit 2026-05-20)**: currently fragmented inside execution-service:

- **CEX withdrawals**: UAC contract types re-exported in `execution_service/adapters/order_adapter.py:20-50`
  (BinanceWithdrawRequest/Response, OKX, Bybit, Coinbase, Upbit). Actual RPC lives in venue adapter packages.
- **DeFi protocol deposits/withdrawals**:
  `execution_service/defi_execution/protocols/{aave,morpho,idle,karak,yearn, puffer}.py` each with `deposit()` +
  `withdraw()` methods.
- **DeFi lending venue withdraw**: `execution_service/venues/{aave,morpho}.py`.
- **CEX↔DEX bridges**: `execution_service/defi_execution/hyperliquid_bridge.py` (deposit_usdc_to_hyperliquid,
  withdraw_usdc_from_hyperliquid).
- **Cross-chain bridges**: `execution_service/v2/handlers.py` BridgeHandler + `algo_library/intent_engine.py`
  `_decompose_bridge()`.
- **No cross-client rebalancing**: `client-reporting-api` tracks transfer history for P&L reporting but does NOT execute
  moves. Sub-account transfers (margin↔spot within one exchange) NOT FOUND in workspace.

Decision (per this plan): **transfers stay owned by execution-service** but get a unified `TransferCoordinator` facade
that strategy-service invokes via UAC `TransferIntent` events. **HARD RULE — all transfer endpoints scoped to a single
client_id; `TransferIntent.source_account` and `.dest_account` MUST belong to the same `client_id` — TransferCoordinator
REJECTS any intent where source/dest clients differ (raises `CrossClientTransferForbiddenError`). Funds never move
between different clients; only between portfolios/wallets/accounts of one client.** Intra-client multi-portfolio +
multi-wallet rebalancing is post-cutover (E.3 — named successor below). Sub-account transfers added on demand when an
archetype needs them (still intra-client).

## Architecture decision tree (operator-locked 2026-05-20)

| Axis                                        | Decision                                                                                                                                                                                                                                 | Rationale                                                                                                                                                           |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Per-VM topology (strategy-service)          | One VM per (archetype × shard). Shard 0 holds clients 0..N-1; shard 1 holds N..2N-1; auto-spawned on capacity threshold (E.2).                                                                                                           | Singleton-per-archetype already exists; adding shard suffix is mechanical. Crash isolation between archetypes preserved.                                            |
| Per-client isolation (strategy-service)     | Subprocess per client (multiprocessing.Process) under a parent StrategySupervisor. Hard crash isolation (segfault/OOM/uncaught all survived).                                                                                            | Soft isolation (asyncio task + try/except) doesn't survive segfault/OOM. Subprocess gives true parallel CPU for MTM/risk paths.                                     |
| Pricing centralisation                      | MarkPriceAggregator owned by StrategySupervisor; broadcasts per-tick computed marks to all ClientWorker subprocesses via `multiprocessing.shared_memory` (zero-copy).                                                                    | Audit 2026-05-20 confirmed MTM compute is local. One compute per symbol per tick, broadcast to N clients, not N computes.                                           |
| Hot client register/deregister              | Push via UAC `ClientLifecycleEvent` bus (extends `KillSwitchBusEvent` pattern). Supervisor subscribes.                                                                                                                                   | Low-frequency operator action; bus is the right surface; composes with Phase 5 KillSwitchBusSubscriberBase lift.                                                    |
| Hot credential rotation                     | Pull via ClientWorker poll of Cloud KMS / Secret Manager (interval per-venue configurable, default 60s).                                                                                                                                 | High-frequency automated rotation; push would couple supervisor to rotation cadence.                                                                                |
| Per-client preflight                        | ClientWorker boot: (a) load creds from KMS, (b) per-venue auth ping, (c) per-venue balance fetch, (d) emit `CLIENT_READY` event. If any step fails → emit `CLIENT_QUARANTINED` + supervisor marks worker dead; other clients unaffected. | Operator wants clients to fail in isolation without bringing down others.                                                                                           |
| Execution-service per-client                | KEEP existing: one execution-service process per client (already enforced by isolation_policy.py). Deployment-api fans out per `CLIENT_ID`.                                                                                              | Already correct; no rewrite.                                                                                                                                        |
| Multi-venue concurrency (execution-service) | KEEP existing: asyncio.gather + SmartOrderRouter. Document the contract in codex. Add per-venue circuit breaker (E.1 — see Phase 4).                                                                                                     | Current pattern is fine for May-23. Per-venue rate-limit / circuit-breaker hardening can layer on.                                                                  |
| Transfer ownership                          | execution-service owns ALL transfers (CEX withdrawals, DeFi deposit/withdraw, bridges, sub-account moves). Strategy-service emits `TransferIntent` events; execution-service consumes.                                                   | Single ownership boundary; mirrors orders pattern.                                                                                                                  |
| **Cross-client fund movement**              | **FORBIDDEN — never. HARD RULE.** TransferCoordinator rejects any intent where source_account.client_id ≠ dest_account.client_id. Custody + legal boundary.                                                                              | Each client = separately-managed account under own custody/legal entity. Cross-client moves = custody violation + regulatory breach. Not an engineering preference. |
| Intra-client rebalancing                    | Post-cutover (E.3, this plan). Two legitimate scopes only: (a) multi-portfolio (shifting allocation between archetypes for ONE client); (b) multi-wallet/account (moving between ONE client's wallets/accounts).                         | Not needed for 2-client May-23 launch; defer until concrete intra-client use case lands.                                                                            |
| GIL / true parallelism                      | Subprocess gives each ClientWorker its own GIL → true parallel CPU. Free-threading (PEP 703) explicitly NOT in scope until C-extension recompile audit.                                                                                  | Subprocess pattern is portable across Python 3.12/3.13/3.14; free-threading is a future optimisation.                                                               |

## Phased execution DAG

```
Phase 0 (pre-audit)  →  Phase 1 (UAC contracts)  →  Phase 2 (UTL bases)  →  Phase 3 (supervisor)  →  Phase 4 (ClientWorker + IPC)
                                                                                                          ↓
                                                                          Phase 7 (e2e + unit tests)  ←  Phase 5 (preflight + hot reload)  →  Phase 6 (execution-service wiring + transfer facade)
                                                                                                          ↓
                                                                                                     Phase 8 (deployment-service wiring + paper VM cutover)
                                                                                                          ↓
                                                                                                     Phase 9 (codex SSOT)
                                                                                                          ↓
                                                                                              [POST-MAY-23] Phase E.2 (auto-shard) + Phase E.3 (rebalancer)
```

todos:

- id: phase-0-pre-audit-manifest content: |
  - [x] ✅ [AGENT] P0. Phase 0 — Pre-audit manifest (read-only). Produce
        `plans/active/issues/per_client_isolation_preaudit_2026_05_20.md` enumerating: (a) every callsite in
        strategy-service that currently assumes single-tenant process (env var reads, module-level globals holding
        client state, singleton patterns) — these need ClientContext refactor in Phase 4; (b) every UAC type that
        carries (or should carry) `client_id` — current state vs target state; (c) every kill-switch event subscriber
        that needs ClientLifecycleEvent equivalent — composes with Phase 5 of strategy_repo_consolidation; (d) every
        cross-process boundary in colocated_engine.py that needs IPC replacement (shared_memory or
        multiprocessing.Queue); (e) verify execution-service `isolation_policy.py` semantics — confirm
        `assert_client_allowed` covers ALL event-bus subscribers in execution-service (grep + read every subscriber);
        (f) MTM compute paths re-verified per 2026-05-20 audit — 4 paths confirmed; capture any drift since audit; (g)
        per-venue credential refresh cadence per venue type (CEX vs DEX vs lending) — drives KMS poll interval defaults
        in Phase 5. — pm@17b75c44 + pm@68a31e04 status: done

- id: phase-1-uac-contracts content: |
  - [x] ✅ [AGENT] P0. Phase 1 — UAC contracts. Add to `unified_api_contracts/canonical/crosscutting/`: (1)
        `ClientLifecycleEvent` (StrEnum kind: REGISTER / DEREGISTER / QUARANTINE / UNQUARANTINE / CREDENTIAL_ROTATED;
        payload: client_id, archetype_id, shard_id, timestamp, reason); (2) `ClientReadyEvent` (emitted by ClientWorker
        after preflight green; client_id, archetype_id, shard_id, venue_auth_status: dict[venue, OK|FAILED|SKIPPED]);
        (3) `ClientQuarantinedEvent` (emitted on preflight failure or N restart attempts; client_id, archetype_id,
        shard_id, quarantine_reason: enum, last_error_message, retry_after_seconds); (4) `ShardCapacityEvent` (emitted
        by StrategySupervisor when occupancy ≥ threshold; archetype_id, shard_id, occupancy_pct, memory_pct, cpu_pct,
        recommended_action: SPAWN_NEW_SHARD); (5) `TransferIntent` (strategy-service → execution-service; client_id,
        transfer_type: CEX_WITHDRAW | DEFI_DEPOSIT | DEFI_WITHDRAW | BRIDGE | SUBACCOUNT_MOVE; source_venue, dest_venue,
        asset, amount, idempotency_key); (6) `TransferResult` (execution-service → strategy-service; matches
        TransferIntent.idempotency_key; status: SUBMITTED | CONFIRMED | FAILED; on-chain tx_hash or CEX withdrawal_id;
        fee, gas_used). Tests: schema-parity cassettes per UAC discipline (every commit
        `pytest tests/test_cassette_schema_parity.py`). QG: STEP 5.69 bucket-name SSOT compliant (no inline bucket
        strings in event payloads). — uac@d0f72fd (7 files, 879 insertions: client_lifecycle_events.py +
        transfer_events.py + 37 unit tests + __init__ exports + source_priority + availability_semantics fixes)
        status: done

- id: phase-2-utl-bases content: |
  - [ ] [AGENT] P0. Phase 2 — UTL bases. Add to UTL: (1)
        `unified_trading_library/lifecycle/client_lifecycle_bus_subscriber_base.py` — `ClientLifecycleBusSubscriberBase`
        EXTENDS the `KillSwitchBusSubscriberBase` lifted in Phase 5 of strategy_repo_consolidation. Same scaffold,
        different event type. Sub-classes implement `on_register(event)` / `on_deregister(event)` /
        `on_credential_rotated(event)`; (2) `unified_trading_library/lifecycle/client_credential_kms_poller.py` —
        `ClientCredentialKmsPoller`: polls Cloud KMS / Secret Manager every N seconds for credential rotation per
        (client_id, venue); emits in-process `CredentialRotatedSignal` for ClientWorker to absorb. Configurable poll
        interval per venue (CEX ~60s, DEX ~300s, lending ~600s). Uses `UnifiedCloudConfig` — never `os.getenv` per
        workspace rule; (3) `unified_trading_library/services/strategy_supervisor_base.py` — `StrategySupervisorBase`
        abstract: manages ClientWorker subprocess lifecycle (spawn, health-watch, restart with exponential backoff,
        quarantine after N restarts), shared-memory mark broadcast, capacity threshold monitoring. Sub-classes implement
        archetype-specific signal generation; (4) `unified_trading_library/services/client_worker_base.py` —
        `ClientWorkerBase` abstract: subprocess entry point, reads ClientLifecycleEvent stream, runs preflight, emits
        CLIENT_READY, consumes shared-memory marks, owns per-client state (positions, fills, PnL, risk, credentials),
        publishes TransferIntent / Order events. Sub-classes implement per-archetype trading logic. **Composes with
        Phase 5 strategy_repo_consolidation**: ConfigReloaderBase + KillSwitchBusSubscriberBase must land FIRST (slot 5
        is doing those NOW per un-defer 2026-05-20). This Phase 2 inherits from those bases. Tests: unit tests for each
        base (mock subprocess + mock event bus + mock KMS); basedpyright clean. status: pending blocked_by:
        phase-1-uac-contracts

- id: phase-3-supervisor content: |
  - [x] ✅ [AGENT] P0. Phase 3 — StrategySupervisor implementation in strategy-service. Concrete subclass of
        `StrategySupervisorBase`: (1) MarkPriceAggregator: subscribes to MTDS/MDPS mark price stream once per
        (archetype, shard); maintains shared-memory dict keyed by instrument_id, value =
        `MarkSnapshot(price, mtm_value_per_unit, timestamp,         stale_after_ms)`. ClientWorkers consume read-only
        via multiprocessing.shared_memory.SharedMemory; (2) ClientAdmissionController: subscribes to
        ClientLifecycleEvent bus; on REGISTER spawns ClientWorker subprocess, waits for CLIENT_READY (timeout
        configurable, default 30s); on DEREGISTER sends SIGTERM, waits for graceful drain (timeout 60s), reaps; on
        subprocess crash restarts with exponential backoff (1s, 2s, 4s, 8s, 16s, then QUARANTINE); (3)
        ShardCapacitySensor: polls own VM memory_pct (psutil) + cpu_pct (psutil) + event-loop-lag every 10s; when
        (memory ≥ 70% OR cpu ≥ 80% OR clients ≥ shard_capacity_max) for 3 consecutive samples, emits
        ShardCapacityEvent.SPAWN_NEW_SHARD; (4) HealthAggregator: rolls up per-ClientWorker heartbeats into one
        Health-API response served on `strategy-service/api/main.py` (extend the Phase 2 aggregated-health endpoint with
        per-client breakdown); (5) Lifecycle: starts on VM boot, registers archetype's pre-configured client list from
        `clients/<archetype>/<shard>/clients.yaml` (operator-managed; loaded at boot, hot-reloadable via
        ClientLifecycleEvent.REGISTER). Tests: unit tests with mocked subprocess + mocked shared_memory + mocked event
        bus (simulate REGISTER → spawn → READY → DEREGISTER → reap; simulate crash → restart → quarantine after 5
        attempts; simulate capacity threshold → SPAWN_NEW_SHARD emission). — strategy-service@4fb14035 + QG 82.98% coverage, 24 tests pass

- id: phase-4-client-worker-ipc content: |
  - [ ] [AGENT] P0. Phase 4 — ClientWorker subprocess + IPC wiring. Concrete subclass of `ClientWorkerBase` in
        strategy-service: (1) Subprocess entry point: spawned via `multiprocessing.get_context("spawn").Process` (spawn
        not fork — cleaner for venue-adapter HTTP clients which don't always survive fork). Receives at startup:
        client_id, archetype_id, shard_id, shared_memory_name, parent_event_pipe; (2) Per-client state owned:
        PositionStateStore (per-client UAC PositionRecord cache), ExecutionRouter (publishes Order events keyed by
        client_id; consumes Fill events filtered by client_id), PnLAttributor (per-client books), RiskGuard (per-client
        limits from clients.yaml), CredentialStore (per-client venue creds, hot-reloadable); (3) Consume shared-memory
        marks: every tick, read MarkPriceAggregator's shared dict; recompute per-position unrealized_pnl using shared
        mtm_value_per_unit × position qty (NOT the local MTM compute from current strategy-service — that compute moves
        to the aggregator); (4) IPC: parent → child = multiprocessing.Pipe (events: lifecycle, credential-rotation,
        shutdown); child → parent = same pipe (events: ready, quarantined, heartbeat, order-emitted,
        transfer-intent-emitted); (5) Refactor existing strategy-service surfaces (signal_generation, pnl, position,
        risk) to ACCEPT a ClientContext argument instead of reading process-level globals. ClientContext carries
        client_id, credentials, position cache, books, risk limits; (6) colocated_engine.py rewrite: SharedState becomes
        per-ClientWorker; the parent supervisor owns MarkPriceAggregator + EngineCtx (supervisor-level shared read-only
        config visible to all ClientWorkers in the shard — NOT cross-client fund-movement state); per-client logic moves
        into ClientWorker.run(). Tests: unit tests for ClientWorker lifecycle (start → preflight → ready →
        process-event-loop → graceful-shutdown); crash test (raise unhandled exception in worker → supervisor detects
        via pipe close → restart logic); IPC test (parent emits credential-rotation → worker reloads CredentialStore
        without restart). status: pending blocked_by: phase-3-supervisor

- id: phase-5-preflight-and-hot-reload content: |
  - [ ] [AGENT] P0. Phase 5 — Preflight auth + balance check + hybrid hot-reload wiring. In ClientWorker: (1) Preflight
        sequence (boot only, blocks CLIENT_READY emission until green): (a) Load credentials from Cloud KMS for every
        venue this client trades (list from clients.yaml); (b) Per-venue auth ping (e.g. Binance `GET /api/v3/account`
        with HMAC-signed request; Hyperliquid `POST /info` with wallet signature; Aave `eth_call` to balanceOf with
        wallet address); (c) Per-venue balance fetch (asserts ≥ minimum_threshold from clients.yaml, else emit
        CLIENT_QUARANTINED with `INSUFFICIENT_BALANCE`); (d) Emit CLIENT_READY with `venue_auth_status` dict; (2)
        Hot-reload sequence (runs continuously alongside main event loop): (a) ClientCredentialKmsPoller polls KMS at
        configured interval per (client_id, venue); (b) On rotation detected → emit in-process CredentialRotatedSignal →
        CredentialStore reloads → next venue request uses new cred. Old creds discarded after grace period (10s) for
        in-flight requests; (c) On ClientLifecycleEvent.CREDENTIAL_ROTATED (push from operator via bus) → same flow but
        bypasses KMS poll (immediate); (3) Per-venue circuit breaker: track per-venue auth-failure count + balance-fetch
        failure count; trip breaker (15min cooldown) after 3 consecutive failures within 5min. Trip emits
        `VENUE_CIRCUIT_TRIPPED` event for alerting-service. Tests: preflight green path (mock KMS + mock venue auth →
        CLIENT_READY); preflight INSUFFICIENT_BALANCE path → CLIENT_QUARANTINED; preflight venue-auth-timeout →
        CLIENT_QUARANTINED with `VENUE_AUTH_TIMEOUT`; push credential rotation (operator emits CREDENTIAL_ROTATED bus
        event) → worker reloads + venue request uses new cred within 100ms; pull credential rotation (KMS poll detects
        rotation) → reload within poll_interval + 1s. status: pending blocked_by: phase-4-client-worker-ipc

- id: phase-6-execution-service-wiring-and-transfer-facade content: |
  - [ ] [AGENT] P0. Phase 6 — Execution-service wiring + TransferCoordinator facade: (1) Document existing per-process
        per-client isolation (`isolation_policy.py`) in codex
        `04-architecture/execution-service-per-client-isolation.md` — confirm pattern, no code change needed for May-23
        (already correct); (2) Document existing OMS surface (PersistentOrderManager + UnifiedOrderManager protocol) in
        codex `04-architecture/oms-protocol-and-state-machine.md`; (3) Document existing multi-venue concurrent routing
        (asyncio.gather + SmartOrderRouter) in codex `04-architecture/multi-venue-concurrent-routing.md` — covers
        per-venue rate limit + circuit breaker pattern (extend existing pattern if needed; current pattern is sufficient
        for May-23 per audit); (4) Add `execution_service/transfer_coordinator.py` `TransferCoordinator`: SINGLE entry
        point for all TransferIntent events; routes by transfer_type to the right existing implementation: CEX_WITHDRAW
        → adapters/order_adapter.py venue withdraw; DEFI_DEPOSIT → defi_execution/protocols/<protocol>/deposit;
        DEFI_WITHDRAW → defi_execution/protocols/<protocol>/withdraw; BRIDGE → v2/handlers.py BridgeHandler;
        SUBACCOUNT_MOVE → NEW (per-venue subaccount API; only Binance + OKX have it; raise NotSupported for other venues
        with named successor `subaccount_transfers_phase_2_2026_06_01.md`); (5) Wire TransferIntent event subscription
        via UAC event bus; emit TransferResult on completion; persistence via existing OrderPersistenceAdapter pattern
        (extend or add TransferPersistenceAdapter); (6) Add per-venue rate-limit + circuit-breaker hardening only if
        Phase 0 audit § (e) flags gaps. Otherwise confirm existing pattern is sufficient. Tests: TransferCoordinator
        route-by-type unit tests (mock each downstream handler); idempotency test (same TransferIntent.idempotency_key
        submitted twice → second is no-op, returns cached TransferResult); cross-client reject test (TransferIntent with
        foreign client_id rejected at bus by assert_client_allowed). status: pending blocked_by:
        phase-5-preflight-and-hot-reload

- id: phase-7-e2e-and-unit-test-bundle content: |
  - [ ] [AGENT] P0. Phase 7 — End-to-end + unit test bundle for 2-client May-23 scenario: (1) E2E test in
        `e2e-testing/scripts/defi/`: spawn StrategySupervisor with 2 clients (us + defi-client-1); verify both reach
        CLIENT_READY; emit synthetic signal → both clients route orders to execution-service (one process per client) →
        fills come back → per-client PnL recorded; force CRASH in client A worker (raise SystemExit) → verify supervisor
        restarts within 16s + client B unaffected throughout; force QUARANTINE on client A (5 restart failures) → verify
        CLIENT_QUARANTINED emitted + client B still trading; (2) Unit test bundle: hot-add 3rd client at runtime
        (REGISTER event) → spawn within 30s → CLIENT_READY emitted; hot-remove 3rd client (DEREGISTER) → graceful
        drain + reap within 60s; credential rotation via push (CREDENTIAL_ROTATED bus event) → next venue request uses
        new cred; credential rotation via pull (KMS poll detects rotation) → reload within poll_interval + 1s; (3)
        Capacity simulation test: spawn supervisor with shard_capacity_max=3, register 4 clients → 3rd REGISTER triggers
        ShardCapacityEvent.SPAWN_NEW_SHARD emission; 4th REGISTER queued or rejected (operator-decision pending —
        DEFAULT: rejected with QUEUE_FULL until SPAWN_NEW_SHARD ack from deployment-service); (4) Crash matrix: segfault
        in worker (via ctypes call to invalid address) → subprocess dies → supervisor restart; OOM in worker (allocate
        10GB while VM has 8GB) → kernel OOM-kill subprocess → supervisor restart; (5) Performance baseline: 2 clients ×
        100 ticks/sec sustained for 10min → MTM compute happens ONCE per symbol per tick in supervisor (verify via
        prom-metric `mtm_compute_count_total`); shared-memory read latency p99 < 100us per ClientWorker tick. Tests live
        in: `strategy-service/tests/per_client_isolation/`, `execution-service/tests/transfer_coordinator/`,
        `e2e-testing/scripts/defi/per_client_isolation_e2e.py`. PYTEST_UNIT_DIR may need adjustment for strategy-service
        per CLAUDE.md per-family override rule. status: pending blocked_by:
        phase-6-execution-service-wiring-and-transfer-facade

- id: phase-8-deployment-service-wiring content: |
  - [ ] [AGENT] P0. Phase 8 — deployment-service + deployment-api wiring for shard naming + clients.yaml: (1) Update
        `deployment-service/scripts/vm/launch-strategy-paper-vm.sh` + `launch-strategy-live-vm.sh` to accept `--shard N`
        (default 0) and `--clients-yaml-path PATH`. VM name pattern: `strategy-{mode}-{archetype}-shard{N}-{ts}` (was:
        `strategy-{mode}-{archetype}-{ts}`). Singleton lock changes to `{mode}-{archetype}-{shard}` triplet; (2) Update
        `VM_PREFIX_TO_BUCKET` in `deployment-service/scripts/vm/vm_zombie_watchdog.py` to recognise the new shard suffix
        pattern. lifecycle_class = LONG_LIVED_LIVE for live VMs, SCHEDULED_RECURRING for paper VMs; (3) Add
        `deployment-api/api/routes/strategy_shard.py`: `POST /api/strategy/shard/spawn` endpoint (consumes
        ShardCapacityEvent → launches new VM via existing launch-strategy script); `POST /api/strategy/shard/drain`
        endpoint (DEREGISTER all clients → SIGTERM supervisor → reap); (4) Per-client clients.yaml schema in
        `deployment-service/configs/strategy/{archetype}/clients.yaml`: list of (client_id, shard_id,
        venue_creds_kms_path, min_balance_per_venue, risk_limits) tuples. Operator-managed; supervisor reads at boot +
        on REGISTER event. For May-23: two entries (us + defi-client-1) with shard_id=0 for both. Tests: launch script
        smoke test with `--shard 1 --clients-yaml-path /tmp/test_clients.yaml` → VM spawns with correct name + env vars;
        vm_zombie_watchdog recognises new pattern; clients.yaml schema validated by UAC type (add
        `unified_api_contracts/canonical/domain/strategy/clients_yaml_schema.py`). status: pending blocked_by:
        phase-7-e2e-and-unit-test-bundle

- id: phase-9-codex-ssot content: |
  - [x] ✅ **[AGENT] P1. Phase 9 — Codex SSOT updates (ALL 8 docs complete)** —
        PM@32d1929db (slot 8, docs 1/6/7/8 2026-05-20) + slot 7@9db39606 (docs 2/3/4/5 2026-05-20, sanity-checked
        by slot 8 2026-05-20) - ✅ (1) `codex/04-architecture/per-client-isolation-architecture.md` —
        supervisor + ClientWorker subprocess, MarkPriceAggregator, hybrid hot-reload, preflight, crash isolation, GIL
        rationale, clients.yaml - ✅ (2) `codex/04-architecture/execution-service-per-client-isolation.md` — isolation_policy.py:1-80
        pattern confirmed, one-process-per-client, client-funds-isolation.md cross-ref present - ✅ (3) `codex/04-architecture/oms-protocol-and-state-machine.md` —
        OMS state machine, UnifiedOrderManager/OrderPersistenceAdapter/PersistentOrderManager coverage confirmed - ✅ (4) `codex/04-architecture/multi-venue-concurrent-routing.md` —
        concurrent.py two-leg asyncio.gather + SmartOrderRouter coverage confirmed - ✅ (5)
        `codex/04-architecture/transfer-coordinator.md` — client-funds-isolation.md HARD RULE cross-ref present,
        enforce sequence covers client_id check + isolation_policy.assert_client_allowed - ✅ (6)
        `codex/04-architecture/client-lifecycle-event-bus.md` — REGISTER/DEREGISTER/QUARANTINE/CREDENTIAL_ROTATED,
        push-vs-pull, ShardCapacityEvent, supervisor subscription code snippet - ✅ (7)
        `codex/05-infrastructure/strategy-shard-vm-topology.md` — VM naming, capacity thresholds, shard auto-spawn,
        vm_zombie_watchdog prefix mapping, drain-before-migration rule - ✅ (8)
        `codex/04-architecture/promote-workflow-architecture.md` UPDATED — per-client + per-shard taxonomy added,
        shard-invisible-to-promote clarified, E.2 listed in deferred status

- id: phase-e2-auto-shard-supervisor-signal content: |
  - [ ] **POST-MAY-23** [AGENT] P1. Phase E.2 — Auto-shard supervisor signal end-to-end: Wire deployment-service to
        CONSUME ShardCapacityEvent.SPAWN_NEW_SHARD and automatically launch the next shard VM. May-23 ships the EVENT
        EMISSION (Phase 3 ShardCapacitySensor) + manual VM launch endpoint (Phase 8 `/api/strategy/shard/spawn`); E.2
        closes the loop by adding the deployment-service consumer + cron loop that watches the bus and triggers VM
        launches automatically. Includes: anti-thrash debounce (don't spawn 3 shards in 60s if one client floods);
        cost-ceiling guard (operator-configured max VMs per archetype); operator-override (manual SPAWN_NEW_SHARD via
        API). Target: 2026-05-28. status: deferred blocked_by: phase-9-codex-ssot

- id: phase-e3-intra-client-rebalancer content: |
  - [ ] **POST-MAY-23** [AGENT] P2. Phase E.3 — **Intra-client** RebalanceCoordinator (two legitimate scopes;
        cross-client fund movement is FORBIDDEN by HARD RULE — see plan body): Add `IntraClientRebalanceCoordinator`
        (sub-package in strategy-service or new top-level service — decide at filing time). Owns TWO and ONLY TWO
        rebalance scopes, BOTH bounded by `client_id` invariant: (a) **Intra-client multi-portfolio**: shifting
        allocation between strategy archetypes (portfolios) for ONE client — e.g. client X reduces `carry_staked_basis`
        exposure to fund `arbitrage_price_dispersion`. All TransferIntent events emitted carry the same client_id on
        source + dest. (b) **Intra-client multi-wallet / multi-account**: moving funds between ONE client's wallets or
        accounts — e.g. client X's main wallet → client X's archetype-specific subaccount, or client X's Binance
        subaccount → client X's Coinbase wallet. Same client_id invariant. **Invariant enforced at code AND test
        level**: every TransferIntent emitted by this coordinator MUST satisfy
        `source_account.client_id == dest_account.client_id`. Unit test asserts coordinator REFUSES to emit any
        cross-client intent (raises `CrossClientTransferForbiddenError`). Defence-in-depth: TransferCoordinator
        (Phase 6) ALSO rejects at the execution-service consumer side. Requires legal/custody review only for the
        multi-wallet variant if client X's wallets sit under different custody providers (Copper vs CEFFU vs
        self-custody). Multi-portfolio rebalancing within one custody provider needs no legal review. Target: 2026-06-01
        to 2026-06-15. status: deferred blocked_by: phase-e2-auto-shard-supervisor-signal

## Slot assignment (slot 1 main proposes — operator may reallocate)

| Slot | Phase                                                  | Cal AI-days | Depends on                                                       |
| ---- | ------------------------------------------------------ | ----------- | ---------------------------------------------------------------- |
| 5    | Phases 1 + 2 (UAC + UTL bases)                         | ~1.5        | Phase 5 strategy_repo_consolidation UTL lifts (in flight)        |
| 4    | Phase 3 (StrategySupervisor)                           | ~1          | Phase 2 (slot 5)                                                 |
| 6    | Phase 4 (ClientWorker + IPC)                           | ~1.5        | Phase 3 (slot 4)                                                 |
| 4    | Phase 5 (preflight + hot reload)                       | ~0.8        | Phase 4 (slot 6)                                                 |
| 7    | Phase 6 (execution-service docs + TransferCoordinator) | ~1          | Phase 5 (slot 4) — but most is doc-only, can parallel-start      |
| 6    | Phase 7 (e2e + unit tests)                             | ~1          | Phase 6 (slot 7)                                                 |
| 7    | Phase 8 (deployment-service wiring)                    | ~0.5        | Phase 7 (slot 6)                                                 |
| 8    | Phase 9 (codex SSOT)                                   | ~0.5        | Phase 8 (slot 7) — but can parallel-start since most is doc-only |

Total: ~7.8 cal-AI-days. With 8-slot parallel fan-out and 3 calendar days (May-20 → May-23), achievable IF Phase 5 UTL
lifts land May-20 EOD (slot 5 active).

## Success criteria (May-23 cutover gate)

- ✅ 2 clients (us + defi-client-1) live on at least 1 archetype VM (paper or live mode)
- ✅ Hot-add 3rd client at runtime works (operator can emit REGISTER and worker spawns < 30s)
- ✅ Client crash isolation verified: kill -9 on one ClientWorker → supervisor restarts within 16s + other clients
  untouched throughout
- ✅ Credential rotation verified: KMS rotation → next venue call uses new cred within 60s (pull); push event → within
  1s
- ✅ MarkPriceAggregator: one compute per symbol per tick (prom-metric verifies); shared-memory broadcast latency p99 <
  100us
- ✅ TransferIntent / TransferResult flow live for at least 1 DeFi deposit (e.g. USDC → Aave) per client
- ✅ basedpyright clean across UAC + UTL + strategy-service + execution-service
- ✅ All Phase 7 unit + e2e tests green

## Out-of-scope for May-23 (named successors)

- Auto-shard end-to-end → Phase E.2 (this plan), 2026-05-28
- Intra-client multi-portfolio + multi-wallet rebalancing → Phase E.3 (this plan), 2026-06-01. **Cross-client fund
  movement is NEVER in scope — HARD RULE codified in this plan + `codex/04-architecture/client-funds-isolation.md`.**
- Sub-account transfers for non-Binance/OKX venues → `subaccount_transfers_phase_2_2026_06_01.md` (to be created)
- Free-threading (PEP 703) evaluation → `python_free_threading_eval_2026_07_01.md` (to be created post-cutover)

## Composes with

- `plans/active/strategy_repo_consolidation_2026_05_19.md` Phase 5 (UTL lifts) — must land first (slot 5 active)
- `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` — VM launcher pattern this extends
- `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md` — credential surface this consumes
- `plans/active/master_to_live_defi_2026_05_23.md` — promotes E.0+E.1 as new success criterion (Group H or similar)
