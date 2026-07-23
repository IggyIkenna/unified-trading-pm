---
scope: [engineer, admin]
last_reviewed: 2026-05-18
---

# 11 — Project Management

PM methodology standards, scope specifications (epics), architecture decision records, and domain reference data.

**This section contains:** durable standards, ADRs, and scope specs. **For active task tracking:**
`plans/active/master_to_live_defi_2026_05_23.md` (auto-inventory between `<!-- AUTO-INVENTORY-START/END -->` markers;
regenerate via `python3 scripts/plans/regenerate_active_plan_inventory.py`). SSOT for tracker:
`/codex/11-project-management/active-plan-inventory-tracker.md`. **For active plans and roadmaps:**
`unified-trading-pm/plans/`

Boundary rule: See `unified-trading-pm/codex/13-codex-governance/SSOT-BOUNDARY.md`

---

## Active Epics (19 epics in 5 tiers — everlasting)

Epics live under `plans/epics/<slug>.md` — **everlasting, no date suffix, no `estimate_*` fields**. Each owns one
persistent code surface and one assigned VM. Full SSOT for the epic flow:
[`../../plans/epics/README.md`](../../plans/epics/README.md) (this section's pointer:
[`epic-execution-with-sub-agents.md`](epic-execution-with-sub-agents.md)).

**Legacy YAML schema** at `codex/11-project-management/epics/epic-schema.yaml` was the pre-2026-05-21 readiness-pipeline
form. It is superseded by the markdown-primary model; the YAML files (`cefi-epic.yaml` / `defi-epic.yaml` / etc.) are
archaeology only — do NOT add new entries there.

### L0 — Asset-group ops (5 epics)

| Epic                                | Assigned VM     | Owns                                                                  |
| ----------------------------------- | --------------- | --------------------------------------------------------------------- |
| `plans/epics/defi_master.md`        | `vm-defi`       | DeFi adapters + on-chain execution + Copper custody + DeFi archetypes |
| `plans/epics/cefi_master.md`        | `vm-cefi`       | CeFi adapters + CCXT + CEFFU + perp hedge legs + CeFi archetypes      |
| `plans/epics/tradfi_master.md`      | `vm-tradfi`     | TradFi adapters + dated futures + TradFi archetypes                   |
| `plans/epics/sports_master.md`      | `vm-sports`     | Sports adapters + GBP settlement + sports archetypes                  |
| `plans/epics/predictions_master.md` | `vm-prediction` | Polymarket + Kalshi + binary-outcome archetypes                       |

### L1 — Data pipeline (4 epics)

| Epic                                    | Assigned VM            | Owns                                                                  |
| --------------------------------------- | ---------------------- | --------------------------------------------------------------------- |
| `plans/epics/instruments_master.md`     | `vm-cefi` (co-located) | instruments-service: IS reference + universe SSOT                     |
| `plans/epics/mtds_mdps_master.md`       | `vm-ml`                | MTDS adapters + MDPS candles + writegate + raw market data            |
| `plans/epics/features_and_ml_master.md` | `vm-ml`                | features-service (8 families) + ml-service (inference + training)     |
| `plans/epics/manifest_master.md`        | `vm-defi` (co-located) | Manifest schema v8 + honest absence + backfill + evolution discipline |

### L2 — Trading core (3 epics; co-located on one VM)

| Epic                                  | Assigned VM       | Owns                                                        |
| ------------------------------------- | ----------------- | ----------------------------------------------------------- |
| `plans/epics/strategy_master.md`      | `vm-trading-core` | strategy-service post-consolidation; 53 archetypes          |
| `plans/epics/execution_master.md`     | `vm-trading-core` | execution-service handlers + transfers + treasury + custody |
| `plans/epics/trading_agent_master.md` | `vm-trading-core` | trading-agent-service closed-loop allocator                 |

### L3 — Operator surfaces (2 epics; one VM)

| Epic                                                   | Assigned VM       | Owns                                                            |
| ------------------------------------------------------ | ----------------- | --------------------------------------------------------------- |
| `plans/epics/dart_and_promote_master.md`               | `vm-operator-ops` | DART + ManualTradeGateDialog + promote workflow + state machine |
| `plans/epics/deployment_and_user_management_master.md` | `vm-operator-ops` | deployment-api + deployment-ui + user-management                |

### L4 — Cross-cutting (4 epics; one VM)

| Epic                                                    | Assigned VM        | Owns                                                                                                       |
| ------------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------- |
| `plans/epics/infrastructure_master.md`                  | `vm-cross-cutting` | VMs + tarballs + per-tab worktrees + cloud + bootstrap                                                     |
| `plans/epics/observability_master.md`                   | `vm-cross-cutting` | alerting-service + monitoring + telemetry + 3am-auto-recovery                                              |
| `plans/epics/batch_live_symmetry_master.md`             | `vm-cross-cutting` | Per-service batch=live audit; reconciliation                                                               |
| `plans/epics/client_isolation_and_governance_master.md` | `vm-cross-cutting` | Per-client subprocess isolation + funds isolation + jurisdiction + share-class reconciliation + UAC schema |

### L5 — Meta (1 epic)

| Epic                                 | Assigned VM       | Owns                                                        |
| ------------------------------------ | ----------------- | ----------------------------------------------------------- |
| `plans/epics/orchestrator_master.md` | `vm-orchestrator` | agent-orchestrator multi-VM stack + planning VM + dashboard |

**Cutover master (NOT an epic)**: `plans/active/master_to_live_defi_2026_05_23.md` is a dated, one-shot plan tracking
May-23 cutover across all 19 epics. Archives after cutover. Not in `plans/epics/`.

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
