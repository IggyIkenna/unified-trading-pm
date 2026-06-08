#!/usr/bin/env python3
"""QG STEP — open-edge (left) bar ingestion detector (bar-boundary correctness).

Per ``bar_edge_left_vs_right_remediation_2026_06_08.md`` Phase 0 (== the
``audit_criteria_automation_2026_06_08.md`` Tier-2 "no pre-aggregated open-edge
bar ingestion" step): a CLOSED OHLCV candle MUST be timestamped on its RIGHT
(close) edge ``t_close``. Stamping the vendor's OPEN/left (bar-START) edge on a
closed bar is **look-ahead → leakage** and the MDPS bar-boundary gate does NOT
catch it (a uniform one-interval left-shift stays grid-aligned).

This is the STATIC counterpart to the runtime ingestion-time assertion. It
flags an ingestion/adapter function that consumes a vendor bar-START field and
stamps it as the candle timestamp WITHOUT converting to the close edge.

Detection (AST, per-function — low false-positive by construction)
------------------------------------------------------------------
A function is FLAGGED when it references an open-edge START marker AND does NOT
contain a close-edge conversion / close-field reference (and is not opted-out):

* **Unambiguous START tokens** (flagged anywhere — these are unmistakably
  bar-START field names): ``periodStartUnix`` / ``openTimestamp``.
* **Contextual START pattern** (flagged ONLY inside a candle/ohlcv/kline
  function — name contains ``candle`` / ``ohlcv`` / ``kline``): a subscript
  ``["t"]`` / ``.get("t")`` (the vendor bar-start field). The broader
  open-index ``bar[0]`` / DataFrame ``.index`` patterns are deliberately NOT
  static-flagged — they are too generic to separate from correct
  tick-aggregation internals without dataflow analysis (they false-positived
  the verified-correct MDPS aggregators in the fleet sweep), so that slice of
  the class is covered by the RUNTIME ingestion-time assertion instead.

A function is CLEARED (suppressed) when it ALSO contains any of:

* a call to ``compute_bar_close_boundary(...)`` (the canonical conversion), or
* an explicit close-field reference — ``["T"]`` / ``.get("T")`` / ``[6]`` /
  ``closeTime`` / ``close_time`` / ``period_end`` / ``t_close`` / ``periodEnd``,
  or
* the per-line opt-out marker ``# noqa: bar-boundary-open-edge`` on the START
  reference line.

Baseline ratchet (model: ``check_pipeline_mode_explicit_at_record_calls.py``):
``(repo, file, function)`` occurrences in ``bar_edge_open_ingestion_baseline.yaml``
surface as WARNINGS (exit-clean); any NON-baselined occurrence is an ERROR
(exit 1). So pre-existing latent sites are tolerated while NEW open-edge
ingestion fails the commit.

Exit codes: 0 = clean (only baselined warnings); 1 = new violation(s); 2 = arg/IO error.

Usage::

    # per-repo (base-service.sh STEP 5.92):
    python check_bar_edge_open_ingestion.py --workspace-root <ws> --scope <repo> --source-dir <pkg>
    # workspace-wide sweep / baseline generation:
    python check_bar_edge_open_ingestion.py --workspace-root <ws>
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

import yaml

#: Unambiguous bar-START field names (flagged regardless of function context).
UNAMBIGUOUS_START_TOKENS: Final[frozenset[str]] = frozenset({"periodStartUnix", "openTimestamp"})

#: Substrings marking a function as a candle/ohlcv builder (enables the
#: contextual ``["t"]`` START pattern, too generic to flag everywhere).
CANDLE_FN_MARKERS: Final[tuple[str, ...]] = ("candle", "ohlcv", "kline")

#: Close-edge markers: any of these in the function body suppress the flag.
CLOSE_TOKENS: Final[frozenset[str]] = frozenset({"closeTime", "close_time", "period_end", "periodEnd", "t_close", "T"})
#: The canonical conversion call name.
CLOSE_CONVERSION_FN: Final[str] = "compute_bar_close_boundary"

#: Per-line opt-out marker.
NOQA_MARKER: Final[str] = "# noqa: bar-boundary-open-edge"

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
        "test",
    }
)
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = ("/archive/", "/.archive/", "/_archived/", ".egg-info")

REQUIRED_KEYS: Final[tuple[str, ...]] = ("repo", "file", "function")


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    function: str
    line: int
    snippet: str

    @property
    def baseline_key(self) -> tuple[str, str, str]:
        return (self.repo, self.file, self.function)


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "bar_edge_open_ingestion_baseline.yaml"


def load_baseline() -> tuple[set[tuple[str, str, str]], str]:
    path = _baseline_path()
    if not path.exists():
        return set(), "bar_edge_left_vs_right_remediation_2026_06_08.md Phase 1"
    raw = cast("dict[str, object]", yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    successor = str(raw.get("default_successor", "bar_edge_left_vs_right_remediation_2026_06_08.md Phase 1"))
    out: set[tuple[str, str, str]] = set()
    entries = cast("list[dict[str, object]]", raw.get("entries") or [])
    for item in entries:
        if any(k not in item for k in REQUIRED_KEYS):
            print(f"[check_bar_edge_open_ingestion] baseline entry missing keys: {item}", file=sys.stderr)
            continue
        out.add((str(item["repo"]), str(item["file"]), str(item["function"])))
    return out, successor


def _iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if set(path.parts) & EXCLUDE_DIR_NAMES:
            continue
        s = str(path).replace("\\", "/")
        if any(frag in s for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        yield path


def _const_str(node: ast.expr) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _subscript_or_get_key(node: ast.expr) -> str | None:
    """Return the string key of ``x["k"]`` (Subscript) or ``x.get("k")`` (Call)."""
    if isinstance(node, ast.Subscript):
        return _const_str(node.slice)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
        return _const_str(node.args[0])
    return None


def _root_name(node: ast.expr) -> str:
    """Best-effort root identifier of an attribute/subscript chain."""
    cur: ast.expr = node
    while True:
        if isinstance(cur, (ast.Attribute, ast.Subscript)):
            cur = cur.value
        elif isinstance(cur, ast.Call):
            cur = cur.func
        else:
            break
    return cur.id if isinstance(cur, ast.Name) else ""


def _analyze_function(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
    file_lines: list[str],
) -> tuple[int, str] | None:
    """Return (lineno, snippet) of the first open-edge START reference if the
    function is an UNCLEARED open-edge candle ingester, else None."""
    is_candle_fn = any(m in fn.name.lower() for m in CANDLE_FN_MARKERS)
    cleared = False
    start_hit: tuple[int, str] | None = None

    for node in ast.walk(fn):
        # CLEAR: canonical conversion call.
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
            fname = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            if fname == CLOSE_CONVERSION_FN:
                cleared = True

        # CLEAR: explicit close-field name reference (attr, name, or key).
        if isinstance(node, ast.Name) and node.id in CLOSE_TOKENS:
            cleared = True
        if isinstance(node, ast.Attribute) and node.attr in CLOSE_TOKENS:
            cleared = True
        key = _subscript_or_get_key(node) if isinstance(node, (ast.Subscript, ast.Call)) else None
        if key in CLOSE_TOKENS:
            cleared = True
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == 6:
            cleared = True  # Binance kline close-time index

        # START: unambiguous tokens (Name/Attribute/key).
        line_no = getattr(node, "lineno", 0)
        snippet = file_lines[line_no - 1].strip() if 0 < line_no <= len(file_lines) else ""
        if NOQA_MARKER in snippet:
            continue
        if isinstance(node, ast.Name) and node.id in UNAMBIGUOUS_START_TOKENS:
            start_hit = start_hit or (line_no, snippet)
        if isinstance(node, ast.Attribute) and node.attr in UNAMBIGUOUS_START_TOKENS:
            start_hit = start_hit or (line_no, snippet)
        if key in UNAMBIGUOUS_START_TOKENS:
            start_hit = start_hit or (line_no, snippet)

        # START: contextual pattern (vendor "t" open field, candle fns only).
        if is_candle_fn and key == "t":
            start_hit = start_hit or (line_no, snippet)

    if start_hit is not None and not cleared:
        return start_hit
    return None


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_bar_edge_open_ingestion] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            hit = _analyze_function(node, lines)
            if hit is not None:
                findings.append(Finding(repo=repo, file=rel, function=node.name, line=hit[0], snippet=hit[1]))
    return findings


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_bar_edge_open_ingestion] scope dir not found: {repo_root}", file=sys.stderr)
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
    parser = argparse.ArgumentParser(description="Open-edge (left) bar ingestion detector.")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name (per-repo QG mode).")
    parser.add_argument("--source-dir", default=None, help="Package sub-dir within the scoped repo.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = cast(Path, args.workspace_root).resolve()
    scope = cast("str | None", args.scope)
    source_dir = cast("str | None", args.source_dir)
    baseline, successor = load_baseline()
    scopes = _resolve_scopes(workspace_root, scope, source_dir)
    if not scopes:
        print("[check_bar_edge_open_ingestion] no source trees to scan — skipping.")
        return 0

    all_findings: list[Finding] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name
        for py in _iter_py_files(scan_root):
            all_findings.extend(_scan_file(py, repo_name, repo_root))

    errors = [f for f in all_findings if f.baseline_key not in baseline]
    warnings = [f for f in all_findings if f.baseline_key in baseline]

    for f in warnings:
        print(f"[WARN] {f.repo}/{f.file}:{f.line}  {f.function}(...) — baselined open-edge; successor: {successor}")
    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.function}(...) — stamps a vendor bar-START (open/left) edge "
            f"without a close conversion.\n"
            f"         {f.snippet}\n"
            f"         Use the vendor close field (e.g. kline [6] / `T`) OR "
            f"unified_trading_library.availability_stamping.compute_bar_close_boundary(open_ts, timeframe) → t_close. "
            f"If genuinely N/A add '{NOQA_MARKER}' on the line, or baseline it in "
            f"bar_edge_open_ingestion_baseline.yaml.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_bar_edge_open_ingestion] FAIL — {len(errors)} new open-edge ingestion site(s) "
            f"({len(warnings)} baselined).",
            file=sys.stderr,
        )
        return 1
    print(f"[check_bar_edge_open_ingestion] OK — {len(warnings)} baselined; 0 new open-edge ingestion sites.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
