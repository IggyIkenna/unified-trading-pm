---
doc_type: codex-ssot
title: "Cross-Cutting: Execution Policies"
summary:
  The execution-policy layer — a versioned, artifact-registered rule table mapping (venue × action × condition) → (algo
  + params). Strategies emit intent and reference a policy_id; execution-service resolves the algo (MARKET_SWEEP/
  TWAP/VWAP/POV/ICEBERG/SMART_ROUTED/MEV_PROTECTED_SWAP/ATOMIC_MULTI_LEG/…) + params at order time. Covers policy
  structure/resolution flow, the algo library, cost-model coupling, benchmark-fill declaration, and versioning rules.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [strategy, execution, defi, cefi, benchmark-fills]
related:
  [
    ../../../04-architecture/execution-policy.md,
    ../../../04-architecture/artifact-versioning.md,
    /codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md,
    ../axes/venue-eligibility.md,
  ]
created: 2026-04-17
authoritative_for: [strategy cross-cutting execution-policy rule-table + algo-library catalog]
referenced_by:
  [
    /codex/04-architecture/execution-policy.md,
    /codex/04-architecture/fixed-grid-config.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/09-strategy/_archived_pre_v2/cross-cutting/cost-modeling.md,
    /codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md,
    /codex/09-strategy/_archived_pre_v2/cross-cutting/multi-leg-execution.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cross-Cutting: Execution Policies

> **What it is:** A versioned, artifact-registered **rule table** that maps (venue × action × condition) → (algorithm +
> parameters). Strategies reference an execution policy by ID; execution-service resolves the algo + params at order
> time. Enables per-venue, per-action customization without strategy code changes.

## Why a policy layer

Without a policy layer, every strategy would have to:

- Encode venue-specific algo choice (TWAP vs VWAP vs POV vs ICEBERG)
- Encode algo parameters (aggression, slice size, deadline)
- Encode cost-model assumptions inline
- Re-test behavior on every venue change

With an execution policy:

- Strategy emits intent (e.g., "establish 100 BTC long by 14:00 UTC")
- Policy maps intent → algo choice given venue + instrument + urgency + size
- Strategy code is stable; policy evolves independently

## Policy structure

```yaml
policy_id: cefi-crypto-large-size-v3
version: 3 # monotonic; content-hashed
description: Large-size CEX crypto execution with TWAP + cost cap
applies_to:
  action: TRADE
  venue_categories: [CEFI]
  instrument_types: [SPOT, PERP]
  urgency: [LOW, MEDIUM] # HIGH falls through to market-sweep policy

rules:
  - when:
      notional_usd: { "<": 50_000 }
    then:
      algo: MARKET_SWEEP
      params: { max_slippage_bps: 10 }

  - when:
      notional_usd: { ">=": 50_000, "<": 500_000 }
    then:
      algo: TWAP
      params:
        slice_count: 10
        window_seconds: 300
        participation_rate: 0.20

  - when:
      notional_usd: { ">=": 500_000 }
    then:
      algo: TWAP
      params:
        slice_count: 30
        window_seconds: 1800
        participation_rate: 0.10
        dark_pool_opt_in: false

cost_model_ref: cefi-cost-model-v2 # separate versioned artifact
benchmark_mode_ref: vwap-window-v1 # what benchmark to compare live fills against
```

## Policy resolution flow

```
StrategyInstruction emitted
        │
        ▼
  execution-service
        │
        ▼
  Resolve execution_policy_ref → rule table
        │
        ▼
  Evaluate rules against instruction + current market state
        │
        ▼
  Select algo + params
        │
        ▼
  Invoke algo_library with params
        │
        ▼
  Generate child orders → venue adapter
```

## Policy categories

| Category         | Typical policies                                                               |
| ---------------- | ------------------------------------------------------------------------------ |
| CeFi crypto      | Small: market-sweep; Medium: TWAP; Large: TWAP + participation cap             |
| DeFi swap        | Small: direct; Medium: route optimizer + MEV protection; Large: multi-hop TWAP |
| DeFi lend/stake  | Deposit/withdraw direct; no algo                                               |
| Sports arb       | Simultaneous market-order on all legs; deadline cap                            |
| Sports ML        | Single back/lay at quoted price; no algo                                       |
| TradFi equity    | Small: market; Medium: VWAP; Large: Implementation Shortfall                   |
| Vol options      | Iceberg with passive pegging; native multi-leg atomic                          |
| Market making    | CONTINUOUS quote loop; inventory skew adjustments                              |
| Multi-leg basket | Coordinated TWAP across legs; balance factor exposures during slice            |

## Algos in the library

(Each is artifact-versioned separately; policy references by name+version.)

- `MARKET_SWEEP`
- `LIMIT_BEST`
- `TWAP`
- `VWAP`
- `POV` (percent of volume)
- `IMPLEMENTATION_SHORTFALL`
- `ICEBERG`
- `PEG_TO_BEST`
- `SMART_ROUTED` (runs SOR per slice)
- `MEV_PROTECTED_SWAP`
- `ATOMIC_MULTI_LEG`
- `LEADER_HEDGE`
- `DELTA_HEDGE_CONTINUOUS`
- `SPORTS_SIMULTANEOUS_LEGS`
- `QUOTE_LOOP` (market making)
- `LIQUIDATION_FLASH_LOAN`

Each algo declares:

- Applicable action types
- Required params (with defaults)
- Optional params
- Output: child order stream
- Benchmark fills function (for batch mode)

## Benchmark fills contract

Every algo declares a **benchmark fill function** — a deterministic pricing rule that produces fills as if there were
zero market impact and zero timing alpha. Used in:

- **Batch / backtest mode** (group B): benchmark replaces real fills; strategy alpha isolated from execution alpha
- **Live mode**: benchmark fills computed alongside real fills for continuous execution-alpha measurement

Example benchmark functions:

| Algo                 | Benchmark                           |
| -------------------- | ----------------------------------- |
| `MARKET_SWEEP`       | mid price at order arrival          |
| `TWAP(window)`       | time-weighted mid over the window   |
| `VWAP(window)`       | volume-weighted mid over the window |
| `ICEBERG`            | same as the passive target          |
| `QUOTE_LOOP`         | mid at each quote update            |
| `MEV_PROTECTED_SWAP` | pool mid at block N                 |

Full contract: [benchmark-fills.md](benchmark-fills.md).

## Policy versioning rules

- Policy content change → new version (monotonic)
- Strategy config pins a specific policy version
- New policy version does NOT auto-upgrade consumers
- Consumer opt-in per config change
- Old policy versions remain resolvable for audit + replay

Full artifact-versioning rules:
[../../../04-architecture/artifact-versioning.md](../../../04-architecture/artifact-versioning.md).

## Cost-model coupling

Every policy references a cost model (`cost_model_ref`):

- Expected fees per venue (tier-aware)
- Expected slippage curve (size → bps)
- Gas model (DeFi)
- Commission (sports books)
- Haircut model (for margin)

Strategy's go/no-go decision may use the cost model at emission time (for net-edge calc); execution uses it to pick algo
params.

## Policy-to-instruction dispatch

```python
def select_algo(instruction: StrategyInstruction, policy: ExecutionPolicy) -> AlgoInvocation:
    for rule in policy.rules:
        if rule.when_matches(instruction, market_state.now()):
            algo_cls = algo_registry[rule.then.algo]
            return algo_cls(params=rule.then.params, cost_model=policy.cost_model_ref)
    raise NoRuleMatched(instruction, policy)
```

## Policy evolution

- Daily/weekly tuning = new minor version (same algo, new params)
- Algo swap = new major version
- Scope change = new policy (don't mutate applicability)
- Shadow deployments: run old + new policy in parallel, compare exec alpha before promoting

## Not in this doc

- **Venue eligibility** — [../axes/venue-eligibility.md](../axes/venue-eligibility.md); policy assumes venue is already
  eligible
- **SOR among eligible venues** — [venue-selection-split.md](venue-selection-split.md); SOR picks venue, policy picks
  how to execute ON that venue
- **Risk pre-flight** — [risk-gates.md](risk-gates.md)
- **Algo implementation** — execution-service/algo_library/
- **Per-strategy-family defaults** — individual family docs

## Cross-references

- Architecture: [../../../04-architecture/execution-policy.md](../../../04-architecture/execution-policy.md)
- Artifact versioning:
  [../../../04-architecture/artifact-versioning.md](../../../04-architecture/artifact-versioning.md)
- Benchmark fills: [benchmark-fills.md](benchmark-fills.md)
- Venue selection: [venue-selection-split.md](venue-selection-split.md)
- MEV protection: [mev-protection.md](mev-protection.md)
