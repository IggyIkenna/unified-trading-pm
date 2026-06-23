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
    `plans/archive/*.md` that mention `DEFERRED|post-cutover|out of scope` MUST
    reference a successor plan (presence of `**MIGRATED TO:**` or `successor:` or
    `→ plans/active/`).

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

DEFAULT_BASELINE_PATH = Path(__file__).parent / "plan_discipline_baseline.yaml"

_DEFERRED_RE = re.compile(r"\*\*DEFERRED\*\*|\bDEFERRED\b\s*[—\-]|\[DEFERRED\]", re.IGNORECASE)
_BANNER_RE = re.compile(r"##\s+Deferred work\s+—\s+migrated to", re.IGNORECASE)
_SUCCESSOR_RE = re.compile(
    r"MIGRATED TO:|successor:|→\s+plans/active/|See:\s+plans/active/|see\s+plans/active/",
    re.IGNORECASE,
)
_ARCHIVE_OK_TOKENS_RE = re.compile(r"\bpost.cutover\b|\bout of scope\b|\bDEFERRED\b", re.IGNORECASE)
_ACTIVE_FNAME_RE = re.compile(r"^[a-z0-9_]+(_\d{4}_\d{2}_\d{2})?\.md$")
_ISSUE_FNAME_RE = re.compile(r"^[a-z0-9_]+_\d{4}_\d{2}_\d{2}\.md$")


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
        if _DEFERRED_RE.search(text) and not _BANNER_RE.search(text):
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
        if _ARCHIVE_OK_TOKENS_RE.search(text) and not _SUCCESSOR_RE.search(text):
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

    active_dir = workspace_root / "unified-trading-pm" / "plans" / "active"
    archive_dir = workspace_root / "unified-trading-pm" / "plans" / "archive"
    issues_dir = workspace_root / "unified-trading-pm" / "plans" / "active" / "issues"

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
