---
doc_type: audit-result
title:
  Canonical instrument_id compliance audit — instruments-service, MTDS, deployment-api/UI, strategy-service, GCS
  parquet, manifest
summary: >-
  2026-07-08 cross-repo audit (7 parallel research passes) of canonical instrument_id compliance, spawned from a
  mockup-backfill session that had already found ~10 real divergences. Found the scope is far larger and more severe
  than format/naming drift: 5 real P0 live-correctness bugs (a genuine data-collision on Kraken-Futures dated futures; a
  silently-defeated live position-reconciliation check for every CCXT venue; 23 DeFi adapters that silently return empty
  on type-filtered queries; a live≠batch instrument_id divergence for 13 major CeFi venues; a cross-service exact-string
  match in deployment-api that can silently produce phantom-missing coverage) plus ~40 P1/P2 format, key-vs-field, and
  venue-token-duplication findings across every asset group. `canonical_id_builder.py` — read elsewhere as "the SSOT" —
  has effectively zero enforcement: virtually every adapter/consumer sampled builds its own instrument_id ad hoc.
status: fail
nature: notes
asset_group: [cefi, defi, tradfi, sports, prediction, meta]
stage: [data, meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    deployment-api,
    deployment-ui,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [instrument-id, canonicalization, audit, live-vs-batch, data-integrity, reconciliation, honest-coverage]
related:
  [
    ../../active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    ../../active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    ../../active/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    ../../active/instruments_service_docs_consolidation_2026_07_08.md,
    ../../epics/instruments_master.md,
    ../../epics/batch_live_symmetry_master.md,
    ../../epics/client_isolation_and_governance_master.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-07-08
authoritative_for: [canonical instrument_id compliance state across the workspace, as of 2026-07-08]
referenced_by:
owner: ikenna
last_reviewed: 2026-07-08
code_refs:
  [
    unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py,
    instruments-service/instruments_service/reference_data/adapters/,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/,
    deployment-api/deployment_api/services/data_status/breakdowns_core.py,
    strategy-service/strategy_service/position/core/reconciliation_engine.py,
  ]
type: data-correctness
auditor: claude (6-agent Workflow + 1 follow-up agent, operator-directed)
severity: P0
date: 2026-07-08
audited_scope: >-
  instruments-service adapters (39+ files sampled), MTDS (adapters + ~50 live websocket connectors + manifest-rebuild
  scripts), deployment-api (11 files reading instrument_id/instrument_type), deployment-ui (10 files), strategy-service
  (position/reconciliation/PnL engines), real GCS parquet reads (cefi/defi/tradfi/sports/prediction catalogs +
  instruments-store and market-tick-data manifests, 5 asset groups).
parent_epic: instruments_master
resulting_plan:
  [
    ../../active/canonical_id_p0_kraken_futures_collision_2026_07_08.md,
    ../../active/canonical_id_p0_defi_adapter_type_filter_bug_2026_07_08.md,
    ../../active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md,
    ../../active/canonical_id_p0_strategy_reconciliation_2026_07_08.md,
  ]
lib_version:
doc_versions_checked: []
---

# Canonical instrument_id compliance audit — 2026-07-08

> **This audit found real, live, silently-wrong-today bugs, not just naming/format inconsistency.** Per the workspace
> rule that data-pipeline-correctness findings don't get deferred, the 5 P0 items below each get their own small,
> immediately-actionable plan (listed in `resulting_plan:` above) rather than waiting for the broader canonicalization
> decision to land. The P1/P2 findings feed the existing [[instrument_id_format_canonicalization_2026_07_08]] decision
> doc and the [[instruments_service_docs_consolidation_2026_07_08]] plan's Phase 1.

## Why this audit happened

Spawned mid-session from `instruments_service_docs_consolidation_2026_07_08.md`'s Phase 1 (audit-before-writing), after
the operator asked for the docs-consolidation effort to actually check "all the services... everything in GCS, the
manifest, the parquet file names" for canonical instrument_id usage — not just instruments-service's own docs. Split out
as its own audit (per this workspace's audit-is-its-own-plan rule) rather than folded into the docs plan directly. Run
as a 6-agent parallel Workflow (instruments-service / MTDS / deployment-api / deployment-ui / GCS-parquet-reality /
manifest-reality) plus one follow-up agent (strategy-service, not originally in scope, added when the operator pointed
out it's where the `@LIN`/`@INV` convention already lives).

## P0 — real, live, silently-wrong-today bugs (own plans, not deferred)

1. **Kraken-Futures dated-future symbol collision — real data corruption.**
   `market-tick-data-service/.../tardis_adapter.py:341-352` (`_extract_underlying_for_chain`) assumes a `TICKER-QUOTE`
   shape; Kraken's real format is `{TYPE_PREFIX}_{PAIR}_{DATE}` (`FI_XBTUSD_220325` — `FI`/`FF`/`PI`/`PF` are
   contract-type codes, not tickers). The regex falls through to grabbing the 2-letter type-prefix. Confirmed via 5 real
   parquet files: BCH/ETH/LTC/XBT/XRP quarterly futures (same 2026-03-25 expiry) all write to the byte-identical
   `instrument_id` `KRAKEN-FUTURES:FUTURE:FI-USD-inverse-20220325`. Structural — every Kraken dated future hits this. →
   `canonical_id_p0_kraken_futures_collision_2026_07_08.md`
2. **Live position reconciliation silently defeated for every CCXT venue.**
   `strategy-service/.../reconciliation_engine.py::_find_exchange_qty` compares the internal canonical `instrument_id`
   against `ex_pos["instrument"]`, which is the raw exchange symbol from the CCXT/Binance/Bybit adapters
   (`instrument_id=str(pos.get("symbol") or "")`, unmodified). Canonical vs. raw never string-match → always falls
   through to `exchange_qty=Decimal("0")`. The check whose job is to catch a real position mismatch cannot distinguish
   "no exchange position" from "the string comparison failed." Affects Binance/Bybit/OKX/Deribit/Coinbase/Upbit/Kraken.
   → `canonical_id_p0_strategy_reconciliation_2026_07_08.md`
3. **23 DeFi adapters silently return empty on canonical-form type filters.** 7 lending adapters
   (Euler_V2/Fluid/Radiant/Venus/Benqi/Morpho/Compound_V3) + 16 yield-bearing/LST adapters
   (Lido/EtherFi/JitoRestaking/Idle/KelpDAO/Karak/RocketPool/SolBlaze/Symbiotic/Sanctum/Convex/Ethena/Renzo/Pendle/Puffer/Yearn)
   guard `get_instruments()` against lowercase snake_case literals (`"lending_market"`, `"yield_bearing"`) that never
   match the real uppercase `InstrumentType` StrEnum values (`"LENDING"`, `"YIELD_BEARING"`). Any canonical-form
   type-filtered fetch across most of the DeFi universe silently returns nothing. →
   `canonical_id_p0_defi_adapter_type_filter_bug_2026_07_08.md`
4. **Live≠batch instrument_id divergence, 13 major CeFi venues.** The CCXT adapter
   (`instruments-service/.../ccxt_adapter.py:156-157`, the live-mode route for BINANCE-SPOT/-FUTURES,
   BYBIT(+SPOT/FUTURES), OKX(+SPOT/SWAP/FUTURES), DERIBIT, COINBASE-SPOT, UPBIT, KRAKEN-SPOT/-FUTURES) stores the bare
   unmodified ccxt-native symbol as `instrument_key` — never passed through any canonicalizer. Batch (Tardis) produces a
   differently-shaped id for the same real instrument. Same instrument, structurally different ids depending on mode — a
   direct live=batch determinism violation (this workspace's own core invariant). →
   `canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md`
5. **deployment-api: 2 live bugs beyond the field-vs-key pattern.** (a) Tier-3 CeFi per-instrument coverage does an
   exact-string match between instruments-service's catalog `instrument_id` and MTDS's manifest `instrument_id` — given
   confirmed ad hoc/inconsistent formats (findings above), this can silently produce phantom-missing or 0%-coverage
   results. (b) `derive_underlying_from_instrument_id`'s fallback assumes bare `BASE-QUOTE` with no venue prefix —
   proven wrong against every real production sample — corrupting the "group by underlying" breakdown today. Folded into
   `canonical_id_p0_strategy_reconciliation_2026_07_08.md`'s scope (deployment-api is the consumer-side half of the same
   reconciliation-correctness problem).

## P1/P2 — format, key-vs-field, and structural findings (feed the canonicalization decision + docs consolidation, staged)

**Confirmed correct as-designed, NOT findings (initial audit framing was wrong, corrected after operator review):**

- Sports keeps its own `LEAGUE:MATCHUP:DATE`-style scheme, not forced into `VENUE:TYPE:SYMBOL` — operator-confirmed
  reasonable, sports doesn't have a clean TYPE/SYMBOL concept.
- The 31 shared `canonical_question_group` keys between Polymarket/Kalshi rows are NOT a collision —
  `canonical_question_group` is a thematic cross-venue label
  (`unified_api_contracts/canonical/domain/instruments_catalog.py`), `venue` is tracked as a separate column, and
  sharing the label across venues is the intended mechanism for cross-venue arb comparison (same pattern as sports
  fixtures being venue/bookmaker-independent). Still open: whether any real consumer treats `instrument_id` as globally
  unique without also keying on `venue` — not yet checked.

**Real findings, staged for the canonicalization decision + docs rewrite:**

- Venue-token duplicate-spelling pattern is systemic, not a 1-off: `AAVE_V3`/`AAVEV3` (OPTIMISM),
  `MORPHO_VAULTS`/`MORPHOVAULTS`, `YEARN_V3`/`YEARNV3`, `UNISWAP_V3`/`UNISWAPV3` (the last 2 acknowledged only in a code
  comment inside `rebuild_defi_manifest.py`, never fixed at the GCS-object-path level). **New instance found 2026-07-08
  (docs-consolidation pass)**: `yearn.py:133` hardcodes `venue_tag = f"YEARN-{self._chain}"` (bare `YEARN`, no `_V3`) —
  every UAC registry (`defi_venue_capabilities.py`, `venue_launch_dates.py`, `defi_venues.py`, `venue_mapping.py`)
  consistently expects `YEARN_V3-{chain}`. This is a distinct variant from the `YEARN_V3`/`YEARNV3` underscore-spacing
  typo already listed — here the adapter's real instrument records key off a venue string (`YEARN-ARBITRUM`) that
  literally never matches any UAC venue-capability/launch-date lookup for `YEARN_V3-ARBITRUM`, silently breaking
  venue-gated feature/capability checks for every real Yearn instrument. Not yet fixed.
- Key-vs-field abbreviation mismatch (already known for PERP/PERPETUAL, LST/YIELD_BEARING/LENDING) recurs on
  `SPOT`-vs-`SPOT_PAIR`, `VAULT`-vs-`POOL`, `STAKE`-vs-`STAKING`, and reaches 10 more Solana/DeFi venues not previously
  listed (drift, mango, zeta, flash_trade, meteora, jupiter, phoenix, lifinity, kamino, marinade) plus MTDS's own
  Fluid/Karak/Jito/Symbiotic adapters stamping non-enum `instrument_type` strings (`"LENDING_MARKET"`,
  `"RESTAKING_VAULT"`) alongside canonical-key-shaped ids.
- A_TOKEN/DEBT_TOKEN lending canonicalization (already decided for AAVE_V3/SPARK/COMPOUND_V3/MORPHO) needs to cover 5
  more protocols: Euler_V2, Fluid, Radiant, Venus, Benqi.
- IBKR's TradFi adapter builds `SYMBOL:RAW_CODE:CCY` — wrong segment order, no venue token, collapses
  stocks/bonds/FX-cash into one generic `SPOT_PAIR` despite `canonical_id_builder.py` already having distinct
  EQUITY/BOND/CURRENCY types for this.
- Betfair stores raw `marketId/selectionId` with `/` instead of `:` — the most degenerate raw-passthrough found.
- Sports' own catalog is bare: `venue` is empty-string for all 116 real rows, one row's key is the literal sentinel
  `"UNKNOWN"`, only league-level entities exist (no team/match/player instrument_ids anywhere).
- TradFi has the worst delimiter-collision exposure: 38,233 real rows split into 3-9 colon-segments instead of 3 (up to
  8 colons for 3-leg butterfly spreads), ~62,650 combo rows with zero leg decomposition, 224 securities double-keyed as
  both EQUITY and SPOT_PAIR, and — operator-flagged as never acceptable, confirmed real — 92.7% of TradFi rows carry
  literal whitespace as an uncontrolled sub-delimiter.
- Prediction catalog: Polymarket rows are a bare on-chain hash (100% of 1.22M rows), Kalshi rows are a raw unprefixed
  venue ticker (100% of 45,485 rows); `base_asset`/`underlying`/`raw_symbol` are NULL for all 2.48M prediction rows. A
  real infra bug: `instruments-store-pred-prd` vs `instruments-store-prediction` bucket-naming split, both live,
  breaking the standard asset_group→bucket resolution pattern for this one asset group.
- Even `canonical_id_builder.py`'s own cited-as-correct sports example (`build_fixture_id`) doesn't follow
  `VENUE:TYPE:SYMBOL` — a different `LEAGUE:MATCHUP:DATE` scheme with a second, differently-shaped fallback path in the
  same function. (Now understood as reasonable per the operator's sports clarification above — flagged here only because
  the builder's own docstring cites it as "the correct integrated example" of the VENUE:TYPE:SYMBOL convention, which it
  isn't.)
- deployment-ui is genuinely canonical-agnostic (zero TS literal-unions, zero string-splitting on either field,
  confirmed across 10 files) — 9 of 10 seed findings render correctly today regardless of format. Two real exceptions:
  the AAVE_V3-OPTIMISM duplicate visibly fragments into two venue rows (no venue de-dup logic), and Bitfinex's dropped
  rows simply never reach the UI (upstream filtering, not a UI bug). One new minor finding: a hardcoded
  `name.toUpperCase() === "POLYMARKET"` string comparison in `DataStatusTab.tsx`, low-risk (a follow-up server call
  corrects it).
- Manifest layer: `instruments-store`'s `_index/availability_index.parquet` (CeFi/DeFi/TradFi) never carries a populated
  `instrument_id` at all (100% blank across 86,904/214,733/16,981 rows) — it's a date×venue×`data_type` rollup,
  structurally unaffected by the catalog's key-vs-field drift. The real per-instrument grain lives in the MTDS manifest,
  which independently reproduces and amplifies every catalog-level finding at far larger scale (millions of rows), plus
  new defects: systemic instrument_type casing drift (lowercase vs uppercase for the identical concept, sometimes on the
  same instrument_id/date), a literal migration-artifact sentinel (`'ticks'`/`'ticks_migrated*...'`) polluting 4,074
  TradFi rows, and one real cross-asset-group contaminated row (a CEFI record inside the SPORTS bucket's manifest).
- MTDS's manifest-rebuild script sets `instrument_id` to the raw GCS filename stem in one code path and leaves it blank
  in another, for the same real captured data that has a fully-populated, correctly-shaped `instrument_id` inside the
  parquet rows themselves.
- ~50 MTDS live websocket connector files each hand-roll their own `instrument_id.split(":")` parsing with no shared
  logic — a concrete migration-cost data point: canonicalizing the format means touching all ~50 individually, not one
  shared parser.
- `canonical_id_builder.py` (`unified-api-contracts`) is reached by more real production code than previously known
  (MTDS's `canonical_write.py` for DeFi `lst_rates`, and `tardis_shared.py` for CeFi/TradFi dated-derivative backfills)
  but inconsistently — other real ingestion paths for the same data types still bypass it, producing a 3rd/4th distinct
  construction convention.

## Operator decisions made reviewing this audit (2026-07-08)

- No trailing `@VENUE` on the margin marker (redundant — venue is already the first colon-segment). Target:
  `VENUE:TYPE:BASE[_QUOTE]@LIN|@INV-YYYYMMDD[-STRIKE-C|P]`.
- The convention must be enforced via real, callable builder functions everywhere — not docstring-only assertions
  (today's state for both `canonical_id_builder.py` and strategy-service's `@LIN`/`@INV`).
- DEX-pool fee tier must be part of the canonical symbol (real basis-point values matching Uniswap V3's convention:
  100/500/3000/10000), not dropped as it is today (bare pool_address only).
- DeFi should follow the same general `VENUE(-CHAIN):TYPE:SYMBOL` shape as CeFi — not treated as a fundamentally
  different scheme (unlike Sports, which legitimately is different).
- Whitespace as a delimiter is never acceptable anywhere.
- Scope explicitly includes breaking live behavior — no live trading is running yet, live VMs can be stopped for this
  migration. Sequence: audit (this doc) → decisions → ground-up migration (UAC → instruments-service → MTDS →
  strategy-service → deployment-api/UI, in that order, deployment last since it's the lightest lift) → refresh the
  mockup artifacts to visually verify full shard-dimension coverage → GCS/manifest/filename migrations fully spec'd and
  executed → MTDS resumes downloading the remaining MVP universe on a consistent canonical foundation.
- Tracked under existing epics (`instruments_master` primary, cross-referenced from `batch_live_symmetry_master` for the
  live≠batch/reconciliation findings and `client_isolation_and_governance_master` for the UAC-schema governance angle)
  rather than a new 21st epic — this workspace's epic registry is a fixed 20-entry, VM-assigned table, not a free-form
  initiative tracker.

## Still open (not yet checked)

- Whether any real consumer treats prediction `instrument_id` as globally unique without keying on `venue` too (the one
  unresolved piece of the canonical_question_group question above).
- Full migration-mechanics scoping (backfill vs. go-forward-only) for each P0/P1 finding — tracked as a todo on
  [[instrument_id_format_canonicalization_2026_07_08]].
- The MVP-universe-per-asset-group cross-check against `/codex/09-strategy/mvp-universe-per-asset-group.md` (part of the
  docs-consolidation plan's Phase 1, not yet done).
