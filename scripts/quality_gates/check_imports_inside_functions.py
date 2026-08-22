#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG check — imports inside functions (replaces regex-based check).

Enforces the workspace rule that imports should live at module top-level, not
inside function/method bodies. Nested-function imports hide dependencies from
the import-time graph + bypass module-load-time validation; they're allowed
only as escape hatches (legitimate cases use ``# noqa: imports-inside-functions``).

**Why AST not regex** — the prior regex check (``base-service.sh`` lines
502-505) matched any indented ``import ...`` / ``from ... import ...`` line,
which fires false positives on:

1. Docstring usage examples — ``\"\"\"... from foo import bar ...\"\"\"`` reads as
   "indented import" to a regex but is content inside a string literal.
2. Comments — ``    # from foo import bar`` (commented-out) — same story.
3. String literals embedded in code — error-message templates citing import
   paths, etc.
4. Multi-line strings that happen to wrap an ``import`` line.

Reference incident 2026-05-11: `features_service/{cross_instrument,calendar}/
monitors/feature_freshness.py` docstring containing
``from features_service.monitors import FeatureFreshnessChecker`` (a usage
example) flagged as a real nested import. Operator decision (a) 2026-05-11 —
upgrade the check to AST-based.

How it works
------------
1. AST-walks every ``.py`` file under the given source dir(s), skipping venvs
   / build artefacts / archived trees / tests/ / __init__.py.
2. For each ``Import`` / ``ImportFrom`` node, checks if any ancestor in the
   AST stack is a ``FunctionDef`` / ``AsyncFunctionDef`` / ``Lambda``. If yes
   → flagged as "import inside function" (the real violation).
3. Module-level imports (top-level + ``If`` / ``Try`` / ``With`` blocks at
   module scope) are NOT flagged. ``TYPE_CHECKING`` blocks (``if TYPE_CHECKING:``)
   are also not flagged — they're a legitimate module-level pattern.
4. Honours ``# noqa: imports-inside-functions`` per-line opt-out — the marker
   appears on the import line itself; case-insensitive match.

So docstrings + comments + string literals never trigger (they're not AST
``Import`` / ``ImportFrom`` nodes); only ACTUAL nested imports do.

Usage::

    # per-repo (called from base-service.sh / base-library.sh):
    python check_imports_inside_functions.py --source-dir <pkg>

    # exit-code semantics: 0 = no violations; 1 = violations; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Final

# ── Constants ────────────────────────────────────────────────────────────────

#: Per-line opt-out markers (case-insensitive). Handles both the canonical
#: single-code form (``# noqa: imports-inside-functions``) and multi-code
#: form where the marker appears after a comma (``
#: Also recognises the ruff code PLC0415 which is the ruff equivalent.
NOQA_MARKERS: Final[tuple[str, ...]] = (
    "noqa: imports-inside-functions",
    "noqa: qg-inside-import",
    # Multi-code variants — appear after a comma in the noqa list:
    ", imports-inside-functions",
    ", qg-inside-import",
    # ruff PLC0415 is the canonical ruff code for "import outside top-level"; treat
    # it as equivalent to qg-inside-import when it's the sole or first code:
    "noqa: plc0415",
)

#: AST node types that scope an import as "inside a function" (real violation).
FUNCTION_SCOPE_NODES: Final[tuple[type[ast.AST], ...]] = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
)

#: Path globs to skip wholesale (venvs, build artefacts, tests, __init__.py).
SKIP_PATH_PARTS: Final[frozenset[str]] = frozenset(
    {".venv", ".venv-workspace", "venv", "build", "dist", "node_modules", "tests", "__pycache__"}
)


# ── AST helpers ──────────────────────────────────────────────────────────────


def _iter_python_files(source_dir: Path) -> Iterator[Path]:
    """Yield every .py file under source_dir, skipping uninteresting trees."""
    for path in source_dir.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        if any(part in SKIP_PATH_PARTS for part in path.parts):
            continue
        yield path


def _has_function_ancestor(stack: list[ast.AST]) -> bool:
    """Return True if any ancestor in the AST walk stack is a function-scope node."""
    return any(isinstance(ancestor, FUNCTION_SCOPE_NODES) for ancestor in stack)


def _line_has_noqa(file_lines: list[str], lineno: int) -> bool:
    """Return True if the source line at lineno carries any noqa opt-out marker."""
    if lineno < 1 or lineno > len(file_lines):
        return False
    line_lower = file_lines[lineno - 1].lower()
    return any(marker in line_lower for marker in NOQA_MARKERS)


def _import_targets_self_package(node: ast.Import | ast.ImportFrom, self_pkg: str | None) -> bool:
    """Return True if the import targets the same package the source dir represents.

    Preserves base-library.sh self-package auto-skip behaviour (line 337's
    ``grep -v "from ${_SELF_PKG}\\."`` filter): inside-function imports of
    one's own package are typically circular-import workarounds — allow them
    without explicit noqa.
    """
    if not self_pkg:
        return False
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        return module == self_pkg or module.startswith(f"{self_pkg}.")
    # bare ``import foo.bar``
    return any(alias.name == self_pkg or alias.name.startswith(f"{self_pkg}.") for alias in node.names)


def _walk_with_stack(node: ast.AST, stack: list[ast.AST]) -> Iterator[tuple[ast.AST, list[ast.AST]]]:
    """Walk an AST yielding each node + its ancestor stack."""
    yield node, list(stack)
    stack.append(node)
    for child in ast.iter_child_nodes(node):
        yield from _walk_with_stack(child, stack)
    stack.pop()


# ── Main check ───────────────────────────────────────────────────────────────


def find_function_scope_imports(source_path: Path, self_pkg: str | None = None) -> list[tuple[int, str]]:
    """Return list of (lineno, source_line) for actual function-scope imports.

    Skips:
    - Imports with the per-line noqa marker (``# noqa: imports-inside-functions``
      or legacy ``# noqa: qg-inside-import``).
    - Imports targeting the self-package (preserves base-library.sh behaviour
      for circular-import workarounds).
    - Imports inside TYPE_CHECKING blocks at MODULE scope (these are not in
      function bodies, so already skipped by the ancestor-stack check; noted
      for clarity).
    """
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return []

    file_lines = source.splitlines()
    violations: list[tuple[int, str]] = []

    for node, stack in _walk_with_stack(tree, []):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if not _has_function_ancestor(stack):
            continue
        if _line_has_noqa(file_lines, node.lineno):
            continue
        if _import_targets_self_package(node, self_pkg):
            continue

        line_text = file_lines[node.lineno - 1].strip() if 0 < node.lineno <= len(file_lines) else "<unknown>"
        violations.append((node.lineno, line_text))

    return violations


def _path_matches_any_glob(path: Path, source_dir: Path, exclude_globs: list[str]) -> bool:
    """Return True if path (relative to source_dir) matches any of the exclude globs.

    Glob format mirrors `rg --glob` (POSIX-shell-style): supports ``*`` /
    ``**`` / ``?``. Leading ``!`` is stripped (callers pass exclusion globs
    in either form).
    """
    try:
        rel = path.relative_to(source_dir)
    except ValueError:
        return False
    rel_str = str(rel)
    for raw in exclude_globs:
        pattern = raw.lstrip("!")
        if Path(rel_str).match(pattern):
            return True
        # Also check against the bare path in case glob is rooted:
        if path.match(pattern):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for imports inside function bodies (AST-based).")
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Source directory to scan (e.g. <repo>/<package_name>).",
    )
    parser.add_argument(
        "--self-pkg",
        type=str,
        default=None,
        help="Self-package name to auto-skip on inside-function imports (preserves base-library.sh behaviour). "
        "If omitted, defaults to source-dir basename.",
    )
    parser.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="Additional glob patterns to skip (mirrors --glob '!<pattern>' in the prior rg-based check). Repeatable.",
    )
    parser.add_argument(
        "--max-violations-shown",
        type=int,
        default=10,
        help="Max violations printed before truncating (default 10).",
    )
    args = parser.parse_args()

    source_dir: Path = args.source_dir.resolve()
    if not source_dir.is_dir():
        print(f"ERROR: source-dir not a directory: {source_dir}", file=sys.stderr)
        return 2

    self_pkg: str | None = args.self_pkg if args.self_pkg is not None else source_dir.name

    all_violations: list[tuple[Path, int, str]] = []
    for path in _iter_python_files(source_dir):
        if _path_matches_any_glob(path, source_dir, args.exclude_glob):
            continue
        for lineno, line_text in find_function_scope_imports(path, self_pkg=self_pkg):
            all_violations.append((path, lineno, line_text))

    if not all_violations:
        return 0

    print(f"FAIL: {len(all_violations)} imports inside function bodies (AST-detected):", file=sys.stderr)
    for path, lineno, line_text in all_violations[: args.max_violations_shown]:
        try:
            rel = path.relative_to(Path.cwd())
        except ValueError:
            rel = path
        print(f"  {rel}:{lineno}: {line_text}", file=sys.stderr)
    if len(all_violations) > args.max_violations_shown:
        print(
            f"  ... ({len(all_violations) - args.max_violations_shown} more not shown)",
            file=sys.stderr,
        )
    print(
        "Move imports to module top-level OR add `# noqa: imports-inside-functions` per-line opt-out.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
