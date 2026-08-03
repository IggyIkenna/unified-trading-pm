# Epic: deployment_and_user_management_master
# Lifecycle: permanent
# Delete-when: NA
"""Test-impact / selective-execution selector — the design's fallback rule as code.

Combines `import_graph_walker.py` (static reachability) with the verified
dynamic-dispatch allowlist (`test_impact_allowlist.yaml`) to produce the
design's binary output: either `RUN_FULL_SUITE=true`, or a provably-safe
narrowed test-file set. Per the design's own safety guarantee, ambiguity
always resolves to `RUN_FULL_SUITE=true` — never a best-guess subset.

Design doc: test_impact_selective_execution_design_2026_08_03.md
Plan: test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md (Phase 2, todo 2)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml
from import_graph_walker import affected_test_files, build_import_edges, invert_edges

#: Repos this v1 selector never narrows for — shared-dependency repos other
#: test suites editable-install against. Out of scope by explicit design
#: decision, not a gap to close later.
NO_NARROW_REPOS: Final[frozenset[str]] = frozenset({"unified-trading-library", "unified-api-contracts"})

#: Grep pattern for a genuine dynamic-dispatch call site — used both to
#: verify allowlist entries and to fail-closed on an UNCLASSIFIED site a
#: changed file introduces.
_DYNAMIC_DISPATCH_PATTERN: Final[re.Pattern[str]] = re.compile(r"importlib\.import_module|__getattr__|__import__\(")


@dataclass(frozen=True)
class SelectorResult:
    run_full_suite: bool
    reason: str
    narrowed_test_files: frozenset[Path] = frozenset()


def load_allowlist(allowlist_path: Path) -> dict[str, object]:
    raw = yaml.safe_load(allowlist_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{allowlist_path} must be a YAML mapping.")
    return raw


def _repo_dynamic_dispatch_prefixes(allowlist: dict[str, object], repo_name: str) -> list[str]:
    # A repo genuinely may have no entry (no verified dynamic dispatch found
    # for it yet) — {} is the correct default, not a masked error.
    repos = allowlist.get("repos", {})  # noqa: qg-empty-fallback
    if not isinstance(repos, dict):
        return []
    entry = repos.get(repo_name)
    if not isinstance(entry, dict):
        return []
    # Likewise, an entry with zero dynamic-dispatch paths is a real, valid state.
    paths = entry.get("dynamic_dispatch_paths", [])  # noqa: qg-empty-fallback
    if not isinstance(paths, list):
        return []
    return [p["path"] for p in paths if isinstance(p, dict) and isinstance(p.get("path"), str)]


def _cross_cutting_manifests(allowlist: dict[str, object]) -> frozenset[str]:
    # The manifest section is optional in principle (though the checked-in
    # allowlist always populates it) — absent means "no cross-cutting
    # manifests declared," a real, valid state, not a masked error.
    names = allowlist.get("cross_cutting_manifests", [])  # noqa: qg-empty-fallback
    if not isinstance(names, list):
        return frozenset()
    return frozenset(n for n in names if isinstance(n, str))


def _is_high_level_conftest(path: Path, repo_root: Path) -> bool:
    """Repo-root-level or top-level `tests/` conftest — invalidates the WHOLE
    suite, since fixture resolution walks upward from every test to the root."""
    parent = path.parent
    return parent == repo_root or (parent.name == "tests" and parent.parent == repo_root)


def _tests_under_subtree(directory: Path) -> frozenset[Path]:
    """Every test file (per the `tests/`-component / `test_`-prefix
    convention) under `directory`, recursively."""
    found: set[Path] = set()
    for path in directory.rglob("*.py"):
        if path.is_file() and (path.name.startswith("test_") or "tests" in path.relative_to(directory).parts):
            found.add(path)
    return frozenset(found)


def _matches_dynamic_dispatch_allowlist(changed: Path, repo_root: Path, prefixes: list[str]) -> bool:
    rel = changed.relative_to(repo_root).as_posix()
    for prefix in prefixes:
        stripped = prefix.rstrip("/")
        if rel == stripped or rel.startswith(f"{stripped}/"):
            return True
    return False


def _has_unclassified_dynamic_dispatch(changed: Path) -> bool:
    """Fail-closed check: a changed file that ITSELF contains a dynamic-
    dispatch call site is unsafe to narrow around, allowlisted or not — this
    catches a NEW dispatch pattern the allowlist hasn't been updated for yet."""
    try:
        text = changed.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return bool(_DYNAMIC_DISPATCH_PATTERN.search(text))


def classify_diff(
    repo_root: Path,
    repo_name: str,
    changed_files: list[Path],
    allowlist: dict[str, object],
) -> SelectorResult:
    """The design's fallback rule, applied to one repo's diff."""
    if repo_name in NO_NARROW_REPOS:
        return SelectorResult(True, f"{repo_name} is a shared-dependency repo — narrowing out of scope for v1")

    if not changed_files:
        return SelectorResult(False, "no changed files", frozenset())

    dynamic_dispatch_prefixes = _repo_dynamic_dispatch_prefixes(allowlist, repo_name)
    cross_cutting = _cross_cutting_manifests(allowlist)

    leaf_conftest_dirs: set[Path] = set()
    for changed in changed_files:
        if not changed.is_file():
            return SelectorResult(True, f"changed file not found on disk (deleted?): {changed}")

        if changed.name == "conftest.py":
            if _is_high_level_conftest(changed, repo_root):
                return SelectorResult(True, f"high-level conftest.py touched: {changed.relative_to(repo_root)}")
            leaf_conftest_dirs.add(changed.parent)
            continue

        if changed.name in cross_cutting:
            return SelectorResult(True, f"cross-cutting manifest touched: {changed.relative_to(repo_root)}")

        if _matches_dynamic_dispatch_allowlist(changed, repo_root, dynamic_dispatch_prefixes):
            return SelectorResult(True, f"verified dynamic-dispatch path touched: {changed.relative_to(repo_root)}")

        if _has_unclassified_dynamic_dispatch(changed):
            return SelectorResult(
                True,
                f"changed file contains an unallowlisted dynamic-dispatch call site: {changed.relative_to(repo_root)}"
                " — add it to test_impact_allowlist.yaml with a verified file:line citation first",
            )

    for changed in changed_files:
        if changed.suffix != ".py":
            continue
        try:
            ast.parse(changed.read_text(encoding="utf-8"), filename=str(changed))
        except (SyntaxError, ValueError, OSError, UnicodeDecodeError):
            return SelectorResult(True, f"AST walk cannot parse a changed file: {changed.relative_to(repo_root)}")

    edges = build_import_edges(repo_root)

    inverted = invert_edges(edges)
    narrowed = set(affected_test_files(changed_files, inverted))
    for conftest_dir in leaf_conftest_dirs:
        narrowed |= _tests_under_subtree(conftest_dir)

    return SelectorResult(False, "narrowed via import-graph reachability + leaf-conftest subtrees", frozenset(narrowed))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Test-impact/selective-execution selector.")
    default_allowlist = Path(__file__).resolve().parent / "test_impact_allowlist.yaml"
    _ = parser.add_argument("--repo-root", type=Path, required=True)
    _ = parser.add_argument("--repo-name", type=str, required=True)
    _ = parser.add_argument("--allowlist", type=Path, default=default_allowlist)
    _ = parser.add_argument("--changed-file", action="append", default=[], dest="changed_files")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    try:
        allowlist = load_allowlist(args.allowlist)
        changed = [(repo_root / f).resolve() for f in args.changed_files]
        result = classify_diff(repo_root, args.repo_name, changed, allowlist)
    except Exception as exc:
        # Fail-open to full suite on ANY selector error — the design's own
        # explicit requirement ("fail-open to running everything, never
        # fail-open to running nothing").
        print(f"RUN_FULL_SUITE=true  # selector process error, fail-open: {exc}", file=sys.stderr)
        return 0

    if result.run_full_suite:
        print(f"RUN_FULL_SUITE=true  # {result.reason}")
    else:
        print(f"RUN_FULL_SUITE=false  # {result.reason}")
        for f in sorted(result.narrowed_test_files):
            print(f.relative_to(repo_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
