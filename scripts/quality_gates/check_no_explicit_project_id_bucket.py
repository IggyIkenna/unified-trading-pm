#!/usr/bin/env python3
"""AST-walk QG STEP 5.72 — ban explicit ``project_id=`` on asset-group bucket builders.

Passing an explicit ``project_id`` to ``get_bucket_name(...)`` /
``get_write_bucket_name(...)`` **bypasses the cloud-providers.yaml SSOT** and
returns the legacy no-env shape (e.g. ``instruments-store-sports-{pid}`` /
``market-data-tick-defi-{pid}``) instead of the env-tiered canonical form
(``instruments-store-sports-prd-{pid}``). Those legacy no-env buckets are
DELETED at each asset_group's legacy-bucket decommission, so any live read/write
resolving the no-env form silently breaks at cutover.

Canonical: call the builder WITHOUT ``project_id`` (it then delegates to the
yaml SSOT and applies the env tier), or use
``unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(
cloud=..., kind=..., asset_group=...)`` directly.

Scope: only flags calls whose first positional arg is a *string-literal*
asset-group bucket domain (``instruments`` / ``market_data`` / ``features_*``)
AND that pass a ``project_id`` (kwarg OR 3rd positional). Non-asset-group
domains (``ml_models`` / ``ml_artifacts`` / ``pnl`` / ``risk`` / ``positions``)
are NOT asset-group-split and not in the decommission scope, so they are
exempt. Calls whose domain is a runtime variable are skipped (cannot resolve).

NOT in scope: ``scripts/`` + ``tests/`` + migration trees (they DELIBERATELY
read the legacy no-env bucket to migrate it). The bucket-naming SSOT modules
themselves (``cloud_constants.py`` / ``bucket_naming.py``) are skipped — they
are where the ``project_id`` forwarding plumbing legitimately lives.

Whitelist inline marker: ``# QG-allow: reading-legacy-bucket-for-migration`` on
the call line bypasses the check for a genuine migration-read.

Usage::

    # per-repo (run by base-service.sh STEP 5.72):
    python check_no_explicit_project_id_bucket.py \\
        --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: Bucket-builder functions that accept an SSOT-bypassing ``project_id``.
BUILDER_NAMES: Final[frozenset[str]] = frozenset({"get_bucket_name", "get_write_bucket_name"})

#: Asset-group-split bucket domains (env-tiered + decommissioned at AG cutover).
ASSET_GROUP_DOMAINS: Final[frozenset[str]] = frozenset(
    {
        "instruments",
        "market_data",
        "features_calendar",
        "features_delta_one",
        "features_onchain",
        "features_volatility",
        "features_sports",
        "features_prediction",
    }
)

#: Top-level dir names to skip when walking (scripts/tests/migrations excluded).
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
        "migrations",
    }
)

#: Path-fragment patterns that indicate archived / generated / migration trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    "/migration",
    "/migrate",
    ".egg-info",
)

#: SSOT modules where ``project_id`` forwarding plumbing legitimately lives.
EXCLUDE_FILE_NAMES: Final[frozenset[str]] = frozenset({"cloud_constants.py", "bucket_naming.py"})

#: Inline marker on the call line to bypass the check.
WHITELIST_MARKER: Final[str] = "QG-allow: reading-legacy-bucket-for-migration"


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    line: int
    func: str
    snippet: str


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


def _line(lines: list[str], lineno: int) -> str:
    return lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""


def _first_arg_domain(node: ast.Call) -> str | None:
    """Return the first positional arg as a string literal, else None."""
    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    return None


def _has_project_id(node: ast.Call) -> bool:
    """True if the call passes project_id (kwarg) OR a 3rd positional arg."""
    if any(kw.arg == "project_id" for kw in node.keywords):
        return True
    # 3rd positional arg of get_bucket_name(domain, asset_group, project_id).
    return len(node.args) >= 3


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_no_explicit_project_id_bucket] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        fname = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
        if fname not in BUILDER_NAMES:
            continue
        domain = _first_arg_domain(node)
        if domain is None or domain not in ASSET_GROUP_DOMAINS:
            continue
        if not _has_project_id(node):
            continue
        snippet = _line(lines, node.lineno)
        if WHITELIST_MARKER in snippet:
            continue
        findings.append(Finding(repo=repo, file=rel, line=node.lineno, func=fname, snippet=snippet))
    return findings


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_no_explicit_project_id_bucket] scope dir not found: {repo_root}", file=sys.stderr)
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
    parser = argparse.ArgumentParser(
        description="Ban explicit project_id= on asset-group bucket builders (QG STEP 5.72)."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument("--source-dir", default=None, help="Package sub-dir within the scoped repo.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_no_explicit_project_id_bucket] no source trees to scan — skipping.")
        return 0

    errors: list[Finding] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name
        for py in _iter_py_files(scan_root):
            errors.extend(_scan_file(py, repo_name, repo_root))

    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.func}(<asset-group domain>, ..., project_id=...)  — "
            f"explicit project_id bypasses the cloud-providers.yaml SSOT → legacy no-env bucket.\n"
            f"         {f.snippet}\n"
            f"         Drop the project_id arg (delegates to the yaml SSOT → env-tiered -prd- canonical) OR use "
            f"resolve_bucket_name(cloud=..., kind=..., asset_group=...). If genuinely reading the legacy bucket "
            f"to migrate it, add inline marker '# {WHITELIST_MARKER}'.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_no_explicit_project_id_bucket] FAIL — {len(errors)} explicit-project_id occurrence(s).",
            file=sys.stderr,
        )
        return 1
    print("[check_no_explicit_project_id_bucket] OK — 0 explicit-project_id asset-group bucket builders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
