#!/usr/bin/env python3
"""Git merge driver: 3-way merge pyproject.toml, resolving the `version = "X"` line to the
HIGHER semver instead of conflicting. Exit 0 if fully resolved, 1 if non-version conflicts remain.

Invoked by git during the staging->main `--rebase` promote (cure B). The version is bumped
one-commit-per-bump and main's version line is ALSO written by the LDR->main drain lineage, so the
per-bump `--rebase` conflicts ONLY on `version =`; the resolution is always deterministic (higher
semver wins). Genuine (non-version) conflicts are left as conflict markers (exit 1) so the rebase
pauses and the promoter escalates to conflict-resolution-agent.

Wire-up (runner-local, NOT committed into any repo):
    git config merge.semvermax.driver "python3 .../semver_max_merge_driver.py %O %A %B"
    printf 'pyproject.toml merge=semvermax\\n' > .git/info/attributes

SSOT: plans/active/issues/cicd_consolidated_remaining_2026_06_24.md (cure B).
"""

# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
from __future__ import annotations

import re
import subprocess
import sys

_VER_RE = re.compile(r'^version\s*=\s*"([^"]+)"\s*$')


def _semver_key(version: str) -> list[tuple[int, object]]:
    """Sort key that orders 0.9.0 < 0.10.0 numerically (not lexically)."""
    key: list[tuple[int, object]] = []
    for part in re.split(r"[.\-+]", version):
        key.append((0, int(part)) if part.isdigit() else (1, part))
    return key


def main() -> int:
    if len(sys.argv) < 4:
        sys.stderr.write("usage: semver_max_merge_driver.py %O %A %B\n")
        return 2
    base, ours, theirs = sys.argv[1], sys.argv[2], sys.argv[3]

    merged = subprocess.run(
        ["git", "merge-file", "-p", "-L", "ours", "-L", "base", "-L", "theirs", ours, base, theirs],
        capture_output=True,
        text=True,
        check=False,
    )
    if merged.returncode == 0:
        # clean 3-way merge — no conflict at all
        with open(ours, "w") as handle:
            handle.write(merged.stdout)
        return 0

    # Conflicts present: resolve ONLY hunks that are solely the `version =` line on both sides.
    lines = merged.stdout.splitlines(keepends=True)
    resolved: list[str] = []
    other_conflict = False
    idx = 0
    while idx < len(lines):
        if lines[idx].startswith("<<<<<<<"):
            ours_block: list[str] = []
            theirs_block: list[str] = []
            idx += 1
            while idx < len(lines) and not lines[idx].startswith("======="):
                ours_block.append(lines[idx])
                idx += 1
            idx += 1  # skip the ======= divider
            while idx < len(lines) and not lines[idx].startswith(">>>>>>>"):
                theirs_block.append(lines[idx])
                idx += 1
            idx += 1  # skip the >>>>>>> trailer

            ours_v = _VER_RE.match(ours_block[0].rstrip("\n")) if len(ours_block) == 1 else None
            theirs_v = _VER_RE.match(theirs_block[0].rstrip("\n")) if len(theirs_block) == 1 else None
            if ours_v and theirs_v:
                higher = max(ours_v.group(1), theirs_v.group(1), key=_semver_key)
                resolved.append(f'version = "{higher}"\n')
            else:
                # a genuine, non-version conflict — keep markers so git treats the file conflicted
                other_conflict = True
                resolved.append("<<<<<<< ours\n")
                resolved.extend(ours_block)
                resolved.append("=======\n")
                resolved.extend(theirs_block)
                resolved.append(">>>>>>> theirs\n")
        else:
            resolved.append(lines[idx])
            idx += 1

    with open(ours, "w") as handle:
        handle.write("".join(resolved))
    return 1 if other_conflict else 0


if __name__ == "__main__":
    raise SystemExit(main())
