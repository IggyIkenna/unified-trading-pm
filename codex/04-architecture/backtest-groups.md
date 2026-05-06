---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Backtest Groups (A / B / C)

> **What it is:** Three distinct backtest concerns, each with its own owner, its own fixed/dynamic split, and its own
> output. The benchmark-fills contract bridges them — Group B uses benchmark fills (zero exec alpha, strategy alpha
> isolated); Group C uses a matching engine and measures execution alpha against the same benchmark.

## The three groups

| Group                  | Owner               | Purpose                                                             | Uses                                          |
| ---------------------- | ------------------- | ------------------------------------------------------------------- | --------------------------------------------- |
| **A. ML Training**     | ml-training-service | Produce versioned model artifacts                                   | Historical labels + features                  |
| **B. Strategy**        | strategy-service    | Decide if a strategy archetype + config is profitable BEFORE deploy | Benchmark fills (zero exec alpha)             |
| **C. Execution Alpha** | execution-service   | Tune execution policy / algo choice GIVEN strategy intent           | Matching engine with realistic microstructure |

## Why split

Without this split:

- "Backtest" conflates model quality + strategy alpha + execution alpha
- A loss in backtest can't be attributed — maybe the model is bad, maybe the threshold is bad, maybe simulated fills are
  unrealistic, maybe all three
- Optimizing one confounder reshapes the others

With the split:

- **Group A** isolates model quality: held-out AUC, LogLoss, calibration — no trading decision involved
- **Group B** isolates strategy alpha: given a model + features, does the archetype + config + staking method produce
  positive P&L assuming best-case execution?
- **Group C** isolates execution alpha: given a fixed strategy instruction stream, which execution policy + algo
  minimizes slippage vs benchmark?

## Group A — ML Training

### Owner

`ml-training-service`

### Fixed per experiment family

- Training data period (e.g., 2019-01-01 to 2024-12-31)
- Target variable (e.g., `future_return_24h_bps`, `win_home_team`)
- Feature set (reference to feature group versions)
- Model family (CatBoost, XGBoost, LightGBM, linear, etc.)
- Evaluation metrics (LogLoss for classifiers, RMSE for regressors, calibration curves, ROC-AUC)

### Dynamic (searched)

- Hyperparameters (depth, learning rate, regularization, ...)
- Train/val/test split ratios
- Calibration function (isotonic, sigmoid)
- Class weighting
- Feature subset (ablation)

### Output

Versioned model artifact in registry: `CRYPTO_BTC_CATBOOST_V4@v3` with metadata:

- Training period
- Feature group versions consumed
- Hyperparameters
- Held-out metrics
- Calibration curve

### Infra

Dedicated VMs for training runs. See memory feedback `run_backtests_on_vms.md`.

## Group B — Strategy

### Owner

`strategy-service`

### Fixed per experiment family

- Archetype (e.g., `ML_DIRECTIONAL_CONTINUOUS`)
- Eligible venues
- Feature group versions
- Model versions
- Settlement model (continuous vs event-settled)
- Share class
- Signal → target logic (the archetype code path)

### Dynamic (searched)

- Thresholds (min_edge_bps, min_confidence_threshold)
- Kelly fraction
- Lookback / smoothing windows
- Staking method + params
- Risk limits (max_position_pct, max_daily_loss)
- Rebalance cadence
- Venue-allocation weights (if SOR mode)

### Uses benchmark fills

Group B runs **batch mode with benchmark fills** — strategy alpha in isolation. No matching-engine microstructure; zero
execution alpha. P&L = benchmark_pnl.

This forces the archetype/config to stand or fall on its _decision quality_, not on optimistic fill assumptions.

### Output

- Per-config Sharpe / Sortino / Calmar / max DD
- Per-config P&L curve
- Per-config trade stats
- **Deployable config candidate** with content hash + version

Promoted configs become new config versions for the strategy instance. Picked up on next tick.

### Cross-validation

Walk-forward, purged k-fold (for overlapping bars), or simple train/validate/test. Archetype's backtest runner declares
the CV strategy.

## Group C — Execution Alpha

### Owner

`execution-service`

### Fixed per experiment family

- Strategy instruction stream (from historical live runs OR Group B simulated stream)
- Venue microstructure data (tick-level book, trades, mid snapshots)
- Cost model
- Benchmark mode (same as Group B's benchmark)

### Dynamic (searched)

- Algo choice (TWAP vs VWAP vs POV vs Iceberg vs SMART_ROUTED)
- Algo params (slice count, window, participation, aggression)
- MEV protection mode (DeFi)
- Venue routing preferences (SOR algorithm + tie-breakers)
- Order-type selection (limit vs market; maker vs taker)

### Matching engine

Replays historical book; simulates fills with:

- Queue-position model for passive orders
- Market-impact model for aggressive orders
- Latency model (venue-specific)
- Rejection model (margin / rate-limit probabilities)
- Slippage curve per size

### Output

- `execution_alpha_bps` per instruction
- Cumulative exec alpha per policy version
- Comparison across algo choices
- **Deployable execution policy candidate**

Promoted policies become new policy versions. Consumer opt-in per strategy config.

## How the three interact

```
A. ML Training
   ↓
   model_v3
   ↓
B. Strategy backtest (with benchmark fills)
   ↓
   config_hash_v5 (using model_v3, thresholds tuned)
   ↓
C. Execution backtest (with matching engine)
   ↓
   exec_policy_v3 (for config_v5's instruction stream)
   ↓
DEPLOY: archetype + config_v5 + exec_policy_v3
```

Changes propagate with opt-in:

- New model v4 → re-run Group B with v4 → new config_v6 → re-run Group C → new exec_policy_v4

## Benchmark fills bridge

The same `benchmark_fill` function is used by:

- Group B: replaces real fills entirely
- Group C: the baseline against which matching-engine fills are compared
- Live: computed alongside real fills for continuous exec-alpha measurement

Determinism guarantees that Group B P&L + Group C exec_alpha ≈ Live P&L (within microstructure noise).

## Anti-patterns to avoid

**Don't bake execution-quality assumptions into Group B**

- E.g., `fill_price = quote_mid - 5_bps` "because realistic"
- This is smuggling Group C into Group B
- Use pure benchmark; let Group C handle fill realism

**Don't use Group B's P&L to compare execution policies**

- Group B is indifferent to execution; won't distinguish policies
- Use Group C for execution comparisons

**Don't skip cross-validation in Group A**

- Single train/test split invites overfitting disguised as alpha
- Use walk-forward purged CV for time-series data

**Don't optimize Group B params on live data without holdout**

- Creates survivorship bias in config selection

## Category coverage

All five categories use all three groups:

| Category    | Group A examples            | Group B examples                  | Group C examples           |
| ----------- | --------------------------- | --------------------------------- | -------------------------- |
| CeFi crypto | BTC direction model         | ML directional threshold tuning   | TWAP vs POV on Binance     |
| DeFi        | Yield predictor             | Yield rotation lending thresholds | MEV protection mode        |
| Sports      | 1X2 outcome model           | Halftime ML staking               | Simultaneous-leg timing    |
| TradFi      | Equity cross-section ranker | Stat arb thresholds               | IS vs VWAP on IBKR         |
| Prediction  | Polymarket price predictor  | Threshold-crossed bet size        | CLOB aggressive vs passive |

## Unity meta-broker specifics

For Unity-routed strategies, Group C has an additional dimension: **child book selection** — given Unity's internal SOR,
which child book preferences optimize fills? Group C with Unity requires Unity's historical fill-by-book data to
simulate.

## Infrastructure

- **Group A**: large-memory VMs, GPU optional, training clusters
- **Group B**: stateless workers, parallel config-grid execution
- **Group C**: large-disk VMs (full orderbook replay), sequential (single playback)

See memory feedback `run_backtests_on_vms.md`: always use colocated VMs, never local.

## Cross-references

- Benchmark fills contract:
  [../09-strategy/architecture-v2/cross-cutting/benchmark-fills.md](../09-strategy/architecture-v2/cross-cutting/benchmark-fills.md)
- Execution policy: [execution-policy.md](execution-policy.md)
- Artifact versioning: [artifact-versioning.md](artifact-versioning.md)
- Strategy-execution protocol: [strategy-execution-protocol.md](strategy-execution-protocol.md)

## Not in this doc

- **ML training code** — ml-training-service
- **Strategy engine code** — strategy-service
- **Matching engine implementation** — execution-service/matching_engine/
- **CI/CD for backtest runs** — deployment-service
- **Per-category data availability** — data-availability manifest (SSOT in codex/02-data/)
