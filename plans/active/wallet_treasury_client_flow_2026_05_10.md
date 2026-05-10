---
title: Wallet / treasury / client lifecycle MVP — onboarding + custody + allocation + post-trade for cutover
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (Group F item 19 Copper+CEFFU treasury, Group G item 23 operator UX)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md
  - plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md
  - plans/active/disaster_recovery_circuit_breakers_2026_05_10.md
  - plans/active/risk_simulations_limits_alerting_2026_05_10.md
related_codex:
  - codex/04-architecture/interface-credential-convention.md
  - codex/04-architecture/capital-efficiency-patterns.md
  - codex/04-architecture/flash-loan-receiver.md
---

# Wallet / treasury / client lifecycle MVP

## Why this plan exists

May-23 cutover gates on the operator being able to: onboard 1 demo client end-to-end (deposit + KYC stub + API keys +
risk preferences + share-class subscription), wire treasury (Copper + CEFFU custody endpoints + DeFi wallet PK), allocate
capital across the 2 cutover archetypes, and run post-trade settlement (reconcile + fee accrual + statement). Today
custody endpoints are partial (stubs in execution-service config); share-class subscription doesn't exist; allocation
engine is signal-leasing-flavoured rather than per-client; post-trade is execution events without per-client rollup.
This plan ships the cutover MVP for the demo client only; multi-client + multi-fund accounting + KYC compliance + tax
reporting deferred post-cutover.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. UAC client lifecycle contracts: `ClientOnboardingState`, `ClientKYCStub`, `ClientApiKeyMaterial`,
   `ClientRiskPreferences`, `ClientShareClassSubscription`, `TreasurySource` (Copper / CEFFU / DeFi PK / sub-account).
2. Custody contracts: `CopperEndpoint`, `CEFFUEndpoint`, `DefiWalletKeyMaterial` per chain. Reuses
   `api_keys_wallets_accounts_readiness_2026_05_10` registry.
3. Share-class subscription model: per-client subscribe to per-archetype with size + drawdown preference. Reuses
   `client_reporting_pnl_attribution_mvp_2026_05_10` `ClientShareClass`.
4. Allocation engine MVP: per-client × per-archetype allocation per declared share-class subscription. For cutover —
   demo client subscribes to 100% of both archetypes.
5. Post-trade settlement event emitter: per-trade settle event + per-trade fee accrual + per-day perf-fee crystallization
   (simple flat-fee for MVP).
6. Statement emitter: daily PnL statement + position snapshot per client; emits to `gs://{pid}-client-statements/`.
7. Withdrawal flow stub: operator-initiated withdrawal request emit + reconciliation (full automation post-cutover).
8. deployment-ui Treasury tab: per-client view of subscriptions + allocations + custody pings + post-trade history.
9. Codex SSOTs: 2 NEW + 2 UPDATE.
10. Real-VM cutover-archetype dry-run: full lifecycle for demo client end-to-end.

### Non-goals (post-cutover)

- Full multi-client onboarding (production KYC integration with named provider) — cutover uses KYC stub.
- Multi-fund accounting + per-share-class P&L attribution — owned by `client_reporting` post-cutover phase.
- Multi-sig wallet ceremonies + cold-wallet rotation — current scope is hot-wallet via Secret Manager.
- Allocation across 50+ archetypes — cutover handles 2.
- Tax reporting / regulatory disclosures — multi-quarter, separate plan.
- Performance fee high-water-mark across share classes — simple flat-fee MVP only.
- Automated withdrawal execution — cutover stub captures request; execution post-cutover.

## Pre-audit / blast radius

| Repo                                  | Surface                                                                                                          |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`               | NEW: `canonical/domain/client_lifecycle/`, `canonical/domain/treasury/`                                          |
| `unified-trading-library`             | NEW: `client_lifecycle/onboarding.py`, `treasury/custody_pinger.py`, `allocation/engine.py`, `post_trade/settler.py` |
| `position-balance-monitor-service`    | UPDATE: per-client lineage on every event (composes with client-reporting plan)                                  |
| `execution-service`                   | UPDATE: custody-endpoint-pinger pre-trade; per-trade settlement event emit                                       |
| `client-reporting-api`                | NEW endpoints: `/api/clients/onboarding`, `/clients/{id}/treasury`, `/clients/{id}/subscriptions`                 |
| `deployment-ui`                       | NEW Treasury tab                                                                                                 |
| `unified-trading-pm`                  | NEW + UPDATE codex docs                                                                                          |

## Phased execution DAG

```text
0 (pre-audit) → 1 (UAC client + treasury contracts) → 2 (UTL onboarding + custody-pinger + allocation + settler) →
3 (per-service per-client lineage migration, parallel) → 4 (post-trade settlement events) →
5 (statement emitter + withdrawal stub) → 6 (deployment-api+ui Treasury tab) → 7 (demo client seed) →
8 (codex SSOTs) → 9 (real-VM cutover dry-run) → 10 (cutover gate)
```

## Phase 0 — Pre-audit (Day 1, ~0.5 AI-day, 3 parallel sub-agents)

- [ ] [AGENT] P0. **0.A Existing custody endpoint audit.** What's wired in execution-service config; what's stub vs real; what Copper + CEFFU SDK shape exists.
- [ ] [AGENT] P0. **0.B Existing position-balance per-client state audit.** Composes with client-reporting plan's audit.
- [ ] [SCRIPT] P0. **0.C Banners on cross-plan files.**

**Full-execution criterion**: § Audit findings; banners on 4 plans.

## Phase 1 — UAC client + treasury contracts (Days 2-3, ~1.5 AI-days)

- [ ] [AGENT] P0. **1.A `ClientOnboardingState` closed enum.** `DRAFT / KYC_SUBMITTED / KYC_APPROVED / DEPOSITED / SUBSCRIBED / LIVE / SUSPENDED`.
- [ ] [AGENT] P0. **1.B Client lifecycle Pydantic dataclasses.** `ClientKYCStub`, `ClientApiKeyMaterial` (refs credential-registry id), `ClientRiskPreferences`, `ClientShareClassSubscription`.
- [ ] [AGENT] P0. **1.C Treasury contracts.** `CopperEndpoint`, `CEFFUEndpoint`, `DefiWalletKeyMaterial`, `SubAccountId`. Endpoint configs reference credential-registry by id; key material never inlined.
- [ ] [AGENT] P0. **1.D `TreasurySource` closed enum.** `COPPER / CEFFU / DEFI_HOT_WALLET / SUB_ACCOUNT_<venue>`.
- [ ] [AGENT] P0. **1.E Tests.** ≥25 unit tests.

**Full-execution criterion**: UAC PR pushed; QG green.

## Phase 2 — UTL onboarding + custody-pinger + allocation + settler (Days 3-6, ~3 AI-days)

- [ ] [AGENT] P0. **2.A `client_lifecycle/onboarding.py`.** State machine: `advance(client_id, target_state, evidence)` per closed-transition graph.
- [ ] [AGENT] P0. **2.B `treasury/custody_pinger.py`.** Per-`TreasurySource` ping (Copper API / CEFFU API / DeFi wallet on-chain balance). Returns `CustodyPingResult` (reachable + balance + as-of-time).
- [ ] [AGENT] P0. **2.C `allocation/engine.py`.** Per-client × per-archetype allocator: read `ClientShareClassSubscription`, compute per-archetype size, emit `AllocationDecision` events. MVP: demo client → 100% of each cutover archetype.
- [ ] [AGENT] P0. **2.D `post_trade/settler.py`.** Per-trade settle handler: subscribes to execution events, emits `TradeSettledEvent` with per-client + per-fee + per-financing decomposition. Reuses `client_reporting` PnL attribution decomposition.
- [ ] [AGENT] P0. **2.E Tests.** ≥40 unit tests.

**Full-execution criterion**: UTL PR pushed; QG green; integration test drives onboarding state machine + ping + allocate + settle on stub data.

## Phase 3 — Per-service per-client lineage migration (Days 6-8, ~2 AI-days, 3 parallel sub-agents)

- [ ] [AGENT] P0. **3.A position-balance per-client lineage.** Reuses `client_reporting_pnl_attribution_mvp_2026_05_10` Phase 3.A migration; ensure trade-id → client-id resolution stable.
- [ ] [AGENT] P0. **3.B execution-service custody-pinger pre-trade.** Before any live order, pings the relevant custody endpoint; failure → `CustodyDisconnect` breaker fires (per DR plan).
- [ ] [AGENT] P0. **3.C Allocation engine subscription.** Strategy-service signal generator queries `allocation/engine.py` per signal to size per-client.

**Full-execution criterion**: per-repo QG green; integration test verifies pre-trade ping + allocation per-client.

## Phase 4 — Post-trade settlement events (Day 9, ~1 AI-day)

- [ ] [AGENT] P0. **4.A `TradeSettledEvent` per trade.** Emitted within named SLA of execution fill.
- [ ] [AGENT] P0. **4.B Per-day fee accrual.** UTL `post_trade/settler.py` aggregates per-client fees daily; emits `FeeAccruedEvent`.
- [ ] [AGENT] P0. **4.C Per-day perf-fee crystallization (flat MVP).** Simple flat-fee = `gross_pnl × flat_rate`; per-share-class flat rate.

**Full-execution criterion**: every paper-trade fill produces matching `TradeSettledEvent` within SLA; daily fee aggregate matches sum-of-trades.

## Phase 5 — Statement emitter + withdrawal stub (Day 10, ~0.5 AI-day)

- [ ] [AGENT] P0. **5.A Daily statement emitter.** Per-client daily PnL + position snapshot + fee accrual → `gs://{pid}-client-statements/{client_id}/{YYYY-MM-DD}/statement.parquet`.
- [ ] [AGENT] P0. **5.B Withdrawal request stub.** UI button → `WithdrawalRequestedEvent`; reconciliation rule fires; manual operator action to execute.

**Full-execution criterion**: statement parquet emitted daily; stub withdrawal event roundtrips through reconciliation rule.

## Phase 6 — deployment-api + ui Treasury tab (Days 10-11, ~1 AI-day)

- [ ] [AGENT] P0. **6.A `/api/clients/{id}/treasury` endpoint.** Returns `(treasury_sources, custody_ping_results, allocations, last_settled)`.
- [ ] [AGENT] P0. **6.B `/api/clients/{id}/subscriptions` endpoint.** Per-client share-class subscription list.
- [ ] [AGENT] P0. **6.C deployment-ui Treasury tab.** Per-client view: subscriptions + allocations + custody pings + post-trade history + withdrawal request button.
- [ ] [AGENT] P0. **6.D Playwright smoke.**

**Full-execution criterion**: operator can drive demo client treasury view end-to-end in real-cloud mode.

## Phase 7 — Demo client seed (Day 11, ~0.5 AI-day)

- [ ] [AGENT] P0. **7.A Demo client onboarding.** Walk demo client DRAFT → LIVE through onboarding state machine; KYC stub approved; deposit recorded; share-class subscriptions to both cutover archetypes.
- [ ] [AGENT] P0. **7.B Treasury wired.** Copper + CEFFU + DeFi PK pingable; sub-accounts assigned per cutover venue.

**Full-execution criterion**: demo client `ClientOnboardingState == LIVE`; treasury pings green for all sources.

## Phase 8 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [ ] [AGENT] P0. **8.A NEW `codex/04-architecture/client-lifecycle-state-machine.md`.** Onboarding states + transitions.
- [ ] [AGENT] P0. **8.B NEW `codex/04-architecture/treasury-custody-flow.md`.** Custody-source taxonomy, pre-trade ping, sub-account allocation.
- [ ] [AGENT] P0. **8.C UPDATE `interface-credential-convention.md`** — custody endpoint credentials via registry.
- [ ] [AGENT] P0. **8.D UPDATE `capital-efficiency-patterns.md`** — per-client allocation cross-link.

**Full-execution criterion**: 2 NEW + 2 UPDATE; cross-references resolve.

## Phase 9 — Real-VM cutover dry-run (Days 12-13, ~1 AI-day)

- [ ] [SCRIPT] P0. **9.A Cutover-archetype demo client dry-run.** VM `wallet-treasury-cutover-` runs full lifecycle: onboarding → treasury ping → allocation → 24h paper-trade → settle → fee accrual → daily statement → withdrawal stub.
- [ ] [AGENT] P0. **9.B Evidence capture.** Per-stage event log; statement parquet sample; fee accrual matches gross PnL × flat rate.

**Full-execution criterion**: full lifecycle log green; statement parquet emitted; reconciliation green.

## Phase 10 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **10.A Master plan rows.** Group F item 19 + Group G item 23 rows include "demo client lifecycle end-to-end green."
- [ ] [AGENT] P0. **10.B Banners removed.**

**Full-execution criterion**: master plan rows green; banners gone.

## Cross-plan coordination

- `api_keys_wallets_accounts_readiness_2026_05_10` — custody endpoint credentials live there; this plan consumes by id.
- `client_reporting_pnl_attribution_mvp_2026_05_10` — share-class + per-client lineage shared.
- `risk_simulations_limits_alerting_2026_05_10` — per-client risk preferences become per-client risk-rule limits.
- `disaster_recovery_circuit_breakers_2026_05_10` — `CustodyDisconnect` breaker fires from this plan's pinger; banner reciprocal.

## Deferred work after 2026-05-10 plan-creation session

| Item                                                | Status              | Successor / blocker                                                       |
| --------------------------------------------------- | ------------------- | ------------------------------------------------------------------------- |
| Full multi-client onboarding (production KYC)       | DEFERRED-PER-USER   | Post-cutover; cutover uses KYC stub                                       |
| Multi-fund accounting + per-share-class P&L         | DEFERRED-PER-USER   | `client_reporting` post-cutover phase                                     |
| Multi-sig wallet ceremonies + cold-wallet rotation  | DEFERRED-PER-USER   | Post-cutover; cutover uses hot-wallet via Secret Manager                  |
| Allocation across 50+ archetypes                    | DEFERRED-PER-USER   | Post-cutover; cutover handles 2                                           |
| Tax reporting / regulatory disclosures              | DEFERRED-PER-USER   | Multi-quarter; compliance plan owns                                       |
| Performance fee high-water-mark across share classes | DEFERRED-PER-USER  | Post-cutover                                                              |
| Automated withdrawal execution                      | DEFERRED-PER-USER   | Post-cutover; cutover stubs request                                       |

## Done definition

1. ✅ Phases 0-10 every checkbox flipped with evidence.
2. ✅ UAC + UTL + 4 service repos + UI + PM green.
3. ✅ Demo client end-to-end: onboarding → treasury → allocation → settle → statement; reconciliation green.
4. ✅ 2 NEW + 2 UPDATE codex docs.
5. ✅ Master plan Group F item 19 + Group G item 23 rows green.

## Audit findings

(Phase 0 sub-agents fill.)

## DONE block

(Filled at completion.)
