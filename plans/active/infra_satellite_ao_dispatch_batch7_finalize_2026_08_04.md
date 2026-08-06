---
doc_type: plan
title: Infra satellite AO dispatch batch 7 — finalize (reconcile source-doc checkboxes + archive)
summary: >-
  Gated closeout for `infra_satellite_ao_dispatch_batch7_2026_08_04.md`, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24; machine-enforced by
  `scripts/quality_gates/check_finalize_plan_coverage.py`). Once all three batch todos are done, reconciles the
  corresponding checkbox/text back into each source doc
  (`issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md`'s todos 1-2,
  `issues/deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md`'s sole todo — narrowed, not closed)
  and checks whether either source doc is now an archival candidate. Neither is expected to fully archive: the
  na-eligibility-audit doc's population is fully consumed by this batch (both todos), so it likely DOES become
  archival-eligible once both land — verify at finalize time rather than assuming either way; the terraform doc keeps
  its own operator-gated (a)/(b) decision remainder, so it stays open regardless.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, finalize, batch-7, plan-hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch7_2026_08_04.md,
    /plans/active/issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md,
    /plans/active/issues/deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [infra_satellite_ao_dispatch_batch7_2026_08_04]
gate_on_depends: true
locked_by:
locked_since:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch7_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
supersedes:
superseded_by:
source: >-
  Authored alongside its parent batch by `/ag-closeout-audit infra` (2026-08-04), per the standing
  finalize-plan-coverage rule (every ≥2-todo `assigned_vm: planning` plan needs a gated finalize twin).
---

# Infra satellite AO batch 7 — finalize

Machine-held via `depends_on` + `gate_on_depends: true` until all three of
`infra_satellite_ao_dispatch_batch7_2026_08_04.md`'s todos are done — this plan can never dispatch early, regardless of
whether the batch is `draft` or `active` at the time (the gate reads the batch's own checkboxes directly, per the
skill's no-double-gate mechanism).

## Todos

- [ ] [REVIEW] P3. **Reconcile
      `issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md`'s todos 1-2.**
      Once batch7's content-hash (todo 1) and SKILL.md-update (todo 2) todos ship, flip both of that source doc's
      `- [ ] [SCRIPT] P3` / `- [ ] [DOCS] P3` checkboxes to `[x]`, citing the batch7 commit SHA(s). Both of that doc's
      todos are consumed by this batch — if flipping both leaves it with zero open checkboxes and no other
      operator-gated remainder, treat it as an archival candidate (confirm via `check_archive_candidates.sh` or a direct
      re-read) rather than leaving it stranded `active`/`open` with nothing left to do. (repo: unified-trading-pm)
- [ ] [REVIEW] P3. **Reconcile `issues/deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md`'s sole
      todo — narrow, do NOT close.** Once batch7's investigation todo ships (with its dated git-history finding recorded
      in that doc's Progress Log), update the source doc's own
      `- [ ] [OPERATOR] P3. Investigate via git log --follow/git blame...` todo text to reflect that the investigation
      is done and cite the finding — but do **NOT** flip it to `[x]`: the (a)/(b) structural decision (fix the
      misleading comment vs. wire a real `module` block) remains an open, narrower `[OPERATOR]` item regardless of what
      the investigation found. This source doc stays `assigned_vm: NA`, NOT an archival candidate this round. (repo:
      unified-trading-pm)
- [ ] [DOC] P3. **Archive `infra_satellite_ao_dispatch_batch7_2026_08_04.md`** once all three todos above are done and
      both reconciliations are verified — run the standard 6-step archival ritual (`git mv` to `plans/archive/2026_08/`,
      fix every corpus referrer path, confirm `check_ag_closeout_linkage.py` and `regenerate_active_plan_inventory.py`
      both stay clean). Do this as a SEPARATE commit from the checkbox-flip commits above (never combine a flip +
      `git mv` in one commit — 2026-07-30 incident,
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). (repo: unified-trading-pm)

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual + the
  never-combine-flip-with-git-mv rule
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-04** — Authored alongside `infra_satellite_ao_dispatch_batch7_2026_08_04.md` by `/ag-closeout-audit infra`
  (autonomous mode, scheduled daily run, slot 10).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (2 entries), still accurate.
