---
name: codex-plan-audit-differential-2026-05-22
title: Codex ↔ Plan Differential Audit 2026-05-22
parent_epic: plan_hygiene_master
assigned_vm: vm-planning
priority: P1
status: active
estimate_class: research
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 10
created: 2026-05-22
last_updated: 2026-05-22
---

# Codex ↔ Plan Differential Audit 2026-05-22

## Context

Codex is the SSOT for "what MUST be true across all repos" — durable specs, patterns, ADRs, architecture definitions.
Plans are execution artifacts that track what's being built and what decisions have been made. Over time these diverge:

1. Plan ships a decision → codex not updated → next agent reads stale codex → implements wrong pattern
2. Plan discovers a codex gap → filed as todo → never written → gap persists
3. Codex says "future / post-cutover" for things plans already shipped → misleads agents

**Operator intent:** Codex must paint target reality — current state + planned delta + final destination — for every
architectural surface. Even if code isn't there yet, the destination must be unambiguous.

**Scope:** Full breadth — all 717 codex docs × 44 active plans × 26 epics. **Fix mode:** Fix inline — audit IS the fix
pass.

---

## Audit Taxonomy

| Tag                 | Meaning                                                   | Fix                                                   |
| ------------------- | --------------------------------------------------------- | ----------------------------------------------------- |
| `CODEX-MISSING`     | Plan decision / contract has no codex home                | Write stub or expand existing section                 |
| `CODEX-STALE`       | Codex says "future / planned" but plan already shipped it | Update to current; keep delta note for remaining work |
| `CODEX-CONTRADICTS` | Codex says X, plan decided Y                              | Determine canonical; update the loser                 |
| `CODEX-AHEAD`       | Codex describes aspirational state, code not there yet    | Add `## Current State` box with honest gap            |
| `BROKEN-REF`        | Plan or codex references a path that doesn't exist        | Create stub or fix reference                          |
| `ORPHAN-EPIC-REF`   | Active plan references a SUPERSEDED epic as `parent_epic` | Re-parent to live epic                                |

Priority: P0 = agent assumption violated; P1 = likely to cause next-agent confusion; P2 = cleanup.

---

## Phase 0 — Structural Scan (DONE 2026-05-22)

See full baseline: `plans/audit/results/codex_plan_diff_scan_2026_05_22.md`

- [x] [SCRIPT] P0. Broken-ref scan — 7 refs found, 2 false positives (codex/CLAUDE.md = inline text, not link), 1
      placeholder (xyz-foo.md), 5 legitimate CODEX-MISSING from issues plan
- [x] [SCRIPT] P0. Codex SSOT classification scan — 23 plans have Codex SSOT sections
- [x] [SCRIPT] P1. Orphan plan scan — 0 orphans (all active plans have parent_epic)
- [x] [SCRIPT] P1. SUPERSEDED doc scan — 38 codex docs contain SUPERSEDED markers
- [x] [SCRIPT] P1. Stale delta marker scan — 132 "future", 66 "post-cutover", 12 "post-May-23", 10 "TODO", 7 "not yet
      implemented"
- [x] [WRITE] P0. Baseline counts published to `plans/audit/results/codex_plan_diff_scan_2026_05_22.md`

---

## Phase 1 — Epic-Level Semantic Audit

### Group A — L0 Asset-Group Epics

- [ ] [READ+FIX] P0. `defi_master.md` ↔ `codex/04-architecture/defi-execution-overview.md` + archetypes/ — DeFi error
      codes, CLOUD_KMS_ENCRYPTED custody, chain/connector patterns
- [ ] [READ+FIX] P0. `cefi_master.md` ↔ `codex/04-architecture/batch-live-architecture.md` + CeFi venue patterns
- [ ] [READ+FIX] P1. `tradfi_master.md` ↔ `codex/02-data/per-asset-group-bucket-layouts.md` + tick data docs
- [ ] [READ+FIX] P1. `sports_master.md` ↔ `codex/01-domain/sports-instruments.md` + sports GCS paths
- [ ] [READ+FIX] P1. `predictions_master.md` ↔ codex predictions coverage

### Group B — L1 Pipeline Epics

- [x] [READ+FIX] P0. `mtds_mdps_master.md` ↔ `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — verify
      Phase -2..14 sequencing — **DONE 2026-05-22**: added `## Current state + pipeline migration context` delta box +
      mtds_mdps_master pointer in Related docs. `CODEX-MISSING` finding: pipeline coordination (Phases -2 to 14) had no
      codex home → addressed.
- [x] [READ+FIX] P0. `manifest_master.md` ↔ `codex/02-data/availability-manifest-and-data-status.md` — v5+ 4-state
      capture*status, 17 EXPECTED*\* reasons, cluster validation, available_at — **DONE 2026-05-22**:
      `manifest-migration-coordination.md` had two `SUPERSEDED-FORWARD-LINK` findings (referenced
      `manifest_migration_SUPERSEDED_2026_05_21` in both frontmatter + cross-refs section → updated to
      `manifest_master.md`). Also `CODEX-STALE`: status block said `MANIFEST_SCHEMA_VERSION = 7` as current → updated to
      reflect v8 shipped 2026-05-12 but data-side migration pending (Phases 6-7 of mtds_mdps_master).
- [x] [READ+FIX] P0. `instruments_master.md` ↔ `codex/03-services/` + instrument record patterns — **DONE 2026-05-22**:
      `codex/03-services/` has no instruments-service coverage (by design — instruments docs live in
      `04-architecture/`). `instruments-live-architecture.md` was `CODEX-AHEAD` (describes full target routing table
      without signalling activation state) → added `[DELTA 2026-05-22]` current-state box documenting which phases are
      DONE vs pending.
- [x] [READ+FIX] P1. `features_and_ml_master.md` ↔ ML/features codex sections (Phase 3 streaming MVP state) — **DONE
      2026-05-22**: `features-service-architecture.md` had three findings: (1) `CODEX-AHEAD`: `LookaheadBiasError`
      "6-of-8 family adoption pending" overstated progress (wires DEFERRED per Q1 resolution) → updated to reflect
      deferred state with blocker reason. (2) `CODEX-MISSING`: Phase 3 streaming MVP (`carry_staked_basis` live
      pipeline, plan `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19`) had no codex entry → added
      `## Live streaming MVP — Phase 3 current state` delta box. (3) `BROKEN-REF`: plan link pointed to
      `plans/active/features_repo_consolidation_2026_05_08.md` (ARCHIVED 2026-05-21) → corrected to `plans/archive/`
      path in both migration history and cross-references. `ml-service-architecture.md` correctly reflects standalone
      `ml-service` (no fix needed).

### Group C — L2 Functional Epics

- [ ] [READ+FIX] P0. `execution_master.md` ↔ `codex/04-architecture/` execution suite — UAC error codes, adapter
      patterns, credential convention
- [ ] [READ+FIX] P0. `strategy_master.md` ↔ `codex/09-strategy/architecture-v2/` — strategy registry, archetype coverage
      matrix
- [ ] [READ+FIX] P1. `global_ledger_pnl_attribution_master.md` ↔ codex global-ledger section (stub exists?)
- [ ] [READ+FIX] P1. `trading_agent_master.md` ↔ `codex/04-architecture/trading-agent-service-directive-pipeline.md` —
      PARTIALLY SUPERSEDED banner correct?
- [ ] [READ+FIX] P1. `client_isolation_and_governance_master.md` ↔
      `codex/04-architecture/per-client-isolation-architecture.md` + `client-funds-isolation.md`
- [ ] [READ+FIX] P1. `dart_and_promote_master.md` ↔ `codex/04-architecture/promote-workflow-architecture.md`

### Group D — L3-L5 Meta Epics

- [ ] [READ+FIX] P1. `infrastructure_master.md` ↔ `codex/05-infrastructure/` — VM tarball, bucket naming, zombie
      watchdog, lifecycle classes
- [ ] [READ+FIX] P1. `batch_live_symmetry_master.md` ↔ `codex/04-architecture/batch-live-architecture.md`
- [ ] [READ+FIX] P1. `deployment_and_user_management_master.md` ↔ `codex/03-deployment/`
- [ ] [READ+FIX] P2. `observability_master.md` ↔ `codex/03-observability/`
- [ ] [READ+FIX] P2. `orchestrator_master.md` ↔ `codex/12-agent-workflow/orchestrator-multi-vm-topology.md`
- [ ] [READ+FIX] P2. `plan_hygiene_master.md` ↔ `codex/11-project-management/plan-hygiene.md`

---

## Phase 2 — Critical-Path Plan→Codex Verification

### Sub-phase 2A — LDR-locked plans (P0)

- [ ] [READ+FIX] P0. `writegate_honest_coverage_endtoend_2026_05_06.md` Codex SSOT → `codex/02-data/` writegate +
      emission semantics
- [ ] [READ+FIX] P0. `per_client_isolation_and_venue_fanout_topology_2026_05_20.md` → per-client-isolation +
      client-funds-isolation + strategy-shard-vm-topology
- [ ] [READ+FIX] P0. `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` → live-pipeline-architecture +
      honest-absence + quality-gates
- [ ] [READ+FIX] P0. `available_at_schema_lift_post_cutover_2026_05_19.md` → availability-manifest + quality-gates
      (confirm post-cutover boundary marked correctly)
- [ ] [READ+FIX] P0. `batch_live_symmetry_2026_05_10.md` → verify 2 promised NEW codex docs exist (cefi-batch-live +
      mode-axis-discipline); write stubs if missing
- [ ] [READ+FIX] P0. `trading_agent_service_architecture_unlock_2026_05_22.md` →
      `codex/04-architecture/trading-agent-service-directive-pipeline.md` + config-reloader-pattern

### Sub-phase 2B — Remaining plans with Codex SSOT sections (P1)

- [ ] [READ+FIX] P1. `strategy_execution_contract_remediation_2026_05_20.md` → strategy→execution contract docs
- [ ] [READ+FIX] P1. `cme_polymarket_arb_2026_05_08.md` → `codex/02-data/per-asset-group-bucket-layouts.md` +
      cme-polymarket-arb playbook
- [ ] [READ+FIX] P1. `kalshi_api_migration_to_elections_subdomain_2026_05_20.md` → contracts-scope-and-layout
- [ ] [READ+FIX] P1. `global_ledger_pnl_attribution_discovery_2026_05_21.md` → check
      `codex/04-architecture/global-ledger-architecture.md`; write stub if missing
- [ ] [READ+FIX] P1. `aws_epic_vm_fleet_2026_05_22.md` → `codex/05-infrastructure/agent-orchestrator-worker-topology.md`
- [ ] [READ+FIX] P1. `api_keys_wallets_accounts_readiness_2026_05_10.md` → 4 missing codex docs (credentials-matrix,
      aws-iam-matrix, secret-manager-naming, rotation-runbook)
- [ ] [READ+FIX] P1. `master_to_live_defi_2026_05_23.md` → the 5 codex gaps it listed
- [ ] [READ+FIX] P1. `honest_coverage_formula_consolidation_2026_05_19.md` → codex SSOT targets
- [ ] [READ+FIX] P1. `code_freeze_migrate_backfill_sequencing_2026_05_10.md` → codex SSOT targets
- [ ] [READ+FIX] P1. `promote_workflow_may23_cli_path_2026_05_10.md` → promote-workflow-architecture
- [ ] [READ+FIX] P1. `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` → post-cutover UI pipeline docs
- [ ] [READ+FIX] P1. `manifest_schema_final_gate_2026_05_09.md` → manifest v8 schema docs
- [ ] [READ+FIX] P1. `strategy_archetype_logic_audit_2026_05_20.md` (audit/results/) → verify 5 CODEX-MISSING docs:
      allocator-pipeline-contract, instrument-type-leverage-matrix, strategy-execution-runtime,
      treasury-trading-wallet-invariant, universe-enumeration-contract
- [ ] [READ+FIX] P1. `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` → TradFi tick data codex docs
- [ ] [READ+FIX] P1. `_trading_agent_unlock_plan_change_manifest_2026_05_20.md` → codex SSOT targets
- [ ] [READ+FIX] P2. `mega_audit_and_plan_beefup_progression_2026_05_20.md` → codex SSOT targets

---

## Phase 3 — Delta Annotation + Stubs + Structural Fixes

Standard delta box:

```
> **[DELTA 2026-05-22]**
> **Current state:** [what's shipped to live-defi-rollout]
> **Planned delta:** [what active plan `<slug>` is delivering]
> **Target architecture:** [final destination]
```

- [x] [EDIT] P0. Apply delta boxes to all P0 CODEX-STALE codex docs ✅ PM@77f0ef404 — delta boxes added to
      `codex/02-data/availability-manifest-and-data-status.md` (top-level v8 migration state + v8 CeFi reshaping note)
      and `codex/02-data/honest-absence-downstream-handling.md` (reason taxonomy + per-service consumer-class table).
      Remaining P0 CODEX-STALE docs tracked under Phase 1+2 above (Group A-D epic checks, Sub-phase 2A LDR-locked
      plans).
- [x] [EDIT] P0. Fix SUPERSEDED banners pointing to SUPERSEDED epics (update forward link to current live epic) ✅
      PM@77f0ef404 (partial) — trading-agent-service-directive-pipeline.md line 217 already points to
      `plans/epics/trading_agent_master.md` (no change needed). Remaining SUPERSEDED banner fixes tracked under Phase 1
      Group C items (strategy_master, dart_and_promote_master, etc.).
- [ ] [WRITE] P1. Write stubs for CODEX-MISSING P0/P1 findings
- [ ] [EDIT] P1. Apply delta boxes to all P1 CODEX-STALE / CODEX-AHEAD docs
- [ ] [EDIT] P1. Update the 12 "post-May-23" codex markers (May-23 = today — mark as shipped or deferred with named
      plan)
- [ ] [EDIT] P2. Fix BROKEN-REF findings

---

## Phase 4 — Verification

- [ ] [SCRIPT] P0. Re-run structural scan → broken-ref count = 0; SUPERSEDED-with-dead-link = 0
- [ ] [VERIFY] P0. Every P0 finding has a resolution
- [ ] [WRITE] P0. Update `plans/audit/results/codex_plan_diff_scan_2026_05_22.md` with after-counts

---

## This Plan's Own Codex Impact

- [ ] [WRITE] `codex/11-project-management/codex-audit-playbook.md` — stub: recurring audit cadence

---

## Full Execution Criterion

1. Broken-ref count = 0 (script verified)
2. Every active plan with "Codex SSOT" section classified DONE / PARTIAL+delta-box / DEFERRED+named-plan
3. Every live L0-L2 epic has at least one owned codex SSOT pointer
4. `plans/audit/results/codex_plan_diff_scan_2026_05_22.md` with before/after counts published
5. `codex/11-project-management/codex-audit-playbook.md` stub written
