---
doc_type: codex-ssot
title: UAC `__init__.py` Lazy-Loading Pattern
summary: >-
  PEP 562 `__getattr__`/`_LAZY_EXPORTS`/`TYPE_CHECKING` pattern for `unified-api-contracts`' aggregator `__init__.py`
  files — preserves every existing public import path with zero breaking changes while cutting fleet-wide import cost.
  Three files converted (`registry/__init__.py`, `internal/architecture_v2/__init__.py`, `internal/__init__.py`,
  ~27% fewer modules on `from unified_api_contracts.internal import X`); the top-level `unified_api_contracts/__init__.py`
  was attempted and reverted after a real silent data-corruption bug, not yet safe to ship. Covers the two subtle
  bugs the conversion hit (submodule-name collision, statement-ordering-before-`__getattr__`) and the convention for
  adding new exports going forward.
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [uac, imports, lazy-loading, pep-562, performance, refactor]
related:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /plans/active/lazy_scoped_loading_refactor_2026_08_16.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
  ]
created: 2026-08-20
authoritative_for:
  [
    PEP-562 lazy-export pattern for UAC's aggregator `__init__.py` files,
    the two conversion pitfalls,
    the top-level file's known-broken state,
  ]
referenced_by: []
owner:
last_reviewed:
code_refs:
  [
    unified-api-contracts/unified_api_contracts/registry/__init__.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/__init__.py,
    unified-api-contracts/unified_api_contracts/internal/__init__.py,
  ]
---

# UAC `__init__.py` Lazy-Loading Pattern

## Why

`unified-api-contracts` is imported by every service in the fleet. Its aggregator `__init__.py` files historically did
`from .X import (A, B, C, ...)` at module top level for every re-exported name — hundreds of names per file, each
eagerly importing its source module the instant ANYTHING from the package is touched. This is the "dominant blocker"
named in `/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`'s Layer 2: fleet-wide blast radius, not just a
local cost — a service that needs one enum pays for every DeFi registry, every archetype schema, every capability
declaration, regardless of what it actually uses.

## The pattern

PEP 562 module-level `__getattr__`/`__dir__`, extending a pattern already hand-written for 6 names in
`registry/__init__.py` before this session (for an unrelated import-cycle reason — see the comment at the top of that
file's `_LAZY_EXPORTS` block):

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .some_submodule import SomeName, OtherName

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "SomeName": (".some_submodule", "SomeName"),
    "OtherName": (".some_submodule", "OtherName"),
}


def __getattr__(name: str) -> object:
    if name in _LAZY_EXPORTS:
        from importlib import import_module
        from typing import cast

        module_name, attr = _LAZY_EXPORTS[name]
        return cast("object", getattr(import_module(module_name, __package__), attr))
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return list(__all__)


__all__ = ["SomeName", "OtherName"]
```

**Every existing public import path keeps working unchanged** — `from unified_api_contracts.internal import
StrategyArchetype`, `import unified_api_contracts.registry`, `unified_api_contracts.registry.some_name` — because
`from X import Y` and `getattr(X, "Y")` both fall back to `X.__getattr__("Y")` when `Y` isn't already bound. This is
the operator-ruled shape (2026-08-20, recorded in the plan above): option (a) lazy submodule attributes, explicitly
NOT (b) explicit-import-plus-deprecation (real fleet-wide breaking churn) or (c) leave-UAC-eager.

## Converted so far

| File                                                         | Lazy exports | Source modules | Shipped                            |
| ------------------------------------------------------------ | -----------: | -------------: | ---------------------------------- |
| `unified_api_contracts/registry/__init__.py`                 |          585 |             62 | `unified-api-contracts@684c6e0e52` |
| `unified_api_contracts/internal/architecture_v2/__init__.py` |          305 |             41 | `unified-api-contracts@34b81221ef` |
| `unified_api_contracts/internal/__init__.py`                 |        1,162 |            165 | `unified-api-contracts@34b81221ef` |

Measured: `from unified_api_contracts.internal import StrategyArchetype` — 1,766 modules/2,209.9ms before, 1,295
modules after (~27% fewer). `registry/__init__.py` alone measured near-zero improvement on its own import, because the
mandatory parent-package chain (`unified_api_contracts/__init__` → `internal/__init__` → `architecture_v2/__init__`)
dominated the cost until those two were also converted — don't trust a single-file measurement in isolation for this
package; the whole ancestor chain has to be lazy before the number moves.

## NOT converted — `unified_api_contracts/__init__.py` (top-level), known broken, do not ship as-is

The top-level package root was converted the same way and reverted. **A real, silent data-corruption bug**: three
module-level registries — `SCENARIO_REGISTRY`, `SYNTHETIC_GENERATOR_REGISTRY`, `SCENARIO_ARCHETYPE_MATRIX` — come
back **empty** through the lazy top-level init, populated correctly through the eager original. Confirmed NOT caused
by the file's own `_VENUES` eager-import loop (disproven: emptying that list entirely, corruption persisted).
Confirmed the three registries populate correctly when their own defining module is reached via the CURRENT (still
eager) top-level `__init__.py`. Root cause not yet isolated — the search space is the ~122 OTHER now-lazy modules in
that file, not the ~37-entry venue list. Full investigation trail:
`/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`'s 2026-08-20 Progress Log entries. **Do not attempt this
file again without reading that trail first** — the `_VENUES` theory is a documented dead end, not a lead.

## Two conversion pitfalls, hit for real, not hypothetical

**1. A name that collides with its own source submodule's leaf name breaks silently.** If module `X.py` defines a
function/class ALSO named `X` (e.g. `expected_coverage.py` defining `def expected_coverage(...)`), importing that
submodule for ANY reason — even to resolve a completely different, unrelated sibling name from the same file —
makes Python's own import machinery bind the SUBMODULE onto the parent package's namespace under that exact name.
Once bound, normal attribute lookup finds the submodule directly and `__getattr__` never fires again for that name —
it's permanently shadowed, not raising, just silently wrong (`type(x) is module`, not the intended function/class).
**Fix**: keep any such name an ordinary eager import instead of routing it through `_LAZY_EXPORTS`. Grep for this
before converting a new file: any `from .X import (..., X, ...)` where the imported name matches the module's own
leaf name.

**2. Live, import-triggering code below the lazy block must be emitted AFTER `__getattr__` exists, not before.** A
manually-inlined computed value (e.g. a Pydantic union type alias built from several imported classes, or an
eager-import loop like `unified_api_contracts/__init__.py`'s `_VENUES` block) can trigger a RE-ENTRANT circular
import back into the package currently mid-initialization. If that live code runs before `__getattr__` is bound on
the module, the re-entrant import has no lazy fallback and fails outright with `ImportError` instead of resolving
correctly. Confirmed via a real case: `execution_service`'s equivalent doesn't apply here, but
`external/databento/databento_classifier.py` does `from unified_api_contracts import UNDERLYING_NORMALIZATION` at
its own module level — reached via the top-level file's `_VENUES` loop — and failed exactly this way until
`__getattr__`'s definition was moved earlier in the generated file, ahead of any preserved live statement.

## Convention going forward

Adding a new public name to any of the three converted files: add it to `_LAZY_EXPORTS` (and the matching
`TYPE_CHECKING` import + `__all__` entry), not a plain top-level `from .X import Y` — reintroducing an eager import
defeats the point incrementally, one addition at a time, with no gate that would catch it. `registry/__init__.py`'s
pre-existing 6-entry `_LAZY_EXPORTS` block (added earlier for an import-cycle reason, unrelated to this session's
work) is the canonical worked example already in the codebase.
