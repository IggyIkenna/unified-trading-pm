# Task: CI/CD Phase 1 — Foundation (BLOCKING)

**Goal**: Complete the 5 critical CI/CD alignment tasks that block Master Plan implementation
**Method**: 3 fast sub-agents MANDATORY (Task tool)
**Time**: 2-4 hours
**Reference**: `.cursor/plans/code_optimizations_and_ci_cd_alignment/UNIFIED-SETUP-AND-EXECUTION-PLAN.md` Track 1

**⚠️ SUB-AGENTS REQUIRED**: Master orchestrates ONLY, never edits directly!

---

## Checklist (5 Tasks, 5 Repos)

| # | Task | Repo | Sub-Agent |
|---|------|------|-----------|
| 1 | Remove config fallback + fix path deps + remove quality gates bypass | risk-and-exposure-service | Agent 1 |
| 2 | Update UCS >=1.5.0 + add test-in-image | pnl-attribution-service, alerting-service | Agent 2 |
| 3 | Update UCS >=1.5.0 | unified-trading-deployment-v3 | Agent 3 |
| 4 | Fix path deps (clone to `../`) | ml-inference-service | Agent 1 |

---

## 🚀 PROMPT (Copy-Paste to Execute)

```
Execute task: CI/CD Phase 1 Foundation

⚠️ MANDATORY: Use Task tool to launch 3 sub-agents (model: fast, subagent_type: generalPurpose)

REFERENCE: .cursor/plans/code_optimizations_and_ci_cd_alignment/UNIFIED-SETUP-AND-EXECUTION-PLAN.md
DETAILS: AUDIT_TO_A_GRADE_ROADMAP/ALIGNMENT_SUMMARY.md §1-5

Sub-Agent 1 (risk-and-exposure-service):
- Remove config fallback: Replace try/except ImportError with direct `from unified_config_interface import UnifiedCloudConfig`
- Fix path deps: quality-gates.yml must clone to `../` not deps/ or ./
- Remove quality gates bypass: Remove `|| echo "⚠️ Quality gates need work"` from quality gates step

Sub-Agent 2 (pnl-attribution-service, alerting-service):
- Update pyproject.toml: unified-trading-services to >=1.5.0 or >=1.5.0,<2.0.0
- Add test-in-image pattern to cloudbuild.yaml (see ALIGNMENT_SUMMARY §3 for template)

Sub-Agent 3 (unified-trading-deployment-v3, ml-inference-service):
- deployment-v3: Update UCS version in pyproject.toml
- ml-inference-service: Fix quality-gates.yml checkout to use ../ for path deps

VERIFICATION: bash scripts/quality-gates.sh --no-fix --quick passes in each modified repo
CRITICAL: Use quickmerge for commits, never git push directly
```

---

## Context Files (Sub-Agents Must Read)

- `.cursor/plans/code_optimizations_and_ci_cd_alignment/UNIFIED-SETUP-AND-EXECUTION-PLAN.md`
- `AUDIT_TO_A_GRADE_ROADMAP/ALIGNMENT_SUMMARY.md` (sections 1-5)
- `.cursor/rules/path-dependency-ci.mdc`
- `.cursor/rules/no-empty-fallbacks.mdc`

---

## Safeguards

- NEVER: Skip tests, use pip install (use uv), add empty fallbacks
- MUST: Use quickmerge for commits, verify quality gates pass
- Master reviews all changes before approval
