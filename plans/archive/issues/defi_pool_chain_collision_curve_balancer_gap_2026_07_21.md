---
doc_type: issue
title: DeFi POOL cross-chain address collision — CURVE unaddressed, Balancer patch conflicts with Option-A ruling
summary:
  A superseded plan's CURVE cross-chain pool-address collision fix was never carried forward by its successor, and a
  2026-07-08 Balancer @CHAIN instrument_id patch conflicts with the 2026-07-18 Option-A ruling that instrument_id must
  stay bare. Surfaced by a /plan-reconcile archival-verification sub-agent; not auto-fixed, not silently archived away.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service, unified-trading-pm, features-service]
scope: [engineer, admin]
tags: [defi, canonical-id, pool-identity, data-correctness, cross-chain]
related:
  [
    /plans/archive/2026_07/defi_pool_id_chain_uniqueness_2026_07_18.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/archive/issues/mdps_orchestration_scanner_bare_instrument_id_chain_collision_2026_07_29.md,
  ]
created: 2026-07-21
priority: P1
parent_epic: defi_master
assigned_vm: planning
locked_by:
resolved_by:
  "market-tick-data-service@5bf8a3c7 (Stage 2 MTDS preflight fix) + features-service (Stage 4 chain-stamping fix,
  mtds_canonical_reader.py + 2 calculators, this session) — all 5 stages of the trace now terminal: Stage 1 PASS, Stage
  2 FAIL→FIXED, Stage 3 confirmed moot, Stage 4 FAIL→FIXED, Stage 5 confirmed not vulnerable"
source: [/plan-reconcile audit, 2026-07-21]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **✅ ARCHIVED 2026-07-30** — all 6 todos `[x]`, 0 open work, `status: resolved`, `resolved_by` set, unlocked. The
> 5-stage cross-chain-collision trace (catalogue → MTDS preflight → MDPS dedup → features-service calculators →
> manifest/data-status) is now fully terminal. Moved to `plans/archive/issues/`.

# DeFi POOL cross-chain address collision — CURVE unaddressed, Balancer patch conflicts with Option-A ruling

> Surfaced by a `/plan-reconcile` read-only sub-agent verifying archival of the superseded
> `defi_pool_id_chain_uniqueness_2026_07_18.md` against its successor `defi_consolidated_closeout_2026_07_18.md`. Filed
> per CLAUDE.md's "big finding" triage rule (data-correctness) — NOT auto-fixed, NOT silently archived away.

## The original bug (2026-07-18)

The live DeFi catalogue has 6 pool contract addresses deployed on TWO chains each (12 rows) that collide on
`instrument_id == pool_address.lower()` — any consumer keying on bare `instrument_id` silently picks one chain's pool.
`defi_pool_id_chain_uniqueness_2026_07_18.md` was opened to fix this by adding `chain` to the POOL identity everywhere.

That plan was superseded 2026-07-18 by `defi_consolidated_closeout_2026_07_18.md`, which the operator ruled should use a
different mechanism: a **two-id / dual-key model (Option A)** — `instrument_id` stays bare `pool_address.lower()`;
`chain` instead lives in the symbolic `canonical_instrument_id`/`glued_pair_id` (`VENUE-CHAIN:POOL:...`). This is a
legitimate, deliberate, better-considered replacement — not a silent drop of the original plan.

## What's actually unresolved today (verified against live code, 2026-07-21)

1. **CURVE collision unaddressed.** The CURVE cross-chain pool (`0x004c167d...`, deployed on AVALANCHE + OPTIMISM) that
   motivated the original bug report has **no fix, test, or tracked todo anywhere** targeting it specifically. Its
   `instrument_id` is still bare and still colliding.
2. **Balancer patch conflicts with the Option-A ruling.** 5 Balancer addresses WERE patched — but on 2026-07-08, via an
   earlier, narrower mechanism: `@CHAIN`-suffixing `instrument_id` directly in `prod/catalog.parquet`
   (`instruments-service` script `balancer_cross_chain_pool_address_collision_backfill_2026_07_08.py`, scoped only to
   `venue=="BALANCER"`). The later 2026-07-18 Option-A ruling states `instrument_id` **MUST stay**
   `pool_address.lower()` (bare, no suffix), because `market_tick_data_service/engine/defi_catalog_reader.py:192` reads
   the catalogue's `instrument_id` column verbatim, and MTDS independently derives
   `instrument_id = pool_address.lower()` at capture time via the same UAC property (bare, no suffix). **Nobody has
   reconciled the 2026-07-08 patch against the 2026-07-18 ruling** — for as long as the `@CHAIN`-suffixed patch remains
   live in `prod/catalog.parquet`, there is a plausible expected-universe-vs-actual-write key mismatch for exactly those
   5 Balancer rows.
3. **Codex SSOT not updated.** `/codex/02-data/defi-canonical-naming-ssot.md` was never updated with the two-id/dual-key
   POOL model. The model is documented in `unified_api_contracts/canonical/crosscutting/defi.py` docstrings,
   `instruments-service/docs/DEFI_INSTRUMENTS.md`, and the closeout plan body — but not in the codex doc the original
   plan named as its post-phase-audit target.

## Live-code ground truth (verified, not just plan-text)

- `unified_api_contracts/canonical/crosscutting/defi.py:409-435` (`build_pool_identity`) — chain lives in the symbolic
  `glued_pair_id`/`canonical_instrument_id` only.
- `unified_api_contracts/canonical/crosscutting/defi.py:313-331` (`DefiPoolIdentity.canonical_instrument_id` property) —
  the machine `instrument_id` stays `pool_address.lower()`, chain-agnostic, by deliberate Option-A design.
- `instruments-service/scripts/build_instrument_catalogue.py:1151-1199` (`_aggregate_key`) — DOES fold chain into the
  catalogue's internal per-pool lifecycle-merge key (`pool::{chain}::{address}`, line 1186) — this predates both plans
  and correctly keeps the two chains' lifecycles from merging internally, but doesn't touch the emitted `instrument_id`.

## Recommended fix (not yet actioned — operator/plan-owner decision)

- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot-5, review)** — Verified each of the 6 known cross-chain pool-address
      collisions end-to-end (catalogue → MTDS → MDPS traced; features/manifest-data-status NOT independently traced, see
      the 2026-07-26 Update below). Catalogue + MTDS-read stages PASS for all 6; 2 genuine FAIL/RISK findings at the
      pre-flight/dedup-skip layers (Stage 2 MTDS, Stage 3 MDPS) — see the new P2 followup todo below.
- [x] ✅ [DATA] P1. **RESOLVED/MOOT 2026-07-26 (slot-5, review)** — Reconcile the 2026-07-08 Balancer `@CHAIN`
      `instrument_id` patch against the 2026-07-18 Option-A ruling. Live catalogue check: ZERO `@CHAIN`-suffixed
      `instrument_id` values anywhere in the 12,219-row prod catalogue — the patch is no longer present (reverted or
      superseded by a later regen). Nothing left to reconcile; no action needed.
- [x] ✅ [DATA] P1. **ALREADY CORRECT 2026-07-26 (slot-5, review) — this item's premise was stale.** CURVE's
      `instrument_id` IS bare (`pool_address.lower()`) — which is the CORRECT Option-A state, not a bug to fix.
      Disambiguation lives in `canonical_instrument_id` (`CURVE-AVALANCHE:POOL:USDC-WETH.E` vs
      `CURVE-OPTIMISM:POOL:CRVUSD-CRV`), confirmed live and correct for both chain rows. There is no CURVE-specific gap
      distinct from the general pre-flight/dedup finding below (which affects CURVE and all 5 Balancer rows identically,
      not CURVE alone).
- [x] ✅ [DOC] P2. **DONE 2026-07-28 (slot-13)** — Added "POOL identity is a two-id / dual-key model (Option A,
      operator-ruled 2026-07-18)" section to `/codex/02-data/defi-canonical-naming-ssot.md`: documents `instrument_id`
      (bare `pool_address.lower()`, machine/manifest join key) vs `canonical_instrument_id`/ `glued_pair_id`
      (`VENUE-CHAIN:POOL:BASE-QUOTE[-FEE_BPS]`, symbolic/UI key), sourced from
      `unified_api_contracts/canonical/crosscutting/defi.py`'s `DefiPoolIdentity`/`build_pool_identity`; notes the
      separate internal-only `instruments-service/scripts/build_instrument_catalogue.py::_aggregate_key`
      `pool::{chain}::{address}` lifecycle-merge key is unrelated to the two ids above; cross-links the still-open P2
      pre-flight/dedup keying-gap todo in this same issue doc. `code_refs`/`related`/`last_reviewed` updated accordingly
      — unified-trading-pm@(see commit below).

## Update (2026-07-26, slot-5/review — defi_satellite_ao_dispatch_batch1-024, end-to-end verification)

Live-verified all 6 collision rows (1 CURVE + 5 BALANCER) against the current prod catalogue
(`instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`, 12,219 rows) and traced the
catalogue→MTDS→MDPS code paths. Per-stage verdict (identical mechanism across all 6 rows, so reported per-stage rather
than a mechanically-repeated 6×5 table):

**The 6 rows, confirmed live:**

| instrument_id (bare, lowercased)             | venue    | chains              | canonical_instrument_id (both rows)                                                                    |
| -------------------------------------------- | -------- | ------------------- | ------------------------------------------------------------------------------------------------------ |
| `0x004c167d27ada24305b76d80762997fa6eb8d9b2` | CURVE    | AVALANCHE, OPTIMISM | `CURVE-AVALANCHE:POOL:USDC-WETH.E` / `CURVE-OPTIMISM:POOL:CRVUSD-CRV`                                  |
| `0x01abc00e86c7e258823b9a055fd62ca6cf61a163` | BALANCER | ETHEREUM, POLYGON   | `BALANCER-ETHEREUM:POOL:YFI-UNI-SUSHI-AAVE-MKR-BAL-COMP-WETH` / `BALANCER-POLYGON:POOL:WBTC-WETH-BIFI` |
| `0x03cd191f589d12b0582a99808cf19851e468e6b5` | BALANCER | ETHEREUM, POLYGON   | `BALANCER-ETHEREUM:POOL:MKR-BAL` / `BALANCER-POLYGON:POOL:WBTC-USDC-WETH`                              |
| `0x06df3b2bbb68adc8b0e302443692037ed9f91b42` | BALANCER | ETHEREUM, POLYGON   | `BALANCER-ETHEREUM:POOL:DAI-USDC-USDT` / `BALANCER-POLYGON:POOL:USDC-DAI-MIMATIC-USDT`                 |
| `0xc6a5032dc4bf638e15b4a66bc718ba7ba474ff73` | BALANCER | ETHEREUM, POLYGON   | `BALANCER-ETHEREUM:POOL:DAI-WETH` / `BALANCER-POLYGON:POOL:USDC-WETH-BAL`                              |
| `0xfeadd389a5c427952d8fdb8057d6c8ba1156cc56` | BALANCER | ETHEREUM, POLYGON   | `BALANCER-ETHEREUM:POOL:WBTC-RENBTC-SBTC` / `BALANCER-POLYGON:POOL:WBTC-RENBTC`                        |

**Stage 1 — Catalogue: PASS, and finding #2 (Balancer `@CHAIN` patch conflict) is MOOT — already resolved.** Queried
`prod/catalog.parquet` directly: ZERO `instrument_id` values anywhere in the 12,219-row catalogue carry an `@CHAIN`
suffix (checked exhaustively for any `@` in `instrument_id` — the only matches are unrelated `@LIN`-margin-suffixed CEFI
perpetuals, not Balancer pools). All 6 collision rows now show clean bare `instrument_id = pool_address.lower()` with
`chain` as a genuine separate column and correctly-disambiguated `canonical_instrument_id`/`glued_pair_id` per row. The
2026-07-08 `@CHAIN` patch described in this doc's "What's actually unresolved" §2 is **no longer present** in the live
catalogue — either reverted or superseded by a later catalogue regen; either way, today's catalogue is
Option-A-compliant for all 6 rows. **This closes finding #2 outright** (no reconciliation action needed — there is
nothing left to reconcile).

**Stage 2 — MTDS: READ is PASS, PRE-FLIGHT SKIP-CHECK is a genuine FAIL/RISK finding.**
`market_tick_data_service/engine/defi_catalog_reader.py:192-207` reads the catalogue's `instrument_id` column verbatim
(bare, by design — comment confirms this is intentional so "the expected-universe instrument_id matches the manifest
cell") AND separately carries the catalogue's `chain` column onto the returned `CatalogRow` — correct. **But**
`market_tick_data_service/engine/orchestrator/__init__.py::_run_preflight_availability_check` (~L487-560) builds its
"already captured, skip" atom-tracking set keyed on `(venue, data_type)` → `{atom}` where `atom = instrument_id` (bare)
— **`chain` is never read or included anywhere in this function** (confirmed: zero occurrences of `"chain"` in the whole
file). For our exact collision shape (same `venue`, same bare `instrument_id`, two different `chain`s) this pre-flight
optimization cannot distinguish `(CURVE, AVALANCHE, 0x004c…)` from `(CURVE, OPTIMISM, 0x004c…)` — if one chain's shard
is already `captured`, the skip-set would make the OTHER chain's genuinely-uncaptured shard look already-covered,
silently skipping its re-fetch on a subsequent run (this is a pre-flight freshness OPTIMIZATION, not a write-path bug —
it doesn't corrupt data already written, but it can cause a real gap to go unnoticed/unfetched).

**Stage 3 — MDPS: same bug class, second independent instance.**
`market_data_processing_service/app/core/orchestration_scanner.py` (~L680-693) builds an `existing_outputs` dedup set
keyed on `(timeframe, instrument_id)` via `extract_instrument_id_from_blob_path(blob_metadata.name)` — again bare
`instrument_id`, no `chain` component. Same risk shape as Stage 2: if MDPS's output-existence check ever extracts the
bare pool address as the per-instrument key (rather than a chain-embedded canonical form), two chains' candle outputs
for the same address could shadow each other in this dedup set. **Not fully confirmed empirically** this pass — a scoped
`gcloud storage ls` under a real captured day's prefix (to check whether the actual output filename embeds `chain` or
not) was attempted but the manifest reader was in a slow degraded per-VM-shard fallback mode (consolidated blob
age >120s) and the check did not complete in this session; the static evidence (file/line above) stands on its own as a
credible risk finding regardless.

**Stage 4 (features-service) + Stage 5 (manifest/data-status) — NOT independently traced this pass.** Given the depth
already required to confirm Stages 1-3, and that the identified risk is a pre-flight/dedup OPTIMIZATION gap (not a
proven data-corruption bug), tracing the remaining 2 stages is left as explicit follow-up rather than guessed at.

**Overall verdict: 4 of 6 rows-worth-of-mechanism PASS at the catalogue+read layers; 2 genuine FAIL/RISK findings at the
pre-flight/dedup-skip layers (Stages 2-3), both the SAME architectural bug class (bare-`instrument_id`-only keying with
no `chain` component) rather than 2 unrelated bugs.** Filed as a new P2 follow-up todo below (distinct from the resolved
`@CHAN` patch finding and the still-open CURVE-fix / codex-doc todos already in this doc).

- [x] ✅ [DATA] P2 (MTDS half). **DONE 2026-07-29 — Fixed the bare-`instrument_id`-only pre-flight/dedup keying gap in
      `market_tick_data_service/engine/orchestrator/__init__.py::_run_preflight_availability_check`.** `chain` is now
      colon-prefixed into the atom string when present (`f"{chain}:{atom}"`), so cross-chain-colliding bare pool
      addresses (CURVE/BALANCER) stay distinct in the skip-set instead of one chain's captured shard silently masking
      the other's genuinely-uncaptured shard; falls back to the bare atom when no `chain` value exists (non-DeFi rows
      unaffected). New regression tests in `test_preflight_atom_coverage.py` using the real CURVE collision address
      (`0x004c167d27ada24305b76d80762997fa6eb8d9b2`, AVALANCHE vs OPTIMISM) proving the two chains' shards stay
      distinct, plus a no-chain-column fallback test. `quality-gates.sh` green. — market-tick-data-service@5bf8a3c7.
      **MDPS half — CONFIRMED MOOT 2026-07-29**, re-filed and closed as
      `plans/archive/issues/mdps_orchestration_scanner_bare_instrument_id_chain_collision_2026_07_29.md`: a scoped GCS
      read of real `processed_candles/` output for 2 of the 6 collision rows (CURVE, both `dex_pool_swaps` and
      `dex_pool_state`, `day=2026-07-25`) found every real MDPS candle output filename is the FULL canonical
      chain-embedded id (e.g. `CURVE-AVALANCHE:POOL:USDC-USDT.parquet`), never the bare `pool_address.lower()` — so
      `orchestration_scanner.py`'s `existing_outputs` dedup key can never collide across chains at this site (chain is
      already baked into the id string itself), unlike MTDS's raw-tick side which reads the catalogue's bare
      `instrument_id` verbatim by design. No code change needed. Repos: market-tick-data-service (done),
      market-data-processing-service (confirmed non-issue, no fix required).
- [x] ✅ [DATA] P2. **DONE 2026-07-30 — Stage 4 (features-service) was a genuine FAIL, now FIXED; Stage 5
      (manifest/data-status) traced and confirmed NOT vulnerable.**

      **Stage 4 — features-service onchain pool calculators: confirmed FAIL, root-caused, fixed.**
                              `features_service/onchain/adapters/mtds_canonical_reader.py::read_canonical_defi_parquets` fans a shard list across
                              MULTIPLE `chain` values per venue (`pool_invariant_drift_calculator.py` loops `_CURVE_CHAINS` + `_BALANCER_CHAINS`
                              — the exact 1 CURVE + 5 BALANCER collision addresses this doc tracks; `concentrated_liquidity_il_realised_
                              calculator.py` loops `_UNISWAP_V3_CHAINS`), reads each shard's parquet, then `pd.concat`s them into one `raw_data`
                              frame — but `chain` is a hive PATH partition only, never a written parquet column, for the `dex_pool_state`/
                              `dex_pool_swaps` schema (confirmed via `unified_api_contracts.registry._schema_spec_defi.DEFI_POOL_WINDOW_COLUMNS`
                              — no `chain` `ColumnSpec` exists there), so the concatenated frame had ALREADY lost chain identity before either
                              calculator's `calculate_features()` ran — those two calculators then emitted output rows keyed only on
                              `(timestamp, pool_address)`, silently indistinguishable across the 2 chains for every collision address (e.g. the
                              CURVE `0x004c167d…` row could be AVALANCHE or OPTIMISM data with no way to tell downstream). This is worse than a
                              pre-flight skip risk (Stage 2/3's shape) — it's a genuine content-conflation bug in computed feature output.
                              Root-cause fix (not a workaround): `read_canonical_defi_parquets` now stamps `part["chain"] = shard.chain` onto
                              every row read from a shard whose parquet content lacks a `chain` column (defensive: preserves an existing
                              `chain` column verbatim if the schema ever adds one, e.g. mirrors how `gas_fees`/`block_priority_gas_distribution_
                              calculator.py` already carries `chain` natively). Both calculators updated to require/propagate `chain` through to
                              their output rows (empty string, never fabricated, when a caller feeds `calculate_features()` directly without a
                              `chain` column — e.g. existing unit tests). New regression tests: `test_mtds_canonical_reader.py` (chain-stamping
                              when absent, chain-preservation when already present, and an explicit 2-chain-same-`pool_address`-collision test
                              using the real CURVE address `0x004c167d27ada24305b76d80762997fa6eb8d9b2` proving the concatenated rows stay
                              chain-distinguishable) + `test_defi_pipeline_extension_calculators.py` (both calculators, 2-chain collision →
                              2 output rows with matching `pool_address` but distinct `chain`). `.qg_last_passed_sha` verified green (see
                              features-service quality-gates.sh run this session). — features-service (sha recorded in the Progress Log below).

                              **Stage 5 — manifest/data-status: traced, confirmed NOT vulnerable (no fix needed).** Two independent manifest
                              surfaces checked: (1) `market_data_processing_service/app/core/canonical_writer_stamping.py` (the MDPS candle
                              manifest row_key builder) carries an explicit, dedicated `chain=row_key.get("chain", "")` field forwarded into the
                              manifest row — the schema is chain-aware by design, consistent with Stage 3's already-confirmed-moot finding that
                              real MDPS candle output filenames are the FULL canonical chain-embedded id, never the bare pool address, so this
                              surface was never exposed to the collision. (2) `features_service/onchain/app/core/feature_writer.py`'s onchain
                              emission-policy manifest write (`_check_emission_policy`'s `row_key={"feature_group": group, "date": date}`) is
                              keyed at the (feature_group, date) grain — no `pool_address`/`instrument_id`/`chain` dimension at all — so the
                              manifest CELL for `pool_invariant_drift`/`concentrated_liquidity_il_realised` was never at risk of a cross-chain
                              collision; the bug that existed (now fixed above) was entirely inside the feature CONTENT rows within that one
                              manifest-tracked file, not the manifest addressing itself. **Conclusion: this doc's full 5-stage trace is now
                              complete** — Stage 1 (catalogue) PASS, Stage 2 (MTDS preflight) was FAIL→FIXED, Stage 3 (MDPS dedup) confirmed
                              moot, Stage 4 (features-service) was FAIL→FIXED, Stage 5 (manifest/data-status) confirmed not vulnerable.

## Provenance

- `defi_pool_id_chain_uniqueness_2026_07_18.md` — original bug report + design (superseded, archived 2026-07-21).
- `defi_consolidated_closeout_2026_07_18.md` — successor plan, owns the Option-A architecture (active, unlocked, still
  has 23 open todos as of 2026-07-21 — this finding is NOT yet one of them).
