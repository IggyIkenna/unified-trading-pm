---
doc_type: issue
title: Venue coverage — we can EXECUTE on ~30 DeFi protocols and READ positions from 3
summary: >-
  Audit of venue coverage against the MTDS capture universe (158 venues, 84 families) across the two surfaces a venue
  must be supported on — a strategy-service position adapter (client-credentialed, read-only, the exchange side of
  reconciliation) and execution-service instruction handling. CeFi is covered on both sides, largely because the ccxt
  position adapter is generic over any ccxt exchange_id. DeFi is badly asymmetric — execution-service ships ~30 protocol
  modules while strategy-service ships exactly 3 position adapters (aave, morpho, uniswap), so for most DeFi protocols
  we can act and cannot reconcile. This includes Lido, Marinade, Kamino and Jupiter, i.e. both legs of the two DeFi
  archetypes shipping real in the carve-out.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution, strategy]
repos: [strategy-service, execution-service, unified-api-contracts]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [venue-coverage, reconciliation, position-adapters, disclosure]
priority: P0
source: operator-request-2026-08-14
parent_epic: infrastructure_master
related:
  [
    /plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md,
  ]
created: 2026-08-14
owner:
resolved_by:
locked_by:
---

# Venue coverage — read vs execute asymmetry

> **Operator framing 2026-08-14**: _"we know the venues we have in MTDS for reading market feed batch, that's
> effectively our universe. For each we need inside strategy-service adaptors to get the position data using
> client-based credentials … of course execution-service needs to be able to handle the possible strategy instructions
> for each of these venues too. We don't need credentials to fully build the code, not just stubs."_

**Position reading is not optional infrastructure — it is the exchange side of reconciliation.**
`ReconciliationSnapshot` (`strategy_service/position/models.py:174`) compares `internal_quantity` against
`exchange_quantity` and emits `discrepancy` / `discrepancy_value` (USD) / `discrepancy_pct`; three engines consume it
(`pnl_reconciliation_engine`, `transfer_reconciler`, `correction_dispatcher`), and on a material gap the dispatcher
POSTs a correction order to execution-service. **No position adapter for a venue means no exchange side, which means no
reconciliation and no correction loop for anything held there.**

## The universe

| Measure                                                     | Count |
| ----------------------------------------------------------- | ----- |
| MTDS capture venues (`VENUE_DATA_TYPE_CAPABILITIES` ∪ DeFi) | 158   |
| Distinct venue families                                     | 84    |

## Surface 1 — strategy-service position adapters (the READ side)

`position/position_interface/factory.py::get_position_adapter()` is the resolver. It **raises `ValueError` on an unknown
venue** — fail-loud, no silent fallback, which is correct.

Supported, verbatim from the factory:

- **CeFi**: `binance`, `bybit`, `okx`, `deribit`, `hyperliquid`, `ccxt`, `upbit`, `ibkr`, `betfair`, `polymarket`
- **DeFi**: `aave`, `aave_v3`, `morpho`, `uniswap`, `uniswap_v2`, `uniswap_v3`, `uniswap_v4`

**CeFi coverage is effectively broad**, because `adapters/ccxt.py` is generic: `getattr(ccxt, exchange_id)` constructs
any ccxt-supported exchange, so Kraken / Bitfinex / Bitget / Coinbase / Gate are reachable via
`venue="ccxt", exchange_id="<id>"` without a dedicated module. The dedicated CeFi adapters exist for venues needing
bespoke auth (Bybit V5 HMAC, Deribit, Hyperliquid signing).

**DeFi coverage is NOT generic — this is the finding.** `adapters/_defi_rpc.py` contains only `resolve_defi_rpc_url()`,
a URL resolver. There is **no generic ERC-20 `balanceOf` / token-balance path**, so a DeFi protocol is readable only if
it has its own adapter module. Three do.

**All adapters are read-only by contract.** `BasePositionAdapter` (ABC) declares exactly `get_balances`,
`get_positions`, `get_account_snapshot`, `get_normalized_positions`, `venue_name`. No `create_order`, no
`send_transaction`, no `withdraw`. The `sign` occurrences are HMAC **request** signing for authenticated GETs (Bybit V5,
Polymarket CLOB), not transaction signing.

## Surface 2 — execution-service (the ACT side)

`execution_service/defi_execution/protocols/` ships **40 modules** covering roughly 30 distinct protocols: `aave`,
`morpho`, `uniswap`, `lido`, `marinade`, `kamino`, `jupiter`, `orca`, `raydium`, `pendle`, `convex`, `yearn`, `beefy`,
`etherfi`, `kelpdao`, `renzo`, `puffer`, `rocket_pool`, `solblaze`, `symbiotic`, `eigenlayer`, `jito_restaking`,
`karak`, `idle`, `aster`, `hyperliquid`, `bybit`, `weth`, plus `cctp` / `bridge` for transfers. `venues/` adds
`deribit`, `lido`, `uniswap` connectors.

## The asymmetry

| Asset group | Can EXECUTE | Can READ positions | Verdict                                              |
| ----------- | ----------- | ------------------ | ---------------------------------------------------- |
| CeFi        | yes         | yes (ccxt-generic) | **Balanced** — both sides covered                    |
| DeFi        | ~30         | **3**              | **~27 protocols we can act on but cannot reconcile** |

**This is the wrong way round.** Being able to act without being able to see is strictly worse than the inverse: an
instruction executes, the position changes, and nothing can confirm it landed or detect drift afterwards.

### It hits the carve-out archetypes directly

Both DeFi archetypes shipping REAL in the carve-out depend on protocols we can execute against and cannot read:

| Archetype                  | Leg           | Execute          | Read position |
| -------------------------- | ------------- | ---------------- | ------------- |
| `CARRY_STAKED_BASIS` (ETH) | Lido stETH    | ✅ `lido.py`     | ❌            |
| `CARRY_STAKED_BASIS` (SOL) | Marinade mSOL | ✅ `marinade.py` | ❌            |
| `CARRY_RECURSIVE_STAKED`   | Kamino borrow | ✅ `kamino.py`   | ❌            |
| SOL perp leg               | Jupiter       | ✅ `jupiter.py`  | ❌            |

So today we can open both legs of a staked-basis position and reconcile neither.

## Todos

- [ ] [AGENT] P0. **Build DeFi position adapters for the carve-out path first** — Lido, Marinade, Kamino, Jupiter. These
      are not "more venues"; they are the reconciliation side of the two archetypes we are shipping real. Build the code
      fully (operator: _"we don't need credentials to fully build the code, not just stubs"_) — credentials gate RUNNING
      an adapter, not writing one.
- [ ] [AGENT] P0. **Generic-first, bespoke-by-exception — operator ruling 2026-08-14, and it applies to BOTH services.**
      A large share of DeFi position reading is an ERC-20/SPL token balance plus a protocol-specific call, so a generic
      **token-balance reader** (wallet + token + chain → balance) covers every LST and most LP positions in one module
      and shrinks the ~27 gap dramatically. **The same shape applies on the execution side**: bundle what shares a
      mechanism into one module and carve out only what genuinely differs. The exceptions in both directions are
      **on-chain dynamics** — state that cannot be read or written as a plain balance: lending health factors, Pendle
      maturities, concentrated-liquidity ranges/ticks, restaking withdrawal queues, and anything with a
      slippage/route-dependent write path. **Measure before building**: count what fraction of the ~27 a generic reader
      actually closes, and list the residue explicitly. Writing 27 near-identical modules and writing one generic module
      plus 5 exceptions are very different amounts of surface to maintain and to disclose — and the second is also far
      easier for a client engineer to audit.
- [ ] [AGENT] P1. **Build the venue-coverage cascade as THREE SIT invariants** — operator ruling 2026-08-14, recorded as
      the SSOT in
      [integration-testing-layers § "The venue-coverage cascade"](/codex/06-coding-standards/integration-testing-layers.md).
      In-repo checks belong in `quality-gates.sh`; these are cross-repo, so no single repo's gate can see the other side
      of the implication and they must run in SIT. Directional, and the direction is the point: **(1)** every MTDS batch
      capture adapter has a live one (**not** the reverse — a live venue may predate its backfill); **(2)** every MTDS
      venue has a strategy-service position reader on batch, live AND paper; **(3)** every venue strategy-service
      supports has an execution-service adaptor. Invariant 3 is the one that would have caught this issue. **It must
      compare instruction ACTIONS, not venue names** — a module that swaps but cannot stake passes a naive existence
      check, which is exactly the blind spot noted in the caveat below.
- [ ] [AGENT] P1. **Audit execution-service instruction coverage per venue.** This audit measured that protocol modules
      EXIST; it did not verify each handles every `InstructionActionV2` an archetype may emit for that venue. A module
      that swaps but cannot stake is a partial gap this table would score as ✅.
- [ ] [OPERATOR] P2. **Disclosure decision on out-of-mandate adapters.** `betfair`, `ibkr` and `polymarket` are working
      credentialed integrations for sports betting, retail brokerage and prediction markets — nothing to do with a DeFi
      mandate. They are inert unless a venue is configured, so shipping them costs nothing operationally. Purely a
      question of what we disclose. Record the decision in the Elysium plan § E.

## What sharing strategy-service actually conveys (measured 2026-08-14)

Operator question ahead of the pre-carve-out repository send: _"do we end up giving them any live adaptors to do
anything, or does everything route to execution-service?"_ **Complete read, zero write.**

| Working in their hands                                                                     | Inert without execution-service                                                                     |
| ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Every archetype engine — the alpha logic itself                                            | Order placement — `correction_dispatcher._submit_order()` POSTs to `{execution_service_url}/orders` |
| **Group B backtesting, fully self-contained** — benchmark fills replace execution entirely | Fill realism — all five matchers are execution-service                                              |
| Instruction emission — they can see exactly what each strategy would do                    | Transfers — emit-side netting only; every rail is execution-service                                 |
| Read-only venue balances/positions across 14 adapters                                      | Algo selection — the execution-policy registry                                                      |
| Netting, risk, PnL attribution, the four ledgers                                           |                                                                                                     |

**No signing, no chain writes, no order placement anywhere in strategy-service** — zero `web3` / `eth_account` / Solana
imports, and `BasePositionAdapter` declares only getters.

### Why the carve-out spec still matters (operator question, answered 2026-08-14)

The question was whether a carve-out is moot, since `ExecutionService` is one of the ten interfaces and everything that
does real work routes to a service we keep. **It is not moot, and the reason is Group B**: strategy-service plus
pipeline data is a complete research and backtest system with no execution-service involvement, so the carved package
delivers genuine, self-sufficient value — the alpha and the research loop. What it cannot do is trade.

**This strengthens the commercial position rather than weakening it.** The carve-out document is what makes the seam
legible: a reader of §04's per-interface resolution table should be able to see how much sits behind `ExecutionService`
— the policy registry, five matchers, fill realism, the transfer rails, custody — and conclude that reimplementing that
side is a serious programme. Declining to describe the seam would hide the very asymmetry that argues against carving
out. **Keep the spec; let §04 do the persuading.**

## Correction recorded (2026-08-13/14)

An earlier chat answer to the operator stated strategy-service had **only** a ccxt adapter and could therefore read CeFi
positions only. **That was wrong** — there are 14 adapter modules spanning all five asset groups. The error came from
grepping for `import ccxt|web3|solana|eth_account` and concluding from that single probe; the DeFi adapters reach chains
via `_defi_rpc.py` rather than importing `web3`, so the probe could not have found them. Listing the directory would
have taken one command. Same failure class as the `venue_balance_tracker` and shadow-`BookType` errors the same week —
recorded here because a repository-disclosure decision was being made partly on that answer. The read-only property was
correct and is now verified at the ABC rather than inferred.

## Deferred work after 2026-08-14

| Item                                                                | Kind               | Blocked on                                                                                                             |
| ------------------------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Measure what the generic token-balance reader closes of the ~27 gap | Not done           | nobody — do this BEFORE building 27 modules                                                                            |
| Build generic reader + bespoke exceptions (both services)           | Not done           | the measurement above                                                                                                  |
| Lido / Marinade / Kamino / Jupiter position adapters                | Not done           | may be subsumed by the generic reader — measure first                                                                  |
| 3 directional SIT invariants                                        | Not done           | nobody                                                                                                                 |
| Per-venue instruction-ACTION coverage audit                         | Not done           | nobody — this audit proved modules EXIST, not that each handles every action                                           |
| B6 — a consumer per governing section                               | **Operator-owned** | a design call on which consumer owns each section; an agent already investigated 4 and correctly declined to force one |
| Disclosure call on betfair / ibkr / polymarket adapters             | **Operator-owned** | out-of-mandate venues; inert unless configured, so cost-free to ship                                                   |
| Review of the other session's 7 shipped tasks                       | Not done           | their ships landing; UAC confirmed at `8c72b501`                                                                       |
| Artifact pass (reconciliation + venue/instruction registry)         | Not done           | the chunks being verified landed                                                                                       |

**Recommended next: verify the other session's ships, then measure the generic-reader coverage.** The first is
verification of work already claimed done (and two of its codex outputs were found orphaned tonight, so the claim needs
checking); the second decides whether the venue gap is 27 modules of work or roughly one plus a handful of exceptions —
an order-of-magnitude difference in both build cost and disclosure surface.

## Lessons — 2026-08-14

- **A method name is not its return type.** `venue_balance_tracker.get_all_balances()` returns the SPORTS `VenueBalance`
  (`is_exchange`, "Betfair, Matchbook", float `balance`). Naming it as the DeFi balance source in a spec cost a
  sub-agent real time before it pushed back correctly. **Read the type.**
- **Wrong-vocabulary probes produced FIVE false conclusions this week**, the last one tonight: verifying
  `transfer-rebalance.md` at origin with a phrase that belongs to `benchmark-fills.md` and briefly reading MISSING on
  work that had shipped hours earlier. Before concluding absence, confirm the probe could have found the thing.
- **`git status` untracked (`??`) does not mean unshipped.** `safe-doc-push` commits from an isolated worktree, so a
  file it pushed still shows untracked locally. Four PM files looked at-risk tonight and were already at origin — but
  **two genuinely were not**, and only checking each against `origin/` separated them.
- **Orphaned outputs are a real failure mode of task-splitting.** Chunk 2 wrote two codex docs; the ship tasks named
  UAC, strategy-service and execution-service and nobody owned PM, so both sat uncommitted for 2.5 hours. **When
  splitting work, name the doc repo in someone's ship scope.**
