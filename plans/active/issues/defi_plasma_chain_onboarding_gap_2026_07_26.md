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
- [x] ✅ [CODE] P2. **Capture adapter scoping.** Determine what data source is actually reachable for Plasma-chain
      Aave/Fluid market data (a Goldsky/The Graph subgraph, direct RPC + known contract addresses, or a DefiLlama-style
      aggregator) — this needs its own investigation, not an assumption that an existing subgraph-pattern adapter (like
      the EULER_V2 Goldsky adapter) directly transfers. Repo: market-tick-data-service. Done when: a concrete
      data-source plan is documented (endpoint/API, auth requirements if any, expected schema) as the basis for a
      properly-scoped capture-wiring todo — this todo's done-when is the SCOPING, not the implementation. — **DONE
      2026-07-28 (slot-8)**: see "## Data-source scoping (P2 findings)" below. Verdict for both venues: **direct RPC via
      Alchemy, NOT a subgraph** — no Aave-V3-Plasma or Fluid subgraph exists (Fluid has no subgraph on ANY chain today);
      the existing RPC-fallback adapters (`lending_indices_handler.py`/`lending_indices_rpc.py` for Aave,
      `fluid_adapter.py`/`fluid_liquidity_resolver.py` for Fluid) already implement exactly this pattern for other
      chains (OPTIMISM precedent for Aave) — Plasma is a parameter addition to existing code, not new architecture. P3
      below is now re-scoped with the concrete addresses/files found.
- [ ] [CODE] P3. Wire real capture for `AAVE-PLASMA` and `FLUID-PLASMA` per the P2 scoping below: (1) add
      `9745: ChainConfig(rpc_url_template="https://plasma-mainnet.g.alchemy.com/v2/{api_key}", ...)` to `CHAIN_CONFIGS`
      in `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_chain_data.py` (repo:
      unified-api-contracts); (2) add a `"PLASMA"` entry to `_AAVE_V3_POOL_ADDRESSES` +
      `_AAVE_V3_DATA_PROVIDER_ADDRESSES` in `market_tick_data_service/cli/handlers/lending_indices_handler.py`, using
      FRESH-pulled addresses from `aave-address-book`'s `AaveV3Plasma.sol` (do not trust this doc's transcription —
      re-derive at implementation time); (3) confirm `FluidAdapter`/`fluid_liquidity_resolver.py` accept
      `chain="PLASMA"` without any Ethereum-only hardcoding (spot-check needed, not a rewrite); (4) once wired, verify
      real rows land in the manifest and update `defi_venues.py`'s phase from `"pipeline"` to `"live"` for whichever
      venues have working, verified capture. `FLUID-PLASMA`'s launch date must still be confirmed (per the P1 todo
      above) before its `PROTOCOL_LAUNCH_DATES` entry can land — that's a prerequisite for `FLUID-PLASMA` specifically,
      not for `AAVE-PLASMA`. Repos: unified-api-contracts, market-tick-data-service.

## 2026-07-31 partial progress (slot-3) — wiring done ((1)-(3)), live verification + phase flip still open ((4))

Picked up this doc's own P3 todo fresh. Completed the three wiring sub-items, live-verified as shipped:

- **(1) UAC `CHAIN_CONFIGS[9745]`** — added, with `reorg_depth=30`/`avg_block_time_s=1.0` (PlasmaBFT gives sub-second
  block production + Bitcoin-anchored fast finality per live web search — matches the existing fast-finality-L2
  convention already used for INK/WORLDCHAIN/UNICHAIN, not a slow-L1 value) and `native_gas_token="XPL"`. **Adjacent
  finding fixed in the same commit**: `VENUE_CHAIN_MAP[AAVE_PLASMA]`/`[FLUID_PLASMA]` in `venue_constants.py` were still
  mapped to the placeholder `"ethereum"` value from before real chain identity was resolved — corrected to `"plasma"`.
  Shipped: `unified-api-contracts@fb792b7a`, verified on `origin/live-defi-rollout`, full `quality-gates.sh` green
  (incl. the DeFi-address citation ratchet).
- **(2) MTDS `_AAVE_V3_POOL_ADDRESSES`/`_AAVE_V3_DATA_PROVIDER_ADDRESSES["PLASMA"]`** — added, addresses **re-verified
  live** via a fresh fetch of `bgd-labs/aave-address-book`'s `AaveV3Plasma.sol` (not trusted from this doc's earlier
  transcription, per its own instruction): `POOL=0x925a2A7214Ed92428B5b1B090F80b25700095e12`,
  `AAVE_PROTOCOL_DATA_PROVIDER=0xf2D6E38B407e31E7E7e4a16E6769728b76c7419F` — both byte-identical to the P2 scoping
  section's transcription below, so that transcription was accurate. Confirmed (per the P2 note) this data-provider
  address does NOT match the shared CREATE2 address used by ARBITRUM/OPTIMISM/POLYGON/AVALANCHE — documented inline.
- **(3) `FluidAdapter`/`fluid_liquidity_resolver.py` chain="PLASMA" spot-check** — done. `fluid_liquidity_resolver.py`
  needs no change (the `FLUID_LIQUIDITY_RESOLVER_ADDRESS` constant is already the same CREATE2 address across chains,
  confirmed in the P2 section below). **`fluid_adapter.py` DID have an Ethereum-only hardcode this spot-check caught**:
  `self.venue = "FLUID-ETHEREUM"` was a literal, unconditional on the `chain=` constructor arg — with Plasma capture
  dispatched, every `FLUID-PLASMA` row would have been mislabeled `FLUID-ETHEREUM` (wrong venue on every downstream row:
  instrument keys, error classification, manifest writes). Fixed to `self.venue = f"FLUID-{self.chain}"` (produces
  `FLUID-PLASMA` for `chain="PLASMA"`, preserves `FLUID-ETHEREUM` for the existing default). The actual
  `download_market_data()` RPC path (`_ensure_alchemy_client`, `BlockResolver(w3, chain=self.chain)`) was already
  chain-aware — no other hardcoding found. Note: a SEPARATE, unrelated dead-code path in the same file, `_ensure_web3()`
  / `self.web3`, DOES hardcode `eth-mainnet.g.alchemy.com` — left as-is because it has zero call sites anywhere in the
  adapter (confirmed via grep — `_ensure_web3()` is defined but never invoked), so it cannot affect Plasma capture;
  flagging here rather than silently leaving an unexplained hardcode in a reviewer's path. Shipped:
  `market-tick-data-service@6bcc5154`, verified on `origin/live-defi-rollout`, full `quality-gates.sh` green.

**(4) partially de-risked, still NOT done — the manifest-write leg specifically is what's left.** Initially the shell
had no `GCP_PROJECT_ID`/`AWS_ACCOUNT_ID` set (`get_secret_client()` fails closed:
`"GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in environment"`); found `gcloud config get-value project` already
resolves one (`central-element-323112`) and exporting it as `GCP_PROJECT_ID` unblocked Secret Manager. With that, ran a
real, live proof of the RPC-fallback fetch path in-process (NOT via the CLI, NOT writing to GCS/manifest):

- `AlchemyBaseClient(chain="PLASMA").get_web3("PLASMA")` connects and reports `chain_id=9745` (real Plasma RPC,
  correctly resolved via the new `CHAIN_CONFIGS[9745]` entry).
- `w3.eth.get_code(...)` on both re-verified addresses returns real deployed bytecode (Pool: 1841 bytes,
  AaveProtocolDataProvider: 7420 bytes) — not an EOA/empty address, confirming both addresses are live contracts on
  Plasma mainnet, not typos.
- Called `_fetch_aave_v3_via_rpc(handler, "PLASMA", ...)` directly for 2026-07-30 (today - 1, live at time of run):
  **returned 18 real reserve rows** (USDT0, USDe, sUSDe, WETH, GHO, WXPL, several Pendle PT- tokens, etc.) with genuine
  non-trivial `liquidity_index`/`liquidity_rate` values (e.g. USDT0 `liquidity_rate≈3.27%`, USDe`≈1.69%`) — this is the
  exact function + exact addresses this todo wired, proven against real on-chain state, not a mock.

**What's still open**: this proves the fetch/parse/address-wiring layer end-to-end but did NOT go through the production
CLI → GCS write → manifest-record path (that also needs `record_captured(source=...)`, shard-key conventions, and a real
or `-test-` bucket target — a materially bigger, higher-blast-radius step than an in-process RPC read, and this
session's `est_hours: 1.0` budget is already well spent). Not fabricating a "landed in manifest" claim for work not
actually done — leaving todo 3's checkbox UNCHECKED and phase `AAVE-PLASMA`/`FLUID-PLASMA` at `"pipeline"`.
**Recommended next step (now much lower-risk than before this session)**: dispatch a real (or at minimum
staging/test-bucket) MTDS `lending_indices` capture for `AAVE-PLASMA` for a recent day, confirm rows appear in the
manifest with `venue=AAVE-PLASMA`/`chain=PLASMA`, then flip `defi_venues.py`'s `"AAVE-PLASMA": "pipeline"` → `"live"`
(and `FLUID-PLASMA` once its still-open `PROTOCOL_LAUNCH_DATES` date is confirmed per the P1 todo above) and finally
check this todo's box.

## Data-source scoping (P2 findings, 2026-07-28, slot-8)

**Verdict: direct RPC via Alchemy for both venues — no subgraph exists for either.** Evidence below (web search + GitHub
file reads, not a live on-chain/GraphQL call — the implementer should do one live confirmation pass, e.g. an actual
`eth_getCode`/GraphQL probe, before wiring, per the re-verify notes inline).

### AAVE-PLASMA

- **No Aave V3 subgraph found for Plasma** on The Graph (checked `thegraph.com/explorer` + the `aave/protocol-subgraphs`
  repo config). This mirrors the existing `SUBGRAPH_IDS["aave_v3"]["OPTIMISM"]` comment in
  `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py` — Aave doesn't reliably
  publish/maintain subgraphs for every chain, and the codebase already has a working RPC-fallback path for exactly this
  case.
- **Aave DOES have canonical contracts on Plasma**, registered in the community-maintained `aave-address-book`
  (`bgd-labs/aave-address-book`, `src/AaveV3Plasma.sol` exists — confirms Plasma is a real, recognized Aave V3 market,
  not a rumor):
  - `POOL`: `0x925a2A7214Ed92428B5b1B090F80b25700095e12`
  - `POOL_ADDRESSES_PROVIDER`: `0x061D8e131F26512348ee5FA42e2DF1bA9d6505E9`
  - `AAVE_PROTOCOL_DATA_PROVIDER`: `0xf2D6E38B407e31E7E7e4a16E6769728b76c7419F`
  - `ORACLE`: `0x33E0b3fc976DC9C516926BA48CfC0A9E10a2aAA5`
  - **RE-VERIFY before wiring**: these were extracted via an LLM-summarized fetch of the raw Solidity file, not a
    byte-for-byte diff. Re-pull `src/AaveV3Plasma.sol` directly at implementation time and copy-paste; don't trust this
    transcription for the actual commit.
  - Note the DATA_PROVIDER address does **NOT** match the shared CREATE2 address already hardcoded for
    ARBITRUM/OPTIMISM/POLYGON/AVALANCHE in `lending_indices_handler.py`'s `_AAVE_V3_DATA_PROVIDER_ADDRESSES`
    (`0x7F23D86Ee20D869112572136221e173428DD740B`) — Plasma is evidently a newer Aave V3 factory deployment, so don't
    assume that shared address carries over; use Plasma's own.
- **Concrete wiring** mirrors the existing OPTIMISM RPC-fallback pattern
  (`market_tick_data_service/cli/handlers/lending_indices_handler.py` + `lending_indices_rpc.py`):
  1. `CHAIN_CONFIGS[9745]` needs an Alchemy RPC template — Alchemy officially supports Plasma
     (`https://plasma-mainnet.g.alchemy.com/v2/{api_key}`, confirmed via alchemy.com/rpc/plasma).
     `MAINNET_CHAIN_IDS["PLASMA"] = 9745` already landed (P1 above); `CHAIN_CONFIGS` is the one remaining registry gap —
     `AlchemyBaseClient._resolve_rpc_url` chains `MAINNET_CHAIN_IDS` → `CHAIN_CONFIGS`, and chain_id 9745 has no
     `CHAIN_CONFIGS` entry yet.
  2. Add `"PLASMA"` to `_AAVE_V3_POOL_ADDRESSES` and `_AAVE_V3_DATA_PROVIDER_ADDRESSES` (addresses above, re-verified).
  3. **Do NOT** add a `SUBGRAPH_IDS["aave_v3"]["PLASMA"]` entry — leaving it absent is what routes
     `_fetch_aave_v3_via_rpc` down the RPC-fallback path (same dict shape as the OPTIMISM precedent).
  4. Expected schema: `lending_indices` only (via `getAllReservesTokens` + the existing `_DATA_PROVIDER_ABI` calls) —
     same ceiling as OPTIMISM's RPC fallback; no `oracle_prices`/`risk_params`/`liquidations` from this path.
  5. Auth: none beyond the existing Alchemy API key already used for every other chain (`get_secret_client()`).

### FLUID-PLASMA

- **Fluid IS live on Plasma** with dedicated periphery contracts, confirmed via
  `Instadapp/fluid-contracts-public/deployments/deployments.md`:
  - `LiquidityResolver` on Plasma: `0xca13A15de31235A37134B4717021C35A3CF25C60` — **identical to the address already
    hardcoded** as `FLUID_LIQUIDITY_RESOLVER_ADDRESS` in
    `market_tick_data_service/market_interface/adapters/defi/fluid_liquidity_resolver.py:110` (that constant's own
    comment already documents "mainnet/arbitrum/base/polygon/plasma/bnb, all 0xca13A15de31235A37134B4717021C35A3CF25C60"
    — Fluid deploys this resolver at a deterministic CREATE2 address across every chain, Plasma included). **No new
    address needed for this contract** — this match is a direct byte-comparison against the existing repo constant, not
    a fresh transcription, so no re-verify needed here.
  - `LendingResolver` on Plasma: `0x48D32f49aFeAEC7AE66ad7B9264f446fc11a1569` (not currently consumed by any adapter in
    this repo — re-verify before use, same caveat as the Aave addresses above).
  - `Liquidity` core contract on Plasma: `0x52Aa899454998Be5b000Ad077a46Bbe360F4e497` (re-verify before use).
  - The `FluidVaultResolver` address used by `fluid_adapter.py`
    (`FLUID_VAULT_RESOLVER_ADDRESS = 0xA5C3E16523eeeDDcC34706b0E6bE88b4c6EA95cC`) was **not** independently confirmed on
    Plasma in this pass — re-verify via `eth_getCode` against Plasma RPC before assuming the same CREATE2 carries over
    for this specific contract (only the Liquidity-layer resolver's cross-chain identity is proven above; the Vault
    resolver's is not).
- **No Fluid subgraph exists for any chain today** (the `SUBGRAPH_IDS["fluid"]` comment already says "Multi-chain: Fluid
  subgraph IDs need verification", and there's a still-open community bounty on gov.fluid.io to build one from scratch).
  Fluid capture in this codebase is already 100% RPC-based (`fluid_adapter.py`/`fluid_liquidity_resolver.py` call the
  resolver contracts directly via Alchemy) — Plasma slots into the exact same existing pattern, no new adapter
  architecture needed.
- **Concrete wiring**:
  1. Same `CHAIN_CONFIGS[9745]` addition as AAVE above (shared step).
  2. `FluidAdapter(chain="PLASMA")` should work with no code changes once (1) lands, PROVIDED `fluid_adapter.py`'s
     vault-discovery step doesn't hardcode `chain="ETHEREUM"` anywhere — needs a quick spot-check at implementation
     time, not a rewrite.
  3. Expected schema: identical to existing Fluid rows (Liquidity Layer `getOverallTokenData` → `lending_indices`-shaped
     rows: supply/borrow totals, utilization, rate data).
  4. Auth: none beyond the existing Alchemy key.

### Not recommended: DefiLlama aggregator

DefiLlama does track Aave V3 on Plasma at the protocol/chain-TVL level (`defillama.com/protocol/aave-v3` lists Plasma
among 23 chains), but its public API (`api.llama.fi`) exposes chain-level TVL, not the per-reserve
`lending_indices`/`risk_params`/`liquidations` granularity this system's DeFi data model requires. Not a substitute for
the RPC path above — only useful as a coarse cross-check if capture ever needs a sanity-check total.

## Codex SSOTs

None directly on point — this is a UAC-registry-internal chain-onboarding gap, not a cross-cutting data pipeline
contract. `/codex/02-data/defi-canonical-naming-ssot.md` may be relevant once capture wiring actually starts (venue
naming conventions).

## 2026-07-31 progress checkpoint (slot 15) — real code bug found + fixed, manifest-write leg still in flight

Picked up sub-item (4) (the manifest-write leg slot-3 left open). **Found and fixed a genuine wiring bug the doc's own
todo 3 guidance got wrong**: `_collect_protocol_chain` (`lending_indices_handler.py`) short-circuits to "No subgraph ID
for protocol=%s chain=%s, skipping" and returns `{}` the moment `get_subgraph_id(protocol, chain)` is falsy — PLASMA has
NO subgraph_id entry at all, so it never reached `_query_and_parse`'s cascade, and the 3rd-tier RPC fallback
(`_fetch_aave_v3_via_rpc`) lives ONLY inside that cascade (triggers when a REGISTERED subgraph_id returns 0 rows, not
when no subgraph_id exists). This doc's own todo 3 text ("leaving `SUBGRAPH_IDS[...]` absent is what routes
`_fetch_aave_v3_via_rpc` down the RPC-fallback path, same shape as OPTIMISM") is factually wrong for this dispatch path
— OPTIMISM has a real (broken/empty) subgraph_id registered, which is why it reaches the cascade at all; PLASMA has
none. Confirmed via two live dry-runs against the real CLI (not just slot-3's in-process call, which bypassed this exact
gating logic): before the fix, `--lending-chains PLASMA` produced 0 rows with the skip warning; after,
`Aave V3 RPC fallback: 18 rows for PLASMA (18 reserves x 1 blocks)` — same 18 rows slot-3 validated in-process.

**Fix**: extracted a `_rpc_only_fallback()` helper (also needed to keep `_collect_protocol_chain` under the QG
function-size gate) that routes any `aave_v3` protocol/chain pair with a registered pool address but no subgraph_id
straight to `_fetch_aave_v3_via_rpc`, before falling back to the original skip-and-log behavior for every other case
(unchanged). Two local commits on `market-tick-data-service`, **NOT yet pushed** (quality-gates.sh in flight at
checkpoint time, ~47% through the unit suite on a loaded shared host):

- `19d432fe` — `fix(lending-indices): route no-subgraph aave_v3 chains to direct RPC fallback`
- `daf90798` — `refactor(lending-indices): extract _rpc_only_fallback to fix function-size QG gate` (the first commit
  alone pushed `_collect_protocol_chain` to 68L, over the size ceiling; this is the fix, no behavior change)

**Exact resume steps for whoever picks this up** (including a future me, if this session ends before shipping):

1. `cd market-tick-data-service && bash scripts/quality-gates.sh` — if still running/was killed, re-run. If GREEN, ship
   both commits via `quickmerge --agent --files market_tick_data_service/cli/handlers/lending_indices_handler.py`
   (single quickmerge call covers both, they're already committed locally in sequence). If RED, read the failure — it
   was ONLY the function-size gate before (now fixed); a different failure needs its own diagnosis, don't assume it's
   the same issue.
2. Once shipped, run the REAL (non-`--dry-run`) capture:
   `GCP_PROJECT_ID=central-element-323112 .venv/bin/python -m market_tick_data_service --operation collect-lending-indices --mode batch --asset-group defi --lending-protocols aave_v3 --lending-chains PLASMA --start-date 2026-07-30 --end-date 2026-07-30 --log-level INFO`
   (drop `--dry-run`; **use `--lending-chains`, NOT `--venues`** — the latter is not consumed by this handler and
   silently sweeps every default chain instead, a real trap this session hit once already).
3. Confirm rows landed in the manifest for `venue=AAVE-PLASMA`/`chain=PLASMA` (read the availability index or query the
   manifest directly for that date/venue — don't just trust the CLI's own log output).
4. Flip `unified-api-contracts/unified_api_contracts/registry/defi_venues.py`'s `"AAVE-PLASMA": "pipeline"` →
   `"AAVE-PLASMA": "live"` (line ~588; leave `"FLUID-PLASMA": "pipeline"` unchanged — its `PROTOCOL_LAUNCH_DATES` entry
   is still unconfirmed per the P1 todo above, a separate prerequisite).
5. Ship the UAC phase flip, then flip this doc's P3 todo checkbox with both SHAs cited, `/done`.

**Lesson for whoever re-derives a "should route to RPC fallback" claim in this codebase**: verify against the ACTUAL
call path used by the real CLI entrypoint, not just a direct in-process function call — `_fetch_aave_v3_via_rpc` being
correctly wired and reachable are two different claims, and this doc's own todo 3 conflated them.
