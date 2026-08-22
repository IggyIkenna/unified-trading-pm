#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG STEP 5.103 — asyncio script must explicitly drain ManifestWriter before exit.

Per ``plans/active/issues/manifest_atexit_drain_races_asyncio_shutdown_2026_07_09.md``:
``ManifestWriter``'s ``atexit``-registered ``flush_all_pending_buckets()`` handler —
documented as the GUARANTEED drain for fast-exit processes — races the ``asyncio``
event loop's own executor teardown. By the time the ``atexit`` handler runs during
CPython interpreter shutdown, an executor the manifest write path depends on
(``asyncio``'s default ``ThreadPoolExecutor`` / ``gcsfs`` internal threads / GCS
client transport threads) may already be torn down, so the "guaranteed" drain
silently fails (a WARNING log line, not a raised exception) — an asyncio script
relying solely on the ``atexit`` guarantee can lose its final, un-debounced batch
of manifest writes with no visible error in its own success reporting. The
underlying race in ``unified_trading_library`` is unfixed (tracked separately in
the issue doc's P0 items); this check is the "catch new instances going forward"
mitigation for item P2.

What is flagged (whole-FILE, line-based literal-substring match — deliberately
NOT an AST walk; a script either explicitly drains before exit or it doesn't, this
isn't a per-call-site concern like the ``record_*`` kwarg ratchets): a ``.py`` file
that contains BOTH ``asyncio.run(`` AND ``MANIFEST_PER_VM_SHARDS`` (the per-VM
per-shard manifest mode this race was discovered under) but does NOT contain
``flush_all_pending_buckets(`` anywhere in the same file — i.e. an asyncio-driven
script that opts into per-VM shard manifest writes without an explicit pre-exit
drain call.

Per-file opt-out: ``# noqa: qg-asyncio-manifest-drain`` anywhere in the file, with
an optional one-line reason (e.g. a script that only ever reads the manifest, or
whose ``MANIFEST_PER_VM_SHARDS`` reference is a docstring/comment, not an actual
env-var set).

Shape — **baseline ratchet** (NOT zero-tolerance; the 2026-07-09 sweep found 3
pre-existing instruments-service backfill scripts with the anti-pattern, filed as
a separate P1 audit item in the sibling issue doc — this gate exists to stop the
count from GROWING while that backlog is worked off):

  1. Load ``asyncio_manifest_explicit_drain_baseline.yaml`` — a per-repo count of
     the currently-known offending files (those WITHOUT the noqa marker).
  2. Scan every ``.py`` file under the scan root (skipping venvs / build
     artefacts / archived trees / tests).
  3. count <= baseline -> OK (a WARN when strictly below, so the operator
     ratchets the baseline DOWN). count > baseline -> ERROR (exit 1): a NEW
     offending file landed — add an explicit ``_mw.flush_all_pending_buckets()``
     call at the end of the asyncio ``main()`` coroutine (while the event loop and
     its executors are still alive, before ``asyncio.run()`` returns), or add
     ``# noqa: qg-asyncio-manifest-drain`` with a one-line reason for a genuinely
     deliberate, safe case.

The baseline ONLY shrinks: re-run with ``--update-baseline`` after fixing sites
(counts are clamped DOWN — never raised).

Usage::

    # per-repo (run by base-service.sh STEP 5.103):
    python check_asyncio_manifest_explicit_drain.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_asyncio_manifest_explicit_drain.py --workspace-root <ws>

    # ratchet the baseline DOWN after fixing sites:
    python check_asyncio_manifest_explicit_drain.py --workspace-root <ws> --update-baseline

Exit codes: 0 = clean / at-or-below baseline; 1 = over baseline; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: The "grandfathered, intentional" per-file exemption marker.
NOQA_MARKER: Final[str] = "noqa: qg-asyncio-manifest-drain"

#: Literal substrings that make up the anti-pattern. A file that contains both
#: MUST-markers but not the drain marker is flagged.
_MUST_HAVE_MARKERS: Final[tuple[str, ...]] = ("asyncio.run(", "MANIFEST_PER_VM_SHARDS")
_DRAIN_MARKER: Final[str] = "flush_all_pending_buckets("

#: Top-level dir names to skip when walking. Deliberately does NOT exclude
#: `scripts/` — the anti-pattern lives almost entirely in one-off backfill/closer
#: scripts under `scripts/backfill/` etc., so excluding it would blind the check.
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
        "testing",
        # Agent-local scratch (Claude Code worktrees + settings) and the Cursor
        # equivalent — ephemeral copies of the repo nested under the scope; never
        # source. Without this an isolated agent worktree double-counts every site.
        ".claude",
        ".cursor",
    }
)

#: Path-fragment patterns that indicate archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)

#: Test-file basename patterns (skipped — defensive, in case a test file lives
#: outside a `tests/`/`testing/` dir).
TEST_FILE_PREFIXES: Final[tuple[str, ...]] = ("test_",)
TEST_FILE_SUFFIXES: Final[tuple[str, ...]] = ("_test.py",)


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "asyncio_manifest_explicit_drain_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts of offending files."""

    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))


def load_baseline(path: Path | None = None) -> Baseline:
    baseline_file = path if path is not None else _baseline_path()
    if not baseline_file.exists():
        return Baseline()
    raw = yaml.safe_load(baseline_file.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, int] = {}
    for repo, val in repos_raw.items():
        if isinstance(val, dict):
            counts[str(repo)] = int(val.get("count", 0))
        else:
            counts[str(repo)] = int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline, path: Path | None = None) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised above the
    existing baseline (a higher count means a new offending file landed; fix it,
    don't bake it in)."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        if repo not in counts:
            # Not scanned this run (scoped --update-baseline) — carry the existing
            # row forward verbatim. Treating unobserved as 0 + down-clamp zeroes the
            # fleet (same defect class as check_ruff_rule_ratchet, incident 2026-06-10).
            merged[repo] = {"count": existing.allowed(repo)}
            continue
        observed = int(counts[repo])
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for QG STEP 5.103 — asyncio-script-must-explicitly-drain-manifest ratchet.\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of `.py`\n"
        "# files (WITHOUT a `# noqa: qg-asyncio-manifest-drain` marker) the gate\n"
        "# tolerates in that repo that call `asyncio.run(` AND reference\n"
        "# `MANIFEST_PER_VM_SHARDS` but have no explicit `flush_all_pending_buckets(`\n"
        "# call in the same file (tests/ + testing/ excluded). A repo whose live count\n"
        "# EXCEEDS its baseline fails CI — a NEW offending file landed; add an explicit\n"
        "# `_mw.flush_all_pending_buckets()` call before `asyncio.run()` returns, or add\n"
        "# `# noqa: qg-asyncio-manifest-drain` with a one-line reason for a genuinely\n"
        "# deliberate, safe case.\n"
        "#\n"
        "# LOWER a count (re-run `--update-baseline`) the moment sites are fixed.\n"
        "# NEVER raise a count. Repos not listed default to count=0.\n"
        "#\n"
        "# SSOT: plans/active/issues/manifest_atexit_drain_races_asyncio_shutdown_2026_07_09.md.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note
            or ("Seeded 2026-07-09 — manifest_atexit_drain_races_asyncio_shutdown fleet sweep (QG STEP 5.103)."),
            "repos": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = baseline_file.write_text(header + body, encoding="utf-8")


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
        if _is_excluded_path(path):
            continue
        yield path


def file_missing_explicit_drain(source_path: Path) -> bool:
    """True if this file has the anti-pattern: asyncio.run( + MANIFEST_PER_VM_SHARDS
    both present, no explicit flush_all_pending_buckets( call, and no noqa marker."""
    try:
        text = source_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if NOQA_MARKER in text:
        return False
    if not all(marker in text for marker in _MUST_HAVE_MARKERS):
        return False
    return _DRAIN_MARKER not in text


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[str]  # repo-relative file paths


def scan_repo(scan_root: Path, repo_name: str, repo_root: Path | None = None) -> RepoScan:
    rel_base = repo_root if repo_root is not None else scan_root
    sites: list[str] = []
    for py in _iter_py_files(scan_root):
        if file_missing_explicit_drain(py):
            rel = py.relative_to(rel_base).as_posix() if py.is_relative_to(rel_base) else py.as_posix()
            sites.append(rel)
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    """Return [(repo_name, scan_root)]. --scope -> that repo only (optionally
    narrowed to --source-dir under it). Else every immediate git-repo sub-dir."""
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(
                f"[check_asyncio_manifest_explicit_drain] --scope {scope!r} not under {workspace_root}",
                file=sys.stderr,
            )
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
    parser = argparse.ArgumentParser(
        description="asyncio-script-must-explicitly-drain-manifest ratchet (QG STEP 5.103)."
    )
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
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=None,
        help="Override the baseline yaml path (unit tests only).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline_file: Path | None = args.baseline_file
    baseline = load_baseline(baseline_file)
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_asyncio_manifest_explicit_drain] no repos in scope.", file=sys.stderr)
        return 0  # nothing to check — not a failure

    observed: dict[str, int] = {}
    failures: list[str] = []
    info_lines: list[str] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name if (workspace_root / repo_name).is_dir() else scan_root
        scan = scan_repo(scan_root, repo_name, repo_root=repo_root)
        observed[repo_name] = scan.count
        allowed = baseline.allowed(repo_name)
        if scan.count > allowed:
            over = scan.sites[allowed:] if allowed < len(scan.sites) else scan.sites
            sites_str = "; ".join(over[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} offending file(s) > baseline {allowed}. "
                f"New/over-baseline file(s): {sites_str}" + (" ..." if len(over) > 20 else "")
            )
        elif scan.count < allowed:
            info_lines.append(
                f"[WARN] {repo_name}: {scan.count} < baseline {allowed} — ratchet the baseline DOWN "
                f"(re-run `--update-baseline`)."
            )
        else:
            info_lines.append(f"[OK]   {repo_name}: {scan.count} (== baseline)")

    if args.update_baseline:
        write_baseline(observed, baseline, baseline_file)
        print(f"[check_asyncio_manifest_explicit_drain] baseline updated at {baseline_file or _baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n→ A file that calls asyncio.run( and sets/reads MANIFEST_PER_VM_SHARDS must also call "
            "_mw.flush_all_pending_buckets() explicitly BEFORE asyncio.run() returns — the atexit-registered "
            "drain races the event loop's own executor teardown and can silently drop buffered manifest writes "
            "(WARNING log line, no raised exception). For a genuinely deliberate, safe case (e.g. read-only "
            "manifest access, or a docstring/comment mention of the env var) add "
            "`# noqa: qg-asyncio-manifest-drain` with a one-line reason. SSOT: "
            "plans/active/issues/manifest_atexit_drain_races_asyncio_shutdown_2026_07_09.md. "
            "Baseline: unified-trading-pm/scripts/quality_gates/asyncio_manifest_explicit_drain_baseline.yaml "
            "(NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
