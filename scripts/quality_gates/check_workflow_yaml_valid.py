#!/usr/bin/env python3
# Epic: infrastructure_master
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
        result = subprocess.run(["actionlint", *workflows], capture_output=True, text=True)
        if result.returncode != 0:
            print(
                f"✅ workflow-yaml: {len(workflows)} workflows PARSE (gate green). "
                "actionlint flagged issues (informational, non-blocking):"
            )
            print((result.stdout + result.stderr).strip()[:1500])
            return 0
        print(f"✅ workflow-yaml: {len(workflows)} workflows parse + actionlint clean")
        return 0

    print(f"✅ workflow-yaml: {len(workflows)} workflows parse (actionlint not installed — parse-only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
