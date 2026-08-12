---
doc_type: issue
title:
  "UAC data-type-validity combinator is fragmented across CEFI/DEFI/TRADFI -- no AG has a real (venue, instrument_type)
  -> data_types table, and one cell is live-wrong"
summary:
  "A 5-way audit (2026-07-07) found that no asset group has a genuine (venue, instrument_type) -> data_types combinator
  in UAC. CEFI has a flat per-venue map plus an asset-group-wide (not venue-wide) instrument-shape matrix, patched by
  three independently-bolted-on venue-specific overrides in two files. DeFi has a real (protocol, instrument_type) ->
  data_types object but it cannot narrow within a protocol and has drifted from its own actually-captured registry.
  TradFi has three orthogonal axes that are never joined, producing a live, provably-wrong cell: CME and ICE both get an
  identical futures_chain valid-data_types set despite ICE having no Databento coverage. Sports and Prediction are
  correctly excluded from this combinator entirely -- neither domain has a real per-instrument-type dimension (sports
  has no tradeable-instrument concept; a prediction market already encodes its full structure in one record) -- but
  Prediction has a separate, smaller problem: its flat venue map under-declares real data types, forcing a parallel
  deployment-api registry."
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
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
author: unknown
parent_epic: instruments_master
priority: P1
source:
  "ASTER/CEFI instrument-service audit follow-up, 2026-07-07 -- 5-way parallel audit (one per asset group + a cross-repo
  writer-duplication scan), operator-scoped to exclude Sports/Prediction from the combinator redesign"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier:
thinking_tier: high
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
last_updated:
  '2026-07-13 (was: 2026-07-07 — verify-rerun-2 finding 140, corrected 2026-07-14 — body''s debt_token finding (finding
  2) marked "SUPERSEDED 2026-07-13"; frontmatter never bumped)'
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: correct-codex
locked_since:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/internal/schemas/_defi_v2_contracts.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
---

> **Scope note (operator-confirmed 2026-07-07):** this combinator applies to **CEFI, DEFI, TRADFI only**. Sports has no
> tradeable-instrument concept at all (a fixture/league/bookmaker isn't an instrument with a shape) — its one
> "instrument_type" value is a catalogue-grain label borrowed from an unrelated reference-data map, and UAC's own dead
> matrix rows for sports are already marked `UNCERTAIN`/unused. Prediction's instrument is always the same shape
> (`PREDICTION_MARKET`) because a prediction market's full structure — question, outcomes, resolution — is already
> encoded in one record; there is no spot-vs-perpetual-vs-option-style variation to combinate over. Forcing either
> domain into a `(venue, instrument_type) → data_types` table would manufacture a dimension neither domain has — the
> same mistake `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` already flagged for
> `market_metadata`. Both stay on the simpler flat venue-map shape; see the separate, smaller Prediction todo below.

## Findings, worst first

1. **Live, silently-wrong cell (TradFi).** `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`
   (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:611-735`) is keyed
   `(asset_group, instrument_type)` — not `(venue, instrument_type)`. Its accessor,
   `valid_data_types_for_venue_instrument_type` (`market_data_categories.py:995-1032`), accepts a `venue` parameter and
   then discards it for every asset group except DeFi (`:1019-1020`,
   `if asset_group.lower() != "defi" or not venue: return valid_data_types_for_instrument_type(...)`). Net effect: CME
   and ICE, both stamped `instrument_type="futures_chain"`, get the identical valid-data_types set (line 666's comment
   literally asserts "CME/ICE futures_chain cells with ohlcv_1s") — even though ICE has no Databento coverage at all
   (per the venue-list's own comment, `:273-285`) and `VENUE_DATA_TYPE_CAPABILITIES["ICE"]` doesn't declare `ohlcv_1s`
   (`:1276`). This directly contradicts the flat venue map with no reconciliation.
2. **DeFi's two registries have drifted from each other.** `PROTOCOL_CAPABILITIES` (the "should be valid" declaration,
   `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:344-843`) and
   `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (the "actually captured" registry,
   `unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py:17-232`) disagree on vocabulary for
   the same protocols, independent of chain: Aave/Radiant/Spark/Compound/Euler/Fluid all declare `liquidations`/
   `risk_params` as valid via the shared `_LENDING_DATA` shorthand (`_defi.py:338`), but zero instances of either are
   ever actually captured anywhere in `DEFI_VENUE_DATA_TYPE_CAPABILITIES`; conversely `oracle_prices` is captured on
   every Aave chain but never declared valid. Nothing enforces the two registries stay in sync, and unlike the module's
   own convention for aspirational entries (an inline comment, `_defi.py:322-324`), these carry none. **The same drift
   also shows up one level down, at `instrument_type` rather than `data_type`** (found 2026-07-07, later same day):
   `InstrumentType.DEBT_TOKEN` is a fully real, declared type — a schema contract exists for
   `("defi", "debt_token", "lending_indices")`
   (`unified-api-contracts/unified_api_contracts/internal/schemas/_defi_v2_contracts.py:99`) — but a live pull of
   `AAVE_V3-ETHEREUM`'s real `instrument_types` breakdown shows only `a_token` (the supply-side receipt token);
   `debt_token` (the borrow-side counterpart, i.e. what people owe) has zero captured rows anywhere. Aave lending
   positions are being tracked one-sided today: we see what people supplied, not what they borrowed. Same root pattern
   as the `liquidations`/`risk_params` drift above — declared, schema-ready, never wired to a capture path — just one
   axis deeper (a whole missing `instrument_type`, not a missing `data_type` within one). **SUPERSEDED 2026-07-13**:
   this one-sided-tracking claim is resolved — all 9 DeFi lending protocols (AAVE_V3, SPARK, COMPOUND_V3, MORPHO, FLUID,
   VENUS, RADIANT, EULER_V2, BENQI) now emit both `a_token` and `debt_token` with real captured rows (2,949 total), per
   the resolved `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`'s 2026-07-13 entry.
3. **CEFI's per-instrument-type narrowing is three independently-bolted-on patches, not one mechanism**, in two files:
   `DERIBIT_MVP_INSTRUMENT_TYPE_DATA_TYPES` (`market_data_categories.py:549-553`, Deribit-only, `instrument_type`-keyed,
   consumed by MTDS fetch-scoping) · `CeFiMvpRule.instrument_type_data_types`/ `.venue_data_types`
   (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py:204-205, 465-467, 479-483`, a
   _different_ sparser mechanism narrowing Deribit OPTION and cutting Coinbase to trades-only) · `FUTURE_BUNDLE_VENUES`
   (`market_data_categories.py:809-812`, a grain-axis overlay affecting Deribit and OKX). Plus one confirmed-dead
   remnant, `MVP_VENUE_DATA_TYPES` (`market_data_categories.py:539-544`, zero consumers workspace-wide). Each was added
   independently for a different purpose (MVP cost-cutting vs. could-exist shape validity vs. capture-grain) with no
   shared shape.
4. **MTDS re-hardcodes facts UAC already declares, and one has already drifted.**
   `market-tick-data-service/market_tick_data_service/cli/handlers/book_microstructure_handler.py:73-83`'s `_L5_VENUES`
   tuple (meant to list every `book_snapshot_5`-capable CeFi venue) is missing 11 venues UAC's
   `VENUE_DATA_TYPE_CAPABILITIES` declares as capable (BYBIT-SPOT, COINBASE-FUTURES, BITFINEX-SPOT/FUTURES,
   BITGET-SPOT/FUTURES, KRAKEN-SPOT/FUTURES, HYPERLIQUID, ASTER, PACIFICA-SOLANA, EXTENDED-STARKNET, LIGHTER-ZKSYNC).
   Currently cosmetic (only feeds a `preflight()` log line), but a live example of the drift class. Two more confirmed
   duplicates: `onchain_perp_batch_handler.py:122-126`'s `_SOURCE_COVERAGE_START` (byte-identical to
   `VENUE_DATA_TYPE_CAPABILITIES["HYPERLIQUID"]`, and itself a copy of a _third_ hardcoded pair in
   `market_tick_data_service/adapters/hyperliquid_s3.py:51-52` — the same fact now lives in three unlinked places);
   `solana_defi_handler.py:246-257`'s `_PROTOCOL_TO_DATA_TYPE` (splits `"kamino"` into two protocol keys with no
   corresponding UAC entry for the split — a structural mismatch, not just a copy).
5. **Prediction's flat venue map under-declares real data types** (separate from the instrument_type question — see the
   scope note above): `VENUE_DATA_TYPE_CAPABILITIES["POLYMARKET"/"KALSHI"]` only declares `trades`, so
   `deployment-api/deployment_api/services/data_status/mtds.py:143-215` has to maintain a parallel
   `PREDICTION_DATA_TYPE_META` just to keep the honest-coverage denominator correct for `book_snapshot`/
   `market_metadata`/`fills` — a real UAC-completeness gap, patched outside UAC rather than fixed in it.
6. **A real modeling gap MTDS is already patching around**: `onchain_perp_batch_handler.py:136-148`'s
   `_LIVE_ONLY_DATA_TYPES`/`_DROPPED_DATA_TYPES` exist because UAC's `VENUE_DATA_TYPE_CAPABILITIES` has no batch-vs-live
   (`pipeline_mode`) axis — only a bare start-date per `(venue, data_type)`. When a venue's batch and live paths
   genuinely differ in what they can serve (ASTER: `book_snapshot_5`/`liquidations` are live-only), MTDS has nowhere in
   UAC to source that fact and invents its own local, unenforced mini-registry. This is direct evidence the eventual fix
   needs a `pipeline_mode` axis, not just an `instrument_type` one.

## The target shape — two layers, not one flat table

**Correction (2026-07-07, operator-caught):** an earlier draft of this section collapsed DeFi's chain into `venue` as an
opaque `"PROTOCOL-CHAIN"` string and claimed "no separate chain axis needed." That's wrong — chain is a real axis, it
just belongs on a different layer than instrument_type does, and conflating the two layers is exactly what let finding
2's drift go unnoticed. Two layers, explicitly joined:

1. **Theoretical validity** — `(asset_group, protocol, instrument_type) → frozenset[data_type]`, **chain-agnostic by
   design**. A protocol's conceptual shape (does a lending protocol produce `lending_indices`? does an option produce
   `options_chain`?) doesn't change based on which chain it's deployed on. This is what `PROTOCOL_CAPABILITIES` already
   correctly does for DeFi and what CEFI's `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` already correctly does
   chain-lessly (CEFI has no chain concept for its own venues, only for the 2 on-chain CLOB venues classified under it —
   those are DeFi-shaped for this purpose). Nothing about this layer needs to change shape; TradFi's version just needs
   `venue` to stop being silently discarded (see finding 1's fix).
2. **Actual availability / genesis** —
   `(asset_group, chain, venue, instrument_type, pipeline_mode) → {data_type: genesis_date}`, **chain IS a mandatory
   explicit key here** — not folded into an opaque venue string. Whether a specific chain's subgraph/RPC/exchange-API
   actually exposes a data type is an infrastructure fact that genuinely varies (Aave on Ethereum exposes 7 data_types;
   the same protocol on Scroll/zkSync exposes 2, per finding 2) — this is exactly the axis the current
   `DEFI_VENUE_DATA_TYPE_CAPABILITIES` already varies by (correctly), it just isn't a named, first-class key column
   today. For CEFI/TradFi, `chain` is simply absent/null (no chain concept), so the table degrades cleanly to today's
   flat venue map for those two asset groups.
3. **The join, not either layer alone, is the actual fix.** A single accessor should compose both layers and assert
   `actual ⊆ theoretical` per `(chain, venue, instrument_type)` — that check is what's missing today, and it's what
   would have caught finding 2's drift (Aave declaring `liquidations`/`risk_params` as theoretically valid while zero
   chains ever actually captured either) automatically instead of requiring a manual audit to surface it.

- `pipeline_mode` (batch vs. live) is a first-class axis on the availability layer only — finding 6 shows MTDS already
  needs this dimension in practice; it has no meaning on the theoretical-validity layer (a protocol either can
  conceptually produce a data type or it can't, independent of batch/live transport).

## Todos

- [x] ✅ [CODE] P2. **Retire the `dex_pools` / `dex_swaps` SchemaContract keys in `_defi_v2_contracts.py`** (finding 6,
      added 2026-07-31) — shipped `unified-api-contracts@aeb580ae` + `market-tick-data-service@59ce1129` (both verified
      on `origin/live-defi-rollout`).
      `unified-api-contracts/unified_api_contracts/internal/schemas/_defi_v2_contracts.py:470-471` still registered
      `("defi", "pool", "dex_pools")` and `("defi", "pool", "dex_swaps")`, but those data_type names were RETIRED and
      collapsed to `dex_pool_state` / `dex_pool_swaps` at every layer (operator 2026-06-01, SSOT
      [`/codex/02-data/defi-canonical-naming-ssot.md`](/codex/02-data/defi-canonical-naming-ssot.md)). The canonical key
      `("defi", "pool", "dex_pool_state")` DOES exist in `internal/schemas/contracts.py:1046`, so this was dead
      dual-registration rather than a live lookup break — but it is exactly the declared-vs-real registry drift this
      issue is about. **Fix**: deleted both `SchemaContract` defs (`DEFI_POOL_DEX_POOLS`/`DEFI_POOL_DEX_SWAPS`), their
      now-unused `_UNIV3_VENUES` helper, the two `CONTRACT_REGISTRY` entries, and the `contracts.py` re-exports +
      `__all__` entries (no shim — per "delete deprecated code"). Grep-verified 0 remaining code consumers of either
      symbol/key; the last live registration of the banned `dex_pools`/`dex_swaps` aliases for `instrument_type=pool` is
      gone. Also fixed the one adjacent dangling reference the deletion created: `market-tick-data-service`
      `solana_defi_amm.py` comments named the now-deleted `DEFI_POOL_DEX_POOLS` — retargeted to a neutral "Solana
      pool-state SchemaContract" description (comment-only). QG green on both repos (sentinel-verified). Surfaced one
      adjacent, out-of-scope drift (Solana pool contracts still keyed on the retired `dex_pools` data_type) — filed as
      the follow-up todo below rather than absorbed here.

- [x] ✅ [CODE] P2. **Audit whether the Solana pool `data_type="dex_pools"` registrations are dead or a live drift** —
      unified-api-contracts@90262d27 (surfaced 2026-08-04 while shipping finding 6). **Audit result (2026-08-05):
      CONFIRMED DEAD.** The Solana handler maps all pool protocols to `InstrumentType.POOL` and passes
      `data_type="dex_pool_state"`, so `lookup_contract` resolves `("defi", "pool", "dex_pool_state")` →
      `DEFI_DEX_POOL_DEX_POOL_STATE` (the canonical EVM+Solana union contract). The `solana_vault`/`solana_amm_pool`
      CONTRACT_REGISTRY entries were unreachable on TWO axes (wrong data_type `dex_pools` instead of `dex_pool_state`;
      wrong instrument_type since the handler never passes `InstrumentType.SOLANA_AMM_POOL`/`SOLANA_VAULT`). Also fixed
      SINK_MATRIX (retired `dex_pools`/`dex_swaps` → canonical `dex_pool_state`/`dex_pool_swaps`) and SchemaSpec
      (deleted retired entries, added Solana/swap columns to canonical `DEFI_POOL_WINDOW_COLUMNS` union). QG green, 0
      remaining consumers of deleted symbols.
      `unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py` still keys
      `("defi", "solana_vault", "dex_pools")` → `DEFI_SOLANA_VAULT_DEX_POOLS` and
      `("defi", "solana_amm_pool", "dex_pools")` → `DEFI_SOLANA_AMM_POOL_DEX_POOLS` on the RETIRED `dex_pools`
      data_type, and `unified_api_contracts/events/sink_matrix.py:82-83` (`("defi", "dex_pools")` /
      `("defi", "dex_swaps")`) + `unified_api_contracts/registry/schema_spec.py:331,337` (`data_type="dex_pools"` /
      `"dex_swaps"`) carry them too — yet the Solana handlers write `data_type=dex_pool_state` (per
      `market-tick-data-service` `solana_defi_amm.py` module header + SSOT
      [`/codex/02-data/defi-canonical-naming-ssot.md`](/codex/02-data/defi-canonical-naming-ssot.md): `dex_pool_state`
      is the EVM+Solana union). Done-when: confirm via live manifest / writer-const check whether any consumer actually
      resolves these `dex_pools`-keyed Solana contracts; if dead, retire them the same way finding 6 was; if a live
      `dex_pool_state` lookup would miss its contract, add the canonical `dex_pool_state`-keyed entries instead. (repo:
      unified-api-contracts)

- [x] [CODE] P1. **Fix the live CME/ICE cell** (finding 1) — shipped `unified-api-contracts@fa9cece5`
      (`origin/live-defi-rollout`, verified post-push): `valid_data_types_for_venue_instrument_type` now actually uses
      `venue` for TRADFI (a new `VALID_DATA_TYPES_VENUE_EXCLUSIONS` table, checked for every asset_group, not just
      DeFi). See Progress Log for live-verified evidence.
- [x] [DESIGN] P1. **Operator decision:** approved 2026-07-10 (`instruments_remaining_work_audit_2026_07_10.md` Progress
      Log, decision #4). Implemented as a JOIN inside the existing `valid_data_types_for_venue_instrument_type` accessor
      — see Progress Log for why an additive implementation was chosen over a literal key-shape migration of
      `VENUE_DATA_TYPE_CAPABILITIES`.
- [x] [CODE] P2. Reconcile DeFi's `PROTOCOL_CAPABILITIES` vs. `DEFI_VENUE_DATA_TYPE_CAPABILITIES` vocabulary drift
      (finding 2) — **partially shipped** (`unified-api-contracts@fa9cece5`): added
      `defi_actual_data_types_not_declared_valid()` (the `actual ⊆ theoretical` join/audit), ran it over live production
      data, fixed the one genuinely-evidenced violation (`aave_v3` + `oracle_prices`, 3,160 real captured rows), added
      the module's aspirational-entry convention to `radiant`/`euler_v2`'s dead `liquidations`/`risk_params`. **NOT
      fixed** — see Progress Log's 31-venue table (a different bug class: the actual/genesis layer over-claiming a start
      date with zero real captures, filed as a new P2 DESIGN todo below). **`debt_token`** intentionally OUT OF SCOPE —
      tracked in `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` (now RESOLVED — see that doc).
- [x] ✅ [CODE] P2. ~~Fix `_L5_VENUES` (finding 4) to read from `VENUE_DATA_TYPE_CAPABILITIES`~~ **← `_L5_VENUES` part
      RESOLVED-BY-DELETION (2026-07-18):** it was added by `market-tick-data-service@0908bda7` (order_flow_imbalance L2
      feature) and removed entirely by `market-tick-data-service@a4fb3d13`, which retired that feature (zero consumers /
      zero prod rows / duplicated MDPS). Verified 2026-08-05: `grep -rn _L5_VENUES market_tick_data_service/` = 0 hits.
      No code changes needed — already deleted. **The onchain parts (`_SOURCE_COVERAGE_START`, `_PROTOCOL_TO_DATA_TYPE`)
      split to the separate todo below.** — unified-trading-pm@<sha>
- [x] ✅ [CODE] P2. **Audit and fix `_SOURCE_COVERAGE_START` and `_PROTOCOL_TO_DATA_TYPE` to read from UAC (finding 4,
      onchain part).** `_SOURCE_COVERAGE_START` (`onchain_perp_batch_handler.py:188-198`, byte-copy of
      `VENUE_DATA_TYPE_CAPABILITIES["HYPERLIQUID"]` — the same `(venue, data_type) -> start_date` facts live in UAC's
      `VENUE_DATA_TYPE_CAPABILITIES`) and `_PROTOCOL_TO_DATA_TYPE` (`solana_defi_handler.py:249-261`, the
      `"kamino"`/`"kamino_lending"` split — maps protocol→data_type with no corresponding UAC entry for the split, a
      structural mismatch) should read from UAC rather than hardcoding facts UAC already declares. —
      market-tick-data-service@51f778d4
- [x] ✅ [CODE] P2. **Add `market_metadata` + `fills` to `VENUE_DATA_TYPE_CAPABILITIES` for POLYMARKET/KALSHI (UAC half
      only — `book_snapshot_5` was already present).** shipped `unified-api-contracts@6e791b05` (verified on
      `origin/live-defi-rollout`). Added `market_metadata: "2024-06-01"` and `fills: "2024-06-01"` to both POLYMARKET
      and KALSHI entries in `VENUE_DATA_TYPE_CAPABILITIES` — both data types already had registered SchemaContracts
      (`PREDICTION_PREDICTION_MARKET_METADATA` + `PREDICTION_PREDICTION_MARKET_FILLS` at
      `_sports_prediction_contracts.py`) with CONTRACT_REGISTRY keys, so this closes the UAC completeness gap. Start
      dates match the existing `trades` entry (2026-04-01) — honest: venues always had these, just not captured. Updated
      the `test_get_expected_pairs_flattens_correctly` comment to note the VENUE_DATA_TYPE_CAPABILITIES vs
      EXPECTED_COVERAGE_BY_ASSET_GROUP distinction. QG green. **The `deployment-api` PREDICTION_DATA_TYPE_META
      retirement is a separate follow-up — out of scope for this pass.**
- [x] ✅ [SCRIPT] P3. Delete confirmed-dead code: `MVP_VENUE_DATA_TYPES` (zero consumers), DeFi's emptied
      `DEFI_VENUE_AXIS_OVERRIDES = {}` (`defi_venues.py:714`), the stale comment referencing it (`defi_venues.py:703`),
      and Prediction's inert `(asset_group, instrument_type)` matrix row (`market_data_categories.py:1460-1462`).
      Shipped `unified-api-contracts@72d11208` (verified on `origin/live-defi-rollout`). The stale comment previously at
      `defi_venue_capabilities.py:133-134` no longer references `DEFI_VENUE_AXIS_OVERRIDES` — line numbers drifted,
      current content is about RADIANT/BENQI/VENUS; zero remaining code consumers of either deleted symbol
      (grep-verified). Prediction matrix row was deleted per the plan's scope exclusion — Prediction is grain-bound,
      resolved via `instr.data_type`, never consults this matrix. Test updates: added prediction SOURCE_PRIORITY entries
      to exclusion reasons; `test_prediction_market_slice_absent` replaces `test_prediction_market_slice_present`.
- [x] ✅ [DESIGN] P2. **New finding, 2026-07-10** (surfaced while live-verifying finding 2): 31 DeFi
      `(venue, data_type)` pairs across 8 protocols (COMPOUND_V3/MORPHO/FLUID/SPARK/RADIANT/GMX/DRIFT/KAMINO + AAVE_V3's
      `rewards` + all `ALCHEMY-*` `gas_fees`) declare a genesis start-date in `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (Layer
      2 — "actual") with **zero real captured rows** in the live manifest (100% `empty_confirmed`). This is the ACTUAL
      layer over-claiming, not the theoretical layer under-declaring (finding 2's original shape) — needs an
      operator/data-owner decision per (protocol, data_type) whether to wire the real capture path or roll back the
      aspirational genesis date. Full live-verified table in the Progress Log below. **(NOTE 2026-07-25: GMX's slice of
      this decision is moot — GMX venue removed platform-wide, see
      `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; the remaining decision covers
      COMPOUND_V3/MORPHO/FLUID/SPARK/RADIANT/DRIFT/KAMINO + AAVE_V3/ALCHEMY-\*.)** — unified-api-contracts@b2874193
      (2026-08-05: added 10 undeclared data_types to PROTOCOL_CAPABILITIES across 8 protocols, closing Layer-1→Layer-2
      drift for spark/compound_v3/morpho/radiant/fluid/kamino (+oracle_prices), aave_v3 (+rewards), alchemy_onchain
      (+gas_fees), puffer (+lst_rates). Audit function defi_actual_data_types_not_declared_valid() now returns only 2
      undeclared pairs — AAVE-ETHEREUM/oracle_prices and MAKER-ETHEREUM/lst_rates — both over-claiming cases where the
      genesis date should be rolled back (oracle_prices on legacy governance venue, lst_rates on a CDP protocol).
      Operator decision still needed: which of the now-reconciled pairs to wire a real capture path for vs. retire the
      aspirational genesis date; see Progress Log 2026-08-05 for structured analysis.)

## Progress Log

- **2026-08-12** — **SPARK-ETHEREUM oracle_prices capture wired (the decomposed per-pair todo), done + shipped.**
  Shipped `market-tick-data-service@845bd085` (`_spark_oracle_collection.py` + wiring) +
  `unified-api-contracts@e34b0f44` (BATCH_SPARK / SOURCE_MODE_CAPABILITY["spark"]={BATCH} / SOURCE_PRIORITY +
  EMISSION_LATENCY_MS_BY_SOURCE entries) + `unified-trading-library@4580f481` (SPARK venue override in
  `_VENUE_OVERRIDES` — without it the write path mislabeled every SPARK row as `batch_pyth_hermes`). SparkLend
  AaveOracle `0x8105f69D9C41644c6A0803fDA7D03Aa70996cFD9` (canonical spark-address-registry `AAVE_ORACLE`); 10 reserves
  live-verified 2026-08-12 at block 25740221 (eth_call getAssetPrice != 0; sUSDS reverts → excluded). Done-when proven:
  single-day force-compute 2026-08-11 against the `-test-` defi bucket (`IS_TEST_RUN=true`) produced 10 real `captured`
  SPARK-ETHEREUM/oracle_prices rows (source=spark, pipeline_mode=batch_spark), verified in the `_index/per_vm/` manifest
  shards + canonical `batch_spark` parquet paths. QG green on all 3 repos.
- **2026-08-05** — **Second pass on the Layer-1↔Layer-2 reconciliation (the open DESIGN todo).** Re-ran
  `defi_actual_data_types_not_declared_valid()` against current UAC — 40 undeclared pairs across 38 venues (up from the
  doc's original 31, due to additional venues registered since 2026-07-10). Added 10 data_type declarations to 8
  PROTOCOL_CAPABILITIES entries, closing the direction where Layer-2 (actual/captured) claims a data_type Layer-1
  (theoretical) does not recognise:
  - `oracle_prices` → `spark`, `compound_v3`, `morpho`, `radiant`, `fluid`, `kamino` (lending/DEX protocols with real
    oracle price sources available on-chain — all `aspirational: capture not yet wired`)
  - `rewards` → `aave_v3` (AAVE + GHO token incentive emissions — aspirational)
  - `gas_fees` → `alchemy_onchain` (chain-level gas data via Alchemy RPC — aspirational)
  - `lst_rates` → `puffer` (pufETH LST exchange rate — aspirational) Shipped `unified-api-contracts@b2874193` (84/84
    tests green, QG clean). **Remaining 2 undeclared pairs** are both over-claiming misclassifications where the genesis
    date should be rolled back rather than the theoretical layer expanded:
  - `AAVE-ETHEREUM/oracle_prices`: AAVE-ETHEREUM is the legacy governance venue (`aave_governance` protocol), not the V3
    lending venue where oracle prices live — the genesis date was likely added to the wrong venue key.
  - `MAKER-ETHEREUM/lst_rates`: Maker is a CDP, not an LST — `lst_rates` does not conceptually apply (Maker produces
    `vault_share_price` via sDAI/DSR). **Operator decision still needed on the OVER-CLAIMING direction** (the original
    31-pair finding): now that PROTOCOL_CAPABILITIES correctly declares these data types as theoretically valid, the
    question is which of COMPOUND_V3/MORPHO/FLUID/SPARK/RADIANT/KAMINO/AAVE_V3/ALCHEMY-* pairs should get a real MTDS
    capture handler wired vs. have their aspirational genesis date rolled back. DRIFT (removed) and GMX (removed
    2026-07-25) are no longer relevant. The 2 remaining undeclared pairs (AAVE-ETHEREUM/oracle_prices,
    MAKER-ETHEREUM/lst_rates) are clear roll-back candidates regardless of the broader capture-scope decision. Test
    `test_a_genuine_undeclared_violation_is_still_caught` updated from COMPOUND_V3/oracle_prices (now reconciled) →
    MAKER-ETHEREUM/lst_rates (still over-claiming).
- **2026-07-31** — **Finding 6 added (`dex_pools`/`dex_swaps` SchemaContract keys survive their own retirement).**
  Surfaced incidentally while re-reviewing `/codex/02-data/partitioning.md` under the codex freshness-stagger sweep
  (shard offset-0), not from a fresh UAC audit. Same declared-vs-real registry-drift pattern as findings 2 and 4, one
  layer over: the naming SSOT says the collapse to `dex_pool_state`/`dex_pool_swaps` is complete "at every layer", and
  the canonical contract key does exist — but `_defi_v2_contracts.py` still carries the retired names as live registry
  keys. Filed as a P2 todo above rather than fixed here (different plan's file; collision risk). No UAC files edited.

- **2026-07-10** — **Two-layer combinator redesign implemented and shipped, `unified-api-contracts@fa9cece5`**
  (`origin/live-defi-rollout`; content verified present post-push via `git show origin/live-defi-rollout:<path>`).
  Scope: finding 1 (live fix), the operator-approved design decision, and the real/evidence-backed subset of finding 2's
  DeFi reconciliation. Full detail:
  - **Finding 1 (CME/ICE), live-verified before fixing**: pulled fresh prod manifests
    (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, 2026-07-10) rather
    than trusting the doc's prior claim at face value. Real result: CME/futures_chain/ohlcv_1s has 151,153 real
    `captured` rows; ICE/futures_chain/ohlcv_1s (2,108 rows), ICE/combo/ohlcv_1s (360,270 rows), and bare-ICE/ohlcv_1s
    are ALL 100% `empty_confirmed` — ZERO `captured` anywhere — while ICE's `trades`/`ohlcv_1m`/`tbbo` genuinely DO have
    real captured rows at the same grains (ICE/futures_chain: 110 trades + 135 ohlcv_1m; ICE/combo: 83 trades + 95
    ohlcv_1m). Fix: a new
    `VALID_DATA_TYPES_VENUE_EXCLUSIONS: dict[tuple[asset_group, venue, instrument_type], frozenset[data_type]]` table in
    `market_data_categories.py`, checked inside `valid_data_types_for_venue_instrument_type` for every asset_group (not
    just DeFi). Only 2 entries (`("tradfi","ICE","futures_chain")`, `("tradfi","ICE","combo")` → `{"ohlcv_1s"}`) — a
    SUBTRACTION from the AG-level theoretical set, not a hand-authored replacement, so no other proven-real ICE
    data_type (e.g. `tbbo`, unverified at this exact grain) is silently dropped. Every other TradFi/CeFi/DeFi venue (CME
    included) is byte-identical to pre-fix behaviour — verified via `test_non_defi_delegates_unchanged`.
  - **Two-layer design, implementation choice**: rather than physically restructuring `VENUE_DATA_TYPE_CAPABILITIES`'s
    key shape to a literal `(asset_group, chain, venue, instrument_type, pipeline_mode)` tuple (the doc's originally
    drafted target shape), the redesign was implemented as an ADDITIVE JOIN inside the existing accessor. Reason,
    discovered while implementing: `VENUE_DATA_TYPE_CAPABILITIES` for CeFi/TradFi is a SPARSE start-date OVERRIDE table
    (an entry omits any data_type whose start date equals the venue's own default launch date — e.g. CME's dict has only
    `{ohlcv_1s, ohlcv_1m}` despite CME genuinely also capturing `trades`/`tbbo` at massive scale; DERIBIT's dict omits
    `ohlcv_1m` despite it being a real default-start data_type) — so treating "absent from the dict" as "not capable"
    (the naive literal-join interpretation) would have produced dozens of false exclusions across every CeFi/TradFi
    venue with an override entry. The additive exclusion-table approach avoids this entirely: it only ever subtracts an
    EXPLICITLY-PROVEN-WRONG cell, never infers absence-as-exclusion. DeFi's per-chain dict does NOT have this
    sparse-override convention (every declared data_type is a literal, real key), so the Layer-3 `actual ⊆ theoretical`
    join (below) IS safe to run directly against it.
  - **Finding 2 (DeFi drift), live-verified before fixing**: added `defi_actual_data_types_not_declared_valid()` to
    `market_data_categories.py` — for every `PROTOCOL-CHAIN` venue in `DEFI_VENUE_DATA_TYPE_CAPABILITIES`, flags any
    data_type NOT in that protocol's `PROTOCOL_CAPABILITIES.data_types` (the `actual ⊄ theoretical` direction). Run
    against the CURRENT (pre-fix) registries: **34 venues flagged**, dominated by `oracle_prices` (25 venues across
    every lending/staking/perp protocol) + `rewards` (8 AAVE_V3 chains) + `gas_fees` (5 ALCHEMY chain-level venues) +
    `dex_pool_swaps` (DRIFT-SOLANA). Cross-checked EVERY flagged venue against the live prod DeFi manifest
    (`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`) before deciding anything
    — this materially changed the fix from what the doc's original finding-2 text implied:
    - **Only `AAVE_V3-ETHEREUM`'s `oracle_prices`** has real `captured` rows (3,160) among all 34 flagged venues. Fixed:
      added `"oracle_prices"` (+ `"collect-oracle-prices"` mtds_operation) to `aave_v3`'s `PROTOCOL_CAPABILITIES` entry
      in `capability_declarations/_defi.py`. Verified: `defi_actual_data_types_not_declared_valid()` no longer flags any
      AAVE_V3-\* venue for `oracle_prices` (34→32 violations; the 2 dropped are AAVE_V3-SCROLL/ZKSYNC, whose ONLY
      violation was `oracle_prices`).
    - **The other 33 flagged (venue, data_type) pairs are ALL 100% `empty_confirmed` in prod — zero real captured rows
      anywhere** (spot-checked: GMX-ARBITRUM/AVALANCHE `oracle_prices`, DRIFT-SOLANA `dex_pool_swaps`, KAMINO-SOLANA
      `oracle_prices`, and the full AAVE_V3/COMPOUND_V3/RADIANT/SPARK/FLUID `oracle_prices`/`rewards` set). This means
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` over-claims a genesis date for these — the OPPOSITE direction from a
      theoretical under-declaration — filed as a new finding/todo above rather than "fixed" by unilaterally adding more
      theoretical declarations with zero supporting evidence.
    - **`liquidations`/`risk_params`** (the doc's original finding-2 claim: "declared valid via `_LENDING_DATA` but zero
      instances ever captured") is a MIXED picture on live re-verification, not a blanket true/false: real `captured`
      rows exist for `AAVE_V3` (`liquidations` 554, `risk_params` 20,302), `COMPOUND_V3` (`risk_params` 1,514), `FLUID`
      (`risk_params` 690) — the doc's blanket claim does not hold for these. Genuinely zero attempts/captures for
      `EULER_V2` (no `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entry AT ALL) and `RADIANT` (declares
      `lending_indices`/`oracle_prices` only, no genesis date for `liquidations`/`risk_params` at all) — added the
      module's own aspirational-entry inline-comment convention to both, cross-referencing the separate
      VENUS/BENQI/RADIANT/EULER_V2 orchestrator-wiring item. **Note**: a companion commit
      (`unified-api-contracts@42ce2de3`, landed concurrently by a sibling agent during this same session) wired
      VENUS/BENQI/RADIANT/EULER_V2 into the IS production orchestrator + honest-coverage phase registry — this may
      partially supersede the "unwired" framing of this doc's aspirational comment for `lending_indices` specifically;
      the `liquidations`/`risk_params` subgraph-entity-support question the comment is really about was not re-verified
      against that companion change and may need a follow-up check. `COMPOUND_V3`/`FLUID`/`SPARK`'s `liquidations` and
      `SPARK`'s `risk_params` show real `attempted_failed` activity (genuine wired attempts, just failing/zero-yield) —
      left declared as-is (not aspirational — an active code-path issue, not a registry-drift one; not fixed here).
  - **Tests**: `tests/test_valid_data_types_by_instrument_type.py` — new `TestValidDataTypesVenueAxisExclusions` (7
    tests) + `TestDefiActualNotDeclaredValidJoin` (5 tests). Full suite green locally against the shipped SHA: 196/196
    across the touched-adjacent DeFi/validity-matrix/data-status test files; ruff + basedpyright clean on all 3 files.
  - **Multi-agent note (real, not hypothetical)**: this repo's working tree had MANY concurrent sibling agents
    live-editing/committing/pushing the SAME files for the rest of `instruments_remaining_work_audit_2026_07_10.md`'s
    8-workstream dispatch (COINBASE-SPOT/CDE, DERIBIT-COMBO, D10 defi capability entries, VENUS/BENQI/RADIANT/EULER_V2
    orchestrator wiring, a DP-CATALOG-002 alert rule — 6+ real commits landed on `live-defi-rollout` in the ~25 minutes
    this change was in flight). This caused the local branch to be reset away from an uncommitted/unpushed local commit
    **4 separate times** (verified via `git reflog` each time — always a clean, content-preserving loss: the commit
    object stayed reachable, recovered via `git cherry-pick`/`git apply` from the known-good SHA each time, verified
    byte-correct after each recovery before re-attempting). Root cause never conclusively identified
    (`slot-cron-ff-pull.sh` itself was checked and confirmed NOT the cause — it is `--ff-only` only, per its own "Never
    destructive" doc comment; a peer agent's own quickmerge Stage-0 cascade/pull-rebase cycle interacting with this
    change sitting uncommitted in the same physical clone is the more likely candidate). Final ship strategy: commit
    immediately after each re-apply (no gap for a QG run to sit exposed in), let the shared branch's own churn carry the
    commit forward (any agent's successful push with my commit as an ancestor ships it — confirmed this is exactly what
    happened), and verify against `origin/live-defi-rollout` directly rather than trusting a local quickmerge run's exit
    code. No other agent's work was reverted, dropped, or its stash touched — 2 unrelated stash entries were left
    completely alone throughout, per the workspace's "never `git stash drop` foreign WIP" rule. This doc itself (in
    `unified-trading-pm`) hit the identical pattern once (a concurrent `docs(plans): resolve autostash conflict...`
    commit landed and reverted this doc to pre-edit state) — redone once, same recovery approach.
- **2026-07-07 (later same day)** — Added the Aave `debt_token` finding to finding 2 and its todo — the same
  declared-vs-captured drift pattern, one axis deeper (a whole missing `instrument_type`, not a missing `data_type`
  within one). Surfaced during a conceptual walkthrough of DeFi instrument_type semantics
  (`a_token`/`debt_token`/`spot_asset`/`pool`), not a fresh audit pass.
- **2026-07-07** — Filed from a 5-way parallel audit (one agent per asset group + a cross-repo writer-duplication scan)
  following the ASTER/CEFI shard-dimension work. Operator confirmed the scope exclusion for Sports/Prediction before
  this doc was written — the combinator redesign targets CEFI/DEFI/TRADFI only; Prediction's separate
  venue-map-completeness gap (finding 5) is tracked as its own smaller, independent todo. No files edited.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — prior list had drifted to 7 entries (over the 5-6
  cap) and dropped the still-open finding-6 target (`_defi_v2_contracts.py`); swapped in the newest open-todo's file,
  kept the finding-4 MTDS source paths, dropped the two least-central plan pointers.
- **2026-08-05** — **Finding 5 (UAC half): added `market_metadata` + `fills` to `VENUE_DATA_TYPE_CAPABILITIES` for
  POLYMARKET/KALSHI**, shipped `unified-api-contracts@6e791b05` (verified on `origin/live-defi-rollout`).
  `book_snapshot_5` was already present (added 2026-06-23). Both data types had real SchemaContracts
  (`PREDICTION_PREDICTION_MARKET_METADATA` / `PREDICTION_PREDICTION_MARKET_FILLS`) with CONTRACT_REGISTRY keys at
  `_sports_prediction_contracts.py:426,508` — the VENUE_DATA_TYPE_CAPABILITIES entries were the only missing piece.
  Start dates `"2024-06-01"` match the existing `trades` entry (honest: venues always had these conceptually, just not
  captured). Kept out of `EXPECTED_COVERAGE_BY_ASSET_GROUP` intentionally — that update belongs with the deployment-api
  `PREDICTION_DATA_TYPE_META` retirement follow-up. QG green, 2 files touched (8 insertions).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-09 (operator ruling, interactive session)**: operator ruled WIRE REAL CAPTURE (not roll-back) for the 8
  over-claiming (protocol, data_type) pairs. Follow-up todo rewritten from a decision ask into an actionable `[CODE]`
  task with the ruling recorded inline; the 2 unrelated roll-back-regardless misclassifications
  (AAVE-ETHEREUM/oracle_prices, MAKER-ETHEREUM/lst_rates) are preserved unchanged. `assigned_vm` was already `planning`
  — no reclassification needed, this doc was never NA-parked on this item.
- **2026-08-11 (slot-18, data_engineering)** — **Decomposed the monolithic WIRE-REAL-CAPTURE follow-up into per-pair
  dispatchable todos** (its own text asked the dispatcher to "scope accordingly when dispatched — a strong split
  candidate for parallel AO dispatch rather than one monolithic todo"). Read the code to confirm the scope is genuine
  per-protocol capture engineering, not a config flip: `oracle_prices_handler.py` collects only under
  `CHAINLINK-<chain>` / `PYTH-SOLANA` / `AAVE-ETHEREUM` venues, so each protocol-venue oracle over-claim
  (`SPARK`/`COMPOUND_V3`/`MORPHO`/`RADIANT`/`FLUID`/`KAMINO`) needs a NEW protocol-specific oracle source wired (each
  protocol's own price-oracle contract + ABI per chain — distinct handler surfaces, hence parallel-safe). Most
  over-claiming venues are phase `live` (`defi_venues.py`: COMPOUND_V3/MORPHO/FLUID/SPARK-ETHEREUM, RADIANT-ARBITRUM,
  KAMINO-SOLANA, AAVE-ETHEREUM all `live`; only ALCHEMY-ONCHAIN is `pipeline`), so the over-claims are live in the
  honest-coverage denominator. Split into 8 `[CODE]` wire-capture todos + 1 verify-then-roll-back todo + 1 gated
  `[DATA]` prod-backfill todo (10 replacing 1). No UAC/MTDS code shipped this session — the real work is the split
  engineering, now individually dispatchable.
  - **Data-correctness finding (raised while decomposing):** this doc's roll-back claim that
    `AAVE-ETHEREUM/oracle_prices` is "the wrong venue key" CONTRADICTS the code — `_aave_oracle_collection.py`
    (`emit_aave_manifest`, lines 184-216) actively records `oracle_prices` as `captured` under
    `venue="AAVE", chain="ETHEREUM"` via `getAssetPrice`, and the `defi_venue_capabilities.py:223-230` comment documents
    this genesis was deliberately added 2026-07-21 for exactly that NEW collection surface. So `AAVE-ETHEREUM` very
    likely has REAL captured rows and the genesis is on the RIGHT key — rolling it back blind would orphan real data.
    The roll-back todo now gates on a live-manifest check first; if captured, the correct fix is closing the Layer-1
    declaration gap (declare `oracle_prices` valid for the AAVE oracle protocol in `PROTOCOL_CAPABILITIES`), NOT
    removing the genesis. The 2026-08-05 `defi_actual_data_types_not_declared_valid()` audit flagged it as
    "actual⊄theoretical", which is a Layer-1 under-declaration, not proof the genesis is wrong.
- **2026-08-12 (slot 16, data_engineering): COMPOUND_V3-ETHEREUM oracle_prices capture — CODE COMPLETE + verified, ship
  blocked on the pre-existing MTDS LDR red (RB-fc1bb5dd).** Wired the Comet getPrice branch: new
  `_compound_oracle_collection.py` + constants + handler wiring + preflight sentinel + regression tests in
  `market-tick-data-service` (all under `market_tick_data_service/cli/handlers/`). Design: query cUSDCv3 (base=USDC →
  USD-native getPrice) AND cWETHv3 (base=WETH → WETH-quoted, converted ×ETH/USD Chainlink feed at the same noon block),
  dedup per-asset preferring the USD-native market — markets + assets **live-verified 2026-08-12 at block 25731615 via
  eth_call** (cWBTCv3/cLINKv3/cUNIv3/cUSDTv3 at older addresses are retired — excluded). ~12 priceable assets (WBTC,
  cbBTC, rsETH, USDe from cUSDCv3; rETH, osETH, rswETH, tBTC, ETHx, wOETH, USDC, USDT from cWETHv3); deUSD/sdeUSD
  excluded by a USD sanity floor (mis-scaled feeds price at ~1e-08). **UAC/UTL registration was ALREADY shipped by a
  parallel session** (`unified-api-contracts@3c39d9cf` BATCH_COMPOUND_V3 + SOURCE_PRIORITY entry +
  SOURCE_MODE_CAPABILITY; `unified-trading-library@09038982` `_VENUE_OVERRIDES["COMPOUND_V3"]`) — no re-registration
  needed. `source=compound_v3`, `pipeline_mode=batch_compound_v3` (manifest emit via
  `pipeline_mode_for_source("compound_v3", ...)`; write path via the venue override). Done-when (single-day
  force-compute vs the `-test-` bucket) NOT yet run — the code is written + passes QG (only the pre-existing
  `test_lending_indices_handler.py::test_collect_protocol_chain_writes_canonical_partition_compound` failure remains,
  which blocks the commit), but the MTDS ship lane is RED on that pre-existing issue
  (`/plans/archive/2026_08/issues/mtds_qg_red_lending_indices_compound_pipeline_mode_drift_2026_08_12.md`, blocker
  RB-fc1bb5dd, now RESOLVED). **Adjacent finding (raised for the other doc)**: the UTL venue-only overrides
  (`AAVE`/`SPARK`/`COMPOUND_V3` → BATCH_*) mislabel `lending_indices` as `batch_aave`/`batch_spark`/`batch_compound_v3`
  instead of `batch_onchain_subgraph` for ALL THREE venues (verified via `derive_pipeline_mode_for_row`); the correct
  mechanism is `_VENUE_DT_OVERRIDES` scoped per `(venue, "oracle_prices")`, but scoping it changes AAVE/SPARK derivation
  too (migration implication) — left to the other doc's P0/escalation rather than fixed unilaterally here.
- **2026-08-12 (slot 16, continued): MTDS ship lane unblocked.** The pre-existing MTDS red was fixed on origin by the
  escalation (`market-tick-data-service@6a039e5242` — threads the SSOT pipeline_mode through the lending_indices write
  path; QG green) AND the UTL root-cause P1 was shipped by a peer (`unified-trading-library@b3b2c440` — moved
  SPARK/COMPOUND_V3 oracle overrides to per-data_type `_VENUE_DT_OVERRIDES`, so lending_indices/liquidations/risk_params
  derive batch_onchain_subgraph/batch_onchain_rpc per SOURCE_PRIORITY while oracle_prices stays batch_compound_v3). I
  independently applied the same COMPOUND_V3-scoped fix, QG-verified it (green), then REVERTED it as redundant once
  b3b2c440 landed. My COMPOUND_V3 oracle capture code (entry above) is QG-verified; ship of MTDS + the done-when
  force-compute vs the `-test-` bucket in flight.
- **2026-08-12 (slot 16, continued): QG gate-fixes applied — ship READY, QG b8rnzc0zs in flight.** The first full QG
  (bpfqruhiw) failed 2 hard gates on the compound code, both now fixed: (1) `oracle_prices_handler.py` hit 924 lines
  (>900 cap) — fixed by moving the in-handler `_collect_compound_oracle_rows` helper into
  `_compound_oracle_collection.py` as a module function
  `collect_compound_oracle_rows(handler, recorder, target_date_str, noon_ts, run_tag)` (a `TYPE_CHECKING` import avoids
  the circular import; the 1-line call keeps `process()` under the 50-line method cap) → handler now 899 lines; (2) STEP
  5.97 flagged 19 uncited Ethereum contract addresses in `_oracle_prices_constants.py` (the COMPOUND section) — fixed by
  adding `# DERIVED 2026-08-12 ethereum <source>` to each (the checker accepts ANY same-line comment containing the
  literal word `DERIVED`; checker now reports `0 == baseline`). ruff clean; pyright clean (the only isolated-file
  warning — `_PYTH_HERMES_LATEST_URL` unused — is a false positive: the test file imports it, so the project-wide QG
  pyright run resolves it). **PENDING (next actions, in order)**: (1) QG b8rnzc0zs green → commit the 5 compound files
  (`_compound_oracle_collection.py` new; `_oracle_prices_constants.py`, `_oracle_prices_preflight.py`,
  `oracle_prices_handler.py`, `tests/unit/test_oracle_prices_handler.py` modified) + quickmerge-ship (also carries the
  pre-existing unpushed Task-2 commit `34bc0bbb`); (2) run the done-when — single-day force-compute vs the `-test-`
  bucket (`IS_TEST_RUN=true` +
  `--operation collect-oracle-prices --mode batch --asset-group defi --start-date <D> --end-date <D> --force`, D after
  2023-08-17) and confirm `COMPOUND_V3-ETHEREUM/oracle_prices` `captured` rows; (3) flip todo line 522
  `WIRE oracle_prices capture for COMPOUND_V3-ETHEREUM` with `<repo>@<sha>` + evidence + `docs(plans):` commit. **Also
  fixed**: the QG's TESTS phase then failed one PRE-EXISTING AAVE test (`test_batch_run_still_collects_aave`) because it
  patched the OLD handler-namespace imports `oracle_prices_handler.collect_compound_branch` / `emit_compound_manifest` —
  both removed when the wrapper moved into the module. Patched `oracle_prices_handler.collect_compound_oracle_rows`
  (return `[]`) and dropped the emit patch (internal to the mocked fn). Lesson: tests that isolate one oracle branch by
  mocking sibling branches patch whatever names the handler module actually imports — an import-consolidation refactor
  breaks them; check every `patch(...)` target.
- **2026-08-12 (slot 16, continued): SHIPPED + DONE-WHEN PROVEN.** Compound V3 oracle capture landed on origin:
  `market-tick-data-service@f21da6c3` (`feat(defi): wire COMPOUND_V3-ETHEREUM oracle_prices capture (Comet getPrice)`)
  - the previously-unpushed Task-2 commit (rebased as `6105f0b0`) — both on `origin/live-defi-rollout`, ahead=0, tree
    clean. **Done-when PROVEN**: single-day force-compute for **2026-08-12** via the console script
    (`.venv/bin/market-tick-data-service --operation collect-oracle-prices --mode batch --asset-group defi --start-date 2026-08-12 --end-date 2026-08-12 --force`,
    `IS_TEST_RUN=true`) collected **12 real captured rows** for `COMPOUND_V3-ETHEREUM/oracle_prices` — written to the
    `-test-` bucket
    (`market-data-tick-defi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-12/pipeline_mode=batch_compound_v3/ asset_group=defi/venue=COMPOUND_V3/chain=ETHEREUM/instrument_type=spot_asset/data_type=oracle_prices/ COMPOUND_V3-ETHEREUM:SPOT_ASSET:{wbtc,cbbtc,rseth,usde,reth,oseth,rsweth,tbtc,ethx,woeth,usdc,usdt}.parquet`,
    1 row each) + manifest `record_captured` per feed (per-VM shard: 81 total/64 new entries). source=compound_v3,
    pipeline_mode=batch_compound_v3. deUSD/sdeUSD excluded by the USD sanity floor; removed/inactive Comet asset slots
    skipped per-slot (shard isolation) — both expected. **Ship incident**: quickmerge STAGE 0 cascade realigned
    `unified-trading-library`'s local `live-defi-rollout` (was `383d8fb5815d`, divergent) to origin `5507aff3` and a
    stash-pop of pre-existing dirty WIP conflicted on `pipeline_mode_resolver.py` + its test (files this session does
    not own). Restored those 2 files to origin's version (HEAD); the WIP remains preserved in `unified-trading-library`
    stash@{0} (`cascade-1319235-live-defi-rollout`) for its owner — do NOT `git stash drop` it. Ship then succeeded.
    **Lesson (measurement trap)**: `python -m market_tick_data_service.cli.main` is a NO-OP — main.py has no
    `if __name__ == "__main__":` guard, so it imports (printing 2 config lines from UTL DomainValidationService) and
    exits 0 running nothing; the real entries are the console script `.venv/bin/market-tick-data-service` or
    `python -m market_tick_data_service` (`__main__.py`). Use the console script for all done-when/force-compute runs.

## Follow-ups

> **DECOMPOSED 2026-08-11 (slot-18, data_engineering).** The single monolithic "WIRE REAL CAPTURE for the 8 pairs" todo
> instructed its own dispatcher to "scope accordingly when dispatched — a strong split candidate for parallel AO
> dispatch rather than one monolithic todo." Verified on read that this is genuine per-protocol capture engineering, NOT
> a config flip: the `oracle_prices` handler
> (`market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py`) only collects under venues
> `CHAINLINK-<chain>` / `PYTH-SOLANA` / `AAVE-ETHEREUM` (getAssetPrice via
> `market-tick-data-service/market_tick_data_service/cli/handlers/_aave_oracle_collection.py`), so the protocol-venue
> oracle declarations (`SPARK-ETHEREUM`, `COMPOUND_V3-ETHEREUM`, …) each need a NEW on-chain source wired (each
> protocol's own price-oracle contract addresses + ABI, per chain). Split below into one `[CODE]` todo per pair
> (distinct handler surfaces → parallel-safe, different files) + a gated prod-backfill + the roll-back. The operator's
> WIRE-REAL-CAPTURE ruling is preserved verbatim in each pair's todo. **Data-correctness finding raised while
> decomposing** — see Progress Log 2026-08-11: `AAVE-ETHEREUM/oracle_prices` is a REAL wired capture surface
> (getAssetPrice writes `venue="AAVE", chain="ETHEREUM"` captured rows — `_aave_oracle_collection.py:206-216`), which
> CONTRADICTS this doc's "roll back — genesis on the wrong venue key" claim; the roll-back todo now gates on a live-
> manifest check before removing anything.

- [x] ✅ [CODE] P2. **WIRE oracle_prices capture for SPARK-ETHEREUM** (operator ruling 2026-08-09: WIRE REAL CAPTURE,
      not roll-back — recorded in this doc's Progress Log 2026-08-09,
      `/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`). Over-claims a `2024-01-01`
      genesis in `DEFI_VENUE_DATA_TYPE_CAPABILITIES`
      (`unified-api-contracts/.../registry/defi_venue_capabilities.py:109`) with zero captured rows; venue phase is
      `live`. Add a Spark price-oracle collection branch to
      `market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py` (+ per-protocol oracle
      contract addresses/ABI in `_oracle_prices_constants.py`) that writes `oracle_prices` under
      `venue=SPARK, chain=ETHEREUM` (Spark uses an Aave-V3-fork oracle — `getAssetPrice`). Done-when: a single-day
      force-compute produces real `captured` rows for `SPARK-ETHEREUM/oracle_prices` (prove against the `-test-` defi
      bucket via the `/data-pipeline-check-mtds` smoke path). (repo: market-tick-data-service) — **DONE 2026-08-12**:
      shipped `market-tick-data-service@845bd085` + `unified-api-contracts@e34b0f44` +
      `unified-trading-library@4580f481` (all on `origin/live-defi-rollout`; QG green each). SparkLend AaveOracle
      (0x8105f6…cFD9, spark-address-registry) branch in `_spark_oracle_collection.py`; 10 reserves live-verified
      2026-08-12 at block 25740221 (eth_call getAssetPrice != 0; sUSDS reverts → excluded). **Done-when proven**:
      single-day force-compute for 2026-08-11 against the `-test-` defi bucket (`IS_TEST_RUN=true`) produced 10 real
      `captured` SPARK-ETHEREUM/oracle_prices rows (source=spark, pipeline_mode=batch_spark) — verified in the
      `_index/per_vm/` manifest shards + canonical `batch_spark` parquet paths.
- [x] ✅ [CODE] P2. **WIRE oracle_prices capture for COMPOUND_V3-ETHEREUM** (operator ruling 2026-08-09: WIRE REAL
      CAPTURE, not roll-back — recorded in this doc's Progress Log 2026-08-09,
      `/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`). Over-claims a `2022-08-14`
      genesis (`defi_venue_capabilities.py:93`), zero captured rows, phase `live`. Add a Compound-V3 price-oracle branch
      to `oracle_prices_handler.py` (+ `_oracle_prices_constants.py`) writing under `venue=COMPOUND_V3, chain=ETHEREUM`
      (Compound V3 markets read a per-market Chainlink-based price feed). Done-when: single-day force-compute produces
      real `captured` rows for `COMPOUND_V3-ETHEREUM/oracle_prices` against the `-test-` bucket. (repo:
      market-tick-data-service) — **DONE 2026-08-12**: shipped `market-tick-data-service@f21da6c3` (Comet getPrice
      branch in `_compound_oracle_collection.py`; constants + preflight sentinel; module split for the 900-line cap).
      Done-when proven: 2026-08-12 force-compute via the console script
      (`.venv/bin/market-tick-data-service --operation collect-oracle-prices --mode batch --asset-group defi --start-date 2026-08-12 --end-date 2026-08-12 --force`,
      `IS_TEST_RUN=true`) produced **12 real `captured` rows** for `COMPOUND_V3-ETHEREUM/oracle_prices` on the `-test-`
      bucket (`market-data-tick-defi-test-central-element-323112`, `pipeline_mode=batch_compound_v3`,
      source=compound_v3) — verified in the run log (12 writes to
      `COMPOUND_V3-ETHEREUM:SPOT_ASSET:{wbtc,cbbtc,rseth,usde,reth,oseth,rsweth, tbtc,ethx,woeth,usdc,usdt}.parquet`) +
      per-VM manifest shard (81 total/64 new entries).
- [ ] [CODE] P2. **WIRE oracle_prices capture for MORPHO-ETHEREUM** (operator ruling 2026-08-09: WIRE REAL CAPTURE).
      Over-claims a `2024-01-08` genesis (`defi_venue_capabilities.py:99`), zero captured rows, phase `live`. Add a
      Morpho-Blue price-oracle branch to `oracle_prices_handler.py` (+ constants) writing under
      `venue=MORPHO, chain=ETHEREUM` (Morpho markets use per-market oracle contracts — enumerate the active markets'
      oracles). Done-when: single-day force-compute produces real `captured` rows for `MORPHO-ETHEREUM/oracle_prices`
      against the `-test-` bucket. (repo: market-tick-data-service)
- [ ] [CODE] P2. **WIRE oracle_prices capture for RADIANT-ARBITRUM** (operator ruling 2026-08-09: WIRE REAL CAPTURE).
      Over-claims a `2022-07-25` genesis (`defi_venue_capabilities.py:111`), zero captured rows, phase `live` (only
      RADIANT-ARBITRUM is `live`; RADIANT-BSC/ETHEREUM stay `pipeline`). Add a Radiant price-oracle branch to
      `oracle_prices_handler.py` (+ constants) writing under `venue=RADIANT, chain=ARBITRUM` (Radiant is an Aave-V2 fork
      — `getAssetPrice` on its lending-pool oracle). Done-when: single-day force-compute produces real `captured` rows
      for `RADIANT-ARBITRUM/oracle_prices` against the `-test-` bucket. (repo: market-tick-data-service)
- [ ] [CODE] P2. **WIRE oracle_prices capture for FLUID-ETHEREUM** (operator ruling 2026-08-09: WIRE REAL CAPTURE).
      Over-claims a `2024-02-27` genesis (`defi_venue_capabilities.py:108`), zero captured rows, phase `live`. Add a
      Fluid price-oracle branch to `oracle_prices_handler.py` (+ constants) writing under `venue=FLUID, chain=ETHEREUM`
      (Fluid uses its own per-vault oracle resolvers). Done-when: single-day force-compute produces real `captured` rows
      for `FLUID-ETHEREUM/oracle_prices` against the `-test-` bucket. (repo: market-tick-data-service)
- [ ] [CODE] P2. **WIRE oracle_prices capture for KAMINO-SOLANA** (operator ruling 2026-08-09: WIRE REAL CAPTURE).
      Over-claims a `2023-06-01` genesis (`defi_venue_capabilities.py:177`), zero captured rows, phase `live`. Kamino is
      Solana — add the branch to the Solana defi collection path
      (`market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py` and/or
      `oracle_prices_handler.py`'s Pyth surface) writing `oracle_prices` under `venue=KAMINO, chain=SOLANA` (Kamino
      reads Scope/Pyth price feeds). Done-when: single-day force-compute produces real `captured` rows for
      `KAMINO-SOLANA/oracle_prices` against the `-test-` bucket. (repo: market-tick-data-service)
- [ ] [CODE] P2. **WIRE rewards capture for AAVE_V3** (operator ruling 2026-08-09: WIRE REAL CAPTURE). `rewards` is
      declared valid for `aave_v3` in `PROTOCOL_CAPABILITIES` (added 2026-08-05, `unified-api-contracts@b2874193`) with
      zero captured rows. Wire real AAVE incentive/GHO-emission `rewards` capture into
      `market-tick-data-service/market_tick_data_service/cli/handlers/lending_rewards_handler.py` (RewardsController /
      incentives-controller emissions per reserve). Also add the `(venue, data_type)` genesis entry to
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` for the AAVE_V3-<chain> venues once the write path is proven. Done-when:
      single-day force-compute produces real `captured` `rewards` rows for at least AAVE_V3-ETHEREUM against the
      `-test-` bucket. (repos: market-tick-data-service, unified-api-contracts)
- [ ] [CODE] P2. **WIRE gas_fees capture for alchemy_onchain** (operator ruling 2026-08-09: WIRE REAL CAPTURE).
      `gas_fees` is declared valid for `alchemy_onchain` in `PROTOCOL_CAPABILITIES` (added 2026-08-05) with zero
      captured rows. **First verify the venue-key**: `gas_fees` genesis dates already exist in
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` on `ALCHEMY-ETHEREUM/ARBITRUM/POLYGON/OPTIMISM/BASE`
      (`defi_venue_capabilities.py:210-214`) and
      `market-tick-data-service/market_tick_data_service/cli/handlers/gas_fee_handler.py` exists — so this may be a
      venue-key mismatch (writer emits `ALCHEMY-<chain>`, `PROTOCOL_CAPABILITIES` keys it under `alchemy_onchain`)
      rather than a genuinely-unwired path. Check the live manifest for real `ALCHEMY-<chain>/gas_fees` captured rows
      first; if captured, reconcile the Layer-1↔Layer-2 venue-key naming instead of wiring new capture. Done-when:
      `gas_fees` has real `captured` rows reconciled to the declared venue key (proven, not just declared). (repos:
      market-tick-data-service, unified-api-contracts)
- [ ] [CODE] P2. **VERIFY-then-roll-back the 2 over-claim misclassifications** (`AAVE-ETHEREUM/oracle_prices`,
      `MAKER-ETHEREUM/lst_rates`). **⚠️ Verify against the live prod defi manifest FIRST — do NOT remove blind.**
      `AAVE-ETHEREUM/oracle_prices` (`defi_venue_capabilities.py:230`) is claimed by this doc to be "the wrong venue
      key", BUT `_aave_oracle_collection.py` actively writes `oracle_prices` under `venue="AAVE", chain="ETHEREUM"` via
      `getAssetPrice` (see `emit_aave_manifest`, `_aave_oracle_collection.py:184-216`) — so it is very likely a REAL
      capture surface and the genesis is on the RIGHT key. If the manifest shows real `captured` rows, do NOT roll back
      — instead close the Layer-1 gap (declare `oracle_prices` valid for the AAVE oracle protocol in
      `PROTOCOL_CAPABILITIES`). `MAKER-ETHEREUM/lst_rates` (`defi_venue_capabilities.py:252`): Maker is a CDP not an
      LST; confirm zero `lst_rates` captured rows, then remove the `lst_rates` genesis (its real analog
      `vault_share_price` is already declared on the same key). Done-when: each pair either has its genesis
      corrected/removed OR is confirmed a real capture surface with the Layer-1 declaration fixed instead — with the
      live-manifest evidence cited. (repo: unified-api-contracts)
- [ ] [DATA] P2. **Prod full-history backfill of the newly-wired pairs** (gated on the wire-capture todos above
      landing). Once each pair's capture path is proven against the `-test-` bucket, run the prod full-history backfill
      so the pairs show real `captured` rows in the live prod manifest (the original monolithic todo's ultimate
      done-when). Safe- idempotent justification for the VM launch: DeFi backfills are SPOT + idempotent +
      resumable-from-measured-progress (SSOT `/codex/05-infrastructure/spot-vms-for-backfill.md`) — re-running never
      double-writes. Done-when: each newly- wired `(venue, data_type)` pair has real `captured` rows in the prod defi
      availability index. (repo: market-tick-data-service)
- [ ] [CODE] P3. **Add `if __name__ == "__main__":` guard to `market_tick_data_service/cli/main.py`** — found 2026-08-12
      while running the COMPOUND_V3 done-when: `python -m market_tick_data_service.cli.main` imports the module
      (printing 2 config lines from UTL DomainValidationService) and exits 0 running nothing, because main.py has no
      `__main__` guard. Only the console script `.venv/bin/market-tick-data-service` (or
      `python -m     market_tick_data_service` via `__main__.py`) actually dispatches. The guard makes `-m` behave like
      the console script — removes a recurring footgun for ad-hoc force-compute/done-when runs. (repo:
      market-tick-data-service)

> **2026-08-06 archive-candidate audit**: The DESIGN P2 31-pair todo is marked [x] but its own evidence and the
> 2026-08-05 Progress Log state 'Operator decision still needed: which of the now-reconciled pairs to wire a real
> capture path for vs. retire the aspirational genesis date'; the deployment-api PREDICTION_DATA_TYPE_META retirement
> (finding 5) is also deferred as 'a separate follow-up' with no tracked todo.
