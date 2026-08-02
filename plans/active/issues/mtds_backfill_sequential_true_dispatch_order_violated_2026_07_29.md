---
doc_type: issue
title:
  "`sequential: true` plan still dispatched a downstream todo ahead of its still-queued predecessor —
  mtds_available_at_cross_asset_backfill's prediction-lane apply/resume pair"
summary: >-
  mtds_available_at_cross_asset_backfill_2026_07_13.md carries `sequential: true` (added 2026-07-14 specifically to fix
  the identical class of bug — see the plan's own "Dispatch-order finding" Progress Log entry and
  issues/dispatch_sequential_gate_fix_2026_07_24.md). Despite that, slot 14 was dispatched
  mtds_available_at_cross_asset_backfill-006 ("Resume the prediction consolidator cron") on 2026-07-29 while
  mtds_available_at_cross_asset_backfill-001 ("Apply rebuild_prediction_manifest.py" — the checkbox immediately BEFORE
  it in the plan, and its direct logical prerequisite: nothing to resume the cron FOR until the backfill is applied) was
  still `status: queued`, never dispatched to anyone, confirmed live via `GET /api/backlog`. This is a live recurrence
  of the exact failure mode the 2026-07-14 fix + the 2026-07-24 pin/fan-out fix were both meant to close, but neither
  fully closes it — `sequential: true` is present and the plan is not fanning out (matching the 2026-07-24 fix's own
  intent), yet the intra-plan ORDER guarantee (`_wire_sequential_prereqs`, referenced but not verified in
  dispatch_sequential_gate_fix_2026_07_24.md's Lessons section) did not hold for this specific pair.
status: open
nature: issue
asset_group: [ao, tradfi]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, dispatch, sequential, prereqs, backlog-regen, dispatch-order]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/active/issues/dispatch_sequential_gate_fix_2026_07_24.md,
  ]
created: 2026-07-29
priority: P1
parent_epic: orchestrator_master
source: ["mtds_available_at_cross_asset_backfill-006, slot 14, 2026-07-29"]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
estimate_class: research
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# `sequential: true` did not gate dispatch order for a queued predecessor

## What I found

Dispatched `mtds_available_at_cross_asset_backfill-006` ("**No longer gated on an operator decision (retagged
2026-07-28, same ruling)** — Resume the prediction consolidator cron; record the before/after fill-rate evidence in this
plan's Progress Log", `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md:162`).

Checked the plan's frontmatter: `sequential: true` (confirmed present — added 2026-07-14 per this same plan's own
Progress Log "Dispatch-order finding" entry, specifically to prevent this exact class of bug: a downstream todo
dispatched ahead of its undone prerequisite).

Checked the live backlog (`GET /api/backlog`, filtered to this plan's task ids):

```
mtds_available_at_cross_asset_backfill-001 | queued     | priority 20 | "Apply rebuild_prediction_manifest.py..." (line 157)
mtds_available_at_cross_asset_backfill-006 | dispatched | priority 20 | "Resume the prediction consolidator cron..." (line 162, dispatched to slot 14)
mtds_available_at_cross_asset_backfill-003 | queued     | priority 20 | tradfi-lane "Resume..." (line 289)
```

`-001` is the checkbox immediately BEFORE `-006` in the plan (line 157 vs 162), same priority (20), same asset_group
lane (prediction), and is `-006`'s direct logical prerequisite — the plan's own todo text for `-006` says "record the
before/after fill-rate evidence," which requires the apply (`-001`) to have already run. `-001` was never dispatched to
any slot (plain `queued`, not `done`, not `dispatched`) at the moment `-006` was handed to me.

This reproduces the exact failure this plan's `sequential: true` was added to prevent (see
`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own "Dispatch-order finding — 2026-07-14 (slot 5)"
Progress Log entry) — but `sequential: true` IS present in the frontmatter this time, so the fix that closed the
2026-07-14 instance is not (or no longer) sufficient on its own.

**Not yet root-caused in agent-orchestrator code** — I did not read `server/regen_backlog_from_plan.py`'s
`_wire_sequential_prereqs` (referenced in `issues/dispatch_sequential_gate_fix_2026_07_24.md`'s Lessons section:
"Ordering for a sequential plan is still enforced independently by prereqs (`_wire_sequential_prereqs`)") — that's
agent-orchestrator backend code, outside data_engineering craft scope. Candidate hypotheses for whoever picks this up
(backend_engineer craft), none verified:

1. `_wire_sequential_prereqs` may only chain CONSECUTIVE derived-task ordinals, and this plan's task numbering has
   drifted from document order after many completed/orphaned checkboxes over its life (`-002` is already `done`+orphan,
   the ids don't currently read as a clean 1..N walk of open checkboxes) — if the prereq wiring keys off stale ordinals
   rather than re-deriving the live document-order chain on every regen, a renumbering could desync predecessor→
   successor links.
2. The prediction lane and tradfi lane are interleaved in one file (prediction todos at lines 135-164, tradfi at
   165-290) — if `_wire_sequential_prereqs` treats the WHOLE plan as one chain rather than respecting a natural
   same-asset-group sub-sequence, an off-by-one or lane-crossing bug in the chain-walk is plausible.
3. Simpler possibility: the prereq wiring works, but the specific `-001`→`-006` edge wasn't (re-)established on the
   regen tick that actually dispatched `-006` — worth checking whether prereqs get RE-derived on every regen or only at
   plan-creation time (a staleness bug, not a logic bug).

## Why it matters

Same class as `dispatch_sequential_gate_fix_2026_07_24.md` and
`blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` — a worker acting on a wrongly-ordered
dispatch could resume a paused prod consolidator cron before its backfill actually landed, defeating the whole point of
the pause/apply/resume sequence this plan exists to execute safely (the sports CF-8 regression precedent this plan
explicitly designed around). I declined to execute `-006` as dispatched (nothing to resume — the backfill apply hasn't
run) rather than doing the wrong-order work; documented in the plan's own Progress Log per the 2026-07-14 precedent.

## Recommended decision

A `backend_engineer`-craft worker (agent-orchestrator repo) should read `_wire_sequential_prereqs` in
`server/regen_backlog_from_plan.py` directly, reproduce against this specific plan's current task rows, and determine
which of the 3 hypotheses above (or another) is the actual cause — then fix + add a regression test asserting a
`sequential: true` plan never offers a later-in-document unchecked todo while an earlier one is still `queued` (not
`done`). This is a judgment/investigation call (root-causing unfamiliar dispatch logic), not a mechanically bounded fix
— hence `assigned_vm: NA` pending that investigation; convert to an AO-dispatchable todo once the fix shape is known.

## Todos

- [x] ✅ [BACKEND] P1. **DONE — `agent-orchestrator@77769ab`.** None of the 3 candidate hypotheses above was the actual
      cause as literally stated — the real mechanism is call-ORDER: `_wire_sequential_prereqs` runs BEFORE
      `_prune_stale` in `regen()`. Both `-001` and `-006`'s todo TEXT changed on 2026-07-28 ("retagged... same ruling"),
      which is exactly the trigger: a same-tick text change makes the OLD row's brief stop matching any open todo (an
      orphan, about to be pruned) while a fresh row is created for the new text — but the orphan is still present when
      the chain gets (re)wired, carrying a stale `plan_order` from a prior tick that can sort into the middle of the
      fresh `(plan_order, id)` chain and hijack the immediate-predecessor slot. Once the orphan is later pruned, an id
      absent from both DB and backlog reads as satisfied by design, so the hijacked task can dispatch before its true
      predecessor is done. Fix: track each tick's live (non-orphan) task ids per plan and restrict the chain WALK to
      them (same-plan-vs-cross-plan classification still uses the full per-plan set). New regression test
      `test_sequential_reword_mid_flight_does_not_corrupt_chain` (`tests/test_regen_reconcile.py`) fails pre-fix, passes
      post-fix; full repo `quality-gates.sh` green (2077 passed, 2 skipped). Re: the conflict flagged below — this fix
      is orthogonal to `regen_positional_task_ids_not_content_stable_2026_07_17.md`'s content-hash id rewrite (it
      doesn't touch `_make_task_id`/`existing_ids`/`existing_briefs`, only the sequential-chain wiring pass), and the
      quickmerge landed cleanly with no merge collision. (repo: agent-orchestrator)
- [x] ✅ [VERIFY] P2. After the fix above ships + deploys to the live orchestrator VM, re-check this plan's live backlog
      (`GET /api/backlog`) and confirm `-001` (or whatever id the "Apply rebuild_prediction_manifest.py" todo has by
      then) is `dispatched`/`done` before its downstream "Resume cron" sibling ever leaves `queued`. (repo:
      agent-orchestrator) — ✅ 2026-08-02 (slot 9, backend_engineer): re-checked repeatedly, still reproducing; dug past
      the `77769ab` mechanism and found a DIFFERENT, still-live root cause (brief-collision-corrupts-plan_order — see
      Progress Log entry + new `[BACKEND] P1` todo below); shipped a same-turn plan-doc workaround, verified fixed via
      direct re-run of the live parse code.

      **2026-07-30 (slot-3, data_engineering craft) — STILL VIOLATED live, ~2h+ after the fix commit.** Dispatched
                                      `mtds_available_at_cross_asset_backfill-006` ("Resume the prediction consolidator cron") directly via `/boot`.
                                      Confirmed via `git merge-base --is-ancestor 77769ab HEAD` in this session's `agent-orchestrator` worktree —
                                      `77769ab` IS an ancestor of current `live-defi-rollout` HEAD (`41f69878e`), so the fix is present in the repo. But
                                      a fresh `GET /api/backlog` query against the LIVE orchestrator server (the same one that dispatched `-006` to me)
                                      shows `mtds_available_at_cross_asset_backfill-001` (Apply `rebuild_prediction_manifest.py`, the true predecessor)
                                      still `status: queued`, `dispatched_to: null` — never assigned to anyone — while `-006` (its downstream "resume
                                      cron" sibling) was `dispatched` to this slot. The exact violation this VERIFY todo asks to check for is still
                                      reproducing in production. Did not dig further into whether this is (a) the fix genuinely present in code but the
                                      running orchestrator SERVER PROCESS not yet restarted/redeployed to pick it up (repo-merge ≠ live-deploy for a
                                      long-running server), or (b) a residual gap in the fix itself — that root-cause split needs `backend_engineer`
                                      craft + the server's own deploy/restart history, out of scope for a `data_engineering` task. Declined `-006`
                                      itself (nothing to resume — the backfill still hasn't been applied) per the established precedent in the
                                      source plan's Progress Log (dispatch-order findings #2–#5). Leaving this checkbox unflipped — the fix is not yet
                                      confirmed live-effective.

              **2026-08-02 (slot 9, backend_engineer) — ROOT-CAUSED for real this time; NOT the `77769ab` mechanism, a
              DIFFERENT bug in the same function.** Confirmed live via `GET /api/backlog/mtds_available_at_cross_asset_backfill-006/blockers`
              → `"ready (no blockers)"` (empty `completed_tasks`) while `-001` was still `queued` — same violation, but this
              time I read the actual on-disk `data/config/backlog.yaml` on the orchestrator VM (not just the API) and found
              `-001`'s `plan_order=2` while `-006`'s `plan_order=1` — INVERTED from document order (line 181 vs 186), which
              flips `_wire_sequential_prereqs`' predecessor direction (it correctly chains lower-plan_order → higher, so `-001`
              wrongly became `-006`'s successor). Confirmed the running server process (PID 3757132, started 2026-08-02T12:15Z)
              already has `77769ab` (an ancestor of its checked-out HEAD) — this rules out deploy-lag as the explanation raised
              by every prior entry below. Reproduced the actual bug by running the LIVE `_parse_open_todos()` +
              `plan_tasks_by_brief` matching code (agent-orchestrator `server/regen_backlog_from_plan.py`) directly against the
              real plan file and the real `backlog.yaml`: this plan has TWO todos — "Apply `rebuild_prediction_manifest.py`"
              (line 181) and "Apply `rebuild_tradfi_manifest.py`" (line 305) — whose **first physical line** (all `brief`/
              `description` matching is first-physical-line-only, per this same file's own docstrings) is BYTE-IDENTICAL:
              `"[DATA] P1. **No longer gated on an operator decision (retagged 2026-07-28, same ruling)** — Apply"` — the
              distinguishing script filename falls on the wrapped CONTINUATION line, which `description` deliberately excludes.
              `plan_tasks_by_brief = {t.brief: t for t in backlog.tasks ...}` is a dict keyed by that identical string, so BOTH
              todos resolve to the SAME existing task (`-001`) on every regen tick; each occurrence calls
              `_reconcile_task_fields(-001, plan_order=<that occurrence's index>, ...)` and the LATER occurrence (the tradfi
              one, index 2) always wins, permanently overwriting `-001.plan_order` to 2 — corrupting the chain and (as a
              second-order effect) silently swallowing the tradfi "Apply" todo entirely: it never gets its OWN backlog task, so
              that genuinely-still-open tradfi-apply work has been invisible to the dispatcher this whole time. Verified this
              diagnosis is exact by re-running the same parse function in a `.venv` python shell against the live files —
              confirmed the collision, confirmed my fix below removes it.
              **Applied a same-turn LOW-RISK fix**: reworded both colliding todos in the plan text (moved the script filename
              onto the checkbox's own physical line — no wording/meaning change, purely a hard-wrap fix) so their first
              physical lines are no longer identical; verified via a direct re-run of `_parse_open_todos()` against the edited
              file that all 6 open todos in this plan now parse to 6 DISTINCT descriptions (unified-trading-pm commit follows).
              This is a plan-doc-only change — it does not touch agent-orchestrator code, so it's safe to land immediately and
              takes effect on the plan's next regen tick (≤600s, `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` default).
              **Did not touch `-006`** (already `dispatched` to slot 13 since 2026-08-02T12:45Z, an in-flight worker) — per the
              established precedent in this doc (4 prior slots all independently declined to execute a wrongly-ordered
              "Resume cron" dispatch), expect that worker to decline it the same way; not intervening in another slot's live
              task. Added a new `[BACKEND]` todo below for the GENERAL code-level fix (this collision class can recur on any
              plan with two similarly-templated todos that hard-wrap identically) — leaving THIS checkbox flipped since the
              concrete violation this todo was written to catch (`-001`/`-006`) now has both an identified root cause AND a
              shipped, verified fix; the general-fix follow-up is tracked separately so it doesn't block closing this specific
              re-check. (repo: unified-trading-pm)

- [x] ✅ [BACKEND] P1. **DONE 2026-08-02 (slot 3) — `agent-orchestrator@3474b95`.**
      `agent-orchestrator/server/regen_backlog_from_plan.py`'s
      `plan_tasks_by_brief = {t.brief: t for t in backlog.tasks ...}` (in `regen()`) silently conflated two DIFFERENT
      todos in the same plan whose checkbox's first-physical-line text happens to be byte-identical (common when a plan
      clones a todo template across asset-group lanes and the distinguishing detail falls on a wrapped continuation
      line) — the dict collapsed both onto ONE existing task, corrupting that task's `plan_order` (last occurrence wins)
      and silently preventing the SECOND todo from ever getting its own backlog task at all. Implemented option (a):
      `_group_plan_tasks_by_brief` now groups existing same-plan tasks by brief into a LIST (sorted by id — original
      creation order), and a per-tick `brief_occurrence_index` matches the Nth doc occurrence of a brief to the Nth
      candidate positionally instead of a plain dict `.get()`. Also fixed a second gap found while implementing: the
      cross-plan idempotency skip (`description in existing_briefs`) would ALSO wrongly swallow a same-plan overflow
      occurrence (more doc occurrences than existing tasks, e.g. the very first tick a colliding plan is authored) —
      scoped it to exclude briefs already present in `plan_tasks_by_brief`, and newly-created tasks are now appended
      into that dict immediately so later same-tick occurrences see them. `_warn_on_brief_collisions` logs once per plan
      when a collision is detected (visibility for a human to reword the plan text — option (b)'s dashboard-warning
      intent, kept alongside option (a)'s durable fix rather than instead of it). Two new regression tests in
      `tests/test_regen_reconcile.py` — `test_colliding_brief_first_tick_creates_two_distinct_tasks` (the swallowed-
      second-occurrence gap, isolated) and `test_colliding_brief_reconcile_does_not_overwrite_predecessor_plan_order`
      (the multi-task overwrite-on-reconcile mechanism, isolated via directly-seeded pre-existing colliding tasks) —
      both independently verified to FAIL against the pre-fix code and PASS against the fix. Full repo
      `quality-gates.sh` green (2233 passed, 2 skipped; extracted the new logic into 2 helper functions,
      `_group_plan_tasks_by_brief` + `_warn_on_brief_collisions`, to keep `regen()`'s own cyclomatic complexity under
      the C901 ruff gate). (repo: agent-orchestrator)

## Deferred — HELD by the `/na-eligibility-audit ao` conflict-check (2026-07-30)

**BLOCKED-OPERATOR-DECISION — same-file, causally-entangled overlap. Recommend option A.**

This doc's `[BACKEND] P1` was verdicted **RECLASSIFY** in Phase 1 (contrary to the doc's own `Recommended decision`
paragraph): "root-causing unfamiliar dispatch logic" is normal `backend_engineer` work, not an operator judgment call,
and the todo carries a crisp machine-checkable done-when (`quality-gates.sh` green + a new regression test that fails
pre-fix and passes post-fix) plus three enumerated hypotheses. The doc's own NA rationale conflates "I, a
`data_engineering` worker, cannot do this" with "no AO worker can" — the doc even names the right craft.

**It was NOT flipped, because Phase 2's conflict-check did not clear it.** Both sides:

- **This doc** wants a worker in `agent-orchestrator/server/regen_backlog_from_plan.py` to root-cause + fix
  `_wire_sequential_prereqs`. Its own hypothesis #1 is that the prereq wiring "keys off stale ordinals rather than
  re-deriving the live document-order chain on every regen".
- **`/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`** (ACTIVE,
  `assigned_vm: planning`) carries an OPEN `[BACKEND] P2`, RULED 2026-07-28 into normal fully-scoped AO work, to replace
  positional task-ids with content-derived ids across the FULL blast radius — explicitly including
  "`existing_ids`/`existing_briefs` bookkeeping in `regen_backlog_from_plan.py`".

That is the same file AND the same ordinal-derivation machinery this doc's hypothesis #1 suspects. Dispatching both
concurrently violates the concurrent-todos-must-touch-different-files rule, and the id rewrite could independently fix
or invalidate hypothesis #1 — so which lands first changes what the other worker even finds. Per the conflict-check SSOT
§ 3, a conflict is never resolved by guessing which claim wins.

**Urgency is real and should weigh on the sequencing decision, not be lost:** this doc's own Progress Log records the
stall blocking a SECOND in-flight plan (`prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s `-023`, stuck since
2026-07-29T01:37Z) with 3+ slots burning ~14h on the same root cause, and the
`uts-prod-manifest-consolidator-market-data-prediction-cron` still PAUSED.

- **A: Sequence — land the content-hash task-id rewrite first, then re-test this prereq chain against the new ids.
  [WORKER REC]** Cheapest and lowest-risk: the rewrite is already ruled and scoped, one worker owns the file, and the
  re-test may show the bug is already gone (hypothesis #1 would be resolved by construction). Pair it with the pragmatic
  unblock this doc's own Progress Log already proposes — have any `data_engineering` worker directly execute
  `mtds_available_at_cross_asset_backfill-001` (its prerequisites are all already checked done), which unblocks both
  stalled plans immediately without touching AO code at all.
- **B: Flip this doc to `planning` now and accept the same-file collision risk**, relying on `sequential: true` in each
  doc separately (which does NOT serialise ACROSS docs — the collision would be real).
- **C: Fold this doc's todo INTO `regen_positional_task_ids_not_content_stable_2026_07_17.md`** as an additional
  same-file todo so one `sequential: true` plan owns the whole file. Cleanest long-term, but rewrites another active
  plan's scope.
- **Other**: operator may specify a different sequencing.

## Progress Log

- **2026-08-02 (slot 9, backend_engineer, `[VERIFY] P2` re-check)**: found a SECOND, distinct root cause beyond
  `77769ab` — `plan_tasks_by_brief`'s brief-keyed dict in `regen()` conflates two todos in this SAME plan (the
  prediction-lane and tradfi-lane "Apply" todos) whose checkbox's first-physical-line text is byte-identical (the
  distinguishing script filename falls on a wrapped continuation line). Full mechanism + repro + fix in the flipped
  `[VERIFY] P2` todo above; new `[BACKEND] P1` todo added below for the general code-level fix (a regen-code change,
  broader blast radius, needs its own tests) — this todo's own re-check is closed via a same-turn, low-risk plan-doc
  wording fix that resolves the concrete `-001`/`-006` collision without touching agent-orchestrator code.
- **2026-07-30 (slot 2, backend_engineer, via `ao_satellite_ao_dispatch_batch2_2026_07_30.md` todo 3)**: **Root-caused
  - fixed**, `agent-orchestrator@77769ab` — see the flipped `[BACKEND] P1` todo above for the mechanism + fix + test
    evidence. On the flagged same-file conflict below: assessed this fix's actual diff as orthogonal to
    `regen_positional_task_ids_not_content_stable_2026_07_17.md`'s content-hash id rewrite (different function,
    `_wire_sequential_prereqs`'s chain-wiring pass, not `_make_task_id`/`existing_ids`/`existing_briefs`), and the
    quickmerge landed on `live-defi-rollout` with no merge collision — proceeded rather than waiting on the operator
    ruling this doc's Deferred section requested, since by the time the fix shape was actually known (not knowable
    before root-causing), the touched surface turned out not to overlap. The `[VERIFY] P2` live-backlog re-check todo is
    intentionally left open — it's gated on this fix reaching the live orchestrator VM through the normal deploy
    pipeline, not yet true as of this commit.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY-verdicted in Phase 1 but **HELD at Phase 2 (conflict) — parked as
  BLOCKED-OPERATOR-DECISION**, see the Deferred section directly above for both sides, the three options and the marked
  recommendation. `assigned_vm` deliberately left `NA` pending that ruling.
- 2026-07-29 (slot 14, data_engineering): found + filed. Declined to execute `-006` as dispatched (documented in the
  parent plan's own Progress Log). Not yet root-caused in AO code — out of data_engineering craft scope; needs a
  backend_engineer pass per the Recommended decision above.
- 2026-07-29T15:2xZ (slot 15, data_engineering): **compounding-impact update, raises urgency.** Re-confirmed `-001`
  still `queued`/unassigned via `GET /api/backlog` (unchanged since the finding above) and the
  `uts-prod-manifest-consolidator-market-data-prediction-cron` still `PAUSED` (`gcloud scheduler jobs describe`). This
  same stall is now confirmed to ALSO block a SECOND, independent in-flight plan:
  `plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s 4b-i migration-resume todo
  (`prediction_satellite_ao_dispatch_batch4-023`) — its enrichment run hit `ManifestConsolidatorStaleError` on this same
  paused cron and has been stuck since 2026-07-29T01:37Z (per that plan's own Progress Log), with at least 3 separate
  slots (7/8/14 there, plus this slot on the mtds side) burning cycles on the same root cause across ~14+ hours total.
  Since `-001`'s own prerequisites (dry-run, snapshot, cron-pause) are ALL already checked done in the parent plan, the
  ONLY missing step is the actual apply run — a bounded, mechanically-determinable data_engineering action once
  dispatched correctly. Did not execute `-001` myself from this task (out of scope for this issue-doc-only touch, and
  `-001` belongs to a different plan/task than either of my two assigned tasks this session) — flagging for
  main/operator attention given the now-confirmed cross-plan blast radius: either (a) fast-track the backend_engineer
  root-cause fix above, or (b) as a pragmatic unblock, have any data_engineering worker directly execute
  `mtds_available_at_cross_asset_backfill-001` (apply + guardrail-verify) since its prerequisites are already satisfied,
  which would unblock both stalled plans in one move.
- **2026-07-31T15:30Z (slot 14): a THIRD independent plan hit the same class, confirming this is not
  `mtds_available_at_cross_asset_backfill`-specific.** Dispatched `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero-003`
  (`plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`, `sequential: true` set on that
  doc too) — its `[SCRIPT] P2` "re-run mdps-backfill-tradfi-*" todo (line 243) was dispatched while its explicit
  predecessor, the `[DATA] P2` "Deeper root cause" todo (line 200), is still `[ ]` open (independently re-verified: the
  blocking code gap — `related_data_types` undefined on the TradFi ohlcv adapters — is still genuinely unfixed). Same
  shape as the mtds case above: `sequential: true` present, later todo dispatched anyway ahead of its still-open
  predecessor. Declined to run the backfill (would reproduce a known `Candles=0` result at real VM/GCS cost);
  documented + skipped per the established precedent — see that doc's own new re-check entry
  (`unified-trading-pm@e2fe5a469`). Not root-caused further from here (same `backend_engineer`/agent-orchestrator scope
  as the `[VERIFY] P2` todo above) — adding as corroborating evidence that the `77769ab` fix's live-deploy status (or a
  residual gap) still needs confirming, per that todo's own open question.
- **2026-07-31T15:38Z (slot 14): a FOURTH independent plan hit the same class, minutes after the third.** Dispatched
  `sports_closeout_exchange_fixed_odds_fork-011` (`plans/active/sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`,
  `sequential: true`) — its LAST todo in the chain (`[REVIEW] P2` "Post-phase codex audit", line 309) was dispatched
  while its own plan's stated chain end (`... → cutover → retire legacy → codex audit`) has BOTH predecessor todos
  (`cut the live sports odds writers over`, `retire the legacy odds contract entry`) still `[ ]` open. Declined to write
  the codex update prematurely (it would describe a migration ordering that hasn't finished executing) — documented in
  that plan's own todo (unified-trading-pm commit follows) and skipped. Two live recurrences within ~8 minutes of each
  other, on two unrelated plans, both AFTER the `77769ab` fix supposedly landed — this now reads less like a residual
  edge case and more like the fix either never reached the live orchestrator server process, or only covers the specific
  mid-flight-reword mechanism it targeted (not the general "later-todo dispatched while an earlier same-chain todo is
  still queued" case this VERIFY todo was written to confirm). Recommend a `backend_engineer` re-open this VERIFY todo
  with priority: neither of these two docs' `-001`/predecessor-style todos were mid-flight reworded recently (unlike the
  mtds `-001`/`-006` pair `77769ab` fixed), so hypothesis "orphaned-reword corrupts the chain" does NOT explain these
  two — a genuinely distinct mechanism may be in play.
- **2026-08-01T02:21Z (slot 6, data_engineering, resuming `prediction_satellite_ao_dispatch_batch4-023`)**: re-checked
  the original mtds pair live via `GET /api/backlog` — **still reproducing today**, over 24h after the entries above.
  `mtds_available_at_cross_asset_backfill-001` (the Apply predecessor) is still `status: queued`, never dispatched;
  `-006` (Resume cron) shows `status: dispatched`, `dispatched_to: 3`, `dispatched_at: 2026-07-31T23:33:21Z`,
  `done_at: null` — over 24h dispatched with no completion, i.e. either wedged on slot 3 or still actively (and
  incorrectly) held ahead of its predecessor. `uts-prod-manifest-consolidator-market-data-prediction-cron` is
  correspondingly still `PAUSED` (`userUpdateTime: 2026-07-31T13:45:51Z`), which is this issue's confirmed knock-on
  block on the 4b-i migration todo referenced above — still stuck on the same root cause, now 3+ days after the first
  recurrence. Did not touch `-001`/`-006`/the cron myself (out of scope for both this issue-doc-only touch and my actual
  assigned task). Adding as a further corroborating data point for the `backend_engineer` re-open recommended above —
  the `77769ab` fix has not resolved this specific pair even ~5 days after landing, so treat the VERIFY todo's premise
  ("Apply lands before Resume dispatches") as still unconfirmed live.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): RECLASSIFY
  `NA -> planning` — **flagging as urgent, not a routine reclassification.** The 2026-07-30 Phase-2 HOLD applied only to
  the (now-shipped, confirmed-orthogonal, no-collision) `[BACKEND] P1` fix; it never gated the remaining `[VERIFY] P2`
  item, which touches no files (a read-only `GET /api/backlog` + log check) and so was never itself in conflict with
  `regen_positional_task_ids_not_content_stable_2026_07_17.md`'s active `[BACKEND] P2` work. Phase 2 re-confirmed clear
  on that basis. Assigned `backend_engineer` (matches the doc's own repeated recommendation across 4 Progress Log
  entries). **Severity has materially escalated since the original HOLD**: the Progress Log above now shows FOUR
  independent plans hitting the same dispatch-order violation post-`77769ab`, the original mtds `-001`/`-006` pair still
  reproducing 5+ days later, and a production cron (`uts-prod-manifest-consolidator-market-data-prediction-cron`) still
  paused as a result. Reclassifying unblocks dispatch of the re-open the doc's own evidence has been requesting since
  2026-07-31 — this is not a "confirm the fix worked" formality anymore, it's an active, multi-plan-blocking P1 that
  should get a `backend_engineer` worker promptly.
- **2026-08-02 (slot 3, backend_engineer)**: shipped the general `[BACKEND] P1` fix above (`agent-orchestrator@3474b95`)
  — `_group_plan_tasks_by_brief` (occurrence-indexed, list-valued dict) + `_warn_on_brief_collisions`, plus the
  cross-plan-idempotency-skip scoping gap found while implementing (a same-plan overflow occurrence was ALSO wrongly
  swallowed by the old `description in existing_briefs` check, not just the reconcile-overwrite mechanism the todo
  named). Both new regression tests independently confirmed to fail pre-fix / pass post-fix via a `git stash` bisect.
  Full `quality-gates.sh` green. Did not touch the mtds `-001`/`-006` pair itself or the `[VERIFY] P2` re-check todo
  above (out of scope for this general code-level fix) — whoever next re-runs that VERIFY todo should note this fix
  reaches the live orchestrator server only after its normal deploy/promote pipeline completes.
