---
name: carry_staked_basis_funding_scan_experiment
title: "carry_staked_basis funding-carry scan — exploratory analysis harness + journal"
status: active
priority: P2
parent_epic: strategy_master
assigned_vm: vm-trading-core
created: 2026-06-16
last_updated: 2026-06-16
locked_by: live-defi-rollout
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
---

# carry_staked_basis funding-carry scan — analysis harness + journal

Exploratory analysis (operator-driven) of the CeFi funding leg of `carry_staked_basis`: scan ~30 perp coins across
venues, rank each day by **net carry**, hold the best, rotate as carry decays, add LST staking where the short venue
accepts the LST as collateral. This plan is the **journal** for the work and the home for its follow-up todos.

Harness: `e2e-testing/scripts/defi/staked_basis_funding_scan.py` (standalone analysis, NOT a strategy engine —
production path is `strategy-service` `CarryStakedBasisRankAllocator` +
`engine/strategies/v2/carry_and_yield/ staked_basis.py`, batch == live). Wired under strategy-service QG per the
peripheral-script rule.

## Net-carry model

    net_carry(coin, venue) = annualised_short_perp_funding(coin, venue)
                           + staking_apy(coin)   IF venue_accepts_collateral(venue, coin's LST)
                           + 0                    otherwise (plain long-spot / short-perp, funding only)

- Rank by **net carry** (best of staking+funding; funding-only where venue constraints necessitate — operator
  2026-06-16). Per coin, pick the venue maximising net carry.
- **Diversification**: where carry ties (within `_FUNDING_TIE_BPS`), equal-weight across all tied coins (least market
  impact — operator 2026-06-16).
- Funding annualised via UAC `perp_funding_cadence.annualise_funding_rate_bps` (per-venue 8h/1h cadence SSOT).
- Collateral eligibility via UAC `venue_collateral.venue_accepts_collateral`. Verified: stETH/wstETH accepted on **Bybit
  / OKX / Deribit**; **not** Binance / Hyperliquid / Aster. SOL LSTs only on Drift (not in the CEX short set) → **SOL is
  funding-only** in this harness.

## Verified data map (2026-06-16, prod central-element-323112)

| Leg                                 | Bucket                                     | Path / derivation                                                                                                                   |
| ----------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Funding (Binance/OKX/Bybit/Deribit) | `market-data-tick-cefi-prd`                | `…/pipeline_mode=batch_tardis/…/data_type=derivative_ticker/<sym>.parquet` → `funding_rate` col (µs ts)                             |
| Funding (Hyperliquid)               | same                                       | `pipeline_mode=batch_hyperliquid_rest` (ms ts)                                                                                      |
| Funding (Aster)                     | **public API**                             | `fapi.asterdex.com/fapi/v1/fundingRate` (no GCS data; pulled live, paginated; 8h)                                                   |
| Staking (Lido stETH, Jito jitoSOL)  | `lst-rates-central-…` (legacy, not `-prd`) | `day=…/venue=<PROTO>/chain=<CHAIN>/…/data_type=lst_rates/*.parquet`; APY derived from `exchange_rate` growth (raw `apy` col is 0.0) |

Coverage windows: funding to 2026-05-24; staking to 2026-04-29; Hyperliquid GCS partial in May. Gaps are **accepted +
documented** (operator 2026-06-16): we don't chase carry where we lack the data (e.g. no staking rate → funding-only).

## Progress log (journal)

- **2026-06-16** — Built harness; verified end-to-end vs real GCS. Confirmed funding lives in `derivative_ticker` (no
  `data_type=funding_rate`); sources split Tardis vs `batch_hyperliquid_rest`; Aster absent from GCS.
- **2026-06-16** — Added collateral-aware net carry + tie-diversification + Aster-via-public-API + PnL/maxDD/Sharpe +
  self-contained Plotly HTML report (`_out/staked_basis_report.html`).
- **2026-06-16** — Data-quality spot-checks vs exchange APIs: GCS funding **values match Binance exactly**; found a
  **one-settlement offset** in `funding_timestamp` pairing → switched to day-mean (offset-robust). Found UTL
  `FUNDING_PERIODS_PER_DAY` disagrees with UAC `perp_funding_cadence` (Aster/Deribit 8× wrong). Both filed →
  `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`.
- **2026-06-16** — Full 2026-YTD run (2026-01-01 → 05-20, 30 coins, 6 venues incl Aster-API): 140 days, venue coverage
  100% except Hyperliquid 85.7% (May GCS gaps). **Avg net carry 12.2% APY · cumulative 4.80% (13.0% annualised) GROSS.**
  Tie-diversification expanded the basket to ~13.2 coins/day, 2.5 rotations/day. Most-held: NEAR / LINK / UNI / AVAX /
  ADA. **Key finding: net carry ≈ funding (12.2% each)** — staking added ~0 to the basket because ETH funding (~5–8%)
  even +stETH (~3%) rarely beats the ~12% alt-funding cluster, so ETH is seldom selected. The "staked" leg only matters
  when ETH funding is competitive; in a high-alt-funding regime it's a tie-breaker, not a driver. `_FUNDING_TIE_BPS=50`
  drives basket size — tunable. Report: `e2e-testing/scripts/defi/_out/staked_basis_report.html` (gitignored, regen).
- **2026-06-16** — Added oracle (hindsight) vs causal (EWMA, no-lookahead) strategies + a 5 bps/leg cost model (2 legs
  spot+perp per |Δweight|; 1-for-1 rotation ≈ 20 bps) + a hysteresis no-trade buffer + per-year metrics + a local data
  cache (instant param sweeps). **Key result (2025-01-01→2026-05-20, hl=10/buffer=5):** the perfect-foresight oracle is
  a mirage net of costs — turnover 0.54/day → 31.8% cumulative drag → net **1.1%** (2026 net **−7.8%**). The causal
  EWMA+buffer trades 0.05/day → net **18.3%** full window, **2026 net 9.8%** (target hit), **2025 net 21.8%** (2025
  funding was very rich). Lesson: optimise carry-capture PER UNIT TURNOVER, not gross carry.
- **2026-06-16** — Aster data availability (API-only; klines/funding backfill, OI/book live-only): funding 2023-07-22,
  **OHLCV 2023-01-01**, mark/index via klines, trades partial, **OI + L2 quotes live-capture-only** (no historical
  endpoint). Tardis CEX schema (trades/book_snapshot_5/derivative_ticker{mark,index,funding,OI}/liquidations) is the
  canonical benchmark → non-Tardis venues canonize their native API INTO those data_types; genesis is per-(venue,
  data_type), not per-venue. **Aster margining = USDC/USDT-only (CROSS); rejects spot-coin AND LST collateral**
  (`venue_collateral.py`) — so Aster is a stablecoin-margined funding-short only; no same-venue cash-and-carry, no
  staking leg. ETH staked-basis works on Bybit/OKX/Deribit (stETH/wstETH collateral). Filed to the Aster todo in
  `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`.
- **2026-06-16** — Deribit FIX: its stored `funding_rate` is the 8h figure (≈ API interest_8h), annualise at 8h not 1h
  (was 8× over) + ±200% winsor. Switched returns to **LINEAR (non-compounded)** — daily interest summed, mean×365
  annualisation (operator; matches UAC linear convention). Split into **3 strategies** (staked basis / funding
  dispersion = long low/neg-funding perp + short high-funding perp / pure basis no-staking) each oracle+causal, +
  **capital-efficiency** (spot-collateral venues ≈1, cash-margin HL/Aster = 1/(1+max_move), per-asset BTC .20/ETH
  .25/alt .60/small .80) + **min-carry floor 3%** + **ensemble** (best structure per coin) + **cash floor** (lend USDT
  @4% when nothing clears 3%). HTML: side legend + strategy-named end-labels.
- **2026-06-16** — **Full 2022→2026 run** (108k coin·venue·day points, Deribit-fixed, linear, efficiency-adjusted).
  **Causal NET ann by year (ensemble = best-of-all-structures):** 2022 **14.9%** · 2023 **23.5%** · 2024 **31.0%** ·
  2025 **13.9%** · 2026 **9.3%**. Full-window ensemble net **19.8%**, beating every single strategy (dispersion 15.4,
  pure 13.9, staked 12.0) — the structures are complementary and **ETH staked-basis earns its place in the meta-book**
  (it's the ~zero-turnover backbone; dispersion adds spread alpha; pure adds breadth). **2022 bear ≈ 2026 bear
  confirmed** — both far below the 2023-24 bull (funding compresses in bears; 2026 at 9.3% is even tighter than 2022).
  **Cash floor never triggered (0/1600 days)** — across all structures the best opportunity always cleared 3%, so the
  USDT-lending fallback is a dormant safety net for this period. Why ETH looked weak in the OLD combined book: it's a
  relative-ranking + funding-cap + efficiency-blind artifact, not a weak carry — resolved by the ensemble.

## Strategies 4 + 5 (EigenLayer restaking) — design + data status (operator design 2026-06-16)

4. **Restaking yield (EtherFi weETH)** — base staking + EigenLayer rewards (+ seasonal), **LONG-ONLY** (no venue takes
   weETH/eETH as collateral → not market-neutral; it's just the yield on weETH). **Data: weETH EXISTS** in
   `lst-rates-central-…/venue=ETHERFI` (verified 2026-06-16); EigenLayer `eigen_apy_bps` flows via features-service
   `onchain/engine/staking_apy_total.py` + `collectors/chain_event_scanners.py` but its GCS path/cadence is UNCONFIRMED
   (likely `features-delta-one-defi-*`; weekly) → verify before building. Alt: Lido stETH (already wired).
5. **Recursive/leveraged restaking** — loop weETH on a lending market: borrow against weETH → buy more weETH → repeat.
   Yield ≈ `(staking + restaking − borrow_rate) × leverage`, `leverage = 1/(1 − maxLTV)` (high in Aave e-mode), with a
   ~2% basis-move haircut. **Data: BLOCKED — no Aave (Ethereum) lending/borrow rates in GCS** (verified:
   `lending_indices` holds only Solana Kamino/Solend). Need Aave rate backfill (or run the loop on a Solana LST via
   Kamino/Solend). Code refs: `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py`,
   `deployment-api/models/recursive_borrow.py`, DeFi `RECURSIVE_LOOP` error codes; loop math + e-mode maxLTV to source
   from codex strategy docs.

- **2026-06-16** — Replaced the rank-buffer with an **economic rotation gate** (operator): swap a held name only if the
  candidate's carry beats it by > `swap_bps = 4·cost_bps·365/hold_days` (≈ 5.2% for 5 bps/leg + 14-day hold; scales with
  cost). A 1% edge over 2 weeks ≈ 4 bps < 20 bps round-trip → don't trade; ~5%+ does. **Big win — cut churn, lifted net
  everywhere.** Full-window ensemble net **19.8% → 21.7%**; **2026 dispersion 0.8% → 5.0%** (turnover 0.282 →
  0.171/day), 2026 ensemble **9.3% → 10.7%**. Ensemble causal net by year: 2022 **16.3%** · 2023 **26.0%** · 2024
  **33.9%** · 2025 **14.8%** · 2026 **10.7%**.
- **2026-06-16** — Dispersion diagnosis (why 2026 was thin): (1) 2026 cross-venue spreads HALVED (median 0.0%, p95 18%
  vs full-window 42%) — venues largely agree on funding in the bear; (2) only **41% of coin-days have ≥2 venues** (59%
  single-venue → no dispersion); (3) **OKX-SWAP funding is suspiciously sparse — only 9 coins captured in 2026** (vs
  Binance/Bybit 19, Aster 29) → likely an OKX perp-funding backfill gap (OKX lists 100s of perps). Filed below.

## Open data gaps (file/verify)

- [ ] [DATA] P2. OKX-SWAP perp funding sparse — only ~9 coins captured in 2026 (expected ~19+). Verify the OKX
      derivative_ticker backfill universe in MTDS; likely a coverage gap limiting cross-venue dispersion. **Repo:
      market-tick-data-service.**

- **2026-06-16** — Confirmed returns are **LINEAR** (cumulative sum, mean×365 ann) not compounded (operator check):
  ensemble-causal +21.7%/yr × 4.38yr → equity 1.95 (matches chart; compound would be 2.37). Exposed efficiency knobs:
  `--spot-haircut` `--dispersion-eff` (1.0 = clean 2× perp-perp) `--max-move-scale` (cash-margin discount sensitivity).
  Aster/HL cash-margin confirmed: 100% capital deployed but funding earned on only `S=C/(1+max_move)` of base (the
  margin set-aside IS the haircut) → eff=1/(1+max_move); Aster can do pure-basis (discounted) + dispersion (full,
  broadest 29-coin coverage), NOT staked basis.
- **2026-06-16** — **SHARE-CLASS axis gap (operator):** the whole harness is **USD share class** (market-neutral, USDC
  capital, USD % returns, every position shorts a perp). The **ETH-share-class** family is NOT modelled — start with
  ETH, want more ETH, keep the ETH exposure (no perp hedge): (a) **staked ETH** = hold stETH/weETH, earn staking +
  EigenLayer restaking + seasonal, measured IN ETH; (b) **recursive staked ETH** = borrow ETH against LST → stake →
  loop, returns in ETH ≈ `(staking+restaking+eigen − ETH_borrow) × 1/(1−maxLTV)` (Aave e-mode). These ARE strategies 4/5
  but **ETH-denominated + NOT market-neutral** — a distinct `share_class=ETH` track. Data: weETH/stETH rates EXIST;
  eigen path unconfirmed; **ETH borrow rate = the same Aave gap** (no Aave/Ethereum lending in GCS). Also a SOL-share-
  class analogue (JitoSOL/mSOL + Kamino/Solend, which DO exist in GCS).

## Open todos / next steps (added 2026-06-16)

- [ ] [STRATEGY] P2. Add a `share_class` axis (USD / ETH / SOL / BTC). ETH-share-class strategies: staked-ETH yield
      (long LST, no hedge, returns in ETH) + recursive staked-ETH (leveraged loop). **Repo: e2e-testing harness →
      strategy-service.** Blocked-for-recursive: Aave ETH borrow rate (see Aave gap).
- [ ] [DATA] P2. Backfill Aave (Ethereum) supply/borrow rates + maxLTV/e-mode into GCS — unblocks the recursive loop
      (strategy 5, both USD-cash-floor and ETH-borrow) and the real cash-floor rate. Only Solana (Kamino/Solend) exists
      today. **Repo: market-tick-data-service + deployment-service.**
- **2026-06-16** — 🟢 **VM RUNNING — Aave + lending-indices backfill** `mtds-lending-indices-20260616-225256`
  (e2-standard-4, asia-northeast1-c). Verdict from investigation: Aave V3 is a **config-run, not new code** — `aave_v3`
  is first in the MTDS handler's `_DEFAULT_PROTOCOLS` (subgraph + RPC fallback + parser + maxLTV/e-mode all wired).
  Launched `launch-mtds-lending-indices-backfill-vm.sh 2022-01-01 2026-06-16` (all protocols: aave_v3/spark/compound_v3/
  kamino/solend/marginfi). Writes to the **canonical bucket `lending-indices-central-element-323112`** (NEW v9 path, not
  the legacy `market-data-tick-defi/lending_indices/`). Auto-shuts-down on completion (~3–6h); monitor armed. Unblocks:
  recursive loops (USD + ETH), the real Aave-USDT cash-floor rate, ETH-borrow-rate for the ETH-share-class recursive
  strategy.
- **2026-06-16** — OKX historical funding: public `funding-rate-history` API only serves **~3 months** (paginating to
  2023 = empty), so it's NOT a deep-history backfill (unlike Aster). The real fix is the **Tardis OKX backfill
  universe** (only 9 coins captured) — kept as the OKX data todo, not an API path.
- **2026-06-16** — ⚠️ **lending-indices bucket env-split debt (operator-flagged)**: canonical = env-split
  `lending-indices-${ENV_SHORT}-${PID}` (`resolve_bucket_name(kind="lending-indices")` → `lending-indices-prd-…`,
  cloud-providers.yaml:187), BUT the WRITER still lands in the **legacy un-suffixed `lending-indices-central-…`** (data
  back to 2022-11; `-prd` has only `_migration/`) — IDENTICAL to the `lst-rates` debt. So the Aave backfill VM is
  writing to the legacy bucket too. Needs (a) writer-env fix so future writes resolve to `-prd`, (b) migrate existing
  legacy data → `-prd`. Owned by `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (same class as
  lst-rates). The harness reads the legacy bucket for now (as it does for lst-rates).
- **2026-06-16** — Harness cleaned to **0 basedpyright / ruff-green** under the e2e QG config (deleted 2 dead EWMA fns,
  annotated `client: StorageClient`, knob constants → `globals()`); **e2e quality-gates.sh exit 0**. Quickmerge
  **BLOCKED on foreign UAC WIP** (`config_versioning.py` — another agent's uncommitted change; not mine, won't touch).
  Harness stays in working tree (safe); ship once UAC clean (more additions pending anyway).
- **2026-06-16** — **Prod-fidelity investigation (3 agents) — design + decisions for the backtest extension:**
  - **GAS** (separate from execution fees): prod has `execution-service/.../services/gas_cost_model.py` —
    `DEFAULT_GAS_ESTIMATES` (SWAP 200k, SWAP_MULTI_HOP 350k, STAKE 150k, UNSTAKE 200k, BORROW 300k, REPAY 200k, LEND
    200k, WITHDRAW 250k, TRANSFER_ERC20 65k, TRANSFER_ETH 21k, FLASH_BORROW/REPAY 100k, WRAP 50k, ATOMIC_BUNDLE_BASE
    50k; CLOB/CEX TRADE = 0) × L2 multiplier (Op/Base/Arb 0.6, Poly/BSC/Avax 0.8, Linea 0.5).
    `gas_cost_usd = gas_units × gas_price × native_price`. **Gas-price DATA in GCS** (`gas_fees/chain_id=…/date=…/`,
    schema base_fee_gwei + priority_fee_p25/50/75 + blob_base_fee; ETH 2020→, SOL 2021→, 14 EVM chains). → backtest
    computes gas from EXISTING data + the prod gas-unit table.
  - **WALLET / treasury-vs-trading** (`codex/04-architecture/wallet-hierarchy-and-capital-flow.md`): keyed by
    **share_class**, DeFi **20% treasury / 80% hot-per-strategy** (CeFi 0/100), `WalletMappingConfig` reserve_pct 20% +
    min/max bands (10%/30%); rebalance automation **NOT yet shipped** (Phase E.3) → the rebalancing sim is a genuine
    prototype of unshipped logic. Capital map = **4-leg AtomicInstruction** (SWAP usdc→eth → STAKE eth→LST → TRANSFER
    LST→perp venue → TRADE short perp) + passive accrual (FUNDING_ACCRUAL + STAKING_REWARD). Ledger taxonomy = UAC
    `canonical.crosscutting.ledger` (37 EventTypes incl DEPOSIT/WITHDRAWAL_TO_BANK/TRANSFER/CUSTODY_MOVE +
    FUNDING_ACCRUAL/STAKING_REWARD/LENDING_INTEREST); client-funds-isolation HARD RULE (single client_id per transfer).
  - **SLIPPAGE — historical vs static (prod intent):** (1) **DEX swap = HISTORICAL** — `slippage_cost_model.py` +
    `amm.py` (Uniswap V2/V3 math) + historical pool depth (`dex_pools` bucket) → `price_impact_bps` from depth (same
    snapshot as the prod batch replay). (2) **Staking LST premium = STATIC** (~0–50 bps; secondary-market premium NOT
    captured — only the `exchange_rate`). (3) **Lending/borrow rate = HISTORICAL via the Aave IRM curve** (borrow rate
    moves with utilisation: `base + slope1·U + slope2·max(0,U−U_opt)`; slopes + `utilisation_rate` are in
    lending_indices — the Aave backfill VM is filling the ETH utilisation gap now). So **use historical where data
    exists (DEX depth, utilisation), static only for the LST secondary premium.**
- **2026-06-16** — Aave/lending backfill VM **completed rc=0** (self-deleted) but **PARTIAL** — hit GCS/subgraph **429
  rate limits** (~1628 results; manifest-consolidator-stale at end). Aave V3 wrote for Arbitrum/Avalanche/Base; **ETH
  coverage spotty** (absent on latest day). Landed in the **legacy un-suffixed `lending-indices-central-…`** with the
  **old `category=defi`** path key (not `asset_group=`) — confirms BOTH the env-split debt AND a category-vocab debt.
  Lending bucket now spans 1259 days (2022-11-01 → 2026-05-28). **Recursive-ETH + real Aave-USDT cash-floor still need a
  COMPLETE Aave-Ethereum re-run** (narrower per-run scope or a paid subgraph key to dodge 429s) + a consolidator run.
  Todos below.

## Open data gaps (added 2026-06-16, part 2)

- [ ] [DATA] P2. **Complete Aave-Ethereum lending backfill** — first run was 429-throttled (partial; ETH spotty). Re-run
      scoped to `aave_v3 ETHEREUM` only (don't split the subgraph budget across all protocols/chains) or use a paid
      TheGraph key; then run the lending-indices manifest consolidator (it was stale). **Repo:
      market-tick-data-service + deployment-service.** Owner:
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`.
- [ ] [DATA] P3. lending-indices writer emits the **legacy `category=defi` path key** (not canonical `asset_group=`) +
      the legacy un-suffixed bucket — fix both to canonical v9. **Repo: market-tick-data-service.**
- **2026-06-16** — **Treasury/Trading rebalancing sim BUILT** (`--simulate-treasury`, prototypes the unshipped prod
  rebalancer). Models: target 20% treasury (earns cash `cash_apy`) / 80% trading (earns ensemble carry); bands 10–30%; a
  withdrawal shock funded from treasury FIRST, only unwinding trading if it exceeds the buffer; rebalance cost =
  `2·cost_bps` rotation + `rebalance_slip_bps` slippage on moved notional + fixed `$rebalance_gas_usd` gas (anchored by
  `--capital-usd`). **Linear** (operator). **Result (2022→2026, ensemble):** raw 100%-deployed **21.7% ann** →
  treasury-managed **18.1% ann** — the 20% liquidity buffer costs **~3.6%/yr**, almost ALL of it buffer-idle drag (20%
  parked in 4% cash vs 22% carry); rebalance/unwind cost ~0.04%. A **10% withdrawal is fully covered by the 20% buffer
  (no unwind, ~0 cost)**; a **25% withdrawal** exceeds the buffer by 5% → forces a 5% unwind, still ~0.05%. Knobs:
  `--treasury-pct --withdraw-pct --withdraw-interval-days --capital-usd --rebalance-gas-usd --rebalance-slip-bps`.
- **2026-06-16** — **Capital-movement map** (from prod, for fidelity): USDC **DEPOSIT** → treasury (20%) / trading (80%
  TRANSFER treasury→hot) → the 4-leg `AtomicInstruction`: **SWAP** usdc→eth → **STAKE** eth→LST → **TRANSFER** LST→perp
  venue (collateral) → **TRADE** short perp; passive **FUNDING_ACCRUAL + STAKING_REWARD** accrue; on exit unwind (close
  perp → unstake → swap→usdc) → **WITHDRAWAL_TO_BANK**. Each step is a UAC `ledger` EventType (37-value closed set);
  every TRANSFER/CUSTODY_MOVE carries a single `client_id` (funds-isolation HARD RULE). The sim models this at the
  portfolio level (start→deploy→accrue→withdraw); per-leg event ledger = next fidelity.
- **2026-06-16** — Gas + slippage = **bundled into the calibrated rebalance cost (v1)** — rotation + static slippage +
  fixed gas. Higher fidelity (next): per-action gas from prod `gas_cost_model.DEFAULT_GAS_ESTIMATES` × GCS gas-price
  data (`gas_fees/`); **historical** DEX slippage from `dex_pools` depth via prod `slippage_cost_model`/`amm.py`; Aave
  borrow-rate slippage from the IRM utilisation curve (needs the completed Aave-ETH backfill). Todos below.
- **2026-06-16** — Harness **ruff + basedpyright clean, e2e QG exit 0**. Quickmerge pending foreign UAC WIP clear.

## Open todos / next steps (added 2026-06-16, part 3)

- [ ] [STRATEGY] P3. Per-action GAS layer: charge gas per on-chain leg (SWAP 200k / STAKE 150k / TRANSFER 65k / BORROW
      300k from prod `gas_cost_model.DEFAULT_GAS_ESTIMATES`) × historical gas-price (`gas_fees/chain_id=…`) × native
      price. **Repo: e2e-testing harness (reuse execution-service gas_cost_model constants).**
- [ ] [STRATEGY] P3. HISTORICAL slippage: DEX swap from `dex_pools` depth (prod `slippage_cost_model` + `amm.py`),
      borrow-rate from Aave IRM utilisation curve (`base + slope1·U + slope2·max(0,U−U_opt)`); keep LST secondary
      premium static (~0–50 bps, no data). **Repo: e2e-testing harness.**
- [ ] [STRATEGY] P3. Per-leg capital-movement event ledger (DEPOSIT→SWAP→STAKE→TRANSFER→TRADE→accrual→unwind→WITHDRAW)
      using UAC `canonical.crosscutting.ledger` EventTypes, for a faithful capital-flow trace. **Repo: e2e-testing.**
- **2026-06-16** — **Harness SHIPPED under QG**: baseline `e2e-testing@a2b6a44` (orphan-WIP inheritance, promoted) +
  treasury-rebalancing-sim delta `e2e-testing@653da76` landed on live-defi-rollout (ruff + import-patterns +
  basedpyright + full QG green; Tier-C drain → staging ≤30min). Autonomous run complete.
- **2026-06-16** — Operator follow-ups answered (data-verified):
  - **GAS data FOUND**: `gas-fees-central-element-323112` (legacy un-suffixed → same env-split debt; `-prd` exists),
    path `gas_fees/chain_id=<id>/date=…/` schema base_fee_gwei + priority_fee_p25/50/75 + blob_base_fee. **Chains:
    Ethereum(1), Solana, + Op/BSC/Poly/Arb/Avax/Base/Linea**, coverage ≥2024-05. → per-action gas layer can use REAL
    historical ETH+SOL gas prices (no assumption needed).
  - **429 root cause**: GCS **per-object mutation rate limit** on the hot per-VM manifest shard
    (`_index/per_vm/mtds-…parquet` — written every batch; GCS caps ~1 mutation/sec/object) + the **consolidator ~17 days
    stale** (Cloud Run job down for this bucket). Both throttled the Aave backfill → partial. Fix: debounce/ batch the
    per-VM shard writes (or unique per-batch objects) + run the lending-indices manifest consolidator.
  - **Recursive basis = ATOMIC bundle (confirmed)**: prod `AtomicInstruction` (multi-leg + compensation_policy) +
    `FLASH_BORROW`/`FLASH_REPAY` + `ATOMIC_BUNDLE_BASE` gas + 7 `RECURSIVE_LOOP` DeFi error codes. The loop must be one
    atomic tx (flash-loan the borrow→stake→re-borrow) or be liquidatable mid-loop. Recursive strategy models the
    atomic-bundle gas.
  - **Margin-call → treasury (dual-purpose buffer)**: for a DELTA-NEUTRAL basis the hedge absorbs asset moves, so margin
    calls bite mainly on **cash-margin venues (Aster/HL)** where the off-venue spot can't auto-offset the perp loss →
    treasury top-up extends the effective margin buffer beyond the budgeted `max_move` (→ tighter margin / higher eff,
    treasury covers tail moves). Continuous monitor needs the price-MtM layer (next fidelity); a margin-shock coverage
    stat is added to the sim now.
- **2026-06-17** — **Margin-call backstop SHIPPED** (`e2e-testing@d395824`): the treasury is dual-purpose — the 20%
  buffer also funds a margin top-up. Sim reports it: with only ~8% of the ensemble book on cash-margin venues (Aster/HL,
  no on-venue spot offset) and the rest hedge-protected delta-neutral, the treasury covers ~any tail move on that slice.
  Continuous margin monitor needs the price-MtM layer (next fidelity). **All harness work shipped + journaled;
  autonomous run closed.**
- **2026-06-17** — **SEQUENCING (operator):** the remaining next-fidelity todos (per-action gas · historical DEX/IRM
  slippage · per-leg capital-movement ledger · complete Aave-ETH backfill · OKX Tardis universe · ETH/SOL share-class
  staked+recursive · weETH restaking) are **gated on the v9 data-migration / env-split / category= cleanup completing**
  — resume them once that lands. In the meantime built the live/paper emitter (below).
- **2026-06-17** — **Live/paper positioning-instruction emitter BUILT** (`--emit-instructions [--as-of DATE]`): runs the
  SAME causal ensemble model on the latest data and emits the **ideal target book** as instructions — per position: coin
  · structure · weight · notional (= weight × deployable, treasury reserved) · net/funding/staking carry · short(/long)
  venue · and the **leg sequence** per structure (spot_same_venue: BUY_SPOT+SHORT_PERP; staked_basis:
  BUY_SPOT→STAKE→TRANSFER→SHORT_PERP; cash_margin: BUY_SPOT off-venue+POST_MARGIN(USDC×eff)+SHORT_PERP; dispersion:
  LONG_PERP+SHORT_PERP) → printed + `positioning_instructions.json`. **Batch==live by construction**: same GCS
  data/schemas (CoinDay/panel) + same decision logic (`_ewma_threshold_weights`/efficiency/collateral) as the backtest;
  only difference is it emits today's book vs accumulating PnL. Paper/live EXECUTION (fills/PnL) → strategy-service
  `colocated_engine` (run-paper.sh); the emitter is the signal/target-book stage.
- **2026-06-17** — Emitter delta is **QG-green + working-tree-safe**, quickmerge transiently BLOCKED on foreign dep WIP
  (UAC `venue_collateral.py` + execution-service dispersion trace — not mine). Ships on next clean-dep window /
  orphan-WIP inheritance (same path the baseline a2b6a44 took). All code verified (ruff+imports+basedpyright+QG); no
  force-merge through foreign dirty deps.
- **2026-06-17** — **Per-variant emitter + withdrawal/deposit-triggered rebalancing** (operator: "can we simulate
  withdrawals AND deposits to trigger the rebalance, for live and backtest?"). Three deltas:
  1. **Per-variant books** — `--emit-instructions` now emits one IDEAL target book PER strategy variant (staked basis /
     funding dispersion / pure basis / ensemble), not just the ensemble. Each writes
     `positioning_instructions_<variant>.json` + a combined `positioning_instructions_all.json`. Verified on $100k
     (as_of 2026-05-22, latest day with data mid-v9-migration): staked-basis = ETH 100% @ $80k (Lido stETH + OKX short,
     8.3%); dispersion/pure/ensemble = 5×$16k. Each $100k → $20k treasury + $80k deployable.
  2. **Deposit shock in the backtest treasury sim** — withdrawals already existed; added `--deposit-pct` /
     `--deposit-interval-days`. A deposit lands in the treasury wallet (the on-chain entry point) → pushes the treasury
     fraction above the 30% band → the existing rebalance deploys the surplus into the book. Sim line now reports
     `Rebalances / withdrawals / deposits`. Verified: `--withdraw-pct 0.10 --deposit-pct 0.15` → 2 / 1 / 1.
  3. **Flow-triggered rebalance INSTRUCTIONS in the live emitter** — `--flow-usd <signed>` (negative=withdrawal,
     positive=deposit) emits the actual rebalance legs for the ensemble (live) book, same wallet logic as the backtest
     sim: treasury-first on withdrawals (unwind pro-rata only if the buffer is exhausted), deploy-surplus on deposits,
     then resize every position back to 20/80 on the new capital → `rebalance_instructions.json`. Verified on $100k:
     `-$10k` covered by treasury (no unwind, positions trim to $14.4k on $90k); `+$30k` deploys $24k surplus (+$4.8k
     each on $130k); `-$50k` exhausts the $20k buffer → $30k pro-rata unwind, positions $16k→$8k on $50k. Batch==live:
     the live rebalance reuses the same 20/80 band + treasury-first rule the backtest runs each shock.
  - **Code quality**: refactored the emitter's instruction structures to TypedDicts (`Position`/`Instructions`/
    `Rebalance`/`ResizeRow`/`FlowAction`) — removed the `dict[str, object]` `reportUnknown` errors AND the 5 banned
    `# type: ignore` comments. ruff clean; basedpyright on the emitter region clean (the residual 124 file-level errors
    are the pre-existing pandas/requests/argparse-`Any` baseline in the committed scan body — QG type-checks
    `tests/unit/`, not `scripts/`, so they are ungated and pre-date this work; not introduced here).
- **2026-06-17** — Above three deltas **LANDED on LDR** at `e2e-testing@fc5cd0a` (rebased onto the LDR tip after a
  push-time race; file change intact). QG-green (sentinel d982ce0), ruff clean, no `# type: ignore`.
- **2026-06-17** — **Daily positioning guide (manual-execution helper)** (operator: "guide me on what to do if I execute
  manually"). `--target-diff` dumps the TRADES (delta between the persisted CURRENT book and the TARGET ensemble book) +
  the EXPECTED FINAL position (== target) — first run from flat = the trades to put on RIGHT NOW (all OPENs). Trade
  actions: OPEN / CLOSE / INCREASE / REDUCE / SWITCH (coin held but structure-or-venue changed → close old + open new).
  `--apply` SIMULATES execution — persists the target as the new current book (`--state-file`, default
  `<out>/current_book.json`), so day-over-day the delta is genuinely vs yesterday's fill ("target == final": after
  apply, current = the final = the target). Verified: flat→5 OPENs; apply; re-run→NO TRADES (current==target); capital
  100k→250k→5 INCREASEs. Writes `daily_trades.json`. **Cron**: `scripts/defi/daily_positioning_dump.sh` (runs
  `--target-diff --apply` over a rolling 120d window, dumps to `~/.defi_positioning/daily_trades_<DATE>.log` + advances
  state) installed on the human-planning VM crontab at `5 0 * * *` UTC. Batch==live: same ensemble model/data/decisions
  as the backtest — the live guide IS the backtest allocator evaluated on the latest day. Strict-typed
  (`Trade`/`BookState` TypedDicts, `cast` not `# type: ignore`); ruff clean. **Shipping** via watcher (1 foreign dirty
  dep — UAC `venue_collateral.py`).
- **2026-06-17** — **Live/paper multi-venue expansion (operator) — researched + documented**. Probed public perp funding
  endpoints: **11 venues reachable no-auth** (the 6 backtest venues + Gate/KuCoin/Bitget/Kraken-Futures/MEXC). Locked
  each venue's funding field/interval/symbol/sign quirks (HL+Kraken **hourly**; Kraken `fundingRate÷markPrice`
  absolute→relative; Deribit stored 8h-figure; Gate/MEXC expose interval; KuCoin/Kraken `XBT`=BTC; OKX/Deribit/MEXC
  per-coin, rest all-symbols). Wrote the integration SSOT **`codex/02-data/carry-venue-live-integration-reference.md`**
  covering funding venues + LST **staking** (Lido/Jito/RocketPool/Coinbase/ether.fi-weETH+EigenLayer/Marinade) +
  **Aave** lending (cash floor + recursive borrow leg) + the conservative-cash-margin default + how-to-add-a-venue.
  Filed the `--live` build + UAC-registry (cadence/collateral) + staking/lending-source + credentialed-venue TODOs under
  '## Live/paper multi-venue expansion'. batch==live: live snapshot feeds the same FundingPoint→panel→emitter. Code
  build (`--live` mode) is the next step, spec'd by the doc.
- **2026-06-17** — **DEX-perp venues corrected (operator)**: dYdX v4 + Vertex are **PUBLIC** (not credentialed) — dYdX
  `indexer.dydx.trade/v4/perpetualMarkets` (`nextFundingRate`, hourly) verified; Vertex
  `gateway.prod`/`archive.prod.vertexprotocol.com` resolves (the `api.vertexprotocol.com` I'd have used is a stale
  Vercel 404). **Drift**: we HOLD creds (`solana-paper-keypair-private-key`+`solana-wallet-address`); its public Data
  API **403s this VM** (geo/Cloudflare) + authed 401s → wire the **Solana-RPC on-chain** path. Drift **takes
  jitoSOL/mSOL as margin → unlocks SOL staked-basis** (only venue). Already in UAC (`venue_mapping`/`chain_env`). Added
  all three + the **live/paper history carve-out** (no funding history → WARN + use current snapshot + available spot
  history, never block; backtest still needs history) to the spec doc + todos.
- **2026-06-17** — **`--live` multi-venue paper path + Drift wired** (`e2e-testing@6e2ffb8`). `--live` ranks on the
  CURRENT funding snapshot (no history — operator carve-out) across **14 venues**: 11 CeFi/public-perp + dYdX + Vertex +
  Drift. Verified live: **13 venues / 446 funding points**, **SOL staked_basis short DRIFT** in the book (Drift's
  jitoSOL/mSOL collateral unlocks it — the goal). Vertex warn-skips (this VM's IP is TLS-reset by Vertex's edge — host
  issue, not code). Uses oracle-of-now weights on the single snapshot; conservative LST APR default (ETH 3% / SOL 7%) +
  warn (live LST source still a TODO). New venues default to cash-margin (conservative). Coins 30→40. **Drift dependency
  resolution (KEY)**: driftpy's metadata exact-pins ~25 common libs (urllib3==1.26.13 / websockets==13 / zstandard==0.18
  / solders<0.27 / numpy<2 / psutil / aiosignal …) that **cannot be uv-resolved in any shared lock** with the fleet +
  execution-service — BUT it **RUNS fine on the fleet versions** (Drift funding read verified on solders 0.27.1 + numpy
  2.2.6 + the trio). So it lives in an **ISOLATED venv** (`scripts/defi/install_driftpy_venv.sh` → ~/.drift-venv,
  driftpy's own pins) and the harness shells out to `drift_funding_reader.py` there via Helius RPC (ibkr-gateway-infra
  pattern) — NOT a flat dep. execution-service already anticipated this (lazy-loads driftpy in
  `defi_execution/protocols/drift.py`, deliberately undeclared). Production MTDS/execution adapters follow the same
  isolated pattern (filed below).
- **2026-06-17** — **Liquidity layer (ADV + market width)** (operator; `e2e-testing@c973985`). `--live` now snapshots
  per-coin **24h USD volume (ADV) + half-spread** (deepest of Bybit/Gate, one call each) and: (1) **penalises carry by
  the annualised round-trip spread cost** (`2·half_spread·(365/hold)`) so a wide-spread coin must clear a higher funding
  bar — don't chase a thin coin's funding into the spread; (2) **ADV-caps position size** (`--adv-cap-pct`, default 0.5%
  of ADV) → liquidity-scaled sizing; (3) shows `[ADV $Xm · spread Ybps]` per position. Verified live: 39/40 coins; ETH
  staked-basis concentrates in the $2.36B/0.0bps book; STX ADV-capped $16k→$8.7k on its $2M ADV. Knobs
  `--no-liquidity --spread-cost-mult --adv-cap-pct`. **Single-snapshot for paper**; for the **BACKTEST we assume
  liquidity constant** (the snapshot, documented) — e2e-only. Production = a real MDPS ADV/market-width feature (filed).
- **2026-06-17** — **Two `--live` correctness fixes (operator caught the symptom — LDO showing 91%)**. (1)
  **Hourly-venue annualisation was noise**: Kraken/HL/dYdX/Drift settle HOURLY, and `--live` was annualising a SINGLE
  current hourly print x8760. Measured LDO on Kraken: latest hour **+70%/yr** vs trailing-24h mean **-4.8%/yr** vs 7d
  **-14.6%/yr** (the 8 last hourly prints swung -28%..+70%). So it was never a real rate — a single-hour artifact (NOT
  mean-reversion — it never moved; I wrongly asserted that before measuring). FIX: `_live_funding_hourly_trailing` pulls
  each hourly venue's **trailing-24h funding history** (Kraken `historicalfundingrates` last 24 · HL `fundingHistory`
  windowed · dYdX `historicalFunding?limit=24`) and averages — Drift already used `last24h_avg`. 8h venues keep their
  single settlement (already a smoothed period rate; 8h smoothing is a possible refinement). (2) **Single-snapshot
  perp-perp DISPERSION excluded from the LIVE ensemble by default** (`--include-dispersion-live` to keep): across 13
  venues the max-min funding gap is dominated by the thinnest/most-extreme venue (TON 201% short DRIFT/long DYDX) and
  doesn't persist — staked/pure/cash are the trustworthy live signal; the backtest keeps dispersion (it has the
  time-series to verify persistence). Clean live ensemble now = cash-margin funding shorts on high-funding alts (14-23%,
  smoothed) + ETH staked-basis (9.4%) as a variant. **Integration note for the main system**: production funding
  features must carry a **trailing/realised window** per venue cadence (never a single instantaneous print annualised),
  and dispersion needs **per-(coin,venue) liquidity** before it's tradeable — both belong in the MDPS feature.
- **2026-06-17** — **Unified execution-cost model + carry-tilt x liquidity allocation + dynamic universe** (operator;
  `e2e-testing@494add2`). THREE linked changes: (1) **Per-leg cost = fixed cost_bps (fee+base slippage, BTC/ETH-tight) +
  the coin's half-spread (market width)** — folded into BOTH the realised cost (`_run_strategy`) AND the rotation gate
  (`_ewma_threshold_weights`): a flip = exit weakest (2 legs) + enter candidate (2 legs),
  `swap(weak->cand) = [2*(cost+spread_weak) + 2*(cost+spread_cand)]*365/hold`, so a WIDE-SPREAD candidate needs MORE
  carry edge to rotate in (was a separate live-only carry haircut, absent from the backtest + the gate — now unified,
  and the live ADV/spread snapshot is backfilled as a CONSTANT for the backtest). (2) **Allocation = carry-tilt x
  liquidity blend** (`_blend_weights`, shared by oracle + causal):
  `weight ~ carry^tilt_power x min(1,ADV/$100M)^liq_damp_power` — tilt toward bigger funding (tilt=1 proportional),
  dampened toward liquid coins (damp=0.5 sqrt/gentle); the two count against each other so for similar-carry candidates
  ADV decides the split. Replaces flat equal-weight. Knobs `--carry-tilt-power --liq-damp-power`. (3) **Dynamic
  universe: top_n 5->20, min-carry 3%->5%, cash floor 4%->4.5%** — hold up to 20 coins clearing 5%; below 5% lend USDC
  (~4.5% RV, no fees/delta). Verified live: 20-position ensemble, WLD (23.7%/$290M)->w0.163 vs TIA (21.9%/$16M)->w0.061
  (liquidity dampening visible). **ARCHITECTURE (operator confirmed)**: the carry-tilt x liquidity x cost logic runs
  INSIDE each archetype independently (staked basis / dispersion / pure basis each decide their own positioning via
  their own `_select_weights`); the **ensemble is a separate re-weight layer on top**. Both `--emit-instructions`
  (paper) AND the backtest emit EACH individual strategy + the ensemble. We roll out the archetypes as SEPARATE
  strategies; a portfolio-allocation layer (the ensemble/meta) is separate. **Integration note for main system**: this
  per-archetype-then-meta structure is the production shape — each archetype is its own strategy-service strategy with
  the shared cost/liquidity/allocation lib; the meta-allocator is a distinct portfolio layer.
- **2026-06-17** — **Global transaction-cost-optimal rebalance (the 'PhD formula') — BIG win** (operator: the greedy
  rotation 'isn't very smart'). FIRST, measured the market widths: they are **tiny** (median half-spread 0.68bps, max
  4.80bps FET; BTC 0.01 / ETH 0.03) — NOT huge. So the ~7% cost drag was almost entirely **fixed 5bps/leg x turnover**,
  and the **greedy pairwise gate + daily carry-tilt reweighting was OVER-TRADING** (paying the fixed cost too often).
  FIX: replaced the greedy gate with a **per-period global L1 transaction-cost LP** (`_lp_rebalance` via
  scipy.optimize.linprog): maximise `Σ reward_i·w_i - Σ cost_i·|w_i - w_old_i|` s.t. Σw=1, 0<=w<=cap, where
  `reward_i = carry_i x horizon`, `cost_i = 2(fixed+spread_i)` — so the L1 term is the TRUE no-trade band: move weight
  A->B only when `(r_B - r_A)·horizon` beats the round-trip cost `(cost_A+cost_B)`, solved GLOBALLY (the 'which flips
  into what' problem), preferring low-friction pairs; per-coin `cap` diversifies. **RESULT on the cached full backtest
  (2025-01-01 -> 2026-06-16, 40 coins)**: ensemble causal net **6.5% -> 10.8%**, turnover **0.123 -> 0.019/day (6x
  lower)**, drag **7.0% -> 1.0%**; staked basis 5.7->7.3%, dispersion 4.4->8.5%. The greedy gate stays available via
  `--greedy-rotation` for comparison. **Integration note for main system**: production rebalancing must be a global
  transaction-cost optimisation (LP/convex), NOT greedy pairwise + daily reweighting — the no-trade band is what keeps
  turnover (hence fixed-cost drag) low. **Shipping** via watcher (QG-blocked only by a TRANSIENT foreign
  strategy-service version drift from the capability-wizard bump 0.12->0.14->0.15, mid fleet-propagation — not this
  code; ruff+imports+substantive-QG green).
- **2026-06-17** — **Two operator clarifications + a capital-aware liquidity fix** (`e2e@ce0e568`). (1) **The 5% floor
  is on NET CARRY, not raw funding** — confirmed correct: the filter is `net_bps >= min_carry_bps`, and `net_bps` per
  archetype is dispersion=`spread x eff` (the funding DIFFERENTIAL), staked=`(funding+staking) x eff` (so 2% funding +
  3% staking clears 5%), pure=`funding x eff` (absolute — the only one where raw funding is the sole metric). No change
  needed. (2) **Liquidity dampening was capital-BLIND** (operator: at $100k liquidity shouldn't suppress opportunities):
  the ADV factor `min(1, ADV/$100M)^damp` dampened a $2M-ADV coin to 0.14x weight regardless of capital. FIX: the ADV
  reference is now **capital-aware** — `liq_ref = (deployable/top_n) / adv_impact_pct` (knob `--adv-impact-pct`, default
  1%), so a coin earns full weight while a typical position stays under 1% of its ADV. At $100k liq_ref~$400k -> nearly
  every coin gets full weight (no dampening); at large capital low-ADV coins dampen. **NOTE**: this affects the ORACLE +
  LIVE paths; the new default **LP causal path does NOT use ADV dampening at all** (it uses carry - spread-in-cost), so
  liquidity was NOT suppressing the LP backtest. **Why the recent APY looks lower than the old chart's +22%**: the old
  chart is **2022-01-01 -> 2026-05-20** (4.4y, incl. the high-funding 2022-2024 era); the recent LP runs are the
  **18-month 2025-01-01 -> 2026-06-16** window, a much lower-funding regime — it's the WINDOW, not the venue/coin
  additions (a 2022-2026 new-model run is in flight to confirm apples-to-apples). **Staked basis is correctly restricted
  to ETH+SOL only** (`_BASE_TO_LST`).
- **2026-06-17** — **Funding-rate diagnostic + concentration knob** (operator: 'if HYPE/Bybit averages 23% how are we
  not getting that action?'). Built **`plot_funding_history.py`** (faceted plot, one panel/coin, line/venue, annualised
  funding over time — served on localhost:8910). Findings: (a) **only 20 of the 40 coins have GCS funding data** in
  2025-2026 (the 10 newer names WIF/BONK/JUP/JTO/RENDER/FET/TAO/ORDI/STX/LDO have NO coverage) — '40 coins' is
  really 20. (b) Funding **spikes high but means are modest**: HYPE/Bybit mean 23.8% / median 13.9% / max 192% over only
  **128 of 507 days** (HYPE is a 2024-launch). (c) **We DID hold HYPE** — 106 days at avg weight 0.119, right at the
  per-coin cap, so the carry-tilt wanted MORE but the **0.12 cap throttled concentration**. Exposed the cap as
  **`--max-weight`**: sweep on the 18mo window ensemble causal net **0.12->10.8% / 0.25->10.8% / 0.40->11.0% / uncapped
  1.0->13.6%** (avg net carry held 11.5%->14.6%, maxDD -0.01%->-0.34%). So we CAN capture more of the high-funders by
  concentrating; the default 0.12 is the diversified/low-drawdown choice. **Integration note**: the
  diversification-vs-concentration cap is a first-class portfolio knob; production should expose it per risk mandate.
  **Why recent APY < the 2022-2026 +22% chart = the WINDOW** (2025-2026 compressed-funding regime + half the coins
  dataless), NOT the venue/coin additions.
- **2026-06-17** — **ADV-aware per-coin cap** (`e2e@37dcede`, operator: 'raise the cap to 0.33 if ADV allows'). The
  per-coin weight cap is now `min(ceiling, adv_impact_pct x ADV_i / deployable)` — a liquid coin can take up to the
  ceiling (default raised 0.12->**0.33** via `--max-weight`), a thin coin only what its volume absorbs. At $100k
  ensemble ~10.7% (vs flat-0.12 10.8%): it barely rises because **the high-funders are mostly THIN coins** so ADV, not
  the ceiling, binds — the old uncapped 13.6% ignored market impact (unrealistic); 10.7% is the impact-aware
  concentrated result. **Diversification-vs-concentration is now a first-class knob** (ceiling + ADV-affordability).
- **2026-06-17** — **Data-backfill diagnosis (operator: 'we have the prod backfill code, isn't HYPE S3 AWS data')**:
  confirmed. (a) The 10 dataless coins (WIF/BONK/JUP/JTO/RENDER/FET/TAO/ORDI/STX/LDO) are a **cost-curated universe
  gap** — `launch-cefi-sharded-backfill.sh` uses a hand-curated `--instrument-ids` filter (operator chose a subset to
  cap Tardis cost), so these were never captured though Tardis lists them (all are in UAC `defi_major_assets`). (b)
  **HYPE**: Hyperliquid S3 (`hyperliquid-archive`, asset_ctxs/funding from 2023-05) is wired via MTDS
  `HyperliquidS3Downloader` — but HYPE the TOKEN only listed ~Nov-2024, so the 128/507-day gap is mostly genuine (a
  small Nov-Dec 2024 slice could be pulled). **TODO below.**
- **2026-06-17** — **pipeline_mode glued-transport (`hyperliquid_rest`) — provenance + state + harness consumer fix**
  (`e2e@8623c1c`). Operator asked where `rest`-in-the-pipeline-mode came from. ANSWER: the original pipeline*mode hive
  migration (Phase 1B, 2026-05-19) glued transport into the source (`batch_hyperliquid_rest`); **operator R4
  (2026-06-07) RETIRED it** -> canonical
  `pipeline_mode={mode}*{vendor}` (`batch_hyperliquid`) with `transport` (rest/websocket/flat_file) as a SEPARATE manifest column (`default_transport_for_source`); tardis already does this correctly (flat_file in the column). SSOT: `pipeline_mode-partition.md`L13-16/118-120 +`plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`. **CODE IS ALREADY CANONICAL**: UAC `PipelineMode`enum has no`\*\_HYPERLIQUID_REST`members; fleet grep = ZERO active emitters of a glued literal; new writes go to`batch_hyperliquid`. **What remains is DATA not code**: the legacy on-disk `hyperliquid_rest`objects (~19.4K) — the standardisation plan defers this as 'the BREAKING object migration, separate GATED tranche' (L322); plus intentional transitional READ-tokens in UAC`possible_manifest.py`+ a few stale codex doc refs. FIXED my carry harness (the one consumer reading the exact`\_rest`literal) to read canonical`batch_hyperliquid`first, fall back to legacy`batch_hyperliquid_rest`
  until the on-disk migration lands. **REMAINING is the gated on-disk object migration + doc cleanup — belongs in the
  standardisation plan, NOT new code.**
- _(append entries as work continues)_

## Open data gaps (file/verify) — added 2026-06-16

- [ ] [DATA] P2. `lending-indices` (+ `lst-rates`) writer targets the LEGACY un-suffixed bucket; canonical is
      `lending-indices-prd-…` / `lst-rates-prd-…` (empty `_migration/`). Fix the writer to `resolve_bucket_name`
      env-split + migrate legacy data → `-prd`. **Repo: market-tick-data-service + a GCS migration.** Owner:
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`.

## Findings filed

- Data-correctness (cadence registry inconsistency / `funding_timestamp` offset / no historical cadence tracker / Aster
  backfill) → `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`.

## Execution structures + capital efficiency (operator design 2026-06-16)

The funding you _capture per unit of deployed capital_ depends on how the long (spot/LST) and short (perp) legs are
collateralised. Rank on **effective carry = (funding + applied_staking) × capital_efficiency**, not raw funding.

**Five structures** (assign each (coin, venue) opportunity to one):

1. **Spot + perp, same venue, spot IS collateral** — venue liquid for spot AND accepts spot as margin (portfolio/
   unified margin: Binance/Bybit/OKX). Start USDC/USDT → buy spot + short perp, one collateral pool. `efficiency ≈ 1`.
2. **Staked-basis LST + perp, same venue, LST IS collateral** — venue accepts the LST (Bybit/OKX stETH/wstETH, Deribit
   stETH). Earn staking + funding on one margin base. `efficiency ≈ 1 − lst_haircut` (Bybit/OKX 10%, Deribit 7.5%).
3. **Spot on venue A → transfer → short on venue B (B accepts the moved spot/coin as collateral)** — illiquid spot at B,
   so buy spot at A, move it, short at B. Costs: transfer fee + **timing gap** (price can move between buy and short).
   Mitigations: (a) buy→send→short (gap risk); (b) borrow the coin against USDT, post borrowed coin at B, short,
   simultaneously buy at A to repay — needs a margin/borrow account + LTV cap, usually a separate account so often
   impractical; **(c) prime-broker / off-exchange settlement (see below) — the clean answer.**
4. **Spot on venue A + STABLECOIN margin on perp venue B (B rejects spot/LST collateral: Hyperliquid, Aster)** — capital
   splits: cash for spot AND cash for perp margin. `efficiency = notional/(notional+margin) = 1/(1+m)` where `m` = max
   adverse (up) move budgeted before rebalance. Operator example: 100k → 60k spot + 40k margin → short 60k → capture
   **0.6×** the funding. **Per-asset `m`** (max up-move buffer): BTC ~0.20, ETH ~0.25–0.30, mid alt ~0.50–0.60, small
   alt ~0.80 → `f` ≈ 0.83 / 0.77 / 0.62 / 0.56. Parameterise `m` per asset and scale required margin → discount funding
   by `f` in the ranking.
5. **Perp–perp (no spot leg)** — when one venue's funding is ~zero and another's is high (or one negative + one positive
   — observed **20.6%** of coin-days), go **long the low/negative-funding perp + short the high-funding perp**, split
   collateral ~50/50; both legs stablecoin-margined, delta-neutral, full size. This is the
   `arbitrage_price_dispersion`/funding-dispersion cousin — capture the cross-venue spread (p95 ≈ 32% APY).

**Prime-broker / off-exchange-settlement bridge (TODO — find the venue).** The capital-efficiency drag of structures 3–4
largely disappears if a prime broker / tri-party custodian posts _temporary_ collateral at the short venue so you can
short immediately, then you replace it once the spot balance moves over (or just keep collateral in custody, mirrored to
the exchange — never physically moving the coin). This is exactly what **off-exchange settlement networks** do: **Copper
ClearLoop, Ceffu (Binance) MirrorX, FalconX / Hidden Road prime** — collateral stays in custody, the exchange recognises
it for margin, no transfer-timing gap. The workspace already uses **Copper + Ceffu** for custody
(`codex/04-architecture/custody-providers.md`) → ClearLoop/MirrorX are the natural rails for capital-efficient
cross-venue basis. **Action: confirm which of our custody PBs support off-exchange margin on which short venues; if so,
structures 3–4 collapse toward `efficiency ≈ 1`.**

## Funding-regime findings (2025-01-01 → 2026-05-20, 37,128 coin·venue·day points)

- **22.9% of funding observations are NEGATIVE**; median 6.5% APY; a heavy cluster sits at the ~11% cap (0.01%/8h).
- **12% in [0,3%) "meh"** (hold/stake, don't short — `--min-carry-bps` floor); **65% ≥3%**; **~3% ≤ −20%** (flip to
  long-the-perp).
- **20.6% of coin-days have a cross-venue sign split** (neg on one venue, pos on another → structure-5 dispersion play);
  cross-venue spread p95 ≈ 32% APY.
- **Deribit funding is unreliable in the raw feed** (p95 130%, min −878%) — consistent with the 8h-vs-1h normalisation
  bug filed in the cadence issue; winsorise outliers + treat Deribit funding as suspect until that's fixed.

## Live/paper multi-venue expansion (operator 2026-06-17)

**Spec / integration SSOT**: `codex/02-data/carry-venue-live-integration-reference.md` (per-venue funding quirks + LST
staking + Aave lending + conservative-default discipline + how-to-add-a-venue). For paper the decision doesn't need deep
history, so the live path uses **every venue we can reach by public API or hold credentials for** + conservative
estimates (filed below) where a characteristic isn't yet verified. **Probed reachable 2026-06-17** (public, no auth):
Binance, Bybit, OKX, Deribit, Hyperliquid (POST), Aster, **Gate, KuCoin, Bitget, Kraken Futures, MEXC** (11 venues).

- [ ] [STRATEGY] P2. Build the harness `--live` multi-venue snapshot mode per the spec doc §1–§3: fetch current funding
      from all 11 venues (interval-aware annualise — HL+Kraken hourly, Kraken `fundingRate÷markPrice`, Deribit
      8h-figure, Gate/MEXC interval from the API), `FundingPoint(day="LIVE")` → existing
      `_build_panel`/ensemble/`_build_instructions`/ `_diff_to_target` (batch==live). New venues default to cash-margin
      (conservative). Expand coins to ~40. **Repo: e2e-testing harness.**
- [ ] [DATA] P2. UAC `perp_funding_cadence`: add Gate/KuCoin/Bitget/Kraken/MEXC cadences (+ per-pair non-8h exceptions);
      prefer the interval the API returns. **Repo: unified-api-contracts.**
- [ ] [DATA] P2. UAC `venue_collateral`: verify + add the 5 new venues' real collateral programs (several run
      multi-asset/portfolio margin that would lift them off the conservative cash-margin default → better efficiency /
      enables `spot_same_venue`/`staked_basis`). Until verified, cash-margin default holds. **Repo:
      unified-api-contracts.**
- [ ] [DATA] P2. Wire live LST staking APR sources per spec §4: RocketPool rETH, Coinbase cbETH, Marinade mSOL (Lido
      stETH + ether.fi weETH/EigenLayer already mapped); derive from on-chain exchange-rate growth or protocol APR
      endpoint; conservative trailing-realised default + TODO where missing. **Repo: e2e-testing → features-service.**
- [ ] [DATA] P2. Live Aave reserve-data adapter (supply/borrow APY from `getReserveData`
      liquidityRate/variableBorrowRate, RAY-scaled) for the cash floor + recursive borrow leg; Compound v3 source.
      **Repo: e2e-testing → mtds.**
- [ ] [STRATEGY] P2. Wire **dYdX v4 + Vertex** (both PUBLIC, verified 2026-06-17) into the live snapshot: dYdX
      `indexer.dydx.trade/v4/perpetualMarkets` (`nextFundingRate`, hourly); Vertex `gateway.prod`/`archive.prod`
      (public; `api.vertexprotocol.com` is a stale 404). **Repo: e2e-testing harness.**
- [ ] [DATA] P2. Production Drift funding in **MTDS** via the isolated-venv reader pattern (a Drift handler that shells
      out to the driftpy venv / a Drift gateway subprocess; canonize into `derivative_ticker` like other venues). Same
      isolation — driftpy stays out of MTDS flat deps. **Repo: market-tick-data-service.**
- [ ] [EXEC] P2. Finish the **execution-service** Drift trading adapter (`defi_execution/protocols/drift.py` already
      lazy-loads driftpy) — install via the isolated venv / gateway in the Drift-enabled deploy; place short-SOL-PERP
      orders with jitoSOL/mSOL collateral. **Repo: execution-service.**
- [ ] [STRATEGY] P2. Wire **Drift** via the creds/RPC path — we HOLD `solana-paper-keypair-private-key` +
      `solana-wallet-address`; the public Data API 403s this VM (geo) + authed 401s → read funding on-chain via Solana
      RPC. Drift **takes jitoSOL/mSOL as margin → unlocks SOL staked-basis** (the only venue that does). Already in UAC
      (`venue_mapping`/`chain_env`). Not BLOCKED-CREDENTIALS — a wiring task. **Repo: e2e-testing → mtds drift
      handler.**
- [ ] [STRATEGY] P2. Live/paper **history carve-out** (operator 2026-06-17): no funding history for a venue → WARN + use
      the current snapshot (+ whatever spot history exists); never block a venue/coin for missing history. EWMA gate
      degrades to a point estimate under < halflife days. Backtest still needs history; this is live/paper only. **Repo:
      e2e-testing harness.**
- [ ] [STRATEGY] P3. Genuinely credentialed venues (Paradex, Backpack, Edgewink): file each `BLOCKED-CREDENTIALS` with
      the operator ask + build the adapter scaffold anyway (External-Data-Always-Available rule). **Repo: e2e-testing →
      ping ledger.**
- [ ] [STRATEGY] P3. Sign/units cross-check on integration: one coin per venue vs the spec §3 reference values before
      trusting the live ranking. **Repo: e2e-testing harness.**

## Liquidity (ADV + market width) follow-ups (operator 2026-06-17)

- [ ] [DATA] P2. Production **ADV + market-width + tick-size** feature in **MDPS** (per coin × venue, from the
      tickers/book + instrument-info endpoints) so strategy/execution size by liquidity in prod (batch==live). The e2e
      harness snapshot is the prototype. **Repo: market-tick-data-service + unified-api-contracts (schema).**
- [ ] [DATA] P2. **Tick size** per (coin, venue) — pull from each venue's instrument-info endpoint; feed the
      min-increment into spread/round-cost + order sizing. Not yet in the harness (only ADV + spread). **Repo:
      e2e-testing harness → MDPS.**
- [ ] [STRATEGY] P2. Backfill the liquidity snapshot as a **constant** across the backtest window + document the
      assumption inline in the harness/report (e2e-only approximation until MDPS history exists). **Repo: e2e-testing.**
- [ ] [STRATEGY] P2. **Dispersion per-venue-liquidity guard** (live-exclusion shipped 2026-06-17; deeper fix pending):
      `--live` perp-perp dispersion picks cross-venue funding EXTREMES (e.g. LDO 91% short KRAKEN/long BITGET) that
      mean-revert — tighten (per-venue winsor, min-ADV venue filter, require the spread to persist, or down-weight
      dispersion in --live). **Repo: e2e-testing harness.**

## Funding-data backfill to a genuine 40-coin universe (operator 2026-06-17)

- [ ] [DATA] P2. **Backfill the 10 dataless coins** (WIF, BONK, JUP, JTO, RENDER, FET, TAO, ORDI, STX, LDO) into GCS
      perp funding: add their Tardis symbols to the `--instrument-ids` universe in
      `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` (+ the AWS variant) and re-run for 2022->present.
      **COST NOTE**: the universe is deliberately curated to cap Tardis cost — adding 10 coins x ~5 venues x spot+perp
      raises the Tardis bill; confirm scope/window with operator before launch. This is the ONE lever that adds REAL
      opportunity to the carry backtest (vs reweighting 20 coins). **Repo: deployment-service +
      market-tick-data-service.**
- [ ] [DATA] P3. Pull HYPE's full HL-S3 funding history (asset_ctxs) from its listing (~Nov-2024) via
      `HyperliquidS3Downloader` to close the small pre-2025 gap. **Repo: market-tick-data-service.**
- [ ] [STRATEGY] P3. Gate this behind the v9 data-migration completion (per project sequencing); the harness auto-picks
      up new coins once they're in GCS (it skips dataless coins via honest absence). **Repo: e2e-testing.**

### 2026-06-17 — HL `batch_hyperliquid_rest` migration + full-universe funding → fuller backtest

**1. Pipeline_mode migration (DATA, prod).** Verifying the HL funding read path surfaced that HL cefi data was stranded
on the retired glued-transport `pipeline_mode=batch_hyperliquid_rest`. Traced to ground truth (the verdict-pack "19.4K +
64K = 83K" were _projected_ index counts, not on-disk reality): **cefi = 19,361 REAL objects**
(derivative_ticker/trades/book_snapshot_5/liquidations); **defi = 0 objects** (the "64K" is empty_confirmed/
attempted_failed perp_funding cells across 40 non-HL venues, labeled only in the audit projection — no data). The live
manifest stores pipeline_mode BLANK (derived from paths at projection time) → no manifest re-key needed. Migrated the
19,361 cefi objects → `batch_hyperliquid` via `mtds/scripts/migrate_hyperliquid_rest_pipeline_mode_2026_06_17.py`
(segment rename, server-side copy→verify→delete, idempotent). **Verified 0 remaining fleet-wide, byte-parity, 0 loss.**
Issue doc RESOLVED: `plans/active/issues/hyperliquid_rest_pipeline_mode_missed_by_v9_migration_2026_06_17.md`.

**2. Harness — full HL universe funding (the operator's "rest of the HL coins").** The harness read HL funding from the
Tardis `derivative_ticker` path (cefi bucket, ~20 curated coins). The FULL HL perp universe (~230 coins) lives in the
dedicated `perp-funding-{project}` bucket as `data_type=perp_funding` (the production `collect-perp-funding` handler;
already **659 days** present — 2025 fully covered, 2026 to 06-09, gap only 2023-2024). Added a per-day HL `perp_funding`
reader (`_read_hl_funding_day` — one parquet/day serves every coin), wired HL off the `derivative_ticker` task loop into
it, bounded the curated-venue reads to `_DEFAULT_COINS` (else 200+ wasted None-reads/venue/day), and added `--hl-full`
to union the discovered HL universe into `--coins`. HL funds hourly → annualised at
`perp_funding_cadence["hyperliquid"]`.

**3. Reader bug found + fixed (important).** The first `--hl-full` runs reported ~8% ensemble — but that was on a
NEAR-EMPTY HL load: historical perp_funding days (all 2025 / early-2026) were written BEFORE the `pipeline_mode=` path
partition (`asset_group=defi` only); newer days carry `pipeline_mode=batch_hyperliquid`. The reader hardcoded the new
layout → loaded only ~457 HL points (≈2 days) so the backtest effectively ran on the curated ~20-coin derivative_ticker.
Fixed to read BOTH layouts (`e2e@71666cb`) — now **104,066 HL points across 525 days** (was 457).

**4. Fuller backtest — REAL full-universe result** (`--hl-full`, 2025-01-01→2026-06-09, **232-coin universe**, 525 days,
5bps/leg, 5% floor) — causal (realistic, no-trade-band) NET APY full-period: **ensemble 14.1%** (turn 0.072/d, maxDD
−0.61%, drag 3.96%) · pure-basis 13.4% · funding-dispersion ~9% · staked-basis ~8%. Per year: 2025 ensemble causal
**15.5%** net (gross 18.4%, turn 0.073/d) · 2026-YTD ensemble causal **10.4%** net (gross 13.2%). The full HL universe
~DOUBLED the carry vs the bug-limited curated run — the long tail of HL perps carries far more funding, which pure-basis

- the ensemble harvest at tiny turnover/drawdown. Oracle/hindsight variants go deeply negative net (over-rotation).
  Still GROSS carry-only (no hedge/basis MtM) — Sharpe inflated, per existing P3 todo. Universe ~40 → 232 coins, no new
  strategy logic — purely the funding-source change.

**Verification:** `mtds` migration verified 0 objects under `batch_hyperliquid_rest` fleet-wide (independent gcloud
walk); fixed reader validated to load 198–227 HL coins/day on both layouts (2025-06-01 / 2026-01-15 / 2026-04-01).

**5. HL funding is REAL (not a placeholder) — but is dominated by HL's interest-rate FLOOR (operator Q 2026-06-17).**
Checked the code + data after a report that HL "defaults to 1bp/8h when no S3 data". Verdict: NOT a code default — the
S3-miss path (`hyperliquid_s3._fetch_funding_via_rest`) returns `[]` (honest absence) on empty REST `fundingHistory`,
and reads the literal `fundingRate`/`funding` value otherwise (the `0` guards only a malformed record). The data is real

- varied (2053/1296 distinct values, −0.8%/hr to +0.03%/hr, 17–29% negative). BUT **44.8% (2026) / 58.3% (2025) of
  hourly observations sit EXACTLY at 1.25e-5** = HL's interest-rate floor
  (`funding = premium + clamp(interest − premium)`, interest = 0.01%/8h = 1.25e-5/hr); when premium ≈ 0 HL clamps
  funding to exactly that constant. So it's HL's genuine clamped funding (the exact match to HL's formula constant + the
  higher share in the calmer 2025 regime confirm it's sourced from HL, not fabricated). **Strategy implication:** the
  interest floor ≈ **11% APY** that a short structurally earns, so a large part of the HL pure-basis carry is the
  persistent interest floor, premium/dispersion on top — real + durable, but not premium _alpha_. Decompose carry into
  floor vs premium when sizing.

**6. Full 3-year backtest (2023-05-20→2026-06-09, 232-coin universe, 169,241 HL funding points) — CARRY COMPRESSION.**
After backfilling HL funding to 100% over ~3 years, ran the full-history `--hl-full` backtest. Full-period causal NET:
ensemble **27.8%** (turn 0.099/d, maxDD −0.36%, Sharpe 16.6) · pure-basis 25.9% · dispersion 17.7% · staked 13.0%. But
the per-year trend is the real finding — **carry compressed ~4× as HL matured**: ensemble causal net **2023 47.4% → 2024
34.3% → 2025 16.6% → 2026-YTD 10.7%** (pure-basis 39.3→34.3→15.8→10.7). The 27.8% blend is INFLATED by the 2023-2024
HL-launch era (new exchange, few participants, huge directional premiums); **the realistic forward expectation is the
2026 regime ~11%, not the 3-year blend** — the launch-era goldmine won't recur. Turnover stays tiny + drawdown near-zero
throughout (real low-risk carry, just shrinking). Composes with finding #5: the ~11% floor is now most of the remaining
carry, so as premium compresses the strategy converges toward harvesting HL's structural interest rate. Still GROSS
carry-only (no hedge/basis MtM) — Sharpe inflated, per the standing P3 todo.

**7. Cross-sectional funding carry (NEW archetype, operator 2026-06-18) — NOT TRADEABLE, but funding is a strong
MOMENTUM FEATURE.** Built a cross-sectional long-short: long the lowest-funding / short the highest-funding HL coins
(different coins, same venue, $-neutral, liquidity/risk-parity weighted, diversified cap, leverage knob, funding + price
PnL). Needs the new `perp_daily_ctx` (mark*px+volume+OI) backfill. **Verdict: a LOSER.** 3yr naive NET −36%/yr, Sharpe
−1.3, maxDD −125%, winning quarters 4/13 (2024 −87%). A funding band-pass (drop |funding|>60%/yr momentum extremes)
lifts it to ~flat (−1.3%, Sharpe −0.25) but NO config is positive. Root cause (component split): the strategy harvests
ENORMOUS funding but loses ~exactly as much on price — **funding ≈ the adverse price move (efficient market)**: a coin
pays −245%/yr funding \_because* it is being violently shorted (crashing), so longing it loses on price what you gain on
funding. The book is structurally **short-momentum**, which bleeds in crypto.

**The valuable output is the predictive signal (for a SEPARATE ML exercise — NOT built here, operator 2026-06-18):**
extreme funding predicts CONTINUATION, not reversal. **Information coefficient `corr(funding, fwd_return)` = +0.047 (1d)
/ +0.055 (3d) / +0.073 (7d) / +0.057 (14d)** — all positive, peaking at 7d (a genuinely useful single-feature IC).
16,881 liquid (vol≥$10M) coin-days, 2023-06→2026-06. **Tails:** extreme-NEG funding (crowded shorts, |fund|>100%/yr) →
fwd-7d **−6.2%**, only **30% up** (shorts keep winning — NO squeeze on average); extreme-POS funding (crowded longs) →
fwd-7d **+4.8%**, **47% up** (longs keep winning). So a naive "extreme funding = squeeze/reversal" read is WRONG on
average — it's momentum; the **squeeze is the conditional ~30% tail**. ML implication: funding LEVEL is a momentum
feature; isolating the squeeze/crowded-long REVERSAL from the continuation needs additional conditioning features
(funding ACCELERATION / Δfunding, OI change, price extension, liquidation clusters). Analysis is reproducible from the
GCS `perp_funding` + `perp_daily_ctx` datasets (code in `e2e-testing/scripts/defi/staked_basis_funding_scan.py`
`_run_xsec_carry`). HTML: `xsec_carry_report.html` (xsec line vs the delta-neutral strategies).

## Open todos / next steps

- [ ] [RESEARCH→ML] P2. (separate ML agent/exercise — operator 2026-06-18; NOT built by the harness agent — empirical
      handoff) **Funding-dynamics GBM models for squeeze / crowded-long prediction** — full spec immediately below.

  **Hypothesis (finding #7):** funding LEVEL = momentum (IC +0.073 @ 7d). The REVERSAL (short squeeze on crowded shorts
  / unwind of crowded longs) is the conditional ~30% TAIL, predictable from the DYNAMICS of the extreme — how extreme,
  **how long it has persisted at that level** (operator: fresh spike vs stale extreme differ), accel/decel, OI +
  liquidation + extension context.

  **Features (per coin-day):** funding LEVEL (`apy_bps`) + cross-sectional percentile rank; **crowded flags**
  `|funding| > {50,100,200}%/yr` (operator's "abs funding>50%/yr = crowded short/long"); **persistence/recency**
  (operator key feature) — days since `|funding|` first crossed each threshold (current extreme-regime duration), days
  since funding last crossed zero, same-sign run-length; **acceleration** `Δfunding {1,3,7}d` + funding z-score vs
  {20,60}d; **OI** level
  - `ΔOI {1,3,7}d` (rising OI+extreme = build/continuation; collapsing OI+extreme = unwind/reversal); **volume**
    `day_ntl_vlm` + z-score; **price extension/vol** return vs {7,30}d MA + realized vol; **liquidations** (HL S3
    archive) = the squeeze trigger.

  **Targets:** (a) CLASSIFICATION — forward-Nd return is REVERSAL (opposite to funding-momentum) vs CONTINUATION, binary
  or 3-class, horizons {1,3,7,14}d; (b) REGRESSION — forward-Nd return / reversal magnitude. **Model:** GBM
  (LightGBM/XGBoost) cls+reg, walk-forward CV (no lookahead), SHAP/gain importance → keep the predictive subset (expect
  persistence + accel + ΔOI to beat raw level for the reversal tail). **Then blend the validated continuous signals
  (predicted reversal-prob / funding-momentum score) into the EXISTING carry/dispersion models** as features/overlays so
  the live book "does fewer shorts/longs" where a squeeze/unwind is likely. **Data:** GCS HL `perp_funding` (hourly) +
  `perp_daily_ctx` (mark_px/vol/OI), 2023-2026 100% coverage, + HL liquidations from the S3 archive. ⚠ canonicalize
  `perp_daily_ctx` → `derivative_ticker` first (canonical todo below). Reproducible from
  `e2e-testing/scripts/defi/staked_basis_funding_scan.py`. **Repo: features-service / ML.**

  **Squeeze-END predictability — first empirical cut (operator 2026-06-18; do these features predict WHEN the crowd
  unwinds?): NO — the intuitive exhaustion features all predict CONTINUATION or are flat.** On 7,791 extreme-funding
  episodes (|funding|>100%/yr, liquid, 2023-2026), correlating each feature with the 7d REVERSAL (reversal>0 = crowd
  unwound, i.e. price moves against the funding direction): **persistence** (days the extreme has held) corr **−0.041**
  — reversal −1.5% (fresh) → **−5.1% (>10d stale)**, so the longer it persists the HARDER it continues (accelerates, no
  exhaustion); **price extension** (SDs from 20d mean) corr **−0.097** (strongest) — most-extended continues hardest
  (−0.6% → −4.7%); **volume change** corr −0.033; **ΔOI 7d** corr **+0.015** (flat — ~−2% reversal whether OI is
  collapsing or surging). So the slow daily exhaustion proxies do NOT flag the squeeze; the momentum is robust + speeds
  up. **ML implication:** the tradeable, predictable edge is the CONTINUATION (funding-momentum, IC +0.073@7d); the
  squeeze/unwind is a tail that needs FASTER / exogenous signals — funding INFLECTION (the moment funding turns down
  from the extreme), liquidation cascades (HL archive), order-book imbalance, news — NOT the slow daily
  persistence/extension/ OI. Another agent should start the squeeze model from those faster signals, treating these four
  slow features as confirmed non-predictors of the reversal (use them for the continuation side instead).

  **CROSS-VENUE / LIQUIDITY: the funding signal's SIGN INVERTS with coin liquidity, NOT venue (operator 2026-06-18 —
  "does the game change on Binance? are some venues more predictionary?").** Measured `corr(funding, fwd_7d_return)` per
  venue on the SAME curated majors (BTC/ETH/SOL/XRP/BNB/DOGE/AVAX/LINK, derivative_ticker, Jan-May 2025, n=1200/venue):
  **HYPERLIQUID −0.129 · BYBIT −0.108 · BINANCE −0.079 · OKX −0.017** — ALL NEGATIVE (funding = CONTRARIAN/REVERSAL on
  liquid majors: crowded → mean-reverts). But the HL FULL 230-coin universe (perp_funding) IC was **+0.073 (MOMENTUM)**
  — so the earlier "funding=momentum" headline was driven by the ILLIQUID LONG-TAIL, not majors. **Synthesis: liquid
  majors → funding contrarian (reversal); illiquid long-tail → funding momentum (trend).** The venue does NOT flip the
  sign; it modulates STRENGTH — **HL carries the most information on majors (−0.13), then Bybit, Binance, OKX≈0**
  (consistent with HL being the more retail/less-arbitraged book, so its funding extremes are the strongest crowding
  signal). ML implication: the funding feature MUST be conditioned on (liquidity tier × venue) — a single universe-wide
  funding factor has a sign that flips, so split majors-vs-tail and weight venues by their |IC| (HL > Bybit > Binance >
  OKX). **Tested the actionable corollary** (does a MAJORS-ONLY carry win, since majors mean-revert?): no — min_vol
  $50M-500M / n=5-12 nets −1 to −3%/yr (still slightly negative), BUT maxDD collapses to **−3% (vs −125%
  full-universe)**. So the reversal edge on majors is real but too small to overcome the tiny major funding spread +
  costs — confirms funding≈price efficiency even where the sign favours the carry; the value stays in the FEATURE, now
  liquidity/venue-conditioned. Reproducible: `_run_xsec_carry` (min_vol filter) + the cross-venue IC reader
  (derivative_ticker funding_rate+mark_price per venue).

  **REGIME CLASSIFIER BUILT + the decomposition that CORRECTS the above (operator 2026-06-18 — "make a classifier; ml
  can't do it alone without overfitting"). KEY RESULT: the dramatic liquidity/venue regime split was LARGELY A STATIC
  SELECTION ARTIFACT, not a predictive signal.** Built `funding_regime_classifier.py` (sample=(coin,quarter),
  target=sign of within-coin IC, features=log ADV/OI/rvol/|funding|/log px/maturity, LightGBM + grouped-by-coin CV +
  logistic baseline). Before classifying, decomposed the funding→return IC: **BETWEEN-coin (static/selection) = +0.31**
  (coins that MOONED over 2023-24 carried high AVERAGE funding — strong but NOT tradeable, you can't trade "the winners
  had high funding" forward) vs **WITHIN-coin (dynamic/predictive, per-coin demeaned) = +0.02** (≈ZERO genuine
  predictive signal). So the earlier headline ICs (+0.073 momentum / −0.13 reversal) were dominated by the +0.31
  selection effect + small-sample/source differences — **exactly the "other stuff" a raw-funding ML overfits.** After
  demeaning, the residual predictive tilt is WEAK and the OPPOSITE of the hypothesis: liquid → mild MOMENTUM (D5
  +0.066), illiquid → mild REVERSAL (D1 −0.020). The classifier itself: AUC **0.644** (modest, grouped CV), no single
  feature dominates (rvol 19% / log_adv 18% / log_px 18% / |funding| 17% / log_oi 16%), 1-feature log_ADV baseline AUC
  0.522 (liquidity alone ≠ the driver), continuous-IC regressor R²≈0 (unpredictable). **Disciplines for the ML agent:
  (1) DEMEAN funding per-coin before it enters any model — the raw cross-sectional level encodes the un-tradeable +0.31
  selection effect; (2) treat the regime as a WEAK soft-conditioner (AUC ~0.64), never a strong standalone signal; (3)
  the cross-venue |IC| ranking (HL>Bybit>Binance>OKX) and "liquid=reversal" framing are confounded — re-derive on
  per-coin-demeaned funding before trusting them.** Reproducible:
  `e2e-testing/scripts/defi/funding_regime_classifier.py` (prints the decomposition + decile tilt + CV AUC; saves
  panel.parquet + the LGBM model).

- [ ] [STRATEGY] P3. Cross-sectional carry is NOT tradeable standalone (funding≈adverse price) — only revisit with a
      genuine price-neutralising overlay (correlation-paired long/short of co-moving coins, or a momentum/beta hedge)
      AND only if it clears Sharpe; otherwise the archetype is shelved. The delta-neutral staked/pure-basis remain the
      proven winners. **Repo: e2e-testing.**

- [ ] [STRATEGY] P2. Decompose HL pure-basis carry into the interest-rate FLOOR (~11% APY structural, ~45-58% of hours
      clamp to it) vs the premium/dispersion component — so sizing reflects how much is structural vs alpha. **Repo:
      e2e-testing harness → strategy-service.**
- [ ] [DATA] P3. (optional certainty) spot-check a sample of HL funding cells at the 1.25e-5 floor against HL's live
      on-chain `fundingHistory` to confirm the archive's floor values match realized on-chain funding. **Repo:
      e2e-testing.**

- [x] [DATA] ✅ P2. Backfilled HL `perp_funding` to **100% coverage 2023-05-20→2026-06-09 (1117/1117 days, 0 gaps)** via
      the fast S3 `asset_ctxs` archive (`mtds@98d12be`, no REST rate-limit, ~4 min for 374 days/965k rows) + a 7-day
      REST fill for the days HL's S3 archive lags (06-02→08). HL funding history now spans ~3 years for the full
      ~230-coin universe. **Repo: market-tick-data-service.**
- [ ] [STRATEGY] P2. Add the capital-efficiency factor to the harness ranking: structure assignment per (coin, venue)
      (spot-collateral set {Binance/Bybit/OKX/Deribit} vs cash-margin {Hyperliquid/Aster}), per-asset max-move `m` →
      `f=1/(1+m)`, rank by `effective_carry = (funding+staking)×f`, winsorise funding outliers, `--min-carry-bps` floor
      (default 300). **Repo: e2e-testing harness.**
- [ ] [STRATEGY] P2. Add structure-5 (perp–perp funding dispersion: long low/neg-funding perp + short high-funding perp)
      as a candidate alongside the spot/LST basis. **Repo: e2e-testing → strategy-service.**
- [ ] [RESEARCH] P2. Prime-broker / off-exchange-settlement bridge — confirm whether Copper ClearLoop / Ceffu MirrorX /
      FalconX / Hidden Road give off-exchange margin on our short venues (HL/Aster/Bybit/OKX); if yes, structures 3–4
      collapse to `efficiency ≈ 1`. Cross-link `codex/04-architecture/custody-providers.md`. **Repo: PM research +
      execution-service.**

- [ ] [STRATEGY] P2. Use `predicted_funding_rate` (already a `derivative_ticker` column) to gauge ENTRY on venues that
      publish a forward rate — enter/size based on predicted next-cycle funding, not just trailing realised. Only where
      the venue supports a forward rate (operator 2026-06-16). **Repo: e2e-testing harness → then strategy-service.**
- [ ] [STRATEGY] P2. Fold the net-carry signal into `strategy-service` `CarryStakedBasisRankAllocator` (swap the harness
      ranking for the production allocator; batch == live). **Repo: strategy-service.**
- [ ] [STRATEGY] P3. Add fees + slippage (per-venue taker + rotation cost) to turn GROSS carry into NET PnL; today the
      harness is GROSS only. **Repo: e2e-testing harness.**
- [ ] [STRATEGY] P3. Model the hedge/basis mark-to-market (the real risk) — current Sharpe/maxDD are carry-accrual only
      and flatter the strategy. **Repo: e2e-testing → strategy-service backtest (GroupBRunner).**
- [ ] [DATA] P2. (blocked-by issue doc) once exact discrete per-settlement funding is readable, switch the harness off
      the day-mean workaround to true per-settlement realised funding.

## RECONCILIATION with Pass-B (CeFi/Binance cross-coin reversion) — venue-dependence PROVEN (2026-06-18)

The CeFi agent (Pass B, bundle `gs://backtest-results-central-element-323112/cross_coin_funding_handoff_2026_06_18/`)
built a **dollar-neutral cross-sectional funding-RANK reversion** book on Binance perps (long lowest-funding / short
highest-funding, inverse-vol within each leg, EWMA-7 signal, point-in-time incl. 20 dead coins, 5bp) → **Sharpe 1.44,
maxDD −34%, positive every year**. It is 99% cross-sectional PRICE-reversion (funding is just the ranking signal), NOT a
funding harvest. Apparent contradiction with our "carry not tradeable" — RESOLVED, both right:

1. **Reproduced their 1.44 exactly** + audited the vol-scaling salvage (0.49→1.32): **causally CLEAN** —
   `vol30.shift(1)`
   - `sig.ewm().shift(1)`, no lookahead. Their headline survives scrutiny.
2. **Their "+0.31 between-coin selection" ≡ our "+1.17 survivorship" — same finding, two framings.** Their "within-coin
   +0.02 ≈ 0" ≡ "funding has no harvest timing power." Agreed on both.
3. **KEY NEW RESULT — ran their EXACT method on HL (native perp marks, full 230-coin universe, no hand-picked
   survivorship): Sharpe 0.30 (vs Binance 1.44).** Decomposition: **price-only Sharpe −1.03 on HL vs +1.04 on Binance —
   the price component FLIPS SIGN BY VENUE.** Binance (crowded arb zone) → funding pulled to fair → residual is
   REVERSION (short high-funding wins); HL (less-arbitraged, directional) → funding CHASES price → MOMENTUM (short
   high-funding loses). So the cross-sectional reversion edge is **VENUE-DEPENDENT** — it is an arbitrage-intensity
   phenomenon, not a universal funding effect. Our "HL carry not tradeable" + their "Binance reversion 1.44" are the
   SAME truth at opposite ends of the arb spectrum, exactly the operator's economics (HL more directional bets / less
   basis-arb than Binance).
4. **Their methodology improvements are real + transferable**: inverse-vol-within-legs + EWMA-7 lifted HL from our naive
   xsec (−1.3 Sharpe) to +0.30 — the weighting/smoothing genuinely help even where the alpha is absent.

**IMPROVEMENTS for the strategy (journaled for the ML agent):** (a) **VENUE is a first-order gate** — run this reversion
book ONLY on heavily-arbitraged CeFi venues (test Bybit/OKX/Deribit next — predict they also revert), NEVER on HL/DeFi
or thin venues where funding is momentum; add a "venue arb-intensity" feature. (b) **Their #1 caveat
(spot-as-perp-proxy) is perp-ROBUST at the venue level** — our HL test used NATIVE perp marks and reversion still fails
on HL, so the venue-dependence isn't a price-proxy artifact; they should still re-run Binance on true perp marks (fapi
OHLCV) to confirm 1.44 (the cefi GCS bucket is only ~20 curated coins, not their 50, so the full perp re-run needs their
fapi pipeline). (c) the 1.44 leans on the one-off 2026 dispersion spike (yearly 2022 +0.77 → 2026 +2.04) — underwrite
ex-2026. Reproduce: their `_carry_deployable.py` (`CACHE=./cache`); our HL port is the inline harness in this session.

**CROSS-VENUE SWEEP — reversion regime confirmed across ALL arbitraged perp venues; HL is the lone momentum outlier
(2026-06-18).** Ran their exact method (EWMA-7 funding rank, inverse-vol legs, dollar-neutral, 5bp) on each venue. The
robust read is the **price-only Sharpe SIGN** (reversion>0 / momentum<0):

| Venue           | price-only Sharpe                  | net          | ann.ret | universe / source                           | regime                                           |
| --------------- | ---------------------------------- | ------------ | ------- | ------------------------------------------- | ------------------------------------------------ |
| **Bybit**       | **+1.81**                          | +1.48        | +40%/yr | 9 majors, cefi GCS, 1yr                     | reversion (strongest on majors)                  |
| **Aster**       | **+1.10**                          | +1.30        | +51%/yr | 14 coins, LIVE fapi.asterdex.com, 1.7yr     | reversion                                        |
| **Binance**     | +1.04 (50-coin) / +0.09 (9 majors) | 1.44 / −0.12 | +58%/yr | deployable small-caps vs majors             | reversion (edge in small caps; majors efficient) |
| **OKX**         | +0.44                              | +0.20        | +6%/yr  | 9 majors, cefi GCS, 1yr                     | mild reversion                                   |
| **Hyperliquid** | **−1.03**                          | +0.30        | —       | 230 coins, native perp, 3yr                 | **MOMENTUM (outlier)**                           |
| Deribit         | —                                  | —            | —       | symbol mismatch + few perps (options venue) | inconclusive (no data)                           |

**Conclusion: the cross-sectional funding-rank reversion edge is an ARBITRAGE-INTENSITY phenomenon, not DEX-vs-CEX.**
Every well-arbitraged perp venue (Binance, Bybit, OKX, Aster — incl. the Aster DEX, which is Binance-API-compatible with
heavy arb-bot flow) shows price REVERSION (short high-funding wins); only HL — thin arb, dominated by directional bets —
shows MOMENTUM (short high-funding loses). This is exactly the operator's economics. Caveats: the GCS majors sweep is a
short (1yr) 9-coin window so absolute numbers are noisy (Binance majors read weak +0.09 because its edge lives in the
small caps the GCS bucket lacks; the SIGN is the robust part); Aster is short-window + live-pulled. **Strategy
implication: deploy the reversion book across the arbitraged venue set (Binance/Bybit/OKX/Aster), size by each venue's
small-cap funding dispersion, and EXCLUDE HL from this archetype (HL is for the delta-neutral basis/staked carry, not
the reversion book). Aster needs a GCS backfill (today only live-API).** Yield note: the deployable runs ~+58%/yr
(Binance) / +51%/yr (Aster) at ~40% vol — high-octane reversion, NOT smooth carry. Liquidity in the deployable = inverse
price-VOLATILITY weighting (not volume); ADV (Binance-specific spot 15m) is only a universe filter. Per-coin PnL plot
rendered (`/tmp/passB/binance_carry_per_coin_pnl.html` — TLM/CTK/TRX top, dead +116% / survivors +153%).

## ML-Agent Handoff — funding-rate prediction (data + code locations, 2026-06-18)

Self-contained pointer set for the separate ML agent (who has its own features + better predictions) to combine
everything and push the within-coin predictive IC up. **All data is already in GCS production buckets; all code is in
the repos. Test downstream in the production spine (MTDS → features-service → strategy-service), not just the e2e
research harness.**

**WHERE THE DATA IS (GCS, project `central-element-323112`):**

- **Hyperliquid funding + price/OI (DeFi bucket, full ~230-coin universe, 2023-05-20→today, 100% coverage):**
  `gs://perp-funding-central-element-323112/raw_tick_data/by_date/day={YYYY-MM-DD}/pipeline_mode=batch_hyperliquid/asset_group=defi/venue=HYPERLIQUID/chain=HYPERLIQUID/instrument_type=perpetual/data_type={DT}/`
  with `{DT}` ∈ `perp_funding` (hourly `funding_rate`+`premium`) and `perp_daily_ctx` (daily-close `mark_price` +
  `day_ntl_vlm` + `open_interest`). Symbol = bare coin (`BTC`). **Legacy-layout caveat:** historical days
  (2025/early-2026) were written BEFORE the `pipeline_mode=` partition — readers must try BOTH the
  `pipeline_mode=batch_hyperliquid/…` path AND the bare `…/day=D/asset_group=defi/…` path (the harness loaders already
  do).
- **CeFi derivative_ticker (Binance/Bybit/OKX/Deribit/Kraken/Bitget/… funding + mark_price, tick-level):**
  `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day={D}/pipeline_mode={MODE}/asset_group=cefi/venue={VENUE}/instrument_type=perpetual/data_type=derivative_ticker/{SYM}.parquet`.
  `{MODE}` = `batch_tardis` for the CeFi venues, `batch_hyperliquid` for HL's CeFi mirror. Columns: `funding_rate`,
  `mark_price`, `index_price`, `last_price`, `funding_timestamp`. **Venue dirs:** `BINANCE-FUTURES`, `BYBIT`,
  `OKX-SWAP`, `DERIBIT`, `KRAKEN-FUTURES`, `BITGET-FUTURES`, … (perp list is broad; majors-only for some). **Symbol
  formats differ:** Binance/Bybit `BTCUSDT`, OKX `BTC-USDT-SWAP`, HL-CeFi-mirror `BTC-PERP`. Curated ~20-coin Tardis
  coverage (not the full HL universe).
- **HL raw S3 archive (requester-pays, Secret Manager `aws-hyperliquid-s3`, bucket `hyperliquid-archive`):**
  `asset_ctxs/{YYYYMMDD}.csv.lz4` (minute-res funding/OI/premium/oracle_px/mark_px/mid_px/impact_bid/ask/day_ntl_vlm —
  the source the GCS backfill downsamples) and `market_data/{YYYYMMDD}/{hour}/l2Book/` (hourly **L2 order-book
  snapshots** → order-book imbalance, the faster squeeze signal; no standalone liquidations feed — infer from
  book/fills).

**THE CODE (repos, all on `live-defi-rollout`):**

- `e2e-testing/scripts/defi/staked_basis_funding_scan.py` — funding research harness. Reusable loaders:
  `_load_hl_funding(client, frozenset(_live_hl_universe()), days, workers)` → funding points (`.day/.base/.apy_bps`);
  `_load_hl_ctx(client, days, workers)` → `{day:{coin:(mark_px,vol)}}`; `_date_range(start,end)`; `_run_xsec_carry`
  (cross-sectional carry backtest). Cross-venue IC reader pattern is inline in the experiment journal.
- `e2e-testing/scripts/defi/funding_regime_classifier.py` — the LightGBM regime classifier + the IC `decompose()`
  (between-coin selection vs within-coin predictive). Run it: prints the decomposition + decile tilt + grouped-CV AUC,
  saves `/tmp/funding_regime/funding_regime_panel.parquet` + `funding_regime_classifier.txt`.
- `market-tick-data-service/scripts/backfill_hl_funding_from_s3_asset_ctxs_2026_06_17.py` +
  `backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py` — the S3→GCS backfillers (extend for new data_types).

**WHAT WE FOUND (don't repeat; build on it):** funding≈adverse price (efficient); the apparent liquidity/venue regime
split is a **+0.31 between-coin SELECTION artifact**, genuine within-coin predictive IC ≈ **+0.02** (≈0); regime
classifier AUC **0.64** (modest); squeeze-end NOT predicted by slow daily features (persistence/extension/vol/ΔOI all →
continuation or flat). **DISCIPLINES:** (1) DEMEAN funding per-coin before any model — raw level encodes the
un-tradeable selection effect; (2) |IC|>0.15 is a red flag for a confound, not a win; (3) treat the regime as a weak
soft-conditioner. **CANONICAL caveat:** `perp_daily_ctx` is a research-grade (non-UAC, manifest-invisible) data_type —
canonicalize to `derivative_ticker` + register + manifest-track BEFORE any production features-service/strategy-service
pipeline depends on it.

**THE TASK (for the ML agent):** combine your own features + better predictions with the funding features above; raise
the **within-coin (demeaned)** predictive IC (the only honest target); build the squeeze/reversal classifier from the
FASTER signals (funding inflection, L2-book imbalance from the HL archive, OI dynamics) since the slow features are
confirmed non-predictors; then WIRE + TEST in the production spine — features in `features-service` (feature registry),
signal in `strategy-service` (`CarryStakedBasisRankAllocator`), data via `market-tick-data-service` — to see how far we
actually are toward production. Paste `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of any sub-agent spawn.

## Cross-venue REVERSION book — deployable, DD-control, cross-venue filters (2026-06-18, all CAUSAL/no-lookahead)

Extends Pass-B's Binance funding-rank reversion to a live-API multi-venue book + risk overlays + cross-venue signal
filters. Every signal lagged (`.shift(1)`), trailing windows only, fixed thresholds (not fit). Non-compounded
(`cumsum`). Scripts (throwaway, `/tmp`): `build_multivenue.py` (per-venue live-API pull + combine + plot),
`dd_filters.py` (beta/corr/vol filters + vol-target + beta-hedge), `anomaly_filter.py` (cross-venue funding dispersion),
`sizing_test.py` (sizing schemes). Plots served `/tmp/passB/*.html`.

**1. Multi-venue deployable (Pass-B's 30-survivor universe, live-API per venue, 2022→2026, 5bp).** Per-venue Sharpe:
**Binance +1.53 / Bybit +2.06 / Aster +0.71** (Aster short history; OKX dropped on a coverage filter). Reproduces
Pass-B's survivor-only ~1.52 → sound. Combined (Binance+Bybit, mean pairwise corr **0.67**): equal +1.96, causal
inverse-vol +1.98, **causal Sharpe-tilt +2.04** (≈ best-single Bybit 2.06). **Lookahead matters but is small here**:
full-sample Sharpe-tilt was +2.00 vs causal +2.04 — Bybit was _consistently_ best, so trailing-Sharpe tilt converges to
the same allocation. **Concentration:** causal tilt avg weight Bybit 58% / Binance 42%, **max single-venue 100%** (the
`max(Sharpe,0)`-normalize goes all-in when a venue's trailing Sharpe turns negative) → production needs a **per-venue
weight cap (~65%)**. Combined maxDD −18% (tilt) / −23% (equal) vs Binance-alone −34%. **Verdict: multi-venue buys
CAPACITY + robustness + lower-DD-vs-worst-venue, NOT a Sharpe lift — combining 2 venues at corr 0.67 ≈ best-single. A
real Sharpe lift needs 4+ comparable, less-correlated venues** (`S·√(N/(1+(N-1)ρ))`).

**2. HL-momentum cross-venue FILTER (operator idea — works).** HL funding is momentum; use it to veto the reversion
book's falling knives. Gentle veto (drop a long if its HL funding is in the bottom decile = HL says "keeps falling";
drop a short if top decile): Sharpe **1.64→1.77**, maxDD **−34%→−30%**. Dosing is a scalpel — q=0.2/0.33 over-filter
(remove good reversion candidates) and hurt Sharpe. **First real value from HL's (otherwise weak/losing) momentum signal
— as a cross-venue filter, not a standalone book.** Only covers HL-listed coins (26/30 here).

**3. DD CONTROL to ~10% — risk OVERLAYS win, coin-filters BACKFIRE (operator goal).** Diagnostic (per position-day, do
beta/corr/vol predict PnL?): **high-corr-to-BTC coins do BETTER (+15bp) / low-corr WORSE (−7/−23bp); low realized-vol
BEST (+18bp); beta weak.** So **beta/correlation FILTERS hurt** — beta≤1.2 → Sharpe 1.77→1.02/DD −52%; corr≤0.6 →
catastrophic (−122% DD). The "idiosyncratic/low-corr is cleaner" intuition is BACKWARDS for this book. **What works: (a)
BETA-HEDGE** (book is $-neutral but carries residual BTC-beta — long basket of crashed coins ≠ short basket's beta;
hedge by trading BTC sized to `−book_beta`) → Sharpe **1.77→2.03**, DD unchanged (removes market _noise_). **(b)
VOL-TARGET** (scale exposure to a trailing-vol budget) → the DD DIAL: 12% vol → DD −10%, Sharpe slightly up. **Combined
(HL-filter + beta-hedge + vol-target 10%): Sharpe 2.22, maxDD −7%, +27%/yr, Calmar 3.88 — the chosen base.** Dial
vol-target for the DD budget (18% → ~−15% DD/~+40%).

**4. Cross-venue funding-ANOMALY (operator idea — counterintuitive).** Is extreme funding on ONE venue (idiosyncratic)
vs ALL venues (broad consensus) different? Diagnostic (position PnL by Binance-funding outlier-ness vs Bybit/OKX/HL
consensus): **broad CONSENSUS reverts BETTER (+10bp); idiosyncratic single-venue outlier WORSE (−9bp)** — opposite the
first guess (when all venues agree on extreme funding it's genuine crowding that reliably unwinds; a Binance-only quirk
reverts in funding but not price). Weak (19bp spread) + over-filters as a hard gate → a mild _soft overweight_ on
consensus, not a lever.

**5. SIZING — inverse-vol already optimal; don't size by beta (operator idea).** On the chosen base: inverse-vol +2.22 ≈
corr-tilt +2.23 (correlation edge already absorbed by inverse-vol; explicit tilt = noise); **inverse-beta +1.83 /
beta-proportional +1.91 both LOSE** (beta = corr×vol/vol_btc mixes the helpful corr with the harmful vol). The one
refinement: **ivol×inverse-beta → Calmar 4.36, DD −6%, +28%/yr** (best DD-adjusted, slightly lower Sharpe 2.04) — use it
if minimizing DD-per-return beats raw Sharpe.

**Caveats across all:** survivorship-optimistic (currently-listed survivors, no dead coins → above the honest 1.44);
HL/anomaly filters only reach coins listed on the other venues (small-cap tail thinner); Aster short/recent; 2025-26
high-dispersion regime inflates recent years — underwrite ex-2026.

## TURNOVER reduction SOLVED + deployable book committed (2026-06-18, /autonomous, all CAUSAL)

Operator goal: harden the reversion book vs fees by cutting turnover ~2x WITHOUT losing >10% Sharpe, no look-ahead.
**Corrected baseline:** the final book (EWMA-7 + HL-veto + beta-hedge + vol-target) runs **0.70 turnover/day** (not the
~0.3 earlier mis-estimate — the HL-veto's daily flips + the 26-coin concentration drive it). Swept ~25 causal methods
(longer EWMA, hold-N, no-trade band, position-smoothing, rank-buffer hysteresis, L1 flip-gate, combos), scored on
turnover + Sharpe@5bp + **Sharpe@10bp** + DD. **WINNER — and it BEATS the constraint (Sharpe rises, not falls):**

| config                                           | turnover        | Sharpe@5bp | Sharpe@10bp      | DD@10 |
| ------------------------------------------------ | --------------- | ---------- | ---------------- | ----- |
| base EWMA-7                                      | 0.70            | +2.22      | +1.78            | -7%   |
| **EWMA-21 + rank-buffer+6 + no-trade-band 0.03** | **0.27 (-62%)** | **+2.34**  | **+2.16 (+21%)** | -7%   |

Mechanism: the book's churn was mostly NOISE (daily rank flips with no signal). Three cheap causal filters — slower
EWMA-21, rank-hysteresis (keep a name until it leaves the k+6 band), no-trade band (skip <3% weight changes) — strip the
noise trades that were pure fee drag, so the book IMPROVES at every fee level (the win compounds at higher fees). A
no-trade band of 0.02 alone is a free win (Sharpe@10bp 1.78→1.85). Single methods that over-smooth (hold-3d, pos-smooth
a=0.3) lose Sharpe; the combo of three light filters is the sweet spot.

**SHIPPED: `e2e-testing/scripts/defi/funding_reversion_crossvenue_book.py`** (lifecycle marker Epic strategy_master /
campaign / delete-when folded into CarryStakedBasisRankAllocator). Reproducible — pulls Binance funding+price live
(fapi, cached) + HL funding from GCS perp_funding; the full stacked book (EWMA-21 + buffer+6 + band 0.03 + HL-veto +
inverse-vol + beta-hedge + vol-target 10%), causal + non-compounded, with fee-sensitivity + HTML plot. **Full-history
2022-2026 (incl. 2022 bear + pre-HL period where the veto can't apply): Sharpe 2.17, maxDD -16%, +26%/yr, turnover
0.19/day, fee-robust to 20bp (Sharpe 1.78@20bp / 2.04@10bp).** The HL-window-only (2023-2026) is the stronger 2.34/-7%.
CLI knobs: `--ewma-halflife --rank-buffer --no-trade-band --hl-decile --vol-target --fee-bp`. Awaiting the other agent's
cross-sectional ML signals to improve winner/loser selection (not blocking).

## Robustness/OOS, 2022-DD attribution, directional squeeze overlay (2026-06-18, /autonomous, all CAUSAL)

**ROBUSTNESS/OOS of the book's turnover config (guards the meta-level overfit of selecting params on the full sample):**
neighbourhood of 45 configs around (EWMA-21,buffer-6,band-0.03) spans Sharpe@10bp 1.66-2.23 (median 1.88; only 31%

> =2.0; winner 2.04) — ALL positive (no fragile spike) but with real variation. True OOS split @2024-03-26: train-best
> applied UNCHANGED to held-out test = +2.20; the winner is positive on BOTH halves (1st +1.60 / 2nd +2.51). **Verdict:
> generalises, NOT overfit — but the honest FORWARD Sharpe is ~1.6-1.9 @10bp (the OOS-1st-half / neighbourhood median),
> NOT the 2.34 headline** (the 2nd-half strength rides the 2025-26 dispersion). Size on the conservative end.

**2022 DRAWDOWN attributed (operator: coin/venue/market-down/volume/turnover?):** the -16% maxDD (peak 2022-05-12 +20%
-> trough 2022-12-02 +4%, 204 days, ~10mo to recover) is **NONE of those** — it is a BROAD cross-sectional REVERSION
FAILURE. Worst-3 coins = only 37% of losses (BROAD, not concentrated); beta-hedged +7% vs un-hedged +9% (NOT market beta
— removing BTC beta doesn't help); flat across vol quartiles (NOT liquidity); fee drag -0.9% (NOT turnover). The LONG
leg (buying oversold coins) bled **-119% gross** while shorts made +103% — in the relentless 2022 bear (LUNA/FTX) the
reversion premise inverted (oversold kept falling = falling knives) ACROSS the universe. **Critically the HL-veto was
INACTIVE all of 2022 (HL data starts mid-2023)** — the live book's veto specifically targets this, so the -16% is a
worst-case un-vetoed number; HL-era (2023-2026) DDs are -3 to -7%. A relentless bear is the strategy's structural tail
risk (the long leg catches knives) — size for it.

**DIRECTIONAL SQUEEZE-PROTECTION overlay (CeFi agent handoff `…/overlay/`, validated on MY book):** rule = cut/halve a
funding leg on a > threshold-sigma 2-day move AGAINST it (long crashing sigma<-thr / short squeezing sigma>+thr) — the
rare extreme (|sigma|>2 fires ~3% of days). The agent's other signals are dead ends (reversal alpha-blend HURTS, horizon
mismatch; ML IC +0.001) — ONLY this risk overlay is accretive, confirmed on my book. Swept 2.0-3.5 x halve/cut: **all
thresholds help, none hurt; 2.0sigma best on MY (faster, vol-targeted) book** (vs their 2.5 floor). With the agent's
richer signal: Sharpe 2.17->2.28, maxDD -16->-14%, 2022 +0.50->+0.98. **SHIPPED self-computed** (sigma_move_2d = 2-day
return / rolling-30 vol, lagged — live-able, corr +0.49 to theirs, weaker but self-contained): Sharpe 2.17->2.21, maxDD
**-16->-13%**, Calmar 1.66->2.04, 2022 +0.50->+0.58. Wired into
`e2e-testing/scripts/defi/funding_reversion_crossvenue_book.py` as overlay 8 (`--squeeze-threshold` default 2.0 /
`--squeeze-factor` 0.5, default ON; richer external signal substitutable). `reversal_z` is CONTEXT only (naive rule
loses — not wired). Awaiting any future cross-sectional ML signals to strengthen winner/loser selection (not blocking).

## Multi-venue capacity + capped allocator (2026-06-18, /autonomous terminus)

Ran the FULL overlay stack (EWMA-21 + buffer-6 + band-0.03 + HL-veto + inverse-vol + beta-hedge + vol-target + squeeze)
on each arbitraged venue over the 30-survivor universe, combined with a CAUSAL weight-capped Sharpe-tilt. Per-venue:
Binance ~2.2/-13% · Bybit +1.93/-8% · Aster +1.03/-12% (short history, adds capacity). **Combined (Binance+Bybit, corr
0.63): equal-weight Sharpe 2.29 / DD -10%; capped-tilt 2.18 / -9% — both BEAT single-Binance (2.21/-13%) on BOTH axes.**
Multi-venue diversifies the 2022-heavy Binance tail against Bybit (less 2022 exposure) → cuts DD -13%->-10% AND nudges
Sharpe up, plus 2-3x capacity. **Refines the earlier "capacity-not-Sharpe": with the full overlay stack + a 2022-heavy
lead venue, multi-venue helps modestly on Sharpe and meaningfully on DD.** Equal-weight is the best allocator (venues
comparable → tilt adds noise); the cap is a SAFETY RAIL (prevents 100% concentration), not a Sharpe driver. **Cap-logic
refinement for production: a 2-venue cap of X needs floor = 1-X to truly bind (clip+renorm alone gave 87% realized at
cap 65%).** Research script `/tmp/multivenue_capped.py`; plot `multivenue_capped.html`.

- [ ] [STRATEGY] P2. Productionise the multi-venue capacity book: extend `funding_reversion_crossvenue_book.py` to pull
      Bybit/OKX/Aster (live APIs) + run per-venue + combine with an equal-or-capped allocator (floor=1-cap), for
      capacity + the DD-diversification benefit. **Repo: e2e-testing → strategy-service.**

### /autonomous loop terminus (2026-06-18)

Turnover-reduction dispatch + the CeFi directional-signal handoff are both COMPLETE and shipped. Final deployable book
(`funding_reversion_crossvenue_book.py`, e2e@198ee62): stacked causal overlays, turnover 0.19-0.23/day, Sharpe ~2.2
(honest forward ~1.6-1.9 per OOS), maxDD -13% (single) / -10% (multi-venue), Calmar ~2.0, fee-robust to 20bp, 2022-tail
repaired by the squeeze overlay. Remaining winner/loser improvement is BLOCKED on the awaited cross-sectional ML signals
(external dep) — loop terminates here, not idle-spinning.

## Multi-venue CAPITAL flow + transfer instructions + reversal_z verdict + signal-status CORRECTION (2026-06-18)

**CAPITAL accounting (operator: account for $ per venue + transfer instructions + plot the $ balance).** Sim: $1M total,
equal-weight across Binance+Bybit, PnL accrues per venue, weekly rebalance to equal-weight of equity with a 5% no-move
band. **Result: $1M -> $3.08M over 4.5yr (compounded); per-venue today Binance $1.62M / Bybit $1.46M; only 8 transfers
in 4.5yr, ~$75k/yr moved (avg $42k/move) — multi-venue capital friction is NEGLIGIBLE** (the band + 0.63
venue-correlation make rebalancing rare). Current instruction: move $78k Binance->Bybit to re-equalise to $1.538M each.
Transfer log is concrete (date + direction + $) — ready to wire into a TransferIntent flow. Script
`/tmp/capital_flow.py`; plot `/tmp/passB/capital_flow.html` (per-venue $ balance + transfer bars). Composes with
client-funds-isolation (`TransferIntent.client_id`) — these are intra-client multi-venue moves.

- [ ] [STRATEGY] P3. Productionise the multi-venue capital/transfer layer: emit weekly rebalance TransferIntents
      (intra-client, single client_id) from the live per-venue balances vs target weights, 5% no-move band. **Repo:
      e2e-testing -> execution-service TransferCoordinator.**

**reversal_z overlay — TESTED on my book, does NOT help (confirms the CeFi agent).** The economically-sensible use
(reduce a short when reversal_z says oversold/squeeze-prone) HURTS: Sharpe 2.21->1.99/2.17, 2022 +0.58->+0.34. The
opposite sign nominally adds +0.07 (2.28) but is economically BACKWARDS (cuts positions when the reversal signal is
FAVOURABLE to them) = overfit-from-trying-both-signs, not a real edge. NOT shipped (agent warned context-only).

**SIGNAL-STATUS CORRECTION (supersedes the earlier "blocked on awaited ML signals").** The signals are in GCS
(`…/overlay/`) and have been TESTED — there is no better winner/loser signal coming: (a) the CeFi agent's actual
cross-sectional ML signal (15m ensemble, daily-aggregated) HURTS the reversion carry (cs-veto 0.55 / cs-halve 0.77 /
standalone -1.08 on theirs) and does NOT cut the single-coin tail; (b) reversal alpha-blend HURTS (horizon mismatch, the
carry already harvests reversion); (c) reversal_z HURTS on my book (above). STRUCTURAL reason: cs/reversal are REVERSION
signals — the WRONG tool for squeeze/dump avoidance (they lean INTO a squeeze). The ONE transferable accretive overlay
is the MOMENTUM/breakout `sigma_move_2d` squeeze veto — **already shipped** (e2e@198ee62). **The book is COMPLETE, not
blocked.** The CeFi cs alpha is real but 15-min-only — genuinely no value at the daily funding-carry horizon.

## Capital-flow CORRECTION — fixed-leverage moves ~4x more (operator 2026-06-18)

The earlier "$75k/yr moved" was the FULL-FUNDING regime (post full capital, let PnL compound in place, rebalance only on
weight drift) — which minimises transfers but lets LEVERAGE FLOAT DOWN as you profit (under-deployed, idle capital).
Re-modelled FIXED-LEVERAGE (hold each venue's deployed capital flat, sweep PnL gains to a central treasury / top up
losses weekly, 5% band) per the operator's point that exposure + margin must be held: **$302k/yr moved (4.0x more,
~30%/yr of capital ~= the book's PnL flow)** — gains swept out (margin would balloon + de-lever), losses topped up.
Treasury accumulates ~$1.15M of swept PnL on a $1M base (redeploy / yield). **Tradeoff is leverage policy:**
full-funding = fewer transfers but drifting-down leverage + idle capital; fixed-leverage = ~4x transfers (still cheap —
weekly stablecoin sweeps, near-zero fee) but capital-efficient + constant exposure (the regime you'd actually run). The
P3 TransferIntent todo should emit the FIXED-LEVERAGE weekly sweep/top-up (not the full-funding drift-rebalance).
Scripts `/tmp/capital_flow{,2}.py`; plots `capital_flow.html` (full-funding) + `capital_flow_fixedlev.html`
(fixed-leverage + treasury).

## Capital/leverage module + paper-trading runner + return convention (2026-06-18, /autonomous)

**Return convention (operator-confirmed):** the book's % returns are on the NET capital / posted margin (the weights sum
to +1 long / -1 short = 1x net, 2x gross notional), NOT on the gross $ — so +27%/yr is on net (~half on gross). It is
NON-COMPOUNDED: fixed notional sized to the INITIAL capital (vol-targeted to constant 10% vol on that fixed base), PnL
not reinvested -> linear returns + profit accrues to treasury separately. **Vol-target DE-LEVERS the gross** from the
raw 2.0x to ~0.9x avg (0.66x on 2026-06-18), so the book is UNDER-deployed at 10% vol -> only ~18% margin needed, ~82%
free; raising `--vol-target` deploys toward the full 2x for proportionally more return + DD (the "fixed size" is a dial,
fixed per chosen vol target).

**SHIPPED `funding_reversion_multivenue_capital.py` (e2e@0751d27):** plots gross leverage (raw 2x -> vol-targeted ~0.9x,

- 1x-net reference line), margin posted per venue, FREE capital, TREASURY of swept PnL ($1.15M on $1M), and both capital
  regimes (full-funding $75k/yr transfers vs fixed-leverage $302k/yr ~ the PnL flow). CLI
  `--capital --vol-target --max-leverage --dd-buffer`. Plot `funding_capital_book.html`.

**SHIPPED `funding_reversion_paper_trade.py` (e2e@fd96c0b):** the live desired-state engine (the secondary/CLI PAPER
path). Pulls live funding+price per venue (Binance fapi + HL GCS + Bybit/Aster live), computes today's desired positions
(full causal stack, vol-targeted to actual ~0.66x gross), emits per coin/venue: side, weight, $ notional, the coin's
funding yield; net funding carry (+13%/yr on deploy); margin/free per venue; persists `desired_positions.json`. NO real
orders. Daily runs accrue the transfer + paper-PnL ledger. **This wires the book to paper trading** — the production
path (fold into strategy-service `CarryStakedBasisRankAllocator` + promote paper->live VM) stays operator-gated.

The full deployable stack is now 3 committed e2e scripts: `funding_reversion_crossvenue_book.py` (backtest, 8 causal
overlays), `_multivenue_capital.py` (capital/leverage/treasury), `_paper_trade.py` (live paper engine).

## Ensemble orchestrator engine + productionization plan (2026-06-18, /autonomous)

**SHIPPED `funding_ensemble_engine.py` (e2e@5859ec0):** the orchestrator across all 4 strategies + per-venue capital +
liquidation. (1) funding-dispersion
($-neutral perp), (2) funding-rate arb (delta-neutral short-perp/long-spot on top
+funding), (3) pure-basis (delta-neutral on perp-spot premium), (4) staked-basis FULLY WIRED — long LST + short perp on
an LST-collateral venue, LIVE LST APRs (Lido stETH 2.4% @Bybit + ETH funding; jitoSOL 8% @Drift + SOL funding ->
+14.1%/yr net). Restricted to the 30-coin liquid survivor universe (avoids the live 754-perp micro-cap / garbage-basis
pollution). Prints + plots per strategy + ensemble: target positions (coin/venue/side/notional/funding/staking),
**$
balance required PER VENUE** (spot cash + perp margin + on-chain LST — e.g. $1M -> Binance $650k / Bybit $167k / Drift
$167k), and **LIQUIDATION proximity per perp leg with ALERTS\*\* (dist<25% OR margin<3x maint; OK at 3x, min dist 33%).
`DATA_SOURCE=live|gcs_complete` env (gcs_complete reads the dumped canonical data to avoid live gaps). Plot
`funding_ensemble.html`. Insight: the delta-neutral basis strategies are CASH-heavy (long-spot/LST leg ties up full
notional) vs the margin-light perp-only dispersion — the per-venue balance shows it.

**The full deployable RESEARCH->PAPER pipeline is now 5 committed e2e scripts:** `funding_reversion_crossvenue_book.py`
(backtest, 8 overlays), `_multivenue_capital.py` (capital/leverage/treasury), `_paper_trade.py` (live paper engine),
`funding_ensemble_engine.py` (4-strategy orchestrator), `funding_regime_classifier.py` (ML regime decomposition).

**PRODUCTIONIZATION PLAN (strategy-service fold — operator permission GRANTED 2026-06-18; the careful
live-trading-system build, sequenced next):** integration points found —
`strategy_service/engine/strategies/v2/carry_and_yield/` (`staked_basis.py`, `basis_perp.py`, `basis_dated.py`,
`staking_simple.py` already exist; ADD `funding_dispersion.py` for the $-neutral reversion archetype + the 8 overlays),
the portfolio_allocator/allocation_sizer (wire the ensemble SPLIT weights), and
`StrategyServiceConfig(UnifiedCloudConfig)` for the **complete-data env mode** (a typed config field reading the dumped
canonical GCS data — HL perp_funding/derivative_ticker/lst-rates — NOT live, to dodge the small-cap gaps; NO os.getenv).
Requires the strict strategy-service QG + the manifest-allocation-guard tests + the paper->live promote workflow. This
is a multi-file live-trading-system integration — done as a focused build, not rushed; the shipped paper/ensemble engine
is the validated foundation + a runnable paper path TODAY.

- [ ] [STRATEGY] P1. Fold the funding-reversion + ensemble into strategy-service v2 carry_and_yield + allocator with a
      complete-data DATA_SOURCE config mode (reads dumped GCS canonical data). **Repo: strategy-service.** (perm
      granted)
- [ ] [INFRA] P2. Launch the paper VM + daily cron running the paper/ensemble engine (verify per no-fire-and-forget).
      **Repo: deployment-service.** (perm granted)

## Basis archetypes split + LIVE venue/coin coverage gap (operator 2026-06-18)

**Dated basis fixed + basis split into TWO archetypes (e2e@5ba85b8):** `spot_perp_basis` (delta-neutral long-spot/
short-PERP = the funding capture; perp basis ~= 0, realised as funding) vs `dated_basis` (delta-neutral long-spot/
short-QUARTERLY-future = cash-and-carry, annualised basis CONVERGES at expiry — live BTC +3.8% / ETH +6.4%/yr). The v1
conflated them on perps (where basis ~= 0). Now separate in the individual output, ensemble, and per-venue/liquidation.

**HONEST coverage gap (operator: "we're missing loads of venues and coins vs backtest for live; did we evaluate all"):
NO — we did not evaluate all venue x coin, and the LIVE ensemble is narrower than even the backtest.**

- Backtest: Binance DEEP (30 survivors), Bybit/OKX MAJORS-only, Aster 14 coins live, HL full-230 (-> momentum, excluded
  from reversion), Deribit too-few-perps. NOT exhaustive (no full per-venue universe except HL).
- Live ensemble (current): **Binance-only, 30 survivors** (+ Bybit/Drift for staked-basis). Doesn't span the arbitraged
  venues the reversion was confirmed on, nor the broad coin set.

- [ ] [STRATEGY] P1. Expand the LIVE ensemble to MULTI-VENUE x BROAD universe: bulk live snapshots per venue (Binance
      premiumIndex, Bybit /v5/market/tickers, Aster fapi — all return funding+mark in one call; OKX funding is
      per-inst), run dispersion + spot_perp_basis per venue on each venue's top-volume liquid universe (not just 30
      survivors), keep dated_basis (Binance quarterly) + staked_basis (Bybit/Drift). Per-venue balances + liquidation
      already generalise. **Repo: e2e-testing.** (the venues/coins gap)
- [ ] [STRATEGY] P1. Backtest-coverage completion: evaluate the full per-venue universe on Bybit/OKX/Aster (not just
      majors) so live coverage is backed by backtest evidence per venue x coin. **Repo: e2e-testing.**
