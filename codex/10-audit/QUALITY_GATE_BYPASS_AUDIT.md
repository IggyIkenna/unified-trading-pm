---
doc_type: codex-ssot
title: Quality Gate Bypass Audit — Workspace Aggregate (SSOT)
summary:
  Codex-level SSOT for cross-repo quality-gate bypass tracking — defines what counts as a bypass (type:ignore / noqa /
  file-size / coverage exceptions), the per-repo QUALITY_GATE_BYPASS_AUDIT.md file structure, the suppression-category
  rubric (LIBRARY_STUB_MISSING and OVERLOAD_PATTERN acceptable; ARCHITECTURAL_VIOLATION never), and enforcement hooks.
  The Feb-27 scan counts are a historical snapshot.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: [quality-gates, audit, ssot-audit, ssot]
related: [/codex/06-coding-standards/quality-gates.md, /codex/10-audit/QUALITY_GATES_COVERAGE_REPORT.md]
created: 2026-03-27
authoritative_for: [quality-gate bypass audit methodology (cross-repo aggregate)]
referenced_by:
  [
    /codex/06-coding-standards/audit-remediation-guide.md,
    /codex/10-audit/FOUNDATIONAL-REPOS-AUDIT-2026-03-07.md,
    /codex/10-audit/QUALITY_GATES_COVERAGE_REPORT.md,
    codex/QUALITY_GATE_BYPASS_AUDIT.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Quality Gate Bypass Audit — Workspace Aggregate (SSOT)

This document is the **codex-level single source of truth** for cross-repo quality gate bypass tracking. Each repo
maintains its own `QUALITY_GATE_BYPASS_AUDIT.md` with per-file justifications; this document aggregates findings across
all repos and defines the audit methodology.

**Last updated:** 2026-02-27 (workspace-wide scan)

> **Historical snapshot (2026-02-27).** Suppression counts and hotspot repo lists reflect the Feb-27 state. The overall
> count (309 suppressions; 67 ARCHITECTURAL_VIOLATION) will have changed as QG enforcement tightened (STEP 5.x hardening
> through 2026-05). Per-repo `QUALITY_GATE_BYPASS_AUDIT.md` files are the current authoritative record.

---

## Methodology

### What Is a Quality Gate Bypass?

A bypass is any suppression that allows code to pass quality gates despite violating a standard:

- `# type: ignore[...]` — basedpyright suppression
- `# noqa: ...` — ruff lint suppression
- File size exceptions (files exceeding 900 lines)
- Coverage exceptions (repos below 70% for services, 35% for libraries)

### Rules

1. **Every bypass must be documented** in the repo's `QUALITY_GATE_BYPASS_AUDIT.md`
2. **No bypass without justification** — "TODO" or blank entries are non-compliant
3. **Architectural violations are never acceptable** — they must be fixed, not suppressed
4. **Library stub missing** and **overload pattern** suppressions are acceptable with documentation
5. **Periodic re-audit** — all repos scanned quarterly; findings aggregated here

### Per-Repo Audit File Structure

Every repo must have `QUALITY_GATE_BYPASS_AUDIT.md` at its root with these sections:

```markdown
# Quality Gate Bypass Audit — {repo-name}

## 2.1 File Size Exceptions

{table or "None."}

## 2.2 Ruff Exceptions

{table or "None."}

## 2.3 Basedpyright Exceptions

{table with: File | Line | Suppression | Category | Justification, or "None."}
```

Repos with active type suppressions should expand section 2.3 with categorized tables:

| Category                | Acceptable?              | Action                          |
| ----------------------- | ------------------------ | ------------------------------- |
| LIBRARY_STUB_MISSING    | Yes (with documentation) | Document library + reasoning    |
| OVERLOAD_PATTERN        | Yes (with documentation) | Document intentional overload   |
| ARCHITECTURAL_VIOLATION | **No**                   | Must fix — hiding real errors   |
| OPTIONAL_CHAINING       | Fix                      | Add None checks                 |
| UNION_NARROWING         | Fix                      | Narrow types explicitly         |
| UNKNOWN                 | Review                   | Categorize then fix or document |

### Enforcement

- `scripts/quality-gates.sh` Step 5 checks reference `QUALITY_GATE_BYPASS_AUDIT.md` for whitelisted exceptions
- Cursor rules (`strict-quality-gates.mdc`, `quality-gates-audit-factors.mdc`) enforce audit compliance
- Setup checklists (`service-setup-checklist.md`, `library-setup-checklist.md`) require creating this file

---

## Cross-Repo Summary (2026-02-27 Scan)

**Total suppressions found:** 309 across all repos

### Summary by Category

| Category                | Count | Action                            |
| ----------------------- | ----- | --------------------------------- |
| LIBRARY_STUB_MISSING    | 89    | Acceptable — no stubs available   |
| ARCHITECTURAL_VIOLATION | 67    | **Must fix** — hiding real errors |
| OPTIONAL_CHAINING       | 45    | Fix — add None checks             |
| UNION_NARROWING         | 38    | Fix — narrow types explicitly     |
| OVERLOAD_PATTERN        | 27    | Acceptable — intentional          |
| UNKNOWN                 | 43    | Review required                   |

### Hotspots (Repos with Most Suppressions)

| Repo                | Count | Primary Categories                               |
| ------------------- | ----- | ------------------------------------------------ |
| execution-service   | 78    | reportAny (params), pandas iloc, callback typing |
| deployment-service  | ~25   | arg-type (compute_type), var-annotated           |
| execution-service   | ~15   | union-attr (reward loading)                      |
| instruments-service | ~12   | assignment (pandas Series), arg-type             |
| strategy-service    | ~10   | arg-type (constructor patterns)                  |

### Suppressions Requiring Immediate Fix (ARCHITECTURAL_VIOLATION)

| Repo                  | File                                          | Line | Suppression                  | Issue                          |
| --------------------- | --------------------------------------------- | ---- | ---------------------------- | ------------------------------ |
| execution-service     | engine/orchestrator.py                        | 205  | `# type: ignore[reportAny]`  | params should be typed         |
| execution-service     | engine/execution/algorithms/almgren_chriss.py | 24   | `# type: ignore[reportAny]`  | params should be typed         |
| execution-service     | engine/execution/types.py                     | 24   | `# type: ignore[reportAny]`  | Any type in data structure     |
| execution-service     | utils/execution_cloud_service.py              | 78   | `# type: ignore[reportAny]`  | Any type in function signature |
| execution-service     | engine/modes/batch/data_source.py             | 30   | `# type: ignore[reportAny]`  | Any type from pandas           |
| execution-service     | engine/modes/live/data_sink.py                | 136  | `# type: ignore[reportAny]`  | Callback type not narrowed     |
| execution-service     | protocols/etherfi.py                          | 178  | `# type: ignore[union-attr]` | Union type not narrowed        |
| deployment-service    | deployment/monitoring.py                      | 160  | `# type: ignore[arg-type]`   | Incorrect argument type        |
| deployment-service    | deployment/worker_manager.py                  | 118  | `# type: ignore[arg-type]`   | Incorrect argument type        |
| instruments-service   | corporate_actions/adapter.py                  | 209  | `# type: ignore[assignment]` | Incorrect assignment type      |
| strategy-service      | models/position.py                            | 252  | `# type: ignore[arg-type]`   | Incorrect constructor args     |
| unified-domain-client | clients/**init**.py                           | 51   | `# type: ignore[arg-type]`   | Incorrect constructor args     |

### Acceptable Suppressions (LIBRARY_STUB_MISSING / OVERLOAD_PATTERN)

| Repo                     | File                        | Library               | Notes                             |
| ------------------------ | --------------------------- | --------------------- | --------------------------------- |
| execution-service        | data/defi_data_loader.py    | gcsfs                 | Third-party library without stubs |
| deployment-service       | deployment/orchestrator.py  | QuotaBrokerClient     | Optional import pattern           |
| unified-ml-interface     | model_registry.py           | handle_storage_errors | Decorator type inference          |
| unified-trading-services | core/performance_monitor.py | psutil                | Optional import fallback          |
| execution-service        | adapters/binance_ccxt.py    | ccxt                  | Third-party exchange library      |
| instruments-service      | adapters/binance.py         | API response          | JSON response typing              |
| unified-trading-services | auth/google_oauth.py        | FastAPI               | Middleware typing                 |
| unified-trading-services | observability/middleware.py | FastAPI               | Middleware typing                 |

### Suppressions to Review

| Repo                     | File                                       | Line | Category          |
| ------------------------ | ------------------------------------------ | ---- | ----------------- |
| execution-service        | utils/result.py                            | 28   | UNKNOWN           |
| deployment-service       | api/workers/auto_sync.py                   | 38   | OPTIONAL_CHAINING |
| execution-service        | data/config_builder.py                     | 306  | UNION_NARROWING   |
| execution-service        | engine/modes/batch/data_sink.py            | 43   | OPTIONAL_CHAINING |
| unified-domain-client    | clients/instruments.py                     | 132  | OPTIONAL_CHAINING |
| instruments-service      | engine/operations/instruments/scheduler.py | 76   | UNION_NARROWING   |
| strategy-service         | models/instruction.py                      | 185  | UNION_NARROWING   |
| ml-inference-service     | app/core/model_loader.py                   | 119  | OPTIONAL_CHAINING |
| unified-trading-services | persistence.py                             | 244  | UNKNOWN           |
| unified-trading-services | domain/validation.py                       | 418  | UNKNOWN           |

---

## Priority Actions

1. **HIGH PRIORITY:** Fix ARCHITECTURAL_VIOLATION cases (67 total) — these hide real type errors
   - Focus on `reportAny` suppressions in execution-service
   - Fix argument type mismatches in deployment services
   - Address union type narrowing in DeFi interfaces

2. **MEDIUM PRIORITY:** Review OPTIONAL_CHAINING cases (45 total) — add proper None checks
   - pandas DataFrame operations without type narrowing
   - Optional parameter handling without checks

3. **LOW PRIORITY:** Acceptable suppressions for third-party libraries (116 total)
   - Document reasoning for each acceptable case in per-repo audit files
   - Consider contributing stubs upstream where possible

---

## Tracking

| Metric                               | Value      |
| ------------------------------------ | ---------- |
| Audit date                           | 2026-02-27 |
| Total suppressions                   | 309        |
| Must fix (ARCHITECTURAL_VIOLATION)   | 67         |
| Acceptable (LIBRARY_STUB + OVERLOAD) | 116        |
| Review required                      | 126        |

---

## References

- Per-repo audit files: `{repo}/QUALITY_GATE_BYPASS_AUDIT.md`
- Quality gate templates: `06-coding-standards/quality-gates-service-template.sh`, `quality-gates-library-template.sh`
- Quality gate standards: `06-coding-standards/quality-gates.md`
- Type safety rules: `.cursor/rules/no-type-any-use-specific.mdc`, `strict-quality-gates.mdc`
- Setup checklists: `05-infrastructure/service-setup-checklist.md`, `library-setup-checklist.md`
