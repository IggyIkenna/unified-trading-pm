---
doc_type: plan
title: AO satellite AO batch 9 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch9_2026_08_08.md — machine-held via depends_on + gate_on_depends until
  that batch's single todo is done. Reconciles the verified todo's evidence back into
  `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s own checkboxes, archives that doc once fully closed (it
  has no other open items beyond the 2 this batch covers), and runs the standard 6-step archival ritual on the batch
  plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-9, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md,
    /plans/active/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch9_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`'s own todo 3. Ships `status:
  active` (not draft) per the skill's 2026-07-30 finding: `gate_on_depends` already machine-holds every task until the
  batch's own todo is done, so a second draft-gate is redundant — only the batch itself needs `status: draft` + explicit
  operator approval.
---

# AO satellite AO batch 9 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until that batch's sole todo is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [ ] [REVIEW] P0. **Re-verify batch9's done-claim against reality, not against its checkbox** — re-run
      `git show --stat <sha>` for the cited commit(s), re-run the specific named regression test, and re-check the
      14:30-16:30Z recurrence-timing question was actually answered (not left as a TODO inside the todo). **Done when**:
      the claim is verified, and any discrepancy is re-opened as a new tracked todo here with the discrepancy stated.
- [ ] [REVIEW] P0. **Reconcile the verified todo's evidence into
      `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s own 2 remaining checkboxes** (`[DOCS] P1` and
      `[BACKEND] P2`), flipping both with the real commit sha(s). **Done when**: both flips are committed with the
      `docs(plans):` prefix and cite the real commit sha.
- [ ] [REVIEW] P0. **Archive `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`** once both its checkboxes are
      flipped (it has no other open items) — run the standard 6-step archival ritual (banner, codex-alignment check, fix
      every referrer's path corpus-wide, clear the lock). **Done when**:
      `grep -rl review_role_boot_read_unconfirmed_stuck_loop plans/ codex/` returns only the archived copy's own path.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch9_2026_08_08.md`, move to `plans/archive/2026_08/`, fix every
      corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py --commit` (verify the exact entrypoint name at
      execution time). **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly, and
      `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips).

## Progress Log

- **2026-08-08** — Authored in the same turn as its batch by `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`'s
  own todo 3 (dispatch `ao_satellite_ao_dispatch_batch6_finalize-002`, slot 27, infra craft). `sequential: true` since
  the 4 todos are a genuine chain (verify → reconcile → archive source → archive self). Ships `status: active` per the
  skill's 2026-07-30 finding (`gate_on_depends` already holds every task; no separate draft-gate needed).
