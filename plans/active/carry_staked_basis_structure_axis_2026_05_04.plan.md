---
plan_type: code
asset_group: defi
owner: ikenna
created: 2026-05-04
last_updated: 2026-05-05
locked_by: live-defi-rollout
locked_since: 2026-05-04
name: carry-staked-basis-structure-axis-2026-05-04
overview:
  CARRY_STAKED_BASIS is a market-neutral carry trade in USDC share class — long LST, short perp on the same coin, with the LST acting as the perp short's cross-margin. Three architectural pivots over four sessions led here:

    1. (2026-05-04) Refactor away from the COLLATERAL_BORROW default — borrowing USDC on Aave against LST to fund the perp short eats the basis. Replaced by a structure derived from VENUE_COLLATERAL_MATRIX at preflight (LST_AS_MARGIN if accepted, SPLIT_STAKE otherwise).
    2. (2026-05-05) Delete SPLIT_STAKE — strictly dominated by CARRY_BASIS_PERP at 2x size on the unstaked half whenever `funding > staking·f / (2-f)` (almost always at MVP-coin level), and dominated by CARRY_RECURSIVE_STAKED whenever `staking > 3·funding`. Firm rule: if the LST is not accepted as direct cross-margin at the perp venue, the slot is rejected at preflight. LST_AS_MARGIN is the only allowed structure post-2026-05-05.
    3. (2026-05-05) Per-LST × per-venue acceptance is the universe — VENUE_COLLATERAL_MATRIX must encode each individual LST (eETH/weETH, stETH/wstETH, rETH, cbETH, jitoSOL, mSOL, bSOL, …) per venue, with verifiable haircuts. CARRY_STAKED_BASIS catalog enumerates `(lst, perp_venue) ∈ accepted_perp_collateral` filtered. Today that set is 2 (DRIFT/jitoSOL, DRIFT/mSOL); honest, grows organically as Phase 7 audit lands ETH-LST rows.

  Each archetype runs its own ranker (Phase 8) — one shared `BaseRankAllocator` + 7 subclasses with archetype-specific universe filter + ranking metric + top-N config + 250 bps default threshold. CARRY_STAKED_BASIS ranker filters to LST-margin-eligible tuples and ranks by combined `staking_apy_total + funding_apy` (USDC-denominated). No cross-archetype switching — that's a future layer. Tracer drives V2BatchHarness through the full live pipeline (matching engine, position-balance-monitor, risk-service) — batch = live, no closed-form math.

  Share-class table (delta-neutrality intrinsic to archetype, share-class is the eligibility filter):
    YIELD_STAKING_SIMPLE → ETH / SOL only (LST appreciates in same denom).
    CARRY_BASIS_PERP → USDC / USDT only (spot + perp short cancels in USD).
    CARRY_STAKED_BASIS → USDC / USDT only (staked-long + perp-short cancels in USD; LST sits at perp venue).
    CARRY_RECURSIVE_STAKED → ETH or USDC / USDT (ETH path: stake-long + ETH-borrow-short; USD path: USD collateral → borrow ETH → stake).
    CARRY_BASIS_DATED → USDC / USDT only (long spot + short dated future cancels in USD).
    YIELD_ROTATION_LENDING → USDC / USDT (lending stables; no underlying exposure).
    ARBITRAGE_PRICE_DISPERSION → USDC / USDT (perps OR dated, not both — configurable).
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
      - [x] [HUMAN+AGENT] P0. **MTDS perp data backfill — confirmed captured.** 2026-05-05 audit of `gs://market-data-tick-cefi-{pid}/raw_tick_data/by_date/day=2026-04-09/` shows BINANCE-FUTURES, BYBIT, OKX-SWAP, DERIBIT, HYPERLIQUID, BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES all have `derivative_ticker` (which carries `funding_rate` + `open_interest` + `mark_price` + `index_price` per Tardis schema). Plus native `gs://perp-funding-{pid}/perp_funding/{hyperliquid,gmx}/`. Coverage ceiling 2026-04-14 (forward-poll has stalled — separate freshness issue). Original tracer-blocker outdated.
    status: done
    note: "Original blocker dated to 2026-05-04 referenced a hard MTDS gap; 2026-05-05 audit confirmed capture exists for all 8 perp venues. Real blocker is forward-poll freshness ceiling 2026-04-14, not capture."
  - id: phase-4b-upstream-funding-oi-calculator
    content: |
      - [x] [HUMAN+AGENT] P0. **features-delta-one funding_oi backfill — VMs launched 2026-05-05.** The `funding_oi` calculator at `features-delta-one-service/.../app/calculators/funding_oi.py:16 class FundingOI` reads `funding_rate` + `open_interest` (+ optional `mark_price`/`index_price`) from `derivative_ticker` and emits a 12-column feature frame: `funding_rate_raw`, `funding_rate_annualized` (=`rate × 3 × 365`, the metric `CarryBasisPerpRankAllocator` consumes), `funding_positive`/`funding_negative`/`funding_extreme_*` flags, `open_interest_raw`, `oi_change`/`oi_change_pct`, `basis`/`basis_pct`, plus rolling stats `funding_ma_{w}` / `funding_std_{w}` / `funding_min_{w}` / `funding_max_{w}` / `oi_ma_{w}`. Two backfill VMs running 2026-05-05: `features-delta-one-defi-backfill-20260505-115343` (HYPERLIQUID + GMX, 2021-09-01 → 2026-04-14) + `features-delta-one-cefi-backfill-20260505-115407` (BINANCE-FUTURES + BYBIT + OKX-SWAP + DERIBIT + BITGET-FUTURES + KRAKEN-FUTURES + BITFINEX-FUTURES + HYPERLIQUID, 2022-11-02 → 2026-04-14). Auto-shutdown on completion.
    status: in-progress
  - id: phase-4b-upstream-lst-rates-gaps
    content: |
      - [x] [AGENT] P0. **MTDS Solana decoder + EVM hardening shipped 2026-05-05** at MTDS `039cfc1`. New `cli/handlers/solana_lst_archival.py` with 3-tier flow: Tier 1 (Alchemy `getAccountInfo` + SPL stake-pool Borsh decoder, current-state, **Jito only — Marinade IDL deferred**), Tier 2 (The Graph subgraph daily snapshots, **structurally complete but no-op until UAC `SUBGRAPH_IDS["jito"|"marinade"]["SOLANA"]` populated** — when added, lights up automatically without MTDS code change), Tier 3 (REST fallback, current-day only). EVM `_query_rate_with_retry` adds 3-attempt retry + structured per-failure logging (token, block, attempt, exc class, msg) for the weETH/ankrETH gap diagnosis. 16 unit tests, QG green. Backfill VM `mtds-lst-rates-20260505-121442` running 2026-04-05 → 2026-05-05 to fill the gap and pick up retry hardening for any prior transient failures.
    status: in-progress
    note: "For historical Solana days without subgraph: handler records `empty_confirmed` (legitimate 'we tried, no source has it') instead of fudging today's REST rate into a 2024 partition — explicitly noted in module + handler docstrings. See follow-up phase-4b-uac-solana-subgraph-ids."
  - id: phase-4b-uac-solana-subgraph-ids
    content: |
      - [x] [AGENT] P1. **Investigated 2026-05-05: NO production Jito/Marinade Solana subgraphs exist on The Graph.** Verified via workspace-wide grep + audit of UAC `SUBGRAPH_IDS` (in `registry/capability_declarations/_defi.py`) — every existing entry is EVM (Aave V3 / Compound V3 / Spark / Uniswap V2/V3/V4 / Balancer / Curve / Sushi / Aerodrome / Velodrome / Camelot / TraderJoe / Morpho / Fluid / GMX). Solana protocols generally don't use The Graph because Solana's account-state model differs fundamentally from EVM's event-log indexing — Solana state lives in PDAs that protocols expose via direct RPC `getAccountInfo` or protocol-specific REST APIs. Adding placeholder/fake subgraph IDs would be cargo-cult. **Closing this tracker; superseded by phase-4b-tier3-historical-rest below.**
    status: done
    note: "Closing because no production subgraph exists. The right fix is enhancing Tier 3 REST historical lookup (next phase) — both Jito + Marinade REST endpoints already expose multi-day time-series data; the current handler just reads `[-1]` and discards the historical window."
  - id: phase-4b-tier3-historical-rest
    content: |
      - [ ] [AGENT] P1. **MTDS Tier 3 historical REST enhancement** — historicise Solana LST rates by extracting from the time-series the existing REST endpoints already return. (a) **Jito** `kobe.mainnet.jito.network/api/v1/stake_pool_stats` returns `tvl[]`, `supply[]`, `apy[]` arrays where each entry is `{"data": value, "date": iso8601}` going back ~years. Current `_fetch_jito_rate` reads `tvl_series[-1]` only; replace with `_lookup_at_date(series, target_date_str)` that finds the entry whose `date` matches and computes `rate = (tvl_lamports / 1e9) / supply` for that day. (b) **Marinade** `api.marinade.finance/msol/apy/365d` — the `365d` in the URL is literally 365 days of history; same date-lookup pattern. (c) Wire into `solana_lst_archival.fetch_solana_lst_rates_at_slot` so the date-keyed lookup is used for ANY day (current OR historical), and Tier 1 (Alchemy `getAccountInfo` + Borsh) becomes a sanity check / cross-validation layer for the current day only. (d) Add tests: hardcoded fixture for the time-series JSON shape, assertions that lookup-by-date returns the right entry, that out-of-range dates return None (not the current-day value, which would be silently wrong). After this lands: re-run `mtds-lst-rates-` backfill VM over the full historical window (2022-01-01 → today) — Solana side now produces real historical rates for every day in the Jito + Marinade history windows. EVM side already historicised via Alchemy archival eth_call (already shipped at MTDS `039cfc1`).
    status: todo
    blocked_by: phase-4b-upstream-lst-rates-gaps
  - id: phase-4b-tracer-orchestrator-pipe-into-batch-handler
    content: |
      - [x] [AGENT] P0. strategy-service `6d805e0`. Tracer now constructs `V2BatchHarness` per slot and drives `harness.on_tick(candle, features, predictions, now_utc)` day by day. The harness wraps `V2EngineOrchestrator` + the same position-state semantics live mode runs through (per `_apply_*` dispatchers in `batch_harness.py`) — no standalone backtest engine, no inline settlement. Engine's preflight (`entry_bps=200`, `exit_bps=50`) decides each day whether to enter/exit; tracer accrues realised carry only on in-position days (read from `engine.current_position_units`, since `harness.position_state` stays empty for ATOMIC instructions by design — matching-engine territory). Validates against my prior closed-form: same numbers over 2026-04-04..09 because every day was above entry_bps; over windows with funding-regime changes the V2BatchHarness output will diverge as the engine skips below-threshold days.
    status: done
    note: "Validation run 2026-05-04: 4 slots through V2BatchHarness, days_in_pos=6/6 instr_emitted=6 each, net_apy 358-602 bps. Output: gs://strategy-store-{pid}/tracer_runs/CARRY_STAKED_BASIS/2026-05-04/results.parquet."
  - id: phase-4b-tracer-run
    content: |
      - [ ] [HUMAN+AGENT] P1. Run the orchestrator-pipe-into-batch-handler tracer over a 30-day window (e.g. last 30 calendar days, gated on Phase 4b-upstream coverage). Compare net USDC APY by (LST, perp, f) for each combo and publish the winning slot per pair. Acceptance: every (lst, perp) pair has at least one f-value with `net_apy_bps > 0` OR the pair is documented as currently uneconomic. Operator-side.
    status: blocked
    blocked_by: phase-4b-tracer-orchestrator-pipe-into-batch-handler
  - id: phase-5-pm-doc-update
    content: |
      - [x] [AGENT] P2. unified-trading-pm. Rewrote `codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` (existing path; not the speculated `03-strategies/`) to capture (a) USDC-share-class market-neutral framing, (b) two structures (LST_AS_MARGIN / SPLIT_STAKE) with formulas, (c) eligibility derivation from VENUE_COLLATERAL_MATRIX, (d) on-chain APY derivation (real, not vendor), (e) tracer protocol, (f) why COLLATERAL_BORROW was deleted (basis erosion). Cross-references plan + venue_collateral.py + tracer + lst_rates_handler.
    status: done
    note: "Superseded by Phase 6: SPLIT_STAKE was subsequently deleted as strictly dominated; LST_AS_MARGIN is the only allowed structure post-2026-05-05. PM doc to be re-rewritten in Phase 6c."
  - id: phase-6a-engine-delete-split-stake
    content: |
      - [x] [AGENT] P0. strategy-service local — `staked_basis.py` engine: `MarginStructure = Literal["LST_AS_MARGIN"]` (was `LST_AS_MARGIN | SPLIT_STAKE`). `_derive_structure(cfg)` now returns `None` unless the perp venue accepts the LST per `accepted_perp_collateral(perp_venue)`; no USDC-fallback path. `_resolve_setup` defaults `stake_fraction=1.0`; the f-grid is gone (LST is the perp margin, no spare USDC needed). `_build_legs` always emits the 4-leg sequence SWAP + STAKE + TRANSFER + TRADE. `declare_leg_portfolio_state` always reports `lst_long.venue == perp_venue` (LST sits at the perp venue as cross-margin).
    status: done
    note: "Why SPLIT_STAKE is dominated — direct compare at given stake_fraction f and capital C: SPLIT_STAKE = f·(staking + funding) + (1-f)·idle_yield; CARRY_BASIS_PERP at 2x size on the unstaked half = 2·funding. SPLIT_STAKE < BASIS_PERP iff funding > staking·f / (2-f). For f=0.5: BASIS_PERP wins iff funding > staking/3 — almost always true at MVP-coin level. For staking > 3·funding: CARRY_RECURSIVE_STAKED wins by leverage. There is no funding regime where SPLIT_STAKE is the right answer. User explicit: 'if you can't use this liquid staking token as collateral to short the perp, then it doesn't make sense to do the trade.'"
  - id: phase-6b-catalog-collapse-to-matrix-only
    content: |
      - [x] [AGENT] P0. strategy-service local — `target_universe/catalog.py::_build_carry_staked_basis`: enumerate `(lst_asset, perp_venue) ∈ accepted_perp_collateral × LST_REGISTRY` filtered by acceptance. `_STAKED_BASIS_F_VALUES = (Decimal("1.0"),)` only. `_resolve_start_token` requires `lst_asset in accepted` (was OR-with-stable). Slot count today = 2: `CARRY_STAKED_BASIS@jito-drift-f100-usdc-1h-usdc-v2-prod` + `CARRY_STAKED_BASIS@marinade-drift-f100-usdc-1h-usdc-v2-prod`. Honest: DRIFT is the only venue today that accepts an LST as cross-margin per the current matrix (jitoSOL + mSOL, 10% haircut). The slot count grows directly when Phase 7 adds verified ETH-LST-margin rows.
    status: done
  - id: phase-6c-tests-+-pm-doc-rewrite
    content: |
      - [x] [SCRIPT] P0. strategy-service local — 47 carry-and-yield-related unit tests + full unit suite (1,279 tests) all green after SPLIT_STAKE deletion. `test_target_universe.py::test_no_archetype_has_fewer_than_three_rows` carries a documented CARRY_STAKED_BASIS exception (floor lowered to 1) — the count tracks `VENUE_COLLATERAL_MATRIX` directly; no synthetic floor. `test_archetype_engines_filled.py` cases rewritten: HYPERLIQUID/stETH always rejects (no LST_AS_MARGIN available), unknown-perp-venue rejects, no-borrow-apy uses DRIFT/JitoSOL.
      - [ ] [AGENT] P1. unified-trading-pm — rewrite `codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md`: drop the SPLIT_STAKE table row, restate the firm rule (LST must be accepted as cross-margin at the perp venue or the trade is rejected at preflight), document the dominance argument from 6a `note`, point at Phase 7 for matrix expansion. Cross-link the per-archetype ranker family (Phase 8).
    status: in-progress
  - id: phase-6d-strategy-qg-+-quickmerge
    content: |
      - [ ] [SCRIPT] P0. strategy-service Pass 1 `quality-gates.sh` then `quickmerge.sh "feat: delete SPLIT_STAKE from CARRY_STAKED_BASIS, LST_AS_MARGIN-only" --agent`. Branch: live-defi-rollout (per workspace-manifest.json).
    status: todo
    blocked_by: phase-6c-tests-+-pm-doc-rewrite
  - id: phase-7a-matrix-eth-lst-coverage-audit
    content: |
      - [ ] [HUMAN+AGENT] P0. **Per-LST × per-venue acceptance audit.** Today's `VENUE_COLLATERAL_MATRIX` only has LST-margin rows for DRIFT (jitoSOL + mSOL). The honest universe for CARRY_STAKED_BASIS depends on which (LST, perp_venue) tuples actually accept the LST as cross-margin. Audit: for each ETH-perp venue we run (HYPERLIQUID, ASTER, BINANCE, BYBIT, OKX, DERIBIT, GMX, plus DEXes — Aevo, Lyra-V2, Hyperliquid spot/perp wrapper), check each ETH LST (stETH, wstETH, weETH, rETH, cbETH, ETHx, sfrxETH) AND its wrapped equivalents — which is/are accepted as direct cross-margin (NOT lending collateral, NOT spot only)? Output: rows added to `VENUE_COLLATERAL_MATRIX` with verifiable haircut (cite docs URL or admin-set parameter in the venue's risk-engine UI). For SOL-perp venues, repeat for SOL LSTs (jitoSOL, mSOL, bSOL, jupSOL) across DRIFT + ZETA + Mango — DRIFT already covered.
      - [ ] [HUMAN+AGENT] P1. **BTC LST follow-up (de-prioritised).** No mainstream BTC LST is accepted as direct perp margin today (LBTC / wBTC.b / pumpBTC are still in lending-protocol territory). Add a placeholder row only when a venue ships it.
    status: todo
    note: "Why per-LST and not per-asset: weETH + stETH have very different on-chain rate behaviour and very different acceptance — Aave V3 takes weETH at 72.5% LTV but stETH only at the wstETH wrapper, and Hyperliquid takes neither. Treating 'ETH LSTs' as one set would lose every deployment decision the matrix is supposed to make."
  - id: phase-7b-matrix-haircut-correctness
    content: |
      - [ ] [AGENT] P1. After Phase 7a lands rows: extend `get_collateral_haircut(venue, token)` to be the SSOT for ranking-input weighting in Phase 8. Per (LST, perp_venue), the **effective LST notional** the perp short can lean on = `lst_balance · (1 − haircut)`. The ranker uses this haircut-adjusted notional when computing position sizing — not face notional. Add unit test that asserts `get_collateral_haircut("DRIFT", "JitoSOL") == Decimal("0.10")` and that the ranker's effective notional shrinks proportionally.
    status: todo
    blocked_by: phase-7a-matrix-eth-lst-coverage-audit
  - id: phase-7c-catalog-auto-expand
    content: |
      - [ ] [AGENT] P0. Once Phase 7a/b ship, `_build_carry_staked_basis` automatically picks up the new (LST × perp_venue) rows via `accepted_perp_collateral` — no catalog code change needed. Confirm by re-running the catalog generator and asserting slot count grows by exactly the new matrix rows (one per accepting (LST, perp_venue) tuple). Update `test_target_universe::test_slot_count` floor to track the new total. Drop the `n >= 1` exception in `test_no_archetype_has_fewer_than_three_rows` once CARRY_STAKED_BASIS clears 3 slots organically.
    status: todo
    blocked_by: phase-7b-matrix-haircut-correctness
  - id: phase-8a-base-rank-allocator
    content: |
      - [ ] [AGENT] P0. strategy-service — extract `BaseRankAllocator(StrategyAllocator)` from current `CarryFundingRankAllocator` into `engine/allocators/base_rank_allocator.py`. Shape: pre-rank universe filter (abstract `_eligible_universe(input_series) -> Iterable[Tuple[Hashable, ...]]`), ranking metric (abstract `_score(input_series, key) -> Decimal`), top-N at each tier (config-driven), threshold gate (default 250 bps, config-overridable), tie-break (deterministic — by key tuple). Returns `dict[StrategyInstanceId, Decimal]` weights. Drop the existing 3-stage hierarchical hard-coding from `CarryFundingRankAllocator` so subclasses can pick their own grouping arity (1 stage for single-axis archetypes, 2 stages for coin × venue, 3 stages where present).
    status: todo
    note: "Universe filter is the most important method — it's what differentiates CARRY_STAKED_BASIS (LST × perp_venue accepted-only) from CARRY_BASIS_PERP (coin × venue MVP set). Keep it explicitly archetype-specific."
  - id: phase-8b-seven-subclass-allocators
    content: |
      - [ ] [AGENT] P0. strategy-service — implement 7 subclasses, one per archetype. Each shipped under `engine/allocators/{archetype_lower}_rank_allocator.py`:

        | Subclass                               | Universe filter                                                                              | Ranking metric                                                | Top-N config                          |
        | -------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------- |
        | YieldStakingSimpleRankAllocator        | LSTs in registry × eligible-share-class (ETH/SOL)                                            | `staking_apy_total` (base + EIGEN + seasonal − dust)          | top_n_lsts                            |
        | CarryBasisPerpRankAllocator            | MVP-coin set × all perp venues; spot+perp same venue preferred                               | funding APY (annualised)                                      | top_n_coins, top_n_venues_per_coin    |
        | CarryStakedBasisRankAllocator          | (LST × perp_venue) where `venue_accepts_collateral(perp_venue, lst) is True`                 | `staking_apy_total + funding_apy` (combined, USDC-denominated)| top_n_lsts, top_n_venues_per_lst      |
        | CarryRecursiveStakedRankAllocator      | (LST × lending_protocol × leverage_step) where LTV permits                                   | `leverage · (staking_apy_total − borrow_apy)`                 | top_n_loops                           |
        | CarryBasisDatedRankAllocator           | (CME / Deribit) × (ETH / BTC) × matched expiry                                               | dated future basis APY (expiry-matched)                       | top_n_coins, top_n_venues_per_coin    |
        | YieldRotationLendingRankAllocator      | stable lending protocols × chains                                                            | lending APY (supply-side, net of utilisation cap)             | top_n_protocols                       |
        | ArbitragePriceDispersionRankAllocator  | mode=perp → (venue_pair × coin) on funding spread; mode=dated → (venue_pair × coin × expiry) | signed spread (with directional rule for perp-mode)           | mode, top_n_pairs                     |

        Threshold defaults to 250 bps for every archetype, all per-archetype config-overridable via `share_class_config`. Each subclass gets its own unit-test file with at least: empty-universe fallback, threshold-just-below rejection, threshold-just-above selection, top-N truncation, deterministic tie-break.
    status: todo
    blocked_by: phase-8a-base-rank-allocator
  - id: phase-8c-staking-apy-total-aggregator
    content: |
      - [ ] [AGENT] P1. features-onchain-service — implement `staking_apy_total` aggregator combining base LST APY (already on-chain-derived from `lst_rates` rate-diff per Phase 4a-5) + EIGEN AVS rewards (per `eigenlayer_rewards_handler`) + ETHFI / ANKR / Jito seasonal rewards (per `lst_seasonal_rewards_scheduler`) − dust-realisation slippage (per existing dust loader). Single aggregated feature emitted to `lst_yields` feature group; consumed by both YieldStakingSimpleRankAllocator and CarryStakedBasisRankAllocator. Lives next to current `_process_lst_yields` orchestrator method to preserve batch=live consistency.
    status: todo
    note: "Why aggregated and not summed at allocator-level: the dust component is path-dependent (depends on swap notional and pool depth) and the seasonal component has different schedules per LST — both are not APY-shaped natively, so they need a feature-side conversion. Allocators should consume one APY scalar."
  - id: phase-8d-archetype-ranker-wiring-+-tests
    content: |
      - [ ] [AGENT] P0. strategy-service — wire each `*RankAllocator` to its archetype via `AllocatorArchetype` enum + `share_class_config.allocator_class`. Add `AllocatorArchetype.CARRY_STAKED_BASIS_RANK` (and the other 6) values. Update `test_allocator_registry.py` to assert each archetype has its own allocator class. Smoke-test integration: synthetic `StrategyInputSeries` with 10 candidate slots per archetype, assert top-N gating, threshold gating, tie-break determinism.
    status: todo
    blocked_by: phase-8b-seven-subclass-allocators
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

| Venue capability              | Derived leg sequence                                                          | Net carry (USDC)                           |
| ----------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------ |
| Accepts this LST as margin    | SWAP(USDC→native) → STAKE(native→LST) → TRANSFER(LST→perp venue) → TRADE      | `staking_apy_total + funding_apy − fees`   |
| Does not accept this LST      | Reject slot at preflight (firm rule, post-2026-05-05)                         | n/a                                        |
| ~~SPLIT_STAKE (USDC margin)~~ | ~~Deleted 2026-05-05 — strictly dominated by CARRY_BASIS_PERP / RECURSIVE~~   | ~~< basis-perp at 2x or recursive at L>1~~ |
| ~~Aave borrow USDC~~          | ~~Deleted 2026-05-04 — basis-eroding (borrow APY > basis at E-Mode haircut)~~ | ~~negative~~                               |

So "which slots run at all?" is never a question the user answers — it falls directly out of
`venue_accepts_collateral(perp_venue, lst)`. Catalog enumerates `(lst, perp_venue)` tuples filtered to True. Engine
emits the 4-leg sequence. Tracer drives V2BatchHarness through the full live pipeline; orchestrator allocates by
realised carry.

Today's matrix coverage is sparse for LSTs: only DRIFT (jitoSOL + mSOL, 10% haircut). Phase 7 lands the ETH-LST rows
once each (LST, perp_venue) tuple is verified against venue documentation — that is the unblock for non-trivial slot
counts.

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
- **Why f ∈ {0.5, 0.75}** (superseded 2026-05-05): the f-grid was a SPLIT_STAKE-era artefact. Now that the only allowed
  structure is LST_AS_MARGIN, the LST IS the perp margin — there is no spare USDC bucket to fund margin separately, so
  `f = 1.0` is the only meaningful value. `_STAKED_BASIS_F_VALUES` collapsed to `(Decimal("1.0"),)`.
- **Why SPLIT_STAKE was deleted (2026-05-05)**: SPLIT_STAKE was the case where the venue accepts USDC (not the LST) so
  the user staked half their USDC into LST off-venue and posted the other half at the perp venue as USDC margin. It is
  strictly dominated:
  - vs `CARRY_BASIS_PERP` at 2x size on the unstaked half: SPLIT_STAKE = `f·(staking + funding) + (1−f)·idle_yield`;
    `CARRY_BASIS_PERP @ 2x = 2·funding`. SPLIT_STAKE loses iff `funding > staking·f / (2−f)` — at the f=0.5 case, iff
    `funding > staking/3`, which is overwhelmingly the regime for MVP coins (BTC/ETH/SOL).
  - vs `CARRY_RECURSIVE_STAKED`: when `staking > 3·funding` (the only regime where SPLIT_STAKE would beat BASIS_PERP),
    recursive-staked wins by leverage (it amplifies the staking spread, SPLIT_STAKE doesn't). No funding/staking regime
    exists where SPLIT_STAKE is the right answer; remove it cleanly.
- **Why per-LST × per-venue acceptance, not per-asset (2026-05-05)**: weETH and stETH have different on-chain rate
  behaviour, different EigenLayer-restaking exposure, and very different venue acceptance — Aave V3 takes weETH at 72.5%
  LTV but stETH only via the wstETH wrapper, and Hyperliquid takes neither. Treating "ETH LSTs" as one bucket would lose
  every deployment decision the matrix is supposed to make. Phase 7a audit walks each (LST, perp_venue) tuple
  individually with verifiable haircut citations.
- **Why each archetype has its own ranker (2026-05-05)**: cross-archetype orthogonality detection (e.g. switching
  capital between CARRY_BASIS_PERP and CARRY_STAKED_BASIS based on which is paying more) is a future layer. For MVP,
  each archetype has its own `*RankAllocator` subclass with archetype-specific universe filter + ranking metric +
  top-N + 250 bps threshold. The shared `BaseRankAllocator` enforces the contract; subclasses pick grouping arity (1
  stage for staking-simple, 2 for coin × venue, 3 where present).
- **Batch = live (2026-05-04, reaffirmed 2026-05-05)**: the tracer drives `V2BatchHarness` per slot — engine `on_tick` →
  AtomicInstruction → matching engine → position-balance-monitor → equity rebalance — not a standalone closed-form
  simulator. Already shipped at `strategy-service@6d805e0`. There is no "live-only strategy" or "batch-only strategy";
  99% of the code path is identical, only execution-fill source differs.
