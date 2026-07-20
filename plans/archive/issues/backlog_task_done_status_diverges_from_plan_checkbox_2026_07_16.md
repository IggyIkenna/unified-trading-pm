---
doc_type: issue
title: >-
  agent-orchestrator backlog marks tasks `status=done` with a `done_sha` that traces to a "declining/no-action" commit,
  while the source plan's checkbox stays `[ ]` — now actively feeding `gate_on_depends`, which trusts backlog `done`
  over the plan
summary: >
  While working `sports_travel_calculator_tz_aware_kickoff_crash-001` (Todo 2, gated via `depends_on` +
  `gate_on_depends=true` on `sports_p2_features_history_to_ml_ready_2026_06_27.md`), found the live orchestrator
  (restarted `2026-07-16T18:21:11Z`, confirming `agent-orchestrator@2d6365f`'s `.md`-suffix fix is now finally in
  effect) dispatched my task with `dispatch_reason="... prereqs met ..."`. Its `prereqs.completed_tasks`
  (`sports_p2_features_history_to_ml_ready-001`, `-002`) both read `status=done` via `GET /api/backlog` — with
  `done_sha=094756d64` and `done_sha=0402f7a86` respectively. Both SHAs resolve to real commits on `unified-trading-pm`,
  but neither is a completion commit for the task it's cited on: `094756d64` = "sports P2c Todo 1 re-verify — both
  tracked VMs healthy and progressing ... no new action needed (slot-11)"; `0402f7a86` = "sports P2c Todo 3 re-verify —
  still BLOCKED-PREREQ ... (slot-8)". Both are routine "declining, no code touched, checkbox NOT flipped"
  `/skip-current-task` Progress Log commits — the exact opposite of a completion. Confirmed against the actual plan:
  after a clean fresh-pull to LDR HEAD `9d39ed2835ae` (2026-07-16T18:21:16Z),
  `sports_p2_features_history_to_ml_ready_2026_06_27.md` line 101 ("Compute features 2015→present", the task -001 maps
  to) and line 109 ("Features manifest clean over history", the task -002 maps to) are BOTH still `- [ ]` — unflipped.
  This exact plan has an unusually long, well-documented Progress Log (36 consecutive dispatches of the gated child
  task, every single one independently re-verifying Todo 1 as `[ ]` via direct grep) — so this is not a one-off misread,
  it's a confirmed, sustained ground truth that contradicts the backlog's `status=done`.


  **REOPENED / ROOT CAUSE FOUND 2026-07-17 — the shipped fix does not close this, and the bug is LIVE RIGHT NOW.** An
  independent skeptical audit (run before flipping this doc to `resolved`) found the fix guards the wrong thing.
  `/done`'s `no_plan_flip` check WAS correctly upgraded from warning to a hard-409 (`slots_worker.py:709`, gated by
  `done_require_plan_flip`, default True) and the `/reopen` correction path DOES exist (`routes/backlog.py:294`) — both
  as claimed. **But the detector underneath them is insufficient and was never touched.** `check_plan_flip`
  (`server/verify.py:507`) answers only _"did the verified commit touch the plan-of-record FILE?"_ — its own docstring
  says exactly that, and the test is a filename match against the commit's file list. It NEVER diffs whether the
  specific todo's checkbox went `[ ]`->`[x]`. So a `docs(plans): ... re-verified, declining` commit — which appends a
  Progress Log paragraph to the plan file and deliberately leaves the checkbox unflipped — SATISFIES the gate. That is
  precisely the `/skip-current-task` pattern this whole doc is about: the fix hard-blocks everything EXCEPT the one case
  it was built for. **Live reproduction, post-fix**: `l2_book_microstructure_capture-005` and `-007` — two of the exact
  7 tasks this doc's own Todo 3 audit reopened at ~19:41Z — were back at `status=done` within the same session, citing
  `done_sha=6edc8325` (19:54Z) and `1e1c2bda8` (19:59Z). Both post-date ALL four fix commits (@87d6fde 19:08, @666c860
  19:22, @164378c 19:36, @7053dcf 19:53). Both are doc-only commits (33 insertions, plan file ONLY, zero code) whose own
  messages read "**Checkbox NOT flipped** (still correct)" — and both target checkboxes are STILL `- [ ]` at current LDR
  HEAD (`l2_book_microstructure_capture_2026_07_13.md:173,213`, re-verified by hand 2026-07-17). **Therefore**: Todo 3's
  audit was a one-time snapshot that cannot prevent recurrence — and demonstrably did not; the real fix is to make
  `check_plan_flip` diff the todo's checkbox state across the commit (or match the flip line), not merely detect that
  the file was touched. No todo in this doc addresses that gap; it was unrecognised until now.
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [orchestrator, backlog, regen_backlog_from_plan, gate_on_depends, data-integrity, ssot-contradiction, plan-checkbox]
related:
  [
    plans/active/issues/sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md,
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    codex/11-project-management/,
  ]
created: 2026-07-16
parent_epic: agent_operating_framework_master
priority: P1
source:
  sports_travel_calculator_tz_aware_kickoff_crash-001 dispatch, slot 13, 2026-07-16 (Todo 2 re-check, 36th consecutive
  dispatch)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-07-20
locked_by:
resolved_by:
  ao_backlog_regen_integrity_2026_07_20.md todo 7 (backend_engineer) — closed after the independent skeptical audit
  this doc's own precedent required: the 2 poisoned rows (`sports_cf8_available_at_backfill_regression-001`/`-002`)
  the 2026-07-17 audit found no longer exist as live false-`done` rows (re-verified via SSM, both already
  self-resolved by prior mechanisms); `audit_false_done.py`'s equivalent logic re-run confirms `false_done: 0`
  fleet-wide (38 unauditable + 6 honest, 0 unresolved). See that plan's todo 5 for the full investigation.
depends_on: []
---

> **🟢 RESOLVED 2026-07-20** — closed via `ao_backlog_regen_integrity_2026_07_20.md` todo 7, the independent skeptical
> audit this doc's own last entry required before self-declaring done. All todos were already `[x]`; the remaining gate
> was the 2 poisoned rows the 2026-07-17 consolidated close-out's audit found
> (`sports_cf8_available_at_backfill_regression-001`/`-002`). Both re-verified NO LONGER live false-`done` (self-
> resolved by prior id-recycling mechanisms — see that plan's todo 5 for the full trace); `audit_false_done.py`'s logic
> re-run fleet-wide confirms `false_done: 0`. Archived to `plans/archive/issues/`.

> **🟢 EXECUTION CONSOLIDATED 2026-07-17** — this doc's open items are now tracked and executed via
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md)
> (operator-session local plan; verified-live classification table there). Do NOT start work from this doc alone — flip
> items in the plan and mirror them here. This doc stays the detail/evidence record.

# Backlog `status: done` diverges from the plan checkbox it's derived from

## What I found

`GET /api/backlog` (live orchestrator, restarted `2026-07-16T18:21:11Z`) for the two tasks gating
`sports_travel_calculator_tz_aware_kickoff_crash-001` (Todo 2):

```json
{"id": "sports_p2_features_history_to_ml_ready-001", "status": "done", "done_sha": "094756d64", ...}
{"id": "sports_p2_features_history_to_ml_ready-002", "status": "done", "done_sha": "0402f7a86", ...}
```

Both SHAs are real, resolvable commits on `unified-trading-pm` — but neither is a completion of the task it's attached
to:

- `094756d64` — `git show --stat`: "sports P2c Todo 1 re-verify — both tracked VMs healthy and progressing, known
  consolidator-staleness self-recovering, no new action needed (slot-11)". This is a Progress Log entry commit from a
  slot that explicitly declined the work and did NOT flip any checkbox (matches the "declining ... checkbox NOT flipped
  ... `/skip-current-task`" pattern used ~30 times in this exact saga).
- `0402f7a86` — "sports P2c Todo 3 re-verify — still BLOCKED-PREREQ, both tracked VMs healthy (slot-8)". Same pattern —
  a decline commit for a DIFFERENT todo (Todo 3), not task -002 ("Features manifest clean over history").

Ground truth check (fresh-pull to LDR HEAD `9d39ed2835ae`, 2026-07-16T18:21:16Z):

```
$ grep -n "^- \[" plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md
101:- [ ] [DATA] P0. **Compute features 2015→present** ...          <- task -001's source todo
109:- [ ] [DATA] P1. **Features manifest clean over history** ...    <- task -002's source todo
```

Both still `[ ]`. This plan's own Progress Log independently re-verified Todo 1 as `[ ]` at least 30 times across
2026-07-14 through 2026-07-16 (most recently ~14:3xZ today, ~4h before this check) — real coverage percentages tracked
each time (59.8% → 68.6% → ... , never reaching completion). So this is not a stale single read; it's a sustained,
repeatedly-reconfirmed contradiction between the backlog DB's `status: done` and the plan file's actual checkbox state,
which `codex/`/CLAUDE.md declare the SSOT (`done_definition: Checkbox flipped in plan + code shipped` on every task).

## Why it matters

This was previously invisible/inert because `gate_on_depends` never wired for `.md`-suffixed `depends_on` entries (the
bug `agent-orchestrator@2d6365f` fixed, per this issue doc's own — a sibling doc's — Progress Log, slot-12
2026-07-15T12:3xZ) **and** the live process hadn't been restarted to pick up that fix (confirmed unchanged
`server_started: 2026-07-15T07:30:19Z` on ~15 consecutive checks through 2026-07-16T14:3xZ). Now that the restart has
finally landed (`2026-07-16T18:21:11Z`), `gate_on_depends` is live — and it just handed out a dispatch
(`sports_travel_calculator_tz_aware_kickoff_crash-001` to slot 13) whose `dispatch_reason` says "prereqs met", when the
actual upstream work is NOT met by the plan's own ground truth. In other words: the exact mechanism that was fought for
across ~36 dispatches and a multi-day operator escalation to correctly gate premature dispatch is now active, but is
trusting a `done` status that itself appears to be wrong — so the fix doesn't yet deliver the safety it was built for.

If this "`status: done` without a matching plan checkbox flip" pattern is not unique to these 2 tasks, any other
`gate_on_depends`/`prereqs.completed_tasks`-gated task in the fleet could be dispatching on the same false-positive
basis — a correctness regression hiding behind what looks like the fix finally working.

## Recommended decision

**Root-cause CONFIRMED (not just plausible) by reading the `/done` handler directly**
(`agent-orchestrator/server/routes/slots_worker.py:601-760`, `done_slot()`): `plan_flip = verify.check_plan_flip(...)`
runs, and when the cited commit doesn't touch the plan checkbox it appends a `no_plan_flip` `DoneWarning` — but that
warning is **never enforced**. The function only ever raises `HTTPException` for the B1 ownership/idempotency checks
(already-done / not-holder, lines 644-689) and (under a strict env flag) the M9 origin-unreachable case; `no_plan_flip`
falls straight through to `task_row.status = "done"` regardless. So ANY `/done` call whose cited SHA is a real,
resolvable, reachable commit — even a routine "re-verify, declining, no action taken" Progress Log commit that
explicitly did NOT touch the plan — is accepted as a completion. This is exactly what happened here: `094756d64` and
`0402f7a86` are legitimate commits (they pass SHA verification) but are declining-commits, not completions, for the
tasks they're attached to. A slot most likely called `/done` citing its post-fresh-pull HEAD SHA as "evidence" (an easy
mistake — that SHA IS on `live-defi-rollout`, so it passes `verify.verify_done`) without registering that
`check_plan_flip` would (correctly) find no flip and only warn, not block.

Fix: upgrade `no_plan_flip` from warning-only to a **hard 409** (mirroring the existing
`ORCHESTRATOR_DONE_REQUIRE_ORIGIN` strict-mode pattern already used for the M9 origin gate) whenever
`plan_flip["applicable"]` is true — i.e. whenever the task carries a path-shaped `plan_ref` at all, not just for
`gate_on_depends`-relevant tasks, since ANY task's false "done" can silently poison a downstream
`prereqs.completed_tasks` gate today or in the future. Pair with a one-off audit sweep (recommended separately, Todo
below) to catch and reopen any pre-existing false-`done` tasks created before the hard-check ships (this doc's
`-001`/`-002` are confirmed instances; there may be others).

## Todos

- [x] ✅ [INFRA] P1. **Root-caused** how `sports_p2_features_history_to_ml_ready-001`/`-002` got `status: done` while
      their source plan checkboxes remain `[ ]`: confirmed via direct code read that
      `agent-orchestrator/server/routes/slots_worker.py`'s `done_slot()` treats `no_plan_flip` as a non-blocking
      `DoneWarning` (see "Recommended decision" above) — any `/done` call with a real, reachable, but non-completing SHA
      is accepted. No DB/YAML mutation performed (root-clone write is outside worker scope); this todo closes the "which
      of a/b/c" question raised at filing time — it is (a) verbatim, confirmed. (repo: agent-orchestrator) —
      data_engineering slot-13, 2026-07-16.
- [x] ✅ [INFRA] P1. **Upgraded `no_plan_flip` from warning to a hard 409** in `done_slot()`
      (`server/routes/slots_worker.py`) — new `ORCHESTRATOR_DONE_REQUIRE_PLAN_FLIP` config flag (default ON, mirrors the
      `ORCHESTRATOR_DONE_REQUIRE_ORIGIN` strict-mode pattern) hard-rejects `/done` with a 409 whenever
      `plan_flip["applicable"]` is true and the cited commit didn't touch the task's `plan_ref` checkbox; the legacy
      warn-only M3 path is preserved as the env-gated fallback. Added 3 regression tests
      (`tests/test_done_gate_plan_flip_hard_reject.py`): reject-on-unrelated-sha, accept-on-flip, and
      legacy-path-when-env-disabled. Full `quality-gates.sh` green (1350 passed, 1 skipped). Follow-on same session:
      found + fixed two adjacent bugs (`verify._detect_sibling_pm_worktree`'s umbrella-vs-repo-level worktree mismatch,
      and `regen_backlog_from_plan.py` dropping the `issues/` segment from `plan_ref`) that made this exact gate inert
      or fleet-wide-false-rejecting for the cross-repo / issue-doc-sourced cases — see Progress Log. (repo:
      agent-orchestrator) — agent-orchestrator@87d6fde + agent-orchestrator@666c860, infra slot-13, 2026-07-16.
- [x] ✅ [INFRA] P2. **One-off audit sweep**: cross-checked every current `status: done` backlog task carrying a
      `plan_ref` against that plan's live checkbox state — **7/7 (100%) were false-`done`**, not just this doc's
      `-001`/`-002`. Built the missing correction path (`POST /api/backlog/{id}/reopen`, `agent-orchestrator@164378c`, 3
      new tests, full QG green) since none existed, then called it for all 7; verified `GET /api/backlog?status=done`
      now returns 0 tasks with a `plan_ref` and 3/7 already re-dispatched to live slots. Full per-task verdict +
      evidence in the Progress Log. (repo: agent-orchestrator) — infra slot-15, 2026-07-16.
- [x] ✅ [DATA] P2. **Once the above is root-caused and corrected**, re-verify whether
      `sports_p2_features_history_to_ml_ready-001` (Todo 1, "Compute features 2015→present") is actually complete before
      trusting any future `gate_on_depends` dispatch of `sports_travel_calculator_tz_aware_kickoff_crash-001` Todo 2 —
      **re-verified NOT complete**: `sports_p2_features_history_to_ml_ready_2026_06_27.md` line 101 is still `- [ ]` at
      LDR HEAD `6a076159a`, and the plan's own Progress Log's most recent bucket-coverage reading is ~55.4% (2,332/4,210
      days) — genuinely in-progress, nowhere near the ≥95% completeness gate. The backlog's `status: done`/`done_sha` on
      `-001` (and `-002`) is confirmed STALE/WRONG and must not be trusted by any `gate_on_depends` dispatch until Todo
      3's audit sweep reopens it. Not reopening it myself — that DB/YAML mutation is `[INFRA]`-scoped (Todo 3) and
      outside this `data_engineering` task's remit. (repo: features-service, plan:
      sports_p2_features_history_to_ml_ready_2026_06_27.md) — data_engineering slot-6, 2026-07-16.

- [x] ✅ [BACKEND] P0. **NEW 2026-07-17 — the actual root cause: `check_plan_flip` detects a FILE TOUCH, not a CHECKBOX
      FLIP. This doc's four shipped commits do not close the bug, and it is reproducing live.** Everything already
      ticked above is real and stays ticked — the hard-409 (`slots_worker.py:709`) and `/reopen`
      (`routes/backlog.py:294`) both exist and work. The defect is one layer down: `check_plan_flip`
      (`server/verify.py:507`) asks only _"did the verified commit touch the plan-of-record file?"_ (its own docstring),
      implemented as a filename match over the commit's file list. It never diffs the todo's `[ ]`->`[x]`. So the
      canonical `/skip-current-task` artefact — a `docs(plans):` commit appending a Progress Log paragraph and
      deliberately NOT flipping the box — passes the gate and is accepted as a `done_sha`. **The gate blocks every case
      except the one it was built for.** Proof, all post-fix: `l2_book_microstructure_capture-005` (`done_sha=6edc8325`,
      19:54Z) and `-007` (`1e1c2bda8`, 19:59Z) are 2 of the 7 tasks Todo 3 reopened at 19:41Z, back to false-`done`
      within the same session; both SHAs post-date all four fix commits; both are plan-file-only (33 insertions, zero
      code) and say "Checkbox NOT flipped (still correct)" in their own messages; both target boxes are STILL `- [ ]` at
      LDR HEAD (`l2_book_microstructure_capture_2026_07_13.md:173,213`). **Fixed**: `check_plan_flip` now verifies the
      SPECIFIC todo's checkbox transition across the commit via a new `_diff_flips_checkbox()` helper — diffs the plan
      path at the relevant commit and requires BOTH a removed `- [ ] <brief>` line matching the task's exact
      `BacklogTask.brief` text AND an added `- [x] ...` line, in both the single-repo mode (diffs the worker's own
      `sha`) and the cross-repo mode (diffs the PM sibling worktree's matched flip commit — the identical gap existed
      there too, since `_pm_log_touches_plan_ref` only checked "did a recent commit touch the path", same bug). **Gate
      met**: `test_done_rejects_when_commit_touches_plan_file_but_leaves_checkbox_unflipped` (single-repo) and
      `test_done_rejects_cross_repo_when_pm_commit_touches_file_but_leaves_checkbox_unflipped` (cross-repo) are
      bug-injection regression tests — a synthetic doc-only "declining" commit against a plan (touches the file, appends
      a Progress Log paragraph, leaves the checkbox `- [ ]`) is now REJECTED with 409
      (`reason=file_touched_no_checkbox_flip` / `cross_repo_pm_file_touched_no_checkbox_flip`), reproducing exactly the
      `l2_book_microstructure_capture-005`/`-007` live incident against the fixed code. Full `quality-gates.sh` green
      (1365 passed, 1 skipped, up from 1358). **Corollary decided**: this fix makes new false-`done` rows via this exact
      mechanism (file-touch-without-checkbox-flip) impossible going forward — `/done` now hard-rejects them at the
      moment of the call, before a `done_sha` is ever recorded — so Todo 3's one-off reopen sweep does NOT need to
      become periodic for this defect class; a genuinely NEW divergence mechanism would need its own detection, but none
      is known. The "no NEW false-`done` row in a live 24h window" observation is left to the operator/review agent's
      post-deploy audit — a single dispatch can't observe 24h of live traffic. (repo: agent-orchestrator) —
      agent-orchestrator@86b8b8b, backend_engineer slot-13, 2026-07-17.

- [x] ✅ [INFRA] P1. **The gate is fixed; the ALREADY-POISONED rows are not. Two are still live.** Independently
      verified 2026-07-17 (operator session) against authoritative sources on BOTH sides — DB read live from planning-vm
      `/var/lib/orchestrator/state.db` via SSM, plan checkboxes read at `origin/live-defi-rollout` (NOT a local checkout
      — see the trap note below): **`l2_book_microstructure_capture-005` (`done_sha=6edc83254`) and `-007` (`1e1c2bda8`)
      are STILL `status=done` while their todos are STILL `- [ ]`.** `@86b8b8b`/`@d716fd0` stop NEW false-`done`s at
      `/done`-time; a gate cannot repair a row already written. These two are exactly the rows Todo 3 reopened at 19:41Z
      that fell back by 19:59Z — the difference now is that **a reopen will finally STICK**, because the mechanism that
      re-poisoned them is closed. Reopen via `POST /api/backlog/{id}/reopen`. **Operator-gated**: reopening requeues
      them for dispatch (correct — the work genuinely is not done), so it is a live state change, not a bookkeeping
      edit. **Reopened 2026-07-17, infra slot-2**: re-verified ground truth first (fresh-pulled to LDR HEAD
      `dc038c764e7f`, `l2_book_microstructure_capture_2026_07_13.md:173`/`:213` both still `- [ ]`, `GET /api/backlog`
      confirmed both rows still `status=done` with the exact cited `done_sha`s), then called
      `POST /api/backlog/l2_book_microstructure_capture-005/reopen` and `-007/reopen` — both returned
      `{"ok": true, "prior_status": "done", "new_status": "queued"}` with `done_sha` cleared. Verified it STUCK (not
      just a 200): re-fetched both task ids individually (`status: queued`, `done_sha: None`) and re-ran
      `GET /api/backlog?status=done`, confirming zero non-orphan `done` tasks carry a `plan_ref` fleet-wide. Both are
      back in the queue for genuine re-dispatch, now protected by the file-touch-vs-checkbox-flip gate (`@86b8b8b`/
      `@d716fd0`) so this exact re-poisoning mechanism cannot recur. (repo: agent-orchestrator, DB-only mutation, no
      code change) — infra slot-2, 2026-07-17.
- [x] ✅ [INFRA] P2. **58 of 64 `done` rows are UNAUDITABLE, which is not the same as clean.** `tasks.brief_hash` is
      NULL on every row predating that column, so there is no way to map those tasks back to a specific todo and check
      it. The corollary above ("no periodic sweep needed") is sound **for new rows via this defect class** but says
      nothing about this historical tail: we do not know whether they are honest, and `gate_on_depends` trusts them.
      Either backfill `brief_hash` for historical rows (making them auditable) or explicitly rule the tail out of scope
      and record WHY. Tool: `agent-orchestrator/scripts/orchestrator/audit_false_done.py` (promoted 2026-07-17,
      `agent-orchestrator@3f265cc`) — reports `UNAUDITABLE` separately from `honest` precisely so this tail cannot be
      silently counted as clean. **Re-run it; its answer has a date on it.** — **RESOLVED 2026-07-17, infra slot-6:
      ruled out of scope for retroactive backfill, WHY recorded.** Re-ran the tool live (this slot runs directly on the
      orchestrator VM — `hostname`/`workspace_root` match, so `/var/lib/orchestrator/state.db` and the PM sibling clone
      are local, no SSM needed): **at ref `06fab4d08` (2026-07-17), of 68 `done` rows carrying a `plan_ref`: 0
      false_done, 12 honest, 56 UNAUDITABLE, 0 unresolved** (up from 58/64 at filing — the tail grows with fleet
      throughput, as expected for a frozen historical bucket). Cross-checked all 56 unauditable task ids against live
      `GET /api/backlog`: **all 56 are orphaned** (`title` = the synthetic "(orphan — no longer in backlog.yaml)"
      placeholder) — none are still-open todos, so none would self-heal via the existing
      `sync_backlog_to_db`/`bootstrap.py:352` backfill-on-regen path (that path only fires for a `task.id` still present
      in the live-derived `backlog.tasks` list; a pruned id is never visited). Checked every other durable source for
      the lost plaintext: `data/config/backlog.yaml` is gitignored (`# Live backlog + archives are runtime artifacts`) —
      no VCS history to recover a pruned entry's `brief` from; the referenced `backlog_archive_*.yaml` pattern is also
      gitignored but **no writer for it exists anywhere in the repo** (grepped, zero hits) — it's a dead/aspirational
      ignore-rule, not a live snapshot mechanism; `activity_log.details_json` (checked directly against the live DB for
      several orphaned ids, e.g. `l2_book_microstructure_capture-001`) never stores `brief`/`title` — only dispatch
      `reason`/`trigger` metadata. **The plaintext needed to compute a matching `brief_hash` is not persisted anywhere
      still reachable for these 56 rows.** One theoretical path remains: `TaskRow.plan_ref` + `done_sha` + `done_at` DO
      survive pruning (checked directly — e.g. `l2_book_microstructure_capture-001` still carries
      `plan_ref=plans/active/l2_book_microstructure_capture_2026_07_13.md`, `done_at=2026-07-13 19:19:25`), which in
      principle narrows a search of the PM plan file's own (git-tracked) history for the flip commit near `done_at`.
      **Deliberately NOT attempting this per-row reconstruction**: a plan file can have many todos flip over its
      lifetime, so a time-window search has no way to disambiguate WHICH removed `- [ ] ...` line belongs to THIS
      task_id without the original brief text to match against (the exact ambiguity `_diff_flips_checkbox` was built to
      resolve using a KNOWN brief — here the brief is precisely what's missing). A wrong heuristic match would silently
      produce a **false** `brief_hash` — manufacturing false confidence, which is strictly worse than an honest
      `UNAUDITABLE` label. Not worth the risk for a single P2 dispatch; if ever revisited, it needs a human/reviewer
      sign-off per reconstructed row, not an automated guess. **Ruling**: the 56-row historical tail (every `done` row
      whose checkbox flip predates the `brief_hash` column AND has since been pruned from `backlog.yaml`) is
      **permanently unauditable by exact todo identity and out of scope for retroactive backfill** — not because no one
      looked, but because the source text is genuinely gone and no safe reconstruction exists. This bucket is **frozen,
      not growing**: every row inserted after `brief_hash` shipped gets one at creation (`bootstrap.py:393`), and every
      row still open in `backlog.yaml` self-heals on its next regen tick (`bootstrap.py:352`) — confirmed empirically
      today (`false_done: 0`, `unresolved: 0`). Residual risk: `gate_on_depends` still can't distinguish an "unauditable
      but actually honest" row from an "unauditable and silently wrong" one within these 56 — recommending (not
      building, out of this task's single-unit scope) a follow-on to surface an explicit `UNAUDITABLE` provenance flag
      on `GET /api/backlog` responses so a downstream gate/operator can at least SEE which dependency is trusted without
      proof, rather than it reading identically to a verified-honest `done`. (repo: agent-orchestrator, no code change —
      investigation + doc-only ruling) — infra slot-6, 2026-07-17.

## Progress Log

### 2026-07-16T18:2xZ UTC — data_engineering slot-13 (finding filed)

Discovered while working `sports_travel_calculator_tz_aware_kickoff_crash-001` Todo 2 (36th consecutive dispatch of that
task). Filed this issue doc per findings-triage HARD RULE (SSOT contradiction / big finding). No code changed by this
doc. See the sibling issue doc's Progress Log for the corresponding Todo 2 decline entry.

### 2026-07-16T18:4xZ UTC — data_engineering slot-13 (root-caused, Todo 1 flipped)

Prompted to "default fuller solution, do not idle" on a `/progress` check-in — went past filing-and-waiting to actually
confirm root cause rather than leave it as guesswork. Read `agent-orchestrator/server/routes/slots_worker.py`'s
`done_slot()` directly (lines 601-760): `no_plan_flip` is computed via `verify.check_plan_flip(...)` but only ever
appended as a `DoneWarning` — the function's only `HTTPException` raises are the B1 already-done/not-holder checks and
the strict-mode M9 origin gate. So a `/done` call citing ANY real, reachable SHA sails through to `status="done"` even
when that SHA never touched the cited `plan_ref` checkbox. This is a confirmed code-level gap, not speculation: matches
hypothesis (a) from this doc's original filing exactly. No DB write attempted (root-clone SQLite/YAML write is outside
worker scope, confirmed no reopen/reset endpoint exists on `/api/backlog` either — checked `server/routes/backlog.py`).
Flipped Todo 1 (root-cause) `[x]`; left Todos 2 (the actual code fix) and 3 (audit sweep) open for an `infra`-role
follow-up, since shipping a fleet-wide `/done`-semantics change is a higher-blast-radius call than this task's remit
justifies unilaterally. `sports_travel_calculator_tz_aware_kickoff_crash-001` Todo 2 itself remains genuinely blocked
regardless (ground truth re-checked, unchanged) — see the sibling issue doc.

### 2026-07-16T18:5xZ UTC — data_engineering slot-13 (Todo 4 dispatched — still premature, declining)

Backlog regen already picked up this doc's own Todo 4 ("once the above is root-caused and corrected, re-verify whether
`sports_p2_features_history_to_ml_ready-001` is actually complete") and dispatched it back to me
(`backlog_task_done_status_diverges_from_plan_checkbox-003`). Its own text is explicit: "**once** the above is
root-caused **and corrected**" — root-cause (Todo 1) is now `[x]`, but "corrected" (Todo 2, the `no_plan_flip`→hard-409
fix) is still open. So this todo's own stated precondition isn't fully met yet; doing the re-verify now would be the
same premature-dispatch pattern this whole doc exists to describe. Re-checked ground truth anyway (cheap, no GCS walk):
fresh-pulled to LDR HEAD, `sports_p2_features_history_to_ml_ready_2026_06_27.md` lines 101/109 still `- [ ]` — Todo 1
("Compute features 2015→present") is still genuinely incomplete, consistent with every prior check today. Not flipping
this todo — declining, `/skip-current-task`, will re-check once Todo 2 (the code fix) ships.

### 2026-07-16T18:5xZ UTC — data_engineering slot-15 (Todo 4 re-dispatched again — precondition still unmet)

Same task (`backlog_task_done_status_diverges_from_plan_checkbox-003`) dispatched again, this time to slot 15.
Independently re-verified both preconditions from a fresh boot (fresh-pulled every repo in this slot to LDR HEAD
`d206e51558a3866cdfba3b14c4977935e0219dc3`, 2026-07-16T18:39:55Z):

- **Todo 2 (the code fix) still not shipped**: read `agent-orchestrator/server/routes/slots_worker.py` `done_slot()`
  directly (current LDR HEAD) — `no_plan_flip` is still only appended to the `warnings: list[DoneWarning]` (line
  709-715); the function's only `HTTPException` raises remain the B1 already-done/not-holder checks and the strict-mode
  M9 origin/`sha_unverifiable` gates (lines 752-811). No hard-409 branch exists for `no_plan_flip` yet.
- **Ground truth on `sports_p2_features_history_to_ml_ready_2026_06_27.md`**: lines 101
  (`Compute features 2015→present`, task -001) and 109 (`Features manifest clean over history`, task -002) both still
  `- [ ]` at this LDR HEAD — unchanged from every prior check today.

So this todo's own stated precondition ("once the above is root-caused **and corrected**") is still not met — Todo 2 is
the actual gating fix and it's `[INFRA]`-tagged, outside this task's `data_engineering` assigned_role scope anyway. Not
absorbing it unilaterally (single-agent, higher-blast-radius change to `/done` semantics). Declining again via
`/skip-current-task` — will be actionable once Todo 2 ships.

### 2026-07-16T19:2xZ UTC — infra slot-13 (Todo 2 shipped — hard-409 live)

Dispatched `backlog_task_done_status_diverges_from_plan_checkbox-001` (Todo 2, `[INFRA]`-tagged, in scope). Implemented
the fix in `agent-orchestrator/server/routes/slots_worker.py::done_slot()`: the existing `no_plan_flip` warning block
(previously append-only) now also raises `HTTPException(409)` — logging `slot_done_rejected_no_plan_flip` first — when a
new config flag `done_require_plan_flip` (env `ORCHESTRATOR_DONE_REQUIRE_PLAN_FLIP`, `BoolEnvTrue`, **default ON**) is
set, mirroring the existing `done_require_origin`/`ORCHESTRATOR_DONE_REQUIRE_ORIGIN` warn-first-ratchet pattern used for
the M9 origin gate. Chose default-ON (unlike M9's default-OFF) because this is a confirmed, already-exploited
data-integrity hole (this doc's own `-001`/`-002` instances) rather than a speculative risk — env stays as the emergency
off-switch, and the pre-existing warn-only M3 dual-flip-pattern escalation block is preserved as the fallback path when
the flag is disabled. Added `server/config.py::done_require_plan_flip` field.

Added `tests/test_done_gate_plan_flip_hard_reject.py` (3 tests, calling `slots_worker.done_slot()` directly against a
real git repo + bare origin, mirroring `test_task_lifecycle_done_gate_resume.py`'s pattern): (1)
`test_done_rejects_unrelated_sha_for_path_shaped_plan_ref` — a commit that touches an unrelated file gets a 409, task
stays `dispatched`; (2) `test_done_accepts_when_commit_flips_the_plan_checkbox` — a commit that DOES flip the checkbox
completes normally; (3) `test_done_gate_disabled_by_env_keeps_legacy_warning_path` —
`ORCHESTRATOR_DONE_REQUIRE_PLAN_FLIP=false` falls back to the pre-existing warn-only behavior. Also tightened the
now-inaccurate `DoneWarning` docstring (`server/models/worker_api.py`) which claimed "never blocks /done" — it already
didn't, for the M9 origin gates, and now doesn't for `no_plan_flip` either.

Ran `bash scripts/quality-gates.sh` (Pass 1, full, no skip flags) on committed HEAD: ruff lint/format clean,
basedpyright 0 errors, pytest 1350 passed / 1 skipped (existing `test_task_lifecycle_done_gate_resume.py` suite + the 3
new tests, no regressions). Shipped via `quickmerge.sh --agent --files`: landed on `live-defi-rollout` @
`agent-orchestrator@87d6fde`. Todo 2 flipped `[x]` in this same turn. Todos 3 (one-off audit sweep of pre-existing
false-`done` tasks) and the sibling plan's Todo 4 (re-verify `sports_p2_features_history_to_ml_ready-001`) remain open —
the audit sweep (Todo 3) is a fleet-wide DB/YAML mutation task outside a single worker's normal write scope and is left
for a follow-up dispatch.

### 2026-07-16T18:5xZ UTC — data_engineering slot-2 (Todo 4 re-dispatched a third time — precondition still unmet)

Same task (`backlog_task_done_status_diverges_from_plan_checkbox-003`) dispatched again, this time to slot 2.
Independently re-verified both preconditions from a fresh boot (fresh-pulled `agent-orchestrator` and
`unified-trading-pm` in this slot to LDR HEAD `73e6f05135b9`, 2026-07-16T18:46:02Z):

- **Todo 2 (the code fix) still not shipped**: read `agent-orchestrator/server/routes/slots_worker.py` `done_slot()`
  directly (current LDR HEAD `cb0fe676b756`) — `no_plan_flip` is still only appended to `warnings: list[DoneWarning]`
  (lines 709-715, and the corresponding activity-log branch at 867-896); the function's only `HTTPException` raises
  remain the B1 already-done/not-holder checks and the strict-mode M9 origin/`sha_unverifiable` gates. No hard-409
  branch exists for `no_plan_flip` yet.
- **Ground truth on `sports_p2_features_history_to_ml_ready_2026_06_27.md`**: lines 101
  (`Compute features 2015→present`, task -001) and 109 (`Features manifest clean over history`, task -002) both still
  `- [ ]` at this LDR HEAD — unchanged from every prior check today.

Also independently checked the unrelated but higher-priority operator message that arrived on this session's boot
heartbeat (a claimed "unpushed CI-red-fix commit `9e41e2a`" in this slot's `deployment-api` clone): confirmed it was
stale — that commit had been amended to `b63fa7c` (same fix, same message) and already fast-forward-merged onto
`origin/live-defi-rollout` before this session started (HEAD even with origin; the `(market-data, defi): 3600s`
staleness exception is present in `tests/unit/test_route_health_overview.py`). Nothing to ship there.

This todo's own precondition ("once the above is root-caused **and corrected**") remains unmet — Todo 2 is still
`[INFRA]`-scoped and outside this task's `data_engineering` assigned_role. Declining again via `/skip-current-task` —
will be actionable once Todo 2 ships.

### 2026-07-16T18:5xZ UTC — data_engineering slot-5 (Todo 4 re-dispatched a fourth time — precondition still unmet)

Same task (`backlog_task_done_status_diverges_from_plan_checkbox-003`) dispatched again, this time to slot 5.
Independently re-verified both preconditions from a fresh boot (fresh-pulled all 24 repos in this slot to LDR HEAD;
`agent-orchestrator` HEAD `cb0fe676b756b2b0491d96422ce43ffef131bc99`, `unified-trading-pm` HEAD
`7ae7ac3ef7e5541854abc9af6878a9b0b9ec042f`):

- **Todo 2 (the code fix) still not shipped**: read `agent-orchestrator/server/routes/slots_worker.py` `done_slot()`
  directly at this HEAD — `no_plan_flip` is still only appended to `warnings: list[DoneWarning]` (line 712) and logged
  as an activity event (lines 870/883); the function's only `HTTPException` raises remain the B1 already-done/not-holder
  checks and the strict-mode M9 origin/`sha_unverifiable` gates. No hard-409 branch exists for `no_plan_flip` yet — same
  HEAD as the slot-2 check, confirming no fix has landed since.
- **Ground truth on `sports_p2_features_history_to_ml_ready_2026_06_27.md`**: lines 101
  (`Compute features 2015→present`, task -001) and 109 (`Features manifest clean over history`, task -002) both still
  `- [ ]` at this LDR HEAD — unchanged from every prior check today.

This todo's own precondition ("once the above is root-caused **and corrected**") remains unmet — Todo 2 is still
`[INFRA]`-scoped and outside this task's `data_engineering` assigned_role, and per the single-task/no-fan-out rule I'm
not absorbing it unilaterally in this session. Declining again via `/skip-current-task` — will be actionable once Todo 2
ships.

### 2026-07-16T19:0xZ UTC — data_engineering slot-3 (Todo 4 re-dispatched a fifth time — precondition still unmet)

Same task (`backlog_task_done_status_diverges_from_plan_checkbox-003`) dispatched again, this time to slot 3.
Independently re-verified both preconditions from a fresh boot (fresh-pulled all 24 repos in this slot to LDR HEAD;
`agent-orchestrator` HEAD `cb0fe676b756b2b0491d96422ce43ffef131bc99` — same as the slot-2/slot-5 checks, confirming no
fix has landed since, `unified-trading-pm` HEAD `d01105238bb0b890b8d5d8e5a53a007d5c5ab308`):

- **Todo 2 (the code fix) still not shipped**: read `agent-orchestrator/server/routes/slots_worker.py` `done_slot()`
  directly at this HEAD (lines 700-730) — `no_plan_flip` is still only appended to `warnings: list[DoneWarning]` (line
  712); the function's only `HTTPException` raises remain the B1 already-done/not-holder checks and the strict-mode M9
  origin/`sha_unverifiable` gates. No hard-409 branch exists for `no_plan_flip` yet. Checked `GET /api/backlog`: task
  `backlog_task_done_status_diverges_from_plan_checkbox-001` (the actual fix) is `status: dispatched` — actively being
  worked by another slot, not stuck/idle, just not yet shipped.
- **Ground truth on `sports_p2_features_history_to_ml_ready_2026_06_27.md`**: lines 101
  (`Compute features 2015→present`, task -001) and 109 (`Features manifest clean over history`, task -002) both still
  `- [ ]` at this LDR HEAD — unchanged from every prior check today.

This todo's own precondition ("once the above is root-caused **and corrected**") remains unmet — Todo 2 is still
`[INFRA]`-scoped, actively dispatched to another slot, and outside this task's `data_engineering` assigned_role.
Declining again via `/skip-current-task` — will be actionable once Todo 2 ships.

### 2026-07-16T19:1xZ UTC — data_engineering slot-7 (Todo 4 re-dispatched a sixth time — precondition still unmet)

Same task (`backlog_task_done_status_diverges_from_plan_checkbox-003`) dispatched again, this time to slot 7.
Independently re-verified both preconditions from a fresh boot (fresh-pulled all 24 repos in this slot to LDR HEAD;
`agent-orchestrator` HEAD `cb0fe676b756b2b0491d96422ce43ffef131bc99` — same as the slot-2/slot-5/slot-3 checks,
confirming no fix has landed since):

- **Todo 2 (the code fix) still not shipped**: read `agent-orchestrator/server/routes/slots_worker.py` `done_slot()`
  directly at this HEAD (lines 700-730) — `no_plan_flip` is still only appended to `warnings: list[DoneWarning]` (line
  712); the function's only `HTTPException` raises remain the B1 already-done/not-holder checks and the strict-mode M9
  origin/`sha_unverifiable` gates. No hard-409 branch exists for `no_plan_flip` yet. `GET /api/backlog`:
  `backlog_task_done_status_diverges_from_plan_checkbox-001` (the fix) and `-002` (the audit sweep) both
  `status: dispatched` — actively being worked, not stuck/idle, just not yet shipped.
- **Ground truth on `sports_p2_features_history_to_ml_ready_2026_06_27.md`**: lines 101
  (`Compute features 2015→present`, task -001) and 109 (`Features manifest clean over history`, task -002) both still
  `- [ ]` at this LDR HEAD — unchanged from every prior check today.

This todo's own precondition ("once the above is root-caused **and corrected**") remains unmet — Todo 2 is still
`[INFRA]`-scoped, actively dispatched to another slot, and outside this task's `data_engineering` assigned_role.
Declining again via `/skip-current-task` — will be actionable once Todo 2 ships.

### 2026-07-16T19:2xZ UTC — data_engineering slot-6 (Todo 4 re-dispatched a seventh time — precondition still unmet)

Same task (`backlog_task_done_status_diverges_from_plan_checkbox-003`) dispatched again, this time to slot 6.
Independently re-verified both preconditions from a fresh boot (fresh-pulled all 24 repos in this slot to LDR HEAD;
`agent-orchestrator` HEAD `cb0fe676b756b2b0491d96422ce43ffef131bc99` — same as the slot-2/slot-5/slot-3/slot-7 checks,
confirming no fix has landed since; `unified-trading-pm` HEAD `350fb86efcfe166525a8e68368ff853b9be65a17`):

- **Todo 2 (the code fix) still not shipped**: `GET /api/backlog` shows
  `backlog_task_done_status_diverges_from_plan_checkbox-001` (the fix) and `-002` (the audit sweep) both
  `status: dispatched` (no `done_sha`) — actively being worked, not stuck/idle, just not yet shipped. Confirmed via
  direct read of `agent-orchestrator/server/routes/slots_worker.py` at this HEAD: `no_plan_flip` is still only appended
  to `warnings: list[DoneWarning]` (line 712); no hard-409 branch exists yet.
- **Ground truth on `sports_p2_features_history_to_ml_ready_2026_06_27.md`**: lines 101
  (`Compute features 2015→present`, task -001) and 109 (`Features manifest clean over history`, task -002) both still
  `- [ ]` at this LDR HEAD — unchanged from every prior check today.

This todo's own precondition ("once the above is root-caused **and corrected**") remains unmet — Todo 2 is still
`[INFRA]`-scoped, actively dispatched to another slot (not stalled), and outside this task's `data_engineering`
assigned_role. Declining again via `/skip-current-task` — will be actionable once Todo 2 ships.

### 2026-07-16T19:2xZ UTC — data_engineering slot-6 (Todo 2 landed mid-session — precondition now met, Todo 4 done)

While preparing to push the above decline entry, `git push` was rejected as non-fast-forward (branch drift, 1 commit
behind). Ran `git pull --rebase --autostash origin live-defi-rollout` (never force-push) and the incoming commit was
`6a076159a` — "docs(plans): flip Todo 2 — no_plan_flip hard-409 shipped (agent-orchestrator@87d6fde)" from slot-13:
`no_plan_flip` is now a hard 409 (env flag `ORCHESTRATOR_DONE_REQUIRE_PLAN_FLIP`, default ON), with 3 regression tests,
full QG green. So Todo 1 (root-caused) and Todo 2 (corrected) are BOTH now `[x]` — this task's own stated precondition
is met for the first time across its 7 dispatches today.

Did the actual re-verify (this task's real deliverable): re-checked
`sports_p2_features_history_to_ml_ready_2026_06_27.md` at the new LDR HEAD — line 101 ("Compute features 2015→present",
task -001) is still `- [ ]`. Checked the plan's own Progress Log for the latest bucket-coverage reading rather than
re-walking the corpus (single-walk discipline): most recent entries read ~55.4-56.1% (2,332-2,363/4,210 days) — well
below the ≥95% completeness gate, genuinely incomplete. So `sports_p2_features_history_to_ml_ready-001` is confirmed NOT
complete, meaning the backlog's `status: done`/`done_sha=094756d64` on it is stale/wrong, same for `-002`
(`done_sha=0402f7a86`, line 109 also still `- [ ]`) — `GET /api/backlog` confirms `-002` (the audit sweep, Todo 3) is
still `status: dispatched`, so reopening these two false-done tasks is pending that INFRA-scoped sweep, not this task.

Flipped Todo 4 `[x]` with this finding recorded inline. Not reopening `-001`/`-002` myself (DB/YAML mutation is Todo 3's
`[INFRA]` scope, outside this `data_engineering` task's remit and outside worker scope per RULES.md §4 — no
`/api/backlog` reopen endpoint exists anyway, confirmed by the original filing). Shipping this doc via quickmerge and
calling `/done`.

### 2026-07-16T19:3xZ UTC — infra slot-13 (adjacent bugs found + fixed — the hard-409 now actually protects the cross-repo case)

Before calling `/done` on the same task (`backlog_task_done_status_diverges_from_plan_checkbox-001`) whose own commit
(`agent-orchestrator@87d6fde`) just shipped Todo 2, simulated `verify.check_plan_flip` locally against this exact
session's own worktree + this task's own `plan_ref`
(`plans/active/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`, NOT the `issues/`-prefixed real path
— see below) to sanity-check the new hard-409 before shipping it fleet-wide. Found `applicable=False`
(`cross_repo_no_pm_worktree`) — i.e. the gate would NOT have fired for this task at all, cross-repo. Traced why and
found two confirmed, adjacent bugs in the exact mechanism my fix now hard-enforces:

1. `verify._detect_sibling_pm_worktree` assumed the reported `/boot` worktree is already repo-level
   (`.tabs/<N>/<repo>/`, PM sibling one level up) — but `verify.verify_done`'s own NEW-3 (2026-05-19) comment confirms
   workers report the SLOT UMBRELLA (`.tabs/<N>/`), where the PM repo is a DIRECT CHILD, not a sibling of the parent.
   Under the (now-standard) umbrella convention, `_detect_sibling_pm_worktree` always returned `None` — meaning the
   ENTIRE cross-repo M3 plan-flip check (the pre-existing warning, and now my hard-409) has been silently inert for the
   PM-integration-default cross-repo case (agents/RULES.md § 2) this whole time. Fixed to try both layouts (umbrella
   first, then repo-level fallback).
2. `regen_backlog_from_plan.py` derived every task's `plan_ref` as `f"plans/active/{plan_path.name}"` — correct for
   plans directly under `plans/active/`, but WRONG for the `plans/active/issues/` docs the same regen also ingests (line
   ~1137, the 2026-06-10 close-the-loop fix): it drops the `issues/` segment, so `plan_ref` never matches the real file.
   Confirmed via this task's OWN `plan_ref` (reported at boot: no `issues/`, but the real file — this doc — lives at
   `plans/active/issues/...`). Combined with fix #1 making `applicable=True` for real, this would have permanently
   409-rejected `/done` for EVERY issue-doc-sourced task fleet-wide (found_in_commit can never match a wrong path) — a
   materially worse outcome than the warning-only gap Todo 2 was fixing. Fixed to derive the ref relative to `plans_dir`
   (preserves any subdirectory).

Re-simulated after both fixes: `check_plan_flip` now correctly reports `applicable=True` for this task's real cross-repo
layout. Added regression coverage: `test_detect_sibling_pm_worktree_resolves_umbrella_and_repo_level` +
`test_done_rejects_cross_repo_umbrella_worktree_when_pm_flip_missing` +
`test_done_accepts_cross_repo_umbrella_worktree_when_pm_flip_present` (all in
`tests/test_done_gate_plan_flip_hard_reject.py`) and `test_issue_doc_plan_ref_preserves_issues_subdir` (in
`tests/test_regen_backlog_from_plan.py`, asserting the exact `plan_ref` value round-trips with `issues/` preserved).
Full `quality-gates.sh` green (1354 passed, 1 skipped, up from 1350 — the 4 new tests). Shipped via
`quickmerge --agent --files`: `agent-orchestrator@666c860`.

Per findings-triage (CLAUDE.md § "Findings triage" — "in your file → fix in same commit; adjacent → fix in YOUR plan"):
both bugs are in the exact file/mechanism (`verify.py`'s `check_plan_flip` machinery) my own task just made
hard-blocking, and leaving them unfixed would have made the hard-409 either (a) a no-op for the dominant cross-repo case
or (b) a fleet-wide false-rejection footgun for every issue-doc-sourced task — either outcome undermines the very fix
this task exists to ship, so both are in-scope here rather than a separate escalation. Calling `/done` now.

### 2026-07-16T19:0xZ UTC — infra slot-15 (Todo 3 — audit sweep executed, code shipped)

Fresh-pulled every slot repo to LDR HEAD before starting. Ran the audit: `GET /api/backlog?status=done` returned 7 tasks
total, all 7 carrying a non-empty `plan_ref`. For each, resolved the plan file in the freshly-pulled PM sibling clone
(`plans/active/<name>.md` or its `issues/` subpath, both searched), matched the task's `title` text to the corresponding
checkbox line, and independently verified via `git show --stat <done_sha>` in whichever repo actually contains that SHA
(not assumed — searched every repo in the slot for it, since `done_sha` for a code-repo task lives outside
`unified-trading-pm`).

**Result: 7/7 (100%) are confirmed false-`done`** — every single currently-`done` task with a `plan_ref` has its
matching checkbox still `- [ ]` at LDR HEAD, and every cited `done_sha` is either an explicit "re-verify, declining, no
action taken" Progress Log commit, a commit for a _different_ todo than the one it's attached to, or (in one case,
`cefi_deribit_combo_and_okx_bare_venue_gaps-001`) a commit whose own message says "Neither entry alone fully wires
capture" — i.e. explicitly partial, and the plan's own `🚧 PARTIAL PROGRESS` annotation on that exact todo agrees. None
of the 7 are a live judgment call; all are unambiguous. Full list (task id → plan_ref → done_sha → verdict):

1. `mvp_backfill_defi_onchain_v10-002` → `mvp_backfill_defi_onchain_v10_2026_06_27.md` L449 → `1cc8d9f3b` (PM repo,
   "fresh gate re-check ... gate still not met") → MISMATCH.
2. `sports_p2_features_history_to_ml_ready-001` → same plan L101 → `094756d64` (PM repo, "no new action needed") →
   MISMATCH (this doc's original finding).
3. `sports_p2_features_history_to_ml_ready-002` → same plan L109 → `0402f7a86` (PM repo, decline commit for a
   _different_ todo, Todo 3) → MISMATCH (this doc's original finding).
4. `cefi_deribit_combo_and_okx_bare_venue_gaps-001` → issue doc L161 → `f0dc61a22ec53405ab83d2bdc7336772421cc244`
   (unified-api-contracts, partial scaffolding per its own commit message and the plan's own annotation) → MISMATCH.
5. `l2_book_microstructure_capture-005` → `l2_book_microstructure_capture_2026_07_13.md` L173 →
   `ef467572d2faef76402353f09777917086034b24` (market-tick-data-service, commit message says "Todo 4" — wrong todo,
   wrong repo for Todo 5's features-service ask) → MISMATCH.
6. `l2_book_microstructure_capture-007` → same plan L213 → `a24f09e095bf4c9925848b4e585550f39dde59c3` (commit message:
   "verified done-condition false, file NOTIFY-OPERATOR finding" — explicitly NOT done) → MISMATCH.
7. `cefi_deribit_combo_and_okx_bare_venue_gaps-008` → issue doc L1385 → `5a05b88` (deployment-service, unrelated VM
   script fix; task title is "Operator decision needed... unified-api-contracts's...") → MISMATCH.

No reopen/reset endpoint existed on `/api/backlog` (confirmed by reading `server/routes/backlog.py` — only
`GET`/`reload`/`regen`/`DELETE`/`blockers` existed) and the live DB (`agent-orchestrator/data/state/state.db`, a
root-clone runtime path outside any slot's git worktree) is out of a worker's write scope directly, so built the missing
correction path rather than hand-editing the DB: `POST /api/backlog/{task_id}/reopen` (new endpoint,
`server/routes/backlog.py` + `ReopenTaskRequest` model) resets `status=queued` via the existing
`ss.release_task_to_queue` helper and clears `done_sha`/`done_at`/`done_evidence`/`done_verification_json`; refuses 409
if the task is currently `dispatched` (same guard as `DELETE`). 3 new regression tests (`tests/test_backlog_reopen.py`:
clears-and-requeues, missing-task-404s, refuses-dispatched). Full `quality-gates.sh` green (1357 passed, 1 skipped).
Shipped via `quickmerge --agent --files`: `agent-orchestrator@164378c`.

Root-clone deploy is on the existing `ao-self-pull.sh` cron (`*/15`, FF-pulls + restarts on HEAD change — confirmed from
`/var/log/ao-self-pull.log`, not assumed) so the new endpoint needs that cycle before it's callable; armed a background
watchdog (`run_in_background`, ≤20min bound) that waits for the root clone to reach `164378c`, then calls `/reopen` for
all 7 confirmed task ids above with the audit reason, and writes the responses to `reopen_results.json`. Continuing to
monitor rather than idle-waiting; will append the outcome + flip this todo once the watchdog reports back (or file a
follow-up if the 20min window lapses without a deploy).

### 2026-07-16T19:4xZ UTC — infra slot-15 (Todo 3 — reopen executed + verified, closing)

Root clone reached `164378c` at 19:41:07Z (one `ao-self-pull` tick after ship, as expected) and the endpoint probed live
at 19:42:05Z. Called `POST /api/backlog/{id}/reopen` for all 7 confirmed-mismatch task ids from the audit above — all 7
returned `{"ok": true, "prior_status": "done", "new_status": "queued", ...}` with each task's actual prior `done_sha`
echoed back (full log + responses in this task's `reopen_results.json`, not reproduced here). Verified against the live
API immediately after: `GET /api/backlog?status=done` now returns **0** tasks carrying a `plan_ref` (down from 7) —
confirms every reopened row actually left the `done` bucket, not just a 200 with no real effect. Cross-checked the full
listing per task id: 4/7 sitting `queued`, 3/7 already re-`dispatched` to live slots
(`mvp_backfill_defi_onchain_v10-002`→slot 2, `sports_p2_features_history_to_ml_ready-001`→slot 3,
`cefi_deribit_combo_and_okx_bare_venue_gaps-001`→slot 5) — the fleet picked them back up within seconds of requeue, each
now with `done_sha: null`, so a future `/done` on any of them goes through the fresh hard-409 gate (Todo 2) rather than
repeating this exact failure mode. Audit sweep is complete: no other `status: done` + `plan_ref` task existed fleet-wide
beyond the 7 found (0 remain, and the sweep re-ran against live state post-fix, not a stale snapshot). Closing this
todo. (repo: agent-orchestrator) — infra slot-15, 2026-07-16.

### 2026-07-16T19:5xZ UTC — infra slot-15 (adjacent finding + fix: this task's own `/done` self-blocked on the fresh gate)

Calling `/done` for this task hit the very gate Todo 2 just shipped: 409 `cross_repo_pm_log_clean` against
`plan_ref: "plans/active/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md"` (no `issues/`) even though
the real file — and my genuine flip commit `unified-trading-pm@828c7ac` — live at
`plans/active/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`. Root cause: this task's own
`TaskRow`/`backlog.yaml` entry was created BEFORE the `regen_backlog_from_plan.py` `issues/`-segment fix landed
(`agent-orchestrator@666c860`, Todo 2's follow-on), so it still carries the pre-fix, `issues/`-stripped `plan_ref`. That
fix only corrects NEW parses — it does not retroactively correct already-existing rows — so `check_plan_flip`'s
cross-repo git-log search (`_pm_log_touches_plan_ref`) was searching a path that doesn't exist and finding nothing, even
though the flip is real. Given the fresh hard-409 gate is now LIVE fleet-wide, every other pre-fix issue-doc- sourced
task carries the same stale `plan_ref` and would hit the identical false rejection on its own `/done` — a fleet-wide
footgun, not a one-off. Fixed `check_plan_flip` (`server/verify.py`) to try both the literal `plan_ref` and its
`issues/` variant (added `_plan_ref_candidates()`), in both the mode-1 file-in-worktree check and the mode-2 cross-repo
git-log search, before concluding no flip happened. New regression test
(`test_done_accepts_when_task_plan_ref_is_stale_missing_issues_segment`) reproduces this exact self-block. Full
`quality-gates.sh` green (1358 passed, 1 skipped, up from 1357). Shipped via `quickmerge --agent --files`:
`agent-orchestrator@7053dcf`. Per findings-triage (in-file → same-commit-adjacent scope): this bug is in the exact
mechanism (`check_plan_flip`) my own task's `/done` call just exercised, and leaving it unfixed would silently
false-reject every other pre-fix issue-doc-sourced task's legitimate `/done` — clearly in-scope here. Calling `/done`
again now with the corrected gate in place.

### 2026-07-17T UTC — backend_engineer slot-13 (the real fix — file touch vs checkbox flip, all todos now closed)

Dispatched `backlog_task_done_status_diverges_from_plan_checkbox-001` (the P0 `[BACKEND]` todo added by main-agent's
2026-07-17 issue-doc-status-sweep audit, which REOPENED this doc after finding the four earlier commits guard the wrong
thing — `l2_book_microstructure_capture-005`/`-007` reproduced the exact bug live post-fix). Fresh-pulled both repos to
LDR HEAD before starting; re-confirmed the target checkbox was still `- [ ]` (it was) before touching anything.

Root cause confirmed by direct read of `server/verify.py::check_plan_flip` at HEAD: both the mode-1 (single-repo) and
mode-2 (cross-repo) branches computed `found_in_commit` from ONLY "does the commit's file list / recent PM git-log
contain `plan_ref`" — never inspecting what actually changed in that file. A `docs(plans): ... declining` commit that
appends a Progress Log paragraph (touching the file) while deliberately leaving the target `- [ ]` line untouched
satisfies both checks trivially. This is the SAME bug in the cross-repo path too — `_pm_log_touches_plan_ref` returns
the most recent commit touching the path within 10 minutes, with no check on what that commit actually did to the
checkbox.

Fix (`agent-orchestrator@86b8b8b`): added `_diff_flips_checkbox(repo_dir, sha, path, brief)` — runs
`git show --unified=0 --format= <sha> -- <path>` and requires BOTH (a) a removed line matching `- [ ] <brief>` exactly
(brief = `BacklogTask.brief`, the identical single-line text `regen_backlog_from_plan.py`'s `_UNCHECKED_RE` parses the
task from, so no new matching key was needed) AND (b) an added `- [x] ...` line anywhere in that file's diff. Wired into
both `check_plan_flip` modes: mode 1 diffs the worker's own reported `sha` directly; mode 2 diffs whichever commit
`_pm_log_touches_plan_ref` matched (tracked the winning `plan_ref` candidate through the loop, since mode 2 already
tries both the literal and `issues/`-variant paths per the prior fix). Both new call-site params (`sha`, `brief`) are
threaded from `done_slot()` (`task_def.brief`, `req.sha`) — the only production call site. Fails closed
(`found_in_commit=False`) whenever `brief`/`sha` is empty or the diff never shows the exact unchecked line being
removed, matching this doc's own "fail toward rejecting, not silently accepting" posture.

Updated the 4 pre-existing fixtures in `tests/test_done_gate_plan_flip_hard_reject.py` whose `brief="x"` never matched
their plan file's real checkbox text (harmless under the old file-touch-only check; the new diff-match needs a real
brief to compare against) to `brief="[INFRA] P1. do the thing"`, matching the fixtures' own plan content. Added 2
bug-injection regression tests reproducing the live incident directly: a synthetic decline commit that touches the plan
file without flipping the checkbox is now REJECTED with 409
(`test_done_rejects_when_commit_touches_plan_file_but_leaves_checkbox_unflipped` for single-repo,
`test_done_rejects_cross_repo_when_pm_commit_touches_file_but_leaves_checkbox_unflipped` for cross-repo) — both fail
against the pre-fix code and pass against the fix, satisfying this todo's bug-injection gate requirement. Full
`quality-gates.sh` green (1365 passed, 1 skipped, up from 1358 — ruff/basedpyright clean). Shipped via
`quickmerge --agent --files`: `agent-orchestrator@86b8b8b`.

Corollary decided (per the todo's own ask): this fix closes the false-`done` mechanism at its source — `/done` now
hard-rejects a file-touched-but-not-flipped commit BEFORE any `done_sha` is recorded, so Todo 3's one-off reopen sweep
does not need to become a periodic job for THIS defect class. A structurally different divergence mechanism could still
exist and would need its own detection, but none is currently known. The todo's "no NEW false-`done` row in a live 24h
window" clause is a post-deploy observation an operator/review-agent audit should make once the fix has been live for
24h — a single dispatch cannot itself observe 24h of live traffic, so it is not claimed as verified here.

Flipped the todo `[x]` with full evidence inline. All todos in this doc are now checked. Per this doc's own established
precedent (the 2026-07-17 status-sweep commit `unified-trading-pm@df2311afe` explicitly audited 5 similarly-ticked docs
independently before flipping `status: resolved` — this exact doc was the one REOPENED from that sweep because a
self-declared "corrected" claim turned out to be wrong), leaving `status: open` / `resolved_by:` empty for an
independent skeptical audit rather than self-declaring resolution — the same discipline that caught the gap this todo
fixes should be applied before closing the loop on it.

**Adjacent finding + fix, before calling `/done`** (`agent-orchestrator@d716fd0`): while about to commit this exact
Progress Log paragraph as a SEPARATE PM commit (after the checkbox-flip commit `unified-trading-pm@9f813f98a`), realized
my own new mode-2 cross-repo logic would self-block on it — `_pm_log_touches_plan_ref` (as shipped in `86b8b8b`) only
returned the SINGLE MOST RECENT commit touching `plan_ref` within the 10-minute window, and `_diff_flips_checkbox` would
then diff THIS trailing prose-only commit (which doesn't touch the checkbox line at all) instead of the real flip
commit, wrongly reporting `found_in_commit=False`. This is exactly the routine multi-commit-per-session pattern this
whole doc's incident is about, now hitting my own fix. Renamed `_pm_log_touches_plan_ref` to
`_pm_log_commits_touching_plan_ref`, returning ALL matching commits (most-recent-first) instead of just the top one;
`check_plan_flip`'s mode 2 now walks the full list and accepts as soon as any commit's diff flips the checkbox. Added
`test_done_accepts_cross_repo_flip_followed_by_a_trailing_prose_only_commit` reproducing this exact self-block. Full
`quality-gates.sh` green (1366 passed, 1 skipped). Shipped via `quickmerge --agent --files`:
`agent-orchestrator@d716fd0`. Calling `/done` now.

### 2026-07-17T UTC — infra slot-2 (Todo "ALREADY-POISONED rows" — reopened, sticks this time)

Dispatched `backlog_task_done_status_diverges_from_plan_checkbox-001` (the P1 `[INFRA]` todo added by the operator's
2026-07-17 independent audit, which found `l2_book_microstructure_capture-005`/`-007` still `status=done` post-fix).
Fresh-pulled every repo in the slot to LDR HEAD `dc038c764e7f` before touching anything. Re-verified both authoritative
sources independently rather than trusting the doc's dated snapshot: `GET /api/backlog?status=done` still showed both
rows with the exact cited `done_sha`s (`6edc83254`, `1e1c2bda8`);
`grep -n "^- \[" l2_book_microstructure_capture_2026_07_13.md` confirmed lines 173 and 213 both still `- [ ]`.

Called `POST /api/backlog/l2_book_microstructure_capture-005/reopen` and `.../-007/reopen` — both returned
`{"ok": true, "prior_status": "done", "new_status": "queued"}` with `done_sha` cleared. Re-fetched both task ids from
live `GET /api/backlog` to confirm the reopen actually stuck (not just a 200 with no real effect): both read
`status: queued`, `done_sha: null`. Re-ran `GET /api/backlog?status=done` fleet-wide: zero non-orphan `done` tasks now
carry a `plan_ref` — the doc's earlier Todo 3 sweep is back to its clean state, and this time the recurrence is
structurally prevented because `@86b8b8b`/`@d716fd0` (the file-touch-vs-checkbox-flip fix) now hard-blocks the exact
`/done`-time mechanism that re-poisoned these two rows between 19:41Z and 19:59Z on 2026-07-16.

No code change — this is a pure orchestrator DB-state mutation via the existing `/reopen` endpoint, so there is nothing
to ship via quickmerge for this repo. Flipped the todo `[x]` in this same turn with full evidence inline. Shipping this
plan-flip via a direct push (PM `docs(plans):` commit, per the carve-out for plan-flip commits) and calling `/done`.

### 2026-07-17T UTC — infra slot-6 (final Todo — UNAUDITABLE tail ruled out of scope for backfill, all todos now closed)

Dispatched `backlog_task_done_status_diverges_from_plan_checkbox-002` (the last open `[INFRA]` P2 todo). This slot runs
directly ON the orchestrator VM (`workspace_root` from `GET /api/mode` matched this session's own worktree, no SSM
needed for a live read — see finding below), so I re-ran `audit_false_done.py` against the genuinely live
`/var/lib/orchestrator/state.db` and the local PM sibling clone at `origin/live-defi-rollout`.

**Fresh dated answer (ref `06fab4d08`, 2026-07-17)**: 68 `done` rows carry a `plan_ref` (up from 64 at filing) — 0
`false_done`, 12 `honest`, 56 `UNAUDITABLE`, 0 `unresolved`. Cross-checked all 56 unauditable ids against live
`GET /api/backlog`: 100% are orphaned (`title` = the synthetic "(orphan — no longer in backlog.yaml)" placeholder), so
none would self-heal via the existing regen backfill path (`bootstrap.py::sync_backlog_to_db`, line ~352 — only fires
for a `task.id` still present in the live-derived task list).

Investigated whether the lost `brief` text is recoverable from ANY other durable source before ruling it out:
`data/config/backlog.yaml` is gitignored (no VCS history); the `backlog_archive_*.yaml` gitignore pattern has **no
writer anywhere in the repo** (grepped, zero hits — it's a dead ignore rule, not a live snapshot); `activity_log`'s
`details_json` (checked directly against several orphaned ids' rows) never stores `brief`/`title`, only dispatch
reason/trigger. The one surviving lead — `TaskRow.plan_ref`/`done_sha`/`done_at` persist past pruning, which narrows a
search of the (git-tracked) plan file's history for the flip commit — is NOT safely exploitable: multiple todos flip in
the same plan file over its lifetime, and without the original brief text there's no way to disambiguate which removed
`- [ ] ...` line belongs to which task_id. A wrong heuristic match would manufacture a false `brief_hash` — silent false
confidence, strictly worse than an honest `UNAUDITABLE` label. Declined to attempt it.

**Ruling recorded on the todo itself**: the 56-row tail is permanently unauditable by exact todo identity and out of
scope for retroactive backfill — the source text is genuinely gone, not merely un-looked-for. The bucket is frozen, not
growing (every row created after the `brief_hash` column shipped gets one at insert; every still-open row self-heals on
its next regen tick — confirmed by today's `false_done: 0`). Left one follow-on recommendation inline (not built, out of
this single-task's scope): surface an explicit `UNAUDITABLE` provenance flag on `GET /api/backlog` so a downstream
`gate_on_depends` consumer or operator can see which completions are trusted without proof.

No code change — investigation + doc-only ruling, nothing to ship via quickmerge for `agent-orchestrator`. Flipped the
todo `[x]` in this same turn with full evidence inline. All todos in this doc are now checked; per this doc's own
established precedent (it was previously REOPENED from a self-declared "corrected" claim that turned out wrong), leaving
`status: open` / `resolved_by:` empty for an independent skeptical audit rather than self-declaring resolution. Shipping
this plan-flip via a direct push (PM `docs(plans):` commit, per the carve-out for plan-flip commits) and calling
`/done`.

### 2026-07-20T UTC — backend_engineer (per-row decision on the 2 rows the 2026-07-17 skeptical audit found — `ao_backlog_regen_integrity_2026_07_20.md` todo 5)

The independent skeptical audit this doc's last entry asked for happened on 2026-07-17 (the
`ao_open_issues_consolidated_close_out_2026_07_17.md` session): `audit_false_done` reported **2 live false-`done`
rows**, `sports_cf8_available_at_backfill_regression-001` (`done_sha=utl@f5f15e3a`) and `-002`
(`done_sha=utl@0f55cc2b`), both legacy poison predating the `@86b8b8b` gate. Per that plan's own scope note — "AO's part
is notify + re-verify, NOT the fix; do NOT flip a sports checkbox yourself" — re-verified BOTH rows' CURRENT state via
read-only SSM against the live `state.db` before taking any notify action.

**Both rows have already moved on from the 07-17 snapshot — neither is a live false-done today:**

- **`-001`**: now `status: queued` (not `done`) — matches its genuinely still-open checkbox
  (`sports_cf8_available_at_backfill_regression_2026_07_13.md`'s TARGETED re-emit `[DATA]` todo). `done_sha`/`done_at`
  are still populated as historical residue, but the row is no longer claiming completion. Something already corrected
  it between 07-17 and today — not this session's sibling-reset guard (that shipped today, 2026-07-20, after this state
  was already observed), so the correction predates it. No reopen action needed; it's already queued.
- **`-002`**: does not exist as a task row at all anymore. Traced its `activity_log` history: this id was reassigned
  (positional-counter reuse) to a DIFFERENT, later todo — "make backlog parking gates survive plan-checkbox reordering"
  — which genuinely completed and gate-verified on 2026-07-18 (`sha=22738f6`,
  `slot_done_verified: applicable=true, on_origin=true`). That row has SINCE also vanished from `tasks`, meaning the id
  was reused again and, under the pre-fix behavior, silently reset/pruned at least once more since. The specific
  poisoned row the 2026-07-17 audit named simply no longer exists to reopen or flip.

**Broader re-verification (not just the 2 named rows)**: `audit_false_done.py` is currently **non-functional on the live
VM** — a git "dubious ownership" error on the PM sibling worktree silently fails every `git show <ref>:<path>` call, so
a live run today returns `honest: [], false_done: []` regardless of truth (flagged separately in
`ao_backlog_regen_integrity_2026_07_20.md` todo 4's Progress Log for operator attention — not fixed here, it needs an
operator-authorized `git config --global --add safe.directory` on the VM). To still get a real answer, replicated the
script's exact logic (`_brief_hash`/`_UNCHECKED_RE`/`_still_unchecked`) locally against a working PM clone fetched fresh
to `origin/live-defi-rollout` (`c7c5c9a0a`), fed by the live DB's raw rows (read-only SSM): of 44 `done` rows carrying a
`plan_ref`, 38 are the already-ruled-permanently-unauditable NULL-`brief_hash` tail (this doc's own final todo), and of
the 6 with a `brief_hash`, **all 6 are honest** (checkbox genuinely flipped, hash matches) — **0 false_done, 0
unresolved**.

**Gate met**: `false_done: 0`, confirmed via a working equivalent of `audit_false_done.py --db … --pm …` (the sanctioned
tool itself needs the VM-side git fix above before it can confirm this directly). No sports checkbox was flipped by this
session — both named rows resolved via prior mechanisms, not this touch. This closes
`ao_backlog_regen_integrity_ 2026_07_20.md` todo 5's gate and unblocks its todo 7 (closing this doc for real).
