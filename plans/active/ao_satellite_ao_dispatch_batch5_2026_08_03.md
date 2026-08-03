---
doc_type: plan
title: AO satellite AO batch 5 — fifth dispatch batch extracted from the AO tranche's satellite docs
summary: >-
  FIFTH AO-dispatch batch for the `ao` topic tranche, produced by the `/ag-closeout-audit ao` skill run (2026-08-03,
  autonomous mode, scheduled dispatch, real `Workflow` fan-out over all 41 currently mechanically-flagged never-cited
  candidates — up from 41/42 at prior runs since new docs were created 2026-08-01..08-03). Of the 41: 1 is
  `archivable_now` (pure bookkeeping), 1 is `archivable_after_planned_work` (already covered by
  `ao_open_issues_consolidated_close_out_2026_07_17.md`'s own open Phase-5 todo, not batch material), 29 are
  `orphaned_never_touched`/`orphaned_partial_coverage` but NOT AO-eligible (operator-gated design forks,
  credential/host-access gaps, unscoped design questions, or already-claimed-by-a-live-cluster's-own-sequencing), and 10
  are genuinely orphaned AND AO-eligible bounded work — this batch extracts those 10, each conflict-checked against the
  whole `plans/active` corpus before drafting (2 same-file adjacencies found and handled via a sequencing rule rather
  than exclusion, matching batch3/batch4's own precedent).
status: draft
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-5, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md,
    /plans/active/ao_satellite_ao_dispatch_batch4_2026_08_01.md,
    /plans/active/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md,
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 1.4
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
source: >-
  /ag-closeout-audit ao skill run 2026-08-03 (autonomous, scheduled ag_closeout_auditor dispatch, slot 2) — Phase 0
  re-derived the tranche's covering-plan set (unchanged from batch2/3/4's own runs: batch1+finalize (archived),
  batch2+finalize, batch3+finalize, batch4+finalize, `ao_open_issues_consolidated_close_out_2026_07_17.md`); Phase 1 ran
  a real `Workflow` fan-out (41 agents, one per `generate_ag_closeout_audit_candidates.py --tranche ao`-flagged
  never-cited candidate, all 41 succeeded); Phase 3 ran the conflict-check grep against the whole `plans/active` corpus
  for every AO-eligible candidate's target file(s) before drafting.
---

# AO satellite AO batch 5

> **`status: draft` — NOT ingested, NOT dispatched.** Flipping this to `active` is the operator's call
> (`/plans/PLAN_FORMAT.md`; CLAUDE.md § "Plan destination — ASK BEFORE CREATING"). Authored autonomously (scheduled
> dispatch); deliberately stops at draft per the skill's Autonomous-mode contract.

## Why this plan exists

A fresh `/ag-closeout-audit ao` run (2026-08-03) re-derived the tranche's 41 current
`generate_ag_closeout_audit_candidates.py`-flagged never-cited members and ran a real per-doc `Workflow` fan-out over
all of them (a first — prior single-doc-agent runs existed, but this is the first run where every one of the 41 got an
independent fresh read in the same pass). Verdict counts: 1 `archivable_now`, 1 `archivable_after_planned_work`, 10
`orphaned_partial_coverage`, 29 `orphaned_never_touched`. Of the 39 genuinely-orphaned docs, only 10 clear the
AO-dispatch-scope eligibility bar (bounded, worker-determinable-alone outcome, no operator ruling / credential gap /
calendar gate / open design fork) — this batch extracts those 10. The remaining 29 stay exactly where they are:
operator-gated design forks (the largest class — several explicitly self-labelled `[OPERATOR]` or "not yet decided, for
operator review"), credential/host-access gaps, unscoped design questions that need a `/plan-brainstorm` pass first, or
work already claimed/sequenced by the still-active worker-liveness/watchdog cluster the operator ruled on 2026-07-29.
Full per-doc reasoning for all 41 (including the 29 declined) lives in this run's own Workflow journal, cited in the
Progress Log below rather than duplicated here.

## Rules for every worker on this plan

- **Put each todo's new test cases in a test module named for that todo's own concern** — never add to a test module
  another todo on this plan also touches. The todos below are file-disjoint EXCEPT the two explicit same-file pairs
  called out below.
- **File-adjacency #1 (hard sequencing, same file)**: todo 2 (archive `ao_db_lock_storm_and_stuck_shutdown_outage`) and
  todo 3 (`ao_tranche_full_content_audit_findings` bookkeeping) BOTH edit
  `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md` — todo 2 corrects one stale "MISTAGGED" table row,
  todo 3 corrects a different MOVED-item summary sentence + table cell. **Land todo 2 before todo 3** (re-pull fresh
  immediately before todo 3's edit and re-check for a merge conflict on that file — it is actively co-edited by
  na-eligibility-audit/context-scout passes on an almost-daily cadence and currently sits at 902/1000 lines, so also
  re-verify the line-cap headroom before adding any new text there).
- **File-adjacency #2 (soft caution, not a hard collision)**: todo 7 (`self_declared_complete` wiring in
  `agent-orchestrator/server/worker_liveness/_respawn.py`) shares that file with
  `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`'s own still-open
  `[BACKEND] P2` todo (a different facet — `spawn_retry_cap`-vs-escalation ordering, itself gated on "a live trace or
  direct test" per that doc's 2026-08-01 Progress Log, not currently AO-dispatched). No batch-internal collision today,
  but whoever picks up todo 7 should re-grep that file for a fresh diff before starting in case that sibling doc's item
  has since landed.
- **File-adjacency #3 (soft caution, not a hard collision)**: todo 10 (`agent-orchestrator/server/orphan_reap.py`)
  shares that file with `/plans/active/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`'s
  own still-open `[SCRIPT] P3` "optional, defense-in-depth" todo (a different facet — parent-shell identity vs.
  descendant CPU-progress — and that doc is `assigned_vm: NA`, not concurrently AO-dispatched today). Same
  re-grep-before-starting caution as above.
- **Todo 6 touches a codex SSOT (`per-tab-worktrees.md`) and the QG-size-capped `cursor-configs/CLAUDE.md`** — obtain
  operator sign-off before committing either edit, per the workspace HARD RULE that a codex/CLAUDE.md change needs
  sign-off (same convention batch2's `[DOCS] P1` codex-edit todo used). `cursor-configs/CLAUDE.md` measured 40,942 B
  against the 40,960 B hard cap at drafting time (18 B headroom) — any net-positive addition needs an offsetting
  condensation in the same edit; extend the existing SSOT-pointer parenthetical rather than adding a new sentence.
- Do not edit a source issue doc's checkboxes beyond appending your evidence line to the todo you executed. The paired
  finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md`) reconciles evidence back into
  every source doc and runs archival.
- No todo below deletes prod data, mutates a GCS bucket, or launches a VM.

## Todos

- [ ] [DOCS] P2. **Mirror the already-shipped peer-vs-operator reply-routing branch from `agents/main.md` STEP 2B into
      `agents/review.md` STEP 2** (currently the old unconditional "for each message... POST your reply" pattern with no
      `in_reply_to`/`from_role` branching — the source doc's own cited line numbers have drifted, content-search for the
      phrase instead). Document that `/reply` with `in_reply_to` set is the preferred path for answering ANY drained
      message regardless of `from_role` (operator or review's own role → own-thread ack as before; a genuine peer role →
      `/reply` auto-cross-routes to that peer's thread + tmux nudge, backend behavior already live since
      `agent-orchestrator@738b2d3`), and that `POST /api/agents/by-role/<role>/message` remains reserved for brand-new
      outbound-only pings (no `in_reply_to`, never acks, redelivers until the ~30-cap). Docs-only change; does not touch
      `server/routes/agents.py`. **Done when**: `agents/review.md` STEP 2's text and curl example describe the same
      cross-role auto-routing `agents/main.md` STEP 2B already describes (verified by a side-by-side diff of the two
      sections, adapted only for review's own STEP numbering/message-flow context); the target issue doc's line-182 todo
      is flipped `[x]` with the shipping commit sha cited in the same turn. Source:
      `/plans/active/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md` (its
      4th, docs-only item — its P1 backend-routing-code item and P3 operator-sign-off item are explicitly self-gated in
      the source doc and NOT in scope here). Repo: unified-trading-pm.

- [ ] [REVIEW] P2. **Close out `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` — pure bookkeeping, no new
      investigation.** Flip its remaining `[OPERATOR] P2` (line ~225) and `[REVIEW] P2` (line ~232) checkboxes to
      `- [x] ✅`, citing `agent-orchestrator@90a2b2f` and
      `/plans/archive/issues/orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md` as the
      doc that actually performed + verified the live systemd-unit fix (3-way verification already on record: unit
      mtime, `/proc/<pid>/cmdline` no `--reload`, clean `ActiveState`, plus the durable `ao-self-pull.sh` self-heal
      verified live twice). Add that archived doc, plus
      `/plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md` (the follow-up this doc's own
      Progress Log says it filed but never linked), to this doc's `related:`. Set `status: resolved` + `resolved_by`,
      then run the standard 6-step archival ritual (`git mv` to `plans/archive/issues/`, fix every corpus referrer —
      **including the stale "MISTAGGED" table row at
      `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md`** which should move this doc out of that
      bucket now that it's closed, not just retagged — see the file-adjacency rule above, land this BEFORE todo 3).
      **Done when**: the doc reads `status: resolved`, both checkboxes `[x]` with the citations above, lives at
      `plans/archive/issues/`, and `grep -rl ao_db_lock_storm_and_stuck_shutdown_outage plans/ codex/` returns only the
      archived path. Source: `/plans/active/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`. Repo:
      unified-trading-pm.

- [ ] [DOCS] P3. **Close `ao_tranche_full_content_audit_findings_2026_07_31.md`'s §3 (duplicate-doc merge) and §4 (stale
      MOVED-item bookkeeping) — the two eligible slices only; §1/§2 stay NA/operator-gated as the doc already has
      them.** (a) Duplicate-doc formal closure: na-eligibility-audit already concluded (2026-07-31, re-affirmed
      2026-08-02) that `backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md` is a duplicate of
      `ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`. Flip the 07-30 doc's frontmatter to
      `status: resolved` + `superseded_by: ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26`, fold its two
      extra root-cause candidates (seed-timestamp-ordering in `bootstrap.initialise()`; a possibly-inverted frontend
      sort comparator) into the 07-26 survivor's "What was found" section, then archive the 07-30 doc per the standard
      ritual. (b) Tracker MOVED-item bookkeeping: in `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md`
      (land AFTER todo 2 above — same-file rule), re-verify every `➡️ MOVED 2026-07-20 to <child>` bullet tied to
      `ao_scheduled_agent_hygiene_2026_07_20.md` / `ao_fleet_infra_hardening_2026_07_20.md` /
      `ao_fleet_observability_kpis_2026_07_20.md` (all 3 children archived) is flipped `[x]` with a DONE citation, then
      correct the stale MOVED-item count sentence and the `ao_fleet_infra_hardening_2026_07_20.md` status-table cell to
      match the freshly re-counted true state. **Done when**: both duplicate docs have internally-consistent frontmatter
      (07-30 `resolved`+`superseded_by`, archived); the tracker's MOVED-item summary + status-table cell reflect the
      freshly-verified count with no stale figures; this doc's own §3/§4 todos flip `[x]` with commit-sha citations;
      §1/§2 explicitly left open/NA in the same edit. Source:
      `/plans/active/issues/ao_tranche_full_content_audit_findings_2026_07_31.md` (§3+§4 only). Repo:
      unified-trading-pm.

- [ ] [DATA] P2. **Read-only diagnostic on the orchestrator VM's own `data/state/state.db` + `activity_log` (no external
      credential needed — same host every dispatched worker already runs on).** For each of the 5 escalation/agent_ids
      `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`'s Progress Log names (`agt-79063c`, `agt-0cd704`,
      `agt-765e33`, `agt-8fa8d1`, `agt-8e95ca`), determine (a) whether an `AgentRow` with that `agent_id` exists now or
      ever existed (cross-check `escalation_dispatched`/`plan_health_dispatch` `activity_log` rows for that id if the
      `AgentRow` itself is gone/archived), (b) if found, its current `status`/`tmux_session`, and (c) if it existed then
      transitioned away from active/stale before its worker's `/done` call, the `activity_log` event that did it. **Do
      NOT attempt the code fix** (that doc's Todo 2) in this same todo — it is two-hypothesis-contingent on this
      diagnostic's result, a separate gated follow-up. **Done when**: a new dated Progress Log entry on the source doc
      records the table above for all 5 ids that are still within retention; a fully-attempted-but-inconclusive result
      (e.g. all 5 rows already pruned) is an acceptable, explicitly-recorded outcome. Source:
      `/plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md` (diagnostic half of its
      remaining scope only). Repo: agent-orchestrator (read-only).

- [ ] [BACKEND] P2. **Verify whether the shipped `qg_host_adaptive_resource_governor_2026_07_14.md` reservation-ledger
      admission governor satisfies `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`'s own
      still-open `[DEVOPS] P1` done-when** — a real host-level semaphore gating full-suite QG launches on the shared
      orchestrator host so they queue instead of pinning the host at saturation. Check specifically against the
      2026-07-26 incident's own facts (the saturating QG was the features-service full-suite QG, a `base-service.sh`
      -sourcing repo the governor's admission hook covers) and against the 2026-08-02 finding that the governor's
      ledger-sharing only covers the slot-worktree topology, not the separate GHA-glue-runner cross-repo gap (forked
      into `qg_governor_glue_runner_ledger_coordination_2026_08_03.md`). **Done when**: either (a) the `[DEVOPS] P1`
      checkbox flips `[x]` citing the governor's shipped commit(s)/tests as evidence, with an archival check to follow,
      or (b) it stays open with a NEW dated Progress Log entry naming the SPECIFIC uncovered gap with evidence — not a
      4th silent re-confirmation of "genuinely open." Source:
      `/plans/active/issues/host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md` (`[DEVOPS] P1`
      only). Repo: agent-orchestrator (verification, read-only + a possible checkbox flip).

- [ ] [DOCS] P2. [OPERATOR] **Fold the 2026-08-01 multi-agent slot-collision incident into two governance docs, scoped
      to DESCRIPTIVE content only — do not attempt to resolve or pre-empt the still-open `[OPERATOR] P1` decision in the
      source doc.** In `/codex/05-infrastructure/per-tab-worktrees.md`'s "Troubleshooting" section, add a subsection
      naming this as a DISTINCT failure mode from AO-worker-to-AO-worker slot collision: multiple concurrent `claude`
      processes/operators sharing ONE slot's single git checkout (observed: up to 6 concurrent processes on `.tabs/1`,
      repeated `.git/index.lock` contention, autostash-pop re-fights, wrong commit author attribution since
      `.git/config`'s `user.name`/`user.email` is shared state) — cite the interim mitigation available today
      (`scripts/dev/safe-doc-push.sh` for doc-only batches) and point to the source issue doc for full analysis + the
      still-open operator decision + candidate root-cause fixes. In `cursor-configs/CLAUDE.md`'s "Multi-agent safety
      (per-slot worktrees)" section, make ONLY a byte-minimal pointer edit — extend the existing trailing parenthetical
      ("`Troubleshooting`: stale sibling `.venv`s → `uv sync`") to also name "multi-operator slot-sharing" — and verify
      `scripts/quality_gates/check_agent_rules_size_cap.py` still exits 0 afterward (measured 40,942/40,960 B, 18 B
      headroom at drafting time; if no safe condensation is found, skip the CLAUDE.md edit entirely and note the gap in
      the source doc's Progress Log rather than breach the cap). **Obtain operator sign-off before committing either
      edit** (see this plan's "Rules for every worker" section). **Done when**: both target docs contain new content
      naming this failure mode (grep for "sharing one slot"/"multi-operator" hits each); `check_agent_rules_size_cap.py`
      still passes; the source issue doc's `[DOCS] P2` todo flips `[x]` with the commit sha. Source:
      `/plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md` (its
      `[DOCS]     P2` item only — items 2-4, the operator-decision cluster, are NOT in scope). Repo: unified-trading-pm.

- [ ] [BACKEND] P3. **Thread the already-shipped `self_declared_complete` kick-classification signal
      (`agent-orchestrator/server/worker_liveness/__init__.py`, computed ~line 717 via `_SELF_DECLARED_COMPLETE_RE`,
      currently only logged to the activity event ~line 814) through to `_maybe_auto_respawn_stuck_slot` /
      `_respawn.py::maybe_auto_respawn_stuck_slot`** (currently called at `__init__.py:836` with no knowledge of this
      signal), and treat a `self_declared_complete=True` + `current_task is None` escalating slot as reap-eligible
      (route to the existing clean `_reap_idle_session` path) instead of falling through to the destructive
      WIP-resolve→kill→fresh-spawn flow whenever `queued_undispatched > 0` — closing the residual gap: today
      `_idle_reap_eligible = slot_current_task is None and queued_undispatched == 0` never consults
      `self_declared_complete`, so a correctly-idle already-complete one-shot slot gets force-killed and cold-rebooted
      the instant ANY other task is queued system-wide, once it crosses `kick_escalation_threshold`. **See this plan's
      file-adjacency rule #2 before starting** (re-grep `_respawn.py` for a fresh diff first). **Done when**: a new
      regression test in `agent-orchestrator/tests/test_worker_liveness.py` simulates an escalating slot (`force=True`)
      with `current_task=None`, `queued_undispatched > 0`, and the slot's most recent kick flagged
      `self_declared_complete=True`, and asserts the clean `_reap_idle_session` path is invoked (NOT the destructive
      flow) — plus the full existing `worker_liveness`/`_respawn` test suite still passes and `quality-gates.sh` is
      green before shipping. Source:
      `/plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md` (its
      residual-risk finding). Repo: agent-orchestrator.

- [ ] [BACKEND] P2. **Close the connection-release-proof gap on
      `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md`'s still-open "Determine root cause: connection
      LEAK vs. concurrency-over-pool" todo** (the leak-vs-concurrency conclusion is already recorded via the doc's own
      occurrence #6/#7 log and a 2026-07-30 na-eligibility-audit entry — only the formal proof + test remain): (1)
      confirm every hot-path DB session usage — `server/routes/state.py::get_state` → `server/state_store/slots.py`,
      `server/routes/agents.py::agent_poll`, `server/routes/git_health.py::post_slot_git_status`/`get_slot_git_status` —
      routes through `session_scope()`/`read_only_session_scope()` (both already release via `finally: session.close()`,
      `server/db.py:117-152`) rather than a raw session-factory call that could skip cleanup on an error branch; (2) add
      a new pool-exhaustion-and-recovery test, mirroring the threading-harness style
      `tests/test_db_read_only_session.py` already uses (and already cites this exact issue doc), that opens
      `pool_size + max_overflow` concurrent sessions via `get_session_factory()` and holds them past `pool_timeout`,
      asserts the next concurrent request raises the expected pool-exhaustion `TimeoutError`, then releases the held
      sessions and asserts a fresh request succeeds promptly. **Done when**: `quality-gates.sh` green in
      agent-orchestrator; the new test module (`tests/test_db_pool_exhaustion_recovery.py`) demonstrates both the
      exhaustion and the recovery; each of the 4 named hot-path handlers is confirmed (recorded in the test module's
      docstring or a code comment) to route through the release-safe helpers; the source doc's `[BACKEND] P2` todo flips
      `[x]` citing the new test module + commit sha. Source:
      `/plans/active/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` (`[BACKEND] P2` only — its
      codex-governance-matrix item and its unscoped write-batching item are NOT in scope, see this run's Workflow
      journal for why). Repo: agent-orchestrator.

- [ ] [SCRIPT] P3. **Close out the stale `[SCRIPT] P3` todo on `plan_health_tests_leak_real_slack_alerts_2026_07_24.md`
      via VERIFICATION, not re-implementation.** Confirm `scripts/dev/slack-read-channel.py`'s
      `SLACK_ALERTS_READER_BOT_TOKEN` env-var fallback — already shipped `unified-trading-pm@2db15bb` (2026-07-28), 2
      days BEFORE the na-eligibility-audit's 2026-07-30 "direction superseded" annotation — satisfies the todo's own
      original Gate ("documented as secondary, never touches disk/argv") and remains excluded from the
      `no_empty_string_fallback_baseline.yaml` count (re-run
      `check_no_empty_string_fallback.py --scope     unified-trading-pm`; confirm still `<= 319` thanks to its
      `# noqa: qg-empty-fallback` marker). **Done NOT propose** the batch1-ruled "grant
      `secretmanager.versions.access` + remove the fallback" task itself — deciding whether that's still worth doing
      given the shipped fallback already meets its own gate is a live design tradeoff, not a bounded fact. **Do NOT
      grant any IAM roles and do NOT edit `slack-read-channel.py`'s code.** **Done when**: the `[SCRIPT] P3` checkbox
      reads `[x]`, cites `unified-trading-pm@2db15bb` as the commit that met its Gate, cites a fresh
      `check_no_empty_string_fallback.py` count (`<= 319`), and a new dated Progress Log entry records the correction
      (the prior "reverted, retry later" claim was stale by 2 days). Source:
      `/plans/active/issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md` (`[SCRIPT] P3` only). Repo:
      unified-trading-pm (verification only, no code edit).

- [ ] [INFRA] P1. **In `agent-orchestrator/server/orphan_reap.py`'s reap-classification path, before treating a
      heartbeat-silent pane's detached quickmerge subprocess tree as reapable, walk its descendant process tree and
      check for a currently-CPU-progressing child** (e.g. a pytest/basedpyright/ruff/QG subprocess with recent measured
      CPU%, not just process existence) — a pane waiting on a live, CPU-progressing detached quickmerge must NOT be
      classified as frozen/reaped. **See this plan's file-adjacency rule #3 before starting** (re-grep `orphan_reap.py`
      for a fresh diff first — a sibling NA doc has an unrelated, different-facet open todo on the same file). **Done
      when**: a new regression test (mirroring the existing `_pane_is_dead`-style discriminator tests in
      `tests/test_worker_liveness_watchdog.py`) proves a detached quickmerge whose QG subprocess is measurably
      CPU-progressing survives a reap sweep on a heartbeat-silent pane, while a genuinely dead/idle detached tree is
      still reaped (no regression); full `agent-orchestrator` `quality-gates.sh` green. Source:
      `/plans/active/issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` (item 1, the
      reaper-overeagerness fix only — its other 2 items stay held/deferred per that doc's own state). Repo:
      agent-orchestrator.

## Deferred — full per-doc disposition of the 29 declined orphaned candidates

The 29 orphaned-but-not-AO-eligible docs from this run's Phase 1 fan-out are NOT individually re-listed here (their full
reasoning is in this run's Workflow journal, cited in the Progress Log below) — every one falls into one of these
non-batchable categories per the skill's own taxonomy: **operator-gated** (an explicit `[OPERATOR]` tag or "not yet
decided, for operator review" framing — the largest class, e.g.
`ao_backlog_no_collision_gate_long_running_driver_todos_2026_08_02.md`,
`ao_boot_stub_session_vars_field_name_mismatch_2026_08_02.md`,
`ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`, `blocked_questions_ux_redesign_context_loss_and_scale`,
`long_lived_vm_logs_not_backed_up`, `orchestrator_vm_e2e_hardening_2026_07_24.md`); **too-large/unscoped-design** (needs
a `/plan-brainstorm` pass before it's dispatch-ready, e.g. `ahead_push_sentinel_stale_after_amend`,
`utl_shared_clone_commits_repeatedly_reset`'s items 4/5, `regen_positional_task_ids_not_content_stable` per its own
already-ruled full-scope mandate sitting at its source doc); **already claimed by the still-executing
worker-liveness/watchdog cluster's own 2026-07-29 operator sequencing** (`killed_slot_orphans_committed_unpushed_work`,
`wedge_detector_lacks_liveness_by_progress_false_positive`, `slot_recurring_wedge_at_context_pct_75`); **credential/
host-access gaps beyond a standard dev checkout** (`nohup_detached_background_process_killed_by_orphan_reap`'s optional
leg, `git_health_not_clean_since_pinned_constant`); and a handful of newly-created (2026-08-01..08-03) docs
(`ao_non_dispatchable_regex_swallows_resolved_retags`, `cicd_escalation_agentrow_archived_prematurely_mid_session`,
`dp_escalation_worker_dispatch_no_open_issue_check`, `mtds_plan_flip_fabricated_commit_sha_evidence`,
`multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout`'s items 2-4,
`orchestrator_host_memory_exhaustion_4th_recurrence`, `qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge`,
`review_role_boot_read_unconfirmed_stuck_loop`'s own still-open cross-role-file item,
`tradfi_finding_e1_unsourced_operator_ruling_citation`, `worker_session_teardown_kills_long_running_pipeline_check`)
each independently gated on a design fork or operator decision per their own text. None are re-triageable by re-running
this same mechanical filter again without new information — the next `/ag-closeout-audit ao` pass should re-check each
one's _specific named gate_ (per the skill's iterative-drain methodology step 1), not re-derive the classification from
scratch.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`,
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (todos 2, 3).

## Progress Log

- **2026-08-03** — Authored by `/ag-closeout-audit ao` (autonomous mode, scheduled `ag_closeout_auditor` dispatch, slot
  2). Phase 0 confirmed the covering-plan set is unchanged from batch4's run (batch1+finalize archived, batch2+finalize,
  batch3+finalize, batch4+finalize, `ao_open_issues_consolidated_close_out_2026_07_17.md`). Phase 1 ran a real
  `Workflow` fan-out (41 agents, one per `generate_ag_closeout_audit_candidates.py`-flagged never-cited candidate — all
  41 succeeded, 0 errors): 1 `archivable_now`, 1 `archivable_after_planned_work`, 10 `orphaned_partial_coverage`, 29
  `orphaned_never_touched`. Of the 39 orphaned, 10 cleared AO-dispatch-scope eligibility. Phase 3's conflict-check ran
  against the whole `plans/active` corpus for every eligible candidate's target file(s); found 2 same-file adjacencies
  (`ao_open_issues_consolidated_close_out_2026_07_17.md` touched by both todo 2 and todo 3;
  `worker_liveness/_respawn.py` and `orphan_reap.py` each shared with an unrelated, NA, different-facet sibling todo) —
  handled via sequencing/caution rules per batch3/batch4's own precedent rather than exclusion. Left `status: draft`
  deliberately — flipping to `active` is the operator's call. Full per-doc Phase 1 verdicts + reasoning for all 41
  candidates (including the 29 declined): Workflow run `wf_d2e30c15-0f6`, journal at
  `subagents/workflows/wf_d2e30c15-0f6/journal.jsonl` (agent-orchestrator dispatch host).
