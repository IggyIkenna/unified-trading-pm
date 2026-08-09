---
doc_type: issue
title:
  "safe-doc-push.sh prek-patch-restore bug — finalize"
summary: >-
  Gated closeout for `/plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md` —
  machine-held via `depends_on` + `gate_on_depends: true` until all 3 of that doc's todos are done. Re-verifies the
  reproduction, the shipped safety-net code, and the upstream/pin/document follow-up against reality (not against the
  checkbox), then closes out the source doc.
status: open
nature: issue
asset_group: [ci, ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, ao-dispatch, close-out, finalize, safe-doc-push, prek, precommit, data-loss]
related:
  [
    /plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    /scripts/dev/safe-doc-push.sh,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: review
effort: medium
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as the RECLASSIFY of its source doc, `na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)`.
---

# safe-doc-push.sh prek-patch-restore bug — finalize

> **Machine-gated on `/plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`**
> (`depends_on` + `gate_on_depends: true`) — will not dispatch until all 3 of that doc's todos are `done`.

## Todos

- [ ] [REVIEW] P0. **Re-verify the reproduction (todo 1) against reality.** Re-run the reproduction recipe
      independently (stage a file that fails a real prek hook once then passes, with an unrelated unstaged edit
      present) rather than trusting the prior session's own report; confirm the stated verdict (prek-level defect vs.
      `safe-doc-push.sh`'s own retry-loop behavior) actually holds.
- [ ] [REVIEW] P0. **Re-verify the safety-net code (todo 2) against reality.** Confirm the shipped change actually
      detects an orphaned `~/.cache/prek/patches/*.patch` file created during the script's own run and warns loudly
      (non-zero exit or a clearly-flagged stderr warning) instead of exiting 0 silently — reproduce a retry-with-orphan
      scenario and confirm the warning fires, not just re-reading the diff/tests.
- [ ] [REVIEW] P1. **Confirm todo 3's disposition matches todo 1's actual verdict** — if the reproduction confirmed a
      genuine prek-level defect, confirm it was filed upstream or a known-good prek version was pinned or the
      workaround was documented in the script's own header comment (whichever the source doc's todo 3 actually did);
      if the reproduction pointed at `safe-doc-push.sh`'s own retry loop instead, confirm todo 3 was correctly
      re-scoped rather than blindly executed as originally worded.
- [ ] [INFRA] P0. **Archive the source doc if all 3 todos are genuinely done**, then run the 6-step archival ritual:
      banner `/plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`, move to
      `plans/archive/2026_08/issues/`, fix every corpus-wide referrer including this finalize plan's own
      `related:`/`depends_on:`, then re-run the active-plan inventory generator. **Done when**: the source doc is
      archived with a banner, the inventory regenerates cleanly, and `check_finalize_plan_coverage.py` no longer names
      this pair.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md`, `/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-10** — Authored in the same turn as the RECLASSIFY of
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`, per the mandatory finalize-twin rule
  (task_template.md §4). `sequential: true` since the 4 todos are a genuine chain (verify → verify → verify →
  archive). Ships `status: open` (issue-doc status vocabulary; not gated behind a draft flag) — `gate_on_depends`
  already machine-holds every task until the
  source doc's own 3 todos are done, matching the batch7-16 finalize precedent.
