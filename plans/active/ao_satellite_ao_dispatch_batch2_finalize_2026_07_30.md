---
doc_type: plan
title: AO satellite AO batch 2 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch2_2026_07_30.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc (the
  batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether any
  Deferred item's gate has since cleared (the time-gated item in particular — its 2026-08-02 date will likely have
  passed by the time this finalize runs), archives the source docs that reach zero open todos, and runs the standard
  6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-2, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
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
depends_on: [ao_satellite_ao_dispatch_batch2_2026_07_30]
gate_on_depends: true
sequential: true
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-07-30.
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
  ]
---

# AO satellite AO batch 2 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`.
>
> **`status: active`** — machine-gated (not draft-gated): `depends_on` + `gate_on_depends: true` already holds every
> task of this finalize doc until batch2 finishes, so no separate draft flip is needed. **The gate is CURRENTLY CLOSED**
> — `ao_satellite_ao_dispatch_batch2_2026_07_30.md` still has open todos — this doc will not dispatch until batch2
> reaches 0 open todos.

## Todos

- [ ] [REVIEW] P0. **Re-verify every batch-2 done-claim against reality, not against its checkbox** — for each of the 8
      todos in `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md`, re-run `git show --stat <sha>` for every
      cited commit and re-run the specific named test(s) directly rather than trusting the claim, and re-run each todo's
      own stated done-when check where it is a command (the na-eligibility-timer fire-completion read, the orch_token
      reporter-staleness read, the JWT-secret token-survives-restart + healthz check, the 4 orphan-commit dispositions,
      the wip-preserve ref disposition). **NOTE (plan_reconciler agt-c7578b, 2026-08-10)**: the na-eligibility-timer
      item and the wip-preserve-ref item were EXTRACTED 2026-08-09 to `ao_satellite_ao_dispatch_batch10_2026_08_09.md`
      (todos 1/2) and never completed inside batch2 itself — do NOT expect a done-when check to succeed against batch2
      for those 2 specifically; check batch10's own evidence for them instead. **Done when**: all 8 verified, and any
      claim whose evidence does not hold up is re-opened as a new tracked todo in this doc's Progress Log with the
      discrepancy stated.
- [ ] [REVIEW] P0. **Reconcile each todo's evidence into its TRUE source doc (8 docs, listed below)** — batch 2 was an
      extraction, so the 8 source-doc items it covers are the ones that go stale, not the batch's. Flip the specific
      todo in each of: `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (3 of its 4 todos),
      `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md` (both `[WORKER] P1` checkboxes, with
      per-item MOOT-SUPERSEDED-or-recovered dispositions),
      `mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md` (both todos),
      `na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md` (its SCRIPT P3 item only),
      `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (its INFRA P3 item),
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (its DEVOPS P1 item),
      `dispatch_sequential_gate_fix_2026_07_24.md` (its DOCS P1 item — confirm operator sign-off was actually obtained
      before this flip, per that todo's `[OPERATOR]` tag), and `wip_preserve_refs_silently_unrecovered_2026_07_29.md`
      (its `[DATA] P2` item only). **Done when**: every one of those flips is committed with the `docs(plans):` prefix
      and cites the real commit sha (or, for the read-only/host-action items, the verification evidence).
- [ ] [INFRA] P0. **Re-check every Deferred item's gate and spin the cleared ones into batch 3** — walk both Deferred
      sections of the batch plan and, for each entry, state whether its named gate has cleared: the 7 design/judgment
      forks (re-check whether any has since been operator-ruled or the source doc itself narrowed to one direction), the
      cross-tranche-claimed item (re-check whether `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s
      conflict-check todo has landed — if so, this item's status changes from "claimed elsewhere" to "archivable" or
      "genuinely orphaned again" depending on what that check found), and the time-gated item
      (`ao_done_require_origin_not_enforced_2026_07_29.md` — by the time this finalize runs, **2026-08-02 will very
      likely have passed**; re-measure the `on_origin=False` rate over the now-available fuller-volume window and either
      spin it into batch 3 or record why it's still not ready). **Done when**: each entry is marked cleared-and-moved
      (naming the new batch-3 plan and todo) or still-gated with the current reason — no entry left unstated.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** At minimum
      re-check `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (its 4th, DOCS todo may still
      be open if the codex sign-off didn't land in time),
      `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md`,
      `mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`,
      `na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md` (its P2 timeout-retune item likely still open — do
      not archive if so), `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`,
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md`,
      `dispatch_sequential_gate_fix_2026_07_24.md`, and `wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its 2
      SCRIPT items likely still open — do not archive if so). Run the standard 6-step archival ritual (migrate any
      DEFERRED item → banner → codex-alignment check → update CLAUDE.md/codex if a contract changed → fix every
      referrer's path corpus-wide → clear the lock) on any doc that IS fully done. **Done when**:
      `grep -rl <slug> plans/ codex/` returns only the archived copy's own path for each archived doc, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero hard failures.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md`, migrate any still-Deferred item into batch 3 (never
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

- **2026-07-30** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode).
  `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile → re-check gates →
  archive sources → archive self) and several touch the same files. Left `status: draft`.
- **2026-08-06 (/plan-reconcile ao)**: corrected the stale body banner — frontmatter is `status: active` (machine-gated
  via `depends_on`+`gate_on_depends: true`, not draft-gated; the 2026-07-30 entry above records the authoring-time state
  only). Banner text fixed; no dispatch-readiness change — the gate itself is still closed (batch2 has open todos).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — all paths resolve, still the correct archival
  SSOT + batch-sibling set; no change needed. Gated finalize doc, no source path.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate — genuine `*_finalize`
  gate, every todo points at other docs, no source path applies.
