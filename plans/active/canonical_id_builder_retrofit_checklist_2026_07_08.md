---
doc_type: plan
title:
  Retrofit checklist — route every remaining ad hoc instrument_id/leg construction through the new shared
  build_canonical_instrument_id / build_leg builder
summary: >-
  The operator-decided one-builder architecture (instrument_id_format_canonicalization_2026_07_08.md — "one builder for
  everything... every asset group, every instrument type, can get its canonical instrument IDs, same with fixtures, just
  by filling in the right inputs") now has a real implementation: unified-api-contracts' canonical_id_builder.py gained
  build_canonical_instrument_id() (one entry point, dispatches CeFi/DeFi/TradFi/ Prediction to build_instrument_id and
  Sports to the fixture-id domain builder), build_leg() (shared InstrumentLeg construction), and passthrough=True on
  build_instrument_id() (raw exchange-native id wrapping, closing the gap that made the CCXT live-mode fix deliberately
  not route through this module). One real call site (deribit_options_adapter.py) was retrofitted as proof; ~48+ DeFi
  adapters, 5 on-chain-perp adapters, the Deribit combo-leg builder, both Prediction adapters, and 1 sports adapter
  still build instrument_key ad hoc. This plan enumerates that full remaining retrofit, with real file:line pointers
  gathered 2026-07-08.
status: active
nature: notes
asset_group: [cefi, defi, prediction, sports]
stage: [data, meta]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [instrument-id, canonicalization, instrument-identity, builder-retrofit, refactor]
related:
  [
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/archive/2026_07/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    /plans/audit/results/canonical_instrument_id_audit_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  "Sub-agent task (2026-07-08), implementing the operator's one-builder decision recorded in
  instrument_id_format_canonicalization_2026_07_08.md. Filed per that task's instruction to track the FULL remaining
  retrofit as its own plan rather than attempt it all in one pass — the core builder + a couple of proof retrofits +
  this checklist was the scoped deliverable for that round."
context_scope:
  [
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    /plans/audit/results/canonical_instrument_id_audit_2026_07_08.md,
    unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py,
  ]
---

> **What already shipped (2026-07-08, this session)** — read before starting any todo below, it's the infrastructure
> every todo here builds on:
>
> - `unified_api_contracts.build_canonical_instrument_id(asset_group, venue, instrument_type, **kwargs)` — one entry
>   point, dispatches CEFI/DEFI/TRADFI/PREDICTION to `build_instrument_id()`, SPORTS to the fixture-id domain builder
>   (`canonical/domain/sports/canonical_ids.build_fixture_id`, producing `LEAGUE:MATCHUP:DATE` — NOT
>   `VENUE:TYPE:SYMBOL`, by design).
> - `build_instrument_id(..., passthrough=True)` — wraps an already-fully-formed raw/native symbol verbatim as
>   `VENUE[-CHAIN]:TYPE:SYMBOL` (DeFi preserves on-chain case) instead of reconstructing from expiry/strike/right. This
>   is the escape hatch the CCXT live-mode fix needed but didn't have (see
>   `canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md`'s Progress Log).
> - `build_leg(venue, instrument_type, symbol, *, side, ratio=1, ...)` — builds one
>   `unified_api_contracts.internal.InstrumentLeg` via the shared builder instead of an ad hoc f-string.
> - Proof retrofit: `instruments-service/instruments_service/reference_data/adapters/cefi/deribit_options_adapter.py`
>   now calls `build_instrument_id(..., passthrough=True)` for its OPTION `instrument_key` (behavior-preserving,
>   verified against `tests/unit/test_deribit_options_adapter.py`).
> - Compatibility proof (not a live retrofit):
>   `unified-api-contracts/tests/internal/unit/test_canonical_id_builder.py ::TestCcxtTardisCompatibility` shows the
>   shared builder reproduces the real, already-shipped CCXT/Tardis per-venue ids for all sample venues in the CCXT
>   plan's table — `ccxt_adapter.py` itself was NOT touched this round (see todo 9 below for the open refactor
>   question).

## Todos

- [x] [DATA] P1. **Resolve the non-canonical TYPE-token question before retrofitting todo 1** — **RESOLVED 2026-07-27
      (slot-11, `data_engineering`) — stale premise, re-investigated from current code.** The 7 tokens this todo named
      (`VAULT`, `SUPPLY`, `BORROW`, `LENDING_MARKET`, `GOVERNANCE_TOKEN`, `SPOT`, `PERP`) were true-as-of-2026-07-08,
      but **6 of 7 were already fixed by other sessions between 2026-07-09 and 2026-07-16**, using EXISTING enum values
      (no new `InstrumentType` members needed): `VAULT`(EVM restaking/yield)→`YIELD_BEARING`
      (convex/beefy/idle/karak/jito_restaking, commit `bd7580a9` 2026-07-09); `SUPPLY`/`BORROW`→`A_TOKEN`/`DEBT_TOKEN`
      (compound_v3.py, 2026-07-13, `canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py`);
      `LENDING_MARKET`→`A_TOKEN`/`DEBT_TOKEN` pair (benqi/euler_v2/fluid/morpho, same fix wave);
      `GOVERNANCE_TOKEN`→`SPOT_ASSET` (eigenlayer/ethfi, 2026-07-09); `SPOT`→`SPOT_PAIR` (jupiter.py); `PERP` — moot,
      `drift.py`/`flash_trade.py` **deleted entirely** (operator ruling 2026-07-15/16, dead endpoints/~$0 TVL — nothing
      left to retrofit). The enum itself also grew since 2026-07-08: `RESTAKING`, `SOLANA_LENDING`, `SOLANA_VAULT`,
      `SOLANA_AMM_POOL` were added (current full list in `_instrument_enums.py`:
      `SPOT_PAIR, PERPETUAL, FUTURE, OPTION, EQUITY_PERP, TOKENIZED_EQUITY, POOL, DEX_POOL,     LENDING, LST, YIELD_BEARING, A_TOKEN, DEBT_TOKEN, STAKING, RESTAKING, SPOT_ASSET, SOLANA_LENDING, SOLANA_VAULT,     SOLANA_AMM_POOL, ETF, EQUITY, COMMODITY, CURRENCY, INDEX, BOND, CDS, EVENT_CONTRACT, COMBO, PREDICTION_MARKET,     EXCHANGE_ODDS, FIXED_ODDS, PROP`).
      **2 real, NOT-in-the-original-list key-vs-field mismatches found and fixed this round** (same bug class, same
      established fix pattern — key segment must agree with `instrument_type` field, per the AAVE_V3/SPARK/COMPOUND_V3
      precedent): `kamino.py:196` (`instrument_key` said `:VAULT:` while `instrument_type` field was already
      `InstrumentType.SOLANA_VAULT` — fixed, key now says `:SOLANA_VAULT:`) and `pendle.py:267` (`instrument_key`'s TYPE
      segment was the per-record role `PT`/`YT`/`SY`, none of which are real enum values, while `instrument_type` field
      was `YIELD_BEARING` — fixed to `:YIELD_BEARING:`, with the role kept in the SYMBOL segment, e.g.
      `PENDLE-ETHEREUM:YIELD_BEARING:PT-wstETH-25JUN2026`, so PT/YT/SY stay distinguishable without a non-canonical TYPE
      segment; MTDS's own separate `vault_pendle_adapter.py` had already independently made this exact fix and
      documented IS's pendle.py as the still-open counterpart — now closed, MTDS comment updated
      `market-tick-data-service@fbe8abb9`). Both fixes, `instruments-service@d09e0cf4`; `test_pendle_metadata.py`
      updated (role now derived from the symbol segment, not the type segment) — no other cross-repo consumer of the old
      shape found (checked execution-service, market-tick-data-service, deployment-api's legacy display-map, and grep
      for every literal PENDLE/KAMINO instrument_key reference). **No new `InstrumentType` enum members are needed for
      todo 1** — every real value already has a canonical home.
- [x] [DATA] P2. **Retrofit the ~20 DeFi adapters whose `instrument_key` ad hoc f-string already uses a CORRECT enum
      name (DRY-only, no behavior change)** — DONE 2026-08-01 (slot-6, `data_engineering`),
      `instruments-service@d2c73500`. All 16 named sites retrofitted to route through
      `unified_api_contracts.internal.reference.canonical_id_builder.build_instrument_id(venue_tag, InstrumentType.X,     symbol, passthrough=True)`,
      matching the `deribit_options_adapter.py` proof pattern: `compound_v3.py` (A_TOKEN/DEBT_TOKEN), `aave_v3.py`
      (A_TOKEN/DEBT_TOKEN), `spark.py` (A_TOKEN/DEBT_TOKEN), `cbeth.py`, `lido.py`, `renzo.py`, `wbeth.py`, `puffer.py`,
      `rocket_pool.py` (LST), `solana_native_staking.py` (STAKING), `uniswap_v2.py`, `uniswap_v3.py`, `uniswap_v4.py`,
      `raydium.py` (POOL — only the historical-fallback f-string site at the old line 315; the separate
      `build_pool_identity(...)` call for live pools was already routing through a different UAC builder and was left
      untouched), `yearn.py`, `symbiotic.py` (YIELD_BEARING). Byte-identical output verified:
      `_venue_token(venue, chain=None)` uppercases its input and every `venue_tag` in these call sites is already the
      fully-composed, already-uppercase `VENUE-CHAIN` string, so passing it as `venue` with no `chain=` kwarg reproduces
      the exact prior string; DeFi symbols keep their on-chain case under `passthrough=True` (`_build_defi` never
      `.upper()`s the symbol), matching the prior ad hoc f-strings exactly. `quality-gates.sh` green
      (instruments-service). **Follow-up found, not in scope for this todo** — a fresh grep during this pass found 8
      MORE un-migrated ad hoc `instrument_key` f-string sites the 2026-07-27 investigation's list did not name:
      `ankr.py:86`, `mantle.py:86`, `maker.py:101`, `stakewise.py:90`, `swell.py:86`, `stader.py:85` (all `:LST:`), plus
      `kamino.py:199` and `pendle.py:274` (already TYPE-correct per todo 1, still not builder-routed). Tracked as a new
      todo below rather than silently absorbed into this one's scope. **Outstanding from the original investigation, NOT
      addressed by this DRY-only pass** — confirm whether the 7 A_TOKEN/DEBT_TOKEN/YIELD_BEARING/STAKING/SPOT_ASSET/POOL
      tokens named in todo 1's resolution are ALSO silently dropped by the already-fixed P0 "23 DeFi adapters silently
      return empty on canonical-form type filters" finding
      (`canonical_id_p0_defi_adapter_type_filter_bug_2026_07_08.md`), same mechanism/different tokens — separate work
      from the builder-routing done here.
- [x] [DATA] P2. **VERIFY `morpho.py:195`'s real current code against finding 6 — DONE 2026-08-01 (slot-15,
      `data_engineering`), `instruments-service@<pending quickmerge sha>`.** This todo's own premise was stale: the
      quoted snippet (`instrument_key = f"{venue_tag}:LENDING_MARKET:{symbol}-{market_key[:8]}"`) doesn't exist in
      current code at all — it was the shape right after `af05ece3` (2026-07-08, the original dash-fix) and was fully
      superseded by `b5a3f6c9`'s A_TOKEN/DEBT_TOKEN split (confirmed via `git log`/`git show` on both commits). Current
      code (`_market_to_records`, ~line 207) builds `pair_key = f"{collateral_symbol}-{loan_symbol}-{market_key[:8]}"`,
      dash-only, then routes through
      `build_canonical_instrument_id(..., InstrumentType.A_TOKEN/DEBT_TOKEN, ...,     passthrough=True)` — matching
      finding 6's SUPERSEDED banner. **But two real, live findings surfaced by actually doing the verification (a live
      re-fetch + a real catalog query), not just re-reading the code:** 1. **A real, live, severity-escalating code gap
      — FIXED this pass.** Live re-fetch against `blue-api.morpho.org` across all 5 supported chains (2,792 valid
      markets checked) found exactly one real raw collateral-asset symbol embedding a colon: GMX's GM-vault token
      `GM:ETH/USD[WETH-USDC]` (Morpho-Arbitrum market `0x1a926ab8…`). `collateral_symbol`/`loan_symbol` were never
      sanitized before entering `pair_key`, and `canonical_id_builder.py`'s `build_instrument_id` **hard-rejects**
      (raises `ValueError`) any non-sports/prediction symbol containing `:` (the 2026-07-20 fail-loud double-wrapped-id
      guard) — `get_instruments()`'s per-market loop has no try/except, so this ONE market would have aborted
      Morpho-ARBITRUM discovery **entirely** (losing all ~221 valid markets on that chain), not just corrupted its own
      id. Fixed: added `_sanitize_symbol()` (strips `:`/`/`/`[`/`]`) applied to both symbols before building `pair_key`;
      byte-identical for the ~99.96% of markets with clean symbols (verified: normal-market test asserts the exact prior
      string). New regression test: `tests/unit/reference_data/adapters/defi/test_morpho_symbol_sanitization.py` (real
      GM-vault market fixture + a normal-market no-op-sanitization check). 2. **A real, separate, NOT-yet-fixed
      catalog-regeneration-gap finding — new todo below, out of scope for this code-level fix.** Direct query of real
      `prod/catalog.parquet` (2,753 MORPHO rows) found 1,330 (48%) still carry an embedded colon before the market-key
      hex suffix, e.g. `MORPHO-BASE:A_TOKEN:ACBBTC-USDC:0x125081` — traced to
      `scripts/canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py:106`
      (`row["instrument_id"].split(":", 2)`), which parsed stale pre-`af05ece3` `LENDING_MARKET`-shaped rows and
      forwarded whatever colon-containing suffix it found straight into the new `A_TOKEN`/`DEBT_TOKEN` shape, instead of
      re-deriving a clean dash-only `pair_key`. This is the SAME class of defect as finding 2's DEX-pool catalog-regen
      gap — durable code fix does not equal durable historical data. Confirmed:
      `MORPHO-BASE:A_TOKEN:AUSDC-EURC-0x305dd1` (finding 6's ORIGINAL cited example) IS already clean in the real
      catalog — the embedded-colon defect is real but only in a subset of rows, not universal.
- [x] [DATA] P1. **Retrofit the 5 on-chain-perp adapters** — DONE 2026-07-09, `instruments-service@ca2f44e5`. Pure DRY,
      byte-identical output confirmed against the existing test suite, no behavior change.
- [x] [DATA] P1. **Fix the real `:TYPE:` segment bug in Deribit's combo-leg builder** — DONE 2026-07-09,
      `instruments-service@ca2f44e5`. New `_classify_deribit_leg_instrument_type()` classifier verified against
      Deribit's real live `public/get_combos` API (89 real BTC combos / 32 unique legs, 88 real ETH combos / 30 unique
      legs). Real before/after: `DERIBIT:BTC-PERPETUAL` → `DERIBIT:PERPETUAL:BTC-PERPETUAL`. Full evidence:
      `instruments_docs_audit_outstanding_items_2026_07_08.md` finding A2.
- [x] [DATA] P2. **Fix the real `/`-delimiter bug in Betfair's sports adapter** — `betfair.py:279`
      (`_build_runner_record`) builds `instrument_key = f"{market_id}/{selection_id}"`, using `/` instead of the
      workspace's `:`-delimited convention (confirmed in `instruments-service/docs/SPORTS_INSTRUMENTS.md`'s "Known gaps"
      section as "the audit's most degenerate raw-passthrough found"). Sports keeps its own ID scheme (not forced into
      `VENUE:TYPE:SYMBOL` — operator decision), so this does NOT route through `build_canonical_instrument_id`; it just
      needs its own delimiter fix (`f"{market_id}:{selection_id}"`) plus a check for any downstream consumer that
      currently splits on `/`. **CLOSED BY-DESIGN 2026-07-12** (operator ruling, plan-reconciliation finding 341, see
      `active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2): `/` is Betfair's documented native id
      convention — canonical ids for Betfair KEEP the `/` delimiter; downstream consumers must treat it as venue-native,
      not normalise. Zero production Betfair rows exist today (dormant path); if Betfair activates, builders adopt this
      convention as-is.
- [x] [DATA] P1. **Fix the real "no VENUE:TYPE: wrap at all" gap in both Prediction adapters** — ✅ ALREADY SHIPPED
      2026-07-09, `instruments-service@0a0c7397` — **checkbox was never flipped; verified 2026-07-27 (slot-8,
      `data_engineering`) that the code, docs, and tests all match this todo's target shape, no new code needed.** Both
      Kalshi (`kalshi.py:865-867`) and Polymarket (`polymarket/parsing.py:161-163`) now call
      `build_canonical_instrument_id(AssetGroup.PREDICTION, venue, InstrumentType.PREDICTION_MARKET, raw_id)` —
      `KALSHI:PREDICTION_MARKET:<ticker>` / `POLYMARKET:PREDICTION_MARKET:<condition_id>` — WITHOUT `passthrough=True`
      (passthrough upper-cases non-DeFi symbols, which would corrupt Polymarket's lowercase `0x…64hex` condition_id;
      dispatching without it for PREDICTION_MARKET already routes to `_build_sports_or_prediction()`, which preserves
      case verbatim). **Downstream-consumer check** (the one real consumer this todo flagged): Polymarket's
      `_register_clob_token_ids(...)` side-table (`parsing.py:173`) is registered under the FINAL wrapped
      `instrument_key`, not the bare `condition_id` — the commit message documents this as a real bug found + fixed
      during the consumer-impact check. Re-verified 2026-07-27: grep of
      `instruments_service/reference_data/adapters/prediction/` finds zero remaining
      `instrument_key=ticker`/`instrument_key=condition_id` bare-assignment sites; `docs/PREDICTION_INSTRUMENTS.md`
      cites this fix; `tests/unit/test_kalshi_adapter.py` + `tests/unit/test_prediction_adapters_comprehensive.py`
      (lines 297/374/408) + `tests/unit/test_betfair_polymarket_adapter.py:212` all assert the wrapped
      `VENUE:PREDICTION_MARKET:<id>` shape. **Coordination note**:
      `prediction_canonical_identity_migration_2026_07_08.md` (the sibling plan this todo was to coordinate with on the
      separate `canonical_instrument_id` field) is already archived (`plans/archive/2026_07/`) — no live cross-plan
      conflict remains.
- [ ] [DATA] P3. **Cross-reference, don't duplicate, the TradFi combo-leg fix** — finding 7 (CBOE/VX spreads bypassing
      `InstrumentLeg`/COMBO entirely) already has its own dedicated plan,
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`. Note there that the new `build_leg()` helper is
      now available for that plan to use once its pending `[DECISION]` (per-leg `VENUE:` prefix drop) resolves — do not
      re-scope that work into this plan.
- [ ] [DATA] P3. **DECIDED — yes, refactor `ccxt_adapter.py` to call the shared builder.** Operator guidance: no real
      ambiguity here (explicitly "no output change" either way per this todo's own framing) — do it for consistency,
      same for the MTDS callers below. Not urgent, pick up opportunistically.
- [ ] [DATA] P3. **DECIDED — yes, upgrade MTDS's already-correct callers to the new one-entry-point** —
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py:242` and
      `.../cefi/tardis_shared.py:433,464,473`. Cosmetic consistency change, no behavior change expected. Not urgent.
- [x] [DATA] P3. **Retire the misspelled `AAVEV3-OPTIMISM` venue-token duplicate** (finding 5) — DONE, fixed by a
      concurrent sibling agent the same session (DeFi venue-token naming cleanup), confirmed via a fresh real re-query
      of `prod/catalog.parquet`: 0 ghost rows, 16 rows correctly under `AAVE_V3-OPTIMISM`. This todo was stale by the
      time this plan was filed — the parallel work wasn't visible to the agent that wrote it.
- [ ] [SCRIPT] P2. **Ship each retrofit batch via quickmerge**, quality-gates green per repo, citing before/after
      `instrument_key` evidence per adapter touched (same evidence pattern as the CCXT plan's per-venue table). Batch by
      asset-group-cluster (todo 1+2 together, todo 4 alone, todo 6 alone, etc.) rather than one giant commit.
- [ ] [SCRIPT] P2. **Migrate the 1,330 stale-colon MORPHO catalog rows found during the finding-6 verify pass
      (2026-08-01)** — `prod/catalog.parquet`'s MORPHO A_TOKEN/DEBT_TOKEN rows still carry an embedded colon before the
      market-key hex suffix for 1,330 of 2,753 real rows (e.g. `MORPHO-BASE:A_TOKEN:ACBBTC-USDC:0x125081`, should read
      `...:ACBBTC-USDC-0x125081`), because `canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py:106`
      forwarded the stale pre-`af05ece3` `pair_key` string verbatim (via `instrument_id.split(":", 2)`) instead of
      re-deriving it from source columns. Fix: a dedicated migration script (same backup/`--dry-run`/`--apply` pattern
      as the 2026-07-13 script) that re-derives each affected row's `pair_key` from its own already-persisted
      `base_asset`/`quote_asset`/`pool_address` columns (all present per-row — no resynthesis from an external source)
      rather than string-splitting the stale id. Scope check first: confirm whether the same defect recurs for the 6
      FLUID rows the 2026-07-13 script also split (same `split(":", 2)` code path, same `_SPLIT_PREFIXES` list) — not
      verified in this pass, FLUID wasn't queried.

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [ ] [DATA] P2. **NEW (found during this fix's historical-damage verification, 2026-07-08): resolve the `FI_`-vs-`FF_`
      same-(ticker,expiry) instrument_id collision** — 13 real (ticker, expiry) pairs (ETH/XBT only, 2024-2026 range, 45
      of the 125 remediated files) have BOTH an `FI_` and an `FF_` raw Tardis symbol with real, differing row counts
      (not duplicates) that now derive the IDENTICAL corrected `instrument_id` because `derive_row_instrument_id`'s
      FUTURE branch has no field for the `FI`/`FF` contract-subtype. Needs an operator decision on what `FI_` actually
      represents relative to `FF_` for KRAKEN-FUTURES (the existing code comment in `tardis_shared.py` calling `FI_`
      "old index, pre-2020, no longer active" is contradicted by real 2024-2026 data found here) and how to encode the
      distinction in the canonical instrument_id (e.g. a contract-subtype marker) before any further Kraken-Futures
      remediation or backfill. (FOLDED IN from canonical_id_p0_kraken_futures_collision_2026_07_08, 2026-07-15,
      plan-reconcile §6 operator ruling)

## Progress Log

- **2026-07-08** — Filed as the follow-up checklist for the one-builder-for-everything architecture decision. Core
  builder (`build_canonical_instrument_id`, `build_leg`, `passthrough=True`) shipped this session in
  `unified-api-contracts`; one real live retrofit (`deribit_options_adapter.py`) and one compatibility-test proof
  (CCXT/Tardis table) landed alongside it. This plan captures the full remaining retrofit surface with real file:line
  evidence gathered via direct grep + read, not guessed.
- **2026-08-01 (slot-15, `data_engineering`)** — Closed the `morpho.py:195` VERIFY todo. Confirmed via
  `git log`/`git show` that the todo's own quoted "current code" snippet was stale (superseded by `b5a3f6c9`'s
  A_TOKEN/DEBT_TOKEN split, matching finding 6's SUPERSEDED banner). Did the verification the todo actually asked for —
  a live re-fetch against Morpho's real GraphQL API (all 5 chains, 2,792 valid markets) plus a direct query of real
  `prod/catalog.parquet` (2,753 MORPHO rows) — rather than treating the code read alone as sufficient, and found two
  real things the code-only read would have missed: (1) a live severity-escalating bug (one real GMX GM-vault collateral
  symbol embeds a colon, which would abort an entire chain's Morpho discovery via `canonical_id_builder.py`'s fail-loud
  guard + no per-market try/except) — fixed this pass, `instruments-service`; (2) a real, separate, NOT-fixed
  catalog-regeneration gap (1,330/2,753 real rows still stale) — added as a new todo above, correctly scoped out of this
  pass (needs its own migration script, not a code change).
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
