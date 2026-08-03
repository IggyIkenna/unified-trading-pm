# Epic: deployment_and_user_management_master
# Lifecycle: permanent
# Delete-when: NA
"""Per-repo import-graph walker for the test-impact/selective-execution selector.

Extends `check_removed_symbols.py`'s existing `ast.walk()`-over-`Import`/`ImportFrom`
pattern (same `iter_python_files()` / exclude-dir list) into a `file -> {imported
files}` edge table, inverted to `file -> {transitive importers}`.

Design doc: test_impact_selective_execution_design_2026_08_03.md
Plan: test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md (Phase 2, todo 1)

Scope: PER-REPO, not cross-repo. The design's own fallback rule already forces
`RUN_FULL_SUITE=true` whenever a diff touches `unified-trading-library` or
`unified-api-contracts` (shared-dependency repos other test suites editable-install
against — narrowing there is explicitly out of scope for v1). So this walker only
ever needs to resolve imports that land inside the SAME repo; anything that resolves
outside the repo root (stdlib, third-party, or another workspace repo) is an
untracked external leaf, not a graph node.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import sys
from collections import deque
from pathlib import Path
from typing import Final

from check_removed_symbols import iter_python_files

#: Cache-file name, written inside the scanned repo root (mirrors `.qg_content_sentinel`'s
#: per-repo placement pattern — see `scripts/quality-gates-base/base-service.sh`).
CACHE_FILE_NAME: Final[str] = ".import_graph_cache.json"


# ── Content-sentinel cache key ───────────────────────────────────────────────


def compute_content_sentinel(repo_root: Path) -> str:
    """Hash (relative path, size, mtime_ns) for every tracked `.py` file.

    Same purpose as `.qg_content_sentinel` (base-service.sh): a cheap,
    deterministic key that changes iff the tree's `.py` content changed, so a
    repeat run against an unchanged tree can skip rebuilding the edge table.
    """
    hasher = hashlib.sha256()
    entries: list[tuple[str, int, int]] = []
    for path in iter_python_files(repo_root):
        try:
            stat = path.stat()
        except OSError:
            continue
        entries.append((str(path.relative_to(repo_root)), stat.st_size, stat.st_mtime_ns))
    for rel, size, mtime_ns in sorted(entries):
        hasher.update(f"{rel}\0{size}\0{mtime_ns}\n".encode())
    return hasher.hexdigest()


# ── Module-path resolution ───────────────────────────────────────────────────


def _base_dir_for(level: int, importing_file: Path, repo_root: Path) -> Path:
    """The directory a dotted module path resolves relative to."""
    if level == 0:
        return repo_root
    base_dir = importing_file.parent  # level=1: current package, no ascent
    for _ in range(level - 1):
        base_dir = base_dir.parent
    return base_dir


def _resolve_import_target(module_dotted: str, level: int, importing_file: Path, repo_root: Path) -> list[Path]:
    """Every file a `from X import Y` / `import X` statement genuinely
    executes: EVERY ancestor package's `__init__.py` along the dotted path
    (real Python import semantics run each one before the leaf import
    completes), plus the leaf module file and/or its own `__init__.py` if
    it's a package. Missing components (external / stdlib / cross-repo) are
    silently skipped — this only ever returns in-repo files."""
    base_dir = _base_dir_for(level, importing_file, repo_root)
    if not module_dotted:
        # `from . import x` — base_dir IS the package.
        init_file = base_dir / "__init__.py"
        return [init_file] if init_file.is_file() else []

    parts = module_dotted.split(".")
    resolved: list[Path] = []
    current = base_dir
    for idx, part in enumerate(parts):
        current = current / part
        is_leaf = idx == len(parts) - 1
        init_file = current / "__init__.py"
        if init_file.is_file():
            resolved.append(init_file)
        if is_leaf:
            module_file = current.with_suffix(".py")
            if module_file.is_file():
                resolved.append(module_file)
    return resolved


# ── Edge extraction ───────────────────────────────────────────────────────────


def _extract_imported_files(file_path: Path, source_text: str, repo_root: Path) -> set[Path]:
    """Parse one file's imports; return the set of in-repo files it imports."""
    try:
        tree = ast.parse(source_text, filename=str(file_path))
    except (SyntaxError, ValueError):
        # Unparseable file: the CALLER (selector) must treat this as an
        # AST-walk failure -> RUN_FULL_SUITE=true, per the design's fallback
        # rule. The walker itself just can't produce edges for it.
        return set()

    imported: set[Path] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.update(_resolve_import_target(alias.name, 0, file_path, repo_root))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported.update(_resolve_import_target(module, node.level, file_path, repo_root))
            # Each imported name might itself be a submodule (`from pkg import
            # submodule`) — resolve it too for the more precise leaf edge, on
            # top of the ancestor-package edges `module` alone already added.
            for alias in node.names:
                sub_dotted = f"{module}.{alias.name}" if module else alias.name
                imported.update(_resolve_import_target(sub_dotted, node.level, file_path, repo_root))
    imported.discard(file_path)  # a file never "imports itself"
    return imported


# ── Public API ───────────────────────────────────────────────────────────────

#: file -> {files it imports, within the same repo}
ImportEdges = dict[Path, frozenset[Path]]
#: file -> {files that import it directly, within the same repo}
InvertedEdges = dict[Path, frozenset[Path]]


def build_import_edges(repo_root: Path) -> ImportEdges:
    """Build the forward edge table for every `.py` file under `repo_root`."""
    edges: ImportEdges = {}
    for file_path in iter_python_files(repo_root):
        try:
            source_text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            edges[file_path] = frozenset()
            continue
        edges[file_path] = frozenset(_extract_imported_files(file_path, source_text, repo_root))
    return edges


def invert_edges(edges: ImportEdges) -> InvertedEdges:
    """Invert `file -> imports` into `file -> {direct importers}`."""
    inverted: dict[Path, set[Path]] = {f: set() for f in edges}
    for importer, targets in edges.items():
        for target in targets:
            inverted.setdefault(target, set()).add(importer)
    return {f: frozenset(importers) for f, importers in inverted.items()}


def transitive_importers(changed_file: Path, inverted: InvertedEdges) -> frozenset[Path]:
    """BFS over the inverted edge table: every file that (directly or
    transitively) imports `changed_file`."""
    seen: set[Path] = set()
    queue: deque[Path] = deque(inverted.get(changed_file, frozenset()))
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(inverted.get(current, frozenset()) - seen)
    return frozenset(seen)


def affected_test_files(
    changed_files: list[Path],
    inverted: InvertedEdges,
) -> frozenset[Path]:
    """Union of transitive importers of every changed file, filtered to test
    files — a path with a `tests/` directory component or a `test_`-prefixed
    filename, the workspace-wide pytest discovery convention."""
    affected: set[Path] = set()
    for changed in changed_files:
        affected |= transitive_importers(changed, inverted)
        if _is_test_file(changed):
            affected.add(changed)  # a changed test file affects itself
    return frozenset(f for f in affected if _is_test_file(f))


def _is_test_file(path: Path) -> bool:
    """A file pytest actually COLLECTS as a test module — filename
    convention only, per the workspace's `test_*.py` discovery pattern.
    Deliberately NOT "lives under a tests/ directory": that would also flag
    `conftest.py`/`__init__.py`/test-support fixtures, none of which pytest
    collects as tests themselves."""
    return path.name.startswith("test_")


# ── CLI entrypoint (verification / ad-hoc use) ───────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build + query the per-repo import-graph walker (test-impact selector building block)."
    )
    _ = parser.add_argument("--repo-root", type=Path, required=True, help="Repo root to scan.")
    _ = parser.add_argument(
        "--show-importers-of",
        type=Path,
        default=None,
        help="Print the transitive importer set for this file (relative to --repo-root) and exit.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if not repo_root.is_dir():
        print(f"FAIL — --repo-root not a directory: {repo_root}", file=sys.stderr)
        return 2

    sentinel = compute_content_sentinel(repo_root)
    edges = build_import_edges(repo_root)
    inverted = invert_edges(edges)
    print(f"Content sentinel: {sentinel}", file=sys.stderr)
    print(f"Files scanned: {len(edges)}", file=sys.stderr)
    print(f"Total edges: {sum(len(v) for v in edges.values())}", file=sys.stderr)

    if args.show_importers_of is not None:
        target = (repo_root / args.show_importers_of).resolve()
        importers = transitive_importers(target, inverted)
        print(f"\nTransitive importers of {args.show_importers_of} ({len(importers)}):", file=sys.stderr)
        for imp in sorted(importers):
            print(f"  {imp.relative_to(repo_root)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
