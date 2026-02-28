#!/bin/bash
#
# Update Cleanup Issues - Add Codex Standards Reference
#
# The initial cleanup issues are missing critical context:
# 1. Reference to unified-trading-codex/06-coding-standards
# 2. Goal of FULL codex compliance (not just COD-SIZE)
# 3. That codex compliance will be BLOCKING (not warn-only)
#
# This script updates all 13 cleanup issues with this context.
#
# Usage:
#   bash update-cleanup-issues-add-codex-reference.sh
#

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Issue numbers from INITIAL_CLEANUP_SETUP_COMPLETE.md
# Using parallel arrays for bash 3.2 compatibility (macOS default)
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

ISSUE_NUMBERS=(
    147  # execution-services
    23   # strategy-service
    58   # instruments-service
    48   # unified-trading-services
    46   # market-data-processing-service
    38   # ml-training-service
    28   # ml-inference-service
    34   # features-delta-one-service
    25   # features-volatility-service
    37   # features-calendar-service
    27   # features-onchain-service
    51   # market-tick-data-handler
    126  # unified-trading-deployment-v2
)

ADDITIONAL_CONTEXT="

---

## 📚 Codex Standards Reference

This cleanup aligns with **unified-trading-codex** coding standards:

**Repository**: https://github.com/IggyIkenna/unified-trading-codex
**Standards**: \`06-coding-standards/README.md\`

### Key Standards to Enforce

| Standard | Rule | Checked By |
|----------|------|------------|
| **Python Version** | **\`>=3.13,<3.14\`** (hard requirement) | \`pyproject.toml\`, quality gates |
| **File Size** | No files >1500 lines (COD-SIZE) | Manual review |
| **Config** | No \`os.getenv()\` - use config classes | Codex compliance |
| **Logging** | No \`print()\` - use \`logger.info()\` | Codex compliance |
| **Datetime** | No \`datetime.now()\` - use \`datetime.now(timezone.utc)\` | Codex compliance |
| **Errors** | No bare \`except:\` - use \`@handle_api_errors\` | Codex compliance |
| **Imports** | All at top of file (not inside functions) | Codex compliance |
| **Empty Try/Except** | No empty except blocks | Manual review |
| **Async** | No \`requests\` in async code - use \`aiohttp\` | Codex compliance |

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

- ✅ **Python 3.13 enforced**: \`pyproject.toml\` has \`requires-python = \">=3.13,<3.14\"\`
- ✅ **All dependencies updated**: Compatible with Python 3.13
- ✅ All COD-SIZE violations resolved (no files >1500 lines)
- ✅ **All codex compliance violations resolved**:
  - No \`print()\` statements in production code
  - No \`os.getenv()\` usage (use config classes)
  - No naive \`datetime.now()\` (use UTC-aware)
  - No bare \`except:\` blocks
  - No empty try/except blocks
  - All imports at top of file
  - No \`requests\` library in async code
- ✅ **Quality gates improvements applied** (whether COD-related or not):
  - Codex compliance is BLOCKING (not warn-only)
  - Git-aware differential checks for staged files
  - All 4 phases passing: Config, Linting, Tests, Codex
- ✅ All quality gates passing (including codex compliance as BLOCKING)
- ✅ Tests passing
- ✅ Clean slate for future development

---

**Updated**: 2026-02-11 - Added codex standards, Python 3.13 requirement, quality gates fixes"

echo -e "${BLUE}========================================"
echo "Update Cleanup Issues - Add Codex Reference"
echo -e "========================================${NC}"
echo ""
echo "This will update all 13 cleanup issues to include:"
echo "  1. Reference to unified-trading-codex/06-coding-standards"
echo "  2. Full codex compliance standards table"
echo "  3. Note that codex compliance is BLOCKING (not warn-only)"
echo "  4. Updated success criteria"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

UPDATED=0
FAILED=0

# Iterate using array indices
for i in "${!REPOS[@]}"; do
    repo="${REPOS[$i]}"
    issue_number="${ISSUE_NUMBERS[$i]}"

    echo -e "${BLUE}Updating $repo issue #$issue_number...${NC}"

    # Get current body
    CURRENT_BODY=$(gh issue view "$issue_number" --repo "IggyIkenna/$repo" --json body --jq '.body')

    # Check if already updated
    if echo "$CURRENT_BODY" | grep -q "Codex Standards Reference"; then
        echo -e "  ${GREEN}✅ Already updated${NC}"
        continue
    fi

    # Append new context
    NEW_BODY="${CURRENT_BODY}${ADDITIONAL_CONTEXT}"

    # Update issue
    if gh issue edit "$issue_number" \
        --repo "IggyIkenna/$repo" \
        --body "$NEW_BODY" 2>/dev/null; then
        echo -e "  ${GREEN}✅ Updated${NC}"
        UPDATED=$((UPDATED + 1))
    else
        echo -e "  ${RED}❌ Failed${NC}"
        FAILED=$((FAILED + 1))
    fi

    sleep 0.5  # Rate limiting
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Update Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Updated: $UPDATED issues"
echo "Failed:  $FAILED issues"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}⚠️  $FAILED issues failed to update - check manually${NC}"
    exit 1
fi

echo "All issues now reference:"
echo "  - unified-trading-codex/06-coding-standards/README.md"
echo "  - Python 3.13 requirement (>=3.13,<3.14)"
echo "  - Full codex compliance as success criteria"
echo "  - Codex compliance is BLOCKING (not warn-only)"
echo "  - Quality gates improvements (general fixes)"
echo ""
