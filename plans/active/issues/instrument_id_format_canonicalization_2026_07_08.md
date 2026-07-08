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
asset_group: [cefi, defi]
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
last_updated: 2026-07-08
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **OPERATOR DECISION 2026-07-08 — target-state only, not fixed today.** Every finding below gets a canonical target
> format. None of the target formats exist in production yet — this doc (and the mockup entries it backs) show
> current-real vs target-canonical side by side, same pattern already applied to the A_TOKEN/DEBT_TOKEN decision.
> Actually migrating is staged, future work — this doc scopes it, it doesn't execute it.

## The 6 real divergences found, and their target canonical format

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
   `pool_fee_tier_bps` but isn't the one embedded in the instrument_key string). **Not yet re-verified across the other
   12 protocols** — only Uniswap V3 was spot-checked for this update; don't assume the same code-vs-catalog gap shape
   holds for all of them without checking.

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

6. **MORPHO's market-address disambiguator uses a 3rd colon inside the symbol** —
   `MORPHO-BASE:LENDING_MARKET:USDC-EURC:0x305dd1` — colon is the reserved top-level `VENUE:TYPE:SYMBOL` delimiter, so a
   3rd colon is ambiguous to any naive `split(":")` parser. **Target**: dash-separate instead, matching the
   pool-fee-tier fix already applied elsewhere — `MORPHO-BASE:LENDING_MARKET:USDC-EURC-0x305dd1`.

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

8. **Prediction's per-market instrument_id is genuinely opaque, and its enrichment columns are 100% empty — this is
   deeper than a formatting question.** Real, confirmed via `prod/catalog.parquet` (2,486,092 rows, both venues):
   `base_asset`/`underlying`/`raw_symbol` are NULL for every single row. The bulk of individual Polymarket markets carry
   a bare on-chain hash as `instrument_id` (e.g. `0xa91339c0f2c46cbb289ae592f7c0a66f35ff278a3846253f3a11fd059674af11`);
   a smaller subset of both venues (1,243,069 of 2,486,092 rows are unique instrument_ids — real ~50% duplication) carry
   a short readable label shared verbatim across venues (e.g. `BNB_PRICE_RANGE_DAILY`, appearing exactly once per venue
   with different `available_from`/`available_to` windows — likely a recurring-series/template key, not a specific dated
   market instance, though this hasn't been confirmed against `prediction_mapping.py`'s real extraction logic). Unlike
   findings 1-7, this isn't a "wrong delimiter" problem — the fields the format would need are never populated in the
   first place, so no target format is proposed here yet. **Not the same finding as the already-settled
   `canonical_question_group` sharing behavior** (that's confirmed correct-as-designed, see "What this is NOT"); this is
   about the base `instrument_id` field itself for individual markets. Also reconfirmed real and still live: the
   bucket-naming split from the audit — `instruments-store-pred-prd-central-element-323112` exists (33,122 blobs),
   `instruments-store-prediction-prd-central-element-323112` returns a 404.

## What this is NOT

- Not a claim that any of these 6 are fixed today — every target format above is illustrative only, shown in the mockup
  as an explicit "NOT REAL — target canonical" 3rd sample alongside the real captured ones, same visual pattern as the
  A_TOKEN/DEBT_TOKEN decision's current-state-vs-target-state entries.
- Not a complete enumeration of every possible instrument_id anywhere — but coverage was extended 2026-07-08 (operator:
  "shouldl be evertyhting all AG that we expect shown in [the mockup] so we know how things will look") to every
  DEX-pool protocol×chain combination in the DeFi tab (27 total, not just a flagship sample), plus a deliberate check of
  TradFi/Sports/Prediction: TradFi's **single-leg** dated-derivative codes (e.g. `CME:FUTURE:6AF0`) are real
  industry-standard terse contract codes, not an uncleaned internal prefix like Kraken's — no divergence to canonicalize
  there (this carve-out does NOT extend to TradFi's multi-leg spreads — see finding 7, a real divergence found on a
  later pass); Sports fixture IDs are provider-native opaque identifiers, not VENUE:TYPE:SYMBOL keys; Prediction already
  routes through its own dedicated domain builder (`canonical/domain/prediction/prediction_mapping.py`) rather than the
  ad-hoc CeFi/DeFi pattern this doc is mainly about — but a dedicated builder existing doesn't mean its real output is
  canonical (see finding 8: it isn't, though that's a data-completeness gap more than a delimiter/syntax question, and
  is scoped separately from findings 1-7). DERIBIT-COMBO's underscore-in-strikes format was also checked and confirmed a
  real, internally consistent convention (not a canonicalization gap). A dedicated future audit could still find more
  instances of the 6 CeFi/DeFi divergence classes on venues/protocols this session never touched at all (this doc's
  scope is bounded by what this session's other findings happened to surface, not a from-scratch audit of the full
  instrument universe).
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
- [ ] [VERIFY] P2. **Check whether the manifest / deployment-api key off instrument_id VALUE anywhere** (as opposed to
      just the instrument_type field, already checked in
      [[adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08]]) — if any downstream consumer
      pattern-matches or parses the instrument_id string itself (e.g. extracting margin type from a `-inverse-`
      substring), changing the format is a breaking change for that consumer, not just a cosmetic cleanup.
- [x] [DECISION] P3. **Builder-architecture question — RESOLVED 2026-07-08 (operator)**: ONE shared builder for every
      asset group + instrument type + sports fixtures, filled in by structured inputs. See "What this is NOT" above for
      the exact decision language.
- [ ] [SCRIPT] P1. **Fix the Bitfinex BTC-margined-perp asset-filter bug** — found 2026-07-08 while spot-checking real
      volume, not an instrument_id-format issue but adjacent (same investigative pass): the accepted-quote filter
      (`parsing.py:463`, `cefi_instrument_universe.py:131-133`) is documented "derivatives carry no quote and pass," but
      Bitfinex's own symbol parser (`parsing.py:325-339`) DOES extract a real quote for its inverse perps (`ETHF0:BTCF0`
      → base=ETH, quote=BTC), so real Bitfinex derivatives get rejected as if they were an exotic spot cross-pair.
      Confirmed live via `api-pub.bitfinex.com/v2/tickers`: `ETHF0:BTCF0` trades ~~2,034 ETH/day (~~$6-7M/day) — not a
      negligible edge case. Fix: add BTC to the per-venue accepted-quote extension for Bitfinex derivatives, same
      mechanism already used for UPBIT's KRW extension.
- [ ] [DECISION] P1. **Confirm the revised TradFi combo fix** (finding 7, superseding the earlier flat-string proposal)
      — reuse the existing `InstrumentLeg`/`InstrumentType.COMBO` infrastructure (already proven for CME) for CBOE/VX
      spreads too, apply the existing `_resolve_product_root()` human-name registry (`ES→SP500`, `GC→GOLD`, `VX→VIX`) to
      leg symbols, and drop the redundant per-leg `VENUE:` prefix. Real 34,017/4,211/5-row counts (2/3/4-leg) at the
      2026-07-08 evidence pull — re-check row counts if this decision lands materially later, they'll have grown.
- [x] [SCRIPT] P1. **File a dedicated fix plan for finding 7** — real code gap (CBOE/VX spreads bypass existing
      leg-decomposition infrastructure entirely), not just a naming decision; independently shippable, same pattern as
      the P0 fix plans. Filed: [[canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08]]. Repo:
      instruments-service.
- [ ] [DATA] P2. **Investigate `prediction_mapping.py`'s real extraction logic** (finding 8) before proposing any target
      format — need to understand whether the short readable instrument_ids (e.g. `BNB_PRICE_RANGE_DAILY`) are a
      recurring-series/template key or something else, and why `base_asset`/`underlying`/`raw_symbol` are 100% NULL
      (never extracted, or extracted-then-dropped downstream) before deciding what a canonical Prediction instrument_id
      should even contain.

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
