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
author: unknown
last_updated: "2026-08-02"
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
context_scope:
  [
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    instruments-service/instruments_service/reference_data/adapters/defi/_dex_factory_registry.py,
    instruments-service/scripts/canonicalize_defi_manifest_venue_2026_06_14.py,
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
  ]
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

- A `[DATA]` todo tracks: (1) deciding + landing Option A or B above to actually start capturing factory addresses, and
  (2) the UAC `ALL_DEFI_VENUES` registration gap for SushiSwap-on-Arbitrum (and an audit for any other bare-venue chain
  with the same gap). **Two live locations, one execution site** (pointer corrected 2026-08-02 — this bullet previously
  named only `defi_consolidated_closeout_2026_07_18.md` Track 1, which went stale when Track 1 was forked out on
  2026-07-24 and the todo moved with it; a `grep -i factory` against the closeout returned zero hits):
  - **Executable todo** (the one to work): the `[DATA] P2` "NEW 2026-07-21 — actually start capturing factory addresses"
    entry in
    [`/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md),
    the forked Track-1 child.
  - **Roll-up view**: the matching Track-1 entry re-added to
    [`/plans/active/defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md)
    on 2026-08-02, so the AG-level close-out surfaces the residual instead of silently dropping it. Close all three
    (this doc's todo + both plan entries) together.
- This doc stays `status: open` (not `resolved`) — the CODE-level infra (map + resolver + wiring + tests) is done and
  shipped, but the actual 199,397-row residual is NOT reduced by this fix (0 rows resolve today, by honest design) —
  closing this doc as resolved would misrepresent that as "fixed."

## Todos

- [x] ✅ [DECISION] P2. **RULED 2026-08-08 (operator, recorded in
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, `unified-trading-pm@a55b820b76`): Option (b) — on-chain
      RPC `factory()` lookup**, not Option A's live-schema-probe subgraph augmentation. Operator also extended scope
      beyond forward-only capture: the 206,107-row historical residual must be migrated (GCS objects + manifest rows
      rewritten to the resolved canonical venue+chain, legacy bare forms purged once canonical twins are verified) — not
      just a go-forward labeling fix. This closes the "Option A-vs-B design fork is still unruled" premise this doc's
      prior KEEP-NA verdicts (through 2026-08-07) relied on.
- [ ] [SCRIPT] P1. **Execute the remaining half of the 2026-08-08 ruling** — the RPC `factory()` resolver + UAC venue
      registration half shipped 2026-08-09 (see Progress Log below); migrate + purge the historical objects/manifest to
      canonical venue+chain naming, and resolve the UNISWAP-ETHEREUM cohort, still remain. **Execution tracked at
      `/plans/active/defi_satellite_ao_dispatch_batch11_2026_08_09.md`'s follow-up `[SCRIPT] P1` todo
      (`assigned_vm: planning`, active — split 2026-08-09 from the now-closed resolver todo; the intermediate hop at
      `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s own `[SCRIPT] P1` todo was itself further
      extracted there the same day) — work the fix at batch11, not a second copy here; close all three together once it
      ships.**

## Progress Log

- 2026-08-09 (slot 16, data_engineering worker): Closed batch11's resolver todo (RPC `factory()` resolver + resolution
  script shipped `instruments-service@fa54f1d8`; UAC `SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM` venues registered,
  closing the UAC gap section above, `unified-api-contracts@ed6b4c78`). Live run against SUSHISWAP-ARBITRUM:
  12,910/12,910 pool addresses resolved, 100% V2 (classic) factory — first non-zero resolution against this doc's
  "resolved=0 rows (0.0%)" measured baseline. UNISWAP-ETHEREUM cohort not yet run; the GCS-object/manifest migrate+purge
  half of the 2026-08-08 ruling is unstarted — split into batch11's new follow-up todo (VM-scale full-corpus I/O, out of
  interactive-session scope), which THIS doc's todo above now points at. This doc's own todo stays `[ ]` — the ruling
  isn't fully executed yet, full detail in batch11's Progress Log.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - Option A (subgraph augmentation) vs Option B (on-chain RPC) is
  an explicitly undecided design fork; A needs a live-schema probe per fork before landing
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- 2026-08-02 (worker, slot-3): Verified this doc's "Follow-up (tracked)" claim against the corpus — the claimed Track-1
  todo in `defi_consolidated_closeout_2026_07_18.md` was genuinely absent (`grep -i factory` → 0 hits), but the work was
  never lost: it had migrated into the forked Track-1 child `defi_track01_per_instrument_and_canon_id_2026_07_24.md`
  during the 2026-07-24 line-cap fork, where it is still open and carries both halves (Option A/B capture + the UAC
  SushiSwap-Arbitrum registration). Re-added the roll-up entry to the close-out's Track 1 per operator ruling and
  corrected the pointer above to name both locations. No change to the measured figures (206,107 residual, resolved=0)
  and no change to this doc's `status: open` / KEEP-NA classification — the Option A-vs-B design fork is still unruled.
- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): KEEP-NA valid (2026-07-30 verdict re-
  affirmed after the 2026-08-02 pointer correction) — re-read end to end, 1 open item. The 2026-08-02 edit was a pointer
  fix only (naming both the executable Track-1 child and the re-added roll-up view) and its own note states there is "no
  change to this doc's `status: open` / KEEP-NA classification — the Option A-vs-B design fork is still unruled".
  Confirmed: Option A (subgraph query augmentation, needs a live-schema probe per fork or a wrong field name hard-errors
  the query) vs Option B (on-chain RPC `factory()` lookup, needs an RPC provider + pool_address enumeration) remains an
  undecided design call, plus a cross-repo UAC `ALL_DEFI_VENUES` registration prerequisite.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped the archived
  `canonical_closeout_open_questions_2026_07_18.md` for
  `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`, the doc's own 2026-08-02 correction naming it
  as the actual executable-todo location.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdicts re-affirmed) —
  the single open todo still requires an undecided design choice (Option A subgraph augmentation vs Option B on-chain
  RPC lookup) plus a cross-repo UAC registry addition. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — doc's own redirect banner still names
  defi_track01_per_instrument_and_canon_id_2026_07_24 as the doc to work; close all three together, not from here alone.
- **stale-check-defi-tranche 2026-08-09**: the "Option A-vs-B design fork is still unruled" premise every KEEP-NA
  verdict above relied on (2026-07-30 through 2026-08-07) went stale ONE DAY after the last of them: the operator ruled
  2026-08-08 (option b, on-chain RPC lookup, plus an extended scope covering the historical 206,107-row migration+purge)
  — recorded in `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, `unified-trading-pm@a55b820b76` (confirmed
  ancestor of `origin/live-defi-rollout`). Flipped the `[DECISION]` todo `[x]` by citation and rewrote the execution
  todo to point at the now-ruled scope. The doc stays `assigned_vm: NA` and `status: open` — the actual RPC-lookup +
  UAC-registration + historical-migration EXECUTION has not shipped anywhere in the corpus yet (checked: no matching
  commits in instruments-service/market-tick-data-service/unified-api-contracts since 2026-08-08), so this is a citation
  fix, not a completion claim.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA-STALE (already-duplicated), not reclassified — the sole
  open item's execution moved one more hop since the "stale-check-defi-tranche 2026-08-09" entry above: the intermediate
  `defi_track01...md` copy was itself extracted 2026-08-09 into `defi_satellite_ao_dispatch_batch11_2026_08_09.md`
  (`[SCRIPT] P1`, active). Updated the todo's pointer to cite batch11 directly as the live dispatch path. Doc stays
  `assigned_vm: NA`.
