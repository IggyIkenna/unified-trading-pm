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
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
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
depends_on: []
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

---

## Track 1 — Worker liveness / failover / dispatch correctness

- [x] [REVIEW] P2. **DONE — shipped `agent-orchestrator@3d2e368`** (2026-08-14, after this tracker's own authoring).
      `retire_orphaned_blocked_rows()` (`server/blocked_reconcile.py:564`) now called at both `reassign_slot`
      (`server/routes/slots_ops.py:763`) and `skip_current_task` (`:1060`) — the `auto_orphaned_slot_reassigned`
      disposition + `blocked_retired_auto_orphaned_slot_reassigned` log event this todo asked for, exactly. Verified
      2026-08-15 (`/ag-closeout-audit`-style reconciliation sweep, this session). Source:
      `/plans/active/issues/ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06.md` — flip its own
      checkbox too, same evidence.
- [x] [REVIEW] P3. **DONE.** Both `_migrate_parking_state` failure paths now `logger.warning(...)` on drop
      (`server/regen_backlog_from_plan.py` — no-candidate branch ~2876-2895, below-threshold branch ~2899-2919), each
      inline-citing this issue doc. Verified 2026-08-15 (reconciliation sweep, this session). Source:
      `/plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md` (its one remaining open todo,
      "consider an alerting surface," is a separate, deliberately-open P3 — not this claim).
- [x] [REVIEW] P2. **DONE.** `_sweep_unpushed_slots` now calls `heal_dead_slot_branch_quarantine` directly
      (`server/worker_liveness_watchdog.py:1953`) inside its own unconditional per-tick sweep — fires every tick
      regardless of backlog state, no `_do_spawn` gate. Verified 2026-08-15 (reconciliation sweep, this session).
      Source: `/plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` — its own
      checkbox + Progress Log are stale (still describe the gap as open as of 2026-08-03), flip + close.
- [ ] [INFRA] P3. **`orphan_reap.py` special-case a worker-shell-parented detached background process** (distinct from
      the already-fixed CPU-progressing-quickmerge guard — this is `nohup`/`disown`-style background jobs a worker
      itself launched via `run_in_background`). Also cross-check the RAM-exhaustion doc's journalctl signatures against
      `orphan_reap`/`kill_session` — never done. Source:
      `/plans/active/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`.
- [ ] [BACKEND] P1. **STILL OPEN, scope narrowed 2026-08-15 (reconciliation sweep, this session).** `HealthMonitor`
      (`server/health.py:144-160`) and `AgentKeeper` (`server/main_agent_keeper.py:1166-1184`) are now ALSO confirmed
      fixed (explicit "Read/act/write split" docstrings), and `WorkerLivenessKicker`'s `_tick_once` structurally already
      reads-then-acts-then-writes — so 5 of ~10 loops are clean, not 2. `UsagePoller`/
      `AutoParkReconciler`/`RepoHealthWatcher` never made `has_session`/`capture_pane` calls at all — never guilty, just
      contention victims. **The confirmed-still-bad one: `context_lifecycle.py`'s `_read_pct` (~line 1354-1373, called
      every tick for main/review/every worker) still opens `session_scope()` and calls `capture_pane()` (a tmux
      subprocess) INSIDE that open write transaction — the exact anti-pattern, still live today.** `AutoSpawnLoop`/
      `PlanReconcilerLivenessCanary`/`BlockedQueueReconciler` not yet re-checked. **DO-NOT-ARCHIVE guard stays on the
      source doc.** Source: `/plans/active/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`.
- [x] [REVIEW] P2. **DONE.** `WorkerLivenessKicker` now auto-submits a frozen `/compact`/`/pre-compact` at/above
      `context_worker_compact_gate_pct` (`server/worker_liveness/__init__.py:988-1027`, logs
      `frozen_guided_compact_auto_submitted`), citing this exact todo. Verified 2026-08-15 (reconciliation sweep, this
      session). Source: `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`
      (line ~136) — checkbox is stale, flip it.
- [ ] [BACKEND] P2. **Force kill+resume reachable BEFORE `spawn_retry_cap_reached`, ordering unconfirmed.** No commits
      since 2026-08-08 touch `_respawn.py`'s ordering; whether `retry_count` counts each force-resume attempt is still
      an open question. Source: same doc, line ~141.
- [ ] [BACKEND] P3. **Per-slot context-plateau detection — unbuilt.** `grep -r "plateau"` returns zero hits in
      agent-orchestrator. Source: same doc, line ~145.
- **[REVIEW] P3. CANCELLED — SUPERSEDED 2026-08-15 (reconciliation sweep, this session).** Was: manually inspect/reset
  `learned_context_windows.json` once the fleet is fully on sonnet-5. Two follow-on fixes shipped + archived since
  (`ao_learned_context_window_registry_never_revalidates_2026_08_09`,
  `ao_deepseek_context_window_unknown_and_self_repoisoning_2026_08_10`): `context_probe.context_window_for()` now
  self-corrects a poisoned/under-estimated entry at READ time against a repeatedly-confirmed watermark, and
  `model_tier._ALLOWED_MODEL_WINDOWS` carries a corpus-measured sonnet-5 prior (937,882 tokens / 17,974 transcripts) as
  the cold-start fallback. The manual purge-and-relearn this todo asked for is obsolete — the same correction now
  happens automatically. Source: same doc, line ~342.
- [ ] [BACKEND] P2. **Re-run the 60-min context-signal validation after a clean fleet — overdue.** Multiple qualifying
      changes to `context_lifecycle.py`/`context_probe.py` have landed since 2026-08-08 (`a1e2969`, `59d9417`,
      `c00dc13`, `acc41b1`, `4af78dc`, `ac9ba18`, `905c210`, `c730f46`, `e943d72`+) with no re-run recorded since the
      2026-08-10 audit. Source: same doc, line ~411.
- [x] [REVIEW] P3. **DONE.** `DoneRequest.claude_session_id` field exists (`server/models/worker_api.py:275`);
      `_done_one_off` (`server/routes/slots_worker.py:1912-1924`) matches it against the archived row's own
      `claude_session_id` and returns idempotent 200 instead of 409. Tracker's premise ("still has no field") is stale.
      Verified 2026-08-15 (reconciliation sweep, this session). Source:
      `/plans/active/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md` (its own
      "declined-P3, revisited" section already narrates this as shipped — flip the checkbox to match).

## Track 2 — Scheduled jobs, benchmarking, model/provider routing

- [ ] [DATA] P3. **Measure whether the hoisted working-pane guard actually reduced false spawn-retry-cap pages**
      (baseline: 45 cap declarations, 8 false `pane=working` pages, `agent-orchestrator@9d26598`) — cheap, still
      unmeasured since 2026-08-06. Source: `/plans/active/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md`.
- [ ] [DOC] P3. Document the pane-guard-before-cap-branch ordering invariant in
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md`. Source: same doc.
- [ ] [BACKEND] P3. Decide keep-vs-drop on the `no_capacity` legacy status. Source: same doc.
- [ ] [OPERATOR] P2. Re-install all 7 scheduled-job systemd-user timer units on the live VM (installers already
      converted to `systemd --user`, `agent-orchestrator@c3a85c3b4`) — actual re-install unverified from a dev checkout.
      Source: same doc.
- [ ] [SCRIPT] P1. Re-run `/plan-reconcile` (whole-corpus) SOLO for a clean, unconfounded benchmark number. Source:
      `/plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`.
- [ ] [SCRIPT] P1. Re-run `/na-eligibility-audit` (all 9 tranches + integrate) for a clean steady-state benchmark.
      Source: same doc.
- [ ] [SCRIPT] P2. Add `git pull --ff-only` to `na_eligibility_auditor.md` STEP 1 (the orchestrator VM's shared PM
      checkout goes stale between runs — `plan_reconciler.md` already has this fix, the na-eligibility skill doesn't).
      Source: same doc.
- [ ] [DOC] P2. Update the published skills-benchmark artifact once the two re-runs above land. Source: same doc.
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
- **[REVIEW] P3. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: investigate why the flash
  variant trips `free_provider_health_gate_skipped` ~30% more than pro. Source: same doc.
- **[REVIEW] P1. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: re-run the local
  DeepSeek-routing pilot against the redesigned policy. Source: same doc.
- **[DATA] P2. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: give the
  `deepseek_flash_route_fraction` remeasure instruction an actual runnable tool. Source: same doc.
- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: ratio-check DeepSeek
  account-count/cost assumptions. Source: same doc.
- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-14 (operator, out-of-tracker-scope).** Was: address the DeepSeek
  wallet balance top-up recurrence. Source: same doc.

## Track 3 — Boot / context / session hygiene

- [ ] [SCRIPT] P0. **Backfill `context_scope` frontmatter corpus-wide, then harden the field to `Req.R` (required) in
      `scripts/docs/docspec.py`.** Confirmed still `Req.E` (elective) as of this session; backfill itself is large,
      ongoing, multi-session work — re-run the inventory script for a current NEVER_SCOUTED count before scoping
      further. Source: `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md` (also tracked, do not duplicate, in
      `/plans/active/context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`).
- [x] [REVIEW] P1. **DONE.** `server/prompts.py:296` now has a literal curl body for the `/boot` STEP 2 call. Verified
      2026-08-15 (manual grep, this session). Source:
      `/plans/active/issues/ao_boot_stub_session_vars_field_name_mismatch_2026_08_02.md`.
- [x] [REVIEW] P2. **DONE.** Zero `worktree_path` hits left in `server.py`/`routes/agents.py`/`autospawn.py` — the
      rename is complete. Verified 2026-08-15 (manual grep, this session). Source: same doc.
- [x] [REVIEW] P3. **DONE.** `BootRequest` carries `model_config = ConfigDict(extra="forbid")`
      (`server/models/worker_api.py:50`), with a comment citing this exact todo. Verified 2026-08-15 (manual read, this
      session). Source: same doc — with all 3 Track-3 items from it now done, check whether the source doc itself is
      fully closeable.

## Track 4 — Infra / VM / host hygiene

- [ ] [CREDS] P0. **Finish vm-0 Secrets-Manager wiring**: align the blob's stale `ORCHESTRATOR_JWT_SECRET` (SM ← vm-0).
      Exact operator commands already staged as of 2026-08-08 — spot-check they're still current, then run. Source:
      `/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md`.
- [ ] [DESIGN] P0. **Design the dirty-worktree resolution policy** (Ikenna, Slack 2026-06-12 — the "no dirty worktrees"
      next-phase flow). Genuinely unbuilt; the existing `resolve_dirty_state()` is a different, fresh-spawn-only gate.
      Source: same doc.
- [ ] [DIAG] P2. Best-effort root-cause the specific 49.3G/16G-swap peak more precisely, if feasible. Source:
      `/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`.
- [ ] [OPERATOR] P2. Confirm/rule out kernel-level OOM-killer activity via `dmesg`/`journalctl -k` with root access.
      Source: same doc.
- [ ] [BACKEND] P2. **Wire the DB-aware readiness signal to an actual restart trigger.** `_readiness_check()` already
      does a real `select(1)` DB probe (has since 2026-05-19, predates the issue) — but no installer polls `/readiness`
      to act on it; every `ExecStartPre` health-gate only hits `/api/healthz` (liveness). Source:
      `/plans/active/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md`.
- [ ] [BACKEND] P3. Right-size/harden the DB pool for known concurrency — the "raise pool_size/max_overflow" option is
      already disproven by this doc's own occurrence #6/#7 evidence (root cause was write-lock-holding-during-spawn); no
      code addresses the surviving design fork. Source: same doc.
- [ ] [BACKEND] P2. **Surface a cgroup-vs-host RAM mismatch on the dashboard/alerting.** `host_resources.py` reads only
      host-level `/proc/meminfo`; no cgroup-specific memory-stat reader (`memory.current`/`memory.high`/ `memory.max`)
      exists anywhere. Source:
      `/plans/active/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`.
- [ ] [DATA] P2. Audit `unified-trading-system-repos/` (157G, dominant disk consumer) for real cleanup headroom. Source:
      `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md`.
- [ ] [DATA] P2. Investigate ownership/purpose of `/home/ubuntu/mdps_bench_data_fullmonth/` (3.8G). Source: same doc.
- [ ] [SCRIPT] P3. Consider a fleet-wide `PYRIGHT_TIMEOUT` bump if a QG kill recurs outside a burst window — still
      hardcoded at 120s in `base-service.sh`, watch-condition not yet triggered. Source:
      `/plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`.
- [x] [REVIEW] P3. **DONE — shipped `agent-orchestrator@426e8cf55` TODAY (2026-08-15).** New `server/host_tombstone.py`:
      `is_host_tombstoned()`/`tombstoned_since()`, `ip-172-31-0-185` hardcoded as a fail-safe floor + live AWS EC2
      existence check for future ghost hosts. Resolved the design fork as tombstone-never-prune (row stays for audit
      trail); wired into `models/git_health.py` + `routes/git_health.py:361,428` to exclude tombstoned hosts from
      fleet-wide stale/drift totals. Verified 2026-08-15 (reconciliation sweep, this session, same day as the shipping
      commit). Source: `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` — flip its
      checkbox too.
- [ ] [OPERATOR] P2. Run the dry-run + live-apply steps for the content-derived-task-id migration against ~1,728 legacy
      positional ids (minting itself already shipped and live). Source:
      `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md` (tracked live in
      `/plans/active/content_derived_backlog_task_ids_2026_08_08.md`, do not duplicate there).
- [x] [REVIEW] P2. **DONE — shipped `agent-orchestrator@c6d43ac`** (2026-08-14).
      `worktree_clean_check/_ahead_push.py::push_or_preserve_ahead_commits` (lines 262-283): on a rejected push,
      re-verifies against the new HEAD, restamps the sentinel (`_restamp_sentinel_at_head`), and emits a distinct
      `ahead_push_rejected_and_stale` event. Regression:
      `test_sweep_rejected_push_restamps_sentinel_and_flags_rejected`. Verified 2026-08-15 (reconciliation sweep, this
      session). Source:
      `/plans/active/issues/ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md` — flip + archive
      if now 0 open todos.
- [x] [REVIEW] P2. Per-occurrence audit of the ~14 `BLOCKED-PREREQ` files in the active corpus (external-gate-mislabel
      vs. same-corpus-dependency), then re-grep-and-confirm as a follow-up. Source:
      `/plans/active/issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`. **DONE
      2026-08-14** — the ~14-file population had shrunk to exactly 2 files / 6 live occurrences by re-check time (rest
      already fixed/archived independently since 2026-07-28). All 6 classified as genuine case-(b) same-corpus
      dependencies (none mislabeled-external), confirmed still genuinely blocked as of 2026-08-14, full disposition
      table in the source doc's Progress Log. Both of the source doc's own todos closed; spawned 1 new tracked follow-up
      (`[BACKEND] P3`, the residual `agent-orchestrator` design question) — doc correctly stays open, not archived (real
      design work remains).
- [x] [REVIEW] P3. **DONE — shipped `agent-orchestrator@2c8302c`** (2026-08-14). `_upstream_plan_open_on_disk()`
      (`server/regen_backlog_from_plan.py:2483-2516`) is now the single shared definition used by BOTH
      `_wire_gate_on_depends_prereqs` and `gate_on_depends_unmet_upstreams_on_disk`, including the checkbox-scan
      fallback (`_plan_has_any_unchecked_checkbox`) this todo asked for. Verified 2026-08-15 (reconciliation sweep, this
      session). Source: `/plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` — flip
      its checkbox too.

## Track 5 — Dashboard e2e flakiness

_Governed by `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`'s own stated rule: "do not edit a source doc's
checkboxes beyond appending evidence; the paired finalize plan reconciles this" — check that finalize plan's status
before touching the source doc directly._

- [ ] [TEST] P2. Root-cause `deepseek-per-turn-metrics.spec.ts` + `deepseek-wallet-reconciliation.spec.ts` intermittent
      failures — some fix evidence exists elsewhere (timeout bump, poller no-op) but no explicit re-run-confirmation is
      recorded against THIS todo. Source: `/plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`.
- [ ] [TEST] P3. Root-cause `backlog-collision.spec.ts`'s intermittent "click Fix" failure (async-completion race in
      remint→confirm). Source: same doc.
- [ ] [DOC] P3. Note the fix pattern in `/codex/06-coding-standards/ui-testing-layers.md`, including the
      "PlanRegenLoop-in-mock-mode" general class, once root-caused. Source: same doc.
- [ ] [INFRA] P3. Split Playwright's `webServer` config so a single-project e2e run doesn't boot all 6 backend+dashboard
      pairs. Source: same doc.

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
      `status: active →     complete`, all corpus-wide referrers repointed.
- [ ] [SCRIPT] P2. Finish the `context_scope` backfill named in `batch3`'s own open todo (see Track 3) — this is what
      still gates `batch3_finalize`'s 5 todos via `gate_on_depends`. Source:
      `/plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`.
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
- [ ] [UI] P3. Build the backlog-relations UI (`backlog/graph` endpoint doesn't exist yet). Source: same doc.
- [ ] [REVIEW] P3. Re-test the `l2_book` microstructure-capture retest gate once
      `/plans/active/l2_book_microstructure_capture_2026_07_13.md` clears its own `assigned_vm: NA` hold. Source: same
      doc.

---

## Notes

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

- **2026-08-14 (authoring)**: Created from the 5-parallel-agent code-audit sweep of 44 AO-subject-matter docs run
  earlier this session. 10 already-implemented-but-unflipped items were fixed directly (not tracked here — see
  `unified-trading-pm@0969b12571`/`9906379de6`); the gcloud WIF-poisoning security issue was fully resolved + archived
  (`unified-trading-pm@f34adbc7f1` + supporting commits); 58 items confirmed genuinely still open, as of that sweep.
- **2026-08-14 (same-day correction)**: 7 DeepSeek-routing todos CANCELLED per operator direction — that work + the
  Luna/Flex bridge are handled outside this tracker; the "credit-exhausted" gate the first cancelled item cited was
  already stale (accounts funded, DeepSeek actively taking tasks). 51 items remain genuinely open above.
- **2026-08-14 (Track 6 dispatch, sub-agent)**: Worked all 6 assigned Track-6 items to completion — archived batch6 +
  batch6_finalize, batch7 + batch7_finalize, and batch5 + batch5_finalize (all 0-open-todos, full 6-step ritual, corpus
  referrers repointed); applied the RULED 2026-08-06 disposition sweep to the 12 operator-gated docs + bucketed the 7
  unclear docs from `ao_orphan_audit_followup_triage_2026_07_30.md` (archived that doc too, 0 open todos after both
  items); audited the ~14 `BLOCKED-PREREQ` occurrences down to 6 live ones, all confirmed genuine same-corpus
  dependencies, spawned 1 tracked design-question follow-up. **Known residual, not fixed this pass**: `INDEX.md`'s regen
  repeatedly failed to land via `safe-doc-push.sh` (3 attempts, each reporting "THE PUSH LANDED BUT YOUR CHANGE DID NOT"
  against a large, extremely stale local stash pile — 48 autostash/safety-snapshot entries) — reverted the local copy to
  match HEAD rather than keep fighting a pre-existing systemic issue tracked at
  `/plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` (F4/F8); `INDEX.md`
  is machine-regenerated by the daily hygiene sweep regardless, so this is cosmetic staleness, not a correctness gap.
  Also hit + recovered from 2 genuine stash-pop merge conflicts mid-session (both were redundant duplicates of
  already-landed content, resolved by keeping the landed HEAD version; one conflict resolution surfaced and fixed a real
  content duplication bug in the triage doc). See the individual archived docs' own Progress Logs for full per-item
  evidence.
- **context-scout 2026-08-15**: populated/refreshed context_scope (5 entries) — kept to the Track 1/Track 2 codex SSOTs
  - dispatch.py/worker_liveness_watchdog.py; this tracker's own design is "each todo cites its Source doc", so a wider
    list would duplicate what's already per-item.
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
