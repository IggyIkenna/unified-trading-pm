#!/usr/bin/env python3
"""QG STEP — canonical data-model regression detector (AST, baseline-ratchet).

Per ``audit_criteria_automation_2026_06_08.md`` Phase 1 (Tier-2 "code PATTERN
(NEW model)" steps) — converts three recurring agentic-grep audits into a
static gate that catches the *exact* regressions the 2026-06 canonicalisation
fixed. AST-based so docstrings / comments / string-example paths do NOT
false-positive (a naive grep flagged only docstrings + tests in the fleet
sweep). Each pattern carries a ``(repo, file, line, pattern)`` baseline; a
NON-baselined hit is an ERROR (exit 1), a baselined one a WARNING (exit-clean).

Patterns
--------
* ``coarse-pipeline-mode`` — a ``pipeline_mode`` / ``*_PIPELINE_MODE`` target (or
  ``pipeline_mode=`` kwarg) assigned the bare coarse literal ``"batch"`` /
  ``"live"`` / ``""``. The canonical model is source-aware
  ``{mode}_{source}[_{transport}]`` (``batch_databento`` …). Catches the DeFi
  ``DEFAULT_PIPELINE_MODE="batch"`` class reappearing. (Extends STEP 5.85 which
  only bans inline literals in SOURCE_DIR — this also covers ``scripts/``
  migrators/rebuilds + the coarse VALUE specifically + blank.)
* ``exact-coarse-reader`` — a string literal containing the exact coarse path
  segment ``pipeline_mode=batch/`` or ``pipeline_mode=live/`` (trailing slash =
  a path probe). Readers MUST prefix-match ``batch_*``/``live_*``/``replay_*``,
  never the coarse literal (the C-PATH READ fix must not regress).
* ``era-a-chain-write`` — a ``data_type`` target / ``data_type=`` kwarg assigned
  the literal ``"options_chain"`` / ``"futures_chain"``. Era-B: chains are
  INSTRUMENT_TYPES written with ``data_type=trades``; ``data_type=options_chain``
  is the retired Era-A write shape. UAC registry/declaration files (which
  legitimately RETAIN legacy data_type-keyed entries for pre-migration coverage
  lookups, per the coordinator) are path-excluded; genuinely pre-existing write
  sites are baselined (owned by the per-AG v8→v9 migrators).

Whitelist: ``# QG-allow: canonical-model-regression`` on the line.

Exit codes: 0 = clean (baselined warnings only); 1 = new violation(s); 2 = arg/IO error.

Usage::

    python check_canonical_model_regressions.py --workspace-root <ws> --scope <repo> --source-dir <pkg>
    python check_canonical_model_regressions.py --workspace-root <ws>   # fleet sweep
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

# Only the coarse NON-source-aware literals are flagged. Blank ``""`` is NOT
# flagged: it is the canonical v9 SENTINEL (a dataclass field default / a
# features-or-service row) that ``ManifestWriter.add()`` auto-derives for
# derivable market-data rows (utl C-#2 d0745bde) — flagging it would trip every
# legitimate sentinel default. The bad-blank-WRITE-for-a-derivable-row case is
# covered by the UTL auto-derive + the STEP 5.70 explicit-pipeline_mode ratchet.
COARSE_PM_VALUES: Final[frozenset[str]] = frozenset({"batch", "live"})
ERA_A_CHAIN_VALUES: Final[frozenset[str]] = frozenset({"options_chain", "futures_chain"})
COARSE_READER_SEGMENTS: Final[tuple[str, ...]] = ("pipeline_mode=batch/", "pipeline_mode=live/")

WHITELIST_MARKER: Final[str] = "QG-allow: canonical-model-regression"

#: UAC registry / declaration trees that legitimately RETAIN legacy
#: data_type-keyed options_chain/futures_chain entries (coverage lookups +
#: required-input + snapshot-schema declarations) — NOT parquet/manifest
#: writes. Path-excluded from the era-a-chain-write pattern.
ERA_A_EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "unified_api_contracts/registry/",
    "unified_api_contracts/canonical/domain/",
    "unified_api_contracts/internal/",
)

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
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
    # the QG checkers + their baselines necessarily contain the patterns they detect
    "scripts/quality_gates/",
)
REQUIRED_KEYS: Final[tuple[str, ...]] = ("repo", "file", "line", "pattern")


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    line: int
    pattern: str
    snippet: str

    @property
    def baseline_key(self) -> tuple[str, str, int, str]:
        return (self.repo, self.file, self.line, self.pattern)


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "canonical_model_regressions_baseline.yaml"


def load_baseline() -> tuple[set[tuple[str, str, int, str]], str]:
    path = _baseline_path()
    if not path.exists():
        return set(), "the per-AG *_manifest_canonicalisation_2026_06_01.md migrators"
    raw = cast("dict[str, object]", yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    successor = str(raw.get("default_successor", "the per-AG *_manifest_canonicalisation migrators"))
    out: set[tuple[str, str, int, str]] = set()
    entries = cast("list[dict[str, object]]", raw.get("entries") or [])
    for item in entries:
        if any(k not in item for k in REQUIRED_KEYS):
            print(f"[check_canonical_model_regressions] baseline entry missing keys: {item}", file=sys.stderr)
            continue
        out.add((str(item["repo"]), str(item["file"]), int(str(item["line"])), str(item["pattern"])))
    return out, successor


def _iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if set(path.parts) & EXCLUDE_DIR_NAMES:
            continue
        s = str(path).replace("\\", "/")
        if any(frag in s for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        yield path


def _const_str(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _target_names(targets: list[ast.expr]) -> list[str]:
    out: list[str] = []
    for t in targets:
        if isinstance(t, ast.Name):
            out.append(t.id)
        elif isinstance(t, ast.Attribute):
            out.append(t.attr)
    return out


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_canonical_model_regressions] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    era_a_excluded = any(frag in rel for frag in ERA_A_EXCLUDE_PATH_FRAGMENTS)
    findings: list[Finding] = []

    # Collect docstring / bare-string-statement Constant nodes — these are prose
    # (module/class/fn docstrings or example paths) and must NOT trip the
    # string-literal exact-coarse-reader pattern.
    docstring_nodes: set[int] = set()
    for parent in ast.walk(tree):
        if not isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for stmt in parent.body:
            if (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                docstring_nodes.add(id(stmt.value))

    def _snippet(lineno: int) -> str:
        return lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""

    def _flagged(lineno: int) -> bool:
        return WHITELIST_MARKER in _snippet(lineno)

    for node in ast.walk(tree):
        # --- coarse-pipeline-mode + era-a-chain-write: assignments ---
        if isinstance(node, ast.Assign):
            names = _target_names(node.targets)
            val = _const_str(node.value)
            for nm in names:
                if (
                    (nm == "pipeline_mode" or nm.endswith("PIPELINE_MODE"))
                    and val in COARSE_PM_VALUES
                    and not _flagged(node.lineno)
                ):
                    findings.append(Finding(repo, rel, node.lineno, "coarse-pipeline-mode", _snippet(node.lineno)))
                if nm == "data_type" and val in ERA_A_CHAIN_VALUES and not era_a_excluded and not _flagged(node.lineno):
                    findings.append(Finding(repo, rel, node.lineno, "era-a-chain-write", _snippet(node.lineno)))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, (ast.Name, ast.Attribute)):
            nm = node.target.id if isinstance(node.target, ast.Name) else node.target.attr
            val = _const_str(node.value)
            if (
                (nm == "pipeline_mode" or nm.endswith("PIPELINE_MODE"))
                and val in COARSE_PM_VALUES
                and not _flagged(node.lineno)
            ):
                findings.append(Finding(repo, rel, node.lineno, "coarse-pipeline-mode", _snippet(node.lineno)))
            if nm == "data_type" and val in ERA_A_CHAIN_VALUES and not era_a_excluded and not _flagged(node.lineno):
                findings.append(Finding(repo, rel, node.lineno, "era-a-chain-write", _snippet(node.lineno)))

        # --- kwargs: pipeline_mode= / data_type= ---
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                val = _const_str(kw.value)
                if kw.arg == "pipeline_mode" and val in COARSE_PM_VALUES and not _flagged(kw.value.lineno):
                    findings.append(
                        Finding(repo, rel, kw.value.lineno, "coarse-pipeline-mode", _snippet(kw.value.lineno))
                    )
                if (
                    kw.arg == "data_type"
                    and val in ERA_A_CHAIN_VALUES
                    and not era_a_excluded
                    and not _flagged(kw.value.lineno)
                ):
                    findings.append(Finding(repo, rel, kw.value.lineno, "era-a-chain-write", _snippet(kw.value.lineno)))

        # --- exact-coarse-reader: any string constant w/ the coarse path seg
        #     (docstrings / bare-string statements are prose, not reader code) ---
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_nodes
            and any(seg in node.value for seg in COARSE_READER_SEGMENTS)
            and not _flagged(node.lineno)
        ):
            findings.append(Finding(repo, rel, node.lineno, "exact-coarse-reader", _snippet(node.lineno)))

    return findings


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_canonical_model_regressions] scope dir not found: {repo_root}", file=sys.stderr)
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
    parser = argparse.ArgumentParser(description="Canonical data-model regression detector.")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None)
    parser.add_argument("--source-dir", default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = cast(Path, args.workspace_root).resolve()
    scope = cast("str | None", args.scope)
    source_dir = cast("str | None", args.source_dir)
    baseline, successor = load_baseline()
    scopes = _resolve_scopes(workspace_root, scope, source_dir)
    if not scopes:
        print("[check_canonical_model_regressions] no source trees to scan — skipping.")
        return 0

    all_findings: list[Finding] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name
        for py in _iter_py_files(scan_root):
            all_findings.extend(_scan_file(py, repo_name, repo_root))

    errors = [f for f in all_findings if f.baseline_key not in baseline]
    warnings = [f for f in all_findings if f.baseline_key in baseline]

    for f in warnings:
        print(f"[WARN] {f.repo}/{f.file}:{f.line} [{f.pattern}] — baselined; successor: {successor}")
    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line} [{f.pattern}]\n         {f.snippet}\n"
            f"         Canonical model is source-aware (batch_<source>) / Era-B (data_type=trades for chains) / "
            f"prefix-match readers. Fix it, add '# {WHITELIST_MARKER}', or baseline in "
            f"canonical_model_regressions_baseline.yaml (successor: {successor}).",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_canonical_model_regressions] FAIL — {len(errors)} new regression(s) "
            f"({len(warnings)} baselined).",
            file=sys.stderr,
        )
        return 1
    print(f"[check_canonical_model_regressions] OK — {len(warnings)} baselined; 0 new canonical-model regressions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
