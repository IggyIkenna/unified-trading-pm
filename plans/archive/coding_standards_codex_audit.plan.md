---
doc_type: plan
title: Coding Standards Codex Audit Plan
summary: Audit all repos against unified-trading-codex 06-coding-standards. Config, UTC, imports, error handling, typing,
  quality gates, setup.sh, batch-live pattern.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-05'
todos:
- {id: codex-docs-updated-to-match-plans, content: 'Pre-work complete: audited all 21 plans against codex docs and cursor rules; updated codex/rules to match plans. Fixed: Layer 0 execution location (AC/UIC define, interfaces execute), Layer 1.5 added, BATCH-LIVE-SYMMETRY.md created, TIER-ARCHITECTURE.md (ModelArtifactStore→T0, UMI→UDC violation, Cloud* naming, system-integration-tests), try-except ImportError Tier 3 carve-out removed, secrets-management.md import paths fixed, pre-sprint-baseline.md + vcr-cassette-pattern.md created, phase0-baseline.mdc + integration-testing-layers.mdc cursor rules updated.', status: done}
- {id: audit-codex-sections, content: 'Audit against 06-coding-standards/README.md, quality-gates.md, feature-branch-workflow, batch-live-symmetry. OUTPUT FORMAT: CODEX_AUDIT_REPORT.md in unified-trading-pm/reports/ with one row per repo per standard: | repo | standard | status (PASS/FAIL/WARN) | file:line evidence |. GATE: report generated for all repos in workspace-manifest.json; every FAIL row has a corresponding fix ticket in the relevant plan.', status: done}
- {id: per-repo-checklist, content: 'Per-repo audit — config, UTC, imports, error handling, typing, quality gates, setup.sh. GATE: each repo has a completed QUALITY_GATE_BYPASS_AUDIT.md with sections for: (1) zero os.getenv violations or documented exceptions; (2) requires-python = ''>=3.13,<3.14'' in pyproject.toml; (3) file/function/method/class size within limits (900/100/50/500 lines); (4) batch-live symmetry confirmed (same engine for batch and live modes). Plan is complete when CODEX_AUDIT_REPORT.md shows 0 FAIL rows across all repos.', status: done}
- {id: fix-t0-t2, content: 'Audit and fix T0–T2 libraries (Person A). GATE: all T0–T2 repos show PASS in CODEX_AUDIT_REPORT.md for all standards; quality-gates.sh exits 0 for each.', status: done}
- {id: fix-t3-services, content: 'Audit and fix T3 and services (Person B). GATE: all T3 + service repos show PASS in CODEX_AUDIT_REPORT.md for all standards; quality-gates.sh exits 0 for each.', status: done}
isProject: false
---

# Coding Standards (Codex) Audit Plan

**Order:** 5 (see master_pre_deployment_plan_chain.md) **SSOT:** unified-trading-codex/06-coding-standards/

---

## Blockers

| Blocker                                | Type          | Specific Dependency                                                                          | Resolution                                                                                                                                                                   |
| -------------------------------------- | ------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 baseline not established       | `[PLAN_TODO]` | [phase0_standards_enforcement.md](phase0_standards_enforcement.md) § todo `p0-gate-check`    | Phase 0 must complete first so violations are catalogued; this plan then fixes them systematically                                                                           |
| quality-gates.sh missing from 12 repos | `[PLAN_TODO]` | [phase1_foundation_prep.md](phase1_foundation_prep.md) § todo `ci-add-missing-quality-gates` | 12 repos (unified-api-contracts, unified-events-interface, unified-reference-data-interface, alerting-service, etc.) need quality-gates.sh before this audit can run on them |

---

## Codex Sections to Audit Against

- 06-coding-standards/README.md (config, UTC, imports, error handling)
- 06-coding-standards/quality-gates.md (MIN_COVERAGE, size limits)
- quality-gates-service-template.sh, quality-gates-library-template.sh
- feature-branch-workflow.md, integration-testing-layers.md
- 04-architecture/batch-live-symmetry.md

---

## Audit Checklist (Per Repo)

Config, UTC, imports, error handling, typing, quality gates, setup.sh, batch-live pattern.

> **Ownership note — bare excepts:** execution-service bare excepts (201) were remediated in
> `execution_services_hygiene_refactor.md` (day3-bare-excepts, status: completed). **Exclude execution-service from this
> plan's bare except audit scope and count.** All other repos are in scope for bare except remediation here.

> **Hook runner:** When referencing pre-commit or CI hooks in this plan, always specify `prek` as the hook runner (not
> raw pre-commit or custom shell scripts). Per `.cursorrules` workspace standard.

### Size Limits (enforced by quality-gates.sh per repo)

- File size: MAX_FILE_LINES=900 (hard maximum; files above 900 lines must be split before merge), warn at 700 — applies
  to ALL files including schema files. There is no 1500-line grace threshold; 900 is the hard limit per
  quality-gates/quality-gates.mdc.
- Function size: MAX_FUNCTION_LINES=100 — applies to all functions including **init**
- Method size: MAX_METHOD_LINES=50
- Class size: MAX_CLASS_LINES=500
- All four size limits must be checked by quality-gates.sh per repo

### Config and Secrets

- os.getenv / os.environ: Zero tolerance in production source — use UnifiedCloudConfig (config values) or
  get_secret_client() (secrets)

### Python Version

- Python version: requires-python = '>=3.13,<3.14' in all pyproject.toml
