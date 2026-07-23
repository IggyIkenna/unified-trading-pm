---
doc_type: codex-ssot
title: Coding Standard — Artifact Naming
summary: >-
  Naming conventions for all versioned artifacts (feature groups, ML models, execution/cost/risk/MEV/bridge policies,
  allocators, conformance suites) — stable lowercase kebab-case families with explicit `@v{N}` pins, monotonic
  per-family integer versions, immutable content per version, and no implicit "latest" resolution anywhere.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [artifact-naming, ml, features, execution, registry, strategy]
related:
  [
    /codex/04-architecture/artifact-versioning.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
    /codex/04-architecture/schema-versioning.md,
  ]
created: 2026-04-17
authoritative_for: [versioned artifact naming conventions]
referenced_by:
  [/codex/04-architecture/artifact-versioning.md, /codex/06-coding-standards/strategy-identity-versioning.md]
owner:
last_reviewed:
code_refs:
---

# Coding Standard — Artifact Naming

> **What it is:** Naming conventions for all versioned artifacts in the system — feature groups, ML models, execution
> policies, cost models, allocator algorithms, risk policies, MEV policies, bridge policies. Consistent naming enables
> cross-service reference, audit, and replay.

## Universal rules

1. **Names are stable** — once published, never renamed
2. **Names are lowercase kebab-case** with optional `@v{N}` suffix for version pin
3. **No category prefix** beyond what the name itself describes
4. **Immutable per version** — `@v3` always resolves to exactly the same content
5. **Domain-specific prefix** for disambiguation

## Reference syntax

```
{artifact_family_name}@v{N}
```

If `@v{N}` omitted in a config, error (no implicit "latest"). Every reference is explicit.

## Feature groups

Pattern: `{category}-{subdomain}-{freq_or_aspect}[-{instrument}]`

Examples:

```
crypto-ohlc-5m@v7
crypto-orderbook-snapshot@v2
crypto-onchain-ethereum@v4
crypto-onchain-solana@v2
crypto-funding-rate@v3
equity-fundamentals@v4
equity-momentum@v3
equity-vol-adjusted@v2
sports-soccer-pre-game@v5
sports-soccer-halftime@v3
sports-soccer-first-half@v2
sports-tennis-in-play@v1
sports-basketball-pre-game@v1
macro-regime-feature@v4
tradfi-ohlc-daily@v5
tradfi-vol-surface-fit@v2
options-iv-surface-svi@v3
```

## ML models

Pattern: `{category}-{instrument_or_universe}-{model_family}-v{N}`

Note: ML models have BOTH a family name (with `V{major}` in ALL CAPS when materially different architecture) and a
monotonic version within family.

Examples:

```
CRYPTO_BTC_CATBOOST_V4@v3          # CatBoost v4 architecture; content version 3
CRYPTO_ETH_CATBOOST_V4@v2
SPORTS_EPL_1X2_CATBOOST_V3@v5
SPORTS_EPL_OU_CATBOOST_V3@v4
EQUITY_CS_CATBOOST_V3@v2           # cross-sectional ranker for Russell 1000
CRYPTO_BTC_XGBOOST_V1@v1           # new architecture comparison
```

Name-family bump (e.g., `CATBOOST_V4` → `CATBOOST_V5`) is a material architecture change warranting shadow deployment.

## Execution policies

Pattern: `{category}-{action}-{use_case}[-v{N}]`

Examples:

```
cefi-crypto-large-size-v3             # (explicit version in policy id)
cefi-crypto-small-size-v1
defi-swap-route-optimizer-v4
defi-liquidation-flashloan-v2
sports-simul-legs-v2
tradfi-basket-execution-v2
tradfi-paired-execution-v2
options-deribit-atomic-v2
market-making-crypto-clob-v5
market-making-sports-event-settled-v3
```

Here, version is part of the name (for human readability) AND pinned via `@v{N}` for registry lookup.

## Cost models

Pattern: `{category}-cost-model`

Examples:

```
cefi-cost-model@v2
defi-cost-model-ethereum@v3
defi-cost-model-arbitrum@v2
sports-cost-model-unity@v1
sports-cost-model-betfair@v1
tradfi-cost-model-ibkr@v3
```

## Allocator algorithms

Pattern: `ALLOCATOR_{archetype}`

Examples:

```
ALLOCATOR_SHARPE_WEIGHTED@v3
ALLOCATOR_KELLY@v2
ALLOCATOR_RISK_PARITY@v4
ALLOCATOR_MIN_CVAR@v1
ALLOCATOR_REGIME_AWARE@v2
ALLOCATOR_FIXED@v1
ALLOCATOR_PNL_WEIGHTED@v2
ALLOCATOR_MANUAL@v1
```

Per-client instance references an archetype + config:

```yaml
allocator_instance_id: "client-A-allocator"
archetype: ALLOCATOR_SHARPE_WEIGHTED
archetype_version: 3
config_hash: abc123...
config_version: 7
```

## Risk policies

Pattern: `RISK_{scope}`

Examples:

```
RISK_FIRM_WIDE@v5
RISK_CLIENT_{client_id}@v12
RISK_FAMILY_VOL_TRADING@v2
RISK_FAMILY_CARRY_AND_YIELD@v1
RISK_VENUE_BINANCE@v3
```

## MEV policies

Pattern: `mev-{chain}-{use_case}`

Examples:

```
mev-mainnet-swap-standard@v3
mev-mainnet-large-swap@v4
mev-l2-swap-arbitrum@v2
mev-liquidation-flashbots@v1
```

## Bridge policies

Pattern: `bridge-{from_chain}-{to_chain}-{use_case}`

Examples:

```
bridge-ethereum-arbitrum-fast@v3
bridge-ethereum-optimism-stargate@v2
bridge-multi-chain-cctp-usdc@v4
bridge-solana-evm-wormhole@v1
```

## Strategy configs

Pattern: `config_hash + config_version` — NOT a free name. Referenced by tuple `(strategy_instance_id, config_version)`
in registry.

## Conformance test suites

Pattern: `conformance-{artifact_family}`

Examples:

```
conformance-algo-TWAP@v2
conformance-policy-cefi-crypto-large@v3
conformance-model-CRYPTO_BTC_CATBOOST_V4@v3
```

## Versioning rules (cross-artifact)

- Version numbers are monotonic integers (1, 2, 3, ...), scoped to artifact family
- Never skip, never reorder, never re-use
- No "1.0.0" semver on internal artifacts — plain monotonic
- Only UAC uses semver (external/wire schemas)

## Publishing flow

1. New artifact prepared locally
2. Content-hash computed
3. Conformance tests run
4. If passed → registry accepts; assigns next version
5. Publishes `ARTIFACT_PUBLISHED` event
6. Consumer services can reference (but don't auto-upgrade)

## Consumer pinning

Every consumer config pins by explicit `@v{N}`:

```yaml
# strategy config
model_ref: CRYPTO_BTC_CATBOOST_V4@v3
feature_group_refs:
  - crypto-ohlc-5m@v7
  - crypto-onchain-ethereum@v4
execution_policy_ref: cefi-crypto-large-size-v3
cost_model_ref: cefi-cost-model@v2
risk_policy_refs:
  - RISK_CLIENT_client_A@v12
  - RISK_FAMILY_ML_DIRECTIONAL@v1
```

No implicit "latest" resolution anywhere.

## Registry URLs

```
GET  /artifacts/{family}                            → list versions
GET  /artifacts/{family}/@v{N}                      → content + meta
GET  /artifacts/{family}/@v{N}/meta                 → just metadata
POST /artifacts/{family}                            → publish new version
```

## Anti-patterns

- **Implicit latest**: `model_ref: CRYPTO_BTC_CATBOOST_V4` (no version) — forbidden
- **Semver on non-UAC artifacts**: `model_ref: CRYPTO_BTC_CATBOOST_V4@v1.2.3` — plain integers only
- **Renaming an artifact family**: `CRYPTO_BTC_CATBOOST_V4` → `BTC_CATBOOST_V4` — forbidden; publish new family name
- **Mutable content per version**: `@v3` changes between requests — forbidden; immutable
- **Hash without version**: reference by content hash alone — allowed internally; not for configs

## Cross-references

- Artifact versioning architecture:
  [/codex/04-architecture/artifact-versioning.md](/codex/04-architecture/artifact-versioning.md)
- Strategy identity + versioning: [strategy-identity-versioning.md](strategy-identity-versioning.md)
- Schema versioning (separate axis):
  [/codex/04-architecture/schema-versioning.md](/codex/04-architecture/schema-versioning.md)
- Venue capability registry (semver):
  [/codex/03-services/venue-capability-registry.md](/codex/03-services/venue-capability-registry.md)

## Not in this doc

- **Per-artifact content schemas** — owning service
- **Storage backend** — registry implementation
- **Build / CI release flow** — deployment-service
- **UI codegen from artifacts** — UI repos
