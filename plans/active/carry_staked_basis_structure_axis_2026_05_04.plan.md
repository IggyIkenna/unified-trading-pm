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
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
depends_on:
  - defi_pipeline_extension_followups_2026_05_03
todos:
  - id: phase-1a-uac-venue-matrix-extend
    content: |
      - [ ] [AGENT] P0. Extend `unified_api_contracts/registry/venue_collateral.py` `VENUE_COLLATERAL_MATRIX` with LST acceptance rows where verifiable today (Aevo wstETH, GMX-V2 wstETH on ETH-perp markets, Drift wstSOL/jitoSOL). Each new row needs documented haircut + `notes` citing the source. Keep absent rows for unverified venues (default behaviour: `venue_accepts_collateral` returns False) — engine then derives SPLIT_STAKE only.
    status: todo
    note: "Sources: Aevo docs, GMX-V2 markets registry, Drift collateral list. If unverified, omit — better to default to SPLIT_STAKE than over-promise eligibility."
  - id: phase-1b-uac-add-perp-venue-tag
    content: |
      - [ ] [AGENT] P0. In `venue_collateral.py`, add an optional `venue_kind` field to `CollateralAcceptance` (`PERP_CEX` | `PERP_DEX` | `LENDING` | `STAKING`) so callers can filter to perp-margining venues only. Backfill all existing rows. Add `accepted_perp_collateral(venue)` helper returning list filtered to `accepted=True AND venue_kind starts with PERP_`.
    status: todo
  - id: phase-1c-uac-tests-+-qg
    content: |
      - [ ] [SCRIPT] P0. Add unit tests in `unified-api-contracts/tests/internal/unit/` covering: (a) every existing row still resolves, (b) `accepted_perp_collateral("HYPERLIQUID") == ["USDC"]`, (c) new LST rows return correct haircut, (d) absent (venue, token) returns False / None. Run `cd unified-api-contracts && bash scripts/quality-gates.sh`. Quickmerge.
    status: todo
  - id: phase-2a-engine-drop-borrow-path
    content: |
      - [ ] [AGENT] P0. In `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py`, drop `lending_protocol`, `borrow_asset`, `borrow_apy_bps` from `_BasisConfig`, `_extract_config`, `_preflight`, `_build_legs`. Drop the LEND leg (`leg 1`) from the AtomicInstruction emission entirely. Two-leg structure now: (leader) STAKE native→LST, (hedge) TRADE perp short. Update docstring + features-expected list (drop `borrow_apy_bps`).
    status: todo
  - id: phase-2b-engine-usdc-share-class-+-derived-structure
    content: |
      - [ ] [AGENT] P0. Engine takes only **`stake_fraction f` ∈ (0, 1]** as the user-facing structure param (no `margin_structure` enum — derived). Share class = USDC. Preflight queries `accepted_perp_collateral(perp_venue)` to decide leg sequence: (a) if `lst_token` ∈ accepted → leg sequence is BUY_SPOT(USDC→ETH) + STAKE(ETH→LST) + TRANSFER(LST → perp_venue) + TRADE(short ETH-PERP) and `f` controls how much USDC gets converted vs. retained as additional buffer; (b) if `lst_token` ∉ accepted but USDC is accepted (typical CEX) → leg sequence is BUY_SPOT(f·USDC→ETH) + STAKE(ETH→LST) leaving (1−f)·USDC as perp margin + TRADE(short ETH-PERP). Net carry formula in USDC terms: `f · (staking_apy + funding_apy) + (1−f) · usdc_idle_yield − conversion_fees_apy − rebalance_fees_apy`. The `funding_apy` term is positive for short side when funding is positive (longs pay shorts). Drop the explicit `margin_structure` param.
    status: todo
  - id: phase-2c-engine-collateral-haircut-clamp
    content: |
      - [ ] [AGENT] P0. In `_preflight`, look up the perp-venue haircut via `get_collateral_haircut(perp_venue, settle_token)` where `settle_token` is the actual margin asset the engine derived in 2b (LST if accepted there, otherwise USDC). Clamp the perp short notional by `(1 − haircut)`. Reject the slot if **neither** the LST nor USDC is accepted at the perp venue (eligibility error → log + skip; preserves shard isolation). Idle-yield feature `usdc_idle_yield_apy_bps` is only consumed when the derived structure leaves USDC at the perp venue.
    status: todo
    blocked_by: phase-1a-uac-venue-matrix-extend
  - id: phase-2d-engine-unit-tests
    content: |
      - [ ] [SCRIPT] P0. Update `strategy-service/tests/unit/engine/strategies/v2/test_archetype_engines*.py` for the new USDC-share-class semantics. Add cases: (1) Hyperliquid (USDC-only) + stETH → derived structure splits USDC, no LST sent to perp venue; emits 3-leg instruction (BUY_SPOT, STAKE, TRADE); (2) Aevo + wstETH (assuming row added in 1a) → emits 4-leg with TRANSFER LST to perp venue; (3) f=1.0 with USDC-only perp venue → preflight rejects (f=1 means zero perp margin); (4) venue accepts neither LST nor USDC → preflight rejects.
    status: todo
    blocked_by: phase-2b-engine-usdc-share-class-+-derived-structure
  - id: phase-3a-catalog-regenerate
    content: |
      - [ ] [AGENT] P0. Rewrite `_build_carry_staked_basis` in `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py`. **Share class = USDC** (not ETH). For each (lst_venue, lst_token) × (perp_venue): emit slots only if the perp venue accepts EITHER `lst_token` OR `USDC` (use `accepted_perp_collateral`). Emit at f ∈ {0.5, 0.75} (the spot-buy → stake fraction of starting USDC). Initial equity = `Decimal("100000")` USDC. The engine derives the leg sequence from the matrix at runtime — catalog stays minimal. Slot label format: `CARRY_STAKED_BASIS@{lst_venue}-{perp_venue}-f{int(f*100)}-usdc-1h-usdc-v2-prod`.
    status: todo
    blocked_by: phase-2b-engine-usdc-share-class-+-derived-structure
  - id: phase-3b-catalog-tests
    content: |
      - [ ] [SCRIPT] P0. Update `strategy-service/tests/unit/engine/strategies/v2/test_target_universe.py` to assert the new USDC-share-class slot count (3 ETH-LST × 3 ETH-perp × 2 f-values + 2 SOL-LST × 1 SOL-perp × 2 f-values, filtered by venues with USDC or LST accepted). Pin expected slot labels for at least one ETH and one SOL combo to lock the format.
    status: todo
    blocked_by: phase-3a-catalog-regenerate
  - id: phase-3c-strategy-qg-+-quickmerge
    content: |
      - [ ] [SCRIPT] P0. `cd strategy-service && bash scripts/quality-gates.sh` (full Pass 1). Then quickmerge with --files limited to the engine + catalog + tests changed.
    status: todo
    blocked_by: phase-3b-catalog-tests
  - id: phase-4a-tracer-script
    content: |
      - [ ] [AGENT] P1. Add `strategy-service/scripts/trace_carry_staked_basis.py`: iterates the new catalog slots, replays 30 days of (staking_apy_bps, funding_rate_apy_bps, idle_yield_apy_bps, mid_price) feature data via the same `BatchHarness` path the existing tracer family uses, computes net realised APY per slot. Output a parquet table: `slot_label, lst, perp, structure, f, days_in_position, gross_carry_bps, fees_bps, net_apy_bps, max_drawdown_bps, hit_rate`. Writes to `gs://strategy-store-{pid}/tracer_runs/CARRY_STAKED_BASIS/{run_date}/results.parquet`.
    status: todo
    blocked_by: phase-3c-strategy-qg-+-quickmerge
  - id: phase-4b-tracer-run
    content: |
      - [ ] [HUMAN+AGENT] P1. Run the tracer over a 30-day window (2026-04-04 → 2026-05-03) once features-onchain has the LST staking_apy + perp funding feeds backfilled. Compare net APY by structure × f for each (LST, perp) and publish the winning slot per pair. Acceptance: every (lst, perp) has at least one slot with net_apy_bps > 0 OR the pair is documented as currently uneconomic (e.g. funding too negative for the period).
    status: todo
    blocked_by: phase-4a-tracer-script
    note: "Tracer needs upstream features. If staking_apy_bps / funding_rate_apy_bps not yet wired for some venues, plan unblocks once features-onchain ships those feeds. Cross-reference defi_pipeline_extension_followups_2026_05_03 Phase 1 wiring."
  - id: phase-5-pm-doc-update
    content: |
      - [ ] [AGENT] P2. Update `unified-trading-pm/codex/03-strategies/carry-staked-basis.md` (create if missing) capturing: (a) the two structures with formulas, (b) eligibility = derived from VENUE_COLLATERAL_MATRIX, (c) the 30-day tracer protocol, (d) why COLLATERAL_BORROW was dropped (basis erosion via stablecoin borrow). Cross-reference this plan + venue_collateral.py + the tracer script.
    status: todo
    blocked_by: phase-4b-tracer-run
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
