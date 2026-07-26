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
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, deployment-ui, unified-trading-system-ui]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-1, satellite-docs]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_07_25.md,
    /plans/active/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
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

> **`status: draft` — NOT ingested, NOT dispatched.** Flipping this to `active` is the operator's call
> (`/plans/PLAN_FORMAT.md`; CLAUDE.md § "Plan destination — ASK BEFORE CREATING"). It was authored while the operator
> was away, so it deliberately stops at draft.

## Why this plan exists (the coverage gap, measured)

`/plans/active/ao_consolidated_closeout_2026_07_25.md` carries **zero todos** (`grep -c '^- \[ \]'` and
`grep -c '^- \[x\]'` both return 0; `assigned_vm: NA`, `execution_scope: local-only`) — it is a Sources digest plus
close-out criteria, exactly the "digest, not real dispatch" shape the `/ag-closeout-audit` skill describes. No
`ao_*batch*` plan has ever existed for this tranche. So nothing was working the specific open items inside the 35
satellite docs. This plan extracts the conflict-clear, bounded-outcome subset of that work.

## Rules for every worker on this plan

- **Put each todo's new test cases in a test module named for that todo's own concern** — never add to a test module
  another todo on this plan also touches. The todos below are file-disjoint by construction; keep them that way.
- **Do not edit the source issue doc's checkboxes** beyond appending your evidence line to the todo you executed. The
  paired finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`) reconciles evidence back
  into every source doc and runs archival.
- No todo below deletes prod data, mutates a GCS bucket, launches a VM, or writes a secret — so none carries
  `[OPERATOR]` on those grounds. Todo 9 is explicitly read-only and must not push or delete anything.

## Todos

- [ ] [BACKEND] P1. **Break the SQLite write-lock wedge that starves the orchestrator connection pool** — split
      read-only sessions off `BEGIN IMMEDIATE` in `agent-orchestrator/server/db.py` (`_on_begin` currently issues
      `BEGIN IMMEDIATE` for EVERY transaction including reads, so `/api/state`'s `list_slots` read contends for the
      single SQLite writer), align `pool_timeout` against the `busy_timeout` PRAGMA set in `_on_connect` so lock
      contention surfaces as "database is locked" rather than as an opaque "QueuePool limit reached", and audit every
      remaining caller of `autospawn._do_spawn` for one still wrapping the slow spawn in its own `session_scope()`.
      **Measured at HEAD 2026-07-26 (still open)**: `_on_begin` is unconditional; the `busy_timeout=120000` PRAGMA
      comment in `db.py` still points at the never-landed fix "tracked in
      orchestrator_spawn_reliability_db_lock_2026_06_10", a plan that has since been ARCHIVED; `ensure_review_agents`
      HAS already been refactored to call `_do_spawn` outside its transaction, so that leg is done and must not be
      redone. **Done when**: a read-path session no longer takes the write lock (proved by a test in which a simulated
      long write-lock hold does not block a read-path session), the two timeouts are aligned with the reasoning recorded
      in a code comment, any still-wrapping `_do_spawn` caller is named (fixed, or recorded as already-correct), and
      `bash scripts/quality-gates.sh` is green. Source:
      `/plans/active/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` (BACKEND P1 ×2 + P2 timeout
      alignment). Do NOT also raise `pool_size`/`max_overflow` — that doc's own occurrence #6/#7 evidence supersedes the
      resize direction.
- [ ] [BACKEND] P2. **Add a zero/collapse circuit-breaker to the PlanRegenLoop prune path** in
      `agent-orchestrator/server/regen_backlog_from_plan.py`: when a regen tick derives `total=0`, or the derived total
      collapses by more than ~75% versus the last successful tick while `scanned` is non-trivial, skip `prune_stale`
      entirely, keep the prior backlog, log a loud WARNING and cancel nothing; and make the tick abort WITHOUT pruning
      when the derivation could not complete because DB reads were failing. **Done when**: one test proves a simulated
      empty derivation leaves the existing backlog intact and cancels zero in-flight tasks, a second proves a simulated
      collapse is likewise skipped, a third proves a DB-read failure aborts before the prune, and `quality-gates.sh` is
      green. Source:
      `/plans/active/issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md`
      (BACKEND P2 ×2 — combined here because both change the same prune path in the same file). That doc's third todo
      (positional task-ids) is NOT in scope — see this plan's Deferred section.
- [ ] [INFRA] P2. **Make `unified-trading-pm/scripts/dev/slot-git-status-report.sh` prefer `http://localhost:8765`**
      (trusted-local, no bearer token) when the loopback backend is reachable, falling back to the public `ORCH_URL` +
      `ORCH_TOKEN_FILE` when it is not, so an expired/rotated `~/.orch_token` can no longer silence a whole host's
      git-health view. Do NOT unconditionally flip the default `ORCH_URL` — off-VM operator laptops MUST keep the public
      URL + token path. **Done when**: after one reporter tick on the orchestrator host, `/api/fleet/git-health` reports
      `reporter_stale=false` for that host's slots and `git_staleness_alert_sent` stops firing; the off-VM branch is
      proved still to use the public URL + token by reading the code (not only by on-VM behaviour); and the script is
      wired into its primary consumer's `quality-gates.sh` if it was not already. **Two sources prescribe this identical
      fix in the identical direction and are folded into this one todo**:
      `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (INFRA P2) and
      `/plans/active/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (SCRIPT
      P2). Flip BOTH source docs' todos when this lands.
- [ ] [INFRA] P2. **Gate the git-health dirty signal on `dirty_consecutive_ticks >= 2` at BOTH decision sites** — the
      `not_clean_since` clear plus the sync-nudge in `agent-orchestrator/server/routes/git_health.py`, and the FF-pull
      skip decision in `unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh` — so a one-tick phantom-dirty reading can
      neither reset `not_clean_since` nor make the FF-pull cron skip. **Done when**: a unit test proves a single clean
      poll between two dirty polls does NOT reset `not_clean_since`, and a second check proves a one-tick phantom dirty
      does not produce an FF-pull skip; `quality-gates.sh` green. Source:
      `/plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md` (both remaining INFRA P2 todos
      — combined because they are one gate applied at two sites). Per that doc's own 2026-07-23 narrowing, do NOT
      re-hunt a reporter-internal race unless a post-`agent-orchestrator@529b0dc` recurrence is observed.
- [ ] [UI] P2. **Derive the Playwright dev-server port per slot instead of from a shared constant** in
      `deployment-ui/playwright.config.ts` and all three `webServer` blocks of
      `unified-trading-system-ui/playwright.config.ts`, keeping `reuseExistingServer: true`, and log the resolved port
      plus whether a server was reused or freshly spawned so a cross-slot attach is visible rather than silent. Derive
      the slot number from the checkout path and fall back to the existing fixed default when not in a slot clone; the
      slot-identity SSOT is `scripts/hooks/slot-identity-lib.sh`. **Done when**: two concurrent runs launched from two
      different slot clones with NO `PLAYWRIGHT_PORT` override each attach only to their own dev server, with the
      resolved port and reuse status printed in each run's output — cite `pw:L2 ✓` plus the specific spec file per
      `/codex/06-coding-standards/ui-testing-layers.md`. Source:
      `/plans/active/issues/playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md` (UI P2, Option A).
      This is a DIFFERENT file set from `agent-orchestrator/dashboard`'s own playwright config — do not touch that one.
- [ ] [BACKEND] P1. **Verify the sequential-gate fix + its DB migration on the live orchestrator VM.** Read-only. Record
      all three of the source doc's checks with the command and output for each: (a) does the deployed HEAD contain
      `agent-orchestrator@867b1731e` (`git merge-base --is-ancestor`), and which ref does `ao-self-pull.sh` track; (b)
      does the `sequential` column exist on the live `tasks` table; (c) do a non-sequential plan's tasks actually
      dispatch to different slots. **Measured 2026-07-26 before drafting, so state this in the finding**: `867b1731e` IS
      an ancestor of `origin/live-defi-rollout` (`compare` behind_by=0) but is NOT an ancestor of `origin/main`
      (diverged — main 31 ahead / 274 behind), so whether the deployed tree has it depends entirely on which ref the VM
      tracks. This is READ-ONLY — use the read-only SSM path (`/check-agent-orchestrator` or
      `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh`); do not restart the service or mutate
      runtime state. **Done when**: all three checks recorded with evidence in the source doc, and its `[BACKEND] P1`
      todo flipped or re-opened with the specific reason. Source:
      `/plans/active/issues/dispatch_sequential_gate_fix_2026_07_24.md` (BACKEND P1 — its stated "cannot be done until
      the pipeline promotes the commit" gate has now had two days to clear). That doc's `[DOCS] P1` codex-edit todo is
      NOT in scope — codex edits are never autonomous. **BLOCKED-CREDENTIALS (2026-07-26, slot 4)**: cannot execute any
      of the three checks. Both `check-ao-backlog-status.sh` and a hand-rolled `aws ssm send-command` against
      `i-0c9b283b31d6b5ca7` (`ap-northeast-1`) fail identically:
      `AccessDeniedException: User: arn:aws:iam::427895769566:user/ikenna-worker is not authorized to perform:     ssm:SendCommand on resource: arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7 because no     identity-based policy allows the ssm:SendCommand action`.
      Only one AWS profile (`default`) is configured in this environment, and `iam:ListAttachedUserPolicies` on this
      same user is also denied, so there is no self-service path to confirm or fix the policy from inside a worker
      session — this is a genuine operator-only IAM-grant action, not a slot-specific or retriable gap (every slot on
      this host shares the same AWS credentials, so `/skip-current-task` would not route around it). Remediation: grant
      `ssm:SendCommand`/`ssm:GetCommandInvocation` on that instance ARN to
      `arn:aws:iam::427895769566:user/ikenna-worker` (or run the check from a session/account that already has it), then
      re-dispatch this todo. Left unchecked pending operator action — see `/blocked` filed this session.
- [ ] [BACKEND] P3. **Prove `head_backward_canary.py` still fires on one legitimate single realign.** After the
      double-reset guard `agent-orchestrator@3e5de0e7b` landed, and record that the canary needed no modification. A
      test exercising the canary against the reflog signature of one allowed realign satisfies this — the source doc's
      done-when explicitly accepts "either a test or a live observation". **Done when**: the test (or cited live
      observation) exists and passes, the verdict is written into the source doc, and that doc reaches zero open todos
      so the finalize plan can archive it. Source: `/plans/active/issues/slot_double_reset_dataloss_race_2026_07_25.md`
      (BACKEND P3 — the sole residual; both halves of the fix are already verified shipped in that doc).
- [ ] [BACKEND] P3. **Audit every `/skip-current-task` `reason_code` for a silent, unpaged durable park.** Record per
      code whether it can reach a durable park and whether that park pages Slack, so the GATED-specific finding is
      either confirmed to generalise or scoped. Read the skip handler in `agent-orchestrator/server/routes/slots_ops.py`
      and `server/auto_park.py::maybe_auto_park` (plus `_ESCALATING_REASON_CODES`) rather than grepping a symbol.
      **AUDIT-ONLY — do not change `auto_park.py` in this todo**: if the audit finds an uncovered code, file it as a NEW
      tracked todo in the source doc instead, because `auto_park.py`'s other open item
      (`/plans/active/issues/auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md`) is an undecided
      operator-gated design question and must not be pre-empted. **Done when**: the source doc carries a
      per-`reason_code` table with the code-read evidence for each row. Source:
      `/plans/active/issues/gated_skip_park_no_slack_page_2026_07_25.md` (BACKEND P3).
- [ ] [REVIEW] P2. **Read-only: is each of the 7 rootm commit-sets' functionality on LDR today?** For every commit-set
      the rootm-branch doc named, record present-or-absent on `origin/live-defi-rollout`. The 7 `tab/rootm/*` branches
      it says are "LEFT IN PLACE" are **measurably GONE** (verified 2026-07-26 via the GitHub branches API across all
      six named repos: agent-orchestrator 167 / deployment-service 224 / market-tick-data-service 296 / strategy-service
      132 / unified-api-contracts 196 / unified-trading-library 156 branches, ZERO matching `rootm` in any of them), so
      the doc's premise is false and its prescribed per-branch review can no longer be executed as written. Check
      presence-of-functionality by symbol/file (e.g. does `WorkerLivenessWatchdog` exist; does the UCI messaging module
      exist), not by SHA — the SHAs are unrecoverable from the doc. **This todo must not push, cherry-pick, delete a
      branch, or otherwise mutate any repo** — it produces a per-item present/absent table only; anything recorded
      absent is a candidate work-loss for the operator to rule on, not something to recover unilaterally. **Done when**:
      the source doc carries a 7-row present/absent table with per-row evidence plus a dated note that the branches no
      longer exist. Source: `/plans/active/issues/orphan_rootm_branch_unmerged_work_2026_06_05.md`.
- [ ] [BACKEND] P3. **Leave a durable trace on any delete of a `status='done'` orchestrator `tasks` row.** So the
      unexplained done-row disappearances stop needing post-hoc forensics. A SQLite trigger is the mechanism the source
      doc proposes precisely because it fires regardless of call site (including out-of-band SQL); add it through the
      existing idempotent per-column/DDL migration pattern in `agent-orchestrator/server/bootstrap.py` so a fresh
      `state.db` self-heals. **The trace must not break the sanctioned operator delete** —
      `DELETE /api/backlog/{task_id}` legitimately removes a done row on operator request and must still succeed — so
      record rather than raise. **Done when**: a test proves a direct SQL delete of a done row leaves a queryable trace,
      a second proves the sanctioned operator-delete endpoint still succeeds and is traced not blocked, and
      `quality-gates.sh` is green. Source: `/plans/active/issues/ao_backlog_done_row_disappearance_2026_07_25.md`
      (BACKEND P3). Note for the worker:
      `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md` is an explicitly-parked decision
      that also names `bootstrap.py`/regen ids — do not touch task-id derivation here.
- [ ] [REVIEW] P3. **Redefine the ao tranche's membership rule from a hand-maintained Sources list to an epic-based
      rule, then triage the delta.** Added 2026-07-26, resolved `autonomous_session_operator_decisions_2026_07_25.md`
      entry #25 (option C — do both; A already done, this is the B follow-on). The hand-maintained Sources list lost
      `ao_open_issues_consolidated_close_out_2026_07_17.md` (9 open/32 done, real tracked work) for its first 24 hours
      of existence, undetected — a hand list is the wrong mechanism for a corpus this size. Measured:
      `parent_epic ∈ {orchestrator_master,     agent_operating_framework_master}` matches ~75 docs vs. the current
      ~35-doc Sources total. **Done when**: the ~40-doc delta is explicitly triaged (genuinely ao-tranche vs. mistagged
      epic vs. belongs elsewhere), the membership rule in `ao_consolidated_closeout_2026_07_25.md`'s own text is
      switched from "Sources list" to "epic query", and the Sources lists across all 5 Tracks are reconciled against the
      query's actual output.

## Deferred — conflict-gated (do NOT draft competing todos; re-check in batch 2)

- **The worker-liveness / watchdog kick+escalation cluster — a head-on directional contradiction.**
  `/plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` (INFRA P2) wants the
  watchdog to escalate soft-kick → hard-kill + respawn FASTER ("after N consecutive `post_kick_classification=frozen`
  observations (e.g. N=3, ~15-20 min) instead of soft-kicking indefinitely"), while
  `/plans/active/issues/host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md` (BACKEND P1, filed
  five days later) says the frozen classification is itself a FALSE POSITIVE under host load and must be softened
  ("require the ping/pane to be stale across TWO consecutive verify windows … Done when: a regression test … produces
  ZERO `worker_kicked` events"). Landing the first without the second escalates false kicks into false HARD-kills on
  genuinely-progressing workers. Four more docs claim the same mechanism from other angles:
  `/plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md`,
  `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` (its second todo also
  reorders the kill+resume-vs-`spawn_retry_cap` escalation),
  `/plans/active/issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` (INFRA P1, don't reap a
  CPU-progressing detached quickmerge), and
  `/plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`. **Escalated as an
  operator question** (see this run's report) — the ordering is a design call, not a mechanical merge.
- **Failover re-dispatch release-signal / liveness re-check** —
  `/plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (BACKEND P2). Bounded and
  well-evidenced (four incidents, one on a CODE task), but it turns on the same "is a silent worker actually dead"
  judgment as the cluster above, so it must be sequenced after that ordering is ruled.
- **`/done` acceptance semantics** — `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` (INFRA P1,
  gate `/done` on the code being on origin) and `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`
  (BACKEND P3, make `/done` idempotent + owner-checked) both change the same `/done` handler in
  `server/routes/slots_worker.py`. They are compatible in direction but must land as one change, and the on-origin gate
  interacts with the operator-merge-gate governance question in
  `/plans/active/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md` (P1, a held-behind-a-gate
  push must NOT be auto-shipped). Re-triage once that doc's gate-aware sweep decision exists.
- **AutoSpawn no-eligible-worker gap** —
  `/plans/active/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md` (BACKEND
  P2 + two P3 audits). FILE-COLLISION-gated only: it changes `server/autospawn.py`, which todo 1 of this plan may also
  touch. Straightforward batch-2 material once todo 1 lands.
- **Rejected-push recovery in `_ahead_push.py`** —
  `/plans/active/issues/ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md`. Its own doc calls
  this "the single riskiest automated code path in the system" and says the fix needs a real design decision; a
  characterisation test alone would land in `tests/test_watchdog_unpushed_sweep.py`, the same module the gate-aware
  sweep fix above will need. Held on both counts.
- **Periodic dirty-resolution sweep** — `/plans/active/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md`
  (BACKEND P2 ×2). Adding a NEW automatic caller of `commit_and_push_dirty_repos` (a realign path that has already
  destroyed work — see `slot_double_reset_dataloss_race_2026_07_25.md`) while the operator-merge-gate bypass above is
  unresolved is exactly the compounding this skill's non-batchable taxonomy warns about. Re-check after the gate-aware
  sweep decision.
- **Regen positional task-ids** —
  `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md` BACKEND P3 duplicates
  `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`, which
  `/plans/active/ao_issue_docs_consolidated_remediation_2026_07_23.md` records as a parked decision "deferred until a
  new incident forces it". A new incident arguably HAS occurred (the 2026-07-25
  `sync_backlog_to_db: REFUSING to reset task id` collisions), but whether that meets the deferral's own trigger is the
  operator's call. **BLOCKED-OPERATOR-DECISION.**
- **`slack-read-channel.py` env-var token fallback** —
  `/plans/active/issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md` SCRIPT P3. Its stated blocker has
  CLEARED (measured 2026-07-26: `check_no_empty_string_fallback.py --scope unified-trading-pm` reports
  `319 (== baseline)`, so the 320>319 ratchet breach that reverted the diff is resolved — that doc's own BACKEND P2
  ratchet todo is now done-in-substance and is a `/plan-reconcile` flip candidate, not batch material). But the fallback
  itself requires reading an environment variable, and `os.getenv()` is a workspace-wide banned pattern, while the
  script's stated design is "the token never touches disk or argv … resolved in-process via gcloud ADC". How to satisfy
  both is an unresolved compliance question, not a bounded outcome. **BLOCKED-OPERATOR-DECISION.**
- **QG-harness worktree-isolation defects** —
  `/plans/active/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` items 4 and 5. Item 5 (a `PROJECT_ROOT`
  override making the `.qg_last_passed_sha` sentinel record MAIN's HEAD instead of the worktree's) changes what "QG
  green" MEANS — the per-repo quality boundary itself. Too high blast-radius for a batch todo; needs its own scoped plan
  with operator sign-off.

## Deferred — operator decision needed (not batchable, no re-triage will clear it)

- `/plans/active/issues/escalation_backlog_repo_collision_blind_spot_2026_07_25.md` — its Todos heading literally reads
  "NOT for autonomous dispatch as-is"; the first todo is `[OPERATOR-DECISION]` on directionality (a)/(b)/(c) and the
  second is explicitly blocked on it.
- `/plans/active/issues/auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md` — a three-way fork whose option
  (c) is "explicitly rule this is not worth building".
- `/plans/active/issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md` — `[OPERATOR]` shape
  decision gating the `[SCRIPT]` implementation.
- `/plans/active/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md` — a section explicitly titled
  "Candidate fixes (not yet decided)", two legs of which are codex/CLAUDE.md edits (never autonomous).
- `/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md` — "Explicitly NOT actioned"
  per operator instruction; the one bounded leg (capture `claude_session_id` on `BlockedRow` at creation time) would
  start implementing a redesign the operator deferred.
- `/plans/active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md` — carries an explicit operator decision "not
  needed right now … Revive by scheduling these todos".
- `/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md` — all three open todos are operator-gated (two `[CREDS]`
  secret/IAM writes, one `[DESIGN]` dirty-worktree policy including an operator-sanctioned hard reset).
- `/plans/active/agent_orchestrator_alert_channel_cleanup_2026_07_13.md` and
  `/plans/active/ao_fleet_observability_kpis_2026_07_20.md` — both carry an explicit "NOT AO-dispatched /
  operator-driven" declaration in prose, not just the `assigned_vm: NA` default. Both of their remaining todos are now
  genuinely actionable (see this run's report) — extracting them needs the operator to lift that declaration.
- `/plans/active/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` `[OPERATOR]` P1
  (pin the JWT secret; needs a maintenance-window restart of the shared orchestrator) and
  `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` `[INFRA]` P3 (re-mint
  `~/.orch_token`) — credential operations. Their code-side siblings ARE in this batch as todo 3.
- `/plans/active/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md` and
  `/plans/active/issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` per-slot WIP recovery items
  — each needs foreign-worktree access plus a judgment call on whether specific commits are superseded.
- `/plans/active/issues/ao_backlog_done_row_disappearance_2026_07_25.md` `[OPERATOR]` P1 (watch-log check) and its
  `[BACKEND]` P2 (root-cause once a recurrence is caught) — the latter is time-gated on an unobserved recurrence.
- `/plans/active/ao_issue_docs_consolidated_remediation_2026_07_23.md` — both open items are `BLOCKED-OPERATOR-DECISION`
  / `BLOCKED-UPSTREAM-DESIGN` by their own labels.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`,
`/codex/06-coding-standards/ui-testing-layers.md` (todo 5), `/codex/04-architecture/autonomous-recovery-matrix.md`
(todos 1 and 10).

## Progress Log

- **2026-07-26** — Authored by `/ag-closeout-audit ao` (autonomous mode, operator away). Phase 0 resolved membership as
  the 35 Sources of `/plans/active/ao_consolidated_closeout_2026_07_25.md` and found the closeout carries zero todos and
  no `ao_*batch*` plan exists. Phase 1 read all 35 docs end to end (single-threaded — the run environment exposed no
  Workflow/Agent tool, so the skill's per-doc fan-out could not be used); 2 docs are archivable now, 1 is covered by
  `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md`, and 32 are orphaned. Phase 3 grepped every
  candidate target file (`server/db.py`, `regen_backlog_from_plan`, `slot-git-status-report`, `routes/git_health`,
  `slot-cron-ff-pull`, `playwright.config.ts`, `head_backward_canary`, `auto_park.py`, `server/bootstrap.py`,
  `test_watchdog_unpushed_sweep`, `_ahead_push`, `stale_dispatch`, `slots_worker.py`) across the whole `plans/active`
  corpus; two apparent collisions were refuted by reading the hits (the
  `ao_dashboard_backlog_detail_queue_lag_e2e_flaky` playwright mention is a stashed-diff reproduction note about a
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
