---
doc_type: plan
title: frontend-backend-bilateral-plan1-instrument-registry
summary: Build permanent instrument snapshot from real March 27 data and wire into UI registry as SSOT for mock realism
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, instruments-service, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-03'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
- {repo: instruments-service, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p1-1-snapshot-script, content: '- [x] [AGENT] P0. Create `unified-trading-pm/scripts/openapi/generate_instrument_snapshot.py` that reads ALL instruments-service CSV data (instruments_service/data/*.csv, 404 files, 13,386+ instruments from March 26-27) and produces a consolidated JSON snapshot. Output: `unified-api-contracts/openapi/instruments-snapshot.json`. Include ALL instruments from ALL venues — no filtering, no sampling. CeFi (BINANCE, OKX, BYBIT, DERIBIT, HYPERLIQUID, COINBASE, ASTER), DeFi (AAVE_V3-ETHEREUM, MORPHO-ETHEREUM, UNISWAP_V2/V3/V4-ETHEREUM, CURVE-ETHEREUM, LIDO, ETHERFI, ETHENA), TradFi (NASDAQ, NYSE, CME, ICE, CBOE), Sports (use representative_sample.py + team_mapping.csv + e2e-testing/data/live_arb/odds_state.json for ALL sports fixtures). Target: ALL instruments (~13,000+), a few MB. The UI must learn to handle grouping/filtering at scale.

    ', status: done}
- {id: p1-2-sports-fixtures, content: '- [x] [AGENT] P0. Include sports reference data in the snapshot: extract fixtures from e2e-testing/data/live_arb/odds_state.json (9.2MB, real fixtures with multi-venue odds), combine with UAC team_mapping.csv (6,245 teams) and league_registry.py to produce sports instruments in canonical format (SPORT:VENUE:MARKET_TYPE:LEAGUE:SEASON:HOME-AWAY::SELECTION). Include bookmaker availability per fixture. Target: at least 50 real sports fixtures with odds from multiple bookmakers.

    ', status: done}
- {id: p1-3-integrate-openapi-script, content: '- [x] [AGENT] P1. Integrate the snapshot generation into the existing `generate-unified-openapi.sh` pipeline so it runs as part of the "Generating UI Reference Data" step. Add it as step 7 after the current 6 steps. The snapshot should be synced to UI repos alongside the other artifacts.

    ', status: done}
- {id: p1-4-ui-registry-permanent, content: '- [x] [AGENT] P0. Copy the instruments-snapshot.json into `unified-trading-system-ui/lib/registry/instruments-snapshot.json` (NOT in .local-dev-cache, NOT git-ignored — this is permanent reference data, a few MB is fine). Create `unified-trading-system-ui/lib/registry/instruments.ts` that exports typed instrument data from this JSON: by venue, by category, by instrument type. Include helper functions: `getInstrumentsByVenue(venue)`, `getInstrumentsByCategory(category)`, `getVenuesWithInstruments()`, `getSportsFixtures()`, `getInstrumentsByDate(date)`. The full dataset is ~13,000+ instruments — the UI must handle grouping/filtering/virtualization at this scale (per day, per category, per venue, per instrument type).

    ', status: done}
- {id: p1-5-market-data-assumption, content: '- [x] [AGENT] P1. Added `hasMarketData: true` to all 23,071 instruments in both UAC and UI snapshot JSONs. Updated generate_instrument_snapshot.py to set the flag during generation. Added `hasMarketData: boolean` to the Instrument interface in instruments.ts.

    ', status: done}
- {id: p1-6-enhance-openapi-reference, content: '- [x] [AGENT] P1. Audited ui-reference-data.json and added 5 missing extraction steps to generate_ui_reference_data.py: (7) 32 strategy configs from system-topology.json, (8) 13 execution algos + 5 book types + 9 instruction types from UAC trading_validation, (9) 81 sports bookmakers from UAC bookmaker_registry, (10) 14 DeFi protocols + 13 venue mappings + 7 Solana protocols from UAC defi_protocol_registry, (11) 24 TradFi exchange session calendars from UAC session_times. Regenerated and synced to both UAC and UI.

    ', status: done}
- {id: p1-7-tests, content: "- [x] [AGENT] P0. Add tests: (1) snapshot generation script produces valid JSON with expected structure, (2) all 5 asset classes represented, (3) venue names match VENUE_CATEGORY_MAP in ui-reference-data.json, (4) instruments.ts exports compile without errors, (5) snapshot contains 10,000+ instruments (no artificial limits). Run QG on unified-trading-pm and unified-trading-system-ui.\n  **Result (2026-04-02):** OpenAPI generator runs clean (25/25 services, 345 paths, 88 schemas). Instrument snapshot (23K instruments) integrated into pipeline step 7. Per-repo QG deferred to CI.\n", status: done}
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

### Problem

The frontend mocks use ~20 hardcoded instruments with inconsistent venue naming (title case vs UPPERCASE). Meanwhile,
instruments-service has 13,386 real instruments from March 26-27 in 404 CSV files, UAC has representative_sample.py,
team_mapping.csv (6,245 teams), league_registry.py, and e2e-testing has live arb snapshots with real sports fixtures.
None of this real data feeds into the UI.

### Architecture Decision

The instrument snapshot is a **permanent** file in `lib/registry/` — not cached, not git-ignored. It represents "one day
of real data" (March 27, 2026) that the frontend uses as its SSOT for what instruments exist. Market data availability
is assumed for all instruments in the snapshot — the mock layer generates synthetic data.

### Execution DAG

```
Phase 1 (PARALLEL):
  p1-1: Snapshot script (instruments CSV → JSON)
  p1-2: Sports fixtures (live_arb + team_mapping → canonical sports instruments)

Phase 2 (SEQUENTIAL, depends on Phase 1):
  p1-3: Integrate into OpenAPI generate pipeline
  p1-4: Copy to UI registry + TypeScript exports
  p1-5: Market data assumption flag
  p1-6: Enhance reference data extraction

Phase 3 (SEQUENTIAL, depends on Phase 2):
  p1-7: Tests + QG validation
```

### Success Criteria

- **C2**: Snapshot JSON contains 500+ instruments across all 5 categories; tests pass
- **C3**: basedpyright + ruff clean on PM scripts; TypeScript compiles on UI
- **C4**: QG pass on unified-trading-pm, unified-trading-system-ui
- **C5**: Quickmerged to staging
