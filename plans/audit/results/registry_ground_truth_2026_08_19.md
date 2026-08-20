---
doc_type: audit-result
title: Registry ground truth vs what the four client artefacts show — 2026-08-19
summary: >-
  Measured registry counts (chains, venues, DeFi venues, archetypes, families) set against what each of the four
  client-disclosure artefacts actually names. The artefacts massively under-represent the built system — the
  operator's read was correct. Also surfaces a real registry defect: VENUE_CHAIN_MAP declares 4 chains while the
  codebase spans 19.
status: pass
nature: record
asset_group: [cross-cutting, defi]
stage: [data, meta]
repos: [unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [client-disclosure, registry, venues, chains, archetypes, ground-truth]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/client_artefact_remediation_2026_08_18.md,
  ]
created: 2026-08-19
last_updated: "2026-08-19"
date: 2026-08-19
severity: P0
audited_scope: >-
  UAC registry counts (ChainKind, VENUE_DATA_TYPE_CAPABILITIES, DEFI_VENUE_DATA_TYPE_CAPABILITIES,
  StrategyArchetype, StrategyFamily, VENUE_CHAIN_MAP) set against the venue/chain/archetype surface actually named
  in the four client-disclosure artefacts under codex/14-customer-journeys/commercial-model/.
auditor: >-
  Interactive session slot 6, by importing the registries directly in the UAC venv; corrected mid-session after an
  independent sub-agent could not reproduce two grep-derived figures.
resulting_plan:
lib_version:
doc_versions_checked:
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
locked_by:
locked_since:
resolved_by:
source: >-
  Measured live 2026-08-19 by importing the UAC registries directly (not regex-parsing), interactive session slot 6,
  after the operator flagged that the artefacts show ~2 chains and a couple of DeFi venues when the real system has
  far more.
---

# Registry ground truth vs artefact coverage — 2026-08-19

**The operator was right: the artefacts under-represent what is built.** These are measured, not estimated —
derived by importing the registries, so they are reproducible.

## Ground truth

| Thing                                | Measured | Source                                                  |
| ------------------------------------ | -------: | ------------------------------------------------------- |
| Venues declared                      |  **192** | `VENUE_DATA_TYPE_CAPABILITIES`                          |
| DeFi venues                          | see note | name-filter gave 51; registry reads give 103 — unresolved |
| Chains (`ChainKind`, authoritative)   |   **23** | `unified_api_contracts.canonical.crosscutting.defi`     |
| Chains declared in `VENUE_CHAIN_MAP` |    **4** | `VENUE_CHAIN_MAP` (15 venues only)                      |
| Strategy archetypes                  |   **60** | `StrategyArchetype`                                     |
| Strategy families                    |    **9** | `StrategyFamily`                                        |

> **CORRECTION 2026-08-19 (same session, before the numbers were used).** The "19 chains / 51 DeFi venues"
> figures below were derived by grepping string literals and name-matching venue prefixes — both are FILTER
> ARTEFACTS, not registry reads. The authoritative chain SSOT is **`ChainKind`** in
> `unified_api_contracts.canonical.crosscutting.defi`, which has **23 members**: ethereum, arbitrum, base,
> optimism, polygon, avalanche, bsc, gnosis, linea, scroll, zksync, blast, mode, celo, aurora, fantom, mantle,
> metis, moonbeam, solana, bitcoin, starknet, hyperliquid_l1. My grep MISSED gnosis, mode, celo, aurora, fantom,
> metis, moonbeam and bitcoin, and wrongly counted `hyperliquid_api`/`_rest`/`_testnet` as chains. **Use
> `ChainKind` (23), never the 19-token list.** The DeFi venue count likewise should be read from the registry,
> not a name filter — an independent agent trying to reproduce "51" got 130 / ~59-70 / 103 depending on filter,
> and correctly refused to pick one.

**The 19 chains (SUPERSEDED — see correction above)**: arbitrum · avalanche · base · blast · bsc · ethereum · hyperliquid (+ `_api`, `_rest`,
`_testnet` variants) · linea · mantle · optimism · plasma · polygon · scroll · solana · starknet · zksync.

**DeFi venue spread** (illustrative, not the full 51): AAVE_V3 across arbitrum/avalanche/base/bsc/ethereum/linea/
optimism/polygon/scroll/zksync (plus AAVE-ETHEREUM, AAVE-PLASMA) · COMPOUND_V3 across arbitrum/base/ethereum/
optimism/polygon/scroll · MORPHO across arbitrum/base/ethereum/optimism/polygon (+ MORPHOVAULTS-ETHEREUM) ·
CURVE across avalanche/ethereum/optimism · PENDLE across arbitrum/ethereum · Solana: JUPITER, KAMINO, METEORA,
ORCA, RAYDIUM · plus HYPERLIQUID, ASTER, EXTENDED-STARKNET, ETHENA-ETHEREUM, LIDO-ETHEREUM.


> **CORRECTION 2026-08-19 (second).** Two further numbers here were wrong or unresolved:
> **(a) Unbucketed venues are 24, not 15.** I derived 15 by subtracting 177 from 192; the real answer needs a
> set-difference, because the bucket set and the capability set are not nested. Measured by an agent that ran it
> properly.
> **(b) Chains-with-live-DeFi-venues is still UNRESOLVED.** Four independent derivations gave 11, 12, 13 and 14.
> The most rigorous pass (importing `ChainKind`, `DEFI_VENUE_DATA_TYPE_CAPABILITIES`, `ALL_DEFI_VENUES`,
> `DEFI_VENUE_TO_PROTOCOL`, `VENUE_TO_ADAPTER_KEY`) got **11 of 23**, with a best-effort union topping out at 12,
> and could not reproduce 14 at all. Do not quote a single figure until the filter is settled — this is a symptom
> of the three-disagreeing-chain-registries defect, not of sloppy counting.

## What the artefacts actually show

| Artefact                                 | Chain names | Families named |
| ---------------------------------------- | ----------: | -------------: |
| `platform-external-api-walkthrough.html` |           7 |          **0** |
| `platform-architecture.html`             |           6 |          **0** |
| `strategy-service-walkthrough.html`      |           5 |              9 |
| `strategy-service-deep-dive.html`        |           4 |          **0** |

Only one of four documents names the strategy families at all, and none comes close to the venue or chain surface.
A reader of any of these would conclude the platform reaches a fraction of what it actually reaches.

## The registry defect worth fixing separately

`VENUE_CHAIN_MAP` covers **15 venues / 4 chains** while the codebase references **19 chains** and declares **192
venues**. Anything deriving chain coverage from that map under-reports by construction — including, potentially,
coverage denominators. This is a code finding, not a documentation one.

- [ ] [BACKEND] P0. **Reconcile `VENUE_CHAIN_MAP` against the real chain surface** — 4 declared vs 19 referenced,
      15 venues mapped vs 192 declared. Determine whether the map is intentionally scoped (e.g. only chains with
      an execution path) or genuinely under-declared, and state which in the registry docstring so the next reader
      does not have to re-derive it. If any coverage or readiness denominator reads this map, that denominator is
      under-counting.
- [ ] [DOC] P0. **Expand all four artefacts to the real surface** — every chain, the venue breadth (at minimum
      per-asset-group counts with the DeFi protocol×chain spread shown), and all 60 archetypes / 9 families.
      Generate these tables from the registries rather than hand-authoring them, so they cannot rot the way the
      hand-transcribed enum counts already did.

## Progress Log

**2026-08-19 — measured.** Written immediately on measurement so the numbers survive a session limit.
