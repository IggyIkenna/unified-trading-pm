---
name: readiness-state-dump
description: >-
  Derive, per (venue x mode: batch/paper/live), a readiness state across instruments-service -> MTDS -> MDPS ->
  features -> strategy -> execution. Readiness is DERIVED, never declared (operator ruling 2026-08-16) -- a leg with
  no real machine check prints `unverified`, never a silent pass. The strategy leg is specifically an AND of two real
  checks: a position adapter exists for this venue in this mode (strategy-service's own
  position_read_mode_availability), AND at least one archetype's full FEATURE_REQUIRED_INPUTS is satisfiable from
  this venue (the shipped contract-step-17 check) -- both, not either. Tuesday deliverable 1 of
  /plans/active/data_pipeline_completion_2026_08_21.md § "Tuesday dumps", the same artefact
  /plans/epics/system_readiness_master.md's W1/W20 name. Shares its shard-enumeration engine with the
  honest-coverage-dump skill. Trigger on `/readiness-state-dump`, "dump readiness state", "is this venue ready for
  live", "what's blocking this venue from paper", "run the readiness state dump", "derive readiness per venue and
  mode".
---

# readiness-state-dump

Derives, per `(venue x mode)`, a readiness verdict across the six-service chain
(`/plans/epics/system_readiness_master.md` § "The organising principle"): instruments-service -> MTDS -> MDPS ->
features -> strategy -> execution. **Readiness is DERIVED, never declared** (operator ruling 2026-08-16,
`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`): a leg with no real machine check prints
`unverified`, never a silent pass. Tuesday deliverable 1 in
`/plans/active/data_pipeline_completion_2026_08_21.md` § "Tuesday dumps" — **recording the state is the deliverable;
achieving it is not.**

## Run it

**Requires** a Python whose venv has both `unified_api_contracts` AND `unified_trading_library` importable (the
latter via the shared `shard_universe.py` GCS read). `unified-api-contracts` is T0 and does not depend on
`unified-trading-library`, so this does **not** run under UAC's own venv — run it under `instruments-service`'s venv
instead, which carries both:

```bash
cd instruments-service && .venv/bin/python3 \
    ../unified-trading-pm/cursor-configs/skills/readiness-state-dump/scripts/derive_readiness.py
```

```bash
python derive_readiness.py                              # full universe, summary counts
python derive_readiness.py --verbose --limit 20          # per-venue-per-mode detail, capped
python derive_readiness.py --venue OKX-FUTURES --mode LIVE --verbose
python derive_readiness.py --asset-group cefi --json
python derive_readiness.py --skip-strategy-probe         # if strategy-service/.venv is unavailable
python derive_readiness.py --skip-execution-probe        # if execution-service/.venv is unavailable
python derive_readiness.py --skip-mtds-probe             # if market-tick-data-service/.venv is unavailable
```

Three cross-venv subprocess probes back the legs that live outside UAC/instruments-service:

- The strategy position-adapter half shells out **once** (batched across every venue in scope, not per-venue) to
  `strategy-service/.venv` (`_strategy_position_probe.py`).
- The four execution-service surfaces (`execution_orders`/`execution_fills`/`execution_trades`/
  `execution_account_balance`) shell out **once** (batched) to `execution-service/.venv`
  (`_execution_order_capability_probe.py`).
- The `market_tick_data` LIVE leg (reused for both PAPER and LIVE rows, see below) shells out **once** (no per-venue
  input — it reads a global registry) to `market-tick-data-service/.venv` (`_mtds_live_feed_probe.py`).

None of these are imports — UAC code must not depend on a T4 service, and this script itself is UAC-scoped
otherwise. If a venv is missing, the corresponding leg(s) report `unverified` for every row, honestly, rather than
being silently skipped.

**Verified live 2026-08-17** against real production data (288 venues x 3 modes = 864 rows, ~20s): e.g.
`OKX-FUTURES` at `BATCH` correctly derives `strategy=not_ready` even though its archetype half is `ready` — because
`position_read_mode_availability('OKX-FUTURES').batch == "none"` — a concrete proof the AND-logic (`checks.strategy_leg`)
does not let a strong archetype signal paper over a missing position adapter.

**Extended 2026-08-19** (W1's two 2026-08-19 P0s) to the full six-surface table and re-verified live against
`OKX-FUTURES`: `execution_orders` correctly derives `unverified` at `BATCH` (no real check exists for a mode that
never invokes a real adapter) but `ready` at both `PAPER` and `LIVE` (UAC `validate_operation(place_order,
env=testnet|mainnet)` resolves supported) — a concrete proof the orders leg is genuinely mode-aware, not a
mode-invariant proxy repeated three times. `market_tick_data` likewise flips from the `BATCH`-only coverage.json
verdict to the shared live-feed verdict on `PAPER`/`LIVE` (`unverified` — `OKX-FUTURES` is registered in
`WS_FEED_CONNECTOR_FACTORIES`), the same verdict on both rows since paper always consumes the live feed.

## What's real vs. `unverified`, and why (the proxy discipline)

Every leg is one of `ready` / `not_ready` / `unverified`. The policy (see `scripts/checks.py`'s module docstring):

- A **registry/manifest FACT** — an observed capture count, a Layer-1 catalogue enumeration, or an authoritative SSOT
  declaration that something else in the codebase already uses as an approval gate — produces `ready`/`not_ready`.
- A **capability-only proxy** — a code path or registry entry that could serve the request but does not confirm it
  actually ran — reports `unverified` on presence, and `not_ready` on absence (absence is still hard evidence of
  non-readiness; presence of a capability is not hard evidence of operation). Per CLAUDE.md: _"a row count, an exit
  code, a green test, 'the connector exists' are all proxies."_

| Leg                                       | Real check reused                                                                                                                                                                                                                | Why (fact vs. proxy)                                                                                                                                                                       |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **declared**                              | UAC `VENUE_DATA_TYPE_CAPABILITIES` membership                                                                                                                                                                                    | Fact — the registration itself                                                                                                                                                             |
| **instruments_service**                   | `coverage.json`'s `layer_1.by_venue[venue].expected_tuples > 0`                                                                                                                                                                  | Fact — real IS-catalogue enumeration                                                                                                                                                       |
| **market_tick_data** (BATCH)              | `coverage.json` `captured` counts per observed data_type                                                                                                                                                                         | Fact — observed capture                                                                                                                                                                    |
| **market_tick_data** (PAPER, LIVE)        | MTDS `WS_FEED_CONNECTOR_FACTORIES` registry membership (via `_mtds_live_feed_probe.py`) — the SAME verdict on both rows, since paper always consumes the live feed (§ 0 of the reconciliation SSOT, never a separate paper feed) | Proxy — a registered connector class doesn't confirm the live feed is actually flowing; absence still gives a real `not_ready`                                                             |
| **market_data_processing**                | `venue_data_types & MDPS_DERIVABLE_DATA_TYPES`                                                                                                                                                                                   | Proxy — capability only; a future increment should read MDPS's own manifest rows for real observed consumption (absence still gives a real `not_ready`)                                    |
| **features**                              | `venue_strategy_consumability.orphaned_data_types()` (the shipped contract-step-17/18 module, reusing `FEATURE_REQUIRED_INPUTS`)                                                                                                 | Fact — an authoritative SSOT declaration, same tier as `declared`                                                                                                                          |
| **strategy — archetype half**             | `venue_strategy_consumability.satisfying_archetypes()`                                                                                                                                                                           | Fact — `ARCHETYPE_FEATURE_GROUPS` is a declared SSOT, not a proxy                                                                                                                          |
| **strategy — position-adapter half**      | strategy-service's own `position_read_mode_availability(venue)` (mode-aware: batch/live/paper)                                                                                                                                   | Fact — a real, audited per-(venue,mode) table                                                                                                                                              |
| **strategy (overall)**                    | AND of both halves above                                                                                                                                                                                                         | Fails if either half fails; `unverified` only if neither fails and at least one is unverified                                                                                              |
| **execution_orders** (BATCH)              | execution-service adapter presence (`get_supported_venues()`, via `_execution_order_capability_probe.py`)                                                                                                                        | Proxy — BATCH never invokes a real adapter (simulated fills), so presence alone can't confirm order capability; always `unverified` when an adapter is present                             |
| **execution_orders** (PAPER, LIVE)        | UAC `validate_operation(venue, "place_order", env=testnet\|mainnet)`                                                                                                                                                             | Fact — the same declared per-env capability execution-service's own `factory._run_capability_preflight` gates real order placement on                                                      |
| **execution_fills**, **execution_trades** | execution-service adapter presence (`BaseCLOBAdapter.get_fills()` is implemented by construction wherever an adapter is registered — no distinct trades-vs-fills method exists)                                                  | Proxy — presence only; absence still gives a real `not_ready`. Mode-invariant: adapter presence doesn't vary by mode                                                                       |
| **execution_account_balance**             | execution-service adapter presence (`BaseCLOBAdapter.get_account_state()`)                                                                                                                                                       | Proxy — same tier as fills/trades above                                                                                                                                                    |
| **execution_transfers**                   | UAC `VENUE_WALLET_CAPABILITIES` membership                                                                                                                                                                                       | Proxy — declares wallet _structure_, not a proven working rail; absence still gives a real `not_ready`                                                                                     |
| **execution_instruction**                 | `instruction_actions.measure()` — AST coverage of `InstructionActionV2` vs `backtest_v2/action_handlers.py::resolve_settlement`                                                                                                  | Per-venue `unverified` — no per-venue instruction-path registry exists; the coverage measured is GLOBAL, so it is reported as a dump-level finding, never as a per-row verdict (see below) |

### The `execution_instruction` leg — what was measured, and what is still blocked

**Corrected 2026-08-20.** This table previously pointed the leg at
`execution-service/execution_service/v2/policy_resolver.py`, calling it "the real `InstructionActionV2`-adaptor
registry". That is wrong, and it cost a reading of the file to find out: `policy_resolver.py` resolves an execution
**algorithm** for an instruction, keyed by `(client_id, slot_label)`, with venue appearing only as one `applies_to`
gate dimension (`venue_category`). It never answers "can this venue execute this action".

The only action-keyed dispatch that exists is `backtest_v2/action_handlers.py::resolve_settlement`, and it is
**venue-independent and backtest-scoped** (it resolves a deterministic benchmark settlement for the batch=live
determinism proof). So:

- The leg stays **`unverified` per venue** — a real per-venue instruction-path check still does not exist.
- What it now carries is a **measured denominator** instead of "no check wired". Measured 2026-08-20:
  **11/16 `InstructionActionV2` actions have a settlement path** (10 handled, `CANCEL` is control-plane no-fill by
  design), and **5 raise `UnhandledActionError`: `CONVERT_DUST`, `LP_BURN`, `LP_MINT`, `REPAY`, `WITHDRAW`.**
- That gap is surfaced **once, as a dump-level finding**, never folded into the 864 rows. It is global and
  backtest-scoped, so attributing it to any particular venue-mode would claim more than was measured.

Mapping actions onto UAC `operation_details` keys was considered and **rejected as drift**: measured 2026-08-20 that
vocabulary is per-venue idiosyncratic (`place_order` / `create_order` / `new_order` / `post_order` / `add_order` /
`submit_order` / `buy`+`sell`) and mixed with feed endpoints (`l2_book`, `all_mids`, `ws_trades`), so a hand-built
action→operation map would silently misread any venue spelling its order verb differently.

A real per-venue check remains blocked on execution-service exposing one — filed as an inbound request on
`/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`.

**Not covered by this pass, and left honestly `unverified` or absent from the leg set**: ML-published-output
readiness (Pub/Sub-for-live / GCS-for-batch — no static signal), execution transfers' and fills/trades/balance's
proof of real observed operation beyond declared/registered structure, and error-code-classification coverage (step
10). These are legitimate `unverified` states per the operator's own ruling, not gaps this dump papers over.

## The overall (rollup) verdict

`checks.rollup()`: if any leg is `not_ready`, the venue-mode is `not_ready` (a real failure dominates). Else if every
leg is `ready`, it's `ready`. Otherwise (`no failing legs, some unverified`) it's `unverified` — the venue-mode
cannot be confirmed ready, but nothing has actively failed either.

## Shared shard enumeration — no hardcoded grain

Imports `../honest-coverage-dump/scripts/shard_universe.py` (via a `sys.path` insertion at the top of
`derive_readiness.py` — the two skill directories are siblings under `cursor-configs/skills/`) for every
`coverage.json` read. Grain (2-tuple vs. 3-tuple) is auto-detected from the payload, exactly as in
honest-coverage-dump — see that skill's SKILL.md for the detail. This dump never re-reads GCS independently and
never disagrees with honest-coverage-dump about what a "shard" is.

The **venue universe** itself is the union of UAC's declared `VENUE_DATA_TYPE_CAPABILITIES.keys()` and every venue
observed in `coverage.json` — an undeclared-but-captured venue shows up with `declared=not_ready`, which is itself a
real, useful finding (drift between what's registered and what's actually being captured), not a filtered-out edge
case.

## Guardrails

Read-only end to end: reads `coverage.json` via UTL `cloud_interface`, reads UAC registries, and runs three bounded
subprocess probes (`strategy-service`, `execution-service`, `market-tick-data-service`, each into that service's own
venv) calling functions that themselves perform no I/O — the execution-service probe never constructs a real adapter
instance (it only checks registry/capability membership), and the MTDS probe only side-effect-loads connector
modules to populate a registry, it never opens a socket. Never writes GCS, never mutates a registry, never launches a
VM, never calls a live venue API. If `coverage.json` cannot be read, the `instruments_service`/`market_tick_data`
legs report `unverified` for every row rather than aborting the whole dump — the other legs (declared, features,
strategy, execution) do not depend on it.
