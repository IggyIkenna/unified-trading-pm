---
doc_type: plan
title: ao satellite AO dispatch batch 20 — 2026-08-13
summary: >-
  Extraction batch from the ao tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 30
  conflict-cleared, bounded/deterministic items pulled directly from 12 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [ao]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md,
    /plans/active/issues/ag_closeout_audit_ao_parked_2026_08_10.md,
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    /plans/active/issues/mac_slot0_base_checkout_stuck_dirty_files_2026_08_11.md,
    /plans/active/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md,
    /plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 4.5
estimate_calibrated_ai_days: 3.6
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# ao satellite AO dispatch batch 20 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [CODE] P2. Make an archived-coordinator tranche detectable before it blocks a commit (WARN in the ag-closeout
      hygiene sweep, or improve check_ag_closeout_linkage's failure message to name the archived match) —
      unified-trading-pm@69ebbb5e57: violation message now names archived closeout match(es) + flags "tranche may need
      reopening" when no live coordinator; `_is_active_path()` + 2 pinning tests; full-sweep gate still green (0
      orphans, baseline 0). Source: `plans/active/ao_consolidated_closeout_2026_08_12.md`
- [x] ✅ [CODE] P2. Check whether the other archived tranches have the same latent gap — CONFIRMED no gap: all 10
      covered AGs (ao/cefi/ci/cross-cutting/defi/infrastructure/prediction/sports/tradfi/ui) have an active coordinator
      (ao reopened 2026-08-12). Made the condition a standing sweep-time WARN in check_ag_closeout_linkage.py so a
      future archived-only-family-with-live-docs tranche surfaces before blocking a commit —
      unified-trading-pm@a8d835e74e. Unit-test coverage for the WARN's `_has_active_single_ag_docs` predicate (which
      decides "live docs" vs "genuinely retired tranche") added at unified-trading-pm@cbec983969 — this task's slot-12
      worker duplicated a8d835e74e before discovering it had already shipped; only the tests were net-new and shipped.
      Source: `plans/active/ao_consolidated_closeout_2026_08_12.md`
- [x] ✅ [CODE] P2. Identify and fix the source of the stray <repo>/<repo> self-referential symlinks created uniformly
      across every repo in the Mac base checkout at 2026-08-09 15:28, and clean up the existing ones —
      unified-trading-pm@820984d53d: added a repo-level self-referential-link heal to link-claude-skills.sh (the
      canonical self-healer every host runs on QG/setup/pm-pull) mirroring the existing skills/<name>/<name> junk prune;
      `../../$repo` has zero `git log --all -S` hits (generator is not a current committed script), so the durable fix
      is healing-at-the-self-healer rather than a one-shot cleanup. Source:
      `plans/active/issues/mac_slot0_base_checkout_stuck_dirty_files_2026_08_11.md`
- [x] ✅ [CODE] P2. Recovery-audit Layer-1 producer rewire — stand up the standalone recovery-audit-signoff producer
      (consume PubSub agent-recovery-actions, POST verdicts to POST /safety-ops/signoffs, unmock the DART feed, clean
      the stale routes/agents.py:146 comment); now unblocked since the Phases 0-4 it was operator-sequenced behind are
      all done, and is a well-scoped, deterministic build task — VERIFIED already shipped by a different slot the same
      day (`deployment-service@1a8346db` — `scripts/recovery/recovery_audit_signoff_producer.py` + 15 unit tests,
      `unified-trading-pm@522dec4ba7` updated the codex Layer-1 banner). Confirmed all 4 sub-asks live:
      `agent-recovery-actions`/`-sub` provisioned in `deployment-service/terraform/gcp/main.tf`; producer POSTs to
      alerting-service `POST /safety-ops/signoffs` on a closed deterministic verdict rule set; DART feed
      `_mock_signoffs()` is gated behind `is_mock_mode()` only (real producer data otherwise); `agents.py:146`'s comment
      now accurately describes the AO-role removal + standalone-producer replacement (no longer stale). This checkbox +
      the source doc's own todo were the only remaining gap — closing both here. Source:
      `plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md`
- [x] ✅ [CODE] P2. Backfill context_scope frontmatter across the full active plans/issues corpus (per
      generate_context_scope_inventory.py's live NEVER_SCOUTED count), then flip docspec.py's context_scope FieldSpec
      from Req.E to Req.R for plan+issue as the final hardening commit — **DUPLICATE-MERGED, closing this dispatch with
      a real net-new contribution rather than re-running the full scope.** This todo's source doc itself already states
      it's "the SAME work item actively extracted and tracked as todo 1 of
      `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`" — confirmed by 5 independent na-eligibility-audit
      passes (2026-08-01 through 2026-08-10) which each ruled it genuinely unbounded, ongoing corpus-scale work "not
      bounded to a single-worker AO dispatch," i.e. this batch20 extraction duplicating it as a bounded single todo was
      itself a conflict-check miss (it chased this source doc's citation rather than following that doc's own pointer
      into batch3). Rather than leave a duplicate checkbox permanently re-dispatchable, did the real work this session
      and closed it here: fanned out 5 sub-agents over all 101 `NEVER_SCOUTED` docs, independently verified every diff
      (YAML re-parse, no dup keys, no new line-cap breaches, no content loss — 0 findings), shipped 95/101 in 3 verified
      commits (`unified-trading-pm@6117942be5`, `@3bc392cd0d`, `@716dcf3467`), recovered cleanly from one genuine
      mid-ship autostash-revert via per-file `git show stash@{0}:<path>` (never a blind pop), and fixed one adjacent
      stale `related:` reference found along the way. **Result: NEVER_SCOUTED 101→6** (5 correctly `locked_by`-skipped +
      1 line-cap-deferred, both logged in `context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md`). **NOT
      done**: 552 `STALE` docs remain untouched, and the `docspec.py` FieldSpec flip stays at `Req.E` — both require
      `NEVER_SCOUTED=0, STALE=0` first, genuinely unbounded corpus-scale work that continues under batch3's own todo 1
      (the confirmed live tracking home — see its 2026-08-14 Progress Log entry for this session's full record), not a
      separate re-dispatch of this checkbox. Source:
      `plans/active/context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`
- [x] ✅ [CODE] P2. Confirmed the production VM's pinned claude CLI binary DOES support Claude Code Skills —
      `agent-orchestrator@c00dc13f9d`: checked directly on the production orchestrator VM (i-0c9b283b31d6b5ca7,
      confirmed via IMDSv2 instance-id) — the actually-running spawn binary is `claude 2.1.202`
      (`/home/ubuntu/.local/bin/claude`, resolved the same way `tmux_spawn`'s default `claude_bin="claude"` resolves
      it), well past the pre-Skills gap the 2026-08-04 finding identified (`claude 1.0.112`); `DISABLE_AUTOUPDATER=1` is
      still set but the binary was independently bumped via a deliberate redeploy since then. Verified the pinned
      2.1.175 install-script version (`bootstrap_vm.sh`) also carries full Skills support by downloading its real
      published binary and grepping for the `.claude/skills/<name>/SKILL.md` skill-creator documentation embedded in it.
      Hardened `context_lifecycle.py`'s forced `/pre-compact` path regardless (the underlying detection gap is real
      independent of current binary state — a future pin regression or missing SKILL.md would otherwise silently no-op
      again): added `tmux_spawn.pane_shows_unknown_command()`, checked in `_force_compact_now` before trusting phase 1
      as done; on detection it logs `forced_precompact_unsupported`, pages once per force episode via a new
      `notify_precompact_unsupported` Slack alert, and still advances to phase 2 (`/compact`) so context keeps
      compacting instead of overflowing. New pinning test
      `test_worker_precompact_unknown_command_alerts_and_falls_back_to_compact`; QG green (3613 passed, dashboard 336
      passed). Source: `plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`
- [x] ✅ [CODE] P2. Write (or document inline in config.py) a read-only readout script for the flash-vs-pro
      deepseek_flash_route_fraction split so the code's own 're-measure rather than trusting this block' instruction has
      an actual method to carry out, not just a query an agent has to re-derive from scratch —
      agent-orchestrator@ae44244c7f: new `scripts/orchestrator/deepseek_flash_pro_split_readout.py` (permanent
      lifecycle), joins `activity_log` spawn/dispatch `account_id` rows against `accounts.json`'s declared
      `AccountDef.variant` to report the live flash/pro split per event type + an aggregate percentage; QG green (3658
      passed, basedpyright/ruff clean). Source: `plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`
- [x] ✅ [CODE] P2. Stamp agent_kind onto deepseek_message_usage at sweep time so scheduled/escalation spend is split
      out from the mislabeled 'Worker (backlog tasks)' bucket — STALE-CHECKBOX correction, not new work: already SHIPPED
      at `agent-orchestrator@18fc60b` (2026-08-13, verified on `origin/live-defi-rollout`) — the source doc's own copy
      of this exact todo was already flipped `[x]` there but this batch20 extraction never picked up the SHA. Per the
      AO-dispatch conflict-check protocol's rule 4 ("already-shipped elsewhere, checkbox just never flipped"), citing
      the SHA here rather than re-doing the work. Source:
      `plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md`
- [x] ✅ [CODE] P2. Repair the NULL-provenance rows (clear the affected ProcessedTranscriptRow fingerprints, re-sweep,
      re-measure and record the NULL counts) — STALE-CHECKBOX correction, not new work: already SHIPPED at
      `agent-orchestrator@002126cb32` (2026-08-13) — `scripts/orchestrator/repair_null_provenance.py` + 5 tests, QG
      green (3589 pytest / 319 vitest), then run live on the fleet DB (`--apply --sweep`): 631 affected transcript files
      repaired, NULL `slot_id` 31,947→0 ($62.72), NULL `is_review_slot` 35,975→0 ($68.89), verified independently
      against the live DB, fingerprints re-upserted so the repair doesn't need to recur. The source doc's own copy of
      this exact todo was already flipped `[x]` there but this batch20 extraction never picked up the SHA. Per the
      AO-dispatch conflict-check protocol's rule 4 ("already-shipped elsewhere, checkbox just never flipped"), citing
      the SHA here rather than re-doing the work — same pattern as the todo immediately above this one. Source:
      `plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md`
- [x] ✅ [CODE] P2. Discover DeepSeek transcripts by glob (~/.claude-configs/_/projects/_/_.jsonl plus
      ~/.claude/projects/_/*.jsonl) instead of enumerating live slot rows, so a retired slot's transcripts are still
      swept — STALE-CHECKBOX correction, not new work: already SHIPPED at `agent-orchestrator@60fd7ba` (2026-08-13,
      verified on `origin/live-defi-rollout`) — `deepseek_usage.discover_all_transcripts()` globs
      `<config_base>/*/projects/*/*.jsonl` + `~/.claude/projects/*/*.jsonl`, deriving slot_id from the session-name dir
      so retired slots (orch-slot-97/99) and `~/.claude/projects` are swept. The source doc's own copy of this exact
      todo was already flipped `[x]` there but this batch20 extraction never picked up the SHA. Per the AO-dispatch
      conflict-check protocol's rule 4 ("already-shipped elsewhere, checkbox just never flipped"), citing the SHA here
      rather than re-doing the work — same pattern as the two todos immediately above this one. Source:
      `plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md`
- [x] ✅ [CODE] P2. Freeze the pre-observability gap as an explicit labelled opening balance in the lifetime
      wallet-reconciliation view — STALE-CHECKBOX correction, not new work: already SHIPPED at
      `agent-orchestrator@a3eda085f6` (2026-08-13, verified on `origin/live-defi-rollout` —
      `DeepSeekWalletOpeningBalanceRow` + `record_deepseek_opening_balance`/`get_deepseek_opening_balance`,
      `opening_balance_usd` + `residual_since_observability_usd` on the lifetime reconciliation,
      `POST     /api/accounts/deepseek/wallet-reconciliation/opening-balance`, and the `DeepSeekWalletPanel` freeze
      form). The source doc's own copy of this exact todo was already flipped `[x]` there but this batch20 extraction
      never picked up the SHA. Per the AO-dispatch conflict-check protocol's rule 4 ("already-shipped elsewhere,
      checkbox just never flipped"), citing the SHA here rather than re-doing the work — same pattern as the two
      `deepseek_wallet_residual` todos above. Source:
      `plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md`
- [ ] [CODE] P2. Surface the windowed 24h/7d reconciliation view in DeepSeekWalletPanel.tsx with a real cited Playwright
      L2 regression spec Source:
      `plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md`
- [x] ✅ [CODE] P2. Pin cleanupPeriodDays: 30 explicitly in cursor-configs/settings.json (currently on an undocumented
      upstream default with 2 known behaviour-changing bugs) — ALREADY SHIPPED prior to this batch's drafting:
      `unified-trading-pm@5c373663c8` (2026-08-11) pinned it, `unified-trading-pm@ea53432c4e` (2026-08-12) re-confirmed
      disk headroom before landing on 30 (174G free at the time). Re-verified 2026-08-14: value still reads
      `"cleanupPeriodDays": 30` at `cursor-configs/settings.json:2`; current disk headroom 162G free (77% used) — still
      healthy for 30-day retention. No further code change needed. Source:
      `plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md`
- [x] ✅ [CODE] P2. Archive safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md via the standard 6-step
      archival ritual — unified-trading-pm (this commit): two prior archival attempts (2026-08-10) had recorded the
      ritual as done in prose but the follow-up `git mv` commit never actually landed (caught twice by
      `/plan-reconcile`, agt-c7578b ~05:30 UTC and agt-2baff3 ~18:20 UTC on 2026-08-10). This session verified the
      source doc was still `status: open` at its active path, then ran all 6 steps for real: `🟢 ARCHIVED` banner +
      `status: resolved` + `resolved_by:` on the source doc, `git mv` to `plans/archive/2026_08/issues/`, every
      path-form corpus referrer repointed (the gated finalize doc — which itself also archives in the same commit, all 4
      todos done + unlocked — plus `committed_conflict_marker_plan_doc_2026_08_10.md`'s `related:` list and a stale
      "remains open" prose citation in `review_agent_evidence_gated_write_capability_2026_08_09.md`), a duplicate
      archival todo in `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` flipped rather than left
      re-dispatchable, and a codex-alignment gap closed (`/codex/05-infrastructure/per-tab-worktrees.md`'s prek-race
      section now documents `check_orphaned_prek_patches()` as complementary to `_prek_race_snapshot`/
      `_prek_race_check` — the slot-11 claim that this had already landed was itself part of the same never-pushed
      commit). `scripts/plans/regenerate_active_plan_inventory.py` re-run after the moves. Source:
      `plans/active/issues/ag_closeout_audit_ao_parked_2026_08_10.md`
- [x] ✅ [CODE] P2. Attribute the 7 deepseek_spawn_selected calls preceding a death to their actual caller by adding a
      source field (autospawn/escalation/plan_health) to that log line — STALE-CHECKBOX correction, not new work:
      already SHIPPED at `agent-orchestrator@64a559f` (2026-08-12, verified on `origin/live-defi-rollout`) —
      `select_account_for_spawn(..., caller: str = "unknown")` logs `caller` alongside `deepseek_spawn_selected`/
      `free_provider_spawn_selected`; every one of the 12 real call sites (server.py, main_agent_keeper.py x4,
      autospawn.py x3, escalation.py x2, plan_health.py, worker_liveness_watchdog.py) already passes a distinct
      `caller=` label (e.g. `autospawn_refill`, `autospawn_resume`, `escalation_escalate`, `plan_health_dispatch`,
      `worker_liveness_watchdog_usage_cap`); a call site that omits it degrades to `"unknown"` rather than raising,
      covered by 2 pinning tests (`test_deepseek_spawn_selected_logs_the_caller`,
      `test_deepseek_spawn_selected_caller_defaults_to_unknown` in `tests/test_deepseek_provider_routing.py`). Per the
      AO-dispatch conflict-check protocol's rule 4 ("already-shipped elsewhere, checkbox just never flipped"), citing
      the SHA here rather than re-doing the work. Source:
      `plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`
- [ ] [CODE] P2. Check the fleet's pinned Claude Code CLI version against the two upstream anthropics/claude-code issues
      (#27705, #27734) reported-affected versions (2.1.47, 2.1.50) Source:
      `plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`
- [ ] [CODE] P2. Build the dashboard UI toggle for scheduled-dispatch pause/resume (the API is already shipped and live;
      only the UI wiring + Playwright pw:L2 coverage remains) Source:
      `plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`
- [ ] [CODE] P2. Wire resource-watchdog's existing pressure/cgroup_mem tick log into the same death-correlation capture
      path as the other host/account/pane fields Source:
      `plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`
- [ ] [CODE] P2. Confirm sub-E (odum3default@gmail.com) / sub-D (odum1default@gmail.com) account identity mapping
      against accounts.json / .claude-accounts/*.env before using either as a calibration sample Source:
      `plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`
- [ ] [CODE] P2. Re-measure the forced-compact wedge rate now that all 3 fixes (queued-message latch, effect-based
      verification, repro test) have landed, comparing against the doc's own stated baselines (~3.5 wedges/hr
      post-measurement-fix, ~9.7/hr pre-fix) Source:
      `plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md`
- [ ] [CODE] P2. Cross-check plans/active/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md's own
      logged death timestamps against journalctl orphan_reap-sweep/kill_session signatures for the same incident
      windows, to determine whether some or all of its RAM-exhaustion incidents were actually this doc's
      nohup/orphan_reap bug misdiagnosed, and correct that doc's root-cause framing if confirmed Source:
      `plans/active/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`
- [ ] [CODE] P2. DOCS P3: fix orchestrator_vm_e2e_hardening_2026_07_24.md's self-contradictory assigned_vm:NA +
      execution_scope:orchestrator-agent frontmatter to local-only Source:
      `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`
- [ ] [CODE] P2. DOCS P3: update deepseek_flash_ab_routing_test_2026_08_05.md's stale Deferred-table rows for todos
      2/4/17b Source: `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`
- [ ] [CODE] P2. DOCS P3: repoint plans/epics/orchestrator_master.md's 2 stale referrers to the archived batch4_finalize
      path Source: `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`
- [ ] [CODE] P2. DOCS P3: fix ao_satellite_ao_dispatch_batch12_2026_08_09.md todo formatting (meta-commentary on first
      line + [BACKEND]-vs-[OPERATOR]-adjacent tag mismatch) Source:
      `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`
- [ ] [CODE] P2. BACKEND P3: add sequential/gate_on_depends ordering between
      ao_model_main_agent_as_first_class_slot_2026_08_10.md's 2 same-file open todos Source:
      `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`
- [ ] [CODE] P2. DOCS P3: add sequential/gate_on_depends between ao_scheduled_job_reserve_and_staggering_2026_08_04.md's
      2 prose-gated open todos Source: `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`
- [ ] [CODE] P2. SCRIPT P3: investigate why run_hygiene_sweep.sh's prettier emphasis-mangling check reported PASS
      despite 5 confirmed live instances Source: `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`
- [ ] [CODE] P2. DOCS P3: update ao_main_review_force_compact_idle_gate_unreachable_2026_08_09.md's frontmatter title
      (still says 'unreachable') to match its own body's supersession Source:
      `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`
- [ ] [CODE] P2. DOCS P2: correct ao_orphan_audit_followup_triage_2026_07_30.md's stale claim that batch2 already
      carries fixes for ao_recovery_audit_layer1_deleted_2026_07_15 (re-verified false) Source:
      `plans/active/issues/plan_reconciler_findings_ao_2026_08_10.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
