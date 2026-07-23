---
title:
  "Data catalogue cleanup — OddsJam removal, PredictIt removal, Betdaq/Smarkets, combo adapter wiring, Hyperliquid/Aster
  assertion"
status: active
created: 2026-04-24
locked_by: live-defi-rollout
locked_since: 2026-04-24
---

# Data catalogue cleanup — OddsJam removal, PredictIt removal, Betdaq/Smarkets, combo adapter wiring, Hyperliquid/Aster assertion

## Context

Several catalogue entries are either dead weight (OddsJam, PredictIt), partially wired stubs that create false coverage
scores (Betdaq/Smarkets), or structurally ready but never activated (combo instruments for CeFi/TradFi). Additionally,
Hyperliquid and Aster declare no options capability in UAC but there is no explicit runtime assertion blocking an
options fetch attempt — the absence of a capability declaration needs to be a hard error.

For prediction markets, focus is Polymarket (1000+ markets), Kalshi, Manifold. PredictIt is declining/legacy and should
be removed entirely rather than maintained as a stub.

For sports, OddsAPI provides historical odds (the main use case). Oddsjam has no active adapter and provides no
additional coverage. Betdaq and Smarkets have partial structure but no live odds normalization — they should either be
completed or removed. Recommendation: remove Betdaq/Smarkets too (OddsAPI + Betfair covers the necessary spread).

Combos: `InstrumentType.COMBO` exists in UAC, `combo_type`/`leg_weights` columns are in manifest v6, but no
instruments-service adapter fetches combo instruments, and no MTDS adapter captures combo-specific data. DERIBIT
publishes combo strategies; IBKR/Databento publish spread contracts. These need to be wired.

## Scope

**In-scope:**

- Remove OddsJam from all repos (UAC, instruments-service, UI schemas, comments)
- Remove PredictIt adapter and all references (instruments-service, MTDS, UAC capability declarations)
- Remove Betdaq and Smarkets adapters and references (instruments-service, MTDS, UAC)
- Add explicit `UnsupportedCapabilityError` when options/futures are requested for Hyperliquid or Aster
- Wire instruments-service combo adapter for DERIBIT (CeFi) and Databento/IBKR (TradFi)
- Wire MTDS combo data type for DERIBIT combo strategies

**Out-of-scope:**

- Combo Greeks/P&L feature calculator (separate ML/features plan)
- Sports reference data changes (covered by `sports_data_completeness`)
- Weather or venue data for sports

## Pre-audit manifest

| Repo                      | File                                                           | Action                                                                                      |
| ------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| UAC                       | `unified_api_contracts/` + `registry/capability_declarations/` | Remove OddsJam, PredictIt, Betdaq, Smarkets entries; add combo fetch capability for DERIBIT |
| instruments-service       | `reference_data/adapters/sports/`                              | Remove oddsjam_adapter.py, betdaq_adapter.py, smarkets_adapter.py                           |
| instruments-service       | `reference_data/adapters/prediction/`                          | Remove predictit_adapter.py                                                                 |
| instruments-service       | `reference_data/adapters/cefi/`                                | Add deribit_combo_adapter.py                                                                |
| instruments-service       | `reference_data/adapters/tradfi/`                              | Add combo discovery for Databento/IBKR                                                      |
| MTDS                      | `market_interface/adapters/sports/`                            | Remove betdaq, smarkets adapter files                                                       |
| MTDS                      | `market_interface/adapters/cefi/`                              | Add combo data type handling in tardis_adapter                                              |
| MTDS                      | `market_interface/adapters/cefi/tardis_adapter.py`             | Add UnsupportedCapabilityError for Hyperliquid/Aster options                                |
| deployment-api            | expectation config                                             | Remove PredictIt, OddsJam, Betdaq, Smarkets from expected-count rows                        |
| deployment-ui             | `src/lib/data-status-helpers.ts` + BookmakerInfo schemas       | Remove OddsJam entry                                                                        |
| unified-trading-system-ui | `context/api-contracts/canonical-schemas/domain/`              | Remove OddsJam BookmakerInfo                                                                |

## Phases

### Phase 1 — Removals (PARALLEL)

- [ ] [AGENT] P0. Remove OddsJam from everywhere: (a) UAC: delete `bookmaker_registry.py` OddsJam entry; remove from any
      `source_tier` strings. (b) instruments-service: delete `oddsjam_adapter.py` if it exists; remove import/dispatch
      references. (c) MTDS: same. (d) unified-trading-system-ui: remove `BookmakerInfo` entry and any `source_tier`
      comment mentioning oddsjam. (e) deployment-ui: remove from data-status-helpers.ts if present. Search:
      `rg -i "oddsjam|odds_jam" --type py --type ts --glob '!.venv*'` — must return 0 results post-removal.

- [ ] [AGENT] P0. Remove PredictIt from everywhere: (a) UAC: delete capability declaration; remove from prediction venue
      enum if present. (b) instruments-service: delete `predictit_adapter.py`; remove from orchestrator dispatch. (c)
      MTDS: delete `predictit_adapter.py`; remove from orchestrator dispatch. (d) deployment-api: remove from
      expected-count config. Search: `rg -i "predictit" --type py --glob '!.venv*'` — must return 0 post-removal.

- [ ] [AGENT] P0. Remove Betdaq and Smarkets from everywhere: (a) UAC: delete capability declarations for both venues.
      (b) instruments-service: delete `betdaq_adapter.py`, `smarkets_adapter.py`; remove dispatch. (c) MTDS: delete any
      Betdaq/Smarkets adapter files; remove dispatch. (d) deployment-api: remove from expected-count config. Retain
      OddsAPI and Betfair — those stay. Search: `rg -i "betdaq|smarkets" --type py --glob '!.venv*'` — must return 0
      post-removal.

### Phase 2 — Hyperliquid/Aster options guard (PARALLEL with Phase 1)

- [ ] [AGENT] P0. In MTDS `tardis_adapter.py` (or wherever venue capability is checked before fetching), add an explicit
      guard: if `venue in {HYPERLIQUID, ASTER}` and `instrument_type in {OPTION, FUTURE}`, raise
      `UnsupportedCapabilityError(venue=venue, capability="options")` with a clear message. This turns a silent no-op or
      confusing 400 into a loud, diagnosable error.
- [ ] [AGENT] P0. Add the same guard in instruments-service: if an options fetch is attempted for Hyperliquid or Aster,
      raise immediately rather than returning empty results.
- [ ] [AGENT] P0. UAC `capability_declarations/_cefi.py`: add a docstring/comment to Hyperliquid and Aster entries
      explicitly stating `OPTIONS: not supported — venue does not offer listed options contracts`. This prevents future
      agents from adding options logic for these venues.

### Phase 3 — QG pass for removals

- [ ] [QG] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`
- [ ] [QG] P0. `cd instruments-service && bash scripts/quality-gates.sh`
- [ ] [QG] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh`
- [ ] [QG] P0. `cd deployment-service && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. `cd deployment-ui && CI=true npm test -- --run` green.
- [ ] [SCRIPT] P0. Quickmerge all affected repos.

### Phase 4 — Combo instruments adapter: CeFi (DERIBIT) (SEQUENTIAL after Phase 3)

- [ ] [AGENT] P1. instruments-service: add `deribit_combo_adapter.py`. Fetch DERIBIT published combo strategies
      (multi-leg options: straddles, strangles, call/put spreads, condors). DERIBIT exposes these as instruments with
      `kind=combo` in their API. Write to instruments manifest with `instrument_type=COMBO`,
      `combo_type=<strategy_type>`, `leg_weights=<json>`. One manifest row per combo instrument per date.
- [ ] [AGENT] P1. MTDS `tardis_adapter.py`: add handling for `data_type=COMBO_CHAIN` bulk download. When
      `instrument_type=COMBO` and `canonical_bucket` is set, use the existing `download_csv_streaming` path (same as
      options_chain). Shard key: `venue × underlying × date × data_type=COMBO_CHAIN`. Manifest row:
      `instrument_type=COMBO, underlying=BTC or ETH`.
- [ ] [QG] P1. `cd instruments-service && bash scripts/quality-gates.sh`
- [ ] [QG] P1. `cd market-tick-data-service && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P1. Quickmerge instruments-service and MTDS.

### Phase 5 — Combo instruments adapter: TradFi (Databento/IBKR) (PARALLEL with Phase 4)

- [ ] [AGENT] P1. instruments-service TradFi adapter: add combo discovery for Databento (equity spreads, option combos
      like verticals/calendars/condors) and IBKR (multi-leg orders). Write to manifest with
      `instrument_type=COMBO, combo_type=<spread_type>, leg_weights=<json>`.
- [ ] [AGENT] P1. MTDS TradFi adapter: fetch combo contract data from Databento/IBKR when `instrument_type=COMBO`. Shard
      key: `venue × underlying × date × data_type=COMBO_CHAIN`.
- [ ] [QG] P1. QG on instruments-service and MTDS.
- [ ] [SCRIPT] P1. Quickmerge.

### Phase 6 — Codex + PM

- [ ] [AGENT] P1. Update `/codex/02-data/availability-manifest-and-data-status.md`: document combo shard key,
      Hyperliquid/Aster options exclusion, removed venues (OddsJam/PredictIt/Betdaq/Smarkets).
- [ ] [SCRIPT] P1. Quickmerge PM.

## Success criteria

- **Removal gate:** `rg -i "oddsjam|predictit|betdaq|smarkets" --type py --glob '!.venv*'` returns 0 results.
- **Guard gate:** Attempting to fetch options for Hyperliquid or Aster raises `UnsupportedCapabilityError` in both
  instruments-service and MTDS.
- **Combo gate:** `manifest.lookup(venue=DERIBIT, instrument_type=COMBO)` returns rows; parquet exists in GCS for at
  least 1 DERIBIT combo instrument.
- **Code gates:** All affected repos QG green.
