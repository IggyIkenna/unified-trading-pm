---
title: "DeFi 988-missing-dates audit — actionable breakdown by (chain, protocol, data_type)"
created: 2026-05-08
author: defi-988-audit-tab (Tab 6)
source:
  - plans/active/defi_master_2026_05_07.plan.md § "Tail-chain / mid-tier protocol coverage (DeFi data-status — 988 dates
    missing)"
  - unified_api_contracts/registry/chain_env.py (CHAIN_GENESIS_DATES + PROTOCOL_LAUNCH_DATES SSOTs)
  - 10 DeFi GCS manifest buckets at gs://*-{PID}/_index/availability_index.parquet (probed 2026-05-08 05:30 UTC)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# DeFi 988-missing-dates audit

> **Severity**: P1 — diagnostic-only audit; no code changes. Outputs feed Ikenna's D4 DeFi launches and Harsh's D4
> manifest rescan to target the `carry_staked_basis` + `leveraged_funding_arb` chain set first. **Blast radius**: defi
> asset_group only — `defi_master_2026_05_07.plan.md` is the parent. **Suggested owner**: defi_master plan (operator
> triage which findings fold into D4 backfill todos).

## Top-line numbers

Probed all 10 DeFi GCS manifest buckets (`market-data-tick-defi-{pid}` asset-group canonical + 9 per-data-type buckets)
at 2026-05-08 05:30 UTC. **9 of 10 buckets** carry the v5 schema with `capture_status` + `error_reason`;
`solana-defi-{pid}` is on legacy v3 (no capture_status column, last write 2026-04-13) and is excluded — it does not
belong on the May-23 archetype critical path (the asset-group canonical bucket already covers Solana LST data).

| metric                                                                        | rows          |
| ----------------------------------------------------------------------------- | ------------- |
| Total non-captured rows across 7 v5-schema buckets                            | **1,302,654** |
| `legit_pre_genesis` (chain pre-genesis per `CHAIN_GENESIS_DATES`)             | 689,842 (53%) |
| `legit_pre_protocol_launch` (pre-protocol-launch per `PROTOCOL_LAUNCH_DATES`) | 599,180 (46%) |
| `source_returned_zero` (typed honest-empty in `market-data-tick-defi`)        | 6,911 (0.53%) |
| `actually_failed` (subgraph 404 / RPC error / blank-reason failures)          | 4,036 (0.31%) |
| `actually_empty_blank_reason` (silent-fallback risk — predates UTL@68b3804a)  | 2,685 (0.21%) |
| **Actionable total (non-legit)**                                              | **13,632**    |
| Distinct iso_dates with ≥1 non-captured row                                   | 3,027         |
| Distinct iso_dates with ≥1 actionable row                                     | **2,234**     |

**Reconciliation with deployment-ui's "988 dates missing" headline**: the deployment-ui aggregation that yields 988
differs from any single-bucket or all-bucket distinct-date count this audit produced (3,027 / 2,234 / 1,455 depending on
filter). The headline likely applies an additional filter (e.g. min-shards-per-date or only rolls up dates where
`(captured + empty_confirmed)` < expected for ≥1 chain×protocol). **Not blocking** for the backfill priority decision —
the actionable breakdown below is what matters for May-23.

## Per-bucket × band counts

| bucket                  | actually_empty_blank_reason | actually_failed | legit_pre_genesis | legit_pre_protocol_launch | source_returned_zero |
| ----------------------- | --------------------------: | --------------: | ----------------: | ------------------------: | -------------------: |
| `dex-swaps`             |                       1,427 |           1,782 |                 0 |                         0 |                    0 |
| `evm-defi`              |                         363 |               0 |             1,169 |                       995 |                    0 |
| `gas-fees`              |                          12 |              12 |                 0 |                         0 |                    0 |
| `lending-indices`       |                          65 |           2,123 |                 0 |                       145 |                    0 |
| `market-data-tick-defi` |                           0 |             119 |           688,220 |                   598,040 |                6,911 |
| `oracle-prices`         |                           0 |               0 |               453 |                         0 |                    0 |
| `perp-funding`          |                         818 |               0 |                 0 |                         0 |                    0 |

**Reads:**

- The asset-group canonical (`market-data-tick-defi`) is dominated by SSOT-correct pre-genesis/pre-launch clipping. Only
  6,911 source_returned_zero rows + 119 attempted_failed rows are non-trivially actionable.
- `lending-indices` carries 2,123 attempted_failed (subgraph 404 GETs) — overlaps with **Tab 5** in-flight work
  (`lending_indices_handler_bugs_2026_05_07.md` Bug 1 + Bug 2 fixes).
- `dex-swaps` has 1,782 attempted_failed + 1,427 blank-reason empty_confirmed — overlaps with the defi_master P0 todo
  "Subgraph schema-mismatch fixes for PancakeSwap V3, SushiSwap V3, Aerodrome V3, Camelot V3" (line 358-359).
- `perp-funding` has 818 blank-reason empty_confirmed and **zero captured ASTER rows** (see priority #4).
- `evm-defi` has 363 blank-reason empty_confirmed (mostly Eth/Arb/Base AAVE V3 + Compound V3) — same silent-fallback
  class as cefi tardis; relaunch-with-typed-reason will reclassify most.

## Top 25 actionable shards by row count

| bucket                | chain     | venue/protocol | data_type         | rows | distinct_dates | date_min   | date_max   |
| --------------------- | --------- | -------------- | ----------------- | ---: | -------------: | ---------- | ---------- |
| market-data-tick-defi | ETHEREUM  | YEARNV3        | VAULT_SHARE_PRICE | 1533 |           1533 | 2020-01-01 | 2024-03-12 |
| market-data-tick-defi | ETHEREUM  | MORPHOVAULTS   | VAULT_SHARE_PRICE | 1465 |           1465 | 2020-01-01 | 2026-05-03 |
| market-data-tick-defi | ETHEREUM  | ETHENA         | VAULT_SHARE_PRICE | 1414 |           1414 | 2020-01-01 | 2023-11-14 |
| market-data-tick-defi | ETHEREUM  | FRAX           | VAULT_SHARE_PRICE | 1387 |           1387 | 2020-01-01 | 2023-10-18 |
| market-data-tick-defi | ETHEREUM  | MAKER          | VAULT_SHARE_PRICE | 1113 |           1113 | 2020-01-01 | 2023-01-17 |
| dex-swaps             | OPTIMISM  | CURVE          | DEX_SWAPS         |  796 |            796 | 2021-01-01 | 2026-04-14 |
| perp-funding          | ASTER     | ASTER          | PERP_FUNDING      |  759 |            759 | 2022-11-01 | 2026-04-14 |
| dex-swaps             | BSC       | PANCAKESWAPV3  | DEX_SWAPS         |  701 |            701 | 2021-01-01 | 2026-04-14 |
| lending-indices       | LINEA     | AAVEV3         | LENDING_INDICES   |  357 |            357 | 2022-01-01 | 2025-02-10 |
| evm-defi              | ETHEREUM  | AAVEV3         | LENDING_INDICES   |  319 |            319 | 2022-03-14 | 2023-01-26 |
| lending-indices       | ETHEREUM  | SPARK          | LENDING_INDICES   |  293 |            293 | 2022-01-01 | 2024-12-13 |
| lending-indices       | OPTIMISM  | COMPOUNDV3     | LENDING_INDICES   |  219 |            219 | 2022-01-01 | 2023-08-27 |
| lending-indices       | BSC       | AAVEV3         | LENDING_INDICES   |  219 |            219 | 2022-01-01 | 2023-08-27 |
| lending-indices       | BASE      | AAVEV3         | LENDING_INDICES   |  214 |            214 | 2022-01-01 | 2023-08-22 |
| lending-indices       | BASE      | COMPOUNDV3     | LENDING_INDICES   |  211 |            211 | 2022-01-01 | 2023-08-19 |
| lending-indices       | ETHEREUM  | AAVEV3         | LENDING_INDICES   |  132 |            132 | 2022-01-01 | 2022-05-12 |
| lending-indices       | ARBITRUM  | COMPOUNDV3     | LENDING_INDICES   |  131 |            131 | 2022-01-01 | 2022-05-11 |
| lending-indices       | ETHEREUM  | COMPOUNDV3     | LENDING_INDICES   |  131 |            131 | 2022-01-01 | 2022-05-11 |
| dex-swaps             | POLYGON   | UNISWAPV3      | DEX_SWAPS         |  120 |            120 | 2021-01-01 | 2025-04-08 |
| dex-swaps             | ARBITRUM  | SUSHISWAP      | DEX_SWAPS         |   97 |             97 | 2021-01-01 | 2025-06-09 |
| dex-swaps             | AVALANCHE | SUSHISWAPV3    | DEX_SWAPS         |   97 |             97 | 2021-01-01 | 2024-10-22 |
| dex-swaps             | AVALANCHE | BALANCER       | DEX_SWAPS         |   96 |             96 | 2021-01-01 | 2023-02-02 |
| dex-swaps             | BASE      | UNISWAPV3      | DEX_SWAPS         |   96 |             96 | 2021-01-01 | 2023-02-02 |
| dex-swaps             | BASE      | PANCAKESWAPV3  | DEX_SWAPS         |   96 |             96 | 2021-01-01 | 2023-02-02 |
| dex-swaps             | BASE      | SUSHISWAPV3    | DEX_SWAPS         |   96 |             96 | 2021-01-01 | 2023-02-02 |

## Archetype-relevance ranking

### `carry_staked_basis` (May-23 lead) — 10,479 actionable rows

Chains in scope: ETHEREUM, SOLANA, ARBITRUM, BASE. Protocols: AAVE V3, LIDO, ROCKET POOL, ETHER.FI, ETHENA, MAKER
(ETH-side LST + lending) + JITO, MARINADE (Solana LST) + PYTH, CHAINLINK (oracles).

Top concentrations (via the breakdown above):

- **VAULT_SHARE_PRICE on Ethereum vaults**: 6,912 rows for YEARNV3 + MORPHOVAULTS + ETHENA + FRAX + MAKER — all
  currently typed `SOURCE_RETURNED_ZERO`. **Most are pre-protocol-launch** (Ethena 2024-02-19; YEARN V3 2023-07;
  MorphoVaults 2024-06; FRAX vault structure 2020-12) but classified as zero rather than as pre-launch. UAC
  `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` already lists ETHEREUM↔YEARNV3 / MORPHOVAULTS as pending; tightening the
  SSOT will reclassify most of these from `source_returned_zero` to `legit_pre_protocol_launch`. **Action**: research +
  add launch dates to `PROTOCOL_LAUNCH_DATES` (UAC `chain_env.py`), rerun the data-status enumerator's pre-flight clip
  pass.
- **lending-indices LINEA / BSC / BASE / OPTIMISM AAVE V3 + COMPOUND V3**: ~1,400 rows of attempted_failed with 404
  GETs. Tab 5's lending_indices_handler_bugs ships fixes for AAVE V3 ETH (Bug 1) + COMPOUND V3 schema drift (Bug 2). Tab
  5 will resolve Eth + Arb + Base + Optimism Compound V3 cohorts; the LINEA + BSC cohorts are NEW shards that need
  separate routing config.
- **evm-defi ETHEREUM AAVEV3 LENDING_INDICES**: 319 blank-reason empty_confirmed for 2022-03-14 → 2023-01-26 (the period
  AAVE V3 ETH was live but the writegate was running pre-UTL@68b3804a). Adapter relaunch with typed reasons will
  reclassify; either captures real data or stamps `EXPECTED_PRE_PROTOCOL_LAUNCH` /`SOURCE_RETURNED_ZERO`.

### `leveraged_funding_arb` — 818 actionable rows (ALL on perp-funding bucket)

| chain       | venue       | data_type    | rows | date_min   | date_max   |
| ----------- | ----------- | ------------ | ---: | ---------- | ---------- |
| ASTER       | ASTER       | PERP_FUNDING |  759 | 2022-11-01 | 2026-04-14 |
| HYPERLIQUID | HYPERLIQUID | PERP_FUNDING |   59 | 2022-11-01 | 2022-12-29 |

**ASTER**: 759 empty_confirmed rows with **zero captured rows**. Aster mainnet launched ~2024-09 (per public sources);
2022-11-01 → 2024-09 dates are pre-venue-launch and should be `EXPECTED_PRE_GENESIS_CHAIN`-equivalent (ASTER is not
currently in `CHAIN_GENESIS_DATES` SSOT — the SSOT does not yet recognise ASTER as a chain). **Post-launch dates
(2024-09 → 2026-04) returning zero is a CORRECTNESS RISK** for the leveraged_funding_arb archetype: the funding adapter
either has not yet been wired to ASTER, or is silently writing empty placeholders. **Operator decision needed**: is
ASTER on the May-23 hedge-leg path? If yes, this is a P0 correctness gap.

**HYPERLIQUID**: 59 empty_confirmed rows for 2022-11-01 → 2022-12-29 only. HYPERLIQUID mainnet launch was 2023-06; these
are pre-launch dates and would reclassify to `EXPECTED_PRE_GENESIS_CHAIN` once HYPERLIQUID joins `CHAIN_GENESIS_DATES`.
The remaining captured rows (4,757) cover the live window correctly.

## Top-5 priority list for D4 backfill action

| #   | Action                                                                                                                                                         | Resolves rows | Owner / route                                                                                                                                              |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Tab 5 ships lending_indices_handler bugs**: AAVE V3 ETH silent-zero + Compound V3 schema drift                                                               | ~2,442        | Tab 5 in flight; covers ~2,123 lending-indices attempted_failed + 319 evm-defi blank Eth-AAVE-V3                                                           |
| 2   | **DEX subgraph schema fixes** (defi_master line 358): PancakeSwap V3 / SushiSwap V3 / Aerodrome V3 / Camelot V3 across BSC / Base / Arb / Avax / Eth / Polygon | ~1,400        | `defi_master` D4 todo "Mid-tier 60% coverage" — needs subgraph URL + GraphQL query update                                                                  |
| 3   | **PROTOCOL_LAUNCH_DATES tightening** for ETHEREUM YEARNV3 + MORPHOVAULTS + (ETHENA/FRAX/MAKER vault variant)                                                   | ~6,912        | UAC `chain_env.py` SSOT update + UAC `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` removal — reclassifies SOURCE_RETURNED_ZERO → legit_pre_protocol_launch      |
| 4   | **ASTER chain genesis SSOT + perp-funding adapter audit** (P0 if ASTER on hedge-leg path)                                                                      | 759           | UAC `CHAIN_GENESIS_DATES` add ASTER (2024-09 mainnet) + verify `perp-funding` adapter routes ASTER post-launch correctly; needs operator priority decision |
| 5   | **Lending-indices LINEA / BSC routing config** (separate from Tab 5's Eth scope)                                                                               | ~576          | `mtds-lending-indices` adapter — chain→subgraph URL config for LINEA + BSC + remaining unfixed cohorts                                                     |

## Caveats + non-findings

- The `solana-defi-{pid}` bucket (5,028 rows, last write 2026-04-13) is on legacy v3 schema (no `capture_status`).
  Excluded from this audit. Solana LST data is correctly served via the asset-group canonical bucket
  (`market-data-tick-defi`) with proper v5 typing — `JITO` + `MARINADE` for SOLANA show no attempted_failed or
  actually_empty_blank_reason rows in the canonical bucket.
- The `instruments-store-defi-{pid}` bucket has 57,466 rows with NULL `capture_status` and blank `data_type` — all
  written in a single bulk pass at 2026-05-04 15:46 UTC across all chains/protocols. These appear to be **pre-populated
  `expected_unattempted` rows from the v2 enumerator that lack the `capture_status` column stamp**. Cosmetic schema gap;
  reclassification to `expected_unattempted` is a writegate Phase 3.D.5 follow-up. Not actionable for D4 backfill.
- The `lst-rates-{pid}` bucket is **100% captured** (4,356 rows, no non-captured). The `carry_staked_basis` archetype's
  primary input data type is in good shape.
- The `oracle-prices-{pid}` bucket has 453 empty_confirmed rows split evenly across ARBITRUM / BASE / OPTIMISM (151
  each). All on dates pre-2022-08 (i.e. pre-Chainlink-L2-coverage). Stamped without typed reason — same blank-reason
  class as the others; reclassification will set them to `legit_pre_protocol_launch` once `CHAINLINK` per-chain launch
  dates land in `PROTOCOL_LAUNCH_DATES`.

## Recommendation

**Fold-in**: priorities #1 + #5 fold into existing `defi_master_2026_05_07.plan.md` "Lending-indices VM run-quality
bugs" section (which already cross-references Tab 5's plan-of-record). Priority #2 folds into the existing P0 todo on
line 357-359. Priorities #3 and #4 are NEW work that needs operator priority decision before adding as P0 todos to
defi_master:

- **#3** (UAC SSOT tightening): low-risk doc-level fix; recommend ship in Harsh's main-agent session as a small commit
  pair (UAC + PM) once operator OKs the approach.
- **#4** (ASTER): operator decision needed first — confirm whether ASTER is on the May-23 hedge-leg critical path. If
  yes, P0 routing audit + chain-genesis SSOT seed; if no, defer post-cutover.

No new plan needed — all 5 priorities fit into the existing `defi_master` body sections.

## DONE-2026-05-08

- Audit doc filed: `plans/active/issues/defi_988_missing_dates_audit_2026_05_08.md` (this file).
- Probes run: `/tmp/defi_988_audit_priority.py` + `/tmp/defi_988_audit_extras.py` against 10 DeFi GCS manifest buckets
  at 2026-05-08 05:30 UTC.
- SSOTs cross-checked: UAC `CHAIN_GENESIS_DATES` (22 chains) + `PROTOCOL_LAUNCH_DATES` (40 known + 33
  `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`) at `unified_api_contracts/registry/chain_env.py`.
- defi_master annotation: one-line link added to "Tail-chain / mid-tier protocol coverage" section.
- No code changes — diagnostic-only per Tab 6 spawn brief.
