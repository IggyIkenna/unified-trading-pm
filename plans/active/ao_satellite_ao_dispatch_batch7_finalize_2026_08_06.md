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
    /plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
    /plans/active/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
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

- [ ] [REVIEW] P0. **Re-verify every batch-7 done-claim against reality, not against its checkbox** — for each of the 3
      todos in `/plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md`, re-run `git show --stat <sha>` for every
      cited commit and re-run the specific named test(s)/verdict directly rather than trusting the claim (todo 1's
      done-when is a written verdict + evidence, not a commit — check the source doc's Progress Log entry exists and the
      raw per-task metrics are actually present, not just asserted). **Done when**: all 3 verified, and any claim whose
      evidence does not hold up is re-opened as a new tracked todo in this doc's Progress Log with the discrepancy
      stated.
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)** — batch
      7 was an extraction, so the source-doc items it covers are the ones that go stale, not the batch's. Flip the
      specific todo(s) in each of:
      `/plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md` (its first 2 items — leave
      its 3rd item, the unscoped circuit-breaker fork, untouched) and
      `/plans/active/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md` (its 1st + 2nd items — leave its
      3rd item, the operator-decision ask, untouched). **Done when**: both flips are committed with the `docs(plans):`
      prefix and cite the real commit sha(s).
- [ ] [INFRA] P0. **Re-check whether the 1 conflict-gated declined item's named gate has cleared since 2026-08-06, and
      spin it into batch 8 if so.** The gated item: `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`'s 1st item
      (LDR-triggered `quality-gates-v2` template extension) was parked because it targets the same files as
      `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 18. Check whether that sibling plan's todo 18 has since
      landed (and if so, whether it already covers the `ci_trigger_branch`-style parameterization this item needs, or
      leaves a residual gap worth its own todo) — per this skill's iterative-drain methodology, re-check the SPECIFIC
      named gate, don't re-derive the classification from scratch. Also spot-check whether `RB-04f4f852` (blocking that
      same source doc's 3rd item) has cleared. **Done when**: the item is marked cleared-and-moved (naming the new
      batch-8 plan/todo) or still-gated with the current reason — no entry left unstated.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** Re-check
      both source docs named in todo 2 above for whether their OTHER (non-batched, deferred) items are also closed
      before archiving — `ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`'s 3rd item and
      `ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`'s 3rd item are NOT covered by this batch and must keep
      either doc open if still unresolved. Run the standard 6-step archival ritual (migrate any DEFERRED item → banner →
      codex-alignment check → fix every referrer's path corpus-wide → clear the lock) on any doc that IS fully done.
      **Done when**: `grep -rl <slug> plans/ codex/` returns only the archived copy's own path for each archived doc,
      and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero NEW hard failures (compare against the
      baseline recorded at this finalize plan's authoring time).
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
