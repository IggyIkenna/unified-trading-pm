---
doc_type: codex-ssot
title: Onboarding Checklist — Cross-Cutting Concern
summary:
  The full 8-phase operational checklist for onboarding a (strategy_id, client_id, config) instance — credential/venue
  setup, strategy+execution+risk+alert config YAMLs, data-pipeline wiring, sharding, batch jobs, staged live rollout,
  and docs — plus the shorter new-client-vs-new-strategy quick references.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-service,
    execution-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [onboarding, runbook, client-config, strategy, deployment, execution]
related:
  [
    /codex/09-strategy/operational/client-onboarding.md,
    /codex/09-strategy/operational/client-strategy-config.md,
    ../architecture-v2/strategy-catalogue-3tier.md,
    ../architecture-v2/strategy-registry-v2.md,
  ]
created: 2026-03-27
authoritative_for: [8-phase strategy/client onboarding operational checklist]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    /codex/09-strategy/operational/client-onboarding.md,
    /codex/09-strategy/operational/client-strategy-config.md,
    plans/epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Onboarding Checklist — Cross-Cutting Concern

## Overview

This checklist covers the complete operational process for onboarding a new strategy instance or a new client. A
"strategy instance" is a `(strategy_id, client_id, config)` tuple — the atomic unit of execution in the system
(canonical SSOTs: [`../architecture-v2/strategy-catalogue-3tier.md`](../architecture-v2/strategy-catalogue-3tier.md),
[`../architecture-v2/strategy-registry-v2.md`](../architecture-v2/strategy-registry-v2.md), and UAC `ConfigRegistry`;
repointed 2026-05-12 per slot 8 strategy audit ST-13 — the legacy
`_archived_pre_v2/cross-cutting/config-architecture.md` cross-reference is superseded).

Two onboarding scenarios:

| Scenario                    | What Changes                         | Typical Timeline |
| --------------------------- | ------------------------------------ | ---------------- |
| **New strategy for client** | New strategy_id + config + pipeline  | 2–5 days         |
| **New client for strategy** | New client_id + config + credentials | 1–2 days         |

## Phase 1: Venue & Credential Setup

### 1.1 Venue Account Creation

- [ ] Create venue accounts for the client on all required venues
- [ ] Enable API access on each venue account
- [ ] Configure IP whitelisting for production service IPs
- [ ] Set sub-account structure if required (isolated margin per strategy)
- [ ] Record account IDs in client config

### 1.2 API Credential Storage (Secret Manager)

All credentials go into Google Secret Manager. Interfaces are API-keyless — services fetch credentials at runtime and
inject them via constructor params.

```bash
# CeFi venue credentials
gcloud secrets create {client_id}-{venue}-api-key --data-file=key.txt
gcloud secrets create {client_id}-{venue}-api-secret --data-file=secret.txt

# DeFi wallet credentials
gcloud secrets create {client_id}-defi-wallet-private-key --data-file=pk.txt

# Grant access to service accounts
gcloud secrets add-iam-policy-binding {client_id}-{venue}-api-key \
  --member="serviceAccount:execution-service@{project}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Credential naming convention:**

| Secret Name Pattern                   | Used By           | Example                        |
| ------------------------------------- | ----------------- | ------------------------------ |
| `{client_id}-{venue}-api-key`         | execution-service | `odum-binance-api-key`         |
| `{client_id}-{venue}-api-secret`      | execution-service | `odum-binance-api-secret`      |
| `{client_id}-defi-wallet-private-key` | execution-service | `odum-defi-wallet-private-key` |
| `{client_id}-{venue}-passphrase`      | execution-service | `odum-okx-passphrase`          |

### 1.3 DeFi-Specific Setup

For DeFi strategies, additional on-chain setup is required:

- [ ] Fund wallet with native gas token (ETH for L1, ETH for L2s)
- [ ] Deploy flash loan receiver contract if using Aave flash loans:
  ```bash
  bash deployment-service/scripts/deploy-flash-loan-receiver.sh --chain sepolia
  ```
- [ ] Record contract addresses in UAC `config/testnet_contracts.yaml`
- [ ] Verify deployed contracts: `eth_getCode` returns non-empty bytecode
- [ ] Approve token spending for relevant protocols (ERC20 approvals)

## Phase 2: Strategy Configuration

### 2.1 Strategy Config YAML

Create the strategy config file in GCS:

```yaml
# gs://config/{strategy_id}/clients/{client_id}.yaml
strategy_id: DEFI_ETH_BASIS
client_id: odum
version: 1

# Instrument selection
instruments:
  - "WALLET:SPOT_ASSET:ETH"
  - "CEX:PERP:ETH-USDT:BINANCE"

# Signal thresholds
signal:
  min_funding_rate: 0.0001
  min_basis_bps: 15
  entry_threshold: 0.02
  exit_threshold: -0.005

# Position sizing
sizing:
  spot_allocation_pct: 0.90
  max_position_usd: 500000
  max_leverage: 3.0

# Risk limits
risk:
  min_health_factor: 1.5
  max_drawdown_pct: 10
  max_delta_drift: 0.02
  stop_loss_pct: 5

# Cost budget
cost_budget:
  max_total_cost_bps: 15
  max_slippage_bps: 8

# Trigger subscriptions
trigger_subscriptions:
  - source: features-delta-one
    filter: funding_rate_changed
    threshold: 0.0001
  - source: features-onchain
    filter: health_factor_changed
    threshold: 0.05

# Venue fee tiers
venue_fee_tiers:
  BINANCE:
    maker_bps: 2.0
    taker_bps: 4.0
  HYPERLIQUID:
    maker_bps: 0.0
    taker_bps: 2.5
```

### 2.2 Config Validation

- [ ] Validate config against TypedDict schema (`strategy-service/strategy_service/config.py`)
- [ ] Run batch backtest with config on historical data (minimum 6 months)
- [ ] Verify cost budget is achievable given current venue fee tiers
- [ ] Confirm instruments exist in instruments-service registry
- [ ] Verify risk limits are consistent (e.g., `max_leverage` compatible with `min_health_factor`)

### 2.3 Execution Config

```yaml
# gs://config/execution/{strategy_id}/clients/{client_id}.yaml
execution_style: passive # passive | aggressive | urgent
preferred_algo: TWAP # default algo for TRADE instructions
child_order_size_usd: 10000 # max size per child order
max_orders_per_second: 5 # venue rate limit
gas_config:
  max_gas_price_gwei: 50 # DeFi gas ceiling
  priority_fee_gwei: 2.0 # EIP-1559 priority fee
allowed_venues:
  - BINANCE
  - HYPERLIQUID
  - UNISWAP_V3-ETHEREUMEREUM
```

## Phase 3: Risk Limits & Monitoring

### 3.1 Risk Limit Configuration

- [ ] Set position limits per instrument per client
- [ ] Set portfolio-level exposure limits
- [ ] Set drawdown limits (daily, weekly, total)
- [ ] Set concentration limits (max % in single instrument)
- [ ] Configure margin alert thresholds

```yaml
# gs://config/risk/{client_id}/risk_limits.yaml
position_limits:
  per_instrument_usd: 500000
  portfolio_total_usd: 2000000
  max_instruments: 10

exposure_limits:
  max_gross_exposure_usd: 5000000
  max_net_exposure_usd: 1000000
  max_single_venue_pct: 60

drawdown_limits:
  daily_max_pct: 3
  weekly_max_pct: 7
  total_max_pct: 15
  action_on_breach: pause_strategy # pause_strategy | reduce_exposure | alert_only

margin_alerts:
  elevated_hf: 1.5
  warning_hf: 1.2
  critical_hf: 1.05
  auto_deleverage: true
  target_hf_on_deleverage: 2.0
```

### 3.2 Alerting Configuration

- [ ] Configure Telegram alert channel for client
- [ ] Set alert severity routing (which alerts go where)
- [ ] Configure escalation policy (WARN → ELEVATED → CRITICAL)
- [ ] Test alert delivery (send test alert through each channel)

```yaml
# gs://config/alerting/{client_id}/alert_routing.yaml
channels:
  telegram:
    chat_id: "-100XXXXXXXXXX"
    severity_min: warn
  email:
    address: "risk@client.com"
    severity_min: elevated
  pager:
    endpoint: "https://pagerduty.com/integration/xxx"
    severity_min: critical

alert_types:
  - MARGIN_THRESHOLD_BREACHED
  - POSITION_LIMIT_CHECKED
  - COST_DRIFT_DETECTED
  - ML_SIGNAL_STALE
  - FEATURE_STALE
  - ADAPTER_FETCH_FAILED
  - STRATEGY_ERROR
```

## Phase 4: Data Pipeline Wiring

### 4.1 Instrument Registration

- [ ] Verify instruments exist in instruments-service registry
- [ ] If new instruments needed, add to instruments-service config
- [ ] Confirm canonical instrument IDs follow convention: `{VENUE_TYPE}:{PRODUCT}:{SYMBOL}:{VENUE}`

```bash
# Verify instruments are registered
python -c "
from instruments_service.registry import InstrumentRegistry
reg = InstrumentRegistry()
for inst_id in ['WALLET:SPOT_ASSET:ETH', 'CEX:PERP:ETH-USDT:BINANCE']:
    assert reg.get(inst_id) is not None, f'Missing: {inst_id}'
print('All instruments registered')
"
```

### 4.2 Market Data Subscription

- [ ] Configure market-tick-data-service to subscribe to required venue feeds
- [ ] Verify WebSocket connections to required venues
- [ ] Confirm tick data flowing to features pipeline

### 4.3 Feature Pipeline Verification

- [ ] Verify required features-\*-services are computing for target instruments
- [ ] Confirm feature publication to pub/sub topics
- [ ] Check feature freshness (features arriving at expected frequency)
- [ ] Validate feature values are in expected ranges (no NaN, no extreme outliers)

```bash
# Check feature freshness
gsutil ls -l gs://features/delta_one/WALLET:SPOT_ASSET:ETH/$(date +%Y-%m-%d)/
```

### 4.4 ML Model Setup (If Applicable)

- [ ] Verify ML model exists in model registry for strategy
- [ ] Confirm model is promoted to live registry
- [ ] Test ml-inference-api can load and serve predictions
- [ ] Validate prediction latency (< 50ms warm, < 500ms cold)

## Phase 5: Sharding Configuration

### 5.1 Shard Assignment

Sharding config lives in `unified-trading-pm/configs/` (SSOT). Each strategy instance is assigned to a shard.

```yaml
# unified-trading-pm/configs/sharding/{strategy_id}.yaml
shards:
  - shard_id: "defi-eth-basis-shard-1"
    instances:
      - strategy_id: DEFI_ETH_BASIS
        client_id: odum
        config_path: gs://config/DEFI_ETH_BASIS/clients/odum.yaml
      - strategy_id: DEFI_ETH_BASIS
        client_id: alpha
        config_path: gs://config/DEFI_ETH_BASIS/clients/alpha.yaml
    deployment:
      service: strategy-service
      instance_type: Cloud Run
      region: asia-northeast1
      min_instances: 1
      max_instances: 3
```

### 5.2 Shard Validation

- [ ] Verify shard assignment does not exceed per-instance limits
- [ ] Confirm shard has sufficient compute resources for assigned strategies
- [ ] Validate no duplicate `(strategy_id, client_id)` tuples across shards

## Phase 6: Batch Job Setup

### 6.1 Batch Schedule Configuration

- [ ] Configure T+1 reconciliation batch job
- [ ] Set up PnL attribution batch run
- [ ] Configure settlement batch (for strategies with settlement cycles)
- [ ] Verify batch job can access historical data in GCS

```yaml
# Cloud Scheduler job
name: batch-defi-eth-basis-odum
schedule: "0 2 * * *" # 2:00 AM daily
target:
  service: strategy-service
  args:
    --operation: batch
    --mode: batch
    --asset-group: defi
    --strategy-id: DEFI_ETH_BASIS
    --client-id: odum
    --date: yesterday
```

### 6.2 Backfill (Initial Run)

- [ ] Run historical backfill for feature data
- [ ] Run batch backtest to establish baseline performance
- [ ] Verify PnL attribution produces sensible results
- [ ] Compare batch results to expected performance from config validation (Phase 2.2)

## Phase 7: Live Deployment

### 7.1 Pre-Live Checklist

| Check                  | Command / Method                 | Expected Result          |
| ---------------------- | -------------------------------- | ------------------------ |
| Config loads correctly | strategy-service startup logs    | No config errors         |
| Credentials accessible | Secret Manager access audit      | 200 OK on secret fetch   |
| Features flowing       | Feature freshness monitor        | Age < max_staleness      |
| ML model loaded        | ml-inference-api health check    | Model version matches    |
| Risk limits active     | risk-monitoring-service logs     | Limits registered        |
| Alerts configured      | Send test alert                  | Received on all channels |
| Batch job passes       | Run batch for yesterday          | PnL computed, no errors  |
| Venue connectivity     | UTEI/UDEI health check per venue | All venues connected     |
| Margin sufficient      | PBMS margin check                | HF > min_health_factor   |

### 7.2 Staged Rollout

```
Day 1–3: Paper trading (PaperMatchingEngine)
  - Strategy runs live, generates real signals
  - Execution uses PaperMatchingEngine (no real orders)
  - Validate signal quality, frequency, cost estimates

Day 4–7: Small size live
  - Switch to real execution with 10% of target size
  - Monitor fills, slippage, cost vs estimates
  - Verify PnL attribution matches expected

Day 8+: Full size
  - Scale to target position size
  - Continue monitoring for 2 weeks before removing oversight
```

### 7.3 Go-Live Execution

- [ ] Deploy strategy-service with new client config
- [ ] Verify strategy-service logs show new `(strategy_id, client_id)` tuple registered
- [ ] Confirm first feature event processed correctly
- [ ] Monitor first signal generation
- [ ] Monitor first order submission and fill
- [ ] Verify post-trade PnL attribution

## Phase 8: Documentation

### 8.1 Required Documentation

- [ ] Strategy instance documented in PM workspace manifest
- [ ] Client risk profile documented in risk config
- [ ] Venue accounts listed in client config
- [ ] Runbook: what to do if strategy fails / needs manual intervention
- [ ] Escalation contacts for the client

### 8.2 Manifest Registration

```yaml
# unified-trading-pm/workspace-manifest.json (excerpt)
{
  "active_strategies":
    [
      {
        "strategy_id": "DEFI_ETH_BASIS",
        "client_id": "odum",
        "shard_id": "defi-eth-basis-shard-1",
        "config_path": "gs://config/DEFI_ETH_BASIS/clients/odum.yaml",
        "status": "live",
        "onboarded_date": "2026-03-22",
        "owner": "ikenna",
      },
    ],
}
```

## Quick Reference: New Client (Existing Strategy)

If the strategy is already running for another client, the process is shorter:

1. **Credentials:** Create venue accounts + store in Secret Manager (Phase 1)
2. **Config:** Clone existing client config, adjust sizing/risk/fees (Phase 2)
3. **Risk:** Set client-specific risk limits and alert routing (Phase 3)
4. **Shard:** Assign to existing shard or create new one (Phase 5)
5. **Deploy:** Add config to strategy-service, verify processing (Phase 7)

No need to repeat: instrument registration, feature pipeline wiring, ML model setup, or batch job creation — these are
strategy-level, not client-level.

## Quick Reference: New Strategy (Existing Client)

If the client already has other strategies running:

1. **Config:** Create strategy config from default template (Phase 2)
2. **Pipeline:** Wire feature services for new instruments if needed (Phase 4)
3. **ML:** Train and promote model if strategy uses ML (Phase 4.4)
4. **Batch:** Set up batch jobs for new strategy (Phase 6)
5. **Deploy:** Deploy with staged rollout (Phase 7)

No need to repeat: venue account creation, credential storage, risk limit framework, alert routing — these are
client-level, not strategy-level.

## SSOT References

| Concept                | SSOT                   | Location                                                    |
| ---------------------- | ---------------------- | ----------------------------------------------------------- |
| Strategy config schema | TypedDicts             | `strategy-service/strategy_service/config.py`               |
| Credential convention  | Codex architecture doc | `/codex/04-architecture/interface-credential-convention.md` |
| Instrument registry    | instruments-service    | `instruments-service/`                                      |
| Sharding config        | PM configs             | `unified-trading-pm/configs/`                               |
| Risk limits            | GCS risk config        | `gs://config/risk/{client_id}/`                             |
| Alert routing          | alerting-service       | `alerting-service/alerting_service/rules/`                  |
| Contract deployment    | deployment-service     | `deployment-service/scripts/`                               |
| Workspace manifest     | PM manifest            | `unified-trading-pm/workspace-manifest.json`                |
| Client onboarding      | Strategy operational   | `/codex/09-strategy/operational/client-onboarding.md`       |
