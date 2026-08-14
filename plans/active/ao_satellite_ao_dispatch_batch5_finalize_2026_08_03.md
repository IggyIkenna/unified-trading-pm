---
doc_type: plan
title: AO satellite AO batch 5 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch5_2026_08_03.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc(s)
  (the batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether any of
  the 29 declined-orphan docs' named gates have since cleared, archives the source docs that reach zero open todos, and
  runs the standard 6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-5, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch5_2026_08_03]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-08-03. Ships `status: active` (not draft)
  per the skill's 2026-07-30 finding: `gate_on_depends` already machine-holds every task until the batch's own todos are
  done, so a second draft-gate is a redundant, easy-to-forget manual flip — only the batch itself (genuinely unreviewed,
  judgment-laden content) needs `status: draft` + explicit operator approval.
---

# AO satellite AO batch 5 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify every batch-5 done-claim against reality, not against its checkbox** — for each of the
      10 todos in `/plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md`, re-run `git show --stat <sha>` for
      every cited commit and re-run the specific named test(s) directly rather than trusting the claim, and re-run each
      todo's own stated done-when check where it is a command (the diagnostic table completeness, the governor
      verification's evidence citation, the CLAUDE.md size-cap check, the pool-exhaustion-and-recovery test, the
      `check_no_empty_string_fallback.py` count, the reap-classification regression test). **Done when**: all 10
      verified, and any claim whose evidence does not hold up is re-opened as a new tracked todo in this doc's Progress
      Log with the discrepancy stated. **DONE 2026-08-14** — 9/10 fully verified (commit + content + named test/check
      all match the claim); todo 6 has real, correct shipped work but a broken evidence citation (placeholder SHA, no
      recorded operator sign-off) — see Progress Log below for the full per-todo breakdown and the new tracked follow-up
      todo it spawned.
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)** — batch
      5 was an extraction, so the source-doc items it covers are the ones that go stale, not the batch's. Flip the
      specific todo(s) in each of:
      `agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md` (its line-182 docs item),
      `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` (both remaining checkboxes),
      `ao_tranche_full_content_audit_findings_2026_07_31.md` (§3+§4 only),
      `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md` (the diagnostic half),
      `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md` (`[DEVOPS] P1`),
      `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md` (`[DOCS] P2` only),
      `one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md`,
      `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` (`[BACKEND] P2`),
      `plan_health_tests_leak_real_slack_alerts_2026_07_24.md` (`[SCRIPT] P3`), and
      `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` (item 1 only). **Done when**: every one of
      those flips is committed with the `docs(plans):` prefix and cites the real commit sha (or, for the read-only/
      verification-only items, the reproduction evidence).
- [ ] [INFRA] P0. **Re-check whether any of the 29 declined-orphan docs' NAMED gate has cleared since 2026-08-03, and
      spin any newly-conflict-clear items into batch 6** — walk the batch's own "Deferred — full per-doc disposition"
      section category by category: has any operator-gated design fork been ruled since? Has any credential/host-access
      gap closed? Has the worker-liveness/watchdog cluster's own sequencing advanced far enough to free up one of its
      claimed docs? Per this skill's iterative-drain methodology, re-check the SPECIFIC named gate on each, don't
      re-derive the classification from scratch. **Done when**: each of the 29 is marked cleared-and-moved (naming the
      new batch-6 plan/todo) or still-gated with the current reason — no entry left unstated.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** At minimum
      re-check all 10 source docs named in todo 2 above for whether their OTHER (non-batched) items are also closed —
      several (e.g. `orchestrator_db_pool_exhaustion_state_poll_stall`,
      `reaper_kills_inflight_detached_     quickmerge_false_done`) have additional open items NOT covered by this batch
      and must NOT be archived if so. Run the standard 6-step archival ritual (migrate any DEFERRED item → banner →
      codex-alignment check → fix every referrer's path corpus-wide → clear the lock) on any doc that IS fully done.
      **Done when**: `grep -rl <slug> plans/ codex/` returns only the archived copy's own path for each archived doc,
      and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero NEW hard failures (compare against the
      baseline recorded at this finalize plan's authoring time).
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md`, migrate any still-open Deferred item into batch 6
      (never leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_08/`,
      fix every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh` (or the currently-live inventory-regen entrypoint — verify the
      exact script name at execution time, since it has been renamed/relocated at least once in this tranche's history).
      **Done when**: the batch plan is archived with a banner, the inventory regenerates with an orphan count of 0, and
      `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-08-03** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode, scheduled
  dispatch). `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile → re-check
  gates → archive sources → archive self) and several touch the same files. Ships `status: active` per the skill's
  2026-07-30 finding (`gate_on_depends` already holds every task; no separate draft-gate needed).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added
  `agent-orchestrator-single-vm-architecture.md` (§ Dispatch-scope eligibility), already cited in this doc's own Codex
  SSOTs section above but missing from context_scope; needed for todo 3's re-check of the 29 declined-orphan docs'
  gates.
- **2026-08-14 (review, slot 6) — todo 1 re-verification, all 10 batch-5 done-claims checked against reality:**
  - **Todo 1** (`agents/review.md` STEP 2 mirror) — VERIFIED. `git show --stat unified-trading-pm@6c4e57b8a` real, lands
    exactly the claimed diff; `agents/review.md` lines 279-281 contain the cross-role-routing text described.
  - **Todo 2** (`ao_db_lock_storm_and_stuck_shutdown_outage` bookkeeping) — VERIFIED. No sha cited in the batch plan's
    text ("this commit") but resolves to real commit `c3d0894262`; doc's `status: open` correctly retained (not
    prematurely archived), both `related:` additions present.
  - **Todo 3** (`ao_tranche_full_content_audit_findings` §3+§4) — VERIFIED. Resolves to real commit `096926cc5a`;
    `superseded_by: [ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26]` confirmed present in the actual target
    doc's frontmatter (`plans/archive/issues/backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md:30`); the
    corrected MOVED-item summary sentence ("all 29 MOVED items here are closed (fixed 2026-08-08)") is live in
    `ao_open_issues_consolidated_close_out_2026_07_17.md:141`, which measures 985 lines (under the 1000-line hard cap).
  - **Todo 4** (5-agent-id diagnostic table) — VERIFIED. Resolves to real commit `c936992781`; all 5 named ids
    (`agt-79063c`, `agt-0cd704`, `agt-765e33`, `agt-8fa8d1`, `agt-8e95ca`) have a complete table row each in
    `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`.
  - **Todo 5** (host-saturation governor verification) — VERIFIED. `[DEVOPS] P1` checkbox is `[x]` in the archived
    source doc, citing `qg_governor_acquire`'s real flock-based token semaphore as evidence (lines 149-151).
  - **Todo 6** (per-tab-worktrees.md + CLAUDE.md multi-operator-slot-sharing fold-in) — **CONTENT VERIFIED, CITATION
    BROKEN.** Both target docs genuinely contain the claimed content (`per-tab-worktrees.md:288`,
    `cursor-configs/CLAUDE.md:149`) and `check_agent_rules_size_cap.py` passes (40,927/40,960 B). The real shipping
    commit is findable via `git log -S "sharing ONE slot"` → `unified-trading-pm@a33e3306d3` (2026-08-09, slot-8). BUT:
    (a) the batch-5 plan's own todo 6 entry cites no SHA at all, and (b) the source doc's Progress Log cites a literal
    placeholder, `unified-trading-pm@<sha, see commit>`, not a real hash. Neither the commit message nor either doc's
    Progress Log records the operator sign-off this plan's own "Rules for every worker" section required before
    committing a codex/CLAUDE.md edit — see the new follow-up todo below.
  - **Todo 7** (`self_declared_complete` reap threading) — VERIFIED. `git show --stat agent-orchestrator@687cad2d00`
    matches the claimed diff exactly (3 files, the two named tests included); re-ran both named tests directly —
    `test_self_declared_complete_queued_work_reaped_not_respawned` and
    `test_queued_work_escalating_not_self_declared_takes_respawn_path` — 2 passed.
  - **Todo 8** (DB pool-exhaustion-and-recovery test) — VERIFIED. `git show --stat agent-orchestrator@54b86a9` matches;
    re-ran `tests/test_db_pool_exhaustion_recovery.py` directly — 1 passed (bounded to the named test file, not a full
    2779-test re-run, per this todo's own "re-run the specific named test(s)" scope).
  - **Todo 9** (`slack-read-channel.py` env-var fallback) — VERIFIED. `git show --stat unified-trading-pm@2db15bb21`
    matches; re-ran `scripts/quality_gates/check_no_empty_string_fallback.py --scope unified-trading-pm` directly —
    `[OK] unified-trading-pm: 319 (== baseline)`, matching the claimed "<= 319" exactly.
  - **Todo 10** (orphan-reap CPU-progressing discriminator) — VERIFIED. `git show --stat agent-orchestrator@f91b4d0`
    matches; re-ran `tests/test_orphan_process_reap.py` directly — 27 passed (includes the two new discriminator
    regression tests named in the commit).
  - **New tracked follow-up todo** (the one discrepancy this pass found — citation/sign-off gap, not a functional
    defect):
    - [ ] [DOCS] P2. Fix the broken evidence citations for batch-5 todo 6 (the `per-tab-worktrees.md`/`CLAUDE.md`
          multi-operator-slot-sharing fold-in) — replace the source doc's placeholder
          `unified-trading-pm@<sha, see commit>` (in
          `/plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`'s
          2026-08-09 Progress Log entry) and the batch-5 plan's own uncited todo 6 with the real shipping commit,
          `unified-trading-pm@a33e3306d3`. In the same edit, confirm whether operator sign-off was actually obtained
          before that commit (per the batch-5 plan's "Rules for every worker" § requiring sign-off on any codex/
          CLAUDE.md edit) — ask the operator if no record exists — and record the answer in the source doc's Progress
          Log. **Done when**: both citations read the real SHA, and the sign-off question has an explicit recorded
          answer (confirmed-obtained-at-the-time, or retroactively obtained now). This is folded into this finalize
          plan's own todo 2 (source-doc reconciliation) rather than spun out separately, since todo 2 already touches
          this exact source doc's `[DOCS] P2` item.
