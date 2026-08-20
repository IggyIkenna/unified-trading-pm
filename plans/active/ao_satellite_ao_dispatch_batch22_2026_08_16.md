---
doc_type: plan
title: AO satellite AO batch 22 — conflict-clear bounded extraction from the 2026-08-16 closeout audit
summary: >-
  TWENTY-SECOND AO-dispatch batch for the `ao` topic tranche — output of a full `/ag-closeout-audit ao` Phase 0-3 run
  (2026-08-16, dispatch agt-1628ee), scoped to the 42 docs the Phase 1 Workflow classified `orphaned_never_touched`/
  `orphaned_partial_coverage` after the same run's own Phase 2 archived 10 fully-done docs directly. Of those 42, 6
  bounded, conflict-clear, file-disjoint AO-eligible todos survive direct verification against every currently-active
  covering plan (batch3/8/14/21 + their finalizes, the consolidated closeout, the false-done pair) and the
  `ao_open_work_consolidated_tracker_2026_08_14.md`/`ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md`
  in-flight work — zero hits for every candidate's basename. `orchestrator_vm_e2e_hardening_2026_07_24.md`'s
  dirty-worktree-policy deliverables (design-resolved, tracker calls it "highest-value remaining bounded work") were
  deliberately EXCLUDED here despite being bounded — it rewrites the worker prompt template + dispatch hook every
  slot spawn reads, matching this workspace's standing pattern of routing that exact class of change to a deliberate,
  human-attended session rather than casual batch-extraction; flagged prominently in this run's own report instead.
status: active # flipped from draft 2026-08-20 (interactive session, operator-approved) — todo 1-3 already MOOT (shipped elsewhere), converted to CANCELLED-SUPERSEDED markers same turn; todos 4-6 are the real remaining dispatchable work
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-22, satellite-docs, satellite-extraction]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch22_finalize_2026_08_16.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /plans/active/issues/slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md,
    /plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1.0
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /plans/active/issues/slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md,
    /plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  `/ag-closeout-audit ao` (2026-08-16, dispatch agt-1628ee, slot 15). Phase 1 classified 59 candidate docs via a 9-group
  Workflow fan-out; Phase 2 verified + archived 10 fully-done docs directly (checkbox flips backed by 16 independently
  re-verified commit SHAs + 4 direct code reads); this batch is Phase 3's extraction from the remaining 42 orphaned
  docs. Conflict-check: grepped every status:draft/active `ao_satellite_ao_dispatch_batch*` (3/8/14/21) + finalizes,
  the consolidated closeout, and the two in-flight NA trackers for each of the 6 todos' subject matter — zero hits.
---

# AO satellite AO batch 22

> **`status: active`** — operator-approved 2026-08-20. Todos 1-3 were already MOOT (shipped elsewhere) by the time of
> activation — converted to `CANCELLED-SUPERSEDED` markers the same turn (same convention as
> `ao_satellite_ao_dispatch_batch14_2026_08_09.md`'s todo 1) so AO doesn't waste a dispatch re-diagnosing a dead
> checkbox. Todos 4-6 are the real remaining dispatchable work. **`assigned_vm: planning` /
> `execution_scope: orchestrator-agent`**.

## Why this plan exists

`/ag-closeout-audit ao`'s 2026-08-16 run classified 59 non-self-covering `[ao]` docs. 12 were `archivable_now`
(evidence-backed stale checkboxes) — flipped + archived directly in the same run, not duplicated here. Of the
remaining 42 genuinely orphaned docs, most carry a real, stated reason nothing has picked them up: an undecided
design fork, an operator-only credential/live-infra action, a needs-external-engagement investigation, a time-gate on
an unmet condition, or a doc explicitly declared out of AO-dispatch scope by its own text or a standing operator
ruling. This batch extracts only the handful that are genuinely bounded, already-decided (not open design forks), and
conflict-clear.

**Explicitly excluded** (named here so nobody re-derives them as candidates without reading why — full list with
per-doc reasoning is this run's own report/parked-findings doc, not duplicated here):

1. **`orchestrator_vm_e2e_hardening_2026_07_24.md`'s dirty-worktree-policy deliverables** — design is resolved and the
   tracker calls it "highest-value remaining bounded work," but it rewrites the worker prompt template + the AO
   dispatch hook every slot spawn reads on its very first message. Matches this workspace's own standing caution
   (`unified-trading-pm@14478ca26`, invoked repeatedly across this exact tranche's audit history) that routes
   fleet-wide boot/dispatch-critical-path text changes to a deliberate, human-attended session rather than casual
   batch-extraction — flagged as a priority item in this run's report instead of drafted here.
2. **`ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md`'s 2 P3 observability extensions**
   (KPI by-slot/by-day breakdown; extend `death_class` signal coverage) — both genuinely bounded/mechanical, but the
   `death_class` extension touches `server/tmux_pruner.py`'s slot-death loop, the SAME file todo 1 below (the
   plan_reconciler reaped-stale correlation) modifies. Dropped rather than risk a same-file collision between two
   same-priority todos; lowest-value pair in this run's candidate set, safe to leave for a future batch once todo 1
   has landed.
3. Every doc in this run's report/parked-findings doc NOT named above — operator-gated, design-fork, time-gated,
   too-large-or-risky, or genuinely human-only per the non-batchable taxonomy `/ag-closeout-audit`'s own SKILL.md
   states; re-triage on the NEXT `/ag-closeout-audit ao` run per that skill's own iterative-drain methodology, not
   re-derived here.

## Rules for every worker on this plan

- The 6 todos below are file-disjoint (different repos/modules) — safe to run concurrently, no `sequential: true`.
- Todo 1 is cross-repo (agent-orchestrator code + a PM-repo lock-clear write) — both halves are part of the SAME
  todo's done-when, do not split across two dispatches.
- Todos 3, 5, and 6 touch dispatch/liveness-adjacent machinery (`plan_health.py`'s `dispatch()`,
  `worker_liveness_watchdog.py`/`worker_liveness/__init__.py`, `autospawn.py`'s `ensure_review_agents`) — the SAME
  class of fix already shipped successfully via normal AO dispatch earlier today (this run independently verified 5
  such commits: `agent-orchestrator@349dbc04`, `@eb4265c5`, `@ff490c75`, `@2f94a90e`, `@3f5b10a7`), so this is
  consistent with today's own precedent, not a novel risk class for this dispatch path.

## Todos

- **[BACKEND] P1. CANCELLED — SUPERSEDED 2026-08-20 (interactive session, operator-approved batch22 activation) —
      already shipped elsewhere (see evidence below); converted from an open checkbox to this marker per
      `task_template.md` §3's CANCELLED/SUPERSEDED disposition, same convention as
      `ao_satellite_ao_dispatch_batch14_2026_08_09.md`'s todo 1 — do not redispatch.** Wire the `plan_reconciler`
      PM-repo lock-clear into AO's reaped-stale detection path (ruled Option A, 2026-08-15). When a PM-repo doc's `locked_by: plan_reconciler (agt-xxxxxx) since <ts>` correlates to
      an AO `AgentRow` whose `exit_reason` resolves to `reaped-stale` (or the agent is confirmed gone with no live
      tmux session) AND `locked_since` is older than a generous same-day threshold (6-12h — clears a same-day dead
      lock without racing a still-legitimately-running worker), auto-clear the PM-repo lock. Build either an AO-side
      periodic sweep or a PM-side hygiene script calling a new read-only AO endpoint — implementer's choice, per the
      doc's own Option-A framing. **Done when**: a dead-locked `plan_reconciler_findings_<tranche>_<date>.md` with a
      reaped-stale-correlated `locked_by` auto-clears within the chosen sweep's cadence, with a test proving a
      still-live dispatch is NOT cleared. **✅ Already shipped** — `agent-orchestrator@bfe8fb28a0`
      (`PlanReconcilerDeadLockSweep`, `server/plan_reconciler_dead_lock_sweep.py`), landed directly against the
      source doc, this todo is now MOOT. Source (historical): `/plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`
      todo "[BACKEND] P1. Implement Option A auto-clear". Durable contract:
      `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § "PM-repo dead-lock correlation…".
- **[DOCS] P3. CANCELLED — SUPERSEDED 2026-08-20 (interactive session, operator-approved batch22 activation) —
      already shipped elsewhere (see evidence below); converted from an open checkbox per the same
      `task_template.md` §3 disposition as todo 1 above — do not redispatch.** Ensure `plan_reconciler`'s own
      lock-stamping step always includes the dispatch id + timestamp.
      2 of 4 dead 2026-08-09 docs (and a 3rd independently reproduced 2026-08-15, sports tranche) stamped a bare
      `locked_by: plan_reconciler` with no `(agt-xxxxxx) since <ts>` suffix, making dead-session correlation
      impossible for those rows even once todo 1 ships. Audit `cursor-configs/skills/plan-reconcile/SKILL.md`'s
      lock-stamping step for why it sometimes skips the suffix and fix it to be unconditional. **Done when**: every
      `plan_reconciler`-authored `locked_by:` stamp in a fresh run carries both the dispatch id and a timestamp,
      verified against 2+ live runs. Source (historical): `/plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`,
      finding 6 + its `[INFRA] P3` todo. Repo: unified-trading-pm. **✅ Already shipped** —
      `unified-trading-pm@<see that doc's own resolved commit>` fixed the ACTUAL lock-stamping step, which turned out
      to live in `agents/plan_reconciler.md` STEP 2b, not `cursor-configs/skills/plan-reconcile/SKILL.md` as this
      todo's own text assumed (SKILL.md never contained that step — a misleading pointer this fix also corrected at
      the source). This todo is now MOOT.
- **[BACKEND] P1. CANCELLED — SUPERSEDED 2026-08-20 (interactive session, operator-approved batch22 activation) —
      already shipped elsewhere (see evidence below); converted from an open checkbox per the same
      `task_template.md` §3 disposition as todo 1 above — do not redispatch.** Pre-dispatch duplicate-tranche
      live-lock check in `plan_health.py`'s `dispatch()`. A second
      same-day `tranche=X` `plan_reconciler`/`ag_closeout_auditor`/etc. worker can currently be spawned while a first
      worker for the SAME `(tranche, date)` is still alive and holding its findings-doc lock (live 2026-08-16
      instance: `agt-053eab` spawned into `tranche=ao` while `agt-3eb42b` was still active on the identical target).
      Before `autospawn.do_spawn()`, check `plans/active/issues/plan_reconciler_findings_<tranche>_<today>.md` (or the
      relevant family's findings doc) for a live `locked_by:`, or an AO-side non-terminal `AgentRow` for a prior
      dispatch matching the same tranche+date, and skip/queue the new dispatch instead of spawning a collision.
      **Done when**: a second same-day same-tranche dispatch attempt is refused or queued while the prior worker's
      lock is confirmed live, with a regression test. Source (historical):
      `/plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`, the 2026-08-16 `[BACKEND] P1`
      finding ("New gap found live 2026-08-16"). Repo: agent-orchestrator. **✅ Already shipped** —
      `agent-orchestrator@bfe8fb28a0` (`_tranche_dispatch_gate`/`_last_tranche_dispatch`,
      `server/plan_health.py`) — generalized across `reconcile`/`na_eligibility`/`ag_closeout`, so it also covers
      `ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 2's identical `na_eligibility` gap. This todo is now MOOT.
- [x] ✅ [DOCS] P3. ~~Batch the `/poll` + blocked-queue check in `agents/main.md`'s per-tick loop.~~ **ALREADY SHIPPED
      `unified-trading-pm@f637aed3cf`** — done directly while resolving the source issue doc (this plan was never
      activated from `status: draft`, so it held no live lock on the work). STEP 2A + STEP 2.5 now cross-reference
      each other with an explicit "fire together, same turn" instruction; the `/loop` and CronCreate prompt templates
      updated to match; the full STEP sequence was grepped for the same shape (no other fix needed there) and one
      further instance was found + fixed in the "Overnight autonomous operation" loop's steps 1/2/5 (same redundant
      `/api/state` re-fetch pattern). Do NOT redispatch this item. Source (now archived):
      `/plans/archive/issues/ao_main_agent_heartbeat_loop_teaches_non_batching_2026_08_14.md`. Repo: unified-trading-pm.
- [x] [BACKEND] ✅ P2. **Escalate a wedged `tmux_alive=true` + `worker_alive=false` + `phase=pre_boot` slot from indefinite resume-kicks to a kill+respawn.** Confirmed live incident (slot 2, 2026-08-04): the
      WorkerLivenessWatchdog kept sending `watchdog_heartbeat_resumed` kicks every ~17-18min for 1.5h+ without ever
      escalating, and a concrete task-oriented nudge via `/api/slots/{id}/message` could NOT clear it (dispatch will
      not route a task to a slot it marks `pre_boot`/`worker_alive=false` — a worker-facing nudge is structurally the
      wrong tool). Add an escalation path: after N consecutive `watchdog_heartbeat_resumed` kicks or a wall-clock
      bound on a slot stuck in this exact state, force a kill + let AutoSpawn give it a clean respawn — same shape as
      the account-blocked escalation counter shipped earlier today (`agent-orchestrator@aebc1ea36a`,
      `_consecutive_account_blocked_ticks`), alert-only-then-escalate, never a blind force-kill. Also reconcile the
      `phase=pre_boot`/`worker_alive=false`-vs-alive-pane bookkeeping mismatch if it's the same root cause. **Done
      when**: a slot reproducing this exact state (mocked) escalates to kill+respawn within the bounded threshold,
      with a regression test; a currently-healthy slot's normal resume-kick cadence is unaffected (a negative test).
      Source: `/plans/active/issues/slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md`. Repo:
      agent-orchestrator@609d044b8f + evidence: isolated quickmerge QG passed (5284 passed, 4 skipped; coverage 86.1203% > 85.8559% baseline).
- [ ] [BACKEND] P3. **Harden `ensure_review_agents`/the AgentKeeper reap path to positively verify a review slot's live session is actually running the `review` prompt, not just any live session.** The 2026-08-16
      `human_claim`/`human_claim_check` guard fix (already shipped, `agent-orchestrator@d13788ec2f`) closes the ENTRY
      point — nothing should bind an ordinary task onto a reserved review slot again — but does not add a
      detect-and-recover path if a review slot ends up wedged by some other future mechanism, since the reap path
      currently treats any review slot with `tmux_alive: True` as "something is running, leave it alone" regardless
      of whether that something is genuinely review's own boot loop. **Done when**: `ensure_review_agents` (or the
      AgentKeeper reap path) distinguishes a genuinely-running review session from a stray non-review session
      occupying the reserved slot, with a regression test covering both cases. Source:
      `/plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md`, todo "[BACKEND] P3. Second,
      independent gap noted but not chased". Repo: agent-orchestrator.

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`, `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md`,
`/codex/04-architecture/agent-orchestrator-worker-liveness.md`.

## Progress Log

- **2026-08-20 (slot 18)**: Implemented and shipped the bounded pre-boot resume-budget escalation and regression coverage in `agent-orchestrator@609d044b8f`; isolated quickmerge passed 5284 tests with coverage 86.1203% above the 85.8559% baseline.

- **2026-08-16 (ag_closeout_auditor, dispatch agt-1628ee, autonomous)**: Drafted per `/ag-closeout-audit ao`'s Phase 3
  — 6 conflict-clear, file-disjoint, bounded todos extracted from the run's 42 orphaned-doc population after Phase
  1-2 archived 10 fully-done docs directly. `status: draft` per autonomous-mode safety rail; flipping to `active`
  is an operator decision.
- **2026-08-20 (interactive session, operator-approved)**: Reviewed for AO-dispatch readiness. Todos 1-3 were each
  already independently shipped elsewhere by the time of this review (their own text already said so, but the
  checkboxes were never flipped) — converted each to a `CANCELLED-SUPERSEDED` marker (same disposition convention
  `ao_satellite_ao_dispatch_batch14_2026_08_09.md`'s todo 1 already established) so `regen_backlog_from_plan.py`
  stops re-deriving dead dispatchable tasks from them. Todo 4 (already `[x]`, shipped `unified-trading-pm@f637aed3cf`)
  and todos 5-6 (real, open, bounded work) are unaffected. Flipped `status: draft` → `active` — operator approved
  activation now that the plan's live remainder is exactly 2 genuinely bounded, conflict-clear todos.
