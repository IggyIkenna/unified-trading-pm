---
doc_type: plan
title: AO satellite AO batch 2 — second dispatch batch extracted from the AO tranche's satellite docs
summary: >-
  SECOND AO-dispatch batch for the `ao` topic tranche, produced by the `/ag-closeout-audit ao` skill run (2026-07-30,
  autonomous mode, real Workflow per-doc fan-out — unlike the 2026-07-26/07-30 prior audits, which were single-threaded
  with no Workflow/Agent tool access). Batch1 (2026-07-26) landed 5 of its 11 todos and left 6 open (one
  BLOCKED-CREDENTIALS); its own Deferred section already covers most of the remaining conflict-gated cluster (the
  worker-liveness/watchdog contradiction — resolved by the operator 2026-07-29 and now executing directly against the
  source docs, not through a batch). This batch extracts a DIFFERENT set: 8 conflict-clear, bounded items surfaced by a
  fresh Phase 0-1 pass over all 42 current AO-tranche-primary docs — 5 from the `never_cited` set (mechanically-derived
  + 2 more content-verified via the Orthogonality HARD CHECK), 3 from residuals batch1 itself flagged but explicitly
  left out of its own file scope (JWT secret pin, orch_token re-mint, a codex-doc edit). One item
  (`orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage`'s DEVOPS P1) is the same "highest-value
  now-actionable orphan" the prior 2026-07-30 audit identified but did not batch (no operator was reachable that run).
  Every todo below targets files disjoint from every sibling todo, so the plan needs no `sequential` gate.
status: draft
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, features-service, unified-api-contracts, strategy-service]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-2, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit ao skill run 2026-07-30 (autonomous, scheduled dispatch agt-b4e164) — Phase 0 re-derived the
  tranche's 42 current members via scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche ao, confirmed
  batch1+finalize+ao_open_issues_consolidated_close_out_2026_07_17 as the real covering-plan set (the latter is missed
  by the script's filename-pattern glob but manually confirmed as a genuine covering plan per Phase 0.2's
  dependency-graph path); Phase 1 ran a real Workflow fan-out (16 agents, one per never-cited/ partial-coverage
  candidate) plus direct reads of the remaining cited docs; Phase 3 ran the conflict-check grep against both the 3
  covering docs and the whole plans/active corpus before drafting (caught one cross-tranche duplicate-claim, held out of
  this batch).
---

# AO satellite AO batch 2

> **`status: draft` — NOT ingested, NOT dispatched.** Flipping this to `active` is the operator's call
> (`/plans/PLAN_FORMAT.md`; CLAUDE.md § "Plan destination — ASK BEFORE CREATING"). Authored autonomously (scheduled
> dispatch); deliberately stops at draft per the skill's Autonomous-mode contract.

## Why this plan exists

`ao_satellite_ao_dispatch_batch1_2026_07_26.md` is `status: active` with 5/11 todos done and 6 still open (one
BLOCKED-CREDENTIALS, pending an operator IAM grant this plan does not touch). Its own Deferred sections already track
the largest residual cluster (the worker-liveness/watchdog kick+escalation contradiction), which the operator resolved
2026-07-29 and which is now executing directly against its source issue docs — not through a batch, so it is
intentionally NOT re-extracted here. This batch instead covers a **different, freshly-discovered** set: of the 42
AG-primary docs currently tagged `asset_group: [ao]`, a fresh per-doc Workflow pass found 8 conflict-clear,
dispatch-eligible items with no current coverage. See this plan's Deferred sections for the full accounting of every
other orphaned candidate considered and why it was NOT drafted.

## Rules for every worker on this plan

- **Put each todo's new test cases in a test module named for that todo's own concern** — never add to a test module
  another todo on this plan also touches. The todos below are file-disjoint by construction; keep them that way.
- **Do not edit the source issue doc's checkboxes** beyond appending your evidence line to the todo you executed. The
  paired finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md`) reconciles evidence back
  into every source doc and runs archival.
- Todo 6 (JWT secret pin) restarts the live `orchestrator.service` — per the 2026-07-28 CLAUDE.md ruling,
  maintenance-window restarts do not need operator scheduling pre-live-trading (brief downtime OK); group it with any
  OTHER pending shared-orchestrator restart/pause work if one is in flight when you pick this up, rather than restarting
  twice.
- No todo below deletes prod data, mutates a GCS bucket beyond writing one new small secret object, or launches a VM.

## Todos

- [ ] [BACKEND] P2. **Add a 4th `/done`-gate disposition for a genuinely-open todo blocked on another owner's in-flight
      fix, and fix a recurring self-archival rename-blindness bug.** In `agent-orchestrator/server/verify.py`: (1) add
      `_diff_blocks_checkbox` matching a `BLOCKED-ON:<ref>`-style marker (mirroring the existing
      `_diff_cancels_checkbox`/`_diff_defers_checkbox`), accepted via `reason="todo_blocked_pending_other_owner"`; (2)
      extend Mode-2's empty-`pm_shas` fallback to recognize CANCELLED/DEFERRED/BLOCKED markers on the current on-disk
      plan text (mirroring Mode-1's existing L920-932 fallback), not just a raw `[x]` flip; (3) fix the self-archival
      rename-blindness variant — follow git renames in `_pm_log_commits_touching_plan_ref`/`_mode2_disposition` so a
      flip-and-archive-in-one-commit is seen (a recurrence, confirmed twice more, of the already-archived
      `ao_done_gate_checkbox_flip_blind_to_self_archived_plan_ref_2026_07_26.md` bug). **Done when**: `quality-gates.sh`
      green + a regression test per sub-item (blocked-marker acceptance, CANCELLED/DEFERRED/ BLOCKED-on-disk-text
      fallback, rename-followed self-archival detection). Source:
      `/plans/active/issues/ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (3 of its 4 todos
      — the 4th, a codex-doc note, is sequenced behind these and stays with the source doc). Repo: agent-orchestrator.
- [ ] [WORKER] P1. **Re-verify, then recover-or-mark-moot, the 4 named orphaned worker commits.** For each of
      features-service `207afd62` + `d1c1ad8a`, unified-api-contracts `724bd9be`, agent-orchestrator `559452e`: check
      (via `git log --grep` / content-diff against current `origin/live-defi-rollout`) whether the same functional
      change already landed under a different SHA via independent duplicate work. This audit's own Phase-1 pass already
      found strong evidence all 4 did — `a90256f5` (features-service, same census-manifest persist as `207afd62`),
      `a9429cba` (features-service, same `accepted_quotes_for_venue` wiring as `d1c1ad8a`), `698b5b6f`
      (unified-api-contracts, byte-identical commit message/date to `724bd9be`'s saved patch), `09cda29`
      (agent-orchestrator, same `/api/backlog/{id}/reconcile-brief` feature as `559452e`) — confirm each, then flip the
      corresponding item MOOT-SUPERSEDED citing the landed SHA. For any genuinely still-missing item instead,
      cherry-pick the saved backstop patch (`.orch-orphan-commits-recovery/`) onto current origin tip and ship via
      quickmerge per the doc's own stated recipe. **Done when**: all 4 items have an explicit disposition
      (MOOT-SUPERSEDED + landed SHA, or recovered + re-shipped SHA) recorded in the source doc. Source:
      `/plans/active/issues/branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md`. Repos:
      features-service, unified-api-contracts, agent-orchestrator (read-only verification; write only if a genuine
      recovery is needed).
- [ ] [BACKEND] P1. **Root-cause + fix why `sequential: true` did not gate dispatch order for a queued predecessor.**
      `mtds_available_at_cross_asset_backfill_2026_07_13.md` carries `sequential: true` (added 2026-07-14 for this exact
      bug class) yet task `-006` was dispatched while its direct predecessor `-001` was still `queued`. Read
      `_wire_sequential_prereqs` in `agent-orchestrator/server/regen_backlog_from_plan.py` directly, reproduce against
      the plan's current task rows, and determine the actual cause (candidate hypotheses in the source doc:
      stale-ordinal chaining after checkbox renumbering, a lane-crossing bug when two asset-group sub-sequences
      interleave in one file, or prereqs not re-derived on every regen tick). **Done when**: `quality-gates.sh` green +
      a regression test asserting a `sequential: true` plan never offers a later-in-document unchecked todo while an
      earlier one is still `queued` (not `done`); then re-check the live backlog to confirm `-001` dispatches/completes
      before `-006` is ever offered again. Source:
      `/plans/active/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`. Repo:
      agent-orchestrator.
- [ ] [SCRIPT] P3. **Read-only: verify whether `na-eligibility-auditor.timer`'s most recent scheduled fire(s) since
      2026-07-28 reached `agent_kind=na_eligibility_auditor` lifecycle-complete.** Use the read-only SSM path
      (`/check-agent-orchestrator` or `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh`) against the
      `agents` table. The 2026-07-28 07:00 UTC fire is already known to have hit `Active: failed` on a curl TIMEOUT past
      `--max-time 2400`/`TimeoutStartSec=2450` — record whether a LATER fire (pre- or post- any timeout fix since)
      actually completed end-to-end. Do NOT touch the timeout value itself — that is a separate,
      not-yet-dispatch-eligible judgment call (bump vs. diagnose) left deferred pending more `ScheduledJobRunRow` data
      points (see this plan's Deferred section). **Done when**: the source doc records the fire-completion verdict with
      evidence (dispatch id, timestamps, terminal state). Source:
      `/plans/active/issues/na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md` (its SCRIPT P3 item only — NOT
      its P2 timeout-retune item). Repo: agent-orchestrator (read-only).
- [ ] [INFRA] P3. **Re-mint the stale `~/.orch_token` on host `ip-172-31-5-118`.** The public-URL git-status reporter
      path is failing auth on this host because of an expired/rotated token — re-mint it and confirm `reporter_stale`
      clears within one fleet-git-health tick. This is a distinct credential operation from the already-shipped
      loopback-preference fix (batch1 todo 3), which is unaffected by this. **Done when**: a fresh `~/.orch_token` is
      minted on that host and `/api/fleet/git-health` reports `reporter_stale=false` for it within one 15-min tick.
      Source: `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (its remaining
      INFRA P3 item). Repo: agent-orchestrator (host/credential action, no code change expected).
- [ ] [DEVOPS] P1. **Pin `ORCHESTRATOR_JWT_SECRET_GCS` for `orchestrator.service`.** Create a persisted random-value
      secret object (e.g. `gs://central-element-323112-orchestrator-creds/orchestrator/jwt-secret.txt`, mirroring the
      existing pinned internal secret/key pattern), add `Environment=ORCHESTRATOR_JWT_SECRET_GCS=gs://...` to
      `/etc/systemd/system/orchestrator.service` via `sudoedit`, then
      `systemctl daemon-reload && systemctl restart orchestrator.service`. This closes a fleet-wide ~4.5h-outage root
      cause (an unpinned JWT secret regenerates on every restart, invalidating every slot's cached token at once) that
      has sat unclaimed since its only blocker — an operator-chosen maintenance window — was removed by the 2026-07-28
      CLAUDE.md ruling. **Done when**: a token captured before the restart still validates after it, and `/api/healthz`
      reports healthy post-restart. Source:
      `/plans/active/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (its
      remaining DEVOPS P1 item — the SCRIPT P2 loopback-fix half is already done, see batch1 todo 3). Repo:
      agent-orchestrator (live-host action).
- [ ] [DOCS] P1. [OPERATOR] **Update two codex docs still describing the old always-pin dispatch model.**
      `/codex/12-agent-workflow/work-philosophy.md` and
      `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md` both need to state that
      `_claim_plan_for_slot` pinning is now GATED on `sequential: true` (non-sequential plans fan out to N slots by
      default, matching `task_template.md` §4), citing `agent-orchestrator@867b1731e`. Obtain operator sign-off before
      committing the codex-SSOT edit, per the workspace HARD RULE that a codex change needs sign-off. **Done when**:
      neither doc describes unconditional pinning, and both cite the sequential gate + the shipping sha. Source:
      `/plans/active/issues/dispatch_sequential_gate_fix_2026_07_24.md` (its sole remaining DOCS P1 item — the BACKEND
      P1 live-VM verification half is already done, dated 2026-07-29). Repo: unified-trading-pm (codex).
- [ ] [DATA] P2. **Check + recover-or-dispose `strategy-service`'s stranded wip-preserve ref.** Check whether
      `refs/wip-preserve/cascade-strategy-service-a77eb6d170ca` (2026-07-28, a `staging-lock-check.yml`
      self-hosted-runner-migration commit) was independently superseded by a later rollout in strategy-service; if so,
      the ref is safely superseded and can be deleted (cite the superseding SHA). If not, recover it the same way this
      doc's sibling task recovered `unified-trading-library`'s equivalent ref (fetch the preserved ref,
      cherry-pick/fast-forward it onto current `origin/live-defi-rollout`, ship via quickmerge). **Done when**: the
      ref's disposition (superseded-and-deleted, or recovered-and-shipped) is recorded with evidence in the source doc.
      Source: `/plans/active/issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its `[DATA] P2` item only —
      its two `[SCRIPT] P3` items, a fleet-wide sweep design and a "consider" post-push verification, are held in this
      plan's Deferred section). Repo: strategy-service.

## Deferred — orphaned but not currently dispatch-eligible (design/judgment fork, no evidence-based tiebreaker)

- `/plans/active/issues/ao_context_pct_0_for_monitor_heavy_workers_2026_07_29.md` — its actual user-visible fix (todo 1)
  is sequenced behind todo 2, and todo 2 is a live two-direction design call ("a schema migration ... or ... reuse an
  existing signal ... Prefer (b) if it proves reliable enough") whose own tiebreaker ("reliable enough") is itself a
  judgment call, not a hard criterion. Todo 3 is explicitly "not actionable today" per the doc. Re-triage once the DATA
  todo's direction is operator-ruled or the doc itself commits to one path.
- `/plans/archive/issues/ao_self_pull_stalled_by_untracked_backup_files_2026_07_29.md` — **MOOT, resolved 2026-07-30**
  (`agent-orchestrator@61b7a4f`) before this exclusion rationale could become relevant: built a TIME-gated
  `_track_dirty_tick` Slack alert (mirroring the file's own existing `_track_stale_process` pattern), functionally
  verified end-to-end; doc archived, 0 open todos remain. Nothing left to dispatch here.
- `/plans/active/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` — its substantive
  fix is literally phrased "either (a) ... or (b) ..." with no operator ruling; the doc's own Root Cause section leans
  rhetorically toward (a) but never commits. Its second todo (investigate the `priority_override`-vs-`auto_unpark__`
  durability gap) exists to inform the fork, not to stand alone.
- `/plans/active/issues/mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md` — its sole
  open todo is explicitly an unscoped design question the doc's own author declines to prescribe a mechanism for ("a
  design question for whoever owns backlog-regen, not proposing a specific mechanism here").
- `/plans/active/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md` — its sole open todo
  (hunk-scope `quickmerge.sh --files` staging) proposes two alternative implementations ("`git add -p`" or "a restricted
  `git diff <path> | git apply --cached`") with no tiebreaker, touches the ONE shared shipping path every concurrent
  agent depends on, and the doc's own author explicitly declined to attempt it for that reason.
- `/plans/active/issues/unified_trading_pm_stash_pile_accumulation_2026_07_26.md` — the doc's own todo text
  self-disqualifies: "This is a genuinely open-ended judgment call (per-entry content review), not a bounded fact-check
  — best done interactively, not blind-dispatched," consistent with its `assigned_vm: NA`/ `execution_scope: local-only`
  frontmatter.
- `/plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md` — dual-tagged `[prediction, ao]`
  (genuinely cross-tranche, not a mistag — verified by content read). Its recommended fix is "one or both of" two
  dispatcher-side changes (a shared task-id-keyed checkpoint location, or a dispatcher in-flight check) with no stated
  preference, touching the core backlog dispatcher every fleet task depends on — same blast-radius reasoning as the
  quickmerge.sh item above. Needs a design ruling (which mechanism, or both) before it is batchable.
- `/plans/active/issues/na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md`'s **P2 timeout-retune item** (its
  P3 verify item IS in this batch, above) — worded "bump the timeout (or diagnose why...)" with no evidence-based
  tiebreaker, and explicitly gated on "once a few more real data points land" (a temporal gate on top of the design
  fork).
- `/plans/active/issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md`'s **two `[SCRIPT] P3` items** (its
  `[DATA] P2` item IS in this batch, above): a fleet-wide `refs/wip-preserve/**` sweep offers three alternative
  surfacing mechanisms ("a Slack alert, a dashboard panel, or at minimum a codex-documented manual ... check") without
  committing past the stated floor; a post-push content-verification step is framed as "Consider" (a judgment call on
  whether to build it at all, not a mandate).

## Deferred — already claimed by an active plan outside this tranche (conflict-check caught this)

- `/plans/archive/issues/blank_assigned_vm_dispatch_classification_gap_2026_07_26.md` — its sole open todo (run the
  standard conflict-check against the 30 docs this doc itself flipped `NA→planning` on 2026-07-26, before their content
  is trusted for dispatch) is mechanically bounded and would otherwise qualify, but it is already a live, unchecked
  `[REVIEW] P2` todo inside `/plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` (asset_group:
  `[infrastructure]`, a different tranche), which names this exact doc and folds the identical 30-doc conflict-check in
  verbatim. Drafting a competing todo here would duplicate already-claimed active work — do not action it from this
  plan.

## Deferred — time-gated (re-check after the date passes, not a design question)

- ~~`/plans/active/issues/ao_done_require_origin_not_enforced_2026_07_29.md`~~ — **RESOLVED + archived 2026-07-30, stale
  by the time this plan was drafted**: the operator reviewed the 3-spot-check trend (0/151, 0/52, 0/222 false, all 0.0%)
  directly and explicitly overrode the "wait a few days" gate this note assumed still applied. Flipped + shipped
  `agent-orchestrator@cf7cd35`. Now at `/plans/archive/issues/ao_done_require_origin_not_enforced_2026_07_29.md` —
  nothing left to re-triage here.

## Methodology note — scope of this Phase-1 pass

Of the tranche's 42 current members, this run individually re-verified 22 with fresh evidence (16 via a real per-doc
`Workflow` fan-out — a genuine improvement over the 2026-07-26/07-30 prior runs, both single-threaded with no
Workflow/Agent tool access — plus 6 read directly by the auditing agent itself: the two Orthogonality-check dual-tag
docs now covered above,
`ao_fleet_observability_kpis_2026_07_20.md`/`per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md`/
`agent_orchestrator_qg_red_test_autospawn_magicmock_datetime_2026_07_30.md` — all three found self-covering/healthy, no
action needed — and `ao_open_issues_consolidated_close_out_2026_07_17.md` itself, confirmed still self-covering via its
own ~8 genuinely-open Phase 2/5/8/LAST todos). The remaining ~20 members are the mechanically-flagged "cited somewhere"
set; their coverage was cross-checked against a full read of all 3 covering docs (this session) rather than individually
re-fanned-out, consistent with the candidate-generator script's own stated rationale (a citation inside a real covering
todo is near-certain evidence of prior resolution — full re-audit is low marginal value versus prioritizing the
never-cited set). This is the same scope boundary the 2026-07-26 and 2026-07-30 prior runs of this skill applied.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`,
`/codex/04-architecture/autonomous-recovery-matrix.md` (todo 3),
`/codex/12-agent-workflow/pre-task-plan-conflict-check.md`.

## Progress Log

- **2026-07-30** — Authored by `/ag-closeout-audit ao` (autonomous mode, scheduled dispatch agt-b4e164). Phase 0
  re-derived the tranche's 42 current members (via `generate_ag_closeout_audit_candidates.py`) and confirmed the
  covering-plan set (batch1 + finalize + `ao_open_issues_consolidated_close_out_2026_07_17.md`, the last missed by the
  script's filename-glob but manually confirmed as a genuine covering plan). The Orthogonality HARD CHECK found 2 new
  dual-tagged candidates not caught by the earlier same-day retag pass — both verified genuinely cross-tranche (not
  mistags) by reading their content. Phase 1 ran a real `Workflow` fan-out (16 agents) over every never-cited and
  partial-coverage candidate — a first for this tranche; both prior runs (2026-07-26, 2026-07-30 earlier today) were
  single-threaded with no Workflow/Agent tool access, a coverage caveat both explicitly recorded. One agent's result
  came back corrupted (a placeholder, not real analysis) and was re-run directly by the auditing agent. Phase 3's
  conflict-check ran against both the 3 covering docs and the whole `plans/active` corpus for every candidate before
  drafting; it caught one cross-tranche duplicate claim (held out, see Deferred) and confirmed zero file-collisions
  among the 8 drafted todos (no `sequential` gate needed). Left `status: draft` deliberately — flipping to `active` is
  the operator's call.
