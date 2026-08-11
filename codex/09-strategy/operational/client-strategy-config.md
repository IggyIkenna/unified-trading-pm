---
doc_type: codex-ssot
title: Per-Client Strategy Config Overrides
summary:
  The ClientStrategyOverride UAC schema + ClientConfigRegistry that customise per-client strategy execution (venue
  whitelists, multi-coin-rotation/dynamic-weighting gating, fixed_basis_coin, max_leverage/max_position) without forking
  strategy code; applied once at init via _apply_client_venue_filter, with the Patrick DeFi-tier reference.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [client-config, strategy, uac, defi, onboarding]

  [
    /codex/09-strategy/operational/client-onboarding.md,
    /codex/09-strategy/operational/onboarding-checklist.md,
    ../../04-architecture/per-client-isolation-architecture.md,
  ]
created: 2026-04-03
authoritative_for: [ClientStrategyOverride per-client config-override schema + venue-restriction mechanism]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/operational/client-onboarding.md,
    /codex/09-strategy/operational/instrument-filtering.md,
    /codex/09-strategy/operational/onboarding-checklist.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Per-Client Strategy Config Overrides

## Overview

Not every client gets the same strategy features. The `ClientStrategyOverride` schema in UAC allows per-client
customisation of strategy execution parameters — venue restrictions, feature gating, position limits — without changing
the base strategy code.

**Schema location**: `unified_api_contracts.internal.domain.strategy_service.client_config`

## Schema

```python
class ClientStrategyOverride(BaseModel):
    client_id: str
    strategy_id: str

    # Venue restrictions (None = all venues allowed)
    allowed_perp_venues: list[str] | None = None
    allowed_spot_venues: list[str] | None = None
    allowed_lending_venues: list[str] | None = None

    # Feature gating (default = full access)
    multi_coin_rotation: bool = True       # False = locked to fixed_basis_coin
    dynamic_venue_weighting: bool = True   # False = equal weights across venues
    strategy_rotation: bool = False        # Future upsell feature

    # Fixed overrides for basic clients
    fixed_basis_coin: str | None = None    # e.g. "ETH" to lock to single coin
    fixed_venue_weights: dict[str, float] | None = None

    # Risk guardrails
    max_leverage: Decimal | None = None
    max_position_usd: Decimal | None = None
```

## Registry

```python
class ClientConfigRegistry(BaseModel):
    overrides: list[ClientStrategyOverride] = []

    def get_override(self, client_id: str, strategy_id: str) -> ClientStrategyOverride | None:
        """Returns None if no override → use strategy defaults."""

    def get_overrides_for_client(self, client_id: str) -> list[ClientStrategyOverride]:
        """All overrides for a client across all strategies."""
```

The registry is loaded from config at strategy-service startup. In test/demo environments, the `PATRICK_OVERRIDES`
fixture is used directly.

## Venue Restriction Mechanism

Strategy-service applies overrides in `_apply_client_venue_filter()`:

1. Load override for `(client_id, strategy_id)` from registry
2. If `allowed_perp_venues` is set: filter `perp_venues` list to intersection
3. If `multi_coin_rotation=False`: replace `basis_coins` with `[fixed_basis_coin]`
4. If `dynamic_venue_weighting=False`: use equal weights instead of funding-rate weights

The two-waterfall weighting in `compute_two_waterfall_weights()` receives the already-filtered venue list — it does not
need to know about overrides.

## Feature Gating

| Feature                       | Basic (default)     | Premium               |
| ----------------------------- | ------------------- | --------------------- |
| Venue restrictions            | Configurable        | Full access           |
| Multi-coin rotation           | Locked (fixed coin) | Enabled               |
| Dynamic venue weighting       | Equal weights       | Funding-rate weighted |
| Strategy rotation             | Disabled            | Future feature        |
| Recursive staking flash loans | Configurable        | Configurable          |

## Reference Example: Patrick (DeFi Client)

Patrick represents the "DeFi guy" client tier — paid for specific DeFi capabilities:

```python
PATRICK_OVERRIDES = ClientConfigRegistry(
    overrides=[
        ClientStrategyOverride(
            client_id="patrick-elysium",
            strategy_id="BASIS_TRADE",
            allowed_perp_venues=["OKX", "BYBIT", "BINANCE"],  # No HyperLiquid, No Aster
            multi_coin_rotation=False,
            dynamic_venue_weighting=False,
            fixed_basis_coin="ETH",
        ),
        ClientStrategyOverride(
            client_id="patrick-elysium",
            strategy_id="STAKED_BASIS",
            allowed_perp_venues=["OKX", "BYBIT", "BINANCE"],
            multi_coin_rotation=False,
            # Staked basis uses equal weights by default — OK for Patrick
        ),
        ClientStrategyOverride(
            client_id="patrick-elysium",
            strategy_id="RECURSIVE_STAKED_BASIS",
            # Full access — he paid for this tier
        ),
        ClientStrategyOverride(
            client_id="patrick-elysium",
            strategy_id="AAVE_LENDING",
            # Full access — basic lending included in tier
        ),
    ]
)
```

**What Patrick gets vs does not get:**

| Capability              | Patrick                  | Premium                     |
| ----------------------- | ------------------------ | --------------------------- |
| Basis trade venues      | OKX, Bybit, Binance only | All 5 venues                |
| Multi-coin rotation     | No (ETH only)            | Yes (top-20 by funding)     |
| Dynamic venue weighting | No (equal weight)        | Yes (funding-rate weighted) |
| Recursive staking       | Yes (full access)        | Yes                         |
| AAVE lending            | Yes (full access)        | Yes                         |

## Integration with Strategy-Service

At strategy initialisation:

```python
# In DeFiBasisStrategy.__init__()
registry = ClientConfigRegistry.from_config(config)
override = registry.get_override(client_id, strategy_id)
if override:
    self._apply_client_venue_filter(override)
```

The override is applied once at startup. Live config reload is supported via the config reloader.

## Upstream Schema

**SSOT**: `unified_api_contracts.internal.domain.strategy_service.client_config`

Services import from UAC internal facade:

```python
from unified_api_contracts.internal import ClientStrategyOverride, ClientConfigRegistry
```

Do not define override schemas locally in service code.
