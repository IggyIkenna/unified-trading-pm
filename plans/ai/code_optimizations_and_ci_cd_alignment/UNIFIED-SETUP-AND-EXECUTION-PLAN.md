# Unified Setup and Execution Plan

**Status**: Ready to Execute
**Created**: 2026-02-24
**Purpose**: Single canonical execution order combining CI/CD alignment, Master Plan, Audit roadmap, and API Contracts

**When in doubt**: Use this doc for execution order. Use linked source docs for implementation details.

---

## Canonical Source Hierarchy

| Topic | Source of Truth |
|-------|-----------------|
| CI/CD, quickmerge, branching, watcher | `00-MASTER-CICD-PLAN.md` + `00-CONSOLIDATION-SUMMARY.md` |
| Audit phases (code quality, tasks) | `AUDIT_TO_A_GRADE_ROADMAP/INDEPENDENT_AUDIT_REPORT_2026_02_24.md` + `PHASE_1_CRITICAL_FIXES.md` … `PHASE_4_EXCELLENCE.md` |
| CI/CD alignment (config, path deps) | `AUDIT_TO_A_GRADE_ROADMAP/ALIGNMENT_SUMMARY.md` |
| Cross-doc consistency | `AUDIT_TO_A_GRADE_ROADMAP/ALIGNMENT_CHECK.md` |
| API contracts validation | `AUDIT_TO_A_GRADE_ROADMAP/API_CONTRACTS_VALIDATION_PLAN.md` |

---

## Execution Order (Recommended)

### Track 1: CI/CD Phase 1 — Foundation (BLOCKING)

**Must complete before Master Plan.** Est. 2-4 hours.

| # | Task | Repo(s) | Reference |
|---|------|---------|-----------|
| 1 | Remove config fallback | risk-and-exposure-service | ALIGNMENT_SUMMARY §1 |
| 2 | Update UCS version constraints | pnl-attribution-service, alerting-system, unified-trading-deployment-v3 | ALIGNMENT_SUMMARY §2 |
| 3 | Add test-in-image pattern | alerting-system, pnl-attribution-service | ALIGNMENT_SUMMARY §3 |
| 4 | Fix path deps (clone to `../`) | risk-and-exposure-service, ml-inference-service | ALIGNMENT_SUMMARY §4 |
| 5 | Remove quality gates bypass | risk-and-exposure-service | ALIGNMENT_SUMMARY §5 |

**Verification**: `bash scripts/quality-gates.sh --no-fix --quick` passes in all modified repos.

---

### Track 2: Master CI/CD Plan — Advanced Workflow

**After Track 1.** Est. 8-12 hours.

| Stage | Feature | Reference |
|-------|---------|-----------|
| 1 | Dependency validation + cascading quickmerge | 00-MASTER-CICD-PLAN §Stage 1 |
| 2 | Pre-flight audit with LLM auto-fix | 00-MASTER-CICD-PLAN §Stage 2 |
| 3 | Docker quality gates (test-in-image) | 00-MASTER-CICD-PLAN §Stage 3 |
| 4 | Differential branching (`--dep-branch`) | 00-MASTER-CICD-PLAN §Stage 4 |
| 5 | Act simulation (GitHub Actions locally) | 00-MASTER-CICD-PLAN §Stage 5 |
| 6 | Inline agent failure handling | 00-MASTER-CICD-PLAN §Stage 6 |
| 7 | Push + PR with auto-merge | 00-MASTER-CICD-PLAN §Stage 7 |
| + | Dev environment support | 00-MASTER-CICD-PLAN §Dev Environment |
| + | PR watcher (LLM-enhanced) | 00-MASTER-CICD-PLAN §GitHub Actions |

**Pilot**: Start with unified-cloud-services (see PILOT-UCS.md).

---

### Track 3: Audit Phase 1 — Critical Repos

**Can run in parallel with Track 2.** Est. ~1.4 days (18h AI), ~1.4h wall-clock with 4 agents.

| Repo | Priority | Key Issues |
|------|----------|------------|
| unified-trading-deployment-v3 | P1-C1 | 7 files >1500 LOC, 87 broad excepts |
| unified-trade-execution-interface | P1-C2 | 43 failed tests |
| ml-training-service | P1-C3 | 30 failed tests, os.getenv |
| execution-services | P1-C4 | 1,196 prints, 142 broad excepts, 21% coverage |
| market-tick-data-handler | P1-C5 | 641 prints, 1574-line file |

**Reference**: `AUDIT_TO_A_GRADE_ROADMAP/PHASE_1_CRITICAL_FIXES.md`, `TASK_INDEX.md`

---

### Track 4: API Contracts Validation — Parallel

**Execute alongside Tracks 2-3.** Est. 4-6 hours with 2-3 agents.

| Phase | Task | Time |
|-------|------|------|
| 1 | Audit coverage (AC-1.1, AC-1.2) | 45m |
| 2 | Collect API responses (AC-2.1, AC-2.2) | 1.75h |
| 3 | Schema comparison & fix mismatches (AC-3.1, AC-3.2) | 3h |
| 4 | Add validation tests + quality gates (AC-4.1, AC-4.2) | 1.5h |
| 5 | Documentation + weekly validation (AC-5.1, AC-5.2) | 45m |

**Reference**: `AUDIT_TO_A_GRADE_ROADMAP/API_CONTRACTS_VALIDATION_PLAN.md`

---

## Standard Patterns (Universal)

### Path Dependencies

```toml
# pyproject.toml
[tool.uv.sources]
unified-cloud-services = { path = "../unified-cloud-services" }
unified-config-interface = { path = "../unified-config-interface" }
```

### GitHub Actions Checkout

```yaml
- name: Checkout dependencies
  env:
    GH_PAT: ${{ secrets.GH_PAT }}
  run: |
    if [ -n "$GH_PAT" ]; then
      git clone https://x-access-token:${GH_PAT}@github.com/.../unified-cloud-services.git ../unified-cloud-services
      # ... other deps to ../
    else
      echo "❌ GH_PAT not set" && exit 1
    fi
```

### Quality Gates (No Bypass)

```yaml
- name: Run quality gates
  run: bash scripts/quality-gates.sh --no-fix --quick
  # NO: || echo "⚠️ Quality gates need work"
```

### Config (No Fallbacks)

```python
# ✅
from unified_config_interface import UnifiedCloudConfig

class ServiceConfig(UnifiedCloudConfig):
    ...
```

---

## Phase Disambiguation

| "Phase 1" | Meaning |
|-----------|---------|
| **CI/CD Phase 1** | Critical alignment (config fallbacks, UCS versions, test-in-image) — ALIGNMENT_SUMMARY |
| **Audit Phase 1** | 5 critical repos (deployment-v3, order-interface, ml-training, execution-services, market-tick) — PHASE_1_CRITICAL_FIXES |

Use "CI/CD Phase 1" vs "Audit Phase 1" when both are discussed.

---

## Quick Start for Agents

1. **First run**: Execute Track 1 (CI/CD Phase 1) — 5 tasks, 5 repos.
2. **Then**: Start Track 2 (Master Plan) pilot with unified-cloud-services.
3. **Parallel**: Launch 4 agents for Track 3 (Audit Phase 1) — one per critical repo.
4. **Parallel**: Launch 2 agents for Track 4 (API Contracts) — Phase 1 + Phase 2.

---

## Checklist: Track 1 (CI/CD Phase 1)

- [ ] risk-and-exposure-service: Remove config fallback, fix path deps, remove quality gates bypass
- [ ] pnl-attribution-service: Update UCS >=1.5.0, add test-in-image
- [ ] alerting-system: Update UCS >=1.5.0, add test-in-image
- [ ] unified-trading-deployment-v3: Update UCS >=1.5.0
- [ ] ml-inference-service: Fix path deps (clone to `../`)

---

## References

- **Master Plan**: `00-MASTER-CICD-PLAN.md`
- **Consolidation**: `00-CONSOLIDATION-SUMMARY.md`
- **Dependency Matrix**: `DEPENDENCY-MATRIX-CANONICAL.json`
- **Alignment Summary**: `AUDIT_TO_A_GRADE_ROADMAP/ALIGNMENT_SUMMARY.md`
- **Alignment Check**: `AUDIT_TO_A_GRADE_ROADMAP/ALIGNMENT_CHECK.md`
- **Audit Phases**: `AUDIT_TO_A_GRADE_ROADMAP/PHASE_1_CRITICAL_FIXES.md` … `PHASE_4_EXCELLENCE.md`
- **API Contracts**: `AUDIT_TO_A_GRADE_ROADMAP/API_CONTRACTS_VALIDATION_PLAN.md`
- **Quick Start**: `AUDIT_TO_A_GRADE_ROADMAP/QUICK_START.md`
