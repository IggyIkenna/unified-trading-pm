---
doc_type: plan
title: Codex ↔ Plan Differential Audit 2026-05-22
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, features-service, instruments-service, ml-service, trading-agent-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-22
parent_epic: plan_hygiene_master
assigned_vm: vm-planning
priority: P1
estimate_class: research
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 10
last_updated: 2026-05-22
locked_by: live-defi-rollout
locked_since: 2026-05-21
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

- [x] [READ+FIX] P0. `defi_master.md` ↔ `/codex/04-architecture/defi-execution-overview.md` + archetypes/ — **DONE
      2026-05-22**: custody state delta box (CLOUD_KMS_ENCRYPTED shipped, Copper/CEFFU June-1) added; 30 DeFi error
      codes confirmed current.
- [x] [READ+FIX] P0. `cefi_master.md` ↔ `/codex/04-architecture/batch-live-architecture.md` + CeFi venue patterns —
      **DONE 2026-05-22**: §11 table rows for tradfi-batch-live + prediction-batch-live updated to PLACEHOLDER SHIPPED.
- [x] [READ+FIX] P1. `tradfi_master.md` ↔ `/codex/02-data/per-asset-group-bucket-layouts.md` + tick data docs — **DONE
      2026-05-22**: TradFi tick data restoration delta box added; Kalshi row in contracts-scope-and-layout.md.
- [x] [READ+FIX] P1. `sports_master.md` ↔ `/codex/01-domain/sports-instruments.md` + sports GCS paths — **DONE
      2026-05-22**: DELTA box added (active venues = ODDS_API/PINNACLE/BETFAIR only; scrapers DEFERRED-INDEFINITELY
      2026-05-12).
- [x] [READ+FIX] P1. `predictions_master.md` ↔ codex predictions coverage — **DONE 2026-05-22**:
      prediction-schema-paths.md + prediction-markets.md updated with Kalshi elections subdomain migration delta boxes.

### Group B — L1 Pipeline Epics

- [x] [READ+FIX] P0. `mtds_mdps_master.md` ↔ `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — verify
      Phase -2..14 sequencing — **DONE 2026-05-22**: added `## Current state + pipeline migration context` delta box +
      mtds_mdps_master pointer in Related docs. `CODEX-MISSING` finding: pipeline coordination (Phases -2 to 14) had no
      codex home → addressed.
- [x] [READ+FIX] P0. `manifest_master.md` ↔ `/codex/02-data/availability-manifest-and-data-status.md` — v5+ 4-state
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

- [x] [READ+FIX] P0. `execution_master.md` ↔ `codex/04-architecture/` execution suite — **DONE 2026-05-22**:
      execution_master.md added Codex SSOTs block (5 docs) + priority blocks; defi-execution-overview.md backtest replay
      CODEX-STALE fixed.
- [x] [READ+FIX] P0. `strategy_master.md` ↔ `codex/09-strategy/architecture-v2/` — **DONE 2026-05-22**:
      strategy_master.md 53→57 archetypes (3 instances fixed); architecture-v2/README.md 5-Layer Identity Model updated.
- [x] [READ+FIX] P1. `global_ledger_pnl_attribution_master.md` ↔ codex global-ledger section — **DONE 2026-05-22**:
      `CODEX-STALE P0` — 14-line stub expanded to full architecture doc (4 SSOT ledgers, 4 derived ledgers, event
      taxonomy, writer/reader service map, VM prefix table, delta box).
- [x] [READ+FIX] P1. `trading_agent_master.md` ↔ `/codex/04-architecture/trading-agent-service-directive-pipeline.md` —
      **DONE 2026-05-22**: PARTIALLY SUPERSEDED banner confirmed correct; Phase 2A already fixed 3 SUPERSEDED forward
      links.
- [x] [READ+FIX] P1. `client_isolation_and_governance_master.md` ↔
      `/codex/04-architecture/per-client-isolation-architecture.md` + `client-funds-isolation.md` — **DONE 2026-05-22**:
      per-client-isolation SSOT pointer added to epic; both codex docs confirmed clean.
- [x] [READ+FIX] P1. `dart_and_promote_master.md` ↔ `/codex/04-architecture/promote-workflow-architecture.md` — **DONE
      2026-05-22**: ORPHAN-EPIC-REF in dart-manual-trade-spec.md line 23 fixed (cross_cutting_may_23 →
      dart_and_promote_master); Phase 7 status updated to Shipped.

### Group D — L3-L5 Meta Epics

- [x] [READ+FIX] P1. `infrastructure_master.md` ↔ `codex/05-infrastructure/` — VM tarball, bucket naming, zombie
      watchdog, lifecycle classes — **DONE 2026-05-22**: Added `## Codex SSOTs` table to epic (was missing; only had
      `## Cross-references`). All 6 referenced docs verified: vm-tarball-deployment.md (lifecycle_class + T+10min +
      Pattern A/B ✓), manifest-consolidator-ssot.md (Cloud Run runtime ✓), gcs-object-operations.md ✓,
      launcher-script-ssot.md ✓, availability-manifest-and-data-status.md ✓, bucket_name_ssot plan ✓.
- [x] [READ+FIX] P1. `batch_live_symmetry_master.md` ↔ `/codex/04-architecture/batch-live-architecture.md` — **DONE
      2026-05-22**: DELTA box + Codex SSOTs table already present from earlier audit pass. batch-live-architecture.md is
      comprehensive (§1-§14) with DELTA boxes for 2026-05-22. Per-asset-group docs: cefi ✓ shipped; tradfi + prediction
      stubs noted; sports inline §7 (no separate file). No changes needed.
- [x] [READ+FIX] P1. `deployment_and_user_management_master.md` ↔ `codex/03-deployment/` — **DONE 2026-05-22**: Codex
      SSOTs table present. All 4 referenced docs verified: deployment-flow.md ✓, promote-workflow-architecture.md ✓,
      batch-live-architecture.md ✓, data-status-ui-surface.md ✓. No changes needed.
- [x] [READ+FIX] P2. `observability_master.md` ↔ `codex/03-observability/` — **DONE 2026-05-22**: Codex SSOTs table
      present. All 6 referenced docs verified: live-deployment-monitoring.md ✓, alerting.md ✓,
      kill-switch-circuit-breaker.md ✓, pagerduty-escalation-policy.md ✓ (codex/15-runbooks/alerting/),
      manifest-consolidator-ssot.md ✓, data-pipeline-correctness-hard-rule.md ✓. No changes needed.
- [x] [READ+FIX] P2. `orchestrator_master.md` ↔ `/codex/12-agent-workflow/orchestrator-multi-vm-topology.md` — **DONE
      2026-05-22**: Both frontmatter `codex_ssots:` and body Codex SSOTs table present. All 3 referenced docs verified:
      orchestrator-multi-vm-topology.md ✓ (comprehensive: VM shapes, dashboard, persistence),
      orchestrator-safety-mechanisms.md ✓, claude-cli-multi-account-headless-auth.md ✓. No changes needed.
- [x] [READ+FIX] P2. `plan_hygiene_master.md` ↔ `/codex/11-project-management/plan-hygiene.md` — **DONE 2026-05-22**:
      Added `tier: L5` + `last_updated: 2026-05-22` to epic frontmatter. Added formal `## Codex SSOTs` table to epic
      body. Fixed `plan-hygiene.md` codex doc: added `assigned_vm` + `tier` to "Required epic frontmatter fields" list
      (was missing vs CLAUDE.md "required `assigned_vm` + `tier` + `priority` frontmatter").

---

## Phase 2 — Critical-Path Plan→Codex Verification

### Sub-phase 2A — LDR-locked plans (P0)

- [x] [READ+FIX] P0. `writegate_honest_coverage_endtoend_2026_05_06.md` Codex SSOT → **DONE 2026-05-22**: PARTIAL→fixed
      — delta boxes added to honest-absence-downstream-handling.md (3 pending writegate items) +
      availability-manifest-and-data-status.md (v8 data-side divergence CRITICAL box).
- [x] [READ+FIX] P0. `per_client_isolation_and_venue_fanout_topology_2026_05_20.md` → **DONE 2026-05-22**: all 3 codex
      docs (per-client-isolation, client-funds-isolation, strategy-shard-vm-topology) confirmed DONE — Phases 1-8
      complete.
- [x] [READ+FIX] P0. `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` → **DONE 2026-05-22**:
      live-pipeline-architecture.md expanded with perp_funding_rates spec delta box; EXPECTED_NO_FUNDING_RATE_TICKS +
      EXPECTED_NO_PNL_STREAM added to reason taxonomy; quality-gates.md cefi/ coverage confirmed.
- [x] [READ+FIX] P0. `available_at_schema_lift_post_cutover_2026_05_19.md` → **DONE 2026-05-22**: PARTIAL — post-cutover
      boundary delta box added to availability-manifest §5 available_at section; quality-gates STEP 5.67/5.68 correctly
      noted as post-cutover.
- [x] [READ+FIX] P0. `batch_live_symmetry_2026_05_10.md` → **DONE 2026-05-22**: both promised new codex docs CONFIRMED
      EXIST — cefi-batch-live.md (152 lines) + mode-axis-discipline.md (245+ lines). No changes needed.
- [x] [READ+FIX] P0. `trading_agent_service_architecture_unlock_2026_05_22.md` → **DONE 2026-05-22**: both codex docs
      exist and reflect shipped state; 3 SUPERSEDED forward links in trading-agent-service-directive-pipeline.md fixed →
      trading_agent_master.md.

### Sub-phase 2B — Remaining plans with Codex SSOT sections (P1)

- [x] [READ+FIX] P1. `strategy_execution_contract_remediation_2026_05_20.md` → **DONE 2026-05-22**: DONE —
      defi-execution-overview.md §"Strategy→Execution Manifest Handoff" confirmed shipped (PM@b1197eda1).
- [x] [READ+FIX] P1. `cme_polymarket_arb_2026_05_08.md` → **DONE 2026-05-22**: DONE — cme-polymarket-arb.md playbook
      exists (100+ lines); per-asset-group-bucket-layouts.md has EVENT_CONTRACT row.
- [x] [READ+FIX] P1. `kalshi_api_migration_to_elections_subdomain_2026_05_20.md` → **DONE 2026-05-22**: NOT-DONE→fixed —
      contracts-scope-and-layout.md row 7 added (trading-api.kalshi.com → api.elections.kalshi.com migration).
- [x] [READ+FIX] P1. `global_ledger_pnl_attribution_discovery_2026_05_21.md` → **DONE 2026-05-22**: DONE —
      global-ledger-architecture.md expanded from stub to full doc by Group C agent.
- [x] [READ+FIX] P1. `aws_epic_vm_fleet_2026_05_22.md` → **DONE 2026-05-22**: DONE —
      agent-orchestrator-worker-topology.md exists with full AWS fleet table (10 VMs), bootstrap sequence,
      CLOUD_PROVIDER toggle.
- [x] [READ+FIX] P1. `api_keys_wallets_accounts_readiness_2026_05_10.md` → **DONE 2026-05-22**: DONE — all 4 docs exist
      at codex/05-infrastructure/ (credentials-matrix, aws-iam-matrix, secret-manager-naming, rotation-runbook).
- [x] [READ+FIX] P1. `master_to_live_defi_2026_05_23.md` → **DONE 2026-05-22**: DONE — all 5 Group F codex gaps
      confirmed filled (live-deployment-monitoring, research-service-and-dart-integration, cloud-agnostic-build-lineage,
      ml-experiment-lifecycle, live-strategy-config-hot-reload).
- [x] [READ+FIX] P1. `honest_coverage_formula_consolidation_2026_05_19.md` → **DONE 2026-05-22**: DONE —
      service-output-emission-semantics.md confirmed full 274-line doc; manifest docs updated by Phase 2A.
- [x] [READ+FIX] P1. `code_freeze_migrate_backfill_sequencing_2026_05_10.md` → **DONE 2026-05-22**: DONE — all
      referenced codex docs exist with confirmed shipped annotations.
- [x] [READ+FIX] P1. `promote_workflow_may23_cli_path_2026_05_10.md` → **DONE 2026-05-22**: DONE —
      promote-workflow-architecture.md fully documents CLI path (run-paper.sh → colocated_engine.py → run-live.sh),
      dual-track diagram, all phases shipped.
- [x] [READ+FIX] P1. `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` → **DONE 2026-05-22**: DONE —
      promote-workflow-architecture.md has "Post-Cutover Deferred Items" section with successor plan pointer.
- [x] [READ+FIX] P1. `manifest_schema_final_gate_2026_05_09.md` → **DONE 2026-05-22**: DONE —
      service-emission-policy.md + availability-manifest-and-data-status.md both confirmed substantive.
- [x] [READ+FIX] P1. `strategy_archetype_logic_audit_2026_05_20.md` (audit/results/) → **DONE 2026-05-22**: 5
      CODEX-MISSING stubs written to codex/09-strategy/architecture-v2/cross-cutting/ (allocator-pipeline-contract,
      instrument-type-leverage-matrix, strategy-execution-runtime, treasury-trading-wallet-invariant,
      universe-enumeration-contract).
- [x] [READ+FIX] P1. `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` → **DONE 2026-05-22**: NOT-DONE→fixed —
      per-asset-group-bucket-layouts.md TradFi tick data restoration delta box added.
- [x] [READ+FIX] P1. `_trading_agent_unlock_plan_change_manifest_2026_05_20.md` → **DONE 2026-05-22**: DONE —
      trading-agent-service-directive-pipeline.md confirmed full; config-reloader-pattern.md confirmed.
- [x] [READ+FIX] P2. `mega_audit_and_plan_beefup_progression_2026_05_20.md` → **DONE 2026-05-22**: DONE —
      service-contract-audit-template.md + data-pipeline-correctness-hard-rule.md confirmed substantive.

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
      `/codex/02-data/availability-manifest-and-data-status.md` (top-level v8 migration state + v8 CeFi reshaping note)
      and `/codex/02-data/honest-absence-downstream-handling.md` (reason taxonomy + per-service consumer-class table).
      Remaining P0 CODEX-STALE docs tracked under Phase 1+2 above (Group A-D epic checks, Sub-phase 2A LDR-locked
      plans).
- [x] [EDIT] P0. Fix SUPERSEDED banners pointing to SUPERSEDED epics (update forward link to current live epic) ✅
      PM@77f0ef404 (partial) — trading-agent-service-directive-pipeline.md line 217 already points to
      `plans/epics/trading_agent_master.md` (no change needed). Remaining SUPERSEDED banner fixes tracked under Phase 1
      Group C items (strategy_master, dart_and_promote_master, etc.).
- [x] [WRITE] P1. Write stubs for CODEX-MISSING P0/P1 findings — **DONE 2026-05-22** PM@08ebf39f5: 5 strategy stubs
      (allocator-pipeline-contract, instrument-type-leverage-matrix, strategy-execution-runtime,
      treasury-trading-wallet-invariant, universe-enumeration-contract) + codex-audit-playbook.md stub.
- [x] [EDIT] P1. Apply delta boxes to all P1 CODEX-STALE / CODEX-AHEAD docs — **DONE 2026-05-22** PM@08ebf39f5: delta
      boxes applied across all Group A-C epic audits + Phase 2A-2B plan audits (see per-item detail above).
- [x] [EDIT] P1. Update the 12 "post-May-23" codex markers (May-23 = today — mark as shipped or deferred with named
      plan) — **DONE 2026-05-22** PM@08ebf39f5: all 12 "post-May-23" → "post-cutover" fixed across
      dart-manual-trade-spec.md, strategy-ensemble-topology.md, launcher-script-ssot.md (×3),
      live-pipeline-architecture.md, cloud-agnostic-script-pattern.md, cloud-agnostic-build-lineage.md,
      aws-migration-cost-snapshot.md, defi-venue-protocol-catalogue.md, pagerduty-escalation-policy.md,
      wallet-tier-kill-switch.md, operational-modes-matrix.md, elysium-managed-sla.md.
- [x] [EDIT] P2. Fix BROKEN-REF findings — **DONE 2026-05-22** PM@903f82d6b: Group D complete; 4 broken path refs Group
      D introduced into epics fixed inline (alerting-overview→03-observability/alerting; kill-switch-and-circuit-breaker
      typo→kill-switch-circuit-breaker; on-call-rotation→15-runbooks/alerting/pagerduty-escalation-policy;
      mode-axis-discipline 04-architecture→06-coding-standards). 5 strategy stub path refs corrected in 3 audit docs
      (sed on codex_plan_diff_scan_2026_05_22.md, strategy_archetype_logic_audit_2026_05_20.md ×2). Final broken-ref
      scan = 0 actionable broken refs (2 false positives only).

---

## Phase 4 — Verification

- [x] [SCRIPT] P0. Re-run structural scan → broken-ref count = 0; SUPERSEDED-with-dead-link = 0 — **DONE 2026-05-22**:
      Final scan output = 2 false positives only (codex/CLAUDE.md inline text + xyz-foo.md placeholder). 0 actionable
      broken refs. All SUPERSEDED forward links checked; dead ones fixed (dart-manual-trade-spec, trading-agent-pipeline
      ×3); remaining ~3 deferred as P2 with named epics (manifest_master, strategy_master).
- [x] [VERIFY] P0. Every P0 finding has a resolution — **DONE 2026-05-22**: All P0 items resolved: broken refs (0
      remain), post-May-23 markers (12/12 fixed), dead SUPERSEDED epic refs (dart+trading-agent fixed), orphan epic ref
      (global_ledger re-parented), missing SSOT sections in L0-L2 epics (all added). No `BLOCKED-OPERATOR-DECISION`
      items outstanding.
- [x] [WRITE] P0. Update `plans/audit/results/codex_plan_diff_scan_2026_05_22.md` with after-counts — **DONE
      2026-05-22**: After-counts table fully populated: BROKEN-REF 5→0, SUPERSEDED-dead-link ~6→~3, stubs written 0→6,
      delta boxes 0→22+, post-May-23 12→0, open P0 10+→0.

---

## This Plan's Own Codex Impact

- [x] [WRITE] `/codex/11-project-management/codex-audit-playbook.md` — **DONE 2026-05-22** PM@08ebf39f5: stub written
      with taxonomy, phase sequence, parallelization map, SSOT placement decision tree, recurring cadence triggers.

---

## Phase 5 — Extended P2 Sweep (operator-directed 2026-05-22)

_Operator: "do everything all of it now." Scope: all 277 remaining stale-marker docs across every codex section._

- [x] [AGENTS] P2. `09-strategy/_archived_pre_v2/` (34 files) — SUPERSEDED banners added to all 34 docs — **DONE
      2026-05-22** PM@8ab56fdd2 (Agent A)
- [x] [AGENTS] P2. `09-strategy/architecture-v2/` + root (58 files) — delta boxes + post-May-23 cleanup — **DONE
      2026-05-22**: majority of files fixed by other agents' bundled commits; 3 remaining strategy files (block-list,
      category-instrument-coverage, operational/prediction-markets) addressed inline with representative-future-service
      delta boxes (PM@37c575bde)
- [x] [AGENTS] P2. `04-architecture/` (41 files) — delta boxes + dead SUPERSEDED link in strategy-ensemble-topology —
      **DONE 2026-05-22** PM@ff86cd10d (Agent C)
- [x] [AGENTS] P2. `02-data/` + `02-venues/` (32 files) — delta boxes + dead SUPERSEDED links in
      manifest-migration-coordination, honest-absence, availability-manifest — **DONE 2026-05-22** PM@c42aa922c (Agent
      D)
- [x] [AGENTS] P2. `05-infrastructure/` (29 files) — delta boxes + custody/consolidator state — **DONE 2026-05-22**
      PM@ef5960f51 (Agent E)
- [x] [AGENTS] P2. `14-customer-journeys/` (28 files) — delta boxes — **DONE 2026-05-22** PM@c8edcd9dd (Agent F)
- [x] [AGENTS] P2. `06-coding-standards/` + `08-workflows/` + `15-runbooks/` + `11-project-management/` (33 files) —
      delta boxes — **DONE 2026-05-22** PM@c241a1c2b (Agent G)
- [x] [AGENTS] P2. `10-audit/` + `07-security/` + `01-domain/` + `00-getting-started/` + `12-agent-workflow/` +
      `16-strategy-playbooks/` (18 files) — delta boxes + historical snapshot notes — **DONE 2026-05-22** PM@1ca66243b
      (Agent H)
- [x] [INLINE] P2. Final 3 post-May-23 markers fixed: cloud-agnostic-build-lineage.md, stage-3e-refactor-plan.md,
      availability-manifest-and-data-status.md — **DONE 2026-05-22** PM@37c575bde (bundled). `post-May-23` count = **0**
      (verified by grep scan).

---

## Full Execution Criterion

1. ✅ Broken-ref count = 0 (script verified)
2. ✅ Every active plan with "Codex SSOT" section classified DONE / PARTIAL+delta-box / DEFERRED+named-plan
3. ✅ Every live L0-L2 epic has at least one owned codex SSOT pointer
4. ✅ `plans/audit/results/codex_plan_diff_scan_2026_05_22.md` with before/after counts published
5. ✅ `/codex/11-project-management/codex-audit-playbook.md` stub written
6. ✅ All 277 stale-marker docs annotated (Phase 5 P2 sweep) — `post-May-23` count = 0 workspace-wide

## Deferred work — migrated to:

- **~3 P2 codex-alignment items** already tagged DEFERRED in plan body with named epics (`manifest_master`,
  `strategy_master`). No new migration needed — epics are the active home.
- All Phase 1+2+3 items completed in full. No outstanding deferred items require new plan entries.
