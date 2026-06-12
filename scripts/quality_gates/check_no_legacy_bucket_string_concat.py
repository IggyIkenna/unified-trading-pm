#!/usr/bin/env python3
"""AST-walk QG STEP 5.96 — ban string-concat construction of legacy bucket names.

Checks that no production source builds a ``market-data-tick-`` or
``instruments-store-`` bucket name by direct f-string interpolation or string
concatenation, which bypasses ``resolve_bucket_name`` and produces the legacy
flat/long-form names that are being decommissioned.

The two patterns flagged:

1. **F-string interpolation** — any ``ast.JoinedStr`` (f-string) whose first
   constant value starts with or ends with ``"market-data-tick-"`` or
   ``"instruments-store-"`` where that constant is immediately followed by a
   formatted value ``{...}`` (i.e. the prefix is part of the f-string and a
   variable follows it).

2. **String concatenation** — any ``ast.BinOp`` with ``ast.Add`` where the
   left operand is a string literal ending in ``"market-data-tick-"`` or
   ``"instruments-store-"``.

AST-based analysis correctly skips docstrings, comments, and string literals in
expressions that are not f-string or concatenation constructions (such as test
fixtures using the full canonical name ``"market-data-tick-cefi-prd-{pid}"``).

**Exclusions (not scanned)**:

- ``tests/`` and ``scripts/`` directories.
- Files named ``bucket_naming.py``, ``cloud_constants.py``, ``constants.py``
  (SSOT modules where legacy plumbing legitimately lives as dead/redirect code).
- Paths containing ``/migration``, ``/migrate``, or ``/audit``.
- Nodes carrying the inline marker ``# QG-allow: legacy-bucket-name-migration``
  on the same source line.

Usage::

    # per-repo (run by base-service.sh STEP 5.96):
    python check_no_legacy_bucket_string_concat.py \\
        --workspace-root <ws> --scope <repo-dir>
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

LEGACY_PREFIXES: Final[tuple[str, ...]] = ("market-data-tick-", "instruments-store-")
INLINE_ALLOWLIST: Final[str] = "QG-allow: legacy-bucket-name-migration"

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
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "htmlcov",
        ".tox",
        "site-packages",
        "tests",
        "scripts",
    }
)

EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/migration",
    "/migrate",
    "/audit",
    ".egg-info",
)

EXCLUDE_FILE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "bucket_naming.py",
        "cloud_constants.py",
        "constants.py",
    }
)


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    line: int
    kind: str  # "fstring" | "concat"
    snippet: str


def _ends_with_prefix(s: str) -> bool:
    return any(s.endswith(p) for p in LEGACY_PREFIXES)


def _starts_with_prefix(s: str) -> bool:
    return any(s.startswith(p) for p in LEGACY_PREFIXES)


def _check_fstring(node: ast.JoinedStr) -> bool:
    """True if the f-string builds a legacy bucket name via interpolation.

    Detects the pattern: f"market-data-tick-{var}" where a constant string
    ending with the legacy prefix is immediately followed by a FormattedValue.
    """
    values = node.values
    for i, val in enumerate(values):
        if not isinstance(val, ast.Constant) or not isinstance(val.value, str):
            continue
        if _ends_with_prefix(val.value) and i + 1 < len(values) and isinstance(values[i + 1], ast.FormattedValue):
            return True
    return False


def _check_concat(node: ast.BinOp) -> bool:
    """True if the concat builds a legacy bucket name.

    Detects: "market-data-tick-" + expr
    """
    if not isinstance(node.op, ast.Add):
        return False
    if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
        return _ends_with_prefix(node.left.value)
    return False


def _iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if parts & EXCLUDE_DIR_NAMES:
            continue
        if path.name in EXCLUDE_FILE_NAMES:
            continue
        s = str(path).replace("\\", "/")
        if any(frag in s for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        yield path


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(
            f"[check_no_legacy_bucket_string_concat] skip unparseable {path}: {exc}",
            file=sys.stderr,
        )
        return []

    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    findings: list[Finding] = []

    for node in ast.walk(tree):
        kind: str | None = None
        if isinstance(node, ast.JoinedStr) and _check_fstring(node):
            kind = "fstring"
        elif isinstance(node, ast.BinOp) and _check_concat(node):
            kind = "concat"
        if kind is None:
            continue
        lineno: int = getattr(node, "lineno", 0)
        snippet = lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""
        if INLINE_ALLOWLIST in snippet:
            continue
        findings.append(Finding(repo=repo, file=rel, line=lineno, kind=kind, snippet=snippet))

    return findings


def _resolve_scopes(workspace_root: Path, scope: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(
                f"[check_no_legacy_bucket_string_concat] scope dir not found: {repo_root}",
                file=sys.stderr,
            )
            return []
        return [(scope, repo_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir() or child.name in EXCLUDE_DIR_NAMES or child.name.startswith("."):
            continue
        if (child / "pyproject.toml").exists():
            out.append((child.name, child))
    return out


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ban string-concat construction of legacy bucket names (QG STEP 5.96)."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument(
        "--scope",
        default=None,
        help="Single repo dir name to scope to (per-repo QG mode).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    scopes = _resolve_scopes(workspace_root, args.scope)
    if not scopes:
        print("[check_no_legacy_bucket_string_concat] no source trees to scan — skipping.")
        return 0

    errors: list[Finding] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name
        for py in _iter_py_files(scan_root):
            errors.extend(_scan_file(py, repo_name, repo_root))

    for f in errors:
        kind_label = "f-string interpolation" if f.kind == "fstring" else "string concatenation"
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  Legacy bucket name via {kind_label}.\n"
            f"         {f.snippet}\n"
            f"         Use resolve_bucket_name(kind='market-data' | 'instruments-store', "
            f"asset_group=...) instead.\n"
            f"         If this is a genuine migration-read, add "
            f"'# {INLINE_ALLOWLIST}'.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_no_legacy_bucket_string_concat] FAIL — {len(errors)} legacy-bucket "
            f"string-concat occurrence(s). Route through "
            f"unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...).",
            file=sys.stderr,
        )
        return 1

    print("[check_no_legacy_bucket_string_concat] OK — 0 legacy-bucket string-concat constructions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
