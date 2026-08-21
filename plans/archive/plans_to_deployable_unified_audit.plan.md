---
doc_type: plan
title: Plans to Deployable Unified Audit
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, system-integration-tests, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-05'
overview: Canonical workflow for Plans → Code → Tested → Deployable. Unifies PM Codex Drift Zero, Other Alignment, and deployment topology. Four-stage pipeline with Tested and Deployable gates. Supersedes pm_codex_drift_zero_architecture, other_alignment_plan, PM_CODEX_VS_OTHER_ALIGNMENT_DIFF.
todos:
- {id: phase-0-manifest-sync, content: 'Manifest sync (repository_dispatch); update version-bump workflows; remove broken manifest steps. GATE: workspace-manifest.json validates against JSON schema with zero errors; all repo entries have ci_status, quality_gate_status, coverage_pct, bypass_audit_path, testing_level, skipped_gates fields present; repository_dispatch event fires on PM push and reaches dependent workflows without error.', status: completed}
- {id: phase-0b-cleanup, content: 'Codex + PM cleanup; fix paths, merge archives, create SSOT indexes. GATE: no broken relative links in any active plans/active/ .plan.md file; plans/archive/ contains only superseded plans; 00-SSOT-INDEX.md lists all canonical docs.', status: completed}
- {id: phase-1-manifest-validation, content: JSON schema + topological validation for workspace-manifest.json, status: completed}
- {id: phase-2-active-plans, content: Create plans/active/INDEX.md; add index-completeness quality gate, status: completed}
- {id: phase-3-codex-merge-gate, content: Plan-incorporation validator; Codex CI clones PM; doc-only quality gates, status: completed}
- {id: phase-4-pm-triggers-codex, content: Codex sync-with-pm.yml (workflow_run on PM), status: completed}
- {id: phase-5-ci-clone, content: PM and services clone Codex (and PM) as siblings in CI, status: completed}
- {id: phase-6-per-repo-drift, content: run_validators.py --scope/--repo-type; add drift step to quality-gates.sh, status: completed}
- {id: phase-7-diff-checker, content: Refactor 02-run-diff-checker.py to use validators, status: completed}
- {id: phase-8-per-file-headers, content: 'DECISION: Approach A — validator only (no file headers). Implement run_validators.py --check-codex-refs which detects if a source file''s last-touched codex doc version is stale relative to the current codex version. No # codex-ref: comments added to files. GATE: run_validators.py --check-codex-refs exits 0 for all T0–T2 repos.', status: completed}
- {id: phase-9-tested-gate, content: Tested gate — quality gates + integration tests pass, status: completed}
- {id: phase-10-deployable-gate, content: 'Deployable gate — checklist complete (data availability, deployment, catalogue, gaps, recovery, security)', status: completed}
- {id: phase-11-audit, content: Audit — trading_system_audit_prompt.plan.md run; target A+, status: completed}
- {id: checklist-enhancements, content: 'Add the following items to all 19 deployment checklists (checklist.{service}.yaml): (1) data_availability: input/output GCS buckets exist and contain expected data for the service date range; (2) gap_filling: empty date gaps documented with reason and expected fill date; (3) recovery: recovery runbook path documented (e.g. docs/recovery.md); (4) security_audit_trail: AUTH_FAILURE, SECRET_ACCESSED, CONFIG_CHANGED events confirmed in Cloud Logging for at least one test run. GATE: all 19 checklist YAML files pass the updated checklist validator with zero missing sections.', status: completed}
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Plans → Code → Tested → Deployable: Unified Audit and Plan Alignment

**Status:** Canonical (supersedes pm_codex, other_alignment, PM_CODEX_VS_OTHER_ALIGNMENT_DIFF) **Created:** 2026-03-04
**Archived plans:** `plans/archive/` — pm_codex_drift_zero_architecture, other_alignment_plan,
PM_CODEX_VS_OTHER_ALIGNMENT_DIFF **Blockers:** See [INDEX.md](INDEX.md) § Blockers — API keys (Phase 3 venues),
background agents, phase1 completion.

---

## 1. Extended Pipeline: Plans → Code → Tested → Deployable

PM (plans, manifest) → Codex (specs) → Code (implemented) → **Tested** (quality gates + integration tests) →
**Deployable** (checklist complete, actually deploys)

| Stage      | Gate                                       |
| ---------- | ------------------------------------------ |
| Plans      | Manifest validation; plan incorporation    |
| Codex      | Codex merge gate                           |
| Code       | Per-repo drift (validators); quality gates |
| Tested     | quality-gates.sh; pytest; CI green         |
| Deployable | Checklist YAML; runtime-topology; audit    |

**Deployable** ≠ working code: data availability verified, deployment stages passed, data catalogue filled, recovery
documented, security audit trails. Audit prompt gives A+ when everything is documented and verifiable.

**Schema normalization checkpoint:** UAC is SSOT for canonical schemas; interfaces use UAC normalizers; no raw venue
data flows to services. Reference: schema normalization completion plan.

---

## 2. Deployment Topology and Checklists

**SSOT:** `deployment-service/configs/` — runtime-topology, RUNTIME_TOPOLOGY_DECISIONS.md,
RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg

**Checklist phases (1–7):** Repository foundation, Testing & Quality, Deployment Infrastructure, Local Validation,
Production Deployment, Documentation, Data Catalogue.

**Additional items:** data availability, filling empty gaps, recovery processes, security audit trails. Codex audit +
deployment-service configs + SSOT = lots to check against.

---

## 3. Audit Prompt

**SSOT:** `unified-trading-pm/plans/archive/trading_system_audit_prompt.plan.md`

---

## 4. Resolved Decisions

| #   | Decision                  | Resolution                                                                         |
| --- | ------------------------- | ---------------------------------------------------------------------------------- |
| 1   | Per-file headers          | TBD — see §5.1                                                                     |
| 2   | doc_version format        | `codex_repo_version` + `codex_file_that_triggered_agent_version` + `timestamp_UTC` |
| 3   | Enforcement strictness    | Depends on severity (features vs bug vs refactor)                                  |
| 4   | Retroactive headers       | Touched-only                                                                       |
| 5   | Checklist enhancements    | Yes — data availability, gaps, recovery, security                                  |
| 6   | Tested vs Deployable gate | Both                                                                               |

---

## 5. Per-File Headers (Clarification)

**Per-file headers** = Header comments at top of each file recording provenance: `# codex-ref:`, `# doc_version:`,
`# codex_version:`, `# last_modified:`. When Codex doc updates, `doc_version` bumps; stale code is detectable. Options:
A) Validator-only | B) Headers-only | C) Hybrid.

---

## 6. Consolidated Phase Order

Phase 0: Manifest sync | 0b: Cleanup | 1: Manifest validation | 2: Active plans index | 3: Codex merge gate | 4: PM
triggers Codex | 5: CI clone | 6: Per-repo drift | 7: Diff checker | 8: Per-file headers (optional) | 9: **Tested gate**
| 10: **Deployable gate** | 11: **Audit**

---

## 7. Next Steps

1. Add checklist items for data availability, gap-filling, recovery, security audit trail.
2. Define Tested gate — explicit criteria.
3. Define Deployable gate — checklist phases 1–7 + new items.
4. Wire audit prompt — run after Deployable.
5. Update trading_system_audit_prompt.plan.md — reference deployment-service.

---

## 8. Phase 9: Tested Gate

**Definition:** Code is Tested when quality gates and integration tests pass. CI is green.

### Explicit Criteria

| Criterion                                                  | Where                                             | Blocking        |
| ---------------------------------------------------------- | ------------------------------------------------- | --------------- |
| `bash scripts/quality-gates.sh --no-fix` passes            | Per repo                                          | Yes             |
| `pytest --collect-only -q` exits 0                         | Per repo                                          | Yes             |
| Unit tests pass (pytest tests/unit/)                       | Per repo                                          | Yes             |
| Layer 0: Contract alignment (AC↔UIC schemas)              | unified-api-contracts, unified-internal-contracts | Yes             |
| Layer 1: Schema robustness (test_schema_robustness.py)     | Per-service                                       | Yes             |
| Integration tests (if RUN_INTEGRATION=true)                | tests/integration/                                | Per-repo config |
| No blocking lint/type violations                           | ruff, basedpyright                                | Yes             |
| Required test files: test_event_logging.py, test_config.py | Services                                          | Yes             |

### Auditor pre-claim verification

Before claiming the Tested gate, run: `cd <repo> && uv run pytest --collect-only -q`. Collection must exit 0 with no
import/path-deps errors. See pytest-collection-audit-readiness.mdc.

### Out of Scope (Post-Deploy)

- Layer 2: Infrastructure verification (GCP buckets, PubSub, IAM)
- Layer 3a: Smoke tests (system-integration-tests)
- Layer 3b: Full E2E (system-integration-tests)

---

## 9. Phase 10: Deployable Gate

**Definition:** Code is Deployable when checklist is complete. Data availability verified, deployment stages passed,
data catalogue filled, recovery documented, security audit trails.

### Explicit Criteria (Checklist Phases 1–7)

| Phase | Name                      | Key Items                                                    |
| ----- | ------------------------- | ------------------------------------------------------------ |
| 1     | Repository Foundation     | pyproject, uv.lock, UnifiedCloudConfig, Dockerfile, setup.sh |
| 2     | Testing & Quality         | Unit tests, quality gates pass, cloudbuild.yaml              |
| 3     | Deployment Infrastructure | sharding config, dependencies.yaml, terraform, buckets       |
| 4     | Local Validation          | Runs locally, schema, timestamp/date alignment               |
| 5     | Production Deployment     | Image build, deployment, data completeness                   |
| 6     | Documentation             | README, architecture, schema, GCS paths                      |
| 7     | Data Catalogue            | data-catalogue.yaml, pipeline dependency chain               |

### Additional Items (per canonical plan)

| Item                 | Description                                     |
| -------------------- | ----------------------------------------------- |
| Data availability    | Input/output buckets exist; data paths verified |
| Gap-filling          | Empty gaps documented; recovery process defined |
| Recovery             | Recovery processes documented                   |
| Security audit trail | Audit trail for security-relevant actions       |

### SSOT

- **Checklists:** deployment-service/configs/checklist.{service}.yaml
- **Topology (canonical SSOT):** unified-trading-pm/configs/runtime-topology.yaml
  (deployment-service/configs/runtime-topology.yaml is a partial local view only)
- **Decisions:** deployment-service/configs/RUNTIME_TOPOLOGY_DECISIONS.md

### Gate Order

Plans → Code → **Tested** → **Deployable** → Audit (A+)
