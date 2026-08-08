#!/usr/bin/env python3
# Epic: sports_master
# Lifecycle: oneoff
# Delete-when: next scripts/ hygiene sweep (findings recorded in sports_taxonomy_p1_capture_and_contracts_2026_08_08.md)
"""Flag assert-replacement commits the 2026-08-08 weakened-test sweep structurally could not see.

That sweep screened test-touching commits for NET assertion loss + added xfail/skip. A commit
that DELETES a strong assertion and ADDS a different one nets to ZERO — invisible to a
count-based check by construction. This script targets exactly that blind spot: for each
test-touching commit in a date window, diff the touched test files hunk-by-hunk, and flag a
commit only when (a) the net assert-line count across the whole commit is zero, AND (b) at
least one hunk removed an assert line and added a DIFFERENT (non-identical) one in its place —
i.e. a genuine in-place replacement, not a pure reorder.

This is a candidate finder, not a verdict. Every flagged commit still needs a human read (the
sweep's own lesson: it counted, it did not read) to tell a legitimate strengthen/refactor from
a real weakening.

Usage
-----
    python detect_assert_replacement_2026_08_08.py --since 2026-08-07
    python detect_assert_replacement_2026_08_08.py --since 2026-08-07 \
        --repos market-tick-data-service unified-api-contracts

Exit codes
----------
    0  ran to completion (findings, if any, are printed — this is a report tool, not a gate)
    1  a repo/git operation failed
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ASSERT_RE = re.compile(r"\bassert\w*\s*\(|\bassert\b")
TEST_PATH_RE = re.compile(r"(^|/)tests?/.*\.(py|ts|tsx)$|(^|/)test_[^/]+\.py$|_test\.py$|\.spec\.ts$|\.test\.ts$")


@dataclass
class Hunk:
    removed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)


@dataclass
class Finding:
    repo: str
    sha: str
    subject: str
    files: list[str]
    # Per changed hunk: (removed assert lines, added assert lines) — NOT positionally
    # paired (a hunk can remove/add different counts, or reorder unrelated asserts), so
    # never read entry i of one list as "replaced by" entry i of the other. Always open
    # the real diff before drawing a conclusion; this is a candidate list, not a verdict.
    changed_hunks: list[tuple[list[str], list[str]]]


def run(cmd: list[str], cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
    return proc.stdout


def is_test_path(path: str) -> bool:
    return bool(TEST_PATH_RE.search(path))


def commits_since(repo: Path, since: str) -> list[tuple[str, str]]:
    out = run(["git", "log", "--no-merges", f"--since={since}", "--pretty=format:%H\x1f%s"], cwd=repo)
    result: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\x1f")
        result.append((sha, subject))
    return result


def touched_test_files(repo: Path, sha: str) -> list[str]:
    out = run(["git", "show", "--name-only", "--pretty=format:", sha], cwd=repo)
    return [f for f in out.splitlines() if f.strip() and is_test_path(f)]


def diff_hunks(repo: Path, sha: str, files: list[str]) -> list[Hunk]:
    out = run(["git", "show", sha, "--", *files], cwd=repo)
    hunks: list[Hunk] = []
    current: Hunk | None = None
    for line in out.splitlines():
        if line.startswith("@@"):
            current = Hunk()
            hunks.append(current)
            continue
        if current is None:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("-"):
            current.removed.append(line[1:].strip())
        elif line.startswith("+"):
            current.added.append(line[1:].strip())
    return hunks


def analyze_commit(repo_name: str, repo: Path, sha: str, subject: str, files: list[str]) -> Finding | None:
    hunks = diff_hunks(repo, sha, files)
    total_removed = 0
    total_added = 0
    changed_hunks: list[tuple[list[str], list[str]]] = []
    for hunk in hunks:
        removed_asserts = [line for line in hunk.removed if ASSERT_RE.search(line)]
        added_asserts = [line for line in hunk.added if ASSERT_RE.search(line)]
        total_removed += len(removed_asserts)
        total_added += len(added_asserts)
        if not (removed_asserts and added_asserts):
            continue
        if sorted(removed_asserts) == sorted(added_asserts):
            continue  # pure reorder, not a content change
        # A hunk where removed/added assert *sets* differ (order-insensitive) is a
        # candidate — record the whole lists, unpaired; do NOT assume line i of one
        # corresponds to line i of the other (see the Finding docstring/comment).
        changed_hunks.append((removed_asserts, added_asserts))
    net = total_added - total_removed
    if net == 0 and changed_hunks:
        return Finding(repo=repo_name, sha=sha, subject=subject, files=files, changed_hunks=changed_hunks)
    return None


def discover_repos(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if (p / ".git").exists() and "stale-pre-history-rewrite" not in p.name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace-root", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--since", default="2026-08-07")
    parser.add_argument("--repos", nargs="*", default=None, help="explicit repo list; default = every sibling clone")
    args = parser.parse_args()

    root = Path(args.workspace_root)
    repos = args.repos if args.repos else discover_repos(root)

    findings: list[Finding] = []
    scanned_commits = 0
    repos_with_test_commits: set[str] = set()

    for repo_name in repos:
        repo_path = root / repo_name
        try:
            commits = commits_since(repo_path, args.since)
        except subprocess.CalledProcessError as exc:
            print(f"skip {repo_name}: git log failed ({exc})")
            continue
        for sha, subject in commits:
            files = touched_test_files(repo_path, sha)
            if not files:
                continue
            scanned_commits += 1
            repos_with_test_commits.add(repo_name)
            finding = analyze_commit(repo_name, repo_path, sha, subject, files)
            if finding:
                findings.append(finding)

    print(
        f"Scanned {scanned_commits} test-touching commits since {args.since} "
        f"across {len(repos_with_test_commits)} repos: {sorted(repos_with_test_commits)}"
    )
    print(f"Net-zero assert-replacement candidates: {len(findings)}\n")
    for finding in findings:
        print(f"=== {finding.repo}@{finding.sha[:8]} — {finding.subject}")
        print(f"    files: {finding.files}")
        for removed_asserts, added_asserts in finding.changed_hunks:
            print("    hunk removed:")
            for line in removed_asserts:
                print(f"      - {line}")
            print("    hunk added:")
            for line in added_asserts:
                print(f"      + {line}")
        print(f"    verify: git -C {root / finding.repo} show {finding.sha}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
