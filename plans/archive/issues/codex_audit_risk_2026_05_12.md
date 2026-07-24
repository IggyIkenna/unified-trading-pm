---
doc_type: issue
title: Codex audit — Risk area (Phase 1.D)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
author: ikenna-codex-audit-risk-tab
source:
  [
    plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md Phase 1.D,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/kill-switch-event-bus.md,
    /codex/04-architecture/risk-rule-taxonomy.md,
    /codex/04-architecture/risk-preflight-flow.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
    /codex/04-architecture/manual-trade-booking.md,
    /codex/04-architecture/instruments-preflight-chain.md,
    unified_api_contracts/canonical/crosscutting/kill_switch.py (UAC@a7a99b5 + slot 4 2026-05-12),
    unified_api_contracts/canonical/crosscutting/circuit_breaker.py (UAC@a7a99b5),
    unified_api_contracts/canonical/crosscutting/risk_rule.py,
    unified_api_contracts/canonical/crosscutting/alerting/codes.py (KillSwitchScope SSOT),
    unified_api_contracts/internal/domain/defi/wallet_config.py (slot 4 2026-05-12),
    unified_api_contracts/internal/execution.py (WalletSpendingPreCheckResult — slot 8 2026-05-12),
    "unified_api_contracts/registry/circuit_breakers/{carry_staked_basis,arbitrage_price_dispersion}.py",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Codex audit — Risk area (Phase 1.D)

> **Severity**: P1 — pre-cutover audit per `codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 1.D. **Scope**:
> circuit breakers · kill-switch · pre-flight checks · per-archetype limits · wallet-tier kill-switch + spending caps
> (just shipped 2026-05-12 by slot 4 + slot 8) · risk-controller seam · autonomous-recovery routing. **Owner**: Ikenna
> codex-audit-risk-tab (slot 8 sub-agent); operator review for dispositions before any Phase 3 ship.

## Methodology

Read every risk-area surface (10 codex/04-architecture docs anchored above + 6 UAC source modules + 2 per-archetype
registry seeds). For each rule / pattern / claim: cite file:line, classify as KEEP / LIFT / CONSOLIDATE / DELETE / ADD,
attach a 1-line reason + suggested disposition (IMMEDIATE / PRE_CUTOVER / POST_CUTOVER).

Cross-checked the 2026-05-12 same-day shipments:

- **slot 4** — `WalletProvisioningConfig` + `SpendingCaps` + `KillSwitchId.KILL_PER_WALLET` (UAC@`d721b6a` /
  UAC@`5c2d70b`) per `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 3.C-5.
- **slot 8** — `WalletSpendingPreCheckResult` + `ManualInstructionPrecheckResponse` + audit-log surface (UAC@`1d8a059`)
  per `dart_manual_trade_booking_master_2026_05_06.md`.
- **slot 7** — 20 BreakerConfig × 2 archetypes + 20 BreakerRecoveryRule + 11 KillSwitchIds (UAC@`a7a99b5`) per
  `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 1.

Audit pass scope: ~16 distinct risk rules / contracts / drift surfaces across 4 tiers.

## Findings

### Tier 1 — Wallet-tier risk surface (today's slot 4 + slot 8 shipments) — codex catch-up gap

| #   | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Disposition                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Owner                                              | Evidence                                                                                                                                                                                 |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R-1 | **ADD** wallet-tier kill-switch section to `kill-switch-circuit-breaker.md`. Slot 4 shipped `KillSwitchId.KILL_PER_WALLET` (UAC@`d721b6a` 2026-05-12) as the FINEST-grain switch (below per-venue + per-archetype). Doc enumerates 5-axis kill-switch hierarchy (`KILL_ALL_LIVE` → `PER_ARCHETYPE` → `PER_VENUE` → `PER_ASSET_GROUP`) but never mentions the new wallet axis or its runtime-targeting semantics (`target_wallet_id` carried on `KillSwitchArmRequest`). Future readers won't know wallet-tier kill exists from this doc.                                                                                                                                                                                  | IMMEDIATE ✅ DONE @SLOT8-RISK-BATCH (Phase 3 codex edit)                                                                                                                                                                                                                                                                                                                                                                                                                                                           | slot 4 (wallet schema owner)                       | `/codex/04-architecture/kill-switch-circuit-breaker.md` (zero `wallet`/`KILL_PER_WALLET`/`SpendingCaps` mentions) + `unified_api_contracts/canonical/crosscutting/kill_switch.py:99-108` |
| R-2 | **ADD** `KILL_PER_WALLET` row to `kill-switch-event-bus.md` § "`KillSwitchId` registry — 11 closed-set members". Doc says "11 members" + "Cutover-scope kill-switches (Phase 1.C UAC@a7a99b5)" but UAC now has **12 members** (slot 4 added `KILL_PER_WALLET` 2026-05-12). The KillSwitchId table at line 49-61 is stale. Also docstring claims `KillSwitchArmRequest` has 5 fields; UAC@`d721b6a` added `target_wallet_id` (sixth field). Doc is review-blocking for any wallet-tier kill-switch consumer.                                                                                                                                                                                                               | IMMEDIATE ✅ DONE @SLOT8-RISK-BATCH (Phase 3 codex edit)                                                                                                                                                                                                                                                                                                                                                                                                                                                           | slot 4 (wallet schema owner) + ikenna (governance) | `/codex/04-architecture/kill-switch-event-bus.md:39,45-61,93-101` vs `unified_api_contracts/canonical/crosscutting/kill_switch.py:78-108,142-181`                                        |
| R-3 | **ADD** cross-link from `kill-switch-circuit-breaker.md` § "PubSub Events" to `manual-trade-booking.md` § "Wallet-tier wiring (DeFi manual trades)". Slot 8 shipped `WalletSpendingPreCheckResult` audit-log row (UAC@`1d8a059` 2026-05-12) that captures every kill-switch + spending-cap pre-trade check; the kill-switch doc never references it, so the audit-log invariant "every wallet-tier kill-switch fire produces a `WalletSpendingPreCheckResult` row" is invisible to risk-codex readers.                                                                                                                                                                                                                    | IMMEDIATE ✅ DONE @SLOT8-RISK-BATCH (Phase 3 codex edit)                                                                                                                                                                                                                                                                                                                                                                                                                                                           | slot 8 (manual-trade owner)                        | `/codex/04-architecture/kill-switch-circuit-breaker.md:340-356` + `/codex/04-architecture/manual-trade-booking.md:222-271` + `unified_api_contracts/internal/execution.py:192-232`       |
| R-4 | **ADD** Layer-2 SpendingCaps pre-flight to `risk-preflight-flow.md`. The 4-layer risk-gates flow diagram (line 25-70) shows Layer 2 = "RISK PRE-FLIGHT (risk-and-exposure-service)" → `risk_preflight()` evaluator. But slot 4 `SpendingCaps` (per-tx / per-hour / per-day / per-protocol) executes via execution-service runtime per `WalletSpendingPreCheckResult` algorithm in `manual-trade-booking.md` § "Validation algorithm" — outside the codified Layer 2 path. Either (a) document SpendingCaps as a parallel Layer 2.5 wallet-tier preflight, OR (b) absorb SpendingCaps into `risk_preflight()` so all pre-trade checks fan-in at the same layer. Currently neither — silent split-brain pre-flight surface. | PRE_CUTOVER ✅ DONE @c9511517 — `risk-preflight-flow.md` § "Layer-2.5 — wallet-tier pre-flight stack" codifies the 4-layer pre-flight stack per slot 7 (UAC@a7a99b5 circuit_breaker + kill_switch) + slot 8 Day-2 (UAC@1d8a059 WalletSpendingPreCheckResult) contracts. Ordering invariant: kill-switch FIRST short-circuits; then wallet caps (SpendingCaps) → capital allocation (CapitalAllocation) → venue eligibility (CAPABILITY_DECLARATIONS), first-fail wins. Flow diagram updated to show Layer-2.5 box. | ikenna (architecture)                              | `/codex/04-architecture/risk-preflight-flow.md:24-72` + `unified_api_contracts/internal/domain/defi/wallet_config.py:106-141` + `/codex/04-architecture/manual-trade-booking.md:230-247` |

### Tier 2 — UAC ↔ codex enum-count + member drift

| #   | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Disposition                                                                                                                                                                                      | Owner                                        | Evidence                                                                                                                                                                                |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R-5 | **CONSOLIDATE / FIX BROKEN REF** `kill_switch.py:67-72` docstring claims `KILL_PER_WALLET → KillSwitchScope.WALLET`, but `KillSwitchScope` (`alerting/codes.py:276-298`) has **no `WALLET` member** — the closed set is `GLOBAL/CLIENT/VENUE/STRATEGY/ARCHETYPE/INSTRUMENT`. Either (a) add `WALLET` to `KillSwitchScope` enum (canonical layer SSOT), OR (b) fix the docstring to say "no equivalent enum on `KillSwitchScope` — runtime-targeted via `target_wallet_id` (parallel to per-asset-group's GLOBAL-filtered convention)". Today's UAC is internally inconsistent; downstream consumers reading the docstring will fail at runtime. | IMMEDIATE 🟡 ROUTED-TO-SLOT-4 (operator-blessed disposition 2026-05-12 — UAC wallet-schema owner)                                                                                                | slot 4 (wallet schema owner)                 | `unified_api_contracts/canonical/crosscutting/kill_switch.py:67-75` vs `unified_api_contracts/canonical/crosscutting/alerting/codes.py:276-298`                                         |
| R-6 | **ADD** missing `WALLET_CAP_EXCEEDED` AlertCode. `wallet_config.py:114-117` SpendingCaps docstring promises "Cap exceedance fires `unified_api_contracts.alerting.AlertCode` `WALLET_CAP_EXCEEDED` with severity per cap class (per-tx = CRITICAL; per-hour = HIGH; per-day = WARN)", but `alerting/codes.py` has **NO `WALLET_CAP_EXCEEDED` member** (verified by grep). The promised AlertCode doesn't exist — every cap exceedance will fail to emit a typed alert.                                                                                                                                                                          | IMMEDIATE 🟡 ROUTED-TO-SLOT-4 (operator-blessed disposition 2026-05-12 — UAC wallet-schema owner)                                                                                                | slot 4 (wallet schema) + alerting maintainer | `unified_api_contracts/internal/domain/defi/wallet_config.py:114-117` (promise) vs `unified_api_contracts/canonical/crosscutting/alerting/codes.py` (no `WALLET_CAP_EXCEEDED` grep hit) |
| R-7 | **CONSOLIDATE** RiskRuleId vs codex doc count drift. `risk-rule-taxonomy.md:26-54` enumerates 22 `RiskRuleId` members (UAC@945ad5d). UAC `risk_rule.py:53-130` ships **28 members** (Phase 2.H added `FAMILY_*` 6-set). Codex table is stale by 6 members. Reviewers reading the codex see 22 → assume the registry is incomplete; reviewers reading UAC see 28.                                                                                                                                                                                                                                                                                | PRE*CUTOVER ✅ DONE @SLOT8-RISK-PRE_CUTOVER-BATCH — `risk-rule-taxonomy.md` § RiskRuleId heading now flags 28 members + 6 `FAMILY*\*`extension (Phase 2.H) + cross-ref UAC`risk_rule.py:53-130`. | risk-plan owner                              | `/codex/04-architecture/risk-rule-taxonomy.md:26-54` vs `unified_api_contracts/canonical/crosscutting/risk_rule.py:53-130`                                                              |
| R-8 | **CONSOLIDATE** `RiskRuleScope` axis count drift. `risk-rule-taxonomy.md:62-71` lists 6 scopes (`PER_ARCHETYPE` / `PER_VENUE` / `PER_ACCOUNT` / `PER_ASSET_GROUP` / `PER_CLIENT` / `GLOBAL`). UAC `risk_rule.py:172-178` ships **7 scopes** (added `PER_STRATEGY_FAMILY`). Codex table is stale; the family-aggregate axis added Phase 2.H is missing.                                                                                                                                                                                                                                                                                          | PRE_CUTOVER ✅ DONE @SLOT8-RISK-PRE_CUTOVER-BATCH — `risk-rule-taxonomy.md` § RiskRuleScope updated to 7 axes incl. `PER_STRATEGY_FAMILY` row (Phase 2.H).                                       | risk-plan owner                              | `/codex/04-architecture/risk-rule-taxonomy.md:62-71` vs `unified_api_contracts/canonical/crosscutting/risk_rule.py:172-178`                                                             |
| R-9 | **CONSOLIDATE** `RiskRuleTrigger` discriminated-union member count. `risk-rule-taxonomy.md:96-110` lists **13 trigger subtypes** (UAC@945ad5d) — same number that ships in `risk_rule.py:341-358`. KEEP — currently aligned. (Listed for completeness; counter-example to drift trend.)                                                                                                                                                                                                                                                                                                                                                         | KEEP                                                                                                                                                                                             | n/a                                          | `/codex/04-architecture/risk-rule-taxonomy.md:96-110` matches `unified_api_contracts/canonical/crosscutting/risk_rule.py:341-358`                                                       |

### Tier 3 — Pre-flight chain sequencing + pattern documentation

| # | Finding | Disposition | Owner | Evidence | | ---- |
----------------------------------------------------------------------------------------------------------------------------

|
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| -------------------------------------------------------------- | ------------------------------- |
----------------------------------------------------------------------------------------------------------------------------------------------------------------

| | R-10 | **ADD** explicit pre-flight check sequencing — call-graph across paths. | ✅ DONE @<this-commit> —
**operator-RATIFIED 2026-05-12**: Option B (shared UTL helper). Codex `risk-preflight-flow.md` § R-10 banner flipped
PROPOSED→RATIFIED. Implementation work captured as `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 4.C.C (UTL
helper) + 4.C.D (execution-service runtime wire) + 4.C.E (DART) + 4.C.F (strategy-service forward). | operator
(ratified); UTL+execution+strategy maintainers (impl) | codex § R-10 + plan Phase 4.C | | R-11 | **ADD**
capital-allocation pre-flight. Wallet-USD vs archetype-USD aggregation. | ✅ DONE @<this-commit> — **operator-RATIFIED
2026-05-12**: AND-aggregate with wallet-tier HARD floor. Codex `risk-preflight-flow.md` § R-11 banner flipped
PROPOSED→RATIFIED. Implementation work captured as Phase 4.C.C UTL helper (returns
`min(wallet_headroom, archetype_headroom)` + dual-ledger update). | operator (ratified); UTL maintainer (impl) | codex §
R-11 + plan Phase 4.C.C | | R-12 | **CONSOLIDATE** circuit-breaker-rule-taxonomy.md doc says "20 members" total
`CircuitBreakerId` (line 41 + `CircuitBreakerId | StrEnum (20 members)`at TL;DR). UAC`circuit_breaker.py:74-143`ships
exactly 20 members (10 carry_staked_basis + 10 ARBITRAGE_PRICE_DISPERSION). Per-archetype registry
seeds`unified_api_contracts/registry/circuit_breakers/{carry_staked_basis,arbitrage_price_dispersion}.py` ship 10
BreakerConfigs each (verified via grep) + matching BreakerRecoveryRules. KEEP — currently aligned. (Listed for
completeness — slot 7 work IS reflected in codex.) | KEEP | n/a |
`/codex/04-architecture/circuit-breaker-rule-taxonomy.md:41-84` matches
`unified_api_contracts/canonical/crosscutting/circuit_breaker.py:74-143` + registry seeds |

### Tier 4 — Operator-UX + autonomous-recovery surface findings

| # | Finding | Disposition | Owner | Evidence | |
---------------------------------------------------------------------------------------------------- |
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ----------------------------------------------------------------------------------- |
------------------------------------------------------------------------------------------------------------------------------------------------------

| ------------------------------------------------------------------------------- | | R-13 | **ADD**
`BreakerRecoveryMode` per-action defaults to `autonomous-recovery-matrix.md` § "Recovery Timeline" (line 192-216). The
doc shows breaker state transitions (`T+0s` → `T+3600s` cooldown cap) but doesn't show the WHO-decides-recovery question
— for `KILL_ALL` the breaker is `manual_unkill` (operator MUST click), for `BLOCK_NEW` it's `auto_cooldown`. Operator
on-call playbook reading this section will assume auto-recovery for everything; in fact the 4-set
`BreakerAction × BreakerRecoveryMode` mapping is non-trivial. Section 250-273 covers the composition but in technical
Layer-3/Layer-4 framing, NOT in operator-runbook framing. | PRE_CUTOVER ✅ DONE @SLOT8-RISK-PRE_CUTOVER-BATCH —
`autonomous-recovery-matrix.md` § "Recovery Timeline" prefixed with operator-UX note flagging `auto_cooldown` vs
`manual_unkill` boundary + cross-ref `BREAKER_RECOVERY_DEFAULTS` (UAC@a7a99b5) + per-line annotations of which timeline
lines apply to which recovery mode. | recovery-codex maintainer |
`/codex/04-architecture/autonomous-recovery-matrix.md:192-216` + `circuit-breaker-rule-taxonomy.md:115-148` | | R-14 |
**CONSOLIDATE** stale "Gap Implementation Status" table in `autonomous-recovery-matrix.md:237-246`. All 6 gaps (G1-G6)
marked PLANNED. Per slot 7 DR plan Phase 3 (8 reconcilers shipped per `kill-switch-circuit-breaker.md:218-244`) at least
G1 (multi-venue cascade), G3 (dual-failure event), G4 (position-drift auto STOP_NEW_ONLY) appear shipped — table needs
status refresh. PLANNED-when-shipped is a higher trust violation than missing-doc. | PRE_CUTOVER ✅ DONE
@SLOT8-RISK-PRE_CUTOVER-BATCH — `autonomous-recovery-matrix.md` § "Gap Implementation Status" table: G1 / G3 / G4
flipped to SHIPPED (DR Plan Phase 3) + status-refresh banner cites DR plan + `kill-switch-circuit-breaker.md:218-244`;
G2 / G5 / G6 remain PLANNED. | recovery-codex maintainer |
`/codex/04-architecture/autonomous-recovery-matrix.md:237-246` vs `kill-switch-circuit-breaker.md:218-244` (DR Phase 3
reconciler ship) | | R-15 ✅ FILED @ `plans/active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md` (Group
B) | **ADD** "scenario-synthetic vs scheduled-drill provenance distinction" to operator-facing doc.
`kill-switch-event-bus.md:73-89` codifies that `KILL_ALL_LIVE` arming MUST have provenance `OPERATOR_MANUAL` or
`SCHEDULED_DRILL` (NOT `SCENARIO_SYNTHETIC` or `BREAKER_AUTO`). But `KillSwitchId.KILL_ALL_LIVE` docstring
(`kill_switch.py:79-80`) says "Operator-only arming (provenance MUST be OPERATOR_MANUAL or SCHEDULED_DRILL)". Codex doc
(line 86) repeats this. Both are correct, but neither doc explains why `SCHEDULED_DRILL` is treated as
operator-equivalent for the most-dangerous switch. Add 1-paragraph rationale (drill-runner is operator-attended;
chaos-cron is unattended). | POST_CUTOVER | governance | `/codex/04-architecture/kill-switch-event-bus.md:73-89` +
`unified_api_contracts/canonical/crosscutting/kill_switch.py:78-80` | | R-16 ✅ FILED @
`plans/active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md` (Group A) | **ADD** runbook entry for
"wallet-tier kill-switch arm via DART operator UI". Slot 8 shipped DART `ManualTradingPanel` "DeFi Action" tab with
per-row kill-switch button (per `manual-trade-booking.md:256-260`), but no runbook doc exists for: (a) when does on-call
arm KILL_PER_WALLET vs KILL_PER_ARCHETYPE? (b) what's the rollback procedure (manual_unkill via the same button)? (c)
what audit-log line confirms the arm landed? CLAUDE.md "Runbook Execution-Owner SSOT" HARD RULE requires every
operator-runnable runbook to declare `execution.{owner,cadence,verifier,last_executed}`. Wallet-tier kill-switch has no
runbook today. | POST_CUTOVER | DART operability owner (Harsh T6) |
`/codex/04-architecture/manual-trade-booking.md:248-271` + CLAUDE.md "Runbook Execution-Owner SSOT" + no `runbook-*.md`
matching wallet-tier-kill found | | R-17 | **ADD — NEW gap surfaced by operator 2026-05-12** during R-10/R-11
ratification: **LTV (lending) + margin-ratio (perps) checks are missing from the 4-check pre-flight stack**. A wallet
with budget + allocation + kill-switch-off can still get liquidated by Layer-3-permitted action if existing leveraged
position is at 88% LTV with 90% liquidation threshold. **Expand to 5-layer stack**: kill-switch → wallet-caps →
archetype-allocation → **NEW Layer 4 position-health** → venue-eligibility. Lending:
`projected_ltv < liquidation_threshold × ltv_safety_margin (0.85)`. Perps:
`projected_margin_ratio > maintenance_margin × margin_safety_factor (1.5)`. Spot skips Layer 4. Data path: NEW PBM
`GET /positions/health?wallet_id=X` endpoint (5s cache). | ✅ DONE @<this-commit> — **operator-RATIFIED 2026-05-12** as
NEW Layer 4. Codex `risk-preflight-flow.md` § R-17 codified with 5-layer table + per-asset-type safety-margin defaults +
UAC schema extension (`WalletSpendingPreCheckResult` +4 fields: `position_health_check` / `projected_ltv` /
`projected_margin_ratio` / `position_health_denial_reason`). Implementation captured as
`api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 4.C.A (UAC) + 4.C.B (PBM endpoint) + 4.C.C (UTL helper) +
4.C.G (per-venue safety-margin tuning). | operator (ratified); UAC + PBM + UTL maintainers (impl) | codex
`risk-preflight-flow.md` § "R-17 — Position-health is missing from the pre-flight stack" + plan Phase 4.C.A-G | | R-18 |
**ADD — NEW gap surfaced by operator 2026-05-12** during R-11 ratification: **SpendingCaps shape — fixed-USD vs
proportional-to-balance vs hybrid**. Today's `SpendingCaps` are fixed-USD: too tight at $10M wallet; too loose at $50k
wallet. Options A (fixed) / B (proportional %) / C (`min(fixed, proportional)`) / C' (`max(...)`). | ✅ DONE
@<this-commit> — **operator-RATIFIED 2026-05-12**: Option C — `min(fixed, proportional)`. Fixed caps stay as hard
ops-set floor; proportional auto-tightens as wallet shrinks (anti-procyclical). Codex `risk-preflight-flow.md` § R-18
codified. Implementation captured as `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 4.C.A: add per-period
`pct_of_balance: Decimal                                                                                                                                                         | None = None`field
to`SpendingCaps`+`effective_cap(period, current_balance)` helper. | operator (ratified); slot 4 / UAC maintainer (impl)
| codex `risk-preflight-flow.md` § "R-18 — SpendingCaps shape" + plan Phase 4.C.A |

## Disposition aggregate

- **IMMEDIATE**: 6 (R-1 / R-2 / R-3 / R-5 / R-6 / counted from `IMMEDIATE` rows above) — codex doc rewrites + UAC
  internal-consistency fixes that ship in days. Two are highest-priority blocking risks: R-5 broken
  `KillSwitchScope.WALLET` reference + R-6 missing `WALLET_CAP_EXCEEDED` AlertCode (the wallet-tier risk surface won't
  emit typed alerts at all).
- **PRE_CUTOVER**: 7 (R-4 / R-7 / R-8 / R-10 / R-11 / R-13 / R-14) — architecture clean-ups composing with cutover hot
  path; pre-flight call-graph + risk-rule enum-drift + recovery-mode operator-UX.
- **POST_CUTOVER**: 2 (R-15 / R-16) — provenance-rationale addition + wallet-tier-kill runbook governance.
- **KEEP** (counter-examples, not actions): 2 (R-9 trigger-subtype count + R-12 CircuitBreakerId count). Listed to
  document where codex IS aligned with UAC, so reviewers can scope Phase 3 to the misaligned subset.

(Recount precise: IMMEDIATE=5 / PRE_CUTOVER=7 / POST_CUTOVER=2 / KEEP=2 / total findings=16.)

## Critical findings worth operator attention (BIG findings)

Two findings cross the "BIG = data correctness for ≥1 asset_group / cross-repo / contradicts workspace SSOT" bar per
CLAUDE.md "Findings Triage Discipline":

1. **R-5 broken `KillSwitchScope.WALLET` reference** — UAC `kill_switch.py:67-72` documents a `KillSwitchScope.WALLET`
   member that doesn't exist in `alerting/codes.py:276-298`. Any consumer reading the docstring + dispatching on
   `KillSwitchScope` will fail at runtime. This is internal UAC inconsistency on a slot-4 same-day shipment.
2. **R-6 missing `WALLET_CAP_EXCEEDED` AlertCode** — UAC `wallet_config.py:114-117` SpendingCaps docstring promises an
   AlertCode that doesn't ship. Every per-tx / per-hour / per-day cap exceedance will fail to emit a typed alert,
   silently degrading the alerting surface for the wallet-tier risk envelope. This is a P0 cutover-readiness gap if
   spending-caps go live before the AlertCode lands.

Both R-5 and R-6 are slot 4 follow-ups — recommend Phase 3 IMMEDIATE ship via slot 4 (NOT this audit tab — collision
risk per Findings Triage Discipline; audit tab files findings only).

## Recommended next steps

1. **Operator triage** (Phase 2.C disposition gate): confirm dispositions above; flag any disagreements as P0 ping.
2. **Phase 3 ship** (immediate items, ~1-2 AI-days, owner: slot 4 + slot 8 follow-up):
   - R-5 (KillSwitchScope.WALLET broken ref): pick (a) add WALLET enum member OR (b) fix docstring; ship to UAC.
   - R-6 (WALLET_CAP_EXCEEDED AlertCode missing): add to `alerting/codes.py` + cross-link from SpendingCaps docstring.
   - R-1 / R-2 (codex doc catch-up for KILL_PER_WALLET): wallet-tier section in `kill-switch-circuit-breaker.md` +
     refresh KillSwitchId table in `kill-switch-event-bus.md`.
   - R-3 (cross-link manual-trade-booking ↔ kill-switch-circuit-breaker): add reciprocal cross-references for the
     audit-log invariant.
3. **Phase 4 ship** (pre-cutover items, ~3-4 AI-days, owner: ikenna + risk-plan owner):
   - R-4 (Layer 2.5 SpendingCaps documentation): codify SpendingCaps as parallel preflight or absorb into
     `risk_preflight()`.
   - R-7 / R-8 (RiskRuleId + RiskRuleScope codex tables stale): refresh enumeration tables to UAC current state.
   - R-10 / R-11 (pre-flight call-graph + capital-allocation seam): codify in `risk-preflight-flow.md` or a new doc.
   - R-13 / R-14 (autonomous-recovery operator-UX + Gap Implementation Status refresh): rewrite Recovery Timeline +
     update G1-G6 status.
4. **Phase 5 file** (post-cutover backlog):
   - R-15 (provenance-rationale paragraph) + R-16 (wallet-tier-kill runbook): file as separate active plans or fold into
     existing operability plan.

## Composes with

- `plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 1.D (this audit slice).
- `plans/active/disaster_recovery_circuit_breakers_2026_05_10.md` (slot 7 ships canonical circuit-breaker taxonomy +
  reconciler suite; R-12 / R-14 reference it).
- `plans/active/risk_simulations_limits_alerting_2026_05_10.md` (risk-plan owner; R-7 / R-8 / R-10 reference it).
- `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 3-5 (slot 4 wallet schema; R-1 / R-2 / R-5 /
  R-6 reference it).
- `plans/active/dart_manual_trade_booking_master_2026_05_06.md` (slot 8 manual-trade audit-log; R-3 / R-16 reference
  it).
- `plans/active/master_to_live_defi_2026_05_23.md` Group F (capital allocation + kill-switch); R-11 references the
  per-archetype `position_cap_usd` ramp.
- `plans/active/issues/codex_audit_governance_2026_05_12.md` (Phase 1.J governance audit shipped Day-4 by slot 8 — shape
  exemplar for this doc).
