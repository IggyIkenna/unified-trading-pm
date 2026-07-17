---
doc_type: issue
title:
  "AO residuals surviving ao_dispatch_hardening's archival — the four items that had no other home, plus the l2_book
  reopen that did not hold"
summary: |
  `ao_dispatch_hardening_2026_07_16` archived 2026-07-17 with every phase complete. Its two Deferred tables listed 16
  items; most already live in a named issue doc or plan, and those are NOT duplicated here. This doc is the home for the
  four that had nowhere to go — the `/api/escalate` vs `/api/escalation/{id}` name collision, the backlog-relations UI
  awaiting a design, `ORCHESTRATOR_DB_PATH` being absent from `.env.local`, and the never-root-caused 2026-07-12
  degradation onset — so archiving the parent does not orphan them. It also records a NEW finding made during that
  archival: the two false-`done` l2_book rows that infra slot-2 reopened on 2026-07-17 and verified "STUCK" are now
  ABSENT from the DB entirely, while their plan todos are still `- [ ]` on an ingested plan. Absent is not lying, but it
  is not tracked either, and the reopen's own verification no longer holds.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, backlog, escalation, observability, orphaned-todos, tracking-index]
related:
  [
    ../../archive/2026_07/ao_dispatch_hardening_2026_07_16.md,
    backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    regen_positional_task_ids_not_content_stable_2026_07_17.md,
    ao_backlog_prune_gcs_wrong_db_2026_07_17.md,
    ../escalation_pipeline_mvp_2026_06_25.md,
    ../../epics/orchestrator_master.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on:
source:
  - "ao_dispatch_hardening_2026_07_16 Deferred tables (2026-07-16 + 2026-07-17), at its archival. Only the items with NO
    other home are carried here; the rest cite their existing owner and are deliberately not duplicated."
  - "Live DB probe 2026-07-17T13:57Z (/var/lib/orchestrator/state.db) — the l2_book finding below."
---

# AO residuals after `ao_dispatch_hardening` archived

> **Why this doc exists.** The parent plan is complete and archived. Its Deferred tables were the only tracking for a
> handful of items. Rather than leave an archived doc as their home — the mistake
> [`ao_autospawn_role_blind_dispatch_starvation_2026_07_14`](../../archive/issues/ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md)
> records in its own banner, which orphaned two live bugs for two days — the homeless ones move here. **Nothing is
> duplicated**: items that already have an owner are listed in § Already homed with a pointer only.

## Already homed — do NOT re-track here

| Deferred item                                        | Its actual home                                                                                                                                                                           |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reopen the 2 false-`done` rows                       | **DONE** by infra slot-2 2026-07-17 — but see todo 5 below, it did not hold                                                                                                               |
| Unauditable `done` rows (`brief_hash` NULL)          | [`regen_positional_task_ids_not_content_stable_2026_07_17`](regen_positional_task_ids_not_content_stable_2026_07_17.md) todo 1                                                            |
| Durable park for fleet-skipped tasks (the CODE half) | [`ao_skip_blind_spawn_budget_phantom_churn_2026_07_15`](ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md) (1 open todo)                                                             |
| Sports durable park (the OPERATIONAL half)           | **MOOT 2026-07-17** — `-002` no longer exists, `-001` is `done`; sports dispatching normally                                                                                              |
| `escalation_pipeline_mvp` un-pause                   | [`escalation_pipeline_mvp_2026_06_25`](../escalation_pipeline_mvp_2026_06_25.md) (`status: paused`, operator ruling)                                                                      |
| Recovery-audit Layer-1 producer rewire               | [`ao_recovery_audit_layer1_deleted_2026_07_15`](ao_recovery_audit_layer1_deleted_2026_07_15.md)                                                                                           |
| Staleness UI + alerting; audit hosts for freeze      | [`ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16`](ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md) — **another agent owns the UI half** (operator, 2026-07-16) |
| uv-cache reconcile; 30G reclaim; `UV_CACHE_DIR`      | [`ao_host_disk_pressure_2026_07_16`](../ao_host_disk_pressure_2026_07_16.md) — closed + its own Deferred table                                                                            |
| Deep `plan-reconciler`; capability_wizard            | their own issue docs (unchanged by the parent's archival)                                                                                                                                 |

## Todos

- [ ] [BACKEND] P2. **Resolve the `/api/escalate` vs proposed `/api/escalation/{id}` name collision — BEFORE any
      escalation code is written.** Two unrelated concepts one character apart: `/api/escalate` already exists and is
      the **GHA→orchestrator CI-wall judgment dispatch**; the proposed `/api/escalation/{id}` is **operator
      escalation**. Whoever implements the second without noticing the first will either collide on the route or, worse,
      wire operator escalations into the CI judgment path. **Gate**: one of the two is renamed, or a recorded decision
      says why the near-collision is acceptable, cited from
      [`escalation_pipeline_mvp_2026_06_25`](../escalation_pipeline_mvp_2026_06_25.md). Blocked-by: that plan is
      `status: paused` on an operator ruling — this only needs doing if/when it un-pauses.
- [ ] [BACKEND] P2. **`ORCHESTRATOR_DB_PATH` is set in the systemd unit but NOT in `.env.local`.** So any shell-run
      tooling on the VM resolves `config.db_path()` to the **empty in-repo DB** instead of
      `/var/lib/orchestrator/state.db` — a probe reports zeroes and looks like a healthy answer. This bit the 2026-07-17
      session **twice** while diagnosing the prune bug, and it is the same one-concept-two-places family as the
      `ORCHESTRATOR_DB_PATH`/`ORCHESTRATOR_REGEN_DB_PATH` drift that CAUSED that bug
      ([`ao_backlog_prune_gcs_wrong_db_2026_07_17`](ao_backlog_prune_gcs_wrong_db_2026_07_17.md)). **Gate**: a plain
      `.venv/bin/python -c "from server import config; print(config.db_path())"` on the VM, run as `ubuntu` with no env
      overrides, prints the live DB path.
- [ ] [BACKEND] P3. **Root-cause the 2026-07-12 degradation onset.** `worker_polling_dead` went **0 → 587** and the
      spawn:dispatch ratio **0.6:1 → 44:1** on that date. The churn itself is fixed (`f8ace1f`, proven on the live
      rate), but **why it started that day was never explained** — so a recurrence is invisible until it costs again.
      **Gate**: either a named cause with evidence from `activity_log`, or a recorded decision that the pre-fix window
      is not worth excavating now that the mechanism is closed — but not silence.
- [ ] [UI] P3. **Backlog-relations view.** Brief + real data + a 100-task synthetic fixture were handed to the design
      agent 2026-07-17 (`agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md`). **Cannot start until a design lands.**
      The model is a cross-cutting GRAPH, not a hierarchy — measured: 6 of 11 task→task edges cross plans, 1 condition
      gates 2 plans, 25/35 conditions gate nothing. A table cannot show that, which is why three table/tree attempts
      were rejected. Needs `GET /api/backlog/graph` behind it. **Gate**: design received → implemented → the relation a
      table cannot express (one prereq gating tasks in multiple plans) is visible in one view.
- [ ] [INFRA] P2. **NEW 2026-07-17 — the l2_book reopen did NOT hold, and its own verification says it did.**
      `backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16` records that infra slot-2 reopened
      `l2_book_microstructure_capture-005`/`-007`, and verified they STUCK (`status: queued`, `done_sha: None`,
      re-fetched individually). **Measured 2026-07-17T13:57:36Z: both task ids return NOTHING — they are absent from the
      `tasks` table entirely**, while `l2_book_microstructure_capture_2026_07_13.md` is `status: active`,
      `assigned_vm: planning` (i.e. ingested) with those two todos still `- [ ]` (`BLOCKED-OPERATOR-DECISION` /
      `BLOCKED-DATA-CORRECTNESS`). Only 4 l2_book rows survive, all `done`. **Absent is better than false-`done` — it is
      no longer lying — but it is not tracked either**, and an ingested plan's open todo with no row is invisible to
      dispatch. Candidate causes, none verified: the orphan-GC (`acc112f`/`f86b5f0`) correctly pruned them as
      queued-and-undispatched zombies because regen did not re-derive them; or regen derives them under DIFFERENT
      positional ids (see
      [`regen_positional_task_ids_not_content_stable_2026_07_17`](regen_positional_task_ids_not_content_stable_2026_07_17.md));
      or `BLOCKED-*` briefs are excluded somewhere — note `_brief_is_deferred` (`server/dispatch.py:327`) covers
      DEFER/DEFERRED/NICE-TO-HAVE/OPTIONAL/LATER and **not** `BLOCKED-`, so that theory was checked and does not hold.
      **Gate**: explain where those two todos' rows are, and either they exist with a correct status or a recorded
      decision says an operator-blocked todo intentionally has no row. **Do not close by re-reopening** — that is what
      decayed twice already.

## Progress Log

- **2026-07-17** — Filed at `ao_dispatch_hardening_2026_07_16`'s archival, carrying only the Deferred items with no
  other owner. The l2_book todo is new: found while verifying (not assuming) that the parent's Deferred item 1 was
  really complete. It was marked done in its home doc with a detailed "verified it STUCK" note — and the rows are gone.
  That is the second time this exact ledger entry has decayed after a verified-good reopen, which is why the gate above
  forbids closing it by reopening again.
