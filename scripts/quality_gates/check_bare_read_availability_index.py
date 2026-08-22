#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP — ban a NEW bare ``read_availability_index(bucket)`` call
site (no ``columns=``/``filters=`` projection kwarg) in production code.

Per ``plans/active/issues/read_availability_index_bare_defi_callers_2026_07_27.md``:
the UTL ``read_availability_index(bucket, columns=None, filters=None)``
reader (``unified_trading_library/manifest_writer/_read_index.py``) decodes
the WHOLE consolidated availability index into a pandas DataFrame when called
bare — the defi prod index alone is 1.58 GB on disk (several GB once
decoded). A caller reachable with a defi-asset-group bucket that omits both
projection kwargs is one cache-miss/cold-start away from an OOM on a
memory-constrained Cloud Run job or VM (same incident class as
``mtds_backfill_vm_startup_oom_rc137_2026_07_14``). That audit fixed the
~35-40 call sites it found; this checker is the standing writer-side-mirror
guard the audit's own follow-up todo asked for, so no NEW bare call site can
land silently — this is the READER-side counterpart to
``check_manifest_writer_missing_write_before_return.py`` (writer side).

How it works
------------
1. AST-walks every ``.py`` file under the scoped repo (skipping venvs / build
   artefacts / archived trees / ``scripts/`` / ``tests/`` — production code
   only, per the issue doc's own scoping: "non-test, non-scripts code").
2. Flags every ``Call`` whose callee is literally named ``read_availability_index``
   — a bare ``Name`` (``read_availability_index(bucket)``) or an ``Attribute``
   access (``module.read_availability_index(bucket)``) — that carries NEITHER
   a ``columns=`` NOR a ``filters=`` keyword argument. This intentionally does
   NOT follow import aliases or wrapper functions (e.g. deployment-api's own
   ``manifest_source.read_manifest_index()``) — it targets the literal UTL
   call-site name the issue doc audited, matching a raw/aliased import of the
   real function, not every possible indirection.
3. SHRINKING ratchet against ``read_availability_index_bare_call_baseline.yaml``
   — pre-existing occurrences (the issue doc's own P3/P2 "left bare on
   purpose, with an in-code reason" sites, plus anything not yet triaged)
   surface as WARNINGS (exit-clean); a NEW occurrence fails CI.

Whitelist inline marker: ``# QG-allow: bare-read-availability-index`` on the
call line bypasses the check for a deliberate, justified exception (e.g. a
function that must return/write the full, unprojected schema on some code
path — see the issue doc's ``unified-trading-library`` P2 item for real
examples of this class).

Usage::

    # per-repo (run by base-service.sh):
    python check_bare_read_availability_index.py \
        --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>

    # workspace-wide sweep:
    python check_bare_read_availability_index.py --workspace-root <ws>
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

#: The literal callee name this checker targets — matches the issue doc's own
#: audited call shape (a raw/aliased import of the real UTL function), not
#: every wrapper/indirection that eventually reaches it.
TARGET_CALLEE_NAME: Final[str] = "read_availability_index"

#: Keyword args that count as "projected" — either one alone is sufficient.
PROJECTION_KWARGS: Final[frozenset[str]] = frozenset({"columns", "filters"})

#: Top-level dir names to skip when walking — production code only.
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

#: Inline marker on the call line to bypass the check.
WHITELIST_MARKER: Final[str] = "QG-allow: bare-read-availability-index"

#: Required keys per baseline entry.
REQUIRED_KEYS: Final[tuple[str, ...]] = ("repo", "file", "line", "function", "status", "successor")


@dataclass(frozen=True)
class BaselineEntry:
    repo: str
    file: str
    line: int
    function: str
    status: str
    successor: str


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    line: int
    function: str
    snippet: str

    @property
    def baseline_key(self) -> tuple[str, str, int, str]:
        return (self.repo, self.file, self.line, self.function)


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "read_availability_index_bare_call_baseline.yaml"


def load_baseline() -> tuple[dict[tuple[str, str, int, str], BaselineEntry], str]:
    path = _baseline_path()
    if not path.exists():
        return {}, "read_availability_index_bare_defi_callers_2026_07_27"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    default_successor = str(raw.get("default_successor", "read_availability_index_bare_defi_callers_2026_07_27"))
    out: dict[tuple[str, str, int, str], BaselineEntry] = {}
    for item in raw.get("entries", []) or []:  # noqa: qg-empty-fallback
        missing = [k for k in REQUIRED_KEYS if k not in item]
        if missing:
            print(
                f"[check_bare_read_availability_index] baseline entry missing keys {missing}: {item}",
                file=sys.stderr,
            )
            continue
        entry = BaselineEntry(
            repo=str(item["repo"]),
            file=str(item["file"]),
            line=int(item["line"]),
            function=str(item["function"]),
            status=str(item["status"]),
            successor=str(item["successor"]),
        )
        out[(entry.repo, entry.file, entry.line, entry.function)] = entry
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


class _BareCallVisitor(ast.NodeVisitor):
    """Tracks enclosing function scope while walking for bare-call findings."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines
        self._func_stack: list[str] = []
        self.findings: list[tuple[int, str, str]] = []  # (lineno, function, snippet)

    def _enclosing(self) -> str:
        return self._func_stack[-1] if self._func_stack else "<module>"

    def _visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._func_stack.append(node.name)
        self.generic_visit(node)
        self._func_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_func(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        is_target = (isinstance(func, ast.Name) and func.id == TARGET_CALLEE_NAME) or (
            isinstance(func, ast.Attribute) and func.attr == TARGET_CALLEE_NAME
        )
        if is_target:
            has_projection = any(kw.arg in PROJECTION_KWARGS for kw in node.keywords)
            if not has_projection:
                snippet = _line(self._lines, node.lineno)
                if WHITELIST_MARKER not in snippet:
                    self.findings.append((node.lineno, self._enclosing(), snippet))
        self.generic_visit(node)


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_bare_read_availability_index] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    visitor = _BareCallVisitor(lines)
    visitor.visit(tree)
    return [
        Finding(repo=repo, file=rel, line=lineno, function=function, snippet=snippet)
        for lineno, function, snippet in visitor.findings
    ]


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_bare_read_availability_index] scope dir not found: {repo_root}", file=sys.stderr)
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
        description="Bare read_availability_index(bucket) call (no columns=/filters=) detector."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument("--source-dir", default=None, help="Package sub-dir within the scoped repo.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline, default_successor = load_baseline()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_bare_read_availability_index] no source trees to scan — skipping.")
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
            f"[WARN] {f.repo}/{f.file}:{f.line}  {f.function}()  — baselined ({entry.status}); "
            f"successor: {entry.successor}"
        )
    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.function}()  — bare '{TARGET_CALLEE_NAME}(bucket)' call with no "
            f"'columns='/'filters=' projection kwarg — one cache-miss from decoding the whole (up to several-GB, "
            f"defi-reachable) availability index into memory.\n"
            f"         {f.snippet}\n"
            f"         Add 'columns=[...]' (and/or 'filters=[...]') confirmed by a DIRECT read of this call's "
            f"downstream column usage (do not guess/copy a list — see the issue doc's caution), or if genuinely "
            f"unprojectable, add inline marker '# {WHITELIST_MARKER}' with a one-line reason, or add a baseline "
            f"entry under read_availability_index_bare_call_baseline.yaml.\n"
            f"         Default successor for clearing baselined occurrences: {default_successor}.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_bare_read_availability_index] FAIL — {len(errors)} non-baselined occurrence(s) "
            f"({len(warnings)} baselined warning(s)).",
            file=sys.stderr,
        )
        return 1
    print(f"[check_bare_read_availability_index] OK — {len(warnings)} baselined occurrence(s); 0 new occurrences.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
