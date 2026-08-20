---
doc_type: epic
title: Client Isolation + Governance Master (L4)
summary:
  L4 epic owning per-client subprocess isolation + the cross-client funds-isolation HARD RULE
  (CrossClientTransferForbiddenError, per-client_id invariant on every transfer), jurisdiction restrictions (UK vs
  Cayman entity per venue), share-class enum reconciliation, UAC schema evolution, hardcoded-value cleanup, and the
  strategy/client/account ID catalogue.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, fund-administration-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [client-isolation, governance, uac, execution, strategy, data-correctness]
related:
  [
  ]
created: 2026-05-21
name: client_isolation_and_governance_master
tier: L4
priority: P0
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: []
last_updated: 2026-08-20 # was 2026-07-08 -- added fund-administration-service to repos:, the wallet-transfer +
  # per-client-isolation redemption-cadence work in redemption_wallet_transfer_execution_2026_08_20.md lands here.
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Client Isolation + Governance Master (L4)

**Owns**: per-client subprocess isolation + cross-client funds isolation (HARD RULE) + jurisdiction restrictions (UK vs
Cayman entity per venue) + share-class enum reconciliation + UAC schema evolution + hardcoded-value cleanup + client +
strategy ID catalogue + manual UI replication of every live action.

**Assigned VM**: `vm-cross-cutting` (co-located with `infrastructure_master` + `observability_master` +
`batch_live_symmetry_master`).

## Report

Live HTML ledger: https://claude.ai/code/artifact/09b2d4f0-e527-4d9f-a59e-fcf5acda3e70 (generated 2026-08-19,
`/plan-reconcile client_isolation_and_governance_master`)

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
- **UAC schema evolution** — workspace-wide schema migration discipline; deprecation/rename/extension patterns for
  client/strategy/account-ID and share-class schema specifically (this epic's own governance surface); general UAC
  contract-governance work — schema locking/versioning, the canonical_path_violations oracle, registry-completeness
  invariants — moved to [`uac_master`](uac_master.md) 2026-08-18 (epic-taxonomy restructure).
- **Hardcoded-value cleanup** — gas estimates (21000 @ 30 gwei stub); `_WITHDRAWAL_FEES` flat dict; alerting thresholds
  (`_WEETH_DEPEG_THRESHOLD_PCT`, `_RATE_DEVIATION_*_BPS`); migrate to UAC `ALERT_THRESHOLDS` + config-hot-reload paths.

Full archaeology of pre-May-23 5 deliverables:
[`cross_cutting_may_23_SUPERSEDED_2026_05_21.md`](cross_cutting_may_23_SUPERSEDED_2026_05_21.md).

## Codex SSOTs

- [`/codex/04-architecture/client-funds-isolation.md`](/codex/04-architecture/client-funds-isolation.md) — HARD RULE +
  3-layer enforcement
- [`/codex/09-strategy/architecture-v2/axes/share-class.md`](/codex/09-strategy/architecture-v2/axes/share-class.md) —
  share-class axis SSOT
- [`/codex/06-coding-standards/quality-gates.md`](/codex/06-coding-standards/quality-gates.md) — hardcoded-value QG
  steps
- [`/codex/11-project-management/epic-execution-with-sub-agents.md`](/codex/11-project-management/epic-execution-with-sub-agents.md)
  — epic-flow SSOT (pointer to [`README.md`](README.md))

## Composition with other epics

- **Enforces on**: ALL L2 execution/strategy epics (every transfer/order/strategy-emit respects client isolation +
  jurisdiction) — corrected 2026-07-12 (was: "ALL L0 asset-group epics"; `strategy_master`/`execution_master`/
  `trading_agent_master` all self-declare `tier: L2` in their own frontmatter, and `epics/README.md`'s canonical 20-epic
  tier table reserves L0 exclusively for `defi_master`/`cefi_master`/`tradfi_master`/`sports_master`/
  `predictions_master`; this epic's own frontmatter is `tier: L4`. Finding 340.)
  - `strategy_master` + `execution_master` + `trading_agent_master`
- **Co-located VM**: `infrastructure_master` (multi-client VM topology), `observability_master` (cross-client alert
  routing), `batch_live_symmetry_master` (per-client batch=live verification)
- **Upstream signals**: `instruments_master` (venue jurisdiction tags on `InstrumentRecord`)

## Assigned active plans

_(no active plans currently declare `parent_epic: client_isolation_and_governance_master`. Audit-pool wrapper plans for
this epic land here as they are dispatched. See [README.md](README.md) for the audit→plan→epic flow.)_

## Deferred from `per_client_isolation_and_venue_fanout_topology_2026_05_20` (archived 2026-05-22)

- [ ] [AGENT] P1. **Phase E.2 — Auto-shard supervisor signal**: deployment-service consumes
      `ShardCapacityEvent.SPAWN_NEW_SHARD` + auto-launches next shard VM. **MIGRATED FROM:**
      `per_client_isolation_and_venue_fanout_topology_2026_05_20`. Target: 2026-05-28. Create active plan
      `auto_shard_supervisor_signal_2026_05_28.md` when picking up.
- [x] ✅ [AGENT] P2. **Phase E.3 — Intra-client RebalanceCoordinator**: intra-client multi-portfolio + intra-client
      multi-wallet ONLY; cross-client fund movement is NEVER in scope (HARD RULE). **MIGRATED FROM:**
      `per_client_isolation_and_venue_fanout_topology_2026_05_20`. Target: 2026-06-01. SHIPPED — corrected 2026-07-12,
      doc-reconciliation finding 10009, §A2 B-queue ruling (was: unchecked, "Create active plan
      `intra_client_rebalance_coordinator_2026_06_01.md` when picking up"): built + unit-tested
      `strategy-service@1450019e` (2026-06-23) and wired into the live transfer-emit loop `strategy-service@171758fe`
      (2026-06-24) — both commits verified present — per `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
      (task-082/task-090, 2026-06-23/24).
- [ ] [NOTE] Sub-account transfers for non-Binance/OKX venues: `subaccount_transfers_phase_2_2026_06_01.md` (to be
      created). Migrated from same source plan.

## P1 — important; post-current-gate (was P0)

### AUDIT-03 F-25 dispatch (slot 7, 2026-06-01 — from `archive/issues/audit03_ikenna_review_routing_2026_05_22.md`)

- [ ] [CODE] P1. **F-25 — build the FULL unified `ClientConfig` type in `unified_api_contracts.internal`** (NOT a
      minimal stub). Operator decision 2026-06-01: full type, single SSOT for per-client config (KMS refs, venue creds
      shape, isolation policy, portfolio/wallet topology). Replace ad-hoc per-service client-config shapes with this
      type. Repo: unified-api-contracts (+ downstream consumers: strategy-service, execution-service).

### [`uac_coverage_90pct_2026_06_10`](/plans/archive/2026_07/uac_coverage_90pct_2026_06_10.md)

**Sync 2026-07-12** (finding 34, §A2 B-queue ruling): declares `parent_epic: client_isolation_and_governance_master` +
`status: active` + P1, but was absent from this epic's `related_plans` + P1 section — now registered (was: unlisted).
**Corrected 2026-08-19** (`/plan-reconcile client_isolation_and_governance_master`) — this section previously read
"near-complete... only the final PM `quality-gates.sh` confirm-and-flip todo remains open," which was stale. The plan
is now `status: superseded` and fully archived (0 open / 12 done): a later, untracked Phase 5 raised the UAC coverage
gate again (90 → 94, 2026-06-20), reaching 94.62% combined, which mooted this plan's own disputed 89.82%-vs-"≥90%"
numbers. Verified live: `/codex/06-coding-standards/quality-gates.md` lines 505-506 and
`unified-api-contracts/pyproject.toml` `fail_under = 94`. No further action needed here.

### [`per_client_isolation_and_venue_fanout_topology_2026_05_20`](../archive/2026_05/per_client_isolation_and_venue_fanout_topology_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-22 — Phases 0-8 DONE; E.2+E.3 deferred to epic body · **estimate**: 5 cal AI-days
(class: brand-new)

**Corrected 2026-07-12**: removed a duplicate empty `## P1 — important; post-current-gate` header that immediately
followed this line (body read: _"(no plans currently assigned at this priority)"_) — the live P1 content (F-25 dispatch,
above) is the only real P1 section; the duplicate was doc-generation debris that could cause a P1-scanning agent to stop
at the empty block and miss F-25. Finding 33, `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`
§A2 "50 reclassified" blanket ruling.

## P2 — useful; opportunistic

### Canonical instrument_id — UAC-schema governance angle (trimmed 2026-08-18)

**status**: 🔴 CROSS-REFERENCE ONLY — this section previously flagged `canonical_id_builder.py` + instrument-id/
instrument-type UAC schema definitions as touching this epic's "UAC schema" governance scope, but never actually had
a doc filed under this epic for it (the real work always lived under `instruments_master`'s own
[`canonical_instrument_id_audit_2026_07_08`](../audit/results/canonical_instrument_id_audit_2026_07_08.md)). Per the
2026-08-18 epic-taxonomy restructure, general UAC contract-governance work now has its own home,
[`uac_master`](uac_master.md) — see that epic for the current UAC-schema-governance corpus. This pointer is kept only
as a historical cross-reference; `instruments_master` remains the owner of instrument-id/instrument-type schema
content specifically.

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
