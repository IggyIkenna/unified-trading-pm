---
doc_type: issue
title:
  "OPERATOR DECISION: canonicalize instrument_id format everywhere it currently diverges — dated-derivative raw
  prefixes, DEX-pool bare addresses, PERP-vs-PERPETUAL key/field mismatch, a misspelled venue-token duplicate"
summary:
  "While backfilling real instrument_id samples into the instruments-definitions mockup (2026-07-08), found that
  instrument_id format is NOT actually canonical across the workspace — `canonical_id_builder.py` reads as the intended
  SSOT but has exactly one real caller (Polymarket), so every venue builds its own ID ad hoc. Operator reviewed one
  concrete case (KRAKEN-FUTURES:FUTURE:FF_XBTUSD_260731 — Kraken's raw, uncleaned prefix, vs the SAME venue's PERPETUAL
  which DOES get cleaned to BTC-USDT) and decided: yes, canonicalize — full scope, not just Kraken. This doc is the
  operator decision + the enumerated real scope, mirroring
  [[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]'s pattern (a real, decided target-state, current-state
  vs target-state framing in the mockup, staged migration to follow — not fixed today)."
status: open
nature: notes
asset_group: [cefi, defi, prediction]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    instrument-id,
    canonicalization,
    instrument-identity,
    dated-derivatives,
    dex-pool,
    perp-vs-perpetual,
    honest-coverage,
  ]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    ../../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    ../canonical_id_p0_kraken_futures_collision_2026_07_08.md,
    ../canonical_id_p0_defi_adapter_type_filter_bug_2026_07_08.md,
    ../canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md,
    ../canonical_id_p0_strategy_reconciliation_2026_07_08.md,
    ../prediction_canonical_identity_migration_2026_07_08.md,
  ]
created: 2026-07-08
parent_epic: instruments_master
priority: P2
source:
  'Operator, 2026-07-08, reviewing the KRAKEN-FUTURES:FUTURE entry in the drilldown mockup: "but that doesnt tell us we
  ARE moving to canonical everywhere" — then explicitly chose "Yes, decide it now — full scope" when offered the choice
  between leaving this as an unscoped finding vs a real decided target-state.'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
last_updated: 2026-07-15
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **OPERATOR DECISION 2026-07-08 — target-state only, not fixed today** (was: still fully accurate as of authoring;
> **PARTIALLY EXECUTED — banner corrected 2026-07-15**). Every finding below gets a canonical target format. This doc
> (and the mockup entries it backs) originally showed current-real vs target-canonical side by side, same pattern
> already applied to the A_TOKEN/DEBT_TOKEN decision — but per this doc's own Progress Log (2026-07-09 entries), real
> code fixes and historical-data migrations toward these target formats have since landed on `origin/live-defi-rollout`
> (e.g. `instruments-service@176d4610`'s `@LIN`/`@INV` builder + margin-type fixes, `@7fbc38c1`'s Deribit OPTION
> `@LIN`/`@INV`-`YYYYMMDD`, `@0d0c3742`'s Prediction canonical_instrument_id, plus the on-chain-perp and ghost-venue
> historical-data migrations logged below). The "none of the target formats exist in production yet" / "actually
> migrating is staged, future work" claims below are STALE as blanket statements — treat the Progress Log as the
> current-state record; per-finding SUPERSEDED/RESOLVED annotations below track which individual findings are actually
> closed.

## The 8 real divergences found, and their target canonical format

> _(was: "The 6 real divergences found" -- corrected 2026-07-12, finding 97, §A2 B-queue ruling: findings 7-8 were added
> later per this doc's own Progress Log, bringing the real count to 8; the body enumeration below was already correctly
> numbered 1-8, only this header's count had lagged.)_

All verified against real `prod/catalog.parquet` reads (both `cefi` and `defi` asset groups), 2026-07-08.

1. **Dated-derivative raw venue prefixes never get cleaned, unlike the same venue's PERPETUAL — and the formats aren't
   even consistent with EACH OTHER across venues.** `KRAKEN-FUTURES:FUTURE:FF_XBTUSD_260731` (Kraken's own raw
   `FF_`/`FI_` prefix, unstripped) vs the same venue's `KRAKEN-FUTURES:PERPETUAL:ACH-USD` (Kraken's raw `PF_ACHUSD` IS
   cleaned). `BINANCE-FUTURES:FUTURE:BTCUSDT_260925` (raw concatenated + underscore-date). `BYBIT:FUTURE:BTC-01DEC23`
   (no quote segment at all, DDMMMYY date). `DERIBIT:OPTION:BTC-10JUL26-48000-C` (DDMMMYY date, real, and looks clean in
   isolation — but that's not the same as consistent with the other 3 venues above). **Target format — DECIDED
   2026-07-08** (operator, after reviewing an inconsistency between this doc's own illustrative Kraken target and a
   recollection of the strategy-service `@LIN`/`@INV` convention, plus catching that the mockup itself used two
   different date formats across its own targets): `VENUE:TYPE:BASE[_QUOTE]@LIN|@INV-YYYYMMDD[-STRIKE-C|P]` — uniform
   across every venue and every dated-derivative instrument_type (FUTURE and OPTION alike), e.g.
   `KRAKEN-FUTURES:FUTURE:XBT-USD@INV-20260731`, `BYBIT:FUTURE:BTC-USDT@LIN-20231201`,
   `DERIBIT:OPTION:BTC@INV-20260710-48000-C`. Two explicit sub-decisions, both settled over the `-linear-`/`-inverse-`
   word alternative and the `DDMMMYY` alternative respectively:
   - **Margin marker = `@LIN`/`@INV` suffix**, not `canonical_id_builder.py`'s already-written but unused
     `-linear-`/`-inverse-` word form. Chosen to match strategy-service's existing position-ID convention (e.g.
     `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID`) rather than introduce a 3rd convention. **RESOLVED 2026-07-08**:
     operator explicitly confirmed NO trailing `@VENUE` — "I don't see why you would append the venue suffix to
     something that already has venue in its canonical name, so that just seems weird." Also confirmed: the convention
     must be enforced via real, callable builder functions everywhere it applies, not docstring-only assertions (the
     state of both `canonical_id_builder.py` and strategy-service's `@LIN`/`@INV` today, per
     [[canonical_instrument_id_audit_2026_07_08]]).
   - **Date format = `YYYYMMDD`**, not Deribit's real `DDMMMYY` (e.g. `10APR26`). Rationale given: `YYYYMMDD` is
     string-sortable (chronological order = alphabetical order); `DDMMMYY` is more human-glanceable but does NOT sort
     correctly as a string (`"10APR26"` sorts after `"10JAN27"` alphabetically despite being earlier). This means
     Deribit's OPTION/FUTURE entries — previously assessed in the mockup as "already canonical, no fix needed" — are now
     ALSO in scope for this canonicalization; that earlier assessment is superseded.
   - **SCOPE EXPANDED 2026-07-09 (operator) — `@LIN`/`@INV` now applies to `PERPETUAL` too, not just dated
     derivatives.** Original framing above treated PERPETUAL as "already clean" since a venue's real quote currency was
     assumed to disclose margin type. Real evidence disproves that assumption: Kraken-Futures'
     `KRAKEN-FUTURES:PERPETUAL:AAVE-USD` (linear) and `KRAKEN-FUTURES:PERPETUAL:BTC-USD` (inverse) are both real, both
     quote `USD` — the id alone cannot distinguish them today (also the root of the already-known Kraken
     inverse-mislabeled-as-linear bug). Operator: "perps should be included for exactly that reason across the board —
     you can't tell whether something is inverse just from its quote currency because USD is a valid quote currency as
     well." **New target for PERPETUAL**: `VENUE:PERPETUAL:BASE-QUOTE@LIN` / `...@INV` — same marker, no date suffix
     (perpetuals don't expire). Applies everywhere `PERPETUAL` exists across CeFi (including the 5 on-chain-perp CLOBs)
     and TradFi (no TradFi perpetual product exists today). Real examples: `DERIBIT:PERPETUAL:BTC-USD@INV` /
     `DERIBIT:PERPETUAL:BTC-USDC@LIN`; `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` /
     `BINANCE-DELIVERY:PERPETUAL:BTC-USD@INV`. **Not yet determined**: the real LIN/INV value for each of the 5
     on-chain-perp CLOBs — needs real verification of actual settlement/margin mechanics per venue, not an assumption.

2. **DEX-pool instrument_id is a bare on-chain pool address, zero VENUE:TYPE:SYMBOL structure, confirmed across 6,180
   real rows / 13 protocols (Uniswap V2/V3/V4, Balancer, Curve, PancakeSwap_V3, Sushiswap/\_V3, Camelot_V3,
   Aerodrome_V3, TraderJoe_V2, Velodrome_V2, GMX) — zero exceptions.** Real:
   `0x00822ba38a39b79cbc5b7f62ba1a6886a45f9e4c` (venue/chain/base*asset live in separate columns instead). **Target**:
   `VENUE-CHAIN:POOL:TOKEN0-TOKEN1[-FEE_TIER]` (matching `canonical_id_builder.py`'s own `_build_defi` docstring
   example, `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`) — pool_address stays as its own column for on-chain lookups, it
   just stops being the \_entire* identity key. **UPDATE 2026-07-08, reconciled — this is a data-regeneration gap, NOT
   (only) a code gap**: real current adapter code
   (`instruments-service/instruments_service/reference_data/adapters/defi/uniswap_v3.py:489-492`, `_build_pool_record`)
   already builds a structured key — `instrument_key = f"{venue_tag}:POOL:{base}-{quote}:{fee_str}"` (e.g.
   `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH:3000`) — confirmed by reading the code directly. But the REAL, CURRENT
   `prod/catalog.parquet` (re-verified 2026-07-08, 7,284 DeFi rows) still shows the bare-address form with a bare
   `UNISWAP_V3` venue (no `-ETHEREUM` chain suffix) for all 2,030 real Uniswap V3 rows — a venue-tagging shape the
   current code doesn't even produce anymore. This means the persisted catalog predates this adapter code (or was built
   by a different, older write path) and has never been regenerated since — the fix here is likely a **catalog
   regeneration/backfill against the current adapter code**, not a from-scratch code change, though the current code's
   own gaps still apply on top (colon-before-fee-tier should be dash per this finding's target; `fee_str` uses Uniswap's
   raw feeTier units — e.g. `3000` — not real basis points — a real basis-point value is computed separately as
   `pool_fee_tier_bps` but isn't the one embedded in the instrument_key string). **UPDATE 2026-07-08 (all 13 protocols
   re-verified, not just Uniswap V3)** — read `prod/catalog.parquet` directly (6,180 real DEX-pool rows) and traced
   every protocol's adapter code. Result: **zero code gaps found anywhere; this is a pure catalog-regeneration gap
   across all 13 protocols, uniformly.**

   | Protocol              | Real rows | Real chains (catalog)                                  | Persisted `instrument_id` shape        | Adapter code shape                                                      |
   | --------------------- | --------- | ------------------------------------------------------ | -------------------------------------- | ----------------------------------------------------------------------- |
   | UNISWAP_V3            | 2,030     | ARBITRUM, BASE, ETHEREUM, OPTIMISM, POLYGON            | bare address, no chain suffix on venue | Structured (`uniswap_v3.py:490-492`)                                    |
   | BALANCER              | 2,413     | ARBITRUM, AVALANCHE, BASE, ETHEREUM, OPTIMISM, POLYGON | bare address, no chain suffix          | Structured (`balancer.py:224-226`, own adapter class)                   |
   | UNISWAP_V4            | 413       | ETHEREUM                                               | bare address, no chain suffix          | Structured (`uniswap_v4.py:245-247`, own adapter class)                 |
   | TRADER_JOE_V2         | 304       | AVALANCHE                                              | bare address, no chain suffix          | Structured (shares `UniswapV3ReferenceDataAdapter` via `protocol_slug`) |
   | PANCAKESWAP_V3        | 614       | BSC, ZKSYNC, BASE, ETHEREUM                            | bare address, no chain suffix          | Structured (shares `UniswapV3ReferenceDataAdapter`)                     |
   | VELODROME_V2          | 96        | OPTIMISM                                               | bare address, no chain suffix          | Structured (shares `UniswapV3ReferenceDataAdapter`)                     |
   | AERODROME_V3          | 76        | BASE                                                   | bare address, no chain suffix          | Structured (shares `UniswapV3ReferenceDataAdapter`)                     |
   | CAMELOT_V3            | 63        | ARBITRUM                                               | bare address, no chain suffix          | Structured (shares `UniswapV3ReferenceDataAdapter`)                     |
   | SUSHISWAP_V3          | 122       | AVALANCHE, BASE, ETHEREUM                              | bare address, no chain suffix          | Structured (shares `UniswapV3ReferenceDataAdapter`)                     |
   | SUSHISWAP (legacy V2) | 4         | ARBITRUM                                               | bare address, no chain suffix          | Structured (shares `UniswapV3ReferenceDataAdapter`)                     |
   | UNISWAP_V2            | 24        | ETHEREUM                                               | bare address, no chain suffix          | Structured (`uniswap_v2.py:216-218`, own adapter class)                 |
   | CURVE                 | 20        | AVALANCHE, ETHEREUM, OPTIMISM                          | bare address, no chain suffix          | Structured (`curve.py:162-164`, own adapter class, RPC not subgraph)    |
   | GMX                   | 1         | ARBITRUM                                               | bare address, no chain suffix          | Structured (shares `UniswapV3ReferenceDataAdapter`)                     |

   The 8 "shares `UniswapV3ReferenceDataAdapter`" rows are not independently-written code — `factory.py`'s
   `supports_protocol_slug`/`VENUE_PREFIX_TO_PROTOCOL` routing (lines ~474-492) instantiates the SAME
   `UniswapV3ReferenceDataAdapter` class with a different `protocol_slug` constructor arg for all of them, so they run
   through the literal same `_build_pool_record` method already confirmed structured for Uniswap V3 — verifying Uniswap
   V3's code transitively verifies all 8. Balancer/Uniswap V2/Uniswap V4/Curve are separate adapter classes and were
   each individually read and confirmed structured. **No protocol in this list needs a code fix** — the only remaining
   work is the catalog regeneration (already tracked as a todo below) plus the 2 already-known Uniswap-V3-specific code
   gaps noted above (colon-vs-dash fee-tier delimiter, raw feeTier vs bps) which likely also apply to Uniswap V4's
   `fee_str` (same `:{fee_str}` colon shape at `uniswap_v4.py:247`) — not independently re-verified for V4's bps
   handling in this pass.

3. **The 5 on-chain-perp venues (HYPERLIQUID/ASTER/PACIFICA-SOLANA/EXTENDED-STARKNET/LIGHTER-ZKSYNC) all store
   instrument_type=PERPETUAL as the field but embed PERP (not PERPETUAL) in the instrument_id key** — consistent across
   all 5, but disagreeing with both the field and CeFi's own `PERPETUAL`-in-key convention (e.g.
   `BINANCE-FUTURES:PERPETUAL:BTC-USDT`). **Target**: `VENUE:PERPETUAL:...` everywhere, dropping the `PERP` shorthand.

4. **Base-quote normalization is inconsistent even within that same 5-venue on-chain-perp cluster.** Real:
   HYPERLIQUID/LIGHTER-ZKSYNC use a bare symbol (`HYPERLIQUID:PERP:BTC`, no quote at all), ASTER uses the raw
   concatenated exchange symbol (`ASTER:PERP:BTCUSDT`, no dash), PACIFICA-SOLANA's quote segment is literally the string
   `PERP` (`PACIFICA-SOLANA:PERP:SOL-PERP`, not a currency), and EXTENDED-STARKNET is the only one already
   dash-normalized with a real currency (`EXTENDED-STARKNET:PERP:ETH-USD`). **Target**: `VENUE:PERPETUAL:BASE-QUOTE`
   with a real settlement currency for all 5 — e.g. `ASTER:PERPETUAL:BTC-USDT`, `HYPERLIQUID:PERPETUAL:BTC-USD`,
   `PACIFICA-SOLANA:PERPETUAL:SOL-USDC`, `LIGHTER-ZKSYNC:PERPETUAL:BTC-USDC` (exact quote currency per venue TBD at
   implementation time — these are illustrative, not independently re-verified per-venue settlement asset).

5. **AAVE_V3-OPTIMISM has a misspelled venue-token duplicate** — `AAVEV3-OPTIMISM` (missing underscore, 4 real rows)
   coexists with the correctly-spelled `AAVE_V3-OPTIMISM` (12 real rows), fragmenting the real per-chain reserve set
   into 2 disjoint keys invisible to anything querying the correct prefix. **Target**: consolidate all rows under
   `AAVE_V3-OPTIMISM` only; the misspelled variant is retired, not migrated (it's a typo, not a distinct entity).

6. **MORPHO's market-address disambiguator uses a 3rd colon inside the symbol** — **SUPERSEDED 2026-07-13**: the
   `LENDING_MARKET`-typed examples below (`Real`/`Target`) describe the pre-fix model. Per the resolved
   `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` (shipped `instruments-service@72e0113`+`5226818`),
   MORPHO now emits the canonical A_TOKEN/DEBT_TOKEN split — real shape `MORPHO-{CHAIN}:A_TOKEN:A{pair_key}` /
   `MORPHO-{CHAIN}:DEBT_TOKEN:DEBT{pair_key}` (`build_canonical_instrument_id`-routed), 2,666 real MORPHO rows in
   production, 100% canonical. Whether the original 3rd-colon-disambiguator concern still applies to this new key shape
   is **unclear from the resolved doc alone** — `pair_key` reads as a single dash-fused segment (not independently
   colon-delimited) in the one concrete example cited there, which would mean the concern doesn't recur, but no literal
   full real instrument_id was quoted to confirm this. **Flagging as a follow-up**: someone should read
   `morpho.py::_market_to_records`/`_build_pair_key` (or equivalent) directly and confirm `pair_key` never itself
   contains a `:` before treating this finding as fully closed.
   - **Original finding (historical, pre-fix), preserved for record:** `MORPHO-BASE:LENDING_MARKET:USDC-EURC:0x305dd1` —
     colon is the reserved top-level `VENUE:TYPE:SYMBOL` delimiter, so a 3rd colon is ambiguous to any naive
     `split(":")` parser. **Target** (as originally proposed): dash-separate instead, matching the pool-fee-tier fix
     already applied elsewhere — `MORPHO-BASE:LENDING_MARKET:USDC-EURC-0x305dd1`.

7. **TradFi multi-leg spreads reuse the single-leg `SPOT_PAIR` type and separate legs with a whitespace-padded dash of
   raw exchange tickers — but real, structured infrastructure to do this properly already exists and just isn't wired up
   for CBOE.** Real, confirmed via `prod/catalog.parquet` (1,096,069 rows): 34,017 rows carry 2 legs
   (`CBOE:SPOT_PAIR:VX/F1:1:S - VX/G1:1:B`), 4,211 carry 3 legs, 5 carry 4 legs (up to 9 colon-segments). Operator
   pushback on an initial flat-string proposal (a `VENUE:SPREAD:LEG-RATIO-SIDE;...` grammar using raw tickers) was
   correct and led to finding real prior art: `unified_api_contracts.internal.InstrumentLeg` (a proper `BaseModel` with
   `instrument_key`/`side` (`"BUY"`/`"SELL"` words, not letters)/`ratio` fields) is already used by
   `databento/symbology.py::_parse_cme_calendar_spread_legs` (wired into `databento/adapter.py:802`, CME/GLBX.MDP3 only)
   and independently by 2 Deribit combo builders (`cefi/tardis/combos.py`, `cefi/deribit_combo_adapter.py`); a real
   `InstrumentType.COMBO` enum value already exists (`databento/symbology.py:60`); a real ticker→human-name registry
   already exists and covers exactly the operator's own examples — `unified_api_contracts.registry.tradfi_symbology`:
   `"ES": "SP500"`, `"GC": "GOLD"`, `"VX": "VIX"` — via `_resolve_product_root()`; and `process_write.py:184` already
   serializes `legs: list[InstrumentLeg]` to a separate JSON column rather than encoding structure into instrument_id.
   **The real gaps, not a from-scratch design question**: (a) CBOE/VX calendar spreads are explicitly EXCLUDED from
   `_parse_cme_calendar_spread_legs` (`_FUTURES_DATASETS = {"GLBX.MDP3"}` only; comment: "VX class-'S' calendar spreads
   are dropped (outright-only universe)") — wherever the real 34K CBOE `SPOT_PAIR` rows actually come from, it bypasses
   this infrastructure entirely, landing as an undecomposed flat string with the wrong type; (b) even the CME path that
   DOES work doesn't apply `_resolve_product_root()` — `instrument_key=f"{venue}:FUTURE:{front}"` uses the raw ticker
   (`ESM6`), not the human name; (c) that CME `instrument_key` also repeats `VENUE:` per leg, which the operator
   correctly flagged as unnecessary (a combo is already scoped to one venue at the top level) — same redundancy
   objection already settled for margin-marker `@VENUE` in finding 1. **Proposed fix (pending operator confirmation)**:
   route CBOE/VX spreads through the same `InstrumentLeg`/`COMBO` pathway already proven for CME, apply
   `_resolve_product_root()` so legs read `TYPE:SYMBOL` in human names (e.g. `FUTURE:VIX`, not `FUTURE:VX/F1` or
   `FUTURE:VXF1`), and drop the per-leg `VENUE:` prefix in the existing CME builder too (`instrument_key` becomes
   `TYPE:SYMBOL` only, venue implied by the combo's own top-level `VENUE:COMBO:...`). Recommend this become its own fix
   plan under `instruments_master` (real code gap affecting 34K+ live rows, not just a naming decision) — separate from
   and shippable in parallel with the docs-consolidation work.

8. **RESOLVED 2026-07-08 (was: "Prediction's per-market instrument_id is genuinely opaque, and its enrichment columns
   are 100% empty").** Root cause diagnosed, the null-fields bug fixed, and a canonical scheme decided — full write-up
   in `instruments-service/docs/PREDICTION_INSTRUMENTS.md` § "Canonical identity model" (this entry summarizes it; that
   doc is the SSOT).
   - **Root cause (was "not yet understood")**: `base_asset`/`raw_symbol` ARE populated correctly by both adapters at
     `InstrumentRecord` construction and DO survive into the per-day `instrument_availability/by_date/...` parquet
     snapshots (verified: `process_write.py::_records_to_dataframe()` serializes every `InstrumentRecord` field via
     `model_dump()`). They were dropped one level up, in
     `instruments-service/scripts/build_instrument_catalogue.py::build_prediction_catalogue_dataframe()` — Prediction's
     dedicated multi-grain catalogue roll-up never read `raw_symbol`/`base_asset` off the per-day rows into its
     `_PredLifecycle` accumulator (unlike the generic `_extract_meta()` roll-up every other asset group uses, which
     does), so `_emit()` never included those keys and `pd.DataFrame(rows, columns=CATALOG_COLUMNS)` silently backfilled
     `NaN` for all 2,486,092 rows. **Fixed** — `_PredLifecycle`/`_merge_lifecycle`/`_emit()` now thread
     `raw_symbol`/`base_asset` through at the per-conditionId grain; next catalogue regen carries real values.
   - **`underlying` is a genuinely different case** — no adapter ever calls `InstrumentRecord(underlying=...)` at all,
     so there is nothing to "fix" in the roll-up for this field; it was never computed upstream. Conceptually it IS
     sensible for a real subset (crypto/macro/commodity price markets have a natural subject asset — BTC, CPI, GOLD) and
     honestly absent for the rest (politics/geo/entertainment have none; sports has a fixture identity, not a scalar
     asset) — `unified_api_contracts/canonical/domain/predictions/two_axis.py`'s `PredictionUnderlying` enum already
     gives a comprehensive per-cqg mapping, and `cross_venue_mapping.py::_build_mapping()` already applies the right
     `None if sports else underlying.value` convention for its own (separate, matched-pair-only) output schema.
     Populating `InstrumentRecord.underlying` from this same pipeline at adapter-construction time is scoped as a
     migration, not fixed in this pass (see plan below).
   - **The operator's follow-up question — are these fields conceptually sensible for Prediction, and what's the real
     canonical scheme — is answered directly in `PREDICTION_INSTRUMENTS.md`**: `raw_symbol` is real venue-native data,
     not vestigial (was purely a rollup bug). `base_asset`'s VALUES are real but the field name is a poor fit for
     Prediction (Kalshi's value is a genuine venue grouping key; Polymarket's is a synthesized label whose shape varies
     by category — asset-like for crypto, instrument-id-like for sports, raw question text for "other"). `underlying` is
     the right field for the crypto/macro/commodity subset and correctly `None`/`OTHER` for the rest. The canonical
     scheme reuses what already exists rather than inventing a parallel mechanism, per the operator's framing ("pick one
     … from what exists"): `canonical_question_group` stays the family axis; `underlying` (adapter-populated from the
     existing classifier pipeline) + `canonical_instrument_id` (an already-existing `InstrumentRecord` field, currently
     unused for Prediction, populated from `cross_venue_mapping.build_cross_venue_mapping()`'s `canonical_event_id` when
     a real cross-venue pair exists) together are the per-instance axis. Sports specifically ties to the Sports asset
     group's own `build_fixture_id()` scheme (`{LEAGUE}:{HOME}_v_{AWAY}:{YYYYMMDD}`) — same information content today
     via two independent implementations (`SportsFixtureKey.pairing_key()` vs. `build_fixture_id()`), a real
     (currently-unwired) `_cross_reference_fixture()` method already sits in Polymarket's adapter for exactly this
     alignment.
   - **Migration scope** (adapter-level `underlying` population + cross-venue `canonical_instrument_id` wiring + sports
     fixture_id alignment) tracked in [[prediction_canonical_identity_migration_2026_07_08]] (`plans/active/`,
     `assigned_vm: NA`) — not implemented in this pass; requires adapter changes + a cross-venue join step that doesn't
     exist in the per-day write path today.
   - **Bucket-naming split — fixed for INSTRUMENTS, deliberately left for MARKET_DATA.**
     `unified_api_contracts/canonical/gcs_paths.py`'s `BUCKET_TEMPLATES_BY_ASSET_GROUP_KIND[(PREDICTION, INSTRUMENTS)]`
     templated the dead, unabbreviated `instruments-store-prediction-{env}-{project_id}` (confirmed 404;
     `instruments-store-pred-prd-central-element-323112` is the real bucket, 33,122 blobs) — now fixed to the
     abbreviated form. `BUCKET_TEMPLATES_BY_ASSET_GROUP_KIND[(PREDICTION, MARKET_DATA)]` was ALSO found unabbreviated
     (`market-data-tick-prediction-{env}-{project_id}`) and is ACTIVELY consumed by `market-data-processing-service`'s
     `DependencyChecker.UPSTREAM_DEPS_BY_ASSET_GROUP["PREDICTION"]` — but that long-form bucket is a real, still-live
     legacy bucket mid-migration to `market-data-tick-pred-prd-{pid}`
     (`market-tick-data-service/scripts/migrate_prediction_to_pred_prd_v9.py`,
     `prediction_manifest_canonicalisation_2026_06_01.md` §C), so it was deliberately left unchanged pending that
     migration's completion — flipping it now would point the dependency check at the less-complete bucket.

## What this is NOT

- Not a claim that any of these 6 are fixed today — every target format above is illustrative only, shown in the mockup
  as an explicit "NOT REAL — target canonical" 3rd sample alongside the real captured ones, same visual pattern as the
  A_TOKEN/DEBT_TOKEN decision's current-state-vs-target-state entries.
- Not a complete enumeration of every possible instrument_id anywhere — but coverage was extended 2026-07-08 (operator:
  "shouldl be evertyhting all AG that we expect shown in [the mockup] so we know how things will look") to every
  DEX-pool protocol×chain combination in the DeFi tab (27 total, not just a flagship sample), plus a deliberate check of
  TradFi/Sports/Prediction: TradFi's **single-leg** dated-derivative codes (e.g. `CME:FUTURE:6AF0`) were originally
  assessed as real industry-standard terse contract codes, not an uncleaned internal prefix like Kraken's — no
  divergence to canonicalize there. **REVERSED 2026-07-09 (operator)**: "I'd rather adjust tradfi... that's the whole
  point of cross-AG normalisation" — readability of ONE internal standard across every asset group outweighs preserving
  TradFi's real exchange-native terse codes. TradFi single-leg dated derivatives are now IN SCOPE for the same
  `@LIN`/`@INV`-`YYYYMMDD`[-`STRIKE`-`C`|`P`] target as CeFi (finding 1) — this carve-out is retracted, not narrowed.
  TradFi's multi-leg spreads (finding 7) were already in scope regardless; Sports fixture IDs are provider-native opaque
  identifiers, not VENUE:TYPE:SYMBOL keys; Prediction already routes through its own dedicated domain builder
  (`canonical/domain/prediction/prediction_mapping.py`) rather than the ad-hoc CeFi/DeFi pattern this doc is mainly
  about — but a dedicated builder existing doesn't mean its real output is canonical (see finding 8: it isn't, though
  that's a data-completeness gap more than a delimiter/syntax question, and is scoped separately from findings 1-7).
  DERIBIT-COMBO's underscore-in-strikes format was also checked and confirmed a real, internally consistent convention
  (not a canonicalization gap). A dedicated future audit could still find more instances of the 6 CeFi/DeFi divergence
  classes on venues/protocols this session never touched at all (this doc's scope is bounded by what this session's
  other findings happened to surface, not a from-scratch audit of the full instrument universe).
- **Filename-vs-instrument_id naming rule (settled 2026-07-08, operator)**: when a file/partition holds exactly one
  instrument's data, the filename is that instrument's full canonical instrument_id. When a file/partition holds a
  BUNDLE of related instruments for one underlying (e.g. an options/futures chain, or DeFi's many-pools-per-file
  pattern), the filename is the underlying_symbol only — not an attempt to cram multiple instrument_ids into one name.
  Hive-style partition-path directories (venue=/instrument_type=/data_type=/day=) are unaffected and stay exactly as
  they are — this rule is about the leaf filename only, not path structure. Operator intent going forward: "I'd rather
  migrate the GCS so that we do have canonical names" — even though venue/type can already be derived from the
  surrounding path for older files (e.g. bare `BTC-PERPETUAL.parquet`), the eventual GCS/filename migration (last stage
  in the sequencing under "Operator decisions" below) should move every single-instrument file to its full canonical
  instrument_id as the actual filename, not just rely on path-derivability.
- **RESOLVED 2026-07-08**: `canonical_id_builder.py` (or its successor) becomes the ONE enforced shared builder for
  EVERY asset group and instrument type, sports fixtures included — operator: "one builder for everything would make
  more sense... every asset group, every instrument type, can get its canonical instrument IDs, same with fixtures, just
  by filling in the right inputs." Per-domain builders that each independently canonicalize are explicitly REJECTED. See
  the dedicated builder-unification workstream tracked from this decision.

## Todos

- [ ] [SCRIPT] P2. **DEX-pool catalog regeneration (finding 2, all 13 protocols)** — real code is already correct for
      every protocol (see the per-protocol table in finding 2, 2026-07-08 update); the ONLY gap is that
      `prod/catalog.parquet`'s 6,180 DEX-pool rows predate the current adapter code and still show bare on-chain
      addresses with no `-CHAIN` venue suffix. Scope: re-run instrument discovery for all 13 protocol×chain combinations
      in the table above and rewrite/backfill the catalog rows in place (per the migration-mechanics decision below:
      rewrite already-captured rows from already-known data, not a fresh re-download) so `instrument_id` reflects the
      current adapter's structured `VENUE-CHAIN:POOL:BASE-QUOTE[:FEE]` shape. Do this AFTER (or together with) the 2
      Uniswap-V3/V4 fee-tier-delimiter code fixes noted in finding 2, so the regeneration produces the FINAL target
      shape (dash-separated bps fee tier) rather than needing a second regen pass immediately after.
- [ ] [DECISION] P2. **Confirm exact target quote-currency per on-chain-perp venue** (finding 4) — ASTER/PACIFICA/
      LIGHTER-ZKSYNC's real settlement currency needs a quick per-venue API check before the illustrative targets in
      this doc become real implementation targets (e.g. confirm ASTER really settles BTC-USDT in USDT, not some other
      stable).
- [x] [DECISION] P2. **Migration mechanics — RESOLVED 2026-07-08 (operator)**: always backfill/rewrite historical GCS
      rows in place AND correct going forward — never leave a legacy-format historical range unfixed. Mechanism:
      **rewrite/relabel already-downloaded data in place (re-derive the corrected instrument_id from already-captured
      raw fields and rewrite the parquet/partition), not a re-download from the source venue** — applies to every
      finding in this doc (Kraken-Futures historical collision, the dated-derivative `@LIN/@INV-YYYYMMDD` migration,
      TradFi combo/CBOE-VX decomposition, and any other backfill this canonicalization work triggers).
- [x] [VERIFY] P2. **DONE 2026-07-21 — no consumer keys off the manifest `instrument_id` VALUE (for tradfi at least;
      full consumer trace).** Traced every reader of `_index/availability_index.parquet`'s `instrument_id`: (1) served
      honest-coverage takes a seeded internally-consistent 4-state path (numerator+denominator from the same manifest,
      id string irrelevant); the one external-match path (`per_instrument_coverage` Tier-3) already NORMALISES ids
      (`_normalize_instrument_id_for_match` strips `@LIN`/`@INV`+whitespace) so a format change is absorbed, and is
      inactive for seeded tradfi dts anyway; (2) the catalogue/identity RENDER reads `prod/catalog.parquet`, not the
      manifest; (3) `measure_honest_coverage.py` uses the id only as a cross-bucket dedup-key component with a
      `(date,venue,data_type)` fallback; (4) MTDS `reader.py` resolves shards by
      `(venue,data_type,instrument_type,date,captured)`, never the id; (5) ml/strategy/execution guards read the
      features/strategy manifests keyed `asset_group×date`. **No consumer pattern-matches / parses the id string**, so a
      format change is a cosmetic cleanup, not a breaking change. Full evidence: the "✅ RESOLVED (c)/(d) — MOOTED"
      section in [[tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20]]. (Verified for tradfi end-to-end; the
      cefi/defi manifests share the same reader code paths, so the conclusion carries — but the id-normaliser's
      venue-token caveat still applies to a future full cefi/defi canonicalisation.)
- [x] [DECISION] P3. **Builder-architecture question — RESOLVED 2026-07-08 (operator)**: ONE shared builder for every
      asset group + instrument type + sports fixtures, filled in by structured inputs. See "What this is NOT" above for
      the exact decision language.
- [x] [SCRIPT] P1. **Fix the Bitfinex BTC-margined-perp asset-filter bug — DONE.** found 2026-07-08 while spot-checking
      real volume, not an instrument_id-format issue but adjacent (same investigative pass): the accepted-quote filter
      (`parsing.py:463`, `cefi_instrument_universe.py:131-133`) is documented "derivatives carry no quote and pass," but
      Bitfinex's own symbol parser (`parsing.py:325-339`) DOES extract a real quote for its inverse perps (`ETHF0:BTCF0`
      → base=ETH, quote=BTC), so real Bitfinex derivatives get rejected as if they were an exotic spot cross-pair.
      Confirmed live via `api-pub.bitfinex.com/v2/tickers`: `ETHF0:BTCF0` trades ~~2,034 ETH/day (~~$6-7M/day) — not a
      negligible edge case. Fix: add BTC to the per-venue accepted-quote extension for Bitfinex derivatives, same
      mechanism already used for UPBIT's KRW extension. **Verified 2026-07-13**: already shipped
      `unified-api-contracts@4e096316` (confirmed integrated, ancestor of current HEAD) —
      `_CEFI_VENUE_QUOTE_EXTENSIONS["BITFINEX-FUTURES"] = frozenset({"BTC"})`, keyed on the FULL canonical venue string
      so the extension does not leak into `BITFINEX-SPOT`. Functional re-test:
      `_passes_asset_filter("ETH", "BTC",     "PERPETUAL", "BITFINEX-FUTURES")` → `True`;
      `_passes_asset_filter("ETH", "BTC", "SPOT_PAIR", "BITFINEX-SPOT")` → `False` (cross-pair still correctly
      rejected). This todo had gone unchecked despite the fix already landing — caught during a 2026-07-13 full-epic
      status re-verification.
- [x] [DECISION] P1. **Confirm the revised TradFi combo fix — DONE 2026-07-09** (finding 7, superseding the earlier
      flat-string proposal) — reuse the existing `InstrumentLeg`/`InstrumentType.COMBO` infrastructure (already proven
      for CME) for CBOE/VX spreads too, apply the existing `_resolve_product_root()` human-name registry (`ES→SP500`,
      `GC→GOLD`, `VX→VIX`) to leg symbols, and drop the redundant per-leg `VENUE:` prefix. **Real row-count correction,
      twice over**: the original 34,017/4,211/5 (2/3/4-leg) figures above were wrong (never reproducible against real
      data); the 2026-07-08 fix-plan pass corrected this to 4,211(2-leg)+5(3-leg)=4,216, 0 four-leg; a FRESH re-read one
      calendar day later (2026-07-09, this finding's completion pass) found the real population had shrunk to 91 rows
      (all 2-leg) — real, expected volatility (`prod/catalog.parquet` is a lifecycle catalogue for short-dated
      instruments; see the dedicated plan's Progress Log for the full mechanism). Code shipped instruments-service (this
      session); the historical catalog migration ran once 2026-07-08 but was found NOT durable — a subsequent
      independent catalog-rollup regeneration (`build_instrument_catalogue.py`, 2026-07-09 01:03 UTC) re-derived
      `SPOT_PAIR` for the still-unmigrated historical by_date corpus, re-surfacing a 91-row (CBOE) + 312-row (DBEQ,
      adjacent K→EQUITY finding) residual population. Full evidence + the not-yet-implemented TradFi single-leg
      `@LIN`/`@INV` extension (finding 1's 2026-07-09 scope reversal) tracked in
      [[canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08]].
- [x] [SCRIPT] P1. **File a dedicated fix plan for finding 7** — real code gap (CBOE/VX spreads bypass existing
      leg-decomposition infrastructure entirely), not just a naming decision; independently shippable, same pattern as
      the P0 fix plans. Filed: [[canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08]]. Repo:
      instruments-service.
- [x] [DATA] P2. **Investigate `prediction_mapping.py`'s real extraction logic — RESOLVED 2026-07-08.** The short
      readable ids (e.g. `BNB_PRICE_RANGE_DAILY`) are `canonical_question_group` cluster-grain rows, confirmed
      correct-as-designed (see "What this is NOT"), not a `prediction_mapping.py` artifact —
      `PredictionMarketMapper.canonical_id` is computed but discarded, never reaching any `InstrumentRecord` field. The
      real `base_asset`/`raw_symbol` NULL cause: dropped in
      `instruments-service/scripts/build_instrument_catalogue.py::build_prediction_catalogue_dataframe()`'s
      per-conditionId accumulator (never read those columns off the per-day rows) — FIXED same-session. `underlying` was
      never computed upstream at all (no bug to fix there; a real adapter-level migration to populate it is scoped in
      [[prediction_canonical_identity_migration_2026_07_08]]). See finding 8 above +
      `instruments-service/docs/PREDICTION_INSTRUMENTS.md` § "Canonical identity model" for the full write-up. Evidence:
      instruments-service@<pending quickmerge sha>.

## Progress Log

- **2026-07-08** — Filed after the operator reviewed the KRAKEN-FUTURES:FUTURE mockup entry (which showed real-vs-
  illustrative-canonical as a bare 3rd sample row with no decision attached) and asked directly whether the workspace is
  actually moving to canonical everywhere. Given the choice between leaving it unscoped vs deciding now with full scope,
  operator chose full scope. All 6 divergences enumerated here were already discovered during this session's mockup
  backfill pass (2026-07-08) — this doc is the first time they're captured as a decided target-state rather than
  scattered mockup bug notes. No implementation work done yet; migration mechanics are an open todo.
- **2026-07-08 (later same day)** — Operator asked for full-AG coverage in the mockup itself ("shouldl be evertyhting
  all AG that we expect shown in [the mockup] so we know how things will look"), not just the initially-touched sample
  entries. Extended the CURRENT-vs-TARGET-STATE mockup treatment to all 27 real DEX-pool protocol×chain combinations in
  the DeFi tab (previously only 1 flagship example had it). Checked TradFi/Sports/Prediction for the same 6 divergence
  classes and confirmed none apply there (see updated "What this is NOT" section above) — not silently skipped, actively
  ruled out. DERIBIT-COMBO's underscore-in-strikes format also checked and confirmed real/consistent, not a gap.
- **2026-07-08 (later still)** — Operator spot-checked the mockup's CeFi tab directly and caught 3 more things in one
  pass: (1) `BYBIT:FUTURE:BTCUSDT-25DEC26` was fabricated — real is `BYBIT:FUTURE:BTC-01DEC23` (no quote at all, DDMMMYY
  date), fixed; (2) bare `OKX`'s empty PERPETUAL/FUTURE leaves had no cross-reference to where the real data actually
  lives (OKX-SWAP/OKX-FUTURES) — added; (3) surfaced the margin-marker and date-format inconsistency described in
  finding #1 above, which got settled into the two explicit sub-decisions now recorded there. Separately, operator asked
  whether Bitfinex's dropped BTC-margined perps have real volume — checked live, they do (~$6-7M/day on the top one),
  added as a new P1 SCRIPT todo since it's a real, evidence-backed, non-negligible bug, not just a documented gap.
- **2026-07-08 (final)** — A full 7-layer canonical instrument_id audit ([[canonical_instrument_id_audit_2026_07_08]],
  `plans/audit/results/`) ran (6-agent Workflow + 1 strategy-service follow-up), found the scope is far larger than this
  doc's original 6 findings: 5 real P0 live-correctness bugs (Kraken-Futures 5-instrument data collision, silently
  -defeated live reconciliation for every CCXT venue, 23 DeFi adapters silently returning empty on type filters, a
  live≠batch id divergence for 13 CeFi venues, deployment-api cross-service exact-match bugs) plus ~40 more P1/P2
  findings. Operator reviewed and made several corrections + decisions: sports keeps its own ID scheme (not forced into
  VENUE:TYPE:SYMBOL); the 31 shared `canonical_question_group` keys between Polymarket/Kalshi are NOT a collision (venue
  is tracked separately, sharing the label is the intended cross-venue-arb mechanism, same as sports fixtures); no
  trailing `@VENUE`; real builder-function enforcement required, not docstrings; DEX-pool fee tier must be in the
  canonical symbol (real basis-point values); whitespace-as-delimiter is never acceptable; DeFi mirrors CeFi's shape.
  Full scope now: audit (done) → decisions (mostly done) → ground-up migration (UAC → instruments- service → MTDS →
  strategy-service → deployment, live breakage explicitly authorized) → mockup refresh → GCS/ manifest/filename
  migrations (spec'd + executed) → MTDS resumes downloading the remaining MVP universe. Tracked under existing epics
  (`instruments_master` primary, cross-referenced from `batch_live_symmetry_master` and
  `client_isolation_and_governance_master`) per operator decision, not a new epic — this workspace's epic registry is a
  fixed 20-entry table. 4 new P0 fix plans filed for the live bugs (see `related:` above), each independently shippable
  ahead of the broader canonicalization decision.
- **2026-07-08 (even later)** — Before starting the docs-consolidation Phase 3 rewrite, operator asked whether any more
  cross-AG instrument_id conflicts remain. Pulled real `prod/catalog.parquet` evidence for TradFi and Prediction (not
  previously read row-by-row, only spot-checked). Found 2 more real divergences, added as findings 7-8 above: TradFi's
  multi-leg spreads reuse the `SPOT_PAIR` type and whitespace-pad a dash as an uncontrolled leg-separator (real example,
  a VIX calendar spread: `CBOE:SPOT_PAIR:VX/F1:1:S - VX/G1:1:B`) — proposed a target, pending confirmation; Prediction's
  per-market instrument_id is a genuine mix of bare on-chain hashes and short shared labels, with
  `base_asset`/`underlying`/`raw_symbol` 100% NULL across all 2.48M rows — flagged as needing investigation into
  `prediction_mapping.py`'s real extraction logic before any target format gets proposed (deeper than a delimiter
  question). Also reconfirmed the audit's bucket-naming bug is real and still live (`instruments-store-pred-prd` exists,
  `instruments-store-prediction` 404s). Also settled a new rule from the operator on filename-vs-instrument_id:
  single-instrument files get the full canonical instrument_id as filename; bundle-of-many-instruments files (options
  chains, DeFi's many-pools-per-file) get just the underlying_symbol — path/partition structure is unaffected, this is
  about the leaf filename only. Operator confirmed intent to eventually migrate GCS filenames to true canonical form
  (not just rely on path-derivability), sequenced as part of the already-planned GCS/manifest/filename migration stage.
- **2026-07-08 (final)** — Operator correctly pushed back on the initial flat-string TradFi spread proposal
  (`VENUE:SPREAD:LEG-RATIO-SIDE;...` using raw exchange tickers) as not actually human-readable canonical, and
  articulated the real requirement: drop redundant per-leg venue, keep per-leg type + a REAL translated symbol (not
  exchange jargon), signed/labeled direction, ratio. Investigating found this isn't a from-scratch design question —
  `InstrumentLeg`/`InstrumentType.COMBO` + a ticker→human-name registry (`ES→SP500`, `GC→GOLD`, `VX→VIX`) already exist
  and are already used for CME calendar spreads; CBOE/VX spreads are just explicitly excluded from that pathway today
  (dropped, not decomposed), and even the working CME path doesn't yet apply the human-name translation or drop the
  per-leg venue redundancy. Finding 7 rewritten to reflect this; recommended it become its own fix plan (real code gap,
  not a design decision) rather than something resolved purely in this doc.
- **2026-07-08 (finding 8 resolved)** — Operator asked two things together: diagnose the null-fields root cause, and
  answer directly whether `base_asset`/`underlying`/`raw_symbol` even make conceptual sense for Prediction given its
  real matching mechanism is cross-venue question-group sharing, not a base/quote pair. Traced the write path
  end-to-end: both adapters populate `base_asset`/`raw_symbol` correctly at `InstrumentRecord` construction, and
  `process_write.py` correctly serializes them into the per-day GCS snapshots — the NULL happened one level up, in
  `build_instrument_catalogue.py::build_prediction_catalogue_dataframe()`'s dedicated multi-grain roll-up, which never
  read those two columns off the per-day rows into its accumulator (unlike the generic roll-up every other asset group
  uses). Fixed (instruments-service). `underlying` is a different, non-bug case — no adapter ever computes it; read
  `cross_venue_mapping.py` (the real per-instrument Kalshi↔Polymarket matcher — this IS the "something we already have"
  the operator referenced) and `two_axis.py`'s comprehensive `PredictionUnderlying` axis in full: confirmed `underlying`
  is conceptually sound for crypto/macro/commodity markets and correctly None/OTHER for the rest (politics/sports),
  matching a convention `cross_venue_mapping.py` already applies for its own output. Proposed and documented (in
  `PREDICTION_INSTRUMENTS.md`) ONE canonical scheme reusing existing mechanisms: `canonical_question_group` (family
  axis, unchanged) + `underlying` (adapter-populated from the existing classifier, migration) +
  `canonical_instrument_id` (an existing-but-unused `InstrumentRecord` field, populated from `cross_venue_mapping`'s
  `canonical_event_id`, migration) — with sports additionally tying to the Sports asset group's own `build_fixture_id()`
  scheme via a currently-unwired `_cross_reference_fixture()` method already sitting in the Polymarket adapter. Also
  fixed the `gcs_paths.py` dead `instruments-store-prediction-*` bucket template (INSTRUMENTS kind only — the
  MARKET_DATA kind's long form is a real, still-live legacy bucket mid-migration per a separate 2026-06-01 plan,
  deliberately left alone). Filed [[prediction_canonical_identity_migration_2026_07_08]] for the remaining adapter-level
  migration work.
- **2026-07-08 (finding 2, all 13 DEX-pool protocols individually re-verified)** — Follow-up to the earlier
  Uniswap-V3-only reconciliation: read `prod/catalog.parquet` directly (6,180 real DEX-pool rows across all 13
  protocols) and traced every protocol's adapter code (4 independent adapter classes — Uniswap V2/V3/V4, Balancer, Curve
  — plus 8 protocols confirmed to share `UniswapV3ReferenceDataAdapter` via `factory.py`'s `protocol_slug` routing, so
  verifying Uniswap V3's code transitively covers those 8). Result: every one of the 13 protocols shows the identical
  shape — real adapter code already builds a structured `VENUE-CHAIN:POOL:BASE-QUOTE[:FEE]` key, but the persisted
  catalog uniformly still shows the old bare on-chain address with no chain suffix. Zero code gaps found in any of the
  13 — confirms this is purely a catalog-regeneration/backfill gap, not a from-scratch code problem for any protocol.
  Added the full per-protocol table to finding 2 and a dedicated regeneration todo (does not attempt the actual regen in
  this pass — that's a real backfill job, scoped separately). Evidence: instruments-service (no code changes needed for
  this finding — verification only).
- **2026-07-09 (finding 7 completion pass)** — Inherited the finding-7 fix plan's dead WIP (stalled sibling agent, dirty
  tree, no commit) and completed it: CBOE/VX leg decomposition, human-name translation, venue-prefix drop,
  `SPOT_PAIR`→`COMBO` correction, the adjacent Databento `K`→`EQUITY` bug (100% of fresh NASDAQ/NYSE equity captures
  were mistyped `SPOT_PAIR`), and IBKR's `_SEC_TYPE_MAP` collapse (`STK`/`BOND`/`CASH` all→`SPOT_PAIR`, now→`EQUITY`/
  `BOND`/`CURRENCY`) — full evidence in [[canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08]]'s Progress Log.
  Fixed a real pre-existing test regression blocking `quality-gates.sh` (stale 2-arg calls to
  `_parse_cme_calendar_spread_legs` after its signature was narrowed to 1 arg mid-WIP). **New, real finding**: the
  historical `prod/catalog.parquet` in-place migration (already run once, 2026-07-08) is NOT durable —
  `build_instrument_catalogue.py`'s self-refreshing roll-up regenerated the entire catalog from the still-unmigrated
  per-day corpus 2026-07-09 01:03 UTC, silently reverting part of the fix (91 of 4,216 CBOE rows, 312 of 318 DBEQ rows
  re-surfaced as their pre-fix type — confirmed via GCS blob timestamps + a row-level diff against the pre-migration
  snapshot, not new pollution). The durable fix is the CODE change (every future capture is correct); the historical
  by_date corpus itself remains unmigrated (single-walk-discipline-gated, deferred) and is now the real blocker to a
  durable historical fix, not a nice-to-have. **Also confirmed NOT done**: the TradFi single-leg
  `@LIN`/`@INV`-`YYYYMMDD` extension this doc's finding 1 scope-reversal (2026-07-09) calls for — a separate, comparably
  large migration (every TradFi `FUTURE`/`OPTION` build site across 2 adapters + its own historical migration),
  correctly out of scope for the finding-7 combo/leg fix plan; recommend a dedicated fix plan, same pattern as finding 7
  got. 4 commits **committed** instruments-service (3 pre-existing verified commits that were blocked by this WIP's test
  regression, plus this session's combo/leg + IBKR + K-fix work) — see the fix plan's Progress Log for SHAs.
  **Correction, verified via direct `git fetch` + log comparison 2026-07-09**: these 4 commits (`6a1122e5`, `a326f6b9`,
  `57f8a754`, `1a696db7`) are still **local-only on the instruments-service clone**, NOT yet on
  `origin/live-defi-rollout` — "landed" above should read "committed, push pending." Check current real state before
  assuming this is stale:
  `cd instruments-service && git fetch origin live-defi-rollout && git log origin/live-defi-rollout..HEAD --oneline`.

- **2026-07-09 — CRITICAL cross-venue finding: catalog.parquet fixes are NOT durable on their own.**
  `build_instrument_catalogue.py`'s self-refreshing rollup regenerates the entire catalog from the still-unmigrated
  per-day `instrument_availability/by_date/` corpus on every real regen run — confirmed for CBOE/DBEQ (91 of 4,216 CBOE
  rows + 312 of 318 DBEQ rows silently reverted to their pre-fix type after a 2026-07-09 01:03 UTC regen, verified via
  GCS blob timestamps + a row-level diff against the pre-migration snapshot). **This is not TradFi-specific** — the same
  rollup mechanism serves every venue in this doc's scope, so any catalog-level fix for
  Bybit/Kraken/Deribit/OKX/Binance/on-chain-perp/DEX-pool is equally at risk of silent reversion on the next regen
  unless the underlying per-day corpus is ALSO migrated, not just the catalog snapshot. This is why the in-flight
  full-historical-sweep work (below) was scoped to include the per-day corpus, not catalog.parquet alone — treat any
  catalog-only fix reported by an agent as **provisional**, not durable, until its per-day corpus is confirmed migrated
  too.

- **2026-07-15 — cross-reference, not a duplicate finding**: a related but DISTINCT defect —
  `[[cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15]]` (`issues/`) — was found + fixed this
  date. That doc's own framing: "NOT the same defect as this doc — that one is the CATALOGUE's
  `InstrumentRecord.canonical_instrument_id` (fixed via `instruments-service@f90d0e0`,
  `[[canonical_instrument_id_cefi_defi_backfill_2026_07_14]]`); this is MTDS's `TardisAdapter` manifest **write** path
  specifically, which stamped the raw vendor wire symbol as the captured row's `instrument_id` regardless of what the
  catalogue carries." Fixed `market-tick-data-service@56679e78`→`5d44a197` (case-sensitivity supersession)→`90ecde17`
  (persisted tests + honest-absence follow-up). That doc is the SSOT for this specific write-path defect + its remaining
  todos (VM relaunch, relabel `--apply` sign-off, a newly-filed Tier-3 sentinel scheme-mismatch finding) — not
  duplicated here.

## Orchestration state, 2026-07-09 — durable record of in-flight parallel work (for context-loss recovery)

Following the operator's directive to execute this doc's findings entirely including data migration, "so there is zero
trace of the old formats in doc, data, or manifest," work was fanned out across multiple `Workflow` tool runs (scripts
persisted to disk, resumable independent of any chat session). If context is lost, use
`Workflow({scriptPath, resumeFromRunId})` with the paths below — completed agent() calls replay from cache, only the
unfinished tail re-runs.

**Landed on `origin/live-defi-rollout` (verified via direct `git fetch` + log comparison, not agent self-report):**

- `unified-api-contracts@06edd868` + `07d22bdf` — 900-line file-size split (`mvp_scope.py`/`honest_coverage.py`/
  `source_priority.py`/`tradfi_ticker_universe.py`) + `canonical_id_builder.py`'s `margin_marker` kwarg.
- `instruments-service@176d4610` (Bybit/Kraken-Futures margin-type bugs + `@LIN`/`@INV` builder), `@554ef058` (OKX
  margin-type inversion bug), `@7fbc38c1` (Deribit OPTION `@LIN`/`@INV`-`YYYYMMDD`), `@4e072d93` (DEX-pool fee-tier
  dash+bps), `@0d0c3742` (Prediction underlying + cross-venue canonical_instrument_id).
- `market-tick-data-service@19357ad4` (OKX venue-key fix), `@1e8870b1` (on-chain-perp live connectors + manifest
  migration script).

**UPDATE 2026-07-09 — `wf_41d76b71-c79` COMPLETED and independently verified (SHA + content + isolated clean-worktree
test run, not self-report).** `instruments-service@6a1122e5` (`git rev-parse HEAD origin/live-defi-rollout` both return
`6a1122e5b59c1d57b50f9e6d5f676eac8ea7fb12`) plus the 3 previously-local commits (`a326f6b9`, `57f8a754`, `1a696db7`) are
now ALL genuinely on `origin/live-defi-rollout` — this section's prior "committed locally, not yet on origin" is now
stale, kept only as history. Also landed: `unified-trading-pm@f05b57f93`, a real `quickmerge.sh` bug fix (the "already
committed, skip to push" check previously required the WHOLE working tree to be porcelain-clean, essentially never true
in this heavily concurrent shared-tree session — scoped to `--files` instead; may reduce false quickmerge blocks for
every other in-flight agent). Verification also reconfirmed the catalog-durability finding above with direct evidence
(91/312 rows re-surfaced identically after a roll-up 6h post-fix, 0 new pollution).

**In-flight `Workflow` runs (script + run ID, resumable):**

1. `wf_41d76b71-c79` — `tradfi-combo-inherit-and-land` — **COMPLETE**, verified landed (see update above). Script:
   `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/tradfi-combo-inherit-and-land-wf_41d76b71-c79.js`
2. `wf_c4796aec-f35` — `canonical-id-full-historical-sweep` — real (non-smoke-test) catalog + per-day-corpus + GCS
   filename migrations for Bybit/Kraken, Deribit, OKX, on-chain-perp, DEX-pool, Binance. Script:
   `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/canonical-id-full-historical-sweep-wf_c4796aec-f35.js`
3. `wf_118d8268-18c` — `mtds-canonical-symbol-migration` — discovers + migrates MTDS raw trade-tick/orderbook `symbol`
   values (not the full instrument_id) to the canonical symbol shape, per venue family (operator: "every single value,
   parquet file, etc., needs to be part of the scope" — full instrument_id prefix not required for raw ticks, but the
   symbol portion is). Script:
   `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/mtds-canonical-symbol-migration-wf_118d8268-18c.js`

**Still queued:** wiring the shared live-construction path
(`instruments_service/reference_data/adapters/cefi/ tardis/adapter.py`, `ccxt_adapter.py`) for
Bybit/Kraken/OKX/Deribit/Binance's PERPETUAL/FUTURE/OPTION `instrument_key` — every sibling agent this session deferred
touching this shared file due to lock contention with the TradFi WIP, now cleared per the update above; dispatching now.
A final cross-repo zero-old-format-traces verification pass is also queued behind all of the above.

**UPDATE 2026-07-09 — dispatched `wf_9e5f13e3-962`** — `live-wiring-plus-legacy-naming-audit` — wires the shared
live-construction path (`tardis/adapter.py`, `ccxt_adapter.py`) so new captures emit `@LIN`/`@INV` directly, PLUS the
generalized CeFi + DeFi legacy-GCS-naming audit decided below, then verifies both. Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-unified-trading-pm/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/live-wiring-plus-legacy-naming-audit-wf_9e5f13e3-962.js`

**UPDATE 2026-07-09 — `wf_118d8268-18c` (MTDS raw-tick symbol migration) COMPLETE, all 10 stages (5 discover + 5
migrate) done.** Real per-family outcome:

- **on-chain-perp — 100% COMPLETE.** Code shipped `market-tick-data-service@b416ffce96e9` (PR #498, CI green, pending
  automerge); real bugs fixed across all 5 venues' native write paths + live filename sanitization. Historical migration
  independently, comprehensively verified (not sampled): **38,883/38,883 real files canonical, 0 remaining** for
  LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET (a real duplicate-shape consolidation found and fixed along the way),
  plus EXTENDED-STARKNET's manifest (1,175/1,209 rows). Survived 6 background-process kills via idempotent restarts,
  verified against real GCS state each time. ASTER/HYPERLIQUID's own historical rename + Tardis-archive post-fetch remap
  for LIGHTER/PACIFICA/EXTENDED were correctly deferred (real file-lock conflicts with concurrent sibling agents, not
  scope avoidance) — flagged as follow-ups.
- **cefi-dated-perps — code shipped, historical backfill NOT completed this session (environmental, not a code
  defect).** `market-tick-data-service@3ee21c8c` fixes 3 real bugs: OKX-FUTURES dated futures silently written as
  `perpetual` (regex never matched OKX's dash+6-digit shape), Bybit's glued base/quote parsed wrong
  (`BTCUSDT-10JUL26`→`BTC` needed quote-suffix stripping), and a dead `normalise_kraken_futures_symbol` now wired into
  the write path. The historical migration script is real and tested (a clean 81/81-file dry-run) but hit a reproducible
  environmental GCS stall (list/download calls 4-5x slower than normal) across 3 attempts with **zero real writes
  landed** — needs a re-run in a less-contended window, the tool itself is ready.
- **TradFi single-leg — code fixed, historical migration running (now on VM, see below), and a large NEW gap found**:
  120,946 CME `options_chain` entries (**~187.5M rows**) sit under a different, unverified legacy per-contract/spread
  flat layout this fix does NOT cover — correctly excluded rather than risked at that scale, documented in
  `docs/TRADFI_INSTRUMENTS.md` as its own open follow-up, not silently dropped.
- **DEX-pool — code shipped `market-tick-data-service@0ce28623`, historical migration running (now on VM, see below),
  and 2 NEW gaps found**: (1) a **second, distinct writer path** (`0x<address>.parquet` per-pool files, no
  `symbol`/`venue`/`chain` columns, under `pipeline_mode=batch_onchain_subgraph`, confirmed live for CURVE) whose
  forward code is already fixed (different commit `0713c01a`) but whose historical backlog needs its own separate
  migration — correctly skipped, not mis-touched, by the current script; (2) confirmed via repo-wide grep that
  `uniswap_v2`/`uniswap_v4`/`trader_joe_v2`/`velodrome_v2` have **zero forward capture code at all** in
  `dex_pools_handler.py`/`dex_swaps_handler.py` — a real, pre-existing, separate gap.
- **Prediction — code + a real performance bug fixed, historical migration running (2 of 5 shards now on VM)**: found or
  worker counts above 32 made throughput WORSE (128 workers slower than 32) due to undersized HTTP connection pools on 3
  separate client instances (main session, OAuth refresh session, listing client) — fixed by widening the pool. A
  further hardening fix was tested clean but not committed (its own QG run was CPU-starved by the 5 live migration
  shards, correctly not force-shipped) — flagged as a follow-up.

All 5 families' migration scripts are real, backup-first (copy-to-new-key or explicit backup-before-overwrite), and
idempotent/resumable — safe against interruption. The TradFi and DEX-pool historical runs referenced above are the same
ones already moved to VMs in the local-migration-audit update further up this Progress Log.

**OPERATOR DECISION 2026-07-09 — prefer real VM-based execution over session-tied agent execution for the remaining
heavy migrations, because "I will have to leave my laptop at some point."** All 4 `Workflow` runs above execute as
background tasks tied to the operator's current interactive session — if that session ends (laptop closed/asleep), any
in-progress, not-yet-committed/not-yet-written work in them is at risk. Real GCS spot VMs, once launched and verified
started, run independently of any laptop or session — matching this workspace's existing
`codex/05-infrastructure/spot-vms-for-backfill.md` pattern (SPOT by default, no fire-and-forget: verify STARTED<60s +
real progress within the first ~10min, then let it run unattended to completion). Dispatched a survey+launch agent to:
(1) check real current state so no VM is launched for work the session agents already finished, (2) launch real spot VMs
for genuinely large remaining pieces (Binance per-day corpus if still pending, on-chain-perp's ~19,255-object
legacy-naming gap, MTDS's real migration once its discovery scope is known, and any large CeFi/DeFi legacy-naming
migration found), each verified-started before being left to run unattended. **Operator also confirmed (same message)**:
every migration in this effort should move straight from smoke-test-verified to the real full run, not pause for a
second go/no-go — already the standing instruction given to every dispatched agent this session, reconfirmed here.
Report pending — once it lands, this section will be updated with real VM names/instance IDs and how to check on them
from a future session.

**UPDATE 2026-07-09 — VM survey/launch agent reported back. Real result: mostly NOT needed (session agents already
finished the big items); the one genuine VM candidate was ATTEMPTED and FAILED, reverted to local.** Confirmed DONE and
durable via real log evidence (no VM needed): Binance per-day corpus (9,234 files), Bybit/Kraken per-day corpus (9,560
files), Deribit per-day corpus (5,342 files), DEX-pool catalog write-back (`instruments-service@bcfdef1a`). **The one
real VM candidate — on-chain-perp LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET (38,884 files, ~60min projected) —
did NOT end up durably on a VM**: v1 launch failed at boot (`unified-api-contracts` install failure, fixed via
`SETUPTOOLS_SCM_PRETEND_VERSION`), v2 booted and briefly ran real work then stalled (process alive via SSH but zero new
log lines for 5+ min) — agent deleted it under time pressure rather than debug further, and reverted to running the job
**locally** (session-tied again, reduced to 20 workers to fix a real connection-pool contention root cause). No orphaned
VMs confirmed (`onchain-perp-symbol-canon-20260709-123056` verified TERMINATED via direct
`gcloud compute instances list`, not billing). **This directly does not yet satisfy the operator's stated durability
need** — flagging for a proper retry with real stall-debugging (SSH in and diagnose, don't abandon after 5 min) rather
than accepting local execution as the final state.

**Also found, real and still open:**

- ASTER/HYPERLIQUID legacy bare-symbol-shape gap (~19,255 objects): the path-based venue-parsing regex extension looks
  complete in code but is UNCOMMITTED and unvalidated; a fresh dry-run for real numbers has been running 25+ min on the
  initial GCS listing alone (confirmed still alive via direct process check, not obviously hung — GCS listing over a
  huge prefix can genuinely take a while — but no real numbers yet as of this update).
- OKX per-day `@LIN`/`@INV` migration: **no script exists yet** (only a narrower margin_type-only fix shipped earlier);
  confirmed via direct GCS sampling the per-day corpus is still 0% migrated. Blocked on
  `ccxt_adapter.py`/`tardis/adapter.py` live-wiring landing first (`wf_9e5f13e3-962`, still in flight).
- **NEW real finding — CeFi/DeFi legacy-naming audit surfaced a genuine ghost-venue-merge problem**, e.g.
  `UNISWAPV2-ETHEREUM` vs `UNISWAP_V2-ETHEREUM`, `AAVEV3-*` vs `AAVE_V3-*` (echoes the already-known AAVE_V3-OPTIMISM
  misspelling finding 5 above, but broader) — large real scope (many venue-pairs × 1,000-2,300 days each); a sibling
  agent has scaled this to a full local `--apply --workers 48` run as of 13:41 BST — durability status of that run not
  yet independently confirmed.
- TradFi single-leg product-root extension + Prediction instrument-id wrap: both newly-written, still in incremental
  sample-size validation, not yet at full scope.

**UPDATE 2026-07-09 — real gap found in the VM launch itself: it was NOT properly registered for monitoring.** Operator
asked directly whether these migration VMs launch through deployment-service such that they surface in the real
monitoring (deployment-ui `/deployments`, `/cockpit`, Slack, fleet reconciliation) — verified via direct code read that
they did NOT. `deployment-service/scripts/vm/vm_zombie_watchdog.py:762-768`'s `VM_PREFIX_TO_BUCKET` registry (the SSOT
`classify_deployment_target()` longest-prefix-matches against, raising `UnclassifiedDeploymentError` — never a silent
default, per `codex/05-infrastructure/deployment-observability.md`) only recognizes
`canonical-migration-{cefi,tradfi,defi,prediction,legacy}-` prefixes. The prior agent's ad hoc VM name
(`onchain-perp-symbol-canon-...`) matched none of them — it would have surfaced as `UNKNOWN` in
`/api/fleet/reconciliation` (subject to classify-or-kill), never shown in deployment-ui/cockpit/Slack. Real, existing,
purpose-built tool found: `deployment-service/scripts/vm/launch-canonical-migration-vm.sh`
(`Epic: infrastructure_master`, `Lifecycle: oneoff`) already does correct naming/bootstrap (`setup-data-pipeline-vm.sh`,
durable log streaming)/labels — but its `_script_for()` is hardcoded to the older v9 flat→hive canonical-migration
tools, not this session's `@LIN`/`@INV`/legacy-naming scripts. **Corrected instruction issued to the in-flight retry
agent**: either extend `launch-canonical-migration-vm.sh` with a new case for this session's real migration scripts
(preferred — ships via quickmerge in `deployment-service`), or at minimum name any new VM
`canonical-migration-cefi-<timestamp>[-suffix]` (on-chain-perp is already classified under the `cefi` asset group) +
reuse `setup-data-pipeline-vm.sh` + the same metadata/label shape — never an unregistered ad hoc prefix. Report pending.

**UPDATE 2026-07-09 — on-chain-perp symbol-canonicalization DONE, verified, real completion evidence.** Diagnosed the
earlier 404 volume as harmless: 3-4 overlapping local copies of the same idempotent job were hammering the same GCS
prefix from one laptop's network stack, starving connection pools — not a real data bug (download→backup→
upload-new→delete-old ordering makes an interrupted run always safely resumable, confirmed by reading the script).
Relaunched the VM (still the ad hoc `onchain-perp-symbol-canon-*` name — real gap above NOT yet fixed, flagged as a
"don't reuse as-is" for the next migration VM rather than fixed this time since there was no pending future launch to
correct) — booted clean this time, processed all **38,884 files in ~9 minutes**,
`{'skip_already_migrated_prior_run': 9232, 'migrated': 29652}` (sums to 38,884, 0 errors), self-terminated after. Real
GCS spot-check post-run confirms canonical filenames present, zero bare-symbol shapes remain in the sample checked.
Redundant local copy killed once the VM was confirmed healthy. **The naming-registration gap is NOT yet fixed in code**
— next VM launch for this effort MUST either extend `launch-canonical-migration-vm.sh` or use a properly-registered
prefix; do not reuse the scratchpad script again.

**Ghost-venue-merge** (`instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py`,
`UNISWAPV2-ETHEREUM` vs `UNISWAP_V2-ETHEREUM` etc., `--apply --workers 48`): **DONE** —
`total=33003 ok=32992 failed=11 total_ghost_rows=2309519 total_merged_rows=2823314`, real completion log confirmed
(`full_apply_run.log`), 99.97% success.

**UPDATE 2026-07-09 — real audit of ALL concurrently-running local migrations found the durability risk was broader than
the single job first flagged, and a real (not cosmetic) data-loss mechanism.** A full re-check found **9 real local
Python migration processes running simultaneously**, none on a VM. Re-verified real current ETAs (not the stale
first-pass numbers): TradFi single-leg (~6.5h), **DEX-pool symbol-shape (~12.6h — actually the longest, not TradFi)**,
on-chain-perp HL/ASTER (~5-6h, mid-scan), on-chain-perp LIGHTER/PACIFICA/EXTENDED (~1.1h), 5 sharded Prediction jobs
(~1.3h/1.3h/2.3h/**8.2h**/**9.1h**).

**Real finding on the connection-pool warnings**: two distinct phenomena. "Connection pool is full, discarding
connection" (thousands of occurrences) is cosmetic urllib3 noise, zero correlation with real failures. But real
`BrokenPipeError`/`ConnectionResetError`/`SSLEOFError` exceptions (logged as actual errors, each a genuinely
lost/skipped shard, not auto-retried) clustered in the same 1-2 second windows across unrelated processes — real local
resource contention from 9 concurrent processes (several 48-96 workers each) hammering GCS simultaneously. **Confirmed
causally**: DEX-pool's climbing error count (11→45→96) and on-chain-perp's went flat immediately after killing the 2
heaviest local processes — reducing local concurrency measurably improves correctness, not just laptop-closing
durability. Failure rate ~0.1-0.3% of objects, shard-isolated (no corruption) but not auto-retried — needs a small
follow-up remediation pass over each job's `error`-tagged shards once done.

**Moved to properly-registered VMs** (first real use of the corrected naming pattern):
`canonical-migration-tradfi-20260709-160919` (TradFi single-leg — real ~26x speedup once off the shared laptop
connection pool, 145 obj/s vs 5.5 obj/s local, new ETA ~15min not 6.5h) and `canonical-migration-defi-20260709-161510`
(DEX-pool — was the real worst offender: longest ETA + climbing real error count). Both bucket targets verified
byte-identical to the local runs before trusting them; both confirmed healthy via real `run.log` content. **Note**: the
TradFi run used `--skip-manifest` — the `_index/ availability_index.parquet` manifest rewrite is a separate follow-up
once the VM's GCS pass completes, not yet done.

**Left running locally, with real reasoning**: 3 short jobs (~1.1-2.3h each, low/zero errors) — fine as-is.
On-chain-perp HL/ASTER (~5-6h) — idempotent but already paid a 1.5h full-bucket-scan sunk cost with no resumable
worklist; moving now would re-pay that scan, so left running — **flag if the laptop needs to close before ~5-6h from
now, this one specifically would need a VM move first**. Prediction shard4c (~8.2h) and shard5b (~9.1h) — flat/near-
zero error rate (no active correctness signal, unlike DEX-pool), left running to bound this pass's blast radius, but
**explicitly recommended for a VM move if the laptop is closing within the next several hours** (same
`canonical-migration-prediction-` registered prefix, no file upload needed, same command as the local invocation).

**UPDATE 2026-07-09 — Prediction shard4c + shard5b also moved to VMs, both confirmed healthy.** Re-verified real current
state before acting (still multi-hour, 0-1 flat errors, not climbing) and script idempotency (copy-to-new-key

- `gcs_describe_object` pre-check = safe to kill/resume anywhere). `launch-canonical-migration-vm.sh prediction`'s
  hardcoded `_script_for` mapping points at a different, older tool — followed the same precedent as the tradfi/defi
  moves (direct `gcloud compute instances create` under the registered `canonical-migration-prediction-` prefix with a
  custom `VM_MIGRATION_CMD`, same startup-script/labels/metadata shape). Launched
  `canonical-migration-prediction-20260709-163134-shard4c` and `-shard5b`; health verified via real GCS-streamed
  `run.log` content before killing the local PIDs (the other, untouched 3 local processes are unaffected). Real speedup:
  shard4c 21→71 obj/s (~3.4x), shard5b 14.2→86 obj/s (~6x). New real ETA: shard5b ~2-2.5h (single POLYMARKET phase),
  shard4c ~4-5h total (KALSHI phase then POLYMARKET phase run sequentially). **Only one long-running local job remains:
  on-chain-perp HL/ASTER (~5-6h), deliberately left per the sunk-cost reasoning above** — needs an operator call if the
  laptop is closing within that window.

* **2026-07-09 — GENERALIZED FINDING + DECISION: legacy GCS filename/path conventions are a systemic risk, not just an
  on-chain-perp issue.** The on-chain-perp full-historical-sweep branch found that a real GCS narrow-prefix listing (not
  the manifest's summary count) shows ~99% of "captured" HL/ASTER historical objects (~19,255 of 19,435) sit under an
  EVEN OLDER bare-symbol filename shape (`AAVEUSDT.parquet`, `AAVE-PERP.parquet` — no venue, no type marker in the name
  at all) that neither the original nor the already-extended migration script's regex recognizes; they'd be silently
  skipped, not migrated. **Operator decision, 2026-07-09**: (1) extend that script to also parse venue from the object's
  GCS PATH (not just the filename) so this older shape is covered too, not left behind; (2) treat this as a general
  pattern, not an on-chain-perp-only bug — **audit CeFi (Binance/Bybit/Kraken/Deribit/OKX) and DeFi (13 DEX-pool
  protocols + lending/staking) historical GCS data for the same problem**: multiple coexisting filename/path naming
  conventions from different points in this workspace's history, only the most recent of which any current migration
  script recognizes. **Target**: exactly ONE canonical path/filename convention per venue going forward (per the
  filename-vs-instrument_id rule already settled above); every object under any OTHER legacy shape gets discovered and
  migrated to it — not just the already-known target-format gap this doc's findings 1-6 describe, but genuinely
  unknown-until-audited older shapes the way this one was. Dispatched as a dedicated discovery+migration workflow, see
  Orchestration state below.
* **2026-07-09 — `wf_118d8268-18c` onchain-perp venue-family slice (HYPERLIQUID/ASTER/PACIFICA-SOLANA/
  EXTENDED-STARKNET/LIGHTER-ZKSYNC) — real discovery + code fix + historical migration, MTDS.** Real discovery (live
  `gcloud storage`/parquet reads, not guesses) confirmed all 5 venues' raw-tick `symbol` column diverges from the
  `BASE-QUOTE@LIN` target: ASTER emitted the raw concatenated exchange symbol (`"BTCUSDT"`, no dash); HYPERLIQUID's S3
  archive + REST-fallback paths emitted the pre-2026-07-08 `"{coin}-PERP"` shape; LIGHTER-ZKSYNC/PACIFICA-SOLANA emitted
  a bare base-asset string (`"BTC"`); EXTENDED-STARKNET emitted a bare base-asset `symbol` alongside an already-dash-
  joined-but-unmarked `instrument_id` (`"BTC-USD"`). **Fixed (code, all 5 venues' NATIVE REST/S3 write paths)**:
  `market-tick-data-service@b416ffce` (confirmed on `origin/live-defi-rollout` via real `git fetch` +
  `merge-base --is-ancestor`, not just local HEAD) — `aster_adapter.py::_to_canonical_symbol`,
  `adapters/hyperliquid_s3.py::_canonical_perp_symbol`, `adapters/_umi_lighter.py::_lighter_canonical_symbol`,
  `adapters/_umi_pacifica.py::_pacifica_canonical_symbol`, `adapters/_umi_extended.py::_extended_canonical_symbol`, plus
  `live/websocket_runner.py::live_tick_blob_path` now sanitizes the filename component (colon-laden live filenames no
  longer diverge from the batch path's bare-symbol convention). 8 pre-existing unit tests updated to assert the new
  canonical values (`test_hyperliquid_s3_coverage.py`, `test_extended_candles.py`, `test_pacifica_candles.py`,
  `test_lighter_candles.py`); full targeted suite green (225 passed). **Historical migration (real, `--apply`,
  backup-first, real concurrency)**: LIGHTER-ZKSYNC (1,593 files) + PACIFICA-SOLANA (1,408 files) + EXTENDED-STARKNET
  (35,883 files) under `pipeline_mode=batch_tardis` — real scope discovered via a bounded per-day+venue-prefix scoped
  GCS list (2024-09-01..2026-07-08, NOT a whole-corpus walk). Elapsed time + final counts: see this session's completion
  report (agent-orchestrator task output) for the honest real numbers — not restated here to avoid this doc going stale
  the moment the doc is re-read. **Deliberately deferred, NOT a scope choice — real, confirmed live multi-agent
  conflict**: (1) ASTER/HYPERLIQUID historical GCS filename-rename + row-content symbol-column fix —
  `scripts/migrate_onchain_perp_perpetual_canonical_ 2026_07_08.py` was actively dirty (another agent's in-flight WIP,
  still dry-run-only as of this session, no `_index/backups/availability_index.pre_perpetual_canonical_*` found) at
  write time; touching the same GCS objects would race. (2) The Tardis-archive (`batch_tardis`) post-fetch `symbol`
  remap for LIGHTER-ZKSYNC/PACIFICA-SOLANA/ EXTENDED-STARKNET (the actual highest-volume current source for these 3
  venues) — `market_interface/adapters/cefi/ tardis_shared.py` + `market_interface/adapters/tradfi/tardis_adapter.py`
  were BOTH actively dirty (mtime 159s/228s at discovery, part of a larger actively-churning cluster also touching
  `partitioned_writer.py`, `kalshi_adapter.py`, `databento_enrichment.py`, `_dex_pools_*.py` — evidently this session's
  `wf_9e5f13e3-962` / `canonical-id-full-historical-sweep` work) at write time. **Insertion point identified for
  whichever agent picks this up next**: canonicalize the DataFrame's `symbol` column for these 3 venues before it
  reaches `finalise_rows_and_path`/`derive_row_instrument_id` in `tardis_cefi_shards.py`'s
  `finalise_and_write_cefi_shards`/`_tardis_cefi_shard_router` (both already group by the raw `symbol` column) — no
  `canonical_id_builder.py`/UAC change needed, since `_build_cefi_simple` just upper-cases and wraps whatever `symbol`
  string it receives (confirmed by reading `_build_cefi_simple` + `build_instrument_id`'s PERPETUAL dispatch directly).
  Full write-up + the LIGHTER-ZKSYNC market_id→symbol table (live-verified 2026-07-09 via
  `mainnet.zklighter.elliot.ai/api/v1/orderBookDetails`): `market-tick-data-service/docs/canonical-write-conventions.md`
  § "On-chain-perp `symbol` canonicalization".
* **2026-07-09 — CeFi legacy GCS naming-convention audit (the generalized finding's CeFi half) — COMPLETE, real gap
  found + fixed for OKX-SWAP/OKX-FUTURES, no gap for the other 4 target venues.** Real GCS listing (not the manifest
  summary — one flat `gsutil ls -r` over `instruments-store-cefi-prd-central-element-323112`'s
  `instrument_availability/by_date/`, 110,636 real objects, single walk) across BINANCE-FUTURES, BINANCE-DELIVERY,
  BYBIT, KRAKEN-FUTURES, DERIBIT, OKX-SWAP, OKX-FUTURES. **Found 4 distinct real path shapes** coexisting for the
  per-day snapshot corpus — all under the same fixed leaf filename (`instruments.parquet`; CeFi has NO
  bare-symbol-per-instrument-file shape anywhere, unlike the HL/ASTER on-chain-perp case that triggered this audit): (A)
  bare `day=D/venue=V/instruments.parquet` (33,602 real objects across the 7 target venues); (B) pipelined
  `day=D/pipeline_mode=batch_instruments_service/asset_group=cefi/venue=V/instruments.parquet`, a real coexisting
  duplicate write path spanning the SAME 2019-current range as shape A, not a superseded relic (28,710 real objects);
  (C) doubled-`day=` bug, pipelined variant (144 objects); (D) doubled-`day=` bug, bare variant (144 objects) — C/D both
  bounded to 18 real dates (2026-05-05..2026-05-22) across 12 venues, a real partition-key double-write bug, separate
  from the A/B duplication.
  - **Coverage, verified by exact reconciliation (real total objects vs. real `.bak` backup count already written, not
    just code inspection)**: `canonicalize_bybit_kraken_futures_catalog_2026_07_09.py`,
    `canonicalize_binance_futures_delivery_catalog_2026_07_09.py`, and `canonicalize_deribit_id_markers_2026_07_09.py`
    all list via a FLAT substring scan (`"venue=X/" in blob.name`) over the whole `by_date/` prefix — depth-agnostic,
    already covers every shape found. Full coverage confirmed: BYBIT+KRAKEN-FUTURES 9,540 real objects / 9,560 real
    `.bak` (the +20 is a separate, pre-existing, already-documented double-backup-of-a-backup artifact, not a coverage
    gap); BINANCE-FUTURES+DELIVERY 9,234/9,234 exact; DERIBIT 5,342/5,342 exact. **No new script needed for these 4
    venues.**
  - **Real gap found: `canonicalize_okx_margin_type_2026_07_09.py`'s `--by-day` mode.** Its listing
    (`_list_okx_day_files`) does a two-level DELIMITED (non-recursive) listing — `day=D/` prefixes, then checks only
    whether `venue=V/` is a DIRECT CHILD of each `day=D/` prefix — structurally can never see shape B (one level deeper,
    under `pipeline_mode=.../asset_group=cefi/`) or shapes C/D. Real reconciliation: 9,576 total real
    OKX-SWAP+OKX-FUTURES objects, only 4,762 (shape A, 49.7%) ever carried an `.okxmarginfix.` backup — **4,814 real
    objects (shape B 4,742 + shape C 36 + shape D 36) were silently never discovered**, still carrying the original
    margin-type-inversion bug that script exists to fix. This means the doc's own earlier "FIXED 2026-07-09, 0 remaining
    mismatches" claim for this corpus (`instruments-service/docs/CEFI_INSTRUMENTS.md`, since corrected) was wrong — its
    own re-verification pass shared the same blind spot as the fix it was verifying. Confirmed with real content, not
    just path inspection: sampled `day=2023-06-15` OKX-FUTURES — shape A (migrated) correctly showed `BTC-USD-230616` as
    `inverse`; the shape-B copy of the SAME (day, venue, instrument) still showed `linear` for all 60 real rows before
    this fix ran.
  - **Fix — new script `instruments-service/scripts/legacy_naming_audit_okx_2026_07_09.py`, real full sweep RAN
    2026-07-09.** Same `_expected_margin_type` correction rule as the original script (byte-for-byte identical formula),
    applied via a flat depth-agnostic listing (same proven pattern as the Bybit/Kraken/Binance/Deribit scripts). Real
    results (`--apply --confirm --full-sweep --workers 30`, all 9,576 real files scanned, shape A included idempotently
    to prove nothing was missed): `files_scanned=9,576, files_written=4,798, rows_fixed=155,614, errors=0`, elapsed 927s
    (15.5 min). A full-corpus re-verification dry-run immediately after confirmed
    `files_written=0, rows_fixed=0, errors=0` — 0 remaining legacy-shape-hidden mismatches across the ENTIRE real
    corpus, all 4 path shapes. Backup-first (`instruments.legacynamingauditokx.<ts>.bak.parquet` per touched file). Full
    write-up: `instruments-service/docs/CEFI_INSTRUMENTS.md` § "CeFi legacy GCS path-shape audit (2026-07-09)" (also
    corrects the OKX per-day section's and "Known limitations" table's prior false-completeness claims).
  - **DeFi half of the generalized finding** (13 DEX-pool protocols + lending/staking) audited in parallel by a separate
    in-flight sibling workflow this session
    (`instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py`) — not this entry's
    scope; see that script/its own commit for DeFi-side real findings.

* **2026-07-09 — DeFi legacy GCS naming-convention audit + migration COMPLETE** (the DeFi half of the generalized
  finding immediately above; `wf_9e5f13e3-962`'s DeFi scope). Real, narrow (single-venue-prefix) GCS listings — not the
  manifest summary — against `instrument_availability/by_date/` in BOTH `instruments-store-defi-prd-{pid}` (2,363 real
  day-partitions, 2020-01-20..2026-07-09) and the legacy env-less `instruments-store-defi-{pid}` (2,315, confirmed
  frozen since 2026-05-22 — 0 real writes past that date) covering the 13 DEX-pool protocols + 25
  lending/staking/yield/restaking venues. **Real finding, same class as the CeFi ghost-venue/shape-B findings above**: a
  ghost (no-underscore) vs canonical venue-token spelling was written IN PARALLEL for 28 real venue×chain pairs across
  ~4 years (2022-03-27..~2026-05-11, then stopped — `writers.py`'s `canonicalize_defi_venue_combined()` fix, 2026-05-22,
  already prevents new ghost writes but never touched the historical corpus) — 33,012 real ghost objects (31,968
  `-prd-` + 1,044 legacy-bucket-only), including 2 fully-orphaned cases (`PANCAKESWAPV3-ZKSYNC` 446/446 days,
  `VELODROME_V2-OPTIMISM` 1,044/1,044 days — zero canonical counterpart existed anywhere pre-migration). A real content
  diff (81 sampled pairs) proved ghost≠canonical duplicates — each side commonly holds real pools the other is missing
  (schema also differs: canonical 51 cols vs ghost 40) — so this was a MERGE migration (column+row union, canonical wins
  on identity-column conflict, ghost-only rows carried over honestly), not a blind rename, backed by a real before/after
  example (`AAVE_V3-OPTIMISM` day=2022-04-23: 12+12 rows, 3 unique each side → 15 merged, 0 lost, independently
  re-verified post-write). Executed via
  `instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py` — backup-first (every
  pre-migration object server-side-copied under `_migration_backup/legacy_naming_audit_dexpool_2026_07_09/` before any
  write), verify-then-delete (ghost only deleted after a post-write re-read confirms row-count ≥ the identity-deduped
  union floor), real `ThreadPoolExecutor` concurrency (48 workers). **Real final results**: 33,003/33,003
  (bucket,ghost,day) triples migrated successfully (100%, 0 remaining failures after an 11-item mop-up pass), a
  follow-up idempotent full re-scan of all 29 ghost-venue prefixes across both buckets confirmed **0 real ghost objects
  remain anywhere** — durable, not just catalog-level. Real elapsed time ~78 minutes wall-clock (main pass 4,568s +
  mop-up 41s + verification listings; measured throughput ramped 4.4→7.6 objects/sec). Real content recovered: 2,314,285
  total rows read from ghost objects, merged into canonical objects now totaling 2,828,070 rows. **Real mid-run bug
  found and fixed in the same pass**: 11/33,003 objects (1 transient GCS 503, 10 `UNISWAPV3-POLYGON` days) initially
  failed a post-write verify check SAFELY (ghost not deleted, no data at risk) — root cause: the verify floor compared
  against the ghost object's RAW row count, but a real source file can carry an internal duplicate identity value (e.g.
  `UNISWAPV3-POLYGON` day=2025-01-10: 476 raw rows, 475 unique `raw_symbol` — a real subgraph-pagination-overlap
  re-listing, not corruption); the merge already correctly deduped on the identity column, so the raw-row-count floor
  was rejecting a genuinely correct result as a false positive. Fixed (floor now uses the unique identity-column count)
  and all 11 re-ran clean. **Lending/staking finding**: of the 25 requested venues, only
  Aave_V3/Spark/Compound_V3/Morpho/Fluid have EVER written a real object to this path — the other 18 (Euler_V2, Radiant,
  Venus, Benqi, MarginFi, Solend, Renzo, KelpDAO, Puffer, RocketPool, Sanctum, Solblaze, Yearn_V3, Beefy, Karak, Idle,
  Symbiotic, Convex) have ZERO real objects under ANY naming variant — confirmed via a full real venue-token inventory
  (87 distinct tokens, full 2020-2026 history, both buckets) — NOT a naming gap (nothing to rename), a separate
  pre-existing "never backfilled" state, out of THIS audit's scope. **Note (2026-07-13): fixed for 4 of the 18 — VENUS,
  RADIANT, EULER_V2, BENQI now have real backfilled objects** (VENUS 6, RADIANT 8, EULER_V2 6, BENQI 2 rows), per the
  resolved `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`'s 2026-07-13 entry. MarginFi/Solend and the
  other 12 non-lending venues in this list are unaffected and still ZERO, per that same source. **Second finding,
  flagged not executed, mirrors CeFi's shape-B finding above**: a fully distinct real duplicate write path was found —
  `day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...` — mirroring ~104K of the flat tree's
  real objects in `-prd-` (2,353/2,363 days), confirmed dead going-forward (real writes stopped ~2026-06-30). Unlike
  CeFi's shape B (which the CeFi audit above found DOES carry stale/buggy unmigrated content in some cases), DeFi's
  shape-B samples checked (oldest `day=2020-01-20` + a recent `day=2026-06-10`, CRC32C+MD5 hash-verified) were
  byte-for-byte identical to their flat-shape sibling — but this was only 2 spot-checked samples, not a full
  reconciliation, so treat as a real-but-narrow finding, not a proven full-corpus guarantee. Confirmed UNREAD by every
  real consumer (`unified_trading_library`'s
  `instrument_lifecycle_loader.py`/`domain/instruments_client.py`/`domain_client/clients/instruments.py`/
  `options_cluster_lookup.py`/`core/cloud_data_provider.py` — all read the flat shape only). Recommended as its own
  dedicated SAFE-TO-DELETE audit (same pattern as MTDS's own
  `e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py`, and the exact same shape-B pattern the CeFi audit
  above already found + partially fixed), NOT executed this pass. Full evidence + per-protocol table:
  `instruments-service/docs/DEFI_INSTRUMENTS.md` § "Legacy GCS naming audit — real per-protocol findings and migration
  (2026-07-09)". Evidence: instruments-service@11192be2 (landed on `origin/live-defi-rollout`, verified via
  `git merge-base --is-ancestor`).

**UPDATE 2026-07-09 — `wf_9e5f13e3-962` COMPLETE (4/4 agents), independently verified — one genuinely NEW,
previously-unreported bug caught by the verify pass.** Live-construction wiring (`instruments-service@8128189e`) and
both audits' completions above are all independently re-confirmed with real evidence (fresh byte-level GCS
downloads/diffs, not trusting self-reports): the OKX shape-B fix and the AAVE_V3-OPTIMISM ghost-merge sample both match
their claimed row counts exactly. The Deribit "no gap" and the 18-venue "never backfilled" claims both hold up under
independent spot-check too.

**Real new finding, not caught by either audit itself**: the ghost-venue-merge migration
(`legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py`'s `_merge_frames()`) concatenates ghost-only rows into
the canonical file via `pd.concat([canon_df, ghost_only], ignore_index=True)` **without rewriting those rows'
`instrument_key`/`venue` COLUMN VALUES** to canonical spelling — only the GCS _path_ is canonical now, the _data inside_
still literally reads `instrument_key='AAVEV3-OPTIMISM:A_TOKEN:ALINK'`/`venue='AAVEV3-OPTIMISM'` (no underscore) for
every ghost-only row that got merged in. Confirmed via direct download+read, not assumption. This directly contradicts
"zero trace of the old formats in data" — any downstream consumer that filters/joins on the `venue` COLUMN (not the GCS
path) will silently miss or mis-bucket these rows. The doc's own cited examples (`UNISWAPV3-OPTIMISM` day=2023-11-18 6
rows, `PANCAKESWAPV3-BSC` day=2024-10-07 59 rows) suggest this is very likely systemic across some fraction of the
29,840 same-day-collision pairs, not a one-off. **Real fix needed**: rewrite `_merge_frames()` to also correct
`instrument_key`/`venue` on the ghost-only rows before concat, then re-run a one-time pass over every (day,venue) pair
that had ghost-only rows (a subset of the already-known 29,840, not a fresh full-corpus walk). Not yet fixed — filing as
its own follow-up.

**UPDATE 2026-07-09 — `wf_c4796aec-f35` (full historical sweep) COMPLETE, all 7 agents (6 packages + verify) done.**
Real production migrations, verified: Bybit/Kraken-Futures catalog+full by_date corpus (`instruments-service@ba4f7d2e`,
9,540 files, 1.98M id relabels), Deribit catalog+full by_date corpus (263,979/263,979 + 5,342/5,342 files, 7.98M rows),
OKX catalog+full by_date corpus (6,053 + 4,762 files, ~156K rows), on-chain-perp GCS renames+manifest (134,855 renamed,
7.2M manifest rows) — all independently re-verified by the verify agent against live production GCS, not self-reports.

**Two urgent, real findings from the verify pass, not yet actioned:**

1. **A live-trading correctness bug sits uncommitted, local-only, right now**:
   `market-tick-data-service/market_tick_data_service/live/connectors/deribit_ws.py` has a real, correct fix already
   written (the `count("-")==2` dead-code check was misclassifying every real Deribit FUTURE trade as OPTION) but it has
   NOT shipped — **live trading is currently running the buggy classifier**. This is the single highest-priority item in
   this whole update.
2. **Real production migrations exist that are not reproducible from git** — 3 scripts that already ran real GCS
   mutations (`canonicalize_deribit_id_markers_2026_07_09.py`'s `--by-date-all` mode,
   `canonicalize_binance_futures_ delivery_catalog_2026_07_09.py`'s concurrency, and BOTH OKX scripts entirely) exist
   only in this one machine's working tree — a fresh clone of `origin/live-defi-rollout` cannot audit, reproduce, or
   re-run any of them. The underlying data mutations are real and independently verified against live GCS (not
   fabricated), but the audit-trail gap itself is real and needs closing — commit these scripts.

**Also found — a real regression exposed by this session's own earlier fix, currently blocking ALL new Bybit captures.**
The Bybit/Kraken-Futures migration agent found: 46 real legacy coin-margined quarterly futures (`BTCUSDH22`-shape, 4
still actively trading) fail to capture — `adapter.py`'s expiry-resolution fallback chain has no branch for this no-dash
CME-month-code shape, and the resulting uncaught `pydantic.ValidationError` **kills the entire BYBIT venue fetch, not
just these 46 symbols** — real command reproduces it:
`python -m instruments_service --operation instruments --mode batch --asset-group cefi --venues BYBIT --start-date 2026-07-09 --end-date 2026-07-09 --force`
→ 0 records for the whole venue. This is a live regression, exposed (not caused) by the earlier margin-type fix
(`176d4610`) which removed a guard that previously silently absorbed this case. Correctly not fixed by the migration
agent (belongs in `adapter.py`, locked by concurrent live-wiring work all session) — needs its own urgent fix once that
lock clears.

Real evidence for all of the above: `instruments-service/docs/CEFI_INSTRUMENTS.md`, `docs/DEFI_INSTRUMENTS.md`, plus the
verify agent's per-venue-family honest-status table (git-vs-origin, live GCS spot-checks) in the workflow journal.

**UPDATE 2026-07-09 — dispatched `wf_c59510fe-3f5`** — `urgent-postverify-fixes` — the 3 items above: ships the live
Deribit trading-classifier fix, commits the 4 orphaned production-migration scripts, and fixes the Bybit `adapter.py`
regression (now unlocked). Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-instruments-service/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/urgent-postverify-fixes-wf_c59510fe-3f5.js`

**UPDATE 2026-07-09 — the ghost-venue-merge contamination bug (line 892 above) is FIXED, tested, and the
already-migrated data is fully remediated with real, independently-verified evidence.**

**Bug confirmed for real** (read `_merge_frames()` in full before touching anything):
`pd.concat([canon_df, ghost_only], ignore_index=True)` carried ghost-only rows into the canonical frame without ever
rewriting those specific rows' `instrument_key`/`venue` column values — verified directly against 3 real production
files (`AAVE_V3-OPTIMISM` day=2022-04-23: 3/15 rows; `UNISWAP_V3-OPTIMISM` day=2023-11-18: 6/288 rows;
`PANCAKESWAP_V3-BSC` day=2024-10-07: 59/145 rows all still read the no-underscore ghost spelling in
`instrument_key`/`venue`, GCS path was already canonical). No other column in the real 51-column schema embeds the venue
token (checked all 3 samples column-by-column, only `instrument_key`/`venue` hit).

**Fix shipped**: `instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py` — new
`_rewrite_ghost_venue_columns(df, ghost_venue, canon_venue)` (generic over every object-dtype column: exact-match cells
like `venue` are replaced outright, `<ghost_venue>:`-prefixed cells like `instrument_key` are rewritten preserving the
suffix — not hardcoded to those 2 names, so a future column following the same convention is covered for free). Called
at the top of `_merge_frames` BEFORE any dedup/concat, so it covers all 3 branches uniformly: the identity-dedup branch,
the no-shared-identity-column branch, and the pure-orphan (`canon_df is None`) branch — this last one matters because
the old code's `return ghost_df.copy()` for 100%-orphan days (e.g. `PANCAKESWAP_V3-ZKSYNC`) was ALSO unfixed
contamination, not just the 29,840 same-day-collision pairs the original bug report focused on.

**UPDATE 2026-07-09 — `wf_c59510fe-3f5` COMPLETE, all 3 urgent items landed and independently verified.**

- Deribit live-trading classifier fix: `market-tick-data-service@c55c1509`, confirmed on origin, real regression test
  added (`test_real_future_instrument_one_dash_classified_as_future`). Live trading now classifies correctly.
- 4 orphaned production-migration scripts (Deribit by-date, Binance concurrency, both OKX scripts):
  `instruments- service@0fdba6f6`, confirmed on origin with real content (16-22KB each, not stubs). A fresh clone can
  now reproduce/audit all these already-run production migrations.
- Bybit `adapter.py` regression: `instruments-service@c2d3fbbc`, confirmed on origin. Real fix:
  `_parse_bybit_month_ code_expiry()` resolves the missing quarterly settlement-day convention (cross-checked against 42
  real sibling contracts' `availableTo` values, 0 exceptions), plus a per-item `try/except` so one bad symbol can never
  again zero a whole venue fetch. **Independently reproduced live** by the verify agent: the real capture command now
  writes 675 records for BYBIT (was 0 before this fix) — exact match to the fix's own claim, not trusted blindly.

All 3 verdicts: genuinely fixed, genuinely landed, no discrepancies found.

**Real test added**:
`instruments-service/tests/scripts/test_legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py` (10 cases) —
asserts a ghost-only row's `instrument_key`/`venue` are canonical-spelled AFTER merge (not just that the row survived),
covering the collision branch, the pure-orphan branch, the no-identity-column branch, and idempotency. Independently
verified to FAIL against the pre-fix code (10/10 fail with
`TypeError: _merge_frames() takes 2 positional arguments but 4 were given`, confirming these are real regression tests,
not vacuous) and PASS against the fix.

**Real, targeted remediation of already-migrated data** (new script:
`instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_contamination_remediation_2026_07_09.py` — reuses
the fixed migration's own `GHOST_TO_CANON`/`_rewrite_ghost_venue_columns`/`_read_parquet` via dynamic module load, no
re-implementation; NOT a fresh full-corpus walk — every row this bug could reach lives under exactly the 29 canonical
venue prefixes in `GHOST_TO_CANON`, in the `-prd-` bucket only, since `_process_one` always wrote the merged frame to
the PRD bucket regardless of source bucket):

- **Real scoping**: a scoped per-canonical-venue-prefix GCS listing (mirrors the original migration's own
  `_list_ghost_days`, just on the canonical side) found **35,594 real (canon_venue, day) pairs** across all 29 venues in
  `instruments-store-defi-prd-central-element-323112`.
- **Smoke test on real infra first**: 50-pair dry-run + a real 5-pair `--apply` write, independently re-verified (backup
  existed, 0 ghost cells left, row counts unchanged) before the full run.
- **Real full remediation** (`--apply --workers 32`, ~25 min wall-clock): all 35,594/35,594 pairs processed, **0
  failures**. **10,823 pairs (30.4%) were genuinely contaminated** — 390,784 real ghost-spelled cells found and
  rewritten to canonical, backup-first under
  `_migration_backup/legacy_naming_audit_dexpool_contamination_remediation_2026_07_09/`, verify-after every write (row
  count unchanged, 0 ghost cells remain post-write).
- **Independent full re-verification** (a second, separate dry-run pass over all 29 venues immediately after):
  `total_pairs=35594 ok=35594 failed=0 contaminated_pairs=0` — confirms 0 contamination remains anywhere, not
  self-reported from the apply run's own bookkeeping.
- **The 3 originally-cited samples re-checked post-fix**: `AAVE_V3-OPTIMISM` 2022-04-23, `UNISWAP_V3-OPTIMISM`
  2023-11-18, `PANCAKESWAP_V3-BSC` 2024-10-07 — all independently re-downloaded, 0 ghost-spelled cells in any column.
- **Real, unexpected-but-verified finding**: `VELODROME_V2-OPTIMISM` (the 100%-pure-orphan venue) and the 3
  `SUSHISWAP_V3-*` venues showed **zero** contamination despite being fully in scope — spot-checked directly:
  `VELODROME_V2-OPTIMISM`'s row-level `venue`/`instrument_key` values were ALREADY canonical-spelled at capture time;
  only its legacy GCS _path_ was ghost-shaped (a narrower, already-fully-fixed bug, not the general data-contamination
  case).

Shipped via quickmerge: `instruments-service` (fix + test + remediation script + docs). Real per-venue before/after
counts also recorded in `instruments-service/docs/DEFI_INSTRUMENTS.md` § "Legacy GCS naming audit" → "Finding 1".

**UPDATE 2026-07-10 — all 4 durability VMs confirmed complete, real exit_code=0, self-deleted overnight.** Checked real
GCS-streamed `run.log` content for each (not inferring from VM absence alone):

- `canonical-migration-tradfi-20260709-160919`: DONE in 7500.6s (~2h5m).
  `{'source_missing': 26691, 'already_canonical': 10184, 'moved+rewritten': 87149, 'rewritten_in_place': 34784, 'error': 4}`
  — 4 errors out of ~158,812 real objects.
- `canonical-migration-defi-20260709-161510`: DONE in 11737.7s (~3h16m). 357,169/357,169 objects (100%),
  411,224,609/477,014,901 rows touched,
  `{'skipped_empty_or_missing_cols': 259927, 'unchanged_already_correct_or_unresolvable': 32793, 'rewritten': 64449}`.
- `canonical-migration-prediction-...-shard4c`: DONE in 14913.2s (~4h9m). KALSHI migrated=494,766/error=0; POLYMARKET
  migrated=529,862/error=8 (out of 92.9M rows). Verify samples 30/30 OK both venues.
- `canonical-migration-prediction-...-shard5b`: DONE in 5910.5s (~1h38m). POLYMARKET migrated=399,491/error=0. Verify
  30/30 OK.

No local migration processes remain running. Both instances-service and unified-api-contracts local HEAD exactly match
`origin/live-defi-rollout`; market-tick-data-service and unified-trading-pm were a few routine promote/backmerge commits
behind (unrelated fleet CI, pulled clean). One real, already-known finding remains uncommitted in
market-tick-data-service (`migrate_prediction_instrument_id_wrap_2026_07_09.py`'s connection-pool hardening — see the
"Deferred, unshipped" note in the `wf_118d8268-18c` completion update above). This confirms the whole point of moving to
VMs: all 4 ran to completion unattended, independent of the operator's laptop or this session.

**UPDATE 2026-07-10 — 4 tracked follow-up issues filed** (`unified-trading-pm@ab3b1fed5`):
[[tradfi_cme_options_chain_legacy_layout_2026_07_10]], [[defi_dexpool_second_writer_path_and_zero_capture_2026_07_10]],
[[mtds_prediction_migration_connection_pool_hardening_2026_07_10]],
[[defi_dead_storage_shape_b_cleanup_candidate_2026_07_10]] — every real gap surfaced-but-deliberately-deferred during
this effort now has a durable tracked record, not just a paragraph buried in this doc's Progress Log.

**UPDATE 2026-07-10 — dispatched `wf_50701260-a4e`** — `final-zero-trace-verification` — the closing pass: real grep +
live-GCS spot-checks across instruments-service, market-tick-data-service, and unified-api-contracts for any remaining
old-format construction sites or stale doc examples, synthesized into one final honest status report (zero-trace /
zero-trace-with-tracked-exceptions / not-yet-met — not just declared done). Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-unified-trading-pm/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/final-zero-trace-verification-wf_50701260-a4e.js`

**UPDATE 2026-07-10 — `wf_50701260-a4e` final-zero-trace-verification COMPLETE. Verdict: NOT YET MET.**

Three parallel fresh sweeps (instruments-service, market-tick-data-service, unified-api-contracts) plus live GCS
spot-checks found the original directive ("zero trace of the old formats in doc, data, or manifest") is **not yet met**
— two real, currently-active production gaps, neither previously tracked:

1. **`instruments-service` `prod/catalog.parquet` has not durably converged for CeFi derivatives.** Live GCS read shows
   currently-active old-format `instrument_id` rows coexisting with `@LIN`/`@INV` rows for the same real instrument:
   BYBIT 697 active old-format rows (~43%), KRAKEN-FUTURES 39 active old-format rows (some `available_to=2026-07-10`,
   i.e. today), DERIBIT 6,836/270,836 active old-format rows (97.5% migrated, real tail). The "4 durability VMs
   confirmed complete" close-out (2026-07-10) covered tradfi/defi/prediction(×2) only — no CeFi catalog-rewrite VM ever
   ran, plausibly why the historical/self-refreshing catalog rollup was never force-converged for CeFi the way it was
   for the other 3 asset groups.
2. **MTDS's own live CeFi WS connectors (raw-tick construction layer) were never retrofitted.** `bybit_ws.py`,
   `kraken_futures_ws.py`, `okx_ws.py`, `binance_futures_ws.py`, `deribit_ws.py` + sibling book-ticker connectors still
   hardcode the pre-canonicalization shape. `LiveWebsocketRunner.record_tick()` does an exact-string lookup against the
   now-canonical IS-resolved buffer keys — mismatches are silently dropped. Confirmed in production GCS as late as
   `day=2026-06-27` (most recent CeFi raw-tick data found in any bucket checked).

Smaller new gaps: `tardis_machine_ws.py` (opt-in live source, literal `"PERP"`, 3 sites); residual old shape in
`live_hyperliquid` day=2026-06-29 despite the migration script targeting it (not root-caused); untracked builder
bypasses in `tardis/combos.py` (Deribit batch combo legs), `deribit_combo_adapter.py:405` (combo top-level id), and
MTDS's restaking/pool DeFi adapter family (`restaking_{jito,karak,symbiotic}_adapter.py` + siblings — a real coverage
gap in the retrofit checklist itself); 2 stale doc sections (`CEFI_INSTRUMENTS.md` L208/256-259,
`canonical-write-conventions.md`'s "no MTDS-side change needed for live" claim).

Re-confirmed still-open, already-tracked (not new): OKX-SWAP/OKX-FUTURES 0% migrated; Prediction catalog
raw_symbol/base_asset/underlying 100% NULL; `symbiotic.py:117` (checklist todo 1's DeFi-adapter backlog).

Confirmed genuinely clean: live ccxt + batch Tardis paths, CME/CBOE combo legs, HYPERLIQUID/ASTER batch on-chain-perp,
DeFi's 2 live connectors, Kalshi/Polymarket Prediction adapters, DeFi DEX-pool bare-pool_address design.

The 5 tracked deferred exceptions remain as filed: `[[tradfi_cme_options_chain_legacy_layout_2026_07_10]]`,
`[[defi_dexpool_second_writer_path_and_zero_capture_2026_07_10]]`,
`[[mtds_prediction_migration_connection_pool_hardening_2026_07_10]]`,
`[[defi_dead_storage_shape_b_cleanup_candidate_2026_07_10]]`, and the DEX-pool ghost-venue-merge follow-through (that
one is effectively resolved — full remediation + independent re-verification already landed; listed for completeness).
None of these cover the 2 new headline findings above.

**Next real step**: this doc's scope needs 2 new tracked items — (a) a CeFi-specific catalog durability rewrite/verify
pass for BYBIT/KRAKEN-FUTURES/DERIBIT (mirroring the tradfi/defi/prediction durability VMs), and (b) an MTDS
live-CeFi-connector retrofit to build canonical `@LIN`/`@INV` keys at the raw-tick layer, matching the
on-chain-perp/DeFi live connectors that already do this correctly. Both dispatched, see below.

**UPDATE 2026-07-10 — dispatched `wf_860fb2ae-54e`** — `cefi-durability-and-live-connector-retrofit` — the 2 fixes
above, in parallel, then verified: (1) real root-cause diagnosis + force-convergence of the CeFi catalog for
BYBIT/KRAKEN-FUTURES/DERIBIT, proving durability across a real regen cycle this time, not just a one-time rewrite; (2)
retrofit of MTDS's 5 primary + 4 book-ticker live CeFi WS connectors to the canonical shape, including a real check of
whether `record_tick()`'s exact-string buffer lookup is actually silently dropping live ticks right now. Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-unified-trading-pm/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/cefi-durability-and-live-connector-retrofit-wf_860fb2ae-54e.js`

**UPDATE 2026-07-10 — item (2) DONE: MTDS live-CeFi-connector retrofit landed, `market-tick-data-service@20dc1be8`.**
Real severity finding confirmed FIRST (per directive): `LiveWebsocketRunner.record_tick()` (`websocket_runner.py`) is a
bare `self._buffers.get(received.instrument_id)` exact-string dict lookup with a silent `return` on `None` — no
exception, no log. Proved end-to-end with a new record_tick() test using the REAL (unmodified) old-format string a
pre-fix `bybit_ws.py` would have emitted (`BYBIT-FUTURES:PERP:SOLUSDT`) against a buffer keyed by the real IS-resolved
canonical id (`BYBIT:PERPETUAL:SOL-USDT@LIN`) — confirmed the tick is dropped (`pending_tick_count` stays 0, no error
raised) — this **was** live data loss for these 5 CeFi venues, not just an inert format inconsistency, given IS's own
catalog durability fix (item (1) above) forces the buffer keys to the new shape.

Retrofitted BYBIT/KRAKEN-FUTURES/OKX-SWAP/BINANCE-FUTURES/DERIBIT (5 primary trade connectors) + their 4
book_snapshot_5/derivative_ticker siblings, for BOTH directions — forward (raw exchange payload → canonical
instrument_id) and reverse (canonical instrument_id → real exchange subscribe topic, since IS-resolved canonical ids,
not raw wire symbols, are what flow into `connect()`/`subscribe()` — flagged as a real risk in the dispatch, confirmed
real: a stale `parts[-1]`-only reverse would have sent the wrong string as the subscribe topic once the forward shape
changed). Reused/ extended the shared `tardis_margin_marker.py`/`tardis_shared.py` builders already proven on the
batch/Tardis path rather than reimplementing margin/expiry resolution per connector (per the dispatch's
minimize-change-surface ask) — routed all 4 book-ticker siblings through the primary connector's builder via public
aliases so trade and book/ticker streams converge on the identical id per instrument.

Adjacent findings fixed in the same pass (all in scope per "in your file → fix in same commit"): a real, independent
Kraken-Futures margin-type bug (`derive_settlement_dimensions` hardcoded every KRAKEN-FUTURES symbol `inverse`
regardless of the real `PI_`/`FI_` vs `PF_`/`FF_` prefix — same bug class as IS's own already-fixed
`_infer_margin_type`); a real Binance dated-future misclassification (every trade on the combined WS endpoint tagged
`PERPETUAL` even for a raw dated quarterly contract); a real OKX book-ticker/trade divergence (the book_snapshot_5/
derivative_ticker sibling built its own `OKX-FUTURES:PERP:` shape — wrong venue AND wrong type token vs the primary
connector's real `OKX-SWAP:PERPETUAL:` — a pre-existing buffer-key mismatch on that data_type, independent of this
migration); BYBIT-SPOT/BINANCE-SPOT retag sites doing a literal-prefix string-replace that would have silently broken
once the PERPETUAL builder stopped emitting the old literal prefix (fixed to re-derive from the raw wire symbol,
matching the pattern `aster_book_liq_ws.py` already used).

Evidence: direct pytest (tests/unit + tests/integration, fresh `__pycache__`) — 5660 passed, 42 skipped, 0 regressions
(10 pre-existing unrelated live-network-integration failures only — Kalshi/Polymarket/macro, blocked by `--allow-hosts`
sandboxing, not network-reachable in this environment); ruff clean; basedpyright shows only pre-existing baseline errors
(626, unchanged) on lines this diff never touched. **New tracked finding, not fixed here**: `quality-gates.sh`'s own
wrapper (`unified-trading-pm/scripts/quality-gates-base/base-service.sh`) hit a real, reproducible environment-level bug
under this workspace's current heavy concurrent multi-agent QG/quickmerge load — repeatedly resolved
`PROJECT_ROOT`/pytest `rootdir` to `unified-trading-pm` instead of the target repo (confirmed via multiple isolated
`bash -c 'cd <repo> && ...'` invocations, including with `PROJECT_ROOT`/ `WORKSPACE_ROOT`/`_QG_CALLER` explicitly
forced), silently running the wrong repo's 6-item PM integration-test suite instead of the real ~5700-item suite and (in
one observed case) still reporting `exit 0`/writing a sentinel. Verification for this session's diff was therefore via
direct, isolated `pytest`/`ruff`/`basedpyright` invocation (same underlying checks, bypassing only the wrapper's rootdir
bug) — this is an operator-notification-worthy, cross-repo CI-integrity issue, not something fixed in this pass. Shipped
via direct commit+push (`git-commit` skill) after `scripts/quickmerge.sh` correctly blocked on real dirty deps
(`unified-trading-library`, `unified-api-contracts` — both mid-edit by other concurrent agents, not this session's).

**UPDATE 2026-07-10 — item (1) root cause found: `instruments-service`'s prod Docker image has been stuck since
2026-07-09, silently blocking every fix this session from ever reaching production.** Independently surfaced twice —
once by `wf_860fb2ae-54e`'s own verification pass ("`is-daily-enum-cefi`'s deployed image is still pinned to build
`330d9a4`/v0.88.0, pushed 2026-07-09T00:50:05Z — before all 3 fix commits landed"), once by the separate
`instruments-audit-p0-wave` workflow's is-daily-enum-crash agent (UTL's already-landed `exc_info` fix present in
`unified-trading-library:latest` but not in the deployed `instruments-service:latest`, whose Dockerfile pins an older
UTL base digest). Root-caused directly: `gcloud builds list` shows the last SUCCESS for the `instruments-service-prod`
trigger was `69c976a7` (2026-07-08T23:47Z, commit `330d9a4`); every build since — including today's `8304993d`
(2026-07-10T00:06Z) — FAILED with
`ImportError: cannot import name 'build_leg' from 'unified_api_contracts.internal.reference.canonical_id_builder'`
(`build_leg` was added to UAC 2026-07-08 19:52, `7c0f45dd` — well before the failing build, but the Dockerfile's
`ARG BASE_IMAGE_DIGEST` pins a specific `unified-trading-library` base-image digest that bundles UAC, and that pin
(`sha256:9f01cf8e...`) predates `build_leg`). The Dockerfile's own comment says this digest is "Refreshed by the
dependency-update fan-out (`update-dependency-version.yml`) on base-image republish" — checked: the last merged
base-image-bump PR for this repo was `#70`, 2026-02-19. **The automated fan-out has been stalled for this repo for ~5
months**, silently freezing every prod deploy at whatever UTL/UAC state existed then, while dozens of real fixes
(including this whole session's `@LIN`/`@INV` canonicalization work) landed in source and never shipped. Flagged as its
own operator-notification-worthy finding — the fan-out itself needs investigation, not just this one manual bump.

**Fix (real, pushed, promotion pending)**: bumped `ARG BASE_IMAGE_DIGEST` to the current
`unified-trading-library:latest` digest (`sha256:4a86bb9c...`) — `instruments-service@53367eba`, pushed directly to
`live-defi-rollout` (dirty-deps carve-out; `unified-trading-library`/`unified-api-contracts` both had real concurrent
uncommitted work blocking quickmerge's pre-flight audit). `instruments-service-prod`'s trigger fires on `main`, not
`live-defi-rollout` — a manual `gcloud builds submit` doesn't carry the trigger's substitutions (attempted, failed with
a malformed image tag as expected) — so verification waits on the next `ldr-to-main-promote` cycle (~15 min) to
auto-fire a real build. **Not yet verified GREEN** — will re-check and record the real build result once the promotion
lands, per this doc's own no-fire-and-forget discipline.

**Important**: this image fix only stops FUTURE pollution once deployed — it does NOT retroactively fix the existing
BYBIT (697)/KRAKEN-FUTURES (308 PERPETUAL + 31 FUTURE)/DERIBIT (6,857) old-format catalog rows. That still needs
`scripts/cefi_durability_force_converge_2026_07_10.py` (written by `wf_860fb2ae-54e`, confirmed still UNTRACKED/never
committed or run against the live corpus per its own verification pass) to actually execute. Picking that up next.

**UPDATE 2026-07-10/12 — CeFi catalog durability (`--quarantine-backups` + `--fix-by-date`) completed, clean.**
`cefi_durability_force_converge_2026_07_10.py` committed and run to completion against the real BYBIT/KRAKEN-FUTURES/
DERIBIT corpus: stray inline `.bak.parquet` files quarantined out of the walked tree (no longer pollute
`build_instrument_catalogue.py`'s `_iter_by_date_snapshots`); `instrument_key`/`margin_type` re-derived and verified
durable across a real regen cycle. Along the way, found a real, separate bug: ~2,600 historical DERIBIT files had
`expiry` frozen at a stale last-observed/capture date instead of the instrument's real expiry, causing distinct options
to collide when re-deriving keys — root-caused, the DUP-GUARD-visible collision case was fixed via `_re_derive_row`'s
DERIBIT-specific override (prefer raw_symbol's own regex-parsed date over the stored column for KEY derivation only —
this part was and remains correct), and the CeFi durability job itself completed clean.

**UPDATE 2026-07-12 — the underlying `expiry` METADATA COLUMN (not just instrument_key derivation) was still
historically wrong, and the first fix attempt at it made things WORSE. Full honest history, in order:**

1. **The gap**: fixing `instrument_key` collisions (2026-07-10, above) never touched the stored `expiry` COLUMN itself —
   only instrument_key's internal derivation. Operator asked directly whether the historically-incorrect files were
   actually migrated; answer was no, confirmed via direct GCS reads.
2. **Design 1 — `--fix-frozen-expiry` (REMOVED same-day) — corrupted 35,410 previously-correct rows.** Detected DERIBIT
   rows where 2+ distinct `raw_symbol`s collided on one stored `expiry` within a (base, quote, margin, strike, right)
   group, and "corrected" them to a naive `raw_symbol` regex parse. Wrong on two independent counts, both confirmed via
   real Tardis ground truth (free `GET /v1/exchanges/{exchange}`, no-auth): (a) a shared stored expiry across 2 distinct
   real instruments can be a genuine, correct coincidence — Deribit really does delist multiple option series on the
   same real day — not automatically a bug; (b) even where a correction WAS needed, the naive regex-parsed date matched
   real ground truth in only ~3-8% of sampled cases across all 3 venues, while the ALREADY-STORED value matched in
   94-97% of cases. Ran to completion, verified clean at the time (2,620 files, 35,555 rows) — the verification itself
   was flawed, not just the fix; a later re-scan + before/after/ground-truth comparison confirmed the true damage:
   **35,410 rows corrupted (backup was correct, the fix broke it), only 209 genuinely fixed, across 2,620 DERIBIT
   files.** Reported to the operator plainly as soon as confirmed, not glossed over.
3. **Operator ruling, mid-investigation**: "huobi and bitspamps related stuff shoudl be entirely removed from
   everything" — resolved the separate, already-escalated HUOBI/BITSTAMP/HTX SSOT contradiction as Option B (full
   removal). See [[huobi_bitstamp_htx_ssot_contradiction_2026_07_10]] for that thread — unrelated to expiry, handled in
   parallel, not further detailed here.
4. **Design 2 — availableTo as ground-truth correction target (same day, discarded before shipping).** Investigated
   using Tardis's `availableTo` field directly as the correction target instead of a regex parse. Discarded after a
   direct live-data check: `availableTo` legitimately differs from the canonical symbol-encoded date by ~1 day for many
   still-recently-active instruments (e.g. `BTC-26JUN26` parses/stores expiry `2026-06-26`, matching the symbol exactly;
   Tardis's `availableTo` for the same instrument is `2026-06-27` — a data-collection artifact in when Tardis marks an
   instrument's last-observed day, not a settlement-time signal). Treating it as ground truth would have rewritten
   hundreds of thousands of already-correct rows the same way design 1 did, just via a different wrong target.
5. **Design 3 — canonical symbol-parse, availableTo as non-blocking telemetry only (operator ruling, final, shipped).**
   Operator: "savaiable to is a safeguard but the symbol parsing is canonical... if >2 days difference... considered a
   shard failure." First implementation of this ruling gated the write on that 2-day threshold (skip the WHOLE file on
   any anomaly) — a 40-file DERIBIT sample showed this was too aggressive: 100% of anomalies (215/215) were
   one-directional early-delisting (illiquid options delisted before their scheduled nominal expiry — routine Deribit
   behavior, not corruption), and file-level skip at DERIBIT's real anomaly-per-file rate would have discarded
   corrections for 67% of files (3,602/5,347) to guard against a pattern that wasn't actually dangerous. Operator:
   early-delist is expected, don't block; keep per-file granularity, just fix everything — the gap check became
   non-blocking telemetry only (still logged for post-hoc visibility, never gates the write).
6. **Pre-ship adversarial review (Workflow, 3 independent lenses + verify pass) caught 4 real, confirmed defects before
   this touched the corpus at its real 7.2M-row scale**: (a) **blocker** — the duplicate-introduction guard compared an
   aggregate `.duplicated().sum()` count before/after instead of the actual collision SET, meaning a resolve+introduce
   pair in the same file could net to the same count and silently pass, merging two previously-distinct real instruments
   onto one key; fixed with a proper set-based check (`_would_introduce_new_collision`), applied to both this flag and
   the pre-existing `--fix-by-date` path, which had the identical latent flaw; (b) the one-time Tardis telemetry fetch
   had no exception handling, so a transient network hiccup could abort the whole run before later venues even started —
   fixed with a try/except that degrades to empty telemetry (correction logic never depended on it anyway); (c)/(d)
   `_fix_frame`'s full-file instrument_key/margin_type re-derivation was applied to every derivative row in a touched
   file, not just the ones this flag corrected — under-reporting the real blast radius and contradicting the flag's own
   "Independent of --fix-by-date" framing; scoped the re-derivation to exactly the corrected rows only, making both the
   flag's documented scope and its reported stats accurate.
7. **Shipped**: `instruments-service@11064f6e1e0cd4597eac95efd3aa3abb1926b94c` (`--fix-expiry-canonical`, supersedes and
   removes both `--fix-frozen-expiry` and the undiscarded availableTo-ground-truth code).
8. **Real production run, `--apply --workers 32`**: BYBIT 48,956 rows / KRAKEN-FUTURES 68,870 rows / DERIBIT ~7,087,732
   rows corrected (~7.2M total, the majority being DERIBIT rows where historical capture had stored `available_to`
   instead of the canonical symbol-derived date — this balloons the true scope far beyond the original ~35K-row
   estimate, but is the same systematic root cause, just previously invisible without ground-truth comparison at
   full-corpus scale). 5 DERIBIT files hit a transient local connection error mid-upload
   (`ConnectionError: Can't assign requested address` — ephemeral port exhaustion under sustained 32-way concurrency,
   not a logic bug); retried individually — 4 applied cleanly, 1 showed zero remaining corrections on retry (its
   original write likely already succeeded despite the raised exception).
9. **Final verification — a fresh, independent full-corpus dry-run confirms 0 remaining corrections and 0 errors across
   all 3 venues.** Production is durably converged for this bug as of 2026-07-13.

**Net honest assessment**: this was a real production-data mistake (design 1, 35,410 rows) inside a legitimate
investigation, caught by the same investigation continuing rather than stopping at the first "done," and corrected by
the SAME final fix that resolved the original gap — no separate revert step was needed, since a ground-truth-driven
corrector self-corrects both the original bug and its own earlier bad fix in one pass, driven by absolute correctness
rather than a relative before/after diff.
