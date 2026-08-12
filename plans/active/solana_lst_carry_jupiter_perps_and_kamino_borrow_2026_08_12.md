---
doc_type: plan
title: >-
  Solana LST carry — Jupiter perps + Kamino borrow, with coin-agnostic borrow-venue selection
summary: >-
  Restore Solana LST carry after the 2026-07-16 perp-DEX cull left Plan B empty, by integrating the two venues that
  survive on merit: Jupiter perps (the only liquid, never-hacked Solana perp venue) for the hedge leg, and Kamino
  lending (the only venue in the UAC collateral registry that accepts JitoSOL/mSOL) for the LST collateral leg. Jupiter
  alone cannot restore staked basis — verified against its own docs, its JLP pool custodies only
  SOL/ETH/BTC/USDC/USDT/JupUSD and a short requires USDC/USDT margin — so the structure is LST-at-a-lending-venue,
  borrow a stable against it, post that as perp margin. Gated on an economics question the operator raised and that must
  be answered from our own corpus BEFORE any code: is the stablecoin borrow rate reliably below the staking yield? Also
  generalises borrow-venue selection to be coin-agnostic (the same structure is arguably better on ETH, where the data
  is deeper) while keeping the real per-coin/per-venue constraints as the restriction, and closes registry gaps found
  while auditing.
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
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /codex/04-architecture/solana-defi-coverage.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
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
  restriction; and confirm per-archetype borrow/staking/perp venue selection already exists.
---

# Solana LST carry — Jupiter perps + Kamino borrow

**Why this plan exists.** The 2026-07-16 operator ruling dropped every Solana perp DEX, leaving
[Plan B empty](/codex/04-architecture/solana-defi-coverage.md). The SOL-side staked-basis bundle has emitted **zero
eligible (LST, perp_venue) pairs** ever since — correctly, because the gating logic refuses to emit infeasible slots.
This plan restores Solana LST carry through a different structure rather than re-adding a culled venue.

> **This plan does NOT constitute the operator decision to re-add a Solana perp DEX.** The codex requires an explicit
> new decision and `status: draft` here reflects that — **flip to `active` only once the operator approves Jupiter perps
> AND the § A economics gate passes.** Building against a negative economics answer would be waste.

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

- [ ] [AGENT] P1. **Compare LTV and borrow cost across the three Solana lending venues** (Kamino / Solend / MarginFi)
      and against Aave on the ETH side. Operator asked which has better LTV and lower stable borrow rates. **Note for
      the record: Aave has NO Solana deployment** — all 11 `AAVE_V3-*` keys are EVM chains — so Aave is not a candidate
      for the SOL borrow leg, only for the ETH version.
- [ ] [AGENT] P2. **Decide whether borrow-venue selection should be DYNAMIC.** The operator raised it explicitly ("if it
      fluctuates we could dynamically decide"). A rank allocator over lending venues by net spread is the existing idiom
      — `YIELD_ROTATION_LENDING_RANK` already ranks protocols by supply APY, so the mechanism exists and would be
      extended rather than invented. Gate on whether § A shows the ranking actually changes hands often enough to pay
      for itself; a static best-venue choice is correct if it does not.

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

- [ ] [SCRIPT] P2. **Emit Jupiter PERPETUAL instruments** from `reference_data/adapters/defi/jupiter.py`, which today
      emits `SPOT_PAIR` only. Respect the PERP-vs-PERPETUAL canonicalisation the adapter's own docstring already cites,
      and register the venue token in the UAC venue registry rather than hand-rolling a key.
- [ ] [SCRIPT] P2. **Wire Jupiter perp market-data capture** (funding + mark/oracle price) so the hedge leg has the
      inputs the engines read. Declare the data types in `VENUE_DATA_TYPE_CAPABILITIES` with real coverage-start dates,
      and route zero-row days through `record_zero_rows` rather than leaving honest absence implicit.
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
      infeasible slots are emitted before them (the current empty SOL bundle is the correct behaviour and must stay
      correct throughout).
- [ ] [SCRIPT] P2. **Add the ETH equivalent of the same triple** (stETH/wstETH + Aave/Morpho/Spark borrow + a perp
      venue). Sequence it FIRST if § A shows the ETH spread is better — the venues are already integrated, so it is the
      cheaper shipment and it de-risks the Solana one.
- [ ] [SCRIPT] P3. **Confirm the composite path.** A basket across (LST × lending venue × perp venue) is many weighted
      instances of one archetype, not a composite archetype — see
      [portfolio-allocator](/codex/03-services/portfolio-allocator.md). Verify the allocator weights these correctly
      rather than adding a new composition concept.

## F. Documentation

- [ ] [SCRIPT] P2. **Update `/codex/04-architecture/solana-defi-coverage.md`** — Plan B stops being EMPTY when Jupiter
      perps lands. Replace the tombstone's "no supported Solana perp DEX" with the new state, keep the DRIFT/PACIFICA
      history as historical record, and retain the verified Jupiter-collateral finding.
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
