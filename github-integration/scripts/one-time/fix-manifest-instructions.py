#!/usr/bin/env python3
"""
Fix manifest instructions in cleanup issues - clarify local vs GitHub paths
"""

import json
import subprocess

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


def fix_issue(repo, issue_number):
    """Fix the manifest instructions in an issue."""
    print(f"Processing {repo}#{issue_number}...")

    # Get current issue body
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", f"IggyIkenna/{repo}", "--json", "body"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("  ❌ Failed to fetch")
        return False

    body = json.loads(result.stdout)["body"]

    # Replace the manifest section text
    old_text = (
        "📄 **[`CODEX_VIOLATIONS_MANIFEST.md`](https://github.com/IggyIkenna/"
        + repo
        + "/blob/main/CODEX_VIOLATIONS_MANIFEST.md)** contains **ALL violations** you must fix.\n\n**CRITICAL**:\n- ✅ Read the complete manifest from top to bottom"
    )

    new_text = f"📄 **`CODEX_VIOLATIONS_MANIFEST.md`** (in the repo root) contains **ALL violations** you must fix.\n\n**Location**: \n- 🔗 GitHub: [View online](https://github.com/IggyIkenna/{repo}/blob/main/CODEX_VIOLATIONS_MANIFEST.md)\n- 📂 Local: `./CODEX_VIOLATIONS_MANIFEST.md` or `@CODEX_VIOLATIONS_MANIFEST.md`\n\n**CRITICAL**:\n- ✅ Read the complete manifest from top to bottom (it's in your working directory!)"

    if old_text not in body:
        print("  ⚠️  Already fixed or pattern not found")
        return True

    new_body = body.replace(old_text, new_text)

    # Update issue
    result = subprocess.run(
        ["gh", "issue", "edit", str(issue_number), "--repo", f"IggyIkenna/{repo}", "--body", new_body],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("  ❌ Failed to update")
        return False

    print("  ✅ Updated")
    return True


def main():
    print(f"Fixing manifest instructions in {len(ISSUES)} issues...\n")

    success = 0
    for repo, issue_number in ISSUES.items():
        if fix_issue(repo, issue_number):
            success += 1

    print(f"\n✅ Updated {success}/{len(ISSUES)} issues")


if __name__ == "__main__":
    main()
