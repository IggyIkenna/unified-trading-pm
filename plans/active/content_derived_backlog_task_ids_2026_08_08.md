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
- [ ] [BACKEND] P3. **Decide `remint_backlog_collision`'s fate** (`routes/backlog.py:545-687`). Its premise — a
      positional id got reused — is structurally unreachable post-Phase-1. Check whether it has ever actually fired (its
      own `backlog_sibling_reset_guard_collision_reminted` activity event answers this), then either retire it with its
      test, or repurpose it as a general "force a task onto a fresh id" admin tool. Record which and why. (repo:
      agent-orchestrator)

## Phase 2 — historical backfill (Option B). Every irreversible step is operator-gated.

- [ ] [BACKEND] P1. **Build the old→new id map as a REPORT ONLY — no writes.** For every row, derive the new id from the
      ALREADY-STORED `TaskRow.brief_hash` (`orm.py:70`; `sync_backlog_to_db` has populated it since @4695db6), so no
      plaintext re-derivation is needed. Recover the slug from the old id's prefix, or from `TaskRow.plan_ref` for
      orphan `done` rows with no yaml counterpart (the `_orphan_view` case, `routes/backlog.py:67-101`). Emit the map as
      a durable artifact. Done-when: the artifact exists and its row count matches `SELECT COUNT(*) FROM tasks`. (repo:
      agent-orchestrator)
- [ ] [BACKEND] P1. **Exclude the NULL-`brief_hash` tail from the map, permanently.** Those rows' briefs are documented
      unrecoverable (`bootstrap.py:710-727` — backlog.yaml is gitignored, no VCS history, no archive writer,
      activity_log never stored the brief), so they can never get a content id. This mirrors the already-ruled "(c)
      accept permanently" decision for that tail; it is not reopened here. Report the count. (repo: agent-orchestrator)
- [ ] [BACKEND] P1. **Write the pre/post prereq-remap assertion — hazard 2's gate.** Diff every
      `completed_tasks`/`prerequisites` array before and after the proposed map and assert each old id is either
      remapped or was ALREADY legitimately absent pre-migration. A missed remap does not error at runtime
      (`_completed_task_satisfied` treats absent as satisfied) — it silently un-gates. This assertion is the only thing
      that catches it. Done-when: the check runs against the Phase-2 map artifact and reports zero unexplained entries.
      (repo: agent-orchestrator)
- [ ] [BACKEND] P1. **Enforce the dispatched-row deferral — hazard 1's gate.** The migration must SKIP any row whose
      status is `dispatched` and defer its rename to the transition points that already fire on terminal state
      (`done_slot` finalization, `_prune_stale`'s cancel path, `/skip-current-task`'s release). With this ordering
      honored, **no id-alias/back-compat column is needed**. Done-when: a test proves a `dispatched` row is never
      renamed by the migration and is renamed correctly once it goes terminal. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. **Do NOT rewrite `activity_log` or `compactions` rows in place.** Rewriting a past audit entry to an
      id it did not happen under is itself the audit-integrity violation this whole effort exists to prevent. Instead
      append a `backlog_task_id_migrated {old_id, new_id}` activity row per rename so old→new stays resolvable.
      **Also**: `activity_log.task_id` carries synthetic non-task labels (`plan_health.py:1008` writes
      `doc_drift:<key>`) — any walker assuming every non-null value is a real backlog id WILL corrupt those rows. (repo:
      agent-orchestrator)
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
