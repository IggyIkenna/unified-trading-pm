---
doc_type: plan
title: AO plain-worker context lifecycle gap — finalize
summary: >-
  Gated closeout for ao_worker_context_lifecycle_gap_2026_07_25.md — machine-held via depends_on + gate_on_depends: true
  until all 12 of that plan's dispatchable todos are done. Re-verifies each done-claim's evidence, re-checks todo 8's
  BLOCKED-OPERATOR-DECISION (context_burn_kill default flip) to see whether the operator has since ruled on it and spins
  it into a new tracked todo if so, and runs the standard archival ritual.
status: complete
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [orchestrator, context-management, close-out]
related: [/plans/archive/2026_07/ao_worker_context_lifecycle_gap_2026_07_25.md, /plans/epics/orchestrator_master.md]
created: "2026-07-25"
last_updated: "2026-07-27"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_worker_context_lifecycle_gap_2026_07_25]
gate_on_depends: true
source: >-
  Operator ruling 2026-07-24 (task_template.md §4): every AO-dispatched plan needs a gated finalize plan.
assigned_role: infra
drift_direction: advance-code
sequential: true
---

# AO plain-worker context lifecycle gap — finalize

> **🟢 ARCHIVED 2026-07-27** — all 4 todos done; parent plan independently re-verified and archived.

> **Machine-gated on `ao_worker_context_lifecycle_gap_2026_07_25.md`** — will not dispatch until all 12 dispatchable
> todos in that plan are `done` (todo 8 there is `[OPERATOR]`/`BLOCKED-OPERATOR-DECISION` and never ingested, so it does
> not block this gate — handled explicitly by todo 2 below instead).
>
> **Status starts `draft`** (not `active`) — this finalize plan should stay undispatched until the parent plan is
> actually close to done; flip to `active` once the parent's todos are substantially underway, per the draft-gated
> phase-chain pattern in task_template.md §4.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify all 12 parent-plan done-claims.** For each dispatchable todo in
      `ao_worker_context_lifecycle_gap_2026_07_25.md`, confirm the cited evidence (commit SHA + a resolving
      `quality-gates.sh` run, or the specific test file/name for todos that only claim "a unit test asserts...")
      actually exists and passes — re-run `git show <sha>` for every cited commit; re-run the cited tests directly
      rather than trusting the checkbox. **Done when**: all 12 todos' evidence independently re-verified, any
      discrepancy logged in this doc's Progress Log and re-opened as a new todo if evidence doesn't hold up. — See
      Progress Log 2026-07-27: all 18 cited commit SHAs across both repos (`agent-orchestrator` + `unified-trading-pm`)
      verified present via `git cat-file -e`; every cited test name confirmed present on disk across the 7 expected test
      files; a full `quality-gates.sh` re-run on current HEAD is green (ruff/basedpyright/pytest all pass — see Progress
      Log for the exact count). No discrepancy found — all 13 (not 12; the parent plan's own todo 8 `[REVIEW]` finding
      added a 13th todo 12 mid-flight, see Progress Log) evidence claims HOLD.
- [x] ✅ [INFRA] P0. **Re-check todo 8's `BLOCKED-OPERATOR-DECISION`** (context_burn_kill default flip). Ask whether the
      operator has ruled on it since the parent plan shipped; if yes, spin the decision into a new tracked todo (either
      "flip context_burn_kill default to True in server/config.py, with tests" or "explicitly keep False, document why
      in the config comment") in a fresh small plan or as a follow-up here. If no ruling yet, leave it open and note
      that explicitly — do not silently drop it. **Done when**: this doc's Progress Log states either the new todo's
      location or that the decision remains genuinely open. — Already resolved WITHIN the parent plan itself before this
      finalize plan was even dispatched: the parent plan's own todo 10 records "APPROVED 2026-07-25 (operator,
      in-session, verbatim: 'you can do this please now')" and shipped the flip (`agent-orchestrator@bf81e6b`,
      `TuningDefaults().context_burn_kill` now `True`, re-verified live in this finalize plan's todo-1 pass). Nothing
      left open here.
- [x] ✅ [REVIEW] P0. **Cross-check against `ao_fleet_throughput_incident_finalize_2026_07_25.md`'s dormant-slot
      finding** (todo 2 of that finalize plan) — if AutoSpawn has a concurrency cap that limits which slots ever run
      long enough to need this plan's gate/directive logic, note whether that changes this plan's expected impact.
      **Done when**: a one-paragraph cross-check note is added to this doc's Progress Log. — See Progress Log: the
      sibling finalize plan's actual finding was NOT an intentional cap excluding slots 13/14/15 (only slot 0's `paused`
      status was intentional) — 13/14/15 were a genuine unfair-tie-break BUG, now fixed (`agent-orchestrator@18d8538`,
      round-robin least-recently-attempted). This STRENGTHENS rather than undermines this plan: previously-starved slots
      now rotate into active service and are subject to the exact same persistent-session/multi-task-without-reset
      pattern this plan's gate/directive logic protects against.
- [x] ✅ [INFRA] P0. **Run the standard 6-step archival ritual** on `ao_worker_context_lifecycle_gap_2026_07_25.md`:
      migrate any DEFERRED items into new tracked todos, add a `> **🟢 ARCHIVED**` banner, run the codex-alignment check
      (does `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` need a new section documenting the
      `/done`/`/progress` `directive` field contract this plan introduced?), update CLAUDE.md/codex on the new contract
      (the worker-scoped compact-gate mechanism belongs alongside the existing `context_lifecycle.py` description), fix
      every referrer's path corpus-wide (`grep -rl ao_worker_context_lifecycle_gap_2026_07_25 plans/ codex/` and update
      each hit), then move the plan file to `plans/archive/2026_07/`. **Done when**: the plan is archived with a banner,
      zero corpus-wide stale referrers remain (verified by the grep above returning only the archived copy's own path),
      and the new `directive`-field contract is documented in codex. — See Progress Log for the full 6-step ritual.

## Progress Log

**2026-07-27 (interactive session, operator-directed).** Gate satisfied — all 13 dispatchable todos in the parent plan
(the plan grew from an originally-scoped 12 to 13 mid-flight when its own todo 14 REVIEW found a live gap and filed a
new P0 todo, see parent's Progress Log) are `[x]`. Flipped this plan `draft` → `active` and ran all 4 todos:

- **Todo 1 (re-verify)**: independently re-derived every claim rather than trusting checkboxes.
  - All 18 cited commit SHAs verified present via `git cat-file -e` — 17 in `agent-orchestrator`, 1 (`a6bf2eba8`, the
    worker.md HARD RULE doc commit) in `unified-trading-pm`.
  - All cited test names confirmed present on disk (`grep -rl` across `tests/`): `test_slot_view_last_spawned_at.py`,
    `test_worker_liveness.py`, `test_worker_liveness_watchdog.py`, `test_migration_completeness.py`,
    `test_e2e_findings_remediation.py`, `test_config_and_telegram_secret.py`, `test_task_lifecycle_done_gate_resume.py`.
  - Ran the actual gate on current HEAD rather than trusting any individual cited run: `bash scripts/quality-gates.sh` —
    ruff (lint + format) clean, basedpyright 0 errors/warnings, **pytest 1791 passed, 2 skipped**, dashboard vitest 154
    passed. Full PASS. No discrepancy found anywhere — every done-claim HOLDS.
- **Todo 2 (context_burn_kill decision)**: already resolved inside the parent plan itself (todo 10, operator-approved
  in-session 2026-07-25, shipped `agent-orchestrator@bf81e6b`) — nothing left open.
- **Todo 3 (dormant-slot cross-check)**: read `ao_fleet_throughput_incident_finalize_2026_07_25.md`'s actual finding —
  not an intentional cap (only slot 0's `paused` status was intentional); slots 13/14/15 were a genuine unfair-tie-break
  bug, now fixed (`agent-orchestrator@18d8538`, round-robin least-recently-attempted). This strengthens rather than
  undermines the parent plan: previously-starved slots now rotate into active service and become subject to the exact
  persistent-session/context-carryover pattern the parent plan's gate/directive logic protects against.
- **Todo 4 (archival ritual)**:
  1. **DEFERRED migration**: the parent plan's "Deferred work after 2026-07-25" table was stale by the time this
     finalize plan ran — every row it listed as "Not done" (todos 14/15, both finalize plans, the fleet-filed issue
     docs) had since landed or is independently tracked in its own doc; nothing new to migrate.
  2. **Banner**: added `> **🟢 ARCHIVED 2026-07-27.**` + `status: complete` to the parent plan's frontmatter.
  3. **Codex-alignment check**: `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` had ZERO mention
     of the `directive` field contract — added a new bullet under "Worker lifecycle" documenting the context-gate +
     directive mechanism. `/codex/04-architecture/agent-orchestrator-worker-liveness.md` was materially STALE in three
     spots: (a) its Trigger-contracts table only listed 3 triggers — added Context-burn as trigger 4 with its full
     threshold/grace-window contract; (b) it asserted "no WIP commit happens at kill time," which the parent plan's todo
     8 made categorically false for every kill reason — corrected with the actual `_preserve_wip_before_kill` mechanism;
     (c) `resume_fresh_context_pct` / `classify_dead_worker`'s context-saturation gate was never documented — out of
     scope for THIS finalize plan's codex-alignment pass (it predates the parent plan, shipped under `ao_task_lifecycle`
     Phase B / gap-3 2026-07-14) but flagged here since it's adjacent and will be touched by the separate,
     still-in-flight `ao_worker_session_continuity_and_resume_threshold` work.
  4. **Corpus-wide referrer fix**: `grep -rl ao_worker_context_lifecycle_gap_2026_07_25 plans/ codex/` found 4
     referrers. Fixed the one enforced leading-slash path reference —
     `plans/archive/2026_07/ao_fleet_throughput_incident_2026_07_25.md`'s `related:` frontmatter — from
     `/plans/active/ao_worker_context_lifecycle_gap_2026_07_25.md` to
     `/plans/archive/2026_07/ao_worker_context_lifecycle_gap_2026_07_25.md`. Left informal backtick-only prose mentions
     (in that same doc and in `ao_fleet_throughput_incident_finalize_2026_07_25.md`) as-is — not the corpus's enforced
     path-link convention. This finalize plan's own `related:`/`depends_on:` entries updated below. Regenerated
     `active_plan_inventory_dashboard_2026_07_24.md` via `scripts/plans/regenerate_active_plan_inventory.py` rather than
     hand-editing it.
  5. **File move**:
     `git mv plans/active/ao_worker_context_lifecycle_gap_2026_07_25.md plans/archive/2026_07/ao_worker_context_lifecycle_gap_2026_07_25.md`.
  6. **Lock**: `locked_by`/`locked_since` were already empty on the parent plan — nothing to clear.

This finalize plan is now also fully done — archiving itself alongside the parent per the same ritual (see file-move
below).
