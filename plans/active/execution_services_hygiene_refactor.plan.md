---
name: Execution-Service Hygiene & Refactor
overview: |
  Dedicated plan for execution-service (EXEC). Addresses messy codebase, engine.py split by SRP,
  201 bare excepts, 67 ARCHITECTURAL_VIOLATION suppressions, thorough testing, and recovery of
  missing files post cloud issue on ikenna's Mac.

  References: phase3_service_hardening_integration.plan.md (T4 BATCH E — STR + EXEC + SVS).
  Execution order: Day 3 → Day 4.
todos:
  - id: day3-recover-files
    content: "DAY 3.1 — Recover missing files post cloud issue on ikenna's Mac: Identify files lost/corrupted; restore from git history, backup, or re-create; verify execution-service runs after recovery."
    status: pending
  - id: day3-engine-split
    content: "DAY 3.2 — engine.py split by SRP: engine.py 2826L exceeds 900L limit (06-coding-standards/file-splitting-guide.md). Extract by single responsibility — order lifecycle, matching logic, persistence, event emission. Target: no file >900 lines."
    status: pending
  - id: day3-bare-excepts
    content: "DAY 3.3 — Replace 201 bare excepts with proper handling: Use @handle_api_errors or specific exceptions; fail-loud for ImportError (25 remaining); document per-file bypasses in QUALITY_GATE_BYPASS_AUDIT.md only when audited."
    status: pending
  - id: day3-arch-violations
    content: "DAY 3.4 — Resolve 67 ARCHITECTURAL_VIOLATION suppressions: Fix root causes (service→service deps, tier violations); remove type: ignore where possible; ci-arch-violations-fix."
    status: pending
  - id: day3-cross-svc-deps
    content: "DAY 3.5 — exec-svc-cross-svc-deps: Remove execution-service→market-tick-data-service, →risk-and-exposure-service, →instruments-service. Extract shared schemas to unified-api-contracts or unified-internal-contracts."
    status: pending
  - id: day3-other-hygiene
    content: "DAY 3.6 — Other hygiene: qg-exec-services-smoke-import (get_storage_client from unified-cloud-interface); qg-central-element-test-code (test-project placeholder); qg-pip-audit-exec-services; qg-exec-services-codex-18."
    status: pending
  - id: day4-testing
    content: "DAY 4.1 — Thorough testing: Unit tests for split engine modules; schema robustness (test_schema_robustness.py); batch/live seam tests; p0-cdc-tests (consumer tests); ic-strategy-domain-event-validation."
    status: pending
  - id: day4-quality-gates
    content: "DAY 4.2 — Quality gates progression: quickmerge --lint-only → --unit-only → --qg-only → --quick → full (D5). All must pass before declare green."
    status: pending
  - id: day4-topology
    content: "DAY 4.3 — Topology wiring: topology-execution-order-lifecycle (full order lifecycle PubSub); topology-t1-execution-recon (execution T+1 recon)."
    status: pending
isProject: true
---

# Execution-Service Hygiene & Refactor Plan

**Scope:** execution-service (EXEC) — T4 BATCH E in phase3_service_hardening_integration.plan.md
**Execution order:** Day 3 → Day 4
**Reference:** [phase3_service_hardening_integration.plan.md](phase3_service_hardening_integration.plan.md) — t4e-strategy-execution todo

---

## 1. Hygiene and Refactor

| Item                    | Current | Target                                                    | Reference                                   |
| ----------------------- | ------- | --------------------------------------------------------- | ------------------------------------------- |
| engine.py               | 2826L   | Split by SRP, no file >900L                               | 06-coding-standards/file-splitting-guide.md |
| Bare excepts            | 201     | Proper handling (@handle_api_errors, specific exceptions) | quality-gates, strict-quality-gates.mdc     |
| ARCHITECTURAL_VIOLATION | 67      | Fix root causes, remove suppressions                      | ci-arch-violations-fix                      |
| ImportError fallbacks   | 25      | Fail-loud                                                 | quality-importerror-fallbacks               |
| Service→service deps    | 3       | 0 (extract to AC/UIC)                                     | exec-svc-cross-svc-deps                     |

### Phase 3 Execution-Service Todos (from t4e-strategy-execution)

- quality-large-file-splits — engine.py 2826L split by SRP
- vcr-enhanced-error-high-priority — 201 bare excepts
- quality-importerror-fallbacks — execution-service
- quality-type-ignore-arch-violations — 67 ARCHITECTURAL_VIOLATION suppressions
- ci-arch-violations-fix
- qg-exec-import-error-remaining — 25 except ImportError → fail-loud
- qg-exec-services-codex-18 — 18 codex violations
- qg-pip-audit-exec-services
- qg-exec-services-smoke-import — get_storage_client from unified-cloud-interface
- qg-central-element-test-code — central-element-323112 → test-project
- exec-svc-cross-svc-deps — remove market-tick-data-service, risk-and-exposure-service, instruments-service
- topology-execution-order-lifecycle — full order lifecycle PubSub
- topology-t1-execution-recon — execution T+1 recon

---

## 2. Thorough Testing

- **Unit tests** — All split engine modules; no regressions
- **Schema robustness** — tests/unit/test_schema_robustness.py per integration layers
- **Batch/live seam tests** — Mode-agnostic engine; 4 seams (data source, sink, persistence, trigger)
- **Consumer tests** — p0-cdc-tests for strategy+execution
- **Event validation** — ic-strategy-domain-event-validation (Pydantic model_validate)

---

## 3. Recover Missing Files (Post Cloud Issue)

**Context:** Files lost or corrupted on ikenna's Mac due to cloud sync issue.

**Steps:**

1. Identify missing/corrupted files (git status, diff, import errors)
2. Restore from git history (git checkout, git show)
3. If not in git: restore from backup or re-create from codex/specs
4. Verify python -c 'import execution_service' exits 0
5. Run quality-gates.sh after recovery

---

## 4. Day 3–4 Execution Order

| Day         | Task                                                     | Dependencies |
| ----------- | -------------------------------------------------------- | ------------ |
| **Day 3.1** | Recover missing files                                    | —            |
| **Day 3.2** | engine.py split by SRP                                   | 3.1          |
| **Day 3.3** | Replace 201 bare excepts                                 | 3.1          |
| **Day 3.4** | Resolve 67 ARCHITECTURAL_VIOLATION                       | 3.1          |
| **Day 3.5** | exec-svc-cross-svc-deps                                  | 3.1          |
| **Day 3.6** | Other hygiene (smoke, test-project, pip-audit, codex-18) | 3.1          |
| **Day 4.1** | Thorough testing                                         | 3.2–3.6      |
| **Day 4.2** | Quality gates progression → D5                           | 4.1          |
| **Day 4.3** | Topology wiring                                          | 4.2          |

---

## 5. Success Criteria

- [ ] No file >900 lines
- [ ] Zero bare excepts (or audited in QUALITY_GATE_BYPASS_AUDIT.md)
- [ ] Zero ARCHITECTURAL_VIOLATION suppressions (or documented)
- [ ] Zero service→service Python deps
- [ ] Full quickmerge with act simulation (D5) passes
- [ ] All missing files recovered and service runs
