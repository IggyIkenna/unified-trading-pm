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
    /plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    /plans/archive/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
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
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
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

## Orchestration state, 2026-07-09 — split to archive (2026-07-27, line-cap remediation)

This doc's original "Orchestration state, 2026-07-09" section (a dated, context-loss-recovery narrative record with zero
open todos of its own) was moved to
`/plans/archive/2026_07/instrument_id_format_canonicalization_2026_07_08_orchestration_history.md` to bring this doc
back under the 1000-line hard cap (it had grown to 1,309 lines). No content was edited, only relocated — see that doc
for the full historical record if needed.
