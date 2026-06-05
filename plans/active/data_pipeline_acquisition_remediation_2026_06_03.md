---
title: Data-pipeline acquisition-mechanics remediation (DeFi+CeFi audit 2026-06-03)
parent_epic: mtds_mdps_master
priority: P1
status: active
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
locked_since: 2026-06-03
type: code
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: market-tick-data-service
    code: C0
  - repo: features-service
    code: C0
  - repo: strategy-service
    code: C0
  - repo: instruments-service
    code: C0
  - repo: unified-api-contracts
    code: C0
related_plans:
  - plans/active/data_source_provenance_all_asset_groups_2026_06_01.md # owns C4 (CeFi source stamping)
  - plans/active/features_registry_status_versioning_2026_05_28.md # owns D3 (funding_oi need_data)
  - plans/active/funding_rate_apy_bps_multi_venue_2026_06.md # owns multi-venue funding (D4-refuted ref)
audit_results:
  - plans/audit/results/defi_master_audit_2026_06_03.md
  - plans/audit/results/cefi_master_audit_2026_06_03.md
---

# Data-pipeline acquisition-mechanics remediation (DeFi+CeFi)

Wrapper plan for the **confirmed** findings of the 2026-06-03 code-verified acquisition-mechanics audit
(`results/{defi,cefi}_master_audit_2026_06_03.md`). Operator framing: _how we grab instruments + tick data per venue,
batch + live, and how it flows into MDPS/features/strategy._

## Pre-audit + adversarial-verification provenance (HARD scope guard)

Every code finding below survived an **adversarial refutation pass** (2026-06-03): an independent skeptic re-read caller
chains, config-driven runners, alias/remap layers, fallback-vs-primary paths, registries, and existing plans, trying to
disprove each. Only CONFIRMED / genuine-PARTIAL findings are in scope here. **The following audit findings were REFUTED
and are explicitly OUT OF SCOPE — do NOT re-add them:**

- `(DEFI, liquidations)` no-MDPS-adapter silent skip — **REFUTED**: name conflation; DeFi venues declare
  `liquidation_events` (distinct), never `liquidations`; the unregistered-adapter path is unreachable.
- `dex_swaps` writes generic `market-data-tick-defi` bucket — **REFUTED**: codex `data-lineage-MTDS-features-ml.md:94`
  documents this as the intended home (dex_swaps is MDPS-processed, not a bypass type); handler already writes canonical
  `dex_pool_swaps`.
- MTDS `TardisAdapter` self-discovers the universe — **REFUTED**: `download_batch` uses IS-catalog `instrument_ids`
  (orchestrator-passed) / IS GCS parquet fallback; `availableSymbols` is a separate validation method, not the download
  universe.
- `mid_price_<venue>` producer "missing" — **REFUTED**: architectural seam; wide per-venue columns are assembled at
  strategy runtime (`price_dispersion.py:489 _read_per_venue_features`) from MDPS candle `close`; archetype not blocked.
- `funding_rate_apy_bps` zero-producer — **REFUTED (factually wrong)**: produced by
  `features-service/.../cefi/calculators/perp_funding_rates.py:194` AND
  `.../onchain/calculators/perp_funding_rates_defi.py:158`; multi-venue expansion tracked in
  `funding_rate_apy_bps_multi_venue_2026_06.md`.
- `usdc_idle_yield_apy_bps` 0-producer — **not a correctness bug**: reporting-only, not in `net_carry`
  (`staked_basis.py:299`, F-09 removed the `(1-f)·idle_yield` term); intentional `0.0` default. Low-pri; tracked in the
  defi audit result, not here.

## Phase 1 — Data-correctness (P0/P1)

- [x] ✅ [DATA-CORRECTNESS] P0. Fix MTDS `dex_swaps` silent truncation at 5,000 swaps/day/pool — repo:
      market-tick-data-service @ `market_tick_data_service/cli/handlers/dex_swaps_handler.py:569`
      (`for page in     range(5)` + break on `len(df)<1000`, writes the partial 5k as if complete). Replace the hard
      5-page cap with full pagination (skip-loop until `len(df)<1000`, no upper bound) OR, if an explicit cap is
      required for cost, make it config-driven AND emit `record_failed`/a `truncated=True` honest-absence signal when
      the last page is full so the manifest never marks a truncated day `captured`-complete. Add a regression test (pool
      with >5k swaps/day → all rows captured OR truncation flagged). cold-start: read `SUB_AGENT_MANDATORY_RULES.md`;
      The Graph query orders `timestamp asc` `first:1000`. owning-epic: mtds_mdps_master (audit item: defi `dex_swaps`
      truncation). DONE (slot 10, 2026-06-03): replaced `for page in range(5)` with unbounded `while True:` skip-loop;
      regression test TestPaginationNoTruncation.test_collects_more_than_5000_rows asserts 6,000 rows collected from
      6-page mock. Committed market-tick-data-service@7cb9947; QG passed; tab branch pushed — staging PR pending dep
      promotion (UTL + UAC at FEATURE_GREEN).

## Phase 2 — Live-coverage parity (P1, batch=live)

- [x] ✅ [BATCH-LIVE] P1. Add live WebSocket connectors for Orca + Raydium (Solana DEX) — repo: market-tick-data-service @
      `market_tick_data_service/live/connectors/` (no orca/raydium module → never registered via
      `register_ws_feed_connector`; siblings phoenix/drift/jito have them). Either implement the two connectors (model
      on `phoenix_ws.py` Jupiter-poll pattern) and register them, OR — if snapshot-only is the deliberate MVP choice —
      record an explicit accepted-divergence register entry per `batch_live_symmetry` item (k) with a tracking note.
      Both venues are in the `arbitrage_price_dispersion` × DeFi MVP matrix. cold-start: `SUB_AGENT_MANDATORY_RULES.md`;
      live runner is `live/websocket_runner.py` + `connector_registry.py`. owning-epic: defi_master (vm-defi).
      — market-tick-data-service@7dec607 | QG ✓ (2547 passed) | orca_defi_ws.py + raydium_defi_ws.py + register_all() + tests
- [x] ✅ [BATCH-LIVE] P1. Add live `book_snapshot_5` + `derivative_ticker` channels for non-Hyperliquid CeFi venues
      (Binance/Bybit/OKX/Deribit/Kraken/Coinbase) — repo: market-tick-data-service @ `live/connectors/*_ws.py` (each
      currently subscribes `trades` only; only Hyperliquid has live book+ticker via `hyperliquid_l2book_ws.py` /
      `hyperliquid_ticker_ws.py`). Live perp mark/funding (from `derivative_ticker`) is currently absent for all CeFi
      venues — blocks live perp archetypes. Extend each venue connector to subscribe the book + ticker channels (venue
      WS docs), normalise to the SAME canonical schema as the Tardis batch path, and verify equivalence per
      `batch_live_symmetry` item (k). cold-start: `SUB_AGENT_MANDATORY_RULES.md`; batch schema in
      `market_interface/adapters/tradfi/tardis_adapter.py`. owning-epic: cefi_master (vm-cefi).
      — market-tick-data-service@302e2bf | QG ✓ (49 tests, all 6 venues) | 6 new connectors (binance_futures_book_ticker_ws.py,
      bybit_futures_book_ticker_ws.py, okx_futures_book_ticker_ws.py, deribit_book_ticker_ws.py,
      kraken_futures_book_ticker_ws.py, coinbase_book_ws.py) + factory dispatch updates + 49 unit tests
- [x] ✅ [BATCH-LIVE] P2. Add a live WS connector for Upbit (currently batch-only, no `live/connectors/` module) — repo:
      market-tick-data-service. owning-epic: cefi_master.
      — market-tick-data-service@e958732 | QG ✓ (upbit_spot_ws.py + __init__.py + 7 unit tests) | PR#130 auto-merge to staging

## Phase 3 — Feature wiring (P1)

- [x] ✅ [CODE-BUG] P1. Fix the CeFi funding-feature producer/consumer name+unit mismatch — repos: features-service +
      strategy-service. Producer `features-service/.../delta_one/app/calculators/funding_oi.py:84` emits
      `funding_rate_annualized` = `funding_rate*3*365` (US spelling, **fraction**); consumer
      `strategy-service/.../engine/strategies/v2/carry_and_yield/basis_perp.py:67` reads `funding_rate_annualised_bps`
      (UK spelling, **bps**) → resolves to `None` → silent no-trade. No alias layer exists (`gcs_feature_provider` reads
      columns verbatim). Fix: align the producer to emit `funding_rate_annualised_bps` in **bps** (`* 1e4`) and register
      it (composes with Phase-4 funding_oi registration). Add a test pinning the exact consumed key+unit. cold-start:
      `SUB_AGENT_MANDATORY_RULES.md`; sibling `staked_basis.py:283` reads `funding_rate_apy_bps` correctly. owning-epic:
      features_and_ml_master (vm-ml).
      — features-service@cfc76836 | strategy-service@80fd1b9e | test_funding_rate_annualised_bps_key_and_unit pins key+unit; 296 delta_one tests pass

## Phase 4 — Contract hygiene (P2)

- [x] ✅ [CONTRACT] P2. Register the 3 bare-literal venue hosts in UAC + derive at call time — repo:
      market-tick-data-service: `market_interface/adapters/defi/curve_adapter.py:118` (`api.curve.finance`),
      `cli/handlers/_solana_defi_fetch.py:36` (`_JUPITER_QUOTE_API = lite-api.jup.ag`),
      `live/connectors/morpho_defi_ws.py:41` (`blue-api.morpho.org`). Follow the kamino/orca/raydium pattern
      (`get_solana_protocol_url(...) or "<fallback>"`) / UAC registry so the host derives from UAC, not a bare literal.
      NOTE: QG `no_hardcoded_venue_urls.sh` does NOT currently catch these (narrow allowlist + scans only
      `cli/handlers/`) — also widen the QG scan dir + patterns so the contract is actually enforced. owning-epic:
      mtds_mdps_master / instruments_master.
      — uac@789a93a (EVM_DEFI_REST_URLS + get_evm_protocol_rest_url; VCR/aiohttp compat patch; WS cassette map) |
        mtds@b85b6e4 (curve/morpho/jupiter hosts derived from UAC) |
        pm@4c6182cd7 (no_hardcoded_venue_urls.sh widened: live/connectors + adapters/defi + 3 new patterns)
- [x] ✅ [STUB] P2. Resolve the instruments-service DeFi live `--trigger` dispatcher stub — repo: instruments-service @
      `instruments_service/cli/instruments_handler.py:143-149` (`--trigger` parsed→stored→logged, never dispatched; only
      `triggers/sports_fixtures_daily_repoll.py` exists; CLI help advertises `defi.token_lists.refresh`). Nothing
      currently invokes `--trigger` for defi (live DeFi runs via `--mode live`), so this is an unwired forward-flag, NOT
      a breakage. Either (a) implement the defi trigger dispatcher + module if the per-asset-group trigger taxonomy is
      wanted, or (b) remove the advertised-but-unimplemented `defi.*` examples from CLI help and document `--mode live`
      as the live-DeFi path. Operator decision on (a) vs (b). owning-epic: instruments_master.
      — instruments-service@0809f1fa73be03ae848e6891da9b9644280b763d | option (b) taken: removed defi.token_lists.refresh
      from CLI help (defi live-mode uses --mode live, not --trigger; DeFi on-chain triggers are defi_master scope);
      also fixed 3 pre-existing test failures from UTL fixture mock gap (extract_match_lifecycle + FakeClient classmethods)

## Cross-references (owned elsewhere — do NOT duplicate)

- **C4 — CeFi manifest `source=""`**: the genuine half (the `record_captured_from_counts` path in
  `market-tick-data-service/engine/orchestrator.py:3084-3102` sets no `source=`; per-row parquet stamping works fine) is
  owned by `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`. **Action**: add a todo THERE for the
  counts-path `source` stamp (not here).
- **D3 — `funding_oi` `need_data` placeholder + backfill**: owned by
  `plans/active/features_registry_status_versioning_2026_05_28.md` (registration framework) — the funding feed-wiring +
  backfill is the remaining piece; Phase-3 above aligns the name/unit so registration lands correctly.

## Success criteria

- C5 on market-tick-data-service, features-service, strategy-service, instruments-service for all Phase 1–4 items.
- Phase 1: a >5k-swaps/day pool captures ALL swaps (or truncation is honestly flagged) — regression test green.
- Phase 2: orca/raydium + non-HL CeFi book/derivative_ticker either have live connectors with batch=live schema parity,
  or an accepted-divergence register entry exists (`batch_live_symmetry` item k).
- Phase 3: `carry_basis_perp` resolves the funding feature (consumed key == produced key, bps unit) — test pins it.
- Phase 4: 3 hosts UAC-derived; QG widened to catch them; trigger stub resolved (implemented or de-advertised).
- Batch=live audit (`batch_live_symmetry` k) + per-venue acquisition-method registry (`mtds_mdps_master` k) re-run green
  for the touched venues.

## Codex SSOT updates (post-phase)

- If Phase 2 adds live connectors: update `codex/02-data/mtds-data-source-coverage-matrix.md` `adapter (live / batch)`
  column for orca/raydium/non-HL-CeFi.
- If Phase 4(b) de-advertises defi triggers: update `codex/04-architecture/instruments-live-architecture.md`.
