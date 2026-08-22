#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP 5.89 — ``record_empty(reason=...)`` must use closed-set reasons.

Every ``record_empty()`` / ``record_expected_empty()`` call that passes a literal
string ``reason=`` kwarg must use a value from
``unified_api_contracts.canonical.crosscutting.honest_coverage.EMPTY_CONFIRMED_REASONS``.

Why literal-string focus
------------------------
Calls using enum member access (``reason=EmptyConfirmedReason.EXPECTED_HOLIDAY`` or
``.value``) are type-safe and pass through un-flagged.  Calls using bare string
literals (``reason="EXPECTED_HOLIDAY"`` or ``reason="SOURCE_RETURNED_ZERO"``) are
common at migration/adapter callsites and are the main source of typo-drift.

The UTL runtime already raises ``UnknownEmptyConfirmedReasonError`` at call time,
but this static check catches the error *before* tests run, with precise file:line
attribution.

What it checks
--------------
1. AST-walks every ``.py`` file in the scoped source dir(s).
2. For every ``Call`` node whose ``.func.attr`` is ``record_empty`` or
   ``record_expected_empty``, finds the ``reason=`` keyword argument.
3. If the argument is a string literal: verifies it is in KNOWN_REASONS.
4. If the argument is a blank string (``reason=""``): flags it (legacy path,
   raises ``LegacyBlankErrorReasonError`` at runtime).
5. Attribute accesses (``EmptyConfirmedReason.X``, ``SomeEnum.X.value``) pass
   through — they are validated by the type system.

Exemptions
----------
- Files whose path contains ``/manifest_writer.py`` or ``/test_`` (UTL definition
  site + unit tests that intentionally exercise the error path).
- Per-line: ``# QG-allow: record-empty-reason`` on the call line.

Usage::

    python check_record_empty_reason_closed_set.py --workspace-root <ws> --scope <repo>
    python check_record_empty_reason_closed_set.py --workspace-root <ws>  # all repos
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# Closed set — mirrors EmptyConfirmedReason enum in UAC honest_coverage.py.
# Update here whenever a new member is added to EmptyConfirmedReason.
# ---------------------------------------------------------------------------
KNOWN_REASONS: Final[frozenset[str]] = frozenset(
    {
        "EXPECTED_HOLIDAY",
        "EXPECTED_WEEKEND",
        "EXPECTED_PAUSED_LEAGUE",
        "EXPECTED_PRE_SOURCE_COVERAGE_START",
        "EXPECTED_PAST_SOURCE_COVERAGE_END",
        # Registry-derived ONLY (canonical.coverage_exclusions) — a hand-stamped literal at a
        # record_empty callsite would be an unevidenced out-of-bounds claim, which is
        # review-blocking. Listed here to mirror the enum, not to license direct use.
        "EXPECTED_UPSTREAM_OUT_OF_BOUNDS",
        "EXPECTED_SOURCE_DELIVERY_LAG",
        "EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE",
        "EXPECTED_CHAIN_AGGREGATE",
        "EXPECTED_NOT_ENOUGH_TVL",
        "EXPECTED_NO_MAPPING",
        "EXPECTED_NO_PROVIDER_COVERAGE",
        "EXPECTED_WRITE_GATE_NAN_THRESHOLD_EXCEEDED",
        "EXPECTED_ACQUISITION_PENDING",
        "EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH",
        "EXPECTED_SUBGRAPH_DEINDEXED",
        "EXPECTED_PRE_GENESIS_CHAIN",
        "EXPECTED_PRE_VENUE_LAUNCH",
        "EXPECTED_INSTRUMENT_NOT_LISTED",
        "EXPECTED_INSTRUMENT_DELISTED",
        "EXPECTED_PARTIAL_HALF_DAY",
        "EXPECTED_OUTSIDE_TRADING_HOURS",
        "EXPECTED_OUTSIDE_TRANSFER_WINDOW",
        "EXPECTED_PRE_SEASON",
        "EXPECTED_POST_SEASON",
        "EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE",
        "EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE",
        "EXPECTED_OUT_OF_COVERAGE_WINDOW",
        "EXPECTED_DEPRECATED_DATA_TYPE",
        "EXPECTED_REFDATA_CADENCE_CHANGE",
        "EXPECTED_KNOWN_SOURCE_GAP",
        "EXPECTED_PROTOCOL_PAUSED",
        "EXPECTED_OUTSIDE_PROCESSING_SCOPE",
        "EXPECTED_UPSTREAM_EMPTY",
        "EXPECTED_FIXTURE_POSTPONED",
        "EXPECTED_FIXTURE_CANCELLED",
        "EXPECTED_NO_FIXTURE",
        "EXPECTED_LEGACY_MIGRATION_MISSING_EXPIRY",
        "EXPECTED_NO_FUNDING_RATE_TICKS",
        "EXPECTED_NO_PNL_STREAM",
        "SOURCE_RETURNED_ZERO",
        "STRATEGY_ENGINE_RETURNED_ZERO",
        "NO_INPUT_AVAILABLE",
        "LEG_ABSENT_LEFT",
        "LEG_ABSENT_RIGHT",
    }
)

TARGET_METHODS: Final[frozenset[str]] = frozenset({"record_empty", "record_expected_empty"})

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
        # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
        # older/different snapshot of the same repo's source — scanning one
        # produces false violations for code that doesn't exist in the actual
        # checked-out tree (found live 2026-08-06, same class as the
        # check_manifest_import_alignment.py / test_event_logging.py fixes).
        ".claude",
        "scripts",
    }
)

EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
    "/manifest_writer.py",
    "/test_",
)

WHITELIST_MARKER: Final[str] = "QG-allow: record-empty-reason"


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    method: str
    reason_value: str
    message: str


def _iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if parts & EXCLUDE_DIR_NAMES:
            continue
        s = str(path).replace("\\", "/")
        if any(frag in s for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        yield path


def _check_file(path: Path) -> list[Finding]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    lines = source.splitlines()
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        method_name: str | None = None
        if isinstance(func, ast.Attribute) and func.attr in TARGET_METHODS:
            method_name = func.attr
        elif isinstance(func, ast.Name) and func.id in TARGET_METHODS:
            method_name = func.id
        if method_name is None:
            continue

        reason_kw: ast.keyword | None = next(
            (kw for kw in node.keywords if kw.arg == "reason"),
            None,
        )
        if reason_kw is None:
            continue

        if not isinstance(reason_kw.value, ast.Constant) or not isinstance(reason_kw.value.value, str):
            continue

        reason_str: str = reason_kw.value.value
        call_line = node.lineno

        line_text = lines[call_line - 1] if call_line <= len(lines) else ""
        if WHITELIST_MARKER in line_text:
            continue

        if reason_str == "":
            findings.append(
                Finding(
                    file=str(path),
                    line=call_line,
                    method=method_name,
                    reason_value="<blank>",
                    message=(
                        "blank reason string — raises LegacyBlankErrorReasonError at runtime;"
                        " pass a typed reason from EMPTY_CONFIRMED_REASONS"
                    ),
                )
            )
        elif reason_str not in KNOWN_REASONS:
            findings.append(
                Finding(
                    file=str(path),
                    line=call_line,
                    method=method_name,
                    reason_value=reason_str,
                    message=(
                        f"unknown reason {reason_str!r} — not in EMPTY_CONFIRMED_REASONS;"
                        " add to EmptyConfirmedReason enum in UAC honest_coverage.py"
                    ),
                )
            )

    return findings


def _collect_source_dirs(workspace_root: Path, scope: str | None) -> list[Path]:
    repos = (
        [scope] if scope else [d.name for d in workspace_root.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )
    dirs: list[Path] = []
    for repo in repos:
        repo_path = workspace_root / repo
        if not repo_path.is_dir():
            continue
        for candidate in (
            "unified_trading_library",
            "unified_api_contracts",
            "market_tick_data_service",
            "market_data_processing_service",
            "instruments_service",
            "features_service",
            "ml_training_service",
            "ml_inference_service",
            "strategy_service",
            "execution_service",
            "deployment_api",
            "deployment_service",
        ):
            src = repo_path / candidate
            if src.is_dir():
                dirs.append(src)
        if (not dirs or dirs[-1].parent != repo_path) and repo_path.is_dir():
            dirs.append(repo_path)
    return dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="STEP 5.85: record_empty reason closed-set check")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", help="Repo dir name (relative to workspace-root) to limit scan")
    parser.add_argument("--source-dir", type=Path, help="Override source dir (absolute or relative to CWD)")
    args = parser.parse_args()

    if args.source_dir:
        source_dirs = [args.source_dir.resolve()]
    else:
        workspace_root = args.workspace_root.resolve()
        source_dirs = _collect_source_dirs(workspace_root, args.scope)

    all_findings: list[Finding] = []
    for src in source_dirs:
        if not src.is_dir():
            continue
        for py_file in _iter_py_files(src):
            all_findings.extend(_check_file(py_file))

    if not all_findings:
        print("[STEP 5.89] OK: all record_empty/record_expected_empty calls use closed-set reasons")
        sys.exit(0)

    for f in all_findings:
        print(f"[ERROR] {f.file}:{f.line}: {f.method}(reason={f.reason_value!r}) — {f.message}")
    print(f"\n[STEP 5.89] FAIL: {len(all_findings)} unknown/blank reason literal(s) found")
    sys.exit(1)


if __name__ == "__main__":
    main()
