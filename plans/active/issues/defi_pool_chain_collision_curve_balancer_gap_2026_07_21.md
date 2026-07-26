---
doc_type: issue
title: DeFi POOL cross-chain address collision — CURVE unaddressed, Balancer patch conflicts with Option-A ruling
summary:
  A superseded plan's CURVE cross-chain pool-address collision fix was never carried forward by its successor, and a
  2026-07-08 Balancer @CHAIN instrument_id patch conflicts with the 2026-07-18 Option-A ruling that instrument_id must
  stay bare. Surfaced by a /plan-reconcile archival-verification sub-agent; not auto-fixed, not silently archived away.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, canonical-id, pool-identity, data-correctness, cross-chain]
related:
  [
    plans/archive/2026_07/defi_pool_id_chain_uniqueness_2026_07_18.md,
    plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-07-21
priority: P1
parent_epic: defi_master
assigned_vm: planning
locked_by:
resolved_by:
source: [/plan-reconcile audit, 2026-07-21]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

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
- [ ] [DOC] P2. Update `/codex/02-data/defi-canonical-naming-ssot.md` with the two-id/dual-key POOL model (post-phase
      codex audit that `defi_pool_id_chain_uniqueness_2026_07_18.md` named but was superseded before completing).

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

- [ ] [DATA] P2. **Fix the bare-`instrument_id`-only pre-flight/dedup keying gap** found 2026-07-26: add `chain` to the
      atom/key tuple in `market_tick_data_service/engine/orchestrator/__init__.py::_run_preflight_availability_check`
      (currently `(venue, data_type) → {instrument_id}`, needs `(venue, chain, data_type) → {instrument_id}` or fold
      `chain` into the atom string itself), and verify/fix the equivalent gap in
      `market_data_processing_service/app/core/orchestration_scanner.py`'s `existing_outputs` dedup set (confirm whether
      MDPS output filenames already embed chain — if so this may be a non-issue at that specific site, still needs the
      scoped GCS check that timed out in this pass). **Done when**: both sites are confirmed either chain-safe (with
      cited evidence) or fixed, with a regression test for the 2-chain-same-address case using one of the 6 real
      collision addresses above. Repos: market-tick-data-service, market-data-processing-service.

## Provenance

- `defi_pool_id_chain_uniqueness_2026_07_18.md` — original bug report + design (superseded, archived 2026-07-21).
- `defi_consolidated_closeout_2026_07_18.md` — successor plan, owns the Option-A architecture (active, unlocked, still
  has 23 open todos as of 2026-07-21 — this finding is NOT yet one of them).
