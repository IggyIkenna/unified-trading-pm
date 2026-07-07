---
doc_type: issue
title: 'Full MTDS + instruments-service adapter smoke test — 59 real bugs found across CeFi/DeFi/TradFi/Sports/Prediction, plus a real instrument-dimension sample bank and MTDS capability matrix'
summary:
  'Operator asked for a comprehensive smoke test of every single MTDS + instruments-service adapter
  ("to ensure no more adapter issues") plus a representative real instrument_id sample per real
  structural dimension (margin type coin/non-coin, inverse/linear perpetuals, futures, options with
  calls/puts) for every venue — explicitly "so the mockup gives this info on time," before the real
  UAC/instruments-service migration work starts. Ran a 17-cluster parallel investigation (one cluster
  per venue/protocol family) covering every live CeFi venue, every DeFi protocol category (lending,
  pools, yield/staking, restaking, GMX/Drift), all 7 TradFi venues, all 7 Sports providers, and both
  Prediction venues — each cluster actually executed real adapters (not just read code) and pulled real
  production/live data. Found 59 distinct real bugs (several are crash risks or silent-corruption
  violations, not just coverage gaps), confirmed a large real instrument_id sample bank covering every
  real dimension per venue, and produced a full MTDS data_type-capability matrix. This is the single
  largest findings batch of the session — logged here as the master record; smaller, more specific
  issue docs already filed this session (lending a-token/debt-token split, non-Tardis DEX-perp smoke
  test, KALSHI-PERP plan) are cross-referenced rather than duplicated.'
status: open
nature: notes
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data, meta]
repos:
  [
    market-tick-data-service,
    instruments-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags:
  [
    smoke-test,
    adapter-bugs,
    instrument-dimensions,
    margin-type,
    honest-coverage,
    data-pipeline-correctness,
    crash-risk,
    silent-placeholder,
  ]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md,
    ../prediction_capture_incident_remediation_2026_07_06.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P0
source: 'Operator, 2026-07-07: "you are gonna smoke test every single MTDS and IS to ensure no more
  adaptor issues and update mock MTDS and IS with updated source of actual truth given the tests...
  dump representative mock instrument id for every dimension of instruments... for the marketing data
  service, I want to effectively have validated through you that we are able to download every data
  type and instrument type." 17-cluster parallel workflow, each cluster running real adapter execution
  + real production data reads, not guessing.'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 7.2
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — largest single batch this session, spans every MTDS/IS adapter,
> includes multiple P0 crash risks and at least one silent-corruption HARD RULE violation.** This is
> the master record; work items are prioritized below but NOT all fixed yet — most are logged findings,
> not shipped fixes. Cross-referenced docs above cover lending (already filed) and the 5 non-Tardis
> DEX-perp venues (already filed) in more depth; this doc covers everything else plus the full picture.

## 1. Real instrument-dimension sample bank (selected highlights — full bank in Progress Log / workflow journal)

**DERIBIT has BOTH inverse (USD-margined) and linear (USDC-margined) products for PERPETUAL, FUTURE,
AND OPTION alike** — this corrects an assumption made earlier this session (that Deribit was
single-margin-type). Real samples: `DERIBIT:PERPETUAL:BTC-USD` (inverse) / `DERIBIT:PERPETUAL:BTC-USDC`
(linear); `DERIBIT:OPTION:BTC-10JUL26-48000-C`/`-P` (inverse call/put) and
`DERIBIT:OPTION:BTC_USDC-10JUL26-48000-C`/`-P` (linear call/put); `DERIBIT:COMBO:BTC-CS-17JUL26-63000_65000`.

Other confirmed real dimension coverage: BINANCE-DELIVERY (coin-margined inverse) vs BINANCE-FUTURES
(linear); OKX-SWAP/-FUTURES coin-margined vs linear (though margin_type itself is mislabeled — see bugs);
BYBIT inverse PERPETUAL exists but is mistagged linear; COINBASE-FUTURES genuinely has no FUTURE/OPTION/
inverse product (verified 3 ways, not just absent); KRAKEN-FUTURES/BITFINEX-FUTURES have real
inverse+linear splits; CME has real FUTURE/OPTION(call+put)/COMBO but EVENT_CONTRACT is always
misclassified as OPTION (0 real EVENT_CONTRACT rows exist anywhere); PENDLE has a real 3-way split
(PT/YT/SY) — the richest dimension split found in DeFi; POLYMARKET's book_snapshot_5 grain is genuinely
two instruments per market (YES token_id + NO token_id) while its trades grain is one (condition_id) —
a real, deliberate dual-grain design, not an inconsistency.

Full per-venue sample tables (CeFi/DeFi/TradFi/Sports/Prediction) are in the workflow synthesis —
transcribed into both mockups as the next step (see Todos).

## 2. MTDS capability matrix — selected highlights

Most venues/dimensions are WORKS-NOW. Standout non-working ones: FLUID lending_indices 100% broken;
ETHENA oracle_prices/apy always fabricated (1.0/0.0, never a real call); GMX perp_funding always
synthetic (native funding schema fails silently, 100% of rows are OI-imbalance-derived, not real);
GMX liquidations always fails (schema mismatch, recorded as honest zero — indistinguishable from real
absence); DRIFT perp_funding dead endpoint; HUOBI-FUTURES fully unenumerable in production (raw data
confirmed working when called directly — pure wiring gap); ICE/CBOE INDEX data_types fail silently
(routed to Databento instead of Yahoo, empty with no error); POLYMARKET book_snapshot_5 crashes the
entire date's capture (schema mismatch, uncaught).

## 3. Full bug list (59 items, grouped by cluster, priority-tagged)

### P0 — crash risks, silent-corruption HARD RULE violations, or complete coverage gaps

- **[DERIBIT]** `market_tick_data_service/live/connectors/deribit_ws.py:100` — dash-count heuristic
  misclassifies every dated future trade as OPTION on the LIVE path (batch classifier is correct) — a
  real live-vs-batch determinism violation.
- **[LENDING]** `fluid.py:113, venus.py:105, benqi.py:98, radiant.py:121, euler_v2.py:93` — all 5 use
  hardcoded `"LENDING_MARKET"`, not a valid `InstrumentType` enum member — same crash risk as
  COMPOUND_V3/MORPHO (already filed in [[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]) —
  **confirms that todo's open question: none of the 7 not-yet-verified lending protocols has a real
  A_TOKEN/DEBT_TOKEN split.**
- **[LENDING]** `market_tick_data_service/.../defi/fluid_adapter.py:394,399-401,422` — revert-data guard
  never fires (`ContractCustomError` not caught) — FLUID's `lending_indices` is 100% broken in practice.
- **[YIELD_STAKING]** `market-tick-data-service/.../defi/ethena_adapter.py:249-268,270-285` —
  `oracle_prices`/`apy` unconditionally return fabricated hardcoded values (`1.0`/`0.0`) under fake
  source tags — a direct violation of the workspace's "never silent placeholders" HARD RULE.
- **[PREDICTION]** `unified_api_contracts/external/polymarket/schemas.py:74-75` — `bids`/`asks` typed
  `list[list[float]]` but the real API returns `list[dict]` — `ValidationError` on every real order-book
  fetch, uncaught through the full call chain (`polymarket_adapter.py:207,459-498,761-800`), **crashing
  the entire date's `book_snapshot_5` capture**, not just that one market.
- **[SMALL_SPOT/SMALL_DERIV]** `unified_api_contracts/registry/market_data_categories.py:223-271`
  (`VENUES_BY_ASSET_GROUP["cefi"]`) + `venue_adapter_keys.py` + `venue_mapping.py:169-205` —
  `HUOBI-SPOT`, `HUOBI-FUTURES`, `BITSTAMP-SPOT` are missing from the venue universe entirely — never
  fetched at all in production despite real, working adapter code underneath (confirmed by direct calls).
- **[OKX]** `instruments_service/reference_data/router.py:176` area — no `okex-options` routing
  anywhere — 246,000+ real option symbols never wired into the capture pipeline.
- **[OKX]** `instruments-service/.../adapters/cefi/tardis/parsing.py:388-427` — margin_type inverted
  for every OKX-SWAP/OKX-FUTURES derivative (coin-margined tagged linear and vice versa) — a real
  P&L-relevant misclassification, same class as the lending a-token/debt-token issue.
- **[BYBIT]** `parsing.py:396-427 (_infer_margin_type)` — no Bybit branch — every inverse perpetual
  defaults to LINEAR (same margin-type misclassification class as OKX above).
- **[BYBIT]** `parsing.py:541-567 (_split_symbol)` + `adapter.py:712-723` — cannot parse non-dashed
  inverse-future symbols (`BTCUSDU26`) — 46 real products silently dropped from the catalogue entirely.

### P1 — real bugs, real coverage gaps, correctness-relevant but not crash-level

- **[DERIBIT]** 273 real rows tagged `venue=DERIBIT` (not `DERIBIT-COMBO`) with `instrument_type=COMBO`
  in the same-day production parquet — possible regression/duplicate-source, root cause NOT traced
  (needs a follow-up investigation, flagged not fixed).
- **[DERIBIT-COMBO]** no live WS connector registered for this venue at all — combo trades/book cannot
  be captured live, only via batch.
- **[OKX]** `market-tick-data-service/.../live/connectors/okx_ws.py` — OKX-SWAP trades registered under
  the wrong venue key (`OKX-FUTURES`); `instrument_type` hardcoded regardless of swap vs dated future.
- **[BYBIT]** `parsing.py:348-371` (`_resolve_base_quote`) — `base_asset`/`underlying` polluted for
  Bybit linear dated futures (`BTCUSDT` treated as a bare base asset).
- **[COINBASE]** `unified-api-contracts/.../venue_constants.py:433` —
  `INSTRUMENT_TYPES_BY_VENUE["COINBASE-FUTURES"]` omits the real `SPOT_PAIR` (19 rows, 15 MVP) and
  declares a phantom `FUTURE` that has never existed — same phantom-declaration bug class as the
  BYBIT/OKX SPOT_PAIR fix already shipped this session.
- **[SMALL_DERIV]** `venue_mapping.py:830-831` — `("HUOBI-FUTURES","PERPETUAL"):"huobi-dm"` is wrong —
  that Tardis slug is Coin-M Futures only (0 real perpetuals); real Huobi perps live on the unreferenced
  `huobi-dm-swap`/`huobi-dm-linear-swap` slugs.
- **[SMALL_DERIV]** `parsing.py:396-427` — no `cryptofacilities` branch — every Kraken Futures `PI_`/`FI_`
  inverse product mislabeled `linear`.
- **[SMALL_DERIV]** `parsing.py:463 (_passes_asset_filter)` + `cefi_instrument_universe.py:131-133` —
  rejects any quote asset outside `{USDT,USDC,USD}` — 8 real Bitfinex BTC-margined perps silently dropped.
- **[LENDING]** `instruments-service/.../engine/orchestrator/defi.py:102-110` — VENUS/BENQI/RADIANT/
  EULER_V2 adapters are functional (confirmed via direct call) but never invoked by the production
  orchestrator — 0 real catalogue rows despite working code.
- **[POOLS]** `curve.py:30` (`_CURVE_API_TEMPLATE`) — only queries Curve's "main" registry, missing
  factory/factory-crypto pools — roughly a 94% real undercount.
- **[POOLS]** `curve.py:157-160`, `balancer.py:219-222` — both hardcode `coins[0]`/`coins[1]` — silently
  drop the 3rd+ token of any multi-asset pool (e.g. Curve's 3Pool).
- **[POOLS]** `uniswap_v3.py:392-401,490-492` — SushiSwap-Arbitrum's `instrument_key` never includes
  `pool_address` and hardcodes fee tier — 4 real, distinct pools collapse onto one key (real
  double-counting/data-loss risk).
- **[POOLS]** `UNISWAP_V3-BASE` subgraph dark for 5 consecutive days — likely stale/abandoned subgraph,
  same class as the previously-documented AAVE_V3-OPTIMISM case (root cause not investigated, no Graph
  API key available).
- **[RESTAKING_SPOT]** `karak.py:46,52,60` — all 3 Karak vault addresses have zero deployed bytecode
  (fabricated addresses); `symbiotic.py:54,66` — 2 of 4 Symbiotic vault addresses are also fabricated.
- **[RESTAKING_SPOT]** `lst_renzo_adapter.py:158` — ezETH address typo (41 hex chars instead of 40) —
  `Web3.to_checksum_address()` raises `ValueError`.
- **[RESTAKING_SPOT]** `lst_renzo_adapter.py`/`lst_puffer_adapter.py` `_sample_oracle_prices_at_blocks`
  (~294-324) — misses `web3.exceptions.ContractLogicError`, so an AAVE-oracle revert crashes before
  reaching the DefiLlama fallback path.
- **[GMX_DRIFT]** `liquidations_handler.py:205-219` — `_GMX_LIQUIDATIONS_QUERY` requests non-existent
  GraphQL sub-fields; errors are treated as `return None`, indistinguishable from honest zero — this
  fetch has never once succeeded, silently.
- **[GMX_DRIFT]** `uniswap_v3.py:296-314,303,308-309` — GMX's real 9-token vault is truncated to a
  fabricated 2-token pool with a made-up default fee of `"0.3"`.
- **[GMX_DRIFT]** GMX V2 (where essentially all real current GMX liquidity actually lives) is not
  integrated at all — only the abandoned V1 vault is reachable. Real coverage gap, no plan surfaced.
- **[GMX_DRIFT]** `solana_defi_drift.py:67` → `solana_defi_handler.py:376` — dead `/stats/markets`
  endpoint (404); the real fix (Drift SDK constants) already landed in instruments-service's `drift.py`
  but was never propagated to MTDS.
- **[TRADFI]** `databento/adapter.py:764-766` — CME event contracts assumed `instrument_class="BAG"`;
  real Databento returns C/P — 0 real `EVENT_CONTRACT` rows exist anywhere, all silently mistyped OPTION.
- **[TRADFI]** `umi_tick_provider.py:123,493,499` — ICE/CBOE index instruments (Yahoo-sourced) fall
  through to Databento instead of an explicit Yahoo early-return — fails silently, empty, no error.
- **[TRADFI]** production tradfi catalogue is massively stale vs the fixed adapter code: ICE
  16,145/16,146 rows orphaned; CBOE 37,474/37,563 stale; NASDAQ+NYSE 318/589 `SPOT_PAIR` stale;
  duplicate stale `CBOE:INDEX:VIX` row — needs a catalogue purge/rebuild, not a code fix.
- **[TRADFI]** `_umi_yahoo.py` (`fetch_yahoo_fx`, `fetch_yahoo_equities`) — neither respects the
  `instrument_ids` filter — always fetches the full static registry; means `KRX:INDEX:KOSPI-USD` can
  never be reached even in principle until this is fixed.
- **[SPORTS]** `transfermarkt.py TransfermarktAdapter.get_teams()` (~215-256) +
  `unified-api-contracts/.../normalize.py:60-73` — real per-player market values are fetched then
  discarded by the wrong normalize function; the CORRECT function (`normalize_player_values()`,
  normalize.py:92-130) is fully implemented and unit-tested but has ZERO production call sites — 0 of
  5,784 rows have real player-level data despite working code sitting unused.
- **[PREDICTION]** `kalshi_adapter.py` — `parse_order_book()` schema is correct but has no production
  call site — `book_snapshot_5` is simply not wired for Kalshi (trades-only capture today).

### P2/P3 — minor, cosmetic, or doc-drift (full list; batch-fixable)

- `_instrument_enums.py` vs `solana_defi_handler.py:338-339` — `SOLANA_LENDING` type declared but
  MARGINFI/SOLEND use generic `LENDING` — naming inconsistency only.
- `balancer.py` fetches real `pool.type` (WEIGHTED/STABLE/COMPOSABLE_STABLE/GYROE) but
  `_pool_to_record` never reads it — discarded, not used.
- `venue_adapter_keys.py` — `JUPITER-SOLANA` missing even the `NO_ADAPTER_YET` sentinel — registry
  consistency only.
- `vault_idle_adapter.py:32`, `restaking_jito_adapter.py:38` — correct DefiLlama slugs, but IDLE/
  JITORESTAKING are simply absent from DefiLlama's `/pools` dataset — always empty, a data-quality gap
  not a code defect (needs an operator decision: alternate feed, or accept permanently empty).
- `solblaze.py:44` — exchange_rate fallback endpoint is dead (404); real endpoint is `/api/v1/apy`.
- `lido.py:90/94, etherfi.py:83/87, solblaze.py:95/98` + MTDS `lst_*_adapter.py` — `instrument_key`
  literal `LST` disagrees with the same record's own `instrument_type=YIELD_BEARING` field; IS and MTDS
  also disagree with each other (`YIELD_BEARING` vs `LST`) for the identical token.
- `_defi.py` `SUBGRAPH_IDS:62-224` never registers `across`/`stargate` — `bridge_events` is permanently
  dead code for both.
- `restaking_karak_adapter.py:32` — wrong DefiLlama slug (`karak-network` vs `karak`); moot since the
  correct slug also has 0 pools.
- `bridge_events_handler.py` (~256) — Across deposit `symbol` hardcoded `"USDC"` regardless of the real
  `inputToken` — currently unreachable (blocked by the subgraph gap above) but a latent corruption risk
  if that gap is ever fixed without also fixing this.
- Roughly 15+ DeFi adapters repo-wide (symbiotic.py:101, karak.py:102, renzo.py:101, kelpdao.py:74,
  puffer.py:75, rocket_pool.py:74, and more) filter on lowercase `"yield_bearing"` instead of the
  canonical `YIELD_BEARING` — dormant today, would silently empty out if ever called canonically.
- IS vs MTDS disagree on RENZO's key shape for the SAME token — IS emits
  `RENZO-ETHEREUM:LST:EZETH`; MTDS emits `RENZO-ETHEREUM:LRT:EZETH@ETHEREUM` — an SSOT drift, vestigial
  but real and reachable.
- `drift.py:87-90` — class docstring still claims the dead public Data API is used; contradicted by the
  module docstring 3 lines above it.
- Grammar-only: `:PERP:` (IS canonical) vs `:PERPETUAL:` (MTDS docstrings/tests) coexist inconsistently
  for the 5 non-Tardis DEX-perp venues.
- `understat_xg_shots.fixture_id` always null (27/27 sampled) — real join key is `match_id`.
- `progressive_stats.team` always `''` (204/204 sampled) on the SOCCER_FOOTBALL_INFO provider.
- CME/ICE live combo-spread legs are dropped with a WARNING-only log, no failure signal surfaced.
- `TardisAdapter.download_csv()` crashes with `RuntimeError: Event logging not initialized` when called
  outside full `ServiceBootstrap` — likely a test-harness artifact, not verified further (out of scope).
- `instruments-service/.../adapters/cefi/kalshi_perp.py:50,59` — `_KALSHI_BASE_URL` still points at the
  wrong "events" host; `_REPOINT_PENDING=True` still short-circuits both methods to `[]` (tracked
  primarily in [[../prediction_capture_incident_remediation_2026_07_06]] Workstream B — cross-referenced
  here, not duplicated as a separate fix item).
- `/margin/markets/{ticker}/trades` 404s; the real working path is `/margin/trades?ticker={ticker}` —
  Phase 2's plan text in the KALSHI-PERP remediation plan needs this endpoint-shape correction before
  implementation (also tracked there).

## 4. Open questions (not fully resolved by this pass)

1. Root cause of the 273 mistagged `venue=DERIBIT`/`instrument_type=COMBO` rows — unidentified.
2. OKX options wiring needs a `TARDIS_API_KEY` to fully verify end-to-end (blocked on credentials).
3. LIGHTER-ZKSYNC's fix (tracked in [[non_tardis_dexperp_venue_data_status_smoketest_2026_07_07]])
   exists only as uncommitted working-tree changes as of this smoke test — needs commit + plan-flip
   before it counts as shipped (a separate background agent was already dispatched for this fix;
   status pending as of this doc's filing).
4. MARGINFI/SOLEND have no reference-data adapter of any kind — worse than the other 5 lending
   protocols checked; no IS-side coverage plan surfaced.
5. Whether purging/regenerating the stale TradFi catalogue (ICE 16,146→~1 real rows, CBOE 37,563→~89)
   is already scheduled, or needs a new migration plan — unaddressed.
6. Whether ODDS_API's total absence from instruments-service (IS has no reference-data adapter for it,
   only MTDS captures its tick data) is a deliberate division of labor or an accidental gap.

## Todos

- [ ] [TRIAGE] P0. Work through the P0 list above (crash risks + silent-corruption HARD RULE violations
      + complete venue-universe gaps) and fix each — HUOBI-SPOT/HUOBI-FUTURES/BITSTAMP-SPOT missing
      from the venue universe and ETHENA's fabricated oracle_prices/apy are the two most likely to be
      quick, isolated fixes; the OKX options wiring and the 5 lending-protocol invalid-enum fixes
      (FLUID/VENUS/BENQI/RADIANT/EULER_V2 — see [[defi_lending_atoken_debttoken_instrument_split_2026_07_07]])
      are larger and should follow that doc's existing todo structure rather than being re-planned here.
- [ ] [FIX] P0. Fix the DERIBIT live-WS dash-count misclassification (`deribit_ws.py:100`) — a real
      live-vs-batch determinism violation, narrow and well-diagnosed.
- [ ] [FIX] P0. Fix the POLYMARKET book_snapshot_5 schema mismatch (`schemas.py:74-75`,
      `bids`/`asks` should be `list[dict]` not `list[list[float]]`) — currently crashes an entire
      date's capture, not just the affected market.
- [ ] [VERIFY] P1. Root-cause the 273 mistagged DERIBIT/COMBO rows (open question #1) before deciding
      whether this needs a code fix or is a one-off historical artifact.
- [ ] [FIX] P1. Fix the OKX/BYBIT margin-type mislabeling (`parsing.py` — inverse tagged linear in both
      cases) — P&L-relevant misclassification, same severity class as the lending a-token/debt-token
      issue.
- [ ] [FIX] P1. Wire VENUS/BENQI/RADIANT/EULER_V2's already-functional adapters into the production
      orchestrator (`engine/orchestrator/defi.py:102-110`) — code works, it's just never invoked.
- [ ] [FIX] P1. Fix Curve's factory-pool undercount (~94% missing) and the Curve/Balancer 3rd-token drop
      — both are real, sizeable DeFi pool-coverage gaps.
- [ ] [FIX] P2. Batch-fix the ~15+ DeFi adapters filtering on lowercase `"yield_bearing"` instead of
      canonical `YIELD_BEARING` — dormant today but a real landmine if ever triggered.
- [ ] [DECISION] P1. Operator decision needed on IDLE/JITORESTAKING/SYMBIOTIC/KARAK's yield data — all
      4 have correct code pointed at DefiLlama's `/pools` dataset, which simply has zero rows for them.
      Source an alternate feed, or accept structurally-empty as the final state for these 4.
- [ ] [DECISION] P1. Operator decision needed on GMX V2 coverage — real current GMX liquidity lives
      there and it's entirely unintegrated; only the abandoned V1 vault is reachable today.
- [ ] [CODE] P2. Update both drilldown mockups (instruments-definitions + MTDS data-type) with the real
      dimension sample bank and capability matrix from this smoke test — in progress as a direct
      follow-on to this doc.
- [ ] [FIX] P3. Sweep the full P2/P3 minor/cosmetic list above in one batch pass (doc drift, dead
      sentinels, discarded-but-fetched fields, grammar inconsistencies) — low individual value, cheap
      to batch together.

## Progress Log

- **2026-07-07** — Filed after a 17-cluster parallel smoke test (each cluster ran real adapter
  execution against real production data / live APIs, not code-reading alone) covering every live
  CeFi venue, every DeFi protocol category, all 7 TradFi venues, all 7 Sports providers, and both
  Prediction venues. Found 59 distinct real bugs plus a full real instrument-dimension sample bank and
  MTDS capability matrix. This is the master record for the full sweep — no code changed yet beyond
  what's already tracked in the cross-referenced lending/DEX-perp/Kalshi-perp docs; fixes are queued
  above by priority.
