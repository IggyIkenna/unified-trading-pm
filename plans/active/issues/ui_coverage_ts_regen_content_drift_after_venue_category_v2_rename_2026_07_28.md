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
assigned_role: ui_developer # ⚠️ CONTESTED — prediction tranche argues `infra`; see Progress Log 2026-07-30
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
- **na-eligibility-audit 2026-07-30** (tranche=defi, autonomous): RECLASSIFY -> `assigned_vm: planning` (conflict-check
  CLEAR against 231 active planning docs; no open todo elsewhere duplicates this claim) - single todo is a scripted
  regen + QG-green check + a bounded UAC-vs-UI enum grep — deterministic outcome, no design call. Reached independently
  of the cefi tranche above; both agree.
- **na-eligibility-audit 2026-07-30 (prediction tranche)**: **RECLASSIFY — `assigned_vm: NA → planning`, conflict-check
  CLEAR.** This doc already declared `execution_scope: orchestrator-agent` while carrying `assigned_vm: NA` — a
  self-contradiction, and the classic "defaulted to NA and never assessed" shape the audit's RECLASSIFY verdict exists
  for. Its sole open todo is bounded and worker-determinable: a named script invocation
  (`sync-archetype-capability-to-ui.sh --write`), a machine-checkable done-when (the UI's `quality-gates.sh` green
  against the regenerated `coverage.ts`), and a scoped grep with a stated fix pattern. No design or judgment call
  remains — the parent issue already ruled the direction and steps 1/2/4 already shipped
  (`unified-trading-system-ui@7900f560`). **Conflict-check**
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3): enumerated the real claim
  (regenerate `coverage.ts` from `archetype_capability_manifest.json` + sweep for sibling drifted `architecture_v2`
  exports), then checked all four currently-`assigned_vm: planning` docs that mention this ground —
  `tradfi_manifest_content_recovery_completion_2026_07_24.md` (a Progress Log mention of the parity TEST, not the
  regen), `defi_satellite_ao_dispatch_batch2_2026_07_26.md` (cites the manifest JSON only as a fix-pattern precedent for
  unrelated files), `issues/capability_wizard_analysis_findings_2026_06_11.md` (F4 wants a parity drift-CHECK test — a
  complementary deliverable, not this regen), and `issues/capability_wizard_gap_discovery_2026_06_11.md` (manifest CELL
  content/venue_ids, different axis). Zero verbatim or near-verbatim duplicate claims → CLEAR, flipped.
  `assigned_role: infra` filled from the live `agents/*.md` registry (the work's dominant leg is running a PM
  propagation script + a UAC-side grep; `ui_developer` is a near-miss because its role card explicitly excludes running
  Python tooling, and `backend_engineer` excludes UI repos). **Note for the executing worker, not a gate**: if the regen
  turns out to change rendered UI behaviour rather than only generated constants, the workspace UI playwright gate
  (`[UI]` + `pw:L2 ✓` + a cited regression spec, `/codex/06-coding-standards/ui-testing-layers.md`) applies and this
  becomes a `ui_developer` hand-off — decide that from the actual diff, don't assume either way from this note.
  **Finalize-plan coverage**: not required — `doc_type: issue` under `plans/active/issues/` is structurally exempt
  (`check_finalize_plan_coverage.py` globs `plans/active/*.md` only).
- **na-eligibility-audit 2026-07-30** (tranche=sports, autonomous): RECLASSIFY -> `assigned_vm: planning` (flipped in
  place, name unchanged, codex ao-dispatch-batch-naming §1(b)) — the sole todo is bounded, deterministic work with a
  self-contained done-when (re-run `sync-archetype-capability-to-ui.sh --write`, keep the UI's `quality-gates.sh` green,
  grep UAC `architecture_v2` enums against the UI mirror). Its own blocker (the UI-side rename) landed at
  `unified-trading-system-ui@7900f560`, and `execution_scope` was ALREADY `orchestrator-agent` while `assigned_vm` said
  NA — a defaulted-and-never-assessed classification, not a judgment call. Conflict-check CLEAR: no active
  `assigned_vm: planning` doc carries an open todo claiming the coverage.ts regen. Issue doc -> structurally exempt from
  finalize-plan coverage.
- **⚠️ CONTESTED `assigned_role` — integrator note 2026-07-30.** All FOUR tranches that audited this doc (cefi, defi,
  prediction, sports) agree on the RECLASSIFY verdict, so `assigned_vm: planning` is settled. They do NOT agree on the
  owning role: cefi, defi and sports set `assigned_role: ui_developer` (3); prediction set `assigned_role: infra` (1),
  reasoning that the work's dominant leg is running a PM Python propagation script plus a UAC-side grep, and that the
  `ui_developer` role card explicitly excludes running Python tooling. The merge would have produced a duplicate
  `assigned_role` key with conflicting values; the integrator kept `ui_developer` — both the status quo and the 3-1
  majority — and did **not** adjudicate the substance, because the prediction tranche's own note concedes the call
  depends on whether the regen changes rendered UI behaviour or only generated constants, which is only knowable from
  the actual diff. **Operator/executing worker: pick the role from the real diff before dispatch.**
