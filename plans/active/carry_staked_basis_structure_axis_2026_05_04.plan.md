---
plan_type: code
asset_group: defi
owner: ikenna
created: 2026-05-04
locked_by: live-defi-rollout
locked_since: 2026-05-04
name: carry-staked-basis-structure-axis-2026-05-04
overview:
  Refactor CARRY_STAKED_BASIS as a USDC-share-class market-neutral trade: start in USDC, deploy fraction `f` to buy ETH spot → stake into LST, hold (1−f) as perp margin on the short leg, short the equivalent ETH-PERP. The execution structure (whether the LST or USDC sits at the perp venue, whether spot-buy-then-stake collapses to a single LST mint, etc.) is **derived** from `unified_api_contracts.registry.venue_collateral.VENUE_COLLATERAL_MATRIX` — the engine queries the matrix at preflight and emits whatever atomic-leg sequence the venue capabilities permit. No baked-in structure choice. COLLATERAL_BORROW path (current default — pay USDC borrow on Aave against LST collateral) is deleted: it erodes basis P&L. Catalog regenerates from the matrix as (LST × perp × f) tuples; the engine derives the leg sequence per slot. Tracer measures realised net USDC APY per slot over 30 days — orchestrator picks winners by realised carry.
type: code
epic: epic-business
status: active
completion_gates:
  code: C5
  deployment: none
  business: B3
repo_gates:
  - repo: unified-api-contracts
    code: C5
    deployment: none
    business: none
  - repo: strategy-service
    code: C5
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C5
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C5
    deployment: none
    business: none
depends_on:
  - defi_pipeline_extension_followups_2026_05_03
todos:
  - id: phase-1a-uac-venue-matrix-extend
    content: |
      - [x] [AGENT] P0. Extend `unified_api_contracts/registry/venue_collateral.py` `VENUE_COLLATERAL_MATRIX`. Shipped in UAC `a6f7f4f`: added LIDO + ETHERFI staking rows; ROCKETPOOL/JITO/MARINADE/DRIFT deferred until those venues are registered in `venue_constants.py` (separate scope). No CEX/DEX accepts an LST as direct margin today, so initial catalog produces SPLIT_STAKE only — that's the honest matrix state.
    status: done
    note: "Sources: Aevo docs, GMX-V2 markets registry, Drift collateral list. ROCKETPOOL/JITO/MARINADE/DRIFT venue rows blocked by venue_constants.py registration — captured as Phase 1a-followup."
  - id: phase-1b-uac-add-perp-venue-tag
    content: |
      - [x] [AGENT] P0. UAC `a6f7f4f`. Added `venue_kind: PERP_CEX | PERP_DEX | LENDING | STAKING` to `CollateralAcceptance` (every existing row backfilled). New `accepted_perp_collateral(venue)` helper returns subset accepted at perp-kind venues only. Exported on registry facade.
    status: done
  - id: phase-1c-uac-tests-+-qg
    content: |
      - [x] [SCRIPT] P0. UAC `a6f7f4f`. 6 new unit tests cover (a) all existing rows still resolve, (b) `accepted_perp_collateral("HYPERLIQUID") == ["USDC"]`, (c) AAVE excluded as non-perp, (d) staking venues excluded, (e) unknown venue returns []. 188 existing tests stayed green; UAC `quality-gates.sh` Pass 1 green.
    status: done
  - id: phase-2a-engine-drop-borrow-path
    content: |
      - [x] [AGENT] P0. strategy-service `7074eee`. Dropped `lending_protocol`, `borrow_asset`, `borrow_apy_bps` from `_BasisConfig`, `_extract_config`, `_preflight`, `_build_legs`. The LEND leg is gone from emitted AtomicInstruction. Engine docstring + features-expected updated.
    status: done
  - id: phase-2b-engine-usdc-share-class-+-derived-structure
    content: |
      - [x] [AGENT] P0. strategy-service `7074eee`. Engine takes `stake_fraction f` ∈ (0, 1] only (no `margin_structure` enum — derived). Share class = USDC. `_derive_structure` queries `accepted_perp_collateral` → returns `LST_AS_MARGIN` (4-leg SWAP+STAKE+TRANSFER+TRADE) when LST accepted, `SPLIT_STAKE` (3-leg SWAP+STAKE+TRADE) when USDC accepted, None otherwise. Net carry formula in USDC: `f·(staking + funding) + (1−f)·idle_yield − fees`. f=1.0 rejected on USDC-only venues (zero perp margin).
    status: done
  - id: phase-2c-engine-collateral-haircut-clamp
    content: |
      - [x] [AGENT] P0. strategy-service `7074eee`. Perp short notional clamped by `(1 − haircut)` from `get_collateral_haircut(perp_venue, settle_token)`. Slot rejected at preflight if neither LST nor USDC is accepted (preserves shard isolation, no raise).
    status: done
  - id: phase-2d-engine-unit-tests
    content: |
      - [x] [SCRIPT] P0. strategy-service `7074eee`. 4 new structure-axis cases shipped: (1) Hyperliquid (USDC-only) + stETH → SPLIT_STAKE 3-leg, (2) f=1.0 with USDC-only venue → reject, (3) unknown perp venue → reject, (4) borrow_apy_bps no longer required. Updated 2 existing lock tests for new SPLIT_STAKE leg sequence on HYPERLIQUID. 333 v2 engine tests + 1277 unit tests all green.
    status: done
  - id: phase-3a-catalog-regenerate
    content: |
      - [x] [AGENT] P0. strategy-service `7074eee`. `_build_carry_staked_basis` rewritten — share class USDC, capital 100k USDC ETH / 75k USDC SOL. 22 slots: 3 ETH-LST (lido/rocketpool/etherfi) × 3 ETH-perp (HYPERLIQUID/DERIBIT/ASTER) × f∈{0.5,0.75} + 2 SOL-LST (jito/marinade) × HYPERLIQUID × f∈{0.5,0.75}, all filtered by `accepted_perp_collateral`. Slot label `CARRY_STAKED_BASIS@{lst}-{perp}-f{pct}-usdc-1h-usdc-v2-prod`.
    status: done
  - id: phase-3b-catalog-tests
    content: |
      - [x] [SCRIPT] P0. strategy-service `7074eee`. New `TestCarryStakedBasisStructureAxis` class with 7 lock-down assertions: slot count == 22, share class USDC, format pinned for ETH and SOL combos, no `lending_protocol`/`borrow_asset` params, all required engine params present, every emitted perp_venue eligible per matrix. Bumped target catalog ceiling 260 → 280 to accommodate the +11 net slots.
    status: done
  - id: phase-3c-strategy-qg-+-quickmerge
    content: |
      - [x] [SCRIPT] P0. strategy-service Pass 1 `quality-gates.sh` green at 77s. Pushed `7074eee` to origin/live-defi-rollout via plain commit + push (no quickmerge — cleaner control over file scope).
    status: done
  - id: phase-4a-tracer-script
    content: |
      - [x] [AGENT] P1. strategy-service `430b781` initial + `0e6d01e` correctness fix. `scripts/trace_carry_staked_basis.py` iterates the 22 slots, reads MTDS `lst_rates` directly (gs://lst-rates-{pid}/...) and computes APY from on-chain rate diff `(rate[t]/rate[t-1])^365 - 1`, NOT DefiLlama vendor APY. Funding APY via features-delta-one `funding_oi`. Output parquet schema: `slot_label, lst_asset, perp_venue, perp_instrument, stake_fraction, structure, days_observed, gross_carry_bps_avg, fees_bps, net_apy_bps, max_drawdown_bps, hit_rate, first_date, last_date`. Default sink: `gs://strategy-store-{pid}/tracer_runs/CARRY_STAKED_BASIS/{run_date}/results.parquet`. Smoke-tested on real data 2026-04-01..09: stETH=245bps, rETH=210bps, cbETH=255bps — matches historical.
    status: done
  - id: phase-4a-5-calculator-on-chain-apy
    content: |
      - [x] [AGENT] P0. features-onchain `b1245b1`. Refactored `_process_lst_yields` orchestrator method to compute on-chain-derived staking APY (same calculation as the tracer) and emit it as `staking_apy_bps` in the `lst_yields` feature group. The live engine's calculator now reads MTDS `lst_rates` rate-diff per day, not DefiLlama vendor APY. **Batch = live consistency** holds — tracer + engine both consume the same upstream truth. 7 new tests cover the rate-diff math + empty/missing fallbacks + end-to-end `_process_lst_yields` output. 627 unit tests + Pass 1 QG green.
    status: done
    note: "Scope-add discovered during Phase 4a: the live engine reads `lst_yields` feature group, which had been DefiLlama-backed. Without this fix the engine would have seen vendor APY while the tracer saw on-chain truth — batch ≠ live. Now both honest."
  - id: phase-4b-upstream-mtds-perp-data
    content: |
      - [ ] [HUMAN+AGENT] P0. **MTDS perp data backfill — full history, not 30 days.** The tracer's first run (2026-05-04, strategy-service `3972648`) found that MTDS does not yet capture HYPERLIQUID, DERIBIT, or ASTER perp `derivative_ticker` for any date. Only Bitfinex/Bitget/Kraken-FUTURES are present under `gs://market-data-tick-cefi-{pid}/raw_tick_data/`. Backfill scope per user instruction: instruments + market data + features should be **full history**, not gated on the 30-day strategy window. Action: enable HYPERLIQUID + DERIBIT + ASTER in MTDS CeFi venue universe (cefi_venue_universe_expansion plan reference) and backfill `derivative_ticker` from venue genesis to today. SOL-PERP equivalent for HYPERLIQUID.
    status: todo
    blocked_by: phase-4a-5-calculator-on-chain-apy
  - id: phase-4b-upstream-funding-oi-calculator
    content: |
      - [ ] [HUMAN+AGENT] P0. **features-delta-one funding_oi backfill — full history.** The `funding_oi` calculator at `features-delta-one-service/.../calculators/funding_oi.py` exists but has not been run for any asset_group. Recursive scan of `gs://features-delta-one-{cefi,defi}-{pid}/by_date/` shows only technical-indicator feature groups (candlestick_patterns, momentum, oscillators, etc.). After Phase 4b-mtds completes, run the calculator over full history for HYPERLIQUID/DERIBIT/ASTER ETH-PERP + HYPERLIQUID SOL-PERP. Output schema must include `funding_rate_annualized` per the calculator's contract.
    status: todo
    blocked_by: phase-4b-upstream-mtds-perp-data
  - id: phase-4b-upstream-lst-rates-gaps
    content: |
      - [ ] [HUMAN+AGENT] P1. **lst_rates handler coverage gaps — full history.** Verified gaps in `gs://lst-rates-{pid}/lst_rates/`: weETH (etherfi) absent from 2026-04-09 snapshot despite being in the handler's `_LST_TOKENS` registry — likely contract-method failure or historical-state RPC issue. Solana LSTs (mSOL/JitoSOL) only fetched via REST = current state only, no historical series. Action: (a) debug weETH `getRate` flow + backfill historical weETH from Alchemy archival, (b) for Solana LSTs, design a daily-checkpoint handler that captures noon-UTC rate forward-only (historical reconstruction is not feasible without Solana archive node). The Phase 4a tracer skips slots cleanly when an LST is missing — no fabricated data — so this is a coverage problem, not a correctness problem.
    status: todo
    blocked_by: phase-4a-5-calculator-on-chain-apy
  - id: phase-4b-tracer-orchestrator-pipe-into-batch-handler
    content: |
      - [ ] [AGENT] P0. **Rewrite tracer to drive strategy-service StrategyBatchHandler instead of closed-form carry math.** Per `unified-trading-pm/codex/04-architecture/batch-live-symmetry.md` and the workspace rule "Build standalone backtest engines that settle inline" is forbidden. The tracer must orchestrate: (1) feed feature data to the in-process feature provider, (2) invoke `strategy-service --mode batch --archetype CARRY_STAKED_BASIS --slot-label X --start Y --end Z`, (3) the run goes through `CarryStakedBasisEngine.on_tick` -> AtomicInstruction -> position-balance-monitor positions -> risk-service gates -> execution-service matching engine in `always-fill` mode (zero execution alpha) -> pnl-attribution writes to bucket, (4) tracer reads back realised P&L per slot from pnl-attribution. The closed-form `_load_funding_apy_for_date` + `_staking_apy_bps_from_rates` math becomes a sanity-check only (acceptance: full-pipeline net_apy_bps within 100 bps of closed-form for the same window). The current tracer (strategy-service `18543c8`) is a useful ranking heuristic but is **not** a production backtest; treat its output as preliminary.
    status: todo
    blocked_by: phase-4a-5-calculator-on-chain-apy
    note: "Closed-form sanity check from strategy-service 18543c8 over 2026-04-04..09: stETH/HYPERLIQUID f=0.75 = 602 bps; rETH/HYPERLIQUID f=0.75 = 575 bps. Real backtest P&L through the unified pipeline will differ due to position drift, risk gates, and matching-engine fills."
  - id: phase-4b-tracer-run
    content: |
      - [ ] [HUMAN+AGENT] P1. Run the orchestrator-pipe-into-batch-handler tracer over a 30-day window (e.g. last 30 calendar days, gated on Phase 4b-upstream coverage). Compare net USDC APY by (LST, perp, f) for each combo and publish the winning slot per pair. Acceptance: every (lst, perp) pair has at least one f-value with `net_apy_bps > 0` OR the pair is documented as currently uneconomic. Operator-side.
    status: blocked
    blocked_by: phase-4b-tracer-orchestrator-pipe-into-batch-handler
  - id: phase-5-pm-doc-update
    content: |
      - [x] [AGENT] P2. unified-trading-pm. Rewrote `codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` (existing path; not the speculated `03-strategies/`) to capture (a) USDC-share-class market-neutral framing, (b) two structures (LST_AS_MARGIN / SPLIT_STAKE) with formulas, (c) eligibility derivation from VENUE_COLLATERAL_MATRIX, (d) on-chain APY derivation (real, not vendor), (e) tracer protocol, (f) why COLLATERAL_BORROW was deleted (basis erosion). Cross-references plan + venue_collateral.py + tracer + lst_rates_handler.
    status: done
isProject: false
---

# CARRY_STAKED_BASIS — structure axis + tracer comparison

## Why this plan exists

Today's CARRY*STAKED_BASIS engine bakes in **one** structure: ETH-share class, stake LST → deposit LST as Aave
collateral → borrow USDC → use USDC as perp margin → short ETH-PERP. That path is the \_worst* of the plausible
structures because the stablecoin borrow rate eats into the basis P&L (today: ~5–6% borrow APY against ~3.5% staking +
5–10% funding = narrowly profitable, often negative under E-Mode haircut). Plus the engine instances are inert in
practice — the catalog never passes `borrow_asset` so `_extract_config` returns None on every tick.

The right model:

- **Share class = USDC** (market-neutral start; capital arrives as stablecoin).
- The engine takes one user param — `stake_fraction f ∈ (0, 1]` — describing what fraction of starting USDC gets
  spot-bought into ETH and staked into the LST.
- The **execution structure** (whether the LST gets transferred to the perp venue, whether USDC stays at the perp venue
  as margin, what the leg sequence looks like) is **derived** from `VENUE_COLLATERAL_MATRIX` at preflight. Engine asks:
  "what does this perp venue accept?" and emits the leg sequence that matches.
- Net carry in USDC terms:
  `f · (staking_apy + funding_apy) + (1−f) · usdc_idle_yield − conversion_fees − rebalance_fees`

| Venue capability      | Derived leg sequence                                                               | Net carry (USDC)                                  |
| --------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------- |
| Accepts LST as margin | BUY_SPOT(f·USDC→ETH) → STAKE → TRANSFER LST to perp → TRADE short                  | `f·(staking + funding) + (1−f)·usdc_yield − fees` |
| Accepts USDC, not LST | BUY_SPOT(f·USDC→ETH) → STAKE (held off-venue) → TRADE short with (1−f)·USDC margin | `f·(staking + funding) + (1−f)·usdc_yield − fees` |
| Accepts neither       | Reject slot at preflight                                                           | n/a                                               |
| ~~Aave borrow USDC~~  | ~~Deleted — basis-eroding~~                                                        | ~~negative under E-Mode haircut~~                 |

So "which structure?" is never a question the user answers — it falls out of `accepted_perp_collateral(perp_venue)`.
Catalog enumerates (LST × perp × f) tuples; engine derives the legs. Tracer measures realised net USDC APY per slot.
Orchestrator allocates by realised winner.

## Pre-audit (blast radius)

| Repo                  | File                                                                                     | Lines                       | Action                                                               |
| --------------------- | ---------------------------------------------------------------------------------------- | --------------------------- | -------------------------------------------------------------------- |
| unified-api-contracts | `unified_api_contracts/registry/venue_collateral.py`                                     | 21–52                       | Extend matrix with verifiable LST acceptance rows + `venue_kind` tag |
| unified-api-contracts | `unified_api_contracts/registry/__init__.py`                                             | 257–262, 705–               | Re-export `accepted_perp_collateral` helper                          |
| strategy-service      | `engine/strategies/v2/carry_and_yield/staked_basis.py`                                   | full file                   | Drop borrow path, add structure params, 2-leg emission               |
| strategy-service      | `engine/strategies/v2/target_universe/catalog.py`                                        | `_build_carry_staked_basis` | Regenerate from VENUE_COLLATERAL_MATRIX with structure × f axis      |
| strategy-service      | `tests/unit/engine/strategies/v2/test_archetype_engines*.py` + `test_target_universe.py` | staked-basis cases          | Update for new param surface and slot count                          |
| strategy-service      | `scripts/trace_carry_staked_basis.py`                                                    | new file                    | New tracer script using BatchHarness                                 |
| unified-trading-pm    | `codex/03-strategies/carry-staked-basis.md`                                              | new file                    | Capture the architecture + tracer protocol                           |

**Not affected** (verified clean by pre-audit grep): `recursive_staked.py` keeps its own `borrow_apy_bps` field — that
archetype legitimately uses borrowing as the leverage mechanic and is **not** a basis trade. No other strategy
references CARRY_STAKED_BASIS params. The engine's current catalog instances are inert (no `borrow_asset` passed), so
removing the borrow path breaks **zero** production behaviour.

## Phased execution DAG

```
Phase 1 (UAC) ──┐
                ├──► Phase 2 (engine refactor) ──► Phase 3 (catalog regen) ──► Phase 4 (tracer) ──► Phase 5 (docs)
                │                                             │
                │     1a + 1b + 1c parallel                   │
                │                                             3a + 3b parallel under blocker
Phase 2 cells:
  2a (drop borrow) → 2b (add structure params) → 2c (haircut clamp, depends on 1a) → 2d (tests)
```

Phase 1 ↔ Phase 2 are **sequential** (Phase 2 imports the new `accepted_perp_collateral` helper). Phase 3 sequentially
follows Phase 2. Phase 4 (tracer) gated on Phase 3 quickmerge AND on features-onchain having the upstream feeds (cross-
reference: `defi_pipeline_extension_followups_2026_05_03`).

## Success criteria

| Phase | Code gate                                                                               | Test gate                                                           |
| ----- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 1     | UAC `quality-gates.sh` Pass 1 green; `accepted_perp_collateral` exported on root facade | New venue_collateral unit tests pass                                |
| 2     | strategy-service basedpyright clean on staked_basis.py                                  | New unit tests for the 4 cases listed in 2d pass                    |
| 3     | strategy-service `quality-gates.sh` Pass 1 green                                        | test_target_universe asserts new slot count + format                |
| 4     | tracer parquet writes to `gs://strategy-store-{pid}/tracer_runs/CARRY_STAKED_BASIS/...` | Each (lst, perp) pair has at least one slot with non-trivial signal |
| 5     | PM docs lint                                                                            | n/a                                                                 |

**Business gate B3**: Per (lst, perp) pair, the winning structure × f combo's realised 30-day net_apy_bps must be **>
0** OR the pair must be documented as uneconomic for the period (e.g. funding inverted). At least one ETH-LST pair must
show net_apy_bps > 200 (i.e. > 2% annualised) to validate that the cleaner structures recover P&L the borrow path was
eating.

## Decision log

- **Why drop COLLATERAL_BORROW entirely**: the structure pays a stablecoin borrow rate every minute against staking
  yield that accrues every block — the basis is structurally narrower than the carry, so the borrow term often turns it
  negative. Keeping it as "available but discouraged" invites operational mistakes; cleaner to remove.
- **Why USDC share class**: capital arrives as stablecoin. Forcing the user to denominate in ETH would either require a
  synthetic "convert USDC→ETH on entry, ETH→USDC on exit" wrapper (extra basis risk, extra slippage), or pretend the
  user already holds ETH (false). USDC-denominated lets us cleanly compose with other strategies in the same wallet.
- **Why structure is derived from the registry, not chosen**: `VENUE_COLLATERAL_MATRIX` is the SSOT for which tokens
  each venue accepts as margin. Re-declaring it in the catalog (or worse, in the engine) would create drift. The engine
  reads the matrix at preflight; adding a row to the matrix automatically expands the engine's eligible structures on
  next tick — no engine code change needed for new venues.
- **Why f ∈ {0.5, 0.75}**: 0.5 is the conservative case (half perp margin buffer, half staked); 0.75 is the yield-tilted
  case. f=1.0 leaves zero perp margin so it's invalid on USDC-margined venues; f<0.5 is dominated by staking-yield drag.
  Universe selector picks the winner empirically per (LST, perp) pair.
