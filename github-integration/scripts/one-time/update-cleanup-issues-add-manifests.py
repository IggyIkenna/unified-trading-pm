#!/usr/bin/env python3
"""
Update cleanup issues to reference the CODEX_VIOLATIONS_MANIFEST.md file.

Usage:
    python update-cleanup-issues-add-manifests.py [--dry-run]
"""

import subprocess
import sys

# Repo → Issue number mapping from GitHub Project #5 (Initial Cleanup)
ISSUES = {
    "execution-service": 147,
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

# Violation counts
VIOLATION_COUNTS = {
    "execution-service": 927,
    "strategy-service": 307,
    "instruments-service": 797,
    "unified-trading-services": 396,
    "market-data-processing-service": 198,
    "ml-training-service": 104,
    "ml-inference-service": 14,
    "features-delta-one-service": 247,
    "features-volatility-service": 21,
    "features-calendar-service": 27,
    "features-onchain-service": 139,
    "market-tick-data-handler": 388,
    "unified-trading-deployment-v2": 487,
}


def update_issue(repo: str, issue_number: int, violation_count: int, dry_run: bool = False):
    """Update issue body to add manifest reference."""
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
        print(f"  ❌ Error reading issue #{issue_number}: {result.stderr}")
        return False

    current_body = result.stdout.strip()

    # Check if already has manifest reference
    if "CODEX_VIOLATIONS_MANIFEST.md" in current_body:
        print(f"  ⏭  Issue #{issue_number} already references manifest")
        return True

    # Add manifest section at the very top
    manifest_section = f"""## 📋 Pre-Computed Violations Manifest

**{violation_count} violations** have been detected and documented in:

📄 **[`CODEX_VIOLATIONS_MANIFEST.md`](https://github.com/IggyIkenna/{repo}/blob/main/CODEX_VIOLATIONS_MANIFEST.md)**

This manifest contains:
- ✅ **Exact locations** of all violations (file:line)
- ✅ **Violation types** (print(), os.getenv(), datetime.now(), etc.)
- ✅ **Fix instructions** for each type
- ✅ **Automatically verified** by quality gates

### How to Fix

1. **Read the manifest**: See exact violations in `CODEX_VIOLATIONS_MANIFEST.md`
2. **Fix violations**: Follow the instructions for each type
3. **Verify locally**: Run `bash scripts/quality-gates.sh --no-fix`
4. **Submit PR**: Run `bash scripts/quickmerge.sh "Fix codex violations" --files "path/to/fixed/files"`

Quality gates will **BLOCK** merge if any violations remain.

---

"""

    new_body = manifest_section + current_body

    if dry_run:
        print(f"  ✓  Would update issue #{issue_number}")
        return True

    # Update issue
    result = subprocess.run(
        [
            "gh",
            "issue",
            "edit",
            str(issue_number),
            "--repo",
            f"IggyIkenna/{repo}",
            "--body",
            new_body,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  ❌ Error updating issue #{issue_number}: {result.stderr}")
        return False

    print(f"  ✅ Updated issue #{issue_number} ({violation_count} violations)")
    return True


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 80)
    print("Update Cleanup Issues: Add Violation Manifests")
    print("=" * 80)
    print()
    print(f"Dry run: {dry_run}")
    print()

    success_count = 0
    skip_count = 0
    error_count = 0

    for repo, issue_number in ISSUES.items():
        violation_count = VIOLATION_COUNTS.get(repo, 0)
        print(f"{repo} (issue #{issue_number}, {violation_count} violations)")

        if update_issue(repo, issue_number, violation_count, dry_run):
            success_count += 1
        else:
            error_count += 1

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(f"  ✅ Success: {success_count}")
    print(f"  ⏭  Skipped: {skip_count}")
    print(f"  ❌ Errors: {error_count}")
    print()

    if dry_run:
        print("🔍 DRY RUN: No issues updated. Re-run without --dry-run to update.")
    else:
        print("✅ DONE: All issues updated with manifest references.")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
