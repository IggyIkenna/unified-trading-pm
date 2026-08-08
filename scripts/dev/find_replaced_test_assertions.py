#!/usr/bin/env python3
# Epic: sports_master
# Lifecycle: permanent
# Delete-when: NA
"""Flag test-file diff hunks where an assertion or a parametrize data-row was
REPLACED, not added/removed.

Why this exists: the 2026-08-08 fleet-wide "weakened test" sweep
(`/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`, the P1 item
this script's own P2 follow-up references) screened 47 test-touching commits for NET
assertion loss / added xfail-skip. That shape is blind to a commit that deletes a
strong assertion and adds a weak one in the same hunk — net assertion count is
unchanged, so it never surfaces. This script narrows that blind spot: it scans a
commit range for hunks where at least one removed line and at least one added line
both look like either (a) a Python `assert` statement, or (b) a `@pytest.mark.
parametrize` data-row (a parenthesized, quote-containing literal) — and the two sets
of lines are not byte-identical (pure reformatting is not a replacement).

Category (b) exists because the sweep's own seed example — the commit that started
this whole plan item — is a parametrize-row swap, not an assert-line edit
(`market-tick-data-service@85423040` replaced the `("ODDS_API", "sports", ...)` row
with `("PINNACLE", "sports", ...)`, no literal `assert` line touched at all). A
first version of this script that only matched literal `assert` lines was tested
against that exact commit and MISSED it — recorded here so the gap doesn't get
silently reintroduced by a future edit that narrows the matcher back down.

This is DELIBERATELY advisory, not a gate, and deliberately noisy in one direction
only (false positives, never silently miss-by-design). The same sweep's own data is
part of why: of 6 commits its pattern-match flagged, only 1 was a genuine weakening —
the other 5 were legitimate test evolution (behaviour intentionally changed, source
deleted alongside its tests, honest xfails). Telling "weakened" from "evolved"
requires reading the surrounding test and the commit intent, which is exactly the
judgment call CLAUDE.md's findings-triage rules reserve for a human/review pass, not
a mechanizable check. Widening the matcher to catch data-row swaps (category b) also
widens the false-positive surface — any unrelated tuple-literal edit in a test file
can match. That tradeoff is intentional: this tool's job is to narrow the haystack
for a human reader, not to render a verdict — it prints candidates with full
context, it never fails a build, and it never asserts a verdict. See the plan's
`[REVIEW] P2` item for the decision this implements.

Usage (inside a checked-out repo):
    find_replaced_test_assertions.py --since <date-or-refspec> [--head HEAD]
    find_replaced_test_assertions.py --base <sha> --head <sha>

Stdlib-only (`subprocess` + `git`) — no external dependency, runs standalone in any
repo clone. Exit code is always 0; the report is the payload.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field

TEST_PATH_MARKERS = ("test_", "_test.py", "/tests/")

_DATA_ROW_RE = re.compile(r"^\(.*[\"'].*\),?$")
"""A parenthesized literal containing a quoted string, e.g. a parametrize tuple row:
`("PINNACLE", "sports", "market-data-tick-sports-prd-project"),`. Deliberately loose —
this is a haystack-narrowing heuristic, not a parser; a real function CALL that starts
a line with `(` and happens to contain a quoted string argument can also match."""


@dataclass
class ReplacedAssertHunk:
    sha: str
    subject: str
    path: str
    hunk_header: str
    removed_asserts: list[str] = field(default_factory=list)
    added_asserts: list[str] = field(default_factory=list)


def _run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def _is_test_path(path: str) -> bool:
    return any(marker in path for marker in TEST_PATH_MARKERS)


def _is_assert_line(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("assert ") or stripped == "assert" or stripped.startswith("assert("):
        return True
    return bool(_DATA_ROW_RE.match(stripped))


def _commits_in_range(base: str, head: str) -> list[tuple[str, str]]:
    """Return [(sha, subject), ...] oldest-first for commits reachable from head, not base."""
    out = _run(["git", "log", "--reverse", "--format=%H\t%s", f"{base}..{head}"])
    commits: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\t")
        commits.append((sha, subject))
    return commits


def _diff_files(sha: str) -> list[str]:
    out = _run(["git", "show", "--name-only", "--format=", sha])
    return [p for p in out.splitlines() if p.strip()]


def _scan_commit_file(sha: str, subject: str, path: str) -> list[ReplacedAssertHunk]:
    """Parse one file's diff for the given commit; return replaced-assert hunks."""
    try:
        diff = _run(["git", "show", "--format=", "--unified=0", sha, "--", path])
    except subprocess.CalledProcessError:
        return []

    findings: list[ReplacedAssertHunk] = []
    current: ReplacedAssertHunk | None = None

    def _flush() -> None:
        if current is not None and current.removed_asserts and current.added_asserts:
            removed_norm = {line.strip() for line in current.removed_asserts}
            added_norm = {line.strip() for line in current.added_asserts}
            if removed_norm != added_norm:
                findings.append(current)

    for line in diff.splitlines():
        if line.startswith("@@"):
            _flush()
            current = ReplacedAssertHunk(sha=sha, subject=subject, path=path, hunk_header=line)
            continue
        if current is None:
            continue
        if line.startswith("-") and not line.startswith("---"):
            body = line[1:]
            if _is_assert_line(body):
                current.removed_asserts.append(body)
        elif line.startswith("+") and not line.startswith("+++"):
            body = line[1:]
            if _is_assert_line(body):
                current.added_asserts.append(body)
    _flush()
    return findings


def scan_range(base: str, head: str) -> list[ReplacedAssertHunk]:
    findings: list[ReplacedAssertHunk] = []
    for sha, subject in _commits_in_range(base, head):
        for path in _diff_files(sha):
            if not _is_test_path(path):
                continue
            findings.extend(_scan_commit_file(sha, subject, path))
    return findings


def _print_report(findings: list[ReplacedAssertHunk]) -> None:
    if not findings:
        print("find_replaced_test_assertions: no candidate hunks in range.")
        return
    print(
        f"find_replaced_test_assertions: {len(findings)} candidate hunk(s) — "
        "READ each one, do not treat this list as a verdict:\n"
    )
    for f in findings:
        print(f"--- {f.path} @ {f.sha[:10]} ({f.subject})")
        print(f"    {f.hunk_header}")
        for r in f.removed_asserts:
            print(f"    - {r.strip()}")
        for a in f.added_asserts:
            print(f"    + {a.strip()}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="base ref (exclusive); required unless --since given")
    parser.add_argument("--head", default="HEAD", help="head ref (inclusive), default HEAD")
    parser.add_argument("--since", help="a git date/refspec; resolved to a base ref via 'git log -1 --before'")
    args = parser.parse_args()

    if args.base:
        base = args.base
    elif args.since:
        base = _run(["git", "log", "-1", "--format=%H", f"--before={args.since}"]).strip()
        if not base:
            print(f"find_replaced_test_assertions: no commit found before {args.since}", file=sys.stderr)
            return 0
    else:
        parser.error("one of --base or --since is required")
        return 2

    findings = scan_range(base, args.head)
    _print_report(findings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
