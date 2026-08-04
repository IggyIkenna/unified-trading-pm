---
doc_type: plan
title: Sports closeout Track X hygiene — finalize (reconcile parent pointer + archive)
summary: >-
  Gated closeout for sports_closeout_track_x_hygiene_2026_07_25.md — machine-held via depends_on + gate_on_depends: true
  until all 4 of that plan's todos are done. Reconciles evidence back into sports_consolidated_closeout_2026_07_19.md's
  Track X pointer, re-checks whether the league_id fold-in item's landing has unblocked Track V's own league_id todos,
  then runs the standard archival ritual on the Track X plan. Mirrors
  sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md's pattern.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, track-x, finalize, archival]
related:
  [
    /plans/active/sports_closeout_track_x_hygiene_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_closeout_track_x_hygiene_2026_07_25]
gate_on_depends: true
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan,
  mirroring the sports_satellite_ao_dispatch_batch2-finalize precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_closeout_track_x_hygiene_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports closeout Track X hygiene — finalize

> **Machine-gated on `sports_closeout_track_x_hygiene_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 4 tasks in that plan are `done`.

## Todos

- [ ] [REVIEW] P1. **Flip `sports_consolidated_closeout_2026_07_19.md`'s Track X "MOVED 2026-07-25" pointer to a ✅ DONE
      line**, citing the Track X plan's shipped commits for the cross-link note, the league_id fold-in merge, the
      peripheral-bucket contamination fix, and the 2 shipped worktree changes — verify each cited commit exists
      (`git log`, not the source plan's own claim alone). **Done when**: the parent's Track X pointer line reads ✅ DONE
      with all shipped commits cited.
- [ ] [REVIEW] P1. **Confirm the league_id fold-in item's landing has actually unblocked the parent's Track V league_id
      todos** — re-read Track V's league_id-migration section and verify it now cites the merged `LEAGUE_ID_TO_TIER`
      mapping + 28-unmapped-`league_id` gap-analysis rather than treating them as still-external. If Track V's own text
      still reads as blocked on this item, do NOT silently mark it resolved — file a follow-up noting the gap. **Done
      when**: Track V's league_id section is confirmed to cite the merged location, or a follow-up is filed if it does
      not.
- [ ] [DOC] P1. **Archive `sports_closeout_track_x_hygiene_2026_07_25.md`** via the standard 6-step ritual: confirm todo
      2 above resolved cleanly → add the archive banner → codex-alignment check (no new codex doc was created by this
      extraction, so this is a no-op confirmation, not a skip) → grep the corpus for every referrer of
      `sports_closeout_track_x_hygiene_2026_07_25` (including this finalize doc's own filename) and fix each path to the
      archived location → clear `locked_by` (already empty, confirm) → archive this finalize doc alongside it in the
      same commit. **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus referrer resolves to the
      new path, and this finalize doc is archived in the same commit.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — added the merged `LEAGUE_ID_TO_TIER`/gap-analysis
  tracking issue todo 2 must confirm Track V cites, and the archival-ritual codex SSOT in place of the parent epic;
  code-free finalize gate, no source path applicable.
