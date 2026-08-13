---
doc_type: codex-ssot
title: Execution Policy (Architecture View)
summary:
  Internal architecture of execution policies as versioned content-hashed registry artifacts — YAML rule format,
  first-match-wins evaluation engine, applies_to gating, cost-model refs, shadow mode, and conformance/back-tests.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [execution, strategy, registry, canonicalisation, verification]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
    /codex/04-architecture/artifact-versioning.md,
    /codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md,
  ]
created: 2026-04-17
authoritative_for: [execution-policy artifact registry and rule-evaluation engine]
referenced_by:
  [
    /codex/04-architecture/artifact-versioning.md,
    /codex/04-architecture/backtest-groups.md,
    /codex/04-architecture/slow-fast-routing-split.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
  ]
owner:
last_reviewed: 2026-09-02
code_refs:
---

# Execution Policy (Architecture View)

> **What it is:** The artifact format + registry + runtime lookup for execution policies. Companion to
> [/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md](/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md)
> (which covers the strategy-facing perspective). This doc covers the _internal architecture_ of execution policies as
> first-class artifacts.

## Policy as artifact

An execution policy is a versioned artifact in the registry. Content-hashed. Immutable per version. Consumer-opt-in
upgrades.

### File format

```yaml
# execution_policy/cefi-crypto-large-size/v3.yaml
schema_version: 1 # policy schema version (not semver on content)
policy_id: cefi-crypto-large-size
version: 3
parent_version: 2 # for diff review
content_hash: <computed>
created_at_utc: "2026-04-10T12:00:00Z"
created_by: exec-team
description: "Large-size CEX crypto execution with TWAP + cost cap"

applies_to:
  action: TRADE
  venue_categories: [CEFI]
  instrument_types: [SPOT, PERP]
  urgency: [LOW, MEDIUM]

rules:
  - id: small-size
    when:
      notional_usd: { "<": 50_000 }
    then:
      algo: MARKET_SWEEP
      params:
        max_slippage_bps: 10

  - id: medium-size
    when:
      notional_usd: { ">=": 50_000, "<": 500_000 }
    then:
      algo: TWAP
      params:
        slice_count: 10
        window_seconds: 300
        participation_rate: 0.20

  - id: large-size
    when:
      notional_usd: { ">=": 500_000 }
    then:
      algo: TWAP
      params:
        slice_count: 30
        window_seconds: 1800
        participation_rate: 0.10
        dark_pool_opt_in: false

cost_model_ref: cefi-cost-model@v2
benchmark_mode_ref: vwap-window@v1

conformance_tests:
  - name: small_size_picks_sweep
    input: { action: TRADE, notional_usd: 10_000 }
    expected_algo: MARKET_SWEEP
  - name: large_size_picks_twap
    input: { action: TRADE, notional_usd: 1_000_000 }
    expected_algo: TWAP
```

## Rule evaluation engine

Policies are executed by a simple interpreter:

```python
def resolve_algo(instruction, policy):
    ctx = evaluation_context(instruction, market_state.now())
    for rule in policy.rules:
        if match(rule.when, ctx):
            return rule.then.algo, rule.then.params
    raise NoMatchingRule(instruction, policy)
```

`match()` supports:

- Scalar comparisons: `{"<": 50_000}`, `{"<=": X}`, `{"==": X}`, `{"in": [...]}`, `{"not_in": [...]}`
- Compound (implicit AND): multiple keys in `when`
- Explicit `any_of` / `all_of` for OR/AND groups
- References: `{"venue": "BINANCE"}`, `{"instrument_type": "PERP"}`, etc.

## Rule ordering

Rules evaluated **in document order**. First match wins. Default-deny: if no match, error (`NoMatchingRule`). Policies
should include a catch-all if they want default behavior.

## Applies-to gating

Before rule evaluation, execution-service checks `applies_to`:

- Action type matches (else policy skipped; try next policy_ref if any)
- Venue category matches
- Instrument type matches
- Urgency matches

This allows a single strategy to reference multiple policies in priority order if needed:

```yaml
execution_policy_refs:
  - cefi-crypto-large-size@v3 # first try this
  - cefi-crypto-fallback@v1 # catch-all fallback
```

## Cost model reference

Each policy points at a cost model artifact:

```yaml
# cost_model/cefi-cost-model/v2.yaml
venues:
  BINANCE:
    fee_tier_default: VIP_0
    fee_bps_by_tier: { VIP_0: 10.0, VIP_1: 9.0, VIP_3: 7.5, VIP_5: 4.5 }
    taker_maker_ratio_default: 0.7 # 70% taker, 30% maker
    slippage_curve:
      size_usd_to_bps:
        - [10_000, 2]
        - [100_000, 8]
        - [1_000_000, 25]
  OKX: ...
```

Strategies may use the cost model at emission time (for net-edge go/no-go); execution uses it at algo-picking time.

## Policy registry

> **SPEC, not shipped (verified 2026-08-12).** The REST surface below does not exist. What exists is
> `execution-service/execution_service/v2/execution_policies.py`: the artifact dataclasses (`ExecutionPolicyArtifact` /
> `AppliesTo` / `PolicyRule`), content-hashing, and the full first-match-wins / default-deny rule evaluator — faithful
> to this doc's contract, and **with zero consumers.** The types appear only in `v2/__init__.py` re-export plumbing;
> `register()` is in-memory, there is no `client_id` / `slot_label` keying, no GCS loader and no hot reload. Separately,
> the `config_algorithm` hook that would carry a resolved policy into `selector.select_algorithm()` is threaded through
> three levels and **supplied by no call site**. So policies are currently a correct artifact nothing evaluates. Wiring
> plan: `/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` §§ B, G.

Registry service holds all published policies:

```
GET /policies/cefi-crypto-large-size          → [v1, v2, v3]
GET /policies/cefi-crypto-large-size/v3        → content + meta
GET /policies/cefi-crypto-large-size/latest    → v3 (informational; do NOT use for pinning)
POST /policies/ (new version)                  → publishes after conformance check
```

Publishing requires:

- Passes all conformance tests
- Diff-review approved (human sign-off for high-blast-radius policies)
- Not a downgrade (`version > parent_version`)

## Testing

### Conformance tests (per policy)

Declared inline in the policy; run on publish. Verify rule evaluation outputs expected algos for anchor cases.

### Back-tests (policy-level)

Group C backtest (execution alpha): run the same StrategyInstruction history through old and new policies; compare
execution alpha. Decision to promote new version uses this comparison.

### Unit tests (engine-level)

Rule evaluator tested with synthetic policies covering all `match()` operators.

## Algo library versioning

Algos themselves are artifacts:

```yaml
# algo/TWAP/v2.yaml
algo_name: TWAP
version: 2
params_schema:
  slice_count: { type: int, required: true }
  window_seconds: { type: int, required: true }
  participation_rate: { type: float, default: 0.25 }
benchmark_fill: |
  def benchmark_fill(window, market_state):
      return time_weighted_mid(market_state, window)
```

Policy's `algo` field maps to current-major-version default; pin with `@vN` syntax if specific version needed:

```yaml
algo: TWAP@v2
```

## Policy × venue × instrument matrix

Different venues need different policies for the same action. The `applies_to` filter + first-match-wins mechanic
naturally supports:

```
Strategy references: [binance-spot-large@v3, okx-spot-large@v2, bybit-spot-large@v1]
For a BINANCE order, binance-spot-large matches first
For an OKX order, okx-spot-large matches first
```

Or a single multi-venue policy:

```yaml
policy_id: cefi-spot-large-all-venues
rules:
  - when: { venue: BINANCE, notional_usd: { ">=": 500_000 } }
    then: { algo: TWAP, params: { ... } }
  - when: { venue: OKX, notional_usd: { ">=": 500_000 } }
    then: { algo: TWAP, params: { ... } }
  - when: { venue: BYBIT, notional_usd: { ">=": 500_000 } }
    then: { algo: TWAP, params: { ... } }
```

Both patterns supported; team preference.

## Shadow mode

A policy can be deployed in **shadow mode**:

```yaml
# strategy config
execution_policy_ref: cefi-crypto-large-size@v3
shadow_policy_ref: cefi-crypto-large-size@v4 # runs alongside, no effect
```

Execution computes algo + params for both; uses `execution_policy_ref` for actual submission; logs both for comparison.
After N ticks, promote shadow to primary if exec-alpha improves.

## Breakage handling

If a resolved algo or param is invalid (algo deprecated, param out of range), execution emits `POLICY_RESOLUTION_FAILED`
and falls back to `execution_policy_fallback_ref` if declared, else `INSTRUCTION_REJECTED_EXECUTION`.

> **SPEC, not shipped (verified 2026-07-31).** Neither `POLICY_RESOLUTION_FAILED` nor `INSTRUCTION_REJECTED_EXECUTION`
> exists in code. The shipped analogue on the RISK side is `INSTRUCTION_REJECTED_RISK` (UAC
> `canonical/crosscutting/risk_rule/_events.py`) — the execution-side counterparts still need to be added to the
> instruction-lifecycle event set.

## Security / change control

High-impact policies (affecting > $X daily notional) require:

- PR review
- Shadow deploy window
- Operator sign-off
- Audit log entry

Low-impact (param tuning) can deploy with CI-only approval.

## Cross-references

- Strategy-facing view:
  [/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md](/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md)
- Artifact versioning: [artifact-versioning.md](artifact-versioning.md)
- Benchmark fills:
  [/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md](/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md)
- Execution-service algo library: execution-service/algo_library/

## Not in this doc

- **Strategy-side algo selection logic** —
  [/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md](/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md)
- **Algo implementations** — code
- **Per-venue adapter code** — code
- **MEV policy specifics** —
  [/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md](/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md)
