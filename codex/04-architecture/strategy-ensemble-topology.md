---
doc_type: codex-ssot
title: Strategy Ensemble VM Topology
summary:
  Strategy VM topology for the 2026-05-23 cutover — ONE ensemble VM per asset_group (no cross-group state), per-VM
  4-process layout (strategy/PBMS/risk/execution) over loopback Redis, launcher registry + colocation bootstrap.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, infrastructure, execution, spot-vm, live-trading]
related:
  [
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
created: 2026-05-15
authoritative_for: [strategy ensemble VM topology (one-VM-per-asset-group + per-VM process layout)]
referenced_by: [/codex/04-architecture/matching-engine-assumptions.md]
owner:
last_reviewed: 2026-05-17
code_refs:
author: ikenna
sources:
  [
    "plans/active/topology_qgroup_gap_closure_2026_05_09.md Phase 1 (GAP-1, GAP-4)",
    plans/epics/strategy_master.md (supersedes strategy_and_dart_master_SUPERSEDED_2026_05_21.md Phase 1.9),
  ]
---

# Strategy Ensemble VM Topology

> **Rationale.** Closes GAP-1 (Q2.1.a, Q4.1.a) + GAP-4 (Q2.1.d) from the topology Q-doc
> `plans/questions/topology_features_strategy_ml_execution_2026_05_08.md`. This document is the single authoritative
> record of the strategy-service VM topology decision for the 2026-05-23 cutover.

---

## Decision

**ONE VM per asset_group.** Each asset_group runs its own isolated ensemble VM. There is no cross-asset-group sharing of
strategy state, position-balance, or risk exposure within a VM.

| Asset group  | VM role                | Archetypes hosted                                                                     |
| ------------ | ---------------------- | ------------------------------------------------------------------------------------- |
| `defi`       | DeFi ensemble VM       | `carry_staked_basis` + `arbitrage_price_dispersion` (funding-rate-dispersion variant) |
| `cefi`       | CeFi hedge-leg VM      | hedge/short leg for DeFi archetypes + CeFi-native carry + arb                         |
| `tradfi`     | TradFi ensemble VM     | futures carry + ES/NQ arb                                                             |
| `sports`     | Sports ensemble VM     | `arbitrage_sports_book` + `arbitrage_event_markets`                                   |
| `prediction` | Prediction ensemble VM | prediction market arb                                                                 |

DeFi + CeFi are **hybrid**: the DeFi VM owns the long/stake/lend leg (on-chain); the CeFi VM owns the hedge/short perp
leg. Both communicate via the cross-VM coordination bus (Pub/Sub event stream), NOT direct HTTP — the IPC-HTTP pattern
in § "Per-VM process layout" is for within-VM communication only.

---

## Multi-tenancy within a VM

Within a single asset-group VM, multiple archetypes run as **dedicated ensemble instances** (one Python process per
archetype). They share:

- VM-local Redis (streams + pub/sub for IPC) — per § "Per-VM process layout"
- Position-balance-monitor process (single process, reads all strategy events from the local stream)
- Risk-and-exposure process (single process, reads all strategy events + position-balance updates)

They do NOT share:

- Strategy state (each archetype keeps independent state)
- Signal subscriptions (each archetype subscribes to its own feature stream)
- Execution queues (each archetype writes to its own execution queue)

Cross-archetype mixing of strategy state within a VM is **banned**.

---

## Per-VM process layout (GAP-2 + GAP-3)

Four services run as **separate OS processes** on each strategy ensemble VM:

```
VM (one per asset_group)
├── strategy-service           (1 process per archetype, e.g. 2 on DeFi VM)
│   └── IPC: local Redis Stream XADD "strategy:output:{archetype}"
├── position-balance-monitor   (1 process, shared across archetypes)
│   └── IPC: reads "strategy:output:*" + writes "position:state"
├── risk-and-exposure          (1 process, shared across archetypes)
│   └── IPC: reads "strategy:output:*" + "position:state" + writes "risk:state"
└── execution-service          (1 process per archetype, mirrors strategy)
    └── IPC: reads "strategy:output:{archetype}" → HTTP to live venue or batch matching engine
```

**IPC transport**: within-VM — local Redis Stream (port 6379, loopback only). Cross-service calls (strategy → risk API
endpoint, strategy → position-balance API endpoint) use UCI HTTP with default `http://localhost:{port}` when colocated.

**Service discovery** (colocation): env vars override in production:

- `POSITION_BALANCE_URL` — defaults to `http://localhost:8501`
- `RISK_EXPOSURE_URL` — defaults to `http://localhost:8502`
- `EXECUTION_URL` — defaults to `http://localhost:8503`

These env vars are set by the colocation-bootstrap script at VM startup; they remain configurable for remote deployments
(e.g. separate risk VM for larger asset groups post-cutover).

**Batch = Live invariant**: the process layout is identical in batch and live mode. The only difference is that
execution-service routes orders to the matching engine (batch) vs the live venue connector (live). Never build a
separate batch-only process topology.

---

## Launcher registry

Every strategy ensemble VM is launched via a dedicated script in `deployment-service/scripts/vm/`.

| Asset group  | Launcher script                               | VM name prefix         |
| ------------ | --------------------------------------------- | ---------------------- |
| `defi`       | `launch-defi-strategy-vm.sh`                  | `defi-strategy-`       |
| `cefi`       | `launch-cefi-strategy-vm.sh`                  | `cefi-strategy-`       |
| `tradfi`     | (existing backfill launchers — extend)        | `tradfi-*`             |
| `sports`     | (existing sports backfill launchers — extend) | `sports-strategy-`     |
| `prediction` | (post-cutover — see below)                    | `prediction-strategy-` |

All VM name prefixes MUST be registered in `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` before launch. This is enforced
by `TestVmPrefixRegistration::test_all_launch_prefixes_covered_by_watchdog`.

> **[DELTA 2026-05-22]** **Current state:** DeFi and CeFi strategy VM launchers (`launch-defi-strategy-vm.sh`,
> `launch-cefi-strategy-vm.sh`) were shipped as part of the May-23 cutover path. TradFi and Sports launchers extend
> existing backfill launchers. Prediction VM launcher is post-cutover. **Planned delta:**
> `plans/epics/strategy_master.md` tracks prediction launcher creation. **Target architecture:** All 5 asset-group
> strategy VM launchers exist, registered in `VM_PREFIX_TO_BUCKET`, and enforced by `TestVmPrefixRegistration`.

---

## Colocation bootstrap

The colocation bootstrap script (`deployment-service/scripts/vm/colocate-strategy-vm.sh`) runs on VM startup and:

1. Starts local Redis with `redis-server --daemonize yes --port 6379 --bind 127.0.0.1`
2. Sets service-discovery env vars to localhost defaults
3. Starts `position-balance-monitor`, `risk-and-exposure`, and `execution-service` as background daemons
4. Starts strategy-service ensemble(s) in the foreground (one per archetype, parallel `&`)
5. Waits for `VM_SHUTDOWN_ON_COMPLETION` signal and calls `python -m deployment_service.deployments_registry` to emit
   `DEPLOYMENT_COMPLETED` / `DEPLOYMENT_FAILED`

---

## Relationship to other codex docs

- **Process-vs-in-proc IPC detail**: this document (§ "Per-VM process layout")
- **Matching engine configuration**: [`matching-engine-assumptions.md`](matching-engine-assumptions.md)
- **Batch-live architecture**: [`batch-live-architecture.md`](batch-live-architecture.md)
- **Runtime topology (cross-service)**: [`runtime-deployment-topology.md`](runtime-deployment-topology.md)
- **DeFi execution**: [`defi-execution-overview.md`](defi-execution-overview.md)
- **Custody**: [`custody-providers.md`](custody-providers.md)

---

## Open items (post-cutover)

> **[DELTA 2026-05-22]** May-23 cutover landed 2026-05-23. Items below are deferred to the active post-cutover roadmap
> tracked in [`strategy_master.md`](/plans/epics/strategy_master.md).

- Allocator service + dual-projection (Phase 1.9 residuals — see `strategy_master.md`)
- IM-DESK + IM-CLIENT routing through the action-handler engine
- Per-archetype Redis Stream isolation (currently shared within an asset-group VM)
- Separate risk VM for asset groups with >5 concurrent archetypes
