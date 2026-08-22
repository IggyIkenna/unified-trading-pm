#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Standalone checker — bans the swallowed-credential-fetch idiom in ``scripts/``.

``2>/dev/null || true`` wrapped around a credential-fetch command discards BOTH
the exit code and the stderr reason. That exact idiom in
``scripts/self-hosted-runners/glue-runner-run.sh`` hid a `PERMISSION_DENIED`
Secret Manager read for 16 hours while 4,159 crash-loops produced ZERO alerts
(``plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md``).
A credential fetch must fail LOUD, never degrade to an empty string.

What is flagged (regex over backslash-continuation-joined logical lines — a
shell statement wrapped across multiple physical lines via a trailing ``\\``
is joined into one logical line before matching, since that is exactly how the
`glue-runner-run.sh` idiom was written):

A logical line containing ALL THREE of:

1. a credential-fetch command — ``gcloud secrets versions access``,
   ``aws secretsmanager get-secret-value``, ``vault kv get``, or ``vault read``
   (deliberately narrower than "any secrets subcommand" — ``secrets list`` /
   ``secrets add-iam-policy-binding`` / ``secrets versions add`` are not a
   credential VALUE fetch and are out of scope for this checker);
2. ``2>/dev/null`` (the stderr swallow — the piece that discards the "reason");
3. ``|| true`` or ``|| :`` (the exit-code swallow).

Per-line opt-out: ``# noqa: swallowed-credential-fetch`` on any physical line
spanned by the logical line, with a one-line reason.

Scope: this checker greps ``<repo>/scripts/**/*.sh`` ONLY — not the whole repo,
and not Python/other languages. Repos with no ``scripts/`` dir score 0, not an
error.

Shape — **baseline ratchet** (NOT zero-tolerance from day 1; seeded 2026-07-26
with the fleet's real pre-existing count):

  1. Load ``no_swallowed_credential_fetch_baseline.yaml`` — a per-repo count of
     the currently-known swallow sites (those WITHOUT the noqa marker).
  2. Scan every ``.sh`` file under ``<repo>/scripts/``.
  3. count <= baseline -> OK (WARN when strictly below, so the operator
     ratchets the baseline DOWN). count > baseline -> ERROR (exit 1): a NEW
     swallow site landed.

The baseline ONLY shrinks: re-run with ``--update-baseline`` after fixing sites
(counts are clamped DOWN — never raised).

**NOT wired into ``scripts/quality-gates.sh``** (deliberate — see the gated
finalize plan `ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`). Run
standalone until that wiring is decided.

Usage::

    # per-repo:
    python check_no_swallowed_credential_fetch.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_no_swallowed_credential_fetch.py --workspace-root <ws>

    # ratchet the baseline DOWN after fixing sites:
    python check_no_swallowed_credential_fetch.py --workspace-root <ws> --update-baseline

Exit codes: 0 = clean / at-or-below baseline; 1 = over baseline; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: The "grandfathered, intentional" per-line exemption marker (on any physical
#: line spanned by the logical/continuation-joined line).
NOQA_MARKER: Final[str] = "noqa: swallowed-credential-fetch"

#: A credential-VALUE fetch — deliberately narrower than "any secrets
#: subcommand" (list / add-iam-policy-binding / versions add are not a fetch).
CRED_FETCH_RE: Final[re.Pattern[str]] = re.compile(
    r"\bgcloud\s+secrets\s+versions\s+access\b"
    r"|\baws\s+secretsmanager\s+get-secret-value\b"
    r"|\bvault\s+(?:kv\s+get|read)\b"
)

#: The stderr swallow — discards the "reason" (the piece that hid PERMISSION_DENIED).
SWALLOW_RE: Final[re.Pattern[str]] = re.compile(r"2>\s*/dev/null")

#: The exit-code swallow. No trailing `\b` on the `:` branch — `:` is not a
#: word character, so `\b` never matches between it and a following `)`/EOL.
TRUE_RE: Final[re.Pattern[str]] = re.compile(r"\|\|\s*(?:true\b|:)")

#: Top-level dir names to skip when discovering repos.
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
        # Agent-local scratch (Claude Code worktrees + settings) and the Cursor
        # equivalent — ephemeral copies of the repo nested under the scope.
        ".claude",
        ".cursor",
    }
)


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "no_swallowed_credential_fetch_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts of swallowed-credential-fetch sites."""

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
    existing baseline (a higher count means a new swallow site landed; fix it,
    don't bake it in)."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        if repo not in counts:
            # Not scanned this run (scoped --update-baseline) — carry the existing
            # row forward verbatim rather than zeroing it (same defect class as
            # check_ruff_rule_ratchet, incident 2026-06-10).
            merged[repo] = {"count": existing.allowed(repo)}
            continue
        observed = int(counts[repo])
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for check_no_swallowed_credential_fetch.py.\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of\n"
        "# `2>/dev/null || true`-wrapped credential-fetch sites (WITHOUT a\n"
        "# `# noqa: swallowed-credential-fetch` marker) the checker tolerates in\n"
        "# that repo's `scripts/` dir. A repo whose live count EXCEEDS its baseline\n"
        "# fails — a NEW swallow site landed; fail loud instead, or add\n"
        "# `# noqa: swallowed-credential-fetch` with a one-line reason.\n"
        "#\n"
        "# LOWER a count (re-run `--update-baseline`) the moment sites are fixed.\n"
        "# NEVER raise a count. Repos not listed default to count=0.\n"
        "#\n"
        "# SSOT: plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md\n"
        "# + plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-07-26 — ci_satellite_ao_dispatch_batch1 [INFRA] P1.",
            "repos": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = baseline_file.write_text(header + body, encoding="utf-8")


# ── Scanning ─────────────────────────────────────────────────────────────────


def _iter_sh_files(scripts_root: Path) -> Iterator[Path]:
    if not scripts_root.is_dir():
        return
    for path in scripts_root.rglob("*.sh"):
        if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
            continue
        yield path


def _join_continuations(source: str) -> list[tuple[int, str]]:
    """Join backslash-continued physical lines into logical lines.

    Returns [(starting_lineno, logical_line)] — a shell statement wrapped
    across multiple physical lines via a trailing ``\\`` is joined into one
    logical line, since that is exactly the shape of the real
    ``glue-runner-run.sh`` idiom (credential command on one physical line,
    ``2>/dev/null || true`` on the next).
    """
    lines = source.splitlines()
    logical: list[tuple[int, str]] = []
    buf = ""
    start_lineno = 1
    for lineno, raw_line in enumerate(lines, start=1):
        if not buf:
            start_lineno = lineno
        if raw_line.endswith("\\"):
            buf += raw_line[:-1] + " "
        else:
            buf += raw_line
            logical.append((start_lineno, buf))
            buf = ""
    if buf:
        logical.append((start_lineno, buf))
    return logical


def _noqa_in_span(file_lines: list[str], start_lineno: int, end_lineno: int) -> bool:
    """True if the noqa marker sits on any physical line of the statement
    (incl. a continuation line or a trailing same-line comment), OR on the
    line immediately above the statement (the standalone-comment-above
    convention)."""
    for lineno in range(start_lineno - 1, end_lineno + 1):
        if lineno < 1 or lineno > len(file_lines):
            continue
        if NOQA_MARKER in file_lines[lineno - 1].lower():
            return True
    return False


def find_swallowed_credential_fetches(source_path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, snippet)] of swallowed-credential-fetch sites in a file."""
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    file_lines = source.splitlines()
    violations: list[tuple[int, str]] = []
    logical_lines = _join_continuations(source)

    for idx, (start_lineno, logical) in enumerate(logical_lines):
        if not (CRED_FETCH_RE.search(logical) and SWALLOW_RE.search(logical) and TRUE_RE.search(logical)):
            continue
        # The logical line's physical span is [start_lineno, next logical line's
        # start - 1] (or EOF for the last one) — used only for the noqa scan.
        end_lineno = logical_lines[idx + 1][0] - 1 if idx + 1 < len(logical_lines) else len(file_lines)
        if _noqa_in_span(file_lines, start_lineno, end_lineno):
            continue
        violations.append((start_lineno, logical.strip()[:160]))

    return sorted(violations)


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[tuple[str, int, str]]  # (repo-relative-file, line, snippet)


def scan_repo(repo_root: Path, repo_name: str) -> RepoScan:
    scripts_root = repo_root / "scripts"
    sites: list[tuple[str, int, str]] = []
    for sh in _iter_sh_files(scripts_root):
        for lineno, snippet in find_swallowed_credential_fetches(sh):
            rel = sh.relative_to(repo_root).as_posix() if sh.is_relative_to(repo_root) else sh.as_posix()
            sites.append((rel, lineno, snippet))
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None) -> list[tuple[str, Path]]:
    """Return [(repo_name, repo_root)]. --scope -> that repo only. Else every
    immediate git-repo sub-dir of the workspace root."""
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(
                f"[check_no_swallowed_credential_fetch] --scope {scope!r} not a dir under {workspace_root}",
                file=sys.stderr,
            )
            return []
        return [(scope, repo_root)]
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
        description="Swallowed-credential-fetch idiom ratchet (standalone, NOT wired into quality-gates.sh)."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name (per-repo mode).")
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
    scopes = _resolve_scopes(workspace_root, args.scope)
    if not scopes:
        print("[check_no_swallowed_credential_fetch] no repos in scope.", file=sys.stderr)
        return 0  # nothing to check — not a failure

    observed: dict[str, int] = {}
    failures: list[str] = []
    info_lines: list[str] = []
    for repo_name, repo_root in scopes:
        scan = scan_repo(repo_root, repo_name)
        observed[repo_name] = scan.count
        allowed = baseline.allowed(repo_name)
        if scan.count > allowed:
            over = scan.sites[allowed:] if allowed < len(scan.sites) else scan.sites
            sites_str = "; ".join(f"{f}:{ln}" for f, ln, _snippet in over[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} swallowed-credential-fetch site(s) > baseline {allowed}. "
                f"New/over-baseline site(s): {sites_str}" + (" ..." if len(over) > 20 else "")
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
        print(f"[check_no_swallowed_credential_fetch] baseline updated at {baseline_file or _baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n-> A credential fetch must fail LOUD, never degrade to an empty string via "
            "`2>/dev/null || true`. Surface the real error (log it, exit non-zero) instead. For a "
            "documented exception add `# noqa: swallowed-credential-fetch` with a one-line reason. "
            "SSOT: plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md. "
            "Baseline: unified-trading-pm/scripts/quality_gates/no_swallowed_credential_fetch_baseline.yaml "
            "(NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
