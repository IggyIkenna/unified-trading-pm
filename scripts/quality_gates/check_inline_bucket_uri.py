#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG STEP 5.69 — inline ``f"gs://..."`` / ``f"s3://..."`` cloud-URI formatter ratchet.

Enforces CLAUDE.md "Bucket-name SSOT (b+)": every bucket lookup goes through
``unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)``
(or ``resolve_bucket_uri(...)`` for a full URI) — never an inline f-string that
builds a ``gs://`` / ``s3://`` URI by hand. Scattering inline ``f"gs://{bucket}/..."``
formatters across services is how the workspace ended up with the bucket-name
triple-drift the ``bucket_name_ssot_canonicalisation_2026_05_10.md`` plan exists
to collapse (yaml SSOT vs per-family ``config.py`` template vs UTL resolver vs
deployment-api's own internal templates — see that plan's pre-audit manifest
"Layer 1-5").

Shape — **baseline ratchet** (NOT zero-tolerance from day 1). There are dozens
of legitimate ``f"gs://{already_resolved_bucket}/{path}"`` sites — composing a
URI from a *resolved* bucket var + a path is fine — that won't all migrate to
``resolve_bucket_uri()`` at once. So:

  1. Load ``inline_bucket_uri_baseline.yaml`` — a per-repo count of the
     CURRENTLY-KNOWN inline ``f"gs://...`` / ``f"s3://...`` formatters in service
     source (excluding lines carrying a ``# noqa: gs-uri`` marker — the
     "grandfathered, intentional" exemption, already used ~16x in
     execution-service etc.).
  2. Scan every ``.py`` file under the given source dir(s) (skipping venvs /
     build artefacts / archived trees / ``scripts/`` / ``tests/``) and count
     the inline formatters NOT carrying ``# noqa: gs-uri``.
  3. If a repo's count is ``<=`` its baseline → OK (a warning if it's
     ``< baseline`` so the operator knows to ratchet the baseline DOWN). If a
     repo's count ``> baseline`` → ERROR (exit 1) — a NEW inline formatter
     landed; route it through ``resolve_bucket_uri()`` or add a ``# noqa: gs-uri``
     with a one-line reason.

The baseline ONLY shrinks: when consumers migrate to ``resolve_bucket_uri()`` (or
the to-be-removed inline bucket-name templates land in ``code_freeze`` Phase 2.6),
re-run with ``--update-baseline`` to lower the recorded counts. NEVER raise a
baseline (a new inline formatter is a bug, not a baseline item).

v2 is AST-walk based: distinguishes ``f"gs://{x}/..."`` (inline URI build, flagged)
from ``resolve_bucket_uri(...)`` calls (not flagged), and ignores f-strings that
are docstrings — eliminating false positives from documentation examples such as
``bucket_naming.py:16-17``. Falls back to the v1 regex scan for files with syntax
errors. Same shape as QG STEP 5.65's AST-walk.

Usage::

    # per-repo (run by base-service.sh STEP 5.69):
    python check_inline_bucket_uri.py --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>

    # workspace-wide sweep:
    python check_inline_bucket_uri.py --workspace-root <ws>

    # ratchet the baseline DOWN after a migration:
    python check_inline_bucket_uri.py --workspace-root <ws> --update-baseline
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: The "grandfathered, intentional" exemption marker. A line carrying this is
#: skipped entirely (it's a deliberate, audited URI composition).
NOQA_MARKER: Final[str] = "noqa: gs-uri"

#: Matches an f-string literal opener (``f"`` / ``f'`` / ``rf"`` / ``fr'`` / the
#: triple-quoted variants) somewhere before a ``gs://`` or ``s3://`` on the same
#: line. ``re.search`` (not match) — the f-string need not be at line start.
#: A line that has ``gs://`` / ``s3://`` only inside a *plain* string (no ``f``
#: prefix), e.g. ``cloud_path.startswith("gs://")``, does NOT match — that's a
#: scheme check, not a URI build.
_INLINE_URI_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    (?:^|[^A-Za-z0-9_])      # f-prefix not preceded by an identifier char
    (?:r?f|fr)               # f / rf / fr
    (?P<quote>['"]{1,3})     # opening quote(s)
    [^\n]*?                  # ... any chars (non-greedy) up to ...
    (?:gs|s3)://             # ... a gs:// or s3:// scheme
    """,
    re.VERBOSE,
)

#: Top-level dir names to skip when walking. Mirrors check_banned_placeholder_methods.py.
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
        "scripts",  # per "Schema provenance" rule — scripts/ excluded from strict checks
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

#: Test-file basename patterns (also skipped — they pin URI shapes in fixtures).
TEST_FILE_PREFIXES: Final[tuple[str, ...]] = ("test_",)
TEST_FILE_SUFFIXES: Final[tuple[str, ...]] = ("_test.py",)


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "inline_bucket_uri_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts of inline ``gs://`` / ``s3://`` f-strings."""

    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))


def load_baseline() -> Baseline:
    path = _baseline_path()
    if not path.exists():
        return Baseline()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, int] = {}
    for repo, val in repos_raw.items():
        if isinstance(val, dict):
            counts[str(repo)] = int(val.get("count", 0))
        else:
            counts[str(repo)] = int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised above the
    existing baseline (a higher count means a new inline formatter landed; fix
    it, don't bake it in)."""
    path = _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        observed = int(counts.get(repo, 0))
        prior = existing.allowed(repo)
        # Only lower (or keep). If observed > prior the gate already failed —
        # don't silently raise.
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        '# Baseline for QG STEP 5.69 — inline `f"gs://..."` / `f"s3://..."` cloud-URI formatter ratchet.\n'
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of inline\n"
        '# `f"gs://...`/`f"s3://...` formatters (WITHOUT a `# noqa: gs-uri` marker) the\n'
        "# gate tolerates in that repo's service source (scripts/ + tests/ excluded). A\n"
        "# repo whose live count EXCEEDS its baseline fails CI — a NEW inline formatter\n"
        "# landed; route it through `unified_trading_library.cloud_interface.bucket_naming.\n"
        "# resolve_bucket_uri(...)` or add `# noqa: gs-uri` with a one-line reason.\n"
        "#\n"
        "# LOWER a count (re-run `--update-baseline`) the moment a migration removes inline\n"
        "# formatters — e.g. when the to-be-removed inline bucket-name templates land in\n"
        "# code_freeze Phase 2.6 (bucket_name_ssot_canonicalisation_2026_05_10.md Done-def\n"
        "# #3 / GAP-2.4.D deployment-api reader-repoint). NEVER raise a count.\n"
        "#\n"
        "# Repos not listed default to count=0 (zero tolerance — any inline formatter fails).\n"
        "#\n"
        '# SSOT for WHY: CLAUDE.md "Bucket-name SSOT (b+)" + bucket_name_ssot_canonicalisation_2026_05_10.md\n'
        '# (pre-audit manifest Layers 1-5 + "QG STEP 5.6X design"). The `# noqa: gs-uri` marker\n'
        "# convention is documented in execution-service/BYPASS_AUDIT.md + strategy-service/pyproject.toml.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-05-11 (slot 4) - bucket_name_ssot Done-def #5 (QG STEP 5.69).",
            "repos": merged,
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
        if _is_excluded_path(path.relative_to(root) if path.is_relative_to(root) else path):
            continue
        if _is_excluded_path(path):
            continue
        yield path


def _ast_docstring_lines(tree: ast.AST) -> frozenset[int]:
    """Return line numbers occupied by module/class/function docstrings.

    Both plain-string and f-string docstrings are captured so that URIs used
    as documentation examples are not flagged by the AST walker.
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if not isinstance(first, ast.Expr):
            continue
        val = first.value
        if not isinstance(val, (ast.Constant, ast.JoinedStr)):
            continue
        start: int | None = getattr(val, "lineno", None)
        end: int | None = getattr(val, "end_lineno", start)
        if start is not None:
            for ln in range(start, (end if end is not None else start) + 1):
                lines.add(ln)
    return frozenset(lines)


def _fstring_has_cloud_uri(node: ast.JoinedStr) -> bool:
    """Return True if any literal constant part of the f-string contains ``gs://`` or ``s3://``."""
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Constant)
            and isinstance(child.value, str)
            and ("gs://" in child.value or "s3://" in child.value)
        ):
            return True
    return False


def _count_inline_uris_regex(source: str) -> list[int]:
    """v1 fallback: regex-based line scan (used when AST parse fails due to syntax errors)."""
    hits: list[int] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if NOQA_MARKER in line:
            continue
        if _INLINE_URI_RE.search(line):
            hits.append(lineno)
    return hits


def count_inline_uris_in_file(path: Path) -> list[int]:
    """Return the line numbers (1-based) of inline ``gs://`` / ``s3://`` f-string
    formatters in ``path`` that do NOT carry a ``# noqa: gs-uri`` marker.

    v2: AST-walk that skips docstrings (plain-string and f-string) to eliminate
    false positives from documentation examples. Falls back to the v1 regex scan
    for files that fail to parse (syntax errors).
    """
    hits: list[int] = []
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return hits

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return _count_inline_uris_regex(source)

    source_lines = source.splitlines()
    docstring_lines = _ast_docstring_lines(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        lineno: int | None = getattr(node, "lineno", None)
        if lineno is None:
            continue
        if lineno in docstring_lines:
            continue  # URI is a documentation example, not a live build
        if not _fstring_has_cloud_uri(node):
            continue
        source_line = source_lines[lineno - 1] if lineno <= len(source_lines) else ""
        if NOQA_MARKER in source_line:
            continue  # grandfathered inline URI
        hits.append(lineno)

    return sorted(hits)


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[tuple[str, int]]  # (repo-relative-file, line)


def scan_repo(repo_root: Path, repo_name: str) -> RepoScan:
    sites: list[tuple[str, int]] = []
    src_root = repo_root
    for py in _iter_py_files(src_root):
        for ln in count_inline_uris_in_file(py):
            rel = py.relative_to(repo_root).as_posix() if py.is_relative_to(repo_root) else py.as_posix()
            sites.append((rel, ln))
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    """Return [(repo_name, scan_root)]. If --scope given → just that repo
    (optionally narrowed to --source-dir under it). Else → every immediate
    sub-dir of workspace_root that has a .git."""
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_inline_bucket_uri] --scope {scope!r} not a dir under {workspace_root}", file=sys.stderr)
            return []
        scan_root = repo_root / source_dir if source_dir else repo_root
        if not scan_root.exists():
            scan_root = repo_root
        return [(scope, scan_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in EXCLUDE_DIR_NAMES or child.name.startswith("."):
            continue
        if (child / ".git").exists():
            out.append((child.name, child))
    return out


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inline gs://|s3:// f-string URI-formatter ratchet (QG STEP 5.69).")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name (per-repo QG mode).")
    parser.add_argument(
        "--source-dir", default=None, help="Sub-dir under --scope to narrow the scan to (e.g. the package dir)."
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed counts (clamped DOWN — never raised).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    update_baseline_flag = bool(args.update_baseline)
    baseline = load_baseline()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_inline_bucket_uri] no repos in scope.", file=sys.stderr)
        return 0  # nothing to check — not a failure

    observed: dict[str, int] = {}
    failures: list[str] = []
    warnings: list[str] = []
    for repo_name, scan_root in scopes:
        scan = scan_repo(scan_root, repo_name)
        observed[repo_name] = scan.count
        allowed = baseline.allowed(repo_name)
        if scan.count > allowed:
            new_sites = scan.sites[allowed:] if allowed < len(scan.sites) else scan.sites
            sites_str = "; ".join(f"{f}:{ln}" for f, ln in new_sites[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} inline gs://|s3:// f-string formatter(s) "
                f"> baseline {allowed}. New/over-baseline site(s): {sites_str}"
                + (" ..." if len(new_sites) > 20 else "")
            )
        elif scan.count < allowed:
            warnings.append(
                f"[WARN] {repo_name}: {scan.count} < baseline {allowed} — ratchet the baseline DOWN "
                f"(re-run `--update-baseline`)."
            )
        else:
            warnings.append(f"[OK]   {repo_name}: {scan.count} (== baseline)")

    if update_baseline_flag:
        write_baseline(observed, baseline)
        print(f"[check_inline_bucket_uri] baseline updated at {_baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for w in warnings:
        print(w)
    for f in failures:
        print(f, file=sys.stderr)
    if failures:
        print(
            "\n→ Route the new formatter through `unified_trading_library.cloud_interface.bucket_naming."
            "resolve_bucket_uri(cloud=..., kind=..., path=..., asset_group=...)` (or `resolve_bucket_name(...)` "
            "+ compose), OR add `# noqa: gs-uri` with a one-line reason if it's a deliberate, audited URI "
            'composition from an already-resolved bucket var. SSOT: CLAUDE.md "Bucket-name SSOT (b+)" + '
            "bucket_name_ssot_canonicalisation_2026_05_10.md (§ QG STEP 5.6X design). Baseline: "
            "unified-trading-pm/scripts/quality_gates/inline_bucket_uri_baseline.yaml (NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
