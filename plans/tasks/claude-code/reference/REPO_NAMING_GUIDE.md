# Repo Naming Guide for Claude Code

**CRITICAL: Repo folders use DASHES, Python packages use UNDERSCORES**

---

## 🎯 The Pattern

### Repo Folder (with DASHES)

```
/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/
├── unified-config-interface/     ← DASHES (repo folder)
├── unified-events-interface/     ← DASHES
├── unified-trading-library/       ← DASHES
└── instruments-service/          ← DASHES
```

### Python Package (with UNDERSCORES)

```
unified-config-interface/
└── unified_config_interface/     ← UNDERSCORES (Python package)
    ├── __init__.py
    ├── base_config.py
    └── ...
```

---

## ⚠️ Common Mistake

**Wrong** (trying to cd into package):

```bash
cd unified_config_interface  # ❌ This is the Python package, not repo!
```

**Correct** (cd into repo):

```bash
cd unified-config-interface  # ✅ This is the repo folder
```

---

## 📋 All 24 Repos

### Services (14)

- `instruments-service/` → package: `instruments_service/`
- `market-tick-data-handler/` → package: `market_tick_data_handler/`
- `market-data-processing-service/` → package: `market_data_processing_service/`
- `pnl-attribution-service/` → package: `pnl_attribution_service/`
- `features-calendar-service/` → package: `features_calendar_service/`
- `features-delta-one-service/` → package: `features_delta_one_service/`
- `features-volatility-service/` → package: `features_volatility_service/`
- `features-onchain-service/` → package: `features_onchain_service/`
- `ml-training-service/` → package: `ml_training_service/`
- `ml-inference-service/` → package: `ml_inference_service/`
- `strategy-service/` → package: `strategy_service/`
- `execution-service/` → package: `execution_service/`
- `risk-and-exposure-service/` → package: `risk_and_exposure_service/`
- `position-balance-monitor-service/` → package: `position_balance_monitor_service/`

### Libraries (6)

- `unified-trading-library/` → package: `unified_trading_library/`
- `unified-config-interface/` → package: `unified_config_interface/`
- `unified-events-interface/` → package: `unified_events_interface/`
- `unified-market-interface/` → package: `unified_market_interface/`
- `unified-trade-execution-interface/` → package: `unified_trade_execution_interface/`
- `unified-domain-client/` → package: `unified_domain_client/`

### Utility (4)

- `execution-algo-library/` → package: `execution_algo_library/`
- `alerting-service/` → package: `alerting_service/`
- `deployment-service/` → package: `deployment_service/`
- `deployment-api/` → package: `deployment_api/`

---

## 🔧 For Agent CLI Commands

**Always use repo folder (dashes)** in `--workspace`:

```bash
# ✅ CORRECT
agent --workspace /path/to/unified-config-interface "fix errors"

# ❌ WRONG
agent --workspace /path/to/unified_config_interface "fix errors"
```

---

## 🔧 For basedpyright Commands

**Can run from repo root** (checks Python package automatically):

```bash
# From repo folder
cd unified-config-interface
basedpyright --level warning  # Checks unified_config_interface/ package

# Or specify package explicitly
basedpyright --level warning unified_config_interface/
```

---

## 💡 Quick Reference for Claude Code

**When orchestrating, always**:

1. `cd` into repo folder (with dashes)
2. Run basedpyright (it finds package automatically)
3. Use repo folder path for `agent --workspace`

**Example**:

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-config-interface
basedpyright --level warning  # Checks unified_config_interface/ package
agent --workspace $(pwd) "fix"  # Uses repo folder path
```

---

## ✅ Summary

**Repo folders**: Use DASHES (unified-config-interface) **Python packages**: Use UNDERSCORES (unified_config_interface)
**For agent CLI**: Use repo folder path (dashes) **For basedpyright**: Run from repo folder (finds package
automatically)

**This is standard Python convention!**
