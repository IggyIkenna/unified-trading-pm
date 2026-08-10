#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Group A — plan-discipline grep-checks (G-2 + G-5 + G-13).

Three sub-rules:
  - **(a) DEFERRED-without-migration-banner** (G-13): if plan body contains
    `**DEFERRED**` or `[DEFERRED]` or `DEFERRED — ` annotations, the body MUST
    contain a `## Deferred work — migrated to:` banner naming the successor plan.
  - **(b) filename-convention** (G-5): `plans/active/*.md` filenames must match
    `<slug>.md` OR `<slug>_YYYY_MM_DD.md`; `plans/active/issues/*.md` must end
    in `_YYYY_MM_DD.md`.
  - **(c) archived-plans-with-DEFERRED-but-no-successor** (G-2 archive variant):
    `plans/archive/*.md` that carry an EXPLICIT whole-doc deferral/scope marker
    (`**DEFERRED**`-shaped, or a bold/heading `post-cutover`/`out of scope` claim)
    MUST reference a successor plan (presence of `**MIGRATED TO:**` or
    `successor:` or `→ plans/active/`).

Origin: governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group A.

Exit-code semantics: 0 = at/below baseline; 1 = regression; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
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


DEFAULT_BASELINE_PATH = Path(__file__).parent / "plan_discipline_baseline.yaml"

# _DEFERRED_RE matches only precise DEFERRED-shaped tokens:
#   - `**DEFERRED**` / `[DEFERRED]` — the formal bracket/bold markers
#   - `DEFERRED-<QUALIFIER>` — the all-caps governance qualifier convention (e.g.
#     DEFERRED-OPERATOR-DECISION, DEFERRED-BY-HEADROOM) — the char right after the
#     hyphen must be uppercase, or it isn't the qualifier convention
#   - `DEFERRED — ` / `DEFERRED - ` — the bare marker, which requires whitespace
#     between the word and the dash (distinguishes it from the qualifier form,
#     which has no space)
# It deliberately does NOT match (case-sensitive `DEFERRED`, no bare `\bDEFERRED\b`
# alone): lowercase `deferred-<word>` compound modifiers/filenames ("deferred-import",
# "deferred-build-replay" — a GHA workflow name) and meta-referential negations like
# "no DEFERRED-without-successor" (uppercase DEFERRED, but the word after the hyphen
# is lowercase — not a real qualifier tag, just prose describing the absence of one).
_DEFERRED_RE = re.compile(r"\*\*DEFERRED\*\*|\[DEFERRED\]|\bDEFERRED-[A-Z][A-Z0-9-]*\b|\bDEFERRED\b\s+[—-]")
# A DEFERRED token immediately preceded by an opening quote character is a QUOTED
# REFERENCE to another document's own annotation ("...annotated in the doc itself as
# \"DEFERRED — ...\""), not a live in-doc marker for THIS document — the same
# precision philosophy as _ARCHIVE_OK_TOKENS_RE below. Confirmed 2026-07-26
# (plan_discipline_quoted_deferred_false_positive_2026_07_26.md):
# defi_satellite_ao_dispatch_batch2_2026_07_26.md quotes
# e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md's own "DEFERRED — ..."
# annotation while reporting a Phase-1 finding — the checker demanded a migration
# banner for a doc with no actual deferred work of its own.
_QUOTE_CHARS = "\"'“‘"  # noqa: RUF001 — curly quote variants are real prose punctuation, not lookalike typos
# `DEFERRED-BY-DESIGN` is a CLOSED, PERMANENT ruling ("this stays this way on purpose,
# no timeline, nothing to track") — unlike DEFERRED-OPERATOR-DECISION/DEFERRED-BY-HEADROOM
# (which imply a pending question with a real future resolution to point a banner at),
# BY-DESIGN has no successor to migrate to: requiring a "## Deferred work — migrated
# to:" banner for it is a category error, not a real gap. Confirmed 2026-07-27:
# june_2026_vintage_audit_findings_2026_07_27.md's "e2e_defi_config_taxonomy D1 —
# confirmed stays DEFERRED-BY-DESIGN, no timeline" is a live, first-party ruling (not a
# quoted reference), so the quote-exclusion above doesn't apply, but it's the same class
# of false positive as the quoted case: a marker the rule wasn't meant to catch.
_DEFERRED_BY_DESIGN_RE = re.compile(r"\bDEFERRED-BY-DESIGN\b")


def _has_live_deferred_marker(text: str) -> bool:
    """True if `_DEFERRED_RE` matches a token NOT immediately preceded by an opening quote
    and not itself the closed `DEFERRED-BY-DESIGN` qualifier (see comment above)."""
    for m in _DEFERRED_RE.finditer(text):
        if m.start() != 0 and text[m.start() - 1] in _QUOTE_CHARS:
            continue
        if _DEFERRED_BY_DESIGN_RE.fullmatch(m.group()):
            continue
        return True
    return False


_BANNER_RE = re.compile(r"##\s+Deferred work\s+—\s+migrated to", re.IGNORECASE)
_SUCCESSOR_RE = re.compile(
    r"MIGRATED TO:|successor:|→\s+plans/active/|See:\s+plans/active/|see\s+plans/active/",
    re.IGNORECASE,
)
# _ARCHIVE_OK_TOKENS_RE matches only an EXPLICIT whole-doc deferral/scope marker
# (bold-marked `**post-cutover**`/`**out of scope**`, or a `## Post-cutover`/
# `## Out of scope` heading) — not the bare phrase. A bare-substring match over
# the WHOLE archived document text produces systematic false positives: "out of
# scope" is ordinary engineering prose in any operational-log Progress Log entry
# ("out of scope for a single-line path fix", "out of scope here" re: one narrow
# item) and does not itself claim the archived plan's overall remaining work
# moved elsewhere. Confirmed 2026-07-25 (plan_discipline_archive_no_successor_
# regression_2026_07_25.md): 5/5 flagged archive docs at the 0->5 baseline
# regression were bare-prose hits, none an explicit whole-doc deferral marker —
# a 100% false-positive rate for the bare-substring form. Mirrors the same
# precision philosophy already applied to `_DEFERRED_RE` above.
_ARCHIVE_OK_TOKENS_RE = re.compile(
    r"\*\*(?:post.cutover|out of scope)\*\*|^##\s+(?:Post.[Cc]utover|Out of [Ss]cope)\b",
    re.IGNORECASE | re.MULTILINE,
)
_ACTIVE_FNAME_RE = re.compile(r"^[a-z0-9_]+(_\d{4}_\d{2}_\d{2})?\.md$")
_ISSUE_FNAME_RE = re.compile(r"^[a-z0-9_]+_\d{4}_\d{2}_\d{2}\.md$")
# Directory-structure files that are NOT plans and must not be filename-checked as one. INDEX.md is
# the canonical "# Active Plans Index" (referenced by that name across the corpus, so it cannot be
# renamed to satisfy the plan-slug pattern); README.md is a directory readme. Before this exclusion
# INDEX.md was a permanent B-active-filename false-positive that sat in the baseline and consumed a
# ratchet slot for no reason (2026-07-21).
_NON_PLAN_STRUCTURE_FILES = frozenset({"INDEX.md", "README.md"})


@dataclass(frozen=True)
class DisciplineViolation:
    rule: str
    path: Path
    detail: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.path}: {self.detail}"


def _check_rule_a(active_dir: Path) -> list[DisciplineViolation]:
    """Plans with DEFERRED annotations need a migrated-to banner."""
    out: list[DisciplineViolation] = []
    for p in active_dir.glob("*.md"):
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _has_live_deferred_marker(text) and not _BANNER_RE.search(text):
            out.append(
                DisciplineViolation(
                    rule="A-deferred-no-banner",
                    path=p,
                    detail="contains DEFERRED but no '## Deferred work — migrated to:' banner",
                )
            )
    return out


def _check_rule_b(active_dir: Path, issues_dir: Path) -> list[DisciplineViolation]:
    """Filename convention check."""
    out: list[DisciplineViolation] = []
    for p in active_dir.glob("*.md"):
        if p.name in _NON_PLAN_STRUCTURE_FILES:
            continue  # index/readme structure files are not plans
        if not _ACTIVE_FNAME_RE.match(p.name):
            out.append(
                DisciplineViolation(
                    rule="B-active-filename",
                    path=p,
                    detail=f"filename must match <slug>.md or <slug>_YYYY_MM_DD.md: {p.name}",
                )
            )
    if issues_dir.is_dir():
        for p in issues_dir.glob("*.md"):
            if not _ISSUE_FNAME_RE.match(p.name):
                out.append(
                    DisciplineViolation(
                        rule="B-issue-filename",
                        path=p,
                        detail=f"issue filename must match <slug>_YYYY_MM_DD.md: {p.name}",
                    )
                )
    return out


def _check_rule_c(archive_dir: Path) -> list[DisciplineViolation]:
    """Archived plans mentioning DEFERRED/post-cutover MUST reference a successor."""
    out: list[DisciplineViolation] = []
    for p in archive_dir.glob("*.md"):
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if (_ARCHIVE_OK_TOKENS_RE.search(text) or _has_live_deferred_marker(text)) and not _SUCCESSOR_RE.search(text):
            out.append(
                DisciplineViolation(
                    rule="C-archive-no-successor",
                    path=p,
                    detail="mentions DEFERRED/post-cutover/out-of-scope but no successor reference found",
                )
            )
    return out


def _load_baseline(baseline_path: Path) -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count: object = cast(dict[str, object], loaded).get("violation_count")
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(baseline_path: Path, violations: list[DisciplineViolation]) -> None:
    payload: dict[str, object] = {
        "violation_count": len(violations),
        "rule": "plan-discipline",
        "source": "governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group A",
        "baseline_files": [{"rule": v.rule, "path": str(v.path)} for v in violations],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan-discipline check (DEFERRED banners + filename + archive).")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
    )
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)

    active_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "active"
    archive_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "archive"
    issues_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "active" / "issues"

    if not active_dir.is_dir():
        print(f"ERROR: plans/active not found at {active_dir}", file=sys.stderr)
        return 2

    violations: list[DisciplineViolation] = []
    violations.extend(_check_rule_a(active_dir))
    violations.extend(_check_rule_b(active_dir, issues_dir))
    if archive_dir.is_dir():
        violations.extend(_check_rule_c(archive_dir))

    print(
        f"Scanned plans/active/ ({len(list(active_dir.glob('*.md')))} plans) + issues + archive — "
        f"{len(violations)} violation(s)."
    )

    if baseline_write:
        _write_baseline(baseline_path, violations)
        print(f"✅ Wrote baseline ({len(violations)} violations) to {baseline_path}")
        return 0

    by_rule: dict[str, int] = {}
    for v in violations:
        by_rule[v.rule] = by_rule.get(v.rule, 0) + 1
    if by_rule:
        print(f"Per-rule: {by_rule}")
    if violations:
        print("\nFirst 20 violations:")
        for v in violations[:20]:
            try:
                rel = v.path.relative_to(workspace_root)
            except ValueError:
                rel = v.path
            print(f"  - [{v.rule}] {rel}: {v.detail}")
        if len(violations) > 20:
            print(f"  ... + {len(violations) - 20} more")

    if strict:
        if violations:
            print(f"\n❌ STRICT: {len(violations)} violation(s).")
            return 1
        return 0

    baseline = _load_baseline(baseline_path)
    if len(violations) > baseline:
        print(f"\n❌ Regression: {len(violations)} > baseline {baseline}.")
        return 1
    if len(violations) < baseline:
        print(f"\n⚠️  Improvement: {len(violations)} < baseline {baseline}. Re-baseline to codify.")
        return 0
    print(f"\n✅ At baseline ({baseline}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
