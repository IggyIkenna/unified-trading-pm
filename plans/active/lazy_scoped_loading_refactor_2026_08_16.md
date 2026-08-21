---
doc_type: plan
title: Lazy/scoped loading refactor — strategy-service, UAC, execution-service
summary: >-
  Make archetype/algorithm registration and contract imports lazy and deployment-scoped, so a build loads only what it
  needs. Three layers, ascending cost: strategy-service's factory.py eagerly registers every archetype engine across
  every family; unified-api-contracts' registry/__init__.py (1,270 L) and internal/__init__.py (2,708 L) eagerly import
  ~240k lines on any import, with DeFi content interleaved with CeFi/TradFi/sports in flat enums — the dominant blocker
  and fleet-wide in blast radius; execution-service's algorithms/algorithms.py eagerly imports all 7 algorithms and is
  cheapest, since that repo already has the lazy pattern in adapters/algorithm_factory.py and custody/factory.py. A
  lazy factory.py alone does NOT solve it — live collateral calls still import UAC and pull the whole graph. Carve-out
  prerequisite: land this before or alongside the carve-out so later updates do not re-derive a frozen snapshot against
  a moving, eagerly-coupled target. SIT needs no changes.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy, execution]
repos: [unified-api-contracts, strategy-service, execution-service]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [lazy-loading, import-graph, carve-out-prerequisite, uac, refactor]
priority: P0
source: operator-request-2026-08-16
parent_epic: security_and_cross_cutting_master
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
  ]
created: 2026-08-16
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
estimate_class: refactor
estimate_baseline_ai_days: 8.0
estimate_calibrated_ai_days: 3.2
last_updated: "2026-08-16"
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    unified-api-contracts/unified_api_contracts/registry/__init__.py,
    strategy-service/strategy_service/engine/strategies/v2/factory.py,
    execution-service/execution_service/algorithms/algorithms.py,
  ]
---

# Lazy/scoped loading refactor

> **Parent**: [`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`](/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md)
> (workstream W1). **Referenced by**: carve-out plan §A5 P0 #2.

## Why, in one paragraph

A deployment should load the archetypes and contracts it actually uses. Today a single import pulls the whole graph, so
a scoped build is not scoped in any meaningful sense — which is what makes a carve-out expensive to produce AND
expensive to keep in sync afterwards. Landing this **before** the carve-out means later updates diff against a system
that is already scoped, rather than re-deriving a frozen snapshot against a moving, eagerly-coupled target.

## The three layers, measured

Source: `strategy-service/EXTRACTION_AUDIT.md` was cited as the source (internal audit, 2026-08-15/16) but does not
exist in the repo (working tree or history) — spot-checked independently instead by reading the actual code (see 2026-08-16 Progress Log entry); the numbers below held up.

| Layer                  | What is eager                                                                     | Cost   | Blast radius            |
| ---------------------- | ----------------------------------------------------------------------------------- | ------ | ----------------------- |
| strategy-service       | `factory.py` registers every archetype engine across every family, not just DeFi's  | Medium | This repo               |
| **unified-api-contracts** | `registry/__init__.py` (1,270 L) + `internal/__init__.py` (2,708 L) import ~240k lines; `from unified_api_contracts.internal import StrategyArchetype` pulls the package | **High** | **Fleet-wide**          |
| execution-service      | `algorithms/algorithms.py` imports all 7 algorithm implementations at module level   | Low    | This repo               |

**The trap to avoid**: a fully lazy `factory.py` does not fix the UAC layer. The two real archetypes' live collateral
calls import UAC directly, which loads the full eager graph regardless of strategy-service's own laziness. Doing only
layer 1 and declaring the refactor done would be a measured non-result.

**The cheapest layer first is a legitimate order**: execution-service already has the lazy pattern working in
`adapters/algorithm_factory.py` and `custody/factory.py` — that is a proven local template to copy, not a new design.

**SIT needs no changes.** The audit's § "SIT — no coupling" found `system-integration-tests` never runs strategy-service
in a mode that queries a runtime registry, so a lazy registry is invisible to it.

## Todos

- [x] [AGENT] P0. ✅ **Baseline the import cost before changing anything** — measured in fresh venvs (first import,
      cold `.pyc` cache), `sys.modules` delta + wall time. Full numbers in the 2026-08-16 Progress Log entry below.
- [x] [AGENT] P0. ✅ **Layer 3 (execution-service) first** — execution-service@0576039fa2. Converted both
      `algorithms/algorithms.py` (PEP 562 lazy re-export) AND `execution_service/__init__.py` (package root also
      eagerly re-exported all 7 classes — the real fix needed both files, not just the "smallest change" framing
      originally implied; see the two Progress Log entries above). QG green, functionally verified (registry
      auto-discovers all 7). Measured impact is small (~13% wall-time, noise-level module delta) — the algorithms were
      never the dominant import cost; see Progress Log for the `sys.modules` breakdown pointing at UAC/google/ccxt via
      the still-eager sibling imports in `__init__.py`, out of this todo's scope.
- [x] [AGENT] P0. ✅ **Layer 1 (strategy-service)** — strategy-service@ffa68006da. Operator chose the lazy-values design
      over literal deployment-scoped filtering (see Progress Log design-fork entry): `ARCHETYPE_ENGINE_REGISTRY` keeps
      its full, static 32-archetype key set eager (both coverage gates — schema and clients.yaml — keep working
      completely unchanged, no "assert a positive count" scaffolding needed since the key set is never filtered) but
      resolves each engine class lazily via a `collections.abc.Mapping` subclass. QG green, functionally verified
      (resolving one archetype imports only its own family, none of the other 9). Same caveat as Layer 3: `v2/__init__.py`
      has its own separate, pre-existing eager-import surface unrelated to the 10 family submodules — out of this
      todo's scope, see Progress Log.
- [x] ✅ [OPERATOR] P0. **Ruled 2026-08-20: option (a) — lazy submodule attributes.** Preserve every existing public
      import path exactly (PEP 562 module `__getattr__`, mirroring the pattern already proven in Layers 1 and 3);
      zero breaking changes fleet-wide. Operator explicitly rejected (b) explicit-submodule-import-plus-deprecation
      (real fleet-wide breaking churn) and (c) leave-UAC-eager (the carve-out's scoped-build goal would not
      actually be met).
- [ ] [AGENT] P0. **Layer 2 (UAC) per the ruling** — the dominant blocker. DeFi content is interleaved with
      CeFi/TradFi/sports in flat enums and dicts, so this is not a directory move; it is a genuine restructure. Ship
      behind the fleet's normal gates and expect every dependent repo's gate to be the real test.
      **In progress, 2026-08-20** — three files need this treatment, not one: `registry/__init__.py` (1,300L),
      `internal/architecture_v2/__init__.py` (781L), `internal/__init__.py` (2,733L). `internal/__init__.py`
      re-exports mostly FROM `architecture_v2` (not leaf modules directly), so making it lazy alone accomplishes
      little unless `architecture_v2/__init__.py` is ALSO lazy — Python caches import cost at the MODULE level, so
      touching even one name from an eager `architecture_v2/__init__.py` still executes its entire ~780-line import
      block regardless of `internal/__init__.py`'s own laziness. All three need the fix for it to be real.
      **`registry/__init__.py` — shipped `unified-api-contracts@684c6e0e52`.** Built a mechanical AST-based
      converter (not hand-transcription — 585 re-exported names is exactly the scale a manual pass silently drops
      one from) extending the `_LAZY_EXPORTS` pattern already hand-written in this same file for 6 names
      (client_share_classes/schema_spec/withdrawal_approval_rules, added earlier for an import-cycle reason, not
      this refactor). Verified byte-for-byte correct: captured every one of 585 exported values' `repr()` with
      `PYTHONHASHSEED=0` pinned (unpinned, `frozenset`-valued exports show spurious diffs from per-process hash
      randomization, not real content changes — a trap, not a bug, learned the hard way mid-verification), swapped
      the file, re-captured, diffed sorted — 0 real differences (1 memory-address-in-default-repr artifact,
      expected). basedpyright clean (0 errors), full `quality-gates.sh` green.
      **Two genuine defects found and fixed along the way, not just transcribed faithfully**: (1) a name/submodule
      collision — `expected_coverage` is BOTH a function name AND the leaf name of its own source file
      (`expected_coverage.py`); importing that submodule for ANY reason (even to resolve a sibling symbol) makes
      Python's own import machinery bind the SUBMODULE onto the package namespace under that exact name,
      permanently shadowing the intended function and silently bypassing `__getattr__` (which only fires when
      normal attribute lookup fails) — the ORIGINAL eager file worked by accident (whichever import ran last won);
      the lazy version needed this name kept eager explicitly. Grepped for every other such collision in this file
      (name == own leaf submodule name): exactly one, now fixed. **Re-run this same grep on `architecture_v2` and
      `internal` before trusting either is collision-free** — this is a structural risk in ANY `X.py` module that
      also defines a symbol named `X`, not specific to this one file. (2) A genuinely dead import
      (`get_krx_index_daily_source`, eager-bound in the original but never in `__all__` and never consumed via the
      `registry` package path — confirmed via fleet-wide grep, real consumers already import it from the leaf
      module directly) — dropped rather than carried forward, since basedpyright correctly flags a TYPE_CHECKING
      import with no genuine reference as unused once it can no longer hide behind eager-import silence.
      **Honest measured result — the fix works but its OWN impact is near-zero, matching this plan's own Layer-3
      pattern.** `import unified_api_contracts.registry` before: 1,766 modules / 2,209.9ms. After: 1,730 modules —
      only 36 fewer (~2%). Root cause, isolated by measuring `import unified_api_contracts` ALONE: 1,730 modules,
      identical to the `.registry` figure. **The mandatory parent-package import (`unified_api_contracts/__init__`
      → `internal/__init__` → `architecture_v2/__init__`) is ~100% of the cost** — Python must fully execute a
      package's `__init__.py` before any of its submodules can be reached, so `registry/__init__.py` being lazy
      cannot help until the ancestor chain is lazy too. This is NOT a wasted fix (anyone importing
      `unified_api_contracts.registry.<leaf>` directly still benefits, and the collision/dead-import findings are
      real value), but do not report "Layer 2 done" off this alone — the measurable win is gated on
      `architecture_v2/__init__.py` and `internal/__init__.py` landing.
      **`architecture_v2/__init__.py` — shipped `unified-api-contracts@34b81221ef`.** Same AST converter, extended
      to handle a case `registry/__init__.py` didn't have: a live module-level statement
      (`StrategyInstructionV2 = TradeInstruction | SwapInstruction | ...`, a manually-inlined union type "to avoid
      Pydantic reimport races" per its own comment) that needs its ~13 constituent names as real objects at import
      time, not lazy placeholders — the converter now detects any name referenced by a non-import top-level
      statement and force-imports it eagerly instead, while preserving the statement (and its explanatory comment)
      verbatim in its original form. 305 lazy exports, 41 source modules. Verified: 319/319 `__all__` values
      hash-pinned-repr-identical to the original (0 real diffs), basedpyright 0 errors.
      **`internal/__init__.py` — shipped in the SAME commit, `unified-api-contracts@34b81221ef`.** 1162 lazy exports, 165
      source modules — this is the file that re-exports mostly FROM `architecture_v2` rather than leaf modules
      directly, confirming the earlier concern: it needed `architecture_v2/__init__.py` lazy FIRST for its own
      laziness to mean anything (shipping in the same batch, not sequentially, so neither lands without the other).
      Verified: 1162/1162 values hash-pinned-repr-identical (0 real diffs), basedpyright 0 errors.
      **Measured with all three converted**: `from unified_api_contracts.internal import StrategyArchetype` —
      baseline 1,766 modules/2,209.9ms → now **1,295 modules** (471 fewer, ~27%). Real, not noise — unlike
      `registry/__init__.py` alone.
      **Fourth file discovered, not in the plan's original three-layer table**: `unified_api_contracts/__init__.py`
      itself (the TOP-level package root, 2,712 lines) is ALSO fully eager and is why 1,295 modules remain instead
      of near-zero — confirmed by measuring `import unified_api_contracts` alone: also 1,295 modules, identical to
      the `StrategyArchetype` figure, meaning the top-level package init IS the entire remaining cost. Converted
      the ordinary re-export portion (1098 lazy exports, 122 source modules) but **found something the converter
      cannot safely touch and deliberately did not**: a `for _v in _VENUES: __import__(f"{__name__}.external.{_v}",
      ...); sys.modules[f"{__name__}.{_v}"] = _mod` loop (lines ~2701-2712) that eagerly imports ~37 venue-specific
      `external.*` submodules (alchemy, binance, databento, ibkr, ...) at package-init time, unconditionally,
      explicitly populating `sys.modules[f"{__name__}.{_v}"]` so each is reachable as a top-level
      `unified_api_contracts.<venue>` attribute — a deliberate, non-standard flattening pattern this session does
      not understand the full rationale for (some downstream code plausibly relies on eager `hasattr`/attribute
      presence). Making THIS lazy needs a hand-written `__getattr__` branch that replays the same
      `__import__`+`sys.modules` trick on first access, not the mechanical converter — genuine design work, held
      open rather than guessed. The converter's generic "preserve any non-import statement verbatim" path already
      keeps this loop working exactly as before if/when the rest of the file ships; it is just not yet made lazy.
      **Near-miss during this file's conversion, worth recording**: `typing.cast` and `types.ModuleType` are used
      as REAL runtime calls inside that `_VENUES` loop, not just for type hints — the converter's first version
      blanket-skipped ALL `from typing import ...` statements (assuming typing-only names are never runtime-live),
      which silently dropped `cast` entirely and broke the file (`ruff: F821 Undefined name 'cast'`) — caught by
      the SAME lint-before-ship discipline that caught every other defect this session, not by luck. Fixed: only
      the literal `TYPE_CHECKING` import is special-cased now; every other typing import (or bare `import X`, also
      previously unhandled — `import sys` needed the same fix) flows through the normal
      lazy-unless-referenced-by-a-live-statement path. **Also hit a real infra collision, not a code bug**: editing
      this file WHILE `registry/__init__.py`'s quickmerge was still mid-flight (no `--isolated` flag, so it commits
      from this shared working tree directly) caused quickmerge's own prek-hook safety net to detect the
      concurrently-dirty top-level file and revert it — cleanly, nothing corrupted, matches the KNOWN issue class
      `plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md`. **Lesson**: do
      not edit ANY file in a repo while that repo has a non-`--isolated` quickmerge in flight, even a
      `--files`-scoped one touching a different file — wait for it to land first.
      **Converter script**: promoted to `unified-api-contracts/scripts/lazify_init.py` —
      `unified-api-contracts@c1b4c3cf0a` (2026-08-20, pre-compact sweep) — no longer scratchpad-only; smoke-tested
      against `registry/__init__.py` post-promotion (reproduces
      584 lazy exports / 62 source modules, matching the already-shipped file).
- [ ] [AGENT] P0. **Prove the end state with a scoped-build test** — construct a deployment declaring only
      `CARRY_BASIS_PERP` + `CARRY_STAKED_BASIS` (the contracted archetypes) and assert the loaded-module set excludes
      the families it does not use. This is the test that makes the carve-out's laziness verifiable rather than claimed.
- [x] ✅ [AGENT] P1. **Add a regression guard** — extracted to `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 1 (na-eligibility-audit 2026-08-17). so eager imports cannot creep back — a ratcheted module-count or
      import-graph check, shrink-only in the same sense as the other baselines in this corpus.
- [x] [AGENT] P1. ✅ **Re-measure and record the delta** against the baseline from the first todo, in this plan's Progress
      Log, with the numbers rather than an adjective.

## Progress Log

**2026-08-16 — authored.** Forked from the carve-out plan's §A5 P0 #2 at operator request, so the refactor is
discoverable under its own name rather than buried in a plan titled "carve-out stubbed strategy service" — the biggest
item here (UAC) has fleet-wide blast radius well beyond strategy-service, and someone scanning plan titles for it would
not have found it.

**2026-08-16 — status flipped to active; dead source reference dropped and independently re-verified.** Picking up W1.
`strategy-service/EXTRACTION_AUDIT.md`, cited as this plan's evidentiary source, does not exist anywhere in
strategy-service (working tree or git history — confirmed via full recursive case-insensitive search, not gitignored,
simply never committed). Removed the reference from `context_scope` and the "measured" line above rather than leaving a
dangling pointer. Spot-checked the execution-service claims directly against the code instead: `algorithms/algorithms.py`
has exactly 7 module-level eager imports (adaptive_twap, almgren_chriss, hybrid_optimal, passive_aggressive,
pov_dynamic, twap, vwap) matching the plan's count; `adapters/algorithm_factory.py` uses a real `TYPE_CHECKING`-gated
lazy pattern. Both hold up despite the missing source doc. Have not yet spot-checked the strategy-service `factory.py`
or UAC `registry/__init__.py` / `internal/__init__.py` claims the same way — do that before treating those numbers as
verified, not just plausible.

**2026-08-16 — scoping finding on Layer 3: `algorithms.py` laziness alone is insufficient.**
`execution_service/__init__.py` (the package root) does `from execution_service.algorithms.algorithms import
(AdaptiveTWAPExecAlgorithm, ...)` at its own module level (lines 40-48), re-exporting all 7 classes in its `__all__`.
A `from X import Y` statement resolves `Y` immediately at import time regardless of whether `algorithms.py` itself is
made lazy internally (e.g. via PEP 562 module `__getattr__`) — so `import execution_service` (which anything touching
this package does) still eagerly pulls the full 7-algorithm chain through the package root, independent of what
`algorithms.py` looks like. The real fix needs `execution_service/__init__.py` to also switch to a PEP 562
`__getattr__` re-export (this works for both `import execution_service; execution_service.TWAPExecAlgorithm` AND
`from execution_service import TWAPExecAlgorithm` — the latter falls back to `getattr(package, name)` when the name
isn't already a submodule in `sys.modules`). Zero consumers in execution-service itself do
`from execution_service import <algo>ExecAlgorithm` directly (checked), but this repo's fleet-wide consumers are not
visible from this checkout — editing the package root's public API surface is a bigger, more fleet-facing change than
the todo's "smallest change" framing implied. **Not yet made this edit** — flagging before touching
`execution_service/__init__.py`'s `__all__` surface without fleet-wide consumer visibility.

**2026-08-16 — Layer 3 implemented, and the baseline delta reveals the algorithms were never the dominant cost.**
Operator approved editing the package root despite unverified fleet-wide consumers. Changed:
`execution_service/algorithms/algorithms.py` (PEP 562 `__getattr__`/`__dir__`, `_MODULE_BY_NAME` dispatch table) and
`execution_service/__init__.py` (removed the 7-class eager `from ... import (...)` block, added a matching
`__getattr__` that forwards through the now-lazy `algorithms.algorithms` module). Verified functionally: registry's
`ExecAlgorithmRegistry.list_algorithms()` still discovers all 7 algorithms and resolves classes correctly (its
`inspect.getmembers`-based auto-discovery works because `__dir__` still enumerates `__all__`, and `getattr()` during
discovery is exactly what triggers each lazy load — correct behavior, deferred to first real use of the registry, not
import time).

**But the measured delta is noise-level**: `execution_service.algorithms.algorithms` baseline was
modules_loaded=5911/wall_ms=8890.7; after the fix, modules_loaded=5892/wall_ms=7713.7 — a ~19-module, ~13% wall-time
difference, nowhere near proportional to "7 algorithm implementations no longer eager". Root cause, measured via
`sys.modules` top-level package breakdown after `import execution_service`: `google` (GCP SDK) 1312 modules,
`unified_api_contracts` 903, `ccxt` 632, `unified_trading_library` 360, `execution_service` itself only 323,
`pandas` 295, `nautilus_trader` 203. **The 7 algorithms were never the dominant cost** — `execution_service/__init__.py`
still eagerly imports `config.loader`, `data.catalog`, `data.converter`, `data.loader`, `models`, `results.serializer`,
`algorithms.atomic_bundle_executor` and `algorithms.sor` (unchanged, out of this todo's scope), and one or more of
those pull in the UAC (903 modules — corroborating this plan's own Layer-2 claim independent of the missing audit
file), GCP SDK, and ccxt graphs regardless of algorithm laziness. **This todo is done and correct as scoped** (the 7
algorithm classes are genuinely lazy now, confirmed via `sys.modules` delta immediately after `import
execution_service.algorithms.algorithms` alone — the impl modules do not appear in `sys.modules` until an
algorithm-specific attribute is actually accessed), but "Layer 3 done" does not mean "execution-service import cost
fixed" — that requires tracing which of the still-eager `__init__.py` imports pulls in UAC/google/ccxt, which is
outside Layer 3's stated scope and not attempted here. Quality gates run before shipping; see next entry for result.

**2026-08-16 — Layer 3 shipped.** `bash scripts/quality-gates.sh --no-fix` on execution-service:
`✅ ALL QUALITY GATES PASSED (175s)`, sentinel `.qg_last_passed_sha=306318fd7a3dcdbe9341a319332e6d268a0dae37`, no new
findings introduced (both baselined-warning lines pre-existed, 0 new in each). Shipped via
`quickmerge.sh --agent --files 'execution_service/algorithms/algorithms.py execution_service/__init__.py'` —
**execution-service@0576039fa2**, landed on `live-defi-rollout`, `ahead=0` verified post-push. Unrelated local
`uv.lock` drift (a `google-cloud-monitoring` dependency addition, not from this change) was deliberately left
untouched and unshipped — not mine to stage.

**2026-08-16 — Layer 1 (strategy-service) design fork, resolved with the operator before implementing.**
`factory.py`'s todo said "register only the archetypes a deployment declares," but tracing every real consumer
(`clients_yaml_coverage.py`, `catalog_engine_coverage.py`, `param_schema.py`) showed all three only iterate/`.get()`
`ARCHETYPE_ENGINE_REGISTRY`'s **keys** for full-catalog coverage checks — none require the values (engine classes)
except when resolving one specific archetype. `orchestrator.py` likewise only ever resolves one archetype per
strategy instance via `ArchetypeEngineFactory.build()`. A true deployment-scoped filter (the literal wording) would
need a "declared archetypes for this deployment" input that doesn't exist anywhere in this fan-out, and would force
both coverage gates to distinguish "full catalog" from "this deployment's subset" — bigger and riskier than the todo
implied, mirroring the Layer 3 "smallest fix isn't the real fix" pattern. Operator chose the safer option: keep the
full, static archetype→engine **key** set eager (both coverage gates and `param_schema.py` keep working completely
unchanged), resolve each engine **class** lazily on first access via a `collections.abc.Mapping` subclass
(`_LazyArchetypeEngineRegistry`) backed by a static `archetype -> (module_path, class_name)` table — same shape as
the Layer 3 fix, just as a Mapping object instead of module-level `__getattr__` since `ARCHETYPE_ENGINE_REGISTRY` is
an importable identifier, not a module. `__contains__` is overridden explicitly — the default `Mapping` mixin
implements containment via `__getitem__`, which would silently trigger an import on every `in` check otherwise.

**Verified functionally**: importing `factory.py` alone does not pull in any of the 10 archetype-family submodules
(`arbitrage_structural`, `carry_and_yield`, `defi_lp`, `event_driven`, `market_making`, `mev`, `ml_directional`,
`rules_directional`, `stat_arb_pairs`, `vol_trading`); a plain `in` containment check adds none either; resolving one
archetype (`CARRY_BASIS_PERP`) imports only its own family (`carry_and_yield` + its 12 internal submodules) and none
of the other 9 families. Key-set count unchanged (32, matches original dict exactly — recomputed key-by-key against
the pre-change source, not just counted). **Separate, pre-existing finding, out of this todo's scope**: importing
`strategy_service.engine.strategies.v2.factory` at all first runs `v2/__init__.py` (Python package-import mechanics),
which itself eagerly imports `orchestrator`, `registry`, `batch_harness`, `archetype_build_registry`,
`archetype_slot_resolver`, `slot_label`, `shadow_deployment`, `mode_store`, `dust_router_adapter`,
`leg_controller_adapter`, `strategy_preflight_registry`, and all 5 `archetype_slots_*` modules — none of which are
among the 10 heavy archetype-family packages this todo targeted, so this fix is NOT functionally negated the way the
Layer 3 execution-service fix almost was. But same caveat as Layer 3: "Layer 1 done" does not mean "v2 package import
cost fully fixed" — `v2/__init__.py`'s own eager surface is a distinct, unaddressed concern. Quality gates run before
shipping; see next entry for result.

**2026-08-16 — Layer 1 shipped.** `bash scripts/quality-gates.sh --no-fix` on strategy-service:
`✅ ALL QUALITY GATES PASSED (110s)`, sentinel `.qg_last_passed_sha=3bed3e9bfc3af82d3bc88a5bc007985d1fc6ad83`. A
post-sentinel peripheral-dir ruff warning (28 pre-existing errors in `e2e-testing/scripts/defi/run_dr_drill_cutover.py`,
unrelated unused-noqa/line-length issues) is informational-only — confirmed by the sentinel being written *before* that
check runs, not touched by this change. Shipped via
`quickmerge.sh --agent --files 'strategy_service/engine/strategies/v2/factory.py'` — **strategy-service@ffa68006da**,
landed on `live-defi-rollout`, `ahead=0` verified post-push. First quickmerge invocation misfired against
`deployment-service` (the recurring directory-persistence bug — a bash working-directory leftover from an earlier `cd`
in the session, not an `--files` scoping issue); caught immediately via the printed repo name, no files touched, fixed
by re-running with an explicit `cd strategy-service &&` prefix. Same pre-existing, not-mine `uv.lock` drift as
execution-service left untouched. **W1's Layer 1 and Layer 3 are both done; Layer 2 (UAC) remains blocked on the
open `[OPERATOR]` ruling todo above** — not started, per that todo's explicit gating.

**2026-08-16 — baseline import cost measured (todo 1 done).** Fresh venvs, first import in each process, `sys.modules`
delta + `time.perf_counter()` wall time. Numbers:

| Repo / import                                                 | modules_loaded | wall_ms |
| -------------------------------------------------------------- | -------------: | ------: |
| execution-service `execution_service.algorithms.algorithms`    | 5911            | 8890.7  |
| strategy-service `strategy_service.engine.strategies.v2.factory` | 2900          | 5633.3  |
| UAC `from unified_api_contracts.internal import StrategyArchetype` | 1766        | 2189.0  |
| UAC `import unified_api_contracts.registry`                    | 1766            | 2209.9  |

**Measurement trap — flag, don't reconcile silently.** This inverts the plan's declared Low/Medium/High cost ranking:
execution-service (declared "Low") is both the heaviest and slowest single import measured; UAC (declared "High",
dominant blocker) is the lightest by module count and fastest by wall time. Two things are NOT in tension here even
though the ranking looks backwards: (1) `modules_loaded` counts imported modules, not lines-per-module — UAC's
~240k-line claim is a parse-cost/LOC metric, a large `internal/__init__.py` still counts as one module in this metric,
so this baseline doesn't measure the same axis the plan's qualitative claim was making; (2) execution-service's own
heavy transitive deps (boto3, ccxt, twisted — seen in its factory.py neighbors during file search) are very plausibly
what's driving its number, unrelated to the 7-algorithm eager-import problem this plan is actually about. **UAC's
fleet-wide blast-radius argument (every consumer pays its cost, not that its own import is the single heaviest) is
unaffected by this** — but the Low/Medium/High labels in the "three layers, measured" table above should not be read
as wall-clock-ranked without this caveat. Not re-deriving the labels here; leaving this for whoever tackles Layer 2 to
weigh, since UAC's actual fix (todo "Layer 2 (UAC) per the ruling") is gated on the pending `[OPERATOR]` ruling anyway.

**2026-08-16 — post-fix delta re-measured (todo "Re-measure and record the delta" done).** Same two imports as the
baseline, run against the current checkouts (both fixes already shipped and on `live-defi-rollout`). **Methodology
deviation, flagged not hidden**: the baseline was measured with a cold `.pyc` cache; this re-measurement is warm-cache
— `find -exec rm -rf` to clear `__pycache__` is blocked outright by this workspace's destructive-command guardrail
(`block_destructive_commands.py`), and there is no non-recursive substitute for a directory tree of cache files. Module
count does not depend on cache state (the same modules import either way); wall time does, so the wall-time deltas
below are directionally suggestive only, not baseline-comparable.

| Repo / import | baseline modules | after modules | baseline wall_ms | after wall_ms (warm cache) |
| --- | ---: | ---: | ---: | ---: |
| execution-service `execution_service.algorithms.algorithms` | 5911 | **5929** | 8890.7 | 13148.2 |
| strategy-service `strategy_service.engine.strategies.v2.factory` | 2900 | **2850** | 5633.3 | 4161.1 |

**strategy-service (Layer 1) shows the expected direction**: -50 modules, and wall time down too despite the warm-cache
skew working against a clean read (config/logging setup on the execution-service run alone printed to stdout, showing
these processes carry real side effects, not pure import-graph measurement).

**execution-service (Layer 3) is higher than its own baseline, not lower — flag, don't reconcile silently.** 5929 is
also higher than the 5892 figure already recorded in the Layer-3-implemented entry above, measured on this same
checkout closer to ship time. The 7-algorithm eager-import fix itself is not in question — that was independently
verified via direct `sys.modules` inspection immediately after the narrower `algorithms.algorithms`-only import in the
Layer 3 entry, confirming the impl modules are genuinely absent until first access. The most plausible explanation for
the higher total now is the pre-existing, not-mine `uv.lock` drift noted at Layer 3 ship time (a `google-cloud-monitoring`
dependency addition, left untouched and unshipped) — if that dependency has since been installed into this `.venv`
between measurements, its transitive import graph would inflate `len(sys.modules)` independent of anything this plan
changed. **Confirmed 2026-08-16 (later same day)**: `git diff uv.lock` in both `execution-service` and `strategy-service`
shows the identical uncommitted 18-line addition — `google-cloud-monitoring==2.31.0` plus its transitive deps
(`grpcio`, `proto-plus`, `protobuf`, `google-api-core[grpc]`, `google-auth`) — locked but not shipped in either repo.
This is the causal mechanism, not just a plausible guess: that dependency's transitive import graph, if resolved into
this `.venv`, inflates `len(sys.modules)` on any import of an execution-service module regardless of this plan's fix.
It is pre-existing, not-mine, uncommitted `uv.lock` drift (workspace `dirty-deps` carve-out — not committed as part of
this doc-only todo). Recorded as a measurement trap for whoever next touches execution-service import cost: re-baseline
against a `.venv` without this pending lock change, not silently smoothed into a false "the fix worked, numbers went
down" narrative.
- **na-eligibility-audit 2026-08-17** [body-hash:113cba0b6fa4629e]: RECLASSIFY (per-todo split) -- extracted the 1 bounded item (regression guard for eager imports) to cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md item 1. Doc stays assigned_vm: NA for its other genuinely operator-gated/design items (the layer-2 UAC restructure needs an operator ruling on scope first). Cross-cutting tranche audit.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries) — added the 3 source paths named in the doc's own three-layer summary (UAC registry/__init__.py, strategy-service's archetype factory, execution-service's algorithms.py); was codex+plan-only before.
- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
- **2026-08-20 — the 4th file (top-level `unified_api_contracts/__init__.py`) attempted, then DELIBERATELY REVERTED — a
  real silent-corruption bug found, not shipped.** Converted the file's ~1,098 ordinary re-exports mechanically (same
  proven approach as the other three), kept its `_VENUES` eager-import loop (lines ~2701-2712, see the earlier entry)
  untouched/preserved verbatim since it needs hand-written design, not the mechanical converter. Passed lint,
  basedpyright (0 errors after two real fixes — see below), and looked ready. **The exhaustive hash-pinned-repr
  correctness sweep (the same method that verified all three shipped files clean) caught a genuine data-corruption
  bug the type checker and linter both missed**: three registries — `SCENARIO_REGISTRY`
  (`canonical/crosscutting/scenario_overlay/`, 13 entries), `SYNTHETIC_GENERATOR_REGISTRY`
  (`canonical/crosscutting/synthetic_generator.py`, 13 entries), `SCENARIO_ARCHETYPE_MATRIX`
  (`registry/scenario_archetype_matrix.py`'s `MATRIX`, aliased) — all come back **EMPTY** through the lazy top-level
  `__init__.py`, populated correctly through the original eager one. Diffed against the FULL 1,099-name `__all__` set,
  hash-pinned; these were the only 3 names affected — not a sample, the complete list.
  **Root cause narrowed to the `_VENUES` loop specifically, not the mechanical conversion itself**: all three
  registries populate CORRECTLY when their own defining module is imported in complete isolation (verified directly —
  `import unified_api_contracts.canonical.crosscutting.scenario_overlay as m; len(m.SCENARIO_REGISTRY)` → 13, fresh
  process, no other `unified_api_contracts` state loaded first). But once the LAZY top-level `__init__.py` runs first
  (which now includes the same `_VENUES` loop, unchanged, importing ~37 `external.*` venue submodules) and you THEN
  import the SAME registry submodule DIRECTLY (bypassing `__getattr__`/`_LAZY_EXPORTS` entirely — same `sys.modules`
  cache, same object) — it comes back empty. Confirmed the returned object is the identical (`is`) instance
  `unified_api_contracts.__getattr__` would hand back, ruling out a dispatch-table bug in the converter itself. **The
  `_VENUES` loop's eager import of ~37 external venue modules — at a point in package-init where the rest of the
  eager graph is no longer present to backstop it — silently leaves at least these 3 registries mid-populated or
  reset**, most plausibly because one or more of those 37 external modules transitively imports one of these three
  registry modules EARLY (before some other prerequisite it depends on is available in the now-mostly-lazy world),
  and Python's `sys.modules` caching means that first, incomplete run sticks for the rest of the process — this part
  is a strong hypothesis, not confirmed to the exact external module; not chased further given time already spent.
  **Two real, independent bugs also found and fixed in the converter itself while getting this far** (both now fixed
  in `lazify_init.py` for future files, even though this file's ship was reverted): (1) a bare `import sys` statement
  got emitted TWICE — once via the general bare-import handling, once again because the `other_statements` collector
  didn't exclude `ast.Import` nodes (only `ast.ImportFrom`) from its "preserve any other top-level statement" sweep;
  (2) `other_statements` (which can contain LIVE, import-triggering code like the `_VENUES` loop) was originally
  emitted BEFORE `__getattr__`/`_LAZY_EXPORTS` were defined in the generated file — meaning a re-entrant circular
  import triggered by that live code (confirmed: `external/databento/databento_classifier.py` does
  `from unified_api_contracts import UNDERLYING_NORMALIZATION` at its own module level) had no lazy fallback to catch
  it and failed outright with `ImportError`. Fixed by moving `other_statements` to emit AFTER `__getattr__` exists.
  **Verdict: reverted `unified_api_contracts/__init__.py` to the clean original — confirmed via `git status
  --porcelain` (empty) and a direct diff against the pre-session backup (byte-identical).** This file needs someone
  to trace the EXACT external module responsible before it can ship safely — silently returning an empty registry in
  production (rather than crashing loudly) is a genuinely dangerous failure mode for whatever consumes these three,
  and this session will not guess which of the 37 external modules it is under time pressure. **Recommended next
  step**: bisect the `_VENUES` list (comment out half, re-run the same hash-pinned diff, repeat) rather than reading
  all 37 external modules' import graphs by hand.
  **What DID ship and stands independently of this**: `registry/__init__.py` (`unified-api-contracts@684c6e0e52`),
  `architecture_v2/__init__.py` + `internal/__init__.py` (`unified-api-contracts@34b81221ef`) — none of the three
  touch the `_VENUES` loop or its 37 external modules, so none carry this risk. The measured 27% import-cost
  reduction already reported is real and already landed; only the 4th file's OWN portion remains undone.
  **Converter script** (fixed, both bugs above patched): promoted to `unified-api-contracts/scripts/lazify_init.py`
  — `unified-api-contracts@c1b4c3cf0a` (2026-08-20) — no longer scratchpad-only, both fixes are baked into the
  committed version.
- **2026-08-20, later same day — correction to the entry above: the `_VENUES` hypothesis was WRONG, and (the
  important part) the already-shipped code is confirmed NOT affected.** Bisected properly instead of assuming:
  patched the reverted lazy top-level `__init__.py` to `_VENUES: list[str] = []` (zero external modules imported at
  all) and re-ran the same check — **still corrupt, all 3 registries still empty.** This flatly disproves the
  `_VENUES`-loop theory from the entry above; the real cause is somewhere among the ~1,098 OTHER now-lazy names in
  this same file, not the 37-entry venue list. Recommended next step in the prior entry (bisect `_VENUES`) is
  therefore WRONG — do not follow it; whoever picks this up needs to bisect across the ~122 source modules the
  ordinary lazy exports touch instead, which is a materially bigger search.
  **The one thing this DID settle, decisively**: re-ran the identical check against the CURRENTLY-SHIPPED tree
  (`git status --porcelain` empty, `ahead=0 behind=0` against origin — i.e. `registry/__init__.py` +
  `architecture_v2/__init__.py` + `internal/__init__.py` lazy, top-level `unified_api_contracts/__init__.py` still
  the ORIGINAL eager one) — `SCENARIO_REGISTRY`=13, `SYNTHETIC_GENERATOR_REGISTRY`=13,
  `SCENARIO_ARCHETYPE_MATRIX`=19 entries total, all correct. **The bug is confined entirely to the reverted,
  unshipped 4th file — the three already-landed commits carry zero risk of this.** Worth stating plainly since the
  prior entry's wording could be read as "something is currently broken" — nothing is; this was caught before
  shipping, which is the system working as intended, not an incident.
  **Also corrects a methodology error in the prior entry's "isolated import" tests**: those ran
  `import unified_api_contracts.canonical.crosscutting.scenario_overlay` directly, but Python mandatorily runs the
  PARENT package's `__init__.py` first regardless — those tests were executed AFTER the top-level file had already
  been reverted to the eager original, so they were silently testing "reached via the eager original," not
  "reached via nothing." There is no way to import a submodule of `unified_api_contracts` without its top-level
  `__init__.py` running first; any future bisection needs to control for that, not assume isolation is possible.
  Not pursued further this tick — the search space is now known to be much larger than one 37-entry list, and
  finding the real culprit warrants its own dedicated pass, not a quick follow-up.
- **2026-08-20 — post-phase codex audit: stubbed the new pattern.** This whole effort had no codex SSOT — the
  pattern, the two conversion pitfalls, and the top-level file's known-broken state all lived only in this plan's
  Progress Log, which archives when the plan does. Wrote
  `/codex/06-coding-standards/uac-init-lazy-loading-pattern.md` covering the `_LAZY_EXPORTS`/`__getattr__`/
  `TYPE_CHECKING` pattern itself, the shipped-file table with shas, the top-level file's do-not-retry-without-
  reading-this warning, both real bugs found (submodule-name collision, statement-ordering-before-`__getattr__`),
  and the going-forward convention for adding new exports. Anyone picking up the top-level file next should start
  there, not re-read this entire plan.
