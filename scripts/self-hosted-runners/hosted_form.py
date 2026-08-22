#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Emit the HOSTED form of a live workflow: the runner flip reverted, all other logic CURRENT.

The flip is `runs-on: [self-hosted, ...]` plus the comment banner directly above it. Both must go:
the banner literally contains the string "self-hosted, glue", so leaving it would make the baseline
fail hosted-baseline.sh's own "baseline CONTAINS the flip marker" check.
"""

import re
import sys

RUNS_ON = re.compile(r"^(\s*)runs-on:\s*\[self-hosted[^\]]*\]\s*$")
FLIP_COMMENT = re.compile(r"^\s*#.*(self-hosted|CI-cost B1|glue-writer|JIT-ephemeral)", re.I)

out: list[str] = []
with open(sys.argv[1], encoding="utf-8") as fh:
    lines = fh.read().splitlines(keepends=True)
for line in lines:
    m = RUNS_ON.match(line.rstrip("\n"))
    if m:
        # Drop the contiguous flip banner immediately above this runs-on.
        while out and FLIP_COMMENT.match(out[-1]):
            out.pop()
        out.append(f"{m.group(1)}runs-on: ubuntu-latest\n")
        continue
    out.append(line)
sys.stdout.write("".join(out))
