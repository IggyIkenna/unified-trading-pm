---
doc_type: plan
title: >-
  corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md — machine-held via depends_on +
  gate_on_depends: true until the source doc's 3 remaining items (defi corrector live-verification, the mirrored
  timestamp + full-column fix, and the workspace-wide per-VM-shard corrector audit) are done. Reconciles the source
  doc's own checkboxes once shipped (citing fresh commit SHAs / grep evidence), then archives it via the standard 6-step
  ritual once fully closed. Authored 2026-08-09 as part of a combined RECLASSIFY + satellite- extraction sweep (round 9,
  cefi tranche), per task_template.md's finalize-plan-coverage rule (every assigned_vm:planning doc needs a companion
  gated finalize plan).
status: complete
nature: process
asset_group: [cefi, defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, manifest, consolidator, dedup, corrector-script]
related:
  [
    /plans/archive/2026_08/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-12"
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
  issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md was reclassified assigned_vm:NA -> planning after
  all 3 open todos cleared the bounded/worker-determinable bar (a live-comparison verification method the source doc's
  own evidence section already spells out step-by-step, a mechanical mirror-fix of an already-shipped commit
  (instruments-service@159c0ebe0), and a grep-scoped cross-workspace audit for one named defect pattern).
  Conflict-checked clean: the only other corpus reference to the source doc is
  instruments_mtds_consistency_remediation_residuals_2026_07_24.md's citation, which is the source doc's OWN origin (the
  N1b session that filed it), not a duplicate extraction or competing dispatch surface. This finalize doc closes the
  finalize-plan-coverage gate the reclassification itself triggered.
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

> **🟢 ARCHIVED 2026-08-12 — COMPLETE** (status: complete, 0 open todos, unlocked). Source doc's all 4 todos were
> already `[x]` with commit citations when this session picked up the gate; independently re-verified against the source
> doc's own evidence sections (no residual work found), then both docs archived + referrers fixed + codex-alignment
> done. See Progress Log below.

## Todos

- [x] ✅ [DATA] P1. **Reconcile.** Once the source doc's 3 todos are executed — (1) the defi corrector live-verification
      (grep `RECONCILER_COMPLETED corrected=` events / git history for whether
      `reconcile_correct_legacy_blank_misflips_2026_05_13.py` has ever run `--apply-flips` against a live defi bucket,
      plus a live-comparison spot-check against the defi manifest mirroring this issue's own cefi "Live evidence"
      section), (2) the mirrored fix (stamp fresh `attempted_at`/`written_at` on every corrected row + check whether the
      script's bulk scan is also column-pruned, needing the same DuckDB full-column re-fetch — mirror
      `instruments-service@159c0ebe0`, add regression tests analogous to
      `test_apply_flips_bumps_timestamps_past_original_row`), and (3) the workspace-wide per-VM-shard corrector audit —
      flip each of the source doc's 3 checkboxes to `[x]` with the commit SHA / grep evidence cited, and cite the same
      evidence here. **Done when**: all 3 source-doc checkboxes are `[x]` with evidence, or any genuinely-not-actionable
      sub-finding is retagged with a stated reason (e.g. defi corrector confirmed never run live — no fix needed, only
      documented). — **DONE 2026-08-12.** All 4 source-doc checkboxes (the 3 this todo names, plus a 4th `[SCRIPT] P2`
      fix-the-4-newly-found-scripts todo the audit spawned) were already `[x]` with commit citations from prior
      sessions: todo 1 (defi verification, slot 28, 2026-08-09 — confirmed 2 live `--apply-flips` runs, no residual live
      impact but both scripts unpatched at the time), todo 2 (defi fix, slot-15, `instruments-service@7be93d5d`), todo 3
      (workspace audit, slot 2, 2026-08-11 — 4 more defective scripts found), and the audit's spawned fix todo
      (`instruments-service@c51e37ab` + `@f6caf7f5`, per the source doc's own Progress Log — a duplicate-work collision
      with slot 6 resolved in favor of the already-landed commits). No sub-finding was left genuinely-not-actionable;
      every finding in the source doc either shipped a fix or was read + ruled safe (the "Checked and found SAFE"
      section). — unified-trading-pm
- [x] ✅ [DOC] P3. **Archive.** Run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md` once todo 1 confirms all 3 items are closed
      — dated archive folder, exact-successor banner, corpus-wide referrer fixup (this finalize doc,
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s citation). Then archive this finalize plan
      itself in the same pass. **Done when**: the source doc and this finalize plan are both under `plans/archive/`, and
      `check_reference_paths.py` shows zero new broken referrers. — **DONE 2026-08-12.** Source doc moved to
      `plans/archive/2026_08/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md` with an archived
      banner (`resolved_by:` citing all 4 landing commits). Codex-alignment: migrated the durable rule (any per-VM-shard
      corrector script must stamp fresh `attempted_at`/`written_at` on a corrected row or silently lose the dedup
      tie-break) into `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Dedup key" — this is a genuinely new
      durable contract the plan's completion established, not just a bug-fix log. Referrers fixed:
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s citation repointed to the archive path +
      resolved note; `plans/epics/infrastructure_master.md`'s link to this finalize plan repointed to its own archive
      path; `plans/active/INDEX.md` regenerated via `scripts/plans/regenerate_active_plan_index.py`. This finalize plan
      itself archived in the same pass (single-repo mode-1 sanctioned same-commit flip+`git mv`, per
      `plan-completion-and-archival-discipline.md`'s 2026-08-10 narrowing). — unified-trading-pm

## Progress Log

- **2026-08-09**: authored alongside the source doc's `assigned_vm: NA -> planning` reclassification (round-9 combined
  RECLASSIFY + satellite-extraction sweep, cefi tranche).
- **2026-08-12 (slot 11)**: dependency gate satisfied — the source doc's 4 todos were all already `[x]` with commit
  citations. Independently re-read the source doc in full rather than trusting the checkboxes alone (its own "Defi
  verification" and "Workspace-wide audit" sections carry the live evidence directly) — confirmed no residual work. Ran
  the 6-step archival ritual on the source doc (banner, `git mv` to `plans/archive/2026_08/issues/`, corpus-wide
  referrer fixup, codex-alignment migration into `manifest-consolidator-ssot.md`), then archived this finalize plan
  itself in the same session per the "archive immediately" rule.
