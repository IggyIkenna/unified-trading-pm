#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Codex doc freshness QG check (gap-G-12 / D-18 codification).

Walks cutover-critical codex surfaces and asserts every `*.md` file declares
`last_reviewed: YYYY-MM-DD` in YAML frontmatter, and that the date is no older
than the configured staleness window (default 90 days).

Cutover-critical surfaces (per governance_qg_automation_gaps_post_cutover_2026_05_12.md
§ Group B):
  - codex/02-data/        — data contracts, manifests, honest-absence
  - codex/04-architecture/ — service architecture + DeFi execution
  - codex/05-infrastructure/ — VM launchers, runbooks, deployment
  - codex/11-project-management/ — orchestration + planning SSOTs

Baseline mode (`--baseline-write`) writes the current violation set (as paths
relative to `--workspace-root`, so the file is portable across per-slot
worktrees) to `scripts/quality_gates/codex_doc_freshness_baseline.yaml`.
Ratchet mode (default) does PER-FILE diffing against that set — it fails ONLY
when a doc violates that was NOT already a known violation at baseline time
(codex_doc_freshness_regression_ambient_staleness_drift_2026_08_09.md): a
count-only ratchet regresses purely from ambient time decay (any doc's
`last_reviewed` crossing the staleness window between two runs, with no single
commit to bisect), so this compares the violating PATH SET, not just its size.
A doc that drops out of the current violation set (got fixed) is not required
to stay fixed forever by this check alone — `--baseline-write` re-snapshots to
shrink the known set once a fix lands, same shrinking-ratchet convention as
this repo's other baselined gates (DTZ/TID251/fallback-import).

A `last_reviewed:` date in the FUTURE is not a data error — it is an intentional staggering
technique (docs-reconcile finding, 2026-08-02): a real content re-review was done, then the
resulting stamp was deliberately set to a disjoint future date so a large cohort of docs that
previously shared one synchronized stamp doesn't all tip stale on the same day again (see e.g.
commit 44aecd1dc, "staggered re-review of 38 codex docs (freshness shard offset-0)"). This
script does not (and should not) validate `last_reviewed <= today` — DO NOT "fix" a future-dated
doc by resetting it to today's date; that collapses the stagger back into the exact cliff this
convention exists to avoid. This is documented ONLY here and in scattered commit messages, not in
a codex doc, as of 2026-08-02 — grep `git log --grep="staggered re-review"` for the full history
if the pattern needs extending to a new cohort.

Exit-code semantics:
  0 — no NEW violation vs. the baseline's known-violation path set (clean)
  1 — a violating doc's path is not in that set (regression) / --strict any violation
  2 — argument / IO / yaml-parse error

SSOT: CLAUDE.md § "Post-Plan-Phase Codex Audit (HARD RULE)" — codex docs
must reflect shipped contracts; `last_reviewed:` is the codified review-stamp.

Origin: plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md
        § "Group B — Codex freshness ratchet (G-12 + D-18)".
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import cast

import yaml


def _pm_root_or_legacy(workspace_root):
    """PM checkout root resolved by CONTENT, not by directory NAME (F7, 2026-08-10).

    See scripts/quality_gates/_pm_root.py for why. Behaviour-preserving in a canonically
    named checkout; fixes resolution when running from a git worktree."""
    import pathlib as _pathlib
    import sys as _sys

    _d = str(_pathlib.Path(__file__).resolve().parent)
    if _d not in _sys.path:
        _sys.path.insert(0, _d)
    from _pm_root import pm_root_or_legacy as _impl

    return _impl(workspace_root)


CUTOVER_CRITICAL_DIRS = (
    "codex/02-data",
    "codex/04-architecture",
    "codex/05-infrastructure",
    "codex/11-project-management",
)
DEFAULT_STALENESS_DAYS = 90
DEFAULT_BASELINE_PATH = Path(__file__).parent / "codex_doc_freshness_baseline.yaml"


class FreshnessViolation:
    """A codex doc failing the freshness SSOT."""

    def __init__(self, path: Path, reason: str, detail: str = "") -> None:
        self.path = path
        self.reason = reason
        self.detail = detail

    def __str__(self) -> str:
        if self.detail:
            return f"{self.path}: {self.reason} ({self.detail})"
        return f"{self.path}: {self.reason}"


def _iter_codex_md(workspace_root: Path) -> list[Path]:
    """Walk cutover-critical codex surfaces for *.md files."""
    candidates: list[Path] = []
    for d in CUTOVER_CRITICAL_DIRS:
        root = (_pm_root_or_legacy(workspace_root)) / d
        if not root.is_dir():
            continue
        for p in root.rglob("*.md"):
            candidates.append(p)
    return sorted(candidates)


def _parse_frontmatter(path: Path) -> dict[str, object] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    raw = text[4:end]
    try:
        loaded = cast(object, yaml.safe_load(raw))
    except yaml.YAMLError:
        return None
    if not isinstance(loaded, dict):
        return None
    return cast(dict[str, object], loaded)


def _parse_last_reviewed(value: object) -> datetime.date | None:
    """Accept date or YYYY-MM-DD string."""
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _check_doc(path: Path, staleness_days: int, today: datetime.date) -> FreshnessViolation | None:
    fm = _parse_frontmatter(path)
    if fm is None:
        return FreshnessViolation(path, "no-frontmatter")
    last_reviewed_raw = fm.get("last_reviewed")
    if last_reviewed_raw is None:
        return FreshnessViolation(path, "no-last_reviewed-field")
    last_reviewed = _parse_last_reviewed(last_reviewed_raw)
    if last_reviewed is None:
        return FreshnessViolation(path, "invalid-last_reviewed-format", str(last_reviewed_raw)[:40])
    age = (today - last_reviewed).days
    if age > staleness_days:
        return FreshnessViolation(path, "stale", f"{age}d old (limit {staleness_days}d; last_reviewed={last_reviewed})")
    return None


class BaselineSnapshot:
    """The baseline's known-violation PATH SET (relative), plus its recorded count.

    ``known_paths`` is what ratchet mode actually diffs against
    (codex_doc_freshness_regression_ambient_staleness_drift_2026_08_09.md) — a
    doc already in this set drifting further stale (or a new-doc-without-
    last_reviewed landing that's ALSO already-known, e.g. re-run same day) is
    not a fresh regression; a doc NOT in this set that now violates is.
    """

    def __init__(self, count: int, known_paths: frozenset[str]) -> None:
        self.count = count
        self.known_paths = known_paths


def _relative_path(path: Path, workspace_root: Path) -> str:
    """Path relative to workspace_root, portable across per-slot worktrees.

    Storing absolute paths in the shared baseline file is itself a bug this
    fix closes: each slot's worktree lives at a different absolute prefix
    (``.tabs/<N>/``), so an absolute-path baseline snapshot written by one
    slot never matches when diffed by another (confirmed live, 2026-08-09 —
    a slot-10 diff embedded its own ``.tabs/4/`` absolute paths and was
    rejected as unshippable independent of any staleness content).
    """
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _load_baseline(baseline_path: Path) -> BaselineSnapshot:
    if not baseline_path.exists():
        return BaselineSnapshot(0, frozenset())
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return BaselineSnapshot(0, frozenset())
    if not isinstance(loaded, dict):
        return BaselineSnapshot(0, frozenset())
    payload = cast(dict[str, object], loaded)
    count_raw = payload.get("violation_count")
    count = count_raw if isinstance(count_raw, int) else 0
    entries_raw = payload.get("baseline_files")
    known_paths: set[str] = set()
    if isinstance(entries_raw, list):
        for entry in cast(list[object], entries_raw):
            if isinstance(entry, dict):
                path_val = cast(dict[str, object], entry).get("path")
                if isinstance(path_val, str):
                    known_paths.add(path_val)
    return BaselineSnapshot(count, frozenset(known_paths))


def _write_baseline(baseline_path: Path, violations: list[FreshnessViolation], workspace_root: Path) -> None:
    payload: dict[str, object] = {
        "violation_count": len(violations),
        "rule": "codex-doc-freshness",
        "source": (
            "CLAUDE.md § 'Post-Plan-Phase Codex Audit (HARD RULE)' + "
            "governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group B"
        ),
        "baseline_files": [{"path": _relative_path(v.path, workspace_root), "reason": v.reason} for v in violations],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _new_violations(
    violations: list[FreshnessViolation], baseline: BaselineSnapshot, workspace_root: Path
) -> list[FreshnessViolation]:
    """Violations whose path is NOT in the baseline's known-violation set.

    Pure decision function (no argparse/IO) so it's independently unit-testable —
    this is the exact per-file diff the module docstring + the
    codex_doc_freshness_regression_ambient_staleness_drift_2026_08_09.md fix
    describe: a doc already known-violating at baseline time drifting further
    stale does NOT reappear here; only a genuinely new path does.
    """
    return [v for v in violations if _relative_path(v.path, workspace_root) not in baseline.known_paths]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check codex docs declare last_reviewed: + are no older than N days.")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
        help="Workspace root to scan",
    )
    parser.add_argument(
        "--staleness-days",
        type=int,
        default=DEFAULT_STALENESS_DAYS,
        help=f"Max age in days (default: {DEFAULT_STALENESS_DAYS})",
    )
    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help=f"Baseline YAML path (default: {DEFAULT_BASELINE_PATH})",
    )
    parser.add_argument(
        "--baseline-write",
        action="store_true",
        help="Write current violation path set + count to baseline file (bootstrap mode)",
    )
    parser.add_argument("--strict", action="store_true", help="Fail on ANY violation (ignore baseline)")
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    staleness_days: int = cast(int, ns.staleness_days)
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)

    if not workspace_root.exists():
        print(f"ERROR: workspace-root does not exist: {workspace_root}", file=sys.stderr)
        return 2

    # Anchor every stored/compared path to the resolved PM checkout root, not the raw
    # --workspace-root argument. quality-gates.sh always passes the PARENT of the repo
    # (WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"), producing
    # "unified-trading-pm/codex/...", while a standalone `--workspace-root .` run (the repo
    # root itself) produces "codex/..." — two different strings for the same doc. A baseline
    # written under one convention silently mismatches every path when diffed under the
    # other, so EVERY known violation reads as "NEW" regardless of content (live 2026-08-12:
    # a --workspace-root . baseline-write failed quality-gates-v2's real --workspace-root
    # "$WORKSPACE_ROOT" invocation for this exact reason). _pm_root_or_legacy already resolves
    # the PM checkout root by content for _iter_codex_md below — reusing it here for the
    # relative-path anchor makes the baseline genuinely invocation-independent, closing the
    # gap the module docstring already claims ("portable across per-slot worktrees").
    pm_root = Path(_pm_root_or_legacy(workspace_root))

    today = datetime.date.today()
    docs = _iter_codex_md(workspace_root)
    violations: list[FreshnessViolation] = []
    for doc in docs:
        v = _check_doc(doc, staleness_days, today)
        if v is not None:
            violations.append(v)

    print(
        f"Scanned {len(docs)} codex doc(s) across {len(CUTOVER_CRITICAL_DIRS)} cutover-critical "
        f"surface(s); {len(violations)} violation(s) (staleness limit: {staleness_days}d)."
    )

    if baseline_write:
        _write_baseline(baseline_path, violations, pm_root)
        print(f"✅ Wrote baseline ({len(violations)} violations) to {baseline_path}")
        return 0

    if violations:
        print("\nViolations (first 20 shown):")
        for v in violations[:20]:
            rel = _relative_path(v.path, pm_root)
            print(f"  - {rel}: {v.reason}{(' (' + v.detail + ')') if v.detail else ''}")
        if len(violations) > 20:
            print(f"  ... + {len(violations) - 20} more")

    if strict:
        if violations:
            print(f"\n❌ STRICT mode: {len(violations)} violation(s).")
            return 1
        print("\n✅ STRICT mode: 0 violations.")
        return 0

    baseline = _load_baseline(baseline_path)
    new_violations = _new_violations(violations, baseline, pm_root)
    if new_violations:
        print(
            f"\n❌ Regression: {len(new_violations)} NEW violation(s) not in the baseline snapshot "
            f"({len(violations)} total, {baseline.count} known-at-baseline):"
        )
        for v in new_violations[:20]:
            rel = _relative_path(v.path, pm_root)
            print(f"  - NEW: {rel}: {v.reason}{(' (' + v.detail + ')') if v.detail else ''}")
        print(
            "Either fix the new violation(s) OR re-run with --baseline-write after intentional debt. "
            "A doc already known-violating at baseline drifting further stale is NOT a new regression "
            "(per-file diffing — see module docstring)."
        )
        return 1
    if len(violations) < baseline.count:
        print(
            f"\n⚠️  Improvement: {len(violations)} < baseline {baseline.count}. "
            f"Run --baseline-write to ratchet down (codifies the win)."
        )
        return 0
    print(f"\n✅ At-or-below baseline (0 new violations; {len(violations)} known, {baseline.count} at baseline).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
