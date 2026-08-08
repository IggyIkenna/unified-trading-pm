#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Advisory scanner — flags test-file diff hunks that REPLACE a check rather than add/remove one.

Origin
------
sports_taxonomy_p1_capture_and_contracts_2026_08_08.md's `[REVIEW] P2` todo: the 2026-08-08
fleet weakened-test sweep screened 47 commits by NET assertion count (added - removed) and read
each flagged commit by hand. That screen is blind to a commit that deletes a strong check and
adds a weak one in the same hunk — it nets to zero and never surfaces.

This is a SCREEN, not a verdict. It cannot tell "weaker" from "different but equally strong" —
that judgment call stays with whoever reads the flagged commit (a review agent, an /code-review
pass, a future sweep). It exists only to widen the CANDIDATE list past net-count so a human/agent
reads the right diffs.

Deliberately covers more than bare `assert` lines: the seed incident
(`market-tick-data-service@85423040`, "swap retired ODDS_API venue for PINNACLE") replaced a
`@pytest.mark.parametrize` INPUT, not an assert statement — the assert line text never changed,
only which case ran. A scanner that only watched `assert` lines would have missed the exact
commit that motivated this tool, so REPLACEMENT_SIGNAL_RE also matches parametrize/fixture-value
decorator lines and JS/TS `expect(...)` chains.

Usage
-----
    python test_replacement_scanner.py --repo <path> --since <date> [--until <date>]
    python test_replacement_scanner.py --repo <path> --commits <sha1,sha2,...>
    python test_replacement_scanner.py --self-test

Exit codes
----------
    0  always (advisory — never blocks a gate; candidate count is informational)
    2  configuration error (bad args, repo not found)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

# ── Signal pattern ───────────────────────────────────────────────────────────

#: Lines matching this are "a check" for scanning purposes: Python assert statements,
#: unittest-style assertXxx(...) calls, pytest.raises, pytest.mark.parametrize decorator
#: lines (the seed incident's actual failure shape), and JS/TS expect(...) chains.
REPLACEMENT_SIGNAL_TOKENS: Final[tuple[str, ...]] = (
    "assert ",
    "assert(",
    ".assert",  # assertEqual/assertTrue/... (unittest) — also catches Assert.
    "pytest.raises",
    "pytest.mark.parametrize",
    "expect(",
)

#: Test-file globs passed to `git log`/`git show` pathspecs.
TEST_FILE_GLOBS: Final[tuple[str, ...]] = (
    "*test_*.py",
    "*_test.py",
    "*.spec.ts",
    "*.spec.tsx",
    "*.test.ts",
    "*.test.tsx",
)


def _is_signal_line(line: str) -> bool:
    return any(tok in line for tok in REPLACEMENT_SIGNAL_TOKENS)


# ── Data model ───────────────────────────────────────────────────────────────


@dataclass
class ReplacementCandidate:
    file_path: str
    hunk_header: str
    removed_lines: list[str] = field(default_factory=list)
    added_lines: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"  {self.file_path}  {self.hunk_header}"]
        for removed in self.removed_lines:
            lines.append(f"    - {removed}")
        for added in self.added_lines:
            lines.append(f"    + {added}")
        return "\n".join(lines)


# ── Pure diff parsing (unit-testable without git) ───────────────────────────


def find_replacement_candidates(diff_text: str) -> list[ReplacementCandidate]:
    """Parse a unified diff and flag hunks that both remove AND add a distinct signal line.

    A hunk where the removed signal lines (stripped of the leading marker + whitespace) are
    NOT identical to the added signal lines is a replacement candidate — the check's content
    changed, not merely its presence/absence. A hunk that re-adds the exact same line (pure
    reformat/move) is not flagged.
    """
    candidates: list[ReplacementCandidate] = []
    current_file = "<unknown>"
    hunk_header = ""
    removed: list[str] = []
    added: list[str] = []

    def flush() -> None:
        if not hunk_header:
            return
        removed_norm = {r.strip() for r in removed}
        added_norm = {a.strip() for a in added}
        if removed_norm and added_norm and removed_norm != added_norm:
            candidates.append(
                ReplacementCandidate(
                    file_path=current_file,
                    hunk_header=hunk_header,
                    removed_lines=list(removed),
                    added_lines=list(added),
                )
            )

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            flush()
            removed, added = [], []
            hunk_header = ""
            # "diff --git a/path b/path" — take the b/ side.
            parts = raw_line.split(" b/", 1)
            current_file = parts[1] if len(parts) == 2 else raw_line
            continue
        if raw_line.startswith("@@"):
            flush()
            removed, added = [], []
            hunk_header = raw_line
            continue
        if not hunk_header:
            continue
        if raw_line.startswith("---") or raw_line.startswith("+++"):
            continue
        if raw_line.startswith("-"):
            content = raw_line[1:]
            if _is_signal_line(content):
                removed.append(content)
        elif raw_line.startswith("+"):
            content = raw_line[1:]
            if _is_signal_line(content):
                added.append(content)

    flush()
    return candidates


# ── git plumbing (thin — the parsing above is what's tested) ───────────────


def _run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell, repo path is CLI-validated
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _resolve_commits(repo: Path, since: str | None, until: str | None) -> list[str]:
    args = ["log", "--format=%H"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    args.append("--")
    args.extend(TEST_FILE_GLOBS)
    output = _run_git(repo, args)
    return [line for line in output.splitlines() if line.strip()]


def scan_commit(repo: Path, sha: str) -> list[ReplacementCandidate]:
    diff_text = _run_git(repo, ["show", "--unified=0", sha, "--", *TEST_FILE_GLOBS])
    return find_replacement_candidates(diff_text)


# ── Self-test (no git needed — the fixed point of this tool's behaviour) ───


def _self_test() -> int:
    seed_incident_diff = """diff --git a/tests/unit/test_reader.py b/tests/unit/test_reader.py
@@ -40,7 +40,7 @@ class TestTickBucket:
-    @pytest.mark.parametrize("venue", [ODDS_API, BETFAIR])
+    @pytest.mark.parametrize("venue", [PINNACLE, BETFAIR])
     def test_asset_group_for_venue(self, venue):
         assert _asset_group_for_venue(venue) == "sports"
"""
    seed = find_replacement_candidates(seed_incident_diff)
    assert len(seed) == 1, f"expected the parametrize-swap to be flagged, got {seed}"
    assert "test_reader.py" in seed[0].file_path

    pure_add_diff = """diff --git a/tests/unit/test_x.py b/tests/unit/test_x.py
@@ -10,0 +11,1 @@ def test_x():
+    assert result.status == "ok"
"""
    assert find_replacement_candidates(pure_add_diff) == [], "pure addition must not be flagged"

    pure_remove_diff = """diff --git a/tests/unit/test_x.py b/tests/unit/test_x.py
@@ -11,1 +10,0 @@ def test_x():
-    assert result.status == "ok"
"""
    assert find_replacement_candidates(pure_remove_diff) == [], "pure removal must not be flagged"

    reformat_only_diff = """diff --git a/tests/unit/test_x.py b/tests/unit/test_x.py
@@ -10,1 +10,1 @@ def test_x():
-    assert result.status == "ok"
+    assert result.status == "ok"
"""
    assert find_replacement_candidates(reformat_only_diff) == [], "identical re-add must not be flagged"

    weakened_assert_diff = """diff --git a/tests/unit/test_y.py b/tests/unit/test_y.py
@@ -20,1 +20,1 @@ def test_y():
-    assert response.venue_count == 27
+    assert response.venue_count > 0
"""
    weakened = find_replacement_candidates(weakened_assert_diff)
    assert len(weakened) == 1, f"expected the weakened assert to be flagged, got {weakened}"

    print("self-test: all scenarios passed (5/5)")
    return 0


# ── CLI ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="repo to scan")
    parser.add_argument("--since", help="git log --since= value, e.g. '2026-08-07'")
    parser.add_argument("--until", help="git log --until= value")
    parser.add_argument("--commits", help="comma-separated SHAs to scan instead of --since/--until")
    parser.add_argument("--self-test", action="store_true", help="run built-in scenarios, no git needed")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if not args.repo:
        parser.error("--repo is required unless --self-test")
    if not args.repo.is_dir():
        print(f"error: {args.repo} is not a directory", file=sys.stderr)
        return 2

    shas = (
        [s.strip() for s in args.commits.split(",") if s.strip()]
        if args.commits
        else _resolve_commits(args.repo, args.since, args.until)
    )

    total_candidates = 0
    for sha in shas:
        candidates = scan_commit(args.repo, sha)
        if candidates:
            print(f"{sha} — {len(candidates)} replacement candidate(s):")
            for c in candidates:
                print(c.render())
            total_candidates += len(candidates)

    print(f"\nscanned {len(shas)} commit(s), {total_candidates} replacement candidate(s) — "
          "read each one; this tool does not judge weaker-vs-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
