---
doc_type: issue
title: 'UAC data-type-validity combinator is fragmented across CEFI/DEFI/TRADFI -- no AG has a real (venue, instrument_type) -> data_types table, and one cell is live-wrong'
summary:
  'A 5-way audit (2026-07-07) found that no asset group has a genuine (venue, instrument_type) -> data_types
  combinator in UAC. CEFI has a flat per-venue map plus an asset-group-wide (not venue-wide) instrument-shape
  matrix, patched by three independently-bolted-on venue-specific overrides in two files. DeFi has a real
  (protocol, instrument_type) -> data_types object but it cannot narrow within a protocol and has drifted from its
  own actually-captured registry. TradFi has three orthogonal axes that are never joined, producing a live,
  provably-wrong cell: CME and ICE both get an identical futures_chain valid-data_types set despite ICE having no
  Databento coverage. Sports and Prediction are correctly excluded from this combinator entirely -- neither domain
  has a real per-instrument-type dimension (sports has no tradeable-instrument concept; a prediction market already
  encodes its full structure in one record) -- but Prediction has a separate, smaller problem: its flat venue map
  under-declares real data types, forcing a parallel deployment-api registry.'
status: open
nature: notes
asset_group: [cefi, defi, tradfi]
stage: [data, meta]
repos: [unified-api-contracts, market-tick-data-service, instruments-service, deployment-api]
scope: [engineer, admin]
tags: [uac, ssot, data-type, instrument-type, combinator, cefi, defi, tradfi, honest-coverage]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P1
source: 'ASTER/CEFI instrument-service audit follow-up, 2026-07-07 -- 5-way parallel audit (one per asset group + a cross-repo writer-duplication scan), operator-scoped to exclude Sports/Prediction from the combinator redesign'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: high
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: correct-codex
locked_since:
---

> **Scope note (operator-confirmed 2026-07-07):** this combinator applies to **CEFI, DEFI, TRADFI only**. Sports has
> no tradeable-instrument concept at all (a fixture/league/bookmaker isn't an instrument with a shape) — its one
> "instrument_type" value is a catalogue-grain label borrowed from an unrelated reference-data map, and UAC's own
> dead matrix rows for sports are already marked `UNCERTAIN`/unused. Prediction's instrument is always the same
> shape (`PREDICTION_MARKET`) because a prediction market's full structure — question, outcomes, resolution — is
> already encoded in one record; there is no spot-vs-perpetual-vs-option-style variation to combinate over. Forcing
> either domain into a `(venue, instrument_type) → data_types` table would manufacture a dimension neither domain
> has — the same mistake `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` already flagged for
> `market_metadata`. Both stay on the simpler flat venue-map shape; see the separate, smaller Prediction todo below.

## Findings, worst first

1. **Live, silently-wrong cell (TradFi).** `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`
   (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:611-735`) is keyed
   `(asset_group, instrument_type)` — not `(venue, instrument_type)`. Its accessor,
   `valid_data_types_for_venue_instrument_type` (`market_data_categories.py:995-1032`), accepts a `venue` parameter
   and then discards it for every asset group except DeFi (`:1019-1020`, `if asset_group.lower() != "defi" or not
   venue: return valid_data_types_for_instrument_type(...)`). Net effect: CME and ICE, both stamped
   `instrument_type="futures_chain"`, get the identical valid-data_types set (line 666's comment literally asserts
   "CME/ICE futures_chain cells with ohlcv_1s") — even though ICE has no Databento coverage at all (per the
   venue-list's own comment, `:273-285`) and `VENUE_DATA_TYPE_CAPABILITIES["ICE"]` doesn't declare `ohlcv_1s`
   (`:1276`). This directly contradicts the flat venue map with no reconciliation.
2. **DeFi's two registries have drifted from each other.** `PROTOCOL_CAPABILITIES` (the "should be valid"
   declaration, `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:344-843`) and
   `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (the "actually captured" registry,
   `unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py:17-232`) disagree on vocabulary
   for the same protocols, independent of chain: Aave/Radiant/Spark/Compound/Euler/Fluid all declare `liquidations`/
   `risk_params` as valid via the shared `_LENDING_DATA` shorthand (`_defi.py:338`), but zero instances of either
   are ever actually captured anywhere in `DEFI_VENUE_DATA_TYPE_CAPABILITIES`; conversely `oracle_prices` is
   captured on every Aave chain but never declared valid. Nothing enforces the two registries stay in sync, and
   unlike the module's own convention for aspirational entries (an inline comment, `_defi.py:322-324`), these carry
   none.
   **The same drift also shows up one level down, at `instrument_type` rather than `data_type`** (found
   2026-07-07, later same day): `InstrumentType.DEBT_TOKEN` is a fully real, declared type — a schema contract
   exists for `("defi", "debt_token", "lending_indices")`
   (`unified-api-contracts/unified_api_contracts/internal/schemas/_defi_v2_contracts.py:99`) — but a live pull of
   `AAVE_V3-ETHEREUM`'s real `instrument_types` breakdown shows only `a_token` (the supply-side receipt token);
   `debt_token` (the borrow-side counterpart, i.e. what people owe) has zero captured rows anywhere. Aave lending
   positions are being tracked one-sided today: we see what people supplied, not what they borrowed. Same root
   pattern as the `liquidations`/`risk_params` drift above — declared, schema-ready, never wired to a capture
   path — just one axis deeper (a whole missing `instrument_type`, not a missing `data_type` within one).
3. **CEFI's per-instrument-type narrowing is three independently-bolted-on patches, not one mechanism**, in two
   files: `DERIBIT_MVP_INSTRUMENT_TYPE_DATA_TYPES` (`market_data_categories.py:549-553`, Deribit-only,
   instrument_type-keyed, consumed by MTDS fetch-scoping) · `CeFiMvpRule.instrument_type_data_types`/
   `.venue_data_types` (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py:204-205,
   465-467, 479-483`, a *different* sparser mechanism narrowing Deribit OPTION and cutting Coinbase to trades-only)
   · `FUTURE_BUNDLE_VENUES` (`market_data_categories.py:809-812`, a grain-axis overlay affecting Deribit and OKX).
   Plus one confirmed-dead remnant, `MVP_VENUE_DATA_TYPES` (`market_data_categories.py:539-544`, zero consumers
   workspace-wide). Each was added independently for a different purpose (MVP cost-cutting vs. could-exist shape
   validity vs. capture-grain) with no shared shape.
4. **MTDS re-hardcodes facts UAC already declares, and one has already drifted.**
   `market-tick-data-service/market_tick_data_service/cli/handlers/book_microstructure_handler.py:73-83`'s
   `_L5_VENUES` tuple (meant to list every `book_snapshot_5`-capable CeFi venue) is missing 11 venues UAC's
   `VENUE_DATA_TYPE_CAPABILITIES` declares as capable (BYBIT-SPOT, COINBASE-FUTURES, BITFINEX-SPOT/FUTURES,
   BITGET-SPOT/FUTURES, KRAKEN-SPOT/FUTURES, HYPERLIQUID, ASTER, PACIFICA-SOLANA, EXTENDED-STARKNET,
   LIGHTER-ZKSYNC). Currently cosmetic (only feeds a `preflight()` log line), but a live example of the drift class.
   Two more confirmed duplicates: `onchain_perp_batch_handler.py:122-126`'s `_SOURCE_COVERAGE_START` (byte-identical
   to `VENUE_DATA_TYPE_CAPABILITIES["HYPERLIQUID"]`, and itself a copy of a *third* hardcoded pair in
   `market_tick_data_service/adapters/hyperliquid_s3.py:51-52` — the same fact now lives in three unlinked places);
   `solana_defi_handler.py:246-257`'s `_PROTOCOL_TO_DATA_TYPE` (splits `"kamino"` into two protocol keys with no
   corresponding UAC entry for the split — a structural mismatch, not just a copy).
5. **Prediction's flat venue map under-declares real data types** (separate from the instrument_type question —
   see the scope note above): `VENUE_DATA_TYPE_CAPABILITIES["POLYMARKET"/"KALSHI"]` only declares `trades`, so
   `deployment-api/deployment_api/services/data_status/mtds.py:143-215` has to maintain a parallel
   `PREDICTION_DATA_TYPE_META` just to keep the honest-coverage denominator correct for `book_snapshot`/
   `market_metadata`/`fills` — a real UAC-completeness gap, patched outside UAC rather than fixed in it.
6. **A real modeling gap MTDS is already patching around**: `onchain_perp_batch_handler.py:136-148`'s
   `_LIVE_ONLY_DATA_TYPES`/`_DROPPED_DATA_TYPES` exist because UAC's `VENUE_DATA_TYPE_CAPABILITIES` has no
   batch-vs-live (`pipeline_mode`) axis — only a bare start-date per `(venue, data_type)`. When a venue's batch and
   live paths genuinely differ in what they can serve (ASTER: `book_snapshot_5`/`liquidations` are live-only), MTDS
   has nowhere in UAC to source that fact and invents its own local, unenforced mini-registry. This is direct
   evidence the eventual fix needs a `pipeline_mode` axis, not just an `instrument_type` one.

## The target shape — two layers, not one flat table

**Correction (2026-07-07, operator-caught):** an earlier draft of this section collapsed DeFi's chain into `venue`
as an opaque `"PROTOCOL-CHAIN"` string and claimed "no separate chain axis needed." That's wrong — chain is a real
axis, it just belongs on a different layer than instrument_type does, and conflating the two layers is exactly
what let finding 2's drift go unnoticed. Two layers, explicitly joined:

1. **Theoretical validity** — `(asset_group, protocol, instrument_type) → frozenset[data_type]`, **chain-agnostic
   by design**. A protocol's conceptual shape (does a lending protocol produce `lending_indices`? does an option
   produce `options_chain`?) doesn't change based on which chain it's deployed on. This is what
   `PROTOCOL_CAPABILITIES` already correctly does for DeFi and what CEFI's `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`
   already correctly does chain-lessly (CEFI has no chain concept for its own venues, only for the 2 on-chain CLOB
   venues classified under it — those are DeFi-shaped for this purpose). Nothing about this layer needs to change
   shape; TradFi's version just needs `venue` to stop being silently discarded (see finding 1's fix).
2. **Actual availability / genesis** — `(asset_group, chain, venue, instrument_type, pipeline_mode) →
   {data_type: genesis_date}`, **chain IS a mandatory explicit key here** — not folded into an opaque venue string.
   Whether a specific chain's subgraph/RPC/exchange-API actually exposes a data type is an infrastructure fact that
   genuinely varies (Aave on Ethereum exposes 7 data_types; the same protocol on Scroll/zkSync exposes 2, per
   finding 2) — this is exactly the axis the current `DEFI_VENUE_DATA_TYPE_CAPABILITIES` already varies by
   (correctly), it just isn't a named, first-class key column today. For CEFI/TradFi, `chain` is simply absent/null
   (no chain concept), so the table degrades cleanly to today's flat venue map for those two asset groups.
3. **The join, not either layer alone, is the actual fix.** A single accessor should compose both layers and
   assert `actual ⊆ theoretical` per `(chain, venue, instrument_type)` — that check is what's missing today, and
   it's what would have caught finding 2's drift (Aave declaring `liquidations`/`risk_params` as theoretically
   valid while zero chains ever actually captured either) automatically instead of requiring a manual audit to
   surface it.
- `pipeline_mode` (batch vs. live) is a first-class axis on the availability layer only — finding 6 shows MTDS
  already needs this dimension in practice; it has no meaning on the theoretical-validity layer (a protocol either
  can conceptually produce a data type or it can't, independent of batch/live transport).

## Todos

- [ ] [CODE] P1. **Fix the live CME/ICE cell** (finding 1) — stop-gap: make
      `valid_data_types_for_venue_instrument_type` actually use `venue` for TRADFI (not just DeFi), or hand-correct
      the `("tradfi","futures_chain")` comment/set at `market_data_categories.py:666` to not claim `ohlcv_1s` for
      ICE. Do this regardless of whether the full combinator redesign (below) is approved — it's a live wrong
      answer today.
- [ ] [DESIGN] P1. **Operator decision:** approve the two-layer target shape above (theoretical validity
      `(asset_group, protocol, instrument_type) → data_types`, chain-agnostic; actual/genesis
      `(asset_group, chain, venue, instrument_type, pipeline_mode) → {data_type: date}`, chain-explicit; joined by
      an `actual ⊆ theoretical` accessor check) as the replacement for the five fragmented mechanisms in findings
      1-4, or an alternative. This is a genuine redesign of a widely-read UAC registry — needs a pre-audit of every
      consumer (`enumerate_expected_universe.py`, `venue_fetch.py`, `possible_manifest.py`,
      `breakdowns_core.py`/`mtds.py` at minimum) before touching it.
- [ ] [CODE] P2. Reconcile DeFi's `PROTOCOL_CAPABILITIES` vs. `DEFI_VENUE_DATA_TYPE_CAPABILITIES` vocabulary drift
      (finding 2) — once the `actual ⊆ theoretical` join check exists (previous todo), run it once over the current
      data to get the full violation list mechanically rather than by hand. Until then: for each
      declared-but-never-captured type (`liquidations`, `risk_params` on the `_LENDING_DATA` protocols) and each
      captured-but-undeclared type (`oracle_prices`), decide per-protocol whether to add the
      inline aspirational-entry comment the module convention expects, or drop the declaration to match reality.
      **Also decide Aave's `debt_token` specifically** (found 2026-07-07, later same day): a real schema contract
      exists (`_defi_v2_contracts.py:99`) but zero rows are ever captured — either wire a borrow-side capture path
      or, if that's out of scope for now, mark the declaration as aspirational per the module's own convention so
      it doesn't silently read as "this works."
- [ ] [CODE] P2. Fix `_L5_VENUES` (finding 4) to read from `VENUE_DATA_TYPE_CAPABILITIES` instead of a hardcoded
      tuple; audit `_SOURCE_COVERAGE_START` and `_PROTOCOL_TO_DATA_TYPE` for the same fix, resolving the
      `"kamino"`/`"kamino_lending"` split mismatch against UAC's single `"kamino"` entry either direction.
- [ ] [CODE] P2. Add the missing `book_snapshot`/`market_metadata`/`fills` declarations to
      `VENUE_DATA_TYPE_CAPABILITIES["POLYMARKET"/"KALSHI"]` (finding 5) and retire deployment-api's parallel
      `PREDICTION_DATA_TYPE_META` once UAC is complete. This is independent of the CEFI/DEFI/TRADFI combinator
      redesign — a plain completeness fix.
- [ ] [SCRIPT] P3. Delete confirmed-dead code: `MVP_VENUE_DATA_TYPES` (zero consumers), DeFi's emptied
      `DEFI_VENUE_AXIS_OVERRIDES = {}` (`defi_venues.py:573`) plus the stale comment referencing it in
      `defi_venue_capabilities.py:133-134`, and Prediction's inert `(asset_group, instrument_type)` matrix row
      (`market_data_categories.py:732-734`, already documented as a no-op) once its scope exclusion (this doc's
      header note) is itself the authoritative record.

## Progress Log

- **2026-07-07 (later same day)** — Added the Aave `debt_token` finding to finding 2 and its todo — the same
  declared-vs-captured drift pattern, one axis deeper (a whole missing `instrument_type`, not a missing
  `data_type` within one). Surfaced during a conceptual walkthrough of DeFi instrument_type semantics
  (`a_token`/`debt_token`/`spot_asset`/`pool`), not a fresh audit pass.
- **2026-07-07** — Filed from a 5-way parallel audit (one agent per asset group + a cross-repo writer-duplication
  scan) following the ASTER/CEFI shard-dimension work. Operator confirmed the scope exclusion for Sports/Prediction
  before this doc was written — the combinator redesign targets CEFI/DEFI/TRADFI only; Prediction's separate
  venue-map-completeness gap (finding 5) is tracked as its own smaller, independent todo. No files edited.
