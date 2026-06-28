---
name: batch_live_symmetry_master
title: "Batch Live Symmetry Master"
type: epic
tier: L4
status: active
priority: P0
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../active/features_no_lookahead_reaggregation_guard_2026_06_28.md
  - ../active/honest_coverage_smoke_harness_2026_06_28.md
  - ../archive/2026_05/available_at_schema_lift_post_cutover_2026_05_19.md
  - ../archive/2026_05/batch_live_symmetry_2026_05_10.md
---

# Batch Live Symmetry Master

**Owns**: per-service batch=live audit; reconciliation; codifies CLAUDE.md HARD RULE 'Batch = Live'

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Codex SSOTs

| Doc                                                      | Owns                                                                                                              |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `codex/04-architecture/batch-live-architecture.md`       | Single-code-path invariant; 4 seam differences (data source, feature calc, ML inference, output); banned patterns |
| `codex/04-architecture/cefi-batch-live.md`               | CeFi-specific batch=live seam; SHIPPED                                                                            |
| `codex/06-coding-standards/mode-axis-discipline.md`      | `--mode batch\|live` CLI axis; `pipeline_mode=` hive key; `ManifestWriter` mode assertion                         |
| `codex/02-data/availability-manifest-and-data-status.md` | Manifest row keys are mode-agnostic; same row key for batch + live equivalent captures                            |

> **[DELTA 2026-05-22]** **Current state:** `cefi-batch-live.md` SHIPPED (Phase 2A). `tradfi-batch-live.md` +
> `prediction-batch-live.md` are PLACEHOLDER stubs — bodies not yet written. `sports-batch-live.md` does not exist.
> **Planned delta:** Phase 2B-2D of `plans/active/batch_live_symmetry_2026_05_10.md` fills the per-asset-group seam
> docs. Do NOT treat stubs as shipped.

## Assigned active plans

_2 active plans declare `parent_epic: batch_live_symmetry_master` in their frontmatter. Workers pick up in priority
order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

### BLRS recon operator-decision dispatch (slot 7, 2026-06-01 — from `batch_live_reconciliation_service_audit_2026_05_27.md`)

- [ ] [CODE] P1. **D2 — BLRS calls strategy-service position query API for the canonical position baseline** (not a
      BLRS-local recomputation). Repo: batch-live-reconciliation-service.
- [ ] [CODE] P1. **D3 — build all 3 recon green gates: drawdown + fill-rate + bps.** Only-bps recon = false-pass. All
      three must be GREEN for a recon pass. Repo: batch-live-reconciliation-service.
- [ ] [CODE] P1. **D4 — move BLRS recon resolution route to `/t1-recon/...`; live recon stays on
      `strategy-service/position`.** Quick rename (slot 7 may ship if clean). Repo: batch-live-reconciliation-service.

### [`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md)

**status**: ✅ ARCHIVED 2026-05-21 · **estimate**: 1.5 cal AI-days (class: design) — all phases shipped; deferred items
tracked in successor plans (defi_master Phase 2, tradfi_master, predictions_master,
available_at_schema_lift_post_cutover Phase B)

## P2 — useful; opportunistic

### [`available_at_schema_lift_post_cutover_2026_05_19`](../archive/2026_05/available_at_schema_lift_post_cutover_2026_05_19.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 7 items DEFERRED-OPERATOR-DECISION (post-cutover architectural slice; gated on
monorepo migration Block B1 ADT lift + features consolidation Phase 5.c). · **estimate**: 5 cal AI-days

**Deferred (MIGRATED FROM archived plan)** — post-cutover architectural backlog:

- **Phase A — UAC `AvailabilityRule` Protocol (5 items, P1)**: Gate: monorepo migration Block B1 ADT lift.
- **Phase B — QG STEP 5.67/5.68 static enforcement (2 items, P2)**: Gate: Phase A + features_repo_consolidation Phase
  5.c.

### [`batch_live_symmetry_2026_05_10`](../archive/2026_05/batch_live_symmetry_2026_05_10.md)

**status**: ✅ ARCHIVED 2026-05-23 — Tabs 1-5 + code-phase checkboxes complete. Tab 6 paper-soak, Tab 7 Playwright e2e,
Tab 8 backtest VM BLOCKED-OPERATOR. Post-cutover architectural items deferred. · **estimate**: 30 cal AI-days (class:
design)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Archived plans

### [`batch_live_symmetry_2026_05_10`](../archive/2026_05/batch_live_symmetry_2026_05_10.md)

**status**: ✅ ARCHIVED 2026-05-23 — Tabs 1-5 complete; VM-launch tabs (6/7/8) BLOCKED-OPERATOR.

**Deferred (migrated):**

- **Tab 6 — Paper-mode smoke + 7-day soak (OPERATOR ACTION)**: Requires reconciler VM launch. Operator-gated.
- **Tab 7 — Playwright e2e matrix (BLOCKED-INFRA)**: Node.js ≥20 not installed. Operator installs Node.js ≥20 →
  re-assign to slot.
- **Tab 8 — Backtest VM launch + 7-day soak (OPERATOR ACTION)**: All VM operations are human-only.
- **Phase 4 — `record_captured(df=...)` DEFAULT-REMOVAL**: DEFERRED post-cutover. Successor:
  `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 4.
- **Post-cutover**: D4 (shadow fills), J1 (phase→mode helper), L4/G1 (LIVE* rename), F4/F5 (UI refactor), I2 (TradFi
  live), I5 (Prediction live WebSocket).*
