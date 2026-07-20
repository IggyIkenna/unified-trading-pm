---
doc_type: issue
title:
  "Backlog regen derives task ids POSITIONALLY, not from content — a completed todo re-read as open can re-dispatch
  under a shifted id and wipe a sibling's done history (R7's surviving half)"
summary: |
  `regen_backlog_from_plan` derives a task id as `slug + next free index` (`_make_task_id`, `next_index = max(used)+1`),
  so a todo's id is a function of its POSITION among that plan's open todos, not of its text. Three guards already make
  this safe in the common case: a brief-keyed reconcile updates a matching todo in place (keeping its id), a
  cross-plan brief match is skipped, and `TaskRow.brief_hash` (@4695db6) resets terminal fields when an id is reused for
  different content. What survives is the composition of two rarer conditions: if a COMPLETED todo is re-read as `- [ ]`
  (its yaml entry was pruned, so neither `existing_ids` nor `existing_briefs` remembers it) AND its derived index has
  shifted onto a sibling's id, the brief_hash guard fires the wrong way — it resets the SIBLING's row to `queued`,
  re-dispatching work that is already done and destroying that sibling's `done_sha`/`done_at` audit history. Requires an
  external race to read a `[x]` as `[ ]`; that race is not hypothetical — the AO's plan clone was frozen 23 commits
  behind for two days (ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16). Separately, the `done` rows carrying
  `brief_hash IS NULL` are exempt from the guard by documented design and can never be protected by it — a live-state
  count that MOVES (56 of 66 at 2026-07-17T13:19Z, vs 58 of 64 a day earlier), so re-run the query rather than cite a
  figure. Every unhashed row is a `done` row, which bounds the exposure and retires half the original reasoning for the
  exemption.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, backlog, regen, task-id, id-collision, brief-hash, audit-history, dispatch]
related:
  [
    ../../archive/2026_07/ao_dispatch_hardening_2026_07_16.md,
    ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md,
    backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    ../../archive/issues/backlog_regen_id_reuse_stale_status_2026_07_15.md,
    ../../archive/issues/ao_dispatch_residuals_2026_07_15.md,
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
  - "ao_dispatch_residuals_2026_07_15 R7 (`Task-ID instability across regen`) — that index is the ONLY doc that carried
    R7, and it archives with ao_dispatch_hardening's Phase 4 close-out. This doc is R7's successor home so the residual
    does not go dark."
  - "ao_dispatch_hardening_2026_07_16 § 'Do NOT implement the source docs' literal remedies' — ruled R7's content-hash
    rewrite OUT of scope (high blast radius) and its dangerous half already fixed at @4695db6."
  - "Code re-verified at agent-orchestrator@3f265cc, 2026-07-17 (this doc's mechanism section cites file:line)."
---

> **🟢 EXECUTION CONSOLIDATED 2026-07-17** — this doc's open items are now tracked and executed via
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md)
> (operator-session local plan; verified-live classification table there). Do NOT start work from this doc alone — flip
> items in the plan and mirror them here. This doc stays the detail/evidence record.

# Regen task ids are positional, not content-stable (R7's surviving half)

> **Why this doc exists.** R7 lived only in `ao_dispatch_residuals_2026_07_15`, a tracking INDEX with no todos of its
> own. That index archives now that `ao_dispatch_hardening_2026_07_16` has homed R1–R6. Archiving it while R7 still had
> nowhere to live would repeat the precise mistake
> [`ao_autospawn_role_blind_dispatch_starvation_2026_07_14`](../../archive/issues/ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md)
> records in its own banner — archived with live `- [ ]` bugs and no `superseded_by`, which orphaned them until a plan
> two days later happened to rediscover them. The index's suggested owner
> (`ao_dispatch_correctness_regen_reconcile_2026_07_07`) is itself archived, so there is no active plan to fold R7 into.

## The mechanism (verified against code, not inferred)

Task ids are derived from POSITION:

- `_make_task_id(slug, index)` — `server/regen_backlog_from_plan.py:1024`
- `next_index = max(used) + 1` over ids already in **backlog.yaml** — `:1223-1229`
- `existing_ids` / `existing_briefs` are built from **the yaml, not the DB** — `:1130`, `:1135`

Three guards already close the common cases, and they are why this is P2 and not P0:

1. **Brief-keyed reconcile (same plan)** — `plan_tasks_by_brief` (`:1217`): a todo whose brief matches an existing task
   from the same `plan_ref` is UPDATED in place, keeping its id. A reworded-but-repositioned todo does not churn.
2. **Cross-plan brief skip** — `:1271`: a brief already mapped to a task in another plan is skipped, never duplicated.
3. **`TaskRow.brief_hash`** — `server/bootstrap.py:354-374` (@4695db6): if an existing row's stored hash disagrees with
   the incoming brief, the id was reused for different content → every terminal field
   (`status`/`dispatched_to`/`done_sha`/`done_at`/…) resets to a fresh `queued`.

**The surviving gap is guard 3 firing in the wrong direction.** A completed todo's yaml entry is pruned (it is no longer
an open todo) while its DB row is retained as `done` (audit history). So the yaml — the only thing regen consults — has
no memory of it. If something re-reads that `[x]` todo as `- [ ]`:

- **It re-derives onto its OWN old id** → `brief_hash` MATCHES → `bootstrap.py:375` `continue` → row stays `done` → not
  re-dispatched. **Safe**, and this is the likely case.
- **It re-derives onto a SIBLING's id** (a neighbour completed and dropped out, shifting the index) → `brief_hash`
  MISMATCHES → the guard resets **the sibling's** row → the already-done todo is re-dispatched under the sibling's id,
  and the sibling's `done_sha`/`done_at`/`done_evidence` are destroyed. **This is the bug.**

It needs an external race to read a `[x]` as `[ ]`. That race is **not hypothetical**: the AO's plan clone was frozen 23
commits behind for two days
([`ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16`](ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md)),
which is exactly a machine serving flipped checkboxes as unflipped.

## The second, permanent hole: NULL `brief_hash` rows are exempt by design

`server/bootstrap.py:352-353` backfills a NULL hash from the INCOMING brief and `continue`s — it never resets. The
docstring (`:338-341`) is explicit and the reasoning is sound: _"we can't retroactively know whether a pre-migration row
matches, and resetting an in-flight task's live status on a schema upgrade would be its own outage."_
`tests/test_regen_backlog_from_plan.py:2036` pins the behaviour, and its docstring names **"in-flight/done"** — so
`done` rows were considered, not overlooked.

The consequence nobody bounded: **a `done` row with `brief_hash IS NULL` whose id is reused silently adopts the new
content's hash and KEEPS `status=done`** — the new todo reads as already complete and never dispatches. That is
precisely the bug @4695db6 was written to kill, still live on any legacy row, permanently. The fix cannot be "reset
them" — that would re-dispatch every completed task in the tail.

**Measured live on the central VM (`/var/lib/orchestrator/state.db`), 2026-07-17T13:19:08Z:**

```
tasks_total=90   done_total=66
done_brief_hash_NULL=56
any_status_brief_hash_NULL=56     <- every NULL-hash row is a `done` row
```

Two things that number tells you, and one trap:

- **The exposure is BOUNDED to `done` rows.** `any_status_brief_hash_NULL == done_brief_hash_NULL == 56`: not one
  `queued`/`blocked`/`dispatched` row is unhashed, because the backfill catches a row the moment regen touches it. So
  the "resetting an in-flight task would be its own outage" half of the docstring's reasoning **no longer binds** —
  there are no in-flight NULL rows left to protect. That materially widens the options in todo 1 below.
- **The count MOVES — re-measure, never cite this figure.** It read **58 of 64** on 2026-07-16 and **56 of 66** a day
  later. Rows enter (`done_total` +2) and leave the NULL set (−2) as regen touches them. Any doc quoting a fixed number
  here is stale on arrival; run the query.

This is the same row set as
[`backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16`](backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md)'s
unauditable tail, reached from a different direction: there they are un-AUDITABLE, here they are un-GUARDED.

## Todos

- [ ] [BACKEND] P2. **Bound the NULL-`brief_hash` tail.** Decide and record ONE of: (a) backfill the hash from a
      trustworthy source (the plan text at each row's `done_sha` — `git show <done_sha>:<plan_ref>` shows what was
      `[x]`'d at completion, which is the same first-line text the brief stores), (b) age the exemption out (rows past N
      days can never be in-flight, so a mismatch is safe to reset), or (c) accept permanently with a WHY recorded in the
      docstring + a count that is monitored, not merely known. **Do not simply reset them** — every completed task in
      the tail would re-dispatch. **Start from the measured fact that every unhashed row is `done`** (there are no
      in-flight NULL rows left): the docstring's stated reason for the exemption is half about not wiping an in-flight
      task's live status, and that half no longer applies, so (b) is cheaper than it looks. **Gate**:
      `select count(*) from tasks where status='done' and brief_hash is null` is either 0, or non-zero with a recorded
      decision AND a check that alarms if it GROWS — growth is the real signal, since a NEW unhashed row would mean the
      backfill path has regressed.
- [x] ✅ [BACKEND] P3. **Make the sibling-reset case impossible or loud.** — `agent-orchestrator@9c7a0fd`
      (`ao_backlog_regen_integrity_2026_07_20.md` todo 1). `sync_backlog_to_db` now refuses to reset a row that is
      `done` with a `done_sha` on brief_hash mismatch, logging an ERROR (new brief + both hashes — the old plaintext
      isn't stored). **Accepted cost**: this also blocks the legitimate "id reused for a NEW todo" case — such a todo
      will silently read as `done` and never dispatch until manually fixed. That's the deliberate trade-off (protect
      audit history over correct auto-routing); todo below (content-derived ids) is the real fix if this proves
      insufficient. **Gate**: `test_sync_refuses_to_reset_a_done_row_on_id_reuse` (new) + 2 existing tests updated to
      the new contract; bug-injected (guard disabled → both dependent tests red; restored → green).
- [ ] [BACKEND] P3. **Content-derived ids — the real fix, deliberately NOT scoped here.**
      `ao_dispatch_hardening_2026_07_16` ruled the content-hash rewrite out (blast radius: `existing_ids` bookkeeping,
      `slot_skips` keyed by task_id, dashboard/API id refs, `done_sha` history). That ruling stands. Re-open ONLY if the
      two todos above prove insufficient — this todo exists so the decision is visible rather than forgotten.

## Progress Log

- **2026-07-20** — Sibling-reset guard todo landed (`agent-orchestrator@9c7a0fd`, via
  `ao_backlog_regen_integrity_2026_07_20.md` todo 1). See the fix-todo checkbox above for the guard's behavior and its
  accepted trade-off (blocks legitimate id-reuse-for-new-todo too).
- **2026-07-17** — Filed as R7's successor home during `ao_dispatch_hardening_2026_07_16` Phase 4 close-out. R7's
  original one-line framing ("a checked-off `[x]` todo can be re-derived under a fresh task id and re-dispatched") was
  **checked against code and is imprecise**: the brief-keyed reconcile (`:1217`) and cross-plan skip (`:1271`) mean a
  re-read todo landing on its own id is correctly left alone. The real failure needs a position SHIFT as well as a stale
  read, and its worst consequence is not the re-dispatch — it is the **sibling's destroyed `done_sha`**. Recording the
  corrected mechanism here rather than carrying the original wording forward, because the original would have sent the
  next reader looking for a bug that is already guarded.
