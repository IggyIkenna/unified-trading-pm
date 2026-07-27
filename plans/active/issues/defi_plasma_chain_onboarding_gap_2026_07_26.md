---
doc_type: issue
title:
  "Plasma L1 (XPL, chain_id 9745) is a large, real, currently-active DeFi market with ZERO chain registration anywhere
  in this codebase — Aave alone has >$6.5B deposits there"
summary: >-
  While resolving `defi_turbo_api_hides_real_captured_data_2026_07_07.md`'s open "which Plasma chain" ambiguity (UAC's
  `AAVE-PLASMA`/`FLUID-PLASMA` placeholder venues carried a comment claiming "Polygon Plasma bridge-side" — the old,
  dead 2018-2020 Polygon Plasma bridge), real-world verification found the comment was simply wrong: this is the 2025
  Tether-backed Plasma L1 (XPL, EVM chain_id 9745, mainnet launched 2025-09-25). Aave went live on Plasma the same day
  with over $6.5B in deposits in the first week alone, making it Aave's 2nd-largest deployment by TVL after Ethereum
  mainnet — this is not a speculative or dead chain, it is one of the largest current DeFi lending markets in existence.
  Fluid (Instadapp) also has a confirmed live deployment on Plasma. Despite this scale, `unified-api-contracts` has ZERO
  chain registration for Plasma anywhere: no `MAINNET_CHAIN_IDS` entry, no `CHAIN_GENESIS_DATES` entry, no RPC
  configuration, and `market-tick-data-service` has no capture adapter for it. The identity-resolution fix itself
  (correcting the wrong "Polygon Plasma bridge" comment, cited with the real-world evidence) is out of scope here —
  already shipped (`unified-api-contracts@<see defi_turbo_api_hides_real_captured_data_2026_07_07.md's todo>`) — this
  doc is specifically the follow-up for the much larger "we're not tracking this market at all" gap.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [defi, plasma, chain-onboarding, aave, fluid, data-correctness, new-venue]
related:
  [
    /plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
drift_direction: advance-code
depends_on: []
source:
  "Found 2026-07-26 (slot-11, data_engineering) while resolving the Plasma-chain-identity VERIFY todo in
  defi_turbo_api_hides_real_captured_data_2026_07_07.md — real-world web-search verification of Aave's and Fluid's
  actual Plasma deployments, not asserted from code alone."
resolved_by:
locked_by:
locked_since:
---

# Plasma L1 is a real, large, live DeFi market with zero chain onboarding here

## What I found

1. **Real-world verification** (web search, 2026-07-26): Aave launched on Plasma (the 2025 Tether-backed L1, ticker XPL)
   on 2025-09-25, attracting over $6.5B in deposits within the first week — as of the most recent coverage found, Plasma
   is Aave's **2nd-largest deployment by TVL**, behind only Ethereum mainnet, ahead of Arbitrum. Fluid (Instadapp) is
   separately confirmed (via its DefiLlama protocol listing) to have a live deployment on Plasma as one of its ~6 active
   chains.
2. **Plasma's technical identity**: EVM-compatible L1, mainnet chain_id **9745** (testnet 9746), per
   chainlist.org/ChainList's public registry.
3. **Zero registration in this codebase**: grepped `unified-api-contracts/unified_api_contracts/registry/` exhaustively
   — `chain_env.py`'s `MAINNET_CHAIN_IDS`/`TESTNET_CHAIN_IDS`/`CHAIN_GENESIS_DATES` dicts have no `"PLASMA"` key at all.
   `AAVE-PLASMA`/`FLUID-PLASMA` venue constants exist (`venue_constants.py`) and are declared in `ALL_DEFI_VENUES` with
   `phase="pipeline"` (`defi_venues.py`), but with no chain_id/genesis-date backing, and `market-tick-data-service` has
   no Plasma-chain capture adapter — the venue strings exist as placeholders only, never wired to anything real.
4. **Why this wasn't caught earlier**: the pre-existing code comment on these placeholder entries claimed they referred
   to the OLD 2018-2020 Polygon Plasma bridge (dead infrastructure, no active DeFi deployments) — plausible-sounding but
   wrong, and nobody had checked. That mislabeling likely suppressed any prior "should we track this" investigation,
   since "dead bridge" reads as obviously not worth pursuing while "large, currently the 2nd-biggest Aave market" reads
   very differently.

## Why it matters

This is a genuine market-coverage gap on the scale of the AAVE_V3-ARBITRUM/POLYGON "hidden data" findings elsewhere in
this exact plan thread, except here the data isn't hidden — it was never captured at all, because nobody knew this was a
real, large, current chain. $6.5B+ in Aave deposits alone is a material DeFi market this system currently has zero
visibility into.

## Recommended decision

This doc stops at diagnosis + scoping, per the workspace's dispatch-scope rule (chain onboarding + capture-adapter
build-out is real feature work, not a bounded audit fix) — splitting into properly-sized follow-up todos rather than
attempting the full build here:

- [x] ✅ [CODE] P1. **UAC chain registration.** Add `"PLASMA": 9745` to `MAINNET_CHAIN_IDS`, a genesis date to
      `CHAIN_GENESIS_DATES` (mainnet launch 2025-09-25, or earlier if a public testnet/beta phase predates it —
      re-verify before committing to the exact date), and (once genesis lands) real `PROTOCOL_LAUNCH_DATES` entries for
      `("PLASMA", "AAVE")` (2025-09-25, well-sourced — see this doc) and `("PLASMA", "FLUID")` (date not yet confirmed —
      needs its own block-explorer/DefiLlama audit before adding). Repo: unified-api-contracts. Done when:
      `MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES` invariant (STEP 5.72) still holds with PLASMA included,
      `test_protocol_launch_dates_chain_known_to_genesis_ssot` and `test_protocol_launch_after_chain_genesis` pass,
      `quality-gates.sh` green. — **DONE unified-api-contracts@2483e157** `registry/chain_env.py`:
      `MAINNET_CHAIN_IDS["PLASMA"]     = 9745`, `CHAIN_GENESIS_DATES["PLASMA"] = "2025-09-25"`,
      `PROTOCOL_LAUNCH_DATES[("PLASMA", "AAVE")] =     "2025-09-25"`. Re-verified the date via live web search (not
      assumed from the doc): plasma.org's own network-configuration docs + Bitget/TheDefiant coverage confirm Mainnet
      Beta + XPL TGE launched 2025-09-25, chain_id 9745 — "Mainnet Beta" is Plasma's own launch branding, not a separate
      earlier phase, so no earlier date applies. `("PLASMA", "AAVE")` removed from
      `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`; `("PLASMA", "FLUID")` stays pending (unconfirmed date, per this todo's
      own scope — that's the P2 scoping todo below). All 4 named/sibling test files green (72 tests:
      `test_protocol_launch_dates.py` ×20, `test_chain_genesis_dates.py` ×9, `test_chain_env.py` ×43).
- [ ] [CODE] P2. **Capture adapter scoping.** Determine what data source is actually reachable for Plasma-chain
      Aave/Fluid market data (a Goldsky/The Graph subgraph, direct RPC + known contract addresses, or a DefiLlama-style
      aggregator) — this needs its own investigation, not an assumption that an existing subgraph-pattern adapter (like
      the EULER_V2 Goldsky adapter) directly transfers. Repo: market-tick-data-service. Done when: a concrete
      data-source plan is documented (endpoint/API, auth requirements if any, expected schema) as the basis for a
      properly-scoped capture-wiring todo — this todo's done-when is the SCOPING, not the implementation.
- [ ] [CODE] P3. Once the above land, wire real capture for `AAVE-PLASMA` and (once its launch date is confirmed)
      `FLUID-PLASMA`, verify real rows land in the manifest, and update `defi_venues.py`'s phase from `"pipeline"` to
      `"live"` for whichever venues have working, verified capture.

## Codex SSOTs

None directly on point — this is a UAC-registry-internal chain-onboarding gap, not a cross-cutting data pipeline
contract. `/codex/02-data/defi-canonical-naming-ssot.md` may be relevant once capture wiring actually starts (venue
naming conventions).
