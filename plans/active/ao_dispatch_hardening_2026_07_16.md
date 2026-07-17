---
doc_type: plan
title:
  AO dispatch + messaging hardening — eligibility-aware spawn budget, per-task tier spawn, dead-slot spill, worker-role
  gate (R1/R2/R5/R6) + the task-worker message channel and the invisible stuck-agent alarm
summary: |
  Fix the four code-confirmed dispatch/autospawn residuals that keep the AO fleet running below designed capacity —
  dead slots respawned onto un-claimable work (credit burn), mixed-tier queues starved, high-affinity tasks stranded on
  dead slots, and review/main slots claiming worker tasks. All four live in two files (server/autospawn.py +
  server/dispatch.py) so they share one plan and one QG sweep. The 2026-07-16 issue-doc sweep added three more, none of
  which any issue doc covered: the SlotMessageRow task-worker message channel still silently drops messages (the
  agent_messages fix never reached it), needs_operator_count is computed but rendered nowhere so a stuck agent is
  invisible, and agent-orchestrator is over its own QG baseline so every push is currently red. Human-executed — AO
  itself is too degraded to be trusted to dispatch its own fix.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    dispatch,
    autospawn,
    spawn-budget,
    role-gate,
    affinity,
    credit-burn,
    fleet-capacity,
    messaging,
    redelivery,
    observability,
  ]
related:
  [
    issues/ao_dispatch_residuals_2026_07_15.md,
    issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md,
    issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md,
    issues/dispatcher_role_eligibility_gap_review_slots_2026_07_13.md,
    issues/ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md,
    issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    ao_host_disk_pressure_2026_07_16.md,
    ../archive/issues/ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md,
    ../epics/orchestrator_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  - operator 2026-07-16 — "our current immediate scope is to make the AO work properly ... it finished some tasks and
    left others undone, worker agents might work or they just sit idle in the loop burning credits ... it doesn't work
    at the capacity it was designed for"
  - issues/ao_dispatch_residuals_2026_07_15.md (R1-R7 index; R1/R2/R5/R6 code-confirmed)
  - AO issue-doc audit 2026-07-16 (10 parallel verification agents)
---

# AO dispatch hardening (R1/R2/R5/R6)

> **Human plan — I execute it** (`assigned_vm: NA`). Deliberately NOT AO-dispatched: this fixes the very machinery that
> dispatches, and the bugs below can starve/skip the fix itself. Ships via `quickmerge.sh --agent --files`.

## Why

Operator (2026-07-16): _"there are so many issues and bugs that it's hard to allocate the plan to it. It finished some
tasks and left others undone, worker agents might work or they just sit idle in the loop burning credits. We think work
is being done but it doesn't work at the capacity it was designed for."_

Those symptoms are not vague — they map 1:1 onto four **code-confirmed** residuals, all verified against live code on
2026-07-16:

| Symptom (operator)                           | Residual | Root cause (verified)                                                                                                                                              |
| -------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| workers sit idle in the loop burning credits | **R1**   | spawn budget is **skip-blind** — `rg slot_skip server/autospawn.py` → **0 hits**; fleet-skipped tasks still inflate it → respawn dead slots onto un-claimable work |
| we think work is being done but it isn't     | **R6**   | `pick_next_task` has no **agent-role** gate; review/main slots never set `slot_role` → read as generic → claim worker tasks, then skip them                        |
| doesn't work at designed capacity            | **R2**   | AutoSpawn resolves ONE `(model, role)` tuple per tick and spawns every slot at it → a mixed-tier queue starves everything but the top task's tier                  |
| finishes some tasks, leaves others undone    | **R5**   | a task pinned `affinity=high` to a **dead** slot never spills → silently stranded forever                                                                          |

Measured blast radius (from `ao_skip_blind_spawn_budget_phantom_churn`, 24h window): **~1014 autospawns / 1184 boots /
954 deaths → 217 dispatches / 101 done**; budget=6 vs claimable=1 (5 phantom); pushed 2 of 4 accounts past the 95%
weekly ceiling on 2026-07-15, shrinking usable rotation to 2. (Accounts had recovered to 0–7% by 2026-07-16 — the burn
is intermittent, the code defect is permanent.)

## Verified code anchors (2026-07-16, current HEAD)

- **R1** — `server/autospawn.py:317` `_has_queued_work` / `:340` `_queued_undispatched_count` filter only
  `status=="queued"` + `dispatched_to is None` + `prereqs_met`. `server/dispatch.py:52` `pick_next_task` additionally
  filters model-tier, craft/role gate, affinity (`_task_is_routable_to`), repo/collision-group, and **`slot_skips`**
  (24h TTL). The asymmetry IS the bug.
- **R2** — `server/autospawn.py:388` `_top_queued_task_params`, called ONCE per tick at `:1646`, before the per-slot
  spawn loop. Its own docstring (`:415`) still admits: _"Known limitation: in a MIXED-tier / MIXED-role queue, all slots
  spawned in one tick use the top task's tier + role."_
- **R5** — `server/dispatch.py:257` `_task_is_routable_to`; `:289` `if affinity == "high": return False` — unconditional
  for every non-target slot, no dead/absent-target fallback.
- **R6** — `server/dispatch.py:79` reads `slot_row.slot_role`; the gate at `:97` no-ops when it's `None`.
  `server/prompts.py:206` sets `slot_role` **only** in `render_worker()`; `render()` (review/main) never does.
  `SlotRow.slot_role` is written only from `req.slot_role` at `server/routes/slots_worker.py:114`. True agent identity
  lives on `AgentRow.role` (`server/orm.py:290`, values `main`/`review`/`custom`), which `dispatch.py` never joins. Both
  `/boot` and `/heartbeat` call `pick_next_task` (`slots_worker.py:204,408,957`) → one shared fix covers both.

## ⚠️ Do NOT implement the source docs' literal remedies (code-verified 2026-07-16)

Three of this plan's own source docs prescribe fixes that current code contradicts. Read this before touching R6 or R7.

- **R6 — `dispatcher_role_eligibility_gap_review_slots` says "add a `slot_role`-based filter". That fix is actively
  dangerous.** `slot_role` is a **craft** field (`data_engineering`, `infra`…), populated only inside `render_worker()`
  (`server/prompts.py:206`). Review/main go through `render()` and never get one — so the filter no-ops for exactly the
  slots it targets. **Worse**: `server/dispatch.py:95-96` notes `slot_role` is `None` for **most ordinary worker slots
  too** (generic, no craft tag), so refusing dispatch on a falsy `slot_role` would **break the majority of normal worker
  dispatch, fleet-wide**. Two independent verification agents reached this from different angles. The gate MUST key off
  a genuine agent-identity signal (`AgentRow.role`, `server/orm.py:290`), never the craft field.
- **R7 — `ao_dispatch_residuals`' "larger fix" (content-hash task IDs) is out of scope and stays out.** Blast radius:
  `existing_ids` bookkeeping, `slot_skips` (keyed by task_id), dashboard/API id refs, `done_sha` history. And **the
  dangerous half of R7 is already fixed** — `agent-orchestrator@4695db6` added `TaskRow.brief_hash` + reset-on-mismatch,
  killing the silent-non-dispatch case. What remains needs an external race and explains **none** of the operator's
  symptoms. R7 goes DOWN the list, not up.
- **R3/R4 are pure prompt/doc text — zero code-regression risk** (`agents/main.md`, `agents/monitor.md`,
  `agents/RULES.md`; verified: zero occurrences of any deadlock-recheck or tier-isolation guidance). Cheap; kept in
  Phase 5.

## Todos

### Phase 0 — unblock the repo (P0, do FIRST)

- [x] [BACKEND] P0. ✅ **DONE 2026-07-16 — `agent-orchestrator@54c9e8d`. Gate green:
      `[OK] agent-orchestrator: 25 (== baseline)`; full `quality-gates.sh --no-fix` →
      `✅ agent-orchestrator quality gate PASSED` (exit 0, sentinel==HEAD); landed on LDR.** **The checker named the
      WRONG line** — it reported `_git_alerts.py:364`, which git-dates to **2026-06-11** (a month old). This repo's
      baseline row carries **no `commit:` anchor**, so the checker fell back to what its own docstring calls "an
      arbitrary positional tail-slice" — whichever site sorts last, not whichever is new (the failure mode named in
      `instruments_service_empty_string_fallback_baseline_breach_2026_07_14`). Blaming all 26 sites against the
      2026-07-08 seed gave exactly one newer: **`server/notifications/slack.py:405` (2026-07-14)** — 25 old + 1 new
      = 26. Fixed by **indexing** (`loss["sha"]`), not `# noqa`: that line builds the `dedup_key` for the
      **silent-data-loss canary**, `sha` is always set by its only producer (frozen `DiscardedCommit`, `sha: str`) so
      the `""` default is unreachable, **and** on this key an `""` would collapse two distinct losses to one dedup_key
      and **suppress a data-loss page** — silent corruption of the exact alert the canary exists to fire.
      ~~**`agent-orchestrator` is over its QG STEP 5.101 baseline — every push is currently red.**~~ Measured
      2026-07-16: `check_no_empty_string_fallback.py --scope agent-orchestrator` → **26 sites > baseline 25**, new site
      at `server/worker_liveness/_git_alerts.py:364`. **This blocks Phase 1-3 from shipping at all**, so it goes first.
      Fix by rewriting the fallback to fail fast, or annotate `# noqa: qg-empty-fallback` with a one-line reason **if**
      the empty string is genuinely a meaningful not-present value there. **Do NOT raise the baseline** —
      `write_baseline()` hard-clamps to `min(observed, prior)` and CLAUDE.md's ratchet HARD RULE says baselines only go
      DOWN. The checker flags it as a "positional tail-slice — no baseline commit on record for this repo yet", so
      confirm the site is genuinely new before annotating. **Gate**: `bash scripts/quality-gates.sh --no-fix` on
      agent-orchestrator reaches STEP 5.101 green. (Tracked as the owning todo on
      `issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`; flip it there too.)

### Phase 1 — stop the burn (P0)

- [x] [BACKEND] P0. ✅ **DONE 2026-07-16 — `agent-orchestrator@7baeedc`. QG green (own exit code 0): 1292 passed,
      basedpyright 0 errors; landed on LDR.** Added `dispatch.claimable_queued_task_ids()` as the ONE SSOT for the
      budget question ("could **any** worker slot take this?") vs `pick_next_task`'s per-slot question; both
      `_has_queued_work` and `_queued_undispatched_count` delegate to it so the two can no longer drift. Also extracted
      `_brief_is_deferred` (the DEFER prefix tuple had been inline — one definition now, not two). **Key design
      decision, pinned by 2 tests: model tier and craft role are deliberately NOT filtered.** `pick_next_task` gates
      them against the ASKING slot, but AutoSpawn CHOOSES them at spawn time — an opus task is not un-claimable just
      because every live slot is sonnet, since the next spawn can BE opus. Filtering them in would zero the budget,
      never spawn the opus/infra worker, and starve the work permanently — worse than the over-count, and for role it
      would reintroduce the exact starvation `ao@8a423bb` fixed. Superset-on-doubt: an empty slot table skips the
      per-slot filters rather than returning 0 (false starvation > stale over-count — the risk the verification agent
      flagged). **R1 does NOT subsume R5**: a task pinned to a slot that exists but is dead still counts 1, because that
      slot can be respawned onto it — the dead-slot spill is genuinely separate. 6 tests: skipped-by-every-slot → 0 vs
      skipped-by-some → 1; tier guard; role guard; DEFER brief; repo collision (+ `parallel_safe` opt-out); affinity pin
      to absent slot. ~~**R1 — eligibility-aware spawn budget.**~~ Extract `pick_next_task`'s eligibility predicate into
      one shared helper (single SSOT for "is this task claimable by any live slot?") and make
      `_has_queued_work`/`_queued_undispatched_count` (`server/autospawn.py:317,340`) use it, so skip-exhausted /
      role-ineligible / collision-blocked / affinity-pinned tasks stop inflating the spawn budget. **Gate**: a task
      skipped by every eligible slot counts 0 toward the budget; existing autospawn tests stay green. Closes R1 + the
      `Skip-exhaustion churn` carry-forward stranded in archived `ao_autospawn_role_blind_dispatch_starvation`.
- [x] [BACKEND] P0. ✅ **DONE 2026-07-16 — `agent-orchestrator@962e676`. QG green (own exit 0): 1302 passed,
      basedpyright 0 errors.** Implemented as a **row in the `_FILTERS` table** (scope `SLOT`), so it lands in BOTH the
      dispatcher and the spawn budget by construction; the budget's hand-written review exclusion was removed (one rule,
      one place). **Did NOT implement the source doc's recommended fix** — it says "add a `slot_role`-based filter";
      `slot_role` is a CRAFT tag that is empty for review/main **and for most ordinary generic workers**, so gating on
      its falsiness would refuse dispatch to the majority of the normal fleet. Keyed on the explicit `review_slot_ids()`
      config list instead; `test_generic_worker_with_no_slot_role_still_gets_tasks` pins that. **Covers 3 routes, not
      the 2 the doc named**: `pick_next_task` is the single chokepoint for `/boot` (`slots_worker.py:204`), `/heartbeat`
      (`:408`) **and `/done`** (`:957` — a worker takes its next task on completion, which the doc missed). No
      route-level TestClient harness exists in this repo; adding one would exercise the same single call. **No
      "main-role slot" exists to test** — main runs as its own tmux session (`MAIN_SESSION_NAME`), not a numbered slot,
      so it never reaches a slot dispatch route. **Blast radius verified on the real fleet BEFORE shipping** (autonomous
      rule 11): central VM has `ORCHESTRATOR_REVIEW_SLOTS` **unset** → `review_slot_ids()` = `{2}` in production; live
      backlog shows tasks dispatched to slots **8/11/13/15 and none to slot 2**; `pick_next_task` only decides NEW
      dispatches so no in-flight work is interrupted. **Test-fixture trap caught**: `conftest.py`'s autouse
      `_default_review_slots_off` neutralises the production default, so tests MUST set `ORCHESTRATOR_REVIEW_SLOTS`
      explicitly or they exercise an empty review set and pass while testing nothing — all 5 tests set it; removing the
      gate fails 3 (the other 2 are negative controls). ~~**R6 — worker-role dispatch gate.**~~ Gate `pick_next_task`
      (`server/dispatch.py:52`) so only slots whose **agent** role is a worker receive a backlog `task_id` (join
      slot→`AgentRow.role`, or thread the role through boot/heartbeat — pick whichever avoids a per-call join in the hot
      path). Keep the existing craft `slot_role` check as-is; this is a distinct, upstream gate. **Gate**: regression
      test dispatching a backlog task to a `review`-role and a `main`-role slot via BOTH `/boot` and `/heartbeat`,
      asserting no `task_id` is returned.

- [x] [BACKEND] P0. ✅ **DONE 2026-07-16 — `agent-orchestrator@bf9a61b`. QG green (own exit 0): 1297 passed,
      basedpyright 0 errors.** **R1 hardening — close the drift gap structurally** (operator question 2026-07-16: _"is
      there a way that we can do this filtering in one place so that the gap between dispatch and AutoSpawn never occurs
      again?"_ — a fair challenge: `7baeedc` shared the filter PRIMITIVES but each function still composed its OWN list,
      so adding a 10th filter to `pick_next_task` and forgetting the budget would have brought the phantom churn
      straight back). `pick_next_task` and `claimable_queued_task_ids` now **derive** from a single `_FILTERS` table;
      each row declares a `FilterScope` — `FLEET` (same answer for all slots → blocks means nobody can claim it), `SLOT`
      (varies by slot, AutoSpawn cannot change it → budget honours existentially), `CAPABILITY` (varies by slot but
      AutoSpawn can spawn one that passes → budget ignores). The asymmetry is now a **type, not tribal memory**: "can
      any slot take T" is the existential form of "can slot S take T" EXCEPT that AutoSpawn picks tier+role at boot.
      **Structural, not disciplinary**: `_Filter.scope` has no default, so a filter cannot be constructed without
      classifying it. **Proved, not asserted** — injecting the plausible "cleanup" (`model_tier` CAPABILITY→FLEET) fails
      **4** tests: the structural pin, the behavioural contract, and **two pre-existing tests** incl.
      `test_opus_task_no_longer_starves_behind_idle_sonnet_in_run_one_tick` — someone had already been burned by that
      exact starvation and left a regression test, which independently confirms the classification is right and that
      "just make them symmetric" would have re-broken it.

### Phase 2 — restore designed capacity (P1)

- [x] [BACKEND] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@6ae43b5`. QG green (own exit 0): 1304 passed,
      basedpyright 0 errors.** New `_spawn_param_plan` yields **one entry per CLAIMABLE task** (same
      `claimable_queued_task_ids` SSOT the budget counts → plan and budget cannot disagree about what is servable),
      ordered starved-role-first then by dispatch's own tie-break; the i-th slot spawned takes the i-th entry.
      `assigned_role` now travels **per-slot** through `to_spawn` instead of being one tick-wide value closed over by
      the slow section — that closure was why every worker in a tick came up at the top task's craft. The "Known
      limitation" docstring is **deleted** (no longer true). **Generalises ao@8a423bb** from "narrow the pool to
      starved" to "sort starved first" — equivalent at the head (a test asserts `plan[0]` still matches, so that fix's
      guarantee is preserved) but the REST of the tick's spawns now serve the OTHER starved roles too.
      **`_top_queued_task_params` DELETED, not shimmed** (CLAUDE.md: delete deprecated code) — basedpyright caught it
      going unused the moment the tick stopped calling it. **Found + fixed a pre-existing latent test bug**: 4 tests
      patched `_top_queued_task_params` with a **3-tuple** while it returned a **4-tuple**, so the tick's unpack raised
      and was swallowed by its `except Exception` — those tests were passing on the sonnet FALLBACK, not on their patch;
      they now patch `_spawn_param_plan` with the right shape. Proof: reverting to the one-tuple behaviour fails both
      new tests; the 5 pre-existing spawn-param tests stay green throughout. ~~**R2 — per-task tier/role spawn.**~~
      Resolve the spawn `(model, effort, thinking, role)` **per slot being spawned** instead of once per tick
      (`server/autospawn.py:1646` + `_top_queued_task_params:388`), so a mixed-tier queue stands up the right tier per
      slot. Delete the now-false "Known limitation" docstring at `:415`. **Gate**: unit test — a queue holding one opus
      task + one sonnet task spawns one slot per tier in a single tick.
- [x] [BACKEND] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@860eaf7`. QG green (own exit 0): 1310 passed,
      basedpyright 0 errors.** Replaced the unconditional `if affinity == "high": return False` with a liveness-aware
      check. **Deliberately NOT "target missing → spill immediately"** (the naive fix the verification agent flagged):
      that defeats the session-continuity guarantee `affinity=high` exists to provide. Gated on a TIME threshold — new
      `high_affinity_spill_after_seconds` (default **600s**, matching `failover.py`'s offline threshold and the
      medium-affinity `target_slot_timeout_seconds`, not an invented number). "Dead" is computed with the fleet's **own
      SSOT** for slot silence (`worker_liveness_watchdog.effective_silence_seconds`) so it means the same thing to the
      dispatcher as to the watchdog that reaps them — that helper is **promoted private→public** (basedpyright flagged
      the cross-module private use rather than let it slide) and is NULL/stale-aware, so a zombie row with no activity
      anchor reads as `inf` = dead, not "just pinged" (the 2026-06-08 incident where six slots were never freed).
      **Composes with R1**: once the pin spills the task is claimable, so it correctly warrants a spawn — before, it was
      un-claimable AND un-spillable, the worst combination. **Superseded an R1-era test expectation**: a pin to an
      absent slot used to assert budget 0 ("routable to nobody"); R5 makes the right answer 1 (it spills) — the test is
      rewritten as a worked example of the two fixes composing, with the history noted, not deleted. Proof: restoring
      the unconditional pin fails 3 of 6 new tests; the 3 that still pass are the live-target guards, which must be
      unaffected. ~~**R5 — high-affinity dead-slot spill.**~~ In `_task_is_routable_to` (`server/dispatch.py:257`),
      replace the unconditional `if affinity == "high": return False` (`:289`) with a liveness-aware check — a
      high-affinity task whose `target_slot` is dead/absent must spill to another eligible slot; a task whose target is
      alive must still NOT spill. **Gate**: two unit tests (dead target → spills; live target → does not).

### Phase 2b — the worker message channel + the invisible alarm (P1, NEW 2026-07-16)

> Surfaced by the AO issue-doc sweep; **no issue doc covers either**. `ao_operator_message_silent_drop_no_reply_ack`
> fixed the `agent_messages` channel (all 10 of its todos verified genuinely in code) — but it fixed it only for
> **main/review/custom chat agents**. The parallel channel that **craft task workers** use was never touched and still
> carries the identical bug the doc was written to kill.

- [x] [BACKEND] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@d90f0f5`. QG green (own exit 0): 1316 passed,
      basedpyright 0 errors.** **Deliberately did NOT port the sibling's redeliver-until-`/reply` design (which this
      todo originally prescribed)** — a decision made after reading the code: task workers have **no reply endpoint**
      (`agents/worker.md` only says "the progress response may include [messages] … read them and act"), so "unanswered"
      is _unobservable_ for a worker, and redelivering until an ack that can never arrive would re-show the same
      instruction on every heartbeat and risk **duplicate ACTIONS** — strictly worse than the drop being fixed. Instead
      delivery is **session-scoped**: a message redelivers only when `delivered_to_session` != the slot's live
      `claude_session_id` — a fresh uuid per spawn (context lost → the new session genuinely hasn't seen it) but
      **preserved across a `--resume` account failover** (context intact → no spurious redelivery). That is also why it
      keys on the session id and not `last_spawned_at`, which would churn on a resume that kept full context. Capped at
      new `slot_message_max_redeliveries` (default 30, mirroring the agent channel) → terminal + counted by
      `count_slot_messages_needing_operator`, i.e. **loud** instead of the silent drop on the FIRST death. Migration
      carries the **one-time backfill** the `agent_messages` migration warned about (historical delivered rows →
      terminal), without which every old message would mismatch the current session on the first post-deploy heartbeat
      and flood every live worker — worse than the bug. **Known limit, documented not hidden**: a session that receives
      a message, ignores it, and keeps running is not detected — that's worker behaviour, not delivery; closing it needs
      a worker-side ack primitive + prompt contract. Proof: restoring the deliver-once semantics fails the
      respawn-survival and cap tests. ~~**Task-worker messages can be silently, permanently lost.**~~ `SlotMessageRow` /
      `enqueue_message` / `take_pending_messages` (`server/state_store/activity.py:223-238`, posted via
      `POST /api/slots/{slot_id}/message`, drained on the worker's next `/boot`/`/heartbeat`/`/progress`) stamps
      `delivered_at` **on take** with **no `answered_at`, no reply-ack, no redelivery** — structurally the exact pre-fix
      shape of `agent_messages`. If a worker's session dies, respawns, or `/compact`s between taking the message and
      acting on it, the message is gone with **zero operator-visible signal**. Port the already-proven `agent_messages`
      pattern (`answered_at` column + redeliver-until-answered + cap) rather than inventing a second mechanism.
      **Gate**: unit tests mirroring `tests/test_agent_message_redelivery.py` — take→no-ack→redelivered; ack stops
      redelivery; cap flips to needs-operator.
- [x] [BACKEND] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@fa73b5d`. QG green (own exit 0): 1316 python passed, tsc
      clean, 90 vitest passed (was 84).** `deliveryChip` now takes `needsOperatorCount` and renders a red **"needs
      operator N"** chip that **OUTRANKS "queued"** — that precedence is the whole point and is pinned by a test: in the
      realistic stuck case BOTH counts are non-zero (the capped message is still pending), so a naive
      `pendingCount`-first check would render the benign amber "queued N" and the operator would never learn the agent
      stopped answering. Also found: the TypeScript `AgentView` type **did not even declare the field the API was
      already serving** — so the UI was structurally blind to it, not merely not-rendering it. TS strict caught the
      `agentTypes` fixture the moment the field became required (fixed, not made optional). ~~**The stuck-agent alarm is
      wired to nothing.**~~ `needs_operator_count` — the counter that fires when an agent stops answering after
      `agent_message_max_redeliveries` (default 30, ≈30 min) — is **computed correctly** at
      `server/routes/agents.py:226-231` and **rendered nowhere**: zero occurrences in the dashboard `.tsx` (only
      `pending_count` is shown, `dashboard/src/layout.tsx:2523`), and no Slack wiring. A genuinely stuck agent is
      invisible short of a manual API query — which is precisely the operator's _"we think work is being done but it
      doesn't work at the capacity it was designed for"_. Surface it (dashboard badge + an alert route). **Gate**: a
      capped-out agent is visible without anyone curling the API. Closes the `[~] Remaining` dashboard item in
      `issues/ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-16 — `agent-orchestrator@da053a9`. QG green (own exit 0): 1323 passed,
      basedpyright 0 errors.** Retried via new `nudge_attempts` (default 3) + `nudge_retry_backoff_s`. **Found a worse
      bug than the todo knew**: `send_command` called `subprocess.run` twice with `capture_output=True`, **no `check=`,
      and never inspected `returncode`** — so a failed `tmux send-keys` raised nothing and `nudge()` returned **True**:
      a send that never landed, reported as delivered. Now raises on a non-zero send AND on a non-zero `C-m` submit
      (text landed but never submitted → the agent sees a half-typed prompt and does nothing, which is worse than a
      clean failure). All 5 call sites already handle the pre-existing missing-session `RuntimeError`, so no caller
      contract changed. **Retry follows ONLY a raised failure** — that is the idempotency argument, and a test pins it:
      `send_command` raises _before typing anything_, so nothing reached the pane and re-sending cannot double-deliver;
      a **successful** send returns immediately and is never repeated, because re-typing a delivered wake into a live
      agent's pane risks it **acting twice**. An unconditional retry loop would look tidier and would be a bug.
      ~~**Nudge is single-shot best-effort.**~~ `server/tmux_spawn.py:1442-1455` `nudge()` makes one `send_command`
      attempt and swallows the failure (`except Exception: ... return False`) — no retry, no idempotency, no
      verification the pane received it. Delivery now survives this (the message redelivers on the next poll), so this
      is a **latency** bug, not a loss bug — but a missed nudge on a heads-down `/loop` costs a full poll cycle. Make it
      retried + idempotent. Closes that doc's last genuinely-open todo.

### Phase 3 — prove it (P0)

- [x] [BACKEND] P0. ✅ **DONE 2026-07-16 — every unit shipped QG-green via quickmerge, each with the gate's OWN exit
      code checked (not `tail`'s — I misread that once and reported a green that wasn't).** Ships: `54c9e8d` (Phase 0) ·
      `7baeedc` (R1) · `bf9a61b` (filter table) · `962e676` (R6) · `6ae43b5` (R2) · `860eaf7` (R5) · `d90f0f5` (worker
      messages) · `fa73b5d` (needs_operator UI) · `da053a9` (nudge) · `f163892` (comment) · `96d005f` (gitignore) ·
      `e7f70c8` (disk backstop). Final QG: **1329 passed, 1 skipped, basedpyright 0 errors, tsc clean, 90 vitest**. All
      landed on LDR; all verified RUNNING on the central VM after the operator's deploy. ~~Regression suite green + full
      `bash scripts/quality-gates.sh` on agent-orchestrator; ship via~~
      `quickmerge.sh "fix(dispatch): ..." --agent --files '<paths>'`. **Gate**: QG green + `Quickmerge:` trailer + LDR
      landed.
- [x] [OPERATOR] P0. ✅ **MEASURED 2026-07-16 17:35Z — VERDICT: R1 did NOT reduce the churn. Residual root-caused to ONE
      dead slot and fixed in `agent-orchestrator@6c778e6`.** Deploy verified first (clone `behind=0`, code RUNNING,
      reload clean, `slot_messages` migration ran once and backfilled exactly as designed — the flood risk did NOT
      materialise), so this is a measurement of the fix, not of a stale box. - **Hourly series across the 15:01Z deploy
      boundary — flat.** `autospawn_succeeded`: 13:00 **29** · 14:00 **27** ‖ _deploy_ ‖ 15:00 **27** · 16:00 **30**. No
      step change. 24h totals: `slot_boot` 1292, `worker_kicked` 1136, `autospawn_succeeded` 915, `worker_polling_dead`
      901 — and **`task_dispatched` 63**, i.e. ~14.5 spawns per dispatch. `task_dispatched` was **0 for the 3h
      straight** after the deploy. - **I MISREAD MY OWN EVIDENCE and must not repeat it.** This todo previously recorded
      `spawned=1 … queue_satisfied: 10–13` as an _"early signal that R1 is working — the budget is SATISFIED after ONE
      spawn"_. **That reading was wrong: it is the signature of the residual BUG.** `queue_satisfied: 13` means 13 slots
      were skipped because `len(to_spawn) >= spawn_budget` — i.e. `spawn_budget == 1`, every tick, forever, for a task
      that then never dispatched. A number consistent with the fix was also consistent with the bug, and I reported the
      flattering reading without testing the other one. - **Root cause (measured, live DB).** 20 backlog tasks / 13
      queued; **12 of 13 are prereq-blocked** behind operator gates (`dvol-historical-pull-approved`,
      `gw-enrichment-landed`, `sports-cf8-maintenance-window-scheduled`, `morpho_vm_complete_and_consolidator_fresh`,
      `cefi-recapture-sweep-complete`, `overnight-cron-selffire-window-passed`) or an unfinished upstream task. The 13th
      — `sports_travel_calculator_tz_aware_kickoff_crash-001` — reads **"ready (no blockers)"** and drove `budget=1`
      every tick. **All 15 real worker slots had already skipped it** (35+ consecutive declines, each logged genuinely
      BLOCKED-PREREQ on a parent-plan todo). **Slot 0 — unconfigured and paused since 2026-07-06 — had no skip**,
      because nothing ever ran there to decline anything. The budget's SLOT scope is EXISTENTIAL and ranged over EVERY
      slot, so dead slot 0 passed on the strength of never having skipped anything → task "claimable" → spawn a REAL
      slot that had already skipped it → handed nothing → idled → watchdog reclaimed it → respawn. ~30/h against ZERO
      dispatches. - **Fix `6c778e6`**: `claimable_queued_task_ids`' candidate set now gates on
      `dispatch.slot_is_spawnable` (configured + not paused) — the SAME predicate `autospawn._should_spawn` uses, which
      `_slot_is_configured` now delegates to, so they cannot drift. R1 made the budget eligibility-aware but left its
      **candidate set** wrong: an existential check is only sound over slots that can actually receive the work.
      Deliberately NOT a `_FILTERS` row (a filter is task-dependent and would also refuse tasks to a paused slot already
      running a worker — 30 tests caught that overreach). QG exit 0, **1342 passed**, basedpyright 0 errors; 2 new
      tests, bug-injection verified. - **Gate**: autospawn:dispatch ratio materially down + no idle-respawn loop on a
      fleet-skipped task. Query: `activity_log` (NOT `activity`) on `/var/lib/orchestrator/state.db`; no `sqlite3` CLI
      on the box — use `.venv/bin/python3`.
- [x] [BACKEND] P0. ✅ **MEASURED 2026-07-16 18:08Z — `6c778e6` did NOT stop the churn. The gate above said "if it does
      NOT, this phase reopens again"; it did not, and it has.** Deploy confirmed first (`SHA=6c778e6`, and
      `slot_not_configured` rose 1→2 as the paused-slot exclusion took effect, so the new code was demonstrably
      running). Ticks still read `spawned=1 … queue_satisfied: 9–13` — budget still 1. - **Second, INDEPENDENT break of
      the same invariant.** `slot_skips` carry a **24h TTL**, so a fleet-wide skip decays UNEVENLY. Live at 18:08:
      `slot 13/14/15/16 → skip 25–29h → EXPIRED → justify budget=1`;
      `slot 2/3/5/6/7 → skip 4–18h → still VALID → cannot take the task`; **and AutoSpawn spawned 2, 3, 5, 6, 7.** -
      **The budget is a COUNT** ("N tasks claimable by SOMEBODY") and cannot say WHICH slots. Nothing checked that the
      slot being spawned was one of the slots that made the count non-zero. So the budget was satisfied by slot 13 while
      the spawn landed on slot 2 — structurally unable to claim the only task that bought it. Boot → poll → nothing →
      idle → watchdog reclaim → respawn. - **Fix `agent-orchestrator@f8ace1f`**: `dispatch.slot_has_claimable_task`
      answers the per-slot question from the SAME `_FILTERS` table (FLEET+SLOT; CAPABILITY still ignored — AutoSpawn
      picks model/role), and the tick asks it before spawning. Each expiring skip now costs exactly ONE spawn — the
      retry the TTL exists for — instead of an unbounded loop, and the tick can reach a TRUE zero. `_apply_fleet_cap`
      extracted from `_run_one_tick` to buy back the C901 budget: **the complexity cap is a real constraint and was not
      raised.** QG exit 0, **1345 passed**. - **Testing lesson worth keeping**: the dispatch tests all passed with the
      new gate DELETED — they prove the PREDICATE, not the CALL. A tick test now pins the wiring, verified by injection;
      its failure output reproduces the live tick line exactly (`checked=2 spawned=1 skips={'queue_satisfied': 1}`).
- [x] [BACKEND] P0. ✅ **DONE 2026-07-17 — verdict: `f8ace1f` WORKS. Closed on the LIVE RATE, as the gate demanded.**
      All three gate conditions met, measured on the central VM's `activity_log` (not on code, tests, or the deploy):
      (1) `git merge-base --is-ancestor f8ace1f HEAD` → **YES**; (2) `no_claimable_task_for_slot` was the ATTRIBUTED
      skip reason at measurement (`checked=17 spawned=3 skips={'no_claimable_task_for_slot': 9, …}`, 18:40); (3) the
      rate collapsed. **`autospawn_succeeded`/h: ~31 → ~0.25** (a 99% collapse). The decisive contrast is spawns vs
      dispatches per hour, which is what "churn" actually means: | hour (UTC) | spawns | dispatches | | --- | --- | ---
      | | 07-16 15:00 | 27 | **0** | | 07-16 16:00 | 30 | **0** | | 07-16 17:00 | 30 | **0** | | _18:28 — f8ace1f
      deployed_ | | | | 07-16 19:00 | 6 | 10 | | 07-16 20:00 | 17 | 19 | | 07-16 21:00 | 8 | 8 | | 07-17 02/03/07 |
      1/1/1 | 1/1/1 | **Pre-fix 15:00–17:00 = 87 spawns / 0 dispatches (INFINITE waste). Post-fix 19:00–21:00 = 31
      spawns / 37 dispatches.** Spawns now TRACK dispatches instead of running away from them — the 17-spawn hour at
      20:00 is a WORKING fleet (19 dispatches), not churn, which is exactly the distinction the two failed fixes could
      not make. Last 12h: **3 spawns / 3 dispatches = 1.00:1** against the 44:1 baseline; `worker_polling_dead` 11/12h
      (~0.9/h, down from ~30/h). Note for the next reader: in the quiet state the tick emits **no INFO line at all** —
      it early-returns at DEBUG (`autospawn.py`, "no dispatchable queued work"), so an absent tick line is healthy idle,
      NOT a dead loop. **Process failure worth recording**: the fix was proven live at 18:44 on 2026-07-16 and this box
      was not flipped until 2026-07-17 — a half-1-without-half-2 violation of the commit-push-flip rule, i.e. the plan
      under-reported real progress for a day.
- [ ] [BACKEND] P1. 🔵 **DIAGNOSED 2026-07-17 — root cause found; the APPLY step is operator/Ikenna-gated (sports
      freeze). Not closeable by me.** `f8ace1f` stops the phantom SPAWN; it does NOT stop the phantom OFFER — in the 12h
      to 2026-07-17, **38 of 49 dispatches were declines**, and `sports_p2_features_history_to_ml_ready-002` alone was
      handed to **13 different slots**, all declining. **The "find out WHY it did not stick first" question is ANSWERED
      — and the premise was wrong. The recipe DOES stick.** Control case, verified live:
      `mvp_backfill_defi_onchain_v10-002` carries `priority:999` + `priority_override:true` + prereq
      `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (value **0**) → dispatch reports "prerequisite … not
      set", it is correctly parked, and the park **survived the 04:10 backlog regen**. So the recipe is sound and
      durable. The sports tasks simply never received it, in two DIFFERENT ways: - `sports_p2_..._ml_ready-002` →
      `prerequisites: []`. **The park was never applied to it at all.** - `sports_p2_..._ml_ready-001` → prereq IS
      present (`sports-cutover-phase6-consolidator-resumed`) **but the condition was flipped to value=1 (TRUE) by
      `slot-phase6-restore`** while the consolidator is still frozen. The gate meant to stop the thrash reads SATISFIED,
      so dispatch says "ready (no blockers)" and keeps offering it, while every worker independently re-checks reality
      and declines (_"0 VMs, sports launches frozen … hard floor ~2026-07-17T19:52Z"_). **A prematurely-TRUE flag is
      worse than no flag: it launders a real block into a false all-clear.** **Blocked on**: the sports freeze + that
      flag are `sports_legacy_bucket_cutover_2026_07_16` Phase 6 — the data-pipeline owner's call (Ikenna). Un-flipping
      another plan's operator-authorized gate is not mine to do. **Next step when unblocked**: apply the mvp_backfill
      recipe to `-002`, and set `sports-cutover-phase6-consolidator-resumed` back to false until Phase 6 T6.1 genuinely
      resumes the consolidator. Tracked in `issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15` +
      `issues/mvp_backfill_defi_v10_002_dispatch_thrash_2026_07_16`.

### Phase 4 — close the paper trail (P2)

- [x] [BACKEND] P2. ✅ **DONE 2026-07-16 — `unified-trading-pm@5a79c4c23`.** Rewrote
      `codex/04-architecture/agent-orchestrator-autospawn.md`: added the **§ Spawn budget** section X3 flagged as
      missing (the `FilterScope` table, the measured 1014/101 churn, and an explicit warning that 'simplifying'
      `CAPABILITY` into the budget starves the fleet), corrected Gate 1 to CLAIMABLE-not-queued, and fixed live
      codex↔code drift — the doc still documented `_top_queued_task_params`, which R2 **deleted**. `last_reviewed`
      bumped. ~~Document the (now-fixed) spawn-budget contract in~~
      `codex/04-architecture/agent-orchestrator-autospawn.md` — the doc-gap flagged as X3's third corroboration in
      `ao_docs_reconciliation_2026_07_15`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-16 — `agent-orchestrator@f163892`.** The comment cited `recovery-audit` as the
      live NEVER_LAUNCH example; that set is now `frozenset()` and its only member's template is deleted, so it pointed
      at nothing. Branch kept (it is the enforcement point for any future never-launch role), and the comment now
      records the scope a reader would otherwise get wrong: the Layer-1 signoff FUNCTION is not retired, only its AO
      worker-role producer. ~~Clean the stale `recovery-audit` comment at `server/routes/agents.py:146` (carried from
      the~~ recovery-audit ruling — a one-line cleanup deliberately batched here to avoid a separate code ship).
- [~] [REVIEW] P2. 🟡 **HALF DONE 2026-07-16 — todos flipped (`unified-trading-pm@5a79c4c23`), ARCHIVAL correctly still
  pending Phase 3.** 7 todos flipped with shas across 4 source docs; `ao_fleet_stall`, `dispatcher_role_eligibility` and
  `ao_operator_message_silent_drop` are now at **0 open todos** and archivable — but deliberately NOT archived, because
  this todo gates archival on the runtime proof and code-shipped ≠ fixed. R3/R4/R7 dispositions are recorded explicitly
  (R7 DOWN-prioritised: its dangerous half is already fixed at `4695db6`), so nothing goes dark. `ao_skip_blind` keeps 1
  open todo by design (durable park — R1 made it MORE important, not less: it fixed the churn and thereby turned a LOUD
  failure into a silent one). ~~Close out the source issue docs once Phase 3's runtime gate passes — archive~~
  `ao_skip_blind_spawn_budget_phantom_churn` (R1), `dispatcher_role_eligibility_gap_review_slots` (R6),
  `ao_dispatch_residuals` (R1-R7 index; note R3/R4/R7 disposition explicitly, don't let them go dark), and flip
  `ao_fleet_stall_opus_spawn_and_skip_thrash`'s R2 todo. **Gate**: no residual left without a home.
- [x] [REVIEW] P2. ✅ **DONE 2026-07-16 — `unified-trading-pm@5a79c4c23`.** Repointed `agent_operating_framework_master`
      → `orchestrator_master`, matching the other four dispatch-code docs/plans; it was the lone outlier. Rationale
      recorded inline: `orchestrator_master` owns the AO RUNTIME (dispatch/autospawn/slots),
      `agent_operating_framework_master` owns how agents WORK (retrieval, charters, plan format) — a skip-blind spawn
      budget is runtime. ~~Fix the F5 epic seam: `ao_skip_blind_spawn_budget_phantom_churn` carries~~
      `parent_epic: agent_operating_framework_master` while every other dispatch-code doc/plan uses
      `orchestrator_master`. Repoint it. (Surfaced by this plan's authoring; `ao_docs_reconciliation` F5 = "cross-epic
      dispatch-code ownership seam fuzzy".)

### Phase 5 — process residuals (P2, from ao_fleet_stall)

- [x] [OPERATOR] P2. ✅ **DONE 2026-07-16 (R3) — `unified-trading-pm@5a79c4c23`.** `agents/main.md` **STEP 2.4**: never
      conclude the fleet is deadlocked from ONE gated task — PROVE it per task via `GET /api/backlog/{task_id}/blockers`
      before stopping dispatch (≥1 `ready (no blockers)` ⇒ NOT deadlocked ⇒ the problem is spawn/dispatch-side), and a
      slot saying "no work for me" is evidence about THAT SLOT, never the queue. `agents/monitor.md`: alert on what you
      MEASURED, never on what you infer — a fleet-stall belief is a HYPOTHESIS, not a breach, and must never be the
      reason dispatch stops. ~~Monitor/main-agent guard — don't extrapolate one gate to "fleet deadlocked"; re-check~~
      `/api/backlog/{id}/blockers` before declaring a stall.
- [x] [OPERATOR] P2. ✅ **DONE 2026-07-16 (R4) — `unified-trading-pm@5a79c4c23`.** `agents/main.md` **STEP 2.6**. The
      framing CHANGED with R2 and the todo says so: per-slot spawn params remove the COST blow-up (one opus plan no
      longer drags every worker up a tier), so the residual guidance is about queue SHAPE, not cost — and it explicitly
      forbids the tempting wrong fix of re-tiering plans to smooth the queue, which would trip the worker's own SSOT
      self-check on "Sonnet on opus-required". ~~Operating guidance — mixing a high-priority Opus plan with Sonnet plans
      in one queue is a~~ known-degraded shape; R2 reduces but does not eliminate it. Capture the guidance once R2
      lands.

## Out of scope (named successors — nothing goes dark)

- **R3/R4** (`ao_dispatch_residuals`) — prompt/heuristic guidance, not grep-able code claims; disposition recorded in
  Phase 4 rather than fixed here.
- **R7** — narrower code gap; fold into Phase 4's close-out decision.
- **Recovery-audit Layer-1 producer rewire** — operator ruling B, DEFERRED behind this plan.
  `issues/ao_recovery_audit_layer1_deleted_2026_07_15.md`.
- ~~**`ao_operator_message_silent_drop`'s P2 nudge idempotency**~~ — **PULLED IN** as Phase 2b (2026-07-16): the sweep
  showed the same doc hides a bigger, uncovered bug (the `SlotMessageRow` task-worker channel), and both are the same
  mechanism family, so they ship together.
- **Host disk pressure + the qg-host-governor mode drift** — split into a sibling **infra**-craft plan so the two can
  run in parallel: [`ao_host_disk_pressure_2026_07_16`](ao_host_disk_pressure_2026_07_16.md). It is a genuinely
  **independent second cause** of the operator's "tasks left half-finished" symptom (a full disk kills a worker's
  pytest/QG mid-task, indistinguishable from the agent giving up) — fixing dispatch alone would NOT have fixed it.

## Codex SSOTs

- `codex/04-architecture/agent-orchestrator-autospawn.md` — autospawn/spawn-budget contract (Phase 4 updates it).
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — single-VM + role-based dispatch.
- `codex/04-architecture/agent-orchestrator-overview.md` — runtime overview.
- `codex/06-coding-standards/quality-gates.md` — the ship gate.

## Progress Log

- **2026-07-16** — Plan created from the AO open-issue audit (10 parallel verification agents). All four residuals
  re-verified against current HEAD before authoring (anchors above); `rg slot_skip server/autospawn.py` → 0 hits
  confirms R1's skip-blindness firsthand. Operator chose: one human plan, all four in one pass. Home =
  `orchestrator_master` (matches all 3 archived dispatch-family plans + 3 of 4 source issue docs).
- **2026-07-16 (expanded)** — Reconciled against the full 20-doc AO issue-doc sweep (7 parallel code-verification
  agents, every todo re-checked against code with `file:line` evidence rather than trusted). Three additions, none of
  which any issue doc covered: **Phase 0** (agent-orchestrator is at 26 > QG baseline 25 — every push red, so it must
  land first), and **Phase 2b** (the `SlotMessageRow` task-worker channel still silently drops messages;
  `needs_operator_count` computed but rendered nowhere). Added the **do-not-implement** section: two independent agents
  confirmed `dispatcher_role_eligibility`'s own recommended `slot_role` fix would break the **majority of normal worker
  dispatch fleet-wide**, and R7's content-hash rewrite is high-blast-radius with its dangerous half already fixed at
  `agent-orchestrator@4695db6`. Operator ruling 2026-07-16: **two human plans** — this one (backend craft) plus a
  sibling infra plan for host disk/governor, so they run in parallel. Estimate 4→6 baseline days for the three new
  items.
- **2026-07-16 (Phase 3 blocked — the fixes were never running).** Every code phase is shipped and QG-green, but the
  runtime bar cannot be measured yet: the central VM's service clone has been frozen 23 commits behind since 2026-07-14
  by a single untracked file, so R1/R2/R5/R6 have not executed once. Root cause fixed in two ships; VM recovery left to
  the operator per their ruling (23 commits, ~22 unverified by this session, onto the live orchestrator). **This plan is
  code-shipped, NOT proven — and that distinction is the entire point of the reconciliation that produced it.** The
  source issue docs (`ao_fleet_stall…`, `dispatcher_role_eligibility…`, `ao_operator_message_silent_drop…`) are at zero
  open todos and are deliberately NOT archived until Phase 3 passes. Full finding + recovery commands:
  `issues/ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md`.
- **2026-07-16 15:08Z (deployed + first reading)** — Operator deployed the VM (and separately repaired a root-PM
  divergence — the clone the AO backend reads plans from, a second staleness with the same blast radius). The 2026-07-16
  dispatch fixes executed on the fleet for the FIRST time at 15:01:12. Deploy is clean (0 errors, 0 tracebacks); the
  `slot_messages` migration ran once in prod and its backfill behaved. Live ticks show
  `spawned=1 … queue_satisfied: 10-13` — R1's intended shape. Baseline re-confirmed from the DB itself (954
  autospawn_succeeded / 24h vs <241 dispatches). **Phase 3 stays OPEN**: 7 minutes post-reload is fleet
  re-establishment, not steady state, and calling it proven on that would be exactly the false-completion this
  reconciliation exists to prevent. Re-measure over ≥6h. Operator is routing the durable staleness UI/alerting to a
  separate agent.

## Deferred work after 2026-07-16

Everything below is TRACKED, not dropped. Nothing here is "done enough" — each row says who owns it and why it did not
happen in this session. Read this + the Progress Log to resume losslessly.

| #   | Item                                                    | Where it lives                                                                    | Why deferred / what to do                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | ------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Phase 3 runtime verdict — the only bar that matters** | this plan, Phase 3                                                                | Fixes are LIVE (worker re-forked 15:01:12, 0 errors) and the early signal is right (`spawned=1 … queue_satisfied: 10-13`), but 7 min post-reload is fleet re-establishment, not steady state. **Needs ≥6h.** Baseline confirmed from the live DB: **954 `autospawn_succeeded` / 24h vs `task_dispatched` not in the top 8 (<241)**. Query `activity_log` (NOT `activity`) on `/var/lib/orchestrator/state.db`; the VM has **no `sqlite3` CLI** — use `.venv/bin/python3`. Gate: autospawn:dispatch ratio materially down + no idle-respawn loop on a fleet-skipped task. **Until this passes, this plan is code-shipped, NOT proven** — and the 3 source issue docs at 0 open todos stay UNARCHIVED by design. |
| 2   | **Durable park for fleet-skipped tasks**                | `issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15` (1 open todo)        | R1 made this MORE important, not less. It fixed the churn — which converts a LOUD failure (visible spawn thrash) into a SILENT one: a task every slot has skipped now simply never spawns anything and nobody is told. Same shape as `needs_operator_count` being computed and rendered nowhere. Out of scope for this plan (dispatch correctness); needs its own.                                                                                                                                                                                                                                                                                                                                             |
| 3   | **Recovery-audit Layer-1 producer rewire**              | `issues/ao_recovery_audit_layer1_deleted_2026_07_15`                              | Operator ruled **B (re-home a standalone producer), scheduled LAST** — after the AO dispatch work. That work is now done, so this is next in that queue. ~90% already exists (contract + ingest + actuation + UI); only the producer is gone. The automated `DISPUTE→SAFE_MODE` tripwire does not fire until it lands.                                                                                                                                                                                                                                                                                                                                                                                         |
| 4   | **Staleness UI surface + alerting**                     | `issues/ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16` (todo 3)      | **Operator is routing this to a dedicated agent** (2026-07-16). Do NOT start it from here without checking with that owner. Requirement of record: a SINGLE frozen clone must raise a WARN — today's dirty-streak alert only fires when EVERY repo in a sweep is dirty, which is why a 2-day outage was invisible.                                                                                                                                                                                                                                                                                                                                                                                             |
| 5   | **Audit every host for the same freeze**                | same doc (todo 4)                                                                 | The gitignore + ff-pull fixes stop RECURRENCE, but a clone already frozen stays frozen (self-sustaining). Main's own checkpoint reports host `hk` "behind 12→20→49, FOUR repos" — check whether it shares this root cause.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 6   | **Prove the deep `plan-reconciler`**                    | `issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10` (3 open)        | The keystone: its proving dispatch was due **2026-06-17** and is ~1 month overdue; it gates the RULE-11 retire of 3 overlapping hygiene runtimes. It runs AS an AO worker, so it was correctly gated behind AO dispatch correctness — **which is now shipped**, so it is unblocked. NB its 2026-06-12 audit findings are STALE (the daily Haiku GHA is 10/10 green, the Cloud Run sweep 8/8).                                                                                                                                                                                                                                                                                                                  |
| 7   | **capability_wizard reconciliation**                    | `issues/capability_wizard_{analysis_findings,gap_discovery}_2026_06_11` (41 open) | **Verified OUT of AO scope** — 1 of 41 todos touches agent-orchestrator and it is already fixed. The wizard is alive and shipping; ~25 of 41 todos are already done and never checked off. Needs its own reconciliation pass before anyone dispatches against it.                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 8   | **uv-cache dual-path reconcile**                        | `ao_host_disk_pressure_2026_07_16` (1 open, P2)                                   | Cosmetic: both caches sit on the same filesystem so dedup is unaffected. Documentation-vs-reality drift, not a disk-pressure driver.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

## Deferred work after 2026-07-17

Session scope was AO correctness: the backlog prune, the Details-tab/DB divergence, the P0 runtime verdict, and a
skeptical audit of five "done-but-still-open" issue docs. Separating the KINDS of not-done, because they need different
responses:

| #   | Item                                                                    | State / why deferred                                                                                                                                                                 | Blocked on            |
| --- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| 1   | **Reopen the 2 confirmed false-`done` rows** (`l2_book…-005`, `-007`)   | **Operator-owned.** Verified live (VM db + LDR). Reopening requeues them for dispatch — a live state change, not bookkeeping. The gate fix means a reopen now STICKS.                | operator ruling       |
| 2   | **58 unauditable `done` rows** (`brief_hash` NULL)                      | **Not done.** Unknown ≠ clean; `gate_on_depends` trusts them. Backfill `brief_hash` or rule the tail out of scope with a recorded WHY.                                               | nobody — pick it up   |
| 3   | **Durable park for the sports chain** (P1 above)                        | **Operator-owned (Ikenna).** Root cause found: the recipe DOES stick (`mvp_backfill_defi_onchain_v10-002` proves it); `-002` was never parked, `-001`'s flag was flipped TRUE early. | sports Phase-6 freeze |
| 4   | **`escalation_pipeline_mvp` — un-pause?**                               | **Operator-owned.** Paused by YOUR 2026-06-26 epic-level ruling. Its `depends_on` is STALE (the broker was archived as NOT-REQUIRED) so it is not actually blocked.                  | operator ruling       |
| 5   | **`/api/escalate` vs proposed `/api/escalation/{id}` name collision**   | **Not done.** Two unrelated concepts one character apart (CI-wall judgment dispatch vs operator escalation). Resolve BEFORE writing escalation code.                                 | (4)                   |
| 6   | **Backlog-relations UI**                                                | **Cannot be done yet.** Brief + real data + a 100-task synthetic fixture handed to the design agent; implementation waits on a design.                                               | design agent output   |
| 7   | **`ORCHESTRATOR_DB_PATH` is in the systemd unit but NOT `.env.local`**  | **Not done.** Shell-run tooling therefore resolves `config.db_path()` to the EMPTY in-repo db. Same footgun family as the incident below — it bit me twice while diagnosing it.      | nobody — pick it up   |
| 8   | **07-12 degradation onset** (`worker_polling_dead` 0→587; 0.6:1 → 44:1) | **Not done.** Never root-caused. The churn is fixed, but WHY it started that day is unexplained — a repeat is undetected until it hurts.                                             | nobody — pick it up   |

**Recommended NEXT: (1) then (2).** Item 1 is two API calls and it makes the ledger honest for the first time — and it
is only worth doing NOW, because before today's gate fix a reopen decayed within minutes. Item 2 is the same question
for the other 58 rows and is the last place a false `done` can still hide.

## Lessons — carry these, they cost real time

- **A downloaded snapshot is stale the instant it lands.** Used for history, never for "is it working now". I answered a
  live question from an 18h-old db copy and got corrected. Worse: my false-`done` audit read plan checkboxes from a
  LOCAL checkout that was **3 commits behind LDR** — a todo flipped upstream would have been FALSELY accused. Always
  read plans at `origin/live-defi-rollout` (the ref the regen itself uses). The promoted `audit_false_done.py` encodes
  this as trap 1.
- **"Zero errors" in an IDLE window proves nothing.** db-locks looked fixed at 0/30min while the fleet was doing
  nothing. The real proof needed a BUSY window — and the honest finding was that locks cluster at **deploys**, not load:
  15/18/19h (my push windows) had 22/44/102 locks; 16/17h were equally busy with 0. Pick the window by the MECHANISM,
  not by convenience.
- **Raw counts mislead; ratios don't.** The 20:00 hour fired 17 spawns and looks like churn — until you see 19
  dispatches. Churn is spawns DECOUPLED from dispatches. Pre-fix 87 spawns/0 dispatches; post-fix 31/37.
- **The exit code is not the tail.** `bash gate.sh | tail` shows the tail's status, not the gate's. Read `$?` from the
  gate. This bit three times in one session.
- **A test can pin the bug.** `assert loop2._db_path is None` guarded "prune nothing", two lines under a comment saying
  the server "prunes zombies by default". A green suite is not evidence the contract is right. Bug-inject to prove a
  test is load-bearing — three of mine passed with the fix deleted.
- **Loud ≠ read.** The prune screamed `no such table: tasks` **393 times in 7 days** and reported `RegenSummary(...)` as
  success on the same tick. A WARNING inside a loop that then logs success is functionally silent. If a failure can
  never self-heal, it is an ERROR that names the fix.
- **Two names for one concept WILL drift.** `ORCHESTRATOR_DB_PATH` (systemd) vs `ORCHESTRATOR_REGEN_DB_PATH`
  (.env.local) diverged when the db moved, and the second only existed to paper over a bad default. The durable fix was
  DELETING the second, not correcting it.
- **My own correction**: I twice told the operator a wrong story about the 250→84 drop — first "a graveyard of the AO's
  completed work" (wrong), then a self-contradiction (claiming ticking `[x]` deletes rows while also saying `done` rows
  are kept forever). The truth: the prune only ever deletes `queued`/`blocked`; **all 145 queued rows had
  `dispatched_to=NULL` — never handed to a worker**. The work was done AROUND the AO, and its rows went stale. If that
  number resurfaces, this is the correct account.
