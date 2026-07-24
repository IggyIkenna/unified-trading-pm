---
doc_type: issue
title: "backlog regen id-slot reuse inherits stale status/dispatched_to/done_sha from a prior, unrelated checkbox"
summary:
  "data_engineering (slot-9, 2026-07-15), working cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch-003.
  Added a new [INFRA] checkbox (4th checkbox) to that issue doc after its 1st checkbox had already flipped ✅ and been
  removed from active derivation. POST /api/backlog/regen assigned the new checkbox the SAME id suffix (`...-004`) the
  completed 1st checkbox previously held, but the DB row kept that old task's `status: done`, `dispatched_to: 11`,
  `done_sha: 5d44a197` — so the brand-new, never-dispatched INFRA todo displayed as already `done`. Left unnoticed, the
  dispatcher would never route it (no worker picks up a `done` task), silently dropping real work while the plan
  checkbox itself correctly showed `- [ ]`. Worked around live via `DELETE /api/backlog/<id>` + `POST
  /api/backlog/reload` + `POST /api/backlog/regen`, which re-derived the same id with clean `status: queued,
  dispatched_to: null, done_sha: null` — confirming the bug is in the id-reuse path specifically, not a permanent hash
  collision."
status: resolved # both actionable todos [x], agent-orchestrator@4695db6 ships the fix + regression coverage
priority: P2
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [backlog, regen, id-collision, tooling-defect, dispatch]
related: [/plans/active/issues/cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md]
created: 2026-07-15
parent_epic: agent_operating_framework_master
assigned_vm: planning
source:
  "Directly observed live via the /api/backlog HTTP surface while working task
  cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch-003: filed a new todo, ran POST /api/backlog/regen, the
  returned task JSON for the new todo carried the previous, unrelated task's terminal fields."
locked_by:
locked_since:
resolved_by: "slot-11 (todo 1), slot-10 (todo 2), agent-orchestrator@4695db6"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# backlog regen: id-slot reuse inherits stale terminal status from a prior checkbox

## What I found

`POST /api/backlog/regen` (and by extension whatever `regen_backlog_from_plan.py` code path it drives) appears to derive
a task's numeric id suffix in a way that is **not stable per-checkbox-content** — when an earlier checkbox in a plan
file is completed (flips `- [x]` and drops out of active derivation) and a NEW checkbox is later added to the same file,
the new checkbox can be assigned the SAME id suffix the completed checkbox used to hold. The DB/YAML row for that id was
not reset on reuse: it retained the completed task's `status: "done"`, `dispatched_to`, and `done_sha`, even though the
row's `title`/`brief` now describe the brand-new, never-worked checkbox.

Concretely, in `plans/active/issues/cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md`:

- Checkbox 1 ("Fix venue_fetch.py...") → task id `...-004`, completed by slot-11, `done_sha=5d44a197`.
- I appended a 4th checkbox ("Confirm a fresh MTDS deployment tarball exists...") after the 3rd.
- `POST /api/backlog/regen` created it as id `...-004` (colliding with checkbox 1's old id) with
  `status: "done", dispatched_to: 11, done_sha: "5d44a197"` already populated — despite the plan file showing `- [ ]`
  (not done) and no worker having ever touched it.

**Confirmed workaround, not a fix**: `DELETE /api/backlog/<id>` (which scrubs both the DB row and the YAML entry) +
`POST /api/backlog/reload` + `POST /api/backlog/regen` re-created the same id suffix with clean
`status: "queued", dispatched_to: null, done_sha: null`. This proves the defect is specifically in how an EXISTING id
row is reused/updated during regen — a fresh derivation (no pre-existing row to collide with) produces the correct
state.

## Why it matters

- **Silent work loss**: a task that displays `status: "done"` is never picked up by `pick_next_task()` — a worker would
  see the checkbox `- [ ]` in the plan file (truth) but the backlog (what actually dispatches work) would disagree and
  nothing would ever route it. This is exactly the class of defect the `/boot-per-shippable-unit` discipline exists to
  prevent (dashboard under-reporting reality, morning audit impossible).
- Any plan that appends a new checkbox AFTER an earlier one in the same doc has already completed is at risk — this is a
  common, ordinary pattern (issue docs accrete todos as investigation proceeds), not an edge case.
- I caught this only because I happened to cross-reference the returned JSON's `status`/`done_sha` against the plan
  file's own `- [ ]` marker before trusting the API. A worker that only checks `/api/backlog` (not the underlying plan
  file) would not have noticed and would have treated the todo as already resolved.

## Recommended decision

1. **Root-cause the id-derivation function** in whatever module backs `POST /api/backlog/regen` /
   `regen_backlog_from_plan.py` (agent-orchestrator repo — exact file not yet located this session). Determine whether
   ids are derived positionally (nth checkbox in file) vs. content-hash — the observed behavior (checkbox 1's old id
   reassigned to checkbox 4) suggests positional derivation among some checkbox subset, which will always be liable to
   reuse a freed slot's id.
2. **On regen, when an id is reused for DIFFERENT checkbox content, reset ALL terminal fields** (`status`,
   `dispatched_to`, `done_sha`, `queued_at`) to fresh `queued` state rather than only updating `title`/`brief`. This is
   the minimal fix — keeps the current derivation scheme but prevents stale-field leakage.
3. Alternatively (larger fix, not required to close this doc): derive ids from a stable hash of checkbox TEXT content
   (or plan_ref + first N chars of the checkbox body) so a given checkbox's identity survives file edits without
   colliding with unrelated checkboxes' freed slots.

- [x] [SCRIPT] P2. ✅ — agent-orchestrator@45446d8. Located: `_make_task_id`/`next_index` in
      `server/regen_backlog_from_plan.py` (`regen()`'s per-plan-slug loop) — POSITIONAL, derived from
      `max(existing YAML id suffix for this slug) + 1`, recomputed fresh from `backlog.yaml` at the top of every
      separate `regen()` call; never content-hash-based, never consults `state.db`. `_prune_stale` removes a task's YAML
      row the instant its brief drops out of open todos, REGARDLESS of terminal status, while deliberately leaving
      `done`/`dispatched` `state.db` rows untouched (only queued/blocked+undispatched rows are DB-deleted) — so a later
      regen tick can reissue the freed id to an unrelated new checkbox, and `sync_backlog_to_db` (called right after
      `regen()` in the `POST /api/backlog/regen` handler) only inserts a `TaskRow` when none exists for that id,
      silently preserving the old row's `status`/`dispatched_to`/`done_sha`. Added
      `test_regen_id_slot_reuse_inherits_stale_terminal_status` in `tests/test_regen_backlog_from_plan.py` reproducing
      the exact repro end-to-end (complete + prune a checkbox in one tick, append an unrelated new checkbox in a later
      tick, `regen()` + `sync_backlog_to_db()` as the endpoint does) — currently `xfail(strict=True)` pending todo 2's
      fix; verified it fails at the intended assertion via `--runxfail`. (repo: agent-orchestrator)
- [x] ✅ [SCRIPT] P2. Fix the reuse path to reset terminal fields (`status`, `dispatched_to`, `done_sha`, `queued_at`)
      whenever a regen assigns an existing id to different checkbox content (compare stored title/brief hash, not just
      id string equality). (repo: agent-orchestrator) — agent-orchestrator@4695db6. Added
      `TaskRow.brief_hash =     sha256(brief)` (migrated via the existing ALTER-TABLE pattern); `sync_backlog_to_db` now
      compares it on every existing row and, on mismatch, resets
      status/dispatched_to/dispatched_at/dispatched_worktree/done_sha/done_at/
      done_evidence/done_verification_json/failover_origin/queued_at to a fresh queued state (a NULL hash — a
      pre-migration row — only backfills on first sync, never resets). Removed the `xfail(strict=True)` marker on
      `test_regen_id_slot_reuse_inherits_stale_terminal_status` (now passes) + added 3 unit tests in
      `tests/test_regen_backlog_from_plan.py`. Both todos in this issue doc are now closed.
