#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP 5.72 — ban explicit ``project_id=`` on asset-group bucket builders.

Passing an explicit ``project_id`` to ``get_bucket_name(...)`` /
``get_write_bucket_name(...)`` **bypasses the cloud-providers.yaml SSOT** and
returns the legacy no-env shape (e.g. ``instruments-store-sports-{pid}`` /
``market-data-tick-defi-{pid}``) instead of the env-tiered canonical form
(``instruments-store-sports-prd-{pid}``). Those legacy no-env buckets are
DELETED at each asset_group's legacy-bucket decommission, so any live read/write
resolving the no-env form silently breaks at cutover.

Canonical: call the builder WITHOUT ``project_id`` (it then delegates to the
yaml SSOT and applies the env tier), or use
``unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(
cloud=..., kind=..., asset_group=...)`` directly.

Scope: only flags calls whose first positional arg is a *string-literal*
asset-group bucket domain (``instruments`` / ``market_data`` / ``features_*``)
AND that pass a ``project_id`` (kwarg OR 3rd positional). Non-asset-group
domains (``ml_models`` / ``ml_artifacts`` / ``pnl`` / ``risk`` / ``positions``)
are NOT asset-group-split and not in the decommission scope, so they are
exempt. Calls whose domain is a runtime variable are skipped (cannot resolve).

NOT in scope: ``scripts/`` + ``tests/`` + migration trees (they DELIBERATELY
read the legacy no-env bucket to migrate it). The bucket-naming SSOT modules
themselves (``cloud_constants.py`` / ``bucket_naming.py``) are skipped — they
are where the ``project_id`` forwarding plumbing legitimately lives.

Whitelist inline marker: ``# QG-allow: reading-legacy-bucket-for-migration`` on
the call line bypasses the check for a genuine migration-read.

Usage::

    # per-repo (run by base-service.sh STEP 5.72):
    python check_no_explicit_project_id_bucket.py \\
        --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: Frozen allowlist of PRE-EXISTING legacy-template-literal occurrences (out-of-scope
#: asset groups: tradfi/calendar/onchain/features-sports SSOT-registry + config
#: defaults). Seeded 2026-07-16 when the literal-scan was added (T1.2 of the sports
#: legacy bucket cutover) because >5 pre-existing occurrences surfaced across repos not
#: in the cutover's delete scope. This is a RATCHET that only goes DOWN: new
#: occurrences fail; fixing a baselined one and pruning its entry is the only edit.
#: Tracked for pay-down in ``plans/active/issues/legacy_bucket_template_literals_2026_07_16.md``.
BASELINE_FILENAME: Final[str] = "check_no_explicit_project_id_bucket_baseline.json"

#: Bucket-builder functions that accept an SSOT-bypassing ``project_id``.
BUILDER_NAMES: Final[frozenset[str]] = frozenset({"get_bucket_name", "get_write_bucket_name"})

#: Legacy no-env bucket-name TEMPLATE literals (``.format(project_id=...)`` style).
#: A module-level string literal like ``"instruments-store-sports-{project_id}"`` +
#: ``.format()`` bypasses the ``get_bucket_name`` AST match above entirely — the
#: builder-call check never sees it — so it silently reconstructs the legacy no-env
#: bucket that is DELETED at each asset_group cutover (the exact blind spot that let
#: deployment-service ``data_status_sports.py`` read the legacy sports bucket). The
#: canonical env-tiered form carries an env segment (``…-sports-prd-{project_id}``),
#: whose ``-prd-`` between the group and ``{project_id}`` makes it NOT match this regex.
LEGACY_BUCKET_TEMPLATE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(instruments-store|market-data-tick|features)-[a-z]+-\{project_id\}$"
)

#: Asset-group-split bucket domains (env-tiered + decommissioned at AG cutover).
ASSET_GROUP_DOMAINS: Final[frozenset[str]] = frozenset(
    {
        "instruments",
        "market_data",
        "features_calendar",
        "features_delta_one",
        "features_onchain",
        "features_volatility",
        "features_sports",
        "features_prediction",
    }
)

#: Top-level dir names to skip when walking (scripts/tests/migrations excluded).
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
        "migrations",
        # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
        # older/different snapshot of the same repo's source — scanning one
        # produces false violations for code that doesn't exist in the actual
        # checked-out tree (found live 2026-08-06, same class as the
        # check_manifest_import_alignment.py / test_event_logging.py fixes).
        ".claude",
    }
)

#: Path-fragment patterns that indicate archived / generated / migration trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    "/migration",
    "/migrate",
    ".egg-info",
)

#: SSOT modules where ``project_id`` forwarding plumbing legitimately lives.
EXCLUDE_FILE_NAMES: Final[frozenset[str]] = frozenset({"cloud_constants.py", "bucket_naming.py"})

#: Inline marker on the call line to bypass the check.
WHITELIST_MARKER: Final[str] = "QG-allow: reading-legacy-bucket-for-migration"


@dataclass(frozen=True)
class Finding:
    repo: str
    file: str
    line: int
    func: str
    snippet: str
    literal: str = ""

    @property
    def baseline_key(self) -> str:
        """Line-agnostic identity for the ratchet baseline: repo/file + literal value.

        Deliberately excludes the line number so unrelated edits above a baselined
        occurrence don't spuriously un-baseline it. Keyed on the matched literal so a
        DIFFERENT legacy template added to the same file is NOT silently suppressed.
        """
        return f"{self.repo}/{self.file}\t{self.literal}"


def _iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if parts & EXCLUDE_DIR_NAMES:
            continue
        if path.name in EXCLUDE_FILE_NAMES:
            continue
        s = str(path).replace("\\", "/")
        if any(frag in s for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        yield path


def _line(lines: list[str], lineno: int) -> str:
    return lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""


def _first_arg_domain(node: ast.Call) -> str | None:
    """Return the first positional arg as a string literal, else None."""
    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    return None


def _has_project_id(node: ast.Call) -> bool:
    """True if the call passes project_id (kwarg) OR a 3rd positional arg."""
    if any(kw.arg == "project_id" for kw in node.keywords):
        return True
    # 3rd positional arg of get_bucket_name(domain, asset_group, project_id).
    return len(node.args) >= 3


def _scan_file(path: Path, repo: str, repo_root: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_no_explicit_project_id_bucket] skip unparseable {path}: {exc}", file=sys.stderr)
        return []
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    lines = src.splitlines()
    findings: list[Finding] = []
    for node in ast.walk(tree):
        # (1) SSOT-bypassing builder CALL with an explicit project_id.
        if isinstance(node, ast.Call):
            func = node.func
            fname = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
            if fname not in BUILDER_NAMES:
                continue
            domain = _first_arg_domain(node)
            if domain is None or domain not in ASSET_GROUP_DOMAINS:
                continue
            if not _has_project_id(node):
                continue
            snippet = _line(lines, node.lineno)
            if WHITELIST_MARKER in snippet:
                continue
            findings.append(Finding(repo=repo, file=rel, line=node.lineno, func=fname, snippet=snippet))
            continue
        # (2) Legacy no-env bucket-name TEMPLATE literal (``.format()`` style) — a raw
        #     string constant that reconstructs the deleted no-env bucket, bypassing (1).
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and LEGACY_BUCKET_TEMPLATE_RE.match(node.value)
        ):
            snippet = _line(lines, node.lineno)
            if WHITELIST_MARKER in snippet:
                continue
            findings.append(
                Finding(
                    repo=repo,
                    file=rel,
                    line=node.lineno,
                    func="<legacy-template-literal>",
                    snippet=snippet,
                    literal=node.value,
                )
            )
    return findings


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_no_explicit_project_id_bucket] scope dir not found: {repo_root}", file=sys.stderr)
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


def _load_baseline(path: Path) -> set[str]:
    """Load the frozen allowlist of pre-existing legacy-template-literal occurrences.

    Returns a set of ``Finding.baseline_key`` strings. Absent file → empty set.
    """
    if not path.is_file():
        return set()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "allow" not in raw:
        return set()
    allow = raw["allow"]
    keys: set[str] = set()
    for entry in allow:
        if isinstance(entry, dict) and "file" in entry and "literal" in entry:
            keys.add(f"{entry['file']}\t{entry['literal']}")
    return keys


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ban explicit project_id= on asset-group bucket builders (QG STEP 5.72)."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument("--source-dir", default=None, help="Package sub-dir within the scoped repo.")
    parser.add_argument(
        "--baseline",
        default=None,
        type=Path,
        help="Path to the frozen pre-existing-occurrence allowlist JSON (default: sibling of this script).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline_path: Path = args.baseline if args.baseline is not None else Path(__file__).parent / BASELINE_FILENAME
    baseline: set[str] = _load_baseline(baseline_path)
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_no_explicit_project_id_bucket] no source trees to scan — skipping.")
        return 0

    all_findings: list[Finding] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name
        for py in _iter_py_files(scan_root):
            all_findings.extend(_scan_file(py, repo_name, repo_root))

    # A builder-call finding (func != literal marker) is NEVER baselineable — the
    # original strict check has zero pre-existing occurrences. Only legacy-template
    # LITERALS carry a baseline (pre-existing out-of-scope tech debt).
    errors: list[Finding] = []
    suppressed = 0
    for f in all_findings:
        if f.func == "<legacy-template-literal>" and f.baseline_key in baseline:
            suppressed += 1
            continue
        errors.append(f)

    for f in errors:
        if f.func == "<legacy-template-literal>":
            headline = (
                f"[ERROR] {f.repo}/{f.file}:{f.line}  legacy no-env bucket-name template literal  — "
                f"a raw '<kind>-<group>-{{project_id}}'.format(...) string rebuilds the legacy no-env "
                f"bucket that is DELETED at cutover, bypassing the builder-call check."
            )
        else:
            headline = (
                f"[ERROR] {f.repo}/{f.file}:{f.line}  {f.func}(<asset-group domain>, ..., project_id=...)  — "
                f"explicit project_id bypasses the cloud-providers.yaml SSOT → legacy no-env bucket."
            )
        print(
            f"{headline}\n"
            f"         {f.snippet}\n"
            f"         Use resolve_bucket_name(cloud=..., kind=..., asset_group=...) (or drop the project_id arg so "
            f"the builder delegates to the yaml SSOT → env-tiered -prd- canonical). If genuinely reading the legacy "
            f"bucket to migrate it, add inline marker '# {WHITELIST_MARKER}'.",
            file=sys.stderr,
        )

    if errors:
        print(
            f"\n[check_no_explicit_project_id_bucket] FAIL — {len(errors)} non-baselined occurrence(s) "
            f"({suppressed} pre-existing occurrence(s) suppressed by the frozen baseline).",
            file=sys.stderr,
        )
        return 1
    print(
        f"[check_no_explicit_project_id_bucket] OK — 0 non-baselined occurrences "
        f"({suppressed} pre-existing suppressed by the frozen baseline)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
