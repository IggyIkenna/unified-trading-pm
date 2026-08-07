#!/usr/bin/env python3
# Epic: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06
# Lifecycle: temporary
# Delete-when: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 9 ships
#
# Used for todo 3 (version-registry-notify.yml) + todo 4 (5 files, 2026-08-07). Still needed
# for todo 5 (semver-agent.yml.tmpl) -- that file uses `{{RUNS_ON}}` (double-brace), not
# `__RUNS_ON__` (double-underscore) -- ADAPT THE MARKER before reuse, don't assume it's the
# same. Also check for OTHER `{{...}}` substitutions in semver-agent.yml.tmpl beyond RUNS_ON
# (the plan's own "Confirmed technical facts" claimed only 1 real variance point, but this
# session already found that same claim wrong for all 6 todo-4 files via split_workflow.py --
# verify, don't assume, for this file too).
"""Generate a workflow_call reusable-workflow file from a PM canonical flat-copy template.
Mechanical transform ONLY: swap the on:/permissions:/concurrency: header for an
`on: workflow_call:` block with a self_hosted_runner_labels input, and replace every
`runs-on: __RUNS_ON__` with the input-driven expression. Job bodies are copied verbatim,
byte-for-byte, via string replace -- never retyped.

Usage: python3 make_reusable.py <src-template.yml> <out-path.yml> [extra_secret1,extra_secret2,...]
Always actionlint the output before shipping -- caught 2 real bugs this way (a missing
workflow_call `inputs:` declaration for request-major-bump.yml's proposed_version/reason/
approver, referenced as bare `inputs.X` in the job body -- workflow_dispatch and workflow_call
both use the `inputs` context, but each needs its OWN inputs: declared on ITS OWN trigger).
"""

import re
import sys


def top_level_sections(lines):
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
    out_path = sys.argv[2]
    extra_secrets = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else []

    with open(src_path) as f:
        content = f.read()
    lines = content.split("\n")

    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("name:"):
            body_start = i
            break
    body_lines = lines[body_start:]
    sections = top_level_sections(body_lines)
    sec_map = {k: (s, e) for k, s, e in sections}

    name_line = body_lines[sec_map["name"][0]]
    jobs_start, jobs_end = sec_map["jobs"]
    jobs_block = "\n".join(body_lines[jobs_start:jobs_end])

    runs_on_expr = (
        "runs-on: ${{ inputs.self_hosted_runner_labels != '' "
        "&& fromJSON(inputs.self_hosted_runner_labels) || 'ubuntu-latest' }}"
    )
    jobs_block = jobs_block.replace("runs-on: __RUNS_ON__", runs_on_expr)
    assert "__RUNS_ON__" not in jobs_block, "unreplaced __RUNS_ON__ marker remains"

    perms_block = ""
    if "permissions" in sec_map:
        p_s, p_e = sec_map["permissions"]
        perms_block = "\n".join(body_lines[p_s:p_e]) + "\n"

    secrets_lines = ["    secrets:", "      GH_PAT:", "        required: false"]
    for s in extra_secrets:
        secrets_lines += [f"      {s}:", "        required: false"]

    out = []
    out.append(name_line)
    out.append("")
    out.append("# Reusable workflow (fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md")
    out.append("# todo 4) -- hosts the logic every fleet repo's own copy used to carry in full. Job")
    out.append(
        "# bodies below are byte-identical to unified-trading-pm/scripts/workflow-templates/"
        + src_path.split("/")[-1]
        + ","
    )
    out.append("# except runs-on: __RUNS_ON__ -> the self_hosted_runner_labels input below (same shape")
    out.append("# as python-quality-gates-v2.yml's already-shipped input).")
    out.append("")
    out.append("on:")
    out.append("  workflow_call:")
    out.append("    inputs:")
    out.append("      self_hosted_runner_labels:")
    out.append("        description:")
    out.append("          'JSON array of runner labels, e.g. ''[\"self-hosted\",\"glue\"]''. Empty string")
    out.append("          (default) = ubuntu-latest.'")
    out.append("        type: string")
    out.append('        default: ""')
    out.extend(secrets_lines)
    out.append("")
    if perms_block:
        out.append(perms_block.rstrip("\n"))
        out.append("")
    out.append(jobs_block)
    out.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(out))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
