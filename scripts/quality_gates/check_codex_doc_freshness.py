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

AGENCY SPLIT (2026-08-12) — this gate blocks only on what the author controls.
The four violation reasons are not the same kind of thing:

  no-frontmatter / yaml-parse-error / no-last_reviewed-field / invalid-last_reviewed-format
      AUTHORING defects. Deterministic, caused by the change in hand, fixable in
      seconds by the person who tripped them. These BLOCK. ``yaml-parse-error`` is
      distinguished from ``no-frontmatter`` (2026-08-13,
      codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md
      Update 2026-08-12): the former means the ``---`` block IS present but malformed
      (e.g. a plain multi-line scalar with an internal ``": "`` breaking ``yaml.safe_load``),
      the latter means there is no frontmatter at all. They need different fixes, so they
      must not share a reason string.
  stale
      The CLOCK moved. Nothing was edited; the doc simply aged past the window.
      This is ADVISORY — printed as an owner-grouped digest, never blocking.

Why: `stale` fired on the calendar and in COHORTS (docs authored in one batch
share a `last_reviewed`, so they tip together — the 2026-05-12 cohort blocked
ships on 08-11, the 05-13 cohort on 08-12), so unrelated changes were blocked by
a clock nobody touched. Worse, the documented remedy was `--baseline-write`,
which made "absorb somebody else's review debt into the baseline" the rational
move under time pressure, and had two agents racing to regenerate the same
baseline. A review-cadence reminder is not a correctness assertion: nobody
claims a 91-day-old doc is WRONG, only unread. See
`/plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md`.

This composes with the retired-doc exemption above rather than duplicating it:
that exemption removes docs which SHOULD NOT be re-read at all, while this makes
the remaining genuine review debt visible without blocking. Neither alone was
enough — the exemption still left live docs tipping on the calendar.

DE-COHORTING (2026-08-14) — even a non-blocking digest still arrives as a flood
when a whole batch of docs shares one `last_reviewed` stamp: they all cross the
90-day line on the same calendar day. Each doc's effective window is therefore
`staleness_days + jitter(doc)`, where `jitter` is a stable 0..13-day offset
derived from the doc's WORKSPACE-RELATIVE path (never the built-in `hash()`,
which is salted per-process by `PYTHONHASHSEED` and would move a doc's cutover
day on every run/slot). Keying off the relative path (not the absolute one)
matters: every `.tabs/<N>/` slot worktree has a different absolute prefix, and
the same doc must land on the same cutover day regardless of which slot's gate
computes it. This spreads a same-day cohort's digest entries across ~2 weeks
instead of one flood, per
`/plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md`'s
"De-cohort the thresholds" todo. It only changes WHEN `stale` fires (already
advisory); it does not touch the three blocking authoring reasons.

`--strict` still fails on ANY violation including staleness — that is the mode a
scheduled digest/audit job uses. Partitioning fails CLOSED: only reasons listed
in `CLOCK_DRIVEN_REASONS` are advisory, so a reason added later blocks by
default rather than silently downgrading itself to a warning.

Exit-code semantics:
  0 — no NEW blocking violation vs. the baseline's known-violation path set
      (advisory staleness may still have been printed as a digest)
  1 — a NEW authoring violation not in that set / --strict any violation
  2 — argument / IO / yaml-parse error

SSOT: CLAUDE.md § "Post-Plan-Phase Codex Audit (HARD RULE)" — codex docs
must reflect shipped contracts; `last_reviewed:` is the codified review-stamp.

Origin: plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md
        § "Group B — Codex freshness ratchet (G-12 + D-18)".
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
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

# Spread of the per-doc jitter offset added to staleness_days (see DE-COHORTING in the
# module docstring). 14 days matches the todo's own suggestion and the cohort's own
# observed size (a batch shares one last_reviewed stamp, so 14 days is plenty to break
# same-day flood into a trickle without meaningfully loosening the 90-day cadence).
JITTER_SPREAD_DAYS = 14


def _jitter_days_for_path(rel_path: str) -> int:
    """Stable 0..JITTER_SPREAD_DAYS-1 offset for a doc, keyed on its WORKSPACE-RELATIVE path.

    Never uses the builtin ``hash()`` — it is salted per-process by ``PYTHONHASHSEED``, so the
    same doc would land on a different cutover day on every invocation/slot. sha256 over a
    path relative to the repo root is deterministic across processes, machines, and the
    per-slot ``.tabs/<N>/`` absolute-prefix worktrees (codex_doc_freshness_baseline.yaml's own
    relative-path convention, reused here for the same portability reason).
    """
    digest = hashlib.sha256(rel_path.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % JITTER_SPREAD_DAYS


# A doc carrying one of these statuses is formally retired: it is no longer the SSOT for
# anything, and it is not supposed to still match the running system.
RETIRED_STATUSES = frozenset({"superseded", "deprecated", "archived"})

# Reasons produced by the passage of TIME rather than by the change in hand.
# Advisory only (digest, non-blocking). Everything not listed here blocks —
# see the module docstring's AGENCY SPLIT section. Keep this set MINIMAL:
# adding a reason here converts a hard gate into a warning, which is a
# governance decision, not a refactor.
CLOCK_DRIVEN_REASONS = frozenset({"stale"})


class FreshnessViolation:
    """A codex doc failing the freshness SSOT."""

    def __init__(self, path: Path, reason: str, detail: str = "", owner: str = "") -> None:
        self.path = path
        self.reason = reason
        self.detail = detail
        self.owner = owner

    def __str__(self) -> str:
        if self.detail:
            return f"{self.path}: {self.reason} ({self.detail})"
        return f"{self.path}: {self.reason}"


class FrontmatterParseError(RuntimeError):
    """A ``---`` frontmatter block is PRESENT but could not be parsed into a mapping.

    Distinct from genuinely absent frontmatter (no ``---`` opener at all). Raised by
    :func:`_parse_frontmatter` for: a missing closing ``---`` delimiter, a ``yaml.safe_load``
    failure (e.g. a plain multi-line scalar containing an unescaped ``": "`` — the
    ``ScannerError`` the 2026-08-12 incident hit), or a parsed non-mapping. Carries the
    underlying parser's message so callers can report a precise ``yaml-parse-error`` violation
    instead of the misleading ``no-frontmatter`` — see
    ``/plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md``
    Update 2026-08-12.
    """


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
    """Parse a doc's YAML frontmatter block into a dict, or None when genuinely absent.

    ``None`` means the file has NO ``---\n`` opener at all — nothing to parse. Every other
    failure mode (opener present but no closing delimiter, ``yaml.safe_load`` raising, or a
    parsed non-mapping) raises :class:`FrontmatterParseError` with the underlying cause, so the
    caller can distinguish "you forgot the frontmatter block" from "your frontmatter is malformed"
    — see that class's docstring.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        raise FrontmatterParseError("frontmatter block present but missing closing '---' delimiter")
    raw = text[4:end]
    try:
        loaded = cast(object, yaml.safe_load(raw))
    except yaml.YAMLError as exc:
        raise FrontmatterParseError(f"yaml parse failed: {exc}") from exc
    if not isinstance(loaded, dict):
        raise FrontmatterParseError(f"frontmatter parsed to {type(loaded).__name__}, expected a mapping")
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


def _is_retired_with_successor(fm: dict[str, object]) -> bool:
    """True when a doc is formally retired AND names what replaced it.

    Such a doc is exempt from the staleness window (operator ruling 2026-08-12,
    /plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md).

    The reason is that "re-review" has no honest meaning here. `last_reviewed` asserts "someone
    checked this still matches the system"; a superseded doc is *supposed* to no longer match,
    so the only available actions on expiry were to stamp it unread or to re-read a doc nobody
    should be reading. Holding retired docs to the live cadence therefore manufactured exactly
    the dishonest-stamp pressure the gate exists to prevent (3 of the 6 docs flagged on
    2026-08-12 were retired).

    **The `superseded_by` requirement is load-bearing, not decoration.** Exempting on `status`
    alone would make this a mute button: any stale doc could be silenced by editing one field.
    Requiring the successor means the only way to buy the exemption is to record where the
    truth moved to — which is the thing that actually protects a reader who greps into a dead
    doc. A retired doc with no successor stays subject to the window, deliberately: nothing
    records what replaced it, so it is the more dangerous shape, not the less.
    """
    status = fm.get("status")
    if not isinstance(status, str) or status.strip().lower() not in RETIRED_STATUSES:
        return False
    successor = fm.get("superseded_by")
    if isinstance(successor, str):
        return bool(successor.strip())
    if isinstance(successor, list):
        return any(isinstance(s, str) and s.strip() for s in cast(list[object], successor))
    return False


def _check_parsed(
    path: Path,
    fm: dict[str, object] | None,
    staleness_days: int,
    today: datetime.date,
    workspace_root: Path | None = None,
) -> FreshnessViolation | None:
    """Freshness verdict for an ALREADY-parsed frontmatter dict.

    Split out from `_check_doc` so `main()` can parse each doc's frontmatter exactly once and
    still classify retired-exempt docs separately, rather than re-reading all 316 files.

    ``workspace_root``, when given, anchors the de-cohorting jitter to a WORKSPACE-RELATIVE
    path (see ``_jitter_days_for_path``) so the same doc jitters identically across every
    slot's `.tabs/<N>/` worktree. ``None`` falls back to ``str(path)`` — still deterministic
    within a single process/run (adequate for direct unit tests that pass bare tmp_path files
    with no shared repo root to anchor against).
    """
    if fm is None:
        return FreshnessViolation(path, "no-frontmatter")
    if _is_retired_with_successor(fm):
        return None
    last_reviewed_raw = fm.get("last_reviewed")
    if last_reviewed_raw is None:
        return FreshnessViolation(path, "no-last_reviewed-field")
    last_reviewed = _parse_last_reviewed(last_reviewed_raw)
    if last_reviewed is None:
        return FreshnessViolation(path, "invalid-last_reviewed-format", str(last_reviewed_raw)[:40])
    rel_anchor = _relative_path(path, workspace_root) if workspace_root is not None else str(path)
    jitter = _jitter_days_for_path(rel_anchor)
    effective_staleness_days = staleness_days + jitter
    age = (today - last_reviewed).days
    if age > effective_staleness_days:
        return FreshnessViolation(
            path,
            "stale",
            f"{age}d old (limit {effective_staleness_days}d = {staleness_days}d + {jitter}d jitter; "
            f"last_reviewed={last_reviewed})",
            owner=str(fm.get("owner") or ""),
        )
    return None


def _check_doc(
    path: Path, staleness_days: int, today: datetime.date, workspace_root: Path | None = None
) -> FreshnessViolation | None:
    """Parse-and-check a single doc. Convenience wrapper over `_check_parsed`.

    Catches :class:`FrontmatterParseError` so a present-but-malformed frontmatter block is
    reported as ``yaml-parse-error`` (with the parser's message as detail) rather than the
    misleading ``no-frontmatter``.
    """
    try:
        fm = _parse_frontmatter(path)
    except FrontmatterParseError as exc:
        return FreshnessViolation(path, "yaml-parse-error", str(exc))
    return _check_parsed(path, fm, staleness_days, today, workspace_root=workspace_root)


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


def partition_by_agency(
    violations: list[FreshnessViolation],
) -> tuple[list[FreshnessViolation], list[FreshnessViolation]]:
    """Split violations into (blocking, advisory) by who/what caused them.

    Advisory == reasons in ``CLOCK_DRIVEN_REASONS`` (the calendar moved).
    Blocking == everything else, INCLUDING any reason introduced later that
    nobody classified — failing closed, so a new check cannot accidentally
    ship as a warning. Pure decision function, matching ``_new_violations``.
    """
    advisory = [v for v in violations if v.reason in CLOCK_DRIVEN_REASONS]
    blocking = [v for v in violations if v.reason not in CLOCK_DRIVEN_REASONS]
    return blocking, advisory


def _print_stale_digest(violations: list[FreshnessViolation], root: Path) -> None:
    """Print the aging docs grouped by their frontmatter ``owner:``.

    Grouped by owner because the point of the digest is routing it to whoever
    can actually re-read the doc; an ungrouped list of 180 paths is noise.
    """
    by_owner: dict[str, list[FreshnessViolation]] = {}
    for v in violations:
        by_owner.setdefault(v.owner or "(unowned)", []).append(v)
    print(f"\n⚠️  Codex review digest — {len(violations)} doc(s) past the freshness window (NOT blocking this ship):")
    for owner in sorted(by_owner):
        entries = by_owner[owner]
        print(f"  {owner} — {len(entries)} doc(s)")
        for v in sorted(entries, key=lambda e: _relative_path(e.path, root)):
            print(f"    - {_relative_path(v.path, root)}: {v.detail}")


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
    exempt_retired: list[Path] = []
    for doc in docs:
        try:
            fm = _parse_frontmatter(doc)
        except FrontmatterParseError as exc:
            # A malformed frontmatter block is an authoring defect (blocking), and carries a
            # precise diagnostic instead of the misleading no-frontmatter -- see
            # _parse_frontmatter / FrontmatterParseError.
            violations.append(FreshnessViolation(doc, "yaml-parse-error", str(exc)))
            continue
        if fm is not None and _is_retired_with_successor(fm):
            exempt_retired.append(doc)
            continue
        v = _check_parsed(doc, fm, staleness_days, today, workspace_root=pm_root)
        if v is not None:
            violations.append(v)

    print(
        f"Scanned {len(docs)} codex doc(s) across {len(CUTOVER_CRITICAL_DIRS)} cutover-critical "
        f"surface(s); {len(violations)} violation(s) (staleness limit: {staleness_days}d)."
    )
    # Report the exempt set rather than dropping it silently: an exemption nobody can see is
    # indistinguishable from a doc the walker missed, and this surface is meant to stay visible.
    if exempt_retired:
        print(f"  exempt-retired: {len(exempt_retired)} doc(s) with a retired status + a named successor")
        for doc in sorted(exempt_retired):
            print(f"    - {_relative_path(doc, pm_root)}")

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
    blocking_new, advisory_new = partition_by_agency(new_violations)

    if advisory_new:
        _print_stale_digest(advisory_new, pm_root)
        print(
            "   ^ review-cadence reminder, NOT a correctness failure — these aged past the window on the\n"
            "     calendar, not because of your change, so they do not block this ship. Re-stamp\n"
            "     last_reviewed: when you next genuinely re-read the doc. Do NOT run --baseline-write to\n"
            "     silence this; that absorbs somebody else's review debt and is what made the ratchet\n"
            "     stop meaning anything."
        )

    if blocking_new:
        print(
            f"\n❌ Regression: {len(blocking_new)} NEW violation(s) not in the baseline snapshot "
            f"({len(violations)} total, {baseline.count} known-at-baseline):"
        )
        for v in blocking_new[:20]:
            rel = _relative_path(v.path, pm_root)
            print(f"  - NEW: {rel}: {v.reason}{(' (' + v.detail + ')') if v.detail else ''}")
        print(
            "These are AUTHORING defects (missing/invalid last_reviewed: or frontmatter), not staleness — "
            "fix them by adding the field to the doc you touched. A doc already known-violating at baseline "
            "drifting further stale is NOT a new regression (per-file diffing — see module docstring)."
        )
        return 1
    # Word this in terms of BLOCKING violations. Saying "0 new violations" while the
    # digest immediately above lists dozens of newly-aged docs is exactly the kind of
    # summary that trains readers to stop believing gate output.
    advisory_note = f"; {len(advisory_new)} new advisory (stale, non-blocking)" if advisory_new else ""
    if len(violations) < baseline.count:
        print(
            f"\n⚠️  Improvement: {len(violations)} < baseline {baseline.count}. "
            f"Run --baseline-write to ratchet down (codifies the win){advisory_note}."
        )
        return 0
    print(
        f"\n✅ At-or-below baseline (0 new BLOCKING violations; "
        f"{len(violations)} total known, {baseline.count} at baseline{advisory_note})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
