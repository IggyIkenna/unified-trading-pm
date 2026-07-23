---
doc_type: codex-ssot
title: Client Onboarding — Cross-Cutting Concern
summary:
  The one-strategy-instance-per-client rule and onboarding flow — every client gets a unique (client_id, strategy_id)
  with separate positions/config/PnL/margin across all asset classes; covers venue+credential setup, GCS config overlay
  + hot-reload, verification, expected position divergence, and client removal.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [onboarding, client-config, strategy, defi, cefi, execution]
related:
  [
    /codex/09-strategy/operational/onboarding-checklist.md,
    /codex/09-strategy/operational/client-strategy-config.md,
    ../../04-architecture/interface-credential-convention.md,
  ]
created: 2026-03-27
authoritative_for: [one-strategy-instance-per-client onboarding rule + per-client position-divergence model]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    /codex/09-strategy/operational/client-strategy-config.md,
    /codex/09-strategy/operational/onboarding-checklist.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Client Onboarding — Cross-Cutting Concern

## Core Rule: One Strategy Instance Per Client

Every client gets their own strategy instance with a unique `(client_id, strategy_id)` tuple. The strategy **template**
is shared (same code, same logic), but each client has:

- **Separate positions** — execution timing causes drift (client A fills at 3500, client B at 3501)
- **Separate config** — same defaults, but per-client overrides possible (allocation %, max leverage)
- **Separate PnL** — attributed independently to each client's positions
- **Separate margin** — health factor / LTV tracked per client account

This is non-negotiable across ALL asset classes (DeFi, CeFi, TradFi, Sports).

## Onboarding Flow

### 1. Venue Account Setup

| Step                    | Who          | What                                                                            |
| ----------------------- | ------------ | ------------------------------------------------------------------------------- |
| Create venue accounts   | HUMAN        | Exchange accounts (Binance, Hyperliquid), DeFi wallets, sports betting accounts |
| Generate API keys       | HUMAN        | Per-client keys for each venue                                                  |
| Store in Secret Manager | HUMAN/SCRIPT | Pattern: `exec-{client_id}-{venue}-{account_type}`                              |
| Verify access           | SCRIPT       | `credential-audit.py --client {client_id} --check-access`                       |

### 2. Strategy Config

```yaml
# GCS: gs://config/{strategy_id}/clients/{client_id}.yaml
client_id: "odum"
strategy_template: "DEFI_ETH_STAKED_BASIS_SCE_1H"
initial_capital: 100000
allocation:
  spot_pct: 0.90
  margin_pct: 0.10
overrides:
  min_combined_apy: 0.05 # Can be client-specific
  max_leverage: 2.5
```

**Hot-reload?** YES — UCI config watcher picks up new client configs from GCS without restart.

### 3. Service Configuration

| Service                          | What Changes                                            | Restart Required? |
| -------------------------------- | ------------------------------------------------------- | ----------------- |
| strategy-service                 | New client config in GCS                                | No (hot-reload)   |
| execution-service                | New client routing rule (client → venue accounts)       | No (hot-reload)   |
| position-balance-monitor-service | Auto-discovers new positions                            | No                |
| risk-and-exposure-service        | Auto-aggregates new client                              | No                |
| alerting-service                 | No change (alert rules are strategy-level)              | No                |
| features-\* services             | No change (features are market-level, not client-level) | No                |

### 4. Verification

- [ ] Strategy instance starts for new client
- [ ] Positions initialised at 0
- [ ] Market data flowing (features fresh per SLA)
- [ ] Execution test: place and cancel a small test order
- [ ] PnL attribution: verify initial equity matches capital
- [ ] Margin health: verify HF/LTV baseline
- [ ] UI: client appears in dashboard

## Position Divergence

Even though all clients run the same strategy template, positions WILL diverge over time because:

1. **Execution timing** — fills happen at slightly different prices
2. **Slippage** — different for larger vs smaller accounts
3. **Gas timing** — DeFi transactions mine in different blocks
4. **Rebalancing** — triggered at different times due to position differences

This is expected and normal. The system handles it by tracking each client's positions independently.

## Client Strategy Config Overrides

Per-client overrides are stored in UAC `ClientStrategyOverride` model and applied at strategy instance initialization.
These allow tailoring strategy behavior without forking the strategy code.

| Field                     | Type        | Description                                                     | Example (Patrick)             |
| ------------------------- | ----------- | --------------------------------------------------------------- | ----------------------------- |
| `allowed_perp_venues`     | `list[str]` | Venue whitelist for perp legs. Empty = all allowed.             | `["OKX", "BYBIT", "BINANCE"]` |
| `multi_coin_rotation`     | `bool`      | Enable/disable multi-coin waterfall in basis strategies.        | `false`                       |
| `fixed_basis_coin`        | `str`       | Lock basis trade to a single coin. Disables Pillar 1 weighting. | `"ETH"`                       |
| `dynamic_venue_weighting` | `bool`      | Use funding-rate-proportional venue weights vs equal weights.   | `false`                       |
| `max_leverage`            | `Decimal`   | Cap on leverage for recursive strategies.                       | `2.5`                         |
| `share_class`             | `str`       | Base currency denomination for P&L (USDT, ETH, BTC).            | `"ETH"`                       |

**How overrides are applied:**

1. Strategy-service loads the base strategy config from GCS (`gs://config/{strategy_id}/base.yaml`).
2. Client overlay is loaded from GCS (`gs://config/{strategy_id}/clients/{client_id}.yaml`).
3. `ClientStrategyOverride` fields in the overlay replace the corresponding base config fields.
4. Validation: overrides are type-checked against the UAC model. Invalid overrides fail loud at init.
5. Hot-reload: config watcher picks up changes to client overlays without service restart.

**Example: Patrick's config overlay:**

```yaml
client_id: "patrick"
overrides:
  allowed_perp_venues: ["OKX", "BYBIT", "BINANCE"]
  multi_coin_rotation: false
  fixed_basis_coin: "ETH"
  dynamic_venue_weighting: false
  share_class: "ETH"
```

This restricts Patrick to OKX/Bybit/Binance only (no Hyperliquid, no Aster), disables multi-coin rotation (ETH only),
uses equal venue weighting instead of funding-rate-proportional, and denominates P&L in ETH.

## Removing a Client

1. Strategy instance generates EXIT signal → closes all positions
2. Verify all positions flat
3. Remove client config from GCS
4. Archive PnL history
5. Remove secrets from Secret Manager (or retain for audit trail)
