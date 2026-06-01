#!/usr/bin/env python3
"""AST-walk QG STEP 5.64 — explicit ``source=`` at every ``record_captured`` call.

Per ``tradfi_massive_dual_source_2026_05_28.md`` Phase 3:

  ``MissingSourceError`` fires at runtime when ``category=="tradfi"`` and
  ``source`` is omitted from ``record_captured``.  This static check catches
  the bug at QG time — before any MTDS or consumer adapter ships — so TradFi
  writers can never silently leave ``source=""`` in the manifest.

  Because detecting the runtime value of ``category`` from AST alone is
  impractical (it may be a variable), this check takes the conservative
  approach: **every ``record_captured(...)`` call site must pass ``source=``
  explicitly**.  Non-TradFi adapters incur no runtime cost (the gate is a
  no-op for non-tradfi categories), and passing ``source=None`` is
  semantically identical to omitting it, so the burden on non-TradFi callers
  is minimal: add ``source=None`` or ``source=""``.

  Existing call sites that predate Phase 3 are baselined in
  ``tradfi_source_explicit_baseline.yaml`` and surface as WARNings (exit-clean)
  until a follow-up sweep clears them.

How it works
------------
1. Loads ``tradfi_source_explicit_baseline.yaml`` (workspace baseline of
   CURRENTLY-KNOWN missing-source occurrences — these surface as WARNings,
   exit-clean).
2. AST-walks every ``.py`` file under the given source dir(s) (skipping
   venvs / build artefacts / archived trees / scripts/ / tests/).
3. Flags every ``Call`` node where ``Call.func`` is an ``Attribute`` matching
   ``"record_captured"`` AND ``source=`` is NOT in ``Call.keywords``.
4. For each flagged occurrence: if ``(repo, file, line)`` is in the baseline →
   WARNING (informational, exit-clean). Else → ERROR + ``file:line`` — exit 1.

Whitelist inline marker: ``# QG-allow: tradfi-source-not-applicable`` on the
same line bypasses the check for genuine exceptions (e.g. a test fixture that
passes kwargs via ``**dict``).

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

#: Only ``record_captured`` requires ``source=`` (the other record_* methods do
#: not accept a ``source`` kwarg in the current UTL API surface).
RECORD_METHOD_NAMES: Final[frozenset[str]] = frozenset({"record_captured"})

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


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_tradfi_source_explicit_at_record_captured] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
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

    all_findings: list[Finding] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name
        for py in _iter_py_files(scan_root):
            all_findings.extend(_scan_file(py, repo_name, repo_root))

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
