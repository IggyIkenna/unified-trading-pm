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
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, backlog, regen, task-id, id-collision, brief-hash, audit-history, dispatch]
related:
  [
    ../../archive/2026_07/ao_dispatch_hardening_2026_07_16.md,
    /plans/archive/issues/ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md,
    /plans/archive/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    ../../archive/issues/backlog_regen_id_reuse_stale_status_2026_07_15.md,
    ../../archive/issues/ao_dispatch_residuals_2026_07_15.md,
    ../../epics/orchestrator_master.md,
  ]
created: 2026-07-17
author: unknown
last_updated: 2026-07-31 # (RULED 2026-07-28: do rewrite via re-scope; assigned_vm REVERTED planning->NA 2026-07-31 per BLK-29884333 — see Progress Log)
parent_epic: orchestrator_master
assigned_vm: NA # NOT AO-dispatchable: banner-guarded, local-only-homed fleet-core rewrite (BLK-29884333 option A); na-audit 2026-07-30 misclassified NA->planning, reverted 2026-07-31
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
context_scope:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/bootstrap.py,
  ]
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

- [x] ✅ [BACKEND] P2. **Bound the NULL-`brief_hash` tail.** — `agent-orchestrator@aaa2db8`
      (`ao_backlog_regen_integrity_2026_07_20.md` todo 3). Chose **(c) accept permanently** — re-measured first (38 rows
      today, down from 56-58, confirming the bucket shrinks, not grows, under normal operation; 0 in-flight, the
      precondition holds) rather than trusting this doc's own cited number. WHY recorded in `sync_backlog_to_db`'s
      docstring; a `check_null_brief_hash_growth.py` alarm (baseline=38) added + tested + live smoke-tested against the
      real DB via SSM. **Gate met**: decision recorded, growth check exists and fires above baseline. (repo:
      agent-orchestrator)
- [x] ✅ [BACKEND] P3. **Make the sibling-reset case impossible or loud.** — `agent-orchestrator@9c7a0fd`
      (`ao_backlog_regen_integrity_2026_07_20.md` todo 1). `sync_backlog_to_db` now refuses to reset a row that is
      `done` with a `done_sha` on brief_hash mismatch, logging an ERROR (new brief + both hashes — the old plaintext
      isn't stored). **Accepted cost**: this also blocks the legitimate "id reused for a NEW todo" case — such a todo
      will silently read as `done` and never dispatch until manually fixed. That's the deliberate trade-off (protect
      audit history over correct auto-routing); todo below (content-derived ids) is the real fix if this proves
      insufficient. **Gate**: `test_sync_refuses_to_reset_a_done_row_on_id_reuse` (new) + 2 existing tests updated to
      the new contract; bug-injected (guard disabled → both dependent tests red; restored → green).
- [ ] [BACKEND] P2. **RULED 2026-07-28 (operator gated-decision closeout pass, applying the standing theme: "opt for
      full completions, no shortcuts, full functionality... if it's about canonicalisation rather than a hack, do it
      properly") — DO THE CONTENT-HASH REWRITE NOW.** The prior deferral ("re-open only if the two todos above prove
      insufficient") is treated as MET: the 2026-07-25 `sync_backlog_to_db: REFUSING to reset task id` incident and the
      2026-07-27 finding below (a `dispatched` row has NO equivalent guard AT ALL, unlike the `done`-row case) are two
      independent guard classes now proven insufficient, not merely theoretically incomplete. Positional ids are the
      hack the existing guards patch around; content-derived ids are the actual canonical fix. **Retagged from a
      parked/deferred decision to a normal, fully-scoped AO-dispatchable todo — full completion required, no partial
      rollout.** The rewrite must cover the FULL blast radius `ao_dispatch_hardening_2026_07_16` originally flagged, not
      a subset: `existing_ids`/`existing_briefs` bookkeeping in `regen_backlog_from_plan.py`, `slot_skips` keyed by
      `task_id`, every dashboard/API id reference, and a migration path for already-`done` rows' ids so `done_sha` audit
      history survives the scheme change (not a fresh-start-only rewrite that abandons existing history). **Gate**:
      content-derived ids ship across that full surface; the sibling guard todos above (`brief_hash` sibling-reset
      protection, NULL-hash tail handling) either become provably unnecessary or are explicitly kept as defense-in-depth
      (decision recorded either way); and the 2026-07-27 `dispatched`-row gap immediately below is closed by this SAME
      rewrite (removing the underlying position-shift cause fixes both bug classes at once) rather than patched
      separately.
- [ ] [BACKEND] P2. **New gap found 2026-07-27 (via
      `backlog_brief_cross_wired_adjacent_collision_group_todos_2026_07_     27.md`): a `dispatched` row has NO
      equivalent protection to the `done`-row sibling-reset guard, and the in-flight worker is never notified.** This
      doc's existing analysis only covered `done` rows losing audit history; it did not consider a `dispatched` row (an
      ACTIVELY-WORKING agent). `sync_backlog_to_db` (`server/bootstrap.py:354-374`) silently resets ANY non-`done` row's
      `status`→`queued`/`dispatched_to`→`None`/etc on a `brief_hash` mismatch — confirmed already covered by the
      EXISTING `test_sync_resets_terminal_fields_when_id_reused_for_different_checkbox`, which asserts the reset fires
      for `status="dispatched"` exactly like `status="queued"`. Unlike the operator-removed- todo path (`_prune_stale`'s
      dispatched-orphan-cancel logic, which marks the row `cancelled` so the worker's next `/heartbeat` sees
      `cancel_task` and stops per `worker.md`), this id-reuse reset path emits NO signal to the in-flight worker at all
      — it keeps working under its own (originally correct) understanding of the task, and can only discover the
      mismatch reactively at `/done` time when the stored `brief` no longer matches what it did. Live incident:
      `cefi_satellite_ao_dispatch_batch1-012` (slot-5, 2026-07-27) — genuinely correct, shipped work
      (market-tick-data-service@94b4aff5) permanently unable to pass `/done`'s cross-repo verification because the id's
      `brief` had been silently repointed to an adjacent todo mid-flight. Two independent fixes worth considering: (a)
      extend the `done`-row guard's protection to `dispatched` rows too (refuse the silent reset while a worker holds it
      — safer, but the guard already carries an accepted "blocks legitimate new-todo routing" cost, which would now also
      apply here); or (b) on a `dispatched`-row brief-hash mismatch, set `cancel_task` (mirroring the existing
      operator-removal signal) so the in-flight worker gets notified and can revert/stop cleanly instead of shipping
      unmatchable work. Repo: agent-orchestrator. **RULED 2026-07-28**: this is the second guard-class failure cited in
      the content-hash rewrite ruling above — do not patch (a)/(b) as a standalone stopgap; the content-derived id
      rewrite removes the underlying position-shift cause of this bug too, so close this todo as part of that same
      rewrite's gate, not separately. If the rewrite's timeline slips and this incident recurs before it ships, (b) is
      the safer interim patch (notifies the worker; (a) silently blocks legitimate routing same as its `done`-row
      sibling) — but treat that as a stopgap, not a substitute for the full fix.

## Progress Log

- **2026-07-31 (main-agent, BLK-29884333 enforcement)** — **THIRD mis-dispatch; `assigned_vm` REVERTED planning->NA.**
  Re-dispatched to slot 4 at `2026-07-31T01:47:40Z`; the worker got 3+ todos into actually rewriting fleet-core
  `_make_task_id`/`regen_backlog_from_plan.py` before the review agent caught it and halted the slot (slot 11 had
  already `/skip`ped the same task at `2026-07-30T23:53Z` citing option A). Root cause per BLK-29884333 (option A,
  main): the 2026-07-30 na-eligibility-audit flipped `assigned_vm: NA -> planning`, wrongly surfacing a banner-guarded,
  local-only-homed, multi-day live-dispatch-core rewrite as a 1-hour AO-dispatchable todo — NOT AO-eligible (outcome not
  worker-determinable; phased design = human decision). Applying the ruling's prescribed revert now (reversible park,
  deletes nothing) to stop the recurrence. The 2026-07-28 "do the rewrite" ruling STANDS but must be re-homed into
  `ao_open_issues_consolidated_close_out_2026_07_17.md` as properly-phased operator/human-planning todos before any
  dispatch — that re-scope, plus hardening the na-audit against banner-guarded/local-homed docs, remain operator-pending
  (BLK-29884333).
- **2026-07-28 (slot-12)** — **Fresh live recurrence, post-fix, on a `done` row this time (not `dispatched`).**
  `sports_consolidated_native_ao_extract-010` (`plan_ref: sports_consolidated_native_ao_extract_2026_07_25.md`, Track H
  denominator todo) was dispatched to me at `2026-07-28T23:02:42Z`. Its plan checkbox had already been flipped +
  extracted into a machine-gated child plan by slot-15 at `unified-trading-pm@dc44d0c6d` (`2026-07-28T12:38:13Z`, "split
  Track H denominator todo into a machine-gated child plan"), and the backlog row itself already carried
  `done_sha=dc44d0c6d` + `done_at=2026-07-28T12:38:45Z` — i.e. **~10h before** the `dispatched_at` I received. So this
  is a `done` row (with a real `done_sha`, not a NULL-hash legacy row) that got re-dispatched despite the 2026-07-20
  sibling-reset guard (`agent-orchestrator@9c7a0fd`) that's supposed to refuse exactly this reset. Confirmed via fresh
  git log the underlying work genuinely never re-executed (MDPS `reprocess_sports_odds.py` HEAD still `6f7422e`,
  unrelated venue-stamp fix; the footystats migration script was never committed to `market-tick-data-service`) — so
  this isn't a case of legitimately-new content landing on a reused id, it's the same completed todo bouncing back.
  Filed as extra evidence for the already-RULED content-hash-id rewrite above (this is a THIRD independent guard-class
  miss, on the `done`-row path this time, not the `dispatched`-row path the 2026-07-27 finding covered) — not a new fix
  task, since the rewrite already covers this blast radius. Raised `/blocked` on my own dispatched -010 rather than
  silently redoing already-done work; see that question's resolution for how the stale duplicate itself was closed.

- **2026-07-28** — **RULED: do the content-hash rewrite now** (operator gated-decision closeout pass, general theme
  applied — "opt for full completions, no shortcuts, full functionality... if it's about canonicalisation rather than a
  hack, do it properly"). The 2026-06-25/26-era deferral ("wait until a new incident forces it") is treated as MET by
  the 2026-07-25 `sync_backlog_to_db: REFUSING to reset task id` incident plus the 2026-07-27 `dispatched`-row gap
  finding (no guard at all, a strictly worse gap than the already-guarded `done`-row case) — two independent guard
  failures, not one theoretical concern. The P3 "deliberately NOT scoped here" todo is retagged P2 and rewritten as a
  normal, fully-scoped AO-dispatchable todo (full blast-radius mandate: `existing_ids`/`existing_briefs`, `slot_skips`,
  dashboard/API id refs, `done_sha` history migration — no partial rewrite). The 2026-07-27 dispatched-row gap todo is
  folded into the same rewrite's gate rather than patched standalone. Mirrored to
  `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md` and
  `/plans/archive/2026_07/ao_issue_docs_consolidated_remediation_2026_07_23.md`, both of which carried the same
  BLOCKED-OPERATOR-DECISION framing. Plan-only change, no code shipped.
- **2026-07-20** — NULL-`brief_hash` tail todo landed, decision (c) accept-permanently (`agent-orchestrator@aaa2db8`,
  via `ao_backlog_regen_integrity_2026_07_20.md` todo 3). Re-measured count is 38 (down from 56-58), confirming the
  bucket shrinks under normal operation. Growth alarm + docstring WHY + tests. See the fix-todo checkbox above.
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
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **na-eligibility-audit 2026-07-31**: KEEP-NA, valid — **DO NOT RECLASSIFY THIS DOC.** Confirmed the 2026-07-31
  BLK-29884333 entry above: the 2026-07-30 na-eligibility-audit RECLASSIFY verdict directly above was itself a
  misclassification, caused a THIRD mis-dispatch of a banner-guarded, local-only-homed, multi-day live-dispatch-core
  rewrite before the operator/main-agent caught and reverted it. This doc carries a top-of-body "🟢 EXECUTION
  CONSOLIDATED" banner explicitly reading "Do NOT start work from this doc alone" (work routes through
  `ao_open_issues_consolidated_close_out_2026_07_17.md` instead) and an `assigned_vm: NA` inline frontmatter comment
  stating "NOT AO-dispatchable" — both citations verified real by reading them directly, per the skill's own
  never-re-litigate rule. Leaving `assigned_vm: NA` untouched. Closed the operator-pending "hardening the na-audit
  against banner-guarded/local-homed docs" half of BLK-29884333 directly: strengthened
  `/cursor-configs/skills/na-eligibility-audit/SKILL.md`'s "Never re-litigate an established ruling" paragraph to
  explicitly name a redirect-to-another-doc banner and an inline `assigned_vm: NA #`-comment citing a prior
  RECLASSIFY-then-revert as hard KEEP-NA triggers (same commit as this marker), so a future run's Phase 1 does not need
  to rediscover this citation by luck.

- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 4 entries resolve on disk (the
  consolidated-execution plan + archived hardening batch + the two source files the mechanism section cites file:line
  against) — no changes.
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — **DO NOT RECLASSIFY THIS DOC**,
  re-affirmed on citation alone per the skill's own hardened rule (the rule this exact incident wrote in). Both
  citations verified real by reading them directly: the top-of-body "🟢 EXECUTION CONSOLIDATED" banner still reads "Do
  NOT start work from this doc alone" and still redirects to
  `/plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md` (confirmed still `assigned_vm: NA`,
  active, present); the inline `assigned_vm: NA #`-comment still states "NOT AO-dispatchable" citing the 2026-07-31
  RECLASSIFY-then-revert (BLK-29884333). No content drift since the 2026-08-03 marker (only incidental context-scout
  touches). Not re-deriving the underlying judgment.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **2026-08-09 (slot-30)** — **FOURTH occurrence, new symptom flavor: two DIFFERENT task_ids concurrently dispatched for
  the SAME todo, not a sibling-id reset after the fact.** Dispatched
  `prediction_betfair_lay_price_adapter_scaffold_deleted-caad88819ca3` (todo 2 of
  `plans/active/issues/prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md`) at ~14:xx UTC; slot-5 was
  independently dispatched the SAME todo's content under its own task_id at the same time (`14:45:17Z` per its commit
  `market-tick-data-service@1200d443`). Both fully implemented + QG-passed the identical `download_batch`/
  `VENUE_REGISTRY` feature; my quickmerge push hit a real rebase conflict against slot-5's already-merged version
  (auto-rebase `CONFLICT (content)` on all 3 touched files). Recovered cleanly — `git rebase --abort`, verified slot-5's
  version satisfied the done_definition, discarded my redundant local commit via `git reset --keep origin/...` (working
  tree was clean, no data lost, original commit `7fd423579a` recoverable via reflog), called `/done` anyway citing
  slot-5's SHA. Server confirmed:
  `"dispatch_reason":"orphan task closed — no backlog.yaml definition found for this task_id"` — my task_id had already
  fallen out of backlog.yaml by the time I finished (~30min of wall-clock work, ~9 QG retries) purely because of the
  race window, not because of anything wrong in my execution. This is the same "external race reads a flipped checkbox
  as unflipped" precondition this doc already names (§ The mechanism) — consistent with regen running against a stale
  plan-clone read of todo 2 as still `- [ ]` while slot-5's flip was in flight, minting a second live `queued` row under
  a fresh id for the same brief instead of guard 1 (same-plan brief-keyed reconcile) catching it. No code fix attempted
  here (this doc's rewrite todo is `assigned_vm: NA`, banner-guarded, operator/local-only-homed) — logging as further
  evidence the standing P2 content-hash-id rewrite is still needed; cost this time was one full worker-session's wasted
  compute, not corrupted audit history.

- **na-eligibility-audit 2026-08-09 (round11)**: **DO NOT RECLASSIFY THIS DOC** — re-affirmed on citation alone, per the
  skill's own hardened rule this exact doc's incident history wrote. Both hard triggers verified real by reading them
  directly: the top-of-body "🟢 EXECUTION CONSOLIDATED" banner still reads "Do NOT start work from this doc alone"; the
  inline `assigned_vm: NA #`-comment still states "NOT AO-dispatchable," citing the 2026-07-31 RECLASSIFY-then-revert
  (BLK-29884333). Checked every round7-10 precedent (IAM self-service, D16, S5.1,
  plan-destination-defaults-AO-dispatched, escalation-N, reversibility-qualified deletes, Option B retirement,
  DeepSeek/Slack credentials) against this doc specifically — NONE of them touch the actual reason this doc is
  hard-KEEP-NA (a documented, THIRD-repeat, real production mis-dispatch of live-dispatch-core rewrite work), so none
  provide grounds to override the standing ruling. The 2026-08-09 (slot-30) recurrence entry directly above is a FOURTH
  live occurrence of the underlying bug (new flavor: concurrent double-dispatch of the same todo, not a post-hoc
  sibling-id reset) — further evidence the rewrite is still needed, not evidence the doc is now AO-dispatchable. No
  per-item extraction either: all 2 open `[BACKEND] P2` todos are explicitly one indivisible, full-blast-radius rewrite
  by the 2026-07-28 operator ruling ("full completion required, no partial rollout").
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: **DO NOT RECLASSIFY THIS DOC** — per this
  sweep's own explicit instruction not to re-litigate this exact doc (documented history of 3-4 real mis-dispatch
  incidents from prior wrongful reclassification). Both hard triggers re-verified present by direct read: the
  top-of-body "🟢 EXECUTION CONSOLIDATED" banner still reads "Do NOT start work from this doc alone"; the inline
  `assigned_vm: NA #` comment still states "NOT AO-dispatchable," citing BLK-29884333. Content unchanged since round11.
  KEEP-NA, valid.
