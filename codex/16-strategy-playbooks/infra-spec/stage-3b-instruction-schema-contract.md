---
doc_type: codex-ssot
title: Stage 3B — Instruction Schema Contract (`(Client, downstream)` fit-check)
summary:
  Engineering projection of rule 10 for signals-only clients — the 8 required instruction fields
  (instrument_venue_context … risk_and_allocation_constraints), Standard/Rich optional depths, the NEW→LIVE→FILLED
  lifecycle + idempotency, the rejected-shape error codes, and the venue × instrument_type × execution_mode compat
  matrix validated by instructions-service/UAC.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, instruments-service]
scope: [engineer, admin]
tags: [execution, instruments, uac, strategy, docspec, validation]
related:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-downstream-analytics-capability-matrix.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md,
  ]
created: 2026-04-20
authoritative_for:
  [
    signals-only instruction-schema engineering contract (8 required fields + lifecycle + rejection codes +
    venue/instrument/mode compat matrix),
  ]
referenced_by:
  [
    /codex/14-customer-journeys/shared-core/instruction-schema-fit-and-package-boundaries.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-downstream-analytics-capability-matrix.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Stage 3B — Instruction Schema Contract (`(Client, downstream)` fit-check)

> **Purpose.** Implements rule 10's commercial + product boundary as an engineering contract. Defines the required field
> set for Odum execution, what Odum does **not** need, lifecycle semantics, and the compatibility matrix across venues ×
> instrument types × execution modes. Used by Stage 3C's derivation engine to resolve signals-only engagement fit, and
> by instructions-service + UAC at runtime for schema validation.
>
> **Authoritative source:**
> [`../_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md).
> This doc is the engineering projection of that rule — field names, types, validation surfaces, compat matrix. If the
> rule text and this doc drift, the rule wins.
>
> **Related:**
>
> - [`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) §1.16 `instruction_schema_fit` dimension, §3 BL-11,
>   BL-18 blocker predicates.
> - [`stage-3b-combo-rules-schema.yaml`](stage-3b-combo-rules-schema.yaml) — `instruction_schema_fit` enum and
>   `schema_depth` sub-dimension.
> - [`stage-3b-downstream-analytics-capability-matrix.md`](stage-3b-downstream-analytics-capability-matrix.md) — what
>   downstream analytics each integration mode supports, keyed off the same boundary.
> - [`../_ssot-rules/04-dart-commercial-axes.md`](../../14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md) —
>   the three DART paths.
> - [`../_ssot-rules/03-same-system-principle.md`](../../14-customer-journeys/_ssot-rules/03-same-system-principle.md) —
>   the "same-system partitioned view" framing underpinning rule 10.

---

## 1. Rule 10 boundary — explicit

Odum signals-only operates on the following principle: **the client sends decisions; Odum operates downstream.** This is
a hard boundary for both product reasons (rule 10 package boundary) and IP reasons (rule 10 §"What Odum does NOT need").

Explicitly **out of Odum's scope** for signals-only clients:

| Upstream concern                       | Why Odum does not need it                                                                                                                                                |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Regime classification**              | The client's decision "we're in a risk-on regime" is encoded in the instruction size and direction; Odum does not need the classifier logic, features, or training data. |
| **Raw model logic**                    | Model code, weights, features, training process — entirely upstream. Odum executes the decision, not the reasoning.                                                      |
| **Signal-generation methodology**      | How market data → trading signal is upstream. The signal comes in as an instruction; the generation path stays with the client.                                          |
| **Broader upstream IP**                | Portfolio construction math, optimisation objective, capacity models — all upstream.                                                                                     |
| **Research / promote pipeline access** | Block 6 per rule 05 is NOT included in signals-only. Clients who need backtest + promote sit on full-pipeline, not signals-only.                                         |

The explicit list matters because it defines what Odum does **not** ask for in integration conversations. A prospect who
feels Odum is asking for regime logic or model internals is sitting in the wrong conversation — escalate to full-DART
(where Odum runs the upstream too) or decline the engagement.

---

## 2. Required fields (8 minimum)

Every client instruction arriving on the Odum signals-only surface MUST express the following fields. A message missing
any required field is rejected at the instructions-service boundary with `SCHEMA_VALIDATION_FAILED`. The eight align 1:1
with rule 10 §"What Odum execution needs".

### 2.1 `instrument_venue_context`

```yaml
field: instrument_venue_context
type: object
required: true
shape:
  instrument_id: string          # unambiguous reference to instruments-service catalogue
  venue: string                  # venue id per 02-venues/venue-registry-reference.md
  asset_group: enum              # CEFI | DEFI | TRADFI | SPORTS | PREDICTION | CROSS_CATEGORY (canonical JSON key)
  # Legacy wire compat: clients may still send the same enum under the key `category` — UAC maps both to one field.
  chain:
    type: string
    optional: true               # DeFi only
  instrument_type: enum
    values: [spot, perp, dated_future, option, lending, staking, lp, event_settled]
validation:
  - instrument_id must resolve in instruments-service
  - venue must be in supported_venues for instrument_type
  - chain must be populated when asset_group == DEFI
```

### 2.2 `intended_action`

```yaml
field: intended_action
type: enum
required: true
values:
  - BUY
  - SELL
  - HEDGE # open a hedge leg (execution-service resolves the counter-leg)
  - CLOSE # close current position
  - ROLL # roll a dated position (execution-service handles contract resolution)
  - REBALANCE # shift to a new target weighting
  - BACK # sports: back the selection
  - LAY # sports: lay the selection
  - LEND # DeFi: supply to lending protocol
  - BORROW # DeFi: borrow against collateral
  - STAKE # DeFi: stake native asset
  - UNSTAKE # DeFi: unstake
  - BRIDGE # DeFi: cross-chain transfer
  - ATOMIC # multi-leg atomic bundle (composite action)
validation:
  - action must map onto execution-service primitive for (venue, instrument_type)
  - ATOMIC requires a nested `legs` array (see §2.6 order_constraints)
```

### 2.3 `size_or_target_exposure`

```yaml
field: size_or_target_exposure
type: oneof [quantity, notional, target_portfolio_weight]
required: true
shape:
  quantity:
    value: decimal
    unit: string # base-asset units ("BTC", "ETH", "contracts")
  notional:
    value: decimal
    currency: string # share-class unit ("USDT", "USDC", "USD", "GBP")
  target_portfolio_weight:
    value: decimal # 0.0..1.0 of client's portfolio NAV
validation:
  - exactly one of {quantity, notional, target_portfolio_weight} must be populated
  - unit must be something Odum's risk-and-exposure service understands
  - target_portfolio_weight requires client has portfolio NAV tracked in Odum
```

### 2.4 `timeframe_urgency`

```yaml
field: timeframe_urgency
type: object
required: true
shape:
  mode: enum
    values: [MARKET, LIMIT_PASSIVE, TIME_WINDOW, SCHEDULED, AT_OPEN, AT_CLOSE]
  deadline:
    type: timestamp
    optional: true           # required when mode in {TIME_WINDOW, SCHEDULED}
  window_minutes:
    type: int
    optional: true           # required when mode == TIME_WINDOW
validation:
  - maps onto execution-service algo_library via (mode, instrument_type, venue)
  - deadline must be >= now + min_venue_latency
```

### 2.5 `order_constraints`

```yaml
field: order_constraints
type: object
required: true
shape:
  price_limit:
    type: decimal
    optional: true
  max_participation_pct:
    type: decimal # % of volume in a window — for TIME_WINDOW/pov algos
    optional: true
  slippage_budget_bps:
    type: decimal # max tolerated slippage vs decision price
    optional: true
  venue_restrictions:
    type: list[string]
    optional: true # veto specific routes under a META_BROKER venue
  time_in_force:
    type: enum
    values: [IOC, FOK, GTC, GTD, DAY]
    optional: true
  legs:
    type: list[object]
    optional: true # required when intended_action == ATOMIC
    shape:
      instrument_id: string
      action: intended_action
      size_or_target_exposure: oneof [quantity, notional, target_portfolio_weight]
validation:
  - at least one of {price_limit, slippage_budget_bps} should be present for LIMIT_PASSIVE mode
  - venue_restrictions must be subset of META_BROKER's child venues
```

### 2.6 `strategy_instruction_id`

```yaml
field: strategy_instruction_id
type: object
required: true
shape:
  client_strategy_id: string # stable identifier — client's upstream strategy
  instruction_id: string # unique per instruction — client-assigned idempotency key
  parent_instruction_id:
    type: string
    optional: true # for grouped orders / legs
validation:
  - client_strategy_id must be stable across instruction lifecycle
  - (client_strategy_id, instruction_id) tuple must be unique within client scope
  - used by: reconciliation, P&L attribution, client-side lifecycle linkage
```

### 2.7 `lifecycle_replace_cancel`

```yaml
field: lifecycle_replace_cancel
type: object
required: true
shape:
  supersedes_instruction_id:
    type: string
    optional: true             # if this instruction replaces a prior one
  semantic: enum
    values:
      - NEW                    # new instruction, no prior relationship
      - REPLACE                # cancel supersedes_instruction_id, then place this
      - AMEND                  # modify the prior in place (size/price only; same instruction_id)
      - ADD_CHILD              # sibling instruction under parent_instruction_id
      - CANCEL                 # cancel-only; size/action fields ignored
validation:
  - REPLACE requires supersedes_instruction_id
  - AMEND requires matching instruction_id to a live instruction and matching core fields (instrument, venue)
  - CANCEL rejected if target instruction already filled or terminal
```

### 2.8 `risk_and_allocation_constraints`

```yaml
field: risk_and_allocation_constraints
type: object
required: true
shape:
  per_instruction_max_loss:
    type: decimal
    optional: true
  per_client_allocation_cap:
    type: decimal # max % of client portfolio in this strategy
    optional: true
  correlation_limits:
    type: list[object]
    optional: true
    shape:
      with_strategy_id: string
      max_joint_exposure: decimal
  kill_switch_conditions:
    type: list[object]
    optional: true
    shape:
      metric: enum [drawdown_bps, realized_loss_usd, venue_down, feed_stale_sec]
      threshold: decimal
validation:
  - at least ONE of {per_instruction_max_loss, per_client_allocation_cap} must be present
  - kill_switch_conditions must be enforceable by risk-and-exposure-service
```

---

## 3. Optional fields (Standard + Rich schema depths)

Beyond the minimal 8 required fields, clients on `schema_depth = standard` or `schema_depth = rich` can express:

### 3.1 Standard extensions

```yaml
- field: strategy_family_tag
  type: string
  purpose: logical grouping for client reporting ("momentum", "mean_revert", "arb")

- field: parent_child_grouping
  type: object
  shape:
    group_id: string # all instructions sharing group_id are treated as a bundle
    intent: enum [REBALANCE, PAIR_TRADE, MULTI_VENUE_COORDINATED]

- field: scheduling_hints
  type: object
  shape:
    priority: enum [LOW, NORMAL, HIGH, CRITICAL]
    do_not_execute_before: timestamp
    do_not_execute_after: timestamp

- field: reconciliation_annotations
  type: object
  shape:
    client_order_ref: string # client's internal ref; echoed in reconciliation reports
    expected_fill_currency: string
    settlement_instructions: string
```

### 3.2 Rich extensions (negotiated per client; Tier B + often custom premium)

```yaml
- field: proprietary_risk_dimensions
  type: dict[string, decimal]
  purpose: client-defined risk dimensions Odum respects (e.g. "sector_beta", "factor_mkt_rf")

- field: custom_execution_directives
  type: dict[string, string]
  purpose: bespoke routing / algo directives negotiated per client

- field: custom_lifecycle_states
  type: list[string]
  purpose: client-specific workflow states (e.g. "compliance_hold", "treasury_approval")
```

Rich-schema fields are typically **bilateral** — Odum must implement support before the client can populate them.
Unrecognised rich-schema fields raise `SCHEMA_UNKNOWN_EXTENSION` unless pre-negotiated in the client contract.

---

## 4. Unsupported instruction shapes (rejected)

Odum execution will **reject** the following shapes. Each rejection surfaces an actionable error plus the rule 10
boundary citation so the client understands why.

| Shape                                                                                       | Rejection reason                                                         | Error code                             |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------- |
| Instruction with raw feature vector attached                                                | Rule 10 §"What Odum does NOT need" — feature engineering is upstream     | `SCHEMA_UPSTREAM_IP_PRESENT`           |
| Instruction with embedded model weights / code                                              | Same as above                                                            | `SCHEMA_UPSTREAM_IP_PRESENT`           |
| Instruction without `strategy_instruction_id`                                               | Required for reconciliation + P&L attribution                            | `SCHEMA_MISSING_REQUIRED_FIELD`        |
| Instruction asking Odum to "research this signal"                                           | Rule 10 package boundary — research/promote is block 6, not signals-only | `SCHEMA_OUT_OF_PACKAGE`                |
| Instruction requesting new venue / chain / instrument_type not in client's entitlement      | Venue pack / chain pack / instrument-type pack gating                    | `ENTITLEMENT_NOT_IN_SCOPE`             |
| AMEND on an instruction already filled                                                      | Lifecycle semantic: AMEND is only valid on live instructions             | `LIFECYCLE_INVALID_TRANSITION`         |
| CANCEL on an instruction that doesn't exist                                                 | No target to cancel                                                      | `LIFECYCLE_TARGET_NOT_FOUND`           |
| REPLACE without `supersedes_instruction_id`                                                 | REPLACE requires an explicit target                                      | `LIFECYCLE_REPLACE_MISSING_TARGET`     |
| Instruction with `target_portfolio_weight` when client has no tracked NAV                   | Target weight requires portfolio context                                 | `RISK_CLIENT_PORTFOLIO_NOT_TRACKED`    |
| Instruction with ATOMIC action but empty `legs` array                                       | ATOMIC requires ≥ 2 legs                                                 | `SCHEMA_ATOMIC_LEGS_MISSING`           |
| Instruction referencing a retired slot (BL-15)                                              | RETIRED slots do not accept new allocations                              | `LOCK_STATE_RETIRED`                   |
| Instruction from org_scope ≠ slot.exclusive_client_id on a CLIENT_EXCLUSIVE slot (BL-14/22) | Exclusivity enforcement                                                  | `LOCK_STATE_CLIENT_EXCLUSIVE_MISMATCH` |

---

## 5. Lifecycle semantics (detailed)

### 5.1 State machine

```
          NEW ──────────────────────► LIVE ──────────► FILLED
           │                           │
           │                           ├──► PARTIAL
           │                           │
           │     REPLACE               ├──► CANCELLED
           │     AMEND                 │
           │     ADD_CHILD             └──► EXPIRED
           │
           └──► REJECTED (pre-LIVE validation fail)
```

Terminal states: `FILLED`, `PARTIAL` (any remaining unfilled quantity transitions to `CANCELLED` or `EXPIRED` per order
constraints), `CANCELLED`, `EXPIRED`, `REJECTED`.

### 5.2 Semantic rules

- **NEW** — first submission. Must pass schema validation + entitlement check + risk pre-flight.
- **REPLACE** — atomic cancel-then-place. Requires `supersedes_instruction_id` pointing to a non-terminal instruction.
  On success, the prior transitions to `CANCELLED` (replaced), and the new one transitions to `LIVE`.
- **AMEND** — in-place modification. Can only change `size_or_target_exposure.quantity`,
  `order_constraints.price_limit`, `order_constraints.slippage_budget_bps`, `timeframe_urgency.deadline`. Core fields
  (instrument, venue, action) cannot be amended — use REPLACE for those. `instruction_id` matches the target.
- **ADD_CHILD** — new sibling under `parent_instruction_id`. Used for multi-leg bundles where legs are submitted
  individually but coordinated via the parent.
- **CANCEL** — cancel-only. If target is in `PARTIAL`, the unfilled remainder is cancelled; filled portion stays.

### 5.3 Idempotency

`(client_strategy_id, instruction_id)` is the idempotency key. Re-submitting the same NEW instruction with identical
fields returns the existing instruction's current state (no double-execution). Re-submission with differing fields
returns `IDEMPOTENCY_CONFLICT`.

### 5.4 Lifecycle event surface

Every transition emits a UTL event consumed by position-balance-monitor + risk-and-exposure + client-reporting:

| Event                      | Fires on                                                  |
| -------------------------- | --------------------------------------------------------- |
| `INSTRUCTION_ACCEPTED`     | Schema+entitlement+risk pre-flight pass, state → LIVE     |
| `INSTRUCTION_REJECTED`     | Any pre-flight failure                                    |
| `INSTRUCTION_REPLACED`     | REPLACE accepted; prior instruction transitions CANCELLED |
| `INSTRUCTION_AMENDED`      | AMEND accepted; fields updated in place                   |
| `INSTRUCTION_CANCELLED`    | CANCEL accepted                                           |
| `INSTRUCTION_FILLED`       | Full fill — state → FILLED                                |
| `INSTRUCTION_PARTIAL_FILL` | Partial fill — state → PARTIAL                            |
| `INSTRUCTION_EXPIRED`      | Deadline passed without fill                              |

---

## 6. Compatibility matrix — venue × instrument_type × execution_mode × schema shape

Each cell: which required-fields shapes the cell supports, and what is rejected. Rejection maps to a Stage 3B blocker id
where applicable.

### 6.1 CeFi

| venue       | instrument_type | MARKET | LIMIT_PASSIVE | TIME_WINDOW | SCHEDULED | AT_OPEN/CLOSE | ATOMIC multi-leg | Notes / rejections                                  |
| ----------- | --------------- | :----: | :-----------: | :---------: | :-------: | :-----------: | :--------------: | --------------------------------------------------- |
| binance     | spot            |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |        ❌        | No ATOMIC execution — use ADD_CHILD under parent    |
| binance     | perp            |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |        ❌        | Same                                                |
| binance     | option          |   ❌   |      ❌       |     ❌      |    ❌     |      ❌       |        ❌        | Not in v2 scope (BTC/ETH options only; use Deribit) |
| okx         | spot            |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |        ❌        |                                                     |
| okx         | perp            |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |        ❌        |                                                     |
| okx         | option          |   ✅   |      ✅       |     ❌      |    ❌     |      ❌       |        ⚠️        | Multi-leg vol arb — BL-1 blocks DeFi side           |
| bybit       | spot            |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |        ❌        |                                                     |
| bybit       | perp            |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |        ❌        |                                                     |
| hyperliquid | perp            |   ✅   |      ✅       |     ✅      |    ❌     |      ❌       |        ❌        | No scheduled execution                              |
| deribit     | perp            |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |        ❌        |                                                     |
| deribit     | dated_future    |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |        ⚠️        | FUTURES_ROLL ATOMIC pending (BL-10)                 |
| deribit     | option          |   ✅   |      ✅       |     ❌      |    ❌     |      ❌       |        ✅        | Multi-leg option combos supported                   |

### 6.2 TradFi

| venue | instrument_type | MARKET | LIMIT_PASSIVE | TIME_WINDOW | SCHEDULED | AT_OPEN/CLOSE | ATOMIC | Notes                                                    |
| ----- | --------------- | :----: | :-----------: | :---------: | :-------: | :-----------: | :----: | -------------------------------------------------------- |
| ibkr  | spot (equity)   |   ✅   |      ✅       |     ✅      |    ✅     |      ✅       |   ❌   | AT_OPEN/CLOSE via IBKR order types                       |
| ibkr  | spot (FX)       |   ✅   |      ✅       |     ✅      |    ✅     |      ❌       |   ❌   |                                                          |
| ibkr  | option          |   ✅   |      ✅       |     ❌      |    ❌     |      ❌       |   ✅   | CBOE routed via IBKR; multi-leg option combos supported  |
| cme   | dated_future    |   ✅   |      ✅       |     ✅      |    ✅     |      ✅       |   ⚠️   | Calendar-spread combo ticker per BL-10 (pending service) |
| ice   | dated_future    |   ✅   |      ✅       |     ✅      |    ❌     |      ❌       |   ❌   | SCHEDULED partial                                        |

### 6.3 DeFi

| venue × chain         | instrument_type | MARKET | LIMIT_PASSIVE | TIME_WINDOW | SCHEDULED | ATOMIC multi-leg | Notes                                                      |
| --------------------- | --------------- | :----: | :-----------: | :---------: | :-------: | :--------------: | ---------------------------------------------------------- |
| uniswap_v3 × eth      | spot (SWAP)     |   ✅   |      ❌       |     ⚠️      |    ❌     |        ✅        | No limit orders on AMM; TIME_WINDOW via TWAP-splitter algo |
| uniswap_v3 × arbitrum | spot (SWAP)     |   ✅   |      ❌       |     ⚠️      |    ❌     |        ✅        |                                                            |
| aave_v3 × eth         | lending         |   ✅   |      ❌       |     ❌      |    ❌     |        ✅        | ATOMIC used for recursive-staked / flash-loan bundles      |
| aave_v3 × eth         | borrow          |   ✅   |      ❌       |     ❌      |    ❌     |        ✅        |                                                            |
| lido × eth            | staking         |   ✅   |      ❌       |     ❌      |    ❌     |        ❌        |                                                            |
| jito × solana         | staking         |   ✅   |      ❌       |     ❌      |    ❌     |        ❌        |                                                            |
| hyperliquid_dex × hl  | perp            |   ✅   |      ✅       |     ✅      |    ❌     |        ❌        |                                                            |
| drift × solana        | perp            |   ✅   |      ✅       |     ⚠️      |    ❌     |        ❌        |                                                            |
| uniswap × any         | option          |   ❌   |      ❌       |     ❌      |    ❌     |        ❌        | BL-1 — no DeFi options venue                               |
| any × any             | dated_future    |   ❌   |      ❌       |     ❌      |    ❌     |        ❌        | BL-2 — no DeFi dated-future venue                          |

### 6.4 Sports / Prediction

| venue             | instrument_type | PLACE (market) | PLACE (limit odds) | ATOMIC | QUOTE (MM) | Notes                                                           |
| ----------------- | --------------- | :------------: | :----------------: | :----: | :--------: | --------------------------------------------------------------- |
| unity (all books) | event_settled   |       ✅       |         ✅         |   ❌   | ❌ (BL-6)  | Single wallet; arb ATOMIC-like at book layer but place-only API |
| betfair_direct    | event_settled   |       ✅       |         ✅         |   ❌   |     ⚠️     | Lay side — UAC gap #9 `LaySideExecutionSemantics`               |
| smarkets_direct   | event_settled   |       ✅       |         ✅         |   ❌   |     ⚠️     | Same                                                            |
| matchbook_direct  | event_settled   |       ✅       |         ✅         |   ❌   |     ⚠️     | Same                                                            |
| polymarket        | event_settled   |       ✅       |         ✅         |   ❌   |     ❌     | Prediction binary; USDC on Polygon                              |
| kalshi            | event_settled   |   ❌ (BL-5)    |     ❌ (BL-5)      |   ❌   |     ❌     | Execution adapter pending                                       |

Legend: ✅ = supported, ⚠️ = partial / behind a UAC gap, ❌ = rejected with specific error code.

---

## 7. instruction_schema_fit resolution — how rule 10 boundary maps to the 3-value dimension

| `instruction_schema_fit` value   | What the client runs upstream                             | What Odum runs downstream                                        | Blocks included (rule 05)                |
| -------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------- |
| `signals_only`                   | Full upstream: regime, model, signal-gen, portfolio ctor  | Strategy-service entry, execution, reporting, selected analytics | 1, 4, 5, 7, 8, 9, 10, 11 (selected)      |
| `client_strategy_and_downstream` | Client strategy logic (but hosted on Odum infrastructure) | Hosting, execution, reporting, analytics                         | Same as signals_only PLUS hosted compute |
| `full_pipeline`                  | Optional — client can research on Odum too                | Research/promote + strategy + execution + reporting + analytics  | 1, 4, 5, 6, 7, 8, 9, 10, 11              |

The Stage 3C derivation engine applies these mappings to produce `prod_restrictions(client_contract)` per
[`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) §5. Attempting to use block 6 with `signals_only` trips
BL-11.

### 7.1 Pre-demo fit-check discipline

Per rule 10 §"Pre-demo fit-check discipline", before a signals-only demo runs:

1. Does the prospect's instruction surface express all 8 required fields? If yes → proceed.
2. If no, can they adapt? Add a stable strategy id, express size in Odum-understood units, define replace-cancel
   behaviour — most prospects can.
3. If adaptation is not feasible at minimal depth → wrong path. Either full_pipeline, or bespoke (custom premium).
4. Fit-check happens in pb2b (post-first-call briefing), not in the demo itself.

---

## 8. Relationship to other infra-spec docs

- **[`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md)** — §1.16 declares `instruction_schema_fit` as a
  first-class registry dimension; BL-11 + BL-18 enforce the rule-10 boundary predicates.
- **[`stage-3b-combo-rules-schema.yaml`](stage-3b-combo-rules-schema.yaml)** — the YAML registry uses
  `instruction_schema_fit` enum and `schema_depth` sub-dimension from this doc.
- **[`stage-3b-downstream-analytics-capability-matrix.md`](stage-3b-downstream-analytics-capability-matrix.md)** —
  per-capability support per `instruction_schema_fit` value. Load-bearing: signals-only lacks upstream lineage, so
  certain analytics are `not_available`.
- **[`../_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md)**
  — the canonical rule. This doc is the engineering projection; the rule wins on conflict.

---

## 9. Reconciliation pass (vs Agent A's merged rule 10)

Reconciliation pass completed 2026-04-20 against `../_ssot-rules/10-strategy-instruction-schema-principles.md`.

### Verified (no change needed)

Section headings in rule 10 that this document cites all exist verbatim:

- §"What Odum execution needs" at line 21 — the 8 required fields enumerated here in §2.
- §"What Odum does NOT need" at line 45 — §1 out-of-scope table (regime / model logic / signal-gen methodology / broader
  upstream IP). This doc's §1 adds a 5th row (research/promote access) citing rule 05 block 6 + rule 10 §"Package
  boundaries", not §"What Odum does NOT need" — grouping is under the superset "out of Odum's scope for signals-only",
  which is accurate.
- §"Package boundaries" at line 60 — §7 integration-mode table. Included/excluded block lists match 1:1.
- §"Pre-demo fit-check discipline" at line 105 — §7.1 of this doc.
- §"Schema depth as a pricing dimension" at line 91 — §3 Standard + Rich extensions; depths (minimal / standard / rich)
  match verbatim.
- §"Interaction with the same-system principle" at line 134 — cross-references in §7 and throughout.
- §"Enforcement rules" at line 146 — underpins §4 unsupported-shapes rejections.

Field-level check: the 8 required fields in this doc §2.1–§2.8 (`instrument_venue_context`, `intended_action`,
`size_or_target_exposure`, `timeframe_urgency`, `order_constraints`, `strategy_instruction_id`,
`lifecycle_replace_cancel`, `risk_and_allocation_constraints`) correspond 1:1 to rule 10's enumerated required fields
with naming normalised to snake_case identifiers.

### Resolved in this reconciliation pass

None — this document's content aligned with rule 10 as merged. Edits landed in sibling doc
[`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) §1.15 and §3 BL-19; see its §6 for details.

### Watch-for (future rule 10 changes)

If Agent A later adds / removes / renames required fields in rule 10 §"What Odum execution needs", update:

- §2 required-fields YAML blocks and their validation rules here.
- [`stage-3b-combo-rules-schema.yaml`](stage-3b-combo-rules-schema.yaml) BL-18 predicate `required_fields_present`
  fields list.
- §4 unsupported-shapes table (error codes per missing field).
- [`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) §3 BL-18 predicate.

If rule 10 revises §"What Odum does NOT need" (adds or removes upstream-IP items), re-check:

- §1 "Explicitly out of Odum's scope" table here.
- [`stage-3b-downstream-analytics-capability-matrix.md`](stage-3b-downstream-analytics-capability-matrix.md)
  capabilities #9, #13, #16, #17, #18, #24, #26 — their "not available in signals_only" reasoning cites this list.
