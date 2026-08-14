---
doc_type: plan
title: >-
  Solana LST carry — Jupiter perps + Kamino borrow, with coin-agnostic borrow-venue selection
summary: >-
  Restore Solana LST carry after the 2026-07-16 perp-DEX cull left Plan B empty, by integrating Jupiter perps (the
  operator's stated long-term intent, re-authorized 2026-08-14) for the hedge leg, and Kamino lending (the only venue in
  the UAC collateral registry that accepts JitoSOL/mSOL) for the LST collateral leg. Jupiter alone cannot restore staked
  basis — verified against its own docs, its JLP pool custodies only SOL/ETH/BTC/USDC/USDT/JupUSD and a short requires
  USDC/USDT margin — so the structure is LST-at-a-lending-venue, borrow a stable against it, post that as perp margin.
  Gated on an economics question the operator raised and that must be answered from our own corpus BEFORE any code: is
  the stablecoin borrow rate reliably below the staking yield? A second, newly-found gate: real API testing (2026-08-14)
  shows Jupiter's borrow-fee/utilization data has no clean home in an existing UAC schema — a genuine open decision, not
  yet resolved. Also generalises borrow-venue selection to be coin-agnostic and closes registry gaps found while
  auditing. (Pacifica re-integration was originally scoped in this same plan; split out 2026-08-14 to
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md once its gates fully resolved while this plan's stayed
  open — see that plan for the funding-rate/basis venue.)
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
tags: [defi, solana, carry, staked-basis, collateral, jupiter, kamino, lending, venue-onboarding]
related:
  [
    /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /codex/04-architecture/solana-defi-coverage.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
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
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 9.6
assigned_role:
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-12. Operator instruction: "we should add Jupter and Kamino so that staked basis works on
  kamino and abiss on solana", scoped to full integration across repos after auditing what already exists ("these aren't
  new venues"), with the larger plan linked to the Elysium October delivery plan. Operator questions folded in as gating
  todos: is USDC borrow cheaper than SOL staking yield historically; does Aave accept staked SOL; which of Aave/Kamino
  has better LTV and lower stable borrow rates; make the logic coin-agnostic with real coin/venue constraints as the
  restriction; and confirm per-archetype borrow/staking/perp venue selection already exists. Extended 2026-08-14 to
  temporarily include Pacifica re-integration (operator: "jupiter and pacifica please", reversing the 2026-07-16 cull's
  Pacifica portion — see /codex/04-architecture/solana-defi-coverage.md); split back out the same day once real API
  testing resolved every Pacifica gate while this plan's Jupiter gates (economics + a newly-found schema gap) stayed
  open — see /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md.
---

# Solana LST carry — Jupiter perps + Kamino borrow

**Why this plan exists.** The 2026-07-16 operator ruling dropped every Solana perp DEX, leaving
[Plan B empty](/codex/04-architecture/solana-defi-coverage.md). The SOL-side staked-basis bundle has emitted **zero
eligible (LST, perp_venue) pairs** ever since — correctly, because the gating logic refuses to emit infeasible slots.
This plan restores Solana LST carry through a different structure rather than re-adding a culled venue.

> **This plan does NOT constitute the operator decision to re-add a Solana perp DEX.** The codex requires an explicit
> new decision — Jupiter's is recorded in the 2026-08-14 REVERSAL banner on
> `/codex/04-architecture/solana-defi-coverage.md`. `status: draft` here reflects that code work is still gated on
> **two** open questions: §A's economics gate, and §A.3's newly-found schema-mapping gate. **Flip to `active` only once
> both resolve.**

**Status of the two venues — audited 2026-08-12, neither is new.** The operator's instinct was right:

| Surface                    | Jupiter                                                       | Kamino                                                       |
| -------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------ |
| UAC collateral policy      | ❌ absent (no row in either registry)                         | ✅ `CollateralPolicy`, `lending`, JitoSOL/mSOL @15% haircut  |
| UAC params contract        | ❌ none for perps                                             | ✅ `KaminoBorrowParams` **already exists**                   |
| instruments-service        | ✅ adapter — but emits `SPOT_PAIR` only                       | ✅ adapter + factory + defi orchestrator                     |
| market-tick-data-service   | ✅ live connector shipped 2026-08-08 (`jupiter_solana_ws.py`) | ✅ `solana_defi_amm` handler; `lending_indices` from 2023-06 |
| execution-service          | ✅ swap-only (`get_swap_quote` / `execute_swap`)              | ✅ `supply`/`withdraw` — **no `borrow`/`repay`**             |
| strategy-service catalogue | ❌ not a perp-hedge venue candidate                           | ❌ not wired as a borrow venue for staked structures         |

So the work is **two narrow additions on top of substantial existing integration**, not two venue onboardings: Jupiter's
**perp** surface, and Kamino's **borrow** surface.

**The structure, and why it is not `CARRY_STAKED_BASIS`.** Verified against Jupiter's own documentation
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

**Jupiter has no funding-rate mechanism at all** — confirmed via real API call (`perps-api.jup.ag/v1/pool-info` returns
`longBorrowRatePercent`/`shortBorrowRatePercent`, never `funding_rate`). Traders on both sides always pay borrow fees to
the JLP pool, never each other — there's no funding-rate arb/basis signal to capture here, only cheap directional
hedging. **If the goal is a funding-rate basis/dispersion trade, that's a different venue** — see
`/plans/active/pacifica_solana_perp_reintegration_2026_08_14.md`, split out once its own gates resolved.

**Per-archetype venue selection already exists** — confirmed, answering the operator's "I hope is the case":
`recursive_staked.py` already reads `staking_protocol`, **`lending_protocol`** and `perp_venue` as params, and
`staked_basis.py` reads `staking_protocol`, `perp_venue`, `spot_venue`. No new selection mechanism is needed; the work
is populating the registries the selection resolves against.

**Codex SSOTs each change is checked against:** [solana-defi-coverage](/codex/04-architecture/solana-defi-coverage.md) ·
[carry-recursive-staked](/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md) ·
[tier-and-import-architecture](/codex/04-architecture/tier-and-import-architecture.md) ·
[defi-canonical-naming-ssot](/codex/02-data/defi-canonical-naming-ssot.md) ·
[gcs-and-manifest-delete-safety-protocol](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)

## A. Economics gate — answer this BEFORE writing code (blocks everything below)

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
      § A's spread IS computable and the go/no-go analysis can proceed on real history.
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

              **Consequence for § A, in the good direction:** SOL LST history starts **2021-08**, roughly 22 months EARLIER than
                          Kamino's `lending_indices` (2023-06). So the binding constraint on the Solana spread is the **borrow** series, not the
                          staking series, and the full Kamino window is computable. ETH remains deeper (Lido `staking_yields` 2020-12-18) but
                          Solana is in no way blocked.

- [ ] [AGENT] P0. **Use `lst_rates`, NOT `staking_yields`, for the § A spread — they measure different things.**
      Measured 2026-08-12; recorded here because § A's answer is wrong if the wrong series is used.

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
      extended rather than invented. Gate on whether § A shows the ranking actually changes hands often enough to pay
      for itself; a static best-venue choice is correct if it does not.

## A.3 Jupiter Perps schema/asset_group gate — NEW finding 2026-08-14, genuinely unresolved

**Real API calls made** (`https://perps-api.jup.ag/v1/positions?walletAddress=...` and
`.../v1/pool-info?mint=<SOL mint>`) confirm the API is live, public, no-auth: `pool-info` returns real current data —
`longBorrowRatePercent`, `shortBorrowRatePercent`, `longUtilizationPercent`, `shortUtilizationPercent`,
`longAvailableLiquidity`, `shortAvailableLiquidity`, `openFeePercent` — confirming the borrow-fee/utilization mechanism
(not funding rate) this plan already claimed. **What's newly found and NOT yet resolved: which existing UAC schema this
data should write to, and it is not a clean fit.**

Checked directly against the live UAC schema registry (`find_schema`, 2026-08-14):

| data_type                                             | Schema exists for `cefi`?                                                                            | Schema exists for `defi`?                                                                                                                                                                                                    |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `derivative_ticker`                                   | ✅ yes — `funding_rate`, `mark_price`, `index_price`, `open_interest`, `predicted_funding_rate`, ... | ❌ **no schema registered**, despite appearing in `DATA_TYPES_BY_ASSET_GROUP["defi"]`'s generic valid-list                                                                                                                   |
| `perp_funding` / `perp_daily_ctx` / `perp_mark_price` | (not checked — cefi doesn't need them, `derivative_ticker` already bundles this)                     | ❌ **no schema registered**, same false-positive as above                                                                                                                                                                    |
| `utilization`                                         | ❌ no schema registered                                                                              | ✅ yes — `borrow_rate_apy`, `variable_borrow_rate_apy`, `stable_borrow_rate_apy`, `utilization_rate`, `liquidity_rate_apy`, `supply_rate_apy` — **single-sided, no long/short split, no mark/index price, no open interest** |

**The practical problem**: `JUPITER-SOLANA` is pinned to `defi` in `VENUE_TO_ASSET_GROUP` (confirmed live — it's a
strict 1:1 dict, a venue cannot span two asset_groups), and `defi` has no working `derivative_ticker`/`perp_funding`/
`perp_mark_price` schema — those data_types are asset-group-declared but schema-less for defi, a trap: "valid data_type
for this asset_group" and "has a real schema to write against" are DIFFERENT claims, and the generic capability list
doesn't distinguish them. `defi/utilization` DOES have a real schema and is a genuinely good semantic match for the
borrow-rate/utilization fields specifically — but it's single-row-per-instrument shaped, not long/short-split, and
carries no mark/index price or open-interest columns, so it cannot alone serve as a `derivative_ticker`-equivalent for
this venue. **Contrast with the split-out Pacifica plan** — that venue is cleanly `cefi`-classified and
`cefi/derivative_ticker` already has everything it needs, no equivalent gap.

- [ ] [AGENT] P0. **Decide how Jupiter Perps market data maps onto an EXISTING schema, per the operator's explicit
      "ideally without creating new data types" constraint.** Three real options, no clean fourth: (1) write TWO
      `utilization` rows per poll (long side, short side) and accept it doesn't carry mark/index/OI — those would need a
      separate signal source (Jupiter position-account queries can supply mark/index price directly from Solana RPC,
      untested this session); (2) register the perps product under a DIFFERENT venue token than `JUPITER-SOLANA` (e.g. a
      `JUPITER-PERPS` variant) classified under `cefi` instead, where `derivative_ticker`'s real schema already fits —
      but this breaks the "one Jupiter venue" assumption and needs its own UAC venue-registry decision; (3) accept this
      is the one genuine case needing a new/extended schema (e.g. add `borrow_rate_long`/
      `borrow_rate_short`/`utilization_long`/`utilization_short` columns to `defi/utilization`, or a defi-side
      `derivative_ticker` schema) despite the stated preference to avoid it. **This decision blocks §D's Jupiter
      market-data todo — do not write capture code before it resolves.**
- [ ] [AGENT] P1. **Check whether Solana RPC / on-chain Position/Custody account reads can supply Jupiter Perps mark
      price, index price, and open interest** (the fields `pool-info` does NOT return) — the Perpetuals API docs
      describe these as queryable on-chain accounts via standard RPC or Anchor, not necessarily via the REST surface
      tested this session. Untested this session — needed to know whether option (1) above is actually viable (a
      `utilization` row plus a second on-chain read) or whether mark/index/OI simply aren't available at all without
      building an Anchor account decoder.

## Track 2 (Pacifica) todos — MOVED, not deleted

The 15 todos below existed in this plan's former Track 2 (Pacifica) before the 2026-08-14 split (see Progress Log). They
now live, verbatim or refined with real API-test evidence gathered the same day, in
`/plans/active/pacifica_solana_perp_reintegration_2026_08_14.md`. Recorded here in the todo-conservation disposition
format so the split reads as a move, not a silent deletion.

- **[AGENT] P0. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §A).** Pacifica live-WS credential re-test — completed,
  now recorded in the split plan's §A.
- **[AGENT] P1. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §A).** Pacifica REST base-URL/shape re-verification —
  completed, now recorded in the split plan's §A.
- **[AGENT] P2. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §A).** Pacifica markets-discovery endpoint check —
  completed, now recorded in the split plan's §A.
- **[SCRIPT] P1. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §B).** Add `PACIFICA-SOLANA`'s `CollateralPolicy` to
  UAC `COLLATERAL_REGISTRY`.
- **[SCRIPT] P2. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §B).** Re-register `PACIFICA-SOLANA` in
  `VENUES_BY_ASSET_GROUP["cefi"]`.
- **[SCRIPT] P1. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §E).** Build `defi_execution/protocols/pacifica.py`
  from scratch.
- **[SCRIPT] P3. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §E).** Wire `builder_code` support for Pacifica
  order-creation.
- **[SCRIPT] P1. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §C).** Resurrect the instruments-service Pacifica
  reference-data adapter.
- **[SCRIPT] P1. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §D).** Resurrect the MTDS Pacifica batch REST adapter.
- **[SCRIPT] P2. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §D).** Resurrect and activate the MTDS Pacifica live WS
  connector.
- **[SCRIPT] P2. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §D).** Wire Pacifica funding-rate capture via
  `derivative_ticker.funding_rate`.
- **[SCRIPT] P3. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §D).** Restore/rewrite the pruned Pacifica MTDS tests.
- **[SCRIPT] P1. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §F).** Add `PACIFICA-SOLANA` as a `perp_venue`
  candidate for `CARRY_FUNDING_DISPERSION`.
- **[SCRIPT] P2. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §F).** Confirm per-archetype venue selection accepts
  Pacifica with no new mechanism.
- **[SCRIPT] P2. CANCELLED — SUPERSEDED 2026-08-14 (split, per
  /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md §G).** Update the codex venue-registry tables for
  Pacifica once its build lands.

## B. Registry layer — the correct first code change, and it needs no strategy edits

Doing this before any adapter work makes `_staked_basis_eligible()` and `_derive_structure()` resolve Solana correctly
on their own: an LST/venue pair the venue cannot margin is simply never emitted as a slot, so **the gating logic needs
no change at all.**

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

## C. execution-service — the two missing surfaces

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

## D. instruments-service + MTDS — reference data and capture

- [ ] [SCRIPT] P2. **BLOCKED on §A.3.** Emit Jupiter PERPETUAL instruments from
      `reference_data/adapters/defi/jupiter.py` (today emits `SPOT_PAIR` only) — but which venue token/asset_group it
      registers under depends on §A.3's unresolved decision (same `JUPITER-SOLANA` token under `defi`, or a new
      perps-specific token under `cefi`). Resolve §A.3 first or this todo just re-derives the same open question
      mid-implementation.
- [ ] [SCRIPT] P2. **BLOCKED on §A.3.** Wire Jupiter perp market-data capture (borrow-fee/utilization + mark/oracle
      price — NOT `perp_funding`, Jupiter has no funding-rate mechanism, confirmed via real API call: `pool-info`
      returns `longBorrowRatePercent`/`shortBorrowRatePercent`, no `funding_rate` field anywhere). §A.3 found no
      existing `defi` schema cleanly fits this (2 sides, no mark/index/OI in `utilization`) — the actual schema target
      is undecided, so this todo cannot be scoped precisely yet. Once §A.3 resolves: declare the chosen data type(s) in
      `VENUE_DATA_TYPE_CAPABILITIES` with real coverage-start dates, and route zero-row days through `record_zero_rows`
      rather than leaving honest absence implicit.
- [ ] [SCRIPT] P3. **Confirm Kamino `lending_indices` capture is actually live, not merely advertised.** The capability
      registry claims `2023-06-01`; a declared start date is a claim, not evidence. Verify real objects exist across the
      window before § A's backtest depends on them — an entity-agnostic check passes while the target writes zero rows
      (`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`).

## E. strategy-service — make the structure selectable and coin-agnostic

- [ ] [SCRIPT] P1. **Make borrow-venue eligibility coin-agnostic, with the registries as the constraint.** Operator
      instruction: _"make logic coin agnostic albeit the actual constraint of coins and venues should define the
      restrictions"_ — which is already the pattern `_staked_basis_eligible()` uses for LST/perp pairs. Extend the same
      shape to the borrow leg: a (LST, lending_venue, perp_venue) triple is eligible iff the lending venue accepts the
      LST **and** the perp venue accepts the borrowed stable as margin. **No hardcoded chain lists** — the existing
      `_STAKED_BASIS_ETH_LSTS` / `_STAKED_BASIS_SOL_LSTS` split is acceptable as data, but the eligibility test must not
      branch on chain.
- [ ] [SCRIPT] P2. **Emit `CARRY_RECURSIVE_STAKED` slots for the Solana triple** once § B and § C land, and confirm zero
      infeasible slots are emitted before them (the empty SOL bundle is the correct behaviour **of the generator** and
      must stay correct throughout — but see the next todo: it is not the system's actual behaviour).
- [ ] [SCRIPT] P0. **Reconcile the two slot surfaces, which disagree on whether SOL staked basis is runnable at all.**
      Found by the 54-archetype sweep, 2026-08-12. Both surfaces know the identical fact — HYPERLIQUID does not accept
      mSOL/JitoSOL as `LST_AS_MARGIN` — and act on it **oppositely**: `archetype_slots_defi.py:154` declares
      `SOL_STAKED_BASIS` as a live `…-v5-prod` slot (`CARRY_STAKED_BASIS`, mSOL, marinade, spot=jupiter,
      perp=hyperliquid) whose in-line comment states the engine's `_derive_structure` falls back to
      `USDC_MARGIN_BUFFERED` and is therefore "genuinely functional (not a dead slot)"; meanwhile
      `catalog_staked_basis.py:105-120` emits **zero** SOL-side rows because `_resolve_start_token()` returns `None` and
      the generator "just doesn't implement that fallback branch (pre-existing gap, tracked separately)". **Consequence:
      "SOL staked basis is infeasible" is true of one surface and false of the other**, so any claim resting on the
      generator's emptiness — including this plan's § A economics gate — is measuring the wrong surface. Decide ONE
      answer (teach the generator the `USDC_MARGIN_BUFFERED` fallback, or retire the `archetype_slots_defi` row) and
      make the other follow. Evidence: `catalog_staked_basis.py:105,244-275`; `archetype_slots_defi.py:154-176`. The
      parallel-catalog-surface class is already documented in
      [config-key contract drift](/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md) §
      "Second-surface sweep" — this is a **feasibility** divergence, not a config-key one, so it is a new instance of a
      known class.
- [ ] [SCRIPT] P2. **Add the ETH equivalent of the same triple** (stETH/wstETH + Aave/Morpho/Spark borrow + a perp
      venue). Sequence it FIRST if § A shows the ETH spread is better — the venues are already integrated, so it is the
      cheaper shipment and it de-risks the Solana one.
- [ ] [SCRIPT] P3. **Confirm the composite path.** A basket across (LST × lending venue × perp venue) is many weighted
      instances of one archetype, not a composite archetype — see
      [portfolio-allocator](/codex/03-services/portfolio-allocator.md). Verify the allocator weights these correctly
      rather than adding a new composition concept.

## F. Documentation

- [ ] [SCRIPT] P2. **Update `/codex/04-architecture/solana-defi-coverage.md`** — Plan B stops being EMPTY when Jupiter
      perps lands. Note: Pacifica's portion of this update is now tracked in the split-out plan
      (`/plans/active/pacifica_solana_perp_reintegration_2026_08_14.md` §G) — this todo covers the Jupiter-specific
      table update only.
- [ ] [SCRIPT] P2. **Write the `CARRY_RECURSIVE_STAKED` Solana variant into its archetype doc**, including why
      `CARRY_STAKED_BASIS` is NOT available on Solana. That distinction is the single most likely thing for a future
      reader to get wrong, since the two archetypes differ only in where the LST sits.
- [ ] [SCRIPT] P3. **Record the go/no-go from § A in codex** whichever way it lands. A measured "not worth doing" is a
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

- **2026-08-14 (part 1-3, condensed)** — Operator initially asked to use "Pacifica and Jupiter" for a Solana perp
  funding trade; correcting the untested premise (no MTDS coverage of either perps product existed) led to discovering
  the 2026-07-16 cull had killed Pacifica alongside Drift with no evidence Pacifica itself was compromised. Operator
  reversed that ruling ("jupiter and pacifica please" — recorded in the codex tombstone,
  `unified-trading-pm@a26085fadb`) and Pacifica was temporarily folded into this plan as Track 2. Real API testing then
  resolved every Pacifica gate (live WS streamed trades with zero credentials, REST shapes confirmed, schema confirmed
  clean via `cefi/derivative_ticker`) while finding a genuine NEW gate for Jupiter (§A.3 above — no working `defi`-side
  schema for `derivative_ticker`/`perp_funding`, `JUPITER-SOLANA` locked to `defi` where only `utilization` has a real
  (imperfect-fit) schema).

- **2026-08-14 (part 4) — SPLIT.** Operator: "just pacifica then lets build plan from IS to Strategy service." Since
  Pacifica's gates were fully resolved while this plan's (§A economics, §A.3 schema) were not, split Pacifica out to its
  own `status: active` plan (`/plans/active/pacifica_solana_perp_reintegration_2026_08_14.md`) rather than keep blocking
  ready work behind this plan's open gates. This doc reverts to its original Jupiter+Kamino-only scope and estimate
  (baseline 12, calibrated 9.6 — down from the temporary 20/15.4 combined figure). `status: draft` unchanged — still
  gated on §A and the new §A.3.

- **2026-08-14/15 — sibling track complete.** The split-out Pacifica plan finished its full build-out: UAC registry →
  instruments-service → market-tick-data-service (batch + live) → execution-service → strategy-service, all shipped with
  green quality gates across 5 repos (see that plan's Progress Log for commit SHAs). Notable for THIS plan's own gates:
  Pacifica's execution-service protocol ended up simulation-only (`supports_live=False`) because Pacifica's
  order-signing model turned out to require a raw Solana Ed25519 wallet keypair, not an HMAC API-key scheme — worth
  checking whether Jupiter perps (once/if this plan's gates resolve) has the same live-signing constraint, since that's
  a real execution-service scoping question, not just a data-coverage one. This plan (Jupiter+Kamino) remains
  `status: draft`, still gated on §A economics + §A.3 schema-mapping — Pacifica landing does not resolve either gate.
