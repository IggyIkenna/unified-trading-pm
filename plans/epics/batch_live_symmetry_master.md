---
doc_type: epic
title: Batch Live Symmetry Master
summary:
  L4 epic codifying the CLAUDE.md 'Batch = Live' HARD RULE — single-code-path invariant, 4 seam differences (data
  source, feature calc, ML inference, output), per-asset-group batch=live seam docs, and BLRS 3-green-gate
  reconciliation (drawdown + fill-rate + bps, not bps-only).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [batch-live-reconciliation-service, strategy-service]
scope: [engineer, admin]
tags: [reconciliation, pipeline-mode, data-correctness, live-trading, manifest, features, mtds]
related:
  [
    ../archive/2026_07/features_no_lookahead_reaggregation_guard_2026_06_28.md,
    ../archive/2026_07/honest_coverage_smoke_harness_2026_06_28.md,
    ../archive/2026_05/available_at_schema_lift_post_cutover_2026_05_19.md,
    ../archive/2026_05/batch_live_symmetry_2026_05_10.md,
  ]
created: 2026-05-21
name: batch_live_symmetry_master
tier: L4
priority: P0
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/citadel_paper_batch_live_reconciliation_2026_06_19.md
  - ../archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md
  - ../archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08_finalize.md
  - ../active/daily_trading_analyst_llm_job_design_2026_07_29.md
  - ../active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md
  - ../active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md
  - ../active/pipeline_mode_partition_migration_2026_06_01.md
last_updated: 2026-07-12 # was: 2026-07-08 -- corrected 2026-07-14, verify-rerun-2 finding 14: body carries a dated "Count corrected 2026-07-12" entry (finding id 311, §A2 B-queue ruling) that postdated the recorded last_updated
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Batch Live Symmetry Master

**Owns**: per-service batch=live audit; reconciliation; codifies CLAUDE.md HARD RULE 'Batch = Live'

**Status**: populated (was: "stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with
P0/P1/P2/P3 priority blocks listing all assigned active plans." — left in place after fill, corrected 2026-07-12,
finding id 311, §A2 B-queue ruling). Body below (P0 findings, codex SSOT table, DELTA banners, archived-plan summaries)
is populated as of `last_updated: 2026-07-08`; this line is no longer describing an empty stub.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Codex SSOTs

| Doc                                                       | Owns                                                                                                              |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `/codex/04-architecture/batch-live-architecture.md`       | Single-code-path invariant; 4 seam differences (data source, feature calc, ML inference, output); banned patterns |
| `/codex/04-architecture/cefi-batch-live.md`               | CeFi-specific batch=live seam; SHIPPED                                                                            |
| `/codex/06-coding-standards/mode-axis-discipline.md`      | `--mode batch\|live` CLI axis; `pipeline_mode=` hive key; `ManifestWriter` mode assertion                         |
| `/codex/02-data/availability-manifest-and-data-status.md` | Manifest row keys are mode-agnostic; same row key for batch + live equivalent captures                            |

> **[DELTA 2026-05-22 — ✅ RESOLVED, corrected 2026-07-15]** (was: "Current state: `cefi-batch-live.md` SHIPPED (Phase
> 2A). `tradfi-batch-live.md` + `prediction-batch-live.md` are PLACEHOLDER stubs — bodies not yet written.
> `sports-batch-live.md` does not exist. Planned delta: Phase 2B-2D of the (now-archived)
> `plans/archive/2026_05/batch_live_symmetry_2026_05_10.md` fills the per-asset-group seam docs. Do NOT treat stubs as
> shipped.") **Current state**: `/codex/04-architecture/cefi-batch-live.md`, `tradfi-batch-live.md`,
> `prediction-batch-live.md`, and `sports-batch-live.md` are all `status: current` with fully-written bodies — the
> per-asset-group seam docs have shipped. Do not re-dispatch this work.

## Assigned active plans

_7 active plans declare `parent_epic: batch_live_symmetry_master` in their frontmatter. Workers pick up in priority
order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31`](../active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: Recover the live event-log warm-sink
Pub/Sub subscriptions + build the cold-compaction job

## P1 — important; post-current-gate

### [`citadel_paper_batch_live_reconciliation_2026_06_19`](../active/citadel_paper_batch_live_reconciliation_2026_06_19.md)

**status**: active · **estimate**: 38 cal AI-days (class: infra) **title**: Citadel-grade Paper ⟷ Batch ⟷ Live
Reconciliation — the Determinism Spine

### [`citadel_satellite_ao_dispatch_batch1_2026_08_08`](../archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md)

**status**: ✅ ARCHIVED 2026-08-11 — 7/7 todos complete (slots 2/7/9/22/30, 2026-08-08..08-11); gated finalize twin
(`citadel_satellite_ao_dispatch_batch1_2026_08_08_finalize`, also archived) reconciled + archived with it.

### [`daily_trading_analyst_llm_job_design_2026_07_29`](../active/daily_trading_analyst_llm_job_design_2026_07_29.md)

**status**: active · **estimate**: 0.6 cal AI-days (class: design) **title**: Daily cross-cutting LLM "trading analyst"
job — design

## P2 — useful; opportunistic

### [`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize`](../active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md)

**status**: active · **estimate**: 0.16 cal AI-days (class: infra) **title**: Live event-log warm-sink recovery +
cold-compaction — finalize (reconcile parent checkboxes + archive)

### [`pipeline_mode_partition_migration_2026_06_01`](../active/pipeline_mode_partition_migration_2026_06_01.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: infra)

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
