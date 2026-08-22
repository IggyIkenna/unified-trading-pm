#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP — MDPS bar ``available_at`` stamping discipline.

Enforces CLAUDE.md "available_at is per-row, write-time, equal to
live-pipeline-arrival" rule's bar-shape sub-section (codified 2026-05-11):
every MDPS-emitted bar's ``available_at`` must be stamped via the canonical
helper :func:`market_data_processing_service.app.core.canonical_writer.
_stamp_candle_available_at`, NEVER synthesised inline from a `timestamp`
plus a timeframe arithmetic expression.

Why this exists
---------------
The pre-2026-05-11 MDPS bug (off-by-one timeframe overshoot, fixed in
market-data-processing-service@``f004e12`` + issue doc
``plans/active/issues/mdps_canonical_writer_off_by_one_tf_2026_05_11.md``)
arose because `_stamp_candle_available_at` assumed `timestamp = t_open`
when the MDPS aggregator convention is `timestamp = t_close`. The fix was
a one-line correction, but the root failure mode was: there's no static
guard that an `available_at` column assignment goes through the canonical
helper. A future caller could re-introduce the bug by:

* Inlining a fresh `df["available_at"] = df["timestamp"] + tf_delta +
  latency_delta` somewhere new.
* Calling `_stamp_candle_available_at` then over-writing `available_at`
  with a hand-rolled expression.
* Synthesising a per-row `available_at` in a per-asset-group adapter without
  going through canonical_writer.

The Phase 0.5 runtime write-gate (``_validate_stamped_candle_bar_boundary``)
catches contract violations at write-time, but only on the
`_stamp_candle_available_at` code path. This static check ensures every
`available_at` assignment in MDPS source actually goes through that helper
(or is one of the canonical helper's own implementation lines).

How it works
------------
1. AST-walks every ``.py`` file under the given source dir(s) (skipping
   venvs / build artefacts / archived trees / scripts/ / tests/).
2. For each file, collects every assignment statement whose left-hand side
   is ``<expr>["available_at"]`` (the canonical pattern for stamping a
   DataFrame column).
3. Whitelists 4 contexts:
   * The canonical helper itself: file path ends in
     ``app/core/canonical_writer.py`` AND the assignment is inside
     ``_stamp_candle_available_at`` / ``_validate_stamped_candle_bar_boundary``.
   * Lines containing ``# QG-allow: mdps-bar-available-at`` (escape hatch
     for sub-package internals that legitimately need direct access — none
     today; the marker exists for future-proofing per CLAUDE.md "Clear
     context = implement, don't ask" + the workspace `# QG-BYPASS:` precedent).
   * Test files (already excluded by directory scope).
   * Migration scripts (already excluded by directory scope).
4. Any non-whitelisted `available_at` assignment is an ERROR + file:line +
   the canonical helper path as the successor.

The check is **MDPS-scoped**: features-* services + execution-service + other
consumers READ `available_at` (and validate lookahead-bias against it) but
don't write it on the bar surface. CeFi tick stamping uses
``stamp_available_at_cefi_tick`` in UTL — caught by the CeFi adapter Phase 1
review, not this gate. Sports / prediction stamping has its own per-source
helpers + the ``StreamingParquetWriter.enforce_available_at`` write-time
gate (UTL@``f7b704fd``).

Reference: plans/active/available_at_lookahead_bias_completion_2026_05_08.md
Phase 0.6.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# ── Constants ────────────────────────────────────────────────────────────────


#: Helper functions inside `canonical_writer.py` allowed to write
#: `available_at` directly (the canonical helper + its private validator
#: companion). Any other write in MDPS source is a banned bypass.
CANONICAL_WRITER_ALLOWED_FUNCTIONS: Final[frozenset[str]] = frozenset(
    {
        "_stamp_candle_available_at",
        "_validate_stamped_candle_bar_boundary",
    }
)

#: Relative path (from MDPS package root) of the canonical writer module —
#: writes inside CANONICAL_WRITER_ALLOWED_FUNCTIONS within this file are OK.
CANONICAL_WRITER_PATH_SUFFIX: Final[str] = "app/core/canonical_writer.py"

#: Inline escape-hatch comment marker — same shape as workspace
#: ``# QG-BYPASS:`` / ruff-noqa-style precedent.
QG_ALLOW_MARKER: Final[str] = "# QG-allow: mdps-bar-available-at"

#: Top-level dir names to skip when walking. Mirrors the existing
#: `check_banned_placeholder_methods.py` exclusion set (scripts/ + tests/
#: excluded per CLAUDE.md "Schema provenance" rule).
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
        # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
        # older/different snapshot of the same repo's source — scanning one
        # produces false violations for code that doesn't exist in the actual
        # checked-out tree (found live 2026-08-06, same class as the
        # check_manifest_import_alignment.py / test_event_logging.py fixes).
        ".claude",
    }
)

#: Path-fragment patterns that indicate archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)


# ── Data shapes ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Finding:
    """One unauthorised ``available_at`` write surfaced by the scan."""

    repo: str
    file: str  # repo-relative path
    line: int
    enclosing_function: str
    snippet: str


# ── Scanning ─────────────────────────────────────────────────────────────────


def _iter_py_files(scan_root: Path) -> Iterator[Path]:
    """Yield every Python file under ``scan_root`` honouring the exclusion set."""
    for path in scan_root.rglob("*.py"):
        path_str = str(path)
        if any(frag in path_str for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        rel_parts = path.relative_to(scan_root).parts
        if any(part in EXCLUDE_DIR_NAMES for part in rel_parts):
            continue
        yield path


def _enclosing_function_name(node: ast.AST, parents: dict[int, ast.AST]) -> str:
    """Walk up the parent chain to find the innermost enclosing function name.

    Returns ``"<module>"`` if the assignment is at module scope (which would
    itself be unusual for a column assignment — only conceivable in a
    test/migration fixture).
    """
    cur: ast.AST | None = parents.get(id(node))
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur.name
        cur = parents.get(id(cur))
    return "<module>"


def _is_available_at_subscript(target: ast.expr) -> bool:
    """Return True iff ``target`` is the shape ``<anything>["available_at"]``."""
    if not isinstance(target, ast.Subscript):
        return False
    slice_node = target.slice
    # py3.9+: ast.Index removed; ast.Constant directly.
    return bool(isinstance(slice_node, ast.Constant) and slice_node.value == "available_at")


def _scan_file(
    path: Path,
    repo_name: str,
    repo_root: Path,
    canonical_writer_path: Path,
) -> list[Finding]:
    """Walk one ``.py`` file's AST + flag every unauthorised ``available_at`` write."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    # Build parent map so we can find the enclosing FunctionDef for each Assign.
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    source_lines = source.splitlines()
    findings: list[Finding] = []
    rel_path = path.relative_to(repo_root)

    is_canonical_writer_file = path == canonical_writer_path

    for node in ast.walk(tree):
        # ast.Assign covers `df["available_at"] = ...`.
        # ast.AugAssign covers `df["available_at"] += ...` (rare but possible).
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        else:
            continue

        if not any(_is_available_at_subscript(t) for t in targets):
            continue

        enclosing = _enclosing_function_name(node, parents)

        # Whitelist 1: canonical writer's own helpers.
        if is_canonical_writer_file and enclosing in CANONICAL_WRITER_ALLOWED_FUNCTIONS:
            continue

        # Whitelist 2: inline escape-hatch marker on the assignment line.
        line_idx = node.lineno - 1
        line_text = source_lines[line_idx] if 0 <= line_idx < len(source_lines) else ""
        if QG_ALLOW_MARKER in line_text:
            continue

        snippet = line_text.strip()
        findings.append(
            Finding(
                repo=repo_name,
                file=str(rel_path),
                line=node.lineno,
                enclosing_function=enclosing,
                snippet=snippet,
            )
        )
    return findings


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path, Path]]:
    """Resolve which (repo, scan_root, canonical_writer_path) tuples to walk.

    Mirrors the shape of ``check_banned_placeholder_methods._resolve_scopes``
    but adds the canonical_writer path lookup so the AST walker knows which
    file is the allowed-write boundary.
    """
    # Default scope: market-data-processing-service only — that's where bar
    # emission lives. The check has no value outside MDPS.
    repo_name = scope or "market-data-processing-service"
    repo_root = workspace_root / repo_name
    if not repo_root.is_dir():
        return []

    scan_root = repo_root / source_dir if source_dir is not None else repo_root / "market_data_processing_service"
    if not scan_root.is_dir():
        return []

    canonical_writer_path = scan_root / "app" / "core" / "canonical_writer.py"
    return [(repo_name, scan_root, canonical_writer_path)]


# ── Entry point ──────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MDPS bar `available_at` stamping discipline AST-walker.")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument(
        "--scope",
        default=None,
        help="Single repo dir name to scope to. Default = market-data-processing-service.",
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Package sub-dir within the scoped repo (default = market_data_processing_service).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print(f"[check_mdps_bar_available_at_stamping] no source trees to scan under {workspace_root} — skipping.")
        return 0

    all_findings: list[Finding] = []
    for repo_name, scan_root, canonical_writer_path in scopes:
        for py in _iter_py_files(scan_root):
            all_findings.extend(_scan_file(py, repo_name, scan_root, canonical_writer_path))

    if not all_findings:
        print("[check_mdps_bar_available_at_stamping] OK — 0 unauthorised available_at writes.")
        return 0

    for f in all_findings:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  in `{f.enclosing_function}` — "
            f"unauthorised `available_at` write outside the canonical helper.\n"
            f"         {f.snippet}\n"
            f"         Every MDPS-emitted candle's `available_at` MUST be stamped via "
            f"`canonical_writer._stamp_candle_available_at` (`timestamp + emission_latency`), "
            f"NOT inline.\n"
            f"         Pre-2026-05-11 incident: 1-tf overshoot from inline `+ tf_delta`. "
            f"Issue doc: plans/active/issues/mdps_canonical_writer_off_by_one_tf_2026_05_11.md\n"
            f"         To allowlist a legitimate exception, append `{QG_ALLOW_MARKER}` "
            f"to the assignment line.",
            file=sys.stderr,
        )

    print(
        f"\n[check_mdps_bar_available_at_stamping] FAIL — {len(all_findings)} unauthorised available_at write(s).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
