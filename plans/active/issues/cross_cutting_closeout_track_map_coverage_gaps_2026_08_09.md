---
doc_type: issue
title:
  "2 docs carry real, currently-uncovered work invisible to cross_cutting_consolidated_closeout_2026_07_25.md's 24-Track
  map"
summary: >-
  Found during plan_reconciler agt-733350's cross-cutting tranche run (2026-08-09). Filed instead of edited directly
  into the closeout doc because that doc was already at its 1000-line hard cap this same run (trimmed back to 998L) and
  growing it further risks re-breaching the cap. Self-resolved via BLK-3860911c's [WORKER REC] after 2h with no operator
  reply, per the plan-reconcile SKILL's calibration section (a marked recommendation is usually ratified).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer]
tags: [coverage-gap, ag-closeout-audit, plan-hygiene, track-map]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/features_smoke_matrix_p2_rerun_findings_2026_08_05.md,
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md,
  ]
created: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: advance-docs
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "plan_reconciler agt-733350 (slot 27), cross-cutting tranche run, 2026-08-09 -- E1 hunter finding, routed via
  BLK-3860911c"
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/features_smoke_matrix_p2_rerun_findings_2026_08_05.md,
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
  ]
depends_on: []
---

# 2 docs missing from the cross-cutting closeout Track map

## What I found

`cross_cutting_consolidated_closeout_2026_07_25.md`'s 24-Track reachability map is meant to cover every
`asset_group: cross-cutting` doc's real remaining work. Two live docs are not reachable from any Track:

### 1. `features_smoke_matrix_p2_rerun_findings_2026_08_05.md` lineage

This doc (and its 2 archived predecessors, `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md` +
`features_smoke_matrix_verification_findings_2026_08_01.md`) is 0-hit against every Track in the closeout doc. It is not
cosmetic: the lineage contains a **CONFIRMED MDPS `processed_candles` production-stall finding** — a
data-pipeline-correctness-class defect per this workspace's heartbeat rule — that was starving cefi
`delta_one`/`cross_instrument`/`volatility` feature compute for recent dates. Natural home: Track 19 ("Data-pipeline
hardening/self-monitoring family") or Track 10 ("Cross-AG features/ML pipeline").

### 2. `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` (+ its finalize)

**P0 priority, actively `assigned_vm: planning`.** Its own `related:` field explicitly names BOTH Track 17's existing
source doc (`issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md`) AND the closeout doc itself — i.e. it
self-identifies exactly where it belongs — yet neither it nor its finalize twin made it into Track 17. Likely root cause
(matches a pattern the closeout doc's own 2026-08-05 Progress Log entry already named for Tracks 16-24 generally):
`parent_epic: batch_live_symmetry_master` on both docs, which is outside whatever `DATA_EPICS` filter the Track-map
candidate generator uses.

## Why filed here instead of edited into the closeout doc

`cross_cutting_consolidated_closeout_2026_07_25.md` was at 1007 lines (over its 1000-line hard cap) at the start of this
same run; plan_reconciler agt-733350 trimmed it back to 998L via content condensation, not expansion. Adding 2 new Track
entries risks re-breaching the cap and would need its own careful line-budget accounting — better done as a deliberate
follow-up than folded into an already-large reconciliation commit.

## Todos

- [ ] [DOC] P1. Add `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` (+ finalize) to Track 17 of
      `cross_cutting_consolidated_closeout_2026_07_25.md`'s Sources list, given its P0/actively-dispatched status.
      Verify the doc's line count stays at or under 1000 after the addition (condense elsewhere in the same commit if
      not).
- [ ] [DOC] P2. Add the `features_smoke_matrix_p2_rerun_findings_2026_08_05.md` lineage to Track 19 or Track 10 of the
      same closeout doc, same line-budget caveat.
- [ ] [SCRIPT] P2. Check whether the closeout doc's Track-map candidate-generation tooling filters on
      `parent_epic in DATA_EPICS` — if so, confirm whether `batch_live_symmetry_master` should be added to that set (it
      would have caught both of these docs, and likely others), per the 2026-08-05 Progress Log entry's
      already-identified membership-scope gap for Tracks 16-24.

## Progress Log

- **2026-08-09 (plan_reconciler agt-733350)**: filed per BLK-3860911c, self-resolved after 2h with no operator reply
  (marked [WORKER REC] applied: file as a standalone issue doc rather than growing the line-cap-tight closeout doc).
