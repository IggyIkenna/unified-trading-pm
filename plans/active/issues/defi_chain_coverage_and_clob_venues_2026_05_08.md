---
title:
  "DeFi chain coverage cross-service audit + Hyperliquid L1 chain identity phantom + CLOB-on-chain venue instrument
  definitions (Hyperliquid / Lighter / Pacifica / Extended) — manifest rows + per-archetype chain constraints"
created: 2026-05-08
author: ikenna
source:
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_chain_data.py:58-292
    (CHAIN_CONFIGS canonical EVM + Solana)
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:46 (HYPERLIQUID_API source
    listed; chain identity unspecified)
  - unified_api_contracts/internal/domain/strategy_service/venue_set_variants.py:1-10 (_BASE_VENUES_BY_ASSET_GROUP — no
    per-archetype chain constraint)
  - execution-service/execution_service/service_config.py (CHAIN_RPC_TEMPLATES consumer)
  - plans/active/dex_perp_onboarding_handover_2026_05_07.HANDOVER.md:137-150 (Lighter / Pacifica / Extended status;
    Extended Starknet RPC missing)
  - market-tick-data-service commits 10aa715 / 51fecd5 / d898985 / fc53a97 (Lighter + Pacifica adapters)
  - operator directive 2026-05-08:
      "Hyperliquid comes to mind, even though it's a central limit order book and the data types are more like century
      or the book too. I believe it's still a physical chain that we have to move money around. If we're doing
      omni-chain transfers, for example, and we don't know about the protocol dynamics... we need to know what chains
      they are and that we need what ID is set up"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# DeFi chain coverage + CLOB-on-chain venue instrument definitions

> **Severity**: P1 — affects May 23 cutover for omni-chain transfer / smart-order-routing decisions; not strictly
> blocking if first archetypes only trade on canonical-EVM chains, but blocks any cross-chain capital movement
> (Hyperliquid bridges → Arbitrum, Solana via Pacifica, Starknet via Extended). **Blast radius**: UAC (chain enum + RPC
> template SSOT) + execution-service (cross-chain transfers + bridge routing) + features-onchain-service +
> strategy-service (per-archetype chain constraints) + MTDS (per-chain market data) + instruments-service (CLOB-venue
> instrument discovery) + position-balance-monitor (per-chain custody addresses). **Suggested owner**:
> `defi_master_2026_05_07.plan.md` Phase X (new) — coordinates with
> `dex_perp_onboarding_handover_2026_05_07.HANDOVER.md` for the CLOB-venue tail.

## What I found

### Q1 — DeFi chain coverage: PARTIAL — Hyperliquid L1 chain identity missing from UAC enum

**UAC SSOT** at
[\_defi_chain_data.py:58-292](../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_chain_data.py#L58-L292)
defines:

- **Tier 1 (core)**: Ethereum (1), Optimism (10), Base (8453), Arbitrum (42161)
- **Tier 2 (major non-ETH)**: BSC (56), Polygon (137), Avalanche (43114), Gnosis (100)
- **Tier 3 (L2s/zkEVMs)**: zkSync (324), World, Abstract (2741), Mode (34443), Ink (57073), Linea (59144), Blast
  (81457), Scroll (534352), Zora (7777777)
- **Tier 4 (public RPC)**: Fantom (250), Metis (1088), Moonbeam (1284), Mantle (5000), Celo (42220), Aurora (1313161554)
- **Solana**: separate `SOLANA_RPC_TEMPLATES` dict (line 354-362)
- **Testnets**: 11 testnet entries

**Per-service chain awareness**:

- **execution-service**: imports `CHAIN_RPC_TEMPLATES` directly from UAC; has all 16 EVM chains + Solana available.
- **features-onchain-service**: no explicit hardcoded chain list; imports from UAC adapters.
- **MTDS**: per-handler chain coverage varies (gas_fee_handler covers 14 chains; lending_indices covers
  protocol-specific chain subsets).
- **strategy-service**:
  [\_BASE_VENUES_BY_ASSET_GROUP at venue_set_variants.py:1-10](../../../unified_api_contracts/internal/domain/strategy_service/venue_set_variants.py#L1-L10)
  lists DeFi venues (`aave_v3, uniswap_v3, lido`) but **NO per-archetype chain constraint** — strategy archetypes can't
  currently declare "this archetype trades only on Arbitrum + Base."

**Hyperliquid specific gap**: present in UAC `DeFiDataSource` enum at `_defi.py:46` (as `HYPERLIQUID_API`) and
execution-service has a connector — but **Hyperliquid's L1 chain identity is NOT in the EVM chain enum**. It's a
separate L1 (HyperEVM bridges to Arbitrum). Implications:

- For omni-chain transfers (move USDC from Arbitrum → Hyperliquid for perp margin), execution-service has no canonical
  "Hyperliquid chain" to route to. Bridge logic is currently implicit in the Hyperliquid connector itself rather than a
  first-class chain entity.
- For smart-order-routing across venues that span chains (Hyperliquid perp ↔ Aave Arbitrum collateral), the routing
  layer can't reason about chain hops.
- For position-balance-monitor: a balance "on Hyperliquid" has no canonical chain_id, so reconciliation between
  Hyperliquid native balances + Arbitrum-bridged USDC is opaque.

### Q2 — CLOB-on-chain venue instrument definitions: PARTIAL — UAC-registered but instrument-discovery gaps

Four CLOB-on-chain venues per
[dex_perp_onboarding_handover_2026_05_07.HANDOVER.md:137-150](../dex_perp_onboarding_handover_2026_05_07.HANDOVER.md#L137-L150):

| Venue           | Chain                         | UAC `venue_mapping.py` | Live MTDS adapter                         | Instrument-service discovery | Manifest rows |
| --------------- | ----------------------------- | ---------------------- | ----------------------------------------- | ---------------------------- | ------------- |
| **Hyperliquid** | HyperEVM L1 + Arbitrum bridge | ✓                      | ✓ (perp + spot)                           | ⚠ check                     | ⚠            |
| **Lighter**     | zkSync Era                    | ✓ (line 137)           | ✓ ohlcv_1m shipped May 7 (commit 10aa715) | ⚠ check                     | ✓ (1440/day)  |
| **Pacifica**    | Solana                        | ✓ (line 137)           | ✓ kline shipped May 7 (commit 51fecd5)    | ⚠ check                     | ✓ (~4000/day) |
| **Extended**    | Starknet                      | ✓ (line 137)           | ✗ MISSING (handover line 144)             | ✗ no historical adapter      | ✗             |

**Concrete gaps**:

- **Extended**: blocked on missing Starknet RPC template in `CHAIN_RPC_TEMPLATES` (handover line 142) AND missing
  historical OHLCV adapter (line 144). Code-registered in UAC but no production data flowing.
- **All 4**: it's unclear from this audit whether instruments-service has explicit instrument-discovery adapters for
  these 4 venues that produce per-instrument rows in the manifest, vs whether MTDS adapters write market data rows
  without instrument-service catalog rows. The user's observation: "I don't see the management definitions for CeFi or
  DeFi" — likely correct for instrument-discovery (catalog) layer despite UAC venue_mapping presence.

The catalog-presence question matters because the writegate Phase 3.D.5 v2 expected-universe enumerator (per
`mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08.md` and writegate plan) derives the manifest's expected
universe from `instruments-service catalog × dates × data_types`. If Lighter/Pacifica/Hyperliquid/Extended don't have
instrument-discovery rows, their MTDS captured rows have no canonical "expected universe" to compare against — coverage
% undefined at fixture grain.

### Q3 — Asset_group classification: PARTIAL — CLOB-on-chain falls between defi/cefi

These venues are legitimately hybrid: they have on-chain settlement (DeFi-like) but operate central-limit-order-book
matching (CeFi-like). UAC's `VENUES_BY_ASSET_GROUP` requires choosing one. Current state per session memory + handover:

- Hyperliquid: ambiguous — sometimes treated as DeFi, sometimes as cefi-style perp.
- Lighter / Pacifica / Extended: per recent commits, classified as **DeFi** for instrument discovery, but per
  market-data routing they may sit under cefi data-type list (per memory entry on `cefi DATA_TYPES_BY_ASSET_GROUP`
  adding `ohlcv_1m` for Lighter).

This dual classification creates manifest-row-key-shape ambiguity: per CLAUDE.md "Per-asset-group shard-key matrix,"
DeFi rows include `chain` as a first-class axis; CeFi rows don't. Mis-classification → wrong shard atom → manifest
drift.

## Why it matters

- **Cross-chain capital flow blocked**: omni-chain transfer from Aave Arbitrum collateral → Hyperliquid perp margin
  requires explicit chain identity for both endpoints. With Hyperliquid's L1 missing from the chain enum,
  execution-service routes implicitly (hardcoded bridge logic) — works today but breaks for any new cross-chain pair.
- **Smart-order-routing blind**: a strategy that wants to compare Hyperliquid perp price ↔ Lighter perp price ↔
  Pacifica perp price (cross-DEX dispersion arb per session memory) needs canonical chain identities for all three
  venues to reason about settlement layers.
- **Position-balance-monitor reconciliation broken**: a USDC balance on Hyperliquid is custodied on a different chain
  than Aave-Arbitrum-collateralized USDC. Without canonical chain_ids, position math is opaque and audit trails
  reference free-text "Hyperliquid" rather than chain_id=1337-or-whatever.
- **Strategy-service per-archetype chain constraints**: archetypes in `master_to_live_defi_2026_05_23.plan.md`
  (carry_staked_basis lead + leveraged_funding_arb) may need explicit chain-allowed-list. Without it, a strategy could
  trade against a venue on a chain we don't have RPC access to.
- **CLOB-venue instrument-catalog vacuum**: writegate v2 enumerator can't derive expected universe for these venues if
  instruments-service doesn't enumerate them. Coverage % at the data-status drilldown is undefined for Lighter/Pacifica.

## Recommended decision

### Phase 1 — UAC Hyperliquid L1 chain entry + non-EVM chain taxonomy

Add `HYPERLIQUID` (and potentially `STARKNET`) to UAC's chain enum. For non-EVM chains, the existing EVM-centric
`chain_id: int` model needs extension:

```python
class ChainKind(StrEnum):
    EVM = "evm"
    SOLANA_SVM = "solana_svm"
    HYPERLIQUID_L1 = "hyperliquid_l1"
    STARKNET_CAIRO = "starknet_cairo"
    SUI_MOVE = "sui_move"
    APTOS_MOVE = "aptos_move"

@dataclass(frozen=True)
class ChainConfig:
    name: ChainName
    kind: ChainKind
    chain_id: int | None    # EVM only; None for non-EVM
    native_id: str           # EVM hex chain_id, Solana cluster, Starknet network
    rpc_templates: list[str]
    bridge_to: list[ChainName]  # which chains this chain has canonical bridges to (Hyperliquid → Arbitrum, etc.)
```

Add `bridge_to` graph so smart-order-routing can plan multi-hop transfers.

### Phase 2 — instruments-service CLOB-venue discovery adapters

For each of the 4 venues, ensure instruments-service writes per-instrument catalog rows (instrument_id, base/quote,
contract size, tick size, min/max order size, listing date, delisting date). Today's gap (per Q2 audit): need to verify
per venue. If missing, ship discovery adapters paralleling existing CeFi-spot patterns:

- Hyperliquid: `/info` endpoint returns per-perp metadata.
- Lighter: SDK `get_markets()` exposes 170 perps with config.
- Pacifica: `/markets` endpoint.
- Extended: blocked on Starknet RPC template — Phase 2.5.

### Phase 3 — strategy-service per-archetype chain constraints

Extend strategy archetype declaration with `allowed_chains: list[ChainName]`. Pre-flight gate: archetype targeting chain
X requires `ChainName.X in CHAIN_CONFIGS` AND `ChainName.X in execution-service.CHAIN_RPC_TEMPLATES` AND adequate
balance on the chain in position-balance-monitor.

### Phase 4 — Asset_group disambiguation for CLOB-on-chain venues

Workspace decision: declare CLOB-on-chain venues as a hybrid third class. Two options:

- (a) New asset_group `clob_dex` with shard-key matrix:
  `(asset_group=clob_dex, chain, venue, data_type, instrument_type, instrument_id, day)` — chain is a first-class axis
  like defi.
- (b) Keep DeFi classification + extend cefi-style data_types (ohlcv_1m, etc.) to apply to defi shard-key rows.

Option (a) is more honest but creates a 6th asset_group. Operator decision; default = (a).

### Phase 5 — Extended unblocked

Add Starknet RPC template to UAC `CHAIN_RPC_TEMPLATES`; ship historical OHLCV adapter; populate manifest. Per handover
Item C (lifted from `consolidated_defi_data_pipeline_2026_04_15.plan.md` archive). Owns: defi_master.

## Acceptance criteria

- [ ] Hyperliquid L1 + Starknet added to UAC chain enum with `kind` + `native_id` + `bridge_to` graph.
- [ ] All 4 CLOB-on-chain venues have instruments-service discovery adapters writing per-instrument catalog rows.
- [ ] Strategy archetype `allowed_chains` constraint enforced at pre-flight; out-of-allowed-chain trade attempts → typed
      error.
- [ ] Workspace decision on CLOB-on-chain asset_group classification; manifest row_keys aligned to chosen shard-atom.
- [ ] Extended Starknet RPC template + historical OHLCV adapter shipped.
- [ ] writegate v2 expected-universe enumerator handles CLOB-on-chain venues correctly (catalog × dates).
- [ ] Smoke test: smart-order-routing across Aave-Arbitrum collateral → Hyperliquid perp margin succeeds with explicit
      chain hops.
- [ ] Smoke test: cross-DEX perp dispersion arb (Lighter ↔ Pacifica ↔ Hyperliquid) computes correctly with all 3
      venues' canonical chain identities.

## Open questions

- For Hyperliquid: is the bridge-to-Arbitrum the only canonical custody route, or do other chains support it? Affects
  `bridge_to` graph.
- For Pacifica: Solana has different gas/fee semantics — does the perp-margin currency routing match the
  SOLANA_RPC_TEMPLATES treatment?
- For Extended: Starknet's account model is fundamentally different from EVM (account abstraction native). Does our
  position-balance-monitor abstraction hold?
- Are the UAC `VENUES_BY_ASSET_GROUP` keys for these 4 venues already in place, or did the recent additions (May 7) only
  touch market_data_categories? Per memory entry on UAC@e890022 (cefi DATA_TYPES_BY_ASSET_GROUP added ohlcv_1m), the
  routing fix shipped — need to verify VENUES_BY_ASSET_GROUP is consistent.
- Coordination with `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md`: that plan touches the venue
  matrix; should the CLOB-on-chain asset_group decision fold into it?
