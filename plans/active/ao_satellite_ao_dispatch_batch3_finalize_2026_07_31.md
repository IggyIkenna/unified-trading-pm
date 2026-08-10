---
doc_type: plan
title: AO satellite AO batch 3 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch3_2026_07_31.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc(s)
  (the batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether either
  Deferred item's gate has since cleared, archives the source docs that reach zero open todos, and runs the standard
  6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-3, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch3_2026_07_31]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-07-31 (scheduled dispatch agt-23935a). Ships
  `status: active` (not draft) per the skill's 2026-07-30 finding: gate_on_depends already machine-holds every task
  until the batch's own todos are done, so a second draft-gate is a redundant, easy-to-forget manual flip.
---

# AO satellite AO batch 3 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [ ] [REVIEW] P0. **Re-verify every batch-3 done-claim against reality, not against its checkbox** — for each of the 3
      todos in `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`, re-run `git show --stat <sha>` for every
      cited commit and re-run the specific named test(s) directly rather than trusting the claim, and re-run each todo's
      own stated done-when check where it is a command (the `generate_context_scope_inventory.py` zero-remaining check,
      the priority-inversion replay test, the orphan-verifier's 10-verdict reproduction + the liveness discriminator's
      slot-5/slot-15 shape checks + the 25-ref wip-preserve disposition table). **Done when**: all 3 verified, and any
      claim whose evidence does not hold up is re-opened as a new tracked todo in this doc's Progress Log with the
      discrepancy stated.
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)** — batch
      3 was an extraction, so the source-doc items it covers are the ones that go stale, not the batch's. Flip the
      specific todo(s) in each of: `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md` (its `[SCRIPT] P0`
      item), `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md` (both its `[BACKEND] P2` and
      `[SCRIPT] P3` items), `orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md` (both its `[SCRIPT] P2` items
      plus its `[DATA] P3` item), and `wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its own `[DATA] P3` item —
      the duplicate this batch folded in, so it flips in lockstep with `orphaned_commit_recovery`'s `[DATA] P3`, not
      independently). **Done when**: every one of those flips is committed with the `docs(plans):` prefix and cites the
      real commit sha (or, for the read-only verification items, the reproduction evidence).
- [ ] [INFRA] P0. **Re-check both Deferred-bucket items' gates and spin any newly-cleared ones into batch 4** — for
      `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`'s `[REVIEW] P3` item, re-check whether it has
      since been scoped into its own dedicated plan (e.g. via `/plan-brainstorm`) — if so, mark this batch's Deferred
      entry resolved-elsewhere; if not, leave it deferred with the same reasoning. For
      `omniroute_llm_gateway_pilot_design_2026_07_30.md`, re-check whether the operator has since lifted the explicit
      NA/human-only ruling — if lifted, its 5 bounded `[INFRA]`/`[BACKEND]` todos become batch-4 material; if not, leave
      it deferred. Also re-check the data-correctness finding parked in
      `/plans/archive/issues/ag_closeout_audit_ao_parked_2026_07_31.md` (the false "backfill already done" claim in
      `context_scope_consumption_enforcement_2026_07_30.md`) — confirm whether it has been corrected; if not, escalate
      again rather than letting it go stale a second time. **Done when**: each of the 3 items is marked
      cleared-and-moved (naming the new batch-4 plan/todo or the resolving plan) or still-gated with the current reason
      — no entry left unstated.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** At minimum
      re-check `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`,
      `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md`,
      `orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md` (likely still has open non-batched items — check
      before archiving), and `wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its 2 `[SCRIPT] P3` items are still
      deferred judgment calls — do not archive if so). Run the standard 6-step archival ritual (migrate any DEFERRED
      item → banner → codex-alignment check → update CLAUDE.md/codex if a contract changed → fix every referrer's path
      corpus-wide → clear the lock) on any doc that IS fully done. **Done when**: `grep -rl <slug> plans/ codex/`
      returns only the archived copy's own path for each archived doc, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero hard failures.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`, migrate any still-Deferred item into batch 4 (never
      leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_07/`, fix
      every corpus-wide referrer including this finalize plan's own `related:`/ `depends_on:`, then run
      `.venv/bin/python scripts/plan-hygiene/regenerate_active_plan_inventory.py`. **Done when**: the batch plan is
      archived with a banner, the inventory regenerates with an orphan count of 0, and `check_finalize_plan_coverage.py`
      no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-07-31** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode, scheduled
  dispatch agt-23935a). `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile →
  re-check gates → archive sources → archive self) and several touch the same files. Ships `status: active` per the
  skill's 2026-07-30 finding (`gate_on_depends` already holds every task; no separate draft-gate needed).
- **context-scout 2026-08-01**: verified the 3 pre-existing context_scope entries still resolve and are relevant (kept
  in place), added the gated parent batch plan as a 4th entry — refreshed (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — still the correct archival SSOT + batch pointer;
  no change needed. Gated finalize doc, no source path.
