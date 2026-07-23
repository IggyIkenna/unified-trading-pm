---
doc_type: codex-ssot
title: Coding Standard — Strategy Identity + Versioning
summary: >-
  Strategy identity + versioning rules — the 5-layer identity (family→archetype→instance→config→derived categories),
  archetype-ID structural-descriptor rules (no CEFI_/DEFI_/TRADFI_ prefixes), the slot-label grammar, config
  content-hash + monotonic version, the -vN slot suffix, the full event-tag tuple, and the QG enforcement checks.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, strategy-service]
scope: [engineer]
tags: [strategy, versioning, uac, quality-gates, execution]
related:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/06-coding-standards/strategy-display-conventions.md,
    /codex/06-coding-standards/artifact-naming.md,
    /codex/04-architecture/artifact-versioning.md,
  ]
created: 2026-04-17
authoritative_for: [strategy identity + versioning (5-layer identity, archetype-ID rules, slot-label grammar)]
referenced_by:
  [
    /codex/02-data/feature-formula-versioning.md,
    /codex/04-architecture/artifact-versioning.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/data-flow-map.md,
    /codex/04-architecture/schema-versioning.md,
    /codex/04-architecture/shadow-deployment-pattern.md,
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/artifact-naming.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Coding Standard — Strategy Identity + Versioning

> **What it is:** Mandatory naming + versioning rules for strategies. Every strategy in the system has a 5-layer
> identity (family → archetype → instance → config → derived categories), a slot label, version tuples, and full event
> tags. These rules are enforced at QG.

## The 5 layers

| Layer              | Values                           | Change semantics                     |
| ------------------ | -------------------------------- | ------------------------------------ |
| Family             | 8 enum                           | Never (new family = new code domain) |
| Archetype          | 18 enum                          | Build version bumps on code change   |
| Instance           | slot_label                       | Created once; retired later          |
| Config             | content hash + monotonic version | Any config change bumps              |
| Derived categories | multi-valued lists               | Derived from venues; never stored    |

## Archetype ID rules

Archetype IDs:

- **MUST use structural descriptors**: `CONTINUOUS`, `EVENT_SETTLED`, `PAIRS_FIXED`, `CROSS_SECTIONAL`, `BASIS_DATED`,
  `BASIS_PERP`
- **MUST NOT encode execution category**: no `CEFI_`, `DEFI_`, `TRADFI_`, `SPORTS_`, `PREDICTION_` prefixes
- **MUST be stable** — once published, never renamed; new logic = new archetype ID

### Valid

```
ML_DIRECTIONAL_CONTINUOUS
ML_DIRECTIONAL_EVENT_SETTLED
RULES_DIRECTIONAL_CONTINUOUS
CARRY_BASIS_DATED
CARRY_STAKED_BASIS
ARBITRAGE_PRICE_DISPERSION
MARKET_MAKING_CONTINUOUS
VOL_TRADING_OPTIONS
STAT_ARB_PAIRS_FIXED
STAT_ARB_CROSS_SECTIONAL
```

### Invalid

```
CEFI_ML_DIRECTIONAL              # category prefix forbidden
ML_DIRECTIONAL                   # missing structural axis (continuous vs event-settled)
TRADFI_OPTIONS_ML                # category + non-structural
SPORTS_MM                        # category prefix + truncation
```

## Slot label grammar

```
{archetype_id}@{venue_scope}-{instrument_scope}[-{timeframe}]-{share_class}[-v{N}]-{env}
```

Rules:

- `archetype_id` from the 18-enum
- `venue_scope`: venue abbrev(s); multi-venue uses `-` (e.g., `binance-okx`)
- `instrument_scope`: instrument abbrev(s) (e.g., `btc`, `eth`, `russell1000`)
- `timeframe` optional when archetype implies (e.g., Cross-sectional daily); included when strategy-specific
- `share_class` lowercased (usdt, usdc, usd, eth, btc, sol, gbp, eur)
- `v{N}` optional slot version (`-v2`, `-v3`) for material dependency change warranting distinction
- `env` ∈ {prod, paper, canary, dev}

### Examples (valid)

```
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod
CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod
YIELD_ROTATION_LENDING@aave-multichain-usdc-prod
ARBITRAGE_PRICE_DISPERSION@unity-epl-1x2-usd-prod
STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod
VOL_TRADING_OPTIONS@deribit-btc-vol-usdt-prod
MARKET_MAKING_EVENT_SETTLED@betfair-epl-mm-gbp-prod
```

### Examples (invalid)

```
ml-directional@btc                     # missing venue, share class, env
CEFI_ML_DIRECTIONAL@binance-btc-5m-usdt-prod        # category prefix on archetype
ML_DIRECTIONAL_CONTINUOUS@BINANCE-BTC-5m-USDT-prod   # caps inconsistent
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt    # missing env
```

## Config hash + version

### Config hash

- Computed from config content (JSON-serialized, deterministic key order)
- Hash algorithm: SHA-256 truncated to 16 hex chars (e.g., `a7f3b2e1c9d4f8a0`)
- Any content change → new hash

### Config version

- Monotonic integer, scoped to `(slot_label)`
- Increments on every content change
- Persisted per-slot in config registry

### Content hash vs version

Content hash is identity; version is ordinal. Two configs with identical content have same hash regardless of order; but
versions within a slot are always increasing.

## Slot version (optional suffix)

Slot version bumps when a dependency change is material enough to warrant a human-visible distinction:

- Model family swap (CatBoost → XGBoost)
- Feature group major-version bump
- Venue swap (Binance → OKX primary)
- Staking method swap (fractional Kelly → Risk Parity)

Config version alone is insufficient because the new slot is materially a "different strategy" for observability +
reporting purposes. Example:

```
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod       (v1, CatBoost model)
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod    (XGBoost model)
```

These run in parallel (shadow), compared, and eventually one retires.

## Event tag (full tuple)

Every fill, instruction, PnL row, audit entry carries:

```
(
  family,
  archetype_id,
  archetype_build_version,
  strategy_instance_id,
  slot_version,
  config_hash,
  config_version,
  client_id,
  share_class
)
```

`strategy_instance_id` encodes the slot label. `slot_version` is the integer after `-v` in the slot label (default 1 if
no suffix).

## Archetype build version

- Git-SHA based: `{semver}-{git_sha[:7]}`
- Semver from release tag of strategy-service
- Incremented on every strategy-service release

Example: `1.4.2-a7f3b2e`

## Category derivation (multi-valued)

Never hardcode category on the strategy. Derive from venues:

```python
def derive_execution_categories(config):
    return sorted(set(
        venue_registry.get(v).category
        for v in config.execution_venues
    ))

def derive_data_categories(config):
    return sorted(set(
        venue_registry.get(v).category
        for v in config.all_data_subscriptions
    ))
```

For UI + reporting only; never for code routing.

## Instance registration

At creation, the slot is registered with:

```yaml
strategy_instance_id: "ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod"
archetype_id: ML_DIRECTIONAL_CONTINUOUS
family: ML_DIRECTIONAL
client_id: "client_A_fund"
capital_budget_share_class_amount: 2_500_000
capital_budget_share_class: USDT
risk_budget:
  max_daily_loss_bps: 200
  max_drawdown_bps: 500
share_class: USDT
env: prod
created_at_utc: "2026-04-17T00:00:00Z"
created_by: operator@firm
```

Registered in the strategy registry (UAC SSOT) — not hand-maintained per CLAUDE.md memory.

## QG enforcement

The following are checked at quality gates:

1. `archetype_id` ∈ 18-enum (no freeform strings)
2. `slot_label` matches grammar regex
3. No category prefix in archetype ID
4. `share_class` lowercase
5. `env` ∈ {prod, paper, canary, dev}
6. `venue_scope` tokens all in venue registry
7. `share_class` compatible with venue set per share-class axis rules
8. Config hash computed and matches declared hash
9. Config version monotonic (greater than last-persisted version for this slot)
10. Every event carries full event tag

## Retirement

To retire an instance:

1. Kill switch: `DISABLED`
2. Unwind positions (via `AccountInstruction.CLOSE_ALL_FOR_STRATEGY`)
3. Mark instance status `RETIRED` with timestamp
4. Audit log retained permanently
5. Slot label NEVER re-used — if rebirth needed, use `-v2` suffix

## Anti-patterns

- **Renaming an archetype** — never; make a new one
- **Re-using a slot label** — never; pick a new instance id or bump `-v`
- **Hardcoding category in archetype ID** — forbidden
- **Skipping config version** — always monotonic
- **Emitting events without full tag** — rejected at QG
- **Strategy code reading `strategy_instance_id` to branch behavior** — violates archetype-as-code-path; if branching
  needed, separate archetype

## Cross-references

- Full architecture: [/codex/09-strategy/architecture-v2/README.md](/codex/09-strategy/architecture-v2/README.md)
- Strategy-execution protocol:
  [/codex/04-architecture/strategy-execution-protocol.md](/codex/04-architecture/strategy-execution-protocol.md)
- Artifact versioning: [/codex/04-architecture/artifact-versioning.md](/codex/04-architecture/artifact-versioning.md)
- Schema versioning: [/codex/04-architecture/schema-versioning.md](/codex/04-architecture/schema-versioning.md)
- Artifact naming: [artifact-naming.md](artifact-naming.md)

## Not in this doc

- **Per-artifact naming** — [artifact-naming.md](artifact-naming.md)
- **Code module layout** — contribution-guide.md
- **CI/CD release flow** — deployment-service
- **UI naming conventions** — UI repos
