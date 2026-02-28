#!/usr/bin/env python3
"""Update all quickmerge.sh scripts to include issue refs in PR body."""

from pathlib import Path

WORKSPACE = Path("/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos")

SERVICES = [
    "instruments-service",
    "execution-services",
    "market-data-processing-service",
    "market-tick-data-handler",
    "features-volatility-service",
    "features-delta-one-service",
    "unified-trading-deployment-v2",
    "features-calendar-service",
    "features-onchain-service",
    "unified-trading-services",
    "ml-inference-service",
    "ml-training-service",
    "strategy-service",
]

OLD = """# Create PR with auto-merge
PR_URL=$(gh pr create \\
    --title "$COMMIT_MSG" \\
    --body "Automated PR. Will auto-merge once quality gates pass." \\
    --base main \\
    --head "$BRANCH" 2>/dev/null)"""

NEW = """# Create PR with auto-merge
# Extract issue references from commit message for PR body
ISSUE_REFS=$(echo "$COMMIT_MSG" | grep -o -E "(Fixes|Closes|Resolves) [^#]*#[0-9]+" || echo "")
PR_BODY="Automated PR. Will auto-merge once quality gates pass.

$ISSUE_REFS"

PR_URL=$(gh pr create \\
    --title "$COMMIT_MSG" \\
    --body "$PR_BODY" \\
    --base main \\
    --head "$BRANCH" 2>/dev/null)"""

updated = 0
skipped = 0

for service in SERVICES:
    script = WORKSPACE / service / "scripts" / "quickmerge.sh"

    if not script.exists():
        print(f"⏭️  {service}: No quickmerge.sh")
        continue

    content = script.read_text()

    if "ISSUE_REFS=" in content:
        print(f"✅ {service}: Already updated")
        skipped += 1
        continue

    if OLD in content:
        new_content = content.replace(OLD, NEW)
        script.write_text(new_content)
        print(f"✅ {service}: Updated")
        updated += 1
    else:
        print(f"⚠️  {service}: Pattern not found - needs manual check")

print(f"\n✅ Updated: {updated}, Skipped: {skipped}")
