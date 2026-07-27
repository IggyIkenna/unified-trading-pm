---
doc_type: issue
title:
  candle_canonical_path_migration_execution_2026_07_24.md todos 3-15 likely duplicate an ALREADY-COMPLETED P5-P8
  migration (plan-split carried a stale pre-completion snapshot)
summary: >-
  candle_canonical_path_migration_execution_2026_07_24.md was split out of a parent plan on 2026-07-24, but the sibling
  issue doc candle_feature_canonical_path_divergence_2026_07_20.md's own Progress Log shows the ENTIRE P5-P8 migration
  (executor build, drain+snapshot, per-AG SPOT --apply for all 4 asset groups, verify/reconcile) already executed and
  independently verified clean 2026-07-21 through 2026-07-23 -- one day BEFORE the split. The new plan appears to carry
  a stale pre-completion todo snapshot forward, risking a future slot agent re-launching a real ~40-VM SPOT migration
  fleet against an already-migrated corpus.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, prediction]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, ssot-drift, mdps, candle-canonical, migration, cross-plan]
related:
  [
    /plans/active/candle_canonical_path_migration_execution_2026_07_24.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: infra
drift_direction: correct-plan
depends_on: []
source:
  ["surfaced 2026-07-27 while closing candle_canonical_path_migration_execution-002 (todo 2), slot-4 live verification"]
resolved_by:
locked_by:
locked_since:
---

# candle_canonical_path_migration_execution_2026_07_24.md carries stale, already-completed todos

## What I found

Dispatched to close todo 2 of `candle_canonical_path_migration_execution_2026_07_24.md` ("VERIFY on `-test-` via
`/data-pipeline-check-mdps`"), I found the sibling doc `candle_feature_canonical_path_divergence_2026_07_20.md`'s own
Progress Log documents that the **entire remaining scope of this plan** (todos 3-15: reader dual-read verify, Tier-2
census, migration executor build, drain+snapshot, per-AG SPOT `--apply` for defi/prediction/cefi/tradfi, and final
verify/reconcile) was **already executed and independently verified clean on 2026-07-21 through 2026-07-23**:

- 2026-07-21: writer/reader lockstep shipped + `-test-` gate ran and PASSED (`mdps@752eaff`, `mdps@2d720b4`).
- 2026-07-22: P0 census completed (all 4 AGs, ~10.9M candle objects, `ORPHAN=0`); P5 executor shipped (`mdps@6ce1a25`);
  P6 drain + P7 apply started (DEFI canary succeeded).
- 2026-07-22/23: P7 full per-AG `--apply` completed for all 4 asset groups (defi 1,131,814 objects; prediction
  1,165,459; cefi 940,606; tradfi 7,646,831).
- 2026-07-23: P8 cross-AG verify/reconcile — all 4 AGs independently confirmed clean, `ORPHAN=0`.

`candle_canonical_path_migration_execution_2026_07_24.md` was split out of its parent **one day later** (2026-07-24) but
its "Todos" section presents this same work as still open (`- [ ]` on items 2-15), suggesting the split captured a
pre-completion snapshot rather than the actual post-completion state.

**My own live re-verification (2026-07-27, read-only, no VM launches, no prod writes) corroborates the sibling doc's
completion claim**:

- The 3 key SHAs (`mdps@752eaff`, `mdps@2d720b4`, `mdps@6ce1a25`) are all real commits, ancestors of current LDR tip —
  nothing reverted since.
- The exact `-test-` shard the original 2026-07-21 gate used still carries the LOCKED canonical shape today.
- PROD `processed_candles/by_date/` on a recent day for **all 4 asset groups** (cefi, defi, tradfi, prediction) carries
  the canonical `pipeline_mode=/timeframe=/data_type=/instrument_type=/venue=` shape right now.

## Why it matters

Todos 12 and 14 of `candle_canonical_path_migration_execution_2026_07_24.md` spec launching "~40 VMs × ~120 concurrent"
for the per-AG SPOT migration apply. If AO dispatches these to a future slot agent without reconciling against the
sibling doc first, that agent would very plausibly launch a real, costly VM fleet to re-migrate a corpus that is already
migrated — safe (idempotent) but a genuine, avoidable multi-hour/real-$ waste, and a source of confusion for whoever has
to reconcile the two docs' conflicting narratives later.

## Recommended decision

- [ ] [DATA] P1. Main/operator reconciles `candle_canonical_path_migration_execution_2026_07_24.md` todos 3-15 against
      `candle_feature_canonical_path_divergence_2026_07_20.md`'s Progress Log and flips/closes the ones that duplicate
      already-completed work (todo 2 already flipped this session with evidence). Preserve genuinely-open residual items
      that are NOT duplicated here — TRADFI's ~7.1M quarantined objects (sibling doc's own todo 3) and CEFI's 149-object
      residual (sibling doc's own todo 19) — wherever they are currently tracked.
- [ ] [DATA] P2. Once reconciled, check whether `candle_canonical_path_migration_execution_2026_07_24.md` should be
      archived/superseded outright (its entire remaining scope may already live in the sibling doc), or trimmed to only
      the genuinely-not-yet-done pieces, per the plan archival ritual (SSOT: `plans/active/task_template.md`).
