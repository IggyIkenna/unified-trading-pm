---
doc_type: plan
title:
  LST rate honest coverage — wire the four exchange-rate surfaces into the pipeline (denominator → collectors →
  canonical → manifest → daily → sample-verified)
summary: >-
  Operator-directed (2026-07-21) build to bring the four LST exchange-rate surfaces to HONEST COVERAGE end-to-end so the
  DeFi interest PnL can sit on real data. #1 CEX spot = a Tardis backfill (denominator already complete — adding pairs
  is a phantom-minting anti-pattern). #3 Aave oracle = the real code build (plumbing: the getAssetPrice RPC exists but
  is dormant — wire a collection branch + venue registration + Chainlink feed adds, verified on-chain first). #2 DEX
  pool = a collector/endpoint fix (dead Graph subgraphs) + reserve→mid derivation. #4 protocol redemption = a features
  backfill + a Solana/LRT join fix. Denominator-first: register verified feeds/venues so gaps read expected_unattempted
  RED before any fill. Then the interest PnL A2 staking leg (#4) + the recursive borrow leg (unblocks on #3).
status: active
nature: process
asset_group: [defi]
stage: [data, strategy]
repos:
  [
    market-tick-data-service,
    instruments-service,
    unified-api-contracts,
    features-service,
    strategy-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [lst, exchange-rate, oracle, dex, honest-coverage, pnl-correctness, defi, data-pipeline]
related:
  [
    lst_exchange_rate_data_availability_2026_07_21.md,
    pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: ["operator dispatch 2026-07-21: build honest LST-rate coverage then wire interest PnL"]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# LST rate honest coverage — plan of record

**Codex SSOT:** `codex/02-data/lst-exchange-rate-surfaces.md` (the four surfaces, canonical homes, honest-coverage
contract). **Audit:** `plans/active/issues/lst_exchange_rate_data_availability_2026_07_21.md`.

**Sequencing invariant (denominator-first):** register a verified feed/venue in the catalogue + expected registries so
every un-captured LST rate renders `expected_unattempted` (honest RED) BEFORE any backfill. Verify on-chain reality
FIRST so no permanent-false-RED cell is seeded. Shard atom identical writer→manifest→IS→gate→UI.

## Phase 0 — Reality verification (read-only / on-chain; no ship) — pins the TRUE denominator

- [ ] [ONCHAIN] P0. **AAVE reserve oracle reality** — `eth_call getAssetPrice(token)` at a recent block for each
      candidate reserve (wstETH, weETH, rETH, cbETH, rsETH, ezETH, osETH) against `AAVE_ORACLE_ADDRESS` on the main
      Pool; record which return non-zero. rsETH/ezETH may be Lido/Prime-instance-only. Provenance: audit doc §#3.
- [ ] [EXTERNAL] P0. **Chainlink aggregator reality** — confirm on docs.chain.link which of wstETH/weETH/rsETH/ezETH
      have a real PRICE aggregator (not PoR/exchange-rate). Only those get a feed-map entry.
- [ ] [MTDS] P0. **CEX listing reality** — Tardis `availableSymbols` per `*-SPOT` venue per LST base; record genuinely
      listed (LST,venue) vs honest `EXPECTED_INSTRUMENT_NOT_LISTED`. Confirms #1 is backfill-only, no catalogue edit.
- [ ] [MTDS] P0. **DEX endpoint reality** — confirm Curve stETH/ETH + target UniV3/Balancer LST pools roll into
      `catalog.parquet` after a discovery run; identify a live replacement for the dead Curve/Balancer/Sushi subgraphs
      (Graph decentralized-network key / self-host / direct-RPC). If none exists → the DEX collector phase is
      `BLOCKED-CREDENTIALS` (endpoint/key), scaffold + status, not silently dropped.

## Phase 1 — Denominator registration (smallest first-shippable; makes gaps HONEST)

- [ ] [UAC][IS] P1. **Chainlink LST feed-map add** (smallest increment) — add the Phase-0-verified feeds to BOTH the
      MTDS `_oracle_prices_constants.py` (dict shape) and IS `chainlink.py` (tuple shape); the mirror-invariant test
      must pass. Auto-mints `(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` catalogue rows on the next build. One
      quickmerge per repo.
- [ ] [UAC] P1. **AAVE oracle venue registration** — `expected_coverage.py` `AAVE` += `oracle_prices` +
      `AAVE-ETHEREUM: [oracle_prices]`; `defi_venues.py` flip `AAVE-ETHEREUM` phase `pipeline`→`live`;
      `venue_adapter_keys.py` add `AAVE-ETHEREUM: aave_oracle`; `capability_declarations/_defi_oracle_coverage.py`
      coverage-start. Add `aave` to UAC `pipeline_mode_for_source` if absent.
- [ ] [IS] P1. **AaveOracle reference-data adapter** — `adapters/defi/aave_oracle.py` (clone `chainlink.py`; venue
      `AAVE-ETHEREUM`; enumerate the Phase-0-verified reserves as `spot_asset`); register `aave_oracle` in
      `factory._ADAPTERS` + add `AAVE-ETHEREUM` to `orchestrator/defi.py`. Keep IS phase in lockstep with UAC.
- [ ] [IS] P1. **Regenerate catalogue + expected universe** — `build_instrument_catalogue.py` +
      `enumerate_expected_universe.py` (v2); confirm the new `(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` +
      `(AAVE, spot_asset, oracle_prices)` cells appear as `expected_unattempted` (honest RED). Verify #1 (CEX) needs no
      edit (no-op).

## Phase 2 — Collectors ready to fetch

- [ ] [MTDS] P2. **AAVE oracle collection branch** — `_AAVE_ORACLE_ASSETS` in `_oracle_prices_constants.py` +
      `_collect_aave_rows` in `OraclePricesHandler.process()` (LIFT `_ORACLE_ABI`+eth_call from `aave_positions.py`, do
      not re-implement; IS-first filter via `load_oracle_feeds_for_date('AAVE','ETHEREUM',…)`; rows carry
      `source='aave'`, `chain='ETHEREUM'`, `symbol`/`feed`). `_emit_aave_manifest` mirroring `_emit_chainlink_manifest`
      (`record_captured/empty/failed`, `instrument_type=spot_asset`). Confirm STRICT write contract (symbol present).
- [ ] [MTDS] P2. **DEX collector/endpoint** — point `dex_pool_swaps` at the Phase-0 replacement endpoint (or a
      direct-RPC pool-state reader), deepen UniV3, add a reserve→per-interval-mid derivation. If no endpoint/key →
      scaffold + `BLOCKED-CREDENTIALS`, never silently drop.

## Phase 3 — Sample-download test on the `-test-` bucket (runtime verification, no prod write)

- [ ] [MTDS] P3. **Prove force + skip per surface** — sample download for the AAVE oracle (and DEX where endpoint
      available) against the `-test-` bucket: force-leg writes the canonical parquet + manifest `captured`; skip-leg
      fires the freshness skip. Read the VM `run.log` as ground truth. This is the "tested for sample data downloads"
      requirement.

## Phase 4 — Daily-download / MVP gate

- [ ] [IS] P3. **Daily-download inclusion** — confirm the new feeds/venue are `is_mvp`-tagged and land in the daily
      instrument-download universe so they are fetched on the standing cadence, not only on a one-off backfill.

## Phase 5 — Fill on real infra (SPOT VMs; manifest-verified; monitored by TARGET-shard count, not log activity)

- [ ] [MTDS] P2. **#3 oracle backfill** — SPOT-VM RPC backfill (getAssetPrice + Chainlink) over history; monitor by
      manifest count of `(AAVE, spot_asset, oracle_prices)` shards created (`time_created`), not log lines.
- [ ] [MTDS] P2. **#1 CEX-spot contiguity backfill** — full-history Tardis backfill over `*-SPOT` LST venues; SPOT VM,
      `tardis-concurrency-guard` cap-1 (dominant constraint), non-1st-of-month dates use the paid academic key.
- [ ] [FEATURES] P2. **#4 lst_yields backfill** — run the `lst_yields` feature over the full `lst_rates` source
      history + fix the today-vs-prior inner-join/vocab that drops Solana + LRTs (ezETH/rsETH) from the feature output.
- [ ] [MTDS] P3. **#2 DEX fill** — deep-backfill `dex_pool_swaps` once the endpoint lands (else remains
      `BLOCKED-CREDENTIALS`).

## Phase 6 — Interest PnL on honest data (the payoff; see pnl_interest_accrual doc)

- [ ] [STRATEGY] P2. **A2 staking leg** — wire `carry_staked_basis` `STAKING_REWARD`/`CARRY` to the `lst_yields`
      `exchange_rate/prev_rate` index ratio keyed off `cfg['lst_asset']`; explicit-zero the Aave-lending mismodel;
      honest-absence visible; real passive-parity test; 3-lens money-path review; ship to LDR. Prod-NAV recompute stays
      operator-gated.
- [ ] [STRATEGY] P3. **Recursive-staking borrow leg** — unblocks once #3 Aave oracle (collateral) lands; wire the
      `aave_borrow_index` cost leg + the archetype's drivability. Depends on Phase 5 #3.

## Progress Log

- **2026-07-21** — Plan authored from the pipeline-add understand sweep. Codex SSOT `lst-exchange-rate-surfaces.md`
authored alongside. Key reframes captured: #1 CEX = backfill-not-build (catalogue already complete; list edits are
phantom-minting); #3 Aave oracle = plumbing (dormant RPC, not missing); #2 DEX = collector/endpoint problem;
denominator-first honest-coverage invariant. Executing Phase 0 (reality verification) next.
</content>
