---
doc_type: issue
title:
  "Full MTDS + instruments-service adapter smoke test — 59 real bugs found across CeFi/DeFi/TradFi/Sports/Prediction,
  plus a real instrument-dimension sample bank and MTDS capability matrix"
summary:
  'Operator asked for a comprehensive smoke test of every single MTDS + instruments-service adapter ("to ensure no more
  adapter issues") plus a representative real instrument_id sample per real structural dimension (margin type
  coin/non-coin, inverse/linear perpetuals, futures, options with calls/puts) for every venue — explicitly "so the
  mockup gives this info on time," before the real UAC/instruments-service migration work starts. Ran a 17-cluster
  parallel investigation (one cluster per venue/protocol family) covering every live CeFi venue, every DeFi protocol
  category (lending, pools, yield/staking, restaking, GMX/Drift), all 7 TradFi venues, all 7 Sports providers, and both
  Prediction venues — each cluster actually executed real adapters (not just read code) and pulled real production/live
  data. Found 59 distinct real bugs (several are crash risks or silent-corruption violations, not just coverage gaps),
  confirmed a large real instrument_id sample bank covering every real dimension per venue, and produced a full MTDS
  data_type-capability matrix. This is the single largest findings batch of the session — logged here as the master
  record; smaller, more specific issue docs already filed this session (lending a-token/debt-token split, non-Tardis
  DEX-perp smoke test, KALSHI-PERP plan) are cross-referenced rather than duplicated.'
status: open
nature: notes
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data, meta]
repos: [market-tick-data-service, instruments-service, unified-api-contracts, unified-trading-library]
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
source:
  'Operator, 2026-07-07: "you are gonna smoke test every single MTDS and IS to ensure no more adaptor issues and update
  mock MTDS and IS with updated source of actual truth given the tests... dump representative mock instrument id for
  every dimension of instruments... for the marketing data service, I want to effectively have validated through you
  that we are able to download every data type and instrument type." 17-cluster parallel workflow, each cluster running
  real adapter execution + real production data reads, not guessing.'
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

> **NOTIFY-OPERATOR class finding — largest single batch this session, spans every MTDS/IS adapter, includes multiple P0
> crash risks and at least one silent-corruption HARD RULE violation.** This is the master record; work items are
> prioritized below but NOT all fixed yet — most are logged findings, not shipped fixes. Cross-referenced docs above
> cover lending (already filed) and the 5 non-Tardis DEX-perp venues (already filed) in more depth; this doc covers
> everything else plus the full picture.

## 1. Real instrument-dimension sample bank (selected highlights — full bank in Progress Log / workflow journal)

**DERIBIT has BOTH inverse (USD-margined) and linear (USDC-margined) products for PERPETUAL, FUTURE, AND OPTION alike**
— this corrects an assumption made earlier this session (that Deribit was single-margin-type). Real samples:
`DERIBIT:PERPETUAL:BTC-USD` (inverse) / `DERIBIT:PERPETUAL:BTC-USDC` (linear); `DERIBIT:OPTION:BTC-10JUL26-48000-C`/`-P`
(inverse call/put) and `DERIBIT:OPTION:BTC_USDC-10JUL26-48000-C`/`-P` (linear call/put);
`DERIBIT:COMBO:BTC-CS-17JUL26-63000_65000`.

Other confirmed real dimension coverage: BINANCE-DELIVERY (coin-margined inverse) vs BINANCE-FUTURES (linear);
OKX-SWAP/-FUTURES coin-margined vs linear (though margin_type itself is mislabeled — see bugs); BYBIT inverse PERPETUAL
exists but is mistagged linear; COINBASE-FUTURES genuinely has no FUTURE/OPTION/ inverse product (verified 3 ways, not
just absent); KRAKEN-FUTURES/BITFINEX-FUTURES have real inverse+linear splits; CME has real
FUTURE/OPTION(call+put)/COMBO but EVENT_CONTRACT is always misclassified as OPTION (0 real EVENT_CONTRACT rows exist
anywhere); PENDLE has a real 3-way split (PT/YT/SY) — the richest dimension split found in DeFi; POLYMARKET's
book_snapshot_5 grain is genuinely two instruments per market (YES token_id + NO token_id) while its trades grain is one
(condition_id) — a real, deliberate dual-grain design, not an inconsistency.

Full per-venue sample tables (CeFi/DeFi/TradFi/Sports/Prediction) are in the workflow synthesis — transcribed into both
mockups as the next step (see Todos).

## 2. MTDS capability matrix — selected highlights

Most venues/dimensions are WORKS-NOW. Standout non-working ones: FLUID lending_indices 100% broken; ETHENA
oracle_prices/apy always fabricated (1.0/0.0, never a real call); GMX perp_funding always synthetic (native funding
schema fails silently, 100% of rows are OI-imbalance-derived, not real); GMX liquidations always fails (schema mismatch,
recorded as honest zero — indistinguishable from real absence); DRIFT perp_funding dead endpoint; HUOBI-FUTURES fully
unenumerable in production (raw data confirmed working when called directly — pure wiring gap); ICE/CBOE INDEX
data_types fail silently (routed to Databento instead of Yahoo, empty with no error); POLYMARKET book_snapshot_5 crashes
the entire date's capture (schema mismatch, uncaught).

## 3. Full bug list (59 items, grouped by cluster, priority-tagged)

### P0 — crash risks, silent-corruption HARD RULE violations, or complete coverage gaps

- **[DERIBIT]** `market_tick_data_service/live/connectors/deribit_ws.py:100` — dash-count heuristic misclassifies every
  dated future trade as OPTION on the LIVE path (batch classifier is correct) — a real live-vs-batch determinism
  violation.
- **[LENDING]** `fluid.py:113, venus.py:105, benqi.py:98, radiant.py:121, euler_v2.py:93` — all 5 use hardcoded
  `"LENDING_MARKET"`, not a valid `InstrumentType` enum member — same crash risk as COMPOUND_V3/MORPHO (already filed in
  [[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]) — **confirms that todo's open question: none of the 7
  not-yet-verified lending protocols has a real A_TOKEN/DEBT_TOKEN split.**
- **[LENDING]** `market_tick_data_service/.../defi/fluid_adapter.py:394,399-401,422` — revert-data guard never fires
  (`ContractCustomError` not caught) — FLUID's `lending_indices` is 100% broken in practice.
- **[YIELD_STAKING]** `market-tick-data-service/.../defi/ethena_adapter.py:249-268,270-285` — `oracle_prices`/`apy`
  unconditionally return fabricated hardcoded values (`1.0`/`0.0`) under fake source tags — a direct violation of the
  workspace's "never silent placeholders" HARD RULE.
- **[PREDICTION]** `unified_api_contracts/external/polymarket/schemas.py:74-75` — `bids`/`asks` typed
  `list[list[float]]` but the real API returns `list[dict]` — `ValidationError` on every real order-book fetch, uncaught
  through the full call chain (`polymarket_adapter.py:207,459-498,761-800`), **crashing the entire date's
  `book_snapshot_5` capture**, not just that one market.
- **[SMALL_SPOT/SMALL_DERIV]** `unified_api_contracts/registry/market_data_categories.py:223-271`
  (`VENUES_BY_ASSET_GROUP["cefi"]`) + `venue_adapter_keys.py` + `venue_mapping.py:169-205` — `HUOBI-SPOT`,
  `HUOBI-FUTURES`, `BITSTAMP-SPOT` are missing from the venue universe entirely — never fetched at all in production
  despite real, working adapter code underneath (confirmed by direct calls).
- **[OKX]** `instruments_service/reference_data/router.py:176` area — no `okex-options` routing anywhere — 246,000+ real
  option symbols never wired into the capture pipeline.
- **[OKX]** `instruments-service/.../adapters/cefi/tardis/parsing.py:388-427` — margin_type inverted for every
  OKX-SWAP/OKX-FUTURES derivative (coin-margined tagged linear and vice versa) — a real P&L-relevant misclassification,
  same class as the lending a-token/debt-token issue.
- **[BYBIT]** `parsing.py:396-427 (_infer_margin_type)` — no Bybit branch — every inverse perpetual defaults to LINEAR
  (same margin-type misclassification class as OKX above).
- **[BYBIT]** `parsing.py:541-567 (_split_symbol)` + `adapter.py:712-723` — cannot parse non-dashed inverse-future
  symbols (`BTCUSDU26`) — 46 real products silently dropped from the catalogue entirely.

### P1 — real bugs, real coverage gaps, correctness-relevant but not crash-level

- **[DERIBIT]** 273 real rows tagged `venue=DERIBIT` (not `DERIBIT-COMBO`) with `instrument_type=COMBO` in the same-day
  production parquet — possible regression/duplicate-source, root cause NOT traced (needs a follow-up investigation,
  flagged not fixed).
- **[DERIBIT-COMBO]** no live WS connector registered for this venue at all — combo trades/book cannot be captured live,
  only via batch.
- **[OKX]** `market-tick-data-service/.../live/connectors/okx_ws.py` — OKX-SWAP trades registered under the wrong venue
  key (`OKX-FUTURES`); `instrument_type` hardcoded regardless of swap vs dated future.
- **[BYBIT]** `parsing.py:348-371` (`_resolve_base_quote`) — `base_asset`/`underlying` polluted for Bybit linear dated
  futures (`BTCUSDT` treated as a bare base asset).
- **[COINBASE]** `unified-api-contracts/.../venue_constants.py:433` — `INSTRUMENT_TYPES_BY_VENUE["COINBASE-FUTURES"]`
  omits the real `SPOT_PAIR` (19 rows, 15 MVP) and declares a phantom `FUTURE` that has never existed — same
  phantom-declaration bug class as the BYBIT/OKX SPOT_PAIR fix already shipped this session.
- **[SMALL_DERIV]** `venue_mapping.py:830-831` — `("HUOBI-FUTURES","PERPETUAL"):"huobi-dm"` is wrong — that Tardis slug
  is Coin-M Futures only (0 real perpetuals); real Huobi perps live on the unreferenced
  `huobi-dm-swap`/`huobi-dm-linear-swap` slugs.
- **[SMALL_DERIV]** `parsing.py:396-427` — no `cryptofacilities` branch — every Kraken Futures `PI_`/`FI_` inverse
  product mislabeled `linear`.
- **[SMALL_DERIV]** `parsing.py:463 (_passes_asset_filter)` + `cefi_instrument_universe.py:131-133` — rejects any quote
  asset outside `{USDT,USDC,USD}` — 8 real Bitfinex BTC-margined perps silently dropped.
- **[LENDING]** `instruments-service/.../engine/orchestrator/defi.py:102-110` — VENUS/BENQI/RADIANT/ EULER_V2 adapters
  are functional (confirmed via direct call) but never invoked by the production orchestrator — 0 real catalogue rows
  despite working code.
- **[POOLS]** `curve.py:30` (`_CURVE_API_TEMPLATE`) — only queries Curve's "main" registry, missing
  factory/factory-crypto pools — roughly a 94% real undercount.
- **[POOLS]** `curve.py:157-160`, `balancer.py:219-222` — both hardcode `coins[0]`/`coins[1]` — silently drop the 3rd+
  token of any multi-asset pool (e.g. Curve's 3Pool).
- **[POOLS]** `uniswap_v3.py:392-401,490-492` — SushiSwap-Arbitrum's `instrument_key` never includes `pool_address` and
  hardcodes fee tier — 4 real, distinct pools collapse onto one key (real double-counting/data-loss risk).
- **[POOLS]** `UNISWAP_V3-BASE` subgraph dark for 5 consecutive days — likely stale/abandoned subgraph, same class as
  the previously-documented AAVE_V3-OPTIMISM case (root cause not investigated, no Graph API key available).
- **[RESTAKING_SPOT]** `karak.py:46,52,60` — all 3 Karak vault addresses have zero deployed bytecode (fabricated
  addresses); `symbiotic.py:54,66` — 2 of 4 Symbiotic vault addresses are also fabricated.
- **[RESTAKING_SPOT]** `lst_renzo_adapter.py:158` — ezETH address typo (41 hex chars instead of 40) —
  `Web3.to_checksum_address()` raises `ValueError`.
- **[RESTAKING_SPOT]** `lst_renzo_adapter.py`/`lst_puffer_adapter.py` `_sample_oracle_prices_at_blocks` (~294-324) —
  misses `web3.exceptions.ContractLogicError`, so an AAVE-oracle revert crashes before reaching the DefiLlama fallback
  path.
- **[GMX_DRIFT]** `liquidations_handler.py:205-219` — `_GMX_LIQUIDATIONS_QUERY` requests non-existent GraphQL
  sub-fields; errors are treated as `return None`, indistinguishable from honest zero — this fetch has never once
  succeeded, silently.
- **[GMX_DRIFT]** `uniswap_v3.py:296-314,303,308-309` — GMX's real 9-token vault is truncated to a fabricated 2-token
  pool with a made-up default fee of `"0.3"`.
- **[GMX_DRIFT]** GMX V2 (where essentially all real current GMX liquidity actually lives) is not integrated at all —
  only the abandoned V1 vault is reachable. Real coverage gap, no plan surfaced.
- **[GMX_DRIFT]** `solana_defi_drift.py:67` → `solana_defi_handler.py:376` — dead `/stats/markets` endpoint (404); the
  real fix (Drift SDK constants) already landed in instruments-service's `drift.py` but was never propagated to MTDS.
- **[TRADFI]** `databento/adapter.py:764-766` — CME event contracts assumed `instrument_class="BAG"`; real Databento
  returns C/P — 0 real `EVENT_CONTRACT` rows exist anywhere, all silently mistyped OPTION.
- **[TRADFI]** `umi_tick_provider.py:123,493,499` — ICE/CBOE index instruments (Yahoo-sourced) fall through to Databento
  instead of an explicit Yahoo early-return — fails silently, empty, no error.
- **[TRADFI]** production tradfi catalogue is massively stale vs the fixed adapter code: ICE 16,145/16,146 rows
  orphaned; CBOE 37,474/37,563 stale; NASDAQ+NYSE 318/589 `SPOT_PAIR` stale; duplicate stale `CBOE:INDEX:VIX` row —
  needs a catalogue purge/rebuild, not a code fix.
- **[TRADFI]** `_umi_yahoo.py` (`fetch_yahoo_fx`, `fetch_yahoo_equities`) — neither respects the `instrument_ids` filter
  — always fetches the full static registry; means `KRX:INDEX:KOSPI-USD` can never be reached even in principle until
  this is fixed.
- **[SPORTS]** `transfermarkt.py TransfermarktAdapter.get_teams()` (~215-256) +
  `unified-api-contracts/.../normalize.py:60-73` — real per-player market values are fetched then discarded by the wrong
  normalize function; the CORRECT function (`normalize_player_values()`, normalize.py:92-130) is fully implemented and
  unit-tested but has ZERO production call sites — 0 of 5,784 rows have real player-level data despite working code
  sitting unused.
- **[PREDICTION]** `kalshi_adapter.py` — `parse_order_book()` schema is correct but has no production call site —
  `book_snapshot_5` is simply not wired for Kalshi (trades-only capture today).

### P2/P3 — minor, cosmetic, or doc-drift (full list; batch-fixable)

- `_instrument_enums.py` vs `solana_defi_handler.py:338-339` — `SOLANA_LENDING` type declared but MARGINFI/SOLEND use
  generic `LENDING` — naming inconsistency only.
- `balancer.py` fetches real `pool.type` (WEIGHTED/STABLE/COMPOSABLE_STABLE/GYROE) but `_pool_to_record` never reads it
  — discarded, not used.
- `venue_adapter_keys.py` — `JUPITER-SOLANA` missing even the `NO_ADAPTER_YET` sentinel — registry consistency only.
- `vault_idle_adapter.py:32`, `restaking_jito_adapter.py:38` — correct DefiLlama slugs, but IDLE/ JITORESTAKING are
  simply absent from DefiLlama's `/pools` dataset — always empty, a data-quality gap not a code defect (needs an
  operator decision: alternate feed, or accept permanently empty).
- `solblaze.py:44` — exchange_rate fallback endpoint is dead (404); real endpoint is `/api/v1/apy`.
- `lido.py:90/94, etherfi.py:83/87, solblaze.py:95/98` + MTDS `lst_*_adapter.py` — `instrument_key` literal `LST`
  disagrees with the same record's own `instrument_type=YIELD_BEARING` field; IS and MTDS also disagree with each other
  (`YIELD_BEARING` vs `LST`) for the identical token.
- `_defi.py` `SUBGRAPH_IDS:62-224` never registers `across`/`stargate` — `bridge_events` is permanently dead code for
  both.
- `restaking_karak_adapter.py:32` — wrong DefiLlama slug (`karak-network` vs `karak`); moot since the correct slug also
  has 0 pools.
- `bridge_events_handler.py` (~256) — Across deposit `symbol` hardcoded `"USDC"` regardless of the real `inputToken` —
  currently unreachable (blocked by the subgraph gap above) but a latent corruption risk if that gap is ever fixed
  without also fixing this.
- Roughly 15+ DeFi adapters repo-wide (symbiotic.py:101, karak.py:102, renzo.py:101, kelpdao.py:74, puffer.py:75,
  rocket_pool.py:74, and more) filter on lowercase `"yield_bearing"` instead of the canonical `YIELD_BEARING` — dormant
  today, would silently empty out if ever called canonically.
- IS vs MTDS disagree on RENZO's key shape for the SAME token — IS emits `RENZO-ETHEREUM:LST:EZETH`; MTDS emits
  `RENZO-ETHEREUM:LRT:EZETH@ETHEREUM` — an SSOT drift, vestigial but real and reachable.
- `drift.py:87-90` — class docstring still claims the dead public Data API is used; contradicted by the module docstring
  3 lines above it.
- Grammar-only: `:PERP:` (IS canonical) vs `:PERPETUAL:` (MTDS docstrings/tests) coexist inconsistently for the 5
  non-Tardis DEX-perp venues.
- `understat_xg_shots.fixture_id` always null (27/27 sampled) — real join key is `match_id`.
- `progressive_stats.team` always `''` (204/204 sampled) on the SOCCER_FOOTBALL_INFO provider.
- CME/ICE live combo-spread legs are dropped with a WARNING-only log, no failure signal surfaced.
- `TardisAdapter.download_csv()` crashes with `RuntimeError: Event logging not initialized` when called outside full
  `ServiceBootstrap` — likely a test-harness artifact, not verified further (out of scope).
- `instruments-service/.../adapters/cefi/kalshi_perp.py:50,59` — `_KALSHI_BASE_URL` still points at the wrong "events"
  host; `_REPOINT_PENDING=True` still short-circuits both methods to `[]` (tracked primarily in
  [[../prediction_capture_incident_remediation_2026_07_06]] Workstream B — cross-referenced here, not duplicated as a
  separate fix item).
- `/margin/markets/{ticker}/trades` 404s; the real working path is `/margin/trades?ticker={ticker}` — Phase 2's plan
  text in the KALSHI-PERP remediation plan needs this endpoint-shape correction before implementation (also tracked
  there).

## 3a. Operator decisions — structurally-empty / do-not-integrate DeFi coverage gaps (2026-07-10)

Added retroactively (2026-07-10 doc-integrity pass) — the 2026-07-10 flip commit's own todos and Progress Log entry both
said "see new § 3a below/above" but no such section was ever written, leaving both cross-references pointing at nothing.
The operator decisions themselves were real (recorded only as Progress Log prose); this section is the dedicated home
the todos already promised.

- **IDLE / JITORESTAKING / SYMBIOTIC / KARAK yield data — accept structurally empty.** DefiLlama's `/pools` dataset has
  zero rows for these 4 protocols (confirmed, not a code defect — see P2/P3 list above: `vault_idle_adapter.py:32`,
  `restaking_jito_adapter.py:38`). Operator decision: do not chase an alternate feed; accept the gap as
  permanent/structural. **This explicitly does NOT waive** the separately-tracked fabricated vault-address bugs (Karak
  3/3 addresses have zero deployed bytecode, Symbiotic 2/4 addresses likewise) — those remain open P1 findings
  regardless of the DefiLlama-emptiness decision; a fabricated address is a correctness bug independent of whether the
  resulting query would return rows.
- **GMX V2 coverage — do not integrate.** GMX V2 holds effectively all of GMX's real current on-chain liquidity (the
  only V1 vault currently captured is largely abandoned), but the operator decided NOT to integrate V2 this pass. GMX
  capture stays scoped to the V1 vault; the real V2 coverage gap remains open (P1 above), tracked as a known, accepted
  gap rather than a silently-missed one.

## 4. Open questions (not fully resolved by this pass)

1. Root cause of the 273 mistagged `venue=DERIBIT`/`instrument_type=COMBO` rows — unidentified.
2. OKX options wiring needs a `TARDIS_API_KEY` to fully verify end-to-end (blocked on credentials).
3. LIGHTER-ZKSYNC's fix (tracked in [[non_tardis_dexperp_venue_data_status_smoketest_2026_07_07]]) exists only as
   uncommitted working-tree changes as of this smoke test — needs commit + plan-flip before it counts as shipped (a
   separate background agent was already dispatched for this fix; status pending as of this doc's filing).
4. MARGINFI/SOLEND have no reference-data adapter of any kind — worse than the other 5 lending protocols checked; no
   IS-side coverage plan surfaced.
5. Whether purging/regenerating the stale TradFi catalogue (ICE 16,146→~1 real rows, CBOE 37,563→~89) is already
   scheduled, or needs a new migration plan — unaddressed.
6. Whether ODDS_API's total absence from instruments-service (IS has no reference-data adapter for it, only MTDS
   captures its tick data) is a deliberate division of labor or an accidental gap.

## Todos

- [x] [TRIAGE] P0. Work through the P0 list above — HUOBI-SPOT/HUOBI-FUTURES/BITSTAMP-SPOT venue registration
      **BLOCKED-OPERATOR-DECISION, re-triaged 2026-07-10** (see Progress Log — a fresh dispatch re-checked this and
      found the UAC registry files were git-clean, NOT under live concurrent edit as this session's earlier note
      claimed; the REAL blocker is worse — an SSOT contradiction: `unified-api-contracts@181b5311`, one day earlier
      (2026-07-09), deliberately REMOVED huobi/bitstamp/htx from `venue_mapping.py` + `provider_api_versions.yaml` +
      `venue_tokens.py` + `instrument_validation.py` under the commit message "remove never-captured huobi/bitstamp/htx
      venues from registry + instrument universe" — the direct opposite conclusion this P0 finding reaches. Re-reading
      that diff: the removed entries were orphaned Tardis-slug mappings for venues that were never declared in
      `VENUES_BY_ASSET_GROUP["cefi"]` (so "never-captured" is literally true of that dead code) — this does NOT prove
      the venues themselves are unviable, only that the old half-registration was dead. Neither this doc's original
      2026-07-07 finding nor `instruments_remaining_work_audit_2026_07_10.md`'s "Design: aligned with SSOT, Proceed"
      verdict (§ "3. 59-bug MTDS + IS adapter smoke test") was written with knowledge of 181b5311 — this is a genuinely
      new discovery, not a re-litigation. Per the workspace's SSOT- contradiction HARD RULE, re-adding the venues was
      NOT attempted unilaterally this pass — escalated to the operator instead (see Progress Log for the A/B/C
      framing)); ETHENA fabricated oracle_prices/apy **fixed** — see the new todo below; OKX options wiring + 5
      lending-protocol invalid-enum fixes tracked in [[defi_lending_atoken_debttoken_instrument_split_2026_07_07]] as
      designed.
- [x] [FIX] P0. DERIBIT live-WS dash-count misclassification — **already fixed by a concurrent sibling workflow**,
      `market-tick-data-service@c55c1509` ("correct Deribit FUTURE/OPTION classification by real dash-count"), verified
      2026-07-10 before this session touched anything further in that file (which was mid-refactor by the same sibling —
      left untouched).
- [x] [FIX] P0. POLYMARKET book_snapshot_5 schema mismatch — fixed. `unified-api-contracts@42ce2de3` (new
      `PolymarketBookLevel` schema, `bids`/`asks: list[PolymarketBookLevel]`) + `market-tick-data-service@f4a118be`
      (both Polymarket adapter consumers + normalize.py + 4 tests updated to the real object shape). Root cause
      confirmed: real CLOB API returns `[{"price":...,"size":...}]`, not `[[price,size]]`.
- [x] ✅ [FIX] P0. ETHENA fabricated `oracle_prices`/`apy` placeholders — **fixed and shipped 2026-07-10,
      `market-tick-data-service@9be95ecb`**. `ethena_adapter.py` now calls the real AAVE V3 Oracle via RPC (+ DefiLlama
      Coins API fallback) for `oracle_prices` and reuses the real DefiLlama-yields fetch for `current_apy`, with 10 new
      regression tests (`tests/unit/market_interface/adapters/defi/test_ethena_adapter.py`) guarding against the old
      fabricated constants. Was blocked at the quickmerge ship step by live sibling-agent WIP in
      `unified-trading-library`/`unified-api-contracts`; shipped via the dirty-deps carve-out direct push (those repos
      not touched) once the fix had sat ready long enough to justify it.
- [ ] [VERIFY] P1. Root-cause the 273 mistagged DERIBIT/COMBO rows (open question #1) — not attempted this session (out
      of dispatched scope).
- [x] [FIX] P1. OKX/BYBIT margin-type mislabeling — **already fixed by a concurrent sibling workflow**,
      `instruments-service@176d4610` ("correct Bybit/Kraken-Futures margin-type inference bugs + add @LIN/@INV
      canonical-symbol builder") + the OKX branch in `parsing.py::_infer_margin_type` (docstring cites real live
      evidence 2026-07-09, `_UM`/`_CM` infix logic corrected). Verified 2026-07-10 by reading the current code before
      redoing anything.
- [x] [FIX] P1. Wire VENUS/BENQI/RADIANT/EULER_V2 into the production orchestrator — fixed. UAC side (`defi_venues.py`
      DEFI_VENUE_PHASE flip + `venue_adapter_keys.py` RADIANT-BSC entry): `unified-api-contracts@42ce2de3`. IS side
      (`defi.py` `_build_defi_venues()` + golden-fixture regen): `instruments-service@9b0c1095`. 7 venues flipped
      pipeline→live: RADIANT-ARBITRUM/BSC/ ETHEREUM, VENUS-BSC/ETHEREUM, BENQI-AVALANCHE, EULER_V2-ETHEREUM
      (EULER_V2-ARBITRUM stays pipeline — adapter is Ethereum-only). Both QG-verified full-suite green modulo
      pre-existing concurrent-sibling failures (COINBASE-CDE, OKX-SPOT — confirmed unrelated to this diff).
- [x] [FIX] P1. Curve's factory-pool undercount + Curve/Balancer 3rd-token drop — fixed, `instruments-service@9b0c1095`.
      Curve: switched `main`-only registry to Curve's own combined `all` endpoint (live-verified 2026-07-10: main=49 vs
      all=2372 pools on Ethereum, a 48x undercount — worse than the original ~94% estimate; all 7 configured chains
      confirmed live). Both Curve + Balancer: `instrument_key`/symbol now encodes every pool coin/token, not just the
      first 2.
- [x] [FIX] P2. Batch-fix the ~15+ DeFi adapters filtering on lowercase `"yield_bearing"` — **already fixed by prior
      session work** ("fixed 2026-07-08" per the adapters' own docstrings); verified 2026-07-10, zero lowercase
      `"yield_bearing"` string literals remain anywhere in instruments-service production code.
- [x] [DECISION] P1. IDLE/JITORESTAKING/SYMBIOTIC/KARAK yield data — **operator decision applied**: see new § 3a below.
      Accept structurally empty (DefiLlama has zero rows); the separately-tracked fabricated-vault-address bugs (Karak
      3/3, Symbiotic 2/4) are explicitly NOT waived by this.
- [x] [DECISION] P1. GMX V2 coverage — **operator decision applied**: see new § 3a below. Do not integrate V2; GMX
      capture stays scoped to the V1 vault.
- [ ] [CODE] P2. Update both drilldown mockups — not attempted this session (out of dispatched scope).
- [~] [FIX] P3. P2/P3 minor/cosmetic sweep — partial: `drift.py` class-docstring self-contradiction fixed (real source
  is SDK TS constants, not the dead Data API) and the SolBlaze/BlazeStake dead `/api/v1/exchange_rate` endpoint fixed
  (real live endpoint is `/api/v1/stats`, confirmed live 2026-07-10 — this one was NOT actually dead code,
  `_tier3_bsol_rest` in `solana_lst_archival.py` is a real live production code path that could never succeed before
  this fix; parser + APY unit conversion updated to match, shipped `market-tick-data-service@f4a118be`). Remaining ~13
  items in the P2/P3 list not attempted (low value, several already cross-referenced/deferred elsewhere, some touch
  `instrument_key` format which needs the dedicated canonicalization effort, not a cosmetic batch pass).

## Progress Log

- **2026-07-07** — Filed after a 17-cluster parallel smoke test (each cluster ran real adapter execution against real
  production data / live APIs, not code-reading alone) covering every live CeFi venue, every DeFi protocol category, all
  7 TradFi venues, all 7 Sports providers, and both Prediction venues. Found 59 distinct real bugs plus a full real
  instrument-dimension sample bank and MTDS capability matrix. This is the master record for the full sweep — no code
  changed yet beyond what's already tracked in the cross-referenced lending/DEX-perp/Kalshi-perp docs; fixes are queued
  above by priority.
- **2026-07-10** — Dispatched sub-agent worked the P0/P1/P2/P3 todo list under heavy concurrent multi-agent load (3+
  sibling workflows editing the same UAC registry files all session — 2 real UAC-repo `git stash`/reset sweeps hit this
  session's own uncommitted edits mid-task, both recovered by redoing the edits from scratch, confirmed via
  `git stash show -p` before redoing). Real shipped fixes, all QG-verified (full quality-gates.sh, not scoped) before
  commit, all failures cross-checked against `git blame`/file ownership to confirm zero regression from this diff:
  - **Deribit P0 + OKX/BYBIT margin-type P1**: already fixed by concurrent sibling work before this session started on
    them (`market-tick-data-service@c55c1509`, `instruments-service@176d4610`) — verified by reading current code, not
    re-done.
  - **Polymarket book_snapshot_5 P0** (real crash, live-verified root cause: CLOB API returns
    `[{"price":...,"size":...}]` object levels, not `[[price,size]]` tuples): new `PolymarketBookLevel` schema + both
    MTDS adapter consumers + normalize.py + 5 tests — `unified-api-contracts@42ce2de3`,
    `market-tick-data-service@f4a118be`.
  - **VENUS/BENQI/RADIANT/EULER_V2 orchestrator wiring P1**: 7 venues flipped pipeline→live across
    `_build_defi_venues()` + `DEFI_VENUE_PHASE` + `VENUE_TO_ADAPTER_KEY` (RADIANT-BSC needed an explicit entry — the
    auto-gen loop only trusts registered subgraph_ids, and Radiant's BSC deployment has no verified subgraph even though
    the curated reference-data adapter covers it) — `unified-api-contracts@42ce2de3`, `instruments-service@9b0c1095`.
  - **Curve factory-pool undercount P1**: root cause was worse than estimated — live-verified 2026-07-10 the "main"
    registry is only ~2-4% of Curve's real pool count (49 vs 2372 on Ethereum, 48x). Switched to Curve's own combined
    "all" endpoint (already proven live elsewhere in this workspace). Curve + Balancer 3rd-token drop fixed alongside
    (same commit, `instruments-service@9b0c1095`).
  - **P2/P3 partial**: `drift.py` docstring self-contradiction + SolBlaze/BlazeStake dead `/api/v1/exchange_rate`
    endpoint (real replacement `/api/v1/stats`, confirmed live — this was a real live production code path,
    `_tier3_bsol_rest`, not dead code as first assumed; parser + percent→fraction APY unit conversion fixed to match) —
    `instruments-service@9b0c1095`, `market-tick-data-service@f4a118be`. Confirmed already-fixed by prior session work:
    the ~15+ lowercase `"yield_bearing"` filter items (canonical `YIELD_BEARING` everywhere now, dated "fixed
    2026-07-08" in the adapters' own docstrings). Remaining ~13 P2/P3 items not attempted this pass (several already
    cross-referenced/deferred to other docs; a few touch `instrument_key` format and need the dedicated canonicalization
    effort, not a cosmetic batch).
  - **GMX V2 / IDLE-JITORESTAKING-SYMBIOTIC-KARAK operator decision**: documented in new § 3a above — accept
    structurally-empty/do-not-integrate for all 5 per operator direction; explicitly does NOT waive the
    separately-tracked Karak/Symbiotic fabricated-vault-address bugs.
  - **Not attempted** (out of this pass's dispatched scope): HUOBI-SPOT/HUOBI-FUTURES/BITSTAMP-SPOT venue registration
    (the UAC registry files it touches — `market_data_categories.py`, `venue_adapter_keys.py`, `venue_mapping.py`,
    `venue_constants.py` and 5 more — were under continuous concurrent edit from 3 sibling workflows the entire session;
    a "quick isolated fix" per the original finding turned out to require touching the exact same file set those
    workflows own, so it was deliberately deferred rather than risking a collision — still a real, open P0 gap), ETHENA
    fabricated oracle_prices/apy, OKX options wiring (tracked in the lending-split doc as designed), root-causing the
    273 mistagged DERIBIT/COMBO rows, and the mockup-update todo.
- **2026-07-10 (separate dispatch)** — **COINBASE-FUTURES "genuinely has no FUTURE/OPTION/inverse product" finding (line
  93 above) CONFIRMED correct, real fix shipped** — this was the #3 side of the
  `wsfeedconnector_phase35_gap_2026_07_06.md` #3-vs-#8 conflict (see that doc's own 2026-07-10 Progress Log entry for
  the full resolution). 2 independent live API cross-checks (Tardis 273-symbol `coinbase-international` listing +
  Coinbase's own `api.international.coinbase.com` 301-instrument listing) both confirm ZERO dated FUTURE/OPTION products
  on Coinbase INTX — this finding was right. The real, previously-untracked gap: real dated futures exist on a SEPARATE
  Coinbase product (Coinbase Derivatives Exchange, CDE — 99 live contracts, e.g. `BIT-31JUL26-CDE`, confirmed via
  `api.coinbase.com/api/v3/brokerage/market/products?product_type=FUTURE`), which the gap-004 live connector (§1a #8)
  had built real, working parsing logic for but filed under the wrong venue key. Shipped: `COINBASE-CDE` registered as
  its own venue + new reference-data adapter (`unified-api-contracts@1cafb3c5`, `instruments-service@94512ec3`); the
  live connector re-keyed `coinbase_futures_ws.py` → `coinbase_cde_ws.py` (`market-tick-data-service@cdbbdb9b`);
  `INSTRUMENT_TYPES_BY_VENUE["COINBASE-FUTURES"]` rescoped to `{"PERPETUAL","SPOT_PAIR"}` (dropped the phantom `FUTURE`
  this finding flagged, added the real previously-missing `SPOT_PAIR` noted at line 162 below — 46 real `{BASE}-USDC`
  INTX products, confirmed live). Also confirmed live (2026-07-10 production manifest read,
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`): the pre-fix
  `coinbase_futures_ws.py` connector recorded ZERO real rows under any live pipeline*mode from ship (`mtds@fd436aea`,
  2026-07-06) through the fix — a genuine, confirmed silent capture-gap (all 16,819 real COINBASE-FUTURES manifest rows
  are `batch_tardis`; contrast `live_binance` 4,080 real rows + 5 other real `live*\*` CeFi pipeline_modes that DO exist
  in production).
- **2026-07-10 (separate dispatch, "master record" fresh-context follow-up)** — Re-verified this whole doc against
  current code before touching anything (per-SHA verification: all previously-claimed commits confirmed real and
  matching their claimed content). Two real outcomes this pass:
  - **ETHENA fabricated `oracle_prices`/`apy` placeholders — code fix complete + QG-green, BUT NOT YET SHIPPED (blocked,
    see below).** Root cause confirmed unchanged from the original finding:
    `market_tick_data_service/market_interface/adapters/defi/ethena_adapter.py` — `_fetch_oracle_prices` returned a
    hardcoded `price_usd: 1.0` and `_fetch_current_apy` returned a hardcoded `apy: 0.0`, both tagged with real-looking
    source strings despite no real fetch ever happening. Fix: `_fetch_oracle_prices` now calls the REAL AAVE V3 Oracle
    (`getAssetPrice`, address `0x54586bE62E3c3580375aE3723C145253060Ca0C2`) via the same RPC pattern already proven live
    elsewhere in this codebase (`aave_positions.py` / `lst_lido_adapter.py`) — live-verified 2026-07-10 against a public
    Ethereum RPC (sUSDe priced 1.2376 USD, USDe priced 0.9991 USD; independently cross-confirmed against DefiLlama's
    Coins API, which agreed to 3 decimal places), with a DefiLlama Coins API fallback (never a fabricated constant) if
    the RPC path is unavailable. `_fetch_current_apy` now reuses the already-real `_fetch_yields_defillama` fetch
    (live-verified real apy=3.95% for the `ethena-usde` sUSDe pool) instead of a fabricated 0.0; returns `[]` (honest
    empty, per the workspace's silent-placeholder HARD RULE) when no real source is reachable, in both methods. 10 new
    regression tests added (`tests/unit/market_interface/adapters/defi/test_ethena_adapter.py`) asserting the new
    real-source behavior AND explicitly guarding against the old fabricated constants (`price_usd != 1.0`,
    `apy != 0.0`). Full `quality-gates.sh` run green (10/10 new tests pass; verified via `.venv/bin/python -m pytest`
    directly after discovering the base-service.sh gate's own printed "[3/6] TESTS" pytest summary is actually a
    SEPARATE small "PM integration test" sanity check, not the real ~5638-item MTDS suite — the real suite runs silently
    redirected to a temp log, confirmed executed via the zero-test-silent-pass guard + exit 0). **Blocked at ship**:
    `quickmerge.sh`'s pre-flight audit refuses because `unified-trading-library`
    (`unified_trading_library/post_trade/settler.py` modified + `cf_manifest_audit.py` untracked) and
    `unified-api-contracts` (`tests/unit/test_cme_options_universe.py` +
    `unified_api_contracts/registry/tradfi_instrument_universe.py` modified) both have uncommitted sibling-agent WIP —
    confirmed LIVE (not stale-abandoned) via two separate polls totalling ~8 minutes wait, dirty state unchanged
    throughout. Per the dirty-dependency-tree HARD RULE this was NOT forced and the foreign files were NOT touched. The
    diff itself (`ethena_adapter.py` + the new test file) sits uncommitted, ready to ship the moment those two dep repos
    clear — next dispatch/session should retry `quickmerge.sh` first before re-diagnosing.
  - **HUOBI-SPOT/HUOBI-FUTURES/BITSTAMP-SPOT venue registration — re-triaged, found a real SSOT contradiction, NOT
    attempted (escalating, not forcing).** The original "deferred — concurrent edit" note turned out to be stale: the 4
    target UAC registry files were git-clean at the start of this dispatch. But `unified-api-contracts@181b5311`
    (2026-07-09, "fix(cefi): remove never-captured huobi/bitstamp/htx venues from registry + instrument universe") — one
    day before this session even started — deliberately removed huobi/bitstamp/htx from `venue_mapping.py`,
    `provider_api_versions.yaml`, `venue_tokens.py`, and `instrument_validation.py`, reaching the OPPOSITE conclusion to
    this doc's P0 finding. Neither this doc's original 2026-07-07 finding nor
    `instruments_remaining_work_audit_2026_07_10.md`'s "Design: aligned with SSOT, Proceed" verdict for this item was
    written with knowledge of 181b5311 (checked both — neither mentions it) — this is a genuinely new discovery, not a
    re-litigation of an already-settled question. Reading 181b5311's diff: every removed entry was an orphaned
    Tardis-slug mapping-table row for a venue that was NEVER declared in `VENUES_BY_ASSET_GROUP["cefi"]` — so
    "never-captured" is literally true of that specific dead code, but does NOT by itself prove the venues are unviable
    (a half-registered venue with a live Tardis archive underneath is a different fact pattern than a genuinely-dead
    venue). Per the SSOT-contradiction HARD RULE, did not unilaterally re-reverse a same-week peer commit — escalating
    to the operator instead (see this dispatch's final report for the A/B/C framing). Still a real, open P0 gap either
    way.
- **2026-07-10 (later, autonomous session): ETHENA fix shipped** — `market-tick-data-service@9be95ecb`. The diff
  described above (real AAVE V3 Oracle + DefiLlama fallback for `oracle_prices`, real DefiLlama-yields `apy`, 10
  regression tests) had been sitting ready-to-ship since the prior dispatch, blocked purely by the same sibling-agent
  live WIP in `unified-trading-library`/`unified-api-contracts`. Those dep repos were still dirty at ship time
  (unrelated files, confirmed not touched); shipped via the dirty-deps carve-out direct push per the established
  workspace pattern rather than continuing to wait indefinitely. HUOBI/BITSTAMP/HTX SSOT contradiction filed as its own
  dedicated issue doc for the operator (`plans/active/issues/huobi_bitstamp_htx_ssot_contradiction_2026_07_10.md`) with
  live-manifest evidence (zero captured rows for any of the 3 venues) added to sharpen the decision.
