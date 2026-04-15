# Strategy catalog — Codex expectations vs `strategy-service` workflow

**Purpose:** Single reference for (1) what `09-strategy/` says every strategy and the strategy _system_ must express,
and (2) where the live `strategy-service` workflow matches, partially matches, or diverges.

**Primary SSOT (documentation):**

- `09-strategy/README.md` — index, hard rules, principles
- `09-strategy/templates/strategy-description-template.md` — per-strategy document checklist
- `09-strategy/cross-cutting/*.md` — shared concerns
- `09-strategy/{defi,cefi,tradfi,sports}/*.md` — asset-class strategy specs

**Primary SSOT (implementation):**

- `strategy-service/strategy_service/engine/strategies/` — strategy classes
- `strategy-service/strategy_service/engine/` — orchestration, mock path, components
- `strategy-service/strategy_service/config.py` — `component_config`, monitors
- `strategy-service/docs/CONFIG_SCHEMA.md`, `STRATEGY_MODES.md`

---

## 1. Per-strategy document: required nuance (template)

Every strategy markdown under `09-strategy/` is expected to follow
[`templates/strategy-description-template.md`](templates/strategy-description-template.md). The following is the
**contract** for what “complete” means in Codex.

| Section                       | What must be captured                                                                                          |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Header metadata               | Asset class, strategy type, **strategy ID pattern** `{CATEGORY}_{ASSET}_{TYPE}_{INDICATOR}_{MODE}_{TIMEFRAME}` |
| Overview                      | 2–3 sentences: economic intent and role in the book                                                            |
| Token / position flow         | Stepwise wallet/instrument flow from deploy through steady state                                               |
| Instruments                   | Table: instrument key, venue, type, role (canonical key format)                                                |
| Key features consumed         | Feature names, **source features-\* service**, SLA, use (signal vs risk)                                       |
| PnL attribution               | Components, settlement type, mechanism; **balance SOT** and **≤2%** reconciliation rule                        |
| Risk profile                  | Return, Sharpe, drawdown, leverage, scalability targets                                                        |
| Latency profile               | Per-segment p50/p99 and end-to-end; co-location decision                                                       |
| Execution details             | Venues, order types, atomicity, rebalance triggers, gas (DeFi)                                                 |
| Risk & exposure subscriptions | Exposure monitor patterns; **risk type** table with thresholds; custom risk types if any                       |
| Margin & liquidation          | Model (cross/isolated/HF/Reg-T), thresholds, monitoring                                                        |
| Authentication & credentials  | Pointers only: `credentials-registry.yaml`, `CredentialsRegistry`, UAC capability declarations                 |
| Client onboarding             | Accounts, secrets pattern, config location, isolation, restart vs hot-reload                                   |
| UI visualisation              | Standard streams + strategy-specific charts                                                                    |
| Testing stage status          | Rows for MOCK → HISTORICAL → LIVE_MOCK → LIVE_TESTNET → BATCH_REAL → STAGING → LIVE_REAL                       |
| References                    | Link to `strategy_service/engine/strategies/{file}.py`, CONFIG_SCHEMA, STRATEGY_MODES, UAC/UIC                 |

**Template-documented gaps (not optional prose — explicit backlog in template):**

- `StrategyRiskProfile` (UIC) **not yet wired** to strategy-service config; risk subscriptions **implicit in code**
  today.
- **Custom strategy risk types** planned (`p5-risk-custom-risk-types`); no machine-readable registry yet.
- **`trigger_subscriptions`** YAML/schema **not formalised**; `EventDrivenStrategyEngine` should filter before
  `generate_signal()` but **does not yet** (see `config-architecture.md` §3).

---

## 2. System-wide (“all strategies”) expectations from Codex

From `09-strategy/README.md` and `cross-cutting/config-architecture.md`.

| #   | Rule / principle                      | Codex expectation                                                                                             |
| --- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 1   | No raw market data in strategy        | No direct use of market-tick-data-service or market-data-processing-service; only features / ML / monitors    |
| 2   | Event-driven only                     | No timer-first strategies; schedules appear as upstream feature publication events                            |
| 3   | Strategy receives, does not calculate | Exposures, risk, PnL computed elsewhere; strategy emits decisions → `StrategyInstruction`                     |
| 4   | Execution boundary                    | execution-service does SOR, venue, monitoring; strategy sets constraints (e.g. `allowed_venues`, slippage)    |
| 5   | Unit of execution                     | `(strategy_id, client_id, config)`; multi-tenant async in one process; no cross-strategy shared mutable state |
| 6   | Live = batch                          | Same engine, PnL, attribution; different data provider / time window                                          |
| 7   | PnL source of truth                   | Balance-based equity; attribution sums within tolerance                                                       |
| 8   | Index-based yield                     | No APY approximation in PnL math                                                                              |
| 9   | Hot-reload                            | Param reload via UCI/GCS where possible; new strategy _types_ may need restart                                |

**Cross-cutting docs (apply to every strategy doc + runtime):**

| Document                      | Focus                                                                     |
| ----------------------------- | ------------------------------------------------------------------------- |
| `pnl-attribution.md`          | Buckets, reconciliation, settlements                                      |
| `cost-modeling.md`            | Fees, gas, slippage, opportunity cost                                     |
| `ml-pipeline.md`              | Features → model → signal → retrain                                       |
| `latency-profiles.md`         | Segment SLAs                                                              |
| `onboarding-checklist.md`     | New strategy instance / new client                                        |
| `client-onboarding.md`        | Client on existing strategy                                               |
| `config-architecture.md`      | Data boundaries, event model, **trigger subscription gap**                |
| `operational-modes-matrix.md` | `TestingStage`, `OperationalMode`, env axes, IBKR paper vs `TESTNET_MODE` |
| `margin-health.md`            | LTV, HF, liquidation by asset class                                       |
| `prediction-markets.md`       | PM as features + execution + arb                                          |

---

## 3. Codex `README` strategy index vs `strategy_service` exports

`09-strategy/README.md` lists a **curated** set with example Python filenames. The **public** strategy surface is
`strategy_service.engine.strategies.__all__` in
[`strategy_service/engine/strategies/__init__.py`](../../strategy-service/strategy_service/engine/strategies/__init__.py).

### 3.1 Aligned (named in Codex README ↔ implemented & exported in `__all__`)

**36 strategy classes** are exported via `__all__` in `strategy_service/engine/strategies/__init__.py`. The README
indexes **37 entries** (including variants like Unhedged Recursive, ETH Lending, and Omnichain Transfers).

All strategy classes listed in the README are now present in `__all__`. This includes the previously-missing quant
strategies (StatArb, RelVol, CrossExchange, VolSurface) and the newly-added strategies (TradFiMLSwing, TradFiMomentum,
CeFiMLDirectional, CeFiMarketMaking, BTC/SOL/multi-chain DeFi, OptionsMMStrategy).

| Domain     | Classes exported | README entries | Notes                                                         |
| ---------- | ---------------- | -------------- | ------------------------------------------------------------- |
| DeFi EVM   | 8                | 8 + 1 MM       | AmmLPStrategy covers MM; Unhedged Recursive = config variant  |
| DeFi SOL   | 4                | 4              | SolBasis, SolStakedBasis, Kamino, SolConcentratedLP           |
| DeFi BTC   | 2                | 2              | BtcBasis, BtcLending                                          |
| DeFi Multi | 4                | 5              | Omnichain Transfers = meta (no strategy class); rest exported |
| CeFi       | 5                | 4 + 1 MM       | Momentum, MeanReversion, CrossExchange, StatArb, MM           |
| TradFi     | 6                | 5 + 1 MM       | MLDirectional, MLSwing, Momentum, RelVol, VolSurface, OptsMM  |
| Sports     | 6                | 5 + 1 MM       | Arb, Value, ML, HalftimeML, Kelly, MM                         |
| Prediction | 1                | 1              | PredictionArbStrategy                                         |
| **Total**  | **36**           | **37**         | One-off diff = Omnichain Transfers (no class)                 |

### 3.2 system-topology.json coverage (32 entries vs 36 exported classes)

`system-topology.json` contains **32 strategy entries** (specific strategy_id instances, e.g. `CEFI_MOMENTUM_BTC_5M`).
It maps to **20 unique strategy classes**. The following 16 exported classes have **no** topology entry:

| Class                         | Domain     | Reason for gap                                                              |
| ----------------------------- | ---------- | --------------------------------------------------------------------------- |
| `AmmLPStrategy`               | DeFi EVM   | Documented — not yet added to topology                                      |
| `BtcBasisTradeStrategy`       | DeFi BTC   | Documented — not yet added to topology                                      |
| `BtcLendingStrategy`          | DeFi BTC   | Documented — not yet added to topology                                      |
| `CeFiMLDirectionalStrategy`   | CeFi       | Exported — not yet added to topology                                        |
| `CeFiMarketMakingStrategy`    | CeFi       | Exported — not yet added to topology                                        |
| `CrossChainSORStrategy`       | DeFi Multi | Documented — not yet added to topology                                      |
| `CrossChainYieldArbStrategy`  | DeFi Multi | Documented — not yet added to topology                                      |
| `EthenaBenchmarkStrategy`     | DeFi EVM   | Documented — not yet added to topology                                      |
| `KaminoLendingStrategy`       | DeFi SOL   | Documented — not yet added to topology                                      |
| `L2BasisTradeStrategy`        | DeFi Multi | Documented — not yet added to topology                                      |
| `MultiChainLendingStrategy`   | DeFi Multi | Documented — not yet added to topology                                      |
| `OptionsMMStrategy`           | TradFi     | Documented — not yet added to topology                                      |
| `SolBasisTradeStrategy`       | DeFi SOL   | Documented — not yet added to topology                                      |
| `SolConcentratedLPStrategy`   | DeFi SOL   | Documented — not yet added to topology                                      |
| `SolStakedBasisStrategy`      | DeFi SOL   | Documented — not yet added to topology                                      |
| `TradFiMLDirectionalStrategy` | TradFi     | Exported (tradfi_ml/ package) — topology uses TradFiMLSwingStrategy instead |

**Factory export gap:** `create_prediction_arb_btc_strategy` is defined in `prediction_arb/prediction_arb_strategy.py`
and referenced in system-topology.json but is **not** in `__all__`. `PredictionArbStrategy` itself IS exported.

### 3.3 Market-making strategy classes: export status

| Codex entry                         | README status | Export status (current)                                                    |
| ----------------------------------- | ------------- | -------------------------------------------------------------------------- |
| DeFi AMM LP (`market-making-lp.md`) | Documented    | `AmmLPStrategy` exported in `__all__` with `create_amm_lp_strategy`        |
| CeFi `market-making.md`             | Documented    | `CeFiMarketMakingStrategy` exported with `create_*_market_making_strategy` |
| TradFi `market-making-options.md`   | Documented    | `OptionsMMStrategy` exported with `create_*_options_mm_strategy`           |

All three MM strategy classes are now exported. Previously flagged as missing; resolved.

### 3.4 README sports index

- **Sports:** The README table lists **five** non-MM strategies (arb, value, ML, halftime ML, Kelly) plus market making,
  matching **`__all__`** exports. Halftime ML and Kelly do not yet have dedicated `09-strategy/sports/*.md` pages (table
  links omitted until docs exist).

### 3.5 Duplicate / legacy file

- `tradfi_ml_directional.py` at `strategies/` root vs `tradfi_ml/tradfi_ml_directional_strategy.py` — both are imported
  in `__init__.py`. The root file exports `TradFiMLSwingStrategy`; the package exports `TradFiMLDirectionalStrategy`.
  These are distinct classes (swing vs directional), not duplicates.

### 3.6 Missing codex documentation files

The following strategies are in the README index (with links) but the target markdown files do **not** exist:

| README link target              | Strategy class           | Status                 |
| ------------------------------- | ------------------------ | ---------------------- |
| `cefi/cross-exchange.md`        | `CrossExchangeStrategy`  | File missing           |
| `cefi/stat-arb.md`              | `StatArbStrategy`        | File missing           |
| `tradfi/tradfi-momentum.md`     | `TradFiMomentumStrategy` | File missing           |
| `tradfi/relative-volatility.md` | `RelVolStrategy`         | File missing           |
| `tradfi/volatility-surface.md`  | `VolSurfaceStrategy`     | File missing           |
| `prediction/prediction-arb.md`  | `PredictionArbStrategy`  | File missing (dir too) |
| `sports/halftime-ml.md`         | `HalftimeMLStrategy`     | File missing           |
| `sports/kelly.md`               | `KellyCriterionStrategy` | File missing           |

8 strategy docs referenced in README do not exist on disk. All 8 strategies are implemented and exported.

---

## 4. Workflow alignment: architecture vs `strategy-service` behaviour

| Topic                                  | Codex says                                                                     | Observed / likely in `strategy-service`                                                                                                                                         |
| -------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Event-driven engine                    | `EventDrivenStrategyEngine` filters by `trigger_subscriptions`                 | Codex **TODO**: formal schema missing; engine passes **all** features through today (`config-architecture.md`)                                                                  |
| Risk subscriptions                     | `component_config.risk_monitor.enabled_risk_types` + UIC `StrategyRiskProfile` | **Partial:** `RiskMonitorConfig.enabled_risk_types` exists in `config.py`; UIC `StrategyRiskProfile` **not** wired per template                                                 |
| Exposure subscriptions                 | `exposure_monitor.instrument_subscriptions`                                    | **Partial:** `ExposureMonitorConfig` exists in `config.py`; per-strategy docs may exceed what configs enforce in runtime                                                        |
| Multi-instance `(strategy,client,cfg)` | Required                                                                       | Supported in design/docs; **verify** live orchestration matches (pub/sub fan-out, isolation) in deployment configs                                                              |
| No raw MD                              | Hard rule                                                                      | **Audit:** grep strategies for `market_tick` / `market_data_processing` imports (should be empty in production paths)                                                           |
| `STRATEGY_MODES.md`                    | Referenced as canonical                                                        | Large, **basis-strategy-v1** flavoured (share class, delta tracking); may **overlap** or **diverge** from generic `09-strategy` wording — treat as **second SSOT** to reconcile |
| Testing stages                         | Template table MOCK → LIVE_REAL                                                | Machine-readable: `unified_api_contracts.internal.modes.TestingStage`; **per-strategy YAML** in Codex often placeholders — not automatically enforced in CI per strategy        |
| IBKR paper vs `TESTNET_MODE`           | Target: align global mode with TradFi paper                                    | **Documented as incremental** in `operational-modes-matrix.md`; secret `trading_mode` still common                                                                              |

---

## 5. Misalignment summary (actionable)

Use this as a backlog bridge between documentation and engineering.

**Resolved (as of 2026-04-01):**

- ~~Catalog drift: cross_exchange / rel_vol / stat_arb / vol_surface not in README~~ — All four now in README and
  exported.
- ~~Export policy: non-exported strategy packages~~ — All strategy classes are now exported in `__all__`. No
  non-exported strategies remain.
- ~~Market-making classes missing from exports~~ — AmmLPStrategy, CeFiMarketMakingStrategy, OptionsMMStrategy all
  exported.

**Still open:**

1. **8 missing codex docs:** `cefi/cross-exchange.md`, `cefi/stat-arb.md`, `tradfi/tradfi-momentum.md`,
   `tradfi/relative-volatility.md`, `tradfi/volatility-surface.md`, `prediction/prediction-arb.md` (+ prediction/
   directory), `sports/halftime-ml.md`, `sports/kelly.md`. All 8 strategies are implemented and exported but lack
   dedicated codex documentation files.
2. **system-topology.json coverage:** 16 exported strategy classes have no entry in system-topology.json (see 3.2).
   These need topology entries with maturity tracking, config files, and instrument mappings.
3. **Factory export gap:** `create_prediction_arb_btc_strategy` is in system-topology.json but not in `__all__`.
4. **Trigger subscriptions:** Implement UIC model + config + engine filtering per `config-architecture.md` 3 (Codex
   already specifies the gap).
5. **Risk profile wiring:** Wire `StrategyRiskProfile` (UIC) to strategy config and validation; remove “implicit in
   code” as the long-term state.
6. **STRATEGY_MODES vs 09-strategy:** Schedule a **terminology pass** so `docs/STRATEGY_MODES.md` and
   `09-strategy/README.md` use one naming scheme for modes, delta tracking, and share classes.
7. **Per-strategy doc completeness:** Run the template checklist against each `09-strategy/*/*.md` file and mark gaps
   (many still have TBD capital targets and testing-stage placeholders).
8. **API mock data alignment:** `unified-trading-api/mock_data/seed_strategies.py` uses different strategy IDs (e.g.
   `DEFI_ETH_BASIS_SCE_1H`, `CEFI_BTC_ML_DIR_HUF_4H`) than system-topology.json (e.g. `DEFI_BASIS_ETH_1H`,
   `CEFI_MOMENTUM_BTC_5M`). The mock seed data should be regenerated from system-topology.json for consistency.

---

## 6. Related links

- [Strategy README](README.md)
- [Strategy description template](templates/strategy-description-template.md)
- [Config architecture](cross-cutting/config-architecture.md)
- [Operational modes matrix](cross-cutting/operational-modes-matrix.md)
- [Tier 0 UI demo and parity](TIER_ZERO_UI_DEMO_AND_PARITY.md) — Codex ↔ UI mock ↔ future API tiers
- Strategy implementation directory: `strategy-service/strategy_service/engine/strategies/`
- **UI alignment (generators vs hand docs):** `unified-trading-pm/docs/ui-alignment-ssot.md` — machine
  `ui-reference-data.json` vs narrative docs such as
  `unified-trading-system-ui/docs/MOCK_STATIC_BROWSER_AGENT_HANDBOOK.md`
- **Repeatable Tier 0 audit:** `unified-trading-system-ui/docs/END_TO_END_STATIC_TIER_ZERO_TESTING.md`
