# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP — CanonicalFuturesContract construction kwarg validation.

Enforces tradfi_master Q1 (UAC@2ac74e2 Phase 1A): every
`CanonicalFuturesContract(...)` call site MUST pass all 5 hard-required date
fields (`expiry_date`, `last_trading_date`, `first_notice_date`,
`delivery_date`, `settlement_date`) plus `lifecycle_phase`, `venue`, `root`,
`contract_symbol`, `contract_month`, `contract_year`.

How it works
------------
1. AST-walks every `.py` file in the workspace (excluding venvs, build
   artefacts, archived dirs).
2. For each Call node where `func.id == "CanonicalFuturesContract"` OR
   `func.attr == "CanonicalFuturesContract"`, collect the keyword argument
   names actually passed.
3. Exempt `**kwargs` spread calls (cannot statically resolve; treat as a
   trust boundary — surface as a warning, not an error).
4. On missing required kwarg: emit actionable error with file:line + the
   list of missing fields. Exit 1 on any error.

Reference
---------
SSOT: `plans/active/tradfi_canonical_futures_contract_hard_required_fields_2026_05_13.md`
Phase 5. Pydantic ValidationError at runtime is the safety net; this QG
catches the misconstructed call at PR time.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Final

REQUIRED_KWARGS: Final[frozenset[str]] = frozenset(
    {
        "venue",
        "root",
        "contract_symbol",
        "contract_month",
        "contract_year",
        "expiry_date",
        "last_trading_date",
        "first_notice_date",
        "delivery_date",
        "settlement_date",
        "lifecycle_phase",
    }
)

CLASS_NAME: Final[str] = "CanonicalFuturesContract"

EXCLUDE_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".venv",
        ".venv-workspace",
        "venv",
        "node_modules",
        "build",
        "dist",
        "__pycache__",
        ".git",
        ".pytest_cache",
        "plans",  # plan docs may reference the class name in markdown / code blocks
        # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
        # older/different snapshot of the same repo's source — scanning one
        # produces false violations for code that doesn't exist in the actual
        # checked-out tree (found live 2026-08-06, same class as the
        # check_manifest_import_alignment.py / test_event_logging.py fixes).
        ".claude",
    }
)


class _Finding:
    __slots__ = ("kind", "line", "missing", "path")

    def __init__(self, path: Path, line: int, missing: frozenset[str], kind: str) -> None:
        self.path = path
        self.line = line
        self.missing = missing
        self.kind = kind


def _iter_python_files(root: Path) -> Iterable[Path]:
    """Walk every .py file under `root`, skipping excluded dirs."""
    for entry in root.rglob("*.py"):
        if any(part in EXCLUDE_DIR_NAMES for part in entry.parts):
            continue
        yield entry


def _call_target_name(call: ast.Call) -> str | None:
    """Return the called name (handling both `Name(id=X)` and `Attribute(attr=X)`)."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _scan_file(path: Path) -> list[_Finding]:
    """Parse `path` and return any CanonicalFuturesContract construction issues."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    # Cheap pre-filter — skip files that don't mention the class name at all.
    if CLASS_NAME not in source:
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: list[_Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_target_name(node)
        if name != CLASS_NAME:
            continue

        # If a **kwargs spread is present, we can't statically validate.
        has_spread = any(kw.arg is None for kw in node.keywords)
        if has_spread:
            findings.append(_Finding(path, node.lineno, frozenset(), "warn-kwargs-spread"))
            continue

        passed = {kw.arg for kw in node.keywords if kw.arg is not None}
        missing = REQUIRED_KWARGS - passed
        if missing:
            findings.append(_Finding(path, node.lineno, frozenset(missing), "error"))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="QG STEP: assert every CanonicalFuturesContract(...) callsite passes all 11 required kwargs.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root to scan (default: cwd).",
    )
    parser.add_argument(
        "--strict-warn",
        action="store_true",
        help="Treat **kwargs-spread warnings as errors (exit 1).",
    )
    args = parser.parse_args(argv)

    all_findings: list[_Finding] = []
    for py in _iter_python_files(args.root):
        all_findings.extend(_scan_file(py))

    errors = [f for f in all_findings if f.kind == "error"]
    warnings = [f for f in all_findings if f.kind == "warn-kwargs-spread"]

    for f in errors:
        missing_str = ", ".join(sorted(f.missing))
        print(f"ERROR {f.path}:{f.line}: CanonicalFuturesContract(...) missing required kwargs: {missing_str}")
    for f in warnings:
        print(
            f"WARN {f.path}:{f.line}: CanonicalFuturesContract(...) uses **kwargs spread — "
            f"cannot statically validate required kwargs. Verify manually OR pass kwargs explicitly."
        )

    if errors:
        print(f"\n{len(errors)} error(s) found.", file=sys.stderr)
        return 1
    if warnings and args.strict_warn:
        print(f"\n{len(warnings)} warning(s) (strict mode).", file=sys.stderr)
        return 1
    if all_findings:
        print(f"\n{len(warnings)} warning(s); 0 errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
