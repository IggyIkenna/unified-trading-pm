#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG check — `Lifecycle: oneoff` scripts whose SHAPE matches a Phase 0b canonical
template (purge/canonicalize/reconcile/backfill/audit) should not exist as fresh
hand-rolled one-offs outside `deployment-service/scripts/migrations/`.

Codified 2026-08-19, per operator ruling on
`migration_script_canonicalization_into_deployment_service_2026_08_18.md`
(archived; see `/codex/05-infrastructure/migration-script-ssot.md`): the
evidence from that plan's own ~619-file census is that `Lifecycle: oneoff`
was historically the DEFAULT reflex for a fresh migration/backfill/purge/
reconcile/audit script, even though 85% of that population turned out to
share just 5 recurring operation shapes. The 26 files that plan's own
follow-up sweep confirmed as GENUINELY dead (Delete-when satisfied, safe to
delete) share a distinguishing property the 500+ surviving ones don't: each
was scoped to a single, permanently-resolved incident (a specific date-
stamped bug, a specific now-decommissioned bucket, a specific historical
vendor quirk) rather than a general operation category — the SHAPE it used
(purge/canonicalize/etc.) is what made it reusable, not the specific
instance. Once a canonical template exists for a shape, a NEW script
matching that shape should adapt the template, not spawn another bespoke
"temporary" one-off — the fleet's history shows those "temporary" scripts
recur under a new date stamp far more often than they actually vanish.

What is flagged: any file under `<repo>/scripts/` (recursively, `deployment-
service/scripts/migrations/` excluded — that IS the canonical destination)
whose basename matches the SAME operation-shape regex the founding plan's own
§Discovery process used to find the 619-file population, AND whose header
carries `# Lifecycle: oneoff` (not `campaign`/`permanent`/`reusable-*` — those
already self-declare as recurring). This is a **grep-based heuristic with a
documented false-positive boundary** (filename pattern, not true AST/semantic
shape detection) — the same acceptable-shape the launcher-governance QG
checks in `launcher-script-ssot.md` use ("grep with documented false-positive
boundary"). A name match is not proof the file IS purge/canonicalize/
reconcile/backfill/audit-shaped; it is a cheap, cheerfully-imperfect signal
that a human (or agent) should check before defaulting to `oneoff`.

Per-file opt-out: `# QG-allow: <reason>` on the `# Lifecycle:` line itself,
for a script that matches the name pattern but is genuinely NOT
recurring-shaped (e.g. a one-time codegen run, a dev-seeder rename that
happens to contain "fix_"). The marker is part of the contract, not an
escape hatch — the reason must actually explain why the shape doesn't apply.

Shape — **baseline ratchet** (warning-with-baseline, NOT zero-tolerance from
day 1 — the existing ~500-file population is grandfathered; see
`oneoff_recurring_shape_ratchet_baseline.yaml`):

  1. Load the per-repo baseline count.
  2. Walk `<repo>/scripts/` for `.py`/`.sh` files matching the shape-name
     regex, carrying `# Lifecycle: oneoff`, without a `# QG-allow:` marker on
     that same line.
  3. count <= baseline -> OK (WARN when strictly below — ratchet the baseline
     DOWN as legacy files get individually resolved: relocated + wired to a
     template, or deleted once genuinely dead). count > baseline -> ERROR
     (exit 1): a NEW oneoff-marked, shape-matching script landed — adapt the
     matching `deployment-service/scripts/migrations/lib/templates/
     template_{purge,canonicalize,reconcile,backfill,audit}.py` instead, or
     add `# QG-allow: <reason>` if it genuinely isn't shape-matching despite
     the name.

The baseline ONLY shrinks: re-run with `--update-baseline` after resolving
legacy files (counts are clamped DOWN — never raised).

Usage::

    # per-repo (wire into a repo's own quality-gates.sh):
    python check_oneoff_recurring_shape_ratchet.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_oneoff_recurring_shape_ratchet.py --workspace-root <ws>

    # ratchet the baseline DOWN after resolving legacy files:
    python check_oneoff_recurring_shape_ratchet.py --workspace-root <ws> --update-baseline

Exit codes: 0 = clean / at-or-below baseline; 1 = over baseline; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: Same operation-shape name regex the founding plan's own §Discovery process
#: used to identify the ~619-file migration-shaped population fleet-wide.
SHAPE_NAME_RE: Final[re.Pattern[str]] = re.compile(
    r"migrat|backfill|repair|fix_|cleanup|clean_up|one_off|oneoff"
    r"|_20\d{2}_\d{2}_\d{2}|reconcile|purge|wipe_|dedupe|dedup_",
    re.IGNORECASE,
)

LIFECYCLE_LINE_RE: Final[re.Pattern[str]] = re.compile(r"^#\s*Lifecycle:\s*oneoff\b(.*)$")
QG_ALLOW_RE: Final[re.Pattern[str]] = re.compile(r"#\s*QG-allow:\s*\S")

#: Directory the canonical templates already live under — never flagged, this
#: IS the sanctioned destination the whole check exists to steer scripts toward.
CANONICAL_DEST_FRAGMENT: Final[str] = "scripts/migrations"

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
        ".claude",
        ".cursor",
    }
)
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = ("/archive/", "/.archive/", "/_archived/", ".egg-info")


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "oneoff_recurring_shape_ratchet_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
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
        counts[str(repo)] = int(val.get("count", 0)) if isinstance(val, dict) else int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline, path: Path | None = None) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    for repo in sorted(set(counts) | set(existing.counts)):
        if repo not in counts:
            merged[repo] = {"count": existing.allowed(repo)}
            continue
        observed = int(counts[repo])
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for the oneoff-recurring-shape ratchet.\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of\n"
        "# `scripts/` files carrying `# Lifecycle: oneoff` whose basename matches a\n"
        "# Phase 0b canonical-template operation shape (purge/canonicalize/\n"
        "# reconcile/backfill/audit — the founding plan's own §Discovery regex),\n"
        "# without a `# QG-allow:` marker on that line. A repo whose live count\n"
        "# EXCEEDS its baseline fails: a NEW oneoff-marked, shape-matching script\n"
        "# landed — adapt the matching `deployment-service/scripts/migrations/lib/\n"
        "# templates/template_*.py` instead, or add `# QG-allow: <reason>` if it\n"
        "# genuinely isn't shape-matching despite the name.\n"
        "#\n"
        "# LOWER a count (re-run --update-baseline) as legacy files get resolved\n"
        "# (relocated + wired to a template, or deleted once genuinely dead).\n"
        "# NEVER raise a count. Repos not listed default to count=0.\n"
        "#\n"
        "# SSOT: /codex/05-infrastructure/migration-script-ssot.md.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-08-19 at plan archival — day-1 baseline is the legacy population.",
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
    return CANONICAL_DEST_FRAGMENT in posix


def _iter_script_files(scripts_root: Path) -> Iterator[Path]:
    if not scripts_root.is_dir():
        return
    for path in scripts_root.rglob("*"):
        if path.suffix not in (".py", ".sh"):
            continue
        if _is_excluded_path(path):
            continue
        yield path


def _is_flagged(path: Path) -> bool:
    if not SHAPE_NAME_RE.search(path.name):
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    for line in text.splitlines()[:20]:  # marker is always near the top (post-shebang)
        m = LIFECYCLE_LINE_RE.match(line.strip())
        if m and not QG_ALLOW_RE.search(m.group(1)):
            return True
    return False


def scan_repo(repo_root: Path) -> list[Path]:
    return [p for p in _iter_script_files(repo_root / "scripts") if _is_flagged(p)]


# ── CLI ──────────────────────────────────────────────────────────────────────


def _discover_scope_dirs(workspace_root: Path, scope: str | None) -> list[Path]:
    if scope:
        return [workspace_root / scope]
    return [
        d
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "scripts").is_dir()
        and not d.name.startswith(".")
        and ".stale-" not in d.name  # backup dirs from a history-rewrite op, not live repos
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to check (default: whole workspace).")
    parser.add_argument("--update-baseline", action="store_true", help="Rewrite the baseline from observed counts.")
    args = parser.parse_args(argv)

    workspace_root: Path = args.workspace_root.resolve()
    if not workspace_root.is_dir():
        print(f"ERROR: --workspace-root {workspace_root} is not a directory", file=sys.stderr)
        return 2

    existing = load_baseline()
    scope_dirs = _discover_scope_dirs(workspace_root, args.scope)

    observed: dict[str, int] = {}
    failures: list[str] = []
    for repo_dir in scope_dirs:
        repo = repo_dir.name
        flagged = scan_repo(repo_dir)
        observed[repo] = len(flagged)
        allowed = existing.allowed(repo)
        if len(flagged) > allowed:
            failures.append(f"{repo}: {len(flagged)} flagged file(s) > baseline {allowed}")

    if args.update_baseline:
        write_baseline(observed, existing)
        print(f"Baseline updated: {_baseline_path()}")
        return 0

    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        print(
            "\n-> A NEW `Lifecycle: oneoff` script matches a Phase 0b canonical-template shape "
            "(purge/canonicalize/reconcile/backfill/audit). Adapt the matching template under "
            "deployment-service/scripts/migrations/lib/templates/ instead of hand-rolling — or add "
            "`# QG-allow: <reason>` on the `# Lifecycle:` line if it genuinely doesn't fit. "
            "Baseline: scripts/quality_gates/oneoff_recurring_shape_ratchet_baseline.yaml (NEVER raise a count). "
            "SSOT: /codex/05-infrastructure/migration-script-ssot.md."
        )
        return 1

    for repo, count in sorted(observed.items()):
        allowed = existing.allowed(repo)
        status = "OK" if count == allowed else "WARN"
        marker = "" if count == allowed else f" ({count} < baseline {allowed} — ratchet DOWN via --update-baseline)"
        print(f"[{status}] {repo}: {count}{marker}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
