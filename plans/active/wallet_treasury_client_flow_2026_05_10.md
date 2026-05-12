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
estimate_class: design
estimate_baseline_ai_days: 14.8
estimate_calibrated_ai_days: 8.8
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~0.5, ~1.5, ~3, ~2, + 7 more). Class inferred from filename (design, multiplier 0.6×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
---

# Wallet / treasury / client lifecycle MVP

> **🟡 IN-FLIGHT REFACTOR — `FeeRecognitionRow` UAC type added 2026-05-10 PM.** Per
> `client_reporting_pnl_attribution_mvp_2026_05_10` Phase 1.C + codex
> [`pnl-attribution.md § Plan-vs-codex factor name mapping`](../../codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md),
> HWM crystallization is recognised via a NEW `FeeRecognitionRow` table emitted by THIS plan's Phase 4.C — NOT as a
> `PnLAttributionRow.factor` value. Phase 4.C below was extended to declare the type + emit it from Phase 5.G's
> `PerformanceFeeCrystallizedEvent`. The client-reporting-mvp plan's UI tab Phase 5.C2 reads this directly. Be aware
> when touching Phase 4.C / Phase 5.G shapes — the factor × layer attribution decoupling is a workspace-wide rule.

## Why this plan exists

May-23 cutover gates on the operator being able to: onboard 1 demo client end-to-end (deposit + KYC stub + API keys +
risk preferences + share-class subscription), wire treasury (Copper + CEFFU custody endpoints + DeFi wallet PK),
allocate capital across the 2 cutover archetypes, and run post-trade settlement (reconcile + fee accrual + statement).
Today custody endpoints are partial (stubs in execution-service config); share-class subscription doesn't exist;
allocation engine is signal-leasing-flavoured rather than per-client; post-trade is execution events without per-client
rollup. This plan ships the cutover MVP for the demo client only; multi-client + multi-fund accounting + KYC
compliance + tax reporting deferred post-cutover.

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
5. Post-trade settlement event emitter: per-trade settle event + per-trade fee accrual.
6. **Performance-fee high-water-mark accounting** (pulled into May-23 scope per operator direction 2026-05-10):
   per-(client, share-class) HWM ledger, per-period crystallization rule (operator-declared per share-class — DAILY /
   WEEKLY / MONTHLY / QUARTERLY closed enum), per-trade HWM-vs-NAV delta, `PerformanceFeeCrystallizedEvent` emit at
   period boundary. Replaces the "simple flat-fee MVP" the original draft scoped.
7. Statement emitter: daily PnL statement + position snapshot per client + HWM-ledger snapshot; emits to
   `gs://{pid}-client-statements/`.
8. **Automated withdrawal execution** (pulled into May-23 scope per operator direction 2026-05-10): per-`TreasurySource`
   withdrawal executor (Copper API / CEFFU API / DeFi wallet on-chain via `execution-service`), 2-of-N operator approval
   gate above per-treasury threshold, idempotency keys, reconciliation against treasury balance post-execution, audit
   log per withdrawal. Replaces the original "withdrawal flow stub."
9. deployment-ui Treasury tab: per-client view of subscriptions + allocations + custody pings + post-trade history +
   withdrawal queue + HWM ledger + crystallization timeline.
10. Codex SSOTs: 2 NEW + 2 UPDATE.
11. Real-VM cutover-archetype dry-run: full lifecycle for demo client end-to-end including ≥1 automated withdrawal + ≥1
    perf-fee crystallization event.
12. **Native-gas-token treasury reservation + auto-provision** (added 2026-05-12 per operator carry-staked-basis
    discipline; codified in [`pnl-attribution.md`](../../codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md)
    HARD RULE #6 "Gas fees"): every DeFi strategy preflight verifies the wallet's native-gas-token balance per chain
    (ETH on Ethereum / Arbitrum / Optimism / Base; SOL on Solana; BNB on BSC; MATIC on Polygon; AVAX on Avalanche;
    GNO on Gnosis) exceeds a configured threshold. When below threshold, auto-provision routes
    `native_gas_reservation_pct` (default **1.0%** of starting capital per DeFi strategy; tunable per chain via
    `default_basis_trade.yaml::native_gas_reservation_pct_by_chain`) into the native gas token via the spot venue.
    Hard block — strategy emits `record_failed(GAS_INSUFFICIENT)` instead of attempting a tx that will revert at
    validator level. **Treasury accounting**: native-gas reserves are NON-DEPLOYABLE — must be tracked as a separate
    `gas_reserve_balance_native` column in the per-(client, chain, wallet) treasury balance snapshot, excluded from
    `available_capital_usd` for archetype-allocation purposes.
13. **aToken / debt-token treasury discipline** (added 2026-05-12 per operator carry-staked-basis discipline; codified
    in [`pnl-attribution.md`](../../codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md) HARD RULE #4
    "DeFi lending/borrowing yield ... never APY"): Aave V3 / Compound V3 / Spark / Radiant supply positions tracked as
    actual `aToken_balance_native` per (chain, protocol, asset); borrow positions tracked as
    `debt_token_balance_native`. Position-balance-monitor reads on-chain `balanceOf(aToken_addr, wallet)` per block —
    the balance growth IS the yield (no APY proxy). Treasury balance snapshot extends with per-(chain, protocol,
    asset) aToken + debt-token rows alongside the underlying token rows; pnl-attribution-service consumes the
    snapshots' index-growth delta as CARRY_LENDING_SUPPLY / CARRY_LENDING_BORROW. **Banned**: tracking lending
    positions as the underlying token's USD value with an APY-multiplier — discards the on-chain growth signal +
    introduces discretization error.

### Non-goals (post-cutover)

- Full multi-client onboarding (production KYC integration with named provider) — cutover uses KYC stub.
- Multi-fund accounting + per-share-class P&L attribution — owned by `client_reporting` post-cutover phase.
- Multi-sig wallet ceremonies + cold-wallet rotation — current scope is hot-wallet via Secret Manager.
- Allocation across 50+ archetypes — cutover handles 2.
- Tax reporting / regulatory disclosures — multi-quarter, separate plan.

## Pre-audit / blast radius

| Repo                               | Surface                                                                                                              |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`            | NEW: `canonical/domain/client_lifecycle/`, `canonical/domain/treasury/`                                              |
| `unified-trading-library`          | NEW: `client_lifecycle/onboarding.py`, `treasury/custody_pinger.py`, `allocation/engine.py`, `post_trade/settler.py` |
| `position-balance-monitor-service` | UPDATE: per-client lineage on every event (composes with client-reporting plan)                                      |
| `execution-service`                | UPDATE: custody-endpoint-pinger pre-trade; per-trade settlement event emit                                           |
| `client-reporting-api`             | NEW endpoints: `/api/clients/onboarding`, `/clients/{id}/treasury`, `/clients/{id}/subscriptions`                    |
| `deployment-ui`                    | NEW Treasury tab                                                                                                     |
| `unified-trading-pm`               | NEW + UPDATE codex docs                                                                                              |

## Phased execution DAG

```text
0 (pre-audit) → 1 (UAC client + treasury contracts) → 2 (UTL onboarding + custody-pinger + allocation + settler) →
3 (per-service per-client lineage migration, parallel) → 4 (post-trade settlement events) →
5 (statement emitter + withdrawal stub) → 6 (deployment-api+ui Treasury tab) → 7 (demo client seed) →
8 (codex SSOTs) → 9 (real-VM cutover dry-run) → 10 (cutover gate)
```

## Phase 0 — Pre-audit (Day 1, ~0.5 AI-day, 3 parallel sub-agents)

- [ ] [AGENT] P0. **0.A Existing custody endpoint audit.** What's wired in execution-service config; what's stub vs
      real; what Copper + CEFFU SDK shape exists.
- [ ] [AGENT] P0. **0.B Existing position-balance per-client state audit.** Composes with client-reporting plan's audit.
- [ ] [SCRIPT] P0. **0.C Banners on cross-plan files.**

**Full-execution criterion**: § Audit findings; banners on 4 plans.

## Phase 1 — UAC client + treasury contracts (Days 2-3, ~1.5 AI-days)

- [ ] [AGENT] P0. **1.A `ClientOnboardingState` closed enum.**
      `DRAFT / KYC_SUBMITTED / KYC_APPROVED / DEPOSITED / SUBSCRIBED / LIVE / SUSPENDED`.
- [ ] [AGENT] P0. **1.B Client lifecycle Pydantic dataclasses.** `ClientKYCStub`, `ClientApiKeyMaterial` (refs
      credential-registry id), `ClientRiskPreferences`, `ClientShareClassSubscription`.
- [ ] [AGENT] P0. **1.C Treasury contracts.** `CopperEndpoint`, `CEFFUEndpoint`, `DefiWalletKeyMaterial`,
      `SubAccountId`. Endpoint configs reference credential-registry by id; key material never inlined.
- [ ] [AGENT] P0. **1.D `TreasurySource` closed enum.** `COPPER / CEFFU / DEFI_HOT_WALLET / SUB_ACCOUNT_<venue>`.
- [ ] [AGENT] P0. **1.E Tests.** ≥25 unit tests.

**Full-execution criterion**: UAC PR pushed; QG green.

## Phase 2 — UTL onboarding + custody-pinger + allocation + settler (Days 3-6, ~3 AI-days)

- [ ] [AGENT] P0. **2.A `client_lifecycle/onboarding.py`.** State machine: `advance(client_id, target_state, evidence)`
      per closed-transition graph.
- [ ] [AGENT] P0. **2.B `treasury/custody_pinger.py`.** Per-`TreasurySource` ping (Copper API / CEFFU API / DeFi wallet
      on-chain balance). Returns `CustodyPingResult` (reachable + balance + as-of-time).
- [ ] [AGENT] P0. **2.C `allocation/engine.py`.** Per-client × per-archetype allocator: read
      `ClientShareClassSubscription`, compute per-archetype size, emit `AllocationDecision` events. MVP: demo client →
      100% of each cutover archetype.
- [ ] [AGENT] P0. **2.D `post_trade/settler.py`.** Per-trade settle handler: subscribes to execution events, emits
      `TradeSettledEvent` with per-client + per-fee + per-financing decomposition. Reuses `client_reporting` PnL
      attribution decomposition.
- [ ] [AGENT] P0. **2.E Tests.** ≥40 unit tests.

**Full-execution criterion**: UTL PR pushed; QG green; integration test drives onboarding state machine + ping +
allocate + settle on stub data.

## Phase 3 — Per-service per-client lineage migration (Days 6-8, ~2 AI-days, 3 parallel sub-agents)

- [ ] [AGENT] P0. **3.A position-balance per-client lineage.** Reuses `client_reporting_pnl_attribution_mvp_2026_05_10`
      Phase 3.A migration; ensure trade-id → client-id resolution stable.
- [ ] [AGENT] P0. **3.B execution-service custody-pinger pre-trade.** Before any live order, pings the relevant custody
      endpoint; failure → `CustodyDisconnect` breaker fires (per DR plan).
- [ ] [AGENT] P0. **3.C Allocation engine subscription.** Strategy-service signal generator queries
      `allocation/engine.py` per signal to size per-client.

**Full-execution criterion**: per-repo QG green; integration test verifies pre-trade ping + allocation per-client.

## Phase 4 — Post-trade settlement events + HWM ledger contracts (Days 8-9, ~1.5 AI-days)

- [ ] [AGENT] P0. **4.A `TradeSettledEvent` per trade.** Emitted within named SLA of execution fill.
- [ ] [AGENT] P0. **4.B Per-day fee accrual.** UTL `post_trade/settler.py` aggregates per-client fees daily; emits
      `FeeAccruedEvent`.
- [ ] [AGENT] P0. **4.C UAC HWM + FeeRecognition contracts.** `HighWaterMarkLedgerRow` Pydantic —
      `(client_id, share_class_id, as_of, nav, prior_peak_nav, delta, crystallization_due)`. `CrystallizationCadence`
      closed enum: `DAILY / WEEKLY / MONTHLY / QUARTERLY`. Per-share-class `crystallization_cadence` declared in
      `registry/client_share_classes.py` + per-share-class `perf_fee_rate: Decimal`. **NEW `FeeRecognitionRow` Pydantic
      type added 2026-05-10 PM** (per cross-plan banner above + codex `pnl-attribution.md § Plan-vs-codex factor name
      mapping`) — `(client_id, share_class_id, period_start, period_end, recognition_type ∈ {PERFORMANCE_FEE_CRYSTALLIZATION,
      MANAGEMENT_FEE, FLAT_FEE, ...}, amount, recognized_at, source_event_id)`. Phase 5.G's
      `PerformanceFeeCrystallizedEvent` emits one `FeeRecognitionRow` per crystallization (including zero-fee
      underwater case). Stored at `gs://{pid}-client-statements/{client_id}/fee_recognition/{YYYY-MM-DD}/*.parquet`.
      `FeeRecognitionRow` is the SSOT for fee accounting; `PnLAttributionRow` (in `client_reporting_pnl_attribution_mvp`)
      keeps its factor × layer dual axis decoupled — fee recognition does NOT participate in attribution decomposition.
- [ ] [AGENT] P0. **4.D HWM-aware per-trade ledger update.** Per-trade NAV update feeds the HWM ledger row; flat-fee is
      the per-trade base, HWM-driven crystallization is the per-period top-up.

**Full-execution criterion**: every paper-trade fill produces matching `TradeSettledEvent` within SLA; daily fee
aggregate matches sum-of-trades; HWM ledger row updated per trade with `delta = max(0, nav − prior_peak_nav)`.

## Phase 5 — Statement emitter + automated withdrawal + HWM crystallization (Days 9-11, ~3 AI-days, partly parallel with Phase 4)

- [ ] [AGENT] P0. **5.A Daily statement emitter.** Per-client daily PnL + position snapshot + fee accrual + HWM-ledger
      snapshot → `gs://{pid}-client-statements/{client_id}/{YYYY-MM-DD}/statement.parquet`. Statement schema includes
      per-share-class HWM section + most-recent-crystallization summary.
- [ ] [AGENT] P0. **5.B `WithdrawalExecutor` per `TreasurySource`.** UTL `treasury/withdrawal_executor.py`: Copper API
      withdraw (signed via Copper SDK), CEFFU API withdraw, DeFi wallet on-chain withdraw routed through
      `execution-service` connector (composes with `defi_catalogue_chain_primitives_2026_05_10` for chain RPC +
      flash-loan-receiver references). Each executor returns `WithdrawalReceipt` (tx_hash / api_receipt_id / timestamp /
      amount / source / destination).
- [ ] [AGENT] P0. **5.C UAC `WithdrawalApprovalRule` Pydantic.**
      `(treasury_source, amount_bucket, threshold_amount, required_approvers: int, approver_pool: frozenset[OperatorId])`.
      Below threshold = operator-only one-click; above = 2-of-N signed approvals required.
- [ ] [AGENT] P0. **5.D Approval bus integration.** Approvals emit `WithdrawalApprovedEvent` carrying
      `(request_id, operator_id, signed_at, signature)`; only when quorum met does executor fire
      `WithdrawalExecuteRequest` against `WithdrawalExecutor`. Reuses `disaster_recovery_circuit_breakers_2026_05_10`
      `KillSwitchBus` event-bus pattern.
- [ ] [AGENT] P0. **5.E Idempotency + post-execution reconciliation.** Per-`WithdrawalRequestedEvent` `idempotency_key`;
      executor refuses double-fire. Post-execution reconciler fires within 60s: pre-treasury-balance −
      post-treasury-balance ≈ withdrawal*amount within tolerance (gas + fees accounted). Diff > tolerance fires
      `TreasuryReconcilerError` per DR plan; auto-arms `KILL_PER_TREASURY*<source>` if drift > emergency-threshold.
- [ ] [AGENT] P0. **5.F Withdrawal audit log.** Every state transition (REQUESTED → APPROVED → EXECUTED → RECONCILED →
      COMPLETED / FAILED) appends to `gs://{pid}-treasury-audit/withdrawals/{client_id}/{YYYY-MM-DD}/{request_id}.json`.
      Immutable; queryable from UI.
- [ ] [AGENT] P0. **5.G UTL `post_trade/hwm_crystallization.py`.** Per-period boundary detector: when wall-clock crosses
      period boundary per share-class `crystallization_cadence`, emit `PerformanceFeeCrystallizedEvent` with
      `(client_id, share_class_id, period_start, period_end, hwm_at_start, hwm_at_end, gross_pnl, perf_fee_amount, perf_fee_rate)`.
      Underwater client (HWM didn't increase) emits the event with `perf_fee_amount = 0` so reconciliation has the
      explicit zero-row. **Also emits a `FeeRecognitionRow`** (per Phase 4.C extension; `recognition_type =
      PERFORMANCE_FEE_CRYSTALLIZATION`, `amount = perf_fee_amount`, `source_event_id = <event uuid>`) so the
      client_reporting plan's UI tab Phase 5.C2 can render the NAV waterfall fee marker without re-deriving it.
- [ ] [AGENT] P0. **5.H HWM invariant assertion.** UTL helper: `hwm_at_end ≥ hwm_at_start` always; `perf_fee_amount > 0`
      only when `hwm_at_end > hwm_at_start`. Period-boundary crystallization fires exactly once per (client,
      share_class, period). Fails loud on violation.
- [ ] [AGENT] P0. **5.I Tests.** ≥30 unit tests for `WithdrawalExecutor` (mock Copper / CEFFU / DeFi); ≥25 unit tests
      for HWM ledger (multi-period scenarios; underwater client; period-boundary fires-once invariant; multi-share-class
      isolation).

**Full-execution criterion**: per-`TreasurySource` withdrawal executor unit-tests green; integration test drives
REQUESTED → APPROVED (2-of-N) → EXECUTED → RECONCILED end-to-end on stub treasury; HWM ledger emits per-trade row +
per-period `PerformanceFeeCrystallizedEvent` (including 0-fee underwater case); HWM invariant green; statement parquet
emitted daily including HWM section.

## Phase 6 — deployment-api + ui Treasury tab (Days 10-11, ~1 AI-day)

- [ ] [AGENT] P0. **6.A `/api/clients/{id}/treasury` endpoint — CONSUMER ROLE (ratified 2026-05-10 cross-plan audit Q7
      per most-comprehensive-owner rule).** Per-client attribution view. Consumes the canonical multi-source rollup
      shipped by [`api_keys_wallets_accounts_readiness_2026_05_10.md`](api_keys_wallets_accounts_readiness_2026_05_10.md)
      Phase 3.D — `/api/treasury/rollup` (Copper + CEFFU + venue + on-chain unified NAV). This endpoint layers per-client
      attribution (subscription % × source NAV) ON TOP of the canonical rollup; does NOT re-fetch source balances. Reads
      `(treasury_sources, custody_ping_results, allocations, last_settled)` from PBM state populated by api_keys Phase 3.
      NAV reconciliation invariant: `Σ over all clients of /api/clients/{id}/treasury.nav == /api/treasury/rollup.nav` —
      tested in Phase 6.D Playwright smoke + an additional cross-endpoint reconciliation test.
- [ ] [AGENT] P0. **6.B `/api/clients/{id}/subscriptions` endpoint.** Per-client share-class subscription list.
- [ ] [AGENT] P0. **6.C deployment-ui Treasury tab.** Per-client view: subscriptions + allocations + custody pings +
      post-trade history + withdrawal request button.
- [ ] [AGENT] P0. **6.D Playwright smoke.**

**Full-execution criterion**: operator can drive demo client treasury view end-to-end in real-cloud mode.

## Phase 7 — Demo client seed (Day 11, ~0.5 AI-day)

- [ ] [AGENT] P0. **7.A Demo client onboarding.** Walk demo client DRAFT → LIVE through onboarding state machine; KYC
      stub approved; deposit recorded; share-class subscriptions to both cutover archetypes.
- [ ] [AGENT] P0. **7.B Treasury wired.** Copper + CEFFU + DeFi PK pingable; sub-accounts assigned per cutover venue.

**Full-execution criterion**: demo client `ClientOnboardingState == LIVE`; treasury pings green for all sources.

## Phase 8 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [ ] [AGENT] P0. **8.A NEW `codex/04-architecture/client-lifecycle-state-machine.md`.** Onboarding states +
      transitions.
- [ ] [AGENT] P0. **8.B NEW `codex/04-architecture/treasury-custody-flow.md`.** Custody-source taxonomy, pre-trade ping,
      sub-account allocation.
- [ ] [AGENT] P0. **8.C UPDATE `interface-credential-convention.md`** — custody endpoint credentials via registry.
- [ ] [AGENT] P0. **8.D UPDATE `capital-efficiency-patterns.md`** — per-client allocation cross-link.

**Full-execution criterion**: 2 NEW + 2 UPDATE; cross-references resolve.

## Phase 9 — Real-VM cutover dry-run (Days 12-13, ~1 AI-day)

- [ ] [SCRIPT] P0. **9.A Cutover-archetype demo client dry-run.** VM `wallet-treasury-cutover-` runs full lifecycle:
      onboarding → treasury ping → allocation → 24h paper-trade → settle → fee accrual + HWM-ledger update → daily
      statement → ≥1 automated withdrawal (REQUESTED → APPROVED 2-of-N → EXECUTED → RECONCILED) → ≥1 forced
      period-boundary crystallization with non-zero perf-fee + ≥1 underwater zero-fee crystallization.
- [ ] [AGENT] P0. **9.B Evidence capture.** Per-stage event log; statement parquet sample; HWM ledger sample; withdrawal
      audit log sample; reconciliation green.

**Full-execution criterion**: full lifecycle log green; statement parquet emitted; HWM invariant green across forced
multi-period scenario; ≥1 withdrawal completed end-to-end with reconciliation diff < tolerance; ≥1 perf-fee
crystallization event emitted with `perf_fee_amount > 0`; ≥1 underwater crystallization with `perf_fee_amount == 0`.

## Phase 10 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **10.A Master plan rows.** Group F item 19 + Group G item 23 rows include "demo client lifecycle
      end-to-end green."
- [ ] [AGENT] P0. **10.B Banners removed.**

**Full-execution criterion**: master plan rows green; banners gone.

## Cross-plan coordination

- `api_keys_wallets_accounts_readiness_2026_05_10` — custody endpoint credentials live there; this plan consumes by id.
- `client_reporting_pnl_attribution_mvp_2026_05_10` — share-class + per-client lineage shared.
- `risk_simulations_limits_alerting_2026_05_10` — per-client risk preferences become per-client risk-rule limits.
- `disaster_recovery_circuit_breakers_2026_05_10` — `CustodyDisconnect` breaker fires from this plan's pinger; banner
  reciprocal.

## Deferred work after 2026-05-10 plan-creation session

| Item                                                     | Status                        | Successor / blocker                                                |
| -------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| Full multi-client onboarding (production KYC)            | DEFERRED-PER-USER             | Post-cutover; cutover uses KYC stub                                |
| Multi-fund accounting + per-share-class P&L              | DEFERRED-PER-USER             | `client_reporting` post-cutover phase                              |
| Multi-sig wallet ceremonies + cold-wallet rotation       | DEFERRED-PER-USER             | Post-cutover; cutover uses hot-wallet via Secret Manager           |
| Allocation across 50+ archetypes                         | DEFERRED-PER-USER             | Post-cutover; cutover handles 2                                    |
| Tax reporting / regulatory disclosures                   | DEFERRED-PER-USER             | Multi-quarter; compliance plan owns                                |
| ~~Performance fee high-water-mark across share classes~~ | **PULLED FORWARD 2026-05-10** | Now in scope per operator direction; see Phase 4.C-D + Phase 5.F-I |
| ~~Automated withdrawal execution~~                       | **PULLED FORWARD 2026-05-10** | Now in scope per operator direction; see Phase 5.B-F               |

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
