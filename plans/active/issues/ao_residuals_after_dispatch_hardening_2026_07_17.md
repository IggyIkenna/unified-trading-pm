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
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, backlog, escalation, observability, orphaned-todos, tracking-index]
related:
  [
    ../../archive/2026_07/ao_dispatch_hardening_2026_07_16.md,
    /plans/archive/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    /plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    ../../archive/issues/ao_backlog_prune_gcs_wrong_db_2026_07_17.md,
    ../../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md,
    ../../epics/escalation_and_disaster_recovery_master.md,
    ../../epics/orchestrator_master.md,
  ]
created: 2026-07-17
author: unknown
last_updated: 2026-07-23 # re-verified against the live VM (main): DB_PATH todo CLOSED (gate passes), l2_book todo
# re-scoped (measurement void under the dispatch pause), backlog-relations still blocked-upstream after 6 days
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
context_scope:
  [
    /plans/epics/escalation_and_disaster_recovery_master.md,
    /plans/archive/2026_07/escalation_pipeline_mvp_2026_06_25.md,
    agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md,
    /plans/archive/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    /plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    agent-orchestrator/server/dispatch.py,
  ]
source:
  - "ao_dispatch_hardening_2026_07_16 Deferred tables (2026-07-16 + 2026-07-17), at its archival. Only the items with NO
    other home are carried here; the rest cite their existing owner and are deliberately not duplicated."
  - "Live DB probe 2026-07-17T13:57Z (/var/lib/orchestrator/state.db) — the l2_book finding below."
---

> **🟢 EXECUTION CONSOLIDATED 2026-07-17** — this doc's open items are now tracked and executed via
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md)
> (operator-session local plan; verified-live classification table there). Do NOT start work from this doc alone — flip
> items in the plan and mirror them here. This doc stays the detail/evidence record.

# AO residuals after `ao_dispatch_hardening` archived

> **Why this doc exists.** The parent plan is complete and archived. Its Deferred tables were the only tracking for a
> handful of items. Rather than leave an archived doc as their home — the mistake
> [`ao_autospawn_role_blind_dispatch_starvation_2026_07_14`](../../archive/issues/ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md)
> records in its own banner, which orphaned two live bugs for two days — the homeless ones move here. **Nothing is
> duplicated**: items that already have an owner are listed in § Already homed with a pointer only.

## Already homed — do NOT re-track here

| Deferred item                                        | Its actual home                                                                                                                                                                                                                                                                                                                                            |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reopen the 2 false-`done` rows                       | **DONE** by infra slot-2 2026-07-17 — but see todo 5 below, it did not hold                                                                                                                                                                                                                                                                                |
| Unauditable `done` rows (`brief_hash` NULL)          | [`regen_positional_task_ids_not_content_stable_2026_07_17`](regen_positional_task_ids_not_content_stable_2026_07_17.md) todo 1                                                                                                                                                                                                                             |
| Durable park for fleet-skipped tasks (the CODE half) | [`ao_skip_blind_spawn_budget_phantom_churn_2026_07_15`](ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md) (1 open todo)                                                                                                                                                                                                                              |
| Sports durable park (the OPERATIONAL half)           | **MOOT 2026-07-17** — `-002` no longer exists, `-001` is `done`; sports dispatching normally                                                                                                                                                                                                                                                               |
| escalation workstream un-pause                       | **Moved 2026-07-23** → [`escalation_and_disaster_recovery_master`](../../epics/escalation_and_disaster_recovery_master.md) (epic `status: paused`, operator ruling). The child plan [`escalation_pipeline_mvp_2026_06_25`](../../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md) was ARCHIVED (operator); its 5 UNBUILT todos live in the epic now. |
| Recovery-audit Layer-1 producer rewire               | [`ao_recovery_audit_layer1_deleted_2026_07_15`](ao_recovery_audit_layer1_deleted_2026_07_15.md)                                                                                                                                                                                                                                                            |
| Staleness UI + alerting; audit hosts for freeze      | [`ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16`](ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md) — **another agent owns the UI half** (operator, 2026-07-16)                                                                                                                                                                  |
| uv-cache reconcile; 30G reclaim; `UV_CACHE_DIR`      | [`ao_host_disk_pressure_2026_07_16`](../../archive/2026_07/ao_host_disk_pressure_2026_07_16.md) — closed + its own Deferred table                                                                                                                                                                                                                          |
| Deep `plan-reconciler`; capability_wizard            | their own issue docs (unchanged by the parent's archival)                                                                                                                                                                                                                                                                                                  |

## Todos

- [ ] [BACKEND] P2. **Resolve the `/api/escalate` vs proposed `/api/escalation/{id}` name collision — BEFORE any
      escalation code is written.** Two unrelated concepts one character apart: `/api/escalate` already exists and is
      the **GHA→orchestrator CI-wall judgment dispatch**; the proposed `/api/escalation/{id}` is **operator
      escalation**. Whoever implements the second without noticing the first will either collide on the route or, worse,
      wire operator escalations into the CI judgment path. **Gate**: one of the two is renamed, or a recorded decision
      says why the near-collision is acceptable, cited from
      [`escalation_and_disaster_recovery_master`](../../epics/escalation_and_disaster_recovery_master.md) § "P1 —
      escalation pipeline MVP" (the design detail is in the archived child plan
      [`escalation_pipeline_mvp_2026_06_25`](../../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md), archived
      2026-07-23). Blocked-by: that **epic** is `status: paused` on an operator ruling — this only needs doing if/when
      it un-pauses. (was: blocked-by the child plan's own pause, before its todos moved to the epic.)
      **na-eligibility-audit 2026-08-03**: the stated blocker has changed — the epic
      [`escalation_and_disaster_recovery_master`](../../epics/escalation_and_disaster_recovery_master.md) UN-PAUSED
      2026-07-28 (operator gated-decision closeout ruling, `status: paused → active`, full completion of all P1 todos
      committed). This item is no longer blocked by the pause, but the route-collision resolution itself has not been
      done — check the epic's own P1 todo list before duplicating work here. (The archived child-plan citation itself is
      unrelated background — a design-detail pointer, not the actual blocker.) **na-eligibility-audit 2026-08-07
      (citation fix, KEEP-NA-STALE/already-duplicated)**: this exact ask is already tracked verbatim as
      `escalation_and_disaster_recovery_master`'s own `## P1 — escalation pipeline MVP` § `[BACKEND] P0` "Prerequisite —
      resolve the `/api/escalate` vs `/api/escalation/{id}` route-naming collision" todo (that epic is `status: active`,
      `assigned_vm: planning`) — same gate, same two routes, same "land BEFORE the role-agnostic escalation record todo"
      sequencing. Do not duplicate work here; the epic is the live tracking home. This checkbox stays open pending that
      epic's own todo, not re-derived independently.
- [x] [BACKEND] P2. ✅ **RESOLVED 2026-07-23 — the doc's own gate command was run on the live VM and PASSES.**
      `sudo -u ubuntu env -u ORCHESTRATOR_DB_PATH -u ORCHESTRATOR_STATE_JSON .venv/bin/python -c "from server     import config; print(config.db_path())"`
      → `/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db`, and that path holds the LIVE
      data (`tasks=68 agents=78 slots=17`), not an empty DB — which is precisely the failure mode this todo described (a
      probe reporting zeroes that looks like a healthy answer). The one-concept-two-places condition is gone at the
      source: the systemd unit no longer carries `Environment=ORCHESTRATOR_DB_PATH` / `ORCHESTRATOR_STATE_JSON` (only
      `MODE`, `SNAPSHOT_INTERVAL_SECONDS`, `WORKER_HOST`, `PATH`, `TERM`), the `/var/lib/orchestrator` `ReadWritePaths=`
      line is gone, `.env.local` never had the vars, and `/var/lib/orchestrator/` no longer exists on disk. Delivered by
      `ao_fleet_infra_hardening_2026_07_20.md` (archived) todos 1+2 — the config change plus the operator-gated live
      migration. Original item: **`ORCHESTRATOR_DB_PATH` is set in the systemd unit but NOT in `.env.local`.** So any
      shell-run tooling on the VM resolves `config.db_path()` to the **empty in-repo DB** instead of
      `/var/lib/orchestrator/state.db` — a probe reports zeroes and looks like a healthy answer. This bit the 2026-07-17
      session **twice** while diagnosing the prune bug, and it is the same one-concept-two-places family as the
      `ORCHESTRATOR_DB_PATH`/`ORCHESTRATOR_REGEN_DB_PATH` drift that CAUSED that bug
      ([`ao_backlog_prune_gcs_wrong_db_2026_07_17`](../../archive/issues/ao_backlog_prune_gcs_wrong_db_2026_07_17.md)).
      **Gate**: a plain `.venv/bin/python -c "from server import config; print(config.db_path())"` on the VM, run as
      `ubuntu` with no env overrides, prints the live DB path.
- [x] [BACKEND] P3. **Root-cause the 2026-07-12 degradation onset.** ✅ **DONE via
      `/plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md` item 12** — the twin item in
      `ao_open_issues_consolidated_close_out_2026_07_17.md` Phase 5 flipped `[x]` and collapsed to one owner per that
      item's own duplicate-NOTE (this exact item; SYNCED 2026-07-25, apply_batch_12). Named cause: the true onset was
      2026-07-12 15:00 UTC, a second, unalerted `ao-self-pull.sh` dirty-gate wedge (root: a `tempfile.gettempdir()`
      CWD-fallback bug in `regen_backlog_from_plan.py`), not the earlier, well-known 08:1x UTC `/tmp`-ENOSPC blip (which
      was real but contained). Root-fixed same day, `agent-orchestrator@fc9ac53`. Full hourly-breakdown methodology +
      activity-log evidence lives in that plan's Progress Log — not duplicated here.
- [ ] [UI] P3. **Backlog-relations view.** ⏳ **STILL BLOCKED-UPSTREAM-DESIGN, re-checked 2026-07-23 (6 days later, no
      movement):** `docs/BACKLOG_RELATIONS_UX_BRIEF.md` is present, but there is **no design deliverable, no
      `GET /api/backlog/graph` endpoint** (grepped `server/routes/`), and no relations UI commit in `dashboard/src`. The
      blocker is unchanged — this cannot start. **If the design is not coming, say so and close this**; an
      indefinitely-blocked P3 that nobody owns is noise in every future sweep. Brief + real data + a 100-task synthetic
      fixture were handed to the design agent 2026-07-17 (`agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md`).
      **Cannot start until a design lands.** The model is a cross-cutting GRAPH, not a hierarchy — measured: 6 of 11
      task→task edges cross plans, 1 condition gates 2 plans, 25/35 conditions gate nothing. A table cannot show that,
      which is why three table/tree attempts were rejected. Needs `GET /api/backlog/graph` behind it. **Gate**: design
      received → implemented → the relation a table cannot express (one prereq gating tasks in multiple plans) is
      visible in one view.
- [ ] [INFRA] P2. ⚠️ **RE-SCOPED 2026-07-23 — the original measurement is now VOID; do NOT close this as fixed.**
      Re-measured on the migrated live DB: only **1** `l2_book%` task row survives
      (`l2_book_microstructure_capture-001`, `done`), while the plan still shows **2 open todos**. That looks like the
      same divergence, only worse — **but it is not evidence any more**: the plan is now `assigned_vm: NA` (swept into
      the operator's fleet-wide dispatch pause, `unified-trading-pm@468a0f580`), so regen does NOT ingest it and absent
      task rows are the CORRECT, expected behaviour rather than a defect. **The bug is unobservable while dispatch is
      paused, not proven fixed.** **Re-test gate**: when this plan returns to `assigned_vm: planning`, confirm every
      open `- [ ]` gets a task row — if the two BLOCKED todos are again absent while the plan is ingested, the
      reopen-drop defect is live and this todo becomes actionable. Original finding: **NEW 2026-07-17 — the l2_book
      reopen did NOT hold, and its own verification says it did.**
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
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — All 3 open todos cite an
  explicit current blocking condition (a paused epic, an unresolved upstream design call, a void-pending-retest
  measurement) — genuine external/design gates, not defaulted work.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified (6 entries, unchanged) — all still resolve and cover the 3 open todos
  (escalation-route collision blocked on the now-active epic, the blocked-upstream-design UI item, and the l2_book
  re-test gate).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries), still accurate.

- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — re-checked all 3 open items against the round7-10
  precedent set. The escalation-route-collision item cites the epic's own P1 todo as live tracking home (a citation fix,
  not new work); the UI item is explicitly blocked-upstream-design, unchanged; the l2_book re-test gate is explicitly
  void-pending-a-real-retest-condition (plan must return to `assigned_vm: planning` first), not a worker-executable
  check today. None of IAM self-service/D16/S5.1/plan-destination-default/escalation-N/
  reversibility-qualified-deletes/Option-B-retirement/DeepSeek-Slack-credentials apply. Corroborated same-day:
  `/ag-closeout-audit ao` batch12 lists this doc under operator-gated (22).
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — content unchanged since
  round11; all 3 items remain in the exact same state (citation-fix pending an epic todo, blocked-upstream-design UI
  item, void-pending-retest l2_book gate). No new facts apply.
