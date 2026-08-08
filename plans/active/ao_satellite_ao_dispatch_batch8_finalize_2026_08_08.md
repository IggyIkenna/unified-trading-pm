---
doc_type: plan
title: AO satellite AO batch 8 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch8_2026_08_08.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc(s)
  (the batch was an extraction, so the source docs' own checkboxes are the ones that go stale), archives the source docs
  that reach zero open todos, and runs the standard 6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-8, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/active/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch8_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-08-08. Ships `status: active` (not draft)
  per the skill's 2026-07-30 finding: `gate_on_depends` already machine-holds every task until the batch's own todos are
  done, so a second draft-gate is a redundant, easy-to-forget manual flip — only the batch itself (genuinely unreviewed,
  judgment-laden content) needs `status: draft` + explicit operator approval.
---

# AO satellite AO batch 8 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [ ] [REVIEW] P0. **Re-verify every batch-8 done-claim against reality, not against its checkbox** — for each of the 4
      todos in `/plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md`, re-run `git show --stat <sha>` for any
      cited commit and re-run the specific named regression check (the 10x-loop stable-rerun for todos 1-3; the written
      2-clone reproduction verdict for todo 4) directly rather than trusting the claim. **Done when**: all 4 verified,
      and any claim whose evidence does not hold up is re-opened as a new tracked todo in this doc's Progress Log with
      the discrepancy stated.
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)** — batch
      8 was an extraction, so the source-doc items it covers are the ones that go stale, not the batch's. Flip the
      specific todo(s) in each of: `/plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` (items
      1-3; leave item 4 — doc fold-in — untouched unless todo 1's Done-when explicitly landed a codex note, in which
      case flip it too), `/plans/active/issues/e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md`
      (item 1 only; leave items 2-3, the operator-decision cluster, untouched), and
      `/plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` (items 1-2 only;
      leave items 3-4, the operator-gated mitigation, untouched). **Done when**: all flips are committed with the
      `docs(plans):` prefix and cite the real commit sha(s) or the written verdict location.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** Re-check
      each of the 3 source docs named in todo 2 above for whether their OTHER (deferred) items are also closed before
      archiving — none should be archived while a deferred operator-gated item remains open. Run the standard 6-step
      archival ritual (migrate any DEFERRED item → banner → codex-alignment check → fix every referrer's path
      corpus-wide → clear the lock) on any doc that IS fully done. **Done when**: `grep -rl <slug> plans/ codex/`
      returns only the archived copy's own path for each archived doc, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero NEW hard failures (compare against the baseline
      recorded at this finalize plan's authoring time).
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md`, migrate any still-open Deferred item into batch 9
      (never leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_08/`,
      fix every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py --commit` (verify the exact entrypoint name at
      execution time). **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly, and
      `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips).

## Progress Log

- **2026-08-08** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode, scheduled
  dispatch). `sequential: true` is deliberate here: the four todos are a genuine chain (verify → reconcile → archive
  sources → archive self). Ships `status: active` per the skill's 2026-07-30 finding (`gate_on_depends` already holds
  every task; no separate draft-gate needed).
