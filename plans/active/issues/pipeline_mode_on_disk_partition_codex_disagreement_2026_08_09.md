---
doc_type: issue
title:
  "codex/02-data/pipeline-mode-partition.md and codex/02-data/pipeline-mode-and-batch-live-reconciliation.md disagree on
  whether the on-disk hive-partition migration is done"
summary: >-
  Found during plan_reconciler agt-733350's cross-cutting tranche run (2026-08-09, codex-alignment hunter). Filed as a
  standalone doc rather than as a todo on `pipeline_mode_partition_migration_2026_06_01.md` because that plan is
  `locked_by: live-defi-rollout` and touching a locked plan needs an explicit operator ruling this run does not have
  (plan-reconcile SKILL.md Phase 4). Self-resolved (filing only, no codex edit) via BLK-1a00c3ce's [WORKER REC] after 2h
  with no operator reply.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm, instruments-service]
scope: [engineer]
tags: [codex-drift, pipeline-mode, hive-partition, ssot-contradiction]
related:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
    /plans/active/pipeline_mode_partition_migration_2026_06_01.md,
  ]
created: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: investigate
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "plan_reconciler agt-733350 (slot 27), cross-cutting tranche run, 2026-08-09 -- codex-alignment hunter finding, routed
  via BLK-1a00c3ce"
context_scope:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
    /plans/active/pipeline_mode_partition_migration_2026_06_01.md,
  ]
depends_on: []
---

# `pipeline_mode` on-disk partition: 2 codex docs disagree

## What I found

- `codex/02-data/pipeline-mode-partition.md:51,73` (status: current) claims the on-disk hive-partition migration is
  **DONE**: "Documents the `pipeline_mode` hive partition column added across every parquet on disk during the bundled
  GCS migration on **2026-05-19**" + a Phase-3 table: "VM fleet execution (31 VMs, all 5 asset_groups) | ✅ complete |
  2026-05-19 ... No data loss."
- `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md:229-244` (also status: current) claims **IN PROGRESS**:
  "## On-disk partition (IN PROGRESS as named rider per AG L3 walk)... re-scoped from 'Phase 5 DEFERRED'..." with a
  per-bucket table (dated "as of 2026-06-01") showing cefi/defi/tradfi/sports all "In L3 walk plan" (not done) and
  instruments "Pending — not yet in scope."
- Corroborating the "not done" side: the archived plan
  `plans/archive/2026_06/pipeline_mode_implementation_2026_05_28.md:68` (created 9 days AFTER
  `pipeline-mode-partition.md`'s claimed 2026-05-19 completion date) still treats on-disk partitioning as future work:
  "This plan ships **column-level** implementation; the on-disk `pipeline_mode=` partition [is DEFERRED]."
- The active plan `pipeline_mode_partition_migration_2026_06_01.md` (locked, see below) sides with "not done" — its
  per-AG rider table shows all rows still pending — and its own Progress Log (2026-07-21, 2026-08-07 entries) already
  flags this uncertainty in prose ("a live-code spot-check found `pipeline_mode=` already present... may already be live
  as a side effect of other writer work, not silently dropped... recommend an actual `gcloud storage ls`/manifest check
  per asset_group before treating this as done OR as a gap") but that check has never been run, and the flag is prose,
  not a tracked todo.

## Why this matters

An agent grepping only `pipeline-mode-partition.md` would conclude the on-disk hive partition fully landed for all 5
asset groups and skip bundling the rider into a future canonicalisation walk; an agent reading the sibling doc or the
plan would do the opposite. Neither codex doc cross-references the other's contradicting claim.

## Why filed here instead of as a todo on the plan

`pipeline_mode_partition_migration_2026_06_01.md` carries `locked_by: live-defi-rollout` — touching a locked plan's
content needs an explicit operator ruling per `cursor-configs/skills/plan-reconcile/SKILL.md` Phase 4, which this run
does not have. Filing this as its own doc keeps the finding tracked without needing that ruling; once unlocked, the todo
below should move onto the plan itself (or be executed directly, whichever is faster at that point).

## Todos

- [ ] [SCRIPT] P2. Run a live `gcloud storage ls`/manifest spot-check per asset_group (cefi/defi/tradfi/sports/
      prediction/instruments) to determine ground truth on whether the `pipeline_mode=` on-disk hive partition actually
      exists in production GCS paths today.
- [ ] [DOCS] P2. Once the spot-check lands: correct whichever codex doc is wrong with a dated banner (this is a codex
      edit — needs the spot-check's own output as its evidence; do not touch codex speculatively or before the check
      runs). If `pipeline_mode_partition_migration_2026_06_01.md` is unlocked by then, also fold this finding + the
      check's result into that plan directly instead of leaving it as a separate doc.

## Progress Log

- **2026-08-09 (plan_reconciler agt-733350)**: filed per BLK-1a00c3ce, self-resolved after 2h with no operator reply
  (marked [WORKER REC] applied: file the check as a todo — this doc, since the natural target plan is locked — never
  touch codex without the check's own evidence).
