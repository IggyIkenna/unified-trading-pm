#!/usr/bin/env python3
"""
Update Cleanup Issues - Add Codex Standards Reference

Adds comprehensive codex standards context to all 13 cleanup issues.

Usage:
    python update-cleanup-issues-add-codex-reference.py
"""

import subprocess
import sys

# Colors
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"

# Repo -> Issue number mapping
ISSUES = {
    "execution-services": 147,
    "strategy-service": 23,
    "instruments-service": 58,
    "unified-trading-services": 48,
    "market-data-processing-service": 46,
    "ml-training-service": 38,
    "ml-inference-service": 28,
    "features-delta-one-service": 34,
    "features-volatility-service": 25,
    "features-calendar-service": 37,
    "features-onchain-service": 27,
    "market-tick-data-handler": 51,
    "unified-trading-deployment-v2": 126,
}

ADDITIONAL_CONTEXT = """

---

## 📚 Codex Standards Reference

This cleanup aligns with **unified-trading-codex** coding standards:

**Repository**: https://github.com/IggyIkenna/unified-trading-codex
**Standards**: `06-coding-standards/README.md`

### Key Standards to Enforce

| Standard | Rule | Checked By |
|----------|------|------------|
| **Python Version** | **`>=3.13,<3.14`** (hard requirement) | `pyproject.toml`, quality gates |
| **File Size** | No files >1500 lines (COD-SIZE) | Manual review |
| **Config** | No `os.getenv()` - use config classes | Codex compliance |
| **Logging** | No `print()` - use `logger.info()` | Codex compliance |
| **Datetime** | No `datetime.now()` - use `datetime.now(timezone.utc)` | Codex compliance |
| **Errors** | No bare `except:` - use `@handle_api_errors` | Codex compliance |
| **Imports** | All at top of file (not inside functions) | Codex compliance |
| **Empty Try/Except** | No empty except blocks | Manual review |
| **Async** | No `requests` in async code - use `aiohttp` | Codex compliance |

### Quality Gates: Codex Compliance is BLOCKING

**IMPORTANT**: For this cleanup, codex compliance is **BLOCKING** (not warn-only).

```bash
# Current state (BEFORE cleanup)
[4/4] CODEX COMPLIANCE
⚠️  FAILED (warn only - not blocking)  # Doesn't block merge

# After enabling blocking (FOR cleanup)
[4/4] CODEX COMPLIANCE
❌ FAILED  # BLOCKS merge until fixed
```

**Success criteria**: All quality gates pass, including full codex compliance.

---

## 🎯 Updated Success Criteria

- ✅ **Python 3.13 enforced**: `pyproject.toml` has `requires-python = ">=3.13,<3.14"`
- ✅ **All dependencies updated**: Compatible with Python 3.13
- ✅ All COD-SIZE violations resolved (no files >1500 lines)
- ✅ **All codex compliance violations resolved**:
  - No `print()` statements in production code
  - No `os.getenv()` usage (use config classes)
  - No naive `datetime.now()` (use UTC-aware)
  - No bare `except:` blocks
  - No empty try/except blocks
  - All imports at top of file
  - No `requests` library in async code
- ✅ **Quality gates improvements applied** (whether COD-related or not):
  - Codex compliance is BLOCKING (not warn-only)
  - Git-aware differential checks for staged files
  - All 4 phases passing: Config, Linting, Tests, Codex
- ✅ All quality gates passing (including codex compliance as BLOCKING)
- ✅ Tests passing
- ✅ Clean slate for future development

---

**Updated**: 2026-02-11 - Added codex standards, Python 3.13 requirement, quality gates fixes
"""


def main():
    print(f"{BLUE}{'=' * 60}")
    print("Update Cleanup Issues - Add Codex Reference")
    print(f"{'=' * 60}{NC}\n")
    print("This will update all 13 cleanup issues to include:")
    print("  1. Reference to unified-trading-codex/06-coding-standards")
    print("  2. Full codex compliance standards table")
    print("  3. Note that codex compliance is BLOCKING (not warn-only)")
    print("  4. Updated success criteria\n")

    response = input("Continue? (y/n) ")
    if response.lower() != "y":
        print("Aborted.")
        return 0

    print()
    updated = 0
    failed = 0

    for repo, issue_number in ISSUES.items():
        print(f"{BLUE}Updating {repo} issue #{issue_number}...{NC}")

        # Get current body
        result = subprocess.run(
            [
                "gh",
                "issue",
                "view",
                str(issue_number),
                "--repo",
                f"IggyIkenna/{repo}",
                "--json",
                "body",
                "--jq",
                ".body",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  {RED}❌ Failed to fetch issue{NC}")
            failed += 1
            continue

        current_body = result.stdout.strip()

        # Check if already updated
        if "Codex Standards Reference" in current_body:
            print(f"  {GREEN}✅ Already updated{NC}")
            continue

        # Append new context
        new_body = current_body + ADDITIONAL_CONTEXT

        # Update issue
        result = subprocess.run(
            ["gh", "issue", "edit", str(issue_number), "--repo", f"IggyIkenna/{repo}", "--body", new_body],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"  {GREEN}✅ Updated{NC}")
            updated += 1
        else:
            print(f"  {RED}❌ Failed: {result.stderr.strip()}{NC}")
            failed += 1

    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{GREEN}✅ Update Complete{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")
    print(f"Updated: {updated} issues")
    print(f"Failed:  {failed} issues\n")

    if failed > 0:
        print(f"{RED}⚠️  {failed} issues failed to update - check manually{NC}")
        return 1

    print("All issues now reference:")
    print("  - unified-trading-codex/06-coding-standards/README.md")
    print("  - Python 3.13 requirement (>=3.13,<3.14)")
    print("  - Full codex compliance as success criteria")
    print("  - Codex compliance is BLOCKING (not warn-only)")
    print("  - Quality gates improvements (general fixes)\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
