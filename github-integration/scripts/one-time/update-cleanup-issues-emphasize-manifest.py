#!/usr/bin/env python3
"""
Update Cleanup Issues - Emphasize Manifest and Full Quality Gates

Adds critical instructions about reading the full manifest and running complete quality gates.

Usage:
    python update-cleanup-issues-emphasize-manifest.py [--dry-run]
"""

import json
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

# New section to prepend to "How to Fix"
CRITICAL_INSTRUCTIONS = """## 🚨 CRITICAL: Complete Fix Instructions

**BEFORE starting**, understand these requirements:

### 1. Read the ENTIRE Manifest

📄 **`CODEX_VIOLATIONS_MANIFEST.md`** (in the repo root) contains **ALL violations** you must fix.

**Location**:
- 🔗 GitHub: [View online](MANIFEST_LINK)
- 📂 Local: `./CODEX_VIOLATIONS_MANIFEST.md` or `@CODEX_VIOLATIONS_MANIFEST.md`

**CRITICAL**:
- ✅ Read the complete manifest from top to bottom (it's in your working directory!)
- ✅ Fix **EVERY violation** listed (including `examples/` directory)
- ✅ Do not skip any files - the manifest is comprehensive
- ✅ Do not assume any directories are exempt

### 2. Run FULL Quality Gates

After fixing all violations, run:

```bash
bash scripts/quality-gates.sh --no-fix
```

**CRITICAL**: ALL 4 phases MUST pass:
- ✅ **[1/4] Config validation** - pyproject.toml, dependencies
- ✅ **[2/4] Linting** - ruff format + ruff check
- ✅ **[3/4] Tests** - unit tests + smoke tests
- ✅ **[4/4] Codex compliance** - print(), os.getenv(), imports, asyncio, datetime, etc.

**DO NOT claim success unless you see**:
```
✅ QUALITY GATES PASSED
```

If any phase fails, fix the issues and run again. Do not run partial checks (like only ruff).

### 3. Common Mistakes to Avoid

❌ **DON'T**:
- Skip files in `examples/` directory
- Only run `ruff format` + `ruff check` (partial check)
- Claim success without seeing "✅ QUALITY GATES PASSED"
- Miss violations because you didn't read the full manifest

✅ **DO**:
- Read CODEX_VIOLATIONS_MANIFEST.md completely
- Fix every single violation listed
- Run `bash scripts/quality-gates.sh --no-fix` to completion
- Verify all 4 phases pass

---

"""


def get_manifest_link(repo):
    """Generate GitHub link to manifest for repo."""
    return f"https://github.com/IggyIkenna/{repo}/blob/main/CODEX_VIOLATIONS_MANIFEST.md"


def update_issue(repo, issue_number, dry_run=False):
    """Update a single issue with critical instructions."""
    print(f"{BLUE}Processing {repo}#{issue_number}...{NC}")

    # Get current issue body
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
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"{RED}  ❌ Failed to fetch issue: {result.stderr}{NC}")
        return False

    current_body = json.loads(result.stdout)["body"]

    # Check if already updated
    if "🚨 CRITICAL: Complete Fix Instructions" in current_body:
        print(f"{YELLOW}  ⚠️  Already updated (skipping){NC}")
        return True

    # Find the "## 📋 Pre-Computed Violations Manifest" section
    if "## 📋 Pre-Computed Violations Manifest" not in current_body:
        print(f"{YELLOW}  ⚠️  No manifest section found (skipping){NC}")
        return True

    # Insert critical instructions BEFORE the manifest section
    manifest_link = get_manifest_link(repo)
    instructions = CRITICAL_INSTRUCTIONS.replace("MANIFEST_LINK", manifest_link)

    parts = current_body.split("## 📋 Pre-Computed Violations Manifest", 1)
    new_body = parts[0] + instructions + "## 📋 Pre-Computed Violations Manifest" + parts[1]

    if dry_run:
        print(f"{BLUE}  [DRY-RUN] Would update issue with critical instructions{NC}")
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
        print(f"{RED}  ❌ Failed to update: {result.stderr}{NC}")
        return False

    print(f"{GREEN}  ✅ Updated successfully{NC}")
    return True


def main():
    """Update all cleanup issues."""
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print(f"{YELLOW}🔍 DRY-RUN MODE{NC}\n")

    print(f"{BLUE}Updating {len(ISSUES)} cleanup issues...{NC}\n")

    success_count = 0
    failed = []

    for repo, issue_number in ISSUES.items():
        if update_issue(repo, issue_number, dry_run):
            success_count += 1
        else:
            failed.append(f"{repo}#{issue_number}")
        print()

    # Summary
    print("=" * 70)
    print(f"{BLUE}SUMMARY{NC}")
    print("=" * 70)
    print(f"Total issues: {len(ISSUES)}")
    print(f"Updated: {GREEN}{success_count}{NC}")
    print(f"Failed: {RED}{len(failed)}{NC}")

    if failed:
        print(f"\nFailed issues: {', '.join(failed)}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}✅ All issues updated successfully!{NC}")


if __name__ == "__main__":
    main()
