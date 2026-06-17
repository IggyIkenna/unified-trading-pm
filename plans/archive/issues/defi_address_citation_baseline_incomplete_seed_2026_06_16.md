---
title: DeFi address-citation baseline incompletely seeded — blocks ratchet-exit-code hardening rollout
created: 2026-06-16
locked_by: live-defi-rollout
priority: P1
status: resolved
source:
  - QG-agent fleet ratchet sweep 2026-06-16 (check_defi_address_citations.py --workspace-root)
  - qg_base_service_ratchet_exit_code_2026_06_11.md (the hardening this blocks)
  - scripts/quality_gates/defi_address_citation_baseline.yaml
---

# DeFi address-citation baseline incompletely seeded — blocks ratchet-exit-code hardening rollout

> **Operator decision needed (Ikenna):** the fleet is NOT citation-ratchet-clean. Before the `base-service.sh`
> ratchet-exit-code hardening can ship, decide **grandfather-seed** vs **cite-first** for ~468 pre-existing uncited DeFi
> contract addresses across 8 service repos. See **§ Recommended decision**.

## TL;DR

- The **ratchet-exit-code hardening** (`qg_base_service_ratchet_exit_code_2026_06_11.md`, currently held on
  `origin/wip-preserve/qg-ratchet-hardening-2026-06-16`) fixes a real **hollow-green** bug: STEP 5.94/5.95/5.97 ratchets
  increment the violation counter `$V` on over-baseline but `$V` is never re-checked after the codex-compliance verdict
  → an over-baseline ratchet falls through to "ALL QUALITY GATES PASSED" + writes the sentinel. The fix makes any
  over-baseline ratchet hard-fail (exit 1).
- **Consequence of shipping it as-is:** every repo currently **silently over baseline** gets hard-failed on its next
  promote PR. A fleet sweep shows the fleet is NOT clean:
  - **5.94 fallback-imports:** ✅ clean.
  - **5.95 DTZ/TID251:** ✅ now clean — instruments-service `tid251 60>59` (1 new `from google.cloud import storage`)
    was **FIXED + landed** 2026-06-16 (`validate_sports_fixtures_v2_parity.py` → UCI `get_storage_client`).
  - **5.97 DeFi citations:** ❌ **8 repos over baseline 0** (~468 uncited addresses). The 2026-06-16 seed only
    grandfathered `unified-api-contracts: 138`; it missed every service repo's source.

## What I found

### 1. The citation checker silently scans whole service repos (not just `registry/`)

`scripts/quality_gates/check_defi_address_citations.py::scan_repo` is documented to scan
`unified_api_contracts/registry/`. But for any repo WITHOUT that dir — i.e. **every service repo** (only the
unified-api-contracts repo has `registry/`) — it **falls back to scanning the whole repo** (lines ~291-294, with the
comment "other repos have 0 addresses → nothing breaks"). That assumption is **false**: service source is full of real
hardcoded DeFi addresses. So STEP 5.97 with `--scope <service-repo>` does flag them — they're just hollow-green today
(the exact bug the hardening fixes).

### 2. Per-repo over-baseline counts (fleet sweep 2026-06-16)

`python3 scripts/quality_gates/check_defi_address_citations.py --workspace-root ..` (baseline 0 for every repo except
UAC=138):

| Repo                      | Uncited addresses | Sample sites                                                                                                             |
| ------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| execution-service         | **225**           | `execution_service/algo_library/multicall_batcher.py`, `sor_dex.py`, `data/defi_test_data_generator.py`                  |
| market-tick-data-service  | **215**           | `cli/handlers/_instruments_metadata.py`, `cli/handlers/_oracle_prices_constants.py`                                      |
| features-service          | **13**            | `onchain/app/calculators/compound_v3_lending_calculator.py`, `eigen_rewards_calculator.py`, `engine/lending_features.py` |
| strategy-service          | **9**             | `engine/strategies/v2/target_universe/catalog_yield_defi.py`                                                             |
| deployment-service        | **3**             | `scripts/deploy_contract.py`                                                                                             |
| alerting-service          | **1**             | `subscribers/stablecoin_issuer_pause_subscriber.py`                                                                      |
| e2e-testing               | **1**             | `scripts/defi/colocated_engine.py`                                                                                       |
| unified-trading-system-ui | **1**             | `context/internal-contracts/schemas/domain/defi/protocol_sdks.py`                                                        |
| **TOTAL**                 | **~468**          | (UAC's 138 in `registry/` is already grandfathered — separate from these)                                                |

### 3. What the addresses actually are (spot-checked — all genuine, not false positives)

They are **real on-chain contract addresses** — the literal coordinates of the DeFi world the system trades against.
Mostly legitimate, necessary constants; many already carry contextual comments, just not the ratchet's strict per-line
`# DERIVED <date> from <chain> <source>` format.

- **market-tick-data (215)** — DeFi reference + price data: **LST token contracts** (stETH
  `0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84`, wstETH, rETH, cbETH, weETH, ezETH, sDAI, sUSDe…, "immutable Ethereum
  mainnet constants" used as fallback when instruments-service has no parquets); **Chainlink oracle feeds** (ETH/USD
  `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419`, stETH/USD, cbETH/ETH… per chain); Phoenix CLOB pair mints (Solana).
- **execution-service (225)** — DeFi execution machinery: **Multicall3** `0xcA11bde05977b3631167028862bE2a173976CA11`
  (universal batching contract, same address on every EVM chain), DEX **swap routers** (`sor_dex.py`), and DeFi
  **test-data-generator** fixtures.
- **features-service (13)** — Compound v3 market addresses, EigenLayer rewards, lending-feature contracts.
- **strategy-service (9)** — DeFi yield-target catalog protocol addresses.
- **deployment-service / alerting / e2e / ui** — contract-deploy addresses, stablecoin-pause subscriber, colocated
  engine, protocol-SDK schema.

### 4. Why there are ~468

A DeFi system is inherently address-dense: **every protocol × every chain × every token / market / oracle feed is one
on-chain address** ("call this contract at this address" is the entire DeFi interface). Lido + Compound + Aave +
Uniswap + Chainlink + EigenLayer + Phoenix across Ethereum / Solana / L2s naturally produces hundreds. 468 is the
system's real on-chain footprint, dominated by MTDS's price/reference feeds (215) + execution's routers/multicall (225).
It is **not** a code smell or an accidental dump — it is the DeFi reference surface.

## Why it matters

- **The hardening cannot ship until this is resolved.** It's a real safety fix (hollow-green gate → a red ratchet
  currently writes a green sentinel + passes the promote PR). But shipping it with 8 repos over the citation baseline
  would hard-fail all 8 repos' next LDR→staging promote PR (the v2 gate runs the same `base-service.sh`), jamming the
  fleet pipeline.
- **The citation requirement is DeFi-safety-relevant.** A wrong DeFi address = funds sent to the wrong contract. The
  `# DERIVED <date> from <chain> <source>` discipline exists so every address is traceable to a canonical source
  (protocol docs / official deployment registry). That's exactly why this is Ikenna's call, not a mechanical
  agent-grandfather: it's the "do we tolerate the existing uncited DeFi surface, or close the provenance gap first"
  trade-off, in the data-correctness domain.

## Recommended decision (grandfather-seed vs cite-first)

**(a) Grandfather-seed (recommended for unblocking now):** run
`python3 scripts/quality_gates/check_defi_address_citations.py --workspace-root .. --update-baseline` to seed each
repo's current count into `defi_address_citation_baseline.yaml` (completes the incomplete 2026-06-16 seed — same
treatment UAC's 138 got, and the 5.94/5.95 baselines). The fleet becomes citation-ratchet-clean, the **hollow-green
bug-fix (hardening) ships immediately**, the addresses keep working (they already do), and **new** uncited addresses are
blocked. The 468 become a tracked ratchet-DOWN backfill task. Ships in minutes.

**(b) Cite-first:** back-fill real `# DERIVED <date> from <chain> <source>` citations on all 468 before shipping the
hardening. Higher-assurance for DeFi address-correctness (matches the "no silent gaps" stance) but a real multi-repo
effort, and overlaps Ikenna's existing UAC-side DeFi-citation work.

**QG-agent lean:** **(a) now** + a tracked citation-backfill todo, because the hardening's safety win (no more
hollow-green gates) is the urgent part, the addresses are pre-existing + mostly documented, and grandfathering is the
standard ratchet-seeding move. But the call on whether the uncited DeFi surface is acceptable-to-grandfather is
Ikenna's.

## ✅ RESOLVED 2026-06-17 — decision was (b) cite-first, and it's DONE

Ikenna chose **cite-first** and executed it fleet-wide (2026-06-16/17):

- execution-service `f516f51c` — cited 225 DeFi addresses (DERIVED/QG-allow: routers / Multicall3 / bridge / LST /
  Aave).
- unified-api-contracts `2a8599da` — cited the 138 registry addresses (canonical tokens / per-chain wrapped / Uniswap
  routers + pools).
- e2e-testing `2c077b0` — demo wallet `QG-allow`'d. (features/strategy/mtks/etc. cited or QG-allow'd in the same pass.)
- `defi_address_citation_baseline.yaml` ratcheted **DOWN to 0 for every repo** (incl. UAC 138→0).

**Live verification 2026-06-17:** full fleet ratchet sweep is **clean** — `check_defi_address_citations` **0
over-baseline**, and `check_no_fallback_imports` (5.94) + `check_ruff_rule_ratchet` (5.95) also **0**. The fleet is now
fully ratchet-clean → **the ratchet-exit-code hardening is UNBLOCKED and shippable** (see
`qg_base_service_ratchet_exit_code_2026_06_11.md`). This issue is closed; archive on next sweep.

## Status / what's already done

- ✅ instruments-service `tid251` regression fixed + landed (5.95 ratchet fleet-clean).
- ✅ Hardening diff verified + understood; held on `origin/wip-preserve/qg-ratchet-hardening-2026-06-16`.
- ✅ **Citation decision RESOLVED (cite-first, executed by Ikenna)** — fleet citation-ratchet-clean; hardening
  unblocked.

## Related

- `qg_base_service_ratchet_exit_code_2026_06_11.md` — the hardening this blocks.
- `scripts/quality_gates/defi_address_citation_baseline.yaml` — the baseline to seed (currently UAC=138 only).
- `scripts/quality_gates/check_defi_address_citations.py` — the checker (`--update-baseline` to seed, `--scope` per
  repo).
