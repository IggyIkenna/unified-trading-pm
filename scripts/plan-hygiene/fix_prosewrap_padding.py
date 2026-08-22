#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Repair prettier proseWrap continuation-padding (check_prosewrap_padding.sh's flagged lines).

WHY THIS EXISTS: prettier's proseWrap-always markdown printer has a non-idempotent reflow bug for
2nd+ blocks inside list items — every prettier pass ADDS leading-space padding to continuation lines
instead of converging. check_prosewrap_padding.sh (a shrinking ratchet, baseline in
prosewrap_padding_baseline.yaml) stops the bleeding but does NOT fix existing debt; the corpus-wide
remediation todo (plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md) is
hand-repair work. This script automates that hand-repair for a set of files: it collapses exactly the
lines the check flags, in exactly the two corruption classes the check detects.

TRAPS LEARNED (2026-08-10, 18th promote-wall dispatch agt-e56165):
  - The check's --only <path> mode is NOT the tool for "how many violations does this file have at
    HEAD" — it reports violations NEW vs `git show HEAD:<path>`, i.e. 0 for a file whose corruption was
    already committed. Use it pre-commit; use the no-arg corpus mode for the current count.
  - "Anchor indent" (target for over-indented continuation lines) = the nearest preceding non-blank
    line whose indent is below INDENT_THRESHOLD (14). The prior hand-fix (commit c80e2ce565) used this
    same rule — it reduced ~150-space padded lines to the 26-space list-item content indent, not to 0.
    Blindly lstrip()-ing to column 0 would flatten legitimate nested-list indentation.
  - Fenced code blocks and table rows are legitimately exempt — mirror the check's detectors exactly
    (skip lines starting with triple backticks, skip lines starting with a pipe), or the "repair"
    introduces new violations.
  - Repair must be content-preserving: `git diff -w` must be empty after a correct run (this is how the
    check's own docs verify a clean repair).
  - DO NOT add indented comment lines inside the fix loop body. A markdown-aware formatter can
    de-indent a "# ..." comment block inside an `if` body and silently break the Python (observed
    2026-08-10, same session). Keep the loop body code-only; put every explanation in this docstring.

USAGE:
  python3 scripts/plan-hygiene/fix_prosewrap_padding.py <file> [<file> ...]
Prints per-file changed-line counts. Re-run bash scripts/plan-hygiene/check_prosewrap_padding.sh
afterwards to confirm the corpus count dropped; --update-baseline only after a genuine reviewed
cleanup pass (never to silence a live regression — that violates the ratchet contract).
"""

import re
import sys

THRESH = 14  # must stay in sync with INDENT_THRESHOLD in check_prosewrap_padding.sh


def fix_file(path: str, only_lines: set[int] | None = None) -> int:
    """Repair prosewrap padding in ``path``.

    ``only_lines`` (1-indexed) restricts the repair to exactly those lines — the ones
    ``check_prosewrap_padding.sh --only --emit-lines`` identified as NEW in this commit. Without
    it the whole file is repaired, which is right for the supervised corpus-wide remediation but
    wrong at commit time: measured 2026-08-10, whole-file mode rewrites 10 of 25 sampled active
    plans (one by 51 lines). Those edits are genuine repairs — the corpus check sits at BASELINE,
    not zero — but attaching dozens of unrelated line changes to every plan commit widens the
    merge-conflict surface on the busiest file class in a repo already fighting push contention.
    Scoping is therefore the precondition for auto-wiring this into the pre-commit path.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    out = list(lines)
    fence = False
    changed = 0
    for i, ln in enumerate(lines):
        if re.match(r"^\s*```", ln):
            fence = not fence
            continue
        if fence:
            continue
        # Fence state must still be tracked for EVERY line above, so the scope filter applies
        # only after it — an early `continue` here would desynchronise `fence`.
        if only_lines is not None and (i + 1) not in only_lines:
            continue
        is_table = bool(re.match(r"^\s*\|", ln))
        if not is_table and ln.strip():
            m = re.match(r"^( *)", ln)
            ind = len(m.group(1))
            if ind >= THRESH:
                anchor = None
                for j in range(i - 1, -1, -1):
                    a = lines[j]
                    if not a.strip():
                        continue
                    am = re.match(r"^( *)", a)
                    if len(am.group(1)) < THRESH:
                        anchor = len(am.group(1))
                        break
                if anchor is None:
                    anchor = 0
                out[i] = " " * anchor + ln.lstrip()
                changed += 1
        if not is_table:
            s = ln

            def repl(match: re.Match[str]) -> str:
                span = match.group(0)
                return re.sub(r" {3,}", " ", span)

            ns = re.sub(r"`[^`]*`", repl, s)
            if ns != s:
                out[i] = ns
                changed += 1
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
    return changed


def _read_scope_from_stdin() -> dict[str, set[int]]:
    """Parse ``<file>:<lineno>`` pairs (the output of ``--only --emit-lines``) into a per-file
    line scope. Malformed lines are skipped rather than fatal: this runs inside a pre-commit
    hook, where turning a parse hiccup into a blocked commit would be worse than repairing
    nothing."""
    scope: dict[str, set[int]] = {}
    for raw in sys.stdin:
        entry = raw.strip()
        if not entry or ":" not in entry:
            continue
        path, _, lineno = entry.rpartition(":")
        if not path or not lineno.isdigit():
            continue
        scope.setdefault(path, set()).add(int(lineno))
    return scope


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--scoped":
        scope = _read_scope_from_stdin()
        if not scope:
            return 0
        total = 0
        for path, line_nos in sorted(scope.items()):
            count = fix_file(path, only_lines=line_nos)
            total += count
            print(f"{count:5d}  {path}  (scoped to {len(line_nos)} flagged line(s))")
        print(f"TOTAL lines changed: {total}")
        return 0

    files = args
    if not files:
        print(
            "usage: fix_prosewrap_padding.py <file> [<file> ...]\n"
            "       check_prosewrap_padding.sh --only --emit-lines <file>... "
            "| fix_prosewrap_padding.py --scoped",
            file=sys.stderr,
        )
        return 2
    total = 0
    for path in files:
        count = fix_file(path)
        total += count
        print(f"{count:5d}  {path}")
    print(f"TOTAL lines changed: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
