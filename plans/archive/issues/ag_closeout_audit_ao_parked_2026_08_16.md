---
doc_type: issue
title: "/ag-closeout-audit ao — 2026-08-16 parked findings (38 non-batchable orphaned docs)"
summary: >-
  Durable home for the `/ag-closeout-audit ao` run's (dispatch agt-1628ee, 2026-08-16) genuinely-orphaned-but-NOT-
  batchable findings — every doc that survived Phase 1 classification as orphaned but failed Phase 3's dispatch-scope
  eligibility test (operator-gated, design fork, time-gated, too-large/risky, or genuinely human-only), so nothing
  became a batch22 todo. 38 entries, categorized. Two items are flagged for direct operator attention at the top
  (an active P0 incident, and a high-value item deliberately excluded from casual batch-extraction). This is a
  Phase-0-2-adjacent parked doc per the skill's own rule that every genuine finding gets a durable home in the SAME
  run that found it, whichever phase the run stops at.
status: superseded
superseded_by: ag_closeout_audit_ao_parked_2026_08_21
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ag-closeout-audit, ao, parked-findings, orphan-audit, non-batchable]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/ao_satellite_ao_dispatch_batch22_2026_08_16.md,
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-16"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
assigned_role: infra
drift_direction: none
resolved_by:
locked_by:
depends_on: []
source: >-
  /ag-closeout-audit ao, dispatch agt-1628ee, slot 15, 2026-08-16. Phase 1 classified 59 candidate docs (9-group
  Workflow fan-out); 12 archivable_now flipped+archived directly; 6 fed batch22 (drafted, status:draft); 1
  exclude_cross_cutting; the 36 below are the remainder — genuinely orphaned, genuinely not AO-eligible right now.
context_scope: [/cursor-configs/skills/ag-closeout-audit/SKILL.md, /plans/active/ao_consolidated_closeout_2026_08_12.md, /plans/active/ao_satellite_ao_dispatch_batch22_2026_08_16.md, /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md]
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2) — SUPERSEDED** by the 2026-08-21 re-run of the same audit
> (`ag_closeout_audit_ao_parked_2026_08_21.md`, active). 0 open todos, no lock. Kept as a historical
> audit-run record.
# `/ag-closeout-audit ao` 2026-08-16 — parked findings

## Needs direct operator attention (surfaced here, not silently filed)

- **RESOLVED since filing (corrected 2026-08-18, `/plan-reconcile` ao tranche)** — was: "ACTIVE P0 INCIDENT — fleet
  paused at reduced capacity." `ao_fleet_regression_triad_2026_08_16.md` is now `status: resolved` and archived
  (`/plans/archive/issues/ao_fleet_regression_triad_2026_08_16.md`) — Finding 2 (agents dying mid-task) was
  root-caused (`context_lifecycle.py::_tick_target`'s boundary-confirmed compaction path never wrote the corrected
  pct back, re-arming a forced compact every ~3.5min indefinitely) and fixed, `resolved_by: agent-orchestrator@
  9ba4391e60` (fix) + `@1b2dddffc9` (UI). Fleet resumed to full capacity (0 paused) — confirmed via
  `/plans/active/ao_open_work_consolidated_tracker_2026_08_14.md` Track 1's own evidence entry for the same commit.
  Findings 1 (scheduled-reserve slot-set drift) and 3 (human-fleet dashboard misrepresentation) are also both
  resolved per the same source doc's `resolved_by:` (`agent-orchestrator@54f8fc5811` and `@1b2dddffc9`
  respectively). This finding's parked classification (too-large-or-risky, needs a dedicated session) was correct
  AT FILING TIME — the incident has since been fully resolved by a dedicated session, exactly as recommended. No
  remaining operator action on this item.
- **`orchestrator_vm_e2e_hardening_2026_07_24.md`'s dirty-worktree-policy deliverables** — design fully resolved
  (operator discussion, 2026-08-15), the tracker itself calls this "highest-value remaining bounded work," and it is
  technically bounded (2 deliverables: a worker prompt template + dispatch hook for the resolved 3-step flow; a
  bounded-retention sweep for 47+ unpruned `wip-preserve/*`/autostash refs already observed live). Deliberately
  EXCLUDED from batch22 because it rewrites the worker prompt template + AO dispatch hook every slot spawn's first
  message reads from — this workspace's standing pattern (the 2026-07-31 operator directive, invoked repeatedly
  across this tranche's own audit history) routes exactly this class of fleet-wide boot/dispatch-critical-path text
  change to a deliberate, human-attended session. Recommend a dedicated session rather than a future casual
  batch-extraction.

## Ledger

`parked_findings = 38` (this section's category lists below: 12 operator-gated + 13 design-fork + 4 time/external-
gated + 5 too-large-or-risky + 4 human-only); `entries_actually_written = 38`. Balanced.

## Category: operator-gated (13)

Undecided design/judgment call, an explicit sign-off requirement, or a credential/host-level action only a human can
take. Not re-triageable by a future audit re-run — needs an actual operator ruling or action.

- `ao_human_fleet_integration_2026_08_15.md` — Harsh's entire Phase 4 (mint JWT, register, run one real task) is a
  physical impossibility from any session; deferred to Harsh directly.
- `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` — configure `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in
  the planning VM's root `.env.local`, a host-level secret action prepared 2026-08-08 but not yet confirmed executed.
- `autospawn_fleet_cap_headroom_throttling_routine_sla_miss_2026_08_09.md` — capacity/tuning tradeoff decision
  (raise `ORCHESTRATOR_FLEET_WORKER_CAP` / design priority-aware headroom / accept+document), explicitly framed by
  its own text as not a bounded worker todo.
- `citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md` — operator unpark decision (an
  interactive session cannot call the unpark API itself, per the doc's own note).
- `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` — investigate the sub-d 1047x outlier (needs live
  account-console access) + keep sub-e excluded pending its own clean weekly reset.
- `defi_compute_gcp_migration_009_repeat_wedge_parked_2026_08_08.md` — operator unpark decision, explicitly still
  "NOT YET, stays parked" per a 2026-08-16 `/plan-reconcile` re-check.
- `fleet_venv_drift_after_pull_no_resync_2026_08_11.md` — RESOLVED + archived 2026-08-18 (`/plan-reconcile ao`):
  the two shared-clone git conflicts were live-verified clean (both checkouts, no `UU` state, no in-progress
  rebase/merge), 0/9 open, moved to `plans/archive/2026_08/issues/`.
- `fleet_wide_deepseek_crash_loop_undetected_2026_08_11.md` — operator decision on reverting the
  `tuning.deepseek_opus_emergency_fallback` flag (the P1 half — root-causing the tmux-death mechanism — needs
  external DeepSeek engagement, see the time/external-gated category below).
- `ao_human_claim_reserved_slot_bypass_2026_08_16.md` — the manual-recovery-decision half only (whether the
  currently-live wedged review slot needs a kill+respawn); the hardening-gap half already fed batch22.
- `operator_ruling_record_ao_round5_apply_session_2026_08_08.md` — confirm 6 transcribed operator rulings are
  accurate; operator-only by construction.
- `unified_trading_pm_stash_pile_accumulation_2026_07_26.md` — discard 5 of 18 provably-zero-loss stash entries;
  categorically blocked for an agent by the destructive-command guardrail hook, needs a human to run the commands.
- `deepseek_claude_blended_provider_routing_2026_07_28.md` — the review/pilot-comparison/GLM-followup items are
  explicitly "operator is handling elsewhere, not via this tracker" per operator direction 2026-08-14 (the one
  mechanical sub-item, GSM re-sourcing, is already done and covered by `batch14_finalize`'s own reconcile todo — not
  duplicated here).

## Category: design fork (13)

A genuine, undecided two-option-or-more choice with no evidence-based tiebreaker. Re-triageable only once an
operator rules between the options — until then, re-surfacing this in a future audit adds nothing new.

- `ao_backlog_no_collision_gate_long_running_driver_todos_2026_08_02.md` — self-expiring dispatch-cooldown design +
  surfacing prior Progress-Log status at `/boot`.
- `ao_dispatch_ignores_same_doc_operator_predecessor_todo_2026_08_08.md` — whether to encode same-doc
  OPERATOR-then-INFRA todo ordering as a machine-enforced convention.
- `ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md` — an unscoped soft turn-count circuit breaker
  (no committed threshold or mechanism).
- `backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md` — whether the park mechanism should alert on a
  parked task's id silently changing across a regen tick.
- `backlog_regen_reverted_p1_2_park_2026_08_01.md` — a standing hygiene assertion for parked-task drift; repo and
  mechanism both undecided.
- `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` — build a same-file/same-plan prereqs
  mechanism (or a narrower non-dispatchable marker); explicitly "not decidable unilaterally by a single audit pass."
- `context_scope_sufficiency_measurement_2026_08_08.md` — genuinely open-ended; resolves via `/plan-brainstorm`
  before any implementation todo exists.
- `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` — whether the dashboard should gate CI on
  `prettier --check` at all; a policy call, not a bug fix.
- `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md` — the actual root-cause fix approach (widen the
  `AgentRow` status filter vs. fix the registration path) is an open design call per its own 2026-08-10 audit note.
- `todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md` — extending
  `check_todo_regression.sh`'s cross-file exemption; self-flagged as needing "design judgment on the cross-file
  correlation logic, not a mechanical one-liner."
- `dashboard_deepseek_e2e_specs_red_stale_fixture_expectations_2026_08_08.md` — investigate fixture-drift-vs-real-
  regression, then decide whether to gate the dashboard Playwright suite in CI; the gating half is a policy call.
- `ao_tranche_full_content_audit_findings_2026_07_31.md` — standing opportunistic-retag policy; intentionally never
  to be batched by its own explicit design ("Do NOT open a doc solely to retag it, and do NOT batch these").
- `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` — the readiness-probe half shipped and was flipped
  directly this run (`agent-orchestrator@3b4a3299`, verified); the remaining pool right-sizing item (lower
  `pool_timeout` vs. batch/serialise per-slot git-status writes) is confirmed "a real judgment call between two
  designs, not a bounded task" per the tracker's own 2026-08-15 reconciliation.

## Category: time/external-gated (4)

Depends on elapsed real time, an external party's response, or a condition this run confirmed is still unmet.
Re-surfacing every run finds the same "not yet" until the actual gate clears.

- `fleet_wide_deepseek_crash_loop_undetected_2026_08_11.md` — P1 half: confirm the DeepSeek tmux-pane-death
  mechanism, needs DeepSeek-side support engagement or an isolated client-side repro.
- `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` — gated on an explicit 2026-08-02
  operator ruling that `assigned_vm` stays NA until condition `mdps-e2e-shared-host-teardown-fixed` also closes;
  still unmet as of 2026-08-15's last reproduction.
- `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` — the re-run-after-sub-f's-window-reset half is a
  literal clock-gate (also listed above for its operator-gated half).
- `ao_human_fleet_integration_2026_08_15.md` — Ikenna's real task-claim/done cycle is currently blocked because
  every one of the 314 live queued backlog tasks carries a `blocked_reason`; will self-clear as the backlog moves,
  not a standing gate to escalate (also listed above for Harsh's genuinely-gated half).

## Category: too-large-or-risky-for-a-batch-todo (5)

Live, fast-moving, multi-phase investigation docs where folding even a clean-looking sub-item into a batch risks
colliding with the doc's own in-flight state. Needs a dedicated triage/design pass, not a `batchN` slot.

- `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` — 11 open todos on a large, extensively-worked live
  investigation doc, including a genuinely unexplained P0 death (#2, 14:30:28) and several smaller hardening/tooling
  follow-ups tangled into the same active document; needs a dedicated pass reading the whole doc fresh, not
  piecemeal extraction.
- `grok_gemini_translation_proxy_2026_08_14.md` — the mandatory `tool_use`/`tool_result` translation smoke-test
  gate blocks any live fleet traffic on this provider; real, substantial engineering (not yet scoped into
  bounded sub-items) rather than a batch-sized todo.
- `kimi_gemma_provider_onboarding_2026_08_16.md` — a whole new provider-onboarding effort in progress (wallet
  poller, live harness test, billing-schema cross-link, waitlist tracking) with several substantial, only
  loosely-scoped pieces; needs its own dedicated scoping pass before any one piece is batch-sized.
- `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md` — Track B: 7 separate per-scheduled-job
  reliability/escalation-health audits (ag-closeout-auditor, cefi-mtds-smoke, cefi-reconciliation, context-scout,
  docs-reconcile, escalation-queue-reconciler, na-eligibility-auditor) + 1 synthesis todo, each requiring reading
  that job's real dispatch/escalation history and judging reliability — genuine per-job human/audit judgment, not a
  mechanical batch todo; better run as its own dedicated audit pass (mirrors Track A's own now-closed 25-PR sweep in
  scale) than fragmented across batch todos.
- `plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md` — root-causing 2 live AO HTTP-integration gaps
  (`/api/plan-health/result` auth rejection; blocked-question answer-retrieval, with 2 live reproductions already
  recorded) is open-ended investigation into unknown API-layer failure modes, not yet scoped to a bounded fix; the
  3rd item (audit historical runs for silently-missed answers) depends on the first two being understood. Re-scope
  once either root cause is identified.

## Category: genuinely human-only / self-declared out-of-AO-scope (4)

The source doc's own text (or a standing operator ruling) declares this is not AO-dispatch work, or it is a
deliberate observation/burn-in gate with no worker-executable done-state.

- `multi_provider_context_billing_reconciliation_2026_08_16.md` — explicitly: "Not building this as an AO-dispatched
  background-worker plan" (Non-goals section, verbatim).
- `review_agent_evidence_gated_write_capability_2026_08_09.md` — todo 7 is a deliberate operator-set burn-in
  observation gate ("no archival needed yet... leave active for a burn-in period") — by design nothing should track
  this as dispatched work.
- `codex_luna_flex_bridge_2026_08_14.md` — real remaining engineering work, but explicitly excluded from AO-dispatch
  by operator direction 2026-08-14 ("operator is handling both elsewhere, not via this tracker").
- `ao_residuals_after_dispatch_hardening_2026_07_17.md` — 2 of 4 items already done (checkbox-stale, not tracked as
  new work); the 2 genuinely remaining (backlog-relations dashboard UI view, `l2_book` retest) are real feature work
  and a gate blocked on an unrelated doc's own NA hold respectively — neither is a small enough bounded item for this
  batch round; re-assess next run.

## Notes

- Two docs (`ao_residuals_after_dispatch_hardening_2026_07_17.md`, `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`)
  lost their `check_ag_closeout_linkage.py` reachability path when this run archived
  `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md` (their only prior mention). Both are now
  linked directly from `ao_consolidated_closeout_2026_08_12.md`'s own body so this doesn't recur on the next doc that
  happens to reference them going away.
- Every doc named above was read in full (not classified from checkbox count alone) by this run's Phase 1 Workflow
  (9 agents, 59 docs) before being marked orphaned; see the run's own chat report for the per-doc verdict + evidence
  citation this parked doc doesn't repeat.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:21df501b3422cfc6]: KEEP-NA, valid — standing parking register for /ag-closeout-audit ao's non-batchable orphaned findings; zero checkbox todos by design (its content IS the tracking mechanism).

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:e4c6db9037c0bd45]: KEEP-NA, valid — standing parking register for /ag-closeout-audit ao's 36 non-batchable orphaned findings; zero checkboxes by design (the doc's content IS the tracking mechanism). Reconfirms the 2026-08-17 na-eligibility-audit verdict; the 2 'needs direct operator attention' items are correctly marked resolved-since-filing within the doc's own text.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
