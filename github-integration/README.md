# GitHub Integration Scripts

**📖 READ THIS FIRST:** [GITHUB_INTEGRATION_ROADMAP.md](GITHUB_INTEGRATION_ROADMAP.md)

The roadmap explains the 7-stage maturity model, clarifies what appears as "duplication" (it's not), and provides the
complete script reference.

---

## Quick Navigation

### 🚀 Getting Started

**New to these scripts?** Start here:

1. Read [GITHUB_INTEGRATION_ROADMAP.md](GITHUB_INTEGRATION_ROADMAP.md) — Understanding the progression model
2. Check which **stage** your work fits into (0-6)
3. Use the decision guide below to find the right script

### 📊 Current Status

- **Stage 0 (Baseline):** 95% complete
- **Stage 1 (COD Standards):** 100% complete ✅
- **Stage 2 (COD Line Count):** Next up
- **Stage 3-6:** Future

---

## Script Decision Guide

### "What script do I use for...?"

| Need                                            | Script                           | Stage |
| ----------------------------------------------- | -------------------------------- | ----- |
| Check code compliance (imports, config, errors) | `run-diff-checker.py`            | 0     |
| Check service structure (files, directories)    | `check-service-compliance.py`    | 0     |
| Organize CODs into project (one-time setup)     | `setup-cod-project.py`           | 1     |
| Daily COD management (count, search, label)     | `manage-cods.sh`                 | 1     |
| Sync all labels from label-schema.yaml          | `sync-labels.py`                 | 0     |
| Create service-level epics with hierarchy       | `create-service-epics.py`        | 0     |
| Fix sub-issue links after rate limit            | `relink-sub-issues.py`           | 0     |
| Sync issues to projects                         | `sync-project-items.py`          | 0     |
| Auto-fix one issue with Cursor Agent            | `auto-fix-issue.sh`              | 0     |
| Batch fix multiple issues                       | `batch-fix.sh`                   | 0     |
| Close fixed issue                               | `close-fixed-issue.sh`           | 0     |
| Reset project (full wipe and recreate)          | `delete-and-recreate-project.sh` | Maint |
| Clear project items (keep structure)            | `wipe-and-regenerate-project.sh` | Maint |

---

## Documentation Index

### Essential Reading (Start Here)

1. **[GITHUB_INTEGRATION_ROADMAP.md](GITHUB_INTEGRATION_ROADMAP.md)** ⭐
   - 7-stage maturity model
   - Complete script reference
   - Clears up audit confusion
   - Progression strategy

2. **[COD-PROJECT-SETUP.md](COD-PROJECT-SETUP.md)**
   - Stage 1 setup guide
   - COD project automation
   - Troubleshooting

### Reference Docs

- `run-diff-checker.py` docstring — Code compliance checking
- `check-service-compliance.py` docstring — Structural compliance
- `label-schema.yaml` — Master label definitions

### Current Workflow Documentation

**Canonical:** [E2E_WORKFLOW_UNIFIED.md](../../00-getting-started/E2E_WORKFLOW_UNIFIED.md) — Unified workflow (current +
future vision)

**Historical Docs (Archived):**

- `E2E_WORKFLOW_GUIDE.md` — Original workflow (v1.0) - Now archived with redirect
- `MASTER_WORKFLOW.md` — Iteration (v1.5) - Archived
- `UNIFIED_WORKFLOW_FINAL.md` — Previous workflow (v2.0) - Archived with redirect to E2E_WORKFLOW_UNIFIED.md

**Visual Diagrams:**

- [WORKFLOW_DIAGRAM.md](./WORKFLOW_DIAGRAM.md) — 9-stage maturity model
- [CLEAN_WORKFLOW_DIAGRAMS.md](../../12-presentations/CLEAN_WORKFLOW_DIAGRAMS.md) — Visual workflow diagrams

---

## Maturity Stage Quick Reference

### Stage 0: Baseline (Foundation)

**Goal:** Solid infrastructure before automation.

- Dependencies standardized
- Quality gates working
- Builds reliable
- Auth configured

**Scripts:** `run-diff-checker.py`, `check-service-compliance.py`

---

### Stage 1: COD Standards (Organization)

**Goal:** Separate architectural pivots from work items.

- CODs organized in dedicated project
- Main projects show only work items
- Design decisions centralized

**Scripts:** `setup-cod-project.py`, `manage-cods.sh`

**Status:** ✅ Complete

---

### Stage 2: COD Line Count (Quality)

**Goal:** Enforce file size limits, split large files.

- All files <1500 lines
- SRP violations tracked
- Automated monitoring

**Scripts:** `check-file-size-cods.py` (to be created)

**Status:** Next up

---

### Stage 3: Event Logging (Observability)

**Goal:** 11-event lifecycle logging in all services.

**Scripts:** `check-event-logging.py` (to be created)

**Status:** Future

---

### Stage 4: Missing Features (Completeness)

**Goal:** Feature parity across services.

**Scripts:** `check-feature-completeness.py` (to be created)

**Status:** Blocked on architecture docs

---

### Stage 5: New Services (Scaling)

**Goal:** New services 100% compliant from day 1.

**Scripts:** `scaffold-new-service.py`, `validate-new-service.py` (to be created)

**Status:** Blocked on Stage 4

---

### Stage 6: Hardening (Safety)

**Goal:** Safe automation without prod risk.

**Scripts:** `verify-env-isolation.py`, `agent-safety-wrapper.sh` (to be created)

**Status:** Blocked on dev/prod separation

---

## Common Questions

### Q: Why so many scripts?

**A:** Not "many scripts" - **progressive tooling**. Each stage needs different checks. You use scripts sequentially as
you mature, not all at once.

---

### Q: Why not consolidate everything into one mega-script?

**A:** Separation of concerns. Each script has one job:

- ✅ Easier to maintain
- ✅ Easier to test
- ✅ Easier to understand
- ✅ Composable (combine as needed)

---

### Q: Isn't diff-checker and service-compliance duplication?

**A:** No - **complementary:**

- diff-checker: Code patterns (how you write code)
- service-compliance: Structure (what files exist)

Different dimensions. Both needed.

---

### Q: Should we batch more operations?

**A:** We batch where possible:

- ✅ Org-wide searches (97% fewer API calls)
- ❌ Label creation (GitHub limitation)
- ❌ Issue editing (GitHub limitation)
- 🤔 Could use GraphQL for batching (complex, future optimization)

---

### Q: When should we reorganize the directory structure?

**A:** During **Stage 2 refactoring**:

- Create shared utilities
- Organize scripts by stage
- Archive completed migrations
- Extract common patterns

**Not now** - focus on progression, not organization.

---

## Contact & Support

**Questions about this roadmap?**

- See [GITHUB_INTEGRATION_ROADMAP.md](GITHUB_INTEGRATION_ROADMAP.md) for detailed explanations
- Check script docstrings for usage details

**Found an issue?**

- Create GitHub issue in unified-trading-codex
- Label: `enhancement` or `bug`
- Reference this document

---

**Last Updated:** 2026-02-13  
**Canonical Reference:** [GITHUB_INTEGRATION_ROADMAP.md](GITHUB_INTEGRATION_ROADMAP.md)
