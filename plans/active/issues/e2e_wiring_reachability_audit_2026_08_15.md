---
doc_type: issue
title: E2E wiring — what is built vs what is REACHABLE on a production path
summary: >-
  Caller-graph audit of the strategy→execution→venue chain, prompted by the discovery that Marinade/Kamino/Jupiter
  connectors have zero production callers. Recurring finding across five sessions: components are built, complete and
  tested in isolation, and nothing on a live path calls them. Confirms a broken seam on the emergency close-all path
  (strategy POSTs to /api/orders; execution-service exposes no such route, ruling recorded, fix not yet shipped).
  V2InstructionRouter deleted as dead code and DefiAdapter rewired 2026-08-15 (execution-service@37bfaeed0b) —
  re-derived reachability table shows 6 of 32 DeFi connector modules (19%) genuinely reachable-and-live, down from a
  "~16 genuinely live" figure that measured write-path capability, not reachability. Two new uncalled-component
  instances found and documented: RecursiveLoopOrchestrator's real AAVE/Uniswap path is unreached from its one
  production construction site, and QuoteMaintainer has zero production callers. LST address SSOT migration (6
  duplicated addresses) shipped. Also records the read side as genuinely closed and registry-driven.
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
parent_epic: security_and_cross_cutting_master
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
context_scope:
  [
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    strategy-service/strategy_service/close_all/carry_staked_basis.py,
    execution-service/execution_service/api/app.py,
    execution-service/execution_service/api/main.py,
    unified-api-contracts/unified_api_contracts/internal/modes.py,
  ]
---

# E2E wiring — built vs REACHABLE

> **Operator framing 2026-08-15**: _"we need to have everything wired e2e so investigate and complete with docs that we
> can continue to dispatch — we should now have a round up of all the things we need to complete documented."_

**The recurring defect class this documents.** Across three sessions the same shape keeps appearing: something real is
built, tested and complete, and **nothing on a production path can reach it**. It survives every review that asks "does
this work?" because the honest answer is yes — the question that fails is "does anything call it?".

Instances found so far, all independently verified:

| Thing                                           | Built?                 | Reachable?                                                                                                                                                     |
| ----------------------------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GenericTokenBalanceAdapter`                    | yes, +tests            | **was no** — nothing imported it (FIXED, see below)                                                                                                            |
| 24 plan-hygiene tests                           | yes                    | **was no** — directory absent from `PYTEST_UNIT_DIR` (FIXED)                                                                                                   |
| `EnhancedAlphaComparator`                       | yes                    | **no** — no production caller                                                                                                                                  |
| Marinade / Kamino connectors                    | yes, real RPC          | **no** — no production caller (still true 2026-08-15)                                                                                                          |
| Jupiter connector                               | yes, real RPC          | **fixed 2026-08-15** — `DeFiAdapter`, conditional on a Solana secret (`execution-service@37bfaeed0b`)                                                          |
| `V2InstructionRouter`                           | yes, all 14 actions    | **DELETED 2026-08-15** as confirmed dead code (`execution-service@37bfaeed0b`)                                                                                 |
| `DefiAdapter`                                   | yes                    | **fixed 2026-08-15** — wired to real Uniswap/Lido/Jupiter alongside AAVE (`execution-service@37bfaeed0b`); see the re-derived table below for what this covers |
| `RecursiveLoopOrchestrator`'s AAVE/Uniswap path | yes, real (2026-08-15) | **no** — its one production construction site (`api/app.py:321`) doesn't pass the connectors (found 2026-08-15, this session)                                  |
| `QuoteMaintainer`/`DeltaProxyRepricer` wiring   | yes                    | **no** — zero production callers (found 2026-08-15, this session)                                                                                              |

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

## FINDING 2 (P0) — RESOLVED 2026-08-15, `execution-service@37bfaeed0b`

> **⚠️ SUPERSEDED.** The paragraph below described the state as of this doc's creation (`_build_defi_adapter`
> constructing only `AAVEConnector`). A concurrent same-day session (this exact multi-agent checkout — two other live
> sessions were active in this slot while this table was re-derived) shipped `execution-service@37bfaeed0b`, which
> rewired `_build_defi_adapter` to construct real `UniswapConnector`/`LidoConnector`/`JupiterConnector` (Jupiter
> conditional on a Solana wallet secret) and deleted `V2InstructionRouter` outright as confirmed dead code. Full detail
> in
> [the venue-coverage issue's P0 dispatcher-wiring todo](/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md).
> This finding is kept, struck through in spirit, as the "before" half of the record.

`cli/handlers/live_execution_handler.py:495` constructs exactly one connector: `AAVEConnector(is_live=True)`.
`DefiAdapter` — which holds Uniswap / AAVE / Lido / Jupiter — has **zero construction sites outside tests**.

So the execute-side tier table in
[the venue-coverage issue](/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md) is
measuring the wrong property. It scored connectors on whether their write path is real. **A connector with a real write
path and no caller executes nothing.** That table needs re-deriving on reachability, and any client-facing number
derived from it is currently unsupported. **Re-derived below, § "Re-derived reachability table (2026-08-15, session
5)".**

## FINDING 3 — the read side IS genuinely closed (contrast case)

Recorded because it is the one place the chain is complete, and it shows what "done" looks like here:

- `unified-api-contracts@53a5adc7` + `@bed96aa0` — LST token address SSOT, 6 reachable cited addresses.
- `strategy-service@5b2a50ed` — factory routes LST venues from that SSOT; **8 DeFi venues readable, up from 3**.
- Reachability proven by a routing test that resolves through `get_position_adapter()`, the resolver every caller uses —
  not by asserting the adapter class exists.
- Registry-driven, so adding an address makes a venue readable with **no code change** — the read side cannot silently
  fall behind the execute side again.

## Re-derived reachability table (2026-08-15, session 5)

Method: [§ "How to verify a reachability claim"](#how-to-verify-a-reachability-claim-method-so-this-is-repeatable)
below. Production entry points found by `rg 'FastAPI\(|APIRouter\(|def main\('` (excluding tests):
`execution_service/api/app.py` (FastAPI app — `/manual`, `/preview`, evidence, health, + an `@app.on_event("startup")`
wiring block) and `execution_service/cli/main.py`'s `_SERVICE_HANDLERS` dispatch
(`python -m execution_service --operation live_execution --mode live` → `LiveExecutionModeHandler` →
`LiveExecutionHandler`). For each of the 41 files in `defi_execution/protocols/` (not 38 — the count grew this session:
`jito.py` and `pacifica.py` are net-new), 9 are infra/ABC/helper modules with no independent connector to score (`base`,
`solana_base`, `solana_lst_devnet`, `uniswap_encoding`, `aave_live`, `uniswap_live`, `_evm_generic`,
`_hyperliquid_schemas`, `_hyperliquid_signing`) — that leaves **32 connector modules**.

Write-path-real is `supports_live = True` on the class (the fail-closed guard from `execution-service@9946ba5a3` — a
connector cannot construct with `is_live=True` unless it declares this, so the flag is load-bearing, not decorative) or,
for the Solana tree (`BaseSolanaConnector` has no such guard), a read of the write method itself. Reachable is a
non-test, non-`protocols/`, non-`__init__`-re-export instantiation site that a production entry point above actually
reaches.

| Module            | Write path real?                                                                                              | Reachable from production?                                                                                                                      | Covered? |
| ----------------- | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `aave`            | yes (`supports_live=True`)                                                                                    | **yes** — `DeFiAdapter` via CLI `live_execution` entry (LEND/BORROW) + `api/app.py:303` (read-only fetch)                                       | ✅       |
| `uniswap`         | yes (`supports_live=True`)                                                                                    | **yes** — `DeFiAdapter` via CLI `live_execution` entry (SWAP)                                                                                   | ✅       |
| `lido`            | yes (`supports_live=True`)                                                                                    | **yes** — `DeFiAdapter` via CLI `live_execution` entry (STAKE) + `api/app.py:304` (read-only fetch)                                             | ✅       |
| `jupiter`         | yes (`supports_live=True`)                                                                                    | **conditional** — `DeFiAdapter`, only when `solana_wallet_secret` resolves; degrades to `None` (honest NOT-WIRED) otherwise                     | ✅*      |
| `hyperliquid`     | yes (`supports_live=True`)                                                                                    | **yes** — `hyperliquid_wiring.py` → `api/app.py` `@app.on_event("startup")` → perp-hedge rebalance/topup                                        | ✅       |
| `bybit`           | yes (live via CCXT, no `supports_live` flag — not a `BaseConnector`)                                          | **yes** — `bybit_wiring.py` → `api/app.py` startup → perp-hedge rebalance/topup                                                                 | ✅       |
| `aster`           | yes (`supports_live=True`)                                                                                    | no — zero non-test construction sites found                                                                                                     | ❌       |
| `beefy`           | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `bridge` (Socket) | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `cctp`            | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `convex`          | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `eigenlayer`      | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `etherfi`         | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `idle`            | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `kamino`          | yes (+ new `borrow`/`repay` via Kamino's real Transactions API, `execution-service@37bfaeed0b`)               | no — `RecursiveLoopOrchestrator` (the driver the recursive-carry archetype docs name) does not call Kamino; only Aave+Uniswap are wired into it | ❌       |
| `karak`           | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `kelpdao`         | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `marinade`        | yes (real `send_transaction`)                                                                                 | no                                                                                                                                              | ❌       |
| `morpho`          | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `orca`            | yes (real `send_transaction`)                                                                                 | no                                                                                                                                              | ❌       |
| `pendle`          | yes (`supports_live=True`, config-gated)                                                                      | no                                                                                                                                              | ❌       |
| `puffer`          | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `raydium`         | yes (real `send_transaction`)                                                                                 | no                                                                                                                                              | ❌       |
| `renzo`           | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `rocket_pool`     | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `symbiotic`       | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `weth`            | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `yearn`           | yes (`supports_live=True`)                                                                                    | no                                                                                                                                              | ❌       |
| `jito` (jitoSOL)  | reads real; **writes stay simulation-only** (`supports_live=False`, documented SDK blocker)                   | n/a — fails on write-real regardless; zero callers anyway                                                                                       | ❌       |
| `jito_restaking`  | reads real; writes simulation-only (`supports_live=False`, same SDK blocker)                                  | n/a                                                                                                                                             | ❌       |
| `solblaze`        | reads real; writes simulation-only (`supports_live=False`, same SDK blocker)                                  | n/a                                                                                                                                             | ❌       |
| `pacifica`        | signing scaffolded but `supports_live=False` (pending an operator-provided wallet key, per its own docstring) | n/a                                                                                                                                             | ❌       |

**Stated count: 6 of 32 connector modules (19%) are genuinely reachable-and-live today** — `aave`, `uniswap`, `lido`,
`jupiter` (conditional on a secret), `hyperliquid`, `bybit`. This is a module count, not a capability count (per this
doc's own method rule 4) — `aave`/`uniswap`/`lido` are reachable for SWAP/LEND/BORROW/STAKE only via `DeFiAdapter`'s CLI
entry point; `hyperliquid`/`bybit` are reachable only for perp-hedge rebalance/margin-topup, a narrower purpose. The
other 22 write-real connectors and the 4 simulation-by-design ones are unchanged by this session's dispatcher-wiring fix
(`execution-service@37bfaeed0b`) — that fix widened `DeFiAdapter`'s reach from 1 to 4 connectors, not to all 32.

**Residual finding — `RecursiveLoopOrchestrator`'s real AAVE/Uniswap execution path is still unreachable from its own
production construction site.** `execution-service@37bfaeed0b` (this session, landed by a concurrent session in this
same checkout) made `_execute_open_iter`/`_execute_close_iter` call real
`AAVEConnector.supply()`/`.borrow()`/`.repay()`/ `.withdraw()` + `UniswapConnector.swap_exact_input()` instead of
returning dead-code placeholders — genuine progress. But `RecursiveLoopOrchestrator`'s **one** production construction
site, `api/app.py:321` (inside the perp-hedge startup wiring), passes only
`hyperliquid_connector`/`bybit_connector`/`bridge_deposit`/`bybit_deposit` — **not**
`aave_connector`/`uniswap_connector`. So the orchestrator instance actually running in production still executes its
recursive supply→borrow→swap loop in simulated mode (`self._aave is None` → the `0xSIM_OPEN_...` branch), despite the
real branch now existing and being unit-tested. This is the exact defect class this doc documents, one layer deeper than
where the P0 todo looked. **Not fixed here** — the module's own docstring (`family2_position_registry.py:1-30`) records
a 2026-08-09 operator ruling (BLK-7f4d33db, option C) that Family-2 recursive-carry positions are opened by
strategy-service's `CarryRecursiveStakedEngine`, not this orchestrator directly, so wiring `aave_connector`/
`uniswap_connector` into the `api/app.py:321` perp-hedge-lifecycle construction site may not even be the architecturally
right place — that needs a design call, not a credential-wiring patch, and this doc is not the place to make it
unilaterally on a live-capital path. Tracked as a new todo below.

**Adjacent finding — a fresh instance of the same defect class, self-discovered.**
`execution_service/engine/quote_maintenance.py`'s `QuoteMaintainer`/`DeltaProxyRepricer` wiring is real and correctly
connects `DeltaProxyRepricer` to a venue-submission protocol — and has **zero production callers**
(`register_quote_instruction`/`QuoteMaintainer(` have no non-test references anywhere in the repo). Its own docstring
claimed `QuoteHandler.handle()` calls it — false, since `QuoteHandler` was deleted in the same
`execution-service@37bfaeed0b` that deleted `V2InstructionRouter` (they lived in the same now-deleted `v2/handlers.py`)
— a doc that misled this session, fixed in the same turn: the docstring now states plainly that this module has zero
production callers, per the "state explicitly not-yet-wired" instruction this doc's own Task 2 applies to
`V2InstructionRouter`/`DefiAdapter`. No further fix attempted — building the missing QUOTE-instruction receipt path is a
new scope, not a wiring bug in what already exists.

## Todos

- **[OPERATOR] P0. CANCELLED — SUPERSEDED 2026-08-22 (D76 ruling: close the ruling — the close-all contract question
      is formally closed; migrate-onto-`/manual/instruction` was already decided § "CLOSE-ALL RULING (operator,
      2026-08-15)" and the implementation already shipped, `strategy-service@701dce1850` +
      `execution-service@3800849e87`).**
- [x] [AGENT] P0. ✅ **Implement whichever side the ruling picks, and add the missing HTTP-level test** —
      `strategy-service@701dce1850` (close_all request-shape mapping onto `POST /manual/instruction`) +
      `execution-service@3800849e87` (the HTTP-level contract test, FastAPI `TestClient` against the real router,
      including a regression guard that `GET`/`POST /api/orders` still 404s — the exact seam whose absence let this
      survive). The defect survived because nothing exercised strategy→execution over the wire; this test is worth
      more than the fix.
- [x] [AGENT] P0. ✅ **Re-derived the execute-side tier table on CALLER-GRAPH reachability** — see § "Re-derived
      reachability table (2026-08-15, session 5)" above. **6 of 32 connector modules (19%) are genuinely
      reachable-and-live**; the prior "~16 genuinely live" figure measured write-path-realness only. Client artifacts
      citing the old figure need correcting — flagged as the disclosure-artifact todo below.
- [x] [AGENT] P0. ✅ **Decided what `V2InstructionRouter` and `DefiAdapter` are for** — `execution-service@37bfaeed0b`
      (landed 2026-08-15 by a concurrent session in this checkout while this todo was being worked).
      `V2InstructionRouter` **deleted** as confirmed dead code (`v2/router.py` + `v2/handlers.py` + their test file
      removed outright — every one of its 14 action handlers was a stateless note-attacher that never called a
      connector, and the real ATOMIC path already runs through `atomic_instruction_router.py`, never through this
      router). `DefiAdapter` **wired**: `_build_defi_adapter` now constructs real `UniswapConnector`/
      `LidoConnector`/`JupiterConnector` (Jupiter conditional on a Solana secret) alongside the pre-existing
      `AAVEConnector`, reachable via the CLI `live_execution` entry point — see the reachability table above for what
      this does and does not cover. **A new, adjacent uncalled-component finding surfaced while verifying this**:
      `RecursiveLoopOrchestrator`'s real AAVE/Uniswap path and `QuoteMaintainer` — see the two "finding" paragraphs
      above and the new todo directly below.
- [ ] [AGENT] P1. **`RecursiveLoopOrchestrator`'s production construction site (`api/app.py:321`) does not pass
      `aave_connector`/`uniswap_connector`**, so its real recursive-carry execution path (shipped
      `execution-service@37bfaeed0b`) stays simulated in the one place it actually runs. Needs a design call first — per
      `family2_position_registry.py`'s documented 2026-08-09 operator ruling (BLK-7f4d33db, option C), Family-2
      position-opening belongs to strategy-service's `CarryRecursiveStakedEngine`, so the right fix may be wiring
      `recursive_loop_runner.py`'s bridge onto that event flow rather than hand-passing credentials at `api/app.py:321`.
      Resolve as a LOCAL/operator-scoped design todo before dispatching an AO fix.
- [x] [AGENT] P1. ✅ **Add a reachability gate.** — `unified-trading-pm@0428f5ee1f` (new
      `scripts/quality_gates/check_reachability_gate.py`, wired into `quality-gates.sh`'s post-gates sweep). Census
      mode (a directory of classes subclassing a common base — measured 26/33 execution-service DeFi protocol
      connectors unreachable) and registry mode (an explicit `dict[key, type]` registry — `strategy-service`'s
      `STRATEGY_CLOSE_ALL_REGISTRY`, 2/2 unreachable, matches FINDING 1's close-all gap). Registry-mode targets that
      turn out to be dynamic-dispatch (`market-tick-data-service`'s `VENUE_REGISTRY`, `strategy-service`'s
      `ARCHETYPE_ENGINE_REGISTRY`) are detected and reported informationally rather than falsely per-entry-baselined —
      a naive "is `ClassName(...)` ever called by literal name" check scores ~100% false-unreachable for a
      correctly-used dynamic registry, since the whole point of a registry is to avoid one named call site per entry.
      Shrinking-ratchet baseline is a NAME SET, not a count (unlike `check_pytest_unit_dir_coverage.py`'s), so
      swapping one gap for a different one still fails. `features-service`'s per-domain `*_REGISTRY` family is the
      natural next batch of registry-mode targets — noted in-code, not added speculatively (unmeasured).
- [x] ✅ [SCRIPT] P1. **`SymbioticConnector` is now wired but still baselined as unreachable — remove it from
      `reachability_gate_baseline.json`.** `execution-service@85c8310b` ("feat: wire Symbiotic into DeFiAdapter's real
      dispatch (STAKE handler)", 2026-08-16 16:46 UTC) landed the wiring — exactly the intent this gate exists to
      enforce (§ "Add a reachability gate" above) — but nobody has yet re-run
      `check_reachability_gate.py --update-baseline` (or hand-edited the JSON) to drop `SymbioticConnector` from the
      still-expected-unreachable list, so the ratchet ("only shrinks") now fails: `[FAIL] execution-service:
      defi_protocols: 1 baselined class(es) are now reachable and must be removed from the baseline: SymbioticConnector`.
      **This is currently blocking quickmerge tree-wide for every agent on unified-trading-pm** (discovered 2026-08-16
      by plan_reconciler while diagnosing an unrelated docs-only quickmerge failure — confirmed via 2 identical
      consecutive quickmerge failures citing this exact class). Out of plan_reconciler's HARD LIMIT scope
      (`scripts/quality_gates/reachability_gate_baseline.json` is not under `plans/**`) to fix directly. Done when: the
      baseline file drops `SymbioticConnector` (or the wiring is reverted, whichever is correct) and a fresh
      `quality-gates.sh` run on unified-trading-pm no longer fails `reachability-gate` for this class. Repo:
      unified-trading-pm. **Caveat (verified 2026-08-16, plan_reconciler)**: a same-day peer commit (`effde0f7d5`)
      claimed "fix(qg): drop now-reachable SymbioticConnector from reachability baseline" in its message, but
      `git show effde0f7d5 -- scripts/quality_gates/reachability_gate_baseline.json` produces an EMPTY diff — the file
      was not actually touched (its last real touch remains `unified-trading-pm@0428f5ee1f`, the gate's original
      creation commit). Don't trust that commit message as evidence this is done; verify the JSON directly before
      closing this todo. **RESOLVED 2026-08-16 (plan_reconciler)** — `unified-trading-pm@bb6faddb` ("fix(qg): regenerate
      adapter-contract baseline + drop now-reachable SymbioticConnector + tardis options_chain credential unblock
      docs") landed a real 1-line deletion (`git log --stat` confirms `1 file changed, 1 deletion(-)`, unlike
      `effde0f7d5`'s hollow claim above). Independently re-verified by direct measurement, not by trusting the message:
      `git show origin/live-defi-rollout:scripts/quality_gates/reachability_gate_baseline.json | grep -c
      SymbioticConnector` → `0`. The second "Done when" condition (a fresh `quality-gates.sh` run no longer failing
      `reachability-gate` for this class) is being confirmed by the quickmerge attempt shipping this very doc.
- [x] ✅ [AGENT] P1. **SIT invariant 2 — the mode-axis PREREQUISITE now exists, wiring the invariant itself is still
      open.** Operator ruling 2026-08-15 (full ruling text: /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md §
      DESIGN PASS below): build the axis, do not weaken the invariant. **Done**: `BasePositionAdapter`
      now carries an explicit `mode: TradingMode` (+ `testnet` as the PAPER sub-mode selector), resolved per
      adapter-construction rather than a service-global, and `reconciliation_engine.py` gained a `leg:
      ReconVerdictType` guard so a paper-vs-batch (determinism) failure and a paper-vs-live (execution) failure alert
      differently (`strategy-service@701dce1850`). Invariants 1+3 already landed
      (`system-integration-tests@da65ae1`); invariant 3 was itself found deficient on review 2026-08-15 (compared
      venue names not instruction actions, never checked `supports_live`) and rewritten
      (`unified-api-contracts@e9201d80`). Invariant 4 (UAC↔execution LST address drift) is also landed
      (`unified-api-contracts@e9201d80`, `system-integration-tests@c30e412851`) — narrowed mid-session to just
      `mSOL`/SOLANA after Chunk A's address migration landed concurrently for all 6 ETHEREUM addresses
      (`execution-service@d981725c2`). **The invariant itself, "assert a reader exists for each mode a slot actually
      runs in", is now also wired — reconciled 2026-08-17 (slot 15, review), shipped via
      `venue_readiness_ao_dispatch_batch1_2026_08_16`, not by this doc's own dispatch.** `unified-api-contracts@86d5f5af46`
      + `system-integration-tests@cce1adebc6` wired it as invariant #26 in `run_cross_repo_invariants.sh` (both SHAs
      independently re-verified this session as live ancestors of `origin/live-defi-rollout`, content spot-checked
      against the actual `run_cross_repo_invariants.sh` entry). All four SIT invariants from this doc + the venue-coverage
      issue are now shipped.
- [x] [AGENT] P1. ✅ **Build the 4 bespoke position readers** — `strategy-service@701dce1850`. Morpho: real health
      factor via `position()`/`market()`/oracle `price()` on-chain reads (function selectors verified via
      `eth_utils.keccak`, not guessed). Pendle: PT-token balance + maturity, `position_type` liquid/locked by maturity
      vs now. Symbiotic + Karak: vault-share balance + withdrawal-delay metadata, honest-scope (no in-progress
      withdrawal-request tracking claimed). All 4 return `DeFiLendingPosition`/`DeFiStakingPosition` via
      `get_normalized_positions()`, not a bare `CanonicalBalance` — a raw token balance MISREPRESENTS a leveraged
      health-factor position or a maturity-bearing PT token, which is exactly why this todo existed.
- [x] [AGENT] P1. ✅ **Migrate execution-service protocol modules onto the UAC LST address SSOT** —
      `execution-service@d981725c2` (landed by a concurrent session in this checkout while this exact migration was
      independently being written here too; reconciled via rebase — their version is strictly the more complete one
      (adds a shared fail-loud `required_lst_address()` helper in `_evm_generic.py` and also covers `symbiotic.py`,
      neither of which this session's draft had), so it was taken as-is rather than merged piecemeal; this session's
      distinct, non-overlapping contribution — the `quote_maintenance.py` docstring correction and the close-all HTTP
      contract test above — carried through the reconciliation onto `execution-service@3800849e87`). The 6 addresses
      that existed in both places
      (`unified_api_contracts.registry.lst_token_addresses.LST_TOKEN_ADDRESS_BY_CHAIN["ETHEREUM"]`: `stETH`, `wstETH`,
      `rETH`, `weETH`, `ezETH`, `pufETH`) are now sourced by direct dict lookup from that SSOT in `lido.py`,
      `rocket_pool.py`, `etherfi.py`, `renzo.py`, `puffer.py` — the class attribute names (`STETH_ADDRESS`, etc.) are
      unchanged so no consumer/test needed updating, only the literal's source of truth. `EETH_ADDRESS` (etherfi.py)
      stays a local literal, correctly — the UAC SSOT deliberately excludes it (no venue declaration resolves it yet,
      per that module's own docstring). Dict indexing (not the `Optional`-returning `lst_token_address()` helper) so a
      missing key fails loudly at import time rather than silently typing as `str | None`.
      — **Addendum 2026-08-17 (slot 15, review): the 3 addresses this Chunk A migration left pending
      (`marinade.py::MSOL_MINT`, `jito_restaking.py::JITOVSOL_MINT`, `symbiotic.py::DEFAULT_COLLATERAL_WSTETH`) are
      now also migrated — Chunk B, shipped via `venue_readiness_ao_dispatch_batch1_2026_08_16`, not by this doc's own
      dispatch.** `execution-service@529af8d22c` + `unified-api-contracts@6151de2a2a` (updated
      `MIGRATED_TO_UAC_LOOKUP`/`LST_ADDRESS_SOURCE` for the 3 newly migrated entries; `LST_ADDRESS_SOURCE` is now
      empty). Both SHAs independently re-verified this session as live ancestors of `origin/live-defi-rollout`; content
      spot-checked (`execution-service@529af8d22c`'s commit message confirms Marinade/Jito-Restaking/Symbiotic as the
      exact 3 modules, explicitly citing Chunk A's `execution-service@d981725c2` as the prior 6-address migration this
      completes). The LST address SSOT migration for execution-service is now complete for every venue not
      deliberately excluded (eETH/rsETH/bSOL, per the 2026-08-16 operator ruling recorded in
      /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md).
- [x] [AGENT] P2. ✅ **Fix `check_pytest_unit_dir_coverage.py`** — `unified-trading-pm@0428f5ee1f`. Root cause: v1
      only scanned `tests/<family>/unit/` shapes (the MTDS bug shape) and structurally could not see PM's own
      `scripts/plan-hygiene/` co-located `test_*.py` files — a different shape entirely, never in scope. v2 scans for
      any dir holding a `test_*.py` file, with an exclusion list for genuinely-separate test tiers
      (integration/e2e/smoke/etc. — measured: an unscoped scan flagged ~60 false positives across the fleet before
      that exclusion) and PM's `codex/` template dir (`test-templates/test_event_logging.py` is copy-paste boilerplate,
      never collected in place). Baseline recalibrated against the real fleet (6 repos have confirmed genuine
      pre-existing gaps) via a hand-edit of the baseline (not `--update-baseline`, which clamps DOWN-only by design —
      this was a deliberate, reviewed re-measurement after the detection-logic change, not a silent widening).
- [x] ✅ [OPERATOR] P2. **`LST_TOKEN_GENESIS` for Kelp/rsETH and ether.fi/eETH — RULED 2026-08-16: leave DELIBERATELY
      ABSENT until a venue actually needs them.** Not a deferral — the current state is correct by construction, and
      `registry/lst_token_addresses.py` already says so at the point of absence: UAC declares `ETHERFI` as
      `("weETH",)` only and has **no KELPDAO venue at all**, so an entry for eETH or rsETH would be unreachable —
      recreating exactly the orphan class the reachability gate exists to catch. Adding an address to satisfy a
      completeness instinct would trade a known gap for a silent one. **Revisit trigger**: the first strategy that
      genuinely needs rsETH or eETH — at which point the venue declaration and the cited genesis land together in one
      change, so the map never carries an entry no venue declares. The "invented date corrupts denominators" hazard
      is thereby avoided by not creating the row, rather than by sourcing a date for a row nothing reads.
- [ ] [AGENT] P2. **Correct client-facing disclosure artifacts still citing the pre-reachability "~16 genuinely live"
      DeFi execute figure** (e.g. the Elysium disclosure plan) to the reachability-derived **6 of 32 (19%)** — the "16"
      figure measures write-path capability, not what a production process can actually invoke, per this doc's own
      method.

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

> **⚠️ CORRECTED by operator ruling 2026-08-15.** My first pass framed reconciliation as ONE comparison (internal book
> vs venue truth) and asked "does each mode have venue truth?" — concluding `BACKTEST` was degenerate. That framing was
> wrong, and the corrected model is below. The original is preserved as a lesson: the mistake was inventing a model
> instead of reading `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`, which already specifies the
> real one.

### The reconciliation lattice (existing, and it already says this)

Reconciliation is not one comparison — it is a decomposition into two ORTHOGONAL legs that stack:

```
live − batch  =  (paper − batch)  +  (live − paper)
```

- **`paper − batch` (the determinism leg)** — proves the system does in a LIVE LOOP what it does in a BATCH LOOP. Same
  matching assumptions on both sides, so any difference is a loop-mechanics bug. This is the ε=0 spine.
- **`live − paper` (the execution leg)** — with the loop proven identical, the remaining delta IS execution alpha:
  purely a test of the execution/fill assumptions.

**Batch is therefore not reconciled against a venue at all — it is the REFERENCE that paper is proven against.** My
"tautological" objection only applies to reconciling batch against ITSELF, which nothing proposes.

Both legs are already implemented and REACHABLE: `batch-live-reconciliation-service` `engine/orchestrator.py:175` calls
`run_stage3b` (paper-vs-live) and `:196` calls `run_stage3c` (batch-vs-paper), as a T+1 pipeline. A rare positive
contrast case in this doc.

### The corrected mode model (operator, 2026-08-15)

**Modes are `batch` | `paper` | `live`.** Standardise the wording on **batch** (not `BACKTEST`).

**`paper` has a TESTNET SUB-MODE — testnet is a mode WITHIN paper, not a peer of it:**

| paper sub-mode | What the venue side is                                                                            | Independent truth? |
| -------------- | ------------------------------------------------------------------------------------------------- | ------------------ |
| testnet ON     | a real venue-side account (Binance testnet, IBKR paper TWS 7497/4002) reachable by real API calls | **Yes**            |
| testnet OFF    | simulated matching — and it is **the same matching batch uses**                                   | **No**             |

Testnet-off is the common case, because not every venue offers a testnet to send API calls against, and even where one
exists it often cannot hold the balances we would really have had. So paper degrades to matching — which is correct and
by design, since paper and batch are REQUIRED to match trade-for-trade.

**`MANUAL` is NOT a reader mode — it is a deployment topology.** Its purpose is a SECOND execution instance on the same
deployment trust, so that if the automated execution-service is down or restarting, operator-driven open/close
instructions still have a path. It is redundancy, not a mode of reading positions, and it should be removed from any
mode axis. (`ManualExecutionMode` is a real UAC type consumed by `manual_instruction_api`.)

**All three run SIMULTANEOUSLY** — T+1 backfills and replays for batch, alongside inline live and paper feeding each
other. So mode CANNOT be a service-level config: one deployment carries all three concurrently, and mode must be
resolved **per strategy-instance / slot**.

### Corrected proposed shape

1. Mode is a per-instance/slot property, never a service-global. `BasePositionAdapter` gains it explicitly; it is
   resolved per adapter construction, not read from process config.
2. `live` → mainnet endpoints. `paper` → testnet endpoints when the venue HAS a testnet and it is enabled, else the
   shared simulated matcher. `batch` → the batch ledger, which is the reference leg (a legitimate read, not a
   tautology).
3. The existing per-family `testnet: bool` / `fork_mode` flags become the paper sub-mode selector rather than a parallel
   axis.
4. `reconciliation_engine.py` has **no mode guard today** — it publishes `RISK_ALERTS` regardless. It must know WHICH
   LEG it is evaluating, because a paper-testnet-off comparison against batch is a determinism check, while a
   paper-testnet-on comparison against live is an execution check, and they have different meanings on failure.
5. SIT invariant 2 becomes expressible once mode is per-instance: assert a reader exists for each mode a slot actually
   runs in.

### CLOSE-ALL RULING (operator, 2026-08-15) — migrate onto `/manual/instruction`

Not a new `/api/orders`. Verified: `/manual/instruction` is the DIRECT submission path (`submit_manual_instruction`),
while `/manual/pending` is the separate approval-gated one ("require explicit operator approval before execution", 202).
So routing close-all through `/manual/instruction` does NOT put a human in the loop on an emergency flatten — consistent
with the kill-switch rule that protective arming is always autonomous.

The stronger argument: **one path means the emergency flatten is the same code humans exercise routinely**, so it is
continuously proven. An endpoint used only in a crisis is one that is never tested — exactly why this 404 sat latent. It
also composes with `MANUAL` being a redundant deployment: the flatten path is then the one designed to survive the
automated execution-service being unavailable.

The real work is **request-shape mapping** (close-all sends `{venue, instrument_id, side, …}`; the manual API takes its
own model) plus an HTTP-level contract test — the thing whose absence let this survive.

## MANUAL / DISASTER-RECOVERY DESIGN (operator ruling 2026-08-15)

`MANUAL` is **not a reader mode and not a strategy mode** — it is a redundant execution DEPLOYMENT. This section is the
SSOT for what it is for, because it is the easiest of these rulings to re-litigate.

### What redundancy actually buys, by failure mode

The design pressure falls out of this table, not from a coverage wish-list:

| What is down                                                                | Does a second execution deployment help?                                                 |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| strategy-service                                                            | You need an instruction SOURCE, not a redundant executor — the primary executor is fine. |
| execution-service: bad deploy / crash / config / OOM                        | **Yes** — a second instance pinned to different code+config survives.                    |
| execution-service: SHARED dependency (venue creds, GSM, network, venue API) | **No** — the redundant instance shares the failure.                                      |
| venue connectivity itself                                                   | **No.** You log into the exchange UI and trade by hand.                                  |

**Redundancy only buys protection against failures the second instance does NOT share.** So the correct design pressure
is _minimal and independent_, never _exhaustive_. Every dependency the manual deployment shares with the primary is a
failure mode it cannot survive; every strategy feature added to it is surface that can be down when needed. This
resolves the "not exhaustive enough to handle all the strategies" tension — see scoping below.

### RECORD_ONLY is the answer to the venue-connectivity case

`ManualExecutionMode` (UAC `internal/execution.py:47`) already has exactly two values:

- `EXECUTE` — route to venue via orchestrator, the same path automated strategies use.
- **`RECORD_ONLY`** — skip venue execution, record the fill directly (OTC, missed trades).

When venue connectivity is gone you cannot send an order at all — you log in and trade manually. **Your book is then
wrong**, because the system does not know what you did. `RECORD_ONLY` is how you tell it. So in the worst failure the
manual deployment's job is not executing, it is **keeping the book true when execution happened outside the system**.
Wired at `manual_instruction_api.py:242,381` + `manual_instruction_helpers.py:314-319`.

### Reconciliation after a RECORD_ONLY episode — the real hazard

Reconciliation compares POSITION QUANTITIES (internal vs exchange), not fills, so a correctly-entered `RECORD_ONLY`
converges cleanly: the venue has the hand-trade, the book now has it too, they agree. **Double-counting is not the
risk.**

The risk is a hand-entered quantity being WRONG. Reconciliation will correctly detect the discrepancy — and if
`auto_correct_enabled=True`, `CorrectionDispatcher` dispatches a correction ORDER on the strength of a number a human
typed during an incident. That compounds a typo into a real trade.

> **⚠️ The framing above is SUPERSEDED (operator, 2026-08-15).** I proposed disabling auto-correct AFTER a `RECORD_ONLY`
> entry. That is the wrong mechanism and too late. Correct model below.

**The instant-undo problem.** Partial outages are the common case — orders down, position feed fine. Book a manual trade
while reconciliation is armed and reconciliation sees internal ≠ exchange and **corrects it away within seconds**. The
entry is undone by the system almost as soon as it is made. So reconciliation must be **PAUSED BEFORE the entry is
accepted, not disabled after it**, and attempting a manual booking while reconciliation is armed must raise an ALERT
rather than silently proceed.

**Two DISTINCT classes of manual entry** — conflating them is what makes this confusing:

| Class                                | Will the venue ever show it?                      | What reconciliation must do                                                             |
| ------------------------------------ | ------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Reconcilable entry**               | Yes — a real trade the feed reports once restored | Converge normally. Pause during entry so it is not undone before the feed catches up.   |
| **Persistent delta (virtual entry)** | **No — never.** A deliberate permanent offset     | **EXCLUDE it from the comparison**, and keep reconciling everything else, indefinitely. |

The second class has no current answer. It is not a "fake trade" — it is a **consistent delta offset** the system must
treat as real while knowing the exchange will never confirm it. Without exclusion, reconciliation spends the rest of
time trying to unbook it.

**Requirements for a virtual entry** (none of this exists today):

1. A mandatory human-written REASON — an emergency protocol, not a routine booking.
2. A warning at entry, and an alert if attempted while reconciliation is armed.
3. **Excluded from the reconciliation delta** so it is never auto-unbooked, while the rest of the position keeps
   reconciling normally.
4. Persists until a human removes it.

**MiFID: removal is a STATUS CHANGE, never a deletion.** The row is never removed from storage. A deleted entry is
excluded from system behaviour, but the record — and the delete ACTION itself, with actor and reason — stays auditable.

**What exists today (checked 2026-08-15):** `auto_correct_enabled` plus three guards (flag,
`auto_correct_threshold_pct`, `auto_correct_max_qty`) at `correction_dispatcher.py:37-40`. That is a STATIC config flag.
There is **no pause concept, no per-episode suppression, no virtual-entry exclusion, and no soft-delete for trades** —
the `DELETED` statuses in UAC are for VMs and client-reporting, not fills. Zero hits for OTC diff-booking in
`strategy_service/position/`.

- [ ] [AGENT] P0. **Reconciliation PAUSE as a PRECONDITION of manual entry** — armed-state check before the booking is
      accepted, alert if armed, explicit resume. Not a post-hoc disable.
- [ ] [AGENT] P0. **Virtual / persistent-delta entry**: mandatory reason, excluded from the reconciliation delta so it
      is never auto-unbooked, while everything else keeps reconciling; warning at entry.
- [ ] [AGENT] P0. **Soft-delete with audit (MiFID)** — status change only, never row removal; record actor + reason;
      deleted entries excluded from behaviour but retained and auditable.
- [ ] [AGENT] P1. Build OTC reconciliation as a MANUAL REVIEW step, not auto-booking, between internal and exchange
      position (currently unbuilt — zero OTC hits in `position/`). Per D76 ruling (2026-08-22): require manual OTC
      review — auto-booking a hand-entered quantity risks compounding a typo into a real trade. Repo: strategy-service.

## AUDIT / IMMUTABILITY OF THE PRIVATE RECORD (operator ruling 2026-08-15)

**Scope**: positions, trades, fills, orders — **and strategy instructions**, which the operator explicitly pulled into
the same class. Instructions already encode what the system DECIDED (ML, market feed, everything upstream), so auditing
them captures intent as well as outcome. Data-pipeline artefacts are explicitly NOT in this class.

**Property wanted**: the RECORD is immutable and the ACTIONS on it are audited — **including attempts that did not
succeed.** The operator's worked example: an order manager or a regulator must be able to see whether a cancel was
attempted **while the order was in flight** versus **after the fill was confirmed**. Different facts, different
liability.

### What EXISTS (checked 2026-08-15 — do not rebuild)

- `execution_service/utils/audit_log.py::persist_audit_log()` — persists to GCS as an **immutable JSONL blob** and
  validates `EXECUTION_AUDIT` schema fields. The immutability primitive is real.
- `ManualInstructionAuditLog` (`api/manual_schemas.py`) — a typed audit record.
- Genuinely WIRED, not merely present: `api/manual_instruction_helpers.py:131` calls it.
- `orders/oms.py` is the order-management surface; `api/evidence_router.py` exposes evidence; `instruction_lifecycle` is
  a registered service contract (`registry/service_contract_map.py:98`).

### GAP 1 — audit coverage is MANUAL-ONLY

The only caller of `persist_audit_log` is the manual-instruction path. **Automated orders, fills, positions and strategy
instructions do not route through it.** The immutable trail covers the rarest flow and not the routine one — the inverse
of what the ruling wants.

### GAP 2 — the canonical vocabulary cannot express an in-flight cancel

Canonical `OrderStatus` (UAC `canonical/domain/execution/base.py:47`) is exactly:
`PENDING · OPEN · PARTIALLY_FILLED · FILLED · CANCELLED · REJECTED · EXPIRED`.

**There is no `PENDING_CANCEL`.** It exists only in EXTERNAL venue schemas (`external/fix/schemas.py:94,112`,
`external/mexc`) — so we can PARSE a venue telling us a cancel is pending, but cannot RECORD that we attempted one. A
cancel racing a fill collapses to `CANCELLED` or `FILLED` with no trace of the attempt, and the
in-flight-vs-post-confirmation question is unanswerable from our own record.

This is a VOCABULARY gap, not a storage gap — the immutable log would store the transition if the model could express
it.

- [ ] [AGENT] P0. **Extend audit coverage from manual-only to the whole private record** — orders, fills, positions AND
      strategy instructions, through the existing `persist_audit_log` immutable path. Reuse the primitive; do not build
      a second audit mechanism.
- [ ] [AGENT] P0. **Add attempted-action states so an in-flight cancel is distinguishable from a post-confirmation
      cancel**, and a REJECTED cancel is recorded as an attempt rather than vanishing. Either extend canonical
      `OrderStatus` or add a parallel action-audit event — venue schemas already carry `PENDING_CANCEL`.
- [ ] [AGENT] P0. **Audit the ACTION, not just the state** — actor/when/why for cancel, amend, manual booking, virtual
      entry and soft-delete. Pairs with the MiFID todo: a delete is a status change PLUS an audited action record.
- [ ] [AGENT] P1. **Prove each new audit call site's reachability** before claiming coverage — this doc exists because
      components are complete and uncalled. Grep call sites, not imports.

### Artefact disclosure boundary (operator, 2026-08-15)

The client receives **strategy-service code only**. The artefact must carry enough that they understand how
execution-service _generally_ handles their instructions — without becoming a specification anyone could rebuild from.

| Include                                                                                          | Withhold                                                         |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| The INSTRUCTION contract — what a strategy can ask for, what each field means                    | The algorithms that fulfil an instruction                        |
| What the execution flow is TRYING TO ACHIEVE — the goal of each stage                            | The step-by-step execution flow                                  |
| That behaviour is governed per `(client_id, strategy slot)` and hot-reloadable — the config LOOP | The policy rules, thresholds and selection logic inside the loop |
| That `urgency` steers aggressive-vs-passive, and that venue/algo choice follows from policy      | Which algo is chosen under which condition                       |

**Test for a passing artefact**: a client engineer can (a) predict what the system will do with an instruction they
write, and (b) explain why the execution layer exists and what it optimises for — but cannot reconstruct the algorithms
or policy rules from it. Instructions stay clear; execution stays purposeful but not reproducible. **The config loop is
understood, not copyable.**

### Scoping rule: DR is POSITION-shaped, not STRATEGY-shaped

In a disaster you do not need strategy semantics. You need: see positions, flatten a position, place one order, record a
fill that happened elsewhere. **That surface does not grow as strategies are added**, which is what makes it stable
enough to be a dependable fallback. Strategy-shaped instructions are a normal-operations concern.

Corollary (and the cleanest justification for the close-all ruling): **the manual path must speak the EXECUTION
contract, not the strategy contract.** Routing strategy-service-schema instructions through it would couple the
redundancy to the very service it exists to survive. close-all is therefore a position-shaped instruction, which is
already the manual surface's native shape.

### What already exists (checked 2026-08-15 — do NOT rebuild these)

The three capabilities questioned during the ruling are all present:

| Capability                            | Status                                                                                                                                                                                                                       |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Leverage-aware, venue-ordered closing | **Exists.** `close_all/carry_staked_basis.py`: "plan in venue-priority order: hedge first (CeFi), then DeFi unwind", cancels open perp orders, **repays Aave borrow if leveraged**, filtered by a closed-set `SCOPE_VENUES`. |
| Aggressive vs passive                 | **Exists.** `StrategyInstructionEnvelope.urgency: Urgency = Urgency.MEDIUM` (UAC `architecture_v2/schemas.py:221`).                                                                                                          |
| Execution config tied per client+slot | **Exists.** `v2/policy_spec.py` — `bindings: dict["{client_id}:{slot_label}", policy_ref]`, GCS-hot-reloadable.                                                                                                              |

So "how do goals/aggressiveness route to execution" is already the intended seam: strategy sets `urgency` on the
envelope; the `(client_id, slot_label)` policy binding resolves the algorithm. The gap is NOT the contract — it is that
`close_all/*` posts to a nonexistent endpoint (FINDING 1) and so never reaches any of it.

## DOWNSTREAM IMPACT REGISTER — what each ruling forces

Tracked here so a ruling cannot land in one place and rot in four others.

| Surface                                 | Impact                                                                                                                                                                                                                                                                                                                                                                                                                       |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Client artefacts**                    | Execute-side counts are re-derived from CALLER-GRAPH reachability, not module counts. Live handler now wires Uniswap/AAVE/Lido/Jupiter (was 1). Read side 8 venues, registry-driven. **Do not publish a number until Chunk A returns; it has moved three times.**                                                                                                                                                            |
| **Carve-out**                           | DR/manual is a SEPARATE deployment speaking the execution contract — so it is NOT part of a strategy-service carve-out, and sharing strategy-service conveys none of it. Strengthens the existing "complete read, zero write" disclosure position.                                                                                                                                                                           |
| **Codex**                               | `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` already carries the lattice — REFERENCE it, do not duplicate. Needs new/updated: manual-DR topology, the mode axis (now `TradingMode`, shipped), connector liveness + reachability.                                                                                                                                                                      |
| **Plans**                               | venue-coverage issue frontmatter still says "~30 DeFi protocols" (body corrected). Elysium delivery plan inherits every execute-side number.                                                                                                                                                                                                                                                                                 |
| **Already dispatched — DO NOT REGRESS** | `execution-service@37bfaeed0` (real Uniswap/Lido/Jupiter live dispatch, V2InstructionRouter DELETED, Jito connector, Solana signing fix), `strategy-service@926be710` (per-venue per-mode capability axis + `TradingMode`), `@99a93fea` (shadow-SSOT 15/15), `unified-api-contracts@57a0dc9d`/`144b8880` (mSOL + EVM-scoped checksum). Chunk A's re-audit must MEASURE current state, not replay the pre-37bfaeed0 findings. |
| **Existing ratchet**                    | `unified-api-contracts/tests/data/execution_service_venue_reachability_baseline.json` ALREADY tracks venue reachability. EXTEND it — do not build a parallel gate.                                                                                                                                                                                                                                                           |

## RE-TRIAGE against the 2026-08-16 carve-out scope rulings

**Read this before picking up any todo in this document.** The carve-out scope was narrowed sharply on 2026-08-16
(`/plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md` §§A3–A5), and most of this doc's findings were
written BEFORE that narrowing. They are not wrong, but many are no longer on the critical path.

**The contracted scope is now**: BTC/ETH/SOL · **CEX only, exactly four venues** (Bybit, Deribit, Binance, OKX) ·
**ETH staking via Lido only**. Explicitly out: all Solana DeFi/DEX (Jupiter perps, Kamino borrow, Marinade),
Hyperliquid, Aster, every other on-chain venue. Tardis data excluded entirely. DeFi data reduces to Lido rate +
gas fees. Two real archetypes: `CARRY_BASIS_PERP`, `CARRY_STAKED_BASIS` (`CARRY_FUNDING_DISPERSION` ruled out).

### A — GATES THE CARVE-OUT (do these first)

| Item                                                                 | Why it gates                                                     |
| --------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **Lazy-loading refactor, all three layers**                          | §A5 P0. Must land BEFORE/alongside the carve-out, else every later update re-derives a frozen snapshot against a moving eager target |
| E2E completeness: 2 archetypes × 4 CEX venues + Lido, batch/live/paper | §A5 P0. Stronger than "code exists" — the pipeline must run and the data must back it |
| close-all → `/manual/instruction` + HTTP contract test                | Safety, scope-independent. The emergency flatten path 404s today |
| Audit coverage beyond manual; attempted-action states                | Regulatory (MiFID), scope-independent                            |
| Reconciliation pause · virtual persistent-delta entry · soft-delete   | Same — operator-entry safety, applies to any scope               |

**The lazy-loading refactor is three layers, not one** (from `strategy-service/EXTRACTION_AUDIT.md`):

1. `strategy-service/…/factory.py` — eagerly registers every archetype engine across every family. Register only what
   a deployment needs.
2. **`unified-api-contracts` — the dominant blocker.** `registry/__init__.py` (1,270 L) and `internal/__init__.py`
   (2,708 L) eagerly import essentially the whole package: `from unified_api_contracts.internal import
   StrategyArchetype` pulls ~240k lines, with DeFi content interleaved with CeFi/TradFi/sports in flat enums and
   dicts. A lazy `factory.py` does NOT fix this — the live collateral calls still import UAC. **Fleet-wide blast
   radius**, not local.
3. `execution-service/algorithms/algorithms.py` — eagerly imports all 7 algorithms. Cheapest of the three: the repo
   already has the lazy pattern in `adapters/algorithm_factory.py` and `custody/factory.py`.

SIT needs no changes for this (audit § "SIT — no coupling").

### B — REAL, but MAIN-SYSTEM only (does NOT gate the carve-out)

Production still trades these; they are simply outside the contracted universe, so they must not be allowed to block
a send. Marinade / Kamino / Jupiter caller-graph reachability · the 4 bespoke readers (morpho health factor, pendle
maturity, symbiotic + karak withdrawal queues) · vault-share config surface (yearn/beefy/convex/idle) · Kelp rsETH and
ether.fi eETH genesis citations · LST address SSOT entries beyond stETH · Hyperliquid and Aster coverage.

> **Do not delete these todos or mark them done.** They are correctly tracked; they are just not carve-out-gating.
> Re-reading them as "moot" is the error to avoid — the main system runs on them.

### C — CHEAP AND STILL WORTH IT (detectors, review debt)

Reachability gate · `check_pytest_unit_dir_coverage.py` fix · SIT invariants 2 and 4 (1+3 landed, review them) ·
the review backlog, of which **`cc3e07e0c`'s cited contract addresses remain the highest-value item** — the Lido stETH
address is now in the contracted scope, so an error there propagates into the one staking route the client actually
receives.

### What this re-triage changes about priority

The previous ordering put DeFi read/execute coverage first. Under the narrowed scope, **the lazy-loading refactor is
the new head of the queue** — it is an explicit operator P0, it has fleet-wide blast radius, and every day the
carve-out is built against an eagerly-coupled main system raises the cost of keeping it in sync later. The §A5 note is
explicit that both prerequisites are wanted *together*, not compared as alternatives, and that this raises total
pre-ship scope above what §A2 assumed.

## The walkthrough artefact — provenance and editing rules (2026-08-16)

`/codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html` is the target-state, collapsible tour
of strategy-service. Committed 2026-08-16; published to a private artefact URL that redeploys on republish.

**It is a normal HTML file — edit it directly.** It was originally ASSEMBLED by concatenating parts in a session
scratchpad, but those parts are gone and are not needed: the committed file is complete and self-contained. Do not go
looking for a build step.

**The design system is inherited, not invented.** It reuses `strategy-service-deep-dive.html`'s `<style>` block
verbatim — same gold-on-navy tokens, serif body, `.sec-head` / `.keypoints` / `.callout` / `.code` components. The ONLY
addition is the `.st` status mark (live / partial / planned), built from the existing `--good` / `--warn` / `--crit`
tokens. Extend it with those components rather than new CSS: an earlier draft used `<ul class="keypoints">` and
rendered as a broken grid, because that component expects `div > b + span`.

**Two content rules that are not stylistic:**

1. **Status means REACHABLE, not built.** A section earns `live` only when something on a production path calls it —
   the whole point of the document. A status upgraded because "the code exists and passes tests" makes it worthless.
2. **Do NOT name ClearLoop.** There is no ClearLoop code path — zero source hits across all 26 repos; what exists is
   `execution_service/custody/copper.py` and a `COPPER_MPC` signing surface. A client-facing draft already claimed it
   once and was corrected (`/codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md`)
   — a technical reader greps for a named integration. Describe the Copper leg; leave ClearLoop to Copper's own naming.

> **⚠️ `/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` is at 997 of its 1000-line
> HARD cap.** It gained the § I work-surface inventory on 2026-08-16 and has ~3 lines of headroom. The next substantive
> addition WILL breach the gate and block the commit. Split or compress it deliberately, rather than discovering this
> mid-push with something urgent to record.

## Lessons — 2026-08-16 (session 5)

- **A sequential `sed` rename chain cascades.** Renumbering `s12→s14, s13→s15, s14→s16 …` in ASCENDING order re-matched
  already-renamed ids and produced `s18 s17 s18 s17 s18`. Substitute in DESCENDING order so a new value can never be
  matched by a later rule, and verify by printing the whole id list rather than spot-checking one.
- **A repeated `Edit` can land twice and duplicate a whole block.** ~130 lines appeared twice in this doc; I only
  noticed because a later Edit failed with "found 2 matches". Count section headings before pushing an edited doc.
- **But count HEADINGS (`^## `), not substrings.** My own uniqueness check reported a section "duplicated" when the
  second hit was a cross-reference LINK to it. A substring count answers a different question than "does this heading
  appear twice" — the same measure-the-right-property error this whole document is about, committed inside the check
  built to prevent it.
- **`git checkout <ref> -- <file>` + `cp` from a backup is only as good as the backup.** A backup taken AFTER an
  aborted rebase carried a conflict marker on line 1, which broke the `---` frontmatter delimiter, and prettier then
  reflowed the entire YAML block into prose. Recovery is to discard the local copy and re-author from origin — never to
  repair a file you cannot fully see.
- **A word-level "is my copy a superset?" check does not detect structural corruption.** Zero words unique to origin
  proved the CONTENT was a superset while the file carried a stray merge marker and mangled frontmatter. Word-equality and
  structural validity are different properties; the plan-hygiene gate caught what my check could not.
- **Writing ABOUT merge markers trips the merge-marker gate.** These very lessons quoted the literal seven-character
  sequence inside backticks; the plan-discipline checker matched the prose and rejected the commit twice. Describe the
  mechanism in words, never paste the token.
- **This doc has now been mangled FOUR times by one mechanism** — concurrent edit → `safe-doc-push` reconcile →
  prettier reflows the conflicted text and jumbles markers mid-sentence, so a line-anchored grep reads clean while markers
  are present. It is a hot doc edited by three concurrent sessions. Splitting or locking it would fix this; more
  careful editing has not.

## How to verify a reachability claim (method, so this is repeatable)

1. **Find the production entry points** — `rg 'FastAPI\(|APIRouter\(|def main\('`, excluding tests.
2. **Grep the component's instantiation sites**, excluding its own module and `__init__` re-exports. A re-export is not
   a caller. A docstring mention is not a caller.
3. **Follow the chain to a real boundary** — an HTTP route, a CLI entry point, a scheduled job. Stopping at "something
   imports it" is how `V2InstructionRouter` scored as wired.
4. **State which property you measured.** "Write path is real" and "reachable in production" are different claims and
   this corpus has conflated them repeatedly.

- [x] ✅ [AGENT] P1. **Resolve which FastAPI app execution-service's Dockerfile actually deploys** — found 2026-08-15/16,
      not yet chased. `execution_service/api/main.py` (a bare health-only app, `/health`+`/readiness` only) is what the
      Dockerfile's `CMD` serves via uvicorn. `execution_service/api/app.py` — the richer app with `/manual`,
      `/preview`, the evidence router, kill-switch, and the hyperliquid/bybit perp-hedge startup wiring
      (`@app.on_event("startup")`) this doc and its siblings treat as "the" production reachability boundary — is a
      DIFFERENT module. `cloudbuild.yaml` only builds/pushes the image; it does not `gcloud run deploy`, so which app
      actually serves live traffic is resolved elsewhere (deployment-service/deployment-api), not verified this
      session. Every reachability claim in this doc and `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`
      that treats `api/app.py`'s startup wiring as a production entry point is currently UNVERIFIED against actual
      deployment topology — it may be entirely correct (this method matches the doc's own stated "how to verify a
      reachability claim" method above, § step 1: `FastAPI(...)` instantiation, and app.py IS a real FastAPI
      instantiation reachable via `python -m uvicorn` even if not the Dockerfile's default `CMD`), but the gap should
      be closed with a direct check (`/codex/04-architecture/runtime-deployment-topology.md` §5, or a live check of
      the deployed Cloud Run service's actual entrypoint) rather than left assumed.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 12)**: the LST token address SSOT question was stale by
  the time it was asked — already shipped (`unified-api-contracts@53a5adc7` + `@bed96aa0`, 6 reachable cited
  addresses, `strategy-service@5b2a50ed` wired to it, reachability proven by a routing test). No further action.
- **context-scout 2026-08-15**: populated context_scope (5 entries).
- **session 5, 2026-08-15**: re-derived the execute-side tier table on caller-graph reachability (32 connector modules,
  6 genuinely reachable-and-live — see the new table above). Verified, not re-litigated, a concurrent same-slot
  session's `execution-service@37bfaeed0b` (deleted `V2InstructionRouter`, wired `DefiAdapter` to real
  Uniswap/Lido/Jupiter, wired real AAVE/Uniswap calls into `RecursiveLoopOrchestrator`'s iter methods, added Kamino
  borrow/repay, built `jito.py`, fixed a systemic Solana signing bug) — cross-checked its commit-message claims against
  the current code and git log rather than trusting the message. Found and documented two new instances of the same
  defect class: `RecursiveLoopOrchestrator`'s real path is unreached from its one production construction site
  (`api/app.py:321` omits `aave_connector`/`uniswap_connector`), and `QuoteMaintainer`/`DeltaProxyRepricer` (unrelated
  module, found while fixing a stale docstring) has zero production callers. Shipped the LST address SSOT migration
  (`execution-service`, 5 files, 6 addresses) closing the last open Task-3-shaped todo in this doc. Discovered
  mid-session that `execution_service/api/main.py` (the module the Dockerfile's `CMD` actually serves via uvicorn) is a
  bare health-only FastAPI app, distinct from `execution_service/api/app.py` (the richer app with
  `/manual`/`/preview`/kill-switch/perp-hedge startup wiring this doc and its sibling treat as "the" production entry
  point) — did not chase which one Cloud Run actually deploys (deployment-topology question, out of this session's
  scope); flagged here so a future session doesn't re-derive reachability against the wrong app file without knowing
  this ambiguity exists.
- **session 6, 2026-08-16**: shipped the mode-axis DESIGN PASS (`strategy-service@701dce1850`): `BasePositionAdapter`
  gained an explicit `mode: TradingMode` + `testnet` (PAPER sub-mode selector), resolved per adapter-construction;
  `reconciliation_engine.py` gained a `leg: ReconVerdictType` guard (paper-vs-batch = determinism check, paper-vs-live
  = execution check — different meanings on failure); close_all migrated onto `POST /manual/instruction` with request-
  shape mapping (`strategy-service@701dce1850`) + an HTTP-level contract test proving it, including a regression guard
  that `/api/orders` still 404s (`execution-service@3800849e87`); the dual position-resolver (FINDING 4) unified —
  `routing.create_position_adapter` now delegates to `factory.get_position_adapter` instead of carrying a parallel,
  zero-caller implementation; and the 4 bespoke DeFi readers (Morpho health factor, Pendle maturity, Symbiotic + Karak
  withdrawal-delay metadata) shipped, all real reads with machine-verified function selectors, not stubs.
  **Reconciled two independent same-goal collisions from concurrent sessions in this shared checkout, rather than
  overwriting either side**: (1) `execution-service@d981725c2` did the identical LST-address-SSOT migration this
  session was also mid-writing — their version was strictly more complete (a shared `required_lst_address()` helper +
  `symbiotic.py` coverage this session's draft lacked), so it was taken as-is, with this session's non-overlapping
  `quote_maintenance.py` fix and the new contract test carried through onto the same commit chain
  (`execution-service@3800849e87`). (2) `strategy-service@70c3c05f` (Kamino bespoke position adapter, an unrelated
  concurrent effort) touched the same `capabilities.py`/`factory.py` dispatch tables this session's mode-axis rewrite
  also touched — merged additively (both venue lists combined) and, since `KaminoPositionAdapter` predated the mode
  axis and had no `mode`/`testnet` params at all, extended it to accept and thread them through consistently with
  every other adapter, rather than leaving it as a silent mode-unaware exception inside a capabilities table that
  claimed full mode coverage for it. Both reconciliations were done in an isolated `git worktree` (never touching the
  shared checkout's live/dead foreign WIP directly — README.md/config.py/nav_snapshot_publisher.py/
  webhook_dispatcher.py + 2 new docs sat dirty from another concurrent session throughout, checked for liveness via
  mtime each time before ever stashing them, restored via `stash pop` once the reconciled commit was pushed), then the
  reconciled commit was replayed into the real checkout once the foreign WIP tested dead (>120s stale) so the
  baseline-ratchet quality gates (which key off the checkout's directory basename) would resolve against the correct
  scope name rather than the worktree's differently-named one — the first gate run against a mismatched worktree name
  produced a false pass (STEP 5.101/5.107 baseline lookups silently resolved to an empty/zero baseline for the unknown
  scope name, making legitimate pre-existing findings look new; re-run against the correctly-named checkout to get a
  trustworthy result). **Root-caused and reported (not authored — landed independently by another party mid-session,
  `unified-trading-pm@bea0594fd2`) two host-wide QG-governor bugs** that stalled every `unified-api-contracts`
  quickmerge on this host for 2-4 hours: the reservation-mode heavy-phase gate's repo-identity resolution silently fell
  through to the literal string `"unknown"` (neither `QG_GOVERNOR_REPO` nor `SERVICE_NAME` is ever set by any caller),
  inflating every run's RAM reservation to the 5.5 GB worst-case default regardless of the repo's real (much smaller)
  measured baseline; separately, the total-instance gate's acquire loop had no bound, so a process that won a lock but
  hit a control-flow bug before recognizing it would spin printing "queued Ns" forever while still holding the real
  kernel-level flock (confirmed via `lsof` on two independent stuck PIDs, one 1h10m stale, one 4h17m stale, both
  terminated by hand after confirming zero CPU and zero forward progress) — both fixed upstream mid-session (60-minute
  hard bound on the acquire loop; the repo-identity resolver now falls back to the same git-based `_qg_repo_name()`
  auto-detection the total-instance gate already used correctly).
- **2026-08-16 (plan_reconciler, ao tranche, dispatch agt-3eb42b, post-compact)**: filed the `SymbioticConnector`
  reachability-baseline todo above after 2 identical consecutive quickmerge failures isolated it as the sole remaining
  blocker (a separate `plan-commit-sha-evidence` failure in the same runs was a distinct, unrelated bad-SHA citation in
  `self_hosted_runner_billing_migration_wave2_remaining_2026_08_15.md`, independently fixed by a peer session
  mid-diagnosis). Caught `effde0f7d5`'s commit message falsely claiming the baseline fix (empty diff on direct
  measurement) and documented it in-line so the next reader wouldn't trust it. Armed a bounded (~28 min, 60s-interval)
  background watchdog polling `origin/live-defi-rollout`'s actual baseline JSON content directly, rather than
  blind-retrying the full quickmerge — cheaper and matches "poll on a progress metric, not activity." Detected the real
  fix (`unified-trading-pm@bb6faddb`) on the watchdog's first check; re-verified independently before flipping this
  todo (0 occurrences, real 1-line-deletion diff — not another hollow claim).
- **2026-08-17 (slot 15, review) — reconciled two AO dispatch batch shipments back into this doc.**
  `venue_readiness_ao_dispatch_batch1_2026_08_16` shipped both SIT invariant 2 and LST address SSOT migration
  Chunk B (marinade/jito_restaking/symbiotic) as todos of its own, without cross-checking against this doc's already-
  open invariant-2 todo or already-checked LST-migration todo. Flipped the invariant-2 todo to done and added an
  addendum to the LST-migration todo, both independently re-verified: `unified-api-contracts@86d5f5af46` +
  `system-integration-tests@cce1adebc6` (invariant 2), `execution-service@529af8d22c` + `unified-api-contracts@6151de2a2a`
  (LST Chunk B) — all four SHAs confirmed live ancestors of `origin/live-defi-rollout`, content spot-checked, not
  trusted from the batch plan's own copy of the evidence lines. Part of
  `venue_readiness_ao_dispatch_batch1_finalize_2026_08_16`'s reconciliation todo.
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:265f9cd3225b808a]: KEEP-NA, valid -- Heterogeneous P0 issue spanning caller-graph reachability + 2 operator-ruling sections on live-capital reconciliation/audit machinery. Of 11 open items: 2 explicit [OPERATOR] tags, 1 redirects to a LOCAL/operator-scoped design todo per 2026-08-09 ruling BLK-7f4d33db, 1 blocked on Chunk A's number (doc's own note: "has moved three times"), 3 new safety mechanisms on live-capital reconciliation (doc's own text: a typo here "compounds into a real trade"), 3 depend on an undecided OrderStatus-extension-vs-parallel-audit-event design fork, 1 (audit-coverage extension, line 598) is a lower-confidence MISCLASSIFIED_LIKELY_AO_ELIGIBLE flag for a future pass, not acted on this run. A prior same-day pass already closed 2 stale items; none of the current 11 are stale. Cross-cutting tranche audit.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **2026-08-22 — ruling D76 (e2e wiring rulings)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Close the ruling, require manual OTC review (typo-compounding risk), and scope the
  wiring as a LOCAL design plan — it's a live-capital design call, not a patch. Applied above to the close-all-ruling
  todo (CANCELLED, already closed+shipped) and the OTC-auto-book todo (retagged to require manual review). The
  "scope the wiring as a LOCAL design plan" part of this ruling additionally applies to the still-open `[AGENT] P0`
  items under this doc's "MANUAL / DISASTER-RECOVERY DESIGN" (reconciliation pause, virtual/persistent-delta entry,
  soft-delete) and "AUDIT / IMMUTABILITY OF THE PRIVATE RECORD" sections — per the ruling these are a live-capital
  design call that should be scoped as their own LOCAL design plan rather than dispatched as direct AGENT patches;
  not individually rewritten in this pass (a plan-authoring task, out of scope for a doc-ruling sweep) — flagged here
  so it isn't lost. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
