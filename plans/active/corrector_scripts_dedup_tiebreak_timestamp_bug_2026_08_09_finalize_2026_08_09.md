---
doc_type: plan
title: >-
  corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md — machine-held via
  depends_on + gate_on_depends: true until the source doc's 3 remaining items (defi corrector live-verification, the
  mirrored timestamp + full-column fix, and the workspace-wide per-VM-shard corrector audit) are done. Reconciles the
  source doc's own checkboxes once shipped (citing fresh commit SHAs / grep evidence), then archives it via the
  standard 6-step ritual once fully closed. Authored 2026-08-09 as part of a combined RECLASSIFY + satellite-
  extraction sweep (round 9, cefi tranche), per task_template.md's finalize-plan-coverage rule (every
  assigned_vm:planning doc needs a companion gated finalize plan).
status: active
nature: process
asset_group: [cefi, defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, manifest, consolidator, dedup, corrector-script]
related:
  [
    /plans/active/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md,
    /plans/archive/2026_08/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09]
gate_on_depends: true
source: >-
  Round-9 combined RECLASSIFY + satellite-extraction sweep, 2026-08-09 —
  issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md was reclassified assigned_vm:NA -> planning
  after all 3 open todos cleared the bounded/worker-determinable bar (a live-comparison verification method the
  source doc's own evidence section already spells out step-by-step, a mechanical mirror-fix of an already-shipped
  commit (instruments-service@159c0ebe0), and a grep-scoped cross-workspace audit for one named defect pattern).
  Conflict-checked clean: the only other corpus reference to the source doc is
  instruments_mtds_consistency_remediation_residuals_2026_07_24.md's citation, which is the source doc's OWN origin
  (the N1b session that filed it), not a duplicate extraction or competing dispatch surface. This finalize doc closes
  the finalize-plan-coverage gate the reclassification itself triggered.
assigned_role: data_engineering
effort: medium
drift_direction: none
context_scope:
  [
    /plans/active/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    instruments-service/scripts/reconcile_correct_legacy_blank_misflips_2026_05_13.py,
    instruments-service/scripts/reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py,
  ]
---

# corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09 — finalize

## Todos

- [ ] [DATA] P1. **Reconcile.** Once the source doc's 3 todos are executed — (1) the defi corrector
      live-verification (grep `RECONCILER_COMPLETED corrected=` events / git history for whether
      `reconcile_correct_legacy_blank_misflips_2026_05_13.py` has ever run `--apply-flips` against a live defi
      bucket, plus a live-comparison spot-check against the defi manifest mirroring this issue's own cefi "Live
      evidence" section), (2) the mirrored fix (stamp fresh `attempted_at`/`written_at` on every corrected row +
      check whether the script's bulk scan is also column-pruned, needing the same DuckDB full-column re-fetch —
      mirror `instruments-service@159c0ebe0`, add regression tests analogous to
      `test_apply_flips_bumps_timestamps_past_original_row`), and (3) the workspace-wide per-VM-shard corrector
      audit — flip each of the source doc's 3 checkboxes to `[x]` with the commit SHA / grep evidence cited, and
      cite the same evidence here. **Done when**: all 3 source-doc checkboxes are `[x]` with evidence, or any
      genuinely-not-actionable sub-finding is retagged with a stated reason (e.g. defi corrector confirmed never run
      live — no fix needed, only documented).
- [ ] [DOC] P3. **Archive.** Run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md` once todo 1 confirms all 3 items are
      closed — dated archive folder, exact-successor banner, corpus-wide referrer fixup (this finalize doc,
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s citation). Then archive this finalize
      plan itself in the same pass. **Done when**: the source doc and this finalize plan are both under
      `plans/archive/`, and `check_reference_paths.py` shows zero new broken referrers.

## Progress Log

- **2026-08-09**: authored alongside the source doc's `assigned_vm: NA -> planning` reclassification (round-9
  combined RECLASSIFY + satellite-extraction sweep, cefi tranche).
