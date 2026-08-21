#!/usr/bin/env python3
# Epic: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06
# Lifecycle: temporary
# Delete-when: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 9 ships
#
# Read-only diagnostic: print a canonical flat-copy workflow template's structural facts
# (on:/permissions:/concurrency: blocks, __RUNS_ON__ count, job names) WITHOUT reading the
# whole file into an LLM's context — used before authoring each file's reusable-workflow
# version, to catch real per-repo variance (e.g. `github.event.inputs.X` in
# request-major-bump.yml, or a required-status-check job name like staging-lock-check.yml's
# `check-staging-lock`) before blindly converting. See make_reusable.py / make_stub.py for
# the actual transform this informs.
"""Split a fleet flat-copy workflow template into (a) a workflow_call reusable-workflow
body for unified-trading-ci and (b) confirm the local on:/permissions:/concurrency: block
to keep in the per-repo stub. Pure text transform on the __RUNS_ON__ marker + top-level
YAML section boundaries — does not touch job body logic at all.

Usage: python3 split_workflow.py <path-to-canonical-template.yml>
"""

import re
import sys


def top_level_sections(lines):
    """Return list of (key, start_idx, end_idx) for top-level (col-0) keys."""
    sections = []
    cur_key = None
    cur_start = None
    for i, line in enumerate(lines):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):", line)
        if m:
            if cur_key is not None:
                sections.append((cur_key, cur_start, i))
            cur_key = m.group(1)
            cur_start = i
    if cur_key is not None:
        sections.append((cur_key, cur_start, len(lines)))
    return sections


def main():
    src_path = sys.argv[1]
    with open(src_path) as f:
        content = f.read()
    lines = content.split("\n")

    # Strip leading '#'-only header comment block + blank line before `name:`.
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("name:"):
            body_start = i
            break
    body_lines = lines[body_start:]

    sections = top_level_sections(body_lines)
    sec_map = {k: (s, e) for k, s, e in sections}

    name_line = body_lines[sec_map["name"][0]]
    on_start, on_end = sec_map["on"]
    jobs_start, jobs_end = sec_map["jobs"]

    on_block = body_lines[on_start:on_end]
    jobs_block = body_lines[jobs_start:jobs_end]

    n_runs_on = sum(1 for line in jobs_block if "__RUNS_ON__" in line)

    print("=== name line ===")
    print(name_line)
    print(f"=== on: block ({on_end - on_start} lines) ===")
    print("\n".join(on_block))
    if "permissions" in sec_map:
        p_start, p_end = sec_map["permissions"]
        print("=== permissions: block ===")
        print("\n".join(body_lines[p_start:p_end]))
    if "concurrency" in sec_map:
        c_start, c_end = sec_map["concurrency"]
        print("=== concurrency: block ===")
        print("\n".join(body_lines[c_start:c_end]))
    print(f"=== __RUNS_ON__ occurrences in jobs: {n_runs_on} ===")
    print(f"=== jobs: block line count: {jobs_end - jobs_start} ===")
    # Job names (top-level under jobs:, indented by 2 spaces)
    job_names = [line for line in jobs_block if re.match(r"^  [A-Za-z_][A-Za-z0-9_-]*:\s*$", line)]
    print("=== job names ===")
    print("\n".join(job_names))


if __name__ == "__main__":
    main()
