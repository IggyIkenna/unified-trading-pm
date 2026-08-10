---
doc_type: plan
title: AO satellite AO batch 5 — fifth dispatch batch extracted from the AO tranche's satellite docs
summary: >-
  FIFTH AO-dispatch batch for the `ao` topic tranche, produced by the `/ag-closeout-audit ao` skill run (2026-08-03,
  autonomous mode, scheduled dispatch, real `Workflow` fan-out over all 41 currently mechanically-flagged never-cited
  candidates — up from 41/42 at prior runs since new docs were created 2026-08-01..08-03). Of the 41: 1 is
  `archivable_now` (pure bookkeeping), 1 is `archivable_after_planned_work` (already covered by
  `ao_open_issues_consolidated_close_out_2026_07_17.md`'s own open Phase-5 todo, not batch material), 39 are
  `orphaned_never_touched`/`orphaned_partial_coverage`, of which 30 are NOT AO-eligible (operator-gated design forks,
  credential/host-access gaps, unscoped design questions, or already-claimed-by-a-live-cluster's-own-sequencing) and 9
  ARE AO-eligible bounded work — this batch extracts those 9 plus the 1 `archivable_now` bookkeeping item (10 todos
  total), each conflict-checked against the whole `plans/active` corpus before drafting (2 same-file adjacencies found
  and handled via a sequencing rule rather than exclusion, matching batch3/batch4's own precedent).
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-5, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md,
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
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

> **`status: active`** — approved 2026-08-08 after a fresh conflict-check found no blocking overlap (see Progress Log).
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** — the `ao` tranche's 2026-07-17 "local execution
> only" ruling (100%-consistent across batch1-8 until today) was explicitly LIFTED 2026-08-08 (operator, interactive);
> see this doc's Progress Log for the full citation trail. AO-dispatchable now, same as every other tranche. Authored
> autonomously (scheduled dispatch) and originally shipped `status: draft` pending operator approval.

## Why this plan exists

A fresh `/ag-closeout-audit ao` run (2026-08-03) re-derived the tranche's 41 current
`generate_ag_closeout_audit_candidates.py`-flagged never-cited members and ran a real per-doc `Workflow` fan-out over
all of them (a first — prior single-doc-agent runs existed, but this is the first run where every one of the 41 got an
independent fresh read in the same pass). Verdict counts: 1 `archivable_now`, 1 `archivable_after_planned_work`, 10
`orphaned_partial_coverage`, 29 `orphaned_never_touched` (39 orphaned total). Of those 39, only 9 clear the
AO-dispatch-scope eligibility bar (bounded, worker-determinable-alone outcome, no operator ruling / credential gap /
calendar gate / open design fork) — this batch extracts those 9, plus the 1 separately-eligible `archivable_now`
bookkeeping item (10 todos total). The remaining 30 orphaned docs stay exactly where they are: operator-gated design
forks (the largest class — several explicitly self-labelled `[OPERATOR]` or "not yet decided, for operator review"),
credential/host-access gaps, unscoped design questions that need a `/plan-brainstorm` pass first, or work already
claimed/sequenced by the still-active worker-liveness/watchdog cluster the operator ruled on 2026-07-29. Full per-doc
reasoning for all 41 (including the 30 declined) lives in this run's own Workflow journal, cited in the Progress Log
below rather than duplicated here.

## Rules for every worker on this plan

- **Put each todo's new test cases in a test module named for that todo's own concern** — never add to a test module
  another todo on this plan also touches. The todos below are file-disjoint EXCEPT the two explicit same-file pairs
  called out below.
- **File-adjacency #1 (hard sequencing, same file)**: todo 2 (archive `ao_db_lock_storm_and_stuck_shutdown_outage`) and
  todo 3 (`ao_tranche_full_content_audit_findings` bookkeeping) BOTH edit
  `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md` — todo 2 corrects one stale "MISTAGGED" table row,
  todo 3 corrects a different MOVED-item summary sentence + table cell. **Land todo 2 before todo 3** (re-pull fresh
  immediately before todo 3's edit and re-check for a merge conflict on that file — it is actively co-edited by
  na-eligibility-audit/context-scout passes on an almost-daily cadence and measured 983/1000 lines on 2026-08-06
  (`wc -l`, /plan-reconcile ao — was 902/1000 at drafting time; the file keeps growing, so **re-measure again
  immediately before shipping this todo**, do not trust either cached figure).
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
  sign-off (same convention batch2's `[DOCS] P1` codex-edit todo used). `cursor-configs/CLAUDE.md` measured 40,942 B at
  drafting time (18 B headroom) and **40,956 B on 2026-08-06** (`wc -c`, /plan-reconcile ao — only 4 B headroom against
  the 40,960 B hard cap now) — **re-measure again immediately before shipping this todo**, headroom is shrinking and any
  net-positive addition needs an offsetting condensation in the same edit; extend the existing SSOT-pointer
  parenthetical rather than adding a new sentence.
- Do not edit a source issue doc's checkboxes beyond appending your evidence line to the todo you executed. The paired
  finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md`) reconciles evidence back into
  every source doc and runs archival.
- No todo below deletes prod data, mutates a GCS bucket, or launches a VM.

## Todos

- [x] ✅ [DOCS] P2. **Mirror the already-shipped peer-vs-operator reply-routing branch from `agents/main.md` STEP 2B
      into `agents/review.md` STEP 2** (currently the old unconditional "for each message... POST your reply" pattern
      with no `in_reply_to`/`from_role` branching — the source doc's own cited line numbers have drifted, content-search
      for the phrase instead). Document that `/reply` with `in_reply_to` set is the preferred path for answering ANY
      drained message regardless of `from_role` (operator or review's own role → own-thread ack as before; a genuine
      peer role → `/reply` auto-cross-routes to that peer's thread + tmux nudge, backend behavior already live since
      `agent-orchestrator@738b2d3`), and that `POST /api/agents/by-role/<role>/message` remains reserved for brand-new
      outbound-only pings (no `in_reply_to`, never acks, redelivers until the ~30-cap). Docs-only change; does not touch
      `server/routes/agents.py`. **Done when**: `agents/review.md` STEP 2's text and curl example describe the same
      cross-role auto-routing `agents/main.md` STEP 2B already describes (verified by a side-by-side diff of the two
      sections, adapted only for review's own STEP numbering/message-flow context); the target issue doc's line-182 todo
      is flipped `[x]` with the shipping commit sha cited in the same turn. Source:
      `/plans/active/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md` (its
      4th, docs-only item — its P1 backend-routing-code item and P3 operator-sign-off item are explicitly self-gated in
      the source doc and NOT in scope here). Repo: unified-trading-pm. — unified-trading-pm@6c4e57b8a (corrected
      2026-08-08: original citation `ea5d699c9` was fabricated/unresolvable; real shipping commit verified via
      `git log -- agents/review.md`, see the source doc's matching correction note)

- [x] ✅ [REVIEW] P2. **Close out `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` — pure bookkeeping, no new
      investigation.** ~~Flip its remaining `[OPERATOR] P2` / `[REVIEW] P2` checkboxes~~ — **stale premise**: both were
      already `[x]` (closed by other sessions on 2026-08-06, before this todo was dispatched). ~~Set
      `status: resolved` + run the 6-step archival ritual~~ — **not done**: this doc's own `/plan-reconcile ao` pass,
      also 2026-08-06 (same day, after both checkboxes closed — postdates and supersedes this todo's premise), added an
      explicit DO-NOT-ARCHIVE guard: Problem 1 (the SQLite `database is locked` storm) is not resolved by anything in
      the doc, and it must stay `status: open` until that closes (see the doc's own `## Follow-ups` `[AO] P0` todo).
      Archiving now would silently drop a live, still-tracked P0 finding. Did the safe bookkeeping subset instead: added
      `/plans/archive/issues/orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md` and
      `/plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md` to the doc's `related:`, and
      recorded this finding in the doc's own Progress Log. The
      `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md` MISTAGGED-row correction is deferred with it —
      the doc is not actually closed yet, so there is nothing to retag out of that bucket. Source:
      `/plans/active/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`. Repo: unified-trading-pm. —
      unified-trading-pm (this commit)

- [x] [DOCS] P3. ✅ **Close `ao_tranche_full_content_audit_findings_2026_07_31.md`'s §3 (duplicate-doc merge) and §4
      (stale MOVED-item bookkeeping) — DONE 2026-08-08.** (a) Both duplicate docs were already `status: resolved` +
      archived from an earlier sweep, but the 07-30 doc was missing the machine-readable `superseded_by:` pointer (had
      only `resolved_by:` prose) — added `superseded_by: [ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26]`
      and folded its two extra root-cause candidates into the 07-26 survivor's "Why it matters" section. No re-archival
      needed (already there). (b) **Finding that changed scope**: live-checked every `➡️ MOVED 2026-07-20 to <child>`
      bullet tied to all 3 named children in `ao_open_issues_consolidated_close_out_2026_07_17.md` — all 14 (not just
      `ao_fleet_observability_kpis`'s 6) were **already** `- [x]` with `DONE via <child>` citations pre-existing from
      earlier sessions; only the summary sentence was stale (claimed "stay open... still active" when the status table
      already showed all 3 archived). Corrected that sentence (all 29 MOVED items now stated closed) — and had to trim
      it to a net -1 line to clear `check_line_caps.sh`'s HARD gate, the doc having crept to exactly 1001L (now 1000L,
      right at the soft-warn line, zero headroom for the next touch). `ao_fleet_infra_hardening`'s status-table cell was
      already accurate, no separate fix needed. This doc's own §3/§4 todos flipped `[x]` with citations; §1/§2 stay
      `[x]`-operator-ruled as before. Source:
      `/plans/active/issues/ao_tranche_full_content_audit_findings_2026_07_31.md` (§3+§4 only). Repo:
      unified-trading-pm. — unified-trading-pm (this commit)

- [x] ✅ [DATA] P2. **Read-only diagnostic on the orchestrator VM's own `data/state/state.db` + `activity_log` (no
      external credential needed — same host every dispatched worker already runs on).** For each of the 5
      escalation/agent_ids `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`'s Progress Log names
      (`agt-79063c`, `agt-0cd704`, `agt-765e33`, `agt-8fa8d1`, `agt-8e95ca`), determine (a) whether an `AgentRow` with
      that `agent_id` exists now or ever existed (cross-check `escalation_dispatched`/`plan_health_dispatch`
      `activity_log` rows for that id if the `AgentRow` itself is gone/archived), (b) if found, its current
      `status`/`tmux_session`, and (c) if it existed then transitioned away from active/stale before its worker's
      `/done` call, the `activity_log` event that did it. **Do NOT attempt the code fix** (that doc's Todo 2) in this
      same todo — it is two-hypothesis-contingent on this diagnostic's result, a separate gated follow-up. **Done
      2026-08-08** (data_engineering, slot 11) — queried the LIVE `agent-orchestrator/data/state/state.db` (`mode=ro`;
      NOT the empty 0-byte root-clone artifact of the same basename) for all 5 ids. None has a current `AgentRow` (table
      itself appears to carry a rolling retention window, unconfirmed mechanism, independent of this bug); all 5
      registrations are confirmed indirectly via `escalation_dispatched`/`plan_health_dispatched` (one-shot registration
      never logs its own `agent_registered` event — only the persistent-agent `/register` path does,
      `server/routes/agents.py:764`); all 5 were archived via the SAME event, `tmux_session_lost`
      (`archived_lifecycle_complete: true`, from `tmux_pruner.py`'s dead-tmux-session sweep calling
      `archive_agent(exit_reason="reaped-stale")` — confirmed as the ONLY possible transition path since `health.py`
      explicitly skips its silence-based stale dimmers for `lifecycle in (one_shot, scheduled)`), across 3 distinct
      proximate triggers (slot-reuse collision ×2 — the same physical tmux pane completed an unrelated Class-A task
      seconds before the reap; context-saturation wedge-kill ×1; plain silent session loss ×2). Full per-id table +
      evidence in the source doc's new dated Progress Log entry. Source:
      `/plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md` (diagnostic half of its
      remaining scope only; its own [DATA] P2 todo flipped `[x]` in the same commit). Repo: agent-orchestrator
      (read-only, no code changed). — unified-trading-pm (this commit)

- [x] ✅ [BACKEND] P2. **CLOSED 2026-08-08 — verified via source-doc re-read, option (a) applies.** The source doc
      (`host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`) was independently resolved+archived
      2026-08-06 (`resolved_by`: "the standing `[DEVOPS] P1` admission-semaphore todo found already shipped via
      unified-trading-pm's `qg-host-governor.sh` (flock-based, wired into `base-service.sh`/`base-library.sh`); checkbox
      had never been flipped") — its `[DEVOPS] P1` checkbox is already `[x]` at
      `/plans/archive/issues/host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md:146`, citing
      `qg_governor_acquire`'s real `flock`-based `K=max(2, floor(cores/4))` token semaphore wired into both entry points
      — matches this todo's own done-when option (a) exactly. No new verification needed; this todo's own ask was
      answered by a different process before this plan could be dispatched. **Verify whether the shipped
      `qg_host_adaptive_resource_governor_2026_07_14.md` reservation-ledger admission governor satisfies
      `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`'s own still-open `[DEVOPS] P1`
      done-when** — a real host-level semaphore gating full-suite QG launches on the shared orchestrator host so they
      queue instead of pinning the host at saturation. Original text follows. Check specifically against the 2026-07-26
      incident's own facts (the saturating QG was the features-service full-suite QG, a `base-service.sh`-sourcing repo
      the governor's admission hook covers) and against the 2026-08-02 finding that the governor's ledger-sharing only
      covers the slot-worktree topology, not the separate GHA-glue-runner cross-repo gap (forked into
      `qg_governor_glue_runner_ledger_coordination_2026_08_03.md`). **Done when**: either (a) the `[DEVOPS] P1` checkbox
      flips `[x]` citing the governor's shipped commit(s)/tests as evidence, with an archival check to follow, or (b) it
      stays open with a NEW dated Progress Log entry naming the SPECIFIC uncovered gap with evidence — not a 4th silent
      re-confirmation of "genuinely open." Source:
      `/plans/archive/issues/host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md` (`[DEVOPS] P1`
      only). Repo: agent-orchestrator (verification, read-only + a possible checkbox flip).

- [ ] [DOCS] P2. [OPERATOR] **DESCRIPTIVE content only — do NOT resolve or pre-empt the still-open `[OPERATOR] P1`
      decision in the source doc.** Fold the 2026-08-01 multi-agent slot-collision incident into two governance docs. In
      `/codex/05-infrastructure/per-tab-worktrees.md`'s "Troubleshooting" section, add a subsection naming this as a
      DISTINCT failure mode from AO-worker-to-AO-worker slot collision: multiple concurrent `claude` processes/operators
      sharing ONE slot's single git checkout (observed: up to 6 concurrent processes on `.tabs/1`, repeated
      `.git/index.lock` contention, autostash-pop re-fights, wrong commit author attribution since `.git/config`'s
      `user.name`/`user.email` is shared state) — cite the interim mitigation available today
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

- [x] ✅ [BACKEND] P2. **Close the connection-release-proof gap on
      `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md`'s still-open "Determine root cause: connection
      LEAK vs. concurrency-over-pool" todo** — DONE 2026-08-08 (slot 31). `agent-orchestrator@54b86a9`
      (`test(db): prove pool-exhaustion + release-safe recovery for pool exhaustion issue`): (1) confirmed by direct
      source read — `server/routes/state.py::get_state` → `server/state_store/slots.py::list_slots`
      (`read_only_session_scope`), `server/routes/agents.py::agent_poll` (`session_scope`),
      `server/routes/git_health.py::post_slot_git_status`/`get_slot_git_status` (`session_scope`) — all 4 route through
      `session_scope()`/`read_only_session_scope()`, which release via `finally: session.close()`
      (`server/db.py:117-152`); no raw session-factory call skips cleanup. (2) Added
      `tests/test_db_pool_exhaustion_recovery.py`, mirroring `tests/test_db_read_only_session.py`'s style: checks out
      `pool_size + max_overflow` (5+10=15, SQLAlchemy `QueuePool` defaults — `make_engine` never overrides them)
      connections via `get_read_only_session_factory()`, asserts the next checkout raises `sqlalchemy.exc.TimeoutError`,
      releases the held sessions, and asserts a fresh session succeeds promptly (both exhaustion and recovery
      demonstrated in one test). `quality-gates.sh` green (2779 passed, 2 skipped) on this exact SHA. Source
      `[BACKEND] P2` todo flipped in
      `/plans/active/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` citing the same test
      module + SHA. Repo: agent-orchestrator.

- [x] ✅ [SCRIPT] P3. **Close out the stale `[SCRIPT] P3]` todo on
      `plan_health_tests_leak_real_slack_alerts_2026_07_24.md` via VERIFICATION, not re-implementation.** — DONE
      2026-08-06 (slot 2). Verified `unified-trading-pm@2db15bb21`
      (`fix(dev): env-var fallback for slack-read-channel.py when gcloud ADC fails`, 2026-07-28): the
      `SLACK_ALERTS_READER_BOT_TOKEN` env-var fallback at `scripts/dev/slack-read-channel.py:65`
      (`os.environ.get("SLACK_ALERTS_READER_BOT_TOKEN", "")  # noqa:     qg-empty-fallback`) satisfies the original Gate
      — documented as secondary (script header lines 12-30), never touches disk/argv (env var only), and the
      `# noqa: qg-empty-fallback` marker permanently exempts it from the `no_empty_string_fallback_baseline` ratchet.
      The na-eligibility-audit's 2026-07-30 "direction superseded" annotation (ruling: grant IAM + REMOVE fallback)
      postdates the shipped fix by 2 days; the fallback is live, gate-compliant, and the IAM-grant-vs-fallback tradeoff
      is a separate design decision tracked in the issue doc's Progress Log. Source issue doc's `[SCRIPT] P3` flipped
      `[x]` in the same turn with the same evidence. `check_no_empty_string_fallback.py` count verified <= 319 (the
      `# noqa` marker keeps this site excluded).

- [x] ✅ [INFRA] P1. **In `agent-orchestrator/server/orphan_reap.py`'s reap-classification path, before treating a
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
      agent-orchestrator. — agent-orchestrator@f91b4d0

## Deferred — full per-doc disposition of the 31 declined orphaned candidates

**Ledger check**: 41 candidates − 1 `archivable_now` − 1 `archivable_after_planned_work` − 9 orphaned-and-eligible
(drafted as todos 1, 3-10 above) = **31** orphaned-and-declined (corrected 2026-08-06 (/plan-reconcile ao): the "= 30"
this formula previously concluded did not match its own enumerated list below, which a direct recount gives 31 —
matching this doc's own 2026-08-03 self-correction entry's 24+7=31 math; the "9 orphaned-and-eligible" subtraction input
above is the stale figure the arithmetic never reconciled against). All 31 named below (recounted via `grep -oE` over
the category list, not eyeballed). Every one falls into one of these non-batchable categories per the skill's own
taxonomy:

- **Operator-gated** (an explicit `[OPERATOR]` tag or "not yet decided, for operator review" framing — the largest
  class): `ao_backlog_no_collision_gate_long_running_driver_todos_2026_08_02.md`,
  `ao_boot_stub_session_vars_field_name_mismatch_2026_08_02.md`,
  `ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`,
  `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`,
  `long_lived_vm_logs_not_backed_up_2026_07_02.md`, `orchestrator_vm_e2e_hardening_2026_07_24.md`,
  `ao_residuals_after_dispatch_hardening_2026_07_17.md` (its residual UI-design item — three prior design attempts
  already rejected, remaining fallback is itself an operator ruling: keep waiting vs. abandon the P3),
  `backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md` (its fix is explicitly pulled off the AO queue by a
  standing operator directive, `unified-trading-pm@14478ca26`, to work it interactively — its OTHER concern, the
  duplicate-doc bookkeeping, IS in scope via todo 3 above),
  `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` (needs a plan-destination ruling plus
  orchestrator-server-side `backlog.yaml` file access a worker's slot clone doesn't have),
  `deepseek_claude_blended_provider_routing_2026_07_28.md` (every remaining item needs either operator-held DeepSeek
  credentials + a production `accounts.json` edit under a standing operator hold, elapsed calendar time, or a brand-new
  third-party API key nobody has provisioned).
- **Too-large/unscoped-design** (needs a `/plan-brainstorm` pass before it's dispatch-ready):
  `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md`,
  `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md`'s items 4/5,
  `regen_positional_task_ids_not_content_stable_2026_07_17.md` per its own already-ruled full-scope mandate sitting at
  its source doc, `backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md` (a "Consider whether to build an
  alerting surface at all" fork, no Done-when), `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md` (a
  "Consider whether... is worth..." fork its own author declined to make standalone).
- **Already claimed** by the still-executing worker-liveness/watchdog cluster's own 2026-07-29 operator sequencing:
  `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`,
  `wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`,
  `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`; or by another doc's own already-owned
  todo: `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md` (its remaining item
  duplicates `regen_positional_task_ids_not_content_stable_2026_07_17.md`'s own todo — both that doc's annotation and
  batch1's archived Deferred section explicitly forbid drafting a competing todo here); **moved here 2026-08-06
  (/plan-reconcile ao)**: `git_health_not_clean_since_pinned_constant_2026_07_27.md` (2 of its 3 `[BACKEND] P3` todos
  are already tracked as one combined todo in `/plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md`
  (archived 2026-08-07, `assigned_vm: planning`), same "another doc's own already-owned todo" shape as the
  `orchestrator_planregen_prune...` case just above — its 3rd todo is a genuine design-judgment fork (new field vs.
  hysteresis bugfix) that batch3's own combined todo explicitly excludes from its bounded scope, so it was previously
  mis-bucketed under "Credential/host-access gaps" below, which does not describe its actual blocker).
- **Credential/host-access gaps** beyond a standard dev checkout:
  `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`'s optional leg.
- **Newly-created (2026-08-01..08-03) docs**, each independently gated on a design fork or operator decision per their
  own text: `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`,
  `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`,
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`,
  `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`,
  `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`'s items 2-4,
  `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`,
  `qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md`,
  `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s own still-open cross-role-file item,
  `tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md`,
  `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`.

None are re-triageable by re-running this same mechanical filter again without new information — the next
`/ag-closeout-audit ao` pass should re-check each one's _specific named gate_ (per the skill's iterative-drain
methodology step 1), not re-derive the classification from scratch.

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
  `orphaned_never_touched` (39 orphaned total). Of the 39 orphaned, 9 cleared AO-dispatch-scope eligibility (plus the 1
  separately-eligible `archivable_now` item, for 10 todos total). Phase 3's conflict-check ran against the whole
  `plans/active` corpus for every eligible candidate's target file(s); found 2 same-file adjacencies
  (`ao_open_issues_consolidated_close_out_2026_07_17.md` touched by both todo 2 and todo 3;
  `worker_liveness/_respawn.py` and `orphan_reap.py` each shared with an unrelated, NA, different-facet sibling todo) —
  handled via sequencing/caution rules per batch3/batch4's own precedent rather than exclusion. Left `status: draft`
  deliberately — flipping to `active` is the operator's call. Full per-doc Phase 1 verdicts + reasoning for all 41
  candidates (including the 30 declined): Workflow run `wf_d2e30c15-0f6`, journal at
  `subagents/workflows/wf_d2e30c15-0f6/journal.jsonl` (agent-orchestrator dispatch host).
- **2026-08-03 (same-session self-correction)** — First-draft arithmetic was off by one (said "29 declined" instead of
  30 — the 10 AO-eligible total splits into 9 orphaned-eligible + 1 separately-eligible `archivable_now` bookkeeping
  item, not 10 orphaned-eligible) and the Deferred section's per-doc ledger, on a direct recount against the Workflow
  journal, named only 24 of the 30 declined docs (7 missing: `ao_residuals_after_dispatch_hardening_2026_07_17.md`,
  `backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md`,
  `backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md`,
  `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`,
  `deepseek_claude_blended_provider_routing_2026_07_28.md`,
  `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md`,
  `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md`). Fixed both: corrected the count throughout, added all
  7 missing docs to their correct taxonomy category with reasoning pulled from their own Workflow verdict, and added an
  explicit ledger-check line to the Deferred section header per this skill's "count it, don't eyeball it" rule. No todo
  content changed — this was a bookkeeping-accuracy fix on the Deferred section only.
- **2026-08-06 (slot 2, operator session)** — Todo 9 (`[SCRIPT] P3`) closed via verification: confirmed
  `unified-trading-pm@2db15bb21` (2026-07-28) shipped the `SLACK_ALERTS_READER_BOT_TOKEN` env-var fallback with
  `# noqa: qg-empty-fallback` at `scripts/dev/slack-read-channel.py:65`, satisfying the original Gate ("documented as
  secondary, never touches disk/argv"). The `# noqa` marker exempts it from the `no_empty_string_fallback_baseline`
  ratchet. The 2026-07-30 "direction superseded" annotation (grant IAM + REMOVE fallback) postdates the shipped fix by 2
  days; whether to additionally grant the IAM role is a live design tradeoff, not a correctness gap. Source issue doc's
  `[SCRIPT] P3` also flipped `[x]` in the same turn.
- **2026-08-08 (operator-authorized draft→active review)** — Re-ran the shared 3-surface conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) against (a) every active
  `assigned_vm: planning` plan in `parent_epic: orchestrator_master` (only the batch2-8 finalize twins, all correctly
  `gate_on_depends`-held — no independent claim), (b) sibling batches 6/7/8 (no new overlap beyond what those docs' own
  drafting already cross-referenced), and (c) `ao_open_issues_consolidated_close_out_2026_07_17.md` (no new conflict).
  Also spot-checked every open todo's Source doc for post-drafting closure: todo 5's Source
  (`host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`) was independently resolved+archived
  2026-08-06, so its `[DEVOPS] P1` was already answered — closed todo 5 above via verification (option (a), hard
  evidence: the archived doc's own `[x]` checkbox + `resolved_by` citation). Todos 1-4, 6-8, 10 re-verified still
  genuinely open against their live Source docs (todo 1: `agents/review.md` STEP 2 still shows unconditional `/reply`,
  no `in_reply_to`/`from_role` branch, confirmed by direct grep; todo 2: the source doc's `[OPERATOR]`/`[REVIEW]`
  checkboxes are already `[x]` but the doc itself is still `status: open`, un-archived, and the tracker's MISTAGGED-row
  bookkeeping this todo also covers is still pending — todo correctly stays open for that remainder). **Investigated the
  `assigned_vm: NA`/`execution_scope: local-only` frontmatter (atypical for a fresh `_satellite_ao_dispatch_batch{N}_`
  doc per `ag-closeout-audit/SKILL.md`'s own stated `assigned_vm: planning` convention) before touching either field**:
  confirmed via `ao_open_issues_consolidated_close_out_2026_07_17.md`'s own frontmatter `source:` block — a direct
  operator quote, 2026-07-17: _"for all the remaining issues check which are live vs resolved … for all the relevant
  open issue docs create ONE plan, local execution"_ — and its body (line ~98: "**Human plan — operator session executes
  it**"; line ~107: "All are **LOCAL** … operator-assigned agents on this host, never AO-dispatched") that this is a
  real, deliberate, tranche-rooted operator ruling this batch inherits as the consolidated closeout's own satellite
  extraction, not an unexplained deviation — batch2's 2026-08-01 na-eligibility-audit note ("worth the operator's
  attention as a possible systemic skill-convention drift… no explicit ruling/citation found") had not yet traced it to
  this origin. Given the ruling is real but was never re-cited per-batch (and a 2026-07-17-vintage ruling extending to
  fresh 2026-08-03..08-08 batches is itself worth an explicit re-confirmation), left `assigned_vm`/ `execution_scope`
  UNCHANGED — flipping `status: draft → active` only, matching the exact precedent already live on batch2/batch3
  (`status: active`, `assigned_vm: NA`). Fixed the stale draft-era H1 banner to match. **Flagged to the operator as a
  corpus-wide question worth one explicit ruling**: should the `ao` tranche's satellite batches keep deviating from the
  general `assigned_vm: planning` convention indefinitely (codify the exception in `ag-closeout-audit/SKILL.md`), or
  should the 2026-07-17 ruling be treated as scoped to that one plan's original children and NOT extended to new batches
  going forward (in which case batch5-8 should be reclassified to `assigned_vm: planning` after this same
  conflict-check)? Not resolved unilaterally here.
- **2026-08-08 (operator, interactive)**: RULED — the 2026-07-17 local-only ruling is LIFTED for batch5-8 going forward;
  `ao`-tranche work now flows to AO like every other tranche. `assigned_vm: NA → planning`,
  `execution_scope: local-only → orchestrator-agent` applied to this doc and its batch6/7/8 siblings, each already
  conflict-checked clean above. This does not retroactively reopen batch2/3 (already `active`/complete under the old
  ruling) — it applies from this ruling forward.
