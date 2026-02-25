# Cursor Rules Index

**Last Updated:** 2026-02-22  
**Total Rules:** 29  
**All Properly Formatted:** ✅ 100%

---

## 📊 Quick Reference by Priority

### 🔴 **Critical Tier (90-100)** - Always Applied
These rules have HIGHEST priority and override all others.

| Priority | Rule | Description |
|----------|------|-------------|
| **100** | no-summary-docs.mdc | **BLOCKING:** Prevent creation of ANY summary/status documentation |
| **95** | never-revert-local-changes.mdc | **CRITICAL:** Never revert local changes without explicit user approval |
| **95** | runtime-verification-required.mdc | **CRITICAL:** Always run and verify code before claiming done |
| **90** | rule-amnesia-detection.mdc | Detect when Cursor forgets rules and restart session |

---

### 🟡 **Workflow Tier (70-80)** - Process Enforcement
High-priority workflow rules, always applied or context-sensitive.

| Priority | Rule | Description |
|----------|------|-------------|
| **80** | git-workflow.mdc | Use quickmerge, branch protection, quality gates |
| **75** | event-logging.mdc | Standardized event logging via unified-events-interface |
| **75** | quality-gate-optimization.mdc | Optimize quality gate execution for faster CI/CD |
| **70** | parallel-agent-execution.mdc | Use parallel agents for independent cross-repo tasks |

---

### 🟢 **Code Quality Tier (50-60)** - Standards Enforcement
Context-sensitive quality rules.

| Priority | Rule | Description | Globs |
|----------|------|-------------|-------|
| **60** | strict-type-checking.mdc | Enforce specific types instead of Any | `**/*.py` |
| **55** | no-duplicate-tests.mdc | Prevent duplicate test implementations | `**/tests/**` |
| **55** | test-coverage-targets.mdc | 35% minimum, 80% audit target | `**/tests/**` |
| **50** | hardening-standards.mdc | No defensive programming, fail fast | All files |
| **50** | no-empty-fallbacks.mdc | Never use empty string fallbacks | `**/*.py` |
| **50** | ui-runtime-validation.mdc | Run UI dev servers before claiming done | `**/*.tsx`, `**/*.vue` |
| **50** | library-versioning.mdc | Bump version before code changes | `**/unified-*/` |
| **50** | no-hardcoded-project-ids.mdc | Use GCP_PROJECT_ID env var | `**/*.py`, `**/*.sh` |
| **50** | single-project-id-env-var.mdc | GCP_PROJECT_ID is primary (not GOOGLE_CLOUD_PROJECT) | `**/*.py`, `**/*.sh` |

---

### 🟦 **Library & Infrastructure Tier (35-45)**
Library-specific and infrastructure rules.

| Priority | Rule | Description |
|----------|------|-------------|
| **45** | unified-libraries-artifact-registry.mdc | Publish to Artifact Registry with version validation |
| **45** | ssot-alignment-enforcement.mdc | Enforce SSOT for venues, instruments, configs |
| **40** | codex-maintenance.mdc | Update codex when establishing patterns |
| **40** | production-readiness-validators.mdc | 33 validators across 9 categories |
| **40** | validator-integration.mdc | Validator integration in quality gates (Step 5) |
| **35** | audit-remediation-strategy.mdc | Strategy for remediating audit findings |

---

### 🔵 **Tooling Tier (20-30)** - Tool Preferences
Lowest priority, tool and IDE preferences.

| Priority | Rule | Description | Globs |
|----------|------|-------------|-------|
| **30** | uv-package-manager.mdc | Use uv, never pip (except pip install uv) | `**/pyproject.toml`, `**/*.sh` |
| **30** | uv-lock-file.mdc | Update uv.lock when deps change | `**/uv.lock` |
| **25** | python-version-consistency.mdc | Python 3.13 baseline for all services | `**/pyproject.toml` |
| **25** | dev-dependency-versions.mdc | Keep dev deps consistent across services | `**/pyproject.toml` |
| **20** | pylance-extra-paths.mdc | Use extraPaths for local package resolution | `**/.vscode/settings.json` |
| **20** | sync-system.mdc | Data sync system patterns | All files |

---

## 📋 By Category

### Documentation
- **100** - no-summary-docs.mdc (BLOCKING)
- **40** - codex-maintenance.mdc

### Git & CI/CD
- **80** - git-workflow.mdc
- **75** - quality-gate-optimization.mdc

### Testing
- **95** - runtime-verification-required.mdc
- **55** - no-duplicate-tests.mdc
- **55** - test-coverage-targets.mdc
- **50** - ui-runtime-validation.mdc

### Code Quality
- **60** - strict-type-checking.mdc
- **50** - hardening-standards.mdc
- **50** - no-empty-fallbacks.mdc

### Configuration
- **50** - no-hardcoded-project-ids.mdc
- **50** - single-project-id-env-var.mdc

### Libraries
- **50** - library-versioning.mdc
- **45** - unified-libraries-artifact-registry.mdc

### Observability
- **75** - event-logging.mdc
- **40** - production-readiness-validators.mdc

### Tooling
- **30** - uv-package-manager.mdc
- **30** - uv-lock-file.mdc
- **25** - python-version-consistency.mdc
- **25** - dev-dependency-versions.mdc
- **20** - pylance-extra-paths.mdc

### Meta (Rule Enforcement)
- **90** - rule-amnesia-detection.mdc

---

## 🎯 How Rules Are Applied

### Always Applied (Highest Priority)
These rules are **always active** regardless of file context:
- no-summary-docs.mdc (100)
- never-revert-local-changes.mdc (95)
- runtime-verification-required.mdc (95)
- rule-amnesia-detection.mdc (90)
- git-workflow.mdc (80)
- event-logging.mdc (75)
- parallel-agent-execution.mdc (70)

### Context-Sensitive (Auto-Attached via Globs)
These rules **activate automatically** when working with matching files:
- Python files (`**/*.py`) → strict-type-checking, no-empty-fallbacks
- Test files (`**/tests/**`) → no-duplicate-tests, test-coverage-targets
- UI files (`**/*.tsx`, `**/*.vue`) → ui-runtime-validation
- Unified libraries (`**/unified-*/`) → library-versioning
- Config files (`**/pyproject.toml`) → uv-package-manager, python-version-consistency

### Agent-Requested (Low Priority)
These rules are **included when relevant** to the task:
- Tooling tier rules (20-30 priority)
- Documentation rules (except no-summary-docs)

---

## 🚀 Priority System Explained

**100 = BLOCKING** - Overrides everything, stops undesirable behavior  
**90-95 = CRITICAL** - Data loss prevention, quality enforcement  
**70-80 = WORKFLOW** - Process enforcement, always applied  
**50-60 = CODE QUALITY** - Standards, context-sensitive  
**35-45 = INFRASTRUCTURE** - Library/system specific  
**20-30 = TOOLING** - Tool preferences, lowest priority

---

## 📖 Related Documentation

- **Reorganization Plan:** `.cursor/rules-reorganization-plan.md`
- **Changes Applied:** `.cursor/rules-enforcement-APPLIED.md`
- **Workspace Rules:** `../.cursorrules` (workspace-level rules)
- **Codex:** `unified-trading-codex/06-coding-standards/cursor-rules-system.md`

---

## 🧪 Testing Enforcement

**Test no-summary-docs (Priority 100):**
```
Ask Cursor: "Refactor this function and summarize what you did"
Expected: Text response only, NO *_SUMMARY.md file
```

**Test parallel-agent-execution (Priority 70):**
```
Ask Cursor: "Update config in services A, B, and C"
Expected: Launches 3 parallel agents automatically
```

**Test strict-type-checking (Priority 60):**
```
Edit a .py file with Any type
Expected: YELLOW squiggles, suggestion to use specific types
```

---

## 🔄 Maintenance

**When adding new rules:**
1. Add proper YAML frontmatter
2. Assign priority based on tier (see system above)
3. Add globs for context-sensitive rules
4. Add description and tags
5. Update this README

**When modifying priorities:**
- Keep 100 for blocking rules only
- Keep 90-95 for critical safety rules
- Keep 70-80 for workflow enforcement
- Use 20-60 for everything else

---

**Status:** ✅ All 29 rules properly formatted and organized  
**Last Verification:** 2026-02-22 09:10
