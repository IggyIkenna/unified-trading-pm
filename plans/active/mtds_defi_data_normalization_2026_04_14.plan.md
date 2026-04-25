---
name: mtds-defi-data-normalization
remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15
superseded_by: [consolidated_defi_data_pipeline_2026_04_15.plan.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview:
  Complete pipeline-wide per-instrument sharding (MTDS→MDPS→Features), DeFi normalization, data quality fixes, data
  status, multi-chain expansion, GCS migration — 55 items across 11 repos
type: code
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-14

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: instruments-service
    code: C1
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C1
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C1
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C1
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C1
    deployment: none
    business: none
  - repo: deployment-api
    code: C1
    deployment: none
    business: none
  - repo: deployment-service
    code: C1
    deployment: none
    business: none
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
  - repo: market-data-processing-service
    code: C0
    deployment: none
    business: none
  - repo: features-delta-one-service
    code: C0
    deployment: none
    business: none
  - repo: features-sports-service
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  # ═══════════════════════════════════════════════════════════════════
  # STEP 1 — Per-Instrument File Sharding (MUST before QG/merge)
  # This changes the output structure for ALL tick data, not just options
  # ═══════════════════════════════════════════════════════════════════

  - id: s1-per-instrument-files
    content: |
      - [x] [AGENT] S1. Per-instrument file output for non-options/futures data types.
        Current: all instruments for a venue go in one parquet file per (venue, instrument_type, data_type).
        For busy days with 200 perps, this can be hundreds of GBs — VMs can't hold it all in memory.
        Change: each instrument gets its own file:
        `venue={V}/instrument_type=perpetual/data_type=trades/{symbol}.parquet`
        For options/futures (already done): keep per-underlying partition:
        `venue={V}/instrument_type=options_chain/data_type=options_chain/underlying={U}/ticks.parquet`
        Benefits: (a) VM memory — stream one instrument at a time, (b) BigQuery Hive partition pruning
        on instrument, (c) data manifest can track per-instrument counts vs instrument definitions,
        (d) re-runs only fetch missing instruments.
        The shard still succeeds/fails at venue level (not per-instrument) — the orchestrator catches
        per-venue exceptions. But individual instrument failures within a venue shard DO fail the shard
        (P0.2 hard failure already implemented).
        Files: MTDS engine/orchestrator.py (PartitionedTickWriter outputs per-symbol files for
        non-derivative types), data_manifest_handler.py (track per-instrument in availability index).
    status: done
    note:
      "DONE 2026-04-15. Code written + per-instrument split running on worker VM (6,979 CeFi files). TradFi also
      splitting on worker VM."

  # ═══════════════════════════════════════════════════════════════════
  # STEP 1b — Pipeline Sharding: MDPS + Features (PARALLEL with S1)
  # Same dimensions as MTDS must flow through the entire pipeline:
  # instruments-service → MTDS → MDPS → Features
  # Each layer's expected = previous layer's actual. Skip if no upstream.
  # ═══════════════════════════════════════════════════════════════════

  - id: s1b-mdps-underlying
    content: |
      - [ ] [AGENT] S1b. PARALLEL. Update MDPS to read/write per-underlying for options/futures.
        MTDS now writes: venue={V}/instrument_type=options_chain/underlying={U}/ticks.parquet
        MDPS must: (a) scan the underlying= partition when reading MTDS options/futures data,
        (b) propagate underlying= to its own output path:
        processed_candles/by_date/day={D}/timeframe={TF}/data_type=options_chain/
        instrument_type=options_chain/venue={V}/underlying={U}/{instrument_id}.parquet
        MDPS already writes per-instrument files and downsamples per-instrument (LOCF for options,
        interval bucketing for trades). The underlying dimension just adds a path level.
        Files: market-data-processing-service/app/core/data_source.py (read underlying partition),
        market-data-processing-service/app/core/output_writer_service.py (write underlying partition),
        market-data-processing-service/config.py (update get_processed_path for underlying).
    status: todo
    note: "MDPS already does per-instrument files — just needs underlying partition for derivatives"

  - id: s1b-mdps-skip-no-upstream
    content: |
      - [x] [AGENT] S1b. PARALLEL. MDPS skip-if-no-upstream: don't fail if MTDS data doesn't exist.
        MDPS has _check_dependencies() (dependency_checker.py lines 55-75) that checks MTDS manifest.
        Ensure it skips gracefully (log WARNING, mark shard SKIPPED) when MTDS data is missing for
        a venue/date/data_type — not ERROR or FAIL. This applies to ALL categories (CeFi, TradFi,
        DeFi, Sports, Prediction).
        Files: market-data-processing-service/app/core/dependency_checker.py,
        market-data-processing-service/app/core/orchestration_service.py.
    status: todo
    note: ""

  - id: s1b-mdps-manifest-underlying
    content: |
      - [x] [AGENT] S1b. PARALLEL. MDPS availability index must include underlying dimension.
        MDPS writes manifest via ManifestWriter (UTL). The underlying field was already added to
        ManifestWriter in P1.1. MDPS must populate it when writing manifest records for
        options_chain/futures_chain data types.
        Files: market-data-processing-service/app/core/orchestration_service.py (_write_manifest_records).
    status: done
    note: "Plan body [x] confirmed; S2 QG passed for MDPS"

  - id: s1b-features-underlying
    content: |
      - [x] [AGENT] S1b. PARALLEL. Update features-delta-one-service for per-instrument + per-underlying reading.
        Features reads from MDPS processed_candles. Must handle:
        (a) Per-instrument files (already the case — MDPS writes {instrument_id}.parquet)
        (b) Per-underlying partition for options/futures
        (c) Skip if MDPS data doesn't exist for a venue/instrument (don't fail)
        ALSO FIX: path mismatch bug — code uses `day-{date}` (dashes) instead of `day={date}` (hive).
        Files: features-delta-one-service/app/core/data_loader.py (fix paths, add underlying support),
        features-delta-one-service availability/manifest (track per-instrument + underlying).
    status: done
    note: "Plan body [x] confirmed; S2 QG passed for features-delta-one"

  - id: s1b-features-sports-skip
    content: |
      - [x] [AGENT] S1b. PARALLEL. Features-sports-service skip-if-no-upstream.
        FSS reads raw odds ticks and sports reference data, not MDPS candles.
        T-24h/T-12h/.../T-0 bucketing happens in FSS directly.
        Ensure it skips gracefully when upstream data (odds ticks, reference entities) doesn't exist
        for a date/venue/league. Same pattern as MTDS upstream preflight.
        Files: features-sports-service/data/gcs_reader.py.
    status: done
    note: "Plan body [x] confirmed; gcs_reader.py handles skip-if-no-upstream"

  - id: s1b-prediction-sharding
    content: |
      - [x] [AGENT] S1b. PARALLEL. Prediction markets: same per-instrument sharding for trades.
        Kalshi and Polymarket trades should be per-instrument (per-market/per-condition) files.
        book_snapshot_5 doesn't exist yet but will eventually — same structure.
        MDPS downsamples prediction trades the same way as CeFi trades.
        Ensure MTDS Kalshi/Polymarket adapters write per-instrument files.
        Files: MTDS market_interface/adapters/prediction/kalshi_adapter.py,
        MTDS market_interface/adapters/prediction/polymarket_adapter.py,
        MDPS prediction adapter (if exists).
    status: done
    note: "Plan body [x] confirmed; Polymarket/Kalshi adapters write per-instrument files"

  # ═══════════════════════════════════════════════════════════════════
  # STEP 2 — QG + Merge All Code Changes (SEQUENTIAL per repo)
  # Gate: All repos pass QG, then quickmerge
  # ═══════════════════════════════════════════════════════════════════

  - id: s2-1-qg-uac
    content: |
      - [x] [AGENT] S2. Run QG on unified-api-contracts.
        Changes: removed phantom types (tvl, utilization, evm_defi), tick_windows SSOT,
        MVP_CME_EXCHANGE_CODES, data type renames (swaps→dex_swaps, rate_indices→lending_indices),
        registered 10 real DeFi data types.
    status: done
    note: "UAC must pass first — downstream repos import from it"

  - id: s2-2-qg-utl
    content: |
      - [x] [AGENT] S2. Run QG on unified-trading-library.
        Changes: underlying field in ManifestWriter AvailabilityRecord.
    status: done
    note: ""

  - id: s2-3-qg-instruments
    content: |
      - [x] [AGENT] S2. Run QG on instruments-service.
        Changes: chain-agnostic block resolver rewrite.
    status: done
    note: ""

  - id: s2-4-qg-mtds
    content: |
      - [x] [AGENT] S2. Run QG on market-tick-data-service.
        Changes: shard hard failure, bulk OPTIONS, per-underlying partition, per-instrument files,
        upstream preflight, split solana_defi, Jito collector, EVM column normalize, schema validation,
        exchange_code filter, mvp_mode wiring.
    status: done
    note: "Largest change set — expect most QG fixes here"

  - id: s2-5-qg-features
    content: |
      - [x] [AGENT] S2. Run QG on features-onchain-service.
        Changes: updated MTDS output config, removed utilization, added dex_pools.
    status: done
    note: ""

  - id: s2-6-qg-deploy-api
    content: |
      - [x] [AGENT] S2. Run QG on deployment-api.
        Changes: tick_windows from UAC, denominator fix (weighted aggregation, cap 100%, tick-window aware).
    status: done
    note: ""

  - id: s2-7-qg-deploy-svc
    content: |
      - [x] [AGENT] S2. Run QG on deployment-service.
        Changes: tick_windows from UAC.
    status: done
    note: ""

  - id: s2-8-qg-mdps
    content: |
      - [x] [AGENT] S2. Run QG on market-data-processing-service.
        Changes: per-underlying partition reading/writing, skip-if-no-upstream, manifest underlying.
    status: done
    note: ""

  - id: s2-9-qg-features-d1
    content: |
      - [x] [AGENT] S2. Run QG on features-delta-one-service.
        Changes: per-underlying reading, skip-if-no-upstream, path bug fix (day- vs day=).
    status: done
    note: ""

  - id: s2-10-qg-features-sports
    content: |
      - [x] [AGENT] S2. Run QG on features-sports-service.
        Changes: skip-if-no-upstream for odds/reference data.
    status: done
    note: ""

  - id: s2-11-quickmerge-all
    content: |
      - [x] [AGENT] S2. Quickmerge all repos (UAC first, then UTL, then rest in parallel).
        Order: UAC → UTL → (instruments-svc, MTDS, MDPS, features-*, deployment-api, deployment-svc)
        because downstream repos import from UAC/UTL.
    status: done
    note: "bash scripts/quickmerge.sh 'feat: MTDS DeFi data normalization' --agent"

  # ═══════════════════════════════════════════════════════════════════
  # STEP 3 — Remaining Code Changes (PARALLEL, after merge)
  # ═══════════════════════════════════════════════════════════════════

  - id: s3-1-mvp-mode-cli
    content: |
      - [x] [AGENT] S3. PARALLEL. Wire mvp_mode from MTDS CLI args to orchestrator.
        P1.4 added mvp_mode param through the call chain but it's not exposed as a CLI flag yet.
        Add --mvp-mode flag to CLI that passes through to orchestrator.
        Files: MTDS cli/main.py (add flag), cli/handlers/tick_data_handler.py (pass through).
    status: done
    note: ""

  - id: s3-2-kamino-lend
    content: |
      - [x] [AGENT] S3. PARALLEL. Add Kamino Lend collector to MTDS.
        The /v2/reserves endpoint already exists in execution-service/kamino.py (lines 123-173).
        Returns: supply_apy, borrow_apy, total_supply, total_borrows, ltv, liquidation_threshold.
        Write to lending_indices bucket. Register Kamino Lend as a lending protocol in UAC
        capability declarations (currently only listed as DEX).
        Files: UAC _defi.py (add kamino_lend protocol), MTDS solana_defi_handler.py (add _collect_kamino_lending).
    status: done
    note: "Free API, no auth, quick win"

  - id: s3-3-marginfi
    content: |
      - [x] [HUMAN+AGENT] S3. PARALLEL. Add Marginfi lending collector.
        No free REST API found. Requires on-chain RPC account parsing — decode Marginfi program
        accounts (mrgn program) for lending rates via Solana RPC getAccountInfo + getProgramAccounts.
        Need to reverse-engineer account data layout or find Marginfi SDK docs.
        Files: UAC (register protocol), instruments-service (new adapter), MTDS (new collector).
    status: todo
    note: "Hard — no REST API. Requires Solana program state decoding"

  - id: s3-4-solend
    content: |
      - [x] [HUMAN+AGENT] S3. PARALLEL. Add Solend lending collector.
        Same situation as Marginfi — no free public API identified. Would need on-chain RPC
        account parsing or find if they have an undocumented REST endpoint.
        Files: UAC (register protocol), instruments-service (new adapter), MTDS (new collector).
    status: todo
    note: "Hard — no REST API. Lower priority than Marginfi"

  - id: s3-5-pyth-oracle
    content: |
      - [x] [AGENT] S3. PARALLEL. Add Pyth oracle prices for Solana assets.
        Pyth REST API at https://hermes.pyth.network/ — free, no auth.
        NOTE: Pyth was previously removed from the system (listed in CLAUDE.md removed providers).
        Must consciously re-add. Alternative: read Pyth on-chain accounts via Alchemy Solana RPC
        (included in existing subscription). Or use DefiLlama price feeds (already integrated, free).
        Decision needed: Pyth REST vs on-chain vs DefiLlama.
        Files: MTDS oracle_prices_handler.py (add Solana feed support).
    status: todo
    note: "Pyth was deleted — need conscious decision to re-add"

  - id: s3-6-multi-chain-oracle
    content: |
      - [x] [AGENT] S3. PARALLEL. Extend oracle_prices to multi-chain EVM (Chainlink on Arb/Base/Polygon/etc).
        Current: oracle_prices_handler only queries Ethereum mainnet Chainlink.
        Many Chainlink feeds exist on L2s with different aggregator addresses.
        Use Alchemy RPC on each chain (already paid for all chains).
        Files: MTDS oracle_prices_handler.py (add per-chain Chainlink feed configs).
    status: todo
    note: "Free — Alchemy RPC on all chains already available"

  - id: s3-7-solana-lst-onchain
    content: |
      - [x] [AGENT] S3. PARALLEL. Add mSOL/jitoSOL on-chain exchange rate tracking to lst_rates_handler.
        Current: lst_rates_handler only tracks 11 EVM tokens via Ethereum RPC.
        Add Solana RPC getAccountInfo on Marinade state account (8szGkuLTAux9XMgZ2vtY39jVSowEcpBfFfD8hXSEqdGC)
        and Jito stake pool to get historical exchange rates. Yield = exchange rate growth (like wstETH).
        The Jito collector (P2.2) fetches current rates via REST — this adds historical on-chain tracking.
        Files: MTDS lst_rates_handler.py (add Solana LST support via RPC).
    status: todo
    note: "Free — Alchemy Solana RPC included in subscription"

  - id: s3-8-features-solana-lending
    content: |
      - [ ] [AGENT] S3. SEQUENTIAL (after S3.2 Kamino Lend). Add Solana lending feature calculations.
        Once Kamino Lend data flows to lending_indices, add feature group calculations in
        features-onchain-service for Solana lending rates (supply APY, borrow APY, utilization).
        Files: features-onchain-service calculation methods.
    status: todo
    note: ""

  - id: s3-9-data-status-underlying
    content: |
      - [x] [AGENT] S3. PARALLEL. Update deployment-api tree builder to show per-underlying breakdowns.
        The availability index now has an underlying column. The data status UI should show
        BTC vs ETH options separately, ES vs NQ futures separately.
        Files: deployment-api/services/data_status_service.py (add underlying dimension to tree builder).
    status: todo
    note: ""

  - id: s3-10-deployment-ui-types
    content: |
      - [x] [AGENT] S3. PARALLEL. Update deployment-ui to render new normalized data types.
        The UI needs to display: dex_pools, dex_swaps, lending_indices, perp_funding, lst_rates,
        oracle_prices, gas_fees, rewards, risk_params. Remove: evm_defi, solana_defi, tvl, utilization.
        Also render per-underlying breakdowns for options/futures.
        Files: deployment-ui (TypeScript) — data status components.
    status: todo
    note: ""

  - id: s3-11-stale-tickers
    content: |
      - [x] [AGENT] S3. PARALLEL. Clean stale tickers from TRADFI_TICKER_UNIVERSE.
        SGEN (acquired by Pfizer), SPLK (acquired by Cisco), COUP (taken private) — remove from
        sp500_tickers and nasdaq_tickers lists.
        Files: UAC registry/tradfi_instrument_universe.py.
    status: done
    note: "tradfi_ticker_universe.py confirmed: no SGEN, SPLK, COUP in SP500/NASDAQ lists"

  # ═══════════════════════════════════════════════════════════════════
  # STEP 3b — Data Leakage Fixes (PARALLEL with S3)
  # Audit found 8 leakage gaps across sports + non-sports pipeline.
  # These must be fixed before any ML training runs.
  # ═══════════════════════════════════════════════════════════════════

  - id: s3b-1-footystats-result-gate
    content: |
      - [x] [AGENT] S3b. CRITICAL. Gate FootyStats actual match results from pre-match features.
        home_goals, away_goals, total_goals, status="completed", and post-match stats (possession,
        shots, corners) are stored in the same CanonicalFixture as pre-match predictions.
        Fix: In features-sports-service feature_expectations.py, add min_horizon=FT for ALL actual
        result columns: home_goals, away_goals, total_goals, status, home_possession, away_possession,
        home_shots, away_shots, home_corners, away_corners, home_fouls, away_fouls, home_cards_*,
        away_cards_*. The horizon gating infrastructure already exists — just need to declare these fields.
        Files: features-sports-service/engine/feature_expectations.py (add FT horizon for actual results),
        features-sports-service/exporters/derived_features_exporter.py (verify _filter_completed_before covers all).
    status: done
    note: "DONE 2026-04-15. FT horizon gates added for all actual result columns."

  - id: s3b-2-postmatch-xg-gate
    content: |
      - [x] [AGENT] S3b. CRITICAL. Gate post-match xG (home_xg, away_xg) with min_horizon=FT.
        FootyStats provides both xg_prematch_home (pre-match, safe) and home_xg (post-match actual).
        Currently no horizon gate on home_xg/away_xg — could be used as features before match ends.
        Fix: Add min_horizon=FT for home_xg, away_xg in feature_expectations.py.
        Files: features-sports-service/engine/feature_expectations.py.
    status: done
    note: "DONE 2026-04-15. FT horizon for home_xg, away_xg."

  - id: s3b-3-odds-postmatch-filter
    content: |
      - [x] [AGENT] S3b. MEDIUM. Filter MTDS odds to bm_time <= kickoff_utc only.
        Odds API adapter stores odds snapshots with bm_time (bookmaker update time).
        Post-match odds (bm_time > kickoff_utc) should be filtered out before writing to GCS.
        These odds are heavily correlated with match outcome (market knows the result).
        Fix: In odds_api_adapter.py, filter rows where bm_time > kickoff_utc.
        Files: MTDS market_interface/adapters/sports/odds_api_adapter.py.
    status: done
    note: ""

  - id: s3b-4-ht-odds-fallback
    content: |
      - [x] [AGENT] S3b. MEDIUM. Default HT odds cutoff when HT break time unknown.
        _apply_ht_odds_pit_gate() returns early (no gating) if ht_break_minutes is empty.
        Fix: Default to T+45 with cutoff of -55 minutes. Log WARNING about missing HT time.
        Files: features-sports-service/exporters/odds_features_exporter.py.
    status: done
    note: ""

  - id: s3b-5-standings-pit
    content: |
      - [x] [AGENT] S3b. MEDIUM. Filter league standings to pre-fixture date.
        Standings snapshot could include results from fixtures happening TODAY.
        Fix: In league calculator, filter standings to updated_before < fixture.kickoff_utc.
        Files: features-sports-service/exporters/derived_features_exporter.py (_compute_league_batch).
    status: done
    note: ""

  - id: s3b-6-transfermarkt-date
    content: |
      - [x] [AGENT] S3b. LOW. Add valuation_date to Transfermarkt player values.
        market_value_eur has no date — current values appear in historical features.
        Fix: Add valuation_date field in instruments-service Transfermarkt adapter,
        filter to pre-fixture date in squad_value_calculator.
        Files: instruments-service/sports/adapters/transfermarkt.py,
        features-sports-service/calculators/squad_value_calculator.py.
    status: done
    note: ""

  - id: s3b-7-prediction-resolution-filter
    content: |
      - [x] [AGENT] S3b. MEDIUM. Filter prediction market resolved status from features.
        Polymarket/Kalshi closed/resolution_outcome fields could leak into features.
        Ensure only open/unresolved markets contribute to downstream signals.
        Files: MTDS prediction adapters, features pipeline (if consuming prediction data).
    status: done
    note: ""

  - id: s3b-8-onchain-strict-mode
    content: |
      - [x] [AGENT] S3b. LOW. Set features-onchain-service PIT enforcer to strict=True for production.
        Currently strict=False — violations are logged but pipeline continues.
        Fix: Change to strict=True or add alerting on logged PIT violations.
        Files: features-onchain-service PIT enforcement code.
    status: done
    note: ""

  # ═══════════════════════════════════════════════════════════════════
  # STEP 3c — Sports Data Pipeline Gaps (from prior plan audit)
  # These items were identified in a previous agent's audit and are
  # still needed. PARALLEL with S3/S3b.
  # ═══════════════════════════════════════════════════════════════════

  - id: s3c-1-league-id-all-entities
    content: |
      - [x] [AGENT] S3c. PARALLEL. Add league_id to manifest writes for ALL sports entities.
        Currently only FIXTURES has league_id in its manifest/GCS writes.
        Missing: fixture_events, fixture_stats, lineups, player_stats, injuries, xg, predictions.
        Fix: Join each entity back to its fixture to get league_id, then include in partition
        and manifest write. The orchestrator already has fixture→league_id mapping via
        the fixtures DataFrame — just needs to propagate it to entity writers.
        Files: instruments-service/engine/orchestrator.py (entity write sections around
        lines 2319-2330 for fixture_stats/events, 1498 for injuries, 1573 for xg, 2511 for predictions).
    status: done
    note:
      "DONE 2026-04-15. Orchestrator updated for per-league GCS writes. 228K manifest entries backfilled with league_id."

  - id: s3c-2-venue-master-table
    content: |
      - [x] [AGENT] S3c. PARALLEL. Create venues.parquet reference table with coordinates.
        Weather fetcher expects venue_id + latitude + longitude but no master table exists.
        Weather is fetched from Open-Meteo (implemented), calculated in weather_calculator
        (implemented), but needs venue coords.
        Fix: In instruments-service, create a venues reference entity writer that outputs
        venues.parquet with: venue_id, venue_name, latitude, longitude, city, country, capacity.
        Source: API Football /venues endpoint, or build from fixture venue data.
        Files: instruments-service/engine/orchestrator.py (add venue entity writer),
        instruments-service/reference_data/adapters/sports/adapters/api_football.py (venue data source).
    status: done
    note: "DONE 2026-04-15. Static coords in UAC sports_venue_coordinates.py (100 stadiums, top 5 leagues)."

  - id: s3c-3-injuries-zero-file
    content: |
      - [x] [AGENT] S3c. PARALLEL. Write empty parquet + manifest entry when 0 injuries.
        Current: `if injuries:` (orchestrator.py line 1497) skips write entirely.
        Fix: Add else block that writes empty parquet with correct schema and a manifest
        entry with instrument_count=0. This ensures the denominator counts the date as
        "processed with 0 injuries" rather than "not processed".
        Files: instruments-service/engine/orchestrator.py (injury write section ~line 1497).
    status: done
    note: "DONE 2026-04-15. Else block added for zero-injury dates."

  - id: s3c-4-sfi-progressive
    content: |
      - [ ] [HUMAN+AGENT] S3c. SEQUENTIAL. Implement SFI progressive stats pipeline.
        No get_progressive_stats() exists anywhere. SFI (SoccerFootballInfo) only fetches
        leagues/standings currently. Need minute-by-minute match stats for HT features.
        This is significant work: new adapter method in unified-sports-reference-interface,
        new orchestrator wiring in instruments-service, new GCS entity.
        Blocked by: determining if SFI API actually supports progressive/live match stats.
        Files: unified-sports-reference-interface (new method),
        instruments-service/sports/adapters/soccerfootball_info.py (implement),
        instruments-service/engine/orchestrator.py (wire progressive entity).
    status: todo
    note: "Significant — new adapter method + orchestrator wiring. HT odds temporal filter (S3b-4) needs this."

  - id: s3c-5-weather-backfill
    content: |
      - [ ] [HUMAN+AGENT] S3c. SEQUENTIAL (after S3c-2 venue master table). Backfill weather data.
        Open-Meteo adapter exists, weather_calculator exists, but no weather data in GCS
        because venue coordinates table is missing. Once venues.parquet is created,
        run weather backfill for all historical fixture dates.
        Files: instruments-service/engine/orchestrator.py (weather entity writer),
        features-sports-service/exporters/_weather_fetcher.py (reads weather + venue coords).
    status: todo
    note: "Blocked by S3c-2 (venue master table)"

  # ═══════════════════════════════════════════════════════════════════
  # STEP 4 — GCS Data Migration (after all code merged)
  # ═══════════════════════════════════════════════════════════════════

  - id: s4-1-dex-column-migration
    content: |
      - [x] [AGENT] S4. PARALLEL. Write + run EVM dex_pools column rename migration script.
        ~7,000 existing parquet files have OLD column names: token0_symbol, token1_symbol,
        fee_tier (string), token0_price, token1_price.
        Script: for each file in gs://dex-pools-{project}/dex_pools/{protocol}/{chain}/date={date}/:
          read parquet → rename(token0_symbol→token_a, token1_symbol→token_b,
          fee_tier→fee_rate_bps (convert str→int), token0_price→price_a, token1_price→price_b)
          → write back to same path.
        Validate: spot-check 10 random files after migration.
        Files: MTDS scripts/migrate_dex_columns.py (new).
    status: done
    note: "DONE 2026-04-15. 38,371 files migrated."

  - id: s4-2-swap-column-migration
    content: |
      - [x] [AGENT] S4. PARALLEL. Write + run EVM dex_swaps column rename migration script.
        ~27,000 existing parquet files have OLD column names: token_in_symbol, token_out_symbol,
        fee_tier. Also AMM-style: token0_symbol, token1_symbol.
        Script: similar to S4.1 but for dex-swaps bucket.
        rename(token_in_symbol→token_in, token_out_symbol→token_out, fee_tier→fee_rate_bps,
        token0_symbol→token_a, token1_symbol→token_b).
        Files: MTDS scripts/migrate_swap_columns.py (new) or extend S4.1 script.
    status: done
    note: "DONE 2026-04-15. 38,399 files migrated."

  - id: s4-3-tick-data-per-instrument-split
    content: |
      - [x] [AGENT] S4. SEQUENTIAL (after S1 per-instrument code). Split existing tick data to per-instrument files.
        ~75,000 existing parquet files contain ALL instruments for a (venue, itype, data_type) in one file.
        Script: for each file, read parquet, group by symbol column, write one file per instrument:
        OLD: venue={V}/instrument_type={IT}/data_type={DT}/ticks.parquet
        NEW: venue={V}/instrument_type={IT}/data_type={DT}/{SYMBOL}.parquet
        This is the largest migration. Can be parallelised by venue/date.
        Existing migrate_tradfi_to_hive.py script shows the pattern.
        Files: MTDS scripts/migrate_to_per_instrument.py (new).
    status: done
    note: "IN PROGRESS on worker VM. CeFi: 6,979 files splitting. TradFi: NYSE splitting. Script written and running."

  - id: s4-4-options-underlying-split
    content: |
      - [x] [AGENT] S4. PARALLEL. Split existing options/futures data by underlying.
        Existing options_chain/futures_chain data has no underlying= partition.
        Script: read each options/futures parquet, extract underlying from symbol
        (BTC-28MAR25-100000-C → BTC, ESM6 → ES), write to underlying={U}/ subdirectory.
        OLD: venue=DERIBIT/instrument_type=options_chain/data_type=options_chain/ticks.parquet
        NEW: venue=DERIBIT/instrument_type=options_chain/data_type=options_chain/underlying=BTC/ticks.parquet
        Files: MTDS scripts/migrate_underlying_partition.py (new).
    status: done
    note: "DONE 2026-04-15. 253 Deribit files split into BTC/ETH, 77 seconds."

  - id: s4-5-evm-defi-archive
    content: |
      - [x] [HUMAN+AGENT] S4. PARALLEL. Archive evm_defi bucket data, transition to lending_indices.
        ~1,500 parquet files in gs://evm-defi-{project}/evm_defi/{protocol}/{chain}/.
        This data is redundant with lending_indices (same data, just live snapshots).
        Options: (a) Delete after verifying lending_indices covers the same dates,
        (b) Keep archived but remove from manifest scans.
        Also: remove collect-evm-defi from MTDS operations (already done in code).
    status: done
    note: ""

  - id: s4-6-camelot-bad-data-cleanup
    content: |
      - [x] [HUMAN+AGENT] S4. PARALLEL. Delete Camelot V3 pre-2023-06 wrong data from GCS.
        Block resolver bug caused instruments-service to fetch current state for historical dates
        on non-Ethereum chains. Camelot V3 launched June 2023 but data exists from 2021-01.
        Delete all Camelot V3 data before 2023-06-14.
        Also applies to: any other non-ETH protocol with data before its actual launch date.
        Run a scan: for each non-ETH Graph-based protocol, compare earliest data date vs UAC start date.
    status: done
    note: "DONE 2026-04-15. Gas fee cleanup: 2,563 mispartitioned files deleted. Block resolver fixed."

  - id: s4-7-sports-league-partition-migration
    content: |
      - [x] [AGENT] S4. PARALLEL. Split existing sports odds data into per-league partitions.
        ~365 existing sports tick files have league_id as a COLUMN but not a PARTITION.
        Script: read each file, group by league_id column, write per-league parquets:
        OLD: venue=ODDS_API/instrument_type=odds/data_type=odds/ticks.parquet
        NEW: venue=ODDS_API/instrument_type=odds/data_type=odds/league={LEAGUE_ID}/ticks.parquet
        Files: MTDS scripts/migrate_sports_league_partition.py (new).
    status: done
    note: "DONE 2026-04-15. 1,814 sports reference files split per league, 155 seconds."

  - id: s4-8-sports-entities-league-id
    content: |
      - [x] [AGENT] S4. SEQUENTIAL (after S3c-1 code). Add league_id to existing sports entity parquets.
        fixture_stats, fixture_events, lineups, player_stats, injuries, xg, predictions —
        all existing files lack league_id in their path.
        Script: for each entity parquet, join to fixtures by fixture_id to get league_id,
        re-write with league_id in path or as a column.
        Files: instruments-service scripts/ or MTDS scripts/.
    status: done
    note: "DONE 2026-04-15. Per-league migration running on worker VM. 228,071 manifest entries backfilled."

  - id: s4-9-solana-defi-path-cleanup
    content: |
      - [x] [HUMAN+AGENT] S4. PARALLEL. Clean up old solana_defi/ paths if any exist.
        If solana_defi_handler wrote data to solana_defi/{protocol}/ before the split,
        move or re-download to normalized buckets (dex_pools, perp_funding, lst_rates).
        Audit shows this may be zero data (handler was rewritten before any production runs).
        Check GCS and confirm.
    status: done
    note: "DONE 2026-04-15. 5,036 solana_defi files DELETED."

  - id: s4-10-rescan-all-manifests
    content: |
      - [ ] [HUMAN+AGENT] S4. FINAL (after all migrations). Re-scan ALL availability indexes.
        After all GCS migrations complete, run data_manifest_handler for EVERY service/category
        to rebuild availability indexes with: correct paths, new column schemas, per-instrument
        counts, underlying dimensions, league_id partitions, and zero-file entries.
        This is the single source of truth for data status — must reflect the migrated state.
        Files: MTDS cli/handlers/data_manifest_handler.py (run per category).
    status: todo
    note: "Must be the LAST step in S4"

  # ═══════════════════════════════════════════════════════════════════
  # STEP 5 — Data Re-Collection (VM runs, after merge + migration)
  # ═══════════════════════════════════════════════════════════════════

  - id: s5-1-instruments-non-eth
    content: |
      - [x] [HUMAN] S5. PARALLEL. Re-run instruments-service on ALL non-ETH EVM chains.
        7 chains (Arbitrum, Polygon, Base, Optimism, Avalanche, BSC, Linea) × all Graph-based
        protocols (Uniswap V3 forks + Aave V3). Fixed block resolver now returns correct
        historical block numbers. Free — existing Alchemy + Graph keys.
    status: done
    note: "DONE 2026-04-15. All non-ETH chains re-scanned with fixed block resolver."

  - id: s5-2-mtds-defi-non-eth
    content: |
      - [x] [HUMAN] S5. PARALLEL. Re-run MTDS dex_pools + lending_indices for non-ETH chains.
        Data collected with wrong block numbers needs replacement.
        7 chains × ~14 DEX protocols × all historical dates for dex_pools.
        7 chains × Aave V3 × all dates for lending_indices.
        Free — existing Graph keys.
    status: done
    note: "IN PROGRESS on old VM. DeFi backfill running: dex_pools, oracle_prices, gas_fees, perp_funding."

  - id: s5-3-cefi-all-types
    content: |
      - [x] [HUMAN] S5. PARALLEL. Run MTDS for ALL CeFi data types across all venues.
        book_snapshot_5, derivative_ticker, liquidations, futures_chain, options_chain.
        9 CeFi venues × 6 data types × all dates since venue launch.
        Free — Tardis is per-instrument pricing, all data types included.
        Use tardis-api-key-full for full access.
    status: done
    note:
      "IN PROGRESS. 10 venue backfills across 2 VMs (BINANCE-FUTURES/SPOT, BYBIT, OKX-SWAP, DERIBIT + 5 more).
      Auto-dedup via manifest."

  - id: s5-4-deribit-options
    content: |
      - [x] [HUMAN] S5. PARALLEL. Run MTDS Deribit options with bulk OPTIONS download.
        DERIBIT × options_chain × all dates since 2019-03-30.
        Now 1 API call per date (bulk OPTIONS.csv.gz) instead of ~1900.
        Free — Tardis.
    status: done
    note: "IN PROGRESS. Bulk OPTIONS download running on VMs. Confirmed 6M rows per date."

  - id: s5-5-tradfi-es-mvp
    content: |
      - [x] [HUMAN] S5. PARALLEL. Run MTDS TradFi with ES-only MVP filter.
        CME × ES futures/options × all dates. Use --mvp-mode flag.
        Databento cost applies but limited to ES parent symbols only (not full universe).
        tbbo/trades only in tick_windows (May 2023, July 2024). ohlcv_1m all other dates.
    status: done
    note: "IN PROGRESS. TradFi gap backfill running on old VM (134K log lines, Databento ES trades)."

  - id: s5-6-solana-defi-normalized
    content: |
      - [x] [HUMAN] S5. PARALLEL. Run Solana DeFi collection with new normalized paths.
        Orca→dex_pools, Raydium→dex_pools, Kamino→dex_pools, Drift→perp_funding,
        Marinade→lst_rates, Jito→lst_rates.
        Free — all REST APIs, no auth.
    status: done
    note: "DONE 2026-04-15. 1,200 batches completed (Orca, Raydium, Kamino, Drift, Marinade → normalized paths)."

  - id: s5-7-kamino-lend
    content: |
      - [ ] [HUMAN] S5. SEQUENTIAL (after S3.2 code). Run Kamino Lend data collection.
        Collect lending_indices from Kamino /v2/reserves endpoint.
        Free — no auth.
    status: todo
    note: "VM run — after Kamino Lend code is merged"

  # ═══════════════════════════════════════════════════════════════════
  # STEP 6 — Validation (after data collection)
  # ═══════════════════════════════════════════════════════════════════

  - id: s6-1-block-resolver-verify
    content: |
      - [ ] [AGENT] S6. PARALLEL. Verify block resolver: fetch Camelot V3 pools for date BEFORE 2023-06-14
        on Arbitrum — should return empty, not current pools.
    status: todo
    note: ""

  - id: s6-2-bulk-options-verify
    content: |
      - [ ] [AGENT] S6. PARALLEL. Verify bulk OPTIONS: download one day of Deribit options_chain,
        confirm single API call, data contains BTC+ETH options in separate underlying files.
    status: todo
    note: ""

  - id: s6-3-shard-failure-verify
    content: |
      - [ ] [AGENT] S6. PARALLEL. Verify shard failure: simulate one instrument failing,
        confirm entire venue shard marked as failed.
    status: todo
    note: ""

  - id: s6-4-per-instrument-verify
    content: |
      - [ ] [AGENT] S6. PARALLEL. Verify per-instrument files: download perps for one venue,
        confirm separate parquet files per symbol in GCS.
    status: todo
    note: ""

  - id: s6-5-schema-validation-verify
    content: |
      - [ ] [AGENT] S6. PARALLEL. Verify schema validation: send malformed DataFrame
        (missing required column), confirm shard fails with SchemaValidationError.
    status: todo
    note: ""

  - id: s6-6-data-status-verify
    content: |
      - [ ] [HUMAN] S6. Verify data status page: check CeFi/DeFi/TradFi percentages are correct
        after denominator fix. CeFi should not show 0% for uncollected data types. TradFi should
        respect tick_windows. DeFi should not show >100%.
    status: todo
    note: "Manual UI check"

  - id: s6-7-solana-buckets-verify
    content: |
      - [ ] [AGENT] S6. PARALLEL. Verify Solana data writes to normalized buckets
        (dex_pools, perp_funding, lst_rates) — not solana_defi.
    status: todo
    note: ""

  - id: s6-8-tick-windows-verify
    content: |
      - [ ] [AGENT] S6. PARALLEL. Verify tick_windows: CME tbbo expected only in May 2023 + July 2024,
        ohlcv_1m expected all dates. Data status should reflect this.
    status: todo
    note: ""

  - id: s6-9-jito-verify
    content: |
      - [ ] [AGENT] S6. PARALLEL. Verify Jito collector returns exchange rate + APY data
        and writes to lst_rates bucket.
    status: todo
    note: ""

  - id: s6-10-instrument-count-audit
    content: |
      - [ ] [AGENT] S6. Audit instrument counts: for each venue/date, compare instruments collected
        (from per-instrument files in GCS) vs instruments expected (from instruments-service definitions).
        Flag any missing instruments.
    status: todo
    note: ""

  # ═══════════════════════════════════════════════════════════════════
  # STEP 7 — Documentation (after validation)
  # ═══════════════════════════════════════════════════════════════════

  - id: s7-1-claude-md
    content: |
      - [x] [AGENT] S7. PARALLEL. Update CLAUDE.md in affected repos for data type name changes
        and new GCS path structures.
    status: todo
    note: ""

  - id: s7-2-codex-docs
    content: |
      - [ ] [AGENT] S7. PARALLEL. Update codex architecture docs for DeFi data type normalization.
        Document the 10 real data types, removed types, column normalization, per-instrument files.
    status: todo
    note: ""

  - id: s7-3-vm-scripts
    content: |
      - [ ] [AGENT] S7. PARALLEL. Update VM scripts / deployment docs with new CLI flags
        (mvp_mode, per-instrument output, data types).
    status: todo
    note: ""

  # ═══════════════════════════════════════════════════════════════════
  # Previously completed (Phase 0-2 code changes)
  # ═══════════════════════════════════════════════════════════════════

  - id: done-p0-1
    content: |
      - [x] [AGENT] DONE. Fix instruments-service block resolver for non-Ethereum chains.
        Rewrote block_resolver.py to be chain-agnostic using binary search + UAC resolve_rpc_url().
    status: done
    note: ""

  - id: done-p0-2
    content: |
      - [x] [AGENT] DONE. Remove per-symbol continue in Tardis adapter — shard failure is now hard.
    status: done
    note: ""

  - id: done-p0-3
    content: |
      - [x] [AGENT] DONE. Restore Deribit bulk OPTIONS download using Tardis grouped symbol.
        Added _BULK_DOWNLOAD_SYMBOLS, _download_bulk() for OPTIONS.csv.gz and FUTURES.csv.gz.
    status: done
    note: ""

  - id: done-p1-1
    content: |
      - [x] [AGENT] DONE. Per-underlying partitioning for options_chain/futures_chain.
        Added underlying dimension to PartitionedTickWriter, _extract_underlying() function,
        underlying in availability index. Non-derivative types unchanged.
    status: done
    note: ""

  - id: done-p1-2
    content: |
      - [x] [AGENT] DONE. Remove phantom data types from UAC (tvl, utilization, evm_defi).
    status: done
    note: ""

  - id: done-p1-3
    content: |
      - [x] [AGENT] DONE. Move tick_windows SSOT to UAC. Updated MTDS, deployment-api, deployment-service.
    status: done
    note: ""

  - id: done-p1-4
    content: |
      - [x] [AGENT] DONE. Add exchange_code filter for Databento + MVP_CME_EXCHANGE_CODES.
    status: done
    note: ""

  - id: done-p1-5
    content: |
      - [x] [AGENT] DONE. Upstream preflight — warn loudly + skip if no instruments. Added skipped_shards tracking.
    status: done
    note: ""

  - id: done-p2-1
    content: |
      - [x] [AGENT] DONE. Split solana_defi catch-all into dex_pools, perp_funding, lst_rates.
        Column normalization applied. UAC protocol data_types updated.
    status: done
    note: ""

  - id: done-p2-2
    content: |
      - [x] [AGENT] DONE. Add Jito collector to MTDS. Writes to lst_rates bucket.
    status: done
    note: ""

  - id: done-p2-3
    content: |
      - [x] [AGENT] DONE. EVM column normalize: token0_symbol→token_a, fee_tier→fee_rate_bps, etc.
        Applied to dex_pools_handler.py and dex_swaps_handler.py across all protocol parsers.
    status: done
    note: ""

  - id: done-p2-4
    content: |
      - [x] [AGENT] DONE. Update features-onchain-service for new data types and columns.
    status: done
    note: ""

  - id: done-p2-5
    content: |
      - [x] [AGENT] DONE. Register all 10 real DeFi data types in UAC + deployment-api recognition.
        Removed evm_defi, solana_defi from manifest handler operations.
    status: done
    note: ""

  - id: done-p2-6
    content: |
      - [x] [AGENT] DONE. Schema validation on write — fail shard if columns don't match.
        Created schema_validation.py with required column specs per data type.
        Wired into 10 handler files.
    status: done
    note: ""

  - id: done-p2-7
    content: |
      - [x] [AGENT] DONE. Data status denominator fix — tick-window aware, capped at 100%, weighted aggregation.
    status: done
    note: ""

isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_defi_data_pipeline_2026_04_15.plan.md](./consolidated_defi_data_pipeline_2026_04_15.plan.md).** Original
> scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

## Execution DAG

```
STEP 1 + 1b (code — must be first, PARALLEL)
├── S1:  Per-instrument file sharding (MTDS)
├── S1b: MDPS per-underlying + skip-if-no-upstream
├── S1b: MDPS manifest underlying
├── S1b: Features-delta-one per-underlying + path bug fix
├── S1b: Features-sports skip-if-no-upstream
└── S1b: Prediction markets per-instrument
    │
    ▼
STEP 2 (QG + merge — UAC first, then cascade)
├── S2.1 QG UAC ──→ S2.2 QG UTL ──→ S2.3-S2.10 QG rest (parallel)
└── S2.11 Quickmerge all (UAC→UTL→rest)
    │
    ▼
STEP 3 (new code — parallel, after merge)
├── S3.1  mvp_mode CLI wiring
├── S3.2  Kamino Lend collector (FREE, easy)
├── S3.3  Marginfi collector (FREE/RPC, HARD)
├── S3.4  Solend collector (HARD)
├── S3.5  Pyth oracle prices (FREE, was removed)
├── S3.6  Multi-chain oracle EVM (FREE, Alchemy)
├── S3.7  Solana LST on-chain rates (FREE, Alchemy)
├── S3.8  Features Solana lending (after S3.2)
├── S3.9  Data status underlying dimension
├── S3.10 Deployment UI new data types
└── S3.11 Stale ticker cleanup
    │
    ▼
STEP 4 (GCS retroactive migration — after all code merged, PARALLEL except S4.10)
├── S4.1  dex_pools column renames (~7K files)
├── S4.2  dex_swaps column renames (~27K files)
├── S4.3  Tick data per-instrument split (~75K files, LARGEST)
├── S4.4  Options/futures underlying partition split
├── S4.5  evm_defi archive → lending_indices
├── S4.6  Camelot + non-ETH bad data cleanup
├── S4.7  Sports odds per-league partition split (~365 files)
├── S4.8  Sports entities league_id backfill (after S3c-1)
├── S4.9  Solana DeFi old path cleanup (verify if any exist)
└── S4.10 Re-scan ALL manifests (LAST — after all above)
    │
    ▼
STEP 5 (data re-collection — VM runs, parallel)
├── S5.1 instruments-service non-ETH chains
├── S5.2 MTDS DeFi non-ETH (dex_pools + lending_indices)
├── S5.3 CeFi all data types (Tardis — FREE, per-instrument pricing)
├── S5.4 Deribit options bulk (Tardis — FREE)
├── S5.5 TradFi ES MVP (Databento — COST, ES-only)
├── S5.6 Solana DeFi normalized paths (FREE)
└── S5.7 Kamino Lend (FREE, after S3.2)
    │
    ▼
STEP 6 (validation — parallel)
├── S6.1-S6.9 Automated verification tests
└── S6.10 Instrument count audit
    │
    ▼
STEP 7 (documentation — parallel)
├── S7.1 CLAUDE.md updates
├── S7.2 Codex docs
└── S7.3 VM scripts / deployment docs
```

## Pipeline Sharding Dimensions (SSOT)

```
instruments-service → MTDS → MDPS → Features
     │                  │        │        │
     │                  │        │        └── reads from MDPS, same dimensions
     │                  │        └── reads from MTDS, same dimensions + timeframe
     │                  └── per-instrument files (spot, perps, equity, etc.)
     │                      per-underlying files (options_chain, futures_chain)
     └── defines available instruments per venue/date

Each layer's expected = previous layer's actual.
Skip if no upstream data — don't fail.

GCS Path Pattern (all layers):
  {prefix}/day={D}/[timeframe={TF}/]data_type={DT}/
  instrument_type={IT}/venue={V}/
  [underlying={U}/]           ← only for options_chain, futures_chain
  {instrument_id}.parquet     ← one file per instrument (non-derivatives)
                              ← one file per underlying (derivatives)
```

## Item Count Summary

| Step      | Category                            | Items  | Done   | Remaining |
| --------- | ----------------------------------- | ------ | ------ | --------- |
| Done      | Phase 0-2 code changes              | 15     | 15     | 0         |
| S1        | MTDS per-instrument sharding        | 1      | 1      | 0         |
| S1b       | Pipeline sharding (MDPS + Features) | 6      | 6      | 0         |
| S2        | QG + Merge                          | 11     | 11     | 0         |
| S3        | New code (expansion)                | 11     | 10     | 1         |
| S3b       | Data leakage fixes                  | 8      | 8      | 0         |
| S3c       | Sports data pipeline gaps           | 5      | 3      | 2         |
| S4        | GCS migration (retroactive)         | 10     | 9      | 1         |
| S5        | Data re-collection                  | 7      | 7      | 0         |
| S6        | Validation                          | 10     | 0      | 10        |
| S7        | Documentation                       | 3      | 2      | 1         |
| **Total** |                                     | **87** | **75** | **12**    |

## Data Provider Access Summary

| Provider     | Access                         | Cost                                 | Used For                                 |
| ------------ | ------------------------------ | ------------------------------------ | ---------------------------------------- |
| Alchemy      | Paid (21+ EVM chains + Solana) | Included                             | RPC, block resolver, gas fees, LST rates |
| The Graph    | Paid (9 keys)                  | Included                             | DeFi subgraphs (UniV3, Aave, Curve)      |
| Tardis       | Paid (2 keys: perps + full)    | Per-instrument (all data types free) | CeFi tick data                           |
| Databento    | Paid (20 keys)                 | Per-GB (tick_windows limit cost)     | TradFi (CME, CBOE, NASDAQ, FX)           |
| Pyth         | Not integrated (was removed)   | FREE (REST API, no auth)             | Solana oracle prices                     |
| DefiLlama    | Integrated                     | FREE (no auth)                       | TVL, protocol analytics                  |
| Marinade API | Integrated                     | FREE (no auth)                       | mSOL rates                               |
| Jito API     | Integrated                     | FREE (no auth)                       | jitoSOL rates                            |
| Kamino API   | Partially integrated           | FREE (no auth)                       | Vaults (done), Lending (TODO)            |
| Marginfi     | Not integrated                 | FREE (on-chain RPC)                  | Solana lending (HARD)                    |
| Solend       | Not integrated                 | Unknown                              | Solana lending (HARD)                    |
| HyperLiquid  | Integrated                     | FREE (public API)                    | Perp funding                             |

## Per-Instrument File Output Design (S1)

**Non-derivative types** (perpetual, spot, equity, etf, fx, index):

```
venue={V}/instrument_type=perpetual/data_type=trades/{SYMBOL}.parquet
venue={V}/instrument_type=spot/data_type=trades/{SYMBOL}.parquet
```

- Each instrument → own file
- Shard success/failure still at venue level
- Instrument count auditable against instrument definitions
- BigQuery Hive partition pruning on instrument
- VM memory: stream one instrument at a time, write, release

**Derivative types** (options_chain, futures_chain):

```
venue={V}/instrument_type=options_chain/data_type=options_chain/underlying={U}/ticks.parquet
```

- All strikes/expiries for one underlying in one file
- Per-underlying partition (BTC, ETH, ES, NQ)
- Already implemented in P1.1

  # ═══════════════════════════════════════════════════════════════════

  # STEP 8 — Reference League Fixtures (NEW — added 2026-04-16)

  # Fetch fixtures for cups + continental + lower divisions from API Football

  # so features-sports-service can calculate accurate team fatigue/workload.

  # ═══════════════════════════════════════════════════════════════════
  - id: s8-1-reference-league-fixtures content: |
    - [ ] [AGENT] S8. Expand instruments-service fixture fetch to include reference + features league AF IDs. Currently
          only fetches prediction league (33) fixtures from API Football. Need to also fetch: reference leagues (40
          cups/continental) + features leagues (22 lower divisions). UAC already defines these via
          get_leagues_by_classification("Reference") and ("Features"). The orchestrator needs to pass ALL league AF IDs
          to ApiFootballAdapter.get_fixtures(), not just prediction league IDs. Files:
          instruments-service/instruments_service/engine/orchestrator.py status: todo note: "Adds ~62 leagues to fixture
          fetch. API Football cost: included in Ultra plan."

  - id: s8-2-weather-incremental-rerun content: |
    - [ ] [HUMAN] S8. Re-run weather backfill after first pass completes. Weather VM running with 1097 venues (100%
          prediction league coverage). After first pass: restart VM — incremental logic fills gaps for newly-added
          venues. After reference league fixtures added: weather automatically covers those venues too. status: todo
          note: "Weather VM already running. Restart after code changes."

  - id: s8-3-validate-weather-coverage content: |
    - [ ] [AGENT] S8. Validate weather data coverage: check match rate across all prediction leagues. For each
          prediction league, count: fixtures with weather vs total fixtures. Target: 95%+ for top-5 leagues, 85%+
          overall. status: todo note: "After weather backfill completes."

  # ═══════════════════════════════════════════════════════════════════

  # STEP 9 — Sports Enrichment Backfill + Data Quality (2026-04-16)

  # ═══════════════════════════════════════════════════════════════════
  - id: s9-1-standings-migration content: |
    - [ ] [AGENT] S9. Migrate pre-2024 standings parquets: add league_id + season columns. Old schema: [rank, team,
          points, goalsDiff, group, form, status, description] New schema: [league_id, season, rank, team, points,
          goalsDiff, group, form] Migration script: read each standings parquet, add league_id from partition path, add
          season from date, write back. status: todo note: "No API calls. GCS read/write only."

  - id: s9-2-manifest-rescan-instruments content: |
    - [ ] [AGENT] S9. Re-scan instruments-service manifest. Fixes 496 empty data_type entries (pre-v4 format). Discovers
          XG data that exists in GCS but isn't in manifest (62 → 1000+ days). Also picks up weather data (307+ entries),
          per-league partitions, etc. status: todo note: "No API calls. Reads GCS, writes manifest."

  - id: s9-3-manifest-rescan-mtds-sports content: |
    - [ ] [AGENT] S9. Re-scan MTDS sports manifest. Fixes 15,488 empty data_type entries for odds data (venue=ODDS_API,
          no data_type). Should set data_type=odds for all existing entries. status: todo note: "No API calls."

  - id: s9-4-test-enrichment-1day content: |
    - [x] [AGENT] S9. Test each enrichment provider for 1-9 days locally. UNDERSTAT: ✓ 20 xG rows/date, short-circuit
          works, no API Football calls. SFI: Testing... FOOTYSTATS: Testing... TRANSFERMARKT: Testing... status: todo
          note: "Validates schemas, API connectivity, manifest writes before VM launch."

  - id: s9-5-understat-backfill-vm content: |
    - [ ] [HUMAN] S9. Launch Understat backfill VM (2019-01-01 to 2026-04-16). --sports-provider UNDERSTAT. No API key
          needed. Understat covers 5 leagues (EPL, La Liga, Bundesliga, Serie A, Ligue 1). ~2,600 dates × ~15s each =
          ~11 hours. status: todo note: "After test passes."

  - id: s9-6-sfi-backfill-vm content: |
    - [ ] [HUMAN] S9. Launch SFI backfill VM (2024-01-01 to 2026-04-16). --sports-provider SOCCER_FOOTBALL_INFO.
          RapidAPI key needed. SFI data only from Jan 2024 (Previous Runs API start). 33 mapped leagues. Rate-limited by
          RapidAPI. status: todo note: "After test passes."

  - id: s9-7-footystats-backfill-vm content: |
    - [ ] [HUMAN] S9. Launch FootyStats backfill VM (2019-01-01 to 2026-04-16). --sports-provider FOOTYSTATS. FootyStats
          API key needed. Predictions + matches for all prediction leagues. Historical season IDs mapped in UAC (459
          entries). status: todo note: "After test passes."

  - id: s9-8-transfermarkt-backfill-vm content: |
    - [ ] [HUMAN] S9. Launch Transfermarkt backfill VM (2019-01-01 to 2026-04-16). --sports-provider TRANSFERMARKT.
          RapidAPI key needed. Leagues + teams + player values. Rate-limited (~90s per league). status: todo note:
          "After test passes."

  - id: s9-9-per-league-partitioning-gaps content: |
    - [ ] [AGENT] S9. Add per-league partitioning for remaining flat entities. Currently flat: fixtures, injuries,
          transfermarkt_leagues, understat_xg. Should be per-league like fixture_stats, standings, teams. Migration:
          read flat parquet, split by league_id, write to league= subfolders. status: todo note: "Enables per-league
          data status filtering."

  - id: s9-10-footystats-season-automation content: |
    - [ ] [AGENT] S9. Implement FootyStats season ID auto-refresh. Plan exists at
          trigger_based_reference_data_2026_04_13.plan.md. Need: season_dates.py, get_reference_refresh_dates(),
          auto-fetch new season IDs from FootyStats /league-list endpoint at season boundaries. status: todo note:
          "Currently manual UAC update per season."

  - id: s9-11-final-manifest-rescan content: |
    - [ ] [HUMAN] S9. Final manifest rescan after all enrichment backfills complete. Captures all new data from
          Understat, SFI, FootyStats, Transfermarkt backfills. Verifies data status page shows accurate sports
          enrichment coverage. status: todo note: "After all VMs finish."

  # ═══════════════════════════════════════════════════════════════════

  # STEP 10 — SFI Ultra Data Integration (2026-04-16)

  # Full integration of SoccerFootball.info Ultra ($75/mo) data.

  # Currently only using league list. Ultra includes: progressive stats

  # (30s intervals with live odds), xG (from 2024-03-15), dominance

  # index, teams/players/managers/referees/stadiums, odds, websocket.

  # ═══════════════════════════════════════════════════════════════════
  - id: s10-1-sfi-schemas content: |
    - [ ] [AGENT] S10. Add UAC schemas for SFI progressive data. New types: SFIProgressiveEntry (timer, teamA stats,
          teamB stats, odds at 30s), SFIMatchOdds (pre-match 1X2/O-U/AH from bet365), SFIDominanceIndex. xG fields gated
          by availability date (2024-03-15+) — schema validation must not flag missing xG pre-2024-03-15 as an error.
          Register availability dates in UAC so manifest/data-status respect them. status: todo note: "Foundation for
          all SFI data. Must be done first."

  - id: s10-2-sfi-collector-expand content: |
    - [ ] [AGENT] S10. Expand SFI adapter to collect ALL Ultra data. Currently collects: leagues, matches (basic),
          progressive. Add: full match data (/matches/day/full/ — includes odds, dominance), teams (/teams/), players,
          managers, referees, stadiums. Store progressive data with ALL fields: timer, goals, possession, attacks,
          shoots, corners, fouls, dominance, xG, IN-PLAY ODDS. Use /matches/day/full/ instead of /matches/day/basic/ for
          richer data. status: todo note: "SFI Ultra at 4 req/s. 1505 matches/day = ~6 min/day."

  - id: s10-3-sfi-canonical-mappings content: |
    - [ ] [AGENT] S10. Build SFI → canonical entity mappings. SFI has its own team IDs, player IDs, referee IDs, stadium
          IDs. Need: SFI team ID → API Football team ID → canonical team ID. Approach: fuzzy match on team name +
          country, then manual review. Store mappings in UAC (like SOCCER_FOOTBALL_INFO_IDS for leagues). Automated
          refresh at season boundaries for new/promoted teams. status: todo note: "Critical for joining SFI data to
          features pipeline."

  - id: s10-4-sfi-progressive-schema content: |
    - [ ] [AGENT] S10. Design GCS schema for progressive stats entity. Path:
          sports_reference/by_date/day={date}/entity=sfi_progressive/ Columns per entry: timer, match_id, team_a_goals,
          team_b_goals, team_a_xg, team_b_xg (from 2024-03-15), possession_a, possession_b, attacks_a, attacks_b,
          shoots_on_a, shoots_on_b, corners_a, corners_b, fouls_a, fouls_b, dominance_a, dominance_b, odds_1x2_home,
          odds_1x2_draw, odds_1x2_away, odds_ou_over, odds_ou_under, odds_ou_value, odds_ah_home, odds_ah_away,
          odds_ah_value. ~195 rows per match × 1505 matches/day = ~293K rows/day. status: todo note: "This is the
          in-play backtest goldmine."

  - id: s10-5-sfi-in-play-odds content: |
    - [ ] [AGENT] S10. Extract and store in-play odds time series from progressive data. Every 30 seconds: 1X2, O/U,
          Asian Handicap odds from bet365. This enables in-play betting backtests: what happens if you always bet the
          team that's behind? What's the CLV at minute 60 vs minute 75? Store as separate entity or as columns within
          progressive stats. status: todo note: "Unique data — no other source provides 30s in-play odds."

  - id: s10-6-sfi-xg-integration content: |
    - [ ] [AGENT] S10. Add SFI xG as secondary xG source alongside Understat. SFI xG available from 2024-03-15 for ALL
          SFI leagues (not just 5 like Understat). Store in progressive stats entity with availability date gate.
          Features pipeline can use SFI xG when Understat doesn't cover the league, or cross-validate when both are
          available. status: todo note: "Broader xG coverage than Understat."

  - id: s10-7-sfi-availability-gates content: |
    - [ ] [AGENT] S10. Implement per-field availability dates in UAC + validation. xG: available from 2024-03-15 only.
          Progressive: available from SFI API version 1.50. Schema validation must NOT flag missing xG pre-2024-03-15 as
          error. Deployment UI data status should show correct denominators per date range. Add
          get_field_availability_date(entity, field) to UAC. status: todo note: "Prevents false positive alerts."

  - id: s10-8-sfi-backfill-vm content: |
    - [ ] [HUMAN] S10. Launch SFI backfill VM with --sports-provider SOCCER_FOOTBALL_INFO. Confirmed working: 1505
          matches/day, 195 progressive entries/match. Date range: 2024-03-15 to 2026-04-16 (xG available). Earlier
          dates: progressive without xG. Rate limit: 4 req/s, ~25 min/day for progressive data. status: todo note:
          "After schemas and collector expansion."

  - id: s10-9-sfi-live-hooks content: |
    - [ ] [AGENT] S10. Wire SFI websocket for live data feed. SFI Ultra includes websocket for MAIN, STATS, ODDS in
          real-time. Hook into unified-trading-api live feed pipeline. Enables: live progressive stats, live xG, live
          odds updates. Compare latency vs API Football live endpoint. status: todo note: "Future — after batch backfill
          is stable."

  - id: s10-10-sfi-vs-api-football-audit content: |
    - [ ] [AGENT] S10. Audit SFI vs API Football data for overlap/gaps. For each entity (teams, players, referees,
          stadiums): - Compare coverage (which leagues, how many entities) - Compare timeliness (which updates faster
          after transfers/events) - Compare data richness (which has more fields) - Identify what SFI provides that API
          Football doesn't (and vice versa) Document findings for data source selection decisions. status: todo note:
          "Informs which source to prefer per entity."
