---
doc_type: plan
title: DeFi POOL instrument_id chain-uniqueness — add chain to the POOL identity (shard-atom migration)
summary:
  Operator ruled 2026-07-18 for the full fix — the live defi catalogue has 6 pool contract addresses deployed on TWO
  chains each (12 rows) that collide on `instrument_id == pool_address.lower()`, so any consumer keying on instrument_id
  alone silently picks one chain's pool. Add `chain` to the DeFi POOL identity everywhere, gated on a cross-service
  shard-atom check (the atom must be identical across writer/manifest/status/gate/UI AND MTDS/MDPS/ features) so the
  identity change lands coherently rather than fragmenting one lifecycle.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer]
tags: [defi, identity, pool, shard-atom, instrument-id, uniqueness]
related: [data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  "data_status_page_ux_and_canonicalisation_2026_07_16.md LENDING-drain side-discovery (operator ruling 2026-07-18: FULL
  FIX)"
locked_by:
locked_since:
supersedes:
superseded_by:
---

# DeFi POOL instrument_id chain-uniqueness

**Operator ruling (2026-07-18):** full fix — add `chain` to the DeFi POOL identity (not just a catalogue dedupe-key).

## Context

The live defi catalogue carries **6 duplicated `instrument_id`s (12 rows)** where the SAME pool contract address is
deployed on two chains (deterministic EVM deployment puts the same address on multiple chains) and both rows key on
`instrument_id == pool_address.lower()`:

- `0x004c167d…` = CURVE on **AVALANCHE + OPTIMISM**
- `0x01abc00e…`, `0x03cd191f…`, `0x06df3b2b…`, `0xc6a5032d…`, `0xfeadd389…` = BALANCER on **ETHEREUM + POLYGON**

Each pair has a DIFFERENT `available_from` → genuinely distinct instruments colliding on one id. Blast radius is small
(6 of 10,883) but the CLASS is an identity-uniqueness violation: any consumer keying on `instrument_id` alone silently
picks one chain's pool. Fix: include `chain` in the DeFi POOL identity / dedupe key.

**Why gated on a shard-atom check:** the shard atom must be **identical across writer/manifest/status/gate/UI** (data
codex HARD RULE) AND across MTDS/MDPS/features — changing the POOL identity in one place without the others fragments a
single lifecycle into ghosts (the exact failure `_incremental_merge_keys` documents for cefi). So step 1 is the audit.

## Codex SSOTs (read before touching)

- `codex/02-data/availability-manifest-and-data-status.md` — "shard atom identical across
  writer/manifest/status/gate/UI".
- `codex/02-data/defi-canonical-naming-ssot.md` — DeFi canonical identity + naming.
- `codex/04-architecture/tier-and-import-architecture.md` — no service↔service deps; integrate by UAC contract.
- `build_instrument_catalogue._incremental_merge_keys` — the current DeFi POOL dual-form identity
  (`pool::<CHAIN>::<addr.lower()>`) already chain-aware in the merge; the catalogue `instrument_id` is not.

## Todos (audit first — identity change is a coordinated migration)

- [ ] [DATA] P1. **Shard-atom audit FIRST** — enumerate every place the DeFi POOL identity is derived/keyed:
      `build_instrument_catalogue` (`instrument_id` vs the `pool::CHAIN::addr` merge key), MTDS readers, MDPS,
      features-onchain, the availability manifest atom, the data-status shard atom, and any UI drilldown key. Produce a
      table of "current key" per consumer — this is the plan's foundation gate (its findings shape the migration).
- [ ] [DATA] P1. **Decide the canonical POOL identity** — `pool::<CHAIN>::<addr.lower()>` (mirror the existing merge
      key) as the single `instrument_id` form, confirmed against the audit so ALL consumers can adopt it identically.
- [ ] [DATA] P1. **UAC + IS: derive POOL instrument_id with chain** — change the catalogue POOL `instrument_id`
      derivation to include chain; add a UAC/IS unit test asserting the 6 known collisions now produce 12 distinct ids
      with their correct per-chain `available_from`.
- [ ] [DATA] P1. **Propagate to MTDS/MDPS/features** — update every consumer keyed on the bare `instrument_id` to the
      chain-inclusive form in lockstep (shard-atom parity); integrate by UAC contract, not a service↔service dep.
- [ ] [DATA] P1. **Manifest + data-status atom** — reconcile the availability manifest + data-status shard atom to the
      new identity; verify identical atom across writer/manifest/status/gate/UI.
- [ ] [DATA] P2. **Catalogue re-derivation on real infra** — re-run the catalogue so the 6 collisions split; verify on
      real GCS (12 distinct ids, no other id-count regression) + monotonic-guard ACCEPT.
- [ ] [REVIEW] P2. **Post-phase codex audit** — update `defi-canonical-naming-ssot.md` +
      `availability-manifest-and-data-status.md` with the chain-inclusive POOL identity; confirm no plan↔codex drift.

## Progress Log

- **2026-07-18** — Authored from the data-status round-3 LENDING-drain side-discovery after the operator ruled full fix
  (chain in identity, not a catalogue-only dedupe key). Human plan (operator-driven) — it's a coordinated cross-service
  shard-atom migration, so the audit is the foundation gate.
