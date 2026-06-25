---
doc_type: epic
title: Global Ledger + PnL Attribution Master
summary:
status: active
nature: process
stage: [meta]
repos:
  [alerting-service, client-reporting-api, execution-service, greeks-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: []
related:
  &id001 [
    plans/archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    plans/archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md,
  ]
created: 2026-05-21
name: global_ledger_pnl_attribution_master
tier: L2
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: *id001
type: epic
last_updated: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Global Ledger + PnL Attribution Master

**Owns**: the canonical ledger architecture from which position, exposure, PnL, and PnL-attribution are all derived.
Four SSOT ledgers (Instruction / Passive / Treasury / Pricing) authored by execution-service + strategy-service + MTDS +
instruments-service; four derived materialised views (Position / Exposure / PnL / PnLAttribution) computed in
strategy-service `position/` + `risk/` + `pnl/` + `portfolio_allocator/`; one RiskView consumed by alerting-service.

**Status (2026-05-23)**: UAC schemas SHIPPED — `LedgerRow` + 5 enums (`EventOrigin`, `EventType` 37 values, `AssetClass`
17 values, `Direction`, `OptionRight`) + `CrossClientTransferForbiddenError` validator landed in
`unified_api_contracts.canonical.crosscutting.ledger/`. Discovery plan 36/38 BACKED + 2/38 PARTIAL (Phase 2 enum
expansion + Phase 6 TreasuryLedger split — closed by enum expansion + recorded decision; operator [ack] pending).
Migration plan 0/27 — gated on operator [ack] of discovery Phase 3 / 4 / 5 decisions before implementation starts
(target window: post-cutover, 2026-06-01).

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Codex SSOTs

| Doc                                                                  | Owns                                                                                                                              |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `codex/04-architecture/global-ledger-architecture.md`                | 4-SSOT-+-4-derived ledger model; universal PnL recipe; ownership table; per-service writer/reader gap status                      |
| `codex/02-data/ledger-event-taxonomy.md`                             | `EventOrigin` / `EventType` (37) / `AssetClass` (17) / `Direction` / `OptionRight` enum SSOT + routing summary + invariant tables |
| `codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` | Carry-as-theta-family attribution framing; ledger→factor decomposition (delta/gamma/theta/vega/carry/funding/settlement/residual) |
| `codex/04-architecture/client-funds-isolation.md`                    | Cross-client transfer HARD RULE — `client_id == counterparty_client_id` on every transfer/bridge row                              |

## Cross-epic handshakes

| Partner epic                             | Handshake                                                                                                          |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `execution_master`                       | InstructionLedger + PassiveLedger writers (`attribution_builder.build_attribution_rows`); emits via writegate path |
| `strategy_master`                        | Derived-ledger compute (`strategy_service/{position,pnl,risk,portfolio_allocator}/`); PassiveLedger synthesiser    |
| `mtds_mdps_master`                       | PricingLedger writes (`MARK_UPDATE` rows with mid/bid/ask/IV/greeks); carry-rate emission                          |
| `instruments_master`                     | Instrument metadata for passive-event synthesis (expiry / funding interval / rebase schedule / `exercise_style`)   |
| `client_isolation_and_governance_master` | UAC schema governance + cross-client funds isolation HARD RULE validator                                           |
| `observability_master`                   | RiskView consumes PassiveLedger LIQUIDATION/SLASHING rows for alerting                                             |
| `dart_and_promote_master`                | DART consumes PnL + PnLAttribution for promote workflow decisions                                                  |

## Assigned active plans

_2 active plans declare `parent_epic: global_ledger_pnl_attribution_master`. Workers pick up in priority order (P0
first)._

### P0 — Discovery + target-state spec

#### [`global_ledger_pnl_attribution_discovery_2026_05_21`](../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md)

**status**: ✅ ARCHIVED 2026-05-23 — 36/38 BACKED + 2/38 PARTIAL. Operator [ack] pending on Phase 3/5/6; codex SSOT docs
deferred post-cutover. · **estimate**: 3.6 cal AI-days (class: design)

### P1 — Implementation (gated on P0 operator [ack])

#### [`global_ledger_pnl_attribution_migration_2026_06_01`](../archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-23 — Stub plan; all 27 items DEFERRED-OPERATOR-DECISION (gated on discovery plan Phase
3/4/5 operator [ack]; start window 2026-06-01).

### P2 — Continuous-verification + reconciliation

- [ ] [CODE] P2. **Own-greeks vs venue-greeks sanity check — CeFi (Deribit)** (**MIGRATED FROM:**
      `pricing_ledger_carry_rates_mtds_2026_06_01`): Where venue greeks exist (Deribit via
      `unified_api_contracts.normalize_utils.options.DeribitOptionsGreeks`), `greeks-service` computes own greeks AND
      cross-checks against venue-provided. Divergence beyond ε → emit `GREEKS_VENUE_DIVERGENCE` alert via
      alerting-service. Own-computed greeks are authoritative for PricingLedger; venue greeks are the validation
      reference. Tardis-historical Deribit greeks used same way in batch mode. Gate: greeks-service Pub/Sub
      subscription + IS API integration + PricingLedger write-back (Phase 3 items — now all shipped at
      `greeks-service@b0b702d`). (**MIGRATED FROM:** `pricing_ledger_carry_rates_mtds_2026_06_01`)

### P3 — Post-cutover enrichments

_(none yet — defined post-migration ship)_

## Archived plans

### [`global_ledger_pnl_attribution_discovery_2026_05_21`](../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md)

**status**: ✅ ARCHIVED 2026-05-23 — 36/38 BACKED + 2/38 PARTIAL; UAC schemas shipped; operator [ack] pending on Phase
3/5/6.

**Deferred (migrated):**

- **Operator [ack] pending (Phase 3/5/6)**: Late-arriving-data handling + greeks home + TreasuryLedger split decisions.
  Gate for migration sub-plan start.
- **Codex SSOT docs (DEFERRED-POST-CUTOVER)**: `global-ledger-architecture.md` + `ledger-event-taxonomy.md` +
  `pnl-attribution.md` update + CLAUDE.md pointer. All gated on service-repo access.

### [`global_ledger_pnl_attribution_migration_2026_06_01`](../archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-23 — Stub plan; 0/27 items implemented (all DEFERRED-OPERATOR-DECISION, start window
2026-06-01 post-cutover).

**Deferred (migrated):**

- **Pre-migration gate — Phase 3 operator [ack]**: Late-arriving-data handling decision (operator [ack] pending from
  discovery plan).
- **Pre-migration gate — Phase 4 operator [ack]**: Greeks home (where greeks rows live in ledger) decision (operator
  [ack] pending from discovery plan).
- **Pre-migration gate — Phase 5 operator [ack]**: TreasuryLedger split decision (operator [ack] pending from discovery
  plan).
- **Phase 7 — execution-service InstructionLedger writer refactor**: `attribution_builder.build_attribution_rows` → emit
  via writegate path. DEFERRED-POST-CUTOVER (gate: Phase 3/4/5 ack).
- **Phase 8 — strategy-service PassiveLedger synthesiser**: Per-event divergence check path. DEFERRED-POST-CUTOVER
  (gate: Phase 3/4/5 ack).
- **Phase 9 — DART / client-reporting-api / alerting-service reader refactor**: Consumes PnL + PnLAttribution.
  DEFERRED-POST-CUTOVER (gate: Phase 7/8).

## VM assignment notes

Epic runs on **`vm-trading-core`** co-located with `execution_master` + `strategy_master` + `trading_agent_master` (per
`README.md` § "19 epics in 5 tiers"). Bulk of implementation lands in execution-service + strategy-service code, which
is the trading-core service trio. UAC schema PRs route through `client_isolation_and_governance_master` review per its
UAC-schema ownership.

**Anticipated net-new VM prefixes** (discovery Phase 8 confirmed ABSORB-into-existing for all):

- `ledger-reconcile-` → **ABSORB into existing `batch-live-recon-cron-`** (SCHEDULED_RECURRING) for daily
  venue-vs-ledger reconciliation.
- `passive-listener-` → **ABSORB into existing `strategy-live-*`** (LONG_LIVED_LIVE) — PassiveLedger synthesiser runs
  inside `StrategySupervisor` per-client subprocess.
- Derived ledgers → use existing `strategy-paper-*` / `strategy-live-*` / `client-reporting-cutover-*` cohorts.

No new prefixes added to `VM_PREFIX_TO_BUCKET`.

## Continuous-verification path (post-migration)

| Surface                                              | Verification                      | Cadence      |
| ---------------------------------------------------- | --------------------------------- | ------------ |
| InstructionLedger ⟷ venue execution reports          | Daily reconciliation cron         | T+1 daily    |
| PassiveLedger synthesiser ⟷ on-chain/venue emissions | Per-event divergence check        | Per emission |
| PricingLedger ⟷ MTDS canonical prices                | Snapshot cross-check              | Hourly       |
| Derived ledgers ⟷ SSOT replay                        | Backfill replay = production view | Pre-deploy   |
| RiskView liquidation rows ⟷ alerting-service pages   | End-to-end smoke                  | Per event    |
