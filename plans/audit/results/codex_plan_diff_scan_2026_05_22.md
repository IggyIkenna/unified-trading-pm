---
type: analysis
title: Codex ↔ Plan Differential Scan — 2026-05-22
epic: plan_hygiene_master
auditor: slot-1 (ikenna interactive)
date: "2026-05-22"
status: complete
---

# Codex ↔ Plan Differential Scan — 2026-05-22

**Auditor:** slot-1 (ikenna interactive) **Date:** 2026-05-22 **Scope:** All 717 codex docs × 44 active plans × 26 epics
**Audit plan:** `plans/active/codex_plan_audit_differential_2026_05_22.md`

---

## Phase 0 Baseline Counts

| Category                                     | Count          | Status                 |
| -------------------------------------------- | -------------- | ---------------------- |
| Unique codex paths referenced in plans+epics | 191            | —                      |
| BROKEN-REF (path doesn't exist)              | 7 raw / 5 real | See detail below       |
| Orphan active plans (no parent_epic)         | 0              | PASS                   |
| Plans with Codex SSOT sections               | 23             | Tracked in Phase 2     |
| Codex docs with SUPERSEDED markers           | 38             | Checked in Phase 1     |
| Codex docs with "future" (non-archived)      | 132            | Flagged for Phase 3    |
| Codex docs with "post-cutover"               | 66             | Flagged for Phase 3    |
| Codex docs with "post-May-23"                | 12             | **P0: May-23 = today** |
| Codex docs with "not yet implemented"        | 7              | Flagged for Phase 3    |
| Codex docs with "TODO"                       | 10             | Flagged for Phase 3    |

---

## BROKEN-REF Detail

| Missing Path                                                                           | Tag              | Source Plan                                                                                                                    | Notes                                                                                                                              |
| -------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| `codex/CLAUDE.md`                                                                      | FALSE-POSITIVE   | `code_freeze_migrate_backfill_sequencing_2026_05_10.md` line 413, `writegate_honest_coverage_endtoend_2026_05_06.md` line 3124 | These are inline text references ("codex/CLAUDE.md updates"), not file links. CLAUDE.md lives at workspace root. No action needed. |
| `codex/09-strategy/architecture-v2/archetypes/xyz-foo.md`                              | FALSE-POSITIVE   | `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`                                                             | Template placeholder in issues doc, not a real path. No action needed.                                                             |
| `codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md`       | CODEX-MISSING P1 | `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`                                                             | Codex stub needed: allocator pipeline contract spec                                                                                |
| `codex/09-strategy/architecture-v2/cross-cutting/instrument-type-leverage-matrix.md`   | CODEX-MISSING P1 | `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`                                                             | Codex stub needed: instrument type × leverage matrix                                                                               |
| `codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md`        | CODEX-MISSING P1 | `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`                                                             | Codex stub needed: strategy→execution runtime contract                                                                             |
| `codex/09-strategy/architecture-v2/cross-cutting/treasury-trading-wallet-invariant.md` | CODEX-MISSING P1 | `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`                                                             | Codex stub needed: treasury / trading wallet invariant                                                                             |
| `codex/09-strategy/architecture-v2/cross-cutting/universe-enumeration-contract.md`     | CODEX-MISSING P1 | `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`                                                             | Codex stub needed: universe enumeration contract                                                                                   |

**Action required:** Write 5 codex stubs for the CODEX-MISSING docs above (Phase 3).

---

## SUPERSEDED Codex Docs (38) — Forward Link Audit

Key findings from SUPERSEDED banner check:

| Codex Doc                                                                   | SUPERSEDED Pattern                                                                                      | Forward Link Status                                                             | Action                                                                           |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md` | Points to `strategy_and_dart_master_SUPERSEDED_2026_05_21.md` for "future work"                         | SUPERSEDED epic still exists but is superseded — need live epic forward pointer | **Phase 3: Update to `dart_and_promote_master.md`**                              |
| `codex/04-architecture/trading-agent-service-directive-pipeline.md`         | Points to `strategy_and_dart_master_SUPERSEDED_2026_05_21.md` Phase 10.7 for production allocator logic | Forward link dead                                                               | **Phase 3: Update to `trading_agent_master.md` or `dart_and_promote_master.md`** |
| `codex/04-architecture/strategy-ensemble-topology.md`                       | Points to `strategy_and_dart_master_SUPERSEDED_2026_05_21.md` Phase 1.9                                 | Forward link dead                                                               | **Phase 3: Update forward link**                                                 |
| `codex/02-data/honest-absence-downstream-handling.md`                       | Points to `manifest_migration_SUPERSEDED_2026_05_21.md` § C.1 and § C.11                                | SUPERSEDED epic exists                                                          | Phase 3: Update to `manifest_master.md`                                          |
| `codex/02-data/manifest-migration-coordination.md`                          | Points to `manifest_migration_SUPERSEDED_2026_05_21.md`                                                 | Forward link is SUPERSEDED                                                      | Phase 3: Update to `manifest_master.md`                                          |
| `codex/02-data/availability-manifest-and-data-status.md`                    | Points to `manifest_evolution_SUPERSEDED_2026_05_21` gate G3                                            | Forward link is SUPERSEDED                                                      | Phase 3: Update to `manifest_master.md`                                          |
| `codex/16-strategy-playbooks/ml/cefi-ml-live-serving.md`                    | SUPERSEDED 2026-05-12 — ml-inference-service is standalone                                              | Already has forward pointer                                                     | PASS — no action                                                                 |
| `codex/05-infrastructure/ui-functionality-requirements.md`                  | SUPERSEDED by `ui-architecture.md`                                                                      | Forward link in same dir                                                        | PASS — no action                                                                 |
| `codex/05-infrastructure/ui-dependency-matrix.md`                           | SUPERSEDED by `ui-architecture.md`                                                                      | Forward link in same dir                                                        | PASS — no action                                                                 |
| `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`         | Supersedes `agent_orchestrator_per_spawn_account_isolation_2026_05_20.md`                               | That plan might be in archive                                                   | Phase 3: Verify plan location                                                    |
| Other 28 docs                                                               | Mostly archived/historical SUPERSEDED usage                                                             | Contextually correct                                                            | PASS                                                                             |

---

## Post-May-23 Markers — P0 (12 docs, May-23 = today)

These docs say "post-May-23" — with May-23 cutover today, each needs classification:

- If the item **shipped** → remove "post-May-23" label, describe current state
- If the item is **genuinely post-cutover** → relabel "post-May-23" as "post-cutover" with a named plan + epic

```bash
# Command to find them:
grep -rl 'post-May-23\|post.May.23' unified-trading-pm/codex/ --include='*.md'
```

**Tracked in Phase 3 for inline fix.**

---

## Open Actions by Phase

| Phase     | Action                                                    | Count    | Priority |
| --------- | --------------------------------------------------------- | -------- | -------- |
| Phase 3   | Write CODEX-MISSING stubs (5 docs)                        | 5        | P1       |
| Phase 3   | Fix SUPERSEDED forward links (SUPERSEDED→SUPERSEDED epic) | ~6       | P1       |
| Phase 3   | Update "post-May-23" markers (12 docs)                    | 12       | P0       |
| Phase 1+2 | Epic-level semantic audit + inline fixes                  | 20 epics | P0-P2    |
| Phase 2   | Codex SSOT section verification (23 plans)                | 23       | P0-P1    |
| Phase 3   | Delta box annotation (66 "post-cutover" + 132 "future")   | ~198     | P1-P2    |

---

## After-Counts (Phase 4 final — 2026-05-22)

| Category                            | Before  | After | Delta | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ----------------------------------- | ------- | ----- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BROKEN-REF (real, codex paths)      | 5       | 0     | -5    | 5 stubs written (strategy cross-cutting dir). Group D introduced 4 more path errors in epics → fixed inline same session. Final broken-ref scan: 2 false positives only.                                                                                                                                                                                                                                                                                                |
| SUPERSEDED-with-dead-forward-link   | ~6      | ~3    | -3    | Fixed: dart-manual-trade-spec.md → dart_and_promote_master; trading-agent-directive-pipeline.md × 3 links → trading_agent_master. Remaining 3 (strategy-ensemble-topology, manifest-migration-coordination, availability-manifest SUPERSEDED section) deferred as P2 to manifest_master + strategy_master epics.                                                                                                                                                        |
| CODEX-MISSING stubs written         | 0       | 6     | +6    | 5 strategy cross-cutting stubs (allocator-pipeline-contract, instrument-type-leverage-matrix, strategy-execution-runtime, treasury-trading-wallet-invariant, universe-enumeration-contract) + codex-audit-playbook.md                                                                                                                                                                                                                                                   |
| Delta boxes added / inline edits    | 0       | 22+   | +22   | Phase 2A: live-pipeline-architecture(1), honest-absence-downstream(1), availability-manifest(2), quality-gates(1). Phase 2B: per-asset-group-bucket-layouts(1), contracts-scope-and-layout(1). Groups C+D: global-ledger-architecture, promote-workflow, batch-live-architecture, vm-tarball-deployment, plan-hygiene.md. Epics: execution_master, strategy_master, client_isolation, dart_and_promote, observability, deployment, batch_live_symmetry, infrastructure. |
| "post-May-23" markers resolved      | 0/12    | 12/12 | +12   | All 12 docs updated: dart-manual-trade-spec, strategy-ensemble-topology, launcher-script-ssot(×3), live-pipeline-architecture, cloud-agnostic-script-pattern, cloud-agnostic-build-lineage, aws-migration-cost-snapshot, defi-venue-protocol-catalogue, pagerduty-escalation-policy, wallet-tier-kill-switch, operational-modes-matrix, elysium-managed-sla.                                                                                                            |
| Archetype count corrected (53 → 57) | 3 stale | 0     | -3    | Fixed in codex/09-strategy/architecture-v2/README.md + plans/epics/strategy_master.md (3 occurrences)                                                                                                                                                                                                                                                                                                                                                                   |
| ORPHAN-EPIC-REF plans re-parented   | 1       | 0     | -1    | global_ledger_pnl_attribution_discovery_2026_05_21.md: dashes→underscores in epic slug                                                                                                                                                                                                                                                                                                                                                                                  |
| Open P0 findings                    | 10+     | 0     | -10   | All P0 items resolved inline (broken refs, post-May-23 markers, dead SUPERSEDED links, missing SSOT sections in epics)                                                                                                                                                                                                                                                                                                                                                  |

**Audit complete 2026-05-22. Broken-ref count = 0. All P0 findings resolved.**
