---
scope: [engineer, admin]
last_reviewed: 2026-08-19
---

# 11 — Project Management

PM methodology standards, scope specifications (epics), architecture decision records, and domain reference data.

**This section contains:** durable standards, ADRs, and scope specs. **For active task tracking:**
`plans/archive/2026_07/master_to_live_defi_2026_05_23.md` (auto-inventory between `<!-- AUTO-INVENTORY-START/END -->`
markers; regenerate via `python3 scripts/plans/regenerate_active_plan_inventory.py`). SSOT for tracker:
`/codex/11-project-management/active-plan-inventory-tracker.md`. **For active plans and roadmaps:**
`unified-trading-pm/plans/`

Boundary rule: See `unified-trading-pm/codex/13-codex-governance/SSOT-BOUNDARY.md`

---

## Active Epics (22 epics in 6 tiers — everlasting)

Epics live under `plans/epics/<slug>.md` — **everlasting, no date suffix, no `estimate_*` fields**. Each owns one
persistent code surface. **Per-epic VM ownership is retired** (single-VM, role-based-dispatch architecture,
2026-06-27) — every epic's `assigned_vm` frontmatter reads `NA`; do not dispatch or match against it. Full SSOT for
the epic flow: [`../../plans/epics/README.md`](../../plans/epics/README.md) (this section's pointer:
[`epic-execution-with-sub-agents.md`](epic-execution-with-sub-agents.md)).

**Legacy YAML schema** at `codex/11-project-management/epics/epic-schema.yaml` was the pre-2026-05-21 readiness-pipeline
form. It is superseded by the markdown-primary model; the YAML files (`cefi-epic.yaml` / `defi-epic.yaml` / etc.) are
archaeology only — do NOT add new entries there.

Mirrored from `plans/epics/README.md`, regenerated 2026-08-19 post epic-taxonomy restructure (19→22: 5 folds —
`infrastructure_master`→`security_and_cross_cutting_master`, `escalation_and_disaster_recovery_master`→
`observability_master`, `dart_and_promote_master`+`trading_agent_master` folded into their consumers,
`global_ledger_pnl_attribution_master`→`strategy_master` — plus 2 new epics, `uac_master` and
`security_and_cross_cutting_master`, and `ci_master` split out of the old infra umbrella):

| #   | Tier | Epic slug                                | Owns                                                                                                         |
| --- | ---- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 1   | L0   | `defi_master`                            | DeFi adapters + on-chain execution + Copper custody + DeFi archetypes                                        |
| 2   | L0   | `cefi_master`                            | CeFi adapters + CCXT + CEFFU + perp hedge legs + CeFi archetypes                                             |
| 3   | L0   | `tradfi_master`                          | TradFi adapters + dated futures (Databento) + TradFi archetypes                                              |
| 4   | L0   | `sports_master`                          | Sports adapters + GBP settlement + sports archetypes                                                         |
| 5   | L0   | `predictions_master`                     | Polymarket + Kalshi + binary-outcome archetypes                                                              |
| 6   | L1   | `instruments_master`                     | instruments-service IS reference + universe SSOT                                                             |
| 7   | L1   | `mtds_mdps_master`                       | MTDS adapters + MDPS candles + writegate + raw market data                                                   |
| 8   | L1   | `features_and_ml_master`                 | features-service (8 families) + ml-service (inference + training)                                            |
| 9   | L1   | `manifest_master`                        | Manifest v9 + honest absence + backfill + evolution discipline                                               |
| 10  | L1   | `uac_master`                             | unified-api-contracts schema/registry SSOT + contract-governance correctness                                 |
| 11  | L2   | `strategy_master`                        | strategy-service; archetypes; portfolio_allocator; risk; position; PnL/HWM attribution                       |
| 12  | L2   | `execution_master`                       | execution-service handlers + transfers + treasury + custody + flash loan + matching engine                   |
| 13  | L3   | `deployment_and_user_management_master`  | deployment-api + deployment-ui + user-management surfaces                                                    |
| 14  | L4   | `ci_master`                              | GitHub Actions delivery pipeline, quickmerge/ship scripts, LDR→main promotion gate set                       |
| 15  | L4   | `observability_master`                   | alerting-service + monitoring/telemetry; Incident Gateway; kill-switch alerting; escalation + DR (folded in) |
| 16  | L4   | `batch_live_symmetry_master`             | Per-service batch=live audit; reconciliation                                                                 |
| 17  | L4   | `client_isolation_and_governance_master` | Per-client isolation + funds isolation + jurisdiction + share-class + UAC schema                             |
| 18  | L4   | `security_and_cross_cutting_master`      | Credentials/secrets + IAM + kill-switch authority; shard/data-status + deployment-build (infra, folded in)   |
| 19  | L4   | `system_readiness_master`                | Everything gating go-live readiness                                                                          |
| 20  | L5   | `orchestrator_master`                    | agent-orchestrator single-VM runtime + promote/live-flip gating machinery                                    |
| 21  | L5   | `agent_operating_framework_master`       | Agent dispatch (assigned_vm fail-closed matcher) + grep-native retrieval + role charters                     |
| 22  | L5   | `plan_hygiene_master`                    | Continuous plan-corpus hygiene: check scripts + hygiene sweep + codex-alignment audit                        |

**Cutover master (NOT an epic)**: `plans/archive/2026_07/master_to_live_defi_2026_05_23.md` is a dated, one-shot plan
tracking the May-23 live DeFi rollout across all 20 epics (the count at cutover time, pre-restructure). Archives after
cutover. Not in `plans/epics/`.

---

## Architecture Decision Records

| File                                                                | Decision                                                                                                                                                                     |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `decisions/adr-2026-04-25-category-and-asset-group-field-naming.md` | Deployment API: general deploy uses `category`, deploy-missing uses `asset_group`; GCS `category=` segments unchanged; global shard-dimension rename is a separate SSOT plan |

---

## PM Methodology Standards

| File                              | Purpose                                                                                                                           |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `audit-lifecycle.md`              | Audit lifecycle summary — 3-layer structure, archival rules, per-epic instruction co-creation rule; SSOT: `plans/audit/README.md` |
| `dual-cloud-cost-ops-playbook.md` | GCP/AWS dual-cloud readiness gates, rollback tagging requirements                                                                 |
| `codex-delta-canonical-brief.md`  | PM operating model: lifecycle model, delivery flow, decision log                                                                  |
| `architecture-constraints.md`     | Locked architectural decisions (exchange boundary, risk stack, sign conventions, DR targets)                                      |

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
