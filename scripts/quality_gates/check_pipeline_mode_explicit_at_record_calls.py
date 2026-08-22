#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP — explicit ``pipeline_mode=`` at every ``record_*`` call.

Per ``manifest_schema_final_gate_2026_05_09.md`` Phase 4.GREP-VERIFY:

  Naive grep ``grep -rln 'record_captured' --include='*.py' | xargs grep -L
  'pipeline_mode='`` returns false positives for files containing only docstring  # QG-allow: pipeline-mode-string-literal
  / comment / dict-key / string-literal references. The 2026-05-12 slot 2 audit
  found 7 grep hits all false-positive across deployment-api /
  system-integration-tests / unified-trading-pm/scripts/. AST-walk is the
  authoritative check.

This check ensures every actual ``Call`` node whose attribute is one of the 5
v8 ``record_*`` write-gate methods passes ``pipeline_mode=`` explicitly. Once
Phase 4.DEFAULT-REMOVAL lands (UTL ManifestWriter drops the 4 transitional
``None`` kwarg defaults), basedpyright would catch any regression at type-check
time, but the check stays wired as a defense-in-depth ratchet — UTL's None
defaults could regress, and a typo like ``pipline_mode=`` would pass type-check
(``**kwargs`` swallow) but fail this check.

How it works
------------
1. Loads ``pipeline_mode_explicit_baseline.yaml`` (workspace baseline of
   CURRENTLY-KNOWN-missing-kwarg occurrences — those are ``pending_phase_4_mtds``
   etc. and surface as WARNINGS, exit-clean).
2. AST-walks every ``.py`` file under the given source dir(s) (skipping venvs /
   build artefacts / archived trees / scripts/ / tests/).
3. Flags every ``Call`` node where ``Call.func`` is an ``Attribute`` matching one
   of the 5 ``record_*`` methods AND ``pipeline_mode=`` is NOT in ``Call.keywords``.
4. For each flagged occurrence: if ``(repo, file, line)`` is in the baseline →
   WARNING (informational, exit-clean). Else → ERROR + ``file:line`` + the
   ``successor:`` from the baseline header — **exit 1**.

Whitelist inline marker: ``# QG-allow: pipeline-mode-not-applicable`` on the
same line bypasses the check for the rare legitimate exception (e.g. a test
fixture passing kwargs via ``**dict``).

Usage::

    # per-repo (run by base-service.sh STEP 5.6x):
    python check_pipeline_mode_explicit_at_record_calls.py --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>

    # workspace-wide sweep:
    python check_pipeline_mode_explicit_at_record_calls.py --workspace-root <ws>
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

#: ``record_*`` method names on ``ManifestWriter`` / ``ShardManifestRecorder`` —
#: every call to one of these MUST pass ``pipeline_mode=`` explicitly post-Phase-4.
RECORD_METHOD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "record_captured",
        "record_empty",
        "record_failed",
        "record_expected_unattempted",
        "record_empty_for_shard",
    }
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
WHITELIST_MARKER: Final[str] = "QG-allow: pipeline-mode-not-applicable"

#: Required keys per baseline entry.
REQUIRED_KEYS: Final[tuple[str, ...]] = ("repo", "file", "line", "method", "status", "successor")

#: Allowed ``status:`` values per baseline entry.
VALID_STATUS: Final[frozenset[str]] = frozenset({"pending_phase_4_mtds", "pending_phase_4_features"})


@dataclass(frozen=True)
class BaselineEntry:
    repo: str
    file: str
    line: int
    method: str
    status: str
    successor: str


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    line: int
    method: str
    snippet: str

    @property
    def baseline_key(self) -> tuple[str, str, int, str]:
        return (self.repo, self.file, self.line, self.method)


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "pipeline_mode_explicit_baseline.yaml"


def load_baseline() -> tuple[dict[tuple[str, str, int, str], BaselineEntry], str]:
    path = _baseline_path()
    if not path.exists():
        return {}, "manifest_schema_final_gate Phase 4.MTDS + Phase 4.DEFAULT-REMOVAL"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    default_successor = str(raw.get("default_successor", "manifest_schema_final_gate Phase 4.DEFAULT-REMOVAL"))
    out: dict[tuple[str, str, int, str], BaselineEntry] = {}
    for item in raw.get("entries", []) or []:  # noqa: qg-empty-fallback
        missing = [k for k in REQUIRED_KEYS if k not in item]
        if missing:
            print(
                f"[check_pipeline_mode_explicit_at_record_calls] baseline entry missing keys {missing}: {item}",
                file=sys.stderr,
            )
            continue
        if item["status"] not in VALID_STATUS:
            print(
                f"[check_pipeline_mode_explicit_at_record_calls] baseline entry has invalid status "
                f"{item['status']!r} (must be one of {sorted(VALID_STATUS)}): {item}",
                file=sys.stderr,
            )
            continue
        entry = BaselineEntry(
            repo=str(item["repo"]),
            file=str(item["file"]),
            line=int(item["line"]),
            method=str(item["method"]),
            status=str(item["status"]),
            successor=str(item["successor"]),
        )
        out[(entry.repo, entry.file, entry.line, entry.method)] = entry
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


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_pipeline_mode_explicit_at_record_calls] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in RECORD_METHOD_NAMES:
            continue
        kwarg_names = {kw.arg for kw in node.keywords if kw.arg is not None}
        if "pipeline_mode" in kwarg_names:
            continue
        snippet = _line(lines, node.lineno)
        if WHITELIST_MARKER in snippet:
            continue
        findings.append(Finding(repo=repo, file=rel, line=node.lineno, method=func.attr, snippet=snippet))
    return findings


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_pipeline_mode_explicit_at_record_calls] scope dir not found: {repo_root}", file=sys.stderr)
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
    parser = argparse.ArgumentParser(description="Explicit pipeline_mode= kwarg at every record_* call detector.")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument("--source-dir", default=None, help="Package sub-dir within the scoped repo.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline, default_successor = load_baseline()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_pipeline_mode_explicit_at_record_calls] no source trees to scan — skipping.")
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
            f"[WARN] {f.repo}/{f.file}:{f.line}  {f.method}(...)  — baselined ({entry.status}); "
            f"successor: {entry.successor}"
        )
    for f in errors:
        print(
            f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.method}(...)  — missing explicit pipeline_mode= kwarg.\n"
            f"         {f.snippet}\n"
            f"         Pass pipeline_mode=PipelineMode.<source> per UAC SOURCE_PRIORITY top entry. If genuinely "
            f"N/A, add inline marker '# {WHITELIST_MARKER}' OR add a baseline entry under "
            f"pipeline_mode_explicit_baseline.yaml.\n"
            f"         Default successor for clearing baselined occurrences: {default_successor}.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_pipeline_mode_explicit_at_record_calls] FAIL — {len(errors)} non-baselined occurrence(s) "
            f"({len(warnings)} baselined warning(s)).",
            file=sys.stderr,
        )
        return 1
    print(
        f"[check_pipeline_mode_explicit_at_record_calls] OK — {len(warnings)} baselined occurrence(s); "
        f"0 new occurrences."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
