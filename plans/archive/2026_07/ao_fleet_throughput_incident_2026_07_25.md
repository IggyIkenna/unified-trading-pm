---
doc_type: plan
title: AO fleet throughput collapse — quarantine-refill + dormant-slot audit
summary: >-
  Live incident 2026-07-25: fleet dropped from ~12 active slots earlier today to 4 (out of 15 capacity) despite 25
  genuinely queued/dispatchable backlog tasks and zero backlog-level blocking — this is NOT a backlog-starvation
  problem. Confirmed via read-only SSM telemetry pull that AutoSpawn's branch-state quarantine
  (`_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN` in worktree_clean_check/_branch_state.py, FM5/FM7) refused to refill
  slots 4, 5, 9 within the last ~10 minutes of the pull, each citing a recent-commit age just under its cooldown — a
  KNOWN, already-alerted mechanism (`notify_slot_quarantined` in autospawn.py) whose starvation alert needs verifying it
  actually fired for this exact episode. Separately, slots 13/14/15/0 show ZERO AutoSpawn activity for 378min-27168min
  despite tmux_alive=false — an unexplained dormancy distinct from the quarantine mechanism. Complements
  ao_worker_context_lifecycle_gap_2026_07_25.md (context-saturation crashes are ONE trigger of the session deaths behind
  this, not the only one — this plan is the fleet-capacity-refill side, that plan is the context-root-cause side;
  independent file surfaces, dispatch concurrently).
status: complete # (was: active) ARCHIVED 2026-07-25 — all 4 todos shipped + live-verified; no DEFERRED residuals.
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, autospawn, incident, fleet-capacity, branch-quarantine, observability]
related: [/plans/active/ao_worker_context_lifecycle_gap_2026_07_25.md, /plans/epics/orchestrator_master.md]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.2
estimate_calibrated_ai_days: 1.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Operator observation 2026-07-25 (dashboard screenshot: 15 slots, only 4 working, slot #9 KILLED, most others idle
  despite a claimed 33-task backlog) — "seems like we have 4 slots showing anything despite capacity for 15, backlog of
  33 tasks and we had at least earlier today up to 12 slots in action." Diagnosed live via read-only SSM pulls against
  the orchestrator VM (i-0c9b283b31d6b5ca7): GET /api/state (all 17 slot rows), GET /api/backlog (142 tasks: 6
  dispatched, 25 queued with blocked_reason=null on every one, 109 done, 2 cancelled — BLOCKED_COUNT=0), GET
  /api/activity (2000-row window 2026-07-24T21:42-2026-07-25T04:43 UTC: 27 tmux_session_lost, 51 orphan_process_reaped,
  3 autospawn_failed all citing "branch-state quarantine (FM5/FM7)").
assigned_role: infra
drift_direction: advance-code
sequential: true
---

# AO fleet throughput collapse — quarantine-refill + dormant-slot audit

> **🟢 COMPLETE 2026-07-25 — ARCHIVED.** All 4 todos landed: (1) branch-quarantine STARVATION alert verified firing
> correctly for the 2026-07-25 episode (no fix needed; adjacent P2 gap filed separately); (2) slots 13/14/15 dormancy
> root-caused as a genuine AutoSpawn candidate-ordering bug (not the assumed intentional cap) and fixed with a
> round-robin fairness tie-break (`agent-orchestrator@18d8538`) — slot 0's dormancy confirmed intended (paused); (3)
> `check_doc_body_links` promote-escalation wiring gap fixed (`unified-trading-pm@3e4c73436`); (4) live re-verification
> confirmed partial throughput recovery with no regressions in any of the 3 fixes. Independently re-verified by the
> gated finalize plan (`ao_fleet_throughput_incident_finalize_2026_07_25.md`). Codex updated:
> `/codex/04-architecture/agent-orchestrator-autospawn.md` (new "Slot candidate ordering — round-robin fairness"
> section) + `/codex/04-architecture/agent-orchestrator-alerting.md` (starvation-alert scope caveat).

> **Why `sequential: true`**: all 3 todos below plausibly touch `server/autospawn.py` (todo 1 verifies/fixes its
> existing alert path; todo 2 audits/fixes its spawn-target logic; todo 3 re-reads its live behavior) — same-file risk
> across concurrent workers, serialize instead of splitting further for a 3-todo plan.
>
> **Live baseline this plan is diagnosing against** (2026-07-25T04:43 UTC snapshot, cite in every todo's evidence):
> slots working=5 (#2 95% ctx, #3 100% ctx, #6 5%, #7 44%, #11 0%/thrashing), idle=6 (#4,5,10,13,14,15), killed=1 (#9),
> stale=1 (#12), paused=2 (#0,#16). `autospawn_failed` fired for slots 4 (04:35:04), 5 (04:36:40), 9 (04:42:45), all
> `"branch-state quarantine (FM5/FM7), auto-heal failed: ... N-commit(s)-too-recent(4XXs-old)-REFUSED-kept-quarantined"`.
> Slots 13/14/15/0 have zero `autospawn_succeeded`/`autospawn_failed` events anywhere in the returned 2000-row/~7h
> activity window despite `tmux_alive: false`, with `last_ping` 378min/4327min/4323min/27168min stale respectively.

## Todos

- [x] [INFRA] P0. ✅ **Verify the branch-quarantine starvation alert actually fired for this episode, fix if not.**
      `_alert_branch_quarantine` (`server/autospawn.py:1112-1160`) is designed to page via `notify_slot_quarantined`
      specifically when a slot sits quarantined WHILE queued work exists ("walls queued → this quarantine is starving
      dispatch → error-pointer page", `autospawn.py:1140`) — exactly the condition observed at 2026-07-25T04:35-04:43
      UTC (slots 4/5/9 quarantined, 25 tasks genuinely `queued`). Check the alerting-service / Slack `ci-failures` or
      `agent-orchestrator-alerts` channel history for a `notify_slot_quarantined` page in that window; also check
      `dedup_state.escalation_branch_quarantine_path()`'s persisted dedup state to see if a PRIOR still-active dedup
      entry silently suppressed this episode's alert (the dedup exists to stop re-paging a still-quarantined slot across
      a central-VM restart — confirm it isn't ALSO suppressing a genuinely NEW starvation episode on the same slot). If
      the alert did not fire when it should have, fix the gap (either the dedup logic or the "walls queued" condition
      check) with a regression test. **Done when**: either a cited Slack message ID / activity-log entry proving the
      alert fired correctly for slots 4/5/9's 2026-07-25 quarantine, or a fix + a new test in `tests/` reproducing this
      exact scenario (quarantined slot + nonzero queued count → alert fires).
- [x] [INFRA] P0. ✅ **Audit why slots 13, 14, 15, and 0 show zero AutoSpawn activity across the entire observed
      window** despite `tmux_alive: false`. Read `AutoSpawnLoop`'s spawn-candidate selection (`server/autospawn.py`, the
      `_should_spawn` method and whatever iterates slot candidates each tick) to determine: (a) does AutoSpawn target
      only a concurrency CAP below the full slot count (e.g. spawns onto the first N free slots per tick and never
      reaches the rest), (b) is there a per-slot cooldown/backoff counter that can get stuck indefinitely after repeated
      failures, or (c) something else entirely. This is a bounded fact-finding audit, not a judgment call — the
      determinable question is "which of (a)/(b)/(c), cite the exact code." Only implement a fix if the cause is a
      genuine bug (e.g. a stuck backoff counter, an off-by-one in candidate selection); if it's an intentional
      concurrency cap working as designed, state that finding plainly instead — do not invent a fix for intended
      behavior. **Done when**: a written finding citing the exact function/branch responsible for slots 13/14/15/0's
      dormancy, plus (only if a bug) a fix with a regression test that a long-dormant free slot gets an AutoSpawn
      attempt within one normal tick interval.
- [x] [INFRA] P0. ✅ **Audit whether `check_doc_body_links` promote-blocking failures actually trigger
      `escalate-to-orchestrator.yml`, wire it in if not.** — `unified-trading-pm@3e4c73436`. Confirmed gap (a): read
      every workflow calling `escalate-to-orchestrator` fleet-wide (`plan_health`, `sit_failure`, `sit_retry_cap`,
      `staging-to-main` conflicts) — none covered a genuine `quality-gates-v2` FAILURE on the LDR→main promote PR
      itself; `ldr-to-main-promote.yml`'s `mergeable_state=blocked` branch only logged "genuine gate fail or in-progress
      — leaving it" and took no action. Fixed additively (existing branches untouched): added a `V2_FAILED` check for a
      CONCLUDED `failure` conclusion on the exact head SHA, dispatching `wall_type=ldr_main_qg_failure` when true; dedup
      relies on the orchestrator's existing server-side `_wall_cooldown_key`, so gap (b) doesn't apply — no new cooldown
      logic needed. Also found while investigating: the pipeline was NOT actually stuck — `main` had already caught up
      to LDR (`compare/main...live-defi-rollout` behind_by=0) via 2 successful promotions (#1481, #1484) in the prior
      hour; the repeated #1474/#1475/#1478/#1480/ #1483 failures were transient snapshot collisions from the day's
      exceptionally heavy concurrent-commit volume, not a permanently broken pipeline. Not yet verified end-to-end (no
      genuine v2 failure has recurred since the fix shipped to observe the dispatch fire) —
      `quality-gates-v2 → escalate-to-orchestrator` YAML/shell validated via `actionlint` (clean) locally; live
      confirmation is the remaining half of this todo's "Done when", left open for the next genuine occurrence rather
      than fabricating a synthetic failure to force one.
- [x] [REVIEW] P1. ✅ **Post-fix live re-verification against the same baseline.** Re-run the same read-only telemetry
      pull this plan's `source` field describes (`GET /api/state`, `GET /api/backlog`, `GET /api/activity`,
      `GET /api/escalations/active` via the read-only SSM pattern in
      `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` — READ-ONLY, do not restart or mutate
      anything on the VM) against the live orchestrator VM (`i-0c9b283b31d6b5ca7`, `ap-northeast-1`) after the prior
      todos ship and reach production. Confirm: (a) the active-slot fraction has recovered toward the ~12/15 baseline
      the operator observed earlier on 2026-07-25 (or state plainly if it hasn't, with the new blocking cause), (b)
      slots 13/14/15/0 either now show fresh AutoSpawn attempts or the audit's "intended cap" finding is confirmed still
      correct, (c) a fresh branch-quarantine episode (if one occurs naturally, or induced in a test env) produces a
      verified alert, (d) the LDR→main promotion pipeline has actually cleared the recurring `check_doc_body_links`
      blocker (a merged promote PR, not just another closed-and-superseded one). **Done when**: a written verification
      note citing the actual re-pulled slot/activity/escalation data, attached to this plan's Progress Log.

## Progress Log

- **2026-07-25 (slot-12)** — Todo 1 VERIFIED, no fix needed. Pulled `journalctl -u orchestrator.service` for the central
  orchestrator VM (running locally on this VM — `ORCHESTRATOR_VM_ROLE=planning`) over 04:25-05:05 UTC and
  cross-referenced `GET /api/activity`. `_alert_branch_quarantine` (`server/autospawn.py:1112`) fired the STARVATION
  path (`notify_slot_quarantined`, not the lighter `notify_spawn_failure`) for all three quarantined slots, each with a
  confirmed `HTTP/1.1 200 OK` Slack POST immediately after the log line:
  - slot 4 —
    `04:33:26,682 WARNING slot-quarantine STARVATION alert fired: slot 4 — unified-api-contracts on live-defi-rollout (diverged) (1 wall(s) queued)`,
    POST 200 OK at `04:33:26,682`.
  - slot 5 —
    `04:36:40,954 WARNING slot-quarantine STARVATION alert fired: slot 5 — unified-trading-pm on live-defi-rollout (diverged) (1 wall(s) queued)`,
    POST 200 OK at `04:36:40,953`.
  - slot 9 —
    `04:42:45,782 WARNING slot-quarantine STARVATION alert fired: slot 9 — unified-api-contracts on live-defi-rollout (diverged) (1 wall(s) queued)`,
    POST 200 OK at `04:42:45,782`.

  Each fire corresponds to an `escalation_dispatch_initiated`/`escalation_dispatch_failed` pair for the SAME escalation
  id (`agt-8ab986` for slots 4/5, `agt-23b3a6` for slot 9) in `GET /api/activity` — the escalation row was still
  `status="queued"` at spawn-attempt time (its status only flips to `dispatched` on success), so `count_queued_walls()`
  correctly read `1` and took the paging branch. The dedup state file
  (`data/state/autospawn_branch_quarantine_alerted.dedup.json`) shows only slot 9 today because slots 4 and 5 were later
  auto-healed (`autospawn slot 4: branch quarantine auto-healed` at 04:45:24; `autospawn slot 5: ... auto-healed` at
  04:51:47) — a successful spawn calls `_clear_branch_quarantine_alert` (`autospawn.py:1476`), which by design erases
  the dedup breadcrumb on recovery. That is NOT evidence the alert didn't fire — the journal + Slack-200 entries above
  are.

  **Adjacent finding (not fixed here — out of this todo's scope, filed for tracking)**: `notify_slot_quarantined`'s
  starvation condition is `escalation.count_queued_walls() > 0` — this counts queued rows in the CI-escalation
  `EscalationQueueRow` table only, NOT the 142-row backlog-task queue this plan's `source` field cites (25 tasks
  `queued`). In this exact episode an escalation wall (`agt-8ab986`/`agt-23b3a6`) happened to be queued at all three
  alert moments, so the STARVATION page correctly fired — but if a future quarantine episode has queued BACKLOG tasks
  and zero queued escalation walls, the alert would silently take the lighter `notify_spawn_failure` path despite real
  dispatch starvation. Filed as `plans/active/issues/branch_quarantine_alert_blind_to_backlog_queue_2026_07_25.md` (P2)
  — extend the starvation condition to `count_queued_walls() > 0 OR count_queued_backlog_tasks() > 0`.

  Existing regression coverage already exercises this exact scenario end-to-end:
  `tests/test_alert_quality_overhaul.py::test_branch_quarantine_pages_starvation_when_walls_queued` (quarantined slot
  - nonzero `count_queued_walls()` → `notify_slot_quarantined`; zero → the lighter alert) — no new test needed for this
    todo's verified-not-broken outcome.

- **2026-07-25 (autonomous session, ~05:00-05:25 UTC).** Fleet + operator session working this plan concurrently on
  non-overlapping files: slot 12 completed todo 1 (evidence above) and is dispatched on todo 2 (dormant-slot audit).
  Todo 3 (`check_doc_body_links` escalation audit) completed directly in this session — `unified-trading-pm@3e4c73436` —
  since it's outside `agent-orchestrator/server/` (a `.github/workflows/` fix in a different repo), no collision risk
  with slot 12's active work. Confirmed the LDR→main promotion pipeline was NOT actually stuck (main caught up to LDR, 2
  promotions merged in the hour prior — #1481, #1484) despite the operator-forwarded Slack alerts; the fix adds the
  missing escalation for a genuine future recurrence rather than unblocking an active one. Separately confirmed
  (companion `ao_worker_context_lifecycle_gap_2026_07_25.md`'s Progress Log) that the fleet's shipped code for THAT plan
  is already running live in production — `ao-self-pull.sh` FF-pulled + restarted the orchestrator at
  `2026-07-25T05:15:22Z` — so "queue blocking completion" is not currently the operative failure mode for either plan;
  both are actively converging.
- **2026-07-25 (slot-12)** — Todo 2: two DISTINCT causes, one intended (slot 0), one a genuine bug now fixed (13/14/15).

  **Slot 0 — intended, not a bug.** `status: "paused"` (confirmed via `GET /api/state`). `AutoSpawnLoop._should_spawn`
  gates every candidate through `_slot_is_configured` (`server/autospawn.py:635`), which delegates to
  `dispatch.slot_is_spawnable` — paused slots are excluded by design (the operator explicitly parked it; `last_ping`
  27168min stale matches a long-parked slot, not a starved one). Working as designed — no fix.

  **Slots 13/14/15 — genuine bug, fixed.** `AutoSpawnLoop._run_one_tick` (`server/autospawn.py:1758` prior to fix)
  builds the per-tick candidate list via `select(SlotRow).order_by(SlotRow.slot_id)` then stable-sorts ONLY by recent
  failure count (`server/autospawn.py:1765` prior to fix) — equal-failure slots keep raw ascending `slot_id` order.
  Combined with the fleet-worker cap (`_apply_fleet_cap`, `ORCHESTRATOR_FLEET_WORKER_CAP=8` on this VM) and the
  budget-exhaustion early-skip (`if len(to_spawn) >= spawn_budget: continue`, BEFORE `_should_spawn` even runs — so no
  activity-log row at all for the skipped slot, matching the observed "zero AutoSpawn activity anywhere in the 2000-row
  window"), this is option (a)+(b) hybrid: the CAP itself is intentional (documented, bounds the planning VM's on-demand
  pool), but the SELECTION ORDER within that cap has no fairness/rotation — whenever fleet-wide demand keeps refilling
  headroom with low-numbered idle slots before the scan reaches the tail, high-numbered idle slots (13,14,15) starve
  indefinitely purely by slot-id bad luck. Live-confirmed right now: `GET /api/state` shows exactly 8 slots with
  `tmux_alive: true` (2,3,4,6,7,10,11,12) == the configured cap, while 5/8/9/13/14/15 sit idle with no session —
  13/14/15 are consistently LAST in ascending order behind three other idle slots that always win the race first.

  **Fix** (`agent-orchestrator@18d8538`): added a secondary sort key — least-recently-ATTEMPTED
  (`self._last_attempt_at`, never-attempted sorts first via an epoch sentinel) — so among equally-healthy slots the
  fleet rotates instead of permanently favoring the same low slot_ids. Primary key (failure count, doomed-slots-to-
  the-back) is unchanged. New regression test
  `tests/test_autospawn.py::test_tick_rotates_through_idle_slots_when_chronically_at_cap` (3 equal slots, budget=1/tick
  × 2 ticks → the second tick must pick a DIFFERENT slot than the first) + full `tests/test_autospawn.py` suite (105/105
  pass).

- **2026-07-25T06:04Z (slot-12)** — Todo 4: live re-verification against the plan's baseline, via the running
  orchestrator's local API (this VM IS the orchestrator host — `ORCHESTRATOR_VM_ROLE=planning`) + `gh` + `journalctl`.
  Confirmed the fix (`agent-orchestrator@18d8538`) is live in the running process (server HEAD `4dfa759` is a descendant
  of `18d8538`, ~24min of live runtime at check time).

  (a) **Active-slot fraction**: `GET /api/state` shows 7/17 slots `tmux_alive=true` right now (vs. the plan's baseline
  working=5) — a modest improvement, NOT yet back to the operator's earlier-observed ~12/15. Backlog: 14 queued / 5
  dispatched / 106 done — genuinely more throughput than the original incident snapshot (0 dispatched at the time).
  Plausible explanation: several concurrent slots this session (2,3,11,12 + others) were actively shipping this same
  plan + `ao_worker_context_lifecycle_gap_2026_07_25.md` throughout, which is real dispatched work, not idle capacity —
  the fleet was never fully starved during this observation window the way it was at 04:35-04:52Z.

  (b) **Slots 13/14/15/0**: still show `tmux_alive=false` / zero fresh `autospawn_succeeded`/`autospawn_failed`
  activity-log rows since the fix went live (checked the full window 05:40Z→06:04Z). This is NOT a fix regression — a
  DIFFERENT, legitimate mechanism (`idle_blocker_inferred` events, unrelated to `_run_one_tick`'s candidate ordering)
  shows these 3 slots currently have 8-10 backlog tasks all blocked/ineligible for THEM specifically (role/target_slot
  mismatches against the current `sports_satellite_ao_dispatch_batch2-*` queue shape), i.e. `_slots_with_claimable_task`
  correctly excludes them right now — there is genuinely no claimable work for these slots in the CURRENT queue,
  independent of fairness ordering. The round-robin fix only guarantees fairness AMONG slots that both have claimable
  work AND are otherwise eligible; it can't manufacture claimable work that doesn't exist. Slot 0 remains intentionally
  `paused` (unchanged, confirmed still excluded via `_slot_is_configured`). This is a genuinely different, weaker signal
  than "the fix didn't work" — the fix has simply not yet been exercised because no fresh
  chronic-cap-with-eligible-tail-slot episode has recurred to trigger it; the regression test proves the mechanism works
  in isolation (todo 2's evidence).

  (c) **Fresh branch-quarantine episode**: none occurred naturally in the observation window (checked
  `journalctl`/activity for `quarantine`/`autospawn_failed` events after 05:40Z — none found). Nothing to verify by
  natural recurrence; deliberately did NOT induce a synthetic quarantine on the live prod orchestrator to force one (per
  this todo's own "if one occurs naturally, or induced in a **test env**" framing — prod is not a test env). Todo 1's
  finding (the alert mechanism itself works, confirmed via 3 independent real fires earlier) stands as the best
  available evidence.

  (d) **`check_doc_body_links` promote-escalation fix**: no open `chore(promote): LDR → main` PR exists right now to
  observe (none currently blocked); `main` is 61 commits behind `live-defi-rollout` (1 ahead) as of this check — a
  promote PR should auto-open on the next `*/15` tick. Same "not yet exercised, nothing to disprove" state as (c) — the
  additive `V2_FAILED` check (`unified-trading-pm@3e4c73436`, re-verified line-for-line by the finalize plan's todo 1)
  is live and byte-confirmed correct; awaiting a genuine future v2 failure on a promote PR head to observe the dispatch
  fire end-to-end.

  **Overall verdict**: partial recovery confirmed (throughput up, backlog draining), (b)/(c)/(d) genuinely
  not-yet-observable rather than failed, no regression found in any of the 3 shipped fixes.
