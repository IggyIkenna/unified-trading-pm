# Sports Betting Service - Documentation

**Purpose:** Syndicate-level sports betting ML pipeline for football (soccer) prediction.

**Coverage:** 34 leagues, 5 seasons (2020-2024), pre-game + half-time predictions **Final Test:** 2025 reserved as
out-of-sample validation

---

## 📚 Document Overview

| Document                             | Purpose                                                                                        | Lines  | Read Order |
| ------------------------------------ | ---------------------------------------------------------------------------------------------- | ------ | ---------- |
| **README.md**                        | This file - navigation guide                                                                   | -      | 1st        |
| **HARSH_IMPLEMENTATION_GUIDE.md**    | 8-week build plan with milestones                                                              | ~1,200 | 2nd        |
| **reference_data_spec.md**           | Stage 1 reference datasets (canonical keys + provider ID mappings)                             | ~220   | 3rd        |
| **raw_data_spec.md**                 | Stage 2 raw download spec (datasets/tables/partitions/clusters) + field appendix               | ~1,500 | 4th        |
| **PROCESSING_PROVIDERS_AND_CLI.md**  | Provider-grouped processing architecture + standard CLI contract + Odds API market-data layout | -      | 5th        |
| **FEATURES_CATALOG.md**              | Authoritative feature list (every feature header) + type/horizon/min-math                      | -      | 6th        |
| **FEATURES_IMPLEMENTATION_GUIDE.md** | Feature implementation nuances (anti-leakage, windows, priors, HT sequencing)                  | -      | 7th        |
| **FEATURES_DOMAIN_GUIDES.md**        | Narrative domain guides (match/team/player/lineup/referee/weather/market/HT)                   | -      | 8th        |
| **FEATURE_ENGINEERING.md**           | Feature inventory (~677 features)                                                              | ~5,400 | 5th        |
| **ML_MODELS.md**                     | Model architecture, trading intelligence                                                       | ~1,800 | 6th        |
| **DEPLOYMENT_GUIDE.md**              | Local → GCP → AWS migration                                                                    | ~450   | 7th        |
| **models.py**                        | Database schemas (SQLAlchemy)                                                                  | ~3,400 | Reference  |
| **CONTRACTOR_AGREEMENT_HARSH.md**    | Contract & payment terms                                                                       | ~1,200 | Reference  |

---

## ⚠️ PROJECT SCOPE

### What This Project DOES (IN SCOPE)

| Stage         | Markets      | Description                                                    |
| ------------- | ------------ | -------------------------------------------------------------- |
| **Pre-Game**  | 1X2, O/U, AH | Arbitrage classification, CLV beating, outcome prediction      |
| **Half-Time** | 1X2, O/U, AH | HT delta CLV, HT delta outcomes (using pre-game + HT features) |

### Betting Markets Covered

| Market  | Full Name        | Prediction                               |
| ------- | ---------------- | ---------------------------------------- |
| **1X2** | Match Winner     | Home Win / Draw / Away Win probabilities |
| **O/U** | Over/Under Goals | Over/Under 2.5 (and other lines)         |
| **AH**  | Asian Handicap   | Handicap-adjusted outcomes               |

### What This Project Does NOT Do (OUT OF SCOPE)

| Item                            | Status          | Notes                |
| ------------------------------- | --------------- | -------------------- |
| **In-Play / Live Betting**      | ❌ NOT IN SCOPE | Future phase         |
| **In-Play Predictions**         | ❌ NOT IN SCOPE | Future phase         |
| **Market Making**               | ❌ NOT IN SCOPE | Future phase         |
| **Fully Automated Execution**   | ❌ NOT IN SCOPE | Semi-automated only  |
| **Exchange Trading / Scalping** | ❌ NOT IN SCOPE | Future phase         |
| **Sports Other Than Football**  | ❌ NOT IN SCOPE | Football only        |
| **Leagues Beyond 36**           | ❌ NOT IN SCOPE | 36 specified leagues |

---

## 🗺️ How to Navigate

### If you're starting the project:

1. **Start with `HARSH_IMPLEMENTATION_GUIDE.md`** - 8-week build plan with task IDs
2. Reference other docs as needed per milestone

### If you need to understand data:

1. **Read `reference_data_spec.md`** - Stage 1 canonical keys + provider ID mappings (join layer)
2. **Read `raw_data_spec.md`** - Stage 2 raw download layout + provider endpoint tables
3. **Read `PROCESSING_PROVIDERS_AND_CLI.md`** - provider-grouped processing boundaries + standard CLI contract + Odds
   API market-data output layout
4. Check `models.py` for database schema

### If you need to build features:

1. **Read `FEATURES_CATALOG.md`** - canonical feature list (every feature header), types, horizons
2. **Read `FEATURES_IMPLEMENTATION_GUIDE.md`** - anti-leakage rules, windows, priors, HT sequencing
3. **Read `FEATURES_DOMAIN_GUIDES.md`** - domain narrative (match/team/player/lineup/referee/weather/market/HT)
4. Reference `FEATURE_ENGINEERING.md` for the original long-form inventory and examples (legacy, still useful)
5. Reference `raw_data_spec.md` (provider field appendix) for source fields

### Archived legacy feature docs

Prior feature docs were consolidated and are preserved for historical context in `sports-betting-service/docs/archive/`.

### If you need to train models:

1. **Read `ML_MODELS.md`** - Model specs, training, trading intelligence
2. Check walk-forward validation in `HARSH_IMPLEMENTATION_GUIDE.md`

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES (7)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ API-Football │ Soccerfootball.info │ FootyStats │ Transfermarkt     │   │
│  │ Understat (5 leagues) │ Odds API │ Open-Meteo                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  📄 raw_data_spec.md + reference_data_spec.md                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FEATURE ENGINEERING (~677)                            │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Market (123) │ Team (60) │ Multi-xG (50) │ Lineup (69) │ Context (81)│   │
│  │ Style (48) │ Manager (32) │ Poisson (42) │ HT Seq (45) │ Efficiency (34)│
│  └────────────────────────────────────────────────────────────────────┘    │
│  📄 FEATURE_ENGINEERING.md                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ML MODELS (8)                                      │
│  ┌─────────────────────────────────┬───────────────────────────────────┐   │
│  │     PRE-GAME MODELS             │        HT DELTA MODELS            │   │
│  │ 2A/3A: CLV @ T-24h              │ 6: HT Delta Base                  │   │
│  │ 2B/3B: CLV @ T-1h               │ 7: HT Delta Meta                  │   │
│  │ 4/5: xG + H2H                   │ Final = PreGame + Delta           │   │
│  └─────────────────────────────────┴───────────────────────────────────┘   │
│  📄 ML_MODELS.md                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TRADING INTELLIGENCE                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Bet Selection │ Kelly Sizing │ Drift Detection │ Arb Classification │   │
│  │ Multi-Model Arbitration │ Market Simulation │ Execution Layer       │   │
│  └────────────────────────────────────────────────────────────────────┘    │
│  📄 ML_MODELS.md §10                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📅 8-Week Build Plan

| Week | Milestone           | Deadline | Key Deliverables                        |
| ---- | ------------------- | -------- | --------------------------------------- |
| 0    | Data Extraction     | Dec 12   | All 7 sources, 34 leagues               |
| 1    | Feature Framework   | Dec 19   | FeatureBuilder, 15 core features        |
| 2    | Pre-Game Features   | Dec 26   | ~500 features, synthetic xG             |
| 3    | Pre-Game Models     | Jan 2    | CLV + xG models, walk-forward           |
| 4    | HT Delta Model      | Jan 9    | Sequencing features, delta architecture |
| 5    | Backtesting         | Jan 16   | Full backtest, ROI dashboards           |
| 6    | Semi-Auto Execution | Jan 23   | Signals, Telegram, dashboard            |
| 7    | Validation & Live   | Jan 30   | Drift detection, soft-live              |

**📄 Full details: `HARSH_IMPLEMENTATION_GUIDE.md`**

---

## 🎯 Key Concepts

### 1. Multi-Source xG

We use **3 labeled xG sources** - disagreement between them is a feature:

| Source         | Coverage         | Confidence |
| -------------- | ---------------- | ---------- |
| Understat      | 5 leagues        | 1.0        |
| Soccerfootball | 35 leagues       | 0.9        |
| FootyStats     | 33 of 35 leagues | 0.85       |
| API-Football   | 35 leagues       | 0.8        |
| Synthetic      | 35 leagues       | 0.75       |

**📄 Details: `FEATURE_ENGINEERING.md` §3.8**

---

### 2. HT Delta Architecture

Half-time models predict **delta adjustments**, not absolute values:

```python
HT_prediction = PreGame_prediction + Model7_Delta(pregame_preds, ht_features)
```

**📄 Details: `ML_MODELS.md` §4**

---

### 3. Market Efficiency Filtering

Not all fixtures are equally "learnable":

```python
if learnability_score < 0.4:
    skip_fixture_flag = 1  # Don't bet on noisy markets
```

**📄 Details: `FEATURE_ENGINEERING.md` §5**

---

### 4. Arb Bucket Classification

| Bucket | Type            | Example            | Edge Range | Risk    |
| ------ | --------------- | ------------------ | ---------- | ------- |
| 1      | Soft → Sharp    | Bovada → Pinnacle  | 0.2-0.6%   | Low     |
| 2      | Soft → Soft     | Bovada → BetOnline | 0.4-1.2%   | Medium  |
| 3      | Soft → Exchange | Bovada → Betfair   | 0.5-1.5%   | Low-Med |

**📄 Details: `ML_MODELS.md` §10.5**

---

### 5. Actual Bookmakers (from Odds API)

| Type           | Bookmakers                                               | Use For                     |
| -------------- | -------------------------------------------------------- | --------------------------- |
| **Sharp**      | `pinnacle`                                               | Reference price, CLV target |
| **Exchange**   | `betfair_uk`, `matchbook`                                | True market, arb lays       |
| **Semi-Sharp** | `lowvig`                                                 | Low margin execution        |
| **Soft**       | `bovada`, `betonlineag`, `mybookieag`, `betus`, `gtbets` | Value bets, arb backs       |

**Broker for Sharp Execution:** AsianConnect88 (free, access to PS3838/Pinnacle)

**📄 Details: `raw_data_spec.md` (Odds API appendix)**

---

### 5. Odds Snapshot Schedule

```
T-24h → T-12h → T-6h → T-90m → T-80m → T-70m → T-60m → T-50m → T-40m → T-30m → T-20m → T-10m → T-0 → HT-2min
```

**📄 Details: `raw_data_spec.md` (Odds API appendix)**

---

## 📁 Database Schema

**File:** `models.py`

### Table Categories

| Category                | Tables                                                                                                                                  | Count  |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| **Core (API-Football)** | Country, Venue, League, Team, Player, Fixture, FixtureStats, FixtureEvent, FixtureLineup, FixturePlayerStats, Injury, Standing          | 12     |
| **Soccerfootball.info** | SoccerfootballMatchStats, SoccerfootballProgressiveStats                                                                                | 2      |
| **FootyStats**          | FootystatsMatchStats, FootystatsRefereeStats, FootystatsTeamSeasonStats                                                                 | 3      |
| **Transfermarkt**       | TransfermarktPlayer, TransfermarktInjury, TransfermarktTransfer, TransfermarktManager, TransfermarktSquad                               | 5      |
| **Understat**           | UnderstatShot, UnderstatTeamStats, UnderstatMatchStats                                                                                  | 3      |
| **Odds**                | OddsSnapshot, OddsHTSnapshot, OddsHistory, OddsMicrostructure, BookmakerMeta, SharpSoftSnapshot                                         | 6      |
| **Market Efficiency**   | LeagueEfficiency                                                                                                                        | 1      |
| **Weather**             | WeatherForecast                                                                                                                         | 1      |
| **Features**            | FeatureVector, TeamRating, MultiSourceXG, TeamStyleEmbedding, ManagerProfile, RefereeTeamHistory, H2HRecord, TravelDistance             | 8      |
| **ML Models**           | MLModelRegistry, WalkForwardFold, FeatureImportance, PredictionLog                                                                      | 4      |
| **Trading**             | BetRecommendation, BetExecution, Signal, DriftAlert, BankrollSnapshot, DailyPnL, ModelPerformance, MarketSimulation, EnsemblePrediction | 9      |
| **Arbitrage**           | ArbOpportunity, ArbBucketStats                                                                                                          | 2      |
| **TOTAL**               |                                                                                                                                         | **56** |

---

## 🔗 Cross-References

### Data Source → Features

| Source         | Features Generated                                                                                              | Doc Section                   |
| -------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| API-Football   | Core fixtures, lineups, events                                                                                  | DATA_ARCH §2, FEAT_ENG §3.4   |
| Soccerfootball | HT stats, match stats                                                                                           | DATA_ARCH §3, FEAT_ENG §4.1   |
| FootyStats     | Dangerous attacks, referee                                                                                      | DATA_ARCH §4, FEAT_ENG §3.5   |
| Transfermarkt  | Squad, injuries, managers                                                                                       | DATA_ARCH §5, FEAT_ENG §3.7   |
| Understat      | Shot-level xG, PPDA                                                                                             | DATA_ARCH §6, FEAT_ENG §3.8   |
| Odds API       | Odds snapshots: T-24h, T-12h, T-6h, T-90m, T-80m, T-70m, T-60m, T-50m, T-40m, T-30m, T-20m, T-10m, T-0, HT-2min | DATA_ARCH §7, FEAT_ENG §3.1   |
| Open-Meteo     | Weather                                                                                                         | DATA_ARCH §8, FEAT_ENG §3.5.2 |

### Features → Models

| Feature Category    | Used By Models    | Doc Section        |
| ------------------- | ----------------- | ------------------ |
| Market features     | CLV (2A/2B/3A/3B) | ML_MODELS §3.1-3.2 |
| Team/xG features    | xG (4/5)          | ML_MODELS §3.3-3.4 |
| HT sequencing       | HT Delta (6/7)    | ML_MODELS §4       |
| Efficiency features | Bet Selection     | ML_MODELS §10.1    |

---

## ⚡ Quick Start Commands

```bash
# 1. Fetch all data (Milestone 0)
sports-betting fetch-all --seasons 2020-2025 --leagues ALL  # 2025 = final OOS test

# 2. Build features (Milestone 2)
sports-betting build-features --date-range 2019-01-01:2024-12-31

# 3. Train models (Milestone 3)
python scripts/train_walk_forward.py --start-year 2019 --end-year 2024

# 4. Run backtest (Milestone 5)
python scripts/backtest_pregame.py --test-year 2024

# 5. Generate signals (Milestone 6)
python scripts/generate_signals.py --date today
```

---

## 📖 Glossary

| Term                   | Definition                                    |
| ---------------------- | --------------------------------------------- |
| **CLV**                | Closing Line Value - edge vs closing odds     |
| **xG**                 | Expected Goals - probability of scoring       |
| **HT**                 | Half-Time                                     |
| **Delta Architecture** | HT models predict adjustments to pre-game     |
| **Walk-Forward**       | Train on past, test on future, expand window  |
| **Sharp Book**         | Bookmaker with accurate odds (Pinnacle)       |
| **Soft Book**          | Bookmaker with beatable odds (Bet365, SkyBet) |
| **PPDA**               | Passes Per Defensive Action (pressing metric) |
| **Learnability**       | How predictable/reliable a fixture is         |
| **Arb**                | Arbitrage opportunity across bookmakers       |

---

## 📞 Support

- **Implementation questions:** See `HARSH_IMPLEMENTATION_GUIDE.md`
- **Data questions:** See `reference_data_spec.md` (Stage 1) and `raw_data_spec.md` (Stage 2)
- **Feature questions:** See `FEATURE_ENGINEERING.md`
- **Model questions:** See `ML_MODELS.md`
- **Schema questions:** See `models.py`

---

**This is a syndicate-level sports betting system.**
