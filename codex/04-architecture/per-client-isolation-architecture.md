---
doc_type: codex-ssot
title: Per-Client Isolation Architecture (Strategy-Service)
summary:
  Strategy-service runs one StrategySupervisor per (archetype × shard) VM that spawns one spawn-context ClientWorker
  subprocess per client — hard crash isolation (segfault/OOM in one client never affects another), a shared-memory
  MarkPriceAggregator (one MTM compute per symbol per tick), hybrid push/pull credential hot-reload, and a 4-step
  CLIENT_READY preflight; designed for the May-23 2-client launch and scaling to N clients per VM.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, deployment-service, execution-service, strategy-service, unified-trading-library]
scope: [engineer, admin]
tags: [per-client-isolation, strategy, cefi, defi, execution, client-funds, reconciliation]
related:
  [
    /codex/04-architecture/client-funds-isolation.md,
    /codex/05-infrastructure/strategy-shard-vm-topology.md,
    /codex/04-architecture/execution-service-per-client-isolation.md,
  ]
created: 2026-05-20
authoritative_for: [strategy-service StrategySupervisor + ClientWorker per-client isolation model]
referenced_by:
  [
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/client-lifecycle-event-bus.md,
    /codex/04-architecture/execution-service-per-client-isolation.md,
    /codex/04-architecture/global-ledger-architecture.md,
    /codex/04-architecture/identity-model.md,
    /codex/04-architecture/promote-workflow-architecture.md,
    /codex/04-architecture/transfer-coordinator.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
  ]
owner:
last_reviewed: 2026-08-14
code_refs:
---

# Per-Client Isolation Architecture (Strategy-Service)

## Overview

Strategy-service runs one `StrategySupervisor` process per (archetype × shard) VM. The supervisor spawns one
`ClientWorker` subprocess per registered client. Hard crash isolation (subprocess boundary) means a segfault, OOM, or
uncaught exception in one ClientWorker does not affect any other client on the same VM.

This architecture was designed for the May-23 2-client launch (Odum Research UK + defi-client-1) and scales to N clients
per archetype VM with auto-shard onto additional VMs when capacity thresholds are breached.

Cross-reference: `/codex/04-architecture/client-funds-isolation.md` HARD RULE — funds NEVER move between different
clients. All TransferIntent events must satisfy `source_account.client_id == dest_account.client_id`.

SSOT: `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md`.

---

## Supervisor + ClientWorker Model

```
StrategySupervisor (main process)
    ├── MarkPriceAggregator          # one MTM compute per symbol per tick; zero-copy broadcast
    ├── ClientAdmissionController    # spawns/reaps ClientWorker subprocesses on REGISTER/DEREGISTER
    ├── ShardCapacitySensor          # emits ShardCapacityEvent when VM saturates
    ├── HealthAggregator             # rolls up per-ClientWorker heartbeats for /health endpoint
    │
    ├── ClientWorker [client_id=A]   # subprocess (own GIL, own address space)
    │     ├── PositionStateStore
    │     ├── ExecutionRouter
    │     ├── PnLAttributor
    │     ├── RiskGuard
    │     └── CredentialStore
    │
    └── ClientWorker [client_id=B]   # crash in A does NOT affect B
          └── ...
```

**Spawn context**: `multiprocessing.get_context("spawn").Process` (spawn, NOT fork). Fork is unreliable for
venue-adapter HTTP clients that use connections acquired before fork; spawn gives a clean address space.

**IPC channels**:

- Parent → child: `multiprocessing.Pipe` — lifecycle events, credential-rotation signals, shutdown
- Child → parent: same pipe — ready ack, quarantine events, heartbeats, order-emitted, transfer-intent-emitted

---

## MarkPriceAggregator (Pricing Centralisation)

**Audit 2026-05-20** confirmed MTM compute is performed locally in 4 paths in strategy-service:

| File                                                                                                                  | Compute                                             |
| --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `strategy_service/pnl/engine/pnl_input_builder.py:197-198`                                                            | `unrealized_pnl = net_qty × last_price - buy_val`   |
| `strategy_service/position/core/mark_price_subscriber.py:52`                                                          | `unrealized_pnl = (mark_price - entry_price) × qty` |
| `unified_trading_library/risk/leg_snapshot_builder.py` (relocated from `strategy_service/position/core/`, 2026-07-13) | `notional = abs(position_units × mark_price)`       |
| `strategy_service/risk/core/risk_calculator.py:127-129`                                                               | aggregates `position_value` for leverage            |

**Post-isolation**: these 4 paths consume **pre-computed** `mtm_value_per_unit` from the supervisor's shared-memory
dict, rather than re-computing per ClientWorker. One compute per symbol per tick, N reads.

**Shared-memory layout**:

- `multiprocessing.shared_memory.SharedMemory` named per (archetype, shard)
- Key: `instrument_id` → `MarkSnapshot(price, mtm_value_per_unit, timestamp, stale_after_ms)`
- Zero-copy reads from ClientWorker (read-only view); supervisor writes at each tick
- p99 read latency target: < 100µs per ClientWorker tick

---

## Hybrid Hot-Reload (Push + Pull)

### Push — client registration / deregistration (low frequency)

| Event                         | Direction                 | Handler                                              |
| ----------------------------- | ------------------------- | ---------------------------------------------------- |
| `REGISTER`                    | bus → supervisor          | Spawn ClientWorker; wait CLIENT_READY (30s timeout)  |
| `DEREGISTER`                  | bus → supervisor          | Send SIGTERM to ClientWorker; wait drain (60s); reap |
| `CREDENTIAL_ROTATED`          | bus → supervisor → worker | Immediate credential reload in CredentialStore       |
| `QUARANTINE` / `UNQUARANTINE` | supervisor → bus          | Emitted by supervisor on worker failure / recovery   |

Events: `ClientLifecycleEvent` UAC type. Supervisor subscribes via `ClientLifecycleBusSubscriberBase` (UTL, extends
`KillSwitchBusSubscriberBase` from Phase 5 of `strategy_repo_consolidation_2026_05_19.md`).

### Pull — credential rotation (high frequency, automated)

`ClientCredentialKmsPoller` polls Cloud KMS / Secret Manager per (client_id, venue) at a configurable interval:

| Venue type | Default poll interval |
| ---------- | --------------------- |
| CEX        | 60s                   |
| DEX        | 300s                  |
| Lending    | 600s                  |

On rotation detected → in-process `CredentialRotatedSignal` → `CredentialStore.reload()` → old cred discarded after 10s
grace period (in-flight requests drain). Push credential rotation (operator bus event) bypasses the poll interval and
reloads immediately.

---

## Preflight Sequence (ClientWorker boot)

Blocks `CLIENT_READY` emission until all steps pass. Any step failure → `CLIENT_QUARANTINED`.

```
Step A: Load credentials from Cloud KMS for every venue in clients.yaml
Step B: Per-venue auth ping
        - CEX: signed REST request (e.g. Binance GET /api/v3/account with HMAC)
        - DeFi: eth_call to balanceOf with wallet address
        - Hyperliquid: POST /info with wallet signature
Step C: Per-venue balance fetch — assert ≥ minimum_threshold from clients.yaml
        - Failure → emit CLIENT_QUARANTINED with reason=INSUFFICIENT_BALANCE
Step D: Emit CLIENT_READY with venue_auth_status dict (OK|FAILED|SKIPPED per venue)
```

---

## Crash Isolation Guarantees

| Failure scenario   | Outcome                                                                |
| ------------------ | ---------------------------------------------------------------------- |
| Uncaught exception | Worker process exits; supervisor detects via pipe close + os.waitpid   |
| Segfault / SIGSEGV | Kernel sends SIGILL; subprocess dies; supervisor detects same way      |
| OOM / SIGKILL      | Kernel OOM-killer kills subprocess; supervisor restart loop triggered  |
| Supervisor crash   | All ClientWorkers become zombies; VM watchdog reboots the archetype VM |

**Restart loop**: exponential backoff (1s, 2s, 4s, 8s, 16s), then QUARANTINE after 5 consecutive crashes. Quarantine
emits `ClientQuarantinedEvent` to alerting-service and marks the slot as available for re-registration after
`retry_after_seconds`.

---

## GIL and True Parallelism

Each `multiprocessing.Process` subprocess gets its own GIL. All CPU-bound paths (MTM compute in supervisor,
pnl/position/risk in each ClientWorker) run in true parallel across CPU cores, not limited by the parent process's GIL.

**Free-threading (PEP 703)** is explicitly out of scope until a C-extension recompile audit is completed. Subprocess
isolation is portable across Python 3.12/3.13/3.14 with no recompile risk.

---

## Clients Configuration

Operator-managed `clients.yaml` per (archetype, shard):

```
deployment-service/configs/strategy/{archetype}/shard{N}/clients.yaml
```

Schema: `unified_api_contracts/canonical/domain/strategy/clients_yaml_schema.py`.

```yaml
clients:
  - client_id: odum-research-uk
    shard_id: 0
    venue_creds_kms_path: projects/central-element-323112/secrets/odum-uk-{venue}-creds
    min_balance_per_venue:
      BINANCE: 1000 # USDC
      HYPERLIQUID: 500
    risk_limits:
      max_position_usd: 50000
      max_daily_drawdown_pct: 5.0

  - client_id: defi-client-1
    shard_id: 0
    venue_creds_kms_path: projects/central-element-323112/secrets/defi-client-1-{venue}-creds
    min_balance_per_venue:
      HYPERLIQUID: 200
    risk_limits:
      max_position_usd: 10000
      max_daily_drawdown_pct: 3.0
```

Loaded at supervisor boot; hot-reloadable via `ClientLifecycleEvent.REGISTER` (operator pushes new entry to bus;
supervisor appends to runtime client list and spawns the new worker) — this REGISTERS a new client; it does not make an
EXISTING client's param values (e.g. leverage) hot-reloadable, which today requires a VM restart because `clients.yaml`
is a git file baked into the deployment, not a GCS-backed reloadable config (see § "Config surface ownership" below).

---

## Config surface ownership — which of the three per-client-shaped files owns what

Three files in the codebase look like they could hold per-client policy. Only one does; resolved by a 2026-08-12
cross-repo audit (`plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md`) after an
operator question found no doc stated the ownership split:

| Surface                                                        | What it actually holds                                                                                                                                              | Live?                                                                                   |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `wallet-config/{chain_env}/wallet_mapping.json`                | Wallet ADDRESSES: `custodian` → `chain_env` → `share_class` → one treasury wallet + trading wallets, plus 3 treasury knobs (`reserve_pct`, `min/max_threshold_pct`) | **No** — schema + path constant only, zero consumers                                    |
| `deployment-service/configs/strategy/{archetype}/clients.yaml` | **THE per-client surface** documented above — `client_id`, `shard_id`, `venue_creds_kms_path`, `min_balance_per_venue`, `risk_limits`                               | **Yes** — validated by `ClientsYaml.model_validate_yaml()` at `StrategySupervisor` boot |
| `strategy_service/configs/*.yaml`                              | Per-STRATEGY config (e.g. `carry_staked_basis.yaml`) — no client dimension                                                                                          | Yes, but not a client surface                                                           |

Two known gaps in the live surface, not yet fixed (tracked in the issue doc above, not restated here): it is keyed
**(archetype, shard) → [client]** rather than client-first, so one client running N archetypes has no single file
answering "what is this client configured to do?"; and `ClientsYamlEntry`/`ClientRiskLimits` are `extra="forbid"` with
no leverage, venue-selection, or coin-universe field, so none of those are expressible without a schema change. Operator
ruling 2026-08-12 (same issue doc, § "Target state") sets the eventual replacement key as **`(client_id, slot_label)`**
— the same pair the event-tag 9-tuple already carries
([strategy-identity-versioning](/codex/06-coding-standards/strategy-identity-versioning.md)) — governing every
strategy-service config surface, not just today's 7-field `clients.yaml`; that migration is still in progress, so this
doc's "Clients Configuration" section above reflects the CURRENT live shape, not the target one.

---

## Key Files

| Path                                                                                                | What                                         |
| --------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `strategy-service/strategy_service/supervisor/strategy_supervisor.py`                               | StrategySupervisor concrete class            |
| `strategy-service/strategy_service/supervisor/mark_price_aggregator.py`                             | MarkPriceAggregator + shared-memory writer   |
| `strategy-service/strategy_service/supervisor/client_admission_controller.py`                       | REGISTER/DEREGISTER handler + restart loop   |
| `strategy-service/strategy_service/supervisor/shard_capacity_sensor.py`                             | psutil polling + ShardCapacityEvent emission |
| `strategy-service/strategy_service/client_worker/client_worker.py`                                  | ClientWorker subprocess entry point          |
| `unified-trading-library/unified_trading_library/services/strategy_supervisor_base.py`              | StrategySupervisorBase abstract              |
| `unified-trading-library/unified_trading_library/services/client_worker_base.py`                    | ClientWorkerBase abstract                    |
| `unified-trading-library/unified_trading_library/lifecycle/client_lifecycle_bus_subscriber_base.py` | Push-event subscription base                 |
| `unified-trading-library/unified_trading_library/lifecycle/client_credential_kms_poller.py`         | KMS poll + CredentialRotatedSignal           |

---

## Composes With

- `/codex/04-architecture/client-funds-isolation.md` — HARD RULE: funds never cross client boundaries
- `/codex/04-architecture/client-lifecycle-event-bus.md` — event types for
  REGISTER/DEREGISTER/QUARANTINE/CREDENTIAL_ROTATED
- `/codex/05-infrastructure/strategy-shard-vm-topology.md` — VM naming, shard auto-spawn, capacity thresholds
- `/codex/04-architecture/execution-service-per-client-isolation.md` — execution-side isolation (one process per client)
