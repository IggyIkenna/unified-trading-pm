---
doc_type: issue
title:
  "Residual from the VenueCategoryV2 rename fix — coverage.ts still needs a content-drift regen + an audit for other
  UAC-side architecture_v2 enum renames the UI mirror may have missed"
summary:
  "ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md's recommended fix had 5 steps; the UI-side rename fix
  (unified-trading-system-ui@7900f560, 2026-07-28) executed steps 1/2/4 (rename VenueAssetGroupV2->VenueCategoryV2, add
  CROSS_CATEGORY, verify quality-gates.sh green) but explicitly deferred steps 3 and 5, since that same session's task
  framing said a separate agent was handling 'the generator-script half in unified-trading-pm' concurrently — this doc
  exists so steps 3/5 stay a tracked todo rather than evaporate as prose in the now-archived parent issue's resolution
  banner, regardless of whether the concurrent sibling agent's own scope already covers them (if it does, this todo is a
  harmless duplicate to tick closed; if it doesn't, this is the only place the residual is tracked)."
status: open
nature: issue
asset_group: [cefi, defi, sports, tradfi, prediction]
stage: [strategy]
repos: [unified-trading-system-ui, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [archetype, capability-registry, ui-sync, coverage-ts, follow-up]
related: [/plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md]
created: 2026-07-28
parent_epic: strategy_master
priority: P3
source:
  [
    "Split out of ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md at archival time, per the todos-not-prose
    archival rule (/codex/12-agent-workflow/plan-completion-and-archival-discipline.md § 2).",
  ]
assigned_vm: planning
assigned_role: ui_developer
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
resolved_by:
---

## What's left

The parent issue's recommended fix had 5 steps. Steps 1/2/4 are done (`unified-trading-system-ui@7900f560`: rename +
`CROSS_CATEGORY` member + green `quality-gates.sh`). Not done:

3. Re-run `bash unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh --write` to regenerate
   `unified-trading-system-ui/lib/architecture-v2/coverage.ts` against the current `archetype_capability_manifest.json`
   — this also picks up unrelated accumulated content drift (TSMOM_BTC_CTA rows, `smarkets_direct` venue additions,
   notes-formatting fixes) that the naming fix alone doesn't touch. With the UI-side rename now landed, running
   `--write` should produce a clean diff (no more undefined-type breakage) — verify this before shipping.
4. Grep for any other UAC-side `architecture_v2` enum/type renames that may have similarly drifted from their UI mirrors
   (the parent issue's own evidence — coverage.ts last synced 2026-06-22, UAC manifest touched multiple times since —
   suggests the sync pipeline's `--check` gate wasn't being run regularly in this UI checkout).

## Todos

- [ ] [ENGINEER] P3. Re-run `sync-archetype-capability-to-ui.sh --write`, verify the UI's `quality-gates.sh` stays green
      against the regenerated `coverage.ts`, and grep UAC's `architecture_v2` enums/types against the UI mirror for any
      other renamed/drifted export — fix any found the same way this issue's parent was fixed.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). sole todo is a bounded script re-run (`sync-archetype-capability-to-ui.sh --write`) + a mechanical
  enum-mirror grep; conflict-check clear (the one `capability_wizard_analysis_findings` hit is a missing-TEST claim, not
  the regen). Shared conflict-check protocol:
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` sect.3 - CLEARED.
