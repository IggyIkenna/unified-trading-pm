#!/usr/bin/env python3
"""AST-walk QG STEP 5.64 — explicit ``source=`` at every *multi-source* manifest write.

Originally (``tradfi_massive_dual_source_2026_05_28.md`` Phase 3) this required
``source=`` at *every* ``record_captured`` call. Generalised by
``data_source_provenance_all_asset_groups_2026_06_01.md`` Phase 6 to the
**registry-driven** rule that matches the UTL runtime gate + universal-stamping
design:

  The UTL writer AUTO-STAMPS the sole external source for single-source cells
  and only RAISES ``MissingSourceError`` when a cell has >1 external source
  (``source_required(asset_group, data_type)`` is True) and ``source`` is blank.
  Computed/service-emitted + unregistered cells are exempt.

  So a static check that demands ``source=`` on *every* callsite would
  false-fail the single-source callsites that legitimately rely on auto-stamp.
  This check therefore flags a callsite ONLY when its ``category`` (asset_group)
  and ``data_type`` are statically resolvable (string literal OR module-level
  ``NAME = "literal"`` constant) AND the pair is multi-source per
  ``source_required()`` AND ``source=`` is absent.

  Callsites whose category/data_type are runtime variables are NOT flagged
  (the AST cannot resolve them) — the UTL runtime gate is the backstop there.
  Both ``record_captured(...)`` and ``add(...)`` (the legacy DeFi path) are
  scanned.

How it works
------------
1. Loads ``tradfi_source_explicit_baseline.yaml`` (baselined legacy
   occurrences → WARNing, exit-clean).
2. AST-walks every ``.py`` file under the given source dir(s) (skipping
   venvs / build artefacts / archived trees / scripts/ / tests/), resolving
   module-level string constants per file.
3. Flags every ``Call`` to ``.record_captured`` / ``.add`` where the resolved
   ``(category, data_type)`` is multi-source per ``source_required()`` and
   ``source=`` is NOT in ``Call.keywords``.
4. For each flagged occurrence: baselined → WARNING (exit-clean); else → ERROR
   + ``file:line`` — exit 1.

Whitelist inline marker: ``# QG-allow: tradfi-source-not-applicable`` on the
same line bypasses the check for genuine exceptions (e.g. a fixture that passes
kwargs via ``**dict``).

If ``unified_api_contracts.source_required`` cannot be imported (e.g. the
scanning venv lacks UAC), the check degrades to a no-op WARNing rather than
false-failing.

Usage::

    # per-repo (run by quality-gates.sh STEP 5.64):
    python check_tradfi_source_explicit_at_record_captured.py \\
        --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>

    # workspace-wide sweep:
    python check_tradfi_source_explicit_at_record_captured.py \\
        --workspace-root <ws>
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

#: ``record_captured`` + legacy ``add`` accept a ``source`` kwarg and apply the
#: registry-driven gate (the other record_* methods do not).
RECORD_METHOD_NAMES: Final[frozenset[str]] = frozenset({"record_captured", "add"})

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
WHITELIST_MARKER: Final[str] = "QG-allow: tradfi-source-not-applicable"

#: Required keys per baseline entry.
REQUIRED_KEYS: Final[tuple[str, ...]] = ("repo", "file", "line", "method", "status", "successor")

#: Allowed ``status:`` values per baseline entry.
VALID_STATUS: Final[frozenset[str]] = frozenset({"pending_phase3_sweep", "pending_massive_mtds_phase4"})


@dataclass(frozen=True)
class BaselineEntry:
    repo: str
    file: str
    line: int
    method: str
    status: str
    successor: str


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    line: int
    method: str
    snippet: str

    @property
    def baseline_key(self) -> tuple[str, str, int, str]:
        return (self.repo, self.file, self.line, self.method)


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "tradfi_source_explicit_baseline.yaml"


def load_baseline() -> tuple[dict[tuple[str, str, int, str], BaselineEntry], str]:
    path = _baseline_path()
    if not path.exists():
        return {}, "tradfi_massive_dual_source_2026_05_28 Phase 3 sweep"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    default_successor = str(raw.get("default_successor", "tradfi_massive_dual_source_2026_05_28 Phase 3 sweep"))
    out: dict[tuple[str, str, int, str], BaselineEntry] = {}
    for item in raw.get("entries", []) or []:  # noqa: qg-empty-fallback
        missing = [k for k in REQUIRED_KEYS if k not in item]
        if missing:
            print(
                f"[check_tradfi_source_explicit_at_record_captured] baseline entry missing keys {missing}: {item}",
                file=sys.stderr,
            )
            continue
        if item["status"] not in VALID_STATUS:
            print(
                f"[check_tradfi_source_explicit_at_record_captured] baseline entry has invalid status "
                f"{item['status']!r} (must be one of {sorted(VALID_STATUS)}): {item}",
                file=sys.stderr,
            )
            continue
        entry = BaselineEntry(
            repo=str(item["repo"]),
            file=str(item["file"]),
            line=int(item["line"]),
            method=str(item["method"]),
            status=str(item["status"]),
            successor=str(item["successor"]),
        )
        out[(entry.repo, entry.file, entry.line, entry.method)] = entry
    return out, default_successor


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


def _load_source_required() -> object | None:
    """Import the UAC ``source_required`` helper, or None if UAC is absent.

    Degrading to None makes the check a no-op WARNing rather than a false-fail
    when the scanning venv lacks UAC.
    """
    try:
        from unified_api_contracts import source_required  # noqa: qg-inside-import — optional dep

        return source_required
    except ImportError:
        return None


def _module_str_constants(tree: ast.Module) -> dict[str, str]:
    """Collect module-level ``NAME = "literal"`` string constants for resolution.

    Lets the check resolve ``data_type=_ORACLE_PRICES_DATA_TYPE`` where the
    constant is ``_ORACLE_PRICES_DATA_TYPE = "oracle_prices"`` at module scope.
    """
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = node.value.value
    return out


def _resolve_kwarg_str(node: ast.Call, name: str, consts: dict[str, str]) -> str | None:
    """Return the static string value of kwarg ``name`` (literal or const), else None."""
    for kw in node.keywords:
        if kw.arg != name:
            continue
        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
        if isinstance(kw.value, ast.Name) and kw.value.id in consts:
            return consts[kw.value.id]
        return None
    return None


def _scan_file(
    path: Path,
    repo: str,
    repo_root: Path,
    source_required: object | None,
) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_tradfi_source_explicit_at_record_captured] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    consts = _module_str_constants(tree)
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in RECORD_METHOD_NAMES:
            continue
        kwarg_names = {kw.arg for kw in node.keywords if kw.arg is not None}
        if "source" in kwarg_names:
            continue
        # Only flag when the cell is statically resolvable AND multi-source.
        # Unresolvable (variable) asset_group/data_type → skip (runtime gate backstop).
        # NB: the manifest-write param was renamed ``category`` → ``asset_group``
        # (UTL ManifestWriter contract upgrade, 2026-06-02) — resolve the new name.
        asset_group = _resolve_kwarg_str(node, "asset_group", consts)
        data_type = _resolve_kwarg_str(node, "data_type", consts)
        if asset_group is None or data_type is None:
            continue
        if source_required is None or not source_required(asset_group, data_type):  # type: ignore[operator]
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
            print(
                f"[check_tradfi_source_explicit_at_record_captured] scope dir not found: {repo_root}",
                file=sys.stderr,
            )
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
    parser = argparse.ArgumentParser(description="Explicit source= kwarg at every record_captured() call detector.")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument("--source-dir", default=None, help="Package sub-dir within the scoped repo.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline, default_successor = load_baseline()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_tradfi_source_explicit_at_record_captured] no source trees to scan — skipping.")
        return 0

    source_required = _load_source_required()
    if source_required is None:
        print(
            "[check_tradfi_source_explicit_at_record_captured] WARN — unified_api_contracts.source_required "
            "not importable in this venv; skipping registry-driven multi-source check (runtime gate is the backstop)."
        )
        return 0

    all_findings: list[Finding] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name
        for py in _iter_py_files(scan_root):
            all_findings.extend(_scan_file(py, repo_name, repo_root, source_required))

    errors: list[Finding] = []
    warnings: list[tuple[Finding, BaselineEntry]] = []
    for f in all_findings:
        entry = baseline.get(f.baseline_key)
        if entry is not None:
            warnings.append((f, entry))
        else:
            errors.append(f)

    for f, entry in warnings:
        print(
            f"[WARN] {f.repo}/{f.file}:{f.line}  {f.method}(...)  — baselined ({entry.status}); "
            f"successor: {entry.successor}"
        )
    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.method}(...)  — missing explicit source= kwarg.\n"
            f"         {f.snippet}\n"
            f'         Pass source=<source_string> (e.g. source="databento" / source="massive") per UAC '
            f"SOURCE_PRIORITY. For non-TradFi adapters: pass source=None. If genuinely N/A, add inline marker "
            f"'# {WHITELIST_MARKER}' OR add a baseline entry under tradfi_source_explicit_baseline.yaml.\n"
            f"         Default successor for clearing baselined occurrences: {default_successor}.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_tradfi_source_explicit_at_record_captured] FAIL — {len(errors)} non-baselined occurrence(s) "
            f"({len(warnings)} baselined warning(s)).",
            file=sys.stderr,
        )
        return 1
    print(
        f"[check_tradfi_source_explicit_at_record_captured] OK — {len(warnings)} baselined occurrence(s); "
        f"0 new occurrences."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
