---
doc_type: plan
title: AO satellite AO batch 12 — 11 bounded items extracted from 4 non-covered `ao`-tranche docs (orchestrator_master)
summary: >-
  TWELFTH AO-dispatch batch for the `ao` topic tranche — produced by a fresh `/ag-closeout-audit ao` Phase 1 run
  (2026-08-09, dispatch `agt-41d860`) that classified 36 `assigned_vm: NA` `ao`-tagged candidate docs not yet cited by
  any of batch1-11 against the full covering-plan family. 34 of 36 came back `orphaned_never_touched` (no active plan
  claims their remaining work); of those, 5 docs carried genuinely bounded, worker-determinable items with no remaining
  judgment call. This batch extracts the 11 such items whose source doc's `parent_epic` is `orchestrator_master` (the
  AO-service-itself epic) — the 12th item, from a doc under `agent_operating_framework_master` (doc/plan-hygiene
  tooling), is split into the sibling `ao_satellite_ao_dispatch_batch13_2026_08_09.md` per the established
  `parent_epic`-is-the-grouping-axis convention (batch11 precedent). Conflict-check: the Phase 1 classification agents
  already grepped all 24 prior covering plans (consolidated-closeout + batch1-11 + finalizes, both active and archived)
  per-item before flagging any item `ao_eligible_candidate_items` — zero hits for 4 of the 5 source docs; the 5th
  (`fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md`) had 2 unrelated corpus-wide citations (a
  `ci`-tranche metadata-retag list, and an independently-resolved provenance-marker doc that fixed a different
  subsystem) neither of which claims this batch's extracted item. All 11 todos are file-disjoint (verified during
  drafting) so this plan needs no `sequential` gate.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-12, satellite-docs, satellite-extraction]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch12_finalize_2026_08_09.md,
    /plans/active/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
    /plans/archive/issues/fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    /plans/active/ao_satellite_ao_dispatch_batch13_2026_08_09.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
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
    /plans/active/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
    /plans/archive/issues/fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/context_probe.py,
  ]
source: >-
  `/ag-closeout-audit ao` Phase 1 run, 2026-08-09 (autonomous, scheduled dispatch `agt-41d860`, slot 10) — a Workflow
  fan-out (36 agents) classifying every `ao`-tagged `assigned_vm: NA` candidate doc not yet cited by any prior batch.
  Each candidate item below was independently verified conflict-clear against all 24 prior covering plans before being
  listed `ao_eligible_candidate_items`; see this batch's own Progress Log for the per-item disposition trail and this
  doc's own `## Deferred` section for the full 36-doc classification report.
---

# AO satellite AO batch 12

> **`status: draft`** — pending operator approval, same convention as batch5-11: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved, same as the rest of this series.

## Why this plan exists

A fresh `/ag-closeout-audit ao` Phase 1 pass (2026-08-09) classified the 36 `ao`-tranche `assigned_vm: NA` docs not
already cited by batch1-11. 34 came back genuinely orphaned (no active plan claims their remaining work); most of those
are correctly non-batchable (operator-gated, genuinely-human-only, conflict-gated with an already-resolved duplicate, or
time-gated pending real-world elapsed time — see the parked-findings doc for the full accounting). 5 docs carried items
that are bounded, worker-determinable, and conflict-clear. This batch extracts the 11 such items whose source doc's
`parent_epic` is `orchestrator_master`.

## Rules for every worker on this plan

- Do not edit the 4 source docs' remaining checkboxes beyond what this plan's own todos below already changed at
  drafting time (a `[x]`/redirect-pointer marking the extracted item). Append your evidence to THIS plan's own todo when
  you finish; the paired finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch12_finalize_2026_08_09.md`)
  reconciles evidence back into each source doc.
- The 11 todos below are file-disjoint by construction — keep new test/evidence files scoped to the todo's own concern.
- Todo 5 and todo 8 are the only todos touching live production state (a `state.db` row repair and a worker-slot git
  reset respectively); both are explicitly `[OPERATOR]`-adjacent per the source docs' own established precedent
  (mirroring `deepseek_flash_ab_routing_test_2026_08_05.md` todo 16's `repair_unpriced_deepseek_spend.py --apply`
  pattern) — dry-run/verify-first, no other todo below deletes prod data or launches a VM.

## Todos

- [x] ✅ [TEST] P2. **Add a unit test in `agent-orchestrator/server/autospawn.py` proving N consecutive DeepSeek
      dispatches split ~50/50 across pro/flash variants, reproducibly across a process restart.** Exercise the full
      `select_account_for_spawn` path (per the source doc's 2026-08-05 ratio-skew Progress Log finding), not just the
      `_deepseek_flash_should_route` accumulator in isolation. **Done when**: the test passes deterministically across 3
      consecutive local runs and `bash scripts/quality-gates.sh` is green in `agent-orchestrator/`. Source:
      `/plans/active/deepseek_flash_ab_routing_test_2026_08_05.md:79` (todo 2). Repo: agent-orchestrator. —
      agent-orchestrator@4d27bc1. 6 new tests in `test_deepseek_provider_routing.py`, all exercising
      `select_account_for_spawn` end-to-end (not the accumulator in isolation): exact 50/50 alternation with active-slot
      counts held equal, reproducibility across a simulated process-restart (both split accumulators reset to their
      literal module-level 0.0), determinism across 3 independent fresh-state runs, degrade-to-pro when the flash pool
      is empty, and a regression test locking in the KNOWN ratio-skew itself (an unfiltered pick can still return flash
      even with `wants_flash` permanently False, when flash has fewer active slots — exactly the behavior the source
      finding warned a strict-alternation-only test would miss). Full `quality-gates.sh` green (3065 pytest + 262
      vitest + tsc + basedpyright + ruff, run twice — once pre-commit, once re-verified on the exact committed SHA per
      the sentinel-ordering rule), ancestry-verified on `origin/live-defi-rollout`.
- [x] ✅ [UI] P2. **Write the missing Playwright regression spec (`pw:L2`, per
      `/codex/06-coding-standards/ui-testing-layers.md`) for the already-shipped per-model pro/flash filter toggle in
      `agent-orchestrator/dashboard/src/TaskUsageWindows.tsx`** (the `_FILTER_OPTIONS` UI change from
      `agent-orchestrator@7d73ded`). **Done when**: the spec asserts the pro/flash filter actually narrows the rendered
      rows, is tagged `pw:L2`, and passes in CI. Source: `/plans/active/deepseek_flash_ab_routing_test_2026_08_05.md:97`
      (todo 4). Repo: agent-orchestrator. — `agent-orchestrator@26f8a49`. New
      `dashboard/tests/e2e/task-usage-provider-filter.spec.ts` (5 tests) reuses the shared e2e fixture (every seeded
      `TaskUsageRow` is `model=deepseek-v4-pro`) rather than mutating it — asserts "All providers" / "DeepSeek (all)" /
      "DeepSeek · Pro" all sum the same 3 rows (17.0K lifetime input, 3 tasks), while "DeepSeek · Flash" and "Anthropic"
      genuinely NARROW the rendered windows down to the known-zero row (never the panel's empty state, per
      `window_task_usage_totals`'s always-5-windows contract — same pattern task-usage-role-group-filter.spec.ts's
      "Conflict resolver" case already established), plus a switch-back-restores-the-sum test. `pw:L2 ✓`
      (`npx playwright test --project=chromium tests/e2e/task-usage-provider-filter.spec.ts`, 5/5 passed; sibling
      `task-usage-role-group-filter.spec.ts` re-run to confirm no regression, 5/5 passed). Full
      `bash scripts/quality-gates.sh` green (3069 pytest + 262 vitest + tsc + basedpyright + ruff, run twice — once
      pre-commit, once re-verified on the exact committed SHA per the sentinel-ordering rule), ancestry-verified on
      `origin/live-defi-rollout`. regression: `dashboard/tests/e2e/task-usage-provider-filter.spec.ts`.
- [x] ✅ [BACKEND] P2. **Build a structured `review_finding` activity-log event** (`task_id`, `severity`,
      `finding_text`, `agent_id`, `created_at`) emitted from the review role's existing finding-post path in
      agent-orchestrator, plus a query/report endpoint or script and a regression test proving emission + retrieval.
      Operator already ruled "yes, build it" (2026-08-08, ao round-5 apply session, item 2). **Done when**: the event is
      emitted on every real review finding, the query endpoint/script returns it, the regression test passes, and
      `bash scripts/quality-gates.sh` is green. Source: `/plans/active/deepseek_flash_ab_routing_test_2026_08_05.md:170`
      (todo 12a). Repo: agent-orchestrator. — agent-orchestrator@7a7ef2e. `POST /api/slots/{slot_id}/message` now logs a
      `review_finding` activity event (task_id/severity/finding_text/agent_id) whenever `from_role == "review"` —
      task_id falls back to the target slot's `current_task` when the caller omits it, severity defaults to
      `needs-rework` (this send path is documented in `review.md` as reserved for worker-actionable defects), so
      emission requires no `review.md` change to start firing on real findings today. Added a new
      `GET /api/review-findings` query endpoint (task_id/slot/severity/date-range filters, severity applied post-fetch
      since it lives in `details_json`) plus a `task_id` SQL filter on `list_activity()`. 7 new regression tests
      (`tests/test_review_findings.py`) cover emission (explicit task_id+severity, slot-current_task fallback,
      non-review roles don't fire) and retrieval (task_id filter, severity filter, event-type isolation). Full
      `quality-gates.sh` green (3076 pytest, run twice — once pre-commit, once re-verified on the exact committed SHA
      per the sentinel-ordering rule), ancestry-verified on `origin/live-defi-rollout`.
- [x] ✅ [UI] P3. **Investigate whether DeepSeek's OpenAI/Anthropic-compatible API endpoint actually honors the Claude
      Code CLI's `thinking: on/off` flag, then relabel the Fleet table's thinking-brain icon honestly based on the
      finding** (the icon currently echoes the CLI's own flag regardless of provider — unconfirmed whether DeepSeek's
      API honors or silently ignores it). **Done when**: the investigation's finding is recorded with evidence (a real
      request/response trace, or documented API-spec confirmation), and the icon's label/tooltip matches reality.
      Source: `/plans/active/deepseek_flash_ab_routing_test_2026_08_05.md:231` (todo 17b). Repo: agent-orchestrator. —
      **Investigated + fixed 2026-08-10 (slot-6, ui_developer): finding is broader than the todo assumed — the flag is
      inert on adaptive-reasoning models regardless of provider, not a DeepSeek-specific honesty gap.** Evidence: 1.
      **DeepSeek's own docs** (`api-docs.deepseek.com/guides/anthropic_api/`): the Anthropic-compat endpoint's
      compatibility table lists `thinking` as "Supported (`budget_tokens` is ignored)" — the on/off type is nominally
      honored, but the CLI's specific `--max-thinking-tokens 31999` value is documented-ignored; DeepSeek applies its
      own internal reasoning-depth control instead. 2. **Live transcript sampling** (real fleet sessions,
      `~/.claude-configs/*/projects/*/<claude_session_id>.jsonl`, grepped for `"type":"thinking"` content blocks): 3
      DeepSeek-routed sessions spawned via `server/escalation.py` (which never passes a `thinking` kwarg — confirmed via
      `_do_spawn`'s `thinking: str | None = None` default, so these ran with the flag OFF/unset) showed 77-118 genuine
      thinking blocks each. **Control**: 3 real-Anthropic sessions with the SAME flag unset (same escalation.py code
      path, non-DeepSeek accounts) ALSO showed 20-96 thinking blocks — ruling out a DeepSeek-specific difference. Root
      cause: `tmux_spawn.py`'s own comment already documents `--max-thinking-tokens` as "inert" on sonnet 5 / opus 4.8 /
      fable 5 (adaptive-reasoning models, `effort` is the real depth control) — this is a model-generation property, not
      a provider-honesty gap, so both providers show thinking content regardless of the flag. 3. **Fix shipped**:
      `agent-orchestrator@64a0291` — `ModelBadge`'s thinking tooltip (`dashboard/src/layout.tsx`) now reads "Thinking
      requested: on/off" (not a flat, unqualified claim) with the inert-on-adaptive-models caveat, plus a
      DeepSeek-specific note that the token budget is ignored even when the flag IS honored. New Playwright spec
      `dashboard/tests/e2e/thinking-flag-honesty.spec.ts` (extends `provider-badge.spec.ts`'s established pattern)
      asserts the honest tooltip renders for the fixture's DeepSeek slot. `tsc --noEmit` clean, full `vitest run` green
      (262/262, no regressions). 4. **Playwright execution gap (honest disclosure, not swept under)**: could not get a
      genuine green `npx playwright test` run in this sandbox — chromium loads the page and JS executes (confirmed:
      manual `curl /api/state` against the exact same e2e backend/port shows slot 1's real data,
      `provider=deepseek,        thinking=null`, correctly seeded), but the Fleet table never populates client-side, so
      `tr.row` locators time out. Isolated this to a PRE-EXISTING environment limitation, not a regression from this
      change: the already-shipped `provider-badge.spec.ts` (untouched by this diff) fails identically, alone,
      single-worker, on this same sandbox. `playwright install chromium --with-deps` fails here (`sudo` blocked by the
      sandbox's no-new-privileges flag) — plausibly a missing browser system dependency specific to this host, not this
      repo's test code. Recommend a follow-up check on a normal dev/CI host before treating `pw:L2` as fully green for
      this spec; the spec itself mirrors a previously-shipped, presumably-passing pattern exactly.
- [ ] [BACKEND] P3. **Retagged 2026-08-09 (was `[OPERATOR] [BACKEND]`) — the source todo this was extracted from
      (`deepseek_flash_ab_routing_test_2026_08_05.md:447` todo 25) already dropped `[OPERATOR]` in favor of plain
      `[BACKEND]`; this copy's tag was stale, not the underlying work, which remains open (see below).** Extend
      `agent-orchestrator/scripts/orchestrator/backfill_task_usage.py` to cover one-off completions lost during a prior
      deploy window, then run it. Operator already ruled "run the backfill" (2026-08-08, ao round-5 apply session, item
      3). The live script's `backfill()` is keyed purely off `SlotHistoryRow`, so one-off tasks (`AgentRow`-only,
      `task_id=f"one-off:{agent_id}"`) have zero candidates today — add a second candidate source selecting `AgentRow`
      rows in the affected window (`registered_at` between the `de73f93` and `acd6d70` deploy timestamps) lacking a
      `TaskUsageRow`, deriving `assigned_at`/`completed_at` from `AgentRow` state (mirroring the one-off capture logic
      `deepseek_usage.build_task_usage_snapshot` already uses), merged into the same
      `_match_usage`/`record_task_usage(backfilled=True)` path. Tagged `[OPERATOR]`-adjacent since the `--apply` step
      mutates live production rows directly via SSM — same provenance as `deepseek_flash_ab_routing_test_2026_08_05.md`
      todo 16's `repair_unpriced_deepseek_spend.py --apply` run. **Done when**: the extension ships with a regression
      test (a one-off candidate with no `SlotHistoryRow` gets matched and backfilled), a live dry-run report is
      reviewed, `--apply` runs via SSM against the live orchestrator VM, and the affected window's one-off
      `TaskUsageRow` count is verified non-zero (or genuinely unmatched due to transcript rotation — report either way).
      Source: `/plans/active/deepseek_flash_ab_routing_test_2026_08_05.md:447` (todo 25). Repo: agent-orchestrator.
- [ ] [BACKEND] P3. **Bound the 12 `UNAUDITABLE` (`brief_hash IS NULL`) rows in the AO backlog `state.db`.** Re-run
      `audit_false_done.py`, re-measure the current count (it has moved since `agent-orchestrator@aaa2db8` shipped), and
      confirm every remaining unhashed row's `status` is `done` (bounds the exposure — a row that is NOT `done` and
      unauditable would be a real gap). Report the split; no bulk-mutation. **Done when**: the current count and the
      done/not-done split are recorded with evidence in this todo. Source:
      `/plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md:343`. Repo:
      agent-orchestrator (read-only DB query).
- [ ] [BACKEND] P3. **Confirm whether the standing false-done breach's silent breach→breach Slack-transition-only
      behavior in `audit_cron_notify.apply_transition` matches the actionable-only alerting contract** documented in
      `/codex/04-architecture/agent-orchestrator-alerting.md`. Report match/mismatch; if mismatched, file a follow-up
      todo rather than fixing silently. **Done when**: the match/mismatch verdict is recorded with the specific contract
      clause cited. Source:
      `/plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md:347`. Repo:
      agent-orchestrator (read-only).
- [ ] [DEVOPS] P2. **Clean-reset the 5 drift-violating repos on `ip-172-31-5-118` slot 0** (`e2e-testing`,
      `instruments-service`, `unified-trading-library`, `execution-service`, `market-data-processing-service`) onto
      current post-history-rewrite `live-defi-rollout` — the source doc confirms no committed work sits on the stale
      base (a re-clone/reset, not a rescue-merge). Requires execution access to that specific host/slot via SSM. **Done
      when**: all 5 repos show `ahead=0`/`behind=0` (or normal small drift) after reset. Source:
      `/plans/archive/issues/fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md:87` (Finding 2 / todo 2
      — Finding 1 was closed as a stale duplicate directly on the source doc, not extracted here). Repo:
      agent-orchestrator (SSM host maintenance).
- [x] ✅ [BACKEND] P1. **Detect the queued-message state and do not spend the force-compact latch on it.** Added a
      `pane_has_queued_messages()` probe to `agent-orchestrator/server/tmux_spawn.py` and had `context_lifecycle`'s
      force-compact path hold the latch un-spent (not re-send) while the target pane shows a queued-not-yet-executed
      message — a second forced `/compact` would compact twice and lose context unnecessarily. Added a new
      `_TargetState.queued_since` field for "submitted but not yet executed". `_force_compact_now` now checks
      `pane_has_queued_messages` first (before either phase's `submit_to_pane` call) and returns without submitting or
      advancing `precompact_forced_at`/`forced_at` while queued; logs `context_force_compact_queued_hold` activity.
      `test_worker_force_holds_latch_unspent_while_pane_shows_queued_message` proves the latch holds across 2 queued
      ticks then submits normally once the queue clears. `bash scripts/quality-gates.sh` green (3022 passed, 2 skipped).
      Evidence: `agent-orchestrator@a1e2969`. Source:
      `/plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md:85` (P1 item 1). Repo:
      agent-orchestrator.
- [ ] [BACKEND] P1. **Verify forced compaction by its EFFECT, not its submission.** Change forced-compact verification
      in `agent-orchestrator/server/context_lifecycle.py` to confirm success via a new `compact_boundary` record
      surfaced by `server/context_probe.py`'s `stale_after_compaction`, instead of trusting
      `tmux_spawn.submit_to_pane()`'s `True` return (which only proves submission, not execution). **Done when**: the
      verification path checks for the boundary record, a regression test proves it catches a queued-but-not-executed
      case the old check would have missed, and `bash scripts/quality-gates.sh` is green. Source:
      `/plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md:89` (P1 item 2). Repo:
      agent-orchestrator.
- [ ] [BACKEND] P2. **Build a deliberate repro for the queued-not-executed `/compact` mechanism** — submit `/compact` to
      a tmux pane mid-turn and confirm (a) it queues rather than executes and (b) `submit_to_pane()` still returns
      `True`. The mechanism is currently inferred from a live pane capture plus five consistent ineffective forces, not
      a controlled repro. **Done when**: the repro script/test reliably reproduces both (a) and (b) on demand. Source:
      `/plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md:93` (P2 item 3). Repo:
      agent-orchestrator.

## Deferred — full disposition of the 36-doc Phase 1 classification (per the parked-findings HARD RULE)

Every genuine parked finding from this run's Phase 1 pass gets a durable home here — this batch's own Deferred section —
per `/cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Parked findings ALWAYS get a durable issue doc" (Phase 3 ran
this cycle, so the batch's own Deferred section is the durable home, not a separate parked-findings doc). 36
`ao`-tranche `assigned_vm: NA` candidate docs (not already cited by batch1-11) were classified via a 36-agent Workflow
fan-out, 2026-08-09.

**Covered by an existing active plan (2) — not orphaned, no extraction needed**:
`ao_recovery_audit_layer1_deleted_2026_07_15.md` (its sole remaining item is fully claimed by
`ao_open_issues_consolidated_close_out_2026_07_17.md`'s Phase-LAST `[BACKEND] P0` todo, operator-sequenced to run last,
re-confirmed by 3 separate na-eligibility-audit passes and batch3/batch10's own declinations) ·
`context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md` (its sole remaining item is fully claimed by
`ao_satellite_ao_dispatch_batch3_2026_07_31.md` todo 1, actively progressing across 5+ sessions, with its own gated
finalize plan already primed to archive this doc once done).

**Fully extracted this run (3) — will read 0 remaining items once batch12/13 land**:
`ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md` (both remaining items → batch12 todos 6-7) ·
`fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md` (Finding 1 closed directly as a stale duplicate of
an already-resolved doc, Finding 2 → batch12 todo 8) · `operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`
(its sole remaining item → batch13 todo 1).

**Partially extracted this run (2) — some items extracted, remainder stays genuinely gated**:
`deepseek_flash_ab_routing_test_2026_08_05.md` (5 of 11 remaining items → batch12 todos 1-5; the other 6 — a 24h
monitoring window, a post-window cost comparison, a completion-quality audit, review-coverage verification, a final
write-up, and an unexplained $2.35 residual — stay `operator-gated`/`time-gated`, blocked on real elapsed monitoring
time and operator/review-agent judgment calls) · `forced_compact_reports_submitted_but_never_executes_2026_08_08.md` (3
of 4 remaining items → batch12 todos 9-11; the 4th — re-measuring the wedge rate — is explicitly `time-gated` on the
other 3 landing plus a fresh multi-hour/day fleet-observation window).

**Declined, zero extraction — genuinely non-batchable as of 2026-08-09 (29)**:

- _operator-gated (22)_: `deepseek_claude_blended_provider_routing_2026_07_28.md` (4/6 items need operator-held DeepSeek
  credentials/production `accounts.json` access; 2 are time-gated real-production pilots) ·
  `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md` ·
  `ao_backlog_no_collision_gate_long_running_driver_todos_2026_08_02.md` ·
  `ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06.md` ·
  `ao_boot_stub_session_vars_field_name_mismatch_2026_08_02.md` ·
  `ao_context_pct_0_for_monitor_heavy_workers_2026_07_29.md` (also human/upstream-CLI-gated) ·
  `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md` · `ao_orphan_audit_followup_triage_2026_07_30.md` ·
  `ao_residuals_after_dispatch_hardening_2026_07_17.md` ·
  `ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md` ·
  `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` · `backlog_regen_reverted_p1_2_park_2026_08_01.md`'s
  unscoped design-fork item · `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` ·
  `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` ·
  `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` ·
  `operator_ruling_record_ao_round5_apply_session_2026_08_08.md` ·
  `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` ·
  `tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md` ·
  `unified_trading_pm_stash_pile_accumulation_2026_07_26.md` (the `git stash drop` loop is explicitly agent-blocked by
  `block_destructive_commands.py`, operator-only per the multi-agent safety HARD RULE) ·
  `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` ·
  `orchestrator_vm_e2e_hardening_2026_07_24.md` (2 of 3 items already moved per batch6-finalize's 2026-08-08 re-check,
  3rd stays a design item) · `slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md` (retagged `[ao]` this
  run — see the Orthogonality fix below; 2 `[OPERATOR]`-tagged kill+respawn items, 1 already claimed by
  `ao_satellite_ao_dispatch_batch5_2026_08_03.md`).
- _genuinely-human-only (4)_: `backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md` ·
  `context_scope_sufficiency_measurement_2026_08_08.md` ·
  `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md` (optional leg only) ·
  `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`.
- _conflict-gated (2)_: `dashboard_deepseek_e2e_specs_red_stale_fixture_expectations_2026_08_08.md` ·
  `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` (a major root-cause fix shipped 2026-08-08
  but spawned 3 new open validation/follow-up todos — more actively contested than at filing, not batch-ready yet).
- _too-large-or-risky (1)_: `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`.

**Ledger**: 36 classified = 2 covered + 3 fully-extracted + 2 partially-extracted + 29 declined-zero-extraction. 12
items extracted across 5 source docs (11 into batch12, 1 into batch13). Full per-doc agent reasoning (evidence
citations, line numbers, covering-plan grep results) is preserved in the Phase 1 Workflow's journal (`wf_cf5dda89-c8d`)
for drill-down if ever needed — not restated here per this doc's own line-cap discipline.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/06-coding-standards/ui-testing-layers.md` (todo 2's `pw:L2` requirement),
`/codex/04-architecture/agent-orchestrator-alerting.md` (todo 7).

## Progress Log

- **2026-08-09** — Authored by `/ag-closeout-audit ao` (autonomous, scheduled dispatch `agt-41d860`, slot 10) Phase 3,
  following a Workflow-based Phase 1 classification of 36 `ao`-tranche `assigned_vm: NA` candidate docs not yet cited by
  batch1-11. Conflict-check: the Phase 1 agents grepped all 24 prior covering plans (consolidated-closeout + batch1-11 +
  finalizes, active and archived) per source doc before flagging any candidate item — zero hits for
  `deepseek_flash_ab_routing_test_2026_08_05.md`, `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md`,
  and `forced_compact_reports_submitted_but_never_executes_2026_08_08.md`. For
  `fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md`, a broadened corpus-wide grep (outside the 24)
  found 2 unrelated citations: a `ci`-tranche metadata-retag list (`ci_satellite_ao_dispatch_batch8_2026_08_09.md`, pure
  frontmatter hygiene, doesn't touch this doc's substance) and the independently-resolved
  `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` (fixed a different subsystem — server-
  side LDR→main marker computation, not worker-slot local-clone drift) — neither claims todo 8's ground. Split by
  `parent_epic` per `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 2: the 11 todos
  above are all from `orchestrator_master`-epic source docs; the 12th candidate item
  (`operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`, `parent_epic: agent_operating_framework_master`)
  is drafted separately as `ao_satellite_ao_dispatch_batch13_2026_08_09.md`, mirroring the batch10/batch11 split.
  File-disjointness verified across all 11 todos (listed target files/paths do not overlap). Full 36-doc classification
  report (including the 29 declined-zero-extraction orphans and the 2 archivable_after_planned_work docs) lives in this
  doc's own `## Deferred` section above, per the parked-findings HARD RULE (Phase 3 ran this cycle, so the batch's
  Deferred section is the durable home, not a separate parked-findings issue doc).
- **stale-`[OPERATOR]`-flip sweep 2026-08-09**: todo about `backfill_task_usage.py` carried a stale `[OPERATOR]` tag —
  the source todo it was extracted from already retagged to plain `[BACKEND]` (the decision was made 2026-08-08, only
  the tag copy here lagged). Retagged to match; checkbox left open since the extension + live `--apply` run itself is
  still real, un-started work, not just a stale tag.
