#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""STEP 5.85 — static AST checker: every record_empty() callsite must pass a non-blank reason=.

Walks Python source under SOURCE_DIR (first CLI arg) and rejects:
  - record_empty(...) with no reason= kwarg
  - record_empty(reason="") or record_empty(reason='')

Excluded paths: manifest_writer.py (definition site), .venv*, build/, tests/.

Exit 0 = clean. Exit 1 = violations found (printed to stdout).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# ".claude" excludes nested per-agent git worktrees (.claude/worktrees/<id>/) — a worktree
# can carry an older/different snapshot of the same repo's source, producing false
# violations for code that doesn't exist in the actual checked-out tree.
_SKIP_DIRS = {".venv", ".venv-workspace", "build", "dist", "__pycache__", "node_modules", ".claude"}
_DEFINITION_FILE_SUFFIX = "manifest_writer.py"


def _is_blank_reason(node: ast.Call) -> bool:
    """Return True if the call has no reason= kwarg or has reason=""."""
    for kw in node.keywords:
        if kw.arg == "reason":
            val = kw.value
            return bool(isinstance(val, ast.Constant) and val.value == "")
    return True


def check_source(path: Path) -> list[tuple[int, str]]:
    violations: list[tuple[int, str]] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return violations

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = ""
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        if name != "record_empty":
            continue
        if _is_blank_reason(node):
            violations.append((node.lineno, f"record_empty() missing non-blank reason= at line {node.lineno}"))
    return violations


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: no_blank_record_empty_reason.py <source_dir>", file=sys.stderr)
        return 1

    source_dir = Path(sys.argv[1])
    if not source_dir.is_dir():
        print(f"ERROR: {source_dir} is not a directory", file=sys.stderr)
        return 1

    total_violations = 0
    for py_file in sorted(source_dir.rglob("*.py")):
        if py_file.name == _DEFINITION_FILE_SUFFIX:
            continue
        if any(skip in py_file.parts for skip in _SKIP_DIRS):
            continue
        violations = check_source(py_file)
        for lineno, msg in violations:
            rel = py_file.relative_to(source_dir)
            print(f"  {rel}:{lineno}: {msg}")
            total_violations += 1

    return 1 if total_violations > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
