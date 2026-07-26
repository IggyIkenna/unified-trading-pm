---
doc_type: plan
title: Sports satellite AO batch 6 — finalize (reconcile source docs + resolve deferrals + archive both)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch6_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 9 of that plan's todos are done. Mirrors the batch3/batch4/batch5-finalize pattern (reconcile each
  distinct source doc's checkboxes once its batch-6 todo lands, then re-check the Deferred conflict-gated +
  operator-gated items for any that have since cleared), and then carries the 4th step batch2-5's finalize plans are all
  missing and which batch6 todo 7 adds to them: archive every source doc this batch drove to terminal status, in the
  same commit as the status flip, so `check_terminal_status_archived.py` never sees a terminal doc in `plans/active/`.
status: draft
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md,
    /plans/active/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch6_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26 (second run of the day, autonomous mode), per task_template.md §4's
  finalize-plan-coverage rule — every assigned_vm: planning plan needs a companion gated finalize plan, mirroring the
  batch2/batch3/batch4/batch5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 6 — finalize

> **⚠️ `status: draft` — NOT dispatched.** Flips to `active` only when its parent batch does, on explicit operator
> approval. Drafted in the same turn as the parent per `task_template.md` § 4's finalize-plan-coverage rule.

> **Machine-gated on `sports_satellite_ao_dispatch_batch6_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 9 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, todo 3 needs todo 2's verdicts, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 9 source docs' checkboxes.** Each batch-6 todo ends with a `Source:` line naming its
      source doc; flip the corresponding checkbox/section there, citing the batch-6 commit(s) that shipped it — **verify
      the cited commit actually exists before citing it**
      (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`), do not trust an evidence line copied from the
      batch plan. Three of the nine need care rather than a mechanical flip: (a) todos 1 and 2 ARE themselves
      checkbox-reconciliation todos on the two features-sweep parts, so for those two the "source doc" reconciliation is
      the deliverable — verify instead that every one of the 24 + 31 checkboxes ended up in one of the three sanctioned
      states (flipped with evidence / annotated with an owner / left open with a stated reason), with zero left in the
      ambiguous original state; (b) todo 3's evidence line belongs in part3 § Y and nowhere else — confirm todo 2 did
      not also flip it (a double-flip would hide which fix actually landed); (c) todos 4 and 8 convert prose to
      checkboxes in their source docs, so confirm no prose item was dropped or silently reworded during conversion (diff
      the "Recommended decision / next steps" text against the new checkboxes). For each source doc: after flipping,
      re-check whether it now has 0 open todos remaining — **checkbox AND prose form, and ignoring checkbox-shaped lines
      inside fenced code blocks** (this audit found a real instance where a `- [ ]` quoted inside a fence read as a live
      todo). Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: all 9 source
      docs' checkboxes/sections are flipped with verified evidence, the three special cases above are each explicitly
      confirmed, and any doc that genuinely reaches 0 open todos is flipped to `status: resolved`.

- [ ] [REVIEW] P1. **Re-check the 8 Deferred items from batch6's own doc** — 2 conflict-gated + 6 operator-gated, the
      latter being 4 doc-level items plus 2 meta-parks (generalise todo 7's finalize-plan fix workspace-wide; assign an
      owning tranche to `sports_prediction_mvp_writetime_precompute_2026_07_24.md`). **Count the bullets in batch6's two
      Deferred sections rather than trusting this number** — it drifted once already during authoring and a restated
      count re-stales on every edit. Now that batch6's todos have landed, some blockers may have cleared as a side
      effect. Specifically: the § Z matchday-recovery ordering conflict may be settled by whatever Track F's re-run
      status is at that point (re-read the closeout's Track F rather than assuming); the
      reconcile-in-place-vs-archive-as-history question may be moot once todos 1 and 2 have actually run and the
      surviving-open count is known (if it drops to ~4 items, the archive-as-history option becomes concretely cheap to
      evaluate — state the measured number); and the two meta-parks are pure operator rulings that no batch6 todo can
      clear, so expect them to still be open unless the operator answered in the interim. For each item: if the blocker
      cleared, extract it as a new tracked todo in a follow-up `batch7` (do not draft it here — this plan's scope is
      reconciliation, not fresh drafting); if still genuinely unresolved, leave it explicitly deferred and do NOT re-ask
      an operator question that has already been asked, just record that the re-check happened. **Done when**: every
      bullet in batch6's Deferred sections has either (a) a note that it is ready for `batch7` extraction because its
      blocker cleared, or (b) an explicit re-verified confirmation the conflict/decision is still open.

- [ ] [REVIEW] P1. **Verify batch6 todo 7's fix actually closed the loop it was written to close, and re-run the gate
      that caught it.** Todo 7 adds a source-doc-archival todo to 5 sports `*_finalize` plans. Confirm (a) all 5 carry
      it, (b) `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures, and (c)
      `.venv/bin/python scripts/plan-hygiene/check_terminal_status_archived.py` reports 0 violations against its
      baseline — including after THIS plan's own todo 1 flipped source docs to `resolved`, which is the exact transition
      that generated today's 10-violation hard failure. If todo 1 flipped any doc to `resolved` without archiving it in
      the same commit, that is the bug todo 7 was meant to prevent reproducing itself inside this very plan — fix it
      here and record that it happened. **Done when**: all three checks pass and the interaction between todo 1 and todo
      7 is explicitly confirmed clean.

- [ ] [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch6_2026_07_26.md` AND every source doc it drove to terminal
      status** via the standard 6-step ritual (per CLAUDE.md's plan-archival rule): migrate any remaining Deferred items
      to a tracked todo elsewhere (todo 2 above should have resolved or re-confirmed all 6 — verify none silently
      vanish) → add the archive banner → run the codex-alignment check (batch6 establishes no new durable contract;
      confirm still true, and note that the finalize-plan-pattern generalisation was deliberately parked, so
      `task_template.md` § 4 is expected to be UNCHANGED) → grep the corpus for every referrer of
      `sports_satellite_ao_dispatch_batch6_2026_07_26` and fix each path to point at the archived location → clear
      `locked_by` (already empty; confirm). **This is the step batch2-5's finalize plans omit**: any source doc todo 1
      flipped to `status: resolved`/`complete` moves to `plans/archive/issues/` (or `plans/archive/2026_07/` for a
      non-issue plan) in the SAME commit as the flip, each with a genuine resolution banner and verified 0 open todos —
      never left terminal-but-active for a CI gate to sweep up. **Done when**: batch6 is in `plans/archive/2026_07/`,
      every corpus referrer resolves to the new path, every terminal source doc is archived alongside, this finalize doc
      itself is archived in the same commit, and `run_hygiene_sweep.sh --ci` is still 0-hard-failures afterwards.
