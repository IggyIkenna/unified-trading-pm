---
name: archetype-code-completeness
description: >-
  Derive, per StrategyArchetype (60 as of 2026-08-20; 59 in scope + 1 policy-excluded) x mode (batch/paper/live), a CODE-completeness verdict --
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

**Re-measured 2026-08-20** after the VOL / MARKET_MAKING / PORTFOLIO registration wave
(`strategy-service`, code-readiness ruling): 59 factory-registered engines, 40 PARAM_SCHEMA_REGISTRY entries,
59/59 target-universe catalogs, 8 dedicated allocator-rank members, 12 paper tick-loader frozenset hits, 17
STRATEGY_TYPE_TO_SLOT reverse-resolutions, 60/60 topology docs present. Overall rollup per mode:
**6 ready / 19 not_ready / 1 excluded_by_policy / 34 unverified** (BATCH; PAPER is 5/19/1/35).

The 19 `not_ready` are now EXACTLY the archetypes with a factory-registered engine but no
`PARAM_SCHEMA_REGISTRY` entry -- `engine_factory` and `target_universe_catalog` are 177/177 ready. That is the
whole remaining code gap, and it is the same set `param_schema.py`'s `_SCHEMA_COVERAGE_BASELINE_MISSING_SCHEMA`
shrinking ratchet already tracks.

The **prior baseline (2026-08-19) was ~6 ready / ~47 not_ready / ~7 unverified** with only 32/60 engines
registered. Most of that gap was not missing code: 22 of the 28 unregistered archetypes had engines shipped WITH
unit tests, deliberately withheld from the registry under a since-superseded policy that required a passing
backtest before registration. The dump under-reported wiring that genuinely existed, which is precisely why
"is it backtested" must never again be inferred from registry absence.

## The five hooks

| Hook                      | Real check reused                                                                                                           | Scope          | Absence means                                                                                                                                                                                                                        |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `engine_factory`          | `factory.ARCHETYPE_ENGINE_REGISTRY` membership + the lazy import actually resolving                                         | mode-invariant | `not_ready` -- no v2 engine class exists; `V2EngineOrchestrator.build()` raises `KeyError` in every mode. EXCEPT for an archetype in `checks.POLICY_EXCLUDED_ARCHETYPES`, which reports `excluded_by_policy` instead -- see below    |
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

`excluded_by_policy` dominates first; then any leg `not_ready` dominates the mode's overall verdict; all-`ready`
legs give `ready`; otherwise (no failures, some `unverified`) the overall is `unverified`. Apart from the
exclusion tier this is readiness-state-dump's `checks.rollup()` policy unchanged.

## `excluded_by_policy` -- a deliberate exclusion is not a gap

`checks.POLICY_EXCLUDED_ARCHETYPES` names archetypes that are permanently and intentionally absent from
`ARCHETYPE_ENGINE_REGISTRY`. Today that is exactly one: **`ARBITRAGE_MEV_SANDWICH`**. Sandwiching extracts value
from other users' pending swaps by front- and back-running them, and the firm does not run it;
`mev/sandwich_theoretical.py` is a post-hoc profit TRACER measuring what a sandwicher would have made against our
OWN flow (an adverse-selection metric), never an execution engine. strategy-service asserts the absence in
`test_sandwich_theoretical.py` and `test_phase8_archetype_factory_smoke.py`.

Such an archetype reports `excluded_by_policy` on EVERY leg, not just `engine_factory` -- its missing schema and
catalog rows are consequences of the decision, not independent findings. Counting them as `not_ready` would leave
a permanently-red row in the matrix and create standing pressure to "finish" it by registering the very thing
policy forbids. So the honest denominator is **59 archetypes in scope, 1 out of scope by decision**.

Adding an entry is a POLICY claim: it needs a cited decision plus an enforcing test in strategy-service. It is
never a way to silence an inconvenient red cell.

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
