---
doc_type: plan
title: >-
  Solana perp DEX build-out — Jupiter perps + Kamino borrow (LST carry), plus Pacifica re-integration (funding/basis)
summary: >-
  Two independent Solana perp-venue tracks, both gated by the 2026-07-16/2026-08-14 operator rulings on
  /codex/04-architecture/solana-defi-coverage.md. (1) Jupiter perps + Kamino borrow restores Solana LST carry — Jupiter
  alone cannot (JLP custodies only SOL/ETH/BTC/USDC/USDT/JupUSD, no LST margin), so the structure is
  LST-at-Kamino/borrow-a-stable/post-as-Jupiter-perp-margin (`CARRY_RECURSIVE_STAKED`), gated on an economics question
  answered from our own corpus BEFORE any code: is the stablecoin borrow rate reliably below the staking yield? (2)
  Pacifica re-integration restores a genuinely different Solana perp venue — real hourly-settled funding rates (unlike
  Jupiter's borrow-fee/utilization model), USDC-only margin (same as Jupiter — neither restores LST staked-basis), and
  most of the code EXISTED before the 2026-07-16 cull deleted it (resurrect from git history, don't rebuild from
  scratch), except execution-service which never had a Pacifica protocol. Also generalises borrow-venue selection to be
  coin-agnostic and closes registry gaps found while auditing.
status: draft
nature: process
asset_group: [defi]
stage: [meta]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    defi,
    solana,
    carry,
    staked-basis,
    funding-dispersion,
    collateral,
    jupiter,
    kamino,
    pacifica,
    lending,
    venue-onboarding,
  ]
related:
  [
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /codex/04-architecture/solana-defi-coverage.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-08-12
last_updated: "2026-08-14"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 15.4
assigned_role:
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-12 (Jupiter+Kamino scope). Operator instruction: "we should add Jupter and Kamino so that
  staked basis works on kamino and abiss on solana", scoped to full integration across repos after auditing what already
  exists ("these aren't new venues"). Extended 2026-08-14: operator asked to use "Pacifica and Jupiter" for a Solana
  perp funding/basis trade; the resulting audit found the 2026-07-16 cull killed Pacifica alongside Drift with no
  evidence Pacifica itself was compromised, surfaced that conflict, and the operator ruled "jupiter and pacifica please"
  (recorded as a formal reversal banner in /codex/04-architecture/solana-defi-coverage.md) — then explicitly chose to
  fold Pacifica into this plan rather than a separate one.
---

# Solana perp DEX build-out — Jupiter perps + Kamino borrow, plus Pacifica re-integration

**Why this plan exists.** The 2026-07-16 operator ruling dropped every Solana perp DEX, leaving
[Plan B empty](/codex/04-architecture/solana-defi-coverage.md). The SOL-side staked-basis bundle emitted **zero eligible
(LST, perp_venue) pairs** from that date until this plan's Jupiter track lands. **2026-08-14**: a second operator ruling
reversed the Pacifica portion of the cull (`/codex/04-architecture/solana-defi-coverage.md`'s 🟢 REVERSAL banner) —
Drift stays removed (real $285M hack, DPRK-attributed, unproven Velocity DEX relaunch), but Pacifica is re-authorized.
This plan now covers both tracks:

- **Track 1 — Jupiter perps + Kamino borrow** restores Solana LST carry via `CARRY_RECURSIVE_STAKED`.
  §A/§B.1/§C.1/§D.1/§E.1.
- **Track 2 — Pacifica re-integration** restores a real funding-rate perp venue for funding-dispersion/straight-basis
  archetypes (not staked-basis — see the collateral finding in §A.2). §A.2/§B.2/§C.2/§D.2/§E.2.

> **This plan does NOT itself add any code for either track's default state.** `status: draft` reflects that Track 1 is
> still gated on §A's economics question, and Track 2's live-capture design is gated on §A.2's credential-status
> re-verification. **Flip to `active` only once both gates resolve** (or once the operator explicitly says to proceed
> regardless).

**Status of Track 1 venues — audited 2026-08-12, neither is new.**

| Surface                    | Jupiter                                                       | Kamino                                                       |
| -------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------ |
| UAC collateral policy      | ❌ absent (no row in either registry)                         | ✅ `CollateralPolicy`, `lending`, JitoSOL/mSOL @15% haircut  |
| UAC params contract        | ❌ none for perps                                             | ✅ `KaminoBorrowParams` **already exists**                   |
| instruments-service        | ✅ adapter — but emits `SPOT_PAIR` only                       | ✅ adapter + factory + defi orchestrator                     |
| market-tick-data-service   | ✅ live connector shipped 2026-08-08 (`jupiter_solana_ws.py`) | ✅ `solana_defi_amm` handler; `lending_indices` from 2023-06 |
| execution-service          | ✅ swap-only (`get_swap_quote` / `execute_swap`)              | ✅ `supply`/`withdraw` — **no `borrow`/`repay`**             |
| strategy-service catalogue | ❌ not a perp-hedge venue candidate                           | ❌ not wired as a borrow venue for staked structures         |

So Track 1 is **two narrow additions on top of substantial existing integration**: Jupiter's **perp** surface, and
Kamino's **borrow** surface.

**Status of Track 2 (Pacifica) — audited 2026-08-14, mostly a RESURRECTION, not a rebuild.** Everything below was real,
working code that the 2026-07-16 cull deleted (not "never built"):

| Surface                          | Pacifica — pre-cull state (git history)                                                                                                                                                                                                       |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UAC collateral policy            | ❌ never existed — net new                                                                                                                                                                                                                    |
| instruments-service              | ✅ existed, deleted `instruments-service@dee3f6a4` — curated top-10-coin adapter (no public markets endpoint at the time; re-verify, docs now describe 20+ markets)                                                                           |
| market-tick-data-service (batch) | ✅ existed + WORKING, deleted `market-tick-data-service@2e674d1f` — full REST adapter (`_umi_pacifica.py`, 495 lines): trades, book snapshots, candles, against `https://api.pacifica.fi/api/v1`                                              |
| market-tick-data-service (live)  | ⚠️ existed but was a **BLOCKED-CREDENTIALS scaffold**, never activated — `wss://ws.pacifica.fi/v1` required a paid Helius/Triton RPC key + Pacifica partner header as of 2026-07-06. **Re-verify before assuming this is still true** (§A.2). |
| execution-service                | ❌ never existed — net new (checked: zero Pacifica commits in execution-service history)                                                                                                                                                      |
| strategy-service catalogue       | ❌ never wired as a perp-hedge venue candidate                                                                                                                                                                                                |

**The structure, and why Jupiter perps is not `CARRY_STAKED_BASIS`.** Verified against Jupiter's own documentation
(`developers.jup.ag/docs/perps/`, fetched 2026-08-12): the JLP pool custodies exactly **SOL, ETH, BTC, USDC, USDT,
JupUSD**, and collateral is side-dependent — _"SOL / wETH / wBTC for long positions"_, _"USDC / USDT for short
positions"_. No LST anywhere. A short therefore **cannot** be margined with JitoSOL. The structure that does work:

```
JitoSOL/mSOL ──deposit──▶ KAMINO (lending, 15% haircut, keeps staking yield)
                              │
                              └──borrow stable──▶ JUPITER perps ──▶ SHORT SOL (USDC/USDT margin)
```

That is **`CARRY_RECURSIVE_STAKED`** (stake → borrow against → hedge), not `CARRY_STAKED_BASIS` (LST posted directly as
perp margin). `CARRY_STAKED_BASIS` remains structurally unavailable on Solana and this plan does not change that.

**Pacifica has the same collateral conclusion, for a different reason.** Pre-cull adapter code (both instruments-service
and MTDS) confirms Pacifica is **USDC unified-margin, linear contracts only** — no coin-margined/inverse product, and
critically **no LST accepted as margin either**. So Pacifica does not restore `CARRY_STAKED_BASIS` any more than Jupiter
does. What Pacifica DOES add that Jupiter doesn't: **real hourly-settled funding rates** (recalculated every 5s per
current `docs.pacifica.fi`) — Jupiter perps has **no funding-rate mechanism at all**, traders pay hourly borrow fees
based on position size and pool utilization instead. If the goal is a classic funding-rate basis/dispersion trade,
Pacifica is the structurally correct venue; Jupiter is not (it would need a different signal — borrow-fee/utilization
spread, not funding rate).

**Per-archetype venue selection already exists** — confirmed 2026-08-12: `recursive_staked.py` already reads
`staking_protocol`, **`lending_protocol`** and `perp_venue` as params, and `staked_basis.py` reads `staking_protocol`,
`perp_venue`, `spot_venue`. No new selection mechanism is needed for Track 1; Track 2 needs Pacifica added as a
`perp_venue` candidate for funding-dispersion/straight-basis archetypes only (§E.2).

**Codex SSOTs each change is checked against:** [solana-defi-coverage](/codex/04-architecture/solana-defi-coverage.md) ·
[carry-recursive-staked](/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md) ·
[carry-funding-dispersion](/codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md) ·
[tier-and-import-architecture](/codex/04-architecture/tier-and-import-architecture.md) ·
[defi-canonical-naming-ssot](/codex/02-data/defi-canonical-naming-ssot.md) ·
[gcs-and-manifest-delete-safety-protocol](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)

## A.1 Jupiter/Kamino economics gate — answer this BEFORE writing Track 1 code

The operator's own framing: _"is usdc borow cheaper than solana staking yield generally? check some history. if so worth
doing else not worth it."_ That is the correct gate — the trade's carry is `staking_yield − borrow_cost − perp_funding`,
so a borrow rate above the staking yield makes it structurally unprofitable regardless of how well it is built.

**We already hold the data.** `VENUE_DATA_TYPE_CAPABILITIES` advertises `lending_indices` for `KAMINO-SOLANA` from
**2023-06-01**, `SOLEND-SOLANA` from **2022-11-01** and `MARGINFI-SOLANA` from
**2025-01-01`**; ETH-side comparators are deeper still (`AAVE_V3-ETHEREUM`from 2023-01-27,`LIDO-ETHEREUM` `staking_yields`
from 2020-12-18).

- [ ] [AGENT] P0. **Compute the historical spread `SOL staking yield − Solana stable borrow rate` across the full
      available window** (Kamino 2023-06 → now; add Solend from 2022-11 for a longer baseline). Report: mean, median,
      percentage of days positive, worst drawdown of the spread, and behaviour during SOL volatility spikes. **Deliver a
      go/no-go recommendation, not just numbers.** Heavy corpus reads run on a VM in-region, never locally
      (`/codex/05-infrastructure/vm-launcher-runbook.md`).
- [ ] [AGENT] P0. **Do the same for the ETH leg and compare.** The operator noted the borrow-against-LST idea applies to
      ETH staked basis too, and the ETH data is materially deeper (Lido staking yields to 2020-12, Aave to 2023-01). If
      the ETH spread is better AND the venues are already integrated, **ETH is the cheaper first shipment and Solana
      should follow it** — say so explicitly if the numbers support it.
- [x] [AGENT] P0. ✅ **NOT blocked on data — CORRECTING my own earlier claim.** I previously wrote that the SOL answer
      might be `BLOCKED-DATA` because the only Solana `staking_yields` venue advertised is `JITORESTAKING-SOLANA`
      (2024-08-01, and that is Jito **restaking**, not LST yield). **That was wrong, because I read the capability
      registry instead of the services.** Both legs are collected: - **SOL staking yield** — MTDS `lst_rates_handler.py`
      covers **MARINADE / mSOL** (alongside stETH/wstETH/rETH/weETH), and `staking_yields_handler.py` covers **JITO**
      (alongside LIDO/ETHERFI/EIGENLAYER). - **Solana stable borrow rate** — `_lending_grain.py` routes `kamino_lending`
      / `solend` / `marginfi` to `InstrumentType.SOLANA_LENDING`, and `_solana_defi_fetch.py` emits `lending_indices`. -
      **Funding** — features-service has `perp_funding_rates.py` (CeFi) and `perp_funding_rates_defi.py` (on-chain). So
      § A.1's spread IS computable and the go/no-go analysis can proceed on real history.
- [x] [AGENT] P2. ✅ **WITHDRAWN — there is no registry drift. I probed the wrong vocabulary, twice.** I claimed
      `VENUE_DATA_TYPE_CAPABILITIES` "under-declares its own handlers" and the operator instructed me to update it. **No
      update was made, because the registry is correct.** SOL LST yield is declared under the data type **`lst_rates`**,
      not `staking_yields`:

      | Venue                  | Declared                                        |
                      | ---------------------- | ----------------------------------------------- |
                      | `MARINADE-SOLANA`      | `lst_rates` from **2021-08-01**                 |
                      | `JITO-SOLANA`          | `lst_rates` from **2021-11-01**                 |
                      | `SOLBLAZE-SOLANA`      | `lst_rates` from 2022-10-15                     |
                      | `JITORESTAKING-SOLANA` | `staking_yields` — restaking, correctly distinct |

                      `lst_rates_handler.py` writes **both** `lst_rates` and `staking_yields`, so the vocabulary split is deliberate and the
                      registry matches the handler exactly. The split is also semantically right: `lst_rates` is the LST exchange-rate/APY
                      series, `staking_yields` is protocol staking APY.

                      **Third correction on the same question, so the lesson is the point, not the fact:** my first verdict was
                      "possibly BLOCKED-DATA" (from reading the registry for the wrong key), my second was "the registry is wrong"
                      (from finding the handlers and still not re-checking the registry with the right key), and the truth is that both the
                      registry and the handlers were right all along. This is exactly the failure
                      `/codex/02-data/four-surface-reconciliation-procedure.md` warns about — **an absence result is evidence ONLY once you
                      have confirmed you probed the vocabulary the WRITER actually emits.** Before declaring any data absent, enumerate the
                      data types the writer emits and grep for those, never for the name you expect.

          **Consequence for § A.1, in the good direction:** SOL LST history starts **2021-08**, roughly 22 months EARLIER than
                      Kamino's `lending_indices` (2023-06). So the binding constraint on the Solana spread is the **borrow** series, not the
                      staking series, and the full Kamino window is computable. ETH remains deeper (Lido `staking_yields` 2020-12-18) but
                      Solana is in no way blocked.

- [ ] [AGENT] P0. **Use `lst_rates`, NOT `staking_yields`, for the § A.1 spread — they measure different things.**
      Measured 2026-08-12; recorded here because § A.1's answer is wrong if the wrong series is used.

      | | `lst_rates` | `staking_yields` |
                      | --- | --- | --- |
                      | `instrument_type` | `lst` | `staking` |
                      | Payload | `exchange_rate` (float64, **non-null**) | `apy` + `total_staked` (nullable) |
                      | Source | **on-chain** — contract / `exchangeRate` / `getPooledEth` / subgraph | **reported** — `yields.llama.fi/pools`, `LIDO_APY_URL`, `ETHERFI_APY_URL` |
                      | Meaning | The LST's redemption rate; **drift over time IS realised accrual** | A published forward-looking APY |
                      | Venues | 14 LST issuers | 26, mostly vaults + restaking |

                      **The axis is reported-vs-measured, not protocol-native-vs-DEX-swapped** (a hypothesis considered and rejected), and it
                      is not about token mechanics either — rebasing vs price-appreciating cuts across both. For a staked-basis P&L you want
                      the **measured** series, because exchange-rate drift is the yield actually earned rather than the number a protocol
                      advertises. `sim_schemas.py` already does exactly that: `stake_apy_bps  # staking yield from MTDS lst_rates`.
                      Only **three** venues declare both (LIDO, ETHERFI, PUFFER) — protocols that genuinely both issue an LST and run a
                      vault/restaking product, so the overlap lets you cross-check advertised against realised rather than being duplication.

- [ ] [AGENT] P1. **Compare LTV and borrow cost across the three Solana lending venues** (Kamino / Solend / MarginFi)
      and against Aave on the ETH side. Operator asked which has better LTV and lower stable borrow rates. **Note for
      the record: Aave has NO Solana deployment** — all 11 `AAVE_V3-*` keys are EVM chains — so Aave is not a candidate
      for the SOL borrow leg, only for the ETH version.
- [ ] [AGENT] P2. **Decide whether borrow-venue selection should be DYNAMIC.** The operator raised it explicitly ("if it
      fluctuates we could dynamically decide"). A rank allocator over lending venues by net spread is the existing idiom
      — `YIELD_ROTATION_LENDING_RANK` already ranks protocols by supply APY, so the mechanism exists and would be
      extended rather than invented. Gate on whether § A.1 shows the ranking actually changes hands often enough to pay
      for itself; a static best-venue choice is correct if it does not.

## A.2 Pacifica gate — re-verify credential status BEFORE designing live capture

The pre-cull live connector (`market-tick-data-service` history, deleted `2e674d1f`) was a **BLOCKED-CREDENTIALS
scaffold, never activated** — as of 2026-07-06 it documented `wss://ws.pacifica.fi/v1` as gated behind a paid
Helius/Triton-tier Solana RPC key plus a Pacifica partner authorisation header, with the free public tier not exposing
the aggregated tick channels needed for capture. **This session's fresh research (2026-08-14) found conflicting signal**
— Pacifica's own marketing/docs now describe "a comprehensive suite of REST and websocket API endpoints" with a Python
SDK, and `docs.pacifica.fi/api-documentation/api/websocket` reads like an openly-documented public API (idle-timeout and
max-connection-lifetime behaviour, not credential-gate language). **These are not necessarily the same claim** — public
documentation existing does not by itself prove the market-data channels are free-tier-accessible; the 2026-07-06
assessment could have been about a different/higher tier than what's now documented, or Pacifica genuinely opened it up.
**Do not build a live-WS design against either claim without re-testing the actual endpoint.**

- [ ] [AGENT] P0. **Re-test `wss://ws.pacifica.fi/v1` (or whatever the current WS host is per fresh docs) against the
      free/public tier with no special credentials.** Confirm whether `trades`/`book`/`ticker`-shaped channels are
      reachable without a paid RPC key or partner header. Report the exact result (which channels work, what auth if any
      is required) — this determines whether Track 2's MTDS live connector can be built for real or must stay a
      documented BLOCKED-CREDENTIALS scaffold like before.
- [ ] [AGENT] P1. **Confirm the REST base URL and symbol/margin facts still hold**: `https://api.pacifica.fi/api/v1`
      (mainnet), `https://test-api.pacifica.fi/api/v1` (testnet) per fresh docs — matches the pre-cull adapter's
      hardcoded base URL, good sign of stability, but re-verify a live `GET` succeeds and the response shape matches the
      deleted parser code (`_parse_pacifica_trades`, `_build_pacifica_book_row` — see git history,
      `market-tick-data-service@2e674d1f~1:market_tick_data_service/adapters/_umi_pacifica.py`) before assuming a
      straight restore.
- [ ] [AGENT] P2. **Check whether Pacifica now exposes a real `/markets` discovery endpoint.** The pre-cull adapter used
      a hand-curated top-10-coin list (`BTC, ETH, SOL, HYPE, XRP, DOGE, BNB, SUI, PUMP, FARTCOIN`) because "the API does
      not expose a public markets discovery endpoint" at adapter-authoring time (pre-2026-07-16). Fresh docs describe
      "20 or more perpetual markets" and a full REST suite — if a discovery endpoint now exists, resurrect the adapter
      to call it dynamically instead of re-hardcoding a stale curated list.

## B. Registry layer (UAC) — the correct first code change, and it needs no strategy edits

Doing this before any adapter work makes `_staked_basis_eligible()` / eligibility checks resolve Solana correctly on
their own: a venue-pair a policy doesn't accept is simply never emitted as a slot, so **the gating logic needs no change
at all.**

### B.1 Jupiter + Kamino

- [ ] [SCRIPT] P1. **Add Jupiter's `CollateralPolicy` to UAC `COLLATERAL_REGISTRY`** — `venue_id="jupiter"`,
      `venue_kind=PERP_DEX`, accepted collateral SOL/wETH/wBTC (long side) and USDC/USDT (short side), sourced to
      `developers.jup.ag/docs/perps/` with the fetch date. Include the JupUSD custody token or state why it is excluded.
      **Encode the side-dependence** — a flat accepted-token list would wrongly imply an LST-free long/short symmetry
      that does not exist, and would let a short slot resolve to SOL margin.
- [ ] [SCRIPT] P1. **Add Kamino rows to `VENUE_COLLATERAL_MATRIX`, or decide deliberately not to.** Today Kamino exists
      ONLY in `COLLATERAL_REGISTRY` (hand-sourced) because the matrix carries no LENDING rows at all. Adding a LENDING
      venue to a perp-shaped matrix may be wrong; the alternative is to keep LENDING out and document the split. **Pick
      one and write the reason down** — the current state is a real asymmetry that already cost an audit.
- [ ] [SCRIPT] P2. **Backfill the four missing PERP_CEX `CollateralPolicy` rows** — `ASTER`, `BITFINEX-FUTURES`,
      `BITGET-FUTURES`, `KRAKEN-FUTURES` have `VENUE_COLLATERAL_MATRIX` rows but no policy in `COLLATERAL_REGISTRY`, so
      their LTV/liquidation semantics are invisible to every registry consumer. **`ASTER` is a live funding-dispersion
      venue**, which makes it the priority of the four.
- [ ] [SCRIPT] P3. **Resolve the `haircut_pct` unit ambiguity.** The field name is identical in `CollateralAcceptance`
      (FRACTION, `0.075`) and `AssetHaircut` (WHOLE PERCENT, `7.5`), with a single ×100 conversion in
      `_ah_from_venue_collateral()`. Values agree exactly (verified 2026-08-12, all 12 shared perp rows) — this is a
      naming hazard, not a divergence, and a 100× collateral error is not a survivable class of bug. Rename one side
      (`haircut_fraction` / `haircut_whole_pct`) or add a typed wrapper. **Cross-reference comments + unit warning
      SHIPPED — Evidence: unified-api-contracts@8c7277b668** (`ALL QUALITY GATES     PASSED`, real exit 0, zero
      failures): both files now carry reciprocal SSOT pointers, the unit boundary is stated on both sides, and the
      coverage asymmetry is named. **The RENAME is what remains open** — comments reduce the odds of the 100× error,
      they do not remove it. Side-finding while shipping it: the `×` character is banned in docstrings by ruff `RUF002`
      (ambiguous-unicode) — write `x100`, not `×100`. Cost one gate cycle.

### B.2 Pacifica

- [ ] [SCRIPT] P1. **Add `PACIFICA-SOLANA`'s `CollateralPolicy` to UAC `COLLATERAL_REGISTRY`** — `venue_kind=PERP_DEX`,
      USDC-only margin (unified, cross OR isolated per docs), linear contracts (no coin-margined product), sourced to
      `docs.pacifica.fi` with the fetch date. This is a clean net-new registration (no pre-cull UAC row ever existed for
      Pacifica) — do not just copy the deleted adapter's assumptions without re-confirming against current docs.
- [ ] [SCRIPT] P2. **Re-register `PACIFICA-SOLANA` in `VENUES_BY_ASSET_GROUP["cefi"]`** (on-chain perp DEX classified as
      CeFi, matching the existing HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC cluster in
      `onchain_perp_batch_handler.py`) — check whether `_VENUE_SOURCE`/`_VENUE_PIPELINE_MODE`/`_VENUE_LAUNCH` need a
      Pacifica row added there too (deploy date 2025-06-01 per pre-cull adapter).

## C. execution-service

### C.1 Jupiter + Kamino

- [ ] [SCRIPT] P1. **Implement Kamino `borrow` / `repay`** in `defi_execution/protocols/kamino.py`. It currently has
      `supply` / `withdraw` / `get_reserves` / `get_vault_info` / `get_price` — the lending side only.
      **`KaminoBorrowParams` already exists in UAC**, so the contract is defined and this is an implementation against a
      settled interface. Without borrow there is no stable to post as perp margin and the structure cannot run.
- [ ] [SCRIPT] P1. **Add a Jupiter perps execution path.** `protocols/jupiter.py` is swap-only. Perp position open/close
      goes through the Jupiter Perpetuals program (`PositionRequest` → `Position` accounts per its docs), which is a
      distinct flow from `execute_swap`. Follow the existing DeFi protocol + `DefiErrorCode` conventions
      (`/codex/04-architecture/defi-execution-overview.md`).
- [ ] [SCRIPT] P2. **Health-factor monitoring for the Kamino borrow leg.** The recursive-staked structure carries
      liquidation risk on the borrow, which is what `LiquidationProximityCircuit` and the UAC
      `LIQUIDATION_PARAMS_REGISTRY` exist for. Kamino's `CollateralPolicy` must carry real `max_ltv` /
      `liquidation_threshold` / `liquidation_bonus` values (not the 15% haircut alone) or the breaker has nothing to act
      on.

### C.2 Pacifica

- [ ] [SCRIPT] P1. **Build `defi_execution/protocols/pacifica.py` from scratch.** Confirmed zero prior Pacifica commits
      anywhere in execution-service history — this is genuine net-new work, not a resurrection. REST base
      `https://api.pacifica.fi/api/v1` (order endpoints: `POST /orders/create`, `POST /orders/create_market` per fresh
      docs); follow the existing DeFi protocol + `DefiErrorCode` conventions
      (`/codex/04-architecture/defi-execution-overview.md`), mirroring the on-chain-CeFi-perp shape already used for
      ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC rather than the AMM-pool shape used for Jupiter/Kamino (Pacifica is an
      off-chain-matching-engine CLOB, not a pool).
- [ ] [SCRIPT] P3. **Wire `builder_code` support if we want fee-share/attribution** — Pacifica's order-creation
      endpoints accept an optional `builder_code` param for partner attribution (per fresh docs). Not required for basic
      execution; note and defer unless there's a reason to register as a builder partner.

## D. instruments-service + MTDS — reference data and capture

### D.1 Jupiter + Kamino

- [ ] [SCRIPT] P2. **Emit Jupiter PERPETUAL instruments** from `reference_data/adapters/defi/jupiter.py`, which today
      emits `SPOT_PAIR` only. Respect the PERP-vs-PERPETUAL canonicalisation the adapter's own docstring already cites,
      and register the venue token in the UAC venue registry rather than hand-rolling a key.
- [ ] [SCRIPT] P2. **Wire Jupiter perp market-data capture** (borrow-fee/utilization + mark/oracle price — NOT
      `perp_funding`, Jupiter has no funding-rate mechanism, see the collateral/mechanism finding above) so the hedge
      leg has the inputs the engines read. Declare the data types in `VENUE_DATA_TYPE_CAPABILITIES` with real
      coverage-start dates, and route zero-row days through `record_zero_rows` rather than leaving honest absence
      implicit.
- [ ] [SCRIPT] P3. **Confirm Kamino `lending_indices` capture is actually live, not merely advertised.** The capability
      registry claims `2023-06-01`; a declared start date is a claim, not evidence. Verify real objects exist across the
      window before § A.1's backtest depends on them — an entity-agnostic check passes while the target writes zero rows
      (`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`).

### D.2 Pacifica — resurrect from git history, don't rebuild blind

- [ ] [SCRIPT] P1. **Resurrect the instruments-service reference-data adapter** —
      `instruments-service@dee3f6a4~1:instruments_service/reference_data/adapters/cefi/pacifica.py` (deleted, real
      working code: curated top-10-coin `PERPETUAL` instrument list, `settle_asset=USDC`, `MarginType.LINEAR`,
      `available_from=2025-06-01`). Restore via `git show`/`git checkout` from that commit as the starting point, THEN
      update per §A.2's re-verification (real `/markets` endpoint if one now exists) rather than restoring the stale
      curated list unmodified. Also restore the factory registration and orchestrator venue-list entry the cull commit
      removed.
- [ ] [SCRIPT] P1. **Resurrect the MTDS batch REST adapter** —
      `market-tick-data-service@2e674d1f~1:market_tick_data_service/adapters/_umi_pacifica.py` (deleted, 495 lines, real
      working code against `https://api.pacifica.fi/api/v1`: `fetch_pacifica_candles`/`fetch_pacifica_rest`, trades +
      book_snapshot_5 parsing, `_PACIFICA_FUNDING_START_MS` floor at 2025-06-01). Restore via `git show`, then re-run
      §A.2's REST re-verification todo against the live endpoint before trusting the restored parser byte-for-byte (API
      response shapes can drift over a month). Also restore the `umi_tick_provider.py` routing re-binds the deleted
      module's docstring says are required.
- [ ] [SCRIPT] P2. **Resurrect (and only then, conditionally, activate) the MTDS live WS connector** —
      `market-tick-data-service@2e674d1f~1:market_tick_data_service/live/connectors/pacifica_solana_perp_ws.py`
      (deleted, was a `BLOCKED-CREDENTIALS` scaffold, `_CREDENTIALS_AVAILABLE = False`, `wss://ws.pacifica.fi/v1`).
      Restore as a scaffold either way (protocol-conforming, tests pass on mocks, safe no-op if creds still gated) —
      **gate real activation (`_CREDENTIALS_AVAILABLE = True` + implementing `_drain_ws_messages`) on §A.2's P0
      re-verification todo's result.** Do not build real WS parsing against an unconfirmed-open endpoint.
- [ ] [SCRIPT] P2. **Wire Pacifica funding-rate capture as `derivative_ticker.funding_rate`, NOT standalone
      `perp_funding`.** Pre-cull history shows Pacifica was already migrated to the bundled `derivative_ticker` shape
      (`market-tick-data-service@ba6df0ac`, "retire standalone perp_funding for HYPERLIQUID/ASTER/PACIFICA-SOLANA/
      LIGHTER-ZKSYNC in favor of derivative_ticker.funding_rate") — follow that established pattern, don't reintroduce a
      standalone `perp_funding` data_type for this venue. Funding settles hourly with 5s recalculation per current docs
      — confirm the capture cadence matches.
- [ ] [SCRIPT] P3. **Restore or rewrite the pruned Pacifica tests** — `tests/unit/test_pacifica_candles.py` (408 lines)
      and `tests/unit/test_pacifica_solana_perp_ws_connector.py` (145 lines) were deleted in the same cull commit
      (`2e674d1f`). Restore as a starting point, update assertions against any API-shape drift found in §A.2.

## E. strategy-service — make the structures selectable and coin-agnostic

### E.1 Jupiter + Kamino (staked-basis / recursive-staked)

- [ ] [SCRIPT] P1. **Make borrow-venue eligibility coin-agnostic, with the registries as the constraint.** Operator
      instruction: _"make logic coin agnostic albeit the actual constraint of coins and venues should define the
      restrictions"_ — which is already the pattern `_staked_basis_eligible()` uses for LST/perp pairs. Extend the same
      shape to the borrow leg: a (LST, lending_venue, perp_venue) triple is eligible iff the lending venue accepts the
      LST **and** the perp venue accepts the borrowed stable as margin. **No hardcoded chain lists** — the existing
      `_STAKED_BASIS_ETH_LSTS` / `_STAKED_BASIS_SOL_LSTS` split is acceptable as data, but the eligibility test must not
      branch on chain.
- [ ] [SCRIPT] P2. **Emit `CARRY_RECURSIVE_STAKED` slots for the Solana triple** once § B.1 and § C.1 land, and confirm
      zero infeasible slots are emitted before them (the empty SOL bundle is the correct behaviour **of the generator**
      and must stay correct throughout — but see the next todo: it is not the system's actual behaviour).
- [ ] [SCRIPT] P0. **Reconcile the two slot surfaces, which disagree on whether SOL staked basis is runnable at all.**
      Found by the 54-archetype sweep, 2026-08-12. Both surfaces know the identical fact — HYPERLIQUID does not accept
      mSOL/JitoSOL as `LST_AS_MARGIN` — and act on it **oppositely**: `archetype_slots_defi.py:154` declares
      `SOL_STAKED_BASIS` as a live `…-v5-prod` slot (`CARRY_STAKED_BASIS`, mSOL, marinade, spot=jupiter,
      perp=hyperliquid) whose in-line comment states the engine's `_derive_structure` falls back to
      `USDC_MARGIN_BUFFERED` and is therefore "genuinely functional (not a dead slot)"; meanwhile
      `catalog_staked_basis.py:105-120` emits **zero** SOL-side rows because `_resolve_start_token()` returns `None` and
      the generator "just doesn't implement that fallback branch (pre-existing gap, tracked separately)". **Consequence:
      "SOL staked basis is infeasible" is true of one surface and false of the other**, so any claim resting on the
      generator's emptiness — including this plan's § A.1 economics gate — is measuring the wrong surface. Decide ONE
      answer (teach the generator the `USDC_MARGIN_BUFFERED` fallback, or retire the `archetype_slots_defi` row) and
      make the other follow. Evidence: `catalog_staked_basis.py:105,244-275`; `archetype_slots_defi.py:154-176`. The
      parallel-catalog-surface class is already documented in
      [config-key contract drift](/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md) §
      "Second-surface sweep" — this is a **feasibility** divergence, not a config-key one, so it is a new instance of a
      known class.
- [ ] [SCRIPT] P2. **Add the ETH equivalent of the same triple** (stETH/wstETH + Aave/Morpho/Spark borrow + a perp
      venue). Sequence it FIRST if § A.1 shows the ETH spread is better — the venues are already integrated, so it is
      the cheaper shipment and it de-risks the Solana one.
- [ ] [SCRIPT] P3. **Confirm the composite path.** A basket across (LST × lending venue × perp venue) is many weighted
      instances of one archetype, not a composite archetype — see
      [portfolio-allocator](/codex/03-services/portfolio-allocator.md). Verify the allocator weights these correctly
      rather than adding a new composition concept.

### E.2 Pacifica (funding-dispersion / straight-basis)

- [ ] [SCRIPT] P1. **Add `PACIFICA-SOLANA` as a `perp_venue` candidate for `CARRY_FUNDING_DISPERSION` and straight-basis
      structures** (never for `CARRY_STAKED_BASIS`/`CARRY_RECURSIVE_STAKED` — no LST margin, see the collateral finding
      above). Mirrors how ASTER is already the priority venue in §B.1's PERP_CEX backfill todo — Pacifica joins that
      same funding-dispersion cluster, not the staked-basis one Jupiter/Kamino target.
- [ ] [SCRIPT] P2. **Confirm per-archetype venue selection accepts Pacifica with no new mechanism.** Same claim already
      verified for Jupiter/Kamino (`recursive_staked.py`/`staked_basis.py` params) — check the funding-dispersion
      archetype's own venue-selection path (likely `funding_rate_dispersion.py` per the earlier grep) reads `perp_venue`
      the same way; if it does, this is registry population only, same shape as Track 1.

## F. Documentation

- [x] [SCRIPT] P2. ✅ **Update `/codex/04-architecture/solana-defi-coverage.md`** — DONE 2026-08-14
      (`unified-trading-pm@a26085fadb`). Added a 🟢 REVERSAL banner to `/codex/04-architecture/solana-defi-coverage.md`
      itself recording the 2026-08-14 operator ruling ("jupiter and pacifica please"), the reasoning (Pacifica wasn't
      itself compromised, current volume/TVL data with the wash-trading caveat), and that DRIFT stays removed. Did not
      yet update the venue-registry tables below the banner (still show pre-cull PACIFICA-SOLANA content as historical)
      — that's the next todo.
- [ ] [SCRIPT] P2. **Update the codex venue-registry tables once B.2/C.2/D.2 land** — replace the "Plan B EMPTY" framing
      and the struck-through DRIFT-only table with the real post-reintegration state (Jupiter perps + Pacifica, Drift
      still absent), and fold in the git-history resurrection facts this plan found (§A.2, §D.2) so a future reader
      doesn't have to re-derive them from `git log`.
- [ ] [SCRIPT] P2. **Write the `CARRY_RECURSIVE_STAKED` Solana variant into its archetype doc**, including why
      `CARRY_STAKED_BASIS` is NOT available on Solana (true for BOTH Jupiter and Pacifica — neither accepts LST margin,
      worth stating once clearly since it's the single most likely thing for a future reader to get wrong).
- [ ] [SCRIPT] P3. **Record the go/no-go from § A.1 in codex** whichever way it lands. A measured "not worth doing" is a
      valuable durable finding and stops this being re-proposed every quarter.

## Progress Log

- **2026-08-12** — Authored on operator instruction. Audit finding that shapes the whole plan: **neither venue is new.**
  Kamino already has a reference-data adapter, an MTDS handler, an execution protocol, a `CollateralPolicy` and
  `KaminoBorrowParams` in UAC; Jupiter already has an adapter, a swap execution path and a live connector shipped
  2026-08-08. The gaps are narrow and specific — Kamino has `supply`/`withdraw` but **no `borrow`**, and Jupiter emits
  `SPOT_PAIR` with a swap-only execution path. Verified against Jupiter's own docs that its perps accept **no LST as
  margin** (JLP custodies SOL/ETH/BTC/USDC/USDT/JupUSD; shorts take USDC/USDT), so the structure must be
  `CARRY_RECURSIVE_STAKED` and `CARRY_STAKED_BASIS` stays unavailable on Solana. Confirmed per-archetype venue selection
  already exists (`staking_protocol` / `lending_protocol` / `perp_venue` are params today), so no new selection
  mechanism is needed. **Answered two operator questions with measurements: Aave has no Solana deployment** (all 11
  `AAVE_V3-*` keys are EVM), and **three** Solana lending venues already carry `lending_indices` history (Kamino
  2023-06, Solend 2022-11, MarginFi 2025-01). Left `status: draft` deliberately — the codex requires an explicit
  operator decision to re-add a Solana perp venue, and § A's economics gate could still return no-go.

- **2026-08-14 (part 1)** — Interactive session: operator asked to use "Pacifica and Jupiter" for a Solana perp
  basis/funding-rate trade, believing MTDS adapters already existed for both. **Corrected**: what's wired under
  `JUPITER-SOLANA` is Jupiter the spot-swap aggregator (`jupiter_solana_ws.py` polls `lite-api.jup.ag/swap/v1/quote`) —
  a different product from Jupiter **Perpetuals** (JLP-pool-backed, separate REST surface at
  `api.jup.ag`/`developers.jup.ag/docs/perps/` covering markets/positions/funding/pricing). Zero coverage of Jupiter
  Perps specifically exists anywhere. `PACIFICA` had zero hits in `VENUES_BY_ASSET_GROUP` or any connector, confirming
  the 2026-07-16 cull held live. Surfaced the conflict (Pacifica killed alongside Drift with no evidence of its own
  compromise) and current Pacifica data (#1 Solana perp DEX by volume 3 months post-launch,
  $100B+ cumulative volume,
  but only ~$27-38M TVL — one external source flags the ratio as a possible wash-trading
  signature). Externally re-verified the Drift hack:
  $285M, 2026-04-01, DPRK-attributed (TRM Labs/Chainalysis/Elliptic), Security-Council
  pre-signed-nonce social-engineering attack, TVL ~$550M
  → ~$252M.

- **2026-08-14 (part 2)** — Operator ruled **"jupiter and pacifica please"** — an explicit reversal of the Pacifica
  portion of the 2026-07-16 cull, recorded as a dated 🟢 REVERSAL banner in
  `/codex/04-architecture/solana-defi-coverage.md` (`unified-trading-pm@a26085fadb`), mirroring how the original cull
  was recorded. Drift stays removed — the reversal is Pacifica-specific. Operator then explicitly chose to fold Pacifica
  into THIS plan (Track 2) rather than a separate doc, despite Pacifica having no staked-basis role — it's a
  funding-dispersion/straight-basis venue, not a Kamino-borrow-structure participant.

  **Follow-up audit found Pacifica re-integration is mostly a RESURRECTION, not a rebuild** — the 2026-07-16 cull
  deleted real, working code rather than removing placeholders: a functioning MTDS batch REST adapter (495 lines,
  `_umi_pacifica.py`, trades + book_snapshot_5 + candles against `https://api.pacifica.fi/api/v1`), a working
  instruments-service reference adapter, and a `BLOCKED-CREDENTIALS`-scaffolded (never activated) live WS connector.
  **execution-service never had Pacifica code at all** (confirmed zero commits) — that piece is genuine net-new work,
  unlike everything else. Found via `git log --diff-filter=D` at the exact pre-deletion commits
  (`instruments-service@dee3f6a4~1`, `market-tick-data-service@2e674d1f~1`) — cited directly in §D.2's todos so a future
  worker restores from git history instead of rebuilding blind.

  **Open question that gates Track 2's live-capture design**: the 2026-07-06 BLOCKED-CREDENTIALS assessment (paid
  Helius/Triton RPC + Pacifica partner header required) predates both the cull and this session's fresh research, which
  found Pacifica's current docs describing an openly-documented REST+WS suite with a Python SDK. **These aren't
  necessarily the same claim** — public docs existing doesn't prove the market-data channels are free-tier-reachable.
  Filed as §A.2's P0 todo: re-test the actual endpoint before designing anything real, don't build against either
  unverified claim.

  Widened `repos`/`tags`/estimates accordingly (baseline 12→20 AI-days, calibrated 9.6→15.4) — Pacifica's execution-
  service build is genuine net-new scope on top of Track 1's narrower additions. `status: draft` unchanged — both tracks
  are still gated (§A.1 economics, §A.2 credential re-verification).
