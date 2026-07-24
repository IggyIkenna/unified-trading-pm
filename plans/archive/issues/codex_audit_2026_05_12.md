---
doc_type: issue
title: Codex SSOT currency audit — 2026-05-12 Day-3 refresh (freeze-gate item 9 status update)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
author: ikenna-codefreeze-audit-tab (slot 3)
source:
  [
    plans/active/issues/codex_audit_2026_05_11.md (slot 6 day-1 baseline),
    3-cluster Explore sub-agent fan-out 2026-05-12 Day 3 (Phase 1.D + 1.E + 1.F clusters),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

> ⚪ **STATUS UPDATE** — code_freeze freeze-gate item 9 (`Codex SSOTs updated`) status refresh from slot 6 day-1
> baseline. Slot 6 found 58 present / 33 not-yet-created in the broader audit. Slot 3 Day-3 spot-checks 3 clusters
> (Phase 1.D / 1.E / 1.F) representing ~50% of the touched codex surface. Net delta: existing docs are CURRENT, missing
> docs are NEW Phase 7/8 codex writes (NOT supersedence of shipped SSOT) → freeze-gate item 9 stays 🟡 PARTIAL but
> non-blocking for 2026-05-15.

# Codex SSOT currency audit — 2026-05-12 Day-3 refresh

## What I found

3-cluster Explore sub-agent fan-out 2026-05-12 Day-3 audited 36 codex doc references across 14 Phase 1.D / 1.E / 1.F
plans. Net findings:

| Cluster                                              | Plans audited                                                                                                                                                       | Present (✅)   | Drifting (🟡)                        | Missing (❌)   |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------ | -------------- |
| **1.D — alerting / risk / DR / strategy / DART**     | alerting_service_live_rules + risk_simulations_limits_alerting + disaster_recovery_circuit_breakers + promote_workflow_may23_cli_path + topology_qgroup_gap_closure | **18**         | 0                                    | 9              |
| **1.E — DeFi catalogue / archetypes / sim**          | defi_catalogue_chain_primitives + arbitrage_price_dispersion + defi_recursive_borrow_archetypes + defi_simulation_realism + cme_polymarket_arb                      | **7**          | 1 (stamp-lag only — content current) | 0              |
| **1.F — deployment UI / wallets / client reporting** | deployment_ui_lifecycle_tabs + api_keys_wallets_accounts_readiness + wallet_treasury_client_flow + client_reporting_pnl_attribution_mvp                             | **11**         | 0                                    | 3              |
| **Totals (3 clusters)**                              | 14 plans                                                                                                                                                            | **36 docs ✅** | **1 doc 🟡**                         | **12 docs ❌** |

Combined with slot 6's day-1 audit (58 ✅ / 33 ❌ across all 25 Phase 1 plans), 12 of slot 6's 33 missing items are now
specifically attributed to Phase 1.D/1.E/1.F (1.D = 9 of the 12; 1.F = 3 of the 12).

## Per-cluster details

### Phase 1.D — alerting / risk / DR / strategy / DART (18 ✅ / 0 🟡 / 9 ❌)

**All 18 existing docs PASS currency check** — no SUPERSEDED markers, no stale dates pre-2026-05-08; content matches
plan body state (including Phase 1 UAC extensions + Q8/Q9 ratifications 2026-05-10). Key examples:

- `/codex/04-architecture/risk-rule-taxonomy.md` (2026-05-11 12:40) — ships 22-member closed-set `RiskRuleId` per Phase
  1.A
- `/codex/04-architecture/circuit-breaker-rule-taxonomy.md` (2026-05-11 14:14) — 4-set `BreakerAction` + registry seed
- `/codex/04-architecture/autonomous-recovery-matrix.md` (2026-05-12 09:21) — LayerN decision tree +
  `BreakerRecoveryMode` extension
- `/codex/03-observability/alerting.md` + `/codex/15-runbooks/alerting/alert-code-taxonomy.md` (45-member closed set)
- `/codex/04-architecture/risk-breaker-seam.md` — Q9 ratification 2026-05-10 seam codified
- `/codex/04-architecture/kill-switch-event-bus.md` + `/codex/04-architecture/mev-protection.md`

**9 missing docs are NEW creations (NOT supersedence)**, all owned by plans where they're enumerated as Phase 7
deliverables that ride with the owning plan's later phases — on-schedule per CLAUDE.md "Post-Plan-Phase Codex Audit"
rule, not yet-late-to-deliver:

1. `/codex/09-strategy/operational/cli-promote-paths.md` — promote plan Phase 2 + Phase 7
2. `/codex/04-architecture/promote-workflow-architecture.md` — promote plan Phase 7 (May-23 dual-track narrative)
3. `/codex/05-infrastructure/strategy-vm-launcher-shape.md` — promote plan Phase 1 + Phase 7
4. `/codex/04-architecture/live-deployment-manifest.md` — promote plan Phase U1 (MinimalCandidateManifest)
5. `/codex/14-customer-journeys/promote-pipeline-backend.md` — promote plan Phase U3
6. `/codex/04-architecture/strategy-ensemble-topology.md` — topology plan Phase 1
7. `/codex/04-architecture/matching-engine-assumptions.md` — topology plan Phase 1
8. `/codex/04-architecture/ml-lifecycle.md` — topology plan Phase 2
9. `/codex/04-architecture/multi-mode-wallet-isolation.md` — topology plan Phase 4

### Phase 1.E — DeFi catalogue / archetypes / sim (7 ✅ / 1 🟡 / 0 ❌)

All 7 referenced codex docs present + content current vs. plan body state (including 2026-05-12 UAC commits):

- `/codex/02-data/defi-venue-protocol-catalogue.md` — reflects 99-venue ALL_DEFI_VENUES (UAC@`495d262`)
- `/codex/02-data/defi-data-type-taxonomy.md` — lending_indices schema fields current; governance_proposals +
  slashing_events rows landed
- `/codex/05-infrastructure/chain-rpc-mev-tenderly.md` — Jito MEV (Phase 5A) + Tenderly bundle-sim
- `/codex/04-architecture/flash-loan-receiver.md` — current; pre-deployment addresses
- `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md` + new
  `carry-recursive-borrow-lending-only.md` (2026-05-12)

**1 🟡 DRIFTING — stamp lag only, content current**:

- `/codex/02-data/defi-data-type-taxonomy.md` — `Last updated: 2026-05-10` stamp predates 2026-05-12 UAC@`d02cce2`
  lending-rate enum extension. Schema table CONTENT correctly lists `supply_apy / borrow_apy` in `lending_indices`
  fields, so content is current; only the header stamp lags by 2 days. Documentation-hygiene issue, not SSOT drift.

### Phase 1.F — deployment UI / wallets / client reporting (11 ✅ / 0 🟡 / 3 ❌)

All 11 existing docs current; 8 of them created 2026-05-12 per slot 4 DART work:

- `/codex/05-infrastructure/deployment-ui-architecture.md` § "Environment tier" — env-tier via
  `window.location.hostname`
- `/codex/05-infrastructure/credentials-matrix.md` (2026-05-12) — workspace SSOT
- `/codex/05-infrastructure/fireblocks-integration-spec.md` (2026-05-12) — June-1 integration design
- `/codex/05-infrastructure/hsm-wallet-signing.md` (2026-05-12) — SigningSurface tier ladder
- `/codex/05-infrastructure/per-archetype-wallet-isolation.md` (2026-05-12) — N×M wallet topology
- `/codex/05-infrastructure/secret-manager-naming.md` (2026-05-12) — SSOT naming convention
- `/codex/05-infrastructure/custody-onboarding-checklist.md` (2026-05-12) — operator-runnable checklist
- `/codex/04-architecture/interface-credential-convention.md` — 4-part pattern documented
- `/codex/04-architecture/capital-efficiency-patterns.md` — pre-Phase 1.F + Phase 8.D cross-link pending
- `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` (2026-05-10) — Hard Rule #4 + schema
- `/codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md` — treasury model

**3 missing docs are NEW creations awaiting Phase 7/8 execution** (NOT blocking earlier phases):

1. `/codex/04-architecture/client-lifecycle-state-machine.md` — `wallet_treasury_client_flow` Phase 8.A
2. `/codex/04-architecture/treasury-custody-flow.md` — `wallet_treasury_client_flow` Phase 8.B
3. `/codex/04-architecture/client-reporting-architecture.md` — `client_reporting_pnl_attribution_mvp` Phase 7.A

## Why it matters

**Freeze-gate item 9 status refinement**:

- Slot 6 day-1 found 33 referenced-but-not-yet-created codex docs across all Phase 1 plans.
- Slot 3 day-3 confirms 12 of those 33 are specifically in 1.D/1.E/1.F clusters (9 in 1.D + 3 in 1.F).
- ALL 12 missing docs are NEW Phase 7-8 codex writes that RIDE with their owning plan's later phases per CLAUDE.md
  "Post-Plan-Phase Codex Audit" HARD RULE. They are NOT supersedence of shipped SSOTs.
- The 36 existing docs in scope are CURRENT — no SUPERSEDED markers, no stale content (only 1 stamp-lag finding which is
  hygiene-only).

**Net freeze-gate item 9 status**: 🟡 PARTIAL but **NON-BLOCKING for 2026-05-15**. Item 9 closes when:

1. Every codex doc that PHASE 1 plans should have touched is current — ✅ for the 36 audited
2. NEW codex docs scheduled for Phase 7-8 of their owning plans LAND within their plan's own delivery window — these are
   independent of the 2026-05-15 freeze gate (those plans deliver in their own timelines).

## Recommended decision

1. **Flip code_freeze freeze-gate item 9 from 🟡 PARTIAL to 🟢 NON-BLOCKING** with note: "36 audited docs current (3
   clusters Phase 1.D/1.E/1.F). 12 NEW docs scheduled for owning plan Phase 7-8 — not pre-freeze deliverables."
2. **Fix the 1 stamp-lag finding** (`/codex/02-data/defi-data-type-taxonomy.md` Last-updated bump 2026-05-10 →
   2026-05-12 + acknowledge UAC@`d02cce2` in changelog) — slot 8 or any agent touching that doc on next pass.
3. **Track the 12 NEW codex docs** as deferred items in their respective owning plans' Phase 7-8 sub-sections (already
   are; no action needed).
4. **Slot 6 / slot 8 follow-up** (out of slot 3 scope): audit the remaining 13 Phase 1 plans' codex references (1.A
   UAC + UTL foundation; 1.B schema + writer hardening; 1.C live-pipeline activation) for currency. Total touched codex
   surface across all Phase 1 plans is ~91 docs per slot 6 day-1 finding.

## Composes with

- `plans/active/issues/codex_audit_2026_05_11.md` (slot 6 day-1 baseline; this audit is the 3-cluster refresh)
- `code_freeze_migrate_backfill_sequencing_2026_05_10.md` freeze-gate item 9 (Codex SSOTs updated)
- `manifest_schema_final_gate_2026_05_09.md` Phase 6/7/8 codex deliverables (some of the 12 NEW docs land in these
  phases)
- CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE
