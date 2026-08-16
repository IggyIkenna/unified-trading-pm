#!/usr/bin/env python3
# Epic: sports_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP — ``ManifestWriter.record_*()`` followed by a ``return``
with no ``.write()``/``.flush()`` on that same instance, when OTHER exit
paths in the SAME function DO call it.

Per ``plans/active/issues/manifest_early_return_missing_write_loss_2026_07_09.md``:
``record_*()`` calls only append to a ``ManifestWriter`` INSTANCE's local
``_records`` list — ``.write()``/``.flush()`` is what moves those records into
the module-level pending buffer. A function with an early-return guard block
that calls ``record_*()`` in a loop then ``return``s with no ``.write()``/
``.flush()`` call silently discards every honest-absence write on that path —
while every OTHER exit path in the same function correctly calls it. This bug
was live in understat.py / weather.py / footystats.py for the guards'
entire lifetime (fixed in ``instruments-service@920b303``); this checker is
the generalised standing guard the issue doc's follow-up todo asked for.

How it works
------------
For each function (``FunctionDef``/``AsyncFunctionDef``, not descending into
nested function/lambda scopes when scanning) with at least one ``return``
statement:

1. Find every ``Name`` variable that receives a ``record_*`` call anywhere in
   the function (``RECORD_METHOD_NAMES``).
2. For each block (a literal statement list — function body, or an
   if/elif/else/for/while/try/except/with body), walk statements in order,
   tracking per-variable "unflushed record pending" state: a statement
   containing a ``var.record_*(...)`` call sets ``pending[var]``; a statement
   containing ``var.write()``/``var.flush()`` clears it. A ``return``
   statement in that block flags every variable still ``pending`` at that
   point as a candidate finding. Nested blocks are analyzed independently
   (their own local pending state) — this matches the actual bug shape
   exactly (record-loop + return as sibling statements in the SAME guard
   block) without needing full control-flow-graph reasoning.
3. A candidate finding for variable V is only reported if there EXISTS
   another return path in the SAME function where V is NOT pending (i.e.
   some other exit correctly calls ``.write()``/``.flush()`` on V) — this is
   the "when OTHER exit paths DO call it" gate from the issue doc, and avoids
   flagging helper functions that legitimately never flush (the caller owns
   that instance's lifecycle).
4. SHRINKING ratchet against
   ``manifest_writer_missing_write_baseline.yaml`` — pre-existing occurrences
   surface as WARNINGS (exit-clean); a NEW occurrence fails CI.

Whitelist inline marker: ``# QG-allow: manifest-write-not-required`` on the
``return`` line bypasses the check for a deliberate exception (e.g. a
dry-run / preview path that intentionally never persists).

Usage::

    # per-repo (run by base-service.sh):
    python check_manifest_writer_missing_write_before_return.py \
        --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>

    # workspace-wide sweep:
    python check_manifest_writer_missing_write_before_return.py --workspace-root <ws>
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

#: ``record_*`` methods that append to a ``ManifestWriter`` instance's local
#: buffer (require an eventual ``.write()``/``.flush()`` to actually persist).
RECORD_METHOD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "record_captured",
        "record_captured_from_counts",
        "record_empty",
        "record_expected_empty",
        "record_expected_unattempted",
        "record_failed",
        "record_zero_rows",
    }
)

#: Methods that persist an instance's buffered records.
WRITE_METHOD_NAMES: Final[frozenset[str]] = frozenset({"write", "flush"})

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

#: Inline marker on the offending ``return`` line to bypass the check.
WHITELIST_MARKER: Final[str] = "QG-allow: manifest-write-not-required"

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
    var: str
    snippet: str

    @property
    def baseline_key(self) -> tuple[str, str, int, str]:
        return (self.repo, self.file, self.line, self.function)


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "manifest_writer_missing_write_baseline.yaml"


def load_baseline() -> tuple[dict[tuple[str, str, int, str], BaselineEntry], str]:
    path = _baseline_path()
    if not path.exists():
        return {}, "manifest_early_return_missing_write_loss_2026_07_09 P2 non-sports audit"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    default_successor = str(raw.get("default_successor", "manifest_early_return_missing_write_loss_2026_07_09"))
    out: dict[tuple[str, str, int, str], BaselineEntry] = {}
    for item in raw.get("entries", []) or []:  # noqa: qg-empty-fallback
        missing = [k for k in REQUIRED_KEYS if k not in item]
        if missing:
            print(
                f"[check_manifest_writer_missing_write_before_return] baseline entry missing keys {missing}: {item}",
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


#: AST node types with a nested statement-list body that constitutes its own
#: sub-block for this analysis (excludes function/lambda defs — those get
#: their own top-level scan pass, never inherited state).
_BLOCK_HOLDER_TYPES: Final[tuple[type[ast.AST], ...]] = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
)


def _child_blocks(stmt: ast.stmt) -> list[list[ast.stmt]]:
    """Direct nested statement-list bodies of ``stmt`` (its own sub-blocks)."""
    if not isinstance(stmt, _BLOCK_HOLDER_TYPES):
        return []
    blocks: list[list[ast.stmt]] = [list(getattr(stmt, "body", []))]
    if hasattr(stmt, "orelse") and stmt.orelse:
        blocks.append(list(stmt.orelse))
    if isinstance(stmt, ast.Try):
        for handler in stmt.handlers:
            blocks.append(list(handler.body))
        if stmt.finalbody:
            blocks.append(list(stmt.finalbody))
    return blocks


def _calls_on_vars(node: ast.AST, method_names: frozenset[str]) -> set[str]:
    """Variable names receiving a ``var.<method>(...)`` call anywhere within
    ``node``, WITHOUT descending into nested function/lambda scopes."""
    found: set[str] = set()

    def _walk(n: ast.AST) -> None:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return  # separate scope — analyzed independently
        if isinstance(n, ast.Call):
            func = n.func
            if isinstance(func, ast.Attribute) and func.attr in method_names and isinstance(func.value, ast.Name):
                found.add(func.value.id)
        for child in ast.iter_child_nodes(n):
            _walk(child)

    _walk(node)
    return found


@dataclass
class _ScanState:
    findings: list[Finding] = field(default_factory=list)
    #: (var, return_lineno) -> True if V was pending (violation) at that return.
    per_var_returns: dict[str, list[tuple[int, bool]]] = field(default_factory=dict)


def _scan_block_with_clean_returns(
    stmts: list[ast.stmt], state: _ScanState, function_name: str, lines: list[str]
) -> None:
    """Walk a statement block tracking per-variable unflushed-record state.

    Flags every ``return`` where a record-using variable is still pending
    (a violation), AND records a clean (non-violating) sample for every
    return where it isn't — the function-level 'other paths DO write' gate
    needs both to decide whether a violation is worth reporting."""
    pending: set[str] = set()
    all_record_vars_seen: set[str] = set()
    for stmt in stmts:
        record_vars = _calls_on_vars(stmt, RECORD_METHOD_NAMES)
        write_vars = _calls_on_vars(stmt, WRITE_METHOD_NAMES)
        all_record_vars_seen |= record_vars
        if isinstance(stmt, ast.Return):
            snippet = _line(lines, stmt.lineno)
            for var in all_record_vars_seen:
                is_violation = var in pending
                state.per_var_returns.setdefault(var, []).append((stmt.lineno, is_violation))
                if is_violation and WHITELIST_MARKER not in snippet:
                    state.findings.append(
                        Finding(repo="", file="", line=stmt.lineno, function=function_name, var=var, snippet=snippet)
                    )
        pending |= record_vars
        pending -= write_vars
        for sub_block in _child_blocks(stmt):
            _scan_block_with_clean_returns(sub_block, state, function_name, lines)


def _scan_function(fn: ast.FunctionDef | ast.AsyncFunctionDef, lines: list[str]) -> list[Finding]:
    state = _ScanState()
    _scan_block_with_clean_returns(list(fn.body), state, fn.name, lines)
    # Gate: only report a var's violating returns if that SAME var has at
    # least one non-violating return elsewhere in the function (some other
    # exit path DOES call .write()/.flush() before returning).
    kept: list[Finding] = []
    for f in state.findings:
        samples = state.per_var_returns.get(f.var, [])
        has_clean_path = any(not is_violation for _, is_violation in samples)
        if has_clean_path:
            kept.append(f)
    return kept


def _iter_top_level_functions(tree: ast.Module) -> Iterator[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Every function def in the module, at any nesting depth — each is its
    own independent scan (nested defs don't inherit outer pending state and
    vice versa, since ``_calls_on_vars``/``_child_blocks`` never descend into
    a FunctionDef/AsyncFunctionDef/Lambda)."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_manifest_writer_missing_write_before_return] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    findings: list[Finding] = []
    for fn in _iter_top_level_functions(tree):
        for f in _scan_function(fn, lines):
            findings.append(
                Finding(repo=repo, file=rel, line=f.line, function=f.function, var=f.var, snippet=f.snippet)
            )
    return findings


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(
                f"[check_manifest_writer_missing_write_before_return] scope dir not found: {repo_root}",
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
    parser = argparse.ArgumentParser(
        description="ManifestWriter.record_*() followed by a return with no .write()/.flush() detector."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument("--source-dir", default=None, help="Package sub-dir within the scoped repo.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline, default_successor = load_baseline()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_manifest_writer_missing_write_before_return] no source trees to scan — skipping.")
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
            f"[WARN] {f.repo}/{f.file}:{f.line}  {f.function}()  var={f.var}  — baselined ({entry.status}); "
            f"successor: {entry.successor}"
        )
    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.function}()  — '{f.var}.record_*(...)' called with no "
            f"'{f.var}.write()'/'{f.var}.flush()' before this return, while another exit path in the same "
            f"function DOES call it.\n"
            f"         {f.snippet}\n"
            f"         Add '{f.var}.write()' (or '.flush()') before this return, or if genuinely intentional, "
            f"add inline marker '# {WHITELIST_MARKER}' on the return line, or add a baseline entry under "
            f"manifest_writer_missing_write_baseline.yaml.\n"
            f"         Default successor for clearing baselined occurrences: {default_successor}.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_manifest_writer_missing_write_before_return] FAIL — {len(errors)} non-baselined "
            f"occurrence(s) ({len(warnings)} baselined warning(s)).",
            file=sys.stderr,
        )
        return 1
    print(
        f"[check_manifest_writer_missing_write_before_return] OK — {len(warnings)} baselined occurrence(s); "
        f"0 new occurrences."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
