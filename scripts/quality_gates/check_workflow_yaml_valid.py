#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG: every .github/workflows/*.yml MUST PARSE as YAML (+ actionlint if available, informational).

WHY (2026-06-29 incident — plans/active/issues/fleet_promote_schedule_yaml_break_2026_06_29.md):
``ldr-to-main-promote-fleet.yml`` had an embedded ``python3 -c`` heredoc at column 0 inside a 10-space
``run: |`` block → the file failed to parse (``could not find expected ':'``). GitHub does NOT schedule a
workflow whose file is unparseable on the default branch, so the ``*/15`` fleet-promoter cron silently
STOPPED for ~7h (fleet-wide no LDR→main drain) — discovered only by a promotion-lag alert, not at merge.

This gate FAILS on an unparseable workflow (the exact incident class) so it's caught pre-merge. actionlint
(if installed) runs as an INFORMATIONAL deeper check — it does NOT fail the gate, to avoid blocking on
pre-existing style warnings; only the YAML-parse failure is enforced.
"""

from __future__ import annotations

import glob
import shutil
import subprocess
import sys

import yaml


def main() -> int:
    workflows = sorted(glob.glob(".github/workflows/*.yml") + glob.glob(".github/workflows/*.yaml"))
    if not workflows:
        print("✅ workflow-yaml: no .github/workflows to check")
        return 0

    unparseable: list[tuple[str, str]] = []
    for path in workflows:
        try:
            with open(path, encoding="utf-8") as fh:
                yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            first = (str(exc).splitlines() or ["YAML parse error"])[0]
            unparseable.append((path, first))

    if unparseable:
        print("❌ workflow-yaml: unparseable workflow(s) — GitHub SILENTLY stops scheduling these:")
        for path, err in unparseable:
            print(f"   {path}: {err}")
        print(
            "   (a YAML break kills scheduled triggers fleet-wide — see "
            "plans/active/issues/fleet_promote_schedule_yaml_break_2026_06_29.md)"
        )
        return 1

    # Informational deeper lint — never fails the gate (avoid blocking on pre-existing style noise).
    if shutil.which("actionlint"):
        findings, stalled = _run_actionlint_per_file(workflows)
        if stalled:
            print(
                f"⚠ workflow-yaml: actionlint's shellcheck integration deadlocked on: {', '.join(stalled)} "
                "(a Go os/exec pipe-buffer stall on large embedded scripts, not a slow lint — see "
                "plans/active/quality_gates_quickmerge_timing_baseline_2026_07_31.md Progress Log). "
                "Re-linted those file(s) with shellcheck disabled so non-shellcheck findings still surface; "
                "informational only, does not fail the gate."
            )
        if findings:
            print(
                f"✅ workflow-yaml: {len(workflows)} workflows PARSE (gate green). "
                "actionlint flagged issues (informational, non-blocking):"
            )
            print("\n".join(findings)[:1500])
            return 0
        print(f"✅ workflow-yaml: {len(workflows)} workflows parse + actionlint clean")
        return 0

    print(f"✅ workflow-yaml: {len(workflows)} workflows parse (actionlint not installed — parse-only)")
    return 0


def _run_actionlint_per_file(workflows: list[str]) -> tuple[list[str], list[str]]:
    """Run actionlint one file at a time so one deadlocking file can't blank out lint signal for the rest.

    A single actionlint invocation over the whole workflow set deadlocks (confirmed via bisection) on
    ``ldr-to-main-promote-fleet.yml``'s embedded bash via actionlint's shellcheck integration — shellcheck
    itself is fast and clean on the exact same script run directly, so the stall is in actionlint's own
    subprocess IPC, not the lint content. Per-file invocation isolates the stall to that one file instead of
    losing informational output for the other ~58 clean files, and a same-file shellcheck-disabled retry
    still recovers non-shellcheck findings for the stalled file rather than skipping it outright.
    """
    findings: list[str] = []
    stalled: list[str] = []
    for path in workflows:
        try:
            result = subprocess.run(["actionlint", path], capture_output=True, text=True, timeout=5)
        except subprocess.TimeoutExpired:
            stalled.append(path)
            try:
                result = subprocess.run(["actionlint", "-shellcheck=", path], capture_output=True, text=True, timeout=5)
            except subprocess.TimeoutExpired:
                findings.append(f"{path}: actionlint timed out even with shellcheck disabled — skipped")
                continue
        except OSError as exc:
            # Shared self-hosted runners install actionlint into a common, non-job-scoped
            # ~/.local/act-tools/bin (python-quality-gates-v2.yml "Install actionlint" step) —
            # a concurrent QG job's cache-miss install can still be extracting that same binary
            # while this run tries to exec it, surfacing as OSError(26, "Text file busy").
            # actionlint is informational-only (never fails the gate) — an environmental exec
            # race on the shared binary must not crash the whole check either.
            findings.append(f"{path}: actionlint invocation failed ({exc}) — skipped (informational only)")
            continue
        if result.returncode != 0:
            findings.append((result.stdout + result.stderr).strip())
    return findings, stalled


if __name__ == "__main__":
    sys.exit(main())
