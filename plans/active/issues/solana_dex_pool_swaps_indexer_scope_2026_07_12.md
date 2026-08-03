---
doc_type: issue
title: Solana dex_pool_swaps (ORCA/RAYDIUM) has no existing data source — new-capability scope
summary: >
  mvp_backfill_defi_onchain_v10_2026_06_27.md G1.6 found that dex_pool_swaps for ORCA and RAYDIUM cannot be filled by
  any existing MTDS code path: SolanaDefiHandler only captures dex_pool_state (current pool/vault snapshots via REST),
  DexSwapsHandler's Solana routing always resolves to no subgraph (get_subgraph_id returns None for these venues, since
  they are REST-API venues with no subgraph), and the ORCA/RAYDIUM live WS connectors (orca_defi_ws.py /
  raydium_defi_ws.py) are Jupiter-quote PRICE pollers, not swap-event capture. Filling this data_type genuinely needs
  new capability - an on-chain Solana swap-event indexer - not a VM launch or a config change. This doc scopes that
  capability (design starting point + a concrete, reusable precedent already in this codebase) so a future plan can pick
  it up sized correctly, rather than attempting it inline in a 1-hour backfill-verification task.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, solana, dex-pool-swaps, new-capability, scoping, orca, raydium]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/solana_defi_fake_history_snapshot_2026_06_17.md,
  ]
created: 2026-07-12
parent_epic: mtds_mdps_master
priority: P2
source: [plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md G1.6, slot-2 2026-07-12]
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12
locked_by:
context_scope:
  [
    /plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/archive/issues/solana_defi_fake_history_snapshot_2026_06_17.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
  ]
resolved_by:
---

# Solana dex_pool_swaps (ORCA/RAYDIUM) — new-capability scope

## What I found

Confirmed (re-reading the code, not re-deriving the G1.6 finding): three existing paths were checked and none produce
individual swap events for ORCA/RAYDIUM on Solana.

1. `market_tick_data_service/cli/handlers/solana_defi_handler.py` (`SolanaDefiHandler`,
   `--operation collect-solana-defi`) via `_solana_defi_fetch.py` captures **`dex_pool_state` only** — periodic REST
   snapshots of the current pool/vault set (`fetch_orca`, `fetch_raydium`, `fetch_kamino_vault`). No per-trade/per-swap
   output.
2. `DexSwapsHandler` (the generic EVM-chain swap handler) resolves protocol→chain via UAC
   `get_supported_chains_for_protocol()`, a `SUBGRAPH_IDS`-only lookup. ORCA/RAYDIUM have no subgraph entry (they're
   REST-API venues, not subgraph-indexed) so this always returns `[]` and the per-protocol loop `continue`s — dead code
   for these two venues specifically.
3. `market_tick_data_service/live/connectors/{orca,raydium}_defi_ws.py` — these are Jupiter
   `lite-api.jup.ag/swap/v1/quote` PRICE-QUOTE pollers (emit a price tick per poll interval), not swap-transaction
   capture. Confirmed by reading `orca_defi_ws.py`'s docstring + poll loop directly — no swap/trade event is ever parsed
   or emitted.

**Conclusion: building `dex_pool_swaps` for these two venues requires a genuine on-chain Solana swap-event indexer**
(parse ORCA Whirlpool / Raydium AMM swap instructions from transaction logs), not a config fix, VM relaunch, or
connector rewire.

## A reusable precedent already exists in this codebase

`market_tick_data_service/scripts/build_drift_v2_sig_index.py` (657 lines) already solves HALF of this exact problem for
a different Solana program (Drift V2 perps): it walks Helius RPC `getSignaturesForAddress` for a program address from
HEAD backwards, chunk-flushing `(signature, slot, blockTime)` tuples to GCS parts (`_index/<program>_sig_index_parts/`)
with `--resume` support seeded from the oldest already-indexed signature — avoiding the OOM class this codebase hit
before (tens of millions of sigs held in RAM). This pattern generalizes directly:

- **Program addresses already registered in UAC**
  (`unified_api_contracts/registry/capability_declarations/_defi_chain_data.py`):
  `raydium.program_id = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"`,
  `orca.program_id = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"` — no new address discovery needed.
- **What `build_drift_v2_sig_index.py` does NOT do** (the other half of this capability, not yet built anywhere): it
  only indexes signatures + blockTime, it does not fetch/parse the actual transaction to extract a swap event (amounts,
  direction, pool/pair, price). A dex_pool_swaps indexer needs a SECOND stage: for each indexed signature, fetch the
  full transaction (`getTransaction` via Helius), decode the Whirlpool/Raydium AMM swap instruction's account + data
  layout into `(pool, base_amount, quote_amount, side, price)`, and write via
  `ManifestWriter.record_captured(..., data_type="dex_pool_swaps", ...)` following the same
  `pipeline_mode`/honest-absence conventions the rest of this asset_group already uses.

## Why this is scoped as its own capability, not folded into a backfill task

- It's a multi-stage build (sig-index walk → per-tx fetch+decode → manifest write), each stage with its own failure
  modes (Helius rate limits, instruction-layout parsing correctness, OOM-safety at scale) — the same "smoke-first, don't
  fan out blind" caution that governs every other new-venue integration in this workspace.
- Instruction decoding for an AMM program is protocol-specific (Whirlpool's swap instruction layout differs from
  Raydium's) — this is genuinely new adapter code per venue, not a shared script extension.
- `mvp_backfill_defi_onchain_v10_2026_06_27.md`'s own G2 gate text already excludes this (`dex_pool_swaps` for
  ORCA/RAYDIUM is a known, separately-tracked gap — see that plan's G1.6 + Progress Log entries) — closing this doc's
  scope is what lets that gate's language stay accurate rather than silently drop the two venues from consideration.

## Recommended next step

File a dedicated implementation plan (repo: `market-tick-data-service`) when this becomes a priority, sized as
`brand-new` (1.0× estimate calibration, per this workspace's estimate-calibration table) given it's genuinely new
adapter capability, not a refactor or config change. Suggested todo breakdown for that future plan:

1. Generalize `build_drift_v2_sig_index.py` (or extract its chunk-flush/resume core into a shared helper) to accept an
   arbitrary program address, so ORCA/RAYDIUM reuse the exact same OOM-safe sig-walk instead of a second bespoke
   implementation.
2. Build the per-signature transaction fetch + instruction decoder for Whirlpool swaps (start here — Orca's swap
   instruction layout is simpler/better-documented than Raydium's CLMM/CPMM variants).
3. Same for Raydium (may need to branch on AMM version — legacy AMM vs CLMM vs CPMM each have a different swap
   instruction shape).
4. Wire the decoded swap records through `ManifestWriter.record_captured(data_type="dex_pool_swaps")` with the same
   honest-absence conventions (`EXPECTED_PRE_VENUE_LAUNCH` pre-genesis, etc.) the `dex_pool_state` path already
   established.
5. Backfill VM launch + G2 re-verification once shipped.

## Open actions

- [ ] [DESIGN] P3. Author the dedicated implementation plan per the breakdown above, when this becomes a priority (repo:
      market-tick-data-service). Not urgent — `dex_pool_swaps` coverage for every OTHER defi venue is unaffected; this
      is a 2-venue gap on a data_type that already has non-zero coverage elsewhere.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - sole todo is 'author a dedicated implementation plan when this
  becomes a priority' — plan-authoring + prioritisation, both operator calls
