# COD-SIZE Threshold Update: 400 → 1500 Lines

**Date:** 2026-02-13  
**Status:** ✅ Complete

## Summary

Updated the file size threshold from 400 lines to 1500 lines across the entire codebase. The 1500-line limit is a hard
maximum for centralized scripts and large adapters. The ideal target remains <500 lines for most modules.

## Rationale

- **400 lines was too restrictive** for legitimate centralized scripts (e.g., instrument handlers, market data
  processors)
- **1500 lines provides flexibility** while still catching truly problematic files
- **Most files 400-1500 lines are acceptable** as centralized utilities
- **Files >1500 lines still need refactoring** (e.g., 3000-line backtest service)

## Files Updated

### 1. Core Threshold Definition

- ✅ `github-integration/run-diff-checker.py`
  - Changed check from `> 400` to `> 1500`
  - Updated title and description text

### 2. Coding Standards Codex

- ✅ `unified-trading-codex/06-coding-standards/README.md`
  - Updated from "~400 lines" to "1500 lines (hard limit)"
  - Added clarification: "Ideal target is <500 lines for most modules"

### 3. Workspace Rules

- ✅ `.cursorrules` (workspace root)
  - Updated anti-pattern table: "File >1500 lines"

### 4. Documentation

- ✅ `github-integration/README.md`
  - Tier 2 section updated to ">1500 lines"
- ✅ `github-integration/list-codex-issues-by-category.sh`
  - Comments and help text updated to ">1500 lines"
- ✅ `CLI_AUTOMATION.md`
  - Tier 2 description updated
- ✅ `E2E_ISSUE_WORKFLOW.md`
  - Canonical batch run section updated
- ✅ `CODE_STANDARDS_CHECKS.md`
  - Check 6 title and table updated
- ✅ `diff-checker-README.md`
  - File size check description updated
- ✅ `UNIFIED_WORKFLOW_FINAL.md`
  - Violation list updated
- ✅ `READY_TO_RUN_SUMMARY.md`
  - Estimate changed from "~5-10" to "~1-5" issues
- ✅ `roadmap-batch-85pct.md`
  - Work item descriptions and acceptance criteria updated

### 5. Audit Files

- ✅ `10-audit/summary.yaml`
  - Changed from "400-line guideline" to "1500-line guideline"
  - Frequency changed from "Most services" to "Some services"
- ✅ `10-audit/live/features-delta-one-service.yaml`
  - Status changed from "fail" to "pass"
  - Updated evidence and notes
- ✅ `10-audit/batch/features-delta-one-service.yaml`
  - Status changed from "fail" to "pass"
- ✅ `10-audit/batch/strategy-service.yaml`
  - Status changed from "fail" to "pass"

### 6. Scripts

- ✅ `github-integration/bulk-close-cod-size.sh`
  - **Smart filtering**: Only closes issues for files 400-1500 lines
  - **Keeps open**: Issues for files >1500 lines (still violations)
- ✅ `github-integration/update-cod-size-threshold.sh`
  - Master workflow script (calls bulk-close)

## Impact

### Before (400-line threshold):

- **~18-20 COD-SIZE issues** across all services
- Many legitimate centralized scripts flagged as violations
- Files like 700-line venue adapters marked as "must fix"

### After (1500-line threshold):

- **~2-3 COD-SIZE issues** remain (only truly huge files)
- Files 400-1500 lines are now acceptable
- Only files like 3000-line backtest service need refactoring

### Issues Automatically Deleted

All issues for files between 400-1500 lines are **deleted** (not closed).

**Rationale:** These issues aren't "fixed" - they're **invalid** because we changed the standard. Deleting is cleaner
than closing.

### Issues Kept Open

Files still needing refactoring (>1500 lines):

- `execution-services/visualizer-ui/backend/instruction_api.py` (1317 lines)
- `execution-services/visualizer-api/app/services/backtest_service.py` (3029 lines)

## Usage

### IMPORTANT: Run Diff Checker First

⚠️ **The bulk-close script only works with EXISTING GitHub issues.** If you have files >1500 lines that don't have
issues yet (like `instruments-service/instrument_processing_service.py` with 2,431 lines), they won't be caught.

**Recommended workflow:**

```bash
cd unified-trading-codex/11-project-management/github-integration

# Step 1: Run diff checker to create issues for ALL current >1500 line files
# Performance: ~9 seconds to check, ~1-2 minutes to create 1000+ issues in parallel
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex --dry-run  # Preview first
python run-diff-checker.py --repo IggyIkenna/unified-trading-codex             # Then create

# Step 2: Run master workflow (or use the simpler combined script)
bash update-cod-size-threshold.sh
```

**Performance optimizations:**

- ✅ Batch fetches all existing issues (1 API call instead of 1,209)
- ✅ Creates issues in parallel with 10 workers (customize with `--max-workers 20`)
- ✅ Dry-run completes in ~9 seconds (was 5-10 minutes)
- ✅ Real run completes in ~1-2 minutes for 1,000+ issues (was ~20 minutes)

The master workflow will:

1. Optionally run diff checker (creates issues for current violations)
2. **DELETE** all COD-SIZE issues for files 400-1500 lines (they're invalid, not fixed)
3. Keep open issues for files >1500 lines
4. Show summary of remaining issues

**Dry run first (recommended):**

```bash
bash update-cod-size-threshold.sh --dry-run
```

### Batch Fix Remaining Issues

For the ~2-3 files that are still >1500 lines:

```bash
cd unified-trading-codex/11-project-management/github-integration
ISSUES=$(bash list-codex-issues-by-category.sh size)
bash batch-fix.sh --model auto --issues "$ISSUES" --max-parallel 4
```

## Quality Gates

**Note:** The quality-gates.sh scripts do NOT check for file size limits. This is intentional:

- File size is a **periodic audit item** (checked by diff checker)
- Quality gates are **fast commit-time checks** (print, os.getenv, datetime, bare except, etc.)
- File size violations create GitHub issues, not commit blocks

## References

- **Original threshold source:** unified-trading-codex/06-coding-standards/README.md
- **Issue tracker:** run-diff-checker.py creates COD-SIZE issues
- **Batch workflow:** E2E_ISSUE_WORKFLOW.md

## Verification

To verify all references were updated:

```bash
cd unified-trading-codex
rg "\b400\b" --type md --type yaml --type sh --type py \
  | grep -i "line\|file.*size" \
  | grep -v "400-1500\|status.*400\|perms\|latency\|price\|cost\|rate"
```

Should return only non-code-related references (HTTP codes, prices, etc.).

## Next Steps

1. ✅ Run `bash update-cod-size-threshold.sh` to close old issues
2. Review remaining open COD-SIZE issues in GitHub
3. Run batch-fix for files >1500 lines (if any remain)
4. Update service-specific .cursorrules if they have hardcoded 400 references
