#!/usr/bin/env python3
# Epic: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06
# Lifecycle: temporary
# Delete-when: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 9 ships
#
# staging-lock-check.yml (todo 11, DONE 2026-08-08): its `check-staging-lock` job is a
# literal required-status-check context on 16 repos' branch protection rulesets
# (`require-staging-lock-check`), and a workflow_call caller job reports its check as
# "<caller job name> / <callee job name>" -- NOT the bare callee name. The FILE_JOB_NAME
# entry below ("check-staging-lock") makes that resolve to the ruleset's NEW context
# "check-staging-lock / check-staging-lock" -- the 16 rulesets were updated to that string
# BEFORE converting, verified live via a real triggered PR (trading-agent-service canary,
# run 31236639223, conclusion=success, check name confirmed via the Checks API).
#
# REAL BUG found + fixed during that canary (SKIP_CALLER_CONCURRENCY below): this file's
# source template carries its own `concurrency:` block, which (unlike every OTHER converted
# file) this script would otherwise ALSO copy into the caller stub -- duplicating the exact
# same group expression (`${{ github.workflow }}-${{ github.ref }}`) in BOTH the caller and
# the callee. For a `pull_request`-triggered caller, that self-referential collision makes
# GitHub fail the ENTIRE run with zero jobs scheduled ("This run likely failed because of a
# workflow file issue", conclusion=failure) -- bisected empirically (7 iterations against a
# live throwaway branch) since actionlint validates each file in isolation and catches
# neither half of the collision. Confirmed NOT an issue for the other 8 files' push-triggered
# callers (semver-agent.yml has the identical duplicate-declaration pattern and works fine
# live) -- this is specific to pull_request triggers, so the fix is scoped to this one file
# rather than stripping caller-side concurrency fleet-wide.
#
# semver-agent.yml.tmpl (todo 5, DONE 2026-08-07, all 23 fleet repos converted): unlike
# the other files, this one needed REAL per-repo `with:` values (repo_name/source_dir/
# version_source) on EVERY caller, not just self-hosted ones -- passed as extra positional
# args (see usage below). `.tmpl` is stripped from the canonical filename to get both the
# FILE_JOB_NAME lookup key and the unified-trading-ci `uses:` target name (the hosted file
# has no .tmpl suffix). This logic lived only in a scratchpad copy for part of the todo-5
# session (the real copy of this file kept getting overwritten by a concurrent session's
# `git pull --rebase --autostash` mid-session) -- reconciled back here post-hoc, verified
# byte-identical output to what actually shipped to all 23 repos.
"""Generate a thin caller-stub workflow file for a given canonical template + repo.
Keeps the ORIGINAL on:/permissions:/concurrency: blocks (the physical trigger every
caller must carry) and replaces jobs: with a single uses: call into unified-trading-ci.

Usage: python3 make_stub.py <canonical-template.yml> <0|1 self-hosted> [repo_name] [source_dir] [version_source]
The 3 extra positional args are required for semver-agent.yml.tmpl only (its reusable
workflow has no universal default for them); omit for every other file.
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
    "semver-agent.yml": "semver",
    "staging-lock-check.yml": "check-staging-lock",
}

# See the header note above: staging-lock-check.yml's callee already declares this exact
# concurrency group; duplicating it in the caller breaks pull_request-triggered runs.
SKIP_CALLER_CONCURRENCY = {"staging-lock-check.yml"}

REQUEST_MAJOR_BUMP_WITH_EXTRA = """      proposed_version: ${{ inputs.proposed_version }}
      reason: ${{ inputs.reason }}
      approver: ${{ inputs.approver }}
"""


def main():
    canonical_path = sys.argv[1]
    self_hosted = sys.argv[2] == "1"
    extra_args = sys.argv[3:]
    fname = canonical_path.split("/")[-1]
    if fname.endswith(".tmpl"):
        fname = fname[: -len(".tmpl")]

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
    if "concurrency" in sec_map and fname not in SKIP_CALLER_CONCURRENCY:
        c_s, c_e = sec_map["concurrency"]
        out.append("\n".join(body_lines[c_s:c_e]).rstrip("\n"))
        out.append("")

    job_name = FILE_JOB_NAME[fname]
    out.append("jobs:")
    out.append(f"  {job_name}:")
    out.append(f"    uses: IggyIkenna/unified-trading-ci/.github/workflows/{fname}@main")
    needs_with = self_hosted or fname in ("request-major-bump.yml", "semver-agent.yml")
    if needs_with:
        out.append("    with:")
        if self_hosted:
            out.append('      self_hosted_runner_labels: \'["self-hosted","glue"]\'')
        if fname == "request-major-bump.yml":
            out.append(REQUEST_MAJOR_BUMP_WITH_EXTRA.rstrip("\n"))
        if fname == "semver-agent.yml":
            repo_name, source_dir, version_source = extra_args
            out.append(f'      repo_name: "{repo_name}"')
            out.append(f'      source_dir: "{source_dir}"')
            out.append(f'      version_source: "{version_source}"')
    out.append("    secrets: inherit")
    out.append("")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()
