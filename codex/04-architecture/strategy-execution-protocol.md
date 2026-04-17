# Strategy ↔ Execution Protocol

> **What it is:** The runtime contract between strategy-service and execution-service. Five protocol rules, eleven
> polymorphic action types, one parallel AccountInstruction envelope, target-state semantics, idempotent reconciliation.
> This is the most load-bearing contract in the system — every strategy and every execution path is constrained by it.

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

Target semantics differ per action type. Don't collapse 11 actions into "just TRADE with extra fields."

| Action   | Target                                             |
| -------- | -------------------------------------------------- |
| TRADE    | position_units                                     |
| SWAP     | one-shot swap quantity + min_out                   |
| LEND     | supplied_amount                                    |
| BORROW   | debt_amount                                        |
| STAKE    | staked_amount                                      |
| UNSTAKE  | unstaked_amount                                    |
| QUOTE    | continuous two-sided quote with spread + inventory |
| TRANSFER | target_balance at destination (same-chain)         |
| BRIDGE   | target_balance at destination chain                |
| ATOMIC   | all legs filled or none                            |
| CANCEL   | references a prior instruction_id                  |

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
[../09-strategy/architecture-v2/cross-cutting/benchmark-fills.md](../09-strategy/architecture-v2/cross-cutting/benchmark-fills.md).

## StrategyInstruction (Polymorphic, 11 Actions)

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
refresh_cadence_ms: int
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

### `CANCEL`

```python
cancel_instruction_id: str
cancel_scope: SINGLE | ALL_FOR_STRATEGY_INSTANCE
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
  [../09-strategy/architecture-v2/README.md](../09-strategy/architecture-v2/README.md)
- Benchmark fills:
  [../09-strategy/architecture-v2/cross-cutting/benchmark-fills.md](../09-strategy/architecture-v2/cross-cutting/benchmark-fills.md)
- Risk gates (4-layer):
  [../09-strategy/architecture-v2/cross-cutting/risk-gates.md](../09-strategy/architecture-v2/cross-cutting/risk-gates.md)
- Venue-account coordination:
  [../09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](../09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
- Execution policies:
  [../09-strategy/architecture-v2/cross-cutting/execution-policies.md](../09-strategy/architecture-v2/cross-cutting/execution-policies.md)
- Artifact versioning: [artifact-versioning.md](artifact-versioning.md)
- Account instructions: [account-instructions.md](account-instructions.md)
- Capital flow model: [capital-flow-model.md](capital-flow-model.md)

## Not in this doc

- **Execution algo implementations** — execution-service/algo_library/
- **Per-venue adapter mechanics** — execution-service/adapters/
- **Strategy-side engine per archetype** — strategy-service/engine/strategies/
- **How fills are stored / queried** — PBMS + event-store
- **Schema serialization formats** — UAC + [schema-versioning.md](schema-versioning.md)
