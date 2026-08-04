---
doc_type: plan
title: Sports satellite AO batch 8 — finalize (reconcile source docs)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch8_2026_07_30.md — machine-held via depends_on + gate_on_depends:
  true until all 5 of that plan's todos are done. Mirrors the batch3-7-finalize pattern: reconcile each distinct source
  doc's checkboxes once its batch-8 todo lands, then archive both docs.
status: complete # (was: active) 2026-08-04 archival: both todos [x], no locked_by
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-8, satellite-docs]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch8_2026_07_30.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch8_2026_07_30]
gate_on_depends: true
source: >-
  /ag-closeout-audit-style workflow run 2026-07-30, per task_template.md §4's finalize-plan-coverage rule — every
  assigned_vm: planning plan needs a companion gated finalize plan, mirroring the batch2-7 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch8_2026_07_30.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27_finalize.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Sports satellite AO batch 8 — finalize

> **🟢 ARCHIVED 2026-08-04.** Both todos done: source-doc reconciliation (todo 1, slot-7) verified all 5 batch-8 commits
> on `origin/live-defi-rollout`, §E3 properly resolved; archival (todo 2, slot-5) completed via the 6-step ritual.
> Deferred items re-verified and all already tracked in their respective target docs. No new durable contract
> established. Archived alongside `sports_satellite_ao_dispatch_batch8_2026_07_30.md` in the same session.

> **Status: draft.** Flip to `active` in the same commit/decision as the parent batch (`gate_on_depends: true` holds
> every todo below back until all 5 parent todos are `done`, regardless of this doc's own `status`).

> **Machine-gated on `sports_satellite_ao_dispatch_batch8_2026_07_30.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 5 tasks in that plan are `done`. `sequential: true` because
> todo 1 needs all 5 parent todos' evidence to reconcile source docs correctly.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile source-doc checkboxes for all 5 batch-8 todos.** Each batch-8 todo ends with a
      `Source:` line naming its specific section in `issues/sports_features_layer_findings_sweep_2026_07_18.md` — flip
      the corresponding checkbox there, citing the batch-8 commit(s) that shipped it. Verify every cited commit/evidence
      actually exists before citing it (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`, or for the audit
      todo, re-run the stated read yourself rather than trusting the batch-8 todo's own claim). For the DIAG-verify todo
      (§E3), confirm it actually resolved to either a closed-with-citation state or a precisely-scoped new finding — not
      left ambiguous. **Done when**: every Source-cited section in the doc is flipped with verified evidence. — **Done
      2026-08-04 (slot-7):** All 5 Source:-bearing batch-8 todos reconciled. Source doc checkboxes already `[x]` and
      cite batch-8. Verified commits on `origin/live-defi-rollout`: `instruments-service@453e76f1` (junk-symbol guard),
      `@627fd31c` (venue case-mismatch), `@af4ce16d` (Vietnamese/Azerbaijani follow-up) — all ancestor-verified. §E3
      properly resolved: closed-with-citation + precisely-scoped residual `[CONFIG] P2`. No code shipped
      (verification-only reconciliation).
- [x] ✅ [DOC] P2. **Archived `sports_satellite_ao_dispatch_batch8_2026_07_30.md` (and this finalize doc) 2026-08-04
      (slot-5).** Both docs terminal — all 5 batch-8 todos verified [x], locked_by empty on both. 6-step ritual: (1)
      Deferred items re-verified and all already tracked in target docs; (2) archive banners added to both docs; (3)
      codex check clean — no new contracts; (4) no CLAUDE.md/codex update needed; (5) referrer paths updated
      corpus-wide; (6) `git mv` both to `plans/archive/2026_07/`. `INDEX.md` regenerated. Hygiene sweep green.

## Codex SSOTs

None new — see the parent batch's own Codex SSOTs section.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (6 entries) -- includes the source doc todo 1 reconciles
  checkboxes against.

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
