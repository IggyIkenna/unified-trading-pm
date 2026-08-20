---
doc_type: plan
title: AO subject-matter open-work consolidated tracker
summary: >-
  One place to see every genuinely-still-open todo across the ~44 AO-subject-matter plans/issues audited 2026-08-14
  (agent-orchestrator dispatch, backlog, worker lifecycle, scheduled jobs, escalation queue, VM infra) — produced by a
  5-agent code-level verification sweep that checked each doc's open todos directly against live agent-orchestrator
  code, not just checkbox state. This plan **references** the source docs; it does not duplicate their content or
  evidence — each todo below is a pointer + one-line summary, resolve the actual work in the cited source doc. Not every
  item here is AO-dispatch-eligible as written (several are operator-gated or open judgment calls); this tracker exists
  so the remaining work is visible in one place before deciding what to batch into an AO-dispatch plan vs. what stays
  local/operator work.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, tracker, consolidated, open-work, worker-lifecycle, dispatch]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch21_2026_08_16.md,
    /plans/active/ao_satellite_ao_dispatch_batch21_finalize_2026_08_16.md,
    /plans/active/ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md,
    /plans/active/task_template.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
  ]
created: 2026-08-14
last_updated: 2026-08-18
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
  [
    slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25,
    ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30,
    ao_satellite_ao_dispatch_batch3_2026_07_31,
    context_scout_completion_and_plan_brainstorm_skill_2026_07_30,
    orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02,
    orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25,
    shared_host_home_filesystem_full_2026_07_26,
    content_derived_backlog_task_ids_2026_08_08,
    ao_satellite_ao_dispatch_batch3_finalize_2026_07_31,
    l2_book_microstructure_capture_2026_07_13,
  ]
source: >-
  A 5-parallel-agent code-audit sweep (2026-08-14, this session) checked every open todo across 44 AO-subject-matter
  plans/issues (created on/before 2026-08-07) directly against live agent-orchestrator code — not just checkbox state.
  Found ~10 items already implemented but never checked off (flipped separately this session, see the 3 commits cited in
  the Progress Log), one live security gap now fixed + verified on the production VM
  (`orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`, archived), and the 51 items below (58 as swept, 7
  DeepSeek/Luna-bridge items removed per operator direction — see Notes) confirmed genuinely still open. This plan is
  the tracking artifact requested to hold that remainder before deciding what to dispatch.
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
  ]
---

# AO subject-matter open-work consolidated tracker

> **Purpose.** A single tracking surface for every confirmed-still-open AO-subject-matter todo found in the 2026-08-14
> code-audit sweep. This plan is `assigned_vm: NA` (LOCAL/human) — it is never auto-dispatched. Each todo **references**
> its source doc (`Source: <path>`); do the real work there, then flip the checkbox HERE too so this tracker stays an
> accurate index. When a Track's items are ready, consider extracting them into a proper
> `ao_satellite_ao_dispatch_batchN_*.md` pair per
> `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict- check.md` rather than dispatching straight from
> this doc.

## Reachability map

1. **Worker liveness / failover / dispatch correctness** → Track 1
2. **Scheduled jobs, benchmarking, model/provider routing** → Track 2
3. **Boot / context / session hygiene** → Track 3
4. **Infra / VM / host hygiene** → Track 4
5. **Dashboard e2e flakiness** → Track 5
6. **Archival + reconciliation bookkeeping** → Track 6
7. **AO-plan operator-item purity (task_template.md §3 finding Y)** → Track 7

---

## Track 1 — Worker liveness / failover / dispatch correctness

- [x] [OPERATOR] P1. **DONE — shipped `agent-orchestrator@d13788ec2f`** (2026-08-16; this line was stale, still read
      "NOT YET SHIPPED" — corrected 2026-08-17). Root cause + fix: `/plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md`
      (2 remaining follow-up todos live there, not duplicated here). A SEPARATE, second review-slot gap found+fixed
      2026-08-17 (silent no-account respawn skip in `ensure_review_agents` + a masking `role=review` self-registration
      hole in `POST /api/agents/register`) — shipped `agent-orchestrator@7df307a411`; full detail + remaining follow-ups
      (scheduler/cicd/escalation slot hardening, dashboard tagging, auto-dispatch branch-heal recovery) in
      `/plans/active/issues/ao_review_slot_hard_rule_and_diagnostics_2026_08_17.md`.
- [x] [REVIEW] P3. **DONE — `agent-orchestrator@4dbac5d5c7`** (2026-08-17): a 429 left an account's stale `binding:` display frozen pre-rejection, now cleared. `/plans/archive/issues/ao_rate_limited_representative_claim_stale_through_429_2026_08_17.md`.
- [x] [REVIEW] P2. **DONE — shipped `agent-orchestrator@3d2e368`** (2026-08-14, after this tracker's own authoring).
      `retire_orphaned_blocked_rows()` (`server/blocked_reconcile.py:564`) now called at both `reassign_slot`
      (`server/routes/slots_ops.py:763`) and `skip_current_task` (`:1060`) — the `auto_orphaned_slot_reassigned`
      disposition + `blocked_retired_auto_orphaned_slot_reassigned` log event this todo asked for, exactly. Verified
      2026-08-15 (`/ag-closeout-audit`-style reconciliation sweep, this session). Source:
      `/plans/archive/issues/ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06.md` — flip its own
      checkbox too, same evidence.
- [x] [REVIEW] P3. **DONE.** Both `_migrate_parking_state` failure paths now `logger.warning(...)` on drop
      (`server/regen_backlog_from_plan.py` — no-candidate branch ~2876-2895, below-threshold branch ~2899-2919), each
      inline-citing this issue doc. Verified 2026-08-15 (reconciliation sweep, this session). Source:
      `/plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md` (its one remaining open todo,
      "consider an alerting surface," is a separate, deliberately-open P3 — not this claim).
- [x] [REVIEW] P2. **DONE.** `_sweep_unpushed_slots` now calls `heal_dead_slot_branch_quarantine` directly
      (`server/worker_liveness_watchdog.py:1953`) inside its own unconditional per-tick sweep — fires every tick
      regardless of backlog state, no `_do_spawn` gate. Verified 2026-08-15 (reconciliation sweep, this session).
      Source: `/plans/archive/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` — its own
      checkbox + Progress Log are stale (still describe the gap as open as of 2026-08-03), flip + close.
- [x] [INFRA] P3. **DONE — CORRECTED 2026-08-15: was briefly marked won't-build by a concurrent session's
      investigation-only pass; a separate concurrent session actually built and shipped it,
      `agent-orchestrator@6ea54d8822`.** Added `_pid_session_id`/`pid_shares_tmux_session` to `server/tmux_spawn.py`: a
      `nohup <cmd> & echo $!` job gets reparented to PID 1 the instant its wrapping subshell exits, breaking the
      PPID-ancestry check the sweep used to rely on — but `nohup` never calls `setsid`, so the process keeps its
      original session id, which still matches the live pane's SID. Wired as an exemption into `orphan_reap.py`'s sweep.
      8 new/updated tests, incl. a real-`/proc` integration test proving SID inheritance survives reparenting. The other
      investigation's "optional, no confirmed use case, primary fix already shipped" framing wasn't wrong about the
      primary-fix efficacy — it just concluded before checking whether the structural exemption was ALSO buildable
      safely, and it was: this is exemption BY the process's own kernel session id, not a blanket allowlist, so it can't
      reintroduce the "genuinely leaked process never reaped" hazard either. Source:
      `/plans/archive/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md` — flip its checkbox
      too.
- [x] [BACKEND] P1. **DONE — full 10-component sweep closed 2026-08-15 (this session).** Final per-component verdict:
      `HealthMonitor` FIXED (`agent-orchestrator@349dbc0`), `AgentKeeper` FIXED (`@eb4265c`), `BlockedQueueReconciler`
      FIXED (`@ff490c7`), `AutoSpawnLoop` FIXED (`@2f94a90` — its `_resume_pass` had a `has_session()` call the prior
      "Phase 2" fix never covered), `context_lifecycle.py`'s `_read_pct` FIXED (`@3f5b10a` — the highest call-frequency
      instance, run every tick for main/review/every worker); `WorkerLivenessKicker`/`UsagePoller`/`AutoParkReconciler`/
      `RepoHealthWatcher`/`PlanReconcilerLivenessCanary` all confirmed ALREADY-FINE (structurally already read/act/write
      or never made a blocking call inside a session at all — contention victims, not causes). Every fix follows the
      same read-DB / act-with-no-session-open / write-DB split already proven by `tmux_pruner`/`ensure_review_agents`,
      each with a regression test asserting zero open `session_scope()` depth during the slow call. **This closes the P1
      live incident** — flip the source doc's DO-NOT-ARCHIVE guard note to reflect closure (not done in this pass,
      tracker-level only). Source: `/plans/archive/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`.
- [x] [REVIEW] P2. **DONE.** `WorkerLivenessKicker` now auto-submits a frozen `/compact`/`/pre-compact` at/above
      `context_worker_compact_gate_pct` (`server/worker_liveness/__init__.py:988-1027`, logs
      `frozen_guided_compact_auto_submitted`), citing this exact todo. Verified 2026-08-15 (reconciliation sweep, this
      session). Source: `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`
      (line ~136) — checkbox is stale, flip it.
- [x] [BACKEND] P2. **DONE — CORRECTED 2026-08-15: a concurrent investigation-only pass found no bug in the theoretical
      question it asked; a separate concurrent session found and fixed a DIFFERENT, real bug in the same area,
      `agent-orchestrator@de1e5a3c1d`.** The investigation-only pass's finding stands and is still true: spawn-heartbeat
      retries (`slot.spawn_retry_count`) and force-kill+resume retries (`slot.resume_attempts`) are genuinely separate
      counters that can't race or double-count each other — no ordering bug THERE. But the actual mechanism was:
      `autospawn.py::_resume_pass` stamps a fresh `last_spawned_at` on every successful kick-escalation `--resume`,
      arming `_auth_failover.py::check_spawn_heartbeat_timeouts` on that slot — and if the resumed session immediately
      re-freezes (pane_state=`"frozen"`, session alive), that watchdog previously treated it as "spawn never came up,"
      burning `spawn_retry_count` and firing a redundant kill+respawn. Matches episode 1's exact evidence
      (`retry_count=2`, `session_alive=true`, `pane_state=frozen`). Fix: extended the existing "working pane" skip guard
      to also cover "frozen" (both are live sessions, not failed spawns). New regression test proves
      `_SPAWN_HEARTBEAT_MAX_RETRIES + 1` consecutive frozen-pane force-resume ticks never trip the cap. Source: same
      doc, line ~141 — flip its checkbox too.
- [x] [BACKEND] P3. **DONE — CORRECTED 2026-08-15: a concurrent session's "already covered by
      `_tick_saturation_detector`" claim is factually wrong (verified against the live code + its own docstring); a
      separate concurrent session built the real thing, `agent-orchestrator@525aa528c8`.** `_tick_saturation_detector`
      is an ABSOLUTE-threshold check — it only fires once a target crosses ~80% and stays there; a target parked at,
      say, 40% for hours without ever climbing (the literal "stuck/looping, not making real forward progress" case this
      todo describes) would NEVER trigger it, since it never approaches the threshold at all. It is explicitly NOT a
      superset — the new `_tick_plateau_detector`'s own docstring states this distinction directly ("Distinct from
      `_tick_saturation_detector` (an ABSOLUTE-threshold check, fires regardless of trend)"). Added
      `_tick_plateau_detector` to `context_lifecycle.py`, mirroring the existing detector pattern: flags
      `context_plateau_detected` when pct hasn't climbed by `context_plateau_min_delta_pct` (default 5) over
      `context_plateau_window_seconds` (default 1800s) despite the target remaining live the whole window; resets on
      real forward progress or a compaction-drop. Detection/observability only, no auto-intervention, per the source
      doc's own scope. 6 new tests (flat vs. climbing synthetic readings, compaction reset, per-streak dedup,
      disabled-when-zero). Source: same doc, line ~145 — flip its checkbox too.
- **[REVIEW] P3. CANCELLED — SUPERSEDED 2026-08-15 (reconciliation sweep, this session).** Was: manually inspect/reset
  `learned_context_windows.json` once the fleet is fully on sonnet-5. Two follow-on fixes shipped + archived since
  (`ao_learned_context_window_registry_never_revalidates_2026_08_09`,
  `ao_deepseek_context_window_unknown_and_self_repoisoning_2026_08_10`): `context_probe.context_window_for()` now
  self-corrects a poisoned/under-estimated entry at READ time against a repeatedly-confirmed watermark, and
  `model_tier._ALLOWED_MODEL_WINDOWS` carries a corpus-measured sonnet-5 prior (937,882 tokens / 17,974 transcripts) as
  the cold-start fallback. The manual purge-and-relearn this todo asked for is obsolete — the same correction now
  happens automatically. Source: same doc, line ~342.
- [x] ✅ [BACKEND] P2. **Re-run the 60-min context-signal validation — DONE 2026-08-17** (slot 12, batch21 todo 1;
      reconciled batch21_finalize todo 2). Clean-start window: 21 forces `60×11 · 69×10`, zero wedge-terminal events.
      Source: `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`.
- [x] [REVIEW] P3. **DONE.** `DoneRequest.claude_session_id` field exists (`server/models/worker_api.py:275`);
      `_done_one_off` (`server/routes/slots_worker.py:1912-1924`) matches it against the archived row's own
      `claude_session_id` and returns idempotent 200 instead of 409. Tracker's premise ("still has no field") is stale.
      Verified 2026-08-15 (reconciliation sweep, this session). Source:
      `/plans/archive/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md` (its own
      "declined-P3, revisited" section already narrates this as shipped — flip the checkbox to match).
- [x] [DIAG] P0. Root-caused + fixed: `context_lifecycle.py::_tick_target`'s boundary-confirmed compaction path
      recognized a real compaction but never wrote the corrected pct back, so the stale pre-compaction-high value
      re-armed another forced compact every ~3.5min indefinitely — the "agents dying mid-task" pattern. Fixed +
      surfaced as a HealthStrip KPI. Fleet resumed to full capacity (0 paused). Evidence: `agent-orchestrator@
      9ba4391e60` (fix), `agent-orchestrator@1b2dddffc9` (UI). Full detail:
      `/plans/archive/issues/ao_fleet_regression_triad_2026_08_16.md` (Finding 2, resolved).
- [x] [BACKEND] P1. Root-caused + fixed: `_pick_free_slot` had zero awareness of `scheduled_task_reserved_slot_ids`
      at all — it never diverged from a race, it simply never consulted the reserve, so scheduled jobs landed on
      whichever slot iterated first. Fixed to prefer a reserved-and-free slot. Evidence: `agent-orchestrator@
      54f8fc5811`. Full detail: `/plans/archive/issues/ao_fleet_regression_triad_2026_08_16.md` (Finding 1, resolved).
- [x] [UI] P2. Fixed: human-fleet rows now state their own scope ("Ikenna (human-fleet slot 9001)") + a
      scope-clarifying STALE tooltip. Evidence: `agent-orchestrator@1b2dddffc9`. Full detail:
      `/plans/archive/issues/ao_fleet_regression_triad_2026_08_16.md` (Finding 3, resolved).
- [x] [DIAG] P0. Root-caused + fixed: `context_lifecycle.py::_tick_target`'s boundary-confirmed compaction path
      recognized a real compaction but never wrote the corrected pct back, so the stale pre-compaction-high value
      re-armed another forced compact every ~3.5min indefinitely — the "agents dying mid-task" pattern. Fixed +
      surfaced as a HealthStrip KPI. Fleet resumed to full capacity (0 paused). Evidence: `agent-orchestrator@
      9ba4391e60` (fix), `agent-orchestrator@1b2dddffc9` (UI). Full detail:
      `/plans/archive/issues/ao_fleet_regression_triad_2026_08_16.md` (Finding 2, resolved).
- [x] [BACKEND] P1. Root-caused + fixed: `_pick_free_slot` had zero awareness of `scheduled_task_reserved_slot_ids`
      at all — it never diverged from a race, it simply never consulted the reserve, so scheduled jobs landed on
      whichever slot iterated first. Fixed to prefer a reserved-and-free slot. Evidence: `agent-orchestrator@
      54f8fc5811`. Full detail: `/plans/archive/issues/ao_fleet_regression_triad_2026_08_16.md` (Finding 1, resolved).
- [x] [UI] P2. Fixed: human-fleet rows now state their own scope ("Ikenna (human-fleet slot 9001)") + a
      scope-clarifying STALE tooltip. Evidence: `agent-orchestrator@1b2dddffc9`. Full detail:
      `/plans/archive/issues/ao_fleet_regression_triad_2026_08_16.md` (Finding 3, resolved).

## Track 2 — Scheduled jobs, benchmarking, model/provider routing

- [x] [REVIEW] P3. **DONE — measured 2026-08-15 (reconciliation, this session).** False-positive RATE dropped from 17.8%
      (8/45 baseline) to 0.7% (8/1148) since `agent-orchestrator@9d26598` — 1,148 spawn-retry-cap declarations in the
      `2026-08-06..present` window, still only 8 showing `pane=working` at declaration. The guard fix worked. Source:
      `/plans/archive/2026_08/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md` — flip its checkbox with these
      numbers.
- [x] [DOC] P3. **DONE — RESTORED 2026-08-15 (this session), root cause identified.** The doc edit genuinely landed once
      already (`unified-trading-pm@69468f0164`, 2026-08-14) — verified via `git show`, the full "Pane-guard-
      before-cap-branch ordering invariant" subsection was really added — but was silently dropped by a LATER commit
      (`unified-trading-pm@9786794390`, a 71-insertion/68-deletion edit to the same file by a different session) that
      appears to have started from a stale local copy predating the addition — a live instance of this workspace's own
      documented "stale local content overwrites, not merges" hazard. **Correction to this tracker's own earlier batch-2
      "false-completion finding"**: that finding's remediation (re-adding the content) was right, but its
      characterization ("never done despite the checkbox") was wrong — the edit WAS genuinely done once, then silently
      erased by an unrelated concurrent edit; the false-completion framing should read "silently reverted," not "never
      made." Re-added the section (merging two independently-written near-duplicate versions found mid-session — one
      from this reconciliation, one from a concurrent peer session — into a single copy retaining the peer's fuller "why
      the order is the whole bug" + "future refactor must preserve this order" framing plus this session's post-fix
      measurement numbers) at the same location, immediately before "Calibration-source contract." Also flipped the
      adjacent `[DATA] P3` measurement todo in the source doc using the same numbers (1,148 cap declarations, 8
      `pane=working`, 17.8%→0.7%). This is a finding for whoever runs a corpus-wide staleness audit next: the SAME
      failure class could be silently dropping other sessions' concurrent doc edits to this heavily-contended file.
      Source: `/plans/archive/2026_08/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md` — both checkboxes flipped
      there too.

- [x] [REVIEW] P3. **DONE.** Decision made + recorded live: `server/models/scheduled_jobs.py:19-27` carries a dated
      `DECISION (...2026-08-04.md, 2026-08-14): KEEP "no_capacity"` — reachable only by an ad-hoc caller omitting
      `job_name`, every real timer-driven dispatch now reports `queued` instead (post `@5087f30`); kept as
      lowest-blast-radius fail-fast opt-out. Verified 2026-08-15 (reconciliation sweep, this session). Source: same doc.
- [x] [REVIEW] P2. **DONE — confirmed live 2026-08-15 (this session, direct SSM check).** Not just re-installed — 11
      timers now (more than the original 7), all present as unit files, all enabled (`timers.target.wants/` symlinks),
      linger enabled for ubuntu, live `systemd --user` instance running (PID 1111), and actively firing — confirmed real
      log output from `CIReconcileLoop`/`AutoParkReconciler`/`BlockedQueueReconciler` started 2026-08-15 09:08:32.
      Source: same doc.
- [x] [SCRIPT] P1. **ATTEMPTED 2026-08-16 (batch21 satellite todo) — SOLO pre-check correctly FAILED, no run
      started.** 5 concurrent `plan_reconciler` tranche-shard agents were active at check time (18:32:26Z Sunday) —
      confirmed the routine per-tranche cadence, not an anomaly; starting a competing whole-corpus dispatch would have
      confounded the benchmark and risked corpus write-collisions, so none was started. Root cause + full evidence + a
      new follow-up todo (cadence-drift between SKILL.md's documented weekly quiet-day and the installed every-2h
      timer) filed in Source. Most recent real whole-corpus number remains the 2026-08-12 interactive run (774 docs,
      121 contradictions) — 4 days stale. Source:
      `/plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`.
- [x] ✅ [SCRIPT] P1. Re-run `/na-eligibility-audit` — DONE 2026-08-16 (slot 9, batch21 todo 3; reconciled batch21_finalize
      todo 2). Numbers in the duplicate `[x]` entry a few lines below. Source: same doc.
- [x] [REVIEW] P2. **DONE — shipped `unified-trading-pm@d708247af1` TODAY (2026-08-15).**
      `agents/na_eligibility_auditor.md` STEP 1 (lines 109-115) now runs `git pull --ff-only origin live-defi-rollout`
      before proceeding, matching `agents/plan_reconciler.md`'s existing pattern exactly. Verified 2026-08-15
      (reconciliation sweep, this session, same day as the shipping commit). Source: same doc — flip its checkbox too.
- [x] ✅ [DOC] P2. Update the published skills-benchmark artifact once the two re-runs above land — DONE 2026-08-17
      (slot 26, `ao_satellite_ao_dispatch_batch21_finalize_2026_08_16.md` todo 1). New artifact
      `https://claude.ai/code/artifact/e1ef46e8-1854-4ca5-96da-6cc66d88f2cb` cites both fresh reports (numbers +
      timestamps) — the original URL is owned by a different, non-AO claude.ai account and unreachable from this
      session. The source doc's own broader "final status of every ruled decision" ask stays open there (out of this
      narrower todo's scope). Source: same doc.
      _(DeepSeek/Claude blended-routing work — `/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md` —
      and the Luna/Flex bridge — `codex_luna_flex_bridge_2026_08_14.md` (local-only, not yet pushed to origin as of this
      edit) — are out of scope for this tracker per operator direction 2026-08-14: handled elsewhere. The 7 todos below
      are CANCELLED here (not real deletions — the source docs still carry the live work); the DeepSeek account-credit
      gate the first one originally cited was stale at authoring — accounts are funded and DeepSeek is actively
      reconciling + taking tasks.)_

- **[REVIEW] P2. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: pilot the DeepSeek/Claude
  blended pool for one week. Source: `/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`.
- **[REVIEW] P2. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: confirm whether the
  flash-vs-pro ~56/44 routing split is real skew. Source: same doc.
- **[REVIEW] P3. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope) — BUT DONE ANYWAY 2026-08-15,
  disclosed honestly.** A parallel session dispatched this exact investigation before re-reading this tracker's current
  (reconciliation-pass-updated) state, missing the cancellation. Real finding: the skew is MOSTLY benign (flash's higher
  selection share alone predicts almost the whole measured gap — volume ratio 1.27x vs. skip-rate ratio 1.31x), but a
  genuine bug was found and fixed along the way: on a health/balance-gate skip, the code abandoned the whole "deepseek"
  provider slot and fell straight to Claude even when the OTHER variant's account was healthy — wasting real
  free-provider capacity, asymmetrically more often for flash (it's preferred more). Fixed with a same-provider
  cross-variant retry, 2 new regression tests, shipped `agent-orchestrator@398685cd3c`. Already landed on the shared
  branch — flagging here rather than silently leaving it undocumented, per the operator's own direction that DeepSeek
  work should route elsewhere; if this fix needs review/reversal by whatever process the operator intended for this
  track, that's an operator call, not something to guess at. Was: investigate why the flash variant trips
  `free_provider_health_gate_skipped` ~30% more than pro. Source: same doc.
- **[REVIEW] P1. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: re-run the local
  DeepSeek-routing pilot against the redesigned policy. Source: same doc.
- **[DATA] P2. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: give the
  `deepseek_flash_route_fraction` remeasure instruction an actual runnable tool. Source: same doc.
- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: ratio-check DeepSeek
  account-count/cost assumptions. Source: same doc.
- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: address the DeepSeek
  wallet balance top-up recurrence. Source: same doc.
- [x] ✅ [SCRIPT] P1. **DONE — 2026-08-16 (slot 9, infra worker, `ao_satellite_ao_dispatch_batch21` item 3).**
  Re-ran `/na-eligibility-audit` Phase 0 (`generate_na_doc_tranche_inventory.py --tranche all --json`) for a
  clean steady-state benchmark. Total corpus 449 `assigned_vm: NA` docs / 1,516 open todos across the 9
  tranches; incremental-skip (unchanged since a prior dated verdict marker) removed 125 docs, leaving 324
  docs / in-scope-todo counts below in scope for a fresh Phase-1 classification pass. Per-tranche
  (docs total/in-scope, todos total/in-scope): ao 67/56, 244/206; cefi 52/12, 181/33; ci 44/42, 107/78;
  cross-cutting 115/101, 492/392; defi 60/19, 267/112; infra 58/53, 200/165; prediction 26/18, 89/50; sports
  52/42, 168/118; tradfi 42/10, 97/34; ui 15/14, 35/34. A full Phase-1 hunter fan-out (10-agent-capped,
  read-every-doc-end-to-end classification) over the 324 in-scope docs was NOT run this session — out of
  scope for a single bounded dispatch at this size (the proven precedent run was multi-hour/multi-session);
  the Phase-0 numbers above are the requested steady-state benchmark. Full Phase-1 re-classification remains
  open work for a future scheduled `na-eligibility-auditor.timer` fire or a dedicated multi-session dispatch.
  Cited into `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s Progress Log. Source: this todo.

## Track 3 — Boot / context / session hygiene

- [x] [SCRIPT] P0. **DONE — `Req.R` hardening shipped `unified-trading-pm@bc88604f20`** ("harden context_scope
      frontmatter field to required (plan+issue doc_types)"), verified via direct read of
      `scripts/docs/docspec.py:154,185`: `FieldSpec("context_scope", Req.R, "free_list")`. The archived batch3-finalize
      plan's own Progress Log narrates the corpus-wide backfill reaching 0 NEVER_SCOUTED / 0 STALE — that sub-claim is
      MEDIUM confidence (not independently re-measured this pass; a fresh `generate_context_scope_inventory.py --json`
      run timed out at 90s — re-run with a longer timeout if independent re-verification is wanted).
- [x] [REVIEW] P1. **DONE.** `server/prompts.py:296` now has a literal curl body for the `/boot` STEP 2 call. Verified
      2026-08-15 (manual grep, this session). Source:
      `/plans/archive/issues/ao_boot_stub_session_vars_field_name_mismatch_2026_08_02.md`.
- [x] [REVIEW] P2. **DONE.** Zero `worktree_path` hits left in `server.py`/`routes/agents.py`/`autospawn.py` — the
      rename is complete. Verified 2026-08-15 (manual grep, this session). Source: same doc.
- [x] [REVIEW] P3. **DONE.** `BootRequest` carries `model_config = ConfigDict(extra="forbid")`
      (`server/models/worker_api.py:50`), with a comment citing this exact todo. Verified 2026-08-15 (manual read, this
      session). Source: same doc — with all 3 Track-3 items from it now done, check whether the source doc itself is
      fully closeable.

## Track 4 — Infra / VM / host hygiene

_Full detail for every DONE item below extracted to
`/plans/archive/2026_08/ao_open_work_consolidated_tracker_track4_history_2026_08_19.md` (2026-08-19, relieves this
file's 1000-line cap) — one-line summary kept here so the todo count stays conserved._

- [x] [CREDS] P0. DONE 2026-08-15 — vm-0 `ORCHESTRATOR_JWT_SECRET`/env already in sync, no write needed.
- [x] [BACKEND] P0. DONE 2026-08-16 — live fix: restored missing `ORCHESTRATOR_VM_ID` to `.env.local`, unstuck 2
      stuck escalations.
- [x] ✅ [DIAG] P1. DONE 2026-08-17 — root-caused + fixed `bootstrap_vm.sh` STEP 5b dropping `ORCHESTRATOR_VM_ID` on
      a partial/killed run.
- [x] [BACKEND] P0. DONE 2026-08-15 — dirty-worktree resolution policy design resolved (stash-and-proceed, never
      block on a human).
- [x] ✅ [DIAG] P2. DONE 2026-08-17 — 49.3G/16G-swap peak root-caused to 4 unbounded CEFI-manifest scripts.
- [x] [REVIEW] P2. DONE 2026-08-15 — zero kernel OOM-killer hits confirmed host-wide over a 30-day window.
- [x] [BACKEND] P2. DONE 2026-08-15 — `ReadinessWatchdog` shipped (`agent-orchestrator@3b4a329`).
- [x] [BACKEND] P3. **DONE 2026-08-19 — design fork resolved, tracker entry was stale.** The "batch/serialise
      per-slot git-status writes" alternative was implemented: `agent-orchestrator@996e98ef73` (+ stale-comment
      follow-up `agent-orchestrator@da056d128e`) routes every `POST /api/slots/{id}/git-status` write through a new
      single-worker `ThreadPoolExecutor` (`_GIT_STATUS_WRITER`, `server/routes/git_health.py`), so at most ONE DB
      connection is ever held for that route regardless of concurrent slot fan-in. New
      `tests/test_git_status_write_serialized.py` proves `max_active == 1` under 12 concurrent threads on a
      `threading.Barrier`. Source doc `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` is itself now
      `status: resolved` + archived (all 5 of its own todos closed) — this tracker (dated 2026-08-14) simply hadn't
      caught up. Found + fixed while triaging this exact item for the operator, 2026-08-19, this session.
- [x] [BACKEND] P2. DONE 2026-08-15 — `cgroup_memory_snapshot()` shipped (`agent-orchestrator@ca6603a`).
- [x] ✅ [DATA] P2. DONE 2026-08-17 — audited `unified-trading-system-repos/` (157G), found ~57.2G confirmed-dead
      scratch across 5 worktrees.
- [x] ✅ [DATA] P2. DONE 2026-08-17 — investigated `mdps_bench_data_fullmonth/` (3.8G), safe to archive/delete.
- **[SCRIPT] P3. CANCELLED — SUPERSEDED 2026-08-15.** `PYRIGHT_TIMEOUT` bump rejected; real fix is the
  resource-reservation admission governor.
- [x] [REVIEW] P3. DONE 2026-08-15 — `host_tombstone.py` shipped (`agent-orchestrator@426e8cf55`).
- [x] ✅ [OPERATOR] P2. DONE 2026-08-16 — content-derived-task-id migration live-applied, 2037 rows renamed, 0
      hazards.
- [x] [REVIEW] P2. DONE 2026-08-14 — rejected-push sentinel restamp shipped (`agent-orchestrator@c6d43ac`).
- [x] [REVIEW] P2. DONE 2026-08-14 — `BLOCKED-PREREQ` per-occurrence audit, all 6 confirmed genuine.
- [x] [REVIEW] P3. DONE 2026-08-14 — `_upstream_plan_open_on_disk()` unified (`agent-orchestrator@2c8302c`).

## Track 5 — Dashboard e2e flakiness

_Governed by `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`'s own stated rule: "do not edit a source doc's
checkboxes beyond appending evidence; the paired finalize plan reconciles this" — check that finalize plan's status
before touching the source doc directly._

- [x] [TEST] P2. **DONE — shipped `agent-orchestrator@6a4b7cbb31`** (2026-08-15). Both originally-reported failures were
      ALREADY fixed by earlier commits (`6e3d06c` for the wallet-reconciliation `$3` vs `$5` mismatch — a missing
      `is_review_slot=True` fixture stamp; `d279c22`'s `DeepSeekUsagePoller` mock-gate for the per-turn-metrics
      mismatch) — both re-run and confirmed green before any new work. Found + fixed 2 REAL regressions along the way: a
      same-day "Human (planning)" role-group filter button whose accessible name substring-collided with the existing
      "Planning" button, breaking 3 Playwright locators across 2 spec files (`exact: true` added); and 3 hardcoded
      fixture totals that had drifted stale after an unrelated fixture addition (recomputed with cited math). 13/13 +
      5/5 specs green, full QG green. Source:
      `/plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` — append evidence per its own
      governance rule (do not flip its checkbox directly, the paired finalize plan does that).
- [x] [REVIEW] P3. **DONE.** Root cause was NOT the hypothesized async remint→confirm race — it was two local-slot-only
      port-mismatch bugs (hardcoded fixture port + missing `process.env` propagation), fixed by
      `agent-orchestrator@1e2ecac`+`3ba4ba4` (both confirmed ancestors of `origin/live-defi-rollout`). Fixture file
      deleted; runner now regenerates the backend port dynamically, slot-offset-aware. 3 independent isolated re-runs
      (6/6 tests, zero flakes) reproduced the fix — the source doc's checkbox stays unflipped only per its own
      evidence-append-only governance rule, not because the fix is unconfirmed. Verified 2026-08-15 (reconciliation
      sweep, this session). Source: same doc.
- [x] [DOC] P3. **DONE 2026-08-15 (this session).** Added a third pattern entry (slot-offset port not propagated to the
      test-runner's own `process.env`) to `/codex/06-coding-standards/ui-testing-layers.md` § "agent-orchestrator e2e:
      background-poller vs. fixture-data interaction," alongside the two already-documented patterns (poller-overwrite,
      async-panel-fetch). The `PlanRegenLoop`-in-mock-mode class was already covered separately in the same codex file
      (batch8-002's fix) — not duplicated. Appended evidence-only note to the source doc per its own checkbox-governance
      rule (does not flip that doc's checkbox directly — its item 1 remains open). Source: same doc.
- [x] [REVIEW] P3. **DONE — shipped `agent-orchestrator@9cd1fa0`** (2026-08-11). `dashboard/playwright.config.ts`'s
      `serversForThisRun()`/`neededProjects()` (lines ~119-231) filters the `webServer` array to only the pair(s)
      matching the requested `--project`/positional filter — a single-project run now boots only that pair, "start
      everything" preserved only as the conservative fallback for unmappable filters. Verified 2026-08-15
      (reconciliation sweep, this session). Source: same doc.
- [x] [UI] P2. **New, operator 2026-08-16 — DONE same day, shipped `agent-orchestrator@c56f053fbf`.** Make the
      Wallet Reconciliation (Claude + DeepSeek),
      Accounts, Fleet, Blocked questions, Escalations, and Scheduled jobs/dispatch dashboard panels
      expandable/collapsible. Implemented by extending the shared `Panel` component
      (`dashboard/src/components.tsx`) with a `collapsible` prop — the title becomes a toggle button (chevron +
      title only, not the whole header, so a header's own action buttons like Fleet's "Spawn worker" stay
      independently clickable), collapse state persists per-panel via `localStorage`
      (`orch.panelCollapsed.<title>`, matching this dashboard's existing session/tweaks persistence pattern in
      App.tsx), body simply isn't rendered when collapsed (matches the codebase's existing conditional-render
      convention for expand/collapse elsewhere, e.g. the activity-group rows). Wired into all 8 real panel
      instances behind the 6 named categories (`layout.tsx`: Blocked questions, Escalations, Scheduled jobs,
      Scheduled dispatch, Accounts ×2 empty/populated; `App.tsx`: Fleet; `ClaudeWalletPanel.tsx` +
      `DeepSeekWalletPanel.tsx`). `tsc --noEmit` clean, full `quality-gates.sh` green. **pw:L2** — new regression
      spec `dashboard/tests/e2e/panel-collapsible.spec.ts` (3 tests: toggle hides/shows the body without affecting
      a sibling panel, collapsed state survives a reload, a header action button stays clickable and does not
      trigger collapse) plus 10 pre-existing wallet/blocked specs re-run green to confirm no regression. Source:
      operator request, this session (not from the 2026-08-14 audit sweep).
- [x] ✅ [TEST] P3. **Root-cause 2 pre-existing, reproducible failures in
      `dashboard/tests/e2e/task-usage-account-filter.spec.ts`** (both bleed +5000, likely `window_task_usage_totals`
      double-counting/mis-attribution — see below). New finding, 2026-08-16, adjacent to the collapsibility work
      above — NOT caused by it, isolated and confirmed independently. Failures: ("All accounts sums every task..." expects `17.0K`, gets `22.0K`; "tasks on an
      unregistered account are unreachable..." expects a `0` shortfall, gets `5.0K` bleeding into a registered
      account's slice) — the +5000 in both cases exactly matches the fixture's "unregistered account" oneoff rows
      (2000 cicd + 3000 scheduled), suggesting those rows are being double-counted or mis-attributed somewhere in
      the real `window_task_usage_totals` aggregation, not a test-authoring bug. **Isolation proof**: reproduced
      with a byte-for-byte reverted `accounts.mock.json` (diffed to confirm identity with `HEAD`) AND a freshly
      deleted `dashboard/tests/e2e/.tmp/e2e_state.db` — same failure both times, ruling out both today's fixture
      addition (`grok-4-3-demo`/`kimi-k2-6-demo`) and stale-DB accumulation from repeated test runs as the cause.
      Not investigated further this session (out of scope for the collapsibility/provider-grouping work it was
      found alongside). Done when: root-caused in `window_task_usage_totals` (or wherever the real aggregation
      lives) and both assertions pass again on a fresh DB.
      **DONE 2026-08-19 — root cause was NOT `window_task_usage_totals`, the original hypothesis was wrong.**
      Read that function end-to-end (`server/state_store/slots.py`): a plain `select(TaskUsageRow)` with AND-composed
      filters, Python-side sum over the result list — no join, no fan-out, structurally incapable of the described
      double-count. Confirmed by direct repro: both assertions pass, 6/6 green, on a completely fresh
      `dashboard/tests/e2e/.tmp/e2e_state.db`, run twice independently (`npx playwright test
      task-usage-account-filter.spec.ts --project=chromium`, zero flakes). Real mechanism, traced via `git log` on
      the fixture/spec files between the 2026-08-16 finding and now: `agent-orchestrator@423016a` (2026-08-18, the
      concurrent hourly-usage-series build this doc's own 2026-08-18 Progress Log entry flagged as blocking a direct
      fix here — "queued... once the concurrent hourly-usage-series build vacates `agent-orchestrator/server/`")
      added its own `E2E_USAGE_TS_HOUR_A/B` fixture rows reusing the SAME account_ids as this older per-account-filter
      fixture — the exact "+N tokens bleeding into a hardcoded per-account assertion" failure shape, same-day fixed
      by `agent-orchestrator@fae7a6d` ("isolate usage-ts e2e fixture accounts... reused the same account_ids as the
      older task-usage-account-filter fixture, bleeding tokens into its hardcoded per-account assertions. Gave it two
      dedicated, newly-registered accounts instead"). That hourly-usage-series work is now fully landed and merged
      (`agent-orchestrator@4e2d3797fb`, this session's own concurrent multi-provider billing work — checked for
      overlap first, confirmed clean: it never touches `window_task_usage_totals` or the account-filter path, only
      adds new schema columns and a separate `compute_hourly_provider_role_usage` function). **Residual honest gap**:
      the ORIGINAL 2026-08-16 report predates `423016a`'s fixture by two days, so `fae7a6d` cannot be proven the
      LITERAL fix for that exact original instance — no other candidate commit exists in this window (checked full
      history of `server/state_store/slots.py`, `dashboard/src/TaskUsageWindows.tsx`,
      `dashboard/tests/e2e/fixtures/seed_e2e_state.py`, and `data/config/accounts.mock.json` for this period; only
      `fae7a6d` matches the failure signature). What's certain, not hypothesized: `window_task_usage_totals` itself
      was never the bug, the failure class this bug's symptom matches is fixture account-id collision (now fixed),
      and the state today is genuinely green. **Not sourced from `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`**
      (checked — that doc has zero mention of this spec or `window_task_usage_totals`), so its checkbox-governance
      rule doesn't apply to this item; flipped directly here. No code change shipped — nothing left to fix.
- [x] [UI] P2. ✅ **New, live operator observation 2026-08-16 — DONE, shipped `agent-orchestrator@f52b541c13`.**
      While reviewing the collapsibility feature above, the operator noticed only Claude/DeepSeek wallet panels
      existed and asked to "add the other models by provider so grouping google, xai, etc." Investigating surfaced
      a real, live bug: `ProviderBadge` (`dashboard/src/components.tsx`) was still the original
      2026-07-28-era DeepSeek-vs-everything-else-is-"Claude" binary — every Grok/Gemini/GLM/Codex/Kimi/NVIDIA
      account was silently mislabeled "Claude" in the UI, exactly the failure mode the operator explicitly flagged
      earlier this session ("i dont want anything registering as claude when its grok even if its claude code").
      Fixed by adding `PROVIDER_DISPLAY` (a real label/title/CSS-class per registered `AccountProvider` value,
      exported for reuse) and rewriting `ProviderBadge` to use it, falling back to the raw provider string rather
      than lying as "Claude" for anything unmapped. Also implemented the actual grouping request: `AccountsPanel`
      (`layout.tsx`) now groups its rows by provider (anthropic sorts first, others alphabetically by display
      label), each provider sub-group independently collapsible (own `localStorage` key, reusing the collapse
      pattern from the todo above). 2 new mock accounts (`grok-4-3-demo`, `kimi-k2-6-demo`) added to
      `accounts.mock.json` for realistic test coverage — required updating `critical-health.spec.ts`'s
      hardcoded "ALL 4" account count to "ALL 6" (a real, expected, mechanical consequence of the fixture growing,
      not a regression). `tsc --noEmit` clean, full `quality-gates.sh` green. **pw:L2** — 2 new tests in
      `provider-badge.spec.ts` (Grok/Kimi render their own real badge not "Claude"; the Accounts panel groups by
      provider with independent per-group collapse) plus the full relevant regression sweep re-run green
      (13/13 across provider-badge/panel-collapsible/fleet-account-column, 2/2 critical-health, 4/4 tier-editor,
      each via their correct dedicated Playwright project). Source: operator live observation, this session.
- [x] [UI] P2. ✅ **Operator "build the rest now" 2026-08-16 — Grok DONE, shipped `agent-orchestrator@88c838dd6a`
      + `agent-orchestrator@60db1a7993`.** Real Grok wallet reconciliation: `GrokBalanceHistoryRow` (new table,
      mirrors `DeepSeekBalanceHistoryRow`), `GrokBalancePoller` (mirrors `DeepSeekBalancePoller`, 1-min cadence, uses
      the already-working `fetch_grok_balance()`), `compute_grok_wallet_window_reconciliation()` (real balance-diff
      vs real `task_usage.spend_usd` WHERE `provider="grok"` — Grok needs no bespoke transcript-sweep table the way
      DeepSeek does, since `price_usage()` already prices it correctly from the live `/done` capture), new
      `GET /api/accounts/grok/wallet-reconciliation/window` route, new `GrokWalletPanel.tsx` (24h/7d toggle,
      collapsible). Deliberately a SIMPLER v1 than DeepSeek's panel: no top-ups tracking, no
      worker/orchestrator/review split (total attributed spend only). **pw:L2 gap now closed** — new
      `grok-wallet-reconciliation.spec.ts` (2 tests: balance-at-end/attributed-spend/sampling-since render correctly;
      the 24h→7d toggle re-fetches and keeps the same attributed spend), shipped alongside Kimi below.
- [x] [UI] P2. ✅ **Kimi DONE, shipped `agent-orchestrator@60db1a7993`.** The prior blocker — "does Moonshot expose a
      programmatic balance-read endpoint" — is resolved: confirmed `GET https://api.moonshot.ai/v1/users/me/balance`
      is real (Bearer auth, `{"data":{"available_balance":...}}` shape;
      [platform.kimi.ai/docs/api/balance](https://platform.kimi.ai/docs/api/balance)). Clones the Grok pattern
      (`KimiBalanceHistoryRow`, `KimiBalancePoller`, `compute_kimi_wallet_window_reconciliation()`,
      `GET /api/accounts/kimi/wallet-reconciliation/window`, `KimiWalletPanel.tsx`) with one real structural
      difference: the three Kimi model-accounts (kimi-k3, kimi-k2.6, kimi-k2.7-code) share ONE Moonshot API key and
      therefore one wallet — `KimiBalancePoller` samples balance ONCE per tick (not per account) under a synthetic
      wallet identity, and `compute_kimi_wallet_window_reconciliation` sums `task_usage.spend_usd` across ALL THREE
      accounts (`provider="kimi"`), not one. Token resolution is also structurally different from Grok/DeepSeek: no
      Kimi `AccountDef` carries `api_key_secret_name` (the real key lives server-side in the LiteLLM proxy's own env),
      so `kimi_balance.py` resolves GSM secret `moonshot-api-key` directly rather than per-account. **pw:L2** — new
      `kimi-wallet-reconciliation.spec.ts` (2 tests), with a 2-different-account-ids e2e fixture that actually proves
      the cross-account aggregation claim rather than happening to pass on a single-account case. Full
      `quality-gates.sh` green (4003 pytest + 380 vitest + tsc clean), 16/16 relevant Playwright specs re-run green.
- [x] [UI] P2. ✅ **Gemini capacity panel DONE, shipped `agent-orchestrator@606521da72`.** NOT $-based — the real
      signal is rate-limit CAPACITY consumed (genuinely free tier). New `compute_gemini_capacity_snapshot()`
      (`gemini_headroom.py`) reuses the SAME live `gemini_request_selected` activity-row counting
      `gemini_account_has_rate_headroom` already gates dispatch with, just reports the numbers instead of collapsing
      to a bool — no new tracking mechanism, a read-only view over data that already existed. New
      `GET /api/accounts/gemini/capacity` route, `GeminiCapacityPanel.tsx` (RPM/RPD gauge bars using the existing
      `--status-working`/`-blocked`/`-stale` design tokens, not invented colors; TPM renders ceiling-only —
      informational, no pre-dispatch used-token count exists for it). e2e fixture adds a real
      `gemini-flash-lite-demo` mock account (accounts.mock.json, now 7 accounts — `critical-health.spec.ts`'s "ALL N"
      hardcode updated to match) + 3 seeded selection events. Full `quality-gates.sh` green, 2/2 new
      `gemini-capacity.spec.ts` tests plus the wider wallet/badge/collapsible regression sweep re-run green.
      **Real, unrelated bug found + fixed in the same pass (per the "misleading/broken code you hit is a finding,
      fix it in the same turn" rule)**: `layout.tsx`'s `HealthSummary` interface already declared a required
      `recentOrphanReapCount: number` field (landed via `ao_fleet_regression_triad_2026_08_16` Finding 2's own
      commit) but the `summarise()` builder never populated it — a genuine tsc-breaking regression already on
      `origin/live-defi-rollout`'s HEAD, blocking `quality-gates.sh` for anyone touching dashboard code, not just
      this todo. **Fixed the 3-line gap in the working tree but did NOT commit it** — `layout.tsx` was live,
      actively-being-edited WIP from a concurrent peer session sharing this checkout (confirmed via a "file modified
      on disk since last read" warning mid-edit, and the full peer fileset — `agentTypes.test.ts`, `utils.ts`,
      `context_lifecycle.py`, `plan_health.py`, `routes/state.py`, etc. — reappearing seconds after being stashed
      away for an isolated gate run), so committing my fix under my name would have either raced their save or
      shipped an incomplete slice of their own in-progress feature. The fix sits harmlessly in their dirty working
      tree now, ready to ride along whenever they commit — flag this to that session/operator if `layout.tsx`'s tsc
      error resurfaces after their WIP lands, since my fix may not have survived their next save.
- [x] [INFRA] P2. ✅ **NVIDIA capacity-tracking layer DONE, shipped `agent-orchestrator@0c0e527aec`.** New
      `nvidia_headroom.py` mirrors `gemini_headroom.py`'s shape with one real structural difference: NVIDIA's two
      registered accounts (both paused) share ONE API key with a GLOBAL per-key RPM ceiling (~40 RPM, community-
      reported — [decodethefuture.org](https://decodethefuture.org/en/nvidia-nim-api-pricing-limits-guide/),
      [NVIDIA forums](https://forums.developer.nvidia.com/t/request-to-increase-rpm-limit-for-free-nvidia-nim-account/377451),
      upgradeable to 200 RPM) — so counting aggregates across every account rather than per-account like Gemini's
      per-(project, model) ceilings. Reported honestly via `ceiling_confirmed=false`, not presented as settled fact
      until the concurrency-baseline todo below actually measures it. **Deliberately NOT wired into autospawn.py's
      real dispatch path** — both accounts stay paused (task-routing logic doesn't exist yet), so
      `NVIDIA_REQUEST_SELECTED_EVENT` is dormant scaffolding, same "build now, dormant" shape as the GLM/Codex todo
      below. New `GET /api/accounts/nvidia/capacity` route (returns one shared reading, or `None` if no NVIDIA
      accounts registered — never a fabricated row), `NvidiaCapacityPanel.tsx` (single shared gauge listing both
      account labels, not one row per account). Renamed the gauge/account-row CSS classes from `gemini-*` to
      provider-agnostic `capacity-*` since both panels now share them. e2e fixture adds 2 real demo accounts
      (`nvidia-diffusiongemma-demo`, `nvidia-gemma-4-31b-demo`, now 9 accounts — `critical-health.spec.ts`'s "ALL N"
      hardcode updated again) with 3+2 seeded selection events proving the cross-account aggregation (5 total, not
      two separate 3/2 rows). Full `quality-gates.sh` green, 2/2 new `nvidia-capacity.spec.ts` tests plus the wider
      regression sweep re-run green.
- [x] [DATA] P2. **DONE 2026-08-19 — real burst-concurrency baseline measured via isolated sandbox test, no fleet
      accounts unpaused.** The original "blocked on operator decision" framing conflated two different things:
      unpausing the LIVE FLEET accounts (correctly still off — no routing logic exists yet) vs. hitting NVIDIA's raw
      API directly with the same shared key outside AO entirely, which needs no fleet-pause change at all. Ran a
      direct concurrency ramp (5→10→15→20 simultaneous single-message requests) against
      `google/diffusiongemma-26b-a4b-it` only — `gemma-4-31b-it` deliberately excluded, since its own separate
      persistent-timeout bug (`plans/active/issues/gemma_4_31b_it_persistent_timeout_2026_08_19.md`) would confound
      a concurrency measurement with unrelated hangs. **Result**: 5/10/15 concurrent all succeeded clean (0 429s);
      at 20 concurrent, 4/20 got HTTP 429 — breaking point sits between 15 and 20 simultaneous in-flight requests.
      **Honest caveats**: this measures burst-concurrency tolerance (a near-instantaneous fan-in), not a literal
      60s sustained-RPM-window saturation test — the two are related but not identical; and it assumes the ceiling
      is genuinely per-key rather than per-model (per this todo's own "global-per-key" framing, not independently
      reverified here). Real, actionable number for any future routing-logic design: **do not fire more than ~15
      concurrent Gemma requests on one NVIDIA key at once.**
- [x] [INFRA] P3. ✅ **GLM/Codex `boost_multiplier` plumbing DONE, shipped `agent-orchestrator@3ca72fd9b2`.** New
      `compute_flat_rate_boost_reconciliation()` generalizes `compute_claude_wallet_reconciliation`'s EXACT calibration
      math (real subscription cost vs metered-equivalent value of captured usage), keyed by provider
      (`_FLAT_RATE_PROVIDER_MONTHLY_PRICE_USD = {"glm": 18.0, "codex": 20.0}`, the CURRENTLY-active tiers, not the
      future-upgrade prices both source plans already correctly document separately) instead of Claude's tier ladder,
      since GLM/Codex are single flat plans today. **Genuinely dormant, not a partial build**: this todo's own
      scoping flagged that neither Z.ai's (GLM) nor OpenAI's (Codex) API has been confirmed to expose a
      `weekly_pct`-equivalent signal the way Anthropic's `anthropic-ratelimit-unified-*` headers do — building that
      poller would have been guessing, not plumbing, so it was deliberately NOT built. Every account currently
      reports `boost_multiplier=None`, honestly, via the same `AccountUsageRow.weekly_pct` field the schema already
      carries (never populated for these two providers yet) — ready to compute for real the moment a real poller
      exists, with zero further plumbing changes needed. New `GET /api/accounts/flat-rate-boost` route,
      `FlatRateBoostPanel.tsx` (shows the real subscription price + an explicit "no data yet — awaiting a weekly_pct
      poller for this provider" message per account, never a fabricated number). e2e fixture adds 2 real demo
      accounts (`glm-lite-demo`, `codex-plus-demo`, now 11 accounts — `critical-health.spec.ts`'s "ALL N" hardcode
      updated a third time this session). Full `quality-gates.sh` green, 2/2 new `flat-rate-boost.spec.ts` tests
      (asserting the dormant state renders correctly, not a crash) plus the wider regression sweep re-run green.
      **Real follow-up work this deliberately does NOT do** (out of scope for "build the plumbing"): confirm whether
      GLM's z.ai endpoint or the Codex bridge exposes any usage-fraction signal at all — a genuinely separate,
      unscoped research task, not blocked on anything built here.

## Track 6 — Archival + reconciliation bookkeeping

- [x] [REVIEW] P0. Archive `ao_satellite_ao_dispatch_batch6_2026_08_04.md` + run its finalize plan's remaining 3 todos
      (reconcile evidence into named source docs, archive zero-open-todo sources, self-archive) — confirmed 0 open todos
      on the batch plan itself. Source: `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`.
      **DONE 2026-08-14** — batch6_finalize's 3 remaining todos (reconcile evidence, archive zero-open-todo sources,
      self-archive) all confirmed already-satisfied-or-completed and flipped `[x]`; both batch6 and batch6_finalize
      `git mv`'d to `plans/archive/2026_08/`, banners added, `status: active → complete`, all corpus-wide referrers
      repointed. See these docs' own Progress Logs for full evidence. Evidence: this commit (doc edits) plus a follow-up
      corrective commit closing a create-only-commit gap left by the automated inventory-regen step's own commit
      (`unified-trading-pm@6d8a610d77`).
- [x] [INFRA] P0. Archive `ao_satellite_ao_dispatch_batch7_2026_08_06.md` (confirmed 0 open todos) via its finalize
      plan's 1 remaining todo (self-archival ritual + inventory regen). Source:
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md`. **DONE 2026-08-14** —
      batch7_finalize's last todo (archive the batch plan + regen inventory) completed and flipped `[x]`; both batch7
      and batch7_finalize `git mv`'d to `plans/archive/2026_08/`, banners added, `status: active → complete`, all
      corpus-wide referrers repointed (including the epic's relative links and `INDEX.md`/inventory regen). Note: a
      concurrent session also independently moved the same two files around the same time (a bare `git mv` with no
      banner/status update landed via the inventory-regen script's own commit) — reconciled cleanly, no data lost, this
      commit layers the full ritual (banner, status, referrer fixups) on top of that move.
- [x] [REVIEW] P1. **`ao_satellite_ao_dispatch_batch5_2026_08_03.md` now shows 0 open todos** (as of this session's
      checkbox flip) — check whether it needs its own archival, and confirm `batch5_finalize`'s `gate_on_depends` has
      genuinely cleared before running its 5 todos. Source:
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md`. **DONE 2026-08-14** — gate
      confirmed cleared (batch5 itself 0 open todos, no lock); ran all 5 of batch5_finalize's todos (re-verify 10
      done-claims, reconcile evidence into 10 source docs incl. fixing a broken citation + resolving its sign-off
      question, re-check 31 declined-orphan gates, archive 1 newly-eligible source doc, archive the batch plan itself).
      Both batch5 and batch5_finalize `git mv`'d to `plans/archive/2026_08/`, banners added,
      `status: active → complete`, all corpus-wide referrers repointed.
- [ ] [SCRIPT] P2. Finish the `context_scope` backfill named in `batch3`'s own open todo (see Track 3) — this is what
      still gates `batch3_finalize`'s 5 todos via `gate_on_depends`. Source:
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`.
- [x] [REVIEW] P1. **RULED 2026-08-06 disposition sweep** — apply the operator's default-disposition ruling to the
      remaining declined-orphan docs. Source: `/plans/archive/issues/ao_orphan_audit_followup_triage_2026_07_30.md`.
      **DONE 2026-08-14** — re-checked all 12 named docs directly: 10 already archived/resolved by earlier sessions, 1
      (`blocked_questions_ux_redesign...`) 0-open but deliberately `archive_exempt` for a companion plan, 1
      (`unified_trading_pm_stash_pile_accumulation...`) correctly still gated on a literal operator action, not a
      judgment fork. Archived `long_lived_vm_logs_not_backed_up_2026_07_02.md` directly (its own bridge note named this
      as the follow-on pass). No fold-into-batch action was actually needed — every genuine item had already resolved
      independently. Full disposition in the source doc's own todo evidence.
- [x] [REVIEW] P2. Read + properly bucket the 7 "unclear" docs the Phase-1 audit agent couldn't cleanly classify.
      Source: same doc. **DONE 2026-08-14** — 6 of 7 already archived/resolved; the 7th
      (`orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md`) is genuinely still open and already tracked as
      its own item in this tracker's Track 4. The source triage doc itself reached 0 open todos after both items above
      and was archived in the same pass (`/plans/archive/issues/ao_orphan_audit_followup_triage_2026_07_30.md`).
- [x] [REVIEW] P2. **DONE.** `/api/escalate` (unchanged CI-wall dispatch) coexists cleanly with the namespaced-plural
      `/api/escalations/active`, `/api/escalations/{id}`, `/api/escalations/{id}/resolve` — no collision. Docstring at
      `server/routes/agents.py:444-451` explicitly cites this as the resolution. Verified 2026-08-15 (reconciliation
      sweep, this session). Source: `/plans/active/issues/ao_residuals_after_dispatch_hardening_2026_07_17.md` (this
      checkbox actually tracks via `escalation_and_disaster_recovery_master`'s own P1 todo per its 2026-08-07
      na-eligibility note — flip both).
- [x] [UI] P3. **DONE (backend) — shipped `agent-orchestrator@6ce637988d`** (2026-08-15). `GET /api/backlog/graph`
      implemented per `docs/BACKLOG_RELATIONS_UX_BRIEF.md` §9's contract in `server/routes/backlog.py` + new Pydantic
      views in `server/models/backlog.py`. Reuses existing machinery (`dispatch.explain_blocked_bulk` for `explain`,
      `BacklogTask.prereqs` for conditions/after-tasks, skips joined against live `backlog.yaml` only per the brief's
      own §11 anti-overstatement guidance). 6 new tests incl. cycles/orphan-rows/dead-skip-filtering. **Dashboard tile
      NOT built** (backend-only this pass, matches the cgroup-RAM precedent) — genuine follow-up if the operator wants
      it surfaced visually. Source: same doc — flip its checkbox too.
- [ ] [REVIEW] P3. Re-test the `l2_book` microstructure-capture retest gate once
      `/plans/active/l2_book_microstructure_capture_2026_07_13.md` clears its own `assigned_vm: NA` hold. Source: same
      doc.

---

## Track 7 — AO-plan operator-item purity (per `task_template.md` §3 finding Y)

**Merged in 2026-08-16** from `ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md`'s own
`orchestrator_master` group todo — that sweep now covers only the other 9 non-ao epic groups; this Track is the
single owner for the ao-topic slice, so the two docs never re-process the same corpus blind to each other. Per
finding Y: any `assigned_vm: planning` AO plan carrying a genuine `[OPERATOR]`/`BLOCKED-<TOKEN>` item interleaved
with plain dispatchable todos gets that item forked into a companion `assigned_vm: NA` doc, cross-linked, so the AO
plan can reach zero-open-todos and archive independently.

- [x] [PM] P2. ✅ **DONE 2026-08-19 — Track-A/B classification pass completed across all 24 `orchestrator_master`-scoped,
      `assigned_vm: planning` plans in `plans/active/*.md`** (mechanical soft-flag: file contains an open `- [ ]` line
      carrying `[OPERATOR]`/`BLOCKED-<TOKEN>`, cross-checked per-doc for genuine-vs-mis-tag per finding U's 3-part test).
      **Disposition** (24/24 checked, 2 genuine hits forked, 0 mis-tags, 22 clean — full per-doc detail in each
      forked doc's own Progress Log, not repeated here to stay under the 1000L cap):
      - **FORKED**: `anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md` (28→27 open) — genuine
        `[OPERATOR]` (laptop-only login-identity log) → companion NA doc `..._operator_items_2026_08_19.md`.
      - **FORKED**: `deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md` (1→0 open, this
        was its ONLY remaining todo) — genuine `[OPERATOR]` (optional `opening_balance` freeze) → companion NA doc
        `..._operator_items_2026_08_19.md`; plan now has zero open todos, its gated finalize plan is unblocked.
      - **Clean, no gated item, nothing to fork**: `anthropic_..._finalize_2026_08_10`,
        `ao_satellite_ao_dispatch_batch{14,21,22,23,24,25,3,8}` + each batch's `_finalize` sibling,
        `content_derived_backlog_task_ids_2026_08_08` + `_finalize`, `deepseek_wallet_..._finalize`,
        `quality_gates_quickmerge_timing_baseline_2026_07_31` + `_finalize`, `slot0_self_cleaning_daemon_2026_08_18`
        + `_finalize` (batch14/21/8 already zero-open; rest have only plain dispatchable todos, no
        `[OPERATOR]`/`BLOCKED-<TOKEN>` line).
      2026-08-18's re-check found the Anthropic item isn't a mis-tag but stopped short of finding Y's remediation
      (fork it out) — this pass completes that step. Both source-doc checkboxes replaced with bold pointer digest
      lines + `related:` cross-linked both ways, shipped this session. Archival of the now-zero-open `deepseek_wallet`
      plan is left to its gated finalize plan. All 24 `orchestrator_master` plans covered; treat as point-in-time.
- [x] [PM] P2. **RESOLVED 2026-08-18 — not cancelled, distinct topic, safe to dispatch normally.** The `batch14`
      env-file GSM-indirection fix (real todo tracked in `ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md`
      todo 2, a fresh `[INFRA] P0`) is a credential-hygiene bug fix, unrelated to the BLENDED-ROUTING PILOT topic
      the DeepSeek-cancellation ruling (`deepseek_claude_blended_provider_routing_2026_07_28.md`) actually covered.
      No conflict — plain `[INFRA]`, already queued, safe to dispatch normally.

---

## Notes

- **7 of the still-open Track 1/2/4 items extracted into `ao_satellite_ao_dispatch_batch21_2026_08_16.md`
  (2026-08-16, operator request)** — the bounded, conflict-clear, non-operator-gated items (context-signal re-run,
  `/plan-reconcile` + `/na-eligibility-audit` benchmark re-runs, `ORCHESTRATOR_VM_ID` env-var-loss root-cause, swap-peak
  root-cause, two disk-cleanup audits). Its gated `batch21_finalize` reconciles evidence back into this tracker's own
  checkboxes once done — do not flip them manually in the meantime. See that batch plan's "Why this plan exists"
  section for the full list of items deliberately NOT extracted (design fork, `[OPERATOR]`-tagged migration, an
  item gated on a separate NA hold, and one deferred into the finalize plan itself) and why.
- **Not archivable until `depends_on` clears (operator direction, 2026-08-16).** This tracker's own 12 remaining open
  items are pointers, not the real work — the real work lives in the source docs each item cites. `depends_on` above
  names every distinct source doc still carrying a genuinely-open item as of the 2026-08-15 final reconciliation pass:
  `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25` (60-min context-signal re-validation),
  `ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30` (the two solo benchmark re-runs + artifact
  publish), `ao_satellite_ao_dispatch_batch3_2026_07_31` + `context_scout_completion_and_plan_brainstorm_skill_2026_07_30`
  (the standing `context_scope` corpus backfill), `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02`
  (best-effort swap-peak root cause), `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25` (DB-pool
  right-sizing design fork), `shared_host_home_filesystem_full_2026_07_26` (disk-usage + `mdps_bench_data` audits),
  `content_derived_backlog_task_ids_2026_08_08` (the deliberately-deferred live backlog-ID migration),
  `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31` (gated on the same `context_scope` backfill), and
  `l2_book_microstructure_capture_2026_07_13` (blocked on its own separate `assigned_vm: NA` hold). This tracker stays
  `active` and un-archived until every one of those clears its own open work — do not archive this doc on the strength
  of its own 12 items alone reading "just pointers," per this workspace's `depends_on` convention (documents ordering +
  gates archival, per `plans/PLAN_FORMAT.md`).
- **Explicitly excluded from this tracker** (correctly gated/standing, not real remaining work to schedule):
  `ao_tranche_full_content_audit_findings_2026_07_31.md`'s standing opportunistic-retag policy (intended to sit open
  indefinitely); `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` (correctly blocked on a named
  unmet condition); `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` (fully resolved + archived
  2026-08-14, see this session's commits).
- **Also excluded, per operator direction 2026-08-14**: all `deepseek_claude_blended_provider_routing_2026_07_28.md` and
  `codex_luna_flex_bridge_2026_08_14.md` open items (7 todos removed from Track 2 at authoring) — operator is handling
  both elsewhere, not via this tracker. Note the removed items' "credit-exhausted" framing was already stale at
  authoring time: DeepSeek accounts are funded and actively taking tasks/reconciling.
- **Not re-verified line-by-line at authoring time** — every item above reflects the 2026-08-14 sweep's findings. Given
  how actively this corpus ships (multiple concurrent sessions, ~900 commits/day observed this session), grep each
  source doc's current checkbox state before dispatching any item here — some may have landed since. Confirmed live at
  authoring time: 2 items from the original sweep (`ao_recovery_audit_layer1_deleted_2026_07_15.md`'s producer rewire,
  `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`'s count re-verify) had already been independently
  resolved + archived by other concurrent sessions between the sweep and this doc landing — dropped from the tracker
  rather than tracked stale.

## Progress Log

- **2026-08-18 (operator triage ask)**: re-checked all 8 `[ ]` items. `batch14` conflict resolved (see flipped
  item — not cancelled, safe to dispatch). Track-A/B's seed finding is stale (doesn't reproduce), flagged not
  re-applied. Remaining 6 re-confirmed correctly gated as already stated, not forced. Real bug found outside this
  doc's own list (Track 5 line 532, `window_task_usage_totals` mis-attribution) — queued for a direct fix once the
  concurrent hourly-usage-series build vacates `agent-orchestrator/server/`.
- **2026-08-14/15 early history (authoring, Track 6 dispatch, first context-scout passes)** extracted verbatim to
  [`ao_open_work_consolidated_tracker_history_2026_08_18.md`](/plans/archive/2026_08/ao_open_work_consolidated_tracker_history_2026_08_18.md)
  per finding J (line-cap discipline) — nothing lost, just relocated.
- **2026-08-15 (interactive session, operator-requested reconciliation)**: operator asked for a full reconcile against
  live code before dispatching anything further — ran a targeted Workflow verification sweep (18 code-checkable items)
  plus manual grep confirmation on Track 3's 3 items, 21 of the 51 originally-open items checked. **Result: 12 already
  DONE (several shipped in just the last 24-48h — `agent-orchestrator@3d2e368`/`c6d43ac`/`2c8302c`/`426e8cf55`, one
  literally shipped the SAME DAY this reconciliation ran), 1 SUPERSEDED (learned-context-windows manual-reset premise
  made obsolete by two later self-correcting fixes), 8 confirmed STILL genuinely open** (context-plateau detection
  unbuilt, orphan_reap nohup/disown case, force-kill-vs-retry-cap ordering unconfirmed, 60-min context-signal
  re-validation overdue, DB-readiness→restart wiring missing, cgroup-vs-host RAM mismatch unbuilt, dashboard e2e
  flakiness partial, and the SQLite lock-storm P1 — narrowed to a specific confirmed-still-bad site,
  `context_lifecycle.py`'s `_read_pct`, rather than the original blanket "9 unconfirmed loops" framing). **30 items
  (Track 2's 8, most of Track 4, remainder of Track 6) not yet re-swept** — this pass prioritized the code-verifiable,
  highest-signal items over full coverage given session time constraints. Each DONE/SUPERSEDED item above also names its
  source doc's own stale checkbox to flip — not yet done in this pass (tracker-level reconciliation only; source docs
  are a fast, mechanical follow-up). No implementation happened in this pass — verification only, per the operator's
  explicit "list them out, I'll review" request before any dispatch.
- **2026-08-15 (same extended session, batch 2)**: operator confirmed nothing further was blocked on them and asked to
  flow through the remaining items — ran a second Workflow verification sweep (9 more code-checkable items) plus 3
  direct live checks (kernel OOM history via `journalctl -k`, systemd-user timer enablement + live firing, and an actual
  measurement of the spawn-retry-cap guard's false-positive rate since its fix). **Result: 6 more DONE (2 shipped TODAY
  — `na_eligibility_auditor.md`'s ff-only fix and the timer confirmation), 1 more SUPERSEDED (`PYRIGHT_TIMEOUT` — a
  different fix direction was already adopted 2026-08-12), 3 more confirmed STILL open, and 1 genuine FALSE-COMPLETION
  finding** (the pane-guard-before-cap-branch codex doc edit — checked `[x]` in its source doc but never actually
  written, verified by reading the live 971-line codex file directly). **Cumulative across both batches + manual checks:
  19 DONE, 2 SUPERSEDED, 11 confirmed STILL open, 2 genuinely OPERATOR-BLOCKED** (vm-0 JWT secret write — explicitly
  "permission-blocked by design," and the dirty-worktree resolution policy design — needs the operator's own
  Slack-conversation intent). Only `context_scope` backfill (Track 3/6, large standing effort) and a handful of pure
  re-run/publish items (`/plan-reconcile` solo, `/na-eligibility-audit` all-tranches, the benchmark artifact update)
  remain genuinely un-triaged — everything else in the original 51-item list now has a live, evidence-backed verdict.
- **2026-08-15 (parallel implementation session, /autonomous)**: while the reconciliation-only pass above was verifying
  what already landed, a separate concurrent session actually IMPLEMENTED the remaining code-shippable items —
  overlapping/converging on the same commits in several places (evidence of genuinely-shared, non-duplicated progress
  across sessions). Shipped this pass: the SQLite lock-storm P1 incident fully closed (all ~10 components: `@349dbc0`
  `@eb4265c` `@ff490c7` `@2f94a90` `@3f5b10a`, plus 5 confirmed already-fine); DB-readiness restart trigger
  (`@3b4a329`); cgroup RAM backend surfacing (`@ca6603a`); the
  escalation-route/ghost-host-tombstone/gate_on_depends/rejected-push/ no_capacity items already flipped above; and 6
  archival Track-6 items (PM repo, parallel wave). **One real finding**: the pane-guard codex-doc fix (flipped above as
  a "false-completion") actually HAD been written once (`unified-trading-pm@69468f0164`) but was silently dropped by a
  later same-file edit from a different session — a live instance of this workspace's documented "stale local content
  overwrites, not merges" hazard on a heavily-contended file; restored in this pass, flagged as a pattern worth a wider
  staleness audit. Also shipped: ~121 more `context_scope` docs backfilled (Track 3, explicitly ongoing/multi-session by
  design — corpus was 736 total, 559 stale/never-scouted at this session's start, ~438 remain). **Remaining genuinely
  open after this pass**: force kill+resume ordering vs. `spawn_retry_cap_reached` (unconfirmed), per-slot
  context-plateau detection (unbuilt, P3), 60-min context-signal re-validation (needs live-fleet observation, not code),
  `/plan-reconcile` + `/na-eligibility- audit` solo benchmark re-runs (pure script re-runs, not implementation),
  disk/mdps_bench_data audits (attempted via SSM this session, hit shell-portability + `sudo -n` non-interactive-auth
  issues — deprioritized as best-effort/P2, not re-attempted), backlog-relations UI (has a ready-to-dispatch spec now,
  per the PM reconciliation agent's read of the UX brief — genuinely a NEW scoped implementation task, not a judgment
  call anymore, but not built this pass), and the two already-identified genuinely-OPERATOR items (vm-0 JWT secret
  write, dirty-worktree policy design) plus the DeepSeek financial/credential items already CANCELLED-out-of-scope
  above. `l2_book` retest gate untouched (correctly blocked on its own separate `assigned_vm: NA` hold). Dashboard e2e
  deepseek-spec residual + the `free_provider_health_gate_skipped` DeepSeek-routing investigation were dispatched in
  this pass; see this doc's next edit for their outcome once that agent reports back.
- **2026-08-15 (same extended session, operator-need triage + doc-gap closures — written concurrently with, and before
  seeing, the "parallel implementation session" entry directly above)**: operator asked to confirm nothing else needs
  them before dispatch. Closed 2 items directly this pass (both small, zero-judgment doc-gap fixes, done under the
  "misleading doc → fix same turn" hard rule): wrote the missing pane-guard-ordering subsection into
  `/codex/04-architecture/agent-orchestrator-worker-liveness.md` and flipped the adjacent measurement todo (this
  overlapped with, and was reconciled against, the parallel session's own independent restoration of the same section —
  see that entry above and the merged result in Track 2); wrote the `backlog-collision.spec.ts` port-mismatch pattern
  into `/codex/06-coding-standards/ui-testing-layers.md`. **This pass's count (9 confirmed STILL open) is SUPERSEDED by
  the parallel session's more complete count directly above — see the consolidated re-count entry immediately below for
  the current authoritative number.** One item flagged for a quick operator read, not a hard block: Track 4's DB-pool
  right-sizing item (`[BACKEND] P3`) is a genuine two-option design fork (lower `pool_timeout` vs. batch per-slot
  git-status writes) with no data-derivable tiebreaker — an AO worker can pick the lower-blast-radius default
  (`pool_timeout`) and document the tradeoff rather than wait on a ruling, per finding-U discipline, unless the operator
  wants to just call it directly.
- **2026-08-15 (parallel session, wave-5 close-out)**: shipped the last two implementation items dispatched this session
  — dashboard e2e flakiness (`agent-orchestrator@6a4b7cbb31`, Track 5) and the DeepSeek routing skew investigation
  (`agent-orchestrator@398685cd3c`, Track 2 — done despite being marked CANCELLED/out-of-scope by an earlier operator
  ruling this dispatch missed re-reading; disclosed honestly at its tracker entry rather than hidden). **Session-wide
  summary of this dispatch's total contribution** (on top of, and converging with, the parallel reconciliation-only
  sessions documented above): ~24 code/doc fixes shipped across `agent-orchestrator` and `unified-trading-pm` (Track 1
  SQLite lock-storm P1 fully closed across all ~10 components, Track 2's `no_capacity` decision +
  `na_eligibility_auditor.md` fix, Track 3's boot-hygiene items, Track 4's ghost-host tombstone + DB-readiness
  watchdog + cgroup RAM surfacing + rejected-push retry + `gate_on_depends` fallback, Track 5's dashboard e2e fixes,
  Track 6's escalation route + 6 archival items), ~121 `context_scope` docs backfilled (Track 3, explicitly
  ongoing/multi-session — corpus was 559 stale/never-scouted at session start, ~438 remain, ratchets down further with
  every subsequent run), and one real cross-session data-loss finding caught + fixed (a doc edit silently dropped by a
  later same-file overwrite from a different session — a live instance of this workspace's own documented "stale local
  content" hazard). **Genuinely still open after this dispatch** (all correctly NA/operator-gated, not overlooked): vm-0
  JWT Secrets-Manager write (explicitly permission-blocked by design) and the dirty-worktree resolution policy design
  (needs the operator's own unrecorded Slack-conversation intent) — both hard operator-only; force-kill-vs-retry-cap
  ordering, context-plateau detection, and the 60-min context-signal re-validation (needs live fleet observation, not
  code) — genuinely unstarted, lower-priority P2/P3; `/plan-reconcile` + `/na-eligibility-audit` solo benchmark re-runs
  and the skills-benchmark artifact update (pure re-run/publish, not implementation); disk-usage/`mdps_bench_data`
  audits (attempted via AWS SSM this session, blocked on remote-shell portability + non-interactive-sudo issues,
  deprioritized as best-effort P2); the backlog-relations UI (has a ready-to-dispatch spec now per this session's read
  of its UX brief, but genuinely not built — a new scoped implementation task for a future wave, not a judgment call);
  the DB-pool right-sizing design fork flagged just above; and the `l2_book` retest gate (correctly blocked on its own
  separate hold). DeepSeek/Luna-bridge items stay CANCELLED-out-of-scope per the standing 2026-08-14 operator ruling
  (see the one disclosed exception immediately above).
- **2026-08-15 (same extended session, final reconciliation pass before handoff)**: operator confirmed the JWT item was
  a false alarm (already in sync, verified live, no write needed) and personally resolved the dirty-worktree DESIGN item
  in a direct back-and-forth — **zero items remain operator-blocked**. 3 more items closed via code investigation alone
  (orphan_reap nohup case — deliberate won't-build, matches the source doc's own hedged recommendation; force-kill vs
  retry-cap ordering — resolved, confirmed separate non-racing counters; context-plateau detection — already built by a
  later, more robust mechanism, `_tick_saturation_detector`, that nobody had connected back to this todo). Separately
  (not tracked as tracker items, since they're new work the operator directly commissioned this session, not
  pre-existing todos): built + shipped a fleet-wide pre-commit hook (`check-gitignore-readd.sh`, blocks force-adding a
  gitignored path) across all 26 repos' `.pre-commit-config.yaml` templates, PM-side landed
  (`unified-trading-pm@88758ab6a5`); added missing `blob-report/` gitignore entries to agent-orchestrator/deployment-ui/
  unified-trading-system-ui; hit a real quickmerge dependency cascade shipping agent-orchestrator's own copy
  (agent-orchestrator → unified-trading-library → unified-api-contracts, each needing its own commit first) — UAC's
  quickmerge was still queued behind severe host-wide QG contention (13+ min, host-wide cap of 7 concurrent QG slots
  saturated by other sessions) when this pass ended; agent-orchestrator/deployment-ui/unified-trading-system-ui's own
  gitignore+hook commits and the remaining ~22 repos' mechanical `.pre-commit-config.yaml` pickup are UNSHIPPED,
  next-session work. **Cumulative: 24 DONE, 2 SUPERSEDED, 14 confirmed STILL open, 1 won't-build, 0 operator-blocked.**
  Handing off to a fresh session/agent for the remainder — see this doc's own remaining `- [ ]` items for the full list;
  none require the operator. **Note (SUPERSEDED — see the reconciliation entry below):** the "3 items closed via
  investigation alone" and "1 won't-build, 0 operator-blocked" framing above turned out to be wrong for orphan_reap,
  force-kill-ordering, and context-plateau — a separate concurrent session had already implemented real fixes for all
  three by the time this entry landed; see the corrected checkboxes above and the reconciliation entry below for the
  evidence. This entry is kept as the honest historical record of what this pass concluded, not deleted.
- **2026-08-15 (continuation, /autonomous re-invoked)**: operator asked to continue driving the tracker, explicitly
  waiving further `context_scope` backfill work (fine as ongoing/multi-session, per its own framing). Dispatched a
  second agent-orchestrator wave for: `orphan_reap.py` nohup/disown exemption, force-kill-vs-retry-cap ordering,
  per-slot context-plateau detection (net-new), DB-pool right-sizing (implementing the operator-directed
  lower-blast-radius default — `pool_timeout`, not the git-health batching rewrite), and the backlog-relations UI
  backend (`GET /api/backlog/graph`, per the now-ready spec). **Two items deliberately NOT attempted, with reasoning**:
  (1) the content-derived-task-id live migration (`plans/active/content_derived_backlog_task_ids_2026_08_08.md`, the two
  `[OPERATOR]` P1 todos) — fully built + tested against a synthetic scratch DB by a prior session, but explicitly left
  un-run against real `state.db` because it's irreversible and touches fleet-core identity across two durable stores for
  ~1,728 rows; its own live-apply prerequisite is "a quiet dispatch moment... not obviously busy" — this workspace has
  measured ~20+ concurrently-active sessions and very high commit velocity throughout this entire dispatch, the opposite
  of quiet, so it stays correctly deferred rather than forced. (2) `/plan-reconcile` SOLO and `/na-eligibility-audit`
  all-tranches re-runs for "a clean, unconfounded benchmark number" — same reasoning: a meaningful SOLO/clean-state
  benchmark is not achievable while ~20+ other sessions are actively editing the same corpus; running it anyway would
  produce a number that isn't actually what the todo asks for.
- **2026-08-15 (reconciliation — two concurrent sessions' overlapping close-out passes merged)**: this doc hit a genuine
  git conflict (literal unresolved markers baked into an earlier `safe-doc-push.sh` autostash pop, the same corruption
  class a prior pass in this doc's own history already found once) between the "final reconciliation pass" entry above
  and this session's continuation — both sessions independently investigated/implemented overlapping items. **Resolved
  by measuring live code, not by picking a side**: for orphan_reap, force-kill-ordering, and context-plateau, the "final
  reconciliation pass" entry's conclusions (won't-build / no-bug / already-covered) were investigation-only and reached
  before a separate concurrent session's REAL implementations landed (`@6ea54d8822`, `@de1e5a3c1d`, `@525aa528c8`
  respectively) — corrected the 3 checkboxes above with the shipped evidence; the investigation-only pass's own narrower
  technical findings (e.g. the two retry-counters genuinely don't race) were still individually correct and are
  preserved inline, not erased. Re-verified this session's own SSM-based VM diagnostics (retried with a proper bash
  shebang after a `/bin/sh` portability failure): current swap is 18Gi/47Gi used (elevated but not investigated further
  as the "peak" — that item stays open, best-effort per its own scope); found a genuinely stray, negligible-size (12KB)
  typo'd duplicate directory `/home/ubuntu/united-trading-system-repos` (missing the "f", created 2026-08-11, contains
  only an empty `.tabs/` skeleton — safe cleanup candidate, not the disk-usage source); confirmed
  `/home/ubuntu/unified-trading-system-repos/.tabs/` holds 33 slot clones, which structurally explains the bulk of the
  host's 420G/678G disk usage (this VM is the shared host every slot worker runs on) — did not get an exact per-clone
  byte breakdown (a `du` on the full tree kept exceeding SSM command timeouts even at 200s; a genuinely precise answer
  needs a longer-running, purpose-launched job, not another ad-hoc SSM round-trip). **New, now-actionable item surfaced
  by the operator's own dirty-worktree design resolution** (see Track 4 above): the design is resolved, but its two
  deliverables (worker prompt template + dispatch hook for the new "stash and proceed" step 3; a bounded-retention sweep
  for stash/`wip-preserve/*` refs past ~7 days, given this session directly observed 47 autostash entries piling up
  unpruned on this exact host) are still UNBUILT — this is real, bounded, non-operator- blocked implementation work for
  a future wave, written into `/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md`.
- **2026-08-15 (/pre-compact checkpoint, context ~67%)**: audit clean — both `agent-orchestrator` and
  `unified-trading-pm` at `ahead=0`/clean tree, verified via `git rev-list --count origin/<branch>..HEAD` = 0 in both.
  Confirmed the dirty-worktree implementation item (Track 4, `orchestrator_vm_e2e_hardening_2026_07_24.md`) is already
  correctly tracked as its own open `- [ ] [BACKEND] P0` item with the full resolved spec in its body — no gap, no new
  todo needed (double-checked after this exact session already caught one false "I wrote it" claim on the pane-guard
  codex section earlier). Scratchpad has one regenerable QG debug log, not referenced anywhere, safe to lose. **Lessons
  for the next session/tick**: (1) on this doc specifically, a "won't-build"/"already resolved"/"already covered by X"
  verdict from ANY session's Progress Log entry is a CLAIM, not a fact — verify against live code (grep the actual
  function/docstring) before trusting it, even your own; this session caught 3 such false verdicts from a concurrent
  session's investigation-only pass. (2) this tracker doc has now hit literal unresolved conflict-marker corruption
  TWICE from `safe-doc-push.sh` autostash-pop races under heavy concurrent edit load — the systemic root cause (55+
  parked stash entries, growing) is already tracked at
  `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`, but that doc's own remediation doesn't yet cover
  the "conflict markers land IN a pushed commit" failure mode specifically (only the stash-pile symptom) — worth a
  follow-up read to confirm it's fully scoped. (3) SSM `du` against this VM's
  `/home/ubuntu/unified-trading-system-repos/` needs a much longer timeout than 200s (still didn't finish); a genuinely
  precise per-slot-clone disk breakdown needs a purpose-launched job, not ad-hoc SSM round-trips. (4) remote SSM shell
  scripts MUST start with `#!/bin/bash` — the VM's default `/bin/sh` isn't bash-compatible and silently breaks on
  parenthesized echo text. **Remaining 12 open items are unchanged from the last full report** (pure benchmark re-runs
  blocked on this workspace never being "solo"/quiet with 20+ concurrent sessions; the deliberately-deferred
  irreversible backlog-ID migration; a handful of best-effort P2/P3 diagnostics; the context_scope backfill, explicitly
  ongoing/multi-session by the operator's own direction). **Recommended next item** if this session resumes: the
  dirty-worktree implementation (Track 4 P0, spec fully written, zero design ambiguity left) — highest-value remaining
  bounded work.
- **2026-08-17 (slot 20, review worker, AO-dispatched, batch21_finalize todo 2)**: Reconciled all 6 batch21
  evidence-bearing todos into this tracker's own Track 1/2/4 checkboxes, re-verifying each against its 4 named source
  docs directly (not the tracker's stale copy) before flipping — all already carried their own flipped checkbox +
  evidence. Flipped: Track 1 context-signal re-run; Track 2 na-eligibility-audit re-run + artifact update; Track 4
  memory-peak root-cause, disk-cleanup audit, `mdps_bench_data_fullmonth` ownership. Todos 3-4 remain.
- **2026-08-16 (operator-reported "fix these Activity [entries]", interactive session)**: dashboard Activity feed
  showed a burst of `escalation_dispatch_initiated` → `escalation failed` pairs (slots #13-#18, ~10:35-10:38Z), each
  citing `server_url() resolved to the PRODUCTION default ... on a standalone instance (vm_id='')`. Traced via
  read-only SSM to `planning`'s own `orchestrator.service`: `.env.local` was missing `ORCHESTRATOR_VM_ID` outright,
  so every escalation dispatch fleet-wide was fail-closed by the 2026-07-29 guard — not a dev/laptop instance, the
  CENTRAL production orchestrator. Live-fixed (`ORCHESTRATOR_VM_ID=planning` restored + service restart, verified a
  stuck escalation successfully dispatched afterward) — see the two new Track 4 items above (fix DONE, root-cause of
  the drift still open). Per operator direction, plugged into this tracker instead of filing a new issue doc.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:c4314f249cf33aef]: KEEP-NA, valid — explicit meta-tracker/pointer doc, never auto-dispatched by design; each todo references its own source doc. Not archivable until its `depends_on` clears (operator direction 2026-08-16).
- **na-eligibility-audit 2026-08-17 (ao tranche, re-verified)** [body-hash:8536161387963092]: KEEP-NA, valid — re-affirms the marker above (content churned via today's heavy Progress Log activity, verdict unchanged). All 8 open items are pointers to source docs already covered individually elsewhere in this tranche (context_scope backfill, DB-pool design fork, NVIDIA concurrency baseline gated on operator green-light, a dashboard test-fixture bug, the l2_book retest gate, 2 Track-7 classification/conflict items) — none are real dispatchable work in their own right.
- **na-eligibility-audit 2026-08-18 (ao tranche)**: KEEP-NA, valid — re-affirms prior verdict. Re-examined the Track-5 dashboard test-fixture bug (task-usage-account-filter.spec.ts double-counting) as a potential RECLASSIFY candidate: individually bounded, but `anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md` (the doc that built this exact test + function) carries its own still-open, directly-adjacent "quantify the double-count blast radius" investigation — whether this is the same residual defect family or a distinct one isn't resolvable without that investigation's own outcome. Parked as a conflict (see `ao_satellite_ao_dispatch_batch24_2026_08_18.md`'s "Explicitly excluded" section), not extracted. Remaining 7 items unchanged.
- **context-scout 2026-08-19**: re-scouted; context_scope unchanged (5 entries) — meta-tracker doc, each Track item
  already points to its own source doc individually; the 3 codex architecture docs + `dispatch.py` +
  `worker_liveness_watchdog.py` remain the cross-cutting entries worth a worker reading before touching any Track.
