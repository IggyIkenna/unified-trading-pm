---
doc_type: codex-ssot
title: Codex Section Registry
summary:
  "Canonical registry of all 14 codex section directories (00-13 + deleted 14 Testing Guides) — each row's purpose,
  update trigger, and correct-content examples, plus the table of content types that do NOT belong in any codex section."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [codex, governance, registry, ssot-audit, docspec]
related: [/codex/13-codex-governance/SSOT-BOUNDARY.md]
created: 2026-03-27
authoritative_for: [codex section registry (14-section directory map)]
referenced_by: [/codex/13-codex-governance/SSOT-BOUNDARY.md]
owner:
last_reviewed:
code_refs:
---

# Codex Section Registry

Canonical registry of all 14 codex sections. Update this when sections are renamed, repurposed, or content is
restructured.

| #   | Directory                | Name               | Purpose                                                                                                                                                                | Update Trigger                                      | Examples of correct content                                             |
| --- | ------------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------- |
| 00  | `00-getting-started/`    | Getting Started    | Onboarding guide and SSOT index for the entire workspace                                                                                                               | New repo added; SSOT location changes               | workspace-structure.md, SSOT-INDEX.md                                   |
| 01  | `01-domain/`             | Domain             | Business domain definitions: instruments, venues, asset classes, event taxonomy                                                                                        | New instrument class or venue type added            | instrument-spec.md, event-taxonomy.md                                   |
| 02  | `02-data-contracts/`     | Data Contracts     | API contract standards, schema evolution rules, versioning policy                                                                                                      | New contract pattern established                    | contract-standards.md, versioning-policy.md                             |
| 03  | `03-market-data/`        | Market Data        | Market data ingestion architecture, normalization standards, feed contracts                                                                                            | New data source type or normalization rule          | ingestion-spec.md, feed-normalization.md                                |
| 04  | `04-architecture/`       | Architecture       | System architecture: tier diagram, service topology, ADRs for cross-cutting decisions                                                                                  | New architectural pattern or cross-cutting decision | tier-and-import-architecture.md, ADRs                                   |
| 05  | `05-infrastructure/`     | Infrastructure     | Infrastructure standards: cloud setup, CI/CD design, workspace tooling architecture                                                                                    | New cloud resource type or CI/CD pattern            | cloud-agnostic-migration.md, ci-cd.md                                   |
| 06  | `06-coding-standards/`   | Coding Standards   | Code quality rules: naming, typing, imports, testing, quality gates                                                                                                    | New code quality rule or pattern established        | testing.md, quality-gates-template.sh, no-any-types.md                  |
| 07  | `07-security/`           | Security           | Security policies: auth standards, secret management, API security                                                                                                     | New security requirement or vulnerability class     | auth-standards.md, secret-management.md                                 |
| 08  | `08-services/`           | Services           | Per-service architecture documentation: contracts, boundaries, responsibilities                                                                                        | New service added or existing service restructured  | service-architecture-template.md                                        |
| 09  | `09-ml/`                 | Machine Learning   | ML system standards: feature engineering, model lifecycle, training pipeline                                                                                           | New ML pattern or model governance rule             | feature-spec.md, model-lifecycle.md                                     |
| 10  | `10-audit/`              | Audit              | Audit methodology, compliance checklists, production-readiness criteria                                                                                                | New audit criterion or compliance requirement       | audit-checklist.md, production-readiness-criteria.md                    |
| 11  | `11-project-management/` | Project Management | PM methodology standards, scope specs (epics), ADRs, domain reference YAMLs                                                                                            | New architecture decision; new domain scope defined | epics/, decisions/, service-registry.yaml, audit-remediation-program.md |
| 12  | `12-agent-workflow/`     | Agent Workflow     | Agent operating procedures: tasking, failure recovery, human review                                                                                                    | New agent capability or workflow pattern            | AGENT-TASKING-GUIDE.md, FAILURE_RECOVERY.md                             |
| 13  | `13-codex-governance/`   | Codex Governance   | Meta-governance: SSOT boundary rules, section registry, cross-reference standards                                                                                      | SSOT boundary dispute; new section added            | SSOT-BOUNDARY.md, SECTION-REGISTRY.md                                   |
| 14  | _(deleted 2026-03-03)_   | Testing Guides     | **Deleted.** Content relocated: 7-layer pipeline → `04-architecture/runtime-deployment-topology.md` (Mermaid source); CLI reference → `deployment-service/docs/cli.md` | —                                                   | —                                                                       |

## What does NOT belong in any codex section

| Content type                                                   | Where it belongs                                           |
| -------------------------------------------------------------- | ---------------------------------------------------------- |
| Active task lists, sprint planning                             | `unified-trading-pm/plans/active/`                         |
| Agent prompt files                                             | `unified-trading-pm/plans/cursor-plans/` or `plans/tasks/` |
| Copy-paste runbooks with commands                              | `unified-trading-pm/docs/runbooks/`                        |
| GitHub automation scripts                                      | `unified-trading-pm/github-integration/`                   |
| Workspace setup scripts                                        | `unified-trading-pm/scripts/workspace/`                    |
| Audit output artifacts (violation reports, coverage snapshots) | `unified-trading-pm/docs/audit/` or `plans/archive/`       |
| Personal handoff documents                                     | `unified-trading-pm/plans/archive/`                        |
| Dated roadmaps with % completion                               | `unified-trading-pm/plans/archive/`                        |
| Presentations and business decks                               | `unified-trading-pm/presentations/`                        |
