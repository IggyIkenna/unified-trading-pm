---
doc_type: plan
title: AO fleet throughput incident — finalize
summary: >-
  Gated closeout for ao_fleet_throughput_incident_2026_07_25.md — machine-held via depends_on + gate_on_depends: true
  until all 3 of that plan's todos are done. Re-verifies each done-claim's cited evidence still resolves, checks whether
  todo 2's dormant-slot finding changes anything about the companion ao_worker_context_lifecycle_gap_2026_07_25.md plan
  (a fixed AutoSpawn cap/backoff could change how many slots are ever candidates for the context-gate logic that plan
  ships), and runs the standard archival ritual.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [orchestrator, autospawn, incident, close-out]
related: [/plans/archive/2026_07/ao_fleet_throughput_incident_2026_07_25.md, /plans/epics/orchestrator_master.md]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_fleet_throughput_incident_2026_07_25]
gate_on_depends: true
source: >-
  Operator ruling 2026-07-24 (task_template.md §4): every AO-dispatched plan needs a gated finalize plan.
assigned_role: infra
drift_direction: advance-code
sequential: true
---

# AO fleet throughput incident — finalize

> **Machine-gated on `ao_fleet_throughput_incident_2026_07_25.md`** — will not dispatch until all 3 of that plan's todos
> are `done`.

## Todos

- [x] ✅ [REVIEW] P1. **Re-verify all 3 parent-plan done-claims.** For each of
      `ao_fleet_throughput_incident_2026_07_25.md`'s 3 todos, confirm the cited evidence (commit SHA, Slack message, or
      activity-log entry) actually resolves — re-run `git show <sha>` for any cited commit and re-check any cited
      activity-log/Slack evidence still exists. **Done when**: all 3 todos' evidence independently re-verified,
      discrepancies (if any) logged in this doc's Progress Log. — VERIFIED 2026-07-25T05:45Z (slot 10, review), all 3
      hold. See Progress Log for full evidence.
- [x] ✅ [INFRA] P1. **Cross-check todo 2's dormant-slot finding against
      `ao_worker_context_lifecycle_gap_2026_07_25.md`.** If the parent plan's audit found slots 13/14/15/0 dormant due
      to an intentional AutoSpawn concurrency cap (not a bug), confirm that cap doesn't undermine the context-lifecycle
      plan's assumption that all working slots are reachable by its new gate/directive logic — if the cap means some
      slots never actually run long enough to accumulate the cross-task context carryover this plan complex was built
      for, note that explicitly (informational, not a required code change). **Done when**: a one-paragraph cross-check
      note is added to this doc's Progress Log.
- [x] ✅ [INFRA] P2. **Run the standard 6-step archival ritual** on `ao_fleet_throughput_incident_2026_07_25.md`:
      migrate any DEFERRED items into new tracked todos, add a `> **🟢 ARCHIVED**` banner, run the codex-alignment check
      (does any `/codex/05-infrastructure/vm-launcher-runbook.md` or orchestrator-alerting doc need updating given todo
      1's alert-verification findings?), update CLAUDE.md/codex on any new contract discovered (e.g. if the dormant-slot
      audit revealed AutoSpawn's real concurrency target, that belongs in
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`), fix every referrer's path corpus-wide
      (`grep -rl ao_fleet_throughput_incident_2026_07_25 plans/ codex/` and update each hit), then move the plan file to
      `plans/archive/2026_07/`. **Done when**: the plan is archived with a banner, zero corpus-wide stale referrers
      remain (verified by the grep above returning only the archived copy's own path), and any real new contract found
      is reflected in codex.

## Progress Log

- **2026-07-25T05:45Z (slot 10, review)** — Todo 1: independently re-verified all 3 parent-plan done-claims. Did not
  trust the doc's prose — re-derived each from source.
  - **Todo 1 (branch-quarantine starvation alert)**: pulled `journalctl -u orchestrator.service` directly on the
    orchestrator host over the exact cited window (`04:25:00`-`04:55:00` UTC) and confirmed, byte-for-byte, all 3 cited
    fires: `slot-quarantine STARVATION alert fired: slot 4` at `04:33:26,682` with a paired
    `POST https://hooks.slack.com/services/.../g0ar1MMpTxruRkbLn2Xt4ZIT "HTTP/1.1 200 OK"` at the SAME timestamp; slot 5
    at `04:36:40,954`; slot 9 at `04:42:45,782` (same pattern). Escalation ids `agt-8ab986`/`agt-23b3a6` and the later
    auto-heal lines (slot 4 `04:45:24`, slot 5 `04:51:47`) also match exactly. **HOLDS.**
  - **Todo 2 (dormant-slot fix, `agent-orchestrator@18d8538`)**: `git show 18d8538` confirms the exact described change
    — a secondary `_last_attempt_at` tie-break added to the candidate sort in `_run_one_tick`, matching the doc's code
    excerpt verbatim. Confirmed `_last_attempt_at` is genuinely written (not a dead field) at 2 call sites. Rather than
    trust the cited "105/105 pass," bootstrapped the venv (`uv sync` — none existed in this slot's clone) and ran the
    actual gate: `bash scripts/quality-gates.sh` on current HEAD (`9c73579`, a descendant of `18d8538`) —
    ruff/basedpyright/pytest all green, **1645 passed, 1 skipped**, full suite. Isolated
    `tests/test_autospawn.py -k rotates` — 1 passed (of 105 collected total in that file, confirming the "105/105"
    figure exactly). **HOLDS.**
  - **Todo 3 (`check_doc_body_links` escalation wiring, `unified-trading-pm@3e4c73436`)**: `git show 3e4c73436` shows
    the exact 23-line additive diff to `.github/workflows/ldr-to-main-promote.yml` described — a `V2_FAILED` check
    dispatching `wall_type=ldr_main_qg_failure` on a concluded v2 failure for the exact head SHA, gated on
    `DRY_RUN!=true`, relying on the orchestrator's existing wall-cooldown dedup (no new cooldown logic added, matching
    the doc's claim that gap (b) didn't apply). **HOLDS.**
  - **Discrepancy noted (informational, not blocking)**: the parent plan (`ao_fleet_throughput_incident_2026_07_25.md`)
    actually lists a **4th** todo — `[REVIEW] P1 "Post-fix live re-verification against the same baseline"` — which is
    still `[ ]` unchecked. This finalize plan's own frontmatter
    (`depends_on: [ao_fleet_throughput_incident_2026_07_25]`, `gate_on_depends: true`) and this todo's brief both only
    reference "3 todos," and this task was dispatchable, so the gate evidently keyed off the 3 that predated the 4th
    being added rather than the plan's current total. Flagging rather than silently treating it as in-scope: the 4th
    todo asks for a live re-pull of `/api/state`/`/api/backlog`/`/api/activity`/`/api/escalations/active` to confirm
    fleet recovery toward the ~12/15 baseline — genuinely useful, still open, but OUT of this todo's declared "3 todos"
    scope. Left for whoever picks up the parent plan's remaining todo 4 (or a future finalize-plan revision) — not
    fabricated here since re-verifying "3" when the doc's real intent may have shifted to "4" is not this task's call to
    make unilaterally.

- **2026-07-25 (slot-12)** — Todo 2 (cross-check): todo 2's finding was NOT that slots 13/14/15/0 are excluded by an
  intentional cap (that was the plan's hypothesis going in) — the actual audit result was slot 0 alone is intentionally
  excluded (`status: paused`), while 13/14/15 were a genuine BUG (unfair ascending-slot_id tie-break under the
  `ORCHESTRATOR_FLEET_WORKER_CAP=8` fleet cap), now fixed (`agent-orchestrator@18d8538`) with a round-robin
  least-recently-attempted tie-break. This does NOT undermine `ao_worker_context_lifecycle_gap_2026_07_25.md`'s
  assumption — if anything it STRENGTHENS the case for that plan: previously-starved high-numbered slots (13/14/15) now
  also rotate INTO active service and accumulate the same persistent-session, multi-task-without-reset pattern the
  context-lifecycle plan's gate/directive logic protects against, rather than sitting permanently idle and exempt from
  it. The fleet cap itself (8 concurrent workers) is unchanged and still bounds how many slots run AT ONCE, but which
  slots take turns is now fair — so the context-gate logic's reach (every currently-dispatched slot, regardless of
  slot_id) is unaffected by the fix; it was never scoped to "only the historically-busy slots" in the first place.

- **2026-07-25T06:14Z (slot-12)** — Todo 3 (archival ritual). Parent plan's own 4th todo (post-fix re-verification,
  flagged as an out-of-scope discrepancy above) was completed first (`unified-trading-pm@4590a5f00` — partial throughput
  recovery confirmed, (b)/(c)/(d) genuinely not-yet-observable rather than failed, no regressions in any of the 3
  shipped fixes) so the archival below reflects the plan's true FULL completion, not just the stale "3 todos" the gate
  keyed off.
  1. **DEFERRED migration**: none found — the parent plan carries no `DEFERRED` items or a "Deferred work" section.
  2. **Banner**: added `> **🟢 COMPLETE 2026-07-25 — ARCHIVED.**` to the plan body + `status: complete` in frontmatter
     (matching the `ao_config_env_var_consolidation_2026_07_18.md` precedent pattern).
  3. **Codex-alignment check**: two real gaps found and closed —
     `/codex/04-architecture/agent-orchestrator-autospawn.md` had NO section documenting slot candidate ordering at all
     (only the budget-SIZE contract, not WHICH slots get picked) — added a new "Slot candidate ordering — round-robin
     fairness (2026-07-25)" section describing the `_last_attempt_at` tie-break fix and its scope (doesn't change the
     fleet cap, only fairness among equally-eligible idle slots).
     `/codex/04-architecture/agent-orchestrator-alerting.md` documented `notify_slot_quarantined` without the
     `count_queued_walls()`-is-escalation-only caveat — added, cross-linked to the P2 issue doc.
     `/codex/05-infrastructure/vm-launcher-runbook.md` checked — no relevant content to touch (todo 1's finding was
     alerting-scoped, not VM-launcher-scoped; correctly out of that doc's remit).
  4. **Corpus-wide referrer fix**: `grep -rl ao_fleet_throughput_incident_2026_07_25 plans/ codex/` found 6 referrers.
     Fixed the 3 with a leading-slash `/plans/active/...` PATH reference (`related:`/`source:` frontmatter arrays in
     `ao_worker_context_lifecycle_gap_2026_07_25.md`, this finalize plan, and
     `issues/branch_quarantine_alert_blind_to_backlog_queue_2026_07_25.md`) to
     `/plans/archive/2026_07/ao_fleet_throughput_incident_2026_07_25.md`. Left the bare-slug `depends_on:` field on this
     finalize plan's own frontmatter untouched (machine-parsed bare slug, explicitly out of scope per
     `cross-reference-path-convention.md`) and left informal backtick-only prose mentions (no leading slash) as-is —
     neither is the corpus's enforced path-link convention. `active_plan_inventory_dashboard_2026_07_24.md`'s stale row
     was NOT hand-edited — regenerated via `scripts/plans/regenerate_active_plan_inventory.py` instead (180 plans, 0
     orphans post-regen).
  5. **File move**:
     `git mv plans/active/ao_fleet_throughput_incident_2026_07_25.md plans/archive/2026_07/ao_fleet_throughput_incident_2026_07_25.md`.
  6. **Lock**: `locked_by`/`locked_since` were already empty on the parent plan — nothing to clear.
