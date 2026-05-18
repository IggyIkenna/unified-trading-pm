---
scope: [engineer, admin]
last_reviewed: 2026-05-18
---

# 11 — Project Management

PM methodology standards, scope specifications (epics), architecture decision records, and domain reference data.

**This section contains:** durable standards, ADRs, and scope specs. **For active task tracking:**
`plans/active/master_to_live_defi_2026_05_23.md` (auto-inventory between `<!-- AUTO-INVENTORY-START/END -->` markers;
regenerate via `python3 scripts/plans/regenerate_active_plan_inventory.py`). SSOT for tracker:
`codex/11-project-management/active-plan-inventory-tracker.md`. **For active plans and roadmaps:**
`unified-trading-pm/plans/`

Boundary rule: See `unified-trading-pm/codex/13-codex-governance/SSOT-BOUNDARY.md`

---

## Active Epics (Scope Specifications)

Epics live under `plans/epics/` (YAML format, schema: `codex/11-project-management/epics/epic-schema.yaml`):

| File                                         | Purpose                                            |
| -------------------------------------------- | -------------------------------------------------- |
| `plans/epics/cefi_master_2026_05_07.md`      | CeFi master epic — perp + spot venues              |
| `plans/epics/defi-epic.yaml`                 | DeFi scope + success criteria                      |
| `plans/epics/tradfi_master_2026_05_07.md`    | TradFi instruments epic                            |
| `plans/epics/sports_master_2026_05_07.md`    | Sports data + strategy epic                        |
| `plans/epics/predictions_master_2026_05_07.md` | Predictions market epic                          |
| `plans/epics/infrastructure_master_2026_05_07.md` | Infrastructure + shard-isolation epic         |

---

## Architecture Decision Records

| File                                                                | Decision                                                                                                                                                                     |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `decisions/adr-2026-04-25-category-and-asset-group-field-naming.md` | Deployment API: general deploy uses `category`, deploy-missing uses `asset_group`; GCS `category=` segments unchanged; global shard-dimension rename is a separate SSOT plan |

---

## PM Methodology Standards

| File                              | Purpose                                                                                      |
| --------------------------------- | -------------------------------------------------------------------------------------------- |
| `dual-cloud-cost-ops-playbook.md` | GCP/AWS dual-cloud readiness gates, rollback tagging requirements                            |
| `codex-delta-canonical-brief.md`  | PM operating model: lifecycle model, delivery flow, decision log                             |
| `architecture-constraints.md`     | Locked architectural decisions (exchange boundary, risk stack, sign conventions, DR targets) |

---

## Domain Reference (Evergreen)

| File                        | Purpose                                                                             |
| --------------------------- | ----------------------------------------------------------------------------------- |
| `service-registry.yaml`     | Domain coverage: venue support, asset classes, infra paths, credentials per service |
| `venue-support-matrix.yaml` | Service × venue support status (full / batch-only / live-only / planned)            |
| `mvp-universe.yaml`         | MVP instrument scope across CEFI / DEFI / TRADFI / SPORTS                           |

---

## Archive

`archive/` contains:

- Completed epics (scope history): exchange-interface, market-data-infrastructure, sports-integration,
  post-trade-and-execution, unified-libraries-refactor
- Point-in-time snapshots: roadmaps, priority matrices, coverage checklists, violations reports
