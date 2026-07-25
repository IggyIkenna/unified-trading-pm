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
assigned_vm:
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

- [ ] [DATA] P1. Verify each of the 6 known cross-chain pool-address collisions (1 CURVE + 5 BALANCER) resolves
      correctly under Option A end-to-end (catalogue → MTDS → MDPS → features → manifest/data-status).
- [ ] [DATA] P1. Reconcile the 2026-07-08 Balancer `@CHAIN` `instrument_id` patch against the 2026-07-18 Option-A ruling
      — either revert the patch (bare `instrument_id`, rely on `canonical_instrument_id` for disambiguation) or
      explicitly ratify Balancer as an intentional carve-out and document why.
- [ ] [DATA] P1. Fix CURVE's still-bare, still-colliding `instrument_id` (currently the only one of the 6 with zero
      mitigation).
- [ ] [DOC] P2. Update `/codex/02-data/defi-canonical-naming-ssot.md` with the two-id/dual-key POOL model (post-phase
      codex audit that `defi_pool_id_chain_uniqueness_2026_07_18.md` named but was superseded before completing).

## Provenance

- `defi_pool_id_chain_uniqueness_2026_07_18.md` — original bug report + design (superseded, archived 2026-07-21).
- `defi_consolidated_closeout_2026_07_18.md` — successor plan, owns the Option-A architecture (active, unlocked, still
  has 23 open todos as of 2026-07-21 — this finding is NOT yet one of them).
