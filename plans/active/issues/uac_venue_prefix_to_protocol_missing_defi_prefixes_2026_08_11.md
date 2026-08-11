---
doc_type: issue
title: >-
  UAC VENUE_PREFIX_TO_PROTOCOL does not yet carry 10 real DeFi venue prefixes (PHOENIX/KAMINO/SOLEND/MARGINFI/
  JITO/MARINADE/SOLBLAZE/LIDO/ETHERFI/EIGENLAYER), so the MTDS prefix-map swap had to keep a local supplement —
  and extending the UAC map naively is unsafe because of the adapter-key auto-gen loop (PHOENIX-SOLANA exclusion)
summary: >-
  The cross-cutting batch-2 prefix-map-mirror item ("swap the hand-maintained MTDS _instruments_metadata.py
  venue-prefix-map mirror for a direct import of UAC VENUE_PREFIX_TO_PROTOCOL") was shipped by deriving
  _PROTOCOL_TO_VENUE_PREFIX from UAC's VENUE_PREFIX_TO_PROTOCOL (first-wins inversion). But UAC's map does not yet
  carry 10 real IS venue prefixes that MTDS needs — PHOENIX, KAMINO, SOLEND, MARGINFI, JITO, MARINADE, SOLBLAZE,
  LIDO, ETHERFI, EIGENLAYER — so a 10-entry local supplement had to remain in _instruments_metadata.py. Extending
  UAC's VENUE_PREFIX_TO_PROTOCOL to absorb them is NOT a mechanical registry edit: that map feeds the adapter-key
  auto-gen loop in unified_api_contracts/registry/venue_adapter_keys.py:388, which would generate a new
  PHOENIX-SOLANA entry in VENUE_TO_ADAPTER_KEY — contradicting that venue's deliberate exclusion
  (venue_adapter_keys.py:313) and flipping is_venue_executable/VENUES_WITH_REFERENCE_ADAPTER membership. Separately,
  5 codex docs still reference the deleted CANONICAL_VENUE_TO_ADAPTER symbol.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, defi, uac, registry, venue-prefix, mtds, codex-doc, stale-doc]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
  ]
created: "2026-08-11"
author: ikennaigboaka [slot-8]
parent_epic: instruments_master
assigned_vm: planning
locked_by:
locked_since:
---

## What I found

Working the cross-cutting batch-2 prefix-map-mirror item
(`market-tick-data-service` `_instruments_metadata.py`), I swapped the hand-maintained
`_PROTOCOL_TO_VENUE_PREFIX` mirror for a derivation from UAC's `VENUE_PREFIX_TO_PROTOCOL` (the SSOT, inverted
first-wins so canonical underscore spellings like `VELODROME_V2`/`TRADER_JOE_V2` beat UAC's legacy glued aliases
`VELODROMEV2`/`TRADER_JOEV2`). Two findings fell out:

1. **UAC's `VENUE_PREFIX_TO_PROTOCOL` is missing 10 real DeFi venue prefixes that MTDS relies on.** The protocols
   PHOENIX, KAMINO, SOLEND, MARGINFI, JITO, MARINADE, SOLBLAZE, LIDO, ETHERFI and EIGENLAYER all map to venue
   prefixes instruments-service actually writes (`PHOENIX`, `KAMINO`, `SOLEND`, `MARGINFI`, `JITO`, `MARINADE`,
   `SOLBLAZE`, `LIDO`, `ETHERFI`, `EIGENLAYER` — confirmed against UAC `VENUE_TO_ADAPTER_KEY` /
   `defi_venue_capabilities.py` / `capability_declarations/_defi.py`), but none is registered in
   `VENUE_PREFIX_TO_PROTOCOL`. So the MTDS swap had to keep a 10-entry local supplement, which is exactly the
   hand-mirror drift risk this batch item exists to eliminate — just a smaller one.

2. **Extending `VENUE_PREFIX_TO_PROTOCOL` is not a mechanical edit.** `venue_adapter_keys.py:388` loops every
   `(prefix, protocol)` in `VENUE_PREFIX_TO_PROTOCOL` and auto-generates `{PREFIX}-{CHAIN}` entries into
   `VENUE_TO_ADAPTER_KEY`. All the supplement venues already exist there **except `PHOENIX-SOLANA`**, which is
   deliberately excluded (comment at `venue_adapter_keys.py:313` documents the operator rulings that dropped Solana
   DEX perp venues). Adding `"PHOENIX": "phoenix"` would re-add `PHOENIX-SOLANA` to `VENUE_TO_ADAPTER_KEY` and flip
   `is_venue_executable("PHOENIX-SOLANA")` + `VENUES_WITH_REFERENCE_ADAPTER` membership — a registry-semantics change
   beyond MTDS's need. (All other 9 prefixes' `-SOLANA`/`-ETHEREUM` venues already exist, so their auto-gen is a
   no-op; PHOENIX is the load-bearing exception.)

Adjacent finding: **5 codex docs still name the deleted `CANONICAL_VENUE_TO_ADAPTER` as the current adapter
registry** (`codex/02-data/instrument-pipeline-defi.md`, `codex/02-data/venue-availability.md`,
`codex/02-data/availability-manifest-and-data-status.md`, `codex/04-architecture/instrument-universe-registry-consolidation.md`,
`codex/04-architecture/solana-defi-coverage.md`). The symbol is confirmed gone from instruments-service; the current
mechanism is UAC `VENUE_TO_ADAPTER_KEY`. (This task fixed the one live code reference — the stale UI comment in
`unified-trading-system-ui/lib/types/defi.ts`.)

## Why it matters

- The whole point of the prefix-map-mirror item is "venue truth lives in UAC, consumers import it". As long as
  `VENUE_PREFIX_TO_PROTOCOL` is incomplete, MTDS keeps a hand supplement that can silently drift from IS's real
  prefixes — the exact failure this batch eliminates, just smaller.
- The PHOENIX auto-gen side effect means the fix is a UAC-registry design decision, not a mechanical add: someone
  must decide whether `PHOENIX-SOLANA` belongs back in `VENUE_TO_ADAPTER_KEY` (and with which adapter key) or stays
  excluded.
- The stale codex docs mislead future workers (they were cited as evidence in this investigation).

## Recommended decision

Consolidate the supplement into UAC deliberately, after resolving the PHOENIX side effect. Bounded, worker-determinable
items below become backlog tasks via PlanRegenLoop.

## Todos

- [ ] [CODE] P2. Add the 10 missing DeFi venue prefixes (PHOENIX, KAMINO, SOLEND, MARGINFI, JITO, MARINADE, SOLBLAZE,
      LIDO, ETHERFI, EIGENLAYER) to UAC `VENUE_PREFIX_TO_PROTOCOL`
      (`unified_api_contracts/registry/venue_adapter_keys.py`), resolving the adapter-key auto-gen side effect first —
      decide PHOENIX-SOLANA's disposition (re-add to `VENUE_TO_ADAPTER_KEY` with an explicit adapter key vs. keep it
      excluded via an explicit guard/sentinel so the auto-gen loop cannot silently re-add it), then verify the auto-gen
      loop (line 388) produces no new unintended `VENUE_TO_ADAPTER_KEY` entries for the other 9. Repo: unified-api-contracts.
      Done when: `VENUE_PREFIX_TO_PROTOCOL` carries all 10, the auto-gen loop's output is verified unchanged-or-intended
      (esp. no surprise PHOENIX-SOLANA entry), and `unified-api-contracts` `quality-gates.sh` is green.
- [ ] [CODE] P3. Once UAC carries the 10 prefixes, drop the local supplement in MTDS
      `market_tick_data_service/cli/handlers/_instruments_metadata.py` (the `_PROTOCOL_TO_VENUE_PREFIX.update({...})`
      block) so `_PROTOCOL_TO_VENUE_PREFIX` is a pure derivation from `VENUE_PREFIX_TO_PROTOCOL`. Repo:
      market-tick-data-service. Done when: the supplement block is gone and the unit tests in
      `tests/unit/test_instruments_metadata_loader.py` (incl. the kamino/solend/marginfi/lido/etherfi/eigenlayer/
      phoenix assertions) still pass.
- [ ] [SCRIPT] P3. Update the 5 codex docs that reference the deleted `CANONICAL_VENUE_TO_ADAPTER`
      (`codex/02-data/instrument-pipeline-defi.md`, `codex/02-data/venue-availability.md`,
      `codex/02-data/availability-manifest-and-data-status.md`, `codex/04-architecture/instrument-universe-registry-consolidation.md`,
      `codex/04-architecture/solana-defi-coverage.md`) to point at the current UAC `VENUE_TO_ADAPTER_KEY` mechanism,
      deleting the dead symbol name rather than updating it. Repo: unified-trading-pm.

## Progress Log

- **2026-08-11 (slot 8)**: Filed from the cross-cutting batch-2 prefix-map-mirror item
  (`cross_cutting_satellite_ao_dispatch_batch2-8ad33c119efd`). MTDS swap shipped
  (`market-tick-data-service@b5310181`, UI comment fix `unified-trading-system-ui@813d79ea`). This doc tracks the
  residual: UAC-side consolidation (todo 1) + MTDS supplement removal once UAC lands (todo 2) + stale codex-doc sweep
  (todo 3).
