---
doc_type: plan
title: AO satellite AO batch 1 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch1_2026_07_26.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc (the
  batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether any
  Deferred item's gate has since cleared, archives the source docs that reach zero open todos, and runs the standard
  6-step archival ritual on the batch plan itself.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-1, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ao_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch1_2026_07_26]
gate_on_depends: true
sequential: true
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit skill run of 2026-07-26.
---

# AO satellite AO batch 1 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`.
>
> **`status: draft`** — stays undispatched until the batch itself is approved by the operator and substantially
> underway, per the draft-gated phase-chain pattern in `/plans/active/task_template.md` §4. Flipping either doc to
> `active` is the operator's call.

## Todos

- [ ] [REVIEW] P0. **Re-verify every batch-1 done-claim against reality, not against its checkbox** — for each of the 10
      todos in `/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md`, re-run `git show --stat <sha>` for every
      cited commit and re-run the specific named test(s) directly rather than trusting the claim, and re-run each todo's
      own stated done-when check where it is a command (e.g. the reporter-staleness read, the per-`reason_code` table's
      code reads, the 7-row rootm present/absent table). **Done when**: all 10 verified, and any claim whose evidence
      does not hold up is re-opened as a new tracked todo in this doc's Progress Log with the discrepancy stated.
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox** — batch 1
      was an extraction, so the 13 source-doc todos it covers are the ones that go stale, not the batch's. Flip the
      specific todo in each of: `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` (3 todos — 2×P1 + the
      P2 timeout alignment), `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md`
      (2×P2), `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (INFRA P2) AND
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (SCRIPT P2) — **both**, since
      batch todo 3 folded a genuine duplicate pair — `git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md`
      (2×INFRA P2), `playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md`,
      `dispatch_sequential_gate_fix_2026_07_24.md` (BACKEND P1 only), `slot_double_reset_dataloss_race_2026_07_25.md`,
      `gated_skip_park_no_slack_page_2026_07_25.md`, `orphan_rootm_branch_unmerged_work_2026_06_05.md` (a prose doc with
      NO checkbox surface — add a dated verdict section instead of a flip), and
      `ao_backlog_done_row_disappearance_2026_07_25.md` (BACKEND P3 only). **Done when**: every one of those flips or
      verdict sections is committed with the `docs(plans):` prefix and cites the real commit sha.
- [ ] [INFRA] P0. **Re-check every Deferred item's gate and spin the cleared ones into batch 2** — walk both Deferred
      sections of the batch plan and, for each entry, state whether its named gate has cleared: the watchdog-cluster
      ordering decision, the failover release-signal item (gated on that ordering), the `/done`-semantics pair (gated on
      the operator-merge-gate decision in `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`), the
      AutoSpawn gap (file-collision-gated on batch todo 1, which by this point HAS landed — so this one should clear),
      the `_ahead_push` rejected-push item, the periodic dirty-resolution sweep, the regen positional-task-id deferral,
      the `slack-read-channel.py` env-var compliance question, and the two QG-harness worktree-isolation items. **Done
      when**: each entry is marked cleared-and-moved (naming the new batch-2 plan and todo) or still-gated with the
      current reason — no entry left unstated.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint the AO closeout's Sources**
      — run the standard 6-step archival ritual per doc (migrate any DEFERRED item into a tracked todo → add the
      `> **🟢 ARCHIVED**` banner → codex-alignment check → update CLAUDE.md/codex if a contract changed → fix every
      referrer's path corpus-wide → clear the lock). At minimum this covers the two docs that were ALREADY fully done
      before batch 1 ran (`ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md` and
      `orchestrator_slots_context_directive_issued_missing_migration_2026_07_25.md`) plus any source doc batch 1 emptied
      (`slot_double_reset_dataloss_race_2026_07_25.md` is the likeliest). **Every one of these is cited as a Source in
      `/plans/active/ao_consolidated_closeout_2026_07_25.md`, so the same commit MUST repoint that doc's Track entries
      at `plans/archive/`** or the tranche reference is silently orphaned. **Done when**:
      `grep -rl <slug> plans/ codex/` returns only the archived copy's own path for each archived doc, the AO closeout's
      Sources resolve, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero hard failures.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md`, migrate any still-Deferred item into batch 2 (never
      leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_07/`, fix
      every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plan-hygiene/regenerate_active_plan_inventory.py`. **Done when**: the batch plan is
      archived with a banner, the inventory regenerates with an orphan count of 0, and `check_finalize_plan_coverage.py`
      no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-07-26** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode).
  `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile → re-check gates →
  archive sources → archive self) and several touch the same files. Left `status: draft`.
