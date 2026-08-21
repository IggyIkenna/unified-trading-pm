---
doc_type: codex-ssot
title: Strategy ↔ Execution Protocol
summary:
  The strategy-to-execution runtime contract — 5 protocol rules (target-state not deltas, intent not algo, polymorphic
  targets, layer separation, benchmark fills), the 15-action StrategyInstruction envelope, idempotent reconciliation.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, execution, ssot, reconciliation, defi]
related:
  [
    /codex/04-architecture/account-instructions.md,
    /codex/04-architecture/slow-fast-routing-split.md,
    /codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md,
  ]
created: 2026-04-17
authoritative_for:
  [
    strategy-execution runtime protocol (five rules + 15 polymorphic actions),
    StrategyInstruction target-state instruction semantics,
  ]
referenced_by:
  [
    /codex/04-architecture/account-instructions.md,
    /codex/04-architecture/artifact-versioning.md,
    /codex/04-architecture/backtest-groups.md,
    /codex/04-architecture/capital-flow-model.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/04-architecture/oms-protocol-and-state-machine.md,
    /codex/04-architecture/order-state-machine.md,
    /codex/04-architecture/share-class-architecture.md,
  ]
owner:
last_reviewed: 2026-10-12
code_refs:
---

# Strategy ↔ Execution Protocol

> **What it is:** The runtime contract between strategy-service and execution-service. Five protocol rules, fifteen
> polymorphic action types, one parallel AccountInstruction envelope, target-state semantics, idempotent reconciliation.
> This is the most load-bearing contract in the system — every strategy and every execution path is constrained by it.
>
> **2026-08-21 update**: `WITHDRAW`/`REPAY` (inverse of `LEND`/`BORROW`) and `LP_MINT`/`LP_BURN` (concentrated-LP
> open/close) shipped this session — `unified-api-contracts@f5fc118ae1` and `@d751e743`. `InstructionActionV2` also
> carries `KILL_SWITCH`/`FLATTEN_POSITION`/`CONVERT_DUST` (18 members total); those three are control-plane actions
> under a separate authority model (see
> [/codex/04-architecture/account-instructions.md](/codex/04-architecture/account-instructions.md)) and are
> deliberately NOT part of this doc's target-state action family, so this doc's "15" counts the target-state family
> only (the original 11 + the 4 added this session). `InstructionActionV2` itself is the live oracle for the full
> member list if this count drifts again.

## Five Protocol Rules

### Rule 1 — Target state, not deltas

Strategies emit the **desired end state**, not the change from current. Execution reconciles.

**Why:** deltas get out of sync with venue state on restart, on partial fills, on reconciliation drift. Target state is
idempotent — emitting the same target twice is a no-op if already there.

```python
# WRONG — delta
instruction = TRADE(side=BUY, delta_units=5)

# RIGHT — target
instruction = TRADE(target_position_units=10)   # current+delta computed at execution
```

For multi-venue / multi-leg, target applies per leg / per venue.

### Rule 2 — Intent + constraints, not algo prescriptions

Strategy says _what_ it wants and _by when_; execution picks _how_.

**Why:** execution can pick better algos than a hard-coded choice; algos can improve without strategy code changes;
strategy stays at the alpha layer.

```python
# WRONG — prescribe the algo
instruction = TRADE(target=10, algo=TWAP, slice_count=5, window_seconds=300)

# RIGHT — intent + constraints
instruction = TRADE(
    target=10,
    urgency=MEDIUM,                # HIGH/MEDIUM/LOW
    deadline_utc="2026-04-17T14:00Z",
    max_cost_bps=15,
    execution_policy_ref="cefi-crypto-large-size-v3"
)
```

Execution resolves `(execution_policy_ref, urgency, deadline, size)` → algo + params.

### Rule 3 — Polymorphic targets

Target semantics differ per action type. Don't collapse 15 actions into "just TRADE with extra fields."

| Action   | Target                                                           |
| -------- | ---------------------------------------------------------------- |
| TRADE    | position_units                                                   |
| SWAP     | one-shot swap quantity + min_out                                 |
| LEND     | supplied_amount                                                  |
| BORROW   | debt_amount                                                      |
| WITHDRAW | target_supplied_amount (inverse of LEND)                         |
| REPAY    | target_debt_amount (inverse of BORROW)                           |
| STAKE    | staked_amount                                                    |
| UNSTAKE  | unstaked_amount                                                  |
| QUOTE    | continuous two-sided quote with spread + inventory + sensitivity |
| TRANSFER | target_balance at destination (same-chain)                       |
| BRIDGE   | target_balance at destination chain                              |
| ATOMIC   | all legs filled or none                                          |
| CANCEL   | references a prior instruction_id                                |
| LP_MINT  | open/add to a concentrated-LP position                           |
| LP_BURN  | close/reduce a concentrated-LP position (inverse of LP_MINT)     |

Type-discriminated at the StrategyInstruction level. Shared fields: `instruction_id`, `client_id`,
`strategy_instance_id`, `timestamp`, `attestations`.

### Rule 4 — Portfolio at strategy, instrument at execution, account at venue-coordination

Layering of concerns:

| Layer               | Owns                                          | Examples                                                      |
| ------------------- | --------------------------------------------- | ------------------------------------------------------------- |
| Portfolio Allocator | Per-strategy equity allocation                | "give strategy A $2.5M, B $1.5M, C $1M"                       |
| Strategy            | Portfolio of positions, signal → target       | "have 10 BTC long across eligible venues"                     |
| Execution           | Per-instrument child orders + venue selection | "place TWAP slice 1 on Binance @ $68k limit"                  |
| Venue coordination  | Shared-account aggregation + pre-flight       | "margin simulator across all strategies on Binance account_1" |
| Risk                | Cross-strategy portfolio limits               | "family vega cap $500k"                                       |

Strategies don't reason about individual child orders. Execution doesn't reason about portfolio alpha. Keep the boundary
clean.

### Rule 5 — Benchmark fills contract

Every fill (real OR simulated) has a `benchmark_price` computed by the algo's deterministic rule. This bridges batch and
live:

- **Batch**: fill = benchmark; `execution_alpha = 0`
- **Live**: fill = real venue fill; `execution_alpha = real - benchmark`

Strategy alpha attribution uses only `benchmark_pnl`. Execution alpha measures `real_pnl - benchmark_pnl`.

Full contract:
[/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md](/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md).

## StrategyInstruction (Polymorphic, 15 Actions)

Common envelope:

```python
class StrategyInstructionBase:
    instruction_id: str                 # content hash; idempotency key
    emitted_at_utc: datetime
    client_id: str
    strategy_instance_id: str
    family: FamilyEnum
    archetype_id: str
    archetype_build_version: str
    slot_version: int
    config_hash: str
    config_version: int
    share_class: ShareClassEnum
    urgency: UrgencyEnum                # HIGH / MEDIUM / LOW
    deadline_utc: Optional[datetime]
    execution_policy_ref: str
    attestations: Dict[str, str]        # model version, feature hashes, etc.
    correlation_id: Optional[str]       # for multi-strategy hedge/pair tracking
    eligible_venues: List[VenueId]
    venue_constraints: Dict[VenueId, VenueConstraints]
```

Action-specific subtypes:

### `TRADE`

```python
target_position_units: Decimal
target_instrument: InstrumentId
max_price: Optional[Decimal]
min_price: Optional[Decimal]
```

### `SWAP`

```python
in_asset: AssetId
out_asset: AssetId
in_amount: Decimal
min_out_amount: Decimal
route_hint: Optional[DexRoute]        # can force a pool; optional
```

### `LEND`

```python
protocol: LendingProtocolId           # AAVE_V3, COMPOUND_V3, MORPHO, SPARK, KAMINO
asset: AssetId
target_supplied_amount: Decimal
min_apy_bps: Optional[int]            # veto if below
```

### `BORROW`

```python
protocol: LendingProtocolId
asset: AssetId
target_debt_amount: Decimal
max_borrow_apy_bps: Optional[int]
collateral_health_min: Optional[Decimal]
```

### `WITHDRAW`

Rate-matched inverse of `LEND` — added 2026-08-21, `unified-api-contracts@f5fc118ae1`, to close the BATCH-settlement
gap (`resolve_settlement` had no dataclass to dispatch on for this enum member). **Name collision, not a duplicate**:
`AccountInstruction` (below) separately has its own `WITHDRAW` action meaning operator withdrawal to off-venue — this
one is a strategy-owned action reducing a supplied lending position, a different envelope and a different authority
model.

```python
protocol: LendingProtocolId
asset: AssetId
target_supplied_amount: Decimal
```

### `REPAY`

Inverse of `BORROW` — same shipment as `WITHDRAW` above.

```python
protocol: LendingProtocolId
asset: AssetId
target_debt_amount: Decimal
```

### `STAKE`

```python
protocol: StakingProtocolId           # LIDO, ROCKET_POOL, JITO, MARINADE, NATIVE_ETH_VALIDATOR
asset: AssetId
target_staked_amount: Decimal
lst_asset: Optional[AssetId]          # expected receipt token
```

### `UNSTAKE`

```python
protocol: StakingProtocolId
asset: AssetId
amount: Decimal
exit_queue_ok: bool                   # accept exit queue latency
```

### `QUOTE`

```python
instrument: InstrumentId
reference_price: Decimal              # from pricer; execution MMs around
half_spread_bps: int
max_inventory_abs: Decimal
skew_on_inventory: bool
refresh_cadence_ms: int                       # STRATEGY-side cadence, distinct from execution's faster tick loop
delta: Optional[Decimal]                      # added 2026-08-21, unified-api-contracts@6be4b136d7
gamma: Optional[Decimal]                      # sensitivity coefficients for DeltaProxyRepricer._reprice():
underlying_instrument_id: Optional[InstrumentId]  # effective_delta = delta + gamma * underlying_move.
                                               # None on all three reproduces the prior hardcoded delta=1.0 /
                                               # self-underlying case, so no existing construction changes meaning.
```

### `TRANSFER`

```python
asset: AssetId
venue_from: VenueId
venue_to: VenueId
target_balance_at_destination: Decimal
max_cost_bps: int
```

### `BRIDGE`

```python
asset: AssetId
chain_from: ChainId
chain_to: ChainId
target_balance_at_destination: Decimal
bridge_hint: Optional[BridgeId]
deadline_utc: datetime
```

### `ATOMIC`

```python
legs: List[Leg]                       # each leg is a TRADE/SWAP/LEND/etc.
execution_mode: ATOMIC | LEADER_HEDGE | SEQUENCED_WITH_PACING
leader_leg: Optional[int]
hedge_deadline_ms: Optional[int]
compensation_policy: Optional[CompensationPolicyEnum]
balance_mode: Optional[BalanceModeEnum]    # MAINTAIN_NEUTRAL_DELTA_THROUGH_EXECUTION
```

#### `ATOMIC` execution — what is IMPLEMENTED (2026-07-20)

The schema above is the contract; this is the state of the code that honours it.

- **Leg executor (exists, PAPER-default):** `execution-service` `execution_service/v2/atomic_leg_executor.py`
  (`execution-service@db75d51d`) translates each `AtomicLeg` → a venue-native `BetOrder` (`side = BACK` when
  `leg.side == "BUY"` else `LAY`; `fixture_id = leg.params["native_market_id"]`; stake = `size_units`) and places it via
  the `SportsAdapter` facade. It implements `LEADER_HEDGE`: the `leader_leg` is placed FIRST, the hedge only on a placed
  leader, within `hedge_deadline_ms`; on hedge failure/timeout it applies `compensation_policy`
  (`CLOSE_LEADER_IF_HEDGE_FAILS` → unwind the leader) and reports
  `AtomicExecutionReport{status, legs_placed, compensation_taken, naked_position}`.
- **PAPER-safe by construction:** the adapter comes from `create_sports_adapter(mode)` and the executor **defaults to
  `OperationalMode.PAPER`** → `PaperBettingAdapter` (simulated fills, zero network, zero credentials). A missing/None
  mode is PAPER, never live; live requires an explicit `OperationalMode.LIVE` **and** Secret-Manager credentials.
- **⚠️ NO LIVE RUNTIME SEAM YET (the gap):** nothing routes an emitted `AtomicInstruction` to that executor in a
  live/paper-live tick loop. `emit_instructions` only records; `V2EngineOrchestrator.on_tick` returns the list for a
  caller to forward, and the ONLY realized caller is the backtest/paper runtime (`GroupBRunner._process_tick` →
  `BenchmarkFillEngine.settle`, which is what produces deterministic paper fills). **Correction 2026-08-15**: the v2
  `AtomicHandler`/`V2InstructionRouter` this paragraph used to cite were deleted — a repo-wide audit found zero
  production callers (every one of the 14 `ACTION_HANDLER_REGISTRY` handlers, `AtomicHandler` included, was a stateless
  note-attacher; see `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`). The real
  ATOMIC live/paper seam is a separate mechanism, `execution_service/v2/atomic_instruction_router.py`'s
  `route_atomic_instructions`, wired into `cli/handlers/live_execution_handler.py`'s `_run_atomic_routing_loop` and
  calling `AtomicLegExecutor` directly — not audited here for live-vs-paper-only status, so the rest of this paragraph's
  "no live runtime seam" claim is unverified against that mechanism, not confirmed false. The legacy live handler speaks
  the old single-`BET` `Instruction`. Because the **T4 tier ban** forbids strategy-service importing execution-service,
  the seam cannot be a direct call — it needs a transport decision (the UTL `EventTransport` event-log seam is the
  architecturally-indicated option). Until then ATOMIC is **paper/backtest-only**. Cross-repo proof of the seam's two
  halves meeting lives in `e2e-testing` (`e2e-testing@7665a027`), the only repo permitted to import both services.
- **Known incomplete:** compensation unwinds via `cancel_bet`, which does not offset an **already-matched** leader; a
  real offsetting bet is required before live (fail-safe is naked + alert, never a false clean report).

### `CANCEL`

```python
cancel_instruction_id: str
cancel_scope: SINGLE | ALL_FOR_STRATEGY_INSTANCE
```

### `LP_MINT`

Open/add to a concentrated-LP position — added 2026-08-21, `unified-api-contracts@d751e743`, closing the last 2/5 of
the BATCH-settlement gap. Superset schema over Uniswap V3 (NFT-position, sqrt-price-bounds) and Orca/Raydium
(pool-address, raw-tick) connector shapes; protocol-specific fields nullable.

```python
protocol: str          # "uniswap_v3" | "orca" | "raydium" | ...
pool_id: str
asset_a: str
asset_b: str
amount_a_desired: Decimal
amount_b_desired: Decimal
amount_a_min: Optional[Decimal]
amount_b_min: Optional[Decimal]
lower_tick: int
upper_tick: int
fee_tier: Optional[int]                # Uniswap-specific tiered-pool selector; None for single-pool-per-pair
```

### `LP_BURN`

Close/reduce a concentrated-LP position — inverse of `LP_MINT`, same shipment.

```python
protocol: str
pool_id: str
position_token_id: Optional[str]       # Uniswap V3's NFT position id; None for Orca/Raydium (no NFT)
liquidity_amount: Decimal
amount_a_min: Optional[Decimal]
amount_b_min: Optional[Decimal]
```

## AccountInstruction (Parallel Envelope)

Operator-driven ops that are NOT benchmarked, NOT attributed to strategy alpha:

```python
class AccountInstruction:
    instruction_id: str
    emitted_at_utc: datetime
    client_id: str
    initiating_operator: str          # audit
    venue: VenueId
    account_id: str
    action: AccountActionEnum
```

Actions:

| Action                 | Purpose                                             |
| ---------------------- | --------------------------------------------------- |
| CLOSE_ALL              | Unwind all positions on this account                |
| CLOSE_ALL_FOR_STRATEGY | Unwind this strategy's share on shared account      |
| SET_MARGIN_MODE        | ISOLATED / CROSS / PORTFOLIO                        |
| SET_LEVERAGE           | Leverage setting per instrument                     |
| EMERGENCY_LIQUIDATE    | Hard liquidation of all positions (stop-loss-style) |
| TRANSFER_SUBACCOUNT    | Operator-initiated subaccount move                  |
| WITHDRAW               | Operator withdrawal to off-venue                    |
| DEPOSIT_ACK            | Acknowledge client deposit + allocate               |

## Event lifecycle per instruction

```
INSTRUCTION_EMITTED (strategy)
    ↓
INSTRUCTION_ACCEPTED_PREFLIGHT  (risk)  OR  INSTRUCTION_REJECTED_* (layer)
    ↓
ORDER_SUBMITTED  (execution, per child order)
    ↓
ORDER_FILLED / ORDER_PARTIALLY_FILLED / ORDER_REJECTED_VENUE / ORDER_TIMED_OUT
    ↓
FILL_ATTRIBUTED  (PBMS)
    ↓
INSTRUCTION_COMPLETED (execution, when all child orders terminal)
```

Every event carries the full event tag:
`(family, archetype_id, archetype_build_version, strategy_instance_id, slot_version, config_hash, config_version, client_id, share_class)`
plus `instruction_id`.

## Idempotency

- `instruction_id = content_hash(envelope + target + attestations)`
- Re-emitting same id: execution returns prior result; no side effect
- Re-emitting same target with new id: execution reconciles; net effect usually no-op
- CANCEL by instruction_id: targets prior instruction, not current state

## Retry semantics

- **Non-final venue errors** (rate limit, timeout, transient): execution retries per policy with backoff
- **Final venue errors** (rejected, insufficient margin): execution emits `INSTRUCTION_FAILED`; strategy decides next
  action
- **Deadline expired**: execution emits `INSTRUCTION_TIMED_OUT` with partial fill state

## Multi-venue / SOR flow

```
Strategy: eligible_venues = [BINANCE, OKX, BYBIT], target = 10 BTC
    ↓
Execution: runs SOR, picks BINANCE for best net price NOW
    ↓
If BINANCE fails / insufficient: falls to OKX
    ↓
If all fail: INSTRUCTION_FAILED
```

Strategy doesn't care which venue — only that target is met. PBMS + coordination handle venue-level position
attribution.

## Cross-references

- Polymorphic StrategyInstruction axis details:
  [/codex/09-strategy/architecture-v2/README.md](/codex/09-strategy/architecture-v2/README.md)
- Benchmark fills:
  [/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md](/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md)
- Risk gates (4-layer):
  [/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md](/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md)
- Venue-account coordination:
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
- Execution policies:
  [/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md](/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md)
- Artifact versioning: [artifact-versioning.md](artifact-versioning.md)
- Account instructions: [account-instructions.md](account-instructions.md)
- Capital flow model: [capital-flow-model.md](capital-flow-model.md)

## Not in this doc

- **Execution algo implementations** — execution-service/algo_library/
- **Per-venue adapter mechanics** — execution-service/adapters/
- **Strategy-side engine per archetype** — strategy-service/engine/strategies/
- **How fills are stored / queried** — PBMS + event-store
- **Schema serialization formats** — UAC + [schema-versioning.md](schema-versioning.md)
