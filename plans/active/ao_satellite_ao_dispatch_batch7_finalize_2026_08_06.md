---
doc_type: plan
title: AO satellite AO batch 7 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch7_2026_08_06.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc(s)
  (the batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether the
  one conflict-gated declined item's named gate has since cleared, archives the source docs that reach zero open todos,
  and runs the standard 6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-7, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch7_2026_08_06]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-08-06. Ships `status: active` (not draft)
  per the skill's 2026-07-30 finding: `gate_on_depends` already machine-holds every task until the batch's own todos are
  done, so a second draft-gate is a redundant, easy-to-forget manual flip — only the batch itself (genuinely unreviewed,
  judgment-laden content) needs `status: draft` + explicit operator approval.
---

# AO satellite AO batch 7 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] [REVIEW] P0. **Re-verify every batch-7 done-claim against reality, not against its checkbox** — for each of the 3
      todos in `/plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md`, re-run `git show --stat <sha>` for every
      cited commit and re-run the specific named test(s)/verdict directly rather than trusting the claim (todo 1's
      done-when is a written verdict + evidence, not a commit — check the source doc's Progress Log entry exists and the
      raw per-task metrics are actually present, not just asserted). **Done when**: all 3 verified, and any claim whose
      evidence does not hold up is re-opened as a new tracked todo in this doc's Progress Log with the discrepancy
      stated. ✅ VERIFIED — all 3 batch-7 done-claims re-checked against reality (commits confirmed on origin, diffs
      match claims, named regression tests re-run directly and pass); no discrepancies found. See Progress Log for
      per-todo evidence.
- [x] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)** — batch
      7 was an extraction, so the source-doc items it covers are the ones that go stale, not the batch's. Flip the
      specific todo(s) in each of:
      `/plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md` (its first 2 items — leave
      its 3rd item, the unscoped circuit-breaker fork, untouched) and
      `/plans/archive/2026_08/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md` (its 1st + 2nd items —
      leave its 3rd item, the operator-decision ask, untouched). **Done when**: both flips are committed with the
      `docs(plans):` prefix and cite the real commit sha(s). ✅
      `ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md` items 1-2 were already `[x]` (flipped earlier,
      `unified-trading-pm@fdaaa3d7b`) and `ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md` item 1 was already
      `[x]` (`unified-trading-pm@199a73ed6`) — but item 2 (`_tick_once()` reorder) had NOT been flipped back even though
      its code (`agent-orchestrator@bc37d03`+`53492cb`) landed and was verified in todo 1 above. Flipped it now (same
      commit as this checkbox); both source docs' named items are fully reconciled.
- [x] [INFRA] P0. **Re-check the conflict-gated declined item's gate and spin it into batch 8 if it has cleared.** The
      gated item: `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`'s 1st item (LDR-triggered `quality-gates-v2`
      template extension) was parked because it targets the same files as
      `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 18. Check whether that sibling plan's todo 18 has since
      landed (and if so, whether it already covers the `ci_trigger_branch`-style parameterization this item needs, or
      leaves a residual gap worth its own todo) — per this skill's iterative-drain methodology, re-check the SPECIFIC
      named gate, don't re-derive the classification from scratch. Also spot-check whether `RB-04f4f852` (blocking that
      same source doc's 3rd item) has cleared. **Done when**: the item is marked cleared-and-moved (naming the new
      batch-8 plan/todo) or still-gated with the current reason — no entry left unstated. ✅ **NO BATCH-8 SPIN-OFF
      NEEDED — the gate cleared AND the work is already done, archived.**
      `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 18 confirmed `[x]` at current HEAD (the file-collision it
      was gated on). `RB-04f4f852` confirmed cleared: not present in the live `/api/repo-blockers` open list. Both gates
      clearing let the source doc's own owner ship the item directly (not via a batch):
      `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`'s 1st item is `[x]` ✅, evidence
      `unified-trading-pm@d597eb759` + `agent-orchestrator@3f22253` (LDR-triggered `quality-gates-v2` now live). The
      doc's 3rd item (the `RB-04f4f852` propagation-lag fix) is also `[x]` ✅, evidence PM promote PR #2436 merged
      ~04:34 UTC 2026-08-07. The entire source doc reached zero open todos and was independently ARCHIVED 2026-08-07
      (`plans/archive/2026_08/issues/agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`, banner "🟢 ARCHIVED
      2026-08-07 — RESOLVED") by a separate `check_archive_candidates` ratchet-fix pass — so there is nothing left to
      extract into batch 8.
- [x] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** Re-check
      both source docs named in todo 2 above for whether their OTHER (non-batched, deferred) items are also closed
      before archiving — `ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`'s 3rd item and
      `ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`'s 3rd item are NOT covered by this batch and must keep
      either doc open if still unresolved. Run the standard 6-step archival ritual (migrate any DEFERRED item → banner →
      codex-alignment check → fix every referrer's path corpus-wide → clear the lock) on any doc that IS fully done.
      **Done when**: `grep -rl <slug> plans/ codex/` returns only the archived copy's own path for each archived doc,
      and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero NEW hard failures (compare against the
      baseline recorded at this finalize plan's authoring time). ✅
      **`ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md` stays OPEN** — its 3rd item (`[INFRA] P3`, the
      unscoped turn-count circuit breaker) is still `[ ]`, so it does NOT reach zero open todos; correctly excluded
      (todo 2's own instruction). **`ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md` ARCHIVED** — its 3rd
      item was already `[x]` (resolved, an operator-question closed by standing codex rule) and its 2nd item was flipped
      `[x]` in todo 2 above, so it reached zero open todos: filled `resolved_by`, flipped `status: open → resolved`,
      added the ARCHIVED banner, `git mv`'d to
      `/plans/archive/2026_08/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`, repointed all 7
      corpus-wide referrer paths (this plan, the batch7 source plan ×3, and the archived
      `escalation_watchdog_retune_and_reconcile_2026_08_07.md` ×3) from the old active path to the new archive path, and
      ran a codex-alignment fix on `/codex/04-architecture/agent-orchestrator-worker-liveness.md` (stale "20 kills"
      cap + "dormant until manual reset" text corrected to the live default of 50 and the actual post-fix behavior —
      only the 5 live kill triggers go dormant on cap-hit, sweep/reclaim/reconcile mechanisms keep running). No DEFERRED
      items existed on the archived doc. `grep -rl ao_human_gated_recovery_audit_closable_gaps_2026_08_06 plans/ codex/`
      returns only the new archived path. Hygiene-sweep verification recorded in the Progress Log.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md`, migrate any still-open Deferred item into batch 8
      (never leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_08/`,
      fix every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py --commit` (verify the exact entrypoint name at
      execution time). **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly, and
      `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-08-06** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode, scheduled
  dispatch). `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile → re-check
  the one deferred gate → archive sources → archive self) and several touch the same files. Ships `status: active` per
  the skill's 2026-07-30 finding (`gate_on_depends` already holds every task; no separate draft-gate needed).
- **context-scout 2026-08-07**: re-verified context_scope (5 entries) — all paths resolve, matches the established
  finalize-doc pattern (parent batch + the 4 archival-ritual codex SSOTs); genuine `*_finalize` gate, no source path.
- **2026-08-08 (slot 3, `review`, dispatch `ao_satellite_ao_dispatch_batch7_finalize-001`)**: Executed todo 1 —
  re-verified all 3 batch-7 done-claims against reality, not against their checkboxes:
  - **Todo 1** (worker.md/SUB_AGENT_MANDATORY_RULES.md batching worked-example, claimed `unified-trading-pm@a20e52125`):
    commit exists, confirmed ancestor of `origin/live-defi-rollout`. Diff matches the claim exactly (22 lines added to
    `agents/worker.md` STEP 1 + 4 lines to `SUB_AGENT_MANDATORY_RULES.md`) — this is the identical text already read
    live in this session's own STEP 1 boot sequence. Cross-checked the claimed source: source doc
    `/plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`'s Progress Log carries the
    raw per-task table (12 tasks, 4 provider/model buckets, per-bucket % single/multi-tool-turn + gap<5s columns) —
    genuine measured data, not just an asserted verdict. Both source-doc items 1-2 already `[x]`.
  - **Todo 2** (`spawn_retry_count` reset, claimed `agent-orchestrator@bc37d03`): commit exists, ancestor of origin.
    Diff confirms `slot.spawn_retry_count = 0` added to the shared spawn-success path in `server/autospawn.py`, and the
    misleading "stays down until manual respawn" text in `server/worker_liveness/_auth_failover.py` replaced with
    accurate Trigger-3 auto-recovery language. Re-ran the named regression test directly:
    `tests/test_autospawn.py::test_do_spawn_resets_spawn_retry_count` — **PASSED**.
  - **Todo 3** (`_tick_once()` reorder + docstring/alert-text fix, claimed `agent-orchestrator@bc37d03` +
    `agent-orchestrator@53492cb`): both commits exist, both ancestors of origin. `bc37d03`'s diff confirms the
    daily-kill-cap early-return moved to sit only ahead of the `active_slots` reap loop (after orphan-session reclaim +
    the 5 reclaim/reconcile calls), the stale "default 20" docstring corrected to "default 50" (2 locations), and an
    inline comment documenting the kept-vs-gated rationale. `53492cb`'s diff confirms `notify_watchdog_kill`'s cap-hit
    alert text reworded to disclose "The WorkerLivenessWatchdog's 5 kill triggers are dormant" (matching
    `notify_watchdog_dormant`'s existing phrasing) and adds the specific named regression test. Re-ran it directly:
    `tests/test_worker_liveness_watchdog.py::test_tick_daily_cap_still_runs_orphan_session_reclaim` — **PASSED**.

  **Verdict: all 3 claims hold up under direct re-verification — no discrepancies, nothing re-opened.** Fleet git-status
  sweep of this slot's other repos (unified-api-contracts, agent-orchestrator, execution-service, strategy-service) also
  confirmed clean/ahead=0/behind=0 — the several queued "GIT STATUS RED"/urgent-fix nudges surfaced at this session's
  boot were all already resolved by earlier turns of this same session (the strategy-service `FILL_COMPLETED` qty/price
  key fix, `strategy-service@4b3f5b0c`, was independently confirmed already shipped and on origin before this todo
  started).

- **2026-08-08 (slot 23, `infra`, dispatch `ao_satellite_ao_dispatch_batch7_finalize-004`)**: Executed todo 3 —
  re-checked the conflict-gated declined item's named gate directly (not re-derived from scratch). Confirmed
  `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 18 is `[x]` at current HEAD, clearing the file-collision the
  item was parked on. Confirmed `RB-04f4f852` has cleared (absent from the live `GET /api/repo-blockers` open list).
  Read the gated source doc directly (`agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`) and found both its
  gated item AND the doc's RB-04f4f852-blocked item were already shipped once the gates cleared — the doc reached zero
  open todos and was independently archived 2026-08-07 by an unrelated `check_archive_candidates` ratchet pass, before
  this finalize plan's sequential drain ever reached todo 3. No batch-8 spin-off item is warranted — the work the gate
  was protecting is already done and shipped, not merely eligible to be scheduled.
