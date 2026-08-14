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
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
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

`execution_service/defi_execution/protocols/` ships **38 `.py` modules** (not 40 — recounted 2026-08-14), which the tier
table below splits into 9 live-capable, 16 simulation-only and the rest infrastructure. The raw list: `aave`, `morpho`,
`uniswap`, `lido`, `marinade`, `kamino`, `jupiter`, `orca`, `raydium`, `pendle`, `convex`, `yearn`, `beefy`, `etherfi`,
`kelpdao`, `renzo`, `puffer`, `rocket_pool`, `solblaze`, `symbiotic`, `eigenlayer`, `jito_restaking`, `karak`, `idle`,
`aster`, `hyperliquid`, `bybit`, `weth`, plus `cctp` / `bridge` for transfers. `venues/` adds `deribit`, `lido`,
`uniswap` connectors.

## The asymmetry

> **⚠️ CORRECTED 2026-08-14 — the original version of this section OVERSTATED execute capability.** It counted a
> protocol as executable because a module for it exists. That is not the same property. Re-measured below by reading
> what each module's write path actually does; the corrected numbers are smaller, and the shape of the problem changed.

| Asset group | Can EXECUTE (live) | Can READ positions | Verdict                                               |
| ----------- | ------------------ | ------------------ | ----------------------------------------------------- |
| CeFi        | yes                | yes (ccxt-generic) | **Balanced** — both sides covered                     |
| DeFi        | **~10, not ~30**   | **3**              | a read gap AND a smaller-than-claimed execute surface |

**This is the wrong way round.** Being able to act without being able to see is strictly worse than the inverse: an
instruction executes, the position changes, and nothing can confirm it landed or detect drift afterwards.

### The three tiers (measured 2026-08-14, by reading each module's write path)

`defi_execution/protocols/` ships 38 `.py` modules, but they are not one kind of thing:

| Tier                     | What it is                                                                                                | Modules                                                                                                                                                                                              |
| ------------------------ | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1 — live-capable**     | branches on `is_live` into a real executor, or makes real RPC/HTTP calls and `send_transaction`s          | `aave` (+`aave_live`), `uniswap` (+`uniswap_live`), `hyperliquid`, `marinade`, `kamino`, `jupiter`, `orca`, `raydium`, `eigenlayer`                                                                  |
| **2 — simulation-only**  | in-memory `_balances` dict, seeded by `set_balance()`; write ops do arithmetic and return `success: True` | `lido`, `rocket_pool`, `etherfi`, `renzo`, `puffer`, `kelpdao`, `symbiotic`, `karak`, `jito_restaking`, `solblaze`, `yearn`, `beefy`, `convex`, `idle`, `pendle`, `morpho`, **`weth`**, **`bridge`** |
| **3 — libraries / ABCs** | correctly not-live: base classes, encoders, mode routers                                                  | `base`, `solana_base` (ABCs holding the live machinery), `uniswap_encoding`, `solana_lst_devnet` (paper-mode devnet router, by design), `_hyperliquid_*`                                             |

**Tier 1 also includes** the Solana tree, which inherits `BaseSolanaConnector` rather than `BaseConnector`: `marinade`,
`kamino`, `jupiter`, `orca`, `raydium` — all real (`aiohttp` + `send_transaction`). And `bybit.py` is live via
`BybitCCXTAdapter`; it sits in this directory but is a CeFi perp connector, not a DeFi protocol.

**Corrected 2026-08-14 (second pass): the simulation-only count is 18, not 16.** `weth` and `bridge` were initially
filed as infrastructure and are not — `WethConnector.wrap()` logs, then returns a simulated `WrapResult` unconditionally
(the code comment says "Paper trade mode" but there is no branch), and `bridge.py` carries `SOCKET_API_BASE` plus
docstrings describing the Socket v2 integration while containing no calling code at all. Both are scaffolds. The first
pass mis-filed them because "infrastructure" was inferred from the module's ROLE rather than read off its write path —
the same error as the original audit, one level down.

**Tier 2 is the finding.** `LidoConnector.stake()` does not build a transaction — it subtracts from
`self._balances["WETH"]`, adds to `self._balances["wstETH"]`, and returns `{"success": True, ...}`. `get_balance()`
reads the same dict. `connect()` sets a flag.

**And the tier-2 modules accept `is_live` and never read it.** All 16 take `is_live` in `__init__`, pass it to
`super().__init__`, and contain **zero** `if self.is_live` branches and **zero** `NotImplementedError` guards. So
`LidoConnector(config, is_live=True).stake(Decimal("10"))` returns success having moved nothing on-chain. The parameter
reads as a capability the code does not have.

Severity is bounded today, and it is worth being precise about why: the one live construction site
(`cli/handlers/live_execution_handler.py:495`) passes only `aave_connector=AAVEConnector(..., is_live=True)` — tier 1 —
and `DefiAdapter` raises `ValueError("LidoConnector not configured")` when the Lido path is called without one. So the
live path fails loudly rather than faking a fill. The trap is latent, not active. But it is one wiring line away from
active, and a client engineer reading this repo will find it.

### It hits the carve-out archetypes directly

| Archetype                  | Leg           | Execute                                  | Read position |
| -------------------------- | ------------- | ---------------------------------------- | ------------- |
| `CARRY_STAKED_BASIS` (ETH) | Lido stETH    | ❌ **simulated only** (`lido.py` tier 2) | ❌            |
| `CARRY_STAKED_BASIS` (SOL) | Marinade mSOL | ✅ real (`aiohttp` + `send_transaction`) | ❌            |
| `CARRY_RECURSIVE_STAKED`   | Kamino borrow | ✅ real (`aiohttp`)                      | ❌            |
| SOL perp leg               | Jupiter       | ✅ real (`aiohttp`)                      | ❌            |

The ETH row is the correction. **The ETH staked-basis archetype has no live Lido execution at all** — neither
`defi_execution/protocols/lido.py` nor `venues/lido.py` (see the dual-path finding below) can stake ETH on-chain. The
earlier "✅ execute" was read off module existence, which this table now shows is not evidence of the property.

So today we can open both legs of a staked-basis position on SOL and reconcile neither; on ETH we cannot open the
staking leg for real either.

### Dual path — three connector classes exist twice

`LidoConnector`, `UniswapConnector` and `BaseConnector` are each defined in **two** places: `execution_service/venues/`
and `execution_service/defi_execution/protocols/`. Both `LidoConnector`s are tier 2 (identical in-memory `_balances`
simulation); `venues/uniswap.py` has zero network references while `protocols/uniswap.py` has a live executor. This is a
same-data-consumption dual path and falls under the operator's standing ruling: **unify to one SSOT path and complete
the build — do not delete the half that is unfinished.**

## Todos

- [ ] [AGENT] P0. **Build DeFi position adapters for the carve-out path first** — Lido, Marinade, Kamino, Jupiter. These
      are not "more venues"; they are the reconciliation side of the two archetypes we are shipping real. Build the code
      fully (operator: _"we don't need credentials to fully build the code, not just stubs"_) — credentials gate RUNNING
      an adapter, not writing one.
- [x] [AGENT] P0. ✅ **Generic-first, bespoke-by-exception — operator ruling 2026-08-14, and it applies to BOTH
      services** (recorded here, in `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` — conversational
      ruling, no separate codex doc exists for it). strategy-service half **SHIPPED**: `strategy-service@4dbbd98e1d`.
      execution-service half **SHIPPED**: `execution-service@2b92d6ac69`. The summary below describes the code as
      shipped. execution-service@2b92d6ac69: built `defi_execution/protocols/_evm_generic.py` (read-only Web3
      connection, ERC-20 balanceOf reader, generic view-call reader, approve+build tx helper) and wired 14 of the 18
      simulation-only modules onto it end-to-end (real read + real write): Lido, Rocket Pool, EtherFi, Renzo, Puffer,
      KelpDAO, Yearn, Beefy, Idle, Convex, Morpho, Pendle, Symbiotic, Karak, plus WETH — `sign_and_send_transaction()`
      (already on `BaseConnector`) does the actual build/sign/broadcast, so each protocol module is now its ABI
      fragment + two calls, not a hand-rolled executor. Morpho and Pendle are config-gated (permissionless markets — the
      caller supplies the on-chain MarketParams/SY-YT-PT addresses, never a guessed default). **Measured, not assumed**:
      Solblaze and Jito Restaking got real SPL balance reads but their write paths stay simulation-only — the SPL
      stake-pool / jito-restaking Anchor programs are non-ABI (fixed account-list, not named functions) and the
      `spl-stake-pool` SDK is not a dependency of this repo, so hand-rolling the instruction bytes was judged too risky
      to guess; flagged as a residue item below, not silently closed. strategy-service@4dbbd98e1d (SHIPPED): built
      `position_interface/adapters/generic_token_balance.py` (dependency-light — raw JSON-RPC `eth_call` for EVM, no
      web3 SDK required; `solana-py` for SPL) covering the same "wallet+token+chain→balance" shape for the read side.
      **Residue**: Marinade/Kamino/Jupiter position adapters (todo above) are NOT yet wired to the generic reader —
      SOL-side LST reads fit the shape, Kamino's lending-position and Jupiter's DEX-position shapes likely don't and
      need their own read logic; not measured this session.
- [x] [AGENT] P0. ✅ **Make a simulation-only connector refuse live mode instead of reporting success** —
      execution-service@9946ba5a3. `BaseConnector.supports_live` defaults to `False` (fail-closed) and `__init__` raises
      `SimulationOnlyConnectorError` when `is_live=True` reaches a connector that has not declared a live path. The six
      BaseConnector-tree connectors that genuinely execute opted in explicitly (`aave`, `hyperliquid`, `uniswap`,
      `eigenlayer`, `aster`, `cctp`) so no working live path broke. **Evidence**: gate green (8101 passed, 0 failed —
      the run before it caught 3 real defects in the new fixtures); verified at origin by reading the blobs back, all 6
      opt-ins and 6 tests present. `tests/unit/defi_execution/test_connector_live_capability.py` carries negative
      controls both ways (the guard fires; simulation still works; a declared connector is not blocked) plus a Lido
      regression anchor asserting `supports_live is False` — **invert that anchor when Lido's live path lands, do not
      delete it.** **Not covered**: the Solana tree (`BaseSolanaConnector`) — separate base class, all its connectors
      are already live; mirror the declaration there when that tree is next touched.
- [x] [AGENT] P0. ✅ **Unify the duplicated connector classes to one SSOT path** — SHIPPED,
      `execution-service@2b92d6ac69`. Confirmed `venues/lido.py`/`venues/uniswap.py`/`venues/base_connector.py` had
      **zero production callers** (`venues/registry.py`'s `AdapterRegistry` only knows `ExternalVenueAdapter` from
      `venues/base.py` — a different class hierarchy; same "dead duplicate" shape already established for
      `venues/morpho.py`/`venues/etherfi.py` on 2026-07-29). Ported the two methods unique to the `venues/` copies —
      `UniswapConnector.swap_exact_output()` and `LidoConnector.wrap_steth()`/`unwrap_wsteth()` — into
      `protocols/{uniswap,lido}.py` (with a real live-mode path for the Lido pair; Uniswap's exact-output stays
      simulation-only pending SwapRouter02 `exactOutputSingle` calldata encoding — see that method's docstring), then
      deleted the three `venues/` files and their orphaned test file, folding equivalent test coverage into
      `tests/defi_execution/unit/test_lido_uniswap_ported_methods.py`.
- [x] [AGENT] P0. ✅ **Re-measure DeFi execute coverage on the three-tier model and correct every downstream claim** —
      SHIPPED, `execution-service@2b92d6ac69`. Of the 18 tier-2 (simulation-only) modules this issue counted, **16 are
      now tier-1 (real reads + real writes)** — Lido, Rocket Pool, EtherFi, Renzo, Puffer, KelpDAO, Yearn, Beefy, Idle,
      Convex, Morpho, Pendle, Symbiotic, Karak, WETH, plus `bridge.py`'s `SocketBridgeConnector` (which turned out to be
      a DIFFERENT bug from the "no calling code" description below — see correction). **2 stay tier-2 by measurement,
      not oversight**: Solblaze and Jito Restaking (SPL stake-pool programs need the `spl-stake-pool`/`jito-restaking`
      SDKs, not installed — see the todo above). **Correction to this doc's own "no calling code" claim on
      `bridge.py`**: reading the current code (this session) showed `SocketBridgeConnector` already called Socket's real
      `/quote` API — the actual bug was `bridge()` returning `TransferStatus.CONFIRMED` from a quote alone, without ever
      building/signing/broadcasting a transaction (a silent-success bug, not a scaffold; same class as the tier-2
      finding). Fixed: `bridge()` now calls Socket's `/build-tx`, approves if needed, and broadcasts via
      `sign_and_send_transaction()`, returning `PENDING` (never a fabricated `CONFIRMED`). Also found and fixed the same
      bug class in `aster.py` (not in this issue's original scope): `_place_order_live()` signed orders but never POSTed
      them, returning a fabricated `status="submitted"` — now makes a real `aiohttp` POST/DELETE to `/fapi/v1/order`.
      **New corrected coverage: DeFi execute ~16 genuinely live** (up from the "~10, not ~30" figure below, which
      predates this session — that "~10" already excluded the 16 tier-2 modules entirely; it did not yet count them as
      converted). **Do not restate a module count as a capability count** — the two Solana modules above still show up
      in a raw `ls` of the directory; they are not live.
- [x] [AGENT] P0. ✅ **Ship the execution-service DeFi connector liveness change set** — SHIPPED,
      `execution-service@2b92d6ac69` on `live-defi-rollout`, `ahead=0` verified against origin, content spot-checked via
      `git show origin/live-defi-rollout:<path>` (not just a clean-tree proxy). 71 files (all 30 protocol modules +
      `_evm_generic.py` new + 3 `venues/` deletions + 21 newly-trackable `tests/unit/data/*.py` files + `.gitignore` + 6
      test-file fixes + wiring/loader files). Gate evidence: 8493 passed, 0 failed, `ALL QUALITY GATES PASSED`, sentinel
      `.qg_last_passed_sha=9180343b6...`. **What actually blocked shipping (correcting the prior guess in this todo —
      dependency-skew/RAM-pressure was NOT the real cause)**: (1) a concurrent session landed
      `execution-service@3a72912c8` (TransferType→BusTransferType migration) on `bridge.py` **on top of a version that
      predated this session's fabricated-CONFIRMED fix** — `git pull --rebase --autostash` (quickmerge's own
      reconciliation step) hit a real content conflict between that regressed upstream and this session's correct
      real-execution rewrite; resolved by keeping this session's version (it's a strict superset — real execution + the
      same enum migration). (2) `tests/unit/data/` (21 hand-written test files, incl. the 5 pre-existing data-loader
      bugs already fixed this session) turned out to have **never been in git history** — a bare `data/` pattern in
      `.gitignore` (meant for repo-root generated data) matches a directory named `data` at ANY depth, silently
      swallowing the entire `tests/unit/data/` suite since whenever it was created. Fixed with a scoped
      `!tests/unit/data/` negation (+ a follow-up `__pycache__` re-exclusion inside it, since a bare `!dir/**` negation
      also un-ignores bytecode cache). (3) the post-conflict gate run surfaced 2 uncited contract addresses
      (null-referral zero-address sentinels in `idle.py`/`lido.py` — fixed via `# QG-allow: defi-citation`) and 20
      method-size violations (real on-chain deposit/withdraw logic pushed several methods over the 50-line cap) across
      13 files — fixed by extracting each live-mode branch into a `_deposit_live()`/`_withdraw_live()` helper, matching
      the pattern `bridge.py`'s own `_execute_bridge_tx()` already established. (4) the fully-green gate runs
      (mid-session) vs the reds seen right after `.env` restoration were the SAME already-diagnosed pydantic-settings
      `.env`-pollution artifact recurring — moved `.env` aside again for the final verify pass, restored it immediately
      after, never touched/deleted it.
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

| Item                                                                | Kind                 | Blocked on                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Measure what the generic token-balance reader closes of the ~27 gap | **Partly done**      | closes the LST-shaped share (Lido et al.); Kamino/Jupiter's non-balance-shaped positions still unmeasured                                                                                                                                                                                                                                                                                   |
| Build generic reader + bespoke exceptions (both services)           | **Done**             | `_evm_generic.py` (execution-service) + `generic_token_balance.py` (strategy-service), this session                                                                                                                                                                                                                                                                                         |
| Lido / Marinade / Kamino / Jupiter position adapters                | **Partly done**      | Lido's wstETH balance is coverable via the new generic reader (not yet wired as a named adapter); Marinade/Kamino/Jupiter still need their own read logic                                                                                                                                                                                                                                   |
| 3 directional SIT invariants                                        | Not done             | nobody                                                                                                                                                                                                                                                                                                                                                                                      |
| Per-venue instruction-ACTION coverage audit                         | Not done             | nobody — this audit proved modules EXIST, not that each handles every action                                                                                                                                                                                                                                                                                                                |
| B6 — a consumer per governing section                               | **Operator-owned**   | a design call on which consumer owns each section; an agent already investigated 4 and correctly declined to force one                                                                                                                                                                                                                                                                      |
| Disclosure call on betfair / ibkr / polymarket adapters             | **Operator-owned**   | out-of-mandate venues; inert unless configured, so cost-free to ship                                                                                                                                                                                                                                                                                                                        |
| Review of the other session's 7 shipped tasks                       | **Done, indirectly** | its `execution-service@9946ba5a3` (the live-mode guard) landed at origin mid-session here and was reconciled via `git pull --rebase --autostash` — verified by reading the merged blob back; one real defect caught in reconciliation (its `aster.py` opt-in declared `supports_live=True` WITHOUT fixing the underlying silent-success bug, which this session's `aster.py` fix addresses) |
| Artifact pass (reconciliation + venue/instruction registry)         | Not done             | the chunks being verified landed, AND the corrected tier numbers above                                                                                                                                                                                                                                                                                                                      |
| Live-mode guard base mechanism (`supports_live` + fail-closed)      | **Done, shipped**    | execution-service@9946ba5a3 (base mechanism) + execution-service@2b92d6ac69 (Solana declaration + extension to all 18 modules)                                                                                                                                                                                                                                                              |
| Unify the 3 duplicated connector classes                            | **Done, shipped**    | execution-service@2b92d6ac69                                                                                                                                                                                                                                                                                                                                                                |
| Wire real writes for 16 of the 18 tier-2 modules                    | **Done, shipped**    | execution-service@2b92d6ac69; Solblaze/Jito Restaking stay simulation-only pending the SPL SDK dependency                                                                                                                                                                                                                                                                                   |

**Recommended next: measure the generic-reader coverage, then fix the tier-2 live-mode guard.** The review of the peer
session's work is _not_ the next item any more — its output is still uncommitted in a live session, so there is nothing
at origin to verify and touching that tree would race their edits. The measurement decides whether the venue gap is 27
modules of work or roughly one plus a handful of exceptions; the guard closes the one finding here that could produce a
silently-wrong result rather than a loud failure.

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
- **Module existence is not capability — this is the same wrong-vocabulary error in a new costume.** The first version
  of this audit scored a protocol "✅ execute" because `lido.py` exists. Reading the write path showed 16 of 38 modules
  are in-memory simulations. The tell was visible in the public surface all along and I did not read it: a method named
  `set_balance()` / `set_exchange_rate()` is a **test seeder**, and a module whose API lets you _set_ the balance is not
  reading it from a chain. **Grep the write path, not the file listing.**
- **`is_live` being in a signature does not mean it is read.** All 16 tier-2 connectors accept it, forward it to
  `super().__init__`, and never branch on it. A parameter is a claim; `rg -c 'if self\.is_live'` is the measurement.
- **ripgrep's `-r` is `--replace`, not `--recursive`** (grep's is recursive). `rg -rn 'LidoConnector|...'` silently
  substituted every match with the literal `n` and produced plausible-looking but corrupted output —
  `class n(BaseConnector)`. It fails _quietly_, as valid-looking results. rg recurses by default; drop the `-r`.
- **A wrapper that converts failure into a success-shaped value is the most dangerous shell habit in this workspace.**
  Two instances in one session, both self-inflicted: `rg -c ... $f || echo 0` turned "file not found" (wrong cwd) into
  "0 matches", i.e. a false ABSENCE across 16 modules; and `cmd > log 2>&1; echo "EXIT=$?"` reports **`echo`'s** status,
  so a gate run with 3 failing tests was recorded as exit 0. Both produce a confident wrong answer rather than an error.
  Put the command last in the pipeline, and never `||` a default onto a measurement.
- **`cd` persists between tool calls; a compound `cd X && …` that gets killed may not persist it.** Several probes ran
  from the wrong directory. Use absolute paths in any command whose result you intend to reason about.
- **A passing test is invisible in gate output — only failures are named.** Grepping the log for the new test file
  returned zero and looked like "it never ran". The real evidence was arithmetic: `8098 passed + 3 failed` became
  `8101 passed`. Count the delta; don't grep for the filename.
- **Read the class boundary before calling a docstring self-contradictory.** `strategy_id` appearing as a field while a
  nearby docstring said it was "removed as redundant" looked like a contradiction; it was two adjacent types
  (`WalletConfig` vs `TradingWalletConfig`) with opposite, and individually correct, resolutions.

## Lessons — 2026-08-14 (session 2)

- **A concurrent session working the identical P0 todo is a real, not hypothetical, risk in this multi-agent
  workspace.** Mid-session, `git fetch` on execution-service surfaced `9946ba5a3` — another session had independently
  built the same `supports_live` fail-closed guard, on 6 of the same connectors, plus the exact test file this session
  had also just written from scratch (`test_connector_live_capability.py`). Caught only because
  `git pull --rebase --autostash` was run BEFORE committing, not after — committing first would have produced a real
  conflict against a shared branch instead of a clean local reconciliation. **Check `git log origin/<branch> -3` before
  every ship, not just before starting.**
- **Reconciliation is a chance to catch a defect, not just merge text.** Diffing the two independent `aster.py`
  implementations of the same declaration showed the other session set `supports_live=True` on Aster WITHOUT actually
  fixing the underlying bug (its `_place_order_live()` still only signed and returned a fabricated `"submitted"`, never
  POSTing) — meaning their commit alone would have mislabeled a still-broken connector as fixed, exactly the
  silent-success failure class this whole guard exists to prevent. A line-by-line reconciliation diff surfaces this;
  blindly taking "theirs" or "ours" on the whole file would not have.
- **A local sibling-repo checkout can be stale in a way that fails an UNRELATED test with a confusing error.**
  `strategy-service`'s `test_loads_arbitrage_price_dispersion` failed with a set-equality mismatch that had nothing to
  do with this session's diff; the root cause was `unified-trading-pm`'s local working copy being 1400+ commits behind
  origin, so a specific archetype doc's `topology_requirements` frontmatter was pre-correction. Diffing the local file
  against `git show origin/<branch>:<path>` found it in under a minute; a naive read of the test failure alone would not
  have pointed at a sibling repo's staleness.
- **Not every red test blocking a ship is caused by the diff being shipped — verify with `git stash -u` before assuming
  otherwise.** A second, unrelated failure (`TypeError: argument of type 'VenueCapabilityRecord' is not iterable`)
  appeared only after the archetype-doc fix above, looking causally connected. Stashing ALL local changes and
  reproducing the failure on a byte-for-byte clean tree proved it was pre-existing flakiness (xdist worker-order
  sensitive), unrelated to anything in this session — the ship succeeded on retry with no code change. Assuming
  causation from mere sequencing would have sent this session chasing an unrelated bug in a different subsystem.
