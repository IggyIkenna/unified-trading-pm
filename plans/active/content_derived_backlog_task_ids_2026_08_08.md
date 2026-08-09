---
doc_type: plan
title:
  Content-derived backlog task ids — replace positional `<slug>-NNN` minting, then backfill every historical row (Option
  B) without ever renaming a dispatched row
summary: >-
  `regen_backlog_from_plan` derives a task id as `slug` + next free positional index, so a todo's id is a function of
  its POSITION among that plan's todos, not its text. When earlier todos are checked off and their yaml entries pruned,
  numbering restarts and a NEW open todo is handed an id an existing `done` row already owns. The `brief_hash` guard
  then correctly refuses the reset and logs `sync_backlog_to_db: REFUSING to reset task id <id>` on EVERY regen tick,
  forever — 60 occurrences in 6h measured 2026-08-08 on `fleet_promoter_glue_runner_stall-001`, then immediately
  recurring on `mtds_backfill_launcher_guard_overapplies_to_nontardis_venues-002` once the first was resolved. Operator
  ruling 2026-07-28 (recorded in the source issue doc) is to do the content-hash rewrite; operator ruling 2026-08-08
  (interactive session) selects **Option B — additionally backfill all ~1,728 historical ids**, not Option A
  (new-ids-only). This plan is the phased execution of that, authored against a full blast-radius map produced
  2026-08-08. Two hazards drive the entire phasing and are written in as gates, because neither fails loudly: (1)
  renaming a `dispatched` row 404s a LIVE worker — `/done`, `/progress` and `/blocked` all look the task up by a
  worker-echoed `task_id`, so a mid-flight rename strands genuinely-completed work with no recovery path; (2) a
  `completed_tasks` prereq entry that the migration fails to remap does NOT error — `_completed_task_satisfied` treats
  an id absent from both DB and backlog as SATISFIED, so a missed remap silently un-gates a downstream task that should
  still be held. Phase 1 (new minting) is safe, bounded and closes the bug for everything created from that point on;
  Phase 2 (the historical backfill) is operator-gated at every irreversible step.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [agent-orchestrator, backlog, regen, task-id, id-collision, brief-hash, audit-history, migration, dispatch, state-db]
related:
  [
    /plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
created: 2026-08-08
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
effort: medium
sequential: true
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator ruling 2026-08-08 (interactive session): "b please" — Option B (full backfill) selected over Option A
  (new-ids-only), and "make it ao plan status active so that AO picks it up". Authored against the blast-radius map
  produced in the same session, which is the prerequisite the source issue doc's own 2026-07-31 entry required before
  any dispatch ("re-homed ... as properly-phased todos before any dispatch").
context_scope:
  [
    /plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/bootstrap.py,
    agent-orchestrator/server/routes/backlog.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/dispatch.py,
  ]
---

# Content-derived backlog task ids (Option B — new minting + full historical backfill)

> **🟡 IN-FLIGHT REFACTOR — fleet-core identity change.** Phase 2 rewrites task ids across `state.db` and
> `backlog.yaml`. Do not hand-edit `backlog.yaml`, do not run a manual `state.db` id UPDATE, and do not start Phase 2
> work while any Phase 1 todo is open.

## Why this supersedes the "not AO-dispatchable" classification

`/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md` carries `assigned_vm: NA` and a record
of THREE reverted dispatch attempts (BLK-29884333, 2026-07-31). That classification was correct at the time and is **not
being re-litigated**: the reverts were because the raw operator ruling was being dispatched with no surface map and no
phasing. Its own 2026-07-31 entry states the requirement — re-home "as properly-phased todos **before any dispatch**".
This plan is that re-homing. The source doc stays `assigned_vm: NA` and remains the analysis SSOT; this plan is the
execution vehicle. **Do not flip the source doc to `planning`.**

## The two hazards that shape every phase

Both were established by reading the code, and both are silent — neither raises, so neither is caught by "did it throw".

1. **Renaming a `dispatched` row strands a live worker.** `POST /api/slots/{id}/done` resolves the task via
   `session.get(TaskRow, req.task_id)` (`routes/slots_worker.py:1727`, 404 on miss) and `DoneRequest`/`ProgressRequest`/
   `BlockedRequest` all carry a **client-echoed** `task_id` the worker holds in session memory. Rename underneath it and
   its next `/progress`, `/blocked` or `/done` 404s, with genuinely-shipped work unable to close. `/heartbeat` is the
   exception — `HeartbeatRequest` carries no task_id; the server reads `slot.current_task` itself.
2. **A missed prereq remap silently un-gates.** `dispatch._completed_task_satisfied` treats an id absent from BOTH the
   DB and the backlog as **satisfied** (deliberate, for the legitimate "upstream finished and pruned" case). So a
   `completed_tasks` entry the migration fails to remap does not deadlock or error — it releases a downstream task that
   should still be blocked, invisibly, until that task dispatches.

## Phase 1 — content-derived minting (safe, closes the bug going forward)

- [x] ✅ [BACKEND] P1. **Audit every worker-facing endpoint for a client-echoed `task_id`.** The blast-radius map
      confirmed `/done`, `/progress`, `/blocked` echo it and `/heartbeat` does not, but did NOT trace
      `/skip-current-task`, `/reassign`, `/park`, `/unpark` or the rest of `routes/slots_worker.py` +
      `routes/slots_ops.py`. Produce the complete list of endpoints whose request model carries a `task_id` the CLIENT
      supplies. This is hazard 1's real blast radius and every later phase depends on it being complete, not sampled.
      Done-when: every endpoint in both route files classified echoed/not-echoed, recorded in this plan's Progress Log.
      (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P1. **Add `_make_content_task_id(plan_ref, brief, occurrence)`** next to the existing `_make_task_id`
      (`regen_backlog_from_plan.py:1556`), returning
      `f"{slug}-{sha256(f'{plan_ref}|{brief}|{occurrence}').hexdigest()[:N]}"`. **The hash input MUST include
      `occurrence`** — `_group_plan_tasks_by_brief`'s own docstring (`:1587-1596`) documents that two genuinely
      different todos in one plan can hard-wrap to a byte-identical first physical line; a `sha256(brief)`-only id
      collides for exactly that documented case and would ship a NEW id-collision bug on day one. `N` is an explicit
      named constant with a test, not a borrowed value — see the next todo. Do NOT yet change any call site. (repo:
      agent-orchestrator) — agent-orchestrator@e0f107a
- [x] ✅ [BACKEND] P2. **Pin the truncation length with a measured collision-probability test.** The `RB-<hex8>`/
      `sjr-<hex8>` precedent (`orm.py:991, :1036`) is a different id namespace and its 8 chars must not be assumed
      transferable. Assert the birthday bound at this corpus's real scale (~2,187 backlog rows today, ~90/tick regen)
      and record the chosen `N` + the margin. Done-when: a test names the constant and fails if it shrinks. (repo:
      agent-orchestrator) — agent-orchestrator@0b1507e
- [x] ✅ [BACKEND] P1. **Switch new-task minting to the content id, collision-checked against BOTH yaml ids AND the full
      historical `tasks` table.** `_make_task_id`'s next-index scan is yaml-only (`:1717, :1831`) — a `done`-and-pruned
      id is invisible to it, which is itself a contributing root cause. `remint_backlog_collision` already does the
      wider check (`routes/backlog.py:638-639`); carry that into the minting path. After this lands, a freed positional
      slot can never be reassigned, because nothing new is positional. (repo: agent-orchestrator) —
      agent-orchestrator@ba6eff5
- [x] ✅ [BACKEND] P2. **Rewrite the two guard tests to inject their collision at the DB layer.**
      `test_sync_resets_terminal_fields_when_id_reused_for_different_checkbox`
      (`tests/test_regen_backlog_from_plan.py:3249`) and `test_sync_refuses_to_reset_a_done_row_on_id_reuse` (`:3300`)
      manufacture a positional collision through normal minting — which becomes unreachable after the previous todo.
      Inject directly so both keep testing the guard in isolation rather than silently becoming vacuous. (repo:
      agent-orchestrator) — agent-orchestrator@a746e83
- [x] ✅ [BACKEND] P2. **Record the guard disposition in `sync_backlog_to_db`'s docstring.** Ruling: **KEEP** the
      sibling-reset guard (`bootstrap.py:747-806`) as defence-in-depth — Phase 1 removes its position-shift trigger but
      not a hand-edited `backlog.yaml` or a bug in the new minting's own collision check. **KEEP** the NULL-`brief_hash`
      backfill branch unchanged. The source doc requires this decision be written down either way. (repo:
      agent-orchestrator) — agent-orchestrator@5ae9dd5
- [x] ✅ [BACKEND] P3. **DONE 2026-08-08 (slot-26, backend_engineer)** — **Decide `remint_backlog_collision`'s fate**
      (`routes/backlog.py:545-687`). Ruling: **KEEP**, not retire. The todo's premise — "structurally unreachable
      post-Phase-1" — does not hold: Phase 1's `_make_content_task_id` switch only prevents a FRESH mint from landing on
      a collided id; it does nothing for the ~2,187 rows already sitting in `backlog.yaml` under the OLD positional
      `<slug>-NNN` scheme, which this endpoint remediates and which only Phase 2's (not-yet-run) historical backfill
      retires the need for. Empirically confirmed via
      `GET /api/activity?type=backlog_sibling_reset_guard_collision_reminted`: 173 fires between 2026-07-26 and
      2026-08-08, **including after** the Phase-1 minting switch landed (`agent-orchestrator@ba6eff5`,
      2026-08-08T14:28:06Z) — `defi_catalog_engine_config_key_contract_drift-002` alone refused 156+ times from 11:38Z
      through past 22:40Z today, well after the switch. Also actively wired into the dashboard's one-click "Fix"
      affordance (`dashboard/src/layout.tsx`, `dashboard/src/api.ts`) with its own e2e coverage
      (`dashboard/tests/e2e/backlog-collision.spec.ts`) — retiring it would be a UI regression too. It already IS the
      general "force a task onto a fresh id" admin tool the alternative disposition asked for (any flagged collision,
      not slug-specific) — no repurposing needed. Recorded the ruling + evidence directly in the endpoint's own
      docstring (not just here) per this plan's established "record the guard disposition in the docstring" pattern
      (Phase 1 todo P2 above). New finding filed as a Follow-up below (the `-002` collision recurring even after an
      explicit remint at 15:44:23Z suggests remint's "future regen ticks stop re-deriving that position" claim doesn't
      always hold — out of this todo's scope to root-cause). No test changes (nothing retired). QG: full suite green
      (basedpyright clean, no new violations). Evidence: agent-orchestrator@e47eb50. Repo: agent-orchestrator.

## Phase 2 — historical backfill (Option B). Every irreversible step is operator-gated.

- [x] ✅ [BACKEND] P1. **DONE 2026-08-08 (slot-7, content_derived_backlog_task_ids-008)** — Build the old→new id map as
      a REPORT ONLY — no writes. For every row, derive the new id from the ALREADY-STORED `TaskRow.brief_hash`
      (`orm.py:70`; `sync_backlog_to_db` has populated it since @4695db6), so no plaintext re-derivation is needed.
      Recover the slug from the old id's prefix, or from `TaskRow.plan_ref` for orphan `done` rows with no yaml
      counterpart (the `_orphan_view` case, `routes/backlog.py:67-101`). Emit the map as a durable artifact. Done-when:
      the artifact exists and its row count matches `SELECT COUNT(*) FROM tasks`. See Progress Log for the algorithm +
      live counts. (repo: agent-orchestrator) — agent-orchestrator@8a8454c
- [x] ✅ [BACKEND] P1. **DONE 2026-08-08 (slot-18, content_derived_backlog_task_ids-009)** — **Exclude the
      NULL-`brief_hash` tail from the map, permanently.** Those rows' briefs are documented unrecoverable
      (`bootstrap.py:710-727` — backlog.yaml is gitignored, no VCS history, no archive writer, activity_log never stored
      the brief), so they can never get a content id. This mirrors the already-ruled "(c) accept permanently" decision
      for that tail; it is not reopened here. Report the count. (repo: agent-orchestrator) — agent-orchestrator@b143bf5
- [x] ✅ [BACKEND] P1. **DONE 2026-08-09 (slot-23, content_derived_backlog_task_ids-010)** — **Write the pre/post
      prereq-remap assertion — hazard 2's gate.** Diff every `completed_tasks`/`prerequisites` array before and after
      the proposed map and assert each old id is either remapped or was ALREADY legitimately absent pre-migration. A
      missed remap does not error at runtime (`_completed_task_satisfied` treats absent as satisfied) — it silently
      un-gates. This assertion is the only thing that catches it. Done-when: the check runs against the Phase-2 map
      artifact and reports zero unexplained entries. (repo: agent-orchestrator) — agent-orchestrator@d86827b
- [x] ✅ [BACKEND] P1. **DONE 2026-08-09 (slot-23, content_derived_backlog_task_ids-011)** — **Enforce the
      dispatched-row deferral — hazard 1's gate.** The migration must SKIP any row whose status is `dispatched` and
      defer its rename to the transition points that already fire on terminal state (`done_slot` finalization,
      `_prune_stale`'s cancel path, `/skip-current-task`'s release). With this ordering honored, **no
      id-alias/back-compat column is needed**. Done-when: a test proves a `dispatched` row is never renamed by the
      migration and is renamed correctly once it goes terminal. (repo: agent-orchestrator) — agent-orchestrator@6b57503
- [x] ✅ [BACKEND] P2. **DONE 2026-08-09 (slot-6, content_derived_backlog_task_ids-012)** — **Do NOT rewrite
      `activity_log` or `compactions` rows in place.** Rewriting a past audit entry to an id it did not happen under is
      itself the audit-integrity violation this whole effort exists to prevent. Instead append a
      `backlog_task_id_migrated {old_id, new_id}` activity row per rename so old→new stays resolvable. **Also**:
      `activity_log.task_id` carries synthetic non-task labels (`plan_health.py:1008` writes `doc_drift:<key>`) — any
      walker assuming every non-null value is a real backlog id WILL corrupt those rows. (repo: agent-orchestrator) —
      **Found + fixed a real parity gap**: of the three deferred-rename transition points, `done_slot` and
      `/skip-current-task` already appended `backlog_task_id_migrated` via `ss.log_activity` — `_prune_stale`'s cancel
      path (raw `sqlite3.Connection`, no ORM Session) did not. Added a best-effort raw `INSERT INTO     activity_log`
      there (degrades silently on a legacy DB missing the table, mirroring the existing `blocked_queue` delete precedent
      in the same function), with a new `trigger: "prune_stale_cancel"` label. Recorded the append-only design
      decision + the `activity_log.task_id`/`compactions.task_id` synthetic-label hazard directly in
      `content_id_migration.py`'s module docstring (the invariant every future bulk-apply script must inherit: an EXACT
      dict-key lookup against the checked-in map, never a fuzzy/substring task-id detector). Added regression coverage
      asserting the new activity row's `old_id`/`new_id`/`trigger` fields, and that the hazard-1
      "not-cancelled-this-tick" no-op case still logs nothing. QG: 2889 passed, 2 skipped, basedpyright clean, ruff
      clean. Evidence: agent-orchestrator@7eb0203 (verified ancestor of origin/live-defi-rollout before this flip).
- [ ] [BACKEND] P2. **Cover the derived-identifier namespaces in the map.** An old id surviving as a SUBSTRING of a
      still-live key is silently orphaned: `BLK-op-{task_id}` (`bootstrap.py:854, :889`), `{task_id}--ruling`
      (`regen_backlog_from_plan.py:2631`), `auto_unpark__{task_id}` (`auto_park.py:92-96`), `task:{task_id}` cooldown
      keys (`auto_park.py:110, :192`), and the dedup keys in `dedup_state.py:418, :430`. Enumerate and remap each.
      (repo: agent-orchestrator)
- [ ] [BACKEND] P2. **Make the migration idempotent + resumable.** Follow the existing `_migrate_*` convention
      (`bootstrap.py:147-159`) with a sentinel so a second run no-ops. Batch with a resumable checkpoint rather than one
      giant transaction across ~1,728 rows (SQLite single-writer; reuse the `busy_timeout=120000` pattern `_prune_stale`
      already uses). Persist the full old→new map BEFORE applying so the inverse can be replayed. **Do NOT wire it into
      `create_all_tables()`'s automatic on-every-boot sequence.** (repo: agent-orchestrator)
- [ ] [OPERATOR] P1. **Dry-run the migration against a SCRATCH COPY of `state.db`, never the live file.** Operator-gated
      because it requires copying live orchestrator state and reading it outside the service. Assert: row-count
      preserved; `done_sha`/`done_at`/`done_evidence` byte-identical pre/post; every `completed_tasks` reference
      remapped-or-justified; idempotent on a second run; zero `dispatched` rows touched. Done-when: the dry-run report
      is attached to this plan's Progress Log. (repo: agent-orchestrator)
- [ ] [OPERATOR] P1. **Apply the backfill to live `state.db` + `backlog.yaml` in one logical operation.**
      Operator-gated: irreversible, touches fleet-core identity, and the two stores are two durable copies of the same
      identity that must not diverge (`remint_backlog_collision` already accepts this two-store risk for ONE row; this
      is ~1,728). Run at a quiet dispatch moment — per CLAUDE.md, maintenance-window scheduling is skipped
      pre-live-trading, so this means "not obviously busy", not a formal window. Verify against the Phase-2 assertions
      immediately after. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. **Re-verify the two live collisions are gone and stay gone.** `fleet_promoter_glue_runner_stall-001`
      (resolved 2026-08-08 by closing its last todo) and
      `mtds_backfill_launcher_guard_overapplies_to_nontardis_venues-002` (open at authoring time). Done-when:
      `journalctl -u orchestrator.service --since "1 hour ago" | grep -c "REFUSING to reset"` returns 0 across a full
      `PlanRegenLoop` cycle. (repo: agent-orchestrator)

## Follow-ups

- [ ] [BACKEND] P3. **Close the citation errors the false-done audit surfaced adjacent to this bug.**
      `mtds_migrate_executor_progress_checkpoint_gap-008/-009/-010` are three backlog rows pointing at ONE
      still-unimplemented todo (`migrate_sports_league_id_casing_2026_07_21.py`, confirmed zero `record_vm_progress`
      occurrences), each citing a wrong sha — a direct symptom of positional ids. After Phase 1, dedupe them to one row.
      Source: /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md. (repo:
      unified-trading-pm)
- [ ] [BACKEND] P2. **Root-cause why `remint_backlog_collision` didn't durably stop
      `defi_catalog_engine_config_key_contract_drift-002`'s collision from recurring.** Found while working the
      `remint_backlog_collision` fate todo above (2026-08-08, slot-26): the collision was reminted exactly once
      (`backlog_sibling_reset_guard_collision_reminted` @ 2026-08-08T15:44:23Z, `new_task_id: -004`), yet
      `backlog_sibling_reset_guard_refused` fired 156+ MORE times for the SAME id `-002` afterward (11:38Z through past
      22:40Z, `existing_done_sha` unchanged at `2667e967d` the whole time) — contradicting the endpoint's own docstring
      claim that reminting makes "future regen ticks stop re-deriving that position back onto the collided id."
      `GET /api/backlog` also shows no `-004` row at all today — only `-002` (`done`), `-001`, `-003`, `-005`.
      Hypothesis (unverified): `regen_backlog_from_plan`'s per-plan matching for an ALREADY-yaml'd checkbox may still
      derive by POSITION-within-brief-group rather than by content, so removing the yaml row at `-002` (what remint
      does) doesn't stop the next regen tick from re-deriving a brand-new entry back at the SAME position/id. Needs
      someone to trace `_group_plan_tasks_by_brief` + `regen()`'s matching path for the specific
      `defi_catalog_engine_config_key_contract_drift_*.md` plan checkbox to confirm/refute. Not fixed here — out of the
      fate-decision todo's scope and touches the same collision-sensitive minting path Phase 1/2 are already carefully
      sequencing around. (repo: agent-orchestrator)

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — one live `state.db`; the never-half-migrated
  risk here is TEMPORAL (in-flight workers), not spatial (no multi-VM fan-out)
- `/codex/12-agent-workflow/commit-push-flip-rule.md` — evidence format for each todo flip

## Progress Log

- **2026-08-08 (interactive session, slot 1)**: Authored. Operator selected Option B (full backfill) over Option A
  (new-minting-only) and directed `assigned_vm: planning` + `status: active`. Phasing and gates come from a blast-radius
  map produced the same session, which is the prerequisite the source issue doc's 2026-07-31 entry required before any
  dispatch. The source doc stays `assigned_vm: NA` as the analysis SSOT — BLK-29884333 is not re-litigated, it is
  satisfied. Phase 1 is fully AO-dispatchable; Phase 2's two irreversible steps (scratch-copy dry-run, live apply) are
  `[OPERATOR]`-tagged because they copy/mutate live orchestrator state.

- **2026-08-08 (slot 9, content_derived_backlog_task_ids-001)**: Complete endpoint audit of `routes/slots_worker.py` and
  `routes/slots_ops.py`. Every endpoint classified. **ECHOED (client supplies `task_id` in request body) — 4
  endpoints:**
  1. `POST /api/slots/{slot_id}/progress` — `ProgressRequest.task_id` (`models/worker_api.py:82`)
  2. `POST /api/slots/{slot_id}/done` — `DoneRequest.task_id` (`models/worker_api.py:181`)
  3. `POST /api/slots/{slot_id}/blocked` — `BlockedRequest.task_id` (`models/worker_api.py:243`)
  4. `POST /api/slots/{slot_id}/unskip-task` — `UnskipTaskRequest.task_id` (`models/slots.py:155`) ← **NEW vs
     blast-radius map**

  **NOT-ECHOED — server derives task from `slot.current_task` or no task_id in model (remaining 17 endpoints):**
  `routes/slots_worker.py`: `/boot` (BootRequest — no task_id), `/heartbeat` (HeartbeatRequest — no task_id),
  `/messages` (GET). `routes/slots_ops.py`: `/message` (SendMessageRequest — no task_id), `/message-live`,
  `/transcript-tail` (GET), `/bootstrap` (query params only), `/reset-worktree` (query params only), `/spawn`
  (SpawnRequest — no task_id), `/claim` (GET), `/claim-interactive` (ClaimInteractiveRequest — no task_id),
  `/in-flight-files` (GET), `/reassign` (ReassignRequest — no task_id; uses `slot.current_task`), `/switch-account`
  (SwitchAccountRequest — no task_id), `/switch-model` (SwitchModelRequest — no task_id), `/skip-current-task`
  (SkipCurrentTaskRequest — no task_id; uses `slot.current_task`), `/clear-skips` (no body), `/clear-spawn-role` (no
  body), `/pause` (no body), `/resume` (no body), `/loop-interval` (LoopIntervalRequest — no task_id), `/log` (GET),
  DELETE (no body).

  **Migration note for `/unskip-task`**: `UnskipTaskRequest.task_id` is operator-facing (removes a per-slot skip
  exclusion via `ss.clear_slot_skip(session, slot_id, req.task_id)`). If a task is renamed while a slot skip row still
  holds the old id, the skip row survives under the old id and an `/unskip-task` call with the new id would silently
  no-op (skip not found, `cleared=False`). Phase 2 migration MUST remap `slot_skips.task_id` in the same pass as
  `tasks.id`.

  **Out of scope** (not in the two slot route files): `/api/backlog/{task_id}/park`, `/unpark` live in
  `routes/backlog.py` — task_id there is a PATH parameter (server-resolved), not a client-echoed body field. Separately,
  `routes/backlog.py` has body-task_id endpoints (`/reconcile-brief`, `/reopen`, `/park/mark-done`) but those are
  backlog-operator endpoints, not worker-facing; included here for completeness of the namespace scan.

- **2026-08-08 (slot 3, content_derived_backlog_task_ids-002)**: Added
  `_make_content_task_id(plan_ref, brief, occurrence)` and `_CONTENT_ID_HEX_CHARS = 12` to
  `server/regen_backlog_from_plan.py` (next to `_make_task_id`). Returns
  `f"{slug}-{sha256(plan_ref|brief|occurrence)[:12]}"`. `occurrence` included in hash per plan requirement
  (brief-collision hazard documented in `_group_plan_tasks_by_brief`). Added 5 tests in
  `tests/test_regen_backlog_from_plan.py` covering format, occurrence-differentiation, determinism, plan_ref-in-hash,
  and `_CONTENT_ID_HEX_CHARS` minimum floor. No call sites changed. QG: 2732 passed. Evidence:
  agent-orchestrator@ac36202 (feat) + e0f107a (pyright fix, both verified on origin/live-defi-rollout).

- **2026-08-08 (slot 16, content_derived_backlog_task_ids-003)**: Replaced placeholder floor test with measured
  birthday-bound assertion in `tests/test_regen_backlog_from_plan.py`. At n=2187 corpus rows (measured 2026-08-08) and
  p_target=1e-6 per regen tick, k_min=11; `_CONTENT_ID_HEX_CHARS=12` has 16x margin above that minimum. Test
  `test_content_id_hex_chars_birthday_bound` names the constant and fails if it shrinks below k_min. QG: 2732+ passed.
  Evidence: agent-orchestrator@0b1507e (verified on origin/live-defi-rollout).

- **2026-08-08 (slot 18, content_derived_backlog_task_ids-004)**: Switched the live minting call site (`regen()`'s
  per-plan add loop) from `_make_task_id(slug, next_index)` to
  `_make_content_task_id(plan_ref_str, description, _occurrence)`. Added `_load_all_db_task_ids(db_path)` (raw sqlite3,
  mirrors `_load_unconsumed_operator_rulings`'s pattern) so the collision check covers the FULL historical `tasks`
  table, not just yaml — a fresh id colliding with a live yaml row is skipped + logged ERROR (should be astronomically
  rare per the birthday-bound test); a fresh id colliding with a non-live DB-only row (done/pruned) is the EXPECTED
  content-stable case and proceeds, governed by the sibling-reset guard (`bootstrap.py`, kept as defence-in-depth per
  todo below). Removed the now-dead positional `next_index`/`existing_for_slug` block. `_make_task_id` itself is KEPT
  (still used by `routes/backlog.py`'s `remint_backlog_collision`, todo P3 below decides its fate) — annotated
  `# pyright: ignore[reportUnusedFunction]` now that its only caller is a cross-module private import. Updated 24 tests
  in `tests/test_regen_backlog_from_plan.py` that asserted hardcoded positional ids (`my_plan-001` etc.) to key off
  `brief` instead (`_by_brief` helper) since ids are no longer predictable strings; rewrote
  `test_regen_id_slot_reuse_inherits_stale_terminal_status` (renamed
  `test_regen_id_slot_reuse_no_longer_reissues_freed_slot`) to assert the FIX — a "totally different" checkbox no longer
  reissues a done row's freed id. QG: 2767 passed (full suite, incl. the two guard tests at `:3249`/`:3300` which are
  UNCHANGED — their own collision-injection todo, P2 below, is separately scoped).

  **Unplanned-but-blocking fix, same session**: local `quality-gates.sh` was red on a clean HEAD (7 pre-existing
  failures in `test_context_lifecycle.py` + `test_worker_liveness.py`, unrelated to this todo) — root-caused to a
  test-isolation gap (fixture session names like `orch-slot-9` collide with REAL slot config dirs on this shared 18-slot
  host, so an unmocked `context_probe.context_used_pct()` read genuine transcript data instead of `None`; invisible on
  CI's ephemeral runner). Fixed by mocking it in both files' worker-path fixtures. Full details + the root-cause
  diagnosis: `/plans/archive/issues/agent_orchestrator_local_qg_red_context_lifecycle_worker_liveness_2026_08_08.md`
  (archived since). Shipped in the SAME commit as the todo above (both were `git add`-staged together since the QG-red
  fix was a hard precondition for shipping anything from this repo on this host). Evidence: agent-orchestrator@ba6eff5
  (verified on origin/live-defi-rollout; QG PASSED 2767/2767 on this exact SHA before quickmerge).

- **2026-08-08 (slot 21, content_derived_backlog_task_ids-005)**: Rewrote both guard-test docstrings
  (`test_sync_resets_terminal_fields_when_id_reused_for_different_checkbox`,
  `test_sync_refuses_to_reset_a_done_row_on_id_reuse`). On inspection both tests already inject their id collision
  mechanically at the DB layer (hand-built `TaskRow` + `BacklogTask` sharing an id, no call through `_make_task_id`/
  `_make_content_task_id`/minting) — the gap was that their docstrings still narrated the OLD "freed positional slot
  reused by normal minting" production scenario, which Phase 1 (previous todo, `agent-orchestrator@ba6eff5`) closed.
  Rewrote both to frame the injection as deliberate/DB-layer, explicitly noting the guard remains meaningful against
  other collision sources (hand-edited `backlog.yaml`, a bug in the new minting collision check) so a future reader
  doesn't mistake the tests (or the guard itself) for testing something now-unreachable and remove them as vacuous. No
  production code changed; test-only docstring edit. QG: 2756 passed, 2 skipped (full suite, basedpyright clean).
  Evidence: agent-orchestrator@a746e83 (verified ancestor of origin/live-defi-rollout before `/done`).

- **2026-08-08 (slot 20, content_derived_backlog_task_ids-006)**: Added a "Guard disposition post-content-derived-ids"
  paragraph to `sync_backlog_to_db`'s docstring (`bootstrap.py`), recording the ruling in writing: the sibling-reset
  guard's original trigger (positional-id reuse) is structurally closed by Phase 1's switch to `_make_content_task_id`,
  but the guard is explicitly KEPT as defence-in-depth against a hand-edited `backlog.yaml` or a latent bug in the new
  minting's own collision check (`_load_all_db_task_ids`). NULL-`brief_hash` backfill branch noted unchanged, pointing
  to its own existing paragraph. Docstring-only change, no production logic touched. `.venv` was absent on this slot's
  agent-orchestrator clone (fresh worktree); ran `uv sync --all-extras` to build it before Pass-1. QG: 2773 passed (full
  suite). Evidence: agent-orchestrator@5ae9dd5 (verified ancestor of origin/live-defi-rollout before `/done`).

- **2026-08-08 (slot 26, content_derived_backlog_task_ids-007, review craft dispatched off
  `cefi_track2_backfill_vm_preempted_no_recovery-003` then reassigned to this backend_engineer task on next
  heartbeat)**: Decided `remint_backlog_collision`'s fate — **KEEP**, not retire. Checked the todo's own premise
  ("structurally unreachable post-Phase-1") against live activity data before accepting it:
  `GET /api/activity?type=backlog_sibling_reset_guard_collision_reminted` shows 173 fires 2026-07-26..2026-08-08,
  **including 156+ for `defi_catalog_engine_config_key_contract_drift-002` alone AFTER** the Phase-1 minting switch
  (`agent-orchestrator@ba6eff5`, landed 2026-08-08T14:28:06Z) — the premise was wrong for pre-existing positional-id
  rows, which Phase 1 never touches (only fresh mints go through `_make_content_task_id`); only Phase 2's not-yet-run
  historical backfill retires the need for this endpoint. Also confirmed it's wired into the dashboard's one-click "Fix"
  UI with its own e2e spec — retiring it would regress that too. Recorded the ruling + evidence in the endpoint's own
  docstring (`routes/backlog.py`), following this plan's established "record the guard disposition in the docstring"
  pattern from todo `-006`. No test changes (nothing retired). `.venv` was absent on this slot's agent-orchestrator
  clone; ran `uv sync --all-extras` before Pass-1. QG: 2816 passed (full suite, basedpyright clean). Evidence:
  agent-orchestrator@e47eb50 (verified ancestor of origin/live-defi-rollout before `/done`). Filed a new Follow-up todo
  for a genuinely new, out-of-scope finding surfaced during this investigation: the `-002` collision kept recurring even
  after an explicit remint at 2026-08-08T15:44:23Z, contradicting the endpoint's own claim that reminting stops future
  re-derivation at the same position — needs a `regen_backlog_from_plan` matching-path trace to confirm/refute, not
  fixed here.

- **2026-08-08 (slot-7, content_derived_backlog_task_ids-008, Phase 2 todo 1)**: Built
  `scripts/orchestrator/build_content_id_migration_map.py` (+ `tests/test_build_content_id_migration_map.py`, 11 tests)
  and ran it read-only against the LIVE `state.db` + `backlog.yaml`. **No writes to either store.**

  **Why the new id can't bit-match a fresh `_make_content_task_id` call**: that function hashes the PLAINTEXT brief
  (`sha256(plan_ref|brief|occurrence)`), but `TaskRow` never stores plaintext brief — only `brief_hash = sha256(brief)`
  — and for a `done` row whose yaml entry is pruned, the plaintext is permanently gone (confirmed again reading
  `sync_backlog_to_db`'s own docstring: no VCS history on backlog.yaml, no archive writer, `activity_log` never stores
  brief/title). A hash cannot be un-hashed, so no formula recovers it. The script instead derives
  `sha256(plan_ref|brief_hash|dup_index)` — same shape, `brief_hash` substituted for the unrecoverable plaintext.
  `dup_index` mirrors `_group_plan_tasks_by_brief`'s own "sorted by old id ascending" disambiguation for rows sharing an
  identical (plan_ref, brief_hash) — the same hard-wrap-collision case `_make_content_task_id`'s docstring documents for
  `occurrence`.

  **De-risking finding (verified against code, not assumed)**: a migrated id does NOT need to bit-match a live
  `_make_content_task_id` recomputation to avoid a duplicate mint on the next regen tick. Traced `regen()`'s matching
  path (`regen_backlog_from_plan.py` ~:1922-1952): the RECONCILE branch matches an open todo to an existing task by
  `(plan_ref, brief-TEXT)` via `_group_plan_tasks_by_brief` — **never by comparing task_id** — and keeps whatever id the
  matched row already has. `_make_content_task_id` is only ever called when NO existing task matches the brief at all (a
  genuinely new todo). So renaming a still-`queued` row is safe for regen correctness, PROVIDED `backlog.yaml`'s `id:`
  field and `state.db`'s `tasks.task_id` are renamed in the same operation — which the Phase 2 apply todo below already
  requires for the two-store-divergence reason. This directly informs (de-risks, doesn't change the plan of) the
  "Enforce the dispatched-row deferral" and "Make the migration idempotent" todos below.

  **Live run** (2026-08-08T23:06Z): 2445 rows, matches `SELECT COUNT(*) FROM tasks` exactly (done-when met).
  - 2342 derived (positional → content)
  - 92 already content-derived (Phase 1 fresh mints since `agent-orchestrator@ba6eff5` landed — correctly passed through
    as no-ops, not re-derived)
  - 11 unrecoverable (`brief_hash IS NULL`, the permanent legacy tail — down from the 38 baseline recorded 2026-07-20,
    consistent with that ruling's "shrinks under normal operation" prediction)
  - 0 unrecoverable-no-slug, 0 slug mismatches (id-prefix vs plan_ref-derived slug agreed on every row), **0 new_id
    collisions** (the critical safety check the script performs — verified on the real corpus, not just unit tests)
  - 1895 orphan rows (no yaml counterpart) — the `done`+pruned audit-history tail this whole effort protects

  Artifact: `agent-orchestrator/scripts/orchestrator/content_derived_backlog_task_ids_2026_08_08_id_map.json` (847 KB,
  compact JSON — added to `.prettierignore` since Prettier's pretty-print pushed it past the repo's 1000 KB pre-commit
  large-file gate on every regen; same precedent as `data/state/state.json`). Re-runnable per the script's own docstring
  (`--db`/`--backlog`/`--out`); exit code is 1 if collisions are ever found on a future run (loud failure, not silent).
  QG: 2821 passed, 2 skipped (full suite, basedpyright clean). Evidence: agent-orchestrator@8a8454c (verified ancestor
  of origin/live-defi-rollout before this flip).

- **2026-08-08 (slot-18, content_derived_backlog_task_ids-009, Phase 2 todo 2)**: `build_content_id_migration_map.py`
  previously included the `brief_hash IS NULL` tail INSIDE `entries` (with `new_id=null`), which would have forced every
  downstream consumer (the not-yet-built prereq-remap assertion + apply scripts) to special-case `new_id is None` on
  every read. Moved those rows to a new top-level `excluded_null_brief_hash` list (a new `ExcludedEntry` TypedDict —
  `old_id`/`plan_ref`/`status`/`done_sha`/`orphan`/`reason`, no `new_id`/`dup_index` since neither is meaningful) so
  `entries` now contains ONLY rows a future apply step can rename/no-op unconditionally. Full-corpus accounting is
  preserved (nothing silently dropped): `main()`'s row-count assertion now checks
  `len(entries) + len(excluded_null_brief_hash) == SELECT COUNT(*) FROM tasks`, and `orphan_rows` sums across both
  lists. `unrecoverable_null_brief_hash` count renamed `excluded_null_brief_hash` throughout (`MapCounts`, docstring,
  CLI summary) to match the new semantics. The other unrecoverable case (no positional id-suffix + no `plan_ref`) is
  UNCHANGED — it is not ruled permanent, so it stays inside `entries` with `new_id=null` as a loud hard-stop. Updated 4
  of the 11 existing unit tests in `tests/test_build_content_id_migration_map.py` to assert the new split (moved count,
  `excluded_null_brief_hash` list membership, orphan flag now read from that list for a NULL-brief_hash row). **Report
  the count** (this todo's own done-when): re-ran the script read-only against the LIVE `state.db` + `backlog.yaml`
  (2026-08-08T23:53Z) — **11 of 2449 rows permanently excluded** (`brief_hash IS NULL`), matching the `-008` baseline
  exactly (no drift since that run); `entries` now holds 2438 rows (97 already-content-derived + 2341 derived + 0
  no-slug), 0 collisions, 0 slug mismatches. Output written to a scratch path outside the repo (this script never writes
  to a root clone; the checked-in artifact from `-008` is unchanged). QG: 2840 passed (full suite, basedpyright clean,
  ruff clean). Evidence: agent-orchestrator@b143bf5 (verified ancestor of origin/live-defi-rollout before this flip).

- **2026-08-09 (slot-23, content_derived_backlog_task_ids-010, Phase 2 todo 3)**: Built
  `scripts/orchestrator/verify_prereq_remap_coverage.py` (+ `tests/test_verify_prereq_remap_coverage.py`, 12 tests).
  Classifies every `completed_tasks`/`prerequisites` reference in the live `backlog.yaml` against the proposed
  id-migration map into 4 buckets: **remapped** (genuine rename in the map — asserted to resolve to the new id),
  **unchanged** (accounted for in the map but keeps its id — passthrough / permanently-excluded NULL-brief_hash tail /
  unrecoverable no-slug row), **legit_absent** (not a live `tasks` row at all, checked fresh against `--db` — the exact
  case `_completed_task_satisfied` already tolerates), **unexplained** (IS a live row but the map doesn't account for it
  — the map is stale relative to the live corpus; this is the only classification that fails the gate, exit 1).
  Schema-tolerant of both the pre- and post-`-009` artifact shapes (the checked-in artifact predates `-009`'s
  `excluded_null_brief_hash` split — malformed/missing fields are defensively dropped, not raised, mirroring
  `server/dedup_state.py`'s best-effort JSON-state convention, rather than trusting `json.loads`'s `Any` return).

  **First live run surfaced real staleness, not a script bug**: running against the checked-in `-008`-era artifact (last
  regenerated 2026-08-08T23:06Z) reported **82 unexplained references** — every one a `completed_tasks` entry pointing
  at a task Phase 1's live content-id minting created in the ~9h since the artifact was built (e.g.
  `sports_taxonomy_p1_capture_and_contracts-<hex>`, satellite-batch finalize chains). This is squarely hazard 2's real
  failure mode (a map that doesn't know about a live row), so per this script's own docstring guidance ("Rebuild it with
  build_content_id_migration_map.py before trusting this map"), re-ran `build_content_id_migration_map.py` against the
  LIVE `state.db`/`backlog.yaml` (2026-08-09T01:20Z) to refresh the checked-in artifact — now 2452 entries + 11
  permanently-excluded (2463 total, matches live `tasks` count exactly), 0 collisions. Re-running the new assertion
  against the refreshed artifact: **1198 references checked, 966 remapped, 106 unchanged, 126 legit_absent, 0
  unexplained** — done-when met. Refreshing the artifact also incidentally closes the `-009` Progress Log's noted gap
  ("the checked-in artifact from -008 is unchanged") — it now matches the current script's schema. QG: 2852 passed, 2
  skipped (full suite, basedpyright clean, ruff clean — pre-existing unrelated thread-exception warnings in
  `test_operator_gated_blocked` and JWT short-key warnings in `test_internal_auth_asymmetric`, not touched by this
  change). Evidence: agent-orchestrator@d86827b (verified ancestor of origin/live-defi-rollout before this flip).

- **2026-08-09 (slot-23, content_derived_backlog_task_ids-011, Phase 2 todo 4)**: Implemented hazard 1's gate. Added
  `server/content_id_migration.py` as the single shared decision point (`is_rename_eligible` / `pending_rename_for` /
  `resolve_deferred_rename` / `rename_yaml_task`) — reads old->new from the already-built, verified migration map
  artifact (`-010`'s refreshed 2452-entry artifact) rather than a live recomputation, so a per-row deferred rename can
  never disagree with what the (separate, operator-gated) bulk apply would compute for the same row. Wired into the
  three named transition points: `done_slot` (after `mark_done`), `_prune_stale`'s cancel path (after the
  dispatched->cancelled UPDATE — no yaml touch needed, every cancelled id is by construction already an orphan being
  pruned from yaml in the same pass), and `/skip-current-task`'s release (after the cooldown/auto-park block, so the
  rename can't shift the id out from under those — deliberately-OLD-id-keyed — calls mid-request; those namespaces are
  `-012`'s separate scope). `done_slot`/skip-current-task also rename the matching `backlog.yaml` entry in the same
  operation when one still exists — skipping that would let `sync_backlog_to_db` re-derive a fresh `queued` row at the
  old id on the next regen tick (confirmed by reading `sync_backlog_to_db`'s own id-matching logic), reintroducing the
  exact two-store divergence this migration exists to fix.

  **Real bug caught by the tests, not just written around**: both ORM call sites run `session_scope()` sessions with
  `autoflush=False` (see the existing M3 dual-flip-warning comment in `slots_worker.py`). The first implementation
  issued the raw `UPDATE tasks SET task_id=...` immediately, before the ORM's own pending `row.status=...` write (still
  unflushed) — on session close, SQLAlchemy tried to flush that pending UPDATE keyed on the now-renamed-away old
  `task_id` and raised `StaleDataError: expected to update 1 row(s); 0 were matched`. Fixed with an explicit
  `session.flush()` immediately before the raw rename in both hooks.

  Tests: `tests/test_content_id_migration.py` (19 tests, pure decision logic — `resolve_deferred_rename` never returns a
  rename for `status="dispatched"` even with a real pending map entry; returns the mapped id for every other status;
  cache mtime-invalidation; yaml rename-in-place preserving sibling tasks) + `tests/test_content_id_migration_wiring.py`
  (6 tests, live wiring at all three call sites, including the negative case: a `_prune_stale` row that stayed
  `dispatched` this tick — the done-not-removed race exception — is never renamed even with a pending map entry). QG:
  2879 passed, 2 skipped (full suite, basedpyright clean, ruff clean — the same two pre-existing unrelated warnings as
  `-010`, not touched by this change). Evidence: agent-orchestrator@6b57503 (verified ancestor of
  origin/live-defi-rollout before this flip).
