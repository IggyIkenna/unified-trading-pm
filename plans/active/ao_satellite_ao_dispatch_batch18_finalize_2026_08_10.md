---
doc_type: plan
title: AO satellite AO batch 18 — finalize
summary: >-
  Gated closeout for `ao_satellite_ao_dispatch_batch18_2026_08_10.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until its sole todo is done. Reconciles evidence back into
  `deepseek_flash_ab_routing_test_2026_08_05.md`'s own checkboxes; archives that doc if it reaches zero open todos.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, ao-dispatch, close-out, batch-18, finalize, satellite-extraction]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch18_2026_08_10.md,
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch18_2026_08_10]
gate_on_depends: true
assigned_role: review
effort: medium
drift_direction: advance-code
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch18_2026_08_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  `/na-eligibility-audit ao` full-tranche sweep, group 3, 2026-08-10 — authored alongside batch18 per the mandatory
  finalize-twin rule (task_template.md §4).
---

# AO satellite AO batch 18 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch18_2026_08_10.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until its sole todo is `done`. The batch itself stays `status: draft`
> until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] ✅ [REVIEW] P1. **Re-verify the batch18 done-claim against reality** — confirm the cited `$/task`/turn-count
      numbers and the completion-quality verdicts are real (re-derive at least one figure independently, not just
      re-read the claim). **Done when**: independently reproduced or the cited evidence directly confirms the claim. —
      **Verified 2026-08-10 by independent re-derivation against a fresh S3 hot-backup of the live orchestrator
      `state.db`**
      (`s3://uts-orchestrator-state-427895769566/backups/sqlite/planning/2026-08-10/live_20260810T031559Z.db`, pulled
      read-only via this slot's own AWS credentials — no SSM `ssm:SendCommand` needed/available from this dev checkout,
      the S3 backup path worked directly). First pass used naive string-compared `completed_at` bounds (`"...T20:41:33"`
      vs the DB's actual `"YYYY-MM-DD HH:MM:SS.ffffff"` space-separated format) and silently mis-filtered — same failure
      mode the original session's own Progress Log entry already flagged and fixed; re-ran parsing real `datetime`
      objects before comparing, matching their corrected methodology. **Todo 9 (cost/throughput) — EXACT match**: pro
      n=61 (cited 61), sum spend $5.44769 (cited $5.4477), avg $/task
      $0.089306 (cited
      $0.08931), avg turns 47.328 (cited 47.33), avg tokens/task 6,374,864 (cited 6,374,864, exact);
      flash n=47 (cited 47), sum spend $3.62237
      (cited $3.6224), avg $/task $0.077072 (cited $0.07707), avg turns 79.702 (cited 79.7), avg tokens/task 14,521,505
      (cited 14,521,505, exact). **Todo 10 Layer-1 (reopen-rate) — confirmed**: all 4 cited reopened task_ids
      independently checked against `task_usage` (correct account_id, completed_at inside the window) and `activity_log`
      (`event_type='backlog_task_reopened'`, exactly 1 event each) — `cefi_track2_backfill_vm_preempted_no_recovery-003`
      (pro), `sports_fast_t1_recon_oom_live_capture_outage-003` / `defi_cefi_venue_chain_axis_contamination-011` /
      `deployment_scripts_bucket_soft_delete_retention_drift-002` (flash) all real, all in-pool, all in-window —
      reproduces the cited pro 1/61 (1.6%) / flash 3/47 (6.4%) split exactly. Claim CONFIRMED real, not fabricated —
      figures, sample sizes, and the underlying methodology all check out. Local db copy deleted after verification
      (scratch only, never committed).
- [x] ✅ [DOC] P0. **Reconcile verified evidence into the source doc's own checkboxes** —
      `deepseek_flash_ab_routing_test_2026_08_05.md`'s todos 9/10/11/13. — Already done in
      `unified-trading-pm@79e653a7a0` (the same batch18-todo-1 commit that wrote the Progress Log entries): despite
      batch18's own "Rules for every worker" reserving the checkbox flip for this finalize plan, that commit's diff
      shows it flipped todos 8/9/10/11/13 directly in the source doc alongside the Progress Log writeup. Verified each
      of the 4 in-scope checkboxes (9/10/11/13) carries real, non-placeholder evidence citing batch18 todo 1's numbers
      (not a bare `[x]`) — re-read the source doc directly, no further action needed. No separate commit required for
      this todo since the reconciliation already landed.
- [x] ✅ [REVIEW] P1. **Archive `deepseek_flash_ab_routing_test_2026_08_05.md` ONLY if it is genuinely at zero open
      todos** — NOT archived: source doc has 5 open todos (2/4/12a/17b/25), all extracted to
      `ao_satellite_ao_dispatch_batch12_2026_08_09.md`. 4 of 5 are done there (todos 1-4: `[x]`), but batch12 todo 5 (←
      source todo 25, `backfill_task_usage.py` one-off extension) is still `- [ ]` — genuinely unfinished. Doc stays
      `status: active` until batch12 (+finalize) closes it out. — unified-trading-pm@494c76c538
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch18_2026_08_10.md`, move to `plans/archive/2026_08/`, fix every
      corpus-wide referrer including this finalize plan's own `related:`, then re-run the active-plan inventory
      generator. **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly, and
      `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md`, `/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-10** — Authored in the same turn as batch18, per the mandatory finalize-twin rule. `sequential: true` since
  the 4 todos are a genuine reconcile→archive chain.
- **2026-08-10 — todo 1 done**: independently re-derived batch18's cited `$/task`/turn-count numbers and the reopen-rate
  completion-quality signal directly from a fresh S3 hot-backup of `state.db` (`ssm:SendCommand` unavailable to this
  slot's AWS identity from this dev checkout — used the S3 `backups/sqlite/planning/` mirror instead, also read-only).
  Both reproduced exactly; see the todo's own evidence line for full numbers. Remaining todos (2/3/4) are separate
  `[DOC]`/`[INFRA]` work — not actioned by this `[REVIEW]` todo.
- **2026-08-10 (slot 23) — todo 2 found already done**: dispatched todo 2 (reconcile evidence into the source doc's own
  checkboxes) and found `unified-trading-pm@79e653a7a0` — the same commit batch18 todo 1 cites for the Progress Log
  writeup — had already flipped the source doc's todos 8/9/10/11/13 checkboxes directly, despite batch18's own "Rules
  for every worker" section reserving that flip for this finalize plan. Verified all 4 in-scope checkboxes carry real
  evidence (not bare `[x]`s) before flipping this todo against the existing commit — no new commit needed for the
  reconciliation itself.
- **2026-08-10 (slot 25) — todo 3: archival check complete, NOT archiving**: independently verified the source doc
  (`deepseek_flash_ab_routing_test_2026_08_05.md`) has 5 open checkboxes (2/4/12a/17b/25), all extracted to
  `ao_satellite_ao_dispatch_batch12_2026_08_09.md`. Cross-referenced batch12's own todo list directly (not inferred):
  todos 1-4 are `[x]` done with real evidence, but todo 5 (← source todo 25, the `backfill_task_usage.py` one-off
  extension) is still `- [ ]` — genuinely unfinished real work, not just an un-flipped checkbox. Batch12's finalize plan
  (`ao_satellite_ao_dispatch_batch12_finalize_2026_08_09.md`) is also still entirely `- [ ]` (machine-gated on batch12
  completing). Source doc stays `status: active` — do NOT archive until batch12 closes out its last todo and its
  finalize reconciles evidence back. This finalize plan's todo 4 (archive batch18 itself) is still pending.
- **context-scout 2026-08-15**: populated/refreshed context_scope (3 entries).
