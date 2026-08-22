#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Fleet sweep: fail when a connector/handler/router class in a covered set has zero
production callers.

Origin: `plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md` — the recurring
defect class across three sessions where "something real is built, tested and complete,
and nothing on a production path can reach it." Measured instances: `GenericTokenBalanceAdapter`
(fixed), 24 plan-hygiene tests (fixed — see `check_pytest_unit_dir_coverage.py`),
`EnhancedAlphaComparator`, Marinade/Kamino/Jupiter connectors, `V2InstructionRouter`,
`DefiAdapter` (both since deleted/rewired, `execution-service@37bfaeed0b`) — a component
survives every review that asks "does this work?" because the honest answer is yes; the
question that fails is "does anything call it?" (measured 2026-08-15: 27 of
execution-service's 33 DeFi protocol connector classes have zero production callers). That
issue doc's own todo: "Add a reachability gate ... this defect class has recurred six/seven
times; a detector is worth more than seven fixes." This is that detector.

**Two "covered set" shapes, because the fleet has both** (measured 2026-08-15 — see
`unified_api_contracts` invariant 3's `test_execution_service_venue_coverage_cascade_
invariant.py` for the narrowest single-purpose version of this same idea):

- **census mode**: no registry exists at all (execution-service's DeFi protocol connectors
  — confirmed via grep, no `PROTOCOL_REGISTRY`/`CONNECTOR_REGISTRY` anywhere, and the
  package's own `__all__` re-export list is incomplete, missing 9 of 33 real connector
  classes). The covered set is every concrete class in a directory that subclasses one of
  a given set of base classes.
- **registry mode**: an explicit `dict[key, type[...]]` literal names every "covered" class
  (e.g. market-tick-data-service's `VENUE_REGISTRY`, strategy-service's
  `ARCHETYPE_ENGINE_REGISTRY` / `STRATEGY_CLOSE_ALL_REGISTRY`). The covered set is every
  class NAME referenced as (or inside a tuple/list) dict value.

Both modes reduce to the same reachability question once the covered set is known: is this
class NAME (following import aliases — a re-export or aliased import is NOT a caller, a
docstring mention is NOT a caller) ever the target of a real `ClassName(...)` call anywhere
in the repo OUTSIDE the class's own defining location and any test file? Static AST
analysis only — this only runs where a target's OWN repo is present as `--workspace-root`.

**Shrinking-ratchet baseline, name-set not count** (`reachability_gate_baseline.json`,
sibling to this file) — unlike `check_pytest_unit_dir_coverage.py`'s count-only baseline,
this stores the actual TOLERATED class names per target, so swapping one gap for a
different one still fails (a count-only baseline would let that through). Measured
2026-08-15: 27 pre-existing execution-service DeFi connectors are baselined; wiring this in
as an unconditional assertion would fail immediately on that backlog (tracked by the origin
issue doc's P0 "re-derive the execute-side tier table on caller-graph reachability" todo).
A NEW unreachable class beyond the baseline fails; a class going from unreachable to
reachable (or DELETED as dead code, `V2InstructionRouter`'s resolution) must be removed
from the baseline in the same change — baselines only ratchet down.

Usage::

    # fleet sweep — checks every configured TARGET against --workspace-root:
    python check_reachability_gate.py --workspace-root <ws>

    # ratchet the baseline DOWN after wiring/deleting an unreachable class:
    python check_reachability_gate.py --workspace-root <ws> --update-baseline

Exit codes: 0 = at-or-below baseline; 1 = new unreachable class/classes or stale baseline
entries; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

#: Dirs never searched for a caller, regardless of target (build/venv/cache noise — same
#: convention as check_pytest_unit_dir_coverage.py's _EXCLUDED_DIR_NAMES).
_EXCLUDED_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".venv",
        ".venv-workspace",
        "venv",
        "node_modules",
        "build",
        "dist",
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "htmlcov",
        ".tox",
        "site-packages",
    }
)


@dataclass(frozen=True)
class ReachabilityTarget:
    """One "covered set" to check for production reachability within one repo.

    `mode="census"`: `census_dir` is scanned for classes directly subclassing one of
    `base_class_names` (excluding `exclude_class_names` — the base/ABC classes themselves).
    `mode="registry"`: `registry_file`'s top-level `registry_var` dict literal's values
    (or tuple/list elements within a value) name the covered classes.

    `search_root` is where callers are looked for; `exclude_prefixes` are repo-relative
    directory prefixes never searched (always includes the covered set's own defining
    location — a class "calling itself" in its own module proves nothing).
    """

    key: str
    repo: str
    mode: str  # "census" | "registry"
    search_root: str
    exclude_prefixes: tuple[str, ...] = ()
    census_dir: str = ""
    base_class_names: tuple[str, ...] = ()
    exclude_class_names: frozenset[str] = frozenset()
    registry_file: str = ""
    registry_var: str = ""


#: Configured targets — each measured end-to-end before being added (2026-08-15). The
#: features-service per-domain `*_REGISTRY`/`HANDLER_REGISTRY` family
#: (`commodity/adapters`, `commodity/engine/factors`, `onchain`/`volatility`/`sports`/
#: `delta_one`/`cross_instrument`/`multi_timeframe` CLI handler maps) is the natural next
#: batch of registry-mode targets — add once each is measured, not speculatively.
TARGETS: Final[tuple[ReachabilityTarget, ...]] = (
    ReachabilityTarget(
        key="execution-service:defi_protocols",
        repo="execution-service",
        mode="census",
        census_dir="execution_service/defi_execution/protocols",
        base_class_names=("BaseConnector", "BaseSolanaConnector", "BaseBridgeConnector"),
        exclude_class_names=frozenset({"BaseConnector", "BaseSolanaConnector", "BaseBridgeConnector"}),
        search_root="execution_service",
        exclude_prefixes=("execution_service/defi_execution/protocols",),
    ),
    # "the single source of truth for supported venues" (factory.py's own comment) — CeFi
    # (7) + TradFi (7) + DeFi (27) + onchain perps (2) + prediction markets (2) + sports
    # (2) adapter classes, one dict keyed by venue name, values `(category, adapter_class)`.
    ReachabilityTarget(
        key="market-tick-data-service:venue_registry",
        repo="market-tick-data-service",
        mode="registry",
        registry_file="market_tick_data_service/market_interface/factory.py",
        registry_var="VENUE_REGISTRY",
        search_root="market_tick_data_service",
    ),
    # One engine class per v2 strategy archetype — "the orchestrator's single lookup point
    # keyed by StrategyArchetype enum value" (factory.py's own docstring).
    ReachabilityTarget(
        key="strategy-service:archetype_engine_registry",
        repo="strategy-service",
        mode="registry",
        registry_file="strategy_service/engine/strategies/v2/factory.py",
        registry_var="ARCHETYPE_ENGINE_REGISTRY",
        search_root="strategy_service",
    ),
    # One close-all script per strategy_id — directly relevant to
    # e2e_wiring_reachability_audit_2026_08_15.md FINDING 1 (the emergency close-all path
    # targeting a non-existent execution-service endpoint): a registry entry with no real
    # caller into execution-service is the same defect class one level up the call chain.
    ReachabilityTarget(
        key="strategy-service:close_all_registry",
        repo="strategy-service",
        mode="registry",
        registry_file="strategy_service/close_all/__init__.py",
        registry_var="STRATEGY_CLOSE_ALL_REGISTRY",
        search_root="strategy_service",
    ),
)


# ── Covered-set derivation ──────────────────────────────────────────────────


def _collect_dict_value_names(node: ast.expr) -> set[str]:
    """Class-name references inside a registry dict value: a bare `Name`, or a
    `Tuple`/`List` containing one (MTDS's `VENUE_REGISTRY` values are `(category, cls)`).
    """
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for elt in node.elts:
            names |= _collect_dict_value_names(elt)
        return names
    return set()


def census_classes(repo_root: Path, target: ReachabilityTarget) -> dict[str, str]:
    """`{class_name: defining_file_relpath}` for every class in `target.census_dir`
    directly subclassing one of `target.base_class_names`, excluding
    `target.exclude_class_names`.
    """
    out: dict[str, str] = {}
    census_root = repo_root / target.census_dir
    if not census_root.is_dir():
        return out
    for source_file in sorted(census_root.glob("*.py")):
        try:
            tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        except SyntaxError:
            continue
        rel = source_file.relative_to(repo_root).as_posix()
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or node.name in target.exclude_class_names:
                continue
            base_names = {b.id for b in node.bases if isinstance(b, ast.Name)}
            if base_names & set(target.base_class_names):
                out[node.name] = rel
    return out


def registry_classes(repo_root: Path, target: ReachabilityTarget) -> dict[str, str]:
    """`{class_name: defining_file_relpath}` for every class NAME referenced as (or inside)
    a value of the top-level dict literal assigned to `target.registry_var` in
    `target.registry_file`.
    """
    out: dict[str, str] = {}
    registry_path = repo_root / target.registry_file
    if not registry_path.is_file():
        return out
    tree = ast.parse(registry_path.read_text(encoding="utf-8"), filename=str(registry_path))
    rel = registry_path.relative_to(repo_root).as_posix()
    for node in ast.walk(tree):
        targets_: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets_ = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and node.target is not None:
            targets_ = [node.target]
        else:
            continue
        if not any(isinstance(t, ast.Name) and t.id == target.registry_var for t in targets_):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        for value in node.value.values:
            for name in _collect_dict_value_names(value):
                out[name] = rel
    return out


def covered_classes(repo_root: Path, target: ReachabilityTarget) -> dict[str, str]:
    if target.mode == "census":
        return census_classes(repo_root, target)
    if target.mode == "registry":
        return registry_classes(repo_root, target)
    raise ValueError(f"unknown ReachabilityTarget.mode: {target.mode!r}")


# ── Reachability — does anything outside the defining location instantiate it? ─────────


def resolve_import_aliases(tree: ast.Module, class_name: str) -> set[str]:
    """Local names `class_name` might be imported as in `tree` (`from x import Y as Z`)."""
    aliases = {class_name}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == class_name:
                    aliases.add(alias.asname or alias.name)
    return aliases


def source_instantiates_any(tree: ast.Module, aliases: set[str]) -> bool:
    """True if `tree` calls `Name(...)` for any name in `aliases` — a real construction,
    not an import, a re-export, or a docstring/comment mention (AST `Call` nodes only)."""
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in aliases
        for node in ast.walk(tree)
    )


def registry_uses_dynamic_dispatch(repo_root: Path, target: ReachabilityTarget) -> bool:
    """True if `target.registry_var` is ever subscripted (`REGISTRY[key]`) or `.get(...)`-ed
    anywhere under `target.search_root` — evidence the registry is looked up BY KEY and its
    value called/returned dynamically, never via a literal `SomeClass(...)` call per entry.

    When true, a per-entry "is ClassName(...) ever called by its literal name" check measures
    the WRONG property: it reports near-total false "unreachable" for a correctly-used
    registry, because the whole point of a registry is to avoid hand-writing one named call
    site per entry. Measured 2026-08-15 building this checker: market-tick-data-service's
    `VENUE_REGISTRY` scored 40/40 "unreachable" and strategy-service's
    `ARCHETYPE_ENGINE_REGISTRY` scored 28/30 — both are dynamic-dispatch in reality
    (`factory.py`'s own `adapter_class(chain=chain, **kwargs)` / `ARCHETYPE_ENGINE_REGISTRY
    [archetype]`, plus an external `.get()` call site in `catalog_engine_coverage.py`) with a
    real, present production caller on the dispatching accessor (`get_adapter()` is called
    from `api.py`/`umi_tick_provider.py`) — the naive check just cannot see a call made
    through a variable instead of a literal name. A dynamic-dispatch target is reported
    informationally and NOT per-entry baselined — silently seeding a fabricated 40/40 count
    would be worse than not checking at all. Distinguishing this from a genuinely dead
    registry matters: `STRATEGY_CLOSE_ALL_REGISTRY` (measured same session) has NO subscript/
    `.get()` site anywhere outside its own defining file — that one gets the real per-entry
    check, and its 2/2 result is a genuine finding, not a false positive.
    """
    root = repo_root / target.search_root
    if not root.is_dir():
        return False
    for source_file in root.rglob("*.py"):
        rel_parts = source_file.relative_to(repo_root).parts
        if any(part.startswith(".") or part in _EXCLUDED_DIR_NAMES for part in rel_parts[:-1]):
            continue
        try:
            tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            base: ast.expr | None = None
            if isinstance(node, ast.Subscript):
                base = node.value
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                base = node.func.value
            if isinstance(base, ast.Name) and base.id == target.registry_var:
                return True
    return False


def _is_excluded(rel_path_parts: tuple[str, ...], file_name: str, exclude_prefixes: tuple[str, ...]) -> bool:
    rel_posix = "/".join(rel_path_parts)
    if any(rel_posix == p or rel_posix.startswith(p + "/") for p in exclude_prefixes):
        return True
    if any(part.startswith(".") or part in _EXCLUDED_DIR_NAMES or part == "tests" for part in rel_path_parts[:-1]):
        return True
    return file_name.startswith("test_")


def class_is_reachable(repo_root: Path, class_name: str, search_root: str, exclude_prefixes: tuple[str, ...]) -> bool:
    """True if `class_name` is instantiated anywhere under `search_root`, outside
    `exclude_prefixes` and any `tests/`/`test_*.py` location.
    """
    root = repo_root / search_root
    if not root.is_dir():
        return False
    for source_file in root.rglob("*.py"):
        rel_parts = source_file.relative_to(repo_root).parts
        if _is_excluded(rel_parts, source_file.name, exclude_prefixes):
            continue
        try:
            tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        except SyntaxError:
            continue
        aliases = resolve_import_aliases(tree, class_name)
        if source_instantiates_any(tree, aliases):
            return True
    return False


def unreachable_classes(repo_root: Path, target: ReachabilityTarget) -> set[str] | None:
    """Covered class names with zero reachable production caller, or `None` if
    `target` is a dynamic-dispatch registry (see `registry_uses_dynamic_dispatch` — a
    per-entry named-call check is the wrong property for those, so they are reported
    informationally instead of fabricating a baseline from a known-wrong measurement).

    Every class's OWN defining/registry file is excluded per-entry (in addition to
    `target.exclude_prefixes`) — census mode's `covered_classes()` already returns the
    class's real defining file (one directory, `census_dir`, covers every entry, so
    `exclude_prefixes` alone is equivalent there); registry mode returns the REGISTRY
    file (the classes themselves are scattered across many sibling modules a blanket
    directory exclusion would wrongly hide as a valid caller-search space — e.g.
    strategy-service's `ARCHETYPE_ENGINE_REGISTRY` imports 20+ engine classes from
    across `engine/strategies/v2/*`, and a real dispatcher calling one FROM a sibling
    engine module must still count).
    """
    if target.mode == "registry" and registry_uses_dynamic_dispatch(repo_root, target):
        return None
    covered = covered_classes(repo_root, target)
    target_prefixes = set(target.exclude_prefixes)
    if target.mode == "census" and not target_prefixes:
        target_prefixes = {target.census_dir}  # fallback: census_dir always excludable as a whole
    unreachable: set[str] = set()
    for name, defining_file in covered.items():
        exclude = tuple(target_prefixes | {defining_file})
        if not class_is_reachable(repo_root, name, target.search_root, exclude):
            unreachable.add(name)
    return unreachable


# ── Baseline (shrinking ratchet, per target — NAME SET, not count) ─────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "reachability_gate_baseline.json"


@dataclass(frozen=True)
class Baseline:
    tolerated: dict[str, set[str]] = field(default_factory=dict)

    def allowed(self, target_key: str) -> set[str]:
        return self.tolerated.get(target_key, set())


def load_baseline(path: Path | None = None) -> Baseline:
    baseline_file = path if path is not None else _baseline_path()
    if not baseline_file.exists():
        return Baseline()
    raw = json.loads(baseline_file.read_text(encoding="utf-8"))
    targets_raw = raw.get("targets") or {}
    tolerated = {key: set(names) for key, names in targets_raw.items()}
    return Baseline(tolerated=tolerated)


def write_baseline(observed: dict[str, set[str]], existing: Baseline, path: Path | None = None) -> None:
    """Persist a new baseline. Unlike check_pytest_unit_dir_coverage.py's count clamp, this
    writes the OBSERVED set verbatim for every target actually scanned this run — a
    deliberate `--update-baseline` invocation is the reviewed act (same convention as that
    checker's own module docstring: "re-run the measurement and review the diff" is the
    only legitimate way to grow a ratchet baseline); unscanned targets are carried forward
    untouched, same as the count-based checker.
    """
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, list[str]] = {}
    for key in sorted(set(observed) | set(existing.tolerated)):
        names = observed[key] if key in observed else existing.allowed(key)
        merged[key] = sorted(names)
    payload = {
        "_comment": (
            "Shrinking-ratchet baseline for the reachability gate (check_reachability_gate.py). "
            "targets[<key>] is the exact set of class names tolerated as unreachable for that "
            "ReachabilityTarget. NEVER hand-add a name here to silence a failure -- either wire "
            "the class into a real production caller, delete it as confirmed dead code (the "
            "V2InstructionRouter resolution), or re-run --update-baseline after reviewing why the "
            "new name is a deliberate, tracked gap. SSOT: "
            "plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md."
        ),
        "targets": merged,
    }
    _ = baseline_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reachability gate (shrinking-ratchet, name-set baseline).")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed unreachable-class sets.",
    )
    parser.add_argument("--baseline-file", type=Path, default=None, help="Override the baseline json path.")
    args = parser.parse_args(argv)

    workspace_root: Path = args.workspace_root.resolve()
    baseline_file: Path | None = args.baseline_file
    baseline = load_baseline(baseline_file)

    observed: dict[str, set[str]] = {}
    failures: list[str] = []
    info_lines: list[str] = []
    for target in TARGETS:
        repo_root = workspace_root / target.repo
        if not repo_root.is_dir():
            continue
        unreachable = unreachable_classes(repo_root, target)
        if unreachable is None:
            info_lines.append(
                f"[SKIP] {target.key}: dynamic-dispatch registry (REGISTRY[key]/.get() call site found) — "
                "per-entry named-call check would be a known-wrong measurement, not checked"
            )
            continue
        observed[target.key] = unreachable
        allowed = baseline.allowed(target.key)

        new_regressions = sorted(unreachable - allowed)
        stale_entries = sorted(allowed - unreachable)
        if new_regressions:
            failures.append(
                f"[FAIL] {target.key}: {len(new_regressions)} NEW unreachable class(es) beyond baseline: "
                f"{', '.join(new_regressions)}"
            )
        if stale_entries:
            failures.append(
                f"[FAIL] {target.key}: {len(stale_entries)} baselined class(es) are now reachable and must be "
                f"removed from the baseline (ratchet only shrinks): {', '.join(stale_entries)}"
            )
        if not new_regressions and not stale_entries:
            info_lines.append(f"[OK]   {target.key}: {len(unreachable)} unreachable (== baseline)")

    if args.update_baseline:
        write_baseline(observed, baseline, baseline_file)
        print(f"[check_reachability_gate] baseline updated at {baseline_file or _baseline_path()}")
        for key in sorted(observed):
            print(f"  {key}: {len(observed[key])} unreachable")
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n→ A class in a covered set (registry entry, or a directory census of a common base class) has no "
            "production caller — it is built and tested but nothing on a live path can reach it. Wire it into a "
            "real dispatcher/handler, delete it as confirmed dead code, or add it to "
            "unified-trading-pm/scripts/quality_gates/reachability_gate_baseline.json with a note (NEVER raise "
            "tolerance silently). SSOT: plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
