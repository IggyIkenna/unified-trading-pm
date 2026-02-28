# Master CI/CD Plan - Corrections & Clarifications

**Date**: 2026-02-24  
**Status**: Active Corrections to 00-MASTER-CICD-PLAN.md  
**Read This First**: Before implementing Master Plan

---

## Critical Corrections

### 1. Quality Gates via Act (Not Direct Docker)

**Master Plan Says**: Stage 3 runs "Local Quality Gates - Docker (30s)"

**CORRECTION**: 
- **Stage 3** should be renamed to "Create PR Branch & Commit"
- **Stage 4** becomes "Act - Full GitHub Actions Simulation (60-90s)"
- Quality gates run **via act**, not directly in Docker
- **Why**: Double benefit - Docker parity + GitHub workflows validation

**Corrected Pipeline**:
```
STAGE 1: Dependency Validation (10s)
STAGE 2: Pre-Flight Audit (15s)
STAGE 3: Create PR Branch & Commit (5s)
STAGE 4: Act - Full GitHub Actions Simulation (60-90s)
  ├─> Runs GitHub Actions locally
  ├─> Uses Docker (same environment as CI)
  ├─> Validates: Ruff, Basedpyright, Pytest, all quality gates
  └─> Timeout: 300s (5 min max)
STAGE 5: Main Agent Handles Failures (inline, max 3 attempts)
STAGE 6: Push & Create PR (5s)
STAGE 7: GitHub Actions PR Watcher (async, after push)
  ├─> LLM analysis of PR
  ├─> Posts detailed feedback as PR comments
  ├─> Separate context for agents
  └─> Blocks merge if critical issues

TOTAL: ~2-3 minutes + async PR watcher feedback
```

---

### 2. Timeout: 300s Everywhere

**Master Plan Shows**: Various timeouts (300s standard; 600s/1800s deprecated)

**CORRECTION**: **300s (5 minutes) everywhere**

**Policy**:
- If quality gates breach 300s → **Investigate root cause**
- **Never** increase timeout to paper over slow tests
- Optimize instead: pytest-xdist, better fixtures, mock external calls

**Enforcement**:
```yaml
# quality-gates.yml
timeout-minutes: 5  # 300s for quality gates step

# cloudbuild.yaml
timeout: '300s'  # 5 minutes
```

**Examples from docs to ignore**:
- ❌ 600s (10 min) - use 300s
- ❌ 1200s (20 min)  
- ❌ 1800s (30 min) - use 300s. If 300s breached, investigate root cause without reducing quality gate quality.
- ✅ 300s (5 min) ONLY

---

### 3. Type Checker: basedpyright (Not pyright)

**Master Plan Should Specify**: basedpyright everywhere

**CORRECTION**: 11 repos still need migration from pyright → basedpyright

**Affected Repos**:
- market-data-processing-service
- pnl-attribution-service
- ml-training-service
- ml-inference-service
- features-calendar-service
- features-onchain-service
- features-delta-one-service
- features-volatility-service
- alerting-system
- unified-trading-deployment-v3
- (+ 3 libraries - check which)

**Change Required**:
```yaml
# Before (wrong)
- name: Type check
  run: pyright {source}/

# After (correct)
- name: Type check (basedpyright)
  run: basedpyright {source}/ --level warning
```

```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "basedpyright>=1.21.0,<2.0.0",  # Not pyright
]

[tool.basedpyright]  # Not tool.pyright
typeCheckingMode = "standard"
reportAny = "error"
```

---

### 4. PR Watcher Implementation

**Master Plan Says**: "Inline agent handles failures (Stage 6)"

**CORRECTION**: 
- **Stage 5**: Inline agent handles act failures (max 3 attempts)
- **Stage 7**: GitHub Actions PR Watcher (async, separate from quickmerge)

**PR Watcher Details**:
```yaml
# .github/workflows/pr-watcher.yml
name: PR Quality Watcher

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  llm-watcher:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    
    steps:
      - name: Checkout PR
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Analyze with LLM
        env:
          CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # LLM analyzes PR diff, commits, quality
          bash .github/scripts/llm-pr-watcher.sh
      
      - name: Post feedback as PR comment
        if: always()
        run: |
          gh pr comment ${{ github.event.pull_request.number }} \
            --body-file /tmp/pr-feedback.md
      
      - name: Block if critical issues
        run: |
          if grep -q "❌ CRITICAL" /tmp/pr-feedback.md; then
            echo "PR has critical issues"
            exit 1
          fi
```

**Feedback Format** (separate context for agents):
```markdown
## 🤖 Automated PR Analysis

### Quality Gates
✅ All quality gates passed via act

### Code Review
⚠️ Found 2 potential issues:

1. **File: src/service.py:45**
   - Issue: Using `os.getenv()` instead of config class
   - Fix: Replace with `config.variable_name`
   - Example: `config = MyServiceConfig(); value = config.gcp_project_id`

2. **File: tests/test_service.py:120**
   - Issue: Test timeout too high (180s)
   - Fix: Reduce to 60s or mock slow external call
   - Example: Add `@patch('external_api.call')`

### Recommendations
- Consider adding unit tests for `process_batch()` (currently 0% coverage)
- File `src/processor.py` approaching 1200 LOC (limit: 1500)

---
*Generated by Claude Code - [Full report](link-to-artifacts)*
```

**Already Implemented**: Check instruments-service for reference

---

### 5. Library Names (Codex Compliance)

**Correct Names** (from Standards Compliance Guide):
- ✅ unified-trading-services (UCS) - **Storage is HERE** (no separate storage interface)
- ✅ unified-config-interface (UCI)
- ✅ unified-events-interface (UEI)
- ✅ unified-domain-client (UDS)
- ✅ unified-market-interface (UMI)
- ✅ unified-trade-execution-interface (UOI)
- ✅ unified-ml-interface (UML) - **CORRECT NAME**

**Wrong Names** (do NOT use):
- ✅ unified-ml-interface (corrected from unified-model-interface)
- ❌ unified-storage-interface (storage is in UCS)
- ❌ unified-crypto-interface (does not exist)

**If Found in Docs**: Update to correct name

---

### 6. Package Manager Bootstrap

**Master Plan Shows**: Various patterns for pip install uv

**CORRECTION**: 

**One Exception to "never use pip"**:
```bash
# Bootstrap uv (ONLY exception to never-use-pip rule)
if ! command -v uv &> /dev/null; then
    pip install uv
fi

# After this, ALWAYS use uv
uv pip install -e ".[dev]"
uv pip install --system ruff==0.15.0
```

**Cursor Rule Update Required**:
`.cursor/rules/uv-package-manager.mdc` already has this right (line 96):
```markdown
**Exception**: `pip install uv` is allowed as a one-time bootstrap when uv is not installed.
```

---

### 7. Phase Terminology Disambiguation

**CONFLICT**: Two different "Phase" numbering systems

**CI/CD Phases** (from Master Plan & optimization docs):
- Phase 1: Core Infrastructure (Docker, act, pre-flight, etc.)
- Phase 2: Unified Quickmerge (all 32 repos)
- Phase 3: GitHub Actions updates (all 32 repos)
- Phase 4: Cloud Build updates
- Phase 5: Documentation
- Phase 6: Validation

**Audit Phases** (from AUDIT_TO_A_GRADE_ROADMAP):
- Phase 1: Critical Fixes (5 F/D repos) - Week 1-2
- Phase 2: High Priority (silent failures, UCS, etc.) - Week 3-4
- Phase 3: Debt Reduction (fallbacks, imports, coverage) - Week 5-8
- Phase 4: Excellence (polish) - Week 9-12

**Resolution**: **ALWAYS specify which phases**:
- "CI/CD Phase 1" (infrastructure setup)
- "Audit Phase 1" (critical repo fixes)

---

### 8. Canonical Reference

**When in doubt**: Use **instruments-service** as reference

**Why**:
- Already hardened to audit quality
- Has proper act setup
- Has basedpyright
- Has 300s timeout
- Has proper dependencies
- (Check for PR watcher implementation)

**Reference Doc**: 
`.cursor/plans/code_optimizations_and_ci_cd_alignment/CANONICAL-REFERENCE-INSTRUMENTS-SERVICE.md`

---

## Implementation Priority

### Before ANY other work:

1. ✅ Document instruments-service as canonical (DONE)
2. ⏳ Verify instruments-service has PR watcher
3. ⏳ Update Master Plan with corrected stages
4. ⏳ Create consolidated roadmap
5. ⏳ Create api-contracts validation plan

### Then:

6. Execute alignment (use instruments-service as template)
7. Migrate 11 repos to basedpyright
8. Ensure 300s timeout everywhere
9. Implement PR watcher in all repos (copy from instruments-service)

---

## Quick Reference

| Topic | Correct Value | Source |
|-------|---------------|--------|
| Quality Gates | Via act (not direct Docker) | User clarification |
| Timeout | 300s everywhere | User requirement |
| Type Checker | basedpyright (not pyright) | Standards guide |
| PR Watcher | Async, posts comments, blocks merge | Master Plan + instruments-service |
| Package Manager | uv (except `pip install uv` bootstrap) | Cursor rules |
| Canonical Repo | instruments-service | User guidance |
| Storage Library | unified-trading-services (not separate) | Standards guide |
| ML Library | unified-ml-interface (not model) | Standards guide |

---

**Read Before Implementing**: This corrects Master Plan without editing the large file
**Next**: Create consolidated execution roadmap with these corrections applied
