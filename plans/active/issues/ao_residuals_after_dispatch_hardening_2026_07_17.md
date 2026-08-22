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
    /plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    ../../archive/issues/ao_backlog_prune_gcs_wrong_db_2026_07_17.md,
    ../../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md,
    ../../epics/escalation_and_disaster_recovery_master.md,
    ../../epics/orchestrator_master.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: 2026-07-17
author: unknown
last_updated: 2026-08-21 # re-verified against the live VM (main): DB_PATH todo CLOSED (gate passes), l2_book todo
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
    /plans/archive/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    /plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md,
  ]
source:
  - "ao_dispatch_hardening_2026_07_16 Deferred tables (2026-07-16 + 2026-07-17), at its archival. Only the items with NO
    other home are carried here; the rest cite their existing owner and are deliberately not duplicated."
  - "Live DB probe 2026-07-17T13:57Z (/var/lib/orchestrator/state.db) — the l2_book finding below."
---

> **🟢 EXECUTION CONSOLIDATED 2026-07-17, banner repointed 2026-08-16 (/plan-reconcile)** — the original coordinator
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../../archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md)
> is now ARCHIVED; this doc's open items route through the CURRENT `ao`-tranche coordinator,
> [`ao_consolidated_closeout_2026_08_12`](../ao_consolidated_closeout_2026_08_12.md) (its own open todo 1, "re-triage
> the 115 inherited `[ao]` docs," is the mechanism that will eventually resolve this doc's ownership). Do NOT start work
> from this doc alone — flip items in the current coordinator and mirror them here. This doc stays the detail/evidence
> record.

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
| Recovery-audit Layer-1 producer rewire               | [`ao_recovery_audit_layer1_deleted_2026_07_15`](../../archive/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md)                                                                                                                                                                                                                                       |
| Staleness UI + alerting; audit hosts for freeze      | [`ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16`](ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md) — **another agent owns the UI half** (operator, 2026-07-16)                                                                                                                                                                  |
| uv-cache reconcile; 30G reclaim; `UV_CACHE_DIR`      | [`ao_host_disk_pressure_2026_07_16`](../../archive/2026_07/ao_host_disk_pressure_2026_07_16.md) — closed + its own Deferred table                                                                                                                                                                                                                          |
| Deep `plan-reconciler`; capability_wizard            | their own issue docs (unchanged by the parent's archival)                                                                                                                                                                                                                                                                                                  |

## Todos

- [x] [BACKEND] P2. ✅ **DONE — verified 2026-08-19 (/plan-reconcile orchestrator_master) directly against
      `agent-orchestrator` code, not just the tracker's claim: `server/routes/agents.py:440-448`'s
      `GET /api/escalations/{escalation_id}` docstring explicitly confirms the namespaced-plural route
      (`/api/escalations/{id}`) has no collision with `/api/escalate` (unchanged CI-wall dispatch), satisfying this
      todo's own gate ("one of the two routes is renamed/namespaced"). Repo: agent-orchestrator (code unchanged by
      this pass — the fix already shipped; only the checkbox was stale). Mirrors
      `ao_open_work_consolidated_tracker_2026_08_14.md`'s already-`[x]` 2026-08-15 verdict, which this same evidence
      now also lands here per its own "flip both" instruction.**
      Resolve the `/api/escalate` vs proposed `/api/escalation/{id}` name collision — BEFORE any
      escalation code is written.** Two unrelated concepts one character apart: `/api/escalate` already exists and is
      the **GHA→orchestrator CI-wall judgment dispatch**; the proposed `/api/escalation/{id}` is **operator
      escalation**. Whoever implements the second without noticing the first will either collide on the route or, worse,
      wire operator escalations into the CI judgment path. **Gate**: one of the two is renamed, or a recorded decision
      says why the near-collision is acceptable, cited from
      [`escalation_and_disaster_recovery_master`](../../epics/escalation_and_disaster_recovery_master.md) § "P1 —
      escalation pipeline MVP" (the design detail is in the archived child plan
      [`escalation_pipeline_mvp_2026_06_25`](../../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md), archived
      2026-07-23). Blocked-by: that **epic** is `status: paused` on an operator ruling — this only needs doing if/when
      it un-pauses (see [`escalation_and_disaster_recovery_master`](../../epics/escalation_and_disaster_recovery_master.md)
      for the pause/un-pause ruling record). (was: blocked-by the child plan's own pause, before its todos moved to the epic.)
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
      sequencing. **Superseded by the 2026-08-19 DONE marker above** — this checkbox is no longer pending the
      epic's own todo, both are now flipped on the same evidence.
- [x] [BACKEND] P2. ✅ **RESOLVED 2026-07-23 — the doc's own gate command was run on the live VM and PASSES.**
      `sudo -u ubuntu env -u ORCHESTRATOR_DB_PATH -u ORCHESTRATOR_STATE_JSON .venv/bin/python -c "from server import config; print(config.db_path())"`
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
- [x] [UI] P3. **Backlog-relations view.** ✅ **SHIPPED 2026-08-19 — `agent-orchestrator@003aafb608`.** Backend:
      `GET /api/backlog/graph` (already existed from an earlier `agent-orchestrator@6ce6379` pass) extended with a
      STRUCTURED `blockers: [{kind: "condition"|"task", ref, satisfied}]` array per task (brief §6's own framing) —
      positionally paired with `needs_conditions`/`after_tasks`, `satisfied` computed from the live
      `PrerequisiteRow.value` / `dispatch.completed_task_satisfied` (new public wrapper) so the frontend never has to
      re-derive dispatch's own done-or-pruned rule. `tests/test_backlog_graph.py` covers the empty-graph case,
      slots-only count, the cross-plan fan-out+skip shape, a full example-D-style task-edge satisfied/pruned/open
      matrix, and the empty-`needs_conditions` (never-gated) case — 8 tests, all green.
      Frontend: `dashboard/src/BacklogRelations.tsx`, a new standalone route (`/backlog-relations`, wired into
      `App.tsx`/`Landing.tsx` alongside Fleet KPIs/Doc Graph/Human Fleet). Design calls against brief §12's open
      questions: (1) organizing principle — no plan grouping, plan is one row attribute; (2) a shared condition
      renders ONCE in a fan-out-ranked "Top conditions" panel with its full `gates` list inline, never duplicated;
      (3) the contradiction (backend-ready-but-fleet-declined) gets its own always-on-top banner PLUS a per-row
      `⚠ ready but declined` badge — never folded into the ordinary skip-count column; (4) one view, not a linked
      primary+detail page — click-to-expand IS the detail (full explain + skip reasons + a small bounded local-edge
      SVG diagram, never a whole-graph layout); (5) scale — deliberately NOT a node-link/force-directed diagram at
      all (three prior attempts already failed at that, brief §7): fan-out is a sort, not a drawing problem, so it
      reads the same at n=300 as n=18 and never needs horizontal scroll (checked against the brief's own "phone over
      SSH/tmux" constraint); (6) `done`/orphan history is a collapsed-by-default section, out of the live view's way.
      Tests: `dashboard/src/BacklogRelations.test.ts` (22 vitest cases against brief §10 worked examples A-D as
      fixtures — the contradiction flag, bucket classification, fan-out ranking, provenance, search). Playwright
      DOES now exist in this repo (`dashboard/playwright.config.ts`, `tests/e2e/*.spec.ts` — the brief's July
      "no Playwright" claim is stale) — added a full `[UI] pw:L2` regression spec,
      `dashboard/tests/e2e/backlog-relations.spec.ts` (10 cases), against a DEDICATED isolated e2e backend +
      fixture (`fixtures/backlog_relations.e2e.yaml` + `seed_e2e_backlog_relations_state.py`, worked examples A-D
      verbatim) — all 10 passing against the real backend, not mocked. **RE-DECIDED 2026-08-14 (6+ weeks after the 2026-07-23 recheck found no
      movement) — the brief itself is READY TO DISPATCH; do not close this as un-actionable.** Re-read
      `agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md` in full. This doc's earlier framing ("cannot start until a
      design lands") was correct as of 2026-07-23, but the brief itself has never actually been un-actionable — it
      already carries a concrete `GET /api/backlog/graph` data contract (brief §9, fully specified JSON shape, already
      extractable from live tables per the brief's own text), an explicit resolved organizing-principle decision (§3:
      the model is a cross-cutting dependency GRAPH, not a plan-grouped tree — this is stated as a conclusion, not an
      open question), three concretely-documented rejected approaches with the specific reason each failed (§7, so a
      future attempt does not repeat them), real worked examples to design/test against (§10), and the existing
      dashboard's design tokens + stack constraints (§8: React 18.3+TS strict, no d3/mermaid/cytoscape, hand-rolled SVG
      precedent). What was missing 2026-07-23 was a human/design-agent turning this into an accepted visual mockup — but
      the brief is substantive enough that a single scoped implementation task can execute it directly (build the
      endpoint + a graph-oriented view per the brief's own resolved constraints) rather than waiting on a separate
      design-only pass that never happened in 4 weeks. **Recommended one-paragraph spec for the next AO-dispatch plan
      that picks this up** (agent-orchestrator + dashboard, NOT actioned here — this doc stays PM-only, the code lives
      in the other repo): Build `GET /api/backlog/graph` (`server/routes/`) returning the brief §9 shape —
      `{slots_total, plans[], tasks[]` (id/title/plan_ref/status/tier/priority/dispatched_to/assigned_role/
      collision_group/repos/needs_conditions/after_tasks/explain/skips/orphan), `conditions[]`
      (name/value/set_by/set_at/gates[])`}`. Build a dashboard view organized around the dependency/condition GRAPH, not
      a plan tree (three tree/DAG-column/kanban attempts were already built and rejected — brief §7 documents exactly
      why each failed, do not re-propose them); the two must-answer questions per the brief's own priority ranking (§5)
      are "why is nothing running" (<5s, no clicking) and "which single condition unblocks the most work" (a fan-out
      question a table cannot answer). Must visually surface a condition shared across plans (§3: the majority of
      task→task edges cross plan boundaries) and the "backend says ready, N workers disagree" contradiction (§10 example
      A — the actual incident that motivated this brief, 15/17 slots declining a task the dispatcher believed was
      ready). Reuse the existing dashboard tokens (`dashboard/src/styles.css`) and dark-first theme; test against the
      brief's §10 worked examples A-D; design for ~10× today's scale (brief §4: currently ~18 actionable tasks, target
      readable at ~180). **If a future pass judges a dedicated design-agent mockup pass is still preferred over
      collapsing design+implementation into one engineering task, that is a legitimate alternate call — but "wait
      indefinitely for an unscoped design pass" is no longer the only option, and this brief should not keep re-reading
      as blocked on the same 2026-07-17 handoff it already resolved most of.** Original 2026-07-23 recheck text (kept
      for context): `docs/BACKLOG_RELATIONS_UX_BRIEF.md` is present, but there is **no design deliverable, no
      `GET /api/backlog/graph` endpoint** (grepped `server/routes/`), and no relations UI commit in `dashboard/src`. The
      blocker is unchanged — this cannot start. **If the design is not coming, say so and close this**; an
      indefinitely-blocked P3 that nobody owns is noise in every future sweep. Brief + real data + a 100-task synthetic
      fixture were handed to the design agent 2026-07-17 (`agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md`).
      **Cannot start until a design lands.** The model is a cross-cutting GRAPH, not a hierarchy — measured: 6 of 11
      task→task edges cross plans, 1 condition gates 2 plans, 25/35 conditions gate nothing. A table cannot show that,
      which is why three table/tree attempts were rejected. Needs `GET /api/backlog/graph` behind it. **Gate**: design
      received → implemented → the relation a table cannot express (one prereq gating tasks in multiple plans) is
      visible in one view.
- [ ] [INFRA] P2. Per D34 ruling (OPERATOR-RULED 2026-08-21 — APPROVED: reactivate l2_book_microstructure_capture
      so the reopen-drop dispatch-defect re-test can run): flip
      `plans/active/l2_book_microstructure_capture_2026_07_13.md`'s `assigned_vm: NA` back to
      `assigned_vm: planning` (`execution_scope: orchestrator-agent`), then execute the re-test gate described
      below. ⚠️ **RE-SCOPED 2026-07-23 — the original measurement is now VOID; do NOT close this as fixed.**
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
- **2026-08-14 (bookkeeping pass) — DECIDED on the backlog-relations UI todo, per this session's operating authority to
  decide rather than defer.** Read `agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md` in full (not re-derived from
  a prior summary). Verdict: the brief is substantive enough to dispatch directly as a scoped implementation task — it
  carries a fully-specified `GET /api/backlog/graph` data contract, an already-resolved organizing-principle decision
  (graph, not plan-tree), three documented rejected approaches with the specific failure reason for each, real worked
  examples, and the dashboard's existing stack/token constraints. What has been missing for 4 weeks is not "the brief
  isn't good enough" but "nobody ever turned it into either an accepted mockup or a scoped implementation task" — the
  design-agent handoff from 2026-07-17 was never actioned by anyone. Rewrote the todo itself with a one-paragraph
  extracted spec (see the todo's own text above) so the next AO-dispatch plan authored against this doc does not need to
  re-read the full brief to scope the work. **Explicitly NOT done here**: no code written, no endpoint built, no plan
  authored — that is Track-6 work for agent-orchestrator + dashboard, a different repo and a different wave, out of this
  session's scope. This is a recommendation + spec extraction only. The todo's checkbox stays `- [ ]` since the actual
  UI/endpoint work remains undone; only the "is this still blocked" verdict changed, from blocked-upstream-design to
  ready-to-dispatch.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:2c7f98d3f07fe05b]: KEEP-NA, valid — item 1 is live-tracked verbatim in the active epic `escalation_and_disaster_recovery_master`'s own todo list (checkbox stays open only as a pointer, per a 2026-08-07 citation-fix); item 2 is explicitly scoped as a future-plan recommendation, not this doc's own execution; item 3 is void pending a retest-gate condition.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA, valid — reaffirmed. The doc has converged to a single
  open todo (items 1-4 — the escalation-route collision, `ORCHESTRATOR_DB_PATH`, the 2026-07-12 degradation onset,
  and the backlog-relations UI — all closed `[x]` by 2026-08-19). The sole remaining item (item 5, the l2_book
  reopen-drop re-test gate) stays void pending its explicit re-test condition: directly checked
  `plans/active/l2_book_microstructure_capture_2026_07_13.md` — still `status: active`, `assigned_vm: NA`, so the
  plan has not returned to `assigned_vm: planning` and the gate this todo names has genuinely not opened yet. Doc
  stays `assigned_vm: NA`.
- **2026-08-21 — ruling D34 (l2_book plan reactivation)**: OPERATOR-RULED 2026-08-21 — APPROVED: reactivate
  l2_book_microstructure_capture (assigned_vm: planning) so the reopen-drop dispatch-defect re-test can run.
  Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
