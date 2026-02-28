#!/bin/bash
# Create Initial Cleanup Issues (one per repo)
#
# Creates cleanup issues in each service repo to fix all codex violations.
# Issues are labeled with 'cod' and 'cleanup' for filtering.
#
# Usage:
#   bash 02-create-issues.sh [--dry-run]

set -euo pipefail

ORG="IggyIkenna"
DRY_RUN=false

# Parse arguments
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE"
    echo ""
fi

# 13 service repos (portfolio-manager-service removed - not in current workspace)
REPOS=(
    "execution-services"
    "strategy-service"
    "instruments-service"
    "unified-trading-services"
    "market-data-processing-service"
    "ml-training-service"
    "ml-inference-service"
    "features-delta-one-service"
    "features-volatility-service"
    "features-calendar-service"
    "features-onchain-service"
    "market-tick-data-handler"
    "unified-trading-deployment-v2"
)

echo "========================================="
echo "Creating Initial Cleanup Issues"
echo "========================================="
echo ""
echo "Repos: ${#REPOS[@]}"
echo ""

CREATED=0
EXISTING=0

for repo in "${REPOS[@]}"; do
    echo "📝 $repo..."

    TITLE="[CLEANUP] Fix all COD violations in $repo"

    # Create issue body
    BODY="## Objective

Fix **all** codex violations in \`$repo\`.

## Scope

**All codex standards from quality gates (8 checks):**
1. ✅ print() → logger.info() (production code only, tests/ excluded)
2. ✅ os.getenv() → config class extending UnifiedCloudServicesConfig
3. ✅ datetime.now() → datetime.now(timezone.utc)
4. ✅ bare except → specific exceptions or @handle_api_errors
5. ✅ **imports inside functions → move to top of file** (NEW: Check 5)
6. ✅ requests → httpx/aiohttp in async code
7. ✅ asyncio.run() in loops → asyncio.gather()
8. ✅ time.sleep() in async → asyncio.sleep()

**Note:** File size violations (>1500 lines) are tracked separately in COD-SIZE issues.

## Manifest

Run this to see current violations:
\`\`\`bash
cd unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup
python3 06-generate-manifests.py --repos \"$repo\"
\`\`\`

Check: \`CODEX_VIOLATIONS_MANIFEST.md\` in the repo root.

## Approach

1. **Pull latest main** (stash local changes first)
2. **Ensure quality gates up-to-date** (has Check 5: imports inside functions)
3. **Fix all violations** listed in manifest
4. **Run quality gates:** \`bash scripts/quality-gates.sh --no-fix\`
5. **Submit PR:** \`bash scripts/quickmerge.sh \"Fix all COD violations for issue #[NUMBER]\" --files \"[changed files]\"\`
6. **Verify CI passes** (if fails, fix infrastructure mismatch)

## Success Criteria

- ✅ All codex violations fixed (see manifest)
- ✅ Quality gates pass locally
- ✅ GitHub Actions pass
- ✅ Cloud Build passes
- ✅ Three-environment consistency maintained
- ✅ No duplicate dependencies (check unified-trading-services first)

## Important

**If CI fails but local passed:** Fix infrastructure, NOT code!
- Update GitHub Actions to install unified-trading-services
- Use python-version-file: 'pyproject.toml'
- Call bash scripts/quality-gates.sh --no-fix

See: @unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup/WORKFLOW.md

## Labels

- \`cod\`: Code-Owned Debt
- \`cleanup\`: Initial cleanup task"

    # Check if issue already exists
    EXISTING_ISSUE=$(gh issue list \
        --repo "$ORG/$repo" \
        --search "\"$TITLE\" in:title" \
        --json number \
        --jq '.[0].number' 2>/dev/null || echo "")

    if [ -n "$EXISTING_ISSUE" ] && [ "$EXISTING_ISSUE" != "null" ]; then
        echo "  ✅ Already exists: #$EXISTING_ISSUE"
        EXISTING=$((EXISTING + 1))
    else
        if [ "$DRY_RUN" = true ]; then
            echo "  🔍 Would create issue"
        else
            # Ensure labels exist
            gh label create "cod" --repo "$ORG/$repo" --color "d73a4a" --description "Code-Owned Debt" 2>/dev/null || true
            gh label create "cleanup" --repo "$ORG/$repo" --color "0e8a16" --description "Initial cleanup task" 2>/dev/null || true

            # Create issue
            ISSUE_NUMBER=$(gh issue create \
                --repo "$ORG/$repo" \
                --title "$TITLE" \
                --body "$BODY" \
                --label "cod,cleanup" \
                --assignee "@me" \
                2>&1 | grep -o "[0-9]*$")

            echo "  ✅ Created: #$ISSUE_NUMBER"
            CREATED=$((CREATED + 1))
        fi
    fi

    sleep 0.5  # Rate limiting
done

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo "  Created: $CREATED"
echo "  Existing: $EXISTING"
echo "  Total: ${#REPOS[@]}"
echo ""
echo "Next: bash 03-link-issues-to-project.sh"
echo ""
