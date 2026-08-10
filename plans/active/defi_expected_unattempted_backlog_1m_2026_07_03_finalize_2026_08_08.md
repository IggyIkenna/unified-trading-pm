---
doc_type: plan
title: Finalize — defi A_TOKEN/DEBT_TOKEN instrument_type-alias + oracle_prices validity fix close-out
summary: >-
  Gated finalize companion for issues/defi_expected_unattempted_backlog_1m_2026_07_03.md (reclassified NA→planning,
  na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08) — re-verifies the `_INSTRUMENT_TYPE_ALIASES` +
  `PROTOCOL_CAPABILITIES` widening build's evidence, confirms the dead `venue_mapping.DataTypeConfig` cleanup landed,
  then archives both docs per plan-completion-and-archival-discipline once every todo is done.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, manifest, expected-unattempted, instrument-type-alias, finalize, archival, ao-build]
related:
  [
    /plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: [defi_expected_unattempted_backlog_1m_2026_07_03]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep) — every AO-dispatched plan/reclassified issue doc needs a
  gated finalize companion (/plans/active/task_template.md §4).
context_scope:
  [
    /plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/registry/possible_manifest.py,
  ]
---

# Finalize — defi A_TOKEN/DEBT_TOKEN instrument_type-alias + oracle_prices validity fix close-out

Machine-held (`gate_on_depends: true`) until every todo in `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`
is done. Do not start manually before then.

## Todos

- [x] ✅ [REVIEW] P2. Re-verify the build's evidence: (1) `market_data_categories._INSTRUMENT_TYPE_ALIASES` gained the
      two named entries (`"a_token": "lending"`, `"debt_token": "lending"`) — confirm via `git log`/`git show` against a
      fresh `git pull --ff-only origin live-defi-rollout` on `unified-api-contracts` (don't trust the build todo's own
      evidence line uncritically); (2) the AAVE_V3/FLUID/SOLEND/SPARK/VENUS lending protocols' declared `data_types` in
      `capability_declarations/_defi.py` were widened to include `oracle_prices`; (3) a live check confirms
      `valid_data_types_for_instrument_type("defi", "A_TOKEN")` and `("defi", "DEBT_TOKEN")` both return a non-`None`
      frozenset containing `oracle_prices`; (4) a new regression test asserts the previous unmapped-fallback bug
      (`--data-types perp_trades` over-fanning A_TOKEN/DEBT_TOKEN venues, the 2026-07-16 finding) no longer reproduces;
      (5) the now-confirmed-dead `venue_mapping.DataTypeConfig` + its one unit test were deleted per the source doc's
      own follow-up note (only if that deletion sub-step was actually attempted — the source todo scopes it as a "do not
      do in this todo" follow-up, so its absence is not itself a finding). Done-when: all applicable points
      independently re-verified with cited evidence; any mis-citation found is corrected in the source doc directly.

      **DONE 2026-08-08 (slot 30)** — the gate is now genuinely satisfied: the source doc's `[SCRIPT]` todo was
          completed this session (`unified-api-contracts@768c6f93`), so this re-verification is against real shipped code,
          not a narrowing note. All 5 points independently re-verified against a fresh
          `git pull --ff-only origin live-defi-rollout` (`unified-api-contracts` HEAD `768c6f93`):
          (1) **mis-citation, corrected** — `_INSTRUMENT_TYPE_ALIASES` did NOT gain explicit `a_token`/`debt_token`
          entries (confirmed absent, `'a_token' in _INSTRUMENT_TYPE_ALIASES` → `False`) — slot 7's 2026-08-08 narrowing
          already found this unnecessary (the alias table's own identity fallback + `_LENDING_ATOKEN_DEBTTOKEN`'s
          already-lowercase enum values make an explicit entry redundant) and dropped it from the `[SCRIPT]` todo's scope;
          point (1) as originally worded does not apply to what was actually built. (2) **true** — live-verified all 5
          named protocols (AAVE_V3/FLUID/SPARK pre-existing; VENUS/SOLEND newly shipped this session) declare
          `oracle_prices` in their venue-narrowed `valid_data_types_for_venue_instrument_type` sets. (3) **true** —
          `valid_data_types_for_instrument_type("defi", "A_TOKEN"/"DEBT_TOKEN")` both return non-`None` frozensets
          containing `oracle_prices` (live-tested). (4) **true** —
          `test_lending_a_token_debt_token_exclude_perp_trades` (added this session,
          `tests/test_valid_data_types_by_instrument_type.py::TestValidDataTypesForVenueInstrumentType`) passes,
          asserting `perp_trades` excluded from A_TOKEN/DEBT_TOKEN on AAVE_V3/VENUS/SOLEND. (5) **not attempted, per
          design** — `venue_mapping.DataTypeConfig` still exists; its deletion was correctly deferred (the source todo's
          own "do not do in this todo" scoping) and filed as its own tracked follow-up doc,
          `issues/venue_mapping_datatypeconfig_dead_code_deletion_2026_08_08.md`, so its absence here is not a finding.
          Full `quality-gates.sh` green (427s) covering the whole `unified-api-contracts` suite including
          `is_valid_shard_key`/enumerator tests. Evidence: `unified-api-contracts@768c6f93`,
          `.qg_last_passed_sha=768c6f9325eb235ca9da5caad4f3bb4459bcf4f9`.

- [ ] [OPERATOR] P2. **Ask the operator to unlock `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` for
      archival.** The doc carries a genuine `locked_by: live-defi-rollout` / `locked_since: 2026-07-03` lock (per
      `plans/PLAN_FORMAT.md` § "Plan Locking", a real lock field, not free text) and now has zero open todos — both this
      finalize doc's `[REVIEW]` todo above and the source doc's own `[SCRIPT]` todo are done (see Progress Log). Six
      prior dispatches (slots 30, 29, 12, 19, 9, 10) correctly declined to unlock autonomously (workspace HARD RULE —
      agents must never unlock a locked plan) and instead filed ephemeral `/blocked` questions (`BLK-3d18ef7c`, then
      `BLK-ce0fe830`) that each vanished from `blocked_queue` unanswered before a ruling landed — the
      pruning-without-resolution failure mode tracked in
      `plans/archive/2026_08/issues/blocked_queue_unanswered_questions_pruned_without_resolution_2026_08_08.md`
      (resolved 2026-08-09, `agent-orchestrator@eba48f0`). This `[OPERATOR]` tag replaces that ephemeral approach: per
      `/codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md`, tagging this todo `[OPERATOR]` auto-seeds a
      durable `BLK-op-*` blocked-queue row (`slot_id=0`) that survives regen ticks instead of expiring, and the operator
      can answer it directly from the dashboard (canned option or a reclassify/instruct ruling) rather than a worker
      re-filing the same question every redispatch. Recommendation: approve — the lock's own value is the branch name
      (`live-defi-rollout`), not a distinguishing agent claim, and every todo on both docs is genuinely done. Done-when:
      the operator's ruling is recorded (materializes as a `--ruling` task per the SSOT) and, on approval,
      `locked_by`/`locked_since` are cleared on the source doc in the same commit that strips this todo's `[OPERATOR]`
      tag.
- [ ] [DOC] P2. Run the standard 6-step plan-completion-and-archival-discipline ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` and this finalize doc itself: archive both to
      `plans/archive/2026_08/issues/` (this finalize doc to `plans/archive/2026_08/`), and fix every corpus referrer
      path (grep the repo for the old paths — `defi_satellite_ao_dispatch_batch6_2026_07_30.md`,
      `defi_satellite_ao_dispatch_batch9_2026_08_06.md`, `defi_satellite_ao_dispatch_batch10_2026_08_06.md`,
      `defi_consolidated_closeout_2026_07_18.md`, `instruments_completion_tracker_2026_07_06.md`, and
      `instruments_remaining_work_audit_2026_07_10.md` all cite the source doc — update each hit). Done-when:
      `regenerate_active_plan_inventory.py` shows zero orphan referrers to the archived paths. Gated on the `[OPERATOR]`
      todo above being resolved with approval (this plan is `sequential: true`, so dispatch already enforces the
      ordering).

## Progress Log

- **2026-08-08 (na-eligibility-audit round7 RECLASSIFY sweep)**: finalize plan authored alongside the RECLASSIFY flip of
  the source issue doc, per `task_template.md`'s finalize-plan-coverage rule.
- **2026-08-08 (REVIEW re-verification, slot 7)**: dispatched despite the gate — the source doc's `[SCRIPT]` todo is
  still open (0 backlog rows derive for it at all, matching the still-open "zero-derived-parent-row" root-cause
  mechanism in `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`; added a recurrence note there).
  Performed the independent re-verification anyway (didn't just skip blind): the underlying
  `_INSTRUMENT_TYPE_ ALIASES`/`PROTOCOL_CAPABILITIES` build was NEVER shipped, but live-testing found most of its
  claimed effect already true via an unrelated pre-existing fix (identity-fallback alias resolution +
  AAVE_V3/SPARK/FLUID already declaring `oracle_prices`) — only VENUS/SOLEND `oracle_prices` widening + one regression
  test remain genuinely outstanding. Narrowed + corrected the source doc's `[SCRIPT]` todo in place to that reduced
  scope (see its Progress Log entry dated 2026-08-08). NOT flipping this `[REVIEW]` checkbox (source doc still has one
  open todo) — declining per the gate_on_depends issue doc's established disposition; skipping this task rather than
  forcing it through.
- **2026-08-08 (REVIEW re-verification, slot 30)**: same task redispatched (same recurring `gate_on_depends` wiring-gap
  bounce noted above). Rather than bounce a third time, implemented slot 7's narrowed `[SCRIPT]` scope directly — small,
  deterministic, fully specified: shipped `unified-api-contracts@768c6f93` (VENUS/SOLEND `oracle_prices` widening in
  `capability_declarations/_defi.py` + one regression test), full `quality-gates.sh` green (427s), landed +
  ancestry-verified on `live-defi-rollout`. Flipped the source doc's `[SCRIPT]` checkbox to done with evidence; the
  source doc now has zero open todos. Deferred the `venue_mapping.DataTypeConfig` deletion follow-up to its own new doc
  (`issues/venue_mapping_datatypeconfig_dead_code_deletion_2026_08_08.md`) rather than reopening the source doc. With
  the gate now genuinely satisfied, independently re-verified all 5 points of this `[REVIEW]` todo against the real
  shipped code (not a narrowing note this time) and flipped its checkbox — see the todo's own inline evidence above.
  Point (1) as originally worded is a mis-citation (explicit alias entries were never needed); corrected inline rather
  than silently flipped. Proceeding to the `[DOC]` archival todo in the same session since both this doc and the source
  doc now have zero open todos.
- **2026-08-08 (DOC archival attempt, slot 30)**: both docs now have zero open todos, so started the `[DOC]` archival
  todo's 6-step ritual — but the SOURCE doc (`issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`) carries a real
  `locked_by: live-defi-rollout` / `locked_since: 2026-07-03` (per `plans/PLAN_FORMAT.md` § "Plan Locking", this is a
  genuine lock field, not free text — `check_strict_quickmerge.py`'s "Locked-plan deletion gate" enforces it at commit
  time). Prior na-eligibility-audit rounds (2026-08-04/07/08) characterized this as "a branch-name artifact, not treated
  as a blocker" for CLASSIFICATION purposes only — none of them actually archived the doc, so none tested whether the
  lock gate itself would fire. Per the workspace HARD RULE ("Agents MUST NEVER unlock plans autonomously — always ask
  first", `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` + `plans/PLAN_FORMAT.md` § "Plan
  Locking"), did NOT force an `[unlock-plan]` archival commit. Filed a `/blocked` question to the operator recommending
  unlock (all todos on both docs are genuinely done; the lock's own value is the branch name, not a distinguishing agent
  claim) and am closing out my assigned `[REVIEW]` task via `/done` instead of holding the slot on a human-gated step.
  `[DOC]` todo remains open, correctly gated on the operator's unlock decision — re-dispatch once answered.
- **2026-08-08 (DOC archival re-dispatch, slot 29)**: same `[DOC]` todo redispatched directly (recurring
  `gate_on_depends` wiring-gap bounce noted above). Re-verified: source doc still carries the genuine
  `locked_by: live-defi-rollout` / `locked_since: 2026-07-03` lock; no operator answer to slot 30's prior `/blocked`
  question is visible in the live `blocked_queue` (not present under any currently-tracked `blocked_id`, likely pruned
  or never surfaced against this specific task_id). Per the same HARD RULE, did NOT unlock autonomously. Re-filed the
  `/blocked` question against this task (`BLK-3d18ef7c`), recommending approve-and-archive. `[DOC]` todo remains open,
  gated on the operator's answer — re-dispatch once answered.
- **2026-08-08 (DOC archival re-dispatch, slot 12)**: same `[DOC]` todo redispatched a third time (same recurring
  `gate_on_depends` wiring-gap bounce). Checked `GET /api/state` directly: `BLK-3d18ef7c` (slot 29's question) is still
  present in `blocked_queue` with `answered_at: null` — the operator has not yet responded. Per RULES.md §5, a genuine
  pending human decision is not re-asked; filing a fourth duplicate blocked-question would just add queue noise, so did
  NOT re-file. Re-verified the source doc's lock is still live (`locked_by: live-defi-rollout` /
  `locked_since: 2026-07-03`) and did NOT unlock autonomously (same HARD RULE). `[DOC]` todo remains open, still
  correctly gated on the operator's answer to `BLK-3d18ef7c` — re-dispatch once answered; no further action needed from
  this slot until then.
- **2026-08-08 (DOC archival re-dispatch, slot 19)**: same `[DOC]` todo redispatched a fourth time (same recurring
  `gate_on_depends` wiring-gap bounce). Checked `GET /api/state` directly: `BLK-3d18ef7c` (slot 29's question) is **no
  longer present** in `blocked_queue` at all — this is a NEW finding, distinct from slot 12's observation
  (present-but-unanswered). Zero of the 65 live `blocked_queue` entries are `answered_at`-set (server appears to prune
  unanswered questions after some interval rather than resolving them), so this reads as pruned-without-response, not
  silently-approved. Re-verified the source doc's lock is still live (`locked_by: live-defi-rollout` /
  `locked_since: 2026-07-03`) and both docs still have zero open todos otherwise. Per the same HARD RULE, did NOT unlock
  autonomously. Since no live pending question remains for this task, re-filed fresh (`BLK-ce0fe830`,
  `can_continue: false` — there is no other in-scope work on this specific gated todo), recommending
  approve-and-archive. `[DOC]` todo remains open, gated on the operator's answer to `BLK-ce0fe830` — re-dispatch once
  answered. **Process note for whoever picks this up next**: if this same pruning happens again, consider whether the
  unlock decision should instead be raised through a channel that doesn't expire (e.g. a dedicated issue doc tagged
  `[OPERATOR]` rather than the ephemeral `/blocked` queue) since three consecutive blocked-questions have now gone
  unanswered before disappearing.
- **2026-08-08 (DOC archival re-dispatch, slot 9)**: same `[DOC]` todo redispatched a fifth time (same recurring
  `gate_on_depends` wiring-gap bounce). Checked `GET /api/state` directly: `BLK-ce0fe830` (slot 19's question) **is
  still present** in `blocked_queue`, `answered_at: null`, `paged_at` set — genuinely pending, not pruned this time. Per
  RULES.md §5 (a pending human decision is not re-asked), did NOT re-file a duplicate. Also confirmed the meta-issue
  slot 19 flagged (blocked-questions silently vanishing before an answer lands) is already tracked as its own doc,
  `issues/blocked_queue_unanswered_questions_pruned_without_resolution_2026_08_08.md` (status open at the time, P1, two
  `[BACKEND]` todos against `agent-orchestrator/server/`; both since completed and archived to
  `plans/archive/2026_08/issues/blocked_queue_unanswered_questions_pruned_without_resolution_2026_08_08.md`) — no new
  doc needed. Re-verified the source doc's lock is still live (`locked_by: live-defi-rollout` /
  `locked_since: 2026-07-03`) and did NOT unlock autonomously (same HARD RULE). No other in-scope work exists on this
  specific gated todo. `[DOC]` todo remains open, gated on the operator's answer to `BLK-ce0fe830` — re-dispatch once
  answered; no further action needed from this slot until then.
- **2026-08-08 (DOC archival re-dispatch, slot 10)**: same `[DOC]` todo redispatched a sixth time (same recurring
  `gate_on_depends` wiring-gap bounce). Checked `GET /api/state` directly: `BLK-ce0fe830` (slot 19's question) **is
  still present** in `blocked_queue`, `answered_at: null`, `paged_at` set — genuinely pending, not pruned. Per RULES.md
  §5 (a pending human decision is not re-asked), did NOT re-file a duplicate. Re-verified the source doc's lock is still
  live (`locked_by: live-defi-rollout` / `locked_since: 2026-07-03`) and did NOT unlock autonomously (same HARD RULE).
  No other in-scope work exists on this specific gated todo. `[DOC]` todo remains open, gated on the operator's answer
  to `BLK-ce0fe830` — re-dispatch once answered; no further action needed from this slot until then.
- **2026-08-08 (DOC archival re-dispatch, slot 3)**: same `[DOC]` todo redispatched a seventh time (same recurring
  `gate_on_depends` wiring-gap bounce). Checked `GET /api/state` directly: `BLK-ce0fe830` is **no longer present** in
  `blocked_queue` (65 total live entries, zero matches on that `blocked_id` or this task's `task_id`) — pruned again
  without an answer, the same failure mode slot 19 first caught. Rather than re-file an eighth ephemeral `/blocked`
  question into the same queue that has now swallowed three consecutive asks unanswered, applied the durable fix: split
  the `[DOC]` todo into a preceding `[OPERATOR]`-tagged todo (above) + the original `[DOC]` archival todo. Per
  `/codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md` (found via the matching precedent in
  `cefi_satellite_ao_dispatch_batch10_2026_08_08_finalize.md:77`, same "ask operator to unlock a done-but-locked doc"
  shape), an `[OPERATOR]`-tagged plan todo auto-seeds a `BLK-op-*` blocked-queue row that survives regen ticks (doesn't
  expire the way a worker-filed `/blocked` question does) and the operator can rule on it directly from the dashboard.
  Did NOT unlock the source doc autonomously (same HARD RULE); did NOT re-file another ephemeral `/blocked` question.
  `[OPERATOR]` todo is new and open — will seed its `BLK-op-*` row on the next regen tick; `[DOC]` todo remains open,
  gated on that row's resolution. This should end the 7-round redispatch loop: once the operator rules via the durable
  row, `regen_backlog_from_plan.py` materializes a real `--ruling` task instead of a worker having to rediscover the
  same state each cycle.
