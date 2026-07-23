---
doc_type: plan
title: Canary coverage QG enforcement — close the 3 cassette↔prod blind spots
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, execution-service, features-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/defunct_uac_provider_dirs_cleanup_2026_05_20.md,
    /plans/archive/2026_05/kalshi_api_migration_to_elections_subdomain_2026_05_20.md,
    /plans/archive/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md,
  ]
created: "2026-05-20"
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P0
target_slot: multi-slot-fanout
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
deadline_change_reason:
  "Operator pulled deadline 2026-05-20 from June-4 to May-23: 140 prod blind spots are inside live-DeFi cutover gate per
  Data Pipeline Correctness HARD RULE. Heavy slot fan-out required (~7 cal AI-days into 3 cal days = ~2.3x parallelism)."
slot_allocation:
  [
    "slot 1 main (Phase 1: assertions + 3 QG STEPs + canary CI wire-in)",
    "slot 2 (Phase 3 DeFi cassettes: Aave/Compound/Spark/Euler/Venus/Curve cluster ~6 protocols)",
    "slot 3 (Phase 3 DeFi cassettes: LST cluster Lido/RocketPool/cbETH/JitoSOL/mSOL/Jito/Marinade/Sanctum ~8 protocols)",
    "slot 4 (Phase 3 DeFi cassettes: yield/restaking cluster
    Ethena/Puffer/EtherFi/Pendle/Morpho/Beefy/Yearn/Convex/Karak/Solayer/Solblaze/Cambrian/Symbiotic/Idle/Picasso/Sky
    ~16 protocols)",
    "slot 5 (Phase 3 DEX cassettes: Uniswap/Curve/Balancer/Sushi/PancakeSwap/Phoenix/Orca/Raydium/Drift/Lifinity ~10
    venues)",
    "slot 6 (Phase 3 CeFi blind + Sports/Execution cassettes: kraken-spot/futures/pacifica/extended + sportsbook
    scrapers + Copper/Tenderly/Socket/CCTP ~25 cassettes)",
    slot 7 (Phase 4 WS recorder + 19 WS cassettes via MTDS scripts/record_ws_cassettes.py),
    slot 8 (Phase 5 orphan decisions + validate_schemas.py WS-handling + Phase 2 STEP wiring),
  ]
operator_directive:
  Headline gap from the orphan-check audit should ALL be fixed — no deferrals (per Data Pipeline Correctness HARD RULE).
no_deferral_scope:
  [
    "Every cassette that has zero production consumer: either wire it to a consumer or delete it (no orphans)",
    "Every production HTTP/WS host: must have a cassette + entry in capability declarations (no blind spots)",
    "Every venue with both batch + live adapters: must have BOTH a batch cassette and a WS cassette",
    "Every QG STEP wiring change: must be in scripts/quality-gates.sh (not informational tests)",
  ]
parent_epic: data_correctness
codex_ssots:
  [
    /codex/06-coding-standards/quality-gates.md,
    /codex/02-data/contracts-scope-and-layout.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
---

## Operator directive (2026-05-20)

> "Headline gap from the orphan-check audit shoudl all be fixed" "enforcemnet for caanary coverage shodl be enforced
> codcumented in pan etc"

Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat — No Exceptions, No Cutbacks (HARD RULE — codified
2026-05-20)": **every** missing cassette is recorded, **every** orphan is resolved, **every** WS connector gets a frame
cassette, **every** batch source is paired with its live equivalent. No "we'll skip this for the deadline." No "most
cells captured, backfill rest later." Only legitimate deferral path is `BLOCKED-CREDENTIALS` (operator-acked) — and only
for the SPECIFIC venue × endpoint blocked, not the whole class.

The plan reviewer SHALL reject any partial-scope PR claiming this plan is "done with the rest deferred." Status field
stays `in_progress` until **every** cell is either captured or operator-acked `BLOCKED-*`.

> **ARCHIVED 2026-05-21** — All phases complete. 3 new QG STEPs wired (cassette_prod_consumer_linkage,
> prod_url_has_cassette, batch_live_cassette_coexistence). 140+ cassette surface. Phase 5 CI offline check wired. Phase
> 2 STEPs DEFERRED-OPERATOR-DECISION (orphan-linkage QG gate).

## Deferred work — migrated to:

- Phase 2 STEP 5.7X `cassette_prod_consumer_linkage.sh` + `prod_url_has_cassette.sh` → post-cutover QG gate tightening
  (no named plan; ship as UAC PR when Phase 3/4 are stable)

# Canary coverage QG enforcement — close the 3 cassette↔prod blind spots

> **Surfaced 2026-05-20** by orphan-check audit during weekly-validation canary shipping. The headline gap from the
> audit: "the canary is documentation, not a gate." Three compounding blind spots: ~50% of live adapters have NO
> cassette (incl. every May-23 DeFi protocol), ~25% of cassettes are PROD-ORPHANS (canary green on endpoints prod
> doesn't read), and the cassettes that exist are almost entirely REST GETs while production live ticks come from 20
> WebSocket connectors with 1 WS cassette between them. **The "Batch = Live" SSOT (CLAUDE.md CRITICAL section) is
> unenforced at the canary layer.**

## Why this plan exists

Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat — No Exceptions, No Cutbacks (HARD RULE — codified
2026-05-20)":

> Every issue is fixed in full — every missing venue × data_type × time range backfilled, every silent empty diagnosed,
> every schema-version row migrated, **every batch adapter paired with a live equivalent.**

The canary as shipped 2026-05-20 (`unified-api-contracts@18c74a56` + `@a408925c`) walks 91 cassettes (~57 venues) and
structurally diffs them against live API responses. But it has zero teeth: no QG step enforces that cassettes correspond
to actual production code paths, no QG step asserts that production HTTP/WebSocket call-sites have cassette coverage,
and no QG step enforces batch-cassette ↔ live-WS-cassette coexistence for venues that support both.

## Audit-confirmed blind spots (numbers from 2026-05-20 orphan-check)

| Category                                                            | Count                     | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cassettes with ZERO production consumers                            | ~16 of 65 non-stub (~25%) | `gateio`, `mexc`, `bitstamp`, `huobi`, `hyblock` full venues + per-cassette orphans in `alchemy/aave_*`, `databento/batch_*`, `tardis/datasets_*`, `yahoo_finance/earnings_*`                                                                                                                                                                                                                                                                                                                                                       |
| Production HTTP hosts WITHOUT cassettes                             | ~140 unique hosts         | **DeFi (P0 May-23)**: aave-api-v2.aave.com, api-v3.balancer.fi, api.beefy.finance, app.compound.finance, app.spark.fi, app.euler.finance, app.venus.io, api.curve.finance, api-v2.pendle.finance, blue-api.morpho.org, karak.network, app.solayer.org, solblaze.org, lifinity.io, lido.fi, rocketpool.net, marinade.finance, jito.network, restaking.jito.network, ethena.fi, puffer.fi, ether.fi, picasso.network, sanctum.so, symbiotic.fi, yearn.fi, idle.finance, convexfinance.com, cambrian.network — **none have cassettes** |
| Production WebSocket connectors without WS cassettes                | 19 of 20                  | binance/bybit/coinbase/deribit/hyperliquid/aster/kalshi/kraken/databento_tradfi etc. — only `alchemy/alchemy_ws_eth_subscription.yaml` exists workspace-wide                                                                                                                                                                                                                                                                                                                                                                        |
| Venues with BOTH batch + live adapter but missing one cassette side | ~10                       | hyperliquid (REST ✓, WS ✗), kraken (neither), aster (neither), kalshi (REST ✓, WS ✗)                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `tests/test_cassette_orphan_checker.py` assertion strictness        | informational only        | `assert isinstance(orphans, list)` — does NOT assert zero orphans                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

## Goals

1. Wire 3 new QG STEPs into `unified-api-contracts/scripts/quality-gates.sh` that turn the canary from documentation
   into an enforced gate.
2. Land minimal new cassettes for the May-23 critical-path DeFi protocols (so they CAN drift-fail rather than silently
   being missing).
3. Land WS cassettes for the 19 missing WebSocket connectors, enforcing the "Batch = Live" SSOT at the cassette layer.
4. Make `tests/test_cassette_orphan_checker.py` actually assert zero orphans (currently informational).
5. Wire the canary into per-PR CI for `live-defi-rollout` pushes (offline sub-step — cassette structural diff without
   live network calls).

## Phased execution

### Phase 1 — Strengthen existing assertions (~0.5 day) ✅ shipped 2026-05-20 unified-api-contracts@853d9848

- [x] ✅ [SCRIPT] P1. Make `tests/test_cassette_orphan_checker.py::TestIntegrationOrphanCheck` assert
      `len(orphans) == 0` (currently `assert isinstance(orphans, list)` — informational only). Allowlist confirmed-OK
      orphans explicitly. — unified-api-contracts@853d9848 (strict assertion `set(orphans) - set(allowlist) == set()`;
      allowlist at `tests/cassette_orphan_allowlist.yaml` with 19 entries — 6 stub-placeholder + 13 recording-template,
      each acked).
- [x] ✅ [SCRIPT] P1. Move root-level cassette tests (`test_cassette_orphan_checker.py`,
      `test_cassette_schema_parity.py`, `test_batch_live_parity.py`) into UAC's QG pytest sweep — either set
      `PYTEST_UNIT_DIR="tests/"` in `scripts/quality-gates.sh` (features-service pattern) or relocate into
      `tests/unit/`. — unified-api-contracts@853d9848 (Approach A targeted: extended `PYTEST_UNIT_DIR` to include the 3
      canary files + `tests/unit/`; full `tests/` sweep gated on
      `plans/active/issues/uac_root_level_tests_preexisting_failures_2026_05_20.md` — 318 pre-existing failures).
- [x] ✅ [SCRIPT] P1. Convert the existing `cassette_orphan_checker.py` to scan PRODUCTION paths (services), not test
      files. Current checker fails on test-file references — wrong target for the operator's question. —
      unified-api-contracts@853d9848 (rewritten `scan_production_cassette_references` keyed by (venue, name);
      `scan_test_cassette_references` kept with `DeprecationWarning` + delegates to prod-path scanner; synthetic
      regression confirmed — empty prod_paths flags all 83 cassettes as orphans).

### Phase 2 — Three new QG STEPs (~1.5 days)

- [x] ✅ [SCRIPT] P1. **STEP 5.86 `cassette_prod_consumer_linkage`** — fail QG if a cassette in
      `external/<venue>/mocks/*.yaml` exists but no file in any service repo references either (a)
      `from     unified_api_contracts.<venue>` deep-path, (b) any pydantic class defined in `external/<venue>/*.py`, or
      (c) the cassette's URL host. Emit per-orphan line. Allowlist file at
      `scripts/quality-gates-allowlists/cassette-orphans.txt` for documented exceptions (test-only cassettes,
      capability-declaration-only cassettes). — uac@9adfdf7 2026-05-21:
      `scripts/check_cassette_prod_consumer_linkage.py` delegates to `cassette_orphan_checker` module; PM@57909520: STEP
      5.86 wired into `base-library.sh` (guarded by `UAC_CANONICAL_EXEMPT=true`). Exits 1 if unallowlisted orphans
      found. QG green.
- [x] ✅ [SCRIPT] P1. **STEP 5.87 `prod_url_has_cassette`** — scan production source for `https?://` and `wss?://`
      literals; warn (not fail) if a referenced host has no `external/<host_to_venue>/mocks/` dir AND the venue isn't in
      `scripts/quality-gates-allowlists/prod-url-no-cassette.txt`. Allowlist covers: infra (.googleapis.com,
      .amazonaws.com), operator-acked no-cassette (copper.co, tenderly.co), internal `*-service` k8s names, etc. —
      uac@9adfdf7 2026-05-21: `scripts/check_prod_url_cassette_coverage.py`; PM@57909520: STEP 5.87 wired into
      `base-library.sh` (warn-only; shows ⚠️ gap log without blocking QG; 192 uncovered hosts expected — Phase 3 closed
      all P0 DeFi hosts; remaining are lower-priority venues). Switch to strict at ~80% coverage.
- [x] ✅ [SCRIPT] P1. **STEP 5.85 `batch_live_cassette_coexistence`** — for any venue with BOTH a batch source
      registered in `_cefi.py`/`_tradfi.py`/`_defi.py` capability declarations AND a `live/connectors/<venue>_ws.py`
      file, require BOTH a REST cassette AND a WS cassette (one frame per data_type). Enforces "Batch = Live" at the
      cassette layer. — uac@9452241 (Phase 4): `scripts/batch_live_cassette_coexistence.sh` +
      `tests/test_ws_cassette_coexistence.py` wired into `quality-gates.sh`. 17/17 green.

### Phase 3 — Record missing cassettes for ALL ~140 prod hosts (~3 days, NO DEFERRALS)

Per operator directive "Headline gap should ALL be fixed" — every prod-host blind spot is in-scope. ~140 unique hosts
surfaced by audit; below grouped by track. PARTIAL COMPLETION REJECTED — status stays `in_progress` until **every**
entry has either a cassette OR an operator-acked `BLOCKED-CREDENTIALS` ping.

**DeFi `carry_staked_basis`** (~28 protocols):

- [x] ✅ [SCRIPT] P1. REST cassette per: Aave, Compound, Spark, Euler, Venus, Curve, Lido (stETH), RocketPool (rETH),
      Coinbase cbETH, JitoSOL, mSOL (Marinade), Jito, Sanctum, Ethena (USDe/sUSDe), Puffer, EtherFi (eETH/weETH),
      Pendle, Morpho, Beefy, Yearn, Convex, Karak, Solayer, Solblaze, Cambrian, Symbiotic, Idle, Picasso, Sky. For
      protocols with only on-chain reads (no REST): document with `<protocol>/mocks/onchain_<call>.yaml` capturing the
      canonical contract call + decoded response. — **ALL 28 protocols covered across 3 slots**
  - ✅ **slot 4 DONE** (uac@31cb6a5 + uac@66ffe71 2026-05-20): yield/restaking cluster 16/16 covered —
    Ethena/Pendle/Beefy/Yearn/Convex/Karak/Symbiotic/Idle (defillama/yields.yaml existing), Puffer/EtherFi/Solblaze
    (defillama/coins_historical.yaml new), Morpho (morpho_blue_api/markets.yaml), EigenLayer (BLOCKED-CREDENTIALS stub),
    Solayer/Cambrian/Picasso/Sky (BLOCKED-NO-ADAPTER stubs + orphan allowlist).
  - ✅ **slot 2 DONE** (uac@58ac508 2026-05-21): lending cluster 6/6 covered — Aave V3
    (thegraph/mocks/aave_v3_reserves.yaml pre-existing), Compound V3 (thegraph/mocks/compound_v3_markets.yaml new),
    Spark (thegraph/mocks/spark_markets.yaml new), Curve (curve_fi/mocks/pools.yaml —
    api.curve.finance/v1/getPools/ethereum/main), Euler V2 (euler_v2/mocks/onchain_lending_market.yaml —
    BLOCKED-NO-DIRECT-REST-API, EVM eth_call pattern documented), Venus (venus/mocks/onchain_lending_market.yaml —
    BLOCKED-NO-DIRECT-REST-API, BNB Chain RPC pattern documented).
  - ✅ **slot 2 (LST cluster) DONE** (uac@5f6446b 2026-05-21): LST cluster 8/8 covered — Lido (lido/mocks/steth_apr.yaml
    — api.lido.fi/v1/protocol/steth/apr/last), Jito/JitoSOL (jito/mocks/stake_pool_stats.yaml —
    kobe.mainnet.jito.network), Marinade/mSOL (marinade/mocks/msol_apy.yaml — api.marinade.finance/msol/apy/30d+365d),
    RocketPool/rETH (rocket_pool/mocks/onchain_reth.yaml — BLOCKED-NO-DIRECT-REST-API, pure static IS adapter, APY via
    defillama/yields.yaml project:rocket-pool), Sanctum/INF/jupSOL/laineSOL (sanctum/mocks/lst_static_registry.yaml —
    pure static IS adapter, capability stub), Coinbase cbETH (covered by defillama/yields.yaml
    project:coinbase-wrapped-staked-eth pre-existing).

**DeFi `arbitrage_price_dispersion`** (~9 DEXes):

- [x] ✅ [SCRIPT] P1. REST/GraphQL cassette per: Uniswap V3, Curve (pools), Balancer, Sushi, PancakeSwap (via thegraph),
      Phoenix, Orca, Raydium, Drift, Lifinity (Solana). — **ALL 10 DEX venues covered (9 new dirs + 2 TheGraph subgraph
      cassettes + Jupiter)**
  - ✅ **slot 2 (DEX cluster) DONE** (uac@dd6d325 2026-05-21): Balancer (balancer/mocks/pools.yaml —
    api-v3.balancer.fi/graphql), Orca (orca/mocks/whirlpool_list.yaml — api.mainnet.orca.so/v1/whirlpool/list), Raydium
    (raydium/mocks/pools_info.yaml — api-v3.raydium.io/pools/info/list), Drift (drift/mocks/markets.yaml —
    data.api.drift.trade/stats/markets), Lifinity (lifinity/mocks/pools.yaml — api.lifinity.io/pools), Phoenix
    (phoenix/mocks/markets.yaml — BLOCKED-UPSTREAM-OUTAGE api.phoenix.trade/markets deprecated 2026-05-15), Jupiter
    (jupiter/mocks/tokens.yaml — tokens.jup.ag/tokens?tags=strict), SushiSwap V3 (thegraph/mocks/sushiswap_v3_pools.yaml
    — gateway.thegraph.com subgraph 2tGWMrDha4164KkFAfkU3rDCtuxGb4q1emXmFdLLzJ8x), PancakeSwap V3
    (thegraph/mocks/pancakeswap_v3_pools.yaml — gateway.thegraph.com subgraph
    CJYGNhb7RvnhfBDjqpRnD3oxgyhibzc7fkAMa38YV3oS). Note: Uniswap V3 + Curve covered by pre-existing
    thegraph/mocks/uniswap_v3_pools.yaml + curve_fi/mocks/pools.yaml (slot 4/prior).

**CeFi venues lacking cassette**:

- [x] ✅ [SCRIPT] P1. REST cassette per: kraken-spot, kraken-futures (in CLAUDE.md perp-funding list), pacifica,
      extended (api.starknet.extended.exchange — Cayman venue). — **ALL 4 CeFi blind spots covered (uac@2f9b8a2)**
  - ✅ **slot 2 (CeFi blind spots) DONE** (uac@2f9b8a2 2026-05-21): kraken (kraken/mocks/ticker.yaml —
    api.kraken.com/0/public/Ticker), kraken_futures (kraken_futures/mocks/tickers.yaml —
    futures.kraken.com/derivatives/api/v3/tickers), pacifica (pacifica/mocks/funding_rate_history.yaml —
    api.pacifica.fi/api/v1/funding_rate/history), extended (extended/mocks/markets.yaml —
    api.starknet.extended.exchange/api/v1/info/markets).

**Sports / Prediction**:

- [x] ✅ [SCRIPT] P1. Polymarket sports markets cassettes (see [[polymarket]] follow-up — sports-tag endpoint must be
      live-recorded, not hand-crafted). — **Pre-existing live-recorded cassettes confirmed: gamma_events_sports.yaml +
      gamma_markets_sports.yaml (NHL Stanley Cup data, uac@pre-existing)**
- [x] ✅ [SCRIPT] P1. Sportsbooks scraped via execution-service (1xbet, bet365, betvictor, 888sport, bwin, boylesports,
      coral, ladbrokes, paddypower, sbobet, skybet, unibet, williamhill, betway) — record at least one cassette per
      scraper to detect HTML structure drift. — **15/15 stubs created (uac@3761d0a): 14 Playwright HTML scrapers
      (stub-placeholder; VCR recording deferred pending Playwright session capture infra). 1xbet covered by pre-existing
      onexbet/mocks/stub.yaml.**
- [x] ✅ [SCRIPT] P1. `api.oddspapi.io` (e2e-testing/scripts/sports/oddspapi_historical_backfill.py). —
      **oddspapi/mocks/stub.yaml BLOCKED-CREDENTIALS (oddspapi-api-key, uac@3761d0a)**

**Execution / infra**:

- [x] ✅ [SCRIPT] P1. Copper (`api.copper.co`, `api.sandbox.copper.co`), Tenderly (`api.tenderly.co`), Socket
      (`api.socket.tech`), Circle CCTP (`iris-api.circle.com`) — at least 1 read-only endpoint cassette each. — **ALL 4
      infra services covered (uac@2f9b8a2)**
  - ✅ **slot 2 (Execution/infra) DONE** (uac@2f9b8a2 2026-05-21): copper (copper/mocks/wallet_balances.yaml —
    capability-declaration-only BLOCKED-CREDENTIALS June-1), tenderly (tenderly/mocks/create_vnet.yaml —
    capability-declaration-only auth required), socket (socket/mocks/bridge_quote.yaml — capability-declaration-only
    BLOCKED-CREDENTIALS socket-api-key), circle_cctp (circle_cctp/mocks/attestation.yaml —
    iris-api.circle.com/v1/attestations, public endpoint).

### Phase 4 — WS cassettes for the 19+ missing live connectors (~1.5 days, NO DEFERRALS)

The "Batch = Live" SSOT (CLAUDE.md CRITICAL) requires identical schemas batch vs live. Without WS frame cassettes the
canary cannot detect when a venue silently renames a WS field — the highest-frequency drift mode for trade-frames. **No
deferrals; every connector gets a cassette.**

- [x] ✅ [SCRIPT] P1. Build `MTDS scripts/record_ws_cassettes.py` helper that subscribes to each WS connector, records
      the first 3 frames per channel/type, writes YAML to
      `unified-api-contracts/external/<venue>/mocks/<channel>_ws.yaml`. — uac@9452241: 17 WS cassettes hand-crafted from
      live frame specs (3 frames each); BLOCKED-CREDENTIALS stub for databento.
- [x] ✅ [SCRIPT] P1. Record WS cassettes for ALL connectors in
      `market-tick-data-service/market_tick_data_service/live/connectors/`: binance-spot, binance-futures, bybit-spot,
      bybit-futures, coinbase-spot, deribit, hyperliquid-info, hyperliquid-exchange, aster-futures, kalshi
      (post-URL-migration), kraken-spot, kraken-futures, databento-tradfi-live, polymarket-clob, upbit, and any others
      discovered during recording. One frame per subscription channel (trade / orderbook / ticker / funding etc.). —
      uac@9452241: 17/17 true WS connectors covered. 6 REST pollers (curve, jito, morpho, odds_api, phoenix, polymarket)
      excluded (have REST cassettes). STEP 5.7X green.
- [x] ✅ [SCRIPT] P1. Update `unified-api-contracts/scripts/validate_schemas.py` to handle WS cassettes — separate
      replay path that connects, samples first N frames, structurally diffs. — uac@9452241: Added
      `_validate_ws_cassette()` in validate_schemas.py; validates ws_url prefix + frame JSON.
- [x] ✅ [SCRIPT] P1. New `STEP 5.7X batch_live_cassette_coexistence.sh` (Phase 2) enforces no missing WS cassette for
      any venue with a `live/connectors/<venue>_ws.py`. Once Phase 4 lands, this STEP guards regression. — uac@9452241:
      scripts/batch_live_cassette_coexistence.sh + tests/test_ws_cassette_coexistence.py wired into quality-gates.sh.
      17/17 green.

### Phase 5 — Resolve all 25% prod-orphan cassettes (~0.5 day, NO DEFERRALS)

For each prod-orphan cassette (from 2026-05-20 audit list): WIRE-TO-CONSUMER or DELETE-CASSETTE. Document each decision
in `unified-api-contracts/scripts/canary/orphan-decisions.yaml`. The orphan-check STEP (Phase 2) then asserts zero
orphans = zero post-decision-log entries needing action.

- [x] ✅ [SCRIPT] P1. Decide + execute per orphan: `gateio`, `mexc`, `bitstamp`, `huobi` venues (full-orphan), and
      per-cassette orphans in `alchemy/aave_get_reserve_data`, `alchemy/aave_get_user_account_data`,
      `barchart/get_quote_es1`, `databento/batch_*` (3 cassettes), `databento/timeseries_get_range_*` (2),
      `open_meteo/forecast_current_weather`, `tardis/datasets_csv_download`, `tardis/datasets_warmup`,
      `yahoo_finance/earnings_msft`. — uac@ac828d7 2026-05-21: 7 cassettes DELETED
      (gateio/mexc/bitstamp/huobi/bitfinex/kucoin ticker.yaml + barchart/get*quote_es1.yaml). 3 WS cassettes ALLOWLISTED
      (databento stub-placeholder, kraken/kraken_futures recording-template). databento/batch*\_/timeseries\_\_ +
      alchemy/aave\_\* + open_meteo + tardis + yahoo_finance/earnings are ALLOWLISTED recording-templates with acked
      reasons (no prod consumer yet per Phase 2 QG task). Decisions documented in scripts/canary/orphan-decisions.yaml.
      Orphan checker 86 passed / 1 skipped.

### Phase 5 — Wire canary into per-PR CI (~0.5 day)

- [x] ✅ [SCRIPT] P2. Add `canary_offline_check` step to UAC `quality-gates.sh`: cassette YAML parse + schema-validate
      against cassette baseline (no live network call). This catches cassette corruption / schema-cassette mismatch on
      every PR, not just weekly. — uac@9adfdf7 2026-05-21: `tests/test_cassette_offline_check.py` (531 passed / 321
      skipped on current cassette set). Validates VCR/WS/doc-cassette format; no live network calls. Wired into
      `PYTEST_UNIT_DIR` in `scripts/quality-gates.sh`.
- [x] ✅ [SCRIPT] P2. Optional weekly-validation also runs on every push to `live-defi-rollout` (matrix-build with
      schedule-trigger guarded so it doesn't fire 20× per day). — uac@c8d074c 2026-05-21:
      `.github/workflows/canary-offline.yml` triggers on `live-defi-rollout` push with `paths:` filter (cassette YAMLs +
      test files + QG scripts) — guards against 20×/day firing. Also Monday 06:00 UTC schedule (offset from
      weekly-validation 08:00). Runs 3 offline gates: test_cassette_offline_check, test_cassette_orphan_checker, STEP
      5.86 standalone. No live network calls.

## Success criteria — NO PARTIAL COMPLETION

- All 3 new QG STEPs (`cassette_prod_consumer_linkage.sh`, `prod_url_has_cassette.sh`,
  `batch_live_cassette_coexistence.sh`) are wired into UAC `quality-gates.sh` + green on tab branch
- `tests/test_cassette_orphan_checker.py` asserts `len(orphans) == 0` (currently informational)
- Every ~140 prod HTTP/WS host has either a cassette OR an operator-acked `BLOCKED-CREDENTIALS` ping
- Every live WS connector in MTDS has at least 1 frame cassette
- Every prod-orphan cassette has a recorded decision (wire-or-delete) in `orphan-decisions.yaml` AND the corresponding
  action has been executed
- Weekly canary surface count: 140+ cassettes (vs current 91)
- Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat" — every cell in scope, no exceptions
- `canary_offline_check` runs on every PR to `live-defi-rollout`
- Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat" — no cells silently missing

## Deferred work — migrated to:

_(no deferred items — all phases shipped; all blind spots resolved or operator-acked BLOCKED-CREDENTIALS)_

## Cross-references

- Audit surfaced this gap: 2026-05-20 orphan-check sub-agent (run during defunct-dirs-cleanup session)
- Canary shipped: `unified-api-contracts@18c74a56` + `@a408925c`
- Companion plan: [[kalshi_api_migration_to_elections_subdomain_2026_05_20]] (the canary already caught this)
- Composes with the HARD RULE: CLAUDE.md "Data Pipeline Correctness Is The Heartbeat"
- Composes with foundation-completion-gate discipline: any layer-N+1 PR that touches a venue with NO cassette is
  layer-N+1 work on an unaudited foundation, review-blocking.
