#!/usr/bin/env python3
"""QG STEP 5.92 — bucket-name string-concat guardrail.

Enforces the bucket-name SSOT rule introduced in
``bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`` Phase 1:
no production source may build a ``market-data-tick-*`` or
``instruments-store-*`` bucket name by string concatenation — every bucket
lookup MUST go through
``unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)``.

String-concat bucket names are exactly how the workspace accumulated dual-write
drift (RC1 in the plan: ``get_bucket_name(f"market-data-tick-{ag}")`` missed the
yaml-delegation map and fell through to the legacy flat name for EVERY live
writer across cefi/defi/tradfi/sports/prediction).

**What this gate detects** (production source only; scripts/ + tests/ excluded):

- ``f"market-data-tick-{...``  — f-string with the literal tick-bucket prefix
- ``f"instruments-store-{...`` — f-string with the literal instruments-store prefix
- ``"market-data-tick-" + ...`` — explicit string concatenation
- ``"instruments-store-" + ...`` — same

Lines carrying ``# noqa: bucket-concat`` are skipped (intentional, audited usage
— e.g. the canonical resolver itself, migration scripts that legitimately compare
legacy vs canonical names).

**Shape** — baseline ratchet (NOT zero-tolerance from day 1): the checker loads
``bucket_name_string_concat_baseline.yaml`` (per-repo count of KNOWN existing
occurrences) and fails only when a repo's live count EXCEEDS its baseline (a NEW
occurrence landed). A repo BELOW its baseline produces a warning (ratchet down).

Usage::

    # per-repo (run by base-service.sh STEP 5.92):
    python check_bucket_name_string_concat.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_bucket_name_string_concat.py --workspace-root <ws>

    # ratchet baseline DOWN after migration:
    python check_bucket_name_string_concat.py --workspace-root <ws> --update-baseline
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

# ── Constants ─────────────────────────────────────────────────────────────────

NOQA_MARKER: Final[str] = "noqa: bucket-concat"

#: Patterns that indicate a bucket name is being built by string concatenation.
#: Matches f-strings with the literal prefix or explicit + concatenation.
_CONCAT_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"""f['"]market-data-tick-\{"""),
    re.compile(r"""f['"]instruments-store-\{"""),
    re.compile(r""""market-data-tick-"\s*\+"""),
    re.compile(r""""instruments-store-"\s*\+"""),
    re.compile(r"""'market-data-tick-'\s*\+"""),
    re.compile(r"""'instruments-store-'\s*\+"""),
]

#: Directories to skip entirely when walking a repo.
_SKIP_DIRS: Final[frozenset[str]] = frozenset(
    {
        "tests",
        "test",
        "scripts",
        ".venv",
        ".venv-workspace",
        "__pycache__",
        "node_modules",
        "build",
        "dist",
        "archive",
        ".git",
    }
)

#: Files to skip by name pattern (migration/audit scripts are explicitly exempt).
_SKIP_FILE_RE: Final[re.Pattern[str]] = re.compile(
    r"(migrat|audit_|migrate_legacy|create.tarballs|check_inline_bucket_uri)",
    re.IGNORECASE,
)

BASELINE_FILENAME: Final[str] = "bucket_name_string_concat_baseline.yaml"


# ── AST-based docstring detection ─────────────────────────────────────────────


def _docstring_line_ranges(source: str) -> frozenset[int]:
    """Return the set of 1-indexed line numbers that are inside a docstring."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return frozenset()

    ranges: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue
        val = node.value
        if not isinstance(val, ast.Constant) or not isinstance(val.value, str):
            continue
        start = node.lineno
        end = node.end_lineno or node.lineno
        ranges.update(range(start, end + 1))
    return frozenset(ranges)


# ── Per-file scanning ─────────────────────────────────────────────────────────


@dataclass
class Hit:
    file: Path
    lineno: int
    line: str


def _scan_file(py_file: Path) -> list[Hit]:
    """Return all bucket-name concat hits in *py_file* (excluding docstrings)."""
    try:
        source = py_file.read_text(errors="replace")
    except OSError:
        return []

    docstring_lines = _docstring_line_ranges(source)
    hits: list[Hit] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if lineno in docstring_lines:
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if NOQA_MARKER in line:
            continue
        for pat in _CONCAT_PATTERNS:
            if pat.search(line):
                hits.append(Hit(file=py_file, lineno=lineno, line=line.rstrip()))
                break
    return hits


def _should_skip_file(py_file: Path, repo_root: Path) -> bool:
    rel = py_file.relative_to(repo_root)
    parts = rel.parts
    if any(p in _SKIP_DIRS for p in parts):
        return True
    if py_file.name.startswith("test_") or py_file.name.endswith("_test.py"):
        return True
    return bool(_SKIP_FILE_RE.search(str(py_file)))


def _scan_repo(repo_root: Path) -> list[Hit]:
    hits: list[Hit] = []
    for py_file in sorted(repo_root.rglob("*.py")):
        if _should_skip_file(py_file, repo_root):
            continue
        hits.extend(_scan_file(py_file))
    return hits


# ── Baseline helpers ───────────────────────────────────────────────────────────


def _load_baseline(pm_root: Path) -> dict[str, int]:
    baseline_path = pm_root / "scripts" / "quality_gates" / BASELINE_FILENAME
    if not baseline_path.exists():
        return {}
    data = yaml.safe_load(baseline_path.read_text()) or {}
    repos = data.get("repos") or {}
    return {repo: int(info.get("count", 0)) for repo, info in repos.items()}


def _save_baseline(pm_root: Path, counts: dict[str, int]) -> None:
    baseline_path = pm_root / "scripts" / "quality_gates" / BASELINE_FILENAME
    existing_data = yaml.safe_load(baseline_path.read_text()) if baseline_path.exists() else {}
    if not isinstance(existing_data, dict):
        existing_data = {}
    existing_repos: dict[str, dict] = existing_data.get("repos") or {}
    for repo, count in counts.items():
        existing_repos[repo] = {"count": count}
    existing_data["repos"] = dict(sorted(existing_repos.items()))
    baseline_path.write_text(yaml.dump(existing_data, default_flow_style=False, sort_keys=False))


# ── Main ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--workspace-root", required=True, type=Path, help="Workspace root containing all repos as subdirs"
    )
    parser.add_argument(
        "--scope", type=str, default=None, help="Restrict check to this repo dir name (e.g. execution-service)"
    )
    parser.add_argument(
        "--update-baseline", action="store_true", help="Write current counts to the baseline file and exit 0"
    )
    args = parser.parse_args(argv)

    ws = args.workspace_root.resolve()
    pm_root = ws / "unified-trading-pm"

    baseline = _load_baseline(pm_root) if pm_root.exists() else {}

    # Collect repos to scan
    if args.scope:
        repo_dirs = [ws / args.scope]
    else:
        repo_dirs = sorted(
            d for d in ws.iterdir() if d.is_dir() and not d.name.startswith(".") and d.name != "unified-trading-pm"
        )

    all_hits: dict[str, list[Hit]] = {}
    for repo_dir in repo_dirs:
        if not repo_dir.is_dir():
            continue
        hits = _scan_repo(repo_dir)
        if hits:
            all_hits[repo_dir.name] = hits

    if args.update_baseline:
        counts = {repo: len(hits) for repo, hits in all_hits.items()}
        _save_baseline(pm_root, counts)
        print(f"[OK] Baseline updated: {counts}")
        return 0

    # Compare against baseline
    exit_code = 0
    for repo, hits in all_hits.items():
        live_count = len(hits)
        allowed = baseline.get(repo, 0)
        if live_count > allowed:
            print(
                f"[FAIL] {repo}: {live_count} bucket-name string-concat occurrence(s) "
                f"({live_count - allowed} above baseline={allowed})."
            )
            for h in hits:
                rel = h.file.relative_to(ws / repo)
                print(f"  {rel}:{h.lineno}: {h.line.strip()}")
            exit_code = 1
        elif live_count < allowed:
            print(
                f"[WARN] {repo}: {live_count} occurrence(s) — BELOW baseline {allowed}; "
                f"run --update-baseline to ratchet down."
            )
        else:
            print(f"[OK]   {repo}: {live_count} occurrence(s) (within baseline)")

    if args.scope and args.scope not in all_hits:
        # No hits for the scoped repo — check against baseline
        repo = args.scope
        allowed = baseline.get(repo, 0)
        if allowed > 0:
            print(f"[WARN] {repo}: 0 occurrence(s) — BELOW baseline {allowed}; run --update-baseline to ratchet down.")
        else:
            print(f"[OK]   {repo}: 0 bucket-name string-concat occurrences")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
