#!/usr/bin/env python3
"""QG STEP 5.94 — ``try: import X … except ImportError:`` fallback-import ratchet.

Enforces the workspace no-empty-fallbacks rule
(``.cursor/rules/standards/no-empty-fallbacks.mdc`` § "No try/except ImportError
Fallbacks", hardened into CI by
``plans/active/harden_grepable_rules_into_ci_gates_2026_06_02.md`` Phase 3):
never wrap library imports in ``try/except ImportError`` (or
``ModuleNotFoundError``) to provide a fallback implementation — fail LOUD at
import time when a required dependency is missing. Silent import fallbacks hide
missing dependencies, mask architectural violations, and make debugging
impossible. The rule applies to ALL tiers (T0-T3, services, UIs) — there is NO
tier-specific exception.

What is flagged (AST-based — docstrings / comments / string literals never
trigger):

1. An ``ast.Try`` whose body contains an ``import`` / ``from … import`` and
   whose handlers catch ``ImportError`` or ``ModuleNotFoundError`` (alone or in
   a tuple) — the canonical fallback-import shim. Flagged regardless of the
   handler body: even a re-raise wrapper is a shim to delete (import directly;
   declare the dep in pyproject).
2. An ``ast.Try`` whose body is **imports only** and whose handlers catch
   ``Exception`` / ``BaseException`` / bare ``except`` — the same shim hiding
   behind a broader catch. (Mixed try-bodies with a broad catch are NOT flagged
   — those are runtime guards, not import guards.)

Per-line opt-out: ``# noqa: fallback-import`` on the ``try:`` line, with a
one-line reason (e.g. a genuinely-optional ML extra gated by a documented
feature flag). The baseline grandfathers the audited pre-existing set.

Shape — **baseline ratchet** (NOT zero-tolerance from day 1; the 2026-06-10
audit measured 73 raw / ~67 real pre-existing sites fleet-wide, e.g.
features-service smoke_matrix shims + UTL optional-dep guards):

  1. Load ``no_fallback_imports_baseline.yaml`` — a per-repo count of the
     currently-known fallback-import sites (those WITHOUT ``# noqa:
     fallback-import``).
  2. Scan every ``.py`` file under the scan root (skipping venvs / build
     artefacts / archived trees / tests).
  3. count <= baseline → OK (a WARN when strictly below, so the operator
     ratchets the baseline DOWN). count > baseline → ERROR (exit 1): a NEW
     fallback-import shim landed — import directly, or add ``# noqa:
     fallback-import`` with a one-line reason.

The baseline ONLY shrinks: re-run with ``--update-baseline`` after removing
shims (counts are clamped DOWN — never raised).

Usage::

    # per-repo (run by base-service.sh / base-library.sh STEP 5.94):
    python check_no_fallback_imports.py --workspace-root <ws> --scope <repo-dir> [--source-dir <pkg>]

    # workspace-wide sweep:
    python check_no_fallback_imports.py --workspace-root <ws>

    # ratchet the baseline DOWN after removing shims:
    python check_no_fallback_imports.py --workspace-root <ws> --update-baseline

Exit codes: 0 = clean / at-or-below baseline; 1 = over baseline; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: The "grandfathered, intentional" per-line exemption marker (on the ``try:`` line).
NOQA_MARKER: Final[str] = "noqa: fallback-import"

#: Exception names that mark a fallback-IMPORT handler when ANY import is in the try body.
IMPORT_ERROR_NAMES: Final[frozenset[str]] = frozenset({"ImportError", "ModuleNotFoundError"})

#: Broad exception names that mark a fallback handler when the try body is imports-ONLY.
BROAD_ERROR_NAMES: Final[frozenset[str]] = frozenset({"Exception", "BaseException"})

#: Top-level dir names to skip when walking. Mirrors check_inline_bucket_uri.py,
#: EXCEPT ``scripts`` stays IN scope — the 2026-06-10 audit's worst offender
#: (features-service, 19 sites) is a repeated ``scripts/*/smoke_matrix.py`` shim.
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
    }
)

#: Path-fragment patterns that indicate archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)

#: Test-file basename patterns (skipped — optional-import guards are a test idiom).
TEST_FILE_PREFIXES: Final[tuple[str, ...]] = ("test_",)
TEST_FILE_SUFFIXES: Final[tuple[str, ...]] = ("_test.py",)


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "no_fallback_imports_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts of fallback-import sites."""

    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))


def load_baseline(path: Path | None = None) -> Baseline:
    baseline_file = path if path is not None else _baseline_path()
    if not baseline_file.exists():
        return Baseline()
    raw = yaml.safe_load(baseline_file.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, int] = {}
    for repo, val in repos_raw.items():
        if isinstance(val, dict):
            counts[str(repo)] = int(val.get("count", 0))
        else:
            counts[str(repo)] = int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline, path: Path | None = None) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised above the
    existing baseline (a higher count means a new shim landed; delete it, don't
    bake it in)."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        if repo not in counts:
            # Not scanned this run (scoped --update-baseline) — carry the existing
            # row forward verbatim. Treating unobserved as 0 + down-clamp zeroes the
            # fleet (same defect class as check_ruff_rule_ratchet, incident 2026-06-10).
            merged[repo] = {"count": existing.allowed(repo)}
            continue
        observed = int(counts[repo])
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for QG STEP 5.94 — try/except-ImportError fallback-import ratchet.\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of\n"
        "# `try: import X … except (ImportError|ModuleNotFoundError|broad)` fallback\n"
        "# shims (WITHOUT a `# noqa: fallback-import` marker) the gate tolerates in\n"
        "# that repo (tests/ excluded; scripts/ INCLUDED). A repo whose live count\n"
        "# EXCEEDS its baseline fails CI — a NEW shim landed; import directly +\n"
        "# declare the dep in pyproject, or add `# noqa: fallback-import` on the\n"
        "# try: line with a one-line reason.\n"
        "#\n"
        "# LOWER a count (re-run `--update-baseline`) the moment shims are removed.\n"
        "# NEVER raise a count. Repos not listed default to count=0.\n"
        "#\n"
        "# SSOT: .cursor/rules/standards/no-empty-fallbacks.mdc § 'No try/except\n"
        "# ImportError Fallbacks' + plans/active/harden_grepable_rules_into_ci_gates_2026_06_02.md.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-06-10 — harden_grepable_rules_into_ci_gates Phase 3 (QG STEP 5.94).",
            "repos": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = baseline_file.write_text(header + body, encoding="utf-8")


# ── Scanning ─────────────────────────────────────────────────────────────────


def _is_excluded_path(path: Path) -> bool:
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return True
    posix = path.as_posix()
    if any(frag in posix for frag in EXCLUDE_PATH_FRAGMENTS):
        return True
    name = path.name
    if any(name.startswith(p) for p in TEST_FILE_PREFIXES):
        return True
    return bool(any(name.endswith(s) for s in TEST_FILE_SUFFIXES))


def _iter_py_files(root: Path) -> Iterator[Path]:
    if root.is_file() and root.suffix == ".py" and not _is_excluded_path(root):
        yield root
        return
    for path in root.rglob("*.py"):
        if _is_excluded_path(path):
            continue
        yield path


def _handler_catches(handler: ast.ExceptHandler, names: frozenset[str]) -> bool:
    """True if the handler's exception spec names any of ``names``.

    Handles ``except ImportError:``, ``except (ImportError, OSError):`` and
    dotted forms like ``except builtins.ImportError:``.
    """
    spec = handler.type
    if spec is None:
        return False  # bare except — handled separately by the caller
    candidates: list[ast.expr] = list(spec.elts) if isinstance(spec, ast.Tuple) else [spec]
    for cand in candidates:
        if isinstance(cand, ast.Name) and cand.id in names:
            return True
        if isinstance(cand, ast.Attribute) and cand.attr in names:
            return True
    return False


def _body_has_import(body: list[ast.stmt]) -> bool:
    """True if any statement (recursively) in the try body is an import."""
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return True
    return False


def _body_is_imports_only(body: list[ast.stmt]) -> bool:
    """True if EVERY direct statement in the try body is an import."""
    return bool(body) and all(isinstance(stmt, (ast.Import, ast.ImportFrom)) for stmt in body)


def _line_has_noqa(file_lines: list[str], lineno: int) -> bool:
    if lineno < 1 or lineno > len(file_lines):
        return False
    return NOQA_MARKER in file_lines[lineno - 1].lower()


def find_fallback_imports(source_path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, description)] of fallback-import try/except sites in a file."""
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

    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if not _body_has_import(node.body):
            continue
        if _line_has_noqa(file_lines, node.lineno):
            continue

        catches_import_error = any(_handler_catches(h, IMPORT_ERROR_NAMES) for h in node.handlers)
        catches_broad = any(h.type is None or _handler_catches(h, BROAD_ERROR_NAMES) for h in node.handlers)

        if catches_import_error:
            violations.append((node.lineno, "try/except ImportError|ModuleNotFoundError around import"))
        elif catches_broad and _body_is_imports_only(node.body):
            violations.append((node.lineno, "imports-only try body with broad except (hidden import fallback)"))

    return sorted(violations)


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[tuple[str, int, str]]  # (repo-relative-file, line, description)


def scan_repo(scan_root: Path, repo_name: str, repo_root: Path | None = None) -> RepoScan:
    rel_base = repo_root if repo_root is not None else scan_root
    sites: list[tuple[str, int, str]] = []
    for py in _iter_py_files(scan_root):
        for lineno, desc in find_fallback_imports(py):
            rel = py.relative_to(rel_base).as_posix() if py.is_relative_to(rel_base) else py.as_posix()
            sites.append((rel, lineno, desc))
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    """Return [(repo_name, scan_root)]. --scope → that repo only (optionally
    narrowed to --source-dir under it). Else every immediate git-repo sub-dir."""
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_no_fallback_imports] --scope {scope!r} not a dir under {workspace_root}", file=sys.stderr)
            return []
        scan_root = repo_root / source_dir if source_dir else repo_root
        if not scan_root.exists():
            scan_root = repo_root
        return [(scope, scan_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in EXCLUDE_DIR_NAMES or child.name.startswith("."):
            continue
        if (child / ".git").exists():
            out.append((child.name, child))
    return out


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="try/except-ImportError fallback-import ratchet (QG STEP 5.94).")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name (per-repo QG mode).")
    parser.add_argument(
        "--source-dir", default=None, help="Sub-dir under --scope to narrow the scan to (e.g. the package dir)."
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed counts (clamped DOWN — never raised).",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=None,
        help="Override the baseline yaml path (unit tests only).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline_file: Path | None = args.baseline_file
    baseline = load_baseline(baseline_file)
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_no_fallback_imports] no repos in scope.", file=sys.stderr)
        return 0  # nothing to check — not a failure

    observed: dict[str, int] = {}
    failures: list[str] = []
    info_lines: list[str] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name if (workspace_root / repo_name).is_dir() else scan_root
        scan = scan_repo(scan_root, repo_name, repo_root=repo_root)
        observed[repo_name] = scan.count
        allowed = baseline.allowed(repo_name)
        if scan.count > allowed:
            over = scan.sites[allowed:] if allowed < len(scan.sites) else scan.sites
            sites_str = "; ".join(f"{f}:{ln}" for f, ln, _desc in over[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} fallback-import site(s) > baseline {allowed}. "
                f"New/over-baseline site(s): {sites_str}" + (" ..." if len(over) > 20 else "")
            )
        elif scan.count < allowed:
            info_lines.append(
                f"[WARN] {repo_name}: {scan.count} < baseline {allowed} — ratchet the baseline DOWN "
                f"(re-run `--update-baseline`)."
            )
        else:
            info_lines.append(f"[OK]   {repo_name}: {scan.count} (== baseline)")

    if args.update_baseline:
        write_baseline(observed, baseline, baseline_file)
        print(f"[check_no_fallback_imports] baseline updated at {baseline_file or _baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n→ Import the dependency directly + declare it in pyproject.toml — never a try/except "
            "ImportError fallback shim (fail LOUD at import time). For a genuinely-optional, documented "
            "extra add `# noqa: fallback-import` on the try: line with a one-line reason. SSOT: "
            ".cursor/rules/standards/no-empty-fallbacks.mdc + harden_grepable_rules_into_ci_gates_2026_06_02.md. "
            "Baseline: unified-trading-pm/scripts/quality_gates/no_fallback_imports_baseline.yaml "
            "(NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
