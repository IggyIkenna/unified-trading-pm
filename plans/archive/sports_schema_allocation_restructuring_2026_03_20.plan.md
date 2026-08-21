---
doc_type: plan
title: sports-schema-allocation-restructuring
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-20'
overview: 'Fix 7 misplaced sports schemas + prediction market cross-venue mappings.

  Phases 0-7: schema moves (DONE). Phase 8: PredictionMarketMapping type +

  Polymarket/Kalshi football + crypto/macro mapping data.

  '
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-internal-contracts, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-reference-data-interface, code: C0, deployment: none, business: none}
- {repo: unified-features-interface, code: C0, deployment: none, business: none}
- {repo: unified-market-interface, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: instruments-service, code: C0, deployment: none, business: none}
- {repo: features-sports-service, code: C0, deployment: none, business: none}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none}
depends_on: [sports-canonical-mapping-and-gcs-migration]
todos:
- {id: p0a-commit-instruments, content: "- [x] [AGENT] P0. Commit instruments-service pending QG fixes + sports mapping migration.\n  Commit 5de52bd: 83 files, +4660/-10400.\n", status: done}
- {id: p0b-commit-uac, content: "- [x] [AGENT] P0. Commit UAC sports data + DeFi cleanup + registry.\n  Commit cdc5610: 121 files, +19519/-17415.\n", status: done}
- {id: p0c-commit-usri, content: '- [x] [AGENT] P0. Commit USRI re-exports. Commit 618b6b8.

    ', status: done}
- {id: p1a-uic-sports-feature-vector, content: "- [x] [AGENT] P0. Add SportsFeatureVector + 5 mixin files to UIC.\n  Commit 4d43f1e: 8 files, +1474.\n", status: done}
- {id: p1b-uac-round-names, content: "- [x] [AGENT] P0. Add round_names.py to UAC canonical/domain/sports/.\n  Part of commit d9e729b.\n", status: done}
- {id: p2a-uac-remove-feature-vector, content: "- [x] [AGENT] P0. Remove SportsFeatureVector from UAC (clean break).\n  Commit d9e729b: deleted 6 files, updated 4 init files.\n", status: done}
- {id: p2b-instruments-replace-round-names, content: "- [x] [AGENT] P0. Replace round_names with UAC re-export.\n  Part of commit d806b8f.\n", status: done}
- {id: p3a-urdi-api-football, content: "- [x] [AGENT] P0. Create ApiFootballReferenceDataAdapter in URDI.\n  Commits fa34336 + 72fcaca (adapter + factory/router registration).\n", status: done}
- {id: p3b-features-interface-understat-footystats, content: "- [x] [AGENT] P0. Create understat + footystats adapters in features-interface.\n  Commit 8cc1aad: 6 files, +323.\n", status: done}
- {id: p3c-umi-remove-adapters, content: "- [x] [AGENT] P0. Remove 3 adapters from UMI alt_data.\n  Commit b1c335c: 2 files, -20 +9.\n", status: done}
- {id: p4a-mtds-dedup, content: "- [x] [AGENT] P0. MTDS schemas → UIC re-export.\n  Commit c26ebe1: -106 +10.\n", status: done}
- {id: p4b-fss-imports, content: "- [x] [AGENT] P0. FSS imports → URDI + features-interface.\n  Commit bd64769.\n", status: done}
- {id: p5-validation-sweep, content: "- [x] [SCRIPT] P0. All 9 repos committed, pre-commit hooks pass.\n  QG sweep deferred to post-Phase-8.\n", status: done}
- {id: p6-gcs-player-migration, content: "- [x] [AGENT] P0. GCS player mapping migration script.\n  Commit 2fe23a0 in PM.\n", status: done}
- {id: p7a-player-alias-resolver, content: "- [x] [AGENT] P0. PlayerAliasResolver + tests.\n  Commit d806b8f in instruments-service.\n", status: done}
- {id: p7b-player-alias-tests, content: "- [x] [AGENT] P0. test_player_aliases.py (6 tests) + QG exclusion.\n  Commit d806b8f.\n", status: done}
- {id: p8a-prediction-market-mapping-type, content: "- [ ] [AGENT] P0. Create PredictionMarketMapping type in UAC.\n  File: canonical/domain/prediction_markets/mappings.py\n  Frozen BaseModel with:\n  - canonical_event_id (str): e.g. \"EPL:ARS-v-CHE:20260322\" or \"BTC:ABOVE:95000:20260321T1400Z\"\n  - category (str): \"sports\" | \"crypto\" | \"macro\"\n  - sub_category (str): \"epl\" | \"btc_price\" | \"spx_close\"\n  - underlying (str | None): \"BTC\", \"SPX\", None for sports\n  - odds_api_event_id (str | None): Only for sports\n  - api_football_fixture_id (int | None): Only for sports\n  - polymarket_condition_id (str | None)\n  - polymarket_neg_risk_market_id (str | None)\n  - kalshi_event_ticker (str | None)\n  - kalshi_market_ticker (str | None)\n  - timeframe (str | None): \"5m\", \"1h\", \"1d\", None for sports\n  - strike (float | None): 95000.0 (BTC), 5800.0 (SPX), None for sports\n  - expiry_utc (datetime | None)\n  Export from UAC __init__.py and new prediction_markets.py facade.\n",
  status: todo}
- {id: p8b-polymarket-sports-mappings, content: "- [ ] [AGENT] P0. Add Polymarket sports mapping data.\n  File: external/polymarket/sports_mappings.py\n  Map Odds API football fixtures → Polymarket condition_ids.\n  Scope: leagues currently in LEAGUE_REGISTRY with Odds API coverage.\n  Pattern: dict[str, str] keyed by canonical fixture ID.\n  Include helper: get_polymarket_condition_id(fixture_id: str) -> str | None\n", status: todo, blocked_by: p8a-prediction-market-mapping-type}
- {id: p8c-polymarket-crypto-mappings, content: "- [ ] [AGENT] P0. Add Polymarket crypto/macro mapping data.\n  File: external/polymarket/crypto_macro_mappings.py\n  Map BTC up/down markets (5m to 1d timeframes) and S&P up/down markets\n  to Polymarket condition_ids.\n  Pattern: list[PredictionMarketMapping] for active markets.\n  Note: crypto/macro markets are ephemeral (created daily) — data here is\n  the SCHEMA + helpers, not static lookup tables. Dynamic resolution via\n  Gamma API tag_slug=\"crypto\"|\"economics\" at runtime.\n  Include: POLYMARKET_CRYPTO_TAG_SLUGS, POLYMARKET_MACRO_TAG_SLUGS constants.\n", status: todo, blocked_by: p8a-prediction-market-mapping-type}
- {id: p8d-kalshi-sports-mappings, content: "- [ ] [AGENT] P0. Add Kalshi sports mapping data.\n  File: external/kalshi/sports_mappings.py\n  Map Odds API football fixtures → Kalshi event/market tickers.\n  Pattern mirrors polymarket/sports_mappings.py.\n  Include helper: get_kalshi_ticker(fixture_id: str) -> str | None\n", status: todo, blocked_by: p8a-prediction-market-mapping-type}
- {id: p8e-kalshi-crypto-macro-mappings, content: "- [ ] [AGENT] P0. Add Kalshi crypto/macro mapping data.\n  File: external/kalshi/crypto_macro_mappings.py\n  Map BTC up/down (KXBTC series) and S&P up/down (KXSPY series).\n  Kalshi uses structured tickers: KXBTC-{DATE}-T{STRIKE}\n  Include: parse_kalshi_ticker() to extract underlying, strike, expiry.\n", status: todo, blocked_by: p8a-prediction-market-mapping-type}
- {id: p8f-urdi-kalshi-adapter, content: "- [ ] [AGENT] P1. Create KalshiReferenceDataAdapter in URDI.\n  Port from existing Kalshi schemas in UAC external/kalshi/.\n  Return InstrumentRecord with instrument_type=\"prediction_market\".\n  Register in factory + router.\n  QG: cd unified-reference-data-interface && bash scripts/quality-gates.sh\n", status: todo}
- {id: p8g-prediction-market-resolver, content: "- [ ] [AGENT] P1. Create PredictionMarketResolver in instruments-service.\n  File: instruments_service/sports/prediction_market_resolver.py\n  Mirrors TeamAliasResolver/PlayerAliasResolver pattern.\n  Resolves same event across Polymarket, Kalshi, Odds API.\n  Methods: find_by_polymarket_id(), find_by_kalshi_ticker(),\n  find_by_odds_api_event(), find_by_fixture_id().\n  For crypto/macro: find_by_underlying_strike_expiry().\n", status: todo, blocked_by: p8b-polymarket-sports-mappings}
- {id: p8h-qg-sweep, content: "- [ ] [SCRIPT] P0. Full QG sweep: UAC, URDI, instruments-service.\n  Verify PredictionMarketMapping importable from UAC facade.\n  Verify KalshiReferenceDataAdapter in URDI factory.\n  Verify PredictionMarketResolver tests pass.\n", status: todo, blocked_by: p8g-prediction-market-resolver}
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Sports Schema Allocation Restructuring

## Problem

Sports domain audit identified 7 misplaced schemas violating the system's allocation principles:

1. **SportsFeatureVector** (derived ML feature, 16 mixins, 250+ fields) in UAC — should be UIC
2. **MTDS schemas/sports.py** — duplicate of UIC SSOT (file says "migration pending Phase 2")
3. **ApiFootballAdapter** in UMI — fetches reference data, belongs in URDI
4. **UnderstatAdapter** in UMI — fetches derived features (xG), belongs in features-interface
5. **FootystatsAdapter** in UMI — fetches derived features, belongs in features-interface
6. **round_names.py** in instruments-service — reference data registry, belongs in UAC
7. Plus: GCS player mapping migration + PlayerAliasResolver (new capabilities)

## Allocation Principles (User-Defined)

| Data type                               | Schema location                  | Connectivity       | Owner service            |
| --------------------------------------- | -------------------------------- | ------------------ | ------------------------ |
| Raw market data (odds)                  | UAC canonical + UIC tick schemas | UMI                | market-tick-data-service |
| Derived features (xG, predictors)       | UIC features_sports/             | features-interface | features-sports-service  |
| Static reference data (fixtures, teams) | UAC canonical + UIC storage      | URDI               | instruments-service      |
| External raw schemas                    | UAC external/{provider}/         | N/A                | N/A                      |
| Registry/config                         | UAC registry/                    | N/A                | N/A                      |

## Dependency DAG

```
Phases 0-7 ── ALL DONE ────────────────────────
                    │
Phase 8 ┌─ 8a: PredictionMarketMapping type ─────────────┐
[PARALLEL] ├─ 8b: Polymarket sports mappings (football)     │
           ├─ 8c: Polymarket crypto/macro mappings (BTC/SPX)│
           ├─ 8d: Kalshi sports mappings                    │
           ├─ 8e: Kalshi crypto/macro mappings              │ QG gate
           ├─ 8f: KalshiReferenceDataAdapter (URDI)         │
           └─ 8g: PredictionMarketResolver (instruments)  ──┤
                                                            │
Phase 8h ── Full QG sweep ──────────────────────────────────
```

## Pre-Audit: Blast Radius

| Move                                 | Files affected                                                           | Runtime imports outside source |
| ------------------------------------ | ------------------------------------------------------------------------ | ------------------------------ |
| SportsFeatureVector (UAC→UIC)        | 57 files total — all UAC-internal or UI context copies                   | **Zero**                       |
| MTDS duplicate                       | 2 consumers: odds_tick_adapter.py:34, test_sports_schemas.py:10          | 2 files                        |
| ApiFootballAdapter (UMI→URDI)        | 2 consumers: features-sports-service cli/\_providers.py, UMI **init**.py | 2 files                        |
| Understat/FootyStats (UMI→feat-intf) | 2 consumers each: FSS cli/\_providers.py, UMI **init**.py                | 2 files each                   |
| round_names (instruments→UAC)        | Used only within instruments-service sports/ module                      | 0 external                     |

## NSBS GCS Migration Assessment

| Bucket                                   | Content                | Action                                     |
| ---------------------------------------- | ---------------------- | ------------------------------------------ |
| football-raw-data-all-sources-{pid}      | Raw reference parquets | FOLLOW-UP                                  |
| market-data-tick-sports-{pid}-v3         | Odds ticks 50GB+       | FOLLOW-UP                                  |
| football-mapped-consolidated-{pid}       | Canonical mappings     | Phase 6 (player), follow-up (team/fixture) |
| football-ml-features-{pid}               | Feature vectors        | NO — regenerate                            |
| football-ml-models-and-predictions-{pid} | CatBoost models        | NO — retrain                               |
| football-backtest-results-{pid}          | Backtest outputs       | NO — re-run                                |

## Success Criteria

**Phases 0-7 (DONE):**

- All 9 repo commits pass pre-commit hooks
- SportsFeatureVector importable from UIC, ImportError from UAC (clean break)
- ApiFootballReferenceDataAdapter in URDI factory, removed from UMI
- UnderstatAdapter/FootystatsAdapter in features-interface, removed from UMI
- PlayerAliasResolver tests pass, migration script runs in dry-run

**Phase 8 (pending):**

- `from unified_api_contracts import PredictionMarketMapping` works
- `from unified_api_contracts.external.polymarket import get_polymarket_condition_id` works
- `from unified_api_contracts.external.kalshi import get_kalshi_ticker` works
- KalshiReferenceDataAdapter registered in URDI factory
- PredictionMarketResolver resolves same event across Polymarket, Kalshi, Odds API
- All 3 repos QG green (UAC, URDI, instruments-service)
