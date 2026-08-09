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
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, features-service, unified-api-contracts, strategy-service]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-2, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
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
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/12-agent-workflow/work-philosophy.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md,
    agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh,
  ]
---

# AO satellite AO batch 2

> **`status: active`** — dispatched and ingested; 5 of this plan's 9 todos already carry same-day shipped commit
> evidence (e.g. `agent-orchestrator@77769ab`, confirmed an ancestor of `origin/live-defi-rollout`). Authored
> autonomously (scheduled dispatch) and originally shipped `status: draft` pending operator approval; this banner is
> corrected 2026-08-06 to match the frontmatter — it previously described the pre-approval draft state and was never
> updated after the operator flipped the plan to active.

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

- [x] ✅ [BACKEND] P2. **DONE 2026-07-30 (slot-3, backend_engineer) — all 3 sub-items VERIFIED ALREADY SHIPPED, no new
      code needed.** Add a 4th `/done`-gate disposition for a genuinely-open todo blocked on another owner's in-flight
      fix, and fix a recurring self-archival rename-blindness bug. In `agent-orchestrator/server/verify.py`: (1) add
      `_diff_blocks_checkbox` matching a `BLOCKED-ON:<ref>`-style marker (mirroring the existing
      `_diff_cancels_checkbox`/`_diff_defers_checkbox`), accepted via `reason="todo_blocked_pending_other_owner"`; (2)
      extend Mode-2's empty-`pm_shas` fallback to recognize CANCELLED/DEFERRED/BLOCKED markers on the current on-disk
      plan text (mirroring Mode-1's existing L920-932 fallback), not just a raw `[x]` flip; (3) fix the self-archival
      rename-blindness variant — follow git renames in `_pm_log_commits_touching_plan_ref`/`_mode2_disposition` so a
      flip-and-archive-in-one-commit is seen (a recurrence, confirmed twice more, of the already-archived
      `ao_done_gate_checkbox_flip_blind_to_self_archived_plan_ref_2026_07_26.md` bug). **Done when**: `quality-gates.sh`
      green + a regression test per sub-item (blocked-marker acceptance, CANCELLED/DEFERRED/ BLOCKED-on-disk-text
      fallback, rename-followed self-archival detection). Source:
      `/plans/archive/2026_07/issues/ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (3 of
      its 4 todos — the 4th, a codex-doc note, is sequenced behind these and stays with the source doc). Repo:
      agent-orchestrator.

      **Verification (not a re-implementation)**: on picking this up, read `server/verify.py` directly before writing
                                                                          any code and found all 3 sub-items already present on current HEAD:
                                                                          - Sub-items (1) + (2) (the `BLOCKED-ON` disposition + the Mode-1/Mode-2 marker-fallback for an aged-out log
                                                                          window): already shipped by a different worker (slot-7, per the source doc's own Progress Log) at
                                                                          `agent-orchestrator@22a14b1` (`_diff_blocks_checkbox`, `_ADDED_BLOCKED_LINE_RE`,
                                                                          `reason="todo_blocked_pending_other_owner"`) and `agent-orchestrator@e1b30f5` (`_marker_disposition_in_text`,
                                                                          `_mode1_fallback_disposition`/`_mode2_no_recent_commit_disposition`) — both confirmed ancestors of my current
                                                                          HEAD via `git merge-base --is-ancestor`.
                                                                          - Sub-item (3) (self-archival rename-blindness): traced `_same_commit_added_path_matching_basename` +
                                                                          `_flips_at_path_or_rename`/`_cancels_at_path_or_rename`/`_defers_at_path_or_rename` — already wired into BOTH
                                                                          `_mode1_disposition` AND `_mode2_disposition` — to an EARLIER, separate commit,
                                                                          `agent-orchestrator@587c8db` (2026-07-28T20:30:49+01:00, `fix(ao): M3 plan-flip check follows an archival
                                                                          git-mv bundled with the checkbox flip`), also confirmed an ancestor of HEAD. This means the 2 real-world
                                                                          recurrences the source doc's todo 4 cites (2026-07-29, slots 12 and 2) hit an already-shipped-but-likely
                                                                          not-yet-deployed-to-the-live-orchestrator-process version of the fix, not a genuine code gap — the codebase
                                                                          itself was already correct by the time those recurrences were reported.
                                                                          - Regression tests for all 3 sub-items already exist and PASS on HEAD — ran them directly rather than trusting
                                                                          the claim: full `tests/test_done_gate_plan_flip_hard_reject.py` (29/29 passed), specifically confirming
                                                                          `test_done_accepts_when_commit_blocks_todo_pending_other_owner` +
                                                                          `test_done_accepts_cross_repo_when_pm_commit_blocks_todo_pending_other_owner` (sub-item 1),
                                                                          `test_done_accepts_cross_repo_when_todo_blocked_outside_the_log_window` +
                                                                          `test_done_accepts_cross_repo_when_todo_deferred_outside_the_log_window` +
                                                                          `test_done_accepts_cross_repo_when_todo_cancelled_outside_the_log_window` +
                                                                          `test_done_rejects_cross_repo_when_marker_disposition_is_ambiguous` (sub-item 2), and
                                                                          `test_done_accepts_cross_repo_when_checkbox_flip_bundled_with_archival_git_mv` +
                                                                          `test_done_accepts_single_repo_when_checkbox_flip_bundled_with_archival_git_mv` (sub-item 3, both PASSED).
                                                                          - No code changes shipped (there was nothing to change) — per this plan's "don't edit the source issue doc's
                                                                          checkboxes" rule, `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md`'s own todo 4 is
                                                                          left untouched here; the paired finalize plan reconciles this evidence back into it.

- [x] [WORKER] P1. ✅ **MOOT — already fully resolved before this batch was drafted; re-verified 2026-07-30, no action
      needed.** The source doc (`branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md`) was already
      `status: resolved` + ARCHIVED the same day this batch2 audit ran, by an earlier "bounded recovery sweep, infra
      role" pass that already recorded the exact disposition this todo asks for, for all 4 items — this batch2 audit's
      Phase-1 pass apparently re-derived the same finding independently without noticing the source doc had already
      closed it. Independently re-verified all 4 today via `git merge-base --is-ancestor` + content-diff against current
      `origin/live-defi-rollout` (unified-trading-system-repos/.tabs/8): (1) features-service `207afd62` — orphan
      confirmed NOT on origin; `a90256f5` confirmed ON origin ("feat(sports): always write stable derived_features
      residue census manifest"). (2) features-service `d1c1ad8a` — orphan confirmed NOT on origin; `a9429cba` confirmed
      ON origin, `accepted_quotes_for_venue` symbol live at `mvp_universe_filter.py:48,64,71,97`. (3)
      unified-api-contracts `724bd9be` — orphan confirmed NOT on origin; `698b5b6f` confirmed ON origin,
      `git diff 724bd9be 698b5b6f --stat` is EMPTY (byte-identical). (4) agent-orchestrator `559452e` — orphan confirmed
      NOT on origin; `09cda29` confirmed ON origin, route live at `server/routes/backlog.py:391` +
      `tests/test_backlog_reconcile_brief.py` present. No genuine recovery needed for any of the 4 (matches the
      already-recorded verdict); no code changes made in any of the 3 verification-only repos. Source doc's own
      checkboxes/dispositions left untouched (already correct, doc archived) per this plan's "don't edit the source
      doc's checkboxes" rule. Repos: features-service, unified-api-contracts, agent-orchestrator (read-only, confirmed
      no write needed), unified-trading-pm (this flip).
- [x] [BACKEND] P1. ✅ **Root-caused + fixed — `agent-orchestrator@77769ab`.** Actual cause: NONE of the 3 candidate
      hypotheses in the source doc as literally stated — the real mechanism is call-ORDER, not stale ordinals or lane
      interleaving per se. `_wire_sequential_prereqs` (server/regen_backlog_from_plan.py) runs BEFORE `_prune_stale` in
      `regen()`'s pipeline. When a same-plan todo's TEXT changes mid-tick (a reword/retag — exactly what happened to
      both `-001`'s and `-006`'s todo text on 2026-07-28, "retagged... same ruling"), the OLD row for the pre-edit brief
      is still sitting in `backlog.tasks` at chain-wiring time (an orphan about to be pruned, but not yet), carrying a
      STALE `plan_order` from a prior tick that can tie/interleave with the freshly (re)computed `(plan_order, id)`
      values for the plan's live todos — sorting the stale row into the chain and hijacking the immediate-predecessor
      slot the fresh row should have gotten. Once the orphan is pruned moments later (same tick or the next), an id
      absent from both DB and backlog reads as satisfied by design, so the hijacked task can dispatch with its TRUE
      predecessor still queued. Reproduced via a self-contained regen() test (reword a mid-sequential-plan todo, assert
      the reworded row still chains onto its true document-order predecessor, not the stale orphan) — FAILS on pre-fix
      code (`['p-002'] == ['p-001']` mismatch), PASSES post-fix. **Fix**: track each tick's live (non-orphan) task ids
      per plan during the scan loop (`current_task_ids_by_plan`) and restrict `_wire_sequential_prereqs`'s chain WALK to
      those live ids only, while still classifying same-plan-vs-cross-plan links from the FULL per-plan task set (so a
      genuinely stale same-plan link is still recognised + stripped by the non-sequential branch) —
      `_wire_sequential_prereqs` signature gained an optional `current_task_ids_by_plan: dict[str, set[str]] | None`
      param, defaulting to the old (unfiltered) behavior when omitted. **Gate met**: new regression test
      `test_sequential_reword_mid_flight_does_not_corrupt_chain` (`tests/test_regen_reconcile.py`) fails pre-fix, passes
      post-fix; full `tests/test_regen_reconcile.py` (17/17), the broader regen-touching suite (287/287 across
      `test_backlog_reconcile_brief.py`, `test_done_gate_plan_flip_hard_reject.py`, `test_e2e_findings_remediation.py`,
      `test_failover_allowed.py`, `test_operator_gated_dispatch_ruling.py`, `test_regen_backlog_from_plan.py`,
      `test_regen_effort_field.py`, `test_role_registry.py`, `test_skip_endpoint_cooldown_and_park.py`,
      `test_skip_stale_marker_orphan.py`), and the full repo `quality-gates.sh` (2077 passed, 2 skipped) all green.
      Shipped via quickmerge, landed on `live-defi-rollout`. **Live-backlog re-check deliberately NOT done from this
      todo** — the source issue doc already tracks it as its own separate `[VERIFY] P2` todo, explicitly gated on the
      fix reaching the live orchestrator VM through the normal deploy pipeline (this fix hasn't been deployed there yet
      as of this commit; forcing a live orchestrator restart mid-fleet-operation to satisfy it here would be out of this
      todo's scope). `mtds_available_at_cross_asset_backfill_2026_07_13.md` carries `sequential: true` (added 2026-07-14
      for this exact bug class) yet task `-006` was dispatched while its direct predecessor `-001` was still `queued`.
      Source: `/plans/archive/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`. Repo:
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
      `/plans/archive/issues/na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md` (its SCRIPT P3 item only —
      NOT its P2 timeout-retune item). Repo: agent-orchestrator (read-only). **➡️ EXTRACTED 2026-08-09 to
      `ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1 — do NOT action here.**
- [x] [INFRA] P3. ✅ **MOOT — verified resolved 2026-08-06, no action needed (na-eligibility-audit round9, 2026-08-09).**
      Re-mint the stale `~/.orch_token` on host `ip-172-31-5-118`. Source doc
      (`git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`) itself already closed this exact item as
      MOOT on 2026-08-06: the loopback-preference fix (batch1 todo 3, shipped 2026-07-26) removed this host's
      public-URL-token dependency entirely, measured live from `hk` at the time —
      `/api/fleet/git-health` host `ip-172-31-5-118` showed 17 slots, `reporter_stale` **0**. No re-mint was or is
      needed for this host. This copy of the todo went stale when the source doc resolved it via a different fix
      (loopback, not re-mint) rather than the credential op this copy describes — closing on the source doc's own
      evidence rather than leaving a stopgap open against a host that no longer needs it. Source:
      `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (its own MOOT-verified
      entry, 2026-08-06). Repo: agent-orchestrator.
- [x] [DEVOPS] P1. ✅ **DONE 2026-07-30 — already resolved, don't dispatch.** The `.env.local`-based literal
      `ORCHESTRATOR_JWT_SECRET` was found already durably pinned (verified: a token survives a real restart), and the
      systemd-unit-level `ORCHESTRATOR_JWT_SECRET_GCS` drop-in this todo describes was separately completed the same day
      (`/etc/systemd/system/orchestrator.service.d/jwt-secret-gcs.conf`, verified via a genuine `systemctl     restart`
      — token survived). Full evidence in the source doc's own "Remaining work" section (both todos) — now archived at
      `/plans/archive/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md`. Repo:
      agent-orchestrator (no code change needed for this todo specifically).
- [x] ✅ [DOCS] P1. **DUPLICATE OF ALREADY-SHIPPED WORK — stale todo, no action needed.** Update two codex docs still
      describing the old always-pin dispatch model. `/codex/12-agent-workflow/work-philosophy.md` and
      `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md` both need to state that
      `_claim_plan_for_slot` pinning is now GATED on `sequential: true` (non-sequential plans fan out to N slots by
      default, matching `task_template.md` §4), citing `agent-orchestrator@867b1731e`. **Operator ruling 2026-08-08**
      (interactive Q&A, item 1 of the ao round-5 apply digest): "Approve, ship as drafted" — but on locating the actual
      source doc (`/plans/archive/issues/dispatch_sequential_gate_fix_2026_07_24.md`), this exact edit was already
      operator-approved and shipped 2 days earlier, 2026-08-06 (during `/plan-reconcile ao`, "Fix both codex docs now")
      as `unified-trading-pm@41a51d9ff`. Re-verified live 2026-08-08: both
      `/codex/12-agent-workflow/work-philosophy.md:89-92` and
      `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md:167-171` state the gate-on-`sequential:true`
      behavior and cite `agent-orchestrator@867b1731e`; neither describes unconditional pinning. This batch2 todo was a
      second, unresolved copy of the same source-doc citation that lagged the source doc's own closure — the source doc
      itself has been `status: resolved` + archived since 2026-08-06. No further edit needed; the operator's 2026-08-08
      approval is honored by confirming the already-shipped content matches what was approved. **Done when**: neither
      doc describes unconditional pinning, and both cite the sequential gate + the shipping sha — CONFIRMED. Source:
      `/plans/archive/issues/dispatch_sequential_gate_fix_2026_07_24.md` (its sole remaining DOCS P1 item — the BACKEND
      P1 live-VM verification half is already done, dated 2026-07-29). Repo: unified-trading-pm (codex).
- [ ] [DATA] P2. **Check + recover-or-dispose `strategy-service`'s stranded wip-preserve ref.** Check whether
      `refs/wip-preserve/cascade-strategy-service-a77eb6d170ca` (2026-07-28, a `staging-lock-check.yml`
      self-hosted-runner-migration commit) was independently superseded by a later rollout in strategy-service; if so,
      the ref is safely superseded and can be deleted (cite the superseding SHA). If not, recover it the same way this
      doc's sibling task recovered `unified-trading-library`'s equivalent ref (fetch the preserved ref,
      cherry-pick/fast-forward it onto current `origin/live-defi-rollout`, ship via quickmerge). **Done when**: the
      ref's disposition (superseded-and-deleted, or recovered-and-shipped) is recorded with evidence in the source doc.
      **➡️ EXTRACTED 2026-08-09 to `ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 2 — do NOT action here.**
      Source: `/plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its `[DATA] P2` item only —
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
- `/plans/archive/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` — its substantive
  fix is literally phrased "either (a) ... or (b) ..." with no operator ruling; the doc's own Root Cause section leans
  rhetorically toward (a) but never commits. Its second todo (investigate the `priority_override`-vs-`auto_unpark__`
  durability gap) exists to inform the fork, not to stand alone.
- `/plans/archive/issues/mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md` — its sole
  open todo is explicitly an unscoped design question the doc's own author declines to prescribe a mechanism for ("a
  design question for whoever owns backlog-regen, not proposing a specific mechanism here").
- `/plans/archive/2026_08/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md` — its sole open
  todo (hunk-scope `quickmerge.sh --files` staging) proposes two alternative implementations ("`git add -p`" or "a
  restricted `git diff <path> | git apply --cached`") with no tiebreaker, touches the ONE shared shipping path every
  concurrent agent depends on, and the doc's own author explicitly declined to attempt it for that reason.
- `/plans/active/issues/unified_trading_pm_stash_pile_accumulation_2026_07_26.md` — the doc's own todo text
  self-disqualifies: "This is a genuinely open-ended judgment call (per-entry content review), not a bounded fact-check
  — best done interactively, not blind-dispatched," consistent with its `assigned_vm: NA`/ `execution_scope: local-only`
  frontmatter.
- `/plans/archive/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md` — dual-tagged `[prediction, ao]`
  (genuinely cross-tranche, not a mistag — verified by content read). Its recommended fix is "one or both of" two
  dispatcher-side changes (a shared task-id-keyed checkpoint location, or a dispatcher in-flight check) with no stated
  preference, touching the core backlog dispatcher every fleet task depends on — same blast-radius reasoning as the
  quickmerge.sh item above. Needs a design ruling (which mechanism, or both) before it is batchable.
- `/plans/archive/issues/na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md`'s **P2 timeout-retune item** (its
  P3 verify item IS in this batch, above) — worded "bump the timeout (or diagnose why...)" with no evidence-based
  tiebreaker, and explicitly gated on "once a few more real data points land" (a temporal gate on top of the design
  fork).
- `/plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md`'s **two `[SCRIPT] P3` items** (its
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

- ~~`/plans/archive/issues/ao_done_require_origin_not_enforced_2026_07_29.md`~~ — **RESOLVED + archived 2026-07-30,
  stale by the time this plan was drafted**: the operator reviewed the 3-spot-check trend (0/151, 0/52, 0/222 false, all
  0.0%) directly and explicitly overrode the "wait a few days" gate this note assumed still applied. Flipped + shipped
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
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — this doc
  carries the same NA/local-only satellite-batch convention as batch1/batch3/batch4 (all 4-for-4 in this tranche, not a
  one-off default; `ao_open_issues_consolidated_close_out_2026_07_17.md:136` records it as established fact). Of the 4
  open items, 3 require the same specialized SSM/host/credential access this tranche's work consistently uses
  interactive sessions for, and 1 (`[DOCS] P1`) is explicitly `[OPERATOR]`-tagged. **Worth the operator's attention as a
  possible systemic skill-convention drift** (the `ag-closeout-audit` SKILL.md's own authoring convention for
  `_satellite_ao_dispatch_batch{N}_` docs states `assigned_vm: planning` — no explicit ruling/citation found in any of
  the 4 `ao` batch docs explaining the deviation) — not treated as an audit-scope oversight this run given its 100%
  consistency, but a one-time explicit ruling would save future audits from re-deriving this reasoning.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries, trimmed from 8) — re-derived off the 4 genuinely
  still-open todos (na-timer check, orch_token re-mint, codex-doc update, wip-preserve ref) rather than the whole
  original batch's now-mostly-done spread; dispatch-batch coordinator, no source path.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — swapped the generic single-vm-architecture codex
  pointer for `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh`, the tool the still-open SCRIPT P3
  todo directly names; not a pure coordinator doc — the plan's largest (now-done) todo shipped real code
  (`server/verify.py` + several test files), so a source path belongs here despite the `_satellite_ao_dispatch_batchN_`
  naming pattern.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. Of the 4 open items, 3 need the specialized SSM/host/credential access this tranche consistently
  uses interactive sessions for, and the 4th (`[DOCS] P1`) is explicitly `[OPERATOR]`-tagged.
- **2026-08-08 (ao round-5 operator Q&A apply session)**: operator answered "Approve, ship as drafted" on this doc's
  `[DOCS] P1` codex-edit todo — but the edit was already shipped 2026-08-06 (`unified-trading-pm@41a51d9ff`) against the
  actual source doc (`dispatch_sequential_gate_fix_2026_07_24.md`, archived same day); this batch2 copy of the citation
  had simply gone stale. Re-verified both codex docs live and flipped the checkbox. 3 items remain open (na- timer
  verification, orch_token re-mint, wip-preserve ref) — none in this session's scope.
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA-STALE, citation-closed — the `orch_token` re-mint item was
  found already resolved on the SOURCE doc (`git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`,
  2026-08-06 MOOT verdict) by a different fix (loopback preference) than the one this copy describes (re-mint);
  flipped `[x]` with the source doc's own evidence cited, not a new dispatch. The na-timer verification and
  wip-preserve-ref items were already `EXTRACTED 2026-08-09` to `ao_satellite_ao_dispatch_batch10_2026_08_09.md` by a
  concurrent same-day pass — 0 items remain un-actioned on this doc. Whole-doc RECLASSIFY not applicable (this doc is
  itself a dispatch-coordination artifact, not a source doc).
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **2**, matching. Both visible open lines are citation-pointers already correctly marked
  `➡️ EXTRACTED 2026-08-09 to ao_satellite_ao_dispatch_batch10_2026_08_09.md` (verified live: that extraction target
  exists) — per round9's own "0 items remain un-actioned on this doc" verdict, real remaining work here is zero. This
  is itself a dispatch-coordination satellite artifact (not a source doc), so whole-doc RECLASSIFY doesn't apply; stays
  `assigned_vm: NA` per the tranche's own 100%-consistent established convention (batch1/3/4 all NA too).
