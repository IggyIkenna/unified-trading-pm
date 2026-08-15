---
doc_type: issue
title: E2E wiring — what is built vs what is REACHABLE on a production path
summary: >-
  Caller-graph audit of the strategy→execution→venue chain, prompted by the discovery that Marinade/Kamino/Jupiter
  connectors have zero production callers. Recurring finding across three sessions: components are built, complete and
  tested in isolation, and nothing on a live path calls them. Confirms a broken seam on the emergency close-all path
  (strategy POSTs to /api/orders; execution-service exposes no such route), zero production callers for
  V2InstructionRouter and DefiAdapter, and a live handler wiring exactly one of 38 DeFi connectors. Also records the
  read side as genuinely closed and registry-driven. Written to be dispatchable.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution, strategy]
repos: [strategy-service, execution-service, unified-api-contracts, system-integration-tests]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [e2e-wiring, reachability, caller-graph, reconciliation, disclosure]
priority: P0
source: operator-request-2026-08-15
parent_epic: infrastructure_master
related:
  [
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
  ]
created: 2026-08-15
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# E2E wiring — built vs REACHABLE

> **Operator framing 2026-08-15**: _"we need to have everything wired e2e so investigate and complete with docs that we
> can continue to dispatch — we should now have a round up of all the things we need to complete documented."_

**The recurring defect class this documents.** Across three sessions the same shape keeps appearing: something real is
built, tested and complete, and **nothing on a production path can reach it**. It survives every review that asks "does
this work?" because the honest answer is yes — the question that fails is "does anything call it?".

Instances found so far, all independently verified:

| Thing                                  | Built?              | Reachable?                                                   |
| -------------------------------------- | ------------------- | ------------------------------------------------------------ |
| `GenericTokenBalanceAdapter`           | yes, +tests         | **was no** — nothing imported it (FIXED, see below)          |
| 24 plan-hygiene tests                  | yes                 | **was no** — directory absent from `PYTEST_UNIT_DIR` (FIXED) |
| `EnhancedAlphaComparator`              | yes                 | **no** — no production caller                                |
| Marinade / Kamino / Jupiter connectors | yes, real RPC       | **no** — no production caller                                |
| `V2InstructionRouter`                  | yes, all 14 actions | **no** — no production caller                                |
| `DefiAdapter`                          | yes                 | **no** — zero construction sites outside tests               |

**Reading a method's body answers "can this act". Grepping its instantiation sites answers the load-bearing question:
"does anything ask it to."** Every audit in this corpus should now do the second.

## FINDING 1 (P0) — the emergency close-all path targets an endpoint that does not exist

`strategy_service/close_all/carry_staked_basis.py:133` (and `arbitrage_price_dispersion.py:132`) POST to
`{execution_service_url}/api/orders`.

**execution-service exposes no such route.** Its complete surface, from `api/app.py`'s five `include_router` calls:

| Router                   | Prefix     |
| ------------------------ | ---------- |
| `manual_instruction_api` | `/manual`  |
| `preview_routes`         | `/preview` |
| `evidence_router`        | (none)     |
| `make_health_router`     | health     |

A repo-wide search for a route containing `orders` returns only result-serializer dict keys — no endpoint. So the
close-all path 404s at runtime.

**Why this is the worst one to have latent**: close-all is the emergency flatten path. It is invoked precisely when
something is already wrong, and it fails at the moment it is needed. Nothing catches it today because no test exercises
strategy→execution over HTTP, and both halves pass their own suites.

**Fix requires a ruling, not just code** — the two sides disagree about the contract, and it is not obvious which is
right: does execution-service gain an `/api/orders` endpoint, or does close-all migrate onto the existing
`/manual/instruction` surface (which carries precheck / approve / reject semantics close-all may not want)?

## FINDING 2 (P0) — one of 38 DeFi connectors is reachable from the live handler

`cli/handlers/live_execution_handler.py:495` constructs exactly one connector: `AAVEConnector(is_live=True)`.
`DefiAdapter` — which holds Uniswap / AAVE / Lido / Jupiter — has **zero construction sites outside tests**.

So the execute-side tier table in
[the venue-coverage issue](/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md) is
measuring the wrong property. It scored connectors on whether their write path is real. **A connector with a real write
path and no caller executes nothing.** That table needs re-deriving on reachability, and any client-facing number
derived from it is currently unsupported.

## FINDING 3 — the read side IS genuinely closed (contrast case)

Recorded because it is the one place the chain is complete, and it shows what "done" looks like here:

- `unified-api-contracts@53a5adc7` + `@bed96aa0` — LST token address SSOT, 6 reachable cited addresses.
- `strategy-service@5b2a50ed` — factory routes LST venues from that SSOT; **8 DeFi venues readable, up from 3**.
- Reachability proven by a routing test that resolves through `get_position_adapter()`, the resolver every caller uses —
  not by asserting the adapter class exists.
- Registry-driven, so adding an address makes a venue readable with **no code change** — the read side cannot silently
  fall behind the execute side again.

## Todos

- [ ] [OPERATOR] P0. **Rule on the close-all contract** — new `/api/orders` endpoint in execution-service, or migrate
      `close_all/*` onto `/manual/instruction`? Both halves currently pass their own tests while the seam is broken.
- [ ] [AGENT] P0. **Implement whichever side the ruling picks, and add the missing HTTP-level test** — the defect
      survived because nothing exercises strategy→execution over the wire. A contract test that would have failed here
      is worth more than the fix.
- [ ] [AGENT] P0. **Re-derive the execute-side tier table on CALLER-GRAPH reachability.** For each of the 38 protocol
      modules record: write path real? AND reachable from a production entry point? Both must be true to score covered.
      Correct every downstream number, including the client artifacts.
- [ ] [AGENT] P0. **Decide what `V2InstructionRouter` and `DefiAdapter` are for.** Both are complete and uncalled.
      Either wire them into the live path or mark them explicitly as not-yet-wired in their own docstrings — leaving a
      complete-looking uncalled component is how this class of defect propagates.
- [ ] [AGENT] P1. **Add a reachability gate.** A check that fails when a connector/handler/router in a covered-venue
      list has no production caller. This defect class has recurred six times; a detector is worth more than six fixes.
- [ ] [AGENT] P1. **SIT invariant 2 needs a mode axis first** (operator ruling 2026-08-15: build the axis, do not weaken
      the invariant). `position_interface/` has one boolean per venue and no batch/live/paper distinction anywhere in
      adapter resolution. Design pass required before the invariant is expressible. Invariants 1+3 already landed
      (`system-integration-tests@da65ae1`); invariant 4 (UAC↔execution address drift) is unstarted.
- [ ] [AGENT] P1. **Build the 4 bespoke position readers** — Morpho health factor, Pendle maturity, Symbiotic + Karak
      withdrawal queues. A bare token balance MISREPRESENTS these rather than merely missing them.
- [ ] [AGENT] P1. **Migrate execution-service protocol modules onto the UAC LST address SSOT** — 6 addresses currently
      exist in both places; invariant 4 guards the window until the migration lands.
- [ ] [AGENT] P2. **Fix `check_pytest_unit_dir_coverage.py`** — it exists to catch test dirs missing from
      `PYTEST_UNIT_DIR` and passed while 24 tests across 4 files sat uncollected.
- [ ] [OPERATOR] P2. **Cited `LST_TOKEN_GENESIS` date for Kelp/rsETH and ether.fi/eETH** — both have cited addresses but
      no venue declaration. That map drives coverage denominators, so an invented date corrupts them silently.

## FINDING 4 — a second, dead position-adapter resolver

`position/position_interface/` has **two** adapter-building paths:

| Resolver                                    | Production callers                                                                                |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `factory.get_position_adapter(venue, **kw)` | **yes** — `AccountQueryClient` → `balance_reconciliation_engine` + `position/engine/orchestrator` |
| `routing.create_position_adapter(config)`   | **none** — zero callers outside its own module and the `__init__` re-export                       |

`routing.py` carries a full parallel implementation (`PositionDataSourceConfig`, `_build_defi_adapter`,
`_build_cefi_adapter`, `_build_market_adapter`, `_build_cefi_alt_adapter`) and a typed config object the factory path
does not have. Per the standing ruling this is a **unify-and-complete**, not a delete: `routing.py`'s typed
`PositionDataSourceConfig` is arguably the better interface, and the LST wiring currently lives only in `factory.py`.

Recorded also because it nearly bit: the LST read-side wiring (`strategy-service@5b2a50ed`) went into `factory.py`. Had
production used `routing.py`, that fix would have been a seventh unreachable component — authored by the same session
that documented the defect class. Verified reachable before claiming otherwise.

## DESIGN PASS — the mode axis for position reading (operator ruling 2026-08-15)

Operator chose "add the mode axis to `position_interface/` first" over weakening SIT invariant 2.

**Current state**: `BasePositionAdapter` has **zero** mode awareness. What exists is ad-hoc and per-family — CeFi
adapters take `testnet: bool`, DeFi adapters take `fork_mode` / `tenderly_fork_rpc_url`. Neither is the batch/live/paper
axis; both are network-selection flags.

**Canonical vocabulary is `OperationalMode`** (`unified_api_contracts/internal/modes.py:215`): `LIVE` · `MANUAL` ·
`BACKTEST` · `PAPER`. Note the ruling said "batch" — the canonical term is `BACKTEST`, and there is a fourth mode
(`MANUAL`) the ruling did not mention.

**The design question, and why it is not mechanical.** Reconciliation compares the internal book against _independent
venue truth_. That independence is what makes a match meaningful. Per mode:

| Mode       | Is there independent venue truth to read?                                                                                                                            |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LIVE`     | Yes — mainnet venue API / chain RPC.                                                                                                                                 |
| `PAPER`    | **Yes** — CeFi paper accounts are real venue-side accounts (Binance testnet, IBKR paper TWS ports 7497/4002, already known to `routing.py`). Independently readable. |
| `BACKTEST` | **No** — the "venue" is the simulator. Reading from it makes reconciliation compare the book against itself.                                                         |
| `MANUAL`   | Same as `LIVE` (real venue), but instruction origin differs — likely not a reader distinction at all.                                                                |

**So the axis is meaningful for LIVE/PAPER and degenerate for BACKTEST**, and the existing `testnet: bool` is the
two-state shadow of it. The dangerous outcome to avoid: a `BACKTEST` reader that returns simulator state, producing a
reconciliation that **always agrees, detects nothing, and reports green** — the same fabricated-agreement failure class
as a zero-token adapter reporting zero balances.

`reconciliation_engine.py` currently has **no mode guard at all** — it publishes `RISK_ALERTS` regardless of mode.

**Proposed shape** (needs operator confirmation before a refactor touching every adapter):

1. `BasePositionAdapter` gains an explicit `operational_mode: OperationalMode`, replacing per-family `testnet` /
   `fork_mode` flags as the SSOT for endpoint selection.
2. `LIVE` → mainnet endpoints; `PAPER` → venue paper/testnet endpoints (real, independent).
3. `BACKTEST` → **no external adapter is constructed**. Reconciliation in backtest either skips, or compares against the
   backtest ledger with an explicit non-independent marker so a green result cannot be mistaken for evidence.
4. Only then is SIT invariant 2 expressible, and it should assert a reader for `LIVE` and `PAPER` — asserting one for
   `BACKTEST` would be asserting the tautology exists.

## How to verify a reachability claim (method, so this is repeatable)

1. **Find the production entry points** — `rg 'FastAPI\(|APIRouter\(|def main\('`, excluding tests.
2. **Grep the component's instantiation sites**, excluding its own module and `__init__` re-exports. A re-export is not
   a caller. A docstring mention is not a caller.
3. **Follow the chain to a real boundary** — an HTTP route, a CLI entry point, a scheduled job. Stopping at "something
   imports it" is how `V2InstructionRouter` scored as wired.
4. **State which property you measured.** "Write path is real" and "reachable in production" are different claims and
   this corpus has conflated them repeatedly.
