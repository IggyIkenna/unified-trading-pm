#!/usr/bin/env python3
# Epic: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06
# Lifecycle: temporary
# Delete-when: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 9 ships
#
# DO NOT run this for staging-lock-check.yml (todo 11) without reading that todo first: its
# `check-staging-lock` job is a literal required-status-check context on 16 repos' branch
# protection rulesets (`require-staging-lock-check`), and a workflow_call caller job reports
# its check as "<caller job name> / <callee job name>" -- NOT the bare callee name. Converting
# it with this script's default pattern silently breaks that required check the moment
# staging is un-frozen. Fix the ruleset context strings FIRST (todo 11's option (a)), verify
# with a real triggered run, THEN convert.
#
# For semver-agent.yml.tmpl (todo 5): add its RUNS_ON-equivalent handling (see
# make_reusable.py's header) and add its job name to FILE_JOB_NAME below before use.
"""Generate a thin caller-stub workflow file for a given canonical template + repo.
Keeps the ORIGINAL on:/permissions:/concurrency: blocks (the physical trigger every
caller must carry) and replaces jobs: with a single uses: call into unified-trading-ci.

Usage: python3 make_stub.py <canonical-template.yml> <0|1 self-hosted>
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


FILE_JOB_NAME = {
    "main-backmerge-to-ldr.yml": "backmerge",
    "major-bump-issue-handler.yml": "handle-major-bump",
    "request-major-bump.yml": "request-major-bump",
    "staging-backmerge-to-ldr.yml": "backmerge",
    "update-dependency-version.yml": "update-dep",
}

REQUEST_MAJOR_BUMP_WITH_EXTRA = """      proposed_version: ${{ inputs.proposed_version }}
      reason: ${{ inputs.reason }}
      approver: ${{ inputs.approver }}
"""


def main():
    canonical_path = sys.argv[1]
    self_hosted = sys.argv[2] == "1"
    fname = canonical_path.split("/")[-1]

    with open(canonical_path) as f:
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
    on_s, on_e = sec_map["on"]
    on_block = "\n".join(body_lines[on_s:on_e]).rstrip("\n")

    out = [name_line, ""]
    out.append("# Thin caller stub (fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md")
    out.append("# todo 4) -- the actual logic now lives in unified-trading-ci as a workflow_call")
    out.append("# reusable workflow. Local trigger config is unavoidable (GitHub Actions requires a")
    out.append("# physical file per repo to declare it), but no job logic lives here anymore.")
    out.append("#")
    out.append("# Do NOT hand-edit the logic here — edit")
    out.append(f"# unified-trading-ci/.github/workflows/{fname} and every caller picks it up")
    out.append("# automatically on the next run (pinned @main).")
    out.append("")
    out.append(on_block)
    out.append("")

    if "permissions" in sec_map:
        p_s, p_e = sec_map["permissions"]
        out.append("\n".join(body_lines[p_s:p_e]).rstrip("\n"))
        out.append("")
    if "concurrency" in sec_map:
        c_s, c_e = sec_map["concurrency"]
        out.append("\n".join(body_lines[c_s:c_e]).rstrip("\n"))
        out.append("")

    job_name = FILE_JOB_NAME[fname]
    out.append("jobs:")
    out.append(f"  {job_name}:")
    out.append(f"    uses: IggyIkenna/unified-trading-ci/.github/workflows/{fname}@main")
    if self_hosted or fname == "request-major-bump.yml":
        out.append("    with:")
        if self_hosted:
            out.append('      self_hosted_runner_labels: \'["self-hosted","glue"]\'')
        if fname == "request-major-bump.yml":
            out.append(REQUEST_MAJOR_BUMP_WITH_EXTRA.rstrip("\n"))
    out.append("    secrets: inherit")
    out.append("")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()
