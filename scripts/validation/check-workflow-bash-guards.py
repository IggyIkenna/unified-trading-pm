#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Check GitHub Actions workflows for two classes of bash-guard failures.

Problem 1 — secrets.TELEGRAM_CHAT_ID
  TELEGRAM_CHAT_ID is propagated as a GitHub *variable* (gh variable set),
  not a secret (gh secret set).  Referencing it as secrets.TELEGRAM_CHAT_ID
  resolves to an empty string, causing curl 404s.
  Fix: use vars.TELEGRAM_CHAT_ID.

Problem 2 — $(cmd && echo ...) without || true in variable assignments
  Under bash -e (the GHA default), a command substitution that exits non-zero
  causes the step to abort immediately — even when it is embedded inside a
  larger variable assignment like PROMPT="...$(cmd && echo ...)...".
  Any $(... && ...) or $(... || ...) construct that can exit non-zero without
  an explicit || true / || : guard will silently kill the step.
  Fix: end the substitution with || true: $(cmd && echo "..." || true).

Usage:
    python3 check-workflow-bash-guards.py [--dir PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import cast

# Matches $(... && ...) substitution that has NO || anywhere inside the parens.
# $(A && B || C) is fine (always exits 0).  $(A && B) alone will exit 1 when A fails.
_CMD_SUBST_AND_NO_OR = re.compile(r"\$\((?![^)]*\|\|)[^)]*&&[^)]*\)")


def _check_file(path: Path) -> list[str]:
    violations: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return violations

    for lineno, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if stripped.startswith("#"):
            continue

        # Check 1: secrets.TELEGRAM_CHAT_ID
        if "secrets.TELEGRAM_CHAT_ID" in raw:
            violations.append(
                f"  {path}:{lineno}: secrets.TELEGRAM_CHAT_ID → use vars.TELEGRAM_CHAT_ID"
                " (TELEGRAM_CHAT_ID is a GH variable, not a secret)"
            )

        # Check 2: $(... && ...) with no || fallback inside — will exit non-zero under bash -e
        if _CMD_SUBST_AND_NO_OR.search(raw):
            violations.append(
                f"  {path}:{lineno}: $(... && ...) substitution without '|| true' guard"
                " — will abort step under bash -e when the && branch is false"
            )

    return violations


def check_dir(workflows_dir: Path) -> int:
    if not workflows_dir.is_dir():
        return 0
    total = 0
    for yml in sorted(workflows_dir.glob("*.yml")):
        issues = _check_file(yml)
        if issues:
            for msg in issues:
                print(msg)
            total += len(issues)
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        type=str,
        default=".github/workflows",
        help="Workflows directory to check (default: .github/workflows)",
    )
    args = parser.parse_args()

    wf_dir = Path(cast(str, args.dir))
    total = check_dir(wf_dir)
    if total:
        print(f"\n{total} workflow bash-guard violation(s) found. See messages above for fixes.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
