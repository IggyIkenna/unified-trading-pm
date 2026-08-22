#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
"""Clear the `locked_by: live-defi-rollout` hardcoded-placeholder value corpus-wide.

Context: `locked_by: live-defi-rollout` (the shared branch name, never a real actor
identity) was stamped on ~96 plans/active + plans/active/issues docs by a doc-creation
template that copied the pattern from scripts/plans/fix_epic_frontmatter_2026_05_21.py:133.
Every genuine lock in this corpus carries a real actor id (e.g. `plan_reconciler
(agt-xxxxxx) since <ts>`); this value never has. It is a non-genuine placeholder that
blocks archival via the `locked_by` HARD-STOP with zero autonomous remediation path.

Operator ruling (interactive session, 2026-08-12): Option B from
plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md —
leave the HARD-STOP as-is (any non-empty locked_by blocks auto-archival, no exceptions)
and instead run this one-time corpus-wide sweep that CLEARS locked_by/locked_since on
every doc where the value is EXACTLY `live-defi-rollout`, restoring pre-bug state so
normal archival logic picks the doc up on its next pass.

Safety: this script does NOT blind-regex the whole corpus. For every candidate doc it
parses frontmatter individually and only clears the two fields when `locked_by` is
*exactly* the literal string `live-defi-rollout` (not a substring, not a prose mention,
not a different real actor that happens to embed the branch name). Any doc whose
locked_by carries additional content beyond the bare literal (e.g. a real actor id that
happens to also reference the branch) is reported as SKIPPED-AMBIGUOUS and left untouched.

Usage:
    python3 scripts/plans/clear_locked_by_placeholder_2026_08_12.py --dry-run
    python3 scripts/plans/clear_locked_by_placeholder_2026_08_12.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [
    REPO_ROOT / "plans" / "active",
    REPO_ROOT / "plans" / "active" / "issues",
]
PLACEHOLDER = "live-defi-rollout"

LOCKED_BY_RE = re.compile(r"^locked_by:\s*(.*?)\s*$")
LOCKED_SINCE_RE = re.compile(r"^locked_since:\s*(.*?)\s*$")


def iter_candidate_files() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for d in SCAN_DIRS:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            if p.resolve() in seen:
                continue
            seen.add(p.resolve())
            out.append(p)
    return out


def frontmatter_bounds(text: str) -> tuple[int, int] | None:
    """Return (start, end) char offsets of the frontmatter block body (between --- markers)."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return (4, end)  # body starts right after the opening "---\n"


def classify(path: Path) -> tuple[str, str | None, str | None]:
    """Classify a doc. Returns (verdict, locked_by_value, locked_since_value).

    verdict in {"CLEAR", "SKIP-NOT-PLACEHOLDER", "SKIP-NO-FRONTMATTER", "SKIP-NO-LOCKED-BY-LINE"}.
    """
    text = path.read_text()
    bounds = frontmatter_bounds(text)
    if bounds is None:
        return ("SKIP-NO-FRONTMATTER", None, None)
    start, end = bounds
    body = text[start:end]
    locked_by_val: str | None = None
    locked_since_val: str | None = None
    for line in body.splitlines():
        m = LOCKED_BY_RE.match(line)
        if m is not None:
            locked_by_val = m.group(1)
            continue
        m = LOCKED_SINCE_RE.match(line)
        if m is not None:
            locked_since_val = m.group(1)
    if locked_by_val is None:
        return ("SKIP-NO-LOCKED-BY-LINE", None, None)
    if locked_by_val != PLACEHOLDER:
        return ("SKIP-NOT-PLACEHOLDER", locked_by_val, locked_since_val)
    return ("CLEAR", locked_by_val, locked_since_val)


def apply_clear(path: Path) -> None:
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    out_lines = []
    for line in lines:
        stripped = line.rstrip("\n")
        if LOCKED_BY_RE.match(stripped) and stripped.split(":", 1)[0] == "locked_by":
            out_lines.append("locked_by:\n")
            continue
        if LOCKED_SINCE_RE.match(stripped) and stripped.split(":", 1)[0] == "locked_since":
            out_lines.append("locked_since:\n")
            continue
        out_lines.append(line)
    path.write_text("".join(out_lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    candidates = iter_candidate_files()
    to_clear: list[Path] = []
    skip_not_placeholder: list[tuple[Path, str]] = []
    skip_other: list[tuple[Path, str]] = []

    for path in candidates:
        verdict, locked_by_val, _locked_since_val = classify(path)
        if verdict == "CLEAR":
            to_clear.append(path)
        elif verdict == "SKIP-NOT-PLACEHOLDER":
            if locked_by_val:  # non-empty but not the exact placeholder
                skip_not_placeholder.append((path, locked_by_val))
        else:
            skip_other.append((path, verdict))

    print(f"Scanned {len(candidates)} docs under plans/active/ + plans/active/issues/")
    print(f"Docs with locked_by == '{PLACEHOLDER}' (exact): {len(to_clear)}")
    if skip_not_placeholder:
        print(f"Docs with a non-empty, non-placeholder locked_by (left untouched, {len(skip_not_placeholder)}):")
        for p, v in skip_not_placeholder:
            print(f"  SKIP-AMBIGUOUS  {p.relative_to(REPO_ROOT)}  locked_by={v!r}")

    if args.dry_run:
        print("\n--- DRY RUN: would clear locked_by/locked_since on: ---")
        for p in to_clear:
            print(f"  {p.relative_to(REPO_ROOT)}")
        print(f"\nTotal: {len(to_clear)} docs would be cleared.")
        return 0

    # --apply
    cleared: list[Path] = []
    for p in to_clear:
        apply_clear(p)
        cleared.append(p)
    print(f"\nCleared locked_by/locked_since on {len(cleared)} docs.")
    for p in cleared:
        print(f"  CLEARED  {p.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
