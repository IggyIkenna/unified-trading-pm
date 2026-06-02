#!/usr/bin/env python3
"""AST-walk QG STEP 5.71 — ban the legacy ``category=`` kwarg at manifest writes.

The UTL ``ManifestWriter`` asset-group write param was renamed
``category`` → ``asset_group`` (UTL ManifestWriter contract upgrade,
2026-06-02; ``sports_manifest_canonicalisation_2026_06_01.md`` +
``defi_manifest_canonicalisation_2026_06_01.md`` cross-AG dead-bucket root).
v9 post-migration canonical vocabulary is ``asset_group`` everywhere — NEVER
``category``, not even as a fallback (operator directive 2026-06-02).

This ratchet flags any call that passes a ``category=`` keyword to one of the
asset-group-bearing ``ManifestWriter`` methods:

    record_captured / add / validate_df / write_with_zero_fill

(the four methods that carried the legacy ``category`` parameter). Callers MUST
pass ``asset_group=`` instead.

NOT in scope (left untouched — different axes):
  * ``ErrorCategory`` / ``failure_category`` / ``market_category`` /
    ``BookmakerCategory`` / ``error_category`` enum usages,
  * the legacy on-disk hive key ``category=`` in GCS path strings (migrated by
    each asset_group's L3 single-walk, not by code),
  * log-event detail dict keys named ``"category"`` (observability payloads).
Because this is an AST keyword-name check on four specific method calls, those
other surfaces are structurally excluded.

How it works
------------
1. AST-walks every ``.py`` file under the scoped repo (skipping
   venvs / build artefacts / archived trees / scripts/ / tests/).
2. Flags every ``Call`` to ``.record_captured`` / ``.add`` / ``.validate_df`` /
   ``.write_with_zero_fill`` that has a ``category=`` keyword argument.
3. Any flagged occurrence → ERROR + ``file:line`` — exit 1. Zero tolerance
   (the workspace-wide rename already removed every occurrence).

Whitelist inline marker: ``# QG-allow: category-kwarg-legacy`` on the call line
bypasses the check for a genuine, justified exception.

Usage::

    # per-repo (run by base-service.sh STEP 5.71):
    python check_no_category_kwarg_at_manifest_write.py \\
        --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>

    # workspace-wide sweep:
    python check_no_category_kwarg_at_manifest_write.py --workspace-root <ws>
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: ManifestWriter methods that carried the legacy ``category`` parameter.
MANIFEST_WRITE_METHODS: Final[frozenset[str]] = frozenset(
    {"record_captured", "add", "validate_df", "write_with_zero_fill"}
)

#: Top-level dir names to skip when walking.
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
        "scripts",
        "tests",
    }
)

#: Path-fragment patterns that indicate archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)

#: Inline marker on the call line to bypass the check.
WHITELIST_MARKER: Final[str] = "QG-allow: category-kwarg-legacy"


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    line: int
    method: str
    snippet: str


def _iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if parts & EXCLUDE_DIR_NAMES:
            continue
        s = str(path).replace("\\", "/")
        if any(frag in s for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        yield path


def _line(lines: list[str], lineno: int) -> str:
    return lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_no_category_kwarg_at_manifest_write] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in MANIFEST_WRITE_METHODS:
            continue
        if not any(kw.arg == "category" for kw in node.keywords):
            continue
        snippet = _line(lines, node.lineno)
        if WHITELIST_MARKER in snippet:
            continue
        findings.append(Finding(repo=repo, file=rel, line=node.lineno, method=func.attr, snippet=snippet))
    return findings


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_no_category_kwarg_at_manifest_write] scope dir not found: {repo_root}", file=sys.stderr)
            return []
        if source_dir and (repo_root / source_dir).is_dir():
            return [(scope, repo_root / source_dir)]
        return [(scope, repo_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir() or child.name in EXCLUDE_DIR_NAMES or child.name.startswith("."):
            continue
        if (child / "pyproject.toml").exists():
            out.append((child.name, child))
    return out


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ban legacy category= kwarg at ManifestWriter writes (QG STEP 5.71).")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument("--source-dir", default=None, help="Package sub-dir within the scoped repo.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_no_category_kwarg_at_manifest_write] no source trees to scan — skipping.")
        return 0

    errors: list[Finding] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name
        for py in _iter_py_files(scan_root):
            errors.extend(_scan_file(py, repo_name, repo_root))

    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.method}(category=...)  — legacy asset-group kwarg.\n"
            f"         {f.snippet}\n"
            f"         Rename ``category=`` → ``asset_group=`` (UTL ManifestWriter contract, v9 canonical). "
            f"If genuinely N/A, add inline marker '# {WHITELIST_MARKER}' with a one-line reason.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_no_category_kwarg_at_manifest_write] FAIL — {len(errors)} legacy category= occurrence(s).",
            file=sys.stderr,
        )
        return 1
    print("[check_no_category_kwarg_at_manifest_write] OK — 0 legacy category= kwargs at manifest writes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
