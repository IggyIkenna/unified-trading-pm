#!/usr/bin/env python3
# Epic: instruments_master
# Lifecycle: permanent
# Delete-when: NA
"""QG guard — no NEW ``URDI`` references in instruments-service source.

Enforces the ruling in
``plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md`` (finding 369,
corrected 2026-07-12): ``urdi_reference_provider.py`` is grep-confirmed
LOAD-BEARING — imported by the engine orchestrator, ``reference_data`` utils, and
six production adapters — so it is **NOT** a phantom name to rename away. The
earlier "audit + rename in instruments-service" follow-up was itself wrong (an
``rg URDI`` → 0-hits reading; the module is the LIVE external-fetch spine). The
correct, standing guard is the OPPOSITE of a rename: freeze the existing
load-bearing footprint and prevent NEW ``URDI`` refs from proliferating.

This is that grep-based CI guard. It is a per-repo **shrinking count ratchet**
(same shape as QG STEP 5.94/5.95/5.105): the baseline grandfathers the current,
audited ``URDI``-matching source lines; a repo whose live count EXCEEDS its
baseline fails CI (a NEW ``URDI`` reference landed). It never asks anyone to
touch the existing spine — only to not grow it.

What is counted: every ``.py`` source line containing the literal token ``URDI``
(case-sensitive acronym, substring match — exactly what ``rg URDI`` finds), under
the scan root, EXCLUDING tests / venvs / build / archived trees. A line carrying
the per-line escape ``# QG-allow: urdi-legacy`` (with a one-line reason) is not
counted — use it for a genuinely-required new reference to the load-bearing spine
(e.g. a new production adapter wiring into ``urdi_reference_provider``).

Scope: this guard is deliberately instruments-service-ONLY (the repo owning the
load-bearing module). It is wired into ``instruments-service/scripts/quality-gates.sh``
alone — NOT the shared base-service.sh — because ``URDI`` is a legitimate concept
referenced in other repos' code/docs (UAC, UTL, execution-service, …) and a
workspace-wide zero-default would flag those. Repos not in the baseline default
to count=0, so the checker no-ops for any scope it wasn't seeded for.

Usage::

    # per-repo (run by instruments-service/scripts/quality-gates.sh):
    python check_no_new_urdi_refs.py --workspace-root <ws> --scope instruments-service

    # ratchet the baseline DOWN after removing refs:
    python check_no_new_urdi_refs.py --workspace-root <ws> --scope instruments-service --update-baseline

Exit codes: 0 = clean / at-or-below baseline; 1 = over baseline; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: The literal token that marks a URDI reference (case-sensitive acronym — a
#: substring match, exactly what ``rg URDI`` reports).
URDI_TOKEN: Final[str] = "URDI"

#: Per-line exemption marker (with a one-line reason) — a required new reference
#: to the load-bearing spine. A line carrying this is not counted.
QG_ALLOW_MARKER: Final[str] = "QG-allow: urdi-legacy"

#: Top-level dir names to skip when walking (mirrors check_no_fallback_imports.py).
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
        ".claude",
        ".cursor",
    }
)

#: Path-fragment patterns that indicate archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)

#: Test-file basename patterns (skipped — the source-footprint intent is production code).
TEST_FILE_PREFIXES: Final[tuple[str, ...]] = ("test_",)
TEST_FILE_SUFFIXES: Final[tuple[str, ...]] = ("_test.py",)


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "no_new_urdi_refs_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts of URDI-matching source lines."""

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
    existing baseline (a higher count means a new reference landed; delete it or
    mark it, don't bake it in)."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        if repo not in counts:
            # Not scanned this run (scoped --update-baseline) — carry the existing
            # row forward verbatim (treating unobserved as 0 + down-clamp would zero
            # the row; same defect class guarded against in check_no_fallback_imports).
            merged[repo] = {"count": existing.allowed(repo)}
            continue
        observed = int(counts[repo])
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for the no-NEW-URDI-refs grep guard (instruments-service).\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of\n"
        "# `.py` source lines containing the literal token `URDI` (tests excluded)\n"
        "# the guard tolerates in that repo. A repo whose live count EXCEEDS its\n"
        "# baseline fails CI — a NEW URDI reference landed. The load-bearing\n"
        "# `urdi_reference_provider.py` spine is grandfathered here on purpose; the\n"
        "# guard exists to STOP proliferation, NOT to rename the existing module\n"
        "# (finding 369, corrected 2026-07-12 — the module is the LIVE fetch spine).\n"
        "#\n"
        "# For a genuinely-required new reference to the spine (e.g. a new production\n"
        "# adapter wiring into it), add `# QG-allow: urdi-legacy` on the line with a\n"
        "# one-line reason. LOWER a count (re-run `--update-baseline`) the moment\n"
        "# refs are removed. NEVER raise a count. Repos not listed default to count=0\n"
        "# (this guard is instruments-service-ONLY — wired into that repo's\n"
        "# quality-gates.sh, not the shared base-service.sh).\n"
        "#\n"
        "# SSOT: plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md (finding 369).\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-07-31 — codex_vs_repo_docs_ssot_audit finding 369 grep guard.",
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


def find_urdi_refs(source_path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, stripped-line)] of URDI-referencing source lines in a file.

    A line carrying the ``# QG-allow: urdi-legacy`` escape is not returned.
    """
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if URDI_TOKEN not in line:
            continue
        if QG_ALLOW_MARKER in line:
            continue
        hits.append((lineno, line.strip()))
    return hits


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[tuple[str, int, str]]  # (repo-relative-file, line, stripped-line)


def scan_repo(scan_root: Path, repo_name: str, repo_root: Path | None = None) -> RepoScan:
    rel_base = repo_root if repo_root is not None else scan_root
    sites: list[tuple[str, int, str]] = []
    for py in _iter_py_files(scan_root):
        for lineno, text in find_urdi_refs(py):
            rel = py.relative_to(rel_base).as_posix() if py.is_relative_to(rel_base) else py.as_posix()
            sites.append((rel, lineno, text))
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    """Return [(repo_name, scan_root)]. --scope → that repo only (optionally
    narrowed to --source-dir under it). Else every immediate git-repo sub-dir."""
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_no_new_urdi_refs] --scope {scope!r} not a dir under {workspace_root}", file=sys.stderr)
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
    parser = argparse.ArgumentParser(description="no-NEW-URDI-refs grep guard (instruments-service).")
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
        print("[check_no_new_urdi_refs] no repos in scope.", file=sys.stderr)
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
            sites_str = "; ".join(f"{f}:{ln}" for f, ln, _txt in over[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} URDI source-ref line(s) > baseline {allowed}. "
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
        print(f"[check_no_new_urdi_refs] baseline updated at {baseline_file or _baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n→ `urdi_reference_provider.py` is the load-bearing external-fetch spine — do NOT rename it. "
            "But do NOT grow the URDI footprint either: a NEW URDI reference landed above the grandfathered "
            "baseline. Remove it, or (if it is a genuinely-required new wiring into the spine) add "
            "`# QG-allow: urdi-legacy` on the line with a one-line reason. SSOT: "
            "plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md (finding 369). "
            "Baseline: unified-trading-pm/scripts/quality_gates/no_new_urdi_refs_baseline.yaml "
            "(NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
