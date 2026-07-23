---
doc_type: issue
title:
  "DeFi bare SUSHISWAP/UNISWAP manifest venues (199,397 rows) — factory-address resolver built + wired, but NO row
  captured today carries a factory address, so resolution is 100% residual pending upstream capture + a UAC registry gap
  for SushiSwap-on-Arbitrum"
summary: >-
  Operator ruling (defi_consolidated_closeout_2026_07_18.md § "Operator decisions applied (2026-07-21..."): derive the
  bare SUSHISWAP/UNISWAP manifest venue's version from the pool's deploying factory contract address, not "undecidable".
  Built + wired a static, cited factory-address→version map + resolver (instruments-service `_dex_factory_registry.py`)
  into the manifest venue-canonicalization script (`canonicalize_defi_manifest_venue_2026_06_14.py`). Pre-check
  (mandatory before adding a new field) found NO factory/creator/deployer address column anywhere in the
  currently-captured data path — not in `InstrumentRecord`, not in the v9 availability-manifest schema, not in any of
  the 4 subgraph query cascades the shared `UniswapV3ReferenceDataAdapter` uses to capture SushiSwap/Uniswap-fork pools.
  So the resolver is correctly-built forward-looking infrastructure that resolves ZERO of today's 199,397 rows (100%
  residual) — not a guess, a precisely-documented gap. A SECOND, independent blocker was found for the single largest
  bare-venue cohort (SushiSwap-on-Arbitrum): UAC's `ALL_DEFI_VENUES` has NO registered versioned venue for it at all
  (neither `SUSHISWAP_V2-ARBITRUM` nor `SUSHISWAP_V3-ARBITRUM` exists — only the bare `SUSHISWAP-ARBITRUM`), so even a
  perfectly-resolved factory address on that chain cannot be safely written back without a UAC registry addition first
  (cross-repo prerequisite, out of instruments-service's scope).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [data-correctness, defi, venue-canonicalization, factory-address, sushiswap, uniswap, dex-pool, residual]
related: [defi_consolidated_closeout_2026_07_18, canonical_closeout_open_questions_2026_07_18]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: "defi_consolidated_closeout_2026_07_18.md Track 1 [DECISION] P2 item + Operator decisions applied (2026-07-21)"
resolved_by:
  "instruments-service@3ffd1adf (2026-07-21): _dex_factory_registry.py + wiring into
  canonicalize_defi_manifest_venue_2026_06_14.py, shipped + tested (35/35 new tests green). Infra-complete; the
  199,397/206,107-row residual itself is NOT reduced (0 resolved today, by honest design) — this doc stays informative
  re: the follow-up capture work + UAC registry gap, not a claim the data problem is solved."
---

# DeFi bare SUSHISWAP/UNISWAP version — factory-resolver built, 100% residual today (no factory data captured anywhere)

## What shipped (instruments-service@3ffd1adf)

1. **New module** `instruments_service/reference_data/adapters/defi/_dex_factory_registry.py` — a static, cited
   factory-contract-address → protocol-version map (Uniswap V2/V3/V4, SushiSwap V2/V3) covering every chain this
   workspace actually captures Uniswap/SushiSwap data on (ETHEREUM, ARBITRUM, OPTIMISM, POLYGON, BASE, AVALANCHE —
   verified against UAC `chain_env.PROTOCOL_LAUNCH_DATES` + `registry/defi_venues.ALL_DEFI_VENUES`). Uniswap V3's
   addresses are re-exported from the already-audited UAC SSOT
   (`unified_api_contracts.registry.dex_router_addresses.UNISWAP_V3_FACTORY_BY_CHAIN`, audited 2026-06-12); every other
   address was verified live (WebSearch + a direct WebFetch to the chain's block explorer, cross-checked against
   DefiLlama's maintained `dimension-adapters` fee/volume registry) before being hardcoded — see the module docstring
   for the full per-address citation trail.
2. **Wired** into `scripts/canonicalize_defi_manifest_venue_2026_06_14.py`'s `_canonical_venue()` /
   `canonicalise_venue_column()`: if a row carries a `factory_address` column, the resolver is tried FIRST and the
   constructed `{version}-{chain}` string is used ONLY if it is already a registered `ALL_DEFI_VENUES` member — never
   mints an unregistered venue. Zero-regression: absent the column (every row today), behavior is byte-for-byte
   identical to before this change (proven by
   `tests/unit/scripts/test_canonicalize_defi_manifest_venue_factory_resolution.py::test_no_factory_column_unchanged_output`).
3. **Regression tests** for the resolver itself (`tests/unit/reference_data/adapters/defi/test_dex_factory_registry.py`)
   including the real cross-chain address-collision case this research surfaced (see below).

## Why it resolves 0 of the 199,397 rows today (verified, not assumed)

Pre-check performed (per the dispatch's explicit instruction to check before assuming a new field is needed): grepped
instruments-service + market-tick-data-service for any existing factory/creator/deployer address column, then read every
consumer on the capture path.

| Layer                                                                                                                                                                                                                                                                    | Checked                    | Finding                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `InstrumentRecord` (`unified_api_contracts.internal.reference.instrument`)                                                                                                                                                                                               | full field list            | no factory-address field                                                                                                                                                                                              |
| Availability-manifest schema (v9, `/codex/02-data/availability-manifest-and-data-status.md`)                                                                                                                                                                             | full column list           | no factory-address column; DEX pools carry `pool_address` row-level INSIDE the raw MTDS parquet for the "DEX V3 + CLMM" cluster-shard family only, never in the manifest itself, and never a factory address anywhere |
| The 4 subgraph query cascades `UniswapV3ReferenceDataAdapter` uses to capture SushiSwap/Uniswap-fork pools (`instruments_service/reference_data/adapters/defi/uniswap_v3.py`: native `pools` query, Algebra-fork fallback, SushiSwap `pairs` fallback, Messari fallback) | full GraphQL query text    | none requests a `factory` field                                                                                                                                                                                       |
| MTDS `uniswapv2_adapter.py`                                                                                                                                                                                                                                              | `FACTORY_ADDRESS` constant | exists but is a compile-time Python constant, never written onto the captured row                                                                                                                                     |

Given this, the resolver is genuinely forward-looking: it will fire automatically the day ANY of the following lands
(neither is in this fix's scope — both are real follow-up options, not decided between here):

- **Option A — subgraph query augmentation**: add a `factory { id }` (or equivalent) selection to the query templates.
  NOT done in this fix because the exact field name/availability differs across the 4 subgraph schema families (native
  Uniswap-V3-shape, Algebra fork, SushiSwap custom `pairs`, Messari) and could not be safely verified live against each
  specific deployed subgraph without risking a schema-error regression on a currently-working capture path (a wrong
  field name causes a hard GraphQL error → cascade misfire → false `attempted_failed`). Needs a live-schema probe per
  fork before landing.
- **Option B — on-chain RPC lookup**: call the standard `factory()` view function every Uniswap V2/V3 pool and SushiSwap
  V2/V3 pool contract exposes, keyed off the ALREADY-captured `pool_address`. Works without touching the live subgraph
  queries at all, but needs an RPC provider (Infura was removed from this workspace 2026-07-19 era; Alchemy is already
  used elsewhere for gas-fee oracles) + enumerating the unique `pool_address` set from the raw MTDS parquet (not the
  manifest, which lacks per-pool granularity) + a backfill run.

## Second, independent blocker: SushiSwap-on-Arbitrum has no registered versioned venue at all (UAC gap)

`SUSHISWAP-ARBITRUM` (bare) is the ONLY SushiSwap-Arbitrum entry anywhere in UAC `ALL_DEFI_VENUES` — confirmed via
direct grep of `unified_api_contracts/registry/defi_venues.py` (2026-07-21). Neither `SUSHISWAP_V2-ARBITRUM` nor
`SUSHISWAP_V3-ARBITRUM` is registered. This means: even once Option A or B above lands and a factory address IS resolved
for an Arbitrum Sushi pool, the wired resolver's own safety guard (never emit a venue string that isn't an
`ALL_DEFI_VENUES` member) will STILL fall through to the bare form for that chain specifically, until UAC adds the
missing registry entries. This is a genuine, precise, cross-repo (UAC) prerequisite — not a guess, not a workaround
needed in instruments-service.

Live research this session (WebSearch + WebFetch, cross-checked against DefiLlama's `dimension-adapters` registry)
independently confirmed the SushiSwap V2 (classic) and V3 factory addresses on Arbitrum ARE cleanly resolvable
(`0xc35DADB65012eC5796536bD9864eD8773aBc74C4` / `0x1af415a1EbA07a4986a52B6f2e7dE7003D82231e` respectively) — the address
data is not the blocker for Arbitrum, the missing UAC registry slot is. Also surfaced as a side-finding: the address
`0xc35DADB65012eC5796536bD9864eD8773aBc74C4` is SushiSwap V2 Classic Factory on ARBITRUM/POLYGON/BSC/AVALANCHE but
SushiSwap V3 Factory on BASE — the SAME bytecode address denotes a DIFFERENT protocol version depending on chain (a real
deployment collision, not a data error). The registry keys strictly by `(chain, address)`, never address alone,
specifically because of this.

## Measured resolved vs. residual (this session)

Live read-only inspection of the prod DeFi manifest
(`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, 52,291,377 total rows),
2026-07-21:

| Bare venue                       | Rows        |
| -------------------------------- | ----------- |
| `SUSHISWAP` + chain=`ARBITRUM`   | 192,560     |
| `UNISWAP` + chain=`ETHEREUM`     | 13,420      |
| `SUSHISWAP` (no chain at all)    | 127         |
| **Total bare SUSHISWAP/UNISWAP** | **206,107** |

(The Track-1 todo's original audited figure was 199,397 — the ~6,710-row delta is ongoing forward capture between the
original audit and this measurement, not a discrepancy in method; both counts describe the SAME bare-venue defect.)

- **Resolved by the new factory-address resolver: 0 rows (0.0%).**
- **Residual: 206,107 rows (100%).**
- **Why, precisely** — confirmed by walking the ENTIRE 41-column manifest schema for this pull: zero columns match
  `factory|deployer|creator` (regex-checked programmatically, not eyeballed). There is no data for the resolver to
  resolve against; this is not a resolver defect, it's the pre-check finding above made concrete against the real
  corpus.
- **Capture-status composition of the residual** (for context — not something this fix changes): `captured` 143,673 ·
  `empty_confirmed` 51,973 · `attempted_failed` 6,433 · `expected_unattempted` 4,028.
- **instrument_type composition**: `pool` 160,990 (the DEX-pool rows the operator ruling is about) · `""` (blank) 37,644
  (non-pool data_types — `lending_indices`, `oracle_prices`, `governance_events`, etc. — riding the same bare venue
  string but out of this fix's POOL-version scope; each such data_type has exactly 1,948 rows, consistent with a per-day
  expected-shard seed rather than pool-level captures).

## Follow-up (tracked)

- Added a new `[DATA]` todo under `defi_consolidated_closeout_2026_07_18.md` Track 1 for: (1) deciding + landing Option
  A or B above to actually start capturing factory addresses, and (2) the UAC `ALL_DEFI_VENUES` registration gap for
  SushiSwap-on-Arbitrum (and an audit for any other bare-venue chain with the same gap).
- This doc stays `status: open` (not `resolved`) — the CODE-level infra (map + resolver + wiring + tests) is done and
  shipped, but the actual 199,397-row residual is NOT reduced by this fix (0 rows resolve today, by honest design) —
  closing this doc as resolved would misrepresent that as "fixed."
