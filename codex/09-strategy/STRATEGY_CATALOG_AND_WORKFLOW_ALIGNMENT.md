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

### 3.1 Aligned (named in Codex index ↔ implemented & exported)

| Codex area | Codex doc / file hint               | Implementation (exported)                                                       |
| ---------- | ----------------------------------- | ------------------------------------------------------------------------------- |
| DeFi       | `defi_basis.py`                     | `BasisTradeStrategy`, `create_basis_trade_strategy`                             |
| DeFi       | `defi_staked_basis.py`              | `StakedBasisStrategy`, `create_staked_basis_strategy`                           |
| DeFi       | `defi_lending.py`                   | `AAVELendingStrategy`, `create_aave_lending_strategy`                           |
| DeFi       | `defi_recursive_basis.py`           | `RecursiveStakedBasisStrategy`, `create_recursive_staked_basis_strategy`        |
| CeFi       | `cefi_momentum.py`                  | `CeFiMomentumStrategy`, `create_*_momentum_strategy`                            |
| CeFi       | `mean_reversion_strategy.py`        | `MeanReversionStrategy`, `create_*_mean_reversion`                              |
| TradFi     | `tradfi_ml_directional_strategy.py` | `TradFiMLDirectionalStrategy`, `validate_tradfi_ml_config` (under `tradfi_ml/`) |
| TradFi     | `options_ml_strategy.py`            | `OptionsMLStrategy`, `create_*_ml_strategy` variants                            |
| Sports     | `arbitrage_strategy.py`             | `ArbitrageStrategy`, `create_arbitrage_strategy`                                |
| Sports     | `value_betting_strategy.py`         | `ValueBettingStrategy`, `create_value_betting_strategy`                         |
| Sports     | `ml_sports_strategy.py`             | `MLSportsStrategy`, `create_ml_sports_strategy`                                 |
| Sports     | `market_making.py`                  | `SportsMarketMakingStrategy`, `create_market_making_strategy`                   |
| Cross      | `prediction-markets.md` / mapping   | `PredictionArbStrategy`, `normalize_*_market`, `CanonicalPredictionMarket`      |

**Additional sports implementations in code (exported) with no dedicated `09-strategy/{name}.md` file:**

- `HalftimeMLStrategy` (`sports/halftime_ml.py`)
- `KellyCriterionStrategy` (`sports/kelly.py`)

**TradFi in code but not in Codex README table:**

- `TradFiMomentumStrategy`, `create_spy_momentum_strategy` (`tradfi_momentum.py`) — Codex CeFi/TradFi split mentions
  ML + options; this is an extra TradFi momentum path in code.

### 3.2 Implemented on disk but **not** in `__init__.py` exports (easy to miss in “workflow”)

These modules exist under `engine/strategies/` but are **not** part of the public package surface today:

| Path (under `strategies/`)                  | Note                 |
| ------------------------------------------- | -------------------- |
| `cross_exchange/cross_exchange_strategy.py` | Cross-exchange logic |
| `rel_vol/rel_vol_strategy.py`               | Relative vol         |
| `stat_arb/stat_arb_strategy.py`             | Stat arb             |
| `volatility/vol_surface_strategy.py`        | Vol surface          |

**Misalignment:** Codex describes a **closed catalog** in the README; the repo contains **additional** strategy modules
that are neither indexed in `09-strategy/README.md` nor exported. Onboarding and observability playbooks in Codex assume
the README index is complete.

### 3.3 Documented in Codex as “TBD” / MM-only (no `Code complete` row)

| Codex entry                         | README status | Implementation note                                                          |
| ----------------------------------- | ------------- | ---------------------------------------------------------------------------- |
| DeFi AMM LP (`market-making-lp.md`) | Documented    | No dedicated exported class matching that doc in `__init__.py`               |
| CeFi `market-making.md`             | Documented    | No `CeFiMarketMaking` in exports (sports has `SportsMarketMakingStrategy`)   |
| TradFi `market-making-options.md`   | Documented    | No separate exported “options MM” class in `__init__.py` (options ML exists) |

### 3.4 README sports index

- **Sports:** The README table lists **five** non-MM strategies (arb, value, ML, halftime ML, Kelly) plus market making,
  matching **`__all__`** exports. Halftime ML and Kelly do not yet have dedicated `09-strategy/sports/*.md` pages (table
  links omitted until docs exist).

### 3.5 Duplicate / legacy file

- `tradfi_ml_directional.py` at `strategies/` root vs `tradfi_ml/tradfi_ml_directional_strategy.py` — imports use the
  package path; root file risks drift if both are maintained.

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

1. **Catalog drift:** Update `09-strategy/README.md` to include **TradFi momentum**, **Halftime ML**, **Kelly**,
   **Prediction arb**, and either document or delete **cross_exchange / rel_vol / stat_arb / vol_surface** (or move to
   “experimental” with explicit non-export status).
2. **Export policy:** Decide whether non-exported strategy packages are **deprecated**, **internal**, or **upcoming**;
   align Codex and `__init__.py`.
3. **Trigger subscriptions:** Implement UIC model + config + engine filtering per `config-architecture.md` §3 (Codex
   already specifies the gap).
4. **Risk profile wiring:** Wire `StrategyRiskProfile` (UIC) to strategy config and validation; remove “implicit in
   code” as the long-term state.
5. **STRATEGY_MODES vs 09-strategy:** Schedule a **terminology pass** so `docs/STRATEGY_MODES.md` and
   `09-strategy/README.md` use one naming scheme for modes, delta tracking, and share classes.
6. **Per-strategy doc completeness:** Run the template checklist against each `09-strategy/*/*.md` file and mark gaps
   (many still have TBD capital targets and testing-stage placeholders).
7. **Sports docs:** Add `09-strategy/sports/` markdown for Halftime ML and Kelly (or link from a single “advanced
   sports” page) to match the README table.

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
