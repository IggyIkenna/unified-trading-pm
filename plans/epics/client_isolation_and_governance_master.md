---
name: client_isolation_and_governance_master
title: "Client Isolation + Governance Master (L4)"
type: epic
tier: L4
status: active
priority: P0
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-22
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md
  - ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md
---

# Client Isolation + Governance Master (L4)

**Owns**: per-client subprocess isolation + cross-client funds isolation (HARD RULE) + jurisdiction restrictions (UK vs
Cayman entity per venue) + share-class enum reconciliation + UAC schema evolution + hardcoded-value cleanup + client +
strategy ID catalogue + manual UI replication of every live action.

**Assigned VM**: `vm-cross-cutting` (co-located with `infrastructure_master` + `observability_master` +
`batch_live_symmetry_master`).

## Scope inherited from `cross_cutting_may_23_SUPERSEDED_2026_05_21` (extended 2026-05-21)

The pre-2026-05-21 `cross_cutting_may_23_2026` epic wrapped 5 workspace-wide concerns. **This epic absorbs them +
extends to govern post-May-23 cross-cutting evolution**:

1. **Strategy catalogue (HARD)** — every (archetype, venue, instrument-type) combination enumerated; per-archetype venue
   matrix + configuration parameters; full universe modelled even where not launching live this cycle.
2. **Strategy IDs** — stable machine-readable IDs for every archetype × venue × client × account combination; UAC
   canonical naming + versioning; propagated through every fill / signal / model inference.
3. **Clients + accounts** — client model in UAC; account-per-venue mapping; capital allocation matrix per (client,
   archetype, venue); client-account-strategy tagging.
4. **UI replication of every live action** (DART manual-trade lane) — manual operator action through the UI for every
   live trade / model training / DeFi swap / CeFi order / sports bet. Operator safety valve.
5. **Infrastructure / stability / deployment / live functionality / speed** — perfect infrastructure for May-23 cutover.

**Extension scope** (post-May-23 cross-cutting work):

- **Cross-client funds isolation HARD RULE** — 3-layer enforcement (UAC schema / strategy emit / execution consume);
  `CrossClientTransferForbiddenError`; per-client-id invariant on every transfer/withdraw/deposit/bridge/sub-account
  move.
- **Per-client subprocess isolation** — `ClientWorker` per `multiprocessing.Process` per client; `MarkPriceAggregator`
  shared-memory broadcast; `ClientAdmissionController` restart loop; `ShardCapacitySensor`.
- **Jurisdiction restrictions** — `VENUE_JURISDICTION_RESTRICTIONS: dict[str, VenueJurisdictionRule]` (NEW, P0); UK
  entity blocked from Extended Starknet (etc.); Cayman entity as gateway for venues banning UK residents.
- **Share-class enum reconciliation** — Enum A (3-value `canonical.crosscutting.share_class.ShareClass`) vs Enum B
  (9-value `internal.architecture_v2.enums.ShareClass`); GBP/EUR/USD/SOL/USDC/FDUSD silently dropped from root facade.
- **UAC schema evolution** — workspace-wide schema migration discipline; deprecation/rename/extension patterns.
- **Hardcoded-value cleanup** — gas estimates (21000 @ 30 gwei stub); `_WITHDRAWAL_FEES` flat dict; alerting thresholds
  (`_WEETH_DEPEG_THRESHOLD_PCT`, `_RATE_DEVIATION_*_BPS`); migrate to UAC `ALERT_THRESHOLDS` + config-hot-reload paths.

Full archaeology of pre-May-23 5 deliverables:
[`cross_cutting_may_23_SUPERSEDED_2026_05_21.md`](cross_cutting_may_23_SUPERSEDED_2026_05_21.md).

## Codex SSOTs

- [`codex/04-architecture/client-funds-isolation.md`](../../codex/04-architecture/client-funds-isolation.md) — HARD
  RULE + 3-layer enforcement
- [`codex/09-strategy/architecture-v2/axes/share-class.md`](../../codex/09-strategy/architecture-v2/axes/share-class.md)
  — share-class axis SSOT
- [`codex/06-coding-standards/quality-gates.md`](../../codex/06-coding-standards/quality-gates.md) — hardcoded-value QG
  steps
- [`codex/11-project-management/epic-execution-with-sub-agents.md`](../../codex/11-project-management/epic-execution-with-sub-agents.md)
  — epic-flow SSOT (pointer to [`README.md`](README.md))

## Composition with other epics

- **Enforces on**: ALL L0 asset-group epics (every transfer/order/strategy-emit respects client isolation +
  jurisdiction)
  - `strategy_master` + `execution_master` + `trading_agent_master`
- **Co-located VM**: `infrastructure_master` (multi-client VM topology), `observability_master` (cross-client alert
  routing), `batch_live_symmetry_master` (per-client batch=live verification)
- **Upstream signals**: `instruments_master` (venue jurisdiction tags on `InstrumentRecord`)

## Assigned active plans

_1 active plans declare `parent_epic: client_isolation_and_governance_master` in their frontmatter. Workers pick up in
priority order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## Assigned active plans

_1 active plans declare `parent_epic: client_isolation_and_governance_master` in their frontmatter. Workers pick up in
priority order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority — per_client_isolation archived 2026-05-22)_

## Deferred from `per_client_isolation_and_venue_fanout_topology_2026_05_20` (archived 2026-05-22)

- [ ] [AGENT] P1. **Phase E.2 — Auto-shard supervisor signal**: deployment-service consumes
      `ShardCapacityEvent.SPAWN_NEW_SHARD` + auto-launches next shard VM. **MIGRATED FROM:**
      `per_client_isolation_and_venue_fanout_topology_2026_05_20`. Target: 2026-05-28. Create active plan
      `auto_shard_supervisor_signal_2026_05_28.md` when picking up.
- [ ] [AGENT] P2. **Phase E.3 — Intra-client RebalanceCoordinator**: intra-client multi-portfolio + intra-client
      multi-wallet ONLY; cross-client fund movement is NEVER in scope (HARD RULE). **MIGRATED FROM:**
      `per_client_isolation_and_venue_fanout_topology_2026_05_20`. Target: 2026-06-01. Create active plan
      `intra_client_rebalance_coordinator_2026_06_01.md` when picking up.
- [ ] [NOTE] Sub-account transfers for non-Binance/OKX venues: `subaccount_transfers_phase_2_2026_06_01.md` (to be
      created). Migrated from same source plan.

## P1 — important; post-current-gate (was P0)

### [`per_client_isolation_and_venue_fanout_topology_2026_05_20`](../archive/2026_05/per_client_isolation_and_venue_fanout_topology_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-22 — Phases 0-8 DONE; E.2+E.3 deferred to epic body · **estimate**: 5 cal AI-days
(class: brand-new)

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

_(no plans currently assigned at this priority)_

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
