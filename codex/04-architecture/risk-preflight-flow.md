---
doc_type: codex-ssot
title: Risk Pre-Flight Flow
summary:
  The Layer-2 order-submission path — the UTL risk_preflight(order, context) helper every order goes through (called by
  both strategy-service before sizing AND execution-service before venue submit, no caching), its aggregation semantics
  (any-BLOCK-wins, min-of-scale_factors, MONITOR/TEST_ONLY passthrough), plus the DeFi-only Layer-2.5 wallet-tier stack
  (5 checks — kill-switch → wallet caps → archetype allocation → position-health → venue eligibility; short-circuit).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [risk, execution, strategy, defi, kill-switch]
related:
  [
    /codex/04-architecture/risk-rule-taxonomy.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md,
  ]
created: 2026-05-11
authoritative_for:
  [risk pre-flight order-submission flow, risk_preflight aggregation semantics, Layer-2.5 wallet-tier pre-flight stack]
referenced_by:
  [
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/risk-rule-taxonomy.md,
  ]
owner:
last_reviewed: 2026-05-20
code_refs:
---

# Risk Pre-Flight Flow

> **⚠️ Migration note (2026-05-20)**: `risk-and-exposure-service` is now `strategy_service/risk/` (sub-package of
> `strategy-service`). `position-balance-monitor-service` is now `strategy_service/position/`. CLI:
> `strategy-service --operation risk-monitor`. See
> [`strategy-service-architecture.md`](strategy-service-architecture.md).

> **What it is:** The order-submission path that every instruction takes from strategy emission to venue submission. The
> UTL helper `risk_preflight(order, context) -> RiskPreflightResult` is the single integration point — every order goes
> through it BEFORE reaching execution-service. Returns one aggregate decision: pass / scale-down (with min-aggregated
> factor) / block (with reason set) / test-only (with route-divert annotation). Companion to
> [`risk-rule-taxonomy.md`](risk-rule-taxonomy.md).

## TL;DR

`risk_preflight()` lives at **Layer 2** of the
[4-layer risk-gates model](/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md). Strategy-service calls it
BEFORE sizing the order; execution-service calls it BEFORE submitting to the venue. (Both calls happen — defense in
depth — but strategy-side caching is forbidden because portfolio state changes per tick.) The helper iterates every
`RiskRule` whose scope matches `(archetype_id, venue, account_id, asset_group, client_id)` from the registry, evaluates
each via `evaluate_rule(rule, context)`, and aggregates the per-rule consequences into a single `RiskPreflightResult`.
Block aggregates as "any BLOCK wins"; scale-down aggregates as "min of all scale_factors"; monitor and test-only are
passthrough annotations.

## Flow diagram

```
┌────────────────────────────────────────────────────────────────┐
│  STRATEGY GENERATOR                                             │
│  - Produces target position delta + signal direction            │
│  - Calls risk_preflight(intended_order, ctx) BEFORE sizing      │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  Layer 1 — STRATEGY SELF-CHECK (intra-service)                  │
│  Local checks; cheap; catches bugs early.                       │
│  Fails → drop instruction, emit REJECTED_SELF_CHECK.            │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  Layer 2 — RISK PRE-FLIGHT (risk-and-exposure-service)          │
│  risk_preflight(order, context) →                               │
│    for rule in applicable_rules(scope_axes):                    │
│        result = evaluate_rule(rule, context)                    │
│    aggregate(results) → RiskPreflightResult                     │
└────────────────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┬───────────┐
              ▼           ▼           ▼           ▼
           BLOCK     SCALE_DOWN    MONITOR    TEST_ONLY
              │           │           │           │
              ▼           ▼           ▼           ▼
        INSTRUCTION_  RESIZED     instruction   route-divert
        REJECTED_     EXECUTION   passes        to matching
        RISK          (scale_     unchanged     engine (no
        (alert+halt)  factor=min) + advisory    live venue)
              │           │           │           │
              ▼           ▼           ▼           ▼
           — END —  Layer 2.5     Layer 2.5    Layer 2.5
                    wallet-tier   wallet-tier  wallet-tier
                    (DeFi only;   (DeFi only)  (DeFi only)
                    skipped for
                    CeFi/TradFi)
                          │           │           │
                          ▼           ▼           ▼
                  ┌──────────────────────────────────────────┐
                  │  Layer 2.5 — WALLET-TIER PRE-FLIGHT       │
                  │  (DeFi orders + manual-trade booking)     │
                  │  1. Kill-switch check (KillSwitchBus)     │
                  │  2. Wallet caps (SpendingCaps; 4 caps)    │
                  │  3. Capital allocation (CapitalAllocation)│
                  │  4. Venue eligibility (CAPABILITY_DECLS)  │
                  │  Strict ordered short-circuit; kill-switch│
                  │  first short-circuits; first-fail wins.   │
                  └──────────────────────────────────────────┘
                          │           │           │
                          ▼           ▼           ▼
                      Layer 3     Layer 3     matching engine
                      execution   execution   simulated fill
                      pre-trade   pre-trade
                          │           │
                          ▼           ▼
                      Layer 4 — VENUE-SIDE RISK
                      (external; venue may reject)
                          │
                          ▼
                      ORDER_FILLED / ORDER_REJECTED_VENUE
                      (Layer 4 → ErrorAction classification)
```

## Layer-2.5 — wallet-tier pre-flight stack (DeFi + manual-trade booking)

> **Codified 2026-05-12 per Risk audit R-4** (issue doc `plans/archive/issues/codex_audit_risk_2026_05_12.md`). Lifts
> the 4-layer wallet-tier pre-flight stack already shipped via slot 7 (circuit_breaker + kill_switch contracts at
> `UAC@a7a99b5` — 20 `BreakerConfig × 2 archetypes` + 20 `BreakerRecoveryRule` + 11 `KillSwitchIds`) and slot 8 Day-2
> (`WalletSpendingPreCheckResult` at UAC@`1d8a059` — kill-switch + caps validation). Lives BETWEEN Layer 2
> (`risk_preflight()`) and Layer 3 (execution pre-trade). Engaged whenever `ManualInstruction.wallet_id` is non-empty
> (DeFi manual trades) AND for every DeFi strategy-emitted order; CeFi / TradFi / sports / prediction orders skip Layer
> 2.5 entirely (no wallet-tier surface).

### Why a sub-layer (and not absorbed into Layer 2)

Layer 2 `risk_preflight()` is the **portfolio-state-driven** envelope (concentration / drawdown / VaR / correlation —
inputs come from position-balance-monitor + risk-and-exposure-service). Layer 2.5 is the **wallet-state-driven**
envelope (kill-switch armed-state + per-tx / per-hour / per-day / per-protocol USD caps — inputs come from
`KillSwitchBus` most-recent state + per-wallet `SpendingCaps`). The two surfaces have different SSOTs, different
ownership (Layer 2 = risk-and-exposure-service; Layer 2.5 = execution-service runtime + DART manual-trade endpoint), and
different update cadences (portfolio re-evaluated per tick; wallet state re-evaluated per kill-switch event + per-wallet
rolling-window query). Codifying them as parallel sub-layers keeps both SSOTs honest. See R-11 cross-link in
`plans/archive/issues/codex_audit_risk_2026_05_12.md` for the wallet-USD ↔ archetype-USD cap-aggregation architecture
call (still operator-gated as of 2026-05-12).

### The 4 checks (in order)

The Layer-2.5 stack runs as a **strict ordered short-circuit** — every check below is gated by the prior check passing:

1. **Kill-switch check (most-recent state from KillSwitchBus)** — load `WalletProvisioningConfig.kill_switch_id`; query
   the live `KillSwitchBus` for the most-recent state on that ID. If armed (per `KillSwitchId.KILL_PER_WALLET` semantics
   from UAC `canonical/crosscutting/kill_switch.py`), set `kill_switch_armed=True`, `passed=False`,
   `denial_reason="kill_switch_armed"`, and **short-circuit** — skip checks 2/3/4. This is the FIRST check because a
   wallet whose kill-switch is armed must NEVER spend (cap-headroom is irrelevant). SSOT: slot 7 `KillSwitchBus`
   contract at `UAC@a7a99b5`; slot 4 `KillSwitchId.KILL_PER_WALLET` member at `UAC@d721b6a`.
2. **Wallet-tier check (`WalletSpendingPreCheckResult` per slot 8 Day-2)** — populate `per_tx_check` / `per_hour_check`
   / `per_day_check` / `per_protocol_check` fields by calling `SpendingCaps.is_within_per_tx(amount_usd)` and querying
   position-balance-monitor-service for rolling 1h / 24h spend on this wallet. Aggregate
   `passed = all 4 cap checks True`. SSOT: slot 8 Day-2 `WalletSpendingPreCheckResult` at UAC@`1d8a059`
   (`unified_api_contracts/internal/execution.py:192-232`) + `SpendingCaps` at
   `unified_api_contracts/internal/domain/defi/wallet_config.py:106-141`. Full validation algorithm in
   [`manual-trade-booking.md`](manual-trade-booking.md) § "Wallet-tier wiring (DeFi manual trades)" §§ "Validation
   algorithm".
3. **Capital allocation check (`CapitalAllocation` per cross_cutting #3)** — confirm the (archetype × wallet) routing
   target's `position_cap_usd` + `kill_switch_drawdown_pct` ramp accepts this order size at current drawdown. Distinct
   envelope from check (2) — wallet caps are spending-velocity bounds; archetype caps are exposure-ceiling bounds.
   Aggregation semantics (subsume-vs-AND-aggregate) is operator-gated per R-11. Until that call lands, the conservative
   default is **AND-aggregate** (most-restrictive wins, mirroring Layer 2 SCALE_DOWN min-aggregation).
4. **Venue eligibility check (UAC `CAPABILITY_DECLARATIONS`)** — confirm `manual_instruction.venue` (or the
   strategy-selected venue for non-manual flows) is declared eligible for this archetype × asset_group × operational
   mode. SSOT: UAC `unified_api_contracts/registry/capability_declarations/*.py` registered through
   `unified_api_contracts.registry.CAPABILITY_DECLARATIONS`. Failure → `denial_reason="venue_not_eligible"`.

### Ordering invariant (strict)

**Kill-switch check FIRST short-circuits**; if armed, the remaining 3 checks DO NOT run (their inputs are not collected,
their fields stay `None` on the resulting `WalletSpendingPreCheckResult`). If kill-switch passes, the remaining 3 checks
run in order (2 → 3 → 4); each one's `denial_reason` short-circuits the rest. The aggregate is "first check to fail
wins" (NOT min-aggregation across all 4 — caps + capital + eligibility are categorically distinct failure modes that
don't compose into a single "factor").

### Composition with Layer 2

Layer 2 `risk_preflight()` runs FIRST. If Layer 2 returns `decision="block"`, Layer 2.5 is skipped (block wins). If
Layer 2 returns `pass` / `scale_down` / `monitor` / `test_only`, the (possibly scaled) order proceeds to Layer 2.5. A
Layer 2.5 failure surfaces as `INSTRUCTION_REJECTED_WALLET_PRECHECK` (audit-log row written via
`ManualInstructionAuditLog`; PubSub event emitted) and the order never reaches Layer 3. The two layers cannot
"reconcile" — a Layer 2 `scale_down` followed by Layer 2.5 `passed=False` is still a hard block; the scale-down factor
is discarded.

### Where Layer 2.5 surfaces in operator playbooks

- **DART manual-trade panel** → operator sees the pre-check echo BEFORE submit (per
  [`manual-trade-booking.md`](manual-trade-booking.md) § "UI surface" "Pre-submit validation echo" via
  `POST /manual/instruction/precheck` dry-run).
- **Strategy-emitted DeFi orders** → execution-service runtime runs the same 4-check algorithm before venue submission;
  a denial routes to `INSTRUCTION_REJECTED_WALLET_PRECHECK` lifecycle event + the appropriate `KILL_SWITCH_*` or cap
  alert.
- **Audit log** → every Layer-2.5 evaluation (pass OR fail) writes a `WalletSpendingPreCheckResult` row keyed by
  `(wallet_id, archetype_id, submitted_by, timestamp)`; downstream reconcilers + batch-live recon read this row to
  verify "every wallet-tier kill-switch fire produced a `WalletSpendingPreCheckResult` row" (the invariant cross-linked
  from R-3 in the same audit doc).

### Anti-patterns specific to Layer 2.5

- **Don't reorder the 4 checks.** Kill-switch must always be first (an armed wallet should not even compute cap headroom
  — that wastes a position-balance-monitor RPC). Venue eligibility runs last (cheapest check).
- **Don't merge Layer 2.5 into Layer 2.** Different SSOTs (`SpendingCaps` ≠ `RiskRule`), different evaluators
  (execution-service runtime ≠ risk-and-exposure-service `evaluate_rule`), different update cadences.
- **Don't skip Layer 2.5 for strategy-emitted orders.** The wallet-tier surface is wallet-scope-bound, not
  manual-trade-scope-bound. Strategy emission MUST run the same 4-check pipeline before venue submission.
- **Don't cache the kill-switch state.** Query `KillSwitchBus` per pre-check; the bus has microsecond-latency local
  state + the safety-critical invariant is "fresh state per pre-check."

### R-10 — Where the 4 checks live (call-graph implementation)

> **✅ RATIFIED 2026-05-12 by operator** (slot 8 audit recommendation accepted). **Canonical: Option B — shared UTL
> helper.** A single
> `unified_trading_library.risk_preflight.run_wallet_preflight_checks(instruction) -> WalletSpendingPreCheckResult`
> function lives in UTL. Every consumer (execution-service runtime + DART `/manual/instruction` endpoint +
> strategy-service forward path) calls it. The helper owns the strict-ordered short-circuit + audit-log row write.
> **Rejected alternatives**: Option A (per-service implementation) — drift risk between services; Option C (dedicated
> `preflight-service` microservice) — +20-50ms RPC hop unacceptable for live DeFi.
>
> **Why Option B**: matches the workspace's existing UTL-helper-as-SSOT pattern (e.g. `ApiKeyReloader`,
> `ManifestWriter`, `availability_stamping`); zero network hop; single update point when invariants evolve; basedpyright
> catches the "forgot to call it" case (every consumer's type-checker requires the helper). The discipline cost of
> Option A (forgetting one check across N services) is a known failure mode in this workspace (see Findings Triage
> incidents).

### R-11 — Wallet-USD vs archetype-USD aggregation semantics

> **✅ RATIFIED 2026-05-12 by operator** (slot 8 audit recommendation accepted). **Canonical: AND-aggregate with
> wallet-tier as HARD floor.** The pre-flight stack returns `min(wallet_headroom, archetype_headroom)` as the allowed
> action size; BOTH ledgers update on the spend (wallet daily-spend AND archetype daily-spend tick down by the spent
> amount). **Multi-archetype wallets** (e.g. 3 archetypes share `hot-trading-eth-1`): the wallet daily-spend aggregates
> ALL archetypes' activity on that wallet; per-archetype ledgers stay archetype-scoped. **Rejected alternatives**:
> Subsume (tighter-wins-but-only-track-the-loser) — loses visibility of the looser axis's spend; Hierarchical (one axis
> primary) — defeats the safety-net role of the non-primary axis.
>
> **Why AND-aggregate**: wallet caps are the _operational_ safety net (set by ops/treasury); archetype allocations are
> the _strategy budget_ (set by strategy/risk). Both should constrain; both should track; pre-flight returns the binding
> constraint as the allowed action size. This matches how slot 4's `SpendingCaps` are already shaped (per-tx / per-hour
> / per-day / per-protocol — designed as hard floors regardless of strategy budget).

### R-17 — Position-health is missing from the pre-flight stack (NEW 2026-05-12)

> **🟢 NEW gap surfaced by operator 2026-05-12** during R-10/R-11 ratification (re-numbered from initial R-12 draft to
> avoid collision with existing risk-audit R-12 circuit-breaker finding; this is risk-area finding R-17 in the issue
> doc). **Layer-2.5 expanded from 4 → 5 checks**: position-health (LTV for lending; margin ratio for perps) was missing.
> A wallet can have spending budget
>
> - archetype allocation + kill-switch off + venue allowed, but the existing leveraged position is at 88% LTV on Aave
>   with 90% liquidation threshold — one more borrow tips it over. Today's pre-flight doesn't catch this.

The expanded 5-layer stack:

| Layer | Check                                | Data source                                                              | Failure mode prevented               |
| ----- | ------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------ |
| 1     | Kill-switch armed                    | `KillSwitchBus` (per slot 7 UAC@`a7a99b5`)                               | Operator panic-stop bypass           |
| 2     | Wallet caps headroom                 | `WalletProvisioningConfig.SpendingCaps` (per slot 4 UAC@`d721b6a`)       | Daily / hourly / per-tx blow-through |
| 3     | Archetype allocation headroom        | `CapitalAllocation` (per cross_cutting #3 Tab 6.B)                       | Archetype budget exhaustion          |
| 4     | **Position health** _(NEW per R-17)_ | PBMS rolling state + on-chain query                                      | Liquidation from over-leverage       |
| 5     | Venue eligibility                    | `CAPABILITY_DECLARATIONS` + `WalletProvisioningConfig.allowed_protocols` | Trade on unauthorized venue          |

**Layer 4 specifics**:

- **Lending positions** (Aave / Compound / Morpho / Spark / Radiant / lst protocols):
  `projected_ltv = (current_debt_usd + new_borrow_usd) / collateral_usd < liquidation_threshold × ltv_safety_margin`.
  Recommended `ltv_safety_margin = 0.85` (15% buffer below liquidation; tunable per-protocol).
- **Perp positions** (Hyperliquid / Aster / Drift / Binance / Deribit / Bybit / OKX):
  `projected_margin_ratio = (margin + unrealized_pnl) / (position_value + new_notional) > maintenance_margin × margin_safety_factor`.
  Recommended `margin_safety_factor = 1.5` (50% buffer above maintenance margin; tunable per-venue).
- **Spot trades** (Uniswap swaps / spot CeFi): skip Layer 4 (no leverage, no liquidation; only Layers 1-3+5 apply).
- **Atomic transactions** (flash-loan-receiver): Layer 4 evaluates the END state after all sub-operations (loan + arb +
  repay); if end-state is unhealthy, reject the atomic.

**Layer 4 data path**: `position-balance-monitor-service` exposes a `GET /positions/health?wallet_id=X` query returning
current `{ltv, margin_ratio, liquidation_threshold, maintenance_margin}` per open position. UTL
`run_wallet_preflight_checks` (per R-10) calls this query as the Layer-4 step; cache 5s to avoid hammering PBM
(kill-switch + spending caps are zero-RPC inline checks; position-health is the only network hop in the pre-flight
stack).

**WalletSpendingPreCheckResult extension** (UAC `internal/execution.py`): add 4 fields:

- `position_health_check: bool | None` — `None` if Layer 4 skipped (spot trade); `True/False` per evaluation
- `projected_ltv: Decimal | None` — populated for lending operations
- `projected_margin_ratio: Decimal | None` — populated for perp operations
- `position_health_denial_reason: str` — closed-set: `"projected_ltv_breach"` / `"projected_margin_breach"` / empty

Ordering invariant in the strict-short-circuit: 1 → 2 → 3 → 4 → 5 (kill-switch always first; venue-eligibility always
last; position-health between budget checks + venue-check since it's a derived-position-state check, not a static-config
check).

### R-18 — SpendingCaps shape: fixed-USD vs proportional-to-balance vs hybrid (NEW 2026-05-12)

> **✅ RATIFIED 2026-05-12 by operator** (slot 8 audit recommendation accepted; re-numbered from initial R-13 draft to
> avoid collision with existing risk-audit R-13 finding). **Canonical: Option C — `min(fixed, proportional)`.**
> `SpendingCaps` extended with per-period `pct_of_balance: Decimal | None = None` field; pre-flight Layer 2 computes
> `effective_cap = min(per_period_usd, pct_of_balance × current_balance)` when both present (either may be None — only
> the populated one binds). Fixed caps stay as ops-set absolute floor; proportional auto-tightens as wallet shrinks
> (anti-procyclical for losses).

Today's `WalletProvisioningConfig.SpendingCaps` (per slot 4 UAC@`d721b6a`) carries fixed-USD values:
`per_tx_usd: Decimal | None` / `per_hour_usd: Decimal | None` / `per_day_usd: Decimal | None` /
`per_protocol_usd: dict[str, Decimal]`.

The operator question: should these be fixed, proportional-to-balance, or hybrid? Treasury-practice tradeoff:

| Design                                     | Behaviour                               | Pros                                                                     | Cons                                                                          |
| ------------------------------------------ | --------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| **A — Fixed USD** (today)                  | `per_day = $100k` regardless of balance | Simple; protects absolute blow-through                                   | Wrong at scale — $100k/day too tight on $10M wallet, too loose on $50k wallet |
| **B — Proportional**                       | `per_day = 5% × balance`                | Auto-scales with wallet                                                  | If balance → 0, cap → 0 (stuck); procyclical (rapid drawdowns shrink cap)     |
| **C — Hybrid `min(fixed, proportional)`**  | `per_day = min($100k, 5% × balance)`    | Fixed = hard floor (anti-blow-through) + proportional = anti-procyclical | Two knobs to tune                                                             |
| **C' — Hybrid `max(fixed, proportional)`** | `per_day = max($100k, 5% × balance)`    | Small wallets operate normally even if proportional = tiny               | Loosens safety for big wallets                                                |

Slot 8 audit recommendation: **C — `min(fixed, proportional)`** — fixed caps stay as ops-set floor; proportional
auto-tightens as wallet shrinks (anti-procyclical for losses). Schema change: add per-period
`pct_of_balance: Decimal | None = None` field to `SpendingCaps`; pre-flight computes
`min(per_period_usd, pct_of_balance × current_balance)` if both present.

✅ **Operator-ratified Option C 2026-05-12.** Decision unblocks slot 4 schema update + R-17 pre-flight Layer 4 wiring
(Layer 4 reads `SpendingCaps` effective cap via the new `effective_cap(period, current_balance)` helper).

## Aggregation semantics

`risk_preflight()` returns a single `RiskPreflightResult`:

```python
@dataclass(frozen=True)
class RiskPreflightResult:
    decision: Literal["pass", "scale_down", "block", "test_only"]
    scale_factor: Decimal | None  # None unless decision == "scale_down"; else min of all SCALE_DOWN fires
    blocked_by: list[RiskRuleFiredEvent]  # non-empty iff decision == "block"
    scaled_by: list[RiskRuleFiredEvent]  # SCALE_DOWN fires that contributed to scale_factor
    monitored: list[RiskRuleFiredEvent]  # passthrough advisory fires (decision unchanged)
    test_only_routed_by: RiskRuleFiredEvent | None  # at most one rule can route to TEST mode
    decision_layer: Literal["LAYER_2"]
```

### `BLOCK` semantics

Any `BLOCK` rule fire causes `decision = "block"`. ALL blocking rules are surfaced in `blocked_by` (not just the first
one) — operator dashboards show every reason simultaneously. The instruction never reaches Layer 3. Emits
`INSTRUCTION_REJECTED_RISK` + one `RiskRuleFiredEvent` per blocking rule + per-rule `RISK_RULE_BLOCKED` AlertCode (or
generic `PREFLIGHT_FAILED` if the rule predates the per-rule code addition).

Aggregation of multiple blocks:

- All block reasons surfaced (no first-wins).
- Severity = `max(rule.alerting_severity for rule in blocked_by)`.
- Kill-switch engagement: if any `blocked_by` rule has `triggers_kill_switch: true` AND per-rule threshold count met,
  the corresponding kill-switch trigger fires per the cross-product table in
  [risk-rule-taxonomy.md](risk-rule-taxonomy.md).

### `SCALE_DOWN` semantics

Multiple `SCALE_DOWN` rules can fire on the same instruction. Aggregation is **min of all scale_factors** — the
most-restrictive rule wins.

```python
# Three rules fire on the same instruction:
# rule_A: scale_factor = 0.80 (concentration cap suggests 20% reduction)
# rule_B: scale_factor = 0.50 (correlation cap suggests 50% reduction)
# rule_C: scale_factor = 0.90 (slippage budget suggests 10% reduction)
# Aggregate: 0.50 — rule_B wins.
```

Order size = `intended_size × aggregate_scale_factor`. Emits `INSTRUCTION_ACCEPTED_PREFLIGHT` with `size_adjusted: true`
annotation + one `RiskRuleFiredEvent` per SCALE_DOWN rule + `RISK_RULE_SCALED_DOWN` AlertCode per rule + Layer 3 emits
`RESIZED_EXECUTION` on actual venue submission.

A `BLOCK` rule firing alongside any number of `SCALE_DOWN` rules always wins (decision = "block"; scale_factor
discarded).

### `MONITOR` semantics

Passthrough decision; instruction is approved unchanged. Each MONITOR rule fire emits `RiskRuleFiredEvent` with the
declared severity (INFO or WARN) and `RISK_RULE_MONITOR_FIRED` AlertCode. Operator dashboards aggregate MONITOR events
for trend visibility; no instruction-level effect.

MONITOR can coexist with any other decision — multiple MONITOR fires alongside a BLOCK, SCALE_DOWN, or pure pass are
fine. All MONITOR events surfaced via `monitored` list.

### `TEST_ONLY` semantics

At most one rule can route an instruction to TEST_ONLY mode (the registry enforces uniqueness — multiple TEST_ONLY rules
on the same instruction is a registry-validation error caught at UAC PR time). When a TEST_ONLY rule fires,
`decision = "test_only"`, the instruction is tagged `mode=TEST`, and Layer 3 routes it to the matching engine instead of
the live venue. Fills are simulated — no real venue contact, no real capital movement.

Use cases: shadow-trading a new archetype against a paper account before live; A/B testing two model versions in
parallel without risking capital on the challenger; smoke-testing a venue integration end-to-end with synthetic fills.

A TEST_ONLY route is incompatible with BLOCK (block wins; TEST_ONLY discarded) but composable with SCALE_DOWN (the
TEST-routed instruction is sized down before going to the matching engine) and MONITOR (advisory events still emit on
the TEST-routed instruction).

## Integration points

### Strategy-service call site

Strategy-service queries `risk_preflight()` BEFORE sizing the order. If the result is `block`, the strategy drops the
intended order and emits `INSTRUCTION_REJECTED_RISK`. If `scale_down`, the strategy sizes the order at
`intended_size × scale_factor` and continues. If `monitor` or `test_only`, the strategy proceeds normally; downstream
side-effects (route divert, advisory events) are handled by the helper + Layer 3 wiring.

### Execution-service call site

Execution-service ALSO calls `risk_preflight()` immediately before venue submission (defense in depth — portfolio state
may have changed between strategy sizing and execution submission, and a different agent's instruction may have breached
the same scope). This is the authoritative check; strategy-side caching is forbidden. If the second preflight returns
`block`, execution-service emits `INSTRUCTION_REJECTED_RISK` from its own service and the order never reaches the venue.

### Kill-switch bus integration

`BLOCK` aggregates with `triggers_kill_switch: true` may engage the kill-switch bus. The engagement is one-directional:
risk preflight emits the trigger event (e.g. `MAX_DRAWDOWN_BREACH` per `RiskRuleTrigger` type); the kill-switch state
machine in execution-service consumes the event and transitions per its own rules — see
[`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md). `SCALE_DOWN`, `MONITOR`, and `TEST_ONLY`
consequences do not engage kill-switch.

For the related (but distinct) **risk-rule-fire → breaker-arm escalation seam**, see
[`risk-breaker-seam.md`](risk-breaker-seam.md). The seam fires only on N-consecutive-SCALE_DOWN-in-window-W aggregates,
not on individual SCALE_DOWN events.

## Anti-patterns

- **Don't skip preflight for "fast path" orders.** Every order goes through preflight — no exceptions. Aggregated rate
  is a few µs per rule; an entire preflight pass is sub-millisecond even with 30+ applicable rules.
- **Don't cache `RiskPreflightResult`.** Portfolio state changes per tick. A cached result is stale within milliseconds
  for actively-traded instruments. Re-evaluate per order.
- **Don't combine `SCALE_DOWN` factors as a product.** Min-aggregation is correct (most-restrictive wins); product
  aggregation would over-shrink instructions when many advisory rules fire simultaneously.
- **Don't surface only the first `BLOCK` reason.** Operators need every reason at once to triage. The `blocked_by` list
  is the contract.
- **Don't evaluate Layer 2 rules inside strategy-service.** Strategy queries the helper but does not own the evaluator.
  Cross-strategy / cross-account rules require the risk-and-exposure-service vantage point.
- **Don't add new aggregation semantics without UAC PR.** The decision-aggregation rules above are part of the helper
  contract; widening them silently changes behaviour across every consumer.

## Cross-references

- Risk rule vocabulary: [risk-rule-taxonomy.md](risk-rule-taxonomy.md)
- Risk-breaker escalation seam: [risk-breaker-seam.md](risk-breaker-seam.md)
- Kill switch + circuit breaker mechanics: [kill-switch-circuit-breaker.md](kill-switch-circuit-breaker.md)
- 4-layer risk-gates separation:
  [/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md](/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md)
- Layer 4 venue-side ErrorAction: [autonomous-recovery-matrix.md](autonomous-recovery-matrix.md)
- Capital-at-risk ceiling composition: [capital-efficiency-patterns.md](capital-efficiency-patterns.md)
- Plan-of-record:
  [plans/active/risk_simulations_limits_alerting_2026_05_10.md](../../plans/archive/risk_simulations_limits_alerting_2026_05_10.md)
