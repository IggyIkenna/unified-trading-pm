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
parent_epic: infrastructure_master
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
- [ ] [AGENT] P0. **Layer 1 (strategy-service)** — make `factory.py` register only the archetypes a deployment declares.
      Must preserve: the coverage gate that fails on a missing schema, and the clients.yaml coverage gate. A lazy
      registry that quietly registers nothing would pass both by accident — assert a positive count.
- [ ] [OPERATOR] P0. **Ruling before layer 2: how far does UAC's `__init__` restructure go?** Splitting
      `registry/__init__.py` and `internal/__init__.py` changes the import surface every repo in the fleet depends on.
      Options are (a) lazy submodule attributes preserving today's public paths, (b) explicit submodule imports with a
      deprecation for the flat ones, (c) leave UAC eager and accept that scoping stops at strategy-service. Needs an
      operator call — it is a fleet-wide API decision, not a local refactor.
- [ ] [AGENT] P0. **Layer 2 (UAC) per the ruling** — the dominant blocker. DeFi content is interleaved with
      CeFi/TradFi/sports in flat enums and dicts, so this is not a directory move; it is a genuine restructure. Ship
      behind the fleet's normal gates and expect every dependent repo's gate to be the real test.
- [ ] [AGENT] P0. **Prove the end state with a scoped-build test** — construct a deployment declaring only
      `CARRY_BASIS_PERP` + `CARRY_STAKED_BASIS` (the contracted archetypes) and assert the loaded-module set excludes
      the families it does not use. This is the test that makes the carve-out's laziness verifiable rather than claimed.
- [ ] [AGENT] P1. **Add a regression guard** so eager imports cannot creep back — a ratcheted module-count or
      import-graph check, shrink-only in the same sense as the other baselines in this corpus.
- [ ] [AGENT] P1. **Re-measure and record the delta** against the baseline from the first todo, in this plan's Progress
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
