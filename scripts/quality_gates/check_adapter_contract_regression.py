#!/usr/bin/env python3
"""QG STEP 5.83 — adapter contract-call regression ratchet (per-file minimums).

Enforces CLAUDE.md "Every adapter MUST classify errors via UAC ``classify_venue_error()``
+ emit ``ADAPTER_FETCH_FAILED``" + the manifest-emission contract (``record_captured`` /
``record_empty`` / ``record_failed``) AT THE FILE LEVEL — once a file ships N contract
calls, subsequent commits MUST keep ≥N calls. Catches the regression class demonstrated
2026-05-20 by ``execution-service@774602ea8`` + ``@6ba53d526`` (lint/method-size sweeps
silently wiping 31 ``classify_venue_error`` calls from
``sports_execution/adapters/exchanges/kalshi.py`` + ``polymarket_clob.py``).

Reference incident: ``plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md``.
The ``no_silent_absence_handlers.sh`` check ensures ``≥1`` call per file; this check
locks in the CURRENT count (file-level ratchet — N stays ≥ previously-observed N).

Shape (mirrors ``check_inline_bucket_uri.py``):

  1. Load ``adapter_contract_baseline.yaml`` — per-file minimum contract-call count
     captured at last ``--regenerate-baseline`` run.
  2. Walk workspace repos (every immediate sub-dir of ``--workspace-root`` with a
     ``.git``), counting per-file occurrences of the 5 contract patterns:
     ``classify_venue_error|ADAPTER_FETCH_FAILED|record_captured|record_empty|record_failed``.
  3. For each baseline-listed file: if observed count < baseline → FAIL (exit 1).
     If observed ≥ baseline → OK. New files (not in baseline) report as INFO; operator
     decides when to add them to the baseline via ``--regenerate-baseline``.

Unlike ``check_inline_bucket_uri`` (per-repo total count, shrinking ratchet), this
check is **per-file** + **non-shrinking** — the baseline only RAISES when the operator
explicitly opts in via ``--regenerate-baseline`` after a legit refactor that intentionally
adds contract calls. A lower count is always a FAIL (regression).

Usage::

    # workspace-wide scan (run by per-service quality-gates.sh):
    python check_adapter_contract_regression.py --workspace-root <ws>

    # regenerate baseline (after legit refactor that intentionally changes counts):
    python check_adapter_contract_regression.py --workspace-root <ws> --regenerate-baseline
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: The adapter-contract patterns. Combined into a single regex for one-pass counting.
#: ``record_zero_rows`` (added 2026-06-05, plan §A10d) is the sanctioned honest-absence write path
#: — handlers route "source succeeded, zero rows" through it instead of a bare
#: ``record_empty(SOURCE_RETURNED_ZERO)``; counting it keeps the contract-call total stable across
#: that rename (and recognises it as a first-class manifest-emission contract call).
CONTRACT_PATTERNS: Final[tuple[str, ...]] = (
    "classify_venue_error",
    "ADAPTER_FETCH_FAILED",
    "record_captured",
    "record_empty",
    "record_zero_rows",
    "record_failed",
)

_CONTRACT_RE: Final[re.Pattern[str]] = re.compile("|".join(CONTRACT_PATTERNS))

#: Top-level dir names to skip when walking. Mirrors check_inline_bucket_uri.
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

#: Test-file basename patterns (also skipped).
TEST_FILE_PREFIXES: Final[tuple[str, ...]] = ("test_",)
TEST_FILE_SUFFIXES: Final[tuple[str, ...]] = ("_test.py",)


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "adapter_contract_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-file minimum contract-call count."""

    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def required(self, file_key: str) -> int:
        return int(self.counts.get(file_key, 0))

    def has(self, file_key: str) -> bool:
        return file_key in self.counts


def load_baseline() -> Baseline:
    path = _baseline_path()
    if not path.exists():
        return Baseline()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    files_raw = raw.get("baseline") or {}
    counts: dict[str, int] = {}
    for file_key, val in files_raw.items():
        if isinstance(val, dict):
            counts[str(file_key)] = int(val.get("count", 0))
        else:
            counts[str(file_key)] = int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline) -> None:
    """Persist a new baseline. ``--regenerate-baseline`` overwrites; the operator
    is responsible for ensuring HEAD is at the post-restoration / post-legit-refactor
    state before invoking."""
    path = _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    for file_key in sorted(counts):
        observed = int(counts[file_key])
        if observed > 0:
            merged[file_key] = {"count": observed}
    header = (
        "# Baseline for QG STEP 5.83 — adapter contract-call regression ratchet (per-file).\n"
        "#\n"
        "# Each entry: `baseline[<workspace-relative-file>].count` = minimum required\n"
        "# count of the 5 adapter-contract patterns in that file:\n"
        "#   classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty | record_failed\n"
        "#\n"
        "# The gate fails (exit 1) for any file whose live count is BELOW its baseline.\n"
        "# Files NOT listed are reported as INFO on a workspace scan; the operator\n"
        "# decides when to add them via `--regenerate-baseline`.\n"
        "#\n"
        "# This is a NON-SHRINKING ratchet. A lower count is always a regression. To\n"
        "# RAISE a baseline (legit refactor intentionally adds contract calls) or to\n"
        "# LOWER a baseline (file was deleted / contract calls intentionally consolidated):\n"
        "# re-run with `--regenerate-baseline` from a known-good HEAD.\n"
        "#\n"
        "# DO NOT manually edit; the file is auto-generated.\n"
        "#\n"
        '# SSOT for WHY: CLAUDE.md "Every adapter MUST classify errors via UAC `classify_venue_error()`\n'
        "# + emit `ADAPTER_FETCH_FAILED`" + " + " + "manifest emission contract (record_*).\n"
        "# Reference incident: plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md\n"
        "# (execution-service@774602ea8 + @6ba53d526 wiped 31 calls from kalshi.py + polymarket_clob.py).\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-05-20 (slot 1) — lint_sweep_774602ea8 regression-audit Phase 1.",
            "baseline": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = path.write_text(header + body, encoding="utf-8")


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
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        if _is_excluded_path(rel):
            continue
        if _is_excluded_path(path):
            continue
        yield path


def count_contract_calls_in_file(path: Path) -> int:
    """Return the number of adapter-contract-pattern occurrences in ``path``.

    Counts all matches via single combined regex (one pass). Comments and docstrings
    are intentionally NOT filtered out — the contract patterns are unique enough
    (e.g. ``ADAPTER_FETCH_FAILED`` is an event constant; ``classify_venue_error``
    is a function name) that mentions in comments are vanishingly rare AND any
    deliberate comment-mention still satisfies the "this file references the
    contract" intent. If false-positive rate becomes a problem later, switch to
    AST-walk per ``check_inline_bucket_uri.py`` v2.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    return len(_CONTRACT_RE.findall(source))


@dataclass(frozen=True)
class FileScan:
    file_key: str  # workspace-relative POSIX path
    count: int


def scan_workspace(workspace_root: Path) -> list[FileScan]:
    """Walk every immediate sub-dir with a ``.git`` + return per-file counts."""
    results: list[FileScan] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in EXCLUDE_DIR_NAMES or child.name.startswith("."):
            continue
        if not (child / ".git").exists():
            continue
        for py in _iter_py_files(child):
            count = count_contract_calls_in_file(py)
            if count == 0:
                continue  # files with zero contract calls are not tracked
            rel = py.relative_to(workspace_root).as_posix()
            results.append(FileScan(file_key=rel, count=count))
    return results


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Adapter contract-call regression ratchet (QG STEP 5.83).",
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument(
        "--regenerate-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed counts (RAISES or LOWERS as needed).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    regenerate = bool(args.regenerate_baseline)
    baseline = load_baseline()

    scans = scan_workspace(workspace_root)
    observed: dict[str, int] = {s.file_key: s.count for s in scans}

    if regenerate:
        write_baseline(observed, baseline)
        print(f"[check_adapter_contract_regression] baseline rewritten at {_baseline_path()}")
        print(f"[check_adapter_contract_regression] {len(observed)} file(s) recorded.")
        for file_key in sorted(observed):
            print(f"  {file_key}: {observed[file_key]}")
        return 0

    failures: list[str] = []
    new_files: list[str] = []
    ok_count = 0

    for file_key, required in sorted(baseline.counts.items()):
        actual = observed.get(file_key, 0)
        if actual < required:
            absent = " (file missing or renamed)" if file_key not in observed else ""
            failures.append(
                f"[FAIL] {file_key}: {actual} contract calls < baseline {required}{absent}. "
                f"Patterns tracked: {' | '.join(CONTRACT_PATTERNS)}."
            )
        else:
            ok_count += 1

    for file_key in sorted(observed):
        if not baseline.has(file_key):
            new_files.append(f"[INFO] new file (not in baseline): {file_key}: {observed[file_key]} contract calls")

    for f in failures:
        print(f, file=sys.stderr)
    if new_files and not failures:
        for n in new_files[:10]:
            print(n)
        if len(new_files) > 10:
            print(f"[INFO] ... + {len(new_files) - 10} more new file(s). Run with --regenerate-baseline to lock in.")

    if failures:
        print(
            f"\n[check_adapter_contract_regression] {len(failures)} file(s) regressed below baseline.\n"
            "→ Restore the missing contract calls (classify_venue_error / ADAPTER_FETCH_FAILED /\n"
            "  record_captured / record_empty / record_failed) — see CLAUDE.md 'Every adapter MUST\n"
            "  classify errors via UAC classify_venue_error()'.\n"
            "→ Reference incident: plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md\n"
            "  (lint sweep wiped 31 calls from kalshi.py + polymarket_clob.py — caught manually 2026-05-20).\n"
            "→ Baseline: unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml\n"
            "  (re-run with --regenerate-baseline ONLY after legit refactor that intentionally\n"
            "  changes counts — never to mask a regression).",
            file=sys.stderr,
        )
        return 1

    print(
        f"[check_adapter_contract_regression] OK — {ok_count} baselined file(s) at or above minimum"
        + (f"; {len(new_files)} new file(s) not yet baselined." if new_files else ".")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
