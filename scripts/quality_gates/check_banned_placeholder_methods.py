#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP — banned NaN-placeholder / bypass-``record_captured`` methods.

Enforces CLAUDE.md "Honest absence vs fake placeholders" + "No double SSOT in
data-saving methodology" + "Four-category empty-output decision" — the
``_create_empty_output()``-style placeholder methods (which emit NaN-OHLC
placeholder bars that LOOK populated and pass the manifest as ``captured``) are
**banned** from ``base_adapter`` and any equivalent base class. Reference
incidents: 2026-05-05 MDPS 1440-NaN-bar (placeholder bars persisted for years
before hand-inspection caught them); Track D audit 2026-05-11.

The banned name-set is deliberately scoped to names that *describe the act of
synthesising a fake empty/closed/placeholder candle* (``_create_empty_output`` /
``_create_full_day_empty_output`` / ``_create_closed_market_candle`` /
``_maybe_write_vix_gap_placeholder``) — a new method with one of those names is
almost certainly the banned shape. ``_handle_empty_tick_data`` was in the set on
day 1 (2026-05-11 @PM a4512ed3) because the pre-reform MDPS TRADFI branch
synthesised NaN candles inside it; writegate Phase 2.A P0-2 surgery (2026-05-11)
reformed both copies (``batch_workers.py`` + ``live_workers.py``) to route
through ``record_empty_for_shard`` — i.e. ``_handle_empty_tick_data`` is now the
*canonical honest-handler name*, so flagging it is pure noise and it was dropped
from the set. (A regression that re-adds NaN-synthesis would do it under a
``_create_*`` name or inline; the runtime 4-pillar ``record_captured`` write-gate
is the real defence, not this static check.)

How it works
------------
1. Loads ``banned_placeholder_methods_baseline.yaml`` (the workspace baseline of
   CURRENTLY-KNOWN occurrences — those are ``pending_removal`` and surface as
   WARNINGS, exit-clean). As of 2026-05-11 PM the baseline holds 2 entries (was
   8) — the writegate Phase 2.A P0-2 surgery deleted 4 of the offenders
   (``tradfi/ohlcv_passthrough.py:_create_full_day_empty_output``,
   ``batch_workers.py``/``orchestration_writer.py``:``_create_closed_market_candle``,
   the legacy ``orchestration_writer.py`` ``_write_candles`` ``upload_bytes``
   bypass) and reformed ``_maybe_write_vix_gap_placeholder`` (still flagged by
   name; baselined-as-warning until writegate cosmetically renames it).
2. AST-walks every ``.py`` file under the given source dir(s) (skipping venvs /
   build artefacts / archived trees / scripts/ / tests/).
3. Flags: (a) ``def <name>`` / ``async def <name>`` for ``name`` in the banned
   method-name set; (b) direct ``*.upload_bytes(...)`` calls in modules whose
   path indicates a candle-write context (``orchestration_writer`` /
   ``output_writer`` / ``candle`` / ``ohlcv``) — these bypass ``record_captured``.
4. For each flagged occurrence: if ``(repo, file, method)`` is in the baseline →
   WARNING (informational, exit-clean). Else → ERROR + ``file:line`` + the
   ``successor:`` from the baseline header — **exit 1**.

So a NEW placeholder method (or one moved to a new file) fails CI immediately;
the residual baselined ones clear as writegate cosmetic renames / dead-code
deletions ship.

Usage::

    # per-repo (run by base-service.sh STEP 5.67):
    python check_banned_placeholder_methods.py --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>

    # workspace-wide sweep:
    python check_banned_placeholder_methods.py --workspace-root <ws>
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

# ── Constants ────────────────────────────────────────────────────────────────

#: Method names that are banned as NaN-placeholder generators. Scoped to names
#: that describe *synthesising a fake empty/closed/placeholder candle* — a new
#: method with one of these names is almost certainly the banned shape.
#: ``_handle_empty_tick_data`` was dropped 2026-05-11 PM after writegate Phase
#: 2.A P0-2 reformed it into the canonical honest-handler (routes through
#: ``record_empty_for_shard``) — see module docstring.
BANNED_METHOD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "_create_empty_output",
        "_create_full_day_empty_output",
        "_create_closed_market_candle",
        "_maybe_write_vix_gap_placeholder",
    }
)

#: Path-fragment substrings that mark a module as a candle-write context — a
#: direct ``*.upload_bytes(...)`` in one of these bypasses ``record_captured``.
CANDLE_WRITE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "orchestration_writer",
    "output_writer",
    "candle_write",
    "candle_processing",
    "ohlcv_passthrough",
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
        "scripts",  # per "Schema provenance" rule — scripts/ is excluded from strict checks
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

#: Required keys per baseline entry.
REQUIRED_KEYS: Final[tuple[str, ...]] = ("repo", "file", "method", "status", "successor")

#: Allowed ``status:`` values per baseline entry.
VALID_STATUS: Final[frozenset[str]] = frozenset({"pending_removal"})


# ── Data shapes ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BaselineEntry:
    """One known-current occurrence the baseline tolerates as a warning."""

    repo: str
    file: str  # repo-relative path
    method: str  # banned method name OR "upload_bytes" for the bypass pattern
    status: str  # "pending_removal"
    successor: str


@dataclass(frozen=True)
class Finding:
    """A flagged occurrence in the source tree."""

    repo: str
    file: str  # repo-relative path
    line: int
    method: str
    snippet: str

    @property
    def baseline_key(self) -> tuple[str, str, str]:
        return (self.repo, self.file, self.method)


# ── Baseline loading ─────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "banned_placeholder_methods_baseline.yaml"


def load_baseline() -> tuple[dict[tuple[str, str, str], BaselineEntry], str]:
    """Return ``({(repo, file, method): BaselineEntry}, default_successor)``."""

    path = _baseline_path()
    if not path.exists():
        return {}, "writegate Phase 2.A (banned-placeholder-method deletion)"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    default_successor = str(raw.get("default_successor", "writegate Phase 2.A"))
    out: dict[tuple[str, str, str], BaselineEntry] = {}
    for item in raw.get("entries", []) or []:  # noqa: qg-empty-fallback
        missing = [k for k in REQUIRED_KEYS if k not in item]
        if missing:
            print(f"[check_banned_placeholder_methods] baseline entry missing keys {missing}: {item}", file=sys.stderr)
            continue
        if item["status"] not in VALID_STATUS:
            print(
                f"[check_banned_placeholder_methods] baseline entry has invalid status "
                f"{item['status']!r} (must be one of {sorted(VALID_STATUS)}): {item}",
                file=sys.stderr,
            )
            continue
        entry = BaselineEntry(
            repo=str(item["repo"]),
            file=str(item["file"]),
            method=str(item["method"]),
            status=str(item["status"]),
            successor=str(item["successor"]),
        )
        out[(entry.repo, entry.file, entry.method)] = entry
    return out, default_successor


# ── Source-tree walking ──────────────────────────────────────────────────────


def _iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if parts & EXCLUDE_DIR_NAMES:
            continue
        s = str(path).replace("\\", "/")
        if any(frag in s for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        yield path


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:  # pragma: no cover — defensive
        print(f"[check_banned_placeholder_methods] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    is_candle_module = any(frag in rel for frag in CANDLE_WRITE_PATH_FRAGMENTS)
    lines = src.splitlines()
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in BANNED_METHOD_NAMES:
            findings.append(
                Finding(repo=repo, file=rel, line=node.lineno, method=node.name, snippet=_line(lines, node.lineno))
            )
        elif is_candle_module and isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "upload_bytes":
                findings.append(
                    Finding(
                        repo=repo, file=rel, line=node.lineno, method="upload_bytes", snippet=_line(lines, node.lineno)
                    )
                )
    return findings


def _line(lines: list[str], lineno: int) -> str:
    return lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""


# ── Entry point ──────────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    """Return ``[(repo_name, scan_root)]`` to walk."""

    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_banned_placeholder_methods] scope dir not found: {repo_root}", file=sys.stderr)
            return []
        if source_dir and (repo_root / source_dir).is_dir():
            return [(scope, repo_root / source_dir)]
        return [(scope, repo_root)]
    # Workspace-wide: every immediate sub-dir with a pyproject.toml.
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir() or child.name in EXCLUDE_DIR_NAMES or child.name.startswith("."):
            continue
        if (child / "pyproject.toml").exists():
            out.append((child.name, child))
    return out


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Banned NaN-placeholder / bypass-record_captured method detector.")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Package sub-dir within the scoped repo (e.g. 'market_data_processing_service').",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline, default_successor = load_baseline()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        # Nothing to scan (scope dir absent etc.) — treat as a clean skip, not a failure.
        print("[check_banned_placeholder_methods] no source trees to scan — skipping.")
        return 0

    all_findings: list[Finding] = []
    for repo_name, scan_root in scopes:
        # The repo_root for relative-path computation is workspace_root/repo_name
        # even when we narrow the scan to a source sub-dir.
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
            f"[WARN] {f.repo}/{f.file}:{f.line}  {f.method}  — baselined ({entry.status}); successor: {entry.successor}"
        )
    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.method}  — banned NaN-placeholder / "
            f"bypass-record_captured pattern.\n"
            f"         {f.snippet}\n"
            f"         Not in banned_placeholder_methods_baseline.yaml — either it's a NEW occurrence (delete it; "
            f"emit record_empty(reason=...) / record_captured() instead) OR an existing one moved files "
            f"(update the baseline).\n"
            f"         Successor for removing the baselined ones: {default_successor}.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_banned_placeholder_methods] FAIL — {len(errors)} non-baselined occurrence(s) "
            f"({len(warnings)} baselined warning(s)).",
            file=sys.stderr,
        )
        return 1
    print(
        f"[check_banned_placeholder_methods] OK — {len(warnings)} baselined occurrence(s) (pending_removal); "
        f"0 new occurrences."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
