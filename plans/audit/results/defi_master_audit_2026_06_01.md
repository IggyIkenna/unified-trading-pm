---
type: audit-result
title: DeFi Master — Strategy Data-Coverage Audit Result (2026-06-01)
epic: defi_master
auditor: ikenna (interactive slot 1)
date: 2026-06-01
status: AMBER
instructions_ref: plans/audit/instructions/defi_master_audit_instructions.md
correction_note:
  First pass reported "0% captured / data missing" — that was a methodology error (read only the market-data-tick-defi
  phantom grid). Corrected after reading the dedicated per-data_type buckets. Data EXISTS (79-96% captured); the real
  problems are data-in-wrong-form (cleanup/migration), not absence.
scope: Strategy Data-Coverage Audit (items o-v) — staked basis carry / funding rate arb / basis carry + Solana MVP
data_source:
  dedicated DeFi buckets (lst-rates/lending-indices/oracle-prices/perp-funding/dex-pools/dex-swaps) +
  market-data-tick-{defi,cefi,tradfi} prd indexes — read from actual manifest + GCS object counts
---

# DeFi Master — Strategy Data-Coverage Audit Result (2026-06-01)

> **Correction banner**: an earlier revision of this file concluded all three strategies were RED with "0% captured /
> data genuinely missing." **That was false** — it read only `market-data-tick-defi-*/_index/`, which holds a phantom
> empty grid. The real data lives in **dedicated per-data_type buckets** and is 79–96% captured. The genesis of the new
> instructions **Step 1.5 "Find the data before declaring it missing"** is this exact mistake. Corrected findings below.

## Headline — the data EXISTS; the problem is data-in-wrong-form, not absence

| data_type         | dedicated bucket    | captured %              | date range              | objects | wrong-form problem                                                                |
| ----------------- | ------------------- | ----------------------- | ----------------------- | ------- | --------------------------------------------------------------------------------- |
| `lst_rates`       | `lst-rates-*`       | **92%** (15,354/16,766) | 2020-01-01 → 2026-05-19 | 34,843  | I wrongly called this "absent"; `market-data-tick-defi` calls it `staking_yields` |
| `lending_indices` | `lending-indices-*` | **91%** (12,687/13,963) | 2022-01-01 → 2026-05-28 | 138,345 | both `lending-indices` + `lending_indices` data_type strings coexist              |
| `oracle_prices`   | `oracle-prices-*`   | **79%** (7,692/9,717)   | 2021-01-01 → 2026-05-19 | 13,177  | Chainlink + Pyth captured; partial window                                         |
| `perp_funding`    | `perp-funding-*`    | **55%** (2,289/4,138)   | 2022-11-01 → 2026-05-16 | 11,489  | DeFi perps only (GMX/HYPERLIQUID/ASTER/PACIFICA); Drift/CeFi separate             |
| `dex_pools`       | `dex-pools-*`       | **96%** (72,658/75,983) | 2021-01-01 → 2026-04-22 | 185,078 | both `dex-pools` + `dex_pools` coexist                                            |
| `dex_swaps`       | `dex-swaps-*`       | **93%** (43,282/46,491) | 2021-01-01 → 2026-04-14 | 46,491  | both `dex-swaps` + `dex_swaps` coexist                                            |

## Real findings (corrected) — cleanup/migration, with a few genuine gaps

- **(C1) Phantom empty grid in `market-data-tick-defi`** — the index there shows `empty_confirmed` for
  `perp_funding`/`staking_yields`/`lending_indices`/`oracle_prices` attributed to a cartesian `data_type × venue`
  cross-product in legacy `VENUE-CHAIN` format (e.g. `perp_funding` on `UNISWAPV3-ETHEREUM`, `LIDO-ETHEREUM`). The real
  captured rows are in the dedicated buckets. **Anything reading `market-data-tick-defi` (a3, data-status UI) sees a
  false "empty".** → CLEANUP/reconcile (delete phantom grid; point denominator at the dedicated indexes).
- **(C2) data_type name fragmentation (hyphen vs underscore)** — `lending-indices` + `lending_indices`, `dex-pools` +
  `dex_pools`, `dex-swaps` + `dex_swaps` coexist in the **same** bucket. → MIGRATION/normalise to the underscore
  canonical.
- **(C3) `staking_yields` vs `lst_rates` alias** — `market-data-tick-defi` carries `staking_yields`; the dedicated
  bucket carries canonical `lst_rates` (92% captured). Same logical data, two names. → MIGRATION/normalise.
- **(C4) schema spread v4–v8, ZERO v9** — `lst-rates` v6/7/8, `lending-indices` v4/6/7/8, `oracle-prices` v5/6/7/8,
  `dex-pools` v4/5/6, `perp-funding` v5/6/8. `MANIFEST_SCHEMA_VERSION=9` but no v9 rows. **The data exists; it needs
  re-versioning, not re-downloading.** → MIGRATION (single-walk window). This is the recurring "constant ≠ data" issue.
- **(C5) genuinely-partial — `perp_funding` 55% + DeFi-only** — captured for GMX/HYPERLIQUID/ASTER/PACIFICA; **Drift +
  CeFi perps are not in this bucket.** CeFi perp funding rides inside `derivative_ticker` (cefi bucket: BINANCE 68%,
  BYBIT 65%, HYPERLIQUID 60%, OKX-SWAP 35%, DERIBIT 23%, **OKX-FUTURES 0%, ASTER 0%** = 100% attempted_failed). →
  DOWNLOAD/fix-fetch for OKX-FUTURES/ASTER; Drift via the Solana MVP plan (Velocity Data API).
- **(C6) `oracle_prices` 79%** — partial window; verify the 21% empties against `is_before_source_coverage_start()`
  before treating any as download (some are pre-genesis-chain, honest).

## Per-venue / per-chain breakdown (the aggregate hides real gaps)

Operator Q1 ("isn't it per venue/chain?"): yes — and the cut reveals holes the data_type headline buried.

| data_type         | venue cut                                                                                     | chain cut                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `lst_rates`       | ANKR/RP/COINBASE/SWELL/STADER/MAKER 100%; **LIDO 85%, ETHENA 71%, ETHERFI 70%, MARINADE 61%** | ETHEREUM 93%, **SOLANA 70%**                                                                   |
| `lending_indices` | COMPOUND_V3/KAMINO/SOLEND/MARGINFI 100%; **AAVE_V3 84%, SPARK 88%**                           | SOLANA 100%, ARBITRUM/BASE 97%, ETHEREUM 90%, **OPTIMISM 67%**                                 |
| `oracle_prices`   | CHAINLINK 90%; **PYTH 48%**                                                                   | ETHEREUM/POLYGON 100%, ARBITRUM/OPTIMISM 90%, BASE 71%, **SOLANA 0% (1,296 rows, 0 captured)** |
| `perp_funding`    | GMX 100%, HYPERLIQUID 93%; **ASTER 44%, PACIFICA 28%, LIGHTER 0%**                            | BSC 100%, **SOLANA 28%, ZKSYNC 0%, DRIFT absent**                                              |
| `dex_pools`       | 90–100% across venues                                                                         | ARB/ETH 98%, BASE/POLYGON/AVAX 96–97%, OPTIMISM 91%, **BSC 74%**                               |
| `dex_swaps`       | 85–96% across venues                                                                          | ETH/ARB 97%, BASE/POLYGON/AVAX 94–96%, OPTIMISM 81%, **BSC 45%**                               |

## Denominator finding (operator Q2: IS + UAC grounding) — the % is NOT yet IS/UAC-grounded

The `92%/91%/…` above is `captured / manifest-self-enumerated rows` — a **self-referential** denominator. It is NOT
`captured / (IS active instruments ∩ UAC EXPECTED_COVERAGE gated by launch+genesis+source-coverage-start)`.

- UAC `EXPECTED_COVERAGE_BY_ASSET_GROUP` declares **90 defi venue-keys**; the manifest enumerated only `lst_rates`
  **14/22**, `lending_indices` **6/21**, `perp_funding` **5/8** of the expected keys → **manifest under-enumeration**.
- Part of that gap is the `VENUE-CHAIN`-vs-flat naming split (UAC `MARINADE-SOLANA` vs manifest `MARINADE`+chain) —
  reconcile per C2/C3 first. But **genuine absentees remain: `DRIFT-SOLANA` (the Solana-MVP blocker), `FRAX`, `MORPHO`,
  `FLUID`.**
- So "true coverage" is **lower** than the enumerated % once the IS∩UAC denominator is used. The audit must report BOTH
  numbers; I have only the enumerated one so far.

## Data-status tab code alignment (operator: "the dashboard should produce these honest numbers by default")

Read `deployment-api/deployment_api/services/data_status_service.py`. Mixed result:

- ✅ **Good** — `coverage-summary` already reads the **dedicated per-data_type buckets** (`_read_defi_merged_index`
  ~L2931 + `_filter_to_canonical_defi_venues`), so the live tab does **not** hit my phantom-grid trap (it shows real
  numbers, not 0%). And `manifest-status` (`_mtds_expected_dates_cached` ~L1130) uses the **correct expected-dates
  denominator** (clips by chain genesis + venue launch + source-coverage-start).
- 🔴 **Gap A (CRITICAL)** — `coverage-summary` (`_build_coverage_for_cat` ~L3454) uses `len(index)` as **both**
  numerator and denominator (self-referential — the exact mistake I made). Should call the expected-dates oracle like
  `manifest-status` does.
- 🔴 **Gap B (HIGH)** — `is_expected()` scope gate is applied only in the per-row `_classify_datum_scope`, **not** in
  the coverage-summary denominator → out-of-scope cells inflate totals.
- 🔴 **Gap C (HIGH)** — the two endpoints (`coverage-summary` vs `manifest-status`) use **different denominators** →
  contradictory %s for the same (service, asset_group).
- 🟠 **Gap D (MED)** — no **per-chain** breakdown in the display (per-venue-string only; DeFi venues are
  PROTOCOL-CHAIN).
- 🟠 **Gap E (MED)** — `data_status_rollup_worker.py` may bake the wrong denominator offline; verify it shares the
  oracle.

## Three-layer integrity (operator framing: IS→…→features, vs manifest, vs manifest integrity)

The audit must separate three things; here is where each stands:

### L1 — Manifest integrity (are all scattered data_types/schemas recorded correctly + completely IN?)

- **Phantom rows**: `market-data-tick-defi` carries a cartesian `data_type × venue` grid in `VENUE-CHAIN` form, all
  empty — quantified phantom (C1). 🔴
- **Object-vs-row ratio (needs reconciliation)**: `lst-rates` had **34,843 objects** but its index has **16,766 rows**
  (~2:1). Likely the bundling/`_index` factor, but **not yet reconciled per `(venue,chain,day)`** — could hide
  un-recorded objects. 🟠 (item x follow-up)
- **Schema spread v4–v8, no v9** recorded in-manifest (C4); `chain` null while venue embeds chain (C1/C3). 🔴
- **Consolidation reach**: deployment-api reads the dedicated indexes (`_read_defi_merged_index`) ✅, but whether the
  **manifest consolidator + a3** fold every dedicated index into the canonical surface is unconfirmed. 🟠

### L2 — API faithfulness (does the data-status query honestly reflect the manifest?)

- `coverage-summary` denominator self-referential + no `is_expected()` gate + disagrees with `manifest-status` (Gaps
  A–C); reads dedicated buckets ✅. 🔴 — see "Data-status tab code alignment" above.
- **Drilldown** (`/api/data-status/drilldown/...` → `data_status_hierarchical.get_hierarchical_drilldown`) — the most
  useful "where's the missing data" UI surface. Audited 2026-06-01:
  - ✅ reads the **dedicated** per-asset_group buckets (not phantom grid) + filters ghost venues
  - ✅ breaks down **per venue × chain × instrument × data_type × date** (full shard tree, leaf = date)
  - ✅ surfaces `error_reason` + captured/empty_confirmed/attempted_failed per cell (validity partly shown)
  - 🔴 **only 3-state** — no `expected_unattempted`/`MISSING_EXPECTED` bin: counts only manifest-present rows, so a cell
    that SHOULD exist but was never attempted is **invisible in the tree** (operator can't see it as missing).
  - 🔴 **denominator self-referential** — `completion% = captured/(captured+empty+failed)`; no IS∩UAC expected set, no
    chain-genesis/venue-launch clipping. So the drilldown shows _validity per present cell_ but not _what should exist
    but doesn't_. Fixes: canonicalisation plan B2/B3.

### L3 — Pipeline coverage propagated IS → MTDS → MDPS → features (THE new big finding)

**Raw data is 79–96% captured but does NOT reach features-service.** Read the features buckets:

- `features-onchain-defi-prd`: **3 rows total** (2026-04-03 → 2026-04-05), feature_groups `lending_rates` + `lst_yields`
  only. Essentially empty. 🔴
- `features-delta-one-defi-prd`: **no `_index` at all** (FileNotFoundError) → `funding_rate_annualised_bps` /
  `basis_bps` not produced for DeFi. 🔴
- `features-volatility-defi-prd`: **no `_index`** → `realized_vol_*` absent. 🔴

So even with lst*rates 92% / perp_funding 55% / dex 90%+ at the **raw** layer, the **features the strategies consume**
(`staking_apy_bps`, `funding_rate_apy_bps`, `basis_bps`, `realized_vol*\*`) are absent/near-empty. **The strategies
cannot run today — the gap is the MTDS→features propagation, not the raw corpus.** This is the single most important
readiness finding and was invisible until the L3 layer was checked.

## Diagnostic — why the low per-venue numbers (operator questions, 2026-06-01)

Read `capture_status` + `error_reason` + captured-date-range per venue. **The low %s are dominated by THREE non-download
causes, not pending backfills:**

1. **Un-gated denominator** — coverage counted from 2020-01-01 even for venues that launched in 2022/2024. Gate by
   `venue_launch_date` → most jump to ~100%.
2. **Reason mislabeling** — pre-launch/pre-genesis dates recorded as `SOURCE_RETURNED_ZERO` or **blank** instead of
   `EXPECTED_PRE_VENUE_LAUNCH` / `EXPECTED_PRE_GENESIS_CHAIN` (blank reason also violates
   `LegacyBlankErrorReasonError`).
3. **Chain-labeling duplication** — same data enumerated twice (captured under blank chain + phantom-empty under the
   real chain).

| Venue / cell                | Raw %    | Real diagnosis                                                                                                                                                                    | Action                                                                                    |
| --------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **DRIFT** perp_funding      | absent   | NOT a new data_type — same `perp_funding`, DRIFT venue/SOLANA chain, never enumerated                                                                                             | **Already covered** by `solana_basis_trading_mvp` Phase 1 (Velocity API backfill) ✅      |
| **LIGHTER** perp_funding    | 0%       | 599 rows ALL `SOURCE_RETURNED_ZERO` across full post-launch life (2024-09→2026-05) — genuine zero from the source                                                                 | **Real fix**: Lighter funding adapter/endpoint returns nothing — verify endpoint (zkSync) |
| **PACIFICA** perp_funding   | 28%      | captured 2025-12→now (~100% of real life); pre-Dec-2025 = `SOURCE_RETURNED_ZERO` (pre-launch, young venue)                                                                        | reason-relabel `EXPECTED_PRE_VENUE_LAUNCH`; no backfill                                   |
| **ASTER** perp_funding      | 44%      | captured since 2024-09 (~100% of real life); pre-launch rows carry **blank reason**                                                                                               | fix blank reason → `EXPECTED_PRE_VENUE_LAUNCH`; no backfill                               |
| **LIDO** lst_rates          | 85%      | captured 2020-12→now (~100%); 353 pre-Dec-2020 = pre-launch `SOURCE_RETURNED_ZERO`                                                                                                | denominator-gate + relabel; no backfill                                                   |
| **ETHERFI** lst_rates       | 70%      | captured 2024-01→now (~100%); pre-2024 = didn't exist                                                                                                                             | denominator-gate + relabel; no backfill                                                   |
| **MARINADE** lst_rates      | 61%      | captured 2022-01→now; pre-genesis block mislabeled                                                                                                                                | denominator-gate + relabel; no backfill                                                   |
| **PYTH** oracle (SOLANA 0%) | 48% / 0% | **double-enumerated**: real data captured under chain=`''` (1,185 rows), phantom-empty under chain=`SOLANA` (1,296: 962 `SOURCE_RETURNED_ZERO` + 334 `EXPECTED_KNOWN_SOURCE_GAP`) | reconcile chain label (`''`→`SOLANA`); the captured data already exists                   |
| **CHAINLINK** oracle        | 90%      | 6,507 captured; 728 empty (453 **blank reason** + 275 `SOURCE_RETURNED_ZERO` pre-genesis) + 1 `attempted_failed` (RPC "Block with id")                                            | fix blank reasons + 1 RPC retry; rest honest pre-genesis                                  |

**So to get to 100%**: it's mostly (a) **gate the denominator by venue-launch/chain-genesis** (item p), (b) **relabel
pre-launch reasons** (fixes the blank-reason `LegacyBlankErrorReasonError` violations too), (c) **reconcile the Pyth
blank-vs-SOLANA chain duplication**. The only genuine data work is **LIGHTER** (adapter returns zero post-launch) +
**DRIFT** (already in the Solana plan) + a handful of `attempted_failed` RPC retries.

**Why it took many passes** (operator Q): both causes, and the difficulty IS the finding — (1) **data not in canonical
placing** (scattered dedicated buckets w/ inconsistent env-suffixes, hyphen/underscore + VENUE-CHAIN + blank-chain
dupes, and a phantom grid in `market-data-tick-defi` that actively returns "empty" to the first reader); (2) **manifest
fragmentation** (per-data_type indexes, no single canonical surface; schema spread v4–v8; mislabeled reasons). The
hard-to-find-ness is itself the L1/L2 bug to fix.

## Solana MVP integration (`solana_basis_trading_mvp_2026_06_01.md`)

The concrete first-live target is the **Solana basis trade** (long SOL on Orca/Raydium + short SOL-PERP on Drift V2).
Coverage cells that actually gate go-live (audit these specifically):

| MVP cell                                                | Source of truth                                                             | Current state                                               | Action                                         |
| ------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------- |
| Drift `perp_funding` SOL-PERP                           | `data.api.drift.trade` Velocity API (free, full history) + `perp-funding-*` | bucket has GMX/HL/ASTER/PACIFICA, **Drift not yet present** | backfill Drift via Velocity API (plan Phase 1) |
| `perp_trades` SOL-PERP (NEW type)                       | Velocity API CSV                                                            | not yet a data_type                                         | declare + ingest (plan)                        |
| Orca/Raydium `dex_pool_state` SOLANA (NEW, time-series) | Alchemy archive RPC                                                         | `dex_pools` has snapshots, not time-series                  | extend `solana_defi_handler.py` (plan)         |
| `oracle_prices` SOLANA (Pyth)                           | Pyth on-chain                                                               | oracle-prices bucket has PYTH (1,185 captured)              | verify Solana/SOL window                       |

> The Bug-D Helius signature-walking infra (28GB, 6293 parts) is **out of MVP scope** per the plan — do not let it
> reappear as a "missing data" finding.

## Per-item verdict (o–w) — corrected

| Item                                   | Verdict         | Evidence                                                                                                                                    |
| -------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| (o) IS universe present                | 🟠 NOT VERIFIED | dedicated buckets enumerate real venues (LIDO/AAVE_V3/CHAINLINK/GMX…); IS↔manifest reconciliation still owed.                              |
| (p) Expected-coverage dump             | 🟠 STALE        | a2 dump 12 days old, END_DATE hardcoded 2026-05-20 — re-run to today.                                                                       |
| (q) Divergence = 0 (all buckets)       | 🟠 AMBER        | Across dedicated buckets, 79–96% captured. Phantom grid (C1) inflates `market-data-tick-defi` divergence falsely.                           |
| (r) v9 per-data_type from data         | 🔴 RED          | v4–v8 spread, 0% v9 (C4) — migration of existing data.                                                                                      |
| (s) SSOT names in rows                 | 🔴 RED          | hyphen/underscore dupes (C2), `staking_yields` alias (C3), `VENUE-CHAIN` strings (C1).                                                      |
| (t) Required-history window            | 🟠 AMBER        | lst_rates/lending/dex have multi-year history; oracle 79% + perp_funding 55% partial; verify interior gaps.                                 |
| (u) features emit over window          | 🟠 NOT VERIFIED | features-onchain-defi-\* bucket exists; per-feature backfill not yet checked.                                                               |
| (v) Honest totality breakdown          | 🟠 PARTIAL      | per data_type × venue/chain produced (above); but on **enumerated** denominator only — true-coverage (IS∩UAC) owed.                         |
| (w) Data-status code honest by default | 🔴 RED          | coverage-summary denom self-referential + no `is_expected()` gate + endpoints disagree + no per-chain (Gaps A–E); dedicated-bucket read ✅. |

## Backlog (classified — mostly cleanup, not download)

- [ ] [CLEANUP] P0. Reconcile/delete the `market-data-tick-defi` phantom empty grid (cartesian data_type×venue,
      VENUE-CHAIN format) vs the captured rows in the dedicated buckets; point the data-status denominator at the real
      indexes. parent_epic: defi_master (C1)
- [ ] [MIGRATION] P1. Normalise data_type aliases in-bucket: `lending-indices`→`lending_indices`,
      `dex-pools`→`dex_pools`, `dex-swaps`→`dex_swaps`, `staking_yields`→`lst_rates` (data exists; rename rows, no
      re-download). parent_epic: defi_master (C2/C3)
- [ ] [MIGRATION] P1. v4–v8 → v9 re-version of dedicated DeFi buckets
      (lst-rates/lending-indices/oracle-prices/perp-funding/dex-pools/dex-swaps), bundled into the single-walk window.
      parent_epic: manifest_master (C4)
- [ ] [DATA] P0. Fix CeFi perp `derivative_ticker` fetch failures — OKX-FUTURES + ASTER 100% attempted_failed; refresh
      to current date (data stale ~3–5 weeks). parent_epic: cefi_master (C5)
- [ ] [DATA] P0. Backfill Drift V2 SOL-PERP `perp_funding` + `perp_trades` via Velocity Data API (Solana MVP critical
      path). parent_epic: mtds_mdps_master → solana_basis_trading_mvp_2026_06_01.md (C5/Solana)
- [ ] [DATA] P1. Extend `solana_defi_handler.py` for Orca/Raydium `dex_pool_state` time-series (Solana MVP).
      parent_epic: mtds_mdps_master (Solana)
- [ ] [DATA] P0. Backfill the UAC-expected venues the manifest never enumerated (true-coverage gap, after naming
      reconciliation): `DRIFT-SOLANA` (Solana MVP — already planned), `FRAX` (lst), `MORPHO` + `FLUID` (lending).
      parent_epic: defi_master (Q2)
- [ ] [DATA] P1. **LIGHTER** perp_funding returns `SOURCE_RETURNED_ZERO` across its whole post-launch life (2024-09→now)
      — verify the Lighter (zkSync) funding endpoint/adapter; real source/adapter fix, not pre-launch. parent_epic:
      defi_master
- [x] ✅ [CODE] **Writer fix shipped** — `oracle_prices_handler.py` + `evm_defi_handler.py` now classify pre-genesis
      empties via UAC `get_chain_genesis_date()` (→ `EXPECTED_PRE_GENESIS_CHAIN`) instead of blanket
      `SOURCE_RETURNED_ZERO`. market-tick-data-service@840d85f1 (ruff clean, parse OK, UAC import resolves). Future
      writes correct.
- [ ] [MIGRATION] P1. **Legacy reason relabeling** (writer now fixed @840d85f1; this is the back-data migration) —
      pre-launch/pre-genesis rows recorded as `SOURCE_RETURNED_ZERO` or **blank** (LIDO/ETHERFI/MARINADE/PACIFICA/ASTER
      pre-launch; CHAINLINK 453 blank + BASE 2022-11→2023-08) → `EXPECTED_PRE_VENUE_LAUNCH` /
      `EXPECTED_PRE_GENESIS_CHAIN`; clears `LegacyBlankErrorReasonError` violations + lifts venue %s without backfill.
      parent_epic: defi_master
- [ ] [CLEANUP] P1. **Pyth chain-label duplication** — oracle_prices Pyth captured under chain=`''` (1,185) but
      phantom-empty under chain=`SOLANA` (1,296). Objects are correctly stored at `venue=PYTH/chain=SOLANA` — only the
      INDEX is wrong; legacy captured rows recorded chain=`''`. Reconcile (`''`→`SOLANA`) + drop the duplicate empties
      on shared dates; fixes "Solana oracle 0%" without backfill. parent_epic: defi_master
- [ ] [DATA] P2. **Pyth ~5-week recent backfill** — captured stops 2026-04-14, today 06-01 → real Pyth coverage ≈82%
      (1,185/1,447 after dedup), not 100%. Run a VM backfill of Pyth oracle 2026-04-15→present (Hermes API; small).
      parent_epic: defi_master
- [ ] [CODE] P0. Fix `data_status_service._build_coverage_for_cat` (`/api/coverage-summary`) denominator: replace
      `len(index)` self-reference with the expected-dates oracle (`_mtds_expected_dates_cached`) + apply `is_expected()`
      scope gate, so the tab matches `manifest-status` and the audit. parent_epic: deployment_and_user_management_master
      (Gap A/B/C)
- [ ] [CODE] P1. Add per-chain breakdown to the data-status coverage view (DeFi PROTOCOL-CHAIN split). parent_epic:
      deployment_and_user_management_master (Gap D)
- [ ] [CODE] P1. Verify `data_status_rollup_worker.py` uses the expected-dates denominator (not manifest row count) so
      the offline rollup is honest. parent_epic: observability_master (Gap E)
- [ ] [AUDIT] P1. Re-compute coverage with the IS∩UAC denominator (true-coverage), per venue × chain, reporting BOTH
      enumerated-coverage and true-coverage (the committed numbers are enumerated-only). parent_epic: defi_master (Q2/v)
- [ ] [SCRIPT] P2. Re-run the coverage query against the dedicated buckets (done — query now reads them); rename
      a4_manifest_v8→v9; make a2/a3 END_DATE dynamic-today. parent_epic: manifest_master

## Transparency (where this sampled vs walked)

- **Walked**: dedicated-bucket `_index/availability_index.parquet` for lst-rates/lending-indices/oracle-prices/
  perp-funding/dex-pools/dex-swaps (full) + market-data-tick-{defi,cefi,tradfi} (full) + GCS object counts per bucket.
- **Not yet covered**: Drift Velocity API actual probe (per the Solana plan, verified there); features-onchain-defi
  per-feature window (item u); per-instrument axis; AWS fleet; non-prd buckets. These are the follow-ups.
- **Methodology fix landed**: instructions Step 1.5 now forces enumerating all candidate buckets + alias/wrong-form
  search before any "missing" verdict — so this 0%-false-alarm cannot recur.

**Archive condition**: archives when all backlog items above are `- [x]` in their parent plans.
