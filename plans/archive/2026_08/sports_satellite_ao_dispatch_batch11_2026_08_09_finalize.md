---
doc_type: plan
title: Sports satellite AO batch 11 — finalize (reconcile source docs)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch11_2026_08_09.md — machine-held via depends_on + gate_on_depends:
  true until both of that plan's todos are done. Mirrors the batch2-10-finalize pattern: reconcile each of the 2
  distinct source docs' checkboxes once its batch-11 todo lands, then archive both docs.
status: archived
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-11, satellite-docs]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/issues/mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md,
    /plans/archive/2026_08/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-16"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch11_2026_08_09]
gate_on_depends: true
source: >-
  Satellite-batch-extraction pass, 2026-08-09, per task_template.md §4's finalize-plan-coverage rule — every
  assigned_vm: planning plan needs a companion gated finalize plan. Authored status: active from the start (not draft)
  per the 2026-07-30 no-double-gate finding: gate_on_depends already machine-holds every todo below regardless of the
  parent batch's own status, so a second manual flip on this doc would be redundant.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch11_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports satellite AO batch 11 — finalize (reconcile source docs)

> **🟢 ARCHIVED 2026-08-16 — all 3 todos complete.** Both source-doc reconciliations done (naming-canonicalization doc
> archived in full 2026-08-15; odds-watchdog issue doc's timeout-audit checkbox flipped with negative-result evidence
> 2026-08-16, doc stays open with its 2 remaining genuinely-open todos) and batch-11's own 2 todos confirmed `[x]` —
> this finalize plan + its paired batch plan
> (`/plans/archive/2026_08/sports_satellite_ao_dispatch_batch11_2026_08_09.md`) archived together per the 6-step
> ritual.

## Todos

- [x] ✅ [DATA] P3. Reconcile `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` — once batch-11 todo 1
      (odds_api HTTP client timeout audit+fix) lands, flip that doc's `[SCRIPT] P3` timeout-audit checkbox with the
      cited evidence (file:line + commit, or the negative-result citation); the doc's other 2 open todos (opportunistic
      live-hang catch, threshold-tuning gated on this audit's finding) stay open/untouched — do not archive the doc, it
      still has genuinely open work. Source: `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`. Done
      when: the `[SCRIPT] P3` checkbox is flipped with evidence and the doc's remaining open todos are unaffected. —
      **DONE (2026-08-16, slot-15)**: flipped with the negative-result citation (file:line evidence transcribed inline);
      doc's other 2 open todos (live-hang catch, threshold tuning) confirmed untouched — doc stays `status: open`, not
      archived. See `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`'s own Progress Log for the
      reconciliation entry.
- [x] ✅ [DATA] P3. Reconcile `sports_odds_feature_naming_canonicalization_2026_07_21.md` — once batch-11 todo 2
      (FSS↔ml-service↔strategy-service parity test) lands, flip that doc's `[REVIEW] P3` todo 7 checkbox with the cited
      test file(s) + commit; the doc's remaining `[REVIEW] P3` todo 8 (cross-reference against the
      wire-sports-end-to-end plan) stays open — do not archive, one item remains. Source:
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`. Done when: todo 7's checkbox is flipped with evidence
      and todo 8 is correctly left open. — **DONE (plan-reconcile 2026-08-15)**: batch-11 todo 2 confirmed `[x]`
      (`features-service@36fb7b88`, pre-existing, 10/10 tests passing, re-verified). The reconcile target moved further
      than this todo's original "done when" anticipated — the canonicalization doc's todo 8 (cross-reference) was
      independently resolved-by-citation on 2026-08-09 (its cross-reference target archived/resolved), so the doc
      reached ZERO open checkboxes and was archived in full this same pass (not left with one item open) — see
      `/plans/archive/2026_08/sports_odds_feature_naming_canonicalization_2026_07_21.md`'s own Progress Log.
- [x] ✅ [PROCESS] P2. Archive `sports_satellite_ao_dispatch_batch11_2026_08_09.md` + this finalize doc once both
      reconciliations above are done and batch-11's own 2 todos are all `[x]`. Done when: both docs sit in
      `plans/archive/2026_08/` with the archive-ritual citation. — **DONE (2026-08-16, slot-15)**: both reconciliations
      confirmed complete (todo 1 above, plus todo 2's 2026-08-15 full archival of the naming-canonicalization source
      doc); batch-11's own 2 todos confirmed `[x]` in `sports_satellite_ao_dispatch_batch11_2026_08_09.md`. Ran the
      6-step archival ritual: no deferred items to migrate (none found); archived-banner added to both docs;
      no new codex contract established by this closeout (pure reconciliation, nothing to stub/update); referrers
      repointed (`plans/epics/sports_master.md`, this doc's own citations in
      `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`; `plans/active/INDEX.md` regenerated via
      `scripts/plans/regenerate_active_plan_index.py`, not hand-edited); both docs `git mv`'d to
      `plans/archive/2026_08/` in this same commit (single-repo mode-1, sanctioned same-commit flip+archival per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).

## Codex SSOTs

- /plans/active/task_template.md §4 — finalize-plan-coverage rule
- /codex/12-agent-workflow/plan-completion-and-archival-discipline.md — the 6-step archival ritual
