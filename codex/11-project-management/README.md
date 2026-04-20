---
scope: [engineer, admin]
---

# 11 — Project Management

PM methodology standards, scope specifications (epics), architecture decision records, and domain reference data.

**This section contains:** durable standards, ADRs, and scope specs. **For active task tracking:**
`unified-trading-pm/plans/cursor-plans/consolidated_remaining_work.plan.md` **For active plans and roadmaps:**
`unified-trading-pm/plans/`

Boundary rule: See `unified-trading-codex/13-codex-governance/SSOT-BOUNDARY.md`

---

## Active Epics (Scope Specifications)

| File                                         | Purpose                                                |
| -------------------------------------------- | ------------------------------------------------------ |
| `epics/data-io-production-readiness-epic.md` | Data I/O production readiness scope + success criteria |

---

## Architecture Decision Records

| File                                         | Decision                                 |
| -------------------------------------------- | ---------------------------------------- |
| `decisions/config-consolidation-option-b.md` | Config consolidation — Option B selected |

---

## PM Methodology Standards

| File                              | Purpose                                                                                      |
| --------------------------------- | -------------------------------------------------------------------------------------------- |
| `audit-remediation-program.md`    | Audit backlog lanes, status lifecycle, owner bootstrap rules                                 |
| `dual-cloud-cost-ops-playbook.md` | GCP/AWS dual-cloud readiness gates, rollback tagging requirements                            |
| `codex-delta-canonical-brief.md`  | PM operating model: lifecycle model, delivery flow, decision log                             |
| `architecture-constraints.md`     | Locked architectural decisions (exchange boundary, risk stack, sign conventions, DR targets) |

---

## Domain Reference (Evergreen)

| File                               | Purpose                                                                             |
| ---------------------------------- | ----------------------------------------------------------------------------------- |
| `service-registry.yaml`            | Domain coverage: venue support, asset classes, infra paths, credentials per service |
| `venue-support-matrix.yaml`        | Service × venue support status (full / batch-only / live-only / planned)            |
| `mvp-universe.yaml`                | MVP instrument scope across CEFI / DEFI / TRADFI / SPORTS                           |
| `project-request-card-template.md` | Template for normalizing incoming project requests                                  |

---

## Archive

`archive/` contains:

- Completed epics (scope history): exchange-interface, market-data-infrastructure, sports-integration,
  post-trade-and-execution, unified-libraries-refactor
- Point-in-time snapshots: roadmaps, priority matrices, coverage checklists, violations reports
