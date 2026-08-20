---
doc_type: plan
title: AO satellite AO batch 1 — first dispatch batch extracted from the AO tranche's satellite docs
summary: >-
  FIRST AO-dispatch batch for the `ao` topic tranche, produced by the `/ag-closeout-audit` skill's full Phase-0/1/2/3
  procedure over all 35 AO-tranche-primary docs (2026-07-26, autonomous mode). The tranche had NO batch plan at all and
  its consolidated closeout carries ZERO todos, so 32 of 35 docs came back orphaned. Phase 3's conflict check cleared 10
  of them into fresh AO-dispatch todos — one pair of near-duplicate todos across two source docs merged into a single
  combined todo citing both — and left the rest in the Deferred sections below, dominated by one large
  worker-liveness/watchdog cluster where two docs prescribe OPPOSITE directions on the same kick/escalation mechanism.
  Every todo below targets files disjoint from every sibling todo, so the plan needs no `sequential` gate.
status: complete
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, deployment-ui, unified-trading-system-ui]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-1, satellite-docs]
related:
  [
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous, operator unreachable) — Phase 0 resolved the tranche membership
  as the 35 Sources of ao_consolidated_closeout_2026_07_25.md and found no existing ao batch/finalize pair; Phase 1 read
  all 35 docs end-to-end single-threaded (no Workflow/Agent tool exists in that environment); Phase 3 ran the conflict
  grep over every candidate target file against the whole plans/active corpus before drafting.
---

# AO satellite AO batch 1

> **🟢 ARCHIVED 2026-08-01** — all 11 todos `[x]`, `locked_by:` empty. Finalized by
> `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`: every done-claim re-verified against
> reality, evidence reconciled into all 11 TRUE source docs, every Deferred item's gate re-checked (2 cleared into
> `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md` (renamed from a mistakenly-numbered "batch 2"),
> the rest still genuinely gated or already resolved elsewhere), and the one net-new fully-resolved doc found during
> that re-check (`escalation_backlog_repo_collision_blind_spot_2026_07_25.md`) archived alongside it.

## Why this plan exists (the coverage gap, measured)

`/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md` (archived 2026-07-30) carried **zero todos**
(`grep -c '^- \[ \]'` and `grep -c '^- \[x\]'` both return 0; `assigned_vm: NA`, `execution_scope: local-only`) — it is
a Sources digest plus close-out criteria, exactly the "digest, not real dispatch" shape the `/ag-closeout-audit` skill
describes. No `ao_*batch*` plan has ever existed for this tranche. So nothing was working the specific open items inside
the 35 satellite docs. This plan extracts the conflict-clear, bounded-outcome subset of that work.

## Rules for every worker on this plan

- **Put each todo's new test cases in a test module named for that todo's own concern** — never add to a test module
  another todo on this plan also touches. The todos below are file-disjoint by construction; keep them that way.
- **Do not edit the source issue doc's checkboxes** beyond appending your evidence line to the todo you executed. The
  paired finalize plan (`/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`) reconciles
  evidence back into every source doc and runs archival.
- No todo below deletes prod data, mutates a GCS bucket, launches a VM, or writes a secret — so none carries
  `[OPERATOR]` on those grounds. Todo 9 is explicitly read-only and must not push or delete anything.

## Todos

- [x] ✅ [BACKEND] P1. **DONE 2026-07-26 (slot-7, `backend_engineer`) — `agent-orchestrator@361e0fe`.** Break the SQLite
      write-lock wedge that starves the orchestrator connection pool — split read-only sessions off `BEGIN IMMEDIATE` in
      `agent-orchestrator/server/db.py` (`_on_begin` currently issues `BEGIN IMMEDIATE` for EVERY transaction including
      reads, so `/api/state`'s `list_slots` read contends for the single SQLite writer), align `pool_timeout` against
      the `busy_timeout` PRAGMA set in `_on_connect` so lock contention surfaces as "database is locked" rather than as
      an opaque "QueuePool limit reached", and audit every remaining caller of `autospawn._do_spawn` for one still
      wrapping the slow spawn in its own `session_scope()`. Added `read_only_session_scope` — its connection carries
      `execution_options(orch_read_only=True)`, which `_on_begin` checks to skip `BEGIN IMMEDIATE` and fall through to
      SQLite's default deferred BEGIN (WAL already allows concurrent readers); wired into `state.py`'s 4 genuinely
      read-only handlers (`get_state`, `get_activity`, `get_activity_rollup`, `get_fleet_kpis`) — `agent_poll` stays on
      `session_scope` since it writes every call (ping update + drain). `pool_timeout` (was the SQLAlchemy default 30s)
      now set to `busy_timeout + 5s` via one `BUSY_TIMEOUT_MS`/`POOL_TIMEOUT_S` source of truth in `db.py`, with the
      reasoning + why `busy_timeout` itself is kept at 120s (not lowered) recorded in a code comment. **`_do_spawn`
      audit verdict: all 5 real callers** (`autospawn.py` ×3 — `ensure_review_agents`/`_run_one_tick`/`_resume_pass` —
      plus `escalation.py` + `plan_health.py`) **already run the slow spawn with no session held** (confirmed by reading
      each call site, not just grep) — Phase 2 of the archived `orchestrator_spawn_reliability_db_lock_2026_06_10`
      landed everywhere, not only `ensure_review_agents`. Found + fixed 2 stale comments in
      `escalation.py`/`plan_health.py` that still described the pre-fix (wrong) "keep the spawn inside the session"
      behavior. New regression test (`tests/test_db_read_only_session.py`) empirically proves a
      `read_only_session_scope` session does not block on a real held write lock (0.001s vs. a >10s hold), with a
      control proving the identical scenario genuinely blocks on a plain `session_scope` (validates the test harness).
      Full `agent-orchestrator` `quality-gates.sh` green (1760 passed, 1 skipped, 49.83s). Did NOT raise
      `pool_size`/`max_overflow` per the source doc's own occurrence #6/#7 evidence. Source:
      `/plans/archive/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` (BACKEND P1 ×2 + P2 timeout
      alignment). Do NOT also raise `pool_size`/`max_overflow` — that doc's own occurrence #6/#7 evidence supersedes the
      resize direction.
- [x] ✅ [BACKEND] P2. **Add a zero/collapse circuit-breaker to the PlanRegenLoop prune path** —
      agent-orchestrator@d66fbf2. Added to `_prune_stale()` in `agent-orchestrator/server/regen_backlog_from_plan.py`: a
      scan of `>= _PRUNE_NONTRIVIAL_SCAN_THRESHOLD` (20) plans that derives zero open todos, or fewer than
      `_PRUNE_COLLAPSE_FRACTION` (0.25) of the already-recorded prunable backlog, now skips `prune_stale` entirely, logs
      a loud WARNING, and cancels nothing (compared against the current backlog.yaml content, which by construction only
      ever reflects the last successful/kept-safe tick — no extra cross-tick state needed). A state.db health probe
      (`SELECT 1 FROM tasks LIMIT 1`) runs before any mutation; a real read failure (not the pre-existing "missing
      `tasks` table" misconfiguration case) aborts the WHOLE prune (yaml + db), not just the db leg. Evidence: 3 new
      tests (`test_prune_stale_circuit_breaker_skips_on_zero_derivation`,
      `test_prune_stale_circuit_breaker_skips_on_collapse`,
      `test_prune_stale_aborts_before_any_prune_on_db_read_failure`) + full `quality-gates.sh` green (1763 passed, 1
      skipped; ruff/basedpyright clean). Source:
      `/plans/archive/issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md`
      (BACKEND P2 ×2 — combined here because both change the same prune path in the same file). That doc's third todo
      (positional task-ids) is NOT in scope — see this plan's Deferred section.
- [x] ✅ **DONE 2026-07-26 (slot-11, `infra`) — `unified-trading-pm@804fa2b9a`.** Made
      `unified-trading-pm/scripts/dev/slot-git-status-report.sh` prefer `http://localhost:8765` (trusted-local, no
      bearer token) when the loopback backend is reachable, falling back to the public `ORCH_URL` + `ORCH_TOKEN_FILE`
      when it is not, so an expired/rotated `~/.orch_token` can no longer silence a whole host's git-health view. Did
      NOT unconditionally flip the default `ORCH_URL` — off-VM operator laptops still get the public URL + token path
      (only skipped when `ORCH_URL` was never explicitly set via env or `--orch-url`). **Done when, verified**: ran the
      reporter live against the real orchestrator with `ORCH_TOKEN_FILE` pointed at a deliberately garbage token, scoped
      to slot 11 — `[loopback] http://localhost:8765 reachable...` fired and the POST succeeded
      (`[ok] slot 11 — 25 repos reported`); `/api/fleet/git-health` immediately showed `reporter_stale=false` for
      slot 11. Off-VM branch verified BY READING THE CODE (not just on-VM behaviour): `_ORCH_URL_EXPLICIT` gates the
      probe off entirely when `--orch-url`/`ORCH_URL` is set, so a laptop reporter keeps the public URL + token path
      unconditionally. **"Wired into quality-gates.sh"**: partially — added 7 new hermetic bats tests
      (`tests/test_slot_git_status_loopback_preference.bats`) covering the new logic, all passing (14/14 total with the
      pre-existing `test_slot_git_status_dirty_count.bats`), but discovered `bats tests/` is not actually invoked by
      `quality-gates.sh`/`base-service.sh` for ANY `.bats` file in this repo — a pre-existing, cross-cutting gap bigger
      than this todo (touches the shared fleet-wide `base-service.sh`). Filed as its own properly-scoped finding rather
      than absorbed here: `/plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`. Both source
      docs' matching todos flipped with evidence:
      `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (INFRA P2) and
      `/plans/archive/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (SCRIPT
      P2).
- [x] [INFRA] P2. ✅ **Gate the git-health dirty signal on `dirty_consecutive_ticks >= 2` at BOTH decision sites** — the
      `not_clean_since` clear plus the sync-nudge in `agent-orchestrator/server/routes/git_health.py`, and the FF-pull
      skip decision in `unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh` — so a one-tick phantom-dirty reading can
      neither reset `not_clean_since` nor make the FF-pull cron skip. **Done when**: a unit test proves a single clean
      poll between two dirty polls does NOT reset `not_clean_since`, and a second check proves a one-tick phantom dirty
      does not produce an FF-pull skip; `quality-gates.sh` green. **Already shipped** — verified on this pass, checkbox
      was simply never flipped: `agent-orchestrator@2530316` (`_propagate_not_clean_since`/`_maybe_send_sync_nudge`
      gate + `tests/test_git_health_dirty_consecutive_ticks_gate.py`, 4 tests incl. the exact clean-blip-between-two-
      dirty-polls case) and `unified-trading-pm@dd172d6b7` (`ff_one()`'s per-repo `dirty_consecutive_ticks>=2`
      confirm-gate in `slot-cron-ff-pull.sh` + `tests/test_slot_cron_ff_pull_dirty_gate.bats`, incl. the one-tick-
      phantom-does-not-skip case and cross-repo isolation). Both trees clean at HEAD on this repo/slot. Source:
      `/plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md` (both remaining INFRA P2 todos
      — combined because they are one gate applied at two sites, both now flipped too). Per that doc's own 2026-07-23
      narrowing, do NOT re-hunt a reporter-internal race unless a post-`agent-orchestrator@529b0dc` recurrence is
      observed.
- [x] ✅ [UI] P2. **Derive the Playwright dev-server port per slot instead of from a shared constant** in
      `deployment-ui/playwright.config.ts` and all three `webServer` blocks of
      `unified-trading-system-ui/playwright.config.ts`, keeping `reuseExistingServer: true`, and log the resolved port
      plus whether a server was reused or freshly spawned so a cross-slot attach is visible rather than silent. Derive
      the slot number from the checkout path and fall back to the existing fixed default when not in a slot clone; the
      slot-identity SSOT is `scripts/hooks/slot-identity-lib.sh`. **Done when**: two concurrent runs launched from two
      different slot clones with NO `PLAYWRIGHT_PORT` override each attach only to their own dev server, with the
      resolved port and reuse status printed in each run's output — cite `pw:L2 ✓` plus the specific spec file per
      `/codex/06-coding-standards/ui-testing-layers.md`. Source:
      `/plans/archive/issues/playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md` (UI P2, Option A).
      This is a DIFFERENT file set from `agent-orchestrator/dashboard`'s own playwright config — do not touch that one.
      — `deployment-ui/playwright.config.ts@5663aa0` already shipped this half pre-session (verified via `git log`).
      This session shipped the `unified-trading-system-ui` half: `unified-trading-system-ui@369eea00` — derived
      `NEXT_PORT=3100+SLOT`/`API_PORT=8030+SLOT` in `tests/e2e/_shared/config.ts` (E2E_CONFIG, the repo's own "single
      source of truth for e2e test-run tunables"), wired all 3 `webServer` blocks + `use.baseURL` off it, and added
      reuse/spawn console logging matching the deployment-ui pattern. Config verified for slot 15 (`tsx -e` dump:
      `slot=15 nextPort=3115 apiPort=8045`); confirmed via live log output that the reuse-detection correctly prints
      `ALREADY UP, will be REUSED` vs `not up, will be freshly SPAWNED`. `pw:L2 ✓` — full `tests/smoke/` first hit 65
      timeouts under measured severe host contention (load 24→53 on 16 cores, other slots' activity, not this change —
      same environment-blocker class as `ui_hardcoded_colour_and_localhost_debt_2026_07_21.md` Batches 1/4); rather than
      fabricate a suite-wide green, cited the narrower evidence this todo's own done-when asks for:
      `tests/smoke/wizard-stepper.spec.ts` (4/4 passed, 56.7s, clean). Full `quality-gates.sh` (typecheck/lint/286
      tests/build/DeFi-citation) green end-to-end, 224s, sentinel `1306658c`→`369eea00` after quickmerge (one
      branch-drift rebase mid-ship, clean fast-forward). **Adjacent finding (not fixed here, outside this todo's file
      list)**: ~40 `tests/e2e/**/*.spec.ts` files (L3a/L3b layer, not part of the `pw:L2` gate) hardcode
      `http://localhost:3100`/`:8030` directly and don't import `E2E_CONFIG`, so they remain exposed to the original
      cross-slot false-result bug this fix closes for the smoke gate — filed
      `/plans/archive/issues/unified_trading_system_ui_e2e_specs_hardcode_ports_bypass_per_slot_derivation_2026_07_28.md`
      with 3 batched follow-up todos, all shipped and the doc archived 2026-08-01.
- [x] ✅ [BACKEND] P1. **DONE 2026-08-01 (interactive session) — read-only, verified live.** This session's ambient AWS
      identity (`arn:aws:iam::427895769566:user/harsh-worker`) is not the `ikenna-worker` identity denied below —
      `aws ssm send-command` against `i-0c9b283b31d6b5ca7` worked immediately, no grant needed (the source doc's own
      `[BACKEND] P1` todo was independently self-serviced + closed the same way on 2026-07-29 by a different identity;
      this is a fresh reconfirmation on a later day, not a duplicate of that check). All three checks, run live via SSM
      against `/home/ubuntu/unified-trading-system-repos/agent-orchestrator` on `i-0c9b283b31d6b5ca7`: (a) deployed HEAD
      = `4f9514a6177d0450d7f3170aa3d8910be8339412`, upstream = `origin/live-defi-rollout`,
      `git merge-base --is-ancestor 867b1731e HEAD` → **YES, ancestor**. (b) `.schema tasks` on the live
      `data/state/state.db` shows `sequential INTEGER NOT NULL DEFAULT 0` — **column exists**. (c) queried
      `SELECT plan_ref, COUNT(DISTINCT dispatched_to) ... GROUP BY plan_ref HAVING slots > 1` against the live DB — **10
      non-sequential plans have tasks spread across 4-9 distinct slots** (e.g.
      `deployment_api_sigabrt_crash_loop_2026_07_24.md` across 9 slots), confirming the fan-out. **All three checks
      pass.** Source: `/plans/archive/issues/dispatch_sequential_gate_fix_2026_07_24.md` — its own `[BACKEND] P1` todo
      is already `[x]` (closed 2026-07-29); this batch todo was simply never flipped to match. That doc's `[DOCS] P1`
      codex-edit todo is NOT in scope — codex edits are never autonomous, needs operator sign-off.
- [x] ✅ [BACKEND] P3. **DONE 2026-08-01 — `agent-orchestrator@7cd01e67c75`.** Added
      `test_head_backward_canary_still_detects_legitimate_post_fix_realign` to `tests/test_dirty_state_resolution.py` —
      reuses the exact allowed-realign scenario from the sibling
      `test_orphan_realigns_normally_when_pre_existing_ahead_commit_is_old_enough` (old-enough pre-existing ahead commit
      clears the Part-B age guard, dirty content on top triggers the orphan-wip inherit path, the real (fixed)
      `commit_and_push_dirty_repos` runs the actual `checkout -B` realign), then calls
      `head_backward_canary.detect_discards_in_repo` against the resulting repo state and asserts exactly one hit with
      `preserved_ref` set (safe via wip-preserve, but still DETECTED — proving the fix did not blind the canary to this
      legitimate case). Confirmed passing
      (`pytest tests/test_dirty_state_resolution.py tests/test_head_backward_canary.py` — 48 passed) and that the canary
      needed NO source modification (only a new test). Source:
      `/plans/archive/issues/slot_double_reset_dataloss_race_2026_07_25.md` (BACKEND P3 — its own checkbox was already
      `[x]` deferring execution to this plan; this closes that deferral with the actual test).
- [x] ✅ [BACKEND] P3. **DONE 2026-08-01 — read-only audit, no code changed (`auto_park.py` untouched, per scope).**
      Read `server/models/slots.py:116`
      (`SkipCurrentTaskRequest.reason_code: Literal["BLOCKED","PARKED","GATED","OTHER"]` — a closed, exhaustive set),
      `server/routes/slots_ops.py`'s `/skip-current-task` handler, and
      `auto_park.py::maybe_auto_park`/`_park_task`/`_ESCALATING_REASON_CODES` directly (not grepped). Full per-code
      table written into `/plans/archive/issues/gated_skip_park_no_slack_page_2026_07_25.md`'s Progress Log:
      BLOCKED/PARKED/GATED all reach durable park via the same `_park_task` call site and all page Slack identically (no
      per-code branching in `notify_task_auto_parked`); OTHER never reaches the durable-park mechanism at all
      (`maybe_auto_park` early-returns), so it's structurally exempt from this class of gap. **Verdict: zero uncovered
      codes found — the GATED fix (`agent-orchestrator@fd749e3b6`) fully generalizes.** This clears the gate below.
      Source: `/plans/archive/issues/gated_skip_park_no_slack_page_2026_07_25.md` (BACKEND P3).
      `/plans/archive/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` is now
      unblocked to dispatch (noted in its own Progress Log) — its implementation is out of scope for this audit-only
      todo.
- [x] ✅ [REVIEW] P2. **DONE — confirmed already resolved at the source, no re-run needed.** Read the archived source
      doc directly: it carries its own 2026-07-30 dated verdict (ARCHIVED banner) covering all 7 commit-sets —
      agent-orchestrator's `WorkerLivenessWatchdog` exists (`server/worker_liveness_watchdog.py` + 4 test files),
      deployment-service's consolidator watchdog exists (`vm_zombie_watchdog.py`/`deadman_poster.py`/
      `cloud_run_job_registry.py`), market-tick-data-service's tardis concurrency cap/`book_snapshot_5`/
      `available_from_datetime` filtering all covered more extensively, strategy-service's kill-switch subscriber exists
      in more complete form, unified-api-contracts' incident/risk/circuit-breaker modules exist,
      unified-trading-library's `cloud_interface/messaging.py` exists verbatim, and the 7th (a `ruff format` commit) is
      trivial/moot. Verdict: superseded-in-spirit, nothing lost, no cherry-pick needed — and the doc's own banner states
      verbatim "flip that todo whenever that plan is next touched." Doing so here; no independent re-verification
      performed (this todo's own **Done when** is satisfied by the doc's existing dated verdict, not a fresh per-item
      table). Source: `/plans/archive/issues/orphan_rootm_branch_unmerged_work_2026_06_05.md` (OPERATOR P2, already
      `[x]`).
- [x] ✅ [BACKEND] P3. **DONE 2026-08-01 — `agent-orchestrator@7cd01e67c75`.** Leave a durable trace on any delete of a
      `status='done'` orchestrator `tasks` row. So the unexplained done-row disappearances stop needing post-hoc
      forensics. A SQLite trigger is the mechanism the source doc proposes precisely because it fires regardless of call
      site (including out-of-band SQL); add it through the existing idempotent per-column/DDL migration pattern in
      `agent-orchestrator/server/bootstrap.py` so a fresh `state.db` self-heals. **The trace must not break the
      sanctioned operator delete** — `DELETE /api/backlog/{task_id}` legitimately removes a done row on operator request
      and must still succeed — so record rather than raise. **Done when**: a test proves a direct SQL delete of a done
      row leaves a queryable trace, a second proves the sanctioned operator-delete endpoint still succeeds and is traced
      not blocked, and `quality-gates.sh` is green. Source:
      `/plans/archive/issues/ao_backlog_done_row_disappearance_2026_07_25.md` (BACKEND P3, resolved 2026-07-28 — see
      note below). Note for the worker:
      `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md` is an explicitly-parked decision
      that also names `bootstrap.py`/regen ids — do not touch task-id derivation here.

      **2026-07-28 update — the actual root cause was found and fixed at the application level** (an UPDATE status
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      regression in `release_task_to_queue()`, not a bare DELETE — see the resolved issue doc), which left this
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      todo's original DELETE-trigger idea a narrower, discretionary defense-in-depth item rather than the primary
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      mitigation. **2026-08-01 — built as that defense-in-depth backstop.** Added
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `bootstrap.py::_migrate_done_task_delete_trace()` — an idempotent migration creating `deleted_done_tasks_trace` +
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      an `AFTER DELETE ON tasks WHEN OLD.status = 'done'` SQLite trigger, which fires regardless of call site
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      (including a raw out-of-band SQL delete the application-level guard cannot see, since that guard only catches an
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      illegal transition made through the ORM). The trigger only INSERTs, never raises. 4 new tests in
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `tests/test_done_task_delete_trace.py`: a raw SQL delete of a done row leaves a trace; the sanctioned
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `DELETE /api/backlog/{task_id}` path still succeeds unconditionally AND is traced; deleting a non-done task
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      leaves no trace (the `WHEN` clause is status-specific); the migration is idempotent across repeated
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `create_all_tables()` calls. Full detail + evidence in
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `/plans/archive/issues/ao_backlog_done_row_disappearance_2026_07_25.md`'s Progress Log.

- [x] ✅ [REVIEW] P3. **DONE-IN-SUBSTANCE 2026-08-01 — via a more rigorous successor pass than this todo originally
      specified, not by literally editing the named doc.** `ao_consolidated_closeout_2026_07_25.md` (the doc this todo's
      "Done when" asks to edit) was **archived 2026-07-30**, and its own archival banner already redirects membership
      authority away from itself: "Archiving it does NOT close the AO tranche's underlying work — that live picture is
      tracked in `ao_satellite_ao_dispatch_batch1_2026_07_26.md` … and the still-open
      `ao_open_issues_consolidated_close_out_2026_07_17.md`, not here." Editing dead text in an archived digest to say
      "epic query" instead of "Sources list" would not change what any live tooling actually reads. The substantive ask
      — triage the Sources-list-vs-epic-query delta — was instead completed against the doc that IS live
      (`ao_open_issues_consolidated_close_out_2026_07_17.md`) via a 2026-07-31 full-content audit of all 88
      `repos`/`parent_epic`-matched issue-doc candidates (read individually, not epic-filtered): **62 confirmed
      genuinely AO-tranche** (36 already correctly `asset_group:[ao]`-tagged + 26 mistagged-but-genuine, now itemized in
      the tracker's own classification table) and **26 confirmed false-positives** (broad multi-repo audits,
      PM/audit-tooling bugs, unrelated content, shared-host/CI-tranche infra — full per-doc reasoning in
      `/plans/active/issues/ao_tranche_full_content_audit_findings_2026_07_31.md` §1). This is a superset of what a
      mechanical `parent_epic ∈ {...}` query would have found (a content read, not a tag filter) and supersedes this
      todo's own "~40-doc delta" estimate with an exact, evidenced 62/26 split. **Not closed by this todo**: the 23-doc
      retag pass and the 26-exclusion-list confirmation are operator-gated decisions, tracked as their own `- [ ]` todos
      in that same findings doc (§1/§2) — this todo's own scope (triage the delta + establish the real membership count)
      is what's done here.

## Deferred — conflict-gated (do NOT draft competing todos; re-check in batch 2)

> **🟢 2026-07-31 re-triage pass completed** (interactive session, not a batch2/3 run) — the ordering question below IS
> now ruled + shipped (soften `agent-orchestrator@64b5310`, harden confirmed pre-existing `@77fc60a`), and the
> `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md` prerequisite shipped
> (`agent-orchestrator@49c919d`). Per-doc re-triage verdicts (still-gated / cleared / reclassified-as-never-actually-
> gated / needs-one-more-check) are recorded in each source doc's own Progress Log, not duplicated here — see
> `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md`,
> `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` (checkbox fixed),
> `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md`,
> `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (still gated, different reason — root cause
> unidentified), `one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md` (reclassified),
> `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md` (reclassified),
> `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` (reclassified),
> `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` (needs one more live check).

- **The worker-liveness / watchdog kick+escalation cluster — a head-on directional contradiction.**
  `/plans/archive/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` (INFRA P2) wants the
  watchdog to escalate soft-kick → hard-kill + respawn FASTER ("after N consecutive `post_kick_classification=frozen`
  observations (e.g. N=3, ~15-20 min) instead of soft-kicking indefinitely"), while
  `/plans/archive/issues/host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md` (BACKEND P1, filed
  five days later) says the frozen classification is itself a FALSE POSITIVE under host load and must be softened
  ("require the ping/pane to be stale across TWO consecutive verify windows … Done when: a regression test … produces
  ZERO `worker_kicked` events"). Landing the first without the second escalates false kicks into false HARD-kills on
  genuinely-progressing workers. Four more docs claim the same mechanism from other angles:
  `/plans/archive/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md`,
  `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` (its second todo also
  reorders the kill+resume-vs-`spawn_retry_cap` escalation),
  `/plans/archive/issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` (INFRA P1, don't reap a
  CPU-progressing detached quickmerge), and
  `/plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`. **Escalated as an
  operator question** (see this run's report) — the ordering is a design call, not a mechanical merge.
- **Failover re-dispatch release-signal / liveness re-check** —
  `/plans/archive/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (BACKEND P2). Bounded and
  well-evidenced (four incidents, one on a CODE task), but it turns on the same "is a silent worker actually dead"
  judgment as the cluster above, so it must be sequenced after that ordering is ruled.
- **`/done` acceptance semantics** — `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` (INFRA P1,
  gate `/done` on the code being on origin) and `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`
  (BACKEND P3, make `/done` idempotent + owner-checked) both change the same `/done` handler in
  `server/routes/slots_worker.py`. They are compatible in direction but must land as one change, and the on-origin gate
  interacts with the operator-merge-gate governance question in
  `/plans/archive/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md` (P1, a held-behind-a-gate
  push must NOT be auto-shipped). Re-triage once that doc's gate-aware sweep decision exists.
- **AutoSpawn no-eligible-worker gap** —
  `/plans/archive/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md`
  (BACKEND P2 + two P3 audits). FILE-COLLISION-gated only: it changes `server/autospawn.py`, which todo 1 of this plan
  may also touch. Straightforward batch-2 material once todo 1 lands.
- **Rejected-push recovery in `_ahead_push.py`** —
  `/plans/active/issues/ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md`. Its own doc calls
  this "the single riskiest automated code path in the system" and says the fix needs a real design decision; a
  characterisation test alone would land in `tests/test_watchdog_unpushed_sweep.py`, the same module the gate-aware
  sweep fix above will need. Held on both counts.
- **Periodic dirty-resolution sweep** — `/plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md`
  (BACKEND P2 ×2). Adding a NEW automatic caller of `commit_and_push_dirty_repos` (a realign path that has already
  destroyed work — see `slot_double_reset_dataloss_race_2026_07_25.md`) while the operator-merge-gate bypass above is
  unresolved is exactly the compounding this skill's non-batchable taxonomy warns about. Re-check after the gate-aware
  sweep decision.
- **Regen positional task-ids** — **RULED 2026-07-28** (operator gated-decision closeout pass, general theme applied:
  "opt for full completions, no shortcuts, full functionality... if it's about canonicalisation rather than a hack, do
  it properly"). `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md` BACKEND P3
  duplicates `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`, which
  `/plans/archive/2026_07/ao_issue_docs_consolidated_remediation_2026_07_23.md` (archived 2026-07-27) recorded as a
  parked decision "deferred until a new incident forces it". **Ruling: the 2026-07-25 incident
  (`sync_backlog_to_db: REFUSING to reset task id` collisions) DOES meet the deferral's own trigger** — reinforced by a
  second, independent guard-gap found 2026-07-27 (a `dispatched` row has NO equivalent protection at all, confirmed in
  the issue doc's own 4th todo). Two guard classes now proven insufficient is stronger than the single-incident bar the
  deferral was waiting on. **Retagged BLOCKED-OPERATOR-DECISION → normal execution work** — do the content-hash rewrite
  now, full scope (not a partial patch): see
  `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`'s updated `[BACKEND] P3` todo for
  the fully-scoped mandate. Do NOT draft a competing batch todo here — dispatch that issue doc's todo directly once
  picked up.
- **`slack-read-channel.py` env-var token fallback** —
  `/plans/archive/issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md` SCRIPT P3. Its stated blocker has
  CLEARED (measured 2026-07-26: `check_no_empty_string_fallback.py --scope unified-trading-pm` reports
  `319 (== baseline)`, so the 320>319 ratchet breach that reverted the diff is resolved — that doc's own BACKEND P2
  ratchet todo is now done-in-substance and is a `/plan-reconcile` flip candidate, not batch material). **No longer
  BLOCKED-OPERATOR-DECISION** — the `os.getenv()`-vs-"never touches disk or argv" tension resolves via the same
  self-service IAM path used elsewhere (finding W /
  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`): grant `secretmanager.versions.access` on the
  relevant secret to `unified-trading-sa` so Secret Manager/gcloud-ADC reads succeed in-process for every AO identity —
  exactly the script's stated design — which obviates the banned `os.getenv()` fallback path entirely; no compliance
  conflict remains once that grant is made. That SCRIPT P3 todo lives in the source doc (out of this batch's file scope)
  — dispatch it there as a normal AO todo (make the grant, verify a live read, remove the env-var fallback), not as an
  operator escalation.
- **QG-harness worktree-isolation defects** —
  `/plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` items 4 and 5. Item 5 (a `PROJECT_ROOT`
  override making the `.qg_last_passed_sha` sentinel record MAIN's HEAD instead of the worktree's) changes what "QG
  green" MEANS — the per-repo quality boundary itself. Too high blast-radius for a batch todo; needs its own scoped plan
  with operator sign-off.

## Deferred — operator decision needed (not batchable, no re-triage will clear it)

- `/plans/archive/issues/escalation_backlog_repo_collision_blind_spot_2026_07_25.md` — its Todos heading literally reads
  "NOT for autonomous dispatch as-is"; the first todo is `[OPERATOR-DECISION]` on directionality (a)/(b)/(c) and the
  second is explicitly blocked on it.
- ~~`/plans/archive/issues/auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md` — a three-way fork whose
  option (c) is "explicitly rule this is not worth building".~~ **RESOLVED 2026-07-29** (batch closeout pass) — decided
  option (c), explicitly declined to build mechanism-level enforcement (reasoning in the issue doc's own todo); no code
  shipped, doc archived. No longer a live design fork.
- ~~`/plans/archive/issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md` — `[OPERATOR]` shape
  decision gating the `[SCRIPT]` implementation.~~ **RULED 2026-07-28** (operator gated-decision closeout pass — this
  decision is the standing theme's own named example: "Things should recover FULLY if they die or restart (e.g. CI
  runners on the planning VM) -- if a decision is about auto-recovery robustness, prefer building the full automatic
  recovery, not just a manual runbook note"). Ruling: DO BOTH — ship the manual runbook step now as an immediate safety
  net, and wire the automatic `setup-glue-runners.sh install` step into `launch-central-brain-aws.sh` as the real,
  full-completion fix (not a fallback). See the issue doc's updated todos for the fully-scoped mandate. No longer a
  design fork — retagged out of `[OPERATOR]`; not batched into THIS batch (file-scope), pick up as a normal execution
  todo from the issue doc directly.
- `/plans/archive/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md` — a section explicitly titled
  "Candidate fixes (not yet decided)", two legs of which are codex/CLAUDE.md edits (never autonomous).
- `/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md` — "Explicitly NOT actioned"
  per operator instruction; the one bounded leg (capture `claude_session_id` on `BlockedRow` at creation time) would
  start implementing a redesign the operator deferred.
- `/plans/archive/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md` — carries an explicit operator decision "not
  needed right now … Revive by scheduling these todos".
- `/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md` — all three open todos are operator-gated (two `[CREDS]`
  secret/IAM writes, one `[DESIGN]` dirty-worktree policy including an operator-sanctioned hard reset).
- `/plans/archive/2026_07/agent_orchestrator_alert_channel_cleanup_2026_07_13.md` — **RESOLVED 2026-07-27**: all todos
  closed with evidence, plan archived; no longer a candidate here.
- `/plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md` — **RESOLVED 2026-07-31**: its one remaining todo
  (AF-2-followup) closed via direct live re-measurement, all todos `[x]`, plan archived; no longer a candidate here.
- `/plans/archive/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` — **no longer
  operator-gated**: its `[OPERATOR]` P1 todo's sole blocker was needing "an operator-chosen maintenance window" for the
  shared-orchestrator restart, which the 2026-07-28 CLAUDE.md ruling ("Maintenance-window restarts (e.g. orchestrator)
  skip operator scheduling pre-live-trading… group + do now, brief downtime OK") clears. The source doc's own tag still
  reads `[OPERATOR]` (out of this batch's file scope to retag directly) — next time that doc is touched, retag to
  `[DEVOPS]`/`[SCRIPT]` P1 and dispatch directly: group with any other pending shared-orchestrator restart/pause work,
  execute now, verify the service comes back healthy afterward.
  `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` `[INFRA]` P3 (re-mint
  `~/.orch_token`) remains a distinct credential operation, unaffected by this ruling. Their code-side siblings ARE in
  this batch as todo 3.
- `/plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md` and
  `/plans/archive/issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` per-slot WIP recovery items
  — each needs foreign-worktree access plus a judgment call on whether specific commits are superseded.
- `/plans/archive/issues/ao_backlog_done_row_disappearance_2026_07_25.md` — **stale tag here**: its watch-log-check todo
  is already `[SCRIPT]` P1 in the source doc, downgraded from `[OPERATOR]` on 2026-07-27 ("Category B, read-only: this
  is a log-tail check via the same read-only AWS SSM path… not a human-only action"); it is a normal AO-dispatchable
  read-only SSM poll (`/check-agent-orchestrator` / `check-ao-backlog-status.sh`), no operator gate. Its `[BACKEND]` P2
  (root-cause once a recurrence is caught) remains genuinely time-gated on an unobserved recurrence.
- `/plans/archive/2026_07/ao_issue_docs_consolidated_remediation_2026_07_23.md` (archived 2026-07-27) — both open items
  were `BLOCKED-OPERATOR-DECISION` / `BLOCKED-UPSTREAM-DESIGN` by their own labels and are now marked DEFERRED rather
  than held open.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`,
`/codex/06-coding-standards/ui-testing-layers.md` (todo 5), `/codex/04-architecture/autonomous-recovery-matrix.md`
(todos 1 and 10).

## Progress Log

- **2026-07-26** — Authored by `/ag-closeout-audit ao` (autonomous mode, operator away). Phase 0 resolved membership as
  the 35 Sources of `/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md` (archived 2026-07-30) and found the
  closeout carries zero todos and no `ao_*batch*` plan exists. Phase 1 read all 35 docs end to end (single-threaded —
  the run environment exposed no Workflow/Agent tool, so the skill's per-doc fan-out could not be used); 2 docs are
  archivable now, 1 is covered by `/plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md`, and 32 are
  orphaned. Phase 3 grepped every candidate target file (`server/db.py`, `regen_backlog_from_plan`,
  `slot-git-status-report`, `routes/git_health`, `slot-cron-ff-pull`, `playwright.config.ts`, `head_backward_canary`,
  `auto_park.py`, `server/bootstrap.py`, `test_watchdog_unpushed_sweep`, `_ahead_push`, `stale_dispatch`,
  `slots_worker.py`) across the whole `plans/active` corpus; two apparent collisions were refuted by reading the hits
  (the `ao_dashboard_backlog_detail_queue_lag_e2e_flaky` playwright mention is a stashed-diff reproduction note about a
  DIFFERENT config file, and every `regen_backlog_from_plan` hit in `ao_open_issues_consolidated_close_out` is
  diagnostic prose, not a competing change), and the genuine ones are in the Deferred sections above. Four facts were
  measured rather than assumed while drafting and are recorded inline in the todos that depend on them: the DB-pool root
  cause is still unfixed at HEAD, the 7 `tab/rootm/*` branches no longer exist anywhere, `867b1731e` is on LDR but not
  on `main`, and the PM empty-string-fallback ratchet is back at baseline. **Left `status: draft` deliberately** —
  flipping to `active` is the operator's call.
- **2026-07-26** — Flipped `status: active` per resolution of
  `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #22 (option B: flip batch, hold finalize —
  `gate_on_depends: true` on the finalize sibling already reconciles once this batch's todos land, nothing to reconcile
  yet).
- **2026-07-28** — Operator gated-decision closeout pass: both design-choice items this plan flagged as
  `BLOCKED-OPERATOR-DECISION`/an operator-decision fork were RULED. (1) Regen positional task-ids — the 2026-07-25
  incident meets the deferral's own "new incident" trigger; do the content-hash rewrite now, full scope (see the updated
  `regen_positional_task_ids_not_content_stable_2026_07_17.md`). (2) CI-runner re-registration on planning-VM relaunch —
  do both: ship the manual runbook step now, wire the automatic reinstall into `launch-central-brain-aws.sh` as the real
  fix (see the updated `central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md`). Neither is executed from
  this plan directly (out of this batch's file scope) — both are now normal execution work at their source docs, ready
  for the next AO dispatch. Plan-only change, no code shipped.
- **2026-08-01** (interactive session) — **All 6 remaining todos closed; this plan reaches 11/11 `[x]`.** Todo 6
  (sequential-gate live-VM verify) and todo 9 (rootm-branch present/absent) were confirmed already resolved at their
  source docs, just never flipped here — no new work needed, checkboxes reconciled. Todo 8 (skip-current-task
  reason_code audit) executed fresh: read-only, found zero uncovered codes, cleared the gate on
  `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`. Todo 11 (Sources-list-vs-epic-query
  triage) resolved as done-in-substance by the 2026-07-31 full-content audit already recorded in
  `ao_open_issues_consolidated_close_out_2026_07_17.md` and
  `issues/ao_tranche_full_content_audit_findings_2026_07_31.md` — editing the literal doc this todo named
  (`ao_consolidated_closeout_2026_07_25.md`) is moot since it archived 2026-07-30 and its own banner already redirects
  membership authority elsewhere. Todos 7 (canary regression test) and 10 (durable delete-trace trigger) shipped real
  code: `agent-orchestrator@7cd01e67c75` — full `quality-gates.sh` green (2162 passed, 2 skipped; ruff/basedpyright/
  dashboard tsc+vitest all clean). Evidence reconciled back into every named source doc per this plan's own "Rules for
  every worker" section. **This plan now has zero open todos and `locked_by:` is empty** — its gated
  `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` sibling's `depends_on` gate has cleared as a direct result;
  not executed in this pass (separate plan, separate scope — flagged to the operator rather than assumed).
