---
title: "CME S&P 500 ML directional signal — pre-audit + MVP backtest plan"
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-20
---

# CME S&P 500 ML directional signal — pre-audit + MVP backtest plan

Target archetype + slot: `ML_DIRECTIONAL_CONTINUOUS@cme-es-dated-1m-usd-prod` (TRADFI / dated_future / venue CME,
rollMode both, status PARTIAL per `unified-trading-system-ui/lib/architecture-v2/coverage.ts:181-192`).

Business driver: CME S&P go-live Sept 2026 is the Jun-Sept 2026 highest-leverage deliverable — unlocks India Options
onboarding and CME asymmetric co-invest (Path-to-$100M, 2026-04-20).

**Headline**: the user's mental model is **only partially correct**. The pipeline has the adapter, canonical-id,
backtest runner, and generic ML harness. It is missing (a) a continuous-series / roll service, (b) ES registration in
ml-training-service's instrument universe, (c) a TRADFI backfill or ML-training VM launcher, (d) confirmation that
multi-year CME ES tick/ohlcv_1m is actually in GCS. Items (a) and (b) are non-trivial (days of work each, not hours).
Item (d) cannot be verified from the local workspace — requires a GCS query against the real project.

## 1. What's already in place (per-repo audit)

### 1.1 instruments-service

- **ES instrument declaration**: YES — implicitly, via UAC's `TRADFI_DATABENTO_INSTRUMENTS` registry
  (`unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py:192` imports `_CME_INDEX_FUTURES`
  which includes ES). The instruments-service Databento adapter
  (`instruments_service/reference_data/adapters/tradfi/databento.py:27-36`) pulls that registry.
- **Canonical id scheme**: YES — `CME:FUTURE:ES-YYYYMMDD` (e.g. `CME:FUTURE:ES-20260620`) is tested in
  `unified-api-contracts/tests/internal/unit/test_canonical_id_builder.py:88-100`. Options are
  `CME:OPTION:ES-YYYYMMDD-STRIKE-[CP]`.
- **Continuous "ES-front" synthetic instrument**: **NO**. No `CME:FUTURE:ES-FRONT` or `CME:CONTINUOUS:ES` instrument
  declared. The Databento classifier
  (`market-tick-data-service/ market_tick_data_service/market_interface/adapters/tradfi/databento_classifier.py`) has a
  `_CONTINUOUS_FUTURE_ROOTS` set that explicitly **filters OUT** roots like `ES/NQ/CL/...`. The design-intent comment in
  `tradfi-venue-coverage-matrix.md` says "MTDS builds continuous series itself" — but that builder is not implemented.
  (Grep for `continuous_series|build_continuous|continuous_contract|front_month` returns only 2 hits: the docs matrix
  itself and a test that asserts the classifier filters continuous roots out.)
- **ICE**: out of scope for this deliverable.

### 1.2 market-tick-data-service

- **CME Databento adapter**: YES — `market_tick_data_service/market_interface/adapters/tradfi/ databento_adapter.py`
  with full canonical-write coverage per `docs/tradfi-venue-coverage-matrix.md` (G6 gate passed 2026-04-18). CME
  future + futures_chain + options_chain + combo + currency are all canonical-write wired with smoke tests.
- **Supported data types for CME future**: `trades`, `ohlcv_1m`, `quotes`, `tbbo`.
- **Historical data in GCS**: **UNKNOWN — cannot be verified from local workspace**. The canonical path is
  `gs://<tick-data-bucket>/raw_tick_data/by_date/day=YYYY-MM-DD/category=tradfi/ venue=CME/instrument_type=future/data_type=ohlcv_1m/ES-*.parquet`.
  Verification requires `gsutil ls` against `gs://<project-bucket>/_index/availability_index.parquet` — OUT OF SCOPE for
  this local audit. **HARD BLOCKER if not backfilled.**
- **Settlement / daily-open / roll reference**: Databento gives price tick data only. There is no dedicated settlement
  capture; Databento OHLCV_1D gives end-of-day close which can proxy.
- **Representative-future service** (for the roll): **DOES NOT EXIST**. Only reference is in
  `unified-trading-system-ui/lib/architecture-v2/block-list.ts` (BL-10 flag). No Python module named
  `representative_future_service` anywhere in the workspace. Codex flags this explicitly:
  `codex/09-strategy/architecture-v2/cross-cutting/futures-roll-and-combos.md`.

### 1.3 unified-api-contracts

- **CME venue capability declaration**: YES — CME is a known venue token; Databento is a known data-provider
  registration; `CME:FUTURE:ES-YYYYMMDD` canonicalisation is locked in.
- **ArchetypeCapability for ML_DIRECTIONAL_CONTINUOUS × TRADFI × dated_future**: **PARTIAL** — `coverage.ts` says
  PARTIAL because "roll service required (BL-10)". UAC gap #11 (`RepresentativeFutureRegistry`) is explicitly unfilled
  in `codex/.../uac-registry-gaps.md`.
- **What's missing**: `RepresentativeFutureRegistry` — the UAC declaration that says, for each dated-future underlying,
  the rule used to pick the front-month (e.g., `3rd Friday rollover`, `volume-crossover heuristic`,
  `open-interest dominance`), plus UTL events `REPRESENTATIVE_FUTURE_CHANGED` and `FUTURES_ROLL`.

### 1.4 unified-trading-library / features-markets-service / unified-features-interface

- **`features-markets-service`**: **does NOT exist** in the workspace. It is name-dropped in workspace documentation but
  the physical repo is not present. The real feature repos are: `features-multi-timeframe-service`,
  `features-delta-one-service`, `features-volatility-service`, `features-calendar-service`,
  `features-commodity-service`, `features-cross-instrument-service`, `features-sports-service`,
  `features-onchain-service`.
- **Directional-ML features relevant to ES 1-minute**:
  - `features-multi-timeframe-service/features_multi_timeframe_service/calculators/` has `tf_momentum_alignment.py`,
    `tf_vol_compression.py`, `tf_structure_context.py`, `tf_session_context.py`, `tf_risk_reward.py`,
    `tf_confluence_signals.py`, `intraday_regime.py`, `micro_regime.py`, `hierarchical_regime_combiner.py`,
    `wedge_confluence.py` — directly usable for an ML_DIRECTIONAL_CONTINUOUS signal.
  - `features-volatility-service` — realised vol, implied-vol structure features.
  - `features-calendar-service` — macro event flags (FOMC / CPI / NFP) which are critical for ES.
  - Term-structure features across the futures curve (front/back basis): **not confirmed**;
    `features-multi-timeframe-service` focuses on timeframes not cross-contract. A curve service could be
    features-commodity-service (not yet audited).
- **TRADFI test coverage in features-multi-timeframe-service**: LOW — grep shows 14 TRADFI mentions across only 9 files,
  mostly docs + smoke/mock scripts. The core calculators have been exercised against CEFI (BTC/ETH perps). Running them
  against ES 1-minute is untested.
- **UTL domain utils**: `unified-trading-library/unified_trading_library/feature_calculator/` exists (per key-repo map)
  — handles the common orchestration.

### 1.5 unified-trading-library/ml/

- **ML training harness**: YES — `unified_trading_library/ml/ml_training_utils.py` has `ProbabilityCalibrator`
  (Platt/isotonic/beta), `BayesianHyperparamOptimizer` (Optuna). `model_registry.py` + `target_registry.py` +
  `artifact_store.py` + `config_schema.py` compose a full training-registry pattern.
- **Reusable for ES**: YES — the harness is instrument-agnostic. BTC-ML directional was trained via this same harness;
  SPY is already registered in `ml-training-service` (see 1.6). ES is not yet registered but can be added.

### 1.6 ml-training-service

- **Service exists**: YES — `ml_training_service/cli/{parser,main,handlers}.py`, with handlers `train_handler.py`,
  `grid_search_handler.py`, `hyperparam_grid_handler.py`, `final_training_handler.py`, `evaluate_handler.py`,
  `preselection_handler.py`, `pipeline_handler.py`.
- **INSTRUMENTS registry** (`ml_training_service/cli/parser.py:14-18`):
  ```python
  INSTRUMENTS = {"CEFI": ["BTC", "ETH", "SOL"], "TRADFI": ["SPY"]}
  INSTRUMENT_ID_MAP = {..., "SPY": "NASDAQ:ETF:SPY-USD"}
  ```
  **ES is not registered.** To train a CME-ES model, this dict needs:
  - `INSTRUMENTS["TRADFI"]` to include `"ES"` (or `"ES_FRONT"` for continuous)
  - `INSTRUMENT_ID_MAP["ES"] = "CME:FUTURE:ES-<expiry>"` for a single dated contract, OR a new synthetic id
    `"CME:CONTINUOUS:ES"` once the roll service lands.
- **Target builders**: swing_high / swing_low / cross_venue_spread are defined. These are directly applicable to ES
  1-minute (a "breakout after swing high" is the standard mean-reversion-vs-breakout 3-class target).

### 1.7 strategy-service

- **`MLDirectionalContinuousEngine`**: YES — fully implemented at
  `strategy_service/engine/strategies/v2/ml_directional/continuous.py:50-138`. Consumes `MLPrediction.predicted_class`
  (1=breakout/LONG, 2=reversion/SHORT, 0=neither/FLAT) + `confidence`. Emits `TradeInstruction` sized by
  `target_equity × max_position_fraction / mid_price`.
- **Batch / backtest runner (Group B — strategy alpha)**: YES — `strategy_service/engine/ backtest_v2/runner.py`
  (`GroupBRunner`). Reuses `V2EngineOrchestrator` so backtest ≡ live (only the fill source differs:
  `BenchmarkFillEngine` replaces real venue). Emits `GroupBBacktestResult` with total_pnl, sharpe, sortino,
  max_drawdown, calmar, num_trades, win_rate.
- **CLI batch-handler**: YES — `strategy_service/cli/handlers/batch_handler.py:47-120` + `batch_utils.py` dispatches
  from a `StrategyDispatch` to archetype engines. Accepts `category` arg ("CEFI", "TRADFI", "DEFI"). `DependencyChecker`
  validates upstream availability.
- **Subscription to `REPRESENTATIVE_FUTURE_CHANGED`**: **NO**. The engine has no roll-event subscriber. Today the engine
  trades whichever `instrument` the caller passes. For `-dated-` slots the engine would need (i) a subscription to the
  roll event, (ii) emission of a `FUTURES_ROLL` combo instruction (`atomic` two-leg listed calendar-spread or synthetic)
  on trigger.
- **Existing CEFI spot + perp instances** (reference for TRADFI dated_future pattern): model slot labels live in
  `strategy_service/engine/strategies/v2/migration/ legacy_strategy_mapping.py` and `target_universe/catalog.py` —
  TRADFI_ML_DIRECTIONAL examples in the archetype doc include `cme-es-1h-usd-prod` but not yet realised as a registered
  slot.

### 1.8 deployment-service / VM tarballs

- **VM tarball infrastructure**: YES — `deployment-service/scripts/vm/create-code-tarballs.sh`
  - `setup-data-pipeline-vm.sh` + `vm-exec-with-gcs-tee.sh`.
- **`TRADFI_REPOS` array** (`create-code-tarballs.sh:52-55`): `CEFI_REPOS + features-volatility-service`. This **is**
  enough to launch backtests (core + strategy-service + execution-service + features + MTDS), but it doesn't include
  `ml-training-service` — training VMs need `--include ml-training-service`.
- **Existing launchers** (`deployment-service/scripts/vm/launch-*.sh`): `launch-cefi-sharded- backfill.sh`,
  `launch-mdps-backfill-vm.sh`, `launch-features-backfill-vm.sh`, `launch-strategy-test-vm.sh`,
  `launch-instruments-smoke-vm.sh`, `launch-canonical-smoke-vm.sh`, `launch-canonical-migration-vm.sh`,
  `launch-sfi-forward-poll.sh`, `launch-footystats-forward- poll.sh`, `launch-mtds-prediction-backfill-vm.sh`. **No
  `launch-tradfi-backfill-vm.sh` and no `launch-ml-training-vm.sh`.** These need to be built. Template:
  `launch-cefi-sharded-backfill.sh` is the cleanest to copy.

## 2. Blockers to ship a runnable backtest

In priority order:

| #   | Blocker                                                                                                                                                                                                                                                                                                                                         | Severity                                                                          | Fix scope                                                                                                          |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| B1  | **CME ES multi-year ohlcv_1m not confirmed to be in GCS.** No way to verify from local workspace. If not present, need Databento backfill across ES expiries 2022-2026 via a yet-to-be-written `launch-tradfi-backfill-vm.sh`.                                                                                                                  | **HARD BLOCKER — probably days of backfill if empty.**                            | MTDS + new launcher                                                                                                |
| B2  | **No continuous-series / representative-future builder.** Strategy can trade any single dated contract (e.g. `CME:FUTURE:ES-20260620`) but that contract only runs 3 months. An ML model trained on a single expiry has almost no training data. For multi-year training you need a rolled continuous series. BL-10 is the canonical reference. | **HARD BLOCKER for a multi-year backtest.** Soft for a single-quarter backtest.   | New module in MTDS OR a new `representative-future-service` repo + UAC `RepresentativeFutureRegistry` + UTL events |
| B3  | **ES not registered in ml-training-service.** `parser.py` hard-codes `TRADFI: ["SPY"]`.                                                                                                                                                                                                                                                         | **ERROR — CLI will reject `--instrument ES`.**                                    | 3-line change to `parser.py`                                                                                       |
| B4  | **No TRADFI backfill / ML-training VM launcher.** Cannot run heavy backtest compute on a VM.                                                                                                                                                                                                                                                    | Medium — can run locally for a smoke, but no serious multi-year run without this. | 2 new shell scripts                                                                                                |
| B5  | **`strategy-service` ML_DIRECTIONAL_CONTINUOUS engine has no `FUTURES_ROLL` emission**. Needed when the representative-future flips. Without it, a backtest running across more than one expiry will flatline when the contract expires.                                                                                                        | Medium — only matters once B2 is real.                                            | Strategy-service engine extension                                                                                  |
| B6  | **Term-structure + macro-calendar features not confirmed wired for TRADFI**. features-calendar-service has FOMC/CPI/NFP but wiring it to TRADFI-feature-group output for ES-1m consumption is untested.                                                                                                                                         | Low — model trains without these, just weaker.                                    | Smoke test                                                                                                         |

## 3. Minimum viable backtest — what "MVP" can realistically mean

Three tiers of "runnable":

**Tier 0 — single-expiry local smoke** (no blockers except B3 + B6 + partial B1):

- Pick a single 90-day ES contract (say `CME:FUTURE:ES-20260620`) that has full ohlcv_1m data.
- Register in `ml-training-service`: `TRADFI: ["SPY", "ES"]` with instrument_id_map entry.
- Run `ml-training-service` swing-high / swing-low training on the 3-month window.
- Run `strategy-service` batch-handler Group B backtest on the same window, single instrument.
- **Output**: a P&L curve + Sharpe for a single-expiry toy run. Useless for alpha claims but demonstrates the pipe
  end-to-end. **~2 engineer-days.**

**Tier 1 — multi-expiry stitched backtest** (solves B1 + B3 + B5 but hacks B2):

- Write a script that concatenates ohlcv_1m across rolled expiries using a volume-crossover heuristic (e.g. roll on the
  day front-month open-interest < next-month open-interest).
- Persist the stitched series as a new synthetic partition under
  `tradfi/venue=CME/instrument_type=future/data_type=ohlcv_1m/ES-FRONT.parquet`.
- Register `CME:CONTINUOUS:ES` in `INSTRUMENT_ID_MAP`. Train model on stitched series.
- Backtest `MLDirectionalContinuousEngine` against stitched series — pretend no roll happens (model emits a single
  LONG/SHORT/FLAT on the stitched price; the fact that the underlying contract rolls is invisible).
- **Output**: a Sharpe + P&L curve across multiple years. Valid for internal strategy-alpha attribution, **not** for
  execution-alpha attribution (no roll cost modelled). **~5-8 engineer-days.**

**Tier 2 — production path with real roll** (solves all blockers):

- B2 properly: build or wire `representative-future-service`; emit `REPRESENTATIVE_FUTURE_CHANGED` events; UAC
  `RepresentativeFutureRegistry`.
- B5 properly: engine subscribes to the event and emits `FUTURES_ROLL` combo instructions.
- Backtest honours rolls with explicit roll-cost accounting.
- **Output**: production-grade Sharpe + P&L with roll costs baked in. **~3-4 engineer-weeks.**

## 4. DAG (Tier 1 MVP path)

```
                              ┌────────────────────────┐
                              │ A0. Verify CME ES data │
                              │     in GCS (HUMAN)     │
                              └────────────────┬───────┘
                                               │ if empty → A1
                                               ▼
                        ┌────────────────────────────────────────────┐
                        │ A1. Write launch-tradfi-backfill-vm.sh     │
                        │     Write create-code-tarballs.sh add      │
                        │     ml-training-service to TRADFI_REPOS    │
                        │     Launch backfill via Databento          │
                        └────────────────────────┬───────────────────┘
                                                 ▼
                        ┌────────────────────────────────────────────┐
                        │ B. Stitch ES front series                  │
                        │    new MTDS script continuous_ES.py        │
                        │    → CME:CONTINUOUS:ES ohlcv_1m parquet    │
                        └────────────────────────┬───────────────────┘
                                                 ▼
              ┌──────────────────────────────────┴──────────────────────────────────┐
              ▼                                                                     ▼
  ┌─────────────────────────┐                               ┌─────────────────────────────┐
  │ C1. Register CME:       │     parallel                  │ C2. Ensure features-        │
  │ CONTINUOUS:ES in        │    ──────────>                │ multi-timeframe-service     │
  │ ml-training-service     │                               │ emits feature group for ES  │
  │ parser.py               │                               │ 1m with correct instrument  │
  └────────────┬────────────┘                               └───────────┬─────────────────┘
               ▼                                                        ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │ D. Train ES-1m swing-high + swing-low model via ml-training-service CLI on a     │
  │    VM or locally. Output: model + calibrator in artifact_store + model_registry  │
  └────────────────────────────────────┬─────────────────────────────────────────────┘
                                       ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │ E. Run strategy-service Group B backtest via batch_handler CLI:                  │
  │      strategy-service --operation backtest --mode batch --category tradfi        │
  │      --archetype ML_DIRECTIONAL_CONTINUOUS --slot cme-es-dated-1m-usd-prod       │
  │    Feed CME:CONTINUOUS:ES ohlcv_1m + inferenced MLPredictions per tick.          │
  │    Output: GroupBBacktestResult (Sharpe, P&L curve, win rate, max_dd).           │
  └──────────────────────────────────────────────────────────────────────────────────┘
```

## 5. Parallelisation

- A0 + A1 must come first (sequential). They gate everything.
- B is sequential after A.
- C1 and C2 are parallel after B (different repos; ml-training-service + features-multi-timeframe-service).
- D is after both C1 and C2.
- E is after D.

## 6. Honest time estimate (serious engineer, real data at hand)

| Task                                         | Wall-clock (engineer)                        | Wall-clock (including VM compute) |
| -------------------------------------------- | -------------------------------------------- | --------------------------------- |
| A0 (verify data)                             | 15 min                                       | 15 min                            |
| A1 (build backfill launcher + run if needed) | 0.5d-1d script, 4-48h backfill               | 2-50h                             |
| B (stitch continuous series)                 | 1.5-2d                                       | same (script is fast)             |
| C1 (register ES in ml-training-service)      | 0.5d                                         | 0.5d                              |
| C2 (TRADFI feature-group smoke)              | 1d                                           | 1d                                |
| D (train ES-1m model, 3-5 year window)       | 0.5d code, 6-24h train                       | 12-48h                            |
| E (backtest run)                             | 1d code glue, 1-4h backtest                  | 4-12h                             |
| **MVP total (Tier 1 stitched)**              | **~5-8 engineer-days + 2-5 days wall-clock** |                                   |
| **Production total (Tier 2 with real roll)** | **~3-4 engineer-weeks**                      |                                   |

## 7. Success criteria — Tier 1 MVP

- Code gates: `bash scripts/quality-gates.sh` green in each of the 4+ touched repos.
- Data gate: `gs://<bucket>/_index/availability_index.parquet` shows `capture_status=captured` for
  `venue=CME / instrument_type=future / underlying=ES / data_type=ohlcv_1m` across at least 3 years of history.
- Model gate: `model_registry` has one registered model `TRADFI_ES_CATBOOST_V1` with ECE < 0.05 on held-out validation
  window.
- Backtest gate: `GroupBBacktestResult` emits with sharpe_ratio non-zero, num_trades > 50, and the fill series passes
  replay parity with an engine-driven live-mode dry-run.
- Documentation gate: this plan's checkboxes all flipped to `[x]` and a
  `codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md` "Realised instances" row added for
  `ML_DIRECTIONAL_CONTINUOUS@cme-es-dated-1m-usd-prod`.

## 8. What this plan explicitly does NOT solve

- **Real roll handling (B2 + B5 properly)**: the Tier 1 MVP uses a stitched continuous series. That's fine for
  strategy-alpha attribution but hides roll costs. Full fix is the Tier 2 path (`representative-future-service` + UAC
  `RepresentativeFutureRegistry` + UTL events + strategy-service engine extension).
- **Execution-alpha backtest**: Group B is strategy alpha (zero execution alpha by construction). Execution alpha
  requires `execution-service` matching engine + CME liquidity assumptions; that's a Group-A follow-up.
- **Options-on-ES expression variants**: archetype supports `atm_call` / `25d_call` expressions — that's a separate
  training + feature-pipeline build since CME options have OPRA schema and greeks. Out of scope for this plan.

## 9. Follow-up items (post-MVP)

- [ ] Build `representative-future-service` (BL-10) + UAC `RepresentativeFutureRegistry`
- [ ] Extend `MLDirectionalContinuousEngine` with `FUTURES_ROLL` emission on roll events
- [ ] Add Reuters / Bloomberg macro event flags for FOMC / CPI / NFP wiring via features-calendar-service
- [ ] Options-on-ES delta expression training path
- [ ] Execution alpha measurement for CME ES via execution-service matching engine

## 10. Todos (Cursor checkboxes — SSOT)

### Phase A — Data foundation

- [ ] [HUMAN] P0. Verify CME ES multi-year `ohlcv_1m` data presence in
      `gs://<tick-data-bucket>/raw_tick_data/by_date/.../venue=CME/.../data_type=ohlcv_1m/ES-*.parquet`. Command:
      `gsutil ls gs://<bucket>/_index/availability_index.parquet` +
      `python -c "import pandas as pd; df = pd.read_parquet('...'); print(df[(df.venue=='CME')&(df.data_type=='ohlcv_1m')].groupby('attempted_at').size())"`.
- [ ] [AGENT] P0. Write `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh` — copy pattern from
      `launch-cefi-sharded-backfill.sh`; `VM_CATEGORY=TRADFI`, `VM_SERVICE=mtds`, metadata for ES expiries 2022-2026.
- [ ] [AGENT] P0. Extend `deployment-service/scripts/vm/create-code-tarballs.sh` `TRADFI_REPOS` with
      `ml-training-service`; add
      `--include features-multi-timeframe-service features-calendar- service features-volatility-service` as scoped
      defaults.

### Phase B — Continuous-series builder

- [ ] [AGENT] P0. Add `market-tick-data-service/market_tick_data_service/scripts/ build_continuous_es.py` — roll on
      volume-crossover heuristic between front and next month; write `CME:CONTINUOUS:ES` partition parquet under
      standard TRADFI canonical path.
- [ ] [AGENT] P0. Add test `tests/market_interface/adapters/tradfi/test_continuous_es_roll.py` — validates stitch
      continuity, no gaps, roll-day price continuity check.

### Phase C1 — ml-training-service registration (parallel)

- [ ] [AGENT] P0. Register ES in `ml-training-service/ml_training_service/cli/parser.py`:
      `INSTRUMENTS["TRADFI"] = ["SPY", "ES"]`; `INSTRUMENT_ID_MAP["ES"] = "CME:CONTINUOUS:ES"`.
- [ ] [AGENT] P1. Add target-builder smoke test for ES in `ml-training-service/tests/`.
- [ ] [AGENT] P0. Run `bash scripts/quality-gates.sh` on ml-training-service.

### Phase C2 — features orchestration (parallel with C1)

- [ ] [AGENT] P1. Verify `features-multi-timeframe-service` emits a feature_group including `CME:CONTINUOUS:ES` on the
      `ohlcv_1m` tick stream. Add smoke test under `features-multi-timeframe-service/tests/` if missing.
- [ ] [AGENT] P1. Confirm `features-calendar-service` macro-event flags (FOMC / CPI / NFP) are wired into the
      feature_group consumed by ML_DIRECTIONAL_CONTINUOUS for TRADFI.

### Phase D — Model training

- [ ] [AGENT] P0. Write `deployment-service/scripts/vm/launch-ml-training-vm.sh` — `VM_CATEGORY=TRADFI`,
      `VM_SERVICE=ml-training-service`, gpu-enabled optional.
- [ ] [AGENT] P0. Train ES-1m swing_high + swing_low models via ml-training-service CLI:
      `--instrument ES --timeframe 1m --target swing_high` (repeat swing_low).
- [ ] [AGENT] P0. Register model in `unified-trading-library.ml.model_registry` as `TRADFI_ES_CATBOOST_V1` (or `_XGB_V1`
      / `_LIGHTGBM_V1` — depending on hyperparam-search outcome).

### Phase E — Backtest run

- [ ] [AGENT] P0. Write strategy-service slot registration for `ML_DIRECTIONAL_CONTINUOUS@cme-es-dated-1m-usd-prod` in
      `strategy_service/engine/strategies/v2/target_universe/catalog.py`.
- [ ] [AGENT] P0. Run `strategy-service` batch-handler CLI on a 1-3 year window:
      `strategy-service --operation backtest --mode batch --category tradfi  --archetype ML_DIRECTIONAL_CONTINUOUS --slot cme-es-dated-1m-usd-prod  --start-date 2023-01-01 --end-date 2025-12-31`.
      Verify `GroupBBacktestResult` emits with expected columns + non-zero fill count.
- [ ] [AGENT] P0. Persist result summary (`sharpe_ratio`, `total_pnl`, `max_drawdown`, `num_trades`, `win_rate`) + P&L
      curve png as backtest artefact under GCS.
- [ ] [AGENT] P1. Refresh VM tarballs: `bash deployment-service/scripts/vm/ create-code-tarballs.sh --category TRADFI`.
- [ ] [AGENT] P2. Add a "Realised instances" row to
      `codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md`.
