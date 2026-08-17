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
```

The strategy position-adapter half additionally shells out **once** (batched across every venue in scope, not
per-venue) to `strategy-service/.venv` as a subprocess (`_strategy_position_probe.py`) — never an import, since UAC
code must not depend on a T4 service and this script itself is UAC-scoped otherwise. If that venv is missing, the
position-adapter half reports `unverified` for every row, honestly, rather than being silently skipped.

**Verified live 2026-08-17** against real production data (288 venues x 3 modes = 864 rows, ~20s): e.g.
`OKX-FUTURES` at `BATCH` correctly derives `strategy=not_ready` even though its archetype half is `ready` — because
`position_read_mode_availability('OKX-FUTURES').batch == "none"` — a concrete proof the AND-logic (`checks.strategy_leg`)
does not let a strong archetype signal paper over a missing position adapter.

## What's real vs. `unverified`, and why (the proxy discipline)

Every leg is one of `ready` / `not_ready` / `unverified`. The policy (see `scripts/checks.py`'s module docstring):

- A **registry/manifest FACT** — an observed capture count, a Layer-1 catalogue enumeration, or an authoritative SSOT
  declaration that something else in the codebase already uses as an approval gate — produces `ready`/`not_ready`.
- A **capability-only proxy** — a code path or registry entry that could serve the request but does not confirm it
  actually ran — reports `unverified` on presence, and `not_ready` on absence (absence is still hard evidence of
  non-readiness; presence of a capability is not hard evidence of operation). Per CLAUDE.md: _"a row count, an exit
  code, a green test, 'the connector exists' are all proxies."_

| Leg                                  | Real check reused                                                                                                                | Why (fact vs. proxy)                                                                                                                                                |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **declared**                         | UAC `VENUE_DATA_TYPE_CAPABILITIES` membership                                                                                    | Fact — the registration itself                                                                                                                                      |
| **instruments_service**              | `coverage.json`'s `layer_1.by_venue[venue].expected_tuples > 0`                                                                  | Fact — real IS-catalogue enumeration                                                                                                                                |
| **market_tick_data** (BATCH only)    | `coverage.json` `captured` counts per observed data_type                                                                         | Fact — observed capture. PAPER/LIVE report `unverified`: coverage.json is not mode-partitioned, so live/paper capture state is not observable from this artifact    |
| **market_data_processing**           | `venue_data_types & MDPS_DERIVABLE_DATA_TYPES`                                                                                   | Proxy — capability only; a future increment should read MDPS's own manifest rows for real observed consumption (absence still gives a real `not_ready`)             |
| **features**                         | `venue_strategy_consumability.orphaned_data_types()` (the shipped contract-step-17/18 module, reusing `FEATURE_REQUIRED_INPUTS`) | Fact — an authoritative SSOT declaration, same tier as `declared`                                                                                                   |
| **strategy — archetype half**        | `venue_strategy_consumability.satisfying_archetypes()`                                                                           | Fact — `ARCHETYPE_FEATURE_GROUPS` is a declared SSOT, not a proxy                                                                                                   |
| **strategy — position-adapter half** | strategy-service's own `position_read_mode_availability(venue)` (mode-aware: batch/live/paper)                                   | Fact — a real, audited per-(venue,mode) table                                                                                                                       |
| **strategy (overall)**               | AND of both halves above                                                                                                         | Fails if either half fails; `unverified` only if neither fails and at least one is unverified                                                                       |
| **execution_transfers**              | UAC `VENUE_WALLET_CAPABILITIES` membership                                                                                       | Proxy — declares wallet _structure_, not a proven working rail; absence still gives a real `not_ready`                                                              |
| **execution_instruction**            | _(none wired yet)_                                                                                                               | Always `unverified` — `execution-service/execution_service/v2/policy_resolver.py` is the real `InstructionActionV2`-adaptor registry a future increment should read |

**Not covered by this pass, and left honestly `unverified` or absent from the leg set**: ML-published-output
readiness (Pub/Sub-for-live / GCS-for-batch — no static signal), execution transfers' proof-of-a-working-rail beyond
declared structure, and error-code-classification coverage (step 10). These are legitimate `unverified` states per
the operator's own ruling, not gaps this dump papers over.

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

Read-only end to end: reads `coverage.json` via UTL `cloud_interface`, reads UAC registries, runs one bounded
subprocess into `strategy-service`'s own venv calling a function that itself performs no I/O. Never writes GCS, never
mutates a registry, never launches a VM, never calls a live venue API. If `coverage.json` cannot be read, the
`instruments_service`/`market_tick_data` legs report `unverified` for every row rather than aborting the whole dump —
the other legs (declared, features, strategy, execution) do not depend on it.
