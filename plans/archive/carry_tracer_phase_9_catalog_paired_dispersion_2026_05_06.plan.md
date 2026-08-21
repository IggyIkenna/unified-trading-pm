---
doc_type: plan
title: carry-tracer-phase-9-catalog-paired-dispersion-2026-05-06
summary:
status: complete
nature: record
asset_group: defi
stage: [meta]
repos: [deployment-service, instruments-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-06
overview: Catalog spec additions + paired_price_dispersion calculator + UAC LST_TOKEN_TO_PROTOCOL_ASSET SSOT — closes the Layer 1 follow-ups behind the Layer 2 tracer adapter shipped 2026-05-06.
type: code
owner: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-06
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: B3}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: features-onchain-service, code: C0, deployment: none, business: none}
- {repo: features-cross-instrument-service, code: C0, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
depends_on: [carry-tracer-pipeline-handoff-2026-05-06]
todos: []
isProject: false
---

# Phase 9 — Catalog spec additions + `paired_price_dispersion` + UAC SSOT

> Closes the Layer 1 follow-ups left over from `carry_tracer_pipeline_handoff_2026_05_06.md`. The Layer 2 tracer adapter
> (`strategy-service@6e73475`) wired the schema-drift bridges and proved YIELD_STAKING_SIMPLE produces real ranked APYs
> through the allocator (sUSDe @ 352bps → weight 0.579 over 2026-04-03..04-09). This plan removes the temporary adapter
> shim by emitting the canonical columns at the calculator level, adds the missing `CARRY_BASIS_DATED` /
> `ARBITRAGE_PRICE_DISPERSION` greenfield calculator, and lands the catalog spec rows the user requested in the
> 2026-05-06 session.

## Progress 2026-05-07

Phase 1 + Phase 3 shipped. Phase 2 calculator + Phase 3.E shim deletion + Phase 4 verification deferred — see handoff
section at the end.

| Phase                                                              | Status                                              | Commits                            |
| ------------------------------------------------------------------ | --------------------------------------------------- | ---------------------------------- |
| 1.A — UAC `LST_TOKEN_TO_PROTOCOL_ASSET` SSOT                       | ✅ shipped                                          | `unified-api-contracts@3613e90`    |
| 1.B — features-onchain emit canonical columns + `supply_apy` alias | ✅ shipped                                          | `features-onchain-service@7f1b2a1` |
| 2 — `paired_price_dispersion` calculator                           | ⏸ deferred (handoff)                               | none                               |
| 3.A-D — strategy-service catalog spec additions                    | ✅ shipped                                          | `strategy-service@e4a0cdd`         |
| 3.E — tracer adapter shim deletion                                 | ⏸ deferred (depends on Phase 1.B re-run + Phase 2) | none                               |
| 4 — partial Stage 3 + Stage 4 verification                         | ⏸ deferred (depends on Phase 1.B re-run + Phase 2) | none                               |

`CARRY_BASIS_DATED` 7 → 16 specs (added 2 NASDAQ-CME ETF-vs-future, 2 intra-Deribit, 5 ETF placeholders marked
`databento_pending`). `ARBITRAGE_PRICE_DISPERSION` 15 → 17 specs (added 2 CME-DERIBIT cross-venue futures arbs).

## Context

After the Layer 2 fix the carry tracer runs end-to-end across 6 of 7 archetypes:

- ✅ `YIELD_STAKING_SIMPLE` — 4 LST slots produce real APY through the allocator.
- 🟡 `YIELD_ROTATION_LENDING` / `ARBITRAGE_PRICE_DISPERSION` (lending arb) — resolver finds data; harness state-machine
  entry-trigger logic deferred (engine-level concern, separate plan).
- 🟡 `CARRY_BASIS_PERP` / `CARRY_STAKED_BASIS` / `ARBITRAGE_PRICE_DISPERSION` (perp dispersion) — blocked by
  features-delta-one MDPS-loader path drift, fixed `features-delta-one-service@cc339e0` 2026-05-06; will produce values
  on next funding_oi backfill run.
- ❌ `CARRY_BASIS_DATED` — feature group `dated_basis_apy` has no calculator. Needs greenfield.

User direction (2026-05-06 session, captured in handoff doc):

> "For the carry basis dated, don't remove the ones you have. Just add those ones that we've mentioned. and refactor the
> future to future cross venue stuff out of carry basis arb into price arb archetype that exists. and for the futures,
> for the commodities and things like that, you would need to do basically the ETF versus the futures for the basis to
> make sense there."

## Layer breakdown

### Layer 1.A — UAC SSOT (`unified-api-contracts`)

Lift the tracer's `_TOKEN_TO_PROTOCOL_ASSET` lookup table into UAC so every consumer (features-onchain calculators,
data-status, downstream allocators, instruments-service) speaks the same `(token → (protocol, asset))` mapping.

- File: `unified_api_contracts/internal/domain/defi/lst.py` (new module).
- Symbol: `LST_TOKEN_TO_PROTOCOL_ASSET: dict[str, tuple[str, str]]` (16 tokens — stETH/wstETH/rETH/cbETH/weETH/ankrETH/
  mETH/swETH/ETHx/osETH/pufETH/sUSDe/sDAI/jitoSOL/mSOL/bSOL).
- Helpers: `tokens_for_protocol_asset(protocol, asset) -> set[str]`,
  `protocol_asset_for_token(token) -> tuple[str, str] | None`.
- Schema-drift sentinel: when adding a new LST in instruments-service, the same PR must add the row to this table —
  enforced via QG STEP that asserts every active LST instrument resolves via the helper.

### Layer 1.B — features-onchain-service calculator emit canonical columns

Currently `lst_yields` emits a single `token` column; the tracer translates via the lookup. Layer 1 emits explicit
`protocol` / `asset` columns alongside `token` so downstream readers (tracer, deployment-status, ML feature joins) don't
need the lookup. Same shape for `lending_rates` — emit `protocol` / `chain` / `asset` columns parsed from the canonical
`instrument_id` (`{PROTOCOL}-{CHAIN}:LENDING:{ASSET}` regex), keep `instrument_id` as the canonical key.

- File: `features_onchain_service/engine/orchestrator.py`, methods `_compute_lst_features_for_day` +
  `_calculate_lending_features`.
- Rename `aave_supply_apy` → `supply_apy` workspace-wide (or emit BOTH for one transition cycle). The Layer 2 tracer has
  a `aave_supply_apy → supply_apy → lending_apy` fallback chain so the rename is non-breaking from the read side.
- After rebuild + 30-day rerun: tracer's `_TOKEN_TO_PROTOCOL_ASSET` adapter becomes a Layer 2 safety net rather than
  load-bearing. Delete the adapter once the calculators ship.

### Layer 1.C — `paired_price_dispersion` calculator (`features-cross-instrument-service`)

New feature group calculator handling BOTH `CARRY_BASIS_DATED` (dated future vs spot/ETF held to convergence) AND
`ARBITRAGE_PRICE_DISPERSION` (cross-venue futures pairs of same expiry). Single compute kernel — both archetypes consume
the same `(left, right, day) → spread_bps + annualised_apy_bps + days_to_expiry` shape; the catalog spec rows identify
which legs to pair.

- Bucket: `features-cross-instrument-{pid}` (matches existing per-service bucket convention).
- Inputs: `raw_tick_data` for spot/ETF/futures of catalog-defined `(left_venue, left_root)` +
  `(right_venue, right_root)`.
- Outputs columns: `left_venue`, `left_root`, `right_venue`, `right_root`, `expiry`, `spread_bps`, `annualised_apy_bps`,
  `days_to_expiry`, `available_at` (per workspace `available_at` rule).
- Shard atom: `(asset_group, data_type=paired_price_dispersion, left_venue, left_root, right_venue, right_root, day)`.
- LookaheadBiasError raised loud per workspace rule.

### Layer 1.D — Catalog spec additions (`strategy-service`)

Per user direction this session:

#### `CARRY_BASIS_DATED` (`engine/strategies/v2/target_universe/catalog.py:_build_carry_basis_dated`) — keep existing 7 specs, ADD:

| spot venue           | future venue    | asset                                                                                                           | notes                                                            |
| -------------------- | --------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| NASDAQ (IBIT)        | CME (MBT)       | BTC                                                                                                             | US BTC ETF vs CME micro BTC futures                              |
| NASDAQ (ETHA)        | CME (MET)       | ETH                                                                                                             | US ETH ETF vs CME micro ETH futures                              |
| DERIBIT (spot index) | DERIBIT (dated) | BTC                                                                                                             | intra-Deribit basis (after 2025/2026 deribit-light VMs complete) |
| DERIBIT (spot index) | DERIBIT (dated) | ETH                                                                                                             | intra-Deribit basis                                              |
| ETF placeholder rows | CME futures     | GLD-GC, USO-CL, UNG-NG, SPY-ES, QQQ-NQ — design specs now, leave instrument_ids documented as databento-pending |

#### `ARBITRAGE_PRICE_DISPERSION` (`_build_arbitrage_price_dispersion`) — keep existing DeFi lending pairs, ADD:

| long venue | short venue     | asset           |
| ---------- | --------------- | --------------- |
| CME (MBT)  | DERIBIT (dated) | BTC same expiry |
| CME (MET)  | DERIBIT (dated) | ETH same expiry |

(Future: pattern-extend to other cross-venue futures pairs as databento + Tardis instrument coverage grows.)

**No allocator changes**: `CarryBasisDatedRankAllocator` + `ArbitragePriceDispersionRankAllocator` already exist and
consume the same shape — new specs flow through unchanged.

## Pre-audit manifest

- `unified-api-contracts/unified_api_contracts/internal/domain/defi/`: confirmed exists (paired with `rate_model.py`
  shipped 2026-05-06 commit `c9ea9e6` adding `AAVE_V3_RATE_MODEL_DEFAULTS_BY_ASSET`).
- `features-onchain-service/features_onchain_service/engine/orchestrator.py`: lst_yields + lending_rates calculators
  shipped 2026-05-06 commits `955abb5` + `c90d01a`. Rename safe — Layer 2 tracer has fallback chain.
- `features-cross-instrument-service`: greenfield calculator; pyproject + service plumbing already stood up — confirm
  `feature_group=paired_price_dispersion` doesn't collide with existing keys via UAC `FeatureGroup` enum.
- `strategy-service/engine/strategies/v2/target_universe/catalog.py`:
  - `_build_carry_basis_dated` at line 446-516 (7 specs).
  - `_build_arbitrage_price_dispersion` at line 951-1063 (2 perp + lending-protocol + cross-chain branches).
  - `CarryBasisDatedRankAllocator` + `ArbitragePriceDispersionRankAllocator` already in
    `strategy_service/portfolio_allocator/archetypes.py`.
- `strategy-service/scripts/trace_all_carry_archetypes.py`: Layer 2 adapter shipped commit `6e73475` —
  `_TOKEN_TO_PROTOCOL_ASSET` + `_per_day_lending_supply_apy_bps` fallback chain delete-targets after Layer 1 rebuild.

## Phased execution DAG

```
Phase 1: UAC SSOT + features-onchain calculator emit canonical columns (PARALLEL)
   ├─ 1.A unified-api-contracts: LST_TOKEN_TO_PROTOCOL_ASSET module + helpers
   └─ 1.B features-onchain-service: orchestrator emits protocol/asset/chain alongside token + instrument_id
      (rename aave_supply_apy → supply_apy)

Phase 2: greenfield calculator (SEQUENTIAL after Phase 1 — uses UAC contracts)
   └─ 1.C features-cross-instrument-service: paired_price_dispersion calculator + parquet writes

Phase 3: catalog updates + tracer cleanup (PARALLEL after Phase 2)
   ├─ 1.D strategy-service catalog: CARRY_BASIS_DATED additions + ARBITRAGE_PRICE_DISPERSION refactor
   └─ 1.E strategy-service scripts: delete tracer's _TOKEN_TO_PROTOCOL_ASSET adapter shim once UAC SSOT consumed

Phase 4: re-run partial Stage 3 + Stage 4 historical verification
   ├─ Run trace_all_carry_archetypes against 2026-04-03..04-09 (smoke) — expect ALL 7 archetypes have non-empty
   │  resolutions (CARRY_BASIS_DATED + cross-venue ARBITRAGE_PRICE_DISPERSION pairs newly populated)
   └─ Run against full 2022-01-01..today (Stage 4 historical, overnight VM)
```

## Success criteria

- Phase 1: UAC `LST_TOKEN_TO_PROTOCOL_ASSET` covers every instrument in `instruments-service` `LST.parquet`;
  features-onchain calculators emit `protocol`/`asset`/`chain` columns; `aave_supply_apy` rename applied (or both
  emitted for transition); QG green on both repos.
- Phase 2: `paired_price_dispersion` parquet exists at
  `gs://features-cross-instrument-{pid}/by_date/day=*/feature_group=paired_price_dispersion/features.parquet` for at
  least the 7 catalog `CARRY_BASIS_DATED` specs + 2 added cross-venue futures specs; row count > 0; LookaheadBiasError
  guard wired.
- Phase 3: catalog spec count: `CARRY_BASIS_DATED` ≥ 12 specs (7 existing + 5 added); `ARBITRAGE_PRICE_DISPERSION` ≥ 2
  cross-venue futures specs added beyond DeFi lending pairs; tracer adapter shim deleted.
- Phase 4 (B3 KPI): tracer's `comparison.parquet` has non-empty `realised_apy_bps` for all 7 archetypes including
  `CARRY_BASIS_DATED` over a 7-day window where all 3 input feature groups have data. `flow_of_funds_legs` non-empty for
  the winning slot of each archetype.

## Out-of-scope (deferred)

- Engine state-machine entry-trigger logic for YIELD_ROTATION_LENDING / ARBITRAGE_PRICE_DISPERSION (slots find data but
  `engine.current_position_units` stays 0 throughout). Engine-level concern — separate plan.
- Compound V3 / Spark / Morpho lending-rate capture in MTDS — currently only Aave V3 rows have populated
  `aave_supply_apy`; Compound/Spark rows are all-NaN. MTDS coverage extension separate plan.
- Pyth Solana on-chain price wiring for jitoSOL / mSOL / bSOL — handoff'd 2026-05-06 unbanning + scoped to Solana only;
  covered by `consolidated_defi_data_pipeline_2026_04_15.md` `mtds-s3-5-pyth-oracle` todo.
- Deribit dated/options 2025+2026 backfill completion — VMs auto-stopped early; needs longer-running re-launch
  (`launch-cefi-sharded-backfill.sh ONLY="DERIBIT:2025:light DERIBIT:2026:light" FORCE=1`). Operational, not code.

## Temporary states + their canonical follow-up plans

- `aave_supply_apy → supply_apy` rename (Phase 1.B): tracer Layer 2 fallback chain in
  `strategy-service/scripts/trace_all_carry_archetypes.py:_per_day_lending_supply_apy_bps` is the temporary state.
  Successor: this plan Phase 3.E deletes it after the rename ships.
- ETF placeholder spec rows (Phase 1.D `CARRY_BASIS_DATED`): documented `instrument_id` placeholders for GLD-GC / USO-CL
  / UNG-NG / SPY-ES / QQQ-NQ, marked `databento_pending`. Successor: when databento ETF coverage adds those symbols,
  instruments-service backfill plan flips placeholder → live spec.

## Handoff for next agent (post-2026-05-07 work)

Three hard items remain. Tackle in order.

### 1. Phase 1.B propagation — re-run features-onchain over 30-day window

The new `features-onchain-service@7f1b2a1` calculator emits canonical `protocol` / `asset` / `chain` columns +
`supply_apy` / `borrow_apy` aliases, but the parquets on disk DON'T have these columns yet — they were written by the
prior code. The carry tracer's Layer 2 adapter shim is what translates between the old shape and the new — so until the
features-onchain output is re-generated with the new code, deleting the shim (Phase 3.E) breaks YIELD_STAKING_SIMPLE.

**Action**: launch a features-onchain VM to re-run `lst_yields` + `lending_rates` over 2026-04-03..2026-04-09 (the
verification window from prior session). After rerun, sample one `lending_rates` parquet and assert
`{protocol, chain, asset, supply_apy, borrow_apy}` are all present + populated. The launcher pattern follows the prior
session's `mtds-lending-indices` / similar VMs — see `deployment-service/scripts/vm/`.

### 2. Phase 2 — `paired_price_dispersion` calculator (greenfield)

This is the BIGGEST remaining piece — a new calculator in `features-cross-instrument-service` that handles BOTH
`CARRY_BASIS_DATED` (dated future vs spot/ETF) AND `ARBITRAGE_PRICE_DISPERSION` cross-venue futures pairs through one
compute kernel. Scope estimate: ~600+ LOC across 5 files (calculator + writer plumbing + reader + tests + orchestrator
wiring) — too large to ship safely without a focused session.

**File map**:

- **NEW**: `features_cross_instrument_service/app/calculators/paired_price_dispersion.py` extending
  `BaseFeatureCalculator`. Required props: `feature_group="paired_price_dispersion"`,
  `required_columns=["timestamp", "left_venue", "left_root", "right_venue", "right_root", "left_close", "right_close", "expiry"]`,
  `output_features=["spread_bps", "annualised_apy_bps", "days_to_expiry"]`. `_calculate_features` kernel: spread_bps =
  (right_close − left_close) / left_close × 1e4; annualised_apy_bps = spread_bps × 365 / days_to_expiry. Stamp
  `available_at` = max(left.tick_ts, right.tick_ts) + scrape latency.
- **NEW**: catalog row resolver — reads strategy-service catalog spec params (`cash_venue` / `future_venue` /
  `cash_instrument` / `future_instrument` for `CARRY_BASIS_DATED`; `long_venue` / `short_venue` / `long_instrument` /
  `asset` for `ARBITRAGE_PRICE_DISPERSION`) → emits `(left_venue, left_root, right_venue, right_root)` pairs. This is
  the pre-flight that maps catalog spec rows to MTDS raw_tick_data fetch keys.
- **EDIT**: `features_cross_instrument_service/engine/orchestrator.py` — register the new calculator in the dispatch
  table (currently 17 calculators; this becomes the 18th). Pattern: same as `cross_venue_calculator.py` — see existing
  imports at top of orchestrator.py.
- **EDIT**: UAC `unified_api_contracts.canonical.crosscutting.feature_groups.FeatureGroup` enum — add
  `PAIRED_PRICE_DISPERSION = "paired_price_dispersion"`. Required-inputs DAG entry:
  `{paired_price_dispersion: [raw_tick_data]}`.
- **NEW**: tests under `features-cross-instrument-service/tests/unit/test_paired_price_dispersion.py` covering: kernel
  computation correctness (known spread → expected APY), expiry parsing, single-leg-empty handling (record_empty),
  cross-venue same-expiry pair selection.
- **NEW**: bucket env var per existing convention — `FEATURES_CROSS_INSTRUMENT_BUCKET` env var read by the writer. Shard
  atom per Phase 9 plan:
  `(asset_group, data_type=paired_price_dispersion, left_venue, left_root, right_venue, right_root, day)`.
- **WIRE**: LookaheadBiasError raised loud per workspace rule — every input row consumed must satisfy
  `input.available_at <= target_ts - horizon`. UTL helper `assert_available_at_present` handles the basic check at
  `record_captured`; the calculator is responsible for the strict-mode raise on temporal violation.

**Pre-audit findings from this session**:

- `features-cross-instrument-service` has 17 existing calculators following the `BaseFeatureCalculator` pattern. The
  closest analogues are `cross_venue_calculator.py` (cross-venue spreads — same shape but no temporal arbitrage) and
  `cme_gap.py` (170 LOC, simplest end-to-end example).
- The orchestrator (`engine/orchestrator.py`) dispatches by feature_group string. Adding a new calculator is mostly
  mechanical: one import + one entry in the registry dict.
- The strategy-service catalog rows for the new specs are already wired (this session's `strategy-service@e4a0cdd`).
  Once the calculator emits parquet at the canonical path, the carry tracer's resolver will find it without further
  changes.

### 3. Phase 3.E — delete tracer adapter shim

Once Phase 1.B re-run completes (parquets have canonical columns) AND Phase 2 calculator emits `paired_price_dispersion`
parquet:

- **DELETE** `_TOKEN_TO_PROTOCOL_ASSET` (and `_tokens_for_protocol_asset`, `_filter_lst_yields_by_protocol_asset`) from
  `strategy-service/scripts/trace_all_carry_archetypes.py`. The features-onchain calculator now emits the `protocol` /
  `asset` columns directly.
- **DELETE** the `aave_supply_apy → supply_apy → lending_apy` fallback chain. Calculator emits both `aave_supply_apy`
  AND `supply_apy` (one transition cycle); after cleanup, just read `supply_apy`. The legacy `aave_*` columns can be
  removed from features-onchain in a follow-up plan once all consumers are updated.
- **KEEP** `_normalise_protocol_name` (strips `_V2`/`_V3`) — that's catalog↔parquet vocab translation independent of
  the calculator-side schema, will be needed even after canonical columns ship.

### 4. Phase 4 — verification

- Re-run partial Stage 3 (3 archetypes: YIELD_STAKING_SIMPLE, CARRY_BASIS_DATED, ARBITRAGE_PRICE_DISPERSION) over
  2026-04-03..04-09. Expect ALL 3 archetypes have non-empty `realised_apy_bps` (CARRY_BASIS_DATED previously had no
  calculator at all; ARBITRAGE_PRICE_DISPERSION was blocked by features-delta-one MDPS-loader path drift, fixed in
  `features-delta-one-service@cc339e0`).
- Stage 4 full historical 2022-01-01..today (overnight VM) once Phase 4 partial is green.

### Operational follow-ups (not code)

- Re-launch `cefi-deribit-2025-light` + `cefi-deribit-2026-light` with longer runtime so intra-Deribit
  CARRY_BASIS_DATED + CME-DERIBIT ARBITRAGE_PRICE_DISPERSION specs have data (currently Deribit dated/options ingestion
  is partial for 2025/2026 — only Jan + Apr have all instrument_types). Launcher:
  `ONLY="DERIBIT:2026:light DERIBIT:2025:light" FORCE=1 bash scripts/vm/launch-cefi-sharded-backfill.sh`.
- Compound/Spark/Morpho lending-rate cross-protocol arb: pre-condition is MTDS coverage extension. Their parquet rows
  are currently all-NaN — only Aave V3 has populated values. Out-of-scope per this plan; covered by separate MTDS plan.
