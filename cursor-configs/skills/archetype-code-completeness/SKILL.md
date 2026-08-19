---
name: archetype-code-completeness
description: >-
  Derive, per StrategyArchetype (60 as of 2026-08-19) x mode (batch/paper/live), a CODE-completeness verdict --
  distinct from readiness-state-dump's `strategy — archetype half` leg, which answers "which archetypes can this
  VENUE'S DATA satisfy" via satisfying_archetypes(). This skill answers a different question: "are this archetype's
  code paths and hooks complete", independent of any venue's data. /plans/epics/system_readiness_master.md § W1:
  "Archetype readiness is CODE completeness, not data availability... Nothing answers [this]." Checks four
  machine-detectable hooks (factory registration, PARAM_SCHEMA_REGISTRY entry, allocator-rank entry, mode-specific
  dispatch) plus a fifth (target_universe catalog) found during research. Where a hook has no clean registry lookup
  (paper's per-family tick-loader dispatch, live's dispatch below the shared orchestrator), emits a DATED AGENT AUDIT
  record instead of guessing or leaving the cell blank. Trigger on `/archetype-code-completeness`, "is this archetype
  code-complete", "which archetypes are wired for batch/paper/live", "archetype code completeness dump", "what's
  missing for this archetype to run", "dump archetype hooks".
---

# archetype-code-completeness

Derives, per `(StrategyArchetype x mode)`, a code-completeness verdict across five hooks living entirely inside
strategy-service. `/plans/epics/system_readiness_master.md` § W1, the todo directly above "Auto-derive readiness per
(venue x mode)": readiness-state-dump's `strategy — archetype half` leg (`satisfying_archetypes()`) answers "which
archetypes can this venue's DATA satisfy" -- a data question. This skill answers "are this archetype's code paths and
hooks complete for batch / paper / live" -- a code question, independent of any venue.

## Run it

**Requires** running under strategy-service's OWN venv -- every hook checked here
(`ARCHETYPE_ENGINE_REGISTRY`, `PARAM_SCHEMA_REGISTRY`, `ALLOCATOR_ARCHETYPE_REGISTRY`, `STRATEGY_TYPE_TO_SLOT`, the
`paper_run_handler.py` tick-loader frozensets, `topology_enforcement`) lives inside strategy-service itself. Unlike
readiness-state-dump (which runs under instruments-service's venv and shells out once to strategy-service for the
position-adapter half), this dump needs **no cross-venv subprocess at all**:

```bash
cd strategy-service && .venv/bin/python3 \
    ../unified-trading-pm/cursor-configs/skills/archetype-code-completeness/scripts/derive_archetype_completeness.py
```

```bash
python derive_archetype_completeness.py                                # full dump, summary view
python derive_archetype_completeness.py --verbose --limit 20
python derive_archetype_completeness.py --archetype CARRY_STAKED_BASIS --mode LIVE
python derive_archetype_completeness.py --json
```

**Verified live 2026-08-19** against real strategy-service code (60 archetypes x 3 modes = 180 rows): counts
cross-validate exactly against a direct read of every source registry (32 factory-registered engines, 35
PARAM_SCHEMA_REGISTRY entries, 8 dedicated allocator-rank members, 12 paper tick-loader frozenset hits, 17
STRATEGY_TYPE_TO_SLOT reverse-resolutions, 60/60 topology docs present). Overall rollup: ~6 ready / ~47 not_ready /
~7 unverified per mode -- most archetypes are genuinely code-incomplete today (only 32/60 have an engine at all; the
entire `VOL_*`/unbuilt `MARKET_MAKING_*` family accounts for most of the gap), which matches what
`param_schema.py`'s and `factory.py`'s own module docstrings already say in prose -- this dump makes it a queryable,
per-archetype, per-mode table instead.

## The five hooks

| Hook                      | Real check reused                                                                                                           | Scope          | Absence means                                                                                                                                                                                                                        |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `engine_factory`          | `factory.ARCHETYPE_ENGINE_REGISTRY` membership + the lazy import actually resolving                                         | mode-invariant | `not_ready` -- no v2 engine class exists; `V2EngineOrchestrator.build()` raises `KeyError` in every mode                                                                                                                             |
| `param_schema`            | `param_schema.PARAM_SCHEMA_REGISTRY` membership (keyed by `archetype.value`)                                                | mode-invariant | `not_ready` -- distinguishes a known baselined gap (`check_archetype_schema_coverage().missing_schema`) from a NEW regression                                                                                                        |
| `target_universe_catalog` | `target_universe.catalog.specs_for_archetype(archetype)` non-empty                                                          | mode-invariant | `not_ready` -- the exact condition `paper_run_handler.py` itself raises `ValueError` on; no rollout instance exists                                                                                                                  |
| `allocator_rank`          | dedicated `AllocatorArchetype.<VALUE>_RANK` member in `ALLOCATOR_ARCHETYPE_REGISTRY`                                        | mode-invariant | **`unverified`, never `not_ready`** -- 8 of 16 `AllocatorArchetype` members are generic and may legitimately apply; see `checks.py`'s module docstring for why this deliberately departs from readiness-state-dump's proxy asymmetry |
| `batch_dispatch`          | `archetype_slot_resolver.STRATEGY_TYPE_TO_SLOT` reverse-lookup                                                              | BATCH only     | `unverified` -- `batch_rerun.py`'s separate paper-manifest-replay path may still cover it; not cleanly confirmable                                                                                                                   |
| `paper_dispatch`          | membership in one of `paper_run_handler.py`'s 9 named tick-loader frozensets (imported live via `getattr`, never hardcoded) | PAPER only     | **DATED AGENT AUDIT (2026-08-19)** -- falls through to a generic perp-basis loader untested for non-DeFi-carry archetypes; `unverified` with the audit citation, not a guess either way                                              |
| `live_topology_gate`      | `topology_enforcement.load_topology_requirements(archetype.value)` resolving                                                | LIVE only      | `not_ready` -- `service_entry.py` calls this unconditionally at live boot; a missing/malformed archetype doc crashes startup, a real gate not a proxy                                                                                |

Full per-hook reasoning, including exactly why `allocator_rank` and `paper_dispatch` deliberately break from the
usual proxy-presence-is-`unverified`/proxy-absence-is-`not_ready` asymmetry, lives in `scripts/checks.py`'s module
docstring -- read it before extending this skill, not this file.

## Rollup

Same policy as readiness-state-dump's `checks.rollup()`: any leg `not_ready` dominates the mode's overall verdict;
all-`ready` legs give `ready`; otherwise (no failures, some `unverified`) the overall is `unverified`.

## Dated agent-audit records

Two hooks above have no clean registry lookup and are recorded as **dated, cited, source-read judgments** rather
than silently guessed or left blank, per the task's own instruction ("where a hook cannot be machine-detected, emit
a dated agent-audit record"):

1. **`paper_dispatch` absence** (per-archetype, ~48/60 archetypes as of 2026-08-19) -- `paper_run_handler.py`'s
   9 named frozensets cover only the DeFi carry/yield family; every other archetype falls through to a generic
   perp-basis loader whose correctness for that archetype was not proven either way by static analysis.
2. **Live dispatch below the shared orchestrator** (system-wide, one note repeated on every LIVE row) --
   `cascade_subscriber.py` and `service_entry.py` were grepped for archetype-registry references and none were
   found, consistent with live reusing `engine_factory`'s shared spine and adding nothing further, but this is an
   absence-of-evidence read. `scripts/checks.py`'s `LIVE_DISPATCH_AGENT_AUDIT_NOTE` and `AGENT_AUDIT_DATE` constants
   are the single place to update if a future pass reads `cascade_subscriber.py` in full and either confirms or
   overturns this.

Re-date (and re-verify) either note if the cited source files change materially after `AGENT_AUDIT_DATE`.

## What this skill deliberately does NOT check

`ARCHETYPE_FEATURE_GROUPS` / `satisfying_archetypes()` (DATA availability, readiness-state-dump's job, not this
skill's), venue-specific readiness of any kind (this skill is not venue-scoped at all), whether a factory-registered
engine's business logic is _correct_ (only that it resolves), and whether `cascade_subscriber.py`'s live message
consumption path has its own per-archetype gate beyond the shared orchestrator (see the live dated-audit note above).

## Guardrails

Read-only end to end: imports strategy-service's own registries and calls `specs_for_archetype()` /
`load_topology_requirements()`, both pure/local (no network or GCS call of their own -- the dynamic-ADV-ranking
fallback inside a couple of carry archetypes' spec builders does attempt a GCS read when `GCP_PROJECT_ID` is unset in
the environment, catches its own failure, logs an `ERROR`-level line, and falls back to a static coin list --
harmless noise on stderr, not a failure of this script; set `GCP_PROJECT_ID` in the environment to silence it).
Never writes GCS, never mutates a registry, never launches a VM, never calls a live venue API.
