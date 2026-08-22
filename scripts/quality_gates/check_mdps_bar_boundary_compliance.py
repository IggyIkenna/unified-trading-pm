#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""STEP 5.74 — AST-walk MDPS source for inline bar-boundary truncation bypasses.

Asserts that MDPS calculators / writers emitting bars do NOT use inline
timestamp-truncation patterns:

* ``pd.Timestamp.floor(...)``
* ``pd.Timestamp.round(...)``
* ``dt.replace(minute=0, ...)`` / ``.replace(second=0, ...)`` / ``.replace(microsecond=0, ...)``
* ``polars.functions.dt.truncate(...)`` / ``pl.col(...).dt.truncate(...)``

These bypass the canonical
:func:`unified_trading_library.availability_stamping.compute_bar_close_boundary`
helper which centralises UTC-midnight-aligned + timeframe-aligned boundary
computation per UAC AVAILABILITY_AT_SEMANTICS.

Pairs with ``available_at_lookahead_bias_completion_2026_05_08`` Phase 0.7
Item 3. Mirror of writegate STEP 5.64 (cluster validation static check).

Why AST not regex — same reason as STEP 5.62
(``check_imports_inside_functions.py``): regex false-positives on docstrings,
comments, string literals containing example code. AST guarantees we only
flag ACTUAL function calls.

How it works
------------

1. AST-walks every ``.py`` file under the source dir, skipping ``.venv*``,
   ``build``, ``dist``, ``__pycache__``, archived trees, and ``tests/``.
2. For each ``Call`` node, checks whether the callee resolves to a banned
   pattern (e.g. ``Attribute(value=..., attr="floor")`` where the call has
   exactly one timeframe-string argument like ``"1h"`` / ``"15min"`` / etc).
3. ``dt.replace(...)`` is banned when the kwargs zero out at least one of
   ``minute`` / ``second`` / ``microsecond`` (the truncation pattern); plain
   ``replace(year=..., month=...)`` is allowed.
4. Honours ``# noqa: bar-boundary-truncation`` per-line opt-out for the rare
   legitimate case (e.g. test fixture constructing a deliberately misaligned
   bar to test the write-gate).

Exit-code semantics: 0 = no violations; 1 = violations; 2 = arg/IO error.

Usage::

    # per-repo (called from base-service.sh STEP 5.74):
    python check_mdps_bar_boundary_compliance.py --source-dir market_data_processing_service

    # for tests:
    python check_mdps_bar_boundary_compliance.py --source-dir <fixture-dir>
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterator
from pathlib import Path

# Timeframe-like string arguments that mark a truncation call as bar-boundary-related.
_TIMEFRAME_ARG_PATTERNS: frozenset[str] = frozenset(
    [
        "1min",
        "5min",
        "15min",
        "30min",
        "1h",
        "2h",
        "4h",
        "6h",
        "12h",
        "1d",
        "1D",
        "1H",
        "1T",  # pandas legacy aliases
        "5T",
        "15T",
        "30T",
        "60T",
        "1m",
        "5m",
        "15m",
        "30m",
        "1H",
        "1S",
    ]
)

# Banned attribute-call patterns: (attribute_name, description)
_BANNED_ATTR_CALLS: dict[str, str] = {
    "floor": "pd.Timestamp.floor() bypass — use compute_bar_close_boundary()",
    "round": "pd.Timestamp.round() bypass — use compute_bar_close_boundary()",
    "truncate": "polars dt.truncate() bypass — use compute_bar_close_boundary()",
}

# kwargs that mark `.replace(...)` as a truncation (zeroing-out time components)
_REPLACE_TRUNCATION_KWARGS: frozenset[str] = frozenset(["minute", "second", "microsecond", "nanosecond"])

# Directories to skip in source walk.
_SKIP_DIR_NAMES: frozenset[str] = frozenset(
    [
        ".venv",
        ".venv-workspace",
        "venv",
        "build",
        "dist",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "tests",
        "test",
        "archive",
        "archived",
    ]
)

_NOQA_MARKER = "# noqa: bar-boundary-truncation"


class _Violation:
    __slots__ = ("col", "file_path", "line", "reason", "snippet")

    def __init__(
        self,
        file_path: Path,
        line: int,
        col: int,
        snippet: str,
        reason: str,
    ) -> None:
        self.file_path = file_path
        self.line = line
        self.col = col
        self.snippet = snippet
        self.reason = reason

    def format(self) -> str:
        return f"{self.file_path}:{self.line}:{self.col}: {self.reason}\n    {self.snippet}"


def _iter_py_files(source_dir: Path) -> Iterator[Path]:
    """Walk source_dir yielding .py files; skip venvs/build/tests/archived."""
    for path in source_dir.rglob("*.py"):
        if any(part in _SKIP_DIR_NAMES for part in path.parts):
            continue
        if any(part.startswith(".venv") for part in path.parts):
            continue
        yield path


def _line_has_noqa(file_lines: list[str], lineno: int) -> bool:
    """Return True if file_lines[lineno-1] contains the noqa opt-out marker."""
    if 1 <= lineno <= len(file_lines):
        return _NOQA_MARKER in file_lines[lineno - 1]
    return False


def _is_timeframe_string_arg(node: ast.expr) -> bool:
    """Return True if node is a string Constant matching a timeframe pattern."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value in _TIMEFRAME_ARG_PATTERNS
    return False


def _call_has_timeframe_arg(call: ast.Call) -> bool:
    """Return True if any positional arg of the call is a timeframe-string."""
    return any(_is_timeframe_string_arg(arg) for arg in call.args)


def _replace_has_truncation_kwargs(call: ast.Call) -> bool:
    """Return True if .replace(...) has truncation kwargs zeroed out."""
    for kw in call.keywords:
        if kw.arg in _REPLACE_TRUNCATION_KWARGS and isinstance(kw.value, ast.Constant) and kw.value.value == 0:
            return True
    return False


def _scan_file(file_path: Path) -> list[_Violation]:
    """Parse + AST-walk a single file; return violations."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        print(
            f"{file_path}: ERROR reading file: {err}",
            file=sys.stderr,
        )
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as err:
        print(
            f"{file_path}:{err.lineno}:{err.offset}: SYNTAX ERROR in source: {err.msg}",
            file=sys.stderr,
        )
        return []

    file_lines = source.splitlines()
    violations: list[_Violation] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue

        attr_name = node.func.attr

        # Pattern 1: .floor("1h") / .round("1h") / .truncate("1h")
        if attr_name in _BANNED_ATTR_CALLS:
            if _call_has_timeframe_arg(node):
                if _line_has_noqa(file_lines, node.lineno):
                    continue
                snippet = file_lines[node.lineno - 1].strip() if 1 <= node.lineno <= len(file_lines) else "<unknown>"
                violations.append(
                    _Violation(
                        file_path=file_path,
                        line=node.lineno,
                        col=node.col_offset,
                        snippet=snippet,
                        reason=_BANNED_ATTR_CALLS[attr_name],
                    )
                )

        # Pattern 2: .replace(minute=0, second=0, microsecond=0)
        elif attr_name == "replace" and _replace_has_truncation_kwargs(node):
            if _line_has_noqa(file_lines, node.lineno):
                continue
            snippet = file_lines[node.lineno - 1].strip() if 1 <= node.lineno <= len(file_lines) else "<unknown>"
            violations.append(
                _Violation(
                    file_path=file_path,
                    line=node.lineno,
                    col=node.col_offset,
                    snippet=snippet,
                    reason=("dt.replace(minute=0, ...) truncation bypass — use compute_bar_close_boundary()"),
                )
            )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=("STEP 5.74 — MDPS bar-boundary truncation-bypass static check."))
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Path to source directory to scan (typically the service package).",
    )
    args = parser.parse_args()

    source_dir: Path = args.source_dir
    if not source_dir.is_dir():
        print(
            f"ERROR: --source-dir {source_dir} is not a directory",
            file=sys.stderr,
        )
        return 2

    all_violations: list[_Violation] = []
    for py_file in _iter_py_files(source_dir):
        all_violations.extend(_scan_file(py_file))

    if not all_violations:
        return 0

    print(
        f"\n❌ STEP 5.74: MDPS bar-boundary truncation-bypass check found {len(all_violations)} violation(s):\n",
        file=sys.stderr,
    )
    for v in all_violations:
        print(v.format(), file=sys.stderr)
    print(
        "\nUse unified_trading_library.availability_stamping."
        "compute_bar_close_boundary() for timeframe-aligned boundary "
        "computation. Or add `# noqa: bar-boundary-truncation` to the line "
        "if this is a legitimate exception (e.g. test fixture).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
