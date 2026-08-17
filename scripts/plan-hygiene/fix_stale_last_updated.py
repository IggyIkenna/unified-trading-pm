#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""
Bump a stale `last_updated:` frontmatter field to match the latest dated entry actually
present in a doc's body (Progress Log entries, dated inline notes, etc.).

Origin: plan_reconciler_findings_all_2026_08_15.md P3 finding -- "Stale `last_updated`
frontmatter, systemic across dozens of docs corpus-wide (body content weeks ahead of
frontmatter date) -- worth a corpus-wide script fix rather than per-doc edits."

A doc's body frequently accumulates dated Progress Log / inline correction entries
(`**DONE 2026-08-15**`, `- **2026-08-16 (...)**`, etc.) long after the frontmatter's
`last_updated:` was last hand-edited. This script finds, for every doc with a
`last_updated:` scalar, the maximum YYYY-MM-DD date appearing anywhere in the body
(never in the future relative to --today), and rewrites the field when the body is
ahead -- appending a `# (was: <old> -- ...)` trailer in the same style already used by
prior manual plan-reconcile fixes, so the correction is self-documenting in git blame.

Usage:
  python3 scripts/plan-hygiene/fix_stale_last_updated.py --dry-run [--dir plans/active]
  python3 scripts/plan-hygiene/fix_stale_last_updated.py --apply --today 2026-08-17
"""

import argparse
import datetime
import pathlib
import re
import sys

PM_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

DATE_RE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
LAST_UPDATED_RE = re.compile(r'^last_updated:\s*"?(\d{4}-\d{2}-\d{2})"?\s*(#.*)?$', re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
LOCKED_BY_RE = re.compile(r"^locked_by:[ \t]*(\S[^\n]*)$", re.MULTILINE)


def is_locked(frontmatter: str) -> bool:
    m = LOCKED_BY_RE.search(frontmatter)
    return bool(m and m.group(1).strip())


def is_real_date(y: str, m: str, d: str) -> bool:
    try:
        datetime.date(int(y), int(m), int(d))
        return True
    except ValueError:
        return False


def max_body_date(body: str, today: str) -> str | None:
    best = None
    for m in DATE_RE.finditer(body):
        candidate = m.group(0)
        if not is_real_date(m.group(1), m.group(2), m.group(3)):
            continue
        if candidate > today:
            continue  # ignore typo'd / future dates -- never trust them as "latest"
        if best is None or candidate > best:
            best = candidate
    return best


def process_file(path: pathlib.Path, today: str) -> str | None:
    text = path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        return None
    frontmatter, body = fm_match.group(1), text[fm_match.end() :]
    if is_locked(frontmatter):
        return None  # actively claimed by another agent -- don't touch, even metadata-only

    lu_match = LAST_UPDATED_RE.search(frontmatter)
    if not lu_match:
        return None  # no last_updated field -- fix_frontmatter.py's job to add one
    old_date = lu_match.group(1)

    newest = max_body_date(body, today)
    if newest is None or newest <= old_date:
        return None

    trailer = (
        f"last_updated: {newest} # (was: {old_date} -- plan_reconciler stale-last-updated corpus "
        f"sweep {today}: bumped to match latest dated body entry)"
    )
    new_frontmatter = frontmatter[: lu_match.start()] + trailer + frontmatter[lu_match.end() :]
    new_text = text[: fm_match.start()] + "---\n" + new_frontmatter + "\n---\n" + body
    path.write_text(new_text, encoding="utf-8")
    return f"{path.relative_to(PM_DIR)}: {old_date} -> {newest}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="plans/active", help="root dir to scan, relative to PM repo root")
    ap.add_argument("--apply", action="store_true", help="write changes (default is dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="explicit dry-run (default behavior)")
    ap.add_argument("--today", required=True, help="YYYY-MM-DD -- upper bound, never trust a later body date")
    args = ap.parse_args()

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.today):
        print(f"--today must be YYYY-MM-DD, got {args.today!r}", file=sys.stderr)
        return 2

    root = PM_DIR / args.dir
    files = sorted(root.rglob("*.md"))
    changed: list[str] = []
    for path in files:
        if "archive" in path.parts:
            continue
        if args.apply:
            result = process_file(path, args.today)
        else:
            text = path.read_text(encoding="utf-8")
            fm_match = FRONTMATTER_RE.match(text)
            result = None
            if fm_match:
                frontmatter, body = fm_match.group(1), text[fm_match.end() :]
                lu_match = LAST_UPDATED_RE.search(frontmatter)
                if lu_match and not is_locked(frontmatter):
                    old_date = lu_match.group(1)
                    newest = max_body_date(body, args.today)
                    if newest is not None and newest > old_date:
                        result = f"{path.relative_to(PM_DIR)}: {old_date} -> {newest}"
        if result:
            changed.append(result)

    mode = "APPLIED" if args.apply else "DRY-RUN (pass --apply to write)"
    print(f"[{mode}] {len(changed)} file(s) with a stale last_updated found under {args.dir}/")
    for line in changed:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
