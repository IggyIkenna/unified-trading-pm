#!/usr/bin/env python3
# Epic: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06
# Lifecycle: temporary
# Delete-when: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 9 ships
#
# Used for todo 3 (version-registry-notify.yml) + todo 4 (5 files, 2026-08-07) + todo 5
# (semver-agent.yml.tmpl, 2026-08-07). CORRECTION to this file's own prior header note: the
# live template already uses `__RUNS_ON__` (double-underscore), NOT `{{RUNS_ON}}` -- that
# note was stale (written from the plan's pre-2026-08-07 text; rollout-workflow-templates.sh
# itself explains why: a bare `{{RUNS_ON}}` gets mangled by this repo's prettier-autostage
# pre-commit hook into invalid YAML, so the marker was migrated to `__RUNS_ON__` fleet-wide
# before todo 5 started). Verified via direct grep, not assumed -- see this epic's plan Todo 5
# findings. semver-agent.yml.tmpl DOES have 3 more real per-repo markers beyond RUNS_ON --
# `__REPO_NAME__`, `__SOURCE_DIR__`, `__VERSION_SOURCE__` -- handled below via the same
# `with:` input pattern (each only added if actually present in the source, so this stays a
# no-op for files that don't have them).
"""Generate a workflow_call reusable-workflow file from a PM canonical flat-copy template.
Mechanical transform ONLY: swap the on:/permissions:/concurrency: header for an
`on: workflow_call:` block with a self_hosted_runner_labels input (+ repo_name/source_dir/
version_source inputs, added only if those markers are present in the source), and replace
every `runs-on: __RUNS_ON__` (and any of the other 3 markers) with the input-driven
expression. Job bodies are copied verbatim, byte-for-byte, via string replace -- never
retyped. A source-level `concurrency:` block (if present) is carried through unchanged.

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

    # A top-level `env:` block (workflow-level, e.g. semver-agent.yml.tmpl's SERVICE_NAME/
    # SOURCE_DIR/GH_ORG) is a REAL section distinct from `jobs:` -- markers can live there
    # instead of (or as well as) inside job bodies (e.g. __SOURCE_DIR__ only ever appears via
    # this env block + shell `${SOURCE_DIR}` indirection inside steps, never as a raw marker
    # inside `jobs:` itself). Dropping this block silently breaks every step that reads it.
    env_block = ""
    if "env" in sec_map:
        e_s, e_e = sec_map["env"]
        env_block = "\n".join(body_lines[e_s:e_e]) + "\n"

    runs_on_expr = (
        "runs-on: ${{ inputs.self_hosted_runner_labels != '' "
        "&& fromJSON(inputs.self_hosted_runner_labels) || 'ubuntu-latest' }}"
    )
    jobs_block = jobs_block.replace("runs-on: __RUNS_ON__", runs_on_expr)
    assert "__RUNS_ON__" not in jobs_block, "unreplaced __RUNS_ON__ marker remains"

    # Real per-repo variance markers beyond RUNS_ON (e.g. semver-agent.yml.tmpl's
    # __REPO_NAME__/__SOURCE_DIR__/__VERSION_SOURCE__) -- each becomes a REQUIRED
    # workflow_call input (no sensible universal default, unlike self_hosted_runner_labels).
    # No-op for files that don't contain a given marker. Checked across BOTH jobs_block and
    # env_block -- a marker present only in env_block (e.g. __SOURCE_DIR__) must still surface
    # an input, or the replace below silently no-ops and the marker ships unreplaced.
    extra_input_specs = [
        ("__REPO_NAME__", "repo_name", "Repo name (e.g. market-tick-data-service) -- the calling repo's own name."),
        ("__SOURCE_DIR__", "source_dir", "Underscore form of repo_name (e.g. market_tick_data_service)."),
        (
            "__VERSION_SOURCE__",
            "version_source",
            "'git-tag' or 'pyproject.toml' -- from workspace-manifest.json's per-repo version_source.",
        ),
    ]
    extra_inputs = []
    for marker, input_name, description in extra_input_specs:
        if marker in jobs_block or marker in env_block:
            replacement = f"${{{{ inputs.{input_name} }}}}"
            jobs_block = jobs_block.replace(marker, replacement)
            env_block = env_block.replace(marker, replacement)
            extra_inputs.append((input_name, description))
    for marker, _, _ in extra_input_specs:
        assert marker not in jobs_block, f"unreplaced {marker} marker remains in jobs_block"
        assert marker not in env_block, f"unreplaced {marker} marker remains in env_block"

    perms_block = ""
    if "permissions" in sec_map:
        p_s, p_e = sec_map["permissions"]
        perms_block = "\n".join(body_lines[p_s:p_e]) + "\n"

    concurrency_block = ""
    if "concurrency" in sec_map:
        c_s, c_e = sec_map["concurrency"]
        concurrency_block = "\n".join(body_lines[c_s:c_e]) + "\n"

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
    for input_name, description in extra_inputs:
        out.append(f"      {input_name}:")
        out.append(f"        description: {description!r}")
        out.append("        type: string")
        out.append("        required: true")
    out.extend(secrets_lines)
    out.append("")
    if env_block:
        out.append(env_block.rstrip("\n"))
        out.append("")
    if perms_block:
        out.append(perms_block.rstrip("\n"))
        out.append("")
    if concurrency_block:
        out.append(concurrency_block.rstrip("\n"))
        out.append("")
    out.append(jobs_block)
    out.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(out))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
