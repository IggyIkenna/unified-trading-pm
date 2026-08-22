---
doc_type: plan
title: DeFi 23 non-producing venues — purge/complete/build/re-home triage
summary:
  Per-venue triage of the 23 declared-but-non-producing DeFi venues (of 126 declared, 103 produce data), answering
  four operator questions — suspected duplicate aliases, cheap chain expansions vs. real adapter gaps, non-venue
  infrastructure re-homing, and the three Solana DEXs — each verdict backed by direct registry/adapter reads, not
  inference. Every code-touching todo edits unified-api-contracts (the DeFi venue/capability/chain-URL SSOT), so all
  of them are BLOCKED until the unified-api-contracts lane currently shipping lands (see banner below).
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [unified-api-contracts, instruments-service, market-tick-data-service, unified-trading-library, unified-trading-system-ui, deployment-service]
scope: [engineer, admin]
tags: [defi, venue-triage, purge, chain-expansion, re-home, lifinity, meteora, phoenix]
related:
  [
    /plans/active/issues/defi_venue_phase_readiness_ruling_2026_08_22.md,
    /plans/active/issues/three_chain_registries_disagree_none_authoritative_2026_08_19.md,
    /plans/audit/results/registry_ground_truth_2026_08_19.md,
    /plans/epics/defi_master.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 7.2
locked_by:
locked_since:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
    unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py,
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_chain_data.py,
    instruments-service/instruments_service/engine/orchestrator/defi.py,
    instruments-service/instruments_service/reference_data/adapters/defi/,
    /plans/active/issues/defi_venue_phase_readiness_ruling_2026_08_22.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: operator-request-2026-08-22
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
---

# DeFi 23 non-producing venues — purge/complete/build/re-home triage

> **🟡 GATING BANNER — read before executing ANY todo below.** Every todo in this plan edits
> `unified-api-contracts` (the DeFi venue/capability/chain-URL SSOT — `defi_venues.py`,
> `defi_venue_capabilities.py`, `capability_declarations/_defi*.py`, `venue_adapter_keys.py`,
> `venue_granularity_seed.py`, `chain_env.py`) even for the "cheap" ones, because `get_solana_protocol_url()` (used by
> the Meteora URL fix) and every chain/subgraph declaration (used by the Aave/Compound/Morpho/PancakeSwap chain
> expansions) live there. **None of these todos are safe to execute until the operator signals the currently-shipping
> unified-api-contracts lane has landed.** The only safe-now work is external research that touches no repo (vault
> address discovery, subgraph-availability checks, Phoenix Perpetuals API investigation) — marked `[RESEARCH-OK-NOW]`
> below.

This plan resolves the operator's 2026-08-22 request to triage the 23 of 126 declared DeFi venues that produce zero
data, answering four specific questions with measured evidence (registry reads, adapter source, and — for the three
Solana DEXs — live upstream re-verification). It does not re-litigate the 2026-08-22
`defi_venue_phase_readiness_ruling` issue (which independently reached NOT-READY/UNCERTAIN verdicts for 19 of these
20 venues via a different lens — IS-producibility) — it complements it with the purge/complete/build/re-home
disposition that issue explicitly did not attempt.

## Q1 — suspected duplicate aliases (UNISWAP-ETHEREUM, COMPOUND-ETHEREUM, MORPHOVAULTS-ETHEREUM, FRAX-ETHEREUM)

**Measured finding: none of the four is a duplicate/legacy alias.** `LEGACY_DEFI_VENUE_ALIASES`
(`unified-api-contracts/unified_api_contracts/registry/defi_venues.py:344`) maps bare `UNISWAP_V2`/`_V3`/`_V4` and
`COMPOUND_V3` to their versioned siblings, but carries **no bare `UNISWAP` or `COMPOUND` entry at all** — the bare
`-ETHEREUM` tokens are separate, deliberately-declared identities. `MORPHO_VAULTS`/`MORPHOVAULTS` alias resolves
*to* `MORPHOVAULTS-ETHEREUM` (it is the alias target, not a stray duplicate of `MORPHO-ETHEREUM`), and `FRAX` aliases
to `FRAX-ETHEREUM` the same way. `defi_venue_capabilities.py` confirms each declares a genuinely different
`data_type` than its "sibling": `UNISWAP-ETHEREUM`→`governance_events` (DAO events, not swaps),
`COMPOUND-ETHEREUM`→`governance_events`, `MORPHOVAULTS-ETHEREUM`→`vault_share_price` (MetaMorpho ERC-4626 vaults,
distinct product from Morpho lending markets), `FRAX-ETHEREUM`→`vault_share_price` (sfrxETH share price).

- [ ] [OPERATOR] P2. **UNISWAP-ETHEREUM / COMPOUND-ETHEREUM — purge, or scope as a new governance-events product.**
      Neither is enumerated by `_build_defi_venues()` (no subgraph mapping, no `_STATIC_DEFI_VENUES` entry) and
      `defi_venues.py`'s module docstring's MTDS sub-dim bucket list (`gas-fees, lending-indices, dex-swaps,
      dex-pools, oracle-prices, lst-rates, liquidations, evm-defi, solana-defi, perp-funding`) has **no
      governance-events bucket at all** — there has never been a physical capture path for this declared data_type,
      not merely an unscheduled one. Zero manifest rows is the expected, converging result of three independent
      registries (orchestrator enumeration, MTDS bucket taxonomy, `DEFI_VENUE_PHASE="pipeline"`), not something a
      single GCS sample would add confidence to. Recommend PURGE (remove the venue token + capability entry) unless
      the operator wants governance-event tracking as a real new product, in which case this becomes a
      [BUILD-ADAPTER] item (new bucket, new writer, new adapter — not a config change).
- [ ] [BACKEND] P2. **MORPHOVAULTS-ETHEREUM — complete-cheaply, not a purge.** Real, distinct product
      (MetaMorpho ERC-4626 vaults) sharing the `vault_share_price` mechanism/data_type with `MAKER-ETHEREUM`
      (`DEFI_VENUE_PHASE="live"`) — the bucket/writer path is proven working via that sibling. Gap is purely
      orchestrator enumeration: add to `_STATIC_DEFI_VENUES` (or a subgraph mapping, whichever matches how the vault
      registry is actually discovered) in `instruments-service/instruments_service/engine/orchestrator/defi.py`,
      flip `DEFI_VENUE_PHASE["MORPHOVAULTS-ETHEREUM"]` to `"live"` in lockstep (denominator-drift guard), same
      pattern as the 2026-07-31 VENUS/RADIANT/BENQI wiring fix this repo already has precedent for.
- [ ] [BACKEND] P2. **FRAX-ETHEREUM — complete-cheaply, real historical data exists.** `defi_venues.py:759` names
      it explicitly: real data captured, stopped dead 2026-06-21, never had a Cloud Scheduler cron (classified
      `UNVERIFIED-CLAIM`, distinct from the `ACCURATE-BUT-MANUAL-ONLY` class that graduated 2026-07-31). This is a
      scheduler-provisioning fix on an already-proven data path (`vault_share_price`, same mechanism as
      MORPHOVAULTS-ETHEREUM/MAKER-ETHEREUM), not new adapter work. Confirm 3 consecutive scheduled runs succeed
      (the same promotion bar the 6 VENUS-class venues cleared), then flip `DEFI_VENUE_PHASE` to `"live"`.

## Q2 — 13 chain expansions, grouped by protocol

**Measured finding: 6 of 8 protocols use a fully chain-parameterized adapter (subgraph ID or curated per-chain
address dict) — the code does not need to change, only chain-specific config/data. 1 (Euler V2) is genuinely
hardcoded to Ethereum despite a cosmetic `chain` constructor arg. 1 (Idle) has a chain-parameterized adapter but a
literally-empty non-Ethereum address dict.**

| Protocol | Mechanism | Live chains (code-confirmed) | Verdict for the listed gap(s) |
|---|---|---|---|
| AAVE_V3 | subgraph (`SUBGRAPH_IDS["aave_v3"]`) | ETHEREUM, ARBITRUM, OPTIMISM (+POLYGON/AVALANCHE/BASE/LINEA/BSC per readiness-ruling issue) | SCROLL, ZKSYNC: no subgraph ID entry — **complete-cheaply pending confirming a working Aave V3 subgraph exists for each chain** (config-only, adapter untouched) |
| COMPOUND_V3 | subgraph (`SUBGRAPH_IDS["compound_v3"]`) | ETHEREUM, ARBITRUM, BASE, OPTIMISM | POLYGON: subgraph comment states explicitly *"Compound V3 not active on Polygon"* — real protocol absence, **PURGE COMPOUND_V3-POLYGON**, not a data gap. SCROLL: no entry, deployment status unconfirmed — **research first**, purge or complete-cheaply depending on finding |
| MORPHO | curated per-chain ID dict, `_MORPHO_CHAIN_IDS` (ETHEREUM/BASE/ARBITRUM/OPTIMISM/POLYGON all present in code) | ETHEREUM, BASE (+ARBITRUM code-ready) | ARBITRUM: **complete-cheaply** — UAC comment cites ~$3.0B real supplied/borrowed liquidity, adapter already wired, only orchestrator enumeration + the still-open manifest-confirmation follow-up (readiness-ruling issue's own todo) remain. OPTIMISM (~$117k max single-market) / POLYGON (single-sided idle markets only): real, thin liquidity — **not worth capturing as declared**, recommend defer/purge-candidate rather than build |
| IDLE | curated per-chain vault-address dict, `_IDLE_VAULTS_BY_CHAIN` | ETHEREUM only — dict has **zero** ARBITRUM or POLYGON entries | Adapter mechanism is parameterized but the data doesn't exist yet — **research-needed**: find real Idle Finance vault addresses on Arbitrum/Polygon (or confirm none exist → purge both) |
| YEARN_V3 | curated per-chain vault-address dict, `_YEARN_VAULTS_BY_CHAIN` | ETHEREUM, ARBITRUM | OPTIMISM: dict has zero entries despite a `_get_deploy_date` OPTIMISM branch existing — **research-needed**, same class as Idle |
| PANCAKESWAP_V3 | subgraph (`SUBGRAPH_IDS["pancakeswap_v3"]`) | BSC, ETHEREUM, BASE | ARBITRUM: no subgraph ID entry — PancakeSwap V3 is a real multichain deployment; **complete-cheaply pending confirming a PancakeSwap V3 Arbitrum subgraph exists** |
| BEEFY | curated per-chain vault-address dict, `_BEEFY_VAULTS_BY_CHAIN` | ETHEREUM, ARBITRUM, BASE, BSC, AVALANCHE | POLYGON: adapter's own comment states *"POLYGON intentionally NOT registered: a Beefy API survey on 2026-05-12"* found it unsuitable — **already deliberately excluded with a dated rationale — PURGE BEEFY-POLYGON**, formalize what the code already decided |
| EULER_V2 | **NOT parameterized** — `_MVP_MARKETS` is a flat, single Ethereum-derived address list; the `chain` constructor arg has no effect on which vaults are returned | ETHEREUM only | ARBITRUM: genuine gap, matches the operator's own catch exactly — **BUILD-ADAPTER** (new `_MVP_MARKETS_BY_CHAIN` dict + real Arbitrum vault-address research), not a config change |

- [ ] [BACKEND] P2. AAVE_V3 — [RESEARCH-OK-NOW] confirm working subgraphs exist for SCROLL/ZKSYNC, then add
      `SUBGRAPH_IDS` entries in `capability_declarations/_defi.py`; flip `DEFI_VENUE_PHASE` in lockstep.
- [ ] [BACKEND] P2. COMPOUND_V3 — purge `COMPOUND_V3-POLYGON` (protocol-confirmed absent); [RESEARCH-OK-NOW]
      confirm SCROLL deployment status before deciding complete-cheaply vs. purge for `COMPOUND_V3-SCROLL`.
- [ ] [BACKEND] P2. MORPHO-ARBITRUM — complete-cheaply: close the readiness-ruling issue's own manifest-confirmation
      follow-up, then wire into `_STATIC_DEFI_VENUES`/subgraph enumeration + flip phase. MORPHO-OPTIMISM /
      MORPHO-POLYGON — do NOT build; document as real-but-thin-liquidity, defer.
- [ ] [BACKEND] P3. IDLE-ARBITRUM / IDLE-POLYGON — [RESEARCH-OK-NOW] find real Idle Finance vault addresses on both
      chains (or confirm none exist); populate `_IDLE_VAULTS_BY_CHAIN` or purge each chain individually based on
      finding.
- [ ] [BACKEND] P3. YEARN_V3-OPTIMISM — [RESEARCH-OK-NOW] find real Yearn V3 Optimism vault addresses; populate
      `_YEARN_VAULTS_BY_CHAIN["OPTIMISM"]` or purge.
- [ ] [BACKEND] P2. PANCAKESWAP_V3-ARBITRUM — [RESEARCH-OK-NOW] confirm a working PancakeSwap V3 Arbitrum subgraph
      exists, then add the `SUBGRAPH_IDS` entry; flip phase.
- [ ] [BACKEND] P3. BEEFY-POLYGON — purge (already deliberately excluded per the adapter's own 2026-05-12 survey
      comment; formalize by removing the aspirational venue token/capability entry).
- [ ] [OPERATOR] P2. EULER_V2-ARBITRUM — build-vs-purge call: real code work required (`_MVP_MARKETS_BY_CHAIN` +
      Arbitrum vault research), not a config flip. Recommend BUILD given Euler V2 is TVL-significant, but flagging
      for an explicit priority call given the effort delta vs. the other seven protocols in this table.

## Q3 — the non-venues (FLASHBOTS-ETHEREUM, ACROSS-ETHEREUM, STARGATE-ETHEREUM)

**Measured finding: all three are STILL-BROKEN class (per `defi_venues.py:759`'s own docstring — "crash-looping
cron or never scheduled at all, two with no SchemaContract registered") — their `bridge_events`/`mev_events`
capture paths have never worked. Separately, and more importantly: `unified_api_contracts.internal.domain.defi
.transfers.TransferType` already declares `STARGATE`, `ACROSS`, `HOP`, `LAYERZERO`, `SOCKET`, `LIFI`, `CCTP` as
bridge-provider identities used by the real, working transfer/execution ledger (`TransferType.BRIDGE` in
`canonical/crosscutting/transfer_events.py`, explicit docstring "Across, Stargate, etc."). This is the "Socket
aggregator" pathway the operator referenced — bridge activity is already tracked correctly at the execution/ledger
layer, under a different mechanism than an MTDS venue token.**

- [ ] [OPERATOR] P2. ACROSS-ETHEREUM / STARGATE-ETHEREUM — RE-HOME, don't purge outright without recording why:
      remove both as `VENUE_DATA_TYPE_CAPABILITIES`/MTDS-venue-shaped tokens (their `bridge_events` capture never
      worked, and no MTDS bucket kind exists for `bridge_events` in the sub-dim taxonomy at all), and note in the
      registry that bridge activity is tracked via `TransferType.BRIDGE` (Across/Stargate/Socket/etc. as provider
      values) at the execution/ledger layer instead — mirrors the ALCHEMY-ONCHAIN 2026-08-22 re-home precedent
      exactly (`DEFI_DATA_SOURCE_CAPABILITIES` dict already exists as the target pattern in
      `defi_venue_capabilities.py`).
- [ ] [OPERATOR] P3. FLASHBOTS-ETHEREUM — no operator ruling exists yet (explicitly separate from the
      ALCHEMY-ONCHAIN 2026-08-21 ruling per the readiness-ruling issue). Same STILL-BROKEN status, same
      infra-not-venue shape (MEV-relay analytics, not a tradeable venue) — recommend RE-HOME to
      `DEFI_DATA_SOURCE_CAPABILITIES` using the identical ALCHEMY-ONCHAIN pattern, pending explicit operator scoping.

## Q4 — the Solana DEXs

- [ ] [OPERATOR] P1. **LIFINITY-SOLANA — execute the removal ruling.** Protocol confirmed dying/dead
      (`api.lifinity.io/pools` → HTTP 522, re-verified 2026-08-22). Consumer inventory (grep + registry-membership +
      path/filename binders, per `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — grep alone is
      NOT sufficient enumeration):
      - **unified-api-contracts**: `registry/defi_venues.py` (`ALL_DEFI_VENUES`, `DEFI_VENUE_PHASE`),
        `registry/defi_venue_capabilities.py`, `registry/capability_declarations/_defi.py` +
        `_defi_chain_data.py`, `registry/venue_adapter_keys.py` (`"LIFINITY-SOLANA": NO_ADAPTER_YET` — note this
        contradicts the adapter actually existing/being wired in `factory._ADAPTERS`, a second, independent finding
        worth a one-line note on removal), `registry/venue_granularity_seed.py` (granularity tuple),
        `registry/defi_major_assets.py`, `registry/market_data_categories.py` (venue-list membership),
        `registry/chain_env.py` (floor-date entry), `registry/expected_coverage.py` (already-removed comment —
        confirms partial prior cleanup), whole `external/lifinity/` subpackage (`__init__.py`, `schemas.py`,
        `mocks/pools.yaml`), `tests/unit/test_venue_adapter_keys.py`, `tests/cassette_orphan_allowlist.yaml`.
      - **instruments-service**: `reference_data/adapters/defi/lifinity.py` (delete), `reference_data/factory.py`
        (registration), `reference_data/utils/defi_utils.py`, `engine/orchestrator/defi.py`, tests
        (`test_defi_adapters_comprehensive.py`, `reference_data/adapters/defi/test_lifinity_metadata.py`), docs
        (`docs/DEFI_INSTRUMENTS.md`, `docs/ADAPTER_ARCHITECTURE.md`), `scripts/backfill_solana_dex_swaps_2026_05_13.py`.
      - **market-tick-data-service**: `cli/handlers/solana_defi_amm.py` (live `_LIFINITY_API/pools` call — the
        actual runtime consumer hitting the dead endpoint), `cli/handlers/solana_defi_handler.py` (protocol-name
        map + `_LIFINITY_API` constant).
      - **unified-trading-library**: `unified_trading_library/pipeline_mode_resolver.py` + its unit test.
      - **unified-trading-system-ui**: `lib/registry/ui-reference-data.json`.
      - **deployment-service**: `scripts/vm/setup-data-pipeline-vm.sh`.
      - Stated blind spot: `instruments-service.stale-pre-history-rewrite-20260805T112453Z/` and equivalent
        `.stale-pre-history-rewrite-*` directories are frozen historical checkouts (confirmed via `git log`), not
        live consumers — deliberately excluded from the migration, not missed.
- [ ] [BACKEND] P2. **METEORA-SOLANA — fix the endpoint, do not purge.** Live WebSearch/WebFetch re-verification
      2026-08-22 found Meteora thriving ($2B+ TVL, active Q1 2026 DLMM upgrade, ongoing 2026 integrations) —
      contradicting the readiness-ruling issue's "app.meteora.ag/api/pools → 404 → dead protocol" inference. The
      protocol moved its public pools API; the real current endpoint is `https://dlmm-api.meteora.ag/pair/all` (or
      `https://dlmm.datapi.meteora.ag/pools`), confirmed via Meteora's own docs
      (`docs.meteora.ag/api-reference/dlmm/pools/pools`). Both consuming repos hardcode the stale fallback behind a
      UAC override hook: `instruments-service/instruments_service/reference_data/adapters/defi/meteora.py:43`
      (`get_solana_protocol_url("meteora", "api_url")`) and
      `market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py:482`
      (`get_solana_protocol_url("meteora")`) — fix is a single UAC config entry
      (`capability_declarations/_defi_chain_data.py`'s `get_solana_protocol_url` source dict), not two separate
      code edits. Verify the new endpoint's response schema still matches `PoolInfo`/whatever `meteora.py` parses
      before re-enabling — a moved API commonly changes shape too.
- [ ] [BACKEND] P2. **PHOENIX-SOLANA — build a new Perpetuals adapter, purge the old spot one.** Our current
      integration (`external/phoenix/schemas.py`, `adapters/defi/phoenix.py`) targets the OLD spot order-book API
      (`api.phoenix.trade/markets`), confirmed deprecated 2026-05-15 (NXDOMAIN, re-verified 2026-08-22) — matches
      the operator's own read that spot volumes are poor. Live WebSearch confirms Ellipsis Labs (same team) shipped
      a genuinely separate **Phoenix Perpetuals** product — announced Solana Breakpoint 2025, private beta late
      2025, broader access through 2026 — a different on-chain program from the old spot CLOB, not a superset. This
      is [RESEARCH-OK-NOW]: investigate Phoenix Perpetuals' actual public API / on-chain program (beta status means
      docs may still be evolving) before scoping the adapter. Once scoped: declare a new data_type (likely
      `perp_funding` and/or `oracle_prices`, whatever the product actually exposes) distinct from the retired
      `governance`/spot-market capability, and remove the dead spot integration (`external/phoenix/` schemas,
      `phoenix.py`'s `api.phoenix.trade` call) in the same change so no dead-endpoint code survives the swap.

## What this plan did NOT do

Live GCS/manifest sampling for Q1's four tokens was not performed as a direct read — the 2026-08-22
`defi_venue_phase_readiness_ruling` issue already documented a reproducible ~120s+ UTL `get_storage_client()` timeout
against `gs://central-element-323112-honest-coverage/{date}/coverage.json` from this same environment class
(laptop-slot session), and this session did not want to burn a second unproductive multi-minute wait on the identical
tooling gap. In its place, three independent, mutually-corroborating code-level signals were used instead (orchestrator
non-enumeration, capability-declaration data_type distinctness, and the MTDS bucket-kind taxonomy's outright absence of
a `governance_events`/`bridge_events`/`mev_events` bucket) — the same class of evidence the readiness-ruling issue itself
used for its 19 NOT-READY verdicts. This is flagged, not hidden: a live manifest read remains open work if the operator
wants it before executing any purge.

## Progress Log

**2026-08-22 — triage written, Phase 1 read-only.** All findings above are measured (registry/adapter source reads +
live WebSearch/WebFetch re-verification for Meteora/Phoenix), not inferred. No files were edited in
`unified-api-contracts` per the operator's Phase 1 read-only instruction. Ready for Phase 2 once the operator signals
the concurrently-shipping unified-api-contracts lane has landed.
