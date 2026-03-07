# Codex Compliance Blocking - Critical Fix

**Date**: 2026-02-11 **Issue**: Codex compliance is "warn only" - doesn't block merges **Impact**: Cleanup project
success criteria cannot be enforced **Solution**: Make codex compliance BLOCKING + update issue context

---

## 🚨 Problem Identified

### Current State (BROKEN for Cleanup)

In all 13 service repos, `scripts/quality-gates.sh` has:

```bash
if [ $CODEX_STATUS -eq 0 ]; then
    echo -e "Codex:    ${GREEN}✅ PASSED${NC}"
else
    echo -e "Codex:    ${YELLOW}⚠️  FAILED (warn only - not blocking)${NC}"
    # Codex violations (print, os.getenv, datetime.now, etc.) are non-blocking for now
fi
```

**THE PROBLEM**:

- Codex compliance CAN FAIL
- But `OVERALL_STATUS` is NOT set to 1
- Merge proceeds even with violations
- ❌ Defeats the purpose of the cleanup!

### What Codex Compliance Checks

Currently checking (in quality-gates.sh):

1. ✅ `print()` statements in production code
2. ✅ `os.getenv()` usage (should use config classes)
3. ✅ `datetime.now()` without UTC
4. ✅ Bare `except:` clauses
5. ✅ `requests` library in async code (should use `aiohttp`)
6. ✅ `asyncio.run()` in loops
7. ✅ `time.sleep()` in async functions

**NOT checking** (but should be): 8. ❌ File size >1500 lines (COD-SIZE) - checked separately 9. ❌ Empty try/except
blocks - needs to be added 10. ❌ Imports inside functions (currently just warns)

### Cleanup Issues Missing Context

The 13 cleanup issues created (#147, #23, #58, etc.) are missing:

- Reference to `unified-trading-codex/06-coding-standards`
- Full list of codex compliance standards
- Note that codex compliance will be BLOCKING
- Updated success criteria

---

## ✅ Solution

### Step 1: Update All 13 Cleanup Issues

Add comprehensive context about codex standards and blocking enforcement:

```bash
cd unified-trading-codex/11-project-management/github-integration
bash scripts/one-time/update-cleanup-issues-add-codex-reference.sh
```

**What this does**:

- Appends section: "📚 Codex Standards Reference"
- Links to `unified-trading-codex/06-coding-standards/README.md`
- Lists all standards in a table (file size, config, logging, datetime, errors, imports, etc.)
- Explains codex compliance is BLOCKING (not warn-only)
- Updates success criteria to include full codex compliance

**Result**: All 13 issues now have complete context.

### Step 2: Enable Codex Compliance Blocking

Make codex compliance failures BLOCK merges in all services:

```bash
cd unified-trading-codex/11-project-management/github-integration
python scripts/one-time/enable-codex-compliance-blocking.py
```

**What this does**:

- Finds all `quality-gates.sh` files (13 services)
- Replaces:
  ```bash
  echo -e "Codex:    ${YELLOW}⚠️  FAILED (warn only - not blocking)${NC}"
  ```
  With:
  ```bash
  echo -e "Codex:    ${RED}❌ FAILED${NC}"
  OVERALL_STATUS=1
  ```
- Removes "non-blocking" comment
- Creates backup before modifying
- Verifies changes

**Result**: Codex violations now BLOCK merges.

### Step 3: Commit Changes

```bash
cd unified-trading-deployment-v2

bash git-quickmerge.sh "Enable codex compliance blocking for cleanup" --all --files \
  "execution-service/scripts/quality-gates.sh" \
  "strategy-service/scripts/quality-gates.sh" \
  "instruments-service/scripts/quality-gates.sh" \
  "unified-trading-services/scripts/quality-gates.sh" \
  "market-data-processing-service/scripts/quality-gates.sh" \
  "ml-training-service/scripts/quality-gates.sh" \
  "ml-inference-service/scripts/quality-gates.sh" \
  "features-delta-one-service/scripts/quality-gates.sh" \
  "features-volatility-service/scripts/quality-gates.sh" \
  "features-calendar-service/scripts/quality-gates.sh" \
  "features-onchain-service/scripts/quality-gates.sh" \
  "market-tick-data-handler/scripts/quality-gates.sh" \
  "unified-trading-deployment-v2/scripts/quality-gates.sh"
```

---

## 🎯 Updated Cleanup Success Criteria

**BEFORE** (incomplete):

- ✅ All COD-SIZE violations resolved (no files >1500 lines)
- ✅ All quality gates passing
- ✅ Tests passing

**AFTER** (comprehensive):

- ✅ All COD-SIZE violations resolved (no files >1500 lines)
- ✅ **All codex compliance violations resolved**:
  - No `print()` statements in production code
  - No `os.getenv()` usage (use config classes)
  - No naive `datetime.now()` (use UTC-aware)
  - No bare `except:` blocks
  - No empty try/except blocks
  - All imports at top of file
  - No `requests` library in async code
- ✅ All quality gates passing (**including codex compliance as BLOCKING**)
- ✅ Tests passing
- ✅ Clean slate for future development

---

## 📊 Impact

### Before This Fix

```bash
# Codex compliance fails but doesn't block
[4/4] CODEX COMPLIANCE
Checking for print() statements... FAIL
Checking for os.getenv() usage... FAIL
Checking for datetime.now() without UTC... FAIL

⚠️  FAILED (warn only - not blocking)

======================================================================
✅ ALL QUALITY GATES PASSED - Safe to push!  # ❌ FALSE POSITIVE!
======================================================================
```

**Result**: PR merges with codex violations. Cleanup incomplete.

### After This Fix

```bash
# Codex compliance fails AND blocks
[4/4] CODEX COMPLIANCE
Checking for print() statements... FAIL
Checking for os.getenv() usage... FAIL
Checking for datetime.now() without UTC... FAIL

❌ FAILED

======================================================================
QUALITY GATES SUMMARY
======================================================================
Config:   ✅ PASSED
Linting:  ✅ PASSED
Tests:    ✅ PASSED
Codex:    ❌ FAILED  # ✅ BLOCKS merge now!
======================================================================

❌ QUALITY GATES FAILED - Fix issues before pushing
======================================================================
```

**Result**: PR cannot merge until codex violations fixed. Cleanup enforced.

---

## 📚 Reference: Codex Standards

Full standards: `unified-trading-codex/06-coding-standards/README.md`

### Key Rules

| Standard      | Rule             | Example                      |
| ------------- | ---------------- | ---------------------------- |
| **Config**    | No `os.getenv()` | Use `config.gcp_project_id`  |
| **Logging**   | No `print()`     | Use `logger.info()`          |
| **Datetime**  | Always UTC       | `datetime.now(timezone.utc)` |
| **Errors**    | No bare except   | Use `@handle_api_errors`     |
| **Imports**   | Top of file      | Never inside functions       |
| **Async**     | No `requests`    | Use `aiohttp`                |
| **File Size** | Max 1500 lines   | COD-SIZE violations          |

### Quality Gate Phases

1. **Config** - Validate configuration
2. **Linting** - ruff format + ruff check
3. **Tests** - pytest with coverage
4. **Codex Compliance** - Coding standards ← **NOW BLOCKING**

---

## 🔧 Testing

### Verify Codex Compliance is Blocking

1. Introduce a violation:

   ```python
   # In any production file
   print("This should fail codex compliance")
   ```

2. Run quality gates:

   ```bash
   bash scripts/quality-gates.sh
   ```

3. Expected result:

   ```
   [4/4] CODEX COMPLIANCE
   Checking for print() statements... FAIL

   ❌ FAILED

   ❌ QUALITY GATES FAILED - Fix issues before pushing
   ```

4. Verify exit code:
   ```bash
   echo $?  # Should be 1 (failure)
   ```

---

## 📋 Next Steps

1. ✅ Update all 13 cleanup issues (add codex context)
2. ✅ Enable codex compliance blocking (13 services)
3. ✅ Commit changes to all services
4. ⏭️ Configure Project #5 workflows (8 workflows from Project #3)
5. ⏭️ Run `batch-fix-v2.sh` with 7 workers
6. ⏭️ Verify all issues auto-close on PR merge
7. ⏭️ Validate clean slate: no COD-SIZE, no codex violations

---

**Status**: Scripts created, ready to execute **Priority**: CRITICAL - must run before cleanup execution **Owner**:
Agent / User **Reference**: Initial Cleanup Project (#5)
