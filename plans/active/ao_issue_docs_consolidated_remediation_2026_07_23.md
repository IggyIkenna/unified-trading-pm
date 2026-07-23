---
doc_type: plan
title: AO issue-docs consolidated remediation — the open work from the 2026-07-23 plan-reconcile sweep
summary:
  Executes the remaining work found by the /plan-reconcile AO-scope sweep of 2026-07-23, which reconciled all 15
  agent-orchestrator issue docs — closing 12 todos with hard evidence, surfacing 13 that existed nowhere, and archiving
  2 fully-resolved docs. What is left is mostly monitoring-integrity and doc-integrity — systems that report the wrong
  thing rather than systems that are down. Zero P0s. Each todo below cites the issue doc that owns it so the evidence
  trail survives, and each states the evidence a done-claim must produce.
status: draft # NOT ingested — operator reviews before flipping to active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, git-health, worker-liveness, plan-hygiene, doc-integrity, plan-reconcile]
related:
  [
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
    /plans/active/issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md,
    /plans/active/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md,
    /plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md,
  ]
created: 2026-07-23
last_updated: 2026-07-23
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true # see "Concurrency" below — several todos share slot-git-status-report.sh / _git_alerts.py / worker_liveness
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: "/plan-reconcile AO-scope run 2026-07-23; every verdict re-verified against code, git and the live VM"
---

# AO issue-docs consolidated remediation

> **STATUS: DRAFT — not ingested by regen, not dispatchable.** Flip to `active` only after the operator review. The open
> decisions this plan could not settle are listed in **§ Open decisions** at the bottom; several todos below are
> deliberately marked non-dispatchable until those are ruled.

## Why this plan exists

The 2026-07-23 `/plan-reconcile` sweep (AO scope) reconciled all 15 agent-orchestrator issue docs against code, git and
the live VM. Outcome: **12 todos closed** with hard evidence, **13 added** that existed nowhere (four issue docs held
real, code-verified findings with **zero** todos and no plan referencing them — invisible to every progress count), and
**2 docs archived** as fully resolved. This plan is the execution vehicle for what survived.

**Severity is mild and worth stating plainly: there are ZERO P0s.** The two genuinely operational problems both resolved
during the audit — fleet-wide FF-pull starvation is measured absent, and the frozen-clone incident is closed. What
remains is monitoring-integrity (the fleet reporting things that are not true) and doc-integrity (agents reading
instructions that are stale). Those matter because they are the class of defect that hides other defects.

## Concurrency — why `sequential: true`

The template's default is intra-plan concurrency, and it is usually right. It is **not** right here: several todos below
edit the SAME files — `scripts/dev/slot-git-status-report.sh` and `scripts/dev/slot-cron-ff-pull.sh` are each touched by
two different todos, and `server/worker_liveness/_git_alerts.py` plus `server/worker_liveness/__init__.py` are touched
by three. Concurrent todos on one file collide, which is banned by multi-agent safety. `sequential: true` is the only
intra-plan mechanism that prevents it, so it is set. **This costs throughput** — see § Open decisions Q1 for the
split-into-two-plans alternative, which would restore parallelism for the ~20 todos that genuinely do not collide.

**Also note (template §4 caveat):** a `[OPERATOR]` or `BLOCKED-`marked todo does NOT count as a predecessor in a
sequential chain. The non-dispatchable todos below are therefore placed so that none of them is the first link holding
back the rest.

## Codex SSOTs (read before touching the matching area)

- `/codex/05-infrastructure/per-tab-worktrees.md` — slot clones, FF-pull cron, the dirty/liveness discriminator
- `/codex/04-architecture/agent-orchestrator-worker-liveness.md` — watchdog, reaper, git-surfaces pass
- `/codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only alerting, state-transition dedup
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch, roles, assigned_vm semantics
- `/codex/12-agent-workflow/canonical-plan-flow.md` — corrected 2026-07-23; `assigned_vm` is `{planning, NA}`

---

## Phase 1 — git-health count integrity (the reporter tells the truth about dirt)

_Source: `/plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md`_

- [ ] [INFRA] P1. Re-derive `dirty_files` in `scripts/dev/slot-git-status-report.sh` from the sample loop's kept
      non-blank lines so the count can never exceed the captured sample. Build the count from the same array the sample
      loop populates (single source of truth), not an independent `wc -l` on the raw capture — this makes the observed
      `dirty_files=1` + empty-`dirty_files_sample` fingerprint structurally impossible regardless of what upstream
      artifact injects a stray count. Cause-agnostic by design: review proved with `cat -A`/hexdump that the tree emits
      ZERO bytes while the reporter posts 1, so do NOT chase the blank-line theory. **Gate**: a unit/bats test asserting
      a clean tree can never yield `dirty_files>0`, and that `dirty_files` always equals the captured sample length.
- [ ] [INFRA] P2. Add the `df>0 with an empty sample` instrumentation to `scripts/dev/slot-git-status-report.sh` — when
      the computed count is non-zero but the sample array is empty, log the raw captured porcelain bytes via `cat -A` to
      the reporter's own log so the next occurrence pins the wrapper trigger. This is the diagnostic half of the todo
      above; it must survive even after the count is made structurally safe. **Gate**: forcing the condition in a test
      emits the raw-bytes log line.
- [ ] [INFRA] P2. Mirror the same single-source count-integrity fix onto the FF-cron dirty gate in
      `scripts/dev/slot-cron-ff-pull.sh` so a phantom count can never trip `[skip:dirty]` and starve FF-pull. The cron
      computes dirt with the same `git status --porcelain` pattern as the reporter, so it hits the same phantom
      independently. **Gate**: a test where a clean tree yields `ff_pull_last_result != skip:dirty`.
- [ ] [INFRA] P2. Gate the `not_clean_since` CLEAR and the sync-nudge in `server/routes/git_health.py` on
      `dirty_consecutive_ticks >= 2` so one clean blip cannot reset the age a genuinely long-dirty repo has accumulated.
      The reporter already sends the field; this is a server-side change using data that already arrives. **Gate**: a
      unit test proving a single clean poll between two dirty polls does NOT reset `not_clean_since`.
- [ ] [INFRA] P2. Extend that same `dirty_consecutive_ticks >= 2` gate to the FF-pull skip decision in
      `scripts/dev/slot-cron-ff-pull.sh` so a one-tick phantom dirty can never skip an FF-pull whatever produced it. Do
      NOT re-hunt a reporter-internal race first — `agent-orchestrator@529b0dc` (cross-host row clobber, live) is a
      complete mechanism for the all-repos-simultaneous fingerprint and the phantom has not reproduced since. **Gate**:
      a test asserting a single-tick all-repos-dirty observation neither clears `not_clean_since` nor causes an FF-pull
      skip.
- [ ] [INFRA] P2. Verify the unexplained `dirty_files=2172` row for `unified-trading-pm` on host `ip-172-31-0-185` slot
      0 by running `git status --porcelain | wc -l` in that clone and recording which it is. Every non-clean row on the
      `hk` host was verified REAL file-for-file, but this host was unreachable from the audit session, so it is the one
      open doubt — either a genuinely wrecked checkout (its own problem, since that clone can never FF while dirty) or
      the phantom surviving at a new magnitude. **Gate**: the measured count recorded in the issue doc with an explicit
      real-or-phantom verdict.

## Phase 2 — worker liveness (stop pageing on healthy workers, start resolving dead ones)

_Sources: `/plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`,
`/plans/active/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md`,
`/plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`_

- [ ] [BACKEND] P2. Add a liveness-by-progress gate to `maybe_alert_git_staleness` and `maybe_nudge_on_red_repos` in
      `server/worker_liveness/_git_alerts.py` so a burst-committing worker is not classified as wedged. Suppress or
      soften when the worktree's last commit (`git log -1 --format=%ct`) is newer than the sustain window, or a live
      child process runs under it (`pgrep -f <worktree>`). Today these key purely on `dirty_files`/`ahead`/`behind` plus
      age, and `_git_surfaces_pass` runs unconditionally for every slot — its own docstring records that the 2026-07-14
      coverage-gap fix REMOVED the live-worker gate, so an actively-working slot has no exemption. **Gate**: a
      regression test where a recent-commit-but-still-dirty worker does NOT fire the staleness alert, with the
      genuinely-stale-slot tests still green.
- [ ] [BACKEND] P2. Add a periodic dirty-resolution sweep to the worker-liveness watchdog that runs independently of any
      spawn attempt. Every caller of `resolve_dirty_state`/`commit_and_push_dirty_repos` today is spawn or respawn time
      (`spawn_slot`, `_do_spawn`, the `slots_ops` pre-spawn gate, `_respawn`), so a dirty slot nobody tries to spawn
      into stays dirty forever. Reuse those same helpers plus the liveness discriminator — dead or expired
      `.agent-claim` means inherit and commit; a live claim or mtime under 120s means PROTECT. **Gate**: a
      deliberately-idle dirty slot with no tmux and an expired claim is inherited within one sweep interval, evidenced
      by a resolution activity row with NO adjacent spawn event.
- [ ] [INFRA] P2. Escalate the liveness watchdog from soft-kick to hard-kill plus respawn after N consecutive frozen
      observations, and make the counter survive the reset that defeated it. `kick_escalation_threshold` already exists
      and shipped 2026-07-09, but the 2026-07-21 incident (55 kicks in 3h, only 7 counted as `worker_kick_failed`) is
      live proof it did not trip — `ping_advanced`/`post_class=="working"` kept resetting `_consecutive_kick_failures`
      to 0 before it reached the threshold. Fix the reset condition, not the threshold value. **Gate**: a test where a
      worker that keeps answering pings while making no progress still escalates to hard-kill.
- [ ] [INFRA] P2. Add a reclaim-and-push path for a killed or idle slot whose worktree holds committed-but-unpushed
      work. `orphan_reap.py` reaps processes and tmux only — its own docstring says so, and it contains no git logic —
      while `_maybe_send_sync_nudge` merely enqueues a slot message, which is a no-op on a dead worker. Note
      `agent-orchestrator@529b0dc` does NOT cover this: it is a git-status keying fix, not a push path. **Gate**: a slot
      killed with local commits ahead of origin has them pushed (or inherited) without a human touching the box,
      evidenced by the commits appearing on `origin/live-defi-rollout`.
- [ ] [BACKEND] P3. Root-cause slot 4's elevated short-lived-orphan rate, or record an explicit accept-as-cadence
      verdict with the comparison data. Compare `slot_resume_respawned`, `autospawn_failed`, `watchdog_slot_killed` and
      `tmux_session_lost` rates for slot 4 against the other slots NORMALISED PER DISPATCH — raw counts are misleading
      because slot 4's dispatch volume differs — over a multi-day window. The periodic orphan sweep already reaps the
      symptom within ~60s, so this is about knowing whether slot 4 is structurally different. **Gate**: either a fixed
      cause (code diff plus a measured 24h orphan-rate drop) or a recorded cadence verdict citing the per-dispatch
      comparison. Silence is not an outcome.

## Phase 3 — cross-role agent messaging (replies reach the agent that asked)

_Source: `/plans/active/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md`_

- [ ] [BACKEND] P1. Route `agent_reply()` in `server/routes/agents.py` to the ORIGINATING role when the answered message
      came from a peer, instead of always the replier's own thread. It currently calls `post_agent_message_by_role` with
      `target_role=agent.role, direction="from_agent"` unconditionally, and `AgentReplyRequest` in
      `server/models/agents.py` has no cross-role target field — so a reply to a peer lands on the replier's own thread
      and the peer never sees it in its poll. When `in_reply_to` resolves to a message whose `from_role` differs, post
      `direction="to_agent"` to that `from_role` plus the tmux nudge. **Gate**: a regression test proving a cross-role
      reply lands in the target role's next `/poll` (not merely its `/history`), with the existing same-role reply-ack
      tests still green.
- [ ] [DOCS] P2. Codify the peer-versus-operator reply branch in `unified-trading-pm/agents/main.md` STEP 2B so the
      procedure is not folklore. Rule to state: `from_role == "operator"` uses `/reply`; any other `from_role` uses
      `POST /api/agents/by-role/<from_role>/message` with `from_agent_id`. The doc currently says to POST a reply for
      EVERY polled message regardless of `from_role`, and the interim mitigation was done ad hoc in one live session and
      never written down. **Gate**: the diff lands and the next live cross-role exchange shows a `to_agent` message in
      the recipient's poll.

## Phase 4 — doc-integrity: dead references in shipped code

_Source: `/plans/active/issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md`_

- [ ] [BACKEND] P2. Repoint or remove the five dead documentation references in `agent-orchestrator/server/` that point
      at files deleted by `agent-orchestrator@19766e7`. The targets are `docs/AUDIT_FINDINGS_2026_05_18.md`,
      `docs/PLAN.md` and `docs/MAIN_AGENT_CUTOVER_REVIEW.md`, all confirmed absent, cited from `bootstrap.py`,
      `models/__init__.py`, `db.py`, `orm.py` and `routes/slots_worker.py`. Point each at the surviving SSOT or delete
      the dangling clause if the docstring stands alone — do NOT resurrect the deleted files. **Gate**:
      `rg -n 'AUDIT_FINDINGS_2026_05_18|docs/PLAN\.md|MAIN_AGENT_CUTOVER_REVIEW' agent-orchestrator/server/` returns
      zero hits and every replacement pointer resolves to a file that exists.
- [ ] [DOCS] P3. Replace `agent-orchestrator/README.md`'s "Files in This Directory" tree with a pointer, and fix its two
      inline `agents/*.md` links. The tree still lists an `agents/` directory and seven files under it that no longer
      exist — the directory was removed in `agent-orchestrator@5eaea29` and role prompts now live in
      `unified-trading-pm/agents/`. Use a pointer rather than re-listing files that will drift again. **Gate**: every
      path in the README tree resolves and no link targets a nonexistent `agents/` file.
- [ ] [DOCS] P3. Correct the branch-flow sentence in `agent-orchestrator/docs/REPO_PROVENANCE.md` to the current model —
      per-slot clones on `live-defi-rollout`, then LDR to `main` DIRECT with staging bypassed by the per-repo `ldr_main`
      toggle. It still describes the retired `tab -> live-defi-rollout -> staging -> main` flow. SSOT:
      `/codex/08-workflows/ci-cd-flow.md`. **Gate**: no `tab ->` flow description remains in the file.
- [ ] [REVIEW] P2. Correct the "0 dead links" claim in `ao_open_issues_consolidated_close_out_2026_07_17.md`'s
      2026-07-18 Progress Log to state the sweep's actual scope. The cited sweep commits landed roughly ten hours AFTER
      the commit that deleted these files and covered different documents, so the line reads as fleet-wide proof when it
      is not — which is exactly what stops the next person re-running the one-second grep. **Gate**: the entry names
      which commits swept what and links the issue doc for the batch it missed.
- [ ] [DOCS] P3. Add a SUPERSEDED banner (or fix the text) in
      `/codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md`, which still carries live
      `tab/<operator>/<N>` references to the RETIRED tab-branch model with no banner. Same class as the
      `canonical-plan-flow.md` correction already applied 2026-07-23. **Gate**: no unbannered tab-branch instruction
      remains in the file.
- [ ] [REVIEW] P3. Re-annotate or reopen the agent-orchestrator line in
      `plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md` that is still marked SHIPPED with no note about the
      post-pivot re-drift. A `[x]` that predates an architecture pivot reads as current coverage when it is not.
      **Gate**: the line carries either a re-verification date or an explicit reopen.

## Phase 5 — plan-quality defense lines

_Source: `/plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md`_

- [ ] [INFRA] P1. Route `plan_health.py::record_result()`'s `doc_drift` findings through `notify_slot_blocked` so drift
      reaches a worker's blocked queue instead of only a Slack WARN. Today `doc_drift` routes solely to
      `slack_notify.notify_plan_health_findings`, and `notify_slot_blocked` is never invoked from `plan_health.py`.
      **Gate**: a doc_drift finding produces a blocked-queue entry visible via the backlog API, with the existing Slack
      path unchanged.
- [ ] [INFRA] P2. Wire `/docs-reconcile` onto the same 24h cadence as the plan-reconciler by adding an installer timer
      alongside `agent-orchestrator/scripts/install-plan-reconciler-timer.sh`, and state the cadence in both skills' own
      docs. No docs-reconciler timer or cron exists anywhere in the repo today — the skill is operator-triggered only.
      **Gate**: `systemctl list-timers` on the orchestrator VM shows the docs-reconcile timer with a computed
      next-elapse, and one run posts a result.
- [ ] [REVIEW] P2. Re-run the sports closeout hygiene audit end-to-end once the plan-quality defense lines are live and
      confirm all four lines fire. This is gated on the two todos above plus the hard-fail wiring; do not start it
      before they land. **Gate**: the audit output shows each of the four defense lines producing its expected signal,
      recorded in the issue doc.

## Phase 6 — measurement residuals (cheap, but each needs a stated verdict)

- [ ] [BACKEND] P3. Root-cause the 2026-07-12 degradation onset — `worker_polling_dead` going 0 to 587 and the
      spawn-to-dispatch ratio moving from 0.6:1 to 44:1 on that date — or record an explicit not-worth-excavating
      decision. The mechanism itself is fixed; what was never explained is why it STARTED that day, which means a
      recurrence would be invisible until it costs again. One `activity_log` excavation pass is enough. **Gate**: a
      named cause with activity-log evidence, or a recorded decision — not silence. NOTE: this item is ALSO open in
      `ao_open_issues_consolidated_close_out_2026_07_17.md` Phase 5; close both or collapse them into one owner first.
- [ ] [INFRA] P2. Re-test the l2_book task-row divergence once `l2_book_microstructure_capture_2026_07_13.md` returns to
      `assigned_vm: planning`, confirming every open todo gets a task row. The original measurement is currently VOID,
      not resolved — that plan is `assigned_vm: NA` after the fleet-wide dispatch pause, so absent task rows are correct
      behaviour rather than the reopen-drop defect. If the BLOCKED todos are again absent while the plan IS ingested,
      the defect is live. **Gate**: the per-todo task-row comparison recorded with an explicit live-or-clear verdict.

---

## Non-dispatchable — kept visible, never ingested

> These carry `[OPERATOR]` or a `BLOCKED-` token so regen excludes them (template §3). They are placed AFTER the
> dispatchable todos deliberately: a non-dispatchable todo does not count as a predecessor in a `sequential` chain, so
> putting one first would let the rest dispatch immediately regardless.

- [ ] [OPERATOR] P2. Rule on the epic-VM code artifacts — `deployment-service/scripts/vm/launch-epic-vm.sh`,
      `launch-epic-vm-aws.sh`, and the ten `agent-orch-vm-*` prefixes registered `LONG_LIVED_LIVE` in
      `vm_prefix_registry.py`. Per-epic VMs were deprecated 2026-06-27 and CLAUDE.md says delete deprecated code with no
      shims, but the failover module received an explicit KEEP ruling on the multi-VM-may-return argument, so this is a
      judgment call rather than a cleanup. Operator direction 2026-07-23 was to file it and decide later. **Gate**: a
      recorded keep-or-delete ruling; if KEEP, the named single-VM scenario that still needs it.
- [ ] [OPERATOR] P3. Spot-check the live fleet for a slot dirty over 24h with no live session, to rank the periodic
      dirty-resolution sweep. If none exists this is a structural gap with no active incident — a reason to sequence it
      behind P1 work, NOT a reason to close it. **Gate**: the one-line finding recorded in the issue doc.
- [ ] [BACKEND] P2. BLOCKED-OPERATOR-DECISION — resolve the `/api/escalate` versus proposed `/api/escalation/{id}` route
      collision before ANY escalation code is written. `/api/escalate` already exists as the GHA-to-orchestrator CI-wall
      judgment dispatch; the proposed route is operator escalation. Whoever implements the second without noticing the
      first will either collide or wire operator escalations into the CI judgment path. Blocked on the
      `escalation_and_disaster_recovery_master` epic being un-paused. **Gate**: one of the two is renamed, or a recorded
      decision explains why the near-collision is acceptable.
- [ ] [UI] P3. BLOCKED-UPSTREAM-DESIGN — build the backlog-relations view once a design lands. The brief plus real data
      and a 100-task synthetic fixture were handed to the design agent on 2026-07-17; re-checked 2026-07-23 with no
      movement, no `GET /api/backlog/graph` endpoint and no relations UI commit. The model is a cross-cutting GRAPH, not
      a hierarchy, which is why three table/tree attempts were rejected. **Gate**: design received, implemented, and the
      relation a table cannot express — one prereq gating tasks in multiple plans — is visible in one view.

## Conservation — where all 33 issue-doc todos went

The sweep left **33** open todos across 13 AO issue docs. This plan carries **28**; the accounting for the other 5 is
below, so nothing is silently dropped.

| Disposition                                              | Count | Where it is                                                      |
| -------------------------------------------------------- | ----- | ---------------------------------------------------------------- |
| Dispatchable todos in this plan                          | 24    | Phases 1-6 above                                                 |
| Non-dispatchable, kept visible here                      | 4     | § Non-dispatchable (2 `[OPERATOR]`, 2 `BLOCKED-`)                |
| Parked decisions — judgment calls, not AO-eligible       | 2     | § Deliberately NOT included, below; stay in their own issue docs |
| Pre-ship sign-off gates, not standalone work             | 2     | § Open decisions Q3 — operator rules whether these become todos  |
| Pointer-only lines (a doc referring work to another doc) | 1     | `ao_docs_reconciliation`'s Tier-6 line, which points at the      |
|                                                          |       | dead-links issue doc whose todos ARE in Phase 4                  |

## Deliberately NOT included

Two open todos from the swept issue docs are **parked decisions, not work**, and per template §4 ("bounded outcome only
— no judgment calls in a todo") they are not eligible for AO dispatch. They stay in their own issue docs:

- **`auto_park_no_flipper_rule_not_mechanism_enforced`** — "decide and build, or explicitly decline, mechanism-level
  enforcement" is an open design question with three candidate options and no chosen target. Resolve it interactively
  first, then write the AO todo against the outcome.
- **`regen_positional_task_ids_not_content_stable`** — content-derived task ids are explicitly deferred and reopen ONLY
  if a new incident proves the landed fixes insufficient. No such incident has occurred.

## Open decisions

See the review conversation — four questions were raised with the operator when this plan was drafted (concurrency
model, the 30 over-cap plans blocking the hard-fail wiring, whether the two pre-ship sign-offs should be plan todos or a
review gate, and whether the doc-integrity phase should be split to a separate role). This section is updated with the
rulings before the plan flips to `active`.

## Progress Log

- **2026-07-23**: Plan authored from the `/plan-reconcile` AO-scope sweep. Born `status: draft` per the operator, who
  reviews before dispatch. 26 dispatchable todos plus 4 non-dispatchable (2 `[OPERATOR]`, 2 `BLOCKED-`), and 2 parked
  decisions deliberately excluded. `sequential: true` set because of real same-file overlap in Phases 1 and 2.
