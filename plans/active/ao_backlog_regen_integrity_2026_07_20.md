---
doc_type: plan
title: AO backlog/regen integrity — stop silent data loss in the task table
summary:
  Four regen/bootstrap defects that silently destroy or misreport task state — a done row recyclable by a sibling reset,
  hand-tuned parking dropped on every id shift, an unbounded NULL brief_hash tail, and an audit that false-positives on
  honest work. Fix them, close the two live false-done rows, and record the two rulings already made. The
  preserve-by-brief fix is a prerequisite for durable auto-park.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, regen, backlog, data-integrity, audit]
related: [ao_open_issues_consolidated_close_out_2026_07_17.md, ao_dispatch_cooldown_and_park_2026_07_20.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.0
assigned_role: backend_engineer
model_tier: sonnet-doable # single-repo, defects already localised to named functions
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# AO backlog/regen integrity

> **Provenance**: Phases 0-1 of `ao_open_issues_consolidated_close_out_2026_07_17.md` (docs #4, #5, #6, #8). That plan
> keeps the audit record; this plan holds the work. **Do not action those entries there.**

## Why these four belong together

They are one theme: **the task table silently losing or misreporting truth.** A `done` row can be recycled by a sibling
reset; a hand-tuned park evaporates when task ids renumber; a NULL `brief_hash` tail makes rows unauditable; and the
audit that is supposed to catch all of this false-positives on honest work, which erodes trust in the one signal we
have. Fixing them piecemeal across different agents would mean four people learning the same regen model.

**Todo 3 is a keystone**: `ao_dispatch_cooldown_and_park_2026_07_20.md`'s durable auto-park is NOT durable until
preservation is keyed by `brief` instead of task id. Land it early and tell that plan's owner.

## Execution environment — LOCAL

Operator-assigned agents on this host, not AO dispatch (`assigned_vm: NA`, `execution_scope: local-only`). Tick
checkboxes by hand. All todos are local code + tests in `agent-orchestrator` (plus one PM doc flip), verified with
`bash scripts/quality-gates.sh`. Todo 1 needs a read-only live-DB check via SSM (pattern:
`scripts/orchestrator/check-ao-backlog-status.sh`; use `sudo python3` +
`sqlite3.connect("file:/var/lib/orchestrator/state.db?mode=ro", uri=True)` — no `sqlite3` CLI on the VM, and a probe run
as `ubuntu` does not inherit the unit's `Environment=`). **Never write to the live DB.**

## Todos

- [x] ✅ [BACKEND] P1. **Sibling-reset guard: never silently recycle a `done` row.** — `agent-orchestrator@9c7a0fd`
      (LDR). `bootstrap.py`'s `sync_backlog_to_db` brief_hash-mismatch branch now checks
      `existing_row.status == "done" and existing_row.done_sha is not None` FIRST — if true, REFUSES the reset, logs an
      ERROR naming the new incoming brief + both hashes (the old brief's plaintext isn't stored, only its hash —
      `brief_hash` predates this fix), and leaves every terminal field untouched. **Trade-off surfaced, not hidden**:
      this also refuses the LEGITIMATE "id reused for a genuinely new todo" case the 2026-07-15 fix was built for — the
      guard cannot distinguish that from "a stale reader shifted an old todo onto this id" from `brief_hash` alone, so a
      new todo landing on a stale done+done_sha id will now silently read as `done` and never dispatch until manually
      fixed. This is the plan's own explicit ruling (protect audit history over correct routing); proper disambiguation
      is content-derived ids, deliberately out of scope per `regen_positional_task_ids_not_content_stable_2026_07_17.md`
      todo 3. **Gate**: added `test_sync_refuses_to_reset_a_done_row_on_id_reuse` (row survives + ERROR logged, asserts
      new brief + both hashes appear in the message) and updated the two existing tests whose scenarios this ruling
      inverts (`test_sync_resets_terminal_fields_when_id_reused_for_different_checkbox` narrowed to a non-done row — the
      case where reset still applies; `test_regen_id_slot_reuse_inherits_stale_terminal_status`'s tick-3 assertion
      flipped from "resets to queued" to "done row survives + ERROR logged", with an inline comment explaining why).
      **Bug- injected**: short-circuited the guard condition, confirmed both dependent tests go RED (2 failed),
      restored, confirmed GREEN (1428 passed). Source: doc #6 todo 2.
- [x] ✅ [BACKEND] P1. **Hand-tuned-field preservation across positional-ID shift — KEYSTONE, land this first.** —
      `agent-orchestrator@a650ee4` (LDR). **Finding: no production code change was needed — re-verify before assuming
      the "keyed by task id" framing.** Grepped every `priority_override` read/write site fleet-wide
      (`server/     regen_backlog_from_plan.py` only, 2 sites): `_reconcile_task_fields` reads-but-never-writes it
      (guards against reverting a hand-set priority); `_migrate_parking_state` (`agent-orchestrator@22738f6`,
      2026-07-18) already keys by brief-similarity for its own separate bug (a REWORDED brief/orphan case). No id-keyed
      preservation code exists anywhere to change. The main regen loop's brief-match (`plan_tasks_by_brief`, RC-1,
      `agent-orchestrator@ff6100a`, **2026-07-07 — predates the incident**) mutates the SAME task object in place on a
      same-brief todo, so `priority`/`priority_override`/`prereqs.prerequisites` survive by construction regardless of
      sibling completion — there is no id shift for a still-open, unreworded todo (`_make_task_id`'s counter only fires
      for a brief with NO current match). **Gate 1 (regression test)**: added
      `test_regen_park_survives_sibling_completion_and_id_shift` — parks the middle of 3 todos, removes the last
      (mirrors mvp-defi's `-003`→gone), regen with `prune_stale=True` (production's default) twice — park survives
      unchanged both ticks. **PASSES on current code, no fix required.** **Gate 2 (live park survives)**: verified
      2026-07-20 via read-only SSM (`i-0c9b283b31d6b5ca7`) directly against the live `backlog.yaml` —
      `mvp_backfill_defi_onchain_v10-001` still carries `priority: 999` +
      `prereqs.prerequisites: [defi_onchain_v10_universe_v2_seed_or_backfill_progressed]`, unchanged since the
      2026-07-17 re-application — **3 days / ~140 `PlanRegenLoop` ticks (30-min cadence) with zero reversion.**
      **Corrected root cause**: the 07-17 loss is better attributed to
      `ao_service_clone_frozen_by_untracked_checkpoint_     2026_07_16` (a stale-clone race reading `[x]` as `[ ]`,
      causing a false-orphan prune-then-recreate with no memory) than to a genuine positional-id mechanism — that class
      is doc #6's territory (this plan's todo 1), and its "recreated fresh, zero memory" residual is doc #6's own todo
      3, **deliberately out of scope** ("re-open ONLY if the two todos above prove insufficient"). **Notified**: added a
      note to `ao_dispatch_cooldown_and_park_2026_07_20.md`'s Progress Log — their auto-park dependency is UNBLOCKED
      (verified, not just assumed). Source: doc #5 fix-todo 3.
- [ ] [BACKEND] P2. **Bound the NULL-`brief_hash` tail — RULED 2026-07-20: accept permanently + a growth alarm.** 54
      rows, all `done`, 0 in-flight (re-measured this session). The ruling (operator A1): do NOT backfill — it is write
      risk against audit history for no gain — and do NOT blanket-reset. Instead document the WHY in the docstring and
      add a **growth alarm**, because growth is the real signal: a rising count means the backfill path regressed.
      **Gate**: the exemption is documented with its reason, and a growth check exists that fires if the count rises
      above today's 54. Source: doc #6 todo 1.
- [ ] [BACKEND] P2. **`audit_false_done` contract — RULED 2026-07-20: checkbox state = truth.** The audit currently
      flags a row whose plan checkbox IS `[x]` purely because the cited `done_sha` is not the commit that flipped it
      (that is exactly `sports_cf8…-002`). The ruling (operator A2): the gate answers "is the work done", and the
      checkbox is the SSOT; keep `done_sha` as provenance, but a sha mismatch must NOT manufacture a false positive — a
      polluted gate signal is worse than a missing one. Trace BOTH consumers (`audit_false_done` and
      `verify.check_plan_flip`) and make them agree on the rule. **Gate**: an already-`[x]` row with a mismatched sha is
      no longer flagged; the rule is documented where both consumers can find it. Source: sports_cf8 study.
- [ ] [BACKEND] P0. **Clear the 2 live false-`done` rows — AO's part is notify + re-verify, NOT the fix.**
      `sports_cf8_available_at_backfill_regression-001` (`done_sha=utl@f5f15e3a`) and `-002` (`utl@0f55cc2b`). **The
      underlying work is NOT AO's** (operator 2026-07-18): it belongs to
      `sports_cf8_available_at_backfill_regression_2026_07_13.md` (epic `mtds_mdps_master`, role `data_engineering`).
      `-001` (`:348`) is a `[ ]`-open DATA re-emit task whose backlog row says `done`; `-002` (`:856`) is genuinely
      `[x]` and should stop being flagged once todo 4 lands. AO scope: notify that plan's owner to verify + flip (or
      reopen), then RE-RUN the audit. **Gate**: `audit_false_done.py --db … --pm …` reports `false_done: 0` after the
      owner's ruling; the per-row decision is recorded on `backlog_task_done_status_diverges…`. **Do NOT flip a sports
      checkbox yourself** — that is the false-done pattern this plan exists to stop.
- [ ] [DOC] P2. **Record that the tasks table is a projection, not a completion ledger.** In the regen docs
      (`server/regen_backlog_from_plan.py` module docstring + the operator-facing regen doc), state: the table holds
      currently-OPEN DISPATCHABLE todos plus dispatched history. `BLOCKED-*` todos are deliberately never ingested
      (`_parse_open_todos` skips them alongside `[x]`), and a todo checked off outside the dispatch loop has its
      still-queued row garbage-collected by `_prune_stale` (done/dispatched rows are never touched). **A missing row is
      therefore never by itself evidence of a lost task.** Provenance: the B1 audit, where this question decayed twice
      because each re-measurement read normal projection churn as instability. **Gate**: the docs say it plainly.
- [ ] [REVIEW] P1. **Close doc #4 (`backlog_task_done_status_diverges…`) for real.** It left `status: open` awaiting "an
      independent skeptical audit"; that audit happened and found the two rows above, so the doc closes only AFTER todo
      5 lands. Record the corollary: the "no periodic sweep needed" ruling holds for the gated mechanism, but the
      UNAUDITABLE→auditable transition (regen backfilling `brief_hash` onto a legacy row) can surface old poison at any
      time — so `audit_false_done.py` runs once per close-out session, **not** on a cron. **Gate**: doc flipped
      `resolved`, `resolved_by` filled, archived per the 5-step ritual.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Every fix here guards audit history. If a test forces you to weaken a guard to pass, the test is wrong — stop and
  say so rather than loosening the guard.**

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — regen/backlog derivation model.
- `codex/11-project-management/` — plan/todo format the regen parses; the checkbox-is-SSOT position behind todo 4.

## Progress Log

- **2026-07-20 — Todo 1 (sibling-reset guard) landed** (`agent-orchestrator@9c7a0fd`). Refuses to reset a
  `done`+`done_sha` row on brief_hash mismatch; ERROR logged; regression test + bug-injection both confirmed
  load-bearing. **Flagging a real trade-off, not just a fix**: this guard also blocks the legitimate "id reused for a
  genuinely new todo" case — such a todo will now silently look `done` and never dispatch until someone notices and
  manually intervenes. That cost is the plan's own explicit ruling (protect audit history over correct auto-routing);
  the proper fix is content-derived ids, deliberately out of scope. Worth watching for in practice.
- **2026-07-20 — Todo 2 (KEYSTONE) landed** (`agent-orchestrator@a650ee4`). No production code change needed — the RC-1
  brief-keyed reconcile (`agent-orchestrator@ff6100a`, 2026-07-07) already predates and prevents the reported mechanism.
  Regression test added + live park (`mvp_backfill_defi_onchain_v10-001`) re-verified holding 3 days / ~140 ticks after
  its 2026-07-17 re-application via read-only SSM. Full detail on the todo itself. Notified
  `ao_dispatch_cooldown_and_park_2026_07_20.md`'s owner via a note on its Progress Log — their auto-park dependency is
  UNBLOCKED.
- **2026-07-20 — plan created** from Phases 0-1 of the consolidated close-out. Two todos ship with rulings already made
  (A1 accept-the-tail, A2 checkbox-is-truth), so they are implementation, not open questions.
