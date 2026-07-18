---
doc_type: plan
title:
  DeFi consolidated close-out — one ordered pass (canonical target → residual canon walk → denominator → coverage →
  forward) mirroring the cefi/tradfi close-outs
summary:
  Single coordination plan that AGGREGATES (references, does NOT duplicate) every open defi + defi-touching IS/MTDS
  plan/issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md /
  tradfi_consolidated_closeout_2026_07_18.md. Authored 2026-07-18 from a 6-agent audit (7 active defi plans + ~35 issues
  + live GCS bucket audit + live manifest distinct-values query) plus direct operator rulings. UNLIKE cefi/tradfi the
  DeFi FOUNDATIONAL migration already ran (canonical-migration-defi-20260618-180603 → v9 + asset_group=defi +
  pipeline_mode + source; dedicated→shared bucket consolidation done) — so what remains is a RESIDUAL canon walk, a
  now-RESOLVED POOL-id policy, a large genuinely-open coverage/denominator effort, a culled-venue purge, and restoring
  the removed data-status enumeration view. The operator-decided canonical target (id grammar, SPOT_ASSET vs SPOT_PAIR
  vs POOL, the two-id model, empty_confirmed vs out-of-scope) is captured here as the target; the actual code+data
  changes are THIS plan's scope (cefi/tradfi findings are passed to their sibling plans).
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    defi,
    close-out,
    consolidation,
    canonicalisation,
    instrument-id,
    pool,
    lending,
    spot-asset,
    manifest,
    empty-confirmed,
    denominator,
    coverage,
    backfill,
    bucket,
    enumeration,
    venue-purge,
  ]
related:
  [
    cefi_consolidated_closeout_2026_07_18.md,
    tradfi_consolidated_closeout_2026_07_18.md,
    data_completion_defi_2026_07_15.md,
    defi_dedicated_bucket_shared_migration_2026_07_13.md,
    defi_onchain_derivable_values_and_date_drift_2026_06_20.md,
    defi_pipeline_e2e_and_coverage_validation_2026_06_20.md,
    mtds_defi_dex_zero_capture_protocols_2026_07_14.md,
    mvp_backfill_defi_onchain_v10_2026_06_27.md,
    master_to_live_defi_2026_05_23.md,
    canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Operator, 2026-07-18 — after directing the cefi + tradfi consolidated close-outs, asked for the same one-pass DeFi
  close-out that aggregates ALL defi IS/MTDS plans+issues, audits the GCS buckets for the canonical path, states the
  canonical target (paths, instrument uids) from buckets+UAC+code+plans, defines the empty_confirmed vs out-of-scope
  basis, and reconciles SPOT_ASSET vs SPOT_PAIR vs POOL — reconciled in code AND backfilled data AND forward data.
  Authored + ground-truth-verified from a 6-agent audit (slot-4, 2026-07-18) with live GCS reads + operator rulings.
---

# DeFi consolidated close-out — one pass to canonical, honestly-covered, forward-clean

> **Purpose.** ONE place that aggregates every open defi + defi-touching IS/MTDS plan/issue into a single ordered pass.
> This plan **references** the source docs; it does not duplicate them. Close a track by closing its source doc(s), then
> tick it here. Mirrors the cefi/tradfi consolidated close-outs. **Ownership (operator 2026-07-18)**: THIS plan is the
> target for the actual DeFi code + data changes; the audit's cefi/tradfi findings + operator decisions are passed to
> the two sibling plans.

## Headline verdict — how DeFi differs from cefi/tradfi

- **The DeFi FOUNDATIONAL migration already ran.** `canonical-migration-defi-20260618-180603` (C0d in
  `data_completion_defi_2026_07_15.md`) took every DeFi object to v9 + `asset_group=defi` + `pipeline_mode=` + a
  `source` column; the dedicated→shared bucket consolidation (`defi_dedicated_bucket_shared_migration_2026_07_13.md`) is
  done (all kinds resolve `kind="tick-data"` on the single `market-data-tick-defi-prd-central-element-323112`). So the
  cefi/tradfi "0% canonical, migrate everything" starting point does NOT apply.
- **What remains is different in kind:** (1) a RESIDUAL canon walk the big migration didn't finish (C2–C12); (2) a
  now-RESOLVED POOL-id policy contradiction; (3) a culled-venue purge; (4) a large genuinely-open coverage/denominator
  effort (the ~63.9M `expected_unattempted` seed, the DRIFT/Velocity backfill, Morpho never wired, a dead Curve/Optimism
  subgraph); (5) restoring the removed data-status "what exists" enumeration view. DeFi's biggest open track is
  **coverage**, not id-canonicalisation.

## Per-instrument re-architecture (operator 2026-07-18 — SUPERSEDES the batch-model tracks; DeFi capture STOPPED)

> **🟡 In-flight refactor + capture halted.** All DeFi capture was STOPPED 2026-07-18 (2 GCP forward-poll VMs
> `defi-fwd-{dex-pools,oracle-prices}-poll` + 5 `uts-prod-mtds-collect-*defi*` / `defi-fwd-oracle-prices-prd` schedulers
> paused; AWS clear; **IS enum/catalogue crons LEFT RUNNING** — IS remains the availability source). DeFi is being
> re-architected to shard-write ONE parquet per instrument (like cefi/tradfi), collapsing SSOT §1 pattern #4 → pattern
> #1. This is the target; the batch-model column/path framing in the tracks below is superseded. Grounded in code
> (workflow `wf_20749dad`).

**Why**: MTDS wrote an arbitrary bunch of instruments per capture into one `{venue}_{chain}_{capture_ts}.parquet` batch,
blank manifest `instrument_id`, multiple batch files per shard-day — the root cause of the manifest/data-status pain +
the duplicate/phantom rows. Fix = **fetch bulk, write per-instrument** (the id is already stamped on every row).

**Confirmed decisions (operator 2026-07-18)**: (1) shard key = the **symbolic `canonical_instrument_id`**
(human-readable filename `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC.parquet`; address = a content column + IS-def/join key); (2)
**per-(instrument, day)** granularity, matching cefi/tradfi; (3) IS owns availability with **`available_from`**
(on-chain genesis) + **`available_to`** (TVL-drop delist) → out-of-window = out-of-scope, in-window + 0 rows =
`empty_confirmed`.

### R1 — Writer: per-instrument fan-out (forward-write) · P0

- [ ] [BACKEND] P0. **`write_defi_rows` (`market_interface/adapters/defi/canonical_write.py:103-296`) fans out**: after
      per-row `instrument_id` enrichment, `df.groupby("instrument_id")` → return a LIST of `(group_df, path)`, each leaf
      `{sanitized_symbol}.parquet` via `build_defi_partition_path(..., file_name=…)` (already accepts `file_name`, no
      builder change). `_write_and_upload` (`cli/handlers/evm_defi_collectors.py:36-68`) loops the upload. **6/7
      handlers already emit per-instrument manifest rows** (dex_pools / dex_swaps / oracle_prices / risk_params /
      lending_indices / lst_rates) — only **`evm_defi`** (bundle-on-both-axes, blank `instrument_id`) needs its single
      bundle `record_captured` replaced with a per-`instrument_id` loop. Resolve `lending`→`A_TOKEN`/`DEBT_TOKEN` BEFORE
      grouping. The sanitizer `[/\\:\s]→_` MUST match R3's so migrated + live objects collide on one key. (repo:
      market-tick-data-service)

### R2 — IS: the honest per-(venue,chain) availability denominator · P0

- [ ] [BACKEND] P0. **IS is structurally already the denominator** (`enumerate_expected_universe.py::_enumerate_v2_defi`
      seeds `expected` per `(venue,chain,itype,instrument_id,data_type,day)`; `available_from` STRONG via real on-chain
      genesis `eth_getCode` binary-search). Close the gaps: **(a) honest `available_to`** — record per-instrument
      TVL-over-time as a first-class attribute + derive `EXPECTED_INSTRUMENT_DELISTED` from a real threshold-crossing
      date (decouple from the top-6000 fetch-ranking) and **relax the `min_ratio=1.0` monotonicity guard**
      (`defi.py:190-214`) so real delistings aren't suppressed; **(b) add `force_include=true`** (TVL-exempt) so
      EIGEN/ETHFI/governance carry honestly vs coincidental liquidity; **(c) extend the catalogue-residual
      empty-reconciliation** (`dex_pools_handler.py:750+` `record_catalogue_residual_empty`) to
      evm_defi/lending/oracle/lst so an IS-listed-but-unfetched instrument becomes a per-instrument
      `EXPECTED_*`/`empty_confirmed`, never a dangling `expected_unattempted`. Keep the per-protocol data_type narrowing
      (stops over-seeding). (repo: instruments-service)

### R3 — Historical migration: batch → per-instrument, column+row UNION · P0 (gated on R1+R2)

- [ ] [DATA] P0. **Fork `migrate_defi_full_v9_canonical`** — cell grain `(venue,chain,day)` → `(instrument_id,day)` and
      **replace winner-pick with column+row UNION** (a sparse RPC-fallback batch may hold columns a fat batch lacks;
      max-rows-wins silently drops schema — THIS is why target=UNION, not winner-pick). Reuse verbatim: single-walk
      `_list_objects`, footer-only `discover_union` + baked `_CANONICAL_UNION`, the LOUD-FAIL `_conform` guard.
      Per-column canonical resolution (coalesce name-drift old→new; `resolve_pool_symbol` 3-tier id;
      venue/chain/instrument_type). Dedupe rows on the natural event key (swaps `tx_hash`; state `block_number`; oracle
      `round_id`), keep the most-populated/canonical. Unresolvable → `_needs_attribution/` (never drop). DRY-RUN
      default. Write `{sanitized_symbol}.parquet` into the same `day=…/data_type=…` partition; then
      `rebuild_defi_manifest` re-derives `instrument_id=stem` via `parse_hive_path` → per-instrument manifest by
      construction. (repo: market-tick-data-service)

### R4 — Coverage against the IS denominator · P1 (gated on R1+R2+R3) → then RESUME capture

- [ ] [DATA] P1. **Score coverage per-instrument** against the IS `available_from/to` window; the ~1.04M stuck
      `expected_unattempted` / false `EXPECTED_INSTRUMENT_DELISTED` rows resolve once the seed (R2) + migrated
      per-instrument manifest (R3) exist with byte-matching keys. A RED DeFi data audit here FREEZES downstream
      (foundation-gate). Then **RESUME the stopped DeFi capture VMs/crons** on the corrected writer.

**Sequencing**: R1+R2 (ship together — new days land per-instrument + reconcile) → R3 (migrate history to the identical
layout) → R4 (coverage) → resume capture. **This SUPERSEDES the batch-model column/path work in the tracks below** — the
column migrations (id/address/lending-split, case, venue-spelling) still happen, but folded into R1/R3, not a separate
cell-grain rewrite. `consolidate_multi_parquet_per_day` winner-pick is RETIRED for DeFi. **Small-files (per-DAY is
bounded by TVL — a non-issue)**: the IS catalogue holds **11,724 valid instruments total** (POOL 7,224 · SPOT_ASSET
1,389 · A_TOKEN 1,117 + DEBT_TOKEN 1,060 · legacy LENDING 892 · GMX PERPETUAL 33 · LST/STAKING ~7 · SPOT_PAIR 2) across
66 (venue,chain) shards, so a day writes **~11.7k tick files max** — the TVL filter is doing its job (measured
2026-07-18, `instruments-store-defi-prd/prod/catalog.parquet`). The only mild concern is the **CUMULATIVE** object count
over the full backfill (~11.7k × days × data_types ≈ a few million tiny objects) — same shape as cefi/tradfi; a
per-instrument-MONTH compaction is a recommended SEPARATE follow-up ONLY if the total object count bites (keeps the
shared `day=` hive). **This is MTDS tick-data only** — IS stays the per-(venue,chain) availability BUNDLE (all
instruments in one `instruments.parquet` with `available_from/to`).

## Canonical target (operator-decided 2026-07-18 — the thing we converge all four surfaces on)

The four surfaces that must agree post-migration: **(1) GCS parquet path**, **(2) parquet
`instrument_id`/`canonical_instrument_id` columns**, **(3) manifest `_index` key**, **(4) data-status render**. For DeFi
**TARGET (operator 2026-07-18): DeFi is FLAT-PER-INSTRUMENT** — one parquet per instrument, filename = the symbolic
canonical id (`filename == instrument_id == manifest key`), exactly like cefi/tradfi. The old multi-instrument
capture-batch (`{venue}_{CHAIN}_{capture_ts}.parquet`) model is **RETIRED** — see the "Per-instrument re-architecture"
section above. The address stays a content column + the IS-definition/join key.

### Path template (operator-locked; forward writer already emits it)

```
gs://market-data-tick-defi-{prd|test}-central-element-323112/raw_tick_data/by_date/day={YYYY-MM-DD}/
  pipeline_mode={mode}_{source}/asset_group=defi/venue={PROTOCOL}/chain={CHAIN}/
  instrument_type={itype_lower}/data_type={dt}/{leaf}.parquet
```

Segment order is **venue BEFORE chain** (locked in `codex/02-data/defi-canonical-naming-ssot.md`; the code + live GCS
confirm it — `per-asset-group-bucket-layouts.md` and `GCS_PATHS.md` are STALE the other way and must be corrected).
`instrument_type` in the PATH is lowercase.

### Instrument-uid grammar per DeFi type (real `build_canonical_instrument_id` output; UPPER type-segment, case-PRESERVED symbol)

Base = `VENUE-CHAIN:TYPE:SYMBOL` (DeFi is the only AG whose venue segment carries a `-CHAIN` suffix; on-chain token case
is preserved — `aUSDC`, `stETH`).

| type                                    | grammar                                                                                                        | example                                                                         |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `SPOT_ASSET`                            | `VENUE-CHAIN:SPOT_ASSET:SYM`                                                                                   | `UNISWAP_V3-ETHEREUM:SPOT_ASSET:WETH`                                           |
| `POOL`                                  | `VENUE-CHAIN:POOL:TOKEN0-TOKEN1[-FEE_BPS]` — **3-segment, fee INSIDE the symbol (operator ruling 2026-07-18)** | `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`                                        |
| `A_TOKEN` / `DEBT_TOKEN`                | supply / borrow leg (isolated markets append `marketId[:8]`)                                                   | `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC` · `MORPHO-BASE:A_TOKEN:AUSDC-EURC-<marketId8>` |
| `LST` / `YIELD_BEARING` / `STAKING`     | staking token / vault share                                                                                    | `LIDO-ETHEREUM:LST:stETH` · `ETHENA-ETHEREUM:YIELD_BEARING:sUSDe`               |
| `PERPETUAL` (on-chain, DeFi lane = GMX) | `VENUE:PERPETUAL:SYM` — **NO chain suffix** (routes cefi-simple branch)                                        | `GMX:PERPETUAL:BTC-USD`                                                         |
| `SOLANA_AMM_POOL` / `SOLANA_LENDING`    | Solana grains                                                                                                  | `ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC`                                          |

### The two-id model (operator ruling 2026-07-18 — "that's fine as long as downstream uses what it needs the right way")

Every address-identified DeFi row carries TWO ids and this is INTENTIONAL — **do NOT mass-rewrite the 22.3M
address-keyed rows**:

- **`canonical_instrument_id` (the canonical/human id)** = the symbolic `VENUE-CHAIN:TYPE:SYMBOL` above. Carries the
  instrument_type; carries NO raw addresses. This is the operator's "type-in-id, symbol-in-id, addresses live in the
  definition" ruling.
- **`instrument_id` (the machine/operational key)** = the address-anchored form (POOL→`pool_address.lower()`,
  SPOT_ASSET→`spot_asset:{chain}:{token_addr}`). Used as the manifest join key + MTDS content-join. The pool/token
  CONTRACT ADDRESS lives HERE and in the instrument DEFINITION (catalogue) — NEVER inside the canonical id.
- **POOL-id policy = Option A (test wins)**: POOL rows legitimately DIVERGE (`instrument_id`=address,
  `canonical_instrument_id`=symbolic key). For SPOT_ASSET the two CONVERGE by construction. Fix the backfill-script
  docstring that wrongly asserts convergence "pool or not"; ensure every consumer reads the RIGHT one (join→address,
  display/canonical→symbolic).

### SPOT_ASSET vs SPOT_PAIR vs POOL — the decision rule

1. CeFi order-book two-token quoted market (or any two-token quoted price) → **`SPOT_PAIR`** (asset_group=cefi, no
   chain).
2. A single on-chain token you want oracle-price / transfers / gas / bridge / gov / MEV data for → **`SPOT_ASSET`**
   (defi, address-keyed; `canonical_instrument_id := instrument_id` so the two CONVERGE). Carries the
   `DEFI_SPOT_ASSET_*` data_types.
3. An AMM/DEX liquidity-pool contract (two legs + fee + pool address) → **`POOL`** (defi, pool-address-keyed; DIVERGE).
   Its two legs are each individually a `SPOT_ASSET`; the pool is a distinct instrument. Solana spot-DEX
   orderbook/quote/per-swap shards use **`DEX_POOL`**/`SOLANA_AMM_POOL`.

### Lending — ONE SSOT (operator ruling 2026-07-18)

`A_TOKEN` (supply) + `DEBT_TOKEN` (borrow) IS the canonical split (net_value = supply − borrow needs both legs). The
legacy flat **`LENDING`** type is retired: its ~16.7M enumerated rows migrate to the split, and the split is baked into
`build_instrument_catalogue.py` row-construction (not a catalog-only patch a `--mode full` rebuild reverts). The
enumeration audit's stray "fold a_token→lending" is BACKWARD — a_token/debt_token are canonical; `lending` migrates.

### empty_confirmed vs out-of-scope (the denominator basis)

Discriminator = **does a manifest row exist**.

- **`empty_confirmed`** — a cell INSIDE the could-exist universe, attempted, source PROVABLY returned 0 rows (typed
  `EmptyConfirmedReason` + `FetchEvidence` or UTL hard-raises `UnprovenHonestAbsenceError`). A materialized row
  (`row_count=0`, blank id). **EXCLUDED from `reachable_coverage`, RETAINED in `all_shards`.** Stays visible. DeFi-legit
  reasons only: `EXPECTED_PRE_GENESIS_CHAIN`, `EXPECTED_PRE_VENUE_LAUNCH`, `EXPECTED_PROTOCOL_PAUSED`,
  `EXPECTED_INSTRUMENT_NOT_LISTED/DELISTED`, `SOURCE_RETURNED_ZERO`, proposed `EXPECTED_SUBGRAPH_DEINDEXED`
  (Curve/Optimism). An instrument-day source-zero on an ALIVE day = `attempted_failed`, NOT silent empty.
- **out-of-scope** — a `(venue, itype, data_type)` tuple that should NEVER generate → **NO manifest row**
  (`ExpectedState.NOT_IN_SCOPE` / `is_valid_shard_key=False` / `is_mvp()=False`). **Clipped from BOTH numerator and
  denominator.** Removed venues leave the registries entirely.
- **The trap (why the denominator lies today):** ~63.9M could-exist cells were never materialized as
  `expected_unattempted` by the writer → no row → they silently masquerade as out-of-scope and UNDERSTATE the
  denominator. Honest only after a fresh single-walk seeds them (gated on the phantom+duplicate purge first).

## Operator decisions applied (2026-07-18)

- **POOL canonical key = 3-segment, fee inside symbol** (`UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`) — the
  `canonical_id_builder` SSOT form, not the 4-segment `DefiPoolIdentity.glued_pair_id` (`…:POOL:USDC-WETH:500`). The
  4-segment form is retired.
- **Two-id model kept** (Option A) — no mass address→symbol rewrite; ensure symbolic `canonical_instrument_id` coexists
  on every row + downstream reads the right id.
- **Retire legacy `LENDING`** → migrate ~16.7M rows to the A_TOKEN/DEBT_TOKEN split + bake into the catalogue builder.
- **instrument_type case**: lowercase in the PATH + manifest COLUMN (writer grain), UPPER stays only in the id SEGMENT.
- **Culled-venue purge = dead-only, snapshot-first, keep LIGHTER + EXTENDED** (see Track 7).
- **Combos = leg-aware signed-weight spec** (cross-AG) — see Track 1 + the cefi/tradfi hand-offs.
- **Restore the removed data-status enumeration** (raw distinct-values audit view) — Track 6.

---

## Track 1 — CANON: instrument-id + residual walk (⛔ gates Half-B historical canonicalisation) · P0

- **Sources**: `data_completion_defi_2026_07_15.md` (C2–C12),
  `issues/defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md`,
  `issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` (RESOLVED code; durability + legacy-row
  migration open), `issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`,
  `issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`.
- **Close-out criterion**: all four surfaces agree for POOL / SPOT_ASSET / perp / lending rows; the POOL policy is
  pinned by one authoritative test; C2–C12 idempotency-clean.

- [ ] [BACKEND] P0. **Fix the POOL-id policy contradiction (Option A).** Correct the
      `backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py` docstring (POOL carve-out), verify the CODE path
      doesn't enforce convergence on POOL rows, and add ONE pinning test that POOL rows diverge
      (`instrument_id`=pool_address, `canonical_instrument_id`=3-segment glued key). Retire the 4-segment
      `DefiPoolIdentity.glued_pair_id` form → 3-segment. (repos: instruments-service, unified-api-contracts)
- [ ] [DATA] P0. **Retire legacy `LENDING` → A_TOKEN/DEBT_TOKEN.** Migrate the ~16.7M `lending` rows to the split (code
      done for 9 EVM protocols) AND bake the split into `build_instrument_catalogue.py` row-construction so a
      `--mode full` rebuild can't revert it (kills the 2026-07-14 durability landmine). (repos: instruments-service)
- [ ] [DATA] P0. **Residual canon walk C2–C12** (single-walk discipline — reuse the existing worklist, no NEW
      whole-corpus walk): C2 data_type alias dedup (`dex_swaps`→`dex_pool_swaps`, `dex_pools`→`dex_pool_state`,
      `lending-indices`→`lending_indices`, `staking_yields`→`lst_rates`); C3 `VENUE-CHAIN`→flat venue + `chain`; C4
      v4–v8→v9; C9 object paths still carrying `category=`/no `pipeline_mode=`; C11 phantom walk; C12 `{VENUE}_V{N}`
      underscore canonicalisation (`TRADER_JOE_V2`/`VELODROME_V2`/`AERODROME_V3`). (repos: market-tick-data-service,
      instruments-service)
- [ ] [DATA] P0. **Manifest instrument_type case + venue-spelling unify** (from the live distinct-values audit):
      case-fold the manifest `instrument_type` column to lowercase (`POOL`→`pool` 13,868 · `LENDING`→`lending` 179,164 ·
      `PERPETUAL`→`perpetual` 4,221 · `YIELD_BEARING`/`STAKING`/`SPOT_PAIR` → lowercase); collapse venue-spelling dups
      (`AAVEV3`/`AAVE`→`AAVE_V3` 64,218 · `MORPHOVAULTS`→`MORPHO` 50,266 · `COMPOUND`→`COMPOUND_V3` 13,904 ·
      `YEARNV3`→`YEARN_V3` · `KAMINO_LENDING`→`KAMINO`); resolve `''`/`NULL` instrument_type (4.49M) from the id/grain.
      (repos: market-tick-data-service, unified-trading-library)
- [ ] [DATA] P1. **perp_funding → `derivative_ticker`** as the canonical raw-funding home for ALL perps (drop the
      Drift-only 24h/7d/30d window aggregates). Ratify enum-member DeFi grains (`lst`/`staking`/`yield_bearing`) as
      canonical (case-fold only, already `InstrumentType` members). (repos: market-tick-data-service,
      unified-api-contracts)
- [ ] [DECISION] P2. **BLOCKED-OPERATOR-DECISION — bare `SUSHISWAP`/`UNISWAP` version (199,397 rows).** The data doesn't
      record the version; derive it per-pool from the factory/router contract address (audit) before choosing a
      canonical `_V{N}` — surface if underivable. `KALSHI_PERP`/`POLYMARKET_PERP`/`HYPERLIQUID` appearing in the defi
      `chain` axis (2,936 rows) = cefi leakage → clean out of the defi manifest (they stay cefi).
- [ ] [BACKEND] P2. **Combo cross-AG hand-off (leg-aware signed-weight spec).** Extend the 1–4-leg cap + shared
      `build_leg()` path to the DERIBIT-COMBO builders (`cefi/deribit_combo_adapter.py`, `tardis/combos.py`) —
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` open P2. DeFi has no combos; this rides here
      only because the DERIBIT-COMBO fix is cefi-side and passed to `cefi_consolidated_closeout_2026_07_18.md`.

## Track 2 — STORE: path authority + bucket hygiene (⛔ flat-vs-hive must be pinned) · P0

- **Sources**: `defi_dedicated_bucket_shared_migration_2026_07_13.md` (2 open P2/P3 + C0f),
  `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`,
  `issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`,
  `issues/features_onchain_bare_bucket_not_asset_group_migratable_2026_07_15.md`,
  `issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`,
  `issues/terraform_bucket_estate_drift_resurrection_2026_07_13.md`.
- **Close-out criterion**: one pinned path shape; zero dedicated-bucket refs; TF state matches live estate;
  lending-indices legacy bucket deleted (snapshot-first).

- [ ] [DATA] P0. **Pin the flat canonical path shape** (venue-before-chain, lowercase itype, `pipeline_mode=`); DELETE
      the dead top-level Solana `dex_pools/`+`lending_indices/` prefixes (frozen 2026-04-14, "Shape-B") and kill the
      second dexpool writer path. **Snapshot-before-delete** (pre-migration drain per the VM runbook). (repos:
      market-tick-data-service)
- [ ] [INFRA] P1. **Correct the STALE codex path docs** — `codex/02-data/per-asset-group-bucket-layouts.md` (documents
      chain-before-venue + omits pipeline_mode) and `market-tick-data-service/docs/GCS_PATHS.md` (shows dead Shape-B) →
      match the operator-locked SSOT + live writer. (repos: unified-trading-pm, market-tick-data-service)
- [ ] [INFRA] P1. **Delete the lending-indices legacy bucket (C0f)** + resolve TF estate drift
      (`market_data_defi_lending_indices_prd` still declared) + the bare `features-onchain` vs asset-group bucket. All
      GCS/bucket DELETEs are snapshot-first. (repos: deployment-service, market-tick-data-service)

## Track 3 — DENOM: empty_confirmed / denominator honesty · P1

- **Sources**: `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` (measured 63.9M via the v2 enumerator),
  `issues/defi_manifest_consolidator_duplicate_race_2026_07_10.md`, `defi-completeness-oracle.md`,
  `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`.
- **Close-out criterion**: fresh single-walk yields zero silent-`M` rows; denominator honest.

- [ ] [DATA] P0. **PURGE first, then seed.** Purge the 1.79M duplicate + ~219.5K phantom rows (re-verify the 219,529
      detected vs 219,632 flipped delta), THEN apply the ~63.9M `expected_unattempted` seed (operator write-volume
      gate). The "1M" framing is the old safety-cap slug — the real target is 63.9M. (repos: market-tick-data-service)
- [ ] [BACKEND] P1. **Add the `EXPECTED_SUBGRAPH_DEINDEXED` reason** to reclassify the 952 false Curve/Optimism
      `attempted_failed` → honest-empty; reconcile `spot_asset` absence from the enumerated catalogue (the v2 corpus
      predates SPOT_ASSET population; `spot_pair` 143K is partly the culled DRIFT SPOT leak). (repos:
      unified-api-contracts, instruments-service)

## Track 4 — CAP: zero-capture protocols · P2

- **Sources**: `mtds_defi_dex_zero_capture_protocols_2026_07_14.md` (2 open),
  `issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`,
  `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`.
- **Close-out criterion**: every MVP protocol/data_type captures or is honestly `empty_confirmed`.

- [ ] [BACKEND] P2. **Wire the remaining zero-capture protocols** (uniswap_v2/v4, trader_joe_v2, velodrome_v2 nearly
      done; Morpho lending indices; Solana ORCA/RAYDIUM swap indexer as a new capability). (repos:
      market-tick-data-service)

## Track 5 — COVERAGE: backfill → MVP-100% (largest open track) · P1 (C-GREEN gated on T1→T3)

- **Sources**: `mvp_backfill_defi_onchain_v10_2026_06_27.md` (G2 final verify),
  `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` (Phase-D carry tracer — prior ✅ was gate-only, data was
  10/10 SKIP → RE-RUN), `defi_onchain_derivable_values_and_date_drift_2026_06_20.md` (2 P1).
- **Close-out criterion**: manifest-counted canonical rows for every MVP cell; carry tracer green on real data.

- [ ] [DATA] P1. **Run the DeFi MVP backfill to 100%** on the canonical/migrated corpus (SPOT VMs; the DRIFT/Velocity
      historical grind is now CULL residue — DRIFT is out of target, so its gap is dropped not filled); re-run the
      Phase-D historical carry tracer on real data; resolve the 2 derivable-values P1s. (repos: deployment-service,
      market-tick-data-service, features-service)

## Track 6 — RENDER: data-status surface #4 + RESTORE the enumeration view · P1

- **Sources**: `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (HYPERLIQUID/ASTER 3.77M/1.07M invisible),
  `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`, the removed-feature archaeology
  (`deployment-api@47a7f67`/`953fa81`/`512180be` gated/suppressed/canonicalised-away the distinct-values view
  2026-07-16→18).
- **Close-out criterion**: data-status renders the canonical DeFi ids; the raw distinct-values audit view is live again.

- [ ] [BACKEND] P1. **RESTORE the "what exists" enumeration** (operator ask 2026-07-18) — a RAW (un-canonicalised)
      distinct-values audit panel per asset_group (venues / instrument_types / data_types / **chains**), each
      non-canonical value badged vs the UAC canonical sets. Source it from the nightly `coverage.json` rollup keys (its
      `by_venue`/`by_venue_data_type`/`by_venue_instrument_type` maps ARE the enumeration) + add `chain` to
      `measure_honest_coverage.py::_READ_COLUMNS`; do NOT add a new whole-corpus walk; do NOT canonicalise the display.
      Endpoint `GET /api/data-status/distinct-values/{asset_group}` (or extend `/catalogue-filter-options` with a
      `raw=true` mode). This is the SSOT-alignment tool: what it surfaces feeds the migration worklist. (repos:
      deployment-api, deployment-ui)
- [ ] [BACKEND] P2. **Fix the turbo-API captured-data hiding** (HYPERLIQUID/ASTER dual-count cefi/defi) + refresh the
      stale UI capability bundles (drift/pacifica residue). (repos: deployment-api, deployment-ui)

## Track 7 — CULL: purge the removed venues everywhere (dead-only, snapshot-first) · P1

> **Operator ruling 2026-07-18**: remove the CULLED venues ENTIRELY — UAC + manifest + GCS data + MVP catalogue + docs —
> to avoid confusion. **KEEP** `KALSHI-PERP`/`POLYMARKET-PERP` (roadmap — will be added), `LIGHTER-ZKSYNC`
> (blocked-credentials MVP scaffold — external-data-always-available rule), `EXTENDED-STARKNET` (live MVP). **All
> GCS-data deletes are snapshot-first** (irreversible). NOTE: LIGHTER/EXTENDED/(culled) PACIFICA are CeFi-classified —
> the cefi purge is passed to `cefi_consolidated_closeout_2026_07_18.md`; this track owns the DeFi-side residue.

- **Sources**: `issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`,
  `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`,
  `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`, `codex/02-data/mvp-scope-canonical.md`
  (STALE — still bolds `PACIFICA-SOLANA` as MVP; code culled it).
- **Close-out criterion**: zero references to culled venues in UAC / manifest / GCS / catalogue / docs; a snapshot
  exists before any delete.

- [ ] [DATA] P1. **Purge the culled Solana-perp venues' DeFi-side residue**
      (DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN) from manifest + GCS data + catalogue, snapshot-first;
      drop the ~20 `architecture_v2` DRIFT leg-spec files + the `launcher_registry` self-heal handoff. Clean the STALE
      `mvp-scope-canonical.md` PACIFICA-as-MVP bolding + any docs naming culled venues. (repos:
      market-tick-data-service, instruments-service, deployment-service, unified-trading-pm)

## Track 8 — INFRA / forward-data: resume steady-state (⛔ for forward honesty) · P1

- **Sources**: `issues/defi_scheduled_collection_outage_paused_crons_2026_07_16.md` (11 collect + 3 fwd crons paused
  since 2026-06-08), `issues/defi_consolidator_cron_left_paused_2026_07_15.md`,
  `issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`,
  `issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md`,
  `issues/defi_code_codex_drift_2026_05_27.md`.
- **Close-out criterion**: forward crons running; consolidator race/pause fixed; codex↔code drift closed.

- [ ] [INFRA] P1. **Resume the paused DeFi crons** (11 collect + 3 forward, paused ~40d — were operator-gated on the
      TradFi close-out) AFTER Track-1/2 land so they write the canonical shape; fix the consolidator duplicate-race +
      SIGKILL; right-size the honest-coverage nightly. **Because live=batch, no live-only DeFi data_type needs separate
      reconciliation** — the forward writer is already canonical (Half-A done); the open work is Half-B (migrate the
      historical corpus) then resume forward. (repos: deployment-service, market-tick-data-service)

## Contradiction resolution (pre-SSOT) — from the 2026-07-18 canonical-target audit (75 findings)

> Operator flow (2026-07-18): fix contradictions to the target BEFORE consolidating the SSOT reference, then migrate. A
> 6-agent audit (slot-4) scanned code + IS/MTDS docs + codex + plans/issues vs the 11-point target ideology and found
> **75 contradictions** (1 blocking · 35 high · 31 medium · 8 low; **53 doc · 17 code · 5 plan**). Most are docs stating
> a now-reversed decision, or docs accurately describing pre-migration code. DOC = align now; CODE = migration (Track
> 1).

### P0 — a real live bug the audit caught (not a doc issue)

- [ ] [BACKEND] P0. **7 lending adapters silently return `[]`** —
      `euler_v2`/`venus`/`solend`/`radiant`/`benqi`/`marginfi`/`fluid` carry a stale type-guard
      `if instrument_type not in (None, LENDING)` but now MINT `A_TOKEN`/`DEBT_TOKEN` → a caller passing the real type
      gets ZERO instruments (a capture gap masquerading as empty). Fix = guard on `(None, A_TOKEN,     DEBT_TOKEN)`,
      mirroring `morpho.py:93`. (repo: instruments-service)

### Blocker + codex-SSOT / UAC-contract doc fixes (must clear BEFORE the SSOT reference — an agent following them mints wrong ids)

- [ ] [DOCS] P0. **Fix the codex/UAC SSOT-source contradictions**: `mvp-scope-canonical.md:56` PACIFICA-as-MVP
      (**BLOCKING**) + `:69` LENDING→A_TOKEN/DEBT_TOKEN; `defi-canonical-naming-ssot.md:72/82/106` `lending` canonical +
      PACIFICA/DRIFT live; `availability-manifest-and-data-status.md:739/666/398` GMX/DRIFT under the cefi axis +
      LENDING + PROTOCOL-CHAIN venue; `per-asset-group-bucket-layouts.md:137` + `defi-data-type-taxonomy.md:197`
      chain-before-venue + combined venue; `unified-api-contracts/docs/canonical-instrument-ids.md:68/70/72` underscore
      venue + DERIBIT-no-quote + LENDING row + tradfi-no-`-USD`; `shard-granularity-cefi.md:106/207` ASTER=USDC + legacy
      DERIBIT grammar. (repos: unified-trading-pm, unified-api-contracts)

### CODE (migration — folds into Track 1)

- [ ] [BACKEND] P0. **POOL glued-key 3-segment convergence** —
      `unified-api-contracts/.../canonical/crosscutting/defi.py:313` `glued_pair_id` emits 4-segment
      `…:POOL:AAVE-USDC:100`, diverging from the MTDS 3-segment producer → **live data-join breakage**; converge to
      `…:POOL:BASE-QUOTE-FEE_BPS` + fix `parse_glued_pool_id`; confirm `defi.py:300` writes the SYMBOLIC 3-seg key into
      `canonical_instrument_id` (address stays in the machine `instrument_id`). (repo: unified-api-contracts)
- [ ] [BACKEND] P1. **SPOT taxonomy hard-enforce + reclassify** (the SPOT_PAIR-misuse fix, operator-agreed) — single
      tokens EIGEN/ETHFI (`eigenlayer.py`/`ethfi.py`) mint SPOT_PAIR → **SPOT_ASSET**; Solana AMM pools (`meteora.py`/
      `lifinity.py`) mint SPOT_PAIR → **DEX_POOL/SOLANA_AMM_POOL**; route all through `build_canonical_instrument_id`;
      fix the `:SPOT:`/`:PERP:`/`:STAKE:` shorthand-vs-enum key mismatches (`pyth.py`/`phoenix.py`/`marinade.py`). **ADD
      a validator**: for defi, `SPOT_PAIR` REQUIRES a two-token `BASE-QUOTE` symbol (single token → SPOT_ASSET; AMM →
      POOL). Data reclass migration for the affected rows. (repos: instruments-service, unified-api-contracts)
- [ ] [BACKEND] P1. **Lending type-guard + retire LENDING from the builder** — the 7-adapter guard bug above; plus
      `canonical_id_builder.py:84/146/194/967` drop/UNSUPPORTED-mark the `LENDING` example + type-set entries
      (A_TOKEN/DEBT_TOKEN only); GMX typed `perpetual` (not POOL/lending). (repo: unified-api-contracts)

### DOC-alignment sweep (IS + MTDS docs, ~33 rows)

- [ ] [DOCS] P1. **Align the IS + MTDS docs to the target** — {DEFI,CEFI,TRADFI}_INSTRUMENTS.md (Deribit-drops-quote →
      keep quote; tradfi FUTURE/EQUITY → `-USD`; EIGEN/ETHFI SPOT_PAIR → SPOT_ASSET; LENDING emitted-list;
      PACIFICA/DRIFT/`pacifica.py`/`drift.py` listed), ADAPTER_ARCHITECTURE.md, GCS_PATHS.md / DEFI_DOWNLOAD_STRATEGY.md
      / DEPLOYMENT_GUIDE.md (Shape-B path order + HYPERLIQUID/ASTER-as-defi), the DATABENTO_* / OPTIONS_CHAIN id
      examples. (repos: instruments-service, market-tick-data-service)

### PLAN/ISSUE stale-claim fixes

- [ ] [PM] P2. **SUPERSEDED banners** — `gcs_hive_partition_malformed_paths_remediation_2026_06_01.md:145` (inverted
      path as "SSOT"), `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md` (DRIFT-is-MVP),
      `instruments_foundation_completeness_2026_06_24.md:1254` (PACIFICA active), + the two MTDS
      DEFI-ASTER/HYPERLIQUID-LOG-REVIEW `category=DEFI` labels. (repo: unified-trading-pm)

### Operator decisions applied (2026-07-18)

- **ASTER = per-symbol REAL quote** (predominantly USDT; the tail keeps its real USD1/USDC — `aster.py` already embeds
  it). NOT hardcoded USDT. Fix `shard-granularity-cefi.md:106` (USDC) + the DEFI_DOWNLOAD docs.
- **BINANCE-DELIVERY = keep registered, mark non-MVP** (live COIN-M product; descope from the MVP backfill, keep the UAC
  scaffold — NOT purged; overrides the earlier "purge" framing). Only the DEAD venues are purged (Track 7).

### Cross-AG — PREDICTION canonicalisation also needs work (own close-out)

- [ ] [DATA] P1. **Prediction is a THIRD shard-atom grain** (operator 2026-07-18, per
      `availability-manifest-and-data-status.md:57-60`): the manifest grain is a **CQG bundle** keyed on
      `canonical_question_group` (`data_type=prediction_canonical_question_group`, e.g. `SPORTS_EPL_MATCH` /
      `BTC_UP_DOWN_DAILY`), with per-CID raw objects (Polymarket `condition_id` / Kalshi ticker) as row-level detail;
      `underlying` is DISPLAY-ONLY, not a key; IS side = `venue → dates` (no data_type axis,
      `VENUE_REFERENCE_DATA_CAPABILITIES={}`); MTDS drilldown is CQG-**above**-data_type
      (`data-status-drilldown-hierarchy.md:42`). The phantom reconciler **WIPES the CQG rows** because it mis-keys
      prediction on per-object `instrument_id` instead of the `(canonical_question_group,     day)` bundle — a P0 the
      SSOT vindicates. **Prediction warrants its own consolidated close-out** (a 4th, alongside cefi/tradfi/defi); this
      row is the pointer so it isn't lost. (repos: market-tick-data-service, deployment-api)

## Codex SSOTs (read before touching a track)

`codex/02-data/defi-canonical-naming-ssot.md`, `codex/02-data/defi-data-pipeline.md`,
`codex/02-data/availability-manifest-and-data-status.md`, `codex/02-data/honest-coverage-model.md`,
`codex/02-data/honest-absence-downstream-handling.md`, `codex/02-data/pipeline-mode-partition.md`,
`codex/02-data/defi-completeness-oracle.md`, `codex/05-infrastructure/manifest-consolidator-ssot.md`,
`codex/05-infrastructure/vm-launcher-runbook.md`, `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`.

## Progress Log

- **2026-07-18 (slot-4, /autonomous) — Canonical-target audit → doc reconciliation → SSOT reference SHIPPED; migrations
  PARKED.** Handoff record (rule 6 — resume losslessly from here):
  - **Committed this session**: DeFi plan + cefi/tradfi pass-through (`unified-trading-pm@58a6a54ed`); the
    contradiction-resolution track + 2 decisions + prediction correction (`@6d60e6199`); the **58 doc-contradiction
    fixes** across 4 repos (UAC `@faca792e` · IS `@198addd1` · MTDS `@5f498858` · PM codex/plans `@709274a5c`); the
    **cross-asset canonical target SSOT** codex doc `codex/02-data/cross-asset-canonical-target-ssot.md` (`@61095c4cd`)
    — the durable SSOT home the operator asked for.
  - **Operator decisions (all in the SSOT doc §11 + here)**: POOL key = 3-seg fee-in-symbol · defi two-id kept (Option
    A, no mass rewrite) · retire legacy LENDING→A_TOKEN/DEBT_TOKEN · itype lowercase in path/column / UPPER in id ·
    ASTER = **per-symbol real quote** (NOT hardcoded USDT) · BINANCE-DELIVERY = **keep registered, non-MVP** (NOT
    purged) · culled-venue purge dead-only + snapshot-first + keep LIGHTER/EXTENDED/KALSHI-PERP/POLYMARKET-PERP · combos
    leg-aware signed-weight · equity `-USD` all four · tradfi daily `ohlcv_24h` · hyphen venue · DERIBIT quote gated ·
    SPOT_PAIR misuse → fix (EIGEN/ETHFI→SPOT_ASSET, AMM→POOL/DEX_POOL) + hard-enforce validator · prediction =
    shard-grain #3 (CQG bundle). The 4 Q&A the operator ruled: purge dead-only+keep LIGHTER/EXTENDED · POOL 3-seg ·
    combos leg-aware · ASTER per-symbol · BINANCE-DELIVERY keep-non-MVP.
  - **PARKED for the operator's return (NOT executed — the migration phase)**: the **17 CODE fixes** incl. the **P0
    7-lending-adapter silent-`[]` bug** (Track-1), the POOL 3-seg glued-key convergence, the SPOT_PAIR reclassify +
    validator, retire-LENDING-from-builder; and the operator-gated DATA ops (63.9M `expected_unattempted` seed after the
    phantom+duplicate purge; the snapshot-first GCS deletes of the Shape-B prefixes + culled-venue data; the historical
    reclass migrations). These are code+data changes the operator sequenced AFTER the SSOT — see the tracks above + the
    consolidated questions doc `plans/active/issues/canonical_closeout_open_questions_2026_07_18.md`.
  - **/plan-reconcile (autonomous) IN FLIGHT**: Phase 0 done — corpus mechanically GREEN (`run_hygiene_sweep.sh --ci`: 0
    hard failures; 1 soft = 17 plans >1000L, splitting operator-gated). Phase-0 flags: 9 unlocked terminal-superseded
    docs = archival candidates (mostly DRIFT-cull issues), 1 locked (`gcs_hive_partition_malformed_paths_remediation`,
    PARK), 4 fully-done candidates to verify+archive. Phase-1 contradiction sweep dispatched (`wf_9458e3be`). Findings →
    the open-questions issue doc.

  the 7 active defi plans + ~35 issues into 8 tracks. Ground truth: the DeFi foundational migration already ran (v9 +
  asset_group + pipeline_mode + source; dedicated→shared bucket done), so the remaining work is a residual canon walk
  (C2–C12), a now-RESOLVED POOL-id policy (Option A, 3-segment key), a culled-venue purge (dead-only, snapshot-first,
  keep LIGHTER/EXTENDED/KALSHI-PERP/POLYMARKET-PERP), a large coverage/denominator effort (~63.9M expected_unattempted
  seed after a phantom+duplicate purge), and restoring the removed data-status enumeration view. Operator rulings
  (2026-07-18) baked into the Canonical-target + Operator-decisions sections: POOL key 3-segment fee-in-symbol; two-id
  model kept (no mass rewrite); retire legacy LENDING → A_TOKEN/DEBT_TOKEN + bake into the catalogue builder;
  instrument_type lowercase in path/column, UPPER in id segment; combos = leg-aware signed-weight spec (cross-AG,
  DERIBIT-COMBO handoff to the cefi plan). Live manifest baseline (distinct-values audit, `market-data-tick-defi-prd`,
  28.35M rows): 98.8% of distinct ids embed a raw address (the machine `instrument_id`, by design under the two-id
  model), instrument_type + venue spelling carry heavy case/version drift (worklist in Track 1). cefi/tradfi findings +
  decisions passed to the two sibling plans per the operator's ownership split. No code/data changed yet — this plan
  holds the scope + target.
