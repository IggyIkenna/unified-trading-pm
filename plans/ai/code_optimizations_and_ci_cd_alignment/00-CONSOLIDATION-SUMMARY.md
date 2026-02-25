# CI/CD Planning Consolidation Summary

## TL;DR - What to Keep/Delete

### ✅ KEEP (Canonical Sources)

1. **`00-MASTER-CICD-PLAN.md`** - Complete implementation guide
2. **`DEPENDENCY-MATRIX-CANONICAL.json`** - Single source of truth for dependencies
3. **`PILOT-UCS.md`** - Interactive testing guide (archive after pilot completes)
4. **`03-cicd-alignment.md`** - Original requirements (archive, superseded by master)
5. **`03-cicd-alignment-watcher-addon.md`** - Original watcher spec (archive, superseded by master)

### ❌ DELETE (Redundant - Merged into Master Plan)

1. **`BRANCH-BASED-DEPENDENCIES.md`** → Fully covered in Master Plan Section 5
2. **`CASCADING-DEPENDENCY-QUICKMERGE.md`** → Fully covered in Master Plan Sections 4-5
3. **`DIFFERENTIAL-BASED-BRANCHING.md`** → Fully covered in Master Plan Section 3
4. **`QUICKMERGE-FLOW-DIAGRAM.md`** → ASCII diagram included in Master Plan Section 2

---

## Alignment Check

### Master Plan vs Original Requirements

| Feature | 03-cicd-alignment.md | 00-MASTER-CICD-PLAN.md | Status |
|---------|---------------------|------------------------|--------|
| Local act simulation | Phase 2 | Stage 5 (Act) | ✅ Aligned |
| Docker quality gates | Phase 1 | Stage 3 (Docker) | ✅ Aligned |
| Pre-commit hooks | Phase 3 | Stage 2 (Pre-flight) | ✅ Enhanced (LLM) |
| Secrets management | Phase 4 | Covered (GH_PAT + Secret Manager) | ✅ Aligned |
| .actrc | Phase 5 | Included in setup | ✅ Aligned |
| GitHub Actions parity | All phases | All stages | ✅ Aligned |

### Master Plan vs Watcher Addon

| Feature | watcher-addon.md | 00-MASTER-CICD-PLAN.md | Status |
|---------|-----------------|------------------------|--------|
| Local watcher | Main focus | Stage 6 (inline agent) | ✅ Simplified |
| GitHub Actions watcher | Secondary | Section 7 (mandatory) | ✅ Enhanced |
| LLM auto-fix | Core feature | Built-in | ✅ Aligned |
| Watch mode default | Suggested | Implemented | ✅ Aligned |
| PR feedback | Not specified | Comment-based | ✅ Added |

**Key Difference**: Master plan removed separate watcher process in favor of inline agent handling (simpler, faster).

---

## New Enhancements in Master Plan

1. **Differential-Based Branching** - Not in original specs
2. **Cascading Dependencies** - Not in original specs
3. **Dev Environment Support** - Not in original specs
4. **Mandatory GitHub Actions Watcher** - Enhanced from addon
5. **Canonical Dependency Matrix** - New infrastructure

---

## Canonical Dependency Matrix

### Purpose
Single source of truth for all repo dependencies. Used by:
- Quickmerge cascade logic
- GitHub Actions branch selection
- Cloud Build dependency polling
- Documentation generation
- Cursor rules validation

### Location
**`/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/code_optimizations_and_ci_cd_alignment/DEPENDENCY-MATRIX-CANONICAL.json`**

### Usage

**Cursor Rules** should reference:
```markdown
When determining dependencies, ALWAYS consult:
.cursor/plans/code_optimizations_and_ci_cd_alignment/DEPENDENCY-MATRIX-CANONICAL.json
```

**Quickmerge** reads local `.dependency-matrix.json`:
```bash
# During Stage 1, quickmerge reads:
jq -r '.dependencies[].name' .dependency-matrix.json
```

**Codex Documentation** should link:
```markdown
See canonical dependency matrix: 
.cursor/plans/code_optimizations_and_ci_cd_alignment/DEPENDENCY-MATRIX-CANONICAL.json
```

---

## Key Findings

### 1. Dependency Hierarchy (3 Levels Confirmed)

**Test Case: instruments-service**

```
Level 0: unified-config-interface, unified-events-interface, api-contracts
  └─> Level 1: unified-cloud-services (needs config/events)
      └─> Level 2: unified-domain-services (needs cloud-services + config + events)
          └─> Level 3: unified-market-interface (needs domain)
              └─> Level 4: unified-trade-execution-interface (needs market)
                  └─> Level 5: instruments-service (needs all above)
```

**Cascade Order** (when `--dep-branch "my-feature"`):
1. unified-config-interface @ my-feature
2. unified-events-interface @ my-feature
3. api-contracts @ my-feature
4. unified-cloud-services @ my-feature
5. unified-domain-services @ my-feature
6. unified-market-interface @ my-feature
7. **instruments-service @ my-feature** ← Current repo

**Validates**: Pilot should test with instruments-service, not just UCS.

### 2. Circular Dependency Handling

**unified-cloud-services ↔ unified-domain-services**

**Problem**:
- UCS imports from UDS (for domain clients)
- UDS imports from UCS (for cloud services)

**Solution** (already implemented):
- Docker has tools only (no app deps)
- Runtime installation from workspace paths
- Stage 1 validation ensures committed before cascading

**Safe** because Stage 1 blocks if uncommitted changes detected.

### 3. Auto-Merge Behavior

**Current**: Quickmerge always uses `--auto-merge` (even on branches)

**Correct** ✅ because:
- Branch PRs should auto-merge to main when CI passes
- Forces everything toward main (good)
- Prevents branch accumulation

**User Concern**: "Quick merge is still auto much all the time, even on the branches. It sets up just still trying to get everything to the main, it's just forcing itself to not be on the main."

**Answer**: Yes, exactly right! Branch isolation is temporary:
```
Branch workflow:
1. Make changes on "my-feature" branch
2. Create PR from "my-feature" → main
3. Auto-merge when CI passes
4. Branch deleted

Goal: Merge to main ASAP, but with safety (all deps on same branch during dev)
```

---

## PR Watcher Implementation

### Requirement (from user)
- Feeds back in PR as comments
- Separate context so agents can read it
- Rich output explaining issues
- **NOT** dump logs to GCS (keep in PR comments)

### Implementation Plan

**`.github/workflows/pr-watcher.yml`**:
```yaml
name: PR Quality Watcher

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  llm-watcher:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout PR
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Analyze with LLM
        env:
          CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
        run: |
          # Gather context
          PR_DIFF=$(git diff origin/main...HEAD)
          PR_COMMITS=$(git log origin/main..HEAD --oneline)
          
          # Create analysis prompt
          cat > /tmp/pr-analysis-prompt.txt <<EOF
          Analyze this PR for:
          
          1. Was quickmerge used? (check commit message pattern)
          2. Are dependencies properly aligned?
          3. Do quality gates pass?
          4. Any Codex violations?
          5. Security issues?
          
          PR Info:
          - Title: ${{ github.event.pull_request.title }}
          - Commits:
          $PR_COMMITS
          
          Diff Summary:
          $PR_DIFF
          
          Return:
          ✅ APPROVED or ❌ ISSUES FOUND
          
          If issues, provide:
          - Clear explanation
          - Fix suggestions
          - Example commands
          EOF
          
          # Run Cursor agent (or Claude/Aider fallback)
          ANALYSIS=$(bash .cursor/scripts/llm-agent-wrapper.sh /tmp/pr-analysis-prompt.txt)
          
          # Post as PR comment
          gh pr comment ${{ github.event.pull_request.number }} \
            --body "## 🤖 Automated PR Analysis

          $ANALYSIS
          
          ---
          *Generated by Cursor agent - see .github/workflows/pr-watcher.yml*"
          
          # Block if issues found
          if echo "$ANALYSIS" | grep -q "❌ ISSUES FOUND"; then
            echo "PR has issues - blocking merge"
            exit 1
          fi
```

**Benefits**:
- ✅ Comment-based feedback (readable by agents)
- ✅ Rich context + fix suggestions
- ✅ Blocks merge if issues detected
- ✅ No GCS logs needed (self-contained)

---

## Cursor Rules Update Required

### `.cursor/rules/ci-cd-workflow.mdc`

```markdown
# CI/CD Workflow Rules

## Canonical Sources

### Dependency Matrix
ALWAYS consult canonical dependency matrix:
.cursor/plans/code_optimizations_and_ci_cd_alignment/DEPENDENCY-MATRIX-CANONICAL.json

When asked about dependencies, reference this file FIRST.

### Master Plan
Implementation guide:
.cursor/plans/code_optimizations_and_ci_cd_alignment/00-MASTER-CICD-PLAN.md

## Mandatory Workflow

### ALWAYS Use Quickmerge
NEVER run quality gates standalone. ALWAYS use:
```bash
bash scripts/quickmerge.sh "commit message"
```

### Check PR Comments
When working on PRs, ALWAYS check for PR watcher comments:
```bash
gh pr view --comments
```

Parse watcher feedback and apply suggested fixes.

## Dependency Changes

If changing dependencies:
```bash
bash scripts/quickmerge.sh "msg" --dep-branch "my-feature"
```

This cascades to all dependencies automatically.
```

---

## Codex Documentation Update Required

### `unified-trading-codex/06-coding-standards/cicd-architecture.md`

Create new doc:
```markdown
# CI/CD Architecture

## Overview

Production-grade CI/CD with zero-surprise merges.

## Canonical Dependency Matrix

**Location**: `.cursor/plans/code_optimizations_and_ci_cd_alignment/DEPENDENCY-MATRIX-CANONICAL.json`

**Purpose**: Single source of truth for all 32 repo dependencies.

**Maintained by**: Manual updates when repos added/restructured

**Used by**:
- Quickmerge cascade logic
- GitHub Actions
- Cloud Build
- Documentation
- Cursor agents

## Workflow

See master plan for complete details:
`.cursor/plans/code_optimizations_and_ci_cd_alignment/00-MASTER-CICD-PLAN.md`

### Quick Reference

**Normal workflow** (no dependency changes):
```bash
bash scripts/quickmerge.sh "feat: new feature"
# Uses main branch for everything
```

**Multi-repo feature** (dependencies changed):
```bash
bash scripts/quickmerge.sh "feat: big refactor" --dep-branch "refactor-2024"
# Cascades to all dependencies
# Creates "refactor-2024" branch across entire tree
```

## PR Watcher

All PRs analyzed by LLM agent. Check comments for feedback:
```bash
gh pr view --comments
```

Agent checks:
1. Quickmerge used?
2. Dependencies aligned?
3. Quality gates pass?
4. Codex compliance?
5. Security issues?

**Auto-merge blocked** if issues found.
```

---

## Recommendation: Documentation vs Implementation

### Delete After Consolidation
1. `BRANCH-BASED-DEPENDENCIES.md` ❌
2. `CASCADING-DEPENDENCY-QUICKMERGE.md` ❌
3. `DIFFERENTIAL-BASED-BRANCHING.md` ❌
4. `QUICKMERGE-FLOW-DIAGRAM.md` ❌

### Archive (Keep for History)
1. `03-cicd-alignment.md` → `ARCHIVE-03-cicd-alignment.md`
2. `03-cicd-alignment-watcher-addon.md` → `ARCHIVE-watcher-addon.md`

### Active Documents
1. **`00-MASTER-CICD-PLAN.md`** - Implementation guide
2. **`DEPENDENCY-MATRIX-CANONICAL.json`** - Dependency source of truth
3. **`PILOT-UCS.md`** - Testing guide (delete after pilot succeeds)
4. **`00-CONSOLIDATION-SUMMARY.md`** - This file (reference for decisions made)

---

## Next Steps

1. ✅ Canonical dependency matrix created
2. ⬜ Test cascade on instruments-service (5-level dependency)
3. ⬜ Implement PR watcher with comments
4. ⬜ Update Codex docs (`cicd-architecture.md`)
5. ⬜ Update Cursor rules (`.cursor/rules/ci-cd-workflow.mdc`)
6. ⬜ Delete redundant planning docs
7. ⬜ Archive original requirements docs

---

**Created**: 2026-02-24  
**Author**: Claude (Sonnet 4)  
**Purpose**: Consolidate 5+ planning docs into clear action plan
