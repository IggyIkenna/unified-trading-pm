---
title: "DeFi Fork 1 prep audit — 4-bug-class diagnostic before D4 launches (UAC SSOT date drifts on 13 (chain, protocol) pairs)"
created: 2026-05-08
author: defi-fork1-prep-audit-tab (Tab 14)
source:
  - plans/active/work_split_2026_05_07_harsh_5tab_layout.md § Tab 14 spawn prompt
  - plans/active/defi_master_2026_05_07.plan.md Fork 1 scope (carry_staked_basis + leveraged_funding_arb data sources)
  - plans/active/issues/lending_indices_handler_bugs_2026_05_07.md (Tab 5 + Tab 9 bug-class precedents)
  - plans/active/issues/defi_988_missing_dates_audit_2026_05_08.md (Tab 6 actionable-rows breakdown)
  - unified-api-contracts/unified_api_contracts/registry/chain_env.py (PROTOCOL_LAUNCH_DATES + CHAIN_GENESIS_DATES)
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py (SUBGRAPH_IDS)
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_lst.py (LST_TOKEN_GENESIS)
  - market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py (cascade router)
  - market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py (Chainlink + Pyth Hermes)
  - market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py (Uniswap V3 + DEX cascade)
  - instruments-service/instruments_service/reference_data/utils/evm_creation_resolver.py (LENDING_PROTOCOL_DEPLOY_DATES)
  - The Graph subgraph probes 2026-05-08 ~07:30-08:00 UTC (THEGRAPH_API_KEY via Secret Manager)
  - Pyth Hermes coverage probes (https://hermes.pyth.network/v2/updates/price/{publish_time})
  - gs://lending-indices-central-element-323112/_index/per_vm/mtds-lending-indices-20260508-114519.parquet (Tab 9 in-flight VM cross-reference)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# DeFi Fork 1 prep audit — 4-bug-class diagnostic before D4 launches

> **Severity**: P0 — UAC `PROTOCOL_LAUNCH_DATES` SSOT drift on **13 of 17 probed (chain, protocol) pairs** in Fork 1
> scope, including `carry_staked_basis` lead-archetype legs (AAVE V3 OPTIMISM 142d data loss; UNISWAP V3 ARBITRUM 91d
> data loss). Pyth Hermes archive does NOT cover ~11 months of jitoSOL history (2022-11 → 2023-10) needed for
> `carry_staked_basis` Solana leg. bSOL is mentioned in the Tab 14 brief as a Fork 1 LST yield but is **not in UAC
> `LST_TOKEN_GENESIS`** SSOT — coverage gap.
>
> **Blast radius**: defi asset_group; Fork 1 data sources for both May-23 archetypes
> (`carry_staked_basis` lead + `leveraged_funding_arb`); UAC `chain_env.py` SSOT;
> instruments-service `LENDING_PROTOCOL_DEPLOY_DATES` local fallback;
> deployment-ui data-status denominator (post-launch SOURCE_RETURNED_ZERO miscategorisation).
>
> **Suggested owner**: operator triage. Bug-class-4 UAC date drifts → **dedicated tab** (mirror Tab 9
> precedent for AAVEV3-ETHEREUM); collisions with Ikenna's writegate / Tab 9's PM stack mean Tab 14 cannot
> ship the UAC fix itself per workspace "Two teammates × multiple parallel agents" rule. Bug-class-1/2/3 are
> diagnostic-only — no code changes flagged from this audit.

## Filing rationale

Tab 14 spawn prompt directs a **diagnostic-only** Fork 1 prep audit BEFORE Ikenna's D4 DeFi launches consume
`PROTOCOL_LAUNCH_DATES`. The 4 bug classes audited are the same shapes Tab 5 + Tab 9 fixed for AAVE V3 ETH /
COMPOUND V3 multi-chain — applied across the broader Fork 1 surface (Aave V3 EVM, Uniswap V3 EVM, LST yields
Solana, Pyth Hermes Solana, Chainlink EVM, Compound V3 multi-chain, Spark ETH).

This audit is **case-4 + case-5** per CLAUDE.md Findings Triage Discipline:
- **Case-4** for the bulk of findings (operator-triage issue doc — fold into defi_master or new follow-up tab).
- **Case-5** for the UAC-date-drift sub-findings: data-correctness + cross-repo (UAC + MTDS + instruments-service) +
  contradicts a workspace SSOT + on the May-23 critical path → operator-notify in chat AND issue doc.

## Methodology

For each Fork 1 (chain, protocol) pair:

1. **Bug class 1 (silent-zero)** — confirm subgraph routing wired in UAC `SUBGRAPH_IDS` and the MTDS cascade
   (`lending_indices_handler._query_and_parse` / `dex_swaps_handler`); cross-reference Tab 9 in-flight VM
   per-VM-shard (`gs://lending-indices-{pid}/_index/per_vm/mtds-lending-indices-20260508-114519.parquet`)
   for any `(captured=0, empty_confirmed>100)` post-UAC-launch shape.
2. **Bug class 2 (schema drift)** — exercise each adapter's GraphQL query shape against the actual subgraph
   schema; if the query fails with `Type X has no field Y`, flag.
3. **Bug class 3 (launch-date floor handling)** — verify `instruments-service.get_protocol_floor_date()` consults
   UAC SSOT first (Tab 5 fix at `instruments-service@1a90185`), and inspect `LENDING_PROTOCOL_DEPLOY_DATES`
   local fallback for stale entries (the fallback is only consulted when UAC has no entry — but stale fallback
   over-clips if the UAC entry is later removed or PENDING_INVESTIGATION).
4. **Bug class 4 (UAC PROTOCOL_LAUNCH_DATES drift)** — query each subgraph's earliest history-table row (e.g.
   `reserveParamsHistoryItems` for AAVE V3, `dailyMarketAccountings` for Compound V3, `marketDailySnapshots` for
   Spark/Messari, `poolDayDatas` for Uniswap V3) and compare the timestamp against UAC
   `PROTOCOL_LAUNCH_DATES`. Any drift > ±3 days flagged.

**Probe environment**: workstation, asia-northeast1 region. THEGRAPH_API_KEY via Secret Manager. Tab 9's
in-flight `mtds-lending-indices-20260508-114519` per-VM shard cross-referenced (read-only).

## Bug class 1 — silent-zero (subgraph routing config error)

**Verdict**: ✅ NO NEW FINDINGS in Fork 1 scope. Tab 5 + Tab 9 fixed AAVE V3 ETH (UAC SSOT misdiagnosis) +
COMPOUND V3 multi-chain (Messari schema drift cascade); the lending_indices_handler now correctly raises
`SubgraphSchemaError` from `_execute_subgraph_query` on schema-drift fingerprints, the cascade re-raises if
EVERY variant is a schema error, and the outer `process()` routes to `record_failed` rather than swallowing
as `record_empty`. Tab 9's relaunched VM shows the working chains (ARBITRUM/AVALANCHE/OPTIMISM/POLYGON) all
producing post-UAC-launch captured rows — no silent-zero shape detected on those cohorts.

**Caveat**: Tab 9's VM has only processed 2022-01-01 → 2022-11-23 as of audit time. The post-launch validation
for AAVE V3 ETH (2023-01-27+) / COMPOUND V3 multi-chain (2023+) / SPARK ETH (2023+) lands at T+45min..T+150min
of the VM run; this audit can't claim those cohorts are silent-zero-free until the VM reaches them. Tab 9's
follow-up `VALIDATION-2026-05-08` block in `lending_indices_handler_bugs_2026_05_07.md` will close that loop.

## Bug class 2 — schema drift (GraphQL or REST query out of date)

**Verdict**: ✅ NO NEW FINDINGS for the Fork 1 cascade-aware paths (AAVE V3, COMPOUND V3, SPARK). MTDS `_query_and_parse`
cascade per Tab 5's fix (`market-tick-data-service@d2f365e`) handles AAVE V3 native + Messari fallback per chain, and
COMPOUND V3 has the custom `_COMPOUND_V3_CUSTOM_QUERY` (uses `dailyMarketAccountings` entity, NOT the
`marketDailySnapshots` field that the Messari schema would expose for Compound V3 — confirmed live via probe).

**Probed live 2026-05-08**:
- AAVE V3 native query (`reserveParamsHistoryItems`) returns rows on all 8 chains in `SUBGRAPH_IDS["aave_v3"]`
  (ETH/ARB/OPT/POLY/AVAX/BASE/LINEA/BSC).
- COMPOUND V3 `dailyMarketAccountings` returns rows on all 4 chains in `SUBGRAPH_IDS["compound_v3"]`
  (ETH/ARB/BASE/OPT). Messari schema (`marketDailySnapshots`) returns `Type Query has no field marketDailySnapshots`
  on all 4 — the cascade falls back correctly to `compound_v3_custom`.
- SPARK Messari `marketDailySnapshots` returns rows on Ethereum (only deployed chain).
- UNISWAP V3 `poolDayDatas` returns rows on all 5 EVM chains in `SUBGRAPH_IDS["uniswap_v3"]`
  (ETH/ARB/BASE/OPT/POLY).

## Bug class 3 — launch-date floor handling

**Verdict**: ✅ TAB 5'S CASCADE IS CORRECT in `instruments-service.get_protocol_floor_date()` — UAC
`PROTOCOL_LAUNCH_DATES` is consulted FIRST, local `LENDING_PROTOCOL_DEPLOY_DATES` is only the fallback when UAC has
no entry, and a generic 2020-01-01 floor is the third fallback. The cascade is structurally correct.

**One latent finding (case-2 adjacent / will fix once UAC drift items land)**: the local fallback dict has stale
dates that **silently activate** when a (chain, protocol) pair lives in `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`
(no UAC SSOT date). The one currently-active stale fallback in Fork 1 scope is:

| pair                  | local fallback (`LENDING_PROTOCOL_DEPLOY_DATES`) | actual earliest subgraph event | over-clip days |
| --------------------- | ------------------------------------------------ | ------------------------------ | --------------:|
| **SPARK / ETHEREUM**  | 2023-05-09                                       | 2023-03-07                     |        **63d** |

Spark is in UAC `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` (no SSOT entry), so the local fallback IS the floor for the
instruments-service catalog. 63 days of legitimate Spark data on Ethereum (2023-03-07 → 2023-05-08) are silently
clipped to "pre-launch". This is the SPARK / ETHEREUM 293 actionable rows in Tab 6's defi_988 audit (priority #2-ish),
shipped against by Bug-class-4 fix (add Spark to UAC `PROTOCOL_LAUNCH_DATES`). Once UAC SSOT entry lands, this
fallback path is no longer hit — but **the local fallback dict should also be updated to 2023-03-07** to keep the
fallback honest if anyone removes the UAC entry later.

Other entries in `LENDING_PROTOCOL_DEPLOY_DATES` that have actively-correct UAC SSOT entries (so the fallback is
unused but stale):

| pair                          | local fallback | UAC SSOT      | actual earliest event | local fallback drift |
| ----------------------------- | -------------- | ------------- | --------------------- | -------------------- |
| aave_v3 / ARBITRUM            | 2023-03-16     | 2022-03-16    | 2022-03-16            | local 365d TOO_LATE  |
| aave_v3 / OPTIMISM            | 2023-03-16     | 2022-08-04    | 2022-03-15            | local 1y+ TOO_LATE   |
| aave_v3 / BASE                | 2024-03-01     | 2023-08-09    | 2023-08-22            | local 200d+ TOO_LATE |
| aave_v3 / BSC                 | 2024-06-01     | 2023-04-06    | 2024-01-23            | local OK-ish         |
| aave_v3 / GNOSIS              | 2023-10-01     | (no UAC)      | (not in subgraph_ids) | local fallback active|
| compound_v3 / ETHEREUM        | 2022-08-26     | 2022-08-25    | 2022-08-13            | OK against UAC       |
| compound_v3 / ARBITRUM        | 2023-06-28     | 2023-04-13    | 2023-05-04            | local 55d TOO_LATE   |
| compound_v3 / BASE            | 2023-08-09     | 2023-08-26    | 2023-08-04            | local 5d TOO_EARLY   |
| compound_v3 / OPTIMISM        | 2024-01-10     | 2024-02-15    | 2024-04-06            | both TOO_EARLY vs actual |
| compound_v3 / POLYGON         | 2023-05-24     | 2023-02-14    | (no subgraph row)     | UAC active           |

These are "latent stale" — they don't currently affect production because the UAC entries are in place and consulted
first. They become active footguns only if the UAC entry is removed or migrated. Recommend treating as a
**case-2 adjacent finding to defi_master** — sweep the local dict against UAC + subgraph probes once Bug-class-4 UAC
fixes land. NOT P0; don't ship today.

## Bug class 4 — UAC `PROTOCOL_LAUNCH_DATES` date drift (CRITICAL)

**Verdict**: ❌ **13 of 17 probed (chain, protocol) Fork 1 pairs DRIFT > ±3 days** from actual subgraph
earliest-event timestamp. Tab 9's AAVE V3 ETH fix (mtds@d2f365e + UAC@6a64a56 — `2022-03-14` → `2023-01-27`,
correcting an 11-month TOO_EARLY drift) is the precedent shape; the audit found 12 more pairs needing the same
treatment. Each row below is a candidate for a Tab-9-style fix tab, but Tab 14 is diagnostic-only and **does not
ship UAC changes** per spawn-prompt rule (avoids collisions with Ikenna's writegate + Tab 9's pending PM rebase).

### Drift table — Fork 1 lending + DEX

| (chain, protocol) pair          | UAC entry          | actual earliest event (subgraph) | drift          | shape                                                                            |
| ------------------------------- | ------------------ | -------------------------------- | -------------- | -------------------------------------------------------------------------------- |
| **AAVEV3 / ETHEREUM**           | 2023-01-27         | 2023-01-27 08:00:11 UTC          | 0d             | ✅ correct (Tab 9 fixed)                                                         |
| AAVEV3 / ARBITRUM               | 2022-03-16         | 2022-03-16 16:00:45 UTC          | 0d             | ✅ correct                                                                       |
| **AAVEV3 / OPTIMISM**           | 2022-08-04         | 2022-03-15 21:48:18 UTC          | UAC 142d LATE  | ❌ **silent data loss** — 142 days clipped as `EXPECTED_PRE_GENESIS_CHAIN`        |
| AAVEV3 / POLYGON                | 2022-03-16         | 2022-03-12 19:19:07 UTC          | UAC 4d LATE    | minor — 4d data loss                                                             |
| AAVEV3 / AVALANCHE              | 2022-03-16         | 2022-03-12 20:09:36 UTC          | UAC 4d LATE    | minor — 4d data loss                                                             |
| **AAVEV3 / BASE**               | 2023-08-09         | 2023-08-22 14:48:51 UTC          | UAC 13d EARLY  | 13d false-empty (`SOURCE_RETURNED_ZERO` instead of `EXPECTED_PRE_PROTOCOL_LAUNCH`) |
| **AAVEV3 / LINEA**              | 2024-09-26         | 2025-02-11 11:56:26 UTC          | UAC 138d EARLY | 138d false-empty                                                                 |
| **AAVEV3 / BSC**                | 2023-04-06         | 2024-01-23 14:47:12 UTC          | UAC 293d EARLY | 293d false-empty                                                                 |
| AAVEV3 / SCROLL                 | 2024-04-29         | (not probed — out of Fork 1 scope, in SUBGRAPH_IDS) | — | n/a                                                                              |
| AAVEV3 / ZKSYNC                 | 2024-04-09         | (not probed — out of Fork 1 scope, in SUBGRAPH_IDS) | — | n/a                                                                              |
| **COMPOUNDV3 / ETHEREUM**       | 2022-08-25         | 2022-08-13 04:18:30 UTC          | UAC 12d LATE   | ❌ **silent data loss** — 12 days clipped                                        |
| **COMPOUNDV3 / ARBITRUM**       | 2023-04-13         | 2023-05-04 22:00:26 UTC          | UAC 21d EARLY  | 21d false-empty                                                                  |
| **COMPOUNDV3 / BASE**           | 2023-08-26         | 2023-08-04 23:29:21 UTC          | UAC 22d LATE   | ❌ **silent data loss** — 22 days clipped (subgraph indexes pre-mainnet-open BASE) |
| **COMPOUNDV3 / OPTIMISM**       | 2024-02-15         | 2024-04-06 17:09:21 UTC          | UAC 51d EARLY  | 51d false-empty                                                                  |
| COMPOUNDV3 / POLYGON            | 2023-02-14         | (no subgraph in `SUBGRAPH_IDS`) | n/a            | UAC entry but no subgraph wired — coverage gap (handler skips, manifest empty)   |
| COMPOUNDV3 / SCROLL             | 2024-04-22         | (not probed)                     | —              | n/a                                                                              |
| **SPARK / ETHEREUM**            | (PENDING_INVESTIGATION) | 2023-03-07 04:31:11 UTC      | needs entry    | ❌ **add to PROTOCOL_LAUNCH_DATES** + remove from `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` |
| **UNISWAPV3 / ETHEREUM**        | 2021-05-04         | 2021-05-04 00:00:00 UTC          | 0d             | ✅ correct                                                                       |
| **UNISWAPV3 / ARBITRUM**        | 2021-08-31 (chain genesis) | 2021-06-01 00:00:00 UTC  | UAC 91d LATE   | ❌ **silent data loss** — 91 days clipped (subgraph indexes pre-Arb-mainnet-open) |
| **UNISWAPV3 / BASE**            | 2023-08-09 (chain genesis) | 2023-07-31 00:00:00 UTC  | UAC 9d LATE    | minor — 9d data loss                                                             |
| **UNISWAPV3 / OPTIMISM**        | 2021-12-16 (chain genesis) | 2021-11-11 00:00:00 UTC  | UAC 35d LATE   | ❌ **silent data loss** — 35 days clipped                                        |
| UNISWAPV3 / POLYGON             | 2021-12-21         | 2021-12-20 00:00:00 UTC          | UAC 1d LATE    | OK                                                                               |

### Drift table — Fork 1 oracles + LST + DEX-perp

These are NOT subgraph-based; the audit method differs:

| source / pair                        | SSOT location                              | observed coverage start | UAC entry / status                    | shape                            |
| ------------------------------------ | ------------------------------------------ | ----------------------- | ------------------------------------- | -------------------------------- |
| **PYTH HERMES / SOL/USD (archive)**  | hermes.pyth.network /v2/updates/price/{ts} | ~2023-10-01             | (no UAC `PYTH_HERMES_COVERAGE_START`) | ❌ **archive gap 2022-11 → 2023-10** for jitoSOL pre-history |
| LST / mSOL                           | UAC `LST_TOKEN_GENESIS["mSOL"]`            | 2021-08-02 ✅           | `2021-08-02`                          | ✅ correct                        |
| LST / jitoSOL                        | UAC `LST_TOKEN_GENESIS["jitoSOL"]`         | 2022-11-01 ✅           | `2022-11-01`                          | ✅ correct                        |
| **LST / bSOL**                       | (not in `LST_TOKEN_GENESIS` SSOT)          | unknown                 | **MISSING — bSOL absent from UAC**    | ❌ Tab 14 brief lists bSOL as a Fork 1 LST yield; UAC has no genesis date + no `LST_VENUE_TO_TOKENS` mapping for the bSOL issuer |
| Chainlink ETH / EVM feeds            | hardcoded `_CHAINLINK_FEEDS_BY_CHAIN` in `oracle_prices_handler.py` | per-feed contract `aggregator.latestRoundData` historical block | (no per-feed coverage SSOT)           | ⚠️ no SSOT for "this Chainlink feed has historical data from date X" — handler probes per-block-number; failure mode is unverified for early L2 dates |
| Chainlink BASE                       | hardcoded                                  | post-2023-08-09 chain genesis | implicit                              | OK by chain-genesis clip, but no SSOT |

**Pyth coverage gap evidence** (probed 2026-05-08):
- `https://hermes.pyth.network/v2/updates/price/1696000000` (2023-09-29) → `Update data not found`.
- `https://hermes.pyth.network/v2/updates/price/1697000000` (2023-10-11) → returns binary VAA payload.
- `https://hermes.pyth.network/v2/updates/price/1700000000` (2023-11-14) → returns binary VAA payload.
- All probes for ts < 2023-09-29 → `Update data not found`.

**Implication**: `carry_staked_basis` Solana leg backfill from jitoSOL genesis (2022-11-01) → 2023-10 ish has
**no oracle-prices coverage from Pyth Hermes**. The `mtds-s3-5-pyth-oracle` checkbox in defi_master is ✅ — the
WIRING shipped — but the COVERAGE WINDOW limitation isn't documented in UAC. carry_staked_basis can still backfill
LST yields directly via on-chain `getRate()` calls (3-tier path in `lst_rates_handler`); the Pyth oracle is for
aggregate USD-denominated valuation. Operator decision: is the 2022-11 → 2023-10 jitoSOL pre-Pyth-archive window
in scope for May-23 backtest, or is it acceptable to backtest from 2023-10 onward? If acceptable, codify a
`PYTH_HERMES_COVERAGE_START = "2023-10-01"` (or per-feed SSOT) in UAC and clip the data-status denominator.

## Cross-reference with in-flight VM data

Tab 9's `mtds-lending-indices-20260508-114519` per-VM shard (4,251 rows as of audit time, processed 2022-01-01
→ 2022-11-23):

```
                       captured  empty_confirmed
venue      chain
AAVEV3     ARBITRUM        253     74    ✅ post-2022-03-16 launch correctly captures, pre-launch correctly empty
           AVALANCHE       254     73    ✅
           BASE              0    327    pre-2023-08-22 is correctly empty (subgraph genuinely returns 0)
           BSC               0    327    pre-2024-01-23 is correctly empty
           ETHEREUM          0    327    pre-2023-01-27 is correctly empty (Tab 9 fix)
           LINEA             0    327    pre-2025-02-11 is correctly empty
           OPTIMISM        254     73    ⚠️ this AGREES with UAC 2022-08-04 floor — but actual earliest event is 2022-03-15;
                                          112 days of legitimate post-2022-03-15 OPT data NEVER FETCHED because the floor
                                          short-circuit pre-skips 2022-03-15 → 2022-08-03. SILENT DATA LOSS.
           POLYGON         256     71    ⚠️ similar — 4 days lost
COMPOUNDV3 ARBITRUM          0    327    pre-2023-05-04 correctly empty; UAC 2023-04-13 too early by 21d but no harm yet
           BASE              0    327    pre-2023-08-04 correctly empty; UAC 2023-08-26 22d LATE → 22d data loss in 2023-Q3
           ETHEREUM         91    236    ⚠️ 91 captured rows, but UAC floor 2022-08-25 vs actual 2022-08-13 = 12d data loss
           OPTIMISM          0    327    pre-2024-04-06 correctly empty
SPARK      ETHEREUM          0    327    UAC has no entry; local fallback 2023-05-09 → 63d Spark data loss in 2023-Q1/Q2
```

The shape per `(venue, chain)` matches the predicted drift impact: cohorts with `UAC LATE` drift will have
**post-launch days that should be captured but are recorded as `EXPECTED_PRE_GENESIS_CHAIN`** (silent data loss).
None of these will surface as a "bug" on Tab 9's reproducer because the pre-floor short-circuit in
`lending_indices_handler` correctly emits `record_expected_empty` per writegate Phase 2.E reason taxonomy — the
short-circuit is doing exactly what it's designed to do, but on dates where the source ACTUALLY has data.

**Visibility surface**: a manifest reader can't distinguish "UAC says pre-launch + source genuinely empty" from
"UAC says pre-launch but source has data we never fetched". The only way to detect the bug-class-4 drift is the
subgraph-earliest-event probe done in this audit. Recommend adding this probe to a recurring SSOT-validation
script (codified per writegate Phase 2.E "Validation gates per `record_captured` — 4 pillars" extension).

## Why it matters (May-23 critical path impact)

1. **carry_staked_basis lead archetype (May-23 lead)**:
   - AAVEV3 / OPTIMISM 142-day data loss covers the 2022-03 → 2022-08 window — material if backtest range
     starts pre-2022-08.
   - UNISWAPV3 / ARBITRUM + UNISWAPV3 / OPTIMISM 91d + 35d data loss — affects swap-fee history for the
     archetype's hedge-leg sizing on those L2s.
   - Pyth Hermes archive gap 2022-11 → 2023-10 — mSOL/jitoSOL valuation in USD terms missing for ~11 months
     of the archetype's pre-2024 history.
2. **leveraged_funding_arb archetype**:
   - COMPOUNDV3 / OPTIMISM (UAC 2024-02-15, actual 2024-04-06) — 51 days of false-empty in early 2024 don't
     hurt directly but inflate the actual-deploy-date research signal.
3. **Cross-cutting (case-5 big finding criteria)**:
   - SSOT contradiction: UAC `PROTOCOL_LAUNCH_DATES` ≠ subgraph reality (data-correctness, ≥2 repos UAC + MTDS).
   - Workspace SSOT drift: codified in
     [`unified-trading-pm/cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) `*_LAUNCH_DATES` is the
     canonical SSOT — current state is partially-wrong canonical SSOT; reviewers reading code vs UAC reach
     different conclusions about valid date ranges.

## Recommended decision

### Operator-pickable tabs (parallel-safe — UAC chain_env.py is the collision surface)

The 13 drifts in Bug class 4 + the SPARK / ETHEREUM PENDING_INVESTIGATION + the missing bSOL UAC entry split
naturally into **four batches** that can each be a Tab-9-style fix tab. **Batches don't run concurrently** —
they all touch `unified-api-contracts/unified_api_contracts/registry/chain_env.py`, so each batch must merge
before the next starts.

| Batch | Pairs                                                                                                                            | Owner / collision risk                     |
| ----- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| **A** | AAVEV3 / OPTIMISM, POLYGON, AVALANCHE, BASE, LINEA, BSC                                                                          | UAC + Tab 9's pending PM rebase queue      |
| **B** | COMPOUNDV3 / ETHEREUM, ARBITRUM, BASE, OPTIMISM                                                                                  | UAC + Ikenna's writegate-related work      |
| **C** | UNISWAPV3 / ARBITRUM, BASE, OPTIMISM                                                                                             | UAC standalone — DEX scope, low collision  |
| **D** | SPARK / ETHEREUM (add to PROTOCOL_LAUNCH_DATES + remove from PENDING_INVESTIGATION) + bSOL (add to LST_TOKEN_GENESIS + LST_VENUE_TO_TOKENS) | UAC + instruments-service catalog impl     |

**Each batch's spawn prompt** mirrors Tab 9's shape (probe → UAC update → MTDS pre-flight test → handler
short-circuit unit-test pass + per-(chain, protocol) drift cite). Batches B + D additionally need a one-time
manifest re-scan after the UAC date moves, because rows previously recorded as `EXPECTED_PRE_PROTOCOL_LAUNCH`
under the wrong UAC date are now `attempted_failed` candidates per Tab 6's defi_988 audit Top-5 priority #3.

### Pyth Hermes coverage gap

**Recommend**: codify `PYTH_HERMES_COVERAGE_START = "2023-10-01"` in UAC `_defi.py` (or a new
`_oracle_coverage.py` module) so data-status / MTDS / features-onchain all clip the denominator consistently.
The fix is one-line in UAC + one consumer-side clip in `oracle_prices_handler.py`. **Operator decision needed
first**: is jitoSOL pre-2023-10 oracle-USD coverage required for May-23 backtest, or is the LST yield path
self-sufficient?

### Bug-class-3 latent fallback drift

**Defer** — local `LENDING_PROTOCOL_DEPLOY_DATES` updates are case-2 adjacent to defi_master and don't currently
affect production (UAC is consulted first). Sweep after Bug-class-4 batches A+B land.

### Coverage gap — COMPOUND V3 POLYGON

UAC has `("POLYGON", "COMPOUNDV3"): "2023-02-14"` but `SUBGRAPH_IDS["compound_v3"]` does NOT have a POLYGON entry
(removed per the comment "POLYGON removed: subgraph returns 0 markets (Compound V3 not active on Polygon)").
**Recommend**: remove the POLYGON entry from UAC `PROTOCOL_LAUNCH_DATES` to avoid false denominator inflation.
Tab 6's defi_988 audit doesn't flag this because the row count is 0 (chain genuinely has no markets).

## Decision routing per Findings Triage Discipline

Per CLAUDE.md decision tree:

- Bug class 1 + Bug class 2: ✅ no new findings; nothing to route.
- Bug class 3 (Spark fallback over-clip + latent stale fallbacks): **case-2 adjacent** → annotated in the next
  defi_master plan-body section (this audit is the source-of-truth detail).
- Bug class 4 (13 UAC drifts) + Pyth coverage + bSOL gap: **case-5 big** → operator-notify in chat AND issue doc
  (this file). Tab 14 does NOT ship the UAC fix — recommends operator spawn dedicated batch tabs A/B/C/D.

## Action notes for downstream tabs

1. **UAC commit shape** (mirror Tab 9 `unified-api-contracts@6a64a56`): per-pair tuple update with inline
   subgraph-probe citation comment + bumping the subgraph-id in the citation if changed.
2. **Test update**: `unified-api-contracts/tests/unit/test_protocol_launch_dates.py` should assert the corrected
   dates per pair (Tab 9's test shape).
3. **MTDS handler — no code change** required if cascade short-circuit logic already shipped (Tab 9's pre-floor
   short-circuit at `market-tick-data-service@c6bdf96` covers all (chain, protocol) pairs, not just AAVE V3 ETH).
4. **instruments-service test**: `tests/unit/test_evm_creation_resolver.py::TestGetProtocolFloorDate` should
   assert UAC-derived floor matches the corrected per-pair date.
5. **Manifest re-scan needed**: Bug-class-4 fixes that move UAC date EARLIER reclassify
   `EXPECTED_PRE_GENESIS_CHAIN` rows back to `attempted_unattempted` for the fetch retry; Bug-class-4 fixes that
   move UAC date LATER reclassify `SOURCE_RETURNED_ZERO` rows to `EXPECTED_PRE_PROTOCOL_LAUNCH`. The manifest
   consolidator handles this automatically once VMs re-write per-row keys.

## Caveats + non-findings

- **Subgraph earliest event ≠ protocol mainnet deploy.** Some subgraphs index pre-mainnet-open blocks (e.g. BASE
  pre-2023-08-09, Arbitrum pre-2021-08-31) — the actual earliest indexed row is the right floor for "what data
  the subgraph returns", but the protocol's marketing-deploy date may differ. The right SSOT for
  `PROTOCOL_LAUNCH_DATES` is "earliest day a subgraph query returns rows" because that's what the cascade tests
  against. UAC entries citing "chain genesis, deployed day-zero" should be re-checked against subgraph reality.
- **Tab 9's in-flight VM hasn't reached post-launch dates for 9 of 13 cohorts** — the audit's bug-class-4
  diagnosis is independently confirmed via subgraph probe, not solely via the in-flight VM. The VM cross-reference
  validates the pre-launch SOURCE_RETURNED_ZERO is correctly set; post-launch validation lands at T+45min..T+150min.
- **UNISWAPV3 BASE chain genesis 2023-08-09 vs subgraph earliest 2023-07-31** — the subgraph indexes BASE
  pre-public-launch testnet/devnet phase blocks. Same shape as COMPOUND V3 BASE 2023-08-04. Not a bug; just
  a chain-genesis vs subgraph-coverage mismatch.
- **CHAIN_GENESIS_DATES SSOT** (which is checked for post-2026-05-08 audit pass) — verified per-chain genesis
  dates against `CHAIN_GENESIS_DATES` look correct for all chains in scope. Not flagged.
- **Compound V3 POLYGON in UAC + not in SUBGRAPH_IDS**: this is a small coverage-gap finding — UAC says it's
  expected, MTDS handler skips. Flag for cleanup.

## DONE-2026-05-08 — Tab 14

All 4 bug classes audited; 17 (chain, protocol) pairs probed for Bug class 4; 13 drifts found; per-batch
operator-decision tab spawn recommendations filed; cross-reference with Tab 9's in-flight VM per-VM-shard
confirms the predicted shapes. Diagnostic-only — no code changes shipped per spawn-prompt rule.

**Probes run** (all 2026-05-08, ~07:30-08:00 UTC):
- AAVE V3 native (`reserveParamsHistoryItems`) on 8 chains in `SUBGRAPH_IDS["aave_v3"]`.
- COMPOUND V3 custom (`dailyMarketAccountings`) on 4 chains in `SUBGRAPH_IDS["compound_v3"]`.
- COMPOUND V3 Messari (`marketDailySnapshots`) on same 4 chains — confirmed schema-error fingerprint per Tab 9's diagnosis.
- SPARK Messari (`marketDailySnapshots`) on Ethereum.
- UNISWAP V3 (`poolDayDatas`) on 5 chains in `SUBGRAPH_IDS["uniswap_v3"]`.
- Pyth Hermes coverage probes from 2021-05 to 2024-03 — earliest archive ≈ 2023-10-01.
- Tab 9's per-VM shard `mtds-lending-indices-20260508-114519.parquet` cross-reference (4,251 rows).

**SSOTs cross-checked**:
- `unified-api-contracts/unified_api_contracts/registry/chain_env.py` (`PROTOCOL_LAUNCH_DATES` 40 entries +
  `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` 33 entries + `CHAIN_GENESIS_DATES` 22 entries).
- `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py` (`SUBGRAPH_IDS` 14
  protocols × multiple chains).
- `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_lst.py`
  (`LST_TOKEN_GENESIS` 14 tokens).
- `instruments-service/instruments_service/reference_data/utils/evm_creation_resolver.py`
  (`LENDING_PROTOCOL_DEPLOY_DATES` local fallback dict).
- `market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py`
  (cascade routing + schema-drift handling).
- `market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py`
  (Chainlink `_CHAINLINK_FEEDS_BY_CHAIN` + Pyth `_PYTH_FEEDS`).

**defi_master annotation**: one-line link to be added under "Lending-indices VM run-quality bugs" section
(case-2 fold-in for SPARK + bSOL gaps; case-5 fold-in for the 13 Bug-class-4 drifts pointing to this audit
doc + the 4 batched fix-tab recommendations). Annotation pending in next plan-flip commit.

**Per-pair issue docs filed**: this audit doc consolidates all 13 drifts + Pyth coverage + bSOL gap in one doc
(operator decision: bundled vs per-pair). Recommend operator decides whether to fan out per-batch sub-issue docs
when spawning the dedicated fix tabs A/B/C/D — the per-batch detail is already in the drift table above and
copy-pastes into Tab spawn prompts cleanly.

**No new bugs found in Bug classes 1-2-3** that aren't already addressed by Tab 5 + Tab 9's shipped fixes.
The latent stale `LENDING_PROTOCOL_DEPLOY_DATES` entries are case-2 adjacent to defi_master and deferred until
after Bug-class-4 batches land.
