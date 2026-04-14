---
name: mtds-defi-data-normalization
overview: Complete pipeline-wide per-instrument sharding (MTDS→MDPS→Features), DeFi normalization, data quality fixes, data status, multi-chain expansion, GCS migration — 55 items across 11 repos
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
      - [ ] [AGENT] S1. Per-instrument file output for non-options/futures data types.
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
    status: todo
    note: "Must be done before QG/merge since it changes output structure"

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
      - [ ] [AGENT] S1b. PARALLEL. MDPS skip-if-no-upstream: don't fail if MTDS data doesn't exist.
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
      - [ ] [AGENT] S1b. PARALLEL. MDPS availability index must include underlying dimension.
        MDPS writes manifest via ManifestWriter (UTL). The underlying field was already added to
        ManifestWriter in P1.1. MDPS must populate it when writing manifest records for
        options_chain/futures_chain data types.
        Files: market-data-processing-service/app/core/orchestration_service.py (_write_manifest_records).
    status: todo
    note: ""

  - id: s1b-features-underlying
    content: |
      - [ ] [AGENT] S1b. PARALLEL. Update features-delta-one-service for per-instrument + per-underlying reading.
        Features reads from MDPS processed_candles. Must handle:
        (a) Per-instrument files (already the case — MDPS writes {instrument_id}.parquet)
        (b) Per-underlying partition for options/futures
        (c) Skip if MDPS data doesn't exist for a venue/instrument (don't fail)
        ALSO FIX: path mismatch bug — code uses `day-{date}` (dashes) instead of `day={date}` (hive).
        Files: features-delta-one-service/app/core/data_loader.py (fix paths, add underlying support),
        features-delta-one-service availability/manifest (track per-instrument + underlying).
    status: todo
    note: "Path bug: day- vs day= must be fixed regardless"

  - id: s1b-features-sports-skip
    content: |
      - [ ] [AGENT] S1b. PARALLEL. Features-sports-service skip-if-no-upstream.
        FSS reads raw odds ticks and sports reference data, not MDPS candles.
        T-24h/T-12h/.../T-0 bucketing happens in FSS directly.
        Ensure it skips gracefully when upstream data (odds ticks, reference entities) doesn't exist
        for a date/venue/league. Same pattern as MTDS upstream preflight.
        Files: features-sports-service/data/gcs_reader.py.
    status: todo
    note: "Sports has different time bucket structure but same skip-if-no-upstream principle"

  - id: s1b-prediction-sharding
    content: |
      - [ ] [AGENT] S1b. PARALLEL. Prediction markets: same per-instrument sharding for trades.
        Kalshi and Polymarket trades should be per-instrument (per-market/per-condition) files.
        book_snapshot_5 doesn't exist yet but will eventually — same structure.
        MDPS downsamples prediction trades the same way as CeFi trades.
        Ensure MTDS Kalshi/Polymarket adapters write per-instrument files.
        Files: MTDS market_interface/adapters/prediction/kalshi_adapter.py,
        MTDS market_interface/adapters/prediction/polymarket_adapter.py,
        MDPS prediction adapter (if exists).
    status: todo
    note: ""

  # ═══════════════════════════════════════════════════════════════════
  # STEP 2 — QG + Merge All Code Changes (SEQUENTIAL per repo)
  # Gate: All repos pass QG, then quickmerge
  # ═══════════════════════════════════════════════════════════════════

  - id: s2-1-qg-uac
    content: |
      - [ ] [AGENT] S2. Run QG on unified-api-contracts.
        Changes: removed phantom types (tvl, utilization, evm_defi), tick_windows SSOT,
        MVP_CME_EXCHANGE_CODES, data type renames (swaps→dex_swaps, rate_indices→lending_indices),
        registered 10 real DeFi data types.
    status: todo
    note: "UAC must pass first — downstream repos import from it"

  - id: s2-2-qg-utl
    content: |
      - [ ] [AGENT] S2. Run QG on unified-trading-library.
        Changes: underlying field in ManifestWriter AvailabilityRecord.
    status: todo
    note: ""

  - id: s2-3-qg-instruments
    content: |
      - [ ] [AGENT] S2. Run QG on instruments-service.
        Changes: chain-agnostic block resolver rewrite.
    status: todo
    note: ""

  - id: s2-4-qg-mtds
    content: |
      - [ ] [AGENT] S2. Run QG on market-tick-data-service.
        Changes: shard hard failure, bulk OPTIONS, per-underlying partition, per-instrument files,
        upstream preflight, split solana_defi, Jito collector, EVM column normalize, schema validation,
        exchange_code filter, mvp_mode wiring.
    status: todo
    note: "Largest change set — expect most QG fixes here"

  - id: s2-5-qg-features
    content: |
      - [ ] [AGENT] S2. Run QG on features-onchain-service.
        Changes: updated MTDS output config, removed utilization, added dex_pools.
    status: todo
    note: ""

  - id: s2-6-qg-deploy-api
    content: |
      - [ ] [AGENT] S2. Run QG on deployment-api.
        Changes: tick_windows from UAC, denominator fix (weighted aggregation, cap 100%, tick-window aware).
    status: todo
    note: ""

  - id: s2-7-qg-deploy-svc
    content: |
      - [ ] [AGENT] S2. Run QG on deployment-service.
        Changes: tick_windows from UAC.
    status: todo
    note: ""

  - id: s2-8-qg-mdps
    content: |
      - [ ] [AGENT] S2. Run QG on market-data-processing-service.
        Changes: per-underlying partition reading/writing, skip-if-no-upstream, manifest underlying.
    status: todo
    note: ""

  - id: s2-9-qg-features-d1
    content: |
      - [ ] [AGENT] S2. Run QG on features-delta-one-service.
        Changes: per-underlying reading, skip-if-no-upstream, path bug fix (day- vs day=).
    status: todo
    note: ""

  - id: s2-10-qg-features-sports
    content: |
      - [ ] [AGENT] S2. Run QG on features-sports-service.
        Changes: skip-if-no-upstream for odds/reference data.
    status: todo
    note: ""

  - id: s2-11-quickmerge-all
    content: |
      - [ ] [AGENT] S2. Quickmerge all repos (UAC first, then UTL, then rest in parallel).
        Order: UAC → UTL → (instruments-svc, MTDS, MDPS, features-*, deployment-api, deployment-svc)
        because downstream repos import from UAC/UTL.
    status: todo
    note: "bash scripts/quickmerge.sh 'feat: MTDS DeFi data normalization' --agent"

  # ═══════════════════════════════════════════════════════════════════
  # STEP 3 — Remaining Code Changes (PARALLEL, after merge)
  # ═══════════════════════════════════════════════════════════════════

  - id: s3-1-mvp-mode-cli
    content: |
      - [ ] [AGENT] S3. PARALLEL. Wire mvp_mode from MTDS CLI args to orchestrator.
        P1.4 added mvp_mode param through the call chain but it's not exposed as a CLI flag yet.
        Add --mvp-mode flag to CLI that passes through to orchestrator.
        Files: MTDS cli/main.py (add flag), cli/handlers/tick_data_handler.py (pass through).
    status: todo
    note: ""

  - id: s3-2-kamino-lend
    content: |
      - [ ] [AGENT] S3. PARALLEL. Add Kamino Lend collector to MTDS.
        The /v2/reserves endpoint already exists in execution-service/kamino.py (lines 123-173).
        Returns: supply_apy, borrow_apy, total_supply, total_borrows, ltv, liquidation_threshold.
        Write to lending_indices bucket. Register Kamino Lend as a lending protocol in UAC
        capability declarations (currently only listed as DEX).
        Files: UAC _defi.py (add kamino_lend protocol), MTDS solana_defi_handler.py (add _collect_kamino_lending).
    status: todo
    note: "Free API, no auth, quick win"

  - id: s3-3-marginfi
    content: |
      - [ ] [HUMAN+AGENT] S3. PARALLEL. Add Marginfi lending collector.
        No free REST API found. Requires on-chain RPC account parsing — decode Marginfi program
        accounts (mrgn program) for lending rates via Solana RPC getAccountInfo + getProgramAccounts.
        Need to reverse-engineer account data layout or find Marginfi SDK docs.
        Files: UAC (register protocol), instruments-service (new adapter), MTDS (new collector).
    status: todo
    note: "Hard — no REST API. Requires Solana program state decoding"

  - id: s3-4-solend
    content: |
      - [ ] [HUMAN+AGENT] S3. PARALLEL. Add Solend lending collector.
        Same situation as Marginfi — no free public API identified. Would need on-chain RPC
        account parsing or find if they have an undocumented REST endpoint.
        Files: UAC (register protocol), instruments-service (new adapter), MTDS (new collector).
    status: todo
    note: "Hard — no REST API. Lower priority than Marginfi"

  - id: s3-5-pyth-oracle
    content: |
      - [ ] [AGENT] S3. PARALLEL. Add Pyth oracle prices for Solana assets.
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
      - [ ] [AGENT] S3. PARALLEL. Extend oracle_prices to multi-chain EVM (Chainlink on Arb/Base/Polygon/etc).
        Current: oracle_prices_handler only queries Ethereum mainnet Chainlink.
        Many Chainlink feeds exist on L2s with different aggregator addresses.
        Use Alchemy RPC on each chain (already paid for all chains).
        Files: MTDS oracle_prices_handler.py (add per-chain Chainlink feed configs).
    status: todo
    note: "Free — Alchemy RPC on all chains already available"

  - id: s3-7-solana-lst-onchain
    content: |
      - [ ] [AGENT] S3. PARALLEL. Add mSOL/jitoSOL on-chain exchange rate tracking to lst_rates_handler.
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
      - [ ] [AGENT] S3. PARALLEL. Update deployment-api tree builder to show per-underlying breakdowns.
        The availability index now has an underlying column. The data status UI should show
        BTC vs ETH options separately, ES vs NQ futures separately.
        Files: deployment-api/services/data_status_service.py (add underlying dimension to tree builder).
    status: todo
    note: ""

  - id: s3-10-deployment-ui-types
    content: |
      - [ ] [AGENT] S3. PARALLEL. Update deployment-ui to render new normalized data types.
        The UI needs to display: dex_pools, dex_swaps, lending_indices, perp_funding, lst_rates,
        oracle_prices, gas_fees, rewards, risk_params. Remove: evm_defi, solana_defi, tvl, utilization.
        Also render per-underlying breakdowns for options/futures.
        Files: deployment-ui (TypeScript) — data status components.
    status: todo
    note: ""

  - id: s3-11-stale-tickers
    content: |
      - [ ] [AGENT] S3. PARALLEL. Clean stale tickers from TRADFI_TICKER_UNIVERSE.
        SGEN (acquired by Pfizer), SPLK (acquired by Cisco), COUP (taken private) — remove from
        sp500_tickers and nasdaq_tickers lists.
        Files: UAC registry/tradfi_instrument_universe.py.
    status: todo
    note: "Small cleanup"

  # ═══════════════════════════════════════════════════════════════════
  # STEP 3b — Data Leakage Fixes (PARALLEL with S3)
  # Audit found 8 leakage gaps across sports + non-sports pipeline.
  # These must be fixed before any ML training runs.
  # ═══════════════════════════════════════════════════════════════════

  - id: s3b-1-footystats-result-gate
    content: |
      - [ ] [AGENT] S3b. CRITICAL. Gate FootyStats actual match results from pre-match features.
        home_goals, away_goals, total_goals, status="completed", and post-match stats (possession,
        shots, corners) are stored in the same CanonicalFixture as pre-match predictions.
        Fix: In features-sports-service feature_expectations.py, add min_horizon=FT for ALL actual
        result columns: home_goals, away_goals, total_goals, status, home_possession, away_possession,
        home_shots, away_shots, home_corners, away_corners, home_fouls, away_fouls, home_cards_*,
        away_cards_*. The horizon gating infrastructure already exists — just need to declare these fields.
        Files: features-sports-service/engine/feature_expectations.py (add FT horizon for actual results),
        features-sports-service/exporters/derived_features_exporter.py (verify _filter_completed_before covers all).
    status: todo
    note: "CRITICAL — actual match results could leak into pre-match features"

  - id: s3b-2-postmatch-xg-gate
    content: |
      - [ ] [AGENT] S3b. CRITICAL. Gate post-match xG (home_xg, away_xg) with min_horizon=FT.
        FootyStats provides both xg_prematch_home (pre-match, safe) and home_xg (post-match actual).
        Currently no horizon gate on home_xg/away_xg — could be used as features before match ends.
        Fix: Add min_horizon=FT for home_xg, away_xg in feature_expectations.py.
        Files: features-sports-service/engine/feature_expectations.py.
    status: todo
    note: "CRITICAL — post-match xG is near-perfect predictor of outcome"

  - id: s3b-3-odds-postmatch-filter
    content: |
      - [ ] [AGENT] S3b. MEDIUM. Filter MTDS odds to bm_time <= kickoff_utc only.
        Odds API adapter stores odds snapshots with bm_time (bookmaker update time).
        Post-match odds (bm_time > kickoff_utc) should be filtered out before writing to GCS.
        These odds are heavily correlated with match outcome (market knows the result).
        Fix: In odds_api_adapter.py, filter rows where bm_time > kickoff_utc.
        Files: MTDS market_interface/adapters/sports/odds_api_adapter.py.
    status: todo
    note: ""

  - id: s3b-4-ht-odds-fallback
    content: |
      - [ ] [AGENT] S3b. MEDIUM. Default HT odds cutoff when HT break time unknown.
        _apply_ht_odds_pit_gate() returns early (no gating) if ht_break_minutes is empty.
        Fix: Default to T+45 with cutoff of -55 minutes. Log WARNING about missing HT time.
        Files: features-sports-service/exporters/odds_features_exporter.py.
    status: todo
    note: ""

  - id: s3b-5-standings-pit
    content: |
      - [ ] [AGENT] S3b. MEDIUM. Filter league standings to pre-fixture date.
        Standings snapshot could include results from fixtures happening TODAY.
        Fix: In league calculator, filter standings to updated_before < fixture.kickoff_utc.
        Files: features-sports-service/exporters/derived_features_exporter.py (_compute_league_batch).
    status: todo
    note: ""

  - id: s3b-6-transfermarkt-date
    content: |
      - [ ] [AGENT] S3b. LOW. Add valuation_date to Transfermarkt player values.
        market_value_eur has no date — current values appear in historical features.
        Fix: Add valuation_date field in instruments-service Transfermarkt adapter,
        filter to pre-fixture date in squad_value_calculator.
        Files: instruments-service/sports/adapters/transfermarkt.py,
        features-sports-service/calculators/squad_value_calculator.py.
    status: todo
    note: ""

  - id: s3b-7-prediction-resolution-filter
    content: |
      - [ ] [AGENT] S3b. MEDIUM. Filter prediction market resolved status from features.
        Polymarket/Kalshi closed/resolution_outcome fields could leak into features.
        Ensure only open/unresolved markets contribute to downstream signals.
        Files: MTDS prediction adapters, features pipeline (if consuming prediction data).
    status: todo
    note: ""

  - id: s3b-8-onchain-strict-mode
    content: |
      - [ ] [AGENT] S3b. LOW. Set features-onchain-service PIT enforcer to strict=True for production.
        Currently strict=False — violations are logged but pipeline continues.
        Fix: Change to strict=True or add alerting on logged PIT violations.
        Files: features-onchain-service PIT enforcement code.
    status: todo
    note: ""

  # ═══════════════════════════════════════════════════════════════════
  # STEP 4 — GCS Data Migration (after all code merged)
  # ═══════════════════════════════════════════════════════════════════

  - id: s4-1-migration-script
    content: |
      - [ ] [AGENT] S4. Write GCS bulk migration script.
        Handles: (a) Solana path moves (solana_defi/ → dex_pools/, perp_funding/, lst_rates/),
        (b) EVM dex_pools column renames (token0_symbol→token_a, fee_tier→fee_rate_bps, etc),
        (c) EVM dex_swaps column renames (token_in_symbol→token_in, etc),
        (d) Delete stale evm_defi/ data,
        (e) Delete Camelot V3 pre-2023-06 wrong data,
        (f) Re-scan availability index for all affected venues.
        Script reads parquet, renames columns, writes back. For path moves, uses GCS copy+delete.
        Files: MTDS scripts/ or PM scripts/.
    status: todo
    note: ""

  - id: s4-2-run-migration
    content: |
      - [ ] [HUMAN+AGENT] S4. Run GCS migration script.
        Execute the migration script from S4.1 against production GCS buckets.
        Verify data integrity after migration (spot-check a few dates per venue).
    status: todo
    note: "Human-initiated — production GCS modification"

  - id: s4-3-rescan-manifests
    content: |
      - [ ] [HUMAN+AGENT] S4. Re-scan availability index for ALL affected DeFi venues.
        After migration, run data_manifest_handler to rebuild the availability index
        with correct paths, data types, and underlying dimensions.
    status: todo
    note: ""

  # ═══════════════════════════════════════════════════════════════════
  # STEP 5 — Data Re-Collection (VM runs, after merge + migration)
  # ═══════════════════════════════════════════════════════════════════

  - id: s5-1-instruments-non-eth
    content: |
      - [ ] [HUMAN] S5. PARALLEL. Re-run instruments-service on ALL non-ETH EVM chains.
        7 chains (Arbitrum, Polygon, Base, Optimism, Avalanche, BSC, Linea) × all Graph-based
        protocols (Uniswap V3 forks + Aave V3). Fixed block resolver now returns correct
        historical block numbers. Free — existing Alchemy + Graph keys.
    status: todo
    note: "VM run"

  - id: s5-2-mtds-defi-non-eth
    content: |
      - [ ] [HUMAN] S5. PARALLEL. Re-run MTDS dex_pools + lending_indices for non-ETH chains.
        Data collected with wrong block numbers needs replacement.
        7 chains × ~14 DEX protocols × all historical dates for dex_pools.
        7 chains × Aave V3 × all dates for lending_indices.
        Free — existing Graph keys.
    status: todo
    note: "VM run — large scope, may take days"

  - id: s5-3-cefi-all-types
    content: |
      - [ ] [HUMAN] S5. PARALLEL. Run MTDS for ALL CeFi data types across all venues.
        book_snapshot_5, derivative_ticker, liquidations, futures_chain, options_chain.
        9 CeFi venues × 6 data types × all dates since venue launch.
        Free — Tardis is per-instrument pricing, all data types included.
        Use tardis-api-key-full for full access.
    status: todo
    note: "VM run — Tardis, no incremental cost"

  - id: s5-4-deribit-options
    content: |
      - [ ] [HUMAN] S5. PARALLEL. Run MTDS Deribit options with bulk OPTIONS download.
        DERIBIT × options_chain × all dates since 2019-03-30.
        Now 1 API call per date (bulk OPTIONS.csv.gz) instead of ~1900.
        Free — Tardis.
    status: todo
    note: "VM run"

  - id: s5-5-tradfi-es-mvp
    content: |
      - [ ] [HUMAN] S5. PARALLEL. Run MTDS TradFi with ES-only MVP filter.
        CME × ES futures/options × all dates. Use --mvp-mode flag.
        Databento cost applies but limited to ES parent symbols only (not full universe).
        tbbo/trades only in tick_windows (May 2023, July 2024). ohlcv_1m all other dates.
    status: todo
    note: "VM run — Databento cost, but ES-only"

  - id: s5-6-solana-defi-normalized
    content: |
      - [ ] [HUMAN] S5. PARALLEL. Run Solana DeFi collection with new normalized paths.
        Orca→dex_pools, Raydium→dex_pools, Kamino→dex_pools, Drift→perp_funding,
        Marinade→lst_rates, Jito→lst_rates.
        Free — all REST APIs, no auth.
    status: todo
    note: "VM run — small data"

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
      - [ ] [AGENT] S7. PARALLEL. Update CLAUDE.md in affected repos for data type name changes
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
STEP 4 (GCS migration — after all code merged)
├── S4.1 Write migration script
├── S4.2 Run migration (human)
└── S4.3 Re-scan manifests
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

| Step | Category | Items | Done | Remaining |
|------|----------|-------|------|-----------|
| Done | Phase 0-2 code changes | 15 | 15 | 0 |
| S1 | MTDS per-instrument sharding | 1 | 0 | 1 |
| S1b | Pipeline sharding (MDPS + Features) | 6 | 0 | 6 |
| S2 | QG + Merge | 11 | 0 | 11 |
| S3 | New code (expansion) | 11 | 0 | 11 |
| S3b | Data leakage fixes | 8 | 0 | 8 |
| S4 | GCS migration | 3 | 0 | 3 |
| S5 | Data re-collection | 7 | 0 | 7 |
| S6 | Validation | 10 | 0 | 10 |
| S7 | Documentation | 3 | 0 | 3 |
| **Total** | | **75** | **15** | **60** |

## Data Provider Access Summary

| Provider | Access | Cost | Used For |
|----------|--------|------|----------|
| Alchemy | Paid (21+ EVM chains + Solana) | Included | RPC, block resolver, gas fees, LST rates |
| The Graph | Paid (9 keys) | Included | DeFi subgraphs (UniV3, Aave, Curve) |
| Tardis | Paid (2 keys: perps + full) | Per-instrument (all data types free) | CeFi tick data |
| Databento | Paid (20 keys) | Per-GB (tick_windows limit cost) | TradFi (CME, CBOE, NASDAQ, FX) |
| Pyth | Not integrated (was removed) | FREE (REST API, no auth) | Solana oracle prices |
| DefiLlama | Integrated | FREE (no auth) | TVL, protocol analytics |
| Marinade API | Integrated | FREE (no auth) | mSOL rates |
| Jito API | Integrated | FREE (no auth) | jitoSOL rates |
| Kamino API | Partially integrated | FREE (no auth) | Vaults (done), Lending (TODO) |
| Marginfi | Not integrated | FREE (on-chain RPC) | Solana lending (HARD) |
| Solend | Not integrated | Unknown | Solana lending (HARD) |
| HyperLiquid | Integrated | FREE (public API) | Perp funding |

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
