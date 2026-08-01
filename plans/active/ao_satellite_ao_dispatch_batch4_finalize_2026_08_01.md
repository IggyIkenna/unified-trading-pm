---
doc_type: plan
title: AO satellite AO batch 4 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch4_2026_08_01.md — machine-held via depends_on + gate_on_depends until
  the batch's sole todo is done. Reconciles the completed todo's evidence back into its TRUE source issue doc (the batch
  was an extraction, so the source doc's own checkbox is the one that goes stale), archives the source doc if it reaches
  zero open todos, and runs the standard 6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-4, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch4_2026_08_01.md,
    /plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch4_2026_08_01]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch4_2026_08_01.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored
  2026-08-01 alongside the batch4 rename/correction (this pair was originally missing — the doc that became batch4 was
  drafted without its finalize twin during the prior session's finalize pass). Ships `status: active` (not draft) per
  the same 2026-07-30 finding batch3_finalize applied: `gate_on_depends` already machine-holds every task until the
  batch's own todo is done, so a second draft-gate is a redundant, easy-to-forget manual flip.
---

# AO satellite AO batch 4 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch4_2026_08_01.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until that plan's sole todo is `done`. No separate `status` flip needed
> either way (mirrors batch3_finalize's convention).

## Todos

- [ ] [REVIEW] P0. **Re-verify batch-4's done-claim against reality, not against its checkbox** — for the sole todo in
      `/plans/active/ao_satellite_ao_dispatch_batch4_2026_08_01.md`, re-run `git show --stat <sha>` for the cited commit
      and re-run the specific named test(s) directly rather than trusting the claim, and re-run the todo's own stated
      done-when check (the silent-but-alive-owner simulation test). **Done when**: verified, and if the evidence does
      not hold up, re-opened as a new tracked todo in this doc's Progress Log with the discrepancy stated.
- [ ] [REVIEW] P0. **Reconcile the verified todo's evidence back into its TRUE source doc's own checkbox** — batch 4 was
      an extraction, so `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`'s `[BACKEND] P2` item is
      the one that goes stale, not the batch's. Flip it with the real commit sha. **Done when**: the flip is committed
      with the `docs(plans):` prefix and cites the real commit sha.
- [ ] [INFRA] P0. **Confirm the file-adjacency caution against `batch3_2026_07_31.md`'s todo 2 was actually respected**
      — check whether batch 4's todo landed before or after batch3's todo 2, and whether the two diffs conflicted in
      `agent-orchestrator/server/worker_liveness_watchdog.py` (or wherever they actually landed). If a real collision
      occurred despite the sequencing note, record what happened and whether a follow-up cleanup is needed. **Done
      when**: the actual landing order and any conflict outcome is recorded here.
- [ ] [REVIEW] P0. **Archive the source doc if it has reached zero open todos, and repoint any referrer.** Check
      `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` — its P3 `/done`-idempotency sibling is
      separately file-collision-held (not part of this batch), so do NOT archive if that item is still open there. Run
      the standard 6-step archival ritual (banner → codex-alignment check → fix every referrer's path corpus-wide →
      clear the lock) only if the doc is genuinely fully done. **Done when**: `grep -rl <slug> plans/ codex/` returns
      only the archived copy's own path if archived, or a stated reason it wasn't.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch4_2026_08_01.md`, move the file to `plans/archive/2026_08/`, fix
      every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py`. **Done when**: the batch plan is archived
      with a banner, the inventory regenerates with an orphan count of 0, and `check_finalize_plan_coverage.py` no
      longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-08-01** — Authored alongside the batch2→batch4 rename/correction. This pair was originally missing its finalize
  twin (the prior session's finalize pass drafted the batch but not its gate); added now to close that gap before
  dispatch, mirroring batch3_finalize's `sequential: true` / `status: active` (not draft) convention. Only 4 todos, not
  5, since batch4 carries a single todo (the dirty-sweep item was dropped as moot before this pair was even finalized) —
  no separate "re-check Deferred gates" todo is needed since this batch's own Deferred-derivation chain ends here
  (batch4 was itself already a Deferred-gate re-check of batch1; it named no further Deferred items of its own to
  re-check).
- **context-scout 2026-08-01**: verified the 3 pre-existing context_scope entries still resolve and are relevant (kept
  in place), added the gated parent batch plan as a 4th entry — refreshed (4 entries).
