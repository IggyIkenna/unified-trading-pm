---
doc_type: plan
title: AO backlog/regen integrity — stop silent data loss in the task table
summary:
  Four regen/bootstrap defects that silently destroy or misreport task state — a done row recyclable by a sibling reset,
  hand-tuned parking dropped on every id shift, an unbounded NULL brief_hash tail, and an audit that false-positives on
  honest work. Fix them, close the two live false-done rows, and record the two rulings already made. The
  preserve-by-brief fix is a prerequisite for durable auto-park.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, regen, backlog, data-integrity, audit]
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_dispatch_cooldown_and_park_2026_07_20.md,
  ]
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

> **🟢 COMPLETE 2026-07-20** — all 7 todos landed. Keystone (todo 2) and NULL-brief_hash-tail (todo 6) needed no new
> code (already covered by prior/sibling work, re-verified rather than re-done); todo 5 found both named false-done rows
> had already self-resolved. Doc #4 closed + archived as this plan's own last todo. See the Progress Log for the full
> account of each todo.

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
- [x] ✅ [BACKEND] P2. **Bound the NULL-`brief_hash` tail — RULED 2026-07-20: accept permanently + a growth alarm.** —
      `agent-orchestrator@aaa2db8` (LDR). **Re-measured before implementing** (per this doc's own "re-measure, never
      cite a fixed number" warning): 38 rows today, not 54 — down from 56-58 across 07-16/17 and 54 at this plan's own
      authoring earlier today, confirming the bucket SHRINKS under normal operation (legacy rows pruned), it does not
      grow. All 38 `done`, 0 in-flight — the ruling's precondition still holds. Documented the WHY directly in
      `sync_backlog_to_db`'s docstring (`server/bootstrap.py`): unrecoverable plaintext (cites the full source search
      from `backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`'s final todo), why backfill-from-diff
      was rejected (ambiguous which removed line belongs to which row without the lost brief text — a wrong heuristic
      match would manufacture false confidence), and the two self-healing paths whose regression the alarm actually
      watches for. **Gate**: added `scripts/orchestrator/check_null_brief_hash_growth.py` (mirrors
      `audit_false_done.py`'s conventions — `--db`/`--json`, exit 1 on alarm) with baseline=38 recorded at today's
      measurement; 6 unit tests (at/below/above baseline, non-done NULL rows excluded from the growth count but reported
      separately, hashed rows excluded, JSON output shape) plus a live smoke-test via read-only SSM against the real
      orchestrator DB — reports `OK: at or below baseline` (38 ≤ 38) today. Source: doc #6 todo 1.
- [x] ✅ [BACKEND] P2. **`audit_false_done` contract — RULED 2026-07-20: checkbox state = truth.** —
      `agent-orchestrator@64ecd57` (LDR). **Traced both consumers first**: `audit_false_done.py` was ALREADY
      checkbox-authoritative — its `_still_unchecked` never reads `done_sha`, only whether a `- [ ]` line still hashes
      to the stored `brief_hash`. The actual offender is `verify.check_plan_flip` (consumed only by
      `server/routes/slots_worker.py`'s `/done` handler, both the hard-409 and the warn-path escalation, from the SAME
      computed `plan_flip` dict) — it hard- rejected purely on whether the CITED sha's diff flipped the checkbox, with
      no fallback to the checkbox's CURRENT state. Added `_brief_is_currently_checked` + wired it into both single-repo
      and cross-repo modes of `check_plan_flip`: when the sha/diff proof fails, read the live plan text — if the brief
      is genuinely `- [x]` today, treat it as flipped (`reason="checkbox_currently_checked_sha_mismatch"`) instead of
      rejecting. Both `slots_worker.py` call sites needed zero changes (they already read the shared dict generically).
      **Gate**: 2 new tests (single-repo: an earlier commit flips it, a later unrelated sha is cited; cross-repo: the
      flip commit is outside `_pm_log_commits_touching_plan_ref`'s lookback window) both accept where the old code would
      409; bug-injected (`_brief_is_currently_checked` forced `False`) confirmed both go red, restored green. **Live
      audit_false_done.py is currently BROKEN on the VM** (separate finding, not fixed here — flagging for the
      operator): running it via SSM hits `fatal: detected dubious ownership in repository` on the PM worktree, so EVERY
      `git show <ref>:<path>` call fails silently → every done row lands in `unresolved`, and `honest`/ `false_done` are
      ALWAYS empty regardless of truth (verified: a live run returned `false_done: [], honest: []` while 44 done rows
      exist). This needs
      `git config --global --add safe.directory     /home/ubuntu/unified-trading-system-repos/unified-trading-pm` on the
      VM — a client-side git trust setting, not a code/data change, but still a VM-side write, so left for the operator
      to authorize/run rather than done unilaterally here. **Corrects the sports_cf8-002 premise this todo cited**:
      direct DB inspection (read-only SSM) shows `-002` no longer exists as a task row at all (its id has since been
      recycled at least once more since the 07-17 audit; see todo 5 for the full timeline) — the specific row this todo
      names is stale, but the FIX (and its tests) covers the general contract regardless. Source: sports_cf8 study.
- [x] ✅ [BACKEND] P0. **Clear the 2 live false-`done` rows — AO's part is notify + re-verify, NOT the fix.** —
      **finding: both rows already self-resolved before any notify action was needed.** Re-verified CURRENT state via
      read-only SSM against the live `state.db` before acting (per this todo's own "re-verify" instruction — the 07-17
      snapshot is 3 days stale): `-001` is now `status: queued` (not `done`) — matches its genuinely still-open `[ ]`
      checkbox; something already corrected it between 07-17 and today (predates this session's sibling-reset guard).
      `-002` no longer exists as a task row — its id was reassigned to a later todo that legitimately completed
      2026-07-18 (`sha=22738f6`, gate-verified), which has SINCE also vanished (the id was reused again under the
      pre-fix behavior). **Neither named row exists to reopen or flip today** — did NOT flip a sports checkbox, per this
      todo's own hard constraint. **Broader gate check**: `audit_false_done.py` is currently non-functional on the live
      VM (git "dubious ownership" blocks every `git show` read — separate finding, flagged on todo 4, not fixed here).
      Replicated its exact logic locally against a working PM clone + the live DB's raw rows instead: of 44 `done` rows,
      38 are the already-ruled-permanently-unauditable NULL-`brief_hash` tail, and all 6 auditable rows are honest —
      **false_done: 0**. **Gate met**. Per-row decision + full investigation recorded on
      `backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`'s Progress Log.
- [x] ✅ [DOC] P2. **Record that the tasks table is a projection, not a completion ledger.** — **already landed by a
      sibling plan before this todo was reached; verified complete, not re-done.** Both required locations already carry
      this exact content (same B1-audit provenance, same wording — `ao_scheduled_agent_hygiene_2026_07_20.md`'s own todo
      6, same underlying finding, split from the same 2026-07-17 consolidated close-out): (1)
      `server/regen_backlog_from_plan.py`'s module docstring — `agent-orchestrator@fd09764`; (2) the operator-facing
      codex doc, `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md` § "The tasks table is a
      projection, not a completion ledger" — `unified-trading-pm@b5e184357`. Read both in full: content matches this
      todo's ask verbatim (BLOCKED-\* never ingested, prune_stale GC of orphans, done/dispatched rows never touched, "a
      missing row is never by itself evidence"). **Gate met** — no new commit needed under this plan; flagging the
      cross-plan duplication here so a future reader doesn't wonder why this todo has no code of its own.
- [x] ✅ [REVIEW] P1. **Close doc #4 (`backlog_task_done_status_diverges…`) for real.** — this commit. **Codex-alignment
      check first** (per the archival ritual): found TWO stale contracts and fixed both before closing —
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` still described the pre-todo-4
      file-touch-vs-checkbox-diff gate only (no mention of the checkbox-currently- checked fallback) and still called
      the sibling-reset guard's positional-id gap "not eliminated" citing the now-narrowed issue doc; both updated to
      the current, shipped contracts. **Recorded the corollary this todo asks for**: added a new § "Auditing
      `status=done` honesty — `audit_false_done.py` cadence" to
      `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md` — the gated mechanism needs no periodic
      sweep, but the UNAUDITABLE→auditable transition can surface old poison at any time, so the tool runs once per
      close-out session, not on a cron. **Resolved doc #4**: `status: resolved`, `resolved_by` filled (cites this plan's
      todo 5 investigation), `last_updated` bumped, a `🟢 RESOLVED` banner added, moved `plans/active/issues/` →
      `plans/archive/issues/` via `git mv`. **Gate met**: doc flipped `resolved`, `resolved_by` filled, archived, codex
      alignment checked and 2 stale sections fixed.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Every fix here guards audit history. If a test forces you to weaken a guard to pass, the test is wrong — stop and
  say so rather than loosening the guard.**

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — regen/backlog derivation model.
- `codex/11-project-management/` — plan/todo format the regen parses; the checkbox-is-SSOT position behind todo 4.

## Progress Log

- **2026-07-20 (post-archival follow-up) — the operator-authorized VM fix from todo 4's entry is now DONE.** Todo 4's
  entry below flagged `audit_false_done.py` as non-functional on the live VM (git "dubious ownership" on the PM sibling
  clone, breaking every `git show` read) and deliberately left the fix for the operator since it's a VM-side write.
  Operator authorized it; applied
  `git config --global --add safe.directory /home/ubuntu/unified-trading-system-repos/unified-trading-pm` for **root**
  specifically (SSM Run Command executes as root on this VM; `ubuntu` owns the clones and never hit the bug). Verified
  by re-running the actual script live: now correctly reports `false_done: []`, `unresolved: []`, `honest`/`unauditable`
  populated — matching this plan's own manual-replication finding. **Root cause of the drift, for whoever looks next**:
  `scripts/bootstrap_vm.sh` has configured this exact safe.directory entry for root since 2026-05-21 — this VM's root
  gitconfig had simply lost that entry at some point after initial provisioning (cause unknown; a sibling entry for
  `agent-orchestrator` was still present). No code change needed — bootstrap already does the right thing for any
  future/re-provisioned VM. One residual, non-blocking note: root has no GitHub SSH key, so the script's own `git fetch`
  step fails ("Host key verification failed") when run as root via SSM — it still works correctly off the already-synced
  ref from the regular `ubuntu`-owned fetch cron, but a future reader re-running this via SSM should expect that stderr
  line and not mistake it for the fix having failed.
- **2026-07-20 — Todo 7 (close doc #4) landed — all 7 todos complete, plan archived.** Codex-alignment check found +
  fixed 2 stale contracts (`agent-orchestrator-single-vm-architecture.md`'s done-gate section and its sibling-reset
  "known sharp edge" bullet); recorded the audit-cadence corollary as a new section in
  `agent-orchestrator-backlog-state-alignment.md`. Doc #4 resolved (`resolved_by` filled, banner added, moved to
  `plans/archive/issues/`). Since every todo here is now `[x]` with no deferred items, archiving this plan too
  (`status: complete`, moved to `plans/archive/2026_07/`) rather than leaving it sitting in `active/` — the
  codex-alignment step above already covers this plan's own archival ritual.
- **2026-07-20 — Todo 3 (NULL brief_hash tail) landed** (`agent-orchestrator@aaa2db8`). Decision (c) accept permanently.
  Re-measured count is 38, not the plan's own cited 54 (bucket shrinks over time, as expected) — 0 in-flight, ruling's
  precondition holds. WHY documented in `sync_backlog_to_db`'s docstring; growth-alarm script added (baseline=38) with
  unit tests + a live smoke-test against the real VM via SSM (`OK: 38 ≤ 38` today).
- **2026-07-20 — Todo 6 (projection-not-ledger doc) found already done by a sibling plan.**
  `ao_scheduled_agent_hygiene_2026_07_20.md` todo 6 shipped the identical content (same B1-audit provenance) to both
  required locations before this todo was reached — verified both read exactly what this todo asked for, no new commit
  needed. Recorded for traceability.
- **2026-07-20 — Todo 5 (clear the 2 live false-done rows) landed — finding: no reopen needed, both already
  self-resolved.** `-001` now `queued` (matches its open checkbox); `-002` no longer exists (id recycled at least twice
  since 07-17). Re-verified `false_done: 0` fleet-wide by replicating `audit_false_done.py`'s logic locally (the live
  VM's copy is currently broken — see todo 4's entry). No sports checkbox flipped. Full writeup on
  `backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`'s Progress Log — unblocks todo 7.
- **2026-07-20 — Todo 4 (checkbox state = truth) landed** (`agent-orchestrator@64ecd57`). `audit_false_done.py` was
  already checkbox-authoritative; the real fix is in `verify.check_plan_flip` (consumed by `/done`'s hard-409 and
  warn-escalation paths). Both new tests + bug-injection confirmed load-bearing. **Two findings surfacing beyond the
  code fix**: (1) `audit_false_done.py` is currently non-functional on the live VM — a git "dubious ownership" error on
  the PM worktree silently breaks every `git show` read, so `honest`/`false_done` are ALWAYS empty regardless of truth
  (needs an operator-authorized `git config --global --add safe.directory` on the VM — a client-side git-trust write,
  not touched here). (2) The sports_cf8-002 row this todo names no longer exists in the live DB at all — see todo 5 for
  the full investigation.
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
