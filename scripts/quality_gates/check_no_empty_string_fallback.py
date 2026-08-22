#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG STEP 5.101 — ``.get("key", "")`` empty-string-fallback ratchet.

Enforces "Empty string fallback — fail fast": a dict `.get("key", "")` call
silently swaps a genuinely-missing/error-worthy field for an empty string,
letting bad data flow through undetected instead of failing loud at the point
of the missing field. This mirrors the workspace's `no-empty-fallbacks.mdc`
family of rules (same spirit as the try/except-ImportError fallback-import
ban — QG STEP 5.94/`check_no_fallback_imports.py`).

Until 2026-07-08 this was wired directly into `base-service.sh`/
`base-library.sh` as an inline `codex_rg` zero-tolerance check (``max allowed:
0``) with NO baseline-ratchet — unlike its DTZ/TID251/fallback-import
siblings, which explicitly grandfather pre-existing debt via a per-repo
baseline so it doesn't grow. Because zero-tolerance covered the ENTIRE fleet
from day one with no ratchet, any repo carrying pre-existing debt for this
pattern (several do) has its `quality-gates.sh` permanently red, blocking
EVERY quickmerge push to that repo — not just changes that touch the pattern.
See ``plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md``.

What is flagged (line-based regex — matches the retired inline ``codex_rg``
pattern): a ``.get("key", "")`` / ``.get('key', '')`` call (either quote style,
independently on each side) whose default value is an empty string literal.

Per-line opt-out: ``# noqa: qg-empty-fallback`` anywhere on the line, with an
optional one-line reason after an em-dash (already used at ~250 sites in this
fleet, e.g. ``market_tick_data_service/market_interface/adapters/bybit.py``,
``.../clients/thegraph_base_client.py`` — a deliberate, safe "field may be
absent, empty string is a meaningful not-present value" case).

Shape — **baseline ratchet** (NOT zero-tolerance; 2026-07-08 fleet audit
measured the real per-repo counts below):

  1. Load ``no_empty_string_fallback_baseline.yaml`` — a per-repo count of the
     currently-known empty-string-fallback sites (those WITHOUT ``# noqa:
     qg-empty-fallback``).
  2. Scan every ``.py`` file under the scan root (skipping venvs / build
     artefacts / archived trees / tests).
  3. count <= baseline -> OK (a WARN when strictly below, so the operator
     ratchets the baseline DOWN). count > baseline -> ERROR (exit 1): a NEW
     empty-string-fallback site landed — rewrite it to fail fast (raise, or
     return `None` and let the caller decide), or add ``# noqa:
     qg-empty-fallback`` with a one-line reason for a genuinely deliberate,
     safe case.

The baseline ONLY shrinks: re-run with ``--update-baseline`` after fixing
sites (counts are clamped DOWN — never raised).

Over-baseline reporting: each ``--update-baseline`` run also stamps the
scanned repo's own current HEAD sha into the baseline row (``commit:``). A
later over-baseline failure git-diffs the repo against that recorded commit
to report the sites genuinely ADDED since then, instead of an arbitrary
positional tail-slice of the full (alphabetically-sorted) site list — the
old approach could report 2-month-old code that merely sorted last
(``instruments_service_empty_string_fallback_baseline_breach_2026_07_14.md``).
A repo whose baseline predates this field (no ``commit:`` recorded yet, or
the recorded commit is unreachable in a shallow/rebased clone) falls back to
the old positional tail-slice, clearly labelled as such in the failure line.

Usage::

    # per-repo (run by base-service.sh / base-library.sh STEP 5.101):
    python check_no_empty_string_fallback.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_no_empty_string_fallback.py --workspace-root <ws>

    # ratchet the baseline DOWN after fixing sites:
    python check_no_empty_string_fallback.py --workspace-root <ws> --update-baseline

Exit codes: 0 = clean / at-or-below baseline; 1 = over baseline; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: The "grandfathered, intentional" per-line exemption marker code.
NOQA_MARKER: Final[str] = "noqa: qg-empty-fallback"

#: A single "noqa" comment carrying multiple codes (space- and/or comma-separated
#: after one prefix — e.g. combining a qg-os-environ exemption with this one on
#: the same line) is a real, existing convention in this workspace — a plain
#: `NOQA_MARKER in line` substring check misses it whenever another code sits
#: between the prefix and this check's own code. Parse the full code list instead.
_NOQA_CODES_PATTERN: Final[re.Pattern[str]] = re.compile(r"#\s*noqa:\s*([\w,\s-]+)")

#: Mirrors the retired inline codex_rg pattern in base-service.sh/base-library.sh:
#: `\.get\(["\x27][\w_]+["\x27]\s*,\s*["\x27]["\x27]\)` — either quote style
#: independently on each side of the key and of the empty-string default.
_EMPTY_STR_PATTERN: Final[re.Pattern[str]] = re.compile(r"""\.get\(["'][\w]+["']\s*,\s*["']["']\)""")

#: Top-level dir names to skip when walking. Mirrors check_no_fallback_imports.py,
#: plus `testing` (base-library.sh's variant of this check also excludes
#: `**/testing/**` — in-package test-support utilities).
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
    return Path(__file__).resolve().parent / "no_empty_string_fallback_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts of empty-string-fallback sites."""

    counts: dict[str, int] = field(default_factory=dict)
    #: repo -> the HEAD sha of that repo's own git history at the moment its
    #: `count` was last set via `--update-baseline`. Powers git-diff-based
    #: over-baseline reporting (see `_diff_added_empty_string_sites`) — a repo
    #: whose baseline predates this field simply has no entry and falls back
    #: to the positional tail-slice.
    commits: dict[str, str] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))

    def commit_for(self, repo: str) -> str | None:
        return self.commits.get(repo)


def load_baseline(path: Path | None = None) -> Baseline:
    baseline_file = path if path is not None else _baseline_path()
    if not baseline_file.exists():
        return Baseline()
    raw = yaml.safe_load(baseline_file.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, int] = {}
    commits: dict[str, str] = {}
    for repo, val in repos_raw.items():
        if isinstance(val, dict):
            counts[str(repo)] = int(val.get("count", 0))
            commit = val.get("commit")
            if commit:
                commits[str(repo)] = str(commit)
        else:
            counts[str(repo)] = int(val)
    return Baseline(counts=counts, commits=commits, note=str(raw.get("note") or ""))


def _current_commit(repo_root: Path) -> str | None:
    """Best-effort HEAD sha for *repo_root* — None if it isn't a git repo (or git
    is unavailable). Never raises: this is a nice-to-have for diff-based
    reporting, not load-bearing for the baseline check itself."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha or None


def write_baseline(
    counts: dict[str, int],
    existing: Baseline,
    path: Path | None = None,
    repo_roots: dict[str, Path] | None = None,
) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised above the
    existing baseline (a higher count means a new site landed; fix it, don't
    bake it in). When *repo_roots* is given, also stamp each scanned repo's
    current HEAD sha so a future over-baseline failure can git-diff against it
    instead of guessing from a positional tail-slice."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int | str]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        if repo not in counts:
            # Not scanned this run (scoped --update-baseline) — carry the existing
            # row forward verbatim. Treating unobserved as 0 + down-clamp zeroes the
            # fleet (same defect class as check_ruff_rule_ratchet, incident 2026-06-10).
            row: dict[str, int | str] = {"count": existing.allowed(repo)}
            existing_commit = existing.commit_for(repo)
            if existing_commit:
                row["commit"] = existing_commit
            merged[repo] = row
            continue
        observed = int(counts[repo])
        prior = existing.allowed(repo)
        row = {"count": min(observed, prior) if repo in existing.counts else observed}
        repo_root = (repo_roots or {}).get(repo)
        commit = (_current_commit(repo_root) if repo_root is not None else None) or existing.commit_for(repo)
        if commit:
            row["commit"] = commit
        merged[repo] = row
    header = (
        '# Baseline for QG STEP 5.101 — .get("key", "") empty-string-fallback ratchet.\n'
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of\n"
        "# `.get(\"key\", \"\")` / `.get('key', '')` empty-string-fallback call sites\n"  # noqa: qg-empty-fallback — doc text describing the pattern, not a real call site
        "# (WITHOUT a `# noqa: qg-empty-fallback` marker) the gate tolerates in that\n"
        "# repo (tests/ + testing/ excluded). A repo whose live count EXCEEDS its\n"
        "# baseline fails CI — a NEW site landed; rewrite it to fail fast (raise, or\n"
        "# return None and let the caller decide), or add `# noqa: qg-empty-fallback`\n"
        "# with a one-line reason for a genuinely deliberate, safe case.\n"
        "#\n"
        "# LOWER a count (re-run `--update-baseline`) the moment sites are fixed.\n"
        "# NEVER raise a count. Repos not listed default to count=0.\n"
        "#\n"
        "# `repos[<repo>].commit` is that repo's own HEAD sha at the moment `count`\n"
        "# was last set — used to git-diff-detect genuinely NEW over-baseline sites\n"
        "# instead of an arbitrary positional tail-slice. Set automatically by\n"
        "# `--update-baseline`; do not hand-edit.\n"
        "#\n"
        "# SSOT: plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,\n"
        "# plans/active/issues/instruments_service_empty_string_fallback_baseline_breach_2026_07_14.md.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note
            or (
                "Seeded 2026-07-08 — mtds_empty_string_fallback_codex_gate_blocking_pushes fleet audit (QG STEP 5.101)."
            ),
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


def find_empty_string_fallbacks(source_path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, line_content)] of empty-string-fallback sites in a file."""
    try:
        lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    hits: list[tuple[int, str]] = []
    for lineno, raw_line in enumerate(lines, start=1):
        if not _EMPTY_STR_PATTERN.search(raw_line):
            continue
        if _has_empty_fallback_noqa(raw_line):
            continue
        hits.append((lineno, raw_line.rstrip()))
    return hits


def _has_empty_fallback_noqa(line: str) -> bool:
    """Whether *line* carries a `qg-empty-fallback` code inside a `# noqa: ...` comment.

    Handles a single-code comment (`# noqa: qg-empty-fallback`), a multi-code one
    (`# noqa: qg-os-environ qg-empty-fallback`, or comma-separated) in ONE cluster,
    AND two (or more) SEPARATE `# noqa: ...` clusters on the same line
    (`# noqa: qg-os-env  # noqa: qg-empty-fallback`) — scans every cluster via
    ``finditer`` and unions their codes, since ``.search()`` alone only sees the
    first cluster and misses a code stacked in a later one
    (`qg_empty_string_fallback_checker_misses_stacked_noqa_2026_07_13.md`).
    """
    codes: set[str] = set()
    for match in _NOQA_CODES_PATTERN.finditer(line):
        codes.update(re.split(r"[,\s]+", match.group(1).strip()))
    return "qg-empty-fallback" in codes


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[tuple[str, int, str]]  # (repo-relative-file, line, content)


def scan_repo(scan_root: Path, repo_name: str, repo_root: Path | None = None) -> RepoScan:
    rel_base = repo_root if repo_root is not None else scan_root
    sites: list[tuple[str, int, str]] = []
    for py in _iter_py_files(scan_root):
        for lineno, content in find_empty_string_fallbacks(py):
            rel = py.relative_to(rel_base).as_posix() if py.is_relative_to(rel_base) else py.as_posix()
            sites.append((rel, lineno, content))
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Git-diff-based over-baseline reporting ──────────────────────────────────


def _diff_added_empty_string_sites(repo_root: Path, baseline_commit: str) -> set[tuple[str, str]] | None:
    """Return {(repo-relative-file, line-content)} of `.get(key, "")` sites ADDED
    in *repo_root* since *baseline_commit* — i.e. lines a unified diff shows as
    `+` that themselves match the empty-string-fallback pattern (and don't carry
    the noqa opt-out). Line numbers drift across commits, so this dedupes on
    content, not (file, lineno).

    Returns None (not an empty set) when the diff can't be computed at all —
    unknown/unreachable commit, not a git repo, git unavailable — so the caller
    can tell "diff came back empty" apart from "diff wasn't possible" and fall
    back to the positional tail-slice instead of reporting a false "no new
    sites".
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--unified=0", f"{baseline_commit}..HEAD", "--", "*.py"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None

    added: set[tuple[str, str]] = set()
    current_file: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("+++ "):
            raw_path = line[4:].strip()
            current_file = None if raw_path == "/dev/null" else raw_path.removeprefix("b/")
            continue
        if line.startswith(("+++", "---")):
            continue
        if not line.startswith("+"):
            continue
        content = line[1:]
        if current_file is None or _is_excluded_path(Path(current_file)):
            continue
        if _EMPTY_STR_PATTERN.search(content) and not _has_empty_fallback_noqa(content):
            added.add((current_file, content.rstrip()))
    return added


def _resolve_over_baseline_sites(
    scan: RepoScan, allowed: int, repo_root: Path, baseline_commit: str | None
) -> tuple[list[tuple[str, int, str]], str]:
    """Return (sites-to-report, detection-note). Prefers git-diff-based detection
    of genuinely NEW sites since *baseline_commit*; falls back to the old
    positional tail-slice (`scan.sites[allowed:]`) — which can surface arbitrary
    pre-existing code that merely sorts last — when no baseline commit is on
    record yet, or the diff can't be computed (e.g. the commit isn't reachable
    in a shallow/rebased clone)."""
    fallback = scan.sites[allowed:] if allowed < len(scan.sites) else scan.sites
    if not baseline_commit:
        return fallback, " (positional tail-slice — no baseline commit on record for this repo yet)"
    diff_sites = _diff_added_empty_string_sites(repo_root, baseline_commit)
    if diff_sites is None:
        return fallback, " (positional tail-slice — git-diff against the baseline commit failed)"
    over = [site for site in scan.sites if (site[0], site[2]) in diff_sites]
    if not over:
        # Diff-detected zero live matches (e.g. sites moved/reformatted since the
        # baseline commit) — still tell the caller something over-baseline exists.
        return fallback, " (positional tail-slice — git-diff found no new sites still present; may be a move/reformat)"
    return over, ""


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    """Return [(repo_name, scan_root)]. --scope -> that repo only (optionally
    narrowed to --source-dir under it). Else every immediate git-repo sub-dir."""
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_no_empty_string_fallback] --scope {scope!r} not under {workspace_root}", file=sys.stderr)
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
        description='.get("key", "") empty-string-fallback ratchet (QG STEP 5.101).'  # noqa: qg-empty-fallback — doc text describing the pattern, not a real call site
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
        print("[check_no_empty_string_fallback] no repos in scope.", file=sys.stderr)
        return 0  # nothing to check — not a failure

    observed: dict[str, int] = {}
    repo_roots: dict[str, Path] = {}
    failures: list[str] = []
    info_lines: list[str] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name if (workspace_root / repo_name).is_dir() else scan_root
        repo_roots[repo_name] = repo_root
        scan = scan_repo(scan_root, repo_name, repo_root=repo_root)
        observed[repo_name] = scan.count
        allowed = baseline.allowed(repo_name)
        if scan.count > allowed:
            baseline_commit = baseline.commit_for(repo_name)
            over, detection_note = _resolve_over_baseline_sites(scan, allowed, repo_root, baseline_commit)
            sites_str = "; ".join(f"{f}:{ln}" for f, ln, _content in over[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} empty-string-fallback site(s) > baseline {allowed}. "
                f"New/over-baseline site(s){detection_note}: {sites_str}" + (" ..." if len(over) > 20 else "")
            )
        elif scan.count < allowed:
            info_lines.append(
                f"[WARN] {repo_name}: {scan.count} < baseline {allowed} — ratchet the baseline DOWN "
                f"(re-run `--update-baseline`)."
            )
        else:
            info_lines.append(f"[OK]   {repo_name}: {scan.count} (== baseline)")

    if args.update_baseline:
        write_baseline(observed, baseline, baseline_file, repo_roots=repo_roots)
        print(f"[check_no_empty_string_fallback] baseline updated at {baseline_file or _baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n→ Rewrite the empty-string-fallback to fail fast (raise, or return None and let the caller "
            'decide) — never silently swap a missing field for "". For a genuinely deliberate, safe case '
            "(field may legitimately be absent; empty string is a meaningful not-present value the rest of "
            "the code correctly treats as falsy/absent) add `# noqa: qg-empty-fallback` with a one-line "
            "reason. SSOT: "
            "plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md. "
            "Baseline: unified-trading-pm/scripts/quality_gates/no_empty_string_fallback_baseline.yaml "
            "(NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
