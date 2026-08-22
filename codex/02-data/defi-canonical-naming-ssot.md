---
doc_type: codex-ssot
title: DeFi canonical naming SSOT (data_type · chain · instrument_type · path · bucket)
summary: >-
  Operator-locked SSOT for the DeFi canonical wire/storage vocabulary — data_type
  (dex_pool_state/dex_pool_swaps/lst_rates/lending_indices/oracle_prices/perp_funding), chain (HYPERLIQUID not
  HYPERLIQUID_L1), instrument_type (incl. perpetual), bare venue + separate chain= path segment, pipeline_mode=
  partition, and the consolidated market-data-tick-defi-prd-{pid} bucket; every writer/reader must converge or the
  surface is review-blocking.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [defi, canonicalisation, pipeline-mode, manifest, data-correctness, ssot-audit, migration]
related:
  [
    /codex/02-data/defi-data-pipeline.md,
    /codex/02-data/defi-data-types-catalog.md,
    /codex/02-data/defi-data-type-taxonomy.md,
    /codex/02-data/pipeline-mode-partition.md,
    ../../plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md,
  ]
created: 2026-06-01
authoritative_for:
  [
    DeFi canonical naming vocabulary,
    DeFi data_type/chain/instrument_type/path/bucket canonical forms,
    on-chain perp CLOB cefi-vs-defi asset_group boundary,
    defi two-id / dual-key model (instrument_id vs canonical_instrument_id),
  ]
referenced_by:
  [
    /codex/02-data/defi-data-pipeline.md,
    /codex/02-data/defi-data-types-catalog.md,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    /codex/04-architecture/solana-defi-coverage.md,
    /codex/04-architecture/token-wrapping-and-collateral.md,
    plans/archive/2026_08/issues/defi_code_codex_drift_2026_05_27.md,
    plans/archive/2026_07/features_service_defi_data_loading_blockers_2026_05_29.md,
    plans/audit/results/defi_c0_datastate_audit_2026_06_01.md,
  ]
owner:
last_reviewed: 2026-07-28
code_refs:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_subgraph.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/defi.py,
    instruments-service/scripts/build_instrument_catalogue.py,
  ]
---

# DeFi canonical naming SSOT (data_type · chain · instrument_type · path · bucket)

> **🟡 WRITE-MODEL SUPERSEDED (operator 2026-07-18) — DeFi → per-instrument (flat pattern #1).** The naming vocabulary
> below (data_type / chain / instrument_type / path / bucket) STANDS. What changes: the leaf file is no longer a
> multi-instrument `{venue}_{chain}_{capture_ts}.parquet` batch — DeFi now shard-writes **ONE parquet per instrument**,
> `{file}` = the symbolic canonical id (`filename == instrument_id == manifest key`), exactly like cefi/tradfi. The
> writer change is a `groupby("instrument_id")` fan-out at `write_defi_rows`; IS owns the per-(venue,chain)
> `available_from`/`available_to` denominator; the historical batch files migrate to per-instrument via a column+row
> UNION (forking `migrate_defi_full_v9_canonical.py`). SSOT: `cross-asset-canonical-target-ssot.md` §1 (pattern #1) +
> `plans/active/defi_consolidated_closeout_2026_07_18.md` § Per-instrument re-architecture (R1–R4). DeFi capture is
> STOPPED pending the writer fix.

> **Status: AUTHORITATIVE (operator-locked 2026-06-01).** This is the single source of truth for the DeFi canonical
> wire/storage vocabulary. The DeFi C0 migration (`migrate_defi_full_v9_canonical.py`) writes to these forms; every
> writer/reader/plan/codex listed below MUST converge on them. A surface that diverges is **review-blocking** (it makes
> migrated data unreadable or splits the SSOT). Provenance: the 2026-06-01 naming-alignment audit (codex +
> instruments-service + MTDS handlers + MDPS/features) caught two regressions (data_type + pipeline_mode) before the
> migration applied; the operator then locked the canonical forms and directed "converge on canonical, fix the
> readers/writers + plans + codex — do not bend the migration to legacy."

## Locked canonical forms

| Axis                                                                     | Canonical value(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Object path**                                                          | `raw_tick_data/by_date/day={D}/pipeline_mode={mode}/asset_group=defi/venue={V}/chain={C}/instrument_type={IT}/data_type={DT}/{file}`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | `pipeline_mode=` IS canonical (operator 2026-06-01), inserted after `day=` — the form `candidate_parquet_paths(pipeline_mode=…)` probes first. `mode` ∈ `batch`/`live`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **data_type** (path + column + manifest + handler const + bucket-domain) | `dex_pool_state` (pools), `dex_pool_swaps` (swaps), `lst_rates`, `lending_indices`, `oracle_prices`, `perp_funding`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | **Collapsed to ONE name everywhere** (operator 2026-06-01). The legacy 2-layer split (on-disk `dex_pool_state` vs manifest `dex_pools`) is RETIRED — `dex_pool_state`/`dex_pool_swaps` are canonical at every layer. (Bucket _name_ stays `dex-pools`/`dex-swaps` — that's a bucket id, not the data_type.) **See "dex_pool_state = EVM + Solana union" below.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **chain**                                                                | `HYPERLIQUID` (not `HYPERLIQUID_L1`), `ETHEREUM`/`ARBITRUM`/`BASE`/`OPTIMISM`/`POLYGON`/`BSC`/`AVALANCHE`/`SOLANA`/`ZKSYNC`/`SCROLL`/`LINEA`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | App-chain perps: `HYPERLIQUID→HYPERLIQUID`, `LIGHTER→ZKSYNC`, `ASTER→BSC`. UAC `ChainKind.HYPERLIQUID_L1.value` MUST resolve to wire `HYPERLIQUID`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **instrument_type**                                                      | `pool` (dex), lending HOLDINGS `a_token`/`debt_token`, `lst`, `spot_asset` (oracle single-asset feed), `spot_pair` (oracle PAIR-denominated feed, e.g. ETH/USD — CHAINLINK + PYTH's `oracle_prices` capability declares `[SPOT_PAIR, SPOT_ASSET]` together, 2026-07-20 catalogue canonicalization; `unified_api_contracts.registry.capability_declarations._defi.PROTOCOL_CAPABILITIES["chainlink"/"pyth"]`; this locked list previously omitted `spot_pair`, which the 2026-08-13 na-eligibility-audit batch13 cross-check flagged as apparent drift against a non-canonical-badged row count — live re-check 2026-08-14 confirmed it is the deliberate, documented oracle-pair type, not drift, corrected here), **`perpetual`** (DeFi DEX-pool perp — GMX was the sole venue here, REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; instrument_type kept for future DEX-pool perp venues) + Solana `solana_amm_pool`/`solana_vault`; market/event lending DATA_TYPES key to `lending` (EVM) / `solana_lending` (Solana) — **PERMANENT** (not interim) | **Lending is two-layer.** HOLDINGS use the **A_TOKEN/DEBT_TOKEN split** — THE SSOT, operator-ruled (IS adapters `@1af1be34`; symbol prefix is **per-protocol, verified against live adapter code 2026-07-26**: `aave_v3`/`spark` mint `A{SYM}`/`DEBT{SYM}` = e.g. `AUSDC`/`DEBTUSDC`; `compound_v3` mints a **different** pair, `C{SYM}`/`BORROW{SYM}` = e.g. `CUSDC`/`BORROWUSDC` — corrected here, the old `aUSDC`/`variableDebtUSDC` phrasing implied a uniform prefix that Compound V3 does not use; isolated-market Morpho/Euler/Fluid/Radiant/Venus/Benqi synthesize `A{coll}-{loan}[-marketId8]`, not a single-reserve symbol). Market/event lending DATA_TYPES (`lending_indices`/`liquidation_events`/`flash_loan_events`/`position_data`/`risk_params`/`liquidations`) key to the market-level `lending` (EVM) / `solana_lending` (Solana) instrument_type — the Wave-B flat-`LENDING`-retire OVER-REACHED (broke 5+ MTDS writers) and was REVERSED (`wn12e7itc`); a second attempt to schedule the retire (session-3, see below) was independently proven unsafe again, for a different reason. **⛔ D2 (2026-07-20) SUPERSEDED — session-3 (2026-07-26, operator present): the physical A_TOKEN/DEBT_TOKEN retire of market/event lending data_types is WON'T-DO, permanently.** `plans/archive/2026_07/defi_lending_writer_retire_prerequisite_2026_07_20.md`'s own investigation (todo 8 handoff) found the flip requires 4 tightly-coupled legs — MTDS writer fan-out, UAC `UNSUPPORTED_BY_DESIGN`, UTL dispatch retarget, **and an instruments-service `expected_unattempted` re-seed** (the EU atom is seeded at the market ADDRESS for the interim model; flipping the writers' atom to per-token ids without an IS re-seed silently regresses EU→captured conversion for ~1.04M rows) — on top of the ~16.7M-row migration that has already been reversed once. Session-3 decided to stop pursuing it: flat `LENDING`/`SOLANA_LENDING` is now the **permanent** form, and canonical A_TOKEN/DEBT_TOKEN → rate lookup goes through **`unified_api_contracts.internal.domain.defi.resolve_lending_underlying`** (pure instrument_key decomposition — no GCS rewrite, no manifest re-key, no IS re-seed; returns the `(protocol, chain, underlying_symbol, rate_field)` needed to look up the existing flat-`LENDING` `lending_indices` row) instead of a physical re-key. Scope: covers `aave_v3`/`spark`/`compound_v3` (the only protocols with both a single-reserve A_TOKEN/DEBT_TOKEN symbol form AND flat-`LENDING` `lending_indices` capture); isolated-market protocols and Morpho return an honest `None` (no join target exists). **DeFi DOES have perps** (operator 2026-06-01): a DEX-pool perp venue is `instrument_type=perpetual` for `asset_group=defi` (on-chain CLOB perps such as Hyperliquid are cefi — see the section below). GMX was the sole DEX-pool perp venue and was REMOVED 2026-07-25 (see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) — no DEX-pool perp venue is currently live. IS `DEFI_ONCHAIN_INSTRUMENT_TYPES` MUST include `PERPETUAL` for any future such venue. |
| **venue**                                                                | bare `venue={PROTOCOL}` (UAC `to_canonical_venue` → `UNISWAP_V3`, `AERODROME_V3`, `TRADER_JOE_V2`, `AAVE_V3`, `LIDO`, …) + separate `chain=`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | NEVER the legacy combined `PROTOCOL-CHAIN` overload in the path; `chain=` is its own segment (per `build_defi_partition_path`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **bucket**                                                               | **CONSOLIDATED `market-data-tick-defi-prd-{pid}`** (data_type lives in the `data_type=` path/column, NOT a separate bucket)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | **CORRECTED 2026-06-21 (operational reality — supersedes the 2026-05-28 dedicated-bucket directive):** the consolidated `market-data-tick-defi-prd-{pid}` is the ONLY defi bucket with a live consolidator (`manifest_consolidator_scheduler.tf` covers it, NOT any `{stem}-prd`) AND the canonical 6.16M-row v9 `_index` (honest-cov source). The 2026-05-28 dedicated `{stem}-prd` migration was never consolidated → operationally incomplete. ALL defi handlers resolve `get_write_bucket_name("market_data", "defi")` (lst_rates mtds@4c85340 + gas_fee/dex_pools/lending_indices/liquidations/oracle_prices/perp_funding/evm_defi/aggregator_route mtds@1c99e5c). Provenance: `plans/active/data_completion_to_100_all_ag_2026_06_21.md` Progress Log 2026-06-21 DEFI lane.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **v9 metadata columns**                                                  | `schema_version=9`, `asset_group=defi`, `pipeline_mode`, `source`, `available_at`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Stamped per row at write/migration time.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

## POOL identity is a two-id / dual-key model (Option A, operator-ruled 2026-07-18)

A DeFi POOL row carries **two, deliberately-divergent** canonical ids — this is the design, not an unresolved gap.
Superseded plan `defi_pool_id_chain_uniqueness_2026_07_18.md` proposed folding `chain` into `instrument_id` directly;
the operator instead ruled for **Option A**, the model actually shipped:

| id                                                                            | value                                                                                                                          | role                                                                                                                                                                                              |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`instrument_id`** (machine key)                                             | `pool_address.lower()` — bare, chain-agnostic, NEVER suffixed                                                                  | The manifest join key + `market_tick_data_service/engine/defi_catalog_reader.py:192`'s content-join key; MTDS independently derives the same bare form at capture time via the same UAC property. |
| **`canonical_instrument_id`** (symbolic key, materialized as `glued_pair_id`) | `<VENUE>-<CHAIN>:POOL:<BASE>-<QUOTE>[-<FEE_BPS>]` (fee glued into the symbol segment with a hyphen, never a 4th colon segment) | The human-readable / UI form — this is where `chain` disambiguates two same-address pools deployed on different chains.                                                                           |

Both ids are produced from one `DefiPoolIdentity` dataclass (`unified_api_contracts/canonical/crosscutting/defi.py`,
built by `build_pool_identity()` or parsed back by `parse_glued_pool_id()`): `.canonical_instrument_id` returns the bare
address, `.glued_pair_id` returns the symbolic form via `glued_venue_prefix(venue, chain)`. **The two properties MUST
keep diverging for POOL rows** — collapsing them (e.g. suffixing `instrument_id` with `@CHAIN`, as a now-reverted
2026-07-08 Balancer patch briefly did) breaks the MTDS join, which expects the bare address.

This is why the 6 known cross-chain pool-address collisions (1 CURVE + 5 BALANCER pool contracts, each deployed on two
chains) are **not bugs**: `instrument_id` colliding across chains is expected under Option A — the two rows are
disambiguated by `canonical_instrument_id`/`glued_pair_id`, not by `instrument_id`. Live-verified 2026-07-26:
`plans/archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md` (archived 2026-07-30, fully closed —
Stage 4/5 trace also completed, see that doc for the full 5-stage verdict).

**Separate, internal-only chain-key**: `instruments-service/scripts/build_instrument_catalogue.py::_aggregate_key` folds
`chain` into the catalogue's own lifecycle-merge key (`pool::{chain}::{pool_address}`) so the two chains' listing
histories don't merge into one lifecycle. This key is internal to the catalogue builder — it is never emitted as
`instrument_id` and is unrelated to the two-id model above; don't conflate the two.

**Known gap this model exposes (open P2, not yet fixed)**: because `instrument_id` is bare by design, any downstream
pre-flight/dedup optimization that keys off `instrument_id` alone (without `chain`) cannot distinguish the two colliding
rows — confirmed live in `market_tick_data_service/engine/orchestrator/__init__.py::_run_preflight_availability_check`
(skip-set keyed `(venue, data_type) → {instrument_id}`, no `chain`) and suspected in
`market_data_processing_service/app/core/orchestration_scanner.py`'s `existing_outputs` dedup set. This can make a
genuinely-uncaptured chain's shard look already-covered and silently skip its re-fetch — a freshness optimization gap,
not a write-path/data-corruption bug. Tracked: same issue doc above, P2 todo "Fix the bare-`instrument_id`-only
pre-flight/dedup keying gap".

## On-chain perp CLOBs are CeFi, NOT DeFi (asset_group boundary — codified 2026-06-25)

On-chain perpetual CLOB exchanges are classified **`asset_group=cefi`** (UAC `VENUE_TO_ASSET_GROUP` /
`VENUES_BY_ASSET_GROUP["cefi"]`), even though they settle on-chain — they trade the perp/hedge leg, not the DeFi
long/stake/lend/AMM leg. **CeFi on-chain perps: `HYPERLIQUID` (HYPERLIQUID), `ASTER` (BSC), `EXTENDED` (STARKNET),
`LIGHTER` (ZKSYNC), `KALSHI_PERP` (chainless), `POLYMARKET_PERP` (POLYGON)** (the latter two added 2026-08-13 per the 2026-08-06 operator
ruling in `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md` — their `perp_funding` capture reroutes to
`asset_group=cefi`, matching the shipped routing fix `market-tick-data-service@2aa23de5`) — each has a cefi
`SourceCapability` (`_cefi.py`) + a cefi venue-launch date + per-CEFI-instrument manifest shape
(`venue, instrument_id, data_type, day`), and rides the **cefi backfill**, not the defi path. **No DeFi perp venue is
currently live** — `GMX` (ARBITRUM/AVALANCHE), the sole DEX-pool-shaped venue in `DEFI_PERP_VENUES`, was REMOVED
2026-07-25 (see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; `DRIFT` + `PACIFICA` were CULLED earlier
— purged from the registry per the 2026-07-16 taxonomy ruling). **2026-06-25 alignment:** the instruments-service
capture path (`engine/orchestrator/defi.py` `_SOLANA_DEFI_VENUES`/`_L2_DEX_PERP_VENUES`) had wrongly enumerated
EXTENDED/PACIFICA/LIGHTER as defi → 1,802 contaminant defi `_index` rows; they were moved to `venue_core._CEFI_VENUES`
(adapters relocated `adapters/defi/`→`adapters/cefi/`) and the contaminant rows purged. SSOT:
`plans/active/instruments_foundation_completeness_2026_06_24.md`.

**Only KALSHI-PERP carries a BLANK `chain` — it is genuinely chainless, not a defect (operator ruling 2026-08-21,
`issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md`, archived).** It's a
CFTC-regulated crypto perpetual exchange with **no underlying blockchain at all** — captured through
`market-tick-data-service`'s DeFi-shaped `perp_funding_handler.py`/`_defi_manifest.py` recorder for implementation
convenience, not because it's chain-bound. That recorder's `_build_row_key` enforces a hard "A4-full" invariant
(every DeFi-family shard carries a non-blank `chain`, `BlankChainError` otherwise) — correct for every genuinely
chain-bound venue, but a category error for KALSHI-PERP. The manifest's real capture history confirms this: 100% of
every real `(venue=KALSHI-PERP, data_type=perp_funding)` row ever recorded carries `chain=""`. The fix
(`market-tick-data-service@f7cdd18b21`) added a small, explicit `_CHAINLESS_VENUES` allowlist to `_build_row_key`.

**CORRECTION, same day (2026-08-21)**: `f7cdd18b21` initially over-generalized this allowlist to
`{"KALSHI-PERP", "POLYMARKET-PERP"}` — wrong. POLYMARKET-PERP settles on-chain on **Polygon** (USDC
deposits/settlement in Polygon smart contracts, confirmed via web research), same "hybrid on-chain-CLOB is still
CeFi" pattern as HYPERLIQUID/ASTER/EXTENDED/LIGHTER, not a chainless venue like KALSHI-PERP. A same-day operator
ruling ("fix all three — Polymarket, Hyperliquid, and Aster") reversed this: POLYMARKET-PERP was removed from
`_CHAINLESS_VENUES` (now `frozenset({"KALSHI-PERP"})` — the only member) and `perp_funding_handler.py`'s
`_chain_map` now stamps `POLYMARKET_PERP → "POLYGON"`. The same ruling also found `onchain_perp_batch_handler.py`
had wrongly blanked HYPERLIQUID's and ASTER's `chain` to `""` for their non-`perp_funding` data_types (a
2026-07-21 restamp cleanup that over-applied the same category error in the other direction) — fixed via
`_REAL_CHAIN_OVERRIDE = {"HYPERLIQUID": "HYPERLIQUID", "ASTER": "BSC"}`; backfills tracked in
`issues/defi_cefi_hyperliquid_perp_funding_manifest_chain_contradiction_2026_08_21.md` and
`issues/mtds_aster_dead_chain_default_and_unverified_instrument_catalogue_field_2026_08_21.md`. **Pattern for a
future chainless CeFi venue piggy-backing on this recorder**: add it to `_CHAINLESS_VENUES` ONLY if it is genuinely
blockchain-free (verify, don't assume from "it's CeFi-classified") — every other CeFi on-chain-perp venue gets its
real chain, never a blank-chain default and never a per-venue hardcoded non-blank workaround stamp.

## `dex_pool_state` = EVM + Solana pool-state UNION under one data_type (CHANGE — operator-noted 2026-06-01)

After the collapse, **`data_type=dex_pool_state` carries BOTH EVM pools and Solana pools under a single name** — it is a
union, not EVM-only:

- **EVM** (Uniswap/Curve/Balancer/Aerodrome/…) → `instrument_type=pool`, columns `price_a`/`price_b`/`fee_rate_bps`/
  `liquidity`/`tvl_usd`/…
- **Solana** (Orca/Raydium/Kamino/…) → `instrument_type=solana_amm_pool` / `solana_vault`, columns
  `sqrt_price`/`tick_spacing`/`token_a_mint`/`vault_type`/`total_shares`/…

The **discriminators are `instrument_type` + `chain`** (+ the superset columns, which co-exist and are null where N/A —
e.g. an EVM cell has `sqrt_price=null`, a Solana cell has `price_a=null`). A consumer that wants only EVM (or only
Solana) pool state filters by `instrument_type`/`chain`, NOT by a separate `data_type`. **Implication for
`solana_defi_legacy_migration`**: its `SOLANA_AMM_POOL`/`SOLANA_VAULT` instrument_types are the discriminator \_within\*
`dex_pool_state` — Solana pools must NOT be re-keyed to a distinct data_type (that would re-split the SSOT). Same logic
for `lending_indices` (EVM `lending` + Solana `solana_lending` instrument_types under one data_type — market/event
lending keying is `LENDING`/`SOLANA_LENDING` **permanently**, NOT the holdings A_TOKEN/DEBT_TOKEN split; the
flat-`LENDING`-retire was reversed once (Wave-B, executed then reverted) — a second attempt (session-3) was
investigated and abandoned before execution, not a second reversal — and is now WON'T-DO — see the instrument_type row above for the
`resolve_lending_underlying` resolver that replaces it, and `issues/canonical_closeout_open_questions_2026_07_18.md` § D
for the superseded history).

## Solana AMM pool SYMBOL grammar — fee/tick-spacing discriminator (CORRECTED 2026-07-24, was bare-symbol)

> **Supersedes the bare `{token_a}-{token_b}` grammar this doc previously implied for Solana AMM pools** (and the stale
> `ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC` example still in `cross-asset-canonical-target-ssot.md` §3 — fix tracked
> alongside this one). The bare form MERGED economically-distinct pools (different fee tiers / tick-spacings sharing one
> token pair — routine for Orca Whirlpools / Raydium CLMM) into a single `instrument_id`/parquet shard via
> `write_defi_rows`'s `groupby("instrument_id")` — confirmed live via Raydium's own API (7/100 sampled top-100 pools
> were duplicate-pair/distinct-`pool_id`, e.g. `WSOL/USDC` had 2 live pools, `AKE/USDC` had 3).

**Writer**: `solana_defi_handler.py::_solana_row_symbol` (kamino/orca/raydium/meteora/lifinity dispatch), fixed
`market-tick-data-service@0d83a8a9`. The SYMBOL segment of `instrument_id`/filename is now
**`{token_a}-{token_b}[-{discriminator}]`**, discriminator resolved by `_pool_fee_discriminator()` with this precedence
(first match wins, against the row's OWN already-captured columns — no new upstream fetch):

1. `TS{tick_spacing}` — Orca `tick_spacing` (most specific).
2. `{fee_rate_bps}BPS` — Orca or Raydium `fee_rate_bps`.
3. `{POOL_TYPE}` (uppercased) — Raydium `pool_type` (Standard/Concentrated label).
4. No discriminator — unchanged bare `{token_a}-{token_b}` when the row carries NONE of the above (currently
   Kamino/Meteora/Lifinity, which don't populate any of these fields yet — matches pre-fix output exactly, no regression
   for those protocols).

Representative canonical ids: `ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC-TS64` (tick-spacing discriminated),
`RAYDIUM-SOLANA:SOLANA_AMM_POOL:SOL-USDC-25BPS` (fee discriminated).

**Scope — this fix does NOT cover the second Solana DEX writer.** `dex_pools_handler.py`'s companion
`_dex_pools_subgraph.py::_collect_solana_dex` (routed via the `collect-dex-pools` CLI op, cron
`uts-prod-mtds-collect-dex-pools-cron`) never resolves a token-pair symbol for Solana at all — `_solana_defi_fetch.py`'s
`fetch_orca`/`fetch_raydium` DO populate `token_a`/`token_b`/`tick_spacing`/`fee_rate_bps` on the row, but
`_collect_solana_dex` never reads them into `symbol`; it always falls back to the bare pool **ADDRESS**
(`row.setdefault("symbol", pool_id_str)`) for both the manifest `record_captured(instrument_id=...)` key and the
`write_defi_rows` parquet file leaf. **Verified 2026-07-24: this is NOT exposed to the same collision bug** — a pool
address is inherently unique per pool, so address-keyed instrument_ids/filenames can never merge two distinct pools. The
gap here is readability (opaque address-named files instead of human-readable symbols), not correctness — no fix
required before that cron resumes on collision grounds. Full writer inventory + cron status:
`plans/active/defi_consolidated_closeout_2026_07_18.md` (`dex_pools_handler.py` todo).

**Manifest impact of the discriminator change**: because the discriminator changes the SYMBOL segment, any pre-existing
`capture_status` cell keyed under the old bare form would need reconciliation against a newly-discriminated cell for the
same underlying pool once captures resume. Measured 2026-07-24 (empirical manifest sample, not reasoned abstractly): the
`uts-prod-mtds-collect-solana-defi-cron` collector — the ONLY writer that ever exercised this symbol path — has been
PAUSED since before this fix shipped, and zero `data_type=dex_pool_state` / `instrument_type=solana_amm_pool` manifest
rows exist for ORCA/RAYDIUM under either form. **Moot today; becomes a real pre-resume reconciliation step only once the
cron resumes and both forms could coexist in the same window.** Full detail:
`plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md` (Solana pool-symbol todo, manifest-impact
sub-item).

## Per-surface alignment status (the fan-out — each is a tracked todo)

| Surface                                                     | Repo                                | Needs                                                                                                                        | Status                                                |
| ----------------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| C0 migration `migrate_defi_full_v9_canonical.py`            | market-tick-data-service            | writes all canonical forms                                                                                                   | ✅ mtds@6a8372b2                                      |
| DeFi handlers `_DATA_TYPE` consts                           | market-tick-data-service            | `dex_pools_handler`→`dex_pool_state`, `dex_swaps_handler`→`dex_pool_swaps`; write `pipeline_mode=` partition                 | ✅ mtds@0a3a7071 (C0-CN2)                             |
| Manifest consolidator + `_PATH_DATA_TYPE`/bucket-domain map | market-tick-data-service / features | drop on-disk→logical `dex_pool_state→dex_pools` remap (now identity)                                                         | ✅ mtds@0a3a7071 + features@dec1b687 (C0-CN3)         |
| features-onchain reader + calculators                       | features-service                    | pipeline_mode-aware reads (pass `pipeline_mode` to `candidate_parquet_paths`); `_PATH_DATA_TYPE` identity                    | ✅ features@dec1b687 (C0-CN4)                         |
| MDPS reader                                                 | market-data-processing-service      | pipeline_mode-aware reads; data_type `dex_pool_state`                                                                        | ✅ mdps@4b9e6e5 (C0-CN5)                              |
| UAC `build_defi_partition_path` + `ChainKind`               | unified-api-contracts               | make `pipeline_mode=` canonical in the builder (not just a probe); `ChainKind.HYPERLIQUID_L1.value='HYPERLIQUID'` (or alias) | ✅ uac@dad96e42 (C0-CN6)                              |
| IS `DEFI_ONCHAIN_INSTRUMENT_TYPES`                          | instruments-service                 | include `PERPETUAL` for DeFi on-chain perps                                                                                  | ✅ verified, IS already produces `perpetual` (C0-CN7) |

> **Status updated 2026-06-02 (slot-2):** all per-surface alignment rows above are SHIPPED on LDR (C0-CN1–8 in
> `defi_manifest_canonicalisation_2026_06_01.md`). The table previously read ☐ TODO — that was stale relative to the
> shipped code. Remaining DeFi-lane work is the OPERATIONAL half (re-dry → apply → RD4 → RD5) + the attribution
> registries (oracle `contract→chain`, lst tokens), tracked in the plan's §C0-RD.

## Sequencing (HARD — prevents the regression the audit caught)

1. **Reader fixes land FIRST** (features + MDPS pipeline_mode-aware; data_type identity) — otherwise consumers reading
   the base `build_defi_partition_path` (no `pipeline_mode=`) won't find migrated data.
2. **Writer fixes land WITH the migration** (handlers write `dex_pool_state`/`dex_pool_swaps` + `pipeline_mode=`) so
   live = batch (identical path).
3. **THEN** the C0 `--apply` migration runs → RD4 completeness+CF gate per bucket → **RD5 delete legacy** per bucket
   (only after that bucket is canonical + readers proven on it).

Applying the migration before the reader fixes would write data the live consumers can't read = the exact "fake
buckets/paths to fit code" regression this SSOT prevents.

## Cross-plan

- `plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md` §C/C2 + C0-RD — the migration owner (this codex
  is its naming SSOT).
- `plans/active/pipeline_mode_partition_migration_2026_06_01.md` — owns making `pipeline_mode=` canonical in the
  writer/reader (lands WITH C0, not after).
- `plans/archive/2026_07/solana_defi_legacy_migration_2026_05_27.md` — dedicated-bucket directive; uses
  `dex_pool_state`.
- `plans/archive/2026_07/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` — owns the legacy DELETE (RD5),
  gated per-AG on C-GREEN.

## DeFi data-pipeline DURABLE gotchas (codified 2026-06-21 — root causes that kept defi MTDS stuck at 6% honest-cov)

These are reader/writer + seeding contracts an agent MUST honour; each was a multi-hour root-cause hunt. Read before
touching defi MTDS capture / honest-cov.

1. **Instruments preflight reader ↔ writer bucket MISMATCH (env-less vs `-prd-`).** The MTDS DeFi capture preflight
   `assert_defi_catalog_fresh` → `run_preflight(DEFI_COLLECT_DAILY)` resolves its bucket via
   `_defi_manifest.build_bucket("instruments", asset_group="defi")` → **`instruments-store-defi-{pid}` (env-LESS
   legacy)**. But every WRITER (IS instruments backfill, `build_instrument_catalogue` roll-up, the instruments
   consolidator) writes **`instruments-store-defi-prd-{pid}` (env-SHORT canonical)**. So the reader reads a stale/empty
   legacy index → catalog preflight `age=None` → handlers route honest-absence → **zero capture**. FIX (durable): align
   the reader to canonical `-prd-` (or write both). Stop-gap: `gcs_copy_object` the fresh `-prd-`
   `_index/availability_index.parquet` → the env-less bucket (valid ≤24h per the staleness window). Same
   env-less-vs-`-prd-` class as the market-data bucket bug.
2. **Consolidated-index staleness default (120s) is FAR too short for a DAILY reference catalog.**
   `read_availability_index` (`manifest_writer/_read_index.py`) checks the consolidated blob's GCS `updated` vs
   `MANIFEST_CONSOLIDATED_STALENESS_SEC` (default **120s**); if older AND per-VM shards exist it FALLS BACK to merging
   per-VM shards. For the daily instrument catalog the consolidated blob is minutes-to-hours old in normal operation →
   it ALWAYS fell back to per-VM shards, which carry **pre-canonicalisation columns (blank `data_type`)** → the
   `data_type='instrument-catalog'` filter matched 0 rows → `age=None`. FIX: defi MTDS launchers pass
   **`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`** (24h — a daily catalog is fresh for 24h) so the reader trusts the
   consolidated index. `setup-data-pipeline-vm.sh` already propagates the metadata.
3. **`expected_unattempted` MUST be seeded in CANONICAL venue/chain or captures NEVER convert it.** The IS
   expected-universe enumerator (`enumerate_expected_universe.py` / `expected-universe-v2-defi`) seeded defi
   `expected_unattempted` with the LEGACY combined `venue=PROTOCOL-CHAIN`, `chain=''`. Handlers CAPTURE canonical
   `venue=PROTOCOL` + separate `chain=X` (this SSOT). Different shard keys → captures create NEW rows, the legacy
   unattempted persist → honest-cov flat at ~6% despite real data flowing. The enumerator/seeder MUST emit the canonical
   venue/chain split (this SSOT applies to the SEEDER, not only the migration + handlers).
4. **NEVER call a synchronous GCS read inside an `async def` handler.** `ManifestFreshnessCache.bulk_load()` /
   `assert_defi_catalog_fresh` do blocking GCS I/O; called directly in async handler code they block the event loop →
   the 120s log-uploader heartbeat starves → the VM LOOKS hung (no log progress) though it's alive. Wrap in
   `await asyncio.to_thread(...)`. And `assert_defi_catalog_fresh` is **keyword-only**
   (`*, project_id, on_date, correlation_id`) — wrap as
   `asyncio.to_thread(lambda: assert_defi_catalog_fresh(project_id=…, on_date=…, correlation_id=…))`, never positional
   (positional → `takes 0 positional arguments but 3 were given`).
5. **DeFi DEX subgraph handlers MUST shard across the 9-key TheGraph pool.** `thegraph-api-key` +
   `thegraph-api-key-2..9` exist in Secret Manager for sharding; `TheGraphBaseClient` has round-robin but
   `dex_pools_handler`/`dex_swaps_handler` hand-rolled a SINGLE key → all DEX VMs collided on key #1. Use the
   round-robin pool (per-request) — not a single key.
6. **Catalogue rollup MUST key `venue_day_counts` on the CANONICAL venue (2026-06-27).** `build_catalogue_dataframe`
   accumulates per-(venue, day) instrument counts for the §7.3 thin-day-aware liveness window. If keyed on the RAW
   snapshot venue (e.g. `PANCAKESWAPV3-BSC`), old ghost venues generate a separate, tiny window ending May 8 — every
   pool that last appeared on that ghost venue's last full day gets `available_to=None` (false-active, the +73
   PANCAKESWAP_V3-BSC discrepancy). FIX: `venue_day_counts` is keyed via `canonicalize_defi_venue_combined(raw_venue)`
   so ghost and canonical forms share ONE liveness window. When looking up `venue_last_full`, the aggregate's meta venue
   is also canonicalised before the dict lookup. Provenance: `instruments-service@50308e0`
   (`fix(catalogue): collapse defi ghost dual-keys …`).
7. **Non-pool DeFi instrument_ids with ghost venue prefixes create dual catalogue rows (2026-06-27).** DeFi lending rows
   (AAVE_V3 / COMPOUND_V3) have `instrument_key=VENUE-CHAIN:TYPE:SYMBOL`. When the IS adapter switched from the
   no-underscore ghost form (`AAVEV3-ARBITRUM`) to canonical (`AAVE_V3-ARBITRUM`) around 2026-05-08, the same logical
   market appears under two `instrument_key`s → two catalogue rows (the +171 AAVE_V3 / +26 COMPOUND_V3 triad
   discrepancy). POOL rows are already protected by the pool-address agg_key collapse. Non-pool rows are fixed by
   `_canonical_instrument_id()` in `_aggregate_key`: the venue-prefix portion (before the first `:`) is normalised via
   `canonicalize_defi_venue_combined` so ghost-keyed rows collapse onto the canonical aggregate key. Provenance:
   `instruments-service@50308e0`.
8. **`canonical_path_violations` was ORDER-blind — a live-only second writer diverged from the batch shape for ~1 month,
   undetected (2026-06-26 → 2026-07-22).** The oracle parsed partition segments into a `key→value` dict, so it validated
   segment PRESENCE/VALUES but never their SEQUENCE.
   `market_tick_data_service.live.websocket_runner. live_tick_blob_path` (the LIVE DeFi write-time path) spliced
   `chain=` in front of `venue=` for every non-cefi asset_group, landing DeFi live writes at
   `asset_group=defi/chain={C}/venue={V}/...` — the reverse of the canonical batch shape (`build_defi_partition_path`:
   `venue={V}/chain={C}/...`) — for the SAME shard. A hand-built reversed-order path proved the oracle returned the
   IDENTICAL violation list as the correct order. FIX: `live_tick_blob_path` reordered to venue-before-chain
   (`mtds@0fcfa803`); `canonical_path_violations` gained a defi-scoped structural check for venue-before-chain order +
   lowercase `instrument_type` + `pipeline_mode=` position immediately after `day=` (`unified-api-contracts`, blocked on
   an unrelated pre-existing QG gate as of 2026-07-22 — see `plans/active/defi_consolidated_closeout_2026_07_18.md`
   Track 2). DeFi live crons are currently PAUSED, so no bad data is known to have landed in prod from this — a pure
   code-path divergence, not a manifested capture defect.

   **Second, independent occurrence found 2026-07-28 (READER side, not the writer above):**
   `market_tick_data_service.reader.CanonicalParquetReader._build_shard_bases` (`_make_base`, ~`reader.py:367-373`) had
   the SAME reversed order on the READ path — `asset_group=defi/chain={C}/venue={V}/...` vs. the canonical
   `venue={V}/chain={C}/...`. Dormant (no live caller passes `chain=` for a DeFi read), but a landmine on a public
   method. Fixed segment order in `_make_base` + the module docstring (`reader.py:26-28`) + the `TestDefiChainAxis`
   unit-test contract's hardcoded mock paths (`tests/market_interface/unit/test_canonical_parquet_reader.py`,
   `TestDefiChainAxis` class), which had asserted the wrong order and would otherwise have locked in the bug. See
   `/plans/archive/issues/gcs_path_resolution_centralization_audit_2026_07_28.md`.
